# Coder task for gpt-6-astra: build the FOCUS-3 feasibility gate — classifier-driven register vs oracle (2026-09-06)

Repo /home/bmarti44/stencil-llm. CPU-only build now (the GPU runs checks 43b/40f via a chain; your GPU stage waits for
an empty compute-process list and no RUNNING.flag under results/quick-checks/*; write results/quick-checks/focus3-gate/
RUNNING.flag while you hold it; never signal anything).
Design: results/focus3-design-astra.md section 5 as amended by results/focus3-design-review-fable.md (D2 register-
agreement endpoint; D3 pair unit = (rule, candidate span); D4 fail-safe qualification; D5 un-release flagged and read
separately) and by the confirmed ship rule (results/check42-review-fable.md item 8; memory: register + every-request
rendering of live task rules; format constraints rendered only in requests of the kind they govern; NO masking in the
ship path). Classifier: data/classifier/model/relations (seed 0, three-epoch GPU model; frozen thresholds S/C/Cm/R =
0.94/0.50/0.50/0.50; held-out-2 operating accuracy 94.4% — results/relations-classifier-report.md, commit 952079b8);
admission of NEW rules via the existing rule/fact head (data/classifier/model/ft) with the disclosed-influence caveat.
Trunk: Qwen3-4B (dense; hf_compatible), 64-128-token caps, greedy.
Build src/stencil/focus3.py + scripts/focus3_gate.py + tests/test_focus3_gate.py:
- REGISTER runtime: rule table (id, text, key, scope, version, status, provenance turn); per user message: candidate
  spans (sentence split) x live rules -> classifier relations (fail-safe: below threshold = none); deterministic
  precedence (same key + overlapping scope, later version wins; user-global survives task switches; tool/assistant
  prose never updates); admission of new rules (rule head); render the live task rules into EVERY task request
  (format constraints only into requests of their kind). No masking. Provenance tags recorded but unused.
- ORACLE runtime: same renderer driven by the script's ground-truth events.
- EPISODES: 64 fresh synthetic episodes (seed 30301; 16 each: override / cancel / complete-and-move-on / switch-and-
  return with a persistent global rule), 12-24 turns, complete user+assistant pairs, executable checkers reusing the
  FOCUS-2/SC1 checker primitives (sort/format/tag families are fine), plus 16 setup episodes for competence/timing.
  Every episode has at least one hard "none" message (quote/hypothetical/tool claim) so false retirements are
  measurable.
- ARMS: classifier-driven register (C), oracle register (O), none (N: no register, no rendering), text-restate-every-
  request without a register (T: renders ALL rules ever stated, superseded included — the naive baseline).
- ENDPOINTS (write the reading BEFORE running): stale-rule executions, false retirements, final-task success, breakage;
  REGISTER AGREEMENT: C's rendered live set equals O's on >= 48/64 episodes and >= 12/16 per family, zero
  contradictory recaps; PASS = C within 4/64 of O on stale-rule executions and final success, false retirements
  <= 2/64, breakage <= 2/64, and C beats T on stale executions; report un-release (switch-back) separately.
- Cost: project first; cap 3 GPU-h; scale to 48 episodes if needed (recorded before running).
CPU tests: register precedence, fail-safe none, renderer placement rule, oracle/classifier parity on a scripted
episode, endpoint scoring, agreement metric. Run tests/test_focus3_gate.py + tests/test_eval_data_separation.py +
tests/test_sealed_guard.py; ruff clean. Then the GPU stage (setup -> gate) when allowed. Outputs under
results/quick-checks/focus3-gate/ (README with pre-written reading, summary.json, records, register traces per episode);
item "FOCUS-3 gate" in results/quick-checks/README.md (6 lines); WORKLOG entry (<= 8 lines). Commit code/tests/results
(git add -f) with explicit pathspecs; no push. Foreground only; never terminate or signal any process; never read the
sealed IFEval input file or the sealed BFCL cohort contents; nothing fit or trained.
