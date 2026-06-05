---
pass_id: first-read
version: 3
---

```yaml
pass_output:
  pass_id: first-read
  repo: <identifier or URL>
  analyzed_at: <ISO 8601 timestamp>
  source_state:
    ref: <string>
    ref_kind: <commit | tag | archive | date | pasted-files | unknown>
    dirty: <true | false | unknown>
  central_abstraction:
    paths:
      - src/core.py; src/engine.py
```
