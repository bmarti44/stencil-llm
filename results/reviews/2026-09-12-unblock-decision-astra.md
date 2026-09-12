Reviewer: Astra | Model: GPT-6 Astra | Date: 2026-09-12
**DECISION: Run one final Exp 4C confirmation of the unchanged package on all 128 frozen SCREEN-LONG items, requiring a positive paired-t efficacy interval, a net output-failure upper bound ≤ +10 percentage points, and no statistically demonstrated failure increase; publish on HuggingFace only if all three conditions and release verification pass.**

## 1. Binding decision and rationale

Brian’s delegation authorizes this **single, final D2 exception**. It authorizes the registration below, not another reminder revision. Exp 4B remains **FAILED / NOT PROVEN under its original registration**.

The remaining scientific question is worth answering: does the **actual package**, switched on versus off, improve measured instruction retention? Research-runtime results cannot settle that question because package outputs differ. The planned computation fits the budget, subject to a measured package pilot.

Keep the reminder unchanged. The literature supports repetition and restoration as plausible mechanisms, but does not establish that a particular header, Python output contract, encoder, or deduplication change reliably improves this combination of a ≤4B model, evicted history, dense coding conventions, greedy decoding, and a 4,096-token limit.

Replace the draft’s +5-point failure margin with **+10 points**, and additionally prohibit publication when the failure interval’s lower endpoint exceeds zero.

This is an explicitly outcome-informed, owner-delegated choice of claim tolerance. It is **not a literature-derived universal acceptable failure rate**. It permits a narrower research claim: improved average checked convention adherence, with the registered analysis excluding a net failure increase greater than ten points. It does not certify unchanged reliability, functional correctness, full instruction compliance, or performance in an autonomous coding session.

Do not use “no demonstrated increase” alone: that could pass while leaving a large increase compatible with the data. Do not switch to invalid-only failures: that would discard the already observed truncation problem.

## 2. Evidence driving the decision

**Local recomputation**

I independently rescored all 48 saved Exp 4B generations using the existing checker and failure classifier: **zero score mismatches and zero failure-field mismatches**.

| Quantity | Recomputed result |
|---|---:|
| Mean required-check fraction, base / focus / oracle | 6.5662% / 10.8854% / 26.2521% |
| Focus-minus-base mean | **+4.3192 points** |
| Paired-t 95% interval, N=16 | **[−1.1505, +9.7889] points** |
| Two-sided paired-t p | **0.1130** |
| Item wins / losses / ties | 4 / 1 / 11 |
| Strict compliance | 0/16 in every arm |
| Any output failure, base / focus | 7/16 / 7/16 |
| Focus-only / base-only failures | 1 / 1 |
| Fully packed / clipped oracle reminders | 8 / 8 |

Thus, the positive bootstrap result is suggestive development evidence; it is not confirmation under the proposed primary test. Sources: [saved summary](/home/bmarti44/stencil-llm/results/memorycode-long/setup_long-4b-role_evicted/summary.json), [Exp 4B results](/home/bmarti44/stencil-llm/results/memorycode-long/RESULTS-4B.md).

Two parity disclosures need correction:

- The existing parity script’s `prompt_match` checks **token counts**, not prompt bytes. My fresh CPU reconstruction using the assembled package and tokenizer independently establishes **32/32 byte-identical SETUP prompts**.
- The reported **0/32 raw generated-token matches** compares different terminal-EOS recording conventions. It does not establish 32 runtime-induced decoding divergences. Nevertheless, only **7/32 stripped output texts match**, so substantial output divergence remains. The saved **16/16 package-off/plain-model matches** remain a separate result.

Preserve the original [parity artifact](/home/bmarti44/stencil-llm/results/memorycode-long/parity-4b.json); append these measurement qualifications.

**Web research**

| Primary source | Specific evidence | Applicability to Stencil |
|---|---|---|
| [MemoryCode, ACL 2025](https://aclanthology.org/2025.acl-long.964/) and [paper](https://arxiv.org/html/2502.13791) | 360 histories; 51 coding instructions, including 16 updatable instructions. Smallest evaluated model: Llama-3.1-8B. Its instruction-prompt accuracy was 71.7%; long-history accuracy was 12.5%. Evaluation used temperature zero. | Directly relevant conventions and histories, but the histories fit native context. No ≤4B result or imposed 3,584-token prompt window. Its retrieval results do not establish that restoring genuinely evicted text cannot help. |
| [SpotLight, 2025 / EACL 2026](https://arxiv.org/html/2505.12025) | On 541 IFEval prompts, Qwen2.5-3B loose prompt/instruction accuracy improved from .42/.53 to .53/.62 using attention steering. A separate 300-instance, five-turn experiment tested repetition with **8B** models; reported deterioration fell from roughly 20% to roughly 5%. | Supports instruction emphasis and repetition. Crucially, the 3B result is an attention intervention; the repetition result uses 8B models. It does not reproduce a particular reminder edit for our package. Our reminder already precedes the request. |
| [PartRep, July 2026](https://arxiv.org/html/2607.01792v1) | Greedy evaluation includes Qwen2.5-3B and Llama3.2-3B. Qwen’s seven-benchmark mean changed **66.9→68.5** with full repetition and **66.9→68.3** with PartRep. Full repetition reduced MMLU **62.5→60.3**. On 1,300 RULER questions at nominal 4k length: **77.7→79.2/80.0**. | Strong recent small-model evidence that repetition can help, with heterogeneous effects. Full repetition expands the context budget; PartRep trains a selector on three million tokens. Neither validates a frozen, zero-parameter edit for dense coding conventions under our matched 4,096-token ceiling. |
| [MultiCodeIF, July 2025](https://arxiv.org/html/2507.00699) and [benchmark repository](https://github.com/SYSUSELab/MultiCodeIF) | 2,021 tasks across 14 languages and nine categories. Qwen3-1.7B coding-style accuracy was **44.2%**; Llama3.2-3B was **43.8%**. Published open-model configuration used temperature .2, top-p .9, top-k 1. | Establishes substantial small-model convention-following limitations. It is not a retention intervention and does not justify multiplying marginal accuracies to predict strict success. |
| [Governance Decay / Constraint Pinning, June 2026](https://arxiv.org/html/2606.22528v2) | 1,323 episodes across seven models and seven conditions. Compaction increased pooled violations from **0% to 30%**; approximately 47 tokens of verbatim pinning plus an integrity check restored **0%**. | Closest mechanistic match to eviction. However, the models and sparse policy tasks do not establish ≤4B performance on dense Python conventions; sampling used temperature .7. Supports testing the existing restoration mechanism, not another wording change. |
| [Compact Constraint Encoding, April 2026](https://arxiv.org/pdf/2604.07192) | Main compliance comparison: **247 pipelines**, groups of 82/81/84. Reported header-versus-full-text interval: **[−2.6,+2.1] points**. Normal versus counter-intuitive constraints: **.998 versus .905**. | Encoding changes did little in that setting, while counter-intuitive content mattered. Exact model builds/sampling were obscured by the platform; this is not a small-model, long-history replication. It cannot establish a universal formatting null. |
| [Factorial configuration study, May 2026](https://arxiv.org/pdf/2605.10039) | **1,650 Claude Code sessions**, 16,050 function observations. Size, position, architecture, and conflict comparisons did not survive correction. Bayes factors **.05–.10** supported size/conflict nulls specifically. | Useful evidence against assuming presentation changes reliably solve adherence. It uses Claude and configuration files, not this small-model reminder. Position’s nonsignificance must not be described as affirmative equivalence. |

A frozen encoder is not sufficiently supported either. [Zero-Mem, July 2026](https://arxiv.org/html/2607.29377v1) reports LoCoMo F1 improvements over GAM of **5.40 and 4.87 points**, but uses GPT-4o-mini and **Qwen2.5-14B**, a richer graph/retrieval pipeline, and question answering. That does not justify substituting an encoder-ranked reminder here.

The pinned [Qwen3-4B model card](https://huggingface.co/Qwen/Qwen3-4B/blob/1cfa9a7208912126459214e8b04321603b3df60c/README.md) also supplies no evidence for the proposed Python contract. Its explicit warning against greedy decoding concerns **thinking mode**; it should not be misapplied to this nonthinking experiment.

**Why +10 is meaningfully more decidable**

The saved paired failure differences give \(s_H=0.365148\). At \(N=128\), the paired-t 95% half-width projected from that spread is **6.3866 points**.

| Upper-bound requirement | Approximate probability of certification under zero net harm, holding that spread fixed |
|---|---:|
| ≤ +5 points | **33.4%** |
| ≤ +10 points | **86.9%** |

These are planning calculations, not probabilities that the artifact works. Summing an illustrative paired-discordance model with focus-only and base-only probabilities each \(1/16\) gives **88.1%** certification for the combined +10-point bound and no-demonstrated-increase veto. If total discordance instead doubles to .25, that falls to about **61.3%**.

The same SETUP-derived calculation gives an approximately **2.54-point** 80%-power detectable primary gain at N=128, or **5.08 points** at twice the observed spread.

The paired item—not each regex check—is the inferential unit. This follows standard paired evaluation analysis; see [Adding Error Bars to Evals](https://arxiv.org/html/2411.00640) and [SciPy’s paired-t documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ttest_rel.html).

## 3. Registration text to freeze

The following supersedes `REGISTRATION-4C-DRAFT.md`. Freeze it before new generation.

**Authority and finality.** Brian delegated the D2 override decision to Astra: “use astra to unblock you, go with its deep web research result decision.” This registration exercises that authority for one final unchanged-package confirmation. Earlier registrations retain their original FAILED / NOT PROVEN readings. No terminal outcome permits another policy, model, workload, sample-size, analytical-gate, or decoding revision. NOT PROVEN is final.

**Items and lineage.** Evaluate all **128 unique SCREEN-LONG dialogues** in the existing seed-1 split, first query only. Use the frozen required checks and structure definitions. Do not pool SETUP, use reserve items, replace failures, enlarge N, or select subgroups. The item-file SHA-256 is:

```text
affe6877f059e5f58466023fe70c45cefeadca4b98d1a036832901d14073ce1a
```

The benchmark vendor revision is `1ab87e119b2f9a498de8075219e1c07f6041b394`. No fitting, training, selection, or tuning occurs on these prompts or recorded responses. Labels and the checker remain outside the intervention.

**Artifact and arms.** Use the assembled `deploy/stencil_focus/build/hub-4b` package, trunk `Qwen/Qwen3-4B` revision:

```text
1cfa9a7208912126459214e8b04321603b3df60c
```

Its current package SHA-256, using the runner’s sorted-filename-plus-content algorithm over top-level `.json`, `.py`, `.txt`, and `.safetensors` files, is:

```text
2489b00c4aa9894339c6060d603c0eaac84442c7145b4eaaf963da498cd54fac
```

The two arms differ only in `stencil_focus=false` versus `true`. Generate both through the package’s `FocusSession` and transformers path. Do not reuse research-runtime baseline generations.

Keep `role_evicted`, W=3,584, E=256, and the exact header **“Earlier instructions still in force:”**. Preserve sentence selection, ordering, packing, cropping, current request, and package stopping behavior. Add no encoder, deduplication, supersession processing, output contract, or wording change.

Use nonthinking greedy decoding, bf16, 512 new tokens, and a 300-second generation deadline. Prompt-plus-generation allocation must not exceed 4,096 tokens. Assert matched on/off prompt lengths. Freeze dependencies, numerical backend, tokenizer, generation configuration, and reviewed harness revision before the pilot; do not select them by scores.

**Execution and records.** Execute items in their existing file order, base then focus. Sort item IDs for statistical computation. Record each terminal arm atomically, including item and artifact hashes, runtime, trunk/tokenizer revisions, decoding settings, actual input-token/prompt hashes, prompt length, raw and scoring-normalized output tokens, terminal EOS, timeout/cap status, elapsed time, checker numerator/denominator, score, and failure categories.

Resume only records matching the frozen manifest. Never replace a valid terminal generation. Missing or corrupted records cause INCOMPLETE; they are not silently excluded or imputed as ordinary model failures.

**Primary estimand.** Let \(Y_{ia}\) be the fraction of retained required regex checks passed, weighting checks equally within an item and items equally across the 128 dialogues. Repeated checks within a family remain separate checks. Missing required structure and terminal timeouts score zero. Parseable capped output retains the existing checker’s fractional credit and is separately counted as an output failure.

Let \(D_i=Y_{i,on}-Y_{i,off}\). Report \(\bar D\), the two-sided paired-t p-value, and

\[
[L_D,U_D]=\bar D\pm t_{.975,127}\frac{s_D}{\sqrt{128}},
\qquad t_{.975,127}=1.9788195347.
\]

Efficacy requires **\(L_D>0\)**. Confidence intervals have approximate repeated-sampling coverage; they do not establish generalization to arbitrary projects.

If all \(D_i\) are identical, use the conservative bounded-variable fallback:

\[
[\bar D-r,\bar D+r]\cap[-1,1],\quad
r=\sqrt{2\log(40)/128},
\]

with two-sided bound \(p=\min(1,2e^{-128\bar D^2/2})\). Label the fallback explicitly; do not report a zero-width t interval.

**Output-failure guard.** Preserve the existing definitions of invalid, capped/truncated, degenerate, and timed out. In particular, valid bare Python is not newly invalidated merely for lacking a fence.

Let \(F_{ia}\) indicate any of these failures and \(H_i=F_{i,on}-F_{i,off}\). Compute \(\bar H\) and its paired-t two-sided 95% interval \([L_H,U_H]\) at N=128. If all \(H_i\) are identical, use the existing conservative discordance interval: form 97.5% two-sided Clopper–Pearson intervals for focus-only and base-only failure probabilities and subtract their opposing endpoints.

The guard passes exactly when:

\[
\boxed{U_H\le0.10\quad\text{and}\quad L_H\le0.}
\]

Any \(L_H>0\) is a demonstrated failure increase and vetoes publication, even if \(U_H\le0.10\). An interval containing zero does not establish equivalence. Report total failures, both discordant counts, each category, the net estimate and interval, and exact two-sided McNemar p; also report the paired-t p where defined.

**Companions and readings.** Report the unchanged 10,000-draw, seed-0 paired percentile bootstrap and exact sign test, strict compliance, failure categories, reminder occupancy, prompt lengths, generation lengths, and latency. These never substitute for the primary decision. Apply the exhaustive publication table in section 5 using unrounded endpoints. No interim efficacy or failure-rate analyses are permitted.

**Budget.** The pilot and technical checks use SETUP only and cannot alter scientific eligibility by their scores. Plan 306 generation calls: 48 SETUP technical calls, two clean-environment replay calls, and 256 SCREEN calls.

Pilot the four previously designated longest SETUP items—`359-99`, `352-99`, `351-99`, `302-49`—in both package arms. Let \(t_{\max}\) be the slowest of these eight measured generations and \(S_p\) their summed generation time. Freeze:

\[
C_{\rm SCREEN}=1.5\,t_{\max}\,256.
\]

The remaining technical allowance is \(1.5\,t_{\max}\,42\). Do not launch SCREEN unless

\[
S_p+1.5\,t_{\max}\,298\le30{,}600\text{ seconds}.
\]

This reserves 1.5 hours of the ten-hour total for loading and other GPU overhead. Enforce **both** the generation ceilings and **10 cumulative active GPU-hours**, including loading, aborted work, pilot, and release checks. Finish within three working days. Budget exhaustion is INCOMPLETE, never an invitation to extend or replenish the budget.

**Disclosure.** This registration follows examination of Exp 4 and Exp 4B SETUP results, short-cohort results, CPU register diagnostics, SCREEN metadata and label-derived diagnostics, options/literature memos, and implementation/result audits. These observations informed continuation and analysis. Development included the overflowing-register replacement, post-hoc first-query fractional analyses, trunk and estimand selection, and oracle-threshold selection. Instrument repairs included cumulative oracle replay and Unicode speaker parsing, with the recorded oracle and focus regenerations. Both permitted policy revisions were already consumed.

The known Exp 4B result included one focus-only failure, one base-only failure, and a positive descriptive fractional effect. The present +10-point margin and demonstrated-increase veto were chosen with those results known. SCREEN is generation-unseen, not item-unseen.

The package and research runtime have materially different outputs; their raw token-parity comparison also mixes EOS recording conventions. Exp 4C evaluates the package itself and retains its stopping behavior. Research-runtime results are not attributed to the package. All earlier results, repairs, parity artifacts, and this decision remain disclosed.

## 4. Exact operational sequence

1. **Record and freeze this decision.** Update the ledger STATE and registration, including the delegated exception, immutable artifact/item hashes, and exhaustive outcomes. Preserve the original registrations and negative results. No further permission request is needed for this decision.

2. **Repair the evaluation harness before GPU work.** The current runner is not ready merely because it imports reviewed helpers:
   - `--runtime package --primary fraction` still reaches the old bootstrap/focus-only gate. Implement the registered paired-t primary and net-failure guard through the actual summary consumer.
   - Resume matching currently ignores package hash and generation path. Make both resume and summary reject mismatched manifests, wrong runtime/configuration, duplicate IDs, missing arms, and incomplete N.
   - Verify and record the **actual generated input**, not only reconstructed token counts.
   - Recheck time remaining after lazy model loading and before generation. Enforce cumulative ceilings on the final generation as well as before subsequent work.
   - Keep raw terminal tokens distinct from scoring-normalized tokens; correct the parity wording without changing the artifact.
   
   Exercise the actual consumer with CPU fixtures covering every reading, boundary equality, zero variance, terminal failures, changed hashes/runtime, missing records, final-call budget breaches, and label isolation. Leave Exp 4B’s analysis unchanged.

3. **Do not waive D1.** This strategy consult is not an implementation review. Reused helpers do not establish correctness of the new generation path, manifest validation, or decision consumer. Run **one focused, author-disjoint implementation review**, following the repository’s reviewer rule: Opus at maximum effort, with any Astra substitution explicitly recorded in the review header. Fix or refute blocking findings before generation. There is no additional scientific-review stage.

4. **Pilot, then append only the deterministic measured budget.** Run the eight fixed SETUP pilot generations. Save timings and records. Apply the formula above without inspecting scores to choose a policy or launch threshold. At the old research timing maximum, the 306-call, 1.5× planning allowance is approximately **6.07 generation-hours**; at 40 seconds per call, raw generation time is **3.40 hours**. Neither replaces the package measurement.

5. **Complete package qualification without another efficacy gate.** Reuse the eight pilot calls while completing all 16 SETUP items in both package arms: 32 package calls total. Run the plain transformers model on the same 16 off-arm prompts with identical decoding and stopping settings; require **16/16 exact off/plain token matches**. Independently verify all 32 package prompt bytes and matched lengths. In a clean environment, replay fixed item `351-99` in both modes and require agreement with the initial package outputs. This brings technical work to 50 calls. Do not rerun research-runtime output parity or require cross-runtime output equality.

6. **Launch SCREEN only after those checks pass.** Use one resident 4B model, a 32-GB declaration, reservations no longer than 55 minutes, and runner budgets no longer than 50 minutes. After loading, start a fresh two-arm pair only with at least 600 seconds of runner time available; retain the reservation buffer. Use absolute paths, owned-PID registration, atomic records, and normal manifest-validated resume. Do not use `--force` or regenerate terminal failures. Monitor completion and cost, not interim scores.

7. **Summarize once and audit once.** After all 128 pairs finish—or a terminal budget/integrity stop—run the corrected package/fraction summary against the frozen manifest and ceiling. Write `RESULTS-4C.md`, all companions, and the applicable reading. Conduct one result audit of coverage, arithmetic, attribution, and publication eligibility. A reporting correction cannot change the policy, discard outcomes, or authorize another experiment.

8. **Apply the publication gate mechanically.** Complete registration, pilot, and implementation review on day 1; technical checks and SCREEN on day 2; final summary, audit, and any authorized HF publication by day 3. Force-add registered result artifacts because `results/` is ignored, verify tracking with `git ls-files`, and respect wrapper locks and explicit commit pathspecs. A GitHub remote push still requires Brian under D9; the qualifying HF push is authorized by this decision. Missing HF credentials are an operational interruption, not a scientific choice.

## 5. Publication on every possible reading

For every outcome, preserve the registration, records, manifest, implementation/result reviews, timings, prior negatives, and disclosures in the repo. Report available descriptive results on an incomplete run, clearly identifying missingness.

Apply this table in order:

| Condition | Final reading | Publication |
|---|---|---|
| Required technical checks fail; primary records are missing/mismatched; or a registered budget is breached | **INCOMPLETE** | Repo report and available records; no 4B HF push. End this line. |
| Valid complete primary interval has \(U_D<0\) | **HARM: reduced checked adherence** | Repo negative; report failure evidence separately; no HF push. |
| Valid complete primary interval contains zero | **NOT PROVEN: insufficient efficacy evidence** | Repo negative; no HF push. Report any demonstrated failure increase explicitly. |
| \(L_D>0\), but \(L_H>0.10\) | **Positive efficacy / demonstrated failure increase exceeding the margin** | Repo findings; artifact NOT PROVEN; no HF push. |
| \(L_D>0\), and \(0<L_H\le0.10\) | **Positive efficacy / demonstrated failure increase** | Repo findings; artifact NOT PROVEN regardless of the upper bound; no HF push. |
| \(L_D>0\), \(L_H\le0\), but \(U_H>0.10\) | **Positive efficacy / noninferiority unresolved** | Repo findings; artifact NOT PROVEN; no HF push. |
| \(L_D>0\), \(L_H\le0\), \(U_H\le0.10\), and release verification passes | **PROVEN within the registered scope** | Repo evidence and HF publication at `bmarti44/stencil-focus-qwen3-4b`. |
| Statistical publication conditions pass, but the release’s identity, clean-environment verification, or off-switch verification fails | **Positive paired result / release blocked** | Preserve the positive measured result in the repo; artifact NOT PROVEN for release; no HF push or scientific rerun. |

On the qualifying HF outcome, use this claim template, substituting computed values:

> **Measured instruction-retention improvement under imposed context eviction.** On 128 frozen MemoryCode SCREEN-LONG first-query items, this exact package with `stencil_focus=true` achieved mean required-check adherence of [ON]% versus [OFF]% with `stencil_focus=false`: paired difference [DELTA] percentage points, 95% CI [LOWER, UPPER], two-sided paired-test p=[P].
>
> Any-output-failure rates were [ON_FAILURE]% and [OFF_FAILURE]%; the paired net difference was [ETA] points, 95% CI [FAILURE_LOWER, FAILURE_UPPER]. This passed the preregistered +10-point upper-bound requirement and showed no statistically demonstrated failure increase. It does not establish equal reliability.
>
> The evaluation used Qwen3-4B, greedy nonthinking decoding, a 3,584-token prompt budget, and at most 512 generated tokens. It measures checked coding-convention adherence on supplied session histories under eviction. It does not establish functional correctness, complete instruction compliance, or autonomous coding-session performance.
>
> Exp 4B previously failed its qualification. This final confirmation followed disclosed development results, SCREEN metadata/label-derived diagnostics, and an owner-authorized analytical revision. The package was evaluated through its own generation path; earlier research-runtime results are reported separately.

Replace the current card’s attribution of research-runtime Exp 4B efficacy to “this artifact.” No nonqualifying outcome authorizes a descriptive HF fallback, another reminder fix, or an Exp 5 rescue under this decision.
