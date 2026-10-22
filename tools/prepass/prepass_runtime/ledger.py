"""Evaluate recorded delivery evidence. This does not prove human reading."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import PurePosixPath

METHODS = {"read", "read-range", "skimmed", "grep-hit", "git-show"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def lines(data):
    parts = data.split(b"\n")
    return [part + b"\n" for part in parts[:-1]] + ([parts[-1]] if parts[-1] else [])


def path_name(value):
    if not isinstance(value, str) or not value or "\0" in value:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and str(path) == value and not {"..", ".git"} & set(path.parts)


def spans(value, count):
    if not isinstance(value, list):
        return False
    previous = 0
    for pair in value:
        if not isinstance(pair, list) or len(pair) != 2 or any(type(n) is not int for n in pair):
            return False
        start, end = pair
        if not 1 <= start <= end <= count or start <= previous:
            return False
        previous = end
    return True


def merge(ranges):
    result = []
    for start, end in sorted(ranges):
        if result and start <= result[-1][1] + 1:
            result[-1][1] = max(end, result[-1][1])
        else:
            result.append([start, end])
    return result


def gaps(required, covered):
    missing = []
    for start, end in required:
        cursor = start
        for left, right in covered:
            if right < cursor:
                continue
            if left > end:
                break
            if left > cursor:
                missing.append([cursor, min(end, left - 1)])
            cursor = max(cursor, right + 1)
        if cursor <= end:
            missing.append([cursor, end])
    return missing


def load_events(data, format):
    events, errors = [], []
    for number, raw in enumerate(data.split(b"\n"), 1):
        if not raw.strip() or (format == "legacy" and raw.startswith(b"#")):
            continue
        if format == "legacy":
            fields = raw.decode("utf-8", "surrogateescape").split("\t")
            events.append(dict(id=f"legacy-{number}", path=fields[0], legacy=True))
            continue
        try:
            event = json.loads(raw)
            if not isinstance(event, dict):
                raise ValueError("An event must be an object.")
            events.append(event)
        except (ValueError, UnicodeError):
            errors.append(dict(row=number, code="invalid_json"))
    return events, errors


def evaluate(manifest, event_bytes, format, requests, source_reader, receipt_reader):
    """Readers return saved bytes. Evaluation does not alter source or ledger."""
    if format not in ("jsonl", "legacy") or manifest.get("version") != 1:
        raise ValueError("Unsupported ledger or inventory version.")
    inventory, payloads, faults = {}, {}, {}
    for row in manifest["files"]:
        name = row["path"]
        if not path_name(name) or name in inventory or type(row["lines"]) is not int or row["lines"] < 0:
            raise ValueError("Invalid inventory path or line count.")
        inventory[name] = row
        if row["kind"] != "text":
            faults[name] = "unavailable"
            continue
        try:
            data = source_reader(name)
        except OSError:
            faults[name] = "unavailable"
            continue
        if sha(data) != row["sha256"] or len(data) != row["bytes"] or len(lines(data)) != row["lines"]:
            faults[name] = "stale"
        else:
            payloads[name] = data
    events, errors = load_events(event_bytes, format)
    grouped = {}
    for number, event in enumerate(events, 1):
        identifier = event.get("id")
        if not isinstance(identifier, str) or not identifier:
            errors.append(dict(row=number, code="invalid_id"))
        else:
            grouped.setdefault(identifier, []).append(event)
    evidence = {name: dict(read=[], empty_read=False, methods=set(), stale=False, legacy=False) for name in inventory}
    outcomes = []
    for identifier, versions in sorted(grouped.items()):
        event = versions[0]
        name = event.get("path")
        error = None
        if any(value != event for value in versions[1:]):
            error = "conflicting_id"
        elif not path_name(name) or name not in inventory:
            error = "unknown_path"
        elif event.get("legacy"):
            evidence[name]["legacy"] = True
            error = "unverified_legacy"
        elif not isinstance(event.get("method"), str) or event["method"] not in METHODS:
            error = "unknown_method"
        elif not isinstance(event.get("pass_id"), str) or not event["pass_id"]:
            error = "invalid_pass"
        elif event.get("view") not in ("current", "history"):
            error = "invalid_view"
        elif name in faults:
            error = "source_" + faults[name]
        else:
            row = inventory[name]
            method, view = event["method"], event["view"]
            receipt = event.get("receipt")
            if not isinstance(receipt, dict) or not path_name(receipt.get("path")):
                error = "invalid_receipt"
            elif receipt.get("truncated") is not False or receipt.get("error") is not None:
                error = "delivery_failed"
            elif not isinstance(event.get("source_sha256"), str) or not re.fullmatch("[0-9a-f]{64}", event["source_sha256"]):
                error = "invalid_source_hash"
            elif view == "current" and method != "git-show" and event["source_sha256"] != row["sha256"]:
                evidence[name]["stale"] = True
                error = "stale_event"
            else:
                try:
                    delivered = receipt_reader(receipt["path"])
                    if type(receipt.get("bytes")) is not int or len(delivered) != receipt["bytes"] or sha(delivered) != receipt.get("sha256"):
                        error = "receipt_hash"
                    elif view == "history" or method == "git-show":
                        evidence[name]["methods"].add("history")
                    elif not spans(event.get("ranges"), row["lines"]):
                        error = "invalid_range"
                    elif method == "read" and event["ranges"] != ([[1, row["lines"]]] if row["lines"] else []):
                        error = "incomplete_read"
                    elif method != "read" and not event["ranges"]:
                        error = "invalid_range"
                    else:
                        source_lines = lines(payloads[name])
                        expected = b"".join(b"".join(source_lines[start - 1:end]) for start, end in event["ranges"])
                        if delivered != expected:
                            error = "receipt_source"
                        else:
                            evidence[name]["methods"].add(method)
                            if method in ("read", "read-range"):
                                evidence[name]["read"].extend(event["ranges"])
                                evidence[name]["empty_read"] |= method == "read" and not source_lines
                except OSError:
                    error = "receipt_unavailable"
        if error:
            errors.append(dict(id=identifier, path=name, code=error))
        outcomes.append(dict(id=identifier, path=name, status="rejected" if error else "accepted", code=error,
                             copies=len(versions)))
    records = []
    for name, row in sorted(inventory.items()):
        value = evidence[name]
        covered = merge(value["read"])
        required = [[1, row["lines"]]] if row["lines"] else []
        missing = gaps(required, covered)
        complete = name not in faults and (not missing if row["lines"] else value["empty_read"])
        methods = value["methods"]
        state = (faults[name] if name in faults else "complete" if complete else "partial" if covered else
                 "skimmed" if "skimmed" in methods else "hit" if "grep-hit" in methods else
                 "historical" if "history" in methods else "stale" if value["stale"] else
                 "unverified" if value["legacy"] else "unread")
        records.append(dict(path=name, sha256=row.get("sha256"), lines=row["lines"], state=state,
                            read_ranges=covered, missing_ranges=missing, methods=sorted(methods)))
    by_path = {row["path"]: row for row in records}
    closure = []
    for request in requests:
        row = by_path.get(request["path"])
        whole = request.get("whole") is True
        required = ([[1, row["lines"]]] if row["lines"] else []) if row and whole else request.get("ranges")
        if not row or not spans(required, row["lines"]):
            raise ValueError("Invalid closure request.")
        missing = gaps(required, row["read_ranges"])
        usable = row["state"] not in ("unavailable", "stale")
        covered = usable and (row["state"] == "complete" if whole and row["lines"] == 0 else bool(required) and not missing)
        closure.append(dict(id=request["id"], path=request["path"], reading_evidence="covered" if covered else "missing",
                            missing_ranges=missing, review_judgment="required"))
    ordered = sorted(records, key=lambda row: (-row["lines"], row["path"]))
    return dict(version=1, status="partial" if errors or faults else "ok", files=records, events=outcomes, errors=errors,
                unread=[row["path"] for row in ordered if row["state"] != "complete"],
                complete=[row["path"] for row in ordered if row["state"] == "complete"], closure=closure,
                limit="Delivery records do not prove attention, understanding, or a review finding.")
