# Adversarial round 4: try to disprove direction proposal rev 3 (E1 primary, E2 fallback)

Read `results/reviews/2026-09-13-direction-proposal-rev3.md`. It was written in response
to your round-3 review (`results/reviews/2026-09-12-direction-adversarial-rev3-astra.md`),
which disproved direction D on chance of working and named two alternatives. The
proposal formalises them. Your task is to DISPROVE, if you can, that E1 (and separately
E2) satisfies ALL of the owner's criteria. Use deep web research through today across
AI and every other relevant academic domain, plus the repository evidence
(`plan/LEDGER.md` 2026-09-12/13 entries, `results/focal/quicklook-v6.json`, your prior
reviews, `results/memorycode-long/RESULTS-4C.md`). Do NOT read `data/bench/`. You named
these directions; be harder on them than you would be on a stranger's.

## The owner's criteria (verbatim)

"a novel, useful recombination of techniques that is not technically novel based on a
meaningless permutation, that is a significant difference, and that has a good chance
of actually working based on current research, not only in the AI domains - but also
all other academic domains."

The goal counts as satisfied only when you cannot disprove it.

## Questions, per direction (E1, then E2)

1. Novelty. Search specifically for: dependency-ordered or plan-ordered instruction
   delivery to LLMs; import/interface-aware constraint injection during code
   generation; "obligation" or "requirement" scheduling in program synthesis; CLT
   element-interactivity applied to prompting; just-in-time information in
   instructional design; and any 2026 work on session-rule lifecycle with timed
   delivery. Cite each and say exactly which claim in the proposal it covers.
2. Meaningless permutation? Is "time delivery by dependency order" a real manipulated
   variable with a predicted effect, or a re-labelling of "put the relevant rules
   first"? In particular: does the relevance-matched, dependency-complete `before`
   arm already capture everything E1 can deliver, making E1 at best a packaging
   improvement? Argue both sides, then decide.
3. Significance and chance of working. Given the mechanism objection you raised for D,
   does E1 actually avoid it, or does it move the problem (who computes the dependency
   map; what happens when the map is wrong; how often the earliest decision is the
   request itself, which collapses E1 into `before`)? Estimate the probability that the
   registered first test in §2 reads positive, and the probability the direction
   yields the owner's artifact (a published model wrapper that beats itself unmodified
   on long coding sessions). Give ranges.
4. The first test. Is it a fair, disconfirming test? Name every confound, the
   minimum N, and what would make a positive reading uninterpretable.
5. Verdict per criterion: DISPROVED / NOT DISPROVED with the decisive reason, for E1
   and for E2.
6. If both are disproved: what would you propose instead, with the same rigor you
   asked of the author (prior art, gap, first cheap test, kill rule)?
7. Anything the owner is not thinking of.

Cite sources with identifiers. Write plainly. Do not soften. Do not add models,
benchmarks or review stages.
