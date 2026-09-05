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
