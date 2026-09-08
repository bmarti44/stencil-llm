# Research decision review — Astra

2026-09-08. Independent, author-disjoint Astra xhigh review, as explicitly
selected by the user. Native review; no wrapper or reviewer substitution.
Writable scope: this file only. The reviewed author synthesized the report;
this reviewer independently checked its consequential primary sources and
reconciled its local evidence. No model calls, generated-code execution,
benchmark replay, training, or additional agents were used.

## Round 1

**Score: 96/100. Disposition: ACCEPTED as a research decision report.**
Open findings: critical 0, high 0, medium 0, low 0. Acceptance threshold:
90/100 with zero open high/critical findings. Numbered findings: none in this
round; any later findings must retain their numbers across revisions.

This accepts preparation of the proposed bounded compatibility check. It does
not establish compatibility, select an adequate reasoning allowance, register
a new experiment, or approve a specific launch. The completed competence run
remains NO-GO. The distinction is explicit in the report and is material to
this acceptance.

### Reviewed snapshot

SHA-256 of the exact local inputs:

| Artifact | SHA-256 |
|---|---|
| `research-next/report-source.md` | `93bf15f547aabce8e065a7c5c10ba599af4a1ee0e515f200f26fe510a3e0fa5b` |
| `run-01/RESULTS.md` | `45c2b37c3c107e9d1e7a965cb6779d196200f5e689682eb847576e50ab3496c3` |
| `run-01/summary.json` | `f0c26e347ed468809c01831359de77a2007bcce6ddfb1c96db0731de8d4b285f` |
| `run-01/source-review-astra.md` | `f76e9c554ba73eff00afe63f529bfe1de6c85f9ffbc2880f7ea9faa6e896c315` |

The four receipt digests embedded in `summary.json` match the current bytes of
`freeze.json`, `lifecycle.json`, `calls/manifest.json`, and
`cleanup-receipts.json`; its source-review digest also matches. This review
preserves the earlier frozen readiness and source audits.

### Primary-source verification

1. Qwen3's original report confirms the cited 30B-A3B thinking/nonthinking
   LiveCodeBench values, 62.6/29.8, and BFCL values, 69.1/58.6, in Tables 15/16.
   Its evaluation setup permits 32,768 output tokens, changes sampling between
   modes, and changes the thinking coding prompt. Figure 2 concerns
   235B-A22B. The report correctly treats this as support for investigating a
   candidate configuration, without attributing the difference solely to mode
   or predicting short-budget local performance.
   [Qwen3 report, sections 4.6–4.7](https://arxiv.org/html/2505.09388v1).

2. The original checkpoint's model card confirms the stated thinking sampling
   values, final-output-only history guidance, and the inability of textual
   `/think` to override `enable_thinking=False`. The research report correctly
   avoids converting the thinking-mode greedy-decoding warning into a causal
   explanation of the completed nonthinking run.
   [Qwen3-30B-A3B model card](https://huggingface.co/Qwen/Qwen3-30B-A3B).

3. The pinned vLLM documentation lists qwen3 reasoning, structured output and
   tool support, and describes the native budget's forced ending-token
   mechanism. The backward boundary scan in `BaseThinkingReasoningParser`
   supports the stated conditional history concern. The serving code extracts
   reasoning before constructing named tool calls from final content. Endpoint
   budget tests use Qwen3-0.6B. None of these establishes the exact local
   30B/named-tool/budget combination; the report accurately leaves that to the
   prospective cold and post-tool check.
   [Pinned documentation](https://github.com/vllm-project/vllm/blob/fe9c3d6c5/docs/features/reasoning_outputs.md),
   [boundary parser](https://github.com/vllm-project/vllm/blob/fe9c3d6c5/vllm/reasoning/basic_parsers.py),
   [serving code](https://github.com/vllm-project/vllm/blob/fe9c3d6c5/vllm/entrypoints/openai/chat_completion/serving.py),
   [endpoint tests](https://github.com/vllm-project/vllm/blob/fe9c3d6c5/tests/entrypoints/openai/chat_completion/test_thinking_token_budget.py).

4. The original tau-bench paper explicitly permits a passing reward despite
   omitted policy-required confirmation, and distinguishes repeated success
   from at-least-one success. The report's finite-oracle qualification is
   supported. Olausson et al. v5, revised February 2, 2024, supports the limited
   cost-aware self-repair claim for its studied models and tasks. Neither
   source licenses extra attempts or private feedback on this spent run.
   [Tau-bench, reward and reliability definitions](https://arxiv.org/html/2406.12045v1),
   [self-repair study](https://arxiv.org/abs/2306.09896v5).

5. Hsueh, Liu and Chen's primary abstract confirms exact methods for paired
   binary noninferiority/equivalence and small-sample asymptotic limitations.
   The report honestly limits its access and does not claim to have selected
   a procedure or calculated power. Independently, its paired expectation
   identity follows by expanding the four joint binary outcomes; a perfect
   manual comparator is unnecessary. Absolute utility, a justified prospective
   margin, and project-level dependence remain distinct design requirements.
   [Primary abstract](https://pubmed.ncbi.nlm.nih.gov/11414572/).

### Local results and resource arithmetic

Reaggregation of the 18 saved call receipts confirms 95,528 prompt tokens,
5,777 completion tokens, 185 public check executions, 15 applied actions and
3 rejected actions. All saved finish reasons are `stop`. Completion HTTP time
sums to 307.08357315306785 seconds, matching the project totals. Request totals
reconcile to 209 terminal evaluation rows and 9/12 passing endpoints; project
totals reconcile to 2/4 finite passes. The earlier source audit explains that
the terminal phase includes inherited helper/cumulative checks; these counts
are executions, not independent observations.

The results prose and summary accurately retain the source defects in both
finite-passing projects, the repeated failed repairs, the initially undisclosed
nested-helper restriction, and independent algorithm/output defects. They do
not claim that finite success proves source correctness or that missing memory
is the sole cause. Lifecycle and frozen-input claims match the completed audit;
this review performed no new GPU/process probe.

Recomputed effective throughput is **18.812468347567442 tokens/second**. Using
the report's explicitly illustrative 780-second allowance:

| Schedule | Recomputed seconds | Report rounding |
|---|---:|---:|
| 36 × 1,536 output tokens | 3,719.327204616936 | 3,719.33 |
| 36 × 2,048 output tokens | 4,699.1029394892485 | 4,699.10 |

Both exceed 3,600 seconds. The report correctly supersedes the earlier
22.83897 estimate for this calculation and makes no guaranteed decode-rate or
worst-case allowance claim. No adequate future schedule has yet been shown.

### Decision alignment and remaining evidence

The decision preserves the user's objective: automatically produced useful
instructions can succeed by matching competent manual prose. It does not
impose universally perfect manual performance or require superiority over an
ideal comparator. It also preserves the particular failed prerequisite's
registered gate rather than redefining that result after inspection.

Investigating native compatibility before fresh semantic qualification is a
reasonable inference from the cited evidence. The explicit remaining work is
the exact interface/history/budget check, a feasible resource plan, and fresh
qualification with disclosed tool restrictions. A small passing check would
still provide neither useful-parity evidence nor general competence. The report
states these limits clearly enough to proceed with preparation.
