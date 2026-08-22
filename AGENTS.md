# Agent playbook — Stencil

Operational lessons for every agent working in this repo (codex coders and
reviewers auto-load this file; the Claude orchestrator loads it via CLAUDE.md).
PLAN.md governs — this file never overrides it; it accumulates the "how to work
well here" lessons from phase retrospectives (PLAN.md Section 2b). Keep entries
short, imperative, and evidence-linked; prune entries that stop paying rent.

## Working rules distilled so far

- PLAN.md is the single source of truth. Read the Section 2b protocol and the
  Work log and ledger section before doing anything; append ledger entries
  (write-ahead for long-running work) as you go.
- Never edit repo files while a review/coder wrapper is running — the wrapper
  hard-fails on uncontained drift, and its restorer can clobber your edits.
  Wrappers serialize on `.review.lock`; respect it.
- Numbers in specs are claims: recompute them. Round 1 of the plan review found
  the registered chance rate mathematically impossible and the registered
  energy tests unpassable by the registered integrator. Verify arithmetic and
  closed forms before building on them.
- Exact-zero and bitwise assertions must fail loudly when vacuous: a `None`
  gradient or a detached graph is a test bug, not a pass.
- Severity honesty: review findings are graded low/medium/high/critical, and
  acceptance mechanically blocks on open high/critical (check_review_scores.py).
  Do not negotiate severities; fix or refute with evidence.
- When a spec is ambiguous, take the most conservative reading, record the
  choice in the PLAN.md ledger, and flag it for the next review round.

## Retrospective log pointers

(none yet — first entry lands at the end of Phase 0; full retros live in
docs/retros/<phase>.md)
