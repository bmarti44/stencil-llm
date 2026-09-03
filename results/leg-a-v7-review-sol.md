# Final confirmation: LEG A registration v7 — sol, 2026-09-03

Reviewed the current registered section plus its in-place Amendment 1 at
`LEDGER-PLAN.md` sha256
`8c3a60445eb9f3a6b1da0e28a26b4c12498cd3817e4e6fb0193515cf7929d74c` against
every exact fix in `results/leg-a-v5-review-{sol,fable}.md`. CPU-only text
review; no GPU/model process was launched, no process was waited on or
signalled, and neither sealed input was read. This is the only repo output.

The Amendment 1 changes now present cure the model-card omission, the pasted
preflight-(6) lead-in, and the stale safety pointer. Two residuals remain.

1. The global `match_impossible` definition is still incompatible with
   decision (i). A same-role `clf_control` shortage both invokes the registered
   other-role fill and satisfies “the disjoint pool of the required role has
   fewer columns than the quota,” which makes A1 uninformative. The same global
   wording also makes `recency_pinned` use a disjoint pool although its arm is
   registered to select from the same user/tool universe. The immediately
   preceding clamp sentence is independently two-readable about whether the
   already-admitted last span or the next, over-quota span is truncated.

   Replace the first two sentences of the `Column clamp for every comparator`
   paragraph, through “not a turn drop,” with exactly:

   > Column clamp for every comparator: matched spans are admitted whole in
   > match order while they fit. If the next span would exceed the treatment's
   > quota, that next span is admitted only through the Qwen3-token boundary
   > that makes the pinned-column count exact, and its echo entry is that same
   > truncated text. `match_impossible` is arm-specific: for `clf_control`, it
   > means the combined disjoint nonselected pool permitted by decision (i)
   > cannot supply the treatment's exact total pinned-column quota under the
   > registered width/age matching rule; a same-role shortage alone is
   > `control_role_shortfall`, not `match_impossible`. For `recency_pinned`, it
   > means the eligible same-role universe cannot supply the treatment's
   > per-role quota; overlap with treatment-selected spans is permitted because
   > recency selection itself determines membership. For `tool_swap_echo`, it
   > means that a selected TOOL chunk has no disjoint TOOL replacement under
   > the registered width/age match. It is recorded per turn and makes the
   > affected contrast uninformative as a whole, not a turn drop.

   In the `clf_control` arm, replace:

   > If no disjoint width/age match exists in either role, A1 is uninformative.

   with exactly:

   > If the combined same-role and decision-(i) other-role pools cannot supply
   > the exact total pinned-column quota under the registered width/age matching
   > rule, A1 is uninformative.

2. The exact fixes introduce three routes by which A1 can be uninformative
   (`match_impossible`, sealed comparator-delta failure, and comparator safety),
   but the outcome table handles only A1 pass/fail when A3 is uninformative.
   It therefore does not determine whether an A1-uninformative leg is
   INCONCLUSIVE or unsupported, and it also omits the eligible-A3 cases in
   which exactly one of A1/A3 passes.

   Append to the first three A1/A3 outcome sentences, immediately before the
   A2 rule, exactly:

   > If A1 is uninformative for any registered reason, the primary benefit
   > claim is INCONCLUSIVE and cannot be reported as supported; every other
   > eligible contrast and secondary metric is still reported. If A3 is
   > eligible and either A1 or A3 does not pass, the primary benefit claim is
   > unsupported.

These are text-only closures and do not reopen decisions (i)-(vii).

## VERDICT

**CONFIRMED-WITH-FIXES.**
