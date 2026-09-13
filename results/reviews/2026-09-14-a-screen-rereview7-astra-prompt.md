# Re-review round 8: candidate-A screen after amendment 7 (still before any GPU work)

You have reviewed this screen seven times: REJECT (15 findings), then DO NOT LAUNCH six times.
Round 7 said: "A silent final interval remains undercharged, and missing spend evidence still
permits GATE PASSED." You were right about the shape of the error, not just the instance: the
heartbeat rule INFERRED TERMINATION FROM SILENCE. All four of your items were reproduced before
anything was changed, and the first one was fixed by deleting the inference, not by widening it.

Your job: decide whether the screen may launch, and find what is still wrong.

Standing instructions from the owner: you review before the timing pilot, the two 4-hour
trainings and the 3 × 48 evaluation; and **"don't over engineer"** — a finding that adds
machinery without changing a decision is one you should not raise. Do NOT read `data/bench/`.
Do not add arms, models, benchmarks or review stages, and do not reframe the direction.

## What changed (read `results/a-screen/REGISTRATION-A-SCREEN.md` §19 first; §18.1 and §18.2 now
carry SUPERSEDED/AMENDED markers pointing at it)

1. **A charge is now bounded by evidence or not at all.** Your counterexample reproduced at
   780 s. The heartbeat slack is gone. Three cases: a launch that wrote `end` is charged its real
   elapsed time; one whose termination was OBSERVED is charged through that observation; one that is
   neither is charged its whole lifetime through `now`, uncapped. `ledger_observe` is the evidence —
   it checks whether the pid in the launch id still exists and, if not, writes one `observed_dead`
   line, after which the charge never moves. A live or recycled pid is not observed and keeps
   accruing. The runner observes BEFORE the model load, so recovering from a kill costs no GPU time;
   the summary only reads, never writes evidence it is about to judge. The ticker survives as a
   progress log with nothing depending on it, which also retires the uncaught-exception defect.
   **Attack the pid test**: is "`/proc/<pid>` is gone" sound evidence of termination here, and is
   there a way for a launch to spend GPU time that none of the three cases charges?

2. **Absent spend evidence is a refusal, not a zero.** Your deleted-sidecar case reproduced.
   `ledger_spent_min` now refuses unless the ledger exists, is non-empty, parses completely, and
   accounts for EVERY launch the records name (each record carries its `launch`; a record without
   one is itself a refusal). And you were right that suppressing only the verdict was cosmetic: for
   an ineligible evaluation the contrasts and the five gates are no longer COMPUTED — the summary
   prints the arm table, the refusals, and the verdict, then stops. Verified on four scenarios,
   including the control: the same records at 40 minutes inside the ceiling still print 12 gate
   lines and `GATE PASSED`, so the refusals are not vacuous.

3. **The ceiling is derived, and it includes the admission margin.** I recomputed your arithmetic
   and got your numbers: request 96 refused at 2,416.158 s, completion at 40.66 min, 2.73 min of
   real load headroom at a 45-minute ceiling, not §18.2's claimed 7.3. `A.arm_budget_min()` now
   COMPUTES the smallest ceiling that still admits the last request — 47.27 min — and the registered
   ceiling is **50 min**, which is 2.5 h for three arms: §15.5's 1.8 h of generations plus 0.7 h
   inside its 2.1 h remainder, so the re-run reserve still stands. A test simulates the real guard
   over all 48 sessions and asserts 95/96 admitted at 45 min and 96/96 at 50.

4. **The registered output cap is enforced.** `--max-new 2048` is refused at parse time for a full
   run, and the summary checks `max_new`, `prompt_budget` and `deadline_s` against their REGISTERED
   values rather than only against each other.

5. **Your low finding is fixed and the claim is now true.** Ambiguity is a value in the env that no
   later rule may see past, so `a = B(); replace(a, ...); a = A()` reports the site UNRESOLVED.

## Where to look

- `results/a-screen/REGISTRATION-A-SCREEN.md` §19 (amendment 7); §12–§18 are the earlier freezes.
- `src/stencil/a_screen.py` (`ledger_observe`, `ledger_charges`, `ledger_spent_min`, `read_status`,
  `arm_budget_min`, `ARM_BUDGET_MIN`), `scripts/a_screen_run.py` (the startup observation, the
  parse-time guards), `scripts/a_screen_summary.py` (eligibility and the short circuit),
  `scripts/a_screen_mutate.py` (`AMBIGUOUS`), `tests/test_a_screen_spend.py` (your cases by name,
  including four end-to-end summary scenarios on synthetic 48-session records).
- Current freeze and clean-tree numbers: §19.7.

## Questions (answer each; cite file:line)

1. For your four items: RESOLVED / PARTIAL / NOT RESOLVED.
2. Is there any remaining path by which a launch spends GPU time that the ledger does not charge, or
   by which an ineligible evaluation reaches a gate reading? And the reverse, which matters as much
   now: can a LEGITIMATE full run inside the registered compute be refused — by the 50-minute
   ceiling, by the uncapped charge for an unobserved launch, or by the new ledger-coverage rule?
3. Is there any remaining path by which a session scores J = 1 while the repository is wrong, or
   J = 0 while it is right?
4. Defects introduced by these fixes: the pid-based observation (including pid recycling and the
   ledger line it appends), the derived ceiling, the parse-time cap enforcement, the summary's short
   circuit, the `AMBIGUOUS` sentinel.
5. Statistics and the five gates: still as §7 registered?
6. Anything else that would make the result uninterpretable.

End with one line: **LAUNCH** or **DO NOT LAUNCH**, and if DO NOT LAUNCH, the shortest list of
changes that would change your answer. Severity per finding: critical / high / medium / low with
a one-line fix. Write plainly; do not soften.
