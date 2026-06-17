---
pass_id: synthesis
version: 1
---

The Synthesis composes the First Read and Discounted Artifact priors into a
single coherent thesis. It may trace a claim back to its evidence and lift out
the load-bearing abstraction, but it never hands work forward to a later pass.

```yaml
pass_output:
  pass_id: synthesis
  repo: <identifier or URL>
  analyzed_at: <ISO 8601 timestamp>
  source_state:
    ref: <string>
    ref_kind: <commit | tag | archive | date | pasted-files | unknown>
    dirty: <true | false | unknown>
  synthesized_central_abstraction:
    name: <one short phrase>
    paths:
      - src/core.py
  confidence:
    overall: <high | medium | low>
    blind_spots: |
      <short paragraph>
    smallest_open:
      path: <repo-relative path>
      why_this_open: <one sentence>
      opened_this_pass: <true | false>
```
