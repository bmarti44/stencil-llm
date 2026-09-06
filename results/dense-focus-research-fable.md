# Weight-side focus on a dense 27B trunk — independent research read (fable, 2026-09-06)

Second opinion to astra on the same brief (scratchpad `dense-focus-research-brief.md`). CPU only; web search and
fetch; no installs; no model launches; nothing under `data/bench` read. Every paper cited below was opened
(abstract/HTML/PDF or the HF/GitHub page); items I could not confirm are marked **[unverified]**. Local evidence is
cited by check number; I reviewed 31/32/34/35/36/38/40b/40e/40f/40h/40i/40j/40k/40l/42/43 myself and the
numbers below are the ones that reproduced in those reviews.

## 0. What the local record already rules out (be blunt)

| Lever | Local result | Status for a dense 27B |
|---|---|---|
| Extracted mean-difference residual vectors (check 31, 1.7B + 4B) | 0 task inductions in 18 cells x 2 trunks; A/B vectors cosine 0.89–0.98 — the vector encodes "an instruction is present", not which one | Closed for the extraction recipe; scaling to 27B does not fix collinearity |
| KV packet / coordinate transplant (32, 33) | 0/64 on both trunks; only the real cue *columns* (34: 59/60) transplant, i.e. the text's own KV | The write channel works only when it carries the text |
| Dense MLP neuron selection (41 frequency, 41b causal) | 41: SET 0/64, text 64/64. 41b: parser-level JS 14/32 with 7/32 broken; " moduleId" prefix on 23/32 | Not possible / marginal-junk |
| MoE router bias (40b–40l) | SET works on a weak prior only; 40k competence 16/32 -> 7/32; 40l "competence direction" = length confound | Moot on dense; also shows the recurring shape: selection bought with competence |
| Rendering (40j, FOCUS-3, 42) | 40j text-only 16/16 executable JS fresh and after 6 retained Python answers; bias/mask add nothing | The working mechanism |

Pattern across all of it: every activation-side actuator we built either did nothing (collinear vectors, operand-free
packets) or bought selection with breakage. The web literature below says the same thing at 2B–9B scale, with
numbers, so there is no reason to expect a 27B dense trunk to behave differently for activation edits. The one
family the local record has **not** tested is weight *selection* (adapters), which is a different mechanism from
activation *addition* — that is where the residual question lives.

## 1. Task / function / in-context vectors at scale

**What it is.** Add a direction (extracted or learned) to the residual stream to make the model behave as if an
instruction or demonstration were present.

**Evidence.**
- Stolfo et al., ICLR 2025, "Improving Instruction-Following through Activation Steering"
  (https://arxiv.org/html/2410.12877): Phi-3-mini, Gemma-2-2B/9B, Mistral-7B. Format-instruction adherence with the
  vector alone (no instruction text) rises from ~10% to ~30%; adding the vector *on top of* the text gives small
  gains; two vectors compose at different layers; degraded outputs (repetition, junk) attributed to layer choice.
  This is the best-case published number for "instruction with no text": ~30% adherence. Our own text bar is 100%.
- AxBench, ICML 2025 (https://arxiv.org/html/2501.17148): steering harmonic-mean scores, Gemma-2-2B / 9B — Prompt
  0.698 / 1.075; LoRA 0.637 / 0.602; ReFT-r1 0.633 / 0.630; DiffMean 0.297 / 0.322; SAE 0.177 / 0.191. Quote:
  "increasing the steering factor monotonically reduces instruction-following capability in all methods." The gap
  between prompting and every vector method *widens* from 2B to 9B.
- Understanding (Un)Reliability of Steering Vectors (https://arxiv.org/html/2505.22637): Llama-2-7B-chat, 36
  datasets; ~1/3 of samples move in the *opposite* direction; anti-steerable fraction 3–50% per dataset; steering
  is reliable only where activation differences are directionally coherent (high cosine across pairs). Our check-31
  vectors were coherent *with each other* (A ~ B), which is the failure mode this paper predicts.
- Steering Code LLMs for language/library control (https://arxiv.org/html/2603.23629): CodeGemma-7B,
  Qwen2.5-Coder-7B, Llama-3.1-8B; diff-in-means directions switch Python/C++, PyTorch/TF etc. under neutral prompts and
  "can sometimes override" explicit instructions, asymmetrically (common target easier); **no pass-rate metric at
  all** (LLM-judge for language only); "beyond a moderate range, generations become increasingly repetitive or
  incomplete." This is the published version of our 40b/41b: language flips, competence unmeasured or lost.
- Learned (not extracted) task vectors (https://arxiv.org/pdf/2509.24169) and FLAS (https://arxiv.org/abs/2605.05892,
  Gemma-2-2B/9B-IT, first learned method to beat prompting on AxBench at 1.015/1.113) show that *trained* vectors can
  close the gap — but a trained vector is a tiny fine-tune, i.e. the same category as the LoRA in §3 with less
  capacity and no clean off-switch semantics beyond "don't add it".

**Expected effect vs our bars.** Selection: partial (published ceiling ~30% without text). Competence: monotone loss
with dose (AxBench). Reversible: yes (stop adding). HOLD with no text: only at the partial level. Fails the
executable-competence bar by the literature's own numbers.

**Quick-check cost.** ~20 GPU-min on the 4B proxy (it *is* check 31); ~40 GPU-min on 27B. Not worth it: it re-runs a
closed check with a larger model and the literature predicts the result.

**Ship-form fit.** Good (a tensor + hook). **Risks.** Emergent misalignment from steering vectors was reported
across families including Qwen-3.5 (https://arxiv.org/abs/2606.08682): steered models "produce harmful responses
with stronger semantic relevance and higher coherence than their finetuned counterparts."

**Verdict: close for dense, with AxBench + Stolfo + (Un)Reliability as the citations.**

## 2. RepE / SAE feature steering on the 27B class

**What exists.** Qwen-Scope (https://arxiv.org/html/2605.11887; HF
https://huggingface.co/Qwen/SAE-Res-Qwen3.5-27B-W80K-L0_50): residual-stream TopK SAEs, width 81,920 (16x of
d_model 5120), L0 50/100, **all 64 layers of Qwen3.5-27B**, 64 `.pt` files, Qwen license, loading snippet on the
card. The HF card says the 27B SAEs are on the **base** model; the paper text says "instruct variant" — the two
sources disagree, **[unverified]** which. **No Qwen3.8 SAEs exist** as of this search; transfer of 3.5-27B SAEs to a
3.8-27B checkpoint is untested and should be assumed broken (different weights).

**Evidence.** Qwen-Scope's own steering demos are qualitative: suppress a Chinese-language feature to stop
code-switching; add a classical-Chinese style feature. No dose curve, no benchmark degradation number, no
instruction-following or coding result. Their code-switching *fix* is SFT with SAE features as an auxiliary loss —
training, not inference control. AxBench (above) puts SAE steering at 0.18–0.19 vs prompting 0.70–1.08. Side-effect
prediction (https://arxiv.org/html/2606.08365; GPT-2, Pythia, Gemma-2-2B, Llama-3.1-8B): the same feature steers
in inconsistent directions across contexts and spreads collateral to unrelated features; screening helps but the
dominant predictor changes per model and "collateral benefits attenuate at alpha >= 2.0".

**Expected effect vs our bars.** Selection of a *style/language* feature: plausible at the parser level (as in
40b/41b). Executable competence: no published measurement; AxBench says SAE is the worst family. HOLD with no
text: same partial ceiling. Reversible: yes.

**Quick-check cost.** Not runnable on 3.8-27B without training SAEs (not <= 1 GPU-h). On 3.5-27B [we do not have it
locally]: load 1–2 layer SAEs, find a "JavaScript" feature on own synthetic prompts, clamp, run the 40k executable
bank — ~1 GPU-h if the bf16 model is present. **Ship-form fit.** Adds 64 x (5120 x 81920 x 2) bf16 ~ 100 GB of SAE
weights if all layers are shipped; one layer ~1.7 GB. Poor.

**Verdict: close.** Nothing here beats what 41b already showed on 4B, and the benchmark literature ranks it last.

## 3. LoRA-as-focus (adapter selection as the Miller wave) — the one live question

**What it is.** Per rule-family adapters; the controller *selects* which adapter is active (SET), keeps it active
across turns with no text (HOLD), swaps it (SWITCH), removes it (CLEAR). Focus becomes a weight selection, not an
activation edit; the trunk is frozen; the ship form is "extra small weight files + custom generate", exactly our
form.

**Evidence, opened.**
- Skill-to-LoRA (https://arxiv.org/html/2606.16769v1): **Qwen3.6-27B** base, rank-16 adapters (~6M params per
  skill), offline self-distillation from SKILL.md files (the model generates task/target pairs, the adapter learns
  to reproduce the *behaviour*, not the text). Agent tasks: S2L 65/210 vs full-skill-text 54/210 vs vanilla 59/210;
  wrong-LoRA and shared-LoRA both reduce performance ("highly skill-specific"); token saving only **6.6%**
  relative. Best for "procedural skills with stable workflows"; skills needing concrete code examples or
  open-ended reasoning "may still benefit from runtime text." Note that in this study the *text* arm was below
  vanilla — long skill text hurt the 27B — so the adapter's win is partly "not having the text", not "holding
  better than text."
- Prompt Baking (https://www.alphaxiv.org/abs/2409.13697v1): KL-distill the prompted distribution into a LoRA
  (~5 min on 7B-class); GSM8K 79.1% baked vs 79.9% few-shot; **baked persona persists over long dialogue where the
  prompted persona decays**; baked models remain promptable and re-bakeable. No un-baking/composition study. This is
  the closest published statement of the Miller HOLD property for weights.
- Activated LoRA, NeurIPS 2025 (https://arxiv.org/abs/2504.12397; https://github.com/IBM/activated-lora): adapter
  weights apply only to tokens after an invocation string, so the base KV cache is reused across adapter
  switches; needs higher rank (r=32); "competitive accuracy with standard LoRA"; now in PEFT. A serving paper
  (https://arxiv.org/abs/2512.17910) builds vLLM cross-model prefix reuse on it (up to 58x latency reduction). aLoRA
  is the mechanical answer to "switch adapters mid-conversation without recomputing the cache". Deactivation
  semantics (returning to base for the *next* turn) are not documented on the repo page **[unverified]** — in
  practice it is "generate the next turn without the adapter."
- Adaptive Minds, LoRAs-as-tools (https://arxiv.org/html/2510.15416): Qwen2.5-7B / Qwen3.5-9B / Llama-3.1-8B; the
  base model routes to one of up to 30 adapters (98.3% routing accuracy); switch < 1 ms in vLLM; specialists +4.6 to
  +84 pp; **off-domain transfer ~0 on 7/9 pairs** — i.e. a wrong adapter mostly does nothing rather than breaking
  the base, which is the reversibility property we need. Multi-step results "mixed."
- LoRA as knowledge memory (https://arxiv.org/html/2603.01097v5; Qwen3 0.6B–14B, Llama): synthetic task-aligned
  formats far outperform raw text for internalisation; capacity is rank-bounded and non-monotone; "multi-LoRA
  systems introduce routing and interference bottlenecks"; "LoRA can catastrophically fail in certain settings."
- Doc-to-LoRA / Text-to-LoRA (https://arxiv.org/pdf/2602.15902; https://arxiv.org/html/2506.06105v2): hypernetworks
  emit a LoRA from a document or task description in one forward pass; Gemma-2/3 only; no Qwen-27B hypernetwork
  exists. Relevant only as the eventual "bake a new user rule in < 1 s" path; not a quick check.
- LatentSkill (https://arxiv.org/pdf/2606.06087): in-weight skills with a selector; documents accuracy loss as the
  number of coexisting skills grows and poor OOD skill combinations. **[numbers not extracted; PDF text noisy]**
- Practitioner note (https://tianpan.co/blog/2026-04-19-lora-adapter-composition-production, blog, **[unverified]**):
  conflicting adapters composed together can cancel to "10% of both"; merging beats switching for latency.

**What this does and does not buy against our bars.**
- SET: yes, for a *pre-trained* rule family (language, indentation, fence policy) — that is a distilled prompt.
- HOLD with no text: this is the property the weight side is *supposed* to have and Prompt Baking reports it.
- SWITCH / CLEAR: adapter off = base. Adaptive Minds' ~0 off-domain transfer suggests cleanness; not yet measured
  on retained history (the adapter's earlier outputs remain in the KV/text and can re-impose the old rule — our
  40d/40h "release" problem reappears at the *history* level, not the weight level).
- Competence: Prompt Baking and S2L report parity or gains on the trained family; nobody reports the paired
  executable-competence contrast we ran in 40k. Must be measured.
- The honest ceiling: S2L's token saving is 6.6%. Rendering a live rule block costs ~50–150 tokens; on a 27B the
  cost is negligible and the KV of the rendered block is cacheable. The *only* reason to prefer an adapter is if it
  HOLDs better than rendering under long retained history (Prompt Baking's drift claim) or if it carries procedures
  text cannot (S2L's claim). Neither has been shown on executable coding under competing rules.
- The deal-breaker for *live user rules*: an adapter takes minutes to distill; a user rule arrives mid-session. So
  LoRA-as-focus can only cover a fixed skill library, never the register's dynamic content. It is a complement to
  rendering, not a replacement.

**Quick-check cost on the GB10.** 4B proxy: Prompt-Baking-style KL distillation of one rendered rule into a
rank-16 LoRA over ~200–400 own synthetic prompts is ~10–20 GPU-min including eval (Prompt Baking reports ~5 min on
7B-class GPUs). 27B bf16: weights 56 GB (https://www.yottalabs.ai/post/how-to-fine-tune-qwen-3-8-27b-with-unsloth-2026);
a DGX Spark thread reports bf16 rank-16 LoRA on Qwen3.5-35B-A3B (67 GB) at ~72 GB peak with ~47 GB headroom
(https://forums.developer.nvidia.com/t/bf16-lora-fine-tuning-of-qwen3-5-35b-a3b-on-dgx-spark-no-quantization-required/363268),
so it fits; **throughput is not reported anywhere I found** [unverified]; my projection is 30–60 min for a few
hundred short steps, so the 27B run is at or over the 1 GPU-h line and needs the bf16 download first (not present
locally: `models/` holds 1.7B, 4B, 30B-A3B only).

**Ship-form fit.** Best of all levers: frozen trunk + N small adapter files + custom generate that selects; aLoRA
gives cache reuse. Caveat for Qwen3.8-27B: 48 of 64 layers are Gated DeltaNet linear-attention layers, 16 are full
attention (https://www.mindstudio.ai/blog/qwen3-8-27b-architecture-benchmarks, **[unverified against the local
config]**). LoRA targets are the same projections; but note that the 40h/40i *attention-mask release* contingency
only touches the 16 full-attention layers on this trunk — the recurrent GDN state cannot be masked. That is a
ship-form finding for the *masking* contingency, independent of this brief.

**Risks.** Distillation data must be our own synthetic prompts (never benchmark data; write the lineage line);
competence loss on the trained family must be measured with paired executable tasks (40k pattern); interference
when two adapters are active (style + language) is documented as real; "release" on retained history is the same
unsolved problem as 40d.

## 4. Attention-level carriers: gist tokens, soft prefixes, pinned instruction KV

**Evidence.** Gist tokens (https://arxiv.org/abs/2304.08467) compress prompts up to 26x but require fine-tuning
the LM with a gist mask and were validated at < ~30-token prompts; 500xCompressor and UniGist push ratios but all
"soft" methods "require co-training with the LLM" (survey https://arxiv.org/pdf/2410.12388). Prefix/prompt tuning on
a frozen trunk is a weight carrier, but I found **no** 2024–26 paper comparing a learned prefix against the plain
system prompt on IFEval-style adherence over multi-turn retention (search came back empty; treat as absent).
Stolfo's steering-vector-only 30% is the nearest data point. Pinned instruction KV is just the cached KV of the
rendered text — which is what every-request rendering with prefix caching already gives us for free.

**Expected effect vs bars.** A learned prefix per rule family is a weaker LoRA (fewer parameters, input-layer only
for prompt tuning); swap-prefix = switch is reversible. It saves ~50–150 tokens per request — the same 6.6%-class
saving. It cannot encode a rule that arrived mid-session without training.

**Quick-check cost.** Same as §3 but with worse capacity; **ship-form fit** fine. **Verdict:** dominated by §3 —
if an adapter cannot HOLD, a prefix will not; if an adapter can, the prefix is the cheaper variant to try second.

## 5. Working-memory / cognitive-control add-ons to frozen LLMs

**Evidence.** Trained persistent memory for frozen decoder-only LLMs (https://arxiv.org/html/2603.22329v1): six
memory injection methods on **GPT-2**; tests factual accumulation, not rules; retained-memory scores 7–18%; weak
injection points fail at 1x capacity. G-MemLLM (https://arxiv.org/html/2602.00015v1) gates latent memory into decoder
layers for long-context reasoning (trained, not frozen-trunk). Frontostriatal gating in transformers
(https://arxiv.org/abs/2402.08211): self-attention keys learn input-gating on toy WM tasks — our GPT-2-era
oscillator/gate result is the same class. Miniature brain transformer (https://arxiv.org/pdf/2603.07217): toy
scale. Memory-augmented transformer survey (https://arxiv.org/pdf/2508.10824): frozen-LLM recurrence is "simulated
via prompt management" (MemGPT-style) — i.e. an external register + rendering, which is what we ship.

**Verdict.** No paper reports rule retention over a long horizon on a frozen 20B+ model with a learned gate. The
literature's own answer for frozen trunks is the external register. Nothing to quick-check.

## 6. Negative evidence (for closing)

- AxBench: prompt > LoRA > ReFT > DiffMean > SAE on both sizes; steering factor "monotonically reduces
  instruction-following" (https://arxiv.org/html/2501.17148).
- (Un)Reliability: ~1/3 of samples anti-steered; steerability is a property of the data's direction coherence
  (https://arxiv.org/html/2505.22637).
- Code steering: language flips without any pass-rate measurement and with quality collapse beyond moderate alpha
  (https://arxiv.org/html/2603.23629).
- Steering-induced emergent misalignment incl. Qwen-3.5 family (https://arxiv.org/abs/2606.08682).
- SAE side effects are context-unstable and spread collaterally; predictors do not transfer across models
  (https://arxiv.org/html/2606.08365).
- Even the pro-steering papers (FLAS, PrOSV https://arxiv.org/abs/2605.05983, RePS https://arxiv.org/abs/2505.20809)
  frame their contribution as *narrowing the gap to prompting* on 2B–27B Gemma, and do so by training — i.e. by
  becoming small fine-tunes.
- Locally: 31 (0/288 inductions), 41 (0/64), 40k (16 -> 7), 40l (length confound).

## RANKED TOP-3 quick checks (each <= 1 GPU-h, pre-written GO, reversible, competence-paired)

Skill pair everywhere: JavaScript rule vs Python default, executable checkers, fresh own synthetic tasks (40k
pattern), greedy, no benchmark data. Data lineage for every item: distill-on = own synthetic prompts with the
teacher's own prompted outputs; evaluate-on = disjoint fresh tasks; nothing from `data/bench`.

**QC-A (decisive; 4B proxy, ~20 GPU-min): baked-rule adapter HOLD/CLEAR on Qwen3-4B.** KL-distill the *rendered JS
rule block* (teacher = trunk + rendered rule; student = trunk + rank-16 LoRA, no rule text) on ~300 synthetic
coding prompts (Prompt Baking recipe). Evaluate 32 fresh tasks x 4 arms: OFF (no text), TEXT (rendered rule),
ADAPTER (no text), ADAPTER+TEXT. Then 16 retained-history episodes: 6 adapter-on JS turns, then adapter off with
Python request (CLEAR).
GO: ADAPTER valid executable JS >= 26/32 (TEXT bar must be >= 28/32 or INELIGIBLE); paired executable pass
ADAPTER vs TEXT losses - wins <= 3 (competence); OFF-after-CLEAR Python >= 13/16 with broken <= 1 (reversible);
ADAPTER broken <= 2/32. MARGINAL: ADAPTER >= 20/32 with competence bar met. Otherwise NOT POSSIBLE -> close weight
side for dense.

**QC-B (only if QC-A GO; 27B, ~60 GPU-min, needs bf16 download): same recipe on Qwen3.8-27B**, 200 distillation
steps rank 16 on the 7 projections, 32 fresh tasks, same arms and bars. Add the 40k executable competence bank
as the paired contrast (ADAPTER vs TEXT wins/losses). Cost is at the 1 GPU-h line **[throughput unverified]**; if
a smoke run projects over, stop at the projection, do not shrink the bank.

**QC-C (only if QC-A GO; 4B, ~25 GPU-min): two-adapter interference + long-horizon HOLD.** Adapters: JS and
"2-space indent, no semicolons" style. 16 episodes x 20 rounds, both adapters on, no text after round 1; compare
against every-request rendering. GO: both rules held >= 14/16 at round 20 with executable pass within 2 of the
rendering arm; wrong-adapter (shuffled) arm imposes neither rule > 2/16. This is the only check that can show a
weight carrier *beating* rendering (Prompt Baking's drift claim) — if it only ties, rendering wins on simplicity.

Not ranked: any residual-vector, SAE-clamp or neuron check on 27B — the literature and checks 31/41/41b predict
the outcome; re-running at scale is spend without information.

## Plain-language paragraph for Brian

Everything we and the literature have tried that *adds* a direction to a dense model — steering vectors, SAE
features, neuron gains — selects a style at the parser level and pays for it in competence; the best published
"instruction with no text" number is ~30% adherence versus our 100% with rendering, and the largest benchmark shows
prompting beating every steering family with the gap widening at larger models. Scaling that to a 27B does not
change the physics, so I would close the activation side for dense models now, with AxBench, Stolfo and the
(Un)Reliability paper as the citations. The one weight-side idea the local record has *not* tested is selection of
a small adapter rather than an activation edit: a rule distilled into a LoRA that the controller switches on and
off. Published work on Qwen-27B-class models says such adapters hold a procedural rule with no text, cost almost
nothing to switch, and mostly do nothing when the wrong one is active — but they save only ~6% of tokens, take
minutes to make, and so can never carry a rule a user typed thirty seconds ago; at best they are a library of
fixed skills beside the register, not a replacement for rendering. The single experiment that decides it is QC-A:
bake the rendered JavaScript rule into a rank-16 adapter on the 4B, and ask, on fresh executable tasks, whether
the adapter with no text matches the rendered text on executable correctness, holds across turns, and releases
cleanly when switched off. If it fails, the weight side is closed for dense models and "rendering + masking is the
mechanism; weights are for knowledge" becomes the recorded position. If it passes, spend one GPU-hour repeating
it on the 27B and one more on two-adapter interference, and only then decide whether a skill library earns a
place in the ship form.
