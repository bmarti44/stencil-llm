Reviewer: Astra | Model: GPT-6 Astra | Date: 2026-09-12

**DECISION: Authorize one final confirmation of the unchanged Qwen3-4B package, expanding the frozen 128-item SCREEN with reserve dialogues up to 196 pairs under a timing-only sample-size rule, retaining affirmative +5-point output-failure noninferiority, and publishing the HF model only if every registered gate passes.**

## 1. Decision and authority

This decision exercises Brian’s delegated authority to override D2 **once**. It also overrides the restriction against opening the existing reserve and replaces G’s research-runtime generation-parity requirement with direct evaluation and reproducibility of the shipping package. Exp 4B remains **FAILED / NOT PROVEN** permanently.

The additional decision beyond the reference options is to spend the available budget on **more independent dialogues**, preserving the intervention and the failure margin. No additional mechanism, trunk, benchmark, training, or efficacy pilot is authorized.

The endpoint is a narrowly supported artifact claim: **higher average required-check compliance on coding-session histories under imposed context eviction**. This experiment cannot establish functional correctness, accurate instruction lifecycle management, or free-running agentic performance. It is a step toward the stated goal; the broader agentic goal must not be marked complete from this result.

Every terminal failure ends this line. There is no subsequent sample extension, prompt repair, model substitution, or alternative significance test.

## 2. Evidence driving the decision

**Local findings, independently recomputed.**

From the saved Exp 4B check vectors:

| Quantity | Recomputed result |
|---|---:|
| Mean required-check compliance: off / on / oracle | 0.065662 / 0.108854 / 0.262521 |
| On minus off | **+4.3192 points** |
| Paired t interval; two-sided p | **[−1.1505, +9.7889]; p = 0.113045** |
| Nonzero differences | \(1/3,\ 1/5,\ 1/6,\ -1/14,\ 1/16\) |
| Wins / losses / ties | 4 / 1 / 11 |
| Any output failure: off / on | 7/16 / 7/16 |
| On-only / off-only failures | 1 / 1 |
| Total generation time, all three arms | **1,788.1761 seconds** |

The positive descriptive movement is worth testing, but SETUP does not prove efficacy or noninferiority. Its failed qualification remains a failed criterion. [Saved records and report](/home/bmarti44/stencil-llm/results/memorycode-long/RESULTS-4B.md)

I also reconstructed the cohort and package prompts on CPU:

- **212 LONG items in 212 distinct dialogues**, leaving **196** after excluding SETUP.
- The original 144 item definitions match reconstruction exactly; none of the 212 has an empty required-family set.
- All **196 prospective on/off pairs** have equal prompt-token counts, nonempty reminders, and reminder lengths within 256 tokens.
- All **32 SETUP package prompts** match reconstructed research prompts byte-for-byte and token-for-token.

The existing parity script’s `prompt_match` field actually compares **lengths**; the independent reconstruction above supplies the stronger equality evidence. Its raw generation comparison reports **0/32**, with only **7/32 text matches after `.strip()`**. Different EOS-recording conventions can affect raw token comparisons, so “numerical kernels caused every mismatch” is not established. The **25 differing texts** nevertheless make direct package evaluation necessary. [Parity implementation](/home/bmarti44/stencil-llm/deploy/stencil_focus/scripts/parity_generate.py:83)

**Why expand the sample rather than weaken the guard?**

Using the observed paired spreads \(s_D=0.102648\) and \(s_H=0.365148\):

| Planning quantity | N = 128 | N = 196 |
|---|---:|---:|
| Approximate 80%-power detectable compliance gain | 2.542 points | 2.054 points |
| Failure t-interval half-width | 6.387 points | 5.144 points |
| Approximate probability of certifying +5-point noninferiority under zero true net harm | **33.4%** | **47.8%** |
| Generation allowance using old \(1.5t_{\max}\) | 5.082 hours | **7.781 hours** |

These are conditional planning calculations, **not probabilities of PROVEN**. Package behavior may differ substantially. About 420 pairs would give approximately 80% noninferiority power under this assumption, requiring approximately **16.7 generation-hours** at the old allowance. That is unavailable. Increasing the margin to manufacture adequate power would change the acceptable harm, not improve the evidence.

Paired dialogue-level analysis is appropriate; regex checks must not be counted as independent observations. [Adding Error Bars to Evals](https://arxiv.org/html/2411.00640)

**Research findings that matter to this decision.**

| Evidence | Verified numbers and setting | Transfer to Stencil |
|---|---|---|
| **MemoryCode, 2025** | 360 histories; evaluation temperature 0. Llama-3.1-8B: instruction **71.7%**, long history **12.5%**. GPT-4o: **94.5% → 30.5%**. Histories fit the evaluated models’ contexts. | Matches coding conventions and long histories, but **not imposed eviction or ≤4B**. It establishes difficulty, not failure of our reminder. [Paper](https://arxiv.org/html/2502.13791), [official repository](https://github.com/Cohere-Labs-Community/MemoryCode) |
| **SpotLight, 2025 / EACL 2026** | Greedy decoding; IFEval **541 prompts**. Qwen2.5-3B prompt/instruction accuracy **42/53 → 53/62%**. MT-IFEval has **300 five-turn conversations**; repetition reduces reported across-turn degradation from roughly **20% to 5%**. | Real small-model steering evidence. However, instruction spans are explicitly separated; this does not solve selection from evicted conversational filler. No matching dense coding experiment. The repetition result refutes the memos’ blanket “repetition cannot help” claim. [Paper](https://arxiv.org/html/2505.12025) |
| **DIRECTER, 2026** | Greedy; IFEval **541 prompts**. Reported aggregate accuracy: Llama-3.2-1B **61.3 → 61.6**, Qwen2.5-3B **63.9 → 67.1**. Prompts are rewritten to separate instructions. | Gains are possible but variable. The metric averages prompt/instruction and strict/loose scores; it is not directly comparable to SpotLight’s table or our outcome. [Paper](https://arxiv.org/html/2603.06745) |
| **Prompt repetition** | Original paper: **47 wins / 0 losses / 23 neutral** over 70 model–benchmark comparisons, using **p < .1**, seven API models. A public small-model replication reports Qwen2.5-1.5B, **N=50 per benchmark**: ARC **22 → 44%**, OpenBookQA **32 → 36%**; the latter is nonsignificant. | No reproducible matching coding-retention result. The small-model repository reports the *best* repetition variant and says its other eight listed models remain unrun. This is insufficient support for changing our reminder now. [Paper](https://arxiv.org/html/2512.14982), [replication](https://github.com/mohamedAtoui/prompt-repetition-experiment) |
| **Constraint Pinning, 2026** | Seven models, **27 episodes per model/condition**, 1,323 main-grid episodes. Compaction violations approximately **30% pooled → 0%** with about **47 pinned tokens**. Includes Qwen3.6-27B; temperature generally **0.7**. | Closest deletion mechanism, but sparse governance constraints, larger models and sampling. Pinning known policy is materially easier than identifying relevant sentences in our history. [Paper](https://arxiv.org/html/2606.22528v2) |
| **CodeMEM, 2026** | **40 dialogues × 9 instructions**, DeepSeek-V3.2, greedy. Instruction accuracy **41.1 → 46.1%** versus full-context+BM25; cumulative conversation accuracy **38.4 → 42.8%**. | Positive coding-memory evidence, but a large-model AST/memory system, not a demonstrated ≤4B replacement. [Paper](https://arxiv.org/html/2601.02868v1) |
| **MemFlow, 2026** | Frozen Qwen3-1.7B; **4,236 questions** across three benchmarks; aggregate **29.0 → 52.4%** versus direct full-context QA. Average complete pipeline input is **10,167 tokens**, versus **2,223** at the answer stage. LongMemEval uses its oracle split. | Evidence for a substantial memory pipeline on recall/comprehension, not a cheap reminder on coding-rule application. The answer-stage token count understates total cost. [Paper](https://arxiv.org/html/2605.03312v1) |
| **Paritok-4B, August 2026** | A released 4B compressor; **300 SWE-bench Lite instances**, but the solver is **Claude Sonnet 4.5**, single-shot with oracle file context. Line-numbered compression retains **89.3%** of baseline solve quality; discordances **17 compressed-only / 30 uncompressed-only**, **p=.079**. | A useful new candidate outside the memos, but **4B is the compressor, not the coding solver**. Nonsignificant loss does not establish noninferiority. This cannot justify replacing our package. [Paper](https://arxiv.org/html/2608.24188v1) |
| **Newer trunks** | Qwen3-4B-Instruct-2507 reports IFEval **81.2 → 83.4**, MultiIF **61.3 → 69.0**, but Aider-Polyglot **13.8 → 12.9**. Qwen3.5-4B reports IFEval **89.8**, IFBench **59.2**, using a different architecture and substantially different recommended generation budgets. | Better general scores do not establish a larger reminder-on/off effect under our 512-token greedy protocol. Neither card supplies that paired experiment. [2507 card](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507), [3.5 card](https://huggingface.co/Qwen/Qwen3.5-4B) |

Two further corrections matter. IFEvalCode reports **1.6K problems across eight languages**, not seven; its English average instruction scores are **13.3% at Qwen3-1.7B and 18.0% at 4B**, while the **Python** scores are **26.7% and 28.6%**. Those averages are not pure naming-convention rates. [IFEvalCode](https://arxiv.org/html/2507.22462)

IF-RLVR improves Tülu-3-8B from **28.9% to 45.9%** on the **300-prompt IFBench**, but that supports a separately trained program, not a locally qualified three-day adaptation. [Generalizing Verifiable Instruction Following](https://arxiv.org/html/2507.02833v3)

**Alternatives rejected, one line each.**

- **Unchanged 128-item draft:** superseded by the timing-only expansion, which buys precision without relaxing acceptable harm.
- **Wider margin or “no significant harm” guard:** rejected because either changes the tolerated harm or fails to establish noninferiority.
- **Reminder repetition, formatting, or language-contract change:** insufficient matching evidence; no benchmark-response-driven intervention editing.
- **Attention steering or relevance ranking:** plausible future mechanisms, but new package behavior and qualification costs without a matching result.
- **Fresh sparse workload:** potentially informative, but introduces authoring, validation and population choices when an external cohort is already available.
- **Verifier repair or constrained decoding:** the benchmark checker cannot enter the intervention; an independently deployable verifier would be a new system.
- **Oracle pass@k:** cannot establish deployable selection or greedy artifact efficacy; zero successes would not establish impossibility.
- **New trunk, MemFlow, CodeMEM or Paritok:** promising adjacent evidence, insufficient justification for another local system-selection cycle.
- **RLVR:** no qualified fit–evaluate–publish budget within this allocation.
- **Immediate descriptive HF release or repo-only stop:** honest alternatives, but they leave an affordable, generation-unseen artifact comparison unanswered.

## 3. Exact registration to freeze

The following text replaces the scientific specification in `REGISTRATION-4C-DRAFT.md`. Hashes, installed-version identifiers and the timing-derived \(N\) are filled mechanically, without discretion.

> **Exp 4C — final package confirmation; binding Astra authorization, 2026-09-12.**
>
> Brian delegated the continuation decision to Astra. Astra authorizes this single exception to D2, prospective use of the existing reserve under the rule below, and replacement of research-runtime generation parity with direct shipping-package evaluation. Exp 4B remains FAILED / NOT PROVEN. No terminal outcome permits another scientific revision.
>
> **Lineage and disclosure.** Fit-on: nothing. Intervention selection and analytical development were informed by Exp 4/4B SETUP results, short-cohort first-query analyses, SCREEN metadata and label-derived CPU diagnostics, the overflowing-register result, trunk/estimand selection, oracle-threshold selection, the options/literature memos, and implementation/result audits. Earlier repairs included cumulative oracle replay, Unicode speaker parsing, oracle regenerations, the recorded 314-49 focus regeneration, and cumulative-budget accounting. Package parity results were also known.
>
> This consultation reconstructed all 212 eligible LONG item definitions and checked package prompt lengths on the 196 non-SETUP items; their model outcomes were not generated. Evaluation is therefore generation-unseen, not item-unseen. Nothing is fit, selected or tuned using evaluation responses. Gold annotations supply cohort/scoring metadata and disclosed diagnostics only; they never enter the intervention. All prior results and this outcome-informed continuation remain disclosed.
>
> **Candidate order and sample size.** Reconstruct `long_items` from vendored MemoryCode revision `1ab87e119b2f9a498de8075219e1c07f6041b394` using the existing tokenizer and unchanged enumeration rules. Apply the existing seed-1 dialogue shuffle. Exclude its first 16 SETUP dialogues. The remaining ordered list contains 196 dialogues; its first 128 must exactly reproduce the original SCREEN definitions.
>
> The original `items.json` SHA-256 is:
>
> `affe6877f059e5f58466023fe70c45cefeadca4b98d1a036832901d14073ce1a`
>
> SHA-256 of the complete 196 evaluation IDs, joined with `\n` and a final newline, is:
>
> `3125634e658bf35fc20e8555199abb5cc8f30ada4c14f328caba08fa7e43ca28`
>
> Let \(t_{\max}\) be the maximum elapsed generation-call time from the eight prescribed pilot calls below. Set
>
> \[
> N=\min\!\left(196,\left\lfloor\frac{28\,800}{3t_{\max}}\right\rfloor\right).
> \]
>
> If \(N<128\), do not evaluate: terminal INELIGIBLE—BUDGET. Otherwise select exactly the first \(N\) dialogues in that fixed order and freeze their complete definitions before evaluation. No outcome, compliance score, failure rate or subgroup statistic participates in this rule. No post-launch extension or reduction is permitted.
>
> **Arms and artifact.** Use the currently assembled Qwen3-4B package, unchanged learned weights at upstream revision `1cfa9a7208912126459214e8b04321603b3df60c`, with a cryptographic manifest of every weight shard, tokenizer/configuration file and remote-code module. Freeze the installed runtime versions and resolved attention backend; use the same environment for qualification, evaluation and release verification.
>
> Generate through the package’s public session interface only. Off: `stencil_focus=false`. On: `stencil_focus=true`, unchanged `role_evicted` policy, renderer, sentence selection and packing. \(W=3584\), \(E=256\), batch size one, bf16, greedy, one beam, 512 newly generated tokens, 300-second deadline. Both arms use identical effective generation settings and fresh session/cache state. The package’s effective EOS setting is frozen explicitly.
>
> Each item uses its existing first query and supplied historical conversation. No oracle, repair, resampling, generated historical trajectory, attention modification or checker feedback is introduced. Assert equal actual prompt lengths before generation and prompt-plus-output allocation at most 4096 tokens. Execute candidate order, alternating off-first and on-first by item index.
>
> **Primary.** Freeze the `history_regex` entries whose families are required by each query. Give each retained check equal weight, including repeated checks within a family; then give each dialogue equal weight. Missing required parents receive zero; missing required structure or a terminal timeout sets the item score to zero. Preserve the inherited scoring of capped outputs and count caps in the failure guard.
>
> Let \(D_i=S_{i,on}-S_{i,off}\). Report \(\bar D\), sample SD, the two-sided paired t-test of \(E[D]=0\), and its matching 95% interval:
>
> \[
> \bar D\pm t_{.975,N-1}s_D/\sqrt N.
> \]
>
> Positive efficacy requires the lower endpoint strictly above zero. The inference assumes independent dialogue units and has approximate coverage for this bounded, discrete distribution.
>
> If \(s_D=0\), do not emit a zero-width inferential interval. Use the bounded-variable Hoeffding interval
>
> \[
> [\,\bar D-\sqrt{2\log(40)/N},\ \bar D+\sqrt{2\log(40)/N}\,]\cap[-1,1]
> \]
>
> and conservative two-sided p bound \(\min(1,2e^{-N\bar D^2/2})\), explicitly labelled as the degenerate-case fallback.
>
> Always report the original paired percentile bootstrap—10,000 draws, seed 0, lexicographically sorted IDs, order statistics 251 and 9750—and exact sign test as companions. Neither can replace the primary decision.
>
> **Output-failure guard.** Retain the existing definitions of invalid, capped, degenerate and timed out. Define \(F_{ia}\) as their union, \(H_i=F_{i,on}-F_{i,off}\), and \(\eta=E[H]\). Report both discordance directions, all category counts, \(\bar H\), a paired t-test against zero and matching 95% interval \([L_H,U_H]\).
>
> If \(s_H=0\), use the existing conservative paired interval: separate two-sided 97.5% Clopper–Pearson intervals for on-only and off-only discordance probabilities, then subtract their opposing endpoints. Report exact McNemar p, with p=1 for no discordances.
>
> **The combined statistical gate requires \(U_H\le0.05\).** Neither an observed net difference below five points nor nonsignificant harm suffices. An interval wholly above zero establishes increased failures under the registered procedure even when the increase remains within the margin.
>
> Report failure-rate equivalence only when the entire interval lies inside \([-0.05,+0.05]\). Crossing zero alone establishes neither equivalence nor noninferiority. No primary-compliance equivalence margin is registered.
>
> **Technical qualification and timing.** Before evaluation, use SETUP IDs `359-99`, `352-99`, `351-99`, `302-49`, in that order, once per flag state: eight timing calls. Record outputs for reproducibility, but do not score them for an efficacy or failure-rate launch gate.
>
> Complete package-off outputs for the other 12 SETUP items; generate all 16 off prompts through plain upstream `AutoModelForCausalLM`; reload the package and replay the original eight calls. Total qualification: **44 generations**. Require 16/16 off/plain raw-token matches and 8/8 package replay matches, using identical EOS conventions. Compare prompt bytes and token IDs separately from lengths. Load package and plain models sequentially.
>
> **Budget.** Maximum additional GPU allocation: **10 hours**, divided into qualification ≤3600 seconds; evaluation generation calls ≤\(3t_{\max}N\le28\,800\) seconds; evaluation loading and other resident-process overhead ≤2700 seconds; final clean-environment verification ≤900 seconds. All attempts, interrupted work and verification count. Unused allowances do not authorize additional experiments.
>
> Reservations remain ≤55 minutes, worker budgets ≤50 minutes, declared memory 32 GB, one Stencil GPU process at a time. Use an owned-process watchdog and stop starting work with sufficient time for outstanding deadlines and the five-minute reservation buffer. Enforce both per-slice and cumulative ceilings.
>
> Complete within three working days of implementation start. Failure to qualify, complete, audit or verify within the applicable limits ends execution; budgets and \(N\) are never enlarged.
>
> **Records and completeness.** Save each terminal arm atomically. Preserve raw generated IDs including EOS, scored IDs with the terminal EOS removed, decoded text, actual stop reason, timeout/cap indicators, scores, failure categories, prompt bytes or lossless reconstruction references, prompt IDs/hash/count, reminder/source offsets, timing, configuration identities, package/environment hashes and item/checker hashes.
>
> Resume only missing work under the same frozen manifest. Never overwrite or regenerate a valid terminal output. Record interrupted-attempt spending. Missing, duplicate, mismatched, malformed or unscored required records prevent confirmation; no item is dropped or replaced.
>
> **Readings and reporting.** Apply Section 5’s table mechanically. No interim efficacy summaries or decisions. Always report strict compliance and its paired interval/McNemar test, absolute fractional scores, primary and companion statistics, output-failure categories and discordances, prompt accounting, missingness, cost and all prior disclosures. The original 128-item subset and added reserve subset are descriptive breakdowns only and cannot establish separate claims.

## 4. Operational sequence

1. **Record the authorization and freeze the specification.** Quote the decision in the ledger. Preserve the original items file and registrations. Create a separate 4C item manifest from the specified order; do not overwrite historical metadata.

2. **Complete the necessary CPU implementation.** The current code is not launch-ready for this registration:
   - Package summaries still use Exp 4B’s decision rule. Implement an explicit 4C analysis mode; a package directory name must not imply confirmatory eligibility. [Current decision function](/home/bmarti44/stencil-llm/scripts/memorycode_screen.py:740)
   - Validate the complete artifact/environment fingerprint on both resume and summary. Current resume matching omits `package_sha256`, and the package manifest calls the weight-index hash `weights_sha256`. Record actual shard identities. [Manifest construction](/home/bmarti44/stencil-llm/scripts/memorycode_package_run.py:59)
   - Add the separate item manifest, timing-only \(N\) calculation, complete accounting, raw-EOS records and release-manifest checks.
   - Keep the retired register’s diagnostic files outside the new primary’s completeness dependencies; reserve items must not require nonexistent `auto/item-*.json` files.
   - Exercise the actual runner/summary/launch consumers with synthetic records covering each terminal reading, changed package hashes, missing pairs, zero variance, timeout zero-credit and ceiling exhaustion.

3. **Conduct one focused Astra implementation review.** **Waive duplicate review of unchanged package prompting and previously reviewed checker code. Do not waive review of the new runner, analysis, sample-size and publication-gate paths.** This strategy consult is not their implementation acceptance. Close findings in the same review record; no additional general research or review stage.

4. **Run the prescribed qualification.** Write ahead to the ledger; use absolute launch paths, reservation coordination and owned PID registration. Monitor timing and operational completion only. Freeze the resulting \(N\), selected IDs, budget and fingerprints before any evaluation generation. At the old measured \(t_{\max}=47.641592214\), the formula selects **196**; at 50 seconds it selects **192**; at 60 seconds, **160**; above 75 seconds it cannot authorize 128.

5. **Launch the single evaluation and finish all registered pairs.** Save arms as completed; resume across slices without inspecting efficacy. Neither the first 128 results nor reserve results trigger a decision.

6. **Summarize once and perform one result audit.** Recompute scores, intervals, reading, identities and spending from terminal records. Preserve every prior negative and disclose any instrument repair. Analysis repairs may reprocess the same outputs; they cannot change the registered scientific question.

7. **Apply the publication gate.** Only statistical success plus accepted audit and clean-environment reproduction authorizes the HF model push. Publish the exact evaluated model/package bytes, with documentation updates excluded from the inference fingerprint. HF authentication, if missing, is an operational dependency; do not request another scientific decision. This authorization does not authorize a GitHub remote push.

Day 1 covers implementation, review, qualification and freeze; day 2 covers evaluation; day 3 covers audit and publication.

## 5. Publication on every possible reading

Evaluate technical status first, then primary efficacy, then the failure guard. Report the failure evidence independently even when primary efficacy fails.

| Condition | Terminal reading | Publication |
|---|---|---|
| Qualification fails, reconstruction differs, or timing gives \(N<128\) | **INELIGIBLE; efficacy NOT PROVEN** | Repo qualification report, timings and disclosures; no HF model release. |
| Evaluation incomplete, required records invalid, configuration mismatch, or budget exceeded | **INCOMPLETE** | Repo report with all available records and explicit missingness; no confirmatory claim or HF model release. |
| Primary upper endpoint \(<0\) | **HARM** | Repo demonstrated compliance-harm result, including failure evidence; no HF model release. |
| Primary interval includes zero | **NOT PROVEN—FINAL** | Repo result stating insufficient evidence of positive efficacy; no HF model release. Any demonstrated output harm is reported alongside. |
| Primary lower endpoint \(>0\), failure upper endpoint \(>0.05\), failure lower endpoint \(\le0.05\) | **POSITIVE EFFICACY / NONINFERIORITY UNRESOLVED; NOT PROVEN—FINAL** | Repo efficacy and failure tables; no HF model release. |
| Primary lower endpoint \(>0\), failure lower endpoint \(>0.05\) | **POSITIVE EFFICACY / DEMONSTRATED EXCESS OUTPUT HARM; NOT PROVEN—FINAL** | Repo result stating the demonstrated margin violation; no HF model release. |
| Primary lower endpoint \(>0\), failure upper endpoint \(\le0.05\), but release verification or audit remains unacceptable | **STATISTICAL GATES PASSED / ARTIFACT RELEASE UNVERIFIED** | Repo statistical result and concrete release defect; no HF model release. |
| Primary lower endpoint \(>0\), failure upper endpoint \(\le0.05\), complete valid records, accepted audit and release verification | **PROVEN—SCOPED** | Exact evaluated artifact on `bmarti44/stencil-focus-qwen3-4b`, plus full repo results and disclosures. |

For the final row, use this card wording, substituting recorded values mechanically:

> **PROVEN for higher average required-check compliance on a MemoryCode-derived coding-session test under imposed context eviction.** On N=[N] paired dialogues, enabling `stencil_focus` changed mean compliance from [off] to [on]: [difference] percentage points, 95% interval [lower, upper], two-sided p=[p]. The net output-failure difference was [difference] points, 95% interval [lower, upper]; its upper bound met the preregistered +5-point noninferiority margin. Strict compliance was [off count]/[N] versus [on count]/[N].
>
> These results were generated through this package against the identical artifact with its modification disabled. The learned Qwen3-4B weights are unchanged. The modification restates selected evicted user sentences within a 256-token reminder and a 3,584-token total prompt budget.
>
> This establishes average partial convention compliance in the stated test. It does not establish fully compliant or functionally correct code, accurate relevance selection or retirement of superseded instructions, or free-running agentic performance. Absolute scores and output failures are reported above.
>
> Exp 4B previously failed qualification. This final registration followed outcome-informed development and an explicit owner-delegated stop-rule override. Earlier research-runtime results were not attributed to this package because generation parity failed. The complete development history, prior negatives, registration, outputs and audit accompany this release.

If failures significantly increase while remaining within the five-point margin, append: **“Enabling the modification demonstrably increased output failures, although the increase satisfied the registered noninferiority margin.”**

I wrote no files, ran no models, used no GPU, and read nothing under `data/bench/`.
