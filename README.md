# repo-review

`repo-review` is a staged review framework for producing deep, taste-oriented
analyses of codebases, plus a small agent-native CLI for maintaining those
reviews over time.

It is not a code review bot, vulnerability scanner, or automatic judgment
engine. The prompts do the interpretive work; the CLI preserves enough
structure that later review passes and delta reviews can be routed, compared,
and resumed without rereading everything from scratch.

## What Is Implemented

- Five staged review prompts: `01-first-read.md`, `02-discounted-artifact.md`,
  `03-trace.md`, `04-twin.md`, and `05-lift.md`.
- YAML frontmatter and structured `pass_output:` appendices for pass outputs.
- Validators for pass frontmatter and first-read pass output.
- Incremental review documentation in `docs/incremental-review.md`.
- Validated reusable pattern notes in `docs/extractable-patterns.md`.
- JSON schemas for claims, review state, diff reports, impact plans, delta
  drift, and pass output.
- A repo-local `repo-review` CLI that exposes machine-readable discovery,
  profile/status helpers, bounded git diff reporting, impact planning, delta
  prompt packet export, claims queries, drift surfacing, artifact ingestion,
  and feedback capture.
- Calibration and delta review artifacts under `reviews/`.
- Helper templates for recurring review decisions under `templates/`.

The agent-facing command registry is discoverable at runtime:

```bash
./repo-review agent-context --json
```

## Review Modes

### Full Review

A full review runs the prompt sequence against a repo state. Present the prompts
to the analyzer one at a time. Later prompts intentionally depend on earlier
blind spots, so showing the whole sequence up front contaminates the result.

1. Run `01-first-read.md`.
2. Run `02-discounted-artifact.md` against the first-read output.
3. Run `03-trace.md`; it may terminate early if the repo has no load-bearing
   obligation.
4. Optionally run `04-twin.md` with a selected adjacent repo.
5. Optionally run `05-lift.md`; it may terminate early if nothing extractable
   survives outside the repo.

Each pass produces prose for a human reader and a structured YAML appendix for
tooling.

### Delta Review

A delta review starts from a prior `review-state.json`, a bounded git diff, and
an impact plan. It does not rerun the whole review. It asks what changed, which
prior claims are affected, and whether the change creates subject drift,
analysis drift, or both.

The implemented v1 CLI assembles prompt packets and structured context. It does
not execute long-running analysis itself, and it does not ship a job queue.
Agents should export a prompt packet, run the analyzer externally, then ingest
the returned artifact.

### Self-Review

Changes to `repo-review` prompts, schemas, validators, CLI behavior, or
agent-facing workflow docs should usually receive a repo-review delta review
against the latest `reviews/repo-review/` state. Routine self-review produces
the same maintenance artifacts as other delta reviews: diff report, impact
plan, prompt packet, analyzer delta review, optional delta drift output, and an
updated review state when durable claims change.

Calibration is separate. Use calibration when testing the method or substrate
itself; use routine self-review when checking whether a framework change
affects existing claims.

## Minimal Human Workflow

Run the prompts manually when starting a new review:

```bash
less 01-first-read.md
less 02-discounted-artifact.md
less 03-trace.md
```

Validate structured pass output when an artifact includes a `pass_output:`
appendix:

```bash
python3 tools/validate_pass_output.py path/to/first-read.md --pass-id first-read
```

Inspect existing examples:

```bash
ls reviews/repo-review/calibration-2026-05-25
ls reviews/oathweaver/delta-2026-05-25
```

## Minimal Agent Workflow

Start with runtime discovery rather than hard-coding command assumptions:

```bash
./repo-review agent-context --json
./repo-review skill-path --json
./repo-review status --json
```

For a delta review, generate a diff report, map it to prior claims, and export a
delta trace prompt packet:

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

Query claims directly when deciding what a change touches:

```bash
./repo-review claims list \
  --review-state reviews/oathweaver/delta-2026-05-25/prior-review-state.json \
  --json --no-input

./repo-review claims affected \
  --impact-plan impact-plan.json \
  --json --no-input
```

Record an analyzer-produced delta review artifact after the external analysis
returns:

```bash
./repo-review ingest --input delta-review.md --kind delta-review --json --no-input
```

## CLI Surface

Implemented commands:

- `agent-context --json`: returns command registry, flags, enums, delivery
  schemes, async strategy, manifest path, and vocabulary policy.
- `skill-path --json`: returns the agent manifest directory.
- `status --json`: reports configured paths, profiles, and next review action.
- `profile list|show|save|delete --json`: manages local profiles.
- `feedback "..." --json --no-input`: appends local workflow feedback.
- `diff --range <from>..<to> --json --no-input`: emits a bounded structured
  git diff report.
- `impact --review-state <path> --diff-report <path> --json --no-input`: maps
  changed paths to claims and uncertainty buckets.
- `export-prompt --pass delta-trace ... --json --no-input`: writes or returns a
  delta trace prompt packet.
- `drift surface ... --json --no-input`: emits structured delta Drift Surfacer
  material.
- `next --json --no-input`: reports the next actionable workflow step.
- `ingest --input <path> --kind delta-review --json --no-input`: validates and
  records an external analyzer artifact.
- `delta --json --no-input`: reports v1 orchestration metadata.
- `aggregate --review-state <path> --review-state <path> --json --no-input`:
  summarizes multiple review states and optional drift outputs without merging
  claim identity.
- `claims list|get|affected --json --no-input`: queries review-state claims.

All shipped commands require `--json`. Automated contexts should also use
`--no-input` on mutating commands. Stdout is result data; stderr is reserved for
JSON diagnostics.

## Artifacts

Primary artifacts:

- Pass prompts: `01-first-read.md` through `05-lift.md`.
- Review outputs: human prose plus structured `pass_output:` YAML appendices.
- Review state: claim/evidence graphs with analyzer identity.
- Diff reports: bounded JSON summaries of changed files and classifications.
- Impact plans: path hits, trigger hits, impacted claims, unaffected claims, and
  unknowns.
- Delta trace prompt packets: analyzer-ready prompt context for delta review.
- Delta review artifacts: analyzer-written updates to prior claims.
- Delta drift reports: structured Drift Surfacer output for changed review
  material.
- Ingest ledger: local JSONL records under `.repo-review/`.
- Helper templates: reusable checklists for affected claims, invalidation
  triggers, drift summaries, contested claims, twin selection, trace obligation
  choice, and lift seed evaluation.

Artifact delivery starts local. `export-prompt` supports normal file output,
`--deliver=stdout`, and `--deliver=file:<path>`. Existing files require
`--overwrite`. Webhook delivery is explicitly deferred in v1.

## Non-Goals

- No automatic full-review execution.
- No claim truth adjudication without analyzer judgment.
- No security-audit, style-lint, or generic code-review guarantee.
- No long-running analysis job queue in v1.
- No webhook artifact delivery in v1.
- No cross-repo global claim identity model.

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

Run pass-output validation fixtures:

```bash
python3 tools/lint_pass_frontmatter.py
python3 tools/validate_pass_output.py tests/fixtures/pass-output/first-read-valid.md --pass-id first-read
```
