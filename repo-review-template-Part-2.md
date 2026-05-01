# Repo Analysis Seed — Part II
*A second-pass prompt for Claude, to be issued only after Part I is complete*

---

## Why this is a separate document

This section exists to catch a specific failure mode: **the central artifact discount.** When a repo contains one document or component that is much larger, much more formal, or much more abstract than its neighbors, the first-pass analyzer reliably underweights it — treating it as ambition, decoration, or aspiration rather than as the load-bearing spine. The bigger and stranger the artifact, the more likely it gets filed under "honorable mention." This is not laziness; it is a structural property of how coverage-oriented reading works. The largest formal artifact resists coverage reading because it requires depth, so the analyzer satisfies the section requirement with a one-line gesture and moves on. The template rewards this: every section gets filled, the analysis looks complete, and the spine never gets read.

The correction is to do a second pass — but the second pass only works if the first pass was done *without knowing the second pass was coming*. If section 9 were appended to Part I, Claude would behave differently throughout sections 1–8: it would search harder for "the artifact I'm probably discounting" while doing the original reading, hedge its judgments to leave room for revision, and produce an analysis pre-shaped to anticipate the correction. The diagnostic value would collapse. We want the first pass performed with the same blindness a real reader brings — coverage-driven, time-bounded, prone to discount the artifact that doesn't look like the spine. We want the *delta between v1 and v2* to be legible, because the delta is itself evidence about what's hard to see on first read, and the delta is often the most interesting finding.

So: complete Part I in full. Produce v1. Then — and only then — paste Part II.

---

## How to use this document

Paste the prompt below into the same Claude chat after the v1 analysis is complete. Do not paste it earlier. If the conversation context has been lost, start a new chat with v1 attached and paste Part II as the first message.

---

## The Prompt

You have produced a complete repo analysis using the Part I template. Now do one more thing.

### 9. The Artifact You Discounted

Identify the single artifact in this repo that you gave the least attention relative to its size, formality, or structural prominence. The usual suspects: the longest document, the most abstract one, the one with the most inbound references, the one you described as "ambitious," "aspirational," "compresses the project into formal axioms," or filed under "honorable mention." Sometimes the candidate is not a document at all — it might be a config file that turns out to encode a DSL, a test suite that turns out to specify the system more completely than the source, a comment thread that turns out to be the design rationale, or a vendored dependency the author rewrote rather than imported. The common signature is: prominent by some structural measure, but quietly under-read on the first pass.

Read it now, properly. Take the time you didn't take the first time.

Then revise any earlier section of the v1 analysis whose judgment changes as a result. Produce a v2 of the full analysis, not a patch — but at the top of v2, include a short note (3–5 sentences) explaining what shifted, what you missed the first time, and why. Be specific about which sections changed and in which direction (sharper, softer, redirected, refuted).

If nothing shifts, say so plainly. But before you do, check: did you actually re-read, or did you re-skim? The failure mode this section exists to catch is the one where the load-bearing spine of the project looks, on first read, like a side document. The discipline is to assume that failure mode is operative until you've done the work to rule it out.

---

### A note on tone for v2

The v2 analysis should not pretend v1 didn't happen. The corrections are part of the artifact. Mark them. The audience — both the human curator and the dreaming agent — benefits from seeing where a careful reader's first impression diverged from their second, because that gap is itself a fragment worth drifting from.
