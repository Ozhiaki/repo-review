---
pass_id: discounted-artifact
name: The Discounted Artifact
version: 4
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

The First Read catches the analyzer's first impression. This pass catches a specific failure of that first impression: **the central artifact discount.**

When a repo contains one document or component that is much larger, much more formal, or much more abstract than its neighbors, the first-pass analyzer reliably under-reads it. The bigger and stranger the artifact, the more likely it gets filed under "honorable mention," "ambitious," "aspirational," or "compresses the project into formal axioms." This is not laziness. It is a structural property of how coverage-oriented reading works. The largest formal artifact resists coverage reading because it requires depth, so the analyzer satisfies the section requirement with a one-line gesture and moves on. The template rewards this: every section gets filled, the analysis looks complete, and the spine never gets read.

The failure is not random. It is a *predictable consequence* of the first-pass instructions. Which means it can be corrected — but only by a second pass that knows what it is correcting.

The correction must be temporally separated from the First Read. If this pass were appended to the first-pass template, the analyzer would behave differently throughout the original sections: it would search harder for "the artifact I'm probably discounting" while doing the original reading, hedge its judgments to leave room for revision, and produce an analysis pre-shaped to anticipate the correction. The diagnostic value would collapse. We want the first pass performed with the same blindness a real reader brings.

Two things follow from this:

1. **The First Read must run in full before this pass is shown to the analyzer.** Producing v1 is the precondition for v2 having any value.
2. **The delta between v1 and v2 is itself the finding.** Not just the corrected analysis. The *gap* between first read and second read tells you what is hard to see on first read for *this kind of repo*. That gap is often more interesting than either version of the analysis alone.

---

## How to use this document

Paste the prompt below into the same Claude chat after the v1 analysis is complete. Do not paste it earlier.

If conversation context has been lost, start a new chat with v1 attached and paste this pass as the first message.

---

## The Prompt

You have produced a complete repo analysis using The First Read template. Now do one more thing.

### 1. The Artifact You Discounted

Identify the single artifact in this repo that you gave the least attention relative to its size, formality, or structural prominence.

The usual suspects:

- The longest document
- The most abstract document
- The one with the most inbound references from other files
- The one you described as "ambitious," "aspirational," "compresses the project into formal axioms," or filed under "honorable mention"
- The one you mentioned in passing without inspecting

Sometimes the candidate is not a document at all. It might be:

- A configuration file that turns out to encode a DSL
- A test suite that specifies the system more completely than the source
- A schema or type definition that the implementation only partially enforces
- A comment thread that turns out to be the design rationale
- A vendored dependency the author rewrote rather than imported
- A `.md` file in an unusual location, like `docs/` rather than the root, that does heavier conceptual work than the README
- A migration history, changelog, or commit narrative that captures what no document captures

The common signature: prominent by some structural measure, but quietly under-read on the first pass.

If multiple artifacts qualify, pick the one whose under-reading would most damage the v1 analysis if it turns out to be load-bearing. Read it now, properly. Take the time you didn't take the first time.

### 2. Update v1

Then revise any earlier section of the v1 analysis whose judgment changes as a result. Produce a v2 of the full analysis, not a patch.

At the top of v2, include a short note (3 to 5 sentences) addressing:

- What the discounted artifact actually contained that v1 missed
- Which v1 sections shifted, and in which direction (sharper, softer, redirected, refuted)
- Why this artifact was discountable on first read — what about its surface invited the under-reading

The third item is the most important. It is also the one analyzers most often skip. Do not skip it. The texture of why an artifact reads as ignorable is itself diagnostic information about the repo. Sometimes the answer is "the artifact looks aspirational because the README treats it as aspirational." Sometimes it is "the artifact is in an unusual file format that the analyzer pattern-matched as configuration." Sometimes it is "the artifact is so large that reading it felt expensive, and the section requirement could be met without it." Each of these is a finding.

### 3. The Null Result Path

If, after honest re-reading, no v1 section's judgment shifts, say so plainly. But before you do, apply this discipline:

- Did you actually re-read the artifact, or did you re-skim it?
- Did you re-read it with the question "what would change about v1 if this were the spine?" or with the question "did v1 already cover this?"
- The first question is the discipline. The second is the dodge.

Null results are legitimate but rare. The failure mode this section exists to catch is the structural one — and structural failure modes are operative until proven otherwise. If you produce a null result, the proof is on you, not on the prompt.

A real null result includes: the name of the artifact, what it actually contains, why first-pass coverage reading would normally under-read it, and the specific reason that under-reading did not damage v1 in this case. "I checked and v1 was fine" is not a null result. It is a re-skim.

---

### Output Format

Produce two outputs:

**Part A: Prose Output**

Produce a v2 of the full analysis, with all sections from The First Read rewritten where they shifted and preserved verbatim where they did not.

At the top of v2, before any other content:

**Revision Note** *(3 to 5 sentences)*
- What v1 missed
- Which v1 sections shifted and how
- Why the missed artifact read as ignorable on first pass

Within the v2 body, mark the corrections explicitly. The audience benefits from seeing where v1 and v2 diverged.

Use this convention:

- For sections that shifted: include a one-line marker at the start of the section, like *`[v2: shifted — was X, now Y]`*
- For sections preserved verbatim: no marker needed
- For sections that were refuted entirely: keep the section heading, replace the content, and mark *`[v2: refuted v1 — original claim was X]`*

After the v2 analysis, append:

**Delta Summary**
A short paragraph (3 to 5 sentences) reflecting on the gap between v1 and v2 as a *standalone finding*. What does the size and shape of the delta tell you about this repo, this analyzer, or this kind of artifact? A small delta on a careful first pass is informative. A large delta on a thorough first pass is more informative. A large delta that points to the same conclusion v1 reached by a different path is the most informative case.

**Part B: Structured Appendix**

After the prose, append a YAML block in this exact shape:

Use `source_state` to identify the exact source state analyzed. If you cannot
identify it, write `unknown` rather than inferring it from `analyzed_at`.

```yaml
pass_output:
  pass_id: discounted-artifact
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
      <one paragraph: the structural reason the first pass under-read this>
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

The v2 analysis should not pretend v1 didn't happen. The corrections are part of the artifact. Mark them. The audience — both the human curator and any downstream consumer of this analysis — benefits from seeing where a careful reader's first impression diverged from their second.

If v1 was wrong, say it was wrong. Do not soften the diagnosis. The series gains nothing from a v2 that flatters v1's errors.

If v1 was right, say it was right *and explain why first-pass coverage reading happened to land correctly this time*. Lucky correctness is different from earned correctness. The distinction matters for what later passes should expect.

The discipline here is the same discipline The First Read demanded: tell the truth as you see it, mark where your sight is weak, and leave the next reader something to push against.
