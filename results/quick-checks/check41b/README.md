# Quick check 41b — causal decision-position neurons (2026-09-05)

Prewritten reading, frozen before model execution; seed 41042; dense Qwen3-4B.
Data lineage: no fitting, training, parameter updates or benchmark input reads.
Gradient readout on 32 uncued synthetic fit tasks; cued JS/Python and uncued
activations from those same tasks only. Cell selection on 8 separate setup tasks;
evaluation on 32 fresh uncued tasks, disjoint IDs and full prompts. The check41
operation bank/parser/checkers are reused; operation families overlap. New check41b
function names prevent exact prompt overlap with previous checks. No sealed input.

Decision position is the final prompt position predicting generated token 1.
c = logsumexp(logits of literal JS tokens function,const,let,//,async) minus
logsumexp(logits of literal Python tokens def,import,class,#,from). Each literal
must encode as one token, with no leading whitespace variants. Preserve token IDs,
per-task top-1 defaults, actual first tokens and first eight tokens. A code fence
can be the actual first token: do not silently move the readout to a later token.
For all 36 layers, use the actual SiLU(gate)*up input to down_proj. Average
x * dc/dx at that position over 32 uncued tasks; save per-task gradients, x and
attributions, plus cued-minus-uncued differences and language-cued means. Rank by
absolute signed mean attribution, stable flat-index ties; k in {50,200,800}.
Report sign/layer distributions and intersections with all check41 frequency sets.

Grid: 8 setup tasks x [k={50,200,800}, T={1,4,16}, multiplicative g={1,3,8}
or cued-mean clamp (no g)] = 36 cells, 288 generations. Positive attribution
neurons multiply by 1+g and negative by 1-g toward JS; swapped reverses sign.
Clamp sets selected neurons to their fit-task cued-JS mean; swapped uses the
cued-Python mean. Shuffled selects random other neurons matched per-layer sign
counts, with their own cued means for clamp. Exactly the first T token-predicting
positions are modified: final prompt position then T-1 decode positions; release
from prediction T+1 onward. Earlier cached changes persist naturally after release.
Pick most valid JS, then least breakage; residual ties lower k, lower T,
multiplicative before clamp, lower gain. Freeze before any screen output.

Screen: all 32 fresh SET tasks, each in correct/swapped/shuffled/OFF/text-cue arms.
If correct SET >=12/32, extend first 16 SET trajectories with their own retained
histories through HOLD/SWITCH/BACK/CLEAR on rotated screen tasks. Reapply first-T
intervention on each active request; SWITCH targets Python, BACK JavaScript,
CLEAR has no intervention or new cue. OFF never has a cue; text-cue explicitly
names the target each active request. No neutral step required in this check.
Parse language, reuse coarse task check and breakage; generated programs never run.
Log c and paired OFF shift for fresh SET, plus same-history unmodified c/shift on
every request (text-cue shift compared with identical history minus current cue).

FIXED READING: POSSIBLE if correct valid JavaScript >=20/32, correct breakage <=2/32,
and shuffled valid JavaScript <=4/32 at SET. Otherwise MARGINAL if correct valid
JavaScript >=12/32; else NOT POSSIBLE. An incomplete screen is PARTIAL, never a
negative finding. On NOT POSSIBLE state plainly: the language decision is not
carried by identifiable MLP neurons at the decision position on this trunk under
this registered selector and intervention. This bounded result cannot exclude
other contrast definitions, sites or distributed representations.

Foreground only; no process signals. Wait behind check41 and check40b, check40b
RUNNING.flag included; poll resources every 600 seconds. Queue on .review.lock
to serialize with the existing check42 waiter. Write our RUNNING.flag only when
holding the GPU slot, remove on exit. 5400-second allocation cap including model
load, pilot, attribution and generation. Cooperative per-forward/per-token stop,
30-second cleanup reserve. No outcome-based redesign or rerun of the screen.
CPU tests verify autograd and first-T hooks through real tiny Qwen3 consumers.
The first setup generation is the charged pilot; record timing and full-design
projection before the remaining matrix. If the projection exceeds the cap, stop
with PARTIAL instead of shrinking the design after seeing outcomes.


Observed results

**MARGINAL** under the prewritten SET reading. Completed in 40.30/90 GPU minutes.

| Arm | Valid JS | Valid Python | Broken | Coarse task | JS + task | Mean c | Mean Δc |
|---|---:|---:|---:|---:|---:|---:|---:|
| OFF | 0/32 | 31/32 | 1/32 | 30/32 | 0/32 | -19.721 | +0.000 |
| correct | 14/32 | 11/32 | 7/32 | 24/32 | 13/32 | 0.875 | +20.596 |
| shuffled | 0/32 | 31/32 | 1/32 | 30/32 | 0/32 | -19.497 | +0.224 |
| swapped | 0/32 | 32/32 | 0/32 | 31/32 | 0/32 | 1.190 | +20.911 |
| text-cue | 32/32 | 0/32 | 0/32 | 28/32 | 28/32 | 22.179 | +41.900 |

Δc compares each request with an unmodified forward pass on the same history and current task without a new cue. For fresh SET this also equals the paired OFF-arm difference. Raw logits are recorded before token 1.

| Arm | Actual first token counts |
|---|---|
| OFF | {"&#96;&#96;&#96;": 32} |
| correct | {" moduleId": 23, "///<": 3, "_^(": 1, "edImage": 3, "一条龙": 1, "簉": 1} |
| shuffled | {"&#96;&#96;&#96;": 32} |
| swapped | {"仓": 1, "孰": 31} |
| text-cue | {"&#96;&#96;&#96;": 32} |

Observed qualification: correct SET starts with ` moduleId` on 23/32 responses; the other first tokens are shown above. These prefixes are not clean code-only answers. The reused checker can accept a labeled JavaScript statement or ignore text outside a fenced code block. Thus the fixed language reading is parser-level evidence, not a claim that the entire response is a runnable program.

Both correct and swapped raise c by about 21 logits at g=3, while only correct induces JavaScript. The first-order attribution sign does not predict the direction of this large finite perturbation. The scalar contrast and the emitted-token context must be distinguished.

Frozen setting: k=200, g=3, T=1, multiply; setup valid JS 4/8, broken 1/8. All 36 cells completed; zero screen records existed at freeze.

Causal selection produced some language induction, but it failed the full feasibility reading. The logit effect and parser outcomes must be distinguished; these results do not establish a reliable language actuator.

The correct SET count triggered all 16 retained-history episodes. Each arm retained its own SET response and subsequent answers.

| Arm / stage | Valid JS | Valid Python | Broken | Coarse task | Mean Δc |
|---|---:|---:|---:|---:|---:|
| correct / HOLD | 7/16 | 7/16 | 2/16 | 13/16 | -2.974 |
| correct / SWITCH | 7/16 | 8/16 | 1/16 | 15/16 | -0.019 |
| correct / BACK | 7/16 | 7/16 | 2/16 | 12/16 | -4.696 |
| correct / CLEAR | 7/16 | 8/16 | 1/16 | 13/16 | +0.000 |
| swapped / HOLD | 0/16 | 16/16 | 0/16 | 16/16 | +36.082 |
| swapped / SWITCH | 0/16 | 13/16 | 3/16 | 13/16 | +39.541 |
| swapped / BACK | 0/16 | 16/16 | 0/16 | 15/16 | +36.936 |
| swapped / CLEAR | 0/16 | 16/16 | 0/16 | 15/16 | +0.000 |
| shuffled / HOLD | 0/16 | 16/16 | 0/16 | 16/16 | +1.255 |
| shuffled / SWITCH | 0/16 | 16/16 | 0/16 | 16/16 | -0.758 |
| shuffled / BACK | 0/16 | 16/16 | 0/16 | 15/16 | +1.361 |
| shuffled / CLEAR | 0/16 | 16/16 | 0/16 | 14/16 | +0.000 |
| OFF / HOLD | 0/16 | 16/16 | 0/16 | 16/16 | +0.000 |
| OFF / SWITCH | 0/16 | 16/16 | 0/16 | 16/16 | +0.000 |
| OFF / BACK | 0/16 | 16/16 | 0/16 | 15/16 | +0.000 |
| OFF / CLEAR | 0/16 | 16/16 | 0/16 | 14/16 | +0.000 |
| text-cue / HOLD | 16/16 | 0/16 | 0/16 | 13/16 | +1.276 |
| text-cue / SWITCH | 0/16 | 16/16 | 0/16 | 16/16 | -27.087 |
| text-cue / BACK | 16/16 | 0/16 | 0/16 | 13/16 | +26.515 |
| text-cue / CLEAR | 4/16 | 10/16 | 2/16 | 13/16 | +0.000 |

Decision readout and neuron distribution

The uncued first token was a code fence on 31/32 fit tasks; the remaining token counts are in attribution-summary.json. The readout stayed at the registered first prediction position.
Mean fit c: uncued -19.128, cued JS 21.652, cued Python -21.181.

| Layer | k50 + | k50 − | k200 + | k200 − | k800 + | k800 − |
|---|---:|---:|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| 1 | 0 | 0 | 0 | 0 | 2 | 1 |
| 2 | 0 | 0 | 0 | 0 | 3 | 1 |
| 3 | 0 | 1 | 0 | 3 | 1 | 4 |
| 4 | 0 | 1 | 0 | 1 | 0 | 3 |
| 5 | 1 | 0 | 1 | 1 | 4 | 2 |
| 6 | 0 | 0 | 4 | 3 | 5 | 11 |
| 7 | 1 | 0 | 2 | 0 | 4 | 6 |
| 8 | 0 | 0 | 0 | 1 | 5 | 3 |
| 9 | 0 | 0 | 1 | 1 | 11 | 9 |
| 10 | 1 | 1 | 4 | 1 | 10 | 8 |
| 11 | 1 | 0 | 1 | 2 | 11 | 7 |
| 12 | 0 | 0 | 0 | 1 | 14 | 15 |
| 13 | 0 | 0 | 4 | 7 | 16 | 13 |
| 14 | 0 | 1 | 4 | 5 | 20 | 24 |
| 15 | 0 | 0 | 1 | 3 | 11 | 14 |
| 16 | 0 | 0 | 1 | 4 | 7 | 24 |
| 17 | 0 | 0 | 1 | 3 | 16 | 15 |
| 18 | 0 | 1 | 5 | 4 | 14 | 18 |
| 19 | 0 | 0 | 5 | 3 | 17 | 19 |
| 20 | 3 | 2 | 7 | 8 | 23 | 26 |
| 21 | 2 | 1 | 6 | 8 | 18 | 28 |
| 22 | 3 | 0 | 5 | 3 | 15 | 15 |
| 23 | 2 | 1 | 6 | 4 | 23 | 25 |
| 24 | 4 | 1 | 6 | 4 | 24 | 18 |
| 25 | 1 | 0 | 4 | 2 | 16 | 13 |
| 26 | 0 | 0 | 3 | 0 | 13 | 14 |
| 27 | 1 | 2 | 4 | 2 | 11 | 6 |
| 28 | 2 | 1 | 2 | 2 | 10 | 3 |
| 29 | 1 | 1 | 3 | 1 | 8 | 3 |
| 30 | 0 | 0 | 0 | 2 | 6 | 4 |
| 31 | 0 | 1 | 3 | 2 | 8 | 6 |
| 32 | 1 | 0 | 2 | 1 | 9 | 5 |
| 33 | 0 | 2 | 3 | 2 | 8 | 11 |
| 34 | 1 | 3 | 4 | 5 | 13 | 11 |
| 35 | 3 | 2 | 12 | 7 | 26 | 12 |

Signs refer to the signed mean activation × gradient. Counts total 28+/22−, 104+/96− and 403+/397− for k=50/200/800.

| Causal k | Frequency k | JS intersection | Python intersection |
|---|---|---:|---:|
| 50 | 200 | 0 | 1 |
| 50 | 500 | 0 | 1 |
| 50 | 1000 | 0 | 2 |
| 200 | 200 | 0 | 2 |
| 200 | 500 | 0 | 2 |
| 200 | 1000 | 0 | 4 |
| 800 | 200 | 2 | 4 |
| 800 | 500 | 2 | 4 |
| 800 | 1000 | 2 | 6 |

Setup grid

| k | g | T | Variant | Valid JS /8 | Broken /8 | Mean Δc |
|---:|---:|---:|---|---:|---:|---:|
| 50 | 1 | 1 | multiply | 0 | 0 | +20.521 |
| 50 | 3 | 1 | multiply | 0 | 5 | +20.638 |
| 50 | 8 | 1 | multiply | 0 | 0 | +18.861 |
| 50 | 0 | 1 | clamp | 0 | 0 | +13.400 |
| 50 | 1 | 4 | multiply | 0 | 0 | +20.521 |
| 50 | 3 | 4 | multiply | 0 | 5 | +20.638 |
| 50 | 8 | 4 | multiply | 0 | 3 | +18.861 |
| 50 | 0 | 4 | clamp | 0 | 1 | +13.400 |
| 50 | 1 | 16 | multiply | 0 | 0 | +20.521 |
| 50 | 3 | 16 | multiply | 0 | 8 | +20.638 |
| 50 | 8 | 16 | multiply | 0 | 8 | +18.861 |
| 50 | 0 | 16 | clamp | 0 | 2 | +13.400 |
| 200 | 1 | 1 | multiply | 0 | 0 | +21.213 |
| 200 | 3 | 1 | multiply | 4 | 1 | +21.350 |
| 200 | 8 | 1 | multiply | 0 | 1 | +21.222 |
| 200 | 0 | 1 | clamp | 0 | 0 | +19.311 |
| 200 | 1 | 4 | multiply | 1 | 2 | +21.213 |
| 200 | 3 | 4 | multiply | 1 | 3 | +21.350 |
| 200 | 8 | 4 | multiply | 0 | 7 | +21.222 |
| 200 | 0 | 4 | clamp | 4 | 2 | +19.311 |
| 200 | 1 | 16 | multiply | 2 | 2 | +21.213 |
| 200 | 3 | 16 | multiply | 0 | 6 | +21.350 |
| 200 | 8 | 16 | multiply | 0 | 7 | +21.222 |
| 200 | 0 | 16 | clamp | 3 | 3 | +19.311 |
| 800 | 1 | 1 | multiply | 0 | 0 | +20.994 |
| 800 | 3 | 1 | multiply | 0 | 0 | +21.052 |
| 800 | 8 | 1 | multiply | 0 | 0 | +21.961 |
| 800 | 0 | 1 | clamp | 0 | 0 | +24.550 |
| 800 | 1 | 4 | multiply | 0 | 8 | +20.994 |
| 800 | 3 | 4 | multiply | 0 | 2 | +21.052 |
| 800 | 8 | 4 | multiply | 0 | 5 | +21.961 |
| 800 | 0 | 4 | clamp | 0 | 8 | +24.550 |
| 800 | 1 | 16 | multiply | 0 | 8 | +20.994 |
| 800 | 3 | 16 | multiply | 0 | 8 | +21.052 |
| 800 | 8 | 16 | multiply | 0 | 6 | +21.961 |
| 800 | 0 | 16 | clamp | 0 | 8 | +24.550 |

Validation and artifacts

Consumer audit PASS: 800 generations, 32 decision tasks, all 36 setup cells. Recomputed all attribution products/means, selected sets and overlaps; rescored every parser result; checked every intervention position, OFF identity, frozen choice, screen reading and conditional histories. CPU gradient/decoding fixtures and import-side-effect checks passed (one known legacy inventory xfail). Ruff passed.
Model/tokenizer hashes match all ten assets in check41’s frozen reference. No weights were fitted or updated. No sealed inputs were read; no process was signaled; foreground execution only. RUNNING.flag was removed at completion.
records.jsonl preserves full prompts, histories, outputs, tokens, intervention counts, timing, parser/task/breakage flags and c shifts. decision-records.jsonl and attributions/ preserve the per-task gradient readout; attributions/README.md describes all arrays. Coarse task checks are syntax/operation witnesses; generated programs were never executed.
The reported first-T release disables new hooks after T predictions; intervened cache states persist naturally. Operation families overlap across otherwise disjoint fit/setup/screen prompts. The keyword-set contrast can move while the actual first token remains a fence. These are limits of this registered construction.

The same seven correct-arm episodes (0, 2, 3, 4, 6, 7, 9) produced valid JavaScript at all four retained-history stages, including SWITCH and CLEAR; history-diagnostics.json records the exact episode identities.

**Correction (astra full review, 2026-09-05)**: (F1, F5) For checks 40b/40c/40d/41b, the provenance description is “locally frozen before execution according to run receipts”. Their freeze files first entered Git with results; matching local hashes and timestamps do not independently establish pre-outcome Git commitment. Checks 41/40e/43 have pre-generation Git anchors. Some checks 34–38 have launch-copy/hash evidence; check39’s exact reading was committed before its recorded start. These are not all committed preregistrations; no fabricated chronology was found. Check41b’s accepted fences/labels can hide damaged prefixes; its 14 parser successes are not 14 clean complete programs. Both signs give large positive proxy shifts, so that proxy does not validate directionality. The same seven JS histories persist through SWITCH/CLEAR; the Python defaults are not successful release of those induced histories.
