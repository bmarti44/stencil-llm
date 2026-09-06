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

## Retrain + held-out-2 — 2026-09-05 (completed 2026-09-06 UTC)

fit-on = kimi+enrich after merged patch; calibrated-on = dev (original seed-specific scenario-disjoint split, fit-author-shared); evaluated-on = held-out-2 once; held-out-1 = development; no benchmark inputs/responses; admission not trained.

This section supersedes the historical GPU-pending status above. The frozen rule and all 592 CPU curve rows reproduce from `b134f6f8`. All seeds retrained from the pinned base BGE encoder for **three full epochs, 489/489 updates**, using exactly the original patched inputs and seed-specific 5,188-fit/576-DEV splits. Foreground GPU training took 49.03/49.15/49.05 seconds (147.24 seconds total fit/calibration/save within the trainers); no budget truncation. The coordination flag was removed after natural completion. Historical CPU metadata and the original calibration curves are preserved.

All three seeds pass the unchanged DEV rule: at most 12/259 none false positives **per positive class**, plus at least 60% correct-positive recall. Seed 0 was designated before outcomes; no seed selection. The three new [curve tables](../data/classifier/model/relations/calibration/gpu-seed0-curve.md) and corresponding seed1/seed2 CSV/PNG/logit files cover both probability and margin grids; all 1,776 GPU curve rows were replayed.

| DEV seed | Argmax accuracy | Operating accuracy | Positive precision | Correct-positive recall | Emitted/all | Combined none-FP | Thresholds S/C/Cm/R |
|---:|---:|---:|---:|---:|---:|---:|---|
| 0 | 91.3% | 91.1% | 292/321 (91.0%) | 292/317 (92.1%) | 321/576 (55.7%) | 26/259 (10.0%) | 0.94/0.50/0.50/0.50 |
| 1 | 91.5% | 91.8% | 298/328 (90.9%) | 298/317 (94.0%) | 328/576 (56.9%) | 28/259 (10.8%) | 0.83/0.50/0.50/0.50 |
| 2 | 90.8% | 90.1% | 277/297 (93.3%) | 277/317 (87.4%) | 297/576 (51.6%) | 17/259 (6.6%) | 0.94/0.50/0.50/0.50 |

Seed-0 per-class DEV none-FP counts are **11/6/7/2 out of 259**; the combined 26/259 (10.0%) is not constrained to 5%. The primary per-class policy qualifies, so the margin fallback is unused. [Thresholds](../data/classifier/model/relations/thresholds.json) now describe `.94/.50/.50/.50`, consumed by `stencil.relation_operating_point.inputs` + `predict`; the historical `.98` consumer is not valid for this policy.

Checkpoint hashes, policy, all seed DEV records, and evaluator were committed in **`0829665c` before held-out-2 was opened**. One CPU inference pass at 2026-09-06 03:55 UTC produced all [357 prediction records](../data/classifier/model/relations/heldout2-records.jsonl) in that same run. Input matches the `8ae68078` git blob; one summary header was excluded, with no pair drops, admission-only rows, or overflow. Fit/evaluation author, declared-relative, exact-pair, and message-text overlaps were zero. Held-out-1 was not reopened. The two held-out sets differ, so historical 81.1% and current accuracy are not a matched estimate of retraining gain.

**Held-out-2 operating accuracy: 337/357 (94.4%).** Argmax diagnostic: 338/357 (94.7%), with 17/151 (11.3%) combined none-FP. The policy remains unchanged after this result.

| Class | Gold support | Operating precision | Operating recall | None-FP / all 151 gold-none |
|---|---:|---:|---:|---:|
| none | 151 | 93.4% | 93.4% | — |
| supersedes | 68 | 96.7% | 86.8% | 2/151 (1.3%) |
| cancels | 47 | 88.7% | 100.0% | 6/151 (4.0%) |
| completes | 45 | 100.0% | 97.8% | 0/151 (0.0%) |
| reinstates | 46 | 95.8% | 100.0% | 2/151 (1.3%) |

Confusion: gold rows / predicted columns, order none, supersedes, cancels, completes, reinstates.
```text
141   2   6   0   2
  9  59   0   0   0
  0   0  47   0   0
  1   0   0  44   0
  0   0   0   0  46
```

Combined none-FP is **10/151 (6.6%)**. All ten errors on gold-none occur in the authored `hard=true` none slice: **10/107 (9.3%)**, with 97/107 correctly returning none. Positive precision is **196/206 (95.1%)**; correct-positive recall and emitted-on-gold-positive coverage are both **196/206 (95.1%)**. Emitted/all coverage is **206/357 (57.7%)**; 151 outputs are none. None outputs include 141 correct negatives and 10 missed positives; they do not all represent a confident absence of relation.

V3 cells below are **descriptive post-evaluation slices** of the frozen author rationales and gold metadata, not separately registered tests or model inputs. [Exact definitions, row IDs, confusion and error IDs](../data/classifier/model/relations/heldout2-v3-cells.json) are reproducible from saved records without another model pass. Scoped replacement/withdrawal cells use global target plus the corresponding gold label; closure-plus-admission uses gold `completes` plus `message_new_rule=true`; other cells match the authored rationale. No admission predictions are scored.

| V3 clause / reconciliation cell | Correct / support | Errors |
|---|---:|---|
| Scoped bare suspension → none | 5/6 (83.3%) | 1 false cancel |
| Scoped explicit replacement → supersedes | 15/22 (68.2%) | 7 missed replacements (none) |
| Whole global withdrawal → cancels | 24/24 (100.0%) | 0 |
| Single-reply exception → none | 2/2 (100.0%) | 0 |
| Uncommitted hedge/proposal → none | 22/22 (100.0%) | 0 |
| Whole-task closure + independent global admission | 22/22 (100.0%) | 0 relation errors; admission untested |
| Whole-task closure without admission | 22/23 (95.7%) | 1 missed completion (none) |
| Sub-unit closure → none | 0/0 (unsupported) | Unsupported; no rationale-tagged examples |
| Inactive target / modified restoration → none | 4/5 (80.0%) | 1 false reinstatement |

**Readiness for FOCUS-3:** this is now a useful offline relation scorer, but it is not ready to drive the register feasibility gate. Scope handling still misses seven of 22 scoped replacements and falsely cancels one bare suspension. Ten gold-none pairs receive non-none proposals, including one tool message; these are scorer outputs, not measured applied register transitions. Admission and the authority/status/scope guards still need implementation and testing, and the separate 64-episode gate has not run. The prospective data minima remain unmet. This result supports continuing that work; it does not establish register safety or a FOCUS-3 PASS.

Validation: 37 targeted synthetic tests passed; lint clean; all artifact/source/input hashes and all 357 stored predictions/probabilities and the confusion matrix replayed. Exactly one held-out-2 attempt and inference pass are recorded. Subsequent work here only summarized those saved records; no fitting, threshold adjustment, checkpoint selection, or further inference followed the held-out result. Safetensors remain local. Metadata, calibration, records and this report are committed with explicit pathspecs; no push and no WORKLOG edits.

## v2 refit — 2026-09-06

**INELIGIBLE for the FOCUS-3 gate.** The requested refit is complete, but the
single CPU setup replay reached **35/36 admissions, 11/12 transitions and two
unauthorized applications**. Recall: supersedes 3/4, cancels 4/4, completes 4/4;
reinstates has no gold support. All three previously named phrasing misses now
pass. The remaining supersedes scores .5708 against C's .90 threshold. The
frozen admission head still admits one quoted sample; another new-task ordering
sentence wrongly supersedes the global tag key (.9493). The registered stop
prevented O setup and all 64-episode C/C'/O/N/T gate inference.

Fit/calibration pool: 7,749 pairs after both patches (123 drops, 225 relabels)
and three mechanical drops (two nonverbatim spans, one invalid status). The
loader repairs exact offsets, normalizes admission spans, backfills identities,
and deduplicates full rendered inputs to retain the status-only minimal pair.
Final none/supersedes/cancels/completes/reinstates counts are
3,259/1,521/1,038/1,024/907. Each seed has 6,974 fit / 775 DEV rows, with connected
scenario/message/relative groups disjoint. The 90 Astra relatives remain
explicitly evaluation-derived: all 90 land in seed 0 DEV; seeds 1/2 each fit on
30. This is development runtime agreement, not unseen-idiom generalization.

All seeds completed three epochs / 654 updates from the same pinned base BGE;
the numerical training algorithm matches 952079b8. Seed 0 remains preselected.
Primary DEV correct-positive recall is 414/449, 425/449, 418/449; supersedes
thresholds .90/.82/.88, all other thresholds .50. C' supersedes thresholds are
.50/.50/.60. Caps are empirical DEV none-FP per class: 5% for C, with supersedes
10% for C'. Admission now uses no positive proposal meeting threshold on any
overlapping pair; P(rule)>=.95 is unchanged. No admission refit or quoted veto.

**Held-out-2 SECOND LOOK, diagnostic only:** one additional seed-0 CPU inference
on the same 357 pairs after all model/policy freezes. C accuracy 343/357 (96.08%)
versus 337/357 (94.40%) on the first look; correct-positive recall 201/206 versus
196/206; none-FP 9/151 versus 10/151. Delta +1.68 accuracy points, +2.43 recall
points, -0.66 none-FP points. C' scores the same logits: 344/357 accuracy,
203/206 recall, 10/151 none-FP. No second-look result informed tuning or selection.

GPU-held time 195.999/10,800 seconds; no gate projection was reached. All 96 setup
records / 16 traces, 357 second-look records, source/model hashes, DEV arrays,
repair/split receipts and both calibration grids are retained. Saved-score
runtime/trainer/calibration audits and an independent action/state audit pass;
92 targeted tests pass, one existing expected failure. Safetensors stay out of
git. [Full v6 registration/results](quick-checks/focus3-gate/v6/RESULTS.md),
[model metadata](../data/classifier/model/relations-v2/README.md). No push.
