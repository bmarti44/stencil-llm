codex
CLEARED in substance. The redesign correctly separates policy error from fixture exposure: if the deployed timing head never presents a candidate, the selector cannot false-press.

Before training, register these exact edits:

- Supersede the old assertion-as-failure language in [PRESS-PLAN.md](/home/bmarti44/stencil-llm/PRESS-PLAN.md:143) and [t1-prereg-draft.md](/home/bmarti44/stencil-llm/results/t1-prereg-draft.md:27).
- Define `HAZARD_COVERAGE` exactly: a session counts once iff, at the targeted work, `timing_prob > tau`, predicted type equals the target type, at least one same-type candidate exists, and no same-type candidate is authoritative. Require `H >= 120/160`.
- Preserve the original pre-guard error definition: a session is false-selection-positive if any above-threshold non-NULL decision anywhere chooses a non-authoritative span. Thus block B passes only if `CP_upper(k_false,160) <= .05`—equivalently `k_false <= 3`—and `H >= 120`.
- If `H < 120`, label the result `INCONCLUSIVE—fixture coverage failure` and close without reseeding or claiming the policy failed.
- Retire the failed 48/48 and 24/24 pretest gates explicitly. Preserve and report the observed `38/48`, `17/24`, and pressure `30/48`; do not recollect them.
- Report `k_hazard/H` and its exact upper bound as a diagnostic. The registered ≤5% claim remains unconditional over deployed sessions; do not describe it as a ≤5% conditional hard-negative bound.

One wording correction: sessions without the target hazard test end-to-end false-selection risk, but they do not necessarily test hard-negative discrimination. Only the `H` exposed sessions establish that non-vacuity.

Confidence: high.
