# Discovery Trials

These results come from the first `/repo-review:update` substrate-discovery
pass on 2026-05-29. Treat the trials as evidence about CLI workflow support, not
as proof that the skill is complete.

## Trial Prompts

### `/repo-review:update Update my analysis for this repo.`

Result: sufficient for fallback orchestration.

The CLI resolved the latest review state for the repo, including baseline commit
`77b7bd3`, and created a durable delta run for `77b7bd3..HEAD`:

- run: `repo-review-delta-2026-05-29-9084c3016f`
- status: `prompt_ready`
- prompt packet:
  `reviews/repo-review/delta-2026-05-29-9084c3016f/delta-trace-prompt.md`

Repeating the same `review start` command returned `mutation_outcome:
existing`, so the skill can rely on CLI duplicate detection for that natural
key.

### `Use repo-review update on this legacy review folder.`

Result: sufficient to block safely, not sufficient for closed-loop update.

`state bootstrap --dry-run` discovered legacy prose files, but produced a
claim-empty state shell and no defensible update baseline. The trial also found
machine-readable ambiguity around duplicate `pass_id` values and inferred
filename-based pass IDs.

Feedback: `feedback-2026-05-29T124043480044Z0000`

Converted Bead: `rep-g7b.9` (`Expose legacy output ambiguity`)

### `Continue the latest repo-review update.`

Result: sufficient for skill translation.

`review continue --latest --json --no-input` returned the latest run, its
`prompt_ready` status, the prompt packet path, and next-action meaning. It also
returned a concrete `run_id`, but the recommended command still used the
placeholder `<run-id>`.

Feedback: `feedback-2026-05-29T124140712286Z0000`

This is non-blocking because the skill can fill the command from `run.run_id`.

### `Ingest this reviewer output and finish the update.`

Result: sufficient for ingest and finish mechanics, incomplete for durable drift
artifact reporting.

A minimal valid `delta_review` Markdown artifact ingested successfully, and
`review finish` completed the run. However, the completed run still had
`run.artifacts.drift_surface: null` even though ingest recommended drift
surfacing. The standalone `drift surface` command can produce JSON, but the
workflow did not bind that artifact back to the run before completion.

Feedback: `feedback-2026-05-29T124217817051Z0000`

Converted Bead: `rep-g7b.10` (`Bind drift surface to run`)

Additional verification found that `review finish` recommends
`repo-review review status --run <run-id> --json --no-input`, and the manifest
advertises `review status`, but the executable rejects `review status` as an
unknown review subcommand.

Feedback: `feedback-2026-05-29T124341923162Z0000`

Converted Bead: `rep-g7b.11` (`Fix review status contract`)

## Feedback Policy

During discovery trials, record CLI or workflow friction with
`repo-review feedback`.

Convert feedback to Beads immediately when it blocks a discovery trial or makes
the skill unable to meet its durable-artifact contract. Batch recurring
non-blocking friction after the trial set is complete.
