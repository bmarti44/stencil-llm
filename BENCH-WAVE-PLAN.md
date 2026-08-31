# BENCH-WAVE-PLAN v1 — the wave on real benchmarks

Brian's directive (2026-08-30): prove the wave mechanism generally with
real benchmarks, starting with IFEval, then the most relevant further
evaluations — improvement AND cross-benchmark generalization. Same
fast-iteration reviewer loop.

Grounding: results/internal-wave-report.md (sealed in-harness win;
clean-format win), results/research-benchmarks.md (landscape:
Qwen3-1.7B non-thinking IFEval 68.2 strict-prompt SAMPLED — anchors
only; no IFEval train split — training uses synthetic constraints;
notable steering deltas on 2-8B models: +3-7 points; 1 prompt ~ 0.18
strict-prompt points -> paired tests, not thresholds).

## B0 — infrastructure + identity (gates everything)

- B0.1 CHECKPOINT IDENTITY: verify which HF checkpoint our
  parity-proven qwen3-1.7b.pt matches (Qwen/Qwen3-1.7B instruct vs
  -Base) by config + a fresh logit-parity spot check; record. All
  baseline comparisons are scoped to that checkpoint.
- B0.2 IFEval RUNNER: vendor Google's rule-based verifiers (or
  lm-eval's ifeval task via a custom LM object exposing
  generate_until); OUR loop = Qwen3 chat template (non-thinking),
  greedy, max_new registered; deterministic end-to-end. TDD: verifier
  vendoring against 5 hand-built response/constraint fixtures;
  template round-trip test.
- B0.3 OWN BASELINE: base model on the 541 IFEval prompts, greedy;
  report all four metrics. This number (not the published sampled
  68.2) is the comparison root. One run, committed with per-prompt
  records FROM THE START (playbook lesson).

## B1 — zero-shot probe (Brian's instinct; exploratory, cheap)

Attach frozen w0-ce unchanged (K = prompt h20; automatic pressing) and
rerun B0.3's prompts. Report the delta with a paired McNemar
(prompt-level strict) — EXPLORATORY, no pass/fail gate; any signal is
information about transfer distance. Also record gain histograms (is
the gain head quiet off-distribution?).

## B2 — do-no-harm (the removability claim, tested externally)

With w0-ce attached: MMLU (loglikelihood, registered 2k-question
subset seeded), GSM8K (registered 200-item subset, greedy 4-shot).
Gate: paired degradation bounds — MMLU accuracy drop <= 0.5 points,
GSM8K drop <= 1.0 point (both directions reported). A gate FAIL is a
real finding about off-distribution gain firing, reported not hidden.

## B3 — the benchmark wave (the recipe on constraint-following)

Training data (fresh, synthetic; NO IFEval eval items): a registered
generator of verifiable-constraint prompts in the IFEval taxonomy
STYLE but with disjoint parameters/phrasings (AutoIF/IFTRAIN pattern):
N_train = 2,000 prompts x canonical adherent responses BUILT
programmatically (constraint types where a canonical response is
deterministically constructible AND verifiable: case, length ranges,
bullets/sections, keyword inclusion/exclusion, start/end phrases,
JSON). Every canonical response passes its own verifier (W0.0-style
zero-failure freeze). Training: the identical W0 recipe — CE through
the frozen trunk, A2 field over the INSTRUCTION span(s), same
optimizer/init/seeds, wave + matched proxy twin (same actuator, proxy
labels = instruction-span pointing + press-at-response-start) for the
causal comparison.
Gates before eval: G-W0a-style connectivity battery on the new data;
held-out synthetic constraint accuracy improvement; ablation battery
(K-perm / gain-perm / uniform at matched gain, binding <90% each).

## B4 — sealed benchmark evaluation

ONE sealed run each (fail-closed, pinned hashes, per-prompt records in
the artifact from the start):
- IFEval 541 (untouched by anything upstream): arms base / wave /
  proxy. PRIMARY: prompt-level strict accuracy, paired McNemar
  one-sided p < 0.05 AND delta >= +2.0 points (>= ~11 prompts; below
  the +3-7 published steering band but above noise). Causal: wave >
  proxy.
- Multi-IF (English subset, registered size): the long-horizon claim;
  same metrics; EXPLORATORY gate (report, no pass/fail — first
  multi-turn external exposure).
- Do-no-harm rerun WITH the B3 wave (same B2 bounds — now a real gate).
Decision table: IFEval PASS + do-no-harm PASS -> the wave mechanism is
externally validated on its first real benchmark; either FAIL -> honest
negative with autopsy; Multi-IF informs the NEXT benchmark's
registration (cross-benchmark generalization = a fresh checkpoint-iii
registration naming benchmark #3 by what B4 reveals, e.g. FollowBench/
ComplexBench/IFBench for taxonomy hold-out, or RULER-style long-context
if Multi-IF shows length sensitivity).

## Frozen rules

Seeds: synthetic-train generator seed 0; subsets drawn with registered
seed 1; one sealed attempt per B4 item, no redraws. TDD for verifiers,
template, generator, canonical builders. Reviews: (i) this plan,
(ii) B0 results + B3 preregistration details, (iii) pre-B4, (iv) close.
Playbook governs (pipefail, consumer-path tests, per-work records in
sealed artifacts, no top-level work in imported scripts). Every claim
scoped to the verified checkpoint identity and greedy decoding.
