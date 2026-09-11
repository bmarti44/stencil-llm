# Archived scripts (cleanup Phase 2, 2026-09-11)

Scripts of closed programs, unreferenced by any test, script, module, README reproduce command, RESULTS.md or plan/BACK-ON-TRACK-PLAN.md at the time of archiving. Moved with `git mv` (history preserved); lint-fixed mechanically only; runnable from the tag `pre-cleanup-2026-09-11`.

| script | docstring (first line) | result / ledger reference |
|---|---|---|
| `audit_focus3_v8.py` | Independent saved-record accounting; no inference, fitting or bank reads. | results/quick-checks/focus3-gate/v8/independent-audit-method.md |
| `audit_relations_heldout2.py` | Audit saved held-out-2 records, without model loading or held-out input access. | none |
| `b0_identity.py` | B0.1 provenance + parity (BENCH-WAVE v2.2 criteria, frozen): | none |
| `b0_kv_drift.py` | Checkpoint-ii FINDING-5: committed per-step KV-vs-full drift | none |
| `b3_base_texts.py` | v4.3 base texts: the FROZEN trunk's own greedy responses to each | none |
| `b3_battery.py` | B3 gradient-connectivity battery (v4.1; sol checkpoint-iii | none |
| `cache_final_checks.py` | Closing checks on the cache-v8 checkpoint (sol deployment-ladder items): | none |
| `calibrate_relations.py` | Recompute/score DEV only; no held-out input option or evaluation path. | results/quick-checks/relations-retrain/historical-cpu-seed0/operating-point.json |
| `ctrb_smoke.py` | CTRB end-to-end plumbing smoke on 12 non-evaluation calibration rows. | none |
| `e2_fit_gate.py` | Fit and certify the fixed six-feature E2 hazard gate. | none |
| `e2_headroom_adjusted.py` | Re-derive within-turn, family/mix/length-adjusted Multi-IF aging headroom. | none |
| `e2_obligation_eval.py` | Multi-IF replayed-history evaluation of the OBLIGATION-STATE gate. | none |
| `e2_pre_eval_audit.py` | Synthetic holdout safe-dose and firing audit before Multi-IF contact. | none |
| `focus_check33.py` | Unregistered Q3: bounded replacement of the A-versus-B residual coordinate. | results/qwen/focus2/development/inputs-33.json |
| `oracle_wire_diag.py` | Sol diagnostic 5: can ANY wire state make the trained osc model emit the | none |
| `qwen3_parity_debug.py` | Locate Qwen3 parity drift by decoder layer and residual sub-step. | none |
| `qwen_p1_micro.py` | P1 microfit: q3-api-micro (QWEN-PLAN Run 1). | none |
| `qwen_upper_bound.py` | P0 admission: with the task state fully VISIBLE, frozen Qwen3-1.7B must | none |
| `reconcile_relations.py` | Reproduce the 2026-09-05 development-only relation audit reconciliation. | none |
| `report_focus3_diag.py` | Write descriptive diagnostic reports from saved records, without inference. | results/quick-checks/focus3-gate/diag/validation.json |
| `selector_s2.py` | S2 registered run: learned contentless selector (SELECTOR-PLAN Amendment 1). | none |
| `selector_s3_a0.py` | S3-A0 scale admission (Amendment 2): base vs FULL-LEDGER re-insertion at | none |
| `selector_s3_a1.py` | S1 registered oracle-spotlight run (SELECTOR-PLAN Amendment 1). | none |
| `selector_s3_a2.py` | S3-A2 registered run (N*=32): learned contentless selector (SELECTOR-PLAN Amendment 1). | none |
| `slab2_v2_report.py` | Descriptive report from audited frozen records; no inference or gate edits. | results/larger-test-v2/pin-verification.json |
| `t0_reactive.py` | PRESS-PLAN T0.5: event-triggered (reactive) pressing baseline. | none |
| `t1_collect.py` | T1 prereg v3: train-hard/calib-hard collection + R2-PRETEST. | none |
| `t2_bakeoff.py` | T2 controller-state bakeoff (t2t3 prereg v3.1; frozen contract). | none |
| `t2_hash_audit.py` | CONTRACT v3 registered post-build pre-run hash audit. | none |
| `t2_recalibrate.py` | Fix theta calibration: theta = max(abstain score) + eps (zero false press | none |
| `timed_t0.py` | T0 (TIMED-SELECTOR-PLAN): oracle confirmation under honest instruments. | none |
| `timed_t1_completion.py` | T1 (TIMED-SELECTOR-PLAN): learned timing + learned address. | none |
