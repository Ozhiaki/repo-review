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

    def write_legacy_reviews(self, directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "01-first-read-fixture.md").write_text(
            """# First Read

Legacy prose.

```yaml
pass_output:
  pass_id: first-read
  repo: fixture
  analyzed_at: 2026-05-13T00:00:00-04:00
```
""",
            encoding="utf-8",
        )
        (directory / "03-synthesis-fixture.md").write_text(
            "# Synthesis\n\nLegacy synthesis prose without a structured appendix.\n",
            encoding="utf-8",
        )

    def candidate_claim(self, claim_id: str = "first_read.central") -> dict:
        return {
            "id": claim_id,
            "kind": "central_abstraction",
            "subject": {"type": "repo", "ref": "."},
            "statement": "The fixture repo has a durable central claim.",
            "evidence_refs": [
                {
                    "id": "ev-first-read-central",
                    "file": "../../01-first-read-fixture.md",
                    "locator": "First Read",
                    "quote": None,
                }
            ],
            "confidence": "medium",
            "claim_status": "active",
            "depends_on_claims": [],
            "related_claims": [],
            "watch_paths": ["repo-review"],
            "invalidation_triggers": ["The CLI is removed."],
            "contested_by": [],
        }

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
        helper_ids = {template["id"] for template in payload["helper_templates"]}
        self.assertIn("affected-claims", helper_ids)
        self.assertIn("trace-obligation", helper_ids)
        for template in payload["helper_templates"]:
            self.assertTrue((ROOT / template["path"]).is_file())
        self.assertEqual(payload["delivery"]["metadata_key"], "delivery_metadata")
        self.assertIn("stdout", payload["delivery_schemes"])
        self.assertIn("file:<path>", payload["delivery_schemes"])
        self.assertTrue(payload["webhook_delivery"]["deferred"])
        self.assertFalse(payload["webhook_delivery"]["supported"])

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
        result = self.run_cli("diff", "--repo", str(ROOT), "--range", "HEAD~1..HEAD", "--limit", "1", "--json", "--no-input")
        payload = self.assert_json_stdout(result)
        self.assertEqual(payload["repo"]["root"], str(ROOT))
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

    def test_export_prompt_writes_and_refuses_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            diff_path = tmp_path / "diff.json"
            impact_path = tmp_path / "impact.json"
            output_path = tmp_path / "prompt.md"
            diff = self.run_cli("diff", "--range", "HEAD~1..HEAD", "--json", "--no-input")
            diff_path.write_text(diff.stdout, encoding="utf-8")
            impact = self.run_cli(
                "impact",
                "--review-state",
                "reviews/repo-review/calibration-2026-05-25/review-state.json",
                "--diff-report",
                str(diff_path),
                "--json",
                "--no-input",
            )
            impact_path.write_text(impact.stdout, encoding="utf-8")

            dry_run = self.run_cli(
                "export-prompt",
                "--pass",
                "delta-trace",
                "--output",
                str(output_path),
                "--dry-run",
                "--json",
                "--no-input",
            )
            dry_payload = self.assert_json_stdout(dry_run)
            self.assertTrue(dry_payload["dry_run"])
            self.assertFalse(output_path.exists())

            written = self.run_cli(
                "export-prompt",
                "--pass",
                "delta-trace",
                "--review-state",
                "reviews/repo-review/calibration-2026-05-25/review-state.json",
                "--diff-report",
                str(diff_path),
                "--impact-plan",
                str(impact_path),
                "--output",
                str(output_path),
                "--json",
                "--no-input",
            )
            self.assert_json_stdout(written)
            prompt = output_path.read_text(encoding="utf-8")
            self.assertIn("Prior Review State", prompt)
            self.assertIn("Diff Report", prompt)
            self.assertIn("Impact Plan", prompt)
            self.assertIn("Conflation Guard", prompt)

            refused = self.run_cli(
                "export-prompt",
                "--pass",
                "delta-trace",
                "--review-state",
                "reviews/repo-review/calibration-2026-05-25/review-state.json",
                "--diff-report",
                str(diff_path),
                "--impact-plan",
                str(impact_path),
                "--output",
                str(output_path),
                "--json",
                "--no-input",
            )
            diagnostic = self.assert_json_stderr(refused)
            self.assertEqual(refused.returncode, 5)
            self.assertIn("--overwrite", diagnostic["valid_values"])

            stdout_delivery = self.run_cli(
                "export-prompt",
                "--pass",
                "delta-trace",
                "--review-state",
                "reviews/repo-review/calibration-2026-05-25/review-state.json",
                "--diff-report",
                str(diff_path),
                "--impact-plan",
                str(impact_path),
                "--deliver",
                "stdout",
                "--json",
                "--no-input",
            )
            stdout_payload = self.assert_json_stdout(stdout_delivery)
            self.assertEqual(stdout_payload["delivery"], "stdout")
            self.assertEqual(stdout_payload["delivery_metadata"]["scheme"], "stdout")
            self.assertIsNone(stdout_payload["delivery_metadata"]["path"])
            self.assertIn("Conflation Guard", stdout_payload["artifact"])

            delivered_path = tmp_path / "delivered.md"
            file_delivery = self.run_cli(
                "export-prompt",
                "--pass",
                "delta-trace",
                "--review-state",
                "reviews/repo-review/calibration-2026-05-25/review-state.json",
                "--diff-report",
                str(diff_path),
                "--impact-plan",
                str(impact_path),
                f"--deliver=file:{delivered_path}",
                "--json",
                "--no-input",
            )
            file_payload = self.assert_json_stdout(file_delivery)
            self.assertEqual(file_payload["delivery"], f"file:{delivered_path}")
            self.assertEqual(file_payload["delivery_metadata"]["scheme"], "file")
            self.assertEqual(file_payload["delivery_metadata"]["path"], str(delivered_path))
            self.assertIn("Conflation Guard", delivered_path.read_text(encoding="utf-8"))

            refused_file_delivery = self.run_cli(
                "export-prompt",
                "--pass",
                "delta-trace",
                "--review-state",
                "reviews/repo-review/calibration-2026-05-25/review-state.json",
                "--diff-report",
                str(diff_path),
                "--impact-plan",
                str(impact_path),
                f"--deliver=file:{delivered_path}",
                "--json",
                "--no-input",
            )
            file_diagnostic = self.assert_json_stderr(refused_file_delivery)
            self.assertEqual(refused_file_delivery.returncode, 5)
            self.assertIn("--overwrite", file_diagnostic["valid_values"])

            webhook_delivery = self.run_cli(
                "export-prompt",
                "--pass",
                "delta-trace",
                "--deliver=webhook:https://example.invalid/repo-review",
                "--json",
                "--no-input",
            )
            webhook_diagnostic = self.assert_json_stderr(webhook_delivery)
            self.assertEqual(webhook_delivery.returncode, 2)
            self.assertIn("deferred", webhook_diagnostic["message"])

            missing_file_path = self.run_cli(
                "export-prompt",
                "--pass",
                "delta-trace",
                "--deliver=file:",
                "--json",
                "--no-input",
            )
            missing_file_diagnostic = self.assert_json_stderr(missing_file_path)
            self.assertEqual(missing_file_path.returncode, 2)
            self.assertIn("file:<path>", missing_file_diagnostic["valid_values"])

    def test_drift_surface_outputs_delta_drift_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            diff_path = Path(tmp) / "diff.json"
            impact_path = Path(tmp) / "impact.json"
            diff = self.run_cli("diff", "--range", "HEAD~1..HEAD", "--json", "--no-input")
            diff_path.write_text(diff.stdout, encoding="utf-8")
            impact = self.run_cli(
                "impact",
                "--review-state",
                "reviews/repo-review/calibration-2026-05-25/review-state.json",
                "--diff-report",
                str(diff_path),
                "--json",
                "--no-input",
            )
            impact_path.write_text(impact.stdout, encoding="utf-8")
            result = self.run_cli(
                "drift",
                "surface",
                "--review-state",
                "reviews/repo-review/calibration-2026-05-25/review-state.json",
                "--diff-report",
                str(diff_path),
                "--impact-plan",
                str(impact_path),
                "--to-review",
                "repo-review-delta-test",
                "--json",
                "--no-input",
            )
        payload = self.assert_json_stdout(result)
        self.assertEqual(payload["from_review"], "repo-review-calibration-2026-05-25")
        self.assertEqual(payload["to_review"], "repo-review-delta-test")
        self.assertIn("produced_by_analyzer", payload)
        self.assertIn("new_snapshot_entries", payload)
        self.assertIn("invalidated_snapshot_entries", payload)
        self.assertIn("strengthened_fascination_seeds", payload)
        self.assertIn("weakened_fascination_seeds", payload)
        self.assertIn("new_fascination_seeds", payload)
        self.assertIn("lane_impacts", payload)

    def test_next_ingest_delta_commands(self) -> None:
        next_payload = self.assert_json_stdout(self.run_cli("next", "--json", "--no-input"))
        self.assertIn("next_action", next_payload)
        self.assertIn("required_inputs", next_payload)
        self.assertIn("missing_inputs", next_payload)
        self.assertIn("recommended_command", next_payload)

        ingest = self.run_cli(
            "ingest",
            "--input",
            "reviews/oathweaver/delta-2026-05-25/delta-review.md",
            "--kind",
            "delta-review",
            "--json",
            "--no-input",
        )
        ingest_payload = self.assert_json_stdout(ingest)
        self.assertIn("entry_id", ingest_payload)
        self.assertTrue(Path(ingest_payload["path"]).is_file())

        delta = self.run_cli("delta", "--json", "--no-input")
        delta_payload = self.assert_json_stdout(delta)
        self.assertFalse(delta_payload["executes_analysis"])
        self.assertTrue(delta_payload["jobs_deferred"])

        wait = self.run_cli("delta", "--wait", "--json", "--no-input")
        diagnostic = self.assert_json_stderr(wait)
        self.assertIn("deferred", diagnostic["message"])

    def test_claims_commands_use_scoped_ids(self) -> None:
        state = "reviews/oathweaver/delta-2026-05-25/prior-review-state.json"
        impact = "reviews/oathweaver/delta-2026-05-25/impact-plan.json"
        listed = self.assert_json_stdout(
            self.run_cli("claims", "list", "--review-state", state, "--claim-status", "active", "--limit", "1", "--json", "--no-input")
        )
        self.assertEqual(listed["truncation"]["limit"], 1)
        qualified_id = listed["claims"][0]["qualified_claim_id"]
        self.assertIn(":", qualified_id)

        got = self.assert_json_stdout(self.run_cli("claims", "get", qualified_id, "--review-state", state, "--json", "--no-input"))
        self.assertEqual(got["qualified_claim_id"], qualified_id)
        self.assertIn("evidence_refs", got["claim"])

        affected = self.assert_json_stdout(self.run_cli("claims", "affected", "--impact-plan", impact, "--json", "--no-input"))
        self.assertIn("affected_claims", affected)
        self.assertIn("qualified_claim_id", affected["affected_claims"][0])

    def test_state_bootstrap_dry_run_write_and_overwrite_refusal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            review_dir = tmp_path / "legacy"
            output_path = tmp_path / "reviews" / "fixture" / "full-2026-05-13" / "review-state.json"
            sidecar_path = output_path.with_name("review-state.bootstrap.json")
            self.write_legacy_reviews(review_dir)

            dry_run = self.run_cli(
                "state",
                "bootstrap",
                "--repo",
                str(ROOT),
                "--review-dir",
                str(review_dir),
                "--output",
                str(output_path),
                "--source-analyzer-id",
                "claude-2026-05-13-fixture",
                "--source-kind",
                "llm",
                "--source-model",
                "claude-opus-4",
                "--source-tool-context",
                "claude.ai",
                "--dry-run",
                "--json",
                "--no-input",
            )
            dry_payload = self.assert_json_stdout(dry_run)
            self.assertFalse(dry_payload["created"])
            self.assertEqual(dry_payload["pass_outputs"], 2)
            self.assertFalse(output_path.exists())
            self.assertFalse(sidecar_path.exists())
            self.assertTrue(any("no structured pass_output" in warning for warning in dry_payload["warnings"]))

            written = self.run_cli(
                "state",
                "bootstrap",
                "--repo",
                str(ROOT),
                "--review-dir",
                str(review_dir),
                "--output",
                str(output_path),
                "--review-state-id",
                "fixture-full-2026-05-13",
                "--source-analyzer-id",
                "claude-2026-05-13-fixture",
                "--source-kind",
                "llm",
                "--source-model",
                "claude-opus-4",
                "--source-tool-context",
                "claude.ai",
                "--json",
                "--no-input",
            )
            payload = self.assert_json_stdout(written)
            self.assertTrue(payload["created"])
            self.assertTrue(output_path.is_file())
            self.assertTrue(sidecar_path.is_file())
            state = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(state["id"], "fixture-full-2026-05-13")
            self.assertEqual(state["claims"], [])
            self.assertIsNone(state["drift_surface"])
            self.assertEqual(state["produced_by_analyzer"]["id"], "claude-2026-05-13-fixture")
            self.assertEqual(len(state["pass_outputs"]), 2)
            self.assertIn("some-pass-outputs-lack-structured-appendix", state["limits"])

            aggregate = self.run_cli("aggregate", "--review-state", str(output_path), "--json", "--no-input")
            aggregate_payload = self.assert_json_stdout(aggregate)
            self.assertEqual(aggregate_payload["review_state_count"], 1)

            refused = self.run_cli(
                "state",
                "bootstrap",
                "--repo",
                str(ROOT),
                "--review-dir",
                str(review_dir),
                "--output",
                str(output_path),
                "--json",
                "--no-input",
            )
            diagnostic = self.assert_json_stderr(refused)
            self.assertEqual(refused.returncode, 5)
            self.assertIn("--overwrite", diagnostic["valid_values"])

    def test_state_bootstrap_unknown_source_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            review_dir = tmp_path / "legacy"
            output_path = tmp_path / "review-state.json"
            self.write_legacy_reviews(review_dir)
            result = self.run_cli(
                "state",
                "bootstrap",
                "--repo",
                str(ROOT),
                "--review-dir",
                str(review_dir),
                "--output",
                str(output_path),
                "--json",
                "--no-input",
            )
            payload = self.assert_json_stdout(result)
            state = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(state["produced_by_analyzer"]["id"], "unknown-pre-bootstrap")
            self.assertEqual(state["produced_by_analyzer"]["kind"], "unknown")
            self.assertIn("source-reviewer-identity-unknown", state["limits"])
            self.assertTrue(any("unknown-pre-bootstrap" in warning for warning in payload["warnings"]))

    def test_claims_import_inherits_identity_audits_and_supports_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            review_dir = tmp_path / "legacy"
            state_path = tmp_path / "review-state.json"
            candidate_path = tmp_path / "candidate-claims.json"
            self.write_legacy_reviews(review_dir)
            self.assert_json_stdout(
                self.run_cli(
                    "state",
                    "bootstrap",
                    "--repo",
                    str(ROOT),
                    "--review-dir",
                    str(review_dir),
                    "--output",
                    str(state_path),
                    "--review-state-id",
                    "fixture-full-2026-05-13",
                    "--json",
                    "--no-input",
                )
            )
            candidate_file = {
                "schema_version": 1,
                "review_state": "fixture-full-2026-05-13",
                "produced_by_analyzer": {
                    "id": "dave-2026-05-27-fixture-claims",
                    "kind": "human",
                    "model": None,
                    "tool_context": "manual claim selection from pre-v1 prose",
                    "prompt_set_version": "repo-review-v1",
                    "notes": "Fixture claim selection.",
                },
                "candidate_claims": [self.candidate_claim()],
                "warnings": [],
            }
            candidate_path.write_text(json.dumps(candidate_file), encoding="utf-8")

            imported = self.run_cli(
                "claims",
                "import",
                "--review-state",
                str(state_path),
                "--input",
                str(candidate_path),
                "--json",
                "--no-input",
            )
            import_payload = self.assert_json_stdout(imported)
            self.assertEqual(import_payload["imported"], 1)
            self.assertEqual(import_payload["replaced"], 0)
            self.assertTrue(Path(import_payload["audit_log"]).is_file())
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(len(state["claims"]), 1)
            self.assertEqual(state["claims"][0]["produced_by_analyzer"]["id"], "dave-2026-05-27-fixture-claims")

            listed = self.assert_json_stdout(self.run_cli("claims", "list", "--review-state", str(state_path), "--json", "--no-input"))
            self.assertEqual(listed["claims"][0]["id"], "first_read.central")
            got = self.assert_json_stdout(
                self.run_cli("claims", "get", "fixture-full-2026-05-13:first_read.central", "--review-state", str(state_path), "--json", "--no-input")
            )
            self.assertEqual(got["claim"]["id"], "first_read.central")

            duplicate = self.run_cli(
                "claims",
                "import",
                "--review-state",
                str(state_path),
                "--input",
                str(candidate_path),
                "--json",
                "--no-input",
            )
            duplicate_diagnostic = self.assert_json_stderr(duplicate)
            self.assertEqual(duplicate.returncode, 5)
            self.assertIn("--overwrite-claims", duplicate_diagnostic["valid_values"])

            candidate_file["candidate_claims"][0]["statement"] = "The updated fixture claim replaces only the matching claim."
            candidate_path.write_text(json.dumps(candidate_file), encoding="utf-8")
            overwritten = self.run_cli(
                "claims",
                "import",
                "--review-state",
                str(state_path),
                "--input",
                str(candidate_path),
                "--overwrite-claims",
                "--json",
                "--no-input",
            )
            overwrite_payload = self.assert_json_stdout(overwritten)
            self.assertEqual(overwrite_payload["replaced"], 1)
            updated_state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(len(updated_state["claims"]), 1)
            self.assertEqual(updated_state["claims"][0]["statement"], "The updated fixture claim replaces only the matching claim.")

    def test_claims_import_refuses_mismatched_review_state_and_invalid_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            review_dir = tmp_path / "legacy"
            state_path = tmp_path / "review-state.json"
            candidate_path = tmp_path / "candidate-claims.json"
            self.write_legacy_reviews(review_dir)
            self.assert_json_stdout(
                self.run_cli(
                    "state",
                    "bootstrap",
                    "--repo",
                    str(ROOT),
                    "--review-dir",
                    str(review_dir),
                    "--output",
                    str(state_path),
                    "--review-state-id",
                    "fixture-full-2026-05-13",
                    "--json",
                    "--no-input",
                )
            )
            candidate_file = {
                "schema_version": 1,
                "review_state": "other-review",
                "produced_by_analyzer": {
                    "id": "dave-2026-05-27-fixture-claims",
                    "kind": "human",
                    "model": None,
                    "tool_context": "manual claim selection from pre-v1 prose",
                    "prompt_set_version": "repo-review-v1",
                    "notes": None,
                },
                "candidate_claims": [self.candidate_claim()],
                "warnings": [],
            }
            candidate_path.write_text(json.dumps(candidate_file), encoding="utf-8")
            mismatched = self.run_cli(
                "claims",
                "import",
                "--review-state",
                str(state_path),
                "--input",
                str(candidate_path),
                "--json",
                "--no-input",
            )
            mismatch_diagnostic = self.assert_json_stderr(mismatched)
            self.assertEqual(mismatched.returncode, 3)
            self.assertIn("--force", mismatch_diagnostic["valid_values"])

            candidate_file["review_state"] = "fixture-full-2026-05-13"
            del candidate_file["candidate_claims"][0]["statement"]
            candidate_path.write_text(json.dumps(candidate_file), encoding="utf-8")
            invalid = self.run_cli(
                "claims",
                "import",
                "--review-state",
                str(state_path),
                "--input",
                str(candidate_path),
                "--json",
                "--no-input",
            )
            invalid_diagnostic = self.assert_json_stderr(invalid)
            self.assertEqual(invalid.returncode, 3)
            self.assertIn("candidate_claims[0].statement", invalid_diagnostic["hint"])

    def test_aggregate_reads_multiple_review_states_without_global_claim_identity(self) -> None:
        result = self.run_cli(
            "aggregate",
            "--review-state",
            "reviews/repo-review/calibration-2026-05-25/review-state.json",
            "--review-state",
            "reviews/oathweaver/delta-2026-05-25/prior-review-state.json",
            "--drift",
            "reviews/oathweaver/delta-2026-05-25/delta-drift.json",
            "--json",
            "--no-input",
        )
        payload = self.assert_json_stdout(result)
        self.assertEqual(payload["review_state_count"], 2)
        self.assertIn("active", payload["totals"]["claim_status_counts"])
        self.assertGreaterEqual(payload["totals"]["analyzer_count"], 2)
        self.assertEqual(payload["totals"]["drift_output_count"], 1)
        self.assertGreater(payload["drift_material"]["counts"]["strengthened_fascination_seeds"], 0)
        self.assertFalse(payload["claim_identity"]["global_claim_identity_supported"])
        for review_state in payload["review_states"]:
            self.assertTrue(all(":" in claim_id for claim_id in review_state["sample_qualified_claim_ids"]))

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
