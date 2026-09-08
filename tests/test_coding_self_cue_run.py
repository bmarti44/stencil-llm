"""Consequential controls for the native-message coding self-cue runner."""

import copy
import importlib.util
import io
import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.error import URLError

import pytest

from scripts import coding_self_cue_run as runner
from scripts import coding_worker_dev as cpu
from tools import run_maintenance_dev as launcher

ROOT = Path(__file__).resolve().parents[1]


def _cpu_fixture_document():
    path = ROOT / "tests/test_coding_worker_dev.py"
    spec = importlib.util.spec_from_file_location("_coding_cpu_test_fixture", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.document()


def _bank():
    base = _cpu_fixture_document()
    documents = []
    for index in range(4):
        document = copy.deepcopy(base)
        episode = document["episode"]
        episode["episode_id"] = f"episode-{index}"
        for round_index, round_ in enumerate(episode["rounds"]):
            round_["manual_recap"] = f"M-ONLY-{index}-{round_index}"
            for rule in round_["oracle"]["effective_rules"]:
                rule["text"] += f" ORACLE-SECRET-{index}-{round_index}"
        episode["rounds"][1]["source_messages"].append(
            {
                "message_id": "assistant-natural-1",
                "role": "assistant",
                "text": "Prior natural assistant context.",
            }
        )
        documents.append(document)
    cpu.validate_bank(documents)
    return documents


def _write_bank(tmp_path, documents=None):
    path = tmp_path / "bank.json"
    path.write_text(json.dumps(documents or _bank()), encoding="utf-8")
    return path


def _check_results(module_text, checks):
    passed = "return 999" not in module_text
    return [
        {
            "check_id": check["check_id"],
            "symbol": check["symbol"],
            "rule_ids": list(check["rule_ids"]),
            "passed": passed,
            "actual": check["expected_values"][0] if passed else 999,
            "expected_values": check["expected_values"],
            "error": None,
            "elapsed_seconds": 0.0,
        }
        for check in checks
    ]


class ScriptedDecoder:
    max_tokens = runner.MAX_OUTPUT_TOKENS

    def __init__(self, documents, *, first_wrong=False):
        self.documents = documents
        self.first_wrong = first_wrong
        self.calls = []
        self.last_http = None
        self.deadline = None

    def set_deadline(self, deadline):
        self.deadline = deadline

    def payload(self, messages):
        return {"model": "fake", "messages": copy.deepcopy(messages)}

    def __call__(self, messages):
        call_index = len(self.calls)
        episode_index, offset = divmod(call_index, 18)
        round_index, arm_index = divmod(offset, 3)
        arm = runner.ARMS[arm_index]
        round_ = self.documents[episode_index]["episode"]["rounds"][round_index]
        patch = round_["reference_patch"]
        if self.first_wrong and call_index == 0:
            patch = "def alpha(x):\n    return 999\n"
        prefix = f"{arm}-PREFIX-{episode_index}-{round_index}\n"
        output = cpu.fenced_response(round_["target"]["path"], patch, prefix)
        self.calls.append(copy.deepcopy(messages))
        response = json.dumps(
            {
                "choices": [
                    {
                        "message": {"role": "assistant", "content": output},
                        "finish_reason": "stop",
                    }
                ]
            }
        )
        self.last_http = {
            "request": {"json": self.payload(messages)},
            "response": {"body": response},
            "finish_reason": "stop",
            "raw_output": output,
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
            "error": None,
        }
        return output


class MemoryResponse(io.BytesIO):
    status = 200
    headers = {"Content-Type": "application/json"}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()


def _native_body(content, finish_reason="stop", usage="valid"):
    body = {
        "choices": [
            {
                "message": {"role": "assistant", "content": content},
                "finish_reason": finish_reason,
            }
        ]
    }
    if usage != "missing":
        body["usage"] = (
            {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5}
            if usage == "valid"
            else usage
        )
    return json.dumps(body).encode()


def test_full_schedule_keeps_actual_own_state_and_discards_ephemeral_cues(tmp_path):
    documents = _bank()
    decoder = ScriptedDecoder(documents, first_wrong=True)
    result = runner.run(
        [_write_bank(tmp_path, documents)],
        tmp_path / "run",
        decoder,
        deadline_seconds=100,
        token_counter=lambda messages: len(json.dumps(messages)),
        check_runner=_check_results,
    )

    assert result["status"] == "COMPLETE"
    assert result["recorded_calls"] == result["completed_check_sets"] == 72
    assert result["network_attempts"] == 72
    assert len(decoder.calls) == 72
    assert "return 999" in decoder.calls[3][-1]["content"]
    assert "return 999" not in decoder.calls[1][-1]["content"]
    assert "return 999" not in decoder.calls[2][-1]["content"]
    assert "C-PREFIX-0-0" not in json.dumps(decoder.calls[4])
    assert "M-ONLY-0-0" not in json.dumps(decoder.calls[5])
    assert "M-ONLY-0-1" in decoder.calls[5][-1]["content"]
    assert all("ORACLE-SECRET" not in json.dumps(call) for call in decoder.calls)
    assert any(
        message == {"role": "assistant", "content": "Prior natural assistant context."}
        for message in decoder.calls[3]
    )

    turn0 = json.loads((tmp_path / "run/turns/turn-0000.json").read_text())
    turn3 = json.loads((tmp_path / "run/turns/turn-0003.json").read_text())
    assert turn0["submission_valid"] is True
    assert turn0["all_checks_passed"] is False
    assert turn0["post_module"].count("return 999") == 1
    assert turn0["canonical_history_after"][-1] == {
        "role": "assistant",
        "content": turn0["extracted_fence"],
    }
    assert "H-PREFIX-0-0" not in json.dumps(turn0["canonical_history_after"])
    assert {item["check_id"] for item in turn3["checks"]} == {
        "initial-helper",
        "functional-0-a",
        "functional-0-b",
        "functional-1-a",
        "functional-1-b",
        "obligation-1-a",
        "obligation-1-b",
    }
    assert all(item["episode_id"] == "episode-0" for item in turn3["checks"])
    assert (tmp_path / "run/workspaces/episode-0/H/round-0.py").read_text() == (
        turn0["post_module"]
    )


def test_native_decoder_preserves_exact_wire_messages_and_length_failure():
    opened = []

    def opener(request, timeout):
        opened.append((request, timeout))
        return MemoryResponse(_native_body("raw capped text", "length"))

    decoder = runner.NativeChatDecoder("127.0.0.1:9", "/model", opener=opener)
    messages = [
        {"role": "system", "content": "system"},
        {"role": "assistant", "content": "prior"},
        {"role": "user", "content": "current"},
    ]
    with pytest.raises(runner.NativeDecodeError, match="output cap reached"):
        decoder(messages)

    request, timeout = opened[0]
    payload = json.loads(request.data)
    assert timeout == runner.REQUEST_TIMEOUT_SECONDS
    assert payload["messages"] == messages
    assert payload["max_tokens"] == 768
    assert payload["temperature"] == 0
    assert decoder.last_http["raw_output"] == "raw capped text"
    assert decoder.last_http["finish_reason"] == "length"
    assert decoder.last_http["response"]["body_base64"]
    assert decoder.last_http["error"].startswith("NativeDecodeError:")


@pytest.mark.parametrize(
    "usage",
    [
        "missing",
        {"prompt_tokens": "3", "completion_tokens": 2, "total_tokens": 5},
        {"prompt_tokens": True, "completion_tokens": 2, "total_tokens": 3},
        {"prompt_tokens": 3, "completion_tokens": -1, "total_tokens": 2},
        {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 6},
        {"prompt_tokens": 3, "completion_tokens": 769, "total_tokens": 772},
    ],
)
def test_native_decoder_rejects_missing_or_invalid_token_accounting(usage):
    def opener(_request, timeout):
        assert timeout > 0
        return MemoryResponse(_native_body("raw response", usage=usage))

    decoder = runner.NativeChatDecoder("127.0.0.1:9", "/model", opener=opener)
    with pytest.raises(runner.NativeDecodeError, match="invalid chat response"):
        decoder([{"role": "user", "content": "current"}])
    assert decoder.last_http["raw_output"] == "raw response"
    assert decoder.last_http["failure_kind"] == "token_accounting"


def test_call_receipt_is_pending_before_decoder_blocks_and_then_finalizes(tmp_path):
    path = tmp_path / "call.json"

    class InspectingDecoder:
        last_http = None

        def payload(self, messages):
            return {"messages": messages}

        def __call__(self, _messages):
            pending = json.loads(path.read_text())
            assert pending["status"] == "PENDING"
            assert pending["episode_id"] == "episode-2"
            assert pending["request_intent"]["messages"][0]["role"] == "user"
            raise runner.NativeDecodeError("transport stopped")

    _, error, receipt = runner._decoder_receipt(
        InspectingDecoder(),
        [{"role": "user", "content": "request"}],
        path,
        call_index=8,
        episode_id="episode-2",
        arm="M",
        round_index=1,
        prompt_tokens=12,
    )
    assert error == "NativeDecodeError: transport stopped"
    assert receipt["status"] == "ERROR"
    assert json.loads(path.read_text()) == receipt


def test_atomic_update_preserves_previous_record_on_serialization_failure(
    tmp_path, monkeypatch
):
    path = tmp_path / "turn.json"
    runner._write_json(path, {"state": "safe"})
    original = path.read_bytes()

    def fail_dump(*_args, **_kwargs):
        raise TypeError("synthetic serialization failure")

    monkeypatch.setattr(runner.json, "dump", fail_dump)
    with pytest.raises(TypeError, match="synthetic serialization failure"):
        runner._write_json(path, {"state": "new"})
    assert path.read_bytes() == original
    assert list(tmp_path.glob(".turn.json.*.tmp")) == []


def test_deadline_records_finished_check_and_explicit_unfinished_ids(tmp_path):
    documents = _bank()
    decoder = ScriptedDecoder(documents)
    current = [0.0]

    def clock():
        return current[0]

    def one_then_deadline(module_text, checks):
        result = _check_results(module_text, checks)
        current[0] = 5.0
        return result

    result = runner.run(
        [_write_bank(tmp_path, documents)],
        tmp_path / "partial",
        decoder,
        deadline_seconds=5,
        token_counter=lambda _messages: 1,
        check_runner=one_then_deadline,
        clock=clock,
    )

    assert result["status"] == "INCOMPLETE"
    assert result["recorded_calls"] == 1
    assert result["completed_check_sets"] == 0
    turn = json.loads((tmp_path / "partial/turns/turn-0000.json").read_text())
    assert turn["check_status"] == "INCOMPLETE_DEADLINE"
    assert [item["check_id"] for item in turn["checks"]] == ["initial-helper"]
    assert turn["unfinished_check_ids"] == [
        "functional-0-a",
        "functional-0-b",
        "obligation-0-a",
        "obligation-0-b",
    ]
    assert turn["pre_module"] and turn["post_module"]


def test_context_rejection_records_one_slot_without_network_or_state_change(tmp_path):
    documents = _bank()
    decoder = ScriptedDecoder(documents)
    result = runner.run(
        [_write_bank(tmp_path, documents)],
        tmp_path / "context",
        decoder,
        deadline_seconds=100,
        token_counter=lambda _messages: runner.CONTEXT_TOKENS,
        check_runner=_check_results,
    )

    assert result["status"] == "INCOMPLETE"
    assert result["recorded_calls"] == 1
    assert result["network_attempts"] == 0
    assert decoder.calls == []
    call = json.loads((tmp_path / "context/calls/call-0000.json").read_text())
    turn = json.loads((tmp_path / "context/turns/turn-0000.json").read_text())
    assert call["status"] == "ERROR"
    assert "ContextLimitError" in call["decoder_error"]
    assert call["failure_kind"] == "capacity"
    assert call["http"] is None
    assert turn["patch_applied"] is False
    assert turn["pre_module"] == turn["post_module"]
    assert turn["canonical_history_after"][-1]["role"] == "user"


def test_real_tokenizer_rejects_over_context_prompt_before_network(tmp_path):
    documents = _bank()
    documents[0]["episode"]["rounds"][0]["request"]["text"] = "token " * 40_000
    decoder = ScriptedDecoder(documents)
    result = runner.run(
        [_write_bank(tmp_path, documents)],
        tmp_path / "real-context",
        decoder,
        deadline_seconds=100,
        check_runner=_check_results,
    )

    assert result["status"] == "INCOMPLETE"
    assert result["recorded_calls"] == 1
    assert result["capacity_failures"] == 1
    assert decoder.calls == []
    call = json.loads((tmp_path / "real-context/calls/call-0000.json").read_text())
    assert call["local_prompt_tokens"] > runner.CONTEXT_TOKENS
    assert call["failure_kind"] == "capacity"


@pytest.mark.parametrize("failure", ["transport", "capacity", "token_accounting"])
def test_actual_native_failures_complete_accounting_but_not_technical_evidence(
    tmp_path, failure
):
    documents = _bank()

    def opener(_request, timeout):
        assert timeout > 0
        if failure == "transport":
            raise URLError("synthetic unreachable server")
        if failure == "token_accounting":
            return MemoryResponse(
                _native_body(
                    "raw response",
                    usage={
                        "prompt_tokens": 3,
                        "completion_tokens": 2,
                        "total_tokens": 6,
                    },
                )
            )
        return MemoryResponse(_native_body("raw capped text", "length"))

    decoder = runner.NativeChatDecoder("127.0.0.1:9", "/model", opener=opener)
    result = runner.run(
        [_write_bank(tmp_path, documents)],
        tmp_path / failure,
        decoder,
        deadline_seconds=100,
        token_counter=lambda _messages: 1,
        check_runner=_check_results,
    )

    assert result["status"] == "INCOMPLETE"
    assert result["accounting_complete"] is True
    assert result["recorded_calls"] == result["completed_check_sets"] == 72
    assert result["technically_complete_calls"] == 0
    assert result[f"{failure}_failures"] == 72
    assert failure.replace("_", "-") in result["reason"]
    call = json.loads((tmp_path / failure / "calls/call-0000.json").read_text())
    turn = json.loads((tmp_path / failure / "turns/turn-0000.json").read_text())
    assert call["failure_kind"] == failure
    assert turn["slot_accounting_complete"] is True
    assert turn["technical_complete"] is False
    assert turn["turn_success"] is False
    if failure == "capacity":
        assert call["raw_output"] == "raw capped text"
        assert call["http"]["finish_reason"] == "length"
    elif failure == "token_accounting":
        assert call["raw_output"] == "raw response"
        assert call["http"]["usage"]["total_tokens"] == 6


def test_preview_contains_only_twelve_actual_cold_prompts_and_hash_bindings(tmp_path):
    documents = _bank()
    result = runner.preview(
        [_write_bank(tmp_path, documents)],
        model="/fixed-model",
        token_counter=lambda messages: len(json.dumps(messages)),
    )

    assert result["model_calls"] == 0
    assert result["actual_cold_prompt_count"] == 12
    assert result["later_actual_prompts_known"] is False
    assert len(result["cold_prompts"]) == 12
    assert len(result["conservative_context_bounds"]) == 72
    actual_bounds = sum(
        row["actual_prompt"] for row in result["conservative_context_bounds"]
    )
    assert actual_bounds == 12
    assert {row["round_index"] for row in result["cold_prompts"]} == {0}
    assert set(result["code_sha256"]) == {
        "scripts/coding_self_cue_run.py",
        "scripts/coding_worker_dev.py",
        "src/stencil/focus/renderer.py",
        "src/stencil/focus/slab.py",
        "src/stencil/focus/slab_sandbox.py",
    }
    for row in result["cold_prompts"]:
        serialized = json.dumps(row["messages"])
        assert "ORACLE-SECRET" not in serialized
        if row["arm"] == "M":
            assert "M-ONLY" in row["messages"][-1]["content"]
        else:
            assert "M-ONLY" not in serialized


def test_absolute_cli_preview_works_without_pythonpath(tmp_path):
    input_path = _write_bank(tmp_path)
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/coding_self_cue_run.py"),
            "--input",
            str(input_path),
            "--preview",
        ],
        cwd=tmp_path,
        env=environment,
        text=True,
        capture_output=True,
        timeout=60,
        check=True,
    )
    preview = json.loads(result.stdout)
    assert preview["actual_cold_prompt_count"] == 12
    assert preview["model_calls"] == 0


def test_worker_rejects_non_four_bank_and_decoder_with_wrong_cap(tmp_path):
    one = _bank()[0]
    one_path = _write_bank(tmp_path, [one])
    with pytest.raises(ValueError, match="exactly four"):
        runner.run(
            [one_path],
            tmp_path / "one",
            ScriptedDecoder([one]),
            deadline_seconds=10,
            token_counter=lambda _messages: 1,
            check_runner=_check_results,
        )

    documents = _bank()
    decoder = ScriptedDecoder(documents)
    decoder.max_tokens = 767
    with pytest.raises(ValueError, match="max_tokens=768"):
        runner.run(
            [_write_bank(tmp_path, documents)],
            tmp_path / "wrong-cap",
            decoder,
            deadline_seconds=10,
            token_counter=lambda _messages: 1,
            check_runner=_check_results,
        )


def test_coding_launcher_plan_uses_registered_cap_budget_and_bindings(capsys):
    run_dir = launcher.ROOT / "results/quick-checks/coding-plan-test"
    assert launcher.main(["--run-dir", str(run_dir), "--mode", "coding"]) == 0
    plan = json.loads(capsys.readouterr().out)
    assert plan["mode"] == "coding"
    assert plan["gpu_held_ceiling_seconds"] == 3600
    assert plan["startup_ceiling_seconds"] == 600
    assert plan["cleanup_reserve_seconds"] == 60
    assert plan["max_tokens"] == 768
    assert plan["input"] == str(launcher.CODING_INPUT)
    assert plan["driver"].endswith("/scripts/coding_self_cue_run.py")
    assert plan["bound_files"] == list(launcher.CODING_BOUND_FILES)
    assert {
        "scripts/coding_self_cue_run.py",
        "scripts/coding_worker_dev.py",
        "src/stencil/focus/renderer.py",
        "src/stencil/focus/slab.py",
        "src/stencil/focus/slab_sandbox.py",
        "results/factorial-prep/current-trunk-hashes.json",
        "results/coding-self-cue/PROTOCOL.md",
        "results/coding-self-cue/kimi-dev-reviewed.json",
        "results/coding-self-cue/preview.json",
    } < set(plan["bound_files"])


def test_launcher_validates_exact_cold_preview_bank_and_source_snapshot(tmp_path):
    documents = _bank()
    input_path = _write_bank(tmp_path, documents)
    preview = runner.preview(
        [input_path],
        model="/model",
        token_counter=lambda messages: len(json.dumps(messages)),
    )
    preview_path = tmp_path / "preview.json"
    preview_path.write_text(json.dumps(preview), encoding="utf-8")

    receipt = launcher.validate_coding_artifacts(input_path, preview_path)
    assert receipt["episodes"] == 4
    assert receipt["scheduled_calls"] == 72
    assert receipt["actual_cold_prompts"] == 12
    assert receipt["bank_sha256"] == cpu.sha256_bytes(input_path.read_bytes())

    preview["conservative_context_bounds"][12]["actual_prompt"] = True
    preview_path.write_text(json.dumps(preview), encoding="utf-8")
    with pytest.raises(RuntimeError, match="mislabels later prompts"):
        launcher.validate_coding_artifacts(input_path, preview_path)


def test_launcher_rejects_preview_from_different_bank(tmp_path):
    documents = _bank()
    input_path = _write_bank(tmp_path, documents)
    preview = runner.preview(
        [input_path],
        model="/model",
        token_counter=lambda messages: len(json.dumps(messages)),
    )
    documents[0]["episode"]["project"] += " changed"
    input_path.write_text(json.dumps(documents), encoding="utf-8")
    preview_path = tmp_path / "preview.json"
    preview_path.write_text(json.dumps(preview), encoding="utf-8")

    with pytest.raises(RuntimeError, match="not bound to the reviewed bank"):
        launcher.validate_coding_artifacts(input_path, preview_path)


def test_launcher_rechecks_startup_ceiling_after_successful_health_response():
    times = iter([599.0, 601.0])

    def opener(_url, timeout):
        assert timeout == 2
        return MemoryResponse(b"")

    with pytest.raises(TimeoutError, match="startup exceeded"):
        launcher.wait_for_server(
            0.0,
            ceiling_seconds=600,
            clock=lambda: next(times),
            opener=opener,
            sleeper=lambda _seconds: None,
        )
