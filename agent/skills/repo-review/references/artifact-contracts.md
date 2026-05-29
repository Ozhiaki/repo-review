# Artifact Contracts

The skill must preserve repo-review's structured artifacts so future agents and
tools can resume without rereading the original chat.

## Review State

A review state records the prior analysis baseline, including repository
metadata, analyzer identity, pass output references, durable claims, drift
material, and known limits.

For update work, the baseline should come from commit provenance recorded with
the latest review state or base analytical output. Legacy prose-only outputs may
fall back to file modified time only when no commit provenance exists.

## Review Runs

Durable runs are the workflow record for delta updates. The CLI's
`agent-context` response defines the supported statuses and transitions.

The expected delta flow is:

```text
created -> diff_ready -> impact_ready -> prompt_ready -> review_received -> ingested -> drift_ready -> complete
```

Runs may also become `blocked` when a human decision or missing input prevents
progress, or `failed` when the CLI records a durable failure and recovery hint.

## Delta Review Artifact

Full ingest requires a delta review artifact. Markdown is the primary format,
and it must contain a structured YAML block named `delta_review`.

Minimal valid Markdown:

```yaml
delta_review:
  summary: "No material drift found."
  candidate_claims: []
  drift: []
  warnings: []
```

The lists may be empty. Entries may be concise prose strings when richer objects
would be premature.

JSON artifacts are valid only when they match the CLI-declared
`delta-review` schema and use `kind: delta-review`.

Use attach-only ingest only to preserve raw reviewer output that is not yet a
valid full-ingest artifact.
