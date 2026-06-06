---
pass_id: delta-review
name: The Delta Review
version: 2
prerequisites:
  - first-read
recommended_prerequisites:
  - discounted-artifact
  - synthesis
  - trace
  - twin
  - lift
output_kind: prose-with-yaml-appendix
terminates_early_when: never
intended_audience:
  - human-curator
  - downstream-analysis-passes
  - downstream-extraction-tools
---

# The Delta Review
*An incremental prompt for updating an existing repo-review analysis after the target repo has changed*

---

## Why this is a separate document

The base passes ask an analyzer to form expensive judgments about a repo at a particular moment in its evolution. That cost is part of their value: The First Read catches a real first impression, The Discounted Artifact corrects a predictable attention failure, the optional Synthesis composes those first two judgments, The Trace tests whether the repo's spine reaches its bones, The Twin anchors originality against an adjacent repo, and The Lift asks what survives extraction.

When the target repo changes, running those base passes again from scratch is often wasteful. Most commits do not invalidate the deepest judgments. They add surface area, strengthen an already-identified move, weaken one claim, or leave the original analysis intact. The update question is narrower:

> Given the prior analysis package and the repo changes since then, what judgments need to move?

This pass exists to answer that question without pretending the analyzer is encountering the repo for the first time. It treats the original prose as the authority and the structured appendices as an index into that authority. The structured output tells the analyzer where claims live, which sections have already shifted, which obligation was traced, which seeds were lifted, and where confidence was weak. The prose carries the nuance that the schema intentionally does not.

---

## What this prompt is for

Use this pass when you have:

- A baseline repo-review analysis package for a target repo.
- A baseline repo state: commit, tag, branch date, archive, or other stable reference.
- A later repo state to compare against.
- Enough repo access to inspect the changes between those two states.

The goal is not to produce a new full review. The goal is to produce an update memo: which prior claims still hold, which are strengthened, which are weakened, which are refuted, which new facts matter, and whether any base pass must be rerun because the repo changed too much for incremental review to be honest.

This pass can operate from the pure text of the original analyses, but it should prefer the structured appendices when available. Use the structured appendices to build the claim map. Use the prose to decide meaning.

When available, use `baseline_source_state` and `updated_source_state` as the
canonical source-state anchors for the comparison. If either side is missing,
mark that side's precision low and fall back to legacy `baseline_ref`,
`updated_ref`, `location` strings, and prose only after checking for the new
fields. Do not infer exact refs from `analyzed_at`.

---

## How to use this document

Paste this prompt into a new analyzer chat or into the same chat that produced the original review. Provide:

1. **The baseline review package.** Include every available prior pass output, prose and YAML appendix. If you only have prose, say so.
2. **The baseline repo reference.** Commit SHA, tag, date, archive URL, or other exact reference.
3. **The updated repo reference.** Commit SHA, tag, date, branch, archive URL, or working tree snapshot.
4. **The change evidence.** Prefer `git diff --stat`, `git log --oneline <baseline>..<updated>`, and changed files. For large repos, include the diff for likely load-bearing files first, then let the analyzer request more.
5. **Any known human concern.** If the update was made for a specific feature, rewrite, incident, or release, say that upfront. That is not contamination; it is the reason the delta exists.

Do not paste the base prompts again unless this pass concludes that a base rerun is required. The analyzer may inspect files and diffs, but should not repeat the base review procedure.

---

## The Prompt

You are updating an existing repo-review analysis after the target repo changed.

You are not performing The First Read again. You are not rerunning The Discounted Artifact, The Synthesis, The Trace, The Twin, or The Lift from scratch. You are conducting a delta review: compare the prior review package against the repo changes since the baseline reference, then decide what must change in the prior analysis.

### 1. Establish the baseline

Identify:

- The baseline repo reference and updated repo reference.
- Which prior pass outputs are available.
- Whether each prior pass has both prose and structured YAML, prose only, or structured YAML only.
- The prior review's weakest confidence points and blind spots.

Use the structured appendices as a claim index. At minimum, extract these candidate claims when present:

- First Read: central abstraction, taste verdict, signature move, weird file, confidence blind spots.
- Discounted Artifact: artifact chosen, delta size, shifted sections, post-v2 central abstraction.
- Synthesis: current thesis, pass movements, surviving claims, unresolved questions, confidence blind spots.
- Trace: load-bearing obligation, enforcement verdict, breaks/gaps/soft spots, v2 update.
- Twin: shared heresy, divergent orthodoxy, hidden lineage, negative space, re-verdict.
- Lift: whether the repo yielded extractables, seed list, extraction difficulty, rankings.

Official synthesis artifacts use `pass_output: pass_id: synthesis` and should be treated as structured compositional prior outputs. Older informal synthesis artifacts with a different root, such as `synthesis_output`, remain useful prose context but should be marked as lacking a standard structured appendix.

Then read the prose around those claims. A schema field is a handle, not the claim itself.

### 2. Build the change map

Inspect the repo changes between baseline and updated references. Do not summarize every file. Build a map organized by analytical relevance:

1. **Spine changes** - changes to the central abstraction, core vocabulary, architecture boundaries, invariants, schemas, protocols, or state machines.
2. **Evidence changes** - changes to files cited by the prior analysis, including the weird file, discounted artifact, traced obligation layers, twin comparison artifacts, and lifted seed locations.
3. **Surface changes** - README, docs, examples, packaging, CLI flags, public APIs, screenshots, marketing, or installation flow.
4. **Verification changes** - tests, fuzzers, CI, linters, release checks, runtime assertions, or operational gates.
5. **History-shape changes** - commits that reveal a change in direction, large rewrites, removals, or consolidation.
6. **Noisy changes** - formatting, dependency bumps, generated files, vendored churn, lockfiles, and mechanical migrations that appear analytically inert.

For each bucket, name the concrete files and commits that matter. If a changed file was central to the prior analysis, inspect it directly. If a changed file looks noisy but touches an analyzed claim, do not dismiss it until you have checked the claim.

### 3. Triage prior claims

For each candidate claim from the prior review package, assign one disposition:

- **unchanged** - the update does not materially affect the claim.
- **strengthened** - new evidence makes the prior claim more defensible.
- **weakened** - new evidence makes the prior claim less defensible but not false.
- **refuted** - new evidence contradicts the claim.
- **superseded** - the claim was once true, but the repo has moved to a different shape.
- **newly-material** - the update introduces a new claim that belongs in the analysis.
- **requires-rerun** - the change is too broad or too identity-level for this pass to update honestly.

Separate **subject drift** from **analysis drift**:

- Subject drift means the repo changed and the prior analysis may need updating.
- Analysis drift means the prior analysis was probably already wrong, and the update merely exposed that fact.

Both are useful, but do not conflate them. If you discover analysis drift, say so directly and explain why it was not caused by the repo update.

### 4. Decide whether incremental review is enough

Most updates should not require a full base rerun. Require a base rerun only when one of these tripwires fires:

- The central abstraction appears replaced rather than modified.
- The traced load-bearing obligation no longer exists or a different obligation now carries the repo.
- The changed files cover most of the prior evidence trail and you cannot inspect them within the available context.
- The repo changed domains, primary audience, runtime model, or public contract.
- The baseline review package is too thin, missing, or prose-only in the exact places the diff touches.
- The update is a broad rewrite whose commit history is itself the main evidence.
- The prior review's weakest blind spot overlaps the changed area and cannot be resolved locally.

If a tripwire fires, do not fake an update. Produce a delta review explaining why incremental review fails and name the smallest base pass or passes that must be rerun.

### 5. Update the analysis

If incremental review is enough, produce a focused update memo. Do not rewrite the whole review. For every changed judgment:

- Quote or paraphrase the prior claim precisely.
- Name the changed evidence.
- State the new disposition.
- Give the replacement judgment if needed.
- Name the pass and section that should be patched.

Also name the claims that remain unchanged when that fact is meaningful. An unchanged central abstraction after a large implementation change is a finding. An unchanged Lift seed after surrounding churn is a finding. An unchanged Trace verdict after added tests may be a strengthened finding rather than a null result.

### 6. Update the structured state

At the end, provide a structured appendix that downstream tools can ingest. It should not try to reproduce every prior pass output. It should identify:

- The baseline and updated references.
- The prior pass outputs consumed.
- The materiality of the repo update.
- The claims whose disposition changed.
- New claims introduced by the update.
- Specific prior pass sections that should be patched.
- Whether any base pass rerun is required.

---

### Output Format

Produce two outputs:

**Part A: Prose Output**

A focused addendum, not a full rewrite.

Use this structure:

**A. Baseline and Inputs**
Name the baseline and updated references. List which prior passes were available and whether structured appendices were present.

**B. Change Map**
Summarize the analytically relevant changes using the six buckets above. Do not catalog inert files.

**C. Claim Triage**
List the prior claims that matter to this update and give each disposition. Be specific about whether a movement is subject drift or analysis drift.

**D. Required Revisions**
For each prior pass section that should change, give the replacement judgment or patch note. If nothing should change, say so and explain why the changed code does not touch the prior analysis.

**E. Updated Verdict**
State whether the repo is now more interesting, less interesting, or unchanged relative to the baseline review; whether its taste is more distinctive, less distinctive, or unchanged; and whether its central abstraction is stronger, weaker, replaced, or unchanged.

**F. Rerun Recommendation**
State whether incremental review is sufficient. If not, name the smallest base pass or passes that must be rerun and why.

**Part B: Structured Appendix**

After the prose, append a YAML block in this exact shape:

```yaml
pass_output:
  pass_id: delta-review
  repo: <identifier or URL>
  analyzed_at: <ISO 8601 timestamp>
  baseline_source_state:
    ref: <string>
    ref_kind: <commit | tag | archive | date | pasted-files | unknown>
    dirty: <true | false | unknown>
  updated_source_state:
    ref: <string>
    ref_kind: <commit | tag | archive | date | pasted-files | unknown>
    dirty: <true | false | unknown>
  prior_passes_consumed:
    - pass_id: <first-read | discounted-artifact | synthesis | trace | twin | lift | other>
      artifact: <file path, URL, pasted text label, or null>
      prose_present: <true | false>
      structured_appendix_present: <true | false>
  change_window:
    diff_basis: <git-diff | commit-range | archive-comparison | file-list | unknown>
    commit_count: <integer or null>
    changed_files_count: <integer or null>
    analytically_relevant_files:
      - <file path>
  materiality: <none | small | medium | large | reanalysis-required>
  incremental_review_sufficient: <true | false>
  rerun_required:
    required: <true | false>
    passes:
      - <first-read | discounted-artifact | trace | twin | lift>
    reason: |
      <one paragraph, or null if no rerun is required>
  claim_updates:
    - id: <stable short slug>
      prior_source:
        pass_id: <pass id>
        section: <section name or structured field>
      prior_claim: |
        <claim as originally understood>
      disposition: <unchanged | strengthened | weakened | refuted | superseded | newly-material | requires-rerun>
      drift_kind: <subject-drift | analysis-drift | no-drift | mixed>
      changed_evidence:
        - location: <file path, commit, or diff hunk description>
          summary: <one sentence>
      replacement_judgment: |
        <new judgment, or null if unchanged>
      patch_prior_analysis: <true | false>
  new_claims:
    - id: <stable short slug>
      belongs_after_pass: <first-read | discounted-artifact | synthesis | trace | twin | lift | delta-review>
      statement: |
        <new claim introduced by the update>
      evidence:
        - <file path, commit, or diff hunk description>
  section_patches:
    - pass_id: <first-read | discounted-artifact | synthesis | trace | twin | lift | delta-review>
      section: <section name>
      direction: <sharper | softer | redirected | refuted | appended | unchanged>
      patch_note: |
        <specific instruction for updating that section>
  updated_verdict:
    repo_more_or_less_interesting: <more | less | unchanged | unclear>
    taste_more_or_less_distinctive: <more | less | unchanged | unclear>
    central_abstraction_status: <stronger | weaker | replaced | unchanged | unclear>
    one_sentence: <overall update verdict>
  confidence:
    overall: <high | medium | low>
    blind_spots: |
      <one paragraph>
```

---

### A note on tone

The failure mode of incremental review is false thrift: saving tokens by preserving a judgment that no longer deserves to stand. The opposite failure mode is false drama: treating every changed file as a philosophical event. Avoid both.

The right posture is forensic and economical. The old review earned its claims once. Your job is to determine which claims still earn themselves after the repo moved.
