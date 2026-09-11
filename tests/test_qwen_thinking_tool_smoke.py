import json
import subprocess
import sys
from http.client import IncompleteRead
from pathlib import Path

import pytest

from scripts import qwen_thinking_tool_smoke as smoke


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


class NativeFixture:
    def __init__(self, sources, *, mutate_render=None, mutate_completion=None):
        self.sources = list(sources)
        self.mutate_render = mutate_render
        self.mutate_completion = mutate_completion
        self.requests = []
        self.completions = 0

    def __call__(self, request, timeout):
        body = bytes(request.data)
        payload = json.loads(body)
        self.requests.append((request.full_url, body, payload, timeout))
        if request.full_url.endswith("/render"):
            call_index = self.completions
            value = {
                "token_ids": [1000 + call_index, 1100 + call_index],
                "sampling_params": {
                    "max_tokens": smoke.MAX_OUTPUT_TOKENS,
                    "temperature": smoke.TEMPERATURE,
                    "top_p": smoke.TOP_P,
                    "top_k": smoke.TOP_K,
                    "seed": smoke.SEED,
                    "thinking_token_budget": smoke.THINKING_TOKEN_BUDGET,
                    "structured_outputs": {"json": smoke.ARGUMENT_SCHEMA},
                },
            }
            if self.mutate_render is not None:
                self.mutate_render(value, call_index)
            return Response(json.dumps(value).encode())

        call_index = self.completions
        self.completions += 1
        source = self.sources[call_index]
        reasoning = f"private-reasoning-{call_index}"
        raw_arguments = "\n\n" + json.dumps(
            {"source": source}, ensure_ascii=True, separators=(",", ":")
        )
        tokenizer = smoke.slab.qwen_tokenizer()
        output_ids = tokenizer.encode(
            f"<think>{reasoning}</think>{raw_arguments}",
            add_special_tokens=False,
        ).ids
        prompt_ids = [1000 + call_index, 1100 + call_index]
        value = {
            "prompt_token_ids": prompt_ids,
            "usage": {
                "prompt_tokens": len(prompt_ids),
                "completion_tokens": len(output_ids),
                "total_tokens": len(prompt_ids) + len(output_ids),
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
                                "id": f"call-{call_index}",
                                "type": "function",
                                "function": {
                                    "name": "replace_function",
                                    "arguments": raw_arguments,
                                },
                            }
                        ],
                    },
                }
            ],
        }
        if self.mutate_completion is not None:
            self.mutate_completion(value, call_index)
        return Response(json.dumps(value).encode())


VALID_SOURCES = [
    "def transform(value):\n    return {'value': value}\n",
    "def transform(value):\n    return {'value': value, 'revised': True}\n",
]


def run_fixture(tmp_path, opener):
    client = smoke.ThinkingToolClient("http://unit.test", "/model", opener=opener)
    return smoke.run(
        smoke.FIXTURE_ID,
        tmp_path / "out",
        client,
        deadline_seconds=30,
        runtime_args=["synthetic"],
    )


def test_two_actual_nonstreaming_calls_preserve_state_and_hide_reasoning(tmp_path):
    opener = NativeFixture(VALID_SOURCES)
    manifest = run_fixture(tmp_path, opener)

    assert manifest["status"] == "COMPLETE"
    assert manifest["technical_compatibility"] == "PASS"
    assert manifest["semantic_competence"] is None
    assert len(opener.requests) == 4
    assert opener.requests[0][1] == opener.requests[1][1]
    assert opener.requests[2][1] == opener.requests[3][1]
    second_messages = opener.requests[2][2]["messages"]
    assistant = next(
        message for message in second_messages if message["role"] == "assistant"
    )
    assert set(assistant) == {"role", "content", "tool_calls"}
    assert "private-reasoning-0" not in json.dumps(second_messages)
    tool_result = json.loads(
        next(message for message in second_messages if message["role"] == "tool")[
            "content"
        ]
    )
    assert tool_result["compiled"] is True
    assert tool_result["executed"] is False
    assert VALID_SOURCES[0] in tool_result["current_module"]
    assert VALID_SOURCES[0] in second_messages[-1]["content"]

    first_record = json.loads((tmp_path / "out/calls/call-00.json").read_text())
    reasoning = first_record["native_exchange"]["reasoning"]
    assert reasoning["observed_reasoning_tokens"] > 0
    assert reasoning["boundary_status"] == "under_allowance"
    assert reasoning["termination_cause_proven"] is False
    raw = first_record["native_exchange"]["completion"]["response"]
    assert raw["body_base64"] and raw["body_sha256"]


def test_exact_whitespace_after_reasoning_boundary_is_valid():
    tokenizer = smoke.slab.qwen_tokenizer()
    reasoning = "inspect"
    raw_arguments = "\n\n" + json.dumps(
        {"source": VALID_SOURCES[0]}, separators=(",", ":")
    )
    ids = tokenizer.encode(
        f"<think>{reasoning}</think>{raw_arguments}", add_special_tokens=False
    ).ids + [smoke._eos_ids()[0]]

    receipt = smoke._reasoning_receipt(ids, reasoning, raw_arguments)

    assert receipt["observed_reasoning_tokens"] > 0
    assert receipt["terminal_eos_token_id"] == smoke._eos_ids()[0]
    with pytest.raises(smoke.native.TechnicalError, match="tool arguments"):
        smoke._reasoning_receipt(ids, reasoning, raw_arguments.strip())


@pytest.mark.parametrize(
    "mutation,kind",
    [
        (
            lambda value, _index: value["sampling_params"].pop("top_k"),
            "render_settings",
        ),
        (
            lambda value, _index: value.update(
                token_ids=[0] * (smoke.CONTEXT_TOKENS - smoke.MAX_OUTPUT_TOKENS + 1)
            ),
            "capacity",
        ),
        (
            lambda value, _index: value["sampling_params"]["structured_outputs"].update(
                json={"type": "array"}
            ),
            "render_schema",
        ),
    ],
)
def test_render_gate_prevents_decode_and_preserves_failure(tmp_path, mutation, kind):
    opener = NativeFixture(VALID_SOURCES, mutate_render=mutation)
    manifest = run_fixture(tmp_path, opener)

    assert manifest["status"] == "INCOMPLETE"
    assert manifest["technical_failure"]["kind"] == kind
    assert len(opener.requests) == 1
    record = json.loads((tmp_path / "out/calls/call-00.json").read_text())
    assert record["native_exchange"]["completion"]["status"] == "NOT_STARTED"
    assert (
        json.loads(record["native_exchange"]["render"]["request"]["body"])["max_tokens"]
        == smoke.MAX_OUTPUT_TOKENS
    )


@pytest.mark.parametrize("defect", ["missing_end", "usage", "prompt_ids"])
def test_completion_accounting_and_boundaries_end_schedule(tmp_path, defect):
    def mutate(value, _index):
        if defect == "missing_end":
            end = smoke._boundary_ids()[1]
            value["choices"][0]["token_ids"].remove(end)
            value["usage"]["completion_tokens"] -= 1
            value["usage"]["total_tokens"] -= 1
        elif defect == "usage":
            value["usage"]["completion_tokens"] += 1
            value["usage"]["total_tokens"] += 1
        else:
            value["prompt_token_ids"] = [999]
            value["usage"]["prompt_tokens"] = 1
            value["usage"]["total_tokens"] -= 1

    opener = NativeFixture(VALID_SOURCES, mutate_completion=mutate)
    manifest = run_fixture(tmp_path, opener)

    assert manifest["status"] == "INCOMPLETE"
    assert len(opener.requests) == 2
    assert manifest["attempted_calls"] == 1
    assert manifest["completed_calls"] == 0


@pytest.mark.parametrize("defect", ["duplicate_start", "over_budget", "prefix"])
def test_ambiguous_over_budget_or_misplaced_reasoning_is_incomplete(tmp_path, defect):
    def mutate(value, _index):
        choice = value["choices"][0]
        start, end = smoke._boundary_ids()
        output = choice["token_ids"]
        end_index = output.index(end)
        suffix = output[end_index:]
        if defect == "duplicate_start":
            output.insert(1, start)
        elif defect == "prefix":
            output.insert(0, 42)
        else:
            interior = [42] * (smoke.THINKING_TOKEN_BUDGET + 1)
            choice["token_ids"] = [start, *interior, *suffix]
            choice["message"]["reasoning"] = smoke.slab.qwen_tokenizer().decode(
                interior, skip_special_tokens=False
            )
        completion = len(choice["token_ids"])
        value["usage"]["completion_tokens"] = completion
        value["usage"]["total_tokens"] = value["usage"]["prompt_tokens"] + completion

    opener = NativeFixture(VALID_SOURCES, mutate_completion=mutate)
    manifest = run_fixture(tmp_path, opener)

    assert manifest["status"] == "INCOMPLETE"
    assert manifest["attempted_calls"] == 1
    assert len(opener.requests) == 2


def test_compile_rejection_is_complete_no_go_without_second_call(tmp_path):
    opener = NativeFixture(["def transform(value):\n    break\n", VALID_SOURCES[1]])
    manifest = run_fixture(tmp_path, opener)

    assert manifest["status"] == "COMPLETE"
    assert manifest["technical_compatibility"] == "NO_GO"
    assert len(opener.requests) == 2
    assert manifest["attempted_calls"] == 1
    assert manifest["technical_failure"] is None


def test_partial_http_bytes_remain_in_pending_call_receipt(tmp_path):
    class BrokenResponse(Response):
        def read(self):
            raise IncompleteRead(b'{"token_ids":', 20)

    def opener(_request, timeout):
        assert timeout > 0
        return BrokenResponse(b"")

    manifest = run_fixture(tmp_path, opener)

    assert manifest["status"] == "INCOMPLETE"
    record = json.loads((tmp_path / "out/calls/call-00.json").read_text())
    response = record["native_exchange"]["render"]["response"]
    assert response["body"] == '{"token_ids":'
    assert response["incomplete_read_expected_bytes"] == 20
    assert record["native_exchange"]["completion"]["status"] == "NOT_STARTED"


def test_preview_cli_is_directly_runnable_from_tmp(tmp_path):
    script = Path(smoke.__file__).resolve()
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--input",
            smoke.FIXTURE_ID,
            "--preview",
        ],
        cwd=tmp_path,
        env={"PATH": "/usr/bin:/bin"},
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    preview = json.loads(result.stdout)
    assert preview["model_calls"] == 0
    assert preview["reasoning_boundaries"]["start_token_id"] == 151667
    assert preview["reasoning_boundaries"]["end_token_id"] == 151668
