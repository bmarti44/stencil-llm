# Step 1: the sixteen development blocks, and whether the instrument bites

Astra's forward review (2026-09-13) recommends **scoped instruction compilation**
at a 28% artifact-success forecast — the first direction above Brian's 25% bar —
and makes step 1 a CPU-only construction gate:

> Build 16 development blocks with matched scope/restoration histories,
> executable alternatives, and the five shortcut policies. 2–4 CPU engineering
> hours; zero GPU. Decision purchased: does the instrument distinguish selective
> revision?
>
> Step 1 has a strict construction gate: gold and valid alternatives pass; every
> shortcut fails its designated contrasts; source metadata cannot reach the
> automatic arm. Failure here means repair the fixture before freezing it, not
> experiment on the model.

**Result: PASS.** No GPU was used and none is required to reproduce it.

    uv run python scripts/scoped_gate.py      # -> results/scoped/GATE.json
    uv run pytest -q tests/test_scoped_blocks.py

## What a block is

One entering repository and **two matched applicability cases** that require
**different executable behaviour from identical entering code**. A block succeeds
only if both cases succeed. The package is `core.py`, a `compat/` subpackage and
`compat/legacy.py` — real nested scopes, not a naming convention — and `core`,
`compat` and `compat.legacy` receive byte-identical entering bodies, so local
code precedent is matched across the two cases and cannot decide either.

The policy universe is **three-valued** (`raise` / `none` / `default`) and the
documented package baseline is `default`, deliberately *not* `raise`: that is
what lets "cancelling a replacement does not revive what it replaced" land on a
different value from the rule it superseded. In a two-valued universe accidental
toggling would look competent. Semantics: `results/scoped/SEMANTICS.md`.

## The sixteen blocks

| block | family | entering code | case A | case B | what it is for |
|---|---|---|---|---|---|
| S1 | scope | none | compat lookup = none | core lookup = raise | newest governs inside the namespace; a fresh operation outside follows the older rule |
| S2 | scope | raise | core lookup = raise | compat lookup = none | the broad rule arrives LAST and preserves the exception: specificity and recency disagree |
| S3 | scope | default | core bulk = raise | core lookup = none | scope by OPERATION: one file, two operations, two answers |
| S4 | scope | none | compat bulk = raise | compat lookup = none | path AND operation together |
| G1 | global | none | core lookup = raise | core bulk = default | a genuine global revision reaches the fresh lookup; the operation-scoped rule survives |
| G2 | global | raise | core bulk = raise | core lookup = none | G1 with the operation scopes swapped |
| G3 | global | raise | compat.legacy lookup = none | compat lookup = default | a broad revision that explicitly clears a narrower exception, then a NEW exception one level deeper |
| C1 | cancel | default | compat lookup = raise | core bulk = default | cancelling an exception exposes the still-live enclosing rule — not the baseline, and not the rule the exception itself replaced |
| C2 | cancel | raise | compat lookup = none | core lookup = raise | cancellation LANGUAGE aimed at an unrelated rule changes nothing |
| C3 | cancel | raise | compat lookup = raise | core lookup = default | QUOTED cancellation changes nothing; separately an obligation is released prospectively |
| C4 | cancel | raise | core lookup = default | compat bulk = none | cancelling a REPLACEMENT does not revive what it replaced: core falls to the baseline |
| R1 | restore | none | core lookup = raise | compat.legacy lookup = default | express reinstatement by reference, naming no value; the obligation added in between survives |
| R2 | restore | default | core lookup = default | compat lookup = none | restoring the global rule leaves the later narrower rule in force |
| R3 | restore | default | compat lookup = none | compat.legacy lookup = default | cancelling a policy never dropped its obligation; reinstating it does not disturb the deeper rule |
| D1 | distance | none | core lookup = raise | compat lookup = none | both rules predate four unrelated messages; the nearest missing-entry sentence is a docs decoy |
| D2 | distance | raise | core bulk = raise | core lookup = none | as D1, with a CLI decoy |

Cancellation appears in all four required forms: unrelated (C2), quoted (C3),
actual-exposing-a-live-default (C1), and actual-not-reviving (C4). Express
reinstatement (R1, R2, R3) refers to the earlier statement and never restates its
value — `test_reinstatement_restores_by_reference_without_restating_a_value`
asserts the message contains none of the three value words.

## The oracle

Four executable suites per case, independently written, never comparing against
the renderer or the history:

| suite | what it runs |
|---|---|
| functional | present keys come back, whatever the missing-entry policy is |
| contract | the missing-entry behaviour the history requires, **observed by running the function**, never read off its source |
| preservation | every entering function in all three modules still behaves as it entered, obligations included |
| obligation | the new function calls `note()` exactly when a live obligation says it must |

Two behaviourally identical alternative spellings per value (`try/except`,
membership test, `dict.get`) pass every case — 96 accepted implementations across
32 cases — so the oracle is behavioural, not textual. The two values that do not
apply are rejected in every case, so it is not vacuous either.

## The defeat matrix

| policy | | defeated |
|---|---|---|
| always_newest | required | 16/16 |
| always_oldest | required | 16/16 |
| flip_on_cancel | required | 16/16 |
| recency_general | required | 16/16 |
| copy_existing | required | 16/16 |
| rollback (whole-state revert) | extra | 16/16 |
| **scoped_recency** | rival | **4/16** — S2 G1 G2 D1 |
| **cancel_revives** | rival | **2/16** — C1 C4 |

**The uniform 16/16 rows are cheap evidence and are reported as such.** Every one
of those policies is scope-blind, and a block whose two cases need different
values refutes any scope-blind policy automatically. The informative rows are the
two **scope-aware rivals**, added because a gate that refuses everything would
satisfy Astra's second clause and be worthless:

- `scoped_recency` resolves scope correctly but lets the most RECENT applicable
  statement win instead of the most SPECIFIC. It passes 12 blocks and fails 4.
- `cancel_revives` resolves scope and specificity correctly but revives the
  superseded rule on cancellation — the heuristic UK drafting guidance rejects
  ("repealing a repeal does not revive the original enactment"). It passes 14
  blocks and fails 2.

`test_the_scope_aware_rivals_both_survive_and_fail` requires each rival to both
survive some blocks and fail some, which is the anti-vacuity evidence.

**Known limitation, stated before any model outcome:** only 4 blocks separate
specificity from recency and only 2 separate cancellation from revival. At
N=16 those two distinctions rest on thin margins, and a rescue result must not be
read as evidence about them. Widening that coverage belongs in the confirmation
material, not in a fixture repaired after seeing outcomes.

## Metadata isolation

`arm_payload(block, case)` returns exactly `{messages, repo, request}`; messages
are exactly `{role, text}`. No event kind, scope, value, reference, block id,
family or `defeats` field is reachable, and both cases of a block receive a
byte-identical repository. Asserted over all 32 cases.

## The economics contrast is built in

Every block renders in three history variants — `revised` (the authored history),
`direct` (each live rule stated once, informationally equivalent), and
`irrelevant` (direct plus interleaved unrelated messages) — holding the
repository and the requested edit fixed. The oracle's requirement is identical
across all three, asserted for all 32 cases. That is
Gonçalves–Libgober–Willis's retraction design made executable: it separates a
difficult *history* from a difficult *final coding task*.

The separation-logic contrast is the `preservation` suite plus the fresh
out-of-scope operations in S1/S2/G1/G2, since copied code cannot test
preservation.

## What this does and does not establish

It establishes that the instrument distinguishes selective revision from six
trivial policies and two scope-aware wrong semantics. **It says nothing about
whether the model can do any of it.** That is step 3, the oracle-reminder rescue
test: 64 short generations, 0.2–0.3 GPU-hours, thresholds prespecified in the
review (≥12/16 blocks and ≥6 wins with ≤1 loss → raise the direction from 28% to
~40%; ≤8/16 or ≤2 net rescued → drop to ~12% and stop).

**GPU work remains paused by Brian's standing instruction.** Nothing here needs
it; step 3 does, and waits.

## Lineage

Development material only. Nothing was fit or selected on any evaluation
benchmark; `data/bench/` was not read. The confirmation projects are separately
authored and frozen before any model outcome is inspected, per the review's
lineage rule. Two fixture repairs were made *before* any model contact and are
recorded here: the code precedent was counterbalanced (it now agrees with case A
in 6 blocks, case B in 5, neither in 5), and S2/D1/C1 were rephrased so the two
scope-aware rivals have something to fail.
