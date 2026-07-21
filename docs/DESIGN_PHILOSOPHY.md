# Design Philosophy & Genesis

Why this project exists, what it is really for, and the rules that govern what may
be added to it. The README tells you how to run a review; this tells you what the
review is *for* — and why certain "improvements" will always be declined.

---

## Genesis: a tool for reading someone else's work

repo-review began as a short series of prompt files with one job: help its author
understand a codebase someone *else* had built. Nothing more ambitious than that.

Two properties of that original tool still govern everything. First, the author
understood every line of every prompt — comprehensibility was the point. You cannot
trust a lens you cannot see through, and a methodology you can't read end to end is
a methodology you're taking on faith. Second, it was never a code review and never
a security audit. Each pass interrogates a different layer of how an author
thinks — what they take to be obvious, where their judgment shows up, what their
machinery actually enforces, what survives when lifted out of context.

---

## The payoff: a primed conversational partner

The most valuable thing a review produces is **not** the written analysis.

It is the agent you are talking to *afterward* — one that has read the repo the way
these passes demand, has been honest with itself about what it didn't understand,
and now holds the whole thing in mind. When the target has an interesting smell or
taste, the conversation that follows is the real product: abstract, high-level, and
genuinely productive in a way that a cold chat about the same repo never is. When
the repo is juicy, that is where the value lands.

Everything else — the passes, the staged discipline, the structured appendix — is
apparatus in service of manufacturing that partner. Keep this first. A change that
makes the artifacts tidier but the conversation duller has the priorities backwards.

---

## Optionality: the tool earns each pass

The series is designed to be run in order, but it never demands completion.

After the first couple of analytical passes, you pick and choose which — if any — of
the later passes to run. If the tool isn't earning its keep on this particular repo,
you put it down. That is a supported outcome, not a failure of nerve. The cost of
entry is two passes, not seven.

Early termination is built into the methodology for the same reason. The Trace stops
if the repo has no load-bearing obligation to trace; the Lift stops if the repo
yields nothing extractable. A pass that halts with a real finding — *"this is a
collection, not an argument"* — tells you more about the repo than one that
fabricates a spine to look thorough. Honesty about emptiness is signal.

---

## Two faces: human and agentic

The original tool was purely human-facing: canonical prose, written for and read by
a person.

Later it grew a second face. A structured **YAML appendix** was added to each pass
so a review could be produced and consumed more autonomously by agents — routing
findings, comparing repos, feeding downstream tools — without a human in the loop
for every step. repo-review now has an *agentic face* alongside its human one, and
it serves both readers with a single discipline: tell the truth as you see it, mark
where your sight is weak, leave the next reader something to push against.

The two faces are not in tension by default. They become a tension only when a
proposed change pulls toward one at the expense of the other — which is what the
next section guards against.

## Output style: standing guidance, not a pass

[`OUTPUT_STYLE.md`](OUTPUT_STYLE.md) is safe standing context for every review
pass. It does not reveal future pass instructions, name a later analytical move,
or change what any pass is supposed to inspect. It only governs prose style:
prefer evidence-backed engineering claims over critic-style labels, extended
metaphor, and author psychology.

This belongs as Markdown guidance rather than as a linter. The validators can
check structure; they cannot decide whether a judgment is well written without
becoming a fake quality gate. The right integration is therefore operational:
provide the style guide with each pass, and let the pass prompt's tone note point
back to it.

---

## The boundary: the agentic face speaks the human idiom

This is the load-bearing rule for everything added from here on:

> **The agentic face must speak the human face's idiom — prose, Markdown, or YAML.
> JSON is the boundary.**

The structured appendix is YAML, not JSON, on purpose. YAML is something a human
reads without friction; JSON is something only a machine reads comfortably. Choosing
YAML kept the human face primary *even in the machine-facing part* of the tool.

So the test for any "make it more machine-consumable" proposal is one question: **can
it be expressed in an artifact a human would also read?** If yes, it's accretive to
both faces — build it. If it can *only* be JSON, that is the signal it doesn't belong
in repo-review at all; it belongs to a separate machine product — an orchestrator, an
aggregator, an extractor — and this project deliberately does not build those.

The concrete precedent: when the series needed a machine-readable manifest of its own
shape, it became Markdown [`PASSES.md`](PASSES.md) — a table and a prerequisite DAG a
person reads — not a `passes.json`. Same information, human idiom. That is the move to
imitate.

---

## The taste filters

Every proposed change is checked against a short list. They are deliberately strict,
because most additions to a small, legible tool make it larger and less legible.

- **Prose stays canonical; structure stays thin.** The writing is the product; the
  structured fields are a thin substrate beneath it, not a second product.
- **No compliance bloat.** Don't add ceremony, self-checks, or boilerplate that
  doesn't earn its weight. Every line a maintainer has to understand is a cost.
- **The validators check structure, never analytical quality.** A linter can prove
  the appendix is well-formed; it cannot prove the review is *good*, and it must not
  pretend to. Structural validity is necessary, never sufficient.
- **No pass anticipates a later pass.** Each pass is performed without knowing what
  the next one asks for. That blindness is not a limitation to engineer around — it
  is the diagnostic. A pass that name-drops a future pass has corrupted the frame.
- **Improvements are accretive increments, not new product surfaces.** Extend what
  exists; don't bolt on a new tool wearing the project's name.

A change that fails these filters is usually trying to turn repo-review into
something it isn't. The answer is usually no — and saying no is how the tool stays
the thing that was worth building.
