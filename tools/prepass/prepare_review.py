#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["tiktoken==0.12.0"]
# ///
"""Prepare source evidence and current-pass instructions. Never start a model."""
import sys

sys.dont_write_bytecode = True

if __name__ == "__main__":
    from prepass_runtime import records as r
    from prepared_review.cli import main

    r.install_interrupt_handler()
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Prepared Review stopped.", file=sys.stderr)
        raise SystemExit(130)
    except (r.PrepassError, OSError, ValueError, KeyError) as exc:
        print("Prepared Review stopped: " + str(exc), file=sys.stderr)
        raise SystemExit(1)
