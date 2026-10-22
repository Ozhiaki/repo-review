"""Canonical records and bounded native commands for prepass evidence."""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time


class PrepassError(RuntimeError):
    pass


def install_interrupt_handler():
    def interrupted(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, interrupted)


def require(condition, message):
    if not condition:
        raise PrepassError(message)


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def hashed_json(value):
    data = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


def read(path):
    require(Path(path).is_file() and not Path(path).is_symlink(), "A JSON record is absent, linked, or not a regular file.")
    return json.loads(Path(path).read_text())


def output_directory(path):
    path = Path(path).absolute()
    require(not any(part.is_symlink() for part in (path, *path.parents)), "An output directory contains a symbolic link.")
    path.mkdir(parents=True, exist_ok=True)
    return path


def save(path, value):
    path = Path(path)
    output_directory(path.parent)
    pending = path.with_name(path.name + ".pending")
    require(not path.is_symlink() and not pending.is_symlink(), "An output record is a symbolic link.")
    require(all(not item.exists() or item.is_file() for item in (path, pending)), "An output record is not a regular file.")
    pending.write_text(json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2) + "\n")
    pending.replace(path)


def tree(root):
    root = Path(root)
    require(root.is_dir() and not root.is_symlink(), "The evidence directory is absent or linked.")
    result = {}
    for here, dirs, files in os.walk(root, followlinks=False):
        for name in sorted(dirs + files):
            path = Path(here) / name
            require(not path.is_symlink(), "An evidence path is a symbolic link: " + str(path))
        dirs.sort()
        for name in sorted(files):
            path = Path(here) / name
            require(path.is_file(), "An evidence path is not a regular file: " + str(path))
            result[path.relative_to(root).as_posix()] = digest(path)
    return result


def say(message):
    print(message, file=sys.stderr, flush=True)


class Commands:
    """Keep native records and stop the complete active process group."""
    def __init__(self, out, seconds, command_seconds=60):
        require(all(math.isfinite(value) and 0 < value < 86400 for value in (seconds, command_seconds)),
                "Time limits must be positive and below 86,400 seconds.")
        self.out = Path(out)
        output_directory(self.out)
        self.deadline = time.monotonic() + seconds
        self.command_seconds = command_seconds
        self.number, self.active = 0, None
        self.env = dict(os.environ)
        for key in list(self.env):
            if key.startswith(("GIT_", "RIPGREP_", "SG_", "AST_GREP_", "COLGREP_", "ZOEKT_", "CTAGS_")) or key in ("PYTHONPATH", "PYTHONHOME", "FORCE_COLOR", "NODE_OPTIONS", "NODE_PATH"):
                self.env.pop(key)
        self.env.update(GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_SYSTEM="/dev/null",
                        GIT_NO_LAZY_FETCH="1", GIT_TERMINAL_PROMPT="0", GIT_OPTIONAL_LOCKS="0",
                        GIT_ATTR_NOSYSTEM="1", GIT_LFS_SKIP_SMUDGE="1", GIT_ALLOW_PROTOCOL="",
                        RIPGREP_CONFIG_PATH="/dev/null", PYTHONDONTWRITEBYTECODE="1", NO_COLOR="1", TERM="dumb")

    def check(self):
        require(time.monotonic() < self.deadline, "The total time limit was reached.")

    def stop(self):
        if self.active is None:
            return
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.killpg(self.active.pid, sig)
            except ProcessLookupError:
                pass
            try:
                self.active.wait(timeout=2)
            except subprocess.TimeoutExpired:
                pass

    def run(self, label, argv, cwd, timeout=None, accepted=(0,), environment=None):
        self.check()
        require(re.fullmatch(r"[a-zA-Z0-9_-]+", label), "The command label is invalid.")
        self.number += 1
        stem = self.out / f"{self.number:04d}-{label}"
        require(not any(stem.with_suffix(suffix).exists() or stem.with_suffix(suffix).is_symlink()
                        for suffix in (".command.json", ".stdout", ".stderr", ".result.json")),
                "A command output path already exists.")
        argv = list(map(str, argv))
        timeout = min(timeout or self.command_seconds, self.command_seconds, self.deadline - time.monotonic())
        save(stem.with_suffix(".command.json"), dict(argv=argv, cwd=str(cwd), timeout_seconds=timeout,
                                                   environment=environment or {}))
        say(f"[{self.number:04d}] {label}")
        started, state, returncode = time.monotonic(), "failed", None
        try:
            with stem.with_suffix(".stdout").open("wb") as stdout, stem.with_suffix(".stderr").open("wb") as stderr:
                self.active = subprocess.Popen(argv, cwd=cwd, env=dict(self.env, **(environment or {})), stdin=subprocess.DEVNULL,
                                               stdout=stdout, stderr=stderr, start_new_session=True)
                notice = 30
                while self.active.poll() is None:
                    elapsed = time.monotonic() - started
                    if elapsed >= timeout:
                        state = "timeout"
                        raise PrepassError(label + " reached its time limit.")
                    require(max(stem.with_suffix(suffix).stat().st_size for suffix in (".stdout", ".stderr")) <= 64 * 1024 * 1024,
                            "A native command produced too much output.")
                    if elapsed >= notice:
                        say(f"Still running {label}: {int(elapsed)} seconds.")
                        notice += 30
                    try:
                        self.active.wait(timeout=.2)
                    except subprocess.TimeoutExpired:
                        pass
            returncode = self.active.returncode
            require(max(stem.with_suffix(suffix).stat().st_size for suffix in (".stdout", ".stderr")) <= 64 * 1024 * 1024,
                    "A native command produced too much output.")
            require(accepted is None or returncode in accepted, label + " failed. Read " + str(stem.with_suffix(".stderr")))
            state = "complete"
            return dict(returncode=returncode, stdout=stem.with_suffix(".stdout").read_bytes(),
                        stderr=stem.with_suffix(".stderr").read_bytes(), seconds=time.monotonic() - started)
        except KeyboardInterrupt:
            state = "interrupted"
            raise
        finally:
            self.stop()
            returncode = self.active.returncode if self.active is not None else returncode
            self.active = None
            save(stem.with_suffix(".result.json"), dict(label=label, state=state, returncode=returncode,
                                                       seconds=time.monotonic() - started))
