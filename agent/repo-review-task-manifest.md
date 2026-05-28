# repo-review Agent Task Manifest

This manifest is the first agent-readable workflow surface for repo-review. It is intentionally small while the incremental review substrate is still being validated.

## Commands

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

### `repo-review agent-context --json`

Returns the shipped command registry, supported flags, enum values, delivery schemes, helper template paths, available profiles, manifest path, and vocabulary policy.

### `repo-review skill-path --json`

Returns the local directory containing this manifest.

### `repo-review status --json`

Returns workflow state first: latest review state, open runs, prompt-ready runs,
candidate claims waiting to import, warnings, and next action. It also preserves
configured paths and available profiles. Configuration precedence is explicit
flag, then environment variable, then selected profile, then default.

### `repo-review profile list|show|save|delete --json`

Manages local profiles stored under `.repo-review/profiles.json`. Mutating profile commands are non-interactive and support `--no-input`; deletion requires `--force`.

### `repo-review feedback "..." --json`

Appends a local feedback entry to `.repo-review/feedback.jsonl` and returns the stored entry id and path.

### `repo-review diff --range <from>..<to> --json --no-input`

Returns a bounded structured git diff report with changed files, summary stats, classification candidates, and truncation metadata. Use `--repo <path>` for a target checkout, `--path <path>` to narrow, and `--limit <n>` to control output size.

### `repo-review impact --review-state <path> --diff-report <path> --json --no-input`

Maps changed files from a diff report to claim `watch_paths` from a review state. Output keeps `path_hits`, `trigger_hits`, `impacted_claims`, `unaffected_claims`, and `unknowns` separate.

### `repo-review export-prompt --pass delta-trace --review-state <path> --diff-report <path> --impact-plan <path> --output <path> --json --no-input`

Writes a delta trace prompt packet. Existing output files require `--overwrite`; `--dry-run` reports the intended output and required inputs without writing. `--deliver=stdout` returns the artifact inside the JSON response, and `--deliver=file:<path>` is equivalent to `--output <path>`. JSON responses include `delivery_metadata` with the selected scheme and local path when applicable.

Webhook delivery is deferred in v1.

### `repo-review drift surface --review-state <path> --diff-report <path> --impact-plan <path> --json --no-input`

Generates a `delta_drift` JSON object tied to the prior review state and diff range. The output can carry new, invalidated, strengthened, and weakened Drift Surfacer material.

### `repo-review next --json --no-input`

Returns the next actionable workflow step, required inputs, missing inputs, intended output path, and a recommended command.

### `repo-review ingest --input <path> --kind delta-review --json --no-input`

Validates and records an external analyzer artifact in the local ingest ledger.

### `repo-review delta --json --no-input`

Reports the selected v1 orchestration model. V1 assembles prompt packets and does not execute analysis, so jobs and `--wait` are deferred.

### `repo-review aggregate --review-state <path> --review-state <path> --json --no-input`

Summarizes multiple review states and optional `--drift <path>` outputs. Aggregation reports claim status counts, analyzer identities, and drift material without merging local claim IDs across review states.

### `repo-review state bootstrap --repo <path> --review-dir <path> --output <path> --json --no-input`

Creates a schema-valid review-state shell from older Markdown review prose. It
discovers review artifacts, preserves files with and without `pass_output:`
appendices, records repo metadata and original source identity, writes
`claims: []`, and creates `review-state.bootstrap.json` next to the generated
state. Use `--dry-run` to preview discovery and warnings without writing, and
`--overwrite` to replace an existing state or sidecar.

Bootstrap is mechanical migration only. It must not promote inferred prose
claims into durable state.

### `repo-review state list --json --no-input`
### `repo-review state latest --json --no-input`
### `repo-review state get --json --no-input`
### `repo-review state validate --json --no-input`

Discovers review-state artifacts for a repo, resolves the latest state, returns
one state by ID or path, and reports schema validity plus readiness warnings.
`state latest` refuses ambiguous latest candidates and asks callers to resolve
with `state list` and `state get`.

### `repo-review runs list --json --no-input`
### `repo-review runs get --json --no-input`
### `repo-review runs prune --json --no-input`

Lists and inspects persisted review runs in `.repo-review/runs.jsonl`.
`runs prune --dry-run` reports completed-run ledger compaction candidates;
non-dry-run pruning requires `--force` and keeps the latest record for every run.

### `repo-review templates list --json --no-input`
### `repo-review templates get --json --no-input`
### `repo-review templates write --json --no-input`

Lists registered helper templates, returns one template by ID, or writes a copy
to `--output <path>` with overwrite protection. Workflow commands use these IDs
when suggesting decision templates.

### `repo-review review start --mode delta --repo <path> --range <from>..<to> --review-state <id-or-path> --json --no-input`

Starts or reuses a delta review run, writes diff, impact, and prompt artifacts,
and records a `prompt_ready` run. Duplicate detection uses repo, range, and prior
review state. `--new-run` creates an explicit separate run and `--dry-run`
reports reads, writes, blockers, warnings, and next action without writing.

### `repo-review review package --run <id> --json --no-input`

Packages an `impact_ready` run into a prompt packet and moves it to
`prompt_ready`. `--dry-run` reports intended writes without changing the ledger.

### `repo-review review continue --run <id>|--latest --json --no-input`

Reports the next action for a run without mutating it. `--apply` performs only
safe deterministic transitions, currently packaging `impact_ready` runs.

### `repo-review review ingest --run <id> --input <review.md> --json --no-input`

Attaches reviewer output with `--attach-only` and moves the run to
`review_received`, or validates a delta-review artifact and moves the run to
`ingested`. Ingest output reports candidate-claim and drift counts, warnings,
and next action. `--dry-run` reports intended changes without writing.

### `repo-review review finish --run <id> --json --no-input`

Refuses unresolved runs and completes finishable `ingested` or `drift_ready`
runs. `--dry-run` reports whether the run is finishable.

## Async Strategy

V1 does not ship `repo-review jobs ...` commands. Long-running analysis execution is deferred; agents should use `export-prompt`, run the analyzer externally, then `ingest` the returned artifact.

### `repo-review claims list|get|affected|import --json --no-input`

Queries durable claims without manually parsing review-state files. `claims list` supports status/kind/subject filters and bounded output; `claims get` returns one claim with evidence refs; `claims affected` reports impacted claims from an impact plan. Output includes fully qualified claim IDs.

`claims import` reads a human-authored candidate claims file, validates each
candidate, inherits file-level reviewer identity into claims that omit
`produced_by_analyzer`, validates durable claim shape, refuses duplicate IDs by
default, supports `--overwrite-claims` for intentional replacement, writes the
review state atomically, and appends `review-state.imports.jsonl`.

## Current Scope

- Full and delta review are specified in `docs/incremental-review.md`.
- Initial schemas live in `schemas/`.
- Helper templates for recurring review decisions live in `templates/`,
  including `templates/bootstrap-candidate-claims.md` for selecting durable
  claims after state bootstrap.
- Pass frontmatter linting lives in `tools/lint_pass_frontmatter.py`.
- First-read output validation lives in `tools/validate_pass_output.py`.

## Agent Contract

- Use `--json` for machine-readable output.
- Treat stdout as result data and stderr as diagnostics.
- Do not rely on commands that are absent from `repo-review agent-context --json`.
- Prefer `--no-input` on mutating commands in automated contexts.
- Prefer workflow commands before low-level primitives:
  `review start`, `review continue`, `review ingest`, and `review finish`.
  Use `diff`, `impact`, and `export-prompt` when rebuilding or inspecting one
  artifact explicitly.
- Resolve run state through `review continue` or `runs get` instead of guessing
  from chat context. Durable statuses move through
  `created -> diff_ready -> impact_ready -> prompt_ready -> review_received -> ingested -> drift_ready -> complete`,
  with `blocked` and `failed` reserved for decision/failure states.
- Human output is available for workflow-friendly commands. Agents should still
  request `--json` for stable parsing.
- Long-running analyzer execution, jobs, and webhook delivery are intentionally
  deferred; package artifacts locally and run reviewers/models outside the CLI.
- Treat bootstrapped states as claim-empty until a reviewer explicitly imports
  human-authored candidate claims.
