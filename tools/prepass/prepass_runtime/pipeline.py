"""Prepare the selected evidence components as one sealed package."""
from __future__ import annotations

import json
from pathlib import Path
import time

from . import adapters, package as foundation, records as r, scope, tokens, toolchain


def render(package, manifest, components, limit):
    header = ["# Prepass facts", "", "Computed source evidence. Review judgment is required.",
              "Use the source copies to verify claims. No search result establishes complete reading.",
              "Source coverage: " + manifest["coverage"] + ".",
              "Source state: " + manifest["signature"] + ".",
              "Commit: " + (manifest["git"].get("head") or "unknown") + ".",
              f"Facts limit: {limit} o200k_base tokens. Full records are separate.", "",
              "| Component | Status | Record |", "|---|---|---|"]
    filenames = dict(outline="declarations.json", syntax="syntax.json", broad="broad-risk.json",
                     python="python-imports.json", javascript="javascript-imports.json", retrieval="retrieval.json")
    for name, component in components.items():
        header.append(f"| {name} | {component['status']} | {filenames[name]} |")
    header += ["", "Submodules remain unexpanded. LFS pointers are not the referenced content.",
               "Grammar validity and runtime name resolution are not established by syntax leads.",
               "Colgrep native file coverage is unconfirmed. Zoekt omissions are in retrieval.json.", ""]
    r.require(tokens.tokens("\n".join(header) + "\n") < limit, "The facts limit cannot hold the required status records.")
    result = list(header)
    sections = [("Inventory", "inventory.json", [json.dumps(dict(path=row["path"], status=row["status"]), ensure_ascii=True)
                    for row in manifest["records"]]),
                ("Declarations", "declarations.json", (package / "declaration-index.md").read_text().splitlines()),
                ("Broad text leads", "broad-risk.json", [json.dumps({key: row[key] for key in ("category", "path", "line")}, ensure_ascii=True)
                    for row in components["broad"]["records"]]),
                ("Syntax leads", "syntax.json", [json.dumps({key: row[key] for key in ("category", "path", "line")}, ensure_ascii=True)
                    for row in components["syntax"]["records"]]),
                ("Python imports", "python-imports.json", [json.dumps(edge, ensure_ascii=True) for edge in components["python"]["edges"]]),
                ("JavaScript imports", "javascript-imports.json", [json.dumps(edge, ensure_ascii=True) for edge in components["javascript"]["edges"]])]
    allowance = max(32, (limit - tokens.tokens("\n".join(result)) - 200) // len(sections))
    for title, filename, lines in sections:
        marker = "[TRUNCATED: read " + filename + "]"
        section = tokens.bounded(["## " + title, "", *lines], allowance, marker)
        proposed = result + [""] + section
        if tokens.tokens("\n".join(proposed) + "\n") <= limit:
            result = proposed
    text = "\n".join(result) + "\n"
    r.require(tokens.tokens(text) <= limit, "The complete facts file exceeds its token limit.")
    (package / "facts.md").write_text(text)
    return tokens.tokens(text)


def run(args):
    started = time.monotonic()
    tools = toolchain.load(args.tools)
    tokenizer_files = tokens.identity()
    foundation.prepare(args)
    output = Path(args.out).expanduser().resolve()
    package = output / "evidence"
    source = package / "source"
    original = r.read(package / "inventory.json")
    metadata = r.read(package / "meta.json")
    snapshot_hashes = r.tree(source)
    commands = r.Commands(package / "adapter-commands", args.total_timeout - (time.monotonic() - started), args.command_timeout)
    r.save(output / "status.json", dict(state="extracting", review_ready=False))
    try:
        rows, payloads = adapters.inventory(original, source)
        r.save(package / "text-inventory.json", rows)
        components = adapters.outline(package, source, rows, payloads, tools, commands)
        components["broad"] = adapters.broad_risk(package, source, rows, payloads, tools, commands)
        components["python"] = adapters.python_graph(package, source, original, args.python_root or ["."])
        components["javascript"] = adapters.javascript_graph(package, source, rows, tools, commands, args.tsconfig)
        components["retrieval"] = adapters.indexes(package, source, rows, tools, commands)
        current, _ = scope.capture(Path(metadata["source_root"]), foundation.git_reader(commands, metadata["git_binary"], Path(metadata["source_root"]), "final"))
        r.require(current["signature"] == original["signature"], "The original source changed during tool work.")
        r.require(r.tree(source) == snapshot_hashes, "An adapter changed the captured source.")
        r.require(foundation.processing_inputs() == metadata["processing_inputs"], "A processing input changed during tool work.")
        r.require(all(r.digest(path) == expected for path, expected in tools["fingerprints"].items()), "A tool bundle file changed during tool work.")
        count = render(package, original, components, args.facts_tokens)
        complete = original["coverage"] == "complete_for_policy" and all(value["status"] in ("ok", "not_applicable") for value in components.values())
        metadata.update(stage="integrated", tools=dict(metadata["tools"], **tools["fingerprints"], **tokenizer_files), adapter_tools=tools,
                        python_roots=args.python_root or ["."], tsconfig=args.tsconfig,
                        facts_tokens=count, facts_token_limit=args.facts_tokens, token_encoding="o200k_base", tokenizer_version="0.12.0",
                        components={key: value["status"] for key, value in components.items()}, review_ready=complete)
        r.save(package / "meta.json", metadata)
        (package / "seal.json").unlink()
        r.save(package / "seal.json", dict(version=1, artifacts=r.tree(package)))
        r.save(output / "status.json", dict(state="complete" if complete else "partial", stage="integrated", review_ready=complete,
            source_preserved=True, coverage=original["coverage"], components=metadata["components"], acceptance="not_measured_here"))
        r.say("Integrated evidence: " + str(package / "facts.md"))
        return 0
    except BaseException as exc:
        r.save(output / "status.json", dict(state="interrupted" if isinstance(exc, KeyboardInterrupt) else "failed",
            stage="integrated", error=str(exc), review_ready=False))
        raise
    finally:
        commands.stop()
