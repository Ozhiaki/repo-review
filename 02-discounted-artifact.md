---
pass_id: discounted-artifact
name: The Discounted Artifact
version: 7
prerequisites:
  - first-read
output_kind: prose-with-yaml-appendix
terminates_early_when: never
intended_audience:
  - human-curator
  - downstream-analysis-passes
  - downstream-extraction-tools
---

# The Discounted Artifact
*A second-pass prompt for Claude, to be issued only after The First Read is complete*

---

## Why this is a separate document

The First Read captures the analyzer's first-pass thesis. This pass catches a specific failure of first-pass coverage: under-reading an artifact that later proves important to the analysis.

When a repo contains one document or component that is much larger, much more formal, or much more abstract than its neighbors, the first-pass analyzer can under-read it. The larger, more formal, or less familiar the artifact, the more likely it gets filed under "honorable mention," "ambitious," "aspirational," or "compresses the project into formal axioms." Treat this as a predictable coverage failure, not as a diligence failure. The largest formal artifact resists coverage reading because it requires depth, so the analyzer satisfies the section requirement with a one-line gesture and moves on. The template rewards this: every section gets filled, the analysis looks complete, while the artifact's actual role remains untested.

The failure is not random. It is a *predictable consequence* of the first-pass instructions. Which means it can be corrected — but only by a second pass that knows what it is correcting.

The second pass should be separate from the first so the first-pass thesis remains available for comparison. If this pass were appended to the first-pass template, the analyzer would behave differently throughout the original sections: it would search harder for "the artifact I'm probably discounting" while doing the original reading, hedge its judgments to leave room for revision, and produce an analysis pre-shaped to anticipate the correction. The diagnostic value would collapse. We want the first pass performed under normal first-pass coverage constraints.

Two things follow from this:

1. **The First Read must run in full before this pass is shown to the analyzer.** Producing v1 is the precondition for v2 having any value.
2. **The comparison between v1 and v2 is part of the finding.** The difference identifies which evidence the first pass missed and how much that miss changed the analysis.

---

## How to use this document

Paste the prompt below into the same Claude chat after the v1 analysis is complete. Do not paste it earlier.

If conversation context has been lost, start a new chat with v1 attached and paste this pass as the first message.

---

## The Prompt

You have produced a complete repo analysis using The First Read template. Now do one more thing.

### 1. The Artifact You Discounted

Identify the single artifact whose under-reading would most change the first-pass analysis if it proved important.

Candidate signals include:

- The longest document
- The most abstract document
- The one with the most inbound references from other files
- The one you described as "ambitious," "aspirational," "compresses the project into formal axioms," or filed under "honorable mention"
- The one you mentioned in passing without inspecting

Sometimes the candidate is not a document at all. It might be:

- A configuration file that turns out to encode a DSL
- A test suite that specifies the system more completely than the source
- A schema or type definition that the implementation only partially enforces
- A comment thread that records design rationale
- A vendored or copied component that changes the dependency story
- A `.md` file in an unusual location, like `docs/` rather than the root, that does heavier conceptual work than the README
- A migration history, changelog, or commit history that records important design changes

The common pattern: structurally prominent or thesis-threatening, but not closely inspected in the first pass.

If multiple artifacts qualify, pick the one whose under-reading would most damage the v1 analysis if it turns out to be load-bearing. Read it closely now. Record the specific evidence that was missed.

### 2. Update v1

Then revise any earlier section of the v1 analysis whose judgment changes as a result. Produce a revised full analysis. Preserve the section structure, but make each changed judgment explicit.

At the top of v2, include a short note (3 to 5 sentences) addressing:

- What the discounted artifact actually contained that v1 missed
- Which v1 sections changed, and in which direction (confirmed, narrowed, broadened, redirected, or refuted)
- Why this artifact was easy to under-read on first pass: location, format, size, naming, generated appearance, or apparent relation to already-read files

The third item is the most important. It is also the one analyzers most often skip. Do not skip it. The reason an artifact was easy to miss is useful evidence about repo organization, naming, generated-file conventions, or documentation structure. Sometimes the answer is "the artifact looks aspirational because the README treats it as aspirational." Sometimes it is "the artifact is in an unusual file format that the analyzer pattern-matched as configuration." Sometimes it is "the artifact is so large that reading it felt expensive, and the section requirement could be met without it." Record that reason concretely.

### 3. The Null Result Path

If, after honest re-reading, no v1 section's judgment shifts, say so plainly. But before you do, apply this discipline:

- Did you actually re-read the artifact, or did you re-skim it?
- Did you re-read it with the question "what would change about v1 if this artifact were central?"
- If nothing changes, what evidence did the close reading actually check?

Null results are legitimate but rare. The failure mode this section exists to catch is under-reading an artifact whose role matters to the thesis. If you produce a null result, explain the artifact's contents, why it was plausible to under-read it, and why close reading did not change any judgment.

A real null result includes: the name of the artifact, what it actually contains, why first-pass coverage reading would normally under-read it, and the specific reason that under-reading did not damage v1 in this case. "I checked and v1 was fine" is not a null result.

---

### Output Format

Produce two outputs:

**Part A: Prose Output**

Produce a revised full analysis using the same section headings. Rewrite sections whose judgment changed. For unchanged sections, summarize that they are unchanged rather than preserving weak prose verbatim.

At the top of v2, before any other content:

**Revision Note** *(3 to 5 sentences)*
- What v1 missed
- Which v1 sections shifted and how
- Why the missed artifact was easy to under-read on first pass

Within the v2 body, mark the corrections explicitly. The audience benefits from seeing where v1 and v2 diverged.

Use this convention:

- For sections that changed: include a one-line marker at the start of the section, like *`[update: narrowed — original claim was X, revised claim is Y]`*
- For unchanged sections: no marker needed
- For sections that were refuted entirely: keep the section heading, replace the content, and mark *`[update: refuted — original claim was X]`*

After the v2 analysis, append:

**Change Summary**
A short paragraph (3 to 5 sentences) explaining what changed from v1 to the revised analysis, why it changed, and what uncertainty remains.

**Part B: Structured Appendix**

After the prose, append a YAML block in this exact shape:

Use `source_state` to identify the exact source state analyzed. If you cannot
identify it, write `unknown` rather than inferring it from `analyzed_at`.

<!-- repo-review:pass_output -->
```yaml
pass_output:
  pass_id: discounted-artifact
  template_version: 7
  repo: <identifier or URL>
  analyzed_at: <ISO 8601 timestamp>
  source_state:
    ref: <string>
    ref_kind: <commit | tag | archive | date | pasted-files | unknown>
    dirty: <true | false | unknown>
  discounted_artifact:
    path: <file path>
    type: <document | config | test-suite | schema | comment-thread | vendored-dep | migration-history | other>
    why_under_read: |
      <one paragraph naming the concrete signals that made this artifact easy to under-read: file name, location, size, format, generated appearance, duplication of already-read data, or lack of references>
  delta_size: <none | small | medium | large>
  shifted_sections:
    - section: <section name from v1, e.g. "central-abstraction">
      direction: <sharper | softer | redirected | refuted>
      one_line_summary: <short>
    - section: ...
      direction: ...
      one_line_summary: ...
  null_result: <true | false>
  null_result_justification: |
    <required only if null_result is true; otherwise null>
  central_abstraction_post_v2:
    name: <one short phrase>
    paths:
      - <file path>
    changed_from_v1: <true | false>
  topic_tags: [<tag>, <tag>, ...]
  confidence:
    overall: <high | medium | low>
    blind_spots: |
      <short paragraph>
    smallest_open:
      path: <repo-relative path>
      why_this_open: <one sentence>
      opened_this_pass: <true | false>
```

---

### A note on tone

The revised analysis should make the changed judgments visible. The audience — both the human curator and any downstream consumer of this analysis — benefits from seeing where a careful reader's first impression diverged from their second.

If v1 was wrong, state the corrected claim and the evidence that changed it.

If v1 was right, explain what close reading confirmed and why first-pass coverage was sufficient in this case.

The discipline here is the same discipline The First Read demanded: tell the truth as you see it, mark where your sight is weak, and leave the next reader clear claims, evidence, and named uncertainties to test.
