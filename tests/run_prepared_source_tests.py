#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Terminal checks for the candidate source package. Included in step 5 acceptance."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

sys.dont_write_bytecode = True
PROJECT = Path(__file__).resolve().parents[1]
ENTRY = PROJECT / "tools/prepass/source_package.py"
sys.path.insert(0, str(PROJECT / "tools/prepass"))
from prepass_runtime import records as r


class SourcePackageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="prepass-integration-")
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name).resolve()
        self.repo, self.out = self.home / "source", self.home / "output"
        self.commands = r.Commands(self.home / "caller-commands", 1200, 60)
        self.addCleanup(self.commands.stop)
        self.repo.mkdir()
        self.git("init", "-b", "main")
        self.put(".gitignore", "ignored/\n")
        self.put("tracked.py", "def sample():\n    return 1\n")
        self.put("absent.py", "missing = 1\n")
        self.git("add", ".")
        self.git("-c", "user.name=Prepass fixture", "-c", "user.email=fixture@example.invalid", "commit", "-m", "Fixture")
        (self.repo / "absent.py").unlink()

    def put(self, name, content):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content if isinstance(content, bytes) else content.encode())

    def git(self, *args):
        return self.commands.run("fixture-git", ["git", "-C", self.repo, *args], self.home)["stdout"]

    def cli(self, *args, code=0):
        result = self.commands.run("candidate-cli", [sys.executable, ENTRY, *args], self.home, accepted=None)
        self.assertEqual(result["returncode"], code, result["stdout"].decode(errors="replace") + result["stderr"].decode(errors="replace"))
        return result

    def prepare(self):
        self.cli("prepare", self.repo, self.out)

    def json(self, name):
        return json.loads((self.out / name).read_text())

    def test_exact_source_scope_and_preservation(self):
        odd = "tests/space ü/line\nname.py"
        self.put(odd, "value = 2\n")
        self.put("empty.py", b"")
        self.put("binary.py", b"\0source")
        self.put("ignored/private.py", "excluded = True\n")
        self.put(".hidden.py", "hidden = 1\n")
        self.put("non-utf8.py", b"\xff\n")
        os.symlink("tracked.py", self.repo / "linked.py")
        before = self.git("status", "--porcelain=v1", "-z", "--untracked-files=all")
        index = (self.repo / ".git/index").read_bytes()
        self.prepare()
        self.assertEqual(before, self.git("status", "--porcelain=v1", "-z", "--untracked-files=all"))
        self.assertEqual(index, (self.repo / ".git/index").read_bytes())
        rows = {row["path"]: row for row in self.json("evidence/inventory.json")["records"]}
        self.assertEqual(rows["linked.py"]["status"], "symlink")
        self.assertEqual(rows["absent.py"]["status"], "missing")
        self.assertEqual(rows["ignored/private.py"]["status"], "ignored")
        self.assertFalse((self.out / "evidence/source/linked.py").exists())
        self.assertFalse((self.out / "evidence/source/ignored/private.py").exists())
        for name in (odd, "empty.py", "binary.py", ".hidden.py", "non-utf8.py", "tracked.py"):
            original = (self.repo / name).read_bytes()
            self.assertEqual((self.out / "evidence/source" / name).read_bytes(), original)
            self.assertEqual(rows[name]["sha256"], hashlib.sha256(original).hexdigest())
        self.assertEqual(self.json("status.json")["state"], "foundation_complete")
        self.assertFalse(self.json("status.json")["review_ready"])

    def test_freshness_state_does_not_change_the_seal(self):
        self.prepare()
        seal = (self.out / "evidence/seal.json").read_bytes()
        self.cli("check", self.out)
        self.assertEqual(self.json("state/freshness.json")["state"], "fresh")
        (self.out / "state/deliveries").mkdir()
        (self.out / "state/deliveries/record.json").write_text("{}\n")
        self.cli("check", self.out)
        self.assertEqual(seal, (self.out / "evidence/seal.json").read_bytes())
        self.put("tracked.py", "def sample():\n    return 2\n")
        self.cli("check", self.out, code=1)
        result = self.json("state/freshness.json")
        self.assertEqual(result["state"], "stale")
        self.assertIn("source_state", result["changed"])
        self.assertEqual((self.out / "evidence/source/tracked.py").read_text(), "def sample():\n    return 1\n")

    def test_changed_evidence_fails_without_a_new_native_command(self):
        self.prepare()
        (self.out / "evidence/facts.md").write_text("changed\n")
        self.cli("check", self.out, code=1)
        self.assertEqual(self.json("state/freshness.json")["changed"], ["package_artifacts"])
        self.assertFalse(list((self.out / "state/checks").rglob("*.command.json")))

    def test_ignored_content_edit_keeps_freshness(self):
        self.put("ignored/private.py", "value = 1\n")
        self.prepare()
        self.put("ignored/private.py", "value = 2\n")
        self.cli("check", self.out)
        self.assertEqual(self.json("state/freshness.json")["state"], "fresh")

    def test_damaged_metadata_replaces_previous_fresh_state(self):
        self.prepare()
        self.cli("check", self.out)
        (self.out / "evidence/meta.json").write_text("invalid json\n")
        self.cli("check", self.out, code=1)
        self.assertEqual(self.json("state/freshness.json")["state"], "unverifiable")

    def test_mutable_state_links_cannot_write_into_the_source(self):
        self.prepare()
        before = r.tree(self.repo)
        os.symlink(self.repo, self.out / "state/checks")
        self.cli("check", self.out, code=1)
        self.assertEqual(before, r.tree(self.repo))
        self.assertEqual(self.json("state/freshness.json")["state"], "unverifiable")

    def test_missing_git_has_a_visible_failed_record(self):
        outside = self.home / "not-git"
        outside.mkdir()
        self.cli("prepare", outside, self.out, code=1)
        self.assertEqual(self.json("status.json")["state"], "failed")
        self.assertFalse((self.out / "evidence/seal.json").exists())
        results = [json.loads(path.read_text()) for path in (self.out / "evidence/commands").glob("*.result.json")]
        self.assertTrue(any(row["returncode"] != 0 for row in results))

    def test_existing_and_source_outputs_are_rejected(self):
        self.cli("prepare", self.repo, self.repo / "output", code=1)
        self.assertFalse((self.repo / "output").exists())
        self.out.mkdir()
        marker = self.out / "keep"
        marker.write_bytes(b"unchanged")
        self.cli("prepare", self.repo, self.out, code=1)
        self.assertEqual(marker.read_bytes(), b"unchanged")

    def test_parser_rejects_invalid_time_limits(self):
        for value in ("0", "-1", "nan", "inf", "86400", "text"):
            with self.subTest(value=value):
                self.cli("prepare", self.repo, self.out, "--total-timeout", value, code=2)
        self.assertFalse(self.out.exists())

    def test_timeout_stops_descendant_processes(self):
        pid_file = self.home / "child.pid"
        program = ("import subprocess,sys,time; from pathlib import Path; "
                   "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); "
                   "Path(sys.argv[1]).write_text(str(child.pid)); time.sleep(60)")
        with self.assertRaises(r.PrepassError):
            self.commands.run("timeout-group", [sys.executable, "-c", program, pid_file], self.home, timeout=1)
        self.assertTrue(pid_file.is_file())
        pid = pid_file.read_text().strip()
        stopped = False
        for _ in range(60):
            state = self.commands.run("descendant-state", ["ps", "-p", pid, "-o", "stat="], self.home, accepted=(0, 1))["stdout"].strip()
            if not state or state.startswith(b"Z"):
                stopped = True
                break
            time.sleep(.05)
        self.assertTrue(stopped, "A timed-out native command left a running descendant.")


if __name__ == "__main__":
    r.install_interrupt_handler()
    unittest.main()
