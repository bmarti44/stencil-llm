# Research: making "is this obligation still unsatisfied, and is it a fixable kind?" computable without task-specific verifiers

Date: 2026-09-01. Scope: literature only (arXiv / ACL / NeurIPS / ICLR / EACL); repo read-only.
Problem as given: 264k-param attention-bias controller on frozen Qwen3-1.7B; actuator causally works for
content-insertion families only; the WHEN signal that works (held-out AUC 0.70-0.76, R3b +2.6pts) is an
obligation-state check that currently requires running vendored IFEval checkers on the partial response.
Question: what computes that obligation state without verifiers, and what is most likely to work here?

Repo context checked (read-only): E0 cached h20 at policy-divergence points but its labels were
repair-vs-regression (causal, blurred; killed). The "6 model-state features" are hand-built scalars
(entropy, margin, conflict energy, attention mass, address stability). NO experiment in WORKLOG/EVF-PLAN
trains a residual-stream probe against per-constraint "satisfied-so-far" labels. That is the gap.

---

## 0. One-paragraph verdict

The literature contains a direct precedent for exactly the missing piece: a linear probe on the frozen
LM's hidden states that reads "how many of the required keywords have been satisfied so far" at every
generation step, at r~0.85-0.90 / MAE<1 on 7B chat models (Sun et al. 2023, arXiv:2310.16343, Table 8).
Nobody has (a) done it for Qwen3-1.7B, (b) made it constraint-conditioned (one probe that takes the
constraint text/family as input rather than one probe per keyword), or (c) wired it as the gate of an
attention-steering actuator. The rest of the literature says: model-dynamics features do not carry the
signal (matches your AUC 0.46-0.54); output-side small judges are unreliable exactly on the "partial /
not yet" label (MCJudgeBench macro-F1 0.44-0.53 for 3-4B judges, VerIF soft-verifier 48% even at 32B);
RL-training the gate end-to-end has no small-scale precedent that beat a hand rule; and the instruction-
following probes that DO work generalize across tasks but NOT across unseen instruction families
(Heo et al. ICLR 2025: AUROC 0.74-0.88 within family, 0.50-0.55 leave-one-family-out). So the recommended
experiment is a verifier-supervised, constraint-conditioned "obligation probe" on the residual stream
(verifier at train time only), evaluated by whether it reproduces R3b's +2.6pts without the checkers, and
whether it can rank soft constraints (tone/pattern) that have no checker at all.

---

## 1. Self-verification / intrinsic satisfaction estimation (output-side)

### 1a. Constraint-level LLM judges — how good are small ones?
- **MCJudgeBench** (Qwen Team, arXiv:2605.03858, 2026). Constraint-level yes/no/partial labels, 8 families
  (Lexicon, Numeric, Format, Content, Component, Faithfulness, Factuality, Style). Small judges:
  Qwen3.5-4B CJAR 0.853 but macro-F1 0.529, intrinsic inconsistency 24.2%; Llama-3.2-3B CJAR 0.770,
  macro-F1 0.441, inconsistency 35.4%. Systematic leniency: gold "partial" is mapped to "yes" more often
  than to "partial". Transfer: the label you need ("not yet satisfied") is precisely the one small judges
  get wrong.
- **VerIF** (arXiv:2506.09942, 2025). Soft-constraint verification by QwQ-32B is only 48.1% accurate
  (Table 1); a distilled IF-Verifier-7B drops policy IFEval from 84.5 to 80.0 vs QwQ. Rule checkers are
  96% precise. Transfer: a 1.7B self-judge will be far below this.
- **Precision over Diversity** (arXiv:2601.04954, 2026). LLM RM (Qwen2.5-32B) precision 71.5% vs 96% for
  rule checkers, and violation recall of only 9.2% vs 81.2%. Training on hard (verifiable) constraints
  only beats mixed: IFEval 80.78 vs 77.82, Multi-IF 58.89 vs 54.44 (Qwen2.5-7B). Attention analysis: hard-
  constraint training internalizes IF as a meta-skill. Transfer: this argues for training your gate on
  verifier labels only and expecting some transfer to soft families, rather than training on noisy judge
  labels.
- **TinyJudge** (arXiv:2606.07520, 2026). Distils a large judge into 0.6B specialists for the three soft
  families that generalize (style, structure, semantic); Qwen3-32B judge only 74.5% on soft constraints;
  point-wise (one constraint per call) beats batch by +6.1%. RL gains +10% avg (7B). Transfer: a 0.6B
  specialist judge per soft family is a real inference-time option, but it needs a separate forward pass
  per constraint per check (they report 6x cheaper than a 32B judge, not free) and it judges finished
  text; no result on prefixes.
- **IF-CRITIC** (arXiv:2511.01014), **RubricEval** (2603.25133), **IF-RewardBench** (2603.04738):
  checklist-decomposition critics; all are >=7B and full-response; no prefix results.

### 1b. Self-check inside the policy
- **Light-IF** (arXiv:2508.03178, 2025): trains 1.7B/32B Qwen3 to "preview and self-check"; Light-IF-32B
  IFBench 0.917 vs 0.838. Requires full RL of the trunk; self-check accuracy never measured. Not
  applicable to a frozen trunk.
- **When Thinking Fails** (arXiv:2505.11423, 2025): CoT lowers "constraint attention" (attention mass to
  GPT-4o-extracted constraint substrings, early-mid layers) and lower constraint attention predicts
  reasoning-induced violations; self-reflection improved IFEval on 11/14 models but hurt ComplexBench on
  10/14; "classifier-selective reasoning" (a trained classifier deciding when to reason) was best,
  Llama-3-8B +10.7pp. Transfer: (i) evidence that attention-to-constraint mass is a violation signal in
  their setting — but your data already found attention mass has no held-out signal at the moment level;
  (ii) the "classifier decides when to intervene" pattern is the same shape as your gate and it worked
  at 8B with a model-specific classifier.
- **Models Recall What They Violate** (arXiv:2604.28031, 2026): models restate violated constraints
  with 97.3% recall (forked query) while violating them; "knows-but-violates" 8-99%. Transfer: the
  obligation is verbally available to the model even when the output drifts; a readout of it is
  plausible, and the failure is action not knowledge (consistent with your actuator finding that focus
  fixes insertion).
- **Small LMs need strong verifiers to self-correct** (arXiv:2404.17140): self-verification by <=8B
  models is unreliable for reasoning; consistent with the above.

### 1c. Partial-prefix reward models (are prefix judgments predictive?)
- **Early Rejection with Partial Reward Modeling** (arXiv:2508.01969, 2025): PRM scores at 64-token
  prefixes correlate >0.90 (Kendall/Pearson) with final scores on math; rho ~ sqrt(tau/L); 1.4-9x FLOP
  savings. Math-only.
- **Reasoning models know when they're right** (arXiv:2504.05419, 2025): 2-layer MLP probes (most
  collapse to linear) on R1-Distill 1.5B-32B hidden states predict intermediate-answer correctness
  ROC-AUC 0.78-0.91 in-domain; math<->math transfer 0.80-0.83; math->logic 0.56-0.63; signal present at
  10% of the chunk (-14pp from peak); early exit saves 24% tokens.
- **Gnosis** (arXiv:2512.20578, 2025): ~5M-param head on final-layer hidden states (dilated conv +
  set-attention pooling) + attention-map statistics (entropy, spectral, diagonal) across layer-head
  grid; Qwen3-1.7B backbone: AUROC 0.95 on math self-judgment vs 0.79 logit entropy, 0.90 SkyworkRM-8B,
  0.91 Gemini 2.5 Pro; zero-shot on partial generations reaches near-peak at 40% completion; ~25 ms
  latency; trained on 54k automatically labeled items in 12 h on 2xA100. Transfer: the most direct
  evidence that a small head on a frozen 1.7B Qwen3 can read task-outcome state from internals
  including partial generations. Their labels were correctness; yours would be verifier labels.
- **One-Token Verification** (arXiv:2603.01025, 2026): LoRA verifier triggered by a [ToT] token reading
  the KV cache; token-level correctness at any stage; AIME24 83.3 vs 79.1 GenRM on Qwen3-4B. Needs LoRA
  on the trunk (not frozen) — off-brand for you.
- **STEP** (arXiv:2601.09093): hidden-state step scorer for trace pruning, 45-70% latency reduction.

Judgment on (1): output-side self-verification with a 1.7B model is a dead end for the "partial / not
yet" label (small judges are lenient precisely there, and it costs a second decode per constraint).
Internal-state readout of outcome state at 1.7B is well supported (Gnosis, probes above).

---

## 2. Internal-state readout of pending obligations

### 2a. Direct precedent: constraint-completion state is linearly readable
- **Sun et al., "Evaluating, Understanding, and Improving Constrained Text Generation for LLMs"**
  (arXiv:2310.16343, v2 2024). Hypothesizes a "constraint completion state" in hidden states; trains a
  linear layer on the LAST layer at EVERY generation step to predict "how many of the required
  keywords (<=5) have been satisfied so far". LLaMA2-7B-chat, Vicuna-7B, Mistral-7B-Instruct,
  Falcon-7B-Instruct: Pearson 0.845-0.898, MAE 0.53-0.68 (Table 8). Probe used only for analysis.
  Separately, "Attention Re-anchoring" (mask-multiplied attention boost on keyword tokens) gives up
  to +8% on lexical constraints (Table 9) — i.e. the same actuator family as yours, and the same
  finding that it helps lexical/insertion constraints.
  Transfer: HIGH. This is your obligation feature, read from h without a checker. Gaps: keyword-count
  only; not constraint-conditioned; 7B not 1.7B; no gating use; last layer only.

### 2b. Instruction-following success is readable but family-specific
- **Heo et al., "Do LLMs 'know' internally when they follow instructions?"** (ICLR 2025,
  arXiv:2410.14516). Linear probes on LLaMA-2-7B/13B-chat, Mistral-7B, Phi-3-mini; IFEval-simple
  (keyword incl/excl, frequency, placeholder, end-phrase x 100 tasks). First-token early-layer probes:
  AUROC 0.74-0.88 across held-out TASKS; middle-token probes 0.54-0.58; leave-one-INSTRUCTION-TYPE-out
  AUROC 0.50-0.55 (also with 23 types). Steering along the probe direction raises success 0.57->0.59,
  0.61->0.65, 0.58->0.64, 0.71->0.74. The direction is most sensitive to instruction PHRASING.
  Transfer: HIGH as a warning. A single "will follow" probe does not transfer to unseen families. Any
  obligation probe must be conditioned on the constraint (text or family embedding) or trained per
  family, and evaluated leave-one-family-out (as you already do).
- **Linear Probes Detect Task Format, Not Reasoning Mode** (arXiv:2606.02907, 2026): probes often read
  surface format. Same caution.
- **Disposition Distillation at Small Scale: a three-arc negative result** (arXiv:2604.11867, 2026):
  frozen-base hidden-state sidecar on Gemma-4-E2B / SmolLM2-1.7B: within-distribution AUC 0.683 ->
  fresh held-out 0.516 (probe read stylistic closure). Transfer: exactly your E0/E2 pattern (in-sample
  0.676 -> held-out 0.5). The falsification pipeline (fresh held-out generation, per-axis sweep, multi-
  layer pooling, cross-model replication) is worth adopting for any probe claim.

### 2c. Goal/progress/length state is readable during generation
- **How Much is Left?** (arXiv:2607.05316, 2026): remaining output length linearly decodable per token
  from late layers of 7-8B models; per-token probe beats countdown (GSM8K MAE 36.6 vs 44.0); jumps at
  retraction tokens. Transfer: your "position in response" feature (AUC 0.55-0.62 alone) and the word-
  cap hazard are readable internally; a "will exceed cap" probe is plausible, which matters because
  your main breakage is n_words_max.
- **Real-Time Progress Prediction** (arXiv:2506.23274): 10-bucket progress probes on Qwen3-0.6B/4B,
  DeepScaleR-1.5B: 30-36% accuracy, MAE 1.1-1.7 buckets (weak at small scale).
- **Doomed from the Start** (arXiv:2607.06503, 2026): residual-stream probes at the final token of each
  agent round predict episode failure at round 1 (behavioral scorers need 3-4 rounds); Llama-3.2-3B /
  Qwen2.5-7B, recall-controlled cascade saves 37-47% compute at 90% recall; adding behavioral features
  gave nothing.
- **A Behavioural and Representational Evaluation of Goal-Directedness** (arXiv:2602.08964): hidden
  states encode coarse plans; trajectory-length predictions track goal progress.
- **When Attention Closes** (arXiv:2605.12922, 2026): Goal Accessibility Ratio (attention mass from
  response tokens to goal tokens in the system prompt) declines 27-48% by late turns, tau=-0.75; but
  residual probes still predict outcomes at AUC up to 0.99 after attention "closes" — the information
  survives in the residual stream even when attention to the goal span is gone. Transfer: supports
  reading obligation state from h rather than from attention mass.
- **Defending against Indirect Prompt Injection by Instruction Detection** (arXiv:2505.06311): last-
  token hidden state at layer 14 of Llama-3.1-8B best detects "an instruction is present/being acted
  on". Mid-layer instruction-state readout.

### 2d. Predicting steerability from internal state (the "is it the kind I can fix" half)
- **When is Your LLM Steerable? / SteerBoost** (arXiv:2606.11599, 2026). Qwen3-1.7B, Gemma-2-2B,
  Llama-3.2-3B. GBDT over (token, layer) grid features from the first k=6 decoded tokens, steered vs
  unsteered, predicts Over/Under/Success-steer: macro-F1 ~0.8 in-distribution, ~0.72 OOD concepts;
  OverSteer recall 87-93%; guided strength search hits ~98% of oracle success with ~11% of the decoded
  tokens. Transfer: HIGH and on your exact backbone. The "one-token counterfactual" in your E1 plan is
  their feature design; they show it predicts over-steering (your breakage) well at 1.7B.
- **Prompt Steering Replacement** (arXiv:2605.03907, 2026): a one-layer ReLU probe on pre-steering
  activations outputs a per-token steering coefficient, trained to imitate the effect of adding the
  instruction to the prompt (MSE on activations or LL on outputs); beats constant steering on IFEval
  and persona tasks (Llama-3.2-3B/3.1-8B, Qwen2.5-7B, Gemma-2-9B). Transfer: this IS "learned per-token
  gate, no verifier at inference"; but its supervision is "match the prompted model", which caps it at
  what prompting achieves and does not encode obligation state.
- **Dynamically Scaled Activation Steering** (arXiv:2512.03661, 2025): logistic-regression gate on the
  token's activation decides steering magnitude; Qwen2.5-1.5B toxicity 9.78%->3.98% at <=5% ppl cost;
  2d+2 FLOPs per token. Same shape as a hidden-state gate; labels were "source-like vs neutral".
- **Directer** (arXiv:2603.06745, 2026): KV-cache steering on instruction tokens, accepted per token
  only if the steered top token stays plausible (p_steered >= beta * p_raw), progressively removing
  layers; IFEval 78.8/84.8 (+6.5 over baseline, ~+4 over PASTA/SpotLight) on Llama-3.1-8B with no
  quality loss; 16% throughput cost. Transfer: a verifier-free, training-free rejection rule for over-
  steering. It would not have caught your word-cap breakage (fluent, plausible, longer), but it is a
  cheap safety filter to stack.

Judgment on (2): the obligation-state readout exists in the literature (2a) and outcome/steerability
readout on Qwen3-1.7B specifically exists (Gnosis, SteerBoost). The known failure is cross-family
transfer of unconditioned probes (2b). Nobody has built a constraint-conditioned obligation probe.

---

## 3. Attention/activation signatures of forgetting

- **When Attention Closes** (2605.12922): the clearest "forgetting signature" — attention mass to goal
  tokens decays over turns and a sliding-window mask produces deterministic closure; but downstream
  outcomes remain probe-readable from the residual stream (AUC up to 0.99). Per-turn, not per-token.
- **When Thinking Fails** (2505.11423): constraint-attention drop under CoT predicts violations
  (early-mid layers). Per-response aggregate.
- **Multi-IF** (arXiv:2410.15553): defines Instruction Forgetting Ratio; behavioral only.
- **LLMs Get Lost in Multi-Turn Conversation** (arXiv:2505.06120): 25-pt drop, loss-of-middle-turns;
  behavioral only.
- **Phase Transitions in Compositional Constraint Satisfaction** (arXiv:2608.12426, 2026): sCSR
  collapses multiplicatively (72.0% x 0.922^(k-1)); constraints needing sustained tracking (word
  counts, letter avoidance) degrade fastest; binary include/exclude constraints are nearly immune; no
  internal analysis. Transfer: matches your family split exactly (insertion fixable, counts/limits not)
  and says the not-fixable families are the "tracking" families — i.e. the actuator cannot supply a
  counter, only an emphasis.
- Your own measurement (attention mass, address stability: AUC ~0.5 at the moment level) is consistent
  with the field: attention-side signals are coarse (per-turn/per-response), residual-side signals are
  where the per-step information is.

Judgment on (3): no paper detects a forgotten obligation per token from attention. Attention decay is
real but slow and turn-scale; do not spend on attention-signature gating.

---

## 4. RL / end-to-end training of a tiny controller with verifier reward (frozen trunk)

- **Small Vectors, Big Effects** (arXiv:2509.06608): RL-trained additive residual vectors on a frozen
  base recover a large share of full-fine-tune reasoning gains; mechanism is mostly token-substitution
  bias at last/penultimate layers ("To", "Step"). Math only.
- **Policy Gradient Steering** (arXiv:2607.27574, 2026): 32-1,152 scalar vectors trained by policy
  gradient on behavioral rewards (chess/football/gridworld), matches LoRA at 1/40 the parameters, one
  gradient update from 20-40 rollouts. Not LLM-IF.
- **Steer2Adapt** (arXiv:2602.07276): composes existing steering vectors; adaptation not gating.
- **Training-Free GRPO** (arXiv:2510.08191): frozen LLM, optimization in context space.
- **Instructions Are All You Need** (arXiv:2510.14420, 2025): constraint-wise binary reward model
  (Qwen2.5-1.5B/7B) trained on pseudo-labels from constraint decomposition — responses to prompts WITH
  constraint c are positives, WITHOUT c are negatives — no external verifier; 14k samples; Kendall tau
  62.7-76.7 vs humans; GRPO policy gains IFEval +21.6 (Qwen2.5-1.5B), AgentIF +7.3 OOD. Transfer: the
  pseudo-labeling trick is verifier-free and family-agnostic, and it works at 1.5B. It labels whole
  responses, not prefixes, but the same trick generates prefix negatives (prefix from a no-constraint
  rollout is "unsatisfied"). This is the best verifier-free label source for soft families.
- **RLCF / Checklists** (arXiv:2507.18624): 72B judge x 25 samples per item plus verifier programs;
  FollowBench HSR +5.5 abs on Qwen2.5-7B. Judge cost is enormous. Not for a GPU-days budget.
- **IFBench** (NeurIPS 2025, arXiv:2507.02833): IF-RLVR overfits: Tulu-3-8B 92.2 IFEval vs 45.9 IFBench
  (46.3-pt gap), Qwen2.5-7B 87.8 vs 54.7; wider constraint variety and wider variable ranges
  generalize better. Transfer: any gate trained on IFEval families will overfit them; train on IFTrain's
  29 extra constraints + IFEval, and hold out families.
- No paper trains a tiny gate/controller by RLVR on a frozen trunk for instruction following and
  reports moment-level gating quality. Your own result (fire-at-first-eligible-step equals the per-turn
  oracle; timing does not create benefit, only avoids harm) means there is little for RL to learn beyond
  a family/obligation classifier; RL would re-derive R3b at far higher cost and variance.

Judgment on (4): dead end for this budget. The learnable object is a classifier with cheap dense
labels; RL adds variance without a new signal. Keep the verifier as a label source, not a reward.

---

## 5. Sidestepping approaches

### 5a. The obvious candidate: auxiliary obligation head trained on verifier labels (verifier train-time only)
Is it established practice? Yes, under several names, none IF-specific: "hidden-state probes as
practical recipe" (streaming moderation, arXiv:2606.10487: token-level probes on generator
activations, one mid layer recovers most of a guard model's decisions, sub-ms per token, no extra
forward pass), "latent verifier" (arXiv:2603.22492, on diffusion hidden states, 0.5B LM connector,
63% cheaper than decode-and-judge), Gnosis (self-awareness head), "value head on hidden states" for
reward-guided decoding (arXiv:2406.07780 trains a Bradley-Terry RM explicitly on partial sequences),
constitutional-classifier-style activation probes. The closest IF instance is Sun et al. 2023's
keyword-count probe (2a), which was never deployed as a gate. So: established pattern, unbuilt instance.

### 5b. Constrained decoding for the verifiable subset + focus for the rest
- Grammar/automata-constrained decoding (arXiv:2508.15866, 2506.09701 ABS, NeuroLogic 2010.12884) gives
  hard guarantees on lexical/format families. NeuroLogic already tracks per-clause reversible/
  irreversible satisfaction state during beam search — the "obligation state" formalized for lexical
  constraints. Transfer: for kw_exist/placeholders/postscript, NeuroLogic-style clause tracking is a
  verifier-free obligation tracker (it is just string matching over the prefix), and constrained
  decoding could enforce them outright at higher fluency risk. Word caps could be enforced by EOS
  forcing. This is engineering, not research; it removes the vendored IFEval checkers only for
  families that were machine-checkable anyway, so it does not address the 81.5% of Multi-IF constraints
  or unbenchmarked obligations.
- **Neuro-Symbolic Verification** (arXiv:2601.17789, 2026): LLM writes executable verifier scripts for
  arbitrary NL constraints, with neural sub-checks for non-symbolic ones. Same box as Multi-IF's 18.5%
  plus LLM-judged remainder.

### 5c. Instruction-hierarchy / span-attribution gating
- **V-Steer** (arXiv:2607.26228, 2026): DLA-based detection of heads favoring lower-priority spans,
  value-vector scaling, IHEval rule following 14.5->77.1 on Llama-3.1-8B at 1.01x cost. Detects
  conflicts between spans, not unmet obligations. Not the missing piece.

---

## 6. Ranked recommendations

### THE ONE TO RUN: constraint-conditioned obligation probe on the residual stream ("OBLIGATION-PROBE")

Claim: replace `run_vendored_checkers(partial_text)` in R3b with `g(h_t, e_c)`, a small head reading the
frozen trunk's residual stream at step t, conditioned on an embedding of constraint c, trained on
verifier labels offline. Inference needs no checker and no extra forward pass.

What to train
- Input: residual stream at a mid-late layer (sweep L in {14, 18, 20, 22, 24} of 28; Sun et al. used the
  last layer, injection-detection and moderation work found mid layers best, "How Much is Left" found
  late layers for length), mean-pooled over the last 8 tokens, concatenated with (i) the trunk's own
  pooled hidden state over the constraint's instruction span (this is the "e_c" — free, already
  computed, and it is what your controller attends to) and (ii) a family one-hot for the 9 IFEval
  families (ablate it; the family-free version is the one that generalizes).
- Head: bilinear / 2-layer MLP, <=1M params. Three outputs per (t, c):
  1. sat_c(t): constraint c already satisfied in the prefix (binary).
  2. fixable_c: constraint is an insertion-type obligation (postscript/placeholder/kw_exist/kw_freq) vs
     a tracking/limit type (word cap, sentence count, caps, title, bullets). Trained on family labels;
     evaluated leave-family-out to see if "insertion-ness" is readable from the instruction span
     representation for an unseen family.
  3. cap_hazard(t): a live length/limit constraint is present AND response is within 25% of the cap
     (label from checker + token count). This is the single most valuable bit (your headline).
- Labels: run the vendored checkers on every prefix of every stored response (WORKLOG says full
  response text for native and all arms is on disk — 564 moments plus the 487+ single-turn base
  records and the calibration set). Per-token labels are free: one checker pass per prefix on CPU.
  Add IFBench/IFTrain's 29 extra verifiable constraints (arXiv:2507.02833) to widen the family set
  beyond IFEval's 25, per the IFBench overfitting result. Add "Instructions Are All You Need"
  pseudo-labels for soft constraints: generate responses with and without constraint c; prefixes of
  without-c responses are negatives for sat_c. This gives labels for tone/style/pattern families with
  no checker.
- Compute: feature extraction is teacher-forced forward passes only (one per stored response, cache
  h_L for all tokens): ~1-2k responses x ~200 tokens on a 1.7B trunk = minutes to an hour on one GB10.
  Probe training: CPU/GPU seconds. Soft-family pseudo-label generation: ~2k extra generations, ~2-3
  GPU-h. Total well under one GPU-day.

Inference-time signal
- At each eligible step: fire iff max over live c of [ (1 - sat_c(t)) * fixable_c ] > theta AND
  cap_hazard(t) < theta_cap AND position > 50% (keep R3b's position term or let the probe absorb it).
  Cost per step: one small matmul on an already-computed hidden state (2d+2 FLOPs per DSAS).
- Optional stacked safety filter: Directer's plausibility rejection (p_steered >= beta * p_raw) on the
  first steered token — training-free, catches gross over-steering, ~16% throughput.

Evaluation (registered before running)
- Primary: reproduce R3b's deployment sim on the 72 harvested turns with the probe in place of the
  checkers. Bar: probe-R3b within 1 turn of checker-R3b (+6 turns, +2.6pts) under session/topic/family
  splits. If it matches, the mechanism has left the verifier box on the families that exist.
- Component AUCs: sat_c(t) per family, leave-family-out. Prior from Sun et al. is r~0.85-0.90 for
  keyword counts on 7B last-layer; expect lower at 1.7B and under family holdout. Kill if leave-family-
  out AUC for sat_c < 0.65 AND family one-hot is doing all the work (then it is a checker in disguise).
- Generalization test that actually answers the research question: hold out ENTIRE families
  (postscript, placeholders) from training and check whether sat_c still ranks satisfied vs unsatisfied
  prefixes for them. Then the Multi-IF slice: run the gate on Multi-IF turns whose constraints have no
  vendored checker, log fires, and score with the Multi-IF judge/checkers post hoc (oracle-timing screen
  already costed at ~2.5 GPU-h on the diagnostic slice per the worklog).
- Falsification protocol from arXiv:2604.11867: fresh held-out generation, per-axis probe sweep,
  multi-layer pooling variant, and a second backbone (Qwen3-4B) replication before any claim.

Honest probability estimates
- P(sat_c probe reaches leave-topic-out AUC >= 0.80 on insertion families at 1.7B): ~0.65 (strong
  precedent at 7B; the label is a simple string property of the prefix; the risk is that the 1.7B trunk
  does not keep a keyword-satisfied state around linearly).
- P(probe-R3b matches checker-R3b within CI on the harvest): ~0.45 (needs sat_c AND cap_hazard to both
  work; cap_hazard has the "How Much is Left" precedent but on 7-8B).
- P(it transfers to a held-out family with no one-hot, i.e. genuinely escapes the box): ~0.25 (Heo et
  al.'s 0.50-0.55 leave-one-type-out is the base rate; conditioning on the instruction-span
  representation is the only thing that could beat it, and it is untested).
- P(it beats the current state, defined as a verifier-free gate with net gain CI clearing zero on the
  harvested turns): ~0.40. That is the single number for "beats current state": it must equal R3b's
  benefit while removing the checkers; it cannot exceed R3b much because the per-moment oracle is only
  +6.0pts and R3b already takes 40% of it.

Why it beats the alternatives at your budget: dense free labels, no new generation on frozen streams,
sub-millisecond inference, a direct precedent, and it is the one experiment that can be killed in a
day on CPU features already on disk.

### Secondary, cheap, worth stacking
- NeuroLogic-style clause tracker for the lexical families (string matching over the prefix, no
  IFEval code): trivial, verifier-shaped but benchmark-independent, and it gives an exact target for
  the probe to be compared against.
- Directer plausibility rejection as an over-steer filter (training-free).
- SteerBoost-style one-token counterfactual features (steered vs unsteered first-k tokens) for
  cap_hazard/over-steer prediction — their macro-F1 0.8 on Qwen3-1.7B is on your exact backbone; this is
  what your E1 "one-token counterfactual" step was going to compute.

### Dead ends (do not spend)
1. Output-side self-verification with the 1.7B trunk as its own judge ("have I done X?" prompting):
   small judges are lenient exactly on "partial/not yet" (MCJudgeBench macro-F1 0.44-0.53, VerIF 48% at
   32B, violation recall 9.2%), and it costs a second decode per constraint per check. Even TinyJudge's
   0.6B specialists are full-response and cost a forward pass each.
2. RL/GRPO-training the gate on verifier reward: no small-scale precedent for IF gating; your own
   analysis shows timing carries no benefit beyond a family/obligation classifier, so RL would re-learn
   R3b with sparse, high-variance rewards. Verifier belongs in the label pipeline, not the reward.
3. Attention-signature forgetting detectors: attention decay is real but turn-scale (GAR -27..48% over
   many turns) and per-response; your moment-level attention-mass AUC ~0.5 is the field's result too.
4. More model-dynamics features (entropy, margin, conflict energy): three independent lines (yours,
   Disposition Distillation's 0.68->0.52 collapse, "Task Format not Reasoning Mode") say they read
   style/format, not obligation.
5. Unconditioned "will-follow" probes: Heo et al. ICLR 2025 leave-one-instruction-type-out AUROC
   0.50-0.55. Any probe not conditioned on the constraint will fail the family split you already run.
6. Trying to make the actuator fix limit/tracking families by better timing: 2608.12426 shows tracking
   constraints are the ones that collapse under load and your data shows focus lengthens output;
   these need a counter (constrained decoding / EOS forcing), not emphasis.
7. Checklist-judge RL (RLCF) at this budget: 72B judge x 25 samples per item.

---

## Citations (arXiv id — venue if known)
- 2310.16343 Sun et al., Evaluating/Understanding/Improving Constrained Text Generation (constraint-completion probe, attention re-anchoring)
- 2410.14516 Heo et al., Do LLMs know internally when they follow instructions? — ICLR 2025
- 2410.12877 Stolfo et al., Improving Instruction-Following through Activation Steering — ICLR 2025
- 2505.12025 SpotLight: Dynamic Attention Steering — EACL 2026 (IFEval +26% prompt-level avg over 3B-72B; bias = log(psi_target/psi_current))
- 2506.13734 InstABoost (constant attention-logit bias to instruction tokens; +8.5% over next best)
- 2311.02262 PASTA
- 2603.06745 Directer (plausibility-gated KV steering, IFEval +6.5)
- 2605.03907 Prompt Steering Replacement (per-token learned steering coefficient)
- 2512.03661 Dynamically Scaled Activation Steering (logistic gate, Qwen2.5-1.5B)
- 2409.05907 Conditional Activation Steering — ICLR 2025
- 2606.11599 When is Your LLM Steerable? (SteerBoost, Qwen3-1.7B)
- 2512.20578 Gnosis (5M-param self-awareness head, Qwen3-1.7B, AUROC 0.95, partial generations)
- 2504.05419 Reasoning Models Know When They're Right (hidden-state correctness probes)
- 2606.10487 Stop Early, Spend Less (token-level hidden-state probes for streaming moderation)
- 2603.01025 One-Token Verification
- 2603.22492 Tiny Inference-Time Scaling with Latent Verifiers
- 2508.01969 Early Rejection with Partial Reward Modeling
- 2406.07780 A Critical Look at Tokenwise Reward-Guided Text Generation (partial-sequence RM)
- 2607.05316 How Much is Left? (remaining length linearly encoded)
- 2506.23274 Real-Time Progress Prediction in Reasoning LMs
- 2607.06503 Doomed from the Start (agent failure probes, recall-controlled cascade)
- 2605.12922 When Attention Closes (Goal Accessibility Ratio; residual probes AUC 0.99)
- 2505.11423 When Thinking Fails (constraint attention; classifier-selective reasoning)
- 2604.28031 Models Recall What They Violate (knows-but-violates)
- 2604.11867 Disposition Distillation at Small Scale (negative result; falsification pipeline)
- 2606.02907 Linear Probes Detect Task Format, Not Reasoning Mode
- 2505.06311 Instruction Detection for prompt-injection defense (layer-14 hidden state)
- 2605.03858 MCJudgeBench (Qwen Team; constraint-level judge evaluation)
- 2506.09942 VerIF (soft verifier 48.1% at 32B)
- 2601.04954 Precision over Diversity (hard-constraint training transfers; judge recall 9.2%)
- 2606.07520 TinyJudge (0.6B specialist soft-constraint judges)
- 2511.01014 IF-CRITIC; 2603.25133 RubricEval; 2603.04738 IF-RewardBench
- 2510.14420 Instructions Are All You Need (pseudo-labels from constraint decomposition; 1.5B RM)
- 2507.18624 Checklists Are Better Than Reward Models (RLCF)
- 2507.02833 Generalizing Verifiable Instruction Following (IFBench) — NeurIPS 2025
- 2508.03178 Light-IF (preview + self-check; 1.7B/32B)
- 2608.12426 Phase Transitions in Compositional Constraint Satisfaction
- 2410.15553 Multi-IF; 2505.06120 LLMs Get Lost in Multi-Turn Conversation
- 2509.06608 Small Vectors, Big Effects (RL-trained steering vectors); 2607.27574 Policy Gradient Steering; 2602.07276 Steer2Adapt; 2510.08191 Training-Free GRPO
- 2607.26228 V-Steer (instruction hierarchies at inference)
- 2601.17789 Neuro-Symbolic Verification on Instruction Following; 2010.12884 NeuroLogic Decoding; 2508.15866 / 2506.09701 constrained decoding
- 2404.17140 Small LMs Need Strong Verifiers to Self-Correct
