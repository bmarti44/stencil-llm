Fit-on: none. Development-on: the two exposed Kimi conversations, attempts 01/02 and synthetic controls. Evaluated-on: none. Primary-source method/documentation reading adds no benchmark bank or examples to development data.

# Research brief — independent closing accuracy review

2026-09-07 · Round 1 · Reviewer: gpt-6-astra, xhigh, native session `/root/maintenance_revision_review`. Explicit user-requested Astra xhigh replaces historical Opus guidance. Author-disjoint from the research lanes and coordinator's synthesis. Purpose: verify the brief's consequential factual claims and bounded recommendation; threat model: trusted but fallible researchers. Only this review file was written. No model inference, GPU use, code/output edits or commits. Web access was limited to cited primary sources; incidental examples were not collected or used as development data.

**Score:** 95 / 100

**Verdict:** PASS — research accuracy and diagnostic recommendation, not experiment readiness or model success.

## Findings

No material correction required; zero open high/critical findings.

The brief preserves the two failed maintenance attempts and correctly limits their meaning. Attempt 02's reported 0/48 complete views and 0/2 trajectories agree with its independent accuracy review; partial relevant prose is acknowledged. This review does not repeat that full trajectory audit. It independently verifies the consequential cold-call evidence below.

The proposed four calls are explicitly prospective and not fully registered. Plain extraction versus extraction plus the existing transaction contract is a useful small discriminator. The brief correctly limits any A/B contrast to combined contract demands, without identifying serialization alone as the cause. Exact prompts, scoring and resource bound still require freezing/review before execution. It neither relabels a full maintenance trial nor erases the two failures or three-failure stop-loss.

## Evidence checks

- Independently reconstructed the saved cold prompt with the local tokenizer, offline and without loading model weights. Rendered bytes and SHA256 match `cold-rendered-prompt.txt`; flat `input_ids` count is **2,039**, matching both audit and saved server usage. The expected empty-thinking assistant suffix matches. Receipt/tokenizer hashes match the audit. Its disclosed scratch `len(BatchEncoding)=2` error is absent from the final count and does not affect the registered run.
- The saved request has one user message and no constrained-decoding field; its schema is inside prompt content. The cold response finishes `stop` after **75 completion tokens** and proposes no operations. An empty update remains legal under the schema, so format validity alone cannot certify the omitted obligations. The freeze uses an OCI digest reference. These checks corroborate CPU reconstruction, not server-rendered byte identity or serving correctness.
- Qwen's guide documents the user-only request and top-level `chat_template_kwargs` switch. Its model card recommends non-thinking sampling settings but places the explicit greedy-decoding warning under thinking mode. vLLM recommends explaining schemas in prompts alongside constrained generation. The brief therefore avoids presenting sampling or JSON changes as established fixes. [Qwen guide](https://qwen.readthedocs.io/en/latest/deployment/vllm.html), [model card](https://huggingface.co/Qwen/Qwen3-30B-A3B/raw/main/README.md), [vLLM documentation](https://docs.vllm.ai/en/latest/features/structured_outputs/).
- Mem0 2025 section 2.1 explicitly separates candidate extraction from reconciliation against retrieved memories. Its system-level conversational QA comparison does not isolate decomposition's causal contribution or test Stencil's scoped obligations. MemGPT sections 2.1–2.2 describe editable unstructured working text and recall storage of messages. These support precedents for simpler extraction and automated prose, without establishing transfer or register necessity. [Mem0 paper](https://arxiv.org/html/2504.19413v1), [MemGPT paper](https://arxiv.org/html/2310.08560v2).
- Mem0's April 2026 repository/release account describes add-only extraction alongside retrieval changes, equal treatment of agent-generated facts and proprietary platform optimizations. The brief correctly attributes the overwrite/deletion explanation to its authors and makes no causal algorithm-win claim. LongMemEval sections 5.2–5.3 support information-loss concerns and preserving original values while expanding retrieval keys; the brief confines that evidence to QA. [Mem0 repository](https://github.com/mem0ai/mem0), [release account](https://mem0.ai/blog/mem0-the-token-efficient-memory-algorithm), [LongMemEval paper](https://arxiv.org/html/2410.10813v2).

## Acceptance boundary

No claim of model incapacity, correct serving implementation, improved maintenance, reliable cancellation, useful coding performance or required versioned register follows. Current documentation is not an exact installed-version audit, and vendor multi-change comparisons are not causal ablations. The report acknowledges both limits and stops research at an appropriately small experimental question. Automatically maintained prose remains eligible under Brian's corrected goal.

`research-brief.md` and `report-source.md` are byte-identical; reviewed SHA256: `8285253ed36de6bc5644f5111a968c1a9880e9d1005d983cb4792953e7702305`. Audit SHA256: `88fff3dbcbdab9817dd182eeb9836e2bd8bf9f03c36e3619aea6aba32b8ea08d`. Rendered-prompt SHA256: `8ed0e234e7e4eb76524c8935c0dc4b39c4927129c4c9249ff60d1659427256b6`. Later evidence-note/status documents were outside this closing brief review.
