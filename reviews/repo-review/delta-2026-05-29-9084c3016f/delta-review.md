# Delta Review Discovery Trial

This artifact is intentionally thin. It exists to exercise the
`/repo-review:update` ingest-and-finish workflow during skill discovery, not to
replace a full analytical update.

```yaml
delta_review:
  summary: "Discovery trial for the repo-review skill update workflow. The current branch adds a canonical provider-neutral repo-review skill source and records skill workflow decisions in Beads."
  candidate_claims:
    - "repo-review now has an in-repo provider-neutral skill skeleton under agent/skills/repo-review/."
    - "The update skill is being defined as review-state revision rather than a fresh full review."
  drift:
    - "Prior review material that treated the CLI as the main user-facing maintenance surface may need revision because a skill layer is now being introduced above the CLI substrate."
  warnings:
    - "Discovery artifact only: not a comprehensive closed-loop delta analysis."
```
