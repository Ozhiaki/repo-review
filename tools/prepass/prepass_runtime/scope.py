"""Capture the tested Git scope and source bytes without trial dependencies."""
from __future__ import annotations

import base64
import json
import hashlib
import os
from pathlib import Path
import re
import stat

from . import records as s

MAX_BYTES = 32 * 1024 * 1024


def pointer(data):
    if not 0 < len(data) < 1024 or not data.endswith(b"\n") or b"\r" in data:
        return None
    try:
        lines = data.decode("utf-8").splitlines()
        pairs = [line.split(" ", 1) for line in lines]
        if any(len(pair) != 2 or not re.fullmatch(r"[a-z0-9.-]+", pair[0]) or not pair[1] or pair[1].startswith(" ") for pair in pairs):
            return None
        keys = [key for key, _ in pairs]
        values = dict(pairs)
        if len(keys) != len(values) or keys[0] != "version" or keys[1:] != sorted(keys[1:]):
            return None
        if values.get("version") != "https://git-lfs.github.com/spec/v1":
            return None
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", values.get("oid", "")) or not re.fullmatch(r"0|[1-9][0-9]*", values.get("size", "")):
            return None
        return dict(oid=values["oid"], size=int(values["size"]), keys=values)
    except UnicodeError:
        return None


def checked_name(name):
    path = Path(name)
    s.require(not path.is_absolute() and path.parts and ".." not in path.parts and ".git" not in path.parts,
              "A selected path leaves the source scope.")
    return path


def read_regular(root, name):
    """Use directory descriptors to reject links in every path component."""
    parts = checked_name(name).parts
    directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for component in parts[:-1]:
            child = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            os.close(directory)
            directory = child
        fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        with os.fdopen(fd, "rb") as stream:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode):
                raise OSError("The selected path is not a regular file.")
            if before.st_size > MAX_BYTES:
                raise OSError("The selected file exceeds the fixed 32 MiB read limit.")
            data = stream.read(MAX_BYTES + 1)
            after = os.fstat(stream.fileno())
        if len(data) > MAX_BYTES or (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise OSError("The selected file changed during its read.")
        return data, stat.S_IMODE(after.st_mode)
    finally:
        os.close(directory)


def capture(root, git, reader=read_regular):
    stage = git("stage", ["ls-files", "--stage", "-z"], accepted=None)
    if stage["returncode"]:
        manifest = dict(version=1, records=[], git={}, errors=[dict(kind="git_inventory_failed", returncode=stage["returncode"],
                        message=stage["stderr"].decode("utf-8", "replace"))], coverage="failed")
        manifest["signature"] = s.hashed_json(manifest)
        return manifest, {}
    index = {}
    for raw in stage["stdout"].split(b"\0"):
        if not raw:
            continue
        header, path = raw.split(b"\t", 1)
        mode, oid, level = header.decode("ascii").split()
        name = os.fsdecode(path)
        checked_name(name)
        index.setdefault(name, []).append(dict(mode=mode, oid=oid, stage=int(level)))
    untracked = {os.fsdecode(p) for p in git("untracked", ["ls-files", "--others", "--exclude-standard", "-z"])["stdout"].split(b"\0") if p}
    ignored = {os.fsdecode(p) for p in git("ignored", ["ls-files", "--others", "--ignored", "--exclude-standard", "-z"])["stdout"].split(b"\0") if p}
    tags = git("tags", ["ls-files", "-t", "-z"])["stdout"].split(b"\0")
    skipped = {os.fsdecode(value[2:]) for value in tags if value.startswith(b"S ")}
    head = git("head", ["rev-parse", "--verify", "HEAD"], accepted=(0, 128))
    config = git("scope-config", ["config", "--get-regexp", r"^(core\.sparsecheckout|extensions\.partialclone|remote\..*\.promisor)$"], accepted=(0, 1))
    exclude_path = git("exclude-path", ["rev-parse", "--git-path", "info/exclude"])["stdout"].rstrip(b"\n")
    info = Path(os.fsdecode(exclude_path))
    info = info if info.is_absolute() else root / info
    controls = {}
    for path in (info, info.with_name("sparse-checkout")):
        controls[path.name] = s.digest(path) if path.is_file() else None
    records, payloads = [], {}
    for name in sorted(set(index) | untracked | ignored):
        checked_name(name)
        row = dict(path=name, selected=name not in ignored, tracked=name in index,
                   index=index.get(name, []), skip_worktree=name in skipped)
        if name in ignored:
            row["status"] = "ignored"
        elif any(value["stage"] for value in row["index"]):
            row["status"] = "unmerged"
        elif any(value["mode"] == "160000" for value in row["index"]):
            try:
                present = stat.S_ISDIR((root / name).lstat().st_mode)
            except FileNotFoundError:
                present = False
            row.update(status="submodule_unexpanded", present=present,
                       git_marker=present and (root / name / ".git").exists())
        else:
            try:
                mode = (root / name).lstat().st_mode
                if stat.S_ISLNK(mode):
                    target = os.readlink(os.fsencode(root / name))
                    row.update(status="symlink", target=os.fsdecode(target), target_sha256=hashlib.sha256(target).hexdigest())
                elif not stat.S_ISREG(mode):
                    row.update(status="unsupported_file_type")
                else:
                    data, permissions = reader(root, name)
                    payloads[name] = data
                    row.update(status="file", sha256=hashlib.sha256(data).hexdigest(), bytes=len(data),
                               permissions=permissions, binary=b"\0" in data, lfs=pointer(data))
            except FileNotFoundError as exc:
                row.update(status="missing", error=dict(kind=type(exc).__name__, message=str(exc)))
            except OSError as exc:
                row.update(status="read_error", error=dict(kind=type(exc).__name__, message=str(exc)))
        records.append(row)
    missing_content = [row["path"] for row in records if row["selected"] and (row["status"] != "file" or row.get("lfs"))]
    manifest = dict(version=1, records=records,
                    git=dict(head=head["stdout"].decode("ascii").strip() if head["returncode"] == 0 else None,
                             scope_config=config["stdout"].decode("utf-8", "surrogateescape"), controls=controls),
                    errors=[], missing_content=missing_content, coverage="partial" if missing_content else "complete_for_policy")
    manifest["signature"] = s.hashed_json(manifest)
    return manifest, payloads



def text_field(value):
    if "text" in value:
        return os.fsdecode(value["text"].encode("utf-8"))
    return os.fsdecode(base64.b64decode(value["bytes"], validate=True))


def search(snapshot, names, pattern, native):
    statuses, matches, errors = {}, [], []
    for offset in range(0, len(names), 400):
        batch = names[offset:offset + 400]
        paths = ["./" + name for name in batch]
        common = ["--no-config", "--sort", "path", "--color", "never", "-e", pattern, "--", *paths]
        found = native(f"matches-{offset // 400}", ["--json", *common])
        empty = native(f"nonmatches-{offset // 400}", ["--files-without-match", "--null", *common])
        seen, nonmatches = set(), {os.fsdecode(p).removeprefix("./") for p in empty["stdout"].split(b"\0") if p}
        for line in found["stdout"].splitlines():
            event = json.loads(line)
            if event["type"] != "match":
                continue
            data = event["data"]
            name = text_field(data["path"]).removeprefix("./")
            s.require(name in batch, "A native match leaves the selected file set.")
            seen.add(name)
            matches.append(dict(path=name, line=data["line_number"], lines=data["lines"],
                                submatches=data["submatches"]))
        s.require(nonmatches <= set(batch), "A native non-match leaves the selected file set.")
        valid = found["returncode"] in (0, 1) and empty["returncode"] in (0, 1) and not found["stderr"] and not empty["stderr"]
        valid &= not (seen & nonmatches) and seen | nonmatches == set(batch)
        if not valid:
            errors.append(dict(batch=batch, match_exit=found["returncode"], nonmatch_exit=empty["returncode"],
                               match_stderr=found["stderr"].decode("utf-8", "replace"),
                               nonmatch_stderr=empty["stderr"].decode("utf-8", "replace")))
        for name in batch:
            statuses[name] = "matched" if valid and name in seen else "no_match" if valid else "error_unconfirmed"
    return statuses, matches, errors
