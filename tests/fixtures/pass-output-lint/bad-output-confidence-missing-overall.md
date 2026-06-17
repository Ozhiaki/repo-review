<!-- repo-review:pass_output -->
```yaml
pass_output:
  pass_id: trace
  repo: example/repo
  analyzed_at: 2026-06-17T00:00:00Z
  source_state:
    ref: abc123
    ref_kind: commit
    dirty: false
  coverage_closure:
    chosen_from_pass: synthesis
    path: src/core.py
    why_this_was_most_thesis_threatening: It anchors the central claim.
    finding: The claim holds under the traced path.
    changed_prior_judgment: false
    shift_summary: null
  confidence:
    blind_spots: |
      The error paths were not traced this pass.
    smallest_open:
      path: src/errors.py
      why_this_open: It carries the untraced error path.
      opened_this_pass: true
```
