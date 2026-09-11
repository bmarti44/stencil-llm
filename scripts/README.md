# scripts/ map (cleanup Phase 2, 2026-09-11)

Every script here is either LIVE (answers `--help` with exit 0; listed with the result it produces) or a CLOSED-program script kept because a test, module or result file still references it (unreferenced closed scripts live in `archive/scripts/`, see its MAP.md). Closed scripts are not retrofitted with argparse: several are sealed one-shot jobs whose code hashes are stored in their result audits, so editing them would break those audits. Run them only from the tag `pre-cleanup-2026-09-11`.

## LIVE scripts (`--help` exit 0; 97)

| script | first docstring line |
|---|---|
| `adv_no_write_10k.py` | The 10k-token adversarial no-write measurement the goal-review registered |
| `b0_score_parity.py` | B0.3 four-metric aggregate parity (registered H1): our runner's |
| `b3_deficit_cal.py` | v4.5 tau calibration (ONE SHOT, registered): base + frozen grid |
| `bfcl_mt.py` | Minimal no-server BFCL V3 multi-turn runner for the hand-rolled Qwen trunk. |
| `bfcl_seal_index.py` | One-time authorized BFCL cohort byte-offset index builder (CPU only). |
| `check_cleanup_invariants.py` | Cleanup invariants: prove a behaviour-preserving cleanup changed no science output. |
| `clf_probe_check.py` | Re-run the 20-session classifier-selector probe with selectable eviction timing. |
| `coding_auto_reasoning.py` | Bounded automatic-focus reasoning pilot for two fresh coding projects. |
| `coding_competence_dev.py` | CPU validator and executable preflight for coding-competence DEV data. |
| `coding_competence_run.py` | Native-tool runtime for the coding-competence prerequisite screen. |
| `coding_self_cue_run.py` | Native-message 72-call runner for the same-response coding focus DEV screen. |
| `coding_worker_dev.py` | CPU-only validator and executable preflight for coding self-cue DEV data. |
| `composition_pilot.py` | DEV-only composition pilot. No evaluation episode construction or benchmark IO. |
| `composition_pilot5.py` | SLAB-2 DEV driver. CPU stubs and vLLM use the identical loop/executor path. |
| `composition_pilot5_screen.py` | Amendment-3 eight-lane screen; owned container, cooperative 900s budget. |
| `composition_pilot7.py` | User-scoped pilot orchestration; pinned science source, bounded owned server. |
| `composition_pilot8_driver.py` | SLAB-2 DEV driver. CPU stubs and vLLM use the identical loop/executor path. |
| `composition_pilot_audit.py` | Re-score saved DEV outputs and validate provenance on CPU; no trunk load. |
| `composition_pilot_report.py` | CPU-only report from same-run DEV journal; never reopens episode content. |
| `convert_gpt2.py` | One-time GPT-2 small weight download, conversion, and parity capture. |
| `convert_qwen3.py` | Convert Qwen3 dense HF checkpoints to the hand-rolled trunk format. |
| `e0_pilot.py` | EVF Phase E0 — the registered kill-fast pilot (EVF-PLAN.md). |
| `e2_multiif_eval.py` | Frozen one-shot E2 Multi-IF replayed-history evaluation. |
| `e2_multiif_own_history.py` | Secondary, policy-level own-history Multi-IF run after replay gate pass. |
| `e2_oracle.py` | THE DECISIVE WHEN TEST (Brian, 2026-09-01): the ORACLE-TIMING ceiling. |
| `exp_a_baseline_fight.py` | Experiment A: the wire vs the trivial baseline (pin/re-insert text). |
| `exp_a_external_log.py` | Experiment A variant: EXTERNAL-LEDGER baseline (every update retained and re-inserted regardless of visibility |
| `export_classifier_hf.py` | Export the registered sentence classifier (data/classifier/model/ft) to a Hub repo. |
| `external_baseline.py` | SLAB-2 external X baseline, R/N only. Default is offline projection. |
| `focus1.py` | FOCUS-1 v2 draft harness. All real model stages require registration/evidence. |
| `focus1_probe.py` | UNREGISTERED quick check 31; never an input to registered FOCUS-1 selection. |
| `focus2.py` | FOCUS-2d CLI. Import/help/prepare/analyze never construct a trunk. |
| `focus2_amendment2.py` | Cost-only adapter for the unchanged FOCUS-2c Amendment 1 science freeze. |
| `focus3_gate.py` | FOCUS-3 foreground feasibility gate. No fitting, masking or sealed inputs. |
| `focus_check32.py` | Unregistered check 32: fixed skill bank and deterministic external slot latch. |
| `focus_check32_kv.py` | Unregistered Q4: operand-free four-column KV extraction and retained episodes. |
| `focus_check34.py` | Unregistered check 34: actual cue-column transplant; user-turn stickiness. |
| `focus_check35.py` | Disclosed check 35: retained cue transplant, recent positions, answer eviction. |
| `focus_check36.py` | Disclosed check 36: replay check35 S1 histories and recompute downstream KV. |
| `focus_check37.py` | Check 37: preread synthetic assistant-history repair, no fitting. |
| `focus_check38.py` | Disclosed check 38: text-only role, recency, and demonstration separator. |
| `focus_check39.py` | Check 39: fresh paired eviction-repair rerun with prospective safety gates. |
| `focus_check40.py` | Disclosed, unregistered check 40. CPU preparation precedes idle-GPU execution. |
| `focus_check40b.py` | Minimal disclosed router-bias SET screen; no training or benchmark inputs. |
| `focus_check40c.py` | Check40c: frozen router direction, dose and first-token duration screen. |
| `focus_check40d.py` | Unregistered frozen-router retained-history control check; no fitting. |
| `focus_check40e.py` | Frozen check40e: router SET transfer to TypeScript and SQL, no fitting. |
| `focus_check40f.py` | Disclosed 40f: frozen router release with position-preserving answer masking. |
| `focus_check40g.py` | Disclosed check40g: same-harness generality controls, one model load. |
| `focus_check40h.py` | Check40h closure: frozen routing plus masking at every skill change. |
| `focus_check40i.py` | Check40i: fresh-seed primary Z closure, reusing frozen check40h machinery. |
| `focus_check40j.py` | Check40j: fixed rendering-by-router screen, retained OFF imitation histories. |
| `focus_check40k.py` | Fresh authored programming competence: frozen JS router additivity, check40k. |
| `focus_check40l.py` | Check40l: fixed dev-derived competence router direction, two doses. |
| `focus_check41.py` | Unregistered check 41: dense Qwen3-4B programming-language neuron scaling. |
| `focus_check41b.py` | Check 41b: decision-position gradient readout and first-T-token MLP intervention. |
| `focus_check42.py` | Disclosed check 42: frozen FOCUS-2d bank, three fresh unmasked arms. |
| `focus_check43.py` | Disclosed check43: frozen SUM/PRODUCT router SET, bounded AST execution. |
| `focus_check43b.py` | Disclosed, bounded norm-matched SUM/PRODUCT routing follow-up. |
| `focus_check44.py` | One-shot check44 admission experiment; import is inert, no benchmark access. |
| `focus_check45.py` | Reproduce Check 45's R4 stop from the pilot README; stdlib/CPU only. |
| `focus_check49.py` | Frozen Check49 two-LoRA experiment. CPU prepare, then one cooperative GPU run. |
| `function_vectors.py` | GPU-deferred extraction and dev-grid selection for function vectors. |
| `g0_oracle.py` | G0 label-free counterfactual salience oracle and 30+30 pilot. |
| `gen_jax_fixtures.py` | Generate pinned LinOSS/D-LinOSS numerical-oracle fixtures once. |
| `larger_test.py` | Amendment 5 one-shot runner; no work at import, evaluation only after freeze. |
| `larger_test_v2.py` | Frozen Amendment 6 pilot/evaluation launcher. No import-time execution. |
| `ledger_eval.py` | LEDGER decider (LEDGER-PLAN.md, amended 2026-09-01 after |
| `maintenance_cold_diagnostic.py` | Four-call DEV diagnostic separating rule extraction from bookkeeping. |
| `maintenance_dev_check.py` | Sequential, DEV-only research driver for automatic register maintenance. |
| `make_data_samples.py` | Write small decoded examples from every Phase 1 task and placement. |
| `make_params.py` | Render the registered Phase 2 trainable-parameter audit. |
| `make_report.py` | Aggregate completed per-seed evaluations into the Phase 3 summary table. |
| `memorycode_screen.py` | Exp 3 MemoryCode-derived screen: items, auto adapter, GPU runs, summary. |
| `multiif_echo_only.py` | Exp 1: echo-only arms on a 128-source Multi-IF subset (REGISTRATION.md alongside). |
| `multiif_evict.py` | Registered Multi-IF post-development evaluation with pre-query KV eviction. |
| `para_probe.py` | (no docstring) |
| `prose_maintenance_dev.py` | Fixed 16-call DEV trial for automatic maintenance of plain prose notes. |
| `qwen_thinking_tool_smoke.py` | Bounded Qwen thinking plus native replace-function compatibility check. |
| `run_matrix.py` | Execute the registered 114-run Phase 3 matrix with exact resume semantics. |
| `sc1.py` | SC1 CPU validation and prospectively gated setup/final execution. |
| `slab2_v2_audit.py` | CPU audit of saved scoped-run receipts through the frozen real consumer. |
| `source_interpreter_fit.py` | Run the one fixed full-FIT source-interpreter job under bounded supervision. |
| `source_interpreter_mechanics.py` | Run one bounded source-interpreter training-mechanics measurement. |
| `source_interpreter_semantic.py` | Prepare and run the fixed fresh source-interpreter semantic comparison. |
| `source_reader_dev.py` | Fixed 48-call DEV trial for an independent source-only rule reader. |
| `source_replay_qualification.py` | Run the bounded two-call native source-replay qualification. |
| `source_replay_screen.py` | Preflight or run the fixed four-project H/S/R source-replay screen. |
| `t0_matrix.py` | PRESS-PLAN T0.2: offline score-policy matrix over the T0.1 trace. |
| `threshold_sweep.py` | Commit-threshold calibration sweep on the noisy-teacher checkpoint (Exp B). |
| `timing_pilot.py` | Exp 0 timing and memory pilot: seconds/item, tok/s and peak memory at MAX context. |
| `train_relations.py` | FOCUS-3 pairwise relations, initialized ONLY from base BGE. |
| `verify_determinism.py` | Run the registered Phase 0 in-process determinism check. |
| `w0_gates.py` | G-W0b/c gates + binding ablation battery (INTERNAL-WAVE-PLAN v3/v3.1). |
| `w0_verify_refs.py` | W0.0 registered verification sweep: every train work's canonical |
| `w1_gates.py` | W1 gates (v3 W1 + v3.1 H2'): held CE (>= 10% improve) + the frozen |
| `w_screen.py` | Exp 2a: wave utilization screen on fresh episodes (plan/BACK-ON-TRACK-PLAN.md). |

## Closed-program scripts kept for references (57)

| script | why `--help` does not apply |
|---|---|
| `agentic_g1.py` | no argparse; runs its registered job when invoked (killed by the 60 s sweep timeout) |
| `agentic_g1b.py` | no argparse; runs its registered job when invoked (killed by the 60 s sweep timeout) |
| `audit_focus3_diag.py` | needs `python -m scripts.<name>` (imports the scripts package) |
| `audit_relations_v3.py` | needs `python -m scripts.<name>` (imports the scripts package) |
| `b0_timing.py` | no argparse; runs its registered job when invoked (killed by the 60 s sweep timeout) |
| `b0_timing_kv.py` | no argparse; runs its registered job when invoked (killed by the 60 s sweep timeout) |
| `b0_timing_long.py` | no argparse; runs its registered job when invoked (killed by the 60 s sweep timeout) |
| `b2_adjudicate.py` | resumes a finished registered run; no --help contract |
| `b2_gsm8k.py` | resumes a finished registered run; no --help contract |
| `b2_mmlu.py` | resumes a finished registered run; no --help contract |
| `b3_deficit_conf.py` | checks the GPU before parsing arguments |
| `b3_dev_gate.py` | no argparse; runs its registered job when invoked (killed by the 60 s sweep timeout) |
| `b3_train.py` | no argparse; runs its registered job when invoked (killed by the 60 s sweep timeout) |
| `b4_ifeval.py` | checks the GPU before parsing arguments |
| `b4_multiif.py` | checks the GPU before parsing arguments |
| `cue_mask_diag.py` | no argparse; runs its registered job when invoked (killed by the 60 s sweep timeout) |
| `evaluate_relations_heldout2.py` | needs `python -m scripts.<name>` (imports the scripts package) |
| `finetune_admission_v2.py` | needs `python -m scripts.<name>` (imports the scripts package) |
| `finetune_admission_v3.py` | needs `python -m scripts.<name>` (imports the scripts package) |
| `focus3_gate_diag.py` | needs `python -m scripts.<name>` (imports the scripts package) |
| `focus3_gate_v3.py` | needs `python -m scripts.<name>` (imports the scripts package) |
| `focus3_gate_v4.py` | needs `python -m scripts.<name>` (imports the scripts package) |
| `focus3_gate_v5.py` | needs `python -m scripts.<name>` (imports the scripts package) |
| `focus3_gate_v6.py` | needs `python -m scripts.<name>` (imports the scripts package) |
| `focus3_gate_v7.py` | needs `python -m scripts.<name>` (imports the scripts package) |
| `focus3_gate_v8.py` | needs `python -m scripts.<name>` (imports the scripts package) |
| `focus_check44b.py` | needs `python -m scripts.<name>` (imports the scripts package) |
| `focus_check44c.py` | needs `python -m scripts.<name>` (imports the scripts package) |
| `g0_certify.py` | sealed one-shot job: refuses to start twice by design |
| `ledger_kv_probe.py` | checks the GPU before parsing arguments |
| `oracle_inject_diag.py` | no argparse; runs its registered job when invoked (killed by the 60 s sweep timeout) |
| `qwen_oracle.py` | no argparse; runs its registered job when invoked (killed by the 60 s sweep timeout) |
| `qwen_p2_drift.py` | no argparse; runs its registered job when invoked (killed by the 60 s sweep timeout) |
| `relations_v3.py` | needs `python -m scripts.<name>` (imports the scripts package) |
| `run_gpt2_arms.py` | no argparse; runs its registered job when invoked (killed by the 60 s sweep timeout) |
| `selector_s0.py` | no argparse; runs its registered job when invoked (killed by the 60 s sweep timeout) |
| `selector_s1.py` | no argparse; runs its registered job when invoked (killed by the 60 s sweep timeout) |
| `selector_s3_final.py` | no argparse; runs its registered job when invoked (killed by the 60 s sweep timeout) |
| `t0_cost.py` | no argparse; runs its registered job when invoked (killed by the 60 s sweep timeout) |
| `t0_costb.py` | no argparse; runs its registered job when invoked (killed by the 60 s sweep timeout) |
| `t0_trace.py` | no argparse; runs its registered job when invoked (killed by the 60 s sweep timeout) |
| `t1_train.py` | no argparse; runs its registered job when invoked (killed by the 60 s sweep timeout) |
| `t2_shakeout.py` | no argparse; runs its registered job when invoked (killed by the 60 s sweep timeout) |
| `t2_train_selector.py` | no argparse; runs its registered job when invoked (killed by the 60 s sweep timeout) |
| `t2b_press_audit.py` | no argparse; runs its registered job when invoked (killed by the 60 s sweep timeout) |
| `timed_t1.py` | no argparse; runs its registered job when invoked (killed by the 60 s sweep timeout) |
| `w0_addenda.py` | no argparse; runs its registered job when invoked (killed by the 60 s sweep timeout) |
| `w0_ceiling.py` | no argparse; runs its registered job when invoked (killed by the 60 s sweep timeout) |
| `w0_replay.py` | no argparse; runs its registered job when invoked (killed by the 60 s sweep timeout) |
| `w0_train.py` | no argparse; runs its registered job when invoked (killed by the 60 s sweep timeout) |
| `w1_train.py` | no argparse; runs its registered job when invoked (killed by the 60 s sweep timeout) |
| `w3_calibrate.py` | no argparse; runs its registered job when invoked (killed by the 60 s sweep timeout) |
| `w3a.py` | sealed one-shot job: refuses to start twice by design |
| `w3a_audit.py` | no argparse; runs its registered job when invoked (killed by the 60 s sweep timeout) |
| `w3b.py` | no argparse; runs its registered job when invoked (killed by the 60 s sweep timeout) |
| `w_seal.py` | sealed one-shot job: refuses to start twice by design |
| `w_seal_audit.py` | no argparse; runs its registered job when invoked (killed by the 60 s sweep timeout) |

Plan-referenced scripts that still need the `--help` contract before their experiment runs: `w0_train.py` (Exp 2b: model load under `main()`, `SEED` env; done when Exp 2 is scheduled), `b2_gsm8k.py` / `b2_mmlu.py` (competence checks for any weight-path component; new registration).
