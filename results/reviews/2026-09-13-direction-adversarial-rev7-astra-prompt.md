# Adversarial round 7: try to disprove proposal rev 5 (candidate A in a prespecified domain with a competence pre-check)

Read `results/reviews/2026-09-13-direction-proposal-rev5.md`. It fixes the conditional
path you stated in round 6 (`results/reviews/2026-09-13-direction-search-rev6-astra.md`):
candidate A narrowed to a prespecified operating domain (eight mutable contract families
on small Python packages) with a registered competence pre-check on the unmodified model
under immediate instructions. Your task is to DISPROVE, if you can, that rev 5 satisfies
ALL of the owner's criteria, using deep web research through today across AI and every
other relevant academic domain, plus the repository evidence and your six prior reviews.
Do NOT read `data/bench/`. You proposed A and the conditional path; be harder on rev 5
than on the author's earlier proposals.

## The owner's criteria (verbatim)

"a novel, useful recombination of techniques that is not technically novel based on a
meaningless permutation, that is a significant difference, and that has a good chance
of actually working based on current research, not only in the AI domains - but also
all other academic domains."

The goal counts as satisfied only when you cannot disprove it. You set the bar for
"good chance" at ≥ 60% before new evidence, and said A reaches 60–75% under the
narrowing condition. Rev 5 claims to satisfy that condition by specification plus a
cheap empirical pre-check.

## Questions

1. Is the narrowing legitimate? Is the eight-family contract schema a prespecified,
   useful operating domain, or a domain reverse-engineered to be easy? Is the
   competence pre-check (32 authored tasks, immediate instructions, J ≥ 50%) a valid
   way to establish your condition without touching evaluation data, and is the
   threshold right? Would passing it actually move A to ≥ 60% in your judgment?
2. Novelty, with fresh search: rule/contract-conditioned preference training for code;
   counterfactual or twin-history training for instruction updating (Supersede
   2606.27472 and anything after it); temporal instruction following fine-tunes;
   contract- or policy-aware code editing agents; anything in September 2026. Cite each
   and say which claim it covers.
3. Meaningless permutation? Is "preference reversal across counterfactual histories"
   a real manipulated variable over ordinary SFT on the same verified solutions, or a
   relabelling? Predict what the `sft` control will do.
4. Significance and usefulness of the narrowed domain: is a model that keeps eight
   contract families current over a long session a significant artifact, or a
   toy?
5. Chance of working: give your probability that the pre-check passes, that the
   screen passes given the pre-check, and that confirmation reads PROVEN given the
   screen; multiply them out for the artifact. State the number you would need and
   whether rev 5 reaches it (a) now and (b) conditional on the pre-check passing.
6. The experiment: every confound in the screen and confirmation (generator leakage
   between training and evaluation projects, template clusters counted as independent
   sessions, the SFT control's compute matching, adapter-off fallback competence,
   compaction handling within 4,096 tokens, the two-live-request design, the function
   guard), the compute feasibility on a GB10 shared with a 30 GB job, and what would
   make a PROVEN uninterpretable.
7. Verdict per criterion: DISPROVED / NOT DISPROVED with the decisive reason, for rev 5
   as written (a) unconditionally and (b) conditional on the pre-check passing.
8. Anything the owner is not thinking of.

Cite sources with identifiers. Write plainly. Do not soften. Do not add models,
benchmarks or review stages.
