"""Frozen prepend layout, adapted from stencil.focus3.render.

Token placement copies scripts/focus3_gate.py:Trunk.answer: encode the whole
current user envelope after system/history, then the assistant thinking prefix.
No substring-based parsing or inference of request kind is performed.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass

from .register import Register, Scope


def compact(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def value_gloss(kind, value):
    """Amendment 2: clarify style values without changing rule layout or data."""
    if kind == "style" and str(value).isdigit() and int(value) > 0:
        return f" indent {value} = block bodies indented by exactly {value} spaces."
    return ""


@dataclass(frozen=True)
class Request:
    text: str
    kind: str
    task_handle: str | None = None
    system: str = ""
    history_ids: tuple[int, ...] = ()
    encode: Callable | None = None
    max_tokens: int | None = None
    template_id: str | None = None
    needs_old_body: bool = False
    rule_mode: str = "R"
    rule_text: str = ""


@dataclass(frozen=True)
class RenderedRequest:
    text: str
    envelope: str
    prompt_ids: tuple[int, ...] | None
    prefix_ids: tuple[int, ...] | None
    live: tuple
    tombstones: tuple[str, ...]
    history_messages: tuple = ()


class RenderOverflow(ValueError):
    pass


def render(register: Register, request: Request) -> RenderedRequest:
    live = register.live(request.task_handle, request.kind)
    scope = Scope(request.task_handle, (request.kind,))
    retired = []
    for retirement in register.retirements:
        if not 0 <= register.generation - retirement.generation < 3:
            continue
        old = next(
            v
            for v in register.versions
            if v.entry.key == retirement.key and v.version == retirement.version
        )
        if not old.entry.scope.contains(scope):
            continue
        retired.append(
            f"Retired: {retirement.key} v{retirement.version}; "
            f"no longer binding; reason {retirement.reason}."
        )
    # Compose applicable structured values, independent of presentation arm.
    # Delivery remains stored literally and becomes visible again under verbose.
    compact_format = any(
        v.entry.key == "format" and v.entry.value == "compact" for v in live
    )
    rows = [
        dict(
            key=v.entry.key,
            version=v.version,
            kind=v.entry.kind,
            value=v.entry.value,
            text=v.entry.text,
            default=v.version == 0,
        )
        for v in live
        if not (compact_format and v.entry.key == "delivery")
    ]
    text = (
        "Active rules for this request (subject to system/developer instructions):\n"
        + compact(rows)
        + ("\nRetired rules (not binding):\n" + "\n".join(retired) if retired else "")
        + (
            "\nPending proposals (not binding): "
            + compact(
                [
                    {
                        "action": e.action,
                        "key": e.key,
                        "target_version": e.target_version,
                        "event_id": e.event_id,
                    }
                    for e in register.proposals
                    if e.scope.contains(scope)
                ]
            )
            if any(e.scope.contains(scope) for e in register.proposals)
            else ""
        )
        + "\nApply the active rules while answering the request below."
        "\nCurrent user request:\n" + request.text
    )
    if request.rule_mode == "N":
        text = request.text
    elif request.rule_mode == "T":
        text = request.rule_text + "\n" + request.text
    # O intentionally replicates R byte for byte (historical determinism arm).
    elif request.rule_mode not in {"R", "O"}:
        raise ValueError("unknown rule mode")
    envelope = (
        "<|im_start|>user\n" + text + "<|im_end|>\n"
        "<|im_start|>assistant\n<think>\n\n</think>\n\n"
    )
    ids = prefix = None
    if request.encode is not None:
        prefix = tuple(request.encode(envelope))
        ids = (
            tuple(
                request.encode("<|im_start|>system\n" + request.system + "<|im_end|>\n")
            )
            + tuple(request.history_ids)
            + prefix
        )
    if request.max_tokens is not None:
        if ids is None:
            raise RenderOverflow("token budget requires an encoder")
        if len(ids) > request.max_tokens:
            raise RenderOverflow("full obligations exceed prompt token budget")
    return RenderedRequest(text, envelope, ids, prefix, live, tuple(retired))
