codex
## Not signed off

No critical findings. Four high-severity blockers remain.

### HIGH — Compaction deletes the selector’s only addressable memory

[TIMED-SELECTOR-PLAN.md:116](/home/bmarti44/stencil-llm/TIMED-SELECTOR-PLAN.md:116) deletes the ledger for base/selector/oracle, while address candidates are restricted to surviving text at [line 123](/home/bmarti44/stencil-llm/TIMED-SELECTOR-PLAN.md:123).

A contentless selector cannot recover an obligation whose text is absent. Therefore either:

- old obligations remain authoritative, making post-compaction selector/oracle success structurally impossible; or
- old obligations cease being authoritative, meaning T2 does not test long-horizon instruction retention.

The canonical live ledger must survive compaction identically for base, selector, oracle, and zero-selector. The spotlight then tests selection, not missing memory. Pinned-ledger policy also remains unspecified—placement, update behavior, and token charging must be exact.

### HIGH — Opportunity records and counterfactuals remain incomplete

The registered tuple at [TIMED-SELECTOR-PLAN.md:140](/home/bmarti44/stencil-llm/TIMED-SELECTOR-PLAN.md:140) lacks fields needed to identify and score opportunities uniquely, particularly per-argument annotations.

Require:

```text
opportunity-id, session, turn, obligation-id, target-object,
moment-class, active-expected-value, superseded-values, scorer
```

Also define stale rate exactly:

```text
numerator   = opportunities whose output obeys a distinct superseded value
denominator = all opportunities having at least one distinct superseded value
```

Invalid/missed outputs remain denominator-only.

The decisive active/absent counterfactual is still missing. T2 must include paired cases with identical syntax where a trained-type obligation is:

- active,
- absent,
- cleared,
- or present only as stale/distractor text.

The seen-type false-press gate does not guarantee these pairs exist. Without them, address/abstain can still be evaluated on an easy distribution that never forces obligation-presence reading.

### HIGH — Training, calibration, and stop behavior are not frozen

The pre-run freeze list at [TIMED-SELECTOR-PLAN.md:179](/home/bmarti44/stencil-llm/TIMED-SELECTOR-PLAN.md:179) omits:

- timing/address architecture and classes
- optimizer, steps, weighting, and negative sampling
- training-session counts
- τ and θ calibration grids/tie-breaking
- inherited β and activation duration
- exact fallback configuration

“Base + oracle rollouts … or the deviation is recorded” at [line 186](/home/bmarti44/stencil-llm/TIMED-SELECTOR-PLAN.md:186) is not a registration. Choose the policy before validation.

Because v2 supersedes the draft, it also does not clearly retain the draft stop clause. Register:

> τ and θ are calibrated once on calibration data; β=2 and current-row one-token activation are frozen before validation. Any validation gate miss stops T2; no post-validation recalibration or dose change.

Or name an exact fallback, trigger, and fresh seed block now.

### HIGH — The behavioral gate can still pass at useless absolute adherence

The repaired Pareto arithmetic at [TIMED-SELECTOR-PLAN.md:158](/home/bmarti44/stencil-llm/TIMED-SELECTOR-PLAN.md:158) fixes the unbounded-cost loophole, but not the absolute-performance loophole.

Example:

```text
base = 0%
oracle = 10%
selector = 5%
reinsertion = 5%
selector cost = 40% of reinsertion
```

This passes headroom, closure, and cost while delivering 5% adherence.

Add frozen absolute floors on both macro and micro adherence, plus a minimum absolute selector lift over base. For example:

```text
A_selector >= 0.70
A_selector - A_base >= 0.10
```

The exact values are the owner’s choice, but they must be registered before build. Also clarify that the ≥24 stale-opportunity condition refers to generator-defined stale opportunities, not actions the base happened to take.

The T1 record qualification is now honest: it establishes syntax-timed pressing of harness-selected spans, not obligation reading. The summary-baseline deferral, semantic gate, provenance rule, two OOD probes, component gates, factorial diagnostics, evidence schema, and post-build hash audit are otherwise adequately addressed.
