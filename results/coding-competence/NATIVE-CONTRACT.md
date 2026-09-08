# Pinned native edit transport and accounting

2026-09-08. Supplements the accepted [prospective protocol](PROTOCOL.md);
this is preparation, not an inference launch. Astra xhigh inspected the pinned
vLLM `fe9c3d6c5` source corresponding to the recorded local image version
`0.19.2rc1.dev134+gfe9c3d6c5`. No new server or model was started for that check.
Runtime compatibility still requires the exact frozen request/response checks.

Use the existing model/image/resource settings, adding BOTH
`--enable-auto-tool-choice --tool-call-parser hermes`. Despite the flag name,
every request forces exactly the named `replace_function` tool. The pinned
parser manager supplies no tool parser without the enable flag, and the render
path rejects named tool choice without a parser. See [parser gating](https://github.com/vllm-project/vllm/blob/fe9c3d6c5/vllm/parser/parser_manager.py)
and [render validation](https://github.com/vllm-project/vllm/blob/fe9c3d6c5/vllm/entrypoints/serve/render/serving.py).

Every request uses `stream:false`, `parallel_tool_calls:false`,
`tool_choice:{"type":"function","function":{"name":"replace_function"}}`,
`return_token_ids:true`, and `chat_template_kwargs:{"enable_thinking":false}`.
The sole tool has a fixed description and parameters exactly:
`{"type":"object","properties":{"source":{"type":"string"}},"required":["source"],"additionalProperties":false}`.
The description, message-building code and numeric settings are frozen with
the runner. No optional free-form second action or implicit completion output.

Before EVERY prospective model call, post the EXACT same request JSON bytes to
`/v1/chat/completions/render`. This non-generation auxiliary request uses the
same `render_chat` path, including tools, native history and current manual
reminder. Record its exact request/response bytes, hashes, status and timing
separately from model actions. Require integer `token_ids`, context eligibility
including the output allowance, and `sampling_params.structured_outputs.json`
structurally equal to the fixed argument schema. This checks configuration,
not whether the generation backend can successfully compile the grammar.
See [endpoint](https://github.com/vllm-project/vllm/blob/fe9c3d6c5/vllm/entrypoints/serve/render/api_router.py),
[response fields](https://github.com/vllm-project/vllm/blob/fe9c3d6c5/vllm/entrypoints/serve/disagg/protocol.py),
and [grammar installation](https://github.com/vllm-project/vllm/blob/fe9c3d6c5/vllm/tool_parsers/abstract_tool_parser.py).

Then send those identical bytes to `/v1/chat/completions`. Require one choice,
one assistant tool call, the exact function name, and arguments decoding to
exactly the specified source object. Do not require `finish_reason:tool_calls`:
pinned successful named calls ordinarily finish with `stop`; an output cap
remains `length`. Accept only the registered named-mode successful finish.
Require response `prompt_token_ids` to equal render `token_ids` exactly, with
length equal to `usage.prompt_tokens`. Request generated IDs and validate
`choices[0].token_ids` against `usage.completion_tokens`; reject missing or
malformed accounting under the pinned return-token-IDs contract. Usage values
are nonnegative integers (not booleans), completion is within cap, and total
is the exact sum. Preserve raw capped/invalid output even when it earns no
submission credit. See [completion fields](https://github.com/vllm-project/vllm/blob/fe9c3d6c5/vllm/entrypoints/openai/chat_completion/serving.py).

The server expands tool model defaults and parses historical argument JSON
before applying the HF template. Consequently local rendering of arbitrary raw
HTTP dictionaries is only provisional sizing evidence. Authoritative render
receipts avoid recreating this normalization by hand. Preserve local CPU
reference/action sizes, but do not claim bit-identical native previews without
the authoritative IDs. Named choice installs argument grammar after rendering;
it does not justify deleting tools or adding a fabricated named-choice suffix.

Technical failure ends the entire run: transport, cap, render/schema/context
failure, malformed usage/IDs or unreplayable native exchange. Save partial
records and mark remaining requests unattempted/incomplete. Do not issue another
model request after such a failure or retry the run. This explicitly closes the
protocol's technical request termination: malformed historical tool arguments
would fail the server's JSON preprocessing on later requests. Raw output cannot
be repaired, dropped or recast to resume. See [history processing](https://github.com/vllm-project/vllm/blob/fe9c3d6c5/vllm/entrypoints/chat_utils.py).

A well-formed native invocation whose exact Python source fails the registered
function/compile consumer is different: it can be retained authentically and
receive a matching tool error within the three-attempt limit. Valid-but-wrong
code likewise remains in state and can get public execution feedback. Private
scoring still never influences stopping, feedback or retries. All auxiliary
requests and execution time count toward the same owned reservation; at most
36 worker generations remain possible. Record the full planned 12-request
schedule, attempted slots, terminal endpoints and incomplete/unattempted work
without fabricating outcomes. Cleanup remains inside the frozen time ceiling.
