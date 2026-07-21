# docs

Reference material for the repo-review series. The seven prompt templates and the
project [`README.md`](../README.md) live at the repo root; these are the documents
you reach for when you need them.

- **[DESIGN_PHILOSOPHY.md](DESIGN_PHILOSOPHY.md)** — why the project exists, the
  human value it delivers (a conversational partner primed on the target repo), and
  the design rules that govern what may be added to it.
- **[OUTPUT_STYLE.md](OUTPUT_STYLE.md)** — standing prose guidance for generated
  repo-review outputs. Safe to provide with every pass because it contains no
  future-pass instructions.
- **[STRUCTURED_OUTPUT_SCHEMA.md](STRUCTURED_OUTPUT_SCHEMA.md)** — the schema for the
  YAML appendix every pass emits: source-state, confidence, coverage-closure, path
  fields, and the extraction marker.
- **[PASSES.md](PASSES.md)** — the drift-checked map of the series: every pass's
  version, prerequisites, early-stop condition, and a prerequisite DAG. Kept in sync
  with the template frontmatters by `tools/lint_pass_map.py`.
