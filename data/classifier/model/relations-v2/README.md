# Relations v2 — 2026-09-06

**INELIGIBLE for the FOCUS-3 gate.** Seed 0 is preselected; seeds 1/2 are DEV
stability checks. Setup: 35/36 admissions, 11/12 transitions, 2 unauthorized
applications. No trunk/gate inference ran.

See [v6 RESULTS](../../../../results/quick-checks/focus3-gate/v6/RESULTS.md) and
[evaluation.json](evaluation.json). The three seed manifests preserve the
pre-evaluation training freeze; their zero evaluation counters describe that
freeze. The later authorized held-out-2 SECOND LOOK and CPU setup receipts live
in v6 and are linked/hash-bound by evaluation.json. No new generalization claim.

Each seed directory contains metadata, tokenizer, DEV logits and local encoder/
head safetensors. Safetensors are deliberately excluded from git; freeze.json
records their SHA-256. Training uses the pinned base BGE, three epochs, 654 steps.
The v6 runner loads seed0 explicitly and selects C/C' DEV thresholds plus the
positive-proposal admission bound. Historical default callers retain their
historical model/policy; no deployment was performed.
