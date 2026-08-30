codex
Not cleared: no critical implementation bug, but three HIGH record/verification issues need correction.

- **HIGH — G-W0b was not proven impossible.** The registered gate genuinely failed: reduction was 30.8%, below 50% ([w0_gates.py](/home/bmarti44/stencil-llm/scripts/w0_gates.py:106)). The sparse oracle-timed hand field is not an architectural ceiling: it acts only at recognized obligation moments, whereas the learned wave can improve every generation row. Moreover, the claimed 3.8% calculation has no committed artifact or code path; [w0-gates-w0-ce.json](/home/bmarti44/stencil-llm/results/qwen/w0-gates-w0-ce.json) contains no oracle measurement. Retract “provably impossible,” “oracle ceiling,” and “exceeds it 8x” in [WORKLOG.md](/home/bmarti44/stencil-llm/WORKLOG.md:1128).

- **HIGH — required per-cell G-W0c reporting is absent.** The contract requires active/cleared/stale/absent reporting ([INTERNAL-WAVE-PLAN.md](/home/bmarti44/stencil-llm/INTERNAL-WAVE-PLAN.md:109)), but [w0_gates.py](/home/bmarti44/stencil-llm/scripts/w0_gates.py:66) emits only aggregate work-level CE. Produce the missing deterministic breakdown from the frozen checkpoint before W1. No retraining is needed.

- **HIGH — “actuator change alone” is not identified by these arms.** Both W0 learned arms use the continuous actuator; there is no same-checkpoint discrete-actuator counterfactual in [w0_replay.py](/home/bmarti44/stencil-llm/scripts/w0_replay.py:68). The historical PRESS model differs in training data, objective, and controller. Rewrite [WORKLOG.md](/home/bmarti44/stencil-llm/WORKLOG.md:1147) to say the proxy objective succeeds when paired with the continuous actuator—not that actuator change alone caused the resurrection. Proving “alone” requires replaying the same proxy checkpoint through a preregistered discrete actuator.

Rulings:

1. **G-W0b amendment: RATIFIED, narrowly.** Preserve `G_W0b=false`; do not recalibrate a threshold post hoc. Retire it as a malformed, redundant diagnostic: despite being called “overfit-1,” the checkpoint was trained on all 40 seeds, while G-W0a, held G-W0c, and behavioral replay now directly establish connectivity and usable capacity. Disclose this as a post-result checkpoint amendment—not an impossible gate.

2. **Implementation audit: PASS otherwise.** `return_hidden=20` returns the layer-20 input, upstream of biased layers; row alignment is correct. The wave and proxy share initialization, features, module, A2 field equation, seeds, schedule, and inference actuator. Proxy BCE/span-CE labels and reductions match v3.1. Trunk parameters are frozen.

3. **Proxy/oracle identity: not verified.** Their aggregate counts are exactly equal, but [w0_replay.py](/home/bmarti44/stencil-llm/scripts/w0_replay.py:89) discards generated strings and writes no per-work hashes. I attempted the requested replay, but this review environment exposes no CUDA device. Add token/code SHA-256 values and equality counts; one-session equality supports only that session, while all 24 are needed for an all-dev identity claim.

4. **Causal gate: mechanically PASS, modest evidence.** Raw closure compares adherence gains: wave `47` versus proxy `42`, not `47` versus `38`; `38` is proxy dU after two broken works. Both satisfy validity. Therefore the registered training-objective test passes on this dev block. Honest headline: **“With the same continuous actuator, CE training added five adherence successes and incurred zero measured paired breakage versus the proxy-trained controller.”**

5. **W1: PROCEED** after committing the wording correction and missing per-cell artifact. Neither requires retraining W0.
