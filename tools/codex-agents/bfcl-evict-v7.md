# Brief: bfcl-evict-v7 — close sol's harness-v6 review (BFCL-V6-1..6) under LEG A v7 + AMENDMENTS 1-3

## Objective
Governing text: LEDGER-PLAN.md LEG A v7 + AMENDMENTS 1-3. Review to close, using each finding's "Required fix" as the
spec: results/harness-v6-review-sol.md — V6-1 CRITICAL (nearest matching must match EVERY selected span before the
clamp and must never suppress a failed clamp; add the consumer-path regression tests sol lists); V6-2 CRITICAL (the
preflight certificate must record hashes of the BYTES ACTUALLY USED — cases, answers, offsets index, function docs,
checker, template — computed at load time from the same file handles, not expected values copied from the manifest;
mismatch refuses); V6-3 HIGH (Amendment-3 echo overflow within the truncation allowance is not a method failure in
sealed summaries); V6-4 HIGH (repeated-call normalization must be the execution normalization used by the checker —
share one function); V6-5 HIGH (the module manifest must cover the full runtime import chain — enumerate via
sys.modules after a dry import and hash every repo-local module reached); V6-6 MEDIUM (overflow boundaries reported
consistently at the three places sol names). If results/harness-v6-review-fable.md exists when you start, close its
findings too and note conflicts. Current code: v6 (9fe7c3f, c547811). Each fix with a CPU test; keep all prior tests
green. `--split sealed` is NOT to be run. NEVER read the sealed IFEval input file. Never modify data/bench/* except
that the offsets index may be REGENERATED ONLY if V6-2 requires a different format (record it). GPU: BUSY — no model
process; record deferred commands.

## Allowlist
See bfcl-evict-v7.allow.

## Tests first (TDD, rule 1)
RED first. Run ONLY tests/test_bfcl.py tests/test_bfcl_evict_v{2,3,4,5,6}.py tests/test_sealed_guard.py and your new
tests/test_bfcl_evict_v7.py. DO NOT run the full suite.

## GPU policy
No GPU. Never wait on a lock; never signal any process.

## Acceptance
CPU tests green; ruff clean; commit EARLY and often.

## Ledger handoff
Append to WORKLOG.md: each finding -> fix (file:line), the certificate's verified-bytes hash list, the module manifest
list, deferred commands.
