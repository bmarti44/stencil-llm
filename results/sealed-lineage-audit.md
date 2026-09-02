# Sealed-set lineage audit (2026-09-02, orchestrator, CPU-only)

Sealed file: data/bench/ifeval_input_data.jsonl, sha256 67ffeee0fcb87c31… (prefix; full hash pinned in
data/bench/pins-manifest.json). Registered use: single-shot, `scripts/b4_ifeval.py` only. Allowed
references (tests/test_sealed_guard.py allowlist): scripts/b4_ifeval.py, scripts/b0_score_parity.py,
tests/test_b3_gen.py, tests/test_ifeval_vendor.py, tests/test_sealed_guard.py.

## The breach
The SALIENCE-2 builder subagent (2026-09-01) trained a first-generation finder using the sealed
IFEval prompts as positives (WORKLOG "INVARIANT BREACH"). No model was run on the sealed file; the
prompts were read as text for finder fitting.

## What is downstream of the breach, and its status
| Artifact | Status |
|---|---|
| First-generation salience2 weights/probe (pre-refit) | Deleted from the tree; superseded by v2b commit 7673cdf. Not referenced by any script or test. |
| src/stencil/salience2_weights.json (sha 6bd0e8564b4b7192…) | v2b, refit with IFEval EXCLUDED (commit 7673cdf). Training corpus = data/b3 synthetic + Multi-IF train split; test_salience2.py asserts the IFEval-free manifest. |
| src/stencil/salience2_probe.npz (21d04595b0e41547…), salience2_hybrid.json (35373c1b90a2872e…) | Same refit lineage, IFEval-free. |
| results/qwen/ledger-kv-probe-v2/, ledger_eval.py slices | Use v2b finder only; no sealed-file reads (guard test passes; runner reads data/bench/multiif_en.jsonl). |
| results/qwen/b3-deficit-conf-s0* | Ran on data/b3/conf-v45.jsonl (synthetic), sha 7399e1b6…; no sealed read. |
| results/qwen/b4-ifeval-* (earlier BENCH-WAVE runs) | Registered single-shot uses of the sealed file, before the breach; untouched. |

## Verification performed
- `git grep -n ifeval_input_data` over src/ scripts/ tests/ deploy/ → only the allowlisted files.
- tests/test_sealed_guard.py passes (CPU).
- sha256 of the sealed file unchanged versus data/bench/pins-manifest.json.

## Conclusion
No live artifact depends on the breached fit. The sealed file has zero model runs beyond the
registered b4_ifeval single-shot. Residual risk: a future subagent reading the file as text — closed by
the isolation guards in the `isolation-and-gates` coder brief (hook + chmod/sha test).
