"""One decoder invocation per request; tools run in the caller.

The injected experimental adapter must delegate to the existing
scripts/focus_check40i.py:mask_change -> focus_check40h.mask_change and its
persistent generation path. This module implements no attention/bias algorithm.
"""

import time
from dataclasses import asdict, dataclass, field, replace
from typing import Protocol

from .journal import Journal
from .register import Decision, Entry, InvalidEntry, Register
from .renderer import Request, compact, render


@dataclass(frozen=True)
class Message:
    """Trusted transport envelope. Never construct role/origin from model text.

    entries contains explicitly adopted structured actions, not proposals.
    Quoted/code/tool/assistant payloads must use their actual origin and role.
    """

    message_id: str
    role: str
    text: str
    entries: tuple[Entry, ...] = ()
    origin: str = "direct"
    adopted: bool = False
    tool_results: tuple = ()
    executed_tool_calls: tuple = ()
    artifact_hashes: tuple = ()


@dataclass(frozen=True)
class DecodeResult:
    text: str
    output_ids: tuple[int, ...] | None = None
    eos: int | None = None
    truncated: bool | None = None
    attempted_tool_calls: tuple = ()
    gpu_held_seconds: float = 0.0


class Actuator(Protocol):
    def eligible(self, request: Request, mode: str) -> bool: ...
    def install(self, session, rendered, mode: str) -> dict: ...
    def restore(self) -> None: ...


@dataclass(frozen=True)
class RequestBindings:
    kind: str
    task_handle: str | None
    template_id: str | None


@dataclass(frozen=True)
class ExperimentalFlagState:
    requested: str = "off"
    applied: str = "off"


@dataclass
class Session:
    """Session state; views/bindings are derived to avoid stale duplicate caches.

    journal_cursor counts successfully appended records in this session; callers
    resuming an existing journal must supply its cursor and request_count.
    Experimental flags describe the most recent attempt, even after restoration.
    """

    register: Register
    request: Request
    journal: Journal
    classifier: object | None = None
    actuator_hook: Actuator | None = None
    messages: list = field(default_factory=list)
    rendered_history: list = field(default_factory=list)
    history_ids: tuple[int, ...] = ()
    request_count: int = 0
    journal_cursor: int = 0
    experimental_flag_state: ExperimentalFlagState = field(
        default_factory=ExperimentalFlagState
    )

    @property
    def register_events(self):
        return self.register.events

    @property
    def live_view(self):
        return self.register.live(self.request.task_handle, self.request.kind)

    @property
    def request_bindings(self):
        return RequestBindings(
            self.request.kind, self.request.task_handle, self.request.template_id
        )


def authenticate(messages):
    entries = []
    ids = set()
    for m in messages:
        if m.message_id in ids:
            raise InvalidEntry("ambiguous source message ID")
        ids.add(m.message_id)
        for e in m.entries:
            if (
                not m.adopted
                or m.origin != "direct"
                or m.role not in {"user", "system", "developer"}
            ):
                raise InvalidEntry("entry lacks explicit authenticated adoption")
            if e.source.role != m.role or e.source.message_id != m.message_id:
                raise InvalidEntry("source envelope mismatch")
            if e.source.span is not None and e.source.span[1] > len(m.text):
                raise InvalidEntry("source span out of bounds")
            entries.append(e)
    return entries


def generate_once(session, new_messages, decoder, tools=None, actuator="off"):
    """Return (literal text, same Session). Failures are journaled and re-raised.

    tools is metadata only; the caller executes DecodeResult.attempted_tool_calls
    and submits results in the next Message. No retries or output selection.
    """
    started, cpu, wall = time.time(), time.process_time(), time.monotonic()
    messages = tuple(new_messages)
    before = session.register.snapshot()
    record = dict(
        request_id=session.request_count,
        journal_cursor=session.journal_cursor,
        request_bindings=asdict(session.request_bindings),
        register_events=before["events"],
        event_generations=before["event_generations"],
        experimental_flag_state=None,
        raw_messages=[asdict(m) for m in messages],
        rendered_messages=None,
        raw_token_ids=None,
        rendered_token_ids=None,
        source_events=[asdict(e) for m in messages for e in m.entries],
        classifier_inputs=[],
        classifier_decisions=[],
        before_versions=before["versions"],
        after_versions=before["versions"],
        before_live_mask=before["live_mask"],
        after_live_mask=before["live_mask"],
        defaults=[asdict(d) for d in session.register.defaults],
        applicability=None,
        output=None,
        output_token_ids=None,
        eos=None,
        truncated=None,
        attempted_tool_calls=[],
        executed_tool_calls=[x for m in messages for x in m.executed_tool_calls],
        tool_results=[x for m in messages for x in m.tool_results],
        artifact_hashes=[x for m in messages for x in m.artifact_hashes],
        started_at=started,
        finished_at=None,
        cpu_seconds=None,
        wall_seconds=None,
        gpu_held_seconds=0.0,
        input_token_count=None,
        output_token_count=None,
        actuator=actuator,
        bias_hash=None,
        whole_body_intervals=None,
        keep_mask=None,
        absolute_positions=None,
        failures=[],
        fallback_reasons=[],
        oracle_checker_results=None,
    )
    session.request_count += 1
    hook = None
    session.experimental_flag_state = ExperimentalFlagState(actuator)
    try:
        if actuator not in {"off", "mask_only", "js_bias_mask"}:
            raise ValueError("unsupported actuator")
        entries = authenticate(messages)
        context = {
            "messages": session.messages + [asdict(m) for m in messages],
            "register": before,
        }
        for e in entries:
            record["classifier_inputs"].append({"entry": asdict(e), "context": context})
            decision = (
                session.classifier.validate(e, context)
                if session.classifier
                else Decision()
            )
            if not isinstance(decision, Decision):
                raise InvalidEntry("invalid classifier decision")
            record["classifier_decisions"].append(asdict(decision))
        # Complete explicit actions remain authoritative even on ABSTAIN/DISAGREE.
        session.register = session.register.apply(entries)
        after = session.register.snapshot()
        record.update(
            after_versions=after["versions"],
            after_live_mask=after["live_mask"],
            register_events=after["events"],
            event_generations=after["event_generations"],
        )
        content = session.request.text
        if messages:
            content = (
                compact(
                    [
                        dict(role=m.role, text=m.text, tool_results=m.tool_results)
                        for m in messages
                    ]
                )
                + "\n"
                + content
            )
        request = replace(
            session.request, text=content, history_ids=session.history_ids
        )
        if request.encode:
            record["raw_token_ids"] = [list(request.encode(m.text)) for m in messages]
        rendered = replace(
            render(session.register, request),
            history_messages=tuple(session.rendered_history),
        )
        record.update(
            rendered_messages=rendered.text,
            rendered_token_ids=rendered.prompt_ids,
            applicability=[asdict(v) for v in rendered.live],
            input_token_count=len(rendered.prompt_ids)
            if rendered.prompt_ids is not None
            else None,
        )
        if actuator != "off":
            candidate = session.actuator_hook
            if (
                candidate is None
                or request.needs_old_body
                or not candidate.eligible(request, actuator)
            ):
                record["fallback_reasons"].append(
                    "experimental actuator unavailable or uncertified request; "
                    "rendering only"
                )
            else:
                hook = candidate  # restore even if installation partially fails
                metadata = hook.install(session, rendered, actuator)
                allowed = {
                    "bias_hash",
                    "whole_body_intervals",
                    "keep_mask",
                    "absolute_positions",
                }
                if set(metadata) != allowed:
                    raise ValueError("incomplete actuator provenance")
                record.update(metadata)
                session.experimental_flag_state = ExperimentalFlagState(
                    actuator, actuator
                )
        # A generation request consumes the tombstone window even if decoding fails.
        session.register = replace(
            session.register, generation=session.register.generation + 1
        )
        session.messages.extend(asdict(m) for m in messages)
        session.rendered_history.append(dict(role="user", text=rendered.text))
        result = decoder(rendered)
        if isinstance(result, str):
            result = DecodeResult(result)
        if not isinstance(result, DecodeResult):
            raise TypeError("decoder must return str or DecodeResult")
        record.update(
            output=result.text,
            output_token_ids=result.output_ids,
            eos=result.eos,
            truncated=result.truncated,
            attempted_tool_calls=result.attempted_tool_calls,
            gpu_held_seconds=result.gpu_held_seconds,
            output_token_count=len(result.output_ids)
            if result.output_ids is not None
            else None,
        )
        session.messages.append(dict(role="assistant", text=result.text))
        session.rendered_history.append(dict(role="assistant", text=result.text))
        if request.encode and rendered.prefix_ids is not None:
            output_ids = (
                result.output_ids
                if result.output_ids is not None
                else tuple(request.encode(result.text))
            )
            im_end = tuple(request.encode("<|im_end|>"))
            closure = (
                (result.eos,) + tuple(request.encode("\n"))
                if result.eos is not None and im_end == (result.eos,)
                else ((result.eos,) if result.eos is not None else ())
                + tuple(request.encode("<|im_end|>\n"))
            )
            session.history_ids += rendered.prefix_ids + tuple(output_ids) + closure
        return result.text, session
    except BaseException as exc:
        record["failures"].append({"type": type(exc).__name__, "message": str(exc)})
        raise
    finally:
        try:
            if hook is not None:
                hook.restore()
        except BaseException as exc:
            record["failures"].append(
                {"type": type(exc).__name__, "message": str(exc), "stage": "restore"}
            )
            raise
        finally:
            record.update(
                experimental_flag_state=asdict(session.experimental_flag_state),
                finished_at=time.time(),
                cpu_seconds=time.process_time() - cpu,
                wall_seconds=time.monotonic() - wall,
            )
            session.journal.append(record)
            session.journal_cursor += 1
