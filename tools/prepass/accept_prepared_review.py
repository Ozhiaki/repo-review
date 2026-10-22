#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["tiktoken==0.12.0"]
# ///
"""Run bounded mechanical acceptance in the operator's terminal. No model calls."""
import argparse
import json
from pathlib import Path
from types import SimpleNamespace
import sys

sys.dont_write_bytecode = True
from prepass_runtime import records as r
from prepared_review import cli, instructions, toolset
from prepared_review.artifacts import tree


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--tools", type=Path)
    parser.add_argument("--go", default="go")
    parser.add_argument("--node")
    parser.add_argument("--node-modules", type=Path)
    args = parser.parse_args()
    root = cli.PROJECT
    protected = [root, *([args.tools.resolve().parent] if args.tools else [])]
    output = cli.protected_output(args.out or root.parent / ("prepared-acceptance-" + cli.stamp()), protected)
    r.output_directory(output)
    commands = r.Commands(output / "commands", 3600, 600)
    r.say("Output: " + str(output))
    r.say("Mechanical acceptance only. No model or subject program will run. Press Ctrl-C once to stop.")
    checks = []
    status = dict(state="failed", model_calls=0)
    before = {}
    try:
        before = dict(cli.inputs(), **{str(path): r.digest(path) for path in [
            Path(__file__).resolve(), root / ".github/workflows/ci.yml",
            *sorted((root / "tests").rglob("*.py")),
            *sorted((root / "tests/fixtures").rglob("*.md")),
            *sorted((root / "tools").glob("lint_*.py")),
        ]})
        r.save(output / "processing-inputs.json", before)
        tools_path = args.tools
        if tools_path is None:
            toolset.create(SimpleNamespace(out=output / "tools", rg="rg", ast_grep="ast-grep",
                node=args.node, node_modules=args.node_modules))
            tools_path = output / "tools/tools.json"
        tools_path = Path(tools_path).resolve()
        tools = toolset.load(tools_path)
        r.save(output / "protocol.json", dict(method="prepared", model_calls=0, tools=str(tools_path),
            checks=["existing prompt and schema checks", "source foundation", "packet and service",
                    "packet robustness", "workflow boundaries", "fresh generic source and twin",
                    "source preservation", "snapshot versus live freshness"],
            scope="Mechanical integration acceptance. No review quality or model cost claim."))
        suites = ["run_pass_template_lint_tests.py", "run_pass_output_lint_tests.py", "run_pass_map_lint_tests.py",
                  "run_fixture_coverage_meta_test.py", "run_prepared_source_tests.py", "run_prepared_review_tests.py",
                  "run_prepared_review_robustness_tests.py", "run_prepared_workflow_tests.py"]
        for name in suites:
            r.say("Check: " + name)
            commands.run(name.removesuffix(".py"), [sys.executable, root / "tests" / name], root,
                         environment={"PREPARED_REVIEW_GO": args.go, **cli.GO_ENV})
            checks.append(dict(name=name, passed=True))
        focal, twin = output / "fixtures/focal", output / "fixtures/twin"
        for repo in (focal, twin):
            repo.mkdir(parents=True)
            commands.run("fixture-git-init", ["git", "-C", repo, "init", "-b", "main"], output)
            (repo / "README.md").write_text("A private acceptance source. Do not execute its programs.\n")
            (repo / "main.py").write_text("def run():\n    return 1\n")
        (focal / "go.mod").write_text("module example.invalid/acceptance\n\ngo 1.22\n")
        (focal / "main.go").write_text('package main\nimport "os"\n'
            'func init() { os.WriteFile("EXECUTED", []byte("bad"), 0600) }\nfunc main() {}\n')
        source_before = {str(repo): tree(repo) for repo in (focal, twin)}
        packet = output / "packet"
        commands.run("fresh-generic-preparation", [sys.executable, cli.ENTRY, "prepare", focal, packet,
            "--twin", twin, "--tools", tools_path, "--go", args.go, "--strict"], output)
        prepared = cli.check(packet)
        r.require(prepared["subject"] == "focal" and set(prepared["sides"]) == {"focal", "twin"},
                  "Generic source selection failed.")
        r.require(all(tree(repo) == source_before[str(repo)] for repo in (focal, twin)), "Preparation changed source or Git state.")
        r.require(not (focal / "EXECUTED").exists(), "A subject program ran.")
        for number in instructions.FILES:
            commands.run("handoff-" + number.replace(".", "-"),
                         [sys.executable, cli.ENTRY, "handoff", packet, "--pass", number], output)
        commands.run("snapshot-and-live-check", [sys.executable, cli.ENTRY, "check", packet, "--live"], output)
        # A new source package can be reused without benchmark records or the
        # now unnecessary ast-grep/rg manifest. All required records exist.
        commands.run("reuse-explicit-package", [sys.executable, cli.ENTRY, "prepare", "--package", packet / "work/focal-package",
            "--out", output / "reused-packet", "--go", args.go], output)
        cli.check(output / "reused-packet")
        (focal / "main.py").write_text("def run():\n    return 2\n")
        commands.run("snapshot-still-valid", [sys.executable, cli.ENTRY, "check", packet], output)
        result = commands.run("live-check-detects-change", [sys.executable, cli.ENTRY, "check", packet, "--live"],
                              output, accepted=(1,))
        r.require(json.loads(result["stdout"])["live_matches"]["focal"] is False, "Live freshness failed to identify the edit.")
        (focal / "main.py").write_text("def run():\n    return 1\n")
        r.require(all(tree(repo) == source_before[str(repo)] for repo in (focal, twin)), "Fixture restoration differs.")
        checks.append(dict(name="fresh-source-package-handoff-and-freshness", passed=True))
        r.require(all(r.digest(path) == sha for path, sha in before.items()), "An implementation input changed during acceptance.")
        toolset.load(tools_path)
        checks.append(dict(name="implementation-and-tool-preservation", passed=True))
        status = dict(state="passed", model_calls=0, source_preserved=True, checks=len(checks))
    except KeyboardInterrupt:
        status = dict(state="interrupted", model_calls=0, error="Acceptance was stopped.")
    except Exception as exc:
        status = dict(state="failed", model_calls=0, error=str(exc))
        r.say("Acceptance stopped: " + str(exc))
    finally:
        commands.stop()
        r.save(output / "checks.json", checks)
        r.save(output / "status.json", status)
        (output / "verdict.md").write_text("# Prepared Review acceptance\n\nState: " + status["state"] + ".\n\n"
            "No model was called. Review quality and model cost are not measured.\n" +
            ("\nFailure: " + status["error"] + "\n" if "error" in status else ""))
        cli.write_seal(output)
    r.say("State: " + status["state"] + ". Records: " + str(output))
    return 0 if status["state"] == "passed" else 1


if __name__ == "__main__":
    r.install_interrupt_handler()
    raise SystemExit(main())
