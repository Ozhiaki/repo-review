#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["tiktoken==0.12.0"]
# ///
"""Check the mechanical packet in the operator's terminal. No model calls."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "tools/prepass")]
from prepared_review import cli, packet, service
from prepass_runtime import ledger, records as r, tokens
from prepared_review.artifacts import tree
from prepared_review.host_capture import Observer


def manifest_for(source):
    rows, counters = [], []
    for path in sorted(source.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        data = path.read_bytes()
        name = path.relative_to(source).as_posix()
        rows.append(dict(path=name, selected=True, status="file", sha256=ledger.sha(data),
                         bytes=len(data), binary=b"\0" in data, lfs=False))
        counters.append(dict(path=name, lines=len(ledger.lines(data))))
    return dict(records=rows, coverage="complete_for_policy", signature="fixture", git=dict(head=None)), counters


def tables_for(source, go=None, counters=None):
    manifest, recorded = manifest_for(source)
    go = go or dict(files=[], edges=[], status="not_applicable", module_roots={})
    tables = packet.compile_tables(source, manifest, recorded if counters is None else counters,
                                   dict(records=[], status="ok"), {}, go)
    return manifest, tables


class PacketTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="prepared-unit-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.source = self.root / "packet/data/focal/source"
        self.source.mkdir(parents=True)
        self.payload = 'first\r\n"second\u2028third"\r\n'.encode()
        (self.source / "main.go").write_bytes(self.payload)

    def prepared(self):
        root = self.root / "packet"
        manifest, tables = tables_for(self.source)
        tables["go"] = dict(files=[dict(path="main.go", error="Fixture source is not parsed")], edges=[], status="partial")
        r.save(root / "data/focal/inventory.json", manifest)
        r.save(root / "data/focal/counter.json", manifest_for(self.source)[1])
        r.save(root / "data/focal/tables.json", tables)
        (root / "data/focal/packet.md").write_text(packet.render(tables, manifest))
        r.save(root / "data/focal/source.sha256.json", tree(self.source))
        r.save(root / "status.json", dict(state="complete"))
        r.save(root / "preparation.json", dict(kind="prepared-review-packet-v1", model_calls=0,
            processing_inputs={}, tool_inputs={}, tool_sha256=service.tool_hash(),
            sides=dict(focal=dict(package="fixture", source_signature=manifest["signature"]))))
        cli.write_seal(root)
        return root

    def client(self, number="01"):
        root = self.prepared()
        state = self.root / "review-state"
        return service.Service(cli.config_for(root, state, number))

    def test_packet_stays_small_with_many_omissions(self):
        manifest, tables = tables_for(self.source)
        tables["scope"]["missing_content"] = ["missing" * 100] * 10000
        tables["scope"]["inventory_errors"] = [dict(path="error" * 100)] * 10000
        for index in range(10000):
            tables["symbols"].append(dict(path=f"p/{index}.go", name="Validate", line=1, end_line=50))
        text = packet.render(tables, manifest)
        self.assertLessEqual(tokens.tokens(text), packet.TOKEN_LIMIT)
        self.assertIn('"missing_content_count": 10000', text)
        self.assertIn("Missing graph coverage is unknown", text)
        self.assertIn("not a product", text)

    def test_counts_exclude_unselected_paths(self):
        manifest, counters = manifest_for(self.source)
        ignored = dict(manifest["records"][0], path="ignored.go", selected=False)
        manifest["records"].append(ignored)
        tables = packet.compile_tables(self.source, manifest, counters, {}, {}, dict(files=[], edges=[], status="not_applicable"))
        self.assertEqual(tables["scope"]["selected_files"], 1)
        self.assertEqual(tables["scope"]["inventory_records"], 2)

    def test_go_shortlist_requires_known_root_complete_parse_and_counts(self):
        row = dict(path="main.go", test=False, imports=[], declarations=[], calls=[])
        go = dict(files=[row], edges=[], status="ok", module_roots={".": "example.test/repo"})
        self.assertTrue(tables_for(self.source, go)[1]["modules"][0]["small_module"])
        self.assertFalse(tables_for(self.source, go, [])[1]["modules"][0]["small_module"])
        go["module_roots"] = {}
        self.assertFalse(tables_for(self.source, go)[1]["modules"][0]["small_module"])
        go["module_roots"] = {".": "example.test/repo"}
        go["status"] = "partial"
        self.assertFalse(tables_for(self.source, go)[1]["modules"][0]["small_module"])

    def test_fixture_packages_do_not_fill_the_compact_review_lists(self):
        manifest, tables = tables_for(self.source)
        names = ["testdata/golden/tiny", "internal/a/testdata/tiny", "examples/tiny", "vendor/tiny", "tests/tiny"]
        names += ["internal/reusable"]
        for name in names:
            tables["symbols"].append(dict(path=name+"/main.go", name="main", line=1, end_line=2))
            tables["modules"].append(dict(path=name, small_module=True, lines=2, production_files=1,
                                           local_dependencies=[], local_dependents=[]))
        text = packet.render(tables, manifest)
        self.assertIn("internal/reusable", text)
        for name in names[:-1]:
            self.assertNotIn('"path": "'+name, text)
        self.assertEqual(len(tables["modules"]), len(names))
        self.assertEqual(len(tables["symbols"]), len(names))

    def test_lookup_gives_no_read_credit(self):
        client = self.client()
        hit = client.invoke("lookup", dict(kind="path", query="main"))
        self.assertEqual(hit["total_matches"], 1)
        self.assertFalse(client.invoke("coverage", dict(path="main.go"))["whole_file_delivered"])
        with self.assertRaises(r.PrepassError):
            client.invoke("lookup", dict(kind="path", query=""))

    def test_source_delivery_needs_a_host_capture(self):
        client = self.client()
        response = client.invoke("read_source", dict(path="main.go", question="What does this source do?"))
        self.assertEqual(response["source"].encode(), self.payload)
        self.assertFalse(client.invoke("coverage", dict(path="main.go"))["whole_file_delivered"])
        observer = Observer(client.home, "fixture-session")
        observer.capture(response, dict(type="user", message="fixture tool result"))
        self.assertTrue(client.invoke("coverage", dict(path="main.go"))["whole_file_delivered"])
        capture = next((client.home / "captures").glob("*.bin"))
        capture.write_bytes(b"different")
        with self.assertRaises(r.PrepassError):
            client.invoke("coverage", dict(path="main.go"))

    def test_ranges_preserve_lf_crlf_and_unicode(self):
        client = self.client()
        response = client.invoke("read_source", dict(path="main.go", question="Check the second line.", start=2, end=2))
        self.assertEqual(response["source"].encode(), ledger.lines(self.payload)[1])
        with self.assertRaises(r.PrepassError):
            client.invoke("read_source", dict(path="main.go", question="Check the source.", start=1))

    def test_read_requires_question_and_rejects_escaped_paths(self):
        client = self.client()
        for path, question in [("../main.go", "Check the source."), (".git/config", "Check the source."), ("main.go", "why")]:
            with self.subTest(path=path, question=question), self.assertRaises(r.PrepassError):
                client.invoke("read_source", dict(path=path, question=question))

    def test_changed_source_is_rejected(self):
        client = self.client()
        (self.source / "main.go").write_bytes(b"different")
        with self.assertRaises(r.PrepassError):
            client.invoke("read_source", dict(path="main.go", question="Check the source."))

    def test_large_file_requires_a_small_range(self):
        (self.source / "main.go").write_bytes(b"a\n" * 20000)
        client = self.client()
        with self.assertRaises(r.PrepassError):
            client.invoke("read_source", dict(path="main.go", question="Check the source."))
        response = client.invoke("read_source", dict(path="main.go", question="Check the first line.", start=1, end=1))
        self.assertEqual(response["source"], "a\n")

    def test_twin_gate_keeps_tool_schema_stable(self):
        client = self.client()
        before = service.tool_hash()
        with self.assertRaises(r.PrepassError):
            client.invoke("lookup", dict(repo="twin", kind="path", query="main"))
        twin = client.packet / "data/twin"
        shutil.copytree(client.packet / "data/focal", twin)
        client.config["pass"] = "04"
        self.assertEqual(client.invoke("lookup", dict(repo="twin", kind="path", query="main"))["total_matches"], 1)
        self.assertEqual(service.tool_hash(), before)

    def test_seal_and_processing_input_drift_are_rejected(self):
        root = self.prepared()
        cli.check(root)
        (root / "data/focal/tables.json").write_text("{}")
        with self.assertRaises(r.PrepassError):
            cli.check(root)
        cli.write_seal(root)
        fixed = self.root / "fixed.py"
        fixed.write_text("original")
        config = r.read(root / "preparation.json")
        config["processing_inputs"] = {str(fixed): r.digest(fixed)}
        r.save(root / "preparation.json", config)
        cli.write_seal(root)
        fixed.write_text("changed")
        with self.assertRaises(r.PrepassError):
            cli.check(root)

    def test_output_cannot_overlap_inputs_or_links(self):
        root = self.prepared()
        with self.assertRaises(r.PrepassError):
            cli.protected_output(root / "new", [root])
        link = self.root / "link"
        link.symlink_to(root, target_is_directory=True)
        with self.assertRaises(r.PrepassError):
            cli.protected_output(link / "new", [])


class GoParserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="prepared-native-")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.root = Path(cls.temporary.name).resolve()
        cls.binary = cls.root / "go-facts"
        compiler = os.environ.get("PREPARED_REVIEW_GO") or shutil.which("go")
        if not compiler:
            raise RuntimeError("An installed Go compiler is required for Prepared Review tests.")
        environment = dict(os.environ, **cli.GO_ENV)
        subprocess.run([compiler, "build", "-trimpath", "-o", str(cls.binary), str(ROOT / "tools/prepass/prepared_review/go_facts.go")],
                       cwd=cls.root, env=environment, check=True, timeout=180, capture_output=True)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(dir=self.root, prefix="source-")
        self.addCleanup(temporary.cleanup)
        self.source = Path(temporary.name).resolve()

    def write(self, name, text):
        target = self.source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    def parse(self, files=None, modules=None, accepted=True):
        names = files if files is not None else sorted(p.relative_to(self.source).as_posix() for p in self.source.rglob("*.go"))
        request = self.source / "request.json"
        r.save(request, dict(root=str(self.source), files=names, modules=modules if modules is not None else {".": "example.test/repo"}))
        result = subprocess.run([str(self.binary), str(request)], capture_output=True, timeout=15)
        if not accepted:
            self.assertNotEqual(result.returncode, 0)
            return None
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        value = json.loads(result.stdout)
        value["status"] = "partial" if any(row.get("error") for row in value["files"]) else "ok"
        return value

    def test_declarations_imports_test_edges_and_no_subject_execution(self):
        sentinel = self.source / "EXECUTED"
        self.write("main.go", 'package main\nimport ("example.test/repo/lib"; "os")\n'
                   f'func init() {{ os.WriteFile({json.dumps(str(sentinel))}, []byte("bad"), 0600) }}\n'
                   'func main() { lib.Check() }\n')
        self.write("lib/lib.go", 'package lib\ntype Guard struct{}\nfunc (g *Guard) Verify() bool { return true }\nfunc Check() {}\n')
        self.write("lib/lib_test.go", 'package lib_test\nimport "example.test/repo/testonly"\nfunc TestThing() { testonly.Check() }\n')
        self.write("testonly/x.go", 'package testonly\nfunc Check() {}\n')
        value = self.parse()
        self.assertFalse(sentinel.exists())
        methods = [d for f in value["files"] for d in f["declarations"] if d["name"] == "Verify"]
        self.assertEqual((methods[0]["receiver"], methods[0]["line"]), ("*Guard", 3))
        self.assertIn((".", "lib", False), [(e["from"], e["to"], e["test"]) for e in value["edges"]])
        self.assertIn(("lib", "testonly", True), [(e["from"], e["to"], e["test"]) for e in value["edges"]])
        tables = tables_for(self.source, value)[1]
        lib = next(row for row in tables["modules"] if row["path"] == "lib")
        self.assertEqual(lib["local_dependencies"], [])
        self.assertEqual(lib["local_dependents"], ["."])
        self.assertTrue(any(c["name"] == "lib.Check" and "not_a_call_graph" in c["resolution"] for c in tables["call_sites"]))

    def test_nested_module_and_build_tags_keep_explicit_limits(self):
        self.write("main.go", 'package main\nimport "other.test/mod/pkg"\nfunc main() { pkg.Call() }\n')
        self.write("nested/pkg/x.go", '//go:build unusual\n\npackage pkg\nfunc Call() {}\n')
        value = self.parse(modules={".": "example.test/repo", "nested": "other.test/mod"})
        self.assertEqual(value["edges"][0]["to"], "nested/pkg")
        self.assertIn("build_tags_not_evaluated", value["edges"][0]["resolution"])

    def test_parse_failure_prevents_small_module_claim(self):
        self.write("broken.go", "package broken\nfunc Bad(\n")
        value = self.parse()
        self.assertEqual(value["status"], "partial")
        self.assertFalse(tables_for(self.source, value)[1]["modules"][0]["small_module"])

    def test_line_directives_do_not_change_source_anchors(self):
        self.write("main.go", 'package main\n//line other.go:9000\nfunc main() { Check() }\nfunc Check() {}\n')
        value = self.parse()
        self.assertEqual(value["files"][0]["declarations"][0]["line"], 3)
        self.assertEqual(value["files"][0]["calls"][0]["line"], 3)

    def test_path_escape_and_symlink_are_rejected(self):
        self.write("good.go", "package good\n")
        self.parse(files=["../outside.go"], accepted=False)
        (self.source / "linked.go").symlink_to(self.source / "good.go")
        self.parse(files=["linked.go"], accepted=False)


if __name__ == "__main__":
    unittest.main()
