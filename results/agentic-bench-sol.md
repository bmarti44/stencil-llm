# Deep research: automatic benefit on long-context, long-horizon agentic work

**Research date:** 2026-09-02

**Decision target:** frozen Qwen3-1.7B, ledger span selection + KV pinning + optional one-line echo, about 30 GPU-hours affordable

**Research method:** primary sources only for factual claims below. I opened arXiv/ACL/OpenReview papers, official GitHub repositories and licenses, official dataset cards, and official leaderboards. The source ledger at the end contains more than 15 independently opened primary sources.

## Executive conclusion

There is no honest way to obtain a full, standard, statistically strong agent-benchmark result within 30 GPU-hours from the supplied `0.4 steps/s` alone. The number is not identified as decoding tokens/s, and every serious full suite is too large even under the optimistic interpretation that one step is one generated token. The appropriate plan is therefore a **sealed two-stage gate**, not a claim based on a convenient tiny subset:

1. **Agentic gate: BFCL V3 multi-turn, 64 pre-registered cases (32 Base, 32 Long Context), ledger versus a token- and KV-matched sham.** It is Apache-2.0, uses predefined users rather than an LLM user simulator, executes tools, maintains environment state, and uses deterministic state/function-call evaluation. At four 80-token model responses per case, two arms cost **28.4 GPU-h** under the optimistic 0.4 generated-token/s model. The principal threat is a severe floor: published Qwen3-1.7B multi-turn results are only **7.80 overall / 2.5 Long Context** in one evaluation and **10.25 multi-turn** in another. A competence preflight must be passed before sealing; otherwise the experiment is incapable of testing the ledger.
2. **Mechanism gate: a sealed 64-item `HANDBOOK-policy` read-only diagnostic derived from HANDBOOK.md’s Apache-2.0 policies and deterministic criteria.** HANDBOOK.md is the strongest benchmark found for the actual mechanism: policy documents are 20–124 pages (about 8.3K–79.4K extracted tokens), tasks average 17 reasoning steps and 30 tool calls, and 824 criteria check required and forbidden behavior. The official 65-task × 4-run protocol is far outside budget—at the low end of its reported output lengths, one paired run is already about **1,174 GPU-h**, before prefill and tool overhead. A 64-item, one-response, 96-token-cap policy-decision diagnostic is about **8.5 GPU-h** under the same optimistic model, but must be labelled a derived mechanism diagnostic, not an official HANDBOOK.md leaderboard score.

This pair addresses two different propositions. BFCL tests whether the automatic ledger helps an actual stateful tool loop. HANDBOOK-policy tests whether it helps preserve old, consequential policy instructions in genuinely long native context. **Neither result may substitute for the other.** A positive long-context diagnostic with no BFCL gain does not prove agentic benefit; a BFCL gain on histories that never overflow the cache does not prove the proposed retention mechanism.

The strongest future full-suite target is [HANDBOOK.md, arXiv:2607.25398](https://arxiv.org/abs/2607.25398), not WebArena, SWE-bench, or an LLM-judged chat benchmark. Its cost makes that a later-budget validation.

## Compute convention and its limitation

The supplied throughput is `0.4 steps/s`. If—and only if—this means **0.4 autoregressive generated tokens/s**, then one GPU-hour produces 1,440 generated token-steps and the paired lower bound is

\[
H_{paired}=\frac{2NRT}{1440},
\]

where `N` is cases, `R` is average model responses per case, and `T` is the per-response generated-token cap. These are deliberately transparent sensitivity calculations, not measured run times. They omit long-context prefill, growing-attention cost, tool/environment latency, retries, and evaluator work, so they are lower bounds. If `0.4 steps/s` means optimizer steps/s, **none of the numerical inference-hour estimates is valid**; first measure end-to-end seconds/case on CPU-prepared, held-out development cases and replace every estimate with `2 × N × observed hours/case`.

For heterogeneous agents where a response count is not fixed by the benchmark, the assumptions are shown rather than hidden. “Full” means the public evaluation set, one run per arm, unless the benchmark’s official protocol specifies repetitions.

## Benchmark map

### Best-aligned and close alternatives

| Benchmark | What it measures; horizon/context | Old standing instruction? Native cache pressure? | Verifier | Local open-weight use; reported 1–3B signal; saturation | License/status | Optimistic full paired cost at 0.4 token/s |
|---|---|---|---|---|---|---|
| **[BFCL V3](https://github.com/ShishirPatil/gorilla/tree/main/berkeley-function-call-leaderboard)** ([data README](https://github.com/ShishirPatil/gorilla/blob/main/berkeley-function-call-leaderboard/bfcl_eval/data/README.md), [leaderboard](https://gorilla.cs.berkeley.edu/leaderboard.html)) | 1,000 multi-turn cases: Base 200, Missing Parameters 200, Missing Functions 200, Long Context 200, Composite 200. Predefined user turns, executable functions, and evolving environment state. Long Context injects hundreds of files or thousands of booking records. | **Partial.** Tool schemas/system scaffold are early and must survive turns; many task-specific constraints arrive later. Long Context supplies native large observations, but actual tokenized length and overflow relative to the project cache must be audited case by case. | Programmatic AST/executable call checks and exact final-state checks; multi-turn is all-or-nothing. No LLM judge or LLM user is required. | Local adapters supported. Published Qwen3-1.7B: FISSION paper base **7.80 overall**, Base 10, Missing Functions 11, Missing Parameters 8, Long Context 2.5; ToolRM paper greedy **55.74 overall single/mixed**, but only **10.25 MT**. A specialized xLAM-2-1B reports **35.12 MT**, showing size is not an absolute barrier but alignment is. Single-turn categories are much nearer saturation than MT; frozen Qwen has a trajectory floor. | [Apache-2.0](https://github.com/ShishirPatil/gorilla/blob/main/LICENSE). Open and runnable after adapting the hand-rolled chat/tool protocol. | Displayed four-category MT score: 800 × 4 responses × 80 tokens = **355.6 h**. All 1,000 = **444.4 h**. Recommended 64-case pair = **28.4 h**. |
| **[HANDBOOK.md](https://github.com/surge-ai/handbook)** ([paper](https://arxiv.org/abs/2607.25398), [leaderboard](https://surgehq.ai/benchmarks/handbook)) | 65 stateful enterprise tasks, five domains, ten fictional companies, 82 tools across six MCP services. Handbooks are 20–124 pages / about 8.3K–79.4K extracted tokens; tasks average 17 reasoning steps and 30 tool calls. 824 criteria: 592 expected behaviors and 232 incorrect behaviors. Official protocol is four runs/task. | **Yes, strongest native match.** Long-lived SOP/policy rules must govern much later actions; many documents exceed 8K. The agent obtains documents through tools, so only policy text actually observed by the model can be selected or pinned. | Deterministic programmatic criteria over tool traces and final state; strict task pass requires every criterion. | Model endpoint is pluggable, but published results are frontier-scale; no 1–3B score. Most frontier agents were below 25% at release; best official score was about 36.2% by the research date, so not saturated. | [Apache-2.0](https://github.com/surge-ai/handbook/blob/main/LICENSE). | Reported output is roughly 13K–60K tokens/trial. Even at 13K, 65 paired tasks = **1,173.6 h**; official four-run paired protocol = **4,694.4 h**, excluding prefill. Derived 64 × 96-token policy diagnostic = **8.5 h**. |
| **[SOP-Bench](https://github.com/amazon-science/SOP-Bench)** ([paper, arXiv:2506.08119](https://arxiv.org/abs/2506.08119)) | Current release: 2,000+ executable tasks across 12 business domains from expert-authored SOPs; README describes 10–50+ decision points. Function-calling and ReAct agents orchestrate synthetic APIs. Metrics include task success, execution completion, conditional success, and tool accuracy. | **Yes conceptually:** the SOP is standing procedure for the later tool sequence. Exact token lengths and fraction exceeding 8K are not reported in the current abstract/README, so genuine cache pressure is unverified. | Executable interfaces and ground-truth outputs; programmatic task/tool metrics. | Local OSS models can be added, although official runner emphasizes Bedrock. Published open models start at 7B: Qwen2.5-7B has very low domain pass rates (including 0% in one domain), so 1.7B floor risk is extreme. Some frontier model/domain combinations reach 100%, while others are 57%; domain-selective saturation, not global saturation. | [CC-BY-NC-4.0](https://github.com/amazon-science/SOP-Bench/blob/main/LICENSE): available for noncommercial research, not permissive for an unrestricted product artifact. | At 2,000 tasks, even an unrealistically small 10 responses × 64 tokens is **1,777.8 h**. A subset could fit, but license and floor make it rank below BFCL/HANDBOOK. |
| **[tau2-bench](https://github.com/sierra-research/tau2-bench)** ([paper, arXiv:2506.07982](https://arxiv.org/abs/2506.07982)) | 115 retail, 50 airline, and 114 balanced telecom cases (279 total). Stateful customer-service conversations; both agent and user may have tools. Policies are supplied to the agent. | **Yes policy-wise**, but typical conversations are not registered as >8K and therefore do not establish actual KV eviction. | Final-state database assertions plus communication/natural-language assertions; telecom is especially programmatic. User is simulated by GPT-4.1 in the paper. Authors estimate about $40 for one all-domain trial with their API models and report simulator error (16% any error, 6% critical), a material confound. | Local agent models are supported, but an external user model remains. FISSION reports Qwen3-1.7B base **7.9 retail / 12 airline / 25 telecom**. Not saturated at the top, but frozen-Qwen floor risk is high. | [MIT](https://github.com/sierra-research/tau2-bench/blob/main/LICENSE). | Assumption 12 agent responses × 80 tokens: **372 h**, plus user-simulator cost. |
| **[tau-bench](https://github.com/sierra-research/tau-bench)** ([paper, arXiv:2406.12045](https://arxiv.org/abs/2406.12045)) | 115 retail + 50 airline policy-following customer-service tasks; conversational tool use and pass^k reliability. Repository now warns users to prefer newer tau2/tau3. | Early policy, but no registered native >8K condition. | Database state plus required communication, with an LLM user. | Local agent endpoint possible. No 1–3B score in the original paper; later Qwen3-1.7B tau/tau2 results are in FISSION. Launch frontier scores were below 50%, so no ceiling. | [MIT](https://github.com/sierra-research/tau-bench/blob/main/LICENSE). | Assumption 10 × 80 tokens: **183.3 h**. |
| **[ComplexFuncBench](https://github.com/zai-org/ComplexFuncBench)** ([paper, arXiv:2501.10132](https://arxiv.org/abs/2501.10132)) | 1,000 samples over hotels, flights, car rental, attractions, and cross-domain queries; average 3.26 steps and 5.07 calls. Includes constraints, implicit parameter reasoning, long values, real API responses, and a 128K condition. | **Weak for this mechanism.** The user’s constraints are generally part of the current query; 128K material tests retrieval/parameter extraction, not a standing instruction issued many turns earlier. | ComplexEval combines exact/rule matching and API-response equivalence; response-quality submetrics use model-based judging. Real Booking/RapidAPI access is a reproducibility dependency. | vLLM endpoint supported. Smallest published: Qwen2.5-7B success 5.0%; Llama-3.1-8B 0.1%. Therefore 1.7B is almost certainly a floor. Top is 61%, not saturated. | Public repository has **no LICENSE file found**; source-visible is not permission to reuse. | Paper uses max 2,048 tokens. Even with 256 × 5.07 calls: **1,802.7 h**; 128K prefill omitted. |
| **[VeriFY](https://github.com/pkrobinette/VerIFY)** ([EACL Findings 2026](https://aclanthology.org/2026.findings-eacl.254/)) | Synthetic 10-, 25-, and 50-turn conversations with explicit style/security constraints and later compliance probes. | **Yes**, deliberately aged across exact turn distances. Context is long-horizon but not necessarily >8K; padding is not the causal condition. | Fully programmatic “Certified Compliance Accuracy.” | Ideal scientifically, and published interventions start at Gemma-7B/Llama-3-8B. However the repository says dataset release is pending Google DeepMind approval. | Paper available under ACL’s CC-BY-4.0 terms; repository has no released dataset and no reusable dataset license. **Not runnable now.** | Cannot estimate a full release that does not exist. For scale, 100 × 25 turns × 128 tokens/response paired is **444.4 h**. |
| **[Lost in Conversation](https://github.com/microsoft/lost_in_conversation)** ([paper, arXiv:2505.06120](https://arxiv.org/abs/2505.06120)) | 600 sharded, multi-turn instructions across code, database, API/action, math, data-to-text, summarization, and translation tasks. Reports an average 39% single-turn-to-multi-turn degradation. | **Yes:** requirements are split across earlier turns. Paper explicitly studies conversational loss, but native histories are not guaranteed to overflow an 8K cache. | Task-specific validators are largely programmatic; several simulations use model-generated user/system behavior. | Local models supported; evaluated open models begin around 8B/13B, with no 1–3B report. Not saturated. | [MIT](https://github.com/microsoft/lost_in_conversation/blob/main/LICENSE). | Assumption four 256-token responses: **853.3 h**. A fixed-history final-turn slice would be cheaper but would no longer be the full protocol. |
| **[SysBench](https://github.com/PKU-Baichuan-MLSystemLab/SysBench)** ([paper, arXiv:2408.10943](https://arxiv.org/abs/2408.10943)) | 500 five-turn dialogues / 2,500 responses; 356 dependent and 144 parallel conversations. System instructions average 2.38 constraints. | **Yes** for system-instruction persistence, but short: the reported system prompts average hundreds of words, not a controlled >8K condition. | GPT-4o checklist verifier, not programmatic; conversation history can expose reference behavior. | Local outputs can be generated. Smallest published Qwen2-7B instruction-satisfaction rate is 26.9%; its dependent-turn R5 result is 1.1. No 1–3B score and severe late-turn floor. | Repository has **no LICENSE file found**. | 500 × 5 × 128 tokens paired = **444.4 h**. |
| **[AgentIF](https://github.com/THU-KEG/AgentIF)** ([paper, arXiv:2505.16944](https://arxiv.org/abs/2505.16944)) | 707 system instructions from 50 real-world agent scenarios; average 1,723 words, maximum 15,630, and about 11.9 constraints. Despite the name, the core evaluation is one system+user input and one response, not a stateful tool trajectory. | The system instruction is early and some examples can exceed 8K, but there is no many-turn aging or tool-state loop. | Constraint-specific code, LLM, or hybrid verifiers; authors recommend GPT-4o for several checks. | vLLM/local generation supported. Published open models begin at 7–8B; Llama-3.1-8B CSR is 53.6. No 1–3B result. Not saturated. | Repository has **no LICENSE file found**. | At 512 output tokens: **502.8 h**. |
| **[MultiChallenge](https://github.com/ekwinox117/multi-challenge)** ([paper, arXiv:2501.17399](https://arxiv.org/abs/2501.17399)) | 273 conversations, average five and at most ten turns, average 1,231.7 words. Of these, 69 test instruction retention, 113 inference memory, 41 reliable editing, and 50 conversational coherence. | The 69 retention items are explicit early-instruction cases, but the paper notes the conversations are short relative to context windows; **no KV-pressure test**. | Instance-specific rubric judged by an LLM. | Any local model can answer fixed histories; no 1–3B result. Best reported frontier score was about 41.4%, so no ceiling. | Repository has **no LICENSE file found**. | If only one final 256-token answer/case: **97.1 h**; any regenerated dialogue costs more. |
| **[Multi-IF](https://github.com/facebookresearch/Multi-IF)** ([paper, arXiv:2410.15553](https://arxiv.org/abs/2410.15553)) | 4,501 three-turn multilingual instruction-following conversations in eight languages; rule-based extensions of IFEval. | Some constraints carry across three turns, but contexts are short and there are no tools or native eviction. Useful corroboration, not the missing agentic proof. | Programmatic instruction checkers. | Local model generation supported. No published 1–3B table found in the primary paper/repo. The project already has a 113-case internal result, so another tiny slice has low marginal value. | [Apache-2.0](https://github.com/facebookresearch/Multi-IF/blob/main/LICENSE); repository archived in December 2025. | 4,501 × 3 × 256 tokens paired = **4,801.1 h**. |

### Long-context, memory, and static-instruction controls

| Benchmark | What it measures; horizon/context | Fit to old-instruction/KV claim | Verifier; small-model evidence | License | Optimistic full paired cost |
|---|---|---|---|---|---|
| **[LIFBench](https://github.com/SheldonWu0327/LIFBench-2024)** ([paper, arXiv:2411.07037](https://arxiv.org/abs/2411.07037)) | 2,766 prompts, 11 tasks, three scenarios, six length bins through 128K; LIFEval is deterministic. | Strong long-context control but wrong causal placement: the short instruction is placed **after** the long context, so it is fresh rather than aged. A positive result would not specifically validate preservation of old instructions. | Programmatic. Published models are 7B+; no 1–3B result found. | [MIT](https://github.com/SheldonWu0327/LIFBench-2024/blob/main/LICENSE). | 256 tokens/item: **983.5 h**, plus large prefill. |
| **[LongMemEval](https://github.com/xiaowu0162/LongMemEval)** ([paper, arXiv:2410.10813](https://arxiv.org/abs/2410.10813)) | 500 questions over long chat histories; `S` averages about 115K tokens/problem, `M` has roughly 500 sessions / 1.5M tokens. Tests information extraction, multi-session reasoning, temporal reasoning, knowledge updates, and abstention. | Excellent native age and cache pressure, but old **facts**, not old instructions. The salience selector is designed for instructions, so failure may be a construct mismatch. | QA accuracy uses GPT-4o judging (reported >97% human agreement); retrieval Recall@k/NDCG can be programmatic if retrieval spans are exposed. Phi-3.5-mini 4B scored 0.342 versus 0.660 oracle context; no 1–3B result. | [MIT](https://github.com/xiaowu0162/LongMemEval/blob/main/LICENSE). | One 128-token answer: **88.9 h**, but enormous prefill dominates. |
| **[LoCoMo](https://github.com/snap-research/locomo)** ([paper, arXiv:2402.17753](https://arxiv.org/abs/2402.17753)) | Long personal conversations: original collection 50 conversations averaging 304.9 turns, 19.3 sessions, and 9,209 tokens; current repository exposes the ten longest with QA/summarization annotations. | Native age, sometimes >8K, but autobiographical facts rather than standing instructions; no tool actions. | Mixture of lexical/LLM evaluation depending on task; no relevant 1–3B intervention result. | [CC-BY-NC-4.0](https://raw.githubusercontent.com/snap-research/locomo/main/LICENSE.txt). | No honest single number because current tasks have different output types; at minimum, long prefill makes it a poor 30 h target. |
| **[MT-Eval](https://github.com/KwanWaiChung/MT-Eval)** ([paper, arXiv:2401.16745](https://arxiv.org/abs/2401.16745)) | 168 dialogues / 1,170 turns, average 6.96; patterns include 10-turn recollection, seven-turn expansion, 12-turn refinement, and three-turn follow-up. Average prompt 760 words, maximum 2,574. | Recollection ages facts/instructions, but histories are normally below 8K and there are no tools. | GPT-4 judge. Smallest reports are 6–7B (for example ChatGLM3-6B); no 1–3B. | [MIT](https://github.com/KwanWaiChung/MT-Eval/blob/main/LICENSE). | 1,170 × 256 tokens paired = **416 h**. |
| **[IFBench](https://github.com/allenai/IFBench)** ([paper](https://openreview.net/forum?id=yfYgwjj5F8)) | 58 out-of-distribution verifiable constraints and 83 programmatic checkers. Includes an optional two-turn constraint-isolation setting. | The added constraint is late/fresh in the two-turn setting; no agent loop or KV pressure. Useful static regression control only. | Fully programmatic. Paper argues IFEval is becoming saturated even at about 2B while IFBench remains harder; no directly comparable Qwen3-1.7B result found. | Code [Apache-2.0](https://github.com/allenai/IFBench/blob/main/LICENSE); released data ODC-BY-1.0, with third-party outputs separately governed. | Dataset expansion count/version should be pinned locally before estimating; one-response tasks are far cheaper than agents but not the target construct. |
| **[FollowBench](https://github.com/YJiangcm/FollowBench)** ([paper, arXiv:2310.20410](https://arxiv.org/abs/2310.20410)) | 820 static prompts with five constraint types and increasing constraint levels. “Multi-level” means constraint difficulty, not multi-turn. | No aged instruction, tools, or native cache pressure. | Rule-based components plus LLM judging. No relevant 1–3B result found. | [Apache-2.0](https://github.com/YJiangcm/FollowBench/blob/main/LICENSE). | 820 × 256 tokens paired = **291.6 h**. |
| **[CFBench](https://github.com/PKU-Baichuan-MLSystemLab/CFBench)** ([paper, arXiv:2408.01122](https://arxiv.org/abs/2408.01122)) | 1,000 Chinese static prompts, 200 scenarios, 50 tasks, composed constraints. | No aged instruction, tools, or KV pressure. | GPT-4o evaluator. No 1–3B result found. | Repository has **no LICENSE file found**. | 1,000 × 256 tokens paired = **355.6 h**. |
| **[RuleArena](https://github.com/SkyRiver-2000/RuleArena)** ([paper, arXiv:2412.08972](https://arxiv.org/abs/2412.08972)) | 816 rule-guided reasoning problems drawn from 95 rules in airline, NBA, and tax domains. | Policies matter, but each item is essentially static rather than aged through a long interaction. | Automatic/exact components with task-specific processing; no relevant 1–3B score. | [MIT](https://github.com/SkyRiver-2000/RuleArena/blob/main/LICENSE). | 816 × 256 tokens paired = **290.1 h**. |
| **[StructFlowBench](https://github.com/MLGroupJLU/StructFlowBench)** ([ACL paper](https://aclanthology.org/2025.findings-acl.486/)) | Multi-turn instruction following across six structural relations among turns. | Tests dependency structure, not controlled old policy under native cache overflow; no tools. | GPT-4o-based multi-dimensional evaluation; no 1–3B result found. | [MIT](https://github.com/MLGroupJLU/StructFlowBench/blob/main/LICENSE). | Version/task count and response caps must be frozen before estimating; LLM-judge cost is additional. |

### Broad agent benchmarks screened out of the immediate gate

| Benchmark | Why it is not the present gate | Verifier / small-model floor | License and burden |
|---|---|---|---|
| **[MINT](https://github.com/xingyaoww/mint-bench)** ([paper, arXiv:2309.10691](https://arxiv.org/abs/2309.10691)) | 586 reasoning/code/ALFWorld instances, up to five turns with Python execution and optional language feedback. It measures interactive problem solving, not persistence of an early standing rule; context is capped around 4K. | Mostly programmatic/dataset metrics, optional GPT-4 feedback. Published Llama-2-7B five-turn success 9.7 and CodeLlama-7B 8.7, already near floor. | Apache-2.0. At 5 × 256 tokens: **1,041.8 h**. |
| **[ToolBench/ToolLLM](https://github.com/OpenBMB/ToolBench)** ([paper, arXiv:2307.16789](https://arxiv.org/abs/2307.16789)) | Large real-API tool-learning/evaluation collection (16,464 APIs, 126,486 training instances, average four reasoning-trace calls), but not a controlled multi-turn old-instruction experiment; APIs are a reproducibility dependency. | ToolEval uses ChatGPT pass/preference judging; authors report 87.1%/80.3% agreement with human pass/preference labels. The published open checkpoint is 7B, not 1–3B. | Apache-2.0. Full evaluation/run cost is not comparable without fixing API retrieval and trajectory caps; not a 30 h target. |
| **[AgentBench](https://github.com/THUDM/AgentBench)** ([paper, arXiv:2308.03688](https://arxiv.org/abs/2308.03688)) | Eight heterogeneous interactive environments (OS, DB, KG, games, household, web). No explicit old-policy or cache-overflow factor, and setup is heavy. | Mixed task-specific programmatic metrics; published open models begin around 13B and are weak. | Apache-2.0. Heterogeneous horizon prevents an honest aggregate estimate without traces; clearly over budget. |
| **[WebArena](https://github.com/web-arena-x/webarena)** ([paper, arXiv:2307.13854](https://arxiv.org/abs/2307.13854)) | 812 self-hosted web tasks, 241 templates. Goals are early, but there is no standing policy and long DOMs are not an old-instruction factor. Requires multiple Docker sites/browser plumbing. | Programmatic functional validators. Launch GPT-4 success 14.41%, GPT-3.5 8.75%, human 78.24%; a 1.7B floor is overwhelmingly likely. | Apache-2.0. At 15 actions × 64 tokens: **1,082.7 h**, excluding browser cost. |
| **[VisualWebArena](https://github.com/web-arena-x/visualwebarena)** ([paper, arXiv:2401.13649](https://arxiv.org/abs/2401.13649)) | 910 visually grounded web tasks. The frozen text-only Qwen trunk cannot satisfy the modality contract, so a result would test missing vision rather than the ledger. | Programmatic web validators plus visual input requirement; no relevant 1–3B text-only result. | MIT. Ineligible regardless of cost. |
| **[SWE-bench](https://github.com/SWE-bench/SWE-bench)** ([paper, arXiv:2310.06770](https://arxiv.org/abs/2310.06770), [site](https://www.swebench.com/)) | 300 Lite / 500 Verified / 2,294 full real repository issues. Long coding trajectories, but no early standing instruction and 1.7B coding/tool competence is the dominant bottleneck. | Exact repository tests. Official evaluation needs substantial Docker/storage resources; README cites roughly 120 GB free storage, 16 GB RAM, and eight CPU cores. No useful 1–3B agent score. | MIT. Agent tokens dominate; far beyond 30 h. |
| **[GAIA](https://arxiv.org/abs/2311.12983)** ([official dataset](https://huggingface.co/datasets/gaia-benchmark/GAIA), [leaderboard](https://huggingface.co/spaces/gaia-benchmark/leaderboard)) | More than 450 web/multimodal/tool questions in three levels; 165 public validation and hidden test answers. It tests breadth/autonomy, not old-policy retention, and requires web/files/vision. | Unambiguous final answers, but live-web variability. Launch human 92% versus GPT-4-with-plugins 15%. No useful 1–3B result. | Dataset is gated and its page requires agreement not to reshare; **no standard open license was displayed on the opened card**, so do not assume CC-BY. Heavy and ineligible for an offline frozen-text gate. |
| **[Agent-SafetyBench](https://github.com/thu-coai/Agent-SafetyBench)** ([paper, arXiv:2412.14470](https://arxiv.org/abs/2412.14470)) | 2,000 cases in 349 environments across eight safety risks and ten failure modes. Relevant to safe tool behavior, but not designed around instruction age or cache overflow. | Mixed environment/safety evaluation; paper reports no tested agent above 60% overall. No 1–3B mechanism result. | MIT. Full agent suite is far beyond budget. |

## What actually identifies the proposed mechanism?

Three properties must be separated:

1. **Instruction age:** a policy/constraint is observed early and is still outcome-relevant after later user/tool tokens. HANDBOOK.md, SOP-Bench, VeriFY, Lost in Conversation, tau/tau2, BFCL’s persistent tool/schema instructions, SysBench, and MultiChallenge’s retention subset have this to varying degrees.
2. **Native cache pressure:** the unmodified benchmark produces more history than the deployed cache limit `K`; the relevant early span would be evicted in the sham arm. HANDBOOK.md clearly contains documents above 8K; LongMemEval and LIFBench clearly contain long native inputs; ComplexFuncBench has a 128K condition; BFCL Long Context has large native observations but must be token-audited. Short conversational benchmarks do **not** prove this merely by having multiple turns.
3. **Agentic consequence:** later tool selection/arguments or environment state are judged, not only prose style. BFCL, HANDBOOK.md, SOP-Bench, tau/tau2, and some broad agent suites qualify. AgentIF, MultiChallenge, SysBench, Multi-IF, MT-Eval, and LIFBench do not supply a stateful tool consequence.

Only HANDBOOK.md cleanly has all three by design. BFCL is the viable budgeted agent test, conditional on demonstrating actual overflow. LongMemEval has age+pressure but the remembered object is a fact, not an instruction. LIFBench has pressure but puts the instruction at the end. This distinction matters: adding artificial distractor padding to a short benchmark can test the implementation, but it is not evidence of benefit on naturally long agent work and should be labelled a stress test.

## What prior mitigation evidence establishes—and does not establish

### VeriFY: closest direct evidence for re-instruction

[VeriFY](https://aclanthology.org/2026.findings-eacl.254/) compares mitigation methods on automatically checked 10/25/50-turn compliance:

| Model | Baseline average CCA | Re-instruct | Other relevant results |
|---|---:|---:|---|
| Gemma-7B | 56.67 | 63.33 | Teach 63.10; Rewrite 63.57; Summarize 60.95; IGA 40.95 |
| Gemma-2-27B | 46.43 | 77.62 | Teach 77.02; Summarize 79.40; IGA 83.12 |
| Llama-3-8B | 61.67 | 65.36 | Smaller but positive re-instruction effect |

Re-instruct repeats the instruction after a programmatic detector has already observed a noncompliant answer, typically adding about 30 tokens/use. The paper’s controlled “five-away” test deliberately injects a rogue response and probes four turns later. This is strong evidence that reminding can repair drift, but it is **not** evidence for an automatic salience finder on natural agent traces: the checker supplies oracle knowledge of failure, and the released dataset is still pending. The paper’s instruction-guided attention (IGA) also becomes incomprehensible at stronger settings, consistent with the project’s observed attention-dose failure rather than a reason to retry the wave.

### Persona drift and Re2

[Persona Drift](https://arxiv.org/abs/2402.10962) ([repository](https://github.com/likenneth/persona_drift)) repeats the full system prompt before each user turn (SPR) and compares split-softmax attention on 8- and 16-turn persona conversations. It reports better late-turn stability from repetition and earlier benefit from split-softmax, with interventions calibrated to roughly a 0.5-point MMLU degradation budget. But the intervention was studied on Llama-2-70B/GPT-3.5 persona behavior, not tool agents; full-prompt repetition is not token-matched against a sham; and the repository has no LICENSE file. It supports the plausibility of reminders, not the automatic-benefit claim.

[Re2 / “Re-Reading Improves Reasoning”](https://arxiv.org/abs/2309.06275) ([repository](https://github.com/Tebmer/Rereading-LLM-Reasoning)) repeats the current question and reports gains across reasoning datasets. It is Apache-2.0 and avoids evaluator leakage because the scoring targets are independent, but it is single-turn and repeats the whole question. It neither tests selecting old spans nor maintaining policies across an agent trajectory.

### Leakage/judge lesson

No reviewed mitigation paper supplies the exact comparison needed here: automatic selector + pin/echo versus an equal-token, equal-KV sham on deterministic, stateful agent outcomes. LLM judges can be biased toward a response that echoes rubric-like wording. The proposed studies avoid that channel entirely: BFCL is scored from executable calls/environment state, and HANDBOOK-policy must be scored from frozen structured criteria. The grader never sees which arm ran, and no expected call, gold action, criterion text, or checker output may enter the model-visible history or selector input.

## Ranked recommendation

### 1. BFCL V3 multi-turn sealed 64-case cohort — immediate agentic gate

**Why first:** permissive license, predefined user messages, stateful tool execution, deterministic evaluation, a native Long Context stratum, and a standard benchmark name. It is much lighter operationally than tau2 (no LLM user), WebArena (no browser stack), SWE-bench (no repository sandbox), or HANDBOOK’s official tasks.

**Cohort:** choose IDs by a public hash rule before outcomes: 32 from MT Base and 32 from MT Long Context, balanced over domains/templates and number of expected turns. Freeze one retry-free, temperature-zero trajectory per arm and identical environment seeds. Do not cherry-pick cases on which the current model succeeds.

**Budget sensitivity:** 64 cases × four model responses × 80 generated tokens × two arms / 1,440 = **28.4 GPU-h**. This is viable only if a CPU-only token/trace audit confirms that four/80 is realistic and a held-out competence preflight measures comparable end-to-end throughput. If the actual mean is five 96-token responses, the same cohort is 42.7 h and must be reduced *before unsealing outcomes* or funded above 30 h.

**Decisive caveat:** BFCL’s published Qwen3-1.7B MT floor means 64 strict final-state binaries alone are unlikely to have useful power. The primary endpoint therefore needs the official expected-call/state information at each turn (defined below), while official all-or-nothing task success remains mandatory. If the official evaluator does not permit a deterministic per-turn score without inventing new labels, then this cohort is only a pilot and **cannot clear the publication gate**; budget must be raised or a more tool-aligned frozen base must be used.

### 2. HANDBOOK-policy 64-item diagnostic — immediate mechanism gate; full HANDBOOK later

**Why second:** it most closely instantiates the causal story—old policies in long documents control later allowed and forbidden actions—and its verifier has positive and negative criteria rather than an LLM stylistic judge. It is Apache-2.0 and substantially less contaminated by generic benchmark training than older suites.

**Derived diagnostic:** before model inference, sample 64 independently checkable policy decisions from at least 16 official tasks and all five domains, stratified by source handbook token length (8–16K, 16–32K, >32K if supported), source-policy age, required versus forbidden behavior, and tool family. Present the native handbook/tool-observation text and a frozen task/state snapshot, then require one small JSON decision: action/tool, required arguments, and `allow|refuse|ask`. Gold labels must be mechanically derived from the existing criterion and independently checked once. The criterion/rubric stays hidden from both selector and model. Use a 96-token cap, giving **8.5 GPU-h** for two arms under the optimistic throughput model; prefill must be measured because it may dominate.

This is a **project diagnostic derived from HANDBOOK.md**, not an official score. It may clear the long-context mechanism half of the gate, never the agentic half. The future definitive validation is the official task loop on a funded cohort, eventually the 65 × 4 protocol.

**Why not SOP-Bench as #2:** it is an excellent SOP agent benchmark and merits a future replication, but its release is CC-BY-NC-4.0, full scale is 2,000+ tasks, policy token-length/KV pressure is not documented, and published 7B floors imply little headroom for a 1.7B base.

## Preregistration draft

### Claim and estimands

**Confirmatory claim:** “Using only the model-visible past, the frozen automatic ledger improves exact policy-following tool behavior on stateful BFCL V3 trajectories and improves exact old-policy decisions under native long context, relative to an equal-token/equal-KV sham, without increasing truncation or malformed tool calls.”

There are two co-primary estimands:

1. **BFCL turn-transition effect.** For episode `i` and required user turn `t`, let `Y_it=1` only if the assistant’s emitted call set is parseable/executable, matches an allowed official expected call/argument set, and produces the expected state transition for that turn; otherwise zero. The estimand is the episode-weighted paired mean difference `mean_i(mean_t(Y_it^ledger - Y_it^sham))`. Each episode, not each turn, is the independent cluster. If official artifacts do not uniquely define the per-turn expectation, do not improvise equivalence with an LLM judge; downgrade this endpoint to exploratory and declare the 64-case experiment underpowered for the main claim.
2. **HANDBOOK-policy exact-decision effect.** Binary exact structured decision per item, averaged within source task and then across tasks, ledger minus sham. Source task/document is the cluster so multiple criteria from one handbook are not treated as independent.

Mandatory secondary endpoints are BFCL official strict final-state/task success; BFCL tool-call parse rate, executable-call rate, exact argument accuracy, number of unnecessary calls, and completion; HANDBOOK required-behavior and forbidden-behavior accuracy separately; output tokens; truncations; and context overflow. Selector precision/recall and span age are mechanism diagnostics, not substitutes for outcomes.

### Arms and equal-context control

- **Ledger:** frozen `src/stencil/salience.py`/`salience2.py` version and thresholds select spans from model-visible history only; selected spans occupy the registered number of protected KV slots and the registered one-line echo template is inserted at the same defined turn boundary. No outcome-specific tuning.
- **Sham base:** use exactly the same wrapper, number of protected KV slots, echo delimiters, and token count. A sealed RNG chooses non-instruction history spans matched to selected spans on role, token length, age band, and position. Exclude current user text, tool results needed for the immediate next call, benchmark gold/reference fields, criterion/rubric text, and checker output from the sham pool using rules frozen before outcomes. If no valid matched sham exists, exclude that pair before generation and report it.
- **Optional natural baseline:** no pin/no echo is descriptive only unless separately funded. The confirmatory comparator is the sham, because “ledger versus fewer tokens” cannot isolate selection/preservation from generic repetition or context length.

The complete prompt token sequence outside the matched span content must be byte-identical across arms. Log token IDs, selected/sham span hashes, positions, age at every probe, protected-slot occupancy, and total model-visible token count. The selector must run before the future response and must never inspect the gold action.

### Cohorts and sealing

- BFCL: 64 fixed IDs, 32 Base and 32 Long Context, selected by published hash from the official V3 data commit; balance template/domain/expected-turn bins. A disjoint development set is used for adapter/competence checks and is never promoted into the confirmatory cohort.
- HANDBOOK-policy: 64 criteria from at least 16 tasks, all five domains, balanced 32 required/32 forbidden where artifacts permit, and predeclared handbook-length bins. Freeze source commit, extraction/tokenization, state snapshots, prompts, gold derivation, and item hashes.
- Deterministic decoding, temperature zero, one trajectory per arm, identical seeds and tool state. If any backend nondeterminism remains, use the same registered number of paired replications and cluster by episode/task; do not rerun failures selectively.
- The confirmatory analysis reads only sealed raw traces. All exclusions are applied from input/pre-execution facts, never from model quality.

### Real-KV eligibility

An item counts toward the **retention** estimand only if all are true:

1. Native benchmark history—not synthetic filler—exceeds the registered cache capacity `K` before the scored action.
2. The policy/instruction span was observed at least `K` intervening tokens before that action or the sham cache log demonstrates it would be outside the retained window.
3. The ledger selected the span automatically before the action.
4. The protected tokens are demonstrably present in the ledger cache and absent from the corresponding unprotected location in sham.

Report noneligible agent episodes separately as an agentic-generalization stratum. Do not silently call BFCL “long context” merely because it belongs to the category; tokenize every trace with the exact frozen tokenizer.

### Statistical test

- Report paired point estimates and percentile plus BCa 95% confidence intervals from 20,000 resamples of whole clusters (for BFCL, the highest-level reuse unit: template when IDs share a template, otherwise episode; for HANDBOOK, source task/document). Also report an exact paired sign-flip/randomization p-value at the cluster level.
- The two co-primary lower confidence bounds must both exceed zero. Control family-wise error with Holm at 0.05, or use the simpler, slightly more conservative Bonferroni rule of one-sided 97.5% lower bounds for both; do not switch conventions after seeing results.
- Show raw discordant-pair counts. If BFCL has fewer than 12 outcome-informative episode clusters or its sham strict success is below 5%, label it a **floor/inconclusive**, even if a turn-level p-value is small.
- Report both equal-episode weighting and a prespecified template-stratified estimate. The latter guards against a template family with many turns dominating the result.
- No practical threshold decides whether evidence exists. Effect size thresholds are additional release conditions, not replacements for confidence intervals.

### Safety/noninferiority gates

All must pass:

- **Truncation:** ledger minus sham truncation incidence ≤ +2 percentage points, and no context-overflow crash.
- **Tool syntax:** invalid/unparseable tool-call excess ≤ +2 points and its one-sided 95% upper bound < +5 points.
- **Execution:** tool execution-error excess ≤ +2 points; no increase in forbidden/incorrect state mutations on HANDBOOK-policy.
- **Length/cost:** mean generated-token excess ≤ 5% and p95 excess ≤ 10%; identical hard `max_new_tokens` and stopping rules.
- **Strict outcome:** BFCL official strict success point estimate must not decrease, even if partial turn-transition accuracy improves.
- **Interference:** the echo must not contain gold answers, expected API names/arguments that were not present in model-visible history, checker messages, or future user content.

The project’s supplied positive Multi-IF point estimate is supporting evidence, not permission to waive these safety gates. In particular, any existing registered truncation/safety failure must be closed by a fresh sealed noninferiority result rather than reinterpreted post hoc.

### Competence preflight before spending the sealed budget

Use a disjoint, outcome-unseen development sample and stop before confirmatory generation unless all conditions pass:

1. Byte-exact Qwen tool chat template, function-schema serialization, tool-call parser, tool-result role, stop tokens, and no-thinking/thinking setting match the frozen hand-rolled trunk. A stock vLLM score does not validate this adapter.
2. At least 80% of simple single-turn calls are parseable and executable, and the model completes at least one full multi-turn case in each selected BFCL stratum. These are competence checks, not benchmark claims.
3. Measured sham strict success is not obviously below 5%, and malformed-call rate is not above 20%. Otherwise BFCL measures base-tool failure and the gate is **blocked**, not failed in favor of the ledger.
4. End-to-end time/case, prompt-prefill time by length bin, generated tokens/turn, turns/case, and peak cache occupancy are measured. Recompute the cohort size before sealing; do not assume `0.4 optimizer steps/s = 0.4 generated tokens/s`.
5. At least half of the intended BFCL Long Context cohort meets the real-KV eligibility rules. If not, BFCL remains an agent test but cannot carry the retention claim.

### What falsifies “automatic benefit for agentic work”?

Any one of the following prevents the claim:

- BFCL paired effect is ≤0, its multiplicity-adjusted lower confidence bound is not >0, or the result is floor/inconclusive under the predeclared discordance/success rule.
- Benefit exists only on the derived HANDBOOK-policy diagnostic, Multi-IF, or short/static tasks, with no positive stateful BFCL result.
- Benefit disappears against the matched sham and exists only against a no-extra-token baseline; that supports generic repetition/context, not automatic selection.
- The selector uses oracle labels, benchmark criteria, future turns, manual spans, or per-task tuning.
- “Long-context” gains occur on cases that never exceed `K`, or protected instructions would not have been evicted.
- Any truncation, malformed-call, execution, strict-outcome, or length safety gate fails.
- The gain is carried only by a post hoc subset, one template family, or an LLM judge that can reward echoed wording.
- Qwen’s tool adapter fails competence preflight. That makes the study incapable of answering the mechanism question; it is not evidence for benefit.

## Is Qwen3-1.7B tool-competent enough?

The primary evidence says **possibly for individual calls, probably not for long strict trajectories without a careful adapter**:

- [ToolRM’s primary OpenReview paper](https://openreview.net/pdf/9c64848ea6efaa8d61c80ad9695b8645ef637546.pdf) reports greedy Qwen3-1.7B BFCL overall 55.74, non-live AST 80.23, live 71.35, but multi-turn only 10.25. Best-of-32 reward reranking raises MT only to 14.12. A specialized xLAM-2-1B reaches MT 35.12, which shows the bottleneck is alignment/tool training as well as parameter count.
- [FISSION-GRPO, ACL 2026 / arXiv:2601.15625](https://arxiv.org/abs/2601.15625) reports the raw Qwen3-1.7B BFCL V3 MT average at 7.80 and Long Context at 2.5. Its same base scores 7.9/12/25 on tau2 retail/airline/telecom. Training can improve these scores, but this project’s trunk is frozen.
- A natural-language echo inserted near a function call can damage strict JSON/tool syntax even when it preserves the right rule. That is why parse and execution error are hard noninferiority gates, not debugging metrics.

Consequently, do not spend 30 h until the adapter preflight succeeds. If it does not, the scientifically correct conclusion is: **the chosen frozen base cannot support a valid agentic test at this budget.** Switching to a tool-specialized model would answer a different model-level question and cannot be smuggled into the frozen-Qwen claim.

## Additional things the original candidate list misses

1. **HANDBOOK.md is the most important 2026 addition.** It operationalizes long policies, long trajectories, tools, and deterministic required/forbidden criteria in one Apache-2.0 benchmark. It is the right eventual external validation even though it is not the cheap first experiment.
2. **SOP-Bench is a close conceptual match.** Its expert SOPs and executable tasks are relevant, but its CC-BY-NC license, 2,000+ scale, and small-model floor reduce immediate utility.
3. **ComplexFuncBench explicitly combines constrained multi-step calls with a 128K condition**, but its constraints are mostly fresh user-query conditions, its 7–8B results are already near zero, it depends on real APIs, and the repository lacks a license.
4. **Tool competence and retention competence are separable.** Published 1.7B BFCL results show reasonable isolated syntax/schema behavior can coexist with near-zero strict multi-turn completion. A partial-turn endpoint is necessary for diagnosis, while strict completion remains the claim-bearing outcome.
5. **The cache counterfactual must be logged.** “Long context” in a benchmark title does not prove that the selected instruction crossed the actual eviction boundary. Position, age, cache occupancy, and survival must be recorded for every scored probe.
6. **Official versus derived scores must stay distinct.** A budgeted slice or policy probe can support a mechanism paper if sealed and fully disclosed, but it cannot be submitted or described as a full leaderboard result.

## Verified versus inferred/from-memory ledger

### Primary sources opened and what was verified

“No license” below means I checked the public repository/obvious license path and found no grant; public visibility alone is not an open-source license.

| # | Primary source opened | Verified from that source | License recorded |
|---:|---|---|---|
| 1 | [BFCL main README](https://github.com/ShishirPatil/gorilla/tree/main/berkeley-function-call-leaderboard) | Evaluator families, local-model workflow, leaderboard protocol | Apache-2.0 at parent repo |
| 2 | [BFCL V3 data README](https://github.com/ShishirPatil/gorilla/blob/main/berkeley-function-call-leaderboard/bfcl_eval/data/README.md) | 1,000 MT category counts, predefined turns, long-context/composite structure | Apache-2.0 |
| 3 | [BFCL official leaderboard](https://gorilla.cs.berkeley.edu/leaderboard.html) | Current category reporting and model results | Site; code/data under repo Apache-2.0 |
| 4 | [FISSION-GRPO, arXiv:2601.15625](https://arxiv.org/abs/2601.15625) and [ACL paper](https://aclanthology.org/2026.acl-long.1880/) | Qwen3-1.7B raw/trained BFCL and tau2 numbers | ACL paper CC-BY-4.0; benchmark licenses separate |
| 5 | [ToolRM OpenReview paper](https://openreview.net/pdf/9c64848ea6efaa8d61c80ad9695b8645ef637546.pdf) | Qwen3-1.7B/xLAM-1B BFCL breakdown and reranking | Paper access verified; no code/data license claim made |
| 6 | [HANDBOOK.md paper, arXiv:2607.25398](https://arxiv.org/abs/2607.25398) | 65 tasks, policy lengths, steps/calls, criteria, strict scoring | Paper access; repo license separate |
| 7 | [HANDBOOK.md repository](https://github.com/surge-ai/handbook) | Tools/services, runnable framework, task artifacts | Apache-2.0 |
| 8 | [HANDBOOK.md official leaderboard](https://surgehq.ai/benchmarks/handbook) | Four runs/task, current score scale, output-token scale | Benchmark repo Apache-2.0 |
| 9 | [SOP-Bench paper, arXiv:2506.08119](https://arxiv.org/abs/2506.08119) | 2,000+ tasks/12 domains, expert SOPs, executable ground truth | Paper access; repo CC-BY-NC-4.0 |
| 10 | [SOP-Bench repository](https://github.com/amazon-science/SOP-Bench) | Decision-point description, metrics, task counts, local-agent extensibility | CC-BY-NC-4.0 |
| 11 | [tau-bench paper, arXiv:2406.12045](https://arxiv.org/abs/2406.12045) | Policy/tool dialogue setup, state/communication scoring, pass^k | Repo MIT |
| 12 | [tau-bench repository](https://github.com/sierra-research/tau-bench) | Domain task counts and migration warning | MIT |
| 13 | [tau2 paper, arXiv:2506.07982](https://arxiv.org/abs/2506.07982) | domains, user/agent tools, simulator-error and cost analysis | Repo MIT |
| 14 | [tau2 repository](https://github.com/sierra-research/tau2-bench) | runnable structure and evaluator/task artifacts | MIT |
| 15 | [ComplexFuncBench paper, arXiv:2501.10132](https://arxiv.org/abs/2501.10132) | 1,000 cases, 128K, 3.26 steps/5.07 calls, ComplexEval, model table | No repository license found |
| 16 | [ComplexFuncBench repository](https://github.com/zai-org/ComplexFuncBench) | vLLM/RapidAPI procedure and public data link | No LICENSE found |
| 17 | [VeriFY EACL paper](https://aclanthology.org/2026.findings-eacl.254/) | 10/25/50-turn construction, programmatic CCA, all mitigation numbers | ACL CC-BY-4.0 |
| 18 | [VeriFY repository](https://github.com/pkrobinette/VerIFY) | Release still pending | No released dataset/license |
| 19 | [Lost in Conversation paper, arXiv:2505.06120](https://arxiv.org/abs/2505.06120) | 600 sharded instructions and degradation claim | Repo MIT |
| 20 | [Lost in Conversation repository](https://github.com/microsoft/lost_in_conversation) | tasks, validators, simulation code | MIT |
| 21 | [SysBench paper, arXiv:2408.10943](https://arxiv.org/abs/2408.10943) | 500 × 5 design, dependencies, evaluator, model results | No repo license found |
| 22 | [SysBench repository](https://github.com/PKU-Baichuan-MLSystemLab/SysBench) | data/code availability | No LICENSE found |
| 23 | [AgentIF paper, arXiv:2505.16944](https://arxiv.org/abs/2505.16944) | 707/50, instruction length/constraints, verifier mix, model results | No repo license found |
| 24 | [AgentIF repository](https://github.com/THU-KEG/AgentIF) | vLLM workflow and data layout | No LICENSE found |
| 25 | [MultiChallenge paper, arXiv:2501.17399](https://arxiv.org/abs/2501.17399) | 273, length/turn stats, category counts, short-context caveat | No repo license found |
| 26 | [MultiChallenge repository](https://github.com/ekwinox117/multi-challenge) | data/evaluator availability | No LICENSE found |
| 27 | [Multi-IF paper, arXiv:2410.15553](https://arxiv.org/abs/2410.15553) | 4,501, three turns, eight languages, rule checks | Repo Apache-2.0 |
| 28 | [Multi-IF repository](https://github.com/facebookresearch/Multi-IF) | release/archive state and evaluator | Apache-2.0 |
| 29 | [LIFBench paper, arXiv:2411.07037](https://arxiv.org/abs/2411.07037) | 2,766, 11 tasks, length bins, instruction-after-context placement | Repo MIT |
| 30 | [LIFBench repository](https://github.com/SheldonWu0327/LIFBench-2024) | data/evaluator availability | MIT |
| 31 | [LongMemEval paper, arXiv:2410.10813](https://arxiv.org/abs/2410.10813) | 500, 115K/1.5M scales, abilities, QA/retrieval evaluation | Repo MIT |
| 32 | [LongMemEval repository](https://github.com/xiaowu0162/LongMemEval) | dataset variants and evaluation code | MIT |
| 33 | [LoCoMo paper, arXiv:2402.17753](https://arxiv.org/abs/2402.17753) | conversation/session/token statistics and tasks | Repo CC-BY-NC-4.0 |
| 34 | [LoCoMo repository and license](https://github.com/snap-research/locomo) | current ten-conversation release and annotations | CC-BY-NC-4.0 |
| 35 | [MT-Eval paper, arXiv:2401.16745](https://arxiv.org/abs/2401.16745) | 168/1,170, turn patterns, lengths, judge/model table | Repo MIT |
| 36 | [MT-Eval repository](https://github.com/KwanWaiChung/MT-Eval) | data/evaluation availability | MIT |
| 37 | [IFBench paper](https://openreview.net/forum?id=yfYgwjj5F8) | OOD verifiable constraints and IFEval saturation motivation | Code Apache-2.0; data ODC-BY-1.0 |
| 38 | [IFBench repository](https://github.com/allenai/IFBench) | checker count, two-turn option, split licenses | Apache-2.0 / ODC-BY-1.0 |
| 39 | [Persona Drift paper, arXiv:2402.10962](https://arxiv.org/abs/2402.10962) | SPR/split-softmax protocols and mitigation scope | No repo license found |
| 40 | [Persona Drift repository](https://github.com/likenneth/persona_drift) | prompt/stability code availability | No LICENSE found |
| 41 | [Re2 paper, arXiv:2309.06275](https://arxiv.org/abs/2309.06275) | full-question rereading intervention and scope | Repo Apache-2.0 |
| 42 | [Re2 repository](https://github.com/Tebmer/Rereading-LLM-Reasoning) | implementation/data pointers | Apache-2.0 |
| 43 | [MINT paper, arXiv:2309.10691](https://arxiv.org/abs/2309.10691) | 586, five-turn setup, small open-model results | Repo Apache-2.0 |
| 44 | [MINT repository](https://github.com/xingyaoww/mint-bench) | runnable environments | Apache-2.0 |
| 45 | [ToolBench paper, arXiv:2307.16789](https://arxiv.org/abs/2307.16789) | API/tool dataset and ToolLLaMA scope | Repo Apache-2.0 |
| 46 | [ToolBench repository/ToolEval README](https://github.com/OpenBMB/ToolBench) | dataset stats, ChatGPT judge and human-agreement checks | Apache-2.0 |
| 47 | [AgentBench paper, arXiv:2308.03688](https://arxiv.org/abs/2308.03688) and [repo](https://github.com/THUDM/AgentBench) | eight environments, model scale, setup | Apache-2.0 |
| 48 | [WebArena paper, arXiv:2307.13854](https://arxiv.org/abs/2307.13854) and [repo](https://github.com/web-arena-x/webarena) | 812 tasks, validators, launch scores, self-hosting | Apache-2.0 |
| 49 | [VisualWebArena paper, arXiv:2401.13649](https://arxiv.org/abs/2401.13649) and [repo](https://github.com/web-arena-x/visualwebarena) | visual requirement and task scale | MIT |
| 50 | [SWE-bench paper, arXiv:2310.06770](https://arxiv.org/abs/2310.06770), [repo](https://github.com/SWE-bench/SWE-bench), [site](https://www.swebench.com/) | suite sizes, exact tests, resource requirements | MIT |
| 51 | [GAIA paper, arXiv:2311.12983](https://arxiv.org/abs/2311.12983), [dataset card](https://huggingface.co/datasets/gaia-benchmark/GAIA) | >450, levels, gating/no-reshare terms, modalities | No standard license displayed on opened card |
| 52 | [FollowBench paper, arXiv:2310.20410](https://arxiv.org/abs/2310.20410) and [repo](https://github.com/YJiangcm/FollowBench) | 820 static multi-level constraints | Apache-2.0 |
| 53 | [CFBench paper, arXiv:2408.01122](https://arxiv.org/abs/2408.01122) and [repo](https://github.com/PKU-Baichuan-MLSystemLab/CFBench) | 1,000 Chinese constraint prompts and GPT-4o evaluator | No LICENSE found |
| 54 | [RuleArena paper, arXiv:2412.08972](https://arxiv.org/abs/2412.08972) and [repo](https://github.com/SkyRiver-2000/RuleArena) | rules/domains/item scale | MIT |
| 55 | [StructFlowBench ACL paper](https://aclanthology.org/2025.findings-acl.486/) and [repo](https://github.com/MLGroupJLU/StructFlowBench) | six turn-relation structures and evaluator | MIT |
| 56 | [Agent-SafetyBench paper, arXiv:2412.14470](https://arxiv.org/abs/2412.14470) and [repo](https://github.com/thu-coai/Agent-SafetyBench) | 2,000/349, risk/failure taxonomy | MIT |

### Inferences, calculations, and supplied facts

- All GPU-hour numbers are my arithmetic under the explicitly stated 0.4 generated-token/s sensitivity model. They are **not** claims made by benchmark authors and are not valid if the supplied rate is a training-step rate.
- “Likely floor,” “best causal fit,” “native KV eligible,” rankings, and proposed cohort sizes are reasoned assessments from the verified benchmark/model results, not quotations.
- The BFCL four-response/80-token, tau/tau2 response counts, and several other token caps are budgeting assumptions, not published averages. They must be replaced by measured development traces.
- The internal ledger results in the research brief (synthetic 56-work counts, Multi-IF point estimate, and single-turn null) were accepted as project-supplied facts; I did not treat them as web-verified external evidence.

### From-memory/unverified items not used to support the recommendation

- I did not find a separately released, permissively licensed benchmark under the exact names **“IFEval-agent”** or **“LongIF”** that adds native stateful tools beyond AgentIF/LIFBench; no claim here depends on those names.
- **ConvBench** was not used because the name is ambiguous across unrelated conversation benchmarks and no candidate found in this pass met the old-policy + native-overflow + programmatic-agent criteria.
- **ToolBench “multi-turn”** was not conflated with BFCL V3. ToolBench/ToolLLM was verified as multi-step real-API tool use with an LLM evaluator; BFCL V3 was separately verified as the stateful multi-turn benchmark recommended here.
- Any benchmark/version counts not explicitly stated above are intentionally marked unknown rather than filled from memory.

## Bottom line for the release decision

Do **not** claim automatic agentic benefit from the existing Multi-IF point estimate or from a new static long-context score. Run the competence check, then the sealed BFCL V3 sham-controlled cohort and the independent HANDBOOK-policy mechanism diagnostic. Clear the claim only if both multiplicity-adjusted cluster-level effects are positive, BFCL official strict success is non-decreasing, real eviction is logged, and all syntax/truncation/cost gates pass. If Qwen3-1.7B remains at the published BFCL trajectory floor, the honest result is that the current budget/model cannot test the claim; the next scientifically justified expenditure is a larger official HANDBOOK.md validation, not another short chat benchmark.
