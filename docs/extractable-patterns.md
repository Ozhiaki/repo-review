# Extractable Review Patterns

This document records repo-review patterns that have evidence from actual
workflow use. It is deliberately narrower than a wishlist. A pattern is listed
as validated only when at least one repo-review calibration or delta run used it
successfully enough that another project could copy the pattern.

## Evidence Base

- `reviews/repo-review/calibration-2026-05-25/review.md`
- `reviews/repo-review/calibration-2026-05-25/calibration-notes.md`
- `reviews/repo-review/calibration-2026-05-25/review-state.json`
- `reviews/oathweaver/delta-2026-05-25/prior-review-state.json`
- `reviews/oathweaver/delta-2026-05-25/impact-plan.json`
- `reviews/oathweaver/delta-2026-05-25/delta-review.md`
- `reviews/oathweaver/delta-2026-05-25/delta-drift.json`
- `reviews/oathweaver/delta-2026-05-25/friction-notes.md`

## Validated Patterns

### Claim/Evidence Review State

Reusable pattern: Convert a prose review into a small set of durable claims,
each with evidence refs, analyzer identity, watch paths, and invalidation
triggers. Treat the review state as the handoff artifact for future maintenance
reviews.

When to apply it:

- A review will need to be revisited after future code changes.
- The output is interpretive, but later readers still need stable handles for
  claims, evidence, and uncertainty.
- The team needs to route diffs to prior judgments without re-running a full
  review.

Validated evidence:

- The repo-review calibration found that four claims were enough to capture the
  central abstraction, substrate shift, trace obligation, and one extractable
  seed without flattening the prose judgment.
- The Oathweaver delta slice used a prior review state to route a real package
  diff to affected claims and produce a delta review.

Do not apply it when:

- The review is intentionally one-off and will not be maintained.
- The claims cannot be tied to evidence refs or future invalidation conditions.
- The workflow would reward inventing claims just to fill a schema.

### Delta As Finding

Reusable pattern: Treat changed interpretation as its own review finding. A
delta review should distinguish subject drift from analysis drift instead of
pretending every update means the underlying repo changed.

When to apply it:

- A prior analysis may be wrong, incomplete, or sharpened by new evidence.
- The repo changed, but the important update may be how the analyst understands
  an existing claim.
- Review consumers need to know whether the subject moved, the interpretation
  moved, or both.

Validated evidence:

- The repo-review calibration identified delta-as-finding as an extractable
  candidate and encoded it as a durable claim.
- The Oathweaver delta review strengthened an existing local-model contract
  claim without invalidating the prior review, and the delta drift output
  separated strengthened material from invalidated or new material.

Do not apply it when:

- The workflow only needs a changelog.
- The prior analysis has no durable claim or evidence structure to revise.
- The distinction between subject and interpretation will not affect any
  downstream decision.

### Scoped Claim Identity

Reusable pattern: Keep local claim IDs scoped to a review state, and qualify
them only when crossing review-state boundaries. Aggregation may summarize
claims across reviews, but it should not merge same-named claims into a global
identity.

When to apply it:

- Multiple reviews may contain similar local claim names such as
  `trace.main_obligation`.
- Tools need to aggregate statuses, analyzers, or drift material across review
  outputs.
- Cross-review comparison is useful, but the project has not designed a global
  claim graph.

Validated evidence:

- The Oathweaver and repo-review states use local claim IDs under different
  review-state IDs.
- CLI claims queries and the aggregation prototype return qualified claim IDs
  while explicitly preserving the no-global-identity boundary.

Do not apply it when:

- A project has already designed and validated a global claim identity model.
- Review states are not durable enough to act as claim scopes.
- Consumers will mistake aggregation for semantic equivalence.

## Candidates Not Yet Promoted

### Staged Blindness As Analysis Control

The repo-review calibration identified staged blindness as a strong candidate:
withholding later prompts changes what the analyzer notices and preserves the
diagnostic value of early passes. It is not promoted here as a validated
extractable because the active-package delta slice did not test the full staged
prompt workflow. Promote it only after a future full review or comparative run
shows that the sequence control still matters outside repo-review itself.

### Helper Templates As Review Scaffolds

The helper templates under `templates/` are practical scaffolds for recurring
decisions, but they have not yet been validated by repeated external review
use. Treat them as repo-review implementation aids until a later review records
which templates reduced friction and which were ignored.
