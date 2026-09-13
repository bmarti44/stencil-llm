# Re-review round 7: candidate-A screen after amendment 6 (still before any GPU work)

You have reviewed this screen six times: REJECT (15 findings), then DO NOT LAUNCH five times.
Round 6 said: "The screen still cannot launch. Interrupted spend can be undercharged, and the
summary can authorize progression from an over-budget evaluation. The previous scoring
counterexamples are closed." You gave a two-item shortest list; both were reproduced by executing
the accounting before anything was changed, then fixed, and your low finding was fixed too.

Your job: decide whether the screen may launch, and find what is still wrong.

Standing instructions from the owner: you review before the timing pilot, the two 4-hour
trainings and the 3 × 48 evaluation; and **"don't over engineer"** — a finding that adds
machinery without changing a decision is one you should not raise. Do NOT read `data/bench/`.
Do not add arms, models, benchmarks or review stages, and do not reframe the direction.

## What changed (read `results/a-screen/REGISTRATION-A-SCREEN.md` §18 first)

1. **Both of your blocking items were reproduced first.** Your loading case charged 600 s for
   900 s of residence, exactly as you said; the pilot's `model_loaded` → `suite_cost_measured` gap
   runs 4 × 11 = 44 suite invocations against a bound assuming six. And synthetic complete
   48-session records at your 2,701 s spend printed `Verdict: GATE PASSED`, text and all.

2. **The caps are gone, replaced by a verified alive-timestamp.** `work_bound_s` and
   `LOAD_BOUND_S` are deleted. A HEARTBEAT thread (`A.ledger_tick`, `TICK_S` = 60 s, first tick
   before the first wait) runs from before the model load until exit, so every interval of a
   launch's life is closed by a mark. A launch with no `end` is charged its last mark plus
   `3 × TICK_S` when its heartbeat is INTACT, and its WHOLE LIFETIME, uncapped, when it is not
   (a hole no mark closes). Attack the intactness argument: is "the ticker would have written
   another mark had it lived longer" sound at three intervals of slack, and is there a way for a
   launch to spend GPU time that neither branch charges?

3. **Budget eligibility is durable and the summary enforces it.** `A.ARM_BUDGET_MIN = 45` is a
   registered per-arm ceiling; a full screen arm is refused at parse time outside `0 < b ≤ 45`
   (§18.2 gives the arithmetic against §15.5). The runner writes `<out>.status.json`; the summary
   refuses an arm whose status is missing, a pilot's, not COMPLETE, outside the ceiling, or claims
   more spend than its budget, AND independently recomputes the arm's spend from its ledger, so a
   status lying about its spend is caught by the evidence. §18.2 also records the ONE escape, which
   is §15.5's own: if the pilot measures a per-request cost that does not fit, the re-run reserve is
   surrendered first and the ceiling may be raised once, before any arm runs, never after. On any
   refusal the verdict is
   `INCOMPLETE (budget eligibility: …)` and **the gates are not read at all** — §8 says no
   checkpoint is selected to rescue an exhausted ceiling, and a "provisional: GATE PASSED" tail is
   exactly that rescue. Verified on your own scenario, on a lying status, and on no status at all;
   the same records inside budget still read GATE PASSED. Judge whether the registered 45 min is
   the right number and whether anything else the summary trusts is undurable.

4. **Your low finding, and your soundness note, are both fixed — and the fix is narrower than
   the finding.** `whole_record_writers` requires the stored expression to derive from one of the
   method's own PARAMETERS. Without that condition 41 of 48 slots qualify and 11 mutants return;
   with it exactly one slot qualifies (S35's `OrderBook.save`) and exactly the two mutants you
   named return — independent agreement with your "the nine other exclusions have defensible
   reachability arguments". 959 → **961** emitted. And it is measured, not argued: the LOOSE rule's
   audit was run to completion first — 970 mutations, **9 undetected** — and those 9 are exactly the
   9 the parameter condition excludes, while the 2 it keeps were already detected. The partition the
   rule draws is the partition between detectable and undetectable. And a name assigned two different classes in
   one function is now dropped from `_env`, so your `old = A(...)` / `old = B(...)` case reports
   the site UNRESOLVED (which exits 1) instead of mutating `B`'s field on an `A`.

## Where to look

- `results/a-screen/REGISTRATION-A-SCREEN.md` §18 (amendment 6); §12–§17 are the earlier freezes.
- `src/stencil/a_screen.py` (heartbeat, `ledger_charges`, `write_status`/`read_status`,
  `ledger_spent_min`, `ARM_BUDGET_MIN`), `scripts/a_screen_run.py` (tick thread, the budget
  refusal, the status artifact), `scripts/a_screen_summary.py` (eligibility),
  `scripts/a_screen_mutate.py` (`whole_record_writers`, `_env`),
  `tests/test_a_screen_spend.py` (your cases by name, including the real summary on synthetic
  48-session records).
- `results/a-screen/AUTHORING.md` amendment 5; `src/stencil/a_screen_pool/s01.py`–`s48.py`.
- Current freeze: SCREEN and TRAIN hashes and the clean-tree check numbers are in §18.6.

## Questions (answer each; cite file:line)

1. For your two blocking items and your low finding: RESOLVED / PARTIAL / NOT RESOLVED.
2. Is there any remaining path by which a launch spends GPU time that the ledger does not charge,
   or by which an ineligible evaluation reaches a gate reading? Include the reverse: does the
   45-minute ceiling or the heartbeat's conservative charge make a LEGITIMATE full run report
   INCOMPLETE when it stayed inside the registered compute?
3. Is there any remaining path by which a session scores J = 1 while the repository is wrong, or
   J = 0 while it is right? The parameter condition on `whole_record_writers` is a judgement about
   what a public suite can observe — attack it if a caller can set a field some other way.
4. Defects introduced by these fixes: the tick thread (it writes to the ledger concurrently with
   the main thread — 3,078 two-thread writes produced 0 malformed lines, attack the argument not
   the sample), the parse-time budget refusal, the status artifact, the summary's two independent
   checks, the narrowed writer rule, the ambiguous-name drop in `_env`. One defect in the new code
   was already found this way and is recorded in §18.4 (`_root_name` walked a method call to its
   argument instead of its receiver; measured to change nothing in the frozen pool).
5. Statistics and the five gates: still as §7 registered?
6. Anything else that would make the result uninterpretable.

End with one line: **LAUNCH** or **DO NOT LAUNCH**, and if DO NOT LAUNCH, the shortest list of
changes that would change your answer. Severity per finding: critical / high / medium / low with
a one-line fix. Write plainly; do not soften.
