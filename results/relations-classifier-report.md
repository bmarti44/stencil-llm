Data lineage: fit-on = Kimi + Astra/Opus enrichment after merged patch; calibrated-on = scenario-disjoint 10% dev split; evaluated-on = author-disjoint Fable held-out, seed 0 once after all freezes. No benchmark inputs/responses used; admission head not trained.

# Relations classifier — 2026-09-05

Kimi: 5,386 → 5,265 retained (121 union drops); enrichment 320 + 322, including 60 inactive-target corrections. Dedup removes 143 rows, leaving 5,764 pairs; each seed uses 5,188 fit / 576 dev. All input files remain unchanged.

| Label | Patched Kimi | Effective Kimi + enrich |
|---|---:|---:|
| none | 2,335 | 2,592 |
| supersedes | 982 | 1,060 |
| cancels | 699 | 723 |
| completes | 640 | 704 |
| reinstates | 609 | 685 |

[All 227 disagreements and reasons](../data/classifier/review/relations-disagreements.md): 193 none, 23 supersedes, 6 cancels, 5 completes; 46 have explicit patches from both reviewers. Omitted patches otherwise retain original labels. Merged summary logs row identities, drop union, hashes and enrichment repairs; Astra-selected span text is preserved and offsets/admission strings normalized.

CPU BGE-small; seed 0 designated before scores. Pilot projected 109.2 CPU-minutes for three epochs, so all seeds were reduced to two before full fitting. Each then hit the cooperative fitting cap: 311/312/312 of 326 updates (partial second epoch), totaling 73.36/73.59/73.49 CPU-minutes for fit/calibration/save. Sequence cap stays 512; no fit or held-out overflows. Pilot cost 1.26 CPU-minutes; final inference cost 1.16 CPU-minutes.

Held-out: 594 pairs, plus one excluded metadata header; no admission-only rows and no dropped pairs. Registered-threshold accuracy **42.9%**; raw argmax accuracy **81.1%** (diagnostic only).

| Class | Support | Precision at thresholds | Recall at thresholds |
|---|---:|---:|---:|
| none | 255 | 42.9% | 100.0% |
| supersedes | 115 | — | 0.0% |
| cancels | 88 | — | 0.0% |
| completes | 67 | — | 0.0% |
| reinstates | 69 | — | 0.0% |

Confusion: gold rows / predicted columns, order none, supersedes, cancels, completes, reinstates.
```text
255   0   0   0   0
115   0   0   0   0
 88   0   0   0   0
 67   0   0   0   0
 69   0   0   0   0
```

Fail-safe operating point: all four positive thresholds = .98 (registered floor); calibrated empirical dev none-FP cap ≤ 2% per positive class. Held-out none-FP = **0/255 (0%)**, also 0/255 for each positive class; hard-negative slice = **0/234 (0%)**. Coverage = **0/594**, all 594 outputs none; positive precision is undefined (—). These zeros reflect abstention, not demonstrated transition safety. Raw argmax none-FP = 84/255 (32.9%).

| Dev seed | Argmax accuracy | Threshold accuracy | Positive predictions | None-FP |
|---:|---:|---:|---:|---:|
| 0 | 86.1% | 45.0% | 0/576 | 0/259 |
| 1 | 87.5% | 45.0% | 0/576 | 0/259 |
| 2 | 88.9% | 45.0% | 0/576 | 0/259 |

Two preflight attempts aborted before inference: shared “Undo that.” text across different targets, then two coarse duplicate keys whose prior-user contexts differ. Evaluation checks were repaired without changing data, fitting functions, weights or thresholds; all 594 full inputs are distinct. The third preflight succeeded and exactly ONE inference pass ran. Manifest preserves both abort receipts, frozen fitting source commit 10c2d39, source/artifact hashes and counters. Author/declared-relative/pair-fingerprint overlap is zero; semantic disjointness from inaccessible corpora is not proven.

**Not ready to drive the register in the [FOCUS-3 section-5 feasibility gate](focus3-design-astra.md#5-quick-feasibility-gate--frozen-reading-before-running-3-gpu-h).** At the registered operating point this checkpoint makes no updates, cancellations, completions or reinstatements. It is an offline pair scorer, not a working register or admission gate; abstention must not be treated as confident evidence of no relation. Admission, runtime authority/status/scope checks and the separate 64-episode gate remain untested. The available fit/dev/held-out counts also miss the prospective minima. No GPU gate or benchmark-transfer claim is made.

[Metrics and dev stability](../data/classifier/model/relations/metrics.json), [thresholds](../data/classifier/model/relations/thresholds.json), [manifest](../data/classifier/model/relations/manifest.json). Validation: 33 targeted tests passed, one expected failure; lint and exact reconciliation reproduction passed. Safetensors stay local; no push.

## Operating point revision — 2026-09-05

The preceding results describe the original CPU checkpoint and historical operating point. Brian's ruling for this revision: the 2% per-positive-class none-FP constraint was an **orchestrator-set development choice, not a science registration**. Held-out-1 was seen once, is now development history, and was not reopened or rescored here. **Held-out-2 remains untouched and reserved for a later final check.** This revision fits on the same patched Kimi + Astra/Opus data and calibrates/evaluates only on the original scenario-disjoint, author-shared DEV splits.

The old development configuration was unsuitable as a usefulness gate because it imposed a `.98` minimum confidence without a coverage requirement. The floor independently caused total abstention; it is inaccurate to attribute that solely to the 2% cap. On CPU seed-0 DEV, removing the floor while retaining 2% per-class FP allows thresholds `.94/.91/.87/.50`, recovering **229/317 positives (72.2%)** at **229/246 precision (93.1%)**. Relaxing to 5% trades some precision for more recall; neither empirical cap is a population safety guarantee.

The rule was frozen at **19:01 UTC, before GPU retraining and before any new held-out look**: choose each class's lowest cutoff on `.50, .51, …, .98` whose actual positive-argmax predictions produce at most `floor(.05 × DEV-none-count)` false positives on gold-none rows. Disable unsupported/infeasible classes at `1.01`. Require total **correct-positive recall ≥60%**. If that fails, choose the lowest single top-two probability margin on `.00, .01, …, .98` satisfying the same per-class FP caps and recall floor. If neither qualifies, retain the per-class policy and explicitly mark usefulness failed. Equality passes the cutoff; ties use fixed label order; overlength inputs abstain. Recalibrate this same rule on each original seed's DEV; seed 0 always supplies the model, with no seed selection.

Coverage denominators are explicit: emitted positives/all DEV; emitted positives on gold-positive rows/all gold positives; and correctly classified positives/all gold positives (the stricter 60% criterion). Per-class coverage is emitted class/all DEV, and per-class recall is correct class/gold class. Precision excludes abstentions; undefined precision is shown as —.

[CPU DEV sweep table](../data/classifier/model/relations/calibration/cpu-seed0-curve.md), [full CSV](../data/classifier/model/relations/calibration/cpu-seed0-curve.csv), and [PNG](../data/classifier/model/relations/calibration/cpu-seed0-curve.png) contain the probability and margin variants. Saved DEV logits and split/checkpoint hashes support reproduction.

| CPU seed-0 policy | Positive precision | Correct-positive recall | Emitted/all DEV | Combined none-FP |
|---|---:|---:|---:|---:|
| Old `.98` floor | — | 0/317 (0%) | 0/576 (0%) | 0/259 (0%) |
| 2% cap without `.98` floor (diagnostic) | 229/246 (93.1%) | 229/317 (72.2%) | 246/576 (42.7%) | 17/259 (6.6%) |
| **Chosen 5% per-class rule** | **283/322 (87.9%)** | **283/317 (89.3%)** | **322/576 (55.9%)** | **36/259 (13.9%)** |
| Margin `.80` (first feasible; diagnostic) | 280/305 (91.8%) | 280/317 (88.3%) | 305/576 (53.0%) | 25/259 (9.7%) |

Chosen CPU thresholds (supersedes/cancels/completes/reinstates): **.89/.50/.50/.50**, with none-FP counts **12/10/9/5 out of 259** (4.63%/3.86%/3.47%/1.93%). Gold-positive coverage is 286/317 (90.2%); correct-positive recall is 283/317. The 5% limit applies **separately to each class**, not to the combined 13.9% none-FP. The margin remains a fallback because the primary policy qualifies, even though its diagnostic precision is higher.

GPU retraining is pending the requested 600-second readiness polls, with a six-hour deadline of **2026-09-06 00:53 UTC**. It requires an empty NVIDIA compute-process list and, for each of check40/check41, a terminal reading or no live run script. Three complete epochs for seeds 0/1/2 are authorized once ready; otherwise retain CPU seed 0 with the frozen rule. Foreground execution only; no signals, held-out inference, benchmark inputs, WORKLOG edits, or push.

The authoritative revised consumer is `stencil.relation_operating_point.inputs` followed by `predict(probs, operating_point["policy"], overflow)`, using [operating-point.json](../data/classifier/model/relations/operating-point.json). The historical trainer's `.98` threshold consumer is not the revised policy. The separate admission head, runtime register guards, and 64-episode gate remain untested; DEV calibration does not establish readiness for deployment.
