"""CPU checks for the fixed four-call cold diagnostic."""

import base64
import hashlib
import importlib.util
import json
from io import BytesIO
from pathlib import Path
from urllib.error import URLError

ROOT = Path(__file__).parents[1]
DEV_BANK = ROOT / "results/factorial-prep/kimi-dev-reviewed.json"


def driver():
    path = ROOT / "scripts/maintenance_cold_diagnostic.py"
    spec = importlib.util.spec_from_file_location("maintenance_cold_diagnostic", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Response(BytesIO):
    status = 200
    headers = {"Content-Type": "application/json"}


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


def contract(prompt):
    raw = prompt.split("--- TRANSACTION CONTRACT START ---\n", 1)[1]
    raw = raw.split("\n--- TRANSACTION CONTRACT END ---", 1)[0]
    return json.loads(raw)


def empty_transaction(prompt):
    digest = contract(prompt)["input"]["base_state_sha256"]
    return json.dumps(
        {"base_state_sha256": digest, "operations": []},
        separators=(",", ":"),
    )


def add_transaction(prompt, source_text):
    digest = contract(prompt)["input"]["base_state_sha256"]
    start = source_text.index("Python 3.11")
    operation = {
        "action": "add",
        "key": {"new": "python-version"},
        "scope": {"task_handle": None, "request_kinds": ["code_answer"]},
        "kind": "language",
        "value": "Use Python 3.11.",
        "text": "Use Python 3.11.",
        "evidence_span": [start, start + len("Python 3.11")],
    }
    return json.dumps(
        {"base_state_sha256": digest, "operations": [operation]},
        separators=(",", ":"),
    )


def read_run(output):
    rows = [
        json.loads(line) for line in (output / "rows.jsonl").read_text().splitlines()
    ]
    receipts = [
        json.loads(path.read_text()) for path in sorted((output / "calls").iterdir())
    ]
    manifest = json.loads((output / "manifest.json").read_text())
    return manifest, rows, receipts


def test_fake_http_runs_fixed_schedule_and_validates_b_offline(tmp_path):
    d = driver()
    requests = []

    def urlopen(request, *, timeout):
        payload = json.loads(request.data)
        prompt = payload["messages"][0]["content"]
        index = len(requests)
        requests.append((request, timeout, payload, prompt))
        if index == 0:
            output = "- Use Python 3.11 for every code answer."
        elif index == 1:
            source = d.build_cases(DEV_BANK)[1].source.text
            output = add_transaction(prompt, source)
        elif index == 2:
            output = "- Use TypeScript in strict mode for all code answers."
        else:
            output = "{malformed"
        return chat_response(output, prompt_tokens=100 + index)

    out = tmp_path / "run"
    decoder = d.bounded.ChatCompletionDecoder(
        "http://localhost:18088", "/model", 1024, opener=urlopen
    )
    manifest = d.run(
        DEV_BANK,
        out,
        decoder,
        deadline_seconds=300,
        runtime_args=["fake-http"],
    )
    saved, rows, receipts = read_run(out)

    assert manifest == saved
    assert manifest["status"] == "COMPLETE"
    assert manifest["recorded_cases"] == 4
    assert manifest["decoder_calls"] == manifest["network_attempts"] == 4
    assert manifest["case_order"] == [item[0] for item in d.SCHEDULE]
    assert len(requests) == len(rows) == len(receipts) == 4
    assert [row["representation"] for row in rows] == [
        "prose",
        "transaction",
        "prose",
        "transaction",
    ]

    for index, (request, timeout, payload, prompt) in enumerate(requests):
        assert request.full_url == "http://localhost:18088/v1/chat/completions"
        assert 0 < timeout <= 60
        assert payload == json.loads(receipts[index]["http"]["request"]["body"])
        assert payload["model"] == "/model"
        assert payload["max_tokens"] == 1024
        assert payload["temperature"] == 0
        assert payload["seed"] == 20260907
        assert payload["chat_template_kwargs"] == {"enable_thinking": False}
        assert payload["messages"] == [{"role": "user", "content": prompt}]
        raw = base64.b64decode(
            receipts[index]["http"]["request"]["body_base64"], validate=True
        )
        assert raw == request.data
        assert (
            hashlib.sha256(raw).hexdigest()
            == receipts[index]["http"]["request"]["body_sha256"]
        )
        assert len(raw) == receipts[index]["http"]["request"]["body_bytes"]
        assert rows[index]["issued_prompt"] == prompt
        assert rows[index]["call_receipt"] == f"calls/call-{index:04d}.json"

    cases = d.build_cases(DEV_BANK)
    assert requests[0][3].startswith(d.SEMANTIC_INSTRUCTION)
    assert requests[1][3].startswith(d.SEMANTIC_INSTRUCTION)
    assert all(cases[0].source.text in requests[index][3] for index in (0, 1))
    assert all(cases[2].source.text in requests[index][3] for index in (2, 3))
    assert "gold_ops" not in "".join(item[3] for item in requests)
    assert rows[0]["structural_validation"]["status"] == "N/A"
    assert rows[2]["structural_validation"]["post_state"] == "N/A"

    first_b = rows[1]["structural_validation"]
    assert first_b["status"] == "ACCEPTED"
    assert len(first_b["post_state"]["events"]) == 1
    assert rows[1]["issued_prompt"] != rows[1]["validation_prompt"]
    assert len(json.loads(rows[1]["validation_prompt"])["semantic_job"]) == 6
    second_b = rows[3]["structural_validation"]
    assert second_b["status"] == "REJECTED"
    assert "invalid JSON" in second_b["error"]
    assert second_b["pre_state"] == second_b["post_state"]
    assert second_b["pre_state"]["events"] == []
    assert rows[3]["automatic_semantic_score"] is None


def test_length_transport_and_response_cap_errors_continue_without_application(
    tmp_path,
):
    d = driver()
    calls = 0

    def urlopen(request, *, timeout):
        nonlocal calls
        prompt = json.loads(request.data)["messages"][0]["content"]
        index = calls
        calls += 1
        if index == 0:
            return chat_response("concise prose")
        if index == 1:
            source = d.build_cases(DEV_BANK)[1].source.text
            return chat_response(
                add_transaction(prompt, source), finish_reason="length"
            )
        if index == 2:
            raise URLError("synthetic transport error")
        return chat_response(
            empty_transaction(prompt) + " " * d.maintenance_updater.MAX_RESPONSE_CHARS
        )

    out = tmp_path / "errors"
    result = d.run(
        DEV_BANK,
        out,
        d.bounded.ChatCompletionDecoder(
            "http://unused", "/model", 1024, opener=urlopen
        ),
        deadline_seconds=300,
    )
    manifest, rows, _receipts = read_run(out)

    assert result["status"] == manifest["status"] == "COMPLETE"
    assert calls == 4 and manifest["network_attempts"] == 4
    assert manifest["transport_errors"] == 2
    assert rows[1]["raw_output"].startswith('{"base_state_sha256"')
    assert "finish_reason=length" in rows[1]["transport_error"]
    length_validation = rows[1]["structural_validation"]
    assert length_validation["status"] == "REJECTED"
    assert "no recorded raw output" in length_validation["error"]
    assert length_validation["pre_state"] == length_validation["post_state"]
    assert rows[2]["structural_validation"]["status"] == "N/A"
    assert "transport" in rows[2]["transport_error"].lower()
    assert rows[3]["structural_validation"]["status"] == "REJECTED"
    assert "character cap" in rows[3]["structural_validation"]["error"]


def test_deadline_writes_partial_manifest_and_receipt_before_stopping(tmp_path):
    d = driver()

    class Clock:
        value = 0.0

        def __call__(self):
            return self.value

    clock = Clock()
    calls = 0

    def urlopen(request, *, timeout):
        nonlocal calls
        calls += 1
        clock.value = 4.5
        return chat_response("concise prose")

    out = tmp_path / "deadline"
    result = d.run(
        DEV_BANK,
        out,
        d.bounded.ChatCompletionDecoder(
            "http://unused", "/model", 1024, opener=urlopen, clock=clock
        ),
        deadline_seconds=5,
        clock=clock,
    )
    manifest, rows, receipts = read_run(out)

    assert result == manifest
    assert manifest["status"] == "INCOMPLETE"
    assert manifest["reason"] == "deadline before next scheduled case"
    assert manifest["recorded_cases"] == 1
    assert manifest["decoder_calls"] == manifest["network_attempts"] == 1
    assert calls == len(rows) == len(receipts) == 1
    assert rows[0]["call_receipt"] == "calls/call-0000.json"


def test_preview_has_exact_requests_without_decoder_or_output_mutation(
    monkeypatch, tmp_path, capsys
):
    d = driver()
    out = tmp_path / "preview-must-not-exist"

    class ForbiddenDecoder:
        def __init__(self, *args, **kwargs):
            raise AssertionError("preview must not construct the network decoder")

    monkeypatch.setattr(d.bounded, "ChatCompletionDecoder", ForbiddenDecoder)
    args = [
        "--input",
        str(DEV_BANK),
        "--output-dir",
        str(out),
        "--base-url",
        "localhost:18088",
        "--model",
        "/model",
        "--max-tokens",
        "1024",
        "--deadline-seconds",
        "300",
        "--preview",
    ]
    assert d.main(args) == 0
    planned = json.loads(capsys.readouterr().out)

    assert not out.exists()
    assert planned["scheduled_cases"] == 4
    assert planned["network_calls"] == 0
    assert planned["output_directory_mutated"] is False
    assert [row["case_id"] for row in planned["requests"]] == [
        item[0] for item in d.SCHEDULE
    ]
    for row in planned["requests"]:
        request = row["http_request"]
        raw = base64.b64decode(request["body_base64"], validate=True)
        assert raw.decode() == request["body"]
        assert len(raw) == request["body_bytes"]
        assert json.loads(raw)["messages"][0]["content"] == row["issued_prompt"]
    assert planned["requests"][0]["validation_prompt"] is None
    assert planned["requests"][1]["validation_prompt"] is not None
