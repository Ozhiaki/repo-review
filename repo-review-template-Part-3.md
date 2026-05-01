# Repo Analysis Seed - Part III
*A third-pass prompt for Claude, to be issued only after Part I and Part II are complete*

---

## Why this is a separate document

This section exists to catch a different failure mode than Part II.

Part II catches **the central artifact discount**: the tendency to under-read the biggest, strangest, most formal artifact in the repo.

Part III catches **the aesthetic overcredit problem**: once the spine has been found, the analyzer may admire the repo's self-conception without checking whether the repo can actually discharge it. A codebase can have a brilliant theory, vocabulary, architecture doctrine, or invariant set and still fail to connect that theory to executable enforcement.

The correction is to trace one load-bearing obligation end to end.

This must be separate from Parts I and II. If the model sees this task too early, it will bias the earlier analysis toward claims that are easy to trace. It may choose the "central abstraction" because it has obvious code references rather than because it is actually central. That corrupts the diagnostic value of the first two passes.

So: complete Part I. Then complete Part II. Only after the v2 analysis exists should you run Part III.

---

## How to use this document

Paste the prompt below into the same Claude chat after the v2 analysis is complete. If the conversation context has been lost, start a new chat with the v1 and v2 analyses attached, plus enough repo context to inspect files.

---

## The Prompt

You have produced a v2 repo analysis after correcting for the central artifact you discounted. Now do one final pass.

### 10. Trace One Load-Bearing Obligation

Pick one claim that appears genuinely load-bearing after the v2 analysis. It should be a claim the repo seems to care about deeply: an invariant, law, safety property, architectural doctrine, protocol rule, behavioral guarantee, or central promise.

Do not pick the easiest claim to trace. Pick the claim whose truth matters most to the repo's identity.

Trace it through the repo from abstraction to enforcement.

For each layer, identify concrete files and explain what the layer contributes:

1. **Abstract Statement**
   Where is the obligation stated most abstractly? This may be a theory document, RFC, architecture note, root instruction, design doctrine, or manifesto-like artifact.

2. **Normative Encoding**
   Where does the repo turn the abstract statement into a named obligation? Look for behavior IDs, requirements, schemas, policy entries, gate definitions, protocol fields, stable IDs, or machine-readable contracts.

3. **Implementation**
   Where does executable code attempt to enforce the obligation? Identify specific modules, functions, state machines, traits, or data structures.

4. **Verification**
   Where is the obligation tested, fuzzed, property-checked, linted, reviewed, or otherwise verified? Include both direct tests and indirect gates.

5. **Operational Enforcement**
   Where does this obligation affect runtime behavior, developer workflow, CI, release, admission, merge, deployment, or incident handling?

6. **Breaks, Gaps, and Soft Spots**
   Where does the trace weaken? Look for stringly-typed checks, missing tests, aspirational docs, unimplemented policy, manual process, unverified assumptions, TODOs, weak threat-model coverage, or code that enforces a narrower property than the abstract claim.

Then answer these questions:

- Is the obligation actually enforceable in the current repo, or mostly aspirational?
- Does the implementation enforce the same claim the abstract layer makes, or a weaker substitute?
- Is the trace intentionally incomplete, with gaps named by the author, or accidentally incomplete?
- What does this trace reveal about the author's taste that the earlier analysis did not?

---

### Output Format

Produce a focused addendum, not a full rewrite.

Use this structure:

**A. Obligation Chosen**
Name the obligation in one sentence. Explain why you chose it over nearby candidates.

**B. Trace**
Walk the obligation through the six layers above. Use concrete file paths and names. Be specific.

**C. Enforcement Verdict**
Give a direct judgment: enforced, partially enforced, aspirational, or incoherent. Explain the verdict.

**D. What Changed**
State whether this trace changes the v2 analysis. It might sharpen it, soften it, expose a contradiction, or confirm it.

**E. Fragments**
Pull out 2-4 short fragments that would work as standalone research snapshot entries.

---

### Selection Guidance

Good candidates often sound like:

- "No authoritative transition without a gate receipt."
- "Default-deny authority."
- "Effects are idempotent under crash/retry."
- "Ledger is the source of truth."
- "Boundary traffic must be typed and canonicalized."
- "Context is machine-validated, not prose-driven."
- "Terminal states absorb all future inputs."
- "Summaries are lossy claims with evidence pointers."
- "Liveness never overrides containment."

Bad candidates:

- Claims that are too small to reveal the repo's worldview.
- Claims that are purely local bug fixes.
- Claims with no abstract/spec layer.
- Claims selected only because they are easy to grep.

---

### A note on tone

This pass should be less literary than the first two. The task is not to admire the repo's philosophy; it is to test whether one important philosophical claim reaches the machinery.

Stay opinionated, but make the opinion earn itself through the trace.

The highest-value outcome is not "the repo is good" or "the repo is bad." The highest-value outcome is a precise answer to:

> Does the discovered spine actually reach the bones?
