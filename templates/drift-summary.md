# Drift Summary Helper

Use this after a delta review to summarize what changed without collapsing
subject drift and analysis drift.

## Inputs

- Prior review state:
- Diff report:
- Impact plan:
- Delta review artifact:
- Analyzer:

## Summary

- Changed subject matter:
- Changed interpretation:
- Claims strengthened:
- Claims weakened:
- Claims invalidated:
- New claims:
- Claims reviewed but left unchanged:

## Drift Classification

For each meaningful update:

- Claim ID:
- Classification: `subject_drift`, `analysis_drift`, or `both`
- Evidence that the repo changed:
- Evidence that the interpretation changed:
- Follow-up needed:

## Guardrails

- A corrected interpretation of unchanged evidence is analysis drift.
- A changed file is not automatically subject drift for every nearby claim.
- Preserve uncertainty instead of forcing a strengthened/weakened verdict.
