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
PATH_RE = re.compile(
    r"\b(?:\.{0,2}/)?[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+\.[A-Za-z0-9]{1,8}\b"
)


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


def block_has_fields(block, key, fields):
    key_re = re.compile(r"^  " + re.escape(key) + r":\s*$")
    for idx, (_, line) in enumerate(block):
        if not key_re.match(line):
            continue

        found = set()
        for _, child in block[idx + 1 :]:
            if not child.strip():
                continue
            if indent_of(child) <= 2:
                break
            child_match = re.match(r"^    ([A-Za-z_][A-Za-z0-9_]*):", child)
            if child_match:
                found.add(child_match.group(1))
        missing = [field for field in fields if field not in found]
        return missing

    return list(fields)


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
