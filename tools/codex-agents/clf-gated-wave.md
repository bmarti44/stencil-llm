# Brief: clf-gated-wave — Brian's proposal as a probe arm: boost ONLY the classifier-selected instructions, ONLY when the model's attention to them is deficient

## Objective
Brian (2026-09-03): "what if the boost was only on at the moment that it needed it? and the classifier is what
tells us whether or not it should be on, and how much, per each saved instruction?" Prior record: an always-on
attention bias degenerates at every dose (H1 wave arms, wave_kill_rule); a deficit-triggered wave (bias only when
per-step attention mass to the span falls below tau, capped at b_max; src/stencil/qwen3.py deficit_gate) did not
degenerate but was net ~0 (sol: 15 repairs / 12 regressions; oracle WHEN-chooser ceiling +7.5). Untested: the
combination — spans = the selector-v2 classifier's picks, gate = deficit, per-span amplitude = f(classifier
confidence). Add it to the corrected-ordering probe (scripts/clf_probe_check.py, eviction pre-query) as arms:
  clf_pinned_wave     : pins as in clf_pinned + deficit-gated bias on the pinned columns, b_max = registered
                        calibration value (read it from results/qwen/b3-deficit-cal.json; do not re-tune), tau likewise
  clf_pinned_wave_conf: same, with per-span b_max scaled by the classifier's P(keep) (linear: b_max * (p-0.5)/0.5)
  clf_pinned_echo_wave: pins + echo + the gated bias (does the wave add anything on top of re-injection?)
Keep all existing arms so the comparison is on identical context ids and the same run. Degeneracy/truncation/
timeout/invalid counts per arm as registered (wave_kill_rule: degenerate > 2/20 kills the arm).
Score with the FINAL selector scores (results/quick-checks/clf_scores_final_s0.json). Deterministic battery before
the probe (CPU with a stub trunk where possible; GPU parts only when the GPU is idle — it is BUSY with the 909 run,
so mark GPU tests skipped-with-reason and do NOT run the probe; the orchestrator runs it after the 909):
zero-deficit -> bitwise-identical logits to clf_pinned; forced deficit -> finite nonzero bias capped at b_max;
confidence scaling monotone; echo+wave arm evicts before the current-turn prefill like every other arm.
NEVER read data/bench/ifeval_input_data.jsonl. Never modify data/bench/*.

## Allowlist
See clf-gated-wave.allow.

## Tests first (TDD, rule 1)
RED first for the three arms' plumbing and the battery. Run ONLY tests/test_clf_probe_check*.py (create) +
tests/test_multiif_evict.py. DO NOT run the full suite.

## GPU policy
GPU is busy (the registered 909 run); do not launch model processes; skip GPU tests with a reason; never wait on
a lock; never signal any process; foreground only.

## Acceptance
CPU tests green; ruff clean; the probe command line to run later written in WORKLOG; commit EARLY.

## Ledger handoff
Append to WORKLOG.md: arms added, tau/b_max values read from the calibration file (with sha), battery results,
the exact probe command for the orchestrator.
