# Round 8: verdict on rev 5 at the owner's numeric bar, with measured data

Two things changed since round 7 (`results/reviews/2026-09-13-direction-adversarial-rev7-astra.md`).

**1. The owner set the bar.** "Good chance of actually working" now means **≥ 25%** on your
artifact-success forecast (owner, 2026-09-13; `plan/LEDGER.md` 07:40Z). Your round-7 numbers
for rev 5 were ~20% as written and ~27% conditional on the registered pre-check passing.

**2. Measured data exist.** All in `results/contracts/` and `plan/LEDGER.md` (entries 05:50Z
to 08:50Z), produced by the unmodified Qwen3-4B package with contracts stated immediately in
the request (no session history), greedy decoding, joint outcome J = executable functional
tests AND contract tests in a sandbox (`src/stencil/contracts.py`; tasks in
`src/stencil/contract_projects.py` (development, exposed) and
`src/stencil/contract_projects_reg.py` (registered, frozen by hash in
`results/contracts/REGISTRATION-PRECHECK.md` before the run)):

| run | tasks | J | functional | note |
|---|---|---|---|---|
| dev16 plain | 16 dev | 8/16 | 15/16 | exposed |
| dev16 explicit | 16 dev | 8/16 | 14/16 | same tasks + an explicit "contracts override the existing code's old convention" paragraph; users project (in-file precedent contradicts the contract) 1/4 → 1/4 |
| **registered pre-check** | 32 new | **14/32 = 0.438 [0.264, 0.623]** | 24/32 = 0.750 [0.566, 0.885] | rule J ≥ 16 AND functional ≥ 20 → **INELIGIBLE** (functional passes; J fails by 2) |

Failure modes (all model-side; every output parsed, none truncated): missing-record policy
ignored (mutating a None lookup, auto-creating an unknown account, swallowing a transport
error); frozen immutability half-applied (new object returned, not stored); in-file precedent
copied over the stated contract (validation placed where the existing function places it;
naming kept as the existing function's pattern) even under the explicit override paragraph;
return shape ignored. Per family J/8: return shape 6, error surface 5, logging 4,
immutability 3, dependency 3, validation 3, missing-record 2, naming 2.

Per the registration, the rev 5 program stops before training. Do NOT read `data/bench/`.

## Questions

1. Reading the data. Is INELIGIBLE the right reading of 14/32 (functional 24/32)? Does the
   precedent-probe result (an explicit override instruction changes nothing; the model
   copies the file's own pattern) change your view of what limits contract adherence at
   4B: capability, attention to in-context precedent, or something else? Cite research on
   in-context precedent/imitation overriding instructions in code models if it exists.
2. Rev 5 at the 25% bar, with this data. Give your artifact-success forecast for candidate
   A (counterfactual LoRA on current-rule execution; `results/reviews/2026-09-13-direction-proposal-rev5.md`)
   now: (a) as registered (domain as is, pre-check failed); (b) with the domain narrowed to
   the families the unmodified model already handles (return shape, error surface, logging:
   15/24) and the precedent-dominated families (naming, validation, missing-record) kept as
   the trained target rather than as an eligibility condition; (c) any other reframing of A
   the data support. State plainly whether each is ≥ 25%. Note that the measured failures
   (stale precedent beating the stated rule) are the exact phenomenon A's objective
   targets; say whether that raises or lowers A's odds and why.
3. Other directions at 25%. Given the measured data, do any of your round-6 candidates
   (B recovery training, C selective memory, E gated intervention, D contrast decoding,
   F transactional validation) or anything else reach ≥ 25% for the owner's artifact
   (published model wrapper that beats itself unmodified on long coding sessions, joint
   outcome)? Rank with numbers.
4. Verdict per criterion for the best candidate at the 25% bar: DISPROVED / NOT DISPROVED,
   with the decisive reason. If NOT DISPROVED, list the minimum registration requirements
   for its screen (arms, N, outcome, guard, compute) so the author can write it without new
   scientific choices.
5. Anything the owner is not thinking of, including whether the 25% bar plus this data
   makes the search well-posed, and what the pre-check failure implies for the published
   4B package's honest card.

Cite sources with identifiers. Write plainly. Do not soften. Do not add models, benchmarks
or review stages.
