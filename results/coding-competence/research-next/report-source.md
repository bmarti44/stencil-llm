# Next step after the coding competence failure

2026-09-08. Decision draft for independent Astra xhigh review. Research lane:
Astra xhigh; methodological retrieval, source spot-checks and synthesis: root.
This is preparation, not a new experiment registration or launch authorization.

Prepare one bounded compatibility check of the existing Qwen3-30B-A3B with
thinking enabled and the model author's recommended sampling. If that works
within a reviewed resource plan, prepare a fresh small worker qualification.
Keep the failed run parked. Do not train the focus interpreter yet.

The intended benefit remains automatic production of useful current instructions.
Matching competent manual prose can meet that objective; superiority over ideal
manual prose is not required. A perfect manual worker is not a universal
prerequisite for a paired comparison, either. Nevertheless, the completed run's
registered gate remains failed, and its source defects cannot be erased by
changing the threshold after observing the results.

## What the completed run establishes

[Run 01](../run-01/RESULTS.md) completed technically: 9/12 request endpoints and
2/4 projects passed finite checks, but independent source inspection found
contract violations in all four projects. Three failed requests repeated
identical code despite actual public error feedback. The initial tool interface
did not disclose the nested-helper ban; later feedback did. Wrong numbering
and other output/validation defects exist independently of that ambiguity.
These observations do not identify a sole cause or measure automatic focus.
All current cases and responses remain spent DEV, excluded from fitting and
future fresh qualification. Neither sealed larger-test directory is reopened.

## Evidence and remaining gaps

| Decision claim | Primary evidence and confidence | Limit or next action |
|---|---|---|
| Thinking is a materially supported candidate on the existing checkpoint | Qwen's original technical report, Tables 15/16, reports thinking/nonthinking LiveCodeBench v5 scores 62.6/29.8 and BFCL v3 69.1/58.6. High confidence in reported values. | Both coding modes allow 32,768 output tokens; sampling and the thinking coding prompt differ. This is not an isolated mode effect or a prediction under our short cap. |
| Use the author's thinking configuration | Original model card specifies thinking temperature 0.6, top_p 0.95, top_k 20, min_p 0, and final-output-only history. High confidence in documented usage. | Its warning about greedy decoding does not prove the cause of our nonthinking repair failures. |
| Existing server can expose reasoning and tools | Pinned vLLM documentation lists qwen3 support for reasoning, structured output and tools, plus native thinking_token_budget. High confidence in documented mechanisms; runtime combination unverified. | Check cold and post-tool calls, reasoning boundaries, final named action, prompt IDs and actual token accounting before fresh cases. |
| Finite success can miss specification violations | Original tau-bench explicitly recognizes that a successful final-state reward can coexist with a policy violation. High confidence in that methodological limitation. | Retain source/dependency review alongside executable outcomes. |
| Useful parity need not require a perfect comparator | Paired binary noninferiority methods compare correlated proportions; no perfect-control assumption is required. High confidence in the general comparison; exact method not selected here. | Prespecify an absolute utility requirement, margin, independent project unit and adequate fresh sample size before the larger comparison. |
| More reasoning fits the existing budget | Not established. Current local accounting is slower than the earlier estimate used by the research lane. | Size the technical check and fresh qualification prospectively; no inference launch from this report. |

The Qwen findings above are author-reported benchmarks from May 2025, not current
leaderboard claims. The paper's thinking-budget curve concerns the much larger
235B-A22B model and cannot choose our 30B-A3B reasoning cap.
[Qwen3 technical report](https://arxiv.org/html/2505.09388v1).
The original checkpoint supports explicit thinking activation; disabling it in
the template cannot be overridden by a textual /think request.
[Original model card](https://huggingface.co/Qwen/Qwen3-30B-A3B).

At the exact serving pin, native reasoning budgets force the configured ending
tokens when the allowance is exhausted; without that setting the overall output
limit is the bound. The compatibility check must exercise this mechanism rather
than infer it from accepted request fields.
[Pinned reasoning documentation](https://github.com/vllm-project/vllm/blob/fe9c3d6c5/docs/features/reasoning_outputs.md).
The reasoning-state detector scans backward through the prompt for the latest
start/end boundary. This creates a conditional hazard if historical closed
reasoning is replayed without a fresh start marker. It is a source-based concern,
not a measured local failure. Preserve raw reasoning receipts separately and
verify actual cold/post-tool rendering with final outputs retained in history.
[Pinned parser](https://github.com/vllm-project/vllm/blob/fe9c3d6c5/vllm/reasoning/basic_parsers.py).

The worker lane also checked named-tool grammar installation, response parsing,
grammar gating and native budget integration at the same pin. Its inspected
budget endpoint tests use Qwen3-0.6B and do not establish our named-tool/30B
combination. CPU inspection and the actual bounded check must resolve that gap.
[Named-tool handling](https://github.com/vllm-project/vllm/blob/fe9c3d6c5/vllm/entrypoints/openai/chat_completion/serving.py),
[budget endpoint tests](https://github.com/vllm-project/vllm/blob/fe9c3d6c5/tests/entrypoints/openai/chat_completion/test_thinking_token_budget.py).

## Utility and comparison

For paired project success indicators A (automatic) and M (manual),
E[A-M] = P(A=1,M=0) - P(A=0,M=1). This identity does not require M always to
succeed. A future noninferiority claim needs a prespecified lower confidence
bound exceeding a justified negative margin, together with an absolute utility
requirement: two systems that always fail are equal but useless. Requests and
check rows within the same project are not independent projects. These are
design requirements, not new numerical gates selected from 9/12.

Hsueh, Liu and Chen (2001) study exact noninferiority/equivalence for paired
binary endpoints and limitations of small-sample asymptotics. Only the primary
abstract was accessible here; it supports the comparison family, not a chosen
formula or sample-size calculation.
[Primary abstract](https://pubmed.ncbi.nlm.nih.gov/11414572/).
Tau-bench compares imperfect agents, distinguishes repeated reliability from
at-least-one-success metrics, and explicitly warns that finite reward may miss
policy violations. This supports keeping outcome definitions honest, not
borrowing a usefulness threshold from that benchmark.
[Original tau-bench paper](https://arxiv.org/html/2406.12045v1).

Self-repair results also caution that additional attempts can yield poor returns
once cost is counted. Those experiments use different models and test access;
they do not justify an extra critic, private feedback, or retries of our spent
cases. Keep a strict prospective attempt budget.
[Olausson et al., revised February 2024](https://arxiv.org/html/2306.09896v5).

## Resource correction and concrete preparation

The completed summary records 5,777 completion tokens over 307.08357315306785
seconds of completion HTTP time: **18.81246835 tokens/second**. This includes
request/prefill overhead and is an observed effective rate, not a guaranteed
thinking decode rate. Using the prior illustrative 780-second fixed allowance:

| Hypothetical maximum schedule | Linear estimate |
|---|---:|
| 36 calls x 2,048 output tokens | 4,699.10 seconds |
| 36 calls x 1,536 output tokens | 3,719.33 seconds |

Both exceed 3,600 seconds even before additional technical smoke work. The
earlier research estimate of 22.83897 tokens/second would misleadingly leave
room at 1,536; it is superseded for this illustration. Neither estimate selects
an adequate reasoning allowance. The 780-second term is an illustrative prior
allowance, not a verified worst-case bound. Real scheduling must include startup,
rendering, growing prompts, execution, receipts and cleanup, with a hard stop.

Next work is CPU preparation: a Sol xhigh brief for an isolated technical check,
using fresh trivial fixtures unrelated to semantic task banks; exact reasoning,
schema and history assertions; complete receipts; measured resource plan; Astra
xhigh review before launch. Do not modify frozen run-01 code or cases to rescue
them. A later fresh semantic qualification uses Kimi K3 through Ollama, with
disjoint lineage and the actual tool restrictions disclosed in advance. A small
compatibility or competence check cannot satisfy the larger automatic-focus goal.

## Research trail and stop

Accessed 2026-09-08. Discovery and targeted follow-up are complete; synthesis
review is pending. The worker lane followed original Qwen report/card into exact
vLLM documentation, grammar/parser/budget source and tests. Searches targeted
Qwen3 reasoning-state history, forced tool choice and thinking-token budgets.
It checked and rejected an apparent later vLLM issue as an established blocker
at this pin. The parent retrieved original tau-bench, paired-binary methods,
Agentless and matched-pair confidence-interval work; the last two are omitted
from the decision because they add no needed action. A second research agent
was unavailable under the thread limit, so root completed that lane.

Root spot-checked Qwen tables/settings, pinned reasoning docs and backward
boundary detection, tau-bench's finite-reward limitation, and recomputed local
resource arithmetic. General web research stops here: remaining uncertainty is
the local compatibility and useful reasoning budget, which papers cannot settle.
No new model call, training, benchmark execution or old-case replay was performed
for this synthesis. The complete automatic-focus objective remains active.
