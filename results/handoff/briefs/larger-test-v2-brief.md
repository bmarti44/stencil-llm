# THE LARGER TEST for gpt-6-astra (GPU <= 12 h): 64 fresh agentic episodes under Amendment 5 (2026-09-07)

AUTHORIZED by results/composition-pilot-7-review-opus.md (read it and the addendum on results/quick-checks/
composition-pilot-7/README.md in full before anything else). No further DEV re-pilot. This supersedes
results/handoff/briefs/larger-test-brief.md.
PART 1 (CPU) — register "SLAB-2 Amendment 5" in tests/fixtures/slab2_cpu_report.md and freeze it in ONE commit
BEFORE opening any evaluation episode:
1. EPISODE-LEVEL UNIT MADE GLOBAL: every gate and every statistic uses the episode as the unit. Delete the
   per-round compact limit (the review proved it invalid: the block-free arm N scores 3/34 against a limit of 2,
   McNemar p = 1.0000, both arms 1/8 at the episode unit).
2. The DETERMINISTIC CPU RE-RENDER CONTROL becomes the ONLY blocking composition check: assert every scheduled
   compact register renders with no delivery row and no `trailer delivery=` string, with bit-exact hashes.
3. PRIMARY = the DELIVERY family of the per-obligation change-round endpoint, episode-paired, within-episode
   averaging before the sign, exact one-sided R > N, Holm over the three families (delivery, format, indent).
   Joint final success stays DESCRIPTIVE ONLY (it is unmeasurable: Q 0/8, all-arms-agree 0/128).
4. Freeze `larger_reading()` IN CODE so the verdict is computed mechanically, plus the evaluation bank frozen by
   id-hash, and a REGISTERED CROSS-RUN REPRODUCIBILITY CONTROL (the review measured ~94% cell reproducibility
   across container restarts: 10 of 166 byte-identical payloads returned different completions, 6.02%,
   CI 3.3-10.7%) — re-issue a fixed set of >= 40 payloads mid-run and report the divergence rate beside the result.
5. PRE-DECLARE the known confounds: (a) T's oracle prose scores 7/8 on delivery, so a PASS credits "the current
   effective value restated at request time", NOT the register data structure per se; (b) history is never
   re-composed (loop.py:363), so old blocks persist in context; (c) the system prompt's worked example
   (slab2.py:71-73) is an arm-invariant driver that pushes even the fresh-context arm to 33/34 on format.
6. Data lineage line first: fit-on none; development-on = the 8 DEV episodes only; evaluated-on = the 64 frozen
   evaluation episodes, opened once, never before now.
PART 2 (GPU) — run it: arms R, N, T (Q as a fresh-context reference on the pre-registered 16-episode subset;
O dropped as byte-identical to R). 16 rounds. The qualified vLLM image/flags; your own container; isolated
checkout of the frozen SHA verified before any GPU access; the pre-run reverse-order concurrency-4 determinism
replay; fixed concurrency schedule recorded; same-run journal with per-round output hashes; cooperative deadline
at 11.5 GPU-h including load and cleanup; records preserved before aggregates; never drop an episode.
PRE-WRITTEN READING (frozen in `larger_reading()`): PASS = the primary exact one-sided test on delivery is
significant after Holm across the three families AND the register arm's episode-level breakage does not exceed the
block-free arm's by more than one episode AND the CPU re-render control passes AND the accounting is complete for
all 64 episodes. FAIL = completed but the conjunction is unmet. INCOMPLETE = a budget or deadline stop with unrun
episodes (never drop pairs, never a partial pass). Report per-family results, per-episode tables, the
reproducibility control, cost audit, and the claim ceiling from results/focus-mechanism-composition-v2-astra.md.
Outputs under results/larger-test/ (REGISTRATION.md committed first, then RESULTS.md, records <= 10 MB each,
summary, server log; HTTP journals out of git with hashes); item in results/quick-checks/README.md; WORKLOG
(<= 8 lines). Commit with explicit pathspecs (git add -f); no push; stop/rm only your own container; never signal
any process; never read anything under data/bench.
