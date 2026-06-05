---
pass_id: lift
version: 3
---

```yaml
pass_output:
  pass_id: lift
  repo: <identifier or URL>
  analyzed_at: <ISO 8601 timestamp>
  source_state:
    ref: <string>
    ref_kind: <commit | tag | archive | date | pasted-files | unknown>
    dirty: <true | false | unknown>
  seeds:
    - id: seed
      source_paths:
        - src/core.py
      source_notes: |
        See src/core.py for the central symbol.
```
