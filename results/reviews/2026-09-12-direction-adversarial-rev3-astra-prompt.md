# Adversarial round 3: try to disprove direction D with the pilot evidence in hand

Your task is to DISPROVE, if you can, that direction D ("focal delivery": session
conventions delivered inside one generation at the syntactic unit they govern;
`results/reviews/2026-09-12-direction-proposal-rev2.md`) satisfies ALL of the owner's
criteria below. Use deep web research across AI and any other academic domain
(cognitive psychology, human factors, education, HCI, software engineering,
operations, medicine, anything relevant), plus the repository evidence. Do NOT read
anything under `data/bench/`. Do not soften. Do not assume the author's framing is
right.

## The owner's criteria (verbatim)

"a novel, useful recombination of techniques that is not technically novel based on a
meaningless permutation, that is a significant difference, and that has a good chance
of actually working based on current research, not only in the AI domains - but also
all other academic domains."

The goal counts as satisfied only when you cannot disprove it.

## What has changed since your round-2 review

Round 2 (`results/reviews/2026-09-12-direction-adversarial-rev2-astra.md`) found D NOT
DISPROVED before any implementation existed. Since then: a runtime was built
(`src/stencil/focal.py`, `src/stencil/focal_runtime.py`), four pilots ran on exposed
SETUP-LONG items with oracle rules (`results/focal/quicklook-v3.json` … `-v6.json`,
logs alongside), and you reviewed the root causes
(`results/reviews/2026-09-12-focal-rootcause-astra.md`) and then v6 independently
(`results/reviews/2026-09-12-focal-v6-review-astra.md`: "stop this configuration; do
not advance it to a registered screen now"; D "unproven rather than disproved").
`plan/LEDGER.md` entries dated 2026-09-12 record the sequence. The Exp 4C result the
direction was meant to improve on is in `results/memorycode-long/RESULTS-4C.md`.

## Questions

1. Novelty. With fresh web research (search for work published through September
   2026), is there now prior art that makes D a meaningless permutation of known
   techniques: in-generation intervention at syntactic boundaries, decision-point
   reminders, structure-aware prompting, compiler/IDE-style inline hints to LLMs,
   just-in-time cueing in human performance literature applied to LLMs, or anything
   else? Cite each item and say exactly which of D's claims it covers.
2. Significance. Is the difference D proposes over a reminder placed before
   generation a significant one, or a cosmetic placement change? Use the pilot
   evidence, the checker semantics, and any literature on reminder placement,
   proximity/contiguity effects, and decay within long outputs.
3. Chance of working. Given v3–v6 (the rules were followed at the cue point; the
   code was functionally damaged; no arm beat the reminder on a fair comparison; the
   user-turn channel avoided the imitation loop), and given current research in AI
   and in other domains on just-in-time versus up-front instruction, estimate
   honestly whether a correctly built version has a good chance of working on the
   owner's actual objective (an artifact that keeps focus on relevant instructions
   over a long agentic coding session, proven against the same artifact unmodified).
   State the probability you would put on a fair registered screen reading positive.
4. Verdict. DISPROVED or NOT DISPROVED, per criterion, with the decisive reason.
5. If DISPROVED on any criterion, or if you judge the chance of working poor: name
   the one to three research directions the repository's evidence and the current
   literature most support as satisfying ALL the owner's criteria, each with the
   specific prior art it recombines, the specific gap it fills, the first cheap
   disconfirming test, and the reason you would not be able to disprove it.
6. Anything the owner is not thinking of.

Cite sources with identifiers (arXiv numbers, DOIs, URLs). Write plainly.
