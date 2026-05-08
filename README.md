# repo-review

A series of prompts for producing deep, taste-oriented analyses of codebases.

Not code reviews. Not security audits. Each pass interrogates a different layer of how the author thinks — what they take to be obvious, where their judgment shows up, what their machinery actually enforces, what survives when lifted out of context.

The series is designed to be run in order. Each pass is meant to be performed without knowing what later passes ask for. The diagnostic value of any single pass depends on the earlier passes being honest about their own blindness.

---

## The Passes

| Order | Name | Catches |
|------|------|---------|
| 01 | The First Read | The first impression — coverage-driven, opinionated, blind to its own blind spots |
| 02 | The Discounted Artifact | The largest or most formal artifact the first pass under-read |
| 03 | The Trace | Whether the repo's stated obligations are actually enforced by the running code |
| 04 | The Twin | What the repo's choices look like next to one adjacent repo with a different mental model |
| 05 | The Lift | What can be torn off the repo and survive on its own |

Passes 01–04 are diagnostic. Pass 05 is extractive. They do different work and produce different output.

---

## How to run a review

**Critical: present the passes to the analyzer one at a time.** Each pass shapes what the analyzer attends to. If later passes are visible while it's working on an earlier one, its direction gets polluted by anticipation of what's coming.

1. Pick a repo worth thinking about.
2. Give the analyzer **The First Read** only. Let it produce its full analysis.
3. Give it **The Discounted Artifact**. It will revise the first read into v2.
4. Give it **The Trace**. It will produce a verdict on whether the spine reaches the bones — or terminate early if no load-bearing obligation exists.
5. Optionally give it **The Twin** with a chosen adjacent repo. The twin must satisfy three constraints (shared terrain, different mental model, comparable maturity). Selection guidance is in the pass itself.
6. Optionally give it **The Lift** to surface extractable seeds — or terminate early if the repo is extraction-poor.

Each pass produces both prose (for the human curator) and a YAML appendix (for downstream tooling).

---

## Output format

Every pass produces two outputs:

- **Prose body.** Opinionated, direct, written for a careful human reader.
- **YAML appendix.** A `pass_output:` block at the end of the document, schema-aware, suitable for ingestion by downstream tools that need to route findings, compare repos, or feed structured data into other systems.

The YAML uses neutral terminology (`topic_tags`, `confidence`, `pass_output`, etc.) so the output can be consumed by tools that have nothing to do with the original use case the series was built for. Each YAML block is keyed by `pass_id`, allowing higher-level tools to route or compose the outputs without parsing prose.

---

## Frontmatter

Each pass starts with YAML frontmatter declaring its `pass_id`, `name`, `version`, `prerequisites`, `output_kind`, `terminates_early_when`, and `intended_audience`. This lets a higher-level orchestration tool inspect what each pass does, what it depends on, and when it might exit early — without reading the prompt itself.

---

## Early termination

Two passes can terminate early with a real finding rather than producing fabricated output:

- **The Trace** terminates if the repo has no load-bearing obligation. Some repos are collections, accumulations, or pedagogical artifacts — their interest is not philosophical enforcement and a trace would invent a spine the repo doesn't have.
- **The Lift** terminates if the repo yields no extractables. Some repos are tightly integrated by design and lose their point when fragmented.

Early termination is a feature, not a failure. The relevant pass produces a one-paragraph statement of *why* the pass terminated, which is itself diagnostic information about the repo.

---

## Audience

Two readers, served by the same discipline:

- A human curator who reads the prose carefully and asks sharper questions afterward.
- Downstream tools that consume the structured YAML output for purposes the analyzer cannot anticipate.

The writing serves both: tell the truth as you see it, mark where your sight is weak, leave the next reader something to push against.

---

## Repo layout

```
repo-review/
├── README.md
├── 01-first-read.md
├── 02-discounted-artifact.md
├── 03-trace.md
├── 04-twin.md
├── 05-lift.md
└── reviews/                         # individual repo analyses
```
