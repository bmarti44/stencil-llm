import hashlib
import json

import pytest
from test_source_replay_screen import project

from scripts import coding_competence_run as native
from scripts import source_replay_screen as driver
from stencil import source_replay as replay


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def binding(root, relative, value=None):
    path = root / relative
    if value is not None:
        if isinstance(value, bytes):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value)
        else:
            write_json(path, value)
    return {"path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def screen_input(tmp_path):
    projects = []
    for index in range(4):
        projects.append(
            binding(
                tmp_path,
                f"projects/p{index + 1}.json",
                project(f"replay-{index + 1:02d}"),
            )
        )
    source_review = binding(tmp_path, "reviews/source.md", b"accepted source review\n")
    evidence = {
        "manifest": {
            "schema_version": 1,
            "status": "COMPLETE",
            "technical_eligible": True,
            "model_calls": 2,
        },
        "lifecycle": {
            "schema_version": 1,
            "status": "DRIVER_EXITED",
            "cleaned": True,
            "elapsed_seconds": 400.0,
        },
        "terminal": {
            "schema_version": 1,
            "status": "ELIGIBLE",
            "technical_eligible": True,
            "whole_elapsed_seconds": 401.0,
        },
        "selector_call": {
            "index": 0,
            "status": "COMPLETE",
            "exchange": {"status": "COMPLETE", "render": {"elapsed_seconds": 0.01}},
        },
        "worker_call": {
            "index": 1,
            "status": "COMPLETE",
            "exchange": {"status": "COMPLETE", "render": {"elapsed_seconds": 0.02}},
        },
    }
    qualification = {
        role: binding(tmp_path, f"qualification/{role}.json", value)
        for role, value in evidence.items()
    }
    qualification["result_review"] = binding(
        tmp_path, "qualification/result-review.md", b"accepted result audit\n"
    )
    manifest = {
        "schema_version": 1,
        "kind": "source-replay-screen-input",
        "projects": projects,
        "source_review": source_review,
        "qualification": qualification,
    }
    input_path = tmp_path / "screen-input.json"
    write_json(input_path, manifest)
    tokenizer = tmp_path / "tokenizer.json"
    tokenizer.write_bytes(b"{}")
    tokenizer_identity = {
        "name": "synthetic-counter",
        "path": str(tokenizer),
        "sha256": hashlib.sha256(tokenizer.read_bytes()).hexdigest(),
    }
    return input_path, tokenizer_identity


def preflight(tmp_path):
    input_path, tokenizer_identity = screen_input(tmp_path)
    receipt = driver.preflight_inputs(
        input_path,
        token_counter=lambda text: len(text.encode("utf-8")) // 8,
        tokenizer_identity=tokenizer_identity,
        root=tmp_path,
    )
    write_json(input_path.with_name(driver.PREFLIGHT_FILENAME), receipt)
    return input_path, receipt


def test_cpu_preflight_uses_exact_consumers_and_preserves_full_records(tmp_path):
    input_path, receipt = preflight(tmp_path)
    assert receipt["status"] == "PASS"
    assert receipt["model_calls"] == 0
    assert len(receipt["projects"]) == 4
    assert sum(len(item["references"]) for item in receipt["projects"]) == 12
    assert all(
        reference["all_checks_passed"] and reference["generation_headroom"] >= 128
        for item in receipt["projects"]
        for reference in item["references"]
    )
    assert all(
        not item["mutant"]["designated_result"]["passed"]
        for item in receipt["projects"]
    )
    assert receipt["projection"]["C"] == 240
    assert receipt["projection"]["r"] == 0.02
    assert receipt["projection"]["projected_seconds"] <= 3000
    assert (
        receipt["input"]["sha256"]
        == hashlib.sha256(input_path.read_bytes()).hexdigest()
    )


class FakeClient:
    def __init__(self, kind, sources=None):
        self.kind = kind
        self.sources = sources or []
        self.deadlines = []
        self.calls = 0

    def set_deadline(self, value):
        self.deadlines.append(value)

    def payload(self, messages):
        encoded = json.dumps(messages)
        if self.kind == "selector":
            assert "current_module" not in encoded
            assert "private" not in encoded
            assert '"arm"' not in encoded
        return {"messages": messages, "kind": self.kind}

    def perform(self, body, persist):
        self.calls += 1
        exchange = {
            "status": "COMPLETE",
            "render": {"elapsed_seconds": 0.01},
            "completion": {"elapsed_seconds": 0.02},
            "usage": {"prompt_tokens": 10, "completion_tokens": 2, "total_tokens": 12},
        }
        persist(exchange)
        if self.kind == "selector":
            arguments = {"source_ids": self.sources[:1]}
            name = "select_source_ids"
        else:
            messages = json.loads(body)["messages"]
            envelope = json.loads(messages[-1]["content"].split("\n", 1)[1])
            symbol = envelope["target"]["symbol"]
            # The first H action is deliberately wrong; its state must reach H round 2.
            wrong = self.calls == 1
            suffix = " + 100" if wrong else ""
            arguments = {"source": f"def {symbol}(x):\n    return x{suffix}\n"}
            name = "replace_function"
        call_id = f"fake-{self.kind}-{self.calls}"
        assistant = {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": call_id,
                    "type": "function",
                    "function": {"name": name, "arguments": json.dumps(arguments)},
                }
            ],
        }
        return {
            "call_id": call_id,
            "arguments": arguments,
            "raw_arguments": json.dumps(arguments),
            "assistant_message": assistant,
            "usage": exchange["usage"],
        }


def test_runtime_precreates_schedule_isolates_arms_and_keeps_supplements_ephemeral(
    tmp_path,
):
    input_path, _ = preflight(tmp_path)
    selectors = []

    def selector_factory(eligible_ids):
        client = FakeClient("selector", eligible_ids)
        selectors.append(client)
        return client

    worker = FakeClient("worker")
    output = tmp_path / "run"
    manifest = driver.run_screen(
        input_path,
        output,
        selector_factory=selector_factory,
        worker_client=worker,
        deadline_seconds=60,
        root=tmp_path,
    )
    assert manifest["status"] == "COMPLETE"
    assert len(manifest["calls"]) == 48
    assert all(item["status"] == "COMPLETE" for item in manifest["calls"])
    assert len(selectors) == 12 and all(client.calls == 1 for client in selectors)
    h_round_two = next(
        item
        for item in manifest["rounds"]
        if item["project_index"] == 0
        and item["round_index"] == 2
        and item["arm"] == "H"
    )
    assert "return x + 100" in h_round_two["module_before"]
    s_round_one = next(
        item
        for item in manifest["rounds"]
        if item["project_index"] == 0
        and item["round_index"] == 1
        and item["arm"] == "S"
    )
    assert replay.EVIDENCE_INTRODUCTION in json.dumps(s_round_one["issued_messages"])
    state = manifest["states"]["replay-01:S"]
    assert replay.EVIDENCE_INTRODUCTION not in json.dumps(state["permanent_history"])
    assert "rationale" not in json.dumps(s_round_one["issued_messages"])
    assert "behavior" not in json.dumps(s_round_one["tool_message"])


class BrokenSelector(FakeClient):
    def perform(self, body, persist):
        raise native.TechnicalError("transport", "synthetic failure")


def test_native_failure_stops_without_retry_and_preserves_unattempted_slots(tmp_path):
    input_path, _ = preflight(tmp_path)
    manifest = driver.run_screen(
        input_path,
        tmp_path / "broken-run",
        selector_factory=lambda ids: BrokenSelector("selector", ids),
        worker_client=FakeClient("worker"),
        deadline_seconds=60,
        root=tmp_path,
    )
    assert manifest["status"] == "INCOMPLETE"
    assert sum(item["status"] == "ERROR" for item in manifest["calls"]) == 1
    assert any(item["status"] == "UNATTEMPTED" for item in manifest["calls"])
    assert manifest["technical_failure"]["kind"] == "transport"


def test_driver_help_smoke():
    with pytest.raises(SystemExit) as exc:
        driver.main(["--help"])
    assert exc.value.code == 0
