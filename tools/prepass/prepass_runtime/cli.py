"""Candidate commands added during the five integration steps."""
from __future__ import annotations

import argparse
import math
import sys

from . import delivery, package, pipeline, records, search


def positive_seconds(value):
    try:
        number = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Use a positive time in seconds.") from exc
    if not math.isfinite(number) or not 0 < number < 86400:
        raise argparse.ArgumentTypeError("Use a positive time below 86,400 seconds.")
    return number


def integer(minimum, maximum):
    def convert(value):
        try:
            number = int(value)
        except ValueError as exc:
            raise argparse.ArgumentTypeError("Use an integer.") from exc
        if not minimum <= number <= maximum:
            raise argparse.ArgumentTypeError(f"Use an integer from {minimum} to {maximum}.")
        return number
    return convert


def add_commands(subparsers):
    prepare = subparsers.add_parser("prepare", help="create the candidate shared source package")
    prepare.add_argument("repo")
    prepare.add_argument("out")
    prepare.add_argument("--git", default="git", help="installed Git binary")
    prepare.set_defaults(func=dispatch, candidate_action=package.prepare)
    check = subparsers.add_parser("check", help="check candidate source and package freshness")
    check.add_argument("out")
    check.set_defaults(func=dispatch, candidate_action=package.check)
    run = subparsers.add_parser("run", help="prepare the integrated prepass package")
    run.add_argument("repo")
    run.add_argument("out")
    run.add_argument("--git", default="git")
    run.add_argument("--tools", required=True, help="explicit hash-checked tools.json bundle")
    run.add_argument("--python-root", action="append")
    run.add_argument("--tsconfig")
    run.add_argument("--facts-tokens", type=integer(512, 100000), default=8000)
    run.set_defaults(func=dispatch, candidate_action=pipeline.run)
    query = subparsers.add_parser("query", help="retrieve source with the tested Colgrep and Zoekt merge")
    query.add_argument("out")
    query.add_argument("question")
    query.add_argument("--term", action="append", required=True)
    query.set_defaults(func=dispatch, candidate_action=search.query)
    read = subparsers.add_parser("read", help="produce a pending source delivery without reading credit")
    read.add_argument("out")
    read.add_argument("path")
    read.add_argument("--pass-id", required=True)
    read.add_argument("--start", type=integer(1, 100000000))
    read.add_argument("--end", type=integer(1, 100000000))
    read.add_argument("--method", choices=("read", "read-range", "skimmed", "grep-hit"))
    read.add_argument("--max-bytes", type=integer(1, 32 * 1024 * 1024), default=32768)
    read.set_defaults(func=dispatch, candidate_action=delivery.read)
    confirm = subparsers.add_parser("confirm", help="record the caller's captured source response")
    confirm.add_argument("out")
    confirm.add_argument("event")
    confirm.add_argument("--receipt", required=True)
    confirm.add_argument("--complete", action="store_true", help="the caller confirms an untruncated successful response")
    confirm.set_defaults(func=dispatch, candidate_action=delivery.confirm)
    unread = subparsers.add_parser("unread", help="list paths without complete current reading evidence")
    unread.add_argument("out")
    unread.add_argument("--legacy", help="evaluate an old ledger as unverified input")
    unread.add_argument("--offset", type=integer(0, 100000000), default=0)
    unread.add_argument("--max-paths", type=integer(1, 100), default=50)
    unread.set_defaults(func=dispatch, candidate_action=delivery.unread)
    closure = subparsers.add_parser("closure", help="check selected reading evidence without a review judgment")
    closure.add_argument("out")
    closure.add_argument("path")
    closure.add_argument("--whole", action="store_true")
    closure.add_argument("--start", type=integer(1, 100000000))
    closure.add_argument("--end", type=integer(1, 100000000))
    closure.set_defaults(func=dispatch, candidate_action=delivery.closure)
    for parser in (prepare, check, run, query, read, confirm, unread, closure):
        parser.add_argument("--total-timeout", type=positive_seconds, default=1200)
        parser.add_argument("--command-timeout", type=positive_seconds, default=60)


def dispatch(args):
    try:
        code = args.candidate_action(args)
    except KeyboardInterrupt:
        print("Prepass stopped. The active child process group was stopped.", file=sys.stderr)
        code = 130
    except (records.PrepassError, OSError, ValueError, KeyError) as exc:
        print("Prepass failed: " + str(exc), file=sys.stderr)
        code = 1
    raise SystemExit(code)
