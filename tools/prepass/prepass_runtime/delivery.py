"""Record delivery at the caller's capture boundary. Producing bytes gives no credit."""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import uuid

from . import ledger, package, records as r, scope, tokens


def fresh(args):
    r.require(package.check(args) == 0, "The source package is stale or unverifiable.")
    output = Path(args.out).expanduser().resolve()
    return output, output / "evidence"


def read(args):
    output, evidence = fresh(args)
    name = str(scope.checked_name(args.path))
    r.require(bool(args.pass_id.strip()), "Supply a nonempty pass ID.")
    manifest = r.read(evidence / "inventory.json")
    row = next((row for row in manifest["records"] if row["path"] == name), None)
    r.require(row is not None and row["status"] == "file" and not row.get("binary") and not row.get("lfs"),
              "The selected path has no available source text.")
    data, _ = scope.read_regular(evidence / "source", name)
    r.require(hashlib.sha256(data).hexdigest() == row["sha256"], "The source hash differs.")
    data.decode("utf-8")
    lines = ledger.lines(data)
    if args.start is None and args.end is None:
        ranges = [[1, len(lines)]] if lines else []
        method = args.method or "read"
    else:
        ranges = [[args.start, args.end]]
        r.require(ledger.spans(ranges, len(lines)), "The requested range is invalid.")
        method = args.method or "read-range"
    r.require(method != "read" or ranges == ([[1, len(lines)]] if lines else []), "A full read requires the complete file range.")
    r.require(method == "read" or ranges, "A nonempty range is required for this reading method.")
    payload = b"".join(b"".join(lines[start - 1:end]) for start, end in ranges)
    truncated = len(payload) > args.max_bytes
    payload = payload[:args.max_bytes]
    identifier = uuid.uuid4().hex
    home = output / "state/pending"
    r.output_directory(home)
    request = dict(id=identifier, path=name, pass_id=args.pass_id, method=method, view="current", ranges=ranges,
                   source_sha256=row["sha256"], produced_bytes=len(payload), produced_sha256=ledger.sha(payload),
                   truncated=truncated, status="pending")
    r.save(home / (identifier + ".json"), request)
    r.say("Delivery ID: " + identifier + (". Output is truncated." if truncated else ". Confirm the captured response before reading credit."))
    try:
        sys.stdout.buffer.write(payload)
        sys.stdout.buffer.flush()
    except (BrokenPipeError, OSError):
        request.update(status="delivery_failed", truncated=True)
        r.save(home / (identifier + ".json"), request)
        raise
    return 0


def confirm(args):
    output, evidence = fresh(args)
    r.require(re.fullmatch(r"[0-9a-f]{32}", args.event), "The delivery ID is invalid.")
    request = r.read(output / "state/pending" / (args.event + ".json"))
    r.require(request["id"] == args.event, "The pending delivery ID differs.")
    capture = Path(args.receipt).expanduser().resolve()
    r.require(not capture.is_relative_to(evidence) and not capture.is_relative_to(output / "state/pending"),
              "Supply the caller's captured response, separate from source and pending records.")
    received, _ = scope.read_regular(capture.parent, capture.name)
    complete = args.complete and not request["truncated"] and request["status"] == "pending"
    complete &= len(received) == request["produced_bytes"] and ledger.sha(received) == request["produced_sha256"]
    receipt_home = output / "state/receipts"
    r.output_directory(receipt_home)
    receipt_path = receipt_home / (args.event + ".bin")
    r.require(not receipt_path.is_symlink(), "A receipt output is a symbolic link.")
    if receipt_path.exists():
        r.require(scope.read_regular(receipt_home, receipt_path.name)[0] == received, "A conflicting confirmation exists for this delivery ID.")
    else:
        with os.fdopen(os.open(receipt_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600), "wb") as stream:
            stream.write(received)
    event = {key: request[key] for key in ("id", "path", "pass_id", "method", "view", "ranges", "source_sha256")}
    event["receipt"] = dict(path="receipts/" + receipt_path.name, bytes=len(received), sha256=ledger.sha(received),
                            truncated=not complete, error=None if complete else "incomplete_capture")
    ledger_path = output / "state/ledger.jsonl"
    with os.fdopen(os.open(ledger_path, os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600), "a+b") as stream:
        r.require(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), "The ledger is not a regular file.")
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        stream.seek(0)
        previous, _ = ledger.load_events(stream.read(), "jsonl")
        versions = [value for value in previous if value.get("id") == event["id"]]
        r.require(not versions or all(value == event for value in versions), "A conflicting ledger event exists.")
        if not versions:
            stream.seek(0, 2)
            stream.write((json.dumps(event, ensure_ascii=True, sort_keys=True) + "\n").encode())
            stream.flush()
    print(json.dumps(dict(id=args.event, confirmed=bool(complete), reading_credit="evaluate_ranges" if complete else "none")))
    return 0 if complete else 1


def evaluate(output, evidence, requests=(), legacy=None):
    manifest = r.read(evidence / "inventory.json")
    counters = {row["path"]: row for row in r.read(evidence / "counter.json")}
    files = []
    for row in manifest["records"]:
        if not row["selected"]:
            continue
        text = row["status"] == "file" and not row.get("binary") and not row.get("lfs")
        files.append(dict(path=row["path"], kind="text" if text else "unavailable", sha256=row.get("sha256"),
                          bytes=row.get("bytes"), lines=counters[row["path"]]["lines"] or 0))
    ledger_path = Path(legacy) if legacy else output / "state/ledger.jsonl"
    events = ledger_path.read_bytes() if ledger_path.exists() else b""
    source_reader = lambda name: scope.read_regular(evidence / "source", name)[0]
    receipt_reader = lambda name: scope.read_regular(output / "state", name)[0]
    return ledger.evaluate(dict(version=1, files=files), events, "legacy" if legacy else "jsonl", list(requests), source_reader, receipt_reader)


def unread(args):
    output, evidence = fresh(args)
    result = evaluate(output, evidence, legacy=args.legacy)
    r.save(output / "state/unread.json", result)
    paths = result["unread"][args.offset:args.offset + args.max_paths]
    page = dict(total_unread=len(result["unread"]), total_complete=len(result["complete"]),
                errors=len(result["errors"]), offset=args.offset, paths=paths, record="state/unread.json")
    while paths and tokens.tokens(json.dumps(page, ensure_ascii=True)) > 3900:
        paths.pop()
    page["next_offset"] = args.offset + len(paths) if args.offset + len(paths) < len(result["unread"]) else None
    r.require(tokens.tokens(json.dumps(page, ensure_ascii=True)) <= 4000, "The unread page exceeds the response limit.")
    print(json.dumps(page, ensure_ascii=True))
    return 0


def closure(args):
    output, evidence = fresh(args)
    request = dict(id="selected", path=str(scope.checked_name(args.path)), whole=args.whole)
    if not args.whole:
        request["ranges"] = [[args.start, args.end]]
    result = evaluate(output, evidence, [request])
    response = result["closure"][0]
    r.save(output / "state/closure.json", response)
    print(json.dumps(response, ensure_ascii=True))
    return 0 if response["reading_evidence"] == "covered" else 1
