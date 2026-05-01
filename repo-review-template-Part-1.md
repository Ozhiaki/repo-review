# Repo Analysis Seed
*A prompt for Claude to produce a deep, taste-oriented analysis of a codebase*

---

## How to use this document

Paste this into a new Claude chat. Then either:
- Share the repo URL and let Claude fetch it, or
- Paste specific files directly, or
- Share the output of `find . -type f | head -100` plus key files you've already identified

Tell Claude upfront if you have a particular hunch about what's interesting. Your instinct is data.

---

## The Prompt

I want you to produce a deep, opinionated analysis of this codebase — not a code review, not a security audit, not a maintainability assessment. I want to understand how the author *thinks*. What do their design decisions reveal about their mental model of the problem? Where did they make an unusual choice, and what does that choice cost and gain?

The word I keep coming back to is **taste**. I want to know if this author has it, where it shows up, and what flavor it is.

---

### What to look for

**The central abstraction**
Every non-trivial codebase has one load-bearing idea — the abstraction that everything else is built around. Find it. Name it precisely. Then ask: is it the *right* abstraction for this problem, or did the author default to a familiar one? What does the choice foreclose? What does it make easy that would otherwise be hard?

**The seams**
Where did the author draw the lines between modules, layers, or concerns? These decisions are almost never discussed in READMEs but they reveal everything. A seam placed well makes the system feel inevitable. A seam placed wrong creates friction that compounds over time. Find the most interesting seam and explain why it's where it is.

**What they chose NOT to do**
Taste is often more visible in omissions than additions. What obvious feature is missing? What abstraction did they refuse to introduce? What dependency did they avoid when a lesser engineer would have reached for it? Absence is a design decision.

**The weird file**
Every interesting codebase has one file that doesn't quite fit — something that reveals the author's actual preoccupations rather than the stated purpose of the project. Find it. It might be a utility that's way too sophisticated for its apparent purpose. A data structure that implies a future the author never shipped. A comment thread that reads like a philosophical argument with themselves.

**Commit history shape** *(if accessible)*
Is this a project built in a single obsessive burst, or one that shows sustained thinking over time? Do the commit messages suggest someone who knew where they were going, or someone who discovered the design by building it? Both are interesting for different reasons. Look for the moment the project changed direction — there's almost always one.

**The README as a window into the author's mind**
Not for the content — for the framing. What problem does the author think they solved? How do they describe the intended user? What do they emphasize that a marketing person would cut? What do they bury that a marketing person would lead with? The gap between what a thing *is* and how its author *describes it* is often where the most interesting material lives.

**Borrowed ideas, transformed**
Almost nothing is truly original. But there's a difference between an author who copies a pattern and one who imports an idea from a completely different domain and applies it somewhere it doesn't quite belong — and makes it work anyway. Find the cross-domain import. Name its origin. Explain what was lost and gained in translation.

**The signature move**
Most authors have one. A recurring structural choice, a preferred way of handling a specific class of problem, a stylistic habit that shows up across the codebase. It might be the way they handle errors, or the way they structure configuration, or a peculiar preference for a certain level of indirection. Find it. It's the closest thing to a fingerprint.

---

### Output format

Structure your analysis in the following sections. Be direct and opinionated. "Interesting" is not a useful word here — say *why* it's interesting and to *whom*. Push past the obvious reading.

**1. The Author's Mental Model** *(~300 words)*
What problem do they think they're solving? This is not necessarily the same as what they wrote in the README. Reconstruct their actual theory of the problem from the evidence of the code.

**2. The Central Abstraction** *(~300 words)*
Name it, locate it in the code, assess it. Is it load-bearing? Is it the right one? What would the codebase look like if they'd made a different choice here?

**3. Three Design Decisions Worth Examining**
For each: what was the decision, what were the alternatives, and what does the choice reveal about the author's priorities and values. These should be specific — file names, function names, data structure choices — not vague gestures at "architecture."

**4. The Weird File / The Unexpected Corner**
Find the thing that doesn't quite fit. Describe it. Explain why it's there.

**5. What This Author Understands That Most Don't**
One paragraph. The sharpest, most confident claim you can make about what insight this codebase embodies that is non-obvious. If you can't make this claim confidently, say so and explain what's missing.

**6. Taste Verdict**
Does this author have taste? What kind? Use a comparison if it helps — other authors, other projects, schools of thought in software design. Be willing to say it's ordinary. Be willing to say it's strange in an unproductive way. But if it's genuinely interesting, say exactly why.

**7. Fragments** *(for Bawaajige)*
Pull out 3–5 short excerpts, observations, or questions from the analysis that would work as standalone research snapshot entries — things a dreaming mind could pick up and drift sideways from. These should be self-contained, surprising, and no longer than 3 sentences each. Label them `[FRAGMENT 1]` through `[FRAGMENT N]`.

**8. Fascination Candidates**
List 1–3 ideas from this codebase that might be worth adding to `fascinations.md`. Not summaries of the repo — ideas that the repo *surfaces* that have a life beyond it. Phrase them the way fascinations are phrased: as open questions or unresolved tensions, not conclusions.

---

### A note on tone

Write like someone who has read a lot of code and has opinions about it. Not contemptuous, not cheerleading. The posture is: *I am trying to understand what this person was thinking, and I will tell you what I actually find.* If something is mediocre, say it plainly and move on. If something is genuinely surprising, dwell on it.

The audience for this analysis is a human who curates interesting ideas for a dreaming agent — and the dreaming agent itself, which will encounter fragments of this analysis in its research inbox and drift sideways from them. Write for both.