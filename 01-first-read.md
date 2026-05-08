---
pass_id: first-read
name: The First Read
version: 2
prerequisites: []
output_kind: prose-with-yaml-appendix
terminates_early_when: never
intended_audience:
  - human-curator
  - downstream-analysis-passes
  - downstream-extraction-tools
---

# The First Read
*A first-pass prompt for Claude to produce a deep, taste-oriented analysis of a codebase*

---

## How to use this document

Paste this into a new Claude chat. Then either:
- Share the repo URL and let Claude fetch it
- Paste specific files directly
- Share `find . -type f | head -100` plus the files you've already identified as load-bearing

If you have a hunch about what's interesting in the repo, say so upfront. Your instinct is data, not contamination.

If you have *no* hunch and you're reviewing this repo because it crossed your path, say that too. The absence of a hunch is also data.

---

## What this prompt is for

This is a first pass. It is meant to be performed without knowing what later passes ask for. The point of the first pass is to capture *the analyzer's first impression* — coverage-driven, time-bounded, opinionated, blind to its own blind spots. Later passes interrogate this first impression. Each one asks: *what did the first pass miss, discount, overcredit, or fail to compare against?*

If you have used the later parts of this series before, do not let that knowledge bleed into this pass. Read this repo as if this were the only pass. The later passes depend on this one being honest about its blindness.

---

## The Prompt

I want you to produce a deep, opinionated analysis of this codebase. Not a code review. Not a security audit. Not a maintainability assessment. I want to understand how the author *thinks*. What do their design decisions reveal about their mental model of the problem? Where did they make an unusual choice, and what does that choice cost and gain?

The word I keep coming back to is **taste**. I want to know if this author has it, where it shows up, and what flavor it is.

Be willing to say the taste is ordinary. Be willing to say the taste is strange in an unproductive way. But if it is genuinely interesting, dwell on why.

---

### What to look for

These are lenses, not a checklist. You do not need to address every one explicitly in the output. Use the ones that surface real findings for *this* repo and skip the ones that don't.

**The central abstraction.** Every non-trivial codebase has one load-bearing idea — the abstraction that everything else is built around. Find it. Name it precisely. Then ask: is it the *right* abstraction for this problem, or did the author default to a familiar one? What does it foreclose? What does it make easy that would otherwise be hard?

**The seams.** Where did the author draw the lines between modules, layers, or concerns? These decisions are almost never discussed in READMEs but they reveal the author's working theory of the problem. A seam placed well makes the system feel inevitable. A seam placed wrong creates friction that compounds over time. Find the most interesting seam and explain why it's where it is.

**What they chose NOT to do.** Taste is often more visible in omissions than additions. What obvious feature is missing? What abstraction did they refuse to introduce? What dependency did they avoid when a lesser engineer would have reached for it? Absence is a design decision.

**The weird file.** Every interesting codebase has one file that doesn't quite fit — something that reveals the author's actual preoccupations rather than the stated purpose of the project. A utility that's way too sophisticated for its apparent purpose. A data structure that implies a future the author never shipped. A comment thread that reads like a philosophical argument with themselves. Find it.

**Commit history shape** *(if accessible)*. Is this a project built in a single obsessive burst, or one that shows sustained thinking over time? Do the commit messages suggest someone who knew where they were going, or someone who discovered the design by building it? Look for the moment the project changed direction — there is almost always one.

**The README as a window into the author's mind.** Not for the content — for the framing. What problem does the author *think* they solved? How do they describe the intended user? What do they emphasize that a marketing person would cut? What do they bury that a marketing person would lead with? The gap between what a thing *is* and how its author *describes it* is often where the most interesting material lives.

**Borrowed ideas, transformed.** Almost nothing is truly original. But there is a difference between an author who copies a pattern and one who imports an idea from a completely different domain and applies it somewhere it doesn't quite belong — and makes it work anyway. Find the cross-domain import. Name its origin. Explain what was lost and gained in translation.

**The signature move.** Most authors have one. A recurring structural choice, a preferred way of handling a specific class of problem, a stylistic habit that shows up across the codebase. The way they handle errors. The way they structure configuration. A peculiar preference for a certain level of indirection. Find it. It is the closest thing to a fingerprint.

---

### Output format

Be direct and opinionated. "Interesting" is not a useful word here — say *why* it is interesting and to *whom*. Push past the obvious reading.

Produce two outputs:

**Part A: Prose Analysis**

**1. The Author's Mental Model** *(~300 words)*
What problem do they think they're solving? This is not necessarily the same as what they wrote in the README. Reconstruct their actual theory of the problem from the evidence of the code.

**2. The Central Abstraction** *(~300 words)*
Name it. Locate it in the code. Assess it. Is it load-bearing? Is it the right one? What would the codebase look like if they had made a different choice here?

**3. Three Design Decisions Worth Examining**
For each: what was the decision, what were the alternatives, what does the choice reveal about the author's priorities. Specific. File names, function names, data structure choices. Not vague gestures at "architecture."

**4. The Weird File / The Unexpected Corner**
Find the thing that doesn't quite fit. Describe it. Explain why it is there.

**5. What This Author Understands That Most Don't**
One paragraph. The sharpest, most confident claim you can make about what insight this codebase embodies that is non-obvious. If you cannot make this claim confidently, say so and explain what is missing — that is also a finding.

**6. Taste Verdict**
Does this author have taste? What kind? Use a comparison if it helps — other authors, other projects, schools of thought in software design. Be willing to say it is ordinary. Be willing to say it is strange in an unproductive way. But if it is genuinely interesting, say exactly why.

**7. Confidence and Reading Conditions**
A short, honest paragraph addressing:
- How much of the repo did you actually read versus skim?
- Which sections of this analysis are you most confident in, and which are scaffolding?
- What did you not have time or context to investigate that you suspect would matter?
- If asked to defend the Taste Verdict against a smart reader who disagreed, where would you feel weakest?

This section is not optional. It is not a hedge. It is the document the later passes need in order to do their work.

**Part B: Structured Appendix**

After the prose, append a YAML block in this exact shape:

```yaml
pass_output:
  pass_id: first-read
  repo: <identifier or URL>
  analyzed_at: <ISO 8601 timestamp>
  central_abstraction:
    name: <one short phrase>
    location: <file path or paths>
    is_load_bearing: <true | false | partial>
  taste_verdict: <distinctive | ordinary | strange-unproductively | strange-productively | insufficient-evidence>
  signature_move:
    name: <one short phrase or null>
    location: <file path or null>
  weird_file:
    path: <file path or null>
    one_line_why: <short explanation or null>
  topic_tags: [<tag>, <tag>, ...]
  confidence:
    overall: <high | medium | low>
    weakest_section: <section number from prose, e.g. "5">
    coverage: <thorough | partial | thin>
    blind_spots: |
      <one paragraph>
```

`topic_tags` are domain or subject tags chosen by the analyzer (e.g. `distributed-systems`, `static-analysis`, `cli-tooling`, `formal-methods`). Multi-tag is acceptable. No-tag is suspicious — the analyzer should be able to place the repo somewhere.

---

### A note on tone

Write like someone who has read a lot of code and has opinions about it. Not contemptuous. Not cheerleading. The posture is: *I am trying to understand what this person was thinking, and I will tell you what I actually find.*

If something is mediocre, say it plainly and move on. If something is genuinely surprising, dwell on it. The audience is a human curator who will read this carefully and ask sharper questions afterward — and downstream tools that will encounter pieces of this analysis later, in different contexts, and use them for purposes the analyzer cannot anticipate.

Both audiences are served by the same discipline: tell the truth as you see it, mark where your sight is weak, and leave the next reader something to push against.
