# Sol xhigh correction brief — mechanics findings 1–3

Fit-on: accepted FIT material only in the later registered run. This correction
uses synthetic CPU tests and read-only frozen input qualification; no training,
evaluation, new semantic data, weights, CUDA or network. Native agent, no wrapper.

Fix the three findings in mechanics-review-astra.md round 2, exact report SHA
`9963300cd61b8afffc0918a10a22d607e0df382dd6f7819e2baf36cdb761ed50`.
Start from e4f45c2c57e416483dcbc6684cb8117ff287cff4. Read the complete findings,
accepted MECHANICS.md and original MECHANICS-CODE-BRIEF.md; neither changes.
Root independently reproduced finding 1 and verified 2/3 against the actual
update/receipt/clock order. All three findings require correction.

Writable allowlist only:
- scripts/source_interpreter_mechanics.py
- tests/test_source_interpreter_mechanics.py

1. Import the installed `stencil.focus` package. Add a fresh subprocess test of
   the actual direct-file path's data consumer without pytest/repository-root
   path injection. Dry-run alone never reaches this consumer. Preserve the
   accepted helper and exact data/tokenization contract.
2. Write durable step intent before work, and record synchronized optimizer
   completion before potentially failing validation, hashing or resource work.
   Keep performed updates distinct from validated updates. Preserve confirmed
   counts and explicitly identify pending/unknown completion on interruption;
   never claim an exact zero for an unresolved attempt. Use the existing receipt
   path and a few explicit stage fields, not a transaction framework. Test the
   actual step consumer with tiny CPU doubles failing after a performed update,
   including warm-up accounting, and pending-step timeout recovery.
3. Separate child exit time from finalization. Include validation, partial-record
   handling and flag cleanup in measured terminal cost. Use a late clock/bound
   check so delayed finalization cannot retain COMPLETE. Explicitly state any
   final receipt-publication tail; root's later outer process observation will
   measure the whole process. Test delayed finalization through the supervisor.

Write failing regressions before fixes. Keep changes narrow: no new trainer,
server, generic validator or changed model/data/settings/budget. No tests on
spent banks or real training. Do not edit the canonical review or original
accepted brief/hash constants merely because this supplemental brief exists.

Acceptance: `.venv/bin/pytest -q tests/test_source_interpreter_mechanics.py`,
Ruff check/format on both files, direct-path CPU qualification, dry-run/import
smoke and `git diff --check`. No full suite or unchanged helper tests. Commit
only the two explicit paths. Return commit and both hashes, exact tests and
red-first evidence, direct-path qualification result, and any residual issue.
Root records the ledger and obtains the same Astra reviewer's delta acceptance
before launching the four-step measurement.
