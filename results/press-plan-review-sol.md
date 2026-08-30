codex
NOT CLEARED. No critical findings; six high findings block P0 as registered.

1. **HIGH — P0 is not an offline/cached phase as claimed.**

[PRESS-PLAN.md:39](/home/bmarti44/stencil-llm/PRESS-PLAN.md:39) says no new GPU runs except P0.4, but:

- The 941-fire artifact contains only aggregate counters, not event identities, h20 states, candidate scores, or rejection reasons ([t2b_press_audit.py:87](/home/bmarti44/stencil-llm/scripts/t2b_press_audit.py:87)).
- Selector training holds h20 features only in memory and saves heads/thresholds, not features ([t2_train_selector.py:79](/home/bmarti44/stencil-llm/scripts/t2_train_selector.py:79), [t2_train_selector.py:224](/home/bmarti44/stencil-llm/scripts/t2_train_selector.py:224)).
- Qwen computes but discards attention weights; P0.2 cannot run from h20 alone across layers ([qwen3.py:105](/home/bmarti44/stencil-llm/src/stencil/qwen3.py:105)).
- P0.3 and P0.5 explicitly require generation replays too.

Before P0, register one deterministic trace-collection GPU pass that stores raw per-event h20, timing logits, every candidate/span/source, all score variants, chosen candidate, rejection reason, cell label, and raw count numerators. Either add a last-row attention-summary hook or defer P0.2. Treat the old 12.96M/941-fire set as legacy exploration, not fresh evidence.

2. **HIGH — the harness cannot perform the candidate-level experiment P0/P1 describes.**

The current address callback returns a type, after which the runner redirects it to the authoritative ledger span ([t2_runner.py:164](/home/bmarti44/stencil-llm/src/stencil/t2_runner.py:164)). If the head selects a quoted same-type lookalike, the harness nevertheless spotlights the correct authoritative span. Conversely, P0.3 cannot deliberately spotlight that wrong quoted span through this API. The active-ledger `key in spans` check can also make post-guard false-press counts partly vacuous.

Before P1:

- Make the candidate policy return the exact selected token span.
- Apply that exact span in the autonomous arm.
- Keep type-to-authoritative-span redirection as a separately named structured baseline.
- Record pre-guard non-NULL decisions, guard rejections, and actual applied presses separately.
- Add a deterministic wrong-span non-vacuity test.

Also, 130/130 is calibration-set address accuracy ([t2_train_selector.py:215](/home/bmarti44/stencil-llm/scripts/t2_train_selector.py:215)); the validation audit cannot split theta rejection from out-of-ledger address rejection. Do not call WHERE independently proven until P0 records that split.

3. **HIGH — the registered Bayes threshold mixes incompatible estimands.**

The 1.7% is `7/409`, the gross parse-loss rate of the whole correct-span oracle policy ([t2b-val.json:46](/home/bmarti44/stencil-llm/results/qwen/t2b-val.json:46)). It is not a false-press probability and not a per-press cost; oracle press counts were never recorded. Exec loss was `11/409 = 2.69%`. Likewise, +14.5 is aggregate policy-level adherence lift, not benefit per correct press.

Therefore [PRESS-PLAN.md:57](/home/bmarti44/stencil-llm/PRESS-PLAN.md:57) and the already-created helper at [press_stats.py:21](/home/bmarti44/stencil-llm/src/stencil/press_stats.py:21) are not evidentially valid, although the algebra is formally correct.

P0.3 must use paired rollouts with exactly one intervention and estimate benefit `B` and harm `H` over the same unit and horizon. Then `p*=H/(B+H)`. If adherence, parse, and execution cannot be converted using a preregistered utility weight, retain a Pareto/risk gate and do not manufacture one scalar `p*`. Specify whether the beta sweep means absolute `{0.25,0.5,1}` or current-beta multiples `{0.5,1,2}`.

4. **HIGH — the negative gate contradicts the new risk policy and overstates its confidence bound.**

The arithmetic is:

- `0/18` one-sided 95% upper bound: 15.33%.
- `0/300`: 0.9936%.

But the latter holds for independent Bernoulli trials. T2 sessions emit multiple correlated opportunities per work and session. Moreover, [PRESS-PLAN.md:90](/home/bmarti44/stencil-llm/PRESS-PLAN.md:90) still requires zero observed false presses, while [PRESS-PLAN.md:156](/home/bmarti44/stencil-llm/PRESS-PLAN.md:156) says measured nonzero risk replaces zero-FP everywhere.

Register:

- The risk level and confidence level.
- The independent unit—prefer independently seeded one-negative fixtures, not hundreds of tokens from a few sessions.
- A gate of `U95(false-press rate) <= registered alpha`, rather than necessarily `k=0`.
- Separate component false selections, applied false presses, and behavioral harm.
- Score-family selection before the untouched calibration sample; otherwise grid/head selection invalidates the simple bound.

5. **HIGH — closure and stop rules do not form a complete decision table.**

Using the recorded rounded rates:

- Dev headroom is `0.569−0.376=0.193`; closure 0.5 requires 47.25% adherence, a 9.65-point lift. The separate 10-point gate is slightly stronger.
- Validation headroom is 14.5 points; closure 0.5 requires only 7.25 points, so the 10-point gate is substantially stronger.

Those thresholds are coherent, but the plan never defines the formula, raw-count calculation, or an oracle-headroom precondition. T2 already demonstrated why `oracle−base >= 0.10` is necessary.

More seriously, P1 passes only at closure ≥0.5 ([PRESS-PLAN.md:92](/home/bmarti44/stencil-llm/PRESS-PLAN.md:92)) but stops only below 0.25 ([PRESS-PLAN.md:99](/home/bmarti44/stencil-llm/PRESS-PLAN.md:99)). The entire `[0.25,0.5)` band has no registered action. The stated dependency ladder also conflicts with P1 closing the autonomous line while P2/P4 are presented as downstream redesigns.

Add an exact decision table: headroom-inconclusive, pass, fail, and at most one named middle-band fallback. Calculate closure from raw paired numerators on the same seeds, never rounded JSON rates.

6. **HIGH — seed and adaptive-selection discipline is not frozen enough.**

“Fresh 13.0xM blocks” and “one validation per surviving policy” at [PRESS-PLAN.md:160](/home/bmarti44/stencil-llm/PRESS-PLAN.md:160) are insufficient. The latter permits several autonomous policies to inspect validation and then report whichever passes.

Before collecting P0 data, freeze:

- Exact seed ranges and counts for trace/train/calibration/dev/validation.
- The old 12.96M validation seeds as legacy exploratory data only.
- Exact theta, beta, top-k, and score grids plus all tie-breaks.
- Separate data for attention-head selection and evaluation.
- One named autonomous finalist for sealed validation. Other policies are exploratory unless multiplicity is handled explicitly.
- A statement that P1–P4 optimizer/architecture details will receive fresh preregistration before their respective launches.

7. **MEDIUM — later rungs are sketches, not executable registrations, and the order wastes work.**

- P5 is already the existing oracle/structured-eligibility arm: `_oracle_moment` plus an active-ledger check ([t2_runner.py:157](/home/bmarti44/stencil-llm/src/stencil/t2_runner.py:157)). Fold it into every replay as a baseline; do not make it a separate final rung.
- P0.2 needs new attention instrumentation and head-selection discipline. Defer it unless the simpler score matrix fails.
- P2 has no training objective, exact period grid, update/clear dynamics, or gate. Defer the inverted-default variant until ordinary soft rhythm demonstrates headroom.
- P3 cannot use “KV rollback”: `Qwen3.forward` has no KV-cache interface ([qwen3.py:132](/home/bmarti44/stencil-llm/src/stencil/qwen3.py:132)), and `score_work` scores completed code, not a local incomplete unit ([t2_runner.py:59](/home/bmarti44/stencil-llm/src/stencil/t2_runner.py:59)). Start with deterministic prefix recomputation and preregister the boundary/verifier before building caching.
- P4’s inert-token probes require recomputing Qwen features; they cannot operate solely on the nonexistent original cache. If retained, run the head-only bakeoff before generation-heavy P2/P3.

8. **MEDIUM — P0.5’s proposed inference is not identified.**

A reactive press cannot repair the already-scored violating work, and some violations have no later active opportunity of that type. Therefore approximately zero aggregate recovery would not establish that violations are “unrecoverable”; it could reflect opportunity placement.

Register the eligible post-feedback denominator, a reactive-oracle ceiling, the exact per-type refractory/reset rule, behavior after update/clear, and both conditional recovery and whole-session lift.
