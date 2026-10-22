"""Query private indexes and apply the retained 4,000-token source merge."""
from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
import uuid

from . import delivery, lexical, merge, records as r, selection, tokens, toolchain


def colgrep_candidates(pool):
    rows = []
    for rank in sorted({row["file_rank"] for row in pool}):
        rows.extend(dict(row) for row in sorted((row for row in pool if row["file_rank"] == rank), key=lambda row: -row["score"])[:3])
    return rows[:30]


def verify_counter(original, private, before):
    after = r.tree(private)
    r.require(after.keys() == before.keys(), "The private Colgrep file list changed.")
    changes = []
    for name, expected in before.items():
        if after[name] == expected:
            continue
        path = Path(name)
        r.require(len(path.parts) == 4 and path.parts[:2] == ("colgrep", "indices") and path.name == "state.json",
                  "A private Colgrep index changed outside its search counter.")
        first, last = r.read(original / path), r.read(private / path)
        a, b = first.get("search_count"), last.get("search_count")
        r.require(type(a) is int and type(b) is int and b == a + 1
                  and {k: v for k, v in first.items() if k != "search_count"} == {k: v for k, v in last.items() if k != "search_count"},
                  "A Colgrep search counter update differs.")
        changes.append(name)
    r.require(len(changes) == 1, "The completed Colgrep search has no unique counter update.")
    return changes


def query(args):
    output, evidence = delivery.fresh(args)
    r.require(1 <= len(args.term) <= 5 and len(set(args.term)) == len(args.term)
              and all(re.fullmatch(r"[a-z0-9_-]{3,32}", term) for term in args.term), "Supply one to five distinct lowercase literal search terms.")
    r.require(tokens.tokens(f"Task:\n{args.question}\n\nRetrieved source evidence:\n") <= 4000,
              "The task text exceeds the query response limit.")
    metadata = r.read(evidence / "meta.json")
    r.require(metadata["stage"] == "integrated", "The package has no prepared search indexes.")
    tools = metadata["adapter_tools"]
    source = evidence / "source"
    rows = r.read(evidence / "text-inventory.json")
    paths = {row["path"] for row in rows if row["status"] == "text"}
    home = output / "state/queries" / uuid.uuid4().hex
    r.output_directory(home)
    r.save(home / "request.json", dict(question=args.question, terms=args.term, policy="colgrep-compact-first"))
    commands = r.Commands(home / "commands", args.total_timeout, args.command_timeout)
    try:
        original_data = evidence / "indexes/colgrep-data"
        data = home / "colgrep-data"
        shutil.copytree(original_data, data)
        config = home / "colgrep-config"
        shutil.copytree(evidence / "indexes/colgrep-config", config)
        before = r.tree(data)
        response = commands.run("colgrep-query", [tools["colgrep"], "--json", "-k", "30", "--no-update", "--force-cpu", "--color", "never",
            "--model", tools["model"], args.question, source], source, environment=toolchain.colgrep_environment(data, config))
        first = colgrep_candidates(selection.native_pool(json.loads(response["stdout"]), source, source, paths))
        changes = verify_counter(original_data, data, before)
        native_query = 'case:no (' + ' or '.join('content:"' + re.escape(term) + '"' for term in args.term) + ')'
        response = commands.run("zoekt-bm25", [tools["zoekt"], "-index", evidence / "indexes/zoekt", "-query", native_query, "-bm25=true"], source)
        retrieval = r.read(evidence / "retrieval.json")
        native_files, _ = lexical.zoekt_hits(json.loads(response["stdout"]), source, paths, set(retrieval["zoekt_eligible"]))
        outlines = []
        for row in r.read(evidence / "declarations.json")["records"]:
            if row["language"] not in ("python", "go") or row["kind"] == "type_alias":
                continue
            expression = (r"\s*(?:async\s+)?(?:def|class)\s+(\w+)" if row["language"] == "python" else
                          r"\s*(\w+)" if row["kind"] == "type_spec" else r"\s*func\s+(?:\([^\n]*?\)\s*)?(\w+)")
            match = re.match(expression, row["text"])
            r.require(match is not None, "A retained retrieval declaration has no source name.")
            # Match the tested retrieval outline's exclusive end-line convention.
            end = row["end_line"] - int(row["text"].endswith("\n"))
            outlines.append(dict(path=row["path"], start=row["line"], end=max(row["line"], end), name=match[1]))
        second = lexical.candidates(native_files, outlines, source)
        candidates, (text, spans, trace) = merge.select(source, first, second, args.question)
        r.require(tokens.tokens(text) <= 4000, "The query response exceeds the retained token limit.")
        r.save(home / "result.json", dict(candidates=candidates, colgrep=first, zoekt=second, spans=spans, trace=trace,
            tokens=tokens.tokens(text), token_limit=4000, colgrep_counter_changes=changes, reading_credit="none"))
        (home / "evidence.txt").write_text(text)
        r.require(delivery.fresh(args)[0] == output, "Post-query source verification failed.")
        print(text, end="")
        return 0
    finally:
        commands.stop()
