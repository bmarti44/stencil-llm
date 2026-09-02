# Agentic / long-horizon benchmark research for the PUBLISH GATE (fable, 2026-09-02)

Scope: answer the five questions in the 2026-09-02 brief (scratchpad/agentic-bench-brief.md) for a frozen
Qwen3-1.7B trunk with the retention/re-injection ledger (salience2 finder + KV pinning + one-line echo).
Method: 32 web sources opened (arXiv abstract/HTML pages, GitHub READMEs, leaderboards); every number below is
tagged VERIFIED (read on the page this session, URL given) or MEMORY (not opened; treat as a claim to recompute).
Repo context read (read-only): results/research-synthesis.md, LEDGER-PLAN.md PUBLISH GATE + ROUND 7 + RE-SCOPE v2,
WORKLOG.md runtime envelope (19.74 tok/s at depth; 39 h ceiling for the 2727-turn Multi-IF run).

Throughput unit used for every GPU-hour estimate (from the WORKLOG envelope, not remeasured): decode ~20 tok/s at
depth, so one assistant turn costs ~20-25 s at a typical 300-450-token reply and ~50 s when it runs to
max_new=1024 (truncation). Prefill below 8k tokens is small next to decode; at 16-32k it is not, so SEQUOR-style
50-turn episodes are budgeted at 1.5x. "Arm" = one full pass of the benchmark with one configuration.

---------------------------------------------------------------------------------------------------------------
## 1. Benchmark table (open benchmarks that touch long-horizon constraint retention in agentic / multi-turn settings)

Columns: what it measures | episode shape (turns / tokens) | verifier | runnable on open weights locally |
reported ~1.5-3B (or nearest small) scores | saturation | license | compute per FULL run at our throughput (one arm).

### A. Agentic / tool-use

**tau-bench (arXiv 2406.12045) / tau2-bench (arXiv 2506.07982; github.com/sierra-research/tau2-bench)** — VERIFIED
- Measures: policy-constrained customer-service agents (retail/airline/telecom) with a simulated user; success =
  final DB state equals goal state (+ action/NL assertions in tau2). pass^k reliability metric.
- Episode: 115 retail / 50 airline / 114 telecom tasks (tau2 paper); dozens of turns, 5-15k tokens per episode
  with policy doc + tool schemas (token count MEMORY).
- Verifier: programmatic (DB state + action match); NL assertions judged (tau2 telecom).
- Open weights: yes via LiteLLM, but the USER SIMULATOR is an LLM (paper: gpt-4.1-2025-04-14; leaderboard doc
  recommends gpt-5.2; any LLM allowed, reported on the board).
- Small-model scores: Qwen3-1.7B base tau-bench retail 6.1 / airline 14.0 (Fission-GRPO, arXiv 2601.15625 Table 1,
  VERIFIED). OpenRouter tau2-airline board: Llama-3.1-8B 30.9%, Qwen2.5-7B 16.7% (VERIFIED). tau2 paper evaluated
  proprietary only (VERIFIED). tau2 telecom Qwen3-4B-Instruct-2507 27% (search snippet from arXiv 2511.08042,
  not confirmed in the PDF body: MEMORY-grade).
- Saturation: none at this scale; the problem is the FLOOR (1.7B at 6-14%).
- License: MIT (tau2-bench repo, VERIFIED); paper CC BY 4.0.
- Compute: ~280 tasks x ~15 agent turns x 4 trials ≈ 17k turns/arm ≈ 100+ GPU-h/arm plus simulator API spend.
  OUT for the gate (floor + cost + simulator nondeterminism).

**BFCL v3/v4 multi-turn (gorilla.cs.berkeley.edu; github ShishirPatil/gorilla)** — VERIFIED
- Measures: multi-turn function calling against executable backends (file system, trading, travel, ...);
  categories multi_turn_base / miss_func / miss_param / long_context, 200 entries each (v3 blog 13; 1000 incl.
  composite). v4 adds memory_kv/vector/rec_sum and web_search categories (TEST_CATEGORIES.md).
- Episode: several user turns, each requiring one or more calls; long_context variant injects "hundreds of files
  or thousands of records" (no token count published; MEMORY: tens of k tokens).
- Verifier: fully programmatic — state-based (backend state after each turn) AND response-based (ground-truth
  call sequence must be a subset of the trajectory); both must pass every turn.
- Open weights: yes (`bfcl generate --backend vllm --local-model-path ...`, README VERIFIED). Our hand-rolled
  trunk would need a handler shim (not vLLM) — engineering cost, not GPU cost.
- Small-model scores: Qwen3-1.7B (untrained) BFCL v4 multi-turn overall 7.80% = base 10.0 / miss_func 11.0 /
  miss_param 8.0 / long_ctx 2.5 (Fission-GRPO Table 1, VERIFIED; sampling T=0.95, 12.8k prompt cap). Qwen3
  tech report BFCL v3 OVERALL 52.2 non-thinking / 56.6 thinking (Tables 19-20, VERIFIED) — the overall is
  dominated by single-turn AST categories. xLAM-2-3b-fc-r multi-turn 56.0%, Qwen3-4B multi-turn 15.75% base
  (search snippets, MEMORY-grade).
- Saturation: none; floor is the issue for 1.7B.
- License: Apache-2.0 (README: leaderboard data and stats, VERIFIED).
- Compute: 200 entries x ~4 turns x ~25 s ≈ 6 GPU-h/arm for one category; base+long_context ≈ 12 GPU-h/arm.
  Cheap, but at 2.5-10% base accuracy the paired difference is almost all zeros (see Section 5).

**AgentIF (arXiv 2505.16944; github THU-KEG/AgentIF)** — VERIFIED
- Measures: instruction following inside long agent system prompts: 707 instructions from 50 real agentic apps,
  avg 11.9 constraints, avg 1,723 words (max 15,630), incl. tool-spec and conditional constraints.
- Episode: SINGLE-TURN (system + user in one input; README data format VERIFIED). No aging.
- Verifier: code / LLM (gpt-4o-2024-11-20 recommended) / hybrid.
- Small-model scores: not in abstract/README (paper says "current models generally perform poorly").
- License: repo LICENSE not found (404) — UNKNOWN.
- Compute: 707 x 1 turn x ~30 s ≈ 6 GPU-h/arm. Not a retention benchmark (single turn) — OUT as primary;
  usable only as a long-system-prompt "buried constraint" set.

**HANDBOOK.md (arXiv 2607.25398; github surge-ai/handbook)** — VERIFIED
- Measures: agent obeys a 14.9k-token-median company handbook (8.3k-79.4k) over ~30 tool calls in an MCP
  environment; 65 tasks, 824 programmatic criteria (Expected-Output + Incorrect-Behavior), strict pass@1.
- Verifier: fully deterministic Python checks on final workspace/service state — the best verifier in this list.
- Scores: Claude Fable 5 36.2%, frontier 21-23%, efficiency tier 3-13%, worst 0.8%. No small open model.
- License: CC BY 4.0 (paper), Apache-2.0 (repo). Needs Docker + Harbor + OpenHands scaffold.
- Compute: 65 tasks x 30 tool calls x 3 trials, with 15-80k-token prefill per step: ~30-60 GPU-h/arm at our
  throughput, and Qwen3-1.7B is predicted at ~0% (efficiency-tier frontier models are 3-13%). OUT (floor).

**Lost in Conversation / sharded simulation (arXiv 2505.06120, ICLR 2026; github microsoft/lost_in_conversation)** — VERIFIED
- Measures: an instruction is split into 2-8 shards revealed one per user turn; the model must integrate all
  shards (each an early-stated constraint) into a final answer. 600 sharded instructions (90-120 per task);
  tasks: code (HumanEval-style unit tests), database (Spider SQL execution), actions (BFCL-style function calls),
  math (GSM8K exact answer), data2text and summary (LLM judge), translation.
- Episode: 2-8 user turns; ~1-3k tokens (MEMORY: short). No KV pressure.
- Verifier: programmatic for code/database/actions/math; LLM for data2text/summary.
- Simulator: GPT-4o-mini picks/rephrases the next shard, classifies strategy, extracts answers (VERIFIED). So the
  user side is NOT fixed — cross-arm comparisons must fix seed/shard order and accept residual simulator noise.
- Small-model scores: FULL -> SHARDED: Llama-3.1-8B 47.8 -> 20.5 (-57%), OLMo-2-13B 51.0 -> 17.5, Phi-4
  54.3 -> 30.4, Llama-3.3-70B 63.3 -> 42.0 (VERIFIED). No 1-3B model; extrapolated 1.7B sharded ≈ 10-15.
- Built-in controls: RECAP (one final turn restating all shards: GPT-4o 59.1 -> 76.6) and SNOWBALL (repeat all
  revealed shards every turn: 59.1 -> 65.3) (VERIFIED). Temperature 0 does not fix the multi-turn loss
  (VERIFIED). These are exactly the "re-injection ceiling" and "superset re-injection" controls we need.
- License: MIT (VERIFIED). Runner is OpenAI/Azure-keyed; local model needs an adapter (README VERIFIED).
- Compute: programmatic subset (actions + database + math ≈ 300 instr) x ~5 turns x ~25 s ≈ 10 GPU-h/arm;
  all 600 ≈ 20 GPU-h/arm. Simulator API cost is small (4o-mini).

**MINT (arXiv 2309.10691; github xingyaoww/mint-bench)** — VERIFIED (abstract + repo listing only)
- Multi-turn tool use (python execution) with GPT-4-simulated language feedback, up to 5 turns, 8 datasets.
  Verifier programmatic per dataset. License MEMORY (Apache-2.0?). Constraints are not aged; the loop tests
  tool-feedback repair, not retention. OUT as primary.

**AgentBench (arXiv 2308.03688; github THUDM/AgentBench)** — VERIFIED (search-level)
- 8 environments (OS, DB, KG, card game, lateral thinking, house-holding, web shopping, web browsing);
  Apache-2.0. Heavy infra; OSS < 70B far behind API models. No retention structure. OUT.

**Agent-SafetyBench (arXiv 2412.14470; github thu-coai/Agent-SafetyBench)** — VERIFIED (search-level)
- 349 environments, 2,000 cases, safety score via judge; MIT. Rule adherence but safety-flavoured, LLM-judged.
  OUT for the gate.

**MemoryAgentBench (arXiv 2507.05257, ICLR 2026; github HUST-AI-HYZ/MemoryAgentBench)** — VERIFIED
- Long texts chunked and injected incrementally ("inject once, query many"); competencies AR / TTL / LRU / CR;
  verifiers substring-EM / EM / Recall@5, LLM-judge only for the LongMemEval and InfBench portions. MIT.
  Context: long (100k+ class, MEMORY). It measures memory of FACTS, not constraints on behaviour. Candidate for
  the long-context leg only if we accept fact retrieval as the estimand — it is not the mechanism's job.

### B. Multi-turn instruction / system-prompt retention (chat, no tools)

**Multi-IF (arXiv 2410.15553; github facebookresearch/Multi-IF)** — VERIFIED (we have it)
- 4,501 x 3-turn IFEval-style conversations, 8 languages; programmatic (strict/loose, instruction/conversation
  level); Apache-2.0. Per-turn: Llama-3.1-8B 0.688 / 0.615 / 0.542; o1-preview 0.877 -> 0.707 (VERIFIED).
  Qwen3-1.7B official Multi-IF 44.7 non-thinking / 51.2 thinking (Qwen3 report, VERIFIED). ~2-4k tokens:
  no KV pressure; eviction must be simulated. Our 909 cohort is already the registered primary P.

**SysBench (arXiv 2408.10943; github PKU-Baichuan-MLSystemLab/SysBench)** — VERIFIED
- 500 system messages x 5 fixed user turns (2,500 turns; 1,951 aligned / 549 misaligned); 6 constraint types;
  dependent vs parallel dialogues. Metrics CSR / ISR / SSR; judge GPT-4o. Scores: GPT-4o 87.1/76.4/54.4;
  Llama-3.1-8B 66.5/46.9/24.9; Qwen2-7B 47.0/26.9/15.0; GLM-4-9B 64.2/44.0/25.9; GPT-4o round-1 84.8% ->
  round-5 33.7% (VERIFIED). Explicit "constraint stated at turn 0 must hold at turn 5" structure. User turns are
  FIXED (no simulator). Tokens/session ~2-5k (MEMORY): no KV pressure. License: LICENSE file 404 — UNKNOWN.
- Compute: 2,500 turns x ~25 s ≈ 17 GPU-h/arm; 300-session subset ≈ 10 GPU-h/arm; judge = GPT-4o API.

**SEQUOR (arXiv 2605.06353; github deep-spin/SEQUOR)** — VERIFIED
- 1,400 conversations x 50 turns from 1,446 real-chat-log constraints; regimes single / tuples / replace / add /
  everything (constraints introduced at specified turns, held or swapped later). User-turn sequences are a fixed
  collection generated offline (Persona Hub + Qwen3-Next-80B), so evaluation needs NO simulator (VERIFIED, both
  paper and README wording; confirm by reading the data files before registering).
- Verifier: LLM-judge (GPT-oss-120B selected; GLM-4.7 94.85% / GPT-oss-120B 93.55% agreement vs gold responses,
  not vs humans). Constraint families (linguistic, style, format, number limits) overlap IFEval-checkable types,
  so a programmatic sub-verifier is feasible for a subset.
- Scores: 10 open models incl. Qwen3-4B-Inst and Gemma3-4B; single-constraint accuracy falls >11% by turn 50,
  tuples 38-40%, add 63% (VERIFIED). No 1.7B.
- KV pressure: REAL — 50 turns x (user ~100 + assistant ~250 tokens) ≈ 15-20k tokens by turn 50 (arithmetic
  from the turn count; per-turn lengths MEMORY). This is the only open chat benchmark in the list where a
  32k-native model actually exceeds 8k without artificial padding.
- License: not shown on repo page or paper — UNKNOWN; ask authors before publishing numbers.
- Compute: full = 70k assistant turns ≈ 300+ GPU-h/arm (OUT). Subset: 60 conversations from 'single' + 60 from
  'add', 50 turns, max_new 256 → 6,000 turns x ~12 s x 1.5 prefill factor ≈ 30 GPU-h/arm. Judge via API.

**MultiChallenge (arXiv 2501.17399; github ekwinox117/multi-challenge)** — VERIFIED
- 273 conversations (instruction retention 69, inference memory 113, versioned editing 41, self-coherence 50),
  ~5 turns, ~1,232 words; GPT-4o judge with instance rubrics (93.9% human alignment). Claude 3.5 Sonnet 41.4%,
  Llama-3.3-70B 23.2%. HF provider supported. License: arXiv non-exclusive (paper); repo not shown. Tiny n for
  the retention category (69) and judge-only → secondary at best.

**MT-Eval (arXiv 2401.16745; github KwanWaiChung/MT-Eval)** — VERIFIED
- 168 dialogues / 1,170 turns; recollection (38 dialogues x 10 turns), expansion, refinement, follow-up;
  GPT-4 judge 1-10; MIT; HF models supported. Recollection = early instruction held over 10 turns; small n.

**StructFlowBench (arXiv 2502.14494; github MLGroupJLU/StructFlowBench)** — VERIFIED (README)
- Six inter-turn relations incl. Recall; GPT-4o judge; MIT; local models supported; sizes not on README.

**EvolIF ("One Battle After Another", arXiv 2511.03508, ACL 2026)** — VERIFIED (HTML)
- Evolving generator, 9-12 IFEval-style constraint groups, programmatic CSR/ISR/robustness/recovery, sessions of
  8-18 turns until "patience" runs out; GPT-5 CSR 88.6%. Code "to be released" at github JiaQiSJTU/EvolIF —
  not yet verified as public. Needs a query-synthesis agent (LLM) per turn. Promising later, not now.

**DriftBench ("Models Recall What They Violate", arXiv 2604.28031; github kruthof/driftbench)** — VERIFIED
- 38 briefs, 6-8 turns, hard constraints judged by Claude Opus 4.6 with GPT-5.4 audit; KBV rate 8-99%.
  Tested "automated constraint monitoring + warning injection" — did NOT close the knows-but-violates gap.
  MIT code / CC-BY-4.0 data. Frontier-only, judge-only, n=38: OUT, but the negative on warning injection is a
  relevant prior (Section 3).

### C. Long-context retention (no tools)

**LongMemEval (arXiv 2410.10813; github xiaowu0162/LongMemEval)** — VERIFIED
- 500 questions; _S ≈ 115k tokens (~40 sessions), _M ≈ 500 sessions (~1.5M); 7 question types; GPT-4o judge with
  >97% human agreement. Long-context drops vs oracle: GPT-4o -30.3%, Llama-3.1-70B -55.1%, Llama-3.1-8B -36.1%,
  Phi-3-128k -45.9% (VERIFIED). MIT. Facts, not constraints; 115k > our 32k native window → OUT as-is.

**LoCoMo (arXiv 2402.17753; github snap-research/locomo)** — VERIFIED
- 10 released conversations (paper describes 50), ~300 turns / up to 35 sessions each; QA F1 + LLM judge;
  license CC BY-NC 4.0 (LICENSE.txt VERIFIED) — non-commercial: incompatible with a Hub release claim. OUT.

**LIFBench (arXiv 2411.07037, ACL 2025; github SheldonWu0327/LIF-Bench-2024)** — VERIFIED
- 2,766 instructions, 3 scenarios / 11 tasks, 4k-128k tokens in six intervals; LIFEval rubric-based automatic
  scoring (no judge); 20 models incl. Qwen2.5 family (1.5B/3B not confirmed on the page). License: arXiv
  non-exclusive (paper); repo not opened. The instruction sits at a fixed position relative to a long document
  — buried-instruction, single turn. Good fit for S2-style "constraint stated >= 8k tokens before the query".
- Compute: 2,766 x 1 turn with 4-32k prefill → ~25 GPU-h/arm over the ≤32k intervals; 500-item slice ≈ 5 GPU-h.

**Lost in the Middle (arXiv 2307.03172; github nelson-liu/lost-in-the-middle)** — VERIFIED
- NQ-open multi-doc QA (10/20/30 docs) + key-value retrieval; substring-match accuracy (MEMORY for metric name);
  MIT. Position-sensitivity, not instruction retention. Useful only as a sanity probe of pinning.

**RuleArena (arXiv 2412.08972, ACL 2025; github skyriver-2000/RuleArena)** — VERIFIED
- 816 datapoints, 3 rulebook domains, single-turn numeric answers (programmatic), MIT. Long rules but single
  turn; 1.7B would be near the floor on tax/NBA arithmetic. OUT.

**Pitfalls of KV Cache Compression (arXiv 2510.00231, ACL 2026)** — VERIFIED
- Uses multi-instruction IFEval prompts and system-prompt leakage as tasks; Llama-3.1-8B and Qwen2.5-14B; shows
  eviction (StreamingLLM/SnapKV/TOVA/H2O/K-Norm) is instruction-biased and proposes eviction-policy fixes.
  Not a benchmark per se but the closest published protocol to our "eviction is real" regime.

Not opened (MEMORY only, listed for completeness): CFBench (arXiv 2408.01122, single-turn Chinese
constraint-following), ConvBench (judge-only), FollowBench (single-turn, LLM+rule), IFBench (we have it),
WebArena/VisualWebArena/SWE-bench (browser/Docker, tens of GPU-h per attempt at 1.7B with near-zero success —
excluded on floor and cost grounds).

---------------------------------------------------------------------------------------------------------------
## 2. Which have "stated early, must hold late" structure, and which have real KV pressure

Explicit aged-constraint structure (mechanistic reason for retention/re-injection to help):
- SEQUOR (single/tuples/add regimes: constraint at turn k, checked every later turn to 50) — strongest.
- SysBench (system message at turn 0, 5 user turns; dependent-dialogue subset; misaligned turns test priority).
- Lost in Conversation (shards are constraints revealed early; final answer must satisfy all; SNOWBALL/RECAP
  show re-injection recovers 6-27 pts on GPT-4o).
- Multi-IF turns 2-3, MT-Eval recollection, MultiChallenge instruction-retention (69 items), EvolIF.
- BFCL multi_turn: only weakly — user intent evolves, but constraints are not restated; long_context variant is
  "find the needle in records", not "obey an old rule".
- AgentIF, RuleArena, LIFBench: long instruction, single turn — buried, not aged.

Real KV pressure (context > 8k during generation without artificial padding):
- SEQUOR at turns ~25-50 (~10-20k tokens) — yes, naturally.
- BFCL multi_turn_long_context — yes (records injected), but base at 2.5%.
- LIFBench 8k-32k intervals — yes, single turn.
- LongMemEval_S (115k) / LoCoMo / MemoryAgentBench — beyond our 32k native window (needs eviction by necessity,
  which is actually our regime, but the tasks are fact QA).
- Multi-IF, SysBench, MT-Eval, MultiChallenge, Lost in Conversation — NO (2-5k tokens); eviction must be simulated
  as in our KV probe. A reviewer will call simulated eviction on a 3k-token conversation a toy unless the
  cache budget is justified by a deployment target (e.g., "512-token KV budget for edge serving").

---------------------------------------------------------------------------------------------------------------
## 3. What retention / re-injection / system-prompt-anchoring methods report

- Lost in Conversation (Laban et al., ICLR 2026, VERIFIED): RECAP (one final restatement of all shards) lifts
  GPT-4o sharded 59.1 -> 76.6; SNOWBALL (repeat everything each turn) 59.1 -> 65.3; both stay below FULL; the
  paper frames repetition as mitigating 15-20% of the loss. Confound handling: same programmatic evaluators
  across settings; simulator held fixed (GPT-4o-mini). Model size: 8B-405B + API; no 1-3B.
- Drift No More (arXiv 2510.07777, VERIFIED): a constraint reminder injected at turn 4 returns Llama-3.1-8B to
  compliance on a synthetic rewriting task; KL-divergence drift metric + o1 judge; also tau-bench dialogues.
  Small-n, judge-scored; confounds not formally handled.
- When Attention Closes (arXiv 2605.12922, VERIFIED): Goal Accessibility Ratio (attention mass on goal tokens)
  declines 27-48% over 50 turns across Mistral-7B, Llama-3.1-8B, Qwen2.5-7B/3B/14B/32B, Mixtral; forcing a
  4096-token sliding window collapses 50-turn fact recall (Llama-3.1-8B -> 0%, Qwen2.5-7B -> 6%); linear probes
  on the residual stream predict recall (AUC to 0.99). No repo. This is the cleanest published evidence that
  eviction-of-the-goal is the failure mode our pinning addresses, and that the effect exists at 3B.
- MT-OSC (arXiv 2604.08782, VERIFIED): background condensation of history (condenser + rule-based decider);
  Llama-3.3-70B statistically indistinguishable from full history at -72% tokens; ~+3% avg accuracy across 13
  LLMs on sharded GSM8K/BFCL-v3/HumanEval/Spider/ToTTo + MT-Eval. Retention by compression, not amplification.
- DriftBench (arXiv 2604.28031, VERIFIED): automated constraint monitor + warning injection every turn does NOT
  close the knows-but-violates gap at frontier scale — a negative prior for naive re-injection when the model
  can restate the rule but chooses novelty.
- Pitfalls of KV Compression (arXiv 2510.00231, VERIFIED abstract): fair per-instruction eviction restores
  adherence on multi-instruction IFEval at 8B/14B (magnitudes not in abstract).
- Research-synthesis anchors (already cross-checked there): SpotLight halves the MT-IFEval cross-turn drop
  (18.2% -> 9.3%); Protection (arXiv 2605.18053) 10% boundary protection recovers 69-90% of ceiling; FlowKV.
- Sizes: nothing published at 1-2B for re-injection on these benchmarks; our 1.7B result would be the first
  datapoint, which cuts both ways (no prior to lean on, no prior to contradict).
- Confounds as handled in the literature: (i) verifier leakage — programmatic verifiers score the OUTPUT only,
  so an echo in the PROMPT cannot leak unless the model copies it, and copying a constraint into the answer is a
  legitimate IFEval fail/pass exactly as for any model; (ii) LLM-judge bias — LongMemEval and MultiChallenge
  validate judges against humans (97% / 93.9%); SEQUOR validates against gold responses only; nobody blinds the
  judge to the arm — we must (strip echo lines from judged transcripts, identical judge prompt per arm).

---------------------------------------------------------------------------------------------------------------
## 4. Smallest credible design for the PUBLISH GATE (preregistration draft)

### 4a. Agentic leg — Lost-in-Conversation, programmatic subset ("LiC-P")
- Tasks: actions (function calls; BFCL-derived), database (Spider SQL executed), math (GSM8K exact); ~300
  sharded instructions, 2-8 shards each. All three verifiers are programmatic; no judge.
- Why this and not BFCL multi-turn / tau-bench: Qwen3-1.7B is at 2.5-14% there (Section 5), so paired
  differences are mostly 0-0 and any gain is noise on tool competence; LiC's actions task is single-call
  function calling where an 8B model still scores ~20 sharded, i.e., there is a floor to stand on.
- Arms (same decoding, same max_new, same seed): BASE (sharded, nothing added) | CONTROL (random-span echo,
  token-matched; Section 4d) | LEDGER (automatic finder + KV keep + one-line echo, exactly the deploy config) |
  SNOWBALL (all shards repeated; the published superset re-injection ceiling; 1 arm only for reference).
- Cost: 300 x ~5 turns x ~25 s ≈ 10 GPU-h/arm; 4 arms ≈ 40 GPU-h; drop SNOWBALL to fit 30 GPU-h, or run the
  actions+database half (≈ 200 instr) for all four arms ≈ 27 GPU-h. Simulator (GPT-4o-mini) API cost negligible;
  fix shard order (the repo has a deterministic ordering option per README "sharded_instructions_600.json";
  confirm) and simulator seed; re-run 10% of BASE twice to measure simulator-induced variance before unblinding.
- Preflight (2 GPU-h): BASE on 40 instructions; require FULL-setting accuracy >= 25% on actions and math, else
  swap in Multi-IF turn-3 as the sole primary (registered fallback, decided before treatment runs).

### 4b. Long-context retention leg — SEQUOR subset ("SEQ-60/60")
- 60 conversations from 'single' + 60 from 'add', 50 turns each, user turns as shipped (no simulator), max_new
  256, own-arm history. Real context growth to ~15-20k tokens: KV eviction in LEDGER/CONTROL/BASE follows the
  registered production policy (KVCache.evict keep=), NOT a simulated budget.
- Verifier: primary = programmatic checkers for the IFEval-checkable constraint subset (length, format, keyword,
  case, count — the SEQUOR pool overlaps these families; register the mapping before running); secondary = the
  paper's judge (GPT-oss-120B via API) on all constraints, judge blinded by stripping echo lines and arm labels.
- Cost: 6,000 turns/arm x ~12 s x 1.5 (deep prefill) ≈ 30 GPU-h/arm — too much for three arms. Register
  SEQ-40/40 (4,000 turns/arm ≈ 20 GPU-h/arm, 3 arms ≈ 60 GPU-h) only if the LiC-P leg passes; otherwise the
  cheaper registered S2 (buried-constraint b3 templates, constraint >= 2048 tokens before the query) stays as
  the long-context leg. Alternative at ≤ 10 GPU-h/arm: LIFBench 8k-32k slice (500 items, rubric-scored, single
  turn) — buried, not aged; weaker mechanistically.
- License blocker: SEQUOR license is not stated on the repo or paper — obtain it in writing before any
  published number; SysBench likewise (LICENSE 404). Both are fine for an internal gate.

### 4c. Estimand, gates, analysis (paired by episode)
- Unit = episode (one sharded instruction / one 50-turn conversation). Primary outcome: episode-level
  programmatic pass (LiC-P) / late-turn (turns 26-50) constraint-satisfaction rate (SEQ).
- Estimand: Δ = mean(LEDGER − CONTROL) over episodes. Test: one-sided paired test with cluster-robust CI
  (cluster = episode; for SEQ additionally cluster = source constraint id), Holm across the two legs at
  α = 0.025 each; gate = clustered lower bound > 0 on the primary. LEDGER − BASE reported alongside (must also be
  > 0; if LEDGER beats BASE but not CONTROL, the benefit is "any extra text", not selection).
- Ceiling reference: SNOWBALL (LiC) / no-eviction full context (SEQ) reported, not gated.
- Safety gates (every arm, ROUND 7 as amended): timeouts ≤ 2% absolute; truncation excess over BASE ≤ +2 pts,
  truncated turns scored as-is and kept in the denominator; tool-call validity (LiC actions: parseable call rate)
  excess-over-base ≥ −2 pts; stale-constraint adoption not above BASE (SEQ 'add'/'replace': a superseded
  constraint being followed counts as a fail; clustered NI bound < 2.0 as registered); echo-copy rate (verbatim
  echo string appearing in the reply) reported, and any constraint whose verifier could be satisfied by copying
  the echo string is excluded from the primary at registration.
- Power: with p_base ≈ 0.15 (LiC-P at 1.7B, extrapolated) and a +5-pt paired effect with discordance ~0.2,
  n = 300 gives ~80% one-sided power at α = 0.025 (McNemar approximation; recompute with the preflight
  discordance before sealing). SEQ late-turn rates are per-turn, so 40 conversations x 25 late turns gives
  1,000 turns but only 40 clusters — the cluster count, not the turn count, is the binding constraint; state it.
- Blinding: finder, keep policy, echo template, max_new, decoding, and the constraint-to-checker map are frozen
  and hashed before the first treatment token is generated; the orchestrator does not touch any of them after
  reading the preflight.

### 4d. Equal-context control (what BASE gets)
Register CONTROL = "random-span echo, token-matched": at every point where LEDGER would inject its one-line
echo, CONTROL injects a span of the same token count sampled uniformly from the same conversation's prior USER
turns (not assistant turns, to avoid re-feeding the model its own errors), formatted with the identical template
("Note: ..."), and pinned in KV with the same keep= budget (same number of columns). This holds constant:
extra tokens, template, position, KV residency budget, and prompt-format novelty; the only difference is WHICH
tokens (salience-selected vs random). It is the exact-column control the KV-probe v2 review asked for.
Do not use SNOWBALL as the control: it is a superset (more tokens), so LEDGER ≤ SNOWBALL is expected and
uninformative; report it as the ceiling. Do not use "no echo" as the only control: a win over it cannot
distinguish selection from "any reminder helps" (Drift No More shows any reminder helps an 8B).

### 4e. Falsifier for "automatic benefit for agentic work"
The claim is falsified — and the Hub release does not happen — if, at the registered n and with all safety
gates intact, ANY of: (1) clustered lower bound of LEDGER − CONTROL ≤ 0 on the LiC-P primary; (2) LEDGER − BASE
> 0 but LEDGER − CONTROL ≤ 0 (benefit is nonspecific text, not selection); (3) the LEDGER gain is present only
when eviction is simulated with a budget below the natural context and vanishes under the production
eviction policy on SEQ (benefit exists only in a toy regime); (4) tool-call validity or truncation excess breaks
the gate. A pass on Multi-IF alone (chat, 3 turns, no tools) is registered as NOT sufficient for the word
"agentic" in the model card.

---------------------------------------------------------------------------------------------------------------
## 5. What we are missing — does Qwen3-1.7B even do agentic work?

- VERIFIED floor numbers (Fission-GRPO, arXiv 2601.15625, Table 1, untrained Qwen3-1.7B, T=0.95): BFCL v4
  multi-turn overall 7.80% (base 10.0, miss_func 11.0, miss_param 8.0, long_context 2.5); tau-bench retail 6.1,
  airline 14.0. Qwen3 report (VERIFIED): BFCL v3 overall 52.2 (non-thinking) — the single-turn AST categories
  carry it. Model card: "excels in tool calling", Qwen-Agent recommended; no numbers on the card.
- Consequence: on any executable multi-turn agent benchmark the base fails 90%+ of episodes for reasons
  (wrong parameters, missed calls, format breaks) that a constraint-retention ledger cannot touch. A paired
  test there measures tool competence plus noise; even a real retention effect would be invisible under a
  ceiling of ~10%. That is why the agentic leg above is the LiC actions/database/math subset (single-call
  function generation, SQL, arithmetic) rather than a stateful tool loop.
- Thinking mode: the report's 1.7B numbers improve in thinking mode (Multi-IF 51.2 vs 44.7; BFCL 56.6 vs
  52.2). Our runs are non-thinking (history without think blocks, per WORKLOG). Register the mode; do not mix.
- Honest wording for the model card if LiC-P passes: "improves constraint retention across turns on sharded
  function-calling / SQL / math tasks and on long-conversation constraint following", not "improves agentic
  tool use". A claim about stateful tool loops needs a base model that can run them.
- Other gaps: (i) the salience finder was tuned on Multi-IF-style constraints; LiC shards and SEQUOR constraints
  are a distribution shift — the finder's recall on a 100-item labelled sample of each must be measured
  (≥ 0.80 as in the SALIENCE-2 gate) BEFORE registration, else a null is uninterpretable; (ii) simulator
  nondeterminism in LiC — measure BASE-vs-BASE rerun variance first; (iii) licenses unknown for SEQUOR, SysBench,
  AgentIF; LoCoMo is CC BY-NC (exclude); (iv) the hand-rolled trunk has no OpenAI-compatible endpoint, and every
  harness above (LiC, BFCL, SEQUOR, SysBench) assumes one — budget the shim before the GPU hours.

---------------------------------------------------------------------------------------------------------------
## 6. Ranked recommendation

1. **Lost-in-Conversation programmatic subset (actions + database + math), 4 arms** — ~27-40 GPU-h total.
   Reasons: aged-constraint structure by construction; programmatic verifiers; MIT; published SNOWBALL/RECAP
   give a literature ceiling; 8B models sit at 20-30 sharded so a 1.7B has a floor to stand on; simulator cost
   negligible. Risk: GPT-4o-mini simulator noise (measure); no KV pressure (so it does not, alone, test the
   eviction claim — that is what leg 2 / S2 is for).
2. **SEQUOR 'single'+'add' subset (40+40 conversations x 50 turns), 3 arms** — ~60 GPU-h at max_new 256; run only
   after leg 1 passes, or shrink to 25+25 (~38 GPU-h). Reasons: the only open chat benchmark with natural
   >8k-token context where the production eviction policy is exercised; fixed user turns; explicit turn-k
   constraint with later checks; Qwen3-4B/Gemma3-4B degradation published. Risks: LLM judge (mitigate with a
   programmatic sub-verifier as primary), unstated license, cluster count = conversations.
   Cheaper stand-in for the long-context leg: the registered S2 buried-constraint set (~10 GPU-h) or a LIFBench
   8-32k slice (~5 GPU-h/arm, rubric-scored, single-turn).
Explicitly rejected for the gate: tau/tau2-bench, BFCL multi-turn, HANDBOOK.md, AgentBench, WebArena,
SWE-bench (floor at 1.7B and/or cost > 100 GPU-h and/or judge/simulator dependence); LongMemEval/LoCoMo/
MemoryAgentBench (fact memory, > 32k, LoCoMo non-commercial); AgentIF/RuleArena/LIFBench as primaries
(single-turn, no aging).

---------------------------------------------------------------------------------------------------------------
## 7. Verified-vs-memory ledger (sources opened this session)

VERIFIED (opened; number/claim read on the page):
1. arxiv.org/abs/2506.07982 + arxiv.org/html/2506.07982 (tau2-bench: 115/50/114 tasks, gpt-4.1 simulator, proprietary-only eval, 74/56/34 pass@1)
2. github.com/sierra-research/tau2-bench (MIT; domains) + docs/leaderboard-submission.md (gpt-5.2 recommended, ≥4 trials)
3. arxiv.org/abs/2406.12045 (tau-bench: DB-state eval, pass^k, CC BY 4.0)
4. openrouter.ai/benchmarks/tau2-bench-airline (Llama-3.1-8B 30.9%, Qwen2.5-7B 16.7%)
5. arxiv.org/html/2601.15625v2 (Fission-GRPO: Qwen3-1.7B BFCL v4 MT 7.80/10.0/11.0/8.0/2.5; tau retail 6.1 airline 14.0)
6. arxiv.org/html/2505.09388 (Qwen3 report: 1.7B IFEval 72.5/68.2, Multi-IF 51.2/44.7, BFCL v3 56.6/52.2)
7. huggingface.co/Qwen/Qwen3-1.7B (Apache-2.0, 32k native, Qwen-Agent recommended)
8. gorilla.cs.berkeley.edu/leaderboard.html (v4 current; AST; unweighted average) + blogs/13_bfcl_v3_multi_turn.html (200/200/200/200/200, state- and response-based checks) + github gorilla README (Apache-2.0; vllm/local path) + TEST_CATEGORIES.md (multi_turn_*, memory_*, web_search_*)
9. arxiv.org/abs/2505.06120 + arxiv.org/html/2505.06120 (LiC: 600 instr, -39%, 8B 47.8->20.5, RECAP 59.1->76.6, SNOWBALL 59.1->65.3, GPT-4o-mini simulator, T=1.0) + github.com/microsoft/lost_in_conversation (MIT; 7 tasks; OpenAI/Azure keys)
10. arxiv.org/abs/2410.10813 + arxiv.org/html/2410.10813 (LongMemEval: 500 q, _S 115k, GPT-4o judge 97%, Llama-3.1-8B -36.1%) + github.com/xiaowu0162/LongMemEval (MIT)
11. arxiv.org/abs/2505.16944 + github.com/THU-KEG/AgentIF (707 instr, 11.9 constraints, 1,723 words, single-turn, gpt-4o-2024-11-20 judge; LICENSE 404)
12. arxiv.org/html/2408.10943 + github.com/PKU-Baichuan-MLSystemLab/SysBench (500x5, CSR/ISR/SSR, GPT-4o judge, 8B scores; LICENSE 404)
13. arxiv.org/abs/2501.17399 + arxiv.org/html/2501.17399 + github.com/ekwinox117/multi-challenge (273 conv, 69/113/41/50, GPT-4o judge 93.9%, Llama-3.3-70B 23.2%)
14. arxiv.org/html/2605.06353v1 and v2 + github.com/deep-spin/SEQUOR + pipeline/README.md (1,400x50, five regimes, GPT-oss-120B judge, Qwen3-4B/Gemma3-4B, 11/38-40/63% drops; fixed user-turn collection; license unstated)
15. arxiv.org/html/2604.28031 + github.com/kruthof/driftbench (38 briefs, KBV 8-99%, monitor+warning fails; MIT/CC-BY)
16. arxiv.org/html/2511.03508v1 (EvolIF: 8-18 turns, GPT-5 CSR 88.56%, code "to be released")
17. arxiv.org/html/2607.25398v1 + github.com/surge-ai/handbook (65 tasks, 14.9k-token median handbook, 824 programmatic criteria, 36.2% best; CC BY 4.0 / Apache-2.0)
18. arxiv.org/html/2605.12922v1 (When Attention Closes: GAR -27-48%, SW=4096 collapse, Qwen2.5-3B included)
19. arxiv.org/html/2604.08782v3 (MT-OSC: condenser, -72% tokens, +3% avg over 13 LLMs; CC BY 4.0)
20. arxiv.org/html/2510.07777 (Drift No More: turn-4 reminder restores Llama-3.1-8B; o1 judge; CC BY-SA)
21. arxiv.org/html/2410.15553 + github.com/facebookresearch/Multi-IF (per-turn table; Apache-2.0)
22. github.com/KwanWaiChung/MT-Eval (MIT; 168 dialogues / 1,170 turns; GPT-4 judge)
23. github.com/MLGroupJLU/StructFlowBench (MIT; GPT-4o judge)
24. github.com/skyriver-2000/RuleArena (MIT; single-turn; 3 domains)
25. arxiv.org/html/2411.07037 (LIFBench: 2,766 instr, 4k-128k, rubric scoring, 20 models)
26. github.com/snap-research/locomo + LICENSE.txt (CC BY-NC 4.0; 10 conversations released)
27. github.com/nelson-liu/lost-in-the-middle (MIT; 10/20/30-doc NQ; KV retrieval)
28. arxiv.org/abs/2510.00231 (Pitfalls of KV compression: multi-instruction IFEval, 5 eviction methods, 8B/14B)
29. arxiv.org/abs/2507.05257 + github.com/HUST-AI-HYZ/MemoryAgentBench (MIT; AR/TTL/LRU/CR; EM/substring/LLM-judge)
30. Search-level only (snippets, not the page body): AgentBench Apache-2.0; Agent-SafetyBench MIT, 2,000 cases; MINT abstract (GPT-4 feedback, ≤5 turns); Enterprise agentic benchmark arXiv 2511.08042 (Qwen3-4B telecom 27% — snippet only).

MEMORY / UNVERIFIED (flag before citing): token counts per episode for tau-bench, SysBench, LiC, SEQUOR
(derived from turn counts, not measured); BFCL long_context token size; MINT license; xLAM-2-3b 56.0% and
Qwen3-4B 15.75% multi-turn BFCL (snippets); CFBench/ConvBench/FollowBench/IFBench details; LiC deterministic
shard-order option (README mentions the 600-instruction file, not the ordering switch — check the code);
our own throughput unit (19.74 tok/s from WORKLOG, not remeasured today); the power calculation assumptions
(p_base 0.15, discordance 0.2) are placeholders to be replaced by preflight measurements.
