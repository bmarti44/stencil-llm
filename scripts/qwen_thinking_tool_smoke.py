#!/usr/bin/env python3
"""Bounded Qwen thinking plus native replace-function compatibility check."""

import argparse
import base64
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
from scripts import coding_competence_run as native  # noqa: E402
from src.stencil.focus import slab  # noqa: E402

FIXTURE_ID = "builtin:qwen-thinking-tool-smoke-v1"
FIXTURE_PATH = "fixture.py"
TARGET_SYMBOL = "transform"
INITIAL_MODULE = """def identity(value):
    return value


def transform(value):
    return identity(value)
"""
SYSTEM_PROMPT = (
    "Maintain the supplied tiny pure-Python module. Respond with exactly one "
    "replace_function tool call. Its source must be one complete synchronous "
    "function named transform, beginning with def at byte zero, using LF lines "
    "and exactly one positional argument without defaults, varargs or keyword-only "
    "arguments. Do not use decorators, imports, global, nonlocal, nested functions "
    "or classes, dunder names or attributes, Markdown, or calls to __import__, "
    "breakpoint, compile, eval, exec, exit, globals, help, input, locals, open, "
    "print, quit or vars. The consumer only compiles and replaces that authenticated "
    "function; it does not execute the generated code."
)
FIRST_REQUEST = (
    "Replace transform with a simple implementation that returns a JSON-like "
    "object containing the input under the key value.\n"
    f"Authenticated target: {TARGET_SYMBOL} in {FIXTURE_PATH}\n"
    f"<current_module>\n{INITIAL_MODULE}</current_module>"
)
SECOND_REQUEST = (
    "Replace transform once more with a simple implementation that also marks "
    "the object as revised. Use the actual current module below.\n"
    f"Authenticated target: {TARGET_SYMBOL} in {FIXTURE_PATH}\n"
    "<current_module>\n{module}</current_module>"
)

MAX_CALLS = 2
MAX_OUTPUT_TOKENS = 2048
THINKING_TOKEN_BUDGET = 512
CONTEXT_TOKENS = 32_768
DEFAULT_DEADLINE_SECONDS = 540.0
SEED = 20260908
TEMPERATURE = 0.6
TOP_P = 0.95
TOP_K = 20
MIN_P = 0.0

ARGUMENT_SCHEMA = copy.deepcopy(cpu.REPLACE_FUNCTION_TOOL["function"]["parameters"])
EOS_CONFIG_PATH = ROOT / "models/qwen3-30b-a3b-hf/generation_config.json"
TOKENIZER_FILES = (
    "models/qwen3-30b-a3b-hf/tokenizer.json",
    "models/qwen3-30b-a3b-hf/tokenizer_config.json",
    "models/qwen3-30b-a3b-hf/config.json",
    "models/qwen3-30b-a3b-hf/generation_config.json",
)
SOURCE_FILES = (
    "scripts/qwen_thinking_tool_smoke.py",
    "tests/test_qwen_thinking_tool_smoke.py",
    "tools/run_qwen_thinking_tool_smoke.py",
    "tests/test_run_qwen_thinking_tool_smoke.py",
    "scripts/coding_competence_run.py",
    "scripts/coding_competence_dev.py",
    "scripts/coding_worker_dev.py",
    "src/stencil/focus/slab.py",
    "src/stencil/focus/slab_sandbox.py",
    "tools/run_coding_competence.py",
    *TOKENIZER_FILES,
)


def _hash_bytes(value):
    return hashlib.sha256(value).hexdigest()


def _hash_text(value):
    return _hash_bytes(value.encode("utf-8"))


def _source_hashes():
    return {
        relative: _hash_bytes((ROOT / relative).read_bytes())
        for relative in SOURCE_FILES
        if (ROOT / relative).is_file()
    }


def _fixture_receipt():
    value = {
        "identifier": FIXTURE_ID,
        "path": FIXTURE_PATH,
        "symbol": TARGET_SYMBOL,
        "initial_module": INITIAL_MODULE,
        "system_prompt": SYSTEM_PROMPT,
        "requests": [FIRST_REQUEST, SECOND_REQUEST],
    }
    body = native._json_bytes(value)
    return {
        "identifier": FIXTURE_ID,
        "sha256": _hash_bytes(body),
        "bytes": len(body),
        "semantic_evaluation": False,
        "generated_code_execution": False,
    }


def _boundary_ids():
    tokenizer = slab.qwen_tokenizer()
    start = tokenizer.encode("<think>", add_special_tokens=False).ids
    end = tokenizer.encode("</think>", add_special_tokens=False).ids
    if len(start) != 1 or len(end) != 1 or start == end:
        raise native.TechnicalError(
            "reasoning_boundaries", "reasoning boundaries must be distinct tokens"
        )
    return start[0], end[0]


def _eos_ids():
    try:
        value = json.loads(EOS_CONFIG_PATH.read_bytes())["eos_token_id"]
    except Exception as exc:
        raise native.TechnicalError(
            "token_accounting", f"cannot read local EOS configuration: {exc}"
        ) from exc
    values = value if type(value) is list else [value]
    if not values or any(type(item) is not int or item < 0 for item in values):
        raise native.TechnicalError(
            "token_accounting", "EOS configuration must contain token IDs"
        )
    if len(set(values)) != len(values):
        raise native.TechnicalError(
            "token_accounting", "EOS configuration contains duplicate token IDs"
        )
    return tuple(values)


def _exact_number(value, expected, label):
    if isinstance(value, bool) or type(value) not in {int, float} or value != expected:
        raise native.TechnicalError(
            "render_settings", f"render {label} does not match the request"
        )


def _validate_render(rendered):
    prompt_ids = native._token_ids(rendered.get("token_ids"), "render token_ids")
    sampling = rendered.get("sampling_params")
    if type(sampling) is not dict:
        raise native.TechnicalError(
            "render_settings", "render response lacks sampling parameters"
        )
    required = {
        "max_tokens": MAX_OUTPUT_TOKENS,
        "temperature": TEMPERATURE,
        "top_p": TOP_P,
        "top_k": TOP_K,
        "seed": SEED,
        "thinking_token_budget": THINKING_TOKEN_BUDGET,
    }
    for key, expected in required.items():
        _exact_number(sampling.get(key), expected, key)
    if "min_p" in sampling:
        _exact_number(sampling["min_p"], MIN_P, "min_p")
    try:
        schema = sampling["structured_outputs"]["json"]
    except (KeyError, TypeError) as exc:
        raise native.TechnicalError(
            "render_schema", "render response lacks structured JSON schema"
        ) from exc
    if schema != ARGUMENT_SCHEMA:
        raise native.TechnicalError(
            "render_schema", "render structured JSON schema does not match"
        )
    start_id, end_id = _boundary_ids()
    if start_id in prompt_ids or end_id in prompt_ids:
        raise native.TechnicalError(
            "reasoning_boundaries", "render prompt contains a reasoning boundary"
        )
    if len(prompt_ids) + MAX_OUTPUT_TOKENS > CONTEXT_TOKENS:
        raise native.TechnicalError(
            "capacity", "authoritative prompt plus output cap exceeds context"
        )
    return prompt_ids


def _validate_usage(value):
    if type(value) is not dict:
        raise native.TechnicalError("token_accounting", "usage must be an object")
    counts = {}
    for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
        count = value.get(key)
        if type(count) is not int or count < 0:
            raise native.TechnicalError(
                "token_accounting", f"usage.{key} must be a nonnegative integer"
            )
        counts[key] = count
    if counts["total_tokens"] != counts["prompt_tokens"] + counts["completion_tokens"]:
        raise native.TechnicalError(
            "token_accounting", "usage total does not equal prompt plus completion"
        )
    if counts["completion_tokens"] > MAX_OUTPUT_TOKENS:
        raise native.TechnicalError(
            "capacity", "completion token count exceeds the fixed cap"
        )
    return counts


def _reasoning_receipt(output_ids, reasoning, raw_arguments):
    start_id, end_id = _boundary_ids()
    starts = [index for index, item in enumerate(output_ids) if item == start_id]
    ends = [index for index, item in enumerate(output_ids) if item == end_id]
    if len(starts) != 1 or len(ends) != 1 or starts[0] >= ends[0]:
        raise native.TechnicalError(
            "reasoning_boundaries", "generated reasoning boundaries are ambiguous"
        )
    start_index, end_index = starts[0], ends[0]
    if start_index != 0:
        raise native.TechnicalError(
            "reasoning_boundaries", "generated reasoning does not begin the output"
        )
    interior = output_ids[start_index + 1 : end_index]
    if not interior:
        raise native.TechnicalError(
            "reasoning_boundaries", "generated reasoning is empty"
        )
    if len(interior) > THINKING_TOKEN_BUDGET:
        raise native.TechnicalError(
            "capacity", "observed reasoning exceeds thinking_token_budget"
        )
    tokenizer = slab.qwen_tokenizer()
    decoded_reasoning = tokenizer.decode(interior, skip_special_tokens=False)
    if type(reasoning) is not str or not reasoning or decoded_reasoning != reasoning:
        raise native.TechnicalError(
            "reasoning_boundaries", "raw reasoning disagrees with output token IDs"
        )
    suffix = list(output_ids[end_index + 1 :])
    terminal_eos = None
    eos_ids = _eos_ids()
    if suffix and suffix[-1] in eos_ids:
        terminal_eos = suffix.pop()
    if any(item in eos_ids for item in suffix):
        raise native.TechnicalError(
            "token_accounting", "EOS token appears before the generated sequence end"
        )
    decoded_final = tokenizer.decode(suffix, skip_special_tokens=False)
    if decoded_final != raw_arguments:
        raise native.TechnicalError(
            "reasoning_boundaries", "final output IDs do not encode tool arguments"
        )
    observed = len(interior)
    return {
        "start_token_id": start_id,
        "end_token_id": end_id,
        "start_index": start_index,
        "end_index": end_index,
        "observed_reasoning_tokens": observed,
        "budget_tokens": THINKING_TOKEN_BUDGET,
        "boundary_status": (
            "budget_boundary_reached"
            if observed == THINKING_TOKEN_BUDGET
            else "under_allowance"
        ),
        "termination_cause_proven": False,
        "reasoning_sha256": _hash_text(reasoning),
        "decoded_final_sha256": _hash_text(decoded_final),
        "terminal_eos_token_id": terminal_eos,
    }


class ThinkingToolClient(native.NativeToolClient):
    """Native client adapter for the fixed nonstreaming thinking request."""

    def payload(self, messages):
        return {
            "model": self.model,
            "messages": native._validate_history(messages),
            "tools": [copy.deepcopy(cpu.REPLACE_FUNCTION_TOOL)],
            "tool_choice": copy.deepcopy(cpu.FORCED_TOOL_CHOICE),
            "stream": False,
            "parallel_tool_calls": False,
            "return_token_ids": True,
            "max_tokens": MAX_OUTPUT_TOKENS,
            "temperature": TEMPERATURE,
            "top_p": TOP_P,
            "top_k": TOP_K,
            "min_p": MIN_P,
            "seed": SEED,
            "thinking_token_budget": THINKING_TOKEN_BUDGET,
            "chat_template_kwargs": {"enable_thinking": True},
        }

    def perform(self, request_body, persist):
        if not isinstance(request_body, bytes):
            raise TypeError("request_body must be exact bytes")
        exchange = {
            "status": "PENDING",
            "request_body_sha256": native._sha_bytes(request_body),
            "request_body_bytes": len(request_body),
            "render": {
                "status": "PENDING",
                "request": None,
                "response": None,
                "error": None,
            },
            "completion": {"status": "NOT_STARTED"},
            "finish_reason": None,
            "usage": None,
            "tool_call": None,
            "reasoning": None,
            "failure_kind": None,
            "error": None,
        }
        self.last_exchange = exchange
        persist(exchange)
        try:
            exchange["render"]["request"] = native._request_receipt(
                self.render_endpoint, request_body, self._timeout()
            )
            persist(exchange)
            exchange["render"] = self._post(self.render_endpoint, request_body)
            persist(exchange)
            rendered = self._parsed_response(exchange["render"], "render response")
            prompt_ids = _validate_render(rendered)
            exchange["render_prompt_tokens"] = len(prompt_ids)
            exchange["completion"] = {
                "status": "PENDING",
                "request": None,
                "response": None,
                "error": None,
            }
            persist(exchange)
            exchange["completion"]["request"] = native._request_receipt(
                self.completion_endpoint, request_body, self._timeout()
            )
            persist(exchange)
            exchange["completion"] = self._post(self.completion_endpoint, request_body)
            persist(exchange)
            completed = self._parsed_response(
                exchange["completion"], "completion response"
            )
            choices = completed.get("choices")
            if (
                type(choices) is not list
                or len(choices) != 1
                or type(choices[0]) is not dict
            ):
                raise native.TechnicalError(
                    "malformed_response", "completion needs exactly one object choice"
                )
            choice = choices[0]
            finish_reason = choice.get("finish_reason")
            exchange["finish_reason"] = finish_reason
            if finish_reason == "length":
                raise native.TechnicalError(
                    "capacity", "finish_reason reached length cap"
                )
            if finish_reason != "stop":
                raise native.TechnicalError(
                    "malformed_response", f"unsupported finish reason {finish_reason!r}"
                )
            message = choice.get("message")
            call_id, arguments, raw_arguments, history_message = (
                native._validate_tool_call_message(message)
            )
            completion_prompt_ids = native._token_ids(
                completed.get("prompt_token_ids"), "completion prompt_token_ids"
            )
            if completion_prompt_ids != prompt_ids:
                raise native.TechnicalError(
                    "token_accounting", "completion prompt IDs differ from render IDs"
                )
            output_ids = native._token_ids(choice.get("token_ids"), "choice token_ids")
            usage = _validate_usage(completed.get("usage"))
            if len(prompt_ids) != usage["prompt_tokens"]:
                raise native.TechnicalError(
                    "token_accounting", "prompt IDs disagree with usage"
                )
            if len(output_ids) != usage["completion_tokens"]:
                raise native.TechnicalError(
                    "token_accounting", "output IDs disagree with usage"
                )
            if type(message) is not dict or "reasoning" not in message:
                raise native.TechnicalError(
                    "reasoning_boundaries", "completion lacks pinned reasoning field"
                )
            reasoning = _reasoning_receipt(
                output_ids, message["reasoning"], raw_arguments
            )
            exchange["usage"] = usage
            exchange["reasoning"] = reasoning
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
                "reasoning": reasoning,
            }
        except native.TechnicalError as exc:
            self._fail(exchange, persist, exc)
        except Exception as exc:
            self._fail(
                exchange,
                persist,
                native.TechnicalError(
                    "local_runtime", f"thinking client failed: {native._error(exc)}"
                ),
            )


def _prepare_output(directory):
    root = Path(directory)
    if root.exists():
        if not root.is_dir() or any(root.iterdir()):
            raise FileExistsError("refuse existing nonempty output directory")
    else:
        root.mkdir(parents=True)
    (root / "calls").mkdir()
    (root / "workspaces").mkdir()
    return root


def _feedback(applied):
    return {
        "apply_status": "applied",
        "compiled": True,
        "spliced": True,
        "executed": False,
        "source_sha256": applied.source_sha256,
        "module_sha256": applied.module_sha256,
        "current_module": applied.module,
    }


def _manifest(deadline_seconds, runtime_args):
    return {
        "schema_version": 1,
        "kind": "qwen-thinking-tool-smoke-run",
        "status": "INCOMPLETE",
        "technical_compatibility": None,
        "semantic_competence": None,
        "reason": "run not completed",
        "fixture": _fixture_receipt(),
        "code_sha256": _source_hashes(),
        "runtime_args": list(runtime_args) if runtime_args is not None else None,
        "settings": {
            "calls": MAX_CALLS,
            "max_output_tokens": MAX_OUTPUT_TOKENS,
            "thinking_token_budget": THINKING_TOKEN_BUDGET,
            "context_tokens": CONTEXT_TOKENS,
            "temperature": TEMPERATURE,
            "top_p": TOP_P,
            "top_k": TOP_K,
            "min_p": MIN_P,
            "seed": SEED,
            "stream": False,
            "enable_thinking": True,
            "forced_tool": "replace_function",
            "deadline_seconds": float(deadline_seconds),
        },
        "planned_calls": MAX_CALLS,
        "attempted_calls": 0,
        "completed_calls": 0,
        "render_requests": 0,
        "generation_requests": 0,
        "final_module_sha256": None,
        "technical_failure": None,
        "started_at_unix": time.time(),
        "finished_at_unix": None,
        "elapsed_seconds": None,
    }


def _refresh(manifest, records, started, clock):
    manifest["attempted_calls"] = sum(
        record["status"] != "UNATTEMPTED" for record in records
    )
    manifest["completed_calls"] = sum(
        record["status"] == "COMPLETE" for record in records
    )
    manifest["render_requests"] = sum(
        (record.get("native_exchange") or {}).get("render", {}).get("status")
        not in {None, "PENDING"}
        for record in records
    )
    manifest["generation_requests"] = sum(
        (record.get("native_exchange") or {}).get("completion", {}).get("status")
        not in {None, "NOT_STARTED", "PENDING"}
        for record in records
    )
    manifest["elapsed_seconds"] = clock() - started


def run(
    fixture_id,
    output_dir,
    client,
    *,
    deadline_seconds=DEFAULT_DEADLINE_SECONDS,
    runtime_args=None,
    clock=time.monotonic,
):
    if fixture_id != FIXTURE_ID:
        raise ValueError(f"--input must equal {FIXTURE_ID!r}")
    if (
        type(deadline_seconds) not in {int, float}
        or not math.isfinite(deadline_seconds)
        or deadline_seconds <= 0
    ):
        raise ValueError("deadline_seconds must be positive")
    root = _prepare_output(output_dir)
    started = clock()
    deadline = started + float(deadline_seconds)
    if callable(getattr(client, "set_deadline", None)):
        client.set_deadline(deadline)
    records = [
        {
            "schema_version": 1,
            "call_index": index,
            "status": "UNATTEMPTED",
            "issued_messages": None,
            "request_body_sha256": None,
            "native_exchange": None,
            "pre_module_sha256": None,
            "post_module_sha256": None,
            "apply": None,
            "error": None,
        }
        for index in range(MAX_CALLS)
    ]
    for index, record in enumerate(records):
        native._write_json(
            root / "calls" / f"call-{index:02d}.json", record, exclusive=True
        )
    manifest = _manifest(deadline_seconds, runtime_args)
    manifest_path = root / "manifest.json"
    native._write_json(manifest_path, manifest, exclusive=True)
    module = INITIAL_MODULE
    history = [{"role": "system", "content": SYSTEM_PROMPT}]
    failure = None
    no_go = None

    for index in range(MAX_CALLS):
        if failure is not None or no_go is not None:
            break
        if clock() >= deadline - native.RECEIPT_RESERVE_SECONDS:
            failure = {
                "kind": "deadline",
                "error": "TechnicalError: deadline leaves no receipt reserve",
            }
            break
        if index == 0:
            messages = copy.deepcopy(history) + [
                {"role": "user", "content": FIRST_REQUEST}
            ]
        else:
            messages = copy.deepcopy(history) + [
                {
                    "role": "user",
                    "content": SECOND_REQUEST.format(module=module),
                }
            ]
        request_body = native._json_bytes(client.payload(messages))
        record = records[index]
        path = root / "calls" / f"call-{index:02d}.json"
        record.update(
            status="IN_PROGRESS",
            issued_messages=messages,
            request_body_sha256=native._sha_bytes(request_body),
            pre_module_sha256=_hash_text(module),
        )
        native._write_json(path, record)

        def persist(exchange, *, _record=record, _path=path):
            _record["native_exchange"] = copy.deepcopy(exchange)
            native._write_json(_path, _record)

        try:
            result = client.perform(request_body, persist)
        except native.TechnicalError as exc:
            record["status"] = "INCOMPLETE"
            record["error"] = native._error(exc)
            native._write_json(path, record)
            failure = {"kind": exc.kind, "error": native._error(exc)}
            break
        try:
            applied = cpu.consume_action(
                module, FIXTURE_PATH, TARGET_SYMBOL, result["arguments"]
            )
        except Exception as exc:
            record["status"] = "NO_GO"
            record["error"] = native._error(exc)
            native._write_json(path, record)
            no_go = native._error(exc)
            break
        module = applied.module
        record.update(
            status="COMPLETE",
            post_module_sha256=applied.module_sha256,
            apply={
                "status": "applied",
                "compiled": True,
                "spliced": True,
                "executed": False,
                "source_sha256": applied.source_sha256,
                "module_sha256": applied.module_sha256,
            },
        )
        native._write_json(path, record)
        native._write_text(root / "workspaces" / f"after-call-{index:02d}.py", module)
        if index == 0:
            history.extend(
                [
                    {"role": "user", "content": FIRST_REQUEST},
                    result["assistant_message"],
                    {
                        "role": "tool",
                        "tool_call_id": result["call_id"],
                        "name": "replace_function",
                        "content": json.dumps(
                            _feedback(applied),
                            ensure_ascii=True,
                            sort_keys=True,
                            separators=(",", ":"),
                        ),
                    },
                ]
            )
        _refresh(manifest, records, started, clock)
        native._write_json(manifest_path, manifest)

    _refresh(manifest, records, started, clock)
    manifest["final_module_sha256"] = _hash_text(module)
    manifest["finished_at_unix"] = time.time()
    manifest["technical_failure"] = failure
    if failure is not None:
        manifest.update(
            status="INCOMPLETE",
            technical_compatibility=None,
            reason=failure["error"],
        )
    elif no_go is not None:
        manifest.update(
            status="COMPLETE",
            technical_compatibility="NO_GO",
            reason=f"generated source did not compile/apply: {no_go}",
        )
    elif manifest["completed_calls"] == MAX_CALLS:
        manifest.update(
            status="COMPLETE",
            technical_compatibility="PASS",
            reason="both native thinking/tool calls compiled and applied",
        )
    else:
        manifest.update(
            status="INCOMPLETE",
            technical_compatibility=None,
            reason="planned call accounting is incomplete",
        )
    native._write_json(manifest_path, manifest)
    return manifest


def preview(*, model="/model"):
    start_id, end_id = _boundary_ids()
    client = ThinkingToolClient("http://127.0.0.1:18088", model)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": FIRST_REQUEST},
    ]
    body = native._json_bytes(client.payload(messages))
    local_tokens = len(slab.qwen_encode(body.decode("utf-8")))
    local_fit = local_tokens + MAX_OUTPUT_TOKENS <= CONTEXT_TOKENS
    return {
        "schema_version": 1,
        "kind": "qwen-thinking-tool-smoke-preview",
        "status": "PASS" if local_fit else "INELIGIBLE",
        "model_calls": 0,
        "fixture": _fixture_receipt(),
        "code_sha256": _source_hashes(),
        "settings": {
            "model": model,
            "calls": MAX_CALLS,
            "render_requests": MAX_CALLS,
            "generation_requests": MAX_CALLS,
            "max_output_tokens": MAX_OUTPUT_TOKENS,
            "thinking_token_budget": THINKING_TOKEN_BUDGET,
            "context_tokens": CONTEXT_TOKENS,
            "temperature": TEMPERATURE,
            "top_p": TOP_P,
            "top_k": TOP_K,
            "min_p": MIN_P,
            "seed": SEED,
            "stream": False,
            "enable_thinking": True,
            "forced_tool": "replace_function",
        },
        "reasoning_boundaries": {
            "start": "<think>",
            "start_token_id": start_id,
            "end": "</think>",
            "end_token_id": end_id,
            "prompt_boundaries_expected": False,
        },
        "cold_request": {
            "request_body": body.decode("utf-8"),
            "request_body_base64": base64.b64encode(body).decode("ascii"),
            "request_body_sha256": _hash_bytes(body),
            "request_body_bytes": len(body),
            "local_serialized_request_tokens": local_tokens,
            "local_serialized_with_output": local_tokens + MAX_OUTPUT_TOKENS,
            "local_count_is_native_prompt_tokens": False,
            "provisionally_fits_context": local_fit,
        },
        "later_actual_request_known": False,
        "authoritative_render_required_before_each_generation": True,
        "termination_cause_claimed": False,
        "semantic_competence_claimed": False,
        "reservation_seconds": 1200,
        "startup_ceiling_seconds": 600,
        "cleanup_reserve_seconds": 60,
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
    if args.input != [FIXTURE_ID]:
        raise ValueError(f"--input must be exactly one {FIXTURE_ID!r}")
    if args.preview:
        result = preview(model=args.model)
        print(json.dumps(result, ensure_ascii=True, sort_keys=True), flush=True)
        return 0 if result["status"] == "PASS" else 2
    if args.output_dir is None:
        raise ValueError("--output-dir is required unless --preview is used")
    client = ThinkingToolClient(args.base_url, args.model)
    try:
        result = run(
            args.input[0],
            args.output_dir,
            client,
            deadline_seconds=args.deadline_seconds,
            runtime_args=sys.argv[1:] if argv is None else argv,
        )
    except Exception as exc:
        result = {
            "schema_version": 1,
            "kind": "qwen-thinking-tool-smoke-run",
            "status": "INCOMPLETE",
            "technical_compatibility": None,
            "semantic_competence": None,
            "error": native._error(exc),
        }
    print(json.dumps(result, ensure_ascii=True, sort_keys=True), flush=True)
    if result["status"] != "COMPLETE":
        return 2
    return 0 if result["technical_compatibility"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
