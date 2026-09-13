# Adversarial review: is this direction worth taking at all?

You are reviewing the Stencil repository at /home/bmarti44/stencil-llm as an
independent adversarial reviewer. Use MAXIMUM reasoning effort. You are
author-disjoint from everything below: you wrote none of it.

**Do not read anything under `data/bench/`.** It holds evaluation benchmarks and
recorded responses; reading it would contaminate the work. Nothing you need is
there.

Write ONLY this review file. Do not edit code.

## Your job

Brian's standing instruction, verbatim: *"we need to make sure we find a novel,
useful recombination of techniques that is not technically novel based on a
meaningless permutation, that is a significant difference, and that has a good
chance of actually working based on current research, not only in the AI
domains - but also all other academic domains. use astra to adversarially try to
disprove the goal with deep web research and anything else that I'm not thinking
of, and consider the goal satisfied when astra can not prove it."*

So: **try to disprove it.** The direction is satisfied only if you cannot.
"Good chance of working" has a numeric bar: **a direction at >= 25% on your
artifact-success forecast is NOT DISPROVED on that criterion.** State your
forecast as a number and say which side of 25% it falls.

Do deep web research. Cover 2024-2026 machine learning, and also look outside
it — cognitive psychology of belief revision and memory updating, formal belief
revision, database/version-control conflict resolution, legal interpretation of
superseded rules, anything that bears on "an agent must stop applying a rule
that was cancelled and keep applying the ones that were not."

## What you reviewed before, and what has changed

Your previous review is `results/reviews/2026-09-13-a-screen-backontrack-astra.md`
(verdict: OFF TRACK, 20%, below 25%). Read it first. Everything below postdates
it and you have not seen any of it. Re-derive your forecast; do not anchor on 20%.

Changes since, all CPU-only:

1. **The mislabelled population is corrected.** You found that
   `stale2.py` called request 1 "no supersession yet" for every session, which
   is false for the 12 reinstatement sessions. The population key is now derived
   (`alt_was_in_force`) and tested over all 624 pool sessions
   (`tests/test_a_screen_supersession.py`).
2. **A baseline results document** — `results/a-screen/RESULTS-BASELINE.md` —
   with the corrected four-cell table, Fisher p = 0.0025 on request 1 and
   p = 0.139 on request 2, family/lifecycle/transition breakdowns, and a stated
   confound list.
3. **`compare.py` refuses before it computes** (identity, completeness,
   uniqueness, replay, step-matching), with 14 mutation tests; **`preflight.py`**
   rewritten on "a check that cannot run is a FAILURE", with 52 mutation tests.
4. **The runner exception is established by recomputation**
   (`analysis/runner_equivalence.py`, `RUNNER-EXCEPTION.md`): the `off` baseline
   does not need re-running, saving ~1 GPU-hour.
5. **`names.py`'s "isolated retention" interpretation is retired**, for the two
   reasons you gave.
6. **The cf adapter finished training**: 134 optimizer steps, status complete,
   `epochs_completed` 0 (still the first pass), CE 0.0006 on never-before-seen
   examples, margin +8.8, loss already 0.0154 at step 40.
7. **A memorisation check I added** (`analysis/overlap.py`): across 192 screen
   golds the closest of 2,304 training golds scores 0.254 difflib / 0.329 token
   Jaccard at MAXIMUM, median 0.124 / 0.244, 0/192 above 0.70.
8. **An instrument defect I found in my own analysis**: run under a bare
   `python3` without pytest, `contracts.run_tests` returns False for every suite,
   so all 96 replies classified "neither" and both contrasts read p = 1.000 — a
   clean, plausible, entirely empty table. Both scripts now self-check.
9. **The design's resolution floor**: with 0 discordant pairs at n = 36 the
   registered conservative paired interval is still +/- 11.5 points. A
   wholly-positive interval needs 10 wins with 0 losses, 12 with 1, 14 with 2.

## The questions, in priority order

1. **Is candidate A a substantive recombination or a meaningless permutation?**
   It is completion-token cross-entropy on gold plus `0.1 * L_DPO` (beta 0.1,
   frozen-trunk reference) where the rejected response is the gold under the
   SUPERSEDED convention. You previously identified Context-DPO (Bi et al., ACL
   2025), Counterfactual DPO (Butcher 2024), IOPO and CRPL as prior art. Is
   anything left that is both substantive and defensible? Answer plainly,
   including "no" if that is the answer.

2. **Is "conditional revision" — the alternative you named: switch when
   applicable, preserve unaffected behaviour, restore when reinstated — actually
   better?** Is IT prior art? Is it a permutation? Does the existing four-lifecycle
   screen (stable / replacement / scope / reinstatement) already operationalise
   it, and if so what would have to change to test it as a claim rather than as
   a taxonomy? Is there published work on scoped or partial rule revision in
   LLMs that makes this dead on arrival too?

3. **Given the +/- 11.5-point resolution floor, is the remaining 1 GPU-hour
   worth spending?** Consider that it cannot resolve a modest effect, that
   cf-vs-off cannot attribute anything to the counterfactual term, and that the
   matched SFT arm is a further ~2.5 GPU-hours. Is there a cheaper experiment
   that discriminates better — including CPU-only ones, or ones on a smaller
   trunk?

4. **Attack today's new work.** Is the corrected population key right, or is
   there a third case I have still mislabelled? Does the overlap measurement
   actually license "not verbatim recall", or is difflib/Jaccard on source text
   the wrong measure for that claim? Do the guards have the "passes by doing
   nothing" property you found twice before? Is `RESULTS-BASELINE.md` honest
   about its selection effect and its confounds, or does any sentence in it
   overclaim?

5. **What am I not thinking of?** Other fields, other framings, other
   workloads, other cheap decisive tests. This is the part Brian asked for
   explicitly.

## Output

End with one line in this form:

`VERDICT — <ON TRACK|OFF TRACK> — <N>% artifact-success forecast, <above|below>
25%; <the single most important action>.`

Grade findings low/medium/high/critical. Cite files as
`/home/bmarti44/stencil-llm/<path>:<line>`. Never delete or soften a prior
finding — mark it resolved or refuted with the evidence.
