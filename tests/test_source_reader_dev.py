"""Focused CPU controls for the fixed source-only reader DEV trial."""

import base64
import hashlib
import importlib.util
import json
from http.client import IncompleteRead
from io import BytesIO
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
DEV_BANK = ROOT / "results/prose-maintenance/kimi-dev-reviewed.json"


def load_module(relative, name):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def driver():
    return load_module("scripts/source_reader_dev.py", "source_reader_dev")


class Response(BytesIO):
    status = 200
    headers = {"Content-Type": "application/json"}


class PartialResponse(Response):
    def read(self, *args, **kwargs):
        raise IncompleteRead(b'{"partial":', 100)


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
        ).encode("utf-8")
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


def exact_body(saved):
    raw = base64.b64decode(saved["body_base64"], validate=True)
    assert saved["body_sha256"] == hashlib.sha256(raw).hexdigest()
    assert saved["body_bytes"] == len(raw)
    return raw


def test_preview_and_fake_http_are_exact_fixed_independent_48_calls(tmp_path):
    d = driver()
    preview = d.preview(DEV_BANK, "http://localhost:18088", "/model", 1024)
    requests = []

    def urlopen(request, *, timeout):
        index = len(requests)
        requests.append((request, timeout))
        return chat_response(f"GENERATED-SELECTION-{index}", prompt_tokens=100 + index)

    out = tmp_path / "run"
    result = d.run(
        DEV_BANK,
        out,
        d.prose.bounded.ChatCompletionDecoder(
            "http://localhost:18088", "/model", 1024, opener=urlopen
        ),
        deadline_seconds=600,
        runtime_args=["fake-http"],
    )
    manifest, rows, receipts = read_run(out)

    assert result == manifest and manifest["status"] == "COMPLETE"
    assert manifest["recorded_calls"] == manifest["decoder_calls"] == 48
    assert manifest["network_attempts"] == manifest["discarded_outputs"] == 48
    assert manifest["call_errors"] == 0
    assert manifest["generated_output_in_any_prompt"] is False
    assert len(requests) == len(rows) == len(receipts) == 48
    assert preview["shown_requests"] == preview["scheduled_calls"] == 48
    assert preview["all_prompts_known_before_inference"] is True

    allocation = d.prose._load(DEV_BANK)
    expected_views = []
    expected_counts = []
    for episode in allocation.episodes:
        for turn in range(8):
            expected_views.extend(["GLOBAL", *episode.task.task_handles])
            expected_counts.extend([turn + 1] * 3)
    assert [row["view"] for row in rows] == expected_views
    assert [row["source_history_count"] for row in rows] == expected_counts
    assert [row["case_id"] for row in rows] == manifest["case_order"]
    assert rows[0]["requested_task"] is None
    assert rows[1]["requested_task"] == allocation.episodes[0].task.task_handles[0]
    assert rows[24]["source_history_count"] == 1

    tool_rows = [
        row
        for row in rows
        if any(item["role"] == "tool" for item in row["source_history"])
    ]
    assert tool_rows
    assert all(row["response_status"] == "RECORDED" for row in tool_rows)
    assert all(row["discarded_after_call"] and not row["fed_forward"] for row in rows)
    assert all(row["automatic_semantic_score"] is None for row in rows)
    assert all(row["automatic_citation_score"] is None for row in rows)

    all_prompts = "\n".join(row["issued_prompt"] for row in rows)
    assert "GENERATED-SELECTION-" not in all_prompts
    assert all(
        hidden not in all_prompts
        for hidden in ("gold_ops", "expected_live", "rationale", "event_id")
    )
    for item in rows[32]["source_history"]:
        assert item["message_id"] in rows[32]["issued_prompt"]
        assert item["text"] in rows[32]["issued_prompt"]

    for index, ((request, timeout), planned, row, receipt) in enumerate(
        zip(requests, preview["requests"], rows, receipts, strict=True)
    ):
        assert 0 < timeout <= 60
        assert request.data == exact_body(planned["http_request"])
        assert request.data == exact_body(receipt["http"]["request"])
        assert json.loads(request.data)["messages"] == [
            {"role": "user", "content": row["issued_prompt"]}
        ]
        assert planned["issued_prompt"] == row["issued_prompt"]
        assert receipt["prompt"] == row["issued_prompt"]
        assert receipt["raw_output"] == f"GENERATED-SELECTION-{index}"
        assert exact_body(receipt["http"]["response"])


def test_errors_are_durable_discarded_and_make_run_incomplete(tmp_path):
    d = driver()
    calls = 0
    corrupt_body = None

    def urlopen(request, *, timeout):
        nonlocal calls, corrupt_body
        index = calls
        calls += 1
        if index == 0:
            return chat_response("length candidate", finish_reason="length")
        if index == 1:
            return chat_response("x" * (d.prose.NOTES_CHARACTER_CAP + 1))
        if index == 2:
            corrupt_body = (
                chat_response("bad marker")
                .getvalue()
                .replace(b"bad marker", b"bad \xff marker")
            )
            return Response(corrupt_body)
        if index == 3:
            return PartialResponse()
        if index == 4:
            return chat_response("bad surrogate: \ud800")
        return chat_response(f"valid selection {index}")

    out = tmp_path / "errors"
    result = d.run(
        DEV_BANK,
        out,
        d.prose.bounded.ChatCompletionDecoder(
            "unused:18088", "/model", 1024, opener=urlopen
        ),
        deadline_seconds=600,
    )
    manifest, rows, receipts = read_run(out)

    assert result["status"] == manifest["status"] == "INCOMPLETE"
    assert manifest["reason"] == "one or more calls failed transport or output validity"
    assert calls == len(rows) == len(receipts) == 48
    assert manifest["recorded_calls"] == manifest["network_attempts"] == 48
    assert manifest["call_errors"] == 5
    assert "length" in rows[0]["error"]
    assert rows[0]["raw_output"] == "length candidate"
    assert "character cap" in rows[1]["error"]
    assert rows[1]["raw_output"] == "x" * (d.prose.NOTES_CHARACTER_CAP + 1)
    assert "UTF-8" in rows[2]["error"]
    assert exact_body(receipts[2]["http"]["response"]) == corrupt_body
    assert "IncompleteRead" in rows[3]["error"]
    assert exact_body(receipts[3]["http"]["response"]) == b'{"partial":'
    assert "Unicode scalar" in rows[4]["error"]
    assert rows[4]["raw_output"] == "bad surrogate: \ud800"
    assert b"\\ud800" in exact_body(receipts[4]["http"]["response"])
    assert all(row["discarded_after_call"] and not row["fed_forward"] for row in rows)
    assert "valid selection 5" not in rows[6]["issued_prompt"]


def test_deadline_saves_one_complete_call_and_partial_manifest(tmp_path):
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
        return chat_response("first selection")

    out = tmp_path / "deadline"
    result = d.run(
        DEV_BANK,
        out,
        d.prose.bounded.ChatCompletionDecoder(
            "unused:18088", "/model", 1024, opener=urlopen, clock=clock
        ),
        deadline_seconds=5,
        clock=clock,
    )
    manifest, rows, receipts = read_run(out)

    assert result == manifest and manifest["status"] == "INCOMPLETE"
    assert manifest["reason"] == "deadline before next scheduled call"
    assert manifest["recorded_calls"] == manifest["decoder_calls"] == 1
    assert manifest["network_attempts"] == calls == len(rows) == len(receipts) == 1
    assert rows[0]["raw_output"] == "first selection"
    assert rows[0]["discarded_after_call"] and not rows[0]["fed_forward"]


def test_input_caps_and_surrogates_fail_whole_without_output(tmp_path):
    d = driver()
    valid = {"message_id": "m0", "role": "user", "text": "source"}
    too_long = dict(valid, text="s" * (d.prose.SOURCE_CHARACTER_CAP + 1))
    with pytest.raises(ValueError, match="source exceeds"):
        d.build_prompt((too_long,), ("one", "two"), None)
    history = tuple(dict(valid, message_id=f"m{i}", text="h" * 5000) for i in range(7))
    with pytest.raises(ValueError, match="history exceeds"):
        d.build_prompt(history, ("one", "two"), None)
    with pytest.raises(ValueError, match="field boundary"):
        d.build_prompt((dict(valid, extra="forbidden"),), ("one", "two"), None)
    with pytest.raises(ValueError, match="prompt exceeds"):
        d.build_prompt((valid,), ("a" * 70000, "b" * 70000), None)

    malformed = json.loads(DEV_BANK.read_text())
    malformed["episodes"][0]["rounds"][0]["message"] = "bad \ud800"
    input_path = tmp_path / "malformed.json"
    input_path.write_text(json.dumps(malformed, ensure_ascii=True))
    out = tmp_path / "must-not-exist"
    with pytest.raises(ValueError, match="Unicode scalar"):
        d.run(input_path, out, lambda prompt: "unused")
    assert not out.exists()


def test_full_preview_cli_has_no_network_or_output_mutation(
    monkeypatch, tmp_path, capsys
):
    d = driver()
    out = tmp_path / "preview-must-not-exist"

    class ForbiddenNetworkDecoder(d.prose.bounded.ChatCompletionDecoder):
        def __call__(self, prompt):
            raise AssertionError("preview must not perform a network action")

    monkeypatch.setattr(
        d.prose.bounded, "ChatCompletionDecoder", ForbiddenNetworkDecoder
    )
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
        "--preview",
    ]
    assert d.main(args) == 0
    planned = json.loads(capsys.readouterr().out)
    assert not out.exists()
    assert planned["shown_requests"] == len(planned["requests"]) == 48
    assert planned["network_calls"] == 0
    assert planned["output_directory_mutated"] is False
    assert planned["generated_output_in_any_prompt"] is False


def test_launcher_four_modes_keep_old_budgets_and_bind_reader(capsys):
    launcher = load_module("tools/run_maintenance_dev.py", "run_maintenance_dev")
    modes = {
        "maintenance": ("scripts/maintenance_dev_check.py", 900),
        "cold": ("scripts/maintenance_cold_diagnostic.py", 900),
        "prose": ("scripts/prose_maintenance_dev.py", 900),
        "source-reader": ("scripts/source_reader_dev.py", 2700),
    }
    for mode, (driver_path, budget) in modes.items():
        run = ROOT / "results/quick-checks" / f"dry-{mode}"
        assert launcher.main(["--mode", mode, "--run-dir", str(run)]) == 0
        plan = json.loads(capsys.readouterr().out)
        assert plan["mode"] == mode
        assert plan["driver"] == str(ROOT / driver_path)
        assert plan["gpu_held_ceiling_seconds"] == budget
        assert plan["startup_ceiling_seconds"] == 600
        assert plan["cleanup_reserve_seconds"] == 60
        assert plan["max_tokens"] == 1024
        if mode == "source-reader":
            assert plan["input"] == str(DEV_BANK)
            assert "results/source-reader/PROTOCOL.md" in plan["bound_files"]
            assert "results/source-reader/preview.json" in plan["bound_files"]
            assert (
                "results/factorial-prep/current-trunk-hashes.json"
                in plan["bound_files"]
            )
            assert "src/stencil/focus/maintenance_updater.py" in plan["bound_files"]
