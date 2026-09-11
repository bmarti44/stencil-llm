**Execute as written: 24/100 — reject.** Exp 1 is salvageable. Exp 2 cannot establish its advertised mechanism. Exp 3 is an underspecified benchmark adaptation. The process changes would recreate several failures the audits identified.

1. **CRITICAL — A/B2: the uniform control does not isolate selection from emphasis.** The wave learns both a varying gain and a spatial field over **every prompt token**. The proposed uniform arm applies fixed β=2 only to active ledger sentences. Consequently, the contrast changes timing, strength, spatial support, and concentration simultaneously. A wave win could reflect avoiding excessive emphasis, emphasizing task text, or using familiar historical wording—not choosing the governing obligation. Peak normalization does not match total bias or resulting attention mass. See [wave.py:20](/home/bmarti44/stencil-llm/src/stencil/wave.py:20), [w0_train.py:75](/home/bmarti44/stencil-llm/scripts/w0_train.py:75), and [w_seal.py:58](/home/bmarti44/stencil-llm/scripts/w_seal.py:58).

   Retain a practical uniform baseline, but add controls that preserve the checkpoint’s timing/gain while perturbing spatial selection, and controls that preserve spatial selection while removing query or step dependence. Match candidate support and register dose selection on development data. Measure where the field acts.

2. **HIGH — A/B2: the claim outruns the task and existing evidence.** The harness supplies an already resolved live ledger at every work turn. The controller does not discover updates or clears; `prompt_at` serializes their correct result for it. The task has three ordinary obligation types plus the held-out comment type, not the SELECTOR task’s 32 obligations. Furthermore, the prior readout experiment explicitly found that the field was **not decodable as “the governing rule now”** under its registered rule. An adherence gain does not overturn that finding. See [t2_sessions.py:295](/home/bmarti44/stencil-llm/src/stencil/t2_sessions.py:295) and [WORKLOG.md:1331](/home/bmarti44/stencil-llm/WORKLOG.md:1331).

   Narrow the claim to conditional attention allocation given a correct external ledger, or add direct tests of current versus stale authority, cleared obligations, and dependence on the current query.

3. **HIGH — A: the literature positioning contradicts the repository’s own research.** SpotLight is not accurately described here as a static, single-turn, uniform-bias equivalent. The local literature audit identifies dynamic deficit-triggered bias and multi-turn evaluation. The earlier search also identifies AutoPASTA’s automatic span selection. Those do not eliminate a narrower learned-controller contribution, but they invalidate the proposed novelty shortcut. See [astra-research-blockers.md:214](/home/bmarti44/stencil-llm/results/astra-research-blockers.md:214), [astra-research-blockers.md:222](/home/bmarti44/stencil-llm/results/astra-research-blockers.md:222), and [research-wave-prior-art.md:11](/home/bmarti44/stencil-llm/results/research-wave-prior-art.md:11).

4. **HIGH — B2: the proposed “fresh sealed” seed block was explicitly retired after exposure.** `13,600,000+i` appears in W3’s registration history. The subsequent amendment says that block was instantiated during review and replaces it; another amendment explicitly supersedes it. Switching to `split="final"` does not establish independence from the exposed construction. See [w3-prereg-draft.md:65](/home/bmarti44/stencil-llm/results/w3-prereg-draft.md:65) and [w3-prereg-draft.md:88](/home/bmarti44/stencil-llm/results/w3-prereg-draft.md:88).

   Reserve a genuinely unused block. Keep smoke fixtures outside it.

5. **HIGH — B2/F: the comment null is contaminated by a checker bug.** `score_work` takes `ast.get_source_segment(code, fn)` and requires its final nonempty line to equal `# reviewed`. Python’s function AST ends at the last statement and excludes a trailing comment. I reproduced this with a standard-library-only fixture:

   ```python
   def f(a, b):
       return a + b
       # reviewed
   ```

   The extracted segment ends at `return a + b`; the check returns false. The canonical builder itself generates precisely this trailing-comment form. Existing reference tests use `split="dev"`, so they miss the held-out comment case. Moreover, `_oracle_moment` has no comment branch. See [t2_runner.py:91](/home/bmarti44/stencil-llm/src/stencil/t2_runner.py:91), [wave_ref.py:29](/home/bmarti44/stencil-llm/src/stencil/wave_ref.py:29), [test_wave_ref.py:18](/home/bmarti44/stencil-llm/tests/test_wave_ref.py:18), and [t2_runner.py:264](/home/bmarti44/stencil-llm/src/stencil/t2_runner.py:264).

   “The model never produces the comment and even the hand press cannot induce it” is therefore unsupported by these scores. Fix the checker prospectively, qualify the historical aggregate, and verify compliant and noncompliant comment fixtures through the actual consumer.

6. **HIGH — B2: LoRA is neither adequately matched nor adequately specified.** The dimension arithmetic is correct: eight layers × rank four × `(4096+3072)` gives **229,376 parameters**. That is **13.22% fewer** than 264,321. More consequentially, the plan leaves scaling, adapter initialization, regularization, training scope, checkpoint selection, and development tuning unspecified. “Same recipe” is ambiguous because the wave objective includes a gain-specific L1 penalty that LoRA cannot share literally. One LoRA seed versus three wave seeds also gives an asymmetric comparison, especially when H4 compares LoRA against the best observed wave.

   LoRA also freezes the original weights, is removable, and adds no prompt tokens. Those are not residual advantages unique to the wave. See [qwen3.py:247](/home/bmarti44/stencil-llm/src/stencil/qwen3.py:247), [w0_train.py:103](/home/bmarti44/stencil-llm/scripts/w0_train.py:103), and the existing removable-adapter result in [check49/README.md:5](/home/bmarti44/stencil-llm/results/quick-checks/check49/README.md:5).

   Register an approximately equal parameter budget, comparable seed coverage, and equal development-selection allowance. If LoRA is dropped, drop the associated superiority/falsification claim too.

7. **HIGH — B2: the inference and verdicts do not match the claim.** A sign test on session adherence differences tests the balance of positive and negative differences, not mean adherence gain. Sessions with small wins can outnumber sessions with large losses. Specify whether the target is session-level win probability, mean session adherence, or pooled opportunity adherence. The secondary work-level McNemar p-value remains uncalibrated for clustered works merely because a “clustering caveat” accompanies it. See the distinction between cluster means and pooled cells in [stats.py:132](/home/bmarti44/stencil-llm/src/stencil/stats.py:132) and the exact binary test in [stats.py:122](/home/bmarti44/stencil-llm/src/stencil/stats.py:122).

   The readings also overlap or omit cases: two significance failures can coexist with disagreement in sign; exactly one nonsignificant positive seed has no clear outcome. Failure to beat uniform does not establish equivalence or make the wave “an automatic SpotLight.” A LoRA point estimate above all waves does not establish matching performance. Register exhaustive outcomes and effect intervals. Requiring all three wave tests to pass is a conjunction; its main problem is not a missing blanket Bonferroni correction.

8. **HIGH — B2/C: the plan omits directly relevant competence harm from the very checkpoint it proposes to revive.** The repository records `w0-ce` reducing MMLU from 48.05% to 45.83%, with 175 degradations versus 57 improvements, and failing the registered noninferiority gate. GSM8K also failed its noninferiority gate. These belong prominently in the research add-on’s card and interpretation, not behind a generic list of other failed wave recipes. See [WORKLOG.md:1586](/home/bmarti44/stencil-llm/WORKLOG.md:1586) and [WORKLOG.md:1613](/home/bmarti44/stencil-llm/WORKLOG.md:1613).

   The new safety rule also rejects the motivating seal: **21/408 = 5.15% paired-broken works**, above 5%. That may be a reasonable prospective standard, but it is a deliberate change requiring explanation—not an automatic correction of an old malformed rule.

9. **MEDIUM — B2/F: the reproduction instructions have avoidable traps.** The cited `manual_seed(0)` lines exist, but the shuffle generator is separately seeded at [w0_train.py:196](/home/bmarti44/stencil-llm/scripts/w0_train.py:196). Specify which random streams vary. Model loading and CUDA initialization occur at module top level, so importing this trainer for LoRA helpers is unsafe; see [w0_train.py:46](/home/bmarti44/stencil-llm/scripts/w0_train.py:46).

   Also, the checkpoint ZIP contains paths beginning `w0-ce/`. Saving identical tensors as `w0-ce-s0.pt` can change the serialized file hash through the archive name. Compare canonical tensor content, or reproduce the original serialization name in an isolated output directory. “Logs mismatch” is insufficient provenance for subsequent pooled analysis.

10. **HIGH — B1: 909 conversations are not 909 independent source prompts.** I reconstructed the saved first-user token sequences: there are **484 distinct first prompts**, comprising **425 pairs and 59 singletons**. The key prefixes give the same grouping. For example, `conv-000` and `conv-001` have keys `1000:1:en` and `1000:8:en` and identical first prompts. See [conv-000.json:4](/home/bmarti44/stencil-llm/results/qwen/multiif-evict-909-prequery-v2/conv-000.json:4) and [conv-001.json:4](/home/bmarti44/stencil-llm/results/qwen/multiif-evict-909-prequery-v2/conv-001.json:4).

   `_cluster_values` clusters only within each conversation, leaving shared-source dependence unaddressed. Use source-prompt clustering, or justify the narrower estimand and report this sensitivity. This does not erase the large historical recovery: my source-grouped sensitivity still gives extremely small C1/C3 p-values. It matters particularly for the proposed small incremental C4 effect. See [multiif_evict.py:488](/home/bmarti44/stencil-llm/scripts/multiif_evict.py:488).

11. **HIGH — B1: the readings cannot justify the shipping decision.** A nonpositive estimate, or a confidence interval crossing zero with a small estimate, does not establish that pins are dispensable. Register a practical margin and an equivalence/noninferiority decision if that is the product question. Conversely, a statistically positive but negligible pin increment does not automatically justify maintaining KV surgery.

   More seriously, the mandatory experiment tests **classifier-selected echo**, while the fallback package ships **role-selected echo**, which is optional. The existing role comparator selects recent user **token columns**, possibly partial sentences, and borrows its budget from the classifier. It is not an independently specified reminder policy. See [multiif_evict.py:271](/home/bmarti44/stencil-llm/scripts/multiif_evict.py:271) and [multiif_evict.py:823](/home/bmarti44/stencil-llm/scripts/multiif_evict.py:823). Make the proposed shipping arm mandatory and define its standalone budget.

12. **HIGH — B1/F: saved records are sufficient for replaying inputs, not for an uncontrolled historical/new-runtime comparison.** The saved echo IDs and eviction coordinates exist. However, `_score_fields` requires original benchmark instruction IDs and kwargs; those scoring specifications are not contained in the listed saved fields. The old metadata also does not pin every relevant runtime component, including the Qwen implementation. A new arm compared against historical outputs needs a verified compatible model, tokenizer, code, numerical environment, and scorer. See [multiif_evict.py:715](/home/bmarti44/stencil-llm/scripts/multiif_evict.py:715), [multiif_evict.py:742](/home/bmarti44/stencil-llm/scripts/multiif_evict.py:742), and [meta.json:27](/home/bmarti44/stencil-llm/results/qwen/multiif-evict-909-prequery-v2/meta.json:27).

   Add baseline replay checks on separate verification records before sealing the new arm. Preserve the current historical safety verdict; a new tolerance is a prospective rule or retrospective sensitivity, not a repaired original PASS.

13. **MEDIUM — B1/A: two causal statements are wrong.** `clf_pinned_echo − clf_pinned` already isolates adding echo **conditional on fixed pins**; those arms do not differ in pins. The missing arm identifies the pin increment conditional on echo and completes the factorial comparison. See [multiif_evict.py:842](/home/bmarti44/stencil-llm/scripts/multiif_evict.py:842).

   Neither outcome identifies whether a separately designed deficit-gated bias would help retained columns. Making that research conditional on C4 can be a spending preference, but it is not scientific falsification of the wave mechanism.

14. **HIGH — B3: MemoryCode’s proposed port does not yet define a reproducible experiment.** `vendor/memorycode` is absent. There is no locally inspectable adapter, pinned upstream evaluator, or mapping from its native examples to the proposed “item.” Given-text sessions can support a replay-based retention test, but converting them into user/assistant turns is a substantive prompt transformation. Specify native prompts, session/query boundaries, whether prior answers are supplied or generated, where eviction occurs, positional treatment, and the unit that contains shared history.

   The existing Multi-IF helper actually prefills history, evicts it, then prefills the current turn while preserving absolute positions. Ordinary text truncation is a different intervention. See [qwen3.py:88](/home/bmarti44/stencil-llm/src/stencil/qwen3.py:88). Call the result a **MemoryCode-derived evaluation** unless native protocol comparability is established. The earlier local audit already distinguishes its convention checks from functional coding success: [astra-research-blockers.md:43](/home/bmarti44/stencil-llm/results/astra-research-blockers.md:43).

15. **HIGH — B3: the oracle is not automatically a ceiling, and label isolation is unspecified.** A label-derived set of applicable instructions may exceed 256 tokens, may require several mutually dependent instructions, and may not map verbatim to a candidate sentence. Ordering or truncation can change performance. An oracle echo can even underperform another echo, so its observed score is not an upper bound on attainable performance.

   Freeze candidate extraction from raw history independently of gold applicability. Only the oracle arm may access applicability/update labels. Use a common budget accounting rule, including headers and source labels, and specify packing, ties, duplicates, and overflow. Otherwise the apparent selector gap can arise from privileged extraction or rendering rather than ranking. The existing renderer adds its own header and bullets without a budget limit: [ledger.py:337](/home/bmarti44/stencil-llm/src/stencil/ledger.py:337).

16. **HIGH — B3: the proposed selectors do not test the same capability.** The frozen classifier returns `P(rule)+P(fact)` and the registered Multi-IF invocation provides **empty context**. It detects salience; it does not rank applicability to the final query. The wave was trained on generation-step states and individual prompt-token keys. Turning it into a once-per-query sentence retriever requires a specified pooling and ranking rule and changes its input distribution. See [selector_v2.py:98](/home/bmarti44/stencil-llm/src/stencil/selector_v2.py:98), [multiif_evict.py:211](/home/bmarti44/stencil-llm/scripts/multiif_evict.py:211), and [wave.py:29](/home/bmarti44/stencil-llm/src/stencil/wave.py:29).

   A failed zero-shot projection transfer would not be evidence against a properly trained query-conditioned selector. Define the BM25 tokenizer, sentence boundaries, length normalization, packing, and ordering too. These are experimental policy choices, not incidental plumbing.

17. **HIGH — B3: the 4B fallback cannot run the stated wave-selector arm.** Qwen3-4B has hidden size **2560**. The W0 controller’s projections accept **2048**. This is a dimension error, not merely an uncertain transfer result. See [4B config.json:11](/home/bmarti44/stencil-llm/models/qwen3-4b-hf/config.json:11) and [wave.py:20](/home/bmarti44/stencil-llm/src/stencil/wave.py:20).

   Pre-register a reduced 4B arm set or a separately justified controller. Do not invent a projection after the 1.7B gate fails.

18. **HIGH — B3: the competence pre-gate confuses ability with retention headroom.** `full ≥4/16` is a weak observed floor; adding `full−evicted ≥3/16` requires a favorable retention contrast in a tiny sample. A competent model can fail the second condition because these particular items do not need memory. Conversely, four easy successes do not establish competence on the evaluation distribution.

   Qualify current-task coding and convention compliance with native/full and legal oracle inputs; report retention headroom separately. Split setup/evaluation by independent history or task family, not merely item ID. The local audit explicitly says no relevant 1.7B/4B MemoryCode competence floor was established: [astra-research-blockers.md:43](/home/bmarti44/stencil-llm/results/astra-research-blockers.md:43).

19. **HIGH — B3: N=64 and the headroom readings cannot support the promised decisions.** Eight net oracle wins can mean 8/0 discordance, with one-sided p=.003906, or 36/28, with p=.190866. The same headroom threshold therefore admits very different evidence. Closing half of eight net wins means four net wins; even **4 wins/0 losses gives p=.0625**, failing the unadjusted test, let alone Holm’s first .0167 threshold.

   “Oracle ≈ role → selection has no value” requires a margin and an interval, not a small observed difference. “BM25 closes 50% → retrieval suffices” likewise needs uncertainty. Register expected discordance and attainable power before calling this decisive. The repo already contains the appropriate finite-enumeration approach and shows only 46.15% power at a 10-point effect for one unadjusted N=64 test under one plausible discordance model: [focus-mechanism-composition-v2-astra.md:117](/home/bmarti44/stencil-llm/results/focus-mechanism-composition-v2-astra.md:117).

20. **HIGH — B3/F: three regex-parity fixtures cannot qualify a coding benchmark adapter.** Matching three vendor outputs can reproduce the same false-positive behavior. Cover every retained checker family with compliant examples and discriminating violations, including stale values, conflicting instructions, strings/comments containing required text, and malformed code. Report convention compliance separately from functional correctness. Either measure functionality or explicitly exclude coding competence/usefulness claims. See the existing warning in [astra-research-blockers.md:43](/home/bmarti44/stencil-llm/results/astra-research-blockers.md:43).

21. **HIGH — C/F: this is a substantial new HF implementation, not a checkpoint/config refresh.** The current package selects top-k entries **once at prefill**, ignores the gain head, and applies sustained fixed-dose bias. It does not implement the proposed retention runner or W0’s continuous per-step field. Repointing its checkpoint cannot reproduce Exp 2. Its uploader stages four files and does not publish the proposed encoder/head runtime. See [model.py:96](/home/bmarti44/stencil-llm/deploy/stencil_wave/src/stencil_wave/model.py:96), [model.py:123](/home/bmarti44/stencil-llm/deploy/stencil_wave/src/stencil_wave/model.py:123), and [push_to_hub.py:33](/home/bmarti44/stencil-llm/deploy/stencil_wave/scripts/push_to_hub.py:33).

   Budget separate work for retention semantics, position/cache bookkeeping, classifier loading, public installation/loading, and the optional continuous controller. A useful release needs an executable example from a clean environment, not merely an uploaded model card.

22. **HIGH — C/F: existing parity receipts do not transfer the research result to the proposed package.** The tests explicitly retain strict parity failures as non-strict `xfail`s; some assertions are weakened to agreement where logit margins mathematically guarantee it. They test short trajectories and fixed column groups, not pre-query eviction or the new continuous wave. See [test_parity.py:14](/home/bmarti44/stencil-llm/deploy/stencil_wave/tests/test_parity.py:14).

   Moving from transformers 4.51.0 to 5.16.1 crosses a major version while the attention adapter patches an internal attention dispatch path. Requalify actual retention and controller behavior. Until then, distinguish research-backend benchmark scores from HF-package measurements. W0’s full-prefix recomputation also differs from retaining previously intervened token states in a decoding cache; that semantic choice needs explicit verification.

23. **HIGH — C: the promised historical classifier dataset is not yet reconstructible as claimed.** I executed only the standard-library preprocessing functions from the six-patch reconstruction path. It produces 20,054 rows, but the source counts differ from the frozen manifest:

   | Source | Frozen manifest | Current reconstruction |
   |---|---:|---:|
   | kimi-k3 | 10,555 | 10,576 |
   | kimi-k3-ctx | 4,084 | 4,080 |
   | kimi-k3-scope | 4,560 | 4,543 |

   Matching the total does not establish dataset identity. See [metrics.json:42](/home/bmarti44/stencil-llm/data/classifier/model/ft/metrics.json:42), [finetune_admission_v2.py:66](/home/bmarti44/stencil-llm/scripts/finetune_admission_v2.py:66), and the prior warning in [astra-program-review.md:87](/home/bmarti44/stencil-llm/results/astra-program-review.md:87).

   Recover the actual frozen corpus or publish a clearly labeled reconstruction. Preserve per-row provenance and split identity; do not imply exact training reproducibility from the count alone.

24. **HIGH — C: Brian’s consent and a NOTICE file are not a complete relicensing plan.** The repository contains GPLv2 text, MIT package metadata, and an Apache model-card declaration. Those may represent inconsistent declarations or distinct intended scopes; the plan has not established which. Brian can authorize relicensing only for rights he controls. Imported code, model components, benchmark assets, and contributed material need their own provenance and terms. Qwen’s or MemoryCode’s license does not determine the license of unrelated repository content. See [LICENSE:1](/home/bmarti44/stencil-llm/LICENSE:1), [package pyproject.toml:6](/home/bmarti44/stencil-llm/deploy/stencil_wave/pyproject.toml:6), and [MODEL_CARD.md:4](/home/bmarti44/stencil-llm/deploy/stencil_wave/MODEL_CARD.md:4).

   Resolve ownership and component scope before offering “Apache-2.0 for the whole repo” as a ready decision. Include the classifier’s BAAI-derived encoder in that inventory; its origin is explicit in [finetune_classifier.py:64](/home/bmarti44/stencil-llm/results/quick-checks/finetune_classifier.py:64).

25. **CRITICAL — D3: “p > .3 is INCONCLUSIVE, never FAIL” suppresses strong adverse evidence.** For a one-sided benefit test, a p-value near one can accompany convincing harm. The repo’s competence-bias result has benefit p=.998291 and two-sided p=.022461, with 2 wins versus 11 losses. Your rule would relabel that adverse result inconclusive. See [quick-checks/README.md:514](/home/bmarti44/stencil-llm/results/quick-checks/README.md:514).

   Delete this rule. Distinguish failed practical criteria, demonstrated harm, insufficient evidence, and established equivalence. None is determined by “missed by one item.”

26. **HIGH — D2/D5: unlimited eligibility repair recreates the amendment spiral.** Instrument bugs and substantive eligibility failures are different. FOCUS-3’s unauthorized admissions were failures of the policy being evaluated, not CPU instrumentation accidents. The diagnostic found false admissions in 21/64 episodes and observable effects from removing them. See [diag/RESULTS.md:65](/home/bmarti44/stencil-llm/results/quick-checks/focus3-gate/diag/RESULTS.md:65).

   Permit bounded technical repair without spending a scientific trial, but count refits, policy changes, and model selection against an explicit development budget. Authoring repair must occur before scientific outcomes are exposed and must preserve the construct and coverage. The already accepted source-construction design has exactly such a bounded correction mechanism; retain its principles rather than replacing them with unrestricted repair: [PREPARATION.md:9](/home/bmarti44/stencil-llm/results/source-replay-preparation-v2/PREPARATION.md:9).

27. **HIGH — D6/F: the process diet removes essential scientific contracts.** Unit/test/N/cost/readings are insufficient without data lineage, complete arm definitions, frozen selection rules, missingness/timeouts, intervention budgets, artifact schema, and stopping behavior. These omissions are already causing the defects above. The repo’s two contamination incidents and lost per-work records directly justify retaining those requirements. See [AGENTS.md:63](/home/bmarti44/stencil-llm/AGENTS.md:63) and [AGENTS.md:92](/home/bmarti44/stencil-llm/AGENTS.md:92).

   Keep a short registration, but make it sufficient to implement the experiment without new scientific choices. Allow focused review of substantive implementation changes and repairs; “never per iteration” must not prohibit checking a changed intervention or scorer.

28. **HIGH — A/C/D: the proposed cross-cutting conclusion is false as written, and the retirement list loses useful distinctions.** C2 compares two pin-selection policies; it says nothing about prose versus structure. The internal-wave report itself gives wave 44.8 versus reinsertion 43.0. W3a subsequently reports a clean-format positive result, even though W3b’s override/readout gates failed. See [multiif_evict.py:590](/home/bmarti44/stencil-llm/scripts/multiif_evict.py:590), [internal-wave-report.md:6](/home/bmarti44/stencil-llm/results/internal-wave-report.md:6), and [WORKLOG.md:1338](/home/bmarti44/stencil-llm/WORKLOG.md:1338).

   Remove “prose beats every mechanism” as a universal conclusion. Preserve the qualified W3a result and the informative W3b readout failure. Parking S3, GPT-2, and the custom authoring pipeline is reasonable prioritization; presenting untested or narrowly tested families as scientifically extinguished is not.

29. **HIGH — E/B: fixed free-memory thresholds do not establish feasibility.** The 1.7B implementation explicitly materializes fp32 attention and full vocabulary logits. At 6,144 tokens, one `[16,T,T]` attention tensor is **2.25 GiB**, and `[T,151936]` fp32 logits are **3.48 GiB**. Those exclude simultaneously live intermediates, weights, loading/conversion peaks, cache, allocator reserve, and the peer process. The older W0 smoke used only 397 tokens. See [qwen3.py:327](/home/bmarti44/stencil-llm/src/stencil/qwen3.py:327), [qwen3.py:445](/home/bmarti44/stencil-llm/src/stencil/qwen3.py:445), and [w0_train.py:174](/home/bmarti44/stencil-llm/scripts/w0_train.py:174).

   Do not multiply inference attention memory by all layers indiscriminately, but do measure the actual peak. Register maximum-length pilots for training, long-history prefill, and package parity. Twenty-six GB free is not a demonstrated budget for every proposed path.

30. **HIGH — E: coordination and deadline guarantees are not implemented by these rules.** Two sessions can both observe free resources and launch before either sees a message. Use one shared reservation mechanism with an atomic acquire/release protocol. The reused Multi-IF entrypoint’s current guard accepts only an empty GPU or one explicitly declared owner; it does not implement “foreign resident server plus one cooperating job.” See [multiif_evict.py:934](/home/bmarti44/stencil-llm/scripts/multiif_evict.py:934) and [determinism.py:34](/home/bmarti44/stencil-llm/src/stencil/determinism.py:34).

   `--deadline 300` is checked after prefill, inside decoding; it is not a hard prefill/process deadline. W0 training and the old seal lack the proposed chunk/deadline interface. Per-session atomic output can still lose a session’s many completed arm/work generations. Save completed work-arm records and stop starting work before the reservation expires.

31. **MEDIUM — B/E: the 7.8-hour estimate is a planning guess presented as a measured program.** The old Multi-IF run spent **14.916 hours across six arms**, plus 5.934 hours generating history. Dividing arm time by six gives 2.486 hours, but does not measure echo-only latency; arm output lengths vary substantially. Three fixed 303-conversation chunks provide essentially no allowance around a 50-minute target.

   W0 training actually took **6 min 9 sec**, reasonably close to the stated 6.5-minute estimate; the 85.6-minute seal estimate is supported by recorded timestamps. Those do not price LoRA qualification, the extra causal controls, MemoryCode adaptation, a 4B retry, shared-device contention, or HF requalification. The earlier MemoryCode audit estimated 4–8 author-hours and a broad 5–15 GPU-hour range—not a measurement either. See [w0-train-status.txt:1](/home/bmarti44/stencil-llm/results/logs/w0-train-status.txt:1), [WORKLOG.md:1252](/home/bmarti44/stencil-llm/WORKLOG.md:1252), and [astra-research-blockers.md:51](/home/bmarti44/stencil-llm/results/astra-research-blockers.md:51).

   Make a measured pilot and revised budget the launch prerequisite, not an optional afterthought.

32. **HIGH — F: the verification list misses the failure modes and contains a failing repository-wide gate.** I ran Ruff without cache writes: **1,501 findings**. `make gate-0` runs Ruff after pytest, so `testpaths` alone cannot make it pass. See [Makefile:8](/home/bmarti44/stencil-llm/Makefile:8) and [pyproject.toml:28](/home/bmarti44/stencil-llm/pyproject.toml:28).

   The proposed tests also omit statistical verdict boundaries, seed-block exclusion, comment qualification, budget packing, oracle isolation, historical baseline replay, and interruption/resume consistency. A count of 911 tracked files establishes neither the right identities nor complete arm coverage. Verify manifest-bound identities and schemas. Scope lint to changed code or explicitly budget the existing debt.

33. **MEDIUM — C/F: the hygiene prescription will not meet its own final check.** The proposed ignores cover `head.safetensors` but leave nested encoder weights in `admission-v2/seed*/encoder`, `ft-v3/seed*/encoder`, and `relations-v3/seed*/encoder` unignored. Existing patterns cover only shallower encoder paths or selected subtrees; see [.gitignore:243](/home/bmarti44/stencil-llm/.gitignore:243).

   `b3-ce-s0.pt` and `w3a-audit.json` are already tracked. The source-replay four-file change remains uncommitted. Resolve its disposition before broad hygiene work, and use explicit pathspecs as [AGENTS.md:33](/home/bmarti44/stencil-llm/AGENTS.md:33) requires.

34. **MEDIUM — B2/F: generated code is executed directly on the host.** `score_work` writes the complete generated program to a temporary file and executes it with the normal Python interpreter. Parsing a function does not exclude other top-level code. The five-second timeout is not a sandbox, and the temporary files are created with `delete=False`. See [t2_runner.py:59](/home/bmarti44/stencil-llm/src/stencil/t2_runner.py:59).

   Qualify the existing sandboxed execution path before extending this approach to public coding inputs; keep scorer changes separate from historical outcome claims.

Additional factual corrections and checks:

| Claim | Verification |
|---|---|
| “Single-turn IFEval, n=1024, +0.39, p=.389” | **HIGH: wrong dataset attribution.** It is synthetic `data/b3/conf-v45.jsonl`. Both code and an explicit correction say so: [b3_deficit_conf.py:72](/home/bmarti44/stencil-llm/scripts/b3_deficit_conf.py:72), [WORKLOG.md:2302](/home/bmarti44/stencil-llm/WORKLOG.md:2302). |
| Multi-IF headline rates and N | Recomputed from all 909 saved records: 2,276 aged constraints; full 65.158%, evicted 16.652%, classifier pins 57.206%, pins+echo 59.227%, role pins 60.501%. |
| C2 “3.5 points” | Correct **conversation-mean** difference; pooled constraint difference is about 3.30 points. Keep estimands labeled. |
| C1/C3 p-values | Recomputed as approximately `3.6933e-85` and `1.5875e-65` under the historical conversation-level method. The saved summary rounds them to zero; shared-source dependence remains finding 10. |
| 911 tracked evidence files | Correct. All `results/gpt2/` files are untracked. |
| W0/classifier hashes | Both cited prefixes match actual bytes: `eab4831f…`, `22328135…`. Encoder size is 133,462,104 bytes, approximately 127.3 MiB. |
| SELECTOR 3.9→88.3 | Saved final artifact contains 5/128 versus 113/128. The 84% reinsertion comparison comes from another experiment block. |
| Deployment “four months stale” | **LOW: false.** Its last commit is September 1, 2026—ten days before this plan. |
| 215 unpushed commits | Correct against the configured upstream. |
| 30B directory “57 GB” | Approximately 56.89 GiB, or 61.08 decimal GB. Label units. |
| Two listed GPT-2 checkpoints “~23 MB” | **LOW: wrong total.** Together they are 15,763,150 bytes. |
| PID 4110069 / 26 GB free | **LOW: stale snapshot.** During this review the PID was absent and `free -g` reported 114 available. No GPU workload was launched. |
| 2,142 collected tests; 246 reviews / 85% | Not independently certified here. There are 181 Python experiment scripts; the review-document count needs a stated classification rule. Test collection is not evidence that tests pass. |

**Minimum edits required for acceptance:**

1. Replace A’s claim with one the actual intervention can identify; correct SpotLight, IFEval, and “prose beats everything” wording.
2. Repair and qualify the comment scorer, preserve the historical qualification, and reserve unused evaluation seeds.
3. Redesign Exp 2 with matched causal ablations, a fair frozen LoRA protocol, explicit estimands, intervals, and exhaustive verdicts. Preserve the known competence-harm disclosures.
4. Make the independently specified shipping reminder arm mandatory in Exp 1; account for shared source prompts and verify historical/new-runtime compatibility.
5. Write a complete MemoryCode adapter contract before authorizing its GPU budget: native-versus-derived protocol, independent split units, label isolation, legal oracle packing, checker qualification, power, and a viable 4B fallback.
6. Delete D3. Retain bounded development/repair budgets, lineage, freezes, complete records, and review of substantive changes.
7. Replace fixed resource guesses with maximum-length pilots, an atomic shared reservation, enforceable stopping, and resumable work-arm records.
8. Separate research results from HF implementation claims; qualify the new package end to end, resolve component licenses and corpus provenance, and replace the unbounded hygiene gate with a concrete scoped check.

Review used source reads, saved-result arithmetic, standard-library checks, and cache-disabled lint. No files were modified and no model, GPU workload, or network process was launched. Upstream MemoryCode contents and external bibliographic/license claims remain unverified beyond the local reports; they must not be treated as cleared by this review.
