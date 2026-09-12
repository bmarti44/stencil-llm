# Adversarial review, round 2, of a proposed research direction (Astra, deep web research, xhigh)

Same standard and same task as round 1 (`results/reviews/2026-09-12-direction-adversarial-astra-prompt.md`,
which you should re-read together with your own round-1 report
`results/reviews/2026-09-12-direction-adversarial-astra.md`). The owner's goal, verbatim: "we need to
make sure we find a novel, useful recombination of techniques that is not technically novel
based on a meaningless permutation, that is a significant difference, and that has a good
chance of actually working based on current research, not only in the AI domains - but also
all other academic domains. use astra to adversarially try to disprove the goal with deep web
research and anything else that I'm not thinking of, and consider the goal satisfied when astra
can not prove it."

Read `results/reviews/2026-09-12-direction-proposal-rev2.md`. It adopts your round-1 bar
("an identified new algorithm, guarantee, or demonstrated interaction") and proposes direction
D (focal delivery of live session conventions at the governed syntactic unit inside one
generation) whose contribution is a set of theory-predicted, unmeasured interactions
(H1 decay × delivery, H2 rule type × delivery, H3 load × delivery), plus fallback X
(verified exemplars instead of prose rules). Do not read `data/bench/`. Do not write files or
run models. Use deep web research (arXiv, ACL/NeurIPS/ICLR/ICSE/FSE/CHI/POPL proceedings,
GitHub, documentation, and the psychology / human-factors / education literatures cited).

Attack, with citations (year, venue or URL) and numbers where they exist:

1. **Novelty.** Find any system that delivers *session-derived* conventions *per governed
   unit inside one completion* (search: re-injection during generation, comment insertion at
   function definitions, per-step rule anchoring at decode time, "context anchoring",
   Answer Engineering / Thinking Intervention / SafeRemind follow-ups, ZORO, Cursor/Claude
   Code hooks that inject rules mid-generation). Find any prior *measurement* of H1, H2 or H3
   (placement × position-in-output, placement × constraint polarity, placement × instruction
   count) in LLMs. State exactly which of T1, T2, D, H1-H3 each predecessor covers.
2. **Theory.** Does the multiprocess framework of prospective memory (McDaniel & Einstein;
   Anderson, Strube & McDaniel 2019) actually predict H1-H3 under the proposal's mapping
   (focal = the rule text is adjacent to the unit the model is writing)? Do the LLM results
   (2603.23530, 2604.20911, 2605.10039, 2606.23459, 2608.02639, 2510.05381, 2604.11088,
   2607.16019) predict a null or an opposite sign for any hypothesis? Is the commission /
   omission distinction stable across those papers, and does the proposal's H2 survive their
   disagreement?
3. **Measurement.** Confounds that would let a positive `focal − before` arise from something
   other than placement: changed continuation after an inserted comment, token-budget
   asymmetry (prompt vs output tokens), the comment block acting as a plan, triggers inside
   strings or examples, the checker's regex families, structure-missing items, the 1,536 cap,
   outcome-exposed items, the register's own errors. Say which confounds the registration in
   section 4 already removes and which it does not.
4. **Usefulness and significance.** Would a demonstrated H1-H3 change practice (compared with
   "re-inject rules every turn", ZORO-style plan anchoring, or a linter + repair loop)? What do
   the nearest systems report, and what magnitude would D need to matter?
5. **Likelihood on this setup.** Qwen3-4B, 2,560-token window, 1,536-token output, greedy,
   MemoryCode-derived items with updates. Mechanism reasons it fails: comment insertion
   ignored by small models, rollback at line start, competing rules at one unit, docstring
   and content rules, and anything else.
6. **Cross-domain.** Any other domain with a stronger analogue or a contrary result
   (checklist timing in surgery and aviation: item-by-item challenge-response vs read-once;
   just-in-time training; point-of-care decision support vs guidelines; worked examples;
   structural priming).
7. **Anything the owner is not thinking of.**

Then give `D: DISPROVED|NOT DISPROVED` and `X: DISPROVED|NOT DISPROVED` on the first two
lines, each with the one decisive reason or a statement of what you tried and why it failed to
disprove. If D is NOT DISPROVED, list the minimum changes to section 4 (arms, estimand, N,
gates, kill criteria) as a numbered list. If D is DISPROVED, construct the strongest direction
that satisfies the owner's goal under the same bar, with citations, and try to disprove that
too. Apply the owner's words, not a stricter private standard: a recombination is
non-meaningless when theory predicts an effect of the combination that no part produces alone
and that effect has not been demonstrated; if you reject that reading, say why in one paragraph.
