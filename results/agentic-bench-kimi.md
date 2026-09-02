# Deep research — kimi-k3 with web tools (2026-09-02); 56 tool calls

I now have enough verified material (30+ pages opened). Writing the full report.

---

# Autonomous-benefit gate: external benchmark survey & design proposal
**Research date: 2026-09-02 · Researcher: kimi-k3 · Target model: frozen Qwen3-1.7B (hand-rolled trunk, bf16, single GB10, ~0.4 steps/s at hard cells; ~30 GPU-h budget)**

> **Cost model used throughout** (state your own constants against these): conservative step time **2.5 s/step** (your hard-cell harness rate) covers prefill≤8k + decode≤~300 tok at 1.7B; optimistic is ~1 s/step. "Episode GPU-h" = episodes × turns × trials × 2.5 s / 3600. Everything below is quoted in **both** arms where relevant.

---

## 1. TL;DR and ranked recommendation

**The uncomfortable finding:** almost every "agentic constraint retention" benchmark in the literature is either (a) **frontier-only** (no ≤3B open model has published numbers; a 1.7B will floor at ~0 pass rate, which cannot demonstrate *automatic mechanism benefit*), or (b) **LLM-judged** (echo-leakage confound you already worry about), or (c) **single-turn / short-context** (no real KV pressure). Only two families meet your triple constraint — *open, programmatic verifier, cheap at 1.7B, aged constraints with real eviction* — and they split the two roles in Brian's gate:

**Ranked:**
1. **τ²-bench (Sierra), retail domain first** — the only open, programmatically verified, *agentic* benchmark where "constraint stated early must hold late" is a first-class graded quantity (policy compliance + multi-step state), with a reliability metric (pass^k) designed for exactly the variance question you have. MIT-licensed code (fetched the LICENSE myself). **~14–18 GPU-h for base+treatment, k=4, retail.** Risk: 1.7B tool-competence floor → mitigations in §6 (prefilter + validity gate + telecom deferred).
2. **RULER variable-tracking (multi-hop tracing) at 8k/16k + MultiChallenge INSTRUCTION_RETENTION axis as the realism complement** — RULER-VT is the canonical synthetic "aged dependency chain" with exact-match verification and tunable length (real eviction >8k, still inside Qwen3-1.7B's trained 32,768-token context → no length-extrapolation confound). **~4–6 GPU-h total.** MultiChallenge's INSTRUCTION_RETENTION axis (3–19-turn human conversations, rubric-graded "YES/NO" per instance) is the cheapest *realistic* aged-constraint test in existence (266 conversations, **~4 GPU-h both arms**) and directly mirrors your ledger's use case — but it is LLM-judged, so it goes in as *secondary* with the transcript-hygiene protocol in §4.

Not recommended as primary: LongMemEval (115k-token histories ≫ the model's **trained 32,768** context — I verified this number on the Qwen3-1.7B model card — so results would be confounded by length extrapolation), τ^bench telecom/solo ablation, Vending-Bench (frontier-only, 1,076+ turns/run), AgentBench/WebArena/GAIA/SWE-bench (infra too heavy; details below with evidence).

---

## 2. Benchmark table

Legend: **V** = verified by me this session (quote in §7 ledger), **M** = from memory, unverified. GPU-h assume the cost model above, both arms, k trials as noted.

| Benchmark (arXiv / repo) | What it measures | Turns & tokens/episode | Verifier type | ≤3B open-model evidence | Saturation at frontier | License | Est. GPU-h @1.7B | Fit for gate |
|---|---|---|---|---|---|---|---|---|
| **τ²-bench** 2506.07982 · github.com/sierra-research/tau2-bench | Policy adherence + task completion + **communication** with an *active user* in a shared, tool-mediated state (Dec-POMDP) | Retail 115 tasks (**V**); ~8–20 turns/conv (M); policy doc + tool outputs ⇒ ~4–10k tok/episode | **Programmatic**: final DB-state equality + required action calls; user-sim is env-coupled, "user-commitment error 16%/6% with coupling" (**V**) | None published at ≤3B (**V**: paper's table is gpt-4.1/o4-mini/claude-3.7 at 34/42/49% pass^1) | Far from saturated: pass^1 34–49% (**V** on new tasks) | **MIT (V — fetched LICENSE, © 2025 Sierra Research)**; user-sim needs an API model externally | Retail, k=4, both arms: **14–18 GPU-h** (115×12 turns×4×2 / 3600×2.5 ≈ 9.6 h + slack; telecom ≈ +8 h) | ✅ **Primary agentic** |
| **τ-bench** 2406.12045 | Same as τ², single-control; retail+airline | ~10 turns/conv (M); ~4–8k tok | Programmatic DB-state vs goal + pass^k metric (**V**) | None at ≤3B published | gpt-4o "<50% … pass⁸ <25% in retail" (**V**) | Same Sierra repo (MIT, **V**) | ~8–12 GPU-h retail only | ✅ folded into τ² repo (revised τ domains included, **V**) |
| **RULER** 2404.06654 · github.com/hsiehjackson/RULER (**V**) | Synthetic long-context: NIAH variants + **variable tracking (multi-hop tracing)** + aggregation + QA w/ distractors | Single-turn, **controllable length 4k–128k** (**V**) | **Programmatic exact-match** | Paper's models are 7B–34B+; *no* 1.5–3B (**V**, model list 10 LMs 4k–128k); at 8k, 7B-class models mostly pass ⇒ room for floor/ceiling at 1.7B is unknown — must pilot | "only four models (GPT-4, Command-R, Yi-34B, Mixtral) maintain satisfactory performance at 32K" (**V**) | Repo exists (**V**); license M (likely Apache-2.0, NVIDIA) — verify before shipping data | VT+NIAH-MK @8k & 16k, 500 items each: **2–6 GPU-h** both arms | ✅ **Primary long-context retention** |
| **MultiChallenge** 2501.17399 · HF `ScaleAI/MultiChallenge` | Multi-turn w/ humans: **INSTRUCTION_RETENTION**, INFERENCE_MEMORY, SELF_COHERENCE, RELIABLE_VERSION_EDITING | **266 convs**, `num_turns` 3–19 (**V**, HF viewer), contexts ~1–3k tok | **LLM-as-judge w/ instance-level rubrics**, "fair agreement with expert raters" (**V**); rows have `pass_criteria=YES` rubric format (**V**) | None published at ≤3B | Frontier models still fail all four axes (abstract **V**; per-axis % M) | Data on HF (**V** exists); license field unread ⇒ **M** | ~2 GPU-h/arm ⇒ **~4 GPU-h total** (+ trivial judge API $) | ✅ Secondary (realistic aged constraints; short ctx ⇒ **no KV pressure**) |
| **"Lost in Multi-Turn"** 2505.06120 | Single-turn fully-specified vs **sharded multi-turn** instruction following across 6 generation tasks | Shards ~2–5 turns; short | Mix of task metrics (code/math exact; LLM judge for open tasks) (M) | Tested open-weight LLMs (**V** abstract); specific small-model rows M | "**average drop of 39%** across six generation tasks" multi- vs single-turn (**V**) | Code availability M (appendix claims) | ~1–2 GPU-h for a sharded subset | ✅ Diagnostic complement (mechanism: assumption/forgetting decomposition), not a gate bench |
| **AgentIF** 2505.16944 | IF under *agentic* instructions: "extended system prompts and detailed tool specs"; 707 instructions from 50 real agentic apps; **avg 1,723 words, max 15,630; avg 11.9 constraints** (**V**) | Single **turn** per instruction (no tool execution) | **Per-constraint programmatic verification spec**, executed as LLM "meta-prompts" (**V**: "construct meta prompts to assess the success of following each constraint") | Incl. **Qwen2.5-7B-Ins & GLM-4-9B-chat** (**V**) — 7–9B not 1.5–3B; "GPT-4o … highest success rate of 56.4% under strict condition" (**V**) | Not saturated | "Publicly available" (**V**); URL/license unread ⇒ **M** (likely thunlp repo) | **1–2 GPU-h** (+ judge API) | 🟡 Supplementary: exactly your Multi-IF result's nearest neighbor; no KV pressure, no episode |
| **SysBench** 2408.10943 | System-message following: constraint violation, instruction misjudgement, **multi-turn instability** | 5 rounds × 500 rows (**V**: "Six types of constraints … across five different domains"; HF viewer: 500 rows) | LLM judge against "**verdict sets**" that decouple constraint satisfaction from response quality (**V**) | Paper's roster M (likely ≥7B APIs) — no verified ≤3B | Reported systematic failures (**V** qualitative) | Repo exists (M: github `qinyanzhao/SysBench` — referenced in HELMET bib **V** only as citation); license M | ~2 GPU-h | 🟡 Supplementary (multi-round constraint aging, but short convs) |
| **Multi-IF** 2410.15553 | Multi-turn (3 rounds) multilingual IFEval extension | 3 turns; short | **Programmatic** (IFEval verifiers) | Paper roster includes ≤3B instruct models (M) | Frontier high single-turn, degrades across turns (M) | You already have it | — | ✅ Already in-house; matches your +2.8pt echo result |
| **LongMemEval** 2410.10813 · github.com/xiaowu0162/LongMemEval (**V**) | Long-term chat memory: extraction, **knowledge updates**, temporal reasoning, abstention | 500 QA; `_s` = "**115k tokens (~40 history sessions)** for Llama 3" (**V**); `_m` = 500 sessions (**V**) | LLM judge; eval needs `OPENAI_API_KEY` (**V**; README) | None at ≤3B; paper reports "30% accuracy drop" for commercial systems (**V**) | Not saturated | Repo LICENSE file exists (**V** exists; name unread ⇒ M, likely MIT); news: **"LongMemEval-V2: long-term memory in agentic context" (2026/05, V)** | Prefill-bound: 500×115k tok ≈ **6–12 GPU-h/arm** ⇒ 12–24 total | ❌ Primary; 🟡 optional slice (115k ≫ trained 32k ⇒ extrapolation confound) |
| **LoCoMo** 2402.17753 | Very-long-term conversational memory | "**300 turns and 9K tokens**" per conv (**V**, truncated abs); ~26–32 sessions (M) | LLM judge + F1 (M) | None ≤3B | Not saturated | M | ~6–10 GPU-h | 🟡 Interesting but judge-heavy |
| **ToolSandbox** 2408.04682 | **Stateful** tool use, implicit **state dependencies**, on-policy user sim, **on-device policy** & insufficient-info scenarios | ~2–6 turns, up to 17 tools (**V** examples) | **Programmatic** milestone/state matchers, "dynamic evaluation strategy" (**V**) | Smallest evaluated: Mistral-7B / Hermes-2-Θ-8B (**V** roster) | "open source and proprietary models … show significant performance gap" (**V**) | Apple sample-code license (M — verify before redistribution) | ~4–8 GPU-h (500-ish scenarios, M count) | 🟡 Strong conceptual match (policy + state), medium integration cost |
| **MINT** 2309.10691 | Multi-turn tool use + **language feedback** (k turns) | ≤5 turns + tool exec (**V** framework "access tools by executing Python code") | Programmatic (task success) (M) | None ≤3B | M | M (likely MIT) | ~6–10 GPU-h | 🟡 Feedback-usage, not constraint-aging |
| **AgentBench** 2308.03688 | 8 environments (OS, DB, webshop, …) | Long episodes, long ctx | Programmatic per env | "many OSS competitors … no larger than 70B" (**V**) — i.e., nothing at 1.7B | M | M | Docker fleet per env ⇒ infra dominates; **too heavy** | ❌ |
| **WebArena / VisualWebArena** 2307.13854 | Real web tasks on self-hosted sites | Long episodes | Programmatic (URL/state/function) | None small; success ~≤15% at GPT-4 era (M) | M | Site stacks to self-host ⇒ infra heavy | ❌ | ❌ |
| **GAIA** 2311.12983 | General assistant w/ web browsing | 466 questions (**V**); "GPT-4 with plugins 15% vs humans 92%" (**V**) | Exact-match answers | None small | Superhuman gap | M | Requires live web tools ⇒ confounded + heavy | ❌ |
| **SWE-bench(-lite)** | Repo issue resolution | Very long agent loops | Programmatic (tests) | 1.7B effectively zero | — | Apache (M) | ❌ infra + pass@ floor | ❌ |
| **BFCL v3/v4 (Gorilla)** (web search unreachable this session; leaderboard not fetched) | Function-calling AST accuracy; v3+ multi-turn state; v4 adds **agentic** (web-search/memory) | 1–10+ turns | Mostly **programmable AST/state** checks | **Small models exist on leaderboard** (xLAM-1B, Qwen2.5-1.5B rows — M) | M | Code Apache (M) | Medium; needs harness port to hand-rolled trunk | 🟡 Good for **base tool-competence calibration** (§6) rather than the gate itself |
| **CFBench** 2408.01122 | Constraint following breadth: 1,000 samples, 200+ scenarios, 10 categories/25+ subcategories (**V**) | Single-turn (M) | LLM judge w/ priority-aware rubrics (M) | M | M | "Data and code publicly available" (**V**); license M | ~1 GPU-h | 🟡 Supplementary |
| **RuleArena** 2412.08972 | Follow **complex real-world rules** (airline fees, NBA, tax) under long rule texts | Single-turn, long ctx (**V** "long-context understanding, logical reasoning, math") | Programmatic answers (M) | M | M | M | ~2–4 GPU-h | 🟡 Rules-as-context; not episodic |
| **Agent-SafetyBench** | Rule/safety adherence in agent settings | — | — | — | — | **Could not verify arXiv id** (2412.14439 turned out to be a superconductivity paper — do not cite) | — | ⛔ unresolved; skip unless Brian has the pointer |
| **Vending-Bench(2)** 2502.15840 · andonlabs.com/evals/vending-bench (**V**) | **Very-long-horizon coherence** in a simulated business; net worth metric | 1,076–2,000+ turns/run (**V**: transcript counters "1460/2000", "1076/1076"); 5 samples/model (**V**) | Programmatic outcome (net worth) | **Frontier-only leaderboard** (Gemini 3 Pro, Grok 4, GPT-5/5.1, Claude Opus 4 … $477–$4,694 net worth; human $844, **V**) | Even top models "meltdown" (**V** doom-loop transcript) | Eval page public; self-serve via contact (**V**) | Borderline ~10–20 GPU-h for 5 runs×2 arms, but **1.7B will produce degenerate runs** ⇒ uninformative | ❌ for gate; keep as stretch goal |
| **ConvBench / StructFlowBench / LongIF/LIFBench / IFEval-agent / "IFBench-multi-turn"** | — | — | — | — | — | **Search returned nothing for StructFlowBench; CFBench/AgentIF resolved to other ids.** I could not verify existence of ConvBench/StructFlowBench/LIFBench as published artifacts this session | — | ⛔ treat as non-candidates (if they exist, they're too obscure to convince a Hub reviewer anyway) |

**Honest summary for Q1's "reported scores at 1.5–3B":** in everything I opened, no benchmark publishes a ≤3B open-model row *except* Multi-IF (roster extends to sub-3B instruct models — **M**) and BFCL's leaderboard (small rows — **M**). This is itself a finding for the Hub story: *small-model agentic retention is unmeasured territory; your harness + τ² pilot would be among the first published 1.7B numbers.* It also means floor/ceiling at 1.7B must be established by a cheap pilot before committing the 30 GPU-h (see §4 step 0 and §6).

---

## 3. Q2 — "aged constraints" and real KV pressure

**Explicit "stated early, must hold late" structure** (mechanistic reason for your ledger to help):

- **τ/τ²-bench** — strongest fit among agentic benchmarks. The policy document is delivered once at the start; the graded quantity (DB-state equality + required actions) is only checkable *if policy constraints held at every intermediate step*; the user simulator introduces evolving demands. τ²'s paper itself frames the failure mode: agents must "keep track of its progress and adapt its communication" and failures include "not asking or asking for incorrect information" (**V**). The τ² user-simulator coupling exists *because* an unconstrained user sim lets agents "win without respecting instruction-following" (**V**) — i.e., the benchmark was redesigned specifically to keep instruction adherence load-bearing through the whole episode. With policy + tools + 10–20 turns, episode contexts hit ~4–10k ⇒ **eviction becomes real around an 8k KV budget.**
- **MultiChallenge INSTRUCTION_RETENTION** — textbook aged constraints, verified directly in the data I pulled: *"For the entire conversation, please do not use bold font"* checked 7 turns in; *four-word limit* rechecked at turn 3; *avoid the word "tradition"* at turn 3; *15-words-per-sentence limit rechecked mid-conversation*. 3–19 turns (**V**). **But no KV pressure** (contexts ~1–3k).
- **SysBench** — 5 multi-round dialogues per system instruction; "multi-turn instability" is an explicit axis (**V**). Short contexts.
- **RULER variable tracking** — the cleanest synthetic analog of "aged dependency": a variable binding introduced at hop 1 must survive N hops of rewriting across a controlled-length haystack, at **configurable 4k–128k** (**V**) ⇒ you can dial exactly the regime where your KV budget (≥8k) forces eviction, while staying <32k (inside Qwen3-1.7B's **verified** native context of 32,768 tokens).
- **LongMemEval knowledge-update axis** — information updated *across sessions* and questioned much later; real KV pressure (**~115k tokens for the `_s` split**, **V**) — but >32k ⇒ length-extrapolation confound for this base, as you found with your own "hard cells".
- **Lost-in-multi-turn sharded setting** — instructions arrive in shards and the model "makes wrong assumptions … attempts to answer before having all information / get lost" (**V**); aged-constraint-shaped but short horizon.
- **τ²-bench v1.0.1** note: Sierra shipped a July-2026 grading update ("banking_knowledge task errors … results produced with tau2-bench < 1.0.1 are not comparable", **V** from repo What's-New) ⇒ **pin ≥1.0.1** so your numbers remain comparable to the public leaderboard.

**KV-pressure >8k (eviction real, not simulated):** RULER @8k/16k (**V** controllable), LongMemEval-S (**V** ~115k), τ/τ² late-episode phases (~4–10k; borderline-real), Vending-Bench (1,000+ turns; **V**). MultiChallenge/SysBench/Lost-in-conversation: **no** — treat them as mechanism-fidelity checks, not KV-pressure tests.

---

## 4. Q3 — prior retention / re-injection / anchoring methods

| Method | What it does | Reported gains & model size | Confound handling | Verified? |
|---|---|---|---|---|
| **Re2 "Re-Reading"** 2309.06275 | Literally re-injects the question once more before answering ("Re-Reading the question as input … first pass could provide global information for the second pass" — **V**) | Reasoning benchmarks, Llama-1/2 7B–70B & chat models (M for exact deltas; abstract claims broad gains incl. with CoT) | None needed (same-token control trivial); evaluated on standard sets | Abstract **V**; numbers **M** |
| **Spotlighting** 2403.14720 (Microsoft) | Transforms/marks trusted vs untrusted spans so instructions stay anchored ("family of prompt engineering techniques … improve LLMs' ability to distinguish among multiple sources of input" — **V**); datamarking/delimiting/encoding modes | GPT-4-family, prompt-injection benchmark suite; ">50% improvement" in attack spotting phrase appears in full text (**V** via ar5iv) | They measure *task-performance impairment* alongside attack reduction (**V**) | **V** |
| **MemGPT** 2310.08560 | OS-paged virtual context: actively moves salient memory into/out of the window | "evaluate our OS-inspired design in two domains where the limited context windows … severely handicaps performance" — document analysis & conversational agents (**V** truncated abs; specific numbers **M**) | Compared against fixed-context baselines with equal info access (**M**) | **V**/M |
| **Instruction Hierarchy** 2404.13208 (OpenAI) | Trains priority ordering so system prompts survive later conflicting turns | Applied to GPT-3.5-scale (**) "drastically increases robustness — even for attack types" not seen in training (**V**) | Synthetic conflict data; held-out attack families | **V** |
| **Lost in the Middle** 2307.03172 | Not a method — the position-effect result that motivates echo-at-recency-bias placement: performance "highest when relevant information occurs at the beginning or end … significantly degrades in the middle" (**V**) | — | — | **V** |
| **Eviction-aware baselines** (H2O 2306.14048 / StreamingLLM 2309.17453 / SnapKV 2404.14469) | KV-cache eviction policies; relevant as **alternative uses of the same KV budget** you must beat under equal memory | — | — | arXiv ids from memory ⇒ **M** |

**How the literature handles your two confounds:**
1. **Verifier leakage from echoed text.** τ/τ² sidestep it entirely: the verifier is *environment state*, not generation text (**V**: "compares the database state at the end of a conversation with the annotated goal state"). MultiChallenge confronts it with "instance-level rubrics" and expert-agreement checking (**V**), but the judge still reads the transcript ⇒ *you must strip ledger echoes from judge-visible transcripts* (preregistered, §5). SysBench's "verdict sets" are exactly a decoupling device — satisfaction is judged against pre-written violation/fulfillment descriptions rather than raw quality (**V**). AgentIF pushes per-constraint programmatic specs executed via meta-prompts to reduce single-judge noise (**V**).
2. **LLM-judge bias / small-model idiosyncrasy.** HELMET replaced n-gram metrics with "reference-based model evaluation" and still warns NIAH "does not reflect differences across models" while open models "significantly lag behind closed ones when the task requires full-context reasoning or following complex instructions" (**V**) — i.e., even with model-based grading, long-context IF deficits at small scale are real, big, and *not* verifier artifacts. That is encouraging for your result being legible at 1.7B.

---

## 5. Q4 — smallest credible gate design (preregistration draft)

### 5.0 Step 0 — calibration pilot (~3 GPU-h, before committing)
Run **base-only** on τ²-retail subset (n=30 tasks, k=2, GPT-4o-mini user sim) + RULER-VT@8k (n=250). **Proceed only if:** base pass^1(retail subset) ∈ [0.05, 0.70] (power band), valid-tool-call rate ≥ 0.80, RULER-VT@8k base ∈ [20%, 90%]. Else: apply the §6 scaffold fix once; if still floored, the agentic half of the gate drops to MultiChallenge+RULER only (pre-registered fallback).

### 5.1 Arms (paired, same RNG seeds & task order)
- **A — base + equal-context control:** same total injected tokens as the ledger echo, but sampled from **low-salience spans** (random-span echo at identical positions), **no KV pinning**. This is the control Brian's gate demands: *base gets the same tokens without selection.*
- **B — ledger (the mechanism):** salience-selected spans pinned via `KVCache.evict keep=` + one-line echoes.
- **C — echo-only** (ablation you already have in-house): echo without pinning — keeps the decomposition interpretable; not required for the gate claim but cheap.

### 5.2 Benchmarks & estimands
**Primary agentic estimand (τ²-retail, k=4 trials, pin code ≥ v1.0.1):**
- Estimand: paired per-task success-rate difference Δ = pass^k(B) − pass^k(A) over the 115 retail tasks; **McNemar** on discordant episode pairs; **cluster bootstrap 95% CI clustered by task_id** across trials.
- Secondary: programmatic **policy-violation rate** (from state/action assertions), per-episode **turns-to-first-violation** (survival analysis — direct evidence for "constraint holds later"), and **user-sim round-efficiency** (τ²'s communication metric — does the model ask for info the ledger preserved?).

**Primary long-context retention estimand (RULER-VT + NIAH-MK, 8k & 16k, 500 items ea):**
- Estimand: paired accuracy Δ(B−A) per length; cluster bootstrap by (task,seed); exact-match verifier = no judge confound.

**Secondary realism:** MultiChallenge INSTRUCTION_RETENTION axis, **echo-stripped transcripts** to judge; McNemar per conversation.

### 5.3 Safety / sanity gates (auto-void conditions)
1. **Degeneration gate:** rep-3/self-BLEU degeneration rate (B) ≤ (A)+1pp; else void run (your wave-bias failure mode, pre-codified).
2. **Tool-validity gate:** valid-call rate (B) ≥ (A)−3pp on τ².
3. **Truncation/token-parity gate:** mean generated tokens & truncation incidence within ±10% across arms; echo token budget identical; **prefill/decode wall-clock logged** so "benefit per GPU-s" is reportable.
4. **Judge-hygiene gate (MultiChallenge only):** judge sees echo-stripped transcript; a separate *with-echo* judging pass is run as a **leakage check** — if with-echo ≫ stripped, the gain is attributed to verifier leakage and voided.
5. **Length-control gate:** Δ at 8k must be ≳ Δ at 4k-control subset (no eviction regime) — evidence that benefit is *retention-under-pressure*, not generic recency padding.

### 5.4 Falsifiers (what would kill "automatic benefit for agentic work")
- F1: CI of Δ(B−A) contains 0 on τ²-retail **and** on RULER-VT@16k.
- F2: Δ(A) alone ≈ Δ(B−base-noecho): random low-salience echoes deliver the same gain ⇒ *selection* is not causal; mechanism degenerates to "any prompt-echo helps".
- F3: Gain appears only in the no-eviction subset (gate 5 fails) ⇒ benefit is not tied to KV-preservation at all.
- F4: τ² gain concentrates in episodes where echoes leaked into judge-visible state (gate 4 fails on MultiChallenge).
- F5: Echo-only arm (C) ≥ B everywhere ⇒ KV pinning component adds nothing (the text-ledger result you already have would stand alone — publishable but weaker claim).

### 5.5 Budget
| Item | GPU-h (conservative) |
|---|---|
| Step-0 pilot | ~3 |
| τ²-retail: 115 tasks × ~12 turns × 2.5 s × k=4 × arms A,B | ~9.6 → **~12** with overhead |
| RULER-VT/MK @8k+16k, A,B | ~6 |
| MultiChallenge axis A,B | ~4 |
| Buffer/reruns | ~5 |
| **Total** | **≈ 30 GPU-h** ✅ |

---

## 6. Q5 — can Qwen3-1.7B even run the scaffold? (base-competence risk)

Evidence I verified this session:
- The **official Qwen3-1.7B model card declares "Expertise in agent capabilities, enabling precise integration with external tools"** and ships an "Agentic Use" section using **Qwen-Agent** with a `<tools>`/`<tool_call>` chat-template (**V**, model card text + template fetched). Context: **32,768 tokens** native; YaRN recommended for up to 131,072 (**V**). License **Apache-2.0** (**V**).
- τ²'s user-sim is itself a model API (their `simulator_guidelines.md`, error modes documented — **V**); nothing requires agent-side APIs, but **all τ² published numbers are ≥ gpt-4o-mini-class models** (**V**).
- The literature consistently shows open/small models collapse in exactly these settings: AgentBench — OSS ≤70B gap (**V**); ToolSandbox — smallest tested 7–8B and "significant performance gap" (**V**); AgentIF — smallest verified 7–9B, GPT-4o at 56.4% strictly (**V**); Lost-in-multi-turn — *all* tested open/closed models drop, avg 39% (**V**).

**Implication:** at 1.7B the binding risk is **tool-call validity**, not retention. Mitigations (preregister): (i) step-0 pilot with the 0.80 validity gate; (ii) a *scaffold equalization*: retry-once-with-error-message on malformed tool calls **in both arms** (τ² already supports this pattern), so the benchmark measures retention on the subset where the base can act at all; (iii) prefilter τ² tasks to those where base reaches ≥1 valid call in the pilot (paired subset fixed before treatment runs — no post-hoc cherry picking); (iv) report validity as a headline safety metric (§5.3). If the floor persists, the honest fallback claim is *"automatic benefit under KV pressure at 1.7B-scale chat workloads"* (RULER + MultiChallenge + your existing Multi-IF result), with the agentic result deferred to a ≥7B sister model.

**Also worth knowing:** LongMemEval's repo announced "**LongMemEval-V2: long-term memory in agentic context**" (May 2026, **V**) — if released before you finish, check whether it's programmatically graded; it could become the ideal secondary agentic-memory benchmark.

---

## 7. Verified vs from-memory ledger

**VERIFIED this session (fetched & quoted):**
1. τ²-bench paper, arXiv:2506.07982 — Dec-POMDP telecom, "compositional task generator", "user-commitment error rate of 16% on Retail and 6% on Airline, against 40% and 12% (GPT-4.1)"; "~20% drop in performance for all models" under dual-control; agent-only: "14% and 11% on Airline and Retail"; pass^1 "just 34% (gpt-4.1), 42% (o4-mini), 49% (claude-3.7-sonnet)" on new tasks; "revised versions of the Airline and Retail domains"; "115 tasks in the Retail domain".
2. τ-bench paper, arXiv:2406.12045 — "compares the database state at the end of a conversation with the annotated goal state"; pass^k; "gpt-4o succeed on <50% … pass^8 <25% in retail".
3. Sierra repo `github.com/sierra-research/tau2-bench` — **MIT License, © 2025 Sierra Research** (raw LICENSE fetched); July-2026 v1.0.1 grading update + "banking_knowledge" note; active leaderboard.
4. Lost-in-multi-turn, arXiv:2505.06120 — "average drop of 39% across six generation tasks"; "200,000+ simulated conversations"; assumption/forgetting decomposition.
5. LongMemEval, arXiv:2410.10813 + repo — 500 questions, five abilities; "30% accuracy drop"; "_s ~115k tokens (~40 history sessions)"; "_m 500 sessions"; GPT-4 judge w/ `OPENAI_API_KEY`; ICLR 2025; **LongMemEval-V2 (agentic context), 2026/05 news item**.
6. Multi-IF, arXiv:2410.15553 — multi-turn + multilingual IF benchmark over IFEval taxonomy.
7. MultiChallenge, arXiv:2501.17399 + HF viewer — 266 rows; axes incl. INSTRUCTION_RETENTION; `num_turns` 3–19; rubric `pass_criteria/YES` judge format; aged-constraint examples quoted verbatim in §3.
8. SysBench, arXiv:2408.10943 (+ ar5iv) — six constraint types, five domains, 5 rounds, 500 rows (HF), "verdict sets" decoupling; multi-turn instability axis.
9. AgentIF, arXiv:2505.16944 (+ ar5iv) — 707 instructions, 50 apps, avg 1,723 words / max 15,630; avg 11.9 constraints; system-prompt avg 1,704 words vs user 19.1; GPT-4o 56.4% strict; meta-prompt per-constraint verification; code released.
10. RULER, arXiv:2404.06654 (+ ar5iv) — 13 tasks; variable-tracking multi-hop tracing; 4k–128k controllable; exact-match; repo `hsiehjackson/RULER`; "only four models … maintain satisfactory performance at 32K".
11. HELMET, arXiv:2410.02694 (+ ar5iv) — 7 categories, lengths to 128k, 51 LCLMs; NIAH saturated; open models lag "when the task requires full-context reasoning or following complex instructions."
12. AgentBench 2308.03688 — 8 environments; OSS ≤70B gap. 13. WebArena 2307.13854 — self-hosted realistic sites. 14. MINT 2309.10691 — tools + language feedback framework. 15. ToolSandbox 2408.04682 — stateful, on-policy user sim, on-device policy scenarios; smallest models evaluated 7–8B (roster quoted). 16. LoCoMo 2402.17753 — "300 turns and 9K tokens". 17. GAIA 2311.12983 — "92% [humans] vs 15% GPT-4 … plugins". 18. CFBench 2408.01122 — 1,000 samples, 200+ scenarios, 10/25+ categories. 19. RuleArena 2412.08972 — airline/NBA/tax long-context rules. 20. Re2 2309.06275; 21. Spotlighting 2403.14720; 22. MemGPT 2310.08560; 23. Instruction Hierarchy 2404.13208; 24. Lost-in-the-Middle 2307.03172.
25. Qwen3-1.7B model card (HF raw) — **Apache-2.0**; 28 layers, 16 Q / 8 KV heads; **context 32,768**; agentic Qwen-Agent usage + tool template; decoding defaults (temp 0.7/top-p 0.8/top-k 20, presence-penalty 1.5 for repetition).
26. Vending-Bench page (andonlabs; paper 2502.15840) — 1,076–2,000-turn runs; 5 samples/model; frontier-only leaderboard incl. Gemini 3 Pro, Grok 4, GPT-5/5.1, Claude Opus 4/Sonnet 4.5, human baseline $844; v1 deprecated for Vending-Bench 2 (2025-11-18); "meltdown" pathology documented.

**UNVERIFIED (memory / unopened):**
- RULER/HELMET/MINT/ToolSandbox/LoCoMo/MultiChallenge/AgentIF/SysBench/CFBench **license specifics** (repos exist; check before redistributing data).
- Multi-IF ≤3B roster rows; per-number gains of Re2; MemGPT model backends & figures; H2O/StreamingLLM/SnapKV arXiv ids; BFCL small-model leaderboard rows (xLAM-1B etc.); τ-bench mean conversation length; MultiChallenge per-axis frontier numbers; Lost-in-conversation repo URL.
- **Agent-SafetyBench: I failed to locate it** (the candidate ID 2412.14439 resolves to a superconductivity paper) — do not cite without a new pointer.
- **ConvBench, StructFlowBench, LongIF/LIFBench, "IFEval-agent": searches returned nothing** — I could not verify these exist as published artifacts; a Hub-facing claim shouldn't lean on them anyway.

---

## 8. What you might be missing (beyond the brief)

1. **A license sweep is owed before Hub upload**: τ² MIT and Qwen3 Apache-2.0 are clean and verified; everything else in the secondary stack (MultiChallenge, AgentIF, SysBench, RULER data) needs its LICENSE file read — 15 minutes of work, done *before* the run, not after.
2. **τ² v1.0.1 pin** (grading fix, July 2026): unpinned runs today would be non-comparable tomorrow.
3. **Communication is the hidden aged-constraint surface of τ²**: "not asking for information that the ledger preserved" is exactly the failure your echo is positioned to fix — preregister the round-efficiency metric so reviewers see the mechanism, not just pass^k.
4. **Equal-context control subtlety**: your random-span control should sample from the *same document regions* the salience finder ignores (don't echo from the user turn you're about to answer — that would leak). Also fix injection position (immediately pre-assistant-turn) in both arms.
5. **Vending-Bench as the stretch demo**: if the gate passes, one 1.7B run of Vending-Bench-2 (or the v1 sim, open-sourced) with/without the ledger is a compelling qualitative figure — long-horizon stability is exactly where frontier models "meltdown", so a small model surviving longer *because it re-anchors its operating constraints* is a story no IF benchmark can tell. Not for the gate; for the Hub demo reel.

**Bottom line for Brian's gate:** run **τ²-retail (v1.0.1, k=4) with the equal-context random-echo control** as the agentic prong and **RULER-VT @8k/16k + MultiChallenge-IR (echo-stripped judging)** as the retention prong, with the five void conditions pre-registered. ~30 GPU-h. The whole design is built so that a null result is still publishable ("selection doesn't matter / echo is sufficient at 1.7B") and a positive result is confound-resistant in exactly the two ways (verifier leakage, judge bias) the literature has already established tooling to detect.

## Tool log
[1] web_search({"query": "tau2-bench arxiv Sierra telecom agentic benchmark 2025"}) -> 3697 chars
[2] web_search({"query": "SysBench arxiv \"system message\" instruction following multi-turn benchmark"}) -> 433 chars
[3] web_search({"query": "AgentIF arxiv instruction following agentic scenarios benchmark 2025"}) -> 938 chars
[4] web_search({"query": "MultiChallenge arxiv Scale AI multi-turn conversation benchmark instruction retention"}) -> 475 chars
[5] web_search({"query": "StructFlowBench arxiv structured workflow benchmark"}) -> 102 chars
[6] web_search({"query": "BFCL v3 Berkeley function calling leaderboard multi-turn arxiv"}) -> 479 chars
[7] web_search({"query": "\"LLMs Get Lost in Multi-Turn Conversation\" arxiv Laban Microsoft"}) -> 102 chars
[8] web_search({"query": "ToolSandbox Apple arxiv stateful conversational tool use benchmark on-device policy"}) -> 477 chars
[9] web_fetch({"url": "https://arxiv.org/abs/2506.07982"}) -> 4560 chars
[10] web_fetch({"url": "https://arxiv.org/abs/2406.12045"}) -> 4094 chars
[11] web_fetch({"url": "https://arxiv.org/abs/2505.06120"}) -> 4277 chars
[12] web_fetch({"url": "https://arxiv.org/abs/2410.10813"}) -> 4822 chars
[13] web_fetch({"url": "https://arxiv.org/abs/2410.15553"}) -> 5091 chars
[14] web_fetch({"url": "https://arxiv.org/abs/2501.17399"}) -> 4378 chars
[15] web_fetch({"url": "https://arxiv.org/abs/2408.10943"}) -> 4648 chars
[16] web_fetch({"url": "https://arxiv.org/abs/2505.16944"}) -> 4957 chars
[17] web_fetch({"url": "https://arxiv.org/abs/2404.06654"}) -> 4712 chars
[18] web_fetch({"url": "https://arxiv.org/abs/2308.03688"}) -> 4634 chars
[19] web_fetch({"url": "https://arxiv.org/abs/2307.13854"}) -> 5155 chars
[20] web_fetch({"url": "https://arxiv.org/abs/2309.10691"}) -> 5293 chars
[21] web_fetch({"url": "https://arxiv.org/abs/2408.04682"}) -> 4466 chars
[22] web_fetch({"url": "https://arxiv.org/abs/2410.02694"}) -> 5168 chars
[23] web_fetch({"url": "https://arxiv.org/abs/2401.16745"}) -> 4695 chars
[24] web_fetch({"url": "https://arxiv.org/abs/2402.17753"}) -> 4663 chars
[25] web_fetch({"url": "https://arxiv.org/abs/2309.06275"}) -> 4706 chars
[26] web_fetch({"url": "https://arxiv.org/abs/2403.14720"}) -> 4449 chars
[27] web_fetch({"url": "https://arxiv.org/abs/2310.08560"}) -> 4448 chars
[28] web_fetch({"url": "https://arxiv.org/abs/2404.13208"}) -> 4163 chars
[29] web_fetch({"url": "https://arxiv.org/abs/2412.08972"}) -> 4823 chars
[30] web_fetch({"url": "https://arxiv.org/abs/2412.10601"}) -> 5453 chars
[31] web_fetch({"url": "https://github.com/sierra-research/tau2-bench"}) -> 9000 chars
[32] web_fetch({"url": "https://github.com/QwenLM/Qwen3"}) -> 9000 chars
[33] web_search({"query": "CFBench \"constraints-following\" benchmark LLM arxiv 2412"}) -> 102 chars
[34] web_search({"query": "Berkeley Function Calling Leaderboard v4 agentic multi-turn results gorilla"}) -> 471 chars
[35] web_fetch({"url": "https://huggingface.co/Qwen/Qwen3-1.7B"}) -> 9000 chars
[36] web_fetch({"url": "https://ar5iv.labs.arxiv.org/html/2505.16944"}) -> 9000 chars
[37] web_fetch({"url": "https://ar5iv.labs.arxiv.org/html/2408.10943v2"}) -> 9000 chars
[38] web_fetch({"url": "https://github.com/NVlabs/RULER"}) -> 449 chars
[39] web_fetch({"url": "https://ar5iv.labs.arxiv.org/html/2506.07982"}) -> 9000 chars
[40] web_search({"query": "github microsoft \"lost in conversation\" OR \"lost_in_conversation\" multi-turn LLM code"}) -> 178 chars
[41] web_fetch({"url": "https://github.com/HSUNAH/RULER"}) -> 449 chars
[42] web_fetch({"url": "https://github.com/xiaowu0162/LongMemEval"}) -> 9000 chars
[43] web_fetch({"url": "https://raw.githubusercontent.com/sierra-research/tau2-bench/main/LICENSE"}) -> 1067 chars
[44] web_fetch({"url": "https://huggingface.co/Qwen/Qwen3-1.7B/raw/main/README.md"}) -> 9000 chars
[45] web_search({"query": "\"CFBench\" constraints-following benchmark large language models"}) -> 439 chars
[46] web_search({"query": "gorilla \"BFCL\" v4 release blog agentic category"}) -> 102 chars
[47] web_fetch({"url": "https://arxiv.org/abs/2412.14439"}) -> 5448 chars
[48] web_fetch({"url": "https://arxiv.org/abs/2311.12983"}) -> 4173 chars
[49] web_fetch({"url": "https://arxiv.org/abs/2408.01122"}) -> 4687 chars
[50] web_fetch({"url": "https://huggingface.co/datasets/ScaleAI/MultiChallenge"}) -> 9000 chars
[51] web_fetch({"url": "https://andonlabs.com/evals/vending-bench"}) -> 8682 chars
[52] web_fetch({"url": "https://ar5iv.labs.arxiv.org/html/2410.02694"}) -> 9000 chars
[53] web_search({"query": "gorilla.cs.berkeley.edu BFCL v4 blog multi-turn agentic"}) -> 102 chars
[54] web_search({"query": "Laban \"lost in conversation\" multi-turn github code microsoft LMOps"}) -> 102 chars
[55] web_fetch({"url": "https://arxiv.org/abs/2307.03172"}) -> 4548 chars
[56] web_fetch({"url": "https://ar5iv.labs.arxiv.org/html/2404.06654"}) -> 9000 chars
