# Exp 4 registration: long-horizon coding-session head-to-head (artifact vs itself, modifications off)

Registered 2026-09-11 before any GPU spend on the LONG cohort (plan/BACK-ON-TRACK-PLAN.md
rev 7.1, section H; Astra rounds 3-4 applied). Script: `scripts/memorycode_screen.py
--cohort long`; helpers in `src/stencil/memorycode.py` (`long_items`, `split_long`,
`build_long_prompt`, `pack_long`, `render_long_reminder`, `output_failures`); tests in
`tests/test_memorycode.py`. Every scientific choice is fixed here; the implementation may
not add one. The evaluation is labelled MEMORYCODE-DERIVED, LONG COHORT: nothing here is
comparable to the MemoryCode paper's native protocol.

## Claim under test

The artifact `bmarti44/stencil-focus-qwen3-1.7b` with `stencil_focus=true` (frozen Qwen3-1.7B
trunk + the frozen instruction register rendered as a reminder, section G) complies with
the coding conventions in force more often than the identical artifact with
`stencil_focus=false`, on coding sessions whose history exceeds the imposed prompt budget.

## Data lineage

- Workload: `vendor/memorycode` (sha `1ab87e11…`, Apache-2.0; pinned in
  `data/bench/pins-manifest.json`). LONG items = the 212 (dialogue, session) pairs whose
  full native history prompt exceeds 3,584 Qwen3 tokens (min 3,693 / median 15,623 /
  P90 51,734 / max 61,046) and whose session has history-regex checks and at least one
  earlier instruction session. `items.json` (written 2026-09-11): seed-1 shuffle of the
  dialogue ids, one item per dialogue → 16 SETUP-LONG, 128 SCREEN-LONG, 68 reserve
  (never opened in this program).
- Nothing in the artifact was fit on MemoryCode: the sentence classifier and the
  relations head were trained on authored data (data/classifier/, MODEL_CARD.md); the
  role rule has no parameters. Only the `oracle` arm reads `dialogue["instructions"]`.

## Prompt construction (both arms; native single-message format)

W = 3,584 tokens is the IMPOSED prompt budget (the local config supports 40,960; the
budget is the experimental condition). `build_long_prompt`: the thread is the whole
session text (sessions 0..s, native `\n\n Session i \n\n` separators) truncated at a
TOKEN boundary keeping the NEWEST tokens so that the complete prompt (frame + thread +
reminder + request + chat template) is ≤ W; the modified arm pays for its reminder with a
shorter thread. Both arms' actual prompt lengths are stored per item; the summary reports
the maximum absolute difference (expected ≤ 2 tokens from retokenisation at the cut) and
the count of items with any difference. One generation per item (the first
`history_eval_query`), greedy, 512-token cap, deadline 300 s, hand-rolled deterministic
runtime (`stencil.qwen3.Qwen3`, Qwen3-1.7B only; no 4B retry in Exp 4).

## Arms

| arm | reminder | window |
|---|---|---|
| `base` | none (`stencil_focus=false`) | newest W tokens |
| `focus` | live rows of the frozen FOCUS-3 register (`memorycode.auto_live`, task scope `MAIN`, per-window turns, overflow counted) built over ALL mentor lines of sessions 0..s−1, chronological, packed newest-first to E = 256 tokens including the header `Earlier instructions still in force:` | newest W − E_actual tokens |
| `oracle` | label-derived live set (`topics.json` texts of `dialogue["instructions"][s]`), same renderer, budget and packing | same rule |

`oracle` runs on SETUP-LONG always and on SCREEN-LONG only if the pilot's t_max ≤ 60 s
(budget section). It is a descriptive ceiling, never a shipping candidate.

Frozen fallback (section G, decided before any LONG generation): if the primary reads
NOT PROVEN, `focus` is rerun ONCE with the zero-parameter role rule over the
TRUNCATED-AWAY region (every mentor sentence outside the base window, newest-first, same
renderer/budget), base outputs reused; both attempts reported; two fixed policies at
one-sided .025 each bound the family-wise false-positive rate at .05; the selected
policy's interval is not a simultaneous 95% interval. The fallback code path
(`--policy role_evicted`) is added before it is needed, not after the primary reads.

## Outcome and checker

Vendored official `compute_score` (unmodified; the `comment` family counts a `#` inside
a string literal, recorded in CONTRACT.md). STRICT compliance per item with applicability
FROZEN from the query before generation (CONTRACT.md amendments 3/3b, stored per item in
`items.json`: `required` families and `structure`): an omitted required parent object
scores 0.0; a generation without the required class/function is strict-FALSE. The primary
cohort is fixed before generation (an item is INAPPLICABLE only when no family is
required; 0 of 144). Fractional score reported alongside. Convention compliance is the
outcome; functional correctness is neither measured nor claimed.

## Estimand, test, N, power

Primary: `focus` − `base` on strict compliance, paired by item, N = 128 SCREEN-LONG.
Exact McNemar on discordant items (two-sided p), and the conservative paired interval
(separate 97.5% Clopper-Pearson bounds on b/N and c/N, difference by union bound).
Power: wholly positive first at 10 wins / 0 losses; with 10 losses it needs 29 wins;
about 26% positive-result probability at win/loss .15/.05, about 91% at .25/.05.
N = 128 establishes a large benefit, not a modest one. Descriptive: `oracle` − `focus`
(headroom), `oracle` − `base`, mean fractional scores, reminder tokens and empty
reminders, the error table of the register (false admissions, missed instruction
sessions, overflow events), prompt-length match.

Output-failure guard: invalid (no parsable code), truncated (hit the cap), degenerate
(4-gram repetition > 0.5) per arm, as EXCESS over `base` per item.

## Readings (exhaustive)

- PROVEN: interval entirely above 0 AND `focus` excess output failures ≤ 5% of items.
- POSITIVE-WITH-OUTPUT-FAILURE-EXCESS: interval above 0, excess > 5%: not PROVEN;
  descriptive publication with the failure table; the fallback is NOT triggered.
- NOT PROVEN: interval covers 0 → the frozen fallback runs once; the second reading is
  final (a second null is a published negative; the artifact is withheld as a claim).
- HARM: interval entirely below 0 → published as demonstrated harm; program ends.
- `oracle` − `focus` gates nothing. The error table is published with every reading and
  is never read as evidence of accurate maintenance.

## Budget (BUDGET line added from the `memorycode-long` pilot before launch)

Pilot: `scripts/timing_pilot.py --family memorycode-long` = the 4 longest SETUP-LONG
windows at W = 3,584, 512-token generation, peak memory and co-resident pids recorded.
Ceiling = 1.5 × t_max × (2 × 144 + 16 oracle-on-SETUP + 128 fallback rerun) = 1.5 ×
t_max × 432 generations, plus the 4-generation pilot and the 32-generation parity check;
`oracle` on SCREEN-LONG (+128) only if t_max ≤ 60 s. Chunks ≤ 50 min under
`tools/gpu_reserve.sh`; atomic per-item records `setup_long/item-<id>.json`,
`screen_long/item-<id>.json`; INCOMPLETE on exhaustion, never rescued.

## Artifacts

`results/memorycode-long/`: `items.json`, `auto/` (register live sets + error tables),
`setup_long/summary.json` (parity/pilot cohort), `screen_long/summary.json` (primary),
`RESULTS.md`, `manifest.json` (sha256 of every record). One Astra result audit after
RESULTS.md (rule D1).

## AMENDMENT 1 (2026-09-11, before any LONG generation; instrument observation, disclosed)

The CPU register phase (`auto --cohort long`, `auto/summary.json`) ran the frozen FOCUS-3
runtime over the 144 SETUP-LONG + SCREEN-LONG items before any GPU spend. Observed:
2,370 admissions (2,401 stored rows), 32,058 overflow events on 138/144 items (the runtime skips every
message once the register holds more than 16 rows, `focus3.py:303`, and MemoryCode
sessions admit ~17 conversational sentences within the first one or two sessions),
2,776 missed instruction sessions, 0 lifecycle relations applied on SETUP-LONG, 6 empty
live sets. On this cohort the classifier register is structurally inert after the first
sessions: its reminder would be ~17 early sentences regardless of what follows.

Change, made with this disclosure and before any generation: the PRIMARY `focus` policy
for SCREEN-LONG is the zero-parameter role rule over the truncated-away region
(`--policy role_evicted`, the construction Exp 1's registered reading selected as the
default text selector). The classifier register (`--policy register`) runs on the 16
SETUP-LONG items only, as a descriptive arm with its error table, documenting the
inertness. There is now ONE primary policy and no fallback rerun: the interval of the
single primary contrast is a plain 95% interval; a NOT PROVEN reading is final. The
budget ceiling drops to 1.5 × t_max × (2 × 144 + 16 oracle + 16 register) = 1.5 × t_max ×
320 generations (+4 pilot, +32 parity). Everything else in this registration is unchanged.
The register-based automatic maintainer is therefore NOT the artifact's primary mechanism
on long sessions; the artifact's frozen configuration (plan G) is amended to match, and
the register ships, if at all, as the opt-in maintainer with its error table.

## AMENDMENT 2 (2026-09-11, before any LONG generation; Astra implementation review,
`results/reviews/2026-09-11-exp4-impl-review-astra.md`, "LAUNCH AFTER EDITS")

Supersession. Amendment 1 is a disclosed POLICY REVISION under rule D2 (one of the two
permitted per program), not an instrument fix: the CPU register phase processed the
SCREEN-LONG items and computed label-derived diagnostics (false admissions, missed
instruction sessions, overflow events, relations applied, empty live sets), so the policy
choice is item-informed; NO generated output and NO compliance outcome of any arm informed
it. With this amendment the following passages above are SUPERSEDED wherever they conflict:
the `focus` row of the Arms table (register as primary), the "Frozen fallback" paragraph,
the NOT PROVEN reading's fallback clause, the `oracle`-on-SCREEN-LONG clause, and the
budget formula with 432 generations.

The sole confirmatory contrast is `focus` (policy `role_evicted`) − `base` on strict
compliance over the frozen 128 SCREEN-LONG items of `items.json`. SETUP-LONG and every
register/oracle comparison are descriptive. No result triggers another policy attempt.
The primary interval is the conservative union-bound paired interval (separate central
97.5% Clopper-Pearson bounds, difference `[L_b − U_c, U_b − L_c]`), coverage at least
95%; no multiplicity adjustment is needed for one frozen primary contrast. Recomputed
thresholds: wholly positive first at 10 wins / 0 losses; 29 wins needed with 10 losses;
positive-result probabilities 25.8% (win/loss .15/.05) and 90.8% (.25/.05).

Execution matrix (frozen; the CLI defaults implement it): SETUP-LONG `base`/`focus`/
`oracle` = 48 generations; SCREEN-LONG `base`/`focus` = 256; SETUP-LONG register arm
(`--arms focus --policy register`, descriptive, written to `setup_long/`) = 16. Total 320,
or 356 with the 4-generation pilot and the 32-generation parity check. No `oracle` on
SCREEN-LONG. Artifact paths: `setup_long-role_evicted/`, `screen_long-role_evicted/`,
`setup_long/` (register arm); every summary records its policy.

Timeouts (registered before generation): a generation whose wall time exceeds the 300 s
deadline, however it ended (break, EOS or cap on the same step), is a TERMINAL STRICT
FAILURE, counted in the `timed_out` output-failure column, kept in the fixed denominator
and never rerun; the record stores the termination reason (`eos` / `cap` / `timeout`).

Output-failure guard, exact formula: `focus` excess = the focus-only discordance rate,
(# items where `focus` has any failure among invalid / truncated / degenerate / timed_out
AND `base` has none) / N. PROVEN requires it ≤ 0.05. Both discordance directions, the net
rate difference and the per-category counts are published alongside.

Completeness: the primary is COMPLETE only when every frozen SCREEN-LONG id has a terminal
`base` and `focus` record under the registered configuration; otherwise the summary
reads INCOMPLETE and no confirmatory reading is issued. Ancillary arms (oracle) are
summarised on the subset that has them. Confirmatory readings are issued only for
`screen_long` under `role_evicted`; SETUP-LONG and register summaries read DESCRIPTIVE.

Reservation rule: `--budget-minutes` is required (positive) for the LONG cohort; an item
starts only if its remaining arms, each at the full deadline, fit before the budget ends
(`elapsed ≥ budget − n_arms × deadline` stops the run); the timer starts at phase entry
(before the model load). Records checkpoint atomically after every terminal arm; a rerun
skips only arms that exist and refuses to mix configurations (items, tokenizer, weights,
model, policy and decoding identities are stored in every record as `manifest`).

Prompt equality is ENFORCED, not observed: `build_long_prompt` raises if the prompt does
not fit W after retrims, and the runner refuses to generate any arm whose complete prompt
length differs from `base` for the same item (CPU test over all 144 frozen items: equal on
every item, 3,584 tokens, no retrims). The eviction boundary is taken from the builder's
metadata (`cut_chars`), never rediscovered from content markers.

Label rule, precise wording: only `oracle` USES labels to construct its intervention;
item selection, scoring and the register's error diagnostics also read labels. The review
traced no label-to-`focus` path (removing the label fields left selection and rendering
unchanged on all frozen items).

## BUDGET line (measured, 2026-09-12 00:48Z, before any LONG generation)

Pilot `results/timing-pilot/memorycode-long.json`: 4 longest SETUP-LONG items at W = 3,584
tokens, 512-token cap, co-resident peer process (7.1 GiB, looped-transformer Huginn run):
t_max = 98.0 s/generation (three items hit the cap at 5.2-5.3 tok/s; one stopped at 317
tokens in 60.2 s), peak 6.86 GB allocated / 9.04 GB reserved. Registered per-generation
budget 1.5 × t_max = 147 s. Ceiling for the amended matrix of 320 generations = 47,040 s =
13.1 GPU-h worst case (every generation at the cap under contention); expected at the
pilot mean of 87.8 s ≈ 7.8 GPU-h; plus the 4-generation pilot (5.9 min, done) and the
32-generation parity check (≤ 1.3 h). Reservations: 55-min slices with `--budget-minutes
50`, peak declared 12 GB. The SCREEN-LONG run is INCOMPLETE, never rescued, if its
cumulative generation time exceeds 1.5 × 98 × 256 = 37,632 s (10.5 GPU-h).
