# Delta Trace Prompt Packet

You are updating an existing repo-review state. Do not rerun a full review.

## Required Output

- Include `produced_by_analyzer` with analyzer identity.
- Update only claims surfaced by the impact plan unless new evidence requires a new claim.
- Label each meaningful update as `subject_drift`, `analysis_drift`, or `both`.
- Preserve contested or uncertain claims instead of silently adjudicating them.

## Conflation Guard

Keep intra-review delta, inter-version delta, analysis drift, and subject drift separate. A corrected interpretation of unchanged evidence is analysis drift, not proof that the repo changed.

## Impact Summary

Impacted claims: 4
Unknowns: 6

## Prior Review State

```json
{
  "claims": [
    {
      "claim_status": "active",
      "confidence": "high",
      "contested_by": [],
      "depends_on_claims": [],
      "evidence_refs": [
        {
          "file": "README.md",
          "id": "ev-readme-pass-order",
          "locator": "How to run a review",
          "quote": "Critical: present the passes to the analyzer one at a time."
        },
        {
          "file": "README.md",
          "id": "ev-root-pass-files",
          "locator": "The Passes",
          "quote": "The series is designed to be run in order."
        }
      ],
      "id": "first_read.central_abstraction",
      "invalidation_triggers": [
        "A runner exposes later passes before prerequisite passes are complete.",
        "Pass files stop declaring prerequisites or review order."
      ],
      "kind": "central_abstraction",
      "produced_by_analyzer": {
        "id": "codex-2026-05-25-calibration",
        "kind": "llm",
        "model": "gpt-5",
        "notes": null,
        "prompt_set_version": "repo-review-v2",
        "tool_context": "codex-desktop"
      },
      "related_claims": [
        "trace.staged_blindness_obligation"
      ],
      "statement": "repo-review is organized around staged interpretive passes that preserve analyzer blindness between review phases.",
      "subject": {
        "ref": ".",
        "type": "repo"
      },
      "watch_paths": [
        "README.md",
        "01-first-read.md",
        "02-discounted-artifact.md",
        "03-trace.md",
        "04-twin.md",
        "05-lift.md"
      ]
    },
    {
      "claim_status": "active",
      "confidence": "high",
      "contested_by": [],
      "depends_on_claims": [
        "first_read.central_abstraction"
      ],
      "evidence_refs": [
        {
          "file": "docs/incremental-review.md",
          "id": "ev-incremental-review-state",
          "locator": "Review State",
          "quote": "A review state is the durable record that a future delta review reads."
        },
        {
          "file": "docs/incremental-review.md",
          "id": "ev-claim-rubric",
          "locator": "Claim Rubric",
          "quote": "A claim is a stable, falsifiable assertion about the repo."
        }
      ],
      "id": "discounted_artifact.incremental_substrate",
      "invalidation_triggers": [
        "Schemas or CLI commands drop claim/evidence identity from review artifacts.",
        "Delta review output updates prose without updating claims."
      ],
      "kind": "methodology",
      "produced_by_analyzer": {
        "id": "codex-2026-05-25-calibration",
        "kind": "llm",
        "model": "gpt-5",
        "notes": null,
        "prompt_set_version": "repo-review-v2",
        "tool_context": "codex-desktop"
      },
      "related_claims": [
        "trace.staged_blindness_obligation"
      ],
      "statement": "The incremental-review design turns reviews into durable claim/evidence state rather than treating them as prose-only reports.",
      "subject": {
        "ref": "docs/incremental-review.md",
        "type": "artifact"
      },
      "watch_paths": [
        "docs/incremental-review.md",
        "schemas/*.schema.json",
        "tools/validate_pass_output.py"
      ]
    },
    {
      "claim_status": "active",
      "confidence": "medium",
      "contested_by": [],
      "depends_on_claims": [
        "first_read.central_abstraction"
      ],
      "evidence_refs": [
        {
          "file": "03-trace.md",
          "id": "ev-frontmatter-prerequisites",
          "locator": "frontmatter prerequisites",
          "quote": "prerequisites:"
        },
        {
          "file": "tools/lint_pass_frontmatter.py",
          "id": "ev-frontmatter-linter",
          "locator": "REQUIRED_KEYS",
          "quote": "REQUIRED_KEYS"
        },
        {
          "file": "repo-review",
          "id": "ev-agent-context",
          "locator": "agent_context",
          "quote": "commands"
        }
      ],
      "id": "trace.staged_blindness_obligation",
      "invalidation_triggers": [
        "A CLI command runs or exports all pass prompts without preserving prerequisite order.",
        "Machine-readable output stops carrying pass identity or prerequisite metadata."
      ],
      "kind": "obligation",
      "produced_by_analyzer": {
        "id": "codex-2026-05-25-calibration",
        "kind": "llm",
        "model": "gpt-5",
        "notes": "Operational enforcement is partial until orchestration exists.",
        "prompt_set_version": "repo-review-v2",
        "tool_context": "codex-desktop"
      },
      "related_claims": [
        "discounted_artifact.incremental_substrate"
      ],
      "statement": "repo-review must preserve staged blindness while making pass outputs machine-inspectable.",
      "subject": {
        "ref": ".",
        "type": "repo"
      },
      "watch_paths": [
        "repo-review",
        "tools/lint_pass_frontmatter.py",
        "tools/validate_pass_output.py",
        "tests/test_agent_native_cli.py",
        "*.md"
      ]
    },
    {
      "claim_status": "active",
      "confidence": "medium",
      "contested_by": [],
      "depends_on_claims": [
        "discounted_artifact.incremental_substrate"
      ],
      "evidence_refs": [
        {
          "file": "docs/incremental-review.md",
          "id": "ev-conflation-guard",
          "locator": "Conflation Guard",
          "quote": "Delta review must keep these concepts separate."
        }
      ],
      "id": "lift.delta_as_finding",
      "invalidation_triggers": [
        "Delta output can update a claim without labeling subject drift versus analysis drift."
      ],
      "kind": "extractable",
      "produced_by_analyzer": {
        "id": "codex-2026-05-25-calibration",
        "kind": "llm",
        "model": "gpt-5",
        "notes": "Candidate extractable; not yet validated on Oathweaver or OverCR.",
        "prompt_set_version": "repo-review-v2",
        "tool_context": "codex-desktop"
      },
      "related_claims": [],
      "statement": "Delta review should treat changed interpretation as a finding distinct from changed subject matter.",
      "subject": {
        "ref": "delta-as-finding",
        "type": "extractable"
      },
      "watch_paths": [
        "docs/incremental-review.md",
        "schemas/impact_plan.schema.json",
        "schemas/delta_drift.schema.json"
      ]
    }
  ],
  "created_at": "2026-05-25T16:00:00-04:00",
  "drift_surface": {
    "fascination_seeds": [
      {
        "seed_id": "staged_blindness_as_method",
        "source_claim": "first_read.central_abstraction",
        "summary": "Prompt sequencing can be treated as a control surface for analysis quality."
      },
      {
        "seed_id": "delta_as_finding",
        "source_claim": "lift.delta_as_finding",
        "summary": "A delta review can surface changed interpretation as an explicit result."
      }
    ],
    "snapshot_entries": [
      {
        "source_claim": "first_read.central_abstraction",
        "summary": "repo-review's main object is staged interpretive attention, not generic code review automation."
      },
      {
        "source_claim": "trace.staged_blindness_obligation",
        "summary": "Operational enforcement is partial: metadata and tests exist, full orchestration does not."
      }
    ]
  },
  "id": "repo-review-calibration-2026-05-25",
  "limits": [
    "self-review target may overfit to repo-review vocabulary",
    "source-only review",
    "no external package calibration yet",
    "operational orchestration remains partial"
  ],
  "mode": "full",
  "pass_outputs": [
    {
      "output_kind": "prose-with-yaml-appendix",
      "pass_id": "calibration-full",
      "path": "reviews/repo-review/calibration-2026-05-25/review.md",
      "produced_by_analyzer": {
        "id": "codex-2026-05-25-calibration",
        "kind": "llm",
        "model": "gpt-5",
        "notes": null,
        "prompt_set_version": "repo-review-v2",
        "tool_context": "codex-desktop"
      }
    }
  ],
  "produced_by_analyzer": {
    "id": "codex-2026-05-25-calibration",
    "kind": "llm",
    "model": "gpt-5",
    "notes": "Calibration review against repo-review itself after initial incremental substrate work.",
    "prompt_set_version": "repo-review-v2",
    "tool_context": "codex-desktop"
  },
  "repo": {
    "commit": "77b7bd3",
    "name": "repo-review",
    "remote": "https://github.com/TheEditor/repo-review.git",
    "root": "/Users/dave/p/repo-review/repo-review"
  },
  "schema_version": 1
}
```

## Diff Report

```json
{
  "changed_files": [
    {
      "additions": 71,
      "classifications": [
        "core-logic"
      ],
      "deletions": 21,
      "path": ".beads/issues.jsonl",
      "status": "modified",
      "summary": "modified file with 71 additions and 21 deletions"
    },
    {
      "additions": 416,
      "classifications": [
        "docs-only"
      ],
      "deletions": 48,
      "path": "README.md",
      "status": "modified",
      "summary": "modified file with 416 additions and 48 deletions"
    },
    {
      "additions": 196,
      "classifications": [
        "docs-only"
      ],
      "deletions": 2,
      "path": "agent/repo-review-task-manifest.md",
      "status": "modified",
      "summary": "modified file with 196 additions and 2 deletions"
    },
    {
      "additions": 57,
      "classifications": [
        "new-subsystem",
        "docs-only"
      ],
      "deletions": 0,
      "path": "agent/skills/repo-review/SKILL.md",
      "status": "added",
      "summary": "added file with 57 additions and 0 deletions"
    },
    {
      "additions": 61,
      "classifications": [
        "new-subsystem",
        "docs-only"
      ],
      "deletions": 0,
      "path": "agent/skills/repo-review/references/artifact-contracts.md",
      "status": "added",
      "summary": "added file with 61 additions and 0 deletions"
    },
    {
      "additions": 102,
      "classifications": [
        "new-subsystem",
        "docs-only"
      ],
      "deletions": 0,
      "path": "agent/skills/repo-review/references/command-selection.md",
      "status": "added",
      "summary": "added file with 102 additions and 0 deletions"
    },
    {
      "additions": 126,
      "classifications": [
        "new-subsystem",
        "docs-only"
      ],
      "deletions": 0,
      "path": "agent/skills/repo-review/references/update.md",
      "status": "added",
      "summary": "added file with 126 additions and 0 deletions"
    },
    {
      "additions": 124,
      "classifications": [
        "new-subsystem",
        "docs-only"
      ],
      "deletions": 0,
      "path": "docs/extractable-patterns.md",
      "status": "added",
      "summary": "added file with 124 additions and 0 deletions"
    },
    {
      "additions": 45,
      "classifications": [
        "docs-only"
      ],
      "deletions": 1,
      "path": "docs/incremental-review.md",
      "status": "modified",
      "summary": "modified file with 45 additions and 1 deletions"
    },
    {
      "additions": 3987,
      "classifications": [
        "core-logic"
      ],
      "deletions": 148,
      "path": "repo-review",
      "status": "modified",
      "summary": "modified file with 3987 additions and 148 deletions"
    },
    {
      "additions": 34,
      "classifications": [
        "new-subsystem"
      ],
      "deletions": 0,
      "path": "reviews/oathweaver/delta-2026-05-25/delta-drift.json",
      "status": "added",
      "summary": "added file with 34 additions and 0 deletions"
    },
    {
      "additions": 71,
      "classifications": [
        "new-subsystem",
        "docs-only"
      ],
      "deletions": 0,
      "path": "reviews/oathweaver/delta-2026-05-25/delta-review.md",
      "status": "added",
      "summary": "added file with 71 additions and 0 deletions"
    },
    {
      "additions": 288,
      "classifications": [
        "new-subsystem",
        "docs-only"
      ],
      "deletions": 0,
      "path": "reviews/oathweaver/delta-2026-05-25/delta-trace-prompt.md",
      "status": "added",
      "summary": "added file with 288 additions and 0 deletions"
    },
    {
      "additions": 54,
      "classifications": [
        "new-subsystem"
      ],
      "deletions": 0,
      "path": "reviews/oathweaver/delta-2026-05-25/diff-report.json",
      "status": "added",
      "summary": "added file with 54 additions and 0 deletions"
    },
    {
      "additions": 24,
      "classifications": [
        "new-subsystem",
        "docs-only"
      ],
      "deletions": 0,
      "path": "reviews/oathweaver/delta-2026-05-25/friction-notes.md",
      "status": "added",
      "summary": "added file with 24 additions and 0 deletions"
    },
    {
      "additions": 48,
      "classifications": [
        "new-subsystem"
      ],
      "deletions": 0,
      "path": "reviews/oathweaver/delta-2026-05-25/impact-plan.json",
      "status": "added",
      "summary": "added file with 48 additions and 0 deletions"
    },
    {
      "additions": 152,
      "classifications": [
        "new-subsystem"
      ],
      "deletions": 0,
      "path": "reviews/oathweaver/delta-2026-05-25/prior-review-state.json",
      "status": "added",
      "summary": "added file with 152 additions and 0 deletions"
    },
    {
      "additions": 54,
      "classifications": [
        "new-subsystem",
        "docs-only"
      ],
      "deletions": 0,
      "path": "reviews/repo-review/calibration-2026-05-25/calibration-notes.md",
      "status": "added",
      "summary": "added file with 54 additions and 0 deletions"
    },
    {
      "additions": 263,
      "classifications": [
        "new-subsystem"
      ],
      "deletions": 0,
      "path": "reviews/repo-review/calibration-2026-05-25/review-state.json",
      "status": "added",
      "summary": "added file with 263 additions and 0 deletions"
    },
    {
      "additions": 38,
      "classifications": [
        "new-subsystem",
        "docs-only"
      ],
      "deletions": 0,
      "path": "reviews/repo-review/calibration-2026-05-25/review.md",
      "status": "added",
      "summary": "added file with 38 additions and 0 deletions"
    },
    {
      "additions": 113,
      "classifications": [
        "new-subsystem",
        "architecture-boundary"
      ],
      "deletions": 0,
      "path": "schemas/candidate_claim.schema.json",
      "status": "added",
      "summary": "added file with 113 additions and 0 deletions"
    },
    {
      "additions": 1,
      "classifications": [
        "architecture-boundary"
      ],
      "deletions": 1,
      "path": "schemas/common.schema.json",
      "status": "modified",
      "summary": "modified file with 1 additions and 1 deletions"
    },
    {
      "additions": 97,
      "classifications": [
        "new-subsystem",
        "architecture-boundary"
      ],
      "deletions": 0,
      "path": "schemas/delta_review_artifact.schema.json",
      "status": "added",
      "summary": "added file with 97 additions and 0 deletions"
    },
    {
      "additions": 114,
      "classifications": [
        "new-subsystem",
        "architecture-boundary"
      ],
      "deletions": 0,
      "path": "schemas/review_run.schema.json",
      "status": "added",
      "summary": "added file with 114 additions and 0 deletions"
    },
    {
      "additions": 29,
      "classifications": [
        "new-subsystem",
        "docs-only"
      ],
      "deletions": 0,
      "path": "templates/affected-claims.md",
      "status": "added",
      "summary": "added file with 29 additions and 0 deletions"
    },
    {
      "additions": 65,
      "classifications": [
        "new-subsystem",
        "docs-only"
      ],
      "deletions": 0,
      "path": "templates/bootstrap-candidate-claims.md",
      "status": "added",
      "summary": "added file with 65 additions and 0 deletions"
    },
    {
      "additions": 39,
      "classifications": [
        "new-subsystem",
        "docs-only"
      ],
      "deletions": 0,
      "path": "templates/contested-claim.md",
      "status": "added",
      "summary": "added file with 39 additions and 0 deletions"
    },
    {
      "additions": 38,
      "classifications": [
        "new-subsystem",
        "docs-only"
      ],
      "deletions": 0,
      "path": "templates/drift-summary.md",
      "status": "added",
      "summary": "added file with 38 additions and 0 deletions"
    },
    {
      "additions": 30,
      "classifications": [
        "new-subsystem",
        "docs-only"
      ],
      "deletions": 0,
      "path": "templates/invalidation-trigger.md",
      "status": "added",
      "summary": "added file with 30 additions and 0 deletions"
    },
    {
      "additions": 33,
      "classifications": [
        "new-subsystem",
        "docs-only"
      ],
      "deletions": 0,
      "path": "templates/lift-seed.md",
      "status": "added",
      "summary": "added file with 33 additions and 0 deletions"
    },
    {
      "additions": 27,
      "classifications": [
        "new-subsystem",
        "docs-only"
      ],
      "deletions": 0,
      "path": "templates/trace-obligation.md",
      "status": "added",
      "summary": "added file with 27 additions and 0 deletions"
    },
    {
      "additions": 31,
      "classifications": [
        "new-subsystem",
        "docs-only"
      ],
      "deletions": 0,
      "path": "templates/twin-selection.md",
      "status": "added",
      "summary": "added file with 31 additions and 0 deletions"
    },
    {
      "additions": 37,
      "classifications": [
        "new-subsystem",
        "docs-only",
        "tests-only"
      ],
      "deletions": 0,
      "path": "tests/fixtures/README.md",
      "status": "added",
      "summary": "added file with 37 additions and 0 deletions"
    },
    {
      "additions": 1965,
      "classifications": [
        "tests-only"
      ],
      "deletions": 0,
      "path": "tests/test_agent_native_cli.py",
      "status": "modified",
      "summary": "modified file with 1965 additions and 0 deletions"
    }
  ],
  "produced_by_analyzer": {
    "id": "repo-review-cli",
    "kind": "tool",
    "model": null,
    "tool_context": "repo-review diff"
  },
  "range": {
    "expression": "77b7bd3..HEAD",
    "from_commit": "77b7bd3",
    "to_commit": "HEAD"
  },
  "repo": {
    "name": "repo-review",
    "remote": "https://github.com/TheEditor/repo-review.git",
    "root": "/Users/dave/p/repo-review/repo-review"
  },
  "schema_version": 1,
  "summary_stats": {
    "additions": 8830,
    "deletions": 221,
    "files_changed": 34
  },
  "truncation": {
    "limit": 50,
    "narrowing_hints": [],
    "shown": 34,
    "total": 34,
    "truncated": false
  },
  "unknowns": []
}
```

## Impact Plan

```json
{
  "diff_range": "77b7bd3..HEAD",
  "from_review": "repo-review-calibration-2026-05-25",
  "impacted_claims": [
    {
      "claim_id": "discounted_artifact.incremental_substrate",
      "impact": "unknown",
      "reason": "Claim surfaced by path_hit.",
      "required_followup_passes": [
        "trace"
      ],
      "surfaced_by": [
        "path_hit"
      ]
    },
    {
      "claim_id": "first_read.central_abstraction",
      "impact": "unknown",
      "reason": "Claim surfaced by path_hit.",
      "required_followup_passes": [
        "trace"
      ],
      "surfaced_by": [
        "path_hit"
      ]
    },
    {
      "claim_id": "lift.delta_as_finding",
      "impact": "unknown",
      "reason": "Claim surfaced by path_hit.",
      "required_followup_passes": [
        "trace"
      ],
      "surfaced_by": [
        "path_hit"
      ]
    },
    {
      "claim_id": "trace.staged_blindness_obligation",
      "impact": "unknown",
      "reason": "Claim surfaced by path_hit.",
      "required_followup_passes": [
        "trace"
      ],
      "surfaced_by": [
        "path_hit"
      ]
    }
  ],
  "path_hits": [
    {
      "claim_id": "first_read.central_abstraction",
      "matched_paths": [
        "README.md"
      ]
    },
    {
      "claim_id": "discounted_artifact.incremental_substrate",
      "matched_paths": [
        "docs/incremental-review.md",
        "schemas/candidate_claim.schema.json",
        "schemas/common.schema.json",
        "schemas/delta_review_artifact.schema.json",
        "schemas/review_run.schema.json"
      ]
    },
    {
      "claim_id": "trace.staged_blindness_obligation",
      "matched_paths": [
        "README.md",
        "agent/repo-review-task-manifest.md",
        "agent/skills/repo-review/SKILL.md",
        "agent/skills/repo-review/references/artifact-contracts.md",
        "agent/skills/repo-review/references/command-selection.md",
        "agent/skills/repo-review/references/update.md",
        "docs/extractable-patterns.md",
        "docs/incremental-review.md",
        "repo-review",
        "reviews/oathweaver/delta-2026-05-25/delta-review.md",
        "reviews/oathweaver/delta-2026-05-25/delta-trace-prompt.md",
        "reviews/oathweaver/delta-2026-05-25/friction-notes.md",
        "reviews/repo-review/calibration-2026-05-25/calibration-notes.md",
        "reviews/repo-review/calibration-2026-05-25/review.md",
        "templates/affected-claims.md",
        "templates/bootstrap-candidate-claims.md",
        "templates/contested-claim.md",
        "templates/drift-summary.md",
        "templates/invalidation-trigger.md",
        "templates/lift-seed.md",
        "templates/trace-obligation.md",
        "templates/twin-selection.md",
        "tests/fixtures/README.md",
        "tests/test_agent_native_cli.py"
      ]
    },
    {
      "claim_id": "lift.delta_as_finding",
      "matched_paths": [
        "docs/incremental-review.md"
      ]
    }
  ],
  "schema_version": 1,
  "to_repo_commit": "HEAD",
  "trigger_hits": [],
  "unaffected_claims": [],
  "unknowns": [
    {
      "changed_file": ".beads/issues.jsonl",
      "classification": "core-logic",
      "reason": "No claim watch_path matched this changed file; semantic trigger evaluation may still be needed."
    },
    {
      "changed_file": "reviews/oathweaver/delta-2026-05-25/delta-drift.json",
      "classification": "new-subsystem",
      "reason": "No claim watch_path matched this changed file; semantic trigger evaluation may still be needed."
    },
    {
      "changed_file": "reviews/oathweaver/delta-2026-05-25/diff-report.json",
      "classification": "new-subsystem",
      "reason": "No claim watch_path matched this changed file; semantic trigger evaluation may still be needed."
    },
    {
      "changed_file": "reviews/oathweaver/delta-2026-05-25/impact-plan.json",
      "classification": "new-subsystem",
      "reason": "No claim watch_path matched this changed file; semantic trigger evaluation may still be needed."
    },
    {
      "changed_file": "reviews/oathweaver/delta-2026-05-25/prior-review-state.json",
      "classification": "new-subsystem",
      "reason": "No claim watch_path matched this changed file; semantic trigger evaluation may still be needed."
    },
    {
      "changed_file": "reviews/repo-review/calibration-2026-05-25/review-state.json",
      "classification": "new-subsystem",
      "reason": "No claim watch_path matched this changed file; semantic trigger evaluation may still be needed."
    }
  ]
}
```
