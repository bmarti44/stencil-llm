# Brief: bfcl-evict-v8 — close fable's harness-v6 review (FV6-1..6) on top of v7 (sol's V6 closure)

## Objective
Governing text: LEDGER-PLAN.md LEG A v7 + AMENDMENTS 1-3. Review to close: results/harness-v6-review-fable.md.
FV6-1 CRITICAL is the same defect as sol's BFCL-V6-1 (nearest matching terminating on the aggregate column total and
discarding the clamp's match_impossible) — verify the v7 closure covers it with fable's exact regression: per-role
column equality asserted on EVERY evicting turn in BOTH the dev invariants AND the sealed path (fail-closed, never
fail-open), and a census test whose stub scorer selects user sentences on every evicting turn (not 2/11).
FV6-2 HIGH: a `full` INITIAL-PROMPT overflow (> 40,960 positions before generation) is registered NA — full does not
generate, per-turn pass NA, excluded from A3 and from full's safety baseline (it must NOT count as a truncated event for
full); only WITHIN-TURN overflow is the truncated-fail case (Amendment 3). 6/11 dev evicting turns exceed 40,960 on the
initial prompt, so this changes the safety baseline. FV6-3 MEDIUM: the echo clamp must also PAD-TO-MATCH when the
comparator echo undershoots (other-role fallback framing tokens) — extend the last entry from its source text up to
the treatment's token count, never beyond; assert |delta| <= 16 after clamping. FV6-4: sealed-path comparator
assertion (same as dev invariants, fail-closed). FV6-5: preflight report includes match_impossible / shortfall /
delta counts. FV6-6: remove the dead `seed` and complete manifest/git provenance fields. Current code: v7 (after the
bfcl-evict-v7 coder). Each fix with a CPU test; all prior tests green. `--split sealed` is NOT to be run. NEVER read
the sealed IFEval input file. Never modify data/bench/*. GPU: BUSY — no model process; record deferred commands.

## Allowlist
See bfcl-evict-v8.allow.

## Tests first (TDD, rule 1)
RED first. Run ONLY tests/test_bfcl.py tests/test_bfcl_evict_v{2,3,4,5,6,7}.py tests/test_sealed_guard.py and your
new tests/test_bfcl_evict_v8.py. DO NOT run the full suite.

## GPU policy
No GPU. Never wait on a lock; never signal any process.

## Acceptance
CPU tests green; ruff clean; commit EARLY and often.

## Ledger handoff
Append to WORKLOG.md: each finding -> fix (file:line), the census test's per-turn per-role equality results,
deferred commands.
