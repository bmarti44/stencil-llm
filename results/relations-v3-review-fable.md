# Relations v3 override refit — one-round accuracy review (fable, 2026-09-06)

Reviewer: fable (author of held-out-3). Scope: report section "2026-09-06 — Relations v3 override refit: NO-GO", `data/classifier/model/relations-v3/`, `scripts/relations_v3.py`, `results/quick-checks/relations-v3/`. CPU only; nothing under `data/bench` opened; GPU untouched. One disclosed diagnostic was run (v2 on held-out-3, Section 4).

## 1. Numbers (all recomputed)

| Claim | Verified | Method |
|---|---|---|
| Held-out-3 accuracy 87.05% (390/448) | yes, exact | rescored `heldout3-records.jsonl` row by row against my gold; every `gold`/`row.label`/message matches the committed bank blob `28cc440e`; confusion matrix reproduced exactly |
| Predictions follow the frozen C policy (S 0.92, others 0.50) | yes, 0 mismatches | re-derived prediction from `probabilities` + thresholds for all 448 rows |
| Supersedes R 73.26% (126/172), P 98.44% (126/128) | yes | confusion row/column |
| none P 75.00% (123/164), R 92.48% (123/133) | yes | confusion |
| Supersedes CP95 [65.98%, 79.71%] | yes | `beta.ppf` k=126, n=172 |
| Held-out-2 second look 95.24% (340/357); v2 96.08%; delta -0.84 | yes | rescored `heldout2-records.jsonl`; `v2-baseline.json` accuracy 0.960784 |
| DEV table 94.65 / 95.21 / 93.99, S thresholds 0.92 / 0.50 / 0.76, seed0 DEV S recall 95.63% | yes | seed `operating-point.json` `arms.C.dev` |
| Runtime 11/12 transitions, 34/36 admissions, unauthorized 6 vs v2 2 | yes | `runtime-summary.json`, `baseline-runtime-audit.json` (v2: 11/12, 35/36, 2) |
| Pool 8,980; 1,231 overrides retained; 3 deletes; 52 start / 1,032 end repairs; 1,116 whole-message spans | yes | independently re-applied the Opus patch and the `load()` repair rule (Section 3) |
| Checkpoint hashes (seed0 encoder `f6200e80…`, head `8b102009…`) | yes | `sha256sum` of local safetensors matches README/freeze.json/manifest |
| F1 floors (v2 held-out-2 minus 3 pts) and the three F1 failures | yes | v2-baseline F1: none .9530, S .9624, cancels .94, completes .9888, reinstates .9787 → floors 92.30/93.24/91.00/95.88/94.87; v3 none 82.83, S 84.00, completes 94.12 fail; cancels 91.74 and reinstates 97.14 pass |

Small note: the report's DEV C thresholds column reads "S/C/Cm/R" but the per-seed files list order cancels/completes/reinstates/supersedes; the values quoted (0.92/0.50/0.50/0.50) are correct once read as supersedes first.

## 2. Freeze order

- `6809791f` (13:48:54 UTC) registers recipe, `scripts/relations_v3.py`, runtime-v2 snapshot, v2 baseline, data-counts.
- `e8c00361` (13:54:32 UTC) commits all three seeds' `thresholds.json`, `operating-point.json`, manifests, DEV records, `freeze.json` (checkpoint SHA-256s) and `audit_relations_v3.py`. No held-out records or metrics are in this commit.
- `heldout3-started.json` timestamp 13:54:44 UTC (12 s after the freeze commit) carries `freeze = sha256(freeze.json) = 175b9d59…` (verified) and the held-out blob `28cc440e` (verified against `git rev-parse`). `evaluate()` asserts `committed(freeze.json)` and the blob, writes the started receipt with `open("x")`, and only then reads the bank. `heldout2-started.json` follows at 13:55:04 UTC.
- `afde6cdc` (13:57:37 UTC) commits records, metrics, evaluation.json, README completion, runtime records. `thresholds.json` content at `e8c00361` equals the working tree (S 0.92).

Freeze order holds. Caveat for honesty: held-out-3 was committed at 13:10 UTC (`3eadcce9`), before the recipe and fit; the "never read before freeze" property is procedural (lineage line + `evaluate()` code path), not mechanically provable. The v2-identical miss profile in Section 4 is consistent with no leakage into fit or calibration.

## 3. Offset repair of kimi-overrides (spot-check 30 rows)

Re-ran the patch + repair rule (`start = message.find(text)`, `end = start + len(text)`) outside the pipeline: 1,231 retained, 0 non-verbatim after patch (row 214's text was patched), 52 start / 1,032 end repairs, 1,116 whole-message spans, 0 messages with more than one occurrence of the span text (so `find` is unambiguous). The 1,032 vs Opus's pre-patch 1,031 differs by one row whose span text the patch changed; the report figure is the correct post-patch count. End error distribution: ±1..9 characters, centred on -1/-2 (Kimi's end offsets were mostly short by a character or two).

Random sample (seed 20260906): 20 end-repaired rows plus 10 clause-level rows. All 30 repaired spans are the intended sentences/clauses: whole-message rows trivially (e.g. idx 28, 303, 480, 747 — original slice truncated at "going for", "three dec", or overran by 3); clause rows land on the intended clause: idx 121 "My colleague said you should probably skip the summary lines" (none, reported speech), idx 141 "maybe we switch French phrases to Spanish ones someday" (hedged), idx 364 "assumptions-list rule is retired" (cancels), idx 376 "Reinstate the original euros convention for the cost study", idx 789 "replace the one-row-per-SKU setup with …", idx 963 "That concludes the keynote invitations;", idx 1197 quoted 'drop the past-tense habit' (none). No repaired span drifted to a neighbouring clause. Repair is sound.

## 4. Disclosed diagnostic: relations-v2 seed0 on held-out-3 (CPU)

Not a registered evaluation; post hoc; no decision authority; v2's held-out-2 look count is unchanged (this is a different bank). Ran the same code path as `relations_v3.evaluate()` (normalize, `encode_rows`, CLS+role head, `h2.make_records`, `relations_v3.metrics`) with the v2 seed0 checkpoint (hashes `6d7e0cf0…`/`e17aa2ae…` verified against the v6 freeze) and its own frozen C policy (S 0.90). `CUDA_VISIBLE_DEVICES=""`, `torch.cuda.is_available()` false, 4.7 s inference. Records and metrics are in the session scratchpad only (not committed).

| | v3 (S .92) | v2 (S .90) |
|---|---:|---:|
| Accuracy | 87.05% (390) | 87.95% (394) |
| Supersedes R / P | 73.26% / 98.44% | 73.26% / 99.21% |
| none P / R | 75.00% / 92.48% | 75.60% / 95.49% |
| cancels F1 | 91.74% | 92.59% |
| completes F1 | 94.12% | 96.39% |
| reinstates F1 | 97.14% | 97.14% |
| Confusion supersedes row | 39 / 126 / 7 / 0 / 0 | 39 / 126 / 7 / 0 / 0 |

v2 misses exactly 126/172 supersedes with the same 39-to-none / 7-to-cancels split; 39 of the 46 missed rows are shared. v3 recovers 7 rows v2 misses (0021, 0039, 0086, 0150, 0181, 0214, 0291 — all now pS ≥ 0.92, all "Update:/For the X/changed my mind" phrasings) and loses 7 that v2 gets (0308, 0309, 0325, 0338, 0351, 0429, 0438 — v3 pS 0.58–0.92 vs v2 0.90–0.95). v3 adds 4 none false positives v2 avoids (0043 cancels, 0319/0375 completes, 0380 supersedes).

Threshold sweep on the same logits (diagnostic only):

| S threshold | v3 acc / S-recall / none-FP | v2 acc / S-recall / none-FP |
|---|---|---|
| 0.50 | 90.85% / 85.47% / 14 | 92.86% / 88.37% / 10 |
| 0.90 | 87.72% / 75.58% / 11 | 87.95% / 73.26% / 6 |
| 0.92 | 87.05% / 73.26% / 10 | 87.05% / 70.93% / 6 |

## 5. Diagnosis of the 46 supersedes misses

By prediction: 39 predicted none, 7 predicted cancels. Of the 39 none: 21 have argmax supersedes but pS < 0.92 (threshold casualties; 6 of them are in [0.85, 0.92)), 17 have argmax none, 1 argmax completes. Scope breakdown follows the family table.

Idiom families (my own classification of my own rows; v3 prediction, then v2 in brackets):

| Family | n | v3 outcome | v2 |
|---|---:|---|---|
| A. Bare new value + temporal marker, no override verb ("Kilometres from now on", "Celsius in the ice log now", "Miles for trail lengths … from now on", "Inches … from tonight", "that's the new rule") | 13 | 13 none (9 argmax none, 4 pS<.92) | 11 none, 2 S |
| B. Task-scoped override of a global rule, leading task prefix ("In the flight briefing, altitudes in metres", "On the pricking chart, thread thickness in tex") | 8 | 8 none (6 pS .63–.90, 2 argmax none) | 6 none, 2 S |
| C. "Actually, B" | 3 | 3 none (all argmax none) | 3 none |
| D. Retire/withdraw A + replacement B ("Scrap the slang, use engineering names", "Millimetres are out; … AWG from here", "scratch the per-block pricing", "numbers are retired", "was a mistake") | 12 | 7 cancels (pC .57–.96), 5 none | 7 cancels, 4 none, 1 S |
| E. Explicit meta-override wording ("that supersedes the one-decimal rule" pS .907, "that overrides what I said before" .902, "that replaces British" .777, "Update:" ×2, "New rule: … replacing", "treat that as the standing rule", "keep it that way", "please follow that", "Let's go with") | 10 | 10 none (8 pS .59–.92, 2 argmax none) | 8 none, 2 S |

Readings:
- The seven cancels errors are all family D: any message containing a withdrawal verb (scrap/scratch/retired/no good/gone) beats the co-present replacement value. This is the one family where the classifier confidently commits to the wrong positive label; it is exactly the "narrower task replacement vs bare suspension" ambiguity Opus flagged as open in the override audit, so the fit data carried it unresolved.
- Families A and C are genuine model misses (argmax none, pS mostly < 0.25): a message that states only the new value and a temporal marker is not read as an override. The training corpus has many "bare value" supersedes rows by my crude regex (kimi-relations ~287), but the held-out-3 versions attach a reason clause ("the new technician prefers it", "we're a small shop") which pushes them toward none-style chatter.
- Families B and E are dominated by threshold casualties: 14 of 18 have argmax supersedes. Explicit "that supersedes / that overrides" wording landing at pS 0.90–0.91 and being cut at 0.92 is the clearest sign that the DEV-calibrated cutoff (chosen for ≤5% DEV none-FP; DEV S recall 95.6%) does not transfer to this bank. But lowering S to 0.50 only reaches 85.5% recall (v2: 88.4%) at 14 none-FP, so the threshold is not the whole story; the bar of 90% is not reachable by re-thresholding either model.
- Scope intersection: the 43 global-target supersedes rows miss 14 (32.6%) vs 32/129 (24.8%) for task-target rows. Within the 43: the 21 hard "task-scoped override of global" rows miss 8 (38%), the 22 plain global changes miss 6 (27%). The scope-intersection cases are over-represented among misses but do not dominate them (8/46); families A, D and E are task-scope rows.
- `hard` flag: 11/25 hard supersedes rows missed (44%) vs 35/147 easy (24%). The bank was written to be supersedes-hard; it is.

## 6. The "none precision collapse"

Not a none-boundary shift. Predicted-none 164 = 123 true + 39 supersedes + 1 cancels + 1 completes; none precision is 75% almost entirely because of supersedes recall. The none false-positive rate on held-out-3 (10/133 = 7.5%) is in line with held-out-2 (v3 6.6%, v2 6.0%), and v2 — fit without the 289 override-none rows — shows the identical 39-supersedes-to-none column. The ten none FPs are reinstates on a cancelled target with a changed value (0014, 0081), reinstates on a different key (0337), completes on task-switch / sub-unit / hedged closure (0255, 0319, 0448), continuation read as completes (0375), changed-fact-not-rule read as supersedes (0365, 0380), single-reply exception read as cancels (0043). Four of these are v3-only, six are shared with v2. Hypothesis "added hard-none rows shifted the boundary": refuted by the v2 diagnostic.

## 7. Answers

1. NO-GO correctly applied. All three registered bars fail on the recomputed numbers; the freeze preceded the read; thresholds and checkpoint are the frozen ones; no post-score change is visible in git.
2. Held-out-3 is a harder bank, not a v3 regression. v2 and v3 produce the same supersedes recall (126/172) with the same error shape, and 39/46 misses are shared; v3 is within one point of v2 in accuracy at the frozen policies and about two points behind at S 0.50. The held-out-2 second look (-0.84) says the same. The override refit neither helped nor materially hurt; the v3-only wins and losses are a wash (7 each) and are threshold-adjacent phrasings.
3. No new small refit is warranted now. The refuted hypothesis is the none-boundary shift. The two live hypotheses are (a) family D "withdraw + replace" is a labelling-policy problem in the fit corpus (Opus left it as an open ambiguity; it should be settled in LABELS-RELATIONS.md and the corpus relabelled before any fit), and (b) families A/B/E are a calibration-transfer problem that no DEV-chosen cutoff will fix while DEV is scenario-disjoint but idiom-matched to the fit corpus. Both are data/spec work, not another three-epoch fit; the required recall gain (73% to 90%) is far beyond what re-thresholding delivers on either model. Park relation refits with v2 in the ship: explicit actions specify their own operation, so free-text relations matter only in assistive mode, and v2 is as good as v3 there. If the assistive path is revisited, spend the next effort on a spec ruling for family D plus an idiom-stratified DEV (or a small idiom-matched calibration set that is not held-out authored) rather than more generated pairs.
4. Corrections to the report:
   - The none precision figure should be attributed to the 39 supersedes-to-none misses, not presented alongside supersedes recall as a second failure mode; the none false-positive rate (7.5%) is unchanged from held-out-2.
   - Add the miss composition: 21/46 argmax supersedes below 0.92, 17 argmax none, 7 cancels, 1 completes; and the family table above.
   - Add the disclosed v2-on-held-out-3 diagnostic (87.95%, S recall 73.26%, identical confusion row) so the NO-GO is not read as a regression.
   - The runtime paragraph should say that three of the six unauthorized applications resolve to the wrong source key `0:20` at runtime (setup_0_01, setup_3_00 ×2, setup_3_02) — a source-resolution effect in the runtime pairing, not only a classifier change — and that v2's runtime supersedes recall is also 3/4, so "3/4" is not a v3 delta.
   - The DEV threshold column header "S/C/Cm/R" should say the order explicitly (supersedes, cancels, completes, reinstates) since the JSON order differs.
   - Minor: "1,031" (Opus pre-patch) vs "1,032" (post-patch) end repairs should be stated as such where both appear.

## 8. Files

- Reviewed: `/home/bmarti44/stencil-llm/results/relations-classifier-report.md` (lines 369–455), `/home/bmarti44/stencil-llm/data/classifier/model/relations-v3/{README.md,evaluation.json,heldout3-*.json*,heldout2-*.json*,seed*/}`, `/home/bmarti44/stencil-llm/scripts/relations_v3.py`, `/home/bmarti44/stencil-llm/results/quick-checks/relations-v3/{freeze.json,recipe.json,audit.json,runtime-summary.json,baseline-runtime-audit.json,v2-baseline.json,data-counts.json}`, `/home/bmarti44/stencil-llm/data/classifier/relations/kimi-overrides.jsonl`, `/home/bmarti44/stencil-llm/data/classifier/review/{overrides-opus-patch.jsonl,overrides-opus-audit.md}`, `/home/bmarti44/stencil-llm/data/classifier/heldout/fable-relations-heldout-3.jsonl`.
- Diagnostic outputs (scratchpad, uncommitted): `v2_diag.py`, `v2-heldout3-records.jsonl`, `v2-heldout3-metrics.json`.
