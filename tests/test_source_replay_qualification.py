import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import coding_competence_run as native
from scripts import source_replay_qualification as qualification


def _fixture():
    return {
        "schema_version": 1,
        "author": "kimi-k3:cloud",
        "lineage": "fresh independent mechanical qualification fixture",
        "initial_file": {
            "path": "module.py",
            "text": "def change(x):\n    return None\n",
        },
        "source_messages": [
            {"message_id": "m01", "role": "user", "text": "Add one to x."}
        ],
        "request": {
            "message_id": "m02",
            "role": "user",
            "text": "Implement change(x) now.",
        },
        "target": {"path": "module.py", "symbol": "change"},
        "reference_patch": "def change(x):\n    return x + 1\n",
        "checks": [
            {"check_id": "c1", "symbol": "change", "input": 1, "expected_values": [2]},
            {"check_id": "c2", "symbol": "change", "input": -1, "expected_values": [0]},
        ],
    }


class FakeClient:
    def __init__(self, result=None, error=None, *, clock=None, advance=0):
        self.result = result
        self.error = error
        self.clock = clock
        self.advance = advance
        self.payloads = []
        self.deadlines = []
        self.calls = 0

    def set_deadline(self, value):
        self.deadlines.append(value)

    def payload(self, messages):
        self.payloads.append(copy.deepcopy(messages))
        return {"messages": messages}

    def perform(self, request_body, persist):
        self.calls += 1
        exchange = {
            "status": "ERROR" if self.error else "COMPLETE",
            "request_body_sha256": qualification._sha_bytes(request_body),
            "render": {"elapsed_seconds": 0.1},
            "completion": {"elapsed_seconds": 0.2},
            "usage": None if self.error else self.result.get("usage"),
        }
        persist(exchange)
        if self.clock is not None:
            self.clock.now += self.advance
        if self.error:
            raise self.error
        return copy.deepcopy(self.result)


def _selector(ids=("m01",)):
    return FakeClient(
        {
            "call_id": "select-1",
            "arguments": {"source_ids": list(ids)},
            "raw_arguments": json.dumps({"source_ids": list(ids)}),
            "assistant_message": {"role": "assistant", "content": ""},
            "usage": {"prompt_tokens": 10, "completion_tokens": 2, "total_tokens": 12},
        }
    )


def _worker(source="def change(x):\n    return x + 1\n"):
    return FakeClient(
        {
            "call_id": "worker-1",
            "arguments": {"source": source},
            "raw_arguments": json.dumps({"source": source}),
            "assistant_message": {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "worker-1",
                        "type": "function",
                        "function": {
                            "name": "replace_function",
                            "arguments": json.dumps({"source": source}),
                        },
                    }
                ],
            },
            "usage": {"prompt_tokens": 30, "completion_tokens": 8, "total_tokens": 38},
        }
    )


def _write_fixture(tmp_path):
    path = tmp_path / "fixture.json"
    path.write_text(json.dumps(_fixture()), encoding="utf-8")
    tokenizer_path = tmp_path / "tokenizer.json"
    tokenizer_path.write_text("{}\n", encoding="utf-8")
    identity = {
        "name": "test-tokenizer",
        "path": str(tokenizer_path),
        "sha256": qualification._sha_bytes(tokenizer_path.read_bytes()),
    }
    preflight = qualification.preflight_fixture(
        path, lambda text: len(text.encode("utf-8")), identity
    )
    (tmp_path / qualification.PREFLIGHT_FILENAME).write_text(
        json.dumps(preflight), encoding="utf-8"
    )
    return path


def test_preflight_uses_exact_native_argument_serialization_and_actual_consumer(
    tmp_path,
):
    _write_fixture(tmp_path)
    receipt = json.loads(
        (tmp_path / qualification.PREFLIGHT_FILENAME).read_text(encoding="utf-8")
    )
    expected = native._json_bytes({"source": _fixture()["reference_patch"]})

    assert receipt["status"] == "PASS"
    assert receipt["model_calls"] == 0
    assert receipt["reference_action"]["argument_body"] == expected.decode("utf-8")
    assert receipt["reference_action"]["argument_body_bytes"] == len(expected)
    assert receipt["reference_action"]["argument_tokens"] == len(expected)
    assert receipt["reference_action"]["response_tokens_with_eos"] == len(expected) + 1
    assert receipt["all_reference_checks_passed"] is True


def test_two_call_qualification_keeps_private_fixture_data_out_of_prompts(tmp_path):
    path = _write_fixture(tmp_path)
    selector = _selector()
    worker = _worker()

    result = qualification.run_qualification(
        path, tmp_path / "out", selector, worker, deadline_seconds=600
    )

    assert result["status"] == "COMPLETE"
    assert result["technical_eligible"] is True
    assert result["behavior_passed"] is True
    assert selector.calls == worker.calls == 1
    selector_text = json.dumps(selector.payloads, ensure_ascii=False)
    worker_text = json.dumps(worker.payloads, ensure_ascii=False)
    fixture = _fixture()
    assert fixture["reference_patch"] not in selector_text + worker_text
    assert "expected_values" not in selector_text + worker_text
    assert "Add one to x." in selector_text + worker_text
    assert worker.payloads[0][-2]["content"].startswith(
        qualification.replay.EVIDENCE_INTRODUCTION
    )
    assert worker.payloads[0][-1]["content"].startswith(
        qualification.replay.WORK_ENVELOPE_INTRODUCTION
    )
    permanent_text = json.dumps(result["permanent_history"], ensure_ascii=False)
    assert qualification.replay.EVIDENCE_INTRODUCTION not in permanent_text
    assert "Add one to x." in permanent_text
    assert max(selector.deadlines + worker.deadlines) <= result["deadline_monotonic"]
    assert len(list((tmp_path / "out" / "calls").glob("call-*.json"))) == 2


def test_wrong_applied_behavior_is_not_a_technical_failure(tmp_path):
    result = qualification.run_qualification(
        _write_fixture(tmp_path),
        tmp_path / "out",
        _selector([]),
        _worker("def change(x):\n    return x\n"),
    )

    assert result["status"] == "COMPLETE"
    assert result["technical_eligible"] is True
    assert result["behavior_passed"] is False
    assert result["selected_source_ids"] == []
    assert result["evidence_message"]["content"].endswith("\n[]")


def test_action_consumer_rejection_is_a_completed_no_go_not_transport(tmp_path):
    result = qualification.run_qualification(
        _write_fixture(tmp_path),
        tmp_path / "out",
        _selector(),
        _worker("def wrong(x):\n    return x\n"),
    )

    assert result["status"] == "COMPLETE_NO_GO"
    assert result["technical_eligible"] is False
    assert result["technical_failure"] is None
    assert result["consumer_failure"]["kind"] == "action_rejected"
    call = json.loads((tmp_path / "out/calls/call-0001.json").read_text())
    assert call["status"] == "COMPLETE"
    assert call["consumer"]["status"] == "REJECTED"


def test_selector_failure_is_durable_and_worker_remains_unattempted(tmp_path):
    selector = FakeClient(error=native.TechnicalError("transport", "offline"))
    worker = _worker()

    result = qualification.run_qualification(
        _write_fixture(tmp_path), tmp_path / "out", selector, worker
    )

    assert result["status"] == "INCOMPLETE"
    assert result["technical_failure"]["kind"] == "transport"
    assert worker.calls == 0
    second = json.loads((tmp_path / "out" / "calls" / "call-0001.json").read_text())
    assert second["status"] == "UNATTEMPTED"


def test_qualification_refuses_nonempty_output_without_model_calls(tmp_path):
    output = tmp_path / "out"
    output.mkdir()
    (output / "existing").write_text("preserve", encoding="utf-8")
    selector = _selector()
    worker = _worker()

    with pytest.raises(FileExistsError, match="nonempty"):
        qualification.run_qualification(
            _write_fixture(tmp_path), output, selector, worker
        )

    assert selector.calls == worker.calls == 0


def test_each_native_pair_has_one_shared_deadline_capped_at_now_plus_181(tmp_path):
    class Clock:
        now = 10.0

        def __call__(self):
            return self.now

    clock = Clock()
    selector = _selector()
    worker = _worker()
    selector.clock = worker.clock = clock
    selector.advance = 25.0
    worker.advance = 30.0

    result = qualification.run_qualification(
        _write_fixture(tmp_path),
        tmp_path / "out",
        selector,
        worker,
        deadline_seconds=600,
        clock=clock,
    )

    assert selector.deadlines == [191.0]
    assert worker.deadlines == [216.0]
    assert result["ended_monotonic"] == 65.0


def test_late_worker_return_cannot_be_published_as_technically_eligible(tmp_path):
    class Clock:
        now = 10.0

        def __call__(self):
            return self.now

    clock = Clock()
    selector = _selector()
    worker = _worker()
    selector.clock = worker.clock = clock
    selector.advance = 20.0
    worker.advance = 181.01

    result = qualification.run_qualification(
        _write_fixture(tmp_path),
        tmp_path / "out",
        selector,
        worker,
        deadline_seconds=600,
        clock=clock,
    )

    assert result["status"] == "INCOMPLETE"
    assert result["technical_eligible"] is False
    assert result["technical_failure"]["kind"] == "deadline"


def test_late_call_receipt_is_rewritten_as_error(tmp_path, monkeypatch):
    class Clock:
        now = 10.0

        def __call__(self):
            return self.now

    clock = Clock()
    original = qualification.native._write_json

    def delayed_write(path, value, **kwargs):
        original(path, value, **kwargs)
        if Path(path).name == "call-0001.json" and value.get("status") == "COMPLETE":
            clock.now = 192.0

    monkeypatch.setattr(qualification.native, "_write_json", delayed_write)
    result = qualification.run_qualification(
        _write_fixture(tmp_path),
        tmp_path / "out",
        _selector(),
        _worker(),
        clock=clock,
    )

    assert result["status"] == "INCOMPLETE"
    call = json.loads((tmp_path / "out/calls/call-0001.json").read_text())
    assert call["status"] == "ERROR"
    assert call["error"]["kind"] == "deadline"


def test_late_final_manifest_publication_is_downgraded(tmp_path, monkeypatch):
    class Clock:
        now = 10.0

        def __call__(self):
            return self.now

    clock = Clock()
    original = qualification.native._write_json

    def delayed_write(path, value, **kwargs):
        original(path, value, **kwargs)
        if Path(path).name == "manifest.json" and value.get("status") == "COMPLETE":
            clock.now = 611.0

    monkeypatch.setattr(qualification.native, "_write_json", delayed_write)
    result = qualification.run_qualification(
        _write_fixture(tmp_path),
        tmp_path / "out",
        _selector(),
        _worker(),
        deadline_seconds=600,
        clock=clock,
    )

    assert result["status"] == "INCOMPLETE"
    manifest = json.loads((tmp_path / "out/manifest.json").read_text())
    assert manifest["technical_eligible"] is False
    assert manifest["technical_failure"]["kind"] == "deadline"


@pytest.mark.parametrize(
    "field,value,error",
    [
        ("schema_version", True, "schema_version"),
        ("lineage", "", "lineage"),
        ("author", "other", "author"),
        ("source_messages", [], "exactly one"),
        (
            "initial_file",
            {"path": "module.py", "text": "def change(x: int):\n    return None\n"},
            "annotations",
        ),
    ],
)
def test_fixture_structure_fails_closed(field, value, error):
    fixture = _fixture()
    fixture[field] = value

    with pytest.raises(ValueError, match=error):
        qualification.validate_fixture(fixture)


def test_direct_help_works_outside_repository(tmp_path):
    script = Path(qualification.__file__).resolve()
    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "--preflight-output" in result.stdout
    assert "--deadline-seconds" in result.stdout
