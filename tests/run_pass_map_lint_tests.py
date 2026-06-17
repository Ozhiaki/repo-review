#!/usr/bin/env python3
"""Fixture tests for tools/lint_pass_map.py.

Near-clone of run_pass_output_lint_tests.py, with one addition: each bad case
carries the substring the lint must emit, so the test proves the fixture trips
its own named guard — not merely that *something* failed. A future change that
stopped validating, say, prerequisites would make bad-pass-map-wrong-prerequisite
stop emitting "prerequisites" and turn this suite red, even though the bad fixture
would still (accidentally) exit non-zero for some other reason.

The single good case runs the lint with NO path argument: it then reads the real
PASSES.md and the real frontmatters and must exit 0. There is deliberately no
good-pass-map.md copy — the real PASSES.md is the positive case.
"""

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LINTER = ROOT / "tools" / "lint_pass_map.py"
FIXTURES = ROOT / "tests" / "fixtures" / "pass-map-lint"

# (fixture_name_or_None, should_pass, expect_substring)
# name=None means "invoke with no path argument" (real PASSES.md). Bad cases name
# a table-only fixture that diverges in exactly one guarded column, plus the
# substring that column's drift message must contain.
CASES = [
    (None, True, None),
    ("bad-pass-map-stale-version.md", False, "version"),
    ("bad-pass-map-missing-pass.md", False, "missing"),
    ("bad-pass-map-unknown-pass.md", False, "unknown"),
    ("bad-pass-map-wrong-prerequisite.md", False, "prerequisites"),
]


def run_case(name, should_pass, expect_substring):
    argv = [sys.executable, str(LINTER)]
    if name is not None:
        argv.append(str(FIXTURES / name))
    result = subprocess.run(
        argv,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    passed = result.returncode == 0
    label = name or "<no-arg: real PASSES.md>"

    if passed != should_pass:
        expectation = "pass" if should_pass else "fail"
        return (
            f"{label}: expected {expectation}, got exit {result.returncode}\n"
            f"{result.stdout.strip()}"
        )
    if not should_pass and expect_substring and expect_substring not in result.stdout:
        return (
            f"{label}: failed as expected but output did not contain "
            f"{expect_substring!r}\n{result.stdout.strip()}"
        )
    return None


def main():
    failures = [failure for case in CASES if (failure := run_case(*case))]
    for failure in failures:
        print(failure)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
