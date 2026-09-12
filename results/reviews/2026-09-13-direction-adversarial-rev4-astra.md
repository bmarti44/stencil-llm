**I reject both E1 and E2 as satisfying all the owner’s criteria today. Neither has a research-supported good chance of producing the specified artifact as currently defined. I cannot conclusively disprove the narrow novelty claim of either.**

E1 supplies information before an irreversible commitment only if its dependency map is correct. Its strongest safe implementation often becomes the dependency-complete `before` arm. E2 removes invalid examples, but neither guarantees a replacement nor establishes that a valid example will help with a different algorithm.

These are research-selection judgments, using the interpretation applied in round 3. They are not statistical rejections inferred from three exposed pilot items. My earlier recommendations were candidates for investigation, not established solutions; their weaknesses deserve the same treatment as D’s.

I searched literature available through **September 12, 2026**, including recent September work, and inspected the proposal, ledger entries, prior reviews, v6 artifact, runtime, and Exp 4C report. I did not read `data/bench/`.

**E1’s broad ingredients are established. The remaining novelty is a specific comparative effect.**

| Prior art and identifier | Exactly which E1 claim it covers |
|---|---|
| [CodePlan, FSE 2024, arXiv:2309.12499](https://arxiv.org/abs/2309.12499) | Dependency analysis, change-impact analysis, ordered edits, and supplying task-specific instructions and repository context at each edit. “Dependency-aware instruction delivery for coding” is already too broad a novelty claim. CodePlan also adapts its plan after changes, a capability E1 excludes. |
| [ZORO, arXiv:2604.15625](https://arxiv.org/html/2604.15625v2) | Evolving coding rules attached to execution steps, including decomposition of steps to accommodate rules and evidence requirements. The proposal acknowledges this predecessor correctly, but moving the boundary inside a completion does not itself establish significance. |
| [Monitor-Guided Decoding, NeurIPS 2023, arXiv:2306.10763](https://arxiv.org/pdf/2306.10763) | Generation-time guidance from repository-wide types, interfaces and dependencies. The proposal understates it as identifier constraints: the paper also demonstrates argument-count and stateful API-protocol constraints. It uses token restrictions rather than prose reminders. |
| [CodeTeam, arXiv:2606.22082](https://arxiv.org/html/2606.22082v1) | Dependency-aware scheduling of code generation with bounded context and interface coordination. This covers the planning-and-context combination, though not E1’s controlled within-output timing comparison. |
| [Synquid, PLDI 2016, arXiv:1510.08419](https://cseweb.ucsd.edu/~npolikarpova/publications/pldi16.pdf) | Propagating requirements into partial programs and rejecting incompatible choices early. “Obligations must influence their prerequisite decisions” is established synthesis practice. It does not test prose-delivery schedules. |
| [ChopChop, DOI:10.1145/3776708](https://doi.org/10.1145/3776708) | Semantic constraints during generation and the requirement that a partial output remain completable. This is a stronger formulation of E1’s earlier-commitment problem than merely identifying a syntactic trigger. |
| [IterGen, arXiv:2410.07295](https://arxiv.org/abs/2410.07295); [Hydra, arXiv:2605.15238](https://arxiv.org/html/2605.15238v1) | Semantic boundaries, verification, retained prefixes and rollback. They cover the proposed execution machinery, not a dependency-timing advantage over equal information supplied beforehand. |
| [TRACE, arXiv:2606.13174](https://arxiv.org/html/2606.13174v1); [Answer Engineering, arXiv:2606.21121](https://arxiv.org/html/2606.21121v1) | Correction-derived rules and lifecycle management; programmable interventions and local trajectory editing. Together they cover much of the “live rules plus runtime delivery” package. |
| [Remember When It Matters, arXiv:2607.08716](https://arxiv.org/html/2607.08716v1) | Maintained execution-state memory delivered before subsequent actions. Its selective-reminder ablation does not uniformly beat always injecting: task-weighted results are 61.2% versus 61.5%. This supports memory assistance more strongly than selective timing. |
| [FalconCopilot, DOI:10.18653/v1/2026.findings-acl.1500](https://aclanthology.org/2026.findings-acl.1500.pdf) | Dependency analysis followed by incremental instruction delivery when prerequisite crew actions are fulfilled. This directly covers dependency-conditioned delivery in aviation assistance, although the instruction recipient and task differ. |
| [RegulAR, arXiv:2608.26715](https://arxiv.org/html/2608.26715v1) | A hierarchical dependency graph supporting procedural guidance, downstream-impact reasoning and recovery. Its small human study supports assistance and understanding, not E1’s coding-success prediction. |
| [Fresh Memory, Stale Plans—PlanFence, arXiv:2609.03340](https://arxiv.org/html/2609.03340v1) | Dependency-scoped validation of a plan against changed requirements immediately before action. It directly anticipates the distinction between receiving the current rule and replacing a decision derived from an obsolete rule. Its controlled results are not general coding-accuracy evidence. |

The narrower question remains:

> With identical actionable information, does a causal, dependency-based delivery policy improve joint correctness over supplying everything relevant beforehand?

I did not find a paper that settles that exact comparison. That is **NOT DISPROVED novelty**, not evidence that the answer will be positive.

**The educational evidence does not predict E1’s proposed ordering as confidently as the proposal says.**

Cognitive load theory’s element interactivity concerns information that must be processed together, relative to existing expertise. It does not imply that delivering each dependency separately or as late as possible improves performance. Highly interacting material can instead require an integrated representation. [Sweller, DOI:10.1007/s10648-010-9128-5](https://doi.org/10.1007/s10648-010-9128-5), [Chen et al., DOI:10.1007/s10648-023-09782-w](https://link.springer.com/article/10.1007/s10648-023-09782-w).

CLT has already been applied explicitly to prompting and inference. *What Makes a Good Natural Language Prompt?* incorporates cognitive-load considerations; CLAI explicitly discusses element interactivity and proposes context shaping and staged inference. Neither validates E1’s dependency-timing mechanism. CLAI is also a preprint whose cognitive analogy should not be treated as an established transformer mechanism. [ACL 2025, DOI:10.18653/v1/2025.acl-long.292](https://aclanthology.org/2025.acl-long.292.pdf), [CLAI, arXiv:2507.00653](https://arxiv.org/html/2507.00653v1).

The especially relevant Kester experiment supported separating declarative and procedural information across time. It **did not support the predicted superiority of declarative-before/procedural-during over the other schedules**. The proposal cites this research while restoring the stronger ordering implication that round 3 already challenged. [Kester et al., DOI:10.1016/j.cedpsych.2005.04.002](https://research.ou.nl/files/1023594/CEP%20L_Kester%20%5BRr%5D.pdf).

Clinical decision support supplies a similarly qualified analogy: point-of-care reminders improved process adherence by a median **4.2 percentage points**, while a separate randomized hard-stop intervention produced treatment delays serious enough to stop the trial. Timely compliance and useful outcomes are distinct. These numbers are not forecasts for coding. [Shojania et al., DOI:10.1503/cmaj.090578](https://pmc.ncbi.nlm.nih.gov/articles/PMC2842864/), [Strom et al., DOI:10.1001/archinternmed.2010.324](https://pubmed.ncbi.nlm.nih.gov/20876410/).

**Dependency timing is a real variable, but dependency correctness does not establish a reason to delay information.**

The argument **for E1** is defensible. A bounded model might benefit from receiving only the obligations needed for its current decision. Withholding future material could reduce interference, while supplying each packet before its consequences become difficult to change. Code-generation research on maintaining prompt influence makes this possibility credible. [Selective Prompt Anchoring, ICML 2025](https://proceedings.mlr.press/v267/tian25a.html).

The argument **against E1** is stronger for this proposal. Let \(d(r)\) be the earliest commitment affected by rule \(r\), and \(t(r)\) its delivery time. Avoiding late delivery requires:

\[
t(r)\le d(r).
\]

That condition does not imply that \(t(r)=d(r)\) is best. `before` satisfies it for every rule by delivering everything at the start. It also receives the same imports, mappings and implementation information.

Consequently, E1 cannot credit a gain to supplying dependencies: that advantage belongs equally to `before`. E1 must demonstrate a benefit from **withholding some already available, relevant information during earlier generation**.

There is also a concrete implementation issue. The existing user-channel branch rebuilds the prompt and re-prefills the retained assistant prefix. A newly delivered rule is therefore not necessarily adjacent to the next code decision. When the rebuilt token sequence, positions and prefix match an up-front construction, the model has no additional memory of when the rule was “delivered.” The remaining causal difference lies in how earlier tokens were generated. [Runtime](/home/bmarti44/stencil-llm/src/stencil/focal_runtime.py:425).

My decision: **not inherently a meaningless permutation**, but the meaningful variable is staged information availability. Calling it dependency order does not establish its benefit.

**E1 moves much of D’s difficulty into the dependency map.**

A static dependency map is straightforward for some known interfaces. It is substantially harder for an unwritten program with several valid implementations:

- A required structure can affect the first emitted declaration.
- A naming convention can affect the first caller or interface.
- A decorator can change imports, signatures, calling conventions and behavior.
- An exception-handling rule can affect return semantics and control flow.
- Dependencies can be conditional or cyclic; a topological order alone cannot represent every case.

The map is therefore generally a function of the request, environment, existing code and evolving generation—not just the rule’s type.

A conservative map moves uncertain obligations to the start. An aggressive map retains the risk that an unobserved earlier commitment already depends on them. An oracle constructed from the eventual solution risks supplying information about that solution through the schedule itself.

The proposal excludes global planning and adaptive scheduling while relying on identifying decisions that may require both. This is a boundary problem in the direction, not merely unfinished implementation.

There is **no measured estimate** of how often E1 collapses to `before`. The repository contains no E1 dependency-map census. I would expect substantial collapse among the proposal’s import, interface and structure cases, but a numerical prevalence claim would be invented.

The implication can nevertheless be computed. If the two policies become identical on a fraction \(c\) of tasks, their maximum average joint-success advantage is \(1-c\). If they coincide on 75% of tasks, a ten-point overall advantage requires a forty-point advantage on the remainder. Those percentages illustrate the constraint; they are not observed frequencies.

The v6 record supplies no evidence that the remaining problem is only dependency arrival. Its strongest-looking convention output contains the imports yet still self-decorates an undefined function and implements Roman-numeral conversion incorrectly. E1 could fix some missing-import failures without fixing algorithmic integration. [v6 artifact](/home/bmarti44/stencil-llm/results/focal/quicklook-v6.json), [round-3 review](/home/bmarti44/stencil-llm/results/reviews/2026-09-12-direction-adversarial-rev3-astra.md).

Exp 4C likewise provides weak encouragement: **+2.05 points, 95% interval [−0.07,+4.16]**, strict compliance **0 versus 1 out of 139**, and an unresolved failure guard. Its capped outputs and different intervention prevent extrapolating those numbers directly to E1. [RESULTS-4C.md](/home/bmarti44/stencil-llm/results/memorycode-long/RESULTS-4C.md).

**E1’s first test has the right comparisons, but it is not yet a complete or reliably disconfirming registration.**

These are the material confounds and ambiguities in §2:

| Issue | Why it matters |
|---|---|
| **Oracle information** | A map derived from a reference implementation, future output or hidden tests can encode the solution’s structure. Equal packet text does not equalize that information. |
| **Unobservable decision points** | A trigger at the first visible manifestation of a choice can still be late. A causal rule for firing before the commitment is missing. |
| **Schedule matching** | Shifting positions changes the schedule. Permuting packets across fixed positions preserves intervention times but can violate prerequisites. The proposal does not choose between them. |
| **Sabotaged control** | Delivering a necessary import/interface rule after commitment makes `staggered` predictably bad. Beating it does not establish superiority over reasonable timely delivery. |
| **Divergent trajectories** | Token offsets and syntax boundaries cease to correspond after the arms generate different code. Outcome-dependent rematching would compromise the comparison. |
| **Early completion and absent triggers** | Some arms may finish before a packet is delivered or never emit the anticipated unit. Dropping those tasks creates selection bias. |
| **Packet content and repetition** | Dependency closure, repeated global rules, labels, name mappings and duplicate suppression must be frozen. Equal totals alone are insufficient. |
| **Role and prompt layout** | Number of messages, instruction priority, packet order and request placement must match their declared causal purpose. |
| **Re-prefill and regeneration** | Retained-prefix processing, discarded tokens, retries and restarts consume compute. Equal delivered tokens do not mean equal resources. |
| **Context and completion budgets** | A history truncated differently, or a treatment with more usable generation space, can explain a gain. Padding is not automatically inert. |
| **Task construction** | Authoring tasks around known failures enriches the hypothesized mechanism. Shared templates are clusters, not independent tasks. |
| **Incorrect task categories** | Naming and `try` rules are not necessarily local. Rule labels cannot substitute for demonstrated dependency structure. |
| **Specification consistency** | Current conventions must be compatible with the requested interface, tests and actual library APIs. Otherwise joint success may be impossible. |
| **Scorer validity** | Query-required scoring fixes a denominator problem, not decorator semantics, import availability, nested-scope handling or weak functional tests. |
| **Historical commitments** | A changed rule may require editing already existing session code. Delivering a reminder during the new completion cannot update an inaccessible caller. |
| **Package attribution** | `base` must be the actual package with the modification off. The continuation rule currently requires no functional harm versus base, but does not explicitly require joint-success superiority over base. |
| **Decision rules** | N, exact test, uncertainty interval, missingness, equivalence margin and interpretation of “majority” are unspecified. The claim also includes beating `unit`, while the continuation rule does not require it. |

A positive result becomes uninterpretable as an E1 timing effect if it depends on privileged oracle information, a deliberately late control, unmatched content, different usable budgets, selecting only successful triggers, or defective scoring. A valid oracle result still would not establish the deployable mapper or long-session artifact.

Two kill rules also overreach:

1. **No observed advantage at 24–32 tasks is not evidence of equality.** It can justify stopping investment, but cannot establish that the mechanism is absent.
2. **An advantage only on local tasks is not “D’s, already disproved.”** D was rejected probabilistically, using confounded pilots. A fair positive local effect would be evidence, although it would fail E1’s dependency-specific rationale.

**My earlier 24–32 recommendation was suitable for finding gross failures, not for establishing a ten-point effect.**

For binary joint success, let \(q\) be the probability that a paired comparison is discordant and let the true advantage be ten percentage points. I computed exact two-sided McNemar power by summing over the binomial distribution of discordant pairs:

| Discordant fraction \(q\) | Minimum N for 80% power | Minimum N for 90% power |
|---:|---:|---:|
| 0.10—all discordances favor treatment | 78 | 91 |
| 0.20 | 168 | 215 |
| 0.30 | 249 | 325 |
| 0.50 | 408 | 539 |

These are independent task/session pairs, not individual conventions or repeated generations treated as new tasks. They concern detecting an advantage over zero, not proving it exceeds ten points.

There is no universal minimum without the discordance assumption. Under \(q=.30\), **249 pairs** is the minimum for 80% power for one comparison. Requiring both superiority comparisons creates a conjunction: targeting 90% power for each gives at least 80% power for both by the union bound, before the additional gates. Testing both required comparisons at .05 does not automatically require Bonferroni correction for that conjunction.

At N=24, three wins and no losses yield **+12.5 points but p=.25**. At N=32, four wins and no losses yield **+12.5 points but p=.125**. Six wins and no losses are the first configuration with two-sided exact p<.05.

The majority clause creates a different problem. Strict wins on a majority of 16 dependency-bearing tasks means at least nine treatment-only successes. A useful population effect with 30% wins, 20% losses and 50% ties has a ten-point advantage, yet only a **2.57%** chance of meeting that majority clause. It is an aggressive investment gate, not a sensitive test of a ten-point benefit.

Finally, “no net functional harm” needs an interval. With zero observed treatment-only failures, the two-sided 95% exact upper bound on their probability is **14.25% at N=24** and **10.89% at N=32**. Even the favorable sufficient calculation for bounding that probability below 5% requires **72 pairs**. That bounds treatment-only harm; it is not the complete paired excess-harm analysis.

Keep 24–32 if the purpose is a cheap screen. Do not call its negative reading equivalence or its positive reading proof.

My subjective forecasts, conditional on fixing the test’s ambiguities without changing E1:

- **Literal §2 continuation gate:** approximately **5–15%**.
- **A published wrapper with a defensible useful improvement over itself unmodified on long coding sessions:** approximately **5–20%**.

These ranges are judgments, not calculated posteriors. The strongest deductions are collapse to `before`, uncertain map correctness, residual functional errors and the substantial gap between oracle terminal generation and the shipping objective.

| E1 criterion | Verdict | Decisive reason |
|---|---|---|
| Novel recombination | **NOT DISPROVED, narrowly** | The exact matched-information timing effect remains unsettled. |
| More than a meaningless permutation | **NOT DISPROVED** | Staged availability can causally change generation; the proposed explanation remains unverified. |
| Significant difference | **NOT DISPROVED** | A useful timing effect is possible, but its reachable population may be small. |
| Useful | **NOT DISPROVED** | Correctly timed information can help; cost and functional benefit are unresolved. |
| Good chance of working | **DISPROVED as a present research-selection judgment** | The dependency condition favors early completeness; the additional reason to delay is weak, while the deployable map remains difficult. |

**E2 has stronger support for examples in general than for its particular lifecycle mechanism.**

| Prior art and identifier | Exactly which E2 claim it covers |
|---|---|
| [Show and Tell, arXiv:2511.13972](https://arxiv.org/html/2511.13972v1) | Prose instructions plus examples for coding-style control. It uses one CSV-tool task, repeated generations and two turns, with functional accuracy near ceiling. Its own limitations explicitly say it does not establish task-success gains or a factorial interaction. “Rules + examples > either alone for coding” is too broad a summary. |
| [Zep, arXiv:2501.13956](https://arxiv.org/html/2501.13956v1) | Temporal validity, contradictory updates and invalidation while preserving history. It does not validate executable examples or their transfer to another algorithm. |
| [Case Factory maintenance, LWA 2014, CEUR Vol.1226, paper 07](https://ceur-ws.org/Vol-1226/paper07.pdf) | Propagating maintenance through dependencies among knowledge sources and cases. Maintaining examples when their supporting knowledge changes is established case-based reasoning practice. |
| [SkillOps, arXiv:2605.13716](https://arxiv.org/html/2605.13716v1) | Executable skill contracts, preconditions, validators, dependency/compatibility relations and repair or retirement. Its reported maintenance-only improvements for retrieval-heavy agents are **0.68–2.90 points**; the larger standalone-agent result cannot be attributed solely to maintenance. Skills are executed, whereas E2’s examples influence a generator. |
| [PlanFence, arXiv:2609.03340](https://arxiv.org/html/2609.03340v1) | Exact dependency/version lineage checked before using a derived plan. This directly challenges broad novelty for checking a stored derivative against changed requirements. It does not establish beneficial imitation from validated code examples. |
| [Library Drift, arXiv:2605.19576](https://arxiv.org/html/2605.19576v1) | Outcome-based lifecycle management of reusable agent knowledge. It also reports harm from premature retirement, undermining the assumption that more invalidation is automatically better. |
| [EvoMem/EvoArena, arXiv:2606.13681](https://arxiv.org/html/2606.13681v1) | Memory updates across changing software, terminal and preference conditions. The reported average improvement is modest; it does not isolate E2’s example-validity mechanism. |
| [STALE/CUPMem, arXiv:2605.06527](https://arxiv.org/html/2605.06527v1) | Changes that invalidate related memories without direct contradiction, and propagation-aware state maintenance. This covers E2’s dependency-invalidation motivation and exposes the difficulty of discovering those dependencies. |

E2’s remaining question is whether **validating demonstrations preserves beneficial imitation while preventing obsolete behavior, beyond what ordinary current-rule prompting already achieves**.

I cannot conclusively disprove that question’s novelty. The distinction between executing a maintained skill and learning from a maintained demonstration matters. Conversely, merely applying an established invalidation operation to another stored object is not enough to establish a significant recombination.

**E2 has two independent mechanism failures.**

First, **validity is not transferability**. A binary-search example can pass every test and every current convention while being a bad demonstration for a traversal task. Version checks cannot establish that its algorithmic structure is appropriate. Testing the source example proves a property of the source example.

Cross-domain research supports this distinction. Analogical-learning experiments find that extracting transferable structure from examples requires more than having a correct case available; explicit comparison can improve transfer. That supports taking the transfer problem seriously, not assuming a model receives the desired abstraction from one example. [Gentner, Loewenstein and Thompson, DOI:10.1037/0022-0663.95.2.393](https://groups.psych.northwestern.edu/gentner/papers/GentnerLoewensteinThompson03.pdf).

Second, **the first test may supply no admissible example precisely when it is needed**.

Consider the stipulated sequence:

1. A successful session example follows naming rule A.
2. The owner replaces A with incompatible naming rule B.
3. The next request needs a different algorithm under B.

The earlier example now fails validation. If there is no other valid example, E2 discards it and becomes rules-only. It cannot strictly outperform an identically rendered rules-only arm on that item under identical deterministic generation.

Replacement is not free. It requires an existing candidate, adaptation, or new synthesis and testing. The latter two need a defined procedure and measured cost; an adapted snippet is also no longer simply a previously successful session example.

More generally, when E2 falls back exactly to rules-only on items without an admissible example, its average advantage over rules-only is bounded by the fraction of items with an admissible example. The proposal does not estimate that coverage.

**E2’s test is substantially less specified than E1’s.**

The following choices can change the result:

- **Example supply:** selection pool, cold-start handling, tie-breaking, replacement and adaptation.
- **Validity definition:** exact version identity versus semantic compatibility; checking one attached rule versus every rule manifested in the snippet.
- **Dependency completeness:** imports alone versus configuration, API behavior, object state and transitive dependencies.
- **Validation leakage:** using a previous task’s available tests is legitimate; selecting examples using the future task’s hidden evaluator supplies privileged information.
- **Changed-rule prevalence:** making every ordinary example stale manufactures a large advantage over that arm without demonstrating ordinary-session value.
- **Unrelated changes:** discarding all examples after every update can destroy useful coverage.
- **Representation:** the validated arm must not uniquely receive clearer labels, newer prose, repaired names or additional explanations unrelated to validation.
- **Budget:** rule truncation, example length, replacement generation and validation must all count.
- **Historical exposure:** retiring an example from retrieval does not remove the same obsolete code from the retained transcript.
- **Functional transfer:** old-algorithm copying needs a task-specific operational definition, not a subjective impression after viewing outputs.
- **Selection bias:** all sessions count, including those with no example, failed validation and no usable replacement.
- **Decision rule:** N, minimum useful difference, exact test, uncertainty and maintenance-cost threshold are absent.

A reduction in obsolete-pattern copying is not sufficient: deleting every example could achieve that while losing all demonstration benefit. A gain over stale examples alone could merely establish that knowingly supplying contradictory examples is harmful.

Likewise, equality with ordinary examples would retire the claimed advantage of validation; it would not logically establish that the underlying idea was never novel. Non-significance would establish neither equality nor lack of novelty.

For binary joint success, the same sample-size calculations apply. E2 provides no quantities from which a more favorable minimum N can be justified.

There is no literal registered-positive probability to calculate because §3 supplies no complete gate. For a fair small screen requiring a useful joint-success advantage over **both** listed comparators, my subjective range is **15–35%**. Conditional on an abundant, genuinely transferable valid-example pool, I would raise it to **35–55%**. That condition is a large part of what needs establishing.

For the owner’s actual published long-session wrapper, I estimate **15–35%**. E2 is more plausible than E1, but its strongest citation concerns style on one task, while the proposal leaves availability, transfer and maintenance unresolved.

| E2 criterion | Verdict | Decisive reason |
|---|---|---|
| Novel recombination | **NOT DISPROVED, narrowly** | Maintained demonstrations influencing generation leave a narrower question than maintained executable skills. |
| More than a meaningless permutation | **NOT DISPROVED** | Excluding invalid examples changes available evidence and can change behavior. |
| Significant difference | **NOT DISPROVED** | Preventing obsolete copying could matter; prevalence and incremental benefit remain unknown. |
| Useful | **NOT DISPROVED** | Valid examples can help, but validation can also remove coverage or preserve misleading algorithms. |
| Good chance of working | **DISPROVED as presently specified, as a research-selection judgment** | The method neither guarantees an admissible example after a change nor tests whether source validity predicts useful transfer. |

**The replacement I would investigate is current-rule demonstration compilation, with no claim that it already satisfies the goal.**

Keep authoritative prose. For the supported convention families, instantiate a small executable demonstration from a fixed template using the **current rule and its actual dependencies**. Construct it when the rule changes, independently of the next task’s solution. Use an intentionally simple body so the demonstration teaches naming, imports, decorators or structure without importing a previous task’s algorithm.

This addresses E2’s supply problem directly and supplies information before E1’s earliest commitments.

Its prior-art burden is substantial. Show and Tell covers rules plus compact demonstrations. Self-ICL already generates demonstrations when no example pool exists. Synthesis and TRACE cover specifications compiled into executable artifacts. None of those components can be claimed as new. [Self-ICL, DOI:10.18653/v1/2023.emnlp-main.968](https://aclanthology.org/2023.emnlp-main.968/).

The narrow candidate gap is whether **compiling changing conventions into task-independent executable demonstrations** improves functional convention transfer while avoiding both stale examples and inappropriate source-algorithm copying. That is an empirical hypothesis, not a novelty certificate.

The cheap test can replace E2’s proposed test, using its three arm slots and the already proposed authored tasks:

- Current prose rules alone.
- Current rules plus ordinary session examples.
- Current rules plus a compiled current-rule demonstration.

Freeze templates before evaluation; give all arms the same available dependency facts and total resource allowance. Generate demonstrations without access to the target solution or evaluator. Score joint success, function-only success, stale conventions, inappropriate copying and construction cost.

The kill rule is straightforward: retire the direction if it does not improve joint success over rules-only, if any apparent gain comes only from defeating deliberately stale examples, or if copied template behavior damages functionality. A 24–32-task result remains a development screen with intervals, not confirmation.

I would put roughly **30–50%** on a useful small-screen result and **20–40%** on the final artifact. That is a somewhat better next experiment, not an honest basis for declaring the owner’s goal met. If its only successful contribution is a convenient implementation of existing few-shot guidance, classify it as engineering.

**The owner is also overlooking three constraints on this search.**

First, an adversarial reviewer’s failure to find a counterexample is not positive evidence of efficacy. Successive narrowing can eventually make any proposal difficult to disprove because little remains specified. Reviewer survival should not substitute for an attainable, informative test.

Second, historical code is part of session state. Updating a rule register, reminder or example cache does not update callers, files or plans already derived from the old rule. Both directions need to state exactly which existing commitments the wrapper can influence.

Third, the proposed tests risk repeating the repository’s original error: rewarding recognizable convention implementation while under-measuring actual success. The v6 output that visibly follows naming and decorator instructions but fails its algorithm is the decisive warning. The joint outcome is necessary; competent executable tests, admissible examples and honest coverage are what make it meaningful.

**The goal remains unmet. E1’s unresolved claim is that delaying complete information helps. E2’s unresolved claim is that an available, valid example is a helpful example. Neither implication is established by its cited research or the repository evidence.**
