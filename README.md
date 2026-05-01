# repo-review

A series of taste-oriented analyses of interesting codebases. Not code reviews. Not security audits. Reconstructions of how the author *thinks* — the central abstraction, the seams, the weird file, the signature move.

Each review aims to surface fragments and fascinations that can feed a dreaming agent's research inbox, alongside a verdict written for humans who care about software design.

## Structure

```
repo-review/
├── repo-review-template-Part-1.md   # Foundation: mental model, central abstraction, taste verdict
├── repo-review-template-Part-2.md   # Extensions
├── repo-review-template-Part-3.md   # Extensions
├── repo-review-template-Part-4.md   # Extensions
└── reviews/                         # individual repo analyses (forthcoming)
```

The templates are layered. Part 1 is the foundation prompt; Parts 2–4 add depth and specialized lenses. Use them together or pick the parts that fit the repo at hand.

## How a review happens

1. Pick a repo worth thinking about.
2. Apply the relevant template parts to produce the analysis.
3. Drop the output in `reviews/`.
4. Pull fragments and fascination candidates into Bawaajige's research inbox.

## Audience

Two readers: a human who curates interesting ideas, and a dreaming agent that drifts sideways from fragments. The writing serves both.
