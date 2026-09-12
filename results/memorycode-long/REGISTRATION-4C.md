# Exp 4C registration: final package confirmation of the unchanged Qwen3-4B artifact

Registered 2026-09-12 14:30Z, before any Exp 4C generation. Authority: Brian delegated the
continuation decision ("use astra to unblock you, go with its deep web research result
decision"; "let it bring forward its own decisions as well"), and Astra's binding decision
(`results/reviews/2026-09-12-unblock-decision-open-astra.md`) is quoted verbatim in
`plan/LEDGER.md` at 2026-09-12 14:05Z. This is the program's SINGLE exception to rule D2. Exp 4B
remains FAILED / NOT PROVEN permanently. No terminal outcome of this registration permits
another policy, workload, sample-size, gate or test revision. The scientific specification
below is Astra's section 3, adopted verbatim with the mechanically filled values marked ⟨⟩.

## Lineage and disclosure

Fit-on: nothing. Intervention selection and analytical development were informed by Exp 4/4B
SETUP results, short-cohort first-query analyses, SCREEN metadata and label-derived CPU
diagnostics, the overflowing-register result, trunk/estimand selection, oracle-threshold
selection, the options/literature memos, and implementation/result audits. Earlier repairs
included cumulative oracle replay, Unicode speaker parsing, oracle regenerations, the recorded
314-49 focus regeneration, and cumulative-budget accounting. Package parity results were also
known (prompts byte-identical 32/32; off switch 16/16; 25/32 differing texts vs the research
runtime).

Astra's consultation reconstructed all 212 eligible LONG item definitions and checked package
prompt lengths on the 196 non-SETUP items; their model outcomes were not generated.
Evaluation is therefore generation-unseen, not item-unseen. Nothing is fit, selected or tuned
using evaluation responses. Gold annotations supply cohort/scoring metadata and disclosed
diagnostics only; they never enter the intervention. All prior results and this
outcome-informed continuation remain disclosed.

## Candidate order and sample size

Reconstruct `long_items` from vendored MemoryCode revision
`1ab87e119b2f9a498de8075219e1c07f6041b394` using the existing tokenizer and unchanged
enumeration rules. Apply the existing seed-1 dialogue shuffle. Exclude its first 16 SETUP
dialogues. The remaining ordered list contains 196 dialogues; its first 128 must exactly
reproduce the original SCREEN definitions (`scripts/memorycode_4c_items.py` asserts this on
dialogue, session, queries, required, structure and history_regex).

Original `items.json` SHA-256: `affe6877f059e5f58466023fe70c45cefeadca4b98d1a036832901d14073ce1a`
(⟨verified 2026-09-12 14:20Z⟩). SHA-256 of the complete 196 evaluation IDs, joined with `\n`
and a final newline: `3125634e658bf35fc20e8555199abb5cc8f30ada4c14f328caba08fa7e43ca28`
(⟨reproduced, `items-4c-candidates.json`⟩).

Let t_max be the maximum elapsed generation-call time from the eight prescribed pilot calls
below. Set **N = min(196, floor(28,800 / (3 t_max)))**. If N < 128, do not evaluate: terminal
INELIGIBLE-BUDGET. Otherwise select exactly the first N dialogues in that fixed order and
freeze their complete definitions (`items-4c.json`, with the frozen-ID SHA-256) before
evaluation. No outcome, compliance score, failure rate or subgroup statistic participates in
this rule. No post-launch extension or reduction is permitted; `items-4c.json` is written once.

## Arms and artifact

The currently assembled Qwen3-4B package (`deploy/stencil_focus/build/hub-4b`), unchanged
learned weights at upstream revision `1cfa9a7208912126459214e8b04321603b3df60c`, with a
cryptographic manifest of every weight shard, tokenizer/configuration file and remote-code
module (⟨`package_manifest` in the runner: per-file SHA-256 plus one aggregate⟩). The installed
runtime versions (torch, transformers) and the resolved attention backend are recorded in
every record; the same environment is used for qualification, evaluation and release
verification.

Generate through the package's public session interface only. Off: `stencil_focus=false`.
On: `stencil_focus=true`, unchanged `role_evicted` policy, renderer, sentence selection and
packing. W = 3,584, E = 256, batch size one, bf16, greedy, one beam, 512 newly generated
tokens, 300-second deadline. Both arms use identical effective generation settings and fresh
session/cache state. The package's effective EOS setting is frozen explicitly (⟨recorded per
record as `eos_token_ids`⟩).

Each item uses its existing first query and supplied historical conversation. No oracle,
repair, resampling, generated historical trajectory, attention modification or checker
feedback is introduced. Assert equal actual prompt lengths before generation and
prompt-plus-output allocation at most 4,096 tokens. Execute in candidate order, alternating
off-first and on-first by item index (even index: off then on; odd: on then off).

## Primary

Freeze the `history_regex` entries whose families are required by each query. Give each
retained check equal weight, including repeated checks within a family; then give each
dialogue equal weight. Missing required parents receive zero; missing required structure or a
terminal timeout sets the item score to zero. Preserve the inherited scoring of capped outputs
and count caps in the failure guard.

Let D_i = S_i,on − S_i,off. Report the mean, sample SD, the two-sided paired t-test of E[D] = 0,
and its matching 95% interval (mean ± t_.975,N−1 · s_D / √N). Positive efficacy requires the
lower endpoint strictly above zero. The inference assumes independent dialogue units and has
approximate coverage for this bounded, discrete distribution.

If s_D = 0, do not emit a zero-width inferential interval: use the bounded-variable Hoeffding
interval [mean − √(2 ln 40 / N), mean + √(2 ln 40 / N)] ∩ [−1, 1] and the conservative two-sided
p bound min(1, 2 exp(−N · mean² / 2)), explicitly labelled as the degenerate-case fallback.

Always report the original paired percentile bootstrap (10,000 draws, seed 0, lexicographically
sorted IDs, order statistics 251 and 9,750) and the exact sign test as companions. Neither can
replace the primary decision.

## Output-failure guard

Retain the existing definitions of invalid, capped, degenerate and timed out. F_ia is their
union, H_i = F_i,on − F_i,off, η = E[H]. Report both discordance directions, all category
counts, the mean of H, a paired t-test against zero and the matching 95% interval [L_H, U_H].
If s_H = 0, use the existing conservative paired interval (separate two-sided 97.5%
Clopper-Pearson intervals for on-only and off-only discordance probabilities, opposing
endpoints subtracted). Report exact McNemar p, with p = 1 for no discordances.

**The combined statistical gate requires U_H ≤ 0.05.** Neither an observed net difference
below five points nor nonsignificant harm suffices. An interval wholly above zero establishes
increased failures under the registered procedure even when the increase remains within the
margin. Report failure-rate equivalence only when the entire interval lies inside
[−0.05, +0.05]. Crossing zero alone establishes neither equivalence nor noninferiority. No
primary-compliance equivalence margin is registered.

## Technical qualification and timing (44 generations)

Before evaluation, use SETUP IDs 359-99, 352-99, 351-99, 302-49, in that order, once per flag
state: eight timing calls. Record outputs for reproducibility; do not score them for any
efficacy or failure-rate launch gate. Then complete package-off outputs for the other 12
SETUP items; generate all 16 off prompts through plain upstream `AutoModelForCausalLM`; reload
the package and replay the original eight calls. Require 16/16 off/plain raw-token matches and
8/8 package replay matches, using identical EOS conventions. Compare prompt bytes and token
IDs separately from lengths. Load package and plain models sequentially. Script:
`scripts/memorycode_4c_qualify.py`, output `results/memorycode-long/qualification-4c.json`.

## Budget

Maximum additional GPU allocation: 10 hours, divided into qualification ≤ 3,600 s; evaluation
generation calls ≤ 3 t_max N ≤ 28,800 s; evaluation loading and other resident-process
overhead ≤ 2,700 s; final clean-environment verification ≤ 900 s. All attempts, interrupted
work and verification count (⟨the runner appends every attempt, including interrupted ones, to
`attempts.jsonl` in the output directory⟩). Unused allowances do not authorize additional
experiments. Reservations ≤ 55 minutes, worker budgets ≤ 50 minutes, declared memory 32 GB, one
Stencil GPU process at a time; stop starting work with sufficient time for outstanding
deadlines and the five-minute reservation buffer; per-slice and cumulative ceilings enforced.
Complete within three working days of implementation start (⟨start 2026-09-12⟩). Failure to
qualify, complete, audit or verify within the applicable limits ends execution; budgets and N
are never enlarged.

## Records and completeness

Each terminal arm saved atomically with: raw generated IDs including EOS, scored IDs with the
terminal EOS removed, decoded text, actual stop reason, timeout/cap indicators, scores, failure
categories, the prompt text, prompt IDs hash and count, reminder text and sentence counts,
timing, configuration identities, package/environment hashes and item/checker hashes. Resume
only missing work under the same frozen manifest; never overwrite or regenerate a valid
terminal output. Missing, duplicate, mismatched, malformed or unscored required records prevent
confirmation; no item is dropped or replaced.

## Readings and reporting (mechanical; technical status, then efficacy, then the guard)

| condition | terminal reading | publication |
|---|---|---|
| qualification fails, reconstruction differs, or timing gives N < 128 | INELIGIBLE; efficacy NOT PROVEN | repo qualification report; no HF release |
| evaluation incomplete, required records invalid, configuration mismatch, or budget exceeded | INCOMPLETE | repo report with missingness; no claim; no HF release |
| primary upper endpoint < 0 | HARM | repo result incl. failure evidence; no HF release |
| primary interval includes 0 | NOT PROVEN, FINAL | repo result; demonstrated output harm reported alongside; no HF release |
| primary lower > 0, U_H > 0.05, L_H ≤ 0.05 | POSITIVE EFFICACY / NONINFERIORITY UNRESOLVED; NOT PROVEN, FINAL | repo tables; no HF release |
| primary lower > 0, L_H > 0.05 | POSITIVE EFFICACY / DEMONSTRATED EXCESS OUTPUT HARM; NOT PROVEN, FINAL | repo result; no HF release |
| primary lower > 0, U_H ≤ 0.05, but audit or release verification unacceptable | STATISTICAL GATES PASSED / ARTIFACT RELEASE UNVERIFIED | repo result and the release defect; no HF release |
| primary lower > 0, U_H ≤ 0.05, complete valid records, accepted audit and release verification | PROVEN, SCOPED | exact evaluated artifact pushed to `bmarti44/stencil-focus-qwen3-4b` with the card wording below |

No interim efficacy summaries or decisions; the summary is computed once when every
registered pair is terminal. Always report strict compliance and its paired interval/McNemar,
absolute fractional scores, primary and companion statistics, failure categories and
discordances, prompt accounting, missingness, cost and all prior disclosures. The original
128-item subset and the added reserve subset are descriptive breakdowns only.

Card wording on PROVEN, SCOPED (values substituted mechanically): "PROVEN for higher average
required-check compliance on a MemoryCode-derived coding-session test under imposed context
eviction. On N=[N] paired dialogues, enabling `stencil_focus` changed mean compliance from
[off] to [on]: [difference] percentage points, 95% interval [lower, upper], two-sided p=[p]. The
net output-failure difference was [difference] points, 95% interval [lower, upper]; its upper
bound met the preregistered +5-point noninferiority margin. Strict compliance was [off]/[N]
versus [on]/[N]. These results were generated through this package against the identical
artifact with its modification disabled. The learned Qwen3-4B weights are unchanged. The
modification restates selected evicted user sentences within a 256-token reminder and a
3,584-token total prompt budget. This establishes average partial convention compliance in the
stated test. It does not establish fully compliant or functionally correct code, accurate
relevance selection or retirement of superseded instructions, or free-running agentic
performance. Absolute scores and output failures are reported above. Exp 4B previously failed
qualification. This final registration followed outcome-informed development and an explicit
owner-delegated stop-rule override. Earlier research-runtime results were not attributed to
this package because generation parity failed. The complete development history, prior
negatives, registration, outputs and audit accompany this release." If failures significantly
increase while remaining within the margin, append: "Enabling the modification demonstrably
increased output failures, although the increase satisfied the registered noninferiority
margin."

## Operational sequence (Astra section 4)

1. Ledger quote and this registration; `items-4c-candidates.json` committed; `items.json` and
   prior registrations untouched.
2. CPU implementation: explicit 4C analysis mode in the summarizer (`--analysis 4c`), full
   artifact/environment fingerprint validated on resume and summary (shard hashes, package
   aggregate, torch/transformers versions, attention backend), the item manifest and
   timing-only N, complete accounting incl. interrupted attempts, raw-EOS records, release
   manifest checks; the retired register's `auto/` files are not a dependency of the 4C
   summary; synthetic-record tests for every terminal reading, changed package hash, missing
   pairs, zero variance, timeout zero-credit and ceiling exhaustion.
3. One focused Astra implementation review of the NEW runner, analysis, sample-size and
   publication-gate paths (unchanged package prompting and reviewed checker code waived).
4. Qualification run; freeze N, IDs, budget and fingerprints before any evaluation generation.
5. The single evaluation, resumed across slices without inspecting efficacy.
6. One summary; one Astra result audit.
7. Publication gate: statistical success + accepted audit + clean-environment reproduction →
   HF push of the exact evaluated package bytes (documentation excluded from the fingerprint).
   HF authentication is an operational dependency only.
