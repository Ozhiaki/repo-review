---
name: repo-review
description: Maintain repo-review analyses through a provider-neutral skill family. Use for `/repo-review:update` and natural-language requests to refresh prior repo-review analysis from durable review state.
---

# repo-review

This skill family gives users a compact way to maintain repo-review analysis
without exposing the CLI's primitive workflow steps as the normal interface.

The first task surface is `/repo-review:update`. It revises prior review state
and prior analytical output against current repository evidence. It is not a
fresh full review, and it does not replace the base prompt sequence.

## Required First Step

Before relying on any repo-review command contract, run:

```bash
repo-review agent-context --json
```

If the current checkout provides `./repo-review`, prefer that executable. Use
the JSON response as the source of truth for available commands, flags, schemas,
run statuses, delivery modes, and helper templates.

If a required command, flag, schema, status, or artifact contract is missing,
stop with a compatibility error. Do not silently replace missing CLI behavior
with hand-written command recipes.

## Task Surfaces

- `/repo-review:update`: revise prior review state from its provenance baseline
  to the current target revision.
- Natural-language fallback: handle requests such as "Use repo-review update to
  refresh my latest analysis" when slash-family task syntax is unavailable.
- Summary-oriented requests such as "which prior claims still hold?" are update
  intent when a usable prior review state exists.
- Future sibling surfaces, likely `/repo-review:ingest` and
  `/repo-review:continue`, are reserved for resumable update flows.
  The first implementation may handle those flows inside this skill body.

For update requests, final responses should name the baseline and target
revision when known, then report changed opinions, new candidate claims or
risks, warnings, unresolved judgment calls, and durable artifact paths. Avoid
presenting command transcripts unless the user asks for operational detail.

## References

- `references/update.md`: user-facing update semantics and workflow modes.
- `references/command-selection.md`: command discovery, compatibility checks,
  and workflow command preferences.
- `references/artifact-contracts.md`: required review-state, run, and
  `delta_review` artifact contracts.
- `references/discovery-trials.md`: first discovery-trial results and feedback
  conversion notes.

Keep this file short. Put detailed workflow instructions in references and keep
the skill body provider-neutral unless a concrete runtime adapter is required.
