# Calibration Notes

Target: `repo-review` at `77b7bd3`

Artifacts:

- `review.md`: compact full review prose.
- `review-state.json`: durable review state with claims, evidence refs, analyzer identity, and Drift Surfacer material.

## Result

The claim/evidence substrate is usable for a first calibration pass. No Phase 0 substrate changes are required from this calibration.

## Calibration Questions

**Did the claim rubric produce too many or too few claims?**

It produced a small useful set. Four claims were enough to capture central abstraction, substrate shift, trace obligation, and one extractable seed. More claims would mostly duplicate prose.

**Were evidence refs precise enough?**

Yes for this target. File plus locator was enough for a future agent to inspect each claim without reading the full review. Exact quotes helped but should remain optional because not every future artifact will have stable short quotes.

**Did structured claims preserve important prose judgments?**

Mostly yes. The `statement`, `confidence`, `invalidation_triggers`, and `produced_by_analyzer.notes` fields preserved the important nuance that operational enforcement is partial rather than absent.

**Could future diffs map to watch paths?**

Yes. The strongest claims map naturally to README/pass files, `docs/incremental-review.md`, schemas, CLI, and validators.

**Were invalidation triggers concrete enough to evaluate?**

Yes. The triggers are phrased as observable future conditions, such as a CLI exposing all prompts without prerequisite order.

**Did analyzer identity reveal useful differences?**

It did not reveal differences in this single-analyzer run, but it was still useful metadata. Calibration against Oathweaver or OverCR should test multi-session or model-different analyzer identity.

**Did Drift Surfacer material fit the substrate?**

Yes. Snapshot entries and fascination seeds could reference claims directly.

**Did schema structure distort the review?**

No. The main friction was not distortion; it was verbosity. Claim objects are long, but the length bought resumability and inspectability.

## Substrate Decision

No docs or schema changes are needed from this calibration. The current substrate should proceed to active-package delta work, with one caution: future tooling should generate claim scaffolds because hand-writing full claim objects is verbose.
