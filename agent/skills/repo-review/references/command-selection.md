# Command Selection

Use the repo-review CLI as the machine-readable substrate, not as the user
experience.

## Discover Before Acting

Run `repo-review agent-context --json` before selecting workflow commands. If
the current repository has an executable `./repo-review`, prefer it over a PATH
binary so the skill and CLI contracts come from the same checkout.

The `agent-context` response is authoritative for:

- commands and subcommands
- flags and enum values
- artifact schemas
- review-run statuses and transitions
- delivery schemes
- helper template paths
- async support or deferred capabilities

## Prefer Workflow Commands

Use workflow commands before low-level primitives when the workflow command
exists in `agent-context`.

For delta update work, prefer:

- `review start` to create or reuse a durable run
- `review continue` to inspect or apply safe next actions
- `review package` or workflow packaging behavior to produce reviewer packets
- `review ingest` to attach or ingest reviewer output
- `review finish` to complete finishable runs

Use lower-level `diff`, `impact`, `export-prompt`, `ingest`, and `drift`
commands only when the workflow command is absent, insufficient, or the
reference for the current task explicitly calls for the primitive.

## Compatibility Errors

If a required command, flag, schema, status, transition, or delivery scheme is
missing, stop and report a compatibility error. The error should name the
missing capability and state that the installed skill and CLI are out of sync.

Do not continue by assembling undocumented command recipes. That risks mutating
review state with contracts the installed CLI does not guarantee.
