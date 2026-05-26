# Invalidation Trigger Helper

Use this when writing or revising `invalidation_triggers` for a durable claim.

## Claim

- Claim ID:
- Statement:
- Evidence refs:
- Watch paths:

## Trigger Candidates

Write triggers as observable future conditions:

- A change to:
  - File or subsystem:
  - Would matter because:
  - Observable invalidating condition:
- A behavior shift in:
  - Runtime, docs, tests, or prompt contract:
  - Would matter because:
  - Observable invalidating condition:

## Quality Check

- Can a future analyzer evaluate the trigger from a diff plus targeted reading?
- Does the trigger name a condition, not a vague concern?
- Is the trigger narrower than "any change in this area"?
- Is it distinct from `watch_paths`?
