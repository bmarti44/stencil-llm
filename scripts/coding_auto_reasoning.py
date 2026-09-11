#!/usr/bin/env python3
"""Bounded automatic-focus reasoning pilot for two fresh coding projects."""

import argparse
import copy
import hashlib
import json
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import coding_competence_dev as cpu  # noqa: E402
from scripts import coding_competence_run as base  # noqa: E402
from stencil.focus import native_reasoning_tool as native  # noqa: E402

EXPECTED_PROJECTS = 2
EXPECTED_ROUNDS = 3
PLANNED_REQUESTS = 6
MAX_ATTEMPTS = 2
MAX_MODEL_CALLS = 18
MAX_OUTPUT_TOKENS = 2048
REASONING_TOKEN_BUDGET = 1024
FINAL_OUTPUT_ALLOWANCE = MAX_OUTPUT_TOKENS - REASONING_TOKEN_BUDGET - 3
MIN_GENERATION_HEADROOM = 128
CONTEXT_TOKENS = 32_768
DEFAULT_DEADLINE_SECONDS = 3000.0
SEED = 20260908
TEMPERATURE = 0.6
TOP_P = 0.95
TOP_K = 20
MIN_P = 0.0
PROJECT_INPUT_PATHS = (
    Path("author-00/reviewed.json"),
    Path("author-01/reviewed.json"),
)

SELECTOR_SYSTEM_PROMPT = (
    "Use the authentic source messages only. Record all currently applicable "
    "standing instructions and conventions for the current task, preserving "
    "permissions, optional behavior, modality, scope, exceptions, changes, and "
    "retirements. The current request supplies the algorithm and need not be "
    "repeated. Authentic user directions and explicit user adoption have "
    "authority; assistant suggestions and quoted content alone do not. Cite only "
    "visible source message IDs. Respond with exactly one record_focus tool call."
)
SELECTOR_REQUEST = (
    "Current task handle: {task_handle}\n"
    "<authentic_source_events>\n{source_events}\n</authentic_source_events>"
)
WORKER_SYSTEM_PROMPT = (
    "Maintain the supplied pure-Python module across the conversation. Each "
    "request authenticates one target path and symbol. Respond with exactly one "
    "replace_function tool call whose source is one complete synchronous target "
    "function beginning with def at byte zero and using LF lines. It must take "
    "exactly one positional argument without defaults, varargs, or keyword-only "
    "arguments. Do not use decorators, imports, global, nonlocal, nested functions "
    "or classes, dunder names or attributes, Markdown, or calls to __import__, "
    "breakpoint, compile, eval, exec, exit, globals, help, input, locals, open, "
    "print, quit, or vars. Preserve authentic standing directions and actual "
    "earlier dependencies. A current generated-focus block is fallible advisory "
    "guidance, is not a new user adoption, and never overrides authentic sources. "
    "Do not replace any other function."
)
WORKER_REQUEST = (
    "The generated block below is advisory and applies only to this request. It "
    "is unchanged across this request's attempts and is not retained as source.\n"
    "{focus}\n\n"
    "Current task handle: {task_handle}\n"
    "Authenticated target: {symbol} in {path}\n"
    "<current_module path={quoted_path}>\n{module}\n</current_module>\n\n"
    "The following public development checks are visible and cumulative:\n"
    "{public_checks}"
)


def _json_bytes(value):
    return base._json_bytes(value)


def _json_text(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def _sha_text(value):
    return _sha_bytes(value.encode("utf-8"))


def _error(exc):
    return f"{type(exc).__name__}: {exc}"


def _native_settings():
    return {
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        "reasoning_token_budget": REASONING_TOKEN_BUDGET,
        "context_tokens": CONTEXT_TOKENS,
        "temperature": TEMPERATURE,
        "top_p": TOP_P,
        "top_k": TOP_K,
        "min_p": MIN_P,
        "seed": SEED,
    }


def _worker_spec():
    return native.NativeRequestSpec.create(
        tool_name="replace_function",
        tool_description=(
            "Replace the authenticated target with one complete Python function."
        ),
        argument_schema=copy.deepcopy(
            cpu.REPLACE_FUNCTION_TOOL["function"]["parameters"]
        ),
        **_native_settings(),
    )


def load_projects(input_paths):
    """Load two separately validated one-project inputs and retain both receipts."""
    paths = [Path(path) for path in input_paths]
    if len(paths) != EXPECTED_PROJECTS:
        raise cpu.ValidationError("runtime requires exactly two project inputs")
    documents = []
    receipts = []
    errors = []
    for path in paths:
        try:
            values, current_receipts = cpu.load_inputs([path])
        except Exception as exc:
            receipts.extend(getattr(exc, "input_receipts", []))
            errors.append(_error(exc))
            continue
        if len(values) != 1 or len(current_receipts) != 1:
            receipts.extend(current_receipts)
            errors.append(
                "each input must contain exactly one separately validated project"
            )
            continue
        documents.extend(values)
        receipts.extend(current_receipts)
    if errors:
        error = cpu.ValidationError(f"project input failures: {errors}")
        error.input_receipts = receipts
        raise error
    episode_ids = [document["public"]["episode_id"] for document in documents]
    if len(set(episode_ids)) != len(episode_ids):
        error = cpu.ValidationError("episode IDs must be unique across project inputs")
        error.input_receipts = receipts
        raise error
    return documents, receipts


def resolve_input_directory(directory):
    root = Path(directory)
    if not root.is_dir():
        raise cpu.ValidationError("--input must be the reviewed project directory")
    return [root / relative for relative in PROJECT_INPUT_PATHS]


def _append_source_events(events, public_round):
    for message in public_round["source_messages"]:
        events.append(
            {
                "message_id": message["message_id"],
                "role": message["role"],
                "text": message["text"],
            }
        )
    request = public_round["request"]
    events.append(
        {
            "message_id": request["message_id"],
            "role": request["role"],
            "task_handle": request["task_handle"],
            "text": request["text"],
        }
    )


def _append_worker_sources(history, public_round):
    for message in public_round["source_messages"]:
        history.append({"role": message["role"], "content": message["text"]})
    request = public_round["request"]
    history.append({"role": request["role"], "content": request["text"]})


def build_selector_messages(source_events, task_handle):
    visible = copy.deepcopy(source_events)
    content = SELECTOR_REQUEST.format(
        task_handle=task_handle,
        source_events=_json_text(visible),
    )
    return [
        {"role": "system", "content": SELECTOR_SYSTEM_PROMPT},
        {"role": "user", "content": content},
    ]


def render_focus(arguments):
    obligations = arguments["obligations"]
    parts = ["<current_generated_focus>", ""]
    for index, obligation in enumerate(obligations):
        parts.extend(
            (
                f'<obligation index="{index}">',
                "<text>",
                obligation["text"],
                "</text>",
                "<source_ids>",
                _json_text(obligation["source_ids"]),
                "</source_ids>",
                "</obligation>",
            )
        )
    parts.append("</current_generated_focus>")
    return "\n".join(parts)


def build_worker_messages(document, history, round_index, module_text, focus):
    public_round = document["public"]["rounds"][round_index]
    target = public_round["target"]
    current = WORKER_REQUEST.format(
        focus=focus,
        task_handle=public_round["request"]["task_handle"],
        symbol=target["symbol"],
        path=target["path"],
        quoted_path=json.dumps(target["path"]),
        module=module_text,
        public_checks=_json_text(base._public_checks(document, round_index)),
    )
    return copy.deepcopy(history) + [{"role": "user", "content": current}]


def _validate_returned_action(action, spec):
    if type(action) is not dict:
        raise native.TechnicalError("malformed_response", "action must be an object")
    needed = {"call_id", "arguments", "raw_arguments", "assistant_message"}
    if not needed <= set(action):
        raise native.TechnicalError(
            "malformed_response", "action is missing validated native fields"
        )
    call_id, arguments, raw_arguments, _message = native._validate_tool_message(
        action["assistant_message"], spec
    )
    if call_id != action["call_id"] or raw_arguments != action["raw_arguments"]:
        raise native.TechnicalError(
            "malformed_response", "action disagrees with its assistant message"
        )
    if not cpu.cpu.json_equal(arguments, action["arguments"]):
        raise native.TechnicalError(
            "malformed_response", "parsed action arguments disagree"
        )
    return action


def _prepare_output(directory):
    return base._prepare_output(directory)


def _planned_records(documents):
    records = []
    request_index = 0
    for document in documents:
        episode_id = document["public"]["episode_id"]
        for round_index, public_round in enumerate(document["public"]["rounds"]):
            records.append(
                {
                    "schema_version": 1,
                    "request_index": request_index,
                    "episode_id": episode_id,
                    "round_index": round_index,
                    "request_message_id": public_round["request"]["message_id"],
                    "task_handle": public_round["request"]["task_handle"],
                    "target": copy.deepcopy(public_round["target"]),
                    "status": "UNATTEMPTED",
                    "selector_call_index": None,
                    "selector_status": "UNATTEMPTED",
                    "focus": None,
                    "focus_raw_arguments": None,
                    "focus_rendering": None,
                    "worker_attempts": [],
                    "public_solved": False,
                    "terminal_private_checks": [],
                    "unfinished_private_check_ids": [],
                    "terminal_private_passed": False,
                    "request_passed": False,
                    "pre_module_sha256": None,
                    "post_module_sha256": None,
                    "technical_error": None,
                }
            )
            request_index += 1
    return records


def _code_hashes():
    paths = {
        Path(__file__).resolve(),
        Path(native.__file__).resolve(),
        Path(base.__file__).resolve(),
        Path(cpu.__file__).resolve(),
        Path(cpu.cpu.__file__).resolve(),
        Path(cpu.cpu.slab.__file__).resolve(),
        Path(cpu.cpu.slab.__file__).with_name("slab_sandbox.py").resolve(),
        ROOT / "models/qwen3-30b-a3b-hf/tokenizer.json",
        ROOT / "models/qwen3-30b-a3b-hf/tokenizer_config.json",
        ROOT / "models/qwen3-30b-a3b-hf/config.json",
        ROOT / "models/qwen3-30b-a3b-hf/generation_config.json",
    }
    return {
        str(path.relative_to(ROOT)): _sha_bytes(path.read_bytes())
        for path in sorted(paths, key=str)
    }


def _manifest(documents, receipts, records, deadline_seconds, runtime_args):
    return {
        "schema_version": 1,
        "kind": "coding-auto-reasoning-run",
        "status": "INCOMPLETE",
        "reason": "run not completed",
        "mechanical_candidate": False,
        "pilot_go": None,
        "pilot_go_note": (
            "Requires independent source/focus and implementation review."
        ),
        "started_at_unix": time.time(),
        "finished_at_unix": None,
        "elapsed_seconds": None,
        "inputs": receipts,
        "code_sha256": _code_hashes(),
        "runtime_args": list(runtime_args) if runtime_args is not None else None,
        "runtime_config": {
            "projects": EXPECTED_PROJECTS,
            "rounds_per_project": EXPECTED_ROUNDS,
            "planned_requests": PLANNED_REQUESTS,
            "max_attempts_per_request": MAX_ATTEMPTS,
            "max_model_calls": MAX_MODEL_CALLS,
            "max_output_tokens": MAX_OUTPUT_TOKENS,
            "reasoning_token_budget": REASONING_TOKEN_BUDGET,
            "context_tokens": CONTEXT_TOKENS,
            "deadline_seconds": float(deadline_seconds),
            "seed": SEED,
            "temperature": TEMPERATURE,
            "top_p": TOP_P,
            "top_k": TOP_K,
            "min_p": MIN_P,
            "selector_source_only": True,
            "focus_persistent_history": False,
            "private_feedback_in_prompts": False,
            "native_render_before_completion": True,
        },
        "planned_work": [
            {
                key: record[key]
                for key in (
                    "request_index",
                    "episode_id",
                    "round_index",
                    "request_message_id",
                    "target",
                )
            }
            for record in records
        ],
        "recorded_requests": 0,
        "completed_requests": 0,
        "unattempted_requests": PLANNED_REQUESTS,
        "recorded_calls": 0,
        "selector_calls": 0,
        "worker_calls": 0,
        "render_requests": 0,
        "generation_requests": 0,
        "technical_failure": None,
        "accounting_complete": False,
        "projects": [],
    }


def _refresh_manifest(manifest, records, calls, started, clock):
    attempted = [record for record in records if record["status"] != "UNATTEMPTED"]
    completed = [record for record in records if record["status"] == "COMPLETE"]
    manifest["recorded_requests"] = len(attempted)
    manifest["completed_requests"] = len(completed)
    manifest["unattempted_requests"] = PLANNED_REQUESTS - len(attempted)
    manifest["recorded_calls"] = len(calls)
    manifest["selector_calls"] = sum(call["kind"] == "selector" for call in calls)
    manifest["worker_calls"] = sum(call["kind"] == "worker" for call in calls)
    manifest["render_requests"] = sum(
        call.get("native_exchange", {}).get("render", {}).get("status")
        not in {None, "PENDING"}
        for call in calls
    )
    manifest["generation_requests"] = sum(
        call.get("native_exchange", {}).get("completion", {}).get("status")
        not in {None, "NOT_STARTED", "PENDING"}
        for call in calls
    )
    manifest["elapsed_seconds"] = clock() - started


def _finish_manifest(manifest, documents, records, calls, started, clock, failure):
    _refresh_manifest(manifest, records, calls, started, clock)
    projects = []
    for document in documents:
        episode_id = document["public"]["episode_id"]
        project_records = [
            record for record in records if record["episode_id"] == episode_id
        ]
        project_calls = [call for call in calls if call["episode_id"] == episode_id]
        usages = [
            call["native_exchange"]["usage"]
            for call in project_calls
            if call.get("native_exchange", {}).get("usage") is not None
        ]
        projects.append(
            {
                "episode_id": episode_id,
                "completed_requests": sum(
                    record["status"] == "COMPLETE" for record in project_records
                ),
                "project_passed": len(project_records) == EXPECTED_ROUNDS
                and all(record["request_passed"] for record in project_records),
                "model_calls": len(project_calls),
                "selector_calls": sum(
                    call["kind"] == "selector" for call in project_calls
                ),
                "worker_calls": sum(call["kind"] == "worker" for call in project_calls),
                "prompt_tokens": sum(item["prompt_tokens"] for item in usages),
                "completion_tokens": sum(item["completion_tokens"] for item in usages),
                "total_tokens": sum(item["total_tokens"] for item in usages),
            }
        )
    manifest["projects"] = projects
    manifest["accounting_complete"] = all(
        record["status"] == "COMPLETE" for record in records
    )
    manifest["mechanical_candidate"] = manifest["accounting_complete"] and any(
        project["project_passed"] for project in projects
    )
    manifest["technical_failure"] = failure
    if failure is not None:
        manifest["status"] = "INCOMPLETE"
        manifest["reason"] = failure["error"]
    elif manifest["accounting_complete"]:
        manifest["status"] = "COMPLETE"
        manifest["reason"] = (
            "mechanical candidate pending independent review"
            if manifest["mechanical_candidate"]
            else "complete mechanical no-go"
        )
    else:
        manifest["status"] = "INCOMPLETE"
        manifest["reason"] = "planned request accounting is incomplete"
    manifest["finished_at_unix"] = time.time()
    manifest["elapsed_seconds"] = clock() - started


def _new_call(
    root,
    calls,
    call_index,
    request_index,
    episode_id,
    round_index,
    kind,
    attempt_index,
    messages,
    payload,
    module_text=None,
):
    request_body = _json_bytes(payload)
    call = {
        "schema_version": 1,
        "status": "PENDING",
        "call_index": call_index,
        "request_index": request_index,
        "episode_id": episode_id,
        "round_index": round_index,
        "kind": kind,
        "attempt_index": attempt_index,
        "started_at_unix": time.time(),
        "elapsed_seconds": None,
        "issued_messages": copy.deepcopy(messages),
        "issued_messages_sha256": _sha_bytes(_json_bytes(messages)),
        "request_intent": copy.deepcopy(payload),
        "request_body": request_body.decode("utf-8"),
        "request_body_sha256": _sha_bytes(request_body),
        "native_exchange": None,
        "tool_call": None,
        "pre_module": module_text,
        "pre_module_sha256": (
            _sha_text(module_text) if module_text is not None else None
        ),
        "post_module": module_text,
        "post_module_sha256": (
            _sha_text(module_text) if module_text is not None else None
        ),
        "apply_status": None,
        "consumer_error": None,
        "public_checks": [],
        "unfinished_public_check_ids": [],
        "all_public_passed": False,
        "technical_error": None,
    }
    path = root / "calls" / f"call-{call_index:04d}.json"
    base._write_json(path, call, exclusive=True)
    calls.append(call)
    return call, path, request_body


def _perform(client, spec, call, call_path, request_body):
    def persist(exchange):
        call["native_exchange"] = copy.deepcopy(exchange)
        base._write_json(call_path, call)

    action = client.perform(request_body, persist)
    return _validate_returned_action(action, spec)


def _mark_technical(call, call_path, exc, call_started, clock):
    call["status"] = "TECHNICAL_ERROR"
    call["technical_error"] = _error(exc)
    call["elapsed_seconds"] = clock() - call_started
    base._write_json(call_path, call)


def run(
    input_paths,
    output_dir,
    client_factory,
    *,
    deadline_seconds=DEFAULT_DEADLINE_SECONDS,
    runtime_args=None,
    check_runner=None,
    clock=time.monotonic,
):
    documents, input_receipts = load_projects(input_paths)
    if (
        type(deadline_seconds) not in {int, float}
        or not math.isfinite(deadline_seconds)
        or deadline_seconds <= 0
    ):
        raise ValueError("deadline_seconds must be positive")
    if not callable(client_factory):
        raise TypeError("client_factory must be callable")
    if check_runner is not None and not callable(check_runner):
        raise TypeError("check_runner must be callable")
    root = _prepare_output(output_dir)
    records = _planned_records(documents)
    if len(records) != PLANNED_REQUESTS:
        raise ValueError("runtime schedule must contain exactly six requests")
    for record in records:
        base._write_json(
            root / "requests" / f"request-{record['request_index']:04d}.json",
            record,
            exclusive=True,
        )
    started = clock()
    deadline = started + float(deadline_seconds)
    manifest = _manifest(
        documents, input_receipts, records, deadline_seconds, runtime_args
    )
    manifest_path = root / "manifest.json"
    base._write_json(manifest_path, manifest, exclusive=True)
    source_events = {document["public"]["episode_id"]: [] for document in documents}
    worker_histories = {
        document["public"]["episode_id"]: [
            {"role": "system", "content": WORKER_SYSTEM_PROMPT}
        ]
        for document in documents
    }
    states = {
        document["public"]["episode_id"]: document["public"]["initial_file"]["text"]
        for document in documents
    }
    used_call_ids = {document["public"]["episode_id"]: set() for document in documents}
    calls = []
    failure = None
    call_index = 0
    request_index = 0

    for document in documents:
        if failure is not None:
            break
        episode_id = document["public"]["episode_id"]
        history = worker_histories[episode_id]
        events = source_events[episode_id]
        for round_index, public_round in enumerate(document["public"]["rounds"]):
            if failure is not None:
                break
            record = records[request_index]
            record_path = root / "requests" / f"request-{request_index:04d}.json"
            record["status"] = "IN_PROGRESS"
            record["pre_module_sha256"] = _sha_text(states[episode_id])
            record["unfinished_private_check_ids"] = [
                check["check_id"]
                for check in base._private_checks(document, round_index)
            ]
            _append_source_events(events, public_round)
            _append_worker_sources(history, public_round)
            record["source_events"] = copy.deepcopy(events)
            record["worker_history_before_request"] = copy.deepcopy(history)
            base._write_json(record_path, record)
            base._write_text(
                root / "workspaces" / f"request-{request_index:04d}-start.py",
                states[episode_id],
            )

            selector_spec = native.record_focus_spec(
                [event["message_id"] for event in events], **_native_settings()
            )
            selector_messages = build_selector_messages(
                events, public_round["request"]["task_handle"]
            )
            selector_started = clock()
            selector_call = None
            selector_path = None
            try:
                if call_index >= MAX_MODEL_CALLS:
                    raise native.TechnicalError(
                        "accounting", "maximum model-call schedule exceeded"
                    )
                selector_client = client_factory(selector_spec)
                if callable(getattr(selector_client, "set_deadline", None)):
                    selector_client.set_deadline(deadline)
                selector_payload = selector_client.payload(selector_messages)
                selector_call, selector_path, selector_body = _new_call(
                    root,
                    calls,
                    call_index,
                    request_index,
                    episode_id,
                    round_index,
                    "selector",
                    None,
                    selector_messages,
                    selector_payload,
                )
                record["selector_call_index"] = call_index
                record["selector_status"] = "PENDING"
                base._write_json(record_path, record)
                selector_action = _perform(
                    selector_client,
                    selector_spec,
                    selector_call,
                    selector_path,
                    selector_body,
                )
                if selector_action["call_id"] in used_call_ids[episode_id]:
                    raise native.TechnicalError(
                        "malformed_response", "tool call ID was reused"
                    )
                used_call_ids[episode_id].add(selector_action["call_id"])
            except Exception as exc:
                if selector_call is not None:
                    _mark_technical(
                        selector_call,
                        selector_path,
                        exc,
                        selector_started,
                        clock,
                    )
                    call_index += 1
                record["selector_status"] = "TECHNICAL_ERROR"
                record["status"] = "TECHNICAL_INCOMPLETE"
                record["technical_error"] = _error(exc)
                base._write_json(record_path, record)
                failure = {
                    "kind": getattr(exc, "kind", "local_request"),
                    "error": _error(exc),
                    "request_index": request_index,
                    "call_index": (
                        selector_call["call_index"] if selector_call else None
                    ),
                }
                break
            selector_call["tool_call"] = {
                "id": selector_action["call_id"],
                "name": "record_focus",
                "raw_arguments": selector_action["raw_arguments"],
                "arguments": copy.deepcopy(selector_action["arguments"]),
            }
            selector_call["status"] = "COMPLETE"
            selector_call["elapsed_seconds"] = clock() - selector_started
            base._write_json(selector_path, selector_call)
            record["selector_status"] = "COMPLETE"
            record["focus"] = copy.deepcopy(selector_action["arguments"])
            record["focus_raw_arguments"] = selector_action["raw_arguments"]
            focus_rendering = render_focus(selector_action["arguments"])
            record["focus_rendering"] = focus_rendering
            base._write_json(record_path, record)
            call_index += 1
            _refresh_manifest(manifest, records, calls, started, clock)
            base._write_json(manifest_path, manifest)

            public_solved = False
            worker_spec = _worker_spec()
            for attempt_index in range(MAX_ATTEMPTS):
                worker_started = clock()
                worker_call = None
                worker_path = None
                try:
                    if call_index >= MAX_MODEL_CALLS:
                        raise native.TechnicalError(
                            "accounting", "maximum model-call schedule exceeded"
                        )
                    messages = build_worker_messages(
                        document,
                        history,
                        round_index,
                        states[episode_id],
                        focus_rendering,
                    )
                    worker_client = client_factory(worker_spec)
                    if callable(getattr(worker_client, "set_deadline", None)):
                        worker_client.set_deadline(deadline)
                    payload = worker_client.payload(messages)
                    worker_call, worker_path, request_body = _new_call(
                        root,
                        calls,
                        call_index,
                        request_index,
                        episode_id,
                        round_index,
                        "worker",
                        attempt_index,
                        messages,
                        payload,
                        states[episode_id],
                    )
                    worker_call["unfinished_public_check_ids"] = [
                        check["check_id"]
                        for check in base._public_checks(document, round_index)
                    ]
                    base._write_json(worker_path, worker_call)
                    record["worker_attempts"].append(
                        {
                            "call_index": call_index,
                            "attempt_index": attempt_index,
                            "status": "PENDING",
                            "source_sha256": None,
                            "post_module_sha256": worker_call["post_module_sha256"],
                            "apply_status": None,
                            "all_public_passed": False,
                        }
                    )
                    base._write_json(record_path, record)
                    action = _perform(
                        worker_client,
                        worker_spec,
                        worker_call,
                        worker_path,
                        request_body,
                    )
                    if action["call_id"] in used_call_ids[episode_id]:
                        raise native.TechnicalError(
                            "malformed_response", "tool call ID was reused"
                        )
                    used_call_ids[episode_id].add(action["call_id"])
                except Exception as exc:
                    if worker_call is not None:
                        _mark_technical(
                            worker_call,
                            worker_path,
                            exc,
                            worker_started,
                            clock,
                        )
                        call_index += 1
                    if record["worker_attempts"]:
                        record["worker_attempts"][-1]["status"] = "TECHNICAL_ERROR"
                    record["status"] = "TECHNICAL_INCOMPLETE"
                    record["technical_error"] = _error(exc)
                    base._write_json(record_path, record)
                    failure = {
                        "kind": getattr(exc, "kind", "local_request"),
                        "error": _error(exc),
                        "request_index": request_index,
                        "call_index": (
                            worker_call["call_index"] if worker_call else None
                        ),
                    }
                    break
                worker_call["tool_call"] = {
                    "id": action["call_id"],
                    "name": "replace_function",
                    "raw_arguments": action["raw_arguments"],
                    "arguments": copy.deepcopy(action["arguments"]),
                }
                source_sha, source_error = base._source_hash(
                    action["arguments"]["source"]
                )
                worker_call["submitted_source_sha256"] = source_sha
                worker_call["submitted_source_hash_error"] = source_error
                target = public_round["target"]
                applied = None
                consumer_error = None
                try:
                    applied = cpu.consume_action(
                        states[episode_id],
                        target["path"],
                        target["symbol"],
                        action["arguments"],
                    )
                except cpu.PatchError as exc:
                    consumer_error = _error(exc)
                if applied is not None:
                    states[episode_id] = applied.module
                    worker_call["apply_status"] = "APPLIED"
                    worker_call["post_module"] = applied.module
                    worker_call["post_module_sha256"] = applied.module_sha256
                    base._write_json(worker_path, worker_call)
                    base._write_text(
                        root
                        / "workspaces"
                        / f"request-{request_index:04d}-attempt-{attempt_index}.py",
                        states[episode_id],
                    )
                    checks_complete = base._run_checks_incremental(
                        worker_call,
                        worker_path,
                        "public_checks",
                        "unfinished_public_check_ids",
                        states[episode_id],
                        episode_id,
                        base._public_checks(document, round_index),
                        deadline=deadline,
                        clock=clock,
                        check_runner=check_runner,
                    )
                    if not checks_complete:
                        error = native.TechnicalError(
                            "deadline", "deadline interrupted public checks"
                        )
                        _mark_technical(
                            worker_call,
                            worker_path,
                            error,
                            worker_started,
                            clock,
                        )
                        record["worker_attempts"][-1]["status"] = "TECHNICAL_ERROR"
                        record["status"] = "TECHNICAL_INCOMPLETE"
                        record["technical_error"] = _error(error)
                        base._write_json(record_path, record)
                        failure = {
                            "kind": "deadline",
                            "error": _error(error),
                            "request_index": request_index,
                            "call_index": call_index,
                        }
                        call_index += 1
                        break
                else:
                    worker_call["apply_status"] = "REJECTED"
                    worker_call["consumer_error"] = consumer_error
                    worker_call["unfinished_public_check_ids"] = []
                feedback = base._tool_feedback(
                    applied is not None,
                    consumer_error,
                    states[episode_id],
                    worker_call["public_checks"],
                )
                history.append(action["assistant_message"])
                history.append(
                    {
                        "role": "tool",
                        "tool_call_id": action["call_id"],
                        "name": "replace_function",
                        "content": _json_text(feedback),
                    }
                )
                worker_call["all_public_passed"] = feedback["all_public_passed"]
                worker_call["status"] = "COMPLETE"
                worker_call["elapsed_seconds"] = clock() - worker_started
                base._write_json(worker_path, worker_call)
                record["worker_attempts"][-1].update(
                    status="COMPLETE",
                    source_sha256=source_sha,
                    post_module_sha256=worker_call["post_module_sha256"],
                    apply_status=worker_call["apply_status"],
                    all_public_passed=worker_call["all_public_passed"],
                )
                base._write_json(record_path, record)
                call_index += 1
                _refresh_manifest(manifest, records, calls, started, clock)
                base._write_json(manifest_path, manifest)
                if applied is not None and worker_call["all_public_passed"]:
                    public_solved = True
                    break
            if failure is not None:
                break
            record["public_solved"] = public_solved
            record["status"] = "TERMINAL_CHECKS"
            record["post_module_sha256"] = _sha_text(states[episode_id])
            private_checks = base._private_checks(document, round_index)
            private_complete = base._run_checks_incremental(
                record,
                record_path,
                "terminal_private_checks",
                "unfinished_private_check_ids",
                states[episode_id],
                episode_id,
                private_checks,
                deadline=deadline,
                clock=clock,
                check_runner=check_runner,
            )
            if not private_complete:
                error = native.TechnicalError(
                    "deadline", "deadline interrupted private checks"
                )
                record["status"] = "TECHNICAL_INCOMPLETE"
                record["technical_error"] = _error(error)
                base._write_json(record_path, record)
                failure = {
                    "kind": "deadline",
                    "error": _error(error),
                    "request_index": request_index,
                    "call_index": None,
                }
                break
            record["terminal_private_passed"] = bool(
                record["terminal_private_checks"]
            ) and all(result["passed"] for result in record["terminal_private_checks"])
            record["request_passed"] = (
                public_solved and record["terminal_private_passed"]
            )
            record["status"] = "COMPLETE"
            record["worker_history_after_request"] = copy.deepcopy(history)
            base._write_text(
                root / "workspaces" / f"request-{request_index:04d}-terminal.py",
                states[episode_id],
            )
            base._write_json(record_path, record)
            request_index += 1
            _refresh_manifest(manifest, records, calls, started, clock)
            base._write_json(manifest_path, manifest)

    _finish_manifest(manifest, documents, records, calls, started, clock, failure)
    base._write_json(manifest_path, manifest)
    return manifest


def _default_token_counter(text):
    return len(cpu.cpu.slab.qwen_encode(text))


def _reference_arguments(document, round_index, source_events):
    private_round = document["private"]["rounds"][round_index]
    task_handle = document["public"]["rounds"][round_index]["request"]["task_handle"]
    focus = {
        "obligations": [
            {"text": rule["text"], "source_ids": list(rule["source_ids"])}
            for rule in private_round["oracle"]["effective_rules"]
            if rule["scope"] in {"global", task_handle}
        ]
    }
    selector_spec = native.record_focus_spec(
        [event["message_id"] for event in source_events], **_native_settings()
    )
    native._validate_arguments(selector_spec, focus)
    return focus, {"source": private_round["reference_patch"]}


def _argument_receipt(episode_id, round_index, kind, arguments, token_counter):
    body = _json_text(arguments).encode("utf-8")
    tokens = int(token_counter(body.decode("utf-8")))
    headroom = FINAL_OUTPUT_ALLOWANCE - tokens
    return {
        "episode_id": episode_id,
        "round_index": round_index,
        "kind": kind,
        "argument_body": body.decode("utf-8"),
        "argument_body_sha256": _sha_bytes(body),
        "argument_body_bytes": len(body),
        "argument_tokens": tokens,
        "full_reasoning_bound_tokens": REASONING_TOKEN_BUDGET,
        "reasoning_delimiter_and_eos_tokens": 3,
        "available_final_tokens": FINAL_OUTPUT_ALLOWANCE,
        "generation_headroom": headroom,
        "eligible": headroom >= MIN_GENERATION_HEADROOM,
    }


def _conservative_growth(document):
    rows = []
    source_bytes = 0
    for round_index, public_round in enumerate(document["public"]["rounds"]):
        source_bytes += sum(
            len(message["text"].encode("utf-8"))
            for message in public_round["source_messages"]
        )
        source_bytes += len(public_round["request"]["text"].encode("utf-8"))
        for attempt_index in range(MAX_ATTEMPTS):
            prior_pairs = round_index * MAX_ATTEMPTS + attempt_index
            rows.append(
                {
                    "episode_id": document["public"]["episode_id"],
                    "round_index": round_index,
                    "attempt_index": attempt_index,
                    "visible_authentic_source_bytes": source_bytes,
                    "maximum_prior_worker_action_pairs": prior_pairs,
                    "maximum_repeated_module_observations": prior_pairs + 1,
                    "module_byte_limit_each_observation": cpu.cpu.MAX_MODULE_BYTES,
                    "submitted_source_byte_limit_each_action": cpu.MAX_SOURCE_BYTES,
                    "universal_future_prompt_fit_claim": False,
                }
            )
    return rows


def preflight_projects(input_paths):
    started = time.monotonic()
    paths = [Path(path) for path in input_paths]
    _documents, receipts = load_projects(paths)
    projects = [cpu.preflight_inputs([path]) for path in paths]
    return {
        "schema_version": 1,
        "kind": "coding-auto-reasoning-cpu-preflight",
        "status": (
            "PASS" if all(item["status"] == "PASS" for item in projects) else "FAIL"
        ),
        "model_calls": 0,
        "documents": len(projects),
        "inputs": receipts,
        "projects": projects,
        "execution_count": sum(item["execution_count"] for item in projects),
        "elapsed_seconds": time.monotonic() - started,
    }


def preview(input_paths, *, model="/model", token_counter=_default_token_counter):
    started = time.monotonic()
    paths = [Path(path) for path in input_paths]
    documents, receipts = load_projects(paths)
    preflight = preflight_projects(paths)
    selector_cold = []
    reference_actions = []
    growth = []
    maximum_checks = 0
    for document in documents:
        episode_id = document["public"]["episode_id"]
        events = []
        growth.extend(_conservative_growth(document))
        for round_index, public_round in enumerate(document["public"]["rounds"]):
            _append_source_events(events, public_round)
            selector_spec = native.record_focus_spec(
                [event["message_id"] for event in events], **_native_settings()
            )
            messages = build_selector_messages(
                events, public_round["request"]["task_handle"]
            )
            client = native.NativeReasoningToolClient(
                "http://127.0.0.1:18088", model, selector_spec
            )
            payload = client.payload(messages)
            body = _json_bytes(payload)
            local_tokens = int(token_counter(body.decode("utf-8")))
            selector_cold.append(
                {
                    "episode_id": episode_id,
                    "round_index": round_index,
                    "visible_source_ids": [event["message_id"] for event in events],
                    "messages_sha256": _sha_bytes(_json_bytes(messages)),
                    "request_body_sha256": _sha_bytes(body),
                    "request_body_bytes": len(body),
                    "local_serialized_request_tokens": local_tokens,
                    "local_serialized_request_with_output": (
                        local_tokens + MAX_OUTPUT_TOKENS
                    ),
                    "local_serialized_request_below_context": (
                        local_tokens + MAX_OUTPUT_TOKENS <= CONTEXT_TOKENS
                    ),
                    "local_count_is_native_prompt_tokens": False,
                }
            )
            focus, edit = _reference_arguments(document, round_index, events)
            reference_actions.append(
                _argument_receipt(
                    episode_id, round_index, "record_focus", focus, token_counter
                )
            )
            reference_actions.append(
                _argument_receipt(
                    episode_id, round_index, "replace_function", edit, token_counter
                )
            )
            maximum_checks += MAX_ATTEMPTS * len(
                base._public_checks(document, round_index)
            ) + len(base._private_checks(document, round_index))
    all_preflight = preflight["status"] == "PASS"
    all_headroom = all(item["eligible"] for item in reference_actions)
    return {
        "schema_version": 1,
        "kind": "coding-auto-reasoning-preview",
        "status": "PASS" if all_preflight and all_headroom else "INELIGIBLE",
        "model_calls": 0,
        "documents": len(documents),
        "scheduled_requests": PLANNED_REQUESTS,
        "max_attempts_per_request": MAX_ATTEMPTS,
        "max_model_calls": MAX_MODEL_CALLS,
        "settings": {
            "model": model,
            "max_output_tokens": MAX_OUTPUT_TOKENS,
            "reasoning_token_budget": REASONING_TOKEN_BUDGET,
            "available_final_tokens": FINAL_OUTPUT_ALLOWANCE,
            "context_tokens": CONTEXT_TOKENS,
            "minimum_generation_headroom": MIN_GENERATION_HEADROOM,
            "seed": SEED,
            "temperature": TEMPERATURE,
            "top_p": TOP_P,
            "top_k": TOP_K,
            "min_p": MIN_P,
        },
        "inputs": receipts,
        "code_sha256": _code_hashes(),
        "preflight": preflight,
        "selector_cold_requests": selector_cold,
        "reference_actions": reference_actions,
        "all_reference_actions_headroom": all_headroom,
        "all_cpu_preflight_passed": all_preflight,
        "future_actual_prompt_claim": False,
        "actual_native_render_required_before_every_generation": True,
        "conservative_growth": growth,
        "resource_bounds": {
            "maximum_render_requests": MAX_MODEL_CALLS,
            "maximum_generation_requests": MAX_MODEL_CALLS,
            "maximum_http_requests": 2 * MAX_MODEL_CALLS,
            "maximum_sandbox_checks": maximum_checks,
            "maximum_prior_worker_action_pairs_per_prompt": max(
                item["maximum_prior_worker_action_pairs"] for item in growth
            ),
            "maximum_repeated_module_observations_per_prompt": max(
                item["maximum_repeated_module_observations"] for item in growth
            ),
        },
        "cpu_elapsed_seconds": time.monotonic() - started,
    }


def _parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help=(
            "reviewed input directory containing exactly author-00/reviewed.json "
            "and author-01/reviewed.json"
        ),
    )
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--base-url", default="http://127.0.0.1:18088")
    parser.add_argument("--model", default="/model")
    parser.add_argument(
        "--deadline-seconds", type=float, default=DEFAULT_DEADLINE_SECONDS
    )
    parser.add_argument("--preview", action="store_true")
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    try:
        input_paths = resolve_input_directory(args.input)
    except Exception as exc:
        result = {
            "schema_version": 1,
            "kind": (
                "coding-auto-reasoning-preview"
                if args.preview
                else "coding-auto-reasoning-run"
            ),
            "status": "INVALID" if args.preview else "INCOMPLETE",
            "model_calls": 0,
            "mechanical_candidate": False,
            "pilot_go": None,
            "error": _error(exc),
            "inputs": getattr(exc, "input_receipts", []),
        }
        print(json.dumps(result, ensure_ascii=True, sort_keys=True), flush=True)
        return 2
    if args.preview:
        try:
            result = preview(input_paths, model=args.model)
        except Exception as exc:
            result = {
                "schema_version": 1,
                "kind": "coding-auto-reasoning-preview",
                "status": "INVALID",
                "model_calls": 0,
                "error": _error(exc),
                "inputs": getattr(exc, "input_receipts", []),
            }
        print(json.dumps(result, ensure_ascii=True, sort_keys=True), flush=True)
        return 0 if result["status"] == "PASS" else 2
    if args.output_dir is None:
        raise ValueError("--output-dir is required unless --preview is used")

    def client_factory(spec):
        return native.NativeReasoningToolClient(args.base_url, args.model, spec)

    try:
        result = run(
            input_paths,
            args.output_dir,
            client_factory,
            deadline_seconds=args.deadline_seconds,
            runtime_args=sys.argv[1:] if argv is None else argv,
        )
    except Exception as exc:
        result = {
            "schema_version": 1,
            "kind": "coding-auto-reasoning-run",
            "status": "INCOMPLETE",
            "mechanical_candidate": False,
            "pilot_go": None,
            "error": _error(exc),
            "inputs": getattr(exc, "input_receipts", []),
        }
    print(json.dumps(result, ensure_ascii=True, sort_keys=True), flush=True)
    if result["status"] != "COMPLETE":
        return 2
    return 0 if result["mechanical_candidate"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
