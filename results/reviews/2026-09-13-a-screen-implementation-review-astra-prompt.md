# Implementation review: six-family candidate-A screen (before any long-running GPU work)

You are the adversarial implementation reviewer for a registered screen. The owner's rule
(2026-09-13): Astra reviews the implementation for bugs BEFORE the timing pilot, the two
4-hour trainings and the 3 × 48 evaluation run; every finding is verified and resolved
first. Do NOT read `data/bench/`. Do not add arms, models, benchmarks or review stages;
do not propose reframing the direction (round 8 closed that: "a 30% forecast is a reason
to purchase the screen's information, not a reason to continue reframing").

## What to review (all committed on main)

- Registration: `results/a-screen/REGISTRATION-A-SCREEN.md` (your own round-8 minimums,
  `results/reviews/2026-09-13-direction-adversarial-rev8-astra.md`), manifest
  `results/a-screen/manifest.json` (`scripts/a_screen_manifest.py`).
- Schema, packing policy, scoring, pair extraction: `src/stencil/a_screen.py`.
- SCREEN pool (48 hand-authored sessions, one per slot): `src/stencil/a_screen_pool/`,
  authored under `results/a-screen/AUTHORING.md`; freeze record
  `results/a-screen/screen-pool.json` (`scripts/a_screen_freeze.py`).
- TRAIN pool (576 generated sessions, 1,152 counterfactual triples): `src/stencil/a_train_pool.py`,
  built and checked by `scripts/a_train_build.py`, freeze record `results/a-screen/train-pool.json`.
- Self-checks: `tests/test_a_screen.py` (241 tests pass: 48 screen slots + 12 sampled train
  sessions × 4 checks, plus a packing unit test).
- Trainer: `scripts/a_screen_train.py` (LoRA r16/α32/dropout 0 on q,k,v,o,gate,up,down;
  AdamW 1e-4, clip 1, seed 0; micro-batch 1 × accumulation 8; `cf` = completion-mean CE +
  0.1·DPO(β 0.1) with the frozen trunk's reference log-probs precomputed once; `sft` = CE only
  on the same positives; fixed wall-clock; FINAL completed step saved). Smoke:
  `results/a-screen/smoke/cf-adapter/train-log.json` (16 examples, 3 min, 2 steps).
- Harness: `scripts/a_screen_run.py` (three arms, greedy, thinking off, ≤ 1,536 new tokens,
  300 s deadline, arm's own repository state, per-request records). Smoke records:
  `results/a-screen/smoke/off-S02.jsonl`, `cf-S02.jsonl` (~15 s per request).
- Gate summary: `scripts/a_screen_summary.py` (exact McNemar, Clopper-Pearson union-bound
  intervals, the five count gates).
- Scorer change: `src/stencil/contracts.py` `score` now runs contract tests independently.

## Questions (answer each; cite file:line)

1. Correctness bugs that would invalidate the screen or bias an arm: packing (does
   `pack` implement "newest whole turns that fit", never dropping the system line or the
   live request; is the token count the exact prompt the model sees?), request-2 history
   (verbatim first reply, event, changed-file rendering), scoring (all four suites at both
   checkpoints; failure handling for parse/apply/truncation/timeout), resumption, EOS
   handling, adapter loading (`off` truly bypasses; `sft`/`cf` identical otherwise),
   determinism.
2. Trainer bugs: loss construction (CE over completion tokens only; DPO sign and β;
   reference computed with NO adapter; sequence-sum vs mean), tokenization boundary
   between prompt and completion (does `prompt_ids + chosen_ids` equal what the harness
   feeds at inference, including the `<|im_end|>` terminator?), autocast/dtype of LoRA
   params, gradient checkpointing with PEFT, accumulation and the "final completed step"
   rule, time accounting (reference scoring inside the allocation), anything that lets
   `cf` and `sft` differ in more than the DPO term.
3. Pool validity: does any SCREEN session leak into TRAIN (constructions, names, wording)?
   Do the family definitions in `AUTHORING.md` match the TRAIN generator's mechanics
   closely enough that the trained targets are the screened targets, and differently
   enough that the screen is not a template match? Are contract tests complete against the
   contract wording (registration §10: every named operation covered, exact counts,
   grandfathering explicit)? Sample at least 12 screen slots across families and
   lifecycles and read them; report concrete defects with slot ids.
4. Counterfactual pairs: in `pairs_from_session`, are chosen/rejected the right gold under
   the right state for each lifecycle class (stable, replacement, scope, reinstatement) and
   for the irrelevant-history variant? Is the counterbalance actually realised
   (`precedent_state`)? Any pair where chosen and rejected are identical or where the
   rejected would pass the applicable contract?
5. Statistics and gate: is `mcnemar_exact` two-sided and exact; is the union-bound interval
   as registered; are gates 1–5 implemented as written in §7?
6. Compute plan against §8: measured ~15 s per request (prompt ≤ 2,560 tokens, ~200–300
   generated tokens) → 288 requests ≈ 1.2 h + 2 × 4 h training + reference scoring
   (~25 min inside cf's allocation) + timing pilot; the 1.5 factor applies to the pilot's
   measured seconds. Does it fit 16 GPU-h, and is anything missing from the accounting?
7. Anything else the owner is not thinking of that would make the screen's result
   uninterpretable.

Severity per finding: critical (invalidates the screen or biases an arm) / high / medium /
low, with a one-line fix. Write plainly; do not soften.
