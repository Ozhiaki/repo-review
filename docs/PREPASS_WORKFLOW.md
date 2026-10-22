# Run a Prepared Review

Set up the local tools before preparation. All examples below start at the repo-review repository root. Replace uppercase paths with your own absolute paths.

## Prepare a new repository

`REPO` is the target Git repository root. `OUT` must be a fresh directory outside repo-review, the target, and other protected inputs. `TOOLS_JSON` is the manifest from [setup](PREPASS_SETUP.md).

```sh
uv run tools/prepass/prepare_review.py prepare REPO OUT --tools TOOLS_JSON
```

The command captures selected tracked and non-ignored untracked files. It records ignored paths, missing content, links, submodules, LFS pointers, and read errors. It does not follow source links or fetch missing content. The fixed file read limit is 32 MiB.

Preparation checks source before and after capture and after extraction. This is not an atomic snapshot. A source change during preparation causes failure.

The command computes declarations, broad and syntax leads, imports, and Go facts. It builds only its own static Go parser when Go files are selected. It does not compile or execute the subject.

For Python layouts, repeat `--python-root` with project-relative import roots. The default is `.`. For TypeScript, use `--tsconfig` with a selected project-relative file. Runtime import changes remain outside static coverage.

An optional twin can be prepared at the same time:

```sh
uv run tools/prepass/prepare_review.py prepare REPO OUT --tools TOOLS_JSON --twin TWIN_REPO
```

The twin has separate `--twin-python-root` and `--twin-tsconfig` options. It is not exposed to earlier passes. The operator can prepare a new packet with a twin later. Reuse the same focal source package to retain its exact source identity.

## Reuse a sealed evidence package

`PACKAGE` is a source package with `evidence/inventory.json`, captured source, counts, and an evidence seal. This is the common prepass package format, not a completed review packet.

```sh
uv run tools/prepass/prepare_review.py prepare --package PACKAGE --out OUT --tools TOOLS_JSON
```

Add `--twin-package TWIN_PACKAGE` when needed. Source and evidence in the input packages remain unchanged. Missing mechanical records are computed in a private derivative.

If all required declaration, syntax, and broad records already exist, `--tools` can be omitted. Python imports can be computed with the standard library. Missing JavaScript tools leave explicit unknown graph coverage. Selected Go source still requires the installed Go compiler.

The old candidate-2 tool bundle is not the new static tool manifest. Record the required installed tool paths with the setup command. Do not edit sealed experiment manifests.

## Check the result

Read `OUT/status.json`. State `complete` means preparation finished. It does not mean every source or language component has complete coverage. Read the recorded limits.

Use these checks:

```sh
uv run tools/prepass/prepare_review.py check OUT
uv run tools/prepass/prepare_review.py check OUT --live
```

The first command checks the prepared bytes, source tables, packet, processing inputs, and tools. The second also checks the original live checkouts. It returns nonzero if a checkout changed or cannot be checked.

A valid snapshot can remain usable after the checkout changes. State that the review concerns the snapshot. Prepare again when the user wants the changed source. Do not describe old captured bytes as the changed checkout.

Preparation preserves an unknown dirty state when the input does not establish it. A commit identifier alone does not identify uncommitted content.

## Deliver the current pass

Print the handoff for pass 01:

```sh
uv run tools/prepass/prepare_review.py handoff OUT --pass 01
```

Give that text to the agent. The handoff includes the output style and only the selected analytical prompt. Pass 01 includes the focal packet. Pass 04 includes the twin packet.

Use `02`, `02.5`, `03`, `04`, or `05` when you choose those passes. Keep later prompts closed until their turn. Keep the agent's own earlier reports available. Do not supply reports from another review unless you intend that extra context.

## Connect source tools

`REVIEW_STATE` is a separate directory outside the packet and protected inputs.

```sh
uv run tools/prepass/prepare_review.py connect OUT --state REVIEW_STATE --pass 01
```

The command prints a connection file. Load it with a compatible MCP host. It does not start a host, server, or model. The configured host can start the service when it connects.

For later passes, repeat the command with the same state directory and the selected pass. Each connection gets a new attempt directory. The service retains prior source captures and pass call counts. Restarting a service does not restore its call budget.

Optional `--agent`, `--model`, and `--reasoning` values record caller-stated settings when the state directory is first created. They do not select a model or verify actual use. Start separate state for another independent review. A changed source or policy cannot reuse the old state.

Read [the host interface](PREPASS_HOST.md) for delivery confirmation. A connection by itself does not confirm delivery.

## Locate the records

The packet directory contains:

```text
OUT/
  status.json
  preparation.json
  manifest.sha256.json
  review-instructions.md
  instructions/             Operator-held prompts; handoff selects one
  data/focal/               packet.md, tables.json, source, and full records
  data/twin/                Optional comparison source
  packages/                 Fresh source captures
  work/                     Private completed mechanical packages
  commands/                 Native command inputs, output, and exits
  native/                   Static Go parser, when needed
```

Mutable connection and delivery records belong in `REVIEW_STATE`. Do not add them to the sealed packet. Do not edit a sealed record to make a check pass.

Preparation has a one-hour total command budget and a ten-minute command limit by default. Use `--total-timeout` and `--command-timeout` to change them before preparation. Long commands report progress. Ctrl-C stops the active child process group. Failed and interrupted output remains available. Select a new output directory for another preparation attempt.
