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

## 2026-09-06 — FOCUS-3 v7 step C: admission refit / INELIGIBLE

The CPU replay reaches36/36 authorized admissions and11/12 correct-source
transitions, but produces **19 unauthorized applications** (14admissions,
4reinstatements,1completion). The registered stop prevented trunk loading,
O setup and all C/C'/O/N/T gate inference. Relation v2 seed0, its thresholds,
C' alternative and prior held-out-2 results remain unchanged.

Semantic key checking drops10cross-key positives (5supersedes/5cancels), including
setup_3_02's ordering→global-tag mismatch; its new-task admission now succeeds.
Key slugs are separate from the unchanged storage IDs/version sequence. The
admission refit nevertheless admits10one-shot sort requests and4inert quoted
sentences, including the original setup_0_01 failure atP(rule)=.978070. It also
passes the unchanged reinstatement prerequisite on four “Reply exactly even.”
requests; generic relation proposals inherit the nominated target key. One
additional completion retires an earlier false-admission row. These observations
are combined-runtime results, not isolated causal estimates or permission to tune.

Admission fit lineage:20054 rows under the six historical admission patch files
plus582sentence-level NONE examples from150Opus/61Kimi-transition/273Kimi-relation
messages, minus2duplicates; zero exact gate-sentence overlaps. Final20634rows,
18571fit/2063DEV per seed, sentence-identity grouping. Original282 taxonomy-
category patch exceptions persist; this is not a clean historical-lineage claim
or verified reconstruction of original training bytes. Three full epochs/1743
updates per seed, fixed.95 admission, designated seed0. DEV accuracy94.72/94.96/
95.06%; rule admissions709/765,733/784,703/757; nonrule admissions16/1298,12/1279,
8/1306. Seed/threshold/model selection never uses Fable or setup outcomes.

Fable diagnostic, one363-row inference per model after freeze: original315/363
(86.78%), v2 318/363 (87.60%), **+0.83points**. Fixed.95 nonrule admissions9→5
of239; rule admissions114→111of124. One preflight aborted before inference on
“Thanks, that fixed it.” across independent authors and different contexts;
full paired inputs are disjoint. Preserve that receipt and the evaluation-only
identity correction. No rows, weights or thresholds changed; original accuracy
reproduces its historical metric. This historically used set is diagnostic.

96targeted tests pass,1existing xfail; saved96records/16traces replay exactly,
all DEV/Fable scores/splits recompute, and independent softmax/trainer/state audit
accounts66actions/57new rows/12status changes with zero unexplained mutations.
229relation pairs/184admission spans, zero overflow. GPU264.589652/10800seconds,
all admission fitting; flag removed naturally. No post-score tuning, signals,
benchmark/sealed reads or push. [Full v7 registration/results](quick-checks/focus3-gate/v7/RESULTS.md),
[admission model metadata](../data/classifier/model/ft-v2/README.md).

## 2026-09-06 — FOCUS-3 v8 step D: INELIGIBLE, final-iteration stop-loss

The last authorized admission/lifecycle iteration stops before the GPU gate.
CPU setup passes 36/36 authorized admissions and 11/12 correct-source transitions,
but has 12 unauthorized actions: eight one-shot payload admissions, three inert
quote admissions, and one completion of a polluted row in the completed task.
V7 had 19 unauthorized actions; false reinstatements fall from four to zero.
This does not meet the required zero-unauthorized bar. No further iteration,
corrective replay, threshold change or post-score tuning was performed.

Fit lineage: exact committed v7 admission corpus (20,634 rows) plus 300 explicit
in-session hand-written JSONL examples: 200 NONE requests carrying payloads and
100 STANDING rules with nearby payload context across ten domains. All targets
are single runtime sentence spans; no duplicates or exact bank overlap. The
historical taxonomy-category patch exceptions remain disclosed. No benchmark,
sealed input or recorded benchmark response supplied new examples. DEV groups
normalized sentence identity across role/label/context; no paraphrase-disjoint
claim. Seed 0 ships by prior designation; seeds 1/2 are stability checks only.

| Admission DEV | Seed 0 | Seed 1 | Seed 2 |
|---|---:|---:|---:|
| Correct / total |1989/2093|1977/2094|1985/2093|
| Non-rule admissions at .95 |18/1374|11/1321|16/1330|
| New-family NONE admissions |0/21|0/20|0/18|
| New-family standing admissions |7/8|7/7|7/7|

The new family has small, overlapping DEV supports across seeds; its zero
observed admissions do not establish safety on longer bank request sentences.
One Fable seed0 inference after all three final checkpoints froze: 318/363
(87.60%), equal to ft-v2; rule admissions unchanged at 111/124; non-rule
admissions worsen 5→8/239 (+1.26 percentage points). The comparator reuses
committed v7 logits after exact row/file-hash verification. Full paired inputs
and authors are disjoint; the existing generic sentence collision has different
context. This historically used held-out remains diagnostic.

Completion proposals now require the completed task's exact non-global scope
before precedence. Reinstatements require the span's own .95 rule admission,
semantic key equality without generic-key borrowing, cancelled/completed target
status, and absence of cancellation language/proposals in the message. The four
v7 generic replies had borrowed their sorting target's key; in v8 three still
pass admission but are rejected by own-key mismatch, and the fourth also falls
below .95. No true reinstatement support exists in setup, so recall is unmeasured.
The one extra completion remains because the previously false quote has the
completed task's scope. Relation v2 and C/C' thresholds are unchanged; its
standing-order supersedes miss remains .570806 below .90. No relation refit or
additional relation held-out evaluation occurred.

122 targeted CPU tests pass, one existing expected failure. The saved runtime
audit reproduces all 96 records and recomputes splits/DEV/Fable metrics. The
independent observer accounts for 59 actions, 50 added rows, 12 status changes,
214 relation pairs and 184 admission spans, with zero unexplained mutations.
Two observer-only input-association errors were corrected with initial logs
preserved; frozen scientific code/data/models/records did not change.
GPU fitting used 269.749111 seconds (4.50 minutes) of 10,800; replay used 16.508058
CPU wall seconds. Own flag removed naturally, no signals, background job or push.
The five-arm gate and its primary/secondary readings remain unmeasured.
[Full results](quick-checks/focus3-gate/v8/RESULTS.md),
[escalation for Brian](quick-checks/focus3-gate/v8/ESCALATION.md),
[ft-v3 metadata](../data/classifier/model/ft-v3/README.md).

## 2026-09-06 — Check44b: NO-GO; precise message admission misses standing-rule spans

C does not replace the ft head. First ship remains explicit structured rule entry,
with C available as an assistive suggester; this check does not authorize gate v9.
On330 previously unopened Fable-2 messages/207 gold spans, C overlap micro P/R is
99.34%/72.95% (151 matches/152 predictions), below the85% recall bar. B's unchanged
ft-v3 head scores95.43%/80.68% (167/175). Exact micro P/R is C 82.24%/60.39%,
B 78.86%/66.67%; overlap macro P/R is C 99.67%/78.69%, B 97.32%/87.22%.
Message-level P/R is C 100%/85.80%, B 99.40%/94.89%; it does not replace span recall.

C admits0/97 payload,0/57 quoted and 0/30 non-user negatives. B has0/97,1/57,0/30.
One-sided95% Clopper-Pearson message upper bounds for C are3.04%,5.12%,9.50%;
zero samples do not certify<=3% population error. Fable supplies101 scenario IDs;
secondary any-error scenario rates/bounds are in diagnostics.json, since the
inherited aggregator expects scenario_id while this bank calls the field scenario.

On the96 development SETUP turns, C has2 turns with unmatched admitted spans,
both task-selection sentences, and 0 request-template admissions. B has22 and 15,
respectively. This head-level diagnostic counts errors on otherwise positive
turns; downstream scope/lifecycle register vetoes are not applied. C meets the
<=2/96 SETUP bar, but held-out recall determines NO-GO. No bank data was fitted.

The frozen sentence splitter can represent only 176/207 spans (85.02%) on Fable-2:
all 31 two-rule messages combine their clauses in one candidate. C loses another
25 representable spans; B loses9. Category recall is C 101/114 single-rule,25/62
two-rule,25/31 rule+payload; B 109/114,27/62,31/31. No overflow, splitter rescue,
threshold change, alternative seed evaluation or repeat inference occurred.
Warm four-thread CPU held-out p50/p95 is C 50.67/60.27ms, B 48.60/54.82ms, excluding
model loading. Integrated shipping latency remains unmeasured.

Fit-on = audited Kimi 2872 after53 Opus replacements plus 231 Opus messages. Whole
domains keep source batches and matched quote pairs together; marketing/travel
are DEV 309/3103 (9.96%,2/20 domain groups), with 2794 fit messages. Domain grouping
is the conservative proxy for absent training scenario IDs. All input pairs use
the full message in segment A and exact frozen candidate in B,512-token overflow
abstention, explicit role rejection. No scope/key or auxiliary-flag heads fitted.

Preselected seed0 DEV overlap recall is 135/147=91.84%; seeds1/2 score138/147=93.88%.
DEV-only thresholds .9883976740722434/.9768228882950498/.956549283252651 each admit
3/183 gold-empty messages. Recipe f03c4398 and all-model freeze bab43b0d precede
Fable-2 commit2b3cfc74 and evaluation. All seeds completed 468 updates/three epochs.
GPU allocation 212.346/3600s includes CPU calibration and saving; peak4.342GiB.

Six focused tests, CPU smoke and frozen hashes pass. All426 records/852 arm
predictions were audited, including independent bitmask matching, macro scores,
B softmax/cutoffs, source snapshot identity and CP binomial equations. All DEV
scores/thresholds reproduce. Safetensors remain local; metadata and hashes are
committed. No signals, background jobs, sealed/benchmark reads or push.
[Full results](quick-checks/check44b/RESULTS.md),
[pre-written reading](quick-checks/check44b/README.md),
[model metadata](../data/classifier/model/admission-v1/README.md).

## 2026-09-06 — Check44c: token BIO admission, NO-GO

C2 and pre-registered C2+B return identical spans on the fresh357-message
heldout-3 bank. Overlap micro P/R77.67%/64.16% (247/385 recall), exact31.76%/26.23%;
overlap macro P/R86.98%/70.26%. Payload negatives0/57, quoted2/36=5.56%, non-user0/34;
one-sided95% CP uppers5.12%,16.47%,8.43%. The85% recall and3% quoted bars fail.
SETUP recovers36/36 admit events and3/4 supersedes, but10/96 false turns exceeds2;
4 request-template false admits,0/40 exact span matches. No runtime swap or gatev9;
explicit structured entry remains first ship. B fallback contributes zero spans.

The sentence candidate ceiling is removed:385/385 gold spans have distinct token
runs and exact tokenizer boundaries, no overflows. Yet unthresholded decoded
BIO runs match only291/385; confidence filtering leaves247. Ideal representability
is not learned extraction accuracy. Heldout-2 is a disclosed secondary second
look: overlap P/R88.89%/81.16% (168/207), payload1/97, quoted2/57, non-user0/30.

Astra CPU-reviewed all1577 kimi2 rows:122 changes including5 dropped placeholders;
1572 retained,1396 gold spans. Original patched kimi2872 + Opus231 give4675 total.
Fit4209/DEV466=9.97%,13 DEV domains; whole source-generation batches kept together
as a scenario proxy because author scenario IDs are absent. Cross-batch semantic
relatives remain a limitation. Kimi2 still contains no literal “Standing rule:”
examples; no heldout or gate wording was added to fill that gap.

All3 final seeds and both DEV thresholds frozen fd43ff8f before first heldout3 read.
Seed0 t=.7273366828,t_low=.9039153621;5/250 DEV empty-message errors for both;
DEV overlap268/286=93.71%. B fit-id overlap1/871 DEV sentences. No seed selection.
GPU88.546/3600 seconds, peak1.494GiB; CPU heldout3 warm p50/p95 C2=87.90/96.01ms,
C2+B=181.39/200.73ms. All783 records/1398 DEV records verified, independent matcher
and CP calculation pass; original runner preserved for an audit-only tuple/list
comparison repair, science AST unchanged. No inference rerun or refit.

[Results and limitations](quick-checks/check44c/RESULTS.md),
[pre-written reading](quick-checks/check44c/README.md),
[model manifest](../data/classifier/model/admission-v2/manifest.json).

## 2026-09-06 — Relations v3 override refit: NO-GO

V2 stays. Accuracy 87.05% fails 94%; supersedes recall 73.26% fails 90%. F1 also fails the registered floors for none (82.83% < 92.30%), supersedes (84.00% < 93.24%), and completes (94.12% < 95.88%).

Fit-on = exact v2 patched relations/transitions/four enrich sets + 1,231 Opus-patched overrides; calibrated-on = scenario-disjoint DEV only; evaluated-on = fresh Fable held-out-3 once after committed model/policy/evaluator freeze `e8c00361` (recipe `6809791f`). The inherited 90 Astra2 evaluation-derived relatives remain disclosed. No benchmark inputs/responses.
Pool: 8,980 pairs; each seed 8,082 fit/898 DEV. Audit patches applied by source+zero-based index; three deletes, 52 start/1,032 end repairs after patching, zero further target-span drops; 1,116 retained whole-message spans. Admitted spans normalized, identities assigned, repeated messages grouped. The seven flagged paraphrase-family rows and connected groups are fit-only, excluded from every DEV. These groups do not establish broad paraphrase disjointness.

All seeds 0/1/2 complete three epochs/759 updates with the v2 recipe; seed 0 preselected. DEV C policies and exact records are saved.

| Seed | DEV accuracy | Supersedes recall | C thresholds S/C/Cm/R |
|---|---:|---:|---|
| 0 | 94.65% | 95.63% | 0.92/0.50/0.50/0.50 |
| 1 | 95.21% | 97.81% | 0.50/0.50/0.50/0.50 |
| 2 | 93.99% | 96.17% | 0.76/0.50/0.50/0.50 |

**Primary fresh held-out-3, one inference pass.**

Accuracy **87.05%** (390/448).

| Label | Support | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| none | 133 | 75.00% | 92.48% | 82.83% |
| supersedes | 172 | 98.44% | 73.26% | 84.00% |
| cancels | 51 | 86.21% | 98.04% | 91.74% |
| completes | 41 | 90.91% | 97.56% | 94.12% |
| reinstates | 51 | 94.44% | 100.00% | 97.14% |

Confusion: gold rows / predicted columns, none/supersedes/cancels/completes/reinstates.
```text
123   2   1   4   3
 39 126   7   0   0
  1   0  50   0   0
  1   0   0  40   0
  0   0   0   0  51
```
Supersedes recall 95% Clopper–Pearson interval: **[65.98%, 79.71%]** (row-level, not cluster-adjusted).

The registered F1 floors (v2 held-out-2 minus 3 percentage points) are none 92.30%, supersedes 93.24%, cancels 91.00%, completes 95.88%, reinstates 94.87%.

**Secondary held-out-2 historical re-look**, after freeze; v3 evaluated once on this already-used bank (v2 already had a disclosed second look). It did not inform fit, calibration or selection.

Accuracy **95.24%** (340/357).

| Label | Support | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| none | 151 | 95.27% | 93.38% | 94.31% |
| supersedes | 68 | 98.41% | 91.18% | 94.66% |
| cancels | 47 | 88.68% | 100.00% | 94.00% |
| completes | 45 | 97.78% | 97.78% | 97.78% |
| reinstates | 46 | 95.83% | 100.00% | 97.87% |

Confusion: gold rows / predicted columns, none/supersedes/cancels/completes/reinstates.
```text
141   1   6   1   2
  6  62   0   0   0
  0   0  47   0   0
  1   0   0  44   0
  0   0   0   0  46
```
Supersedes recall 95% Clopper–Pearson interval: **[81.78%, 96.69%]** (row-level, not cluster-adjusted).

V2 accuracy was 96.08%; v3 change -0.84 points.

**Exact v2 FOCUS-3 runtime diagnostic:** 11/12 transitions versus 11/12, 34/36 admissions versus 35/36; 6 unauthorized applications versus 2. Only relations/C thresholds swapped; original admission and runtime source retained. All 96 turns saved and independently replayed; one previously passing transition regression and one improvement. Runtime recalls are supersedes 3/4, cancels 4/4, completes 4/4; reinstates has zero support. No full gate inference or gate eligibility claim.

- Regression: `setup_0_01`, turn 2, supersedes now updates the wrong source key (`0:20` rather than `0:90`).
- Improvement: `setup_0_02`, turn 2, the standing-order switch now passes.

GPU allocation: 264.77/1800 seconds (4.41 minutes), including calibration/save/CPU work while flagged. Flag removed on natural completion. 11 targeted tests passed; all 2,694 DEV scores, held-out records, binomial bounds, and runtime state replay audited. Source/model/data hashes verified; no post-score model or policy changes, signals, background jobs or push. Safetensors remain local.

[Model README and checkpoint hashes](../data/classifier/model/relations-v3/README.md), [evaluation and reading](../data/classifier/model/relations-v3/evaluation.json), [freeze](quick-checks/relations-v3/freeze.json), [audit](quick-checks/relations-v3/audit.json).

### Orchestrator addendum after the fable accuracy review (2026-09-06; results/relations-v3-review-fable.md)
Numbers and freeze order verified. Disclosed diagnostic: relations-v2 on held-out-3 = 87.95% accuracy, supersedes
recall 126/172 = 73.26% with the identical miss profile (39 to none, 7 to cancels; 39/46 misses shared) — held-out-3
is a HARDER bank, not a v3 regression. The none-precision drop is arithmetic from the supersedes-to-none misses.
Miss families: bare new value + temporal (13), retire/withdraw + replacement (12; a spec ruling is needed), explicit
meta-override wording cut by the 0.92 threshold (10), task-scoped override of global (8), "actually, B" (3).
DECISION: relation refits parked; v2 ships (assistive mode; explicit actions specify their own operation). Reopening
requires a spec ruling on "withdraw + replace" and calibration transfer work, not another refit.

## 2026-09-06 — Check 46: frozen 30B trunk as register updater — NO-GO

Data lineage: fit none; one unchanged prompt with six fresh Astra-authored examples, 20 DEV rows from only kimi-admission-2 and kimi-overrides. One frozen model look at admission/relations heldout-3 (previously exposed to other models); v8 SETUP is development diagnostic. No benchmark reads. [Full report, frozen prompt and records](quick-checks/check46/README.md).

Admission overlap recall **304/385 =78.96%**, precision **89.94%**; exact recall15.32%/precision17.46%. Payload false admissions6/57 (one-sided95% CP upper19.72%), quoted4/36 (23.65%), non-user4/34 (24.93%). Rule-plus-payload52/87 and buried rules34/54 remain weak. Single-sentence two-rule116/140, three-rule37/39; cue-less lexical proxy180/212 (definition/IDs in families.json).

Relations **399/448 =89.06%** accuracy; per-label P/R/F1 are in the report. Supersedes **150/172 =87.21%** passes its recall bar, but the accuracy bar94% fails. Task-scoped override of global **0/21**, all emitted add; withdraw+replace12/12, bare-value+temporal17/18, actually-B7/7. Positive-target identification281/315; raw relation target IDs285/285 valid. This one-rule test does not establish multi-target discrimination.

SETUP recovers36/36 admits and4/4 replacement spans but has **58/96 false-admission turns**. This is the inherited empty-register admission diagnostic, not a lifecycle rollout. Neither half passes; explicit entry stays, no runtime swap.

Qualified vLLM image/flags, greedy thinking-off, strict XGrammar schema plus all-character-substring constraint. **807/807 raw-verbatim and normalized-inclusive**, zero repairs; one capped response and two typed-operation rejections journaled. Removing decoder corruption did not meet the bars;78.96% is this frozen prompt’s operating point, not a trunk-wide ceiling or a model-size-only comparison with check44.

User latency mean6.009s, median5.951s, p95=15.359s; mean1444.9 input/67.7 output tokens. Concurrency4 evaluation cost2.007 amortized GPU-s/message; total2453.221/3600s =40.887min including startup and cleanup. 921 same-call records replayed,6 targeted CPU tests and7 actual grammar witnesses passed. Freeze519c7338; the loader’s summary-header count assertion required a disclosed second physical source read before any inference, with frozen science unchanged (8742da2d). Owned container/flag removed; explicit commits, no push.

Next hypothesis: a small dense generative updater fine-tuned on provenance-reconciled, audited authored register/message/operation data; scenario-disjoint DEV and a fresh author-disjoint evaluation bank. Heldout-3 inputs, outputs, labels and error-derived paraphrases, and all benchmark items/responses, remain excluded from fitting. No training was launched here.
