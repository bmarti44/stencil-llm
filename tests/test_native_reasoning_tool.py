import json
from http.client import IncompleteRead

import pytest

from stencil.focus import native_reasoning_tool as client_module

REPLACE_SCHEMA = {
    "type": "object",
    "properties": {"source": {"type": "string"}},
    "required": ["source"],
    "additionalProperties": False,
}


class Response:
    status = 200
    headers = {"content-type": "application/json"}

    def __init__(self, body):
        self.body = body

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class NativeExchange:
    def __init__(
        self,
        spec,
        arguments,
        *,
        reasoning_ids=None,
        raw_prefix="\n\n",
        terminal_eos=True,
        mutate_render=None,
        mutate_completion=None,
    ):
        self.spec = spec
        self.arguments = arguments
        self.reasoning_ids = reasoning_ids
        self.raw_prefix = raw_prefix
        self.terminal_eos = terminal_eos
        self.mutate_render = mutate_render
        self.mutate_completion = mutate_completion
        self.requests = []

    def __call__(self, request, timeout):
        body = bytes(request.data)
        self.requests.append((request.full_url, body, timeout))
        if request.full_url.endswith("/render"):
            value = {
                "token_ids": [700, 701],
                "sampling_params": {
                    "max_tokens": self.spec.max_output_tokens,
                    "temperature": self.spec.temperature,
                    "top_p": self.spec.top_p,
                    "top_k": self.spec.top_k,
                    "seed": self.spec.seed,
                    "thinking_token_budget": self.spec.reasoning_token_budget,
                    "structured_outputs": {"json": self.spec.argument_schema},
                },
            }
            if self.mutate_render:
                self.mutate_render(value)
            return Response(json.dumps(value).encode())

        tokenizer = client_module.local_tokenizer()
        raw_arguments = self.raw_prefix + json.dumps(
            self.arguments, ensure_ascii=True, separators=(",", ":")
        )
        reasoning_ids = self.reasoning_ids
        if reasoning_ids is None:
            reasoning_ids = tokenizer.encode(
                "inspect-current-source", add_special_tokens=False
            ).ids
        reasoning = tokenizer.decode(reasoning_ids, skip_special_tokens=False)
        start, end = client_module.reasoning_boundary_ids()
        output_ids = [
            start,
            *reasoning_ids,
            end,
            *tokenizer.encode(raw_arguments, add_special_tokens=False).ids,
        ]
        if self.terminal_eos:
            output_ids.append(client_module.local_eos_ids()[0])
        value = {
            "prompt_token_ids": [700, 701],
            "usage": {
                "prompt_tokens": 2,
                "completion_tokens": len(output_ids),
                "total_tokens": 2 + len(output_ids),
            },
            "choices": [
                {
                    "finish_reason": "stop",
                    "token_ids": output_ids,
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "reasoning": reasoning,
                        "tool_calls": [
                            {
                                "id": "native-call-1",
                                "type": "function",
                                "function": {
                                    "name": self.spec.tool_name,
                                    "arguments": raw_arguments,
                                },
                            }
                        ],
                    },
                }
            ],
        }
        if self.mutate_completion:
            self.mutate_completion(value)
        return Response(json.dumps(value).encode())


def make_spec(tool="replace_function", *, allowance=1024, cap=2048):
    settings = {
        "max_output_tokens": cap,
        "reasoning_token_budget": allowance,
        "context_tokens": 32768,
        "temperature": 0.6,
        "top_p": 0.95,
        "top_k": 20,
        "min_p": 0.0,
        "seed": 20260908,
    }
    if tool == "replace_function":
        return client_module.NativeRequestSpec.create(
            tool_name=tool,
            tool_description="Replace the authenticated function.",
            argument_schema=REPLACE_SCHEMA,
            **settings,
        )
    return client_module.record_focus_spec(["m-user", "m-request"], **settings)


def perform(spec, opener, messages=None):
    client = client_module.NativeReasoningToolClient(
        "http://unit.test", "/model", spec, opener=opener
    )
    payload = client.payload(
        messages
        or [
            {"role": "system", "content": "Use the named tool."},
            {"role": "user", "content": "Handle the current request."},
        ]
    )
    body = client_module.json_bytes(payload)
    receipts = []
    result = client.perform(body, lambda exchange: receipts.append(exchange.copy()))
    return result, opener, receipts


@pytest.mark.parametrize(
    "tool,arguments",
    [
        (
            "replace_function",
            {"source": "def transform(value):\n    return value\n"},
        ),
        (
            "record_focus",
            {
                "obligations": [
                    {"text": "Preserve the current key.", "source_ids": ["m-user"]}
                ]
            },
        ),
    ],
)
def test_both_named_schemas_use_same_bytes_and_return_final_only(tool, arguments):
    spec = make_spec(tool)
    opener = NativeExchange(spec, arguments)

    result, opener, receipts = perform(spec, opener)

    assert len(opener.requests) == 2
    assert opener.requests[0][1] == opener.requests[1][1]
    assert json.loads(opener.requests[0][1])["tool_choice"]["function"]["name"] == tool
    assert result["arguments"] == arguments
    assert set(result["assistant_message"]) == {"role", "content", "tool_calls"}
    assert "reasoning" not in result["assistant_message"]
    assert result["reasoning"]["observed_reasoning_tokens"] > 0
    assert receipts[0]["status"] == "PENDING"
    assert receipts[-1]["status"] == "COMPLETE"


def test_record_focus_schema_pins_current_visible_source_enum():
    spec = make_spec("record_focus")
    schema = spec.argument_schema
    enum = schema["properties"]["obligations"]["items"]["properties"]["source_ids"][
        "items"
    ]["enum"]

    assert enum == ["m-user", "m-request"]
    with pytest.raises(ValueError, match="unique visible source"):
        client_module.record_focus_spec(
            ["m-user", "m-user"],
            max_output_tokens=2048,
            reasoning_token_budget=1024,
            context_tokens=32768,
            temperature=0.6,
            top_p=0.95,
            top_k=20,
            min_p=0.0,
            seed=20260908,
        )


@pytest.mark.parametrize(
    "spec,arguments",
    [
        (
            make_spec("replace_function"),
            {"source": 3},
        ),
        (
            make_spec("record_focus"),
            {
                "obligations": [
                    {"text": "Invented source.", "source_ids": ["not-visible"]}
                ]
            },
        ),
    ],
)
def test_returned_arguments_are_checked_against_the_named_schema(spec, arguments):
    opener = NativeExchange(spec, arguments)

    with pytest.raises(client_module.TechnicalError) as error:
        perform(spec, opener)

    assert error.value.kind == "malformed_response"
    assert len(opener.requests) == 2


def test_1024_reasoning_boundary_passes_and_1025_is_rejected():
    spec = make_spec()
    arguments = {"source": "def transform(value):\n    return value\n"}
    accepted = NativeExchange(spec, arguments, reasoning_ids=[42] * 1024)

    result, _, _ = perform(spec, accepted)

    assert result["reasoning"]["observed_reasoning_tokens"] == 1024
    assert result["reasoning"]["boundary_status"] == "budget_boundary_reached"
    rejected = NativeExchange(spec, arguments, reasoning_ids=[42] * 1025)
    with pytest.raises(client_module.TechnicalError) as error:
        perform(spec, rejected)
    assert error.value.kind == "capacity"


def test_exact_final_whitespace_and_terminal_eos_are_accounted():
    spec = make_spec()
    arguments = {"source": "def transform(value):\n    return value\n"}
    opener = NativeExchange(spec, arguments, raw_prefix="\n\n")

    result, _, _ = perform(spec, opener)

    assert result["raw_arguments"].startswith("\n\n")
    assert result["reasoning"]["terminal_eos_token_id"] in (
        client_module.local_eos_ids()
    )
    mismatch = NativeExchange(spec, arguments, raw_prefix="\n\n")

    def change_raw(value):
        value["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"] = (
            value["choices"][0]["message"]["tool_calls"][0]["function"][
                "arguments"
            ].strip()
        )

    mismatch.mutate_completion = change_raw
    with pytest.raises(client_module.TechnicalError, match="tool arguments"):
        perform(spec, mismatch)


@pytest.mark.parametrize(
    "defect,expected_kind,expected_requests",
    [
        ("schema", "render_schema", 1),
        ("name", "malformed_response", 2),
        ("prompt", "token_accounting", 2),
        ("usage", "token_accounting", 2),
        ("cap", "capacity", 2),
    ],
)
def test_schema_name_id_usage_and_cap_fail_through_native_consumer(
    defect, expected_kind, expected_requests
):
    spec = make_spec(allowance=10, cap=40)
    arguments = {"source": "def transform(value):\n    return value\n"}

    def mutate_render(value):
        if defect == "schema":
            value["sampling_params"]["structured_outputs"]["json"] = {"type": "array"}

    def mutate_completion(value):
        choice = value["choices"][0]
        if defect == "name":
            choice["message"]["tool_calls"][0]["function"]["name"] = "wrong"
        elif defect == "prompt":
            value["prompt_token_ids"] = [999]
        elif defect == "usage":
            value["usage"]["completion_tokens"] += 1
            value["usage"]["total_tokens"] += 1
        elif defect == "cap":
            overflow = spec.max_output_tokens + 1 - len(choice["token_ids"])
            choice["token_ids"].extend([42] * max(1, overflow))
            value["usage"]["completion_tokens"] = len(choice["token_ids"])
            value["usage"]["total_tokens"] = value["usage"]["prompt_tokens"] + len(
                choice["token_ids"]
            )

    opener = NativeExchange(
        spec,
        arguments,
        mutate_render=mutate_render,
        mutate_completion=mutate_completion,
    )
    with pytest.raises(client_module.TechnicalError) as error:
        perform(spec, opener)

    assert error.value.kind == expected_kind
    assert len(opener.requests) == expected_requests


def test_native_default_omission_only_accepts_registered_default():
    spec = make_spec()
    arguments = {"source": "def transform(value):\n    return value\n"}
    perform(spec, NativeExchange(spec, arguments))

    def wrong_default(value):
        value["sampling_params"]["min_p"] = 0.1

    opener = NativeExchange(spec, arguments, mutate_render=wrong_default)
    with pytest.raises(client_module.TechnicalError) as error:
        perform(spec, opener)
    assert error.value.kind == "render_settings"


def test_generic_history_validates_matching_final_tool_without_reasoning():
    spec = make_spec("record_focus")
    arguments = {"obligations": []}
    prior_arguments = json.dumps(
        {"obligations": [{"text": "Keep the key.", "source_ids": ["m-user"]}]}
    )
    messages = [
        {"role": "user", "content": "First request"},
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "prior-id",
                    "type": "function",
                    "function": {
                        "name": "record_focus",
                        "arguments": prior_arguments,
                    },
                }
            ],
        },
        {
            "role": "tool",
            "tool_call_id": "prior-id",
            "name": "record_focus",
            "content": "recorded",
        },
        {"role": "user", "content": "Second request"},
    ]

    result, opener, _ = perform(
        spec, NativeExchange(spec, arguments), messages=messages
    )

    assert result["arguments"] == arguments
    outgoing = json.loads(opener.requests[0][1])["messages"]
    assert outgoing == messages
    assert all("reasoning" not in message for message in outgoing)


def test_payload_rejects_orphan_tool_result_with_null_call_id():
    spec = make_spec("record_focus")
    opener = NativeExchange(spec, {"obligations": []})
    client = client_module.NativeReasoningToolClient(
        "http://unit.test", "/model", spec, opener=opener
    )
    messages = [
        {"role": "user", "content": "request"},
        {
            "role": "tool",
            "tool_call_id": None,
            "name": "record_focus",
            "content": "orphan",
        },
    ]

    with pytest.raises(ValueError, match="invalid tool-result"):
        client.payload(messages)
    assert opener.requests == []


def test_partial_transport_retains_pending_and_raw_bytes():
    spec = make_spec()
    receipts = []

    class Broken(Response):
        def read(self):
            raise IncompleteRead(b'{"token_ids":', 12)

    client = client_module.NativeReasoningToolClient(
        "http://unit.test", "/model", spec, opener=lambda *_args, **_kwargs: Broken(b"")
    )
    body = client_module.json_bytes(
        client.payload([{"role": "user", "content": "request"}])
    )
    with pytest.raises(client_module.TechnicalError):
        client.perform(body, lambda exchange: receipts.append(exchange.copy()))

    assert receipts[0]["status"] == "PENDING"
    response = client.last_exchange["render"]["response"]
    assert response["body"] == '{"token_ids":'
    assert response["incomplete_read_expected_bytes"] == 12
    assert client.last_exchange["completion"]["status"] == "NOT_STARTED"
