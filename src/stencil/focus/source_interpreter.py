"""Pure data and token preparation for a source-grounded focus interpreter."""

from __future__ import annotations

import copy
import hashlib
import importlib.metadata
import json
import platform
import statistics
import sys
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
MODEL_PATH = ROOT / "models/qwen3-4b-hf"
BASE_ASSETS_PATH = ROOT / "results/coding-auto-reasoning/research-next/base-assets.json"
SCHEMA_VERSION = 1
SPLITS = {"fit", "dev", "withheld"}
ROLES = {"user", "assistant", "tool"}
EXPECTED_QUERIES = 3
CALIBRATION_DOCUMENTS = 6
CALIBRATION_ROWS = CALIBRATION_DOCUMENTS * EXPECTED_QUERIES
MESSAGE_BANDS = {
    "short": range(8, 13),
    "medium": range(16, 25),
    "longer": range(32, 49),
}

DOCUMENT_KEYS = {
    "schema_version",
    "conversation_id",
    "family_id",
    "split",
    "messages",
    "queries",
}
MESSAGE_REQUIRED_KEYS = {"message_id", "role", "text"}
MESSAGE_OPTIONAL_KEYS = {"task_handle"}
QUERY_KEYS = {"message_id", "target"}
TARGET_KEYS = {"obligations"}
OBLIGATION_KEYS = {"text", "source_ids"}

SYSTEM_PROMPT = (
    "Read only the authentic conversation prefix. Return all currently applicable "
    "standing constraints and conventions for the current task, preserving scope, "
    "modality, permissions, optional behavior, exceptions, changes, and retirement. "
    "The current programming request supplies its algorithm and need not be "
    "repeated. Authentic user directions and explicit user adoption have authority; "
    "assistant suggestions and quoted content alone do not. Return exactly one JSON "
    "object with the key obligations. Each obligation must contain nonempty text and "
    "a nonempty source_ids list citing only visible message IDs. Return no tool "
    "wrapper, commentary, or example."
)
USER_PROMPT = (
    "Current task handle: {task_handle}\n"
    "<authentic_source_events>\n{source_events}\n</authentic_source_events>"
)

TOKENIZER_ASSETS = (
    "config.json",
    "generation_config.json",
    "merges.txt",
    "tokenizer.json",
    "tokenizer_config.json",
    "vocab.json",
)
PACKAGE_NAMES = ("torch", "transformers", "tokenizers", "peft", "accelerate")


class ValidationError(ValueError):
    """A source-interpreter document or serialization is outside the contract."""


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_text(value: str) -> str:
    return _sha_bytes(value.encode("utf-8"))


def _json_text(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _json_bytes(value: Any) -> bytes:
    return _json_text(value).encode("utf-8")


def _error(exc: BaseException) -> str:
    return f"{type(exc).__name__}: {exc}"


def _require_object(value: Any, expected: set[str], label: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValidationError(f"{label} must be an object")
    actual = set(value)
    if actual != expected:
        raise ValidationError(
            f"{label} keys differ: missing={sorted(expected - actual)}, "
            f"extra={sorted(actual - expected)}"
        )
    return value


def _require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValidationError(f"{label} must be nonempty text")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValidationError(f"{label} must contain Unicode scalar text") from exc
    return value


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"JSON object repeats key {key!r}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValidationError(f"JSON constant {value} is not permitted")


def _parse_json(body: bytes) -> Any:
    try:
        return json.loads(
            body,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_json_constant,
        )
    except ValidationError:
        raise
    except Exception as exc:
        raise ValidationError(f"invalid JSON: {exc}") from exc


def record_focus_schema(visible_source_ids: list[str]) -> dict[str, Any]:
    """Return the exact final-only record_focus argument schema."""
    if (
        type(visible_source_ids) is not list
        or not visible_source_ids
        or any(not isinstance(value, str) or not value for value in visible_source_ids)
        or len(set(visible_source_ids)) != len(visible_source_ids)
    ):
        raise ValidationError("record_focus needs unique visible source IDs")
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


def _validate_target(
    target: Any,
    *,
    message_positions: dict[str, int],
    query_position: int,
    label: str,
) -> None:
    target = _require_object(target, TARGET_KEYS, label)
    obligations = target["obligations"]
    if type(obligations) is not list:
        raise ValidationError(f"{label}.obligations must be a list")
    for index, obligation in enumerate(obligations):
        current = f"{label}.obligations[{index}]"
        obligation = _require_object(obligation, OBLIGATION_KEYS, current)
        _require_text(obligation["text"], f"{current}.text")
        source_ids = obligation["source_ids"]
        if type(source_ids) is not list or not source_ids:
            raise ValidationError(f"{current}.source_ids must be a nonempty list")
        for offset, source_id in enumerate(source_ids):
            source_id = _require_text(source_id, f"{current}.source_ids[{offset}]")
            if source_id not in message_positions:
                raise ValidationError(f"{current} cites an unknown message ID")
            if message_positions[source_id] > query_position:
                raise ValidationError(f"{current} contains a future citation")

    visible_ids = [
        message_id
        for message_id, position in message_positions.items()
        if position <= query_position
    ]
    record_focus_schema(visible_ids)


def validate_document(document: Any) -> dict[str, Any]:
    """Validate one conversation without expanding any query prefix."""
    document = _require_object(document, DOCUMENT_KEYS, "document")
    if type(document["schema_version"]) is not int or document["schema_version"] != 1:
        raise ValidationError("schema_version must be integer 1")
    _require_text(document["conversation_id"], "conversation_id")
    _require_text(document["family_id"], "family_id")
    if not isinstance(document["split"], str) or document["split"] not in SPLITS:
        raise ValidationError("split must be fit, dev, or withheld")

    messages = document["messages"]
    if type(messages) is not list or len(messages) < EXPECTED_QUERIES:
        raise ValidationError("messages must be a list containing the query messages")
    message_positions: dict[str, int] = {}
    handle_ids: set[str] = set()
    for index, message in enumerate(messages):
        label = f"messages[{index}]"
        if type(message) is not dict:
            raise ValidationError(f"{label} must be an object")
        keys = set(message)
        if not MESSAGE_REQUIRED_KEYS <= keys or not keys <= (
            MESSAGE_REQUIRED_KEYS | MESSAGE_OPTIONAL_KEYS
        ):
            raise ValidationError(f"{label} has missing or unknown fields")
        message_id = _require_text(message["message_id"], f"{label}.message_id")
        if message_id in message_positions:
            raise ValidationError("message IDs must be unique within a conversation")
        message_positions[message_id] = index
        if not isinstance(message["role"], str) or message["role"] not in ROLES:
            raise ValidationError(f"{label}.role is invalid")
        _require_text(message["text"], f"{label}.text")
        if "task_handle" in message:
            _require_text(message["task_handle"], f"{label}.task_handle")
            if message["role"] != "user":
                raise ValidationError("task_handle occurs only on user work requests")
            handle_ids.add(message_id)

    queries = document["queries"]
    if type(queries) is not list or len(queries) != EXPECTED_QUERIES:
        raise ValidationError("queries must contain exactly three objects")
    query_ids: list[str] = []
    query_positions: list[int] = []
    for index, query in enumerate(queries):
        label = f"queries[{index}]"
        query = _require_object(query, QUERY_KEYS, label)
        message_id = _require_text(query["message_id"], f"{label}.message_id")
        if message_id in query_ids:
            raise ValidationError("query message IDs must be distinct")
        if message_id not in message_positions:
            raise ValidationError(f"{label} identifies an unknown source message")
        position = message_positions[message_id]
        message = messages[position]
        if message["role"] != "user" or "task_handle" not in message:
            raise ValidationError(f"{label} must identify a user work request")
        query_ids.append(message_id)
        query_positions.append(position)
        _validate_target(
            query["target"],
            message_positions=message_positions,
            query_position=position,
            label=f"{label}.target",
        )
    if query_positions != sorted(query_positions):
        raise ValidationError("query order must follow source order")
    if set(query_ids) != handle_ids:
        raise ValidationError("every task_handle message must have exactly one query")
    if query_positions[-1] != len(messages) - 1:
        raise ValidationError("final query must identify the final source message")
    return document


def validate_corpus(documents: Any) -> list[dict[str, Any]]:
    """Validate identities and split assignment before prefix expansion."""
    if type(documents) is not list or not documents:
        raise ValidationError("documents must be a nonempty list")
    conversation_ids: set[str] = set()
    family_splits: dict[str, str] = {}
    for document in documents:
        validate_document(document)
        conversation_id = document["conversation_id"]
        if conversation_id in conversation_ids:
            raise ValidationError("conversation IDs must be unique")
        conversation_ids.add(conversation_id)
        family_id = document["family_id"]
        split = document["split"]
        previous = family_splits.setdefault(family_id, split)
        if previous != split:
            raise ValidationError(f"family {family_id!r} crosses splits")
    return documents


def load_documents(paths: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Read every path before reporting parse or corpus-validation failures."""
    if isinstance(paths, (str, bytes, Path)):
        raise TypeError("paths must be a sequence, not one path")
    values: list[dict[str, Any]] = []
    receipts: list[dict[str, Any]] = []
    errors: list[str] = []
    for raw_path in paths:
        path = Path(raw_path)
        receipt = {
            "path": str(path),
            "bytes": None,
            "sha256": None,
            "conversation_id": None,
            "family_id": None,
            "split": None,
            "read_error": None,
            "parse_error": None,
        }
        receipts.append(receipt)
        try:
            body = path.read_bytes()
            receipt["bytes"] = len(body)
            receipt["sha256"] = _sha_bytes(body)
        except Exception as exc:
            receipt["read_error"] = _error(exc)
            errors.append(receipt["read_error"])
            continue
        try:
            value = _parse_json(body)
            if type(value) is not dict:
                raise ValidationError("each input file must contain one JSON object")
        except Exception as exc:
            receipt["parse_error"] = _error(exc)
            errors.append(receipt["parse_error"])
            continue
        values.append(value)
        for key in ("conversation_id", "family_id", "split"):
            if isinstance(value.get(key), str):
                receipt[key] = value[key]
    if errors:
        error = ValidationError(f"input read/parse failures: {errors}")
        error.input_receipts = receipts
        raise error
    try:
        validate_corpus(values)
    except Exception as exc:
        exc.input_receipts = receipts
        raise
    return values, receipts


@lru_cache(maxsize=1)
def load_tokenizer():
    """Load only the verified local tokenizer; this never loads model weights."""
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(MODEL_PATH, local_files_only=True)


def _token_ids(value: Any, label: str) -> tuple[int, ...]:
    if type(value) is not list or any(
        type(item) is not int or item < 0 for item in value
    ):
        raise ValidationError(f"{label} must be a list of nonnegative token IDs")
    return tuple(value)


def _encode(tokenizer: Any, text: str, label: str) -> tuple[int, ...]:
    try:
        value = tokenizer.encode(text, add_special_tokens=False)
    except Exception as exc:
        raise ValidationError(f"{label} tokenization failed: {exc}") from exc
    return _token_ids(value, label)


def _assert_natural_text(tokenizer: Any, text: str, label: str) -> None:
    ids = _encode(tokenizer, text, label)
    reserved = set(tokenizer.all_special_ids)
    forbidden = [token_id for token_id in ids if token_id in reserved]
    if forbidden:
        raise ValidationError(f"{label} contains a reserved token: {forbidden}")


def _template_ids(tokenizer: Any, messages: list[dict[str, str]]) -> tuple[int, ...]:
    try:
        value = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            enable_thinking=False,
            return_dict=False,
        )
    except Exception as exc:
        raise ValidationError(f"chat template tokenization failed: {exc}") from exc
    return _token_ids(value, "chat template token IDs")


@dataclass(frozen=True, slots=True)
class PreparedRow:
    conversation_id: str
    family_id: str
    split: str
    query_index: int
    query_message_id: str
    task_handle: str
    message_count: int
    message_band: str | None
    source_prefix: tuple[dict[str, Any], ...]
    prompt_messages: tuple[dict[str, str], ...]
    prefix_text: str
    target_text: str
    prefix_ids: tuple[int, ...]
    target_ids: tuple[int, ...]
    target_with_eos_ids: tuple[int, ...]
    input_ids: tuple[int, ...]
    labels: tuple[int, ...]
    attention_mask: tuple[int, ...]
    loss_positions: tuple[int, ...]
    prefix_length: int
    target_length: int
    full_length: int
    eos_token_id: int
    boundary_construction: str
    joint_tokenization_equal: bool

    def receipt(self) -> dict[str, Any]:
        source_prefix = copy.deepcopy(list(self.source_prefix))
        prompt_messages = copy.deepcopy(list(self.prompt_messages))
        return {
            "conversation_id": self.conversation_id,
            "family_id": self.family_id,
            "split": self.split,
            "query_index": self.query_index,
            "query_message_id": self.query_message_id,
            "task_handle": self.task_handle,
            "message_count": self.message_count,
            "message_band": self.message_band,
            "source_prefix": source_prefix,
            "source_prefix_sha256": _sha_bytes(_json_bytes(source_prefix)),
            "prompt_messages": prompt_messages,
            "prompt_messages_sha256": _sha_bytes(_json_bytes(prompt_messages)),
            "prefix_text": self.prefix_text,
            "prefix_text_sha256": _sha_text(self.prefix_text),
            "target_text": self.target_text,
            "target_text_sha256": _sha_text(self.target_text),
            "prefix_ids": list(self.prefix_ids),
            "target_ids": list(self.target_ids),
            "target_with_eos_ids": list(self.target_with_eos_ids),
            "input_ids": list(self.input_ids),
            "labels": list(self.labels),
            "attention_mask": list(self.attention_mask),
            "loss_positions": list(self.loss_positions),
            "prefix_length": self.prefix_length,
            "target_length": self.target_length,
            "full_length": self.full_length,
            "eos_token_id": self.eos_token_id,
            "supervised_tokens": len(self.loss_positions),
            "masked_prefix_tokens": self.prefix_length,
            "target_eos_count": self.target_with_eos_ids.count(self.eos_token_id),
            "boundary_construction": self.boundary_construction,
            "joint_tokenization_equal": self.joint_tokenization_equal,
        }


def _message_band(message_count: int) -> str | None:
    for name, values in MESSAGE_BANDS.items():
        if message_count in values:
            return name
    return None


def prepare_row(document: Any, query_index: int, tokenizer: Any = None) -> PreparedRow:
    """Build exact prefill IDs followed by separately encoded target IDs and EOS."""
    validate_document(document)
    if type(query_index) is not int or not 0 <= query_index < EXPECTED_QUERIES:
        raise IndexError("query_index is out of range")
    tokenizer = tokenizer or load_tokenizer()
    query = document["queries"][query_index]
    positions = {
        message["message_id"]: index
        for index, message in enumerate(document["messages"])
    }
    query_position = positions[query["message_id"]]
    prefix = copy.deepcopy(document["messages"][: query_position + 1])
    current_message = prefix[-1]

    for index, message in enumerate(prefix):
        _assert_natural_text(
            tokenizer, message["message_id"], f"messages[{index}].message_id"
        )
        _assert_natural_text(tokenizer, message["text"], f"messages[{index}].text")
        if "task_handle" in message:
            _assert_natural_text(
                tokenizer,
                message["task_handle"],
                f"messages[{index}].task_handle",
            )
    for index, obligation in enumerate(query["target"]["obligations"]):
        _assert_natural_text(
            tokenizer,
            obligation["text"],
            f"queries[{query_index}].target.obligations[{index}].text",
        )
        for offset, source_id in enumerate(obligation["source_ids"]):
            _assert_natural_text(
                tokenizer,
                source_id,
                f"queries[{query_index}].target.obligations[{index}]"
                f".source_ids[{offset}]",
            )

    source_events = _json_text(prefix)
    prompt_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": USER_PROMPT.format(
                task_handle=current_message["task_handle"],
                source_events=source_events,
            ),
        },
    ]
    try:
        prefix_text = tokenizer.apply_chat_template(
            prompt_messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
    except Exception as exc:
        raise ValidationError(f"chat template rendering failed: {exc}") from exc
    if not isinstance(prefix_text, str) or not prefix_text:
        raise ValidationError("chat template must return a nonempty text prefix")
    prefix_ids = _encode(tokenizer, prefix_text, "generation prefix")
    direct_template_ids = _template_ids(tokenizer, prompt_messages)
    if direct_template_ids != prefix_ids:
        raise ValidationError("text and token chat-template prefixes disagree")
    if tokenizer.decode(list(prefix_ids), skip_special_tokens=False) != prefix_text:
        raise ValidationError("generation prefix token IDs do not decode exactly")

    target_text = _json_text(query["target"])
    target_ids = _encode(tokenizer, target_text, "target JSON")
    if not target_ids:
        raise ValidationError("target JSON has empty supervision")
    reserved_target = set(target_ids) & set(tokenizer.all_special_ids)
    if reserved_target:
        raise ValidationError(
            f"target JSON contains reserved token IDs: {sorted(reserved_target)}"
        )
    if tokenizer.decode(list(target_ids), skip_special_tokens=False) != target_text:
        raise ValidationError("target token IDs do not decode to exact JSON")
    eos_token_id = tokenizer.eos_token_id
    if type(eos_token_id) is not int or eos_token_id < 0:
        raise ValidationError("tokenizer must define one nonnegative EOS token ID")
    target_with_eos = target_ids + (eos_token_id,)
    input_ids = prefix_ids + target_with_eos
    labels = (-100,) * len(prefix_ids) + target_with_eos
    attention_mask = (1,) * len(input_ids)
    loss_positions = tuple(range(len(prefix_ids), len(input_ids)))
    if not loss_positions or labels[loss_positions[0]] != target_ids[0]:
        raise ValidationError("first target loss position is shifted")
    if labels[-1] != eos_token_id or any(
        label != -100 for label in labels[: len(prefix_ids)]
    ):
        raise ValidationError("prefix/EOS loss mask is invalid")
    expected_decoding = prefix_text + target_text + tokenizer.eos_token
    if (
        tokenizer.decode(list(input_ids), skip_special_tokens=False)
        != expected_decoding
    ):
        raise ValidationError("constructed causal sequence does not decode exactly")
    joint_ids = _encode(tokenizer, prefix_text + target_text, "joint prefix and target")
    return PreparedRow(
        conversation_id=document["conversation_id"],
        family_id=document["family_id"],
        split=document["split"],
        query_index=query_index,
        query_message_id=query["message_id"],
        task_handle=current_message["task_handle"],
        message_count=len(document["messages"]),
        message_band=_message_band(len(document["messages"])),
        source_prefix=tuple(prefix),
        prompt_messages=tuple(prompt_messages),
        prefix_text=prefix_text,
        target_text=target_text,
        prefix_ids=prefix_ids,
        target_ids=target_ids,
        target_with_eos_ids=target_with_eos,
        input_ids=input_ids,
        labels=labels,
        attention_mask=attention_mask,
        loss_positions=loss_positions,
        prefix_length=len(prefix_ids),
        target_length=len(target_with_eos),
        full_length=len(input_ids),
        eos_token_id=eos_token_id,
        boundary_construction="separate_prefix_target_ids",
        joint_tokenization_equal=(joint_ids == prefix_ids + target_ids),
    )


def prepare_rows(documents: Any, tokenizer: Any = None) -> list[PreparedRow]:
    """Expand validated conversations into their three source-prefix rows."""
    validate_corpus(documents)
    tokenizer = tokenizer or load_tokenizer()
    return [
        prepare_row(document, query_index, tokenizer)
        for document in documents
        for query_index in range(EXPECTED_QUERIES)
    ]


def _validate_prepared_row(row: PreparedRow) -> None:
    if not (
        len(row.prefix_ids) == row.prefix_length
        and len(row.target_with_eos_ids) == row.target_length
        and len(row.input_ids)
        == len(row.labels)
        == len(row.attention_mask)
        == row.full_length
        == row.prefix_length + row.target_length
    ):
        raise ValidationError("prepared row lengths disagree")
    if not row.target_ids or row.target_with_eos_ids != (
        row.target_ids + (row.eos_token_id,)
    ):
        raise ValidationError("prepared row target has the wrong EOS boundary")
    if row.target_with_eos_ids.count(row.eos_token_id) != 1:
        raise ValidationError("prepared row must contain exactly one target EOS")
    if row.input_ids != row.prefix_ids + row.target_with_eos_ids:
        raise ValidationError("prepared row input is truncated or reordered")
    expected_labels = (-100,) * row.prefix_length + row.target_with_eos_ids
    expected_positions = tuple(range(row.prefix_length, row.full_length))
    if row.labels != expected_labels or row.loss_positions != expected_positions:
        raise ValidationError("prepared row loss positions are shifted")
    if row.attention_mask != (1,) * row.full_length:
        raise ValidationError("prepared row attention mask is invalid")


def collate(rows: Any, *, pad_token_id: int) -> dict[str, Any]:
    """Right-pad exact prepared rows without adding or moving supervision."""
    if type(rows) is not list or not rows:
        raise ValidationError("collation rows must be a nonempty list")
    if type(pad_token_id) is not int or pad_token_id < 0:
        raise ValidationError("pad_token_id must be a nonnegative integer")
    if any(not isinstance(row, PreparedRow) for row in rows):
        raise ValidationError("collation accepts only PreparedRow values")
    for row in rows:
        _validate_prepared_row(row)
    width = max(row.full_length for row in rows)
    input_ids: list[list[int]] = []
    attention_mask: list[list[int]] = []
    labels: list[list[int]] = []
    row_ids = []
    for row in rows:
        padding = width - row.full_length
        input_ids.append(list(row.input_ids) + [pad_token_id] * padding)
        attention_mask.append(list(row.attention_mask) + [0] * padding)
        labels.append(list(row.labels) + [-100] * padding)
        row_ids.append(
            {
                "conversation_id": row.conversation_id,
                "query_message_id": row.query_message_id,
            }
        )
    return {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "labels": labels,
        "row_ids": row_ids,
        "batch_size": len(rows),
        "width": width,
        "padding_side": "right",
        "pad_token_id": pad_token_id,
        "padding_tokens": sum(width - row.full_length for row in rows),
    }


def _asset_hashes() -> dict[str, str]:
    return {
        name: _sha_bytes((MODEL_PATH / name).read_bytes()) for name in TOKENIZER_ASSETS
    }


def _code_hashes() -> dict[str, str]:
    paths = (Path(__file__).resolve(),)
    return {
        str(path.relative_to(ROOT)): _sha_bytes(path.read_bytes()) for path in paths
    }


def _environment_receipt() -> dict[str, Any]:
    versions = {}
    for name in PACKAGE_NAMES:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return {
        "sys_executable": sys.executable,
        "resolved_executable": str(Path(sys.executable).resolve()),
        "sys_prefix": sys.prefix,
        "python_version": platform.python_version(),
        "implementation": platform.python_implementation(),
        "distributions": versions,
    }


def _length_receipt(values: list[int]) -> dict[str, Any]:
    if not values:
        raise ValidationError("length distribution must be nonempty")
    return {
        "count": len(values),
        "values": list(values),
        "minimum": min(values),
        "median": statistics.median(values),
        "maximum": max(values),
    }


def _calibration_bands(documents: list[dict[str, Any]]) -> dict[str, int]:
    counts = {name: 0 for name in MESSAGE_BANDS}
    for document in documents:
        band = _message_band(len(document["messages"]))
        if band is None:
            raise ValidationError(
                "calibration message count must be in a registered message band"
            )
        counts[band] += 1
    if any(value != 2 for value in counts.values()):
        raise ValidationError("calibration requires two documents in each message band")
    return counts


def preview(paths: Any, *, tokenizer: Any = None) -> dict[str, Any]:
    """Produce the complete zero-call CPU preparation receipt for six FIT files."""
    started = time.monotonic()
    documents, input_receipts = load_documents(paths)
    if len(documents) != CALIBRATION_DOCUMENTS:
        raise ValidationError("calibration preview requires exactly six documents")
    if any(document["split"] != "fit" for document in documents):
        raise ValidationError("calibration preview accepts only FIT documents")
    bands = _calibration_bands(documents)
    tokenizer = tokenizer or load_tokenizer()
    rows = prepare_rows(documents, tokenizer)
    if len(rows) != CALIBRATION_ROWS:
        raise ValidationError("calibration preview must retain all 18 query rows")
    batch = collate(rows, pad_token_id=tokenizer.pad_token_id)
    row_receipts = [row.receipt() for row in rows]
    prefix_lengths = [row.prefix_length for row in rows]
    target_lengths = [row.target_length for row in rows]
    full_lengths = [row.full_length for row in rows]
    maxima = {}
    for band in MESSAGE_BANDS:
        selected = [row for row in rows if row.message_band == band]
        maxima[band] = {
            "documents": bands[band],
            "rows": len(selected),
            "maximum_prefix_tokens": max(row.prefix_length for row in selected),
            "maximum_target_tokens_with_eos": max(
                row.target_length for row in selected
            ),
            "maximum_full_tokens": max(row.full_length for row in selected),
        }
    chat_template = tokenizer.chat_template
    if not isinstance(chat_template, str) or not chat_template:
        raise ValidationError("tokenizer must expose one nonempty chat template")
    abstract_schema = record_focus_schema(["VISIBLE_SOURCE_ID"])
    base_assets_hash = (
        _sha_bytes(BASE_ASSETS_PATH.read_bytes())
        if BASE_ASSETS_PATH.is_file()
        else None
    )
    return {
        "schema_version": 1,
        "kind": "source-interpreter-cpu-preview",
        "status": "PASS",
        "fit_on": "none",
        "model_calls": 0,
        "model_loaded": False,
        "gpu_used": False,
        "documents": len(documents),
        "rows": len(rows),
        "splits": {"fit": len(documents), "dev": 0, "withheld": 0},
        "inputs": input_receipts,
        "message_bands": bands,
        "row_receipts": row_receipts,
        "lengths": {
            "prefix_tokens": _length_receipt(prefix_lengths),
            "target_tokens_with_eos": _length_receipt(target_lengths),
            "full_tokens": _length_receipt(full_lengths),
            "maxima_by_message_band": maxima,
            "no_truncation": True,
            "sequence_or_output_cap_selected": False,
        },
        "collation": {
            "batch_size": batch["batch_size"],
            "width": batch["width"],
            "padding_side": batch["padding_side"],
            "pad_token_id": batch["pad_token_id"],
            "padding_tokens": batch["padding_tokens"],
            "input_ids_sha256": _sha_bytes(_json_bytes(batch["input_ids"])),
            "attention_mask_sha256": _sha_bytes(_json_bytes(batch["attention_mask"])),
            "labels_sha256": _sha_bytes(_json_bytes(batch["labels"])),
        },
        "format": {
            "system_prompt": SYSTEM_PROMPT,
            "system_prompt_sha256": _sha_text(SYSTEM_PROMPT),
            "user_prompt_template": USER_PROMPT,
            "user_prompt_template_sha256": _sha_text(USER_PROMPT),
            "record_focus_schema": abstract_schema,
            "record_focus_schema_sha256": _sha_bytes(_json_bytes(abstract_schema)),
            "chat_template": chat_template,
            "chat_template_sha256": _sha_text(chat_template),
            "enable_thinking": False,
            "add_generation_prompt": True,
            "target_json": "UTF-8, unescaped Unicode, sorted keys, compact separators",
            "boundary_construction": "separate_prefix_target_ids",
            "eos_tokens_appended": 1,
        },
        "tokenizer": {
            "path": str(MODEL_PATH),
            "class": type(tokenizer).__name__,
            "name_or_path": tokenizer.name_or_path,
            "eos_token": tokenizer.eos_token,
            "eos_token_id": tokenizer.eos_token_id,
            "pad_token": tokenizer.pad_token,
            "pad_token_id": tokenizer.pad_token_id,
            "all_special_ids": list(tokenizer.all_special_ids),
            "asset_sha256": _asset_hashes(),
            "base_assets_receipt_path": str(BASE_ASSETS_PATH),
            "base_assets_receipt_sha256": base_assets_hash,
        },
        "code_sha256": _code_hashes(),
        "environment": _environment_receipt(),
        "structural_limit": (
            "Shape, identity, split, visibility, token and mask validation does not "
            "establish semantic coverage, authority or family independence."
        ),
        "elapsed_seconds": time.monotonic() - started,
    }
