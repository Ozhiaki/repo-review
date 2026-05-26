# Incremental Review

This document is the engineering spec for incremental repo review. It defines the durable substrate shared by full reviews, delta reviews, validators, prompt packets, and the first agent-native CLI slice.

The design goal is continuity without pretending that repo review has become a mechanical fact extractor. A review remains a judgment-heavy artifact, but durable claims and evidence make later maintenance reviews possible without rerunning every pass from scratch.

## Goals

- Support `full` and `delta` review modes over the same review-state substrate.
- Preserve staged review discipline for full reviews.
- Let delta reviews update only affected claims while recording why each claim was surfaced.
- Separate repo change from analyzer reinterpretation.
- Track analyzer identity on pass outputs, claims, diff reports, impact plans, and Drift Surfacer outputs.
- Keep structured data small enough to calibrate against real reviews before expanding tooling.
- Provide a CLI contract that agents can use without prompts, scraping, unbounded output, or ambiguous mutations.

## Non-Goals

- No web UI in v1.
- No automated adjudication of contradictory analysts.
- No cross-repo claim graph in v1. Cross-review references are allowed only through fully qualified claim IDs.
- No broad CLI before the substrate has validators and at least one calibration review.
- No guarantee that local orchestration eliminates context contamination or training-data contamination.

## Review Modes

`full` review is the current staged workflow expressed as structured state. Passes are still issued in order, and later prompts are withheld until their prerequisites are complete.

`delta` review starts from a prior `review_state`, a later repo commit, and a diff report. It produces an impact plan, a prompt packet for affected claims, updated claims, and a delta Drift Surfacer output.

The modes share these objects:

- review state
- pass output references
- claims and evidence references
- analyzer identity
- diff report
- impact plan
- Drift Surfacer material
- framework limits

Helper templates under `templates/` support recurring decisions such as affected-claim selection, invalidation-trigger writing, drift summaries, contested claims, twin selection, trace obligation choice, and lift seed evaluation. They are reusable checklists, not additional review modes or pass prerequisites.

Aggregation across reviews is read-only in v1. `repo-review aggregate` may summarize multiple review states, claim status counts, analyzer identities, and Drift Surfacer outputs, but it must not imply that local claim IDs share identity across repos or review states. Any displayed claim reference should remain qualified by `review_state.id`.

## Review State

A review state is the durable record that a future delta review reads. It identifies the repo version, analyzer, pass outputs, durable claims, structured drift material, and known limits.

```yaml
review_state:
  schema_version: 1
  id: oathweaver-full-2026-05-01
  repo:
    name: oathweaver
    root: /path/to/oathweaver
    remote: null
    commit: abc123
  mode: full
  created_at: 2026-05-01T00:00:00-04:00
  produced_by_analyzer:
    id: codex-2026-05-01
    kind: llm
    model: gpt-5
    tool_context: codex-desktop
  pass_outputs:
    - pass_id: first-read
      path: reviews/oathweaver/full-2026-05-01/01-first-read.md
      output_kind: prose-with-yaml-appendix
      produced_by_analyzer:
        id: codex-2026-05-01
        kind: llm
        model: gpt-5
        tool_context: codex-desktop
  claims: []
  drift_surface: null
  limits:
    - source-only-review
```

`review_state.id` scopes local claim IDs. Two review states may both contain `trace.main_obligation`; those IDs do not collide unless a tool incorrectly ignores the review-state scope.

Cross-review references must use:

```text
<review_state_id>:<claim_id>
```

Example:

```text
oathweaver-full-2026-05-01:trace.main_obligation
```

If a single review state contains the same local claim ID twice, validators must refuse the state and report both locations.

## Analyzer Identity

Analyzer identity is required anywhere judgment enters the artifact. It does not prove objectivity; it makes drift and contradiction inspectable.

```yaml
produced_by_analyzer:
  id: codex-2026-05-01
  kind: llm
  model: gpt-5
  tool_context: codex-desktop
  prompt_set_version: repo-review-v2
  notes: null
```

`id` should be stable for one review run. `kind` is initially `llm`, `human`, or `hybrid`. `model` and `tool_context` are required for LLM or hybrid outputs.

## Claim Rubric

A claim is a stable, falsifiable assertion about the repo, the repo's self-description, the analyst's interpretation, an obligation, or extractable material. A useful claim could plausibly be strengthened, weakened, superseded, invalidated, contested, or left untouched by future evidence.

Include:

- README guarantees, architecture commitments, contracts, and prompt/frontmatter obligations.
- Analyst judgments such as central abstraction, trace verdict, taste verdict, extraction verdict, or authorial model.
- Claims connected to concrete evidence references.
- Claims with `watch_paths` or prose `invalidation_triggers` that a future diff can test.

Exclude:

- Section headings and connective prose.
- Taste adjectives without evidence.
- Restatements of repo-review prompt instructions.
- Hedges that do not assert anything.
- Generic observations that no future repo diff could plausibly affect.

The substrate distinguishes two families:

- Repo claims about itself: guarantees, docs, APIs, frontmatter, declared behavior.
- Analyst claims about the repo: interpretation, verdicts, strength of evidence, extracted patterns.

## Claim And Evidence Shape

Claim status vocabulary:

- `active`: still believed to hold.
- `superseded`: replaced by a newer claim.
- `contested`: contradicted by another analyst or review state.
- `invalidated`: no longer supported by current repo evidence.

```yaml
claims:
  - id: trace.main_obligation
    kind: obligation
    subject:
      type: repo
      ref: .
    statement: "Later passes must be withheld until prerequisites are complete so earlier observations remain uncontaminated."
    evidence_refs:
      - id: ev-readme-review-order
        file: README.md
        locator: "How to run a review"
        quote: "Critical: present the passes to the analyzer one at a time."
    confidence: high
    claim_status: active
    depends_on_claims: []
    related_claims:
      - first-read.blindness_contract
    watch_paths:
      - README.md
      - 01-first-read.md
      - 02-discounted-artifact.md
      - 03-trace.md
      - 04-twin.md
      - 05-lift.md
    invalidation_triggers:
      - "A runner exposes later passes during earlier pass execution."
      - "Pass metadata stops declaring prerequisites."
    produced_by_analyzer:
      id: codex-2026-05-01
      kind: llm
      model: gpt-5
      tool_context: codex-desktop
    contested_by: []
```

Contested claim shape:

```yaml
claims:
  - id: trace.main_obligation
    claim_status: contested
    contested_by:
      - review_state: oathweaver-full-2026-05-08
        claim_id: trace.no_load_bearing_obligation
        reason: "Second analyst found the repo's interest to be curation rather than enforcement."
```

`watch_paths` are mechanical candidates for impact matching. `invalidation_triggers` are prose conditions that require analyst or LLM evaluation. They must not be collapsed into the same field.

## Conflation Guard

Delta review must keep these concepts separate:

- Intra-review delta: pass-to-pass revision on one repo state, such as first-read to discounted-artifact.
- Inter-version delta: review-state update across repo commits.
- Analysis drift: the analyzer sees the same repo differently.
- Subject drift: the repo changed.

Delta prompts and output schemas must require each meaningful change to be labeled as `subject_drift`, `analysis_drift`, or `both`.

```yaml
claim_update:
  claim_id: trace.main_obligation
  update_kind: weakened
  drift_kind: subject_drift
  reason: "A new command now assembles all prompts together, weakening the staged-blindness obligation."
```

A corrected interpretation of unchanged evidence is analysis drift, not proof that the repo changed.

## Diff Report

A diff report summarizes the repo change in bounded, structured form. It should not dump the full raw diff by default.

```yaml
diff_report:
  schema_version: 1
  repo:
    name: oathweaver
    root: /path/to/oathweaver
    remote: null
  range:
    from_commit: abc123
    to_commit: def456
    expression: abc123..def456
  produced_by_analyzer:
    id: repo-review-cli-2026-05-19
    kind: tool
    model: null
    tool_context: repo-review diff
  changed_files:
    - path: README.md
      status: modified
      additions: 18
      deletions: 4
      classifications:
        - docs-only
        - review-contract
      summary: "Adds a generated prompt-pack workflow."
  unknowns: []
```

## Open Diff Taxonomy

Built-in classifications provide shared language:

- `docs-only`
- `tests-only`
- `dependency-config`
- `public-api`
- `core-logic`
- `architecture-boundary`
- `enforcement-path`
- `generated-vendor-noise`
- `deleted-subsystem`
- `new-subsystem`
- `changed-extraction-candidate`

Project-local classifications are allowed. Unknown or project-local classifications are conservative by default: an impact planner may include them in `unknowns` rather than silently ignore them.

## Impact Plan

An impact plan maps changed files and diff classifications to likely affected claims and follow-up work.

It has two distinct paths:

- `path_hits`: mechanical matches between changed files and claim `watch_paths`.
- `trigger_hits`: analyst- or LLM-evaluated matches against prose `invalidation_triggers`.

```yaml
impact_plan:
  schema_version: 1
  from_review: oathweaver-full-2026-05-01
  to_repo_commit: def456
  diff_range: abc123..def456
  path_hits:
    - claim_id: trace.main_obligation
      matched_paths:
        - README.md
  trigger_hits:
    - claim_id: trace.main_obligation
      matched_trigger: "A runner exposes later passes during earlier pass execution."
      evaluator:
        id: codex-2026-05-19
        kind: llm
        model: gpt-5
        tool_context: codex-desktop
  impacted_claims:
    - claim_id: trace.main_obligation
      impact: possibly_weakened
      surfaced_by:
        - path_hit
        - trigger_hit
      reason: "A new prompt-pack workflow may expose later passes earlier than the original staged contract permits."
      required_followup_passes:
        - trace
  unaffected_claims:
    - claim_id: lift.extractable_seed
      reason: "No changed files touch watch paths and no invalidation trigger matched."
  unknowns:
    - changed_file: generated/client.ts
      reason: "Diff classification is project-local and no claim mapping exists yet."
```

`unknowns` is not a junk drawer. It records changed files, classifications, or trigger evaluations that require analyst input before a claim can be safely treated as unaffected.

## Delta Review Artifact

A delta review produces a human-readable artifact and structured updates. It should not pretend to be a fresh full review.

Minimum structured fields:

```yaml
delta_review:
  schema_version: 1
  id: oathweaver-delta-2026-05-19
  from_review: oathweaver-full-2026-05-01
  diff_range: abc123..def456
  produced_by_analyzer:
    id: codex-2026-05-19
    kind: llm
    model: gpt-5
    tool_context: codex-desktop
  updated_claims:
    - claim_id: trace.main_obligation
      previous_status: active
      new_status: active
      update_kind: weakened
      drift_kind: subject_drift
      evidence_refs:
        - id: ev-readme-prompt-pack
          file: README.md
          locator: "Prompt pack"
  new_claims: []
  invalidated_claims: []
  unresolved_questions: []
```

## Drift Surfacer Delta

Repo review has two products: human analysis and structured downstream material. Delta review must update both.

```yaml
delta_drift:
  schema_version: 1
  repo: oathweaver
  from_review: oathweaver-full-2026-05-01
  to_review: oathweaver-delta-2026-05-19
  diff_range: abc123..def456
  produced_by_analyzer:
    id: codex-2026-05-19
    kind: llm
    model: gpt-5
    tool_context: codex-desktop
  new_snapshot_entries: []
  invalidated_snapshot_entries:
    - source_claim: trace.main_obligation
      reason: "Prior snapshot overstated enforcement after the prompt-pack workflow changed."
  strengthened_fascination_seeds: []
  weakened_fascination_seeds:
    - seed_id: staged-blindness-as-method
      reason: "The repo now has a convenience path that may weaken the method."
  new_fascination_seeds: []
  lane_impacts:
    - lane: ai-agents
      impact: weakened
      reason: "Agent convenience may conflict with staged blindness unless the CLI enforces pass gating."
```

## Agent-Native CLI Contract

Every shipped command must be usable by an agent without hidden interaction.

Required behavior:

- `--no-input` is the canonical headless flag. Commands must not prompt when stdin is not a TTY.
- Data-bearing commands support `--json`. JSON goes to stdout; diagnostics go to stderr.
- JSON mode suppresses color, spinners, progress bars, and decorative prose.
- Errors include `code`, `message`, `hint`, and valid values when relevant.
- Mutating commands define idempotence and support `--dry-run` where practical.
- Destructive behavior uses `--force`; overwrite behavior uses `--overwrite`.
- List/query commands are bounded by default and support limits, filters, or selectors.
- File IO uses `--input <path>`, `--output <path>`, and `-` for stdin/stdout where useful.
- Long-running execution requires `--wait` plus recoverable jobs; if v1 only assembles prompt packets, jobs are deferred and not advertised.

For the implemented v1 slice, `repo-review delta` is prompt-packet-only. It does not execute analysis, `--wait` is refused, and `agent-context` must not advertise `jobs` commands until a future version ships a durable job ledger.

Exit codes:

- `0`: success
- `1`: generic failure
- `2`: invalid invocation or missing required input
- `3`: validation or schema failure
- `4`: requested resource not found
- `5`: unsafe mutation refused
- `6`: external command or git failure
- `7`: interrupted or timed out

Vocabulary policy:

- Prefer verbs: `list`, `get`, `create`, `update`, `delete`.
- Prefer flags: `--json`, `--force`, `--overwrite`, `--limit`, `--profile`, `--wait`, `--dry-run`, `--no-input`.
- Do not introduce aliases such as `ls`, `info`, `--format=json`, or `--skip-confirmations`.

Initial CLI surface:

```text
repo-review agent-context --json
repo-review skill-path --json
repo-review status --json
repo-review profile list --json
repo-review profile show <name> --json
repo-review profile save <name> --repo <path> --output <path> --json --no-input
repo-review profile delete <name> --force --json --no-input
repo-review feedback "..." --json --no-input
```

`agent-context --json` returns machine-readable discovery:

```json
{
  "schema_version": 1,
  "commands": [
    {
      "name": "status",
      "flags": ["--json", "--profile", "--no-input"],
      "output_schema": "schemas/status.schema.json"
    }
  ],
  "profiles": ["default"],
  "delivery_schemes": ["stdout", "file:<path>"],
  "delivery": {
    "metadata_key": "delivery_metadata",
    "supported_schemes": ["stdout", "file:<path>"]
  },
  "webhook_delivery": {
    "supported": false,
    "deferred": true
  },
  "skill_manifest_path": "agent/repo-review-task-manifest.md",
  "vocabulary_policy": {
    "preferred_verbs": ["list", "get", "create", "update", "delete"],
    "banned_aliases": ["ls", "info", "--format=json", "--skip-confirmations"]
  }
}
```

`skill-path --json` returns an existing directory that contains an agent-readable task manifest.

Profile precedence is:

```text
explicit flag > environment variable > profile > default
```

Profiles capture repo root, review output directory, analyzer identity, lane vocabulary path, and preferred output mode.

Feedback writes local JSONL and returns the stored entry:

```json
{
  "entry_id": "feedback-2026-05-19T140000Z",
  "path": ".repo-review/feedback.jsonl"
}
```

Delivery schemes start with `stdout` and `file:<path>`. `stdout` delivery in JSON mode returns the artifact inside the JSON response rather than mixing raw artifact text into stdout. `file:<path>` delivery requires an explicit destination and refuses existing files unless the command also receives `--overwrite`. Artifact-producing commands include `delivery_metadata` in JSON results. `webhook:<url>` is deferred in v1 pending authentication, retry, and failure-reporting policy.

## Framework Limits

Incremental review can reduce repeated work, but it cannot prove the review is complete or unbiased.

- Context contamination: staged prompts reduce contamination but cannot erase prior analyst knowledge.
- Training-data contamination: local tooling cannot prove what the model already knows.
- Analyzer/model differences: a new model can produce analysis drift even when the repo is unchanged.
- Source-only review limits: source review can miss runtime behavior, deployment behavior, and social context.
- Generated/vendor ambiguity: generated and vendor files can dominate diffs unless classified carefully.
- Curator/author/analyzer overlap: overlapping roles can bias what gets noticed and what gets forgiven.
- Stale prior reviews: old review states may be incompatible with newer schemas or repo reality.
- Contradictory analyst outputs: contradictions should be preserved as contested claims, not collapsed prematurely.

## Calibration Criteria

The first calibration review tests methodology, not only schema parsing.

Questions to answer:

- Did the claim rubric produce too many or too few claims?
- Were evidence refs precise enough for a future analyst to verify?
- Did structured claims preserve the prose judgment, or flatten it into weaker statements?
- Could likely future diffs map to `watch_paths`?
- Were `invalidation_triggers` concrete enough to evaluate?
- Did analyzer identity reveal useful differences between outputs?
- Did the Drift Surfacer delta shape capture strengthened, weakened, new, and invalidated material?
- Did any schema requirement distort the review enough that the substrate should change?

Calibration findings may revise this document, schemas, or CLI behavior. Revisions should be recorded as decision-log entries in the relevant plan or tracking issue, including cases where a baseline assumption is kept after explicit review.

## Self-Review Hygiene

Changes to `repo-review` itself should use the same incremental machinery when the change could affect review behavior, not only when the code changes. This is routine maintenance review, separate from calibration.

Run a routine self-review delta when a change touches any of these surfaces:

- pass prompts (`01-first-read.md` through `05-lift.md`)
- `docs/incremental-review.md`
- schemas under `schemas/`
- CLI behavior or command registry in `repo-review`
- agent-facing workflow documentation under `agent/`
- validators or tests that change accepted artifact shape
- review examples or fixtures that become normative examples

Small typo fixes, comment-only edits, tracker-only updates, and README wording that does not change workflow semantics do not require a self-review delta. If a change is ambiguous, record why it was skipped in the relevant issue notes.

Routine self-review should produce or update these artifacts under `reviews/repo-review/`:

- a bounded `diff-report.json` for the repo-review change
- an `impact-plan.json` against the latest repo-review review state
- a `delta-trace-prompt.md` packet exported by the CLI
- a human-authored `delta-review.md` or equivalent analyzer output
- a `delta-drift.json` when Drift Surfacer material changes
- an updated or newly versioned `review-state.json` if durable claims change
- friction notes when the CLI or substrate blocks the workflow

Routine self-review is for regression and drift control: it asks whether the current change invalidates, weakens, strengthens, or extends existing claims about the framework.

Calibration review is different. Calibration tests the method itself. Use calibration when schema shape, claim rubric, staged prompt semantics, analyzer identity requirements, or CLI contract assumptions are being evaluated. Calibration may legitimately revise the framework based on what the review process reveals. Routine self-review should not rewrite the rubric unless it discovers a concrete flaw that deserves its own tracked change.
