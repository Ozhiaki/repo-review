from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path
from types import ModuleType


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

    def assert_human_stderr(self, result: subprocess.CompletedProcess[str], expected_text: str) -> str:
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn(expected_text, result.stderr)
        with self.assertRaises(json.JSONDecodeError):
            json.loads(result.stderr)
        return result.stderr

    def assert_human_stdout(self, result: subprocess.CompletedProcess[str], expected_text: str) -> str:
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertIn(expected_text, result.stdout)
        with self.assertRaises(json.JSONDecodeError):
            json.loads(result.stdout)
        return result.stdout

    def assert_has_keys(self, payload: dict, keys: set[str]) -> None:
        self.assertTrue(keys <= payload.keys(), f"missing keys: {sorted(keys - payload.keys())}")

    def load_cli_module(self) -> ModuleType:
        loader = SourceFileLoader("repo_review_cli", str(CLI))
        spec = importlib.util.spec_from_loader("repo_review_cli", loader)
        self.assertIsNotNone(spec)
        assert spec is not None
        self.assertIsNotNone(spec.loader)
        assert spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

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

    def test_representative_json_success_contract_fields(self) -> None:
        cases = [
            (("agent-context", "--json"), {"schema_version", "commands", "vocabulary_policy", "delivery_schemes"}),
            (("skill-path", "--json"), {"schema_version", "path", "manifest"}),
            (("status", "--json"), {"schema_version", "configured_paths", "sources", "next_actions"}),
            (("profile", "list", "--json", "--no-input"), {"schema_version", "profiles"}),
            (
                ("diff", "--repo", str(ROOT), "--range", "HEAD~1..HEAD", "--limit", "1", "--json", "--no-input"),
                {"schema_version", "repo", "range", "changed_files", "summary_stats", "truncation"},
            ),
            (
                (
                    "claims",
                    "list",
                    "--review-state",
                    "reviews/oathweaver/delta-2026-05-25/prior-review-state.json",
                    "--limit",
                    "1",
                    "--json",
                    "--no-input",
                ),
                {"schema_version", "review_state", "claims", "truncation"},
            ),
            (
                (
                    "aggregate",
                    "--review-state",
                    "reviews/repo-review/calibration-2026-05-25/review-state.json",
                    "--json",
                    "--no-input",
                ),
                {"schema_version", "review_state_count", "review_states", "totals", "claim_identity"},
            ),
        ]
        for args, required_keys in cases:
            with self.subTest(args=args):
                payload = self.assert_json_stdout(self.run_cli(*args))
                self.assert_has_keys(payload, required_keys)

    def test_json_failure_contract_keeps_stdout_empty(self) -> None:
        cases = [
            (("unknown-command", "--json"), "invalid_invocation", "unknown command"),
            (("impact", "--json", "--no-input"), "invalid_invocation", "missing required --review-state"),
            (
                ("export-prompt", "--pass", "delta-trace", "--deliver=file:", "--json", "--no-input"),
                "invalid_invocation",
                "missing file delivery path",
            ),
        ]
        for args, expected_code, expected_message in cases:
            with self.subTest(args=args):
                diagnostic = self.assert_json_stderr(self.run_cli(*args))
                self.assertEqual(diagnostic["code"], expected_code)
                self.assertIn(expected_message, diagnostic["message"])
                self.assertIn("hint", diagnostic)

    def test_targeted_commands_emit_human_output_without_json(self) -> None:
        self.assert_human_stdout(self.run_cli("status"), "Repo-review status")
        self.assert_human_stdout(
            self.run_cli("diff", "--repo", str(ROOT), "--range", "HEAD~1..HEAD", "--limit", "1", "--no-input"),
            "Diff report",
        )
        self.assert_human_stdout(
            self.run_cli(
                "impact",
                "--review-state",
                "reviews/repo-review/calibration-2026-05-25/review-state.json",
                "--diff-report",
                "reviews/oathweaver/delta-2026-05-25/diff-report.json",
                "--no-input",
            ),
            "Impact plan",
        )
        self.assert_human_stdout(
            self.run_cli(
                "claims",
                "list",
                "--review-state",
                "reviews/oathweaver/delta-2026-05-25/prior-review-state.json",
                "--limit",
                "1",
                "--no-input",
            ),
            "Claims",
        )
        self.assert_human_stdout(
            self.run_cli(
                "aggregate",
                "--review-state",
                "reviews/repo-review/calibration-2026-05-25/review-state.json",
                "--no-input",
            ),
            "Aggregate",
        )
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            review_dir = tmp_path / "legacy"
            output_path = tmp_path / "review-state.json"
            self.write_legacy_reviews(review_dir)
            self.assert_human_stdout(
                self.run_cli(
                    "state",
                    "bootstrap",
                    "--repo",
                    str(ROOT),
                    "--review-dir",
                    str(review_dir),
                    "--output",
                    str(output_path),
                    "--dry-run",
                    "--no-input",
                ),
                "State bootstrap dry run",
            )
            self.assert_human_stdout(
                self.run_cli(
                    "export-prompt",
                    "--pass",
                    "delta-trace",
                    "--output",
                    str(tmp_path / "prompt.md"),
                    "--dry-run",
                    "--no-input",
                ),
                "Prompt packet dry run",
            )

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

    def test_actionable_diagnostics_cover_enum_paths_and_human_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            wrong_artifact = tmp_path / "diff-report.json"
            wrong_artifact.write_text(
                json.dumps({"schema_version": 1, "range": {}, "changed_files": []}),
                encoding="utf-8",
            )
            missing_state = tmp_path / "missing-review-state.json"

            enum_diagnostic = self.assert_json_stderr(
                self.run_cli("export-prompt", "--pass", "wrong", "--output", str(tmp_path / "prompt.md"), "--json", "--no-input")
            )
            self.assertEqual(enum_diagnostic["code"], "invalid_invocation")
            self.assertIn("delta-trace", enum_diagnostic["valid_values"])

            missing_path = self.assert_json_stderr(
                self.run_cli(
                    "impact",
                    "--review-state",
                    str(missing_state),
                    "--diff-report",
                    "reviews/oathweaver/delta-2026-05-25/diff-report.json",
                    "--json",
                    "--no-input",
                )
            )
            self.assertEqual(missing_path["code"], "resource_not_found")
            self.assertEqual(missing_path["path"], str(missing_state))
            self.assertEqual(missing_path["expected_artifact_kind"], "review-state")

            wrong_kind = self.assert_json_stderr(
                self.run_cli(
                    "impact",
                    "--review-state",
                    str(wrong_artifact),
                    "--diff-report",
                    "reviews/oathweaver/delta-2026-05-25/diff-report.json",
                    "--json",
                    "--no-input",
                )
            )
            self.assertEqual(wrong_kind["code"], "validation_failed")
            self.assertIn("wrong artifact kind", wrong_kind["message"])
            self.assertEqual(wrong_kind["expected_artifact_kind"], "review-state")

        human_diagnostic = self.assert_human_stderr(self.run_cli("impact", "--no-input"), "Error:")
        self.assertIn("Hint:", human_diagnostic)
        self.assertIn("--review-state", human_diagnostic)
        self.assert_human_stderr(self.run_cli("skill-path"), "skill-path requires --json")

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

    def test_agent_context_exposes_richer_command_schema(self) -> None:
        payload = self.assert_json_stdout(self.run_cli("agent-context", "--json"))
        schema = {command["name"]: command for command in payload["command_schema"]}
        self.assertIn("diff", schema)
        self.assertIn("review start", schema)
        self.assertIn("runs prune", schema)

        diff = schema["diff"]
        self.assertTrue(diff["implemented"])
        self.assertFalse(diff["mutation"])
        self.assertEqual(diff["flags"]["--limit"]["type"], "integer")
        self.assertEqual(diff["output_schema"], "schemas/diff_report.schema.json")
        self.assertIn("repo-review diff", diff["examples"][0])

        review_start = schema["review start"]
        self.assertFalse(review_start["implemented"])
        self.assertTrue(review_start["mutation"])
        self.assertTrue(review_start["dry_run"])
        self.assertEqual(review_start["workflow_role"], "entrypoint")
        self.assertEqual(review_start["flags"]["--mode"]["type"], "enum")
        self.assertIn("delta", review_start["flags"]["--mode"]["values"])
        self.assertEqual(review_start["idempotency"]["natural_key_by_mode"]["delta"], ["repo", "range", "review_state"])

        export_prompt = schema["export-prompt"]
        self.assertTrue(export_prompt["mutation"])
        self.assertTrue(export_prompt["dry_run"])
        self.assertEqual(export_prompt["flags"]["--deliver"]["type"], "delivery-scheme")

        self.assertEqual(review_start["output_schema"], "schemas/review_run.schema.json")
        self.assertEqual(schema["runs get"]["output_schema"], "schemas/review_run.schema.json")

        shipped_command_names = {command["name"] for command in payload["commands"]}
        self.assertNotIn("review start", shipped_command_names)

    def test_review_run_schema_and_migration_helpers(self) -> None:
        self.assertTrue((ROOT / "schemas/review_run.schema.json").is_file())
        cli = self.load_cli_module()
        run = {
            "schema_version": 1,
            "run_id": "repo-review-delta-2026-05-27-abc123",
            "mode": "delta",
            "status": "prompt_ready",
            "repo": {
                "name": "repo-review",
                "root": str(ROOT),
                "remote": None,
                "commit": "abc123",
            },
            "range": "HEAD~1..HEAD",
            "prior_review_state": "reviews/repo-review/full-2026-05-13/review-state.json",
            "output_dir": "reviews/repo-review/delta-2026-05-27",
            "artifacts": {
                "diff_report": "diff-report.json",
                "impact_plan": "impact-plan.json",
                "prompt_packet": "delta-trace-prompt.md",
                "review_artifact": None,
                "drift_surface": None,
            },
            "human_decisions": [],
            "warnings": [],
            "created_at": "2026-05-27T00:00:00Z",
            "updated_at": "2026-05-27T00:00:00Z",
        }
        migrated, migration_errors = cli.migrate_review_run_record(run)
        self.assertEqual(migration_errors, [])
        self.assertEqual(migrated, run)
        self.assertEqual(cli.validate_review_run_shape(run), [])

        future_run = {**run, "schema_version": 99}
        migrated, migration_errors = cli.migrate_review_run_record(future_run)
        self.assertIsNone(migrated)
        self.assertIn("newer than this CLI supports", migration_errors[0])
        self.assertIn("newer than this CLI supports", cli.validate_review_run_shape(future_run)[0])

        invalid_run = {**run, "status": "unknown", "repo": {"name": "repo-review"}}
        validation_errors = cli.validate_review_run_shape(invalid_run)
        self.assertTrue(any("status must be one of" in error for error in validation_errors))
        self.assertTrue(any("repo.root is required" in error for error in validation_errors))

    def test_review_run_transition_contracts_are_discoverable(self) -> None:
        cli = self.load_cli_module()
        payload = self.assert_json_stdout(self.run_cli("agent-context", "--json"))
        review_run = payload["review_run"]
        self.assertEqual(review_run["schema"], "schemas/review_run.schema.json")
        self.assertEqual(set(review_run["statuses"]), set(cli.REVIEW_RUN_STATUSES))
        for status in cli.REVIEW_RUN_STATUSES:
            with self.subTest(status=status):
                contract = review_run["statuses"][status]
                self.assertIn("meaning", contract)
                self.assertIn("next_action", contract)
                action = cli.review_run_next_action(status)
                self.assertEqual(action["next_action"], contract["next_action"])

        transitions = {(transition["from"], transition["to"]): transition["producer"] for transition in review_run["transitions"]}
        self.assertEqual(transitions[(None, "created")], "review start")
        self.assertIn("review ingest", transitions[("review_received", "ingested")])
        self.assertIn("review finish", transitions[("drift_ready", "complete")])
        self.assertIn("human-decision", transitions[("*", "blocked")])
        self.assertIn("recovery hint", transitions[("*", "failed")])
        self.assertIsNone(review_run["statuses"]["blocked"]["recommended_command"])
        self.assertIsNone(review_run["statuses"]["failed"]["recommended_command"])

    def test_mutation_outcome_contracts_are_recorded_per_command(self) -> None:
        payload = self.assert_json_stdout(self.run_cli("agent-context", "--json"))
        schema = {command["name"]: command for command in payload["command_schema"]}
        allowed_outcomes = set(payload["mutation_outcomes"])
        self.assertEqual(
            allowed_outcomes,
            {"created", "updated", "existing", "imported", "replaced", "unchanged", "dry_run"},
        )

        expected = {
            "state": {"created", "existing", "replaced", "dry_run"},
            "claims": {"created", "updated", "existing", "imported", "replaced", "unchanged", "dry_run"},
            "review start": {"created", "existing", "updated", "dry_run"},
            "review package": {"created", "existing", "updated", "dry_run"},
            "review ingest": {"created", "updated", "existing", "imported", "unchanged", "dry_run"},
            "review finish": {"updated", "unchanged", "dry_run"},
            "runs prune": {"updated", "unchanged", "dry_run"},
        }
        for command_name, outcomes in expected.items():
            with self.subTest(command=command_name):
                command = schema[command_name]
                self.assertTrue(command["mutation"])
                self.assertTrue(set(command["allowed_mutation_outcomes"]) <= allowed_outcomes)
                self.assertEqual(set(command["allowed_mutation_outcomes"]), outcomes)
                if command["dry_run"]:
                    self.assertIn("dry_run", command["allowed_mutation_outcomes"])

        read_only_commands = [
            "diff",
            "impact",
            "state validate",
            "state latest",
            "state list",
            "state get",
            "runs list",
            "runs get",
            "review status",
        ]
        for command_name in read_only_commands:
            with self.subTest(command=command_name):
                self.assertFalse(schema[command_name]["mutation"])
                self.assertEqual(schema[command_name]["allowed_mutation_outcomes"], [])

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
