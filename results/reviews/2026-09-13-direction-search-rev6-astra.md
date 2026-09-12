**The widened search produces better experiments than rounds 1–5, but no candidate I would currently give a defensible “good chance” of delivering the full objective. My strongest candidate is counterfactual training on changing coding instructions: roughly 35–55% for the artifact, centered around 45%. I would require at least 60%.**

That is substantially more promising than another reminder wrapper. It is still a research bet.

I searched primary papers, proceedings, author repositories, and recent preprints through **September 12, 2026**, including searches for predecessors that would invalidate my own proposals. I read the protocol, governing-plan context, prior reviews, README, Exp 4C report, and ledger. I did not read `data/bench/`, run models, or modify files.

The probability ranges below are subjective research forecasts, calibrated to the earlier reviews. They are not confidence intervals. “Artifact” means completing the bounded program with a useful paired improvement, acceptable functional performance and cost, and a defensible contribution beyond the obvious existing method. Screen definitions differ, so their probabilities are not perfectly interchangeable with earlier rounds.

| Candidate | Mechanism class | First screen passes | Full artifact succeeds | Decision |
|---|---|---:|---:|---|
| **A. Counterfactual training on current-rule execution** | Training objectives and curriculum | **45–65%** | **35–55%** | First choice |
| **B. Train recovery from the model’s own rule violations** | Learning from execution feedback | **35–55%** | **20–40%** | Second choice |
| **C. Train selective memory updates against downstream code failures** | Learned persistent memory | **30–50%** | **20–35%** | Third choice |
| **D. Contrast decoding against a rule-blind branch** | Decoding | **20–40%** | **10–25%** | Reject as lead contribution |
| **E. Gate a learned representation intervention by rule applicability** | Representation and adapters | **25–45%** | **15–30%** | Reserve experiment |
| **F. Validate code changes as transactions under current rules** | Tools, verification, and execution architecture | **40–60%** | **15–30%** | Useful subsystem; reject as lead |

The screen odds for F exceed its artifact odds because preventing invalid changes is easier than demonstrating a novel model-focus contribution.

**The common first-test design matters.**

For each candidate below, use **48 independent, newly authored small repositories**, each with a frozen 12–20-turn history followed by **two live coding requests**. Balance stable rules, authorized replacements, and scoped exceptions or irrelevant directives. Every arm starts from the same repository state; its two subsequent actions evolve its own state.

The outcome is binary joint success, \(J\): the resulting repository passes functional and regression tests **and** satisfies all applicable instructions at their specified checkpoints. Record function-only success, stale-rule use, unrelated damage, abstention, and cost separately. Private scoring tests remain unavailable to generation and repair.

A common development gate is:

- At least **five net joint-success wins out of 48** over modification-off.
- At least **three net wins** over the candidate’s strongest simple control.
- No observed net decline in function-only success against either comparator.
- All assigned cases count; unsupported rules, timeouts, and abandoned tasks cannot disappear.

Failure means **do not advance this configuration**. It does not mean statistical equivalence or scientific disproof.

These are deliberately inexpensive **history-replay screens**, not proof of autonomous long-horizon operation. Training candidates get a small fixed training allocation; decoding and harness candidates need none. Cap each complete screen at roughly **12–16 GPU-hours including training controls**, subject to measured throughput. Do not run all six. A selected program should reserve roughly **40–60 GPU-hours total**, including confirmation. If the timing pilot cannot support the registered workload, record cost-ineligible before evaluation.

Fit only on authored training projects and trajectories. Development and final evaluation must be separated by project, task construction, and underlying solution family—not merely by random seed or renamed identifiers.

**1. A — Counterfactual training on current-rule execution**

Train an optional LoRA on pairs of histories where a legitimate instruction change reverses which executable solution is appropriate.

For example, a project initially requires missing records to return `None`; a later instruction changes that behavior to `KeyError` only inside one component. Two otherwise comparable histories therefore require different edits. Both solutions must pass their corresponding functional tests and preserve unrelated behavior.

Combine ordinary completion loss with a preference objective that favors the current-rule solution over the stale-rule solution. Reverse that preference in the counterfactual history. Train across delays, distractors, reinstated rules, and scoped exceptions. Require consistent behavior under irrelevant history changes, and changed behavior under relevant instruction changes.

This recombines:

- **Ghost Attention**, which already trains multi-turn instruction persistence through context distillation: **arXiv:2307.09288, §3.3**.
- **IOPO**, input–output preference optimization: **arXiv:2411.06208**.
- **Reverse Preference Optimization**, which already reverses constraints to construct cleaner preference pairs: **arXiv:2505.22172**.
- **SelfCodeAlign**, execution-filtered code training: **arXiv:2410.24198**. [Ghost Attention](https://arxiv.org/html/2307.09288v2), [IOPO](https://arxiv.org/abs/2411.06208), [RPO](https://arxiv.org/abs/2505.22172), [SelfCodeAlign](https://arxiv.org/abs/2410.24198).

The potential contribution is **learning when an instruction remains applicable, changes, or stops applying, while preserving executable behavior**. Neither preference reversal nor long-dialogue fine-tuning is independently new.

The cross-domain prediction comes from practicing retrieval and application under varying conditions, rather than repeatedly presenting the answer. Human retrieval-practice research finds transferable benefits, but substantial dependence on the transfer task. Completed-intention experiments also show that stronger retrieval can produce erroneous execution of obsolete intentions. Together they motivate training **retention and deactivation**, not retention alone. These are design arguments, not quantitative predictions for transformers. [Pan and Rickard, DOI:10.1037/bul0000151](https://doi.org/10.1037/bul0000151), [Scullin et al., completed-intention experiments](https://pmc.ncbi.nlm.nih.gov/articles/PMC3598897/).

**Attack.** The closest additional predecessor is **Supersede, arXiv:2606.27472**, which already trains temporal memory updating in Qwen2.5-3B. Its reported improvement, 9.0% to 16.7%, is encouraging about trainability and discouraging about absolute competence. “Teach a small model to follow updated instructions” is therefore unavailable as the novelty claim. [Supersede](https://arxiv.org/abs/2606.27472).

The remaining gap is temporal and scoped rule selection **coupled to correct code changes**, with controlled evidence beyond ordinary training. This survives narrowly. It becomes a meaningless permutation if regular SFT on the same verified solutions works equally well.

The main failure risks are learning stereotyped rule phrases, rewarding synthetic editing shortcuts, and improving convention adherence while leaving algorithmic errors untouched. Training cannot recover an instruction that the shared memory pipeline discarded completely.

**First test.** Use the common N=48 design with three arms: adapter-off; ordinary SFT on the same positive solutions and histories; full counterfactual objective. Match training compute and inference information. Apply the common gate. Also reject the claimed mechanism if improvements occur only on stable rules while replacement and scope cases deteriorate.

**Artifact path.** Publish one frozen ≤4B trunk plus its unmerged adapter and session implementation. The off switch bypasses the adapter while retaining the same ordinary memory, reminders, tools, and generation budget. No teacher is required at deployment.

**Judgment: the strongest candidate.** It changes a learned capability that the owner needs and gives a direct experiment capable of showing that its particular recombination adds nothing.

**2. B — Train recovery from the model’s own rule violations**

Collect mistakes made by the chosen small model on authored coding sessions. Supply actual execution diagnostics and current-rule violations, then train it to repair the entire affected dependency region while preserving already correct behavior.

Include correct drafts whose target is **leave this alone**, as well as failures requiring substantial revision. Accept training repairs only when they pass both task tests and applicable-rule checks. A bounded second collection pass can expose the trained model’s new error distribution.

This combines **DAgger’s** treatment of distribution shift, **RISE/SCoRe’s** learned correction, and code-specific localized preference training. **DiSCo-LPO** already trains localized code improvements with a regularizer intended to preserve code quality. [DAgger, arXiv:1011.0686](https://arxiv.org/abs/1011.0686), [RISE, arXiv:2407.18219](https://arxiv.org/abs/2407.18219), [SCoRe, arXiv:2409.12917](https://arxiv.org/abs/2409.12917), [DiSCo-LPO, arXiv:2506.00419](https://arxiv.org/abs/2506.00419).

The cross-domain prediction is more substantial than “feedback helps.” Error-management training makes learners practice recovery from encountered failures, with evidence of transfer to unfamiliar problems. The relevant model hypothesis is that **training recovery on its own mistakes** beats expecting an untrained repair ability to emerge at inference time. [Keith and Frese, DOI:10.1037/0021-9010.93.1.59](https://fis.leuphana.de/en/publications/effectiveness-of-error-management-training-a-meta-analysis/).

**Attack.** Almost every ingredient already exists. The narrow gap is recovery from **changing session obligations**, including dependency repair and preservation of previously correct behavior.

There is direct contrary evidence. **Try Again, Don’t Look Back, arXiv:2607.26117**, reports that blind resampling beats feedback-conditioned repair below 7B in its experiments. SCoRe itself reports that offline correction SFT can fail through distribution mismatch or behavioral collapse. Neither paper establishes that a few hours of adapter training solves this at 4B. [Small-model repair study](https://arxiv.org/html/2607.26117v1), [SCoRe](https://arxiv.org/abs/2409.12917).

Furthermore, an ordinary coding agent already runs tests and repairs failures. Adding rule diagnostics is useful engineering, but an extra attempt cannot be credited as a new recovery mechanism.

**First test.** N=48, four arms: adapter-off with ordinary feedback; off with blind retries and the same available-test selector; ordinary solution SFT with feedback; recovery-trained adapter with feedback. Give every arm the same total generation allowance and access to public tests. Require the common gate against the strongest control. Kill if the trained policy improves repairs but causes enough unnecessary edits to lose the function-only comparison.

**Artifact path.** One trunk plus recovery adapter, with the same test-and-repair loop available when the adapter is disabled.

**Judgment: survives, but behind A.** It attacks a demonstrated problem; its effective training recipe and sample efficiency are less certain.

**3. C — Train selective memory updates against downstream code failures**

Use the same small model to maintain a compact persistent record through explicit insert, replace, expire, and no-change operations. Preserve untouched entries mechanically instead of rewriting the entire memory at every compaction.

Train the updater on authored instruction lifecycles, including source, scope, current version, and retirement. Train memory consumption using downstream executable coding outcomes. A perfectly reconstructed ledger that the action model cannot use earns no claim of success.

Relevant predecessors already cover much of this:

- **Memory-R1, arXiv:2508.19828:** learned ADD/UPDATE/DELETE/NOOP operations and memory use.
- **StateLM/Pensieve, arXiv:2602.12108:** a model trained to manage its own context.
- **Multi-Head Recurrent Memory, arXiv:2607.01523:** selective updates that protect untouched memory.
- **Gist tokens, arXiv:2304.08467:** learned compressed representations. [Memory-R1](https://arxiv.org/abs/2508.19828), [StateLM](https://arxiv.org/html/2602.12108v1), [MHM](https://arxiv.org/abs/2607.01523), [Gisting](https://arxiv.org/abs/2304.08467).

The cross-domain connection is selective updating in working memory: maintaining one item should not require reconstructing every other item. Computational neuroscience provides a learned-gating account; protected records provide an actual software mechanism implementing that separation. [O’Reilly and Frank, DOI:10.1162/089976606775093909](https://ccnlab.org/papers/OReillyFrank06.pdf).

**Attack.** Learned memory operations, protected slots, and temporal updating are all anticipated. The possible contribution is training the **retention/update decisions for their consequences on future code execution**, especially scope changes and reinstatement.

The repository already has ample evidence that reliable admission and supersession are difficult. A learned updater could simply repeat those failures with a new architecture. Protected slots also protect mistakes. A deleted qualifier cannot be recovered from a compact record.

Presentation is another threat: **arXiv:2607.16019** found that much of an apparent sophisticated-ledger advantage disappeared under a rendering-matched control. [Render-confound study](https://arxiv.org/abs/2607.16019).

**First test.** N=48 with multiple forced compactions in each prefix. Arms: ordinary prose summary; untrained structured updater with the same schema and renderer; trained selective updater. Let each updater process the actual messages sequentially—no oracle state initialization. Apply the joint-success gate; memory accuracy alone cannot pass it.

**Artifact path.** One trunk and optional memory adapter, invoked serially for memory updates and action generation. Off retains a functioning ordinary memory policy. Session state must survive save/reload and remain isolated across sessions.

**Judgment: survives narrowly.** It addresses the 4,096-token constraint directly, but adds another learned failure point before code generation.

**4. D — Contrast decoding against a rule-blind branch**

Run the same model with and without the current-rule packet. Within a plausibility set, increase the relative weight of tokens supported by the rule-conditioned branch:

\[
s(y)=\log p(y\mid\text{task,rules})
+\alpha\big[\log p(y\mid\text{task,rules})-\log p(y\mid\text{task})\big].
\]

Optionally activate the contrast only when the distributions disagree substantially.

The cross-domain argument is likelihood-ratio discrimination: emphasize evidence that distinguishes two hypotheses while reducing shared background influence. That is a mathematical motivation, not a guarantee of semantic correctness.

**Attack.** This is already a crowded, directly relevant method family. **Instructive Decoding, arXiv:2311.00233**, contrasts instruction variants. **Selective Prompt Anchoring, arXiv:2408.09121**, applies related contrasts to code generation. **Adaptive Contrastive Decoding, DOI:10.1109/ICAIBD64986.2025.11082001**, separates constraints from the underlying task. Most decisively, **IHDec, arXiv:2606.29960**, already uses divergence-triggered contrastive decoding for multi-turn instruction hierarchy. [Instructive Decoding](https://arxiv.org/abs/2311.00233), [SPA](https://proceedings.mlr.press/v267/tian25a.html), [ACD](https://ieeexplore.ieee.org/document/11082001/), [IHDec](https://arxiv.org/abs/2606.29960).

Replacing their negative branch with a session-rule-blind branch is not enough to establish a significant new recombination.

Mechanically, the logit difference measures sensitivity to conditioning, not correctness. It can amplify a mistaken interpretation or suppress a correct, conventional code token precisely because both branches support it. Two branches also consume inference capacity that could fund another attempt.

**First test.** N=48; ordinary decoding, published SPA-style contrast, proposed current-rule contrast. Compare within equal measured resource ceilings, and report token-budget sensitivity. Apply the common gate. A win only over ordinary decoding does not establish the proposed contribution.

**Artifact path.** One model with a custom decoder and `alpha=0` off mode.

**Judgment: reject as the lead direction.** Plausible utility, weak remaining novelty, and no direct fix for failed functional integration.

**5. E — Gate a learned representation intervention by rule applicability**

Encode current rules with the frozen trunk, then use a small learned gate to activate low-rank residual interventions where those rules are applicable. Train on executable positive and negative outcomes, including no-rule and out-of-scope cases. Both on and off receive the same prose instructions.

The intended difference from generic steering is learning **when to leave the model alone**, as well as how to change its behavior.

Prior art includes instruction-specific activation steering, **arXiv:2410.12877**; conditional activation steering, **arXiv:2409.05907**; and context-generated adapters, **SHINE, arXiv:2602.06358**. [Instruction steering](https://arxiv.org/abs/2410.12877), [CAST](https://arxiv.org/abs/2409.05907), [SHINE](https://arxiv.org/abs/2602.06358).

The neuroscience connection is again conditional maintenance and control. A newer direct AI connection is **counterfactual reflection training**, which changes behavior by training what a model would articulate in interrupted contexts. This supports investigating learned internal availability of principles, but its demonstrated setting is not a ≤4B coding model. [Global-workspace study, arXiv:2607.15495](https://arxiv.org/abs/2607.15495).

**Attack.** Conditional steering already exists. A scope gate attached to an instruction vector is a small extension unless it demonstrates useful compositional behavior that ordinary adapters cannot provide.

The difficult part is not producing a gate. It is learning applicability and useful intervention strength across unseen rules without damaging computation. The repository’s wave results already warn that internal interventions can improve a target metric while harming general capability. SHINE’s six-billion-token training scale cannot justify expecting a locally trained miniature hypernetwork to reproduce its capabilities. [SHINE training scale](https://arxiv.org/html/2602.06358v1), [repository qualifications](/home/bmarti44/stencil-llm/README.md).

**First test.** N=48; off, ordinary LoRA, always-active intervention, gated intervention. Same training examples and compute ceiling. Require the common joint-success gate and a positive advantage over always-active steering on scoped and irrelevant-rule cases. Kill if the gate merely reduces intervention frequency without improving useful outcomes.

**Artifact path.** Frozen trunk plus small gate and intervention weights; disabling the intervention exactly bypasses those modules.

**Judgment: reserve only.** Potentially substantive, but less grounded than A and more exposed to representation interference.

**6. F — Validate code changes as transactions under current rules**

Compile a supported subset of instructions into executable checks. Generate a complete proposed patch in a scratch state, validate the affected dependency region and regression tests, then commit or return diagnostics for a bounded repair. Rule changes invalidate the relevant checks and dependent assumptions.

This combines database transactions, compensating actions, synthesis with counterexamples, and code-agent verification. The external mechanism can preserve a checked invariant even when generation itself is unreliable. [Sagas, Garcia-Molina and Salem, 1987](https://www.cs.princeton.edu/techreports/1987/070.pdf), [CEGIS, Solar-Lezama](https://people.csail.mit.edu/asolar/SynthesisCourse/Lecture17.htm).

**Attack.** The combination is substantially anticipated by monitor-guided generation, semantic validation and rollback, **SagaLLM, arXiv:2503.11951**, and **Proof-Carrying Agent Actions, arXiv:2606.04104**. Adding a session-rule version to a transaction record is ordinary maintenance unless a further effect is demonstrated. [MGD, arXiv:2306.10763](https://arxiv.org/abs/2306.10763), [IterGen, arXiv:2410.07295](https://arxiv.org/abs/2410.07295), [SagaLLM](https://arxiv.org/abs/2503.11951), [PCAA](https://arxiv.org/abs/2606.04104).

More fundamentally, rejecting everything preserves many invariants while completing no work. Passing tests also supplies evidence under those tests, not a formal proof of arbitrary program behavior.

The gap would be useful completion under changing, cross-file obligations at fixed repair cost. That could matter operationally. It would primarily demonstrate a verification system, and the model-focus attribution would remain weak.

**First test.** N=48; ordinary generate/test/repair, terminal rule checking with the same diagnostics, transactional checking with invalidation. Identical total attempt budgets. Score completed joint success, including rejected and abandoned requests. Apply the common gate. Fewer committed violations alone cannot pass.

**Artifact path.** One model repository containing the frozen trunk and execution package, with transactional enforcement toggled. The card must attribute the effect to that package.

**Judgment: retain as infrastructure if useful; reject as the owner’s principal research contribution.**

**The strongest positive evidence changes the search direction, not the verdict.**

The June **ComplexConstraints** paper reports Qwen3-4B improvement after LoRA-based training on roughly 900 authored tasks: +15.5 points on its per-criterion measure, with +7.1 points on an independently designed multi-turn-context evaluation. These are relevant grounds for taking small-model training seriously. They are single-seed results, and they do not demonstrate joint functional coding success. [arXiv:2606.09118, §§5.3–5.4](https://arxiv.org/html/2606.09118v1).

That evidence supports ranking A above the reminder family. It does not support assigning A a 70–80% success probability.

The remaining survivors rank **A, B, C, E**. D and F have enough prior coverage that I would not spend this program’s limited budget trying to rescue their novelty.

**The proof must fit the machine before training starts.**

I independently recomputed exact two-sided McNemar power at a true ten-percentage-point improvement:

| Independent paired sessions | 20% discordant | 30% discordant | 40% discordant |
|---:|---:|---:|---:|
| 48 | 23% | 17% | 14% |
| 128 | 67% | 49% | 39% |
| 256 | 95% | 81% | 69% |
| 384 | 99% | 94% | 86% |

These are powers for superiority over zero, **not** for establishing that the lower confidence bound exceeds ten points.

Consequently:

- A 48-session screen can justify stopping or further investment. It cannot reliably certify a ten-point effect.
- A final N around 256–384 may be necessary, depending on discordance and the functional guard.
- The evaluation must contain live actions and repeated compactions. Replaying a long transcript before one completion does not establish resistance to the model’s own accumulating mistakes.
- Sessions, not turns or renamed templates, are the independent units.

Fit that workload using small repositories, short actual patches, and bounded tool output. Do not repeat the 512-token whole-program truncation problem. If measured throughput cannot support the needed N within tens of hours, the intended proof is cost-ineligible.

Use **one registration for the selected program**, containing its development gate and sealed confirmation; one implementation review; one result audit. This search does not justify another ladder of proposal reviews.

**What is binding, and what would have to change?**

The objective is constrained by the conjunction of **coding competence, rule applicability, persistent state, transfer, novelty, and statistical power**. Model size alone is not the entire explanation.

The ≤4B limit probably constrains executable competence more severely than the ability to recognize a rule. Exp 4C’s 0/139 versus 1/139 strict-compliance result and high output-failure rate leave little basis for assuming that improved retention will produce useful programs. However, that experiment’s cap and scoring prevent treating it as a universal ceiling on a trained 4B model. [Exp 4C](/home/bmarti44/stencil-llm/results/memorycode-long/RESULTS-4C.md).

The 4,096-token limit creates a different, absolute issue: after compaction, two sessions requiring different actions can become indistinguishable if their distinguishing instruction was discarded. No decoding trick can reconstruct that missing distinction reliably. Persistent state is necessary; perfect memory is still insufficient.

The same-artifact comparison is **not** inherently binding. A frozen trunk plus an optional unmerged adapter provides a clean comparison. What would weaken it is training a model to depend on a new memory format and then declaring victory after disabling that format without providing a competent fallback.

If the owner requires a forecast above 60% **before any new evidence**, the most defensible change is to narrow the operating domain: a prespecified family of useful maintenance tasks, supported mutable contracts, and a workload where fresh authored development evidence establishes that the model can already execute the task with immediate instructions. Under that condition, I would provisionally put A at **60–75%**. That is a conditional forecast, not evidence that the condition currently holds. Defining the domain must precede looking for favorable evaluation outcomes.

Allowing 7–14B models or more training compute might improve competence and correction learning, but I cannot honestly promise that either change alone crosses 60%. Those are counterfactual relaxations, not proposals under the present constraints. Weakening the outcome to compliance-only would make a positive result easier and repeat the failure the owner explicitly rejected.

One further point: **“nothing reaches 60% today” does not imply the owner must abandon or weaken the goal.** It means the next rational purchase is information. Run A’s bounded screen, with ordinary SFT as the serious opponent. If ordinary SFT ties it, retire the novelty claim. If both lose, stop. If A wins on fresh changing-rule tasks without functional loss, there is finally evidence for raising its probability.

**My recommendation is A’s experiment. My verdict on the owner’s full gate remains: not yet met.**
