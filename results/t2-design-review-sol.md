codex
# Verdict: NOT CLEARED

T2 has the right outline, but the contract remains gameable in four central places: opportunity denominators, per-arm compaction, held-out abstention, and cost arithmetic. The T1 result is a genuine closed-distribution causal result, but its 1.000 metrics do not show that the detector reads active obligations rather than recognizing Python syntax.

No critical findings. Six high-severity findings block the build.

## Findings

### HIGH — Governance opportunities are not defined precisely enough

[TIMED-SELECTOR-PLAN.md:78](/home/bmarti44/stencil-llm/TIMED-SELECTOR-PLAN.md:78) says the generator emits applicable obligations, but does not define the scoring unit.

It must specify whether an opportunity is:

- one `(work turn, obligation)` pair,
- one application per target function,
- one application per argument,
- or one token-level decision moment.

Those produce different denominators. Type hints are the clearest problem: a two-argument function could count as one obligation or two annotation opportunities.

Register an immutable opportunity record before generation:

```json
{
  "session": 123,
  "turn": 17,
  "opportunity_id": "17:target_fn:arg_b:hint",
  "obligation_id": "hint-v3",
  "target": "target_fn.arg_b",
  "expected": "float",
  "superseded": ["int"],
  "scorer": "ast_argument_annotation"
}
```

Required denominator rules:

- Every emitted opportunity appears exactly once.
- Omitted functions, arguments, docstrings, comments, or actions score zero.
- Invalid code scores zero for every code opportunity on that turn.
- Detector silence cannot remove an opportunity.
- Cleared obligations are absent from active-adherence denominators but remain eligible for stale-action scoring.
- Macro = mean of each session’s opportunity adherence.
- Micro = all opportunities pooled.
- Both must pass, or one must be named primary now.
- Stale rate denominator must be opportunities having a distinct superseded value—not wrong answers or detector activations.
- “Process rule” needs a concrete pool, decision moment, and deterministic scorer; AST/exec alone cannot score an unspecified workflow rule.

Also distinguish:

1. **Governance opportunity:** generator-defined, exists even if the model omits the relevant construct.
2. **Detector moment:** token-level opportunity created by the generated syntax.
3. **Opportunity coverage:** fraction of governance opportunities for which a usable detector moment occurred.

That prevents perfect detector recall from coexisting with omitted governed constructs.

### HIGH — “What survives is arm policy” is not a registration

The compaction clause at [TIMED-SELECTOR-PLAN.md:74](/home/bmarti44/stencil-llm/TIMED-SELECTOR-PLAN.md:74) leaves the most outcome-determining choice open.

Register, for every arm:

- exact `K`
- exact compaction turns per 20/40/60-turn stratum
- transcript truncation algorithm
- canonical ledger serialization
- whether the ledger is reinserted at compaction
- ledger placement
- whether old/superseded entries remain
- whether any address/state survives
- how all carried tokens are charged

At minimum, `base`, `zero-selector`, `selector`, and `oracle` must receive byte/token-identical context and the same canonical current ledger. Their only difference may be the attention intervention. Otherwise a selector win can really be “selector arm retained more memory.”

A reasonable policy is:

- Base/zero/selector/oracle: last `K` turns plus one identical canonical active ledger at compaction.
- Pinned: canonical ledger maintained in the pinned prefix and updated deterministically.
- Reinsert: full canonical ledger inserted immediately before every work request.
- No arm may retain hidden text or values in selector state.

Repository state also needs a reset rule per session/arm, deterministic patch application, and deterministic arm-specific checker feedback. “Templated feedback” must say whether it reflects that arm’s actual checker result or replays a common script.

### HIGH — Held-out abstention is currently gameable

The held-out comment obligation at [TIMED-SELECTOR-PLAN.md:90](/home/bmarti44/stencil-llm/TIMED-SELECTOR-PLAN.md:90) is a useful OOD safety check, but not a generalization test.

Two problems:

1. “Abstain scores as base behavior” could mean imputing the paired base score. That is invalid. Generate the selector arm normally and score its actual output. Because earlier selector presses can change its prefix, abstention does not guarantee the same result as base.
2. The detector has no class for the unseen obligation. Safely doing nothing proves open-set conservatism, not generalization.

Rename this an **OOD-abstention safety test** unless positive transfer is required. Report separately:

- actual adherence on held-out opportunities
- false-press rate
- abstention rate
- base adherence
- selector-minus-base effect

One held-out type is insufficient for a “held-out generality” claim, especially because the registered instruments require held-out types plural at [TIMED-SELECTOR-PLAN.md:21](/home/bmarti44/stencil-llm/TIMED-SELECTOR-PLAN.md:21). Use at least two substantially different types or a leave-one-type-out rotation.

More importantly, add counterfactual pairs for trained types:

- same syntax, relevant obligation active
- same syntax, obligation absent
- same syntax, obligation cleared
- same syntax, only a stale same-type obligation present
- same obligation paraphrased and relocated

A detector that fires after every `def`, triple quote, or annotation colon regardless of ledger contents must fail these tests.

### HIGH — The cost-adjusted gate can pass while the system is useless

The gate at [TIMED-SELECTOR-PLAN.md:102](/home/bmarti44/stencil-llm/TIMED-SELECTOR-PLAN.md:102) has several loopholes:

- “or beats it outright” permits unbounded extra cost for an arbitrarily small accuracy win.
- Selector and reinsertion can both perform poorly while remaining within two points.
- Base→oracle closure is unstable or vacuous when the oracle gap is tiny.
- Only parse loss is gated; semantic execution/task success can degrade.
- Stale rate can fall because the selector emits invalid code.
- “Cumulative prompt tokens” is undefined under retained context, KV reuse, compaction, and repeated full-forward decoding.

Use prerequisites and a Pareto gate:

```text
oracle_headroom = A_oracle - A_base >= 0.10  # or another frozen minimum
closure = (A_selector - A_base) / oracle_headroom >= 0.50

cost_pass =
    (A_selector >= A_reinsert - 0.02
     and C_selector <= 0.50 * C_reinsert)
    OR
    (A_selector >= A_reinsert + 0.02
     and C_selector <= C_reinsert)
```

Never permit `C_selector > C_reinsert` to pass the cost gate.

Also require:

- paired parse losses = 0
- paired semantic execution/task-success losses = 0, or an explicit frozen tolerance
- selector adherence above base by a fixed positive amount
- stale reduction only when base has registered stale headroom
- invalid outputs remain in the stale denominator
- both primary macro and micro adherence gates

Define costs separately:

- logical input tokens
- completion tokens
- tokens reprocessed after compaction
- measured wall-clock latency
- selector state bytes
- actual model-forward compute under the chosen KV/no-KV runtime

The exact API/runtime assumption must be frozen.

### HIGH — T2 omits the learned-controller gates needed to diagnose failure

The selector is retrained and recalibrated at [TIMED-SELECTOR-PLAN.md:83](/home/bmarti44/stencil-llm/TIMED-SELECTOR-PLAN.md:83), but the contract does not specify:

- classes
- architecture
- training examples
- rollout sources
- optimizer/steps
- negative-position sampling
- moment-label generator
- activation duration
- hard-address rule
- T2 precision/recall/address gates

Register the inherited architecture and every deliberate change. T2 must report on its own rollouts:

- moment precision and recall
- false activation rate
- address accuracy at true moments
- active-vs-absent counterfactual sensitivity
- learned/oracle and oracle/learned behavioral arms

Without the factorial arms, a miss cannot distinguish timing, addressing, actuator, or benchmark failure. The T2 arms should include at least:

- off/off
- oracle/oracle
- learned/oracle
- oracle/learned
- learned/learned
- parser/oracle
- wrong-span
- rate-matched random timing

Always-on can be restricted to a diagnostic subset because its failure is already established.

The stop rule at [TIMED-SELECTOR-PLAN.md:111](/home/bmarti44/stencil-llm/TIMED-SELECTOR-PLAN.md:111) is also too open. “One registered tau/dose recalibration” does not name the fallback. Either:

- calibrate τ once on calibration data, inherit β=2, freeze both, and stop on a validation miss; or
- specify the exact fallback, trigger, fresh evaluation block, and selection rule now.

No parameter may be changed after inspecting validation under the generic word “recalibration.”

### HIGH — The generator and checker are not frozen enough for a registered run

The ranges at [TIMED-SELECTOR-PLAN.md:66](/home/bmarti44/stencil-llm/TIMED-SELECTOR-PLAN.md:66) are a design sketch, not a deterministic benchmark specification.

Missing:

- number of sessions per split and stratum
- exact turn schedule/generator algorithm
- exact update, clear, reversal, and compaction distributions
- exact obligation/type/template pools
- exact process rules
- decoding settings and generation limits
- repository transition and reset semantics
- environment feedback function
- source-authority/provenance policy
- fixture, generator, checker, tokenizer, and model hashes

Because the fixture does not exist yet, use a two-step freeze:

1. Build the fixture/generator/checker without model evaluation.
2. Freeze hashes, deterministic sample fixtures, expected opportunity ledgers, and checker tests; perform a final pre-run audit.

The current contract must explicitly require that second checkpoint. Otherwise implementation choices can tune the task without technically changing the plan.

## T1 ceiling: real but narrower than it looks

T1 is not behaviorally vacuous. Learned/learned matching oracle on fresh behavioral sessions, together with T0’s wrong-span and random-timing controls, demonstrates a real closed-distribution intervention.

But the 1.000 timing result can be achieved by syntax distillation:

- AST labels are function-name, docstring, and annotation positions in [timed_t1.py:111](/home/bmarti44/stencil-llm/scripts/timed_t1.py:111).
- Every training session contains all three obligation types.
- Therefore `def`, `"""`, and `:` are sufficient labels even if the timing head ignores the ledger.
- Randomized sentence order defeats fixed position memorization but not sentence-template classification.

The proposed single held-out comment type with allowed abstention does not catch this.

There are also two record caveats:

- Despite the plan saying base and oracle rollouts, `collect()` gathers only unmodified base rollouts at [timed_t1.py:157](/home/bmarti44/stencil-llm/scripts/timed_t1.py:157).
- The reported 1.000 precision/recall and address accuracy are calibration metrics at [timed_t1.py:207](/home/bmarti44/stencil-llm/scripts/timed_t1.py:207); validation records measure behavioral output but do not recompute detector PR/address accuracy.

These do not erase the 1.00 behavioral closure. They mean T2 must not present T1’s 1.000 as independent generalization evidence.

## Deferred summary baseline

**Severity: MEDIUM — acceptable with a hard limitation**

Deferring the compaction-summary baseline at [TIMED-SELECTOR-PLAN.md:86](/home/bmarti44/stencil-llm/TIMED-SELECTOR-PLAN.md:86) is acceptable for T2 as a mechanism and benchmark-admission phase.

It is not acceptable for:

- a usefulness/Pareto conclusion,
- claiming the selector beats ordinary agent memory management,
- proceeding directly to 7B,
- or closing the registered comparison.

State explicitly that the G4-equivalent comparison cannot pass without a frozen summary policy and baseline. T2’s token comparison is preliminary.

## Required changes

### MUST

1. Define immutable opportunity records and all macro/micro/stale denominators.
2. Define exact context and compaction policy for every arm; base/zero/selector/oracle must be content-identical.
3. Replace held-out score imputation with actual generated outcomes.
4. Rename the one-type test OOD abstention, or add enough held-out types for a generality claim.
5. Add active/absent/cleared/stale counterfactual tests for trained obligation types.
6. Repair the cost gate with an oracle-headroom prerequisite, absolute usefulness protection, and bounded-cost “beats outright” branch.
7. Gate semantic execution/task success, not parse alone.
8. Register T2 timing/address metrics and factorial diagnostic arms.
9. Freeze selector training, calibration, activation duration, β/τ, and any fallback.
10. Define provenance and require unauthorized writes = 0.
11. Freeze session counts, generator distributions, runtime, decoding, checker, and evidence schema.
12. Require a post-build, pre-run hash/fixture audit.
13. Expand evidence records to include raw output, true opportunities, true/predicted moments, predicted addresses, exact spotlight rows/spans, compaction events, config hashes, and paired-arm identity.

### SHOULD

- Include at least two held-out obligation types or leave-one-type-out evaluation.
- Add parser-timed and always-on diagnostic subsets.
- Report actual latency and state bytes alongside logical token cost.
- Record the T1 base-only-training and calibration-metric caveats in WORKLOG.
- Preserve summary-baseline deferral only with an explicit “no usefulness or 7B gate before G4-equivalent” clause.

The important design correction is simple: T2 must test whether the controller conditions on the **active ledger**, not merely whether it recognizes Python syntax. As written, it does not yet force that distinction.
