codex
NOT CLEARED.

### CRITICAL — The central causal control is invalid

The distillation gate at [INTERNAL-WAVE-PLAN.md:21](/home/bmarti44/stencil-llm/INTERNAL-WAVE-PLAN.md:21) does not test whether differentiable training mattered:

- W0’s gain is already a sigmoid of a linear `h20` head, so a thresholded `h20 → press` model can reproduce its binary timing by construction.
- Distillability after training does not show that label-based training could have learned the policy.
- The probe does not reproduce WHERE—the wave’s q/K field—so “substituted at replay” is undefined.
- The frozen T2b control was trained on a different, checker-bearing distribution; running it under `feedback_mode=none` is not a matched training-signal comparison.

Make distillation descriptive only. Add a matched control trained on the same 40 no-feedback prompts, same features/capacity/seeds, but with the closed proxy objective: timing BCE/CE plus authoritative-span classification. The differentiable-training claim requires the CE wave to beat this matched control on raw closure while both satisfy validity. Keep frozen T2b as a historical baseline.

### CRITICAL — Parameterization B disconnects the gain head

At [line 66](/home/bmarti44/stencil-llm/INTERNAL-WAVE-PLAN.md:66), `b_i = beta_max * sigmoid(e_i)` contains no `g_t`. If B is selected:

- `w_g` is unused;
- its L1 penalty and histograms are meaningless;
- G-W0a’s required nonzero `w_g` gradient is impossible.

Define B explicitly, e.g. `b_ti = g_t * sigmoid(e_ti)`, with `g_t = beta_max·sigmoid(gain_logit_t)`, and use that identical equation in W0.05 oracle fields and training.

### HIGH — WHEN and WHERE ablations are still nonbinding

At [lines 109–115](/home/bmarti44/stencil-llm/INTERNAL-WAVE-PLAN.md:109), only the uniform-field ablation gates progress. K permutation could preserve 100% of the gain—showing WHERE is decorative—or gain permutation could preserve it—showing WHEN is decorative—and the model could still win.

Require each of K permutation, gain permutation, and uniform field to reproduce less than 90% of the held CE gain. Otherwise report the corresponding component as decorative and do not claim an internal timing/address wave.

### HIGH — The frozen field equation and initialization remain ambiguous

[Lines 83–86](/home/bmarti44/stencil-llm/INTERNAL-WAVE-PLAN.md:83) leave two outcome-changing ambiguities:

- “temperature 8.0” does not say `e=8·cos(q,k)` or `e=cos(q,k)/8`; the latter is nearly uniform.
- “w_g zero-init so gain starts at beta/2” contradicts the immediately following weight-zero/bias-`−2` initialization, which starts at `0.119·beta`.

Freeze the literal equations. W0.05 must also specify its 12 seed IDs, oracle inside/outside logits, and a numerical wrong-position degradation floor; “measurable” is gameable.

### HIGH — W1’s training and gate contract remains incomplete

[Lines 132–149](/home/bmarti44/stencil-llm/INTERNAL-WAVE-PLAN.md:132) do not define:

- whether q/g uses predecessor state or the just-updated state;
- full BPTT versus detachment across work turns;
- when optimizer steps occur relative to session state;
- W1 connectivity/held-CE gates;
- a W1 dev headroom precondition or reserve action;
- how much replay-adherence degradation the temporal probe requires.

Register score-before-write or score-after-write explicitly, whole-session BPTT semantics, and an adherence degradation floor such as ≥10% of the wave’s lift. Add W1 headroom ≥0.10 with a named reserve block or an immediate inconclusive close.

The W0 redraw also needs its missing terminal branch: a second headroom miss closes inconclusively.

### HIGH — W2’s paired construction is impossible under the current prompt contract

[W2:153](/home/bmarti44/stencil-llm/INTERNAL-WAVE-PLAN.md:153) asks for identical visible text but different current authority histories. However [t2_sessions.py:284](/home/bmarti44/stencil-llm/src/stencil/t2_sessions.py:284) always reserializes the live authoritative ledger at the top of every prompt:

- different current authority ⇒ different visible text;
- identical current ledger ⇒ donor and recipient have the same correct governance, so the swap has no discriminating target.

State now that W2 requires a separately registered transplant fixture that presents an identical neutral candidate bank while withholding the current authority serialization. Otherwise W2 cannot isolate state from text.
