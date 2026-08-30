codex
NOT CLEARED. Confidence: high.

The differentiable distinction is real but narrower than the plan claims: CE through the trunk provides utility-shaped gradients and removes the hard zero-false-press threshold. It does not remove the liveness problem—the gain head is still a soft WHEN classifier. Success would show that continuous, cost-sensitive control can solve what discrete certified selection could not.

## CRITICAL

1. **The proposed training target does not exist.**

[INTERNAL-WAVE-PLAN.md:56](/home/bmarti44/stencil-llm/INTERNAL-WAVE-PLAN.md:56) calls for CE toward an “adherent continuation” from base trajectories. Existing sessions contain requests, obligations, and scorers—not canonical adherent code—and base outputs can be wrong. Patching expected value tokens into a base continuation is incoherent for multi-token prefixes/docstrings.

Before W0, register a deterministic reference-code builder and verify every reference:

- parses and executes;
- satisfies every active obligation;
- does not accidentally satisfy cleared/stale obligations;
- records prompt length, target IDs, and prediction-row alignment.

Prefer ordinary CE over every canonical continuation token. If CE remains restricted to AST-labelled moments, the honest claim is “a supervised soft timing/address policy,” not internally discovered timing. “No proxy labels” at [line 28](/home/bmarti44/stencil-llm/INTERNAL-WAVE-PLAN.md:28) would be false.

2. **“NO checker” contradicts the runner.**

The win claim excludes checker access at [line 15](/home/bmarti44/stencil-llm/INTERNAL-WAVE-PLAN.md:15), but `run_session` inserts deterministic checker feedback into later prompts at [t2_runner.py:147](/home/bmarti44/stencil-llm/src/stencil/t2_runner.py:147) and [t2_runner.py:193](/home/bmarti44/stencil-llm/src/stencil/t2_runner.py:193). Because the controller consumes trunk states, it can read that feedback indirectly.

Add a frozen `feedback_mode="none"` used identically by train/base/wave/oracle/reinsertion, replacing environment turns with fixed neutral text or removing them. Otherwise narrow the claim to “no checker-triggered press,” which is materially weaker.

3. **W1 has no executable decision table.**

“Dev replay + the same table” at [INTERNAL-WAVE-PLAN.md:84](/home/bmarti44/stencil-llm/INTERNAL-WAVE-PLAN.md:84) self-loops: W0’s passing action is “proceed to W1.” It also leaves CE-gate failures, recurrence-decorative behavioral wins, and sealed-validation outcomes undefined.

Register:

- infrastructure-gradient failure → fix implementation; no scientific verdict;
- W0 CE-gate failure → W0 closes;
- W0 valid behavioral effect → W1;
- W1 closure ≥0.50 + validity + temporal-state probe → dev WIN;
- closure ≥0.50 but temporal probe fails → stateless result, no W2 claim;
- valid closure in `[0.25, 0.50)` → partial close;
- validity failure or closure `<0.25` → close;
- validation: headroom ≥0.10, closure ≥0.50, validity pass, no redraw.

Cut W0’s unspecified “wider q/gain” rescue. W1 is already the decision-relevant next architecture.

## HIGH

4. **The attention path is differentiable, but the tensor/API contract is missing.**

The hook is valid: bias is added before softmax at [qwen3.py:105](/home/bmarti44/stencil-llm/src/stencil/qwen3.py:105). But it accepts something broadcastable to `[B,16,T,T]`; a raw `[G,P]` field cannot be passed directly. Register either a padded `[B,1,T,T]` tensor or a rectangular row/column hook.

Also freeze:

- `K = h20[0:P]` from the exact post-substitution prompt;
- target token `j` uses bias/query row `j-1`;
- prompt columns are exactly `[0,P)`;
- one shared field is applied at layers 20–27;
- batch size 1 plus gradient accumulation unless padding masks are implemented;
- a layer-20 split/resume API, or disclose the roughly doubled lower-trunk pass.

Caching K once per work is sound because prompt states are causal and fixed during generation—but it must be recomputed after every prompt/feedback/compaction change.

At `T=2048`, one fp32 attention matrix is 256 MiB per layer/head bundle; eight layers are 2 GiB before saved-softmax/backward costs. The square bias itself is only 16 MiB and can be shared. Current frozen W0 fixtures are much shorter—measured prompt maximum 412 tokens, ≤532 with 120 generated tokens—so batch-1 is realistic. Register a maximum-length forward/backward peak-memory and timing smoke before training.

5. **The frozen architecture and parameter count disagree.**

The plan says approximately 135k parameters at [line 54](/home/bmarti44/stencil-llm/INTERNAL-WAVE-PLAN.md:54), but the committed controller has separate `W_q` and `W_k` at [wave.py:18](/home/bmarti44/stencil-llm/src/stencil/wave.py:18): exactly **264,321 parameters**.

More importantly, raw unnormalized q/k with default initialization can produce an initially saturated random softmax, while the total bias mass is always at most `g`. A diffuse field over hundreds of prompt tokens is therefore nearly inert; a saturated field points at one random token.

Freeze normalization, temperature, and initialization. The cheapest safe choice is normalized q/k with a registered temperature and a low-gain initialization.

6. **G-W0a’s current anti-vacuity test is invalid and red.**

[test_wave.py:26](/home/bmarti44/stencil-llm/tests/test_wave.py:26) backpropagates through `b.sum()`. Since `b = g·softmax(...)`, `b.sum() = g`; mathematically it has no q/k gradient. I ran the exact test: **1 failed, 4 passed**, failing on `W_q.weight`.

Replace it with:

- a weighted positional synthetic functional for shape-level q/k connectivity;
- the actual trunk CE-only loss—not CE+L1—for the real gate;
- finite, nonzero gradients separately for `W_q`, `W_k`, and `w_g`;
- nonzero `dCE/dbias`;
- detached bias must fail;
- zero field must be bitwise base-equivalent;
- wrong-position and correct-position fields must produce distinguishable logits.

L1 alone must not satisfy connectivity.

7. **`beta_max=4` is not justified, and it is not “2× the proven press.”**

Hard `b=4` was rejected by T0’s strict gate; it also reduced G1 validity. More fundamentally, the old press added beta to every selected-span token, whereas the new controller distributes total mass `g≤4` over the entire prompt. These doses are not comparable.

Before training, run a train-only deterministic oracle-field ceiling over `{2,4}` using the exact proposed field parameterization. Require correct-position benefit, wrong-position non-vacuity, and validity. Select the smallest passing ceiling. If the normalized-softmax field cannot reproduce useful oracle behavior, change the field parameterization before optimizing the controller.

8. **W0’s gates do not establish learned WHEN and WHERE.**

A 10% aggregate CE improvement can be driven by prefix tokens, an always-on prompt boost, or gain alone. Register token/session/type reductions and causal ablations:

- full field versus zero field;
- K-to-position permutation or uniform field at matched gain—tests WHERE;
- gain sequence permutation across generation rows—tests WHEN;
- active versus absent/cleared/stale-only hard-negative cells reported separately.

The falsifiable distinction from PRESS-PLAN is: the continuous controller passes behavioral validity despite nonzero low-level activation where the hard certified selector abstained. It is not “the liveness problem disappeared.”

9. **W1/W2 do not yet prove temporal state.**

Zeroing `s_t` is an out-of-distribution ablation and does not distinguish recurrence from a nonlinear transform of current `h20_t`. Freeze the update schedule—including whether new user/update tokens enter the state—and use a matched reset or predecessor-state permutation while preserving current `h20_t`. Require behavioral degradation as well as CE degradation.

W2’s proposed donor-ledger metric is presently impossible to interpret: donor state queries the recipient prompt keys and cannot emit donor content absent from that prompt. Use paired sessions with identical visible candidate text but different prior authority histories; compare own-state, donor-state, shuffled-state, and reset-state arms at identical moments. Otherwise a transplant cannot separate state from visible text.

10. **Training and multiplicity remain unfrozen.**

Register optimizer, LR, weight decay, epochs/steps, initialization seed, shuffle seed, batching/accumulation, checkpoint selection, exact L1 reduction, and a fixed train/held split—e.g. 40 training seeds and the final 8 of the 48 for G-W0c. Give W1 a fresh dev block or disclose repeated adaptive use. The current reserve block cannot simultaneously serve headroom redraw and an architecture rescue.

Also run `oracle` once; `structured==oracle` is an alias and does not justify a duplicate generation arm.
