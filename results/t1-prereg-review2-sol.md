codex
NOT CLEARED. Three HIGH ambiguities remain.

### HIGH — s0x2 pretest permits a predictably impossible certification

[t1-prereg-draft.md](/home/bmarti44/stencil-llm/results/t1-prereg-draft.md:27) allows only 80% overall assertion coverage and 60% per type. But every assertion miss is a certification failure, while block B passes only with `k <= 3/160`.

At the registered minimum, 20% missing means roughly 32 automatic failures before testing the selector. Replace the coverage gates with:

- train-hard: `48/48` assertion-hit, therefore `16/16` per type;
- calib-hard: `24/24` assertion-hit before component metrics;
- frozen old-policy pressure: at least `10/48` false-selection sessions.

If either assertion coverage or pressure fails, redesign and re-register s0x2 before training. The current draft specifies an action only for pressure failure.

### HIGH — the deployed decision rule remains undefined

The model has listwise logits, but [line 77](/home/bmarti44/stencil-llm/results/t1-prereg-draft.md:76) refers to an “above-threshold” selection without defining a threshold. Freeze the runner-compatible rule:

```text
best_candidate = argmax candidate logits
decision_score = logit(best_candidate) - logit(NULL)

decision_score > 0: return best_candidate
decision_score <= 0: return NULL
runner numeric threshold = 0
```

NULL therefore wins exact ties. Candidate-candidate ties also need a deterministic rule, such as first candidate order.

Also clarify:

- q, k, NULL head and temperature are all trainable;
- if the intended initial temperature is `T=1.0`, initialize  
  `t = softplus_inverse(1) ≈ 0.5413248546`, not `t=1.0`, which gives `T≈1.313`;
- the margin gate means the full registered `0.1` margin is satisfied, not merely a positive difference;
- freeze the exact recall floor as `0.41640866873065013`.

### HIGH — fallback routing and block consumption are ambiguous

[Lines 83–96](/home/bmarti44/stencil-llm/results/t1-prereg-draft.md:83) do not specify whether fallback follows an offline-gate failure, block-B failure, or behavioral mid-band result—and say block E certifies the fallback even when B was never touched.

Register one mechanical table:

- Pretest failure: redesign fixture; no training fallback.
- Initial component-gate failure: use the single 4× retrain. If it passes gates, certify it on still-untouched block B.
- Initial block-B certification failure: either close immediately or use the single fallback on block E—choose now.
- Initial block-B pass followed by safe behavioral closure in `[0.25, 0.50)`: use the single fallback and certify it on E before replay.
- Once the fallback is consumed, any later miss closes the line.

Everything else is repaired: R1 is honestly SKIPPED/UNTESTED, s0x2 does not leak values, trace-feature recomputation is executable, block C is explicitly retired, and the seed ranges do not collide.
