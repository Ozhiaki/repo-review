# Prepared Review source map

Prepared Review promotes the candidate-2 source design evaluated on 2026-10-22. The code and guides are included in this repository. Original experiment records remain in the local `/Users/dave/p/repo-review-prepass/` workspace. That workspace is not a runtime dependency.

## Promoted files

Source paths below are relative to the original candidate code root, `/Users/dave/p/repo-review-prepass/repo-review-prepass/`. The method comparison came from its parent evidence workspace. SHA-256 values identify the original source bytes before adaptation.

| Repository file | Original source | Original SHA-256 |
|---|---|---|
| `tools/prepass/prepass_runtime/__init__.py` | `tools/prepass/prepass_runtime/__init__.py` | `cbc1cd8b463137a78b7d4e60307f534a805c6a277a2225819544d5ac29220c70` |
| `tools/prepass/prepass_runtime/adapters.py` | `tools/prepass/prepass_runtime/adapters.py` | `573dc2af1b6e769b9a77315d618d930451e3a57a927e1eb8607372fc07fe032d` |
| `tools/prepass/prepass_runtime/assets/syntax.yaml` | `tools/prepass/prepass_runtime/assets/syntax.yaml` | `be7eb19b84517c795ff6bb0eaded68938a4700dab2ebc3d2fbae4b187477ed3b` |
| `tools/prepass/prepass_runtime/catalog.py` | `tools/prepass/prepass_runtime/catalog.py` | `7d8d414947254ab96b9c254112485307bff89f62aceeb306872b94feafa30e3f` |
| `tools/prepass/prepass_runtime/cli.py` | `tools/prepass/prepass_runtime/cli.py` | `881d9a97d10709cdc239b4a979f54ab7dd8bdcb4e4757063f38d3ac382b2185d` |
| `tools/prepass/prepass_runtime/declarations.py` | `tools/prepass/prepass_runtime/declarations.py` | `2fdc78c3567b19c1a0bc4168db3d1057368f4ee7497135dbbf13f06ca396114c` |
| `tools/prepass/prepass_runtime/delivery.py` | `tools/prepass/prepass_runtime/delivery.py` | `432f3891afee3800f4098c0269e84f0f0394130129f6f81d1ca0910e371dd291` |
| `tools/prepass/prepass_runtime/ledger.py` | `tools/prepass/prepass_runtime/ledger.py` | `21a908c05ce3dd86c723cff398312ef134deb4ab27568d78b0bb28377b2f303c` |
| `tools/prepass/prepass_runtime/lexical.py` | `tools/prepass/prepass_runtime/lexical.py` | `60666519d9031a5f514ef86116720dad56c3af3afd5d766d4cfa650937220c08` |
| `tools/prepass/prepass_runtime/merge.py` | `tools/prepass/prepass_runtime/merge.py` | `1fea8d7e6d4334cc3718ad22a2c5de28f4de967e7ad1f23d94bee507079d3aea` |
| `tools/prepass/prepass_runtime/package.py` | `tools/prepass/prepass_runtime/package.py` | `0701fb1a5f2b94f7de832f4a3dd8bf010423a104251f93104c7dc2637fc7bcd2` |
| `tools/prepass/prepass_runtime/pipeline.py` | `tools/prepass/prepass_runtime/pipeline.py` | `ab45c3ef57ed772a96d566cda5a7c08320a57e72acf017fe3f2e34a9a97d8aad` |
| `tools/prepass/prepass_runtime/python_imports.py` | `tools/prepass/prepass_runtime/python_imports.py` | `6eb5cfb2d39182deeff8e5193af43176a390a57ef7e398d206761a72b33f77bf` |
| `tools/prepass/prepass_runtime/records.py` | `tools/prepass/prepass_runtime/records.py` | `92b51d65da1862952dfbd55a2e164067a74750497556edc9e1c1ea0dbb11a7fd` |
| `tools/prepass/prepass_runtime/scope.py` | `tools/prepass/prepass_runtime/scope.py` | `3f42fcb8fe9effabff2fe3fe0060d5e4d88c093bce10e4da15609e30da242595` |
| `tools/prepass/prepass_runtime/search.py` | `tools/prepass/prepass_runtime/search.py` | `2b3df4996152fc97c619f41c098f5ef3095173785c63801b1b97c0f0d893dbd7` |
| `tools/prepass/prepass_runtime/selection.py` | `tools/prepass/prepass_runtime/selection.py` | `0eebd5d9fcb91f05ecd3c77ba8b79580592c14396b414b03144758b201aeebe2` |
| `tools/prepass/prepass_runtime/tokens.py` | `tools/prepass/prepass_runtime/tokens.py` | `d22f49081560a08ddadd4b2698be0441ecefd38f8ab2c859951e60687eeac05d` |
| `tools/prepass/prepass_runtime/toolchain.py` | `tools/prepass/prepass_runtime/toolchain.py` | `cea00910075c3d83450e9a7c270a925b5633efb3055e2b2b0bbdf14dbf60f003` |
| `tools/prepass/prepared_review/__init__.py` | `tools/candidate2/__init__.py` | `95488fc91c55a7ae1da6f2cd1d44a88e9e8143aed0f81cf7b0524c57e1c7b1ce` |
| `tools/prepass/prepared_review/packet.py` | `tools/candidate2/packet.py` | `f2493e6195b2837a55d6926ca7556d5fdba1ef801ff713e9f428d23b34044266` |
| `tools/prepass/prepared_review/service.py` | `tools/candidate2/service.py` | `891db6746440aab2d5ef14a7ee8de2128543796270679e36a14754b11e417e02` |
| `tools/prepass/prepared_review/go_facts.go` | `tools/candidate2/go_facts.go` | `2743e33b042a3b16125cba2ab0294b199641e2996fe120b3637cc2e309404f2a` |
| `tools/prepass/prepared_review/artifacts.py` | `tools/review_comparison/artifacts.py` | `10f38f8ec14463d00c057857c0e1fca9746c50ca1cc29af63d3a298eee212347` |
| `tests/run_prepared_review_tests.py` | `tests/run_candidate2_tests.py` | `1f67621b208ca743c31690ea8bdabefa120f4fdd9eef2a6f57c5cc1c75935d5a` |
| `tests/run_prepared_review_robustness_tests.py` | `tests/run_candidate2_robustness_tests.py` | `c66e38220a740af4cbf6feda7758cf3b3bc6ff73acbcaf8866e7b4c7e2a3bdad` |
| `tests/run_prepared_source_tests.py` | `tests/run_prepass_runtime_tests.py` | `8cf38b67a1389af700faf9c42bc680500f222e78f282683f658eef03036a8a71` |
| `tools/prepass/prepared_review/cli.py` | `tools/candidate2/cli.py` | `75f3af0a41599c2afe7da8020d51e06b2fd8cd1acb848ff6a9a31343d342fbfd` |
| `tools/prepass/prepared_review/validation.py` | `tools/candidate2_checks.py` | `2661081556d5de71e02e5eccc66249f461953d46b6a9741265bc41a8dea3eed1` |
| `tools/prepass/prepared_review/host_capture.py` | `tools/review_comparison/host.py` | `8f4551769776a5c1db6bf4762de72862b0612d97ddeeaff13b0e7493ee6c6194` |
| `tools/prepass/prepared_review/instructions.py` | `tools/review_comparison/protocol.py` | `df40ebc4807817cda1a42d7431c015e1fcb3d0216b88a2f22b2c317236690986` |
| `tools/prepass/source_package.py` | `tools/prepass/prepass.py` | `e11ab19418cc15fb3b1f5fb4c3204ba88650bfd43c83172acbaa7cb328ca07c8` |
| `reports/Prepared review method comparison.md` | `/Users/dave/p/repo-review-prepass/candidates/candidate-2/method-comparison.md` | `2f5aaa7457ee758e683243887fef820dc0effc58c1a508a30a3fffe11f111994` |

## Adaptation and verification

The common source runtime, static Go parser, packet selection policy, and source tools come from the candidate design. New integration code supplies generic input selection, component-specific tool manifests, preparation composition, current-pass instructions, and host capture without a model launcher.

The packet title uses Prepared Review. Source seals use the common package producer's complete regular-file policy. Scope and file classifications are checked. Service restarts retain recorded pass call counts. Strict source completeness is optional for ordinary reviews.

The method comparison is copied without changes. Original raw responses, source packages, paid reports, and their seals remain unchanged outside this checkout. Earlier trial code and unrelated research are not included in the integration commit.

Local run `prepared-acceptance-20261022-160701-545328` passed all ten acceptance checks. Its saved-record audit verified 21 command results, 792 sealed artifacts, 145 processing inputs, and all 33 promoted source and target file hashes. The earlier failed run remains unchanged.

The fixtures cover Go and Python. They do not exercise the optional JavaScript graph. No model was called. Acceptance does not measure review quality or model cost.

The exact per-file adaptation and original working-tree records remain in the local `research_notes/Prepared review integration/2026-10-22/` directory. The supported checkout does not need them. For repeatable mechanical checks, use [the setup guide](PREPASS_SETUP.md#run-mechanical-acceptance).
