#!/usr/bin/env python3
"""Lint repo-review pass prompt templates.

This intentionally validates prompt templates, not generated review outputs.
It uses line scanning only so it can run with stock Python.
"""

import re
import sys
from pathlib import Path


DEFAULT_PASS_FILES = [
    "01-first-read.md",
    "02-discounted-artifact.md",
    "02.5-synthesis.md",
    "03-trace.md",
    "04-twin.md",
    "05-lift.md",
    "06-delta-review.md",
]

SOURCE_FIELDS = ("ref", "ref_kind", "dirty")
PATH_KEYS = {"location", "paths", "source_paths", "focal_paths", "twin_paths"}
SINGLE_REPO_PASSES = {
    "first-read",
    "discounted-artifact",
    "synthesis",
    "trace",
    "lift",
}
SMALLEST_OPEN_PASSES = {
    "first-read",
    "discounted-artifact",
    "synthesis",
    "trace",
    "twin",
    "lift",
}
SMALLEST_OPEN_FIELDS = ("path", "why_this_open", "opened_this_pass")
COVERAGE_CLOSURE_PASSES = {"trace", "twin", "lift"}
COVERAGE_CLOSURE_FIELDS = (
    "chosen_from_pass",
    "path",
    "why_this_was_most_thesis_threatening",
    "finding",
    "changed_prior_judgment",
    "shift_summary",
)
PATH_RE = re.compile(
    r"\b(?:\.{0,2}/)?[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+\.[A-Za-z0-9]{1,8}\b"
)

CANONICAL_PASS_IDS = {
    "first-read",
    "discounted-artifact",
    "synthesis",
    "trace",
    "twin",
    "lift",
    "delta-review",
}

# Sequence-number prefix on a pass-template filename, e.g. "01-" or "02.5-".
SEQ_PREFIX_RE = re.compile(r"^\d+(?:\.\d+)?-")

# Canonical series order (not the prerequisite DAG). delta-review is out-of-band
# and exempt from the no-future-pass rule.
SERIES_ORDER = (
    "first-read",
    "discounted-artifact",
    "synthesis",
    "trace",
    "twin",
    "lift",
)

PASS_DISPLAY_NAMES = {
    "first-read": "First Read",
    "discounted-artifact": "Discounted Artifact",
    "synthesis": "Synthesis",
    "trace": "Trace",
    "twin": "Twin",
    "lift": "Lift",
}


def read_lines(path):
    try:
        return path.read_text(encoding="utf-8").splitlines(), None
    except OSError as exc:
        return None, str(exc)


def has_frontmatter(lines):
    if not lines or lines[0].strip() != "---":
        return False
    for line in lines[1:]:
        if line.strip() == "---":
            return True
    return False


def frontmatter_block(lines):
    """Return [(line_no, text), ...] for lines between the first two `---`.

    Returns [] when there is no terminated frontmatter block.
    """
    if not lines or lines[0].strip() != "---":
        return []
    block = []
    for line_no, line in enumerate(lines[1:], start=2):
        if line.strip() == "---":
            return block
        block.append((line_no, line))
    return []


def frontmatter_scalar(block, key):
    """Return (line_no, value) for a top-level `key: value`, else (None, None)."""
    pattern = re.compile(r"^" + re.escape(key) + r":\s*(.*?)\s*$")
    for line_no, line in block:
        match = pattern.match(line)
        if match:
            return line_no, match.group(1).strip("\"'")
    return None, None


def frontmatter_list(block, key):
    """Return [(line_no, item), ...] for a top-level list `key:`.

    Handles the inline form (`key: []`, `key: [a, b]`) and the block form:

        key:
          - a
          - b
    """
    key_re = re.compile(r"^" + re.escape(key) + r":\s*(.*?)\s*$")
    item_re = re.compile(r"^\s+-\s*(.*?)\s*$")
    for idx, (line_no, line) in enumerate(block):
        match = key_re.match(line)
        if not match:
            continue
        inline = match.group(1).strip()
        if inline:
            if inline.startswith("[") and inline.endswith("]"):
                inline = inline[1:-1].strip()
            return [
                (line_no, item.strip().strip("\"'"))
                for item in inline.split(",")
                if item.strip()
            ]
        items = []
        for child_no, child in block[idx + 1 :]:
            if not child.strip():
                continue
            if not child.startswith(" "):
                break
            item_match = item_re.match(child)
            if item_match:
                items.append((child_no, item_match.group(1).strip("\"'")))
        return items
    return []


def frontmatter_failures(path, lines):
    """Internal-consistency checks on a template's YAML frontmatter."""
    failures = []
    block = frontmatter_block(lines)
    if not block:
        return failures

    # version must be a base-10 integer.
    version_no, version = frontmatter_scalar(block, "version")
    if version is not None:
        try:
            int(version, 10)
        except ValueError:
            failures.append(
                f"{path}:{version_no}: frontmatter version is not an integer: {version!r}"
            )

    # pass_id must match the filename (only for sequence-numbered templates;
    # fixtures and other files without an "NN-"/"NN.N-" prefix are exempt).
    pass_id_no, pass_id = frontmatter_scalar(block, "pass_id")
    if pass_id is not None and SEQ_PREFIX_RE.match(path.name):
        expected = SEQ_PREFIX_RE.sub("", path.stem)
        if pass_id != expected:
            failures.append(
                f"{path}:{pass_id_no}: frontmatter pass_id {pass_id!r} does not "
                f"match filename (expected {expected!r})"
            )

    # Every (recommended_)prerequisite must name a known pass_id.
    for key in ("prerequisites", "recommended_prerequisites"):
        for item_no, item in frontmatter_list(block, key):
            if item not in CANONICAL_PASS_IDS:
                failures.append(
                    f"{path}:{item_no}: {key} names unknown pass_id {item!r}"
                )

    return failures


def prose_lines(lines):
    """Return [(line_no, text), ...] for prose lines only.

    Excludes the YAML frontmatter block and every fenced code block (``` or
    ~~~, any info string). The no-future-pass rule scans prose only: forbidden
    pass names legitimately appear in frontmatter (prerequisites) and in fenced
    appendix skeletons (the shared coverage_closure enum), and must not trip it.
    """
    out = []
    in_frontmatter = bool(lines) and lines[0].strip() == "---"
    fence = None  # active fence marker ("```" or "~~~"), or None
    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()
        if in_frontmatter:
            if line_no > 1 and stripped == "---":
                in_frontmatter = False
            continue
        if fence is None:
            opener = re.match(r"^(```+|~~~+)", stripped)
            if opener:
                fence = opener.group(1)[:3]
                continue
            out.append((line_no, line))
        else:
            if stripped.startswith(fence):
                fence = None
    return out


def forward_reference_failures(path, lines, pass_id):
    """A base-sequence template must not name a later pass in its prose.

    `pass_id` is the template's own identity (from frontmatter). For the template
    at series index i, the forbidden set is every pass at index > i.
    """
    if pass_id not in SERIES_ORDER:
        return []  # delta-review and any off-sequence file are exempt
    later = SERIES_ORDER[SERIES_ORDER.index(pass_id) + 1 :]
    if not later:
        return []

    matchers = []  # (later_pass_id, compiled_pattern)
    for later_pass in later:
        display = PASS_DISPLAY_NAMES[later_pass]
        # 1) Proper-noun display name: case-sensitive, whole word
        #    (matches "Trace" and "The Trace" alike).
        matchers.append((later_pass, re.compile(r"\b" + re.escape(display) + r"\b")))
        # 2) Backticked pass_id in reference position.
        matchers.append((later_pass, re.compile("`" + re.escape(later_pass) + "`")))
        # 3) Bare hyphenated id is unambiguous and safe to match bare; bare
        #    single-word ids (trace/twin/lift/synthesis) are NOT matched, to
        #    avoid false positives on the verbs "trace"/"lift"/"twin".
        if "-" in later_pass:
            matchers.append(
                (later_pass, re.compile(r"\b" + re.escape(later_pass) + r"\b"))
            )

    failures = []
    for line_no, line in prose_lines(lines):
        for later_pass, pattern in matchers:
            if pattern.search(line):
                failures.append(
                    f"{path}:{line_no}: names later pass "
                    f"'{PASS_DISPLAY_NAMES[later_pass]}'"
                )
                break
    return failures


def yaml_fenced_blocks(lines):
    blocks = []
    in_block = False
    start = 0
    current = []

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not in_block and stripped in {"```yaml", "```yml"}:
            in_block = True
            start = idx + 1
            current = []
            continue
        if in_block and stripped == "```":
            blocks.append((start, current))
            in_block = False
            current = []
            continue
        if in_block:
            current.append((idx, line))

    return blocks


def pass_output_block(lines):
    for start, block in yaml_fenced_blocks(lines):
        if any(re.match(r"^\s*pass_output:\s*$", line) for _, line in block):
            return start, block
    return None, None


def value_for_key(block, key):
    pattern = re.compile(r"^\s*" + re.escape(key) + r":\s*(.*?)\s*$")
    for _, line in block:
        match = pattern.match(line)
        if match:
            return match.group(1)
    return None


def indent_of(line):
    return len(line) - len(line.lstrip(" "))


def fields_under(block, key, key_indent):
    """Return (direct_child_field_names, key_present).

    Finds the first line `<key_indent spaces>key:` and collects the names of its
    direct children indented exactly key_indent + 2. Works at any nesting depth,
    so it handles both top-level keys (e.g. `coverage_closure`) and nested ones
    (e.g. `smallest_open` under `confidence`).
    """
    child_indent = key_indent + 2
    key_re = re.compile(r"^" + " " * key_indent + re.escape(key) + r":\s*$")
    child_re = re.compile(r"^" + " " * child_indent + r"([A-Za-z_][A-Za-z0-9_]*):")
    for idx, (_, line) in enumerate(block):
        if not key_re.match(line):
            continue

        found = set()
        for _, child in block[idx + 1 :]:
            if not child.strip():
                continue
            if indent_of(child) <= key_indent:
                break
            child_match = child_re.match(child)
            if child_match:
                found.add(child_match.group(1))
        return found, True

    return set(), False


def block_has_fields(block, key, fields):
    found, present = fields_under(block, key, 2)
    if not present:
        return list(fields)
    return [field for field in fields if field not in found]


def source_notes_lines(block):
    notes = []
    for idx, (_, line) in enumerate(block):
        if not re.match(r"^\s*source_notes:\s*(?:\|.*)?$", line):
            continue
        base_indent = indent_of(line)
        for child_no, child in block[idx + 1 :]:
            if not child.strip():
                continue
            if indent_of(child) <= base_indent:
                break
            notes.append((child_no, child.strip()))
    return notes


def path_field_failures(block, path):
    failures = []
    active_path_indent = None

    for line_no, line in block:
        stripped = line.strip()
        if not stripped:
            continue

        current_indent = indent_of(line)
        if active_path_indent is not None and current_indent <= active_path_indent:
            active_path_indent = None

        key_match = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
        if key_match:
            key, value = key_match.group(1), key_match.group(2)
            if key in PATH_KEYS:
                if ";" in value:
                    failures.append(
                        f"{path}:{line_no}: semicolon-delimited path list in `{key}`"
                    )
                if value == "" or value.startswith("|"):
                    active_path_indent = current_indent
                continue

        if active_path_indent is not None and ";" in line:
            failures.append(
                f"{path}:{line_no}: semicolon-delimited path list in path field"
            )

    return failures


def validate_path(path):
    failures = []

    if not path.exists():
        return [f"{path}: missing pass template"]

    lines, error = read_lines(path)
    if error:
        return [f"{path}: cannot read file: {error}"]

    if not has_frontmatter(lines):
        failures.append(f"{path}: missing YAML frontmatter at top")

    failures.extend(frontmatter_failures(path, lines))

    _, fm_pass_id = frontmatter_scalar(frontmatter_block(lines), "pass_id")
    if fm_pass_id:
        failures.extend(forward_reference_failures(path, lines, fm_pass_id))

    _, block = pass_output_block(lines)
    if block is None:
        failures.append(f"{path}: missing pass_output YAML appendix block")
        return failures

    pass_id = value_for_key(block, "pass_id")
    pass_id = pass_id.strip("\"'") if pass_id else ""

    if pass_id in SINGLE_REPO_PASSES:
        missing = block_has_fields(block, "source_state", SOURCE_FIELDS)
        if missing:
            failures.append(
                f"{path}: source_state missing field(s): {', '.join(missing)}"
            )
    elif pass_id == "twin":
        for key in ("focal_source_state", "twin_source_state"):
            missing = block_has_fields(block, key, SOURCE_FIELDS)
            if missing:
                failures.append(f"{path}: {key} missing field(s): {', '.join(missing)}")
    elif pass_id == "delta-review":
        for key in ("baseline_source_state", "updated_source_state"):
            missing = block_has_fields(block, key, SOURCE_FIELDS)
            if missing:
                failures.append(f"{path}: {key} missing field(s): {', '.join(missing)}")
    else:
        failures.append(f"{path}: unknown or missing pass_id in pass_output block")

    if pass_id in SMALLEST_OPEN_PASSES:
        conf_children, conf_present = fields_under(block, "confidence", 2)
        if not conf_present:
            failures.append(f"{path}: missing confidence block")
        elif "smallest_open" not in conf_children:
            failures.append(f"{path}: confidence missing smallest_open")
        else:
            so_children, _ = fields_under(block, "smallest_open", 4)
            missing = [f for f in SMALLEST_OPEN_FIELDS if f not in so_children]
            if missing:
                failures.append(
                    f"{path}: confidence.smallest_open missing field(s): {', '.join(missing)}"
                )

    if pass_id in COVERAGE_CLOSURE_PASSES:
        cc_children, cc_present = fields_under(block, "coverage_closure", 2)
        if not cc_present:
            failures.append(f"{path}: missing coverage_closure block")
        else:
            missing = [f for f in COVERAGE_CLOSURE_FIELDS if f not in cc_children]
            if missing:
                failures.append(
                    f"{path}: coverage_closure missing field(s): {', '.join(missing)}"
                )

    failures.extend(path_field_failures(block, path))

    for line_no, line in source_notes_lines(block):
        if PATH_RE.search(line):
            failures.append(f"{path}:{line_no}: repo-relative path in source_notes")

    return failures


def main(argv):
    paths = [Path(arg) for arg in argv] if argv else [Path(p) for p in DEFAULT_PASS_FILES]
    failures = []
    for path in paths:
        failures.extend(validate_path(path))

    for failure in failures:
        print(failure)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
