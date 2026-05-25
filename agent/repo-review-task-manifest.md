# repo-review Agent Task Manifest

This manifest is the first agent-readable workflow surface for repo-review. It is intentionally small while the incremental review substrate is still being validated.

## Commands

### `repo-review agent-context --json`

Returns the shipped command registry, supported flags, enum values, delivery schemes, available profiles, manifest path, and vocabulary policy.

### `repo-review skill-path --json`

Returns the local directory containing this manifest.

### `repo-review status --json`

Returns configured paths, available profiles, and the next relevant review action. Configuration precedence is explicit flag, then environment variable, then selected profile, then default.

### `repo-review profile list|show|save|delete --json`

Manages local profiles stored under `.repo-review/profiles.json`. Mutating profile commands are non-interactive and support `--no-input`; deletion requires `--force`.

### `repo-review feedback "..." --json`

Appends a local feedback entry to `.repo-review/feedback.jsonl` and returns the stored entry id and path.

### `repo-review diff --range <from>..<to> --json --no-input`

Returns a bounded structured git diff report with changed files, summary stats, classification candidates, and truncation metadata. Use `--path <path>` to narrow and `--limit <n>` to control output size.

### `repo-review impact --review-state <path> --diff-report <path> --json --no-input`

Maps changed files from a diff report to claim `watch_paths` from a review state. Output keeps `path_hits`, `trigger_hits`, `impacted_claims`, `unaffected_claims`, and `unknowns` separate.

## Current Scope

- Full and delta review are specified in `docs/incremental-review.md`.
- Initial schemas live in `schemas/`.
- Pass frontmatter linting lives in `tools/lint_pass_frontmatter.py`.
- First-read output validation lives in `tools/validate_pass_output.py`.

## Agent Contract

- Use `--json` for machine-readable output.
- Treat stdout as result data and stderr as diagnostics.
- Do not rely on commands that are absent from `repo-review agent-context --json`.
- Prefer `--no-input` on mutating commands in automated contexts.
