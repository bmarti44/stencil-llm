#!/usr/bin/env python3
"""Native-message 72-call runner for the same-response coding focus DEV screen."""

import argparse
import base64
import copy
import hashlib
import json
import os
import sys
import tempfile
import time
from collections.abc import Mapping
from functools import lru_cache
from http.client import IncompleteRead
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request as HTTPRequest
from urllib.request import urlopen

try:
    from scripts import coding_worker_dev as cpu
except ModuleNotFoundError as exc:  # Direct ``python scripts/...`` invocation.
    if exc.name != "scripts":
        raise
    import coding_worker_dev as cpu
from stencil.focus import renderer as focus_renderer

ARMS = ("H", "C", "M")
EXPECTED_EPISODES = 4
EXPECTED_ROUNDS = 6
EXPECTED_CALLS = 72
MAX_OUTPUT_TOKENS = 768
CONTEXT_TOKENS = 32_768
RECEIPT_RESERVE_SECONDS = 1.0
REQUEST_TIMEOUT_SECONDS = 600.0
SEED = 20260907
SYSTEM_PROMPT = (
    "Maintain the Python module across this conversation. Each request asks for "
    "one complete target function. Your response may contain brief prose before "
    "the code, then exactly one code fence whose opening line is ```python PATH. "
    "Inside the fence, submit exactly the requested synchronous function with its "
    "def at column zero and one positional argument. Do not submit other functions, "
    "a whole module, imports, tests, tool calls, or prose after the fence. Preserve "
    "the requested behavior and the standing user obligations that apply now."
)
COMMON_CURRENT = (
    "Submit the complete requested function under the response format above. "
    "The module shown here is this arm's actual current state."
)
C_CURRENT = (
    "Before the code fence, briefly recap all and only the standing obligations "
    "that apply to this request, including their scope, strength, and exceptions. "
    "Then submit the complete requested function in the same response."
)
M_CURRENT = (
    "For this request only, use the independently prepared reminder below. It is "
    "ephemeral and must not be treated as a new standing instruction.\n"
    "Applicable obligations:\n{manual_recap}"
)


class NativeDecodeError(RuntimeError):
    """A native chat exchange cannot safely produce a candidate response."""


class ContextLimitError(NativeDecodeError):
    """An exact outgoing native prompt does not fit the registered context."""


def _json_bytes(value):
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _sha_json(value):
    return hashlib.sha256(_json_bytes(value)).hexdigest()


def _sha_text(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _error(exc):
    return f"{type(exc).__name__}: {exc}"


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


def _append_jsonl(handle, value):
    handle.write(json.dumps(value, ensure_ascii=True, sort_keys=True) + "\n")
    handle.flush()


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
        "body_sha256": hashlib.sha256(body).hexdigest(),
        "body_bytes": len(body),
    }
    if incomplete_expected_bytes is not None:
        receipt["incomplete_read_expected_bytes"] = incomplete_expected_bytes
    return receipt


def _validate_usage(usage, max_tokens):
    if type(usage) is not dict:
        raise ValueError("response usage must be an object")
    counts = {}
    for name in ("prompt_tokens", "completion_tokens", "total_tokens"):
        value = usage.get(name)
        if type(value) is not int or value < 0:
            raise ValueError(f"usage.{name} must be a nonnegative integer")
        counts[name] = value
    if counts["total_tokens"] != (
        counts["prompt_tokens"] + counts["completion_tokens"]
    ):
        raise ValueError("usage.total_tokens does not equal prompt plus completion")
    if counts["completion_tokens"] > max_tokens:
        raise ValueError("usage.completion_tokens exceeds the output cap")


def _validate_messages(messages):
    if type(messages) is not list or not messages:
        raise TypeError("native messages must be a nonempty list")
    checked = []
    for index, message in enumerate(messages):
        if type(message) is not dict or set(message) != {"role", "content"}:
            raise TypeError(f"message {index} must contain role and content")
        if message["role"] not in {"system", "user", "assistant"}:
            raise ValueError(f"unsupported native role at message {index}")
        if not isinstance(message["content"], str):
            raise TypeError(f"message {index} content must be a string")
        message["content"].encode("utf-8")
        checked.append(dict(message))
    return checked


class NativeChatDecoder:
    """One native-role request to an already-running chat-completions server."""

    def __init__(self, base_url, model, max_tokens=MAX_OUTPUT_TOKENS, *, opener=None):
        if type(max_tokens) is not int or max_tokens != MAX_OUTPUT_TOKENS:
            raise ValueError("coding screen requires max_tokens=768")
        base_url = str(base_url).rstrip("/")
        if not base_url.startswith(("http://", "https://")):
            base_url = "http://" + base_url
        self.endpoint = base_url + "/v1/chat/completions"
        self.model = str(model)
        self.max_tokens = max_tokens
        self.opener = opener or urlopen
        self.deadline = None
        self.last_http = None

    def set_deadline(self, deadline):
        self.deadline = deadline

    def _timeout(self):
        if self.deadline is None:
            return REQUEST_TIMEOUT_SECONDS
        remaining = self.deadline - time.monotonic() - RECEIPT_RESERVE_SECONDS
        if remaining <= 0:
            raise NativeDecodeError("deadline leaves no time for a receipt")
        return min(REQUEST_TIMEOUT_SECONDS, remaining)

    def payload(self, messages):
        return {
            "model": self.model,
            "messages": _validate_messages(messages),
            "max_tokens": self.max_tokens,
            "temperature": 0,
            "seed": SEED,
            "chat_template_kwargs": {"enable_thinking": False},
        }

    def __call__(self, messages):
        payload = self.payload(messages)
        request_body = _json_bytes(payload)
        timeout = self._timeout()
        request = HTTPRequest(
            self.endpoint,
            data=request_body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        exchange = {
            "request": {
                "url": self.endpoint,
                "method": "POST",
                "headers": {"Content-Type": "application/json"},
                "timeout_seconds": timeout,
                "body": request_body.decode("utf-8"),
                "body_base64": base64.b64encode(request_body).decode("ascii"),
                "body_sha256": hashlib.sha256(request_body).hexdigest(),
                "body_bytes": len(request_body),
                "json": payload,
            },
            "response": None,
            "finish_reason": None,
            "raw_output": None,
            "usage": None,
            "failure_kind": None,
            "error": None,
        }
        self.last_http = exchange
        try:
            with self.opener(request, timeout=timeout) as response:
                try:
                    body = response.read()
                except IncompleteRead as exc:
                    exchange["response"] = _response_receipt(
                        response,
                        exc.partial,
                        incomplete_expected_bytes=exc.expected,
                    )
                    raise NativeDecodeError(
                        f"HTTP response read failure: {_error(exc)}"
                    ) from exc
                exchange["response"] = _response_receipt(response, body)
        except NativeDecodeError as exc:
            exchange["error"] = _error(exc)
            raise
        except HTTPError as exc:
            incomplete = None
            try:
                body = exc.read()
            except IncompleteRead as read_exc:
                body = read_exc.partial
                incomplete = read_exc.expected
            exchange["response"] = _response_receipt(
                exc, body, incomplete_expected_bytes=incomplete
            )
            exchange["error"] = _error(exc)
            raise NativeDecodeError(f"HTTP transport failure: {exc}") from exc
        except Exception as exc:
            exchange["error"] = _error(exc)
            raise NativeDecodeError(f"HTTP transport failure: {exc}") from exc
        try:
            parsed = json.loads(body.decode("utf-8"))
            choices = parsed["choices"]
            if type(choices) is not list or len(choices) != 1:
                raise ValueError("response must contain exactly one choice")
            choice = choices[0]
            content = choice["message"]["content"]
            finish_reason = choice["finish_reason"]
            if not isinstance(content, str):
                raise ValueError("assistant content must be a string")
            exchange["finish_reason"] = finish_reason
            exchange["raw_output"] = content
            exchange["usage"] = parsed.get("usage")
            exchange["response"]["json"] = parsed
            try:
                _validate_usage(exchange["usage"], self.max_tokens)
            except ValueError:
                exchange["failure_kind"] = "token_accounting"
                raise
            if finish_reason == "length":
                raise NativeDecodeError("finish_reason=length: output cap reached")
            if finish_reason != "stop":
                raise ValueError(f"unsupported finish_reason: {finish_reason!r}")
            return content
        except NativeDecodeError as exc:
            exchange["error"] = _error(exc)
            raise
        except UnicodeDecodeError as exc:
            exchange["error"] = _error(exc)
            raise NativeDecodeError(f"response is not valid UTF-8: {exc}") from exc
        except Exception as exc:
            exchange["error"] = _error(exc)
            raise NativeDecodeError(f"invalid chat response: {exc}") from exc


@lru_cache(maxsize=1)
def _chat_tokenizer():
    from transformers import AutoTokenizer

    model = Path(__file__).resolve().parents[1] / "models/qwen3-30b-a3b-hf"
    return AutoTokenizer.from_pretrained(str(model), local_files_only=True)


def native_prompt_tokens(messages):
    messages = _validate_messages(messages)
    encoded = _chat_tokenizer().apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        enable_thinking=False,
    )
    if isinstance(encoded, Mapping):
        if "input_ids" not in encoded:
            raise TypeError("chat template encoding lacks input_ids")
        ids = encoded["input_ids"]
    else:
        ids = encoded
    if hasattr(ids, "tolist"):
        ids = ids.tolist()
    if type(ids) is list and len(ids) == 1 and type(ids[0]) is list:
        ids = ids[0]
    if type(ids) is not list or any(type(item) is not int for item in ids):
        raise TypeError("chat template input_ids have an unsupported shape")
    return len(ids)


def _current_content(round_, module_text, arm):
    target = round_["target"]
    sections = [
        round_["request"]["text"],
        COMMON_CURRENT,
        f"Current task handle: {round_['request']['task_handle']}",
        f"Requested target: {target['symbol']} in {target['path']}",
        f"<current_module path={json.dumps(target['path'])}>\n"
        f"{module_text}\n</current_module>",
    ]
    if arm == "C":
        sections.append(C_CURRENT)
    elif arm == "M":
        sections.append(M_CURRENT.format(manual_recap=round_["manual_recap"]))
    elif arm != "H":
        raise ValueError(f"unknown arm: {arm}")
    return "\n\n".join(sections)


def build_issued_messages(canonical, round_, module_text, arm):
    messages = copy.deepcopy(canonical)
    messages[-1] = {
        "role": "user",
        "content": _current_content(round_, module_text, arm),
    }
    return _validate_messages(messages)


def _append_natural(canonical, round_):
    for message in round_["source_messages"]:
        canonical.append({"role": message["role"], "content": message["text"]})
    canonical.append({"role": "user", "content": round_["request"]["text"]})


def _prepare_output(directory):
    root = Path(directory)
    if root.exists():
        if not root.is_dir() or any(root.iterdir()):
            raise FileExistsError("refuse existing nonempty output directory")
    else:
        root.mkdir(parents=True)
    for name in ("calls", "turns", "workspaces"):
        (root / name).mkdir()
    return root


def _code_hashes():
    root = Path(__file__).resolve().parents[1]
    paths = {
        Path(__file__).resolve(),
        Path(cpu.__file__).resolve(),
        Path(cpu.slab.__file__).resolve(),
        Path(cpu.slab.__file__).with_name("slab_sandbox.py").resolve(),
        Path(focus_renderer.__file__).resolve(),
    }
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(paths, key=str)
    }


def _decoder_receipt(
    decoder,
    messages,
    path,
    *,
    call_index,
    episode_id,
    arm,
    round_index,
    prompt_tokens,
    pre_error=None,
    clock=time.monotonic,
    wall_clock=time.time,
):
    started_at = wall_clock()
    started = clock()
    raw_output = None
    error = pre_error
    if hasattr(decoder, "last_http"):
        decoder.last_http = None
    request_intent = None
    payload_builder = getattr(decoder, "payload", None)
    if error is None and callable(payload_builder):
        try:
            request_intent = payload_builder(messages)
        except Exception as exc:
            error = _error(exc)
    receipt = {
        "schema_version": 1,
        "status": "PENDING",
        "call_index": call_index,
        "episode_id": episode_id,
        "arm": arm,
        "round_index": round_index,
        "started_at_unix": started_at,
        "elapsed_seconds": None,
        "issued_messages": messages,
        "issued_messages_sha256": _sha_json(messages),
        "local_prompt_tokens": prompt_tokens,
        "request_intent": request_intent,
        "raw_output": None,
        "decoder_error": error,
        "failure_kind": None,
        "http": None,
    }
    _write_json(path, receipt, exclusive=True)
    if error is None:
        try:
            raw_output = decoder(messages)
            if not isinstance(raw_output, str):
                raise TypeError("decoder must return a string")
        except Exception as exc:
            error = _error(exc)
    http = getattr(decoder, "last_http", None)
    if raw_output is None and isinstance(http, dict):
        raw_output = http.get("raw_output")
    failure_kind = None
    if error is not None:
        if isinstance(http, dict) and http.get("finish_reason") == "length":
            failure_kind = "capacity"
        elif isinstance(http, dict) and http.get("failure_kind") == "token_accounting":
            failure_kind = "token_accounting"
        elif pre_error is not None and "ContextLimitError" in pre_error:
            failure_kind = "capacity"
        elif pre_error is not None:
            failure_kind = "local_prompt_error"
        else:
            failure_kind = "transport"
    receipt.update(
        status="COMPLETE" if error is None else "ERROR",
        elapsed_seconds=clock() - started,
        raw_output=raw_output,
        decoder_error=error,
        failure_kind=failure_kind,
        http=http,
    )
    _write_json(path, receipt)
    return raw_output, error, receipt


def _run_checks_incremental(
    turn_record,
    turn_path,
    module_text,
    checks,
    *,
    deadline,
    clock,
    check_runner,
):
    for index, check in enumerate(checks):
        if clock() >= deadline - RECEIPT_RESERVE_SECONDS:
            turn_record["check_status"] = "INCOMPLETE_DEADLINE"
            turn_record["unfinished_check_ids"] = [
                item["check_id"] for item in checks[index:]
            ]
            _write_json(turn_path, turn_record)
            return False
        try:
            result = check_runner(module_text, [check])[0]
        except Exception as exc:
            result = {
                "check_id": check["check_id"],
                "symbol": check["symbol"],
                "rule_ids": list(check["rule_ids"]),
                "passed": False,
                "actual": None,
                "expected_values": check["expected_values"],
                "error": _error(exc),
                "elapsed_seconds": None,
            }
        result["episode_id"] = turn_record["episode_id"]
        turn_record["checks"].append(result)
        turn_record["unfinished_check_ids"] = [
            item["check_id"] for item in checks[index + 1 :]
        ]
        _write_json(turn_path, turn_record)
    turn_record["check_status"] = "COMPLETE"
    _write_json(turn_path, turn_record)
    return True


def _new_lane(episode, arm):
    initial = episode["initial_file"]["text"]
    return {
        "episode_id": episode["episode_id"],
        "arm": arm,
        "module": initial,
        "canonical": [{"role": "system", "content": SYSTEM_PROMPT}],
    }


def run(
    input_paths,
    output_dir,
    decoder,
    *,
    deadline_seconds,
    runtime_args=None,
    token_counter=native_prompt_tokens,
    check_runner=cpu.run_checks,
    clock=time.monotonic,
    wall_clock=time.time,
):
    documents, input_receipts = cpu.load_inputs(input_paths)
    if len(documents) != EXPECTED_EPISODES:
        raise ValueError("worker runner requires exactly four DEV episodes")
    if not (
        callable(decoder) and callable(token_counter) and callable(check_runner)
    ):
        raise TypeError("decoder, token counter, and check runner must be callable")
    if hasattr(decoder, "max_tokens") and decoder.max_tokens != MAX_OUTPUT_TOKENS:
        raise ValueError("coding screen requires decoder max_tokens=768")
    if not isinstance(deadline_seconds, (int, float)) or deadline_seconds <= 0:
        raise ValueError("deadline_seconds must be positive")
    root = _prepare_output(output_dir)
    started = clock()
    deadline = started + float(deadline_seconds)
    if hasattr(decoder, "set_deadline"):
        decoder.set_deadline(deadline)
    episodes = [document["episode"] for document in documents]
    lanes = {
        (episode["episode_id"], arm): _new_lane(episode, arm)
        for episode in episodes
        for arm in ARMS
    }
    manifest = {
        "schema_version": 1,
        "status": "INCOMPLETE",
        "reason": "run not completed",
        "started_at_unix": wall_clock(),
        "finished_at_unix": None,
        "elapsed_seconds": None,
        "development_only": True,
        "data_lineage": {
            "fit_on": "none",
            "development_on": "reviewed coding-self-cue DEV bank",
            "evaluated_on": "none",
        },
        "inputs": input_receipts,
        "code_sha256": _code_hashes(),
        "runtime_args": list(runtime_args) if runtime_args is not None else None,
        "runtime_config": {
            "arms": list(ARMS),
            "deadline_seconds": float(deadline_seconds),
            "max_output_tokens": MAX_OUTPUT_TOKENS,
            "context_tokens": CONTEXT_TOKENS,
            "retries": 0,
            "test_feedback_in_prompts": False,
        },
        "scheduled_episodes": EXPECTED_EPISODES,
        "scheduled_rounds": EXPECTED_ROUNDS,
        "scheduled_calls": EXPECTED_CALLS,
        "recorded_calls": 0,
        "network_attempts": 0,
        "completed_check_sets": 0,
        "technically_complete_calls": 0,
        "call_errors": 0,
        "transport_failures": 0,
        "capacity_failures": 0,
        "local_prompt_failures": 0,
        "token_accounting_failures": 0,
        "accounting_complete": False,
        "rows_path": "rows.jsonl",
        "calls_path": "calls",
        "turns_path": "turns",
        "workspaces_path": "workspaces",
    }
    _write_json(root / "manifest.json", manifest)
    stop_reason = None
    call_index = 0
    with (root / "rows.jsonl").open("x", encoding="utf-8") as rows:
        for episode in episodes:
            for round_index, round_ in enumerate(episode["rounds"]):
                for arm in ARMS:
                    if clock() >= deadline - RECEIPT_RESERVE_SECONDS:
                        stop_reason = "deadline before next scheduled call"
                        break
                    lane = lanes[(episode["episode_id"], arm)]
                    canonical_before = copy.deepcopy(lane["canonical"])
                    _append_natural(lane["canonical"], round_)
                    canonical_natural = copy.deepcopy(lane["canonical"])
                    issued = build_issued_messages(
                        lane["canonical"], round_, lane["module"], arm
                    )
                    prompt_tokens = None
                    pre_error = None
                    try:
                        prompt_tokens = int(token_counter(issued))
                        if prompt_tokens + MAX_OUTPUT_TOKENS > CONTEXT_TOKENS:
                            raise ContextLimitError(
                                f"{prompt_tokens}+{MAX_OUTPUT_TOKENS} exceeds context"
                            )
                    except Exception as exc:
                        pre_error = _error(exc)
                    call_path = root / "calls" / f"call-{call_index:04d}.json"
                    raw_output, decoder_error, receipt = _decoder_receipt(
                        decoder,
                        issued,
                        call_path,
                        call_index=call_index,
                        episode_id=episode["episode_id"],
                        arm=arm,
                        round_index=round_index,
                        prompt_tokens=prompt_tokens,
                        pre_error=pre_error,
                        clock=clock,
                        wall_clock=wall_clock,
                    )
                    pre_module = lane["module"]
                    post_module = pre_module
                    parsed = None
                    parse_error = None
                    if decoder_error is None:
                        try:
                            candidate = cpu.parse_response(
                                raw_output,
                                round_["target"]["path"],
                                round_["target"]["symbol"],
                            )
                            post_module = cpu.splice_function(
                                pre_module, candidate.code, candidate.symbol
                            )
                            parsed = candidate
                            lane["module"] = post_module
                            lane["canonical"].append(
                                {"role": "assistant", "content": parsed.fence}
                            )
                        except Exception as exc:
                            parse_error = _error(exc)
                    stable, obligations = cpu._active_checks(episode, round_index)
                    active = stable + obligations
                    turn_path = root / "turns" / f"turn-{call_index:04d}.json"
                    turn_record = {
                        "schema_version": 1,
                        "call_index": call_index,
                        "episode_id": episode["episode_id"],
                        "arm": arm,
                        "round_index": round_index,
                        "source_message_ids": [
                            item["message_id"] for item in round_["source_messages"]
                        ],
                        "request_id": round_["request"]["message_id"],
                        "task_handle": round_["request"]["task_handle"],
                        "target": dict(round_["target"]),
                        "call_receipt": str(call_path.relative_to(root)),
                        "issued_messages_sha256": receipt["issued_messages_sha256"],
                        "raw_output": raw_output,
                        "decoder_error": decoder_error,
                        "parse_error": parse_error,
                        "extracted_prefix": parsed.prefix if parsed else None,
                        "extracted_fence": parsed.fence if parsed else None,
                        "pre_module": pre_module,
                        "pre_module_sha256": _sha_text(pre_module),
                        "post_module": post_module,
                        "post_module_sha256": _sha_text(post_module),
                        "patch_applied": parsed is not None,
                        "canonical_history_before": canonical_before,
                        "canonical_history_natural": canonical_natural,
                        "canonical_history_after": copy.deepcopy(lane["canonical"]),
                        "canonical_history_after_sha256": _sha_json(lane["canonical"]),
                        "check_status": "PENDING",
                        "checks": [],
                        "unfinished_check_ids": [item["check_id"] for item in active],
                    }
                    _write_json(turn_path, turn_record, exclusive=True)
                    manifest["recorded_calls"] += 1
                    http = receipt.get("http")
                    manifest["network_attempts"] += int(
                        isinstance(http, dict) and isinstance(http.get("request"), dict)
                    )
                    manifest["call_errors"] += int(
                        decoder_error is not None or parse_error is not None
                    )
                    kind = receipt.get("failure_kind")
                    failure_counter = {
                        "transport": "transport_failures",
                        "capacity": "capacity_failures",
                        "local_prompt_error": "local_prompt_failures",
                        "token_accounting": "token_accounting_failures",
                    }.get(kind)
                    if failure_counter is not None:
                        manifest[failure_counter] += 1
                    _write_json(root / "manifest.json", manifest)
                    checks_complete = _run_checks_incremental(
                        turn_record,
                        turn_path,
                        post_module,
                        active,
                        deadline=deadline,
                        clock=clock,
                        check_runner=check_runner,
                    )
                    if checks_complete:
                        manifest["completed_check_sets"] += 1
                    all_checks_passed = checks_complete and all(
                        item["passed"] for item in turn_record["checks"]
                    )
                    turn_record["submission_valid"] = parsed is not None
                    turn_record["all_checks_passed"] = all_checks_passed
                    turn_record["turn_success"] = bool(
                        parsed is not None and all_checks_passed
                    )
                    turn_record["slot_accounting_complete"] = checks_complete
                    turn_record["technical_complete"] = bool(
                        checks_complete and decoder_error is None
                    )
                    manifest["technically_complete_calls"] += int(
                        turn_record["technical_complete"]
                    )
                    _write_json(turn_path, turn_record)
                    workspace = (
                        root
                        / "workspaces"
                        / episode["episode_id"]
                        / arm
                        / f"round-{round_index}.py"
                    )
                    workspace.parent.mkdir(parents=True, exist_ok=True)
                    workspace.write_text(post_module, encoding="utf-8")
                    row = {
                        key: value
                        for key, value in turn_record.items()
                        if key not in {
                            "pre_module",
                            "post_module",
                            "canonical_history_before",
                            "canonical_history_natural",
                            "canonical_history_after",
                        }
                    }
                    row["turn_record"] = str(turn_path.relative_to(root))
                    row["workspace"] = str(workspace.relative_to(root))
                    _append_jsonl(rows, row)
                    _write_json(root / "manifest.json", manifest)
                    call_index += 1
                    if not checks_complete:
                        stop_reason = "deadline during executable checks"
                        break
                    if pre_error is not None:
                        stop_reason = "context or local token gate rejected a call"
                        break
                if stop_reason:
                    break
            if stop_reason:
                break
    elapsed = clock() - started
    complete = (
        stop_reason is None
        and manifest["recorded_calls"] == EXPECTED_CALLS
        and manifest["completed_check_sets"] == EXPECTED_CALLS
        and manifest["technically_complete_calls"] == EXPECTED_CALLS
        and elapsed <= deadline_seconds
    )
    manifest["accounting_complete"] = bool(
        manifest["recorded_calls"] == EXPECTED_CALLS
        and manifest["completed_check_sets"] == EXPECTED_CALLS
    )
    incomplete_reason = stop_reason
    if incomplete_reason is None and manifest["accounting_complete"] and not complete:
        if manifest["capacity_failures"]:
            incomplete_reason = "one or more capacity-ineligible calls"
        elif manifest["token_accounting_failures"]:
            incomplete_reason = "one or more token-accounting-incomplete calls"
        elif manifest["transport_failures"]:
            incomplete_reason = "one or more transport-incomplete calls"
        else:
            incomplete_reason = "one or more locally incomplete calls"
    manifest.update(
        status="COMPLETE" if complete else "INCOMPLETE",
        reason=(
            None
            if complete
            else incomplete_reason or "accounting or deadline incomplete"
        ),
        finished_at_unix=wall_clock(),
        elapsed_seconds=elapsed,
    )
    _write_json(root / "manifest.json", manifest)
    return manifest


def _conservative_bounds(episode, token_counter):
    lane = _new_lane(episode, "H")
    rows = []
    prior_targets = set()
    for index, round_ in enumerate(episode["rounds"]):
        _append_natural(lane["canonical"], round_)
        for arm in ARMS:
            issued = build_issued_messages(
                lane["canonical"],
                round_,
                episode["initial_file"]["text"],
                arm,
            )
            base = int(token_counter(issued))
            generated_artifacts = index + len(prior_targets)
            bound = base + generated_artifacts * (MAX_OUTPUT_TOKENS + 64)
            rows.append(
                {
                    "episode_id": episode["episode_id"],
                    "round_index": index,
                    "arm": arm,
                    "actual_prompt": index == 0,
                    "base_tokens_with_empty_generated_history": base,
                    "generated_artifact_allowance": generated_artifacts,
                    "conservative_prompt_bound": bound,
                    "context_with_output_bound": bound + MAX_OUTPUT_TOKENS,
                    "eligible": bound + MAX_OUTPUT_TOKENS <= CONTEXT_TOKENS,
                }
            )
        lane["canonical"].append({"role": "assistant", "content": ""})
        prior_targets.add(round_["target"]["symbol"])
    return rows


def preview(input_paths, *, model="/model", token_counter=native_prompt_tokens):
    documents, input_receipts = cpu.load_inputs(input_paths)
    if len(documents) != EXPECTED_EPISODES:
        raise ValueError("preview requires exactly four DEV episodes")
    decoder = NativeChatDecoder("http://127.0.0.1:18088", model)
    cold = []
    bounds = []
    for document in documents:
        episode = document["episode"]
        round_ = episode["rounds"][0]
        for arm in ARMS:
            lane = _new_lane(episode, arm)
            _append_natural(lane["canonical"], round_)
            issued = build_issued_messages(
                lane["canonical"], round_, lane["module"], arm
            )
            payload = decoder.payload(issued)
            cold.append(
                {
                    "episode_id": episode["episode_id"],
                    "round_index": 0,
                    "arm": arm,
                    "actual_cold_prompt": True,
                    "messages": issued,
                    "messages_sha256": _sha_json(issued),
                    "request_body_sha256": hashlib.sha256(
                        _json_bytes(payload)
                    ).hexdigest(),
                    "prompt_tokens": int(token_counter(issued)),
                }
            )
        bounds.extend(_conservative_bounds(episode, token_counter))
    return {
        "schema_version": 1,
        "kind": "coding-self-cue-native-preview",
        "model_calls": 0,
        "actual_cold_prompt_count": len(cold),
        "later_actual_prompts_known": False,
        "inputs": input_receipts,
        "cold_prompts": cold,
        "conservative_context_bounds": bounds,
        "all_context_bounds_eligible": all(item["eligible"] for item in bounds),
        "code_sha256": _code_hashes(),
    }


def _parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", action="append", required=True)
    parser.add_argument("--output-dir")
    parser.add_argument("--base-url", default="http://127.0.0.1:18088")
    parser.add_argument("--model", default="/model")
    parser.add_argument("--max-tokens", type=int, default=MAX_OUTPUT_TOKENS)
    parser.add_argument("--deadline-seconds", type=float, default=3000.0)
    parser.add_argument("--preview", action="store_true")
    return parser


def main(argv=None):
    runtime_args = list(sys.argv[1:] if argv is None else argv)
    args = _parser().parse_args(runtime_args)
    if args.max_tokens != MAX_OUTPUT_TOKENS:
        raise ValueError("coding screen requires --max-tokens 768")
    if args.preview:
        print(json.dumps(preview(args.input, model=args.model), ensure_ascii=True))
        return 0
    if not args.output_dir:
        raise ValueError("--output-dir is required unless --preview is used")
    decoder = NativeChatDecoder(args.base_url, args.model, args.max_tokens)
    result = run(
        args.input,
        args.output_dir,
        decoder,
        deadline_seconds=args.deadline_seconds,
        runtime_args=runtime_args,
    )
    print(json.dumps(result, ensure_ascii=True, sort_keys=True), flush=True)
    return 0 if result["status"] == "COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
