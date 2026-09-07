# Deep web research for gpt-6-astra: the WEIGHT-SIDE focus mechanism on a DENSE trunk (Qwen 3.8 27B), given what has and has not worked (2026-09-06)

Brian's question: "if we switch to the dense model, maybe the focus mechanism on dense models is worth a deeper look?"
The Miller framing: knowledge stored in the weights, a separate "wave" selects which stored circuit governs now
(set / hold / switch / clear). What we have established on this project (read the cited files; do not repeat them):
- WORKS (the instruction half): an external register + every-request rendering of live rules controls a frozen
  trunk end to end (check 42 cadence; FOCUS-3 oracle 63/64 vs ~30 baselines; results/focus-mechanism-composition-
  v2-astra.md). Attention MASKING of the model's own stale outputs is a certified reversible "release" (checks
  40h/40i) but adds nothing when the rule is rendered (40j) — kept as a flagged contingency.
- CLOSED on the MoE (Qwen3-30B-A3B): router-logit bias selects an output family (Python->JS) only on a weak prompt
  prior (40g/40j), HARMS task competence at the certified dose (40k: 16/32 -> 7/32), and a competence-direction
  bias is a length confound (40l). Concept-level routing (43/43b) null.
- CLOSED on DENSE models (Qwen3-1.7B/4B): residual/activation steering vectors (checks 31-33), KV packet transplant
  (32), dense-model neuron selection by frequency (41) and causal attribution (41b: junk), function/task vectors
  (registered weight-side test: results/quick-checks/README.md items 31-39 and the fable reviews) — all null or
  marginal for selecting a skill/instruction without breaking competence. The GPT-2-era oscillator/gate results
  (archive/) are the only positive weight-side findings, at toy scale.
- The trunk may move to Qwen 3.8 27B DENSE (Qwen3_5 text architecture; 64 layers; local FP8 + GGUF; bf16 to be
  downloaded). No expert routers exist there, so the router lever is moot; the question is whether ANY weight-side
  focus lever on a dense 27B is worth a quick check, or whether the answer is "rendering + masking is the
  mechanism; weights are for knowledge", and we should stop spending on the weight side.
Research (arXiv/ACL/ICLR/NeurIPS 2024-2026, GitHub, HF), with real citations you opened, ranked by (chance of a
real, competence-preserving, reversible SELECTION effect on a 27B dense model) x (cheapness of a <= 1 GPU-h quick
check on our GB10) x (fit with the ship form: frozen trunk, extra small weight files, custom generate):
1. Task/function vectors and in-context-vector methods on 20-30B dense models (ICV, task vectors, function vectors,
   "steering by activation addition" at scale): any evidence of SET/HOLD/SWITCH of a task or instruction with
   competence preserved on real coding tasks? Effect sizes, dose windows, breakage.
2. Representation engineering / SAE-feature steering on dense 27B-class models (Gemma Scope-style SAEs for
   Qwen? Qwen3.5/3.8 SAEs available?): can a feature for "follow the current rule" / "language X" / "style Y" be
   clamped reversibly; evidence on instruction-following and coding; known failures (competence loss, over-
   steering).
3. LoRA-as-focus: small adapters per skill/rule family switched by the controller (activated LoRA / aLoRA, LoRA
   hot-swapping in vLLM, "skill library" adapters, MoLoRA/LoRA-MoE routing) — this makes "focus" a weight SELECTION
   at runtime rather than an activation edit; evidence on multi-adapter switching, interference, and whether an
   adapter can HOLD a rule with no text (the Miller property) better than rendered text; costs.
4. Attention-level control on dense models: attention sinks / persistent prefix tokens / "instruction KV" pinned
   in cache (StreamingLLM-style, gist tokens, prompt compression, "system prompt tokens" learned: e.g. learned soft
   prompts / prefix tuning as the focus carrier) — soft prompts are weights; can a learned prefix per rule family
   hold focus with fewer tokens than rendering, and is it reversible (swap prefix = switch)?
5. Working-memory / cognitive-control architectures added to frozen LLMs (memory tokens, recurrent controllers,
   "thought"/"scratchpad" control, Miller-inspired bursts/gating in transformers, neuroscience-informed gating
   papers 2024-2026): anything with a real result on instruction retention over long horizons.
6. Negative evidence: papers/notes showing activation steering degrades reasoning/coding competence, dose-
   sensitivity, and why prompting dominates at scale (so we can close the line with citations if warranted).
For each: what it is, evidence with links, expected effect on our bars (skill selection with executable
competence preserved, reversible, HOLD with no text), cost of a quick check on Qwen 3.8 27B (or the local 4B dense
as a proxy), ship-form fit, risks. End with: a RANKED TOP-3 quick checks (each <= 1 GPU-h, pre-written GO bar,
reversible, competence-preserving) OR an explicit recommendation to CLOSE the weight-side line for dense models
with the strongest citations; and a plain-language paragraph for Brian: given everything, is the weight side worth
a deeper look on the dense model, and which single experiment would decide it. Write
results/dense-focus-research-astra.md. CPU only; web search; no installs; no model launches; never read anything
under data/bench.
