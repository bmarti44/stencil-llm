VERDICT: REJECT
READING: INCOMPLETE

1. **High — required reminder provenance is incorrect in all 139 pairs, changing the prescribed reading.**

   Independently reconstructed prompts match **278/278** stored prompts. However, **139/139 focus records** contain `kept_spans` that do not reproduce their recorded reminder. There are therefore **0/139 fully conforming pairs**, versus the summary’s **139 valid pairs** and empty invalid-record list.

   The package selects reminder sentences using the **base-window eviction boundary** at [focus_session.py:164](/home/bmarti44/stencil-llm/deploy/stencil_focus/build/hub-4b/focus_session.py:164). The recorder instead derives provenance from the **final focus-window boundary**, then selects the latest spans again at [memorycode_package_run.py:345](/home/bmarti44/stencil-llm/scripts/memorycode_package_run.py:345).

   For example, [item-267-29.json:1249](/home/bmarti44/stencil-llm/results/memorycode-long/screen_long_4c-4b-package-role_evicted/item-267-29.json:1249) records 543 selected sentences, but its provenance reports 552. The actual selection boundary is **55,669** characters; the recorded boundary is **56,911**. The reminder’s first sentence occupies **[54,031, 54,107)** in message **581**; the recorded first span is a different sentence at **[54,802, 54,879)** in message **591**.

   The validator merely requires `reminder_sources` to be a dictionary at [memorycode_4c_summarize.py:263](/home/bmarti44/stencil-llm/scripts/memorycode_4c_summarize.py:263). Thus it admits these contradictions. Provenance is expressly required by [REGISTRATION-4C.md:138](/home/bmarti44/stencil-llm/results/memorycode-long/REGISTRATION-4C.md:138); invalid required records select **INCOMPLETE** at [line 154](/home/bmarti44/stencil-llm/results/memorycode-long/REGISTRATION-4C.md:154), before efficacy is considered.

2. **High — interim efficacy inspection and outcome-dependent continuation entered the procedure.**

   [LEDGER.md:3852](/home/bmarti44/stencil-llm/plan/LEDGER.md:3852) records an owner-directed change during evaluation, a **75-pair** efficacy inspection, and the decision “Not futile; run continues.” [RESULTS-4C.md:98](/home/bmarti44/stencil-llm/results/memorycode-long/RESULTS-4C.md:98) additionally discloses a **100-pair** inspection.

   These disclosures contradict the frozen prohibition on interim efficacy summaries or decisions at [REGISTRATION-4C.md:162](/home/bmarti44/stencil-llm/results/memorycode-long/REGISTRATION-4C.md:162). The owner authorization is disclosed; it does not establish that the original registered procedure remained unchanged. No `progress-4c.json` exists to supply the requested progress/terminal timestamp comparison.

   The receipts establish completion at the original N, without extension or regeneration. The interim looks do **not** establish that the displayed arithmetic is wrong, but the audit’s requirement that nothing outcome-dependent entered is not satisfied.

3. **Low — primary, companions, and descriptive subsets reproduce numerically.**

   The following calculations use **all 139 observed, score-reproducible pairs**. They do not cure finding 1’s record invalidity. Values below are independently recomputed versus [summary-4c.json:23](/home/bmarti44/stencil-llm/results/memorycode-long/screen_long_4c-4b-package-role_evicted/summary-4c.json:23), rounded identically.

   | Quantity | Recomputed | Summary |
   |---|---:|---:|
   | Observed paired N | 139 | 139 |
   | Mean off | 0.084470691333 | 0.084470691333 |
   | Mean on | 0.104926881175 | 0.104926881175 |
   | Mean D | 0.020456189842 | 0.020456189842 |
   | Sample s_D | 0.125930811275 | 0.125930811275 |
   | SE | 0.010681312003 | 0.010681312003 |
   | Paired t, df=138 | 1.915138312290 | 1.915138312290 |
   | t₀.₉₇₅,₁₃₈ | 1.977303542028 | 1.977303542028 |
   | Primary 95% interval | [−0.000664006215, 0.041576385899] | [−0.000664006215, 0.041576385899] |
   | Two-sided p | 0.057543815387 | 0.057543815387 |
   | Bootstrap mean, percentage points | 2.045618984235 | 2.045618984235 |
   | Bootstrap 95% interval, points | [0.142973961496, 4.304961824152] | [0.142973961496, 4.304961824152] |
   | Wins / losses / ties | 25 / 17 / 97 | 25 / 17 / 97 |
   | Exact sign-test p | 0.279956238529 | 0.279956238529 |
   | SCREEN subset N | 128 | 128 |
   | SCREEN mean off / on | 0.082158733360 / 0.104848052883 | 0.082158733360 / 0.104848052883 |
   | Reserve subset N | 11 | 11 |
   | Reserve mean off / on | 0.111373475010 / 0.105844155844 | 0.111373475010 / 0.105844155844 |

   Both difference distributions have nonzero variance, so neither fallback applies. Bootstrap reconstruction used lexicographically sorted IDs, Python’s seed-0 generator, **10,000** draws, and order statistics **251 and 9,750**, matching the frozen implementation at [memorycode_screen.py:687](/home/bmarti44/stencil-llm/scripts/memorycode_screen.py:687).

   If technical validity were satisfied, the primary interval’s inclusion of zero would select **NOT PROVEN, FINAL**. The positive bootstrap interval cannot replace that primary decision.

4. **Medium — strict and failure statistics reproduce, but “output failures unchanged” is unsupported.**

   Independent comparisons with [summary-4c.json:51](/home/bmarti44/stencil-llm/results/memorycode-long/screen_long_4c-4b-package-role_evicted/summary-4c.json:51):

   | Quantity | Recomputed | Summary |
   |---|---:|---:|
   | Strict off / on | 0 / 1 | 0 / 1 |
   | Strict on-only / off-only discordances | 1 / 0 | 1 / 0 |
   | Strict McNemar p | 1 | 1 |
   | Strict difference, points | 0.719424460432 | 0.719424460432 |
   | Conservative strict 95% interval, points | [−3.094313722028, 4.502737563390] | [−3.094313722028, 4.502737563390] |
   | Failure-union count off / on | 60 / 61 | 60 / 61, derived from rates |
   | Failure rate off / on | 0.431654676259 / 0.438848920863 | 0.431654676259 / 0.438848920863 |
   | On-only / off-only failures | 9 / 8 | 9 / 8 |
   | Total failure discordances | 17 | 17 |
   | Invalid off / on | 48 / 46 | 48 / 46 |
   | Capped off / on | 59 / 60 | 59 / 60 |
   | Degenerate off / on | 1 / 0 | 1 / 0 |
   | Timed out off / on | 0 / 0 | 0 / 0 |
   | Mean H | 0.007194244604 | 0.007194244604 |
   | Sample s_H | 0.350907785023 | 0.350907785023 |
   | SE_H | 0.029763609860 | 0.029763609860 |
   | Paired t, df=138 | 0.241712770671 | 0.241712770671 |
   | [L_H, U_H] | [−0.051657446594, 0.066045935803] | [−0.051657446594, 0.066045935803] |
   | Two-sided paired-t p | 0.809361539233 | 0.809361539233 |
   | Failure McNemar p | 1 | 1 |
   | Noninferiority / equivalence / demonstrated increase | false / false / false | false / false / false |

   The strict interval independently uses opposing endpoints of separate **97.5% Clopper–Pearson intervals**, as registered. Failure categories overlap.

   **U_H > 0.05** leaves noninferiority unresolved; the interval establishes neither equivalence nor increased failures. Consequently, “output failures unchanged” at [RESULTS-4C.md:115](/home/bmarti44/stencil-llm/results/memorycode-long/RESULTS-4C.md:115) overstates the evidence. No primary-compliance equivalence margin was registered.

5. **Low — candidate reconstruction, qualification, and artifact identities pass.**

   CPU reconstruction from the local vendored dataset produced **212 items in 212 dialogues**, the identical seed-1 SETUP exclusion, and **196 candidates**. All candidate fields match; the original **128 SCREEN definitions** and frozen **139-item prefix** match exactly.

   | Identity | Independently recomputed SHA-256; matches recorded value |
   |---|---|
   | Original items.json | `affe6877f059e5f58466023fe70c45cefeadca4b98d1a036832901d14073ce1a` |
   | Candidate IDs | `3125634e658bf35fc20e8555199abb5cc8f30ada4c14f328caba08fa7e43ca28` |
   | Frozen IDs | `eb37a6a1bdccbe3c1e752baf8ddf31a53d0f1268d59a9f633d539107cbe51546` |
   | Frozen items file | `55f558621064b88b08ab18b6305df08f603b4cbcc78284d16d1032813d446ebd` |
   | Qualification report | `ea38a9178dac83223d186a05e177bdfada9d0abb7a433b9c0c6bf5cdc84ba3f2` |
   | Package aggregate | `5b150a48c3e9ce2cf6da992d906ddd43ebffbc3f035ed17524107b8bfec8e5a3` |

   References: [items-4c.json:3](/home/bmarti44/stencil-llm/results/memorycode-long/items-4c.json:3), [summary-4c.json:128](/home/bmarti44/stencil-llm/results/memorycode-long/screen_long_4c-4b-package-role_evicted/summary-4c.json:128), and [qualification-4c.json:323](/home/bmarti44/stencil-llm/results/memorycode-long/qualification-4c.json:323).

   All **13 package-file hashes** match qualification. All **three weight shards** match the local upstream copies and download receipts naming revision `1cfa9a7208912126459214e8b04321603b3df60c`. Both recorded checker hashes match. The vendored tree and generation/scoring code are unchanged from closure commit `1ca02a31`.

   The **44 receipts** reproduce **16/16 plain comparisons** and **8/8 package replays**, matching [qualification-4c.json:781](/home/bmarti44/stencil-llm/results/memorycode-long/qualification-4c.json:781). The maximum of the prescribed eight timing calls is **68.688911280944 seconds**, matching the summary; it belongs to `351-99` focus. Therefore:

   **N = min(196, floor(28,800 / (3 × 68.688911280944))) = 139**, matching the freeze and summary.

   All **278 evaluation-arm fingerprints** match qualification, with the prescribed replacement of the candidate-file digest by the frozen evaluation-file digest. Effective EOS is **[151645]** throughout; environment identity includes bf16, SDPA, torch **2.13.0+cu130**, transformers **5.16.1**, and tokenizers **0.23.1**.

6. **Low — terminal coverage, execution order, and spending reconcile from receipts.**

   The directory contains **139 terminal item records**, **278 linked raw outputs**, and **556 attempt-log rows: 278 starts and 278 ends**. There are **zero** missing outputs, duplicate attempts, extra raw outputs, malformed JSON records, or open attempts. Every attempt follows candidate-index order and the registered off/on alternation. These checks establish terminal coverage, subject to finding 1’s provenance invalidity.

   | Budget quantity | Recomputed | Summary |
   |---|---:|---:|
   | Generation ceiling, 3t_maxN | 28,643.276004154 s | 28,643.276004154 s |
   | Evaluation generation spending | 9,101.323609308 s | 9,101.323609308 s |
   | Evaluation resident overhead | 371.982368192 s | 371.982368192 s |
   | Overhead allowance | 2,700 s | 2,700 s |
   | Qualification resident spending | 2,749.019903945 s | 2,749.019903945 s |
   | Qualification allowance | 3,600 s | 3,600 s |
   | Unbounded / exhausted / budget marker | false / false / absent | false / false / false |

   References: [attempts.jsonl:1](/home/bmarti44/stencil-llm/results/memorycode-long/screen_long_4c-4b-package-role_evicted/attempts.jsonl:1), [summary-4c.json:9](/home/bmarti44/stencil-llm/results/memorycode-long/screen_long_4c-4b-package-role_evicted/summary-4c.json:9), and [qualification-4c.json:784](/home/bmarti44/stencil-llm/results/memorycode-long/qualification-4c.json:784).

   All **six process receipts** end cleanly, with no active call. Evaluation’s four processes contain **49, 55, 96, and 78 calls**; their generation totals reconcile individually. Qualification’s two processes contain **42 and 2 calls**. No interrupted-work bound is needed. Process intervals do not overlap, and each remains within its resident ceiling. Total recorded resident spending is **12,222.325853349 seconds**, approximately **3.395 hours**.

7. **Low — all stored scores, failure flags, EOS transformations, and prompts reproduce.**

   I re-scored **278/278 generations**, exceeding the requested 20-record sample. Every stored score dictionary and failure dictionary matched the frozen checker logic at [memorycode.py:345](/home/bmarti44/stencil-llm/src/stencil/memorycode.py:345), [memorycode.py:591](/home/bmarti44/stencil-llm/src/stencil/memorycode.py:591), and [evaluate_model_output.py:23](/home/bmarti44/stencil-llm/vendor/memorycode/code/evaluate_model_output.py:23).

   The explicit 20-generation sample comprised both arms of `150-4`, `152-9`, `153-9`, `157-9`, `158-9`, `159-9`, `160-9`, `162-9`, `164-9`, and `166-9`. It includes the sole strict success, `157-9` focus, and capped output retaining partial credit, `152-9` focus.

   All **278** raw-to-scored token transformations, decoded texts, prompt hashes, and prompt-ID hashes match. EOS/cap counts are **80/59 off** and **79/60 on**, consistent with the summary’s cap counts. There are **zero timeouts**; timeout zero-credit is implemented at [memorycode_package_run.py:618](/home/bmarti44/stencil-llm/scripts/memorycode_package_run.py:618), but this dataset does not empirically exercise that branch.

   Every arm has **3,584 prompt tokens**, equal within every pair, and **3,584 + 512 = 4,096** allocated tokens. All focus reminders are nonempty and within **256 tokens**. Their actual mean is **246.064748201439 tokens**, versus “about 247” in [RESULTS-4C.md:76](/home/bmarti44/stencil-llm/results/memorycode-long/RESULTS-4C.md:76). The required source spans remain incorrect despite correct prompt reconstruction.

8. **Low — the disclosed summary repair is supported; the report’s chronology needs qualification.**

   Both terminal-summary artifacts are retained. Their modification times are **17:33:21.195057Z** for the defective summary and **17:34:16.575768Z** for the corrected summary, after the last item at **17:33:12.414603Z**. The defective summary contains **n=0** statistics and reports INCOMPLETE because its validator could not locate prompt fields.

   The subsequent change merges linked raw-file prompt fields after checking their identities at [memorycode_4c_summarize.py:191](/home/bmarti44/stencil-llm/scripts/memorycode_4c_summarize.py:191). Generation outputs, scoring, and statistical formulas were unchanged. This repair fits the binding allowance for reprocessing unchanged outputs at [unblock decision:186](/home/bmarti44/stencil-llm/results/reviews/2026-09-12-unblock-decision-open-astra.md:186); it is not independently grounds for rejection. Nevertheless, “computed once at 17:40Z” at [RESULTS-4C.md:4](/home/bmarti44/stencil-llm/results/memorycode-long/RESULTS-4C.md:4) is not the literal artifact history.

   Prior development, negative results, generation-unseen lineage, parity failure, and the owner override are disclosed in [REGISTRATION-4C.md:12](/home/bmarti44/stencil-llm/results/memorycode-long/REGISTRATION-4C.md:12). Missingness and cost are derivable; the assertion that all required records are valid is contradicted by finding 1.

   **No HF release is authorized. The program ends with a repo-only report of INCOMPLETE, retaining the reproduced numerical results and these defects.** I wrote no files, ran no models, used no GPU, and read nothing under `data/bench/`.

---

## Closure record (orchestrator, 2026-09-12, after the audit; findings above unchanged)

1. (resolved, post-audit) Provenance recomputed from unchanged outputs by
   `scripts/memorycode_4c_reprovenance.py` (base-window boundary; byte-identical prompt and
   reminder asserted per item; previous values retained in the records and in
   `reprovenance-4c.json`); runner self-checks that kept spans reproduce the reminder; validator
   requires it (`_provenance_reason`, tested). Summary recomputed: 139/139 valid, NOT PROVEN, FINAL.
2. (disclosed, not repairable) Owner-directed interim looks at 75 and 100 pairs; run neither
   stopped nor extended; recorded in RESULTS-4C.md and the ledger as a procedural deviation.
3-7. (no action) Numbers, identities, receipts and scores reproduced.
4. (resolved) "output failures unchanged" replaced by "unresolved" wording in RESULTS-4C.md.
8. (resolved) RESULTS-4C.md now states the literal summary artifact history.
The audit verdict is not re-litigated: REJECT stands as the recorded audit; no HF release.
