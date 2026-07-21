---
pass_id: trace
name: The Trace
version: 7
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

The First Read and The Discounted Artifact test limitations of first-pass coverage. The First Read captures the analyzer's first-pass thesis. The Discounted Artifact catches the tendency to under-read an artifact whose role later proves important to the analysis.

This pass checks whether a central claim is enforced by executable code, tests, workflow, or release process. A repo can have a strong theory, a careful vocabulary, or an ambitious invariant set and still fail to connect it to enforcement.

The correction is to pick one obligation the repo treats as central and trace it from its most abstract statement to the place in the running code where it either holds or doesn't.

This must be separate from the prior passes. If the analyzer knows a trace is coming, it will bias the earlier passes toward claims that are easy to follow through code. The "central abstraction" gets selected for traceability instead of for centrality. That corrupts the diagnostic value of every prior pass.

So: complete The First Read. Then complete The Discounted Artifact. Only after the v2 analysis exists should you run this pass.

---

## How to use this document

Paste the prompt below into the same Claude chat after the v2 analysis is complete. If the conversation context has been lost, start a new chat with the v1 and v2 analyses attached, plus enough repo context to inspect files.

---

## The Prompt

You have produced a complete repo analysis through v2. Now do one final pass.

### Coverage Closure (required — do this before the trace)

Before tracing the obligation, close one open thread the prior passes left
behind. This step is **required**, and it is **separate from the trace's main
analytical work** below — do not fold it into the trace or skip it because the
trace feels more important.

Open the previously named blind spot **most likely to change the current
thesis**. Not any prior blind spot, and not the easiest one to open — the single
one whose resolution is most likely to move the judgment you are carrying into
this pass. (The `smallest_open` carried forward from the earlier passes is the
obvious first candidate, but choose the one that actually most threatens the
thesis.)

State, explicitly:

- **Which prior blind spot you chose** — name the pass it came from and the file path.
- **Why that blind spot was the most thesis-threatening** — why it, above the others, was most likely to change the current thesis.
- **What you found** when you actually opened it.
- **Whether the finding changes any prior judgment**, and if so, how.

Record this in the `coverage_closure` block of the structured appendix. Then
proceed to the trace.

### 1. Does this repo even have a load-bearing obligation?

Before tracing anything, answer this honestly.

Some repos are organized around a central claim the author cares about deeply — an invariant, a doctrine, a safety property, a behavioral guarantee. Those repos reward a trace.

Other repos are not organized that way. They are collections, accumulations, utilities, scripts, demos, sketches, pedagogical artifacts, or working notebooks. Their interest may lie in selection, composition, utility, or documentation rather than enforceable guarantees.

If the repo has no load-bearing obligation, say so plainly and stop. Produce instead a one-paragraph statement of what the repo's interest *actually* is, since it is not philosophical enforcement. The series ends here for this repo. That is a real finding, not a failure.

If the repo has a load-bearing obligation, continue.

### 2. Choose the obligation

Pick one claim that appears genuinely load-bearing after the v2 analysis. It should be a claim the repo seems to care about deeply: an invariant, law, safety property, architectural doctrine, protocol rule, behavioral guarantee, central promise, or domain commitment.

**Do not pick the easiest claim to trace. Pick the claim whose truth matters most to the repo's identity.**

The right claim may be hard to trace on first attempt. If the claim is hard to trace, record where the trace breaks before choosing another claim.

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
- **Wise incompleteness or abandoned ambition?** If the obligation is partially fulfilled, is the gap *deferred* (the author knows, has reasons, would close it under the right conditions) or *abandoned* (the author wrote it, moved on, and the prose now overstates the system)? A deferred gap with a credible reason is not necessarily a defect. An abandoned gap is the central finding.
- **What the trace reveals about engineering judgment.** What does this trace expose about the codebase's actual design discipline that the v1 and v2 readings did not?

What is the smallest piece of evidence that would flip your verdict on deferred-versus-abandoned, or on same-claim-versus-substitute? If you have not looked for it, look now.

### 5. Update v2

This is required. The trace is not a commentary on v2 — it is a revision of v2.

- **Restate the central abstraction in light of the trace.** If the trace confirms v2's choice, say so explicitly. If the trace shifts it, write the replacement central abstraction in full.
- **Identify any v2 section whose judgment changes.** Name the section. State the change in one sentence per section. Sharper, softer, redirected, refuted.
- **If nothing changes, say so plainly** — but state what evidence the trace actually checked.

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
Answer all four verdict questions directly. Be clear. State the verdict and the evidence that supports it.

**E. v2 Update**
State the post-trace central abstraction (confirmed or replaced). List the v2 sections whose judgments shifted, with the direction of each shift.

**F. Evidence Trail**
- One-sentence statement of the verdict.
- One-sentence statement of the obligation.
- The verbatim quote from Layer 1, with location.

**Part B: Structured Appendix**

After the prose, append a YAML block in this exact shape:

Use `source_state` to identify the exact source state analyzed. If you cannot
identify it, write `unknown` rather than inferring it from `analyzed_at`.

<!-- repo-review:pass_output -->
```yaml
pass_output:
  pass_id: trace
  template_version: 7
  repo: <identifier or URL>
  analyzed_at: <ISO 8601 timestamp>
  source_state:
    ref: <string>
    ref_kind: <commit | tag | archive | date | pasted-files | unknown>
    dirty: <true | false | unknown>
  coverage_closure:
    chosen_from_pass: <first-read | discounted-artifact | synthesis>
    path: <repo-relative path>
    why_this_was_most_thesis_threatening: <one sentence>
    finding: <one short paragraph>
    changed_prior_judgment: <true | false>
    shift_summary: <short | null>
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
    abstract_statement:
      paths:
        - <file path>
    normative_encoding:
      paths:
        - <file path>
    implementation:
      paths:
        - <file path>
    verification:
      paths:
        - <file path>
    operational_enforcement:
      paths:
        - <file path>
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
      <short paragraph>
    smallest_open:
      path: <repo-relative path>
      why_this_open: <one sentence>
      opened_this_pass: <true | false>
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

If you have been given the repo-review Output Style Guide, follow it. It is standing prose guidance, not an extra analytical pass.

The trace should be direct and evidence-backed.

Earlier passes establish what the analyzer thinks. The trace tests whether the repo enforces the central claim those passes credited. Avoid unnecessary hedging, but preserve real uncertainty.

Be opinionated. Make the opinion earn itself through the trace. The highest-value outcome is not "the repo is good" or "the repo is bad." The highest-value outcome is a precise, defensible answer to:

> Does the central claim have an enforceable path from statement to implementation, verification, and operation?
