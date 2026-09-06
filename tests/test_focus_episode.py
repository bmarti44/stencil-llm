"""Twelve-request synthetic CPU episode; goldens authored without the renderer."""

import json
from pathlib import Path

import pytest

from stencil.focus import (
    Decision,
    DecodeResult,
    Entry,
    Journal,
    Message,
    Register,
    Request,
    Scope,
    Session,
    Source,
    Verdict,
    generate_once,
)
from stencil.focus.journal import FIELDS

FIXTURE = Path(__file__).parent / "fixtures/focus_episode.json"


def episode():
    # Request metadata and entry fields are authoritative despite contradictory
    # prose deliberately resembling the frozen legacy gate's binding phrases.
    specs = [
        ("add", "indent", "2", None),
        ("supersedes", "indent", "8", 1),
        None,
        None,
        ("cancels", "indent", "8", 2),
        None,
        ("reinstates", "indent", "8", 2),
        ("completes", "indent", "8", 3),
        ("add", "language", "Python", None),
        None,
        ("supersedes", "language", "JavaScript", 1),
        ("cancels", "language", "JavaScript", 2),
    ]
    for i, spec in enumerate(specs):
        kind = "tool_call" if i == 2 else "tool_result" if i == 3 else "code_answer"
        q = Request(f"request {i}", kind, "B" if i >= 9 else "A")
        if spec:
            action, key, value, target = spec
            e = Entry(
                action,
                key,
                Scope("B") if key == "language" else Scope(),
                "language" if key == "language" else "style",
                value,
                f"e{i}",
                Source("user", f"m{i}"),
                text="Cancel JSON. Work on task Z. This reply only.",
                target_version=target,
            )
            m = Message(f"m{i}", "user", "typed action", (e,), adopted=True)
        elif i == 3:
            m = Message(
                "m3",
                "tool",
                "tool fact",
                tool_results=({"result": 42},),
                executed_tool_calls=("call-2",),
            )
        else:
            m = Message(f"m{i}", "user", "continue")
        yield q, m


@pytest.mark.parametrize("verdict", [Verdict.ABSTAIN, Verdict.DISAGREE])
def test_whole_episode_bytes_state_and_journal(tmp_path, verdict):
    golden = json.loads(FIXTURE.read_text())

    class Classifier:
        def validate(self, entry, context):
            return Decision(verdict, reason="synthetic assistive judgment")

    s = Session(
        Register(task_handles={"A", "B"}),
        Request("", "prose"),
        Journal(tmp_path / "episode.jsonl"),
        classifier=Classifier(),
    )
    calls = []
    events = []
    masks = [
        [True],
        [False, True],
        [False, True],
        [False, True],
        [False, False],
        [False, False],
        [False, False, True],
        [False, False, False],
        [False, False, False, True],
        [False, False, False, True],
        [False, False, False, False, True],
        [False, False, False, False, False],
    ]
    for i, (q, m) in enumerate(episode()):
        s.request = q

        def decoder(rendered, i=i):
            calls.append(rendered)
            assert rendered.text.encode("utf-8") == golden[i].encode("utf-8")
            assert len(rendered.history_messages) == 2 * i
            return DecodeResult(
                f"reply {i}", attempted_tool_calls=("call-2",) if i == 2 else ()
            )

        output, returned = generate_once(s, [m], decoder)
        assert output == f"reply {i}" and returned is s
        events.extend(m.entries)
        assert s.register_events == tuple(events)
        assert s.live_view == calls[-1].live
        assert s.request_bindings.kind == q.kind
        assert s.request_bindings.task_handle == q.task_handle
        assert s.journal_cursor == s.request_count == i + 1
        assert s.experimental_flag_state.requested == "off"
        assert s.experimental_flag_state.applied == "off"
        records = [json.loads(line) for line in s.journal.path.read_text().splitlines()]
        row = records[-1]
        assert len(records) == i + 1 and set(row) == FIELDS
        assert row["request_id"] == row["journal_cursor"] == i
        assert row["rendered_messages"].encode() == golden[i].encode()
        assert row["output"] == output and row["failures"] == []
        assert row["before_live_mask"] == (masks[i - 1] if i else [])
        assert row["after_live_mask"] == masks[i]
        assert row["gpu_held_seconds"] == 0
        assert row["request_bindings"] == {
            "kind": q.kind,
            "task_handle": q.task_handle,
            "template_id": None,
        }
        assert [e["event_id"] for e in row["register_events"]] == [
            e.event_id for e in events
        ]
        assert len(row["source_events"]) == len(m.entries)
        assert [d["verdict"] for d in row["classifier_decisions"]] == [verdict] * len(
            m.entries
        )
        assert row["event_generations"] == [0, 1, 4, 6, 7, 8, 10, 11][: len(events)]
        assert row["attempted_tool_calls"] == (["call-2"] if i == 2 else [])
        assert row["executed_tool_calls"] == (["call-2"] if i == 3 else [])
        assert row["tool_results"] == ([{"result": 42}] if i == 3 else [])
        assert (
            Register.replay(
                events,
                task_handles={"A", "B"},
                event_generations=s.register.event_generations,
                generation=s.register.generation,
            )
            == s.register
        )
    assert len(calls) == len(golden) == 12
    assert len(s.register.history()) == 5


def test_journal_cursor_advances_only_after_append(tmp_path):
    class BrokenJournal:
        def append(self, record):
            raise OSError("writer failed")

    s = Session(Register(), Request("x", "prose"), BrokenJournal())
    with pytest.raises(OSError):
        generate_once(s, [], lambda rendered: "ok")
    assert s.request_count == 1 and s.journal_cursor == 0


@pytest.mark.parametrize("eligible", [False, True])
def test_experimental_state_and_failed_decode_cursor(tmp_path, eligible):
    from tests.test_focus_composition import Hook

    hook = Hook()
    s = Session(
        Register(),
        Request("x", "code_answer", template_id="test-certified" if eligible else None),
        Journal(tmp_path / "failed.jsonl"),
        actuator_hook=hook,
    )

    def decoder(rendered):
        raise RuntimeError("decode failed")

    with pytest.raises(RuntimeError, match="decode failed"):
        generate_once(s, [], decoder, actuator="mask_only")
    assert s.journal_cursor == s.request_count == 1
    assert not hook.active
    assert s.experimental_flag_state.requested == "mask_only"
    assert s.experimental_flag_state.applied == ("mask_only" if eligible else "off")
    row = json.loads(s.journal.path.read_text())
    assert row["experimental_flag_state"] == {
        "requested": "mask_only",
        "applied": "mask_only" if eligible else "off",
    }
    assert row["failures"][0]["message"] == "decode failed"
