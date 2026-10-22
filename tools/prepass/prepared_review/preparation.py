"""Compose accepted capture and extraction without building retrieval indexes."""
from pathlib import Path
from types import SimpleNamespace
import shutil
import time

from prepass_runtime import adapters, package as foundation, records as r, scope
from .artifacts import tree
from . import packet


def capture(repo, home, args, commands):
    options = SimpleNamespace(repo=str(repo), out=str(home), git=args.git,
                              total_timeout=max(0.01, commands.deadline-time.monotonic()),
                              command_timeout=args.command_timeout)
    foundation.prepare(options)
    return home


def complete_records(package, home, tools, commands, roots, tsconfig):
    """Make a private package. Never add records to the input package."""
    manifest = packet.verify_package(package)
    home.mkdir(parents=True)
    source = home / "source"
    shutil.copytree(Path(package) / "evidence/source", source)
    expected = tree(source)
    r.require(expected == tree(Path(package) / "evidence/source"), "A private source copy differs.")
    for name in packet.RECORDS:
        original = Path(package) / "evidence" / name
        if original.is_file():
            shutil.copy2(original, home / name)
    rows, payloads = adapters.inventory(manifest, source)
    if not (home / "declarations.json").is_file() or not (home / "syntax.json").is_file():
        r.require("ast_grep" in tools, "Supply --tools to compute missing declaration and syntax records.")
        adapters.outline(home, source, rows, payloads, tools, commands)
    if not (home / "broad-risk.json").is_file():
        r.require("rg" in tools, "Supply --tools to compute missing broad text records.")
        adapters.broad_risk(home, source, rows, payloads, tools, commands)
    if not (home / "python-imports.json").is_file():
        adapters.python_graph(home, source, manifest, roots)
    if not (home / "javascript-imports.json").is_file():
        names = [row["path"] for row in rows if row["status"] == "text"
                 and Path(row["path"]).suffix.lower() in (".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx")]
        if names and "node" not in tools:
            r.save(home / "javascript-imports.json", dict(status="unavailable", nodes=[], edges=[],
                omitted=names, limits=["No Node/dependency-cruiser pair was supplied. Graph coverage is unknown."]))
        else:
            adapters.javascript_graph(home, source, rows, tools, commands, tsconfig)
    r.require(tree(source) == expected, "An extraction tool changed captured source.")
    packet.verify_package(package)
    # prepare_side reads a sealed evidence package. This private derivative
    # contains completed records; the original package remains unchanged.
    derived = home.parent / (home.name + "-package")
    derived.mkdir()
    home.rename(derived / "evidence")
    evidence = derived / "evidence"
    r.save(evidence / "seal.json", dict(version=1, artifacts=r.tree(evidence)))
    return derived


def check_live(repo, expected, commands, git="git"):
    binary = shutil.which(git)
    r.require(binary is not None, "Git is absent.")
    manifest, _ = scope.capture(repo, foundation.git_reader(commands, binary, repo, "live"))
    return manifest["coverage"] != "failed" and manifest["signature"] == expected
