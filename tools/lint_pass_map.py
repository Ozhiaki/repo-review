#!/usr/bin/env python3
"""Drift guard for PASSES.md against the seven template frontmatters.

PASSES.md is a hand-authored, human-facing view of the series (see #4). The
frontmatters are the single source of truth; this lint guarantees the map's
machine-derivable columns never silently drift from them — a stale version cell,
a dropped prerequisite, a row for a pass that no longer exists.

Usage:

    python3 tools/lint_pass_map.py [pass_map_path]

`pass_map_path` is positional and optional, defaulting to <repo-root>/docs/PASSES.md.
The seven real template frontmatters are ALWAYS read from the repo root,
independent of `pass_map_path`. That split — table from the argument, frontmatters
always from the real templates — is what lets a bad fixture supply only a
divergent table while still being checked against the true frontmatters.

It reuses the template linter's frontmatter parser via the same two-line sys.path
import shim that lint_pass_outputs.py uses; the template linter is left
byte-for-byte unchanged (Decision A — no shared module is extracted). Line
scanning only, so it runs with stock Python.
"""

import sys
from pathlib import Path

# Decision A import shim (identical to lint_pass_outputs.py): both files live in
# tools/, so a path insert lets this file import the template linter's primitives
# without editing it.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lint_pass_templates as tmpl  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PASS_MAP = REPO_ROOT / "docs" / "PASSES.md"

EMDASH = "—"  # — : the empty-list rendering in the serialization contract

# Table columns, in order. The first seven are machine-derived from frontmatter
# and guarded here; `catches` is human prose and is not.
COLUMNS = (
    "pass_id",
    "name",
    "version",
    "prerequisites",
    "recommended",
    "output_kind",
    "terminates_early_when",
    "catches",
)

# Frontmatter keys the guarded scalar/list columns map onto.
SCALAR_COLUMNS = {
    "name": "name",
    "version": "version",
    "output_kind": "output_kind",
    "terminates_early_when": "terminates_early_when",
}
LIST_COLUMNS = {
    "prerequisites": "prerequisites",
    "recommended": "recommended_prerequisites",
}


def parse_list_cell(cell):
    """Token SET for a list cell, per the serialization contract.

    An empty cell (blank or a lone em dash) is the empty set; otherwise split on
    commas, trim each token, and drop a lone em dash. Comparison is order- and
    duplicate-insensitive, so the set is the right shape.
    """
    cell = cell.strip()
    if cell in ("", EMDASH):
        return set()
    return {tok.strip() for tok in cell.split(",") if tok.strip() and tok.strip() != EMDASH}


def is_separator_row(cells):
    return bool(cells) and all(c and set(c) <= set(":-") for c in cells)


def table_rows(lines):
    """Yield the table's data rows as lists of stripped cells.

    A table line is one whose stripped form starts with `|`. The header row
    (first cell `pass_id`) and the `---|---` separator row are skipped; the
    Mermaid block carries no leading-pipe lines, so it is naturally ignored.
    """
    rows = []
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if cells and cells[0] == "pass_id":
            continue
        if is_separator_row(cells):
            continue
        rows.append(cells)
    return rows


def read_frontmatters():
    """Map pass_id -> {name, version, output_kind, terminates_early_when,
    prerequisites(set), recommended_prerequisites(set)} from the real templates."""
    fm = {}
    for filename in tmpl.DEFAULT_PASS_FILES:
        path = REPO_ROOT / filename
        lines, error = tmpl.read_lines(path)
        if error:
            continue
        block = tmpl.frontmatter_block(lines)
        pass_id = tmpl.frontmatter_scalar(block, "pass_id")[1]
        if not pass_id:
            continue
        fm[pass_id] = {
            "name": tmpl.frontmatter_scalar(block, "name")[1],
            "version": tmpl.frontmatter_scalar(block, "version")[1],
            "output_kind": tmpl.frontmatter_scalar(block, "output_kind")[1],
            "terminates_early_when": tmpl.frontmatter_scalar(
                block, "terminates_early_when"
            )[1],
            "prerequisites": {i for _, i in tmpl.frontmatter_list(block, "prerequisites")},
            "recommended_prerequisites": {
                i for _, i in tmpl.frontmatter_list(block, "recommended_prerequisites")
            },
        }
    return fm


def lint(pass_map_path):
    label = pass_map_path.name
    failures = []

    lines, error = tmpl.read_lines(pass_map_path)
    if error:
        return [f"{label}: cannot read pass map: {error}"]

    fm = read_frontmatters()
    rows = table_rows(lines)

    # --- Check 1: coverage. Every canonical pass exactly once; no unknown pass. ---
    seen = {}
    for cells in rows:
        if len(cells) != len(COLUMNS):
            failures.append(
                f"{label}: table row has {len(cells)} columns, expected {len(COLUMNS)}: {cells}"
            )
            continue
        pass_id = cells[0]
        seen[pass_id] = seen.get(pass_id, 0) + 1
        if pass_id not in tmpl.CANONICAL_PASS_IDS:
            failures.append(f"{label}: unknown pass {pass_id!r} in table (no such frontmatter)")

    for pass_id in sorted(tmpl.CANONICAL_PASS_IDS):
        if pass_id not in seen:
            failures.append(f"{label}: missing pass {pass_id!r} from table")
    for pass_id, count in seen.items():
        if count > 1:
            failures.append(
                f"{label}: pass {pass_id!r} appears {count} times in table (expected exactly once)"
            )

    # --- Check 2: per-column drift against frontmatter. ---
    for cells in rows:
        if len(cells) != len(COLUMNS):
            continue
        row = dict(zip(COLUMNS, cells))
        pass_id = row["pass_id"]
        truth = fm.get(pass_id)
        if truth is None:
            continue  # unknown pass already reported by check 1

        for column, fm_key in SCALAR_COLUMNS.items():
            said = row[column].strip()
            expected = (truth[fm_key] or "").strip()
            if said != expected:
                failures.append(
                    f"{label}: {pass_id}: {column} says {said!r}, "
                    f"frontmatter says {expected!r}"
                )

        for column, fm_key in LIST_COLUMNS.items():
            said = parse_list_cell(row[column])
            expected = truth[fm_key]
            if said != expected:
                said_str = ", ".join(sorted(said)) or EMDASH
                exp_str = ", ".join(sorted(expected)) or EMDASH
                failures.append(
                    f"{label}: {pass_id}: {column} says {said_str!r}, "
                    f"frontmatter says {exp_str!r}"
                )

    return failures


def main(argv):
    pass_map_path = Path(argv[0]) if argv else DEFAULT_PASS_MAP
    failures = lint(pass_map_path)
    for failure in failures:
        print(failure)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
