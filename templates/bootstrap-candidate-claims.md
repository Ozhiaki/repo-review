# Bootstrap Candidate Claims

Use this template after `repo-review state bootstrap` creates a review-state shell
from pre-v1 prose. Candidate claims are working material. They are not durable
claims until a reviewer accepts them and imports them with `repo-review claims
import`.

## Source Review Material

- Review state ID:
- Legacy prose files:
- Reviewer selecting claims:
- Selection date:

## Candidate File Shape

Write a JSON file with this shape:

```json
{
  "schema_version": 1,
  "review_state": "repo-full-2026-05-13",
  "produced_by_analyzer": {
    "id": "dave-2026-05-26-claim-selection",
    "kind": "human",
    "model": null,
    "tool_context": "manual claim selection from pre-v1 prose",
    "prompt_set_version": "repo-review-v1",
    "notes": "Human-authored candidate claims selected from old review prose."
  },
  "candidate_claims": [],
  "warnings": []
}
```

Each candidate claim should include:

- `id`: stable local claim ID.
- `kind`: claim category.
- `subject`: object with `type` and `ref`.
- `statement`: short durable assertion.
- `evidence_refs`: files, locators, and optional quotes from the legacy prose.
- `confidence`: `high`, `medium`, or `low`.
- `claim_status`: usually `active`.
- `depends_on_claims` and `related_claims`.
- `watch_paths`: repo paths that should surface this claim during impact.
- `invalidation_triggers`: concrete changes that would weaken or defeat it.
- `contested_by`: usually empty during bootstrap.
- Optional per-claim `produced_by_analyzer` when a claim uses a different identity
  than the file-level identity.

If a candidate omits `produced_by_analyzer`, `repo-review claims import` fills it
from the file-level identity before validating the durable claim.

## Import

```bash
repo-review claims import \
  --review-state /path/to/review-state.json \
  --input /path/to/candidate-claims.json \
  --json --no-input
```

Duplicate claim IDs are refused by default. Use `--overwrite-claims` only when
you intentionally want the candidate file to replace matching durable claims.
