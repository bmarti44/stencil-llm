SLAB-2 CPU audit and pilot-5 registration (2026-09-06)

SLAB-2 Amendment 1 — registered 2026-09-06 BEFORE implementation
Review: results/slab2-review-fable.md:33-166 (H1-H3, M4-M7).
Data lineage: fit-on=none; authored DEV development; evaluation grammar/seeds disjoint. No evaluation episode content inspected; regeneration/accounting automated with aggregate output only.
H1: parse before disk mutation; syntax attempts are executed+breakage, name file/line, retain last_parsable on disk; cross-file recovery must remain possible.
H2: reply cap 2048; every request and system use short one-line docstrings. Re-freeze same seeds and rerun full tokenizer accounting/context gate. Historical 577/1024 is reference size, NOT a model measurement.
H3: max_workers=4 in pilot and registered run. Each fixed concurrent group charges GPU-held wall / concurrently held lanes to each lane (including CPU preparation/checking while GPU held); per-arm mean is lane_seconds. Load charged once, then 1.25 reserve on projected lane allocations. Pilot records measured output tokens/lane by arm. CPU timings never qualify cost.
Pre-written projection formula: (output_tokens * size_factor / rate + calls * 0.8) / 3600; reserve x1.25; load separately once. Recompute these three rows from amended reference accounting before GPU: aggregate 24.7 tok/s reference; per-stream 11 tok/s reference (sequential sensitivity); aggregate 24.7 tok/s model-style x1.35 (assumption, not measurement).
M4: preserve RNG draws/seeds; swap delivery/format positions whenever needed so delivery completes strictly before format retirement. Require delivery opportunities in >=7/8 DEV and >=56/64 eval; format remains a floor-gated omission trait.
M5 bounded tolerances, labelled per reply: CRLF; leading/trailing prose outside exactly one triple-backtick fence; trailing trailer period; case-insensitive report/status; any unique task/status/delivery key order; blank lines before trailer; py/python/Python/bare tags; one leading <think></think> block. Unknown/duplicate keys, extra fences, other fences, misplaced/malformed trailers and other variants are categorized breakage.
M6: n_rounds in {16,12}, default 16. Fallback only if measured 16-round projection is (12,15]; >15 stop, <=12 retain 16. At 12 rounds retirement times are 6/7/8, reinstatement DEV9/eval10/11; task switches 2,4,5 (same RNG draws retained). Freeze both schedules now; fallback requires fresh complete 12-round DEV validation and cost <=12 before evaluation; never reduce arms.
M7: scripts/composition_pilot5.py drives loop.generate_once with vLLM adapter; captures DecodeResult.truncated in Executor and records, pending-floor raw records first, complete DEV T floor then rescore. CPU injected decoder smoke uses this exact path. No GPU execution in this fix pass.

Amendment 1 verification (CPU only)

72 episodes x 16 rounds x four arms = 4,608 real-loop reference stub calls. No model competence or measured GPU-cost claim. Evaluation generation/checking was automated; only aggregate counts and hashes were inspected.
Manifests freeze both 16- and 12-round schedules with the same seed namespaces. Both have delivery witness opportunities: DEV 11 in 8/8 episodes; eval 87 in 64/64. Format remains an omission trait gated by the actual DEV T floor.

| Arm | Max context | Registered input tokens | Registered output tokens | Reference output tokens/lane (eval) |
|---|---:|---:|---:|---:|
| R | 13,333 | 6,047,483 | 238,642 | 3,136–4,466 |
| N | 7,171 | 3,000,048 | 238,642 | 3,136–4,466 |
| T | 8,234 | 883,725 | 58,709 | 3,136–4,466 |
| O | 13,333 | 1,506,970 | 58,709 | 3,136–4,466 |

Context gate passes for all 288 lanes: maximum 13,333 + reserved reply 2,048 = 15,381 < 32,768. Registered totals use R/N x64 and frozen nested O/T x16; the audit covers all four arms in all 72 episodes.
Largest reference reply: 577 tokens against cap 2048. Historical 577/1024 was reference size, not model measurement or demonstrated model headroom.

Pre-written cost table for GPU checks 46–50 (frozen before any pilot-5 GPU execution): amended reference output 594,702 tokens, 2,560 calls, assumed 0.8 s/call TTFT. Input tokens are counted above; these sensitivity estimates do not model prefill separately. Add actual load hours once to the reserved column. Only measured four-worker lane allocations determine the 12 GPU-h gate.

| Scenario | Output factor | Hours | With x1.25 reserve (before load) | Cost-rule action at zero load |
|---|---:|---:|---:|---|
| aggregate reference (24.7 tok/s) | 1 | 7.256946 | 9.071182 | 16-round |
| per-stream reference (sequential sensitivity) (11 tok/s) | 1 | 15.586616 | 19.483270 | stop |
| aggregate model-style assumption (24.7 tok/s) | 1.35 | 9.597765 | 11.997207 | 16-round |

The x1.35 scenario leaves only about 10 seconds for load under 12 hours; rounded 12.0 must not decide the gate. No GPU projection is measured by this CPU pass.

Driver: scripts/composition_pilot5.py --cpu-stub --out /tmp/NEW-DIRECTORY; GPU owner instead supplies --model, --endpoint and measured --load-seconds for an already-held vLLM server. Four concurrent lanes, 8 DEV episodes in R/N/T plus O for directly measured O cost. Raw records retain pending-floor scores; freeze all 128 DEV T rows (96 for cost-selected fallback), then write separate scored records. Per-lane allocations and measured output tokens are in summary.json; CPU summaries have null GPU timing/projection. The driver never launches or terminates a server.

Pilot-5 science eligibility remains: complete DEV R/N/T, executed >=90%, caps <=2%, T floor >=50% per eligible trait, >=2 eligible kinds with retirement opportunities in >=2 DEV episodes, R final >=5/8, and measured registered cost <=12 GPU-h. A syntactically invalid file attempt counts executed+breakage but never reaches disk. O DEV lanes measure cost; they do not enter the pilot science gate. CPU reference compliance never freezes a model's floor.

Validation provenance: full requested selection (`CUDA_VISIBLE_DEVICES='' .venv/bin/python -m pytest -q tests/test_focus_*.py tests/test_no_side_effect_imports.py`) completed: 324 passed, 3 failed, 1 expected xfail (827.77 s). One new arithmetic test had been collected before its expected-value correction; the corrected arithmetic plus all five driver tests pass (6 passed). The other two failures are SLAB-1 test_manifest_hashes and test_dev_loop_dry_run: both reproduce unchanged on isolated pre-fix commit 8d02a037 (2 failed, 1.60 s), including prompt 981 vs frozen 879. No SLAB-1 science fixtures were re-frozen by this amendment. Full log: /tmp/slab2-amendment1-tests.log; isolated baseline log: /tmp/slab2-amendment1-baseline.log. Final SLAB-2/import suite result is recorded below.

Final validation: `CUDA_VISIBLE_DEVICES='' .venv/bin/python -m pytest -q tests/test_focus_slab2.py tests/test_focus_slab2_driver.py tests/test_no_side_effect_imports.py` — 110 passed, 1 expected xfail, 70.27 s. Current full-selection status after the correction: 325 passing, 2 confirmed pre-existing SLAB-1 fixture failures, 1 expected xfail. Ruff and whitespace checks pass; source/manifest/accounting hashes match. The 12-round CPU CLI smoke completed all 32 DEV lanes (384 calls), R final 8/8, with null GPU cost and no model eligibility. No GPU execution, process signalling, or push occurred.
