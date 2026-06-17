#!/usr/bin/env python3
"""Fixture tests for tools/lint_pass_templates.py."""

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LINTER = ROOT / "tools" / "lint_pass_templates.py"
FIXTURES = ROOT / "tests" / "fixtures" / "pass-template-lint"

CASES = [
    ("good-first-read.md", True),
    ("good-synthesis.md", True),
    ("good-trace.md", True),
    ("bad-missing-source-state.md", False),
    ("bad-semicolon-in-paths.md", False),
    ("bad-path-in-source-notes.md", False),
    ("bad-no-frontmatter.md", False),
    ("bad-missing-delta-source-state.md", False),
    ("bad-missing-smallest-open.md", False),
    ("bad-smallest-open-missing-path.md", False),
    ("bad-smallest-open-missing-why-this-open.md", False),
    ("bad-smallest-open-missing-opened-this-pass.md", False),
    ("bad-missing-coverage-closure.md", False),
    ("bad-coverage-closure-missing-chosen-from-pass.md", False),
    ("bad-coverage-closure-missing-path.md", False),
    ("bad-coverage-closure-missing-rationale.md", False),
    ("bad-coverage-closure-missing-finding.md", False),
    ("bad-coverage-closure-missing-changed-prior-judgment.md", False),
    ("bad-coverage-closure-missing-shift-summary-when-true.md", False),
    # Frontmatter consistency checks. The pass_id<->filename fixture carries a
    # numeric "NN-" prefix so the filename check applies to it (fixtures without
    # such a prefix are exempt, as the good-*.md fixtures are).
    ("99-passid-filename-mismatch.md", False),
    ("bad-frontmatter-unknown-prerequisite.md", False),
    ("bad-frontmatter-version-not-int.md", False),
    # No-future-pass rule: a base-sequence template must not name a later pass
    # in its prose.
    ("good-synthesis-no-forward-ref.md", True),
    ("bad-synthesis-names-trace.md", False),
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
