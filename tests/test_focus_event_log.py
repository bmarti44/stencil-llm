"""CPU lifecycle properties over independently authored typed event sequences."""

import random
from dataclasses import FrozenInstanceError, replace

import pytest

from stencil.focus import Register, Scope
from stencil.focus.register import InvalidEntry
from tests.test_focus_composition import entry


@pytest.mark.parametrize("seed", range(12))
def test_replay_append_only_and_idempotent(seed):
    rng = random.Random(seed)
    r = Register(task_handles={"A", "B"})
    old_states = []
    for i in range(40):
        key = str(rng.randrange(4))
        versions = [v for v in r.versions if v.entry.key == key]
        live = [
            v
            for v, mask in zip(r.versions, r.live_mask, strict=True)
            if mask and v.entry.key == key
        ]
        if not versions:
            e = entry(key=key, scope=Scope("A"), eid=str(i))
        elif live:
            target = live[0]
            e = replace(
                target.entry,
                action=rng.choice(("supersedes", "cancels", "completes")),
                event_id=str(i),
                target_version=target.version,
            )
        else:
            target = versions[-1]
            e = replace(
                target.entry,
                action="reinstates",
                event_id=str(i),
                target_version=target.version,
            )
        before = r
        old_states.append((r, r.snapshot()))
        r = replace(r, generation=r.generation + rng.randrange(3)).apply([e])
        assert r.events == before.events + (e,)
        assert r.versions[: len(before.versions)] == before.versions
        assert r.apply([e]) is r
        with pytest.raises(InvalidEntry, match="collision"):
            r.apply([replace(e, value="collision")])
        replayed = Register.replay(
            r.events,
            event_generations=r.event_generations,
            generation=r.generation,
            task_handles=r.task_handles,
        )
        assert replayed == r
        for task in (None, "A", "B"):
            assert replayed.live(task, "code_answer") == r.live(task, "code_answer")
        for previous, snapshot in old_states:
            assert previous.snapshot() == snapshot
    history = r.history()
    assert tuple(h.version for h in history) == r.versions
    for h in history:
        assert h.transitions[0] == h.version.entry
        assert all(e in r.events for e in h.transitions)
        for e in r.events:
            if e.key == h.version.entry.key and e.target_version == h.version.version:
                assert e in h.transitions
    with pytest.raises(FrozenInstanceError):
        history[0].version.version = 100


def test_replay_preserves_defaults_and_retirement_clock():
    default = entry(eid="default", value="4")
    r = Register(defaults=(default,)).apply([entry()])
    r = replace(r, generation=7).apply([entry("cancels", target=1, eid="cancel")])
    rebuilt = Register.replay(
        r.events,
        defaults=r.defaults,
        event_generations=r.event_generations,
        generation=9,
    )
    assert rebuilt.retirements == r.retirements
    assert rebuilt.live(None, "prose")[0].entry == default
    assert rebuilt.history("indent")[0].retirement.event_id == "cancel"
    with pytest.raises(InvalidEntry):
        Register.replay(r.events, event_generations=(7, 2))
    with pytest.raises(InvalidEntry):
        Register.replay(r.events, event_generations=(0,))
