# repo-review Agent Task Manifest

This manifest is the first agent-readable workflow surface for repo-review. It is intentionally small while the incremental review substrate is still being validated.

## Commands

### `repo-review agent-context --json`

Returns the shipped command registry, supported flags, enum values, delivery schemes, helper template paths, available profiles, manifest path, and vocabulary policy.

### `repo-review skill-path --json`

Returns the local directory containing this manifest.

### `repo-review status --json`

Returns configured paths, available profiles, and the next relevant review action. Configuration precedence is explicit flag, then environment variable, then selected profile, then default.

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

## Async Strategy

V1 does not ship `repo-review jobs ...` commands. Long-running analysis execution is deferred; agents should use `export-prompt`, run the analyzer externally, then `ingest` the returned artifact.

### `repo-review claims list|get|affected --json --no-input`

Queries durable claims without manually parsing review-state files. `claims list` supports status/kind/subject filters and bounded output; `claims get` returns one claim with evidence refs; `claims affected` reports impacted claims from an impact plan. Output includes fully qualified claim IDs.

## Current Scope

- Full and delta review are specified in `docs/incremental-review.md`.
- Initial schemas live in `schemas/`.
- Helper templates for recurring review decisions live in `templates/`.
- Pass frontmatter linting lives in `tools/lint_pass_frontmatter.py`.
- First-read output validation lives in `tools/validate_pass_output.py`.

## Agent Contract

- Use `--json` for machine-readable output.
- Treat stdout as result data and stderr as diagnostics.
- Do not rely on commands that are absent from `repo-review agent-context --json`.
- Prefer `--no-input` on mutating commands in automated contexts.
