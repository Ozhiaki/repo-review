# `/repo-review:update`

`/repo-review:update` is a review-state revision workflow. It consumes prior
repo-review outputs, durable review state, and Git-derived evidence, then
updates or extends earlier analysis.

It does not replace the base prompt suite. The base prompts remain responsible
for the first comprehensive review. Update work amortizes that analysis across
later repository changes.

Do not treat update as "run all review prompts again." The skill should preserve
the distinction between base review outputs and delta review outputs.

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

## User-Facing Contract

The user should experience update as a compact analytical request, not as a CLI
recipe. Translate intent into workflow commands after capability discovery, then
return the analytical result and durable artifact locations.

When closed-loop analysis completes, final responses should include:

- baseline and target revision reviewed, when known
- prior claims or opinions that strengthened, weakened, invalidated, became
  contested, or stayed materially unchanged
- new candidate claims or risks
- warnings and unresolved judgment calls
- durable artifacts created or updated
- next recommended action, if any

When update cannot continue without a clarification, ask for only the missing
decision. Do not list all possible workflow commands as the default response.

## Boundary Model

Update boundaries are provenance-based. Do not accept arbitrary calendar windows
such as "last 90 days" as the update range. If the user asks for a calendar
window, redirect to the provenance model and explain that repo-review updates
the prior analysis to the current repository state.

Resolve the baseline in this order:

1. Use a Git commit identifier recorded with the latest review state or base
   analytical output.
2. If no commit identifier exists, use the last modified time of the relevant
   base analytical output as a legacy fallback, mapped to a defensible Git
   baseline.
3. If neither source is available, block and ask the user for a baseline commit.

The target revision is normally `HEAD` unless the user explicitly names a
current target revision.

When baseline discovery is ambiguous because the CLI does not expose provenance
or base-output selection clearly enough, record the friction with
`repo-review feedback` during discovery instead of guessing silently.

## Modes

Default to closed-loop delta analysis when the current agent can responsibly
perform the analysis.

Closed-loop sequence:

1. Resolve the target repository.
2. Resolve the latest usable review state and baseline provenance.
3. Start or reuse a durable delta run through the CLI. Let the CLI decide
   whether an existing run matches; do not implement skill-side duplicate
   detection.
4. Inspect Git-derived evidence between the baseline and target revision. Use
   the CLI-produced diff report when available, and inspect source files deeply
   enough to understand affected behavior.
5. Identify prior claims or prior analytical opinions implicated by the changed
   files, watch paths, invalidation triggers, or impact plan.
6. Analyze changed areas deeply enough to revise the prior judgment. Preserve
   the distinction between subject drift and analysis drift when the evidence
   supports it.
7. Produce a valid `delta_review` artifact with `summary`, `candidate_claims`,
   `drift`, and `warnings`.
8. Ingest the artifact through the workflow ingest path.
9. Surface drift and finish the run when the CLI reports it is finishable.
10. Report changed opinions, new candidate claims, warnings, unresolved
    judgment calls, and durable artifact paths.

Use resumable fallback when closed-loop analysis is not responsible. Fallback
must still create or reuse a durable run, package the reviewer prompt, and
return a resumable handoff with the run identity, packet path, reason for
fallback, and next resume instruction.
