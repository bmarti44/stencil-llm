# Brief: bfcl-evict-v9 — close sol's harness-v8 review (BFCL-V8-1..3) under LEG A v7 + AMENDMENTS 1-5

## Objective
Governing text: LEDGER-PLAN.md LEG A v7 + AMENDMENTS 1-5 (A5, appended just before this brief, resolves the A4 vs
decision-(i) conflict: clf_control on control_role_shortfall turns matches the exact TOTAL with per-role deltas
recorded; every other comparator and every non-shortfall clf_control turn matches exact PER-ROLE columns; both
asserted fail-closed on dev AND sealed paths). Review to close, each finding's "Required fix" as the spec:
results/harness-v8-review-sol.md — V8-1 CRITICAL: (a) `run --split sealed` must validate the preflight certificate
BEFORE any sealed byte is read (move validate_preflight_certificate ahead of the loader; a test proves no sealed read
happens on a rejected certificate); (b) the certificate payload must be SPLIT-INVARIANT: it binds the frozen
constants, the harness/module manifest hashes, the selector/trunk/tokenizer/template/checker hashes and the DEV
cohort's verified bytes; the sealed run separately verifies its own cohort bytes against the sealed offsets index and
records them; a genuine dev certificate must validate for the sealed run (test it). V8-2 CRITICAL: implement A5
exactly (remove the exact-total acceptance everywhere EXCEPT the recorded clf_control shortfall case; all three
places sol names). V8-3 HIGH: the preflight competence baseline must exclude full's initial-prompt NA cases from
its denominators as registered (report them). If results/harness-v8-review-fable.md exists at start, close its
findings too. Current code: v8 (2621509, a145340). Each fix with a CPU test; all prior tests green.
`--split sealed` is NOT to be run. NEVER read the sealed IFEval input file. Never modify data/bench/*. GPU: BUSY —
no model process; record deferred commands.

## Allowlist
See bfcl-evict-v9.allow.

## Tests first (TDD, rule 1)
RED first. Run ONLY tests/test_bfcl.py tests/test_bfcl_evict_v{2,3,4,5,6,7,8}.py tests/test_sealed_guard.py and your
new tests/test_bfcl_evict_v9.py. DO NOT run the full suite.

## GPU policy
No GPU. Never wait on a lock; never signal any process.

## Acceptance
CPU tests green; ruff clean; commit EARLY and often.

## Ledger handoff
Append to WORKLOG.md: each finding -> fix (file:line), the certificate payload fields, the no-sealed-read-on-reject
test, deferred commands.
