# `/repo-review:update`

`/repo-review:update` is a review-state revision workflow. It consumes prior
repo-review outputs, durable review state, and Git-derived evidence, then
updates or extends earlier analysis.

It does not replace the base prompt suite. The base prompts remain responsible
for the first comprehensive review. Update work amortizes that analysis across
later repository changes.

## Invocation

Prefer explicit task syntax when the runtime supports it:

```text
/repo-review:update Update my analysis for this repo.
```

Also treat clear natural-language requests as update intent:

```text
Use repo-review update to refresh my latest analysis.
Summarize which prior claims still hold after the latest changes.
```

Ask a concise clarification only when the target repository, latest review
state, or baseline provenance cannot be inferred safely.

## Boundary Model

Update boundaries are provenance-based. Do not accept arbitrary calendar windows
such as "last 90 days" as the update range.

The expected boundary order is:

1. Git commit recorded with the latest review state or base analytical output.
2. Last modified time of the relevant base analytical output as a legacy
   fallback, mapped to a defensible Git baseline.
3. A user-provided baseline commit, requested only when neither prior source is
   available.

The target revision is normally `HEAD` unless the user explicitly names a
current target revision.

## Modes

Default to closed-loop delta analysis when the current agent can responsibly
perform the analysis. The agent should resolve state and provenance, inspect the
Git delta, identify affected prior claims, write a valid `delta_review`, ingest
it, surface drift, finish the run, and report durable artifact paths.

Use resumable fallback when closed-loop analysis is not responsible. Fallback
must still create or reuse a durable run, package the reviewer prompt, and
return a resumable handoff with the run identity, packet path, reason for
fallback, and next resume instruction.
