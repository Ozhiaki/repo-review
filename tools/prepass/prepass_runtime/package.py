"""Build and check the shared source package used by production adapters."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import shutil
import sys
import uuid

from . import VERSION, records as r, scope


def processing_inputs():
    directory = Path(__file__).resolve().parent
    paths = [directory.parent / "source_package.py", *directory.glob("*.py"),
             *[path for path in (directory / "assets").rglob("*") if path.is_file()]]
    return {str(path.resolve()): r.digest(path) for path in sorted(paths)}


def output_path(value, source):
    requested = Path(value).expanduser().absolute()
    r.require(not requested.is_symlink(), "The output path is a symbolic link.")
    output = requested.resolve()
    r.require(not output.exists(), "Select a fresh output directory.")
    r.require(source != output and source not in output.parents and output not in source.parents,
              "The output directory overlaps the source directory.")
    r.require(".git" not in output.parts, "The output directory is inside Git state.")
    return output


def git_reader(commands, binary, root, prefix):
    def git(label, args, accepted=(0,)):
        return commands.run(prefix + "-" + label, [binary, "-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null", "-C", root, *args], root, accepted=accepted)
    return git


def counted_rows(manifest, payloads):
    result = []
    for row in manifest["records"]:
        data = payloads.get(row["path"])
        available = row["status"] == "file" and not row.get("lfs")
        reason = row["status"] if row["status"] != "file" else "lfs_pointer" if row.get("lfs") else None
        result.append(dict(path=row["path"], status="counted" if available else reason,
                           sha256=row.get("sha256"), bytes=row.get("bytes"),
                           lines=(0 if row.get("binary") else data.count(b"\n") + int(bool(data) and not data.endswith(b"\n"))) if available else None))
    return result


def facts(manifest, counters):
    # This foundation summary is deliberately small. Step 2 adds section rendering.
    return "\n".join([
        "# Prepass source package", "", "Integration stage: shared source package only.",
        "This package does not yet include the selected tool adapters.",
        "Computed evidence requires source verification before a review claim.", "",
        "Source coverage: " + manifest["coverage"] + ".",
        "Source commit: " + (manifest["git"].get("head") or "unknown") + ".",
        "Inventory paths: " + str(len(manifest["records"])) + ".",
        "Counted physical files: " + str(sum(row["status"] == "counted" for row in counters)) + ".",
        "Selected paths with unavailable or unexpanded content: " + str(len(manifest.get("missing_content", []))) + ".",
        "Ignored paths: " + str(sum(row["status"] == "ignored" for row in manifest["records"])) + ".", "",
        "Read inventory.json for scope, omissions, source hashes, and file states.",
        "Read counter.json for physical counts. Binary files have no text line count.",
        "Source copies are in source/. Submodules remain unexpanded.",
        "LFS pointers do not establish the presence of the referenced content.",
        "Reading records and later query results belong in the separate state/ directory.", "",
    ])


def prepare(args):
    """Create a fresh package. Native work is performed only when called."""
    root = Path(args.repo).expanduser().resolve()
    r.require(root.is_dir(), "The source directory is absent.")
    output = output_path(args.out, root)
    git = shutil.which(args.git)
    r.require(git is not None, "Git is absent. Select an installed Git binary.")
    git = Path(git).resolve()
    tools = {str(git): r.digest(git), str(Path(sys.executable).resolve()): r.digest(Path(sys.executable).resolve())}
    inputs = processing_inputs()
    output.mkdir(parents=True)
    package = output / "evidence"
    package.mkdir()
    (output / "state").mkdir()
    r.save(output / "status.json", dict(state="preparing", stage="shared_source_package"))
    commands = None
    try:
        commands = r.Commands(package / "commands", args.total_timeout, args.command_timeout)
        git_call = git_reader(commands, git, root, "before")
        top = git_call("root", ["rev-parse", "--show-toplevel"], accepted=None)
        r.require(top["returncode"] == 0, "The source must be a Git repository.")
        r.require(Path(os.fsdecode(top["stdout"].rstrip(b"\n"))).resolve() == root,
                  "Select the Git repository root as the source directory.")
        version = git_call("version", ["--version"])["stdout"].decode("utf-8", "replace").strip()
        manifest, payloads = scope.capture(root, git_call)
        r.require(manifest["coverage"] != "failed", "Git inventory failed. Read the command records.")
        r.save(package / "inventory.json", manifest)
        counters = counted_rows(manifest, payloads)
        r.save(package / "counter.json", counters)
        with (package / "files.tsv").open("w") as stream:
            stream.write("path_json\tstatus\tsha256\n")
            for row in manifest["records"]:
                stream.write(json_string(row["path"]) + "\t" + row["status"] + "\t" + row.get("sha256", "") + "\n")
        snapshot = package / "source"
        snapshot.mkdir()
        for number, (name, data) in enumerate(payloads.items(), 1):
            commands.check()
            target = snapshot / scope.checked_name(name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            r.require(r.digest(target) == hashlib.sha256(data).hexdigest(), "A source copy differs: " + name)
            if number % 1000 == 0:
                r.say(f"Copied {number}/{len(payloads)} source files.")
        # The source is checked after capture and copying. This is not an atomic snapshot.
        after, _ = scope.capture(root, git_reader(commands, git, root, "after"))
        r.require(after["signature"] == manifest["signature"], "Source state changed during preparation.")
        r.require(processing_inputs() == inputs and all(r.digest(path) == expected for path, expected in tools.items()),
                  "A processing source or runtime changed during preparation.")
        (package / "facts.md").write_text(facts(manifest, counters))
        metadata = dict(version=VERSION, source_root=str(root), source_signature=manifest["signature"],
                        coverage=manifest["coverage"], stage="shared_source_package", git_binary=str(git),
                        git_version=version, tools=tools, processing_inputs=inputs,
                        created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"))
        r.save(package / "meta.json", metadata)
        r.save(package / "seal.json", dict(version=VERSION, artifacts=r.tree(package)))
        status = dict(state="foundation_complete", stage="shared_source_package", source_preserved=True,
                      source_signature=manifest["signature"], coverage=manifest["coverage"],
                      review_ready=False, acceptance="pending")
        r.save(output / "status.json", status)
        r.say("Source package: " + str(package))
        r.say("Tool adapters and integration acceptance are pending.")
        return 0
    except BaseException as exc:
        r.save(output / "status.json", dict(state="interrupted" if isinstance(exc, KeyboardInterrupt) else "failed",
                                           stage="shared_source_package", error=str(exc), review_ready=False))
        raise
    finally:
        if commands is not None:
            commands.stop()


def json_string(value):
    import json
    return json.dumps(value, ensure_ascii=True)


def check(args):
    """A failed check must not leave a previous fresh result as the latest state."""
    try:
        return check_package(args)
    except BaseException as exc:
        output = Path(args.out).expanduser().resolve()
        state_home = output / "state"
        if state_home.is_dir() and not state_home.is_symlink() and (output / "status.json").is_file():
            r.save(state_home / "freshness.json", dict(state="unverifiable", changed=["check_failed"],
                                                      error=str(exc), review_ready=False))
        raise


def check_package(args):
    """Write check logs outside the sealed evidence directory."""
    output = Path(args.out).expanduser().resolve()
    package = output / "evidence"
    r.require(package.is_dir() and not package.is_symlink(), "The evidence package is absent or linked.")
    r.require((output / "state").is_dir() and not (output / "state").is_symlink(),
              "The review state directory is absent or linked.")
    metadata, seal = r.read(package / "meta.json"), r.read(package / "seal.json")
    r.require(metadata["version"] == seal["version"] == VERSION, "The package version is unsupported.")
    # Do not execute a runtime selected by damaged metadata.
    actual = r.tree(package)
    actual.pop("seal.json", None)
    check_home = output / "state" / "checks" / uuid.uuid4().hex
    r.output_directory(check_home)
    if actual != seal["artifacts"]:
        result = dict(state="stale", changed=["package_artifacts"], coverage=metadata["coverage"],
                      current_source_signature=None, stage=metadata["stage"], review_ready=False)
        r.save(check_home / "result.json", result)
        r.save(output / "state" / "freshness.json", result)
        r.say("Freshness: stale. Record: " + str(check_home / "result.json"))
        return 1
    commands = r.Commands(check_home / "commands", args.total_timeout, args.command_timeout)
    reasons = []
    try:
        for path, expected in metadata["tools"].items():
            if not Path(path).is_file() or r.digest(path) != expected:
                reasons.append("tool:" + path)
        for path, expected in metadata["processing_inputs"].items():
            if not Path(path).is_file() or r.digest(path) != expected:
                reasons.append("processing_input:" + path)
        root, binary = Path(metadata["source_root"]), Path(metadata["git_binary"])
        can_check = root.is_dir() and str(binary) in metadata["tools"] and binary.is_file() and "tool:" + str(binary) not in reasons
        current = None
        if can_check:
            git_call = git_reader(commands, binary, root, "freshness")
            top = git_call("root", ["rev-parse", "--show-toplevel"], accepted=None)
            if top["returncode"] == 0 and Path(os.fsdecode(top["stdout"].rstrip(b"\n"))).resolve() == root:
                current, _ = scope.capture(root, git_call)
        if current is None or current["coverage"] == "failed":
            state = "unverifiable"
            reasons.append("git_inventory_unavailable")
        else:
            if current["signature"] != metadata["source_signature"]:
                reasons.append("source_state")
            state = "stale" if reasons else "fresh"
        result = dict(state=state, changed=reasons, coverage=metadata["coverage"],
                      current_source_signature=current["signature"] if current else None,
                      stage=metadata["stage"], review_ready=state == "fresh" and metadata.get("review_ready", False))
        r.save(check_home / "result.json", result)
        r.save(output / "state" / "freshness.json", result)
        r.say("Freshness: " + state + ". Record: " + str(check_home / "result.json"))
        return 0 if state == "fresh" else 1
    finally:
        commands.stop()
