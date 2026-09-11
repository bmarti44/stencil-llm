"""Consequential controls for the native coding-competence runtime."""

import copy
import importlib.util
import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import coding_competence_dev as cpu
from scripts import coding_competence_run as runner

ROOT = Path(__file__).resolve().parents[1]


def _fixture_document():
    path = ROOT / "tests/test_coding_competence_dev.py"
    spec = importlib.util.spec_from_file_location("_competence_cpu_fixture", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._document()


def _bank():
    base = _fixture_document()
    documents = []
    for episode_index in range(4):
        document = copy.deepcopy(base)
        document["public"]["episode_id"] = f"runtime-episode-{episode_index}"
        for round_index, public_round in enumerate(document["public"]["rounds"]):
            public_round["source_messages"][0]["text"] = (
                f"FUTURE-PUBLIC-{episode_index}-{round_index}"
            )
            private_round = document["private"]["rounds"][round_index]
            private_round["manual_recap"] = (
                f"CURRENT-REMINDER-{episode_index}-{round_index}"
            )
            for rule in private_round["oracle"]["effective_rules"]:
                rule["text"] += f" PRIVATE-ORACLE-{episode_index}-{round_index}"
        documents.append(document)
    cpu.validate_bank(documents)
    return documents


def _write_bank(tmp_path, documents=None):
    path = tmp_path / "bank.json"
    path.write_text(json.dumps(documents or _bank()), encoding="utf-8")
    return path


class MemoryResponse(io.BytesIO):
    status = 200
    headers = {"Content-Type": "application/json"}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()


class FakeNativeServer:
    def __init__(self, sources, *, failure=None, pending_path=None):
        self.sources = list(sources)
        self.failure = failure
        self.pending_path = pending_path
        self.requests = []
        self.render_payloads = []
        self.completion_payloads = []
        self.prompt_ids = {}
        self.completion_count = 0
        self.saw_pending = False
        self.saw_completion_pending = False

    def _render(self, body):
        payload = json.loads(body)
        self.render_payloads.append(payload)
        ids = cpu.cpu.slab.qwen_encode(body.decode("utf-8"))
        self.prompt_ids[runner._sha_bytes(body)] = ids
        return {
            "token_ids": ids,
            "sampling_params": {
                "structured_outputs": {"json": copy.deepcopy(runner.ARGUMENT_SCHEMA)}
            },
        }

    def _completion(self, body):
        payload = json.loads(body)
        self.completion_payloads.append(payload)
        failure = self.failure if self.completion_count == 0 else None
        source = self.sources[self.completion_count]
        call_id = f"native-call-{self.completion_count}"
        self.completion_count += 1
        if failure == "invalid_json":
            return b"{"
        arguments = json.dumps(
            {"source": source},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        output_ids = cpu.cpu.slab.qwen_encode(arguments)
        prompt_ids = list(self.prompt_ids[runner._sha_bytes(body)])
        if failure == "token_mismatch":
            prompt_ids = prompt_ids + [7]
        total = len(prompt_ids) + len(output_ids)
        result = {
            "prompt_token_ids": prompt_ids,
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": call_id,
                                "type": "function",
                                "function": {
                                    "name": "replace_function",
                                    "arguments": arguments,
                                },
                            }
                        ],
                    },
                    "finish_reason": "length" if failure == "capacity" else "stop",
                    "token_ids": output_ids,
                }
            ],
            "usage": {
                "prompt_tokens": len(prompt_ids),
                "completion_tokens": len(output_ids),
                "total_tokens": total,
            },
        }
        if failure == "usage":
            result["usage"]["total_tokens"] += 1
        return result

    def __call__(self, request, timeout):
        assert timeout > 0
        body = bytes(request.data)
        self.requests.append((request.full_url, body))
        if self.pending_path is not None and not self.saw_pending:
            pending = json.loads(self.pending_path.read_text())
            assert pending["status"] == "PENDING"
            assert pending["native_exchange"]["render"]["status"] == "PENDING"
            self.saw_pending = True
        if (
            self.pending_path is not None
            and not request.full_url.endswith("/render")
            and not self.saw_completion_pending
        ):
            pending = json.loads(self.pending_path.read_text())
            assert pending["native_exchange"]["completion"]["status"] == "PENDING"
            self.saw_completion_pending = True
        if request.full_url.endswith("/render"):
            response = self._render(body)
        else:
            response = self._completion(body)
        if isinstance(response, bytes):
            body_out = response
        else:
            body_out = json.dumps(response).encode("utf-8")
        return MemoryResponse(body_out)


def _reference_sources(documents):
    return [
        private_round["reference_patch"]
        for document in documents
        for private_round in document["private"]["rounds"]
    ]


def test_full_native_run_uses_real_consumer_history_and_hidden_isolation(tmp_path):
    documents = _bank()
    references = _reference_sources(documents)
    invalid = "def alpha(value):\n    break\n"
    wrong = 'def alpha(value):\n    return {"label": "normal", "value": 999}\n'
    sources = [invalid, wrong, references[0], *references[1:]]
    output = tmp_path / "run"
    server = FakeNativeServer(sources, pending_path=output / "calls/call-0000.json")
    client = runner.NativeToolClient("127.0.0.1:9", "/model", opener=server)

    result = runner.run(
        [_write_bank(tmp_path, documents)],
        output,
        client,
        deadline_seconds=100,
    )

    assert result["status"] == "COMPLETE"
    assert result["mechanical_go"] is True
    assert result["competence_go"] is None
    assert result["accounting_complete"] is True
    assert result["recorded_requests"] == 12
    assert result["recorded_calls"] == 14
    assert result["render_requests"] == result["generation_requests"] == 14
    assert server.saw_pending is True
    assert server.saw_completion_pending is True
    assert len(server.requests) == 28
    for offset in range(0, len(server.requests), 2):
        render_url, render_body = server.requests[offset]
        completion_url, completion_body = server.requests[offset + 1]
        assert render_url.endswith("/render")
        assert completion_url.endswith("/chat/completions")
        assert render_body == completion_body
        payload = json.loads(render_body)
        assert payload["tool_choice"] == cpu.FORCED_TOOL_CHOICE
        assert payload["tools"] == [cpu.REPLACE_FUNCTION_TOOL]
        assert payload["return_token_ids"] is True
        assert payload["parallel_tool_calls"] is False
        assert payload["max_tokens"] == 1024

    first = json.loads((output / "requests/request-0000.json").read_text())
    assert [attempt["apply_status"] for attempt in first["attempts"]] == [
        "REJECTED",
        "APPLIED",
        "APPLIED",
    ]
    assert first["public_solved"] is True
    assert first["terminal_private_passed"] is True
    assert {item["check_id"] for item in first["terminal_private_checks"]} == {
        "initial-double",
        "initial-plus-one",
        "private-functional-alpha-0",
        "private-functional-alpha-1",
        "private-obligation-alpha-0",
        "private-obligation-alpha-1",
    }
    rejected = json.loads((output / "calls/call-0000.json").read_text())
    assert rejected["apply_status"] == "REJECTED"
    assert "does not compile" in rejected["consumer_error"]
    assert rejected["pre_module"] == rejected["post_module"]
    wrong_call = json.loads((output / "calls/call-0001.json").read_text())
    assert wrong_call["apply_status"] == "APPLIED"
    assert wrong_call["all_public_passed"] is False
    assert 'value":999' in server.completion_payloads[2]["messages"][-1][
        "content"
    ].replace(" ", "")

    third_messages = server.completion_payloads[2]["messages"]
    assert [message["role"] for message in third_messages[-5:]] == [
        "assistant",
        "tool",
        "assistant",
        "tool",
        "user",
    ]
    for assistant, tool in (
        (third_messages[-5], third_messages[-4]),
        (third_messages[-3], third_messages[-2]),
    ):
        assert assistant["tool_calls"][0]["id"] == tool["tool_call_id"]

    next_request = json.dumps(server.completion_payloads[3], sort_keys=True)
    assert "CURRENT-REMINDER-0-1" in next_request
    assert "CURRENT-REMINDER-0-0" not in next_request
    assert "FUTURE-PUBLIC-0-2" not in next_request
    assert all(
        "PRIVATE-ORACLE" not in json.dumps(payload, sort_keys=True)
        for payload in server.completion_payloads
    )
    assert all(
        "private-functional" not in json.dumps(payload, sort_keys=True)
        for payload in server.completion_payloads
    )
    assert (output / "workspaces/request-0000-terminal.py").read_text() == (
        json.loads((output / "calls/call-0002.json").read_text())["post_module"]
    )
    assert all(project["project_passed"] for project in result["projects"])
    assert sum(project["model_calls"] for project in result["projects"]) == 14
    assert sum(project["total_tokens"] for project in result["projects"]) > 0


@pytest.mark.parametrize(
    ("failure", "kind"),
    [
        ("capacity", "capacity"),
        ("invalid_json", "malformed_response"),
        ("token_mismatch", "token_accounting"),
        ("usage", "token_accounting"),
    ],
)
def test_native_technical_failure_aborts_batch_and_preserves_raw_receipt(
    tmp_path, failure, kind
):
    documents = _bank()
    server = FakeNativeServer(_reference_sources(documents), failure=failure)
    client = runner.NativeToolClient("127.0.0.1:9", "/model", opener=server)
    output = tmp_path / failure

    result = runner.run(
        [_write_bank(tmp_path, documents)],
        output,
        client,
        deadline_seconds=100,
    )

    assert result["status"] == "INCOMPLETE"
    assert result["mechanical_go"] is False
    assert result["accounting_complete"] is False
    assert result["technical_failure"]["kind"] == kind
    assert result["recorded_requests"] == 1
    assert result["completed_requests"] == 0
    assert result["unattempted_requests"] == 11
    assert result["recorded_calls"] == 1
    assert server.completion_count == 1
    assert len(server.requests) == 2
    call = json.loads((output / "calls/call-0000.json").read_text())
    assert call["status"] == "TECHNICAL_ERROR"
    response = call["native_exchange"]["completion"]["response"]
    assert response["body_base64"]
    assert response["body_sha256"]
    assert (
        json.loads((output / "requests/request-0001.json").read_text())["status"]
        == "UNATTEMPTED"
    )
    assert server.requests[0][1] == server.requests[1][1]
    current = json.loads((output / "requests/request-0000.json").read_text())
    assert current["unfinished_private_check_ids"]
    assert call["unfinished_public_check_ids"]


def test_deadline_persists_finished_public_check_and_unfinished_work(tmp_path):
    documents = _bank()
    references = _reference_sources(documents)
    current = [0.0]

    class ImmediateClient:
        def payload(self, messages):
            return {"messages": copy.deepcopy(messages)}

        def perform(self, _body, persist):
            arguments = json.dumps({"source": references[0]})
            exchange = {
                "status": "COMPLETE",
                "render": {"status": "COMPLETE", "elapsed_seconds": 0.0},
                "completion": {"status": "COMPLETE", "elapsed_seconds": 0.0},
                "usage": {
                    "prompt_tokens": 1,
                    "completion_tokens": 1,
                    "total_tokens": 2,
                },
            }
            persist(exchange)
            return {
                "call_id": "immediate-0",
                "arguments": {"source": references[0]},
                "raw_arguments": arguments,
                "assistant_message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "immediate-0",
                            "type": "function",
                            "function": {
                                "name": "replace_function",
                                "arguments": arguments,
                            },
                        }
                    ],
                },
                "usage": exchange["usage"],
            }

    def clock():
        return current[0]

    def one_check(_module, checks):
        check = checks[0]
        current[0] = 5.0
        return [
            {
                "check_id": check["check_id"],
                "symbol": check["symbol"],
                "rule_ids": list(check["rule_ids"]),
                "passed": True,
                "actual": check["expected_values"][0],
                "expected_values": check["expected_values"],
                "error": None,
                "elapsed_seconds": 0.0,
            }
        ]

    output = tmp_path / "deadline"
    result = runner.run(
        [_write_bank(tmp_path, documents)],
        output,
        ImmediateClient(),
        deadline_seconds=5,
        check_runner=one_check,
        clock=clock,
    )

    assert result["status"] == "INCOMPLETE"
    assert result["technical_failure"]["kind"] == "deadline"
    call = json.loads((output / "calls/call-0000.json").read_text())
    assert [item["check_id"] for item in call["public_checks"]] == ["initial-double"]
    assert call["unfinished_public_check_ids"] == [
        "initial-plus-one",
        "public-alpha-0",
        "public-alpha-1",
    ]
    assert (
        json.loads((output / "requests/request-0001.json").read_text())["status"]
        == "UNATTEMPTED"
    )


def test_check_does_not_start_without_sandbox_and_receipt_reserve(tmp_path):
    document = _fixture_document()
    checks = document["public"]["initial_checks"]
    record = {"episode_id": "reserve-control"}
    record_path = tmp_path / "partial-checks.json"
    invocations = []

    def check_runner(_module, _checks):
        invocations.append(True)
        raise AssertionError("sandbox check must not start")

    completed = runner._run_checks_incremental(
        record,
        record_path,
        "checks",
        "unfinished_check_ids",
        document["public"]["initial_file"]["text"],
        "reserve-control",
        checks,
        deadline=1.2,
        clock=lambda: 0.0,
        check_runner=check_runner,
    )

    assert completed is False
    assert invocations == []
    persisted = json.loads(record_path.read_text())
    assert persisted["checks"] == []
    assert persisted["unfinished_check_ids"] == [
        "initial-double",
        "initial-plus-one",
    ]
    assert runner.SANDBOX_CHECK_ALLOWANCE_SECONDS == 2.0
    assert runner.RECEIPT_RESERVE_SECONDS == 1.0


def test_preview_and_absolute_cli_bind_cpu_chain_without_network(tmp_path):
    path = _write_bank(tmp_path)
    result = runner.preview([path])

    assert result["kind"] == "coding-competence-native-preview"
    assert result["status"] == "PASS"
    assert result["model_calls"] == 0
    assert result["documents"] == 4
    assert len(result["reference_actions"]) == 12
    assert result["all_reference_actions_headroom"] is True
    assert all(
        item["eos_allowance_tokens"] == 1 for item in result["reference_actions"]
    )
    assert result["context_preflight"]["actual_cold_request_count"] == 4
    assert result["context_preflight"]["later_actual_requests_known"] is False
    bounds = result["context_preflight"]["conservative_bounds"]
    assert len(bounds) == 36
    assert all(item["future_actual_prompt_claim"] is False for item in bounds)
    assert result["resource_bounds"]["maximum_generation_requests"] == 36
    assert (
        result["resource_bounds"]["maximum_repeated_module_observations_per_prompt"]
        == 9
    )
    assert all(item["source_sha256"] for item in result["reference_actions"])
    assert set(result["code_sha256"]) == {
        "scripts/coding_competence_run.py",
        "scripts/coding_competence_dev.py",
        "scripts/coding_worker_dev.py",
        "src/stencil/focus/slab.py",
        "src/stencil/focus/slab_sandbox.py",
    }
    for cold in result["context_preflight"]["cold_requests"]:
        payload = json.dumps(cold["messages"], sort_keys=True)
        assert "PRIVATE-ORACLE" not in payload
        assert "private-functional" not in payload

    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    process = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/coding_competence_run.py"),
            "--input",
            str(path),
            "--preview",
        ],
        cwd=tmp_path,
        env=environment,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    assert process.returncode == 0, process.stderr
    cli = json.loads(process.stdout)
    assert cli["status"] == "PASS"
    assert cli["inputs"][0]["sha256"] == cpu.sha256_bytes(path.read_bytes())


def test_atomic_receipt_update_preserves_previous_json(tmp_path, monkeypatch):
    path = tmp_path / "receipt.json"
    runner._write_json(path, {"status": "safe"})
    original = path.read_bytes()

    def fail_dump(*_args, **_kwargs):
        raise TypeError("synthetic serialization failure")

    monkeypatch.setattr(runner.json, "dump", fail_dump)
    with pytest.raises(TypeError, match="synthetic serialization failure"):
        runner._write_json(path, {"status": "new"})
    assert path.read_bytes() == original
    assert list(tmp_path.glob(".receipt.json.*.tmp")) == []
