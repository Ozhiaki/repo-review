# Structured Output Schema

This document defines the small structured-output substrate shared by
repo-review pass templates. Prose remains canonical; structured fields exist to
anchor the analyzed source state and make path-bearing fields routable by later
tools.

## Source State

Every standard single-repo pass output includes:

```yaml
source_state:
  ref: <string>
  ref_kind: <commit | tag | archive | date | pasted-files | unknown>
  dirty: <true | false | unknown>
```

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

## Backwards Compatibility

Older outputs without `source_state` remain valid inputs to later passes. Delta
Review should treat missing source-state fields as lower-precision baselines,
continue from the prose and legacy fields, and avoid inferring exact refs from
timestamps.
