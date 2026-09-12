D: NOT DISPROVED — I found prior work on every component and several related interactions, but no demonstration of the specific benefit of matching live session rules to governed units within one completion.
X: NOT DISPROVED — verified-example reuse has strong predecessors and contrary evidence, but I found no decisive test of its proposed advantage under session-rule updates.

I accept the owner’s reading of “non-meaningless recombination.” A previously undemonstrated, theoretically motivated interaction can justify a research direction without a new primitive or an already completed experiment. My round-1 language should not be interpreted as requiring results before proposing the experiment.

**D survives as a research direction, but its current registration does not test the contribution that justifies it.** Several supporting claims are incorrect, H2 is not defensible as written, and section 4 explicitly permits success when all interactions are null. These are correctable defects; they do not establish that the underlying interaction is absent.

I re-read the requested reports, registration, governing-plan sections, and relevant package/checker code. I did not read `data/bench/`, write files, or run models. The literature search is current through September 12, 2026; sources identified only as arXiv papers below are preprints.

**The novelty claim needs substantial narrowing.**

In this table, “partial” means a predecessor implements part of the proposal’s precise definition. “Related” means it measures an adjacent effect, not the exact registered interaction.

| Predecessor | T1: session-derived live register | T2: triggered insertion/rollback | D: live rules at governed units within one completion | H1–H3 coverage |
|---|---|---|---|---|
| [TRACE, 2026](https://arxiv.org/html/2606.13174v1) | Substantial: corrections become rules with update/supersession operations | Enforcement through agent/runtime hooks, not the specified token insertion | No exact match found | No exact H1–H3 measurement |
| [Answer Engineering, 2026](https://arxiv.org/html/2606.21121v1) | No session-maintenance mechanism | Substantial: scoped triggers and local trajectory edits | No session-derived code conventions | No exact H1–H3 measurement |
| [Thinking Intervention, 2025](https://arxiv.org/html/2503.24370v3) | No | Insertion; not the full proposed parser/KV mechanism | No | Reminder-location comparisons related to H1 |
| [Can We Steer Reasoning Direction by Thinking Intervention?, Findings EMNLP 2025](https://aclanthology.org/2025.findings-emnlp.209/) | No | Dynamic trigger-based insertion/replacement | No | **Direct intervention-timing and repetition measurements**, adjacent to H1 |
| [SafeRemind, 2026](https://arxiv.org/html/2601.03662v1) | No | Newline/entropy-triggered reminders | No | Prompt/thinking/answer placement and reminder-count ablations; reminder count is not H3’s live-rule count |
| [IterGen, ICLR 2025](https://arxiv.org/abs/2410.07295), [Hydra, 2026](https://arxiv.org/html/2605.15238v1) | No | Substantial local checking, rollback, and continuation | No live-session convention routing | No exact H1–H3; Hydra already places diagnostic comments before repair continuations |
| [ZORO, 2026](https://arxiv.org/html/2604.15625v2) | Partial: rules develop through situated feedback | Agent-step anchoring, not arbitrary token-stream insertion | Close at plan-step granularity, not within one completion | Demonstrates a combined rule-support system, not the proposed interactions |
| [Selective Prompt Anchoring, ICML 2025](https://proceedings.mlr.press/v267/tian25a.html) | No | Different decoding intervention: contrasts original and masked-prompt logits | No | **Code-generation attention dilution with output progression**; no governed-unit compliance interaction |
| [Did You Forget What I Asked?, 2026](https://arxiv.org/html/2603.23530v1) | No | Before-generation reminders | No | **Reminder × instruction-count measurements already exist**; type/distance comparisons are related to H1/H2 |
| [Order Matters, Findings ACL 2025](https://aclanthology.org/2025.findings-acl.646/), [MOSAIC, 2026](https://arxiv.org/html/2601.18554v1) | No | Prompt ordering, not insertion | No | Constraint-position, type, and count measurements; not D’s delivery policy |

Two omissions matter particularly.

First, **Thinking Intervention is not adequately described as fixed text at a fixed trigger**. Its EMNLP follow-up compares seven insertion stages, static and entity-triggered locations, first versus last occurrences, and single versus repeated interventions. Earlier intervention often wins; intervening repeatedly is not uniformly best. A general claim that “when and where we intervene inside generation has not been measured” is already false. [Findings EMNLP 2025](https://aclanthology.org/2025.findings-emnlp.209/)

Second, **Selective Prompt Anchoring already addresses the proposed transformer-side motivation specifically in code generation**. It measures declining attention to the prompt as code accumulates and counters this through decoding-time anchoring. Its reported maximum Pass@1 improvement is 12.9%. That does not establish D’s interaction, but it removes “code instructions lose influence during generation, so strengthen them during decoding” as the new contribution. The paper and [implementation](https://github.com/magic-YuanTian/Selective-Prompt-Anchoring) belong in the proposal’s central comparison set. [ICML 2025](https://proceedings.mlr.press/v267/tian25a.html)

I also checked the product-hook interpretation. Claude Code’s documented context injection occurs at lifecycle events such as prompt submission and tool execution. Cursor’s `afterAgentThought` concerns a completed thought block and does not expose the proposed function-start insertion interface. These are not evidence of arbitrary token-stream rule injection inside a completion. Conversely, calling them “mid-generation hooks” without specifying the boundary would exaggerate D’s distinction. [Claude Code hooks](https://code.claude.com/docs/en/hooks-guide), [Cursor hooks](https://prod.cursor.com/docs/hooks)

Dynamic retrieval during generation is also established: FLARE anticipates the next sentence and retrieves supporting information; DRAGIN decides when and what to retrieve during generation. Neither supplies the session-lifecycle-plus-code-unit experiment, but broad claims about delivering relevant information at its point of use are unavailable. [FLARE, EMNLP 2023](https://aclanthology.org/2023.emnlp-main.495/), [DRAGIN, ACL 2024](https://aclanthology.org/2024.acl-long.702/)

What remains plausibly new is narrower:

> Matching a currently applicable session rule to its governed code unit provides an advantage over equally repeated, equally formatted reminders, and that advantage changes with within-output distance or irrelevant-rule load.

That is a substantive interaction to investigate. Merely outperforming a once-before reminder does not establish it.

**The prospective-memory theory supports a possibility, not H1–H3 as stated.**

In the multiprocess framework, focality concerns whether the ongoing task processes the features needed to recognize the prospective-memory cue. It is not defined as physical adjacency of the complete instruction to the upcoming action. Supplying the full instruction again also changes external memory support, not just cue focality. The framework permits spontaneous retrieval; it does not entail a zero forgetting slope, a universal advantage for positive requirements, or a benefit increasing monotonically with the number of intentions. [McDaniel and Einstein, 2000](https://doi.org/10.1002/acp.775)

Anderson, Strube, and McDaniel’s meta-analysis included **289 effects from 91 studies and 11,639 participants**. Its focal/nonfocal contrast concerns costs to the ongoing task: approximately **d = 0.24 versus 0.67**, not corresponding gains in intention execution. Focal tasks can still incur costs, and cue-number results do not support a blanket “more intentions makes focal delivery increasingly advantageous” law. These findings motivate a qualified hypothesis; they do not validate the proposal’s mapping. [*Psychological Bulletin*, 2019](https://bpb-us-w2.wpmucdn.com/sites.wustl.edu/dist/e/969/files/2019/09/Anderson-Strube-McDaniel-2019.pdf)

The eight requested LLM papers give a mixed picture:

| Paper | What it actually establishes | Consequence for D |
|---|---|---|
| [2603.23530](https://arxiv.org/html/2603.23530v1) | Tests reminders across instruction counts **1, 2, 3, 5** and mathematical loads. Reminder effects range from **+25 to −20 points** in particular cells. Avoidance constraints are relatively robust in this task construction. | H3’s broad reminder-by-count interaction is already measured and is not uniformly positive. Supports testing conditional effects, not a monotonic sign guarantee. |
| [2604.20911](https://arxiv.org/html/2604.20911v1) | In one Mistral condition, no-bullets adherence falls **73% → 33% → 20%** at turns 5, 16, 25. Several positive markers persist, but other prohibitions also remain stable. Generated history can reinforce visible positive markers. | Opposes H2’s universal ordering. Does not show that prohibition polarity itself causes decay or that reinjection fixes it. |
| [2605.10039](https://arxiv.org/abs/2605.10039) | **1,650 sessions, 16,050 functions**; exploratory function-order association **OR 0.944**. Patterns vary by task and are nonmonotonic; one trajectory falls and then recovers substantially. | Motivates H1, but this is within-session evidence across agent activity, not an experiment on unit position within one completion. A flat focal slope does not follow. |
| [2606.23459](https://arxiv.org/html/2606.23459v1) | Retrospective retrieval remains strong while prospective behavior deteriorates. Explicit anchoring improves state tracking, including **57.4% → 100%**, but can worsen false triggering. | Supports an access–execution distinction. Its positive/negative trigger cases mean trigger present/absent, not “do”/“do not” instruction polarity. It does not validate H2. |
| [2608.02639](https://arxiv.org/html/2608.02639v1) | Large stacking losses, but **15 of 231 rule pairs are logically incompatible**. Compilation gives model-dependent changes, including **+11 points** and **−1.2 points**. | Placement cannot resolve contradictory rules governing the same unit. H3 needs satisfiability and local-load controls. |
| [2510.05381](https://arxiv.org/html/2510.05381v1) | Context length can hurt even when relevant evidence remains adjacent to the question. Long whitespace contexts produce substantial losses in studied models. | Directly undermines “a rule 1–3 lines above the unit does not compete.” Adjacency does not remove accumulated-context effects. The paper does not quantify the expected effect at this 4K setup. |
| [2604.11088](https://arxiv.org/html/2604.11088v1) | On **58 tasks**, curated and random rules both reach **63.8%**, versus **50%** baseline, but individual comparisons are not significant. Rule-arm omnibus **p = .697**. Counts up to 50 do not show the other paper’s collapse. | Equality is not established by nonsignificance. Outcomes are functional task success, not rule compliance. Its polarity observations cannot establish H2’s causal interaction. |
| [2607.16019](https://arxiv.org/html/2607.16019v1) | A ledger comparison gives **+18.2 points**, but after matching rendering the residual is **+2.5 points, CI [−0.5, 5.7]**. Some other lifecycle contrasts remain beneficial. | Strong warning about presentation confounds. It does not establish that rule content generally matters less than placement, nor predict D’s sign. |

The commission/omission terminology is not stable enough to carry H2. It mixes at least four distinctions:

- A positive instruction versus a prohibition.
- Failure to perform an intended action versus performance of an unwanted action.
- A present trigger versus an absent trigger.
- A one-time terminal action versus a requirement with many opportunities to fail.

These are different experimental factors. A prohibition such as avoiding a decorator at each function has a clear governed-unit cue. An “include” requirement can become easier through visible repetition in generated history. Neither belongs to a universal cue-free or cue-dependent category.

There is also a local specification problem: **unit family does not identify polarity**. The checker explicitly supports both “Always include” and “Never include” instructions. Its taxonomy cannot establish that every convention in the proposed cohort is a commission rule. And section 4’s `arm × unit family` test is not a test of the stated commission-versus-avoidance prediction. [Checker boolean branch](/home/bmarti44/stencil-llm/vendor/memorycode/code/evaluate_model_output.py:36)

My resulting assessment is:

- **H1:** plausible after changing “flat” to “less adverse,” with suitable controls.
- **H2:** unsupported as a directional prediction and misregistered.
- **H3:** plausible for irrelevant, satisfiable rules routed away from a unit; not for arbitrary live-rule counts.

An additional H3 problem is that **previously inserted comments remain in the context**. Showing 1–3 fresh rules at the current unit does not reduce the total retained rule text to 1–3. Focal delivery can accumulate more rule tokens than the once-before arm.

**Several measurement protections are good, but they do not identify placement.**

| Issue | What section 4 already removes | What remains |
|---|---|---|
| Different rule identities | Holding the register and rule text fixed removes one major information difference. | Focal repeats and selects rules; before presents all once. This changes dose, local relevance, format, and assistant-prefix content simultaneously. |
| Injected text directly earning credit | Exact span recording and stripping can prevent this. | This must survive rollback and offset changes. Generated copies remain model output; stripping does not remove their causal influence. |
| Changed continuation after comments | Nothing—and changed continuation is the intended causal pathway. | A gain might come from comment-induced planning or code priming rather than governed-unit alignment. An equally formatted, equally repeated insertion control is needed. |
| Token accounting | Reporting prompt, inserted, and generated tokens makes costs visible. | Reporting is not matching. Different retained histories, generation allowances, and truncation can still determine the result. |
| False triggers | Replay K2 addresses occurrences in the stored outputs. | It does not establish coverage on changed continuations, incomplete syntax, decorators, strings, examples, or newly generated structures. |
| Missing structures | Existing `fraction_required` uses a fixed requirement denominator and penalizes missing required structures. | Per-unit H1 can still exclude missing late units and compare different structures across arms. |
| Outcome exposure | Reserving unused generations avoids reusing the 139 known outcome pairs as confirmation. | Remaining items are not wholly unseen, and the reserve accounting must be corrected. |
| Register errors | Both arms sharing a register prevents differing register quality from confounding their comparison. | It does not establish that either arm receives the correct current rules, or that T1 contributes useful lifecycle behavior. |

Three concrete corrections are particularly important.

**The token arithmetic is wrong.**

\[
2{,}560+1{,}536=4{,}096.
\]

That leaves **zero tokens for inserted comments** at full allocation. Either inserted tokens consume the 1,536 allowance, reducing model-authored output, or the sequence exceeds the claimed limit. Registration needs an explicit constraint:

\[
P+I+G\leq 4{,}096,
\]

plus separate accounting for discarded and regenerated tokens. Prompt prefill, forced-token processing, and autoregressive generation also have different costs. Equal token totals alone do not imply equal latency.

Furthermore, if `before` makes room for reminders by evicting additional history while `focal` retains that history, the treatment changes accessible task information. Freeze the same history bytes across the relevant comparisons.

**The checker is not exclusively AST-based.**

Comments are extracted with `re.findall(r"#.*", python_text_code)`, which can also match hashes inside strings. The visitors explicitly handle `FunctionDef` and `Import`, but do not provide equivalent dedicated handling for `AsyncFunctionDef` and `ImportFrom`. Annotation extraction collects existing annotations; it is not itself a universal requirement that every argument be annotated. These distinctions matter when the intervention changes coding style or syntax families. [Comment extraction](/home/bmarti44/stencil-llm/vendor/memorycode/code/extract_objects.py:182), [function visitor](/home/bmarti44/stencil-llm/vendor/memorycode/code/extract_objects.py:118), [annotation extraction](/home/bmarti44/stencil-llm/vendor/memorycode/code/extract_objects.py:49)

The existing structure requirements also come from a query-word heuristic, not a complete semantic specification of the requested program. That limitation is inherited, but becomes more consequential when claiming per-unit effects. [Requirement construction](/home/bmarti44/stencil-llm/src/stencil/memorycode.py:315)

**Generated unit index is a treatment-dependent variable.**

Focal delivery may change how many functions exist, their order, their lengths, or whether the model reaches them before truncation. Comparing compliance at “function 4” can therefore compare different tasks and different surviving outputs. Item random effects do not repair that selection.

Whole-family checks also create an opportunity-count effect: requiring every object to comply becomes harder as more objects are generated, even if each object’s compliance probability is constant. H1 needs identifiable, predeclared units or a controlled-prefix experiment, not merely a mixed model over whatever units each arm happens to produce.

**The particular setup has several credible failure mechanisms.**

- **T1 reintroduces a previously observed weak link.** Exp 4C used role-based evicted mentor sentences, not the proposed classifier-plus-relations lifecycle register. The governing plan records register overflow on **138/144 LONG items** and no applied relations on SETUP. A typing test on gold instructions does not qualify admission, retirement, supersession, or overflow handling. [Governing-plan diagnosis](/home/bmarti44/stencil-llm/plan/BACK-ON-TRACK-PLAN.md:61)

- **“Rollback to the current line start” is not necessarily early enough.** Decorators precede `def`. A function-name constraint must be delivered before the name is chosen. Assignment recognition may require reaching `=`, after an arbitrarily long left-hand side. The claimed **≤10-token rollback bound** has no general syntactic basis.

- **Trigger coverage and instruction execution are separate.** A model can receive the correct comment and still produce the wrong docstring, annotation, identifier, or body. The broad `any` category also lacks a well-defined governed unit; repeated delivery can become indiscriminate prompting.

- **Local rules can conflict or require global knowledge.** A function may simultaneously be subject to class, method, annotation, decorator, and content requirements. “Use this naming style” is much easier to localize than “ensure this method coordinates correctly with the class state.”

- **Small-model success is possible, but comment insertion is not established as sufficient.** Thinking Intervention’s R1-Qwen-7B result improves from **60.99% with a reminder to 62.85% with reminder plus thinking intervention**—a modest incremental gain. Think Anywhere reports that prompting-only or SFT variants can underperform the base model; its stronger results require additional training. That is evidence against assuming a new insertion format is automatically understood. [Thinking Intervention](https://arxiv.org/html/2503.24370v3), [Think Anywhere, 2026](https://arxiv.org/html/2603.29957v2)

- **The old preamble observation does not diagnose the entire failure.** Restating a guideline is evidence of some access to it. It does not establish correct scope resolution, conflict resolution, operational understanding, or ability to execute it. Nor does capped-versus-uncapped performance identify the causal effect of the cap; those are different subsets of outputs.

- **The cost estimate omits substantial uncertainty.** Hydra demonstrates advantages over repair, but explicitly reconstructs a reusable prefix and relies on inference caching rather than providing the proposal’s exact explicit-KV implementation. Qualification must measure the actual path. Four arms also cost more than the two-arm “pair” shorthand suggests. [Hydra](https://arxiv.org/html/2605.15238v1)

My expectation is therefore a **credible chance of a narrow local-compliance effect**, with much weaker grounds for a large end-to-end improvement on this exact setup. I would not assign a numerical probability from these heterogeneous studies.

**Usefulness depends on beating an appropriate alternative.**

The closest systems report effects large enough to make a small uncontrolled improvement unpersuasive:

| System | Reported result | What D must distinguish |
|---|---|---|
| [TRACE, 2026](https://arxiv.org/html/2606.13174v1) | ClawArena violations **100% → 37.6%** in distribution and **2%** out of distribution; task success broadly preserved | Learning session corrections and enforcing them already has demonstrated utility. These benchmark-specific rates are not transferable forecasts. |
| [ZORO, 2026](https://arxiv.org/html/2604.15625v2) | Rule-following measure approximately **0.51 → 0.80** from no support to full support; feature-completion gains were not significant | A user-visible benefit beyond plan anchoring and evidence requirements |
| [Answer Engineering, 2026](https://arxiv.org/html/2606.21121v1) | Target-condition adherence **25.1% → 83.5%**, with **2.78×** slowdown; contrastive condition **58.9% → 77.9%**, **1.33×** slowdown | Reliability must be assessed together with cost and task-specific effects |
| [SafeRemind, 2026](https://arxiv.org/html/2601.03662v1) | Dynamic reminders preserve much more math performance than prompt-level safety reminders, but benign refusal rises **4.4% → 19.2%** | Better compliance can coexist with substantial unwanted behavior |

A demonstrated H1 could change practice if it identifies when a single reminder becomes inadequate and when local delivery beats periodic repetition. H3 could justify routing only relevant rules as a register grows. H2 could guide polarity-specific handling—but the present evidence does not support that policy.

For executable style constraints, a linter or checker plus repair is an essential practical comparator. D may save repair latency or avoid whole-output regeneration. If it merely moves the same work into many decode interruptions, its engineering complexity may not pay off.

As a **proposed practical threshold, not a definition of scientific evidence**, I would look for either:

- Roughly **10 absolute points** of improvement in required-rule compliance over `before`, accompanied by an alignment effect and preserved functional performance; or
- Compliance comparable to checker-plus-repair with a material cost advantage—for example **25% lower latency**, under a registered compliance noninferiority margin.

An observed two-point gain in a family-average score, with almost no wholly compliant programs and unknown functionality, would not establish substantial practical value. A smaller interaction could still be scientifically real.

**The cross-domain evidence is useful, but the strongest analogues are more specific than “human memory works this way.”**

- **Spatial and temporal contiguity provide a stronger H1/H3 analogue.** Ginns’s meta-analysis covers **50 effects and 2,375 students**, with an overall **d = 0.85, CI [0.68, 1.02]**. Integrating related information is particularly helpful with complex material. This supports testing whether aligning a rule with the code it constrains reduces integration demands. It does not supply an LLM effect size or the commission prediction. [*Learning and Instruction*, 2006](https://doi.org/10.1016/j.learninstruc.2006.10.001)

- **Aviation challenge-response is not synonymous with item-by-item instructions before acting.** The classic distinction includes performing a familiar configuration and then checking its actual state. That is closer to verification and repair than to inserting a reminder before every action. [Degani and Wiener, NASA report, 1990](https://www.interruptions.net/literature/Degani-Checklist.pdf)

- **The surgical literature supplies a direct caution against the proposed analogy.** Low and colleagues found that merely making checklists available at the point of care did not produce reliable use. Teams were treating them as read/do lists, which conflicted with individual workflow. Training emphasized completing the work and then performing challenge-response verification. Execution improved with coaching; checks typically took **8–10 seconds**. This was a quality-improvement package, not an isolated randomized placement effect. [*Pediatric Anesthesia*, 2013](https://doi.org/10.1111/pan.12121)

- **Point-of-care decision support generally improves processes more than outcomes.** Across **122 analyzable trials involving 1,203,053 patients**, desired care increased **5.8 points, CI [4.0, 7.6]**, with substantial heterogeneity. In trials reporting clinical endpoints, the median improvement was **0.3 points**. For D, the analogous distinction is convention compliance versus useful, correct software. [Kwan et al., *BMJ*, 2020](https://pmc.ncbi.nlm.nih.gov/articles/7495041/)

- **Just-in-time training has positive evidence, but often includes rehearsal and feedback.** A randomized intubation study reported first-attempt success of **91.4% versus 81.6%** with just-in-time coaching. It does not show that passive adjacent text produces the same benefit. [*BMJ*, 2024](https://pubmed.ncbi.nlm.nih.gov/39681397/)

- **Structural priming supports X’s mechanism, not its superiority.** Transformer language models can reproduce structural priming effects, including cross-linguistic effects. This makes local examples a credible influence on code form. It does not establish faithful application of a revised rule or preservation of semantics. [Sinclair et al., *TACL*, 2022](https://aclanthology.org/2022.tacl-1.60/), [Michaelov et al., EMNLP 2023](https://aclanthology.org/2023.emnlp-main.227/)

- **Adaptive-intervention research offers a better design principle:** intervention availability, receptivity, and burden must be measured; sometimes the appropriate action is no intervention. That argues against treating “fire at every eligible unit” as automatically optimal. Micro-randomized designs also offer a useful analogue for testing proximal effects at eligible decision points. [Nahum-Shani et al., *Annals of Behavioral Medicine*, 2018](https://pmc.ncbi.nlm.nih.gov/articles/PMC5364076/)

**X survives a direct attack, but is less well justified than D.**

Successful-trajectory reuse is already effective. A NeurIPS 2025 study reports that even simple reuse improves ALFWorld **73% → 89%**, Wordcraft **55% → 64%**, and InterCode-SQL **75% → 79%**. Self-generated demonstrations are older still. Thus “reuse verified successful material as examples” is unavailable as the contribution; current-rule verification under updates must do substantive work. [Sarukkai et al., NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/5d1f02132ef51602adf07000ca5b6138-Abstract-Conference.html), [SG-ICL, 2022](https://arxiv.org/abs/2206.08082)

The strongest recent contrary result is **LLMs Learn Better In-Context from Rules than from Examples**, posted September 2, 2026. Across five task families and models including Qwen3, rules generally outperform examples; adding examples or increasing their number does not consistently help. This directly challenges X’s broad superiority premise. It does **not** settle token-matched local code conventions under session updates, so it is not a decisive disproof of X’s scoped interaction. [2026 preprint](https://arxiv.org/html/2609.03213v1)

X also has unresolved implementation assumptions:

- Typing a rule does not provide a verifier for it.
- An example verified under the previous rule version may violate the current version.
- Immediately after an update, there may be **no compliant example in the session**.
- A positive example usually underdetermines prohibitions, exceptions, and quantified requirements.
- Selecting only sessions with usable examples can manufacture an apparent advantage.
- Copying a compliant structure can also copy irrelevant identifiers, assumptions, or defects.

To demonstrate the claimed lifecycle contribution, X would need current-version verification versus stale or unverified selection, update versus no-update cases, and explicit accounting for missing exemplars. Prose-versus-example alone does not identify the novel part. Its proposed commission interaction inherits H2’s terminology problem.

**The minimum section-4 changes are the following.**

1. **Make the interaction a success condition.**  
   Keep `focal − before` as an end-to-end policy estimand, but it cannot establish the proposed scientific contribution by itself. Select a primary interaction before evaluation—preferably H1’s attenuation of distance effects—and require evidence for it. If several interactions can establish success, register multiplicity control. Replace “flat slope” with “less adverse slope”; claiming flatness requires an equivalence margin.

2. **Add a control that matches repetition and comment presentation.**  
   At minimum, compare `before`, `focal`, and reminders repeated at predeclared safe locations without governed-unit alignment. Match rule identities, copy counts, comment format, and budget in the mechanism experiment. When natural continuations make exact matching impossible, use a separate controlled-prefix experiment and label its estimand accordingly. The unrestricted `focal − before` comparison then measures the total delivery policy, including its repetition effects.

3. **Use predeclared units for H1 and manipulated load for H3.**  
   Score named or otherwise identifiable required units, count missing units as failures, and retain dialogue-level clustering. For H3, distinguish total register size, rules relevant to the current unit, incompatible rules, and accumulated inserted tokens. Vary irrelevant-rule load independently where possible. An observational `arm × k` term over heterogeneous dialogues is insufficient to establish the proposed load mechanism.

4. **Remove H2 from confirmation unless it is actually instantiated.**  
   Unit family is not polarity. Either construct independently specified positive/prohibitive conditions with comparable opportunities and difficulty, or report polarity exploratorily. Do not treat a null function-versus-class interaction as a result about commission versus avoidance.

5. **Repair the resource contract before timing.**  
   Freeze identical retained history, explicitly allocate \(P+I+G\leq4096\), and record forced, generated, discarded, and regenerated tokens separately. Register what happens when insertion space is exhausted. Qualify active cache reuse against recomputing the same edited prefix; no-trigger parity does not test the active intervention path.

6. **Qualify the complete current-rule pipeline and restrict coverage claims.**  
   Add admission accuracy, current-rule recall, false active rules, retired-rule resurrection, and overflow reporting. K1 on gold instructions is insufficient. Replace “every unit” with a precisely supported syntax domain, tested on independent fixtures covering decorators, asynchronous functions, multiline headers, assignments, nested scopes, strings, and examples. A 95% replay recall threshold is an empirical gate, not a coverage guarantee.

7. **Audit the measurement contract and include a functional outcome.**  
   Preserve the existing fixed-denominator score and structure penalties. Add unit-level scoring with documented quantifiers and supported syntax. Verify stripping after rollback. Include executable task checks on a suitable subset and a checker-plus-repair comparator if claiming practical advantage. If `both` is to ship, it must pass the relevant gates itself; a focal win does not qualify a descriptive arm.

8. **Correct the cohort description and choose N from precision and power.**  
   Exp 4C used **139 of 196** non-SETUP candidates. The remaining **57 already include the unused reserve**; another reserve cannot be presumed. Their metadata and labels had previously been inspected, although their model outcomes had not been generated. Describe them as generation-unseen, not wholly unseen. [Exp 4C lineage](/home/bmarti44/stencil-llm/results/memorycode-long/REGISTRATION-4C.md:24)

   Using the old paired SD **0.1259**, an illustrative normal approximation gives a 95% mean-effect half-width of about **3.3 points** at N=57 and an 80%-power detectable effect around **4.7 points**. Those calculations do not power the new interaction.

   The inherited failure guard is more restrictive. With zero failure discordances, its fallback upper bound at N=57 is:

   \[
   1-0.0125^{1/57}=0.0740.
   \]

   Thus that result fails the +5-point guard; **N≥86** is needed even for this special zero-discordance case. With 10% discordance and zero true net harm, approximately **314 pairs** are needed for 80% probability of clearing the normal-approximation guard; using the old **17/139** discordance rate gives approximately **384**. These are planning illustrations, not guaranteed requirements for every outcome distribution. [Inherited guard](/home/bmarti44/stencil-llm/results/memorycode-long/REGISTRATION-4C.md:98)

   Freeze N using pilot nuisance estimates for the selected interaction and guard, then check feasibility. If the available cohort and eight-hour budget cannot support that N, register a **screen**, not confirmation.

9. **Separate lifecycle claims from delivery claims.**  
   Holding T1 fixed is appropriate for estimating delivery effects. It does not establish that lifecycle maintenance interacts beneficially with delivery. If that is part of the claimed recombination, include update/no-update conditions and a retirement or stale-rule ablation. Otherwise state that the contribution concerns delivery of a supplied current register, with automatic lifecycle performance assessed separately.

10. **Register distinct scientific, practical, and stopping decisions.**  
    Scientific support requires the selected interaction, not just a positive average. Practical support requires a predeclared worthwhile effect or cost advantage plus the harm and functionality gates. A nonsignificant interaction is “not demonstrated”; call it negligible only if its interval excludes the registered meaningful range. Stop for failed runtime qualification, incorrect rule-state handling, infeasible token accounting, or insufficient feasible N. Any interim futility rule must be fixed in advance, and neither a favorable screen nor a near-significant result authorizes another confirmation cohort.
