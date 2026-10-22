# Set up Prepared Review

Run installation, setup, builds, and acceptance in your terminal. Production preparation does not install tools, download embedding weights, or build subject code.

## Supply the local tools

The retained extraction policy uses these versions:

| Tool | Version | Use |
|---|---|---|
| Python | 3.12 or later | Preparation runtime |
| tiktoken | 0.12.0 | Packet and lookup size limits |
| Git | Installed local version, hash recorded | Source scope and freshness |
| ripgrep | 15.1.0 | Broad text leads |
| ast-grep | 0.41.1 | Declarations and syntax leads |
| Go | Installed local compiler, hash and version recorded | Build the static parser when selected Go files exist |
| Node | 22.23.3, optional | JavaScript import extraction |
| dependency-cruiser | 17.3.3, optional | JavaScript and TypeScript import evidence |
| TypeScript | 5.9.3, with dependency-cruiser | TypeScript analysis support |

Use `uv` to supply the script's declared Python and tokenizer dependency. Cache the `o200k_base` encoding during setup if preparation must run offline:

```sh
uv run --with tiktoken==0.12.0 python -c 'import tiktoken; tiktoken.get_encoding("o200k_base")'
```

Tool installation is separate from the commands below. Use your local package or tool setup to obtain the listed versions. The repository does not add a tool installer. Go compiler and module downloads are disabled when it builds the static parser.

Prepared Review does not require Colgrep, Zoekt, Ctags, or an embedding model. The retained advanced source-package runtime can still use the earlier retrieval pipeline through `source_package.py`, with its separate full bundle. That is not part of the normal Prepared Review setup.

## Record the installed static tools

`TOOLS_DIR` must be a fresh directory outside repo-review and the installed tool inputs. This command checks tool versions and writes `TOOLS_DIR/tools.json`:

```sh
uv run tools/prepass/prepare_review.py tools --out TOOLS_DIR
```

The default executable names are `rg` and `ast-grep`. Use `--rg PATH` and `--ast-grep PATH` for explicit binaries.

For JavaScript and TypeScript, supply the Node executable and the complete local `node_modules` directory containing dependency-cruiser and TypeScript:

```sh
uv run tools/prepass/prepare_review.py tools --out TOOLS_DIR --node NODE_PATH --node-modules NODE_MODULES
```

The manifest records absolute local paths, file hashes, tool versions, and the support directory hash. Preparation rechecks them. Changed or missing inputs cause failure. Create a new manifest after an intentional tool change. Do not modify an old sealed experiment bundle.

Without the optional Node pair, selected JavaScript files retain explicit unavailable graph coverage. Counts, source reads, and supported declarations remain available.

## Run mechanical acceptance

Integration acceptance passed on 2026-10-22 in run `prepared-acceptance-20261022-160701-545328`. All ten registered checks passed. The saved-record audit verified 21 command results, 792 artifacts, and 145 current processing inputs. The native fixtures cover Go and Python. The optional JavaScript graph was not exercised.

Acceptance is an integration check. It is not required before each review. Repeat it after a relevant implementation or environment change.

From the repo-review root, use this command:

```sh
uv run tools/prepass/accept_prepared_review.py
```

It records the installed `rg` and `ast-grep` automatically. It also needs Git and Go. Use `--tools TOOLS_JSON` to supply an existing Prepared Review manifest. `--go PATH`, `--node PATH`, and `--node-modules DIR` select explicit local tools when a new manifest is recorded.

Acceptance runs the existing prompt and schema checks, common source checks, the promoted 18 packet tests, nine robustness tests, and eight integration boundary tests. It prepares private Go and Python fixtures and a twin. It checks package reuse, handoffs, source preservation, and snapshot versus live freshness. It starts no model and executes no subject program.

The command writes a fresh output directory beside repo-review. `--out DIR` selects another fresh path. Read `verdict.md`, `status.json`, `checks.json`, and the command records. A failure remains a failure. Missing required tools do not count as a pass.

The total command budget is one hour. Each acceptance command has a ten-minute limit. Ctrl-C stops the active child process group. Keep failed output for diagnosis.

The CI job runs deterministic packet, workflow, and source tests with declared Python, tokenizer, and Go setup. The terminal acceptance command also checks the installed native extraction path. Neither result measures review quality or model cost.
