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

Impacted claims: 2
Unknowns: 0

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
          "file": "/Users/dave/p/farm/oathweaver/oathweaver-first-read.md",
          "id": "ev-first-read-local-ai",
          "locator": "What This Author Understands That Most Don't",
          "quote": "local AI quality is a systems problem more than a prompting problem"
        }
      ],
      "id": "first_read.local_ai_systems_problem",
      "invalidation_triggers": [
        "Ollama or local model routing changes bypass explicit user/runtime configuration.",
        "Tests stop covering local model availability or routing behavior."
      ],
      "kind": "central_abstraction",
      "produced_by_analyzer": {
        "id": "codex-2026-05-25-delta-slice",
        "kind": "llm",
        "model": "gpt-5",
        "notes": null,
        "prompt_set_version": "repo-review-v2",
        "tool_context": "codex-desktop"
      },
      "related_claims": [
        "trace.hard_fail_artifact_obligation"
      ],
      "statement": "Oathweaver treats local AI quality as a systems problem solved with routing gates, contracts, memory, trace ledgers, smoke tests, replay bundles, and promotion policies.",
      "subject": {
        "ref": ".",
        "type": "repo"
      },
      "watch_paths": [
        "SourceCode/shared_tools/ollama_client.py",
        "SourceCode/shared_tools/inference_router.py",
        "SourceCode/configs/model_routing.json",
        "tests/test_ollama_wait_for_available.py"
      ]
    },
    {
      "claim_status": "active",
      "confidence": "medium",
      "contested_by": [],
      "depends_on_claims": [],
      "evidence_refs": [
        {
          "file": "/Users/dave/p/farm/oathweaver/oathweaver-trace.md",
          "id": "ev-trace-hard-fail",
          "locator": "Obligation Chosen",
          "quote": "a `web_app` build must either be correct-by-construction or hard-fail before delivery"
        }
      ],
      "id": "trace.hard_fail_artifact_obligation",
      "invalidation_triggers": [
        "Runtime or model availability behavior changes make generated-artifact gates environment-sensitive.",
        "Tests fail to enforce a route or model setting that the generated-artifact pipeline depends on."
      ],
      "kind": "obligation",
      "produced_by_analyzer": {
        "id": "codex-2026-05-25-delta-slice",
        "kind": "llm",
        "model": "gpt-5",
        "notes": null,
        "prompt_set_version": "repo-review-v2",
        "tool_context": "codex-desktop"
      },
      "related_claims": [
        "first_read.local_ai_systems_problem"
      ],
      "statement": "A web_app build must either be correct-by-construction or hard-fail before delivery, never silently broken.",
      "subject": {
        "ref": ".",
        "type": "repo"
      },
      "watch_paths": [
        "SourceCode/agents_make/",
        "tests/agents_make/",
        "SourceCode/shared_tools/ollama_client.py"
      ]
    }
  ],
  "created_at": "2026-05-11T02:15:44-04:00",
  "drift_surface": {
    "fascination_seeds": [
      {
        "seed_id": "local_model_contracts",
        "source_claim": "first_read.local_ai_systems_problem",
        "summary": "Local model behavior becomes reliable when configuration and availability are explicit and tested."
      }
    ],
    "snapshot_entries": [
      {
        "source_claim": "first_read.local_ai_systems_problem",
        "summary": "Oathweaver's local-model quality strategy depends on explicit routing, tests, and operational gates."
      }
    ]
  },
  "id": "oathweaver-full-2026-05-11",
  "limits": [
    "Prior state is structured from existing prose review outputs.",
    "Delta slice uses HEAD~1..HEAD as the demonstration range."
  ],
  "mode": "full",
  "pass_outputs": [
    {
      "output_kind": "prose-with-yaml-appendix",
      "pass_id": "first-read",
      "path": "/Users/dave/p/farm/oathweaver/oathweaver-first-read.md",
      "produced_by_analyzer": {
        "id": "codex-2026-05-11-oathweaver-review",
        "kind": "llm",
        "model": "gpt-5",
        "notes": null,
        "prompt_set_version": "repo-review-v2",
        "tool_context": "codex-desktop"
      }
    },
    {
      "output_kind": "prose-with-yaml-appendix",
      "pass_id": "trace",
      "path": "/Users/dave/p/farm/oathweaver/oathweaver-trace.md",
      "produced_by_analyzer": {
        "id": "codex-2026-05-11-oathweaver-review",
        "kind": "llm",
        "model": "gpt-5",
        "notes": null,
        "prompt_set_version": "repo-review-v2",
        "tool_context": "codex-desktop"
      }
    }
  ],
  "produced_by_analyzer": {
    "id": "codex-2026-05-11-oathweaver-review",
    "kind": "llm",
    "model": "gpt-5",
    "notes": "Structured from existing Oathweaver first-read, discounted-artifact, trace, and lift review outputs.",
    "prompt_set_version": "repo-review-v2",
    "tool_context": "codex-desktop"
  },
  "repo": {
    "commit": "c05e1ca8bfe352a1c2c7065cdebadddf2a1fd257",
    "name": "oathweaver",
    "remote": "https://github.com/TheEditor/oathweaver.git",
    "root": "/Users/dave/p/farm/oathweaver/oathweaver"
  },
  "schema_version": 1
}
```

## Diff Report

```json
{
  "changed_files": [
    {
      "additions": 1,
      "classifications": [
        "core-logic"
      ],
      "deletions": 1,
      "path": "SourceCode/shared_tools/ollama_client.py",
      "status": "modified",
      "summary": "modified file with 1 additions and 1 deletions"
    },
    {
      "additions": 46,
      "classifications": [
        "tests-only"
      ],
      "deletions": 0,
      "path": "tests/test_ollama_wait_for_available.py",
      "status": "modified",
      "summary": "modified file with 46 additions and 0 deletions"
    }
  ],
  "produced_by_analyzer": {
    "id": "repo-review-cli",
    "kind": "tool",
    "model": null,
    "tool_context": "repo-review diff"
  },
  "range": {
    "expression": "c05e1ca8bfe352a1c2c7065cdebadddf2a1fd257..59b0337ff006d00f87579f8b65077726404d022a",
    "from_commit": "c05e1ca8bfe352a1c2c7065cdebadddf2a1fd257",
    "to_commit": "59b0337ff006d00f87579f8b65077726404d022a"
  },
  "repo": {
    "name": "oathweaver",
    "remote": "https://github.com/Ozhiaki/oathweaver.git",
    "root": "/Users/dave/p/farm/oathweaver/oathweaver"
  },
  "schema_version": 1,
  "summary_stats": {
    "additions": 47,
    "deletions": 1,
    "files_changed": 2
  },
  "truncation": {
    "limit": 50,
    "narrowing_hints": [],
    "shown": 2,
    "total": 2,
    "truncated": false
  },
  "unknowns": []
}
```

## Impact Plan

```json
{
  "diff_range": "c05e1ca8bfe352a1c2c7065cdebadddf2a1fd257..59b0337ff006d00f87579f8b65077726404d022a",
  "from_review": "oathweaver-full-2026-05-11",
  "impacted_claims": [
    {
      "claim_id": "first_read.local_ai_systems_problem",
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
      "claim_id": "trace.hard_fail_artifact_obligation",
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
      "claim_id": "first_read.local_ai_systems_problem",
      "matched_paths": [
        "SourceCode/shared_tools/ollama_client.py",
        "tests/test_ollama_wait_for_available.py"
      ]
    },
    {
      "claim_id": "trace.hard_fail_artifact_obligation",
      "matched_paths": [
        "SourceCode/shared_tools/ollama_client.py"
      ]
    }
  ],
  "schema_version": 1,
  "to_repo_commit": "59b0337ff006d00f87579f8b65077726404d022a",
  "trigger_hits": [],
  "unaffected_claims": [],
  "unknowns": []
}
```
