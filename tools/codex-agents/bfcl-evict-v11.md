# Brief: bfcl-evict-v11 — close fable's harness-v8 review (FV8-2..7) on top of v10

## Objective
Governing text: LEDGER-PLAN.md LEG A v7 + AMENDMENTS 1-5. Review to close: results/harness-v8-review-fable.md
(FV8-1 is the certificate split-invariance defect already fixed by v9/v10 — verify with fable's dev-vs-sealed
round-trip test; FV8-2 HIGH: `_resource_match` must declare match_impossible ONLY when the eligible pool's TOTAL
columns are fewer than the quota (Amendment 3.1), never when the count of unused resources is fewer than the count
of targets — implement fable's fix and its census case (case 24 t5 all-user stub); FV8-3 MEDIUM: sealed-path
invariant violations are RECORDED and make the affected contrast uninformative (Amendment 4.3), never raise
mid-cohort; schema/preflight delta checks gated on pressure turns; FV8-4 MEDIUM: the echo clamp must measure token
counts LOCALLY (encode only the entry text with the registered boundary handling), not re-encode the full context
per probe — fable's exact fix; keep bitwise-equal clamp results on a test; FV8-5: full's final_pass must exclude NA
turns (not count them as fails); FV8-6: manifest residuals (scripts/__init__.py, bench exclusion); FV8-7: tool_swap
user rows carry _echo_source_columns). Current code: v10 (after the bfcl-evict-v10 coder). Each fix with a CPU test;
all prior tests green. `--split sealed` is NOT to be run. NEVER read the sealed IFEval input file. Never modify
data/bench/*. GPU: BUSY — no model process; record deferred commands.

## Allowlist
See bfcl-evict-v11.allow.

## Tests first (TDD, rule 1)
RED first. Run ONLY tests/test_bfcl.py tests/test_bfcl_evict_v{2,3,4,5,6,7,8,9,10}.py tests/test_sealed_guard.py and
your new tests/test_bfcl_evict_v11.py. DO NOT run the full suite.

## GPU policy
No GPU. Never wait on a lock; never signal any process.

## Acceptance
CPU tests green; ruff clean; commit EARLY and often.

## Ledger handoff
Append to WORKLOG.md: each finding -> fix (file:line), the census results, the local clamp measurement, deferred
commands.
