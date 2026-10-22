# Prepared Review

Prepared Review supplies mechanical source facts before the agent starts its analysis. It is an optional method in repo-review. Direct Review remains available without a prepass.

Both methods use the same analytical prompts and report schema. Method, agent, model, and reasoning setting are separate choices. Either method can produce different useful findings under different settings.

## Select a method

| Method | Starting information | Source access |
|---|---|---|
| Direct Review | Current pass, output style, and user context | The agent's usual source tools |
| Prepared Review | The same instructions, plus mechanical facts and coverage limits | Indexed lookup and question-based reads from captured source |

Prepared Review uses the candidate-2 design evaluated on cli-printing-press and last30days. Its policy tells the agent to use completed counts and locations, select important behavioral questions, and examine source for answers. The policy is part of this method.

## Prepare the source

Use [the setup guide](PREPASS_SETUP.md) to record installed tools. Then use [the workflow guide](PREPASS_WORKFLOW.md) to prepare a repository, check the packet, and deliver one pass at a time.

The entry point is `tools/prepass/prepare_review.py`. It can prepare evidence, check it, print a handoff, and write an MCP connection. It does not start a model or run subject programs.

Preparation records these facts:

- Selected source paths, hashes, byte sizes, languages, and physical line counts.
- Declaration names and locations.
- Broad text and syntax leads.
- Static Python import candidates.
- JavaScript and TypeScript import evidence when the optional tools are supplied.
- Go declarations, call spellings, import candidates, and reverse import candidates.
- Small Go packages that meet explicit size, parse, and dependency rules.

The compact packet has a limit of 3,000 `o200k_base` tokens. Full tables and source remain outside that limit. This is a size measure, not model token usage.

## Understand selection and coverage

The packet gives priority to entry and check names such as `Validate`, `Verify`, `Gate`, `Check`, `Command`, and `Handler`. Its compact lists omit test, fixture, example, and vendor paths by name. The full index retains those files. These path rules do not prove production use.

The small-package list applies to Go. A package needs complete physical counts, a known module root, no Go parse failures, at most 1,200 production lines, and at most two local dependency candidates. These rules identify places to inspect. They do not establish extraction value.

Go build tags are not evaluated. External imports are not resolved. Call spellings do not form a resolved runtime call graph. Go template bodies are not parsed as Go source. Missing graph coverage means unknown coverage.

A packet can finish with partial source or component coverage. Its limits remain visible. `--strict` requires complete captured source under the selection policy. It does not prove complete language analysis or a good review.

## Use source to support claims

`lookup` locates paths, symbols, imports, calls, modules, text, and leads. `read_source` requires a behavioral question. Each response has a 16,384-byte limit. Large files need explicit line ranges.

Packet facts and lookup results give no complete-file reading credit. Only a compatible host can confirm delivery of exact source bytes. Hosts without that adapter leave coverage unconfirmed. Delivery does not prove attention or understanding.

A partial source read cannot establish that a test or mechanism is absent. Keep that limit in the report's source-state and confidence fields.

Later passes remain optional. Pass 02.5 remains composition. Twin source is available through the service only during pass 04. The integration does not add Prepared Review support to pass 06.

## Read the supporting guides

- [Workflow](PREPASS_WORKFLOW.md): new sources, existing packages, handoff, and recovery.
- [Setup](PREPASS_SETUP.md): local tools, manifests, and terminal acceptance.
- [Host interface](PREPASS_HOST.md): MCP and delivery confirmation.
- [Evidence](PREPASS_EVIDENCE.md): evaluated design, results, and limits.

The older `prepass.py` and trial scripts remain local research files outside this integration commit. Their command and output formats differ from Prepared Review. They are not required by a clean checkout.
