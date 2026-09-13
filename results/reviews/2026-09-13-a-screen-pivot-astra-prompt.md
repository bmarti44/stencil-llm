# Review: the candidate-A screen after the review loop was closed — is the experiment now interpretable?

You have reviewed this screen ten times (REJECT once, then DO NOT LAUNCH nine times). **That loop
is over.** The owner intervened mid-session: *"don't do pre-registration, don't over-engineer - we
need to quickly and accurately work on everything. make sure you can see the results as they come
in, and if the trajectory cannot possible recover, stop and fix. you don't have to be academically
rigorous in any of this until we actually have something that we think works and now we want to
prove."*

So this is **not** another gate review. Do not ask for registration amendments, new arms, new
review stages, or machinery whose only effect is rigor for its own sake. The screen is RUNNING.
The `off` arm is executing as you read this.

Your job: find anything that would make the answer **uninterpretable or wrong**, and confirm or
refute the five judgement calls listed below. A finding that does not change a decision is one you
should not raise. Do NOT read `data/bench/`. Do not perform GPU work.

## What the experiment is

Qwen3-4B trunk, frozen. Three arms over 48 SCREEN sessions x 2 requests:
`off` (no adapter), `sft` (LoRA, completion cross-entropy on gold), `cf` (the same cross-entropy
plus `0.1 * L_DPO`, beta 0.1, against the STALE-state gold as the rejected completion).
Each session states a convention early, then a lifecycle event may CHANGE that convention before
request 2. The question is whether the counterfactual term makes the model follow the convention
**in force** rather than the **superseded** one.

Training pairs: `src/stencil/a_screen.py:pairs_from_session` — chosen = gold under the state in
force, rejected = gold under the stale state, two variants per session (`event`, `irrelevant`).

## The five calls to confirm or refute

1. **A fixture was DELETED rather than repaired.** Your round-10 finding 2 showed
   `test_no_public_call_disturbs_the_id_allocator` (added round 9, present in 23 of 48 slots)
   rejects a CORRECT reply: a behaviour-preserving `initialize_bank(bank, accounts)` constructor
   refactor gets called by the fixture with a junk string and the suite fails, while the identical
   helper named `_initialize_bank` passes. I reverted the fixture out of all 23 slots
   (`git checkout eecde769^ -- src/stencil/a_screen_pool/`); SCREEN pool is back to
   `ef802ce2160ee00c`. **Is removal sound, or did it introduce a defect that differs BETWEEN arms?**
   Note the amendment-6 per-operation create-after-operation fixtures are still present.

2. **Your round-10 finding 1 was dropped, with this argument:** the audit under-generates resets
   placed below a lookup, so my suites are less sensitive to allocator damage than I claimed; but
   that is a property of the INSTRUMENT applied identically to `off`, `sft` and `cf`, so it cannot
   manufacture a difference between arms — only add noise equally. Measured at **51 undetected of
   1,695** with statement-level insertion. **Is that argument correct?** If an arm could be
   differentially affected (e.g. adapters systematically produce a reply shape the audit misses),
   say so and name the shape.

3. **The primary readout changed from J to a contract-state measure.** J = all six suites pass at
   BOTH checkpoints. Observed `off` J = 0/25 so far, and when J fails it cannot say WHY: S01's
   failure was plain competence (the reply did not persist the record), not focus. The replacement,
   computed post-hoc from saved records with no extra GPU: re-run each reply against the screen's
   own `contract_tests[state_in_force]` AND `contract_tests[superseded_state]`, giving one clean
   bit per request — `in-force` / `STALE-RULE` / `neither`. Script:
   `/tmp/claude-1000/-home-bmarti44-stencil-llm/14c2306d-603f-4fa8-b992-19e1aefb2f05/scratchpad/stale.py`
   (it reconstructs the ARM's own repository via `A.apply_reply`, not the gold, so request 2 is
   scored on the repository that arm actually built). Interim `off` numbers at 24 sessions:
   in-force 46%, STALE-RULE 19%, neither 35%; conditioning out `neither`, **71% of decidable
   replies follow the convention in force**. **Is this measure sound and correctly computed?**
   Specifically: (a) is the conditional rate `in-force / (in-force + STALE-RULE)` a legitimate
   estimand here or does conditioning on an outcome-dependent set bias the arm comparison; (b) can
   a reply pass BOTH contract suites, and if so is my "both (states agree here)" bucket handled
   right; (c) is the repository reconstruction correct.

4. **Optimizer steps will be matched, not wall clock.** `cf` precomputes DPO reference log-probs
   (measured 52 s per 16 examples, ~1,152 examples, so ~62 min) and then runs TWO forward passes
   per micro-step where `sft` runs one. At an equal 4-hour allocation `cf` gets roughly 166 steps
   against `sft`'s ~360 — under half. A `cf` loss would then be uninterpretable. Plan: run `cf`
   first at 4 h, read its achieved step count, then run `sft` with a new `--max-steps` equal to it
   (`scripts/a_screen_train.py`). **Is matching optimizer steps the right control for this
   question, or does matching compute answer it better?** Both are defensible in general — say
   which this specific claim needs. Also: **is ~166 steps (~1.15 epochs over 1,152 examples, LoRA
   rank 16, lr 1e-4) enough to move the behaviour at all**, or am I setting up a null that means
   nothing? If it is too few, say what you would do given the owner wants an answer quickly.

5. **Leakage was checked and is clean:** TRAIN (576 sessions, 18 projects) and SCREEN (48 sessions,
   48 projects) share 0 project names, 0 request texts, 0 project files. **Is that sufficient to
   rule out leakage, or is there a subtler path** — shared convention vocabulary, shared gold
   idiom, the same generator's phrasing — that would let an adapter win for a reason that does not
   generalise? Both pools come from the same authoring conventions and the same six families, and
   I am stating plainly that a win proves "works on synthetic sessions of this shape", not "works
   in a real agentic coding session".

## Where to look

- `src/stencil/a_screen.py` (`pairs_from_session`, `score_checkpoint`, `gold_files`, `run_tests`),
  `scripts/a_screen_train.py` (the loop, the new `--max-steps`, reference scoring),
  `scripts/a_screen_run.py`, `src/stencil/a_screen_pool/`, `src/stencil/a_train_pool.py`.
- Live records: `results/a-screen/runs/off.jsonl` (one JSON record per request, with `output`,
  `scores`, `target_family`, `support_family`, `lifecycle`, `rule_state`).
- `results/a-screen/REGISTRATION-A-SCREEN.md` is the registration as written; sections 12-21 are
  the earlier review rounds. It is context, not a constraint — the owner has released me from it.
- `plan/LEDGER.md`, last entry, records the direction change.

## Questions (answer each; cite file:line)

1-5. The five calls above: CONFIRMED or REFUTED, with the reason.
6. Is there any remaining path by which this experiment produces a DIFFERENCE BETWEEN ARMS that is
   not caused by the counterfactual objective? That is the only question that matters now.
7. Is there any path by which a real effect is HIDDEN — a floor, a ceiling, or a measure too
   coarse to see it? `off` J = 0/25 is the obvious candidate.
8. Anything else that would make the result uninterpretable.

End with one line: **INTERPRETABLE** or **NOT INTERPRETABLE**, and if the latter, the shortest list
of changes that would change your answer. Severity per finding: critical / high / medium / low with
a one-line fix. Write plainly; do not soften. Prefer "this is fine" over inventing work.
