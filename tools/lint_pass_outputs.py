#!/usr/bin/env python3
"""Lint repo-review *generated outputs* (filled-in pass_output blocks).

This is the sibling of tools/lint_pass_templates.py. That tool validates the
prompt *templates* — skeletons full of `<placeholder>` values — and only checks
field presence. This tool validates a *completed analysis's* pass_output block:
required fields present AND enum membership AND type/shape correctness. A real
output that still carries `<commit | tag | ...>` placeholders is therefore
invalid here, by design.

It reuses the template linter's parsing primitives via an import shim (Decision
A: the template linter is left byte-for-byte unchanged; no shared module is
extracted). Line scanning only, so it runs with stock Python.
"""

import re
import sys
from pathlib import Path

# Decision A import shim: both files live in tools/, so a path insert lets this
# new file import the existing linter's primitives without editing it.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lint_pass_templates as tmpl  # noqa: E402


# --- Enum vocabularies: a controlled copy of docs/STRUCTURED_OUTPUT_SCHEMA.md. ---
# docs/STRUCTURED_OUTPUT_SCHEMA.md stays the canonical, human-facing definition; these
# constants are its executable mirror. Keep every enum here, in one block, so the
# update site is obvious if the schema doc changes (see the drift note in the
# plan / epic risks).
REF_KIND_VALUES = {"commit", "tag", "archive", "date", "pasted-files", "unknown"}
DIRTY_VALUES = {"true", "false", "unknown"}
OVERALL_VALUES = {"high", "medium", "low"}
OPENED_THIS_PASS_VALUES = {"true", "false"}
CHOSEN_FROM_PASS_VALUES = {
    "first-read",
    "discounted-artifact",
    "synthesis",
    "trace",
    "twin",
}
CHANGED_PRIOR_JUDGMENT_VALUES = {"true", "false"}

# The full confidence block the schema doc defines. The template linter models
# only `smallest_open` inside confidence, so this constant is new here.
CONFIDENCE_FIELDS = ("overall", "blind_spots", "smallest_open")

# Reuse the template linter's field tuples and pass-class sets (substrate only).
SOURCE_FIELDS = tmpl.SOURCE_FIELDS
SMALLEST_OPEN_FIELDS = tmpl.SMALLEST_OPEN_FIELDS
COVERAGE_CLOSURE_FIELDS = tmpl.COVERAGE_CLOSURE_FIELDS
SINGLE_REPO_PASSES = tmpl.SINGLE_REPO_PASSES
SMALLEST_OPEN_PASSES = tmpl.SMALLEST_OPEN_PASSES
COVERAGE_CLOSURE_PASSES = tmpl.COVERAGE_CLOSURE_PASSES
CANONICAL_PASS_IDS = tmpl.CANONICAL_PASS_IDS
SERIES_ORDER = tmpl.SERIES_ORDER

# Per-block required-field map for the substrate. Single source for both this
# validator's structure checks and the fixture-coverage meta-lint (#6), which
# imports it to enumerate the one-bad-fixture-per-field matrix.
PER_FIELD_BLOCKS = {
    "source_state": SOURCE_FIELDS,
    "confidence": CONFIDENCE_FIELDS,
    "smallest_open": SMALLEST_OPEN_FIELDS,
    "coverage_closure": COVERAGE_CLOSURE_FIELDS,
}

# Required *top-level* pass_output fields, outside any sub-block: pass_id is the
# routing key, template_version the provenance key. PER_FIELD_BLOCKS models only
# sub-block fields, leaving these two uncovered; the fixture-coverage meta-lint
# (#6) imports this constant to require one dedicated bad fixture per top-level
# required field, the same way it does per sub-block field.
TOP_LEVEL_REQUIRED = ("pass_id", "template_version")

SENTINEL = "<!-- repo-review:pass_output -->"


def clean(value):
    """Strip surrounding whitespace and quotes from a scalar value."""
    return value.strip().strip("\"'") if value is not None else value


def locate_pass_output(lines):
    """Return (start_line, block) for the pass_output block, sentinel-first.

    Prefers the fenced block immediately preceded by the sentinel comment; falls
    back to the template linter's first-`pass_output:`-key heuristic for legacy
    markerless outputs. `block` is a list of (line_no, line) for the body lines,
    matching tmpl.pass_output_block's shape.
    """
    for start, block in tmpl.yaml_fenced_blocks(lines):
        fence_line = start - 1  # the ```yaml line (1-indexed)
        above = fence_line - 1  # candidate sentinel line (1-indexed)
        if above >= 1 and lines[above - 1].strip() == SENTINEL:
            return start, block
    return tmpl.pass_output_block(lines)


def scalar(block, key):
    """Return (line_no, raw_value) for the first `key:` at any indent.

    Callers pass a narrowed sub-block when key names could collide (e.g. `path`
    appears in both smallest_open and coverage_closure).
    """
    pattern = re.compile(r"^\s*" + re.escape(key) + r":\s*(.*?)\s*$")
    for line_no, line in block:
        match = pattern.match(line)
        if match:
            return line_no, match.group(1)
    return None, None


def subblock(block, key, key_indent):
    """Return [(line_no, line), ...] strictly under `key:` at key_indent, or None.

    Children are every following line more-indented than key_indent (blank lines
    included), stopping at the first line indented back to key_indent or less.
    """
    key_re = re.compile(r"^" + " " * key_indent + re.escape(key) + r":\s*$")
    for idx, (line_no, line) in enumerate(block):
        if key_re.match(line):
            sub = []
            for child_no, child in block[idx + 1 :]:
                if child.strip() and tmpl.indent_of(child) <= key_indent:
                    break
                sub.append((child_no, child))
            return sub
    return None


def blind_spots_failures(path, conf):
    """confidence.blind_spots must carry content.

    Accept a non-empty inline scalar (`blind_spots: <text>`) or a block/folded
    scalar (`blind_spots: |` / `>`) followed by >=1 non-blank line indented past
    the key. Fail on a bare `blind_spots:` with no value and no indented body.
    """
    for idx, (line_no, line) in enumerate(conf):
        match = re.match(r"^(\s*)blind_spots:\s*(.*?)\s*$", line)
        if not match:
            continue
        indent = len(match.group(1))
        value = match.group(2)
        if value in ("|", ">", "|-", ">-", "|+", ">+"):
            for _, child in conf[idx + 1 :]:
                if not child.strip():
                    continue
                if tmpl.indent_of(child) > indent:
                    return []  # has a body line
                break
            return [f"{path}:{line_no}: confidence.blind_spots is empty"]
        if value:
            return []  # non-empty inline scalar
        return [f"{path}:{line_no}: confidence.blind_spots is empty"]
    return []  # key absent: handled by the missing-fields check


def enum_failure(path, sub, key, allowed, label):
    """Append-style helper: return [failure] if `key` in `sub` is out of `allowed`."""
    line_no, raw = scalar(sub, key)
    if raw is None:
        return []
    value = clean(raw)
    if value not in allowed:
        return [f"{path}:{line_no}: {label} has invalid value {value!r}"]
    return []


def validate_output(path):
    failures = []

    if not path.exists():
        return [f"{path}: missing output file"]

    lines, error = tmpl.read_lines(path)
    if error:
        return [f"{path}: cannot read file: {error}"]

    _, block = locate_pass_output(lines)
    if block is None:
        return [f"{path}: no pass_output block found (no sentinel, no pass_output: key)"]

    _, pass_id = scalar(block, "pass_id")
    pass_id = clean(pass_id) if pass_id else ""
    if not pass_id:
        return [f"{path}: pass_output missing pass_id"]
    if pass_id not in CANONICAL_PASS_IDS:
        return [f"{path}: pass_output pass_id not in canonical set: {pass_id!r}"]

    # --- template_version: required top-level provenance field. ---
    # Presence + base-10 integer only. A completed output is standalone — there is
    # no frontmatter here to compare against — so this does NOT verify the value is
    # "correct" for any template. Correctness-at-source is guaranteed instead by
    # the template linter's drift guard (#2).
    tv_line, tv_raw = scalar(block, "template_version")
    if tv_raw is None:
        failures.append(f"{path}: pass_output missing template_version")
    else:
        tv = clean(tv_raw)
        try:
            int(tv, 10)
        except ValueError:
            failures.append(
                f"{path}:{tv_line}: pass_output template_version is not an integer: {tv!r}"
            )

    # --- Source state(s): required fields + ref_kind/dirty enums. ---
    if pass_id in SINGLE_REPO_PASSES:
        source_keys = ["source_state"]
    elif pass_id == "twin":
        source_keys = ["focal_source_state", "twin_source_state"]
    elif pass_id == "delta-review":
        source_keys = ["baseline_source_state", "updated_source_state"]
    else:
        source_keys = []

    for key in source_keys:
        missing = tmpl.block_has_fields(block, key, SOURCE_FIELDS)
        if missing:
            failures.append(f"{path}: {key} missing field(s): {', '.join(missing)}")
            continue
        sub = subblock(block, key, 2)
        failures.extend(enum_failure(path, sub, "ref_kind", REF_KIND_VALUES, f"{key}.ref_kind"))
        failures.extend(enum_failure(path, sub, "dirty", DIRTY_VALUES, f"{key}.dirty"))

    # --- Confidence block (every standard single-repo pass). ---
    if pass_id in SMALLEST_OPEN_PASSES:
        conf_children, conf_present = tmpl.fields_under(block, "confidence", 2)
        if not conf_present:
            failures.append(f"{path}: missing confidence block")
        else:
            missing = [f for f in CONFIDENCE_FIELDS if f not in conf_children]
            if missing:
                failures.append(
                    f"{path}: confidence missing field(s): {', '.join(missing)}"
                )
            conf = subblock(block, "confidence", 2)
            if "overall" in conf_children:
                failures.extend(
                    enum_failure(path, conf, "overall", OVERALL_VALUES, "confidence.overall")
                )
            if "blind_spots" in conf_children:
                failures.extend(blind_spots_failures(path, conf))
            if "smallest_open" in conf_children:
                so_children, _ = tmpl.fields_under(block, "smallest_open", 4)
                so_missing = [f for f in SMALLEST_OPEN_FIELDS if f not in so_children]
                if so_missing:
                    failures.append(
                        f"{path}: confidence.smallest_open missing field(s): "
                        f"{', '.join(so_missing)}"
                    )
                smallest = subblock(block, "smallest_open", 4)
                if "opened_this_pass" in so_children:
                    failures.extend(
                        enum_failure(
                            path,
                            smallest,
                            "opened_this_pass",
                            OPENED_THIS_PASS_VALUES,
                            "smallest_open.opened_this_pass",
                        )
                    )

    # --- Coverage closure (trace / twin / lift). ---
    if pass_id in COVERAGE_CLOSURE_PASSES:
        cc_children, cc_present = tmpl.fields_under(block, "coverage_closure", 2)
        if not cc_present:
            failures.append(f"{path}: missing coverage_closure block")
        else:
            missing = [f for f in COVERAGE_CLOSURE_FIELDS if f not in cc_children]
            if missing:
                failures.append(
                    f"{path}: coverage_closure missing field(s): {', '.join(missing)}"
                )
            cc = subblock(block, "coverage_closure", 2)

            chosen_line, chosen_raw = scalar(cc, "chosen_from_pass")
            chosen = clean(chosen_raw) if chosen_raw is not None else None
            if chosen is not None and chosen not in CHOSEN_FROM_PASS_VALUES:
                failures.append(
                    f"{path}:{chosen_line}: coverage_closure.chosen_from_pass "
                    f"has invalid value {chosen!r}"
                )
            elif (
                chosen in SERIES_ORDER
                and pass_id in SERIES_ORDER
                and SERIES_ORDER.index(chosen) >= SERIES_ORDER.index(pass_id)
            ):
                # Cross-check (connects to the no-future-pass rule): the closed
                # blind spot must come from a strictly earlier pass.
                failures.append(
                    f"{path}:{chosen_line}: coverage_closure.chosen_from_pass "
                    f"{chosen!r} is not earlier than {pass_id!r}"
                )

            cpj_line, cpj_raw = scalar(cc, "changed_prior_judgment")
            cpj = clean(cpj_raw) if cpj_raw is not None else None
            if cpj is not None and cpj not in CHANGED_PRIOR_JUDGMENT_VALUES:
                failures.append(
                    f"{path}:{cpj_line}: coverage_closure.changed_prior_judgment "
                    f"is not a bool: {cpj!r}"
                )

            shift_line, shift_raw = scalar(cc, "shift_summary")
            shift = clean(shift_raw) if shift_raw is not None else None
            is_null = shift in (None, "", "null", "~")
            if cpj == "true" and is_null:
                failures.append(
                    f"{path}:{shift_line or cpj_line}: coverage_closure.shift_summary "
                    f"must be non-null when changed_prior_judgment is true"
                )
            if cpj == "false" and not is_null:
                failures.append(
                    f"{path}:{shift_line}: coverage_closure.shift_summary should be "
                    f"null when changed_prior_judgment is false"
                )

    # --- Path-field shape (reused from the template linter). ---
    failures.extend(tmpl.path_field_failures(block, path))
    for line_no, line in tmpl.source_notes_lines(block):
        if tmpl.PATH_RE.search(line):
            failures.append(f"{path}:{line_no}: repo-relative path in source_notes")

    return failures


def main(argv):
    if not argv:
        print("usage: lint_pass_outputs.py <output-file>...", file=sys.stderr)
        return 2

    failures = []
    for arg in argv:
        failures.extend(validate_output(Path(arg)))

    for failure in failures:
        print(failure)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
