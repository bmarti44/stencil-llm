# SLAB-2 Amendment 4 + DEV re-pilot for gpt-6-astra (2026-09-07): fix the composition defect, swap the endpoint

Source: results/composition-pilot-6-review-opus.md and the addendum on results/quick-checks/composition-pilot-6/
README.md. Read both fully (file:line given). Register "SLAB-2 Amendment 4" in tests/fixtures/slab2_cpu_report.md
BEFORE code, then:
PART 1 (CPU) — the proven defect:
1. COMPOSE delivery WITH format. renderer.py:90-106 never composes the task-scoped `delivery` obligation with
   `format=compact`; register.py:437-449 sorts that row LAST, immediately before "Apply the active rules...", and
   slab2.py:107 renders it as the actionable imperative "trailer delivery=ready...". Result: R prints
   `delivery=ready` in 25/34 compact rounds while N never does. Fix the composition so a live `format=compact`
   obligation suppresses or rewrites the delivery row's rendering rather than leaving two contradicting imperatives;
   keep it arm-neutral and value-literal. Prove the fix with the run's own control: re-render the 34 compact
   rounds from the SAVED pilot-6 registers and assert the composed block no longer emits the contradiction.
2. Secondary renderer hygiene (bytes named in the review, none proven causal — do them because they are cheap and
   they shrink the block): drop the dead `provenance`/`scope` tokens (renderer.py:101-102, ~23% of block tokens);
   de-duplicate the run-on style gloss (renderer.py:19-23,96-100); stop retargeting value-free tombstones to the
   current live version (renderer.py:60-89).
PART 2 (CPU) — the endpoint, pre-registered before any GPU work:
3. PRIMARY ENDPOINT becomes PER-OBLIGATION ADHERENCE AT THE OBLIGATION'S CHANGE ROUND, episode-paired, exact test,
   with the episode as the unit. Joint final success becomes a DESCRIPTIVE secondary (Q qualified 0/8; the 4-trait
   conjunction is 0/128 all-arms-agree, so it is unmeasurable and must not gate anything).
4. Drop `delivery_scope` (0/44 in all five arms; scored only against Q). De-conjoin style/language from breakage.
   Fix the vacuous `widths==[]` pass (slab2.py:624-625 region). Re-label Q as a FRESH-CONTEXT REFERENCE, not a
   ceiling. DECLARE O explicitly as a byte-identical replication of R (renderer.py:136) and decide, stating the
   reason, whether to keep it as a 128-round determinism receipt (0.587 GPU-h) or drop it from the larger test.
5. Tests for every item; run tests/test_focus_slab2*.py + tests/test_no_side_effect_imports.py; commit with explicit
   pathspecs; record the new pinned green SHA in tests/fixtures/slab2_cpu_report.md.
PART 3 (GPU <= 1.5 h, only after Part 1-2 are committed and green, from the new pinned SHA; RUNNING.flag under
results/quick-checks/composition-pilot-7/): the DEV re-pilot — 8 DEV episodes x arms R/N/T/Q at 16 rounds (drop O
if Part 2 decided to), determinism replay first.
PRE-WRITTEN READING: ELIGIBLE = the composition defect is gone (R's compact-round `delivery=ready` emissions fall
to <= 2/34 and format adherence R >= 26/34) AND execution/caps/floor gates hold as in pilot 6 AND the PRIMARY
per-obligation change-round endpoint is computable with nonzero denominators for >= 2 obligations in >= 6 episodes
AND the measured projection for the 64-episode run <= 12 GPU-h -> the LARGER TEST IS AUTHORIZED on that endpoint.
INELIGIBLE with the failing item. Do NOT re-run joint final success as a gate.
Outputs under results/quick-checks/composition-pilot-7/ (README with the readings, records <= 10 MB, summary);
item in results/quick-checks/README.md; WORKLOG (<= 6 lines). Commit with explicit pathspecs; no push; stop/rm only
your own container; never signal any process; never read anything under data/bench; DEV only.
