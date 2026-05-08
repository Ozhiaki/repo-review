---
pass_id: trace
name: The Trace
version: 2
prerequisites:
  - first-read
  - discounted-artifact
output_kind: prose-with-yaml-appendix
terminates_early_when: repo-has-no-load-bearing-obligation
intended_audience:
  - human-curator
  - downstream-analysis-passes
  - downstream-extraction-tools
---

# The Trace
*A third-pass prompt for Claude, to be issued only after The First Read and The Discounted Artifact are complete*

---

## Why this is a separate document

The First Read and The Discounted Artifact catch failures of *attention*. The First Read catches the analyzer's first impression. The Discounted Artifact catches the central artifact discount — the tendency to under-read the largest, strangest formal artifact in the repo.

This pass catches a failure of *credit*. Once the spine has been correctly identified, the next failure mode arrives: admiring the spine without checking whether it bears any weight. A repo can have a brilliant theory, an elegant vocabulary, a careful architecture doctrine, an ambitious invariant set — and still fail to connect any of it to executable enforcement. The aesthetic is real. The machinery is somewhere else, or nowhere.

The correction is to pick one obligation the repo treats as central and trace it from its most abstract statement to the place in the running code where it either holds or doesn't.

This must be separate from the prior passes. If the analyzer knows a trace is coming, it will bias the earlier passes toward claims that are easy to follow through code. The "central abstraction" gets selected for traceability instead of for centrality. That corrupts the diagnostic value of every prior pass.

So: complete The First Read. Then complete The Discounted Artifact. Only after the v2 analysis exists should you run this pass.

---

## How to use this document

Paste the prompt below into the same Claude chat after the v2 analysis is complete. If the conversation context has been lost, start a new chat with the v1 and v2 analyses attached, plus enough repo context to inspect files.

---

## The Prompt

You have produced a complete repo analysis through v2. Now do one final pass.

### 1. Does this repo even have a load-bearing obligation?

Before tracing anything, answer this honestly.

Some repos are organized around a central claim the author cares about deeply — an invariant, a doctrine, a safety property, a behavioral guarantee. Those repos reward a trace.

Other repos are not organized that way. They are collections, accumulations, utilities, scripts, demos, sketches, pedagogical artifacts, or working notebooks. Their interest is not philosophical. They have taste, but the taste is in selection, composition, or craft — not in any single load-bearing claim that machinery must enforce.

If the repo has no load-bearing obligation, say so plainly and stop. Produce instead a one-paragraph statement of what the repo's interest *actually* is, since it is not philosophical enforcement. The series ends here for this repo. That is a real finding, not a failure.

If the repo has a load-bearing obligation, continue.

### 2. Choose the obligation

Pick one claim that appears genuinely load-bearing after the v2 analysis. It should be a claim the repo seems to care about deeply: an invariant, law, safety property, architectural doctrine, protocol rule, behavioral guarantee, central promise, or domain commitment.

**Do not pick the easiest claim to trace. Pick the claim whose truth matters most to the repo's identity.**

The right claim often resists tracing on first attempt. That resistance is a feature, not a reason to choose differently.

### 3. Trace the obligation through six layers

For each layer, identify concrete files and explain what the layer contributes.

1. **Abstract Statement** — Where is the obligation stated most abstractly? This may be a theory document, RFC, architecture note, root instruction, design doctrine, or manifesto-like artifact. Quote the strongest single sentence verbatim, with file path.

2. **Normative Encoding** — Where does the repo turn the abstract statement into a named obligation? Look for behavior IDs, requirements, schemas, policy entries, gate definitions, protocol fields, stable IDs, machine-readable contracts, type signatures, or domain vocabularies that name the obligation as a thing the system is responsible for.

3. **Implementation** — Where does executable code attempt to enforce the obligation? Identify specific modules, functions, state machines, traits, or data structures.

4. **Verification** — Where is the obligation tested, fuzzed, property-checked, linted, reviewed, or otherwise verified? Include both direct tests and indirect gates.

5. **Operational Enforcement** — Where does this obligation affect runtime behavior, developer workflow, CI, release, admission, merge, deployment, or incident handling?

6. **Breaks, Gaps, and Soft Spots** — Where does the trace weaken? Look for stringly-typed checks, missing tests, aspirational docs, unimplemented policy, manual process, unverified assumptions, TODOs, weak threat-model coverage, or code that enforces a narrower property than the abstract claim.

### 4. Render a verdict

Answer these directly:

- **Enforcement quality.** Is the obligation enforced, partially enforced, aspirational, or incoherent?
- **Same claim or substitute?** Does the implementation enforce the same claim the abstract layer makes, or a weaker substitute that the author has not noticed is weaker?
- **Wise incompleteness or abandoned ambition?** If the obligation is partially fulfilled, is the gap *deferred* (the author knows, has reasons, would close it under the right conditions) or *abandoned* (the author wrote it, moved on, and the prose now overstates the system)? A deferred gap with a credible reason is a sign of taste, not failure. An abandoned gap is the central finding.
- **What the trace reveals about taste.** What does this trace expose about the author's actual judgment that the v1 and v2 readings did not?

### 5. Update v2

This is required. The trace is not a commentary on v2 — it is a revision of v2.

- **Restate the central abstraction in light of the trace.** If the trace confirms v2's choice, say so explicitly. If the trace shifts it, write the replacement central abstraction in full.
- **Identify any v2 section whose judgment changes.** Name the section. State the change in one sentence per section. Sharper, softer, redirected, refuted.
- **If nothing changes, say so plainly** — but apply the same discipline The Discounted Artifact demands: did the trace actually run, or did you re-skim the abstract layer and call it a trace?

---

### Output Format

Produce two outputs:

**Part A: Prose Output**

A focused addendum, not a full rewrite of v2.

Use this structure:

**A. Load-Bearing Check**
Either: "This repo has a load-bearing obligation. Proceeding." Or: "This repo has no load-bearing obligation. Its interest is [X]." If the second, stop here.

**B. Obligation Chosen**
Name the obligation in one sentence. Explain why you chose it over nearby candidates, and which candidate you considered and rejected.

**C. Trace**
Walk the obligation through the six layers. Use concrete file paths and names. Be specific. The trace is the document.

**D. Verdict**
Answer all four verdict questions directly. Do not hedge. The trace earns the right to a clear judgment.

**E. v2 Update**
State the post-trace central abstraction (confirmed or replaced). List the v2 sections whose judgments shifted, with the direction of each shift.

**F. Evidence Trail**
- One-sentence statement of the verdict.
- One-sentence statement of the obligation.
- The verbatim quote from Layer 1, with location.

**Part B: Structured Appendix**

After the prose, append a YAML block in this exact shape:

```yaml
pass_output:
  pass_id: trace
  repo: <identifier or URL>
  analyzed_at: <ISO 8601 timestamp>
  load_bearing: <true | false>
  early_termination_reason: |
    <required only if load_bearing is false; otherwise null>
  obligation:
    statement: <one sentence>
    abstract_quote: <verbatim>
    abstract_quote_location: <file path>
    rejected_candidates:
      - <candidate one-liner>
      - <candidate one-liner>
  trace_layers:
    abstract_statement: <file path or paths>
    normative_encoding: <file path or paths>
    implementation: <file path or paths>
    verification: <file path or paths>
    operational_enforcement: <file path or paths>
    breaks_gaps_soft_spots: |
      <one paragraph naming the weakest layer and why>
  verdict:
    enforcement_quality: <enforced | partially-enforced | aspirational | incoherent>
    same_claim_or_substitute: <same | substitute>
    gap_character: <none | deferred | abandoned | not-applicable>
    one_sentence: <verdict in one sentence>
  v2_update:
    central_abstraction_changed: <true | false>
    new_central_abstraction: <one short phrase or null>
    sections_shifted:
      - section: <name from v2>
        direction: <sharper | softer | redirected | refuted>
  topic_tags: [<tag>, <tag>, ...]
  confidence:
    overall: <high | medium | low>
    blind_spots: |
      <one paragraph>
```

---

### Selection Guidance

Good obligation candidates take many shapes depending on the repo's domain. A few examples by category:

*Systems / distributed / safety:*
- "No authoritative transition without a gate receipt."
- "Default-deny authority."
- "Effects are idempotent under crash/retry."
- "Ledger is the source of truth."
- "Terminal states absorb all future inputs."

*Libraries / APIs:*
- "The library is unsurprising to someone fluent in the underlying domain."
- "Misuse is hard. Correct use is the path of least resistance."
- "Errors carry enough context to be acted on at the call site."

*DSLs / languages / tools:*
- "The DSL reads more like the domain than like code."
- "The tool fails in ways its user can recover from without reading source."
- "The grammar admits no construction whose meaning the author cannot explain."

*Protocols / formats:*
- "Boundary traffic is typed and canonicalized."
- "Old clients and new servers must interoperate without coordination."

*Pedagogical / reference:*
- "Every example is the smallest example that makes the point."
- "The reader can rebuild the system from the document alone."

These are illustrative, not exhaustive. The right obligation for any given repo is specific to that repo. A claim that does not appear on any list above can still be the right one.

Bad candidates, regardless of category:
- Claims too small to reveal the repo's worldview.
- Claims that are local bug fixes or implementation details.
- Claims with no abstract layer to trace from.
- Claims selected only because they are easy to grep.
- Claims that flatter the analyzer's prior reading by being trivially confirmed.

---

### A note on tone

The trace is high-stakes. Keep your voice.

Earlier passes establish what the analyzer thinks. The trace tests whether the repo earns it. A hedged voice in this pass wastes the test — every "perhaps" and "arguably" lets the analyzer dodge the verdict the trace was built to force.

Be opinionated. Make the opinion earn itself through the trace. The highest-value outcome is not "the repo is good" or "the repo is bad." The highest-value outcome is a precise, defensible answer to:

> Does the discovered spine actually reach the bones?
