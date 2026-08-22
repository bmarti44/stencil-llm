# Agent playbook — Stencil

Operational lessons for every agent working in this repo (codex coders and
reviewers auto-load this file; the Claude orchestrator loads it via CLAUDE.md).
PLAN.md governs — this file never overrides it; it accumulates the "how to work
well here" lessons from phase retrospectives (PLAN.md Section 2b). Keep entries
short, imperative, and evidence-linked; prune entries that stop paying rent.

## Working rules distilled so far

- North star (Brian, 2026-08-22): agents work efficiently, quickly, accurately,
  and autonomously on PLAN.md. Burden test for any new rule/file/process step:
  does it change what an agent would do in a concrete situation, and does it
  make execution faster or more accurate? If not, cut it.
- Layout: PLAN.md (root) = governing science spec. plan/ = working directory:
  PROTOCOL.md (process rules), LEDGER.md (resume from its STATE line),
  AMENDMENTS.md, reviews/, retros/, tiebreaks/.

- PLAN.md (science) and plan/PROTOCOL.md (process) govern together; plan/LEDGER.md
  is operational state. Read PROTOCOL.md and the LEDGER STATE line before doing
  anything; append ledger entries (write-ahead for long-running work) as you go.
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
  choice in plan/LEDGER.md, and flag it for the next review round.

- Background or queued shell commands must use absolute paths — the shell's
  working directory is not guaranteed between commands (a relative-path launch
  silently no-opped a whole review round on 2026-08-22).
- Reviewers: never delete a prior finding — close it with (resolved/refuted)
  markers; the validator rejects candidates that drop high/critical numbers.
- A practical threshold grades magnitude; it can never decide whether evidence
  exists. Existence questions get a registered statistical test.

- Smoke-invoke any edited `set -u` shell script before committing — a
  variable-ordering slip killed a full review round silently (2026-08-22).
- Serialized background chains need per-command failure visibility; a trailing
  echo sentinel masks upstream failures. Read the raw log, not the exit code.

## Retrospective log pointers

(none yet — first entry lands at the end of Phase 0; full retros live in
plan/retros/<phase>.md)
