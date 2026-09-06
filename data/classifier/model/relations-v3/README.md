# Relations v3 — 2026-09-06 (NO-GO; v2 stays)

Fit-on = exact v2 patched Kimi relations/transitions + four enrich sets + audited
Opus-patched Kimi overrides. Calibrated-on = scenario-disjoint DEV only. Evaluated-on
= fresh Fable held-out-3 once after committed checkpoint/policy/evaluator freeze;
held-out-2 is a secondary historical re-look. No benchmark inputs/responses.
The inherited 90 Astra2 evaluation-derived relatives remain disclosed; this is
not a clean unseen-runtime-idiom training lineage. Override audit indices
178/186/291/415/417/877/945 and their connected groups are fit-only, never DEV.

Recipe: [v2 README](../relations-v2/README.md) and
[same v2 fit/calibrate implementation](../../../../scripts/focus3_gate_v6.py).
Pinned BAAI/bge-small-en-v1.5 revision 5c38ec7c405ec4b44b94cc5a9bb96e735b38267a;
three epochs, seeds 0/1/2, seed0 preselected; batch32, AdamW lr3e-5/weight decay.01,
CLS+role one-hot, dropout.1, weighted five-class cross entropy, gradient clipping,
6% warmup/linear decay, 512-token overflow abstention. No seed selection.
Primary C: lowest per-class cutoff .50:.01:.98 with <=5% empirical DEV-none FP;
unsupported classes disabled at1.01. C' retained only as v2 DEV metadata; it cannot
rescue the held-out reading. Final epoch only; no early stopping on scores.

GO iff held-out-3 supersedes recall >=90%, overall accuracy >=94%, and every
label F1 >= v2 held-out-2 C F1 minus .03; otherwise NO-GO and v2 stays.
F1 baseline derives from committed v6 second-look records. Bounds are two-sided
95% equal-tailed Clopper-Pearson on supersedes rows, descriptive under scenario
clustering. The runtime diagnostic uses the exact v2 runtime source and original
admission head, swapping only the relation model/C thresholds, all96 SETUP turns
containing12 transitions. It does not authorize the full gate.

[Recipe, split IDs, source hashes and runtime snapshot](../../../../results/quick-checks/relations-v3/)
are committed before fitting; checkpoint hashes/policy/evaluator are committed
before any held-out-3 read. Safetensors stay local, out of git. Foreground only,
1800-second GPU cap, coordination flag, no signals or push.

## Completed result

NO-GO: accuracy 87.05% < 94%, supersedes recall 73.26% < 90%; none, supersedes and completes F1 also fail their registered floors. V2 stays.

Accuracy **87.05%** (390/448).

| Label | Support | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| none | 133 | 75.00% | 92.48% | 82.83% |
| supersedes | 172 | 98.44% | 73.26% | 84.00% |
| cancels | 51 | 86.21% | 98.04% | 91.74% |
| completes | 41 | 90.91% | 97.56% | 94.12% |
| reinstates | 51 | 94.44% | 100.00% | 97.14% |

Confusion: gold rows / predicted columns, none/supersedes/cancels/completes/reinstates.
```text
123   2   1   4   3
 39 126   7   0   0
  1   0  50   0   0
  1   0   0  40   0
  0   0   0   0  51
```
Supersedes recall 95% Clopper–Pearson interval: **[65.98%, 79.71%]** (row-level, not cluster-adjusted).

[Full report](../../../../results/relations-classifier-report.md), [secondary metrics](heldout2-metrics.json), [fresh held-out records](heldout3-records.jsonl), [runtime/audit](../../../../results/quick-checks/relations-v3/audit.json).

Checkpoint SHA-256 (encoder / head), with per-seed full artifact hashes in each manifest:

- Seed 0: `f6200e807b422443b4740e4f93de6520b3043418fb968797403a95ca848c59a0` / `8b1020090d2b6147244ccc38a3fd7d0d5d28cf68298df060bd88e077a0e46958`.
- Seed 1: `f9c039432abbf2400cb8956007cc8dbc0bf50bb50760e918e30db34f5cdd4067` / `b210b72df22788284456ee06c34d9b4bdb0c604efa0fae5333b23e7996aa4c00`.
- Seed 2: `fbd2d74641e1be1bfd4de3d6cfbfbd69b84fa8a3a5685f47980b12e386823a00` / `f59c4e9f1dacdef08e55d41aac3396b4c2f4db459d42214c4155768a119d849c`.

Checkpoint/policy/evaluator freeze commit: `e8c00361`; recipe: `6809791f`.
The seed manifests and their zero held-out counters describe the pre-evaluation
freeze. [evaluation.json](evaluation.json) records the subsequent one-pass outcomes;
no model or policy changed afterward. DEV arrays and per-row records live in each
seed directory. GPU allocation 264.77/1800 seconds.
