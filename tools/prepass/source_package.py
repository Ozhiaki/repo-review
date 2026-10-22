#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["tiktoken==0.12.0"]
# ///
"""Prepare and use the common source evidence package."""
from __future__ import annotations

import argparse
import sys

sys.dont_write_bytecode = True
from prepass_runtime.cli import add_commands
from prepass_runtime.records import install_interrupt_handler


def main():
    parser = argparse.ArgumentParser(prog="prepass", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    add_commands(commands)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    install_interrupt_handler()
    main()
