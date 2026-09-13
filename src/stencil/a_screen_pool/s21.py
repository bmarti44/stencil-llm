# ruff: noqa: E501
"""S21: conference talks — validation (target, stable) x return_shape (support)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""talkslate package."""\n'

_MODEL = '''"""Talk and room records."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Talk:
    talk_id: str
    title: str
    speaker: str
    minutes: int
    room_id: str | None = None
    hour: int | None = None


@dataclass(frozen=True)
class Room:
    room_id: str
    name: str
    capacity: int
'''

_GRID = '''"""One-line programme entries."""

from talkslate.model import Talk


def programme_line(talk: Talk) -> str:
    where = ""
    if talk.room_id is not None and talk.hour is not None:
        where = f" @ {talk.room_id} {talk.hour:02d}:00"
    return f"{talk.title} - {talk.speaker} ({talk.minutes} min){where}"
'''

_SLATE_HEAD = '''"""Talk table (storage layer) and the public slate operations."""

from talkslate.model import Room, Talk


class TalkTable:
    def __init__(self) -> None:
        self._talks: dict[str, Talk] = {}
        self._rooms: dict[str, Room] = {}

    def insert_talk(self, talk: Talk) -> None:
        if talk.minutes <= 0:
            raise ValueError("minutes must be positive")
        self._talks[talk.talk_id] = talk

    def get_talk(self, talk_id: str) -> Talk:
        return self._talks[talk_id]

    def rooms(self) -> list[Room]:
        return list(self._rooms.values())

    def next_id(self, prefix: str) -> str:
        return f"{prefix}{len(self._talks) + len(self._rooms) + 1}"
'''

_SUBMIT_TALK = """

def submit_talk(table: TalkTable, title: str, speaker: str, minutes: int) -> Talk:
    talk = Talk(table.next_id("T"), title, speaker, minutes)
    table.insert_talk(talk)
    return talk
"""

_SLATE = _SLATE_HEAD + _SUBMIT_TALK

_FILES = {
    "talkslate/__init__.py": _INIT,
    "talkslate/model.py": _MODEL,
    "talkslate/grid.py": _GRID,
    "talkslate/slate.py": _SLATE,
}


def _room_methods(state: str) -> str:
    check = (
        '        if room.capacity <= 0:\n            raise ValueError("capacity must be positive")\n'
        if state == "storage"
        else ""
    )
    return (
        "\n    def insert_room(self, room: Room) -> None:\n"
        + check
        + "        self._rooms[room.room_id] = room\n"
        "\n    def get_room(self, room_id: str) -> Room:\n"
        "        return self._rooms[room_id]\n"
    )


def _add_room(state: str) -> str:
    check = (
        '    if capacity <= 0:\n        raise ValueError("capacity must be positive")\n'
        if state == "api"
        else ""
    )
    return (
        "\n\ndef add_room(table: TalkTable, name: str, capacity: int) -> Room:\n"
        + check
        + '    room = Room(table.next_id("R"), name, capacity)\n'
        "    table.insert_room(room)\n"
        "    return room\n"
    )


def _assign_slot(state: str) -> str:
    check = (
        '        if not 0 <= hour <= 23:\n            raise ValueError("hour must be between 0 and 23")\n'
        if state == "storage"
        else ""
    )
    return (
        "\n    def assign_slot(self, talk_id: str, room_id: str, hour: int) -> Talk:\n"
        + check
        + "        talk = replace(self._talks[talk_id], room_id=room_id, hour=hour)\n"
        "        self._talks[talk_id] = talk\n"
        "        return talk\n"
    )


def _schedule_talk(state: str) -> str:
    check = (
        '    if not 0 <= hour <= 23:\n        raise ValueError("hour must be between 0 and 23")\n'
        if state == "api"
        else ""
    )
    return (
        "\n\ndef schedule_talk(table: TalkTable, talk_id: str, room_id: str, hour: int) -> Talk:\n"
        "    table.get_room(room_id)\n"
        + check
        + "    return table.assign_slot(talk_id, room_id, hour)\n"
    )


def _gold1(state: str) -> str:
    return _SLATE_HEAD + _room_methods(state) + _SUBMIT_TALK + _add_room(state)


def _gold2(state: str) -> str:
    # Built on the checkpoint-1 gold under the state then in force (storage).
    head = _SLATE_HEAD.replace(
        "from talkslate.model import Room, Talk\n",
        "from dataclasses import replace\n\nfrom talkslate.model import Room, Talk\n",
        1,
    )
    return (
        head
        + _room_methods("storage")
        + _assign_slot(state)
        + _SUBMIT_TALK
        + _add_room("storage")
        + _schedule_talk(state)
    )


# ----------------------------------------------------------------- checkpoint 1: add_room

_C1_FUNCTIONAL = {
    "test_room_functional.py": """import pytest

from talkslate.model import Room
from talkslate.slate import TalkTable, add_room, submit_talk


def test_add_room_stores_and_returns_room():
    t = TalkTable()
    r = add_room(t, "Main hall", 120)
    assert r.name == "Main hall" and r.capacity == 120
    assert r.room_id.startswith("R")
    assert t.rooms() == [r] and t.get_room(r.room_id) is r


def test_two_rooms_get_distinct_ids():
    t = TalkTable()
    a = add_room(t, "Main hall", 120)
    b = add_room(t, "Seminar 2", 30)
    assert a.room_id != b.room_id and len(t.rooms()) == 2


def test_get_room_unknown_raises_keyerror():
    t = TalkTable()
    with pytest.raises(KeyError):
        t.get_room("R99")


def test_nonpositive_capacity_raises_and_stores_nothing():
    t = TalkTable()
    for bad in (0, -10):
        with pytest.raises(ValueError):
            add_room(t, "Cupboard", bad)
    assert t.rooms() == []


def test_table_has_insert_room():
    t = TalkTable()
    t.insert_room(Room("R7", "Loft", 12))
    assert t.get_room("R7").name == "Loft"


def test_add_room_keeps_existing_rooms_and_talks():
    t = TalkTable()
    talk = submit_talk(t, "Sorting in practice", "Mina", 30)
    first = add_room(t, "Seminar 2", 30)
    second = add_room(t, "Main hall", 120)
    assert t.get_room(first.room_id) is first
    assert t.get_room(second.room_id) is second
    assert first.room_id != second.room_id
    assert len(t.rooms()) == 2 and t.next_id("X") == "X4"
    assert t.get_talk(talk.talk_id) is talk
    assert talk.room_id is None and talk.hour is None
"""
}

_C1_REGRESSION = {
    "test_room_regression.py": """import pytest

from talkslate.grid import programme_line
from talkslate.slate import TalkTable, submit_talk


def test_submit_talk_and_lookups_unchanged():
    t = TalkTable()
    talk = submit_talk(t, "Sorting in practice", "Mina", 30)
    assert talk.talk_id == "T1" and t.get_talk("T1") is talk
    with pytest.raises(ValueError):
        submit_talk(t, "Empty", "Nobody", 0)
    with pytest.raises(KeyError):
        t.get_talk("T9")
    assert programme_line(talk) == "Sorting in practice - Mina (30 min)"


def test_two_talks_coexist_with_defaults():
    t = TalkTable()
    a = submit_talk(t, "Sorting in practice", "Mina", 30)
    b = submit_talk(t, "Parsers by hand", "Ola", 45)
    assert t.get_talk(a.talk_id) is a and t.get_talk(b.talk_id) is b
    assert a.talk_id != b.talk_id and t.next_id("X") == "X3"
    assert a.room_id is None and a.hour is None
    assert b.minutes == 45 and programme_line(b).endswith("(45 min)")
"""
}

_C1_CONTRACT = {
    "api": {
        "test_room_validation.py": """import pytest

from talkslate.model import Room
from talkslate.slate import TalkTable, add_room


def test_public_function_rejects_nonpositive_capacity():
    t = TalkTable()
    for bad in (0, -4):
        with pytest.raises(ValueError):
            add_room(t, "Cupboard", bad)
    assert t.rooms() == []


def test_table_trusts_callers_on_capacity():
    t = TalkTable()
    t.insert_room(Room("R9", "Cupboard", 0))
    assert [r.room_id for r in t.rooms()] == ["R9"]
"""
    },
    "storage": {
        "test_room_validation.py": """import pytest

from talkslate.model import Room
from talkslate.slate import TalkTable, add_room


def test_table_rejects_nonpositive_capacity():
    t = TalkTable()
    for bad in (0, -4):
        with pytest.raises(ValueError):
            t.insert_room(Room("R9", "Cupboard", bad))
    assert t.rooms() == []


def test_public_function_passes_invalid_capacity_through(monkeypatch):
    t = TalkTable()
    seen = []
    real = t.insert_room

    def spy(room):
        seen.append(room.capacity)
        return real(room)

    monkeypatch.setattr(t, "insert_room", spy)
    with pytest.raises(ValueError):
        add_room(t, "Cupboard", -4)
    assert seen == [-4]
"""
    },
}

_C1_SUPPORT = {
    "test_room_shape.py": """from talkslate.model import Room
from talkslate.slate import TalkTable, add_room


def test_add_room_returns_dataclass_not_dict():
    out = add_room(TalkTable(), "Main hall", 120)
    assert isinstance(out, Room)
    assert not isinstance(out, dict)
"""
}

_REQ1 = Request(
    text=(
        "Add rooms. Give TalkTable an `insert_room(room)` method that stores a Room under "
        "its room_id and a `get_room(room_id)` lookup (an unknown id raises KeyError), and "
        "add a public function `add_room(table, name, capacity)` that mints an id with "
        'prefix "R", stores the room and returns it. A capacity of zero or less is invalid '
        "and must raise ValueError."
    ),
    target="talkslate/slate.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"api": _gold1("api"), "storage": _gold1("storage")},
)

# ----------------------------------------------------------------- checkpoint 2: schedule_talk

_C2_FUNCTIONAL = {
    "test_schedule_functional.py": """import pytest

from talkslate.slate import TalkTable, add_room, schedule_talk, submit_talk


def _crowded():
    t = TalkTable()
    talk = submit_talk(t, "Sorting in practice", "Mina", 30)
    other = submit_talk(t, "Parsers by hand", "Ola", 45)
    room = add_room(t, "Main hall", 120)
    spare = add_room(t, "Seminar 2", 30)
    schedule_talk(t, other.talk_id, spare.room_id, 9)
    return t, talk, other, room, spare


def _setup():
    t, talk, _other, room, _spare = _crowded()
    return t, talk, room


def test_schedule_talk_sets_room_and_hour():
    t, talk, room = _setup()
    out = schedule_talk(t, talk.talk_id, room.room_id, 14)
    assert out.room_id == room.room_id and out.hour == 14
    assert out.title == talk.title and out.minutes == 30
    assert t.get_talk(talk.talk_id).hour == 14


def test_schedule_unknown_talk_or_room_raises_keyerror():
    t, talk, room = _setup()
    with pytest.raises(KeyError):
        schedule_talk(t, "T99", room.room_id, 9)
    with pytest.raises(KeyError):
        schedule_talk(t, talk.talk_id, "R99", 9)


def test_schedule_hour_out_of_range_raises_and_changes_nothing():
    t, talk, room = _setup()
    for bad in (-1, 24):
        with pytest.raises(ValueError):
            schedule_talk(t, talk.talk_id, room.room_id, bad)
    assert t.get_talk(talk.talk_id).hour is None


def test_table_has_assign_slot():
    t, talk, room = _setup()
    out = t.assign_slot(talk.talk_id, room.room_id, 9)
    assert out.hour == 9 and t.get_talk(talk.talk_id).room_id == room.room_id


def test_schedule_keeps_other_talks_rooms_and_count():
    t, talk, other, room, spare = _crowded()
    before = t.get_talk(other.talk_id)
    assert before.room_id == spare.room_id and before.hour == 9
    out = schedule_talk(t, talk.talk_id, room.room_id, 14)
    assert out.room_id == room.room_id and out.hour == 14
    kept = t.get_talk(other.talk_id)
    assert kept.room_id == spare.room_id and kept.hour == 9
    assert kept.title == other.title and kept.minutes == other.minutes
    assert t.get_talk(talk.talk_id).hour == 14
    assert len(t.rooms()) == 2 and t.next_id("X") == "X5"
"""
}

_C2_REGRESSION = {
    "test_schedule_regression.py": """import pytest

from talkslate.grid import programme_line
from talkslate.slate import TalkTable, add_room, submit_talk


def test_talks_and_rooms_unchanged():
    t = TalkTable()
    talk = submit_talk(t, "Sorting in practice", "Mina", 30)
    room = add_room(t, "Main hall", 120)
    assert t.get_talk(talk.talk_id) is talk and t.get_room(room.room_id) is room
    with pytest.raises(ValueError):
        submit_talk(t, "Empty", "Nobody", 0)
    with pytest.raises(ValueError):
        add_room(t, "Cupboard", 0)
    assert programme_line(talk) == "Sorting in practice - Mina (30 min)"


def test_two_talks_and_two_rooms_coexist():
    t = TalkTable()
    a = submit_talk(t, "Sorting in practice", "Mina", 30)
    b = submit_talk(t, "Parsers by hand", "Ola", 45)
    first = add_room(t, "Main hall", 120)
    second = add_room(t, "Seminar 2", 30)
    assert t.get_talk(a.talk_id) is a and t.get_talk(b.talk_id) is b
    assert t.get_room(first.room_id) is first
    assert t.get_room(second.room_id) is second
    assert len(t.rooms()) == 2 and t.next_id("X") == "X5"
    assert a.room_id is None and a.hour is None
    assert programme_line(b) == "Parsers by hand - Ola (45 min)"
"""
}

_C2_CONTRACT = {
    "api": {
        "test_schedule_validation.py": """import pytest

from talkslate.slate import TalkTable, add_room, schedule_talk, submit_talk


def _setup():
    t = TalkTable()
    talk = submit_talk(t, "Sorting in practice", "Mina", 30)
    room = add_room(t, "Main hall", 120)
    return t, talk, room


def test_public_function_rejects_hour_out_of_range():
    t, talk, room = _setup()
    for bad in (-1, 24):
        with pytest.raises(ValueError):
            schedule_talk(t, talk.talk_id, room.room_id, bad)
    assert t.get_talk(talk.talk_id).hour is None


def test_table_trusts_callers_on_hour():
    t, talk, room = _setup()
    out = t.assign_slot(talk.talk_id, room.room_id, 24)
    assert out.hour == 24 and t.get_talk(talk.talk_id).hour == 24
"""
    },
    "storage": {
        "test_schedule_validation.py": """import pytest

from talkslate.slate import TalkTable, add_room, schedule_talk, submit_talk


def _setup():
    t = TalkTable()
    talk = submit_talk(t, "Sorting in practice", "Mina", 30)
    room = add_room(t, "Main hall", 120)
    return t, talk, room


def test_table_rejects_hour_out_of_range():
    t, talk, room = _setup()
    for bad in (-1, 24):
        with pytest.raises(ValueError):
            t.assign_slot(talk.talk_id, room.room_id, bad)
    assert t.get_talk(talk.talk_id).hour is None


def test_public_function_passes_invalid_hour_through(monkeypatch):
    t, talk, room = _setup()
    seen = []
    real = t.assign_slot

    def spy(talk_id, room_id, hour):
        seen.append(hour)
        return real(talk_id, room_id, hour)

    monkeypatch.setattr(t, "assign_slot", spy)
    with pytest.raises(ValueError):
        schedule_talk(t, talk.talk_id, room.room_id, 24)
    assert seen == [24]
"""
    },
}

_C2_SUPPORT = {
    "test_schedule_shape.py": """from talkslate.model import Talk
from talkslate.slate import TalkTable, add_room, schedule_talk, submit_talk


def test_schedule_talk_returns_dataclass_not_dict():
    t = TalkTable()
    talk = submit_talk(t, "Sorting in practice", "Mina", 30)
    room = add_room(t, "Main hall", 120)
    out = schedule_talk(t, talk.talk_id, room.room_id, 10)
    assert isinstance(out, Talk)
    assert not isinstance(out, dict)
"""
}

_REQ2 = Request(
    text=(
        "Add scheduling. Give TalkTable an `assign_slot(talk_id, room_id, hour)` method "
        "that replaces the stored talk with a copy carrying that room and hour and returns "
        "it (an unknown talk raises KeyError), and add a public function `schedule_talk("
        "table, talk_id, room_id, hour)` that checks the room exists via get_room (an "
        "unknown room raises KeyError), applies the slot and returns the updated Talk. An "
        "hour outside 0 to 23 inclusive is invalid and must raise ValueError."
    ),
    target="talkslate/slate.py",
    functional_tests=_C2_FUNCTIONAL,
    regression_tests=_C2_REGRESSION,
    contract_tests=_C2_CONTRACT,
    support_tests=_C2_SUPPORT,
    gold={"api": _gold2("api"), "storage": _gold2("storage")},
)

# ----------------------------------------------------------------- prefix (16 turns)

_PREFIX = [
    Turn(
        "user",
        "I run the programme for a one-day community tech conference, about 120 people, "
        "two rooms, twenty-odd talks. Every year the schedule lives in a Google Sheet that "
        "three volunteers edit at once, and every year somebody double-books the main hall "
        "at 14:00. I want to replace the sheet with a small Python package, `talkslate`, "
        "that holds talks and rooms in memory and prints the programme grid for the "
        "website and the printed handout. It gets driven by a script the night before:\n\n"
        "```\ncd ~/conf2026 && python -m talkslate.print_grid --rooms 2 > handout/"
        "programme.txt\n```\n\nThe CFP closes six weeks out, so the data is small and "
        "changes slowly. Nothing needs to be persistent beyond a JSON dump I can commit to "
        "the repo. Before I write anything: what should the README promise, and what should "
        "it explicitly refuse to do? I want to head off the annual request for a mobile app "
        "with push notifications for room changes. The two rooms are the main hall and a "
        "seminar room across the corridor, and the volunteers are the same three people "
        "every year, so whatever we build has to survive being used once a year by "
        "people who have forgotten it.",
    ),
    Turn(
        "assistant",
        "Promise little and refuse loudly; the refusals are what volunteers read:\n\n```\n"
        "## Scope\ntalkslate holds the accepted talks and the rooms for one conference day "
        "in memory, and renders the programme as plain text. It is a library for scripts, "
        "not a service.\n\n## Non-goals\n- CFP submission or review\n- attendee "
        "registration or tickets\n- a web or mobile front end\n- notifications of room "
        "changes\n```\n\nPlus a five-line usage block so people can see the API without "
        "opening the code:\n\n```python\nfrom talkslate.slate import TalkTable, submit_talk"
        '\n\ntable = TalkTable()\ntalk = submit_talk(table, "Sorting in practice", "Mina", '
        "30)\nprint(talk)\n```\n\nPut the usage block above the scope section rather than "
        "below it; people copy the code first and read the prose only when the code "
        "surprises them. The mobile-app request is best answered by exporting the "
        "grid as JSON; anyone who wants an app can build it on that and you never have to "
        "own it.",
    ),
    Turn(
        "user",
        "Ids: talks are T1, T2, ... and rooms will be R1, R2, ... I'd like the two never "
        "to collide numerically because the volunteers refer to things by number over the "
        "radio on the day ('move seven to the small room'). Also here's the JSON dump shape "
        'I\'m planning to commit after each edit session:\n\n```json\n{\n  "day": '
        '"2026-10-03",\n  "rooms": [{"room_id": "R2", "name": "Main hall", "capacity": '
        '120}],\n  "talks": [\n    {"talk_id": "T1", "title": "Sorting in practice", '
        '"speaker": "Mina", "minutes": 30, "room_id": "R2", "hour": 14},\n    {"talk_id": '
        '"T3", "title": "Fixing flaky tests", "speaker": "Ola", "minutes": 45, "room_id": '
        'null, "hour": null}\n  ]\n}\n```\n\nIs a shared counter across talks and rooms '
        "reasonable, or is that over-thinking it?",
    ),
    Turn(
        "assistant",
        "A shared counter is exactly right for the radio problem: if the number is unique "
        "across both kinds, 'seven' can only mean one thing and the prefix is a courtesy. "
        "The table mints ids from one place:\n\n```python\ndef next_id(self, prefix: str) "
        '-> str:\n    return f"{prefix}{len(self._talks) + len(self._rooms) + 1}"\n```\n\n'
        "You get gaps in each sequence, which nobody will notice in a twenty-talk "
        "programme. If you ever persist the table, swap the length arithmetic for a stored "
        "counter and nothing else moves. Your JSON shape is fine; `room_id` and `hour` "
        "being null for unscheduled talks is clearer than omitting the keys, because the "
        "printing script can rely on every talk having the same fields. Write the dump "
        "with `sort_keys=True`, `indent=2` and a trailing newline so the diff in the repo "
        "stays readable between edit sessions; a two-line diff for a room change is the "
        "whole point of committing it.",
    ),
    Turn(
        "user",
        "The handout needs one line per talk. I wrote the test before the function this "
        "time:\n\n```python\nfrom talkslate.grid import programme_line\nfrom talkslate.model "
        'import Talk\n\n\ndef test_line_for_unscheduled_talk():\n    t = Talk("T3", '
        '"Fixing flaky tests", "Ola", 45)\n    assert programme_line(t) == "Fixing flaky '
        'tests - Ola (45 min)"\n\n\ndef test_line_for_scheduled_talk():\n    t = Talk('
        '"T1", "Sorting in practice", "Mina", 30, room_id="R2", hour=14)\n    assert '
        'programme_line(t) == "Sorting in practice - Mina (30 min) @ R2 14:00"\n```\n\n'
        "Should this be a method on Talk? It would be easy to find, but then the record "
        "knows about the handout, and I already have a second rendering in mind for the "
        "website that uses room names instead of ids. The handout is printed on A5 and "
        "folded, so lines have to stay short; that is why the hour is `14:00` and not a "
        "full timestamp.",
    ),
    Turn(
        "assistant",
        "Keep it a free function in `grid.py`. Two renderings of the same record is the "
        "textbook reason not to bake one of them into the dataclass:\n\n```python\ndef "
        'programme_line(talk: Talk) -> str:\n    where = ""\n    if talk.room_id is not '
        'None and talk.hour is not None:\n        where = f" @ {talk.room_id} {talk.hour:'
        '02d}:00"\n    return f"{talk.title} - {talk.speaker} ({talk.minutes} min){where}"'
        "\n```\n\nThe website version becomes `web_line(talk, room)` in the same module, "
        "taking the Room so it can print the name. `grid.py` depends on `model.py` only; "
        "the table never imports the grid, so you can change the handout format without "
        "touching storage. Give `web_line` the signature `(talk: Talk, room: Room | None)` "
        "and let the caller look the room up once; the grid module then keeps no knowledge "
        "of storage at all.",
    ),
    Turn(
        "user",
        "While testing the dump script I got this and I want to decide the policy once "
        "rather than per method:\n\n```\nTraceback (most recent call last):\n  File "
        '"/home/ola/conf2026/talkslate/dump.py", line 21, in <module>\n    talk = table.'
        'get_talk(row["talk_id"])\n  File "/home/ola/conf2026/talkslate/slate.py", line '
        "16, in get_talk\n    return self._talks[talk_id]\nKeyError: 'T12'\n```\n\nT12 "
        "had been withdrawn by the speaker but the sheet still referenced it. For context, "
        "the dump script walks a list of ids that a volunteer maintains by hand in "
        "`talks.txt`; withdrawn talks are supposed to be struck out of that file, but this "
        "is the second year running that somebody forgot. Should `get_talk` return None so "
        "the script can skip it, or is the KeyError the right call here?",
    ),
    Turn(
        "assistant",
        "The KeyError is right. A withdrawn talk that something still references is a data "
        "problem you want to find before the handout goes to the printer, not a line that "
        "silently disappears. Rule of thumb: `get_*` by id raises KeyError; list-style "
        "queries like `rooms()` return an empty list when there is nothing; actions on an "
        "unknown id raise KeyError because the caller is confused. Scripts that want to "
        "tolerate stale references say so explicitly:\n\n```python\ntry:\n    talk = "
        'table.get_talk(tid)\nexcept KeyError:\n    print(f"withdrawn or unknown: {tid}")'
        "\n    continue\n```\n\nThat keeps the tolerance in the one script that needs it "
        "and leaves the table honest for everyone else. If you want the hand-maintained "
        "list to be less fragile, have the dump script print a one-line summary at the "
        "end, `dumped 19 talks, 1 unknown`, so the stale entry is visible without reading "
        "a traceback; the table itself stays strict.",
    ),
    Turn(
        "user",
        "Two conventions to pin down before the real features. First: public functions in "
        "`talkslate.slate` return Talk or Room dataclass instances, never dicts or tuples. "
        "The sheet-export script last year returned dicts from one helper and objects from "
        "another and I spent an evening on `.get` versus attribute access.",
    ),
    Turn(
        "assistant",
        "Noted: public functions in `talkslate.slate` return Talk or Room instances (lists "
        "of them for queries), never dicts or tuples. One type per record, and the grid "
        "helpers work on anything the slate returns.",
    ),
    Turn(
        "user",
        "Second: validation lives in the table. `TalkTable` methods check their own inputs "
        "and raise ValueError, the way `insert_talk` rejects non-positive minutes today. "
        "Public functions build the record and hand it straight to the table with no "
        "pre-check of their own, so anything that bypasses the public function is still "
        "protected.",
    ),
    Turn(
        "assistant",
        "Understood: the table defends itself. New TalkTable methods validate their inputs "
        "and raise ValueError, and public functions in `slate.py` pass arguments through "
        "without a separate check, matching `insert_talk` and `submit_talk` as they are "
        "now.",
    ),
    Turn(
        "user",
        "One thing for later, not now: I'd like `rooms()` to eventually take an optional "
        "minimum capacity so the scheduling script can ask for rooms big enough for a "
        "keynote, and to come back sorted by capacity descending so the keynote lands in "
        "the biggest room automatically. Just noting it so we leave space for it.",
    ),
    Turn(
        "assistant",
        "Noted. When it comes, an optional keyword `min_capacity: int = 0` keeps the "
        "no-argument call working and the filter is a one-line comprehension over the "
        "stored rooms; the ordering is a `sorted(..., key=lambda r: -r.capacity)` in the "
        "same method. Both are additive and neither touches the public functions.",
    ),
    Turn(
        "user",
        "For the record, the tests that exist today are just these:\n\n```python\nimport "
        "pytest\n\nfrom talkslate.slate import TalkTable, submit_talk\n\n\ndef "
        'test_submit_mints_t1():\n    assert submit_talk(TalkTable(), "a", "b", 20).'
        'talk_id == "T1"\n\n\ndef test_submit_rejects_zero_minutes():\n    with pytest.'
        'raises(ValueError):\n        submit_talk(TalkTable(), "a", "b", 0)\n```\n\nI will '
        "paste the current files with each request so you see the real state.",
    ),
    Turn(
        "assistant",
        "Ready. Send the first feature and I will return the complete `slate.py`.",
    ),
]

_EVENT = (
    "Side note before the next one: the venue confirmed we get the seminar room for the "
    "whole day as well, so there will be two rooms in the data rather than one. Nothing "
    "about how we write the code changes."
)


def build() -> Session:
    return Session(
        id="S21",
        project="talkslate",
        target_family="validation",
        support_family="return_shape",
        lifecycle="stable",
        files=_FILES,
        prefix=_PREFIX,
        states=("storage", "api"),
        state_at=("storage", "storage"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10),
    )
