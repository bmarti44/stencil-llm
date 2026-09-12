# Adversarial round 5: try to disprove direction proposal rev 4 (E3, compiled current-rule demonstrations)

Read `results/reviews/2026-09-13-direction-proposal-rev4.md`. It specifies the
replacement you named in round 4 (`results/reviews/2026-09-13-direction-adversarial-rev4-astra.md`)
as a fixed target. Your task is to DISPROVE, if you can, that E3 satisfies ALL of the
owner's criteria. Use deep web research through today across AI and every other
relevant academic domain, plus the repository evidence (ledger entries 2026-09-12/13,
`results/focal/quicklook-v6.json`, `results/memorycode-long/RESULTS-4C.md`, your four
prior reviews). Do NOT read `data/bench/`. You proposed E3; be harder on it than on D.

## The owner's criteria (verbatim)

"a novel, useful recombination of techniques that is not technically novel based on a
meaningless permutation, that is a significant difference, and that has a good chance
of actually working based on current research, not only in the AI domains - but also
all other academic domains."

The goal counts as satisfied only when you cannot disprove it. You also warned that
successive narrowing can make any proposal hard to disprove by leaving little
specified; apply that warning to rev 4 explicitly: is E3 still a substantive
direction, or has the search narrowed into triviality?

## Questions

1. Novelty. Search specifically for: template- or rule-compiled few-shot examples;
   synthetic demonstration generation conditioned on constraints or style rules;
   "demonstration synthesis" / "example synthesis" for code style, linting, or
   conventions; rule-to-example compilation in instructional design (worked examples
   generated from rules, example-based learning of conventions); coding-assistant
   products or papers (2025–2026) that render examples from repository conventions
   (e.g., rules files with examples, style-guide-to-example tooling). Cite each and
   say exactly which claim it covers.
2. Meaningless permutation? Is "provenance of the demonstration" a real manipulated
   variable with a predicted pattern, or is E3 just "few-shot prompting with
   hand-made examples", automated? Argue both sides, decide.
3. Significance and chance of working. Estimate the probability the §3 screen reads
   CONTINUE, and the probability the direction yields the owner's artifact (a published
   model wrapper that beats itself unmodified on long coding sessions). Give ranges and
   the decisive mechanism reasons: does a trivial template demonstration transfer to a
   real algorithm; does it add tokens the same way a longer rule would; does the
   dependency-complete prose rule already carry the information; does the small 4B
   model copy template bodies.
4. The screen. Is §3 a fair, disconfirming test? List every confound, whether the
   comparators are straw men, and what would make CONTINUE uninterpretable.
5. Verdict per criterion: DISPROVED / NOT DISPROVED with the decisive reason.
6. If disproved: state whether, in your judgment, ANY direction reachable from this
   repository's assets (a 4B trunk, a sentence classifier, a rule register, the
   MemoryCode-derived renderer, a session wrapper) can satisfy "good chance of working"
   for the owner's artifact, and if so name it with the same rigor; if not, say so and
   say what the owner should conclude.
7. Anything the owner is not thinking of.

Cite sources with identifiers. Write plainly. Do not soften. Do not add models,
benchmarks or review stages.
