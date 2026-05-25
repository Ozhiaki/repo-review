#!/usr/bin/env python3
"""Validate structured pass_output appendices in repo-review artifacts."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


TASTE_VERDICTS = {
    "distinctive",
    "ordinary",
    "strange-unproductively",
    "strange-productively",
    "insufficient-evidence",
}
LOAD_BEARING = {True, False, "partial"}
CONFIDENCE = {"high", "medium", "low"}
COVERAGE = {"thorough", "partial", "thin"}


@dataclass
class ValidationError:
    path: Path
    message: str
    hint: str

    def render(self) -> str:
        return f"{self.path}: {self.message}\n  hint: {self.hint}"


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "null":
        return None
    if value == "true":
        return True
    if value == "false":
        return False
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [parse_scalar(part.strip()) for part in inner.split(",")]
    return value.strip('"').strip("'")


def extract_yaml_block(text: str) -> str | None:
    blocks = re.findall(r"```ya?ml\n(.*?)\n```", text, flags=re.DOTALL)
    for block in reversed(blocks):
        if re.search(r"^pass_output:\s*$", block, flags=re.MULTILINE):
            return block
    return None


def parse_yaml_subset(block: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    lines = block.splitlines()
    index = 0

    while index < len(lines):
        raw = lines[index]
        index += 1
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        if line.startswith("- "):
            continue
        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]

        if value == "|":
            block_lines: list[str] = []
            while index < len(lines):
                next_raw = lines[index]
                next_indent = len(next_raw) - len(next_raw.lstrip(" "))
                if next_raw.strip() and next_indent <= indent:
                    break
                block_lines.append(next_raw[indent + 2 :] if len(next_raw) > indent + 2 else "")
                index += 1
            parent[key] = "\n".join(block_lines).strip()
            continue

        if value:
            parent[key] = parse_scalar(value)
            continue

        child: dict[str, Any] = {}
        parent[key] = child
        stack.append((indent, child))

    return root


def get_path(data: dict[str, Any], dotted: str) -> Any:
    current: Any = data
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def require_path(path: Path, data: dict[str, Any], dotted: str, errors: list[ValidationError]) -> Any:
    value = get_path(data, dotted)
    if value in (None, ""):
        errors.append(
            ValidationError(
                path,
                f"missing required field '{dotted}'",
                f"Add '{dotted}' to the pass_output YAML appendix.",
            )
        )
    return value


def validate_first_read(path: Path, data: dict[str, Any]) -> list[ValidationError]:
    errors: list[ValidationError] = []
    required = [
        "pass_output.pass_id",
        "pass_output.repo",
        "pass_output.analyzed_at",
        "pass_output.central_abstraction.name",
        "pass_output.central_abstraction.location",
        "pass_output.central_abstraction.is_load_bearing",
        "pass_output.taste_verdict",
        "pass_output.signature_move.name",
        "pass_output.signature_move.location",
        "pass_output.weird_file.path",
        "pass_output.weird_file.one_line_why",
        "pass_output.topic_tags",
        "pass_output.confidence.overall",
        "pass_output.confidence.weakest_section",
        "pass_output.confidence.coverage",
        "pass_output.confidence.blind_spots",
    ]
    values = {field: require_path(path, data, field, errors) for field in required}

    if values["pass_output.pass_id"] != "first-read":
        errors.append(
            ValidationError(
                path,
                f"pass_output.pass_id must be 'first-read', got {values['pass_output.pass_id']!r}",
                "Use --pass-id for the expected pass and keep the appendix pass_id aligned.",
            )
        )

    if values["pass_output.central_abstraction.is_load_bearing"] not in LOAD_BEARING:
        errors.append(
            ValidationError(
                path,
                "central_abstraction.is_load_bearing has an invalid value",
                "Use true, false, or partial.",
            )
        )

    if values["pass_output.taste_verdict"] not in TASTE_VERDICTS:
        errors.append(
            ValidationError(
                path,
                "taste_verdict has an invalid value",
                f"Use one of: {', '.join(sorted(TASTE_VERDICTS))}.",
            )
        )

    topic_tags = values["pass_output.topic_tags"]
    if not isinstance(topic_tags, list) or not topic_tags:
        errors.append(
            ValidationError(
                path,
                "topic_tags must be a non-empty list",
                "Use inline YAML list syntax such as topic_tags: [cli-tooling, prompts].",
            )
        )

    if values["pass_output.confidence.overall"] not in CONFIDENCE:
        errors.append(
            ValidationError(path, "confidence.overall has an invalid value", "Use high, medium, or low.")
        )
    if values["pass_output.confidence.coverage"] not in COVERAGE:
        errors.append(
            ValidationError(path, "confidence.coverage has an invalid value", "Use thorough, partial, or thin.")
        )

    return errors


def validate_text(path: Path, text: str, pass_id: str) -> list[ValidationError]:
    block = extract_yaml_block(text)
    if block is None:
        return [
            ValidationError(
                path,
                "missing fenced YAML pass_output appendix",
                "Append a ```yaml block containing pass_output: at the end of the artifact.",
            )
        ]
    data = parse_yaml_subset(block)
    if pass_id == "first-read":
        return validate_first_read(path, data)
    return [
        ValidationError(
            path,
            f"unsupported pass_id '{pass_id}'",
            "This initial validator only supports --pass-id first-read.",
        )
    ]


def validate_file(path: Path, pass_id: str) -> list[ValidationError]:
    return validate_text(path, path.read_text(encoding="utf-8"), pass_id)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate repo-review pass output appendices.")
    parser.add_argument("files", nargs="+", type=Path, help="Pass output artifact files to validate.")
    parser.add_argument("--pass-id", default="first-read", help="Expected pass_id. Currently supports first-read.")
    args = parser.parse_args()

    errors: list[ValidationError] = []
    for path in args.files:
        errors.extend(validate_file(path, args.pass_id))

    if errors:
        for error in errors:
            print(error.render(), file=sys.stderr)
        return 1

    print(f"OK: validated {len(args.files)} {args.pass_id} pass output artifact(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
