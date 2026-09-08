#!/usr/bin/env python3
"""Prepare four staged Kimi source-replay projects; dry-run by default."""

import argparse
import copy
import hashlib
import json
import math
import multiprocessing
import os
import sys
import tempfile
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from stencil import source_replay_authoring as authoring  # noqa: E402

RESULTS = ROOT / "results/source-replay-staged"
DEFAULT_FREEZE = RESULTS / "preparation-freeze.json"
SCAFFOLD_PROMPT = "results/source-replay-staged/scaffold-prompt.txt"
ROUND_PROMPT = "results/source-replay-staged/round-prompt.txt"
DATA_CONTRACT = "results/source-replay/DATA-CONTRACT.md"
REVIEW_SNAPSHOT = (
    "results/source-replay-staged/preparation-code-review-at-acceptance.md"
)
ENDPOINT = "http://127.0.0.1:11434/api/generate"
MODEL = "kimi-k3:cloud"
RESPONSE_MODEL = "kimi-k3"
PROJECT_IDS = tuple(f"staged-{index:02d}" for index in range(1, 5))
DOMAINS = (
    "inventory transformations",
    "scheduling records",
    "document metadata processing",
    "sensor-event summarization",
)
REQUEST_DEADLINE_SECONDS = 450
WHOLE_DEADLINE_SECONDS = 2400
MAX_REQUESTS = 16
MAX_FILE_BYTES = 10_000_000
TRANSPORT_CLEANUP_SECONDS = 0.25
TRANSPORT_CHUNK_BYTES = 65_536
STATIC_SUBJECTS = {
    "results/source-replay-staged/PREPARATION.md",
    SCAFFOLD_PROMPT,
    ROUND_PROMPT,
    "results/source-replay/SPEC.md",
    DATA_CONTRACT,
    "src/stencil/source_replay_authoring.py",
    "tools/prepare_source_replay.py",
    "tests/test_source_replay_authoring.py",
    "tests/test_prepare_source_replay.py",
    "src/stencil/source_replay_screen.py",
    "src/stencil/source_replay.py",
    "scripts/coding_competence_dev.py",
    "scripts/coding_worker_dev.py",
    "src/stencil/focus/slab.py",
    "src/stencil/focus/slab_sandbox.py",
    "src/stencil/focus/renderer.py",
}
REQUIRED_SUBJECTS = {*STATIC_SUBJECTS, REVIEW_SNAPSHOT}
FREEZE_FIELDS = {
    "schema_version",
    "kind",
    "status",
    "endpoint",
    "model",
    "stream",
    "think",
    "project_ids",
    "domains",
    "request_deadline_seconds",
    "whole_deadline_seconds",
    "max_requests",
    "subjects",
    "code_review",
}
REVIEW_FIELDS = {
    "path",
    "sha256",
    "round",
    "score",
    "disposition",
    "open_high",
    "open_critical",
}


class PreparationFailure(RuntimeError):
    def __init__(self, kind, message, *, response=None, attempted=False):
        super().__init__(message)
        self.kind = kind
        self.response = copy.deepcopy(response)
        self.attempted = attempted


class _SupervisedTransportError(RuntimeError):
    def __init__(self, message, *, raw=None, attempted=False, deadline=False):
        super().__init__(message)
        self.raw = copy.deepcopy(raw)
        self.attempted = attempted
        self.deadline = deadline


def _sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def _bound_path(root, relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise RuntimeError("freeze subjects must be repository-relative paths")
    root = Path(root).resolve()
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise RuntimeError("freeze subject escapes the repository") from exc
    return path


def _read_json(path, label):
    try:
        return authoring.parse_author_json(Path(path).read_bytes())
    except ValueError as exc:
        raise RuntimeError(f"{label} is invalid: {exc}") from exc


def _valid_hash(value):
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def validate_freeze(path, *, root=ROOT):
    """Validate exact immutable subjects and root-recorded review evidence."""
    root = Path(root).resolve()
    freeze = _read_json(path, "preparation freeze")
    if set(freeze) != FREEZE_FIELDS:
        raise RuntimeError("preparation freeze has the wrong fields")
    if (
        type(freeze["schema_version"]) is not int
        or freeze["schema_version"] != 1
        or freeze["kind"] != "source-replay-staged-preparation-freeze"
        or freeze["status"] != "ACCEPTED"
        or freeze["endpoint"] != ENDPOINT
        or freeze["model"] != MODEL
        or freeze["stream"] is not False
        or freeze["think"] is not True
        or freeze["project_ids"] != list(PROJECT_IDS)
        or freeze["domains"] != list(DOMAINS)
        or type(freeze["request_deadline_seconds"]) is not int
        or freeze["request_deadline_seconds"] != REQUEST_DEADLINE_SECONDS
        or type(freeze["whole_deadline_seconds"]) is not int
        or freeze["whole_deadline_seconds"] != WHOLE_DEADLINE_SECONDS
        or type(freeze["max_requests"]) is not int
        or freeze["max_requests"] != MAX_REQUESTS
    ):
        raise RuntimeError("preparation freeze settings differ from registration")
    subjects = freeze["subjects"]
    if type(subjects) is not dict or set(subjects) != REQUIRED_SUBJECTS:
        raise RuntimeError("freeze does not bind the exact required subject set")
    for relative, digest in subjects.items():
        file_path = _bound_path(root, relative)
        if not file_path.is_file() or not _valid_hash(digest):
            raise RuntimeError(f"freeze subject is missing or invalid: {relative}")
        if _sha_bytes(file_path.read_bytes()) != digest:
            raise RuntimeError(f"freeze subject hash mismatch: {relative}")
    review = freeze["code_review"]
    if type(review) is not dict or set(review) != REVIEW_FIELDS:
        raise RuntimeError("code_review receipt has the wrong fields")
    if (
        review["path"] != REVIEW_SNAPSHOT
        or review["sha256"] != subjects[REVIEW_SNAPSHOT]
        or type(review["round"]) is not int
        or review["round"] < 2
        or type(review["score"]) is not int
        or not 90 <= review["score"] <= 100
        or review["disposition"] != "ACCEPT"
        or type(review["open_high"]) is not int
        or review["open_high"] != 0
        or type(review["open_critical"]) is not int
        or review["open_critical"] != 0
    ):
        raise RuntimeError("code_review receipt is not an accepted current snapshot")
    return {
        "freeze": freeze,
        "freeze_sha256": _sha_bytes(Path(path).read_bytes()),
        "root": root,
    }


def planned_slots():
    return [
        {
            "slot_index": stage * 4 + project_index,
            "project_index": project_index,
            "project_id": project_id,
            "stage": stage,
            "status": "UNATTEMPTED",
            "attempts": 0,
        }
        for stage in range(4)
        for project_index, project_id in enumerate(PROJECT_IDS)
    ]


def dry_plan(run_dir, freeze_path=DEFAULT_FREEZE, *, root=ROOT):
    root = Path(root).resolve()
    return {
        "schema_version": 1,
        "kind": "source-replay-staged-preparation-plan",
        "execute": False,
        "run_dir": str(Path(run_dir)),
        "freeze": str(Path(freeze_path)),
        "freeze_status": "present" if Path(freeze_path).is_file() else "missing",
        "endpoint": ENDPOINT,
        "model": MODEL,
        "stream": False,
        "think": True,
        "request_deadline_seconds": REQUEST_DEADLINE_SECONDS,
        "whole_deadline_seconds": WHOLE_DEADLINE_SECONDS,
        "max_requests": MAX_REQUESTS,
        "planned_slots": planned_slots(),
        "required_subjects": {
            relative: _sha_bytes((root / relative).read_bytes())
            if (root / relative).is_file()
            else None
            for relative in sorted(REQUIRED_SUBJECTS)
        },
    }


def _write_bytes(path, value, *, exclusive=False):
    value = bytes(value)
    if len(value) >= MAX_FILE_BYTES:
        raise PreparationFailure("artifact_size", "artifact exceeds repository limit")
    path = Path(path)
    if exclusive:
        with path.open("xb") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        return
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            "wb", dir=path.parent, prefix=f".{path.name}.", delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _write_json(path, value, *, exclusive=False):
    body = (
        json.dumps(value, ensure_ascii=True, allow_nan=False, indent=2, sort_keys=True)
        + "\n"
    ).encode("utf-8")
    _write_bytes(path, body, exclusive=exclusive)


def _register_pid(path=ROOT / ".stencil-owned-pids"):
    with Path(path).open("a", encoding="utf-8") as handle:
        handle.write(f"{os.getpid()}\n")
        handle.flush()
        os.fsync(handle.fileno())


def _transport_child(connection, url, body, socket_timeout):
    """Stream one urllib response to its supervising parent process."""
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        try:
            response = urllib.request.urlopen(request, timeout=socket_timeout)
        except urllib.error.HTTPError as exc:
            response = exc
        with response:
            status = getattr(response, "status", None)
            if status is None:
                status = response.code
            connection.send(("metadata", int(status), dict(response.headers.items())))
            reader = getattr(response, "read1", response.read)
            while True:
                chunk = reader(TRANSPORT_CHUNK_BYTES)
                if not chunk:
                    break
                connection.send(("body", bytes(chunk)))
            connection.send(("complete",))
    except BaseException as exc:
        try:
            connection.send(("error", type(exc).__name__, str(exc)))
        except (BrokenPipeError, EOFError, OSError):
            pass
    finally:
        connection.close()


def _stop_owned_process(process):
    """Bound cleanup of exactly one child created by this transport."""
    if process.is_alive():
        process.terminate()
    process.join(TRANSPORT_CLEANUP_SECONDS / 2)
    if process.is_alive():
        process.kill()
        process.join(TRANSPORT_CLEANUP_SECONDS / 2)
    alive = process.is_alive()
    process.close()
    if alive:
        raise RuntimeError("owned transport process did not stop")


def _partial_raw(metadata, chunks):
    if metadata is None:
        return None
    return {
        "status": metadata[0],
        "headers": metadata[1],
        "body": b"".join(chunks),
    }


def _transport(url, body, timeout, *, absolute_deadline=None):
    """Run urllib in a spawn child under one absolute monotonic deadline."""
    if absolute_deadline is None:
        absolute_deadline = time.monotonic() + timeout
    context = multiprocessing.get_context("spawn")
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(
        target=_transport_child,
        args=(sender, url, body, timeout),
        name="source-replay-http",
        daemon=True,
    )
    attempted = False
    metadata = None
    chunks = []
    active_deadline = absolute_deadline - TRANSPORT_CLEANUP_SECONDS
    try:
        if time.monotonic() >= active_deadline:
            raise _SupervisedTransportError(
                "absolute author request deadline expired before transport",
                deadline=True,
            )
        try:
            process.start()
            attempted = True
        except Exception as exc:
            raise _SupervisedTransportError(
                f"could not start owned transport: {type(exc).__name__}: {exc}"
            ) from exc
        finally:
            sender.close()
        while True:
            remaining = active_deadline - time.monotonic()
            if remaining <= 0:
                raise _SupervisedTransportError(
                    "absolute author request deadline expired",
                    raw=_partial_raw(metadata, chunks),
                    attempted=attempted,
                    deadline=True,
                )
            if not receiver.poll(min(remaining, 0.05)):
                if process.is_alive():
                    continue
                if receiver.poll(0):
                    continue
                raise _SupervisedTransportError(
                    "owned transport exited without a complete response",
                    raw=_partial_raw(metadata, chunks),
                    attempted=attempted,
                )
            try:
                message = receiver.recv()
            except EOFError as exc:
                raise _SupervisedTransportError(
                    "owned transport closed before a complete response",
                    raw=_partial_raw(metadata, chunks),
                    attempted=attempted,
                ) from exc
            if message[0] == "metadata":
                if metadata is not None:
                    raise _SupervisedTransportError(
                        "owned transport returned duplicate metadata",
                        raw=_partial_raw(metadata, chunks),
                        attempted=attempted,
                    )
                metadata = (message[1], message[2])
            elif message[0] == "body":
                if metadata is None:
                    raise _SupervisedTransportError(
                        "owned transport returned body before metadata",
                        attempted=attempted,
                    )
                chunks.append(message[1])
            elif message[0] == "complete":
                raw = _partial_raw(metadata, chunks)
                if raw is None:
                    raise _SupervisedTransportError(
                        "owned transport completed without metadata",
                        attempted=attempted,
                    )
                return raw
            elif message[0] == "error":
                raise _SupervisedTransportError(
                    f"urllib child failed: {message[1]}: {message[2]}",
                    raw=_partial_raw(metadata, chunks),
                    attempted=attempted,
                )
            else:
                raise _SupervisedTransportError(
                    "owned transport returned an invalid event",
                    raw=_partial_raw(metadata, chunks),
                    attempted=attempted,
                )
    finally:
        sender.close()
        receiver.close()
        if process.pid is not None:
            _stop_owned_process(process)
        else:
            process.close()


def _deadline(deadline, clock):
    now = clock()
    if now >= deadline:
        raise PreparationFailure("deadline", "whole preparation deadline expired")
    return min(REQUEST_DEADLINE_SECONDS, deadline - now)


def _request_bytes(prompt):
    return json.dumps(
        {
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "think": True,
        },
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _response_envelope(value):
    if type(value) is not dict:
        raise PreparationFailure("envelope", "Ollama envelope must be an object")
    response = value.get("response")
    thinking = value.get("thinking")
    if (
        value.get("model") != RESPONSE_MODEL
        or value.get("done") is not True
        or value.get("done_reason") != "stop"
        or not isinstance(response, str)
        or not response
        or not isinstance(thinking, str)
    ):
        raise PreparationFailure("envelope", "Ollama envelope is incomplete")
    counts = {}
    for key in ("prompt_eval_count", "eval_count"):
        count = value.get(key)
        if type(count) is not int or count < 0:
            raise PreparationFailure("envelope", f"Ollama {key} is invalid")
        counts[key] = count
    return response, thinking, counts


def _save_response_receipt(
    run,
    slot,
    raw,
    started,
    started_unix,
    ended,
    *,
    response_complete,
):
    if type(raw) is not dict or set(raw) != {"status", "headers", "body"}:
        raise PreparationFailure(
            "transport", "transport returned an invalid receipt", attempted=True
        )
    response_body = raw["body"]
    if not isinstance(response_body, bytes):
        raise PreparationFailure(
            "transport", "transport body is not exact bytes", attempted=True
        )
    response_path = Path("raw") / f"call-{slot['slot_index']:04d}-response.bin"
    try:
        _write_bytes(run / response_path, response_body, exclusive=True)
    except PreparationFailure as exc:
        raise PreparationFailure(exc.kind, str(exc), attempted=True) from exc
    return {
        "status": raw["status"],
        "headers": copy.deepcopy(raw["headers"]),
        "raw_path": str(response_path),
        "body_bytes": len(response_body),
        "body_sha256": _sha_bytes(response_body),
        "response_complete": response_complete,
        "started_monotonic": started,
        "started_at_unix": started_unix,
        "ended_monotonic": ended,
        "ended_at_unix": time.time(),
        "elapsed_seconds": ended - started,
    }


def _perform_http(run, slot, body, deadline, transport, clock):
    started = clock()
    if started >= deadline:
        raise PreparationFailure("deadline", "whole preparation deadline expired")
    timeout = min(REQUEST_DEADLINE_SECONDS, deadline - started)
    started_unix = time.time()
    try:
        if transport is _transport:
            raw = transport(
                ENDPOINT,
                body,
                timeout,
                absolute_deadline=min(deadline, started + REQUEST_DEADLINE_SECONDS),
            )
        else:
            raw = transport(ENDPOINT, body, timeout)
    except _SupervisedTransportError as exc:
        ended = clock()
        receipt = None
        if exc.raw is not None:
            receipt = _save_response_receipt(
                run,
                slot,
                exc.raw,
                started,
                started_unix,
                ended,
                response_complete=False,
            )
        raise PreparationFailure(
            "deadline" if exc.deadline else "transport",
            str(exc),
            response=receipt,
            attempted=exc.attempted,
        ) from exc
    except Exception as exc:
        raise PreparationFailure(
            "transport",
            f"author request failed: {type(exc).__name__}: {exc}",
            attempted=True,
        ) from exc
    ended = clock()
    receipt = _save_response_receipt(
        run,
        slot,
        raw,
        started,
        started_unix,
        ended,
        response_complete=True,
    )
    response_body = raw["body"]
    if raw["status"] != 200:
        raise PreparationFailure(
            "transport",
            f"author HTTP status {raw['status']}",
            response=receipt,
            attempted=True,
        )
    try:
        envelope = authoring.parse_author_json(response_body)
    except ValueError as exc:
        raise PreparationFailure(
            "envelope", str(exc), response=receipt, attempted=True
        ) from exc
    try:
        content, thinking, counts = _response_envelope(envelope)
    except PreparationFailure as exc:
        raise PreparationFailure(
            exc.kind, str(exc), response=receipt, attempted=True
        ) from exc
    receipt.update(
        envelope=envelope,
        response_bytes=len(content.encode("utf-8")),
        response_sha256=_sha_bytes(content.encode("utf-8")),
        thinking_bytes=len(thinking.encode("utf-8")),
        thinking_sha256=_sha_bytes(thinking.encode("utf-8")),
        reported_token_counts=counts,
        done_reason=envelope["done_reason"],
    )
    if receipt["elapsed_seconds"] > timeout or ended >= deadline:
        raise PreparationFailure(
            "deadline",
            "author response returned after its request or whole deadline",
            response=receipt,
            attempted=True,
        )
    return receipt, content, timeout


def _prompt_for_stage(stage, project_index, states, texts):
    project_id = PROJECT_IDS[project_index]
    if stage == 0:
        return authoring.render_scaffold_prompt(
            texts["scaffold_prompt"], project_id, DOMAINS[project_index]
        )
    state = states[project_index]
    return authoring.render_round_prompt(
        texts["round_prompt"],
        project_id,
        stage,
        state["scaffold"],
        state["packets"],
        texts["data_contract"],
    )


def _failure_terminal(job, status, reason, stage, started, deadline, clock):
    ended = clock()
    job.update(
        status=status,
        reason=reason,
        terminal_stage=stage,
        ended_monotonic=ended,
        elapsed_seconds=ended - started,
    )
    return job


def publish_terminal(
    path,
    job,
    started,
    deadline,
    *,
    clock=time.monotonic,
    writer=None,
):
    """Publish a positive result only if the completed write remains in budget."""
    if writer is None:
        writer = _write_json
    terminal = {
        "schema_version": 1,
        "kind": "source-replay-staged-preparation-terminal",
        "status": job["status"],
        "reason": job["reason"],
        "terminal_stage": job["terminal_stage"],
        "started_monotonic": started,
        "deadline_monotonic": deadline,
        "published_monotonic": clock(),
    }
    if terminal["published_monotonic"] >= deadline:
        terminal.update(
            status="INCOMPLETE", reason="positive publication exceeded whole deadline"
        )
    writer(path, terminal)
    if terminal["status"] == "PREPARED_UNREVIEWED" and clock() >= deadline:
        terminal.update(
            status="INCOMPLETE", reason="positive publication exceeded whole deadline"
        )
        writer(path, terminal)
    return terminal


def run_preparation(
    run_dir,
    freeze_path,
    *,
    root=ROOT,
    transport=_transport,
    executor_factory=ThreadPoolExecutor,
    clock=time.monotonic,
    register_pid=_register_pid,
    whole_deadline_seconds=None,
):
    """Execute at most sixteen calls in four strict stage barriers."""
    binding = validate_freeze(freeze_path, root=root)
    run = Path(run_dir)
    if not run.is_absolute():
        raise ValueError("run-dir must be absolute")
    if run.exists():
        raise FileExistsError("run-dir must be a new path")
    started = clock()
    allowance = (
        WHOLE_DEADLINE_SECONDS
        if whole_deadline_seconds is None
        else whole_deadline_seconds
    )
    if (
        isinstance(allowance, bool)
        or type(allowance) not in {int, float}
        or not math.isfinite(allowance)
        or allowance <= 0
        or allowance > WHOLE_DEADLINE_SECONDS
    ):
        raise ValueError("whole deadline override is invalid")
    deadline = started + allowance
    register_pid()
    run.mkdir(parents=False)
    (run / "calls").mkdir()
    (run / "raw").mkdir()
    (run / "stages").mkdir()
    (run / "projects").mkdir()
    slots = planned_slots()
    job = {
        "schema_version": 1,
        "kind": "source-replay-staged-preparation-job",
        "status": "IN_PROGRESS",
        "reason": "four stage barriers have not completed",
        "terminal_stage": None,
        "started_monotonic": started,
        "deadline_monotonic": deadline,
        "ended_monotonic": None,
        "elapsed_seconds": None,
        "freeze": binding["freeze"],
        "freeze_sha256": binding["freeze_sha256"],
        "request_options": {
            "endpoint": ENDPOINT,
            "model": MODEL,
            "stream": False,
            "think": True,
            "request_deadline_seconds": REQUEST_DEADLINE_SECONDS,
        },
        "planned_slots": slots,
        "prepared_projects": [],
    }
    _write_json(run / "job.json", job, exclusive=True)
    texts = {
        "scaffold_prompt": (binding["root"] / SCAFFOLD_PROMPT).read_text(
            encoding="utf-8"
        ),
        "round_prompt": (binding["root"] / ROUND_PROMPT).read_text(encoding="utf-8"),
        "data_contract": (binding["root"] / DATA_CONTRACT).read_text(encoding="utf-8"),
    }
    states = [
        {
            "scaffold": None,
            "lineage": None,
            "packets": [],
            "reference_module": None,
            "validation_records": [],
        }
        for _ in PROJECT_IDS
    ]
    failure = None
    for stage in range(4):
        try:
            _deadline(deadline, clock)
        except PreparationFailure as exc:
            failure = ("INCOMPLETE", str(exc), stage)
            break
        stage_slots = slots[stage * 4 : (stage + 1) * 4]
        prepared = []
        for project_index, slot in enumerate(stage_slots):
            try:
                prompt = _prompt_for_stage(stage, project_index, states, texts)
                body = _request_bytes(prompt)
                request_path = (
                    Path("raw") / f"call-{slot['slot_index']:04d}-request.bin"
                )
                _write_bytes(run / request_path, body, exclusive=True)
                timeout = _deadline(deadline, clock)
            except Exception as exc:
                failure = ("INCOMPLETE", f"request preparation failed: {exc}", stage)
                break
            record = {
                **copy.deepcopy(slot),
                "request": {
                    "url": ENDPOINT,
                    "timeout_seconds": timeout,
                    "raw_path": str(request_path),
                    "body_bytes": len(body),
                    "body_sha256": _sha_bytes(body),
                },
                "response": None,
                "parsed_content": None,
                "validation": None,
                "error": None,
            }
            _write_json(
                run / "calls" / f"call-{slot['slot_index']:04d}.json",
                record,
                exclusive=True,
            )
            prepared.append((project_index, slot, record, body, timeout))
        _write_json(run / "job.json", job)
        if failure is not None:
            break
        for _, slot, record, _, _ in prepared:
            slot["status"] = "PENDING"
            record["status"] = "PENDING"
            _write_json(run / "calls" / f"call-{slot['slot_index']:04d}.json", record)
        _write_json(run / "job.json", job)
        with executor_factory(max_workers=4) as executor:
            futures = [
                (
                    item,
                    executor.submit(
                        _perform_http,
                        run,
                        item[1],
                        item[3],
                        deadline,
                        transport,
                        clock,
                    ),
                )
                for item in prepared
            ]
            delivered = []
            for item, future in futures:
                project_index, slot, record, _, _ = item
                try:
                    response, content, actual_timeout = future.result()
                    slot["attempts"] = 1
                    record["attempts"] = 1
                    record["response"] = response
                    record["request"]["timeout_seconds"] = actual_timeout
                    delivered.append((project_index, slot, record, content))
                except PreparationFailure as exc:
                    if exc.attempted or exc.response is not None:
                        slot["attempts"] = 1
                        record["attempts"] = 1
                    if exc.response is not None:
                        record["response"] = exc.response
                    slot["status"] = "ERROR"
                    record["status"] = "ERROR"
                    record["error"] = {"kind": exc.kind, "message": str(exc)}
                    failure = ("INCOMPLETE", str(exc), stage)
                except Exception as exc:
                    slot["status"] = "ERROR"
                    record["status"] = "ERROR"
                    record["error"] = {
                        "kind": "local_runtime",
                        "message": f"{type(exc).__name__}: {exc}",
                    }
                    failure = ("INCOMPLETE", record["error"]["message"], stage)
                _write_json(
                    run / "calls" / f"call-{slot['slot_index']:04d}.json", record
                )
        if failure is not None:
            for _, slot, record, _ in delivered:
                slot["status"] = "DELIVERED_UNVALIDATED"
                record["status"] = "DELIVERED_UNVALIDATED"
                _write_json(
                    run / "calls" / f"call-{slot['slot_index']:04d}.json", record
                )
        if failure is None:
            for project_index, slot, record, content in delivered:
                try:
                    _deadline(deadline, clock)
                    authored = authoring.parse_author_json(content)
                    record["parsed_content"] = authored
                    if stage == 0:
                        scaffold, lineage = authoring.assemble_scaffold(
                            PROJECT_IDS[project_index], authored
                        )
                        states[project_index].update(
                            scaffold=scaffold,
                            lineage=lineage,
                            reference_module=scaffold["initial_file"]["text"],
                        )
                        record["validation"] = {
                            "scaffold": scaffold,
                            "lineage": lineage,
                        }
                    else:

                        def check_deadline():
                            _deadline(deadline, clock)

                        packet, module, validation = (
                            authoring.validate_and_apply_packet(
                                states[project_index]["scaffold"],
                                states[project_index]["packets"],
                                authored,
                                stage,
                                states[project_index]["reference_module"],
                                deadline_check=check_deadline,
                            )
                        )
                        states[project_index]["packets"].append(packet)
                        states[project_index]["reference_module"] = module
                        states[project_index]["validation_records"].append(validation)
                        record["validation"] = validation
                    slot["status"] = "COMPLETE"
                    record["status"] = "COMPLETE"
                except authoring.StageValidationError as exc:
                    record["validation"] = exc.record
                    slot["status"] = "INELIGIBLE"
                    record["status"] = "INELIGIBLE"
                    record["error"] = {"kind": "validation", "message": str(exc)}
                    failure = ("INELIGIBLE", str(exc), stage)
                except authoring.StageExecutionInterrupted as exc:
                    record["validation"] = exc.record
                    slot["status"] = "ERROR"
                    record["status"] = "ERROR"
                    record["error"] = {"kind": "deadline", "message": str(exc)}
                    failure = ("INCOMPLETE", str(exc), stage)
                except PreparationFailure as exc:
                    slot["status"] = "ERROR"
                    record["status"] = "ERROR"
                    record["error"] = {"kind": exc.kind, "message": str(exc)}
                    failure = ("INCOMPLETE", str(exc), stage)
                except ValueError as exc:
                    slot["status"] = "INELIGIBLE"
                    record["status"] = "INELIGIBLE"
                    record["error"] = {"kind": "validation", "message": str(exc)}
                    failure = ("INELIGIBLE", str(exc), stage)
                except Exception as exc:
                    slot["status"] = "ERROR"
                    record["status"] = "ERROR"
                    record["error"] = {
                        "kind": "local_validation",
                        "message": f"{type(exc).__name__}: {exc}",
                    }
                    failure = ("INCOMPLETE", record["error"]["message"], stage)
                _write_json(
                    run / "calls" / f"call-{slot['slot_index']:04d}.json", record
                )
        _write_json(
            run / "stages" / f"stage-{stage}.json",
            {
                "stage": stage,
                "status": "COMPLETE" if failure is None else failure[0],
                "slots": copy.deepcopy(stage_slots),
            },
            exclusive=True,
        )
        _write_json(run / "job.json", job)
        if failure is not None:
            break

    if failure is None:
        try:
            for project_index, state in enumerate(states):
                _deadline(deadline, clock)
                project = authoring.assemble_project(
                    state["scaffold"], state["lineage"], state["packets"]
                )
                project_dir = run / "projects" / PROJECT_IDS[project_index]
                project_dir.mkdir()
                _write_json(project_dir / "authored.json", project, exclusive=True)
                _write_json(
                    project_dir / "validation.json",
                    {
                        "project_id": PROJECT_IDS[project_index],
                        "records": state["validation_records"],
                    },
                    exclusive=True,
                )
                authored_path = project_dir / "authored.json"
                authored_bytes = authored_path.read_bytes()
                job["prepared_projects"].append(
                    {
                        "project_id": PROJECT_IDS[project_index],
                        "path": str(authored_path.relative_to(run)),
                        "bytes": len(authored_bytes),
                        "sha256": _sha_bytes(authored_bytes),
                    }
                )
            _deadline(deadline, clock)
            _failure_terminal(
                job,
                "PREPARED_UNREVIEWED",
                "all four projects assembled; source review and final preflight remain",
                3,
                started,
                deadline,
                clock,
            )
        except PreparationFailure as exc:
            failure = ("INCOMPLETE", str(exc), 3)
        except ValueError as exc:
            failure = ("INELIGIBLE", str(exc), 3)
        except Exception as exc:
            failure = (
                "INCOMPLETE",
                f"final assembly failed: {type(exc).__name__}: {exc}",
                3,
            )
    if failure is not None:
        _failure_terminal(job, *failure, started, deadline, clock)
    _write_json(run / "job.json", job)
    terminal = publish_terminal(
        run / "terminal.json", job, started, deadline, clock=clock
    )
    if terminal["status"] != job["status"]:
        job.update(status=terminal["status"], reason=terminal["reason"])
        _write_json(run / "job.json", job)
    return terminal


def _parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, default=DEFAULT_FREEZE)
    parser.add_argument("--execute", action="store_true")
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    if not args.run_dir.is_absolute():
        raise ValueError("run-dir must be absolute")
    if not args.execute:
        print(
            json.dumps(
                dry_plan(args.run_dir, args.freeze),
                ensure_ascii=True,
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    terminal = run_preparation(args.run_dir, args.freeze)
    print(json.dumps(terminal, ensure_ascii=True, sort_keys=True))
    if terminal["status"] == "PREPARED_UNREVIEWED":
        return 0
    return 1 if terminal["status"] == "INELIGIBLE" else 2


if __name__ == "__main__":
    sys.exit(main())
