#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["tiktoken==0.12.0"]
# ///
"""Check the integration boundaries. Run in the operator's terminal or CI."""
from pathlib import Path
from types import SimpleNamespace
import json
import shutil
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/prepass"))
from prepared_review import cli, instructions, packet, service, toolset, validation
from prepared_review.artifacts import tree
from prepared_review.host_capture import Observer
from prepass_runtime import ledger, records as r


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="prepared-workflow-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.packet = self.root / "packet"
        folder = self.packet / "data/focal"
        source = folder / "source"
        source.mkdir(parents=True)
        data = b"def run():\n    return 1\n"
        (source / "main.py").write_bytes(data)
        manifest = dict(records=[dict(path="main.py", status="file", selected=True, binary=False, lfs=False,
            sha256=ledger.sha(data), bytes=len(data))], coverage="complete_for_policy", signature="fixture-source",
            git=dict(head=None), errors=[], missing_content=[])
        counters = [dict(path="main.py", lines=2)]
        tables = packet.compile_tables(source, manifest, counters, dict(records=[], status="ok"), {},
                                       dict(files=[], edges=[], status="not_applicable"))
        for name, value in [("inventory.json", manifest), ("counter.json", counters),
                            ("tables.json", tables), ("source.sha256.json", tree(source))]:
            r.save(folder / name, value)
        (folder / "packet.md").write_text(packet.render(tables, manifest))
        for name in [*instructions.FILES.values(), "docs/OUTPUT_STYLE.md"]:
            path = self.packet / "instructions" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, path)
        self.config = dict(kind="prepared-review-packet-v1", model_calls=0, method="prepared", method_version=1,
            subject="fixture", processing_inputs={}, tool_inputs={}, tool_sha256=service.tool_hash(),
            policy_sha256=r.hashed_json(packet.POLICY), sides=dict(focal=dict(package=str(self.root / "input"),
            input_path=str(self.root / "input"), input_kind="package", source_signature="fixture-source",
            source_state=dict(ref=None, ref_kind="unknown", dirty="unknown"), packet_tokens=100)))
        r.save(self.packet / "preparation.json", self.config)
        r.save(self.packet / "status.json", dict(state="complete"))
        cli.write_seal(self.packet)

    def connection(self, number="01"):
        state = self.root / "review"
        args = SimpleNamespace(packet=self.packet, state=state, number=number, agent=None, model=None, reasoning=None)
        cli.connect(args)
        home = next((state / "passes" / number).glob("attempt-*"))
        return state, home

    def test_no_arguments_cannot_start_an_old_default(self):
        with self.assertRaises(SystemExit) as error:
            cli.main([])
        self.assertEqual(error.exception.code, 2)

    def test_handoff_returns_only_the_selected_template_and_style(self):
        for number, name in instructions.FILES.items():
            if number == "04":
                continue
            text = cli.handoff(self.packet, number)
            self.assertIn((ROOT / name).read_text(), text)
            self.assertIn((ROOT / "docs/OUTPUT_STYLE.md").read_text(), text)
            for other, future in instructions.FILES.items():
                if other != number:
                    self.assertNotIn((ROOT / future).read_text(), text)
        with self.assertRaises(r.PrepassError):
            cli.handoff(self.packet, "04")
        with self.assertRaises(r.PrepassError):
            cli.handoff(self.packet, "06")

    def test_connection_reuses_run_state_without_overwriting_an_attempt(self):
        state, first = self.connection()
        self.connection()
        self.assertEqual(len(list((state / "passes/01").glob("attempt-*"))), 2)
        self.assertTrue(first.is_dir())
        self.connection("02")
        config = r.read(first / "mcp.json")
        self.assertEqual(config["mcpServers"]["review"]["args"][0], str(cli.ENTRY))
        self.assertTrue((state / "review-note.md").is_file())

    def test_different_source_cannot_reuse_the_same_run_state(self):
        self.connection()
        self.config["sides"]["focal"]["source_signature"] = "another-source"
        r.save(self.packet / "preparation.json", self.config)
        cli.write_seal(self.packet)
        with self.assertRaises(r.PrepassError):
            self.connection("02")

    def test_partial_capture_remains_usable_only_with_visible_limits(self):
        path = self.packet / "data/focal/inventory.json"
        manifest = r.read(path)
        manifest.update(coverage="partial", missing_content=["absent.py"])
        r.save(path, manifest)
        tables = r.read(self.packet / "data/focal/tables.json")
        tables["scope"]["policy"] = "partial"
        tables["scope"]["missing_content"] = ["absent.py"]
        r.save(self.packet / "data/focal/tables.json", tables)
        ordered = dict(tables,
            scope={key: tables["scope"][key] for key in ("policy", "selected_files", "inventory_records", "missing_content", "inventory_errors")},
            import_status={key: tables["import_status"][key] for key in ("go", "python", "javascript")})
        (self.packet / "data/focal/packet.md").write_text(packet.render(ordered, manifest))
        self.assertTrue(validation.check_side(self.packet, "focal", strict=False))
        with self.assertRaises(r.PrepassError):
            validation.check_side(self.packet, "focal", strict=True)

    def test_capture_requires_a_successful_untruncated_host_result(self):
        state, home = self.connection()
        client = service.Service(r.read(home / "service.json"))
        response = client.invoke("read_source", dict(path="main.py", question="What does run return?"))
        observer = Observer(home, "session")
        observer.event(dict(type="assistant", message=dict(content=[dict(type="tool_use", id="call", name="mcp__review__read_source")])))
        block = dict(type="tool_result", tool_use_id="call", content=json.dumps(response), truncated=True)
        observer.event(dict(type="user", message=dict(content=[block])))
        self.assertFalse(client.invoke("coverage", dict(path="main.py"))["whole_file_delivered"])
        block.update(truncated=False, is_error=True)
        observer.event(dict(type="user", message=dict(content=[block])))
        self.assertFalse(client.invoke("coverage", dict(path="main.py"))["whole_file_delivered"])
        block["is_error"] = False
        observer.event(dict(type="user", message=dict(content=[block])))
        self.assertTrue(client.invoke("coverage", dict(path="main.py"))["whole_file_delivered"])

    def test_service_restart_keeps_the_pass_call_budget(self):
        state, home = self.connection()
        (home / "tool-calls.jsonl").write_text("{}\n" * instructions.LIMITS["calls_per_pass"])
        client = service.Service(r.read(home / "service.json"))
        with self.assertRaises(r.PrepassError):
            client.invoke("lookup", dict(kind="path", query="main"))

    def test_static_tool_manifest_needs_no_embedding_or_retrieval_files(self):
        path = self.root / "tools.json"
        tools = {}
        for name in ("rg", "ast_grep"):
            tool = self.root / name
            tool.write_bytes(name.encode())
            tools[name] = str(tool)
        r.save(path, dict(kind="prepared-review-tools-v1", tools=tools,
                         files={value: r.digest(value) for value in tools.values()}, trees={}))
        self.assertEqual(toolset.load(path)["rg"], tools["rg"])
        Path(tools["rg"]).write_text("changed")
        with self.assertRaises(r.PrepassError):
            toolset.load(path)


if __name__ == "__main__":
    unittest.main()
