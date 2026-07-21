---
pass_id: lift
name: The Lift
version: 7
prerequisites:
  - first-read
  - discounted-artifact
  - trace
recommended_prerequisites:
  - twin
output_kind: prose-with-yaml-appendix
terminates_early_when: repo-yields-no-extractables
intended_audience:
  - human-curator
  - downstream-extraction-tools
  - builders-considering-extraction
---

# The Lift
*A fifth-pass prompt for identifying extractable seeds within a repo*

---

## Why this is a separate document

The first four passes analyze the repo to understand it. They produce *diagnostic* output — the codebase's working theory, central abstraction, enforceability, and how the repo measures against an adjacent neighbor.

This pass does something different. It identifies components, patterns, or workflows that could be reused outside the repo. The shift in attention is significant: diagnostic reading looks for what makes the system *itself*, while extractive reading looks for what remains useful outside the system. These are not opposed activities, but they are not the same one. Conflating them produces both bad diagnoses (the analyzer notices only what's portable) and bad extractions (the analyzer pulls out things that only work in their original home).

This pass is for after diagnostic work is complete. It assumes you already know what the repo *is*. Now you ask: what could become a standalone artifact.

---

## When to run this

After The First Read, The Discounted Artifact, and The Trace are complete. If The Twin has also been performed, even better — comparison-derived patterns are sometimes the most extractable seeds because the twin pass already proved they generalize across at least one other repo.

Do not run this prompt before The Trace. Pre-trace extraction tends to identify candidates that turn out to be aesthetic — patterns the analyzer admired in the README that don't actually appear in the running code. The trace filters those out. Running this pass after the trace means the candidates you identify have already been checked against implementation and enforcement.

---

## How to use this document

Paste the prompt below into the same Claude chat after The Trace (and ideally The Twin) is complete.

---

## The Prompt

You have produced a complete diagnostic analysis of this repo. Now do something different: identify what is extractable.

An extractable candidate is a small part of the repo that could become useful outside it with modest reshaping. Not "could be reused with effort" — something that, with modest reshaping, could live as its own artifact: a library, a CLI, a checker, a pattern writeup, a single-file utility, a GitHub Action, a teaching example, a domain primitive.

The discipline is standalone utility: the candidate should do real work, remain understandable, and have a specific user without requiring the parent repo. A candidate that requires the rest of the repo to be intelligible is not extractable. A candidate that loses its point when removed from its original context is not extractable. A candidate that is technically liftable but uninteresting on its own is not extractable.

### 1. Does this repo yield extractables at all?

Before listing seeds, answer this honestly.

Some repos are extraction-rich. They are deliberately modular, or they accumulated good utilities over time, or they solve general problems with general code. Their components or patterns can be separated cleanly.

Other repos are extraction-poor. They are tightly integrated by design, deeply domain-specific, exploratory or research-oriented, or built around an idea that loses its point when fragmented. Their value is in the whole, not the parts. Trying to extract from them produces wishlist candidates that are not meaningfully separable.

If the repo is extraction-poor, say so plainly. Produce instead a one-paragraph statement of *why* extraction fails for this repo — what about its construction makes its value non-fragmentable. That is a real finding about the repo's character. The pass ends here.

If the repo yields real extractables, continue.

### Coverage Closure (required — do this before identifying extractable candidates)

Before identifying extractable candidates, close one open thread the prior passes
left behind. This step is **required**, and it is **separate from the extraction
work** below — do not fold it into the extraction analysis or skip it because the candidates
feel more useful.

Open the previously named blind spot **most likely to change the current
thesis** about what this repo yields. Not any prior blind spot, and not the
easiest one to open — the single one whose resolution is most likely to move the
judgment you are carrying into this pass. (The `smallest_open` carried forward
from the earlier passes is the obvious first candidate.)

State, explicitly:

- **Which prior blind spot you chose** — name the pass it came from and the file path.
- **Why that blind spot was the most thesis-threatening** — why it, above the others, was most likely to change the current thesis.
- **What you found** when you actually opened it.
- **Whether the finding changes any prior judgment**, and if so, how.

Record this in the `coverage_closure` block of the structured appendix. Then
identify the candidates.

### 2. Identify the extractable candidates

Identify between 1 and 5 extractable candidates. Prefer fewer, better-supported candidates over a larger list. A repo with one strong extractable candidate is more useful than a repo with several weak candidates.

A candidate may be:

- A single file or module
- A function, trait, or type with surrounding scaffolding
- A test harness or fuzzing rig
- A CLI workflow or script chain
- A schema, config pattern, or DSL fragment
- A small domain-specific checker or linter rule
- A reusable safety, retry, or invariant primitive
- A design pattern that could become a standalone article
- *A combination* — sometimes the candidate is not one piece but the way three small pieces interact. The pattern emerges from the interaction, not the components. Allow for this.

For each candidate, produce the structured entry below.

### 3. Per-candidate structure

**Name.** Standalone, descriptive, not borrowing the parent repo's vocabulary unless the vocabulary is itself extractable.

**Source location.** Exact file paths, function names, line ranges where useful. The reader should be able to find it without searching.

**What it does.** One paragraph in plain language. Assume the reader has not read the parent repo.

**Why it works standalone.** This is the load-bearing question. Address all three:
- *Boundaries.* What does the candidate depend on, and what dependencies are essential vs incidental?
- *Stubs.* What would need to be replaced or stubbed out to make it standalone?
- *Loss.* What changes when removed from its original context: meaning, dependencies, performance, scope, trust model, or something else?

**Standalone form.** What it could become. Be specific: not "a library" but "a Rust crate exposing X with Y interface." Not "a CLI" but "a `<name> <verb> <noun>` invocation that does Z."

**First MVP.** This deserves its own thinking, not a checkbox. What is the smallest version of this candidate that does *real work*? Not the smallest version that compiles — the smallest version that, on its own, would be useful enough that someone might install or read it. If you cannot articulate a useful MVP smaller than the full candidate, the candidate may not be as portable as it looks.

**Why it's worth extracting.** Discipline check. Name a specific class of user, a specific problem they have, and why this candidate addresses that problem better than available alternatives. If you cannot pass this test, the candidate is liftable but not worth lifting.

**Topic tags.** Which topic or domain tags apply if extracted? Multi-tag is acceptable. No-tag is suspicious — it usually means the candidate is too generic to be interesting or too specific to be portable. Sharpen or cut.

**Extraction difficulty.** Easy, medium, or hard, with one sentence justifying the rating.

### 4. Ranking

After all candidates are described, produce a short ranked list along these dimensions:

1. **Best immediate extraction** — could be lifted this week with little reshaping.
2. **Most unexpected viable extraction** — the candidate that surprises by being extractable, or whose standalone form is unexpected.
3. **Most product-relevant extraction** — the candidate with the clearest user, problem, and product context.
4. **Best educational extraction** — the candidate that teaches something general by being a worked example of it.
5. **Best design-pattern writeup** — the candidate whose value is in the *pattern*, not the code, and which would travel best as an article.

A single candidate may rank on multiple dimensions. A dimension may have no candidate worth ranking — say so rather than padding.

---

### Output Format

Produce two outputs:

**Part A: Prose Output**

A short prose preamble naming the extraction-yield finding, followed by per-candidate prose entries using the structure in section 3, followed by the ranking in section 4. Be opinionated; do not catalog.

**Part B: Structured Appendix**

After the prose, append a YAML block in this exact shape:

Use `source_state` to identify the exact source state analyzed. Put repo-relative
paths only in `source_paths`; use `source_notes` for symbols, headings, line
hints, or other non-path context.

<!-- repo-review:pass_output -->
```yaml
pass_output:
  pass_id: lift
  template_version: 7
  repo: <identifier or URL>
  analyzed_at: <ISO 8601 timestamp>
  source_state:
    ref: <string>
    ref_kind: <commit | tag | archive | date | pasted-files | unknown>
    dirty: <true | false | unknown>
  coverage_closure:
    chosen_from_pass: <first-read | discounted-artifact | synthesis | trace | twin>
    path: <repo-relative path>
    why_this_was_most_thesis_threatening: <one sentence>
    finding: <one short paragraph>
    changed_prior_judgment: <true | false>
    shift_summary: <short | null>
  yields_extractables: <true | false>
  early_termination_reason: |
    <required only if yields_extractables is false; otherwise null>
  seeds:
    - id: <short slug>
      name: <standalone name>
      source_paths:
        - <file path>
      source_notes: |
        <function names, symbols, headings, line hints, or context>
      what_it_does: |
        <paragraph>
      survives_because:
        boundaries: |
          <one paragraph on dependencies>
        stubs: |
          <what needs replacing>
        loss: |
          <what changes on extraction>
      standalone_form: |
        <specific artifact form>
      first_mvp: |
        <smallest version doing real work>
      worth_extracting_because: |
        <specific user, specific problem, specific advantage>
      topic_tags: [<tag>, <tag>, ...]
      extraction_difficulty: <easy | medium | hard>
      difficulty_justification: <one sentence>
  ranking:
    immediate: <seed id or "none">
    weird: <seed id or "none">
    commercial: <seed id or "none">
    educational: <seed id or "none">
    design_pattern: <seed id or "none">
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

If you have been given the repo-review Output Style Guide, follow it. It is standing prose guidance, not an extra analytical pass.

Extractive reading invites a particular failure: cataloging. The analyzer, faced with a request for a list of candidates, may produce an overlong inventory instead of a small set of defended candidates. Resist this.

A real extraction pass is *opinionated*. It says: *this thing is worth lifting, this other thing isn't, here is why*. It may omit candidates that are technically reusable but not worth extracting. It is willing to identify a single candidate and stop, if that candidate is the only one that passes the standalone-utility test.

The audience is a builder considering what to actually extract. They are not served by a list. They are served by a small number of well-defended candidates and an honest accounting of which are worth their time.

If the repo yields one strong candidate and nothing else, that is the best possible output. Produce it and stop.
