# Scoped instruction semantics (frozen 2026-09-13, before any model outcome)

Astra's forward review requires the intended semantics to be *defined*, not
assumed, because "cancel B therefore A" is exactly the universal binary
heuristic that UK drafting guidance says is wrong (repealing a repeal does not
revive the original enactment) and that `git revert` avoids by recording a
reversal instead of deleting ancestry.

This file is the specification the executable oracle implements.  It is
repository documentation, not a label: the automatic arm may read the package's
own docstring baseline, and nothing else here.

## The policy universe is three-valued

A *missing-entry policy* is one of:

| value | lookup behaviour | bulk behaviour |
|---|---|---|
| `raise` | raise `MissingEntry(key)` | raise `MissingEntry(key)` on the first missing key |
| `none` | return `None` | put `None` in the result for each missing key |
| `default` | return `DEFAULT` | put `DEFAULT` in the result for each missing key |

Three values, deliberately: in a binary universe accidental toggling is right
half the time, so a flip-on-cancellation shortcut would look competent.

## The documented package baseline is `default`

Every project's `__init__.py` docstring states: *"Unless an instruction says
otherwise, a missing entry yields DEFAULT."*  The baseline is `default` and NOT
`raise`, so that cancelling a policy which replaced `raise` cannot be confused
with reviving `raise`: non-revival and revival land on different values.

## Instruction events

An authoritative message may carry at most one event.

- **set(scope, value)** / **replace(scope, value)** — the scope's live policy
  becomes `value`.  `replace` is `set` on a scope that already has one; the
  superseded statement stays in the history and remains referenceable.
- **cancel(scope)** — the scope's live policy is removed.  Resolution then falls
  to the nearest enclosing live scope, and to the documented baseline if there
  is none.  **Cancelling a policy does not revive the policy it replaced.**
- **reinstate(ref)** — an express instruction that the policy established by an
  earlier identified statement applies again.  It refers to that statement
  ("the rule we had for compat before the change") and does **not** restate its
  value.  Reinstatement is the only way a superseded **statement** returns to
  force.  It is NOT the only way an earlier **value** recurs: a new `set` may
  state the same value again, and a cancellation may expose an enclosing live
  rule that happens to carry it.  Statement and value are different things and
  the fixture keeps them apart.
- **obligate(name, scope)** / **release(name, scope)** — an obligation
  independent of the policy stack (e.g. "every public function calls note()").
  Obligations and policies have independent support: cancelling a policy never
  drops an obligation, and cancelling an obligation never changes a policy.
- **noise** — an authoritative message that carries no event.

A `set`, `replace` or `cancel` message may additionally **clear** named narrower
scopes when it says so ("for the whole package, compat included").  Clearing
removes the live policy at each scope it names **exactly**; it does not reach
that scope's descendants, which is why a rule established afterwards one level
deeper still stands.

## Applicability

A policy applies to a request if its path scope matches and its operation scope
matches.

- path scope `*` matches everything; scope `s` matches path `s` and any `s.x`.
- operation scope `None` matches every operation; `lookup` / `bulk` match that
  operation only.
- Specificity is `(path depth, 1 if the operation is named else 0)`, ordered
  lexicographically.  The most specific live policy wins.  **Path depth
  outranking operation specificity is a stipulation**, not a general truth about
  instructions; it is internally consistent for these hierarchical scopes, and
  it is stated in the public prompt so no arm has to guess it.

**Ties are structurally impossible, not a semantic question.** For any request
the matching scopes form a chain of distinct depths, and the operation flag
separates the two keys of one scope, so no two live policies can share a
specificity.  `tests/test_scoped_blocks.py` proves this by enumeration; the
resolver's ambiguity flag stays as a defensive assertion and the gate refuses any
case that trips it.

## Prospective by default

An instruction governs work done after it.  Existing code is not retroactively
rewritten unless the instruction says so, so *preservation* is "the entering
repository still behaves as it entered", measured by running it.

## What this is not

These are coherent stipulations, not the only defensible reading of how
instructions change in conversation.  A developer may well intend "cancel that
change" as an undo that restores what came before.  Because the protocol is a
choice, it is stated **publicly in the prompt both conditions receive** — the
conventions block naming prospectivity, specificity, non-reviving cancellation
and express reinstatement.  It is task specification, not a gold label.

Known limit of the present fixture: no development block has two independent
supports for one obligation, so the blocks test that an obligation survives a
POLICY change, not that it survives the withdrawal of one of several supports.
The resolver handles the multi-support case and is unit-tested; the blocks do
not exercise it.

## What this forbids

A whole-state rollback to the moment of a reinstated policy is wrong: an
unrelated obligation introduced in between has independent support and must
survive.  That is the `git revert` lesson and the separation-logic frame rule,
and the oracle tests it directly.
