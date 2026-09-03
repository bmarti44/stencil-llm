# Brief: multiif-control-shortfall — the Leg B run crashed at conversation 145: "cannot match 79 pinned columns with 68 controls"

## Objective
scripts/multiif_evict.py died at 11:14 on conversation 145/909 (log in the orchestrator's scratchpad) in
matched_control_spans (line ~244): the classifier pinned more than half of the evictable range on a short history, so an
exact-column control cannot be drawn. LEDGER-PLAN.md "LEG B AMENDMENT 3" (appended before this brief) registers the
handling: when an exact-column control cannot be drawn, the conversation is recorded with control_impossible = true,
its clf_control arm is NOT run (fields null), it is EXCLUDED from contrast C1 and counted in the summary
(n_control_impossible), and every other arm runs and scores normally (C2, C3 and all reported metrics keep it). Implement
exactly that; never raise; never delete records. Also: (1) record the shortfall arithmetic per conversation (pinned
columns, available columns); (2) the summary's C1 population and n_control_impossible; (3) a resume-safe change: the
meta hash of the harness will change — the registered rule is that a resume refuses on meta difference, so the
orchestrator RESTARTS the run in a NEW directory (multiif-evict-909-prequery-v2); do not weaken the resume check;
(4) tests: a synthetic conversation whose pins exceed half the evictable range runs all other arms and produces the
recorded fields; summary excludes it from C1 only.
NEVER read data/bench/ifeval_input_data.jsonl. Never modify data/bench/*. GPU: do NOT launch model processes (a probe
and a queued preflight own it); CPU tests only.

## Allowlist
See multiif-control-shortfall.allow.

## Tests first (TDD, rule 1)
RED first. Run ONLY tests/test_multiif_evict.py + your new test. DO NOT run the full suite.

## GPU policy
No GPU. Never wait on a lock; never signal any process.

## Acceptance
Tests green; ruff clean; commit before finishing.

## Ledger handoff
Append to WORKLOG.md: the fix (file:line), the recorded fields, the restart command for the orchestrator.
