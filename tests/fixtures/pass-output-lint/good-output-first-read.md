<!-- repo-review:pass_output -->
```yaml
pass_output:
  pass_id: first-read
  source_state:
    ref: ddd444
    ref_kind: commit
    dirty: false
  confidence:
    overall: low
    blind_spots: |
      Most of the test suite was not read.
    smallest_open:
      path: tests/test_core.py
      why_this_open: It would confirm the intended behavior.
      opened_this_pass: false
```
