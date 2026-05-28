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
future human, model, or agent can resume the review without starting from
scratch.

## Start Here

For a first review, read the prompts in order and give them to your reviewer
one at a time. The reviewer might be you, an LLM chat, or an agent acting under
your direction:

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

If you use an agent or script, it should start by asking the repo what helper
surface is available. This is not the review itself. It is capability discovery
for tooling that helps package, validate, and maintain the structured products
of a human-directed review:

```bash
./repo-review agent-context --json
./repo-review status --json
```

`agent-context` returns the machine-readable command registry: supported
commands, flags, enums, delivery modes, helper templates, async policy, and the
path to the agent task manifest. An agent should read this before assuming a
command exists.

`status` starts with operational workflow state: latest review state, open runs,
prompt-ready runs, candidate claims waiting to import, warnings, and next
action. It also returns repo root, review output directory, profile settings,
and other configuration details. A script should use it to discover local paths
and defaults instead of hard-coding them.

The intended flow is human-first: a person applies the staged review prompts,
keeps or edits the resulting prose, and decides what the repo means. The
structured appendices and review-state files from that manual review then feed
the CLI. The CLI helps with later maintenance: diff reports, impact plans,
prompt packets, claim lookup, drift summaries, aggregation, and ingest records.

If you have older prose reviews but no `review-state.json`, bootstrap a state
shell before running maintenance commands:

```bash
./repo-review state bootstrap \
  --repo /path/to/target-repo \
  --review-dir /path/to/old-review-files \
  --output /path/to/reviews/<repo>/full-<date>/review-state.json \
  --source-analyzer-id <original-reviewer-id> \
  --source-kind llm \
  --json --no-input
```

Bootstrap preserves discovered Markdown review artifacts and writes
`claims: []`. It does not invent durable claims from prose. After inspecting the
old review, use `templates/bootstrap-candidate-claims.md` to author a candidate
claims JSON file and import it:

```bash
./repo-review claims import \
  --review-state /path/to/review-state.json \
  --input /path/to/candidate-claims.json \
  --json --no-input
```

For an incremental review of a changed repo, prefer the workflow command first:

```bash
./repo-review review start \
  --mode delta \
  --repo /path/to/target \
  --range HEAD~1..HEAD \
  --review-state /path/to/review-state.json \
  --json --no-input
```

`review start --mode delta` creates or reuses a run, writes the diff report,
impact plan, and delta prompt packet, and normally leaves the run in
`prompt_ready`.

To inspect what should happen next without changing anything:

```bash
./repo-review review continue --latest --json --no-input
./repo-review review continue --latest
```

Send the prompt packet to an external reviewer or model. After it returns a
delta review artifact, attach or ingest it and finish when complete:

```bash
./repo-review review ingest --run <run-id> --input delta-review.md --attach-only --json --no-input
./repo-review review ingest --run <run-id> --input delta-review.md --json --no-input
./repo-review review finish --run <run-id> --json --no-input
```

Low-level primitives remain available when you need to inspect or rebuild one
artifact manually:

```bash
./repo-review diff --repo /path/to/target --range HEAD~1..HEAD --json --no-input > diff-report.json
./repo-review impact --review-state /path/to/review-state.json --diff-report diff-report.json --json --no-input > impact-plan.json
./repo-review export-prompt --pass delta-trace --review-state /path/to/review-state.json --diff-report diff-report.json --impact-plan impact-plan.json --output delta-trace-prompt.md --json --no-input
./repo-review ingest --input delta-review.md --kind delta-review --json --no-input
```

Human output is the default for workflow-friendly commands. Use `--json` when a
script or agent needs a stable contract:

```bash
./repo-review status
./repo-review review start --mode delta --repo /path/to/target --range HEAD~1..HEAD --review-state /path/to/review-state.json
./repo-review status --json
./repo-review review start --mode delta --repo /path/to/target --range HEAD~1..HEAD --review-state /path/to/review-state.json --json --no-input
```

Run statuses are durable and drive `review continue`:

```text
created -> diff_ready -> impact_ready -> prompt_ready -> review_received -> ingested -> drift_ready -> complete
```

Any command may record `blocked` when a human decision is required, or `failed`
when a durable failure/recovery hint needs to be reported. Long-running skill
execution and webhook delivery are intentionally deferred in this CLI slice:
the CLI packages artifacts and records state; reviewers/models still run
outside it.

## What You Get

A full review produces prose plus a structured appendix. The prose is for the
curator. The structured appendix gives later tools stable handles for pass
identity, findings, evidence, and follow-up work.

An incremental review works from these artifacts:

- `review-state.json`: durable claims, evidence refs, reviewer identity, watch
  paths, and invalidation triggers.
- `diff-report.json`: bounded summary of changed files.
- `impact-plan.json`: candidate claim impacts and unknowns.
- `delta-trace-prompt.md`: reviewer-ready prompt packet.
- `delta-review.md`: reviewer-written update.
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

<!-- repo-review-command-registry:start -->
| Command | Role | Mutation | Dry run | Output schema | Flags | Outcomes | Examples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `repo-review agent-context` | introspection | no | no | - | `--json` | - | `repo-review agent-context --json` |
| `repo-review aggregate` | primitive | no | no | - | `--drift`, `--json`, `--limit`, `--no-input`, `--review-state` | - | - |
| `repo-review claims` | primitive | yes | no | - | `--claim-status`, `--force`, `--impact-plan`, `--input`, `--json`, `--kind`, `--limit`, `--no-input`, `--overwrite-claims`, `--review-state`, `--subject` | `created`, `updated`, `existing`, `imported`, `replaced`, `unchanged`, `dry_run` | `repo-review claims list --review-state <path> --json --no-input` |
| `repo-review delta` | primitive | no | no | - | `--diff-report`, `--impact-plan`, `--json`, `--no-input`, `--output`, `--review-state`, `--wait` | - | - |
| `repo-review diff` | primitive | no | no | `schemas/diff_report.schema.json` | `--json`, `--limit`, `--no-input`, `--path`, `--range`, `--repo` | - | `repo-review diff --repo . --range HEAD~1..HEAD --json --no-input` |
| `repo-review drift` | primitive | no | no | `schemas/delta_drift.schema.json` | `--diff-report`, `--impact-plan`, `--json`, `--no-input`, `--review-state`, `--to-review` | - | - |
| `repo-review export-prompt` | primitive | yes | yes | - | `--deliver`, `--diff-report`, `--dry-run`, `--impact-plan`, `--json`, `--no-input`, `--output`, `--overwrite`, `--pass`, `--review-state` | `created`, `existing`, `updated`, `dry_run` | `repo-review export-prompt --pass delta-trace --review-state <path> --diff-report <path> --impact-plan <path> --output <path> --json --no-input` |
| `repo-review feedback` | primitive | yes | no | - | `--json`, `--limit`, `--no-input`, `--output`, `--overwrite` | `created`, `unchanged` | `repo-review feedback "message" --json --no-input` |
| `repo-review impact` | primitive | no | no | `schemas/impact_plan.schema.json` | `--diff-report`, `--json`, `--no-input`, `--review-state` | - | `repo-review impact --review-state <path> --diff-report <path> --json --no-input` |
| `repo-review ingest` | primitive | yes | no | - | `--input`, `--json`, `--kind`, `--no-input` | `created` | `repo-review ingest --input <path> --kind delta-review --json --no-input` |
| `repo-review next` | primitive | no | no | - | `--diff-report`, `--impact-plan`, `--json`, `--no-input`, `--output`, `--review-state` | - | - |
| `repo-review profile` | primitive | yes | no | - | `--force`, `--json`, `--no-input` | `created`, `updated`, `existing`, `unchanged` | - |
| `repo-review review` | workflow | yes | yes | `schemas/review_run.schema.json` | `--dry-run`, `--json`, `--mode`, `--new-run`, `--no-input`, `--output`, `--range`, `--repo`, `--review-state` | `created`, `existing`, `updated`, `dry_run` | `repo-review review start --mode delta --repo . --range HEAD~1..HEAD --review-state latest --json --no-input` |
| `repo-review review continue` | resume | yes | no | `schemas/review_run.schema.json` | `--apply`, `--json`, `--latest`, `--no-input`, `--run` | - | `repo-review review continue --latest --json --no-input` |
| `repo-review review finish` | finish | yes | yes | `schemas/review_run.schema.json` | `--dry-run`, `--json`, `--latest`, `--no-input`, `--run` | `updated`, `unchanged`, `dry_run` | - |
| `repo-review review ingest` | ingest | yes | yes | `schemas/review_run.schema.json` | `--attach-only`, `--dry-run`, `--input`, `--json`, `--kind`, `--latest`, `--no-input`, `--run` | `updated`, `dry_run` | - |
| `repo-review review package` | artifact | yes | yes | `schemas/review_run.schema.json` | `--deliver`, `--dry-run`, `--json`, `--latest`, `--no-input`, `--output`, `--overwrite`, `--run` | `created`, `existing`, `updated`, `dry_run` | - |
| `repo-review review start` | entrypoint | yes | yes | `schemas/review_run.schema.json` | `--dry-run`, `--json`, `--mode`, `--new-run`, `--no-input`, `--output`, `--range`, `--repo`, `--review-state` | `created`, `existing`, `updated`, `dry_run` | `repo-review review start --mode delta --repo . --range HEAD~1..HEAD --review-state latest --json --no-input` |
| `repo-review review status` | status | no | no | `schemas/review_run.schema.json` | `--json`, `--latest`, `--no-input`, `--run` | - | - |
| `repo-review runs` | runs | yes | yes | `schemas/review_run.schema.json` | `--dry-run`, `--force`, `--json`, `--limit`, `--no-input`, `--repo`, `--run` | `updated`, `unchanged`, `dry_run` | `repo-review runs list --repo . --json --no-input` |
| `repo-review runs get` | runs | no | no | `schemas/review_run.schema.json` | `--json`, `--no-input`, `--repo`, `--run` | - | - |
| `repo-review runs list` | runs | no | no | `schemas/review_run.schema.json` | `--json`, `--limit`, `--no-input`, `--repo` | - | - |
| `repo-review runs prune` | runs | yes | yes | `schemas/review_run.schema.json` | `--dry-run`, `--force`, `--json`, `--no-input`, `--repo` | `updated`, `unchanged`, `dry_run` | - |
| `repo-review skill-path` | introspection | no | no | - | `--json` | - | - |
| `repo-review state` | primitive | yes | yes | `schemas/review_state.schema.json` | `--created-at`, `--dry-run`, `--json`, `--no-input`, `--output`, `--overwrite`, `--repo`, `--review-dir`, `--review-state-id`, `--source-analyzer-id`, `--source-kind`, `--source-model`, `--source-notes`, `--source-prompt-set-version`, `--source-tool-context` | `created`, `existing`, `replaced`, `dry_run` | `repo-review state bootstrap --repo <path> --review-dir <path> --output <path> --json --no-input` |
| `repo-review state get` | state-discovery | no | no | - | `--json`, `--no-input`, `--review-state` | - | - |
| `repo-review state latest` | state-discovery | no | no | - | `--json`, `--mode`, `--no-input`, `--repo` | - | - |
| `repo-review state list` | state-discovery | no | no | - | `--json`, `--no-input`, `--repo` | - | - |
| `repo-review state validate` | state-discovery | no | no | - | `--json`, `--no-input`, `--review-state` | - | - |
| `repo-review status` | status | no | no | - | `--analyzer-id`, `--json`, `--lane-vocabulary`, `--output`, `--output-mode`, `--profile`, `--repo` | - | - |
| `repo-review templates` | templates | yes | no | - | `--json`, `--no-input`, `--output`, `--overwrite` | `created`, `unchanged` | `repo-review templates list --json --no-input` |
<!-- repo-review-command-registry:end -->

Discovery and setup:

```bash
./repo-review agent-context --json
./repo-review skill-path --json
./repo-review status --json
./repo-review profile list --json --no-input
./repo-review state bootstrap --repo <path> --review-dir <path> --output <path> --json --no-input
./repo-review state list --repo <path> --json --no-input
./repo-review state latest --repo <path> --json --no-input
./repo-review state get --review-state <id-or-path> --json --no-input
./repo-review state validate --review-state <path> --json --no-input
```

Delta review:

```bash
./repo-review review start --mode delta --repo <path> --range <from>..<to> --review-state <id-or-path> --json --no-input
./repo-review review package --run <id> --json --no-input
./repo-review review continue --run <id> --json --no-input
./repo-review review ingest --run <id> --input <review.md> --json --no-input
./repo-review review finish --run <id> --json --no-input
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
./repo-review claims import --review-state <path> --input <candidate-claims.json> --json --no-input
./repo-review drift surface --review-state <path> --diff-report <path> --impact-plan <path> --json --no-input
./repo-review aggregate --review-state <path> --review-state <path> --json --no-input
./repo-review runs list --repo <path> --json --no-input
./repo-review runs get <id> --repo <path> --json --no-input
./repo-review runs prune --repo <path> --dry-run --json --no-input
./repo-review templates list --json --no-input
./repo-review templates get <id> --json --no-input
./repo-review templates write <id> --output <path> --json --no-input
```

Use `--json` for stable machine output. Mutating commands should use
`--no-input` in automated contexts. In JSON mode, stdout is result data and
stderr is reserved for JSON diagnostics.

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

Migrate older prose reviews:

```bash
./repo-review state bootstrap \
  --repo /path/to/repo \
  --review-dir /path/to/legacy-review \
  --output reviews/<repo>/full-<date>/review-state.json \
  --dry-run \
  --json --no-input
```

Remove `--dry-run` to write `review-state.json` and
`review-state.bootstrap.json`. Then draft candidate claims with
`templates/bootstrap-candidate-claims.md` and run `claims import`. Duplicate
claim IDs are refused by default; use `--overwrite-claims` only when replacing
matching durable claims intentionally.

## What Exists Today

- Five staged review prompts.
- Frontmatter linting for pass prompts.
- First-read output appendix validation.
- Initial schemas for pass output, claims, review state, diff reports, impact
  plans, and delta drift.
- CLI commands for discovery, profiles, workflow-aware status, feedback,
  diffing, impact planning, prompt export, ingestion, claims, state bootstrap
  and discovery, run ledgers, delta review start/package/continue/ingest/finish,
  drift, aggregation, and next-step guidance.
- Calibration artifacts for repo-review itself.
- A worked Oathweaver delta slice.
- Helper templates for affected claims, invalidation triggers, drift summaries,
  contested claims, twin selection, trace obligation choice, and lift seed
  evaluation.
- Evidence-scoped extractable pattern notes in
  `docs/extractable-patterns.md`.

## What It Does Not Do

- It does not run a full review automatically.
- It does not decide whether claims are true without reviewer judgment.
- It does not silently convert old prose into durable claims during bootstrap.
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
