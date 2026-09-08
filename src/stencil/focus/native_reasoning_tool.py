"""Parameterized native reasoning and forced-tool client for bounded pilots."""

import copy
import json
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from scripts import coding_competence_run as native
from stencil.focus import slab

TechnicalError = native.TechnicalError

ROOT = Path(__file__).resolve().parents[3]
GENERATION_CONFIG = ROOT / "models/qwen3-30b-a3b-hf/generation_config.json"
REPLACE_FUNCTION_SCHEMA = {
    "type": "object",
    "properties": {"source": {"type": "string"}},
    "required": ["source"],
    "additionalProperties": False,
}


def json_bytes(value):
    """Return the canonical bytes sent unchanged to render and generation."""
    return native._json_bytes(value)


def _canonical_json(value):
    try:
        return json_bytes(value).decode("ascii")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ValueError(f"argument_schema must be JSON: {exc}") from exc


def _exact_int(value, label, *, positive=False):
    if type(value) is not int or value < (1 if positive else 0):
        requirement = "positive" if positive else "nonnegative"
        raise ValueError(f"{label} must be a {requirement} integer")


def _finite_number(value, label):
    if isinstance(value, bool) or type(value) not in {int, float}:
        raise ValueError(f"{label} must be a finite number")
    if not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number")


def _focus_schema(visible_source_ids):
    return {
        "type": "object",
        "properties": {
            "obligations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "minLength": 1},
                        "source_ids": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": list(visible_source_ids),
                            },
                            "minItems": 1,
                        },
                    },
                    "required": ["text", "source_ids"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["obligations"],
        "additionalProperties": False,
    }


def _focus_source_ids(schema):
    try:
        values = schema["properties"]["obligations"]["items"]["properties"][
            "source_ids"
        ]["items"]["enum"]
    except (KeyError, TypeError) as exc:
        raise ValueError("record_focus schema lacks its visible-source enum") from exc
    if (
        type(values) is not list
        or not values
        or any(not isinstance(value, str) or not value for value in values)
        or len(set(values)) != len(values)
    ):
        raise ValueError("record_focus needs unique visible source IDs")
    if schema != _focus_schema(values):
        raise ValueError("record_focus schema has the wrong shape")
    return tuple(values)


@dataclass(frozen=True, slots=True)
class NativeRequestSpec:
    """Deeply immutable native request settings and canonical argument schema."""

    tool_name: str
    tool_description: str
    argument_schema_json: str
    max_output_tokens: int
    reasoning_token_budget: int
    context_tokens: int
    temperature: float
    top_p: float
    top_k: int
    min_p: float
    seed: int

    def __post_init__(self):
        if self.tool_name not in {"replace_function", "record_focus"}:
            raise ValueError("unsupported native tool name")
        if not isinstance(self.tool_description, str) or not self.tool_description:
            raise ValueError("tool_description must be nonempty text")
        try:
            schema = json.loads(self.argument_schema_json)
        except (TypeError, json.JSONDecodeError) as exc:
            raise ValueError("argument_schema_json must be JSON text") from exc
        if type(schema) is not dict or self.argument_schema_json != _canonical_json(
            schema
        ):
            raise ValueError("argument_schema_json must be a canonical object")
        if self.tool_name == "replace_function":
            if schema != REPLACE_FUNCTION_SCHEMA:
                raise ValueError("replace_function schema has the wrong shape")
        else:
            _focus_source_ids(schema)
        _exact_int(self.max_output_tokens, "max_output_tokens", positive=True)
        _exact_int(
            self.reasoning_token_budget,
            "reasoning_token_budget",
            positive=True,
        )
        _exact_int(self.context_tokens, "context_tokens", positive=True)
        _exact_int(self.top_k, "top_k", positive=True)
        _exact_int(self.seed, "seed")
        if self.reasoning_token_budget >= self.max_output_tokens:
            raise ValueError("reasoning budget must leave final-output capacity")
        if self.max_output_tokens >= self.context_tokens:
            raise ValueError("output cap must be smaller than context")
        for value, label in (
            (self.temperature, "temperature"),
            (self.top_p, "top_p"),
            (self.min_p, "min_p"),
        ):
            _finite_number(value, label)
        if self.temperature <= 0 or not 0 < self.top_p <= 1 or not 0 <= self.min_p <= 1:
            raise ValueError("sampling values are outside supported ranges")

    @classmethod
    def create(cls, *, argument_schema, **kwargs):
        return cls(argument_schema_json=_canonical_json(argument_schema), **kwargs)

    @property
    def argument_schema(self):
        return json.loads(self.argument_schema_json)

    @property
    def tool(self):
        return {
            "type": "function",
            "function": {
                "name": self.tool_name,
                "description": self.tool_description,
                "parameters": self.argument_schema,
            },
        }

    @property
    def forced_choice(self):
        return {
            "type": "function",
            "function": {"name": self.tool_name},
        }


def record_focus_spec(visible_source_ids, **settings):
    values = list(visible_source_ids)
    if (
        not values
        or any(not isinstance(value, str) or not value for value in values)
        or len(set(values)) != len(values)
    ):
        raise ValueError("record_focus needs unique visible source IDs")
    return NativeRequestSpec.create(
        tool_name="record_focus",
        tool_description=(
            "Record current obligations grounded in visible source message IDs."
        ),
        argument_schema=_focus_schema(values),
        **settings,
    )


@lru_cache(maxsize=1)
def local_tokenizer():
    return slab.qwen_tokenizer()


@lru_cache(maxsize=1)
def reasoning_boundary_ids():
    tokenizer = local_tokenizer()
    start = tokenizer.encode("<think>", add_special_tokens=False).ids
    end = tokenizer.encode("</think>", add_special_tokens=False).ids
    if len(start) != 1 or len(end) != 1 or start == end:
        raise TechnicalError(
            "reasoning_boundaries", "reasoning boundaries must be distinct tokens"
        )
    return start[0], end[0]


@lru_cache(maxsize=1)
def local_eos_ids():
    try:
        value = json.loads(GENERATION_CONFIG.read_bytes())["eos_token_id"]
    except Exception as exc:
        raise TechnicalError(
            "token_accounting", f"cannot read local EOS configuration: {exc}"
        ) from exc
    values = value if type(value) is list else [value]
    if (
        not values
        or any(type(item) is not int or item < 0 for item in values)
        or len(set(values)) != len(values)
    ):
        raise TechnicalError(
            "token_accounting", "EOS configuration must contain unique token IDs"
        )
    return tuple(values)


def _validate_arguments(spec, arguments):
    if type(arguments) is not dict:
        raise TechnicalError("malformed_response", "tool arguments must be an object")
    if spec.tool_name == "replace_function":
        if set(arguments) != {"source"} or not isinstance(arguments["source"], str):
            raise TechnicalError(
                "malformed_response", "replace_function needs exactly string source"
            )
        return
    if set(arguments) != {"obligations"} or type(arguments["obligations"]) is not list:
        raise TechnicalError(
            "malformed_response", "record_focus needs exactly obligations list"
        )
    allowed = set(_focus_source_ids(spec.argument_schema))
    for obligation in arguments["obligations"]:
        if (
            type(obligation) is not dict
            or set(obligation) != {"text", "source_ids"}
            or not isinstance(obligation["text"], str)
            or not obligation["text"]
            or type(obligation["source_ids"]) is not list
            or not obligation["source_ids"]
            or any(
                not isinstance(source_id, str) or source_id not in allowed
                for source_id in obligation["source_ids"]
            )
        ):
            raise TechnicalError(
                "malformed_response", "record_focus arguments violate their schema"
            )


def _validate_tool_message(message, spec):
    if type(message) is not dict or message.get("role") != "assistant":
        raise TechnicalError("malformed_response", "tool message must be assistant")
    if set(message) != {"role", "content", "tool_calls"}:
        raise TechnicalError(
            "malformed_response", "history tool message contains non-final fields"
        )
    if message["content"] is not None and message["content"] != "":
        raise TechnicalError(
            "malformed_response", "named tool response contains completion text"
        )
    calls = message["tool_calls"]
    if type(calls) is not list or len(calls) != 1 or type(calls[0]) is not dict:
        raise TechnicalError(
            "malformed_response", "response must contain exactly one tool call"
        )
    call = calls[0]
    function = call.get("function")
    if call.get("type") != "function" or type(function) is not dict:
        raise TechnicalError("malformed_response", "tool call shape is invalid")
    call_id = call.get("id")
    if not isinstance(call_id, str) or not call_id:
        raise TechnicalError("malformed_response", "tool call ID is missing")
    if function.get("name") != spec.tool_name:
        raise TechnicalError("malformed_response", "wrong native tool function")
    raw_arguments = function.get("arguments")
    if not isinstance(raw_arguments, str):
        raise TechnicalError("malformed_response", "tool arguments must be JSON text")
    try:
        arguments = json.loads(raw_arguments)
    except json.JSONDecodeError as exc:
        raise TechnicalError(
            "malformed_response", f"tool arguments are invalid JSON: {exc}"
        ) from exc
    _validate_arguments(spec, arguments)
    return call_id, arguments, raw_arguments, copy.deepcopy(message)


def _validate_history(messages, spec):
    if type(messages) is not list or not messages:
        raise ValueError("messages must be a nonempty list")
    result = copy.deepcopy(messages)
    pending_id = None
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
            if pending_id is not None:
                raise ValueError("assistant tool call lacks its tool result")
            pending_id = _validate_tool_message(message, spec)[0]
        elif role == "tool":
            if (
                pending_id is None
                or set(message) != {"role", "tool_call_id", "name", "content"}
                or message["tool_call_id"] != pending_id
                or message["name"] != spec.tool_name
                or not isinstance(message["content"], str)
            ):
                raise ValueError(f"message {index} has invalid tool-result content")
            pending_id = None
        else:
            raise ValueError(f"message {index} has unsupported role")
    if pending_id is not None:
        raise ValueError("assistant tool call lacks its tool result")
    json_bytes(result)
    return result


def _exact_number(value, expected, label):
    if isinstance(value, bool) or type(value) not in {int, float} or value != expected:
        raise TechnicalError(
            "render_settings", f"render {label} does not match the request"
        )


def _validate_render(rendered, spec):
    prompt_ids = native._token_ids(rendered.get("token_ids"), "render token_ids")
    sampling = rendered.get("sampling_params")
    if type(sampling) is not dict:
        raise TechnicalError(
            "render_settings", "render response lacks sampling parameters"
        )
    required = {
        "max_tokens": spec.max_output_tokens,
        "temperature": spec.temperature,
        "top_p": spec.top_p,
        "top_k": spec.top_k,
        "seed": spec.seed,
        "thinking_token_budget": spec.reasoning_token_budget,
    }
    for key, expected in required.items():
        _exact_number(sampling.get(key), expected, key)
    if "min_p" in sampling:
        _exact_number(sampling["min_p"], spec.min_p, "min_p")
    elif spec.min_p != 0:
        raise TechnicalError(
            "render_settings", "render omitted a nondefault min_p value"
        )
    try:
        schema = sampling["structured_outputs"]["json"]
    except (KeyError, TypeError) as exc:
        raise TechnicalError(
            "render_schema", "render response lacks structured JSON schema"
        ) from exc
    if schema != spec.argument_schema:
        raise TechnicalError(
            "render_schema", "render structured JSON schema does not match"
        )
    start_id, end_id = reasoning_boundary_ids()
    if start_id in prompt_ids or end_id in prompt_ids:
        raise TechnicalError(
            "reasoning_boundaries", "render prompt contains a reasoning boundary"
        )
    if len(prompt_ids) + spec.max_output_tokens > spec.context_tokens:
        raise TechnicalError(
            "capacity", "authoritative prompt plus output cap exceeds context"
        )
    return prompt_ids


def _validate_usage(value, spec):
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
    if counts["total_tokens"] != counts["prompt_tokens"] + counts["completion_tokens"]:
        raise TechnicalError(
            "token_accounting", "usage total does not equal prompt plus completion"
        )
    if counts["completion_tokens"] > spec.max_output_tokens:
        raise TechnicalError("capacity", "completion token count exceeds fixed cap")
    return counts


def _reasoning_receipt(output_ids, reasoning, raw_arguments, spec):
    start_id, end_id = reasoning_boundary_ids()
    starts = [index for index, value in enumerate(output_ids) if value == start_id]
    ends = [index for index, value in enumerate(output_ids) if value == end_id]
    if len(starts) != 1 or len(ends) != 1 or starts[0] != 0 or starts[0] >= ends[0]:
        raise TechnicalError(
            "reasoning_boundaries", "generated reasoning boundaries are ambiguous"
        )
    end_index = ends[0]
    interior = output_ids[1:end_index]
    if not interior:
        raise TechnicalError("reasoning_boundaries", "generated reasoning is empty")
    if len(interior) > spec.reasoning_token_budget:
        raise TechnicalError(
            "capacity", "observed reasoning exceeds thinking_token_budget"
        )
    decoded_reasoning = local_tokenizer().decode(
        interior, skip_special_tokens=False
    )
    if type(reasoning) is not str or not reasoning or decoded_reasoning != reasoning:
        raise TechnicalError(
            "reasoning_boundaries", "raw reasoning disagrees with output token IDs"
        )
    suffix = list(output_ids[end_index + 1 :])
    terminal_eos = None
    eos_ids = local_eos_ids()
    if suffix and suffix[-1] in eos_ids:
        terminal_eos = suffix.pop()
    if any(value in eos_ids for value in output_ids[: end_index + 1] + suffix):
        raise TechnicalError(
            "token_accounting", "EOS token appears before generated sequence end"
        )
    decoded_final = local_tokenizer().decode(suffix, skip_special_tokens=False)
    if decoded_final != raw_arguments:
        raise TechnicalError(
            "reasoning_boundaries", "final output IDs do not encode tool arguments"
        )
    count = len(interior)
    return {
        "start_token_id": start_id,
        "end_token_id": end_id,
        "start_index": 0,
        "end_index": end_index,
        "observed_reasoning_tokens": count,
        "budget_tokens": spec.reasoning_token_budget,
        "boundary_status": (
            "budget_boundary_reached"
            if count == spec.reasoning_token_budget
            else "under_allowance"
        ),
        "termination_cause_proven": False,
        "reasoning_sha256": native._sha_bytes(reasoning.encode("utf-8")),
        "decoded_final_sha256": native._sha_bytes(decoded_final.encode("utf-8")),
        "terminal_eos_token_id": terminal_eos,
    }


class NativeReasoningToolClient(native.NativeToolClient):
    """Forced named-tool client with parameterized reasoning/accounting gates."""

    def __init__(self, base_url, model, spec, *, opener=None):
        if not isinstance(spec, NativeRequestSpec):
            raise TypeError("spec must be NativeRequestSpec")
        super().__init__(base_url, model, opener=opener)
        self.spec = spec

    def payload(self, messages):
        spec = self.spec
        return {
            "model": self.model,
            "messages": _validate_history(messages, spec),
            "tools": [spec.tool],
            "tool_choice": spec.forced_choice,
            "stream": False,
            "parallel_tool_calls": False,
            "return_token_ids": True,
            "max_tokens": spec.max_output_tokens,
            "temperature": spec.temperature,
            "top_p": spec.top_p,
            "top_k": spec.top_k,
            "min_p": spec.min_p,
            "seed": spec.seed,
            "thinking_token_budget": spec.reasoning_token_budget,
            "chat_template_kwargs": {"enable_thinking": True},
        }

    def perform(self, request_body, persist):
        if not isinstance(request_body, bytes):
            raise TypeError("request_body must be exact bytes")
        exchange = {
            "status": "PENDING",
            "request_body_sha256": native._sha_bytes(request_body),
            "request_body_bytes": len(request_body),
            "tool_name": self.spec.tool_name,
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
            prompt_ids = _validate_render(rendered, self.spec)
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
            exchange["completion"] = self._post(
                self.completion_endpoint, request_body
            )
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
                raise TechnicalError(
                    "malformed_response", "completion needs exactly one object choice"
                )
            choice = choices[0]
            finish_reason = choice.get("finish_reason")
            exchange["finish_reason"] = finish_reason
            if finish_reason == "length":
                raise TechnicalError("capacity", "finish_reason reached length cap")
            if finish_reason != "stop":
                raise TechnicalError(
                    "malformed_response", f"unsupported finish reason {finish_reason!r}"
                )
            message = choice.get("message")
            if type(message) is not dict or "reasoning" not in message:
                raise TechnicalError(
                    "reasoning_boundaries", "completion lacks pinned reasoning field"
                )
            response_message = {
                "role": message.get("role"),
                "content": message.get("content"),
                "tool_calls": copy.deepcopy(message.get("tool_calls")),
            }
            call_id, arguments, raw_arguments, history_message = (
                _validate_tool_message(response_message, self.spec)
            )
            completion_prompt_ids = native._token_ids(
                completed.get("prompt_token_ids"), "completion prompt_token_ids"
            )
            if completion_prompt_ids != prompt_ids:
                raise TechnicalError(
                    "token_accounting", "completion prompt IDs differ from render IDs"
                )
            output_ids = native._token_ids(choice.get("token_ids"), "choice token_ids")
            usage = _validate_usage(completed.get("usage"), self.spec)
            if len(prompt_ids) != usage["prompt_tokens"]:
                raise TechnicalError(
                    "token_accounting", "prompt IDs disagree with usage"
                )
            if len(output_ids) != usage["completion_tokens"]:
                raise TechnicalError(
                    "token_accounting", "output IDs disagree with usage"
                )
            reasoning = _reasoning_receipt(
                output_ids, message["reasoning"], raw_arguments, self.spec
            )
            exchange["usage"] = usage
            exchange["reasoning"] = reasoning
            exchange["tool_call"] = {
                "id": call_id,
                "name": self.spec.tool_name,
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
        except TechnicalError as exc:
            self._fail(exchange, persist, exc)
        except Exception as exc:
            self._fail(
                exchange,
                persist,
                TechnicalError(
                    "local_runtime", f"native client failed: {native._error(exc)}"
                ),
            )
