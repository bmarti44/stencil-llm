# Quick check 32 (Q4): operand-free KV packet transplant

Unregistered, disclosed quick check; seed 32040; 2026-09-05. Q2 was declined by Brian and never run to completion. Sources: `results/hypotheses-fable.md` #3 and `results/hypotheses-astra.md` #4. This tests extracted latent instructions, not training or a claim of content-free circuitry.

## Fixed reading — written before any Q4 model execution

For each trunk, 64 paired episodes, each with SET(A), HOLD(A), SWITCH(B), BACK(A), CLEAR(copy). **PASS** requires correct-packet SET/HOLD/SWITCH/BACK jointly value-exact in >=40/64 episodes; text-cue bar jointly >=48/64 (otherwise **INELIGIBLE**); swapped packet jointly follows B/B/A/B in >=40/64; shuffled packet produces either task on ANY of the first four decisions in <=8/64; correct-packet breakage on ANY of five decisions <=2/64; correct-packet CLEAR impositions (A or B output) <=2/64; and the per-layer residual audit is reported. **MARGINAL** requires correct SET alone >=32/64 and shuffled induction <=8/64, provided the text bar is eligible. **FAIL** otherwise. Incomplete matrices are **PARTIAL**, with counts and no extrapolated verdict. The layer >=12 diagnostic cannot rescue the primary all-layer verdict. HOLD without reapplication is reported separately. Thresholds will not change after outcomes.

Breakage means truncated output, repeated 4-gram fraction >0.2, duplicated output integers, or inability to parse a list of integers after format-only leniency. Leniency accepts code fences, quoted integer entries and a single list embedded in prose; it never drops/adds values, changes signs or reorders. Strict JSON integer-list exactness is recorded too. Because reverse(input) cannot equal a distinct input, “exclude already in A- or B-form” is conservatively implemented as rejecting ascending AND descending inputs; this also ensures A, B and copy targets differ. All 320 unordered operand sets are unique, with 5–8 distinct integers in -20..20.

## Frozen implementation choices and lineage

Extraction-only, fit-on=nothing: 32 operand/answer-free authored cue paraphrases each for A, B and OFF, with seed-shuffled order separate from the seed-32040 evaluation RNG. Donor and recipient suffix positions are identically 80–83 (zero-based absolute positions). A generic JSON-format system prefix and explicit space-token padding align all inputs; the suffix is exactly four tokens, ` The context is ready`. No donor cue columns are copied. Each packet averages suffix post-RoPE K and V in fp32, then casts to bf16 for cache replacement. Per-layer K/V norms and joint cosine(A,B) are reported. No benchmark inputs or recorded benchmark responses are accessed; no fitting, training, tuning or test-driven selection.

Six arms: correct all layers, swapped all layers, per-episode independent random K/V with each layer's K and V norm matched to the corresponding packet, OFF throughout, text-cue bar with no cache edits, correct at layers >=12 only (zero-based). Same lists across arms and trunks. SET is a one-shot four-column write before the operand query; HOLD retains those columns across a 128-token neutral filler turn and makes zero writes. SWITCH/BACK overwrite those columns; CLEAR restores packet_OFF there without rebuilding any other columns. OFF is installed once and retained throughout. Text bar has A in its initial system prompt, no new cue for HOLD, B at SWITCH, A at BACK, and an explicit copy request at CLEAR. All generated tokens and EOS stay in history; greedy hook-free generation, maximum 64 output tokens per decision.

A simultaneous teacher-forced OFF replay receives the treated arm's identical token IDs with identical forward-call boundaries, using the second row of a batch of two. It begins from the same neutral recipient prefix plus packet_OFF, never task packets. Thus full-cache residuals isolate changed cache state on identical histories without differences caused by separately generated answers or prefill chunking. At CLEAR record per-layer K/V max-absolute differences for the four restored positions, all remaining positions, and the whole cache, plus bitwise-equality flags. In the subset arm, low layers remain the clean neutral prefix and the shadow matches that baseline. Text bar has no surgery; its shadow is an identical text replay and is labelled accordingly. Restored-column equality alone does not establish whole-cache clearance; residuals are descriptive, not an additional zero-residual pass threshold.

GPU precheck: compute-app query and pmon empty; no holders of `/dev/nvidia0` or `/dev/nvidia-uvm`. GB10 utilization remained fixed at 96%, memory activity 0%, power 19W; disclosed as apparently stale utilization telemetry. Compute processes are checked again before loading and periodically during execution; any foreign compute process aborts the run cooperatively. Foreground only; no process signals; 90 GPU-minutes total, 4B first. The cap includes extraction, loading and audit work, with partial records flushed as produced.

## Results

Authorized rerun completed on 2026-09-05, **4B first, then 1.7B**, in **73.74 GPU-minutes total**, below the 90-minute cap. Both trunks completed all 64 episodes in all six arms (3,840 decisions total). The new pre-launch `nvidia-smi` check showed 0% utilization and no compute apps. The earlier aborted attempt and its telemetry are preserved in `prior-abort-4f039a4/`; `rerun-before-run.md` preserves the exact README hashed by this execution. The prepared script and every byte above Results remain unchanged from `4f039a4`. No process was signalled, no sealed benchmark contents were read, and no fitting or training occurred.

CPU scorer/cache/fake-trunk checks, Ruff, and targeted import checks passed (3 passed, 1 expected legacy xfail). Per-trunk `validation.json` records verification of all raw scores, token histories, extraction IDs, packet norms/cosines/hashes, HOLD retention, and residual aggregates. An initial audit assumption of bitwise-equal text replay was rejected by the measured control; the discrepancy is explicitly reported below.

### 4b: **INELIGIBLE**

| Arm | n | SET | HOLD (no reapply) | SWITCH | BACK | Joint | Strict joint | CLEAR copy | Impositions | Breakage | Any induction |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| correct | 64 | 0 | 0 | 0 | 0 | 0 | 0 | 64 | 0 | 0 | 0 |
| swapped | 64 | 0 | 0 | 0 | 0 | 0 | 0 | 64 | 0 | 0 | 0 |
| shuffled | 64 | 0 | 0 | 0 | 0 | 0 | 0 | 64 | 0 | 64 | 0 |
| off | 64 | 0 | 0 | 0 | 0 | 0 | 0 | 64 | 0 | 0 | 0 |
| text | 64 | 59 | 64 | 33 | 62 | 29 | 27 | 64 | 0 | 1 | 64 |
| layers_ge12 | 64 | 0 | 0 | 0 | 0 | 0 | 0 | 64 | 0 | 0 | 0 |

Counts use each arm’s completed episodes; decision denominators for partial runs are in summary.json. Swapped target is B/B/A/B; other task columns target A/A/B/A. Any induction means either task on any of the first four decisions.

The fixed reading is **INELIGIBLE** because the text-cue bar completed only 29/64 full sequences (required: 48/64). The correct packet completed 0/64 sequences: SET, HOLD without reapplication, SWITCH and BACK each scored 0/64, and its first four outputs always copied the input. Swapped and layer >=12 packets likewise induced no task. CLEAR copied correctly in 64/64, with 0/64 task impositions and 0/64 correct-arm breakage, but no task had been established to erase. All four restored columns were bitwise equal to OFF; the remaining cache was unequal in every correct-arm episode. This extraction provides no evidence of usable retained task state or whole-cache clear-by-restore on this trunk; the missed text bar limits a general mechanism verdict. Runtime: 47.93 GPU-minutes.

Maximum residual over all layers and CLEAR episodes (exact-token OFF replay):

| Arm | Max restored K | Max restored V | Max outside K | Max outside V |
|---|---:|---:|---:|---:|
| correct | 0 | 0 | 23.5391 | 31.5625 |
| swapped | 0 | 0 | 24.5625 | 31.6234 |
| shuffled | 0 | 0 | 91.1719 | 96.125 |
| off | 0 | 0 | 1.3125 | 2.60547 |
| text | 0 | 0 | 1 | 2.25 |
| layers_ge12 | 0 | 0 | 30.5 | 32.1562 |

Every layer is retained in summary.json and each CLEAR record. Zero restored-column difference does not imply zero downstream residual. Packet norms and cosines for every layer are in packet-stats.json; extraction cue IDs and exact tokens are in extraction.jsonl; packet tensors are in packets-fp32.pt.

Replay-control audit: off: 2/64 whole-cache-unequal episodes, max K/V 1.3125/2.60547; text: 1/64 whole-cache-unequal episodes, max K/V 1/2.25. Identical-token, unedited batch rows can themselves differ numerically in this run, so raw nonzero residuals cannot be attributed entirely to packet surgery. These discrepancies remain in the records and tables; no subtraction or zero-residual threshold was introduced. Every restored suffix column was bitwise equal in every arm.

The shuffled arm induced neither task (0/64 episodes) but had breakage in 64/64; its negative induction score is not evidence of intact general behavior. Strict per-decision counts are in summary.json, alongside the strict joint column above.

Packet extraction statistics (fp32 means; zero-based layers):

| Layer | A K norm | A V norm | B K norm | B V norm | OFF K norm | OFF V norm | Cosine(A,B) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | 853.352295 | 2.00928068 | 853.352295 | 2.00928068 | 853.352295 | 2.00928068 | 1.00000131 |
| 1 | 197.913284 | 3.14488244 | 198.165634 | 3.15093327 | 197.730438 | 3.14477921 | 0.99994266 |
| 2 | 106.003006 | 4.54696035 | 106.837723 | 4.5350008 | 106.567764 | 4.49432802 | 0.999343812 |
| 3 | 127.722221 | 6.30638552 | 127.463921 | 6.26308393 | 126.864479 | 6.18485165 | 0.999024808 |
| 4 | 205.143127 | 8.17820072 | 207.512802 | 8.17672348 | 214.395477 | 8.10925388 | 0.999317765 |
| 5 | 306.807465 | 9.23504543 | 310.479706 | 9.27699471 | 314.906464 | 9.23087788 | 0.999368191 |
| 6 | 155.622498 | 12.8202944 | 157.727158 | 12.8420525 | 159.118774 | 12.3378887 | 0.999259531 |
| 7 | 123.56144 | 17.8861923 | 123.364441 | 17.7540989 | 122.648476 | 16.8642292 | 0.998592854 |
| 8 | 200.073227 | 22.2265549 | 201.12616 | 22.0901413 | 206.133133 | 21.1571388 | 0.999064803 |
| 9 | 115.246307 | 23.1243706 | 115.395256 | 22.6826267 | 114.309097 | 21.4072056 | 0.997062922 |
| 10 | 164.502975 | 29.8325672 | 165.223465 | 29.576376 | 168.988892 | 27.6184616 | 0.998331785 |
| 11 | 173.829132 | 19.9770145 | 174.653122 | 20.0035458 | 175.26503 | 18.523695 | 0.998486698 |
| 12 | 137.323593 | 22.2885704 | 138.394196 | 22.2874146 | 137.928726 | 21.7697754 | 0.997388482 |
| 13 | 118.072823 | 21.3383999 | 116.938034 | 21.5377941 | 117.057907 | 20.0938625 | 0.991698027 |
| 14 | 148.338654 | 25.4678173 | 148.58136 | 25.3792858 | 146.788025 | 23.6311226 | 0.997428179 |
| 15 | 124.002716 | 24.1718636 | 123.69825 | 24.1576557 | 121.454529 | 23.1495495 | 0.994905531 |
| 16 | 115.43306 | 31.0111752 | 115.537117 | 30.800108 | 114.907829 | 27.807539 | 0.988627017 |
| 17 | 122.579414 | 25.1250305 | 121.957352 | 25.1170044 | 120.688545 | 23.8365288 | 0.991343558 |
| 18 | 117.852943 | 28.378334 | 117.158722 | 28.5737858 | 115.964943 | 26.8236732 | 0.990209579 |
| 19 | 124.621445 | 38.6510124 | 124.571335 | 38.2727127 | 123.622475 | 35.281311 | 0.992881715 |
| 20 | 122.504845 | 38.8876915 | 121.96817 | 38.8594627 | 120.8918 | 36.1266861 | 0.987721682 |
| 21 | 125.488358 | 41.1655006 | 124.664612 | 41.6243896 | 123.786209 | 38.8488426 | 0.991350651 |
| 22 | 129.624115 | 50.770092 | 129.405869 | 50.5680046 | 128.787415 | 47.3719292 | 0.991752863 |
| 23 | 145.356216 | 51.727459 | 144.870834 | 51.8888664 | 144.247574 | 48.3426704 | 0.993936241 |
| 24 | 123.312599 | 68.9145126 | 122.545555 | 69.3981247 | 121.163414 | 65.855484 | 0.992834985 |
| 25 | 135.473526 | 59.967907 | 134.899323 | 60.2793045 | 134.938309 | 56.3829575 | 0.994654417 |
| 26 | 112.471764 | 72.625618 | 112.114861 | 73.4589233 | 110.758316 | 68.0809021 | 0.992515028 |
| 27 | 111.029076 | 76.8948975 | 111.071678 | 77.9456787 | 110.586357 | 72.9650497 | 0.992169619 |
| 28 | 114.28093 | 86.6965485 | 114.117378 | 87.8732681 | 113.083511 | 82.7251205 | 0.992765009 |
| 29 | 115.167725 | 138.087433 | 114.859024 | 140.641174 | 113.55999 | 134.071945 | 0.993692875 |
| 30 | 127.949013 | 135.987335 | 127.839058 | 138.289246 | 127.785912 | 130.418869 | 0.991038322 |
| 31 | 114.982712 | 172.11525 | 114.967705 | 176.19519 | 113.396545 | 166.162155 | 0.992526531 |
| 32 | 115.785957 | 209.081284 | 115.394402 | 212.616196 | 114.937515 | 205.204529 | 0.992668033 |
| 33 | 110.034973 | 334.388519 | 109.457848 | 340.949646 | 107.485603 | 330.959351 | 0.993814945 |
| 34 | 119.480476 | 261.489288 | 119.344345 | 263.196533 | 118.7052 | 257.715271 | 0.98870331 |
| 35 | 178.434814 | 158.642487 | 181.400024 | 161.145447 | 181.959579 | 156.119995 | 0.990229964 |

Cosines are the raw fp32 computation; roundoff can place values slightly above 1. Full-precision numbers and packet hashes are preserved in the JSON artifacts.


### 1.7b: **INELIGIBLE**

| Arm | n | SET | HOLD (no reapply) | SWITCH | BACK | Joint | Strict joint | CLEAR copy | Impositions | Breakage | Any induction |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| correct | 64 | 0 | 0 | 0 | 0 | 0 | 0 | 64 | 0 | 0 | 0 |
| swapped | 64 | 0 | 0 | 0 | 0 | 0 | 0 | 64 | 0 | 0 | 0 |
| shuffled | 64 | 0 | 0 | 0 | 0 | 0 | 0 | 60 | 0 | 64 | 0 |
| off | 64 | 0 | 0 | 0 | 0 | 0 | 0 | 64 | 0 | 0 | 0 |
| text | 64 | 46 | 50 | 14 | 50 | 6 | 6 | 64 | 0 | 2 | 63 |
| layers_ge12 | 64 | 0 | 0 | 0 | 0 | 0 | 0 | 64 | 0 | 0 | 0 |

Counts use each arm’s completed episodes; decision denominators for partial runs are in summary.json. Swapped target is B/B/A/B; other task columns target A/A/B/A. Any induction means either task on any of the first four decisions.

The fixed reading is **INELIGIBLE** because the text-cue bar completed only 6/64 full sequences (required: 48/64). The correct packet completed 0/64 sequences: SET, HOLD without reapplication, SWITCH and BACK each scored 0/64, and its first four outputs always copied the input. Swapped and layer >=12 packets likewise induced no task. CLEAR copied correctly in 64/64, with 0/64 task impositions and 0/64 correct-arm breakage, but no task had been established to erase. All four restored columns were bitwise equal to OFF; the remaining cache was unequal in every correct-arm episode. This extraction provides no evidence of usable retained task state or whole-cache clear-by-restore on this trunk; the missed text bar limits a general mechanism verdict. Runtime: 25.80 GPU-minutes.

Maximum residual over all layers and CLEAR episodes (exact-token OFF replay):

| Arm | Max restored K | Max restored V | Max outside K | Max outside V |
|---|---:|---:|---:|---:|
| correct | 0 | 0 | 36.125 | 96.5156 |
| swapped | 0 | 0 | 32.75 | 77.6562 |
| shuffled | 0 | 0 | 309 | 250 |
| off | 0 | 0 | 8.03125 | 27.3125 |
| text | 0 | 0 | 14.0625 | 34.3125 |
| layers_ge12 | 0 | 0 | 4.125 | 21 |

Every layer is retained in summary.json and each CLEAR record. Zero restored-column difference does not imply zero downstream residual. Packet norms and cosines for every layer are in packet-stats.json; extraction cue IDs and exact tokens are in extraction.jsonl; packet tensors are in packets-fp32.pt.

Replay-control audit: off: 2/64 whole-cache-unequal episodes, max K/V 8.03125/27.3125; text: 1/64 whole-cache-unequal episodes, max K/V 14.0625/34.3125. Identical-token, unedited batch rows can themselves differ numerically in this run, so raw nonzero residuals cannot be attributed entirely to packet surgery. These discrepancies remain in the records and tables; no subtraction or zero-residual threshold was introduced. Every restored suffix column was bitwise equal in every arm.

The shuffled arm induced neither task (0/64 episodes) but had breakage in 64/64; its negative induction score is not evidence of intact general behavior. Strict per-decision counts are in summary.json, alongside the strict joint column above.

Packet extraction statistics (fp32 means; zero-based layers):

| Layer | A K norm | A V norm | B K norm | B V norm | OFF K norm | OFF V norm | Cosine(A,B) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | 1020.44476 | 9.38146687 | 1020.44476 | 9.38146687 | 1020.44476 | 9.38146687 | 1.00000393 |
| 1 | 498.663147 | 8.00421619 | 498.845947 | 7.97659016 | 498.082245 | 7.97324514 | 0.99998343 |
| 2 | 513.661194 | 10.0554008 | 516.12146 | 10.0392847 | 520.312866 | 9.95481491 | 0.999942482 |
| 3 | 321.67453 | 26.5569878 | 324.339874 | 26.4711742 | 328.85083 | 25.66502 | 0.999760211 |
| 4 | 453.103027 | 26.4800148 | 457.384979 | 26.4633465 | 460.26532 | 25.9125042 | 0.999707282 |
| 5 | 499.746979 | 31.7455597 | 503.074158 | 31.6093769 | 506.718903 | 30.7689133 | 0.999835372 |
| 6 | 318.691895 | 28.1290493 | 317.499756 | 28.2128315 | 322.122467 | 27.3389893 | 0.99954468 |
| 7 | 282.618896 | 42.0940132 | 284.785248 | 41.6443748 | 282.772552 | 41.3183289 | 0.999449611 |
| 8 | 133.533264 | 42.9027252 | 133.68866 | 42.9199371 | 136.132294 | 42.5803032 | 0.997622728 |
| 9 | 201.192612 | 62.7463036 | 200.848282 | 63.0614281 | 201.813446 | 60.443531 | 0.99832207 |
| 10 | 301.212067 | 55.9420242 | 301.521637 | 55.5911484 | 300.573547 | 55.5194092 | 0.999092042 |
| 11 | 151.450958 | 72.3733368 | 150.669083 | 72.279274 | 148.883087 | 72.0473328 | 0.996670008 |
| 12 | 181.03447 | 84.9603729 | 179.83696 | 84.9129868 | 188.808334 | 84.7088852 | 0.996646762 |
| 13 | 117.224869 | 96.8955002 | 116.434616 | 98.4427338 | 116.267769 | 95.5349121 | 0.992657781 |
| 14 | 136.820023 | 110.632774 | 135.386658 | 111.429062 | 138.323303 | 106.317207 | 0.991716444 |
| 15 | 261.337036 | 159.322754 | 257.956238 | 160.656616 | 262.773895 | 150.301956 | 0.994959712 |
| 16 | 138.645172 | 188.774139 | 137.847534 | 189.183456 | 138.650208 | 184.038406 | 0.99246192 |
| 17 | 153.060623 | 290.165497 | 151.336609 | 292.420502 | 152.435608 | 284.758423 | 0.990881681 |
| 18 | 139.357086 | 318.552338 | 139.055664 | 320.251129 | 137.830414 | 312.185822 | 0.992893457 |
| 19 | 146.518829 | 410.367706 | 145.121948 | 412.039825 | 144.298889 | 397.457947 | 0.993580401 |
| 20 | 148.845337 | 509.415527 | 147.809753 | 506.883911 | 148.333694 | 495.662231 | 0.994825184 |
| 21 | 135.885635 | 684.148254 | 135.059387 | 681.270813 | 134.439072 | 663.536011 | 0.995093584 |
| 22 | 117.57222 | 763.841003 | 117.189583 | 755.562805 | 116.890091 | 737.009399 | 0.994029999 |
| 23 | 173.280975 | 878.103577 | 173.402618 | 866.415771 | 174.998566 | 840.079346 | 0.99451077 |
| 24 | 202.418518 | 1143.30688 | 202.210556 | 1125.99036 | 198.364914 | 1104.64453 | 0.995486856 |
| 25 | 184.179871 | 1427.79004 | 183.708237 | 1403.74805 | 182.40509 | 1369.68005 | 0.995433211 |
| 26 | 135.493256 | 1359.73804 | 134.732651 | 1337.37256 | 134.236038 | 1316.5531 | 0.994173169 |
| 27 | 180.756485 | 708.035828 | 181.462128 | 693.470459 | 184.476929 | 661.77948 | 0.980282307 |

Cosines are the raw fp32 computation; roundoff can place values slightly above 1. Full-precision numbers and packet hashes are preserved in the JSON artifacts.
