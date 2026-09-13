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

**Result: PASS — after repair.** Astra's implementation review
(`results/reviews/2026-09-13-scoped-instrument-astra.md`, VERDICT REPAIR)
rejected the first PASS with six high findings, reproducing two wrong resolvers
that passed 16/16 and three materially wrong implementations that passed all four
suites. Every one is repaired below and locked in by a regression test. No GPU
was used and none is required to reproduce it.

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
| R1 | restore | none | core lookup = raise | compat.legacy lookup = default | reinstatement refers to the SECOND statement at its scope, so "restore the first rule ever stated here" is wrong; the obligation added in between survives |
| R2 | restore | default | core lookup = default | compat lookup = none | restoring the global rule leaves the later narrower rule in force |
| R3 | restore | default | compat lookup = none + log | core lookup = raise, NO log | the obligation is scoped to `compat/`, so a fresh function in `core.py` must not log; cancelling the policy never dropped the obligation |
| D1 | distance | none | core lookup = raise | compat lookup = none | both rules predate four unrelated messages; the nearest missing-entry sentence is a docs decoy |
| D2 | distance | raise | core bulk = raise | core lookup = none | as D1, with a CLI decoy |

Cancellation appears in all four required forms: unrelated (C2), quoted (C3),
actual-exposing-a-live-default (C1), and actual-not-reviving (C4). Express
reinstatement (R1, R2, R3) refers to the earlier statement and never restates its
value — `test_reinstatement_restores_by_reference_without_restating_a_value`
asserts the message contains none of the three value words.

## The oracle

Four executable suites per case. Its requirement is each case's **hand-frozen
`expect_value` / `expect_note`**, authored from the block's public message
wording — *not* anything the resolver computes.

That is a correction, not a detail. The first version had `gold_candidate()` and
`evaluate()` both call `resolve()`, so agreement between them validated nothing:
a wrong resolver was simply believed twice. The earlier claim that the oracle
"never consults the history" was **false** and is withdrawn. The gate now asserts
that `resolve()` reproduces the authored expectations, which is a real check in
the direction that matters.

| suite | what it runs |
|---|---|
| functional | present keys come back — both keys for a lookup; for a bulk gather, a two-key batch *and* an empty batch, as a list in the requested order |
| contract | the required missing-entry behaviour, **observed by running the function**. A bulk gather is probed with a MIXED batch and must preserve the present entries, their order and the result length. A raise counts only if it names the key that was missing |
| preservation | every entering function in all three modules still returns its present entries correctly, still classifies missing entries as it did on entry, and still logs exactly as it did |
| obligation | the new function logs, **before it touches the table**, on a successful lookup *and* on a missing one — or never logs, when no obligation applies |

Three of those strengthenings exist because Astra produced implementations that
passed the weaker versions:

- a bulk gather returning `[None]` for a three-key batch — losing two present
  entries — was classified `none` and passed, because `observe()` read only the
  first element of the result;
- a function that rebound an existing one to a broken lambda passed
  preservation, because preservation compared only missing-entry classifications
  and never present-key behaviour;
- a function that logged *after* reading the table, and not at all on a failed
  lookup, passed the obligation suite, because it checked only membership in
  `CALLS` on a present-key call.

"Calls `note()` as its **first statement**" is syntactic and a behavioural oracle
cannot see syntax. The observable requirement is therefore *logs before it
touches the table, on both paths*, checked with an instrumented mapping that
records accesses on the same timeline as the log.

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
| **reinstate_first** | rival | **1/16** — R1 |
| **obligation_global** | rival | **1/16** — R3 |

**The uniform 16/16 rows are cheap evidence and are reported as such.** Every one
of those policies is scope-blind, and a block whose two cases need different
values refutes any scope-blind policy automatically. The informative rows are the
four **scope-aware rivals**, each wrong in one specific way:

- `scoped_recency` — correct scoping, but the most RECENT applicable statement
  wins instead of the most SPECIFIC.
- `cancel_revives` — correct scoping and specificity, but cancellation revives
  the superseded rule, the heuristic UK drafting guidance rejects.
- `reinstate_first` — correct in every respect except that reinstatement
  restores the FIRST policy ever stated at that scope, ignoring which statement
  was referenced.
- `obligation_global` — correct policies, but every logging obligation is
  treated as package-wide, ignoring its scope.

The last two exist because Astra reproduced them **passing 16/16** on the first
version of the fixture: every reinstatement happened to reference the first
policy at its scope, and the only scoped obligation had both of its cases inside
its own scope. Both blocks were repaired to Astra's specification — R1 now has an
earlier DEFAULT policy at the same scope and reinstates the *second* statement;
R3's obligation is scoped to `compat/` in its own wording and its cases now
straddle that boundary.

**One earlier gate rule was wrong and has been removed.** The first version
required each rival to *survive* somewhere, on the theory that a rival failing
everywhere would prove the oracle merely refuses everything. Astra: a correct
fixture may legitimately defeat a wrong policy everywhere, and the positive
control is the independently spelled valid implementations — not the survival of
a wrong one.

**Known limitation, stated before any model outcome:** the four rivals are
separated by 4, 2, 1 and 1 blocks. At N=16 those distinctions rest on thin
margins, and a rescue result must not be read as evidence about any of them.
Widening that coverage belongs in the confirmation material, not in a fixture
repaired after seeing outcomes.

## Metadata isolation

`arm_payload(block, case)` returns exactly `{messages, repo, request}`; messages
are exactly `{role, text}`. No event kind, scope, value, reference, block id,
family or `defeats` field is reachable.

**But `arm_payload` is not what the runner sends.** Astra's point: those checks
validated a serializer the generation path does not consume. The isolation
assertions now also run on **the actual prompt strings** the runner builds, in
both conditions, for all 32 cases — no block id, no `applicable`, no `defeats`,
and the `off` prompt never contains the reminder header.

What the prompt *does* carry, deliberately and identically in both conditions, is
the task specification the hidden oracle enforces: the package `__init__.py` with
its documented default, and a short conventions block stating that instructions
are prospective, that the more specific rule wins, that cancelling does not
revive what was replaced, and that an instruction can expressly put an earlier
one back in force.

That was a real defect, not a nicety. Before it, **C4's `core` case asked the
model to "fall back to what the package documents" while withholding the
documentation**, and the visible entering code implemented `raise` — pointing at
the wrong answer. C4 was unanswerable in both conditions.

## The economics contrast, and how much of it is really there

Every block renders in three history variants — `revised` (the authored history),
`direct` (each live rule stated once, informationally equivalent), and
`irrelevant` (direct plus interleaved unrelated messages) — holding the
repository and the requested edit fixed. The oracle's requirement is identical
across all three, asserted for all 32 cases, and `direct` never restates a
superseded value.

**The honest accounting:** `direct` is strictly shorter than `revised` in 12/16
blocks, but only **7/16 blocks contain a superseded statement at all** (G1, G2,
G3, C1, C4, R1, R2). For the other nine, `direct` differs from `revised` only by
dropping noise — which is the *irrelevant-history* condition, not the
*retraction* condition. So the Gonçalves–Libgober–Willis contrast is available on
7 blocks and the irrelevant-history contrast on 16.

**And the registered runner uses `revised` only.** The variants exist and are
tested; the rescue diagnostic does not estimate the economics contrast. Saying it
"implements" that contrast would be wrong, and the earlier wording came close.

The separation-logic contrast is the `preservation` suite plus the fresh
out-of-scope operations in S1/S2/G1/G2, since copied code cannot test
preservation.

## What these blocks are not

Registered before any result exists, because each of these will otherwise be
embarrassing in the write-up:

- They are **independent single-function additions with fresh entering
  repositories**, not continuing coding sessions. There is no accumulated edit
  state, no tool-feedback loop, no context turnover and no automatic extraction.
- The edit interface is **append-only**, so existing source is preserved
  structurally; preservation can still fail through runtime side effects, but
  this is a far narrower maintenance task than general code editing.
- All 16 blocks share **one rate-table package** and a small implementation
  vocabulary. They are 16 authored contrasts, **not 16 independent repository
  samples**, and nothing here supports a generalisation beyond this workload.
- The scorer runs model output in a separate process. That buys **crash
  separation and a timeout — not a filesystem or information sandbox.** An
  earlier claim that model output goes through "the repository's existing
  sandboxed path" was inaccurate and is withdrawn.
- No block has two independent supports for one obligation, so the fixture tests
  that an obligation survives a POLICY change, not that it survives the
  withdrawal of one of several supports.

## Lineage

Development material only. Nothing was fit or selected on any evaluation
benchmark; `data/bench/` was not read. The confirmation projects are separately
authored and frozen before any model outcome is inspected, per the review's
lineage rule. Fixture repairs made *before* any model contact, all recorded here: the code
precedent was counterbalanced (it agrees with case A in 6 blocks, case B in 4,
neither in 6); S2/D1/C1 were rephrased so the scope-aware rivals have something
to fail; and after Astra's implementation review, R1 and R3 were rebuilt, the
four oracle suites were strengthened, per-case expectations were frozen by hand,
and the public wording was corrected to name the files the requests actually
name.
