# repo-review

`repo-review` helps you produce and maintain deep codebase reviews.

Use it when a normal code review is too narrow. It is built for questions like:

- What does this repo believe?
- Where does the author's taste show up in the code?
- Which claims are actually enforced?
- What changed since the last serious review?
- Which earlier review claims need another look?

The repo contains two things:

- A staged prompt sequence for full reviews.
- A small CLI for maintaining review state and running delta reviews later.

The CLI does not replace judgment. It helps preserve enough structure that a
future human or agent can resume the review without starting from scratch.

## Start Here

For a first review, read the prompts in order and give them to the analyzer one
at a time:

```bash
less 01-first-read.md
less 02-discounted-artifact.md
less 03-trace.md
```

Then optionally continue with:

```bash
less 04-twin.md
less 05-lift.md
```

For an agent or script, start by asking the repo what it supports:

```bash
./repo-review agent-context --json
./repo-review status --json
```

For an incremental review of a changed repo, generate a diff report, map it to
prior claims, and export a prompt packet:

```bash
./repo-review diff --repo /path/to/target --range HEAD~1..HEAD --json --no-input > diff-report.json

./repo-review impact \
  --review-state reviews/oathweaver/delta-2026-05-25/prior-review-state.json \
  --diff-report diff-report.json \
  --json --no-input > impact-plan.json

./repo-review export-prompt \
  --pass delta-trace \
  --review-state reviews/oathweaver/delta-2026-05-25/prior-review-state.json \
  --diff-report diff-report.json \
  --impact-plan impact-plan.json \
  --output delta-trace-prompt.md \
  --json --no-input
```

That packet is for an external analyzer. After the analyzer returns a delta
review artifact, record it:

```bash
./repo-review ingest --input delta-review.md --kind delta-review --json --no-input
```

## What You Get

A full review produces prose plus a structured appendix. The prose is for the
curator. The structured appendix gives later tools stable handles for pass
identity, findings, evidence, and follow-up work.

An incremental review works from these artifacts:

- `review-state.json`: durable claims, evidence refs, analyzer identity, watch
  paths, and invalidation triggers.
- `diff-report.json`: bounded summary of changed files.
- `impact-plan.json`: candidate claim impacts and unknowns.
- `delta-trace-prompt.md`: analyzer-ready prompt packet.
- `delta-review.md`: analyzer-written update.
- `delta-drift.json`: structured summary of strengthened, weakened, new, or
  invalidated review material.

Examples live under:

```bash
reviews/repo-review/calibration-2026-05-25
reviews/oathweaver/delta-2026-05-25
```

## The Full Review Passes

| Order | Prompt | Purpose |
| --- | --- | --- |
| 01 | `01-first-read.md` | Capture the first serious read, including blind spots. |
| 02 | `02-discounted-artifact.md` | Re-read the artifact the first pass underweighted. |
| 03 | `03-trace.md` | Trace a central obligation from claim to enforcement. |
| 04 | `04-twin.md` | Compare the repo to an adjacent repo with a different model. |
| 05 | `05-lift.md` | Identify what can survive outside the repo. |

Do not show later prompts early. The sequence is part of the method: later
passes are designed to reveal what earlier passes missed.

## The CLI In One Page

Discovery and setup:

```bash
./repo-review agent-context --json
./repo-review skill-path --json
./repo-review status --json
./repo-review profile list --json --no-input
```

Delta review:

```bash
./repo-review diff --range <from>..<to> --json --no-input
./repo-review impact --review-state <path> --diff-report <path> --json --no-input
./repo-review export-prompt --pass delta-trace --review-state <path> --diff-report <path> --impact-plan <path> --output <path> --json --no-input
./repo-review ingest --input <path> --kind delta-review --json --no-input
```

Claims, drift, and aggregation:

```bash
./repo-review claims list --review-state <path> --json --no-input
./repo-review claims get <id> --review-state <path> --json --no-input
./repo-review claims affected --impact-plan <path> --json --no-input
./repo-review drift surface --review-state <path> --diff-report <path> --impact-plan <path> --json --no-input
./repo-review aggregate --review-state <path> --review-state <path> --json --no-input
```

All shipped commands require `--json`. Mutating commands should use
`--no-input` in automated contexts. Stdout is result data; stderr is reserved
for JSON diagnostics.

## Common Tasks

Validate pass prompt metadata:

```bash
python3 tools/lint_pass_frontmatter.py
```

Validate a first-read output appendix:

```bash
python3 tools/validate_pass_output.py path/to/first-read.md --pass-id first-read
```

Return a prompt packet in JSON instead of writing a file:

```bash
./repo-review export-prompt \
  --pass delta-trace \
  --review-state <path> \
  --diff-report <path> \
  --impact-plan <path> \
  --deliver=stdout \
  --json --no-input
```

Use helper templates for recurring review decisions:

```bash
ls templates
```

## What Exists Today

- Five staged review prompts.
- Frontmatter linting for pass prompts.
- First-read output appendix validation.
- Initial schemas for pass output, claims, review state, diff reports, impact
  plans, and delta drift.
- CLI commands for discovery, profiles, status, feedback, diffing, impact
  planning, prompt export, ingestion, claims, drift, aggregation, and next-step
  guidance.
- Calibration artifacts for repo-review itself.
- A worked Oathweaver delta slice.
- Helper templates for affected claims, invalidation triggers, drift summaries,
  contested claims, twin selection, trace obligation choice, and lift seed
  evaluation.
- Evidence-scoped extractable pattern notes in
  `docs/extractable-patterns.md`.

## What It Does Not Do

- It does not run a full review automatically.
- It does not decide whether claims are true without an analyzer.
- It is not a security audit, style linter, or generic code-review tool.
- It does not execute long-running analysis jobs in v1.
- It does not deliver artifacts to webhooks in v1.
- It does not define global claim identity across repos.

## Self-Review

Changes to repo-review prompts, schemas, validators, CLI behavior, or
agent-facing workflow docs should usually get a repo-review delta review against
the latest `reviews/repo-review/` state.

Routine self-review asks whether a framework change affects existing claims.
Calibration is different: use calibration when testing the method or substrate
itself.

Details are in `docs/incremental-review.md`.

## Repo Layout

```text
repo-review/
├── 01-first-read.md
├── 02-discounted-artifact.md
├── 03-trace.md
├── 04-twin.md
├── 05-lift.md
├── agent/
│   └── repo-review-task-manifest.md
├── docs/
│   ├── extractable-patterns.md
│   └── incremental-review.md
├── repo-review
├── reviews/
├── schemas/
├── templates/
├── tests/
└── tools/
```

## Verification

Run the CLI contract tests:

```bash
python3 -m unittest tests.test_agent_native_cli
```

Run the lightweight docs/artifact checks:

```bash
python3 tools/lint_pass_frontmatter.py
python3 tools/validate_pass_output.py tests/fixtures/pass-output/first-read-valid.md --pass-id first-read
```
