"""Strict nonthinking native client for selecting original source IDs."""

import copy
import json

from scripts import coding_competence_run as native

MAX_OUTPUT_TOKENS = 128
CONTEXT_TOKENS = 32_768
MAX_SELECTED_IDS = 4
SEED = 20260908
TOOL_NAME = "select_source_ids"
TOOL_DESCRIPTION = "Select original source message IDs relevant to the request."
TechnicalError = native.TechnicalError


def _schema(eligible_ids):
    return {
        "type": "object",
        "properties": {
            "source_ids": {
                "type": "array",
                "items": {"type": "string", "enum": list(eligible_ids)},
                "minItems": 0,
                "maxItems": MAX_SELECTED_IDS,
            }
        },
        "required": ["source_ids"],
        "additionalProperties": False,
    }


def _validate_ids(eligible_ids):
    values = list(eligible_ids)
    if (
        not values
        or any(not isinstance(value, str) or not value for value in values)
        or len(set(values)) != len(values)
    ):
        raise ValueError("eligible source IDs must be nonempty unique strings")
    return tuple(values)


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
    if counts["total_tokens"] != counts["prompt_tokens"] + counts["completion_tokens"]:
        raise TechnicalError(
            "token_accounting", "usage total does not equal prompt plus completion"
        )
    if counts["completion_tokens"] > MAX_OUTPUT_TOKENS:
        raise TechnicalError("capacity", "completion token count exceeds selector cap")
    return counts


class NativeSourceSelectorClient(native.NativeToolClient):
    """Two-stage forced-tool client whose only output is eligible source IDs."""

    def __init__(self, base_url, model, eligible_source_ids, *, opener=None):
        super().__init__(base_url, model, opener=opener)
        self.eligible_source_ids = _validate_ids(eligible_source_ids)
        self.argument_schema = _schema(self.eligible_source_ids)

    @property
    def tool(self):
        return {
            "type": "function",
            "function": {
                "name": TOOL_NAME,
                "description": TOOL_DESCRIPTION,
                "parameters": copy.deepcopy(self.argument_schema),
            },
        }

    def payload(self, messages):
        return {
            "model": self.model,
            "messages": native._validate_history(messages),
            "tools": [self.tool],
            "tool_choice": {"type": "function", "function": {"name": TOOL_NAME}},
            "stream": False,
            "parallel_tool_calls": False,
            "return_token_ids": True,
            "max_tokens": MAX_OUTPUT_TOKENS,
            "temperature": 0,
            "seed": SEED,
            "chat_template_kwargs": {"enable_thinking": False},
        }

    def _tool_message(self, message):
        if type(message) is not dict or message.get("role") != "assistant":
            raise TechnicalError(
                "malformed_response", "choice message must be assistant"
            )
        if message.get("content") is not None and message.get("content") != "":
            raise TechnicalError(
                "malformed_response", "named tool response contains completion text"
            )
        calls = message.get("tool_calls")
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
        if function.get("name") != TOOL_NAME:
            raise TechnicalError("malformed_response", "wrong native tool function")
        raw_arguments = function.get("arguments")
        if not isinstance(raw_arguments, str):
            raise TechnicalError(
                "malformed_response", "tool arguments must be JSON text"
            )
        try:
            arguments = json.loads(raw_arguments)
        except json.JSONDecodeError as exc:
            raise TechnicalError(
                "malformed_response", f"tool arguments are invalid JSON: {exc}"
            ) from exc
        source_ids = arguments.get("source_ids") if type(arguments) is dict else None
        if type(arguments) is not dict or set(arguments) != {"source_ids"}:
            raise TechnicalError(
                "malformed_response", "tool arguments need exactly source_ids"
            )
        if (
            type(source_ids) is not list
            or len(source_ids) > MAX_SELECTED_IDS
            or any(
                not isinstance(value, str) or value not in self.eligible_source_ids
                for value in source_ids
            )
            or len(set(source_ids)) != len(source_ids)
        ):
            raise TechnicalError(
                "malformed_response", "source_ids violate the eligible IDs schema"
            )
        history_message = {
            "role": "assistant",
            "content": message.get("content"),
            "tool_calls": copy.deepcopy(calls),
        }
        return call_id, arguments, raw_arguments, history_message

    def perform(self, request_body, persist):
        if not isinstance(request_body, bytes):
            raise TypeError("request_body must be exact bytes")
        exchange = {
            "status": "PENDING",
            "request_body_sha256": native._sha_bytes(request_body),
            "request_body_bytes": len(request_body),
            "render": {
                "status": "PENDING",
                "request": native._request_receipt(
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
            prompt_ids = native._token_ids(
                rendered.get("token_ids"), "render token_ids"
            )
            try:
                rendered_schema = rendered["sampling_params"]["structured_outputs"][
                    "json"
                ]
            except (KeyError, TypeError) as exc:
                raise TechnicalError(
                    "render_schema", "render response lacks structured JSON schema"
                ) from exc
            if rendered_schema != self.argument_schema:
                raise TechnicalError(
                    "render_schema", "render structured JSON schema does not match"
                )
            if len(prompt_ids) + MAX_OUTPUT_TOKENS > CONTEXT_TOKENS:
                raise TechnicalError("capacity", "authoritative context limit exceeded")

            exchange["completion"] = {
                "status": "PENDING",
                "request": native._request_receipt(
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
                raise TechnicalError("capacity", "finish_reason length reached cap")
            if finish_reason != "stop":
                raise TechnicalError(
                    "malformed_response", f"unsupported finish reason {finish_reason!r}"
                )
            call_id, arguments, raw_arguments, history_message = self._tool_message(
                choice.get("message")
            )
            completion_prompt_ids = native._token_ids(
                completed.get("prompt_token_ids"), "completion prompt_token_ids"
            )
            if completion_prompt_ids != prompt_ids:
                raise TechnicalError(
                    "token_accounting", "completion prompt IDs differ from render IDs"
                )
            output_ids = native._token_ids(choice.get("token_ids"), "choice token_ids")
            usage = _validate_usage(completed.get("usage"))
            if len(prompt_ids) != usage["prompt_tokens"]:
                raise TechnicalError(
                    "token_accounting", "prompt IDs disagree with usage"
                )
            if len(output_ids) != usage["completion_tokens"]:
                raise TechnicalError(
                    "token_accounting", "output IDs disagree with usage"
                )
            exchange["usage"] = usage
            exchange["tool_call"] = {
                "id": call_id,
                "name": TOOL_NAME,
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
                TechnicalError(
                    "local_runtime", f"selector client failed: {native._error(exc)}"
                ),
            )
