# FOCUS-2d outcome — FAIL-SAFETY

Data lineage FIRST — fit-on: none; evaluated-on: fresh synthetic FOCUS-2d competence/pilot/final banks, disjoint from development and each other. Seeds 9053721/9053722/9053723 unchanged; no prior outputs or certificates reused, no fitting/training or benchmark evaluation. The required earlier sealed-guard acceptance test was the sole authorized sealed-input reader.

**FAIL-SAFETY**, from final analysis of a **COMPLETE** 256 x five-arm run; not an early scheduling stop. All 7,296 final raw records were validated; all 256 scheduled episodes are eligible, with zero delay-invalid exclusions. The 384 delay generations ended at cap 160 or earlier; no 320-token retries. The sixth-break stop did not trigger.

Candidate a458e22; implementation/CPU acceptance ed80743 (104 passed, 1 existing xfail, ruff clean); authorized predicate repair 7b8eef4 (nine predicate checks). Freeze 8a1176f2055b494299a325f42d9f533ae75d582e, manifest 3e9ae3c1c23bd47e10526d8cca694f27645aac9d0574ea582669b6fec7af6902; REGISTERED/receipt f0f796f, pilot authorization 5685fa7, complete run/analysis/audit 30211a6. All seven prepared input files remain byte-identical to ff67b78. The prior assembly stop and old script are preserved under stop-at-freeze; FOCUS-2c Amendment 2 remains FAIL-SAFETY at 11/256.

Competence PASS: ascending 61/64 (bar 52), descending 57/64 (bar 52), default 64/64 (bar 56). Pilot PASS: four valid cells, 114 records, worst cell 72.87206026306376 seconds; registered total projection 24,013.651209137985 seconds (6.670459 hours), including 25% reserve. Actual charged allocation: competence 373.7267173510045 + pilot 287.2916367829311 + final 16351.383859334048 = 17012.402213467984 seconds; analyzer 29.708377194125205 seconds; total **17042.11059066211 seconds = 4.733920 hours**, below the 28,800-second cap. Prior legs remain separately disclosed development in freeze/freeze-receipt.json.

All-five success totals: neither 0/256; placement-only 32/256; eviction-only 108/256; BOTH 143/256; text-restate 176/256.

| BOTH vs | All-five Y | Delta (pp) | b/c | Exact one-sided p | Holm p |
| --- | --- | --- | --- | --- | --- |
| placement-only | 143 vs 32 / 256 | +43.359375 | 121/10 | 1.15311103e-25 | 3.45933309e-25 |
| eviction-only | 143 vs 108 / 256 | +13.671875 | 71/36 | 0.000461578998 | 0.000923157996 |
| text-restate | 143 vs 176 / 256 | -12.890625 | 33/66 | 0.999718896 | 0.999718896 |


Primary FAIL: BOTH beats both component arms after Holm, but does not beat text-restate and misses the required >=5-point advantage (observed -12.890625 pp). Nominal paired-score 95% intervals are preserved in analysis.json; the registered exact tests and magnitude rule decide the result.

Fixed secondaries: placement-only >= text-restate is NOT observed (32/256 vs 176/256, delta -56.25 pp; b/c=11/155, exact one-sided p=1). Eviction-only vs neither is 108/256 vs 0/256, +42.1875 pp; b/c=108/0, p=3.0814879110195774e-33. These descriptive readings cannot rescue primary/safety failure or carry the headline; no noninferiority/equivalence claim.

The structural F6 gate passes: h=1, r=0, exact p=.5, h<=5; registered one-sided upper h rate 0.018395769886273616. The combined safety result is FAIL because the unchanged-constraint endpoint has h=59, r=0 (net 59 > 2), p=1.734723475976807e-18. F6 schema_invalid is reported separately and does not drive the sixth-break stop; its one truncated invalid-JSON case overlaps the structural row.

| F6 episode flag | neither | placement-only | eviction-only | both | text-restate |
| --- | --- | --- | --- | --- | --- |
| broken | 0 | 0 | 0 | 1 | 0 |
| json_invalid | 0 | 0 | 0 | 1 | 0 |
| schema_invalid | 1 | 1 | 0 | 59 | 0 |
| truncated | 0 | 0 | 0 | 1 | 0 |
| empty | 0 | 0 | 0 | 0 | 0 |
| repetitive | 0 | 0 | 0 | 0 | 0 |
| placeholder | 0 | 0 | 0 | 0 | 0 |


| Failure endpoint | BOTH / text-restate | h/r | Exact p | Gate |
| --- | --- | --- | --- | --- |
| constraint | 59/256 vs 0/256 | 59/0 | 1.73472348e-18 | FAIL |
| user_fact | 1/256 vs 0/256 | 1/0 | 0.5 | PASS |
| tool_fact | 1/256 vs 0/256 | 1/0 | 0.5 | PASS |
| assistant_fact | 64/64 vs 42/64 | 22/0 | 2.38418579e-07 | disclosed, not gated |


Assistant-fact cost is disclosed, not gated: failures 64/64 BOTH versus 42/64 text-restate, +34.375 pp, b/c=22/0, p=2.384185791015625e-7. Of 64 memo-source episodes, 36 lack a valid source memo (36/36 failures in both arms); among 28 valid sources, failures are 28/28 versus 6/28. Do not attribute the 36 invalid-source failures to eviction; the observed paired excess is 22 episodes.

| Stratum | n | BOTH Y | Placement Y | Eviction Y | Text-restate Y |
| --- | --- | --- | --- | --- | --- |
| both_correct=False | 58 | 35 | 10 | 25 | 41 |
| both_correct=True | 198 | 108 | 22 | 83 | 135 |
| direction=ascending | 128 | 69 | 14 | 59 | 80 |
| direction=descending | 128 | 74 | 18 | 49 | 96 |
| delay=0 | 128 | 89 | 24 | 46 | 91 |
| delay=512 | 128 | 54 | 8 | 62 | 85 |


F11: both-correct prior stratum n=198 has BOTH-minus-placement +43.434343 pp (b/c=94/8, p=4.7173150125305585e-20); the other n=58 has +43.103448 pp (27/2, p=8.121132850646973e-7). The gain versus placement is present in the both-correct stratum, so the observed component-arm benefit is not confined to wrong-prior cleanup. These stratified tests are descriptive and do not rescue the failed text-restate contrast or safety gate. The sort-family stratum is the full sample.

Plain language: the split-cue configuration completed the full registered experiment, but failed the unchanged-constraint safety gate. At CLEAR, 58 BOTH responses returned the payload as a bare JSON array, losing the required answer/tag object despite its persistent system instruction; 57 of these occurred after a 512-token delay and one without a delay. One further SWITCH response was truncated and invalid JSON. BOTH beat the placement-only and eviction-only component arms on the all-five endpoint, but scored below text-restate, so it failed the registered efficacy rule as well. Do not promote this configuration or claim extra control over text-restate. These observations do not establish a causal explanation for the remaining schema failures, equivalence, absence of a mechanism, benchmark transfer or general safety; no rescue or successor run was attempted.

## Checkpoint success

Each denominator is 256; rows require the registered exact task value and unchanged constraints.

| Arm | SWITCH | HOLD | BACK | CLEAR | NEUTRAL2 |
| --- | --- | --- | --- | --- | --- |
| neither | 116 | 137 | 186 | 2 | 11 |
| placement-only | 244 | 185 | 249 | 253 | 43 |
| eviction-only | 186 | 227 | 168 | 253 | 255 |
| both | 213 | 238 | 230 | 198 | 256 |
| text-restate | 225 | 243 | 229 | 228 | 256 |

## F11 contrasts

All p-values below are descriptive, unadjusted exact one-sided McNemar. Delta is BOTH minus comparator in percentage points.

| Field | Stratum | Comparator | n | BOTH / comparator Y | Delta pp | b/c | p | Nominal paired-score 95% CI (pp) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| both_correct | False | eviction-only | 58 | 35 / 25 | +17.241379 | 15/5 | 0.0206947327 | [2.288236, 31.922031] |
| both_correct | False | placement-only | 58 | 35 / 10 | +43.103448 | 27/2 | 8.12113285e-07 | [27.777714, 56.832668] |
| both_correct | False | text-restate | 58 | 35 / 41 | -10.344828 | 6/12 | 0.951873779 | [-24.873720, 4.249484] |
| both_correct | True | eviction-only | 198 | 108 / 83 | +12.626263 | 56/31 | 0.00483660927 | [3.449204, 21.627255] |
| both_correct | True | placement-only | 198 | 108 / 22 | +43.434343 | 94/8 | 4.71731501e-20 | [35.229567, 51.170274] |
| both_correct | True | text-restate | 198 | 108 / 135 | -13.636364 | 27/54 | 0.999155681 | [-22.306203, -4.822293] |
| delay | 0 | eviction-only | 128 | 89 / 46 | +33.593750 | 47/4 | 1.20815358e-10 | [24.292602, 42.885890] |
| delay | 0 | placement-only | 128 | 89 / 24 | +50.781250 | 70/5 | 4.9088778e-16 | [40.236647, 60.131894] |
| delay | 0 | text-restate | 128 | 89 / 91 | -1.562500 | 22/24 | 0.670630961 | [-12.046176, 8.937277] |
| delay | 512 | eviction-only | 128 | 54 / 62 | -6.250000 | 24/32 | 0.885597229 | [-17.628649, 5.271827] |
| delay | 512 | placement-only | 128 | 54 / 8 | +35.937500 | 51/5 | 5.85146237e-11 | [26.133137, 45.449505] |
| delay | 512 | text-restate | 128 | 54 / 85 | -24.218750 | 11/42 | 0.999997225 | [-34.454624, -13.656042] |
| direction | ascending | eviction-only | 128 | 69 / 59 | +7.812500 | 29/19 | 0.0967063264 | [-2.854865, 18.381653] |
| direction | ascending | placement-only | 128 | 69 / 14 | +42.968750 | 61/6 | 7.47218639e-13 | [32.435249, 52.660000] |
| direction | ascending | text-restate | 128 | 69 / 80 | -8.593750 | 22/33 | 0.947605259 | [-19.809545, 2.806872] |
| direction | descending | eviction-only | 128 | 74 / 49 | +19.531250 | 42/17 | 0.000773583465 | [7.999849, 30.604436] |
| direction | descending | placement-only | 128 | 74 / 18 | +43.750000 | 60/4 | 3.68152232e-14 | [33.817323, 53.094275] |
| direction | descending | text-restate | 128 | 74 / 96 | -17.187500 | 11/33 | 0.999805935 | [-27.001086, -7.336280] |
| family | sort | eviction-only | 256 | 143 / 108 | +13.671875 | 71/36 | 0.000461578998 | [5.847853, 21.375997] |
| family | sort | placement-only | 256 | 143 / 32 | +43.359375 | 121/10 | 1.15311103e-25 | [36.212320, 50.165336] |
| family | sort | text-restate | 256 | 143 / 176 | -12.890625 | 33/66 | 0.999718896 | [-20.336880, -5.367211] |

## CLEAR and NEUTRAL2 direction/default readings

Counts of outputs satisfying each registered value imposition; schema-invalid responses satisfy none. Denominator 128 in each initial-direction cell.

| Initial direction | Arm | Checkpoint | Ascending | Descending | Default | Placeholder |
| --- | --- | --- | --- | --- | --- | --- |
| ascending | neither | CLEAR | 71 | 34 | 0 | 0 |
| ascending | neither | NEUTRAL2 | 72 | 21 | 4 | 0 |
| ascending | placement-only | CLEAR | 2 | 0 | 126 | 0 |
| ascending | placement-only | NEUTRAL2 | 73 | 4 | 20 | 0 |
| ascending | eviction-only | CLEAR | 0 | 0 | 127 | 0 |
| ascending | eviction-only | NEUTRAL2 | 0 | 0 | 128 | 0 |
| ascending | both | CLEAR | 0 | 0 | 98 | 0 |
| ascending | both | NEUTRAL2 | 0 | 0 | 128 | 0 |
| ascending | text-restate | CLEAR | 21 | 0 | 105 | 0 |
| ascending | text-restate | NEUTRAL2 | 0 | 0 | 128 | 0 |
| descending | neither | CLEAR | 25 | 63 | 2 | 0 |
| descending | neither | NEUTRAL2 | 18 | 58 | 7 | 0 |
| descending | placement-only | CLEAR | 1 | 0 | 127 | 0 |
| descending | placement-only | NEUTRAL2 | 42 | 20 | 23 | 0 |
| descending | eviction-only | CLEAR | 0 | 0 | 126 | 0 |
| descending | eviction-only | NEUTRAL2 | 0 | 0 | 127 | 0 |
| descending | both | CLEAR | 0 | 0 | 100 | 0 |
| descending | both | NEUTRAL2 | 0 | 0 | 128 | 0 |
| descending | text-restate | CLEAR | 1 | 0 | 123 | 0 |
| descending | text-restate | NEUTRAL2 | 0 | 0 | 128 | 0 |

## Interpretation limits and prewritten readings

Prewritten readings (v1 anchor retained; v2 committed before any FOCUS-2 outcome, with development outcomes disclosed): PASS requires competence, all primary comparisons/magnitude and safety, within scope below; significant but <5-point component gains -> PASS with MARGINAL ADDED CONTROL, no headline joint-control claim. Failure to beat placement/text -> no demonstrated extra mechanism (compatible with prompting), not equivalence. Repair STOP/loss of CLEAR gains -> release fragile, do not proceed/promote. Primary benefit plus collateral/breakage failure -> unsafe context management, do not promote. Benefit confined to wrong prior answers -> error-demonstration cleanup; no stale-correct mechanism claim. If both fails, still publish the fixed placement-only >= text-restate and eviction-only vs neither secondary readings with their limits above. Other failed contrasts -> FAIL, not a compact-state conclusion; INELIGIBLE/INCOMPLETE/INVALID earn no efficacy claim. A null on the stringent all-five endpoint is not evidence of absence or established power.

"context-management mechanism on a frozen trunk; not compact state, not waves"; oracle-managed synthetic episodes only, no autonomous change detection, benchmark transfer, literature priority, Miller weight-circuit selection, or general safety claim. Retained HOLD asymmetry and default priors stay visible. Neither/eviction-only alone cannot carry a headline.

Absence of detected harm plus a count cap; not proof of noninferiority.

Source artifacts: [analysis.json](analysis.json), [analysis-audit.json](analysis-audit.json), [run receipt](outputs/run/end.json), [launch receipt](launch-receipt.json), [frozen registration](freeze/section.md), [preserved assembly failure](stop-at-freeze/failure.json).
