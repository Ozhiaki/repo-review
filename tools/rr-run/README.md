# rr-run

`rr-run.sh` runs passes 01 to 05 on one target repo, in one Claude session, one pass at a time. It uses [gashki](https://github.com/Ozhiaki/gashki) to start the agent in a tmux pane, send each pass prompt and wait for the turn to end. After the last pass, the pane stays open. The human then talks with the same agent.

## Run

From a pane inside tmux:

```bash
tools/rr-run/rr-run.sh ~/p/farm/<name>/<name>
```

The repo must sit in a folder of the same name. The pass outputs go to that parent folder, with `rr-run.log`.

## What it needs

- gashki with JSON contract 2 on `PATH`, or in `GASHKI`. The script checks `gashki --version`.
- tmux, jq, python3 (for `tools/lint_pass_outputs.py`), Claude Code.

## What it does

- Spawns `rr-<name>/analyst` beside the current pane: Sonnet (`RR_MODEL`), bypassPermissions, 1M context, folder trust answered.
- For each pass: fills `{REPO}`, `{ART}`, `{SCRATCH}` and `{RR}` in `prompts/<pass>.txt`, sends it, and waits from the send's `turn_cursor`. Only a Stop hook ends the wait.
- On an approval prompt: rings the bell and waits for the human.
- After each pass: moves stray `.md` files from the repo to the parent, lints the new outputs and logs lint, approvals and compactions.
- After pass 05: deletes `.rr-scratch` (pass 04's clones). A stopped run keeps it.

## Known limits

- The pass 05 source_notes rule does not always hold: lint failed on television and frizbee.
- `SPEC.md` is the first design draft. The script has changed since; this README is current.
