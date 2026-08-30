codex
Not cleared yet. The headline diagnosis is correct, but one HIGH threshold bug must be fixed before naming `cos_max` or touching block A.

## Empirical verification

The digest-checked trace recomputes as follows:

- 381 events: 323 active, 39 cleared, 19 absent, across 48 sessions.
- Legacy all-type max scores on the 58 inactive events range from `14,196.17` to `185,938.0`.
- The maximum is a cleared `prefix` event whose winning candidate is a live `doc` span—direct confirmation of cross-type contamination.
- All 58 inactive events have zero candidates matching `pred_type`.
- All 323 active events select the live same-type span under both raw-QK and cosine:
  - raw selected scores: `47,080.88–376,550.53`
  - cosine: `0.640774–0.907935`
- Among the 269 active events containing same-type lookalikes, the minimum live-minus-lookalike margin is `47,494.92` raw and `0.250697` cosine.

So yes: [t0_trace.py](/home/bmarti44/stencil-llm/scripts/t0_trace.py:116) ranged across every type, while [press_families.py](/home/bmarti44/stencil-llm/src/stencil/press_families.py:17) eliminates that contamination. The apparent autonomous separation is currently structural, not discriminative.

The claimed “~4× raw-scale drift” is not established. At the old `185,849.81` threshold, 68/323 trace active events survive—21.1%, close to calibration’s 32/130 = 24.6%. The evidence supports cross-type threshold pollution, not a fourfold scale shift. Cosine remains a sensible choice for scale invariance, but do not record the drift claim without matched-distribution evidence.

## HIGH — cosine threshold is unit-dependent and dangerously permissive

[t0_matrix.py](/home/bmarti44/stencil-llm/scripts/t0_matrix.py:59) claims to enumerate thresholds “just below” observed scores, but uses:

```python
uniq[0] - 1.0
```

Consequently:

- minimum observed cosine = `0.640774`
- frozen cosine threshold = `-0.359226`

Those are decision-equivalent on this trace because every negative is `-inf`, but radically different on the proposed hard fixtures. Almost any vaguely related candidate would exceed `-0.359`. The arbitrary `-1` also defeats the bounded-scale rationale for choosing cosine.

Replace threshold enumeration with the representable boundaries:

```python
import math

uniq = sorted({x["score"] for x in evald if x["score"] != float("-inf")})
cands_t = sorted(
    set(uniq)
    | {math.nextafter(s, -math.inf) for s in uniq}
) if uniq else [0.0]
```

With the registered higher-threshold tie-break, cosine should then freeze just below `0.640774`, not at `-0.359`.

Also remove the `-inf` exclusion from AUPRC at [t0_matrix.py](/home/bmarti44/stencil-llm/scripts/t0_matrix.py:71), because the plan specifies “active vs all.” It will remain `1.000`, but honestly: the 58 negatives rank at the bottom rather than disappearing from the calculation.

Add a scale-sensitive regression test, rerun only the offline matrix, record its new digest, and do not touch block A beforehand.

## Rulings

1. Tie-break: approve `cos_max`, conditional on the threshold fix.

Register the post-trace deterministic order:

1. `cos_max`
2. `raw_max`

Do not use `top1_top2` or `top1_logsumexp` as the runner-up without changing their singleton semantics: both return `+inf` when only one same-type candidate exists at [press_families.py](/home/bmarti44/stencil-llm/src/stencil/press_families.py:49), guaranteeing a false press on a single-lookalike inactive fixture.

Disclose that cosine was chosen adaptively after the registered AUPRC tie, based on boundedness and positive-scale invariance—not on demonstrated fourfold drift.

2. Certification vacuity: extend the fixture generator.

Certifying as-is would satisfy the literal bound while testing only “no candidate means no press.” That is not worth spending sealed block A on.

Apply the extension consistently to every certification block, not just A:

- Assign each session one deterministic inactive target, balanced across `prefix/doc/hint` and absent/cleared/stale-only cells.
- Put an S0-style, format-identical, same-type non-live note inside the surviving window of its targeted work.
- Keep it outside the authoritative ledger span so the pre-membership-guard failure definition is exercised.
- Assert that each session produces at least one timing fire of the targeted type with a same-type non-live candidate and no live same-type candidate.
- If that assertion fails, count the session as a certification failure; never silently remove it from the 160-session denominator.
- Freeze the threshold before collecting the sealed block; no recalibration from fixture outcomes.

The resulting CP bound applies to this registered hard-negative fixture distribution. Report natural S0 safety separately as structural safety.

3. Skip T1 training: approve only as a one-way shortcut.

After non-vacuous certification, behavior-test the existing policy directly. Call it “zero-new-training reuse of the previously supervised timing/address heads,” not “zero-training.”

- If oracle headroom binds, closure is at least `0.50`, and validity passes: name it a finalist and skip T1 training.
- For every other conclusive result: proceed with registered T1 training. A failure by this fixed scorer cannot close the joint candidate-or-null architecture, which is a different policy.
- The T1 decision table becomes terminal only when applied to the trained T1 policy.
- If training is reached, its preregistration must add inactive same-type lookalikes to nonsealed training data; the current trace contains none.

No other high/critical defect appeared in the T0 evidence. The cross-type autopsy is real and valuable; the only blocker to G0 execution is fixing and refreezing the threshold machinery.
