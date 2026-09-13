# ruff: noqa: E501
"""S43: radio schedule — missing_record (target, scope) x logging (support, warn)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""radio_schedule package: the community station\'s weekly grid."""\n'

_MODEL = '''"""Programme slots."""

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Slot:
    slot_id: str
    show: str
    day: str
    start: int  # minutes after midnight
    length_min: int
    status: str = "planned"
    host: str | None = None

    def with_changes(self, **changes) -> "Slot":
        return replace(self, **changes)
'''

_GRID = '''"""The weekly programme grid."""

import logging

from radio_schedule.model import Slot

log = logging.getLogger("radio_schedule")


class Grid:
    def __init__(self) -> None:
        self._slots: dict[str, Slot] = {}
        self._counter = 0

    def add_slot(self, show: str, day: str, start: int, length_min: int) -> Slot:
        self._counter += 1
        slot = Slot(f"S{self._counter}", show, day, start, length_min)
        if self._overlaps(slot):
            log.warning("slot %s (%s) overlaps another slot on %s", slot.slot_id, show, day)
        self._slots[slot.slot_id] = slot
        return slot

    def cancel(self, slot_id: str) -> Slot | None:
        slot = self._slots.get(slot_id)
        if slot is None:
            return None
        cancelled = slot.with_changes(status="cancelled")
        self._slots[slot_id] = cancelled
        return cancelled

    def get(self, slot_id: str) -> Slot | None:
        return self._slots.get(slot_id)

    def on_day(self, day: str) -> list[Slot]:
        return [s for s in self._slots.values() if s.day == day]

    def _overlaps(self, slot: Slot) -> bool:
        end = slot.start + slot.length_min
        return any(
            s.day == slot.day and s.start < end and slot.start < s.start + s.length_min
            for s in self._slots.values()
        )
'''

_FILES = {
    "radio_schedule/__init__.py": _INIT,
    "radio_schedule/model.py": _MODEL,
    "radio_schedule/grid.py": _GRID,
}

_HELPER_COMMON = """import logging

import pytest

from radio_schedule.grid import Grid
from radio_schedule.model import Slot


def _warnings(caplog):
    return [r for r in caplog.records if r.levelno == logging.WARNING]
"""

# ----------------------------------------------------------------- checkpoint 1: assign_host

_C1_HELPER = (
    _HELPER_COMMON
    + """

def _assign(grid):
    fn = getattr(grid, "assign_host", None) or getattr(grid, "set_host", None)
    assert fn is not None, "no assign_host method found"
    return fn
"""
)

_C1_FUNCTIONAL = {
    "test_assign_functional.py": _C1_HELPER
    + """

def test_assign_host_sets_host_and_stores():
    g = Grid()
    s = g.add_slot("Morning Mix", "mon", 420, 120)
    out = _assign(g)(s.slot_id, "ravi")
    assert out.host == "ravi" and out.slot_id == s.slot_id
    assert out.show == "Morning Mix" and out.status == "planned"
    assert g.get(s.slot_id).host == "ravi"


def test_assign_host_replaces_previous_host():
    g = Grid()
    s = g.add_slot("Morning Mix", "mon", 420, 120)
    _assign(g)(s.slot_id, "ravi")
    out = _assign(g)(s.slot_id, "june")
    assert out.host == "june" and g.get(s.slot_id).host == "june"


def test_assign_host_leaves_other_slots_alone():
    g = Grid()
    a = g.add_slot("Morning Mix", "mon", 420, 120)
    b = g.add_slot("Lunch Jazz", "mon", 720, 60)
    _assign(g)(a.slot_id, "ravi")
    assert g.get(b.slot_id).host is None and len(g.on_day("mon")) == 2
"""
}

_C1_REGRESSION = {
    "test_assign_regression.py": _HELPER_COMMON
    + """

def test_add_cancel_get_on_day_unchanged(caplog):
    caplog.set_level(logging.DEBUG)
    g = Grid()
    s = g.add_slot("Morning Mix", "mon", 420, 120)
    assert s.slot_id == "S1" and s.status == "planned" and s.host is None
    assert g.get("S1") is s and g.get("S9") is None
    assert g.cancel("S9") is None
    assert g.cancel("S1").status == "cancelled"
    assert g.get("S1").status == "cancelled"
    assert [x.slot_id for x in g.on_day("mon")] == ["S1"] and g.on_day("tue") == []
    assert caplog.records == []
    g.add_slot("Breakfast Chat", "mon", 480, 30)
    assert len(_warnings(caplog)) == 1 and len(caplog.records) == 1
"""
}

_C1_CONTRACT = {
    "none": {
        "test_assign_missing.py": _C1_HELPER
        + """

def test_assign_host_unknown_returns_none_and_changes_nothing():
    g = Grid()
    s = g.add_slot("Morning Mix", "mon", 420, 120)
    assert _assign(g)("S404", "ravi") is None
    assert g.get(s.slot_id).host is None and g.get("S404") is None
    assert len(g.on_day("mon")) == 1
"""
    },
    "raise": {
        "test_assign_missing.py": _C1_HELPER
        + """

def test_assign_host_unknown_raises_keyerror():
    g = Grid()
    g.add_slot("Morning Mix", "mon", 420, 120)
    with pytest.raises(KeyError):
        _assign(g)("S404", "ravi")
"""
    },
}

_C1_SUPPORT = {
    "test_assign_logging.py": _C1_HELPER
    + """

def test_add_slot_overlap_warns_exactly_once(caplog):
    caplog.set_level(logging.DEBUG)
    g = Grid()
    g.add_slot("Morning Mix", "mon", 420, 120)
    assert caplog.records == []
    g.add_slot("Breakfast Chat", "mon", 480, 30)
    assert len(caplog.records) == 1 and len(_warnings(caplog)) == 1


def test_assign_host_double_booked_warns_exactly_once(caplog):
    caplog.set_level(logging.DEBUG)
    g = Grid()
    a = g.add_slot("Morning Mix", "mon", 420, 120)
    b = g.add_slot("Lunch Jazz", "mon", 720, 60)
    _assign(g)(a.slot_id, "ravi")
    assert caplog.records == []
    out = _assign(g)(b.slot_id, "ravi")
    assert out.host == "ravi"
    assert len(caplog.records) == 1 and len(_warnings(caplog)) == 1


def test_assign_host_normal_path_logs_nothing(caplog):
    caplog.set_level(logging.DEBUG)
    g = Grid()
    a = g.add_slot("Morning Mix", "mon", 420, 120)
    b = g.add_slot("Lunch Jazz", "tue", 720, 60)
    _assign(g)(a.slot_id, "ravi")
    _assign(g)(b.slot_id, "ravi")
    assert caplog.records == []
"""
}

_ASSIGN_NONE = """
    def assign_host(self, slot_id: str, host: str) -> Slot | None:
        slot = self._slots.get(slot_id)
        if slot is None:
            return None
        if any(s.host == host and s.day == slot.day and s.slot_id != slot_id for s in self._slots.values()):
            log.warning("host %s already has a slot on %s", host, slot.day)
        assigned = slot.with_changes(host=host)
        self._slots[slot_id] = assigned
        return assigned
"""

_ASSIGN_RAISE = """
    def assign_host(self, slot_id: str, host: str) -> Slot:
        slot = self._slots[slot_id]
        if any(s.host == host and s.day == slot.day and s.slot_id != slot_id for s in self._slots.values()):
            log.warning("host %s already has a slot on %s", host, slot.day)
        assigned = slot.with_changes(host=host)
        self._slots[slot_id] = assigned
        return assigned
"""


def _gold1(state: str) -> str:
    body = _ASSIGN_NONE if state == "none" else _ASSIGN_RAISE
    return _GRID.replace("\n    def get(", body + "\n    def get(", 1)


_REQ1 = Request(
    text=(
        "Add a public method `assign_host(slot_id, host)` on Grid for the planning desk: "
        "it sets the slot's host to the given name (replacing any previous host), stores "
        "the updated slot and returns it. If that host already has another slot on the "
        "same day, that is a notable condition for the schedule editor, but the "
        "assignment still goes ahead."
    ),
    target="radio_schedule/grid.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"none": _gold1("none"), "raise": _gold1("raise")},
)

# ----------------------------------------------------------------- checkpoint 2: go_live

_C2_HELPER = (
    _HELPER_COMMON
    + """

def _live(grid):
    fn = getattr(grid, "go_live", None) or getattr(grid, "start", None)
    assert fn is not None, "no go_live method found"
    return fn
"""
)

_C2_FUNCTIONAL = {
    "test_live_functional.py": _C2_HELPER
    + """

def test_go_live_sets_status_on_air():
    g = Grid()
    s = g.add_slot("Morning Mix", "mon", 420, 120)
    g.assign_host(s.slot_id, "ravi")
    out = _live(g)(s.slot_id)
    assert out.status == "on_air" and out.slot_id == s.slot_id
    assert out.host == "ravi" and out.show == "Morning Mix"
    assert g.get(s.slot_id).status == "on_air"


def test_go_live_when_another_is_on_air_still_goes_live():
    g = Grid()
    a = g.add_slot("Morning Mix", "mon", 420, 120)
    b = g.add_slot("Lunch Jazz", "mon", 720, 60)
    _live(g)(a.slot_id)
    out = _live(g)(b.slot_id)
    assert out.status == "on_air" and g.get(a.slot_id).status == "on_air"


def test_go_live_leaves_other_slots_alone():
    g = Grid()
    a = g.add_slot("Morning Mix", "mon", 420, 120)
    b = g.add_slot("Lunch Jazz", "tue", 720, 60)
    _live(g)(a.slot_id)
    assert g.get(b.slot_id).status == "planned" and len(g.on_day("mon")) == 1
"""
}

_C2_REGRESSION = {
    "test_live_regression.py": _HELPER_COMMON
    + """

def test_add_cancel_assign_get_unchanged(caplog):
    caplog.set_level(logging.DEBUG)
    g = Grid()
    s = g.add_slot("Morning Mix", "mon", 420, 120)
    assert g.get("S1") is s and g.get("S9") is None
    assert g.assign_host("S1", "ravi").host == "ravi"
    assert g.assign_host("S9", "ravi") is None
    assert g.cancel("S9") is None
    assert g.cancel("S1").status == "cancelled"
    assert g.get("S1").status == "cancelled"
    assert [x.slot_id for x in g.on_day("mon")] == ["S1"]
    assert caplog.records == []
    t = g.add_slot("Lunch Jazz", "mon", 720, 60)
    g.assign_host(t.slot_id, "ravi")
    assert len(_warnings(caplog)) == 1 and len(caplog.records) == 1
"""
}

_C2_CONTRACT = {
    "none": {
        "test_live_missing.py": _C2_HELPER
        + """

def test_go_live_unknown_returns_none_and_changes_nothing():
    g = Grid()
    s = g.add_slot("Morning Mix", "mon", 420, 120)
    assert _live(g)("S404") is None
    assert g.get(s.slot_id).status == "planned" and g.get("S404") is None
    assert len(g.on_day("mon")) == 1
"""
    },
    "raise": {
        "test_live_missing.py": _C2_HELPER
        + """

def test_go_live_unknown_raises_keyerror():
    g = Grid()
    g.add_slot("Morning Mix", "mon", 420, 120)
    with pytest.raises(KeyError):
        _live(g)("S404")
"""
    },
}

_C2_SUPPORT = {
    "test_live_logging.py": _C2_HELPER
    + """

def test_add_slot_and_assign_host_still_warn_exactly_once(caplog):
    caplog.set_level(logging.DEBUG)
    g = Grid()
    a = g.add_slot("Morning Mix", "mon", 420, 120)
    b = g.add_slot("Breakfast Chat", "mon", 480, 30)
    assert len(caplog.records) == 1 and len(_warnings(caplog)) == 1
    caplog.clear()
    g.assign_host(a.slot_id, "ravi")
    g.assign_host(b.slot_id, "ravi")
    assert len(caplog.records) == 1 and len(_warnings(caplog)) == 1


def test_go_live_with_another_on_air_warns_exactly_once(caplog):
    caplog.set_level(logging.DEBUG)
    g = Grid()
    a = g.add_slot("Morning Mix", "mon", 420, 120)
    b = g.add_slot("Lunch Jazz", "mon", 720, 60)
    _live(g)(a.slot_id)
    assert caplog.records == []
    out = _live(g)(b.slot_id)
    assert out.status == "on_air"
    assert len(caplog.records) == 1 and len(_warnings(caplog)) == 1


def test_go_live_normal_path_logs_nothing(caplog):
    caplog.set_level(logging.DEBUG)
    g = Grid()
    a = g.add_slot("Morning Mix", "mon", 420, 120)
    b = g.add_slot("Lunch Jazz", "tue", 720, 60)
    _live(g)(a.slot_id)
    _live(g)(b.slot_id)
    assert caplog.records == []
"""
}

_LIVE_NONE = """
    def go_live(self, slot_id: str) -> Slot | None:
        slot = self._slots.get(slot_id)
        if slot is None:
            return None
        if any(s.status == "on_air" and s.day == slot.day and s.slot_id != slot_id for s in self._slots.values()):
            log.warning("another slot is already on air on %s", slot.day)
        live = slot.with_changes(status="on_air")
        self._slots[slot_id] = live
        return live
"""

_LIVE_RAISE = """
    def go_live(self, slot_id: str) -> Slot:
        slot = self._slots[slot_id]
        if any(s.status == "on_air" and s.day == slot.day and s.slot_id != slot_id for s in self._slots.values()):
            log.warning("another slot is already on air on %s", slot.day)
        live = slot.with_changes(status="on_air")
        self._slots[slot_id] = live
        return live
"""


def _gold2(state: str) -> str:
    # Built on the checkpoint-1 gold under the state then in force (none).
    body = _LIVE_NONE if state == "none" else _LIVE_RAISE
    return _gold1("none").replace("\n    def get(", body + "\n    def get(", 1)


_REQ2 = Request(
    text=(
        "Add a public method `go_live(slot_id)` on Grid for the on-air desk, called by "
        "the studio automation the moment a presenter opens the fader: it sets the "
        'slot status to "on_air", stores the updated slot and returns it. If another '
        "slot on the same day is already on air, that is a notable condition for the "
        "studio, but the slot still goes live. Host and show are left as they are."
    ),
    target="radio_schedule/grid.py",
    functional_tests=_C2_FUNCTIONAL,
    regression_tests=_C2_REGRESSION,
    contract_tests=_C2_CONTRACT,
    support_tests=_C2_SUPPORT,
    gold={"none": _gold2("none"), "raise": _gold2("raise")},
)

# ----------------------------------------------------------------- prefix (16 turns)

_PREFIX = [
    Turn(
        "user",
        "I look after the schedule for a small community radio station: one studio, "
        "about forty volunteer presenters, and a weekly grid that changes every time "
        "someone goes on holiday. The grid lives in a spreadsheet that the studio "
        "automation cannot read, so twice a month the wrong jingle plays over the wrong "
        "show. I am writing a small `radio_schedule` package: a Grid in memory, a Slot "
        "record per programme, and eventually an export the automation can consume. "
        "Slots are a day, a start in minutes after midnight and a length, so a Monday "
        'breakfast show is:\n\n```python\ngrid.add_slot("Morning Mix", "mon", 420, '
        "120)\n```\n\nCould you draft a README scope section? The station manager "
        "thinks this will also handle the music library and the licensing returns, "
        "and I want the first paragraph to say plainly that it is the grid and nothing "
        "else. Two desks will use it: the planning desk, which is me on a Tuesday "
        "evening, and the on-air desk, which is the studio automation and whoever is "
        "presenting at the time. Neither desk should need to read the code.",
    ),
    Turn(
        "assistant",
        "A scope block that draws the line at the grid:\n\n```\n## Scope\n"
        "radio_schedule is the station's programme grid. It keeps Slot records (show, "
        "day, start, length, host, status) in memory for the running process and is "
        "the single source the planning desk edits and the on-air desk reads. It does "
        "not hold the music library, licensing returns, presenter contact details or "
        "audio; the automation keeps doing all of that.\n\n## Non-goals\n- music "
        "library or playout\n- licensing reports\n- presenter rota or contacts\n```\n\n"
        "And a usage block so both desks see the same model:\n\n```python\nfrom "
        'radio_schedule.grid import Grid\n\ngrid = Grid()\nmix = grid.add_slot("Morning '
        'Mix", "mon", 420, 120)\nprint(mix.slot_id, mix.day, mix.start)\n```\n\nMinutes '
        "after midnight is the right unit: it makes overlap arithmetic integer-only and "
        "the automation already thinks in minutes, so the export will be a straight "
        "copy rather than a conversion. Keep day as a short lowercase string for now; "
        "if the grid ever needs dates, that is an export concern, not a Slot field.",
    ),
    Turn(
        "user",
        "About slot ids. I mint S1, S2, ... from a counter, and the grid is rebuilt "
        "from the spreadsheet each time the planning script runs, so the ids are not "
        "stable across runs. The automation vendor's docs want a 'stable programme "
        "reference' in the export, and the presenters have started quoting ids to each "
        "other in the WhatsApp group. Here is what the planning script prints "
        "today:\n\n```\nS1 mon 07:00 Morning Mix (120)\nS2 mon 12:00 Lunch Jazz (60)\n"
        "S3 tue 07:00 Morning Mix (120)\nS4 tue 19:00 Folk Hour (60)\n```\n\nShould "
        "the id be derived from day and start, like mon-0700, so it is stable, or "
        "should I keep the counter and put a stable key in the export only? I would "
        "rather not repaint the ids after presenters have learned them, and the "
        "vendor will not say what happens if the reference changes between exports.",
    ),
    Turn(
        "assistant",
        "Keep the counter for the id and put the stable reference in the export. An id "
        "derived from day and start stops being an id the moment a show moves half an "
        "hour, and moves are exactly the edits you make most; presenters would then "
        "quote an id that no longer matches the slot. The export can carry "
        "`day`, `start` and `show` alongside the counter id, which is all the automation "
        "needs to match programmes across runs, and only `add_slot` mints ids so a "
        "later change is one line:\n\n```python\ndef _next_id(self) -> str:\n    "
        'self._counter += 1\n    return f"S{self._counter}"\n```\n\nIf the WhatsApp '
        "quoting becomes a problem, print the show name next to the id in every "
        "message the planning script emits, as your listing already does, and the ids "
        "become a convenience rather than something anyone has to remember. The "
        "vendor's silence on changed references is itself a reason to give them a key "
        "that only changes when the programme really moves. "
        "Say so in the README so nobody derives ids from the clock later "
        "when the counter looks inconvenient.",
    ),
    Turn(
        "user",
        "Here is my test file so far. I want to check the shape before writing more, "
        "and in particular whether testing `on_day` by ids is the right level or "
        "whether I should compare whole Slot objects:\n\n```python\nfrom "
        "radio_schedule.grid import Grid\n\n\ndef test_add_slot_mints_sequential_ids():"
        '\n    g = Grid()\n    assert g.add_slot("Morning Mix", "mon", 420, 120).slot_id '
        '== "S1"\n    assert g.add_slot("Lunch Jazz", "mon", 720, 60).slot_id == "S2"\n'
        "\n\ndef test_on_day_filters_by_day():\n    g = Grid()\n    g.add_slot("
        '"Morning Mix", "mon", 420, 120)\n    g.add_slot("Folk Hour", "tue", 1140, 60)\n'
        '    assert [s.slot_id for s in g.on_day("mon")] == ["S1"]\n\n\ndef '
        'test_get_unknown_is_none():\n    assert Grid().get("S7") is None\n```\n\n'
        "Whole-object comparisons feel brittle because Slot will grow fields.",
    ),
    Turn(
        "assistant",
        "Ids are the right level for `on_day`: the test is about membership and order, "
        "and comparing ids keeps it green when Slot grows a field. Compare whole "
        "objects only where the test is about the record itself, such as a cancel test "
        "that checks the status flipped and nothing else moved:\n\n```python\ndef "
        'test_cancel_flips_status_only():\n    g = Grid()\n    s = g.add_slot("Morning '
        'Mix", "mon", 420, 120)\n    out = g.cancel(s.slot_id)\n    assert out == '
        's.with_changes(status="cancelled")\n    assert g.get(s.slot_id) is out\n```\n\n'
        "That one earns the whole-object comparison because 'nothing else moved' is "
        "the assertion. For the overlap logic I would add a table test with three "
        "cases: touching ends (no overlap), one minute inside (overlap), and a "
        "different day at the same time (no overlap). Those three cases are where "
        "every overlap bug I have seen actually lives, and they take six lines. "
        "Put them in their own file so the grid tests stay about the grid "
        "and the arithmetic tests stay about minutes.",
    ),
    Turn(
        "user",
        "Now the thing I actually need a rule for. When the planning desk adds a slot "
        "that overlaps an existing one, what should happen? Today `add_slot` accepts "
        "it and emits a warning through the `radio_schedule` logger, and the planning "
        "script shows warnings in yellow so I see them at a glance. That is the "
        "behaviour I want: the grid is often deliberately overlapped for a week while "
        "two shows swap, so raising would block real work. But last week I got this in "
        "the script output for one overlapping slot:\n\n```\nWARNING radio_schedule: "
        "slot S9 (Breakfast Chat) overlaps another slot on mon\nWARNING radio_schedule: "
        "slot S9 (Breakfast Chat) overlaps another slot on mon\n```\n\nbecause a helper "
        "I wrote called `add_slot` twice on a retry. Two warnings for one condition "
        "makes the yellow lines useless. How should I pin this down so it stays one "
        "warning per condition and the normal path stays silent? I would like the "
        "rule to be something a test enforces, not a comment someone ignores. "
        "The station manager reads the yellow lines too, so noise there has a cost.",
    ),
    Turn(
        "assistant",
        "Pin it in the tests with `caplog` and count records, not substrings. Set the "
        "capture level to DEBUG so 'nothing logged' is really nothing, and assert the "
        "exact number:\n\n```python\ndef test_overlap_warns_exactly_once(caplog):\n"
        '    caplog.set_level(logging.DEBUG)\n    g = Grid()\n    g.add_slot("Morning '
        'Mix", "mon", 420, 120)\n    assert caplog.records == []\n    g.add_slot('
        '"Breakfast Chat", "mon", 480, 30)\n    assert len(caplog.records) == 1\n    '
        "assert caplog.records[0].levelno == logging.WARNING\n```\n\nThe first "
        "assertion pins the silent normal path, the second pins exactly one WARNING "
        "for the condition, and the retry bug shows up as a count of two. The retry "
        "helper should be fixed separately so it does not call `add_slot` again on a "
        "path that already succeeded; the grid's job is one warning per condition it "
        "detects, no more. "
        "Keep the message stable as well, since people grep the script output for it.",
    ),
    Turn(
        "user",
        "That is the convention, stated once: when a public Grid method meets a "
        "notable-but-non-fatal condition (an overlap, a double-booked host, that kind "
        "of thing) it emits exactly one `logging.warning` on the `radio_schedule` "
        "logger and carries on; it never raises for it, never logs twice, and logs "
        "nothing at all on the normal path. `add_slot` already does this for overlaps "
        "and new methods do the same for their own conditions.",
    ),
    Turn(
        "assistant",
        "Noted: exactly one warning per notable condition on the `radio_schedule` "
        "logger, the operation still completes, and the normal path emits no log "
        "record. New methods will check their condition once, warn once, and proceed.",
    ),
    Turn(
        "user",
        "Second convention, for unknown ids. Methods that act on a slot by id, like "
        "`cancel`, return None when the id is not in the grid and change nothing. The "
        "planning script feeds ids copied from the spreadsheet and stale ones are "
        "common; printing 'no such slot' and moving on is what I want there. New "
        "methods that act on an id do the same.",
    ),
    Turn(
        "assistant",
        "Understood: id-keyed actions return None on an unknown slot id and leave the "
        "grid untouched, matching `cancel`. New methods will look up with "
        "`self._slots.get(slot_id)` and return None before doing anything else.",
    ),
    Turn(
        "user",
        "For later: the export for the automation. I imagine the planning script "
        "doing:\n\n```python\nfor slot in grid.on_day(day):\n    writer.writerow([slot."
        'day, slot.start, slot.length_min, slot.show, slot.host or ""])\n```\n\nNot '
        "now, just checking Slot already has what the automation's CSV wants.",
    ),
    Turn(
        "assistant",
        "It does: day, start, length and show are all on Slot, and host is optional, "
        "so the empty-string fallback in your row is the only conversion. Sorting "
        "`on_day` output by `start` before writing keeps the CSV in broadcast order.",
    ),
    Turn(
        "user",
        "Right, let's get host assignment working before Tuesday's planning session. I "
        "will paste the current files with each request so you see the real state of "
        "the code rather than my memory of it.",
    ),
    Turn(
        "assistant",
        "Ready when you are. Send the request and I will return the full grid module.",
    ),
]

_EVENT = (
    "One scoped exception to the unknown-id rule, effective now: methods used by the "
    "on-air desk (anything the studio automation calls while broadcasting) raise "
    "KeyError on an unknown slot id, because the automation must stop rather than "
    "silently carry on with a mistyped id from the studio. Planning-desk methods, "
    "including `cancel` and `assign_host`, keep returning None as before."
)


def build() -> Session:
    return Session(
        id="S43",
        project="radio_schedule",
        target_family="missing_record",
        support_family="logging",
        lifecycle="scope",
        files=_FILES,
        prefix=_PREFIX,
        states=("none", "raise"),
        state_at=("none", "raise"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10),
        tags={"support_state": "warn", "scope": "on-air desk methods"},
    )
