# Output Style Guide

repo-review prose should be evidence-first, precise, and opinionated without
becoming literary criticism. Strong judgments are welcome, but they should name
the file, behavior, artifact, or workflow that justifies the judgment.

This guide is safe standing context for every pass. It does not reveal future
pass instructions or change a pass's analytical scope.

## Core Standard

Prefer direct engineering claims:

> The harness is more disciplined than the publication path: event scripts run
> hidden checks, while the README, markdown results, JSON, and dashboard are not
> generated from one canonical source.

Avoid critic-style summaries:

> The author has sharp measurement instincts inside the harness, but the
> dashboard exposes the shadow side of that taste.

## Evidence Before Atmosphere

Use technical predicates before atmospheric modifiers. Words like "messy,"
"rough," "sharp," "ugly," "beautiful," "fragile," and "sloppy" are acceptable
only when tied to a concrete property.

Good:

- "Messy model output" when referring to thinking traces, malformed code
  fences, truncation, or unclosed reasoning blocks.
- "Stale dashboard" when followed by the actual mismatch.
- "Publication drift" when naming disagreement between public result artifacts.

Weak:

- "Local inference is ugly."
- "Sharp instincts."
- "Ordinary-to-sloppy taste."
- "Fragile public evidence surface."

## Translate Taste Into Judgment

Do not use "taste" as the main explanatory frame unless quoting prompt
terminology or filling a required schema field. In prose, translate it into
narrower engineering claims.

Use:

- "sound judgment about measurement validity"
- "weak discipline around code reuse"
- "strong harness design"
- "weak publication consistency"
- "productive but uneven"

Avoid:

- "good taste"
- "ordinary taste"
- "strange-productively"
- "shadow side of that taste"
- "what the trace reveals about taste"

If the YAML requires a compact verdict such as `strange-productively`, the prose
should render it as normal English: "productive but uneven."

## Avoid Author Psychology

Write about the codebase's demonstrated priorities, not the author's
personality.

Use:

- "The repository documents harness failures but lacks a corresponding
  publication-generation mechanism."
- "`references/harness-fixes.md` reveals sustained concern with measurement
  failures."
- "The event scripts favor inspectability over shared abstractions."

Avoid:

- "The author is strongest when..."
- "The author's real obsession..."
- "Psychologically revealing..."
- "For opposite emotional reasons..."
- "A careful empiricist..."

Author-level language is acceptable only when it is strict shorthand for
evidence already shown. Even then, prefer codebase-level phrasing.

## Use Metaphor Sparingly

One controlling analogy can help; extended metaphor chains make the analysis
feel less rigorous. If a metaphor does not name a real technical structure,
replace it with direct language.

Replace:

- "leaderboard numbers are not vibes" -> "leaderboard scores are not merely
  subjective impressions"
- "the measuring instrument lied" -> "the harness produced misleading
  measurements"
- "primitive, but not stupid" -> "simple, but intentionally inspectable"
- "scar map" / "small scars" -> "failure history" / "repair patterns"
- "the structure will creak" -> "the structure will become harder to evolve
  safely"
- "spine reaches the bones" -> "the central claim is enforced through
  implementation, verification, and operation"
- "edge of v1's truth" -> "the later pass narrows the earlier claim"

Do not extend one analogy across several sections.

## Keep Pass Vocabulary Subordinate

repo-review outputs have necessary process terms: v1, v2, pass movement, trace
layers, coverage closure, seeds, rankings, and structured verdicts. Use them for
auditability, but do not let them become the main prose style.

Use required labels, then translate quickly:

- "The first-pass central abstraction survived."
- "The discounted artifact narrowed the measurement-hygiene claim to the
  harness."
- "The trace found a substitute claim: hidden checks exist, but the public
  no-partial-credit/no-human-judgment promise is stronger than the
  implementation."

Avoid ornamental pass language:

- "What Pass 2 leavened"
- "bounds rather than refutes"
- "the delta is the finding" without naming the changed claim
- repeated "sharper," "softer," or "redirected" after the section that requires
  them

## Prefer Concrete Artifact Names

Avoid generic nouns that blur the system. "Surface," "artifact," "layer," and
"story" should be replaced with the actual object when possible.

Use:

- "dashboard"
- "README"
- "tracked JSON results"
- "markdown results"
- "event runners"
- "publication path"
- "published results artifacts"
- "run directories"
- "manifest/report/replay workflow"

Avoid:

- "public surface"
- "publication surface"
- "evidence surface"
- "weakest surface"
- "reporting layer" when the repo only has independent files

## State Comparisons Carefully

Comparative passes should not become originality scoring. Replace "more
interesting," "less interesting," and "less distinctive taste" with concrete
changes in the claim.

Use:

- "The twin makes the event-script architecture look more conventional."
- "The consumer-hardware benchmark framing remains distinctive."
- "The adjacent repo has a stronger evidence lifecycle: manifests, report
  hashes, replayable run directories, and tests."
- "Hidden tests are a scoring tactic, not a full evidence contract."

Avoid:

- "less singular"
- "less interesting as a software artifact"
- "more distinctive editorially"
- "opposite emotional reasons"

Field-wide claims need either named examples or softer scope.

## Make Synthesis Cleaner Than Its Inputs

A synthesis should not preserve weak phrasing from earlier passes just because
it is summarizing them. Translate inherited labels into cleaner current claims.

Translate:

- "weird file" -> "revealing artifact"
- "psychologically revealing" -> "revealing about project priorities"
- "strange-productively" -> "productive but uneven"
- "ordinary-to-sloppy taste" -> "weak publication discipline"
- "strong lab instrument, fragile public evidence surface" -> "the harness is
  more reliable than the publication path"

The best synthesis output is a short current account with a concrete unresolved
question.

## Keep Extraction Practical

Extraction/lift prose should sound like product and component assessment, not
excavation.

Use:

- "extractable candidate"
- "reusable component"
- "standalone utility"
- "works outside the parent repo"
- "representative malformed or trace-heavy responses"
- "unexpected viable extraction"
- "product-relevant extraction"

Avoid:

- "torn off"
- "alive on its own"
- "peel off"
- "seed hunt"
- "real ugly responses"
- "weird extraction" outside a required ranking label

Commercial claims must name a likely user and problem. Do not rank something as
commercially useful merely because it sounds productizable.

## Quick Rewrite Rules

- Replace slogans with claims.
- Replace author traits with repository evidence.
- Replace metaphors with failure modes.
- Replace generic "surface" language with named artifacts.
- Replace schema labels with normal prose when outside YAML.
- Replace comparison drama with changed claims.
- Keep every strong adjective near the evidence that earns it.
