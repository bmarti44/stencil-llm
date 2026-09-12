A: DISPROVED  
B: DISPROVED  
C: DISPROVED  
D: DISPROVED  

These verdicts concern the candidates **as substantively novel research directions under the owner’s stated standard**. Useful implementations remain plausible. I found no single predecessor containing every detail of A1–A5, but found direct predecessors for the supposedly new mechanisms and a close predecessor for the conversational policy pipeline. The remaining differences are integration and presentation choices without an identified new algorithm, guarantee, or demonstrated interaction.

I read the requested proposal, Exp 4C registration/results, plan sections G–K, and the shipping package. This review used primary papers, proceedings, repositories, and documentation available through September 12, 2026. I did not read `data/bench/`, write files, or run generation experiments.

**A’s decisive failure is substantive novelty: TRACE already supplies conversational rule acquisition, compilation, and retirement; Answer Engineering already supplies compiled policy interventions inside generation.**

TRACE converts user corrections into atomic, applicable rules, compiles checks, and manages explicit New/Update/Supersede/Split/Noop operations. Its enforcement runs at agent hooks. Answer Engineering compiles a rule DSL into monitoring, replacement, rollback, and forced insertion during an ongoing completion. Connecting the former’s current rules to the latter’s intervention machinery describes A’s principal contribution. Canonical user-reviewed requirements also already exist in Kiro. [TRACE, 2026 preprint](https://arxiv.org/html/2606.13174v1); [Answer Engineering, 2026 preprint](https://arxiv.org/html/2606.21121v1); [Kiro requirements workflow](https://kiro.dev/docs/specs/feature-specs/requirements-first/)

That directly overturns the proposal’s strongest novelty assertion: **A5 is already present in prior work.**

The following mapping distinguishes implemented capabilities from superficially similar ones. “Partial” does not mean the complete proposed component exists.

| Closest source | A1: admission | A2: canonical readback | A3: executable monitors | A4: retirement | A5: control inside completion |
|---|---|---|---|---|---|
| [TRACE, 2026](https://arxiv.org/html/2606.13174v1) | Yes: corrections/preferences | Partial: atomic directives and applicability; user-facing readback unverified | Yes | Yes: versions and supersession | No: agent hooks |
| [Answer Engineering, 2026](https://arxiv.org/html/2606.21121v1) | No automatic acquisition | No | Yes, from authored DSL | Listed as future work | Yes: triggers, insertion, edits, rollback |
| [IterGen, ICLR 2025](https://arxiv.org/html/2410.07295v2) | No | No | Programmer-supplied semantic predicates | No | Yes: unit-level checks, rollback, regeneration, KV reuse |
| [Hydra, 2026](https://arxiv.org/html/2605.15238v1) | No | No | Incremental static checks | No | Yes: rollback and diagnostic-comment insertion before continuation |
| [Antislop, 2025](https://arxiv.org/html/2510.15061v1) | No | No | Supplied strings/regexes | No | Yes: style-pattern detection and backtracking |
| [Thinking Intervention, 2025](https://arxiv.org/html/2503.24370v3) | No session acquisition | Partial: first-person instruction reminders | Trigger matching | No | Yes: trigger-conditioned insertion and continuation |
| [SafeRemind, 2026](https://arxiv.org/html/2601.03662v1) | No | No | Entropy/newline trigger | No | Yes: reminder insertion without rollback |
| [LintCFG, 2026](https://arxiv.org/html/2602.07783v1) | Standards supplied | Structured representation, without conversational confirmation | Yes: NL standards → DSL → linter configuration | No | No |
| [Kiro, introduced 2025](https://kiro.dev/blog/introducing-kiro/) | Partial: requirements extraction from requests | Yes: conditional requirements reviewed by user | Not the proposed monitors | Document updates, not demonstrated monitor retirement | No |
| [Zep, 2025](https://arxiv.org/html/2501.13956v1) | Partial: conversational facts | No | No | Yes: temporal invalidation | No |
| [AgentSpec, ICSE 2026](https://cposkitt.github.io/files/publications/agentspec_llm_enforcement_icse26.pdf) | NL policy supplied | No capture readback | Yes: trigger/check/enforcement DSL | Not established | Agent-action boundaries |
| [ChopChop, POPL 2026](https://doi.org/10.1145/3776708) | No | No | User-programmed AST constraints | No | Semantic constrained decoding; not the proposed cue loop |

Several narrower exclusions in the proposal also fail:

- **Rollback is already used for policy violations.** IterGen checks completed email addresses against prohibited addresses and rewinds violations. On 100 DecodingTrust examples, Llama-3-8B leaks fell from **67 to zero**, while average generation time increased **0.56→0.76 seconds**. The authors explicitly acknowledge that exact-address checks can still permit fragment leakage. This is content-policy enforcement, not compiler repair. [IterGen, §4.2](https://arxiv.org/html/2410.07295v2)
- **Code-style constraints are already decode-time objects.** TreeCoder exposes style, syntax, and execution constraints, including comment suppression. Comment suppression alone changed reported task accuracy **32.3→32.8%**; larger combined gains cannot be credited to style control. Its illustrative No-Comments pseudocode appears reversed, so I would verify the implementation before relying on that particular example. [TreeCoder, 2025 preprint](https://arxiv.org/html/2511.22277v1)
- **Semantic judges plus rewind are established.** RAIN evaluates generated content and guides rewinding without changing weights; it reports harmlessness **82→97%** for LLaMA-30B on its HH evaluation. [RAIN, ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/hash/5a4699b3d0bf7ba934fe10cdba5a8a32-Abstract-Conference.html)
- **Agent guardrails are not confined to between-task reminders.** NeMo supports buffered validation of output streams. Its documented default can stream a chunk before validation; validating first adds latency. Guardrails AI also documents validation-triggered reasks, with restrictions on streaming behavior. These are relevant baselines, although neither documentation establishes A’s exact KV rollback implementation. [NeMo streaming](https://docs.nvidia.com/nemo/guardrails/latest/configure-rails/yaml-schema/streaming/output-rail-streaming.html); [Guardrails reasks](https://guardrailsai.com/guardrails/docs/concepts/concurrency)

**A could produce a large gain, but the proposed experiment would not attribute it to a novel contribution.**

Prior systems already report substantial gains from enforcement:

| System | Reported result | What it does not establish |
|---|---|---|
| TRACE | ClawArena preference violations **100→37.6%** in distribution and **100→2.0%** out of distribution | Representative prevalence or Stencil performance; the evaluation uses simulated correction interactions |
| Answer Engineering | Two diagnostic branches: adherence **25.1→83.5%** and **58.9→77.9%**; slowdowns **2.78×/1.33×** | Coding correctness, conversational compilation, or generally inexpensive intervention |
| Type-constrained decoding | Compilation errors reduced by **more than half** | Gains from session conventions or readback |
| Aider | Existing automatic lint → diagnostics → repair workflow | A published effect estimate on this workload |

Sources: [TRACE](https://arxiv.org/html/2606.13174v1), [Answer Engineering](https://arxiv.org/html/2606.21121v1), [type-constrained generation, PLDI 2025](https://arxiv.org/abs/2504.09246), [Aider documentation](https://aider.chat/docs/usage/lint-test.html).

These results prevent an honest assertion that “+20 points cannot happen.” They instead undermine the attribution argument: **a large improvement over reminders could come entirely from established enforcement machinery.**

The necessary scientific comparison is against a pipeline with the **same extracted current rules, same monitors, and matched total computational budget**, enforced through existing output/unit repair. An enforcement-on versus enforcement-off comparison cannot distinguish the proposed contribution from adding a linter and repair loop.

The proposal also overinterprets its local evidence. Exp 4C measured one newest-first reminder policy: **+2.05 points, 95% CI [−0.07,+4.16]**. That is not an upper bound on better relevance selection, shorter contexts, larger output budgets, or other reminders. Likewise, the Exp 4B oracle-reminder score is the performance of one prompting intervention, not the model’s capability ceiling. [Exp 4C results](/home/bmarti44/stencil-llm/results/memorycode-long/RESULTS-4C.md)

**A’s likelihood argument contains a false guarantee and several unmeasured bottlenecks.**

1. **Monitor coverage is not a lower bound on improvement.** A perfect monitor can reject every violation while the generator fails every repair. Illustratively, if \(v\) is baseline violation mass, \(c\) is correct applicable-monitor coverage, \(r\) is successful repair probability, and \(h\) is newly introduced harm, an idealized gain is approximately \(vcr-h\). Coverage alone does not bound \(r\) or \(h\).

   After the single permitted retry, the system can release a violation, abort, or produce compliant but functionally wrong code. The proposal has not supplied a mechanism ensuring a useful compliant completion.

2. **Accurate canonical text does not imply an accurate executable monitor.** LintCFG uses GPT-4o. At option-value level, its end-to-end results are **72.1% accuracy, 69.3% precision, 70.3% recall, and 69.8% F1**. Nineteen of 68 Java standards lacked a Checkstyle configuration; constructing the reference configurations took **120 expert-hours**. High intermediate DSL scores do not remove this final translation problem. [LintCFG, §§4.1–4.2](https://arxiv.org/html/2602.07783v1)

3. **Content judges remain fallible instruction followers.** LLMBar specifically tests evaluators’ ability to recognize instruction adherence. Its best reported GPT-4 evaluator reached **82.8%** on adversarial examples, compared with **95% human agreement**; several weaker evaluators performed near chance. These are not direct estimates for a Stencil judge, but they refute treating an unspecified small judge as a reliable semantic oracle. [LLMBar, ICLR 2024](https://openreview.net/pdf?id=tC2lDRhHNT)

4. **Rollback can be expensive.** Hydra’s **71% latency/70% token reductions** concern Qwen2.5-Coder-32B on C/C++ static-error cases **relative to post-hoc repair**. Its corresponding gpt-oss-120B reductions are **25%/27%**. These numbers do not bound added cost over plain generation. Antislop reports **69–96% throughput reductions** with large 1,000–8,000-pattern banlists. That stress test is not a Stencil forecast, but it defeats a general cheap-rollback assumption. [Hydra](https://arxiv.org/html/2605.15238v1); [Antislop](https://arxiv.org/html/2510.15061v1)

5. **Some violations are recognizable only after the useful repair point.** A naming policy may be checkable immediately; a complete docstring policy requires more structure; “explain why this algorithm is appropriate” needs semantic judgment. Partial Python is routinely unparsable. A violated dependency may originate before the most recent syntactic checkpoint. Inserting a comment can also alter docstring placement, formatting, or token-budget consumption.

6. **The package does not already contain the proposed machinery.** Its current `generate` method makes one ordinary model-generation call. Admission is instruction-role sentence selection, not the proposed classifier/monitor pipeline. Moreover, `chat_prompt` embeds the rendered history inside **one native user message**: adding an `"assistant"` record alone does not create a separate native assistant turn for A2. Compiler, monitor, checkpoint, intervention provenance, and revised chat-role handling are substantial new implementation work. [Generation path](/home/bmarti44/stencil-llm/deploy/stencil_focus/stencil_focus/modeling_stencil_focus.py:62); [session formatting](/home/bmarti44/stencil-llm/deploy/stencil_focus/stencil_focus/focus_session.py:30)

The existing baseline also has a severe completion problem: **60/139 output failures**, including **59 capped outputs**. The proposed gain could largely measure recovering missing structures, or adding checker-recognized material, while functional correctness remains unknown. Exp 4C’s failure-difference interval **[−5.17,+6.60] points** already failed the proposed +5-point noninferiority margin. Reusing its sample size does not solve that uncertainty. [Exp 4C results](/home/bmarti44/stencil-llm/results/memorycode-long/RESULTS-4C.md)

**B is DISPROVED as a new direction because structured instruction readback with user correction is already an operational coding-assistant workflow.**

Kiro converts prompts into conditional EARS requirements, asks the user to review and confirm them, and proceeds to implementation. EARS itself dates to **IEEE Requirements Engineering 2009**. The proposal’s claim that no prior system gives users this correction point is false. [Kiro workflow](https://kiro.dev/docs/specs/feature-specs/requirements-first/); [Mavin et al., EARS](https://research.manchester.ac.uk/en/publications/easy-approach-to-requirements-syntax-ears/)

For the self-authored-text component, RECITE uses generated recitations before answers, while Self-Notes interleaves model-authored notes with context. Their outcomes concern other tasks, but they establish the computational pattern. [RECITE, ICLR 2023](https://arxiv.org/abs/2210.01296); [Self-Notes, NeurIPS 2023](https://arxiv.org/abs/2305.00833)

The significance attack is attribution: B changes representation, wording, placement, context length, and potentially available information through user corrections. Any gain can arise from those changes. ClarifyGPT already reports GPT-4 Pass@1 **70.96→80.80%** with requirements clarification in a ten-participant study; improved intent capture is useful and established. [ClarifyGPT, FSE 2024](https://2024.esec-fse.org/details/fse-2024-research-papers/89/ClarifyGPT-A-Framework-for-Enhancing-LLM-based-Code-Generation-via-Requirements-Clar)

The likelihood failure is that readback can confidently preserve a mistaken interpretation. Historical MemoryCode dialogues cannot supply the new human corrections B would elicit. A gold-informed simulated correction would be an assisted intervention requiring explicit disclosure.

**C is DISPROVED because trigger-conditioned insertion inside a completion already exists explicitly.**

Thinking Intervention monitors generated postfixes for trigger strings, appends an intervention, and resumes generation; it permits domain-specific triggers. SafeRemind implements this without rollback using newline/entropy triggers. Answer Engineering’s `After`/forced-continuation operations provide an even closer programmable insertion mechanism. Substituting `def` or `class` for another trigger and supplying a session rule does not introduce a new control operation. [Thinking Intervention, §2.3](https://arxiv.org/html/2503.24370v3); [SafeRemind, Algorithm 1](https://arxiv.org/html/2601.03662v1); [Answer Engineering implementation](https://github.com/victorlavrenko/answer-engineering)

Measured effects span small benefits and substantial tradeoffs:

- Thinking Intervention’s IFEval strict prompt accuracy improves over reminder prompting by **1.86 points** for R1-Qwen-7B and **1.11 points** for QwQ-32B.
- SafeRemind raises its JailbreakBench safety score **53→90%**, while benign refusal rises **4.4→19.2%**; MATH-500 falls **88.4→86.2%**.

These findings support a placement experiment, but provide neither novelty nor a generally harmless gain. [Thinking Intervention, Table 2](https://arxiv.org/html/2503.24370v3); [SafeRemind, Tables 4–5](https://arxiv.org/html/2601.03662v1)

For coding, triggers can fire in quoted examples or comments; multiple rules can compete; omitted structures never trigger. A comparison restricted to outputs that happened to trigger would select on behavior changed by the treatment.

The proposal’s distance citation also does not say what it claims. Du et al. explicitly move evidence immediately beside the question and still find degradation with increasing context length. Their mitigation recites evidence into a **new shorter prompt**. This does not establish that moving a rule 250 tokens closer to a code construct solves the problem. [Du et al., 2025, §4.1](https://arxiv.org/html/2510.05381v1)

**D is DISPROVED as a new direction because supersession-aware state and retrieval already exist; “contrast once” is an unvalidated rendering parameter.**

Zep invalidates temporally overlapping contradictory facts while preserving validity information. MemStrata applies deterministic retirement to software-history facts before retrieval. On **130 clean atomic transitions from 707 fixes**, it reports answer accuracy **.908**, versus **.569/.585** for RAG comparators. The approximately **18% extraction coverage** sharply limits the generality of those gains. [Zep, 2025](https://arxiv.org/html/2501.13956v1); [MemStrata, 2026](https://arxiv.org/html/2608.20685v1)

An especially relevant significance attack comes from *Presentation, Not Mechanism*: an apparent revision-ledger gain of **18.2 points** shrinks to **2.1–2.5 points**, indistinguishable from zero, after matching presentation. On its reverted-revert comparison, coarse invalidation beats the finer ledger by **8.4 points, 95% CI [4.1,12.8], n=439**. Rendering can dominate the apparent lifecycle effect. [2026 preprint](https://arxiv.org/html/2607.16019v1)

D also needs distinctions absent from “latest wins”: updates versus exceptions, task-local versus global rules, historical questions versus current-state requests, and retractions versus corrections. Retiring a reminder does not remove the old instruction from the remaining transcript.

Most importantly, **P3 does not isolate proactive interference**. When two monitors impose incompatible requirements, retaining both makes the allowed-output set empty or unnecessarily restrictive. Removing one can help through ordinary constraint consistency, without any memory-interference mechanism.

**The cross-domain findings are mostly real; their transfer and predicted magnitude are overstated.**

| Imported result | Evidence and replication status | What survives the grounding attack |
|---|---|---|
| **Aviation readback/hearback** | FAA operational analyses report correction of readback errors ranging from **50% on ground frequencies to 89% en route**. These are correction fractions among errors, not randomized treatment effects. NASA warns that an unchallenged readback does not establish correctness. [FAA, 1998](https://rosap.ntl.bts.gov/view/dot/8490/dot_8490_DS1.pdf); [NASA, 1988](https://ntrs.nasa.gov/citations/19890007398) | A two-party verification loop is a sound analogue. Assistant restatement plus silent user noncorrection does not complete it. |
| **Implementation intentions** | The familiar **d=.65 [.60,.70]** comes from **Gollwitzer & Sheeran 2006**, 94 tests, 8,461 participants. A newer 642-test synthesis gives **d=.36 [.33,.40]**; robust Bayesian publication-bias adjustment gives **.15 [.08,.22]**. [2006 synthesis](https://doi.org/10.1016/S0065-2601(06)38002-1); [new synthesis, online 2024](https://doi.org/10.1080/10463283.2024.2334563) | Replicated human benefit, heterogeneous and smaller under some bias adjustments. It supports testing conditional plans; it supplies no MemoryCode percentage-point prediction. |
| **Generation effect** | Slamecka–Graf’s five experiments were followed by a meta-analysis of **445 effects across 86 studies**, averaging **.40**. A 2024 text-learning replication found substantial task dependence and did not reproduce its preregistered interaction. [1978 experiments](https://andymatuschak.org/prompts/Slamecka1978.pdf); [2007 synthesis](https://doi.org/10.3758/BF03193441); [2024 replication](https://onlinelibrary.wiley.com/doi/full/10.1002/acp.4230) | Robust human phenomenon. It does not establish an additional memory channel for model-authored text. |
| **Cue-focal prospective memory** | A 2019 meta-analysis covers **289 effects, 91 studies, 11,639 participants**. Ongoing-task costs are smaller for focal cues, **d=.24**, than nonfocal cues, **d=.67**. Increasing focal-cue count can still impair prospective-memory accuracy. [Primary synthesis](https://bpb-us-w2.wpmucdn.com/sites.wustl.edu/dist/e/969/files/2019/09/Anderson-Strube-McDaniel-2019.pdf) | Focality means overlap between cue processing and the ongoing task—not short token distance. Syntax-conditioned delivery is a hypothesis, not a replication of the human mechanism. |
| **Directed forgetting** | Context-change experiments reproduce forgetting costs/benefits; reinstating the original context reduces them. Reduced recall does not imply erasure. [Sahakyan & Kelley, 2002](https://sahakyanlab.weebly.com/uploads/1/2/4/2/124249919/sahakyan_kelley_2002.pdf) | Supports sensitivity to retrieval context. It does not establish that contrast-once rendering is optimal. |
| **Reconsolidation** | Four direct motor-memory replications, **n=64**, and three conceptual declarative replications, **n=48**, failed to reproduce the expected updating effect. A registered fear-memory replication, **62/group**, found no benefit: recovery difference **d=.17, p=.35**. [Hardwicke et al., PNAS 2016](https://discovery.ucl.ac.uk/id/eprint/1490313/); [Chalkia et al., Cortex 2020](https://ppw.kuleuven.be/okp/_pdf/Chalkia2020NPAOF.pdf) | Biological reconsolidation is not globally refuted. Its use to justify deleting an external monitor is decorative. |
| **Edit automata** | Genuine formal theory of insertion, suppression, and termination, with **soundness and transparency** requirements. The 2005 paper treats finite, arbitrarily long executions; later work develops infinite-renewal results. [Ligatti, Bauer & Walker, IJIS 2005](https://users.ece.cmu.edu/~lbauer/papers/2005/ijis2005-editauto.pdf) | The strongest formal connection, but a bounded retry loop does not inherit these guarantees. Correct predicates, output boundaries, compatible policies, and valid fallback behavior must be established. |

The generation-effect mapping has a particularly simple mechanistic problem. For a frozen autoregressive transformer, identical token histories, roles, positions, model state, and decoding conditions produce the same next-token distribution regardless of whether earlier text was sampled or supplied. Any readback benefit must arise through changed content, placement, representation, or corrections. “The assistant wrote it itself” supplies no additional causal mechanism.

There is genuine field support for human planning: specifying a vaccination date and time increased uptake by **4.2 percentage points** in a randomized study of **3,272 employees**. That establishes useful human behavior change without licensing the proposal’s ≥20-point LLM prediction. [Milkman et al., PNAS 2011](https://pmc.ncbi.nlm.nih.gov/articles/PMC3127912/)

The proposal’s newer AI-memory citations likewise need narrower readings:

- *Unable to Forget* demonstrates interference in overwritten key-value retrieval; one fixed-length experiment falls from nearly **100% with two keys to below 5% with 46**. It does not test coding-monitor retirement or contrast-once rendering. [2025 paper](https://arxiv.org/html/2506.08184v3)
- TriggerBench’s **1,265 tasks** distinguish prospective behavior from retrospective recall, which remains around **98%** in long contexts. It is diagnostic evidence, not an intervention trial validating C. [2026 paper](https://arxiv.org/html/2606.23459v1)
- *Remember When It Matters* reports Terminal-Bench **37.6→45.9%**, using a prompted Opus-4.6 memory agent with Sonnet-4.5. The main result is not from its learned open model. Its selective-versus-always-inject table also gives micro-averages **61.2% versus 61.5%**, so selective delivery is not uniformly superior. [2026 paper](https://arxiv.org/html/2607.08716v1)

**Several stronger analogues expose what the framing misses.**

**Supervisory control** is a closer mathematical match than prospective memory. Ramadge–Wonham model a process as a language generator and a supervisor as restricting its behavior. The central issue is whether permitted behavior remains reachable under the supervisor’s control capabilities. A rule checker does not answer that question. [SIAM Journal on Control and Optimization, 1987](https://epubs.siam.org/doi/10.1137/0325013)

**Runtime assurance/Simplex** separates a complex controller from a dependable fallback and switching logic. A’s fallback is another generation attempt from the same fallible model. It therefore lacks the architectural feature that makes the analogy provide assurance. [Simplex, ACC 1998](https://doi.org/10.1109/ACC.1998.703255); [verified Simplex, ACM TECS 2015](https://doi.org/10.1145/2723871)

**Requirements engineering and truth maintenance** supply established representations for conditional obligations, exceptions, dependencies, and retractions. Doyle’s truth-maintenance system already records justifications and supports dependency-directed revision. Treating each new utterance as replacing an older sentence can lose those dependencies. [Doyle, Artificial Intelligence 1979](https://www.sciencedirect.com/science/article/pii/0004370279900080)

**Medicine’s checklist literature cautions against equating procedural compliance with outcomes.** The initial eight-hospital checklist study reported complications **11→7%** and mortality **1.5→0.8%**. Subsequent Ontario adoption across **101 hospitals and over 215,000 procedures** found mortality **0.71→0.65%, OR .91 [.80,1.03], p=.13**, without a significant complication reduction. This does not disprove checklists; it shows that implementation fidelity and actual outcomes matter. [Haynes et al., NEJM 2009](https://flexiblelearning.auckland.ac.nz/hqsc-site/5/files/haynes_et_al_2009_a_ssc_to_reduce_morbidity_and_mortality_in_a_global_population.pdf); [Urbach et al., NEJM 2014](https://pubmed.ncbi.nlm.nih.gov/24620866/)

There are also four immediate experimental blind spots:

1. **Checker expressibility is not instruction coverage.** A benchmark’s regexes measure selected observable properties. Their existence does not show that arbitrary conventions are captured accurately.
2. **Injected text can directly satisfy the measurement.** Cue comments or forced docstrings may increase checker scores without changing the intended behavior. Intervention-authored tokens need provenance, and functional tests must remain independent.
3. **The 139 dialogues are now outcome-exposed.** Reusing their infrastructure is sensible; reusing them as fresh confirmatory evidence for an outcome-informed mechanism is not. The distinction must remain explicit.
4. **P1–P4 do not jointly establish the claimed contribution.** P1 lacks an established enforcement comparator; P2 measures extraction rather than monitor semantics; P3 confounds interference with inconsistent constraints; P4 confounds focality with placement and changed continuation. Since A fails the novelty test, these predictions do not warrant a confirmation registration in their current form.

**The strongest replacement I can construct is E: counterexample-validated evolving policy compilation. It also fails the novelty standard as a pipeline.**

The substantive problem is enforcing the **wrong interpretation**. E would maintain candidate interpretations of a rule, produce small examples that distinguish their behavior, obtain authoritative labels for those examples, compile the selected interpretation, and preserve version-specific regression witnesses through later updates. Its value would be measured through false enforcement, missed violations, user effort, and functionally correct completions.

This has stronger grounding than self-authorship or reconsolidation—but the adversarial search finds close predecessors:

- **ARTEMIS, ICSE 2026**, translates NL requirements through structured NL, generates low-complexity distinguishing traces, and uses user judgments to eliminate candidate specifications. Across five requirements datasets, it reports **1.57× higher translation accuracy** and, for requirements with more than ten candidates, **2.52× average reduction in validation effort**, up to **10.83×**. It already contains E’s central semantic-validation mechanism. [ARTEMIS](https://cs.stanford.edu/people/trippel/pubs/mendoza_ICSE26.pdf)
- **Agentic Synthesis against Counterexample-Supplemented Sketches, 2026**, already evolves governing policy through approved counterexamples, retains provenance and regression gates, and tests regeneration from the revised specification. Its small demonstration reports **19/21 withheld cases** versus **15/21** for an initial-sketch/replay comparator; the authors explicitly limit generalization from one model and reveal order. [Paper](https://arxiv.org/abs/2607.15854)
- TRACE supplies the remaining conversion into persistent coding-agent checks.

**E: DISPROVED as a substantively new pipeline.** Applying these existing mechanisms to session conventions could be useful engineering, but calling that recombination novel would repeat A’s problem.

I cannot honestly name a replacement that this review establishes satisfies all three requirements—substantive novelty, significant utility, and a research-supported likelihood of success. The owner’s goal remains unmet. The decisive result of this review is that the proposed mechanisms already exist, while the claimed novel contribution has not been separated from their established effects.
