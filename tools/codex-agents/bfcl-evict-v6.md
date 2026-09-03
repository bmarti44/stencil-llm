# Brief: bfcl-evict-v6 — close fable's harness-v4 review (F1-F10) under LEG A AMENDMENT 3

## Objective
Governing text: LEDGER-PLAN.md LEG A v7 + AMENDMENTS 1-3 (A3 appended just before this brief). Review to close:
results/harness-v4-review-fable.md (F1 CRITICAL nearest-width/nearest-turn matching instead of exact; F2 CRITICAL
token-exact echo clamp mirroring the column clamp, char text for untruncated entries; F3 HIGH full position-overflow
pass=None crash -> truncated fail semantics; F4 degenerate (verify v5 closed it); F5 harness hash (verify v5's manifest
hash closed it); F6 tool_swap echo order must match the treatment's ordering rule; F7 scorer truncation undercount
(count on pair length); F8 literal invariant fields / shared-plan facts duplicated across arms; F9 echo-only stratum
and outcome label reporting; F10 dev loader (verify v5 closed it)). The current code is v5 (commits ddd397a, 5a01ab3,
c7a3265; 68 tests). Implement each open item with a CPU test; re-run fable's dev census logic (a test with the real
dev slice, CPU, no model: match_impossible must NOT fire under nearest matching on the 11 evicting turns; echo delta
must be 0 or within the truncation allowance under the token-exact clamp using a stub scorer). Recompute the
registration hash over v7 + A1 + A2 + A3 text and refuse a preflight certificate computed over stale text.
`--split sealed` is NOT to be run. NEVER read data/bench/ifeval_input_data.jsonl. Never modify data/bench/* (the
offsets index is already sealed). GPU: BUSY — no model process; record deferred commands.

## Allowlist
See bfcl-evict-v6.allow.

## Tests first (TDD, rule 1)
RED first. Run ONLY tests/test_bfcl.py tests/test_bfcl_evict_v{2,3,4,5}.py tests/test_sealed_guard.py and your new
tests/test_bfcl_evict_v6.py. DO NOT run the full suite.

## GPU policy
No GPU. Never wait on a lock; never signal any process.

## Acceptance
CPU tests green; ruff clean; commit EARLY and often.

## Ledger handoff
Append to WORKLOG.md: each finding -> fix (file:line), the dev-census test results, the new registration hash,
deferred commands.
