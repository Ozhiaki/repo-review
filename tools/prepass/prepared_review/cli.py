"""Prepare and inspect a fixed source snapshot. No model client or launcher."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys
import time
import uuid

from prepass_runtime import package as foundation, records as r, scope, tokens
from prepass_runtime.cli import positive_seconds
from .artifacts import tree
from . import instructions, packet, preparation, service, toolset, validation

PROJECT = Path(__file__).resolve().parents[3]
ENTRY = PROJECT / "tools/prepass/prepare_review.py"
SEAL = "manifest.sha256.json"
GO_ENV = dict(GOTOOLCHAIN="local", GOPROXY="off", GOSUMDB="off", GOWORK="off", GO111MODULE="off",
              CGO_ENABLED="0", GOENV="off", GOFLAGS="")


def stamp():
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]


def sealed(root, name=SEAL):
    root = Path(root)
    manifest = r.read(root / name)
    expected = manifest.get("artifacts", manifest)
    actual = tree(root)
    actual.pop(name, None)
    r.require(actual == expected, "The sealed records changed: " + str(root))


def write_seal(root):
    actual = tree(root)
    actual.pop(SEAL, None)
    r.save(Path(root) / SEAL, actual)


def inputs():
    paths = [*Path(__file__).parent.glob("*.py"), Path(__file__).with_name("go_facts.go"), ENTRY,
             PROJECT / "docs/PREPASS.md", PROJECT / "docs/OUTPUT_STYLE.md",
             *[PROJECT / name for name in instructions.FILES.values()], Path(sys.executable).resolve()]
    return dict(foundation.processing_inputs(), **tokens.identity(), **{str(p): r.digest(p) for p in paths})


def check(root):
    root = Path(root).expanduser().resolve()
    sealed(root)
    r.require(r.read(root / "status.json")["state"] == "complete", "The prepared packet is incomplete.")
    config = r.read(root / "preparation.json")
    r.require(config["kind"] == "prepared-review-packet-v1" and config["model_calls"] == 0,
              "This is not a Prepared Review packet.")
    for key in ("processing_inputs", "tool_inputs"):
        r.require(all(Path(path).is_file() and r.digest(path) == sha for path, sha in config[key].items()),
                  "A recorded processing or tool input changed.")
    r.require(all(r.hashed_json(tree(path)) == sha for path, sha in config.get("tool_trees", {}).items()),
              "A recorded tool directory changed.")
    r.require(service.tool_hash() == config["tool_sha256"], "The prepared tool definitions changed.")
    for side in config["sides"]:
        manifest = r.read(root / "data" / side / "inventory.json")
        r.require(config["sides"][side]["source_signature"] == manifest["signature"],
                  "The recorded source identity differs from its inventory.")
        r.require(tree(root / "data" / side / "source") == r.read(root / "data" / side / "source.sha256.json"),
                  "Captured source changed.")
        validation.check_side(root, side, strict=False)
    return config


def protected_output(path, protected):
    path = Path(path).expanduser().absolute()
    r.require(not path.exists() and not path.is_symlink(), "Select a fresh output directory.")
    r.require(not any(parent.is_symlink() for parent in path.parents), "An output parent is linked.")
    r.require(".git" not in path.parts, "The output is inside Git state.")
    path = path.resolve()
    for item in protected:
        item = Path(item).resolve()
        r.require(not path.is_relative_to(item) and not item.is_relative_to(path), "The output overlaps protected input.")
    return path


def prepare(args):
    r.require(bool(args.repo) != bool(args.package), "Select a repository or --package.")
    r.require(not args.twin or not args.twin_package, "Select --twin or --twin-package.")
    r.require(not args.repo or args.tools, "Supply --tools for fresh-source preparation.")
    requested = {"focal": ("repo", args.repo) if args.repo else ("package", args.package)}
    if args.twin or args.twin_package:
        requested["twin"] = ("repo", args.twin) if args.twin else ("package", args.twin_package)
    requested = {side: (kind, Path(path).expanduser().resolve()) for side, (kind, path) in requested.items()}
    r.require(args.tools or not any(kind == "repo" for kind, _ in requested.values()),
              "Supply --tools for a fresh focal or twin repository.")
    r.require(not (args.out and args.output), "Supply one output directory.")
    tools = toolset.load(args.tools) if args.tools else {"fingerprints": {}, "tree_fingerprints": {}}
    protected = [PROJECT, *[path for _, path in requested.values()], *tools["fingerprints"], *tools["tree_fingerprints"]]
    output = protected_output(args.out or args.output, protected) if (args.out or args.output) else None
    r.require(output is not None, "Supply an output directory or --out.")
    r.output_directory(output)
    commands = r.Commands(output / "commands", args.total_timeout, args.command_timeout)
    started = time.monotonic()
    r.say("Output: " + str(output))
    r.say("Prepared Review mechanical preparation. No model calls. Press Ctrl-C once to stop.")
    status = dict(state="failed", model_calls=0)
    code = 1
    try:
        fixed = inputs()
        packages = {}
        for side, (kind, path) in requested.items():
            if kind == "repo":
                path = preparation.capture(path, output / "packages" / side, args, commands)
            packet.verify_package(path)
            packages[side] = path
        has_go = any(row["selected"] and row["status"] == "file" and row["path"].endswith(".go")
                     and not row.get("binary") and not row.get("lfs")
                     for path in packages.values() for row in packet.verify_package(path)["records"])
        helper = None
        fingerprints = dict(tools["fingerprints"])
        if has_go:
            compiler = toolset.executable(args.go)
            fingerprints[str(compiler)] = r.digest(compiler)
            commands.run("go-version", [compiler, "version"], output, environment=GO_ENV)
            helper = output / "native/go-facts"
            helper.parent.mkdir()
            commands.run("build-static-go-parser", [compiler, "build", "-trimpath", "-o", helper,
                         Path(__file__).with_name("go_facts.go")], output, environment=GO_ENV)
            fingerprints[str(helper)] = r.digest(helper)
        sides = {}
        for side, package in packages.items():
            roots = args.twin_python_root if side == "twin" else args.python_root
            roots = roots or ["."]
            for name in roots:
                r.require(name == "." or (not Path(name).is_absolute() and ".." not in Path(name).parts
                          and ".git" not in Path(name).parts), "A Python root leaves captured source.")
            derived = preparation.complete_records(package, output / "work" / side, tools, commands, roots,
                args.twin_tsconfig if side == "twin" else args.tsconfig)
            sides[side] = packet.prepare_side(derived, output / "data" / side, helper, commands, tools)
            # Keep the real input identity. Internal derivatives are implementation records.
            sides[side]["package"] = str(package)
            sides[side]["input_kind"], sides[side]["input_path"] = requested[side][0], str(requested[side][1])
            sides[side]["validation"] = validation.check_side(output, side, strict=args.strict)
            if requested[side][0] == "repo":
                r.require(preparation.check_live(requested[side][1], sides[side]["source_signature"], commands, args.git),
                          "Source changed during mechanical preparation.")
        for name in [*instructions.FILES.values(), "docs/OUTPUT_STYLE.md"]:
            target = output / "instructions" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(PROJECT / name, target)
        source_name = Path(r.read(packages["focal"] / "evidence/meta.json")["source_root"]).name
        config = dict(kind="prepared-review-packet-v1", method=instructions.METHOD, method_version=instructions.VERSION,
            model_calls=0, subject=source_name, sides=sides, processing_inputs=fixed,
            tool_inputs=fingerprints, tool_trees=tools["tree_fingerprints"], tool_sha256=service.tool_hash(),
            policy_sha256=r.hashed_json(packet.POLICY), packet_budget=packet.TOKEN_LIMIT, token_encoding="o200k_base",
            budget_note="Packet size proxy, not model token usage.", elapsed_seconds=time.monotonic()-started)
        r.save(output / "preparation.json", config)
        (output / "review-instructions.md").write_text("# Prepared Review\n\n" + packet.POLICY + "\n"
            "Use handoff for the current pass only. Later passes are optional.\n"
            "Use source for behavioral claims. A partial read cannot establish absence.\n"
            "Delivery evidence does not prove understanding. No model cost saving is claimed.\n")
        r.require(all(r.digest(path) == sha for path, sha in fixed.items()), "A processing input changed during preparation.")
        r.require(all(r.digest(path) == sha for path, sha in fingerprints.items()), "A tool changed during preparation.")
        if args.tools:
            toolset.load(args.tools)
        for package in packages.values():
            packet.verify_package(package)
        for side, (kind, path) in requested.items():
            if kind == "repo":
                r.require(preparation.check_live(path, sides[side]["source_signature"], commands, args.git),
                          "Source changed before preparation completed.")
        status = dict(state="complete", model_calls=0, source_preserved=True,
                      packet_tokens={side: row["packet_tokens"] for side, row in sides.items()},
                      coverage={side: row["validation"] for side, row in sides.items()})
        code = 0
    except KeyboardInterrupt:
        status = dict(state="interrupted", model_calls=0, error="Mechanical preparation was stopped.")
        code = 130
    except Exception as exc:
        status = dict(state="failed", model_calls=0, error=str(exc))
        r.say("Preparation stopped: " + str(exc))
    finally:
        commands.stop()
        r.save(output / "status.json", status)
        write_seal(output)
    r.say("State: " + status["state"] + ". No model was called.")
    if code == 0:
        r.say("Packet: " + str(output / "data/focal/packet.md"))
    return code


def config_for(packet_root, state, number, home=None):
    r.require(number in instructions.FILES, "Unknown review pass.")
    return dict(packet=str(packet_root), packet_manifest_sha256=r.digest(Path(packet_root)/SEAL),
                home=str(home or Path(state)/"passes"/number/"attempt-001"), run_home=str(state),
                **{"pass": number}, prepared_tool_sha256=service.tool_hash())


def handoff(root, number):
    r.require(number in instructions.FILES, "Unknown review pass.")
    config = check(root)
    root = Path(root).expanduser().resolve()
    text = (root / "instructions" / instructions.FILES[number]).read_text()
    header = "PREPARED REVIEW: MECHANICAL WORK ALREADY COMPLETE\n" + packet.POLICY + "\n"
    header += "Source state: " + json.dumps(config["sides"]["focal"]["source_state"]) + ".\n"
    header += "Captured source signature: " + config["sides"]["focal"]["source_signature"] + ".\n"
    header += "Use lookup for locations and read_source for behavioral questions.\n"
    header += "STANDING OUTPUT STYLE\n" + (root / "instructions/docs/OUTPUT_STYLE.md").read_text() + "\n"
    if number == "01":
        header += "COMPLETED MECHANICAL PACKET\n" + (root / "data/focal/packet.md").read_text()
    if number == "04":
        r.require("twin" in config["sides"], "Prepare a twin source for pass 04.")
        label = "the captured source at repo='twin', source state " + json.dumps(config["sides"]["twin"]["source_state"])
        text = text.replace("[USER PROVIDES TWIN HERE — repo URL, prior analysis, or pasted files]", label)
        header += "COMPARISON MECHANICAL PACKET\n" + (root / "data/twin/packet.md").read_text()
    return header + "\nCURRENT ANALYTICAL PASS\n" + text


def connect(args):
    root = args.packet.expanduser().resolve()
    prepared = check(root)
    if args.number == "04":
        r.require("twin" in prepared["sides"], "Prepare a twin source for pass 04.")
    state = args.state.expanduser().absolute()
    protected = [PROJECT, root, *[row["input_path"] for row in prepared["sides"].values()]]
    r.require(not state.is_symlink() and not any(p.is_symlink() for p in state.parents), "Review state is linked.")
    r.require(".git" not in state.parts, "Review state is inside Git state.")
    state = state.resolve()
    r.require(all(not state.is_relative_to(p) and not Path(p).is_relative_to(state) for p in map(Path, protected)),
              "Review state overlaps a protected input.")
    identity = dict(method="prepared", method_version=instructions.VERSION,
                    focal_source=prepared["sides"]["focal"]["source_signature"],
                    policy_sha256=prepared["policy_sha256"], tool_sha256=prepared["tool_sha256"],
                    instruction_sha256=r.hashed_json(tree(root / "instructions")))
    if state.exists():
        r.require(r.read(state / "run.json")["identity"] == identity, "Review state belongs to different source or policy.")
    else:
        r.save(state / "run.json", dict(identity=identity, agent=args.agent, model=args.model, reasoning=args.reasoning,
            note="Caller-stated settings. No model was started or measured."))
        (state / "review-note.md").write_text("# Prepared Review run\n\n"
            "Method: prepared, version 1.\n\nSource signature: `" + identity["focal_source"] + "`.\n\n"
            "Caller-stated agent: " + (args.agent or "unknown") + ".\n\n"
            "Caller-stated model: " + (args.model or "unknown") + ".\n\n"
            "Caller-stated reasoning setting: " + (args.reasoning or "unknown") + ".\n\n"
            "Method, agent, and reasoning are separate choices. Delivery does not prove understanding.\n")
    home = state / "passes" / args.number / ("attempt-" + stamp())
    config = config_for(root, state, args.number, home)
    r.save(home / "service.json", config)
    r.save(home / "mcp.json", dict(mcpServers=dict(review=dict(command=sys.executable,
        args=[str(ENTRY), "serve", str(home / "service.json")]))))
    r.say("Connection file: " + str(home / "mcp.json") + ". No model was started.")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    bundle = sub.add_parser("tools", help="record installed static tools without installing them")
    bundle.add_argument("--out", type=Path, required=True)
    bundle.add_argument("--rg", default="rg")
    bundle.add_argument("--ast-grep", default="ast-grep")
    bundle.add_argument("--node")
    bundle.add_argument("--node-modules", type=Path)
    prep = sub.add_parser("prepare", help="prepare mechanical evidence; never start a model")
    prep.add_argument("repo", nargs="?", type=Path)
    prep.add_argument("output", nargs="?", type=Path)
    prep.add_argument("--package", type=Path)
    prep.add_argument("--twin", type=Path)
    prep.add_argument("--twin-package", type=Path)
    prep.add_argument("--out", type=Path)
    prep.add_argument("--tools", type=Path)
    prep.add_argument("--git", default="git")
    prep.add_argument("--go", default="go")
    prep.add_argument("--python-root", action="append")
    prep.add_argument("--twin-python-root", action="append")
    prep.add_argument("--tsconfig")
    prep.add_argument("--twin-tsconfig")
    prep.add_argument("--strict", action="store_true", help="require complete captured source under its scope policy")
    prep.add_argument("--total-timeout", type=positive_seconds, default=3600)
    prep.add_argument("--command-timeout", type=positive_seconds, default=600)
    verify = sub.add_parser("check")
    verify.add_argument("packet", type=Path)
    verify.add_argument("--live", action="store_true", help="also compare the original live checkout")
    prompt = sub.add_parser("handoff")
    prompt.add_argument("packet", type=Path)
    prompt.add_argument("--pass", dest="number", choices=list(instructions.FILES), required=True)
    connection = sub.add_parser("connect")
    connection.add_argument("packet", type=Path)
    connection.add_argument("--state", type=Path, required=True)
    connection.add_argument("--pass", dest="number", choices=list(instructions.FILES), required=True)
    for name in ("agent", "model", "reasoning"):
        connection.add_argument("--" + name)
    serve = sub.add_parser("serve")
    serve.add_argument("config", type=Path)
    args = parser.parse_args(argv)
    if args.action == "tools":
        return toolset.create(args)
    if args.action == "prepare":
        return prepare(args)
    if args.action == "serve":
        service.serve(args.config)
        return 0
    if args.action == "check":
        root = args.packet.expanduser().resolve()
        config = check(root)
        live = {}
        if args.live:
            commands = r.Commands(root.parent / ("live-check-" + stamp()), 1200, 60)
            try:
                for side, row in config["sides"].items():
                    manifest = r.read(root / "data" / side / "inventory.json")
                    meta = r.read(root / "data" / side / "meta.json")
                    live[side] = preparation.check_live(Path(meta["source_root"]), manifest["signature"], commands)
            finally:
                commands.stop()
        print(json.dumps(dict(valid=True, method="prepared", model_calls=0, live_matches=live,
                              packet_tokens={side: row["packet_tokens"] for side, row in config["sides"].items()})))
        return 0 if all(live.values()) else 1
    if args.action == "handoff":
        print(handoff(args.packet, args.number))
        return 0
    return connect(args)
