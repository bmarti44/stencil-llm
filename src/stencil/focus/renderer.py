"""Frozen prepend layout, adapted from stencil.focus3.render.

Token placement copies scripts/focus3_gate.py:Trunk.answer: encode the whole
current user envelope after system/history, then the assistant thinking prefix.
No substring-based parsing or inference of request kind is performed.
"""

import json
from collections.abc import Callable
from dataclasses import asdict, dataclass

from .register import Register, Scope


def compact(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


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
        replacement = next((v for v in live if v.entry.key == retirement.key), None)
        target = (
            "default " + compact(replacement.entry.value)
            if replacement and replacement.version == 0
            else f"{replacement.entry.key} v{replacement.version}"
            if replacement
            else "default null (no configured obligation)"
        )
        link = (
            "; reinstated as a new version"
            if replacement
            and replacement.entry.action == "reinstates"
            and replacement.previous == old.version
            else ""
        )
        retired.append(
            f"Retired: {retirement.key} v{retirement.version}; "
            f"no longer binding in {compact(asdict(old.entry.scope))}; "
            f"replaced by {target}; reason {retirement.reason}{link}."
        )
    rows = [
        dict(
            key=v.entry.key,
            version=v.version,
            kind=v.entry.kind,
            value=v.entry.value,
            text=v.entry.text,
            scope=asdict(v.entry.scope),
            provenance=asdict(v.entry.source),
            default=v.version == 0,
        )
        for v in live
    ]
    text = (
        "Active rules for this request (subject to system/developer instructions):\n"
        + compact(rows)
        + "\nRetired rules (not binding):\n"
        + "\n".join(retired)
        + "\nApply the active rules while answering the request below."
        "\nCurrent user request:\n" + request.text
    )
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
