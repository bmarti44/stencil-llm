import copy
import hashlib
import http.server
import json
import multiprocessing
import threading
import time
from concurrent.futures import Future

import pytest
from test_source_replay_authoring import packets, scaffold_response

from tools import prepare_source_replay as prepare


class InlineExecutor:
    def __init__(self, **_kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def submit(self, function, *args, **kwargs):
        future = Future()
        try:
            future.set_result(function(*args, **kwargs))
        except Exception as exc:
            future.set_exception(exc)
        return future


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def freeze(tmp_path):
    subjects = {}
    for relative in prepare.REQUIRED_SUBJECTS:
        if relative == prepare.REVIEW_SNAPSHOT:
            continue
        source = prepare.ROOT / relative
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())
        subjects[relative] = hashlib.sha256(destination.read_bytes()).hexdigest()
    review_path = tmp_path / prepare.REVIEW_SNAPSHOT
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_text(
        "Round 2 implementation ACCEPT 96/100, zero high/critical.\n"
    )
    subjects[prepare.REVIEW_SNAPSHOT] = hashlib.sha256(
        review_path.read_bytes()
    ).hexdigest()
    value = {
        "schema_version": 1,
        "kind": "source-replay-staged-preparation-freeze",
        "status": "ACCEPTED",
        "endpoint": "http://127.0.0.1:11434/api/generate",
        "model": "kimi-k3:cloud",
        "stream": False,
        "think": True,
        "project_ids": [f"staged-{index:02d}" for index in range(1, 5)],
        "domains": list(prepare.DOMAINS),
        "request_deadline_seconds": 450,
        "whole_deadline_seconds": 2400,
        "max_requests": 16,
        "subjects": subjects,
        "code_review": {
            "path": prepare.REVIEW_SNAPSHOT,
            "sha256": subjects[prepare.REVIEW_SNAPSHOT],
            "round": 2,
            "score": 96,
            "disposition": "ACCEPT",
            "open_high": 0,
            "open_critical": 0,
        },
    }
    path = tmp_path / "freeze.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def envelope(content, thinking="private reasoning"):
    return json.dumps(
        {
            "model": "kimi-k3",
            "response": json.dumps(content, ensure_ascii=False),
            "thinking": thinking,
            "done": True,
            "done_reason": "stop",
            "prompt_eval_count": 10,
            "eval_count": 20,
        },
        ensure_ascii=False,
    ).encode("utf-8")


class FakeTransport:
    def __init__(self, *, fail_stage=None, clock=None, elapsed=1):
        self.fail_stage = fail_stage
        self.clock = clock
        self.elapsed = elapsed
        self.calls = []

    def __call__(self, url, body, timeout):
        payload = json.loads(body)
        prompt = payload["prompt"]
        project_index = next(
            index for index in range(1, 5) if f"staged-{index:02d}" in prompt
        )
        if "Author the complete public instruction schedule" in prompt:
            stage = 0
            content = scaffold_response()
        else:
            stage = int(prompt.split("Current round (integer): ", 1)[1].splitlines()[0])
            content = packets()[stage - 1]
        self.calls.append((project_index, stage, timeout, bytes(body)))
        if self.clock is not None:
            self.clock.now += self.elapsed
        if self.fail_stage == (project_index, stage):
            content = {"wrong": "shape"}
        return {
            "status": 200,
            "headers": {"content-type": "application/json"},
            "body": envelope(content),
        }


class LocalServer:
    def __init__(self, handler):
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def url(self):
        return f"http://127.0.0.1:{self.server.server_port}/api/generate"

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_args):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=1)


def test_default_dry_plan_has_all_slots_and_no_files_or_network(tmp_path, capsys):
    run = tmp_path / "does-not-exist"
    assert prepare.main(["--run-dir", str(run)]) == 0
    plan = json.loads(capsys.readouterr().out)
    assert len(plan["planned_slots"]) == 16
    assert not run.exists()
    assert plan["execute"] is False


def test_exact_freeze_rejects_changed_subject(tmp_path):
    freeze_path = freeze(tmp_path)
    result = prepare.validate_freeze(freeze_path, root=tmp_path)
    assert result["freeze"]["max_requests"] == 16
    changed = tmp_path / next(iter(prepare.REQUIRED_SUBJECTS))
    changed.write_text("changed\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="hash mismatch"):
        prepare.validate_freeze(freeze_path, root=tmp_path)


def test_four_barriers_write_raw_receipts_and_assemble_exact_projects(tmp_path):
    freeze_path = freeze(tmp_path)
    transport = FakeTransport()
    run = tmp_path / "run"
    terminal = prepare.run_preparation(
        run,
        freeze_path,
        root=tmp_path,
        transport=transport,
        executor_factory=InlineExecutor,
        register_pid=lambda: None,
    )
    assert terminal["status"] == "PREPARED_UNREVIEWED"
    assert len(transport.calls) == 16
    job = json.loads((run / "job.json").read_text())
    assert all(slot["status"] == "COMPLETE" for slot in job["planned_slots"])
    assert len(list(run.glob("projects/*/authored.json"))) == 4
    first = json.loads((run / "calls/call-0000.json").read_text())
    assert (run / first["request"]["raw_path"]).read_bytes() == transport.calls[0][3]
    assert (
        first["response"]["body_sha256"]
        == hashlib.sha256(
            (run / first["response"]["raw_path"]).read_bytes()
        ).hexdigest()
    )
    assert first["response"]["thinking_bytes"] > 0
    assert len(job["prepared_projects"]) == 4
    authored = run / job["prepared_projects"][0]["path"]
    assert (
        job["prepared_projects"][0]["sha256"]
        == hashlib.sha256(authored.read_bytes()).hexdigest()
    )


def test_envelope_requires_known_remote_name_and_normal_stop():
    content, thinking, counts = prepare._response_envelope(
        json.loads(envelope({"valid": True}))
    )
    assert json.loads(content) == {"valid": True}
    assert thinking == "private reasoning"
    assert counts == {"prompt_eval_count": 10, "eval_count": 20}
    bad = json.loads(envelope({"valid": True}))
    bad["done_reason"] = "length"
    with pytest.raises(prepare.PreparationFailure, match="incomplete"):
        prepare._response_envelope(bad)


def test_actual_transport_preserves_http_error_body_and_metadata(tmp_path, monkeypatch):
    response_body = b'{"error":"synthetic unavailable"}'

    class ErrorHandler(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            self.rfile.read(int(self.headers["content-length"]))
            self.send_response(503)
            self.send_header("Content-Type", "application/json")
            self.send_header("X-Synthetic", "preserved")
            self.end_headers()
            self.wfile.write(response_body)

        def log_message(self, *_args):
            pass

    run = tmp_path / "http-error"
    (run / "raw").mkdir(parents=True)
    with LocalServer(ErrorHandler) as server:
        monkeypatch.setattr(prepare, "ENDPOINT", server.url)
        with pytest.raises(prepare.PreparationFailure) as caught:
            prepare._perform_http(
                run,
                {"slot_index": 0},
                b"{}",
                time.monotonic() + 5,
                prepare._transport,
                time.monotonic,
            )
    assert caught.value.kind == "transport"
    receipt = caught.value.response
    assert receipt["status"] == 503
    assert receipt["headers"]["X-Synthetic"] == "preserved"
    assert (run / receipt["raw_path"]).read_bytes() == response_body


def test_actual_transport_has_absolute_deadline_and_cleans_owned_reader(
    tmp_path, monkeypatch
):
    complete_body = b"x" * 30

    class TrickleHandler(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            self.rfile.read(int(self.headers["content-length"]))
            self.send_response(200)
            self.send_header("Content-Length", str(len(complete_body)))
            self.end_headers()
            try:
                for byte in complete_body:
                    self.wfile.write(bytes([byte]))
                    self.wfile.flush()
                    time.sleep(0.04)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def log_message(self, *_args):
            pass

    run = tmp_path / "trickle"
    (run / "raw").mkdir(parents=True)
    before = {child.pid for child in multiprocessing.active_children()}
    with LocalServer(TrickleHandler) as server:
        monkeypatch.setattr(prepare, "ENDPOINT", server.url)
        started = time.monotonic()
        with prepare.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                prepare._perform_http,
                run,
                {"slot_index": 0},
                b"{}",
                started + 0.45,
                prepare._transport,
                time.monotonic,
            )
            with pytest.raises(prepare.PreparationFailure) as caught:
                future.result()
        elapsed = time.monotonic() - started
    assert caught.value.kind == "deadline"
    assert elapsed < 0.9
    receipt = caught.value.response
    partial = (run / receipt["raw_path"]).read_bytes()
    assert 0 < len(partial) < len(complete_body)
    assert receipt["response_complete"] is False
    assert {child.pid for child in multiprocessing.active_children()} == before


def test_spawn_start_failure_records_zero_transport_attempts(tmp_path, monkeypatch):
    def fail_start(_process):
        raise OSError("synthetic spawn failure")

    monkeypatch.setattr(multiprocessing.context.SpawnProcess, "start", fail_start)
    run = tmp_path / "run"
    terminal = prepare.run_preparation(
        run,
        freeze(tmp_path),
        root=tmp_path,
        transport=prepare._transport,
        executor_factory=InlineExecutor,
        register_pid=lambda: None,
    )
    assert terminal["status"] == "INCOMPLETE"
    job = json.loads((run / "job.json").read_text())
    assert sum(slot["attempts"] for slot in job["planned_slots"]) == 0
    assert all(slot["status"] == "ERROR" for slot in job["planned_slots"][:4])
    assert all(slot["status"] == "UNATTEMPTED" for slot in job["planned_slots"][4:])


def test_barrier_failure_has_no_retry_and_leaves_later_slots_unattempted(tmp_path):
    transport = FakeTransport(fail_stage=(2, 1))
    run = tmp_path / "run"
    terminal = prepare.run_preparation(
        run,
        freeze(tmp_path),
        root=tmp_path,
        transport=transport,
        executor_factory=InlineExecutor,
        register_pid=lambda: None,
    )
    assert terminal["status"] == "INELIGIBLE"
    assert len(transport.calls) == 8
    job = json.loads((run / "job.json").read_text())
    assert sum(slot["status"] == "UNATTEMPTED" for slot in job["planned_slots"]) == 8
    assert sum(slot["attempts"] for slot in job["planned_slots"]) == 8


def test_transport_failure_preserves_deliveries_and_counts_only_http_attempts(tmp_path):
    class FailedTransport(FakeTransport):
        def __call__(self, url, body, timeout):
            payload = json.loads(body)
            if "staged-02" in payload["prompt"]:
                self.calls.append((2, 0, timeout, bytes(body)))
                raise TimeoutError("synthetic transport failure")
            return super().__call__(url, body, timeout)

    transport = FailedTransport()
    run = tmp_path / "run"
    terminal = prepare.run_preparation(
        run,
        freeze(tmp_path),
        root=tmp_path,
        transport=transport,
        executor_factory=InlineExecutor,
        register_pid=lambda: None,
    )
    assert terminal["status"] == "INCOMPLETE"
    job = json.loads((run / "job.json").read_text())
    assert sum(slot["attempts"] for slot in job["planned_slots"]) == 4
    assert (
        sum(
            slot["status"] == "DELIVERED_UNVALIDATED"
            for slot in job["planned_slots"][:4]
        )
        == 3
    )
    assert all(slot["status"] == "UNATTEMPTED" for slot in job["planned_slots"][4:])


def test_request_preparation_failure_does_not_count_transport_attempt(
    tmp_path, monkeypatch
):
    original = prepare._prompt_for_stage

    def fail_second(stage, project_index, states, texts):
        if stage == 0 and project_index == 1:
            raise ValueError("synthetic prompt failure")
        return original(stage, project_index, states, texts)

    monkeypatch.setattr(prepare, "_prompt_for_stage", fail_second)
    transport = FakeTransport()
    run = tmp_path / "run"
    terminal = prepare.run_preparation(
        run,
        freeze(tmp_path),
        root=tmp_path,
        transport=transport,
        executor_factory=InlineExecutor,
        register_pid=lambda: None,
    )
    assert terminal["status"] == "INCOMPLETE"
    assert transport.calls == []
    job = json.loads((run / "job.json").read_text())
    assert sum(slot["attempts"] for slot in job["planned_slots"]) == 0
    assert all(slot["status"] == "UNATTEMPTED" for slot in job["planned_slots"])


def test_partial_case_evidence_is_incomplete_through_driver(tmp_path, monkeypatch):
    record = {
        "public_results": [{"check_id": "synthetic", "input": 1, "passed": True}],
        "private_results": [],
    }

    def interrupted(*_args, **_kwargs):
        raise prepare.authoring.StageExecutionInterrupted(
            "synthetic whole deadline", record
        )

    monkeypatch.setattr(prepare.authoring, "validate_and_apply_packet", interrupted)
    run = tmp_path / "run"
    terminal = prepare.run_preparation(
        run,
        freeze(tmp_path),
        root=tmp_path,
        transport=FakeTransport(),
        executor_factory=InlineExecutor,
        register_pid=lambda: None,
    )
    assert terminal["status"] == "INCOMPLETE"
    interrupted_call = json.loads((run / "calls/call-0004.json").read_text())
    assert interrupted_call["validation"] == record
    assert interrupted_call["error"]["kind"] == "deadline"


@pytest.mark.parametrize("behavior", [[], {}])
def test_malformed_behavior_is_ineligible_through_driver(tmp_path, behavior):
    class MalformedTransport(FakeTransport):
        def __call__(self, url, body, timeout):
            raw = super().__call__(url, body, timeout)
            prompt = json.loads(body)["prompt"]
            if "Current round (integer): 1" in prompt:
                packet = copy.deepcopy(packets()[0])
                packet["private_checks"][0]["behavior"] = behavior
                raw["body"] = envelope(packet)
            return raw

    transport = MalformedTransport()
    run = tmp_path / "run"
    terminal = prepare.run_preparation(
        run,
        freeze(tmp_path),
        root=tmp_path,
        transport=transport,
        executor_factory=InlineExecutor,
        register_pid=lambda: None,
    )
    assert terminal["status"] == "INELIGIBLE"
    assert len(transport.calls) == 8
    job = json.loads((run / "job.json").read_text())
    assert job["status"] == "INELIGIBLE"
    assert sum(slot["attempts"] for slot in job["planned_slots"]) == 8
    assert all(slot["status"] == "UNATTEMPTED" for slot in job["planned_slots"][8:])
    assert (run / "terminal.json").is_file()


def test_unexpected_local_validation_exception_is_incomplete(tmp_path, monkeypatch):
    def broken_validator(*_args, **_kwargs):
        raise RuntimeError("synthetic validator defect")

    monkeypatch.setattr(
        prepare.authoring, "validate_and_apply_packet", broken_validator
    )
    transport = FakeTransport()
    run = tmp_path / "run"
    terminal = prepare.run_preparation(
        run,
        freeze(tmp_path),
        root=tmp_path,
        transport=transport,
        executor_factory=InlineExecutor,
        register_pid=lambda: None,
    )
    assert terminal["status"] == "INCOMPLETE"
    assert len(transport.calls) == 8
    record = json.loads((run / "calls/call-0004.json").read_text())
    assert record["error"]["kind"] == "local_validation"


def test_shared_deadline_and_late_positive_publication_are_incomplete(tmp_path):
    clock = Clock()
    transport = FakeTransport(clock=clock)
    terminal = prepare.run_preparation(
        tmp_path / "run",
        freeze(tmp_path),
        root=tmp_path,
        transport=transport,
        executor_factory=InlineExecutor,
        clock=clock,
        register_pid=lambda: None,
        whole_deadline_seconds=5,
    )
    assert terminal["status"] == "INCOMPLETE"
    assert transport.calls
    assert transport.calls[0][2] == 5
    assert all(timeout <= 5 for _, _, timeout, _ in transport.calls)

    clock = Clock()
    transport = FakeTransport(clock=clock, elapsed=451)
    run = tmp_path / "late-call"
    terminal = prepare.run_preparation(
        run,
        freeze(tmp_path / "late-freeze"),
        root=tmp_path / "late-freeze",
        transport=transport,
        executor_factory=InlineExecutor,
        clock=clock,
        register_pid=lambda: None,
    )
    assert terminal["status"] == "INCOMPLETE"
    call = json.loads((run / "calls/call-0000.json").read_text())
    assert call["response"]["elapsed_seconds"] == 451
    assert (run / call["response"]["raw_path"]).is_file()

    clock = Clock()
    clock.now = 2399
    writes = []

    def writer(path, value):
        writes.append(json.loads(json.dumps(value)))
        if value["status"] == "PREPARED_UNREVIEWED":
            clock.now = 2400.01

    result = prepare.publish_terminal(
        tmp_path / "terminal.json",
        {
            "status": "PREPARED_UNREVIEWED",
            "reason": "synthetic complete preparation",
            "terminal_stage": 3,
        },
        0,
        2400,
        clock=clock,
        writer=writer,
    )
    assert result["status"] == "INCOMPLETE"
    assert "publication" in result["reason"]
    assert writes[-1]["status"] == "INCOMPLETE"


def test_import_and_help_have_no_side_effects(tmp_path):
    before = set(tmp_path.iterdir())
    with pytest.raises(SystemExit) as exc:
        prepare.main(["--help"])
    assert exc.value.code == 0
    assert set(tmp_path.iterdir()) == before
