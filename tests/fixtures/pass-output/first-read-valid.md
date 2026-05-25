# First Read Fixture

This is a minimal prose body for the first-read pass output.

```yaml
pass_output:
  pass_id: first-read
  repo: repo-review-fixture
  analyzed_at: 2026-05-25T00:00:00-04:00
  central_abstraction:
    name: staged interpretive passes
    location: README.md
    is_load_bearing: true
  taste_verdict: distinctive
  signature_move:
    name: blindness-preserving sequence
    location: README.md
  weird_file:
    path: 03-trace.md
    one_line_why: The trace pass turns taste into an enforcement question.
  topic_tags: [repo-review, prompts, analysis]
  confidence:
    overall: medium
    weakest_section: "4"
    coverage: partial
    blind_spots: |
      Fixture output, not a real review. It exists to exercise validator shape checks.
```
