# Affected Claims Helper

Use this when converting a diff report and impact plan into a review decision.
It is a helper, not a new pass.

## Inputs

- Review state:
- Diff report:
- Impact plan:
- Analyzer:

## Claim Selection

For each candidate claim:

- Claim ID:
- Source bucket: `path_hit`, `trigger_hit`, `unknown`, or `manual`
- Changed files or triggers:
- Why this claim is affected:
- Why nearby claims are not affected:
- Required evidence to inspect before updating:
- Decision: `review`, `leave_unaffected`, or `needs_curator`

## Guardrails

- Do not treat a `watch_paths` match as proof that the claim changed.
- Do not treat an absent path match as proof that a semantic trigger is safe.
- Keep local claim IDs scoped to their review state.
