#!/usr/bin/env python3
"""Validate repo-review pass prompt frontmatter."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REQUIRED_KEYS = {
    "pass_id",
    "name",
    "version",
    "prerequisites",
    "output_kind",
    "terminates_early_when",
    "intended_audience",
}

KNOWN_OUTPUT_KINDS = {"prose-with-yaml-appendix"}
KNOWN_TERMINATION = {
    "never",
    "repo-has-no-load-bearing-obligation",
    "repo-yields-no-extractables",
}
KNOWN_AUDIENCES = {
    "builders-considering-extraction",
    "human-curator",
    "downstream-analysis-passes",
    "downstream-extraction-tools",
}
INCREMENTAL_KEYS = {
    "incremental_review",
    "claim_outputs",
    "watch_paths",
    "invalidation_triggers",
}


@dataclass
class LintError:
    path: Path
    message: str
    hint: str

    def render(self) -> str:
        return f"{self.path}: {self.message}\n  hint: {self.hint}"


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "[]":
        return []
    if value == "null":
        return None
    if value.isdigit():
        return int(value)
    return value.strip('"').strip("'")


def parse_frontmatter(path: Path) -> tuple[dict[str, Any] | None, list[LintError]]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, [
            LintError(
                path,
                "missing YAML frontmatter fence",
                "Start pass files with a '---' frontmatter block.",
            )
        ]

    end = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = index
            break

    if end is None:
        return None, [
            LintError(
                path,
                "unterminated YAML frontmatter",
                "Add a closing '---' line before the markdown body.",
            )
        ]

    data: dict[str, Any] = {}
    current_key: str | None = None
    for raw in lines[1:end]:
        if not raw.strip():
            continue
        if raw.startswith("  - "):
            if current_key is None:
                return None, [
                    LintError(
                        path,
                        "list item appears before a key",
                        "Place list items under keys like prerequisites or intended_audience.",
                    )
                ]
            data.setdefault(current_key, [])
            if not isinstance(data[current_key], list):
                return None, [
                    LintError(
                        path,
                        f"{current_key} mixes scalar and list syntax",
                        f"Use either '{current_key}: []' or an indented list, not both.",
                    )
                ]
            data[current_key].append(parse_scalar(raw[4:]))
            continue
        if raw.startswith(" "):
            return None, [
                LintError(
                    path,
                    "unsupported nested frontmatter",
                    "Keep pass frontmatter to top-level scalars and simple lists.",
                )
            ]
        if ":" not in raw:
            return None, [
                LintError(
                    path,
                    f"malformed frontmatter line: {raw}",
                    "Use 'key: value' syntax.",
                )
            ]
        key, value = raw.split(":", 1)
        key = key.strip()
        current_key = key
        if value.strip():
            data[key] = parse_scalar(value)
        else:
            data[key] = []
    return data, []


def validate_file(path: Path, known_pass_ids: set[str] | None = None) -> tuple[dict[str, Any] | None, list[LintError]]:
    frontmatter, errors = parse_frontmatter(path)
    if errors or frontmatter is None:
        return frontmatter, errors

    missing = sorted(REQUIRED_KEYS - frontmatter.keys())
    for key in missing:
        errors.append(
            LintError(
                path,
                f"missing required key '{key}'",
                f"Add '{key}' to the pass frontmatter.",
            )
        )

    extra_incremental = sorted(INCREMENTAL_KEYS & frontmatter.keys())
    if extra_incremental:
        errors.append(
            LintError(
                path,
                f"unsupported incremental frontmatter keys: {', '.join(extra_incremental)}",
                "Phase 0 defines the incremental substrate, but pass frontmatter has not adopted these keys yet.",
            )
        )

    pass_id = frontmatter.get("pass_id")
    if not isinstance(pass_id, str) or not pass_id:
        errors.append(LintError(path, "pass_id must be a non-empty string", "Use a stable kebab-case pass id."))

    name = frontmatter.get("name")
    if not isinstance(name, str) or not name:
        errors.append(LintError(path, "name must be a non-empty string", "Use the human pass name."))

    version = frontmatter.get("version")
    if not isinstance(version, int) or version < 1:
        errors.append(LintError(path, "version must be a positive integer", "Set version to an integer like 2."))

    prerequisites = frontmatter.get("prerequisites")
    if not isinstance(prerequisites, list):
        errors.append(LintError(path, "prerequisites must be a list", "Use prerequisites: [] or an indented list."))
    elif known_pass_ids is not None:
        for prereq in prerequisites:
            if prereq not in known_pass_ids:
                errors.append(
                    LintError(
                        path,
                        f"unknown prerequisite pass_id '{prereq}'",
                        f"Use one of: {', '.join(sorted(known_pass_ids))}.",
                    )
                )

    recommended_prerequisites = frontmatter.get("recommended_prerequisites", [])
    if not isinstance(recommended_prerequisites, list):
        errors.append(
            LintError(
                path,
                "recommended_prerequisites must be a list when present",
                "Use recommended_prerequisites: [] or an indented list.",
            )
        )
    elif known_pass_ids is not None:
        for prereq in recommended_prerequisites:
            if prereq not in known_pass_ids:
                errors.append(
                    LintError(
                        path,
                        f"unknown recommended prerequisite pass_id '{prereq}'",
                        f"Use one of: {', '.join(sorted(known_pass_ids))}.",
                    )
                )

    output_kind = frontmatter.get("output_kind")
    if output_kind not in KNOWN_OUTPUT_KINDS:
        errors.append(
            LintError(
                path,
                f"unknown output_kind '{output_kind}'",
                f"Use one of: {', '.join(sorted(KNOWN_OUTPUT_KINDS))}.",
            )
        )

    termination = frontmatter.get("terminates_early_when")
    if termination not in KNOWN_TERMINATION:
        errors.append(
            LintError(
                path,
                f"unknown terminates_early_when '{termination}'",
                f"Use one of: {', '.join(sorted(KNOWN_TERMINATION))}.",
            )
        )

    audience = frontmatter.get("intended_audience")
    if not isinstance(audience, list) or not audience:
        errors.append(LintError(path, "intended_audience must be a non-empty list", "List at least one supported audience."))
    else:
        for item in audience:
            if item not in KNOWN_AUDIENCES:
                errors.append(
                    LintError(
                        path,
                        f"unknown intended_audience '{item}'",
                        f"Use one of: {', '.join(sorted(KNOWN_AUDIENCES))}.",
                    )
                )

    return frontmatter, errors


def default_pass_files(root: Path) -> list[Path]:
    return sorted(root.glob("[0-9][0-9]-*.md"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate repo-review pass prompt frontmatter.")
    parser.add_argument("files", nargs="*", type=Path, help="Pass markdown files to lint. Defaults to root pass files.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root for default pass discovery.")
    args = parser.parse_args()

    paths = args.files or default_pass_files(args.root)
    if not paths:
        print("No pass files found.", file=sys.stderr)
        return 2

    known_pass_ids: set[str] = set()
    parsed: dict[Path, dict[str, Any]] = {}
    errors: list[LintError] = []

    for path in paths:
        frontmatter, parse_errors = parse_frontmatter(path)
        if parse_errors or frontmatter is None:
            errors.extend(parse_errors)
            continue
        parsed[path] = frontmatter
        pass_id = frontmatter.get("pass_id")
        if isinstance(pass_id, str) and pass_id:
            known_pass_ids.add(pass_id)

    for path in paths:
        _, file_errors = validate_file(path, known_pass_ids)
        errors.extend(file_errors)

    if errors:
        for error in errors:
            print(error.render(), file=sys.stderr)
        return 1

    print(f"OK: validated {len(paths)} pass frontmatter block(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
