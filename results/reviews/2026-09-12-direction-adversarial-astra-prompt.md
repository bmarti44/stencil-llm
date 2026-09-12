# Adversarial review of a proposed research direction (Astra, deep web research, xhigh)

You are asked to DISPROVE, not to improve. The owner's goal, verbatim: "we need to make sure
we find a novel, useful recombination of techniques that is not technically novel based on a
meaningless permutation, that is a significant difference, and that has a good chance of
actually working based on current research, not only in the AI domains - but also all other
academic domains. use astra to adversarially try to disprove the goal with deep web research
and anything else that I'm not thinking of, and consider the goal satisfied when astra can
not prove it."

Read `results/reviews/2026-09-12-direction-proposal.md` (the proposal) and, for context,
`results/memorycode-long/RESULTS-4C.md` and `results/memorycode-long/REGISTRATION-4C.md`
(what was just tried and why it gave +2 points), `plan/BACK-ON-TRACK-PLAN.md` sections G-K,
and the package under `deploy/stencil_focus/stencil_focus/`. Do not read `data/bench/`. Do not
write files or run models. Use deep web research: arXiv, ACL/NeurIPS/ICLR/POPL/PLDI/FSE/ICSE
proceedings, GitHub, blogs, and the non-AI literatures the proposal cites (human factors and
aviation readback, prospective memory and implementation intentions, directed forgetting and
proactive interference, runtime enforcement and edit automata, software engineering linters).

For the primary candidate A and each of B, C, D:

1. **Novelty attack.** Find the closest existing systems or papers (give citations with
   year and venue or URL). State precisely which of the parts A1-A5 each one already has,
   and whether the combination reduces to one of them plus a trivial permutation. Search
   explicitly for: decode-time enforcement of natural-language coding conventions or style
   policies; rollback/regenerate on policy violation; trigger-conditioned in-generation
   insertion of rules; readback or confirmation protocols for LLM instruction capture;
   canonical if-then rule compilation from chat; supersession-aware rule rendering; runtime
   verification / edit automata applied to LLM token streams; agent guardrail frameworks.
2. **Significance attack.** Argue the expected effect is small, unattributable to the novel
   part, or achievable by an existing off-the-shelf pipeline (e.g. linters + repair loop).
   Quantify where possible: what do the nearest systems report?
3. **Likelihood attack.** Where does the mechanism break: monitor compilation accuracy from
   natural language, content rules that regex cannot express, judge-based monitors
   re-introducing attention failures, rollback loops and degeneration, latency, harm to
   functional correctness. Cite measured numbers from the literature.
4. **Cross-domain grounding attack.** Check each imported result: readback/hearback
   effectiveness evidence; implementation intentions meta-analyses (effect size and
   replication status); the generation effect; cue-focal prospective memory (multiprocess
   framework) and its replication; directed forgetting and reconsolidation; edit automata's
   enforceable-policy theory. Say whether each is real, replicated, and correctly mapped
   onto the LLM setting, or whether the mapping is decorative.
5. **Anything the owner is not thinking of.** Other academic domains with a stronger
   analogue (control theory, operations research, organizational science, law, medicine,
   safety engineering, linguistics, education), and any reason the whole framing is wrong.

Then give a verdict per candidate: DISPROVED (with the one decisive reason) or NOT DISPROVED
(state what you tried and why it failed to disprove). If A is NOT DISPROVED, specify the
minimum registration for its predictions P1-P4 (arms, estimand, N, gates, kill criteria),
reusing the existing Exp 4C infrastructure. If A is DISPROVED, name the strongest direction
you can construct that satisfies the owner's goal under the same standard, with citations,
and try to disprove that too.

Output: a Markdown report beginning with one line per candidate,
`A: DISPROVED|NOT DISPROVED`, etc., followed by the findings with citations. Be concrete and
quantitative; a verdict without a cited decisive reason is not a disproof.
