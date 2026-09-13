**Rev 5 is INELIGIBLE and stays stopped. A newly registered, six-family version of A reaches my 25% bar: approximately 30% artifact-success probability.** That forecast treats contract execution as something to learn, retains the difficult policy families as targets, and excludes dependency and immutability work. It does not reinterpret the failed pre-check as a pass.

I recomputed the recorded counts, intervals, and probe transitions, and verified the three registered source hashes. I inspected task definitions and saved outputs. I did not run models or read `data/bench/`.

The reading of the pre-check is straightforward:

| Quantity | Result | Reading |
|---|---:|---|
| Joint success | 14/32; exact binomial 95% interval [0.264, 0.623] | Fails the registered ≥16 rule |
| Functional success | 24/32; interval [0.566, 0.885] | Passes the registered ≥20 rule |
| Operational eligibility | **INELIGIBLE** | Stop before training |

The interval covering 50% does not override the count rule. Conversely, failing that rule does not establish that population competence is below 50%. Under an independent-binomial model, the two-sided test against 50% gives **p = 0.597**. This is a **failed eligibility criterion**, with insufficient evidence for a population-below-threshold claim—not demonstrated harm or equivalence. [Registration](/home/bmarti44/stencil-llm/results/contracts/REGISTRATION-PRECHECK.md:22).

There are two important qualifications to those intervals and family summaries.

First, these are eight project constructions with four contract-state combinations each. The binomial intervals reproduce the registration, but do not account for project clustering or establish uncertainty over general maintenance work.

Second, **15/24 is not 15 successful tasks among 24 distinct tasks**. It sums overlapping family memberships. Exporter’s four successes enter both return shape and error surface. Recomputing from the records:

- Tasks containing at least one of return shape, error surface, or logging: **11/20 J**.
- Tasks containing only those families: **4/4 J**, all from exporter.
- Tasks excluding dependency and immutability: **8/16 J, 14/16 functional**, across mailer, auth, ledger, and exporter.

These are exploratory summaries, not a replacement eligibility test. Moreover, “logging 4/8” means joint success on tasks containing logging; it does not measure logging adherence separately. The scorer skips contract tests after functional failure. [Records](/home/bmarti44/stencil-llm/results/contracts/precheck.jsonl), [scorer](/home/bmarti44/stencil-llm/src/stencil/contracts.py:136).

The precedent probe changes my diagnosis, but less decisively than the ledger claims. Its paired J outcomes are **two gains, two losses, twelve unchanged**; exact McNemar **p = 1.0**. A conservative simultaneous-binomial difference interval is approximately **[−40.9, +40.9] percentage points**, under task independence. The users project remains 1/4.

Therefore:

- This particular override paragraph produced no net improvement.
- The repeated users failures support a behavioral diagnosis of copying local conventions despite an explicit contrary rule.
- They do not establish that reminders generally cannot help, or identify attention as the causal mechanism.

My current diagnosis is **unreliable selection and execution of the governing rule, compounded by code-integration failures**. Local imitation is one contributor. Missing-record omissions can also reflect defaults learned during training or incomplete handling of exceptional paths. Returning an updated frozen object without storing it is an integration failure. “Capability” and “attention” are not competing explanations at this level: reliable instruction-conditioned execution is itself a capability.

Research supports nearby mechanisms:

| Source | What it supports |
|---|---|
| Kou et al., **arXiv:2306.01220; DOI:10.1145/3660807** | Code-generation models attend differently from programmers; analysis of incorrect code identifies recurring attention patterns associated with errors. It does not isolate stale repository precedent overriding an authorized change. [Paper](https://arxiv.org/abs/2306.01220) |
| Tian and Zhang, **Selective Prompt Anchoring, arXiv:2408.09121; ICML 2025** | Attention to the user prompt diminishes during code generation; changing its influence improves generation in their experiments. This directly cautions against concluding that attention interventions cannot help from one failed paragraph. [Proceedings](https://proceedings.mlr.press/v267/tian25a.html) |
| Verma, **arXiv:2607.26117** | Small code models frequently reproduce failed attempts when given them for repair; blind resampling beats feedback-conditioned repair below 7B in that study. This is direct code-specific evidence for anchoring on previous code. [Paper](https://arxiv.org/abs/2607.26117) |
| Wan et al., **arXiv:2602.03664** | Multi-turn agents imitate previous responses; preference training aimed at conversational inertia improves outcomes. The authors explicitly disclaim definitive causal identification from their attention evidence. This concerns agent histories, rather than the present single-request repository task. [Paper](https://arxiv.org/html/2602.03664v1) |
| Ali et al., **arXiv:2410.01288** | Demonstrates copying answers from in-context examples instead of generalizing the task pattern. Relevant supporting evidence, not a coding-contract experiment. [Paper](https://arxiv.org/abs/2410.01288) |

I found no verified study that establishes the exact causal claim here: **this Qwen3-4B package follows contradictory in-file precedent because of a particular attention mechanism**.

My revised A forecasts are:

| Version | Artifact-success forecast | ≥25%? |
|---|---:|---|
| **(a) Rev 5 as registered** | **0% through its authorized experimental path** | **No** |
| **(b) Six-family A:** return shape, error surface, and logging as supporting requirements; naming, validation, and missing-record behavior as trained targets; dependency and immutability excluded | **30%** | **Yes** |
| **(c) All eight families retained, but a new registration treats contract failures as training targets and removes the J eligibility prerequisite** | **22%** | **No** |

The zero in (a) is procedural: the registered path has terminated. It is not a claim that training could never work. The 22% row estimates a new all-eight-family program instead.

I interpret (b) as a **six-family operating domain**, not a three-family evaluation with three additional training-only families. If naming, validation, and missing-record behavior are the proposed benefit, they must remain in the primary outcome.

These are subjective end-to-end research forecasts, not estimated frequencies or confidence bounds. A plausible judgment range around the leading 30% is roughly **15–45%**. The owner’s bar concerns my forecast, not its lower uncertainty bound.

The leading estimate corresponds approximately to **55% probability of completing and passing the screen**, followed by **55% probability of successful confirmation and publication conditional on that pass**: about 30% overall. Those conditional judgments include compute, functional preservation, transfer, and the strength of the SFT control.

**The measured stale-precedent failures raise A’s odds relative to memory-only interventions. They do not automatically raise its absolute odds.** They identify a recurring wrong alternative that a counterfactual objective can penalize while preserving the correct alternative under a different rule. Functional success on many failures makes this more promising than a setting dominated by unparsable or nonsensical programs.

Against that, the pre-check weakens the original assumption that basic execution was already secured. The eight-family program’s integration burden remains substantial. The six-family reframing improves the forecast by removing that burden—not by declaring the remaining failures solved.

Ordinary SFT remains the strongest objection. It receives both current-rule solutions under their corresponding histories and can learn the same conditional mapping. The data support **training this behavior** more strongly than they support **the incremental preference objective**.

Positive transfer evidence exists: **ComplexConstraints, arXiv:2606.09118**, reports Qwen3-4B gains of 15.5 points on per-criterion compliance and 7.1 points on an independent multi-turn-context evaluation. Those are single-seed results under a different training procedure and outcome. **Supersede, arXiv:2606.27472**, reports held-out updating accuracy improving from 7/78 to 13/78, illustrating both trainability and limited absolute transfer. Neither supplies A’s success probability. [ComplexConstraints](https://arxiv.org/html/2606.09118v1), [Supersede](https://arxiv.org/html/2606.27472v1).

For the other directions, I retain round 6’s **full-goal** interpretation of artifact success: useful joint improvement, acceptable functional performance and cost, and a defensible contribution beyond the obvious existing method.

| Rank | Direction | Forecast | ≥25%? | Decisive consideration |
|---:|---|---:|---|---|
| 1 | **Six-family A** | **30%** | **Yes** | Directly targets recurring rule-selection errors; SFT superiority remains uncertain |
| 2 | **B: recovery training** | **24%** | No | Concrete repairable failures exist, but anchoring and matched blind retries remain serious opponents |
| 3 | **E: gated intervention** | **20%** | No | Could change rule application, but applicability learning and functional interference remain unmeasured |
| 4 | **F: transactional validation** | **18%** | No | Can detect these violations; completing useful repairs and establishing a distinct contribution are harder |
| 5 | **C: selective memory** | **16%** | No | The new failures occur with the rules already present; memory preservation alone misses the binding problem |
| 6 | **D: contrast decoding** | **12%** | No | Plausible attention benefit, substantial direct prior coverage, and no dependable integration remedy |

If the event is **only an engineering wrapper that improves J over its unmodified baseline**, I would put F around **40%**, and ordinary execution-verified SFT around **45%**. Those clear 25% for that narrower event. They do not thereby satisfy the owner’s novel-recombination requirement. This distinction must remain explicit; otherwise the forecast changes meaning between candidates.

For the leading six-family A, the criterion verdict is:

| Criterion | Verdict | Decisive reason |
|---|---|---|
| Novel recombination | **NOT DISPROVED** | A narrow claim survives: temporal/scoped policy changes coupled to executable maintenance, with incremental value assessed against matched SFT |
| Useful | **NOT DISPROVED** | Missing-record behavior, validation placement, and public API compatibility can materially affect maintenance |
| More than a meaningless permutation | **NOT DISPROVED** | Rejecting the stale patch changes the optimization; whether that matters is testable |
| Significant difference | **NOT DISPROVED** | A material joint-success gain is plausible; cosmetic naming substitutions alone would not establish it |
| ≥25% artifact-success forecast | **NOT DISPROVED** | My forecast is approximately 30% |
| All criteria prospectively | **NOT DISPROVED** | Sufficient basis for one bounded screen; no efficacy claim has been established |

The novelty claim must remain narrow. **IOPO, arXiv:2411.06208**, already uses input-output preference relationships; **CRPL, arXiv:2608.29352**, combines related-instruction perturbations with verified preference construction. The conversational-inertia paper also means that **preference training against harmful imitation is already prior art**. A needs its executable temporal/scoped result and its SFT comparison. [IOPO](https://arxiv.org/abs/2411.06208), [CRPL](https://arxiv.org/abs/2608.29352), [Conversational inertia](https://arxiv.org/html/2602.03664v1).

The minimum screen registration I recommend is the following. These are proposed choices for the **new program**, not amendments to the failed pre-check.

1. **Freeze the domain and lineage.** Use the six families above. Exactly one of naming, validation, or missing-record behavior is the changing target per session; one of return shape, error surface, or logging is a supporting requirement. Training, screen, and confirmation use disjoint projects and solution constructions. Keep all inspected pre-check prompts and responses excluded from fitting. Record that family selection used the pre-check’s exploratory summaries.

2. **Use N = 48 independent projects, one session each.** Give each target family 16 sessions and each supporting family 16. Cover all nine pairings: six sessions in each diagonal cell of a fixed 3×3 ordering, five in every other cell. Allocate 12 sessions each to stable rules, replacement, scoped exception, and reinstatement. Freeze the complete assignment manifest before generation. Contract-state variants of one repository do not become separate independent observations.

3. **Keep three arms: `off`, `sft`, `cf`.** Same frozen Qwen3-4B trunk, tools, session memory, rendering, generation limits, and initial repositories. Off bypasses the adapter. SFT receives every positive history/solution used by CF, including both counterfactual directions and irrelevant-history variants. CF adds the stale-alternative preference term. No teacher or private scoring diagnostics enter inference.

4. **Fix the training intervention before the screen.** A concrete small recipe is rank-16 LoRA, alpha 32, dropout zero, AdamW learning rate \(10^{-4}\), gradient clipping 1, seed zero; completion-token mean cross-entropy plus \(0.1\,L_{\mathrm{DPO}}\), with DPO \(\beta=0.1\) and the frozen trunk as reference. Use 576 authored counterfactual pairs, balanced across the nine pairings and four lifecycle classes, with an irrelevant-history variant of each history. Both directions must have executable gold patches; the stale alternative must fail the applicable contract. Counterbalance the convention shown by the existing code. Use a fixed four-hour training allocation per adapter, including CF reference scoring, and the final completed update—not the best checkpoint. SFT can make more passes through the same positives within its equal allocation. Report actual exposure and compute.

5. **Make the session genuinely stateful within the existing screen.** Use a frozen 16-turn prefix and two live coding requests. Apply each arm’s first patch to its own repository; its second request sees that resulting state. Put the relevant replacement, exception, or reinstatement between the live requests; stable cases receive an irrelevant message instead. Exercise compaction in the prefix and between requests. Freeze the common memory/packing policy and show exactly which historical instructions reach the model. No externally computed “current rule” answer is supplied. This remains a limited history-replay screen.

6. **Define one binary session outcome.** \(J=1\) only if both live checkpoints pass the task’s functional requirements, protected regression requirements, and all applicable contract checks. Define function-only success over those same checkpoints. No partial credit in the primary outcome. One generation per request, greedy, thinking disabled, at most 1,536 new tokens, with prompt plus reserved output ≤4,096. Parsing failures, failed patch application, truncation, timeout, and abandonment count as failures. Private tests remain private.

7. **Use an explicit development gate.** CF must achieve at least **five net J wins over off**, at least **three over SFT**, and **no observed net function-only decline against either**. In the 36 changing-rule sessions, require positive net J advantage over both comparators; require nonnegative net J differences within each of replacement, scope, and reinstatement separately. Report paired wins/losses/ties, two-sided exact McNemar p-values, and 95% paired intervals. These statistical summaries do not replace the development count gates. Failure stops this configuration; it does not demonstrate equivalence.

8. **Cap the entire screen at 16 GPU-hours.** Include timing, both four-hour trainings, reference scoring, loading, and \(3×48×2=288\) evaluation generations. Use the required maximum-context pilot and the protocol’s 1.5 contention factor. The observed pre-check average is 18.8 seconds per task; extrapolating it gives about 1.5 hours for 288 calls, but it does not measure long-context or training throughput. If the measured workload does not fit, record cost-ineligible; if a launched run exhausts its ceiling, record incomplete. Do not reduce N, drop failures, or select a checkpoint to rescue it.

Save per-request prompts, outputs, repository hashes, rule-state annotations, separate test outcomes, timing, tokens, and terminal reasons as work completes. Run this through the existing registration, implementation-review, and result-audit process. No additional review stage is justified.

The screen does not prove autonomous long-session reliability. The existing confirmation must test the live-session behavior claimed by the eventual card. If confirmation merely repeats a frozen prefix plus two actions, the claim must say that. My 30% forecast includes the risk that adequate confirmation cannot be completed within the program’s compute ceiling.

There are three further issues the owner should address.

**The checker currently measures less than “all applicable contracts.”** In auth, the logging instruction explicitly covers issuing and rotating tokens, but the warning test checks rotation, and the gold code leaves issuance unchanged. That test also accepts any matching warning rather than enforcing exactly one. The storage-validation gold retains validation in the existing public function despite the globally worded rule. These are concrete scope and coverage mismatches. [Tests and contract wording](/home/bmarti44/stencil-llm/src/stencil/contract_projects_reg.py:774), [gold construction](/home/bmarti44/stencil-llm/src/stencil/contract_projects_reg.py:823).

Preserve the sealed result. Fix these construction problems before freezing new work: either explicitly grandfather existing operations or test the required migration. Gold passing and cross-state gold failing are useful self-checks, but do not establish complete specification coverage.

**The 25% bar makes a bounded investment decision possible; it does not fully specify the research goal.** The sampling distribution, live horizon, practical improvement, functional guard, and publication claim still determine what “success” means. Freeze those once. A 30% forecast is a reason to purchase the screen’s information, not a reason to continue reframing until a favorable result appears.

**The package card needs a narrow, factual negative.** Suitable wording is:

> On 32 registered immediate-instruction tasks across eight authored projects, greedy non-thinking generation passed the functional tests on 24 tasks and both functional and contract tests on 14. The registered eligibility rule failed, and the proposed training program stopped before training. All outputs parsed and none were truncated. This test does not establish reliable contract adherence or measure the long-session memory modification’s benefit.

Report the intervals with their project-dependence limitation. Avoid “4B cannot do this,” “attention is the cause,” or “the wrapper fixes these failures.”

There are also existing documentation discrepancies: [RESULTS-4C](/home/bmarti44/stencil-llm/results/memorycode-long/RESULTS-4C.md:15) says the 4B artifact was withheld from Hugging Face, while the local [hub-4b card](/home/bmarti44/stencil-llm/deploy/stencil_focus/build/hub-4b/README.md:4) identifies a 1.7B trunk and says the earlier head-to-head has not run. I have not verified a later remote upload. Any published card must identify the actual trunk and completed results accurately.
