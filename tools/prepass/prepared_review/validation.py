"""Validate mechanical records independently of a model or comparison run."""
from pathlib import Path
from prepass_runtime import ledger, records as r, scope, tokens
from . import packet


def check_side(root, side, *, strict=True):
    folder = Path(root) / "data" / side
    manifest = r.read(folder / "inventory.json")
    tables = r.read(folder / "tables.json")
    selected = {row["path"]: row for row in manifest["records"] if row["selected"] and row["status"] == "file"}
    indexed = {row["path"]: row for row in tables["files"]}
    r.require(len(indexed) == len(tables["files"]) and indexed.keys() == selected.keys(), "File-index coverage differs from selected source.")
    r.require(tables["scope"]["policy"] == manifest["coverage"]
              and tables["scope"]["selected_files"] == len(selected)
              and tables["scope"]["inventory_records"] == len(manifest["records"]),
              "Packet scope differs from captured source.")
    if strict:
        r.require(manifest["coverage"] == "complete_for_policy" and not manifest.get("errors") and not manifest.get("missing_content"),
                  "Strict validation requires complete source under the recorded selection policy.")
    counters = {row["path"]: row for row in r.read(folder / "counter.json")}
    lengths = {}
    readable = []
    for name, original in selected.items():
        data, _ = scope.read_regular(folder / "source", name)
        row = indexed[name]
        r.require(ledger.sha(data) == row["sha256"] == original["sha256"], "A file hash differs: " + name)
        r.require(len(data) == row["bytes"] == original["bytes"], "A file size differs: " + name)
        r.require(row["binary"] == bool(original.get("binary")) and row["lfs"] == bool(original.get("lfs")),
                  "A file content classification differs: " + name)
        lengths[name] = len(ledger.lines(data))
        expected = None if original.get("lfs") else 0 if original.get("binary") else lengths[name]
        r.require(counters[name]["lines"] == row["lines"] == expected, "A physical line count differs: " + name)
        if not row["binary"] and not row["lfs"]:
            try:
                data.decode("utf-8")
                if 0 < len(data) <= 1024 and len(name) <= 160:
                    readable.append(name)
            except UnicodeError:
                pass
    for row in [*tables["symbols"], *tables["call_sites"]]:
        name = row["path"]
        r.require(name in selected and row["sha256"] == selected[name]["sha256"], "An anchor has no matching source hash.")
        r.require(type(row["line"]) is int and 1 <= row["line"] <= row.get("end_line", row["line"]) <= lengths[name],
                  "An anchor leaves its source: " + name)
    go_names = {name for name, row in selected.items() if name.endswith(".go") and not row.get("binary") and not row.get("lfs")}
    r.require({row["path"] for row in tables["go"]["files"]} == go_names, "Selected Go files are missing from the parser record.")
    for row in tables["modules"]:
        if row["small_module"]:
            r.require(row["module_root_known"] and row["line_coverage"] == "complete" and not row["parse_errors"]
                and tables["go"]["status"] == "ok" and row["lines"] <= 1200 and len(row["local_dependencies"]) <= 2,
                "A small-module claim lacks its required evidence.")
    text = (folder / "packet.md").read_text()
    r.require(tokens.tokens(text) <= packet.TOKEN_LIMIT, "The packet exceeds its size limit.")
    # The retained v1 renderer uses insertion order for these JSON objects.
    # Stored JSON sorts keys. Restore the producer's declared field order.
    ordered = dict(tables,
        scope={key:tables["scope"][key] for key in ("policy","selected_files","inventory_records","missing_content","inventory_errors")},
        import_status={key:tables["import_status"][key] for key in ("go","python","javascript")})
    r.require(packet.render(ordered, manifest) == text, "The packet cannot be reproduced from its tables.")
    return dict(selected_files=len(selected), anchors=len(tables["symbols"]), calls=len(tables["call_sites"]),
                packet_tokens=tokens.tokens(text), readable_probe=next(iter(sorted(readable)), None),
                import_status=tables["import_status"], outline_status=tables["outline_status"])
