# Structured Output Schema

This document defines the small structured-output substrate shared by
repo-review pass templates. Prose remains canonical; structured fields exist to
anchor the analyzed source state and make path-bearing fields routable by later
tools.

## Output Extraction Marker

Each pass template carries a stable sentinel comment on the line immediately
above its `pass_output` fenced block:

````markdown
<!-- repo-review:pass_output -->
```yaml
pass_output:
  ...
```
````

The sentinel is exactly `<!-- repo-review:pass_output -->`. It is an HTML comment
(invisible in rendered Markdown) that gives downstream tools an unambiguous anchor
for locating the structured appendix. Consumers should prefer the sentinel to find
the block, and fall back to the older heuristic — the first `pass_output:`-keyed
`yaml` fence — for legacy outputs emitted before the marker existed.

## Source State

Every standard single-repo pass output includes:

```yaml
source_state:
  ref: <string>
  ref_kind: <commit | tag | archive | date | pasted-files | unknown>
  dirty: <true | false | unknown>
```

This includes the optional Synthesis pass. Synthesis composes prior review
artifacts, but its `source_state` still records the focal repo source state
being synthesized, not the review artifact files.

- `ref` is the most precise identifier actually available for the analyzed
  source state. Prefer an exact commit SHA when available. Use `unknown` rather
  than inferring from `analyzed_at`.
- `ref_kind` describes the identifier: `commit`, `tag`, `archive`, `date`,
  `pasted-files`, or `unknown`.
- `dirty` records whether uncommitted local changes were included: `true`,
  `false`, or `unknown`.

`analyzed_at` records when the analysis was produced. It does not identify what
code was analyzed.

## Multi-State Passes

Delta Review compares two source states and uses:

```yaml
baseline_source_state:
  ref: <string>
  ref_kind: <commit | tag | archive | date | pasted-files | unknown>
  dirty: <true | false | unknown>
updated_source_state:
  ref: <string>
  ref_kind: <commit | tag | archive | date | pasted-files | unknown>
  dirty: <true | false | unknown>
```

Twin compares two repositories and uses:

```yaml
focal_source_state:
  ref: <string>
  ref_kind: <commit | tag | archive | date | pasted-files | unknown>
  dirty: <true | false | unknown>
twin_source_state:
  ref: <string>
  ref_kind: <commit | tag | archive | date | pasted-files | unknown>
  dirty: <true | false | unknown>
```

## Path Fields

Use `path` when exactly one repo-relative path is expected. Use path arrays
when a field can cite more than one file:

```yaml
paths:
  - src/core/operations.ts
  - src/core/engine.ts
```

Twin uses `focal_paths` and `twin_paths` for comparison entries. Lift seeds use
`source_paths` for repo-relative paths and `source_notes` for symbols, function
names, headings, line hints, or other non-path context:

```yaml
source_paths:
  - src/core/operations.ts
source_notes: |
  OperationBuilder and apply_operation are the relevant symbols.
```

Do not put repo-relative paths in `source_notes`.

Synthesis uses `paths` for repo-relative evidence behind synthesized claims.
Use separate prose fields such as `source_state_notes` and `movement_summary`
for non-path context.

## Confidence

Every standard single-repo pass (`first-read`, `discounted-artifact`,
`synthesis`, `trace`, `twin`, `lift`) carries a confidence block:

```yaml
confidence:
  overall: <high | medium | low>
  blind_spots: |
    <short paragraph>
  smallest_open:
    path: <repo-relative path>
    why_this_open: <one sentence>
    opened_this_pass: <true | false>
```

- `blind_spots` is a short, concrete prose paragraph naming what the pass did
  not resolve. It augments `smallest_open`; it does not replace it.
- `smallest_open` names the single smallest concrete file or document that, if
  opened next, would most reduce the pass's largest uncertainty. It is a routing
  aid — not proof the file was later opened.
  - `path` is the repo-relative path of that file.
  - `why_this_open` is one sentence on why opening it would most reduce
    uncertainty.
  - `opened_this_pass` records whether the analyzer opened this file during the
    current pass: `true` if it was opened now, `false` if it was left open. A
    `false` is an honest acknowledgment that the most useful open remains
    unaddressed; it does not name a future pass to hand the work to. The Coverage
    Closure step in `trace`, `twin`, and `lift` is what later forces the most
    thesis-threatening carried-forward open to be opened.

## Coverage Closure

Passes `trace`, `twin`, and `lift` begin with a Coverage Closure step: before
the pass's main work, the analyzer opens the previously named blind spot most
likely to change the current thesis, and records:

```yaml
coverage_closure:
  chosen_from_pass: <first-read | discounted-artifact | synthesis | trace | twin>
  path: <repo-relative path>
  why_this_was_most_thesis_threatening: <one sentence>
  finding: <one short paragraph>
  changed_prior_judgment: <true | false>
  shift_summary: <short | null>
```

- This is a single chosen blind spot, not an array. The point is
  prioritization: open the one most likely to matter, not any prior blind spot.
- `chosen_from_pass` names the earlier pass whose blind spot was chosen.
- `why_this_was_most_thesis_threatening` is one sentence justifying that this
  open, above the others, was most likely to change the current thesis.
- `finding` is a short paragraph on what opening it revealed.
- `changed_prior_judgment` is `true` when the finding shifts any prior judgment.
- `shift_summary` describes the shift in short form, or is `null` when
  `changed_prior_judgment` is `false`.

## Backwards Compatibility

Older outputs without `source_state` remain valid inputs to later passes. Delta
Review should treat missing source-state fields as lower-precision baselines,
continue from the prose and legacy fields, and avoid inferring exact refs from
timestamps.
