# Exp 4B registration: the same head-to-head on the Qwen3-4B trunk with a per-constraint primary

Registered 2026-09-12 before any Qwen3-4B generation on the LONG cohort. This is a NEW
registration (plan rev 7.2, section J), chosen by Brian ("pick the most likely direction")
from `results/reviews/2026-09-12-options-memo.md` after Exp 4's SETUP-LONG read a strict
floor at 1.7B under a corrected oracle. It is the program's SECOND AND LAST policy revision
under rule D2 (amendment 1 of Exp 4 was the first): a NOT PROVEN or HARM reading here ends
the program with a published negative and no further revision. Everything not restated
below is inherited unchanged from `REGISTRATION.md` (amendments 1-2 and the BUDGET line):
items, window W = 3,584, reminder budget E = 256, the `role_evicted` focus policy, token-
matched prompts, the vendored checker with frozen applicability, timeouts, completeness,
reservation rule, manifests, label rule, no SCREEN oracle.

## What changes

1. **Trunk: Qwen3-4B** (`models/qwen3-4b.pt`, hand-rolled runtime; HF copy
   `models/qwen3-4b-hf`). The artifact becomes `bmarti44/stencil-focus-qwen3-4b` (frozen 4B
   trunk + the same `stencil_focus` package). Nothing is claimed about the 1.7B artifact,
   whose SETUP-LONG result is published as a descriptive negative (section "Disclosures").
2. **Primary estimand: per-constraint compliance with a frozen denominator.**
   `fraction_required` (memorycode.py) = the mean official family score over the families
   REQUIRED by the query (CONTRACT.md amendments 3/3b; stored per item in `items.json`); an
   absent required parent scores 0.0; a generation without the required class/function
   scores 0.0; optional families an output happens to introduce are IGNORED (Astra floor
   consult, finding 3: the unfrozen fraction changed denominators across arms). Items whose
   query requires nothing are inapplicable (0 of 144). Primary contrast: `focus` − `base`
   on `fraction_required`, paired by item, N = 128 SCREEN-LONG, reported in points of 100:
   paired mean difference with a 95% percentile bootstrap over items (rng seed 0, 10,000
   draws) and an exact two-sided sign test on discordant items
   (`memorycode_screen._paired_mean_bootstrap`). Strict compliance with the McNemar /
   union-bound interval of Exp 4 is reported ALONGSIDE as the secondary, never as the gate.
3. **Qualification gate on SETUP-LONG (16 items × base/focus/oracle = 48 generations) before
   any SCREEN spend.** The SCREEN launches only if ALL hold on SETUP-LONG at 4B:
   (a) `oracle` mean `fraction_required` ≥ 0.20 (the trunk can apply stated conventions at
   all; the 4B short cohort read 0.255); (b) `focus`-only output-failure discordance ≤ 5%;
   (c) the `focus` − `base` bootstrap upper bound > 0 (harm not already demonstrated at
   n = 16). Otherwise the program STOPS: SETUP-LONG is published as the negative, the SCREEN
   is never opened.
4. **Execution matrix:** SETUP-LONG base/focus/oracle = 48; SCREEN-LONG base/focus = 256;
   total 304 generations (+4 pilot, +32 parity). No register arm at 4B (the register is
   structurally inert on this cohort, `auto/summary.json`). Output directories:
   `setup_long-4b-role_evicted/`, `screen_long-4b-role_evicted/`.

## Readings (exhaustive; SCREEN-LONG only, policy role_evicted, primary complete)

- PROVEN: bootstrap interval entirely above 0 AND `focus`-only output-failure discordance
  ≤ 5% of items → the 4B artifact is published with the table (per-constraint gain; strict
  alongside; "coding-session instruction retention", not "agentic", until Exp 5).
- POSITIVE-WITH-OUTPUT-FAILURE-EXCESS: interval above 0, excess > 5% → not PROVEN;
  descriptive publication with the failure table.
- NOT PROVEN: interval covers 0 → final; published negative; artifact withheld as a claim.
- HARM: interval entirely below 0 → published as demonstrated harm; program ends.
- INCOMPLETE: any frozen SCREEN-LONG item lacks a terminal base or focus record → no
  confirmatory reading.
- DESCRIPTIVE: SETUP-LONG and every oracle comparison.

## Power, stated

On the 1.7B SETUP-LONG items the paired per-constraint differences had a standard deviation
of about 11 points (mean −5.2, interval [−10.6, −0.4] at n = 16). At N = 128 the bootstrap
standard error of the mean is about 1 point if the 4B spread is similar and about 2 points
if it doubles. Approximate 80%-power detectable gains (normal approximation) are 2.6 points
at the observed SETUP spread and 5.3 points at twice that spread; these are planning
approximations, not guarantees. The bootstrap interval determines the primary efficacy
reading. The sign test is a descriptive directional companion and may disagree with it (four
gains of 1.0 and 124 ties give +3.1 points [0.8, 6.3] with sign p = .125 and still satisfy
the efficacy gate). Strict compliance is descriptive and cannot establish or rescue the claim.

## Budget (filled from the 4B pilot before launch)

Pilot: `scripts/timing_pilot.py --family memorycode-long --model 4b` = the 4 longest
SETUP-LONG windows at W = 3,584, 512-token cap; writes
`results/timing-pilot/memorycode-long-4b.json`. Ceiling = 1.5 × t_max × 304 generations;
SCREEN INCOMPLETE if its cumulative generation time exceeds 1.5 × t_max × 256. Reservation
peak declared 14 GB (the 4B short run peaked near 9.7 GB). Chunks ≤ 55 min, `--budget-
minutes 50`. BUDGET line appended below once measured.

## Data lineage

Unchanged: `vendor/memorycode` sha `1ab87e11…`; the same seed-1 split (`items.json`: 16
SETUP-LONG, 128 SCREEN-LONG, 68 reserve never opened). Nothing in the artifact was fit on
MemoryCode; the role rule has no parameters; only `oracle` uses labels to construct its
intervention; item selection, scoring and error diagnostics read labels.

## Disclosures (what informed this registration)

- Exp 4 (1.7B) SETUP-LONG, corrected oracle, 16 items: strict 0/16 on all arms; per-
  constraint `fraction_required` base .120 / focus .069 / oracle .063; focus − base −5.2
  points [−10.6, −0.4], 1 win / 7 losses / 8 ties (descriptive, n = 16). The 1.7B SCREEN
  was not run; this is reported explicitly as "primary not run" with the reason.
- Exp 3b at 4B (short cohort, 16 items, post-hoc per-constraint look): history .031,
  restate_all .099, register .203, oracle .255; restate_all − history +6.8 [0.0, +14.6]
  (3/0), oracle − history +22.4 [+3.1, +43.8] (6/1). These post-hoc looks on SETUP cohorts
  informed the trunk and estimand choice; no SCREEN item has been generated at either trunk.
- Astra's quick-test template for this path asked for fresh authored items; this
  registration keeps the frozen MemoryCode-derived items instead (external workload, already
  enumerated, budgeted), accepting the conjunction floor on strict and moving the primary to
  the per-constraint score with a frozen denominator.
- Implementation review (rule D1): one Astra read-only review of this file and the code
  before the SETUP-LONG launch; result audit after RESULTS.md.

## Artifacts

`results/memorycode-long/`: `setup_long-4b-role_evicted/summary.json` (qualification),
`screen_long-4b-role_evicted/summary.json` (primary, `--primary fraction`),
`RESULTS-4B.md`, `manifest-4b.json` (sha256 of every record), `parity-4b.json` (package
parity on the 16 SETUP-LONG items, both flag states, before publication).

## BUDGET line (measured, 2026-09-12 10:55Z, before any 4B LONG generation)

Pilot `results/timing-pilot/memorycode-long-4b.json`: the same 4 longest SETUP-LONG items at
W = 3,584 tokens, 512-token cap, Qwen3-4B, GPU otherwise idle (no co-resident process):
t_max = 47.6 s/generation (two items at the cap at 10.7-10.8 tok/s; one stopped at 481
tokens in 45.1 s, one at 144 tokens in 13.8 s), mean 38.5 s, peak 9.14 GB allocated /
9.66 GB reserved. The 4B trunk ran faster than the 1.7B pilot (5.2 tok/s) because that pilot
was measured under the peer's co-resident run. The fixed spending allowance is 1.5 times the
measured pilot rate; exhaustion remains INCOMPLETE whatever its cause.
Registered per-generation budget 1.5 × t_max = 71.5 s; the generation deadline stays the
inherited 300 s (a timeout is a terminal strict failure and scores 0.0 on the primary).
Ceiling for 304 generations = 21,725 s = 6.0 GPU-h worst case; expected at the pilot mean
≈ 3.3 GPU-h; plus the 4-generation pilot (2.6 min, done) and the 32-generation parity check
(≤ 38 min). Reservations: 55-min slices with `--budget-minutes 50`, peak declared 14 GB.
SETUP-LONG (48 generations) is expected to finish in one slice (worst case two). The
SCREEN-LONG run is INCOMPLETE, never rescued, if its cumulative generation time exceeds
1.5 × 47.64159221400041 × 256 = 18,294.37 s (5.08 GPU-h); the full-precision pilot value is
authoritative (see the amendment below for the enforced ceilings).

## AMENDMENT 1 (Astra implementation review, 2026-09-12 11:40Z, before any 4B LONG generation)

Review: `results/reviews/2026-09-12-exp4b-impl-review-astra.md` (BLOCK, nine findings). All
required edits are applied below and in code before the SETUP-LONG 4B launch; none changes an
arm, an estimand or a threshold. Numbers here are recomputed from the committed files.

1. **Weighting unit, stated precisely (finding 1).** For item *i*, freeze the list of
   `history_regex` entries whose family belongs to `required_i`. Each retained regex CHECK
   receives equal weight, including multiple checks belonging to the same family (98 of 144
   items have more checks than distinct required families; item 352-99 has 12 required
   families and 32 checks). The item score is their arithmetic mean, with absent required
   parents scored zero; missing required structure sets the entire item score to zero (it
   gates the item and adds no denominator term, so it does not double-count). Items receive
   equal weight in the cohort mean. `fraction_required` now raises on malformed input (score /
   check length mismatch, a required family without a check) instead of truncating.
2. **Bootstrap convention (finding 7).** The interval endpoints are order statistics 251 and
   9,750 of the 10,000 sorted bootstrap means (250 draws trimmed from either end); coverage is
   approximate. Empty or unequal-length inputs return an explicit empty result or raise; a
   complete SCREEN with zero oracle records summarizes without error (tested).
3. **Qualification is a mechanical object (finding 3).** `summary.json["qualification"]` on
   `setup_long-4b-role_evicted/` (written by `summarize --primary fraction`) has `status`
   PASSED / FAILED / INCOMPLETE. It is INCOMPLETE unless all 16 frozen items carry valid
   terminal base, focus AND oracle records; PASSED only if (a) `mean_fraction_required.oracle`
   ≥ 0.20, (b) `output_failure_excess_over_base.focus.excess_fraction` ≤ 0.05 (zero focus-only
   failures at n = 16), (c) `focus_vs_base.fraction_required_bootstrap.upper_points` > 0.
   `upper == 0` fails (c) without demonstrating harm. The SCREEN launch script reads this
   field and refuses to start on anything but PASSED. A stopped SETUP run is published; no
   tuning or pooling of SETUP records into the SCREEN.
4. **Record validity and the registered N (finding 4).** The summary trusts no CLI label: a
   record enters only when its manifest names the summarized model, the registered window
   (3,584) and reminder budget (256) and every arm's first generation is terminal (eos / cap /
   timeout) and scored; offending ids are listed under `invalid_record_ids` and make the
   primary INCOMPLETE. `primary_complete` additionally requires `items_scored` == the frozen
   cohort size (an inapplicable item cannot shrink N silently). The Exp 4B confirmatory
   reading requires model `4b`; the fraction reading on any 1.7B directory is DESCRIPTIVE.
   `_record_matches` now also compares `window` and `budget_tokens` on resume. The old
   output-dependent `fraction` fallback is reached only by records without per-family scores,
   which the validity check excludes from any confirmatory summary.
5. **Timeouts (finding 5).** A terminal timeout scores 0.0 on `fraction_required` in the
   generation record and on legacy recomputation (tested with an otherwise compliant output).
6. **Cumulative ceilings, enforced (finding 6).** `run --ceiling-seconds X` reconstructs the
   cumulative generation seconds of the run's arms from every saved record across chunks
   before each item, stops when X is reached and writes `BUDGET_EXHAUSTED.json`; `summarize`
   recomputes the spend and reads INCOMPLETE when the marker exists or the spend exceeds the
   ceiling, even if the crossing generation completed. Registered values (1.5 × t_max with
   t_max = 47.64159221400041 s, full precision): per generation 71.46238832100062 s;
   SETUP-LONG 48 generations → 3,430.1946394080296 s; SCREEN-LONG 256 generations →
   18,294.371410176158 s; total 304 → 21,724.566049584188 s (6.03 GPU-h). Expected at the
   pilot mean: SETUP 30.8 min, all 304 generations 3.25 GPU-h. With the 300-s deadline the
   chunk rule stops starting items at minute 35 of a 50-minute budget for SETUP (three arms)
   and minute 40 for SCREEN (two arms).
7. **Disclosures (finding 8).** The post-hoc 4B short-cohort fractional analysis uses only
   the first query of each of the 16 items, matching the LONG protocol (.031 / .099 / .203 /
   .255 for history / restate_all / register / oracle; averaging all queries per item would
   give .094 / .133 / .224 / .278). The oracle qualification threshold 0.20 was chosen after
   these descriptive outcomes were available. Instrument repairs before this registration
   (plan/LEDGER.md, 2026-09-12 entries): the oracle live set is now the cumulative event
   replay (verified against `history_regex` on all 224 items), the speaker split is
   name-based and Unicode-safe, and the LONG SETUP focus output of item 314-49 was regenerated
   because the ASCII-only split had left it without candidates; the oracle arm of all 16
   SETUP-LONG items and the Exp 3b oracle were regenerated for the same reason. Label use,
   precisely: only `oracle` uses gold labels to construct its intervention; item selection,
   scoring and the error table read labels; the focus policy reads none.
8. **Memory reservation (finding 9).** The runner constructs the 4B model in float32
   (4,022,468,096 parameters ≈ 16.1 GB) before loading the bf16 checkpoint (≈ 8.0 GB) and
   casting, so the loading peak on unified memory is ≈ 24 GB plus process overhead, not the
   9.66 GiB CUDA allocator peak the pilot recorded after loading. The reservation for every
   Exp 4B slice is 32 GB. The pilot's `peak_*_gb` fields are GiB (bytes / 2³⁰) measured by
   the CUDA allocator after loading; the report now says so.
9. **Sanity check of the consumer on the committed 1.7B SETUP-LONG records** (same code
   path, descriptive): 16/16 valid, per-constraint base .120 / focus .069 / oracle .063,
   focus − base −5.17 points [−10.56, −0.43], cumulative primary-arm generation time 2,708 s.
