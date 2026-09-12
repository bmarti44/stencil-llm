**I would now reject D as satisfying all the owner’s criteria. The decisive weakness is its chance of producing a useful, functionally sound improvement—not a conclusive novelty objection. I put about 20% on a fair registered screen reading positive for the owner’s actual objective.**

That is a research judgment, not a statistical rejection inferred from three exposed items. The pilots cannot establish that every correctly implemented version of D will fail. They do undermine the claim that successful cue delivery makes success reasonably likely.

I searched literature available through **September 12, 2026**, including September publications, and inspected the proposal, runtime, pilots, checker, reviews, ledger, and Exp 4C report. I independently reproduced the v6 scores and the diagnostic Roman-numeral failure. I did not read `data/bench/`.

| Owner’s criterion | Verdict on D as a research direction | Decisive reason |
|---|---|---|
| Novel recombination | **NOT DISPROVED**, narrowly | The components have close predecessors. I did not find a demonstrated interaction exactly matching live session conventions, governed code units, and within-output delivery. |
| More than a meaningless permutation | **NOT DISPROVED**, but conditional | A useful effect attributable to semantic placement could qualify. The pilots have not isolated that effect. |
| Significant difference | **NOT DISPROVED** | Delivery can materially change behavior. Whether it produces a significant *benefit over a fair reminder* remains unknown. |
| Useful | **NOT DISPROVED for a corrected version; unsupported by v6** | Local compliance is real, but the strongest apparent improvement accompanies broken functionality. |
| Good chance of working on the actual objective | **DISPROVED as a present research-selection judgment** | The mechanism addresses instruction arrival, while the evidence exposes failures of planning, integration, and execution. Oracle pilots bypass additional unresolved difficulties. |

The last verdict is explicitly probabilistic. It does not mean impossibility. I would not describe my estimated one-in-five prospect as a good chance.

**The novelty claim survives only in a much narrower form than “just-in-time instructions for code.”**

The following prior art covers nearly all of D’s machinery and much of its motivation. The recent arXiv results should be treated as preprint evidence, not as independently replicated findings.

| Prior art | Exactly what it covers in D | What remains different |
|---|---|---|
| **Monitor-Guided Decoding**, NeurIPS 2023, [arXiv:2306.10763](https://arxiv.org/abs/2306.10763) | Static-analysis monitors intervene during code generation at relevant contexts; global program information guides local choices. This directly anticipates transferring IDE assistance into generation. | It constrains choices rather than delivering evolving session conventions as prose. |
| **IterGen**, ICLR 2025, [arXiv:2410.07295](https://arxiv.org/abs/2410.07295) | Grammar boundaries, semantic validation, rollback, and continuation. | No demonstrated live-convention placement interaction. |
| **Hydra**, May 2026, [arXiv:2605.15238](https://arxiv.org/html/2605.15238v1) | Compiler feedback during generation, checkpoint rollback, and diagnostic comments appended to a retained code prefix before continuation. Compiler-style inline hints are already present. | Reactive compiler diagnostics differ from prospective convention reminders. |
| **Can We Steer Reasoning Direction by Thinking Intervention?**, Findings EMNLP 2025, [DOI:10.18653/v1/2025.findings-emnlp.209](https://aclanthology.org/2025.findings-emnlp.209/) | Interventions during generation, including position, style, dynamic triggers, and single versus repeated delivery. | Reasoning tasks rather than session-governed code units. The proposal’s characterization of this family as merely fixed text at a fixed trigger is too restrictive. |
| **SafeRemind**, January 2026, [arXiv:2601.03662](https://arxiv.org/html/2601.03662v1) | Reminder placement during generation, newline/entropy triggers, and comparisons involving intervention frequency and channel. | Safety reminders rather than evolving coding conventions. |
| **Answer Engineering**, June 2026, [arXiv:2606.21121](https://arxiv.org/html/2606.21121v1) | Scoped micro-rules, executable triggers, insertion/replacement, rollback, and external protocol memory. It also includes a software-engineering example and proposes rule-lifecycle management. | Its evaluation does not establish D’s specific session-rule × code-unit interaction. Lifecycle management is partly future work. |
| **TRACE**, June 2026, [arXiv:2606.13174](https://arxiv.org/html/2606.13174v1), and **ZORO**, April 2026, [arXiv:2604.15625](https://arxiv.org/html/2604.15625v2) | Turning corrections into scoped constraints; updating or superseding rules; attaching rules and verification to agent execution. | Agent/workflow boundaries rather than every syntactic unit inside a completion. |
| **FLARE**, EMNLP 2023, [DOI:10.18653/v1/2023.emnlp-main.495](https://aclanthology.org/2023.emnlp-main.495/), and **DRAGIN**, ACL 2024, [paper](https://aclanthology.org/2024.acl-long.702/) | Supplying relevant external information during generation according to the current generation need. FLARE anticipates an upcoming sentence and can regenerate it. | Retrieved knowledge rather than session conventions. |
| **Selective Prompt Anchoring**, ICML 2025, [paper](https://proceedings.mlr.press/v267/tian25a.html) | The exact motivation that growing generated code dilutes influence from the original prompt, plus a decoding intervention to counter it. | Attention/decoding control rather than local textual cues. |
| **Remember When It Matters**, July 2026, [arXiv:2607.08716](https://arxiv.org/html/2607.08716v1) | Maintained memory plus timely reminders to an otherwise unchanged action agent, evaluated on long-horizon tasks. | Between-action intervention rather than syntactic insertion. |
| **Kernel-Managed Shared Memory**, September 9, 2026, [arXiv:2609.10144](https://arxiv.org/abs/2609.10144) | System-managed retrieval and injection of relevant persistent information. | Personalization and system-level memory, not D’s code-unit experiment. |

An exact-match search for “session conventions per governed unit inside one completion” sets the novelty bar too conveniently. Changing the source of a rule from a protocol file to a session register, and changing a trigger to `def`, is not automatically a meaningful contribution.

The defensible remaining claim is:

> At equal information and comparable cost, aligning live conventions with the code decisions they govern produces a useful improvement that ordinary reminders and unaligned delivery do not produce.

No source I found conclusively disposes of that claim. No pilot establishes it either. The [proposal’s registration](/home/bmarti44/stencil-llm/results/reviews/2026-09-12-direction-proposal-rev2.md) still allows a positive primary score with all proposed interactions null. Such a result could establish utility for a package while leaving its claimed nontrivial recombination unexplained.

**The pilot evidence shows consequential intervention, but it does not isolate a placement advantage.**

There is no fair placement comparison in v3–v6. These are successive debugging experiments on exposed items, with changes to content, filtering, channel, tokenization, and delivery policy. Earlier pilots did contain item-level gains; a blanket account in which every focal output always lost would be false. The [root-cause review](/home/bmarti44/stencil-llm/results/reviews/2026-09-12-focal-rootcause-astra.md) documents why those gains did not qualify the mechanism.

For v6, independently reproducing the two scoring procedures gives:

| Arm | Mean pilot all-check score | Mean existing query-required score |
|---|---:|---:|
| Before-generation reminder | 48.5% | 33.3% |
| Focal header | 34.3% | 52.0% |
| Focal phased | 22.2% | 27.8% |
| User-turn phased | 41.1% | 63.6% |

These columns summarize the **same three outputs per arm**. They are not independent experiments.

The discrepancy is substantive. The [pilot scorer](/home/bmarti44/stencil-llm/scripts/focal_quicklook.py:48) rewards conventions for structures the query did not request. The established [required score](/home/bmarti44/stencil-llm/src/stencil/memorycode.py:380) gates on the requested structure. On 314-49, the reminder produces a class instead of the required free function; its required score becomes zero. User-turn delivery then appears to gain 30.3 percentage points on the mean, driven by one item. This prevents using the original negative means as decisive evidence against placement.

But that apparent rescue exposes the larger problem:

- On **314-49**, the user-turn output scores **10/11** on required checks while decorating the function with its own undefined name.
- After removing decorators and isolating the function body for diagnosis, it returns **0 for `I`, −1 for `IV`, and 1 for `VI`**. The correct values are 1, 4, and 6.
- On **186-14**, all three focal arms use an unbound `retry` decorator.
- The phased comment arm on 314-49 produces the cue-imitation loop and exhausts its generation allowance.

These findings are reproducible from the [v6 artifact](/home/bmarti44/stencil-llm/results/focal/quicklook-v6.json) and detailed in the [independent review](/home/bmarti44/stencil-llm/results/reviews/2026-09-12-focal-v6-review-astra.md:295). The isolated-body test diagnoses algorithmic failure; it does not certify the baseline’s whole program.

The checker makes this outcome possible. It recognizes decorator names without establishing that decorators are available or correctly applied. It ignores `ImportFrom` in relevant import checks and treats some nested functions differently from the runtime’s detector. **Checker compliance is an incomplete proxy for implementing the instruction correctly.**

The comparison also changes information. The reminder receives 22/9/9 rules across the three items; comment arms deliver 11/6/4, and the user arm 11/6/9. A gain could come from excluding irrelevant rules. A fair relevant-only reminder might obtain that gain without mid-generation intervention.

Furthermore, the user channel rebuilds the prompt and re-prefills the retained assistant prefix. Its rules are not necessarily adjacent to the current code unit. Its avoidance of catastrophic imitation is useful engineering evidence, but it does not validate the proposed “one to three lines away” explanation. See the [runtime branch](/home/bmarti44/stencil-llm/src/stencil/focal_runtime.py:425).

**A syntactic boundary is often later than the decision the convention constrains.**

This is the strongest mechanism objection.

A decorator convention can require an earlier import. A naming convention affects callers as well as definitions. A class convention can require choosing a class before any class boundary exists. A required `try` block changes the organization of a body, not merely its first token.

Consider an already generated call to `f`, followed later by its definition. If the reminder at `def f` demands the name `x_f`, rolling back only the definition cannot repair the earlier call. Delivering the cue at every definition does not solve the dependency.

A correct implementation must sometimes supply the obligation earlier or revise a larger dependency region. Both options exceed the proposal’s simple account of complete coverage through local unit triggers.

This also weakens the diagnosis drawn from Exp 4C. The [result](/home/bmarti44/stencil-llm/results/memorycode-long/RESULTS-4C.md) was +2.05 percentage points, with a 95% interval of approximately −0.07 to +4.16 points. Its failure guard was inconclusive, and 119/278 outputs hit the cap. Restating guidelines before violating them does not identify prospective memory as the sole bottleneck. It is also compatible with conflict, inadequate implementation knowledge, poor planning, and insufficient generation budget.

**Research outside AI supports contingent cueing, not a general rule that later and closer is better.**

| Evidence | What it supports—and what it does not |
|---|---|
| **Spatial contiguity meta-analysis**, 58 comparisons, 2,426 participants, effect size *g* = .63. [DOI:10.1007/s10648-018-9435-9](https://link.springer.com/article/10.1007/s10648-018-9435-9) | Integrating related instructional material can materially help human learning. This is evidence against dismissing placement as inherently cosmetic. It does not establish an equivalent token-distance effect in transformers. |
| **Kester, Kirschner & van Merriënboer**, troubleshooting experiment, 85 students. [DOI:10.1016/j.cedpsych.2005.04.002](https://research.ou.nl/en/publications/just-in-time-information-presentation-improving-learning-a-troubl/) | Separating declarative and procedural information across time improved transfer. The predicted additional advantage of declarative-before/procedural-during ordering was **not supported**. D therefore needs a staggered but unaligned control. |
| **Ballhausen et al.**, prospective memory and maintenance load. [DOI:10.3758/s13421-017-0720-5](https://pubmed.ncbi.nlm.nih.gov/28600628/) | Focal-cue benefits appeared under low maintenance load and disappeared under high load. Recognizing a cue does not eliminate the resources needed to execute the intention. This weakens D’s confident H3 prediction. |
| **Bailey & Konstan**, interruption experiment. [DOI:10.1016/j.chb.2005.12.009](https://www.sciencedirect.com/science/article/pii/S074756320500107X) | Delivering interruptions at task boundaries reduced disruption compared with interrupting ongoing work. It does not imply that every narrow syntactic boundary is a good interruption opportunity. |
| **Kawamoto et al.**, 70-trial clinical decision-support review. [DOI:10.1136/bmj.38398.500764.8F](https://www.bmj.com/cgi/reprint/330/7494/765) | Workflow integration and delivery at the decision point were associated with successful systems. These were bundled system features, not an isolated causal estimate of reminder timing. |
| **Shojania et al.**, point-of-care reminder review. [DOI:10.1503/cmaj.090578](https://pubmed.ncbi.nlm.nih.gov/20212028/) | Median improvement in process adherence was 4.2 percentage points, with substantial variation. Timeliness does not guarantee a large effect or a better final outcome. |
| **Strom et al.**, randomized prescribing-alert trial. [DOI:10.1001/archinternmed.2010.324](https://pubmed.ncbi.nlm.nih.gov/20876410/) | A strong alert greatly improved the targeted prescribing behavior, but the trial stopped early after treatment delays. This is a direct warning about substituting local compliance for overall success. |
| **HeartSteps**, micro-randomized intervention study. [DOI:10.1093/abm/kay067](https://pmc.ncbi.nlm.nih.gov/articles/PMC6401341/) | Reminder effects depended on intervention type and diminished over time; the pooled average effect was uncertain. Human habituation is not evidence of transformer habituation, but uniform benefits from repeated cues should not be assumed. |

The AI evidence gives similar reasons for restraint. Thinking Intervention found advantages for earlier and single interventions in relevant comparisons. SafeRemind explicitly studies placement and repetition rather than treating maximum cue coverage as desirable. Answer Engineering reports cases where repeated successful detection and local repair failed to overcome earlier commitments, and cases where intervention damaged previously correct answers. These are close relatives of D’s observed problems. [Thinking Intervention](https://aclanthology.org/2025.findings-emnlp.209/), [SafeRemind](https://arxiv.org/html/2601.03662v1), [Answer Engineering, §6.8](https://arxiv.org/html/2606.21121v1).

There is favorable evidence too. Selective Prompt Anchoring demonstrates that maintaining prompt influence can improve code generation. But the proposal overstates the coding-configuration study: its reported per-function association is not a controlled demonstration of monotonic decay inside one completion. Transposing that association into H1 remains a hypothesis. [Selective Prompt Anchoring](https://proceedings.mlr.press/v267/tian25a.html), [Instruction Adherence, arXiv:2605.10039](https://arxiv.org/abs/2605.10039).

**My 20% estimate grants repairs to the implementation.**

By a fair positive screen, I mean a practically meaningful improvement on fresh, long coding sessions, against the same artifact unmodified, accompanied by:

- Functional correctness and instruction compliance measured together.
- A competitive, relevance-matched before-generation reminder.
- Comparable resource allowances.
- Evidence for the particular placement interaction claimed as the contribution.

My subjective uncertainty range is roughly **10–35%**. It is not a confidence interval or a posterior calculated from the pilot wins.

The estimate is low even granting correct lexing, tokenization, rollback, scoring, and removal of the observed imitation failure:

1. Cue arrival is demonstrated; useful integration remains uncertain.
2. Some rules arrive after dependencies have been chosen.
3. Rules that are easy to recognize can be difficult to combine with correct algorithms.
4. Oracle pilots bypass admission, relevance, supersession, and scope errors.
5. The experiment still has to transfer from terminal code generation to a genuinely evolving agentic session.

The strongest positive evidence for the owner’s broader objective actually concerns intervention **before the next agent action**. Remember When It Matters reports Terminal-Bench pass rates rising from 37.6% to 45.9% with an unchanged action agent. However, it uses an additional strong memory model, and its ablation does not show selective reminders uniformly beating always-inject reminders: the task-weighted figures are 61.2% versus 61.5%. It supports maintained, actionable memory more strongly than D’s particular timing claim. [arXiv:2607.08716](https://arxiv.org/html/2607.08716v1).

**I would investigate two alternatives, with explicit opportunities to kill them cheaply.**

Neither is certified to satisfy all the criteria. Claiming that now would repeat the proposal’s mistake. These are the two specific recombinations I currently find hardest to dismiss.

**1. Deliver obligations before their dependencies are committed.** Maintain session rules, but map each rule to the earliest decision that must account for it: choosing an interface, importing a decorator, selecting a structure, issuing an edit, or defining a local name. Include the dependencies needed to execute the rule. Use bounded verification and repair, with identical repair allowances in comparison arms.

This recombines TRACE’s rule lifecycle, MGD’s program context, IterGen/Hydra’s controlled validation and rollback, and the distinction between planning information and procedural information studied in education. Generic rules attached to plans are already covered by ZORO; that cannot be the novelty claim.

The specific gap is whether **dependency-aware timing** improves functional compliance over both syntactic timing and an equally relevant up-front packet, particularly when a session rule changes after earlier code has been written.

The first cheap disconfirming test should use roughly 24–32 small, independently constructed development tasks with executable tests. Half should involve genuinely local conventions; half should involve imports, callers, or interfaces. Use an oracle dependency map first. Compare up-front delivery, syntactic delivery, and dependency-aware delivery, including a matched staggered control.

Kill the direction if oracle dependency timing produces no practically useful advantage or introduces functional harm. Do not build a learned router to rescue a failed oracle test.

I cannot presently disprove the specific interaction because the repository supplies concrete dependency failures, while the cited literature does not settle this controlled comparison under evolving session rules. Its benefit would change when the artifact intervenes and what information it supplies.

**2. Retain current rules and attach examples whose validity is rechecked after changes.** Keep the authoritative rule in prose. Add a minimal, previously successful session example only while its rule version, dependencies, and relevant tests remain valid. Invalidate or replace it when those conditions change.

This recombines worked examples, executable verification, TRACE’s correction lifecycle, and temporal invalidation such as [Zep, arXiv:2501.13956](https://arxiv.org/abs/2501.13956). It also fits the coding evidence from **Show and Tell**, where rules plus examples outperformed either alone. That paper weakens the proposal’s fallback of examples *instead of* rules. [arXiv:2511.13972](https://arxiv.org/abs/2511.13972).

The gap is not “examples help.” It is whether **checking example validity against changed session conventions prevents harmful copying while preserving the benefit of demonstrations**, under equal budgets.

The first cheap test should use independent development sessions containing rule changes followed by related but algorithmically different coding tasks. Compare rules alone, rules plus ordinary examples, and rules plus revalidated examples. Measure task tests, convention compliance, and propagation of obsolete patterns.

Kill the novelty claim if ordinary rules-plus-examples performs equally well. Kill the usefulness claim if selecting or maintaining examples costs more than the benefit, or encourages copying an inappropriate algorithm.

I cannot presently disprove this narrower interaction. It directly addresses the pilots’ gap between naming a decorator and supplying a usable implementation. It still needs to beat ordinary few-shot prompting and existing memory systems.

**Several issues deserve more attention before another screen.**

- **The current benchmark can reward the wrong product.** A function with 10/11 convention checks and an incorrect algorithm is not a near-success for the owner’s objective. Task success must participate in acceptance.
- **Long input is not a long agentic session.** The latter includes edits, tool failures, changing requirements, obsolete memories, and recovery. Oracle rules attached to one final generation leave most of that untested.
- **The proposed decay measurement can manufacture its own pattern.** If a check requires every generated unit to comply, whole-output success decreases with more units even when each unit has constant success probability: under a simple independent illustration, it is \(p^n\). Measure individual opportunities and control their number; do not infer fading from aggregate failure.
- **Output structure is itself affected by treatment.** Comparing compliance only on units a model elects to generate can reward omission of difficult units. Required opportunities need an external definition.
- **On/off proves a package effect, not the proposed explanation.** A positive package comparison could come entirely from relevance filtering, repetition, extra computation, or better wording.
- **“Correctly built D” needs a fixed boundary.** Adding global planning, dependency repair, example memory, and adaptive scheduling indefinitely would make D impossible to disprove by changing what D means.
- **A remaining generation-unseen item is not automatically an untouched confirmation item.** Preserve the exposure history, freeze the design, and check whether the available sample can support the registered harm guard.

I would keep the current configuration stopped. The next experiment worth buying is an oracle test of whether delivering dependency-complete obligations earlier preserves functionality. If a matched relevant reminder performs equally well, retire the special delivery claim.
