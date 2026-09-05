# FOCUS-2c Amendment 2 — FAIL-SAFETY

Data lineage: fit-on **none**; evaluated-on the unchanged synthetic final bank, disjoint from frozen development inputs. No training or benchmark data. Standing competence and the amended timing-pilot prefix were disclosed before this cost-only amendment.

The registered sixth both-only broken episode stopped the final scheduler after **11 of 256 episodes**, all in the first ascending-initial-direction, zero-delay cell. The other 245 episodes were never scheduled. All 297 generated request records are complete and retained. CPU analysis and an independent raw-record bookkeeping audit confirm the stop. The GPU returned cooperatively; no process was signaled.

Frozen competence remains ascending 63/64, descending 59/64, default 64/64. No competence or pilot response was regenerated. Amendment 2 uses the existing pilot measurement directly under the explicit ruling; the historical pilot remains INCOMPLETE with two completed cells, and no four-cell passing certificate is claimed.

## Registered readings on the observed prefix

All numbers below use the observed n=11 unless stated. The registered denominators remain 256 episodes and 64 assistant-memo episodes. This is a safety-stopped prefix from one cell, not a completed or balanced matrix. Paired tests and asymptotic intervals are nominal descriptive outputs on that prefix; they cannot establish the registered full-matrix efficacy endpoint, equivalence, or absence.

| Arm | All-five successes / observed 11 |
|---|---:|
| both | 0/11 |
| eviction-only | 1/11 |
| neither | 0/11 |
| placement-only | 1/11 |
| text-restate | 3/11 |

| Primary: both versus | b, c | Difference (percentage points) | Nominal paired-score 95% interval (points) | Exact one-sided p | Holm p |
|---|---:|---:|---:|---:|---:|
| eviction-only | 0, 1 | -9.09 | [-37.74, 19.15] | 1 | 1 |
| placement-only | 0, 1 | -9.09 | [-37.74, 19.15] | 1 | 1 |
| text-restate | 0, 3 | -27.27 | [-56.56, 5.67] | 1 | 1 |

**F6 safety:** both has a broken response in 11/11 episodes; text-restate in 5/11. Paired table [[5,6],[0,0]], h=6, r=0, nominal exact harm p=.015625. The raw h<=5 cap was first exceeded at final:sort:ascending:0:10 (the eleventh episode); no later episode was generated. The full-denominator upper-h confidence bound is unavailable.

At NEUTRAL2, all 11 both-arm responses are valid JSON objects that omit the required tag, and all fail the registered schema check. None of these 11 responses is truncated, empty, repetitive, or a period placeholder. Both-arm HOLD also has 7/11 schema-invalid responses. These describe the observed outputs; no causal diagnosis or repair is inferred.

User-fact, tool-fact and unchanged-constraint failures are each both 11/11 versus text-restate 2/11, h=9, r=0, nominal exact harm p=.001953125; none has a passing full-matrix gate. Assistant-fact failures are disclosed, not gated: both 11/11 versus text-restate 10/11 (fixed memo denominator 64), h=1, r=0, p=.5. Ten of 11 shared SET memo sources were invalid/missing; that source-invalid stratum has failures 10/10 versus 10/10, and the single valid-source episode has 1/1 versus 0/1.

**Secondary readings:** placement-only >= text-restate is false in the prefix (1/11 versus 3/11, b=0,c=2, delta=-18.18 points, p=1, nominal 95% interval [-47.70,12.41] points). Eviction-only versus neither is 1/11 versus 0/11 (b=1,c=0, delta=+9.09 points, p=.5, interval [-19.15,37.74] points). Neither comparison rescues the safety terminal or establishes noninferiority/equivalence.

**F11:** both-correct prior stratum n=9: both 0, placement-only 1, eviction-only 1, text-restate 3; prior-error stratum n=2: each of these arms has zero all-five successes. No positive added-control or stale-correct mechanism effect is demonstrated. No descending-initial-direction or 512-token-delay final episode was reached. Final delay attempts, retries and exclusions are all zero; the amended pilot delay observations stand separately.

| Arm | SWITCH | HOLD | BACK | CLEAR | NEUTRAL2 |
|---|---:|---:|---:|---:|---:|
| neither | 6/11 | 8/11 | 8/11 | 0/11 | 0/11 |
| placement-only | 9/11 | 7/11 | 10/11 | 11/11 | 1/11 |
| eviction-only | 4/11 | 8/11 | 7/11 | 11/11 | 8/11 |
| both | 5/11 | 1/11 | 9/11 | 11/11 | 0/11 |
| text-restate | 10/11 | 11/11 | 9/11 | 9/11 | 6/11 |

Default-copy impositions at CLEAR/NEUTRAL2 are neither 0/0, placement-only 11/1, eviction-only 11/10, both 11/0, text-restate 9/9 (each observed out of 11; per-direction registered denominator 128). Full ascending/descending/default imposition tables and checkpoint flag counts are retained in analysis.json. CLEAR gains do not recover subsequent failures or rescue the all-five endpoint.

## Cost and provenance

Final-stage allocation: 700.891718210 seconds, including 33.641167659 seconds of model loading. Prior competence/pilots: 571.490530856 seconds. Cumulative allocation: 1272.382249066 seconds = 0.353439514 GPU-h. CPU analysis: 9.068784174 seconds, conservatively charged against the cap. Total charged: 1281.451033240 seconds = **0.355958620 hours of 8**. The stop was safety, not cost.

Authorizing historical projection lower bound: 24,481.54566539952 seconds. Conservative unchanged-rule projection using the complete amended-pilot non-load duration as a worst-cell upper bound: 24,653.588666807977 seconds including prior spend and the 25% reserve (6.848219074113326 hours). No new pilot. Earlier FOCUS-2 0.289918 GPU-h, FOCUS-2b 0.096616 GPU-h and checks 37/38/39 14.715/8.02/16.591 GPU-min remain separately disclosed development.

- Cost amendment: 129386f; adapter and CPU acceptance: 2e22e274b443513f05a8cb30a037243465b9c15e; re-registration: cd7d1f1.
- Science freeze unchanged: 658622149ea6589f5ea68e2d9f07921f0899a3b8; manifest e97c205bc54e889605ff7b9e2e9f2faf6bfbe4e4d25f11c60ff8165b0ea5bb87.
- [Launch receipt](launch-receipt.json), [analysis](analysis.json), [terminal audit](terminal-audit.json), [audit script](terminal-audit.py.txt).
- Final raw records and start/end receipts: [unchanged frozen output path](../amendment1/outputs/run/).
- CPU acceptance: 100 passed, 1 expected legacy xfail; Ruff clean. All frozen scientific dependencies were checked before model loading and again before analysis.

In plain language, the higher budget allowed the final experiment to start, but the combined placement-and-eviction arm quickly violated the registered breakage limit. At the second neutral request it consistently dropped the required tag. Competence still passes, but these context-management results are unsafe under the registered rule and must not be promoted. The stopped prefix cannot tell us how the full 256-episode comparison or the unrun conditions would have performed. There is no efficacy, compact-state, wave, or benchmark-transfer claim.
