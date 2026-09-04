# Stencil research: decisions at the six current blockers

Date: 2026-09-04. Audience: Brian and the Stencil research team. Evidence cutoff: 2026-09-04.

**Recommendation:** finish the unchanged BFCL preflight and its one registered 4B fallback; stop BFCL if that fails. Make the independently budgeted selector comparison the next main experiment. Add explicit task/version state as a separate small prototype, test text consolidation with raw-source fallback, and keep amplification off. The literature supports these engineering choices more strongly than another wave search.

This report follows results/astra-program-review.md, LEDGER-PLAN.md “PROGRAM-REVIEW CLARIFICATIONS,” WORKLOG.md and README.md. The clarification record already limits the earlier claims. The reported 0/7 BFCL progress comes from the research brief; I did not inspect the running job’s outcomes. Root plan/PROTOCOL.md and plan/LEDGER.md are archived; their archived process/state records and current AGENTIC-PLAN.md were consulted. This is a prospective research recommendation, not an amendment or authorization to run experiments.

Research used live primary papers, official code and documentation, plus foreground CPU calculations. No GPU/model process, training, process signal, sealed IFEval input or sealed BFCL cohort contents were used. This report is the sole file written.

**Cost convention:** all GPU-h below are future planning estimates, not measured runtimes or spending commitments. For a local 4B, use a deliberately broad 20–60 output-token/s scenario, then add measured prefill, selector, extraction and checker overhead. GPU-h = total device-busy seconds/3,600; count every arm and memory-writing call. Author-hours include original scenarios, implementation and checking. Measure a separate setup slice before committing a new run budget; do not change the running BFCL registration. Research itself used 0 GPU-h.

## 1. Competence floor: 4B is a justified final check, not a likely rescue

### What is actually known

“Base” must be disambiguated: the original post-trained Qwen3 checkpoint before a research paper’s additional fitting is different from Qwen’s pretrained -Base checkpoint. Non-thinking is an inference mode of the original hybrid chat models. No trustworthy BFCL V3 multi-turn score for the actual pretrained 1.7B/4B/8B -Base checkpoints was found. The original release distinguishes these model families. [Qwen Team, Qwen3 Technical Report, May 2025](https://arxiv.org/html/2505.09388v1)

| Original post-trained model | Non-thinking BFCL V3 multi-turn evidence | How to use it |
|---|---|---|
| Qwen3-1.7B | Vanilla 12.5% in a June 2026 study: category scores 14/11/14/11. Its study removes training cases from three categories and evaluates the remainder; model revision and final denominator are not pinned clearly. | Low–medium confidence; a study-specific macro average, not a comparable official full-cohort estimate. The vanilla row precedes that study’s interventions. [Multi-Step Tool-Use RL, §4.1/Table 1](https://arxiv.org/html/2606.26027v1) |
| Qwen3-4B | 6.88% non-thinking; 25.38% thinking in the same paper. | High confidence in reported values; limited transfer to Stencil’s teacher-forced endpoint, renderer and context limit. [Song et al., EnvScaler, January 2026, Tables 4/9](https://arxiv.org/html/2601.05808v1) |
| Qwen3-8B | 11.8% non-thinking; 20.0/4.0/13.0/10.0 across Base/Missing Function/Missing Parameter/Long Context. | High reporting confidence; no evidence that merely going to 8B guarantees a useful floor. [Zhao et al., MUA-RL, August 2025, Table 2](https://arxiv.org/html/2508.18669v1) |

Do not rank these three models from those cross-study numbers. The often-quoted original non-thinking BFCL V3 scores 52.2/57.6/60.2 for 1.7B/4B/8B are **aggregate BFCL**, not multi-turn. [Qwen report, Tables 18/20](https://arxiv.org/html/2505.09388v1) The live official leaderboard is now V4; its current rows are not automatically comparable V3/non-thinking measurements. [BFCL official leaderboard](https://gorilla.cs.berkeley.edu/leaderboard.html) Qwen3-4B-Instruct-2507 is another checkpoint, so its scores cannot certify the prepared original 4B. [Official 2507 model card](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507)

EnvScaler uses native function-call interfaces, temperature 0.7, three-run averages and a 64K context setting. These differ materially from Stencil’s frozen setup. The 6.88% result is evidence against *assuming* competence, not a prediction of the registered 32-case outcome. [EnvScaler, Appendix B.2/C.2](https://arxiv.org/html/2601.05808v1)

### Alternative families: checker quality and competence are separate questions

“No credible original-4B result found” below is an evidence gap, not a measured zero.

| Family | Executable checking / construct | Evidence and suitability |
|---|---|---|
| τ-bench / τ²-bench | τ-bench checks final database state and required response information, with an LLM user simulator. | Original non-thinking 4B scores 20.15% in EnvScaler Table 9: some competence, but extra simulator cost and policy reasoning. Not an obviously cheaper rescue. [τ-bench, Yao et al., 2024](https://arxiv.org/html/2406.12045v1), [EnvScaler](https://arxiv.org/html/2601.05808v1) |
| ToolTalk | Handcrafted conversations, simulated tools and automated tool-sequence evaluation. | Small and implementable; no credible original-4B floor found. Sequence correctness still conflates tool skill with retention. [Farn et al., 2023 paper](https://arxiv.org/abs/2311.10775), [official code](https://github.com/microsoft/tooltalk) |
| AppWorld | Stateful applications with executable final-state tests, including collateral changes. | Strong agentic construct, substantial coding/integration demands. A 2026 paper reports a Qwen3-4B-Instruct baseline at 16.67% TestN/7.91% TestC, but checkpoint/mode comparability to original 4B is unresolved. [AppWorld, 2024](https://arxiv.org/abs/2407.18901), [CoEvolve, 2026](https://arxiv.org/html/2604.15840v1) |
| WorkBench | Workplace tools/databases with state-based automatic evaluation. | Appropriate executable outcome; no demonstrated original-4B competence advantage found. [WorkBench, 2024](https://arxiv.org/html/2405.00823v1) |
| MINT | Python tools and task-specific final checks; optional model-generated feedback. | Main setup permits five turns, so limited long-horizon evidence; no original-4B floor found. Feedback changes the assistance regime. [Wang et al., ICLR 2024](https://arxiv.org/html/2309.10691v2) |
| LongMemEval | Long-term conversational recall, including updates and temporal reasoning; official answer grading uses an LLM judge. | Useful memory evaluation, but fails the strict executable-task-checker requirement. No clean original-4B floor established. [Official evaluation code](https://github.com/xiaowu0162/LongMemEval) |
| MemoryAgentBench | Mixed metrics; FactConsolidation uses substring exact match for updated facts. | Good factual-update diagnostic, not executable agent success. Many questions from one stream are not independent episodes; Qwen3-Embedding-4B results concern retrieval, not a 4B answering agent. [Hu et al., 2025/2026, v3](https://arxiv.org/html/2507.05257v3) |
| ACEBench | Agent tasks check final states; other subsets include user adjustments and task switches. | Most promising external tool alternative: original non-thinking 4B 30.56% in EnvScaler. Original agent section is only 20 multi-step plus 30 multi-turn cases; multi-turn requires a user simulator. [ACEBench, Chen et al., 2025](https://arxiv.org/html/2501.12851v1), [EnvScaler Table 9](https://arxiv.org/html/2601.05808v1) |
| MemoryCode | Multi-session coding conventions with updates; regex/syntax checks. | Best construct match for retention and supersession, but checks do not establish functional code correctness. Published models start at 8B; no 4B floor demonstrated. [Rakotonirina et al., ACL 2025](https://arxiv.org/html/2502.13791v1) |

All can be *post-development evaluations* if their items, responses, checker feedback and scores never enter fitting or policy selection. Benchmark papers/aggregate scores may inform this research choice, so “no benchmark awareness” would be false. Freeze the complete policy and name the external family before item access; do not run several families and select the favorable one. Foundation-model pretraining exposure remains unknown.

### Options and recommendation

1. **Finish BFCL with the registered 4B fallback:** roughly 4–16 GPU-h planning range for the 32-case multi-arm check; 2–4 author-hours. Runtime uncertainty is high.
2. **Switch directly to ACEBench:** roughly 2–8 GPU-h plus separately counted user-simulator inference, 8–16 author-hours for adaptation. Better small-model evidence, but a small test and another integration project.
3. **Run the original authored study first, then MemoryCode once:** §3 costs first; later external adaptation roughly 4–8 author-hours and 5–15 GPU-h depending on history/query counts. Supports retention/update claims rather than general agent execution.

**Recommend option 1 to close the existing leg, followed by option 3 for the program’s next stage. Confidence: high in this decision rule; low that original 4B will clear every floor.** If an executable tool-agent claim remains essential, ACEBench is the named alternative to MemoryCode, selected before outcomes—not an additional opportunity to pass.

**Registration sketch:** preserve the exact existing fallback trigger. The current ledger requires full teacher-forced case pass ≥5/32 overall and ≥2/8 long-context, full per-turn ≥6/40 on long-context, base case pass ≥5/32 and base per-turn ≥6/40. Recheck every floor once on 4B; any failure closes Leg A as INCONCLUSIVE. Preserve the registered feasibility/safety rules and 30 GPU-h sealed-cost gate. Do not open the sealed cohort to diagnose failure. A passing preflight does not resolve the case-mean inference defect: any successor binary-endpoint analysis needs its own prospective registration before sealed outcomes are accessed.

## 2. Scope resolution: separate “worth remembering” from “applicable now”

### Literature and practice

| System | Actual update mechanism | Relevant limitation |
|---|---|---|
| MemGPT / Letta | Model-directed editable memory; Letta can attach/detach task-relevant memory blocks without deleting them. | Supplies an explicit state boundary, not guaranteed interpretation of arbitrary cancellation language. [Packer et al., 2023](https://arxiv.org/abs/2310.08560), [Letta block API, accessed 2026-09-04](https://docs.letta.com/api/typescript/resources/agents/subresources/blocks) |
| Mem0 | Contextual extraction followed by related-memory retrieval and ADD/UPDATE/DELETE/NOOP decisions. | A separate update pass, unlike sentence-only salience; reported setup does not establish 4B instruction-authority accuracy. [Chhikara et al., April 2025, §2](https://arxiv.org/html/2504.19413v1) |
| Zep / Graphiti | Temporally conflicting edges are invalidated while history is preserved; distinguishes system timestamps from fact-validity timestamps. | Ingestion recency alone is not event validity; a graph is unnecessary for a small instruction register. [Rasmussen et al., January 2025, §2.2.3](https://arxiv.org/html/2501.13956v1) |
| A-MEM | Linked notes and “memory evolution” update contextual descriptions, tags and associations. | Does not specify a universal instruction precedence/task-lifetime policy. [Xu et al., February 2025, §3](https://arxiv.org/html/2502.12110v1) |
| LangMem | Structured memory extraction with updates and optional deletes; application controls interpretation. | Useful API pattern, not evidence that inferred overrides are correct. [Official memory API](https://langchain-ai.github.io/langmem/reference/memory/) |
| Generative Agents | Retrieve experiences, reflect into higher-level memories, and plan. | Believable simulated behavior is a different endpoint from exact instruction supersession. [Park et al., 2023](https://arxiv.org/abs/2304.03442) |

LongMemEval explicitly tests knowledge updates and temporal reasoning; its design recommendations include time-aware retrieval. MemoryAgentBench FactConsolidation tests newer counterfactual facts replacing older ones. MemoryCode tests changed/deprecated coding instructions, making it closer to Stencil’s missing behavior. These three constructs should not be conflated. [LongMemEval, ICLR 2025](https://arxiv.org/html/2410.10813v2), [MemoryAgentBench](https://arxiv.org/html/2507.05257v3), [MemoryCode](https://arxiv.org/html/2502.13791v1)

A particularly relevant August 2026 revision separates semantic evidence extraction from policy execution. Its whole pipeline gains 10.8 points on FactConsolidation, but changing just the executor adds about 2 points, and zero at 262K; LongMemEval gives 26/45 versus 29/45, p=.45. This supports separation of responsibilities, not “latest timestamp solves memory.” [Reddy & Challaram, Reliable Post-Retrieval Assembly, v2](https://arxiv.org/html/2606.01435v2)

### Options and recommendation

1. Explicit task/key/version register driven by application events and unambiguous user updates: 0 GPU-h; 8–12 author-hours. Limited coverage of implicit transitions.
2. Same register plus one frozen contextual extractor for ordinary language: approximately 1–3 GPU-h for a small pilot; 12–20 author-hours total.
3. Adopt a full graph/agent memory stack or fit a supersession classifier: approximately 40+ author-hours and additional inference/training cost; unnecessary before measuring option 2.

**Recommend option 2, with deterministic precedence and soft retirement. Confidence: high in the architectural fix; medium in frozen-4B extraction and final-task benefit.** No retraining of the salience classifier is required. This is a bounded prototype, not a claim to solve arbitrary implicit scope.

**Registration sketch:**

- Store record ID, source turn/quote, role, instruction-or-fact kind, task ID, key, version, status and supersedes link. Keep immutable originals; distinguish task suspension from completion/cancellation.
- Inspect every incoming user message for updates **before salience admission**. A low-scoring “cancel that” must still reach the update handler. Application-verified completion may generate an event; an assistant merely saying “done” does not.
- The frozen extractor sees the new message, recent conversational context and at most 64 candidate records/4,096 input tokens; at most 256 output tokens. It proposes an operation and supporting quote with target IDs. Invalid references or unresolved scope cause no retirement and are recorded as unresolved.
- The program applies later-version precedence only within the same key and overlapping task scope under permitted authority. User-global instructions survive task switches. Tool results may update factual fields under a declared source policy; tool prose cannot cancel user instructions.
- Task IDs come from visible task events/application metadata or the frozen extractor, never hidden evaluator labels. Resuming a suspended task reactivates still-valid entries; cancelled entries require an explicit new instruction.
- Eligibility precedes either selector. Retired records cannot be newly pinned or echoed; record any copies still present in the common recent-context window. Do not claim all stale information has vanished from activations.
- Use 16 original setup episodes plus 64 different frozen feasibility episodes: 16 each for override, cancellation, completion/reopening and switching with a persistent rule. Include quoted old values and factual changes that are not instruction changes. No benchmark items or diagnostics enter authoring.
- Compare resolver-on/off with the same frozen rule selector, reader and budgets. Record active-state agreement, false retirements, stale reinjection and final executable success. Feasibility passes only with zero unsupported retirements/authority violations, no net final-success loss, and ≥50% fewer stale-execution episodes when the baseline has at least eight; otherwise record failure or insufficient evidence.
- This gate is operational, not a powered superiority claim. Keep it separate from §3’s primary comparison. If subsequently adopted, apply the identical frozen resolver to both arms in a newly named package evaluation; never credit a resolver difference to learned selection.

## 3. Learned versus rule selector: a useful 256-case experiment with an honest power limit

### Precedents and scope

IFEval demonstrates programmatically verifiable instruction evaluation; RULER demonstrates procedural control over retrieval difficulty and context length. MemoryCode is the closest authored precedent: 51 manually constructed conventions, 16 updateable, combined with generated names/personas/filler. These support the *method of construction*, not reuse of their items or templates. [Zhou et al., 2023](https://arxiv.org/abs/2311.07911), [Hsieh et al., 2024](https://arxiv.org/abs/2404.06654), [MemoryCode, §3](https://arxiv.org/html/2502.13791v1)

The target is delayed use of conversation information at one executable decision, conditional on a common history. Scripted histories isolate memory selection; they do not establish success of a free-running long-horizon agent.

**Lineage to register:** “Classifier fit-on = its previously frozen development-informed corpus; no new fitting. Setup = newly authored task/checker fixtures, disjoint from final sources and seeds. Evaluated-on = 256 new source episodes, never used for fitting, threshold selection, prompt selection or policy revision. Benchmark error examples and recorded benchmark responses are excluded from author prompts. Historical benchmark-family influence on the frozen classifier remains disclosed.”

### Authoring contract and frozen design

1. Give authors only this neutral contract and the original task/schema specification—not program-review diagnostics, benchmark items, selector scores or benchmark-derived examples. Authors should not know which policy is expected to win. No model or human author may consult benchmark prompts to create paraphrases.
2. Author **256 distinct source scenarios**, plus 32 unrelated setup scenarios. Names/IDs alone must not be used to turn a small number of stories into 256 independent semantic sources. No setup/final siblings.
3. Draw final episode factors independently from a frozen distribution: editing vs tool-work 50:50; indispensable user-origin vs tool-origin information 50:50; old vs more recent indispensable span 50:50; continuing/overridden/cancelled-or-completed/switched scope each 25%. Cross these factors; old tool facts and recent user facts must both matter sometimes.
4. These are sampling probabilities, giving expected counts 128/128 and 64 per scope category, **not outcome-conditioned balancing**. Record realized counts. Independently sampled factors preserve the simple mixture estimand in §5; do not enforce fixed strata then silently claim an IID-mixture exact test.
5. Each episode has 12–24 scripted turns and 4,096–8,192 tokens before the final request. Procedurally sample fictional entity names, 6–12 character identifiers, exact values, record order and irrelevant facts from pinned seeds; reject collisions using task data alone.
6. Construct benign distractors with both durable-looking and transient information; relevance must not be recoverable solely from role, position or a special marker. Include useful old information and useless recent information without making every case an engineered recency trap.
7. Editing tasks produce a bounded JSON patch or small text artifact checked against executable schema/content rules. Tool tasks make one final call into an isolated in-memory database; check the complete resulting state, including protected records. Tool responses providing needed facts appear in the scripted history.
8. The final query omits the earlier literal/rule being tested. One binary pass requires all prespecified final obligations and state invariants. Missing objects, no-op output, malformed syntax, stale values and unfinished generation fail; correctness must not be vacuous.
9. An independent checker reviewer validates each reference and adversarial mutations: old-ID substitution, cancelled action, wrong entity, wrong scope, empty output and collateral edit. References and hidden checks never enter selector, echo or summarizer inputs.
10. Freeze the current classifier’s files, threshold and segmentation. Freeze an independently implemented rule: prior-user spans newest-first, then prior-tool spans newest-first. It reads no classifier scores, quotas, selected counts or echo lengths. Deterministic tie-breaks use source offsets.
11. Both arms use pre-query eviction, the same protected system/schema prefix and most recent 1,024 history tokens. For C evictable history columns, pin cap B = min(256, floor(0.25 C)); added echo cap E = 256 tokenizer tokens, including header and source labels. Freeze the tokenizer and renderer.
12. Each policy admits whole spans in its own ranking while they fit, skips oversize spans and continues; no quota borrowing or artificial dose matching. Echo selected spans chronologically within E, with source role/turn labels and quoted tool facts. Report actual pin/echo use and information retained, not just ceilings.
13. Primary arms are the existing frozen classifier+pins+echo and rule+pins+echo. Keep the new scope resolver and digest **off in both** for this test, so their adoption is a distinct experiment. Disable all amplification. Fixed non-thinking decoding, one output per arm, ≤256 generated tokens; record paired case rows in the same run.
14. On the separate 32-case setup set, use the prepared 4B and freeze reader settings before measuring: full-context success ≥24/32 and full minus evicted success ≥8/32. Measure timing there. If either fails, do not open final outcomes; report that this proposed instrument lacks competence/headroom. Any redesign gets new setup/final sources.
15. The sole primary contrast is classifier minus rule binary success. Subgroup success, override errors, exact-ID errors, selector latency, retained tokens and failure types are descriptive. Use §5’s exact test; no selective retries, outcome filtering or extra confirmatory contrasts.

### Sample size: recomputed rather than assumed

Let q = P(the two policies disagree), δ = P(classifier-only pass) − P(rule-only pass). Under δ=.05, b-probability=(q+.05)/2 and c-probability=(q−.05)/2. Exact one-sided α=.05 power was computed on CPU by summing over M~Binomial(N,q) and B|M~Binomial(M,(q+.05)/(2q)), rejecting when P[Binomial(M,.5)≥B]≤.05. The q=.20 result was independently checked with integer binomial-tail enumeration. This is a calculation, not an empirical estimate of Stencil discordance. [Exact power method, author-maintained exact2x2 documentation](https://search.r-project.org/CRAN/refmans/exact2x2/html/powerPaired2x2.html)

| Assumed discordance q | Power at N=256, true gain 5 points | First N reaching 80% in the computed grid |
|---|---:|---:|
| .10 | 78.2% | 268 |
| .20 | 50.9% | 527 |
| .30 | 38.2% | 776 |
| .40 | 31.6% | 1,024 |

At N=256, a true ten-point gain has 97.4% power if q=.20 and 88.6% if q=.30. Thus 256 is credible for finding a substantial advantage, **not a generally powered five-point test**. Requiring both p≤.05 and an observed gain ≥.05 is a further gate: at true δ=.05 and q=.20 its probability is only 49.7%. No sample-size claim should confuse detection of a positive effect with proof that the population gain exceeds five points.

### Options and recommendation

1. **256-case fixed experiment:** approximately 3–8 GPU-h including setup and two final arms; 40–64 author-hours. The author estimate assumes 6–10 minutes per scenario plus 12–16 hours for shared machinery/checker review.
2. **A precommitted ~800-case experiment:** approximately 8–24 GPU-h and 95–155 author-hours; reasonable for detecting five points near q=.30, but much more authoring.
3. **A 64-case feasibility probe:** approximately 1–3 GPU-h and 12–20 author-hours; useful for gross defects, poor for the requested effect size.

**Recommend option 1 as a bounded decision experiment. Confidence: high in validity if sampling/lineage hold; medium that it will discriminate the policies.** Keep the learned selector only if its exact one-sided test passes, observed gain is ≥5 points (at least 13 net extra successes/256), and the operational limits below pass. Otherwise choose the rule by simplicity, saying “no worthwhile learned advantage demonstrated,” not “equivalent.” Do not enlarge N after seeing an unfavorable p-value.

**Registration sketch:** “N=256 independently authored/source-independent episodes sampled from the frozen mixture. One paired final binary endpoint. α=.05 one-sided, classifier superiority; effect and paired uncertainty reported. At least 13 net extra passes required for engineering adoption. Classifier-only invalid/truncated/repetitive-output episodes, compared with the rule, must number at most two; no checker-detected collateral state corruption is permitted. Invalid means parser/schema failure; truncated means reaching the generation limit without a complete valid output; repetitive means a normalized four-token block repeated at least eight consecutive times. Record each flag and their episode-level union. Mean total latency may not exceed 1.25× rule latency; measure all selector/echo overhead. These are operational cost/failure limits, not noninferiority proofs. If projected total runtime exceeds the predeclared 8 GPU-h budget, defer the test without shrinking its final cohort.”

## 4. Consolidation: test a digest, not a second learning program

### What the literature supports

- Recursive dialogue summaries and MaLP-style rehearsal provide text-memory update precedents; MaLP also includes parameter-efficient learning, so its whole result is not evidence for a training-free summary alone. [Wang et al., 2023](https://arxiv.org/abs/2308.15022), [MaLP, NAACL 2024, §2.3](https://arxiv.org/html/2309.11696v3)
- ReadAgent creates textual gist memories and rereads original passages when needed. This is the closest design precedent for a digest with source fallback. [Lee et al., 2024](https://arxiv.org/abs/2402.09727)
- MemoryBank uses time/reinforcement-inspired forgetting; Generative Agents forms higher-level reflections. Neither establishes that rarely used binding instructions or exact IDs can safely be forgotten. [Zhong et al., 2023/AAAI 2024](https://arxiv.org/abs/2305.10250), [Park et al., 2023](https://arxiv.org/abs/2304.03442)
- Learned gist tokens require training to encode prompts into latent tokens; they are distinct from ordinary text summaries on a frozen reader. [Mu et al., NeurIPS 2023](https://arxiv.org/abs/2304.08467)
- H₂O keeps recent/heavy-attention KVs; SnapKV selects per-head positions using a prompt-end observation window; PyramidKV varies cache allocation across layers. StreamingLLM keeps attention sinks and a recent window. These manage transient GPU state; they do not create durable, updateable semantic memory or establish recall of arbitrary evicted details. [H₂O, 2023](https://arxiv.org/abs/2306.14048), [SnapKV, 2024](https://arxiv.org/abs/2404.14469), [PyramidKV, 2024](https://arxiv.org/abs/2406.02069), [StreamingLLM, ICLR 2024](https://arxiv.org/abs/2309.17453)
- Sleep-time compute precomputes context-dependent information before queries arrive; benefits depend on amortization and query predictability. It is not inherently LoRA or compression. InfiniteICL is a genuine context-to-LoRA example, requiring generated QA data and fitting; it is outside this frozen/no-fitting experiment. [Lin et al., 2025](https://arxiv.org/abs/2504.13171), [Cao et al., ACL Findings 2025](https://aclanthology.org/2025.findings-acl.595/)
- LightMem provides a staged consolidation architecture, but its 2026 reproduction warns against assuming constructed memories beat raw retrieval: changing the retriever alone yields 58.1–75.5% accuracy; matched-token benefits depend on retriever/budget, and construction can remove needed evidence. [Fang et al., 2025/2026](https://arxiv.org/abs/2510.18866), [Zhou et al., July 2026 reproduction](https://arxiv.org/html/2607.29104v1)

### Options and recommendation

1. Extractive compaction: deduplicate records and remove scaffolding while preserving exact values; 0–1 GPU-h, 6–10 author-hours.
2. Source-linked abstractive digest plus verbatim literal/state register and one bounded raw lookup: 2–6 GPU-h, 12–24 author-hours.
3. Learned gist/KV encoders or LoRA memory: a separate fitting/integration program; plausibly 16–40+ author-hours before a useful trial, GPU cost not responsibly predictable from this repo’s evidence.

**Recommend option 2, capped at one feasibility study. Confidence: high in experiment priority; medium that it will preserve fidelity at a useful cost.** “Neural” is too broad to imply that cache pruning, text digestion and weight learning solve the same problem.

**Registration sketch:**

- Author 16 setup and 64 separate feasibility episodes, disjoint from §3 and all external evaluation items. Each has three successive ~1,024-token chunks containing exact identifiers/numbers, compressible prose, corrections, cancellations and task changes.
- Freeze writer, reader, scope handling, retrieval rule and prompts after setup. After each chunk, produce a recursive digest from prior digest plus new text, ≤512 tokens including exact-value/state entries and provenance. Writer sees only history available then; no final questions or answers.
- Use three arms: raw-source retrieval, digest-only, digest plus at most one source lookup. All reader calls share a 512-token memory ceiling, common query/recent context and a frozen source-ranking policy. Fallback text replaces digest text within the ceiling; charge the triggering read and any repeated reader call.
- A CPU “rehearsal” check verifies source IDs, copied literals and supported state transitions against originals. It can reject unsupported content but cannot certify all omissions or semantic claims. No hidden-answer oracle repairs the digest; no repeated prompt search.
- Ask four prespecified independent continuation questions per final history, branching from the same final memory without feeding answers back. One episode outcome is all four executable checks passing; questions are not four independent statistical cases.
- Record per-cycle compression, omitted necessary facts, literal corruption, false state changes, final checks, stale-rule execution, invalid/truncated outputs, fallback frequency and ingest/read token counts and latency. Retain both intended source references and actually supplied reader text.
- Feasibility requires final active digest ≥4× smaller than original history and digest-package success ≥48/64 episodes; no fabricated literals or unsupported state transitions; no more than two digest-package losses among the 64 episodes the raw arm passes; no added stale-rule execution or invalid/truncated outputs. Report raw-arm failures and compression relative to the same selected source records as well as whole history, so dropping irrelevant filler cannot masquerade as semantic compression.
- Compute total ingest-plus-read tokens and device time for the four queries, and report the one-query cost. Do **not** require total-cost savings against 512-token raw retrieval: three ~1,024-token ingestion passes already cost more input tokens than four full 512-token memory reads. The feasible first gate is a smaller active representation with the stated fidelity limits. If mean digest read cost is lower, report estimated break-even Q = ingestion overhead / (raw read cost − digest read cost), separately for tokens and device time; otherwise report no finite break-even. Any later amortization experiment fixes Q prospectively. A feasibility pass does not establish total storage or compute savings.
- Cap at 6 GPU-h; no post-outcome rescue. Treat the result as engineering feasibility, with paired counts/intervals, not proof of noninferiority. Keeping the raw archive means total durable storage has not shrunk; the claim concerns active representation and read cost only.

## 5. Statistics: use the binary endpoint to simplify both inference and implementation

### What is valid

For IID paired binary outcomes, marginal success difference equals discordant probability difference. Conditional on m=b+c discordances, the equal-marginal null gives b~Binomial(m,.5). Exact McNemar is therefore the sign test on **binary pair differences**, with ties omitted from the test but retained in the effect denominator. [Fay & Lumbard, Statistics in Medicine 2021](https://onlinelibrary.wiley.com/doi/abs/10.1002/sim.8829), [author-maintained McNemar documentation](https://search.r-project.org/CRAN/refmans/exact2x2/html/mcnemarExactDP.html)

A sign test on nonbinary case-mean differences instead asks whether positive differences are more frequent than negative ones, conditional on a difference. It does not test mean benefit. Permuting signs of arbitrary case means requires symmetry/exchangeability or a valid paired randomization design; enumerating all signs supplies computational exactness, not those assumptions. [Fay & Lumbard](https://onlinelibrary.wiley.com/doi/abs/10.1002/sim.8829), [SciPy permutation-test definitions](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.permutation_test.html)

The repo review’s counterexample remains decisive: D=+.2 with probability 5/6 and −1 otherwise has mean zero; six positive cases occur with probability (5/6)^6=.3349 yet get sign-flip p=1/64. That is local mathematical evidence against the old distribution-free mean claim.

### Options and recommendation

1. **Exact McNemar on one final binary outcome/case:** simplest scientifically relevant answer; negligible CPU, 0 GPU-h, 1–2 author-hours to register/verify.
2. Exact sign test on case-mean signs: similarly cheap, but changes the estimand to frequency of improvement.
3. Case-mean permutation/bootstrap: preserves a richer outcome only with additional assumptions or asymptotic approximation; no justified small-k exact mean-benefit guarantee here.

**Recommend option 1. Confidence: high**, conditional on independent sampling from the registered episode distribution, fixed policies and no outcome-based exclusions. Multiple turns, seeds or questions from the same source are not new independent cases. Randomizing arm execution order addresses runtime order effects; it does not create the missing sign-symmetry justification for arbitrary case means.

**Registration text:**

> The sole confirmatory estimand is Δ=P(Yclassifier=1)−P(Yrule=1) for a fresh episode sampled from the frozen authoring distribution. Both policies run on every episode from identical prescribed histories. b counts classifier-only successes; c counts rule-only successes; N includes all paired episodes. Test H0:Δ≤0 against Δ>0 with p=Σ from j=b to b+c of choose(b+c,j)·2^(−b−c); set p=1 if b+c=0. Reject at p≤.05. Report b,c, both marginal rates, Δhat=(b−c)/N and uncertainty. No mid-p, asymptotic replacement, outcome-dependent stopping, selective reruns or exclusion of difficult cases.

> For a conservative paired 95% interval for Δ, obtain separate two-sided 97.5% Clopper–Pearson intervals [Lb,Ub] for b/N and [Lc,Uc] for c/N, then report [Lb−Uc,Ub−Lc]. By the union bound both discordant probabilities are covered with probability at least .95, without assuming those counts independent. This interval may be wider than an interval compatible with McNemar and need not exclude zero whenever its test rejects; the primary test and descriptive interval have deliberately separate roles.

The interval construction above is a transparent conservative derivation, using exact binomial intervals already available in SciPy. A tighter compatible interval is available from Fay–Lumbard/exact2x2, but adding that dependency is unnecessary for this decision. [SciPy Clopper–Pearson API](https://docs.scipy.org/doc/scipy-1.16.1/reference/generated/scipy.stats._result_classes.BinomTestResult.proportion_ci.html), [exact2x2 implementation documentation](https://search.r-project.org/CRAN/refmans/exact2x2/html/mcnemarExactDP.html)

> Generation failures, malformed output, truncation and exhausted action budgets score zero; record their cause. A predeclared infrastructure interruption may resume the missing attempt from identical state without changing completed outputs. An unresolved harness defect invalidates the run; it does not permit dropping selected pairs. The five-point threshold is an engineering adoption requirement on the estimate, not a test that Δ>.05. No superiority finding means “not demonstrated,” never equivalence.

With fewer than five discordant pairs, even all wins cannot pass one-sided .05 (four wins give .0625; five give .03125). At small k, statistical honesty often means inconclusive. Operational “at most two extra failures” gates are not safety noninferiority: even zero events in 64 independent cases leaves a one-sided 95% binomial upper bound of 4.57% (CPU calculation).

## 6. Miller-inspired focus: external positives do not warrant another wave now

### Evidence for steering, with the relevant boundaries

| Method | Positive evidence | Why it does not resolve this blocker |
|---|---|---|
| PASTA, ICLR 2024 | Reweights specified input spans through profiled attention heads, without changing base weights. | Profiling uses task examples; information remains in context. It does not restore removed arbitrary literals. [Zhang et al., paper/code](https://github.com/QingruZhang/PASTA) |
| SpotLight, EACL March 2026 | Dynamic deficit-triggered attention bias; Qwen2.5-3B IFEval loose prompt accuracy .42→.53. Final paper uses target .1 for all tasks/models. | Multi-turn evaluation retains history; very long contexts/responses remain untested, and extreme emphasis can be incoherent. Close to Stencil’s already tested deficit route. [Venkateswaran & Contractor, final paper](https://aclanthology.org/2026.eacl-long.174.pdf) |
| Instruction-specific activation vectors, ICLR 2025 | Contrastive directions improve format, length and lexical compliance. | Examples/validation determine vectors and strengths; repetition and factual-error tradeoffs are documented. Strength remains fixed through generation; no evicted-ID recovery result. [Stolfo et al.](https://arxiv.org/html/2410.12877v2) |
| CAST, ICLR 2025 | Prompt-conditioned gating of behavior vectors gives selective refusal. | Once triggered, steering continues at subsequent decoding steps. This is routing, not evidence for clearing-based retention. [Lee et al.](https://arxiv.org/html/2409.05907v3) |
| InstABoost, revised March 2026 | Principled additive attention bias improves behavior/fluency tradeoffs. | Validation selects strength; excessive focus removes useful context. Another close attention-bias relative, not a new memory carrier. [Guardieiro et al.](https://arxiv.org/html/2506.13734v3) |
| ReFT, NeurIPS 2024 | Learns efficient interventions in hidden representations of frozen trunks. | Intervention parameters are trained. It starts another learning program rather than supplying a no-fitting rescue. [Wu et al.](https://arxiv.org/abs/2404.03592) |
| V-Steer, July 2026 | Edits retained value-cache entries once, using selected heads; improves instruction-hierarchy conflicts while preserving fused decoding. | Distinct future candidate, but no Qwen3-4B evicted-memory demonstration. Aggressive V-Simple loses 8.5 MMLU points; aligned IHEval under V-Steer falls 55.6→53.6. Effects depend on variant/dose. [Zeng et al., Tables 6/7](https://arxiv.org/html/2607.26228v1) |
| KV Cache Steering, 2025 | One-shot cache interventions derived from reasoning traces alter reasoning behavior. | Reasoning induction is not demonstrated exact delayed-instruction retention. [Belitsky et al.](https://arxiv.org/abs/2507.08799) |

Version reconciliation matters: SpotLight’s 2025 preprint selected targets from .1–.4 by task; the 2026 final paper fixes .1. The final version supplies a better transfer argument, but still does not test eviction recovery. [Final §3.2 and limitations](https://aclanthology.org/2026.eacl-long.174.pdf)

Attention cannot directly access a KV entry that has been removed. Some other retained text/vector/state could encode that information, so this is not a proof that all activation-mediated memory is impossible. Stencil’s own review supplies the closer negative: sustained function vectors truncate 14–15/20 cases; clearing reduces truncation to 2/20 but leaves compliance at 13/56 versus pin+echo 46/56.

### Options and recommendation

1. **Amplification off; retain and reinject:** 0 incremental GPU-h, 1–2 author-hours beyond §3.
2. One future V-Steer-on-retained-memory feasibility study: approximately 2–6 GPU-h, 8–16 author-hours, after competence and the selector question are resolved.
3. A learned ReFT/conditional-vector program: approximately 8–24 GPU-h for a bounded prototype plus 16–32 author-hours; new development data and registration, uncertain return.

**Recommend option 1. Confidence: high for the program decision; medium for generalizing any steering paper to this trunk.** There is credible 2024–2026 evidence that transient steering can help use present instructions. No reviewed evidence establishes reliable, degeneration-free recovery of arbitrary evicted instructions on this substrate. Another wave now has lower decision value than scope, competence and a fair selector comparison.

**Registration sketch:** “All next-study arms disable attention amplification and residual steering. Record an intervention counter required to remain zero. The mechanism under test is selective preservation and source-labelled reinjection. Score exact final success, active-versus-stale instruction use, nonce fidelity, truncation/repetition and total resource use. Positive results support engineering retention/reactivation; they neither validate a biological traveling-wave mechanism nor rule out future activation steering.”

If later reopened, use one prespecified V-Steer setting on 64 new episodes against the identical retained-memory+echo baseline; no sweep on those outcomes, and no five-point-power claim. That would test utilization of retained information, not restoration after deletion. Miller’s traveling-wave account remains inspiration; its biological claims require measurements this program does not make. [MIT Picower account](https://picower.mit.edu/news/cognition-and-consciousness-arise-analog-computations-says-new-theory)

## Execution order and research limits

Close the already registered BFCL decision first. Prepare §3’s original sources/checkers next; the small scope and digest prototypes are independent and must not change that frozen comparison after outcomes. Adopt additional memory machinery only through a newly frozen package comparison. Name one external family before its items are accessed.

Search covered exact Qwen model/mode/BFCL-version combinations; all eight requested alternative families plus ACEBench/MemoryCode; named memory systems; consolidation, KV and context-to-weight methods; exact paired inference; and PASTA through 2026 steering. Follow-up searches resolved the 1.7B split mismatch, 4B checkpoint ambiguity, SpotLight final-version change, post-retrieval executor ablation and LightMem counterevidence. Primary sources were preferred; older statistical references were retained because the mathematics is not a 2023–2026 novelty.

Remaining gaps are substantive: no matching published 4B result certifies Stencil’s exact preflight; no original-4B benchmark simultaneously establishes easy long-horizon competence and clean memory isolation; 4B scope extraction and repeated exact-literal digestion are unvalidated. Some live documentation routes redirect, and some publisher pages blocked full-text access; consequential claims were checked against available primary papers/code or explicitly qualified. Search stopped when further broad retrieval was unlikely to change the six recommended decisions.
