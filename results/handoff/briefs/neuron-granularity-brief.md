# Deep web research for gpt-6-astra: what is the right granularity for NEURON-level focus below expert routing? (2026-09-05)

Brian's question (verbatim): "I think style is not the correct granularity... what are some universal concepts that all
programming languages share, and then let's use the most likely one to perform the focus further on the neurons? or
would different experts even need to be loaded potentially in this instance? ... see if it even makes sense or if we just
let the experts handle it, or do even more experts?"
Repo /home/bmarti44/stencil-llm (CPU only; read-only; the GPU is running check 40d). Context: results/quick-checks/
README.md items 40b/40c (router-logit bias on Qwen3-30B-A3B flips Python -> JavaScript 32/32 clean; shuffled 0),
41/41b (dense-4B neuron scaling: null / junk), results/check40b-review-fable.md, results/moe-routing-research-astra.md,
results/astra-drift-assessment.md (Miller: slow control selects which stored representations express).
Use LIVE WEB SEARCH (2023-2026; cite URLs). Deliver results/neuron-granularity-research-astra.md (<= 120 lines):
1. UNIVERSAL PROGRAMMING CONCEPTS a code model must represent language-independently, with interpretability evidence
   that they are localized (neurons/features/heads/experts): e.g. recursion vs iteration; control flow (loops,
   branches); error handling; data-structure choice (map vs list); mutation vs pure/functional; typing; algorithmic
   strategy (e.g. sort algorithm); I/O vs computation; test-writing; refactoring. Cite: language-agnostic code
   representations, cross-lingual concept neurons in code LMs, SAE/feature studies on code, "concept" vs "syntax"
   neurons, algorithm-specific circuits, expert specialization analyses in MoE code models (Qwen3-MoE, DeepSeek-Coder-V2,
   Mixtral, OLMoE). Rank the concepts by (a) evidence of localization, (b) executable checkability of the
   distinction on short tasks, (c) independence from surface language.
2. EXPERTS vs NEURONS: does the literature show MoE experts partition by SYNTAX/language (surface) while concepts are
   spread across experts (residual/attention), or do experts also specialize by concept? What do fine-grained-expert
   models (DeepSeek-V3/V4 256 experts, Qwen3-235B-A22B 128 experts, OLMoE 64) change? Is "more experts" or "load a
   different expert set" a sensible lever for concept-level focus, and can a model's routing be biased at the concept
   level (evidence: expert steering papers by behaviour, not language)?
3. NEURON-LEVEL evidence: within-expert or dense-MLP neurons that causally control a concept (recursion neurons? loop
   neurons?) — any 2024-2026 results with interventions that flip an executable property without breaking code; the
   failure modes we saw (junk first tokens; gradient attribution sign errors) and what methods avoid them
   (activation patching, SAE features, causal scrubbing).
4. RECOMMENDATION: the single most likely concept pair to test next, at which level (router bias on the MoE / neurons
   within favored experts / SAE features / attention heads), with an executable checker (e.g. recursion vs iteration
   detected by AST across Python and JS), the quick-test design (<= 1.5 GPU-h; own seeds; no benchmark data; set-only
   first), pass/fail reading, and blunt odds. Say plainly if the honest answer is "let the experts handle it" or
   "concept-level focus needs SAE features, not raw neurons".
5. What to cut. HARD RULES: CPU only; never launch any GPU/model process; foreground only; never terminate or signal
   any process; no repo edits other than writing results/neuron-granularity-research-astra.md; never read the sealed
   IFEval input file or the sealed BFCL cohort contents.
