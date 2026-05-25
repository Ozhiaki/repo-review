# repo-review Agent Task Manifest

This manifest is the first agent-readable workflow surface for repo-review. It is intentionally small while the incremental review substrate is still being validated.

## Commands

### `repo-review agent-context --json`

Returns the shipped command registry, supported flags, enum values, delivery schemes, available profiles, manifest path, and vocabulary policy.

### `repo-review skill-path --json`

Returns the local directory containing this manifest.

## Current Scope

- Full and delta review are specified in `docs/incremental-review.md`.
- Initial schemas live in `schemas/`.
- Pass frontmatter linting lives in `tools/lint_pass_frontmatter.py`.
- First-read output validation lives in `tools/validate_pass_output.py`.

## Agent Contract

- Use `--json` for machine-readable output.
- Treat stdout as result data and stderr as diagnostics.
- Do not rely on commands that are absent from `repo-review agent-context --json`.
