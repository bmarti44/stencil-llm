"""Targeted CPU controls for the fixed prose-maintenance DEV trial."""

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
    return load_module("scripts/prose_maintenance_dev.py", "prose_maintenance_dev")


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


def response_bytes(receipt):
    saved = receipt["http"]["response"]
    raw = base64.b64decode(saved["body_base64"], validate=True)
    assert saved["body_sha256"] == hashlib.sha256(raw).hexdigest()
    assert saved["body_bytes"] == len(raw)
    return raw


def test_actual_http_path_carries_only_own_notes_and_natural_history(tmp_path):
    d = driver()
    requests = []
    allocation = d._load(DEV_BANK)
    tool_index = next(
        index
        for index, round_ in enumerate(
            round_ for episode in allocation.episodes for round_ in episode.rounds
        )
        if round_.messages[0].role == "tool"
    )

    def urlopen(request, *, timeout):
        index = len(requests)
        payload = json.loads(request.data)
        requests.append((request, timeout, payload))
        output = (
            "NONUSER CANDIDATE MUST NOT APPLY"
            if index == tool_index
            else f"actual notes {index}"
        )
        return chat_response(output, prompt_tokens=20 + index)

    out = tmp_path / "run"
    result = d.run(
        DEV_BANK,
        out,
        d.bounded.ChatCompletionDecoder(
            "http://localhost:18088", "/model", 1024, opener=urlopen
        ),
        deadline_seconds=300,
        runtime_args=["fake-http"],
    )
    manifest, rows, receipts = read_run(out)

    assert result == manifest
    assert manifest["status"] == "COMPLETE"
    assert manifest["scheduled_calls"] == manifest["recorded_calls"] == 16
    assert manifest["decoder_calls"] == manifest["network_attempts"] == 16
    assert len(requests) == len(rows) == len(receipts) == 16
    assert [row["history_count"] for row in rows] == list(range(8)) * 2
    assert rows[0]["pre_notes"] == d.EMPTY_NOTES
    assert rows[0]["post_notes"] == "actual notes 0"
    assert rows[1]["pre_notes"] == "actual notes 0"
    assert rows[1]["source_history"] == [
        {
            "message_id": rows[0]["source_id"],
            "role": rows[0]["source_role"],
            "text": rows[0]["source_text"],
        }
    ]
    assert "actual notes 0" in rows[1]["issued_prompt"]
    assert rows[0]["source_text"] in rows[1]["issued_prompt"]

    tool_row = rows[tool_index]
    next_row = rows[tool_index + 1]
    assert tool_row["source_role"] == "tool"
    assert tool_row["candidate_status"] == "BLOCKED_NON_USER"
    assert not tool_row["applied"] and tool_row["candidate_error"] is None
    assert tool_row["post_notes"] == tool_row["pre_notes"]
    assert next_row["pre_notes"] == tool_row["pre_notes"]
    assert "NONUSER CANDIDATE MUST NOT APPLY" not in next_row["issued_prompt"]
    assert rows[8]["pre_notes"] == d.EMPTY_NOTES
    assert rows[8]["history_count"] == 0 and rows[8]["source_history"] == []

    prompts = "\n".join(row["issued_prompt"] for row in rows)
    assert all(
        hidden not in prompts
        for hidden in ("gold_ops", "expected_live", "rationale", "event_id")
    )
    assert d.INSTRUCTION in rows[0]["issued_prompt"]
    assert "code_answer" in rows[0]["issued_prompt"]
    assert all(row["automatic_semantic_score"] is None for row in rows)

    for index, ((request, timeout, payload), row, receipt) in enumerate(
        zip(requests, rows, receipts, strict=True)
    ):
        assert 0 < timeout <= 60
        assert request.full_url == "http://localhost:18088/v1/chat/completions"
        assert payload["messages"] == [
            {"role": "user", "content": row["issued_prompt"]}
        ]
        assert payload["max_tokens"] == 1024
        saved = receipt["http"]["request"]
        raw = base64.b64decode(saved["body_base64"], validate=True)
        assert raw == request.data
        assert saved["body_sha256"] == hashlib.sha256(raw).hexdigest()
        assert saved["body_bytes"] == len(raw)
        assert receipt["raw_output"] == rows[index]["raw_output"]
        assert response_bytes(receipt)


def test_failures_and_nonuser_candidates_never_partially_apply(tmp_path):
    d = driver()
    calls = 0
    corrupt_body = None

    def urlopen(request, *, timeout):
        nonlocal calls, corrupt_body
        index = calls
        calls += 1
        if index == 0:
            return chat_response("stable notes")
        if index == 1:
            return chat_response("length candidate", finish_reason="length")
        if index == 2:
            return chat_response("x" * (d.NOTES_CHARACTER_CAP + 1))
        if index == 3:
            return chat_response("valid user notes after prior failures")
        if index == 4:
            corrupt_body = (
                chat_response("bad marker")
                .getvalue()
                .replace(b"bad marker", b"bad \xff marker")
            )
            return Response(corrupt_body)
        if index == 5:
            return PartialResponse()
        if index == 6:
            return chat_response("bad surrogate: \ud800")
        if index == 10:
            return chat_response("tool tried to erase every rule")
        return chat_response(f"recovered notes {index}")

    out = tmp_path / "errors"
    result = d.run(
        DEV_BANK,
        out,
        d.bounded.ChatCompletionDecoder("unused:18088", "/model", 1024, opener=urlopen),
        deadline_seconds=300,
    )
    manifest, rows, receipts = read_run(out)

    assert result["status"] == manifest["status"] == "COMPLETE"
    assert calls == len(rows) == len(receipts) == 16
    assert manifest["candidate_errors"] == 5
    assert rows[0]["post_notes"] == "stable notes"
    for index in (1, 2, 4, 5, 6):
        assert rows[index]["post_notes"] == rows[index]["pre_notes"]
        assert not rows[index]["applied"]
    assert "length" in rows[1]["candidate_error"]
    assert rows[1]["raw_output"] == "length candidate"
    assert "character cap" in rows[2]["candidate_error"]
    assert rows[2]["raw_output"] == "x" * (d.NOTES_CHARACTER_CAP + 1)
    assert rows[3]["applied"]
    assert "UTF-8" in rows[4]["candidate_error"]
    assert response_bytes(receipts[4]) == corrupt_body
    assert "IncompleteRead" in rows[5]["candidate_error"]
    assert response_bytes(receipts[5]) == b'{"partial":'
    assert "Unicode scalar" in rows[6]["candidate_error"]
    assert receipts[6]["raw_output"] == "bad surrogate: \ud800"
    assert rows[6]["raw_output"] == "bad surrogate: \ud800"
    assert b"\\ud800" in response_bytes(receipts[6])
    assert rows[7]["applied"] and rows[7]["post_notes"] == "recovered notes 7"
    assert rows[10]["source_role"] == "tool"
    assert rows[10]["candidate_status"] == "BLOCKED_NON_USER"
    assert rows[10]["post_notes"] == rows[10]["pre_notes"]


def test_deadline_saves_partial_manifest_and_complete_first_receipt(tmp_path):
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
        return chat_response("first notes")

    out = tmp_path / "partial"
    result = d.run(
        DEV_BANK,
        out,
        d.bounded.ChatCompletionDecoder(
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
    assert rows[0]["call_receipt"] == "calls/call-0000.json"


def test_preview_shows_two_cold_prompts_without_actions_or_fake_future_state(
    monkeypatch, tmp_path, capsys
):
    d = driver()
    out = tmp_path / "must-not-exist"

    class ForbiddenNetworkDecoder(d.bounded.ChatCompletionDecoder):
        def __call__(self, prompt):
            raise AssertionError("preview must not perform a network action")

    monkeypatch.setattr(d.bounded, "ChatCompletionDecoder", ForbiddenNetworkDecoder)
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
    assert planned["scheduled_calls"] == 16
    assert planned["shown_cold_prompts"] == 2
    assert planned["network_calls"] == 0
    assert planned["output_directory_mutated"] is False
    assert planned["later_prompts_known"] is False
    assert "cannot be known" in planned["note"]
    assert len(planned["requests"]) == 2
    for item in planned["requests"]:
        assert d.EMPTY_NOTES in item["issued_prompt"]
        assert "(none)" in item["issued_prompt"]
        raw = base64.b64decode(item["http_request"]["body_base64"], validate=True)
        assert json.loads(raw)["messages"][0]["content"] == item["issued_prompt"]


def test_all_whole_input_caps_reject_without_truncation():
    d = driver()
    source = {"role": "user", "text": "source"}
    with pytest.raises(ValueError, match="notes exceed"):
        d.build_prompt("n" * (d.NOTES_CHARACTER_CAP + 1), (), source, ("a", "b"))
    with pytest.raises(ValueError, match="source exceeds"):
        d.build_prompt(
            d.EMPTY_NOTES,
            (),
            {"role": "user", "text": "s" * (d.SOURCE_CHARACTER_CAP + 1)},
            ("a", "b"),
        )
    history = ({"role": "user", "text": "h" * (d.HISTORY_CHARACTER_CAP + 1)},)
    with pytest.raises(ValueError, match="history exceeds"):
        d.build_prompt(d.EMPTY_NOTES, history, source, ("a", "b"))
    with pytest.raises(ValueError, match="Unicode scalar"):
        d.build_prompt("bad \ud800", (), source, ("a", "b"))


def test_launcher_prose_mode_binds_new_recipe_and_preserves_old_modes(capsys):
    launcher = load_module("tools/run_maintenance_dev.py", "run_maintenance_dev")
    expected = {
        "maintenance": (
            "scripts/maintenance_dev_check.py",
            "results/factorial-prep/kimi-dev-reviewed.json",
        ),
        "cold": (
            "scripts/maintenance_cold_diagnostic.py",
            "results/factorial-prep/kimi-dev-reviewed.json",
        ),
        "prose": (
            "scripts/prose_maintenance_dev.py",
            "results/prose-maintenance/kimi-dev-reviewed.json",
        ),
    }
    for mode, (driver_path, input_path) in expected.items():
        run = ROOT / "results/quick-checks" / f"dry-{mode}"
        assert launcher.main(["--mode", mode, "--run-dir", str(run)]) == 0
        plan = json.loads(capsys.readouterr().out)
        assert plan["mode"] == mode
        assert plan["driver"] == str(ROOT / driver_path)
        assert plan["input"] == str(ROOT / input_path)
        assert plan["max_tokens"] == 1024
        assert plan["gpu_held_ceiling_seconds"] == 900
        assert plan["startup_ceiling_seconds"] == 600
        assert plan["cleanup_reserve_seconds"] == 60
        if mode == "prose":
            assert "results/prose-maintenance/PROTOCOL.md" in plan["bound_files"]
            assert (
                "results/prose-maintenance/kimi-dev-reviewed.json"
                in plan["bound_files"]
            )
