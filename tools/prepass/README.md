# Prepared Review source preparation

Prepared Review is the supported optional method. Direct Review uses the
original prompt workflow and needs no prepass.

The entry points are:

- `prepare_review.py`: record static tools, prepare source, check a packet,
  print the current pass, and connect an MCP source service.
- `accept_prepared_review.py`: run mechanical integration acceptance.
- `source_package.py`: advanced access to the common source package and the
  retained full retrieval pipeline, with its separate tool bundle.

Preparation starts no model and runs no subject program.

Read the [method guide](../../docs/PREPASS.md), [setup](../../docs/PREPASS_SETUP.md),
[workflow](../../docs/PREPASS_WORKFLOW.md), and [host interface](../../docs/PREPASS_HOST.md).
The [source map](../../docs/PREPASS_PROVENANCE.md) identifies promoted files.

The earlier experimental `prepass.py`, trial scripts, and research records
remain in the local workspace. They are outside this integration commit and
are not dependencies of Prepared Review.
