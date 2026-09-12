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
if it doubles, so the design resolves mean gains of roughly 3-5 points; it cannot resolve a
1-point gain. A positive reading needs most items to move in the same direction, not a few
large outliers.

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
