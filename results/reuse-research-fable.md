# Reuse research: what already exists for P1–P7 (fable, 2026-09-06)

Scope: live web research (arXiv/ACL/OpenReview, GitHub, HF Hub, vLLM/SGLang/transformers/flash-attn
issues and docs) against the brief in the scratchpad. Read first: AGENTS.md, the composition design
and my review, quick-checks 31–44b, check40g, check44b + my review, and astra's three memos
(admission, MoE routing, neuron granularity). I do NOT repeat astra's items (Mem0/Letta/Zep papers,
CarMem, VARS paper, AdaMem, SteerMoE/RICE/Ban&Pick/C3PO/MetaNet papers, etc.); I extend them with
code, licenses, and newer primaries. CPU only; no model launched; nothing under data/bench read;
only this file written (results/ is gitignored, so nothing is committed). "Opened" = I fetched the
page; "unverified" = seen only in search snippets.

Verdict scale: drop-in / adapt (<= 1 day) / idea only / nothing reusable.

## P1. ADMISSION (span-level standing-rule detection)

| Item | What it is | License / maturity | Verdict |
|---|---|---|---|
| NLSI dataset, [paper](https://arxiv.org/abs/2311.09796) (NAACL Findings 2024), [HF data](https://huggingface.co/datasets/nikitam/nlsi), [repo](https://github.com/nikitacs16/nlsi) (opened) | 2,445 SGD-derived examples; each has `all_standing_instructions` (4–21 NL rules, given as a profile) and `applicable_standing_instructions` (0–6) per request, plus API calls. Task = which standing rules APPLY to this request, not extraction from user turns. | CC-BY-SA-4.0; test split 2,044, train 150 | adapt — for the render-scope matcher (E step, check42's request-kind lesson), not for admission |
| TAPS, [ACL](https://aclanthology.org/2025.emnlp-main.1200/), [repo](https://github.com/grill-lab/taps) (opened) | Structured tagging + uncertainty tool detector; SOTA open-source on NLSI. | Apache-2.0 | idea only (applicability, not admission) |
| VARS pref-extractor, [HF model](https://huggingface.co/blackhao0426/pref-extractor-qwen3-0.6b-full-sft), [repo](https://github.com/YurenHao0426/VARS) (opened; paper already in astra's memo) | Qwen3-0.6B full-SFT; input dialogue window, output `{condition, action, confidence}` tuples; 564K training rows released (`blackhao0426/user-preference-564k`, built from LMSYS-Chat/WildChat/Alpaca/SlimOrca + GPT-5.1 labels). Recall 97.5%, precision 37.7%, JSON validity 99.7%. | Apache-2.0 (model and repo) | idea only — high-recall paraphrased tuples, no source spans, precision 38%; usable at most as a recall-side candidate proposer, which is not 44b's bottleneck |
| Mem0 write prompts, [prompts.py](https://raw.githubusercontent.com/mem0ai/mem0/main/mem0/configs/prompts.py) (opened) | ADD/UPDATE/DELETE/NONE rules; extraction prompt explicitly extracts "incidental personal facts" embedded in requests and "key factual data FROM shared content"; skips assistant echoes. | Apache-2.0 | idea only — an ANTI-pattern for us: it admits from payloads by design; keep as a negative-family reference for why generic memory prompts fail our payload/quote families |
| MemGuard, [arXiv](https://arxiv.org/abs/2605.28009) (opened) | Type-aware memory (facts vs events vs behavioral rules stored separately, composed selectively at read). +28% reliability, 5.8x fewer memory tokens. | code not stated | idea only — supports our separate rule register vs fact store; no detector |
| ProMem, [arXiv](https://arxiv.org/abs/2601.04463) (opened); MemDelta, [arXiv](https://arxiv.org/abs/2606.29914) (opened) | ProMem: separate strategies for details/events/relations (EMNLP 2026 Findings). MemDelta: memory-eval confounds; "report write-path cost". | not stated | idea only |
| RECAST-30K, [arXiv](https://arxiv.org/abs/2505.19030) (unverified: license, source prompts) | 30k instances, 19 constraint types extracted from real prompt-response pairs. | unverified | idea only — a constraint-type label schema; lineage unknown, do not fit on it without checking provenance against IFEval-style sources |
| Span labeling with LLMs, [arXiv](https://arxiv.org/html/2601.16946) (unverified) | Compares tagging / matching / indexing strategies for LLM span labeling; small LLMs match fine-tuned encoders. | unverified | idea only — directly relevant to check44c's required token-level candidate generation |

REUSE VERDICT: nothing drop-in; one adapt (NLSI for scope/applicability). No public dataset or
model labels the standing-rule-vs-request/quotation boundary at span level with source offsets.

Concrete step (adapt): use NLSI's (request, all_standing_instructions, applicable) triples to fit
and DEV-calibrate a small "does live rule R apply to request Q" cross-encoder for the renderer's
request-kind matching (check42's B lesson). Data lineage: fit-on NLSI train+val (401 rows) plus our
own authored data; evaluate-on our fresh banks only; NLSI test never used as our decision bank.

Risks: NLSI is SGD-domain (hotels/flights), so transfer to coding obligations is unproven; VARS
labels are GPT-5.1 synthetic and WildChat-derived (no overlap with our authored banks, but do not
let it into a held-out); CC-BY-SA share-alike on NLSI derivatives.

## P2. RELATIONS / REGISTER (supersedes, cancels, completes, reinstates; versions)

| Item | What it is | License / maturity | Verdict |
|---|---|---|---|
| ReBIND / "Dead Text or Binding Clause?", [arXiv](https://arxiv.org/html/2608.12599) (opened) | Measures "relapse": revoked constraints keep shaping outputs. Qwen3-8B: relapse rises 0.011 -> 0.403 as constraints go 2 -> 8; ahead-of-time ledger compilation cuts relapse by 0.192 [0.134, 0.251]; one-sentence "tombstone" notes for revocations recover ~1/3 of that; a prospective probe predicts relapse at AUROC 0.897. Benchmark RELAPSE-Code = 67 HumanEval tasks x 201 checkers, immediate/delayed revocation scripts. | release: generator, protocols, pre-registration, trajectories (license not stated) | adapt (<= 1 day): add tombstone lines for retired rules to our every-request render; adopt "relapse" as a named endpoint |
| Graphiti (Zep), [repo](https://github.com/getzep/graphiti) (opened) | Bi-temporal edges `valid_at/invalid_at` + `created_at/expired_at`; contradictions invalidate, never delete; extraction needs structured-output LLMs ("very small models frequently emit JSON that doesn't match"). | Apache-2.0, active | idea only — schema mirrors our retire-by-mask-never-delete; its update logic is LLM-driven |
| MemoryAgentBench, [repo](https://github.com/HUST-AI-HYZ/MemoryAgentBench) (opened; ICLR 2026) | Conflict-Resolution category (FactConsolidation single/multi-hop): overwrite outdated facts, answer only with newest; substring-exact-match scoring. | MIT | eval candidate only (fact overwrite, not rule supersession); never fit |
| LongMemEval, [repo](https://github.com/xiaowu0162/LongMemEval) (opened) | 500 questions incl. "Knowledge Updates" and "Abstention" types; GPT-4o judge. | MIT | eval candidate only |
| ConInstruct, [arXiv](https://arxiv.org/abs/2511.14342) (opened) | Conflict detection/resolution among constraints; DeepSeek-R1 F1 91.5; models rarely notify users. | release not stated | idea only — within-prompt conflicts, not versioned updates |
| Mem0 ADD/UPDATE/DELETE/NONE (above) | Coarse update ops; "semantically equivalent -> NONE". | Apache-2.0 | idea only — our four relations are strictly richer |
| DST literature (MultiWOZ/SGD slot updates) | Slot-value ontologies; no free-text rule versioning. | — | nothing reusable |

REUSE VERDICT: idea only, plus one adapt (tombstones + relapse endpoint from ReBIND). No public
classifier or dataset for supersedes/cancels/completes/reinstates over free-text rules exists; our
FOCUS-3 v8 relation data remains the only such corpus I can find.

Concrete step: in the renderer, emit `retired: <key> v<n> (superseded by v<n+1> at msg <id>)` for
rules retired within the last K requests; measure on the existing 40i/42 banks (CPU render diff +
one ~20 GPU-min rerun) whether tombstones reduce stale-rule execution independent of masking.

Risks: RELAPSE-Code is HumanEval-derived — evaluation-only at most, never fit (AGENTS.md rule);
their numbers are Qwen3-8B dense, not our MoE.

## P3. RENDERING CADENCE (every-request render beat one-time statement in check42)

| Item | Evidence | Verdict |
|---|---|---|
| Laban et al., "LLMs Get Lost in Multi-Turn Conversation", [HTML](https://arxiv.org/html/2505.06120) (opened; ICLR'26 outstanding paper) | SNOWBALL (restate all shards every turn) vs RECAP (once at end) vs SHARDED, GPT-4o-mini / GPT-4o: Sharded 50.4/59.1, Snowball 61.8/65.3, Recap 66.5/76.6, Full 86.8/93.0. Every-turn restatement recovers 15–20% of the loss but stays 20+ points below single-turn Full. | idea only — independent confirmation of check42's direction AND of a hard ceiling for prompt-only cadence |
| Prompt Repetition (Google), [arXiv](https://arxiv.org/abs/2512.14982) (opened) | Repeating the whole prompt wins 47/70 model-benchmark pairs, 0 losses, no extra output tokens (single-turn, non-reasoning). | idea only — supports rendering obligations twice (top and as final-check block) |
| ReBIND repair ladder (above) | L1 = promote clause to an end-of-spec "final-check block"; adaptive routing adds nothing (-1.7pp). | adapt — put the live-rule block LAST in the request; skip adaptive cadence |
| DriftBench, [arXiv](https://arxiv.org/abs/2604.28031) (opened) | "Knows-but-violates": models restate constraints they violate (KBV 8–99% across 7 models); structured checkpointing only partially helps. CC-BY-4.0 release. | idea only — restatement/recap is not adherence; our endpoints must stay behavioral (they are) |
| "When Attention Closes", [arXiv](https://arxiv.org/abs/2605.12922) (opened) | Goal Accessibility Ratio: goal tokens become less attention-accessible over turns; force-closing the channel (Mistral) collapses 20-fact recall to 11%. | idea only — mechanistic support both for fresh re-rendering near the query and for masking as a release lever |
| Boosting IF at scale / SCALEDIF, [arXiv](https://arxiv.org/abs/2510.14842) (opened) | Adherence falls with instruction count; conflict among instructions is a main driver; a conflict scorer predicts the drop. | idea only — bound the number of live rules rendered; pre-check conflicts (our C step) |
| Anthropic context engineering, [post](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) (opened); long-running harnesses, [post](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) (opened) | Compaction, structured notes, tool-result clearing; per-session re-orientation via progress file + feature list; no quantitative cadence result, no explicit per-turn re-injection rule. | idea only |
| Claude Code memory/system-reminder, [docs](https://code.claude.com/docs/en/memory), [issue #52018](https://github.com/anthropics/claude-code/issues/52018) (unverified detail) | CLAUDE.md injected once at start; path-scoped rules re-injected as `<system-reminder>` when matching files are touched; kept out of the system prompt for prefix-cache economics. | idea only — event-triggered re-render (on file touch) is a cadence we have not tested |
| OpenHands condenser, [docs](https://docs.openhands.dev/sdk/arch/condenser) (opened) | Keeps first 4 events + tail; LLM-summarizes the middle at 120 events; no explicit instruction re-injection. | idea only |
| "Less Context, Better Agents", [arXiv](https://arxiv.org/html/2606.10209) (opened) | Keep last 5 tool pairs + summaries of evicted ones: 71.0 -> 91.6% task completion, -62.7% tokens (GPT-5, Dynamics 365). | idea only — tool-result pruning is a free win for the larger test's token caps |
| Context-as-a-Tool (CAT), [arXiv](https://arxiv.org/abs/2512.22087) (ACL Findings 2026, search only); VISTA proprioceptive dashboard, [arXiv](https://arxiv.org/html/2606.30005) (opened) | CAT: stable task semantics kept separate from short-term trace. VISTA: render a per-block ledger (ids, tokens, recency, archive status, budget) every turn; LOCA-Bench 50.7 vs 22.7 ReAct. | idea only — both converge on "stable register segment + fresh render each turn" |

REUSE VERDICT: idea only (all prompt-level); one adapt (final-check-block ordering + tombstones).
Nothing in the harnesses is measured more rigorously than check42 for our exact question.

Risk/insight: the Snowball ceiling shows every-request text alone leaves a 20+ point gap driven by
the model's own early commitments — which is precisely the lever only own-output masking (our Z)
can touch. That is the cleanest external argument for keeping the mask arm.

## P4. SKILL SELECTION IN THE WEIGHTS (MoE router bias on Qwen3-30B-A3B)

| Item | What it is | License / maturity | Verdict |
|---|---|---|---|
| SteerMoE code, [repo](https://github.com/adobe-research/SteerMoE), [LICENSE](https://raw.githubusercontent.com/adobe-research/SteerMoE/main/LICENSE) (opened) | Modified vLLM model code in `src/modeling_vllm`; `custom_steering.ipynb` detects experts from paired activation frequencies. 37 stars, 7 commits; models not named in README. | Adobe Research License — NONCOMMERCIAL | idea only (license); our 43b/40c profile recipe already does the contrastive part |
| EasySteer, [repo](https://github.com/ZJU-REAL/EasySteer) (opened) | vLLM fork (`vllm.steer_vectors`, tracks v0.26) with hidden-state steering AND "MoE router logits" capture/steering; 294 stars, 322 commits, EMNLP 2026 demo. Qwen3-MoE support not stated. | Apache-2.0 | adapt (<= 1 day) for a bias-only throughput pilot on vLLM; NOT a full-stack path (vLLM has no per-request key mask, see P5) |
| vLLM `FusedTopKBiasRouter` / `e_score_correction_bias`, [doc](https://docs.vllm.ai/en/latest/api/vllm/model_executor/layers/fused_moe/router/fused_topk_bias_router/) (opened) | Per-layer `(num_experts,)` float32 bias slot applied in fused top-k (DeepSeek-V3-style, default sigmoid scoring). Same shape as our 48x128 profile. | Apache-2.0, core vLLM | idea only until checked: DeepSeek semantics bias SELECTION only (weights from unbiased scores), whereas our recipe biases logits before softmax and changes weights too; Qwen3-30B-A3B has no bias tensor by default |
| REAP, [repo](https://github.com/CerebrasResearch/reap) (opened; ICLR 2026) | Expert pruning by router gate value x activation norm; supports Qwen3-30B-A3B via `MODEL_ATTRS`; has an "observer" module collecting per-expert router/activation statistics; released a 24,576-sample agentic calibration mix (code/reasoning/tool-calling/multi-turn). | Apache-2.0, production-grade | adapt (<= 1 day): reuse the observer for profile statistics and its calibration mix as NEUTRAL breakage-calibration text (not as profile donors); its "router keeps independent control after pruning" claim is weak support for the actuator |
| Rewiring Experts on the Fly, [arXiv](https://arxiv.org/html/2510.14853v1) (opened) | Additive per-layer router-logit bias delta^(l) optimized ONLINE on the model's own already-generated tokens (CE loss), re-fit every ~128 tokens; HumanEval +3.6–6.7 on OLMoE/DeepSeek-V2-Lite/Qwen1.5-MoE; no Qwen3, no code. | none | idea only — a self-fit bias is a candidate HOLD mechanism (fit delta to the last JS reply to sustain it) that does not need a stored profile; untested for switch/clear |
| "What Gets Activated: domain vs driver experts", [arXiv](https://arxiv.org/abs/2601.10159) (opened) | Entropy vs causal-effect metrics; driver experts are causal and triggered by EARLY tokens in a sentence. | code not stated | idea only — consistent with our decision-token finding (40b review: decision at the fence label) |
| DBES, [arXiv](https://arxiv.org/abs/2605.18498) (opened) | Five specialization metrics (routing specialization, effective rank, domain isolation, stiffness, n-gram expertise) on Qwen/DeepSeek/GLM. | code not stated | idea only — could grade profile quality before certification |
| qwen3-moe-analyzer, [repo](https://github.com/sionic-ai/qwen3-moe-analyzer) (opened) | Forced expert pools + EMA router stats on Qwen3 MoE (vLLM/MLX); 1 commit, 11 stars. | none stated | idea only |
| MoE2-LoRA, [arXiv](https://arxiv.org/html/2607.21978) (opened); peft [issue #2527](https://github.com/huggingface/peft/issues/2527) (opened) | Shared LoRA pool routed by reusing the pretrained router logits; Qwen3-30B-A3B at 39M trainable params; no code. peft: LoRA on fused 3D expert weights NOT supported (closed unimplemented, May 2025). | — | nothing reusable (and out of scope: no training) |
| Bandarkar multilingual-routing code | not found | — | unverified; nothing reusable |

REUSE VERDICT: nothing drop-in. Two adapts (EasySteer for a vLLM bias-only speed pilot; REAP
observer + neutral calibration mix). The literature has still not shown a retained-history
SET/HOLD/SWITCH/CLEAR with release — our 40i remains the only such result I can find.

Risks: SteerMoE license bars commercial use; REAP calibration mix is generic web/agentic data
(check for HumanEval/MBPP overlap before using as any calibration set); EasySteer's Qwen3-MoE
compatibility is unverified.

## P5. ATTENTION MASKING AS RELEASE (position-preserving persistent key mask)

| Item | What it is | License / maturity | Verdict |
|---|---|---|---|
| transformers `masking_utils`, [attention_interface docs](https://huggingface.co/docs/transformers/main/en/attention_interface) (opened) | `create_causal_mask(..., and_mask_function=f)` with `f(batch, head, q_idx, kv_idx) -> bool`; custom 4D masks (bool or 0/-inf float) accepted as-is by sdpa/eager; flex needs a BlockMask; `generate()` builds masks via `create_masks_for_generate`, which can be OVERRIDDEN on the model class. | Apache-2.0, current | drop-in — this is the sanctioned way to install our persistent keep-mask with unchanged positions (the 40i path); override `create_masks_for_generate` instead of hand-building 4D tensors |
| FlexAttention BlockMask, HF [issue #37006](https://github.com/huggingface/transformers/issues/37006) (opened), [integration](https://github.com/huggingface/transformers/blob/main/src/transformers/integrations/flex_attention.py) | Sparse block masks compiled from `mask_mod`; whole-code-body evictions are contiguous spans, so block sparsity actually skips compute (sdpa -inf masks do not). Issue: HF recreates BlockMasks per layer/forward (expensive). | Apache-2.0 | adapt (<= 1 day): register a keep-mask `and_mask_function`, cache one BlockMask per request, verify bitwise/near parity vs the sdpa 4D path on 40i records |
| kvpress (NVIDIA), [repo](https://github.com/NVIDIA/kvpress) (opened) | 40+ scoring presses, mostly prefill; experimental `DecodingPress`; `KeyRerotationPress` RE-ROTATES keys (changes positions) — the opposite of our invariant; no explicit-index press; Qwen3 dense tested, MoE not stated. | Apache-2.0, 1.2k stars | idea only — they compress physically; we mask logically |
| KVCache-Factory, [repo](https://github.com/Zefan-Cai/KVCache-Factory) (opened) | 16 methods (H2O/SnapKV/StreamingLLM/...), decode-time support. | MIT, pinned transformers 4.44.2 | nothing reusable (incompatible pin; scoring-based) |
| vLLM custom masks [#5228](https://github.com/vllm-project/vllm/issues/5228), 4D mask [#6615](https://github.com/vllm-project/vllm/issues/6615) (opened) | Both closed "not planned" (stale). | — | nothing reusable |
| vLLM FlexAttention backend, [doc](https://docs.vllm.ai/en/stable/api/vllm/v1/attention/backends/flex_attention/) (opened) | Layer-level `logical_mask_mod` hook, block-mask rebuild on change; prefix caching supported; per-REQUEST arbitrary masks not documented. | Apache-2.0 | idea only — a per-request keep-mask would need a fork; unverified feasibility |
| SGLang / FA3 custom masks, [flash-attn #1576](https://github.com/Dao-AILab/flash-attention/issues/1576) (opened) | Custom mask request for FA3 (from SGLang) closed without action; no SGLang per-request mask API found. | — | nothing reusable (unverified negative) |
| MEMENTO, [arXiv](https://arxiv.org/abs/2604.09852) (opened); Neural Garbage Collection, [arXiv](https://arxiv.org/abs/2604.18002) (opened); Forgetting Transformer, [arXiv](https://arxiv.org/abs/2503.02130) (search) | Learned self-eviction (SFT on 228K traces; RL on task reward; architectural forget gate). MEMENTO: removing KV of summarized blocks costs 15pp on AIME24 — KV states carry information the text does not. | datasets released; code not stated | idea only (all require training); MEMENTO's dual-stream finding is a caution for masking facts |
| Multi-Segment Attention / AsymCache, [arXiv](https://arxiv.org/abs/2606.02964) (opened) | Kernel for non-contiguous KV context with lossless evict/reconstruct. | code not stated | idea only — the kernel shape a serving version of our mask would need |

REUSE VERDICT: drop-in exists only inside HF transformers (and it is what we already use); adapt =
flex BlockMask for speed. No serving engine offers per-request persistent key masks with prefix
caching; the ship form stays HF custom code.

Risks: HF masking API churn between 4.5x and 5.x (astra found a 5.2.0 router-tuple trap; expect
the same for `create_masks_for_generate`); flex path compile time and decode q_len=1 overheads
must be measured, not assumed.

## P6. LARGER TEST (evaluation candidates; none may be fit on)

| Candidate | Fit to our question | License / cost | Verdict |
|---|---|---|---|
| EvoCode-Bench, [arXiv](https://arxiv.org/abs/2605.24110) (opened) | 26 stateful tasks, 5–15 rounds, workspace preserved, cumulative executable tests check new AND still-active prior requirements; MT@4 vs SR gap 22–40 points; Harbor multi-turn infra released. | license not stated; 227 rounds total | adapt — closest published analogue of our episode design; run once as an external sanity bank after our fresh bank |
| StaminaBench, [arXiv](https://arxiv.org/html/2606.19613v1) (opened) | Procedurally generated evolving REST-API specs, 100 turns, Docker HTTP verification, no LLM in spec/test generation; Python/JS/Rust. Requirements compound (no supersession). | "released for research use"; frontier cost $13–23K per config — irrelevant for short local runs | adapt — the GENERATOR is the reusable part: fresh, seedable, contamination-free episodes; add our own supersede/cancel events |
| SlopCodeBench, [arXiv](https://arxiv.org/abs/2603.24755) (opened) | 36 problems, 196 checkpoints; measures erosion/verbosity over iterations. | CC-BY-4.0 paper; code at scbench.ai | eval candidate (secondary) |
| SWE-EVO, [arXiv](https://arxiv.org/abs/2512.18470) (search); Long-Horizon-Terminal-Bench, [arXiv](https://arxiv.org/html/2607.08964) (opened) | 48 tasks x 21 files; 46 tasks x 9.8M tokens/task. | CC-BY-4.0 | no — far beyond one-GPU/30B budgets |
| ReBIND RELAPSE-Code (P2) | Revocation scripts with executable checkers — exactly "stale execution". | HumanEval-derived | eval-only candidate; do not fit; prefer our fresh bank |
| RuLES, [repo](https://github.com/normster/llm_rules) (opened) | 14 scenarios, programmatic rule checkers, vLLM local models. | Apache-2.0, v3.0 | adapt — cheap single-GPU adherence smoke test for the register+render stack |
| tau2-bench, [repo](https://github.com/sierra-research/tau2-bench) (opened) | Policy document in system prompt; DB-state grading; pass^k. | MIT | eval candidate (policy following), heavier tool sim |
| PrefEval, [repo](https://github.com/amazon-science/PrefEval), [LICENSE](https://raw.githubusercontent.com/amazon-science/PrefEval/main/LICENSE) (opened) | 3,000 pref/query pairs, explicit/implicit, 0–300 turns; has a "reminder" baseline (= rendering). | CC-BY-NC-4.0 | eval candidate (non-commercial) |
| MultiChallenge, [repo](https://github.com/ekwinox117/multi-challenge) (opened; LICENSE 404) | Instruction-retention axis; LLM judge. | unverified license | eval candidate (named in brief); judge cost |
| MemoryAgentBench (MIT), LongMemEval (MIT) (P2) | Knowledge-update / conflict-resolution facts. | MIT | eval candidates for the register, not for coding |
| AgentIF, [repo](https://github.com/THU-KEG/AgentIF) (opened; LICENSE 404) | Single-turn, 11.9 constraints/instruction. | unverified | low relevance |

REUSE VERDICT: adapt (StaminaBench-style generator + EvoCode-style cumulative tests for our own
fresh bank; RuLES as a cheap side-check). Evaluation-only names: EvoCode-Bench, RELAPSE-Code,
MultiChallenge, LongMemEval, PrefEval, MemoryAgentBench.

Risks: every public benchmark above becomes off-limits as fit/selection data the moment we name it
as an evaluation candidate (AGENTS.md rule); EvoCode/StaminaBench licenses unverified; Harbor
requires an adapter to our custom generate loop.

## P7. ANYTHING ELSE

| Item | What it is | Verdict |
|---|---|---|
| HF `custom_generate`, [docs](https://huggingface.co/docs/transformers/en/generation_strategies) (opened) | Hub or LOCAL `custom_generate/generate.py` (+ `requirements.txt`) replaces `generate()` for ANY model via `model.generate(custom_generate=..., trust_remote_code=True)`; a callable form reuses generate's input preparation and overrides only the loop. | drop-in precedent for the ship form: the focus controller (register, render, bias hook, keep-mask, journal) as a `custom_generate` package over unchanged Qwen3-30B-A3B shards — no model subclass, no re-upload of weights |
| Frontostriatal gating in transformers, [arXiv](https://arxiv.org/abs/2402.08211) (opened) | Trained on WM tasks, attention specializes into input-gating vs output-gating heads with role-addressable memory. | idea only — supports the parked head-gate closure test (Q6) |
| Lundqvist & Miller spatial computing, [Nat Commun 2023](https://www.nature.com/articles/s41467-023-36555-4), [TICS 2024 "Beta: bursts of cognition"](https://www.cell.com/trends/cognitive-sciences/fulltext/S1364-6613(24)00077-9) (search) | Control information (item order, which item is active) is carried by the spatial pattern of beta bursts, independent of item content in the recurrent weights. | idea only — the closest neuroscience analogue to "register decides, weights store": our register + mask is the control layer; nothing to import |
| Gated Attention (Qwen3-Next), [arXiv](https://arxiv.org/abs/2505.06708), [code](https://github.com/qiuzh20/gated_attention) (search; NeurIPS 2025 oral) | Per-head sigmoid gate after SDPA; attention-sink-free; shipped in Qwen3-Next-80B-A3B. | idea only — a future trunk with per-head gates would give a native per-head "focus" actuator; Qwen3-30B-A3B lacks it |
| VISTA proprioceptive dashboard (P3) | Render the runtime ledger (block ids, ages, archive status, budget) to the model each turn; +28pp over ReAct without training. | idea — render our mask/epoch state as text too, so the trunk knows what it can no longer see |
| Control system over frozen LLM harness, [arXiv](https://arxiv.org/abs/2607.25415) (opened) | Bandit/REINFORCE over prompt template, tools, memory, verification policy; CC-BY-4.0 code (dpaul0501/context-optimization-rl). | idea only |
| PolicyGuard, [arXiv](https://arxiv.org/abs/2606.29225) (opened) | Dialogue-grounded verifier sub-agent; tau2 airline pass^4 +6 to +12pp with half the blocking of argument-level guards. | idea only — product-side violation check reading the register; not for the registered run (no self-grading) |
| Learned prompt routers (MasRouter, RCR-Router, MetaGym) (search) | Route among LLMs/agents/system prompts. | nothing reusable for a single frozen trunk |

## TOP-5 "do this next" (ranked)

1. Fix admission where 44b actually failed: candidate generation. Build the token-level span
   tagger for check44c (BIO head on the existing encoder, or the LLM "tagging" strategy on
   Qwen3-1.7B), fix `Mrs.`/`;`/`:`-list splitting, register the splitter ceiling as its own bar.
   External data: none for admission; NLSI only for the scope/applicability matcher.
2. Add ReBIND-style tombstone lines for retired rules and a final-check block ordering to the
   every-request renderer; rerun the 42/40i-style bank (~20 GPU-min) to see whether tombstones cut
   stale execution WITHOUT masking. If yes, the mask's job shrinks to imitation of own outputs.
3. Run the ~20-min text-vs-text+bias check (my design review, section 3) before any serving work;
   only if the bias adds to rendered cues, spend a day on EasySteer/vLLM for a bias-only speed pilot.
4. Move the persistent keep-mask onto `create_masks_for_generate` + `and_mask_function`, then try
   the FlexAttention BlockMask backend for throughput; require parity on 40i records first.
5. Author the larger-test bank with a StaminaBench-style procedural generator (own seeds, own
   supersede/cancel/complete events, EvoCode-style cumulative tests); package the controller as a
   `custom_generate` directory; keep EvoCode-Bench/RELAPSE-Code/RuLES as evaluation-only side checks.

## TOP-3 things Brian may not be thinking of

1. The Snowball ceiling. Even restating every rule every turn leaves GPT-4o 20+ points below
   single-turn (65.3 vs 93.0). The residue is the model's commitment to its own earlier outputs —
   the one thing prompt harnesses cannot remove and our own-output mask (Z) can. That is the
   sharpest external framing for why the mask arm deserves its O vs O_off test, and why the test
   should measure "relapse" (ReBIND's word) on revoked rules, not only final success.
2. Ship form and serving already have slots for our two levers. HF `custom_generate` makes the
   controller a loadable directory over stock weights (no subclass, no reupload), and vLLM's fused
   MoE routers already carry a per-layer `(num_experts,)` bias tensor (`e_score_correction_bias`,
   `FusedTopKBiasRouter`). The semantics differ (selection-only vs our pre-softmax bias), so a
   one-hour check of whether selection-only bias reproduces 40c's 32/32 would tell us if the shipped
   actuator can be a 24 KiB tensor instead of a kernel.
3. "Knows-but-violates" is measurable prospectively. DriftBench (KBV 8–99%) and ReBIND (relapse
   probe AUROC 0.897) show that restatement is not adherence and that relapse risk is predictable
   from the dialogue before generation. A cheap CPU-side relapse probe could gate WHEN to apply the
   mask/bias (apply only when relapse risk is high), turning our always-on actuator into a
   triggered one — closer to Miller's bursts than a sustained bias, and cheaper.

## Unverified / not found (stated so nobody assumes otherwise)
Bandarkar routing code (not found); SGLang per-request custom masks (no API found; negative
unverified); RECAST license and prompt provenance; MultiChallenge, AgentIF, EvoCode-Bench,
StaminaBench licenses; EasySteer Qwen3-MoE support; vLLM FlexAttention per-request masks; the
"Span labeling with LLMs" paper (search snippet only); Rewiring-Experts code (none stated).
