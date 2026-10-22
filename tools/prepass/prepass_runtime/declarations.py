"""Build declaration and syntax records from logged native output."""
from __future__ import annotations

from collections import defaultdict
from bisect import bisect_left
import hashlib
import json
from pathlib import Path
import re

from . import catalog as prepass
from . import records as s

SYNTAX = Path(__file__).resolve().parent / "assets/syntax.yaml"
IGNORE = [item for name in ("hidden", "dot", "exclude", "global", "parent", "vcs") for item in ("--no-ignore", name)]


def syntax_rules():
    return [json.loads(part) for part in SYNTAX.read_text().split("\n---\n")]


def outline_rules(languages, extra=True):
    rules = []
    for language in sorted(languages):
        kinds = list(prepass.OUTLINE_KINDS[language])
        if extra and language == "go":
            kinds.append("type_alias")
        for kind in kinds:
            rules.append(dict(id=language + "." + kind, language=language, severity="hint", rule=dict(kind=kind)))
    return rules


def inline(rules):
    return "\n---\n".join(json.dumps(rule, ensure_ascii=True) for rule in rules)


def relative(name, root, selected):
    path = Path(name)
    if path.is_absolute():
        name = path.relative_to(root).as_posix()
    else:
        name = name.removeprefix("./")
    s.require(name in selected, "Native output names a file outside its selected batch.")
    return name


def normalize(native, root, selected, payloads, family):
    records = []
    metadata = {name: (hashlib.sha256(payloads[name]).hexdigest(), [match.start() for match in re.finditer(b"\n", payloads[name])])
                for name in selected}
    for item in native:
        name = relative(item["file"], root, selected)
        data = payloads[name]
        interval = item["range"]
        start, end = interval["byteOffset"]["start"], interval["byteOffset"]["end"]
        s.require(type(start) is int and type(end) is int and 0 <= start < end <= len(data), "Invalid native byte offsets.")
        s.require(data[start:end] == item["text"].encode("utf-8"), "Native match bytes differ from source bytes.")
        source_hash, newline_offsets = metadata[name]
        first, last = bisect_left(newline_offsets, start) + 1, bisect_left(newline_offsets, end) + 1
        s.require(first == interval["start"]["line"] + 1 and last == interval["end"]["line"] + 1,
                  "Native line and byte coordinates disagree.")
        rule = item["ruleId"]
        identity = s.hashed_json([name, source_hash, rule, start, end])
        row = dict(id=identity, path=name, sha256=source_hash, rule=rule,
                   start=start, end=end, line=first, end_line=last, text=item["text"])
        if family == "outline":
            language, kind = rule.split(".", 1)
            row.update(language=language, kind=kind, parent=None, relation="selected_declaration_byte_containment")
        else:
            row.update(category=rule.split("-", 1)[1], resolution="syntax_only")
        records.append(row)
    unique = {row["id"]: row for row in records}
    return sorted(unique.values(), key=lambda row: (row["path"], row["start"], -row["end"], row["rule"]))


def parents(records):
    stacks = defaultdict(list)
    for row in records:
        stack = stacks[row["path"]]
        while stack and not (stack[-1]["start"] <= row["start"] and row["end"] <= stack[-1]["end"]
                             and (stack[-1]["start"], stack[-1]["end"]) != (row["start"], row["end"])):
            stack.pop()
        row["parent"] = stack[-1]["id"] if stack else None
        stack.append(row)


def inspected_files(stderr, root, batch):
    # Entity logs contain literal paths, including newlines. Match complete
    # selected names before treating the remaining diagnostics as lines.
    names = {value for name in batch for value in (name, "./" + name, str(root / name))}
    alternatives = "|".join(re.escape(name) for name in sorted(names, key=lambda name: (-len(name), name)))
    entity = re.compile(r"^sg: entity\|file\|(?P<path>" + alternatives
                        + r"): language=[^,\r\n]+,appliedRuleCount=(?P<count>\d+)\r?$", re.MULTILINE)
    inspected = set()
    def consume(match):
        if int(match["count"]) > 0:
            inspected.add(relative(match["path"], root, batch))
        return ""
    remainder = entity.sub(consume, stderr.decode("utf-8", "replace"))
    other = [line for line in remainder.splitlines()
             if line and not line.startswith(("sg: summary|", "sg: entity|rule|"))]
    return inspected, other


def scan(root, inventory, payloads, family, native, bad=False):
    statuses, records, errors = {}, [], []
    available = {row["path"] for row in inventory if row["status"] == "text"}
    rules = syntax_rules() if family == "syntax" else outline_rules({prepass.SG_LANG_BY_EXT[Path(name).suffix.lower()]
                   for name in available if Path(name).suffix.lower() in prepass.SG_LANG_BY_EXT})
    supported = {rule["language"].lower() for rule in rules}
    targets = []
    for row in inventory:
        name = row["path"]
        language = prepass.SG_LANG_BY_EXT.get(Path(name).suffix.lower())
        reason = row["status"] if row["status"] != "text" else "empty" if row["bytes"] == 0 else "unsupported_language" if language not in supported else None
        statuses[name] = dict(path=name, sha256=row.get("sha256"), status=reason or "pending", syntax_validity="not_checked")
        if not reason:
            targets.append(name)
    for offset in range(0, len(targets), 100):
        batch = targets[offset:offset + 100]
        selected_languages = {prepass.SG_LANG_BY_EXT[Path(name).suffix.lower()] for name in batch}
        batch_rules = [rule for rule in rules if rule["language"].lower() in selected_languages]
        if bad:
            batch_rules = [dict(id="python.invalid-kind", language="python", rule=dict(kind="THIS_KIND_DOES_NOT_EXIST"))]
        response = native(family + "-" + str(offset // 100), inline(batch_rules), batch)
        good_exit = response["returncode"] in (0, 1)
        inspected, other = inspected_files(response["stderr"], root, batch)
        if not good_exit or other:
            errors.append(dict(batch=batch, returncode=response["returncode"], stderr=response["stderr"].decode("utf-8", "replace")))
            for name in batch:
                statuses[name]["status"] = "scan_error"
            continue
        try:
            output = json.loads(response["stdout"])
            s.require(isinstance(output, list), "Native JSON is not an array.")
            normalized = normalize(output, root, batch, payloads, family)
            allowed = {rule["id"] for rule in batch_rules}
            s.require(all(row["rule"] in allowed for row in normalized), "A native rule ID is not registered.")
        except (KeyError, TypeError, UnicodeError, ValueError) as exc:
            raise RuntimeError("Invalid successful ast-grep output: " + str(exc)) from exc
        records.extend(normalized)
        matched = {row["path"] for row in normalized}
        for name in batch:
            statuses[name]["status"] = "scanned_matches" if name in inspected and name in matched else "scanned_no_match" if name in inspected else "scan_unconfirmed"
        if inspected != set(batch):
            errors.append(dict(batch=batch, kind="file_scan_unconfirmed", missing=sorted(set(batch) - inspected)))
    records.sort(key=lambda row: (row["path"], row["start"], -row["end"], row["rule"]))
    if family == "outline":
        parents(records)
    return dict(records=records, files=[statuses[name] for name in sorted(statuses)], errors=errors,
                status="partial" if errors else "ok", limit="Grammar validity and semantic name resolution are not established.")


def index(records, limit):
    lines = ["# Declaration index", "", "Complete declaration bytes are in declarations.json. Parent links are byte containment."]
    for row in records:
        lines.append(json.dumps(dict(path=row["path"], line=row["line"], end_line=row["end_line"], kind=row["kind"], id=row["id"]), ensure_ascii=True, sort_keys=True))
    if len(lines) > limit:
        lines = lines[:limit - 1] + ["[TRUNCATED: more declarations are in declarations.json]"]
    return "\n".join(lines) + "\n"
