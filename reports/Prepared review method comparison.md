# Compare the two review methods

Date: October 22, 2026.

The candidate is a useful alternative review method. It changes the questions that receive attention and can produce useful extraction ideas that the baseline does not select. Matching the baseline's extraction list is not a quality requirement.

My earlier assessment gave too much weight to baseline findings that the candidate omitted. That was an unsuitable measure for discovery. The correct test is whether each selected idea has source support, a useful independent purpose, and a credible account of its boundaries. A different selection can improve the combined discovery result.

The evidence covers all 24 reports: six stages, two methods, and two focal repositories. I also examined the preparation policy, packet construction, tool call records, resource totals, and selected source claims. No model review, build, source execution, or native test suite ran for this comparison. The [evidence record](/Users/dave/p/repo-review-prepass/candidates/candidate-2/method-comparison-evidence.json) identifies every report and its hash.

## What changes between the methods

Both methods use the same six analytical stages, the same saved source for each comparison, Sonnet 5.5, and Extra effort. The candidate adds a compact structural packet, an index, and a policy that tells the model to avoid repeating the file survey. Each source read must state a behavioral question. The baseline discovers paths through directory lists and text searches, then reads source.

This changes starting information and search discipline. It does not replace review judgment with static analysis. The candidate still chooses its thesis, trace obligation, comparison questions, and extraction options.

The candidate packet is selective. Its entry list favors names such as `Validate`, `Verify`, `Gate`, `Check`, `Command`, and `Handler`. Its small-module list is Go-specific. The compact lists omit tests, fixtures, examples, and vendor paths by path-name rules. Full indexes retain those paths. Generated Go template bodies are not parsed as Go source. These choices can affect initial attention. They do not determine the final choices. See the [packet policy and renderer](/Users/dave/p/repo-review-prepass/repo-review-prepass/tools/candidate2/packet.py:17) and [candidate tool definitions](/Users/dave/p/repo-review-prepass/repo-review-prepass/tools/candidate2/service.py:21).

The saved tool calls show this navigation pattern:

| Measure | CPP baseline | CPP candidate | L3 baseline | L3 candidate |
| --- | ---: | ---: | ---: | ---: |
| Source-read calls | 130 | 116 | 143 | 129 |
| Distinct source paths requested, including the comparison repo | 96 | 77 | 87 | 70 |
| Total tool calls | 247 | 258 | 208 | 239 |

The candidate requests fewer distinct source paths and makes more tool calls in both comparisons. Those extra calls are targeted lookups. This is evidence of a more selective navigation process. It does not prove greater depth or lower quality.

Most candidate lookups are for text and symbols. CPP has 81 text, 26 symbol, 29 path, three module, one call, and one heuristic-lead lookup. L3 has 60 text, 24 symbol, and 25 path lookups. There is little evidence that dependency graph queries caused the different reviews. The experiment changes the packet, policy, and tool interface together, so their separate effects are unknown.

## What CPP shows

CPP is a Go code-generation factory. It combines specifications, templates, hand-written commands, published output, and a long agent workflow. The selected source also includes much test and generated material. Its review problem includes both code structure and the consistency of several descriptions of the same workflow.

Both methods identify `APISpec` as central. Both choose `docs/SPEC-EXTENSIONS.md` in stage 02 and revise the account toward a two-syntax authoring contract. Both later trace the promise that printed commands use the real target rather than invent results. Both find that the main suspicious-command signal warns without blocking shipment. The candidate therefore retains important central findings. See [CPP baseline stage 02](/Users/dave/p/repo-review-prepass/candidates/candidate-2/cli-printing-press/reports/baseline/stage-02.md) and [CPP candidate stage 02](/Users/dave/p/repo-review-prepass/candidates/candidate-2/cli-printing-press/reports/candidate/stage-02.md), then [CPP baseline stage 03](/Users/dave/p/repo-review-prepass/candidates/candidate-2/cli-printing-press/reports/baseline/stage-03.md) and [CPP candidate stage 03](/Users/dave/p/repo-review-prepass/candidates/candidate-2/cli-printing-press/reports/candidate/stage-03.md).

The differences are useful. The baseline gives more attention to the complete product: generated and hand-written commands, skill consistency, and how changes reach published CLIs. Its lift selects a skill verifier, a Cobra-to-MCP bridge, a template drift classifier, and a workflow ledger.

The candidate gives more attention to the exact checks and state transitions. Its trace adds first-match verdict ordering, where a warning can precede a failure rule. Its lift selects a workflow ledger with Markdown conformance checks, a gate for bulk acceptance of scanner findings, and declaration-level regeneration merge. The ledger gate is a substantial discovery. It turns repeated agent triage failures into a reusable checking pattern. The source has both the original PII implementation and an adapted tools-audit implementation. This is stronger support for reuse than a small file alone. See [CPP candidate stage 05](/Users/dave/p/repo-review-prepass/candidates/candidate-2/cli-printing-press/reports/candidate/stage-05.md), [PII completion checks](/Users/dave/p/repo-review-prepass/candidates/candidate-2/cli-printing-press/records/code-analysis/data/focal/source/internal/artifacts/pii.go:1152), and [verdict ordering](/Users/dave/p/repo-review-prepass/candidates/candidate-2/cli-printing-press/records/code-analysis/data/focal/source/internal/pipeline/dogfood.go:2772).

I no longer count the omitted MCP bridge as evidence of lower candidate quality by itself. The baseline finds a useful integration component. The candidate finds a useful control mechanism. The skill verifier also remains a valid baseline option even if the candidate prefers a different approach to skill consistency. Selection and factual accuracy must be judged separately. See [CPP baseline stage 05](/Users/dave/p/repo-review-prepass/candidates/candidate-2/cli-printing-press/reports/baseline/stage-05.md).

The candidate also gives a useful account of regeneration coupling: tree copying, module paths, generated markers, Cobra registration restoration, owner handling, and syntax-tree overlay. Its first version is limited to read-only classification. That is useful planning detail. The difficulty labels in the two reports attach to somewhat different proposed scopes; they are not a controlled estimate of the same extraction.

## What L3 shows

L3 is mainly a Python network integration and ranking engine. The host model performs part of the product behavior through a large skill file. Correct behavior depends on source availability, ranking choices, host instructions, rendered text, and packaging. This is a different problem from a code-generation factory.

The candidate identifies the host/engine contract as central in stage 01. The baseline initially gives the typed query plan and rank fusion the central role. Both broaden their accounts after reading the full skill file in stage 02. Both find contradictions inside the runtime instructions. This contradicts a simple claim that the candidate sees code while the baseline sees prose. Both methods can treat Markdown as executable product behavior. See [L3 baseline stage 01](/Users/dave/p/repo-review-prepass/candidates/candidate-2/last30days/runs/run-20261021-162639-78d777/reports/baseline/stage-01.md), [L3 candidate stage 01](/Users/dave/p/repo-review-prepass/candidates/candidate-2/last30days/runs/run-20261021-162639-78d777/reports/candidate/stage-01.md), [L3 baseline stage 02](/Users/dave/p/repo-review-prepass/candidates/candidate-2/last30days/runs/run-20261021-162639-78d777/reports/baseline/stage-02.md), and [L3 candidate stage 02](/Users/dave/p/repo-review-prepass/candidates/candidate-2/last30days/runs/run-20261021-162639-78d777/reports/candidate/stage-02.md).

Stage 03 is the main difference. The baseline traces the engagement-first product promise. It asks whether the engine's ranking policy matches that promise. The candidate traces failed-source disclosure. It asks whether a failure recorded in typed state is still visible after rendering and host synthesis. These are different, important questions.

The candidate's trace is especially useful. A test deliberately omits a failed zero-item source from the user footer while retaining the failure in evidence for the host. The candidate follows this through the host rules, status defaults, strict exit handling, and evaluation coverage. It exposes a boundary where good internal state does not itself establish good user disclosure. The report cannot prove how a real host resolves the conflicting instructions because no host transcripts are supplied. The source supports the risk and the boundary analysis. See [L3 candidate stage 03](/Users/dave/p/repo-review-prepass/candidates/candidate-2/last30days/runs/run-20261021-162639-78d777/reports/candidate/stage-03.md) and the [footer test](/Users/dave/p/repo-review-prepass/candidates/candidate-2/last30days/records/code-analysis/run-20261021-161839-4b7fcc/packet/data/focal/source/tests/test_render_footer.py:79).

The baseline trace remains useful for product policy. It connects ranking code to the engagement-first claim and distinguishes research mode from discovery mode. Its numerical account needs care: coefficients at different ranking stages are not a measured percentage of total ranking influence. Candidate selection, rank fusion, and later filtering also affect the result. Neither review measures ranking quality on real data. See [L3 baseline stage 03](/Users/dave/p/repo-review-prepass/candidates/candidate-2/last30days/runs/run-20261021-162639-78d777/reports/baseline/stage-03.md).

Those choices carry into the lifts. The baseline selects typed HTTP failure capture, bounded daemon workers, checkpoint handoff, and an evidence threshold before ranking. The candidate selects replay with evaluation checks, source outcome records, checkpoint handoff, and an AST check for required call arguments. The candidate's evaluation thresholds for each fixture and explicit outcome merge rules are substantial additions. Its call checker is a useful small convention-enforcement pattern. A requirement to reproduce the baseline's worker utility or evidence threshold would suppress this useful difference. See [L3 baseline stage 05](/Users/dave/p/repo-review-prepass/candidates/candidate-2/last30days/runs/run-20261021-162639-78d777/reports/baseline/stage-05.md) and [L3 candidate stage 05](/Users/dave/p/repo-review-prepass/candidates/candidate-2/last30days/runs/run-20261021-162639-78d777/reports/candidate/stage-05.md).

For discovery of reusable checks and protocols, I no longer have a basis for a general baseline preference on L3. The candidate is at least a strong alternative, and it can be the more useful selection for a reader interested in those mechanisms.

## Strengths and failure modes

The baseline tends to preserve more product and integration context in these runs. It follows architectural explanations, user promises, and examples toward transferable components. That is useful when the interesting part is how a product combines capabilities. Its costs are broader reading, repeated orientation, and a risk of judging implementation against an early headline too narrowly.

The candidate tends to produce a more explicit account of contracts, transitions, checks, and failure handling. It is useful when the interesting part is how a system keeps a workflow reliable. Its costs are many small lookups, selective source coverage, and a risk of treating a narrow search as sufficient evidence of absence. These are tendencies in this sample. Both methods also show the other method's strengths.

The L3 engagement-test error is a clear example of the candidate risk. The stage 05 read covered lines 500–600 of `test_rerank_v3.py`. The relevant test is at line 63. The report then said no test varies engagement. The index contained the file; the reading strategy did not establish the absence claim. This is a factual error, not a reason to reject its four extraction ideas. See the [delivered read record](/Users/dave/p/repo-review-prepass/candidates/candidate-2/last30days/runs/run-20261021-162639-78d777/records/reviews/candidate2/passes/05/attempt-001/produced/8d03caac83054cf6a0821f68326cf253.json) and [counterexample test](/Users/dave/p/repo-review-prepass/candidates/candidate-2/last30days/records/code-analysis/run-20261021-161839-4b7fcc/packet/data/focal/source/tests/test_rerank_v3.py:63).

The baseline has its own source error. Its L3 lift says an abandoned worker holds a semaphore slot that affects later batches. The semaphore is local to each invocation. Later batches can overlap with abandoned work, but do not share its semaphore. See the [local semaphore](/Users/dave/p/repo-review-prepass/candidates/candidate-2/last30days/records/code-analysis/run-20261021-161839-4b7fcc/packet/data/focal/source/skills/last30days/scripts/lib/pipeline.py:922). Neither method can establish absence from a small source sample. Neither replaces execution.

Both methods are affected by early question selection. Stage 02.5 adds no new source evidence. It consolidates the earlier account. Later stages then select one trace and one unresolved question at a time. This makes a sensible early difference productive across the sequence. It can also preserve a weak assumption. Different lifts are partly the result of these accumulated choices, not just the final extraction prompt.

## Predictions for other repositories

These are predictions from the mechanism and the two observed pairs. They are not measured class-level results.

| Repository characteristic | Expected method fit | Main limit |
| --- | --- | --- |
| Large repository with clear modules, declarations, and many entry points | Candidate should reduce initial orientation work. CPP supports this prediction. | Reliable locations do not establish behavior or extraction value. |
| Stateful workflows, ledgers, validators, recovery paths, or many policy checks | Candidate is likely to find reusable control and verification mechanisms. | It can overvalue checks that establish form but do not establish truth. |
| CLI integrations, emitted templates, wrappers, and useful combinations of several components | Baseline browsing can find useful integration components. Candidate remains useful when it deliberately enters those files. | The current Go parser does not parse template bodies. |
| Large prose contracts coupled to code | Both methods can work well. Both found the important large document in both repos. | Neither establishes actual model compliance from the instructions alone. |
| Small repository whose important source fits in context | Little expected advantage from a separate structural packet. | Preparation and lookup overhead may exceed the orientation saving. |
| Dynamic registration, reflection, plugins, or weak static index coverage | Candidate structural guidance becomes less informative; broad baseline browsing remains useful. | Neither interface resolves runtime behavior by itself. |
| Numerical libraries, ranking systems, scientific code, or benchmark-led products | Baseline may ask useful questions about the domain promise. Candidate may map the implementation and test mechanisms well. | Both need domain checks and execution to judge numerical validity or real output quality. |

Language alone is a poor selector. The current implementation has a richer Go package analysis, which is a plausible advantage for CPP. But the L3 candidate still produced a strong cross-layer trace and useful Python extraction ideas. Its best findings did not depend on Go module queries.

## Resource use and limits of inference

The fixed-rate model cost was 11.3% lower for CPP and 2.25% higher for L3. These are estimates, not billing records. L3 includes a usage stop and resume, with a fresh cache write after the wait. Preparation cost is outside these model totals. See the [CPP resource record](/Users/dave/p/repo-review-prepass/candidates/candidate-2/cli-printing-press/records/model-review/comparison.json) and [L3 resource record](/Users/dave/p/repo-review-prepass/candidates/candidate-2/last30days/runs/run-20261021-162639-78d777/records/comparison.json).

The stage pattern is informative. CPP candidate stages 01 and 02 together cost 40.5% less, but stages 03–05 together cost 16.8% more. L3 has the reverse pattern: its early stages cost more, including the interruption, while stages 03–05 cost 22.9% less. The candidate is not uniformly cheaper at every stage. The cost of establishing an account and the cost of developing it can move in different directions.

There is one completed sequence per method per repository. This does not separate method effects from model variation, cache state, order, and early question choice. Also, CPP and L3 share an agent-workflow environment and a preference for explicit rules and checks. L3 even invokes Printing Press for MCP bundle packaging. They are different products, but do not cover the range of ordinary libraries, services, scientific systems, or sparse legacy code. See the [L3 packaging instructions](/Users/dave/p/repo-review-prepass/candidates/candidate-2/last30days/records/code-analysis/run-20261021-161839-4b7fcc/packet/data/focal/source/mcp/README.md:24).

## Revised decision

Keep the two review methods distinct. Judge each artifact by source support, useful discovery, extraction boundaries, and the reader's goal. Use overlap to identify common findings, not as a quality score. Count an omission against a review only when it breaks its stated scope or leaves a critical claim unsupported.

For finding reusable control mechanisms and verification patterns, the candidate has a strong case in both repositories. For a broader account of product semantics and integration opportunities, the baseline remains useful. Neither method has established universal superiority.

A candidate artifact can be more useful and still fail the experiment's cost requirement. The L3 candidate did not meet the 10% cost reduction requirement. That result does not establish that its lift is worse. My earlier assessment did not keep these judgments separate enough.
