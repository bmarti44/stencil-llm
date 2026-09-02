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
- CODERS launched by `tools/run_codex_agent.sh`: the `.review.lock` you see is
  held by YOUR OWN wrapper for the duration of your task. Never wait for it and
  never poll it — write, test, and `git commit` your allowlisted files directly.
  Two coders (2026-09-02) finished their work, then waited on their own lock
  until the timeout and the restorer wiped the tree. Also: never run the full
  pytest suite (it exceeds the wrapper timeout); run the targeted tests named in
  the brief. Orchestrator: while a wrapper is active, commit only with explicit
  pathspecs (`git commit -- <paths>`) so a coder's staged index is not swept in.
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
- Never import a script that does work at module top level: importing
  t2_train_selector for one helper silently RETRAINED and overwrote the
  registered checkpoint before every evaluation (closing-review CRITICAL,
  2026-08-30). Shared helpers live in src/; script bodies go under a
  main() guard; tests/test_no_side_effect_imports.py enforces this.
- Claim only what the artifact measures: "never pressed"/"bitwise identical"
  died under sol's re-verification (actual: 14/14794 presses, code-string
  identity). Either instrument the exact claim (press counters, hashes) or
  narrow the words to the measurement (2026-08-30).

- Smoke-invoke any edited `set -u` shell script before committing — a
  variable-ordering slip killed a full review round silently (2026-08-22).
- Serialized background chains need per-command failure visibility; a trailing
  echo sentinel masks upstream failures. Read the raw log, not the exit code.
- `pytest | tail` swallows the failure exit code — a red test got committed
  under a green-looking chain (2026-08-30). Use `set -o pipefail` in any
  chain that pipes a test runner.
- Test the consumer's semantics, not the producer's output: a validator must be
  exercised through the exact code path that consumes it (a `tr`-based check
  passed while the real `read -d ''` consumer dropped the final path, 2026-08-22).
- The orchestrator is the terminator: flagging an absurd loop without acting is
  not acting. Apply the burden test and the registered stop-loss mechanically —
  in the amendment spiral, "one more fix" repeatedly beat "stop" until a human
  intervened.

## Retrospective log pointers

- plan/retros/plan.md (2026-08-22) — acceptance loop; the amendment spiral is
  the centerpiece; corrections appended after its kimi review.
- plan/retros/phase0.md (2026-08-22) — first implementation phase; 2-round
  convergence; corrections appended after its kimi review.
- plan/retros/phase1.md (2026-08-22) — generators pinned by three-way
  independent agreement; README-row recurrence drove mechanization.
- `results/*` is GITIGNORED by the repo layout policy: `git add -A` silently
  skips new result artifacts. Registered artifacts must be `git add -f`'d, and
  "committed" claims verified with `git ls-files` (six B0 artifacts were
  claimed committed while untracked, 2026-08-30).
- Sealed one-shot jobs MUST write their registered per-work records in
  the same run — twice (w_seal, w3a) the records were built in memory
  and only aggregates written, forcing reproduction audits. Put the
  registered output field list in the artifact writer and dry-assert it
  on a smoke run before sealing (2026-08-30).
