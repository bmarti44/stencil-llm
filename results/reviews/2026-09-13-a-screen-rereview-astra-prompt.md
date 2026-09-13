# Re-review: candidate-A screen after amendment 1 (still before any long-running GPU work)

You reviewed this screen's implementation and read **REJECT for launch** on 15 findings
(`results/reviews/2026-09-13-a-screen-implementation-review-astra.md`): "The scorer can award
false session successes, and permitted first replies can remove every governing rule from
request 2. Resolve the findings before the timing pilot."

All 15 were worked. Your job now: decide whether the screen may launch, and find what is still
wrong. The owner's rule (2026-09-13) is that you review for bugs BEFORE the timing pilot, the two
4-hour trainings and the 3 × 48 evaluation, and that every finding is verified and resolved
first. A second standing instruction from the owner is "don't over engineer": a finding that adds
machinery without changing a decision is a finding you should not raise.

Do NOT read `data/bench/`. Do not add arms, models, benchmarks or review stages. Do not propose
reframing the direction; round 8 closed that ("a 30% forecast is a reason to purchase the
screen's information, not a reason to continue reframing").

## What changed (all committed on main, commit `aa2706c7`)

Read `results/a-screen/REGISTRATION-A-SCREEN.md` **§13, amendment 1** first: it lists every
change against your finding numbers, including the two places where your finding did not
reproduce as written and what was found instead.

Summary of the resolutions, so you can attack them directly:

- **F7** `src/stencil/a_screen.py`: a PROTECTED suite at checkpoint 2 re-runs request 1's
  functional, contract-under-state-1 and support tests on the checkpoint-2 repository
  (`protected_`-prefixed), ANDed with `api_preserved` / `public_api` (AST: public top-level
  defs/classes and public methods as qualified names). J now requires five suites at both
  checkpoints.
- **F1** request 2 always renders the CURRENT content of changed files; `drop_first_order(2)`
  evicts the superseded request/reply pair before any prefix turn; `required_indices` is asserted
  at run time in `scripts/a_screen_run.py`; `synthetic_reply` qualifies every session at the
  1,536-token cap. The registered caps are UNCHANGED (1,536 new / 2,560 prompt); an earlier
  attempt to raise them removed the compaction pressure and was reverted.
- **F2** request 1 renders from `files0` (the original repository).
- **F9** mutation-verified. The missing-record "changes nothing" test now snapshots the complete
  record mapping before/after the unknown-id call (previously an implementation that cleared the
  whole store passed). Your logging claim located the defect in the `silent` state, which is in
  fact airtight (`assert caplog.records == []` under `caplog.set_level(logging.DEBUG)` catches
  INFO and DEBUG; verified by mutation); the real defect was the **`warn`** state's "active
  records produce no log record" test, which checked only `levelno >= WARNING`. Both are fixed in
  `src/stencil/a_train_pool.py`.
- **F10** `scripts/a_screen_freeze.py` narrows the claim to what it verifies and records a
  measured `overlap` block; §1 and §13.3 of the registration now match it.
- **F11/F12** `scripts/a_screen_summary.py`: alpha 0.025 per component interval; both requests
  loaded and validated; duplicate records, mixed identities and a request 2 without a request 1
  refused; session outcomes recomputed from the stored suites; INCOMPLETE read against the
  manifest.
- **F13** §13.5 decides it: one uninterrupted 4-hour process per allocation under
  `STENCIL_GPU_SHARE=1`, no resumption, and `scripts/a_screen_run.py` refuses an adapter whose
  `train-log.json` is missing, non-final, or trained under a different objective than the arm.
- **F3, F4, F5, F6, F14, F15** per-request persistence and identity-filtered resume; the full EOS
  set with a late EOS still failing; the determinism import before torch; split training
  telemetry; `--longest N`; freeze verification in both entrypoints with non-zero exit on any
  problem.
- Pools re-frozen: SCREEN `e0867688b60e1071`, TRAIN `f6b3d63e941e1d70`.
  `tests/test_a_screen.py`: 301 passed.

## Questions (answer each; cite file:line)

1. **Did each of the 15 findings actually get resolved, or only moved?** For each, say
   RESOLVED / PARTIAL / NOT RESOLVED / WITHDRAWN and why. Be specific about F1 and F7: construct
   the worst permitted reply you can and say what it scores.
2. **New defects introduced by the fixes.** The PROTECTED suite, `api_preserved`, the
   `drop_first` eviction order, the snapshot helper in the TRAIN checkers, the summary's
   validation loader and the adapter guard are all new code. Can any of them (a) fail a correct
   reply, (b) pass an incorrect one, or (c) differ between arms? `api_preserved` in particular:
   is an AST-name check the right test, and does it forbid a legitimate solution to any of the 48
   slots?
3. **Is the screen's claim now supported by its apparatus?** Given §13.3's measured construction
   overlap (44/48 slots share TRAIN's dataclass-plus-mapping idiom), what exactly may the screen
   conclude if `cf` beats `off` and `sft` at the §7 gate, and what may it not? Is §6's binary
   outcome still the right unit?
4. **Statistics.** Verify `mcnemar_exact` is exact and two-sided, that the union-bound interval
   is the registered one at alpha 0.025, and that gates 1-5 match §7 as written. Recompute at
   least one boundary case by hand.
5. **Compute against §8.** ~15 s/request × 288 requests + 2 × 4 h training + reference scoring
   inside `cf`'s allocation + the pilot, against the 16 GPU-h ceiling, with §13.5's
   one-allowed-re-run rule. Does it fit, and is anything missing?
6. **Anything that would make the screen's result uninterpretable** that the owner is not
   thinking of.

End with one line: **LAUNCH** or **DO NOT LAUNCH**, and if DO NOT LAUNCH, the shortest list of
changes that would change your answer. Severity per finding: critical / high / medium / low with
a one-line fix. Write plainly; do not soften.
