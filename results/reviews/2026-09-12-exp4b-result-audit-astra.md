**Reviewer: Astra | Model: GPT-6 Astra | Date: 2026-09-12 | Read-only result audit**

**DISCREPANCIES.** All 48 saved generations reproduce under CPU rescoring: per-item `fraction_required`, arm means, bootstrap intervals, sign tests, strict outcomes, and failure categories agree with the committed summary. Qualification correctly **FAILED on condition (b): 1/16 = 6.25% > 5%**. The registered consequence remains **program stops; SCREEN never opened**. Corrections are needed to denominator labels, oracle packing counts, cost reporting, strict-test wording, and interpretation. The implementation review’s cumulative-budget correction remains incomplete, and its promised SCREEN launch guard is not verifiable in the committed implementation. Neither changes this run’s FAILED result. I wrote no files, ran no models, used no GPU, and did not access `data/bench/`.

1. **[low — verified] The compliance statistics reproduce exactly.**  
   Rescoring the committed outputs with the vendored checker reproduces every stored score and failure field. Arm means are **base 0.0656624042, focus 0.1088543685, oracle 0.2625211699**. Independently resampling paired differences in sorted item order, resetting `random.Random(0)` for each contrast, using 10,000 draws and order statistics **251 and 9750**, gives:

   | Contrast | Mean, points | 95% bootstrap interval | Wins/losses/ties | Two-sided sign p |
   |---|---:|---:|---:|---:|
   | focus − base | 4.319196 | [0.093006, 9.531250] | 4/1/11 | 0.375 |
   | oracle − focus | 15.366680 | [4.027478, 27.260401] | 8/3/5 | 0.2265625 |
   | oracle − base | 19.685877 | [7.767231, 33.143094] | 9/1/6 | 0.021484375 |

   All displayed rounding in [RESULTS-4B.md:26](/home/bmarti44/stencil-llm/results/memorycode-long/RESULTS-4B.md:26) and [RESULTS-4B.md:35](/home/bmarti44/stencil-llm/results/memorycode-long/RESULTS-4B.md:35) is correct. Invalid/truncated/degenerate counts reproduce as **5/7/0, 3/6/0, 4/8/1**, respectively; all arms have zero timeouts and zero strict passes. Categories overlap and must not be summed as distinct failed items.

2. **[medium] “Required checks” actually lists distinct required families; oracle packing counts are wrong.**  
   The column at [RESULTS-4B.md:47](/home/bmarti44/stencil-llm/results/memorycode-long/RESULTS-4B.md:47) repeats the weighting ambiguity corrected by amendment 1. In the table’s existing item order, the actual denominator counts are:

   `3, 2, 3, 5, 6, 5, 4, 6, 14, 14, 19, 11, 13, 32, 32, 29`.

   For example, `352-99` has **12 families but 32 equally weighted checks**. The scores themselves use the correct frozen denominators. State that each retained regex check receives equal weight, then items receive equal weight, as registered at [REGISTRATION-4B.md:134](/home/bmarti44/stencil-llm/results/memorycode-long/REGISTRATION-4B.md:134).

   Also replace “complete live set on 10 items … packed on six” at [RESULTS-4B.md:66](/home/bmarti44/stencil-llm/results/memorycode-long/RESULTS-4B.md:66) with **complete on eight; clipped on eight**. Clipped items are `302-49`, `312-49`, `313-49`, `314-49`, `326-49`, `351-99`, `352-99`, and `359-99`. The focus token and kept/selected counts reproduce.

3. **[high — implementation-review finding 6 remains partially unresolved] SETUP budget summarization excludes oracle spending.**  
   Recomputed generation seconds are:

   | Arm/accounting scope | Seconds |
   |---|---:|
   | base | 625.807053 |
   | focus | 561.260405 |
   | oracle | 601.108655 |
   | base + focus | 1,187.067458 |
   | All 48 generations | **1,788.176113** |

   Thus [RESULTS-4B.md:4](/home/bmarti44/stencil-llm/results/memorycode-long/RESULTS-4B.md:4) correctly labels 1,187 seconds as primary-arm spending, but compares that subtotal against the **three-arm** SETUP allowance. Report total spending against that allowance: **1,788.176113 / 3,430.194639 seconds**.

   The implementation defect is at [memorycode_screen.py:1005](/home/bmarti44/stencil-llm/scripts/memorycode_screen.py:1005): summarization always counts base/focus, whereas the runner counts its requested arms. The runner checks exhaustion before another unfinished item, so a final oracle generation can cross the ceiling without producing a marker. Through the actual summary consumer, using virtual records only, **3,440 total seconds** with **2,240 base/focus seconds** still returned `complete=true`, `exhausted=false`, and qualification `FAILED`, where the registered budget rule requires `INCOMPLETE`.

   This leaves the requirement at [REGISTRATION-4B.md:168](/home/bmarti44/stencil-llm/results/memorycode-long/REGISTRATION-4B.md:168) incompletely implemented. **The actual run stayed below the ceiling; no generation rerun is warranted.**

4. **[medium] “McNemar undefined” contradicts the registered convention, and the D3 interpretation needs to be explicit.**  
   At [RESULTS-4B.md:41](/home/bmarti44/stencil-llm/results/memorycode-long/RESULTS-4B.md:41), replace “McNemar undefined” with **“no discordances; two-sided p = 1 by the registered convention.”** The strict paired difference is **0 points**, with the registered conservative interval **[−23.957414, +23.957414]** for every contrast. Both follow directly from [memorycode_screen.py:641](/home/bmarti44/stencil-llm/scripts/memorycode_screen.py:641).

   Under [plan D3:629](/home/bmarti44/stencil-llm/plan/BACK-ON-TRACK-PLAN.md:629), distinguish **failed qualification criterion** from demonstrated population harm, insufficient evidence, and equivalence. The positive fractional bootstrap interval and sign p = .375 address different questions. Neither establishes artifact efficacy from SETUP.

   Focus and base each have **7/16 items with any output failure**, with one discordance each way. A descriptive application of the registered paired method gives net failure difference **0 points [−33.711701, +33.711701], p = 1**. That establishes neither increased net failure nor equivalence, and it does not replace condition (b).

5. **[low — verified] The numerical gate and recorded stop are correct; the prose should make the governing stop unconditional.**  
   Conditions reproduce as **(a) .262521 ≥ .20: pass; (b) .0625 ≤ .05: fail; (c) 9.53125 > 0: pass**. The sole focus-only failure is `184-14`, whose focus output is unparsable; the base-only failure is `186-14`. Oracle has four oracle-only failures and three base-only failures, giving net **+6.25 points**. See [summary.json:201](/home/bmarti44/stencil-llm/results/memorycode-long/setup_long-4b-role_evicted/summary.json:201).

   [REGISTRATION-4B.md:32](/home/bmarti44/stencil-llm/results/memorycode-long/REGISTRATION-4B.md:32) expressly requires stopping on any failed qualification condition. No SCREEN generation records exist in the inspected LONG result tree.

   The report explicitly rejects rescue, and reporting fewer invalid outputs or zero net failure is legitimate. However, “no further revision … without Brian” at [RESULTS-4B.md:19](/home/bmarti44/stencil-llm/results/memorycode-long/RESULTS-4B.md:19) should say that continuation requires **an explicit override of D2**, rather than suggesting an ordinary remaining registration option.

6. **[medium] Most implementation-review edits landed; “all applied” is too strong.**  
   Comparing against [the implementation review:124](/home/bmarti44/stencil-llm/results/reviews/2026-09-12-exp4b-impl-review-astra.md:124):

   | Prior finding | Audit disposition |
   |---|---|
   | 1: weighting and malformed inputs | Landed. |
   | 2: empty/unequal bootstrap and zero-oracle SCREEN | Landed; complete, incomplete, and empty consumer cases exercised in memory. |
   | 3: complete mechanical qualification | Object landed; incomplete oracle coverage returns INCOMPLETE. **Launch enforcement remains unverified.** |
   | 4: configuration validity, scored N, resume matching | Specified checks landed; actual records pass. |
   | 5: timeout zero credit | Runner and recomputation overrides landed. |
   | 6: cumulative budget | Partially landed; SETUP omission described above remains. |
   | 7: statistical interpretation | Registration corrected; RESULTS still needs finding 4’s corrections. |
   | 8: development disclosures | First-query, threshold-selection, regeneration, and label-use disclosures landed. |
   | 9: memory accounting | 32-GB reservation and GiB clarification registered; actual reservation request is not evidenced by terminal records. |

   Amendment 1 promises a launch script consuming `qualification.status` at [REGISTRATION-4B.md:153](/home/bmarti44/stencil-llm/results/memorycode-long/REGISTRATION-4B.md:153). No corresponding committed launch driver was found; [memorycode_screen.py:1246](/home/bmarti44/stencil-llm/scripts/memorycode_screen.py:1246) dispatches `run` without that check. This is an enforcement-evidence gap, **not evidence that SCREEN ran**.

7. **[low — verified, with provenance limits] The saved records satisfy the amended configuration and scoring requirements.**  
   All frozen SETUP IDs have one terminal scored generation per arm. Every manifest names **4b / role_evicted / window 3584 / budget 256 / greedy / cap 512 / deadline 300**. Independently hashing `models/qwen3-4b.pt` gives:

   `8a65acadef4209b00cbc90869e595976269954453b8f9ae5adcf8b6d5dfd0dfc`

   This matches every record, including [item-184-14.json:50](/home/bmarti44/stencil-llm/results/memorycode-long/setup_long-4b-role_evicted/item-184-14.json:50). Item and tokenizer hashes also match. All **48 stored prompt counts equal 3584**, generated IDs decode to the saved text, and reminder token counts reproduce.

   All manifests identify commit `b462785a`, which contains amendment 1 and the reviewed edits. The records first appear together in `0fb6e11d`; no committed replacement history, 1.7B contamination, or output-dependent denominator was found. Saved records cannot prove the absence of discarded uncommitted runs or independently establish launch times. The separately registered `manifest-4b.json` is absent; package parity is also absent and must not be implied complete.

8. **[medium] The descriptive framing is mostly faithful, but the cross-model sentence overstates the observation.**  
   The page-wide DESCRIPTIVE label and explicit “both SCREENs never run / no artifact claim” statements are correct. The net-versus-focus-only discussion does not argue the gate away.

   Replace “The Qwen3-4B trunk applies stated conventions where 1.7B did not” at [RESULTS-4B.md:72](/home/bmarti44/stencil-llm/results/memorycode-long/RESULTS-4B.md:72) with the measured comparison: **“Descriptively, oracle mean fraction_required was .262521 at 4B versus .062937 at 1.7B on these SETUP items.”** The recomputed 1.7B value is nonzero; the present categorical wording is too broad.

9. **[medium] A third registration would be a disclosed departure from this program’s stop rule.**  
   Under [D1–D2:620](/home/bmarti44/stencil-llm/plan/BACK-ON-TRACK-PLAN.md:620), [section J:220](/home/bmarti44/stencil-llm/plan/BACK-ON-TRACK-PLAN.md:220), and the last [ledger entry:3748](/home/bmarti44/stencil-llm/plan/LEDGER.md:3748), the legitimate paths are:

   - **Accept the stop and publish the negative.** Correct the report, preserve the records, and disclose FAILED qualification, both unrun SCREENs, and no established artifact claim.
   - **Publish the package descriptively**, subject to the registered publication/parity requirements and authorization for any deferred execution. Disclose the failed gate, absent confirmatory evidence, and actual parity status. A software release does not establish efficacy.
   - **Continue only after Brian explicitly overrides D2 and a new registration is frozen.** It must acknowledge that both policy revisions were spent, Exp 4B stopped on the observed focus-only failure, and any altered gate or other scientific choice is informed by these outcomes. Preserve all prior negatives; identify every reused dataset and development look, the changed decisions, revised budget and stopping rule, and the status of any prospective evidence. Merely renaming the experiment does not reset the program budget.

   A demonstrated instrument bug can receive a disclosed correction under D2. The accounting bug here supports CPU summary repair; it supplies no reason to regenerate valid outputs or reopen SCREEN. D1 does not authorize repeated audits until acceptance.

**Minimum corrections to RESULTS-4B.md**

- Correct the check-denominator column and state equal weighting per retained regex check.
- Replace oracle packing **10/6** with **8/8**.
- Report **1,788.176113 seconds total**, retaining **1,187.067458** only as the base/focus subtotal; disclose the summary’s oracle-time omission.
- Replace “McNemar undefined” with **p = 1**, and report the strict interval.
- Explicitly distinguish failed qualification from demonstrated harm or equivalence; retain the frozen focus-only gate.
- Replace the categorical cross-model statement with the descriptive means.
- State plainly: **“The program stops under D2. Any continuation requires an explicit override and a new, outcome-informed registration.”**
- Disclose the missing aggregate manifest and uncompleted package parity; do not imply the launch guard or every implementation-review requirement was verified.
