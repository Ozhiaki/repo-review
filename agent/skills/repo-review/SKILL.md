---
name: repo-review
description: Maintain repo-review analyses through a provider-neutral skill family. Use for `/repo-review:update` and natural-language requests to refresh prior repo-review analysis from durable review state.
---

# repo-review

This skill family gives users a compact way to maintain repo-review analysis
without exposing the CLI's primitive workflow steps as the normal interface.

The first task surface is `/repo-review:update`. It revises prior review state
and prior analytical output against current repository evidence. It is not a
fresh full review.

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
- Future sibling surfaces, likely `/repo-review:ingest` and
  `/repo-review:continue`, are reserved for resumable update flows.

## References

- `references/update.md`: user-facing update semantics and workflow modes.
- `references/command-selection.md`: command discovery, compatibility checks,
  and workflow command preferences.
- `references/artifact-contracts.md`: required review-state, run, and
  `delta_review` artifact contracts.

Keep this file short. Put detailed workflow instructions in references and keep
the skill body provider-neutral unless a concrete runtime adapter is required.
