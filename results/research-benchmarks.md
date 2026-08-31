# External-validation benchmark landscape (fable, 2026-08-30)

Flagship: IFEval (541 prompts, deterministic Python verifiers, 4
metrics; Qwen3-1.7B instruct NON-THINKING published: 68.2 strict-prompt
— arXiv 2505.09388 Table 20). Multi-turn anchor: Multi-IF (Qwen3-1.7B
non-thinking 44.7). NO train split exists — training data must be
synthetic constraints (AutoIF / IFTRAIN / Tulu-3-RLVR style), eval on
the untouched 541 + a held-out-taxonomy check (IFBench/Multi-IF).

CRITICAL caveats: published numbers are SAMPLED (temp 0.7/top-p 0.8/
presence 1.5), not greedy, and are for the post-trained chat model —
our greedy baseline must be measured ourselves; published = anchors
only. Verify which checkpoint our parity trunk matches (base vs
instruct) before any comparison claim.

Do-no-harm suite: MMLU-Redux (64.4 non-thinking), GSM8K (75.44 base
4-shot), MBPP/EvalPlus — run WITH the wave attached, claim = no
degradation (tests the gain head's off-distribution silence).

Harness: lm-eval-harness custom LM object passed directly to
simple_evaluate (model_guide.md); IFEval is generate_until-only
(loglikelihood stubs ok); task names ifeval / leaderboard_ifeval.

Effect-size anchors: published steering interventions on 2-8B models
cluster +3-7 IFEval points (Stolfo ICLR'25; ROAST +3.15 on Qwen3-8B;
Directer +6.5 attention-boosting — nearest mechanism). 1 prompt ~ 0.18
strict-prompt points; use paired tests, not thresholds.

Full citations in the session transcript / agent report.
