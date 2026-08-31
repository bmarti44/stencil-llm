# Research: making the wave controller help on open-ended generation
Date: 2026-08-31. Scope: web/arXiv survey for the wave-controller program (frozen Qwen3-1.7B trunk, 264k-param pre-softmax attention bias in layers 20-27, instruction-span pointing). Our empirical facts taken as given: +18.5 pts when the pointed-at info is out of attention's reach; -4.6 pts (best recipe) on IFEval-style free generation; root causes (a) teacher-forced CE rewards imitation, (b) always-on bias starves attention over the model's own recent output, (c) no static gain dose beats base.

## Headline finding

The literature does NOT support the strong scope hypothesis ("attention steering can only help when information is out of reach"). It supports a sharper claim: **static, always-on attention biases fail on instruction following for models that already read the prompt, while closed-loop, deficit-triggered biases show positive IFEval deltas at 3B-72B scale.** SpotLight (arXiv 2505.12025) is the existence proof, and its authors' diagnosis of static methods is word-for-word ours: static biases "ignore the model's natural attention distributions and potentially break generation by over-steering when the attention is already adequate." Our root causes (b) and (c) are a rediscovery of this; the published fix is a per-step feedback law, not a better static dose.

---

## Q2. Attention steering at inference (answered first — it carries the headline)

### PASTA — arXiv 2311.02262 (ICLR'24)
- Method: post-hoc reweighting at a profiled subset of attention heads; upweight user-marked spans, downweight the rest. Static (constant strength for the whole generation), inference-only.
- Measured: synthetic instruction tasks (Pronouns Changing, JSON Formatting), context-conflict/bias tasks. GPT-J-6B: 39.9% -> ~93% compliance on Pronouns Changing (+53 pts); LLaMA-7B JSON formatting 96.6% format / 85.1% prediction accuracy.
- Scale/conditions: base (non-instruction-tuned or weakly tuned) 6-7B models, tasks where the base model largely ignores the instruction — i.e., huge headroom. Requires per-model head profiling (~1000 examples).
- Mapping to us: this is the regime where our wave already wins. PASTA's wins are on models/tasks with instruction-reading deficits; it is not evidence a static bias helps a competent instruction-tuned model. Consistent with our -4.6.

### SpotLight — "Spotlight Your Instructions: Instruction-following with Dynamic Attention Steering", arXiv 2505.12025 — THE key paper
- Method: per-decoding-step, per-query-position feedback. Compute the post-softmax attention proportion on the highlighted spans, psi_current(i) = sum_{j in S} A_ij / sum_k A_ik. If psi_current < psi_target, add pre-softmax bias B_ij = log(psi_target / psi_current(i)) on span keys; otherwise bias = 0. Applied across all layers/heads (no profiling). Bias vanishes exactly when attention is already adequate — so the model's attention over its own recent output is untouched whenever it is doing fine.
- Measured, instruction-tuned models 3B-72B (Qwen2.5-3B/7B/72B, Llama-3.1-8B/70B, Granite-3.1-8B, Mistral-7B):
  - IFEval (prompt/instr-level): Qwen-3B 0.42/0.53 -> 0.53/0.62 (PASTA: 0.42/0.55); Qwen-7B 0.47/0.59 -> 0.54/0.66; Llama-8B 0.42/0.55 -> 0.51/0.62. So +7 to +11 pts prompt-level on IFEval, on models that already read the prompt, where PASTA gives +0 to +3.
  - ManyIFEval (many simultaneous instructions): >30% prompt-level accuracy improvement.
  - HotpotQA: +10% vs base, +6% vs PASTA (EM/F1). WildJailbreak refusal +6-10%.
- Failure mode acknowledged: at high target strengths, relevance degrades ("over-focus").
- Mapping to us: direct. Our controller is a learned static-dose version of what SpotLight does with a closed-loop rule. The delta between PASTA-on-IFEval (~0) and SpotLight-on-IFEval (+7..+11) is the measured value of conditionality. Strong candidate: keep our learned span-pointer and gain geometry, but multiply it by a per-step deficit term (or replace amplitude with the log-ratio law) so the bias is zero whenever attention on the spans already meets target. This addresses (b) and (c) without retraining the trunk.

### InstABoost — "Instruction Following by Principled Boosting Attention", arXiv 2506.13734
- Constant additive pre-softmax bias B on instruction tokens, all layers/heads (exponential multiplicative boost e^B on those keys). Llama-3-8B-Instruct, Gemma-7B-it, 15 steering tasks (persona, emotion, jailbreak-resistance, truthfulness, QA). Matches/outperforms latent-steering baselines, avoids fluency collapse; but documents an "instruction over-focus" failure where boosting suppresses benign competing rules — a constant bias again pays a tax. No IFEval numbers.
- Mapping: corroborates that a well-placed constant pre-softmax bias is viable for categorical behaviors but degrades when the task needs balanced attention — same tension we hit.

### AutoPASTA — "Model Tells Itself Where to Attend", arXiv 2409.10790
- Model self-identifies key context sentences, then PASTA-style steering on them. +7.95% avg for Llama-3-70B-Instruct on open-book QA (faithfulness/grounding). Not IFEval; the target is context the model under-uses — again the "out of reach / under-attended" regime.

### Selective Prompt Anchoring (SPA) — arXiv 2408.09121 (ICML'25)
- Documents attention dilution: models pay progressively less attention to the user prompt as more tokens are generated, and links this to errors. Fix: logit-level anchoring (contrast logits with and without prompt masked, scale the difference) — the whole prompt, applied through decoding. Pass@1 up to +12.9% across 6 code LLMs / 6 benchmarks.
- Mapping: evidence that prompt-attention decay during generation is a real, exploitable failure — but SPA acts on logits, not attention, so it cannot starve self-attention over recent output the way our bias does. Also note their anchoring strength is small and tuned; large strengths hurt.

### Conditions where steering helps vs hurts (synthesis for Q2)
- Helps: instruction-reading deficit (weak/base models — PASTA), attention dilution over long generations (SPA), under-attended context (AutoPASTA), many simultaneous constraints (SpotLight/ManyIFEval), positional degradation (found-in-the-middle).
- Hurts/neutral: static bias on competent instruction-tuned models at ordinary prompt lengths (PASTA's ~0 on IFEval; our -4.6; InstABoost over-focus; broad activation-steering literature: "Analysing the Safety Pitfalls of Steering Vectors" arXiv 2603.24543, "Forecasting Side Effects of Activation Steering" arXiv 2608.11227, "Minimizing Collateral Damage in Activation Steering" arXiv 2605.01167 all report collateral capability loss from unconditional interventions).

---

## Q1. Training objectives that make steering help open-ended generation

### RLVR / GRPO with constraint checkers as reward (mature at 1-8B; applied to full models, not yet to tiny controllers)
- "Generalizing Verifiable Instruction Following" — arXiv 2507.02833 (IFBench). GRPO with per-constraint verifier functions as outcome reward; IFEval categories saturate (>90%) under IF-RLVR; gains concentrate on deterministic format/length/punctuation constraints, limited on semantic ones. Trains 7-8B policies.
- VerIF — arXiv 2506.09942. Rule-based code verification + LLM verification (QwQ-32B) as reward; VerInstruct (~22k instances); SOTA IF at comparable size, general capabilities "unaffected."
- IFDecorator — arXiv 2508.04632. Wraps IF-RLVR with difficulty curriculum + intent checks to prevent reward hacking of verifiers.
- MDP-GRPO — arXiv 2606.06058. Stabilizes GRPO for multi-constraint IF (per-constraint credit).
- Mapping: the reward machinery is exactly our deterministic-verification culture (we already own machine checkers). Nothing published trains a 264k-param attention controller with GRPO on a frozen trunk — the nearest neighbors are below — so this is open ground, and cheap: the policy has 264k params, rollouts are the cost.

### On-policy / RL-trained lightweight controllers over frozen trunks
- Guiding Giants (WAS) — arXiv 2505.20309. Trainable lightweight controller reads intermediate activations, emits a global scale + per-layer weights modulating a precomputed steering vector, per-token at inference. Trained discriminatively (harmful vs benign), not RL, but it is the published "stateful gain schedule for a frozen LLM" blueprint. Llama/Mistral, safety benchmarks (ToxicChat refusal up significantly).
- VSPO — arXiv 2605.15604. Uses steering vectors at varying intensities to generate on-policy rollouts feeding GRPO — steering as an exploration device for RLVR.
- Policy Gradient Steering — arXiv 2607.27574. Formulates steering itself as RL: accumulate policy gradients of a behavioral objective over a few rollouts into a removable task vector.
- EAST — arXiv 2406.00244. Entropy-weighted steering vector to control an agent's action-entropy — precedent for uncertainty-coupled intervention strength.
- Mapping: combine WAS's architecture (controller reads decoding-time hidden state, outputs time-varying gain) with IF-RLVR's reward (our checkers). GRPO over rollouts scores the controller, not the trunk. This attacks root cause (a) head-on: reward constraint execution, not imitation of canonical responses.

### Contrast pairs with machine-verified minimal violations — yes, there is literature
- MuSC — arXiv 2502.11541 (ACL'25). Builds negatives by constraint mutation (Constraint-Dropout / Constraint-Negate / Constraint-Substitute) and — crucially — does token-aware preference optimization: dynamic token-level supervision concentrating the preference gradient on the tokens where the pair differs. Self-generated pairs, no GPT-4 teacher. Significant gains on complex + general IF benchmarks at 7-8B.
- "From Complex to Simple" — arXiv 2404.15846. DPO triplets where negatives fail specified constraints; shows the discrimination signal from constraint-failing negatives is what teaches multi-constraint following.
- Automatic Pair Construction for Contrastive Post-training — arXiv 2310.02263 (NAACL'24 Findings). Curriculum from easy to hard contrast pairs.
- Mapping: our machine-verified minimal violation mutations are a strictly better version of MuSC's negatives (ours are verified-minimal). The published recipe to exploit them is token-level DPO/preference loss on the controller only — the gradient localizes on exactly the violating tokens, which teacher-forced CE cannot do. This is the highest-leverage supervised objective available to us short of RL.

### KL-preserving / side-effect-bounded steering objectives
- "Steering Without Side Effects" — arXiv 2406.15518 (KL-budgeted post-deployment control; steer only flagged cases).
- Minimizing Collateral Damage in Activation Steering — arXiv 2605.01167; Forecasting Side Effects — arXiv 2608.11227. Frame: constrain KL(steered || base) off-target while maximizing on-target effect.
- Mapping: cheap addition to any of the above — add a KL(wave || base) penalty on tokens where the verifier says base is already compliant. With attenuating gain converging to base from below, an explicit off-target KL anchor is likely necessary for any static component to be net-nonnegative.

### Scheduled sampling for controllers
- No paper trains an attention-steering controller with scheduled sampling specifically. The general exposure-bias literature (Bengio et al. 2015; Confidence-Aware Scheduled Sampling, arXiv 2107.10427) transfers: our root cause (a) is textbook exposure bias — the controller never sees its own downstream consequences under teacher forcing. The field's actual cure at LM scale has been on-policy RL (above), not scheduled sampling; recommend going straight to rollouts.

---

## Q3. State-conditional / adaptive gating — the stateful version exists in pieces

- SpotLight (2505.12025): state = current attention distribution; fire only on deficit. Simplest, proven on IFEval. (See Q2.)
- CAST — "Programming Refusal with Conditional Activation Steering", arXiv 2409.05907 (ICLR'25, IBM). Condition vectors gate behavior vectors by hidden-state similarity: "if condition then steer." Prompt-conditional rather than decoding-state-conditional, but the gating machinery (project hidden state onto a learned condition direction, threshold) is reusable per-step.
- Guiding Giants WAS (2505.20309): learned controller network reads activations during generation, emits time-varying, layer-resolved gain. The closest published artifact to "our wave with a brain."
- EAST (2406.00244): entropy of the action distribution as the state variable driving steering.
- FLARE — arXiv 2305.06983: intervene (retrieve) only when next-sentence token confidence is low — the canonical "intervene when about to fail" decoding loop.
- Entropy-informed decoding — arXiv 2605.09745: entropy + entropy-variance triggers for inserting interventions at high-uncertainty points.
- Steering Vector Fields — arXiv 2602.01654: replaces a global static vector with a context-dependent field refreshed from evolving hidden states; explicitly stronger on long-form generation, and documents that vanilla static vectors lose effectiveness as context grows.
- Nobody has published: a learned gate that tracks unmet obligations (pending placeholders, counts, case constraints) and fires span-pointing only for the still-unsatisfied constraint. The ingredients (verifiable per-constraint state + conditional gating) all exist separately; the combination is open.

## Q4. The scope hypothesis — supported in weak form, refuted in strong form

Supporting evidence (steering wins where attention is degraded/insufficient):
- Found-in-the-Middle — arXiv 2406.16008 (ACL'24 Findings): attention calibration against U-shaped positional bias; up to +15 pts on long-context RAG/retrieval tasks. Gains exist precisely because attention mis-allocates.
- Focus Directions — arXiv 2503.23306: KQ-space directions at "contextual heads" fix long-context task misalignment.
- "Don't Lose Focus" — arXiv 2605.06342: steering's harm concentrates in attention rerouting; key-orthogonal projection preserves NIAH performance — i.e., naive steering hurts exactly when sparse high attention on important distant tokens must be preserved. (Mechanistically kin to our root cause (b).)
- PASTA's gains living on weak models/synthetic tasks; AutoPASTA's on under-used context; SPA's on diluted prompt attention over long code generations; our own +18.5 out-of-reach result.
- Multi-turn decay: Multi-IF (arXiv 2410.15553) — accuracy drops monotonically with turns (o1-preview 88% -> 71% by turn 3, "instruction forgetting"); "Measuring and Controlling Instruction (In)stability" — arXiv 2402.10962: system-prompt drift within 8 rounds in LLaMA2-70B-chat/GPT-3.5, attributed to attention decay, mitigated by split-softmax (an attention-budget intervention on the system prompt — mechanistically our wave's cousin, and it helps there); MMMT-IF — arXiv 2409.18216 (instructions dispersed across long dialogues); "When Attention Closes" — arXiv 2605.12922.
- Steering Vector Fields (2602.01654): static vectors work <2K tokens, degrade with context — dose-response of staticness with context length.

Refuting the strong form: SpotLight's +7..+11 IFEval prompt-level on instruction-tuned 3B-70B models shows in-reach instruction following IS improvable by attention steering — provided the intervention is closed-loop. So: scope determines how much headroom exists; the control law determines whether you can collect it without paying the always-on tax. Our data (-4.6 with the best static recipe; convergence to base from below as gain attenuates) is exactly what this literature predicts for a stateless spotlight, and is not evidence the mechanism is scope-limited.

## Q5. Neuroscience-inspired oscillation/top-down models — candid: no LM-benchmark wins yet

- Neural Wave Machines — Keller & Welling, ICML 2023 (PMLR v202): locally coupled oscillatory RNNs with traveling waves; wins on synthetic sequence tasks, not LMs.
- Traveling Waves Encode the Recent Past — arXiv 2309.08045: wave-based RNNs solve longer sequence tasks, learn faster — again synthetic memory tasks.
- Traveling Waves Integrate Spatial Information — arXiv 2502.06034; spacetime perspective — arXiv 2409.13669. Same story.
- Gated Attention for LLMs — arXiv 2505.06708 (NeurIPS'25, Qwen team; 1.7B dense & 15B MoE, 3.5T tokens): head-specific sigmoid gate after SDPA improves quality, stability, and removes attention sinks. Not oscillatory and requires pretraining, but it is the strongest evidence that a learned multiplicative gate on attention output is beneficial at exactly our trunk's scale (Qwen 1.7B) — supports "gate, don't bias, and make it input-dependent."
- Verdict: Miller-flavored oscillation-gated selection has no published empirical win on real LM benchmarks. Our program is ahead of that literature, not behind it; cite it as inspiration, not evidence.

---

## Ranked shortlist — three concrete next steps

1. **Close the loop: deficit-triggered wave (SpotLight-ize the controller).** Keep the learned span pointer and layer placement; replace the static gain with per-step conditional amplitude: measure post-softmax attention mass on the pointed spans at each query position, fire only when below a target, with strength log(psi_target/psi_current) or controller-predicted. Bias is exactly zero when attention is adequate — root causes (b) and (c) die by construction. SpotLight's IFEval numbers (+7..+11 prompt-level, 3B-8B instruction-tuned) are the preregisterable prior that this recipe has positive expected delta on the exact benchmark where we now lose. Cheapest experiment: pure inference-time change, our existing harness verifies it deterministically. (arXiv 2505.12025; corroboration 2506.13734, 2408.09121.)

2. **Retrain the controller on-policy with our verifiers as reward, plus token-level contrast on our minimal-violation mutations.** Two-stage: (i) token-aware preference optimization (MuSC-style, arXiv 2502.11541; 2404.15846) on our machine-verified minimal violation pairs — gradient localizes on violating tokens, killing the imitation bias of teacher-forced CE (root cause a); (ii) GRPO on rollouts with per-constraint checker rewards (IF-RLVR recipe: 2507.02833, 2506.09942, 2508.04632), policy = 264k controller only, trunk frozen — unpublished combination, cheap at our scale, and our deterministic-verification culture is precisely the reward infrastructure this literature assumes. Add an off-target KL(wave || base) anchor on already-compliant tokens (2406.15518, 2605.01167).

3. **Preregister the scope-graded battery where the mechanism should win even in static form, with turn/length/distractor load as the registered moderator.** Predicted ordering of wave delta: Multi-IF later turns (arXiv 2410.15553; frontier models drop 17 pts by turn 3) > ManyIFEval high-constraint-count cells (SpotLight got +30% there) > MMMT-IF dispersed instructions (2409.18216) > system-prompt-stability self-chats (2402.10962 protocol) > long-context IF / NIAH-with-constraints (found-in-the-middle regime, 2406.16008) >> single-turn IFEval (expected ~0 or negative for static wave). A monotone delta-vs-load curve crossing zero is a publishable confirmation of the weak scope hypothesis and defines the wave's deployment envelope; pairing it with step 1 tests whether closed-loop control flattens the curve's negative end to >= 0.

## Secondary citations index
PASTA 2311.02262 | SpotLight 2505.12025 | InstABoost 2506.13734 | AutoPASTA 2409.10790 | SPA 2408.09121 | Found-in-the-Middle 2406.16008 | Focus Directions 2503.23306 | Don't Lose Focus 2605.06342 | Steering Vector Fields 2602.01654 | CAST 2409.05907 | Guiding Giants WAS 2505.20309 | EAST 2406.00244 | FLARE 2305.06983 | Entropy-informed decoding 2605.09745 | IF-RLVR/IFBench 2507.02833 | VerIF 2506.09942 | IFDecorator 2508.04632 | MDP-GRPO 2606.06058 | MuSC 2502.11541 | From Complex to Simple 2404.15846 | Pair construction 2310.02263 | Steering w/o Side Effects 2406.15518 | Collateral damage 2605.01167 | Side-effect forecasting 2608.11227 | Safety pitfalls 2603.24543 | Multi-IF 2410.15553 | MMMT-IF 2409.18216 | Instruction (in)stability / split-softmax 2402.10962 | When Attention Closes 2605.12922 | VSPO 2605.15604 | Policy Gradient Steering 2607.27574 | Gated Attention 2505.06708 | Neural Wave Machines (Keller & Welling, ICML'23) | Traveling waves 2309.08045, 2502.06034.

Caveats: Multi-IF id (2410.15553) cited from memory plus a search snippet reporting the 88->71 o1-preview turn decay — verify id before preregistering. Several 26xx-series ids are 2026 preprints not yet peer-reviewed. SpotLight numbers transcribed from the paper's HTML (prompt-level/instr-level pairs); re-verify Table values before quoting in a registered document.
