# Unblocking automatic rule maintenance

Prepared for Brian and the Stencil team, 2026-09-07. Scope: choose the next small diagnostic after two exposed-development failures. This is an implementation decision brief, not a benchmark survey or a claim of reliable automation.

**Recommendation: test rule understanding separately from register bookkeeping.** Do not launch another full maintenance run yet. Keep automatically maintained prose as a valid candidate: matching good manual reminders automatically remains the goal.

## What the experiments establish

Both eight-turn conversations failed complete maintenance in both attempts. Attempt02 added explicit semantic guidance but still achieved 0/48 complete views and 0/2 whole trajectories. Some meaningful dependency and permission content appeared, but global language rules remained absent. Exact request/response and state replay passed. These exposed-DEV outcomes locate a problem in the complete recipe; they do not isolate its cause. [Attempt02 and independent audit](../../quick-checks/maintenance-dev-02/RESULTS.md).

The current request combines natural text, previous state, opaque IDs, lifecycle rules and a large schema in one user message. The schema is plain prompt text, not a constrained-decoding parameter. The second cold ETL response ended normally after 75 tokens with an empty update. Adding format enforcement alone cannot make that syntactically valid omission semantically correct. This is a deduction from the saved request, response and schema, not a literature result.

## Evidence that changes the next action

**The documented request shape is valid.** Qwen documents user-only requests and the same top-level non-thinking flag. The local frozen tokenizer renders the expected empty thinking prefix; its reconstructed 2,039 tokens match the server's recorded cold-prompt count. This is CPU reconstruction, not a capture of server-rendered bytes. The image pin is an OCI digest, not a Git commit, and current documentation does not establish the exact installed implementation. [Qwen deployment guide](https://qwen.readthedocs.io/en/latest/deployment/vllm.html), [local template audit](template-audit.json).

**Neither schema text nor deterministic decoding is a proven culprit.** Qwen recommends different non-thinking sampling settings, but its explicit warning about greedy decoding is under thinking mode. vLLM documents schema-constrained generation and also recommends explaining the schema in the prompt. Therefore neither a sampling change nor removing JSON is justified as a known fix. Keep sampling fixed for the diagnostic. [Original Qwen3-30B-A3B model card](https://huggingface.co/Qwen/Qwen3-30B-A3B/raw/main/README.md), [vLLM structured-output documentation](https://docs.vllm.ai/en/latest/features/structured_outputs/).

**Separating extraction and update has precedent, not proof of transfer.** Mem0's 2025 method first extracts candidate facts, then asks an LLM to reconcile them against retrieved memories. Its conversational-question-answering results do not measure Stencil's complete scoped instruction histories or isolate decomposition as the cause of improvement. [Chhikara et al., Mem0, April 2025, section 2.1](https://arxiv.org/html/2504.19413v1).

**The literature does not require a versioned register.** MemGPT maintains an editable block of unstructured text alongside original-message recall storage. This makes automated prose a credible comparison; its evidence does not establish reliable instruction cancellation or parity in coding quality. [Packer et al., MemGPT, February 2024 revision, sections 2.1–2.3](https://arxiv.org/html/2310.08560v2).

**Preserve evidence, and avoid copying a whole memory product.** Mem0's April2026 README describes a move to add-only extraction alongside several retrieval changes; its managed-platform results include proprietary optimizations. Its authors attribute some earlier losses to overwriting/deleting information. This is evidence against treating the older architecture as settled, not causal proof that add-only is better. We must not adopt its equal treatment of agent-generated facts as authority for user rules. [Mem0 author repository](https://github.com/mem0ai/mem0), [author release explanation](https://mem0.ai/blog/mem0-the-token-efficient-memory-algorithm).

LongMemEval's representation experiments find that replacing original conversation values with summaries or facts can lose information, while using derived facts to enrich retrieval keys preserves the originals. These are QA experiments, not tests of our authorization or lifecycle semantics. Retain source messages even when testing simpler notes. [Wu et al., LongMemEval, March2025 revision, sections 5.2–5.3](https://arxiv.org/html/2410.10813v2).

## Smallest next diagnostic

Prepare and review a separate four-call DEV diagnostic: the two existing cold Kimi messages, each under two minimal contracts. In A, list all durable obligations in plain prose, including scope and modality. In B, use the same extraction instruction and source but require the existing transaction contract from an empty state. Freeze the exact prompts, reading and resource bound first; keep the same model, thinking flag, temperature, seed and token cap. No example answers, retries or hand-corrected outputs. This is a proposal, not an executed or fully registered test.

Score whether every explicit obligation is present with correct scope and modality, and whether anything is invented. Report structural validity separately. A succeeds/B fails would implicate combined extraction-and-transaction demands; it would not distinguish serialization from every other contract difference. Both succeed would motivate investigating the surrounding prompt packaging. A fails would direct work away from transaction engineering toward basic extraction/model setup. None of these outcomes measures multi-turn maintenance, fresh generalization or useful coding performance.

If a simple extractor earns further work, the subsequent test must include changes, retractions, reinstatement, scoped permissions, rejected quotations and self-carried mistakes on newly authored DEV conversations. Do not bypass the existing two failures or the three-failure maintenance stop-loss by relabeling a full maintenance trial. No third maintenance attempt, architecture adoption, paid service or larger run is authorized by this brief.

## Limits and stopping decision

Two independent research lanes reviewed primary protocol sources and memory methods; the coordinator independently checked consequential claims. Additional inspected work included A-MEM and studies of memory-error propagation, but it did not change the minimal recommendation and is cataloged in the evidence notes. Current docs and vendor comparisons have version and attribution limits. Incidental paper/search examples were not used as development data. No downloaded benchmark bank entered this work.

Research stops here because the remaining question is experimental: can this model extract these rules when relieved of register bookkeeping? The evidence supports that diagnostic, not a promised solution. Markdown structure and local links were checked; no PDF or visual rendering was produced.
