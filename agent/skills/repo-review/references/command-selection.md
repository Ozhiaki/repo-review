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

## Required Update Capabilities

For `/repo-review:update`, require these capabilities in `agent-context` before
starting the workflow:

- state discovery: `state latest`, `state list`, `state get`, or equivalent
  review-state resolution commands with `--json` and `--no-input`
- run creation or reuse: `review start` with `--mode`, `--repo`, `--range`,
  `--review-state`, `--json`, and `--no-input`
- run resumption: `review continue` with `--run` or `--latest`, `--json`, and
  `--no-input`
- prompt packaging: `review package` or an equivalent workflow-supported
  packaging command with file or stdout delivery metadata
- reviewer ingest: `review ingest` with `--run` or `--latest`, `--input`,
  `--json`, `--no-input`, and attach-only support for raw reviewer output
- run finish: `review finish` with `--run` or `--latest`, `--json`, and
  `--no-input`
- drift surfacing: a workflow transition or `drift surface` command that can
  produce `schemas/delta_drift.schema.json`
- local feedback: `feedback` with `--json` and `--no-input` so discovery
  friction can be recorded

Also require the CLI-declared `delta-review` artifact schema, including a
Markdown primary format with a required `delta_review` block or an equivalent
JSON schema contract.

## Required Statuses

For durable update runs, require status meanings for:

- `prompt_ready`
- `review_received`
- `ingested`
- `drift_ready`
- `complete`
- `blocked`
- `failed`

The skill may also use earlier setup statuses such as `created`, `diff_ready`,
and `impact_ready` when the CLI reports them.

Fallback handoffs should prefer a run in `prompt_ready` with a concrete packet
path. If a run is already `review_received` or `ingested`, use `review continue`
to determine whether the next resume instruction should be ingest, drift
surfacing, finish, or a human decision.

When a CLI response includes both a concrete `run.run_id` and a
`next_action.recommended_command` containing `<run-id>`, substitute the concrete
run id before presenting the command to the user. Record feedback only if the
response lacks the machine-readable run id or the substitution would be
ambiguous.

Discovery feedback converted into CLI work:

- `feedback-2026-05-29T124043480044Z0000` -> `rep-g7b.9`
- `feedback-2026-05-29T124217817051Z0000` -> `rep-g7b.10`
- `feedback-2026-05-29T124341923162Z0000` -> `rep-g7b.11`

Discovery feedback handled by skill instructions:

- `feedback-2026-05-29T124140712286Z0000`: non-blocking `<run-id>`
  placeholder in a recommended command where `run.run_id` is available.

## Error Shape

A compatibility refusal should be short and actionable:

```text
repo-review compatibility error: missing <capability>. This skill expects a CLI
that exposes <required command/flag/schema/status> through
`repo-review agent-context --json`; update the skill or CLI so they match.
```
