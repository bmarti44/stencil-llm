# Brief: bfcl-evict-v10 — close sol's harness-v9 review (BFCL-V9-1 CRITICAL, V9-2 HIGH) and fable's harness-v8 review if present

## Objective
Governing text: LEDGER-PLAN.md LEG A v7 + AMENDMENTS 1-5. Reviews: results/harness-v9-review-sol.md (V9-1 CRITICAL:
the emitted preflight certificate must be tied to the exact bytes and run identity that produced the PASSING
preflight — bind the preflight run's own meta digest, its verified-bytes hashes, its records' digests, the trunk
choice and arm set, and the gate results into the certificate, sign it with a digest over that payload, and make the
sealed run refuse a certificate whose payload does not match a preflight.json that exists with those exact digests
and gates = passed; test: a certificate from a failed or altered preflight is rejected; V9-2 HIGH: a comparator
safety breach must make the contrasts that use it uninformative BEFORE the primary_claim_status table is evaluated,
so SUPPORTED_A1_ONLY cannot be reached through a breached clf_control; complete the table test with breach cases)
and results/harness-v8-review-fable.md (apply every finding if the file exists; note conflicts, resolve toward the
registered text). Current code: v9 (fb17fc9, 8049e8f). Each fix with a CPU test; all prior tests green.
`--split sealed` is NOT to be run. NEVER read the sealed IFEval input file. Never modify data/bench/*. GPU: BUSY —
no model process; record deferred commands.

## Allowlist
See bfcl-evict-v10.allow.

## Tests first (TDD, rule 1)
RED first. Run ONLY tests/test_bfcl.py tests/test_bfcl_evict_v{2,3,4,5,6,7,8,9}.py tests/test_sealed_guard.py and
your new tests/test_bfcl_evict_v10.py. DO NOT run the full suite.

## GPU policy
No GPU. Never wait on a lock; never signal any process.

## Acceptance
CPU tests green; ruff clean; commit EARLY and often.

## Ledger handoff
Append to WORKLOG.md: each finding -> fix (file:line), the certificate payload/signature, the completed decision-table
cases, deferred commands.
