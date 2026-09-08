# Native contract source review — round 1

2026-09-08. Reviewer: Astra, xhigh, explicitly requested in place of the
repository's default Opus reviewer. Author-disjoint review of parent prose.
Scope: pinned-source transport and accounting expectations only; no runtime
code, endpoint invocation, model loading, or inference was reviewed or run.

Reviewed: [NATIVE-CONTRACT.md](NATIVE-CONTRACT.md), SHA-256
`d324c5fa599e56ddeaac69c3dd44e8f3e338805a2c37903362e456f75c472374`.
Source pin: vLLM `fe9c3d6c5`, corresponding to the previously recorded image
version `0.19.2rc1.dev134+gfe9c3d6c5`.

**Accuracy score: 96/100. Verdict: ACCEPT for this documentation unit.**
Threshold: 90; open critical/high/medium/low findings: 0/0/0/0.

The contract accurately requires both parser flags while forcing named
`replace_function` in each request. The authoritative render endpoint accepts
the same chat request and uses the completion preprocessing path. The stated
native-history normalization and named-call `stop` versus cap `length`
distinction agree with the pinned source.

Two decisive receipt requirements were rechecked directly:

- Named tool selection returns the tool's parameter dictionary as the JSON
  constraint. `SamplingParams` serialization retains the non-default
  `structured_outputs` field, so the stated response path
  `sampling_params.structured_outputs.json` is supported. This establishes
  configured schema evidence, as the contract says, without proving backend
  grammar compilation. Sources: [schema selection](https://github.com/vllm-project/vllm/blob/fe9c3d6c5/vllm/tool_parsers/utils.py),
  [constraint installation](https://github.com/vllm-project/vllm/blob/fe9c3d6c5/vllm/tool_parsers/abstract_tool_parser.py),
  [serialization](https://github.com/vllm-project/vllm/blob/fe9c3d6c5/vllm/v1/serial_utils.py).
- With `return_token_ids:true`, the nonstreaming response populates both
  `prompt_token_ids` and `choices[0].token_ids`. Usage is computed from those
  engine token arrays. Strict presence, identity and length checks therefore
  fit the registered text-only, single-choice path; missing IDs need not be
  silently treated as optional instrumentation. Source: [completion response
  construction](https://github.com/vllm-project/vllm/blob/fe9c3d6c5/vllm/entrypoints/openai/chat_completion/serving.py).

Entire-run termination on technical failure is an explicit prospective policy,
not a claim about vLLM's behavior. It closes the malformed-argument replay edge
without repairing or discarding history. JSON-valid Python consumer failures
remain eligible for authentic tool feedback within the three-attempt budget.
Auxiliary render receipts and their time are explicitly accounted for.

No findings were raised. Actual image compatibility, consumer enforcement,
generation headroom and reservation eligibility remain separate readiness
checks; this acceptance does not authorize inference.
