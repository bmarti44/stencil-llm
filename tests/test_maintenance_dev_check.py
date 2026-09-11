"""CPU checks for the sequential automatic-maintenance DEV driver."""

import base64
import hashlib
import importlib.util
import json
import re
from http.client import IncompleteRead
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError, URLError

import pytest

ROOT = Path(__file__).parents[1]
DEV_BANK = ROOT / "results/factorial-prep/kimi-dev-reviewed.json"


def driver():
    path = ROOT / "scripts/maintenance_dev_check.py"
    spec = importlib.util.spec_from_file_location("maintenance_dev_check", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Response(BytesIO):
    status = 200
    headers = {"Content-Type": "application/json"}


class PartialResponse(Response):
    status = 206
    headers = {"Content-Type": "application/json", "X-Synthetic": "partial"}

    def __init__(self, partial):
        super().__init__()
        self.partial = partial

    def read(self, *args, **kwargs):
        raise IncompleteRead(self.partial, 100)


def base_hash(prompt):
    digest = json.loads(prompt)["input"]["base_state_sha256"]
    assert re.fullmatch(r"[0-9a-f]{64}", digest)
    return digest


def chat_response(content, *, finish_reason="stop", prompt_tokens=10):
    return Response(
        json.dumps(
            {
                "id": "fake-chat",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": content},
                        "finish_reason": finish_reason,
                    }
                ],
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": 3,
                    "total_tokens": prompt_tokens + 3,
                },
            }
        ).encode()
    )


def exact_response_bytes(receipt):
    response = receipt["http"]["response"]
    raw = base64.b64decode(response["body_base64"], validate=True)
    assert response["body_sha256"] == hashlib.sha256(raw).hexdigest()
    assert response["body_bytes"] == len(raw)
    return raw


def test_cli_real_consumer_runs_two_sequential_trajectories(monkeypatch, tmp_path):
    d = driver()
    requests = []

    def urlopen(request, *, timeout):
        payload = json.loads(request.data)
        prompt = payload["messages"][0]["content"]
        requests.append((request, timeout, payload, prompt))
        output = json.dumps(
            {"base_state_sha256": base_hash(prompt), "operations": []},
            separators=(",", ":"),
        )
        return chat_response(output)

    monkeypatch.setattr(d, "urlopen", urlopen)
    out = tmp_path / "run"
    args = [
        "--input",
        str(DEV_BANK),
        "--output-dir",
        str(out),
        "--base-url",
        "http://localhost:18088",
        "--model",
        "/model",
        "--max-tokens",
        "1024",
        "--deadline-seconds",
        "300",
    ]
    assert d.main(args) == 0

    rows = [json.loads(line) for line in (out / "rows.jsonl").read_text().splitlines()]
    manifest = json.loads((out / "manifest.json").read_text())
    receipts = [
        json.loads(path.read_text()) for path in sorted((out / "calls").iterdir())
    ]
    assert len(requests) == len(rows) == len(receipts) == 16
    assert manifest["status"] == "COMPLETE"
    assert manifest["scheduled_turns"] == manifest["recorded_turns"] == 16
    assert manifest["runtime_args"] == args
    assert manifest["gold_source"] == {
        "path": str(DEV_BANK),
        "sha256": d.sha256_file(DEV_BANK),
    }
    assert "accuracy" not in manifest and "score" not in manifest

    for request, timeout, payload, prompt in requests:
        assert request.full_url == "http://localhost:18088/v1/chat/completions"
        assert 0 < timeout <= 60
        assert payload["model"] == "/model"
        assert payload["max_tokens"] == 1024
        assert payload["temperature"] == 0
        assert payload["seed"] == 20260907
        assert payload["chat_template_kwargs"] == {"enable_thinking": False}
        assert payload["messages"] == [{"role": "user", "content": prompt}]
        assert all(
            hidden not in prompt
            for hidden in ("gold_ops", "expected_ops", "expected_live", "rationale")
        )
    assert all(row["accepted"] and row["accepted_ops"] == [] for row in rows)
    assert rows[0]["source"]["message_id"].endswith(":round:0")
    assert rows[1]["past_message_count"] == 1
    assert rows[8]["past_message_count"] == 0
    assert all(receipt["http"]["request"]["body"] for receipt in receipts)
    assert all(receipt["http"]["response"]["body"] for receipt in receipts)
    assert all(
        exact_response_bytes(receipt)
        == receipt["http"]["response"]["body"].encode("utf-8")
        for receipt in receipts
    )


def test_state_advances_only_from_accepted_actual_results(tmp_path):
    d = driver()
    calls = 0

    def urlopen(request, *, timeout):
        nonlocal calls
        prompt = json.loads(request.data)["messages"][0]["content"]
        state_hash = base_hash(prompt)
        if calls in {0, 8}:
            # The first source in each episode is authoritative. Ground a simple
            # test-only rule in its first code point; no annotation is consulted.
            source = json.loads(prompt)["input"]["source"]["text"]
            operation = {
                "action": "add",
                "key": {"new": "test_rule"},
                "scope": {
                    "task_handle": None,
                    "request_kinds": ["code_answer"],
                },
                "kind": "process",
                "value": "test value",
                "text": source[0],
                "evidence_span": [0, 1],
            }
            operations = [operation]
        else:
            operations = []
        calls += 1
        return chat_response(
            json.dumps(
                {"base_state_sha256": state_hash, "operations": operations},
                separators=(",", ":"),
            )
        )

    out = tmp_path / "state"
    result = d.run(
        DEV_BANK,
        out,
        d.ChatCompletionDecoder("unused:18088", "/model", 1024, opener=urlopen),
        deadline_seconds=300,
        runtime_args=["injected-http-test"],
    )
    rows = [json.loads(line) for line in (out / "rows.jsonl").read_text().splitlines()]
    assert result["status"] == "COMPLETE" and calls == 16
    assert rows[0]["accepted"] and len(rows[0]["post_state"]["events"]) == 1
    assert len(rows[1]["pre_state"]["events"]) == 1
    assert rows[1]["pre_state"]["events"] == rows[0]["post_state"]["events"]
    assert rows[1]["pre_state_sha256"] != rows[0]["post_state_sha256"]
    assert rows[8]["pre_state"]["events"] == []
    assert rows[8]["generation"] == 0 and rows[9]["generation"] == 1


def test_transport_protocol_and_length_failures_have_receipts_and_continue(tmp_path):
    d = driver()
    calls = 0

    def urlopen(request, *, timeout):
        nonlocal calls
        prompt = json.loads(request.data)["messages"][0]["content"]
        output = json.dumps(
            {"base_state_sha256": base_hash(prompt), "operations": []},
            separators=(",", ":"),
        )
        index = calls
        calls += 1
        if index == 0:
            return chat_response(output, finish_reason="length")
        if index == 1:
            raise URLError("synthetic transport failure")
        if index == 2:
            return Response(json.dumps({"choices": []}).encode())
        if index == 3:
            body = b'{"error":"synthetic unavailable"}'
            raise HTTPError(
                request.full_url,
                503,
                "unavailable",
                {"Retry-After": "1"},
                BytesIO(body),
            )
        return chat_response(output)

    out = tmp_path / "failures"
    result = d.run(
        DEV_BANK,
        out,
        d.ChatCompletionDecoder("http://unused", "/model", 1024, opener=urlopen),
        deadline_seconds=300,
        runtime_args=["failure-test"],
    )
    rows = [json.loads(line) for line in (out / "rows.jsonl").read_text().splitlines()]
    receipts = [
        json.loads(path.read_text()) for path in sorted((out / "calls").iterdir())
    ]
    assert result["status"] == "COMPLETE" and len(rows) == calls == 16
    assert rows[0]["raw_output"] is not None
    assert "length" in rows[0]["error"]
    assert "transport" in rows[1]["error"].lower()
    assert rows[0]["pre_state"] == rows[0]["post_state"]
    assert rows[1]["pre_state"] == rows[1]["post_state"]
    assert receipts[0]["http"]["finish_reason"] == "length"
    assert receipts[1]["http"]["response"] is None
    assert receipts[1]["decoder_error"]
    assert receipts[2]["http"]["response"]["body"] == '{"choices": []}'
    assert exact_response_bytes(receipts[3]) == b'{"error":"synthetic unavailable"}'
    assert receipts[3]["http"]["response"]["status"] == 503


def test_invalid_utf8_is_exactly_preserved_rejected_and_never_committed(tmp_path):
    d = driver()
    calls = 0
    corrupt_body = None

    def urlopen(request, *, timeout):
        nonlocal calls, corrupt_body
        prompt = json.loads(request.data)["messages"][0]["content"]
        state_hash = base_hash(prompt)
        if calls == 0:
            source = json.loads(prompt)["input"]["source"]["text"]
            operation = {
                "action": "add",
                "key": {"new": "corrupt_test"},
                "scope": {
                    "task_handle": None,
                    "request_kinds": ["code_answer"],
                },
                "kind": "process",
                "value": "VALUE_MARKER",
                "text": source[0],
                "evidence_span": [0, 1],
            }
            proposal = json.dumps(
                {"base_state_sha256": state_hash, "operations": [operation]},
                separators=(",", ":"),
            )
            normal = chat_response(proposal).getvalue()
            corrupt_body = normal.replace(b"VALUE_MARKER", b"VALUE_\xff")
            response = Response(corrupt_body)
        else:
            proposal = json.dumps(
                {"base_state_sha256": state_hash, "operations": []},
                separators=(",", ":"),
            )
            response = chat_response(proposal)
        calls += 1
        return response

    out = tmp_path / "invalid-utf8"
    result = d.run(
        DEV_BANK,
        out,
        d.ChatCompletionDecoder("http://unused", "/model", 1024, opener=urlopen),
        deadline_seconds=300,
        runtime_args=["invalid-utf8-test"],
    )
    rows = [json.loads(line) for line in (out / "rows.jsonl").read_text().splitlines()]
    receipts = [
        json.loads(path.read_text()) for path in sorted((out / "calls").iterdir())
    ]
    assert result["status"] == "COMPLETE" and calls == len(rows) == 16
    assert not rows[0]["accepted"] and "UTF-8" in rows[0]["error"]
    assert rows[0]["pre_state"] == rows[0]["post_state"]
    assert rows[1]["pre_state"]["events"] == []
    assert receipts[0]["http"]["response"]["body"] is None
    assert exact_response_bytes(receipts[0]) == corrupt_body


def test_incomplete_read_preserves_partial_response_and_schedule(tmp_path):
    d = driver()
    calls = 0
    partial = b'{"choices":[{"message":'

    def urlopen(request, *, timeout):
        nonlocal calls
        prompt = json.loads(request.data)["messages"][0]["content"]
        if calls == 0:
            response = PartialResponse(partial)
        else:
            proposal = json.dumps(
                {"base_state_sha256": base_hash(prompt), "operations": []},
                separators=(",", ":"),
            )
            response = chat_response(proposal)
        calls += 1
        return response

    out = tmp_path / "partial-read"
    result = d.run(
        DEV_BANK,
        out,
        d.ChatCompletionDecoder("http://unused", "/model", 1024, opener=urlopen),
        deadline_seconds=300,
        runtime_args=["partial-read-test"],
    )
    rows = [json.loads(line) for line in (out / "rows.jsonl").read_text().splitlines()]
    receipts = [
        json.loads(path.read_text()) for path in sorted((out / "calls").iterdir())
    ]
    response = receipts[0]["http"]["response"]
    assert result["status"] == "COMPLETE" and calls == len(rows) == 16
    assert not rows[0]["accepted"] and "IncompleteRead" in rows[0]["error"]
    assert rows[1]["accepted"] and rows[1]["pre_state"]["events"] == []
    assert exact_response_bytes(receipts[0]) == partial
    assert response["status"] == 206
    assert response["headers"]["X-Synthetic"] == "partial"
    assert response["incomplete_read_expected_bytes"] == 100


def test_dev_gate_output_gate_and_explicit_deadline(tmp_path):
    d = driver()
    raw = json.loads(DEV_BANK.read_text())
    raw["split"] = "eval"
    evaluation = tmp_path / "not-dev.json"
    evaluation.write_text(json.dumps(raw))

    def decoder(prompt):
        pytest.fail("decoder must not be called")

    with pytest.raises(ValueError, match="DEV"):
        d.run(evaluation, tmp_path / "eval-out", decoder)

    occupied = tmp_path / "occupied"
    occupied.mkdir()
    (occupied / "keep").write_text("user data")
    with pytest.raises(FileExistsError, match="nonempty"):
        d.run(DEV_BANK, occupied, decoder)
    assert (occupied / "keep").read_text() == "user data"

    out = tmp_path / "deadline"
    manifest = d.run(
        DEV_BANK,
        out,
        decoder,
        deadline_seconds=0.5,
        runtime_args=["deadline-test"],
        clock=lambda: 0.0,
    )
    assert manifest["status"] == "INCOMPLETE"
    assert manifest["recorded_turns"] == 0
    assert manifest["reason"] == "deadline before next scheduled turn"
