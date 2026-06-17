#!/usr/bin/env python3
"""Meta-lint: every required output-schema field has a dedicated bad fixture.

A test-of-tests guaranteeing the output negative-fixture suite stays complete.
For each required substrate field the output validator enforces, the canonical
`bad-output-<block>-missing-<field>.md` fixture must exist, be registered
expect-fail in run_pass_output_lint_tests.CASES, and actually cause a non-zero
exit. This stops a future field being added to the validator without a matching
negative test silently eroding coverage.

Decision D: scope is the output validator's structured pass_output required
schema fields only (PER_FIELD_BLOCKS). It deliberately does NOT retrofit the
pre-existing template-fixture suite, and the frontmatter and no-future-pass
checks — which are not schema fields — sit outside this assertion (they ship
their own bad fixtures elsewhere). Source-state fields are checked once against
the canonical `source_state` shape, not across the twin/delta multi-state keys.
"""

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))

import lint_pass_outputs as outlint  # noqa: E402
import run_pass_output_lint_tests as harness  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures" / "pass-output-lint"
LINTER = ROOT / "tools" / "lint_pass_outputs.py"


def fixture_name(block_key, field):
    return f"bad-output-{block_key.replace('_', '-')}-missing-{field.replace('_', '-')}.md"


def expect_fail_fixtures():
    return {name for name, should_pass in harness.CASES if not should_pass}


def main():
    expect_fail = expect_fail_fixtures()
    gaps = []

    for block_key, fields in outlint.PER_FIELD_BLOCKS.items():
        for field in fields:
            name = fixture_name(block_key, field)
            path = FIXTURES / name
            reasons = []

            if not path.exists():
                reasons.append("no dedicated bad fixture on disk")
            if name not in expect_fail:
                reasons.append("not registered expect-fail in run_pass_output_lint_tests.CASES")
            if path.exists():
                rc = subprocess.run(
                    [sys.executable, str(LINTER), str(path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                ).returncode
                if rc == 0:
                    reasons.append("fixture does not cause a non-zero exit")

            if reasons:
                gaps.append(f"{block_key}.{field} ({name}): " + "; ".join(reasons))

    if gaps:
        print("Output-schema field coverage is incomplete:")
        for gap in gaps:
            print(f"  - {gap}")
        return 1

    total = sum(len(fields) for fields in outlint.PER_FIELD_BLOCKS.values())
    print(
        f"OK: all {total} required output-schema fields have a dedicated, "
        f"registered, failing bad fixture."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
