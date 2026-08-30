# INTERNAL-WAVE-PLAN v1 — the wave generated inside

Successor registered by PRESS-PLAN's close. Question: can a small
trained recurrent controller, running alongside the frozen trunk and
EMITTING the attention bias natively, govern generation — replacing the
external parser/checker clocking with an internal dynamical process?
This is the toy-phase result (a trained oscillator state carries and
transplants task identity) married to the scale result (attention-gain
presses select behavior on Qwen3-1.7B).

## The bar (quantified by PRESS-PLAN)

Structured pressing scores +14.5 val adherence at a ~1.7% paired
validity tax. The internal wave's WIN condition is closure >= 0.50 of
oracle headroom on dev under the T0.3 validity rule, with NO parser, NO
checker, and NO ledger-span lookup at inference — the controller sees
only what the trunk computes. Anything less that still beats base is a
partial result; the honest-map clause applies as always.

## Why this is not the closed discriminative line

PRESS-PLAN's lines made discrete, certifiable press DECISIONS trained
from labels. The wave differs on all three axes that mattered:
1. TRAINING SIGNAL: the attn_bias enters pre-softmax, so logits are
   differentiable w.r.t. the bias through the frozen trunk. The wave is
   trained by DIRECT CE — "raise the adherent continuation's
   probability at governed moments" — gradients flowing through the
   trunk into the controller. No proxy labels, no press classification.
2. OUTPUT FORM: a continuous bias FIELD over prompt positions (bounded
   gain), not a thresholded decision — no zero-one boundary to certify;
   behavioral outcomes + the validity rule judge it.
3. STATE: recurrent across steps and turns (W1), the toy-phase carrier
   at scale.

## Frozen seeds (fresh; nothing overlaps prior blocks)

- teacher trajectories / train: 13,400,000+i, i<48 (s0, dev split)
- overfit-sanity: the single seed 13,400,000
- dev replay: 13,450,000+i, i<24 (s0)
- reserve dev: 13,455,000+i, i<24
- sealed validation: 13,500,000+i, i<96 (only via fresh registration
  after a dev WIN; one named finalist)

## Ladder (short cycles; each rung gated before the next)

### W0 — differentiable-press feasibility (stateless wave)

Architecture (frozen at review; shape-TDD only before real data):
controller reads h20_t (last-position, layer 20, fp32) and per-position
prompt key features K (pooled h20 of the prompt, computed once per
work); emits bias row b_t = g_t * softmax(q_t K^T / sqrt(d)) where
q_t = W_q h20_t (64-d) and g_t = beta_max * sigmoid(w_g . h20_t),
beta_max = 4.0 (2x the proven press, bounded). Bias applied at layers
20-27 to the current row over PROMPT positions only. ~135k params.

Training: teacher-forced base trajectories from the train seeds (the
existing collection machinery); loss = CE toward the ADHERENT
continuation token at AST-labeled governed moments (prefix/doc/hint
value tokens), plus an L1 gain penalty (lambda = 0.01) everywhere —
press only where it pays. Deterministic gates before any replay:
- G-W0a gradient non-vacuity (exact-zero lesson): dLoss/d(controller
  params) nonzero on a fixture batch, and a deliberately detached bias
  must FAIL this test (the test proves it can catch vacuity);
- G-W0b overfit-1: on the single overfit seed, moment CE falls >= 50%
  from init (the mechanism can learn at all);
- G-W0c held-moment CE improvement >= 10% on train-seed holdout works.
Then ONE dev replay (arms: base, wave, oracle, structured==oracle,
reinsertion): closure and the T0.3 validity rule from raw paired
numerators, headroom >= 0.10 precondition (reserve re-draw rule as in
PRESS-PLAN). Decision table: closure >= 0.25 + validity pass -> W1;
[0.10, 0.25) + validity -> ONE architecture iteration (wider q/gain
heads, registered before results are seen further), re-judged once;
< 0.10 or validity fail -> W0 CLOSES (the differentiable press does
not work at this scale) and the program closes honestly.

### W1 — recurrence (the actual wave)

State s_t (64-d GRU over h20_t, reset per session, carried ACROSS
work turns within a session); q_t and g_t become functions of
[h20_t; s_t]. Same loss + gates (G-W1a/b/c mirror W0's). Additional
registered probe: state ablation — zeroing s_t at eval must degrade
moment CE by >= 10% relative, else the recurrence is decorative and W1
reports "stateless suffices" (that is a finding, not a failure).
Dev replay + the same table; WIN condition checked here (closure >=
0.50). Compaction-survival check: adherence on post-compaction works
reported separately (the wave must not depend on aged-out text).

### W2 — the transplant (the Miller signature, only after a W1 WIN)

The toy-phase demonstration at scale: swap s_t between two sessions
with different ledgers mid-generation; the wave's governance must
follow the STATE, not the text (registered metric: adherence to the
donor session's ledger types at matched moments, vs a shuffled-state
control). This is the "waves select circuits" claim on a real model;
registered fully before it runs, reviewed at checkpoint.

## Frozen rules

- Trunk bitwise frozen (existing test machinery); every claim's number
  recomputed from artifacts; press logs for every replay; no script
  imported by another does top-level work; pipefail in test chains.
- Reviews: sol + fable at (i) this plan, (ii) W0 results, (iii) W1
  results / any W2 registration, (iv) close. Loop while high/critical.
- Validity: the T0.3 rule (Delta-U >= 0.8 * adherence gain, > 0).
- Halting is success; every closed rung gets a WORKLOG autopsy.
- Sealed validation only via fresh registration after a dev WIN.
