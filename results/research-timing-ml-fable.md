# ML research — when-to-intervene for the press decision (fable, 2026-08-30)

Lane: selective prediction / contrastive near-duplicates / conditional
steering / routers-gates / RL + try-then-revert. Full citations at end.

## 1. Selective prediction / conformal risk control
- Conformal Risk Control (Angelopoulos et al., ICLR 2024, arXiv:2208.02814)
  + Risk-Controlling Prediction Sets (JACM 2021): pick threshold lambda on
  calib so E[loss] <= alpha, finite-sample, no retraining. Our
  zero-false-press rule is the degenerate alpha=0 target — with lookalike
  distractors the only feasible lambda is "never press" (observed).
  Choose alpha in {0.5,1,2,5}% or a weighted loss; measure the harm of a
  false press directly (press a WRONG span, score adherence delta) to set
  the cost ratio empirically instead of assuming infinity.
- Learn then Test (arXiv:2110.01052): joint calibration of
  (tau_timing, tau_live) as multiple hypothesis testing over a grid —
  composing two independently-calibrated thresholds is what killed our
  abstain rule.
- SelectiveNet (ICML 2019, arXiv:1901.09192): post-hoc thresholds on a
  score never trained for rejection are dominated by a selection head
  trained with a coverage-constrained objective. Our max-score measures
  address sharpness, which lookalikes share by construction.
- Conformal abstention for LLMs (arXiv:2405.01563), conformal factuality
  (arXiv:2402.10978), Fast-yet-Safe early exit (NeurIPS 2024,
  arXiv:2405.20915): per-token intervention decisions calibrated against
  a SEQUENCE-level risk — legitimizes calibrating directly on
  session-level adherence delta.

## 2. Contrastive discrimination of live vs quoted (format-identical)
- RocketQA (NAACL 2021, arXiv:2010.08191) + ANCE (ICLR 2021,
  arXiv:2007.00808): mine hard negatives from the model's own top-scoring
  mistakes; denoise with a cross-attention judge. Key structural lesson:
  a bi-encoder score (our query-key max) has a ceiling on
  near-duplicates; liveness is a property of span+CONTEXT (supersession
  markers, quote fences, turn boundaries), so any span-only score fails
  at any threshold. Build a probe over span + pooled context (or
  span-to-context attention pattern).
- Hard-negative contrastive (ICLR 2021 arXiv:2010.04592; FaceNet
  semi-hard triplets): fine-tune only a low-rank projection of the
  address space with triplet margin on mined (anchor=query state,
  pos=live span keys, neg=quoted lookalike keys); rerun the SAME
  threshold machinery on projected scores. Metric: live/quoted d-prime
  before/after.
- Attention Tracker (NAACL Findings 2025, arXiv:2411.00348) — the free
  lunch: prompt-injection detection via the "distraction effect" — in
  specific important heads, last-token attention mass shifts from live to
  competing instruction. Evidence liveness is ALREADY linearized in
  head-selective attention mass, training-free. Replicate the head scan
  on Qwen3-1.7B from cached logs; liveness score = summed mass over top-k
  heads. Corroboration: Instruction Hierarchy (arXiv:2404.13208),
  Instructional Segment Embedding (ICLR 2025, arXiv:2410.09102).

## 3. Conditional activation steering
- CAST (ICLR 2025, arXiv:2409.05907): separate CONDITION vector from
  BEHAVIOR vector; steer only when activation projection crosses a
  threshold; layer+threshold by F1 grid search (NOT zero-FP
  calibration). Direct blueprint for the press condition.
- ITI (NeurIPS 2023, arXiv:2306.03341): probe every head, intervene only
  in top-K — head-sparse pressing may reduce collateral damage, raising
  the tolerable false-press budget from the other side.
- Guiding Giants (arXiv:2505.20309): tiny controller emits continuous
  per-token steering strength — soft press strength s in [0,1] instead of
  binary press x binary abstain.

## 4. Routers and gates as templates
- CALM (NeurIPS 2022, arXiv:2207.07061): per-token gate calibrated via
  LTT against a sequence-level quality constraint; decaying threshold
  along the sequence -> schedule-aware press threshold (lower right after
  an instruction is issued).
- Expert-Choice Routing (NeurIPS 2022, arXiv:2202.09368) — the
  reframing: our abstain pathology is a load-balance failure (gate sends
  zero traffic). Invert: per instruction lifetime, a press BUDGET of k;
  press the k highest-RANKED moments. Ranking is robust to score
  miscalibration; the max-score may rank the true moment first even when
  it can't separate live/quoted absolutely. Zero-training eval on cached
  logs: top-1/top-3 agreement with oracle moments.
- Speculative decoding acceptance rules (arXiv:2211.17192, Medusa
  arXiv:2401.10774, lossy verification arXiv:2607.26627): the field
  never aims for zero errors — choose a distortion budget with
  analyzable failure modes; press on a likelihood RATIO
  p_live/p_quoted, not a single-score threshold.

## 5. RL/bandit timing and try-then-revert
- Options framework (Sutton-Precup-Singh 1999), Option-Critic (AAAI
  2017, arXiv:1609.05140), off-policy termination (arXiv:1711.03817):
  press-until-release is an option; termination collapse matches our
  abstain collapse; deliberation cost = principled press budget.
  Practical first step is a contextual-bandit reduction: at each
  timing-head moment, run BOTH continuations (deterministic, fixed
  horizon), fit a reward model over layer-20 features — directly tests
  whether press-advantage is decodable at all. Also: Timing is
  Everything (arXiv:2205.15953), budgeted acting with regret guarantees.
- Backtracking decoding (arXiv:2409.14586, arXiv:2503.08919, ROCODE
  arXiv:2411.07112, imperfect verifiers arXiv:2510.03149): press
  optimistically, fork pressed/unpressed from the same KV checkpoint,
  keep the continuation the deterministic checker scores higher, roll
  back the other. ~2x decode only at press moments. Dissolves
  zero-false-press from a third direction AND manufactures perfect
  per-moment press-advantage labels — a label factory for every learned
  approach above.

## Ranked top-3 by information per GPU-hour
1. Attention-mass liveness head-scan + per-instruction budgeted ranking
   (2c + 4b): near-zero GPU; decisive either way; training-free
   controller candidate if separation exists.
2. CRC/LTT recalibration at a nonzero false-press budget + empirical
   false-press cost (1 + CALM): a few GPU-hours; reshapes the objective
   for all subsequent work.
3. Fork-and-judge with KV rollback (5b): ~10-20 GPU-h pilot; immediately
   deployable policy needing no liveness discrimination + the label
   dataset the contrastive/RL approaches require.
