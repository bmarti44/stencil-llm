# Relations v3 — 2026-09-06 (pre-evaluation registration)

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
