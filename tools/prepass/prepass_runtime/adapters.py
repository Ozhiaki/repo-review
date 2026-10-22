"""Run the selected extraction tools against the captured source only."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path

from . import catalog, declarations, python_imports, records as r, scope, toolchain


def inventory(manifest, source):
    rows, payloads = [], {}
    for original in manifest["records"]:
        row = dict(path=original["path"], sha256=original.get("sha256"), bytes=original.get("bytes"))
        if original["status"] != "file":
            row["status"] = original["status"]
        elif original.get("lfs"):
            row["status"] = "lfs_pointer"
        elif original.get("binary"):
            row["status"] = "binary"
        else:
            data, _ = scope.read_regular(source, row["path"])
            r.require(hashlib.sha256(data).hexdigest() == row["sha256"], "A source copy differs from its inventory.")
            try:
                data.decode("utf-8")
                row["status"] = "text"
                payloads[row["path"]] = data
            except UnicodeError:
                row["status"] = "non_utf8"
        rows.append(row)
    return rows, payloads


def outline(package, source, rows, payloads, tools, commands):
    config = package / "control/sgconfig.yml"
    config.parent.mkdir()
    config.write_text("ruleDirs: []\n")
    r.require(r.digest(declarations.SYNTAX) == "be7eb19b84517c795ff6bb0eaded68938a4700dab2ebc3d2fbae4b187477ed3b",
              "The retained syntax rules changed.")
    def native(label, rules, batch):
        return commands.run(label, [tools["ast_grep"], "scan", "--config", config, "--inline-rules", rules,
            "--json=compact", "--color", "never", *declarations.IGNORE, "--inspect=entity", "--",
            *["./" + name for name in batch]], source, accepted=None)
    results = {}
    for family, filename in (("outline", "declarations.json"), ("syntax", "syntax.json")):
        result = declarations.scan(source, rows, payloads, family, native)
        r.save(package / filename, result)
        results[family] = result
    (package / "declaration-index.md").write_text(declarations.index(results["outline"]["records"], 80))
    return results


def broad_risk(package, source, rows, payloads, tools, commands):
    names = [row["path"] for row in rows if row["status"] == "text" and catalog.lang_of(row["path"])
             not in catalog.DOC_LANGS | catalog.DATA_LANGS | {"Other", "Binary"}]
    matches, files, errors = [], [], []
    for category, pattern in [*catalog.RISK, ("panic-sites", catalog.PANIC_PATTERN)]:
        selected_names = names if category != "panic-sites" else [name for name in names if name.endswith(".rs") and not catalog.TEST_PATH.search(name)]
        def native(label, argv):
            return commands.run("broad-" + category + "-" + label, [tools["rg"], *argv], source, accepted=None)
        statuses, native_matches, failures = scope.search(source, selected_names, pattern, native)
        errors.extend(dict(category=category, **error) for error in failures)
        for item in native_matches:
            data = payloads[item["path"]]
            line = item["line"]
            parts = data.split(b"\n")
            source_lines = [part + b"\n" for part in parts[:-1]] + ([parts[-1]] if parts[-1] else [])
            delivered = scope.text_field(item["lines"]).encode("utf-8", "surrogateescape")
            r.require(1 <= line <= len(source_lines) and delivered == source_lines[line - 1], "A broad match differs from source bytes.")
            matches.append(dict(category=category, path=item["path"], line=line, text=delivered.decode("utf-8"),
                                sha256=hashlib.sha256(data).hexdigest(), resolution="broad_text"))
        for row in rows:
            files.append(dict(category=category, path=row["path"], sha256=row.get("sha256"),
                              status=statuses.get(row["path"], "not_code" if row["status"] == "text" else row["status"])))
    result = dict(status="partial" if errors else "ok", files=files, records=matches, errors=errors,
                  categories=[name for name, _ in catalog.RISK], limit="Text matches include comments and strings.")
    r.save(package / "broad-risk.json", result)
    with (package / "risk.tsv").open("w") as stream:
        stream.write("category\tpath_json\tline\ttext_json\n")
        for row in matches:
            stream.write(f"{row['category']}\t{json.dumps(row['path'], ensure_ascii=True)}\t{row['line']}\t{json.dumps(row['text'], ensure_ascii=True)}\n")
    return result


def python_graph(package, source, manifest, roots):
    for root in roots:
        r.require(root == "." or str(scope.checked_name(root)) == root, "A Python import root is invalid.")
    files = [row["path"] for row in manifest["records"] if row["status"] == "file" and not row.get("binary")
             and not row.get("lfs") and row["path"].endswith(".py")]
    result = python_imports.build(source, files, roots)
    result["status"] = "partial" if result["errors"] else "ok"
    result["scope"] = [dict(path=row["path"], status="selected" if row["path"] in files else "not_python" if row["status"] == "file" else row["status"])
                       for row in manifest["records"]]
    r.save(package / "python-imports.json", result)
    return result


def javascript_graph(package, source, rows, tools, commands, tsconfig):
    names = [row["path"] for row in rows if row["status"] == "text" and Path(row["path"]).suffix.lower() in (".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx")]
    if not names:
        result = dict(status="not_applicable", nodes=[], edges=[], unresolved=[], omitted=[], native_error=None)
    else:
        argv = [tools["node"], tools["cruiser"], "--no-config", "--no-cache", "--no-progress", "--output-type", "json",
                "--ts-pre-compilation-deps", "--do-not-follow", "node_modules"]
        if tsconfig:
            config = scope.checked_name(tsconfig)
            r.require((source / config).is_file(), "The selected TypeScript configuration is absent from the source package.")
            argv += ["--ts-config", tsconfig]
        response = commands.run("javascript-graph", [*argv, "--", *names], source, accepted=None,
                                environment={"NODE_OPTIONS": "", "NODE_PATH": ""})
        if response["returncode"]:
            result = dict(status="failed", nodes=[], edges=[], unresolved=[], omitted=names,
                          native_error=dict(returncode=response["returncode"], stderr=response["stderr"].decode("utf-8", "replace")))
        else:
            native = json.loads(response["stdout"])
            r.require(isinstance(native.get("modules"), list), "The native graph has no module records.")
            r.save(package / "javascript-native.json", native)
            selected, nodes, edges, unresolved = set(names), set(), set(), []
            def canonical(value):
                path = Path(value)
                path = path if path.is_absolute() else source / path
                try:
                    return path.resolve().relative_to(source.resolve()).as_posix()
                except ValueError:
                    return None
            for unit in native["modules"]:
                origin = canonical(unit["source"])
                if origin not in selected:
                    continue
                nodes.add(origin)
                for item in unit.get("dependencies", []):
                    target = canonical(item.get("resolved", ""))
                    if item.get("couldNotResolve"):
                        unresolved.append(dict(source=origin, name=item.get("module")))
                    elif target in selected:
                        edges.add((origin, target))
            omitted = sorted(selected - nodes)
            result = dict(status="partial" if omitted else "ok", nodes=sorted(nodes), edges=sorted(edges), unresolved=unresolved,
                          omitted=omitted, native_error=None)
    result["scope"] = [dict(path=row["path"], sha256=row.get("sha256"), status="selected" if row["path"] in names else
                            "not_javascript" if row["status"] == "text" else row["status"]) for row in rows]
    result["limits"] = ["Edges describe static source candidates among selected files.",
                        "External dependencies and runtime-generated imports are not a complete runtime graph.",
                        "Native failure leaves an absent graph. It does not establish parser recovery."]
    r.save(package / "javascript-imports.json", result)
    return result


def indexes(package, source, rows, tools, commands):
    text = [row for row in rows if row["status"] == "text"]
    home = package / "indexes"
    home.mkdir()
    r.save(home / "manifest.json", dict(files=[dict(path=row["path"]) for row in text]))
    response = commands.run("zoekt-index", [tools["zoekt"], "-mode", "index", "-index", home / "zoekt", "-source", source,
        "-manifest", home / "manifest.json", "-name", "prepass", "-symbols=true", "-ctags", tools["ctags"]], package, accepted=None)
    r.require(response["returncode"] == 0, "Zoekt index preparation failed. Read the command records.")
    built = json.loads(response["stdout"])
    r.require(built["options"]["DisableCTags"] is False, "The retained Zoekt symbol configuration changed.")
    selected = {row["path"]: row for row in text}
    found = {row["path"]: row for row in built["files"]}
    r.require(len(found) == len(built["files"]) and found.keys() == selected.keys(), "The native index file list differs.")
    for name, row in found.items():
        r.require(row["sha256"] == selected[name]["sha256"] and row["bytes"] == selected[name]["bytes"], "Native index bytes differ.")
    response = commands.run("zoekt-audit", [tools["zoekt"], "-mode", "audit", "-index", home / "zoekt"], package)
    audit = json.loads(response["stdout"])
    from .lexical import no_truncation
    no_truncation(audit["stats"])
    stored = {row["path"]: row for row in audit["files"]}
    r.require(stored.keys() == found.keys(), "The stored native file list differs.")
    eligible = []
    for name, row in found.items():
        r.require(row["skip_reason"] in range(5), "The native index skip reason is unknown.")
        if row["skip_reason"] == 0:
            r.require(stored[name]["sha256"] == row["sha256"] and stored[name]["bytes"] == row["bytes"], "Stored index bytes differ.")
            eligible.append(name)
    r.save(home / "zoekt-build.json", dict(build=built, audit=audit, eligible=sorted(eligible)))
    environment = toolchain.colgrep_environment(home / "colgrep-data", home / "colgrep-config")
    (home / "colgrep-data").mkdir()
    (home / "colgrep-config").mkdir()
    response = commands.run("colgrep-index", [tools["colgrep"], "init", "--force-cpu", "--model", tools["model"], "-y",
        "--color", "never", source], source, accepted=None, environment=environment)
    r.require(response["returncode"] == 0, "Colgrep index preparation failed. Read the command records.")
    r.require((home / "colgrep-data").is_dir(), "Colgrep did not create its private index.")
    # The first search creates merged-array caches and SQLite sidecar files.
    # Create them before sealing evidence, so review queries can keep the
    # strict rule that only one private search counter may change.
    response = commands.run("colgrep-prepare-search-cache", [tools["colgrep"], "--json", "-k", "30", "--no-update",
        "--force-cpu", "--color", "never", "--model", tools["model"], "source code", source], source,
        environment=environment)
    from .selection import native_pool
    native_pool(json.loads(response["stdout"]), source, source, set(selected))
    result = dict(status="ok", model="lightonai/LateOn-Code-edge", model_path=tools["model"],
                  colgrep_search_cache="prepared_before_seal",
                  colgrep_scope="native_file_coverage_unconfirmed", zoekt_eligible=sorted(eligible),
                  colgrep_files=[dict(path=row["path"], sha256=row.get("sha256"),
                                     status="native_scope_unconfirmed" if row["status"] == "text" else row["status"]) for row in rows],
                  zoekt_omitted=[dict(path=name, reason=row["skip_reason"]) for name, row in found.items() if row["skip_reason"] != 0])
    r.save(package / "retrieval.json", result)
    return result
