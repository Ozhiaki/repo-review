# Delta Review Runbook

This runbook is a local-agent execution harness for `06-delta-review.md`.

Use it when the prior review artifacts and the target repo are available on
disk. The point is to avoid pasting every prompt, artifact, diff, and file list
by hand. The agent should read the delta-review prompt as the analytical
authority, then derive the evidence locally.

## Inputs

Provide these values:

```text
review_artifact_dir: <directory containing prior repo-review outputs>
repo_dir: <local checkout of the reviewed repo>
baseline_ref: <commit/tag/archive/date or "derive from prior artifacts">
updated_ref: <commit/tag/archive/date or "current HEAD">
output_path: <where to write the delta-review artifact>
```

Optional:

```text
human_concern: <release, incident, feature, or concern motivating the delta>
```

## Execution Contract

The local agent should:

1. Read `06-delta-review.md`.
2. Read prior review artifacts from `review_artifact_dir`.
3. Treat prose as authority and structured appendices as claim indexes.
4. Derive `baseline_ref` from prior `source_state` fields when the user did
   not provide it explicitly.
5. Derive `updated_ref` from `repo_dir` when the user says `current HEAD`.
6. Generate git evidence locally:
   - worktree status
   - commit count
   - commit log
   - diff stat
   - changed-file list
7. Derive focused files mechanically:
   - extract repo-relative paths from prior structured appendices and prose
   - intersect those paths with changed files
   - inspect that intersection first
   - add high-churn or newly central files only as secondary evidence, and name
     why they were added
8. Produce only the delta-review output.
9. Save the result to `output_path`.

Do not paste or rerun the base pass prompts unless `06-delta-review.md`
concludes that a base rerun is required.

## Synthesis Handling

Official synthesis artifacts use:

```yaml
pass_output:
  pass_id: synthesis
```

Treat these as structured compositional prior outputs.

Legacy informal synthesis artifacts may use another root, such as
`synthesis_output`. Treat those as prose context unless the user asks for a
normalization pass. Do not force them into the official schema during delta
review.

## Reusable Prompt

```text
Read /Users/dave/p/repo-review/repo-review/06-delta-review.md.

Use the prior review artifacts in:
<review_artifact_dir>

Use the repo at:
<repo_dir>

Baseline source state is:
<baseline_ref or "derive from prior artifacts">

Updated source state is:
<updated_ref or "current HEAD">

Generate delta evidence from git locally. Derive focused files from prior
review artifact paths intersected with changed files. Treat official
`pass_output: pass_id: synthesis` artifacts as structured compositional prior
outputs. Treat legacy informal synthesis artifacts as prose context only.

Produce only the delta-review output and save it to:
<output_path>
```

## Minimal Verification

After the artifact is written, check that its YAML appendix includes:

```yaml
pass_output:
  pass_id: delta-review
  baseline_source_state:
  updated_source_state:
  prior_passes_consumed:
  change_window:
  materiality:
  incremental_review_sufficient:
  rerun_required:
  claim_updates:
```
