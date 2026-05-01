# repo-review

A series of taste-oriented analyses of interesting codebases. Not code reviews. Not security audits. Reconstructions of how the author *thinks* — the central abstraction, the seams, the weird file, the signature move.

Each review aims to surface fragments and fascinations that can feed a dreaming agent's research inbox, alongside a verdict written for humans who care about software design.

## Structure

```
repo-review/
├── repo-review-template-Part-1.md   # Foundation: mental model, central abstraction, taste verdict
├── repo-review-template-Part-2.md   # Extension
├── repo-review-template-Part-3.md   # Extension
├── repo-review-template-Part-4.md   # Extension
└── reviews/                         # individual repo analyses (forthcoming)
```

The templates are layered. Part 1 is the foundation; Parts 2–4 add depth and specialized lenses.

## How to run a review

**Critical: present the parts to the agent one at a time.** Each stage shapes what the agent attends to. If later parts are visible while it's working on an earlier one, its direction gets polluted by anticipation of what's coming.

1. Pick a repo worth thinking about.
2. Give the agent **Part 1 only**. Let it produce its full Part 1 analysis.
3. Give the agent **Part 2 only**. Let it produce its full Part 2 analysis.
4. **After Part 2**, ask the agent to combine its first two outputs — using what was learned in Part 2 to rewrite or rephrase Part 1 in light of the new information. Part 2 often reframes what Part 1 saw; the merge produces the real foundation.
5. Continue with Part 3, then Part 4, each in isolation.
6. Drop the final output in `reviews/`.
7. Pull fragments and fascination candidates into Bawaajige's research inbox.

## Audience

Two readers: a human who curates interesting ideas, and a dreaming agent that drifts sideways from fragments. The writing serves both.
