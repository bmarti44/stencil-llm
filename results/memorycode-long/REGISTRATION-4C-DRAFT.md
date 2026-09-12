# DRAFT, NOT REGISTERED: Exp 4C, one final confirmation of the unchanged 4B artifact on the frozen SCREEN-LONG cohort, through the package's own generation path

Status: DRAFT written 2026-09-12 after Exp 4B FAILED its qualification and after Astra's
next-path consult (`results/reviews/2026-09-12-next-path-consult-astra.md`). It is NOT in
force. It becomes a registration only if Brian explicitly overrides rule D2 (both policy
revisions are consumed) and this file is renamed `REGISTRATION-4C.md` with that override
quoted in its header, before any generation. Nothing below may run before that.

## Disclosure (verbatim from the consult, adopted)

This registration was written after examination of the Exp 4 and Exp 4B SETUP-LONG
results, the short-cohort results, the CPU register diagnostics, the options and literature
memos, and the implementation and result audits. These observations informed continuation
and the analytical design. Exp 4B failed its registered qualification on a focus-only
output failure; the opposing base-only failure and positive descriptive fractional effect
were known before this registration. Both permitted policy revisions were already consumed.
Brian's explicit override of that stop is required; the prior registration remains
FAILED / NOT PROVEN. We retain the frozen artifact intervention, items, prompts, decoding,
checker and per-constraint estimand, but replace the SETUP failure launch gate with
final-sample inference on net failure excess and an affirmative noninferiority requirement.
We also replace the primary percentile-bootstrap decision with a paired-mean t-test and
matching interval, retaining the original bootstrap and sign test as reported companions.
Earlier development included SCREEN metadata and label-derived CPU diagnostics, the switch
away from the overflowing register, post-hoc first-query fractional analyses, trunk and
estimand selection, and selection of the oracle qualification threshold. Earlier instrument
repairs included cumulative oracle replay and Unicode speaker parsing, with the associated
oracle regenerations and the recorded focus regeneration. SCREEN is generation-unseen, not
item-unseen; SETUP will not enter its estimator. Nothing is newly fit or tuned on evaluation
prompts or recorded responses. Gold labels remain confined to evaluation and disclosed
diagnostics, never the deployed intervention. All prior results will remain published, and
no terminal outcome of this registration permits another policy, workload, sample-size or
gate revision.

Added after the 4B parity check (`parity-4b.json`): the research runtime and the package's
`transformers` path render identical prompts (32/32) and the off switch is exact (16/16),
but their greedy outputs differ token-for-token on 32/32 generations. Exp 4C therefore
generates THROUGH THE PACKAGE (`deploy/stencil_focus`, `transformers` bf16, greedy), so the
result is attributable to the published artifact by construction. The research runtime is
not used for any Exp 4C generation.

## Items, arms, prompts (unchanged from Exp 4B)

All 128 frozen SCREEN-LONG items (`items.json`, seed-1 split), first query, frozen required
families and structure, equal item weights; no SETUP pooling, no reserve, no subgroup.
Arms: the identical assembled 4B artifact (`deploy/stencil_focus/build/hub-4b`, trunk
`Qwen/Qwen3-4B` revision `1cfa9a72…`, package sha recorded) with `stencil_focus=true`
(`role_evicted`, W = 3,584, E = 256) versus `stencil_focus=false`; greedy, 512 new tokens,
300-s deadline; prompt token counts asserted equal per item before generation; no oracle.

## Estimands and tests

Primary: Δ = E[D_i], D_i = fraction_required(on) − fraction_required(off) per item, equal
weight per retained required regex check within an item, then per item; missing structure
and terminal timeouts score 0. Decision: two-sided paired-mean t-test and its 95% interval;
the percentile bootstrap (seed 0, 10,000 draws) and the exact sign test are reported as
companions and never substitute. Power (from the 16 Exp 4B records, s_D = .1026): standard
error 0.91 points at N = 128; 80%-power detectable gain 2.5 points (5.1 at twice the spread).

Output-failure guard (replaces the launch gate): F_ia = any of invalid / capped / degenerate /
timed out; H_i = F_i,on − F_i,off; η = E[H_i] with a paired-mean 95% interval at N = 128
(the registered conservative discordance interval if all H_i are identical). PROVEN requires
the interval's upper endpoint ≤ +5 points (affirmative noninferiority). Stated limitation:
with s_H = .365 the half-width is ≈ 6.3 points, so under zero true net harm the guard
certifies only ≈ 34% of the time; ≈ 419 pairs would be needed for 80% noninferiority power,
which exceeds the budget. That is accepted as the price of an affirmative safety standard.

## Readings (exhaustive)

| condition | reading |
|---|---|
| missing/invalid primary records, ceiling breached, configuration mismatch, or package parity (prompt + off switch) fails | INCOMPLETE |
| primary interval wholly below 0 | HARM |
| primary interval includes 0 | NOT PROVEN, final |
| primary interval wholly positive AND failure upper bound ≤ +5 | PROVEN (claim: higher mean per-constraint compliance under imposed context eviction on coding-session histories; not agentic, not functional correctness) |
| primary positive, failure interval crosses +5 | POSITIVE EFFICACY / OUTPUT-SAFETY UNRESOLVED; artifact claim NOT PROVEN |
| primary positive, failure lower bound > +5 | POSITIVE EFFICACY / DEMONSTRATED OUTPUT HARM; artifact claim NOT PROVEN |

Any failure interval wholly above 0 is reported as increased failures regardless of the
margin; an interval crossing 0 is never called equivalence. Strict compliance, categories
and companions are reported with every reading. No interim looks.

## Budget and execution

256 generations through the package; the package path was not timed at 3.6k tokens, so a
4-item package pilot (the same four longest SETUP-LONG items) sets t_max; ceiling = 1.5 ×
t_max × 256 enforced cumulatively across chunks (`--ceiling-seconds`, marker file,
INCOMPLETE on breach). Expected ≈ 3 GPU-h at ~40 s/generation. 55-min reservations, 50-min
runner budgets, 32 GB declared (one 4B copy resident). Records atomic per arm with the
package sha, trunk revision, config, prompt sha256 and prompt token count. Implementation:
a `run-package` phase in `scripts/memorycode_screen.py` (or a sibling script) that builds
prompts via `FocusSession` and scores with the vendored checker; one Astra implementation
review (rule D1) before launch; result audit after.

## Publication on PROVEN only

`bmarti44/stencil-focus-qwen3-4b` with `MODEL_CARD-4b.md` updated to the Exp 4C table; the
card states the scope ("coding-session instruction retention under context eviction"), the
FAILED Exp 4B qualification, and that the agentic claim awaits Exp 5. On any other reading
the artifact is withheld as a claim; the negative is published in `RESULTS-4C.md`.
