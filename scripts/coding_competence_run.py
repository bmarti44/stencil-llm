#!/usr/bin/env python3
"""Native-tool runtime for the coding-competence prerequisite screen."""

import argparse
import base64
import copy
import hashlib
import json
import math
import os
import sys
import tempfile
import time
from http.client import IncompleteRead
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request as HTTPRequest
from urllib.request import urlopen

try:
    from scripts import coding_competence_dev as cpu
except ModuleNotFoundError as exc:  # Direct ``python scripts/...`` invocation.
    if exc.name != "scripts":
        raise
    import coding_competence_dev as cpu

EXPECTED_EPISODES = 4
EXPECTED_ROUNDS = 3
PLANNED_REQUESTS = 12
MAX_ATTEMPTS = 3
MAX_MODEL_CALLS = 36
MAX_OUTPUT_TOKENS = 1024
CONTEXT_TOKENS = 32_768
DEFAULT_DEADLINE_SECONDS = 2700.0
HTTP_TIMEOUT_SECONDS = 600.0
RECEIPT_RESERVE_SECONDS = 1.0
SANDBOX_CHECK_ALLOWANCE_SECONDS = 2.0
SEED = 20260908

SYSTEM_PROMPT = (
    "Maintain the supplied pure-Python module across this conversation. Each "
    "request authenticates one target path and symbol. Respond with exactly one "
    "replace_function tool call whose source is the complete requested synchronous "
    "function, beginning with def at column zero. Preserve applicable standing "
    "directions and use actual earlier dependencies. Do not return Markdown or "
    "replace any other function."
)
CURRENT_PROMPT = (
    "The reminder in this block applies only to the current request; it is not a "
    "new standing instruction and will be removed before the next request.\n"
    "<current_manual_reminder>\n{manual_recap}\n</current_manual_reminder>\n\n"
    "Current task handle: {task_handle}\n"
    "Authenticated target: {symbol} in {path}\n"
    "<current_module path={quoted_path}>\n{module}\n</current_module>\n\n"
    "The following public development cases are visible and cumulative:\n"
    "{public_checks}"
)

ARGUMENT_SCHEMA = copy.deepcopy(cpu.REPLACE_FUNCTION_TOOL["function"]["parameters"])


class TechnicalError(RuntimeError):
    """The native exchange or run cannot provide complete technical evidence."""

    def __init__(self, kind, message):
        super().__init__(message)
        self.kind = kind


def _error(exc):
    return f"{type(exc).__name__}: {exc}"


def _json_bytes(value):
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def _sha_text(value):
    return _sha_bytes(value.encode("utf-8"))


def _source_hash(value):
    try:
        return _sha_text(value), None
    except UnicodeEncodeError as exc:
        return None, _error(exc)


def _write_json(path, value, *, exclusive=False):
    path = Path(path)
    if exclusive:
        with path.open("x", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=True, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        return
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            json.dump(value, handle, ensure_ascii=True, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _write_text(path, value):
    path = Path(path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
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


def _response_headers(response):
    headers = getattr(response, "headers", None)
    if headers is None:
        return {}
    return dict(headers.items()) if hasattr(headers, "items") else dict(headers)


def _response_receipt(response, body, *, incomplete_expected_bytes=None):
    body = bytes(body)
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError:
        text = None
    receipt = {
        "status": getattr(response, "status", getattr(response, "code", None)),
        "headers": _response_headers(response),
        "body": text,
        "body_base64": base64.b64encode(body).decode("ascii"),
        "body_sha256": _sha_bytes(body),
        "body_bytes": len(body),
    }
    if incomplete_expected_bytes is not None:
        receipt["incomplete_read_expected_bytes"] = incomplete_expected_bytes
    return receipt


def _request_receipt(url, body, timeout):
    return {
        "url": url,
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "timeout_seconds": timeout,
        "body": body.decode("utf-8"),
        "body_base64": base64.b64encode(body).decode("ascii"),
        "body_sha256": _sha_bytes(body),
        "body_bytes": len(body),
    }


def _token_ids(value, label):
    if type(value) is not list or not value:
        raise TechnicalError("token_accounting", f"{label} must be a nonempty list")
    if any(type(item) is not int or item < 0 for item in value):
        raise TechnicalError(
            "token_accounting", f"{label} must contain nonnegative integers"
        )
    return value


def _validate_usage(value):
    if type(value) is not dict:
        raise TechnicalError("token_accounting", "usage must be an object")
    counts = {}
    for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
        count = value.get(key)
        if type(count) is not int or count < 0:
            raise TechnicalError(
                "token_accounting", f"usage.{key} must be a nonnegative integer"
            )
        counts[key] = count
    if counts["total_tokens"] != (
        counts["prompt_tokens"] + counts["completion_tokens"]
    ):
        raise TechnicalError(
            "token_accounting", "usage total does not equal prompt plus completion"
        )
    if counts["completion_tokens"] > MAX_OUTPUT_TOKENS:
        raise TechnicalError("capacity", "completion token count exceeds the cap")
    return counts


def _validate_tool_call_message(message):
    if type(message) is not dict or message.get("role") != "assistant":
        raise TechnicalError("malformed_response", "choice message must be assistant")
    if message.get("content") is not None and message.get("content") != "":
        raise TechnicalError(
            "malformed_response", "named tool response contains completion text"
        )
    tool_calls = message.get("tool_calls")
    if type(tool_calls) is not list or len(tool_calls) != 1:
        raise TechnicalError(
            "malformed_response", "response must contain exactly one tool call"
        )
    call = tool_calls[0]
    if type(call) is not dict or call.get("type") != "function":
        raise TechnicalError("malformed_response", "tool call type must be function")
    call_id = call.get("id")
    function = call.get("function")
    if not isinstance(call_id, str) or not call_id:
        raise TechnicalError("malformed_response", "tool call id is missing")
    if type(function) is not dict or function.get("name") != "replace_function":
        raise TechnicalError("malformed_response", "wrong native tool function")
    raw_arguments = function.get("arguments")
    if not isinstance(raw_arguments, str):
        raise TechnicalError("malformed_response", "tool arguments must be JSON text")
    try:
        arguments = json.loads(raw_arguments)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise TechnicalError(
            "malformed_response", f"tool arguments are invalid JSON: {exc}"
        ) from exc
    if type(arguments) is not dict or set(arguments) != {"source"}:
        raise TechnicalError(
            "malformed_response", "tool arguments must contain exactly source"
        )
    if not isinstance(arguments["source"], str):
        raise TechnicalError("malformed_response", "tool source must be a string")
    history_message = {
        "role": "assistant",
        "content": message.get("content"),
        "tool_calls": copy.deepcopy(tool_calls),
    }
    return call_id, arguments, raw_arguments, history_message


def _validate_history(messages):
    if type(messages) is not list or not messages:
        raise ValueError("messages must be a nonempty list")
    result = copy.deepcopy(messages)
    for index, message in enumerate(result):
        if type(message) is not dict:
            raise ValueError(f"message {index} must be an object")
        role = message.get("role")
        if role in {"system", "user"}:
            if set(message) != {"role", "content"} or not isinstance(
                message["content"], str
            ):
                raise ValueError(f"message {index} has invalid {role} content")
        elif role == "assistant" and set(message) == {"role", "content"}:
            if not isinstance(message["content"], str):
                raise ValueError(f"message {index} assistant content must be text")
        elif role == "assistant":
            _validate_tool_call_message(message)
        elif role == "tool":
            if set(message) != {"role", "tool_call_id", "name", "content"}:
                raise ValueError(f"message {index} has invalid tool-result fields")
            if (
                not isinstance(message["tool_call_id"], str)
                or not message["tool_call_id"]
                or message["name"] != "replace_function"
                or not isinstance(message["content"], str)
            ):
                raise ValueError(f"message {index} has invalid tool-result content")
        else:
            raise ValueError(f"message {index} has unsupported role")
    _json_bytes(result)
    return result


class NativeToolClient:
    """Two-stage authoritative render and named-tool completion client."""

    def __init__(self, base_url, model, *, opener=None):
        base_url = str(base_url).rstrip("/")
        if not base_url.startswith(("http://", "https://")):
            base_url = "http://" + base_url
        self.render_endpoint = base_url + "/v1/chat/completions/render"
        self.completion_endpoint = base_url + "/v1/chat/completions"
        self.model = str(model)
        self.opener = opener or urlopen
        self.deadline = None
        self.last_exchange = None

    def set_deadline(self, deadline):
        self.deadline = deadline

    def _timeout(self):
        if self.deadline is None:
            return HTTP_TIMEOUT_SECONDS
        remaining = self.deadline - time.monotonic() - RECEIPT_RESERVE_SECONDS
        if remaining <= 0:
            raise TechnicalError("deadline", "deadline leaves no receipt reserve")
        return min(HTTP_TIMEOUT_SECONDS, remaining)

    def payload(self, messages):
        return {
            "model": self.model,
            "messages": _validate_history(messages),
            "tools": [copy.deepcopy(cpu.REPLACE_FUNCTION_TOOL)],
            "tool_choice": copy.deepcopy(cpu.FORCED_TOOL_CHOICE),
            "stream": False,
            "parallel_tool_calls": False,
            "return_token_ids": True,
            "max_tokens": MAX_OUTPUT_TOKENS,
            "temperature": 0,
            "seed": SEED,
            "chat_template_kwargs": {"enable_thinking": False},
        }

    def _post(self, url, body):
        started_at = time.time()
        started = time.monotonic()
        timeout = self._timeout()
        request = HTTPRequest(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        receipt = {
            "status": "PENDING",
            "request": _request_receipt(url, body, timeout),
            "response": None,
            "error": None,
            "started_at_unix": started_at,
            "elapsed_seconds": None,
        }
        try:
            with self.opener(request, timeout=timeout) as response:
                try:
                    response_body = response.read()
                except IncompleteRead as exc:
                    receipt["response"] = _response_receipt(
                        response,
                        exc.partial,
                        incomplete_expected_bytes=exc.expected,
                    )
                    raise OSError(f"incomplete HTTP response: {exc}") from exc
                receipt["response"] = _response_receipt(response, response_body)
                if receipt["response"]["status"] != 200:
                    raise OSError(f"unexpected HTTP status {response.status}")
        except HTTPError as exc:
            incomplete = None
            try:
                response_body = exc.read()
            except IncompleteRead as read_exc:
                response_body = read_exc.partial
                incomplete = read_exc.expected
            receipt["response"] = _response_receipt(
                exc, response_body, incomplete_expected_bytes=incomplete
            )
            receipt["status"] = "ERROR"
            receipt["error"] = _error(exc)
            receipt["elapsed_seconds"] = time.monotonic() - started
            return receipt
        except Exception as exc:
            receipt["status"] = "ERROR"
            receipt["error"] = _error(exc)
            receipt["elapsed_seconds"] = time.monotonic() - started
            return receipt
        receipt["status"] = "COMPLETE"
        receipt["elapsed_seconds"] = time.monotonic() - started
        return receipt

    @staticmethod
    def _parsed_response(receipt, label):
        if receipt["status"] != "COMPLETE":
            raise TechnicalError("transport", f"{label} transport failed")
        body = receipt["response"]["body"]
        if body is None:
            raise TechnicalError("malformed_response", f"{label} is not UTF-8")
        try:
            value = json.loads(body)
        except json.JSONDecodeError as exc:
            raise TechnicalError(
                "malformed_response", f"{label} is invalid JSON: {exc}"
            ) from exc
        if type(value) is not dict:
            raise TechnicalError("malformed_response", f"{label} must be a JSON object")
        receipt["response"]["json"] = value
        return value

    @staticmethod
    def _fail(exchange, persist, exc):
        exchange["status"] = "ERROR"
        exchange["failure_kind"] = exc.kind
        exchange["error"] = _error(exc)
        persist(exchange)
        raise exc

    def perform(self, request_body, persist):
        if not isinstance(request_body, bytes):
            raise TypeError("request_body must be exact bytes")
        request_sha256 = _sha_bytes(request_body)
        exchange = {
            "status": "PENDING",
            "request_body_sha256": request_sha256,
            "request_body_bytes": len(request_body),
            "render": {
                "status": "PENDING",
                "request": _request_receipt(
                    self.render_endpoint, request_body, self._timeout()
                ),
                "response": None,
                "error": None,
            },
            "completion": {"status": "NOT_STARTED"},
            "finish_reason": None,
            "usage": None,
            "tool_call": None,
            "failure_kind": None,
            "error": None,
        }
        self.last_exchange = exchange
        persist(exchange)
        try:
            exchange["render"] = self._post(self.render_endpoint, request_body)
            persist(exchange)
            rendered = self._parsed_response(exchange["render"], "render response")
            prompt_ids = _token_ids(rendered.get("token_ids"), "render token_ids")
            try:
                rendered_schema = rendered["sampling_params"]["structured_outputs"][
                    "json"
                ]
            except (KeyError, TypeError) as exc:
                raise TechnicalError(
                    "render_schema", "render response lacks structured JSON schema"
                ) from exc
            if rendered_schema != ARGUMENT_SCHEMA:
                raise TechnicalError(
                    "render_schema", "render structured JSON schema does not match"
                )
            if len(prompt_ids) + MAX_OUTPUT_TOKENS > CONTEXT_TOKENS:
                raise TechnicalError("capacity", "authoritative context limit exceeded")

            exchange["completion"] = {
                "status": "PENDING",
                "request": _request_receipt(
                    self.completion_endpoint, request_body, self._timeout()
                ),
                "response": None,
                "error": None,
            }
            persist(exchange)
            exchange["completion"] = self._post(self.completion_endpoint, request_body)
            persist(exchange)
            completed = self._parsed_response(
                exchange["completion"], "completion response"
            )
            choices = completed.get("choices")
            if type(choices) is not list or len(choices) != 1:
                raise TechnicalError(
                    "malformed_response", "completion needs exactly one choice"
                )
            choice = choices[0]
            if type(choice) is not dict:
                raise TechnicalError("malformed_response", "choice must be an object")
            finish_reason = choice.get("finish_reason")
            exchange["finish_reason"] = finish_reason
            exchange["completion"]["response"]["json"] = completed
            if finish_reason == "length":
                raise TechnicalError("capacity", "finish_reason length reached cap")
            if finish_reason != "stop":
                raise TechnicalError(
                    "malformed_response", f"unsupported finish reason {finish_reason!r}"
                )
            call_id, arguments, raw_arguments, history_message = (
                _validate_tool_call_message(choice.get("message"))
            )
            render_ids = _token_ids(
                completed.get("prompt_token_ids"), "completion prompt_token_ids"
            )
            if render_ids != prompt_ids:
                raise TechnicalError(
                    "token_accounting", "completion prompt IDs differ from render IDs"
                )
            output_ids = _token_ids(choice.get("token_ids"), "choice token_ids")
            usage = _validate_usage(completed.get("usage"))
            if len(render_ids) != usage["prompt_tokens"]:
                raise TechnicalError(
                    "token_accounting", "prompt token IDs disagree with usage"
                )
            if len(output_ids) != usage["completion_tokens"]:
                raise TechnicalError(
                    "token_accounting", "output token IDs disagree with usage"
                )
            exchange["usage"] = usage
            exchange["tool_call"] = {
                "id": call_id,
                "name": "replace_function",
                "raw_arguments": raw_arguments,
                "arguments": arguments,
            }
            exchange["status"] = "COMPLETE"
            persist(exchange)
            return {
                "call_id": call_id,
                "arguments": arguments,
                "raw_arguments": raw_arguments,
                "assistant_message": history_message,
                "usage": usage,
            }
        except TechnicalError as exc:
            self._fail(exchange, persist, exc)
        except Exception as exc:
            self._fail(
                exchange,
                persist,
                TechnicalError("local_runtime", f"native client failed: {_error(exc)}"),
            )


def _public_checks(document, round_index):
    checks = list(document["public"]["initial_checks"])
    for public_round in document["public"]["rounds"][: round_index + 1]:
        checks.extend(public_round["public_checks"])
    return checks


def _private_checks(document, round_index):
    checks = list(document["public"]["initial_checks"])
    for private_round in document["private"]["rounds"][: round_index + 1]:
        checks.extend(private_round["functional_checks"])
    checks.extend(document["private"]["rounds"][round_index]["obligation_checks"])
    return checks


def _append_natural(history, public_round):
    for message in public_round["source_messages"]:
        history.append({"role": message["role"], "content": message["text"]})
    history.append({"role": "user", "content": public_round["request"]["text"]})


def build_issued_messages(document, history, round_index, module_text):
    public_round = document["public"]["rounds"][round_index]
    private_round = document["private"]["rounds"][round_index]
    target = public_round["target"]
    visible_checks = _public_checks(document, round_index)
    current = CURRENT_PROMPT.format(
        manual_recap=private_round["manual_recap"],
        task_handle=public_round["request"]["task_handle"],
        symbol=target["symbol"],
        path=target["path"],
        quoted_path=json.dumps(target["path"]),
        module=module_text,
        public_checks=json.dumps(
            visible_checks,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ),
    )
    return _validate_history(
        copy.deepcopy(history) + [{"role": "user", "content": current}]
    )


def _tool_feedback(applied, error, module_text, results):
    return {
        "apply_status": "applied" if applied else "rejected",
        "error": error,
        "current_module": module_text,
        "public_checks": [
            {
                "check_id": result["check_id"],
                "passed": result["passed"],
                "actual": result["actual"],
                "error": result["error"],
            }
            for result in results
        ],
        "all_public_passed": bool(results)
        and all(result["passed"] for result in results),
    }


def _execute_check(module_text, episode_id, check, check_runner):
    if check_runner is None:
        return cpu._run_check_group(module_text, episode_id, [check])[0]
    result = check_runner(module_text, [check])[0]
    result = copy.deepcopy(result)
    result["episode_id"] = episode_id
    result["input"] = copy.deepcopy(check["input"])
    result["module_sha256"] = _sha_text(module_text)
    result["check_sha256"] = _sha_bytes(_json_bytes(check))
    return result


def _run_checks_incremental(
    record,
    record_path,
    key,
    unfinished_key,
    module_text,
    episode_id,
    checks,
    *,
    deadline,
    clock,
    check_runner,
):
    record[key] = []
    record[unfinished_key] = [check["check_id"] for check in checks]
    _write_json(record_path, record)
    for index, check in enumerate(checks):
        if clock() >= deadline - (
            SANDBOX_CHECK_ALLOWANCE_SECONDS + RECEIPT_RESERVE_SECONDS
        ):
            return False
        result = _execute_check(module_text, episode_id, check, check_runner)
        record[key].append(result)
        record[unfinished_key] = [
            remaining["check_id"] for remaining in checks[index + 1 :]
        ]
        _write_json(record_path, record)
        if clock() >= deadline - RECEIPT_RESERVE_SECONDS:
            return False
    return True


def _prepare_output(directory):
    root = Path(directory)
    if root.exists():
        if not root.is_dir() or any(root.iterdir()):
            raise FileExistsError("refuse existing nonempty output directory")
    else:
        root.mkdir(parents=True)
    for name in ("calls", "requests", "workspaces"):
        (root / name).mkdir()
    return root


def _code_hashes():
    root = Path(__file__).resolve().parents[1]
    paths = {
        Path(__file__).resolve(),
        Path(cpu.__file__).resolve(),
        Path(cpu.cpu.__file__).resolve(),
        Path(cpu.cpu.slab.__file__).resolve(),
        Path(cpu.cpu.slab.__file__).with_name("slab_sandbox.py").resolve(),
    }
    return {
        str(path.relative_to(root)): _sha_bytes(path.read_bytes())
        for path in sorted(paths, key=str)
    }


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
                    "attempts": [],
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


def _manifest(documents, input_receipts, deadline_seconds, runtime_args, records):
    return {
        "schema_version": 1,
        "kind": "coding-competence-native-run",
        "status": "INCOMPLETE",
        "reason": "run not completed",
        "mechanical_go": False,
        "competence_go": None,
        "competence_go_note": (
            "Requires independent source review and launcher lifecycle evidence."
        ),
        "started_at_unix": time.time(),
        "finished_at_unix": None,
        "elapsed_seconds": None,
        "inputs": input_receipts,
        "code_sha256": _code_hashes(),
        "runtime_args": list(runtime_args) if runtime_args is not None else None,
        "runtime_config": {
            "episodes": EXPECTED_EPISODES,
            "rounds_per_episode": EXPECTED_ROUNDS,
            "planned_requests": PLANNED_REQUESTS,
            "max_attempts_per_request": MAX_ATTEMPTS,
            "max_model_calls": MAX_MODEL_CALLS,
            "max_output_tokens": MAX_OUTPUT_TOKENS,
            "context_tokens": CONTEXT_TOKENS,
            "deadline_seconds": float(deadline_seconds),
            "seed": SEED,
            "temperature": 0,
            "native_render_before_completion": True,
            "private_feedback_in_prompts": False,
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
    manifest["render_requests"] = sum(
        call.get("native_exchange", {}).get("render", {}).get("status") != "PENDING"
        for call in calls
        if call.get("native_exchange")
    )
    manifest["generation_requests"] = sum(
        call.get("native_exchange", {}).get("completion", {}).get("status")
        not in {None, "NOT_STARTED", "PENDING"}
        for call in calls
        if call.get("native_exchange")
    )
    manifest["elapsed_seconds"] = clock() - started


def _finish_manifest(manifest, records, calls, documents, started, clock, failure):
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
        render_seconds = sum(
            call["native_exchange"].get("render", {}).get("elapsed_seconds") or 0
            for call in project_calls
            if call.get("native_exchange")
        )
        completion_seconds = sum(
            call["native_exchange"].get("completion", {}).get("elapsed_seconds") or 0
            for call in project_calls
            if call.get("native_exchange")
        )
        projects.append(
            {
                "episode_id": episode_id,
                "completed_requests": sum(
                    record["status"] == "COMPLETE" for record in project_records
                ),
                "project_passed": len(project_records) == EXPECTED_ROUNDS
                and all(record["request_passed"] for record in project_records),
                "first_submissions": [
                    record["attempts"][0] if record["attempts"] else None
                    for record in project_records
                ],
                "terminal_submissions": [
                    record["attempts"][-1] if record["attempts"] else None
                    for record in project_records
                ],
                "model_calls": len(project_calls),
                "prompt_tokens": sum(usage["prompt_tokens"] for usage in usages),
                "completion_tokens": sum(
                    usage["completion_tokens"] for usage in usages
                ),
                "total_tokens": sum(usage["total_tokens"] for usage in usages),
                "call_elapsed_seconds": sum(
                    call.get("elapsed_seconds") or 0 for call in project_calls
                ),
                "render_elapsed_seconds": render_seconds,
                "completion_elapsed_seconds": completion_seconds,
            }
        )
    manifest["projects"] = projects
    manifest["accounting_complete"] = all(
        record["status"] == "COMPLETE" for record in records
    )
    manifest["mechanical_go"] = manifest["accounting_complete"] and all(
        project["project_passed"] for project in projects
    )
    manifest["technical_failure"] = failure
    if failure is not None:
        manifest["status"] = "INCOMPLETE"
        manifest["reason"] = failure["error"]
    elif manifest["accounting_complete"]:
        manifest["status"] = "COMPLETE"
        manifest["reason"] = (
            "mechanical prerequisites passed"
            if manifest["mechanical_go"]
            else "complete mechanical no-go"
        )
    else:
        manifest["status"] = "INCOMPLETE"
        manifest["reason"] = "planned request accounting is incomplete"
    manifest["finished_at_unix"] = time.time()
    manifest["elapsed_seconds"] = clock() - started


def run(
    input_paths,
    output_dir,
    client,
    *,
    deadline_seconds=DEFAULT_DEADLINE_SECONDS,
    runtime_args=None,
    check_runner=None,
    clock=time.monotonic,
):
    documents, input_receipts = cpu.load_inputs(input_paths)
    if len(documents) != EXPECTED_EPISODES:
        raise ValueError("runtime requires exactly four competence episodes")
    if (
        type(deadline_seconds) not in {int, float}
        or not math.isfinite(deadline_seconds)
        or deadline_seconds <= 0
    ):
        raise ValueError("deadline_seconds must be positive")
    if not callable(getattr(client, "payload", None)) or not callable(
        getattr(client, "perform", None)
    ):
        raise TypeError("client must provide payload and perform")
    if check_runner is not None and not callable(check_runner):
        raise TypeError("check_runner must be callable")
    root = _prepare_output(output_dir)
    records = _planned_records(documents)
    if len(records) != PLANNED_REQUESTS:
        raise ValueError("runtime schedule must contain exactly 12 requests")
    for record in records:
        _write_json(
            root / "requests" / f"request-{record['request_index']:04d}.json",
            record,
            exclusive=True,
        )
    started = clock()
    deadline = started + float(deadline_seconds)
    if callable(getattr(client, "set_deadline", None)):
        client.set_deadline(deadline)
    manifest = _manifest(
        documents, input_receipts, deadline_seconds, runtime_args, records
    )
    manifest_path = root / "manifest.json"
    _write_json(manifest_path, manifest, exclusive=True)
    histories = {
        document["public"]["episode_id"]: [{"role": "system", "content": SYSTEM_PROMPT}]
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
        history = histories[episode_id]
        for round_index, public_round in enumerate(document["public"]["rounds"]):
            if failure is not None:
                break
            record = records[request_index]
            record_path = root / "requests" / f"request-{request_index:04d}.json"
            record["status"] = "IN_PROGRESS"
            record["pre_module_sha256"] = _sha_text(states[episode_id])
            record["unfinished_private_check_ids"] = [
                check["check_id"] for check in _private_checks(document, round_index)
            ]
            _append_natural(history, public_round)
            record["history_before_attempts"] = copy.deepcopy(history)
            _write_json(record_path, record)
            _write_text(
                root / "workspaces" / f"request-{request_index:04d}-start.py",
                states[episode_id],
            )
            public_solved = False
            for attempt_index in range(MAX_ATTEMPTS):
                if call_index >= MAX_MODEL_CALLS:
                    failure = {
                        "kind": "accounting",
                        "error": "TechnicalError: maximum model-call schedule exceeded",
                        "request_index": request_index,
                    }
                    break
                messages = build_issued_messages(
                    document, history, round_index, states[episode_id]
                )
                try:
                    payload = client.payload(messages)
                    request_body = _json_bytes(payload)
                except Exception as exc:
                    record["status"] = "TECHNICAL_INCOMPLETE"
                    record["technical_error"] = _error(exc)
                    _write_json(record_path, record)
                    failure = {
                        "kind": "local_request",
                        "error": _error(exc),
                        "request_index": request_index,
                    }
                    break
                call_path = root / "calls" / f"call-{call_index:04d}.json"
                call_started = clock()
                call = {
                    "schema_version": 1,
                    "status": "PENDING",
                    "call_index": call_index,
                    "request_index": request_index,
                    "episode_id": episode_id,
                    "round_index": round_index,
                    "attempt_index": attempt_index,
                    "started_at_unix": time.time(),
                    "elapsed_seconds": None,
                    "issued_messages": messages,
                    "issued_messages_sha256": _sha_bytes(_json_bytes(messages)),
                    "request_intent": payload,
                    "request_body": request_body.decode("utf-8"),
                    "request_body_sha256": _sha_bytes(request_body),
                    "native_exchange": None,
                    "tool_call": None,
                    "apply_status": None,
                    "consumer_error": None,
                    "pre_module": states[episode_id],
                    "pre_module_sha256": _sha_text(states[episode_id]),
                    "post_module": states[episode_id],
                    "post_module_sha256": _sha_text(states[episode_id]),
                    "public_checks": [],
                    "unfinished_public_check_ids": [
                        check["check_id"]
                        for check in _public_checks(document, round_index)
                    ],
                    "all_public_passed": False,
                    "technical_error": None,
                }
                _write_json(call_path, call, exclusive=True)
                calls.append(call)
                record["attempts"].append(
                    {
                        "call_index": call_index,
                        "attempt_index": attempt_index,
                        "status": "PENDING",
                        "source_sha256": None,
                        "post_module_sha256": call["post_module_sha256"],
                        "all_public_passed": False,
                    }
                )
                _write_json(record_path, record)

                def persist(exchange, call=call, call_path=call_path):
                    call["native_exchange"] = copy.deepcopy(exchange)
                    _write_json(call_path, call)

                try:
                    action = client.perform(request_body, persist)
                    if action["call_id"] in used_call_ids[episode_id]:
                        raise TechnicalError(
                            "malformed_response", "tool call ID was reused"
                        )
                    used_call_ids[episode_id].add(action["call_id"])
                except TechnicalError as exc:
                    call["status"] = "TECHNICAL_ERROR"
                    call["technical_error"] = _error(exc)
                    call["elapsed_seconds"] = clock() - call_started
                    _write_json(call_path, call)
                    record["attempts"][-1]["status"] = "TECHNICAL_ERROR"
                    record["status"] = "TECHNICAL_INCOMPLETE"
                    record["technical_error"] = _error(exc)
                    _write_json(record_path, record)
                    failure = {
                        "kind": exc.kind,
                        "error": _error(exc),
                        "request_index": request_index,
                        "call_index": call_index,
                    }
                    call_index += 1
                    break
                call["tool_call"] = {
                    "id": action["call_id"],
                    "name": "replace_function",
                    "raw_arguments": action["raw_arguments"],
                    "arguments": action["arguments"],
                }
                source_sha256, source_hash_error = _source_hash(
                    action["arguments"]["source"]
                )
                call["submitted_source_sha256"] = source_sha256
                call["submitted_source_hash_error"] = source_hash_error
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
                    call["apply_status"] = "APPLIED"
                    call["post_module"] = applied.module
                    call["post_module_sha256"] = applied.module_sha256
                    _write_json(call_path, call)
                    _write_text(
                        root
                        / "workspaces"
                        / f"request-{request_index:04d}-attempt-{attempt_index}.py",
                        states[episode_id],
                    )
                    checks_complete = _run_checks_incremental(
                        call,
                        call_path,
                        "public_checks",
                        "unfinished_public_check_ids",
                        states[episode_id],
                        episode_id,
                        _public_checks(document, round_index),
                        deadline=deadline,
                        clock=clock,
                        check_runner=check_runner,
                    )
                    if not checks_complete:
                        call["status"] = "TECHNICAL_ERROR"
                        call["technical_error"] = (
                            "TechnicalError: deadline interrupted public checks"
                        )
                        call["elapsed_seconds"] = clock() - call_started
                        _write_json(call_path, call)
                        record["attempts"][-1]["status"] = "TECHNICAL_ERROR"
                        record["status"] = "TECHNICAL_INCOMPLETE"
                        record["technical_error"] = call["technical_error"]
                        _write_json(record_path, record)
                        failure = {
                            "kind": "deadline",
                            "error": call["technical_error"],
                            "request_index": request_index,
                            "call_index": call_index,
                        }
                        call_index += 1
                        break
                else:
                    call["apply_status"] = "REJECTED"
                    call["consumer_error"] = consumer_error
                    call["unfinished_public_check_ids"] = []
                feedback = _tool_feedback(
                    applied is not None,
                    consumer_error,
                    states[episode_id],
                    call["public_checks"],
                )
                history.append(action["assistant_message"])
                history.append(
                    {
                        "role": "tool",
                        "tool_call_id": action["call_id"],
                        "name": "replace_function",
                        "content": json.dumps(
                            feedback,
                            ensure_ascii=False,
                            sort_keys=True,
                            separators=(",", ":"),
                        ),
                    }
                )
                call["all_public_passed"] = feedback["all_public_passed"]
                call["status"] = "COMPLETE"
                call["elapsed_seconds"] = clock() - call_started
                _write_json(call_path, call)
                record["attempts"][-1].update(
                    status="COMPLETE",
                    source_sha256=source_sha256,
                    post_module_sha256=call["post_module_sha256"],
                    apply_status=call["apply_status"],
                    all_public_passed=call["all_public_passed"],
                )
                _write_json(record_path, record)
                call_index += 1
                _refresh_manifest(manifest, records, calls, started, clock)
                _write_json(manifest_path, manifest)
                if applied is not None and call["all_public_passed"]:
                    public_solved = True
                    break
            if failure is not None:
                break
            record["public_solved"] = public_solved
            record["status"] = "TERMINAL_CHECKS"
            record["post_module_sha256"] = _sha_text(states[episode_id])
            private_checks = _private_checks(document, round_index)
            private_complete = _run_checks_incremental(
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
                record["status"] = "TECHNICAL_INCOMPLETE"
                record["technical_error"] = (
                    "TechnicalError: deadline interrupted private checks"
                )
                _write_json(record_path, record)
                failure = {
                    "kind": "deadline",
                    "error": record["technical_error"],
                    "request_index": request_index,
                }
                break
            record["terminal_private_passed"] = bool(
                record["terminal_private_checks"]
            ) and all(result["passed"] for result in record["terminal_private_checks"])
            record["request_passed"] = (
                public_solved and record["terminal_private_passed"]
            )
            record["status"] = "COMPLETE"
            record["history_after_request"] = copy.deepcopy(history)
            _write_text(
                root / "workspaces" / f"request-{request_index:04d}-terminal.py",
                states[episode_id],
            )
            _write_json(record_path, record)
            request_index += 1
            _refresh_manifest(manifest, records, calls, started, clock)
            _write_json(manifest_path, manifest)

    _finish_manifest(manifest, records, calls, documents, started, clock, failure)
    _write_json(manifest_path, manifest)
    return manifest


def _default_token_counter(text):
    return len(cpu.cpu.slab.qwen_encode(text))


def _conservative_context_bounds(document):
    """Bound growing content without inventing a future generated history."""
    natural_texts = []
    rows = []
    episode_id = document["public"]["episode_id"]
    for round_index, public_round in enumerate(document["public"]["rounds"]):
        natural_texts.extend(
            message["text"] for message in public_round["source_messages"]
        )
        natural_texts.append(public_round["request"]["text"])
        visible_checks = _public_checks(document, round_index)
        current_without_module = CURRENT_PROMPT.format(
            manual_recap=document["private"]["rounds"][round_index]["manual_recap"],
            task_handle=public_round["request"]["task_handle"],
            symbol=public_round["target"]["symbol"],
            path=public_round["target"]["path"],
            quoted_path=json.dumps(public_round["target"]["path"]),
            module="",
            public_checks=json.dumps(
                visible_checks,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
        )
        fixed_content_bytes = sum(
            len(text.encode("utf-8"))
            for text in [SYSTEM_PROMPT, *natural_texts, current_without_module]
        )
        for attempt_index in range(MAX_ATTEMPTS):
            prior_action_rounds = [
                prior_round
                for prior_round in range(round_index)
                for _ in range(MAX_ATTEMPTS)
            ] + [round_index] * attempt_index
            prior_actions = len(prior_action_rounds)
            public_outcome_slots = sum(
                len(_public_checks(document, prior_round))
                for prior_round in prior_action_rounds
            )
            module_observations = prior_actions + 1
            message_count = 2 + len(natural_texts) + 2 * prior_actions
            # Qwen's byte-level fallback cannot need more text tokens than UTF-8
            # bytes. The extra reserve covers fixed chat/tool wrappers. These are
            # absolute contract envelopes, not claims about a future actual prompt.
            wrapper_token_reserve = 4096 + 64 * message_count
            content_byte_bound = (
                fixed_content_bytes
                + cpu.cpu.MAX_MODULE_BYTES
                + prior_actions
                * (6 * cpu.cpu.MAX_MODULE_BYTES + 6 * cpu.MAX_SOURCE_BYTES + 2048)
                + public_outcome_slots * (6 * cpu.cpu.MAX_RESPONSE_BYTES + 1024)
            )
            context_bound = content_byte_bound + wrapper_token_reserve
            rows.append(
                {
                    "episode_id": episode_id,
                    "round_index": round_index,
                    "attempt_index": attempt_index,
                    "prior_action_pairs": prior_actions,
                    "repeated_current_module_observations": module_observations,
                    "public_outcome_slots": public_outcome_slots,
                    "fixed_visible_content_bytes": fixed_content_bytes,
                    "content_utf8_byte_bound": content_byte_bound,
                    "chat_and_tool_wrapper_token_reserve": wrapper_token_reserve,
                    "conservative_prompt_token_bound": context_bound,
                    "context_with_output_bound": context_bound + MAX_OUTPUT_TOKENS,
                    "fits_context": (
                        context_bound + MAX_OUTPUT_TOKENS <= CONTEXT_TOKENS
                    ),
                    "future_actual_prompt_claim": False,
                }
            )
    return rows


def preview(input_paths, *, model="/model", token_counter=_default_token_counter):
    documents, input_receipts = cpu.load_inputs(input_paths)
    if len(documents) != EXPECTED_EPISODES:
        raise ValueError("preview requires exactly four competence episodes")
    client = NativeToolClient("http://127.0.0.1:18088", model)
    reference_actions = []
    cold_requests = []
    context_bounds = []
    max_sandbox_checks = 0
    request_index = 0
    for document in documents:
        context_bounds.extend(_conservative_context_bounds(document))
        history = [{"role": "system", "content": SYSTEM_PROMPT}]
        initial_module = document["public"]["initial_file"]["text"]
        for round_index, public_round in enumerate(document["public"]["rounds"]):
            private_round = document["private"]["rounds"][round_index]
            action_body = _json_bytes({"source": private_round["reference_patch"]})
            action_text = action_body.decode("utf-8")
            argument_tokens = int(token_counter(action_text))
            response_tokens_with_eos = argument_tokens + 1
            headroom = MAX_OUTPUT_TOKENS - response_tokens_with_eos
            reference_actions.append(
                {
                    "request_index": request_index,
                    "episode_id": document["public"]["episode_id"],
                    "round_index": round_index,
                    "target": copy.deepcopy(public_round["target"]),
                    "argument_body": action_text,
                    "argument_body_base64": base64.b64encode(action_body).decode(
                        "ascii"
                    ),
                    "argument_body_sha256": _sha_bytes(action_body),
                    "argument_body_bytes": len(action_body),
                    "source_sha256": _sha_text(private_round["reference_patch"]),
                    "argument_tokens": argument_tokens,
                    "eos_allowance_tokens": 1,
                    "response_tokens_with_eos": response_tokens_with_eos,
                    "generation_headroom": headroom,
                    "eligible": headroom >= cpu.MIN_GENERATION_HEADROOM,
                }
            )
            max_sandbox_checks += MAX_ATTEMPTS * len(
                _public_checks(document, round_index)
            ) + len(_private_checks(document, round_index))
            if round_index == 0:
                _append_natural(history, public_round)
                issued = build_issued_messages(
                    document, history, round_index, initial_module
                )
                payload = client.payload(issued)
                payload_body = _json_bytes(payload)
                serialized_tokens = int(token_counter(payload_body.decode("utf-8")))
                cold_requests.append(
                    {
                        "request_index": request_index,
                        "episode_id": document["public"]["episode_id"],
                        "round_index": round_index,
                        "messages": issued,
                        "messages_sha256": _sha_bytes(_json_bytes(issued)),
                        "request_body_sha256": _sha_bytes(payload_body),
                        "request_body_bytes": len(payload_body),
                        "local_serialized_request_tokens": serialized_tokens,
                        "local_serialized_request_with_output": (
                            serialized_tokens + MAX_OUTPUT_TOKENS
                        ),
                        "local_serialized_request_below_context": (
                            serialized_tokens + MAX_OUTPUT_TOKENS <= CONTEXT_TOKENS
                        ),
                        "local_count_is_native_prompt_tokens": False,
                    }
                )
            request_index += 1
    all_headroom = all(item["eligible"] for item in reference_actions)
    return {
        "schema_version": 1,
        "kind": "coding-competence-native-preview",
        "status": "PASS" if all_headroom else "INELIGIBLE",
        "model_calls": 0,
        "documents": len(documents),
        "scheduled_requests": PLANNED_REQUESTS,
        "max_attempts_per_request": MAX_ATTEMPTS,
        "max_model_calls": MAX_MODEL_CALLS,
        "settings": {
            "model": model,
            "max_output_tokens": MAX_OUTPUT_TOKENS,
            "context_tokens": CONTEXT_TOKENS,
            "minimum_generation_headroom": cpu.MIN_GENERATION_HEADROOM,
            "seed": SEED,
            "temperature": 0,
        },
        "inputs": input_receipts,
        "code_sha256": _code_hashes(),
        "reference_actions": reference_actions,
        "all_reference_actions_headroom": all_headroom,
        "context_preflight": {
            "actual_cold_request_count": len(cold_requests),
            "cold_requests": cold_requests,
            "later_actual_requests_known": False,
            "local_counts_are_provisional": True,
            "all_local_cold_serializations_below_context": all(
                item["local_serialized_request_below_context"] for item in cold_requests
            ),
            "authoritative_render_required_before_every_model_call": True,
            "conservative_bounds": context_bounds,
            "all_conservative_bounds_fit": all(
                item["fits_context"] for item in context_bounds
            ),
            "bound_interpretation": (
                "Absolute allowed-size envelopes; they do not serialize gold "
                "histories or predict future actual prompts."
            ),
        },
        "resource_bounds": {
            "maximum_render_requests": MAX_MODEL_CALLS,
            "maximum_generation_requests": MAX_MODEL_CALLS,
            "maximum_http_requests": 2 * MAX_MODEL_CALLS,
            "maximum_sandbox_checks": max_sandbox_checks,
            "maximum_prior_action_pairs_per_prompt": max(
                item["prior_action_pairs"] for item in context_bounds
            ),
            "maximum_repeated_module_observations_per_prompt": max(
                item["repeated_current_module_observations"] for item in context_bounds
            ),
        },
    }


def _parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", action="append", required=True)
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
    if args.preview:
        try:
            result = preview(args.input, model=args.model)
        except Exception as exc:
            result = {
                "schema_version": 1,
                "kind": "coding-competence-native-preview",
                "status": "INVALID",
                "model_calls": 0,
                "error": _error(exc),
            }
        print(json.dumps(result, ensure_ascii=True, sort_keys=True), flush=True)
        return 0 if result["status"] == "PASS" else 2
    if args.output_dir is None:
        raise ValueError("--output-dir is required unless --preview is used")
    client = NativeToolClient(args.base_url, args.model)
    try:
        result = run(
            args.input,
            args.output_dir,
            client,
            deadline_seconds=args.deadline_seconds,
            runtime_args=sys.argv[1:] if argv is None else argv,
        )
    except Exception as exc:
        result = {
            "schema_version": 1,
            "kind": "coding-competence-native-run",
            "status": "INCOMPLETE",
            "mechanical_go": False,
            "competence_go": None,
            "error": _error(exc),
        }
    print(json.dumps(result, ensure_ascii=True, sort_keys=True), flush=True)
    if result["status"] != "COMPLETE":
        return 2
    return 0 if result["mechanical_go"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
