**Rev 5 does not satisfy all the owner’s criteria, either now or merely conditional on passing its pre-check.** The decisive failure is the claimed ≥60% chance of producing the intended artifact. The narrowing is legitimate in principle, and a narrow recombination claim survives the literature search. The pre-check does not establish enough to support the probability claim, and the confirmation does not establish everything the artifact’s claim requires.

**I retract my earlier provisional 60–75% estimate for this concrete protocol.** I did not adequately account for the strength of the competence evidence, the difficulty of beating matched SFT, or the joint acceptance rule’s power. The author followed the direction I suggested. That does not make my earlier forecast sound.

I reviewed the proposal, all six prior reviews, the governing process and state, the deployed session implementation, and the recorded package results. I did not read `data/bench/`. Research cutoff is **September 12, 2026**, the environment’s current date; the September 13 filenames do not establish a later cutoff.

**1. The narrowing is defensible; its claimed evidential consequence is not.**

Choosing a domain where a small model already possesses the underlying coding competence is sensible. Domain restriction is not inherently a meaningless permutation or evidence manipulation. Missing-record behavior, exception propagation, validation placement, return types, logging, dependencies, and mutability can matter in real maintenance. I found no evidence that these eight families were selected using evaluation outcomes.

However, [rev 5’s domain table](/home/bmarti44/stencil-llm/results/reviews/2026-09-13-direction-proposal-rev5.md:34) freezes **family names and examples**, not a complete operating distribution. It leaves unspecified:

- The frequency and difficulty of each family.
- How many contracts apply simultaneously.
- Scope precedence, overlapping exceptions, exception expiration, and reinstatement semantics.
- Whether changes require updating callers, tests, serialization, and existing stored state.
- What constitutes a distinct project or solution family.
- How much irrelevant history, code, and tool output must fit alongside the contracts.

These choices determine whether the domain is useful maintenance or a collection of easily recognized substitutions. Calling the schema “closed” does not resolve them.

The claim that all eight concern behavior “not style” is also too broad. A naming convention can be purely stylistic unless public callers and compatibility are involved. A dependency preference can be satisfied superficially without exercising the fallback. The tests and task construction decide whether these are behavioral requirements.

The competence check is a legitimate **development stop screen**. Authored, disjoint development tasks can establish feasibility without contaminating a later evaluation. But **16/32 joint successes does not establish reliable competence across this domain**.

I independently computed the following exact binomial intervals. They assume independent tasks sampled from a specified target distribution—an assumption the proposal has not yet secured.

| Pre-check result | Observed success | Exact two-sided 95% interval |
|---|---:|---:|
| Minimum passing joint result: 16/32 | 50.0% | 31.9–68.1% |
| Minimum passing function-only result: 20/32 | 62.5% | 43.7–78.9% |

A model with a true 40% joint success rate passes the **J component alone** about 16.5% of the time. A model with a true 50% rate passes that component about 57.0% of the time. The function requirement adds information, but it does not repair the uncertainty about joint competence.

Even if there were four tasks per family—which is not specified—a model could obtain all sixteen joint successes from four families and fail every task in the other four. Aggregate eligibility would still be possible.

There is also a mismatch between immediate competence and session competence. If individual requests each succeed with probability 0.5, two independent successes occur with probability 0.25. Actual requests need not be independent; that is precisely why a single-request check cannot establish the session outcome.

**Is the threshold right?** It is defensible as a cheap rule for abandoning an obviously unsuitable configuration. It is unsupported as the threshold that moves this program above 60%. No cited research calibrates that implication.

Passing with 16/32 and passing with 31/32 should produce different forecasts. Rev 5 treats both as the same evidential condition. Conversely, failing would establish a negative about **this trunk, task distribution, prompting, and budget**, not every possible 4B trunk.

**2. Fresh search leaves a narrow gap, with substantial prior coverage.**

The table distinguishes what each source actually covers from what remains unestablished.

| Source and identifier | Claim it covers; remaining difference |
|---|---|
| **IOPO**, [arXiv:2411.06208](https://arxiv.org/html/2411.06208v2) | Already constructs the four combinations of two instructions and two responses, preferring matched over mismatched combinations. Reversing which response is preferred when the instruction changes is established prior art. It does not establish scoped, temporal repository maintenance. |
| **RPO**, [arXiv:2505.22172](https://arxiv.org/html/2505.22172v1) | Reverses constraints to construct preference pairs and trains multi-turn system-constraint following. It covers constraint reversal and persistence training. It does not supply rev 5’s complete executable maintenance setting or its matched-positive SFT comparison. |
| **Cross-Relational Preference Learning**, **August 29, 2026**, [arXiv:2608.29352](https://arxiv.org/html/2608.29352v1) | The strongest fresh overlap: perturb related instructions, sample responses across their permissible regions, and verify atomic constraints. This substantially narrows any claim around counterfactual preference construction plus verification. Temporal scope changes coupled to functioning repository edits remain outside its demonstrated claim. |
| **CodeUltraFeedback**, [arXiv:2403.09032](https://arxiv.org/abs/2403.09032) | Coding preferences, SFT, DPO, and improved functional correctness already coexist. “Preference training for code under user requirements” is not the novelty. Its preferences are not rev 5’s executable temporal contract histories. |
| **SelfCodeAlign**, [arXiv:2410.24198](https://arxiv.org/abs/2410.24198) | Execution-filtered synthetic code training already works through supervised learning. This is both prior coverage and a reason to take `sft` seriously. |
| **Ghost Attention**, [Llama 2, arXiv:2307.09288, §3.3](https://arxiv.org/html/2307.09288v2) | Training multi-turn instruction persistence through context distillation predates this proposal. Persistence alone does not establish authorized deactivation or scoped exceptions. |
| **Supersede**, [arXiv:2606.27472](https://arxiv.org/html/2606.27472v1) | Direct predecessor for learning temporal updating with a small LoRA-adapted model and bounded memory. It demonstrates updating training, not reliable functional code editing. Its transfer results are a warning discussed below. |
| **PACT**, [arXiv:2510.12047](https://arxiv.org/html/2510.12047v1) | Explicitly evaluates whether generated code respects contracts as well as functionality. Contract-aware code generation is established territory. Its methods do not establish temporal counterfactual adapter training. |
| **TRACE**, [arXiv:2606.13174](https://arxiv.org/abs/2606.13174) | Compiles user corrections into runtime enforcement for coding agents. Maintaining and enforcing evolving coding rules is already a systems contribution. Its mechanism differs from training the patch-generating policy. |
| **ZORO**, [arXiv:2604.15625](https://arxiv.org/abs/2604.15625) | Connects active coding rules, implementation evidence, and evolving user feedback. Rule-aware editing agents are not an empty prior-art category. It does not demonstrate rev 5’s objective. |
| **TIMER**, [DOI:10.1038/s41746-025-01965-9](https://www.nature.com/articles/s41746-025-01965-9) | Time-aware instruction tuning for longitudinal clinical records. Temporal training is not unique to coding or conversational preference research. Clinical timeline reasoning is not instruction supersession, so this is adjacent evidence, not an exact predecessor. |
| **GRAFT**, **September 7, 2026**, [arXiv:2609.07160](https://arxiv.org/abs/2609.07160) | Combines constraint-aware SFT and preference optimization for instructions anchored within diffusion-model outputs. It covers another contemporary recombination of these training ingredients, not temporal autoregressive code editing. |
| **CAPTURE**, **September 2, 2026**, [arXiv:2609.02265](https://arxiv.org/abs/2609.02265) | Models genuine preference changes versus temporary context and poisoned memory, with counterfactual auditing. Authenticity and scope cannot generally be reduced to recency. It does not train counterfactual code-patch preferences. |
| **PlanFence**, **September 3, 2026**, [arXiv:2609.03340](https://arxiv.org/abs/2609.03340) | Shows how an agent can have current facts while executing a plan derived from obsolete requirements. This attacks the assumption that correct remembered contracts imply correct subsequent action. Its controlled systems results are not a general coding-accuracy estimate. |
| **Synthetic Worlds / Synapse**, [arXiv:2609.00184](https://arxiv.org/abs/2609.00184) | Uses coherent synthetic timelines for learning updated knowledge. It is relevant to synthetic temporal training, but changing parametric knowledge is different from applying a new session-local coding rule. |

I did **not** find a verified predecessor demonstrating the complete combination of:

> A small optional adapter learning temporal and scoped contract selection, producing executable repository edits, and outperforming SFT on the same verified histories and solutions.

That is the surviving claim. It is substantially narrower than preference reversal, instruction updating, contract-aware coding, or verification individually.

**3. The training intervention is real, but SFT already receives the central counterfactual information.**

Suppose history \(h_0\) requires patch \(a\), while an authorized change produces history \(h_1\), requiring patch \(b\).

Ordinary SFT on the specified positives optimizes:

\[
-\log \pi(a\mid h_0)-\log \pi(b\mid h_1).
\]

It already teaches **different actions under different histories**.

The counterfactual objective additionally pushes down the stale alternative under each history, typically using reference-relative preference scores:

\[
a \succ b\mid h_0,\qquad b \succ a\mid h_1.
\]

Those additional gradients are real. They can improve discrimination between plausible alternatives. They are not mathematically identical to positive-only SFT.

But three limits matter:

- The counterfactual history-to-solution mapping is shared by both arms.
- On a simple deterministic task distribution, both objectives can approach the same correct conditional mapping.
- If `cf` also receives a consistency objective, different sampling, or different effective exposure, the comparison identifies the **whole training package’s effect**, not preference reversal alone.

**My prediction:** `sft` will obtain much of the improvement over `off`. It learns the patch conventions, the supported scope vocabulary, and the association between changed instructions and changed solutions. `cf` may improve stale-alternative rejection, but a large, dependable advantage over a properly trained `sft` is less likely than the proposal implies.

The relevant research supports that prediction without guaranteeing a tie. RPO reports advantages for preference training, but its training conditions do not reproduce rev 5’s tightly matched control. Conversely, **Bayesian teaching enables probabilistic reasoning in large language models**, [DOI:10.1038/s41467-025-67998-6](https://www.nature.com/articles/s41467-025-67998-6), teaches sequential belief updating through SFT and reports similar results with DPO and LoRA alternatives. That is direct evidence that carefully constructed updating examples can matter more than choosing a preference objective.

Thus **meaningless permutation is NOT DISPROVED in advance**, but the burden falls on the incremental result against `sft`. Renaming the examples “counterfactual” does not meet it.

There is a further evidential limit: **confirmation contains no SFT arm**. A noisy screen can select `cf` even when its population performance equals `sft`; confirmation can then correctly establish `cf > off`. That result would confirm a useful trained package, while leaving the distinctive contribution supported only by the screen. I am not proposing another arm. I am limiting what the existing design can establish.

**4. Eight families can be useful and significant. Counting families does not establish either.**

This domain is not inherently a toy. Small packages can contain important APIs, and exception handling, return shapes, dependency changes, and mutability can require coordinated edits. Repository-level maintenance has substantive dependency problems, as illustrated by **CodePlan**, [arXiv:2309.12499](https://arxiv.org/abs/2309.12499).

The distinction is in what successful execution requires:

| Potentially substantive artifact | Weak artifact that the present wording also permits |
|---|---|
| Keeps a scoped exception local while preserving the default elsewhere | Recognizes a repeated phrase and substitutes one token |
| Updates affected callers and preserves unrelated behavior | Changes only the demonstrated function |
| Handles a later revision against its own earlier edits | Receives an already-correct frozen repository history |
| Preserves the distinguishing instruction through actual compaction | Answers two requests after a transcript that never strains memory |
| Improves joint success across the declared distribution | Wins mainly on a few easy families |

The confirmation’s lower-bound-above-zero rule also does not establish a practically significant difference. For example, **11 J wins and zero losses out of 256** is a **4.30-point observed improvement**. It passes exact McNemar and even the conservative Clopper–Pearson difference construction discussed below. Whether that gain warrants the artifact depends on absolute reliability and practical costs.

“Useful” remains plausible. “Significant difference” remains plausible. **Neither is certified merely by the proposed word PROVEN.**

**5. The cross-disciplinary evidence supports the problem, not a ≥60% forecast.**

The proposal’s cognitive-science motivation survives scrutiny, with restrictions:

- **Retrieval-practice transfer:** Pan and Rickard’s meta-analysis finds transfer benefits that depend on task relationships and learning conditions. It does not establish that explicitly rejected stale code patches outperform SFT on the same current-rule examples. [DOI:10.1037/bul0000151, author manuscript](https://pdf.retrievalpractice.org/transfer/Pan_Rickard_2018.pdf).
- **Completed intentions:** Strongly encoding an intention can increase later commission errors after it is completed. That supports treating retention and deactivation as separate problems. It also warns that stronger instruction learning can strengthen obsolete responses. [Scullin et al., PMCID:PMC3669231](https://pmc.ncbi.nlm.nih.gov/articles/PMC3669231/).
- **Extinction and context:** Learning to suppress an old response need not erase it; changes of context can permit its return. This motivates concern about compaction and paraphrase, but supplies no numerical probability for transformer behavior. [Bouton, DOI:10.1016/S0006-3223(02)01546-9](https://pubmed.ncbi.nlm.nih.gov/12437938/).
- **Metamorphic testing:** Controlled input transformations with specified output relationships are established software-testing methodology. Counterfactual histories and irrelevant-history invariance fit this logic. They help define informative examples; they do not guarantee that a learner acquires the intended abstraction. [Chen, Cheung and Yiu, HKUST-CS98-01](https://www.cse.ust.hk/faculty/scc/publ/CS98-01-metamorphictesting.pdf).

The strongest favorable small-model evidence remains **ComplexConstraints**: Qwen3-4B improves by 15.5 points on a per-criterion measure and 7.1 points on an independent multi-turn-context evaluation after LoRA-based training. Those are relevant positive results. They are single-seed results, and per-criterion compliance is easier than conjunctive functional session success. [arXiv:2606.09118](https://arxiv.org/html/2606.09118v1).

The strongest directly relevant caution is **Supersede**. Its procedural training reward rises substantially, while reported held-out real-world correctness changes from **7/78 to 13/78**. That is evidence of some transfer, with low absolute reliability. Also, its actual main training used current-answer correctness; the explicit stale-answer penalty was an ablation, not the main demonstrated training recipe. It cannot support an exaggerated claim that directly penalizing obsolete instructions has already solved transfer. [arXiv:2606.27472](https://arxiv.org/html/2606.27472v1).

The repository supplies another caution. [Exp 4C](/home/bmarti44/stencil-llm/results/memorycode-long/RESULTS-4C.md:16) ended **NOT PROVEN, FINAL**, with roughly a two-point average compliance improvement and a failed noninferiority gate. Those outcomes do not estimate rev 5’s functional competence—the tasks and metrics differ—but they refute treating the existing package as an already-established reliable session foundation.

My present forecasts are:

| Event | Subjective probability |
|---|---:|
| Pre-check passes | **75%** |
| Screen passes, conditional on the pre-check passing | **45%** |
| Confirmation reads PROVEN, conditional on both preceding passes | **60%** |

These are research judgments, not confidence intervals or probabilities extracted from published effect sizes. The confirmation forecast grants reasonable resolution of the unspecified interval and function guard; the literal text does not define a unique acceptance event.

By the probability chain rule:

\[
P(\text{successful path})=0.75\times0.45\times0.60
=\mathbf{20.25\%}.
\]

Conditional only on passing the pre-check:

\[
P(\text{successful path}\mid\text{pre-check pass})
=0.45\times0.60
=\mathbf{27\%}.
\]

Those products do not assume independent stages; the probabilities are conditional. They are generous proxies for the owner’s complete artifact, because a PROVEN reading would still have the contribution and usefulness limits described above.

**Required: ≥60%. Rev 5 reaches neither 60% now nor 60% conditional on the stated pre-check passing.** Stronger actual pre-check results could change the forecast, but merely crossing its binary threshold does not.

**6. The experiment has unresolved threats to interpretation, not just implementation details.**

The following concerns apply to the existing arms and stages.

| Issue | What would invalidate or limit the conclusion |
|---|---|
| **Generator leakage** | Different repository names and random seeds can preserve the same dependency graph, edit skeleton, history language, and solution. Such a split measures transfer within the generator, not necessarily across the claimed solution families. |
| **Execution filtering** | Filtering training to successful solutions can disproportionately retain easy families or stereotyped patches. If evaluation is similarly filtered using model success, competence and improvement become selected outcomes. |
| **Template clustering** | Multiple sessions derived from a shared template may share failure causes. Their count cannot automatically support the claimed population-level precision. |
| **Counterfactual validity** | Both designated positives must execute correctly under their respective contracts; each stale negative must fail the intended current contract. Otherwise the preference signal can encode ordinary code quality, unsatisfiable tasks, or arbitrary labels. |
| **Shortcut features** | Wording, identifiers, patch length, update position, or formatting can reveal which patch wins. The observed gain could be template classification without transferable scope handling. |
| **SFT compute matching** | Equal steps, equal examples, and equal elapsed time are different matches. Preference training processes additional completions and possibly reference scores. The accounting and exposure must be explicit. |
| **SFT data matching** | Both arms must receive both positive twin histories and equivalent relevant augmentations. Otherwise `cf` gets more information, and the control cannot answer the stated question. |
| **Training specification** | Dataset size, loss formula and weights, preference temperature, adapter configuration, epochs, checkpoint choice, and effective batch are not fixed. The proposal names an objective family, not an executable training protocol. |
| **Adapter-off competence** | Bypassing LoRA preserves trunk weights, but does not establish that the common session renderer gives the trunk usable inputs. An immediate-instruction pre-check does not validate the deployment memory path. |
| **Memory information** | Shared memory controls information differences between arms. It does not ensure that either receives the instruction needed to choose the correct patch. |
| **Compaction** | Twelve to twenty turns do not guarantee even one meaningful compaction. The proposal does not fix repeated compactions or preservation of update provenance. |
| **Two live requests** | They must evolve each arm’s own repository, with failures retained. Resetting before request two, supplying a gold repair, or checking only the terminal state changes the question. |
| **Unit of analysis** | The pair of live requests is one session outcome. Counting them as independent observations doubles the nominal sample without doubling independent sessions. |
| **Tests and repair** | Private tests must remain private through tool output and repair. Public tests, repair allowances, dependencies, deadlines, and patch application must be identical across arms. |
| **Function guard** | Its noninferiority margin, confidence level, interval method, and handling of observed declines are unspecified. Consequently PROVEN is not fully defined. |
| **Contribution claim** | Confirmation against `off` cannot by itself establish advantage over ordinary SFT or isolate deactivation as the cause. |

Shared templates do **not automatically** make every within-generator experiment invalid. Independent draws from a fixed, explicitly limited generator can support conclusions about that generator. The error is claiming broader independent maintenance sessions without matching the sampling and uncertainty calculation to that claim. This is the relevant lesson from pseudoreplication, not “eight families means N=8.” [Hurlbert, DOI:10.2307/1942661](https://esajournals.onlinelibrary.wiley.com/doi/10.2307/1942661).

Several issues deserve more detail.

**The deployed memory implementation does not resolve supersession.** The current [session code](/home/bmarti44/stencil-llm/deploy/stencil_focus/stencil_focus/focus_session.py:16) collects evicted user instruction sentences and packs them newest-first under an “Earlier instructions still in force” header. It is not a semantic current-contract register. Its packing also stops when the next whole sentence does not fit.

That implementation can retain obsolete instructions, lose the distinguishing replacement, or frame both as active. Its [generation wrapper](/home/bmarti44/stencil-llm/deploy/stencil_focus/stencil_focus/modeling_stencil_focus.py:62) does not by itself implement a repository-editing loop that appends and executes every generated action.

If compaction maps two histories requiring different patches to the **same delivered model input**, no adapter can reliably recover the missing distinction. Supplying an oracle current-contract register would resolve the information problem by externally performing part of the proposed task. That would need to be reflected in the claim.

The 4,096-token ceiling must include code, conversation, reminders, tool results, formatting, and reserved generation. Short patches reduce output cost. They do not guarantee that the necessary input fits.

**Two live requests establish only limited exposure to the model’s own actions.** The frozen prefix avoids a large amount of endogenous error accumulation. Neither “two live requests” nor “12–20 turns” establishes long-session reliability through repeated updating and compaction. Round 6 explicitly identified that distinction; rev 5 does not settle it. [Round 6](/home/bmarti44/stencil-llm/results/reviews/2026-09-13-direction-search-rev6-astra.md:203).

**The functional outcome needs a coherent definition.** Changing `None` to `KeyError` changes intended behavior. Old tests cannot remain authoritative for the changed behavior, while new contract-specific tests cannot be used to imply preservation of unrelated functionality. The function-only guard needs a defined set of protected requirements under each authorized contract state.

It also measures an average. Equal numbers of repaired and newly broken repositories can produce no net function decline. That is not “no damage.” Both models can be unreliable and still satisfy noninferiority.

**The quoted power is not the power of the stated acceptance rule.**

I independently reproduced the proposal’s exact McNemar numbers. They are correct for that test at a true ten-point improvement.

But the proposal also requires a conservative interval entirely above zero. The repository contains multiple interval implementations: [SC1 uses a conservative Clopper–Pearson difference](/home/bmarti44/stencil-llm/src/stencil/sc1.py:649), while [FOCUS2 uses a Tango inversion](/home/bmarti44/stencil-llm/src/stencil/focus2.py:996). “Conservative paired interval” does not select one.

If rev 5 uses the SC1 construction—simultaneous bounds on win and loss probabilities—the exact acceptance probabilities are substantially lower:

| Discordance at true +10-point J effect | Exact McNemar power | Probability CP-difference lower bound exceeds zero |
|---|---:|---:|
| 20% | 94.7% | 71.0% |
| 30% | 81.3% | 46.6% |
| 40% | 68.8% | 34.9% |

These are calculations for that specified construction, **not a claim that every valid paired interval has this power**. They demonstrate why the interval must be named before quoting acceptance power.

The function guard reduces joint acceptance further. As an illustration, under no true function change, a five-point margin and a conventional two-sided 95% normal interval would pass with approximately 72%, 43%, or 31% probability at function discordance of 10%, 20%, or 30%, respectively. These are marginal illustrations, not quantities to multiply assuming independence.

A zero margin is different again: requiring the function interval’s lower endpoint to be nonnegative generally demands evidence of improvement, rather than ordinary noninferiority.

The wording also conflicts: the screen prohibits observed net decline; confirmation invokes statistical noninferiority; the kill rule says “Function-only decline → stop.” These can produce different decisions on the same records.

Finally, the screen is an investment gate. Five wins and zero losses against `off` yields exact two-sided \(p=0.0625\); three and zero against `sft` yields \(p=0.25\). Passing those thresholds is not strong evidence of superiority, and failing them is not equivalence. A literal observed tie is likewise not evidence that the population effects are equal.

Registering confirmation after a screen is not automatically invalid if confirmation remains untouched. But the interval, margin, sampling unit, and claim are currently unresolved. Rev 5 therefore overstates how fully it fixes the experiment.

**The GB10 budget is plausible in memory, unestablished in throughput.**

NVIDIA specifies **128 GB unified memory** and **273 GB/s memory bandwidth** for DGX Spark. Its advertised FP4 performance is not a BF16 LoRA-training throughput measurement. [NVIDIA specifications](https://www.nvidia.com/en-eu/products/workstations/dgx-spark/).

A roughly 4B-parameter BF16 trunk needs about 8 GB for weights. From the official Qwen3-4B configuration, a 4,096-token BF16 KV cache is about **0.56 GiB per sequence**, before other buffers. A 30 GB co-resident job therefore does not make this program inherently impossible. [Official Qwen3-4B configuration](https://huggingface.co/Qwen/Qwen3-4B/blob/3fb356690bbdae7353c94efb3eecdce276e6ed1c/config.json).

Training memory is another matter. Freezing weights removes their optimizer-state burden; it does not remove backward activations or base-model matrix operations. Preference comparisons increase processed sequences. Efficient attention, checkpointing, microbatching, and reference-score handling determine whether the implementation fits comfortably or fails.

Assuming confirmation retains the two-request session design, generation counts are:

- Pre-check: 32.
- Screen: \(3\times48\times2=288\).
- Confirmation: \(2\times256\times2=1,024\).
- Total: **1,344 generations**, before training-data generation.

After a 16-hour screen, a 40–60-hour total leaves a gross 24–44 hours for confirmation and remaining costs: about **84–155 seconds per confirmation generation**, before deducting other work.

The existing package measured a maximum of 68.689 seconds among eight capped timing calls, with a different co-resident workload. That demonstrates possible order of magnitude, not feasibility for this training objective and a 30 GB competing job. [Recorded timing](/home/bmarti44/stencil-llm/results/memorycode-long/RESULTS-4C.md:23).

The proposed timing pilot is appropriate. **The budget is not disproved, but no measured basis yet supports promising it.** Human effort to author genuinely different projects and validate their contracts is also outside the GPU-hour arithmetic.

**7. Verdict by owner criterion.**

Here, DISPROVED means the proposal fails the stated decision criterion on present evidence. It does not mean the experiment cannot succeed. NOT DISPROVED means the attempted objection did not defeat the prospective claim; it does not mean the result has already been demonstrated.

| Owner criterion | Rev 5 now | Conditional on the stated pre-check passing | Decisive reason |
|---|---|---|---|
| Novel recombination | **NOT DISPROVED** | **NOT DISPROVED** | A narrow gap remains around temporal, scoped rule selection coupled to executable repository edits and an incremental SFT comparison. |
| Useful | **NOT DISPROVED** | **NOT DISPROVED** | These maintenance requirements can matter. Their usefulness depends on substantive task construction and achieved reliability. |
| More than a meaningless permutation | **NOT DISPROVED** | **NOT DISPROVED** | Explicit preference and consistency losses change training. Whether they add value over shared counterfactual SFT remains unresolved. |
| Significant difference | **NOT DISPROVED** | **NOT DISPROVED** | The restricted capability could be significant. The proposed significance test does not by itself establish practical significance. |
| ≥60% chance of the intended artifact | **DISPROVED** | **DISPROVED** | Approximately **20% now**, **27% conditional on the binary pre-check**, with substantial unresolved acceptance and transfer risks. |
| **All criteria jointly satisfied** | **DISPROVED** | **DISPROVED** | The probability criterion fails; a passing competence screen does not establish the remaining conjunction. |

**8. The owner’s main blind spots are authority, dependencies, and what “PROVEN” proves.**

A scoped exception does not generally deactivate the global rule. Reinstating a rule is not necessarily restoring every dependent decision made under it. Correct behavior requires a relationship among authority, scope, time, and affected code—not just remembering the latest sentence.

A model can also state the current contract correctly while preserving stale callers, cached assumptions, or earlier implementation decisions. PlanFence makes the corresponding distinction explicit for agent plans; repository maintenance contains the same dependency problem. Training successful final patches can help, but the proposal must not equate current-rule recall with completed migration.

Execution verification is only as strong as its observable requirements. A test can miss double logging, accept a fallback that never runs, overlook aliasing under copy-on-write, or reward an implementation that satisfies the example while breaking an untested caller. An executable checker is not automatically an adequate specification.

The largest overlooked possibility is this:

**Rev 5 can produce a statistically valid PROVEN against `off`, yet leave the owner’s intended claim unresolved—because ordinary SFT may explain the gain, the sampled projects may cover only a narrow generator, the live interaction is short, and absolute reliability may remain poor.**

Those are limits of the existing design’s conclusion. Passing its pre-check does not remove them.
