# repo-review Calibration Review

Target commit: `77b7bd3`

This calibration review exercises the incremental-review substrate against `repo-review` itself after the first design, schema, validator, and CLI slices landed. It is intentionally compact; the durable review state in `review-state.json` is the primary calibration artifact.

## First Read

The repo is organized around staged interpretive prompts. Its core claim is not that it can automatically assess a codebase, but that disciplined sequencing changes what an analyzer notices. The README makes this explicit: later passes must be withheld so the first pass remains honest about its blindness.

The strongest design move is that each pass catches a different failure mode: initial overconfidence, under-reading of formal artifacts, aesthetic overcredit, isolation bias, and premature extraction. The new tooling preserves that framing by starting with introspection and validation rather than broad automation.

## Discounted Artifact

The most under-read artifact is now `docs/incremental-review.md`. It changes the repo from a prompt collection into a substrate design: reviews become claim/evidence graphs with analyzer identity, diff reports, impact plans, and delta Drift Surfacer material.

The document is practical enough to implement from. Its weakness is that schemas and CLI are still early: the JSON Schemas are initial contracts, and the CLI only exposes introspection, profiles, status, and feedback. That is an acceptable calibration state, not a mismatch.

## Trace

Load-bearing obligation: repo-review must preserve staged blindness while making outputs machine-inspectable.

The abstract statement is in `README.md`, where it says to present passes one at a time. The normative encoding is pass frontmatter: `prerequisites`, `pass_id`, `output_kind`, and early termination metadata. The implementation layer is currently narrow: `tools/lint_pass_frontmatter.py`, `tools/validate_pass_output.py`, and `repo-review agent-context --json`. Verification exists through `tests/test_agent_native_cli.py` plus fixture checks.

The weakest layer is operational enforcement. There is no full orchestrator yet that prevents a user from handing all prompts to an analyzer at once. The v1 substrate is honest about that gap: it specifies the obligation, validates prompt metadata, and exposes agent context, but does not yet run the full workflow.

## Twin

The adjacent comparison is a conventional static-site or docs-only prompt repo. Against that baseline, repo-review is unusual because it treats prompt sequence as methodology rather than documentation organization. The new incremental substrate keeps that difference visible by making claims and invalidation triggers first-class instead of reducing review maintenance to changed-file summaries.

## Lift

Two extractable patterns survive the calibration:

- Staged blindness as an analysis-control pattern.
- Delta-as-finding: changed interpretations must be labeled separately from changed subjects.

Both are still candidates, not final extractables. They need evidence from Oathweaver or OverCR delta runs before Phase 4 should present them as validated reusable patterns.
