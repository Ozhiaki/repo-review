from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "repo-review"


class AgentNativeCliTests(unittest.TestCase):
    def run_cli(self, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)
        return subprocess.run(
            [str(CLI), *args],
            cwd=ROOT,
            env=merged_env,
            input="",
            text=True,
            capture_output=True,
            timeout=2,
            check=False,
        )

    def assert_json_stdout(self, result: subprocess.CompletedProcess[str]) -> dict:
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        return json.loads(result.stdout)

    def assert_json_stderr(self, result: subprocess.CompletedProcess[str]) -> dict:
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        return json.loads(result.stderr)

    def test_json_commands_emit_parseable_stdout_only(self) -> None:
        for args in [
            ("agent-context", "--json"),
            ("skill-path", "--json"),
            ("status", "--json"),
            ("profile", "list", "--json", "--no-input"),
        ]:
            with self.subTest(args=args):
                payload = self.assert_json_stdout(self.run_cli(*args))
                self.assertEqual(payload["schema_version"], 1)

    def test_machine_mode_does_not_prompt(self) -> None:
        result = self.run_cli("feedback", "noninteractive test", "--json", "--no-input")
        payload = self.assert_json_stdout(result)
        self.assertIn("entry_id", payload)
        self.assertTrue(Path(payload["path"]).is_file())

    def test_actionable_error_shape_with_valid_values(self) -> None:
        diagnostic = self.assert_json_stderr(self.run_cli("unknown-command", "--json"))
        self.assertIn("code", diagnostic)
        self.assertIn("message", diagnostic)
        self.assertIn("hint", diagnostic)
        self.assertIn("valid_values", diagnostic)
        self.assertIn("agent-context", diagnostic["valid_values"])

    def test_vocabulary_policy_has_required_and_banned_terms(self) -> None:
        payload = self.assert_json_stdout(self.run_cli("agent-context", "--json"))
        policy = payload["vocabulary_policy"]
        self.assertIn("--json", policy["preferred_flags"])
        self.assertIn("--force", policy["preferred_flags"])
        self.assertIn("--overwrite", policy["preferred_flags"])
        self.assertIn("--dry-run", policy["preferred_flags"])
        self.assertIn("--format=json", policy["banned_aliases"])
        command_names = {command["name"] for command in payload["commands"]}
        self.assertFalse(command_names & {"ls", "info"})

    def test_profile_precedence_flag_env_profile_default(self) -> None:
        profile_name = "test-precedence"
        try:
            save = self.run_cli(
                "profile",
                "save",
                profile_name,
                "--repo",
                "/tmp/profile-repo",
                "--output",
                "/tmp/profile-output",
                "--analyzer-id",
                "profile-agent",
                "--json",
                "--no-input",
            )
            self.assert_json_stdout(save)

            status = self.run_cli(
                "status",
                "--profile",
                profile_name,
                "--repo",
                "/tmp/flag-repo",
                "--json",
                env={"REPO_REVIEW_REPO": "/tmp/env-repo"},
            )
            payload = self.assert_json_stdout(status)
            self.assertEqual(payload["configured_paths"]["repo_root"], "/tmp/flag-repo")
            self.assertEqual(payload["sources"]["repo_root"], "flag")
            self.assertEqual(payload["configured_paths"]["review_output_dir"], "/tmp/profile-output")
            self.assertEqual(payload["sources"]["review_output_dir"], "profile")
            self.assertEqual(payload["sources"]["lane_vocabulary_path"], "default")
        finally:
            self.run_cli("profile", "delete", profile_name, "--force", "--json", "--no-input")

    def test_safe_mutation_requires_force_for_delete(self) -> None:
        result = self.run_cli("profile", "delete", "missing", "--json", "--no-input")
        diagnostic = self.assert_json_stderr(result)
        self.assertEqual(result.returncode, 5)
        self.assertEqual(diagnostic["code"], "unsafe_mutation_refused")
        self.assertIn("--force", diagnostic["valid_values"])

    def test_diff_command_returns_bounded_json(self) -> None:
        result = self.run_cli("diff", "--range", "HEAD~1..HEAD", "--limit", "1", "--json", "--no-input")
        payload = self.assert_json_stdout(result)
        self.assertIn("changed_files", payload)
        self.assertIn("summary_stats", payload)
        self.assertEqual(payload["truncation"]["limit"], 1)
        self.assertIn("truncated", payload["truncation"])

    def test_impact_command_separates_output_buckets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            diff_path = Path(tmp) / "diff.json"
            diff = self.run_cli("diff", "--range", "HEAD~1..HEAD", "--json", "--no-input")
            diff_path.write_text(diff.stdout, encoding="utf-8")
            result = self.run_cli(
                "impact",
                "--review-state",
                "reviews/repo-review/calibration-2026-05-25/review-state.json",
                "--diff-report",
                str(diff_path),
                "--json",
                "--no-input",
            )
        payload = self.assert_json_stdout(result)
        self.assertIn("path_hits", payload)
        self.assertIn("trigger_hits", payload)
        self.assertIn("impacted_claims", payload)
        self.assertIn("unaffected_claims", payload)
        self.assertIn("unknowns", payload)

    def test_python_files_compile(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(CLI), str(ROOT / "tools/lint_pass_frontmatter.py"), str(ROOT / "tools/validate_pass_output.py")],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=2,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
