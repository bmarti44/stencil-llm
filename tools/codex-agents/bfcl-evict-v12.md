# Brief: bfcl-evict-v12 — close fable's harness-v10 review (FV10-1, FV10-2, FV10-4/5) under LEG A AMENDMENT 6; final gate before the registered preflight

## Objective
Governing text: LEDGER-PLAN.md LEG A v7 + AMENDMENTS 1-6. Review: results/harness-v10-review-fable.md.
FV10-1 HIGH: `_turn_plan` must record invariant violations as `invariant_violation` (never as `match_impossible`);
`assert_dev_invariants` must FAIL on invariant_violation (no `or match_impossible` acceptance); the preflight's
excessive-echo stop predicate must not be disabled by match_impossible; on the sealed path an invariant_violation
is recorded and makes the affected contrast uninformative (Amendment 6). Three tests as fable lists (recency/tool-swap
column mismatch on a pressure turn; delta 29; certification refused).
FV10-2 HIGH: the post-run drift check must compare the harness manifest and data hashes only — exclude git
provenance (commits or untracked files during the ~7 GPU-h preflight must NOT abort or block the certificate); record
both provenances in evidence; test it.
FV10-4/5 LOW: `final_score.valid` excludes NA turns; notes.
Then: run the full allowlisted CPU suites, recompute and record the manifest hash and the registration hash (over
v7 + A1-A6) in WORKLOG. Current code: v10 (1a475df). `--split sealed` is NOT to be run. NEVER read the sealed IFEval
input file. Never modify data/bench/*. GPU: BUSY — no model process.

## Allowlist
See bfcl-evict-v12.allow.

## Tests first (TDD, rule 1)
RED first. Run ONLY tests/test_bfcl.py tests/test_bfcl_evict_v*.py tests/test_sealed_guard.py and your new
tests/test_bfcl_evict_v12.py. DO NOT run the full suite.

## GPU policy
No GPU. Never wait on a lock; never signal any process.

## Acceptance
CPU tests green; ruff clean; commit EARLY and often.

## Ledger handoff
Append to WORKLOG.md: each finding -> fix (file:line), the recomputed hashes, the exact registered preflight commands.
