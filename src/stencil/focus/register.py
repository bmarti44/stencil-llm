"""Explicit lifecycle register. No natural-language interpretation or model imports.

Owns immutable records and transactional validation. The historical FOCUS-3
gate runtime (stencil.focus3) is legacy-only and must never be imported here.
"""

from dataclasses import asdict, dataclass, replace
from enum import StrEnum
from typing import Protocol

REQUEST_KINDS = frozenset(
    {"final_answer", "code_answer", "tool_call", "tool_result", "prose"}
)
AUTHORITY = {"user": 1, "developer": 2, "system": 3}


class InvalidEntry(ValueError):
    pass


class Unsupported(ValueError):
    pass


class Verdict(StrEnum):
    ACCEPT = "ACCEPT"
    ABSTAIN = "ABSTAIN"
    DISAGREE = "DISAGREE"


@dataclass(frozen=True)
class Decision:
    verdict: Verdict = Verdict.ABSTAIN
    scores: tuple[float, ...] = ()
    reason: str = "explicit-only; classifier unavailable"


class Validator(Protocol):
    def validate(self, entry, context) -> Decision: ...


@dataclass(frozen=True)
class Scope:
    task_handle: str | None = None
    request_kinds: tuple[str, ...] = ()

    def __post_init__(self):
        object.__setattr__(
            self, "request_kinds", tuple(sorted(set(self.request_kinds)))
        )
        if not set(self.request_kinds) <= REQUEST_KINDS:
            raise Unsupported("unknown request kind")
        if self.task_handle is not None and (
            not isinstance(self.task_handle, str) or not self.task_handle
        ):
            raise Unsupported("invalid task handle")

    def contains(self, other):
        return (self.task_handle is None or self.task_handle == other.task_handle) and (
            not self.request_kinds
            or bool(other.request_kinds)
            and set(other.request_kinds) <= set(self.request_kinds)
        )

    def overlaps(self, other):
        return (
            self.task_handle is None
            or other.task_handle is None
            or self.task_handle == other.task_handle
        ) and (
            not self.request_kinds
            or not other.request_kinds
            or bool(set(self.request_kinds) & set(other.request_kinds))
        )


@dataclass(frozen=True)
class Source:
    role: str
    message_id: str
    span: tuple[int, int] | None = None

    def __post_init__(self):
        if self.span is not None:
            object.__setattr__(self, "span", tuple(self.span))
            if (
                len(self.span) != 2
                or any(type(x) is not int for x in self.span)
                or not 0 <= self.span[0] < self.span[1]
            ):
                raise InvalidEntry("invalid source span")


@dataclass(frozen=True)
class Entry:
    action: str
    key: str
    scope: Scope
    kind: str
    value: str
    event_id: str
    source: Source
    text: str | None = None
    target_version: int | None = None

    def __post_init__(self):
        if self.action not in {
            "add",
            "supersedes",
            "cancels",
            "completes",
            "reinstates",
        } or self.kind not in {"language", "style", "format", "process"}:
            raise InvalidEntry("unsupported action/kind")
        if not isinstance(self.scope, Scope) or not isinstance(self.source, Source):
            raise InvalidEntry("typed scope/source required")
        if any(
            not isinstance(x, str) or not x
            for x in (self.key, self.event_id, self.value, self.source.message_id)
        ):
            raise InvalidEntry("nonempty identifiers/value required")
        if self.text is not None and not isinstance(self.text, str):
            raise InvalidEntry("text must be a string")
        if self.target_version is not None and (
            type(self.target_version) is not int or self.target_version < 1
        ):
            raise InvalidEntry("invalid target_version")


@dataclass(frozen=True)
class Version:
    entry: Entry
    version: int
    previous: int | None = None


@dataclass(frozen=True)
class Retirement:
    key: str
    version: int
    event_id: str
    reason: str
    generation: int


@dataclass(frozen=True)
class VersionHistory:
    version: Version
    transitions: tuple[Entry, ...]
    retirement: Retirement | None


@dataclass(frozen=True)
class Register:
    defaults: tuple[Entry, ...] = ()
    task_handles: frozenset[str] = frozenset()
    events: tuple[Entry, ...] = ()
    versions: tuple[Version, ...] = ()
    retirements: tuple[Retirement, ...] = ()
    generation: int = 0
    event_generations: tuple[int, ...] = ()

    def __post_init__(self):
        for name in (
            "defaults",
            "events",
            "versions",
            "retirements",
            "event_generations",
        ):
            object.__setattr__(self, name, tuple(getattr(self, name)))
        object.__setattr__(self, "task_handles", frozenset(self.task_handles))
        for d in self.defaults:
            self.check_scope(d.scope)
            if d.source.role not in AUTHORITY or d.action != "add":
                raise InvalidEntry("invalid configured default")
        for i, d in enumerate(self.defaults):
            for other in self.defaults[:i]:
                if (
                    d.key == other.key
                    and d.scope.overlaps(other.scope)
                    and (
                        d.scope == other.scope
                        or not (
                            d.scope.contains(other.scope)
                            or other.scope.contains(d.scope)
                        )
                    )
                ):
                    raise InvalidEntry("ambiguous defaults")

    @classmethod
    def replay(
        cls,
        events,
        *,
        defaults=(),
        task_handles=(),
        event_generations=None,
        generation=None,
    ):
        """Rebuild from source entries and their append clocks, never cached views.

        Clocks are optional for lifecycle-only replay; retain them to reproduce
        the renderer's three-generation retirement window as well.
        """
        events = tuple(events)
        clocks = (
            (0,) * len(events)
            if event_generations is None
            else tuple(event_generations)
        )
        if (
            len(clocks) != len(events)
            or any(type(t) is not int or t < 0 for t in clocks)
            or tuple(sorted(clocks)) != clocks
        ):
            raise InvalidEntry("invalid event generations")
        end = clocks[-1] if clocks else 0
        generation = end if generation is None else generation
        if type(generation) is not int or generation < end:
            raise InvalidEntry("invalid replay generation")
        state = cls(defaults=defaults, task_handles=task_handles)
        for event, clock in zip(events, clocks, strict=True):
            state = replace(state, generation=clock).apply((event,))
        return replace(state, generation=generation)

    def history(self, key=None):
        """Every created version plus original and incoming transition evidence."""
        return tuple(
            VersionHistory(
                v,
                (v.entry,)
                + tuple(
                    e
                    for e in self.events
                    if e.key == v.entry.key and e.target_version == v.version
                ),
                next(
                    (
                        r
                        for r in self.retirements
                        if r.key == v.entry.key and r.version == v.version
                    ),
                    None,
                ),
            )
            for v in self.versions
            if key is None or v.entry.key == key
        )

    @property
    def live_mask(self):
        retired = {(r.key, r.version) for r in self.retirements}
        return tuple((v.entry.key, v.version) not in retired for v in self.versions)

    def check_scope(self, scope):
        if scope.task_handle is not None and scope.task_handle not in self.task_handles:
            raise Unsupported("undeclared task handle")

    def apply(self, entries):
        """Returns a new register only after the entire transaction succeeds.

        The caller MUST authenticate entries first (loop.authenticate). Direct
        use is a trusted structured API, never a parser of transcript content.
        """
        state = self
        for entry in entries:
            state = state._apply(entry)
        return state

    def _apply(self, e):
        self.check_scope(e.scope)
        if e.source.role not in AUTHORITY:
            raise InvalidEntry("source has no rule authority")
        prior = [x for x in self.events if x.event_id == e.event_id]
        if prior:
            if prior[0] != e:
                raise InvalidEntry("event ID collision")
            return self
        same = [v for v in self.versions if v.entry.key == e.key]
        if any(v.entry.kind != e.kind for v in same):
            raise InvalidEntry("key kind is immutable")
        target = None
        if e.action != "add":
            matches = [v for v in same if v.version == e.target_version]
            if len(matches) != 1:
                raise InvalidEntry("missing/ambiguous/wrong target_version")
            target = matches[0]
            live = self.live_mask[self.versions.index(target)]
            if (
                e.scope != target.entry.scope
                or AUTHORITY[e.source.role] < AUTHORITY[target.entry.source.role]
            ):
                raise InvalidEntry("target scope/authority mismatch")
            if e.action == "reinstates":
                if live or any(
                    v.previous == target.version
                    for v in same
                    if v.entry.action == "reinstates"
                ):
                    raise InvalidEntry("stale reinstatement target")
                if e.value != target.entry.value or e.text != target.entry.text:
                    raise InvalidEntry(
                        "reinstatement must preserve original value/text"
                    )
            elif not live:
                raise InvalidEntry("stale target_version")
            if e.action in {"cancels", "completes"} and e.value != target.entry.value:
                raise InvalidEntry("retirement value differs from target")
        elif e.target_version is not None or any(
            v.entry.scope == e.scope for v in same
        ):
            raise InvalidEntry("add requires a new key/scope; use an exact target")
        retiring = (
            target if e.action in {"supersedes", "cancels", "completes"} else None
        )
        creates = e.action in {"add", "supersedes", "reinstates"}
        if creates:
            for v, live in zip(self.versions, self.live_mask, strict=True):
                if not live or v == retiring or v.entry.key != e.key:
                    continue
                s = v.entry.scope
                if s == e.scope:
                    raise InvalidEntry(
                        "same-scope addition requires exact supersedes target"
                    )
                if s.overlaps(e.scope) and not (
                    s.contains(e.scope) or e.scope.contains(s)
                ):
                    raise Unsupported("unsupported scope intersection")
        versions = self.versions
        if creates:
            versions += (
                Version(
                    e, max((v.version for v in same), default=0) + 1, e.target_version
                ),
            )
        retirements = self.retirements
        if retiring:
            retirements += (
                Retirement(
                    e.key, retiring.version, e.event_id, e.action, self.generation
                ),
            )
        return replace(
            self,
            events=self.events + (e,),
            versions=versions,
            retirements=retirements,
            event_generations=self.event_generations + (self.generation,),
        )

    def live(self, task_handle, request_kind):
        scope = Scope(task_handle, (request_kind,))
        self.check_scope(scope)
        candidates = [
            v
            for v, live in zip(self.versions, self.live_mask, strict=True)
            if live and v.entry.scope.contains(scope)
        ]
        # Configuration defaults are fallbacks, not immutable system mandates.
        explicit_keys = {v.entry.key for v in candidates}
        for d in self.defaults:
            if d.scope.contains(scope) and d.key not in explicit_keys:
                candidates.append(Version(d, 0))
        selected = {}
        for v in candidates:
            old = selected.get(v.entry.key)
            if (
                old is None
                or AUTHORITY[v.entry.source.role] > AUTHORITY[old.entry.source.role]
                or (
                    AUTHORITY[v.entry.source.role] == AUTHORITY[old.entry.source.role]
                    and old.entry.scope.contains(v.entry.scope)
                )
            ):
                selected[v.entry.key] = v
        return tuple(
            sorted(
                selected.values(),
                key=lambda v: (
                    2
                    if v.entry.scope.request_kinds
                    else 1
                    if v.entry.scope.task_handle
                    else 0,
                    v.entry.key,
                    v.version,
                ),
            )
        )

    def snapshot(self):
        return dict(
            events=[asdict(e) for e in self.events],
            event_generations=list(self.event_generations),
            retirements=[asdict(r) for r in self.retirements],
            versions=[asdict(v) for v in self.versions],
            live_mask=list(self.live_mask),
            generation=self.generation,
        )
