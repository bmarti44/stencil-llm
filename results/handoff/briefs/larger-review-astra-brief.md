# Independent review of the completed larger test for gpt-6-astra (CPU only) — 2026-09-07

You built and ran this experiment. Review it as an ADVERSARIAL AUDITOR of your own work, exactly as you did in
results/full-program-review-astra.md, where you correctly identified your own errors across the program. An Opus
maximum-reasoning reviewer is auditing the same run independently; do not read its file
(results/larger-test-review-opus.md) if it appears, and do not coordinate — two independent reads are the point.
THE FROZEN RESULT STANDS. Nothing you find may change, rerun or reinterpret it. Do not touch the GPU, any
RUNNING.flag, any container, or any code. Never signal any process. Never read anything under data/bench.

Subject: results/larger-test/RESULTS.md + REGISTRATION.md + records + summary + server log; contract = SLAB-2
Amendment 5; authorization = results/composition-pilot-7-review-opus.md; frozen SHA
95fa7fc0c006518ef84c1ea20c152c079ae1798a. Reported: FAIL on the conjunction; failing clause = register-arm episode
breakage exceeds plain history by more than one (R 20 vs N 14). Primary passed overwhelmingly: delivery 40/0/24 over
64 paired episodes, one-sided p = 9.09e-13, Holm 2.73e-12; format 24/9/25, p = .0068, Holm .0135; indent 9/5/40,
p = .212 with a negative missing-write sensitivity. Descriptive: any-breakage R 20 / N 14 / T 29 / Q 7 of 16;
any-nonwrite R 13 / N 2 / T 19; zero caps; joint final R 12 / N 5 / T 14.

Answer, with file:line and recomputed numbers:
1. ACCOUNTING AND INTEGRITY: 3,328 unique scheduled records; 64/64 complete in R/N/T; frozen SHA actually ran; the
   registration commit precedes the first evaluation record; the verdict came from the frozen larger_reading() and
   not from hand computation; the bank was opened once; the midpoint cross-run reproducibility control's measured
   divergence and whether the primary's margin survives it.
2. WHERE YOU MIGHT STILL BE WRONG: apply your own audit's lesson list. Name every place this run could be
   overstating or misreporting, including any place the RESULTS prose asserts more than the records support, any
   pseudo-replication, any denominator that differs between arms, and any metric that is not arm-neutral.
3. THE 13 REGISTER-ARM NON-WRITES versus 2 for plain history: classify all 13 by cause with literal outputs. Then
   the 20 breakage episodes. Is the excess the lock/format artifact family that produced four ineligible pilots, a
   cost of the rendered block, or something else? Give the exact episode-level paired test on breakage with its
   interval. Explain why T, which renders correct prose every turn, has MORE breakage (29) and more non-writes (19)
   than R, and what that implies about attributing harm to rendering at all.
4. WAS THE HARM CLAUSE WELL-FORMED? It was calibrated on eight DEV episodes. Apply your own pilot-7 lesson: a gate
   must be applied to its own negative control at the registered unit before freezing. Would this clause have
   failed an arm that cannot suffer the mechanism's harm? State plainly whether the FAIL reflects a real cost or a
   mis-set bar, and say which without softening it.
5. CLAIM SENTENCES: reconcile with Section 4 of your full-program audit. Write the exact sentences a write-up may
   contain and the ones it may not, now using the final numbers rather than placeholders. Address head-on whether
   an overwhelming primary with a failed conjunction is a positive result, a negative result, or an inconclusive
   one, and what the honest headline is.
6. THE SINGLE MOST INFORMATIVE SUCCESSOR, with a cost and a new honest lineage, given that this bank is now spent.
Grade findings low/medium/high/critical. Write ONLY results/larger-test-review-astra.md and commit it with an
explicit pathspec (git add -f); no push. Report back a 12-line summary whose last line is your honest headline for
this experiment.
