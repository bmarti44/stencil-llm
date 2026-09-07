"""Pure structural adapter for independently authored maintenance episodes.

The authored JSON contains natural messages and gold annotations only.  This
module never executes message content or generated code; it converts annotations
to the existing typed register API and checks every declared effective-state
probe by replaying that API.

The compact authoring shape labels only expected key/value pairs.  Scope and
kind in :class:`EffectiveRule` are therefore resolved from the typed gold
operations.  Validation certifies exact probe coverage and authored key/value
snapshots; it is not an independent annotation of gold-operation scope or kind.
"""

import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

from .register import (
    AUTHORITY,
    REQUEST_KINDS,
    Entry,
    InvalidEntry,
    Register,
    Scope,
    Source,
    Unsupported,
)

SCHEMA_VERSION = 1
SPLITS = frozenset({"dev", "eval"})
MESSAGE_ROLES = frozenset({"system", "developer", "user", "assistant", "tool"})
AUTHORED_ACTIONS = frozenset({"add", "supersedes", "cancels", "reinstates"})


class SchemaError(ValueError):
    """The authored structure or its typed lifecycle trace is invalid."""


@dataclass(frozen=True)
class Metadata:
    author: str
    model: str
    lineage: str


@dataclass(frozen=True)
class Message:
    message_id: str
    role: str
    content: str


@dataclass(frozen=True)
class TaskSpec:
    domain: str
    task_handles: tuple[str, ...]
    request_kinds: tuple[str, ...]


@dataclass(frozen=True)
class EffectiveRule:
    key: str
    kind: str
    value: str
    scope: Scope


@dataclass(frozen=True)
class EffectiveView:
    task_handle: str | None
    request_kind: str
    rules: tuple[EffectiveRule, ...]


@dataclass(frozen=True)
class MaintenanceRound:
    index: int
    messages: tuple[Message, ...]
    expected_ops: tuple[Entry, ...]
    expected_effective: tuple[EffectiveView, ...]
    rationale: str


@dataclass(frozen=True)
class MaintenanceEpisode:
    episode_id: str
    split: str
    task: TaskSpec
    rounds: tuple[MaintenanceRound, ...]


@dataclass(frozen=True)
class MaintenanceAllocation:
    schema_version: int
    split: str
    metadata: Metadata
    episodes: tuple[MaintenanceEpisode, ...]


def _nonempty(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SchemaError(f"{path} must be a nonempty string")
    return value


def _record(value: Any, fields: set[str], path: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise SchemaError(f"{path} must be an object")
    unknown, missing = set(value) - fields, fields - set(value)
    if unknown:
        raise SchemaError(f"{path} has unknown fields: {sorted(unknown)}")
    if missing:
        raise SchemaError(f"{path} is missing fields: {sorted(missing)}")
    return value


def _list(value: Any, path: str) -> list[Any]:
    if type(value) is not list:
        raise SchemaError(f"{path} must be an array")
    return value


def _semantic(version) -> EffectiveRule:
    entry = version.entry
    return EffectiveRule(entry.key, entry.kind, entry.value, entry.scope)


def _expected_views(raw: Any, task: TaskSpec, state: Register, path: str):
    if type(raw) is not dict:
        raise SchemaError(f"{path} must be an object")
    probes = {"GLOBAL", *task.task_handles}
    if set(raw) != probes:
        raise SchemaError(
            f"{path} must contain exactly the effective probes {sorted(probes)}"
        )
    views = []
    for name in sorted(probes):
        handle = None if name == "GLOBAL" else name
        values = raw[name]
        if type(values) is not dict or any(
            not isinstance(k, str) or not k or not isinstance(v, str) or not v
            for k, v in values.items()
        ):
            raise SchemaError(f"{path}.{name} must map nonempty string keys to values")
        for request_kind in task.request_kinds:
            actual = {v.entry.key: v for v in state.live(handle, request_kind)}
            unknown = set(values) - set(actual)
            if unknown:
                raise SchemaError(
                    f"{path}.{name} cannot resolve expected keys: {sorted(unknown)}"
                )
            rules = tuple(
                EffectiveRule(
                    key, actual[key].entry.kind, value, actual[key].entry.scope
                )
                for key, value in sorted(values.items())
            )
            views.append(EffectiveView(handle, request_kind, rules))
    return tuple(views)


def validate_episode(episode: MaintenanceEpisode) -> MaintenanceEpisode:
    if not isinstance(episode, MaintenanceEpisode):
        raise SchemaError("typed MaintenanceEpisode required")
    _nonempty(episode.episode_id, "episode_id")
    if episode.split not in SPLITS:
        raise SchemaError("invalid episode split")
    task = episode.task
    if not isinstance(task, TaskSpec):
        raise SchemaError("typed TaskSpec required")
    _nonempty(task.domain, "task.domain")
    if (
        not task.task_handles
        or len(set(task.task_handles)) != len(task.task_handles)
        or any(
            not isinstance(x, str) or not x or x == "GLOBAL" for x in task.task_handles
        )
    ):
        raise SchemaError("task handles must be distinct nonempty non-GLOBAL strings")
    if (
        not task.request_kinds
        or len(set(task.request_kinds)) != len(task.request_kinds)
        or not set(task.request_kinds) <= REQUEST_KINDS
    ):
        raise SchemaError("invalid task request kinds")
    if not episode.rounds or tuple(r.index for r in episode.rounds) != tuple(
        range(len(episode.rounds))
    ):
        raise SchemaError("round indices must be contiguous from zero")

    state = Register(task_handles=frozenset(task.task_handles))
    message_ids: set[str] = set()
    event_ids: set[str] = set()
    expected_probes = {
        (handle, kind)
        for handle in (None, *task.task_handles)
        for kind in task.request_kinds
    }
    for round_ in episode.rounds:
        if not isinstance(round_, MaintenanceRound) or not round_.messages:
            raise SchemaError(f"round {round_.index} needs typed messages")
        messages = {}
        for message in round_.messages:
            if not isinstance(message, Message):
                raise SchemaError(f"round {round_.index} has an untyped message")
            _nonempty(message.message_id, "message_id")
            _nonempty(message.content, "message content")
            if message.role not in MESSAGE_ROLES:
                raise SchemaError("invalid message role")
            if message.message_id in message_ids:
                raise SchemaError(f"duplicate message_id: {message.message_id}")
            message_ids.add(message.message_id)
            messages[message.message_id] = message

        for entry in round_.expected_ops:
            if not isinstance(entry, Entry):
                raise SchemaError(f"round {round_.index} has an untyped operation")
            if entry.event_id in event_ids:
                raise SchemaError(f"duplicate event_id: {entry.event_id}")
            event_ids.add(entry.event_id)
            source = messages.get(entry.source.message_id)
            if source is None or source.role != entry.source.role:
                raise SchemaError(
                    "operation source must be a current message with exact role"
                )
            if entry.source.role not in AUTHORITY:
                raise SchemaError("operation source has no rule authority")
            if entry.source.span is not None:
                start, end = entry.source.span
                if end > len(source.content) or entry.text != source.content[start:end]:
                    raise SchemaError(
                        "source span must select operation text by Unicode offset"
                    )
            if entry.action == "completes":
                if (
                    entry.evidence is None
                    or entry.evidence.kind != "user_event"
                    or entry.evidence.reference != entry.source.message_id
                ):
                    raise SchemaError(
                        "completion evidence must reference its current source message"
                    )
            elif entry.evidence is not None:
                raise SchemaError("only completion operations may carry evidence")

        if any(not isinstance(v, EffectiveView) for v in round_.expected_effective):
            raise SchemaError("typed effective views required")
        views = {(v.task_handle, v.request_kind): v for v in round_.expected_effective}
        if (
            len(views) != len(round_.expected_effective)
            or set(views) != expected_probes
        ):
            raise SchemaError(
                "round must contain exactly all task/global effective probes"
            )
        try:
            state = replace(state, generation=round_.index).apply(round_.expected_ops)
            for probe, view in views.items():
                if any(not isinstance(rule, EffectiveRule) for rule in view.rules):
                    raise SchemaError("typed effective rules required")
                if len({r.key for r in view.rules}) != len(view.rules):
                    raise SchemaError("duplicate effective rule key")
                actual = tuple(
                    sorted(
                        (_semantic(v) for v in state.live(*probe)),
                        key=lambda r: r.key,
                    )
                )
                expected = tuple(sorted(view.rules, key=lambda r: r.key))
                if actual != expected:
                    raise SchemaError(
                        f"round {round_.index} expected effective state mismatch "
                        f"at {probe}"
                    )
        except (InvalidEntry, Unsupported) as exc:
            raise SchemaError(f"round {round_.index} invalid lifecycle: {exc}") from exc
        _nonempty(round_.rationale, f"round {round_.index} rationale")
    return episode


def validate_allocation(
    allocation: MaintenanceAllocation, *, expected_rounds: int | None = None
) -> MaintenanceAllocation:
    if not isinstance(allocation, MaintenanceAllocation):
        raise SchemaError("typed MaintenanceAllocation required")
    if allocation.schema_version != SCHEMA_VERSION or allocation.split not in SPLITS:
        raise SchemaError("invalid schema version or allocation split")
    if not isinstance(allocation.metadata, Metadata):
        raise SchemaError("typed Metadata required")
    for field, value in asdict(allocation.metadata).items():
        _nonempty(value, f"metadata.{field}")
    ids, events = set(), set()
    if not allocation.episodes:
        raise SchemaError("allocation must contain episodes")
    for episode in allocation.episodes:
        if episode.episode_id in ids:
            raise SchemaError(f"duplicate episode_id: {episode.episode_id}")
        ids.add(episode.episode_id)
        if episode.split != allocation.split:
            raise SchemaError("episode split differs from allocation")
        if expected_rounds is not None and len(episode.rounds) != expected_rounds:
            raise SchemaError(f"episode must contain exactly {expected_rounds} rounds")
        validate_episode(episode)
        for round_ in episode.rounds:
            for entry in round_.expected_ops:
                if entry.event_id in events:
                    raise SchemaError(
                        f"duplicate event_id across allocation: {entry.event_id}"
                    )
                events.add(entry.event_id)
    conversations = [_conversation_fingerprint(e) for e in allocation.episodes]
    if len(set(conversations)) != len(conversations):
        raise SchemaError("duplicate conversation content across allocation")
    return allocation


def validate_allocations(dev: MaintenanceAllocation, evaluation: MaintenanceAllocation):
    validate_allocation(dev)
    validate_allocation(evaluation)
    if dev.split != "dev":
        raise SchemaError("expected dev allocation")
    if evaluation.split != "eval":
        raise SchemaError("expected eval allocation")
    dev_ids = {e.episode_id for e in dev.episodes}
    eval_ids = {e.episode_id for e in evaluation.episodes}
    if dev_ids & eval_ids:
        raise SchemaError("duplicate episode_id across allocations")
    dev_conversations = {_conversation_fingerprint(e) for e in dev.episodes}
    eval_conversations = {_conversation_fingerprint(e) for e in evaluation.episodes}
    if dev_conversations & eval_conversations:
        raise SchemaError("duplicate conversation content across allocations")
    return dev, evaluation


def _conversation_fingerprint(episode: MaintenanceEpisode) -> str:
    messages = [
        {"role": message.role, "content": message.content}
        for round_ in episode.rounds
        for message in round_.messages
    ]
    return json.dumps(
        messages, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def adapt_authored_bank(
    raw: Any,
    *,
    expected_episodes: int | None = None,
    expected_rounds: int | None = None,
) -> MaintenanceAllocation:
    top = _record(raw, {"author", "model", "split", "lineage", "episodes"}, "bank")
    metadata = Metadata(
        *(_nonempty(top[k], f"bank.{k}") for k in ("author", "model", "lineage"))
    )
    split = _nonempty(top["split"], "bank.split")
    if split not in SPLITS:
        raise SchemaError("invalid bank split")
    raw_episodes = _list(top["episodes"], "bank.episodes")
    if expected_episodes is not None and len(raw_episodes) != expected_episodes:
        raise SchemaError(f"bank must contain exactly {expected_episodes} episodes")
    episodes = []
    for ei, item in enumerate(raw_episodes):
        ep = _record(
            item,
            {"episode_id", "domain", "task_handles", "initial_rules", "rounds"},
            f"episodes[{ei}]",
        )
        if _list(ep["initial_rules"], f"episodes[{ei}].initial_rules"):
            raise SchemaError("authored initial_rules must be empty")
        handles = tuple(
            _nonempty(x, "task handle")
            for x in _list(ep["task_handles"], "task_handles")
        )
        task = TaskSpec(_nonempty(ep["domain"], "domain"), handles, ("code_answer",))
        state = Register(task_handles=frozenset(handles))
        created = {}
        rounds = []
        for ri, item_round in enumerate(_list(ep["rounds"], "rounds")):
            row = _record(
                item_round,
                {
                    "index",
                    "role",
                    "message",
                    "gold_ops",
                    "expected_live",
                    "rationale",
                },
                f"rounds[{ri}]",
            )
            if type(row["index"]) is not int or row["index"] != ri:
                raise SchemaError("authored round indices must be contiguous from zero")
            role = _nonempty(row["role"], "round role")
            if role not in {"user", "tool"}:
                raise SchemaError("authored round role must be user or tool")
            message_id = f"{_nonempty(ep['episode_id'], 'episode_id')}:round:{ri}"
            message = Message(
                message_id, role, _nonempty(row["message"], "round message")
            )
            raw_ops = _list(row["gold_ops"], "gold_ops")
            if role == "tool" and raw_ops:
                raise SchemaError("tool round cannot contain gold operations")
            ops = []
            for oi, item_op in enumerate(raw_ops):
                op = _record(
                    item_op,
                    {
                        "action",
                        "key",
                        "kind",
                        "value",
                        "task_handle",
                        "target_event",
                        "event_id",
                    },
                    f"gold_ops[{oi}]",
                )
                action = _nonempty(op["action"], "operation action")
                if action not in AUTHORED_ACTIONS:
                    raise SchemaError("unsupported authored action")
                target_event = op["target_event"]
                if action == "add":
                    if target_event is not None:
                        raise SchemaError("add target_event must be null")
                    target_version = None
                else:
                    if not isinstance(target_event, str) or target_event not in created:
                        raise SchemaError(
                            "non-add target_event must name an earlier created version"
                        )
                    target = created[target_event]
                    target_version = target.version
                handle = op["task_handle"]
                if handle is not None and handle not in handles:
                    raise SchemaError("operation task_handle is undeclared")
                key = _nonempty(op["key"], "operation key")
                scope = Scope(handle, ("code_answer",))
                if action != "add" and (
                    target.entry.key != key or target.entry.scope != scope
                ):
                    raise SchemaError(
                        "target_event must address the operation's exact key and scope"
                    )
                try:
                    entry = Entry(
                        action=action,
                        key=key,
                        scope=scope,
                        kind=_nonempty(op["kind"], "operation kind"),
                        value=_nonempty(op["value"], "operation value"),
                        event_id=_nonempty(op["event_id"], "operation event_id"),
                        source=Source(role, message_id),
                        text=None,
                        target_version=target_version,
                        evidence=None,
                    )
                    state = state.apply((entry,))
                except (InvalidEntry, Unsupported) as exc:
                    raise SchemaError(f"round {ri} invalid lifecycle: {exc}") from exc
                if action in {"add", "supersedes", "reinstates"}:
                    created[entry.event_id] = next(
                        v for v in state.versions if v.entry.event_id == entry.event_id
                    )
                ops.append(entry)
            expected = _expected_views(
                row["expected_live"], task, state, "expected_live"
            )
            rounds.append(
                MaintenanceRound(
                    ri,
                    (message,),
                    tuple(ops),
                    expected,
                    _nonempty(row["rationale"], "rationale"),
                )
            )
        episodes.append(
            MaintenanceEpisode(
                _nonempty(ep["episode_id"], "episode_id"),
                split,
                task,
                tuple(rounds),
            )
        )
    allocation = MaintenanceAllocation(SCHEMA_VERSION, split, metadata, tuple(episodes))
    validate_allocation(allocation, expected_rounds=expected_rounds)
    return allocation


def _reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise SchemaError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def loads_authored_bank(text: str, **expectations) -> MaintenanceAllocation:
    try:
        raw = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except json.JSONDecodeError as exc:
        raise SchemaError(f"invalid JSON: {exc.msg}") from exc
    return adapt_authored_bank(raw, **expectations)


def load_authored_bank(path: str | Path, **expectations) -> MaintenanceAllocation:
    return loads_authored_bank(Path(path).read_text(), **expectations)


def canonical_json(allocation: MaintenanceAllocation) -> str:
    validate_allocation(allocation)
    return (
        json.dumps(
            asdict(allocation),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    )
