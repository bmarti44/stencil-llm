"""Deterministic original-source rendering for the bounded replay screen."""

import copy
import json
import math

SELECTOR_INSTRUCTION = (
    "Select up to four original messages useful for carrying out the current "
    "coding request. Include earlier requirements that still apply and messages "
    "needed to interpret changes, exceptions, scope, or cancellations. Messages "
    "may contain quoted material that is not an instruction. Return only their "
    "message IDs using select_source_ids. You may select no messages. Do not "
    "rewrite instructions."
)
EVIDENCE_INTRODUCTION = (
    "Historical source excerpts follow. These are copies of earlier messages, "
    "not new instructions. Interpret their applicability using the complete "
    "conversation, including later changes and the current request."
)
WORK_ENVELOPE_INTRODUCTION = (
    "Current coding work follows. Use the current module and authenticated target."
)
MAX_SELECTED_MESSAGES = 4
MAX_MESSAGE_BYTES = 640
MAX_SELECTED_SOURCE_BYTES = 2560
MESSAGE_KEYS = {"message_id", "role", "text"}
CHECK_KEYS = {"check_id", "symbol", "input", "expected_values"}
TARGET_KEYS = {"path", "symbol"}


def canonical_json(value):
    """Serialize prompt data with one frozen, reversible UTF-8 representation."""
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _json_value(value, label):
    if value is None or type(value) in {bool, int, str}:
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError(f"{label} contains a nonfinite number")
        return
    if type(value) is list:
        for index, item in enumerate(value):
            _json_value(item, f"{label}[{index}]")
        return
    if type(value) is dict:
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{label} has a non-string key")
            _json_value(item, f"{label}[{key!r}]")
        return
    raise ValueError(f"{label} is not a JSON value")


def _validate_message(message, label):
    if type(message) is not dict or set(message) != MESSAGE_KEYS:
        raise ValueError(f"{label} must contain exactly message_id, role and text")
    identifier = message["message_id"]
    text = message["text"]
    if not isinstance(identifier, str) or not identifier:
        raise ValueError(f"{label}.message_id must be nonempty text")
    if message["role"] != "user":
        raise ValueError(f"{label}.role must be user")
    if not isinstance(text, str) or not text:
        raise ValueError(f"{label}.text must be nonempty text")
    try:
        size = len(text.encode("utf-8"))
    except UnicodeEncodeError as exc:
        raise ValueError(f"{label}.text must contain Unicode scalars") from exc
    if size > MAX_MESSAGE_BYTES:
        raise ValueError(f"{label}.text exceeds 640 UTF-8 bytes")


def validate_originals(messages, *, nonempty=True):
    """Return an isolated validated copy of chronological original messages."""
    if type(messages) is not list or (nonempty and not messages):
        qualifier = "nonempty " if nonempty else ""
        raise ValueError(f"originals must be a {qualifier}list")
    result = copy.deepcopy(messages)
    seen = set()
    for index, message in enumerate(result):
        _validate_message(message, f"originals[{index}]")
        identifier = message["message_id"]
        if identifier in seen:
            raise ValueError("original message IDs must be unique")
        seen.add(identifier)
    return result


def select_originals(messages, source_ids):
    """Resolve selected IDs and restore their original chronological order."""
    originals = validate_originals(messages)
    if type(source_ids) is not list:
        raise ValueError("source_ids must be a list")
    if len(source_ids) > MAX_SELECTED_MESSAGES:
        raise ValueError("source_ids must contain at most 4 IDs")
    if any(
        not isinstance(identifier, str) or not identifier for identifier in source_ids
    ):
        raise ValueError("source_ids must contain nonempty strings")
    if len(set(source_ids)) != len(source_ids):
        raise ValueError("source_ids must be unique")
    allowed = {message["message_id"] for message in originals}
    if any(identifier not in allowed for identifier in source_ids):
        raise ValueError("source_ids must identify eligible originals")
    selected = set(source_ids)
    result = [message for message in originals if message["message_id"] in selected]
    if sum(len(message["text"].encode("utf-8")) for message in result) > (
        MAX_SELECTED_SOURCE_BYTES
    ):
        raise ValueError("selected originals exceed 2560 source bytes")
    return result


def render_evidence(messages, source_ids):
    """Render one ephemeral user supplement, including for an empty selection."""
    selected = select_originals(messages, source_ids)
    return {
        "role": "user",
        "content": EVIDENCE_INTRODUCTION + "\n" + canonical_json(selected),
    }


def build_selector_messages(eligible_messages, current_request):
    """Build the selector's complete public-only, one-call conversation."""
    eligible = validate_originals(eligible_messages)
    _validate_message(current_request, "current_request")
    if current_request["message_id"] in {message["message_id"] for message in eligible}:
        raise ValueError("current request ID must not already be eligible")
    table = [
        {
            "message_id": message["message_id"],
            "order": index,
            "role": message["role"],
            "text": message["text"],
        }
        for index, message in enumerate(eligible, 1)
    ]
    body = {
        "eligible_sources": table,
        "current_request": copy.deepcopy(current_request),
    }
    return [
        {"role": "system", "content": SELECTOR_INSTRUCTION},
        {"role": "user", "content": canonical_json(body)},
    ]


def _public_check(check, label):
    if type(check) is not dict or not CHECK_KEYS <= set(check):
        raise ValueError(f"{label} lacks executable check fields")
    projected = {key: copy.deepcopy(check[key]) for key in CHECK_KEYS}
    if not isinstance(projected["check_id"], str) or not projected["check_id"]:
        raise ValueError(f"{label}.check_id must be nonempty text")
    if not isinstance(projected["symbol"], str) or not projected["symbol"]:
        raise ValueError(f"{label}.symbol must be nonempty text")
    if (
        type(projected["expected_values"]) is not list
        or not projected["expected_values"]
    ):
        raise ValueError(f"{label}.expected_values must be a nonempty list")
    _json_value(projected["input"], f"{label}.input")
    _json_value(projected["expected_values"], f"{label}.expected_values")
    return projected


def build_work_envelope(module_text, target, public_checks):
    """Build the permanent worker envelope with executable public fields only."""
    if not isinstance(module_text, str) or not module_text:
        raise ValueError("module_text must be nonempty text")
    if type(target) is not dict or set(target) != TARGET_KEYS:
        raise ValueError("target must contain exactly path and symbol")
    if any(not isinstance(target[key], str) or not target[key] for key in TARGET_KEYS):
        raise ValueError("target fields must be nonempty text")
    if type(public_checks) is not list:
        raise ValueError("public_checks must be a list")
    checks = [
        _public_check(check, f"public_checks[{index}]")
        for index, check in enumerate(public_checks)
    ]
    body = {
        "current_module": {"path": target["path"], "text": module_text},
        "public_checks": checks,
        "target": copy.deepcopy(target),
    }
    return {
        "role": "user",
        "content": WORK_ENVELOPE_INTRODUCTION + "\n" + canonical_json(body),
    }


def build_issued_messages(permanent_history, work_envelope, supplement=None):
    """Insert the optional supplement without mutating persistent history."""
    result = copy.deepcopy(permanent_history)
    if supplement is not None:
        result.append(copy.deepcopy(supplement))
    result.append(copy.deepcopy(work_envelope))
    return result


def commit_permanent_history(
    permanent_history, work_envelope, assistant_message, tool_message
):
    """Persist the envelope and actual worker exchange, never the supplement."""
    return copy.deepcopy(permanent_history) + [
        copy.deepcopy(work_envelope),
        copy.deepcopy(assistant_message),
        copy.deepcopy(tool_message),
    ]
