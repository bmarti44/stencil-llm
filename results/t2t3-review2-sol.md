codex
NOT CLEARED. Four HIGH issues remain.

1. HIGH — controller architectures and scramble operation are still underfrozen

[t2t3-prereg-draft.md:29](/home/bmarti44/stencil-llm/results/t2t3-prereg-draft.md:29) promises parameter counts before training but leaves outcome-relevant choices unspecified: candidate-feature pooling, controller dimensions/activations, state routing, `rho/omega/tau` parameterization and initialization, null-oscillator period, and extra-column initialization in the warm-started head.

Register an architecture/count table or code digest before training. Also formalize:

```text
z_pre = transition(z_previous, D)
logits = scorer(current_event, z_pre)
z_next = write(z_pre, current_event)
```

“Permute phase components across events” is ambiguous and can leak future state. Define it within each `(session, type, complex-component)` while preserving each event’s magnitude, with no cross-session or future-content movement. Require the inert CE bound separately for both 32 and 128 tokens.

2. HIGH — T2’s screens and terminal table remain incomplete

The T1 zero-NULL gate checked every inactive candidate-bearing event, not merely target hazards; see [t1_train.py:98](/home/bmarti44/stencil-llm/scripts/t1_train.py:98). T2 could achieve zero target-hazard leakage while introducing off-target leaks and then burn block B.

Register:

- Winner metric may remain target-hazard leakage.
- Pilot eligibility requires zero false-selection sessions across all inactive candidate-bearing calib events, with target-hazard leakage reported separately.
- Certification precedence: `k_false > 3` is policy `FAIL` regardless of hazard coverage; only `k_false <= 3 && n_h < 112` is `VOID`.
- Replace “registered behavioral dev table” with a T2-specific table. T1’s mid-band retraining fallback was already consumed. Recommended: ≥0.50 plus validity passes; ≥0.25 with failed validity triggers T4; safe `[0.25,0.50)` is a partial result and closes T2 without retraining; otherwise close. Preserve the registered headroom/redraw rule.

3. HIGH — T0.3b’s gating estimator is not reproducible yet

[t2t3-prereg-draft.md:71](/home/bmarti44/stencil-llm/results/t2t3-prereg-draft.md:71) requires 200 pairs per gain, but period changes the scheduled-step distribution. Different pooling choices can flip the `>0` decision.

Freeze:

- At least 200 deterministic single-intervention pairs per `(P,g)` cell.
- Selection order for scheduled interventions.
- Unpressed/base trajectories define the schedule; each paired branch applies exactly one press.
- `expected_ΔU_cell = sum(ΔU_i)/n_cell` directly. Category frequencies are diagnostic, not a separately adjustable weighting.
- Same registered `U` and `BROKEN` definitions as T0.3.

4. HIGH — T3 finalist selection is still discretionary

“Named via fresh preregistration after the grid” at [t2t3-prereg-draft.md:107](/home/bmarti44/stencil-llm/results/t2t3-prereg-draft.md:107) is not a mechanical multiplicity rule.

Before the grid, freeze:

- Among valid full-pass rhythm cells, select maximum closure; deterministic safety tie-break such as lower `g`, then larger `P`.
- For the partial path, use that mechanically selected rhythm cell’s combined arm.
- The combined arm must itself pass the validity rule before becoming finalist.
- Define whether T4 triggers inspect rhythm, combined, or both, and precedence when another valid finalist exists.
- The later preregistration may record the mechanically selected cell and validation machinery; it may not choose among cells after viewing results.
