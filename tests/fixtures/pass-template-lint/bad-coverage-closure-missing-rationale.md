---
pass_id: trace
version: 3
---

```yaml
pass_output:
  pass_id: trace
  repo: <identifier or URL>
  analyzed_at: <ISO 8601 timestamp>
  source_state:
    ref: <string>
    ref_kind: <commit | tag | archive | date | pasted-files | unknown>
    dirty: <true | false | unknown>
  coverage_closure:
    chosen_from_pass: <first-read | discounted-artifact | synthesis>
    path: <repo-relative path>
    finding: <one short paragraph>
    changed_prior_judgment: <true | false>
    shift_summary: <short | null>
  confidence:
    overall: <high | medium | low>
    blind_spots: |
      <short paragraph>
    smallest_open:
      path: <repo-relative path>
      why_this_open: <one sentence>
      opened_this_pass: <true | false>
```
