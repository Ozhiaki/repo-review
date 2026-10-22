#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["tiktoken==0.12.0"]
# ///
"""Check multilingual packets and fail-closed validation in the operator's terminal."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "tools/prepass")]
from prepared_review import cli, packet
from prepared_review.validation import check_side
from prepass_runtime import ledger, records as r


class RobustnessTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="prepared-robust-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.folder = self.root / "data/focal"
        source = self.folder / "source"
        source.mkdir(parents=True)
        payloads = {"main.py": b"def run():\r\n    return 1\r\n", "README.md": b"Read this.\n", "empty.txt": b"", "image.bin": b"\x00\xff"}
        records, counters = [], []
        for name, data in payloads.items():
            (source / name).write_bytes(data)
            records.append(dict(path=name, selected=True, status="file", binary=name.endswith(".bin"), lfs=None,
                                sha256=ledger.sha(data), bytes=len(data)))
            counters.append(dict(path=name, lines=0 if name.endswith(".bin") else len(ledger.lines(data))))
        self.manifest = dict(records=records, coverage="complete_for_policy", signature="fixture", git=dict(head=None), errors=[], missing_content=[])
        declarations = dict(status="ok", records=[dict(path="main.py", text="def run():", kind="function", line=1,
            end_line=2, sha256=ledger.sha(payloads["main.py"]))])
        self.tables = packet.compile_tables(source, self.manifest, counters, declarations, {},
            dict(files=[], edges=[], status="not_applicable"), dict(status="ok"))
        r.save(self.folder / "counter.json", counters)
        self.save()

    def save(self):
        r.save(self.folder / "inventory.json", self.manifest)
        r.save(self.folder / "tables.json", self.tables)
        (self.folder / "packet.md").write_text(packet.render(self.tables, self.manifest))

    def test_python_only_packet_preserves_crlf_empty_and_binary_counts(self):
        result = check_side(self.root, "focal")
        self.assertEqual(result["selected_files"], 4)
        self.assertEqual(result["anchors"], 1)

    def test_changed_source_is_rejected(self):
        (self.folder / "source/main.py").write_text("different")
        with self.assertRaises(r.PrepassError):check_side(self.root, "focal")

    def test_json_key_order_does_not_change_packet_validation(self):
        value = json.loads((self.folder / "tables.json").read_text())
        r.save(self.folder / "tables.json", dict(reversed(list(value.items()))))
        self.assertTrue(check_side(self.root, "focal"))

    def test_missing_file_index_row_is_rejected(self):
        self.tables["files"].pop()
        self.save()
        with self.assertRaises(r.PrepassError):check_side(self.root, "focal")

    def test_wrong_line_count_is_rejected(self):
        self.tables["files"][0]["lines"] = 999
        self.save()
        with self.assertRaises(r.PrepassError):check_side(self.root, "focal")

    def test_anchor_outside_source_is_rejected(self):
        self.tables["symbols"][0]["end_line"] = 999
        self.save()
        with self.assertRaises(r.PrepassError):check_side(self.root, "focal")

    def test_missing_content_cannot_become_a_comparison_packet(self):
        self.manifest["missing_content"] = ["missing.py"]
        self.save()
        with self.assertRaises(r.PrepassError):check_side(self.root, "focal")

    def test_hand_edited_summary_is_rejected(self):
        (self.folder / "packet.md").write_text("A different summary.")
        with self.assertRaises(r.PrepassError):check_side(self.root, "focal")

    def test_unknown_graph_coverage_is_explicit(self):
        self.tables["import_status"]["python"] = "unavailable"
        self.save()
        text = (self.folder / "packet.md").read_text()
        self.assertIn('"python": "unavailable"', text)
        self.assertIn("Missing graph coverage is unknown", text)
        check_side(self.root, "focal")


if __name__ == "__main__":
    unittest.main()
