import json

import pytest

from scripts import coding_competence_run as native
from stencil.focus.native_source_selector import (
    MAX_OUTPUT_TOKENS,
    NativeSourceSelectorClient,
)


class FakeResponse:
    status = 200
    headers = {"Content-Type": "application/json"}

    def __init__(self, value):
        self.body = json.dumps(value).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.body


class FakeOpener:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def __call__(self, request, timeout):
        self.requests.append((request.full_url, request.data, timeout))
        return FakeResponse(self.responses.pop(0))


def _completion(
    source_ids=("m01",),
    *,
    prompt_ids=(10, 11),
    output_ids=(20,),
    tool_name="select_source_ids",
    arguments=None,
    finish_reason="stop",
    usage=None,
):
    if arguments is None:
        arguments = json.dumps({"source_ids": list(source_ids)})
    if usage is None:
        usage = {
            "prompt_tokens": len(prompt_ids),
            "completion_tokens": len(output_ids),
            "total_tokens": len(prompt_ids) + len(output_ids),
        }
    return {
        "prompt_token_ids": list(prompt_ids),
        "choices": [
            {
                "finish_reason": finish_reason,
                "token_ids": list(output_ids),
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "selection-1",
                            "type": "function",
                            "function": {"name": tool_name, "arguments": arguments},
                        }
                    ],
                },
            }
        ],
        "usage": usage,
    }


def _client(completion=None, render=None):
    client = NativeSourceSelectorClient("127.0.0.1:9", "/model", ["m01", "m02"])
    rendered = render or {
        "token_ids": [10, 11],
        "sampling_params": {"structured_outputs": {"json": client.argument_schema}},
    }
    opener = FakeOpener([rendered, completion or _completion()])
    client.opener = opener
    return client, opener


def test_payload_is_forced_ids_only_nonthinking_and_fixed_cap():
    client, _ = _client()
    messages = [{"role": "user", "content": "select"}]

    payload = client.payload(messages)

    assert payload["max_tokens"] == 128
    assert payload["temperature"] == 0
    assert payload["seed"] == 20260908
    assert payload["chat_template_kwargs"] == {"enable_thinking": False}
    assert payload["tool_choice"]["function"]["name"] == "select_source_ids"
    assert payload["tools"][0]["function"]["parameters"] == client.argument_schema
    assert client.argument_schema["properties"]["source_ids"] == {
        "type": "array",
        "items": {"type": "string", "enum": ["m01", "m02"]},
        "minItems": 0,
        "maxItems": 4,
    }


def test_perform_reuses_exact_request_bytes_and_accepts_stop_at_cap():
    completion = _completion(output_ids=tuple(range(MAX_OUTPUT_TOKENS)))
    client, opener = _client(completion=completion)
    body = native._json_bytes(client.payload([{"role": "user", "content": "select"}]))
    receipts = []

    result = client.perform(body, lambda exchange: receipts.append(exchange.copy()))

    assert result["arguments"] == {"source_ids": ["m01"]}
    assert [request[1] for request in opener.requests] == [body, body]
    assert receipts[-1]["status"] == "COMPLETE"
    assert receipts[-1]["usage"]["completion_tokens"] == 128


@pytest.mark.parametrize(
    "completion,render,kind",
    [
        (_completion(prompt_ids=(99,)), None, "token_accounting"),
        (
            None,
            {
                "token_ids": [10, 11],
                "sampling_params": {"structured_outputs": {"json": {}}},
            },
            "render_schema",
        ),
        (_completion(tool_name="replace_function"), None, "malformed_response"),
        (_completion(arguments="{"), None, "malformed_response"),
        (_completion(source_ids=("m01", "m01")), None, "malformed_response"),
        (_completion(source_ids=("missing",)), None, "malformed_response"),
        (_completion(finish_reason="length"), None, "capacity"),
        (
            _completion(
                output_ids=tuple(range(129)),
                usage={
                    "prompt_tokens": 2,
                    "completion_tokens": 129,
                    "total_tokens": 131,
                },
            ),
            None,
            "capacity",
        ),
    ],
)
def test_perform_rejects_invalid_native_exchange(completion, render, kind):
    client, _ = _client(completion=completion, render=render)
    body = native._json_bytes(client.payload([{"role": "user", "content": "select"}]))

    with pytest.raises(native.TechnicalError) as caught:
        client.perform(body, lambda _exchange: None)

    assert caught.value.kind == kind


def test_perform_rejects_authoritative_context_overflow():
    client, _ = _client(
        render={
            "token_ids": list(range(32768 - MAX_OUTPUT_TOKENS + 1)),
            "sampling_params": {
                "structured_outputs": {
                    "json": NativeSourceSelectorClient(
                        "127.0.0.1:9", "/model", ["m01", "m02"]
                    ).argument_schema
                }
            },
        }
    )
    body = native._json_bytes(client.payload([{"role": "user", "content": "select"}]))

    with pytest.raises(native.TechnicalError) as caught:
        client.perform(body, lambda _exchange: None)

    assert caught.value.kind == "capacity"
