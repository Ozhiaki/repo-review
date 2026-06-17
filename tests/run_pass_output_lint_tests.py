#!/usr/bin/env python3
"""Fixture tests for tools/lint_pass_outputs.py."""

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LINTER = ROOT / "tools" / "lint_pass_outputs.py"
FIXTURES = ROOT / "tests" / "fixtures" / "pass-output-lint"

CASES = [
    # Good: one valid filled output per pass class.
    ("good-output-delta-review.md", True),
    ("good-output-first-read.md", True),
    ("good-output-trace.md", True),
    ("good-output-twin.md", True),
    # Per-field presence: one bad fixture per required substrate field. The
    # filename is bad-output-<block>-missing-<field>.md, derived mechanically
    # from the field name; the coverage-meta-test asserts this set is complete.
    ("bad-output-source-state-missing-ref.md", False),
    ("bad-output-source-state-missing-ref-kind.md", False),
    ("bad-output-source-state-missing-dirty.md", False),
    ("bad-output-confidence-missing-overall.md", False),
    ("bad-output-confidence-missing-blind-spots.md", False),
    ("bad-output-confidence-missing-smallest-open.md", False),
    ("bad-output-smallest-open-missing-path.md", False),
    ("bad-output-smallest-open-missing-why-this-open.md", False),
    ("bad-output-smallest-open-missing-opened-this-pass.md", False),
    ("bad-output-coverage-closure-missing-chosen-from-pass.md", False),
    ("bad-output-coverage-closure-missing-path.md", False),
    ("bad-output-coverage-closure-missing-why-this-was-most-thesis-threatening.md", False),
    ("bad-output-coverage-closure-missing-finding.md", False),
    ("bad-output-coverage-closure-missing-changed-prior-judgment.md", False),
    ("bad-output-coverage-closure-missing-shift-summary.md", False),
    # Block presence: a whole substrate block (incl. multi-state variants) gone.
    ("bad-output-missing-source-state.md", False),
    ("bad-output-twin-missing-focal-source-state.md", False),
    ("bad-output-twin-missing-twin-source-state.md", False),
    ("bad-output-delta-missing-baseline-source-state.md", False),
    ("bad-output-delta-missing-updated-source-state.md", False),
    ("bad-output-missing-confidence.md", False),
    ("bad-output-missing-coverage-closure.md", False),
    # Value level: enum / type / path-shape / conditional violations.
    ("bad-output-bad-ref-kind-enum.md", False),
    ("bad-output-bad-overall-enum.md", False),
    ("bad-output-opened-this-pass-not-bool.md", False),
    ("bad-output-chosen-from-pass-bad-enum.md", False),
    ("bad-output-changed-prior-judgment-not-bool.md", False),
    ("bad-output-shift-summary-null-when-changed.md", False),
    ("bad-output-path-in-source-notes.md", False),
    ("bad-output-semicolon-paths.md", False),
]


def run_case(name, should_pass):
    path = FIXTURES / name
    result = subprocess.run(
        [sys.executable, str(LINTER), str(path)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    passed = result.returncode == 0
    if passed == should_pass:
        return None

    expectation = "pass" if should_pass else "fail"
    return (
        f"{name}: expected {expectation}, got exit {result.returncode}\n"
        f"{result.stdout.strip()}"
    )


def main():
    failures = [failure for name, ok in CASES if (failure := run_case(name, ok))]
    for failure in failures:
        print(failure)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
