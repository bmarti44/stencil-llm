codex
NOT CLEARED. T2 is decision-relevant, and T3 does not need A1 false-selection certification, but five HIGH issues change execution.

1. HIGH — T2’s recurrent training contract is not executable

[t2t3-prereg-draft.md:18](/home/bmarti44/stencil-llm/results/t2t3-prereg-draft.md:18) combines session state with T1’s shuffled event batches. Freeze:

- State reset per session; events ordered by `(work_turn, step)`.
- Session-sequence batches, not shuffled rows; specify batch size, masking, loss normalization, BPTT/detach behavior.
- Score from the pre-write state, then update from the current event; otherwise the controller can become an extra feed-forward layer.
- Exact warm-start artifact and whether shared T1 parameters remain trainable.
- Parameter counts for every contender, matching controller-specific parameters—not totals dominated by the common T1 head—within 10%.

2. HIGH — event-only evolution narrows the oscillator claim and makes the probes ambiguous

State updated only at timing fires tests opportunity-indexed recurrence, not an oscillator evolving through tokens or instruction changes. That is still useful, but must be labeled accordingly. Under this clock, inert-token insertion does not advance phase; it only perturbs `h20`.

For the fast path, keep the cached event clock and narrow the claim. Define a nonzero probe metric such as mean held-out CE:

- inert insertion: `CE_inserted <= 1.10 * CE_original`;
- phase scramble: `CE_scrambled >= 1.20 * CE_original`, plus at least one decision change.

Leakage-relative degradation is undefined when baseline leakage is zero—the certification trigger. Freeze the scramble operation and seed.

3. HIGH — T2’s post-screen path is incomplete

[t2t3-prereg-draft.md:38](/home/bmarti44/stencil-llm/results/t2t3-prereg-draft.md:38) must specify:

- Only the mechanically selected winner may use block B.
- Pilot eligibility requires zero calib leakage plus the existing address, recall, and margin screens.
- Block-B risk failure closes T2 without trying a runner-up.
- An A1 coverage void may consume E once for the identical frozen policy; a second void closes inconclusively.
- A block pass proceeds to the registered behavioral dev table. Certification alone proves safety, not usefulness.
- Nonzero leakage means ranking-only science and no generation pilot. This resolves the current contradiction where an oscillator can “earn a pilot” yet be ineligible for certification.

B and E are currently untouched.

4. HIGH — T3’s wrong-authoritative-span risk is unmeasured

The structural guard proves provenance, so an A1 false-selection certificate would indeed be vacuous. But it does not prove semantic correctness of the scheduled type.

T0.3 tested a same-type live span at the wrong moment and a non-live span at the right moment; it never tested another type’s authoritative span. The implementation confirms this at [t0_cost.py:107](/home/bmarti44/stencil-llm/scripts/t0_cost.py:107).

Before the grid, run a paired audit using the actual four schedules. Classify scheduled presses as:

- matching-type moment;
- wrong-type authoritative span at a moment;
- no recognized moment.

Measure paired ΔU, parse/exec loss, and changed-output rate at both gains. If every cell’s schedule-frequency-weighted expected ΔU is nonpositive, skip the grid. Replace “safety by construction” with “provenance safety by construction; semantic mistargeting is measured separately.”

5. HIGH — T3’s grid and decision table are underdefined

[t2t3-prereg-draft.md:63](/home/bmarti44/stencil-llm/results/t2t3-prereg-draft.md:63) needs:

- Exact scheduler origin/reset, zero-based step rule, ledger-order/update behavior, and no-live behavior.
- Remove T2-supplied gain/phase: T2 does not define such an output, and its event clock is incompatible with T3’s token clock.
- Include the reactive-only arm or explicitly pin its same-seed artifact; otherwise marginal contribution cannot be computed.
- Define marginal closure exactly as  
  `(A_rhythm+reactive - A_reactive) / (A_oracle - A_base)`.
- Freeze selection and tie-breaking across both rhythm and combined arms.
- Preserve T4: any closure ≥0.25 with failed validity triggers T4 rather than closing T3.
- Remove “certification-equivalent” for validation. Validation measures final usefulness; it is not a false-selection confidence bound.

The four-cell same-dev comparison followed by naming one cell for sealed validation is acceptable multiplicity handling once the selection rule is frozen.
