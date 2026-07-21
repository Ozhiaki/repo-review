---
pass_id: first-read
name: The First Read
version: 7
prerequisites: []
output_kind: prose-with-yaml-appendix
terminates_early_when: never
intended_audience:
  - human-curator
  - downstream-analysis-passes
  - downstream-extraction-tools
---

# The First Read
*A first-pass prompt for producing a deep, evidence-backed analysis of a codebase's engineering judgment*

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

This is a first pass. It is meant to be performed without knowing what later passes ask for. The point of the first pass is to capture *the analyzer's first-pass thesis* — coverage-driven, time-bounded, opinionated, evidence-backed, and explicit about incomplete coverage. Later passes interrogate this first-pass thesis. Each one asks: *what did the first pass miss, discount, overcredit, or fail to compare against?*

If you have used the later parts of this series before, do not let that knowledge bleed into this pass. Read this repo as if this were the only pass. The later passes depend on this one being explicit about what it has not verified.

---

## The Prompt

I want you to produce a deep, opinionated analysis of this codebase. Not a code review. Not a security audit. Not a maintainability assessment. I want to understand the working theory of the problem embodied by the codebase. What do its design decisions reveal about the author's priorities, assumptions, and tradeoffs? Where did it make an unusual choice, and what does that choice cost and gain?

The focus is **engineering judgment**: where the design is strong, where it is weak, and what evidence supports that assessment.

Be willing to say the engineering judgment is ordinary, uneven, or weak. If a design choice is genuinely unusual and effective, explain the concrete mechanism that makes it work.

---

### What to look for

These are lenses, not a checklist. You do not need to address every one explicitly in the output. Use the ones that surface real findings for *this* repo and skip the ones that don't.

**The central abstraction.** Many non-trivial codebases have a load-bearing idea — an abstraction much of the system is built around. Find it if it exists. Name it precisely. Then ask: is it the *right* abstraction for this problem, or did the author default to a familiar one? What does it foreclose? What does it make easy that would otherwise be hard?

**The seams.** Where did the author draw the lines between modules, layers, or concerns? These decisions are almost never discussed in READMEs but they reveal the codebase's working theory of the problem. A boundary placed well localizes change, clarifies ownership, and reduces coupling. A boundary placed poorly spreads changes across modules or makes behavior harder to reason about. Find the most interesting boundary and explain why it is where it is.

**What they chose NOT to do.** Engineering judgment is often visible in omissions as much as additions. What obvious feature is missing? What abstraction did they refuse to introduce? What dependency did they avoid, and what did that avoidance cost or preserve? Absence is a design decision.

**The revealing artifact.** Look for a file, script, document, generated artifact, or test whose contents materially change how the codebase should be understood. It may be unusually detailed, stale, central despite looking peripheral, or inconsistent with the README. Explain what it reveals.

**Commit history shape** *(if accessible)*. Is this a project built in a short concentrated period, or one that shows sustained thinking over time? Does the design direction appear planned upfront, discovered through implementation, or revised after specific failures? Look for the moment the project changed direction — there is almost always one.

**The README as public framing.** Not just for content — for the claims it foregrounds. What problem does the README say the project solves? How does it describe the intended user? What implementation details, constraints, or caveats does it understate? Where does the README align or diverge from the code? The gap between what a thing *is* and how its public framing describes it is often where the most useful material lives.

**Borrowed ideas, transformed.** Almost nothing is truly original. But there is a difference between copying a pattern and adapting an idea to a different context, with identifiable gains and losses. Find the cross-domain import if one exists. Name its origin. Explain what was lost and gained in translation.

**Recurring design pattern.** Look for a structural choice that appears across the codebase: the way errors are handled, configuration is structured, indirection is introduced, or a specific class of problem is solved. Treat it as a pattern in the code, not as a personality trait.

---

### Output format

Be direct and opinionated, but tie every strong judgment to a concrete file, function, data structure, workflow, or documented behavior. "Interesting" is not a useful word here — say *why* it is interesting and to *whom*. Push past the obvious reading.

Produce two outputs:

**Part A: Prose Analysis**

**1. The Codebase's Working Theory** *(~300 words)*
What problem does the codebase appear organized to solve? This is not necessarily the same as what the README says. Reconstruct the system's actual theory of the problem from the evidence of the code.

**2. The Central Abstraction** *(~300 words)*
Name it. Locate it in the code. Assess it. Is it load-bearing? Is it the right one? What would the codebase look like if they had made a different choice here?

**3. Three Design Decisions Worth Examining**
For each: what was the decision, what were the alternatives, what does the choice reveal about the author's priorities. Specific. File names, function names, data structure choices. Not vague gestures at "architecture."

**4. Revealing Artifact / Unexpected Evidence**
Find the artifact that most changes or complicates the first-pass thesis. Describe it and explain what it reveals about the system.

**5. Non-Obvious System Insight**
One paragraph. The sharpest evidence-backed claim you can make about a non-obvious problem this codebase handles well. If you cannot make this claim confidently, say so and explain what is missing — that is also a finding.

**6. Engineering Judgment Verdict**
Where does the codebase show strong judgment, weak judgment, or uneven judgment? Use comparisons only when they clarify concrete tradeoffs. Be willing to say the judgment is ordinary, unusual and unproductive, or productive but uneven.

**7. Confidence and Reading Conditions**
A short, honest paragraph (not an open-ended reflection) addressing:
- How much of the repo did you actually read versus skim?
- Which sections of this analysis are you most confident in, and which are scaffolding?
- What did you not have time or context to investigate that you suspect would matter? Keep this to your blind spots, concretely named.
- Which judgment would be easiest to challenge, and what specific additional evidence would reduce that uncertainty?
- What is the single smallest concrete file or document path that, if opened next, would most reduce your largest uncertainty? Say whether you are opening it now or leaving it open.

This section is not optional. It is not a hedge. It is the document the later passes need in order to do their work.

**Part B: Structured Appendix**

After the prose, append a YAML block in this exact shape:

Use `source_state` to identify the exact source state analyzed. If you cannot
identify it, write `unknown` rather than inferring it from `analyzed_at`.

<!-- repo-review:pass_output -->
```yaml
pass_output:
  pass_id: first-read
  template_version: 7
  repo: <identifier or URL>
  analyzed_at: <ISO 8601 timestamp>
  source_state:
    ref: <string>
    ref_kind: <commit | tag | archive | date | pasted-files | unknown>
    dirty: <true | false | unknown>
  central_abstraction:
    name: <one short phrase>
    paths:
      - <file path>
    is_load_bearing: <true | false | partial>
  taste_verdict: <distinctive | ordinary | strange-unproductively | strange-productively | insufficient-evidence>
  signature_move:
    name: <one short phrase or null>
    paths:
      - <file path>
  weird_file:
    path: <file path or null>
    one_line_why: <short explanation or null>
  topic_tags: [<tag>, <tag>, ...]
  confidence:
    overall: <high | medium | low>
    weakest_section: <section number from prose, e.g. "5">
    coverage: <thorough | partial | thin>
    blind_spots: |
      <short paragraph>
    smallest_open:
      path: <repo-relative path>
      why_this_open: <one sentence>
      opened_this_pass: <true | false>
```

`topic_tags` are domain or subject tags chosen by the analyzer (e.g. `distributed-systems`, `static-analysis`, `cli-tooling`, `formal-methods`). Multi-tag is acceptable. No-tag is suspicious — the analyzer should be able to place the repo somewhere.

---

### A note on tone

Write like someone who has read a lot of code and has opinions about it. Not contemptuous. Not cheerleading. Prefer precise technical nouns and verbs over metaphors, jokes, or critic-style labels. Use metaphor only when it compresses a real technical structure and does not replace evidence.

If something is mediocre, say it plainly and move on. If something is genuinely surprising, explain the mechanism that makes it surprising. Do not infer personality traits when a design preference, operational priority, or code pattern is enough. The audience is a human curator who will read this carefully and ask sharper questions afterward — and downstream tools that will encounter pieces of this analysis later, in different contexts, and use them for purposes the analyzer cannot anticipate.

Both audiences are served by the same discipline: tell the truth as you see it, mark where your sight is weak, and leave the next reader clear claims, evidence, and named uncertainties to test.
