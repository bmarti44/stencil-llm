# ruff: noqa: E501
"""S39: drone flight logs — missing_record (target, scope) x error_surface (support, propagate)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""flightlog package: the club\'s drone flight log."""\n'

_MODEL = '''"""Flight records."""

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Flight:
    flight_id: str
    pilot: str
    drone: str
    duration_min: int
    status: str = "open"
    reviewer: str | None = None

    def with_changes(self, **changes) -> "Flight":
        return replace(self, **changes)
'''

_EXPORT = '''"""JSON-lines export file read by the ground station."""

import json


def append_json(path: str, record: dict) -> None:
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\\n")
'''

_LOG = '''"""The club flight log."""

from flightlog import export
from flightlog.model import Flight


class FlightLog:
    def __init__(self, export_path: str) -> None:
        self._export_path = export_path
        self._flights: dict[str, Flight] = {}
        self._counter = 0

    def record(self, pilot: str, drone: str, duration_min: int) -> Flight:
        self._counter += 1
        flight = Flight(f"F{self._counter}", pilot, drone, duration_min)
        self._flights[flight.flight_id] = flight
        export.append_json(self._export_path, {"event": "record", "flight_id": flight.flight_id, "pilot": pilot})
        return flight

    def close(self, flight_id: str) -> Flight:
        flight = self._flights[flight_id]
        closed = flight.with_changes(status="closed")
        self._flights[flight_id] = closed
        export.append_json(self._export_path, {"event": "close", "flight_id": flight_id})
        return closed

    def get(self, flight_id: str) -> Flight | None:
        return self._flights.get(flight_id)

    def count(self) -> int:
        return len(self._flights)
'''

_FILES = {
    "flightlog/__init__.py": _INIT,
    "flightlog/model.py": _MODEL,
    "flightlog/export.py": _EXPORT,
    "flightlog/log.py": _LOG,
}

_HELPER_COMMON = """import json

import pytest

from flightlog import export
from flightlog.log import FlightLog
from flightlog.model import Flight


def _log(tmp_path):
    path = tmp_path / "export.jsonl"
    return FlightLog(str(path)), path


def _last(path):
    return json.loads(path.read_text().splitlines()[-1])


_ERR = OSError(5, "Input/output error")


def _boom(path, record):
    raise _ERR
"""

# ----------------------------------------------------------------- checkpoint 1: approve

_C1_HELPER = (
    _HELPER_COMMON
    + """

def _approve(log):
    fn = getattr(log, "approve", None) or getattr(log, "approve_flight", None)
    assert fn is not None, "no approve method found"
    return fn
"""
)

_C1_FUNCTIONAL = {
    "test_approve_functional.py": _C1_HELPER
    + """

# Every fixture below holds at least TWO flights, and the flight the test does
# not operate on is approved first so that its status and reviewer (both
# defaulted attributes) are NOT the dataclass defaults.  An operation that
# wipes unrelated records, or resets an unrelated defaulted attribute, is then
# visible through the log's own public reader.
def _assert_other_intact(log, other, pilot, drone, minutes, reviewer):
    kept = log.get(other.flight_id)
    assert kept is not None, "an unrelated flight was dropped from the log"
    assert kept.flight_id == other.flight_id and kept.pilot == pilot
    assert kept.drone == drone and kept.duration_min == minutes
    assert kept.status == "approved" and kept.reviewer == reviewer
    assert log.count() == 2


def test_approve_sets_status_and_reviewer(tmp_path):
    log, _ = _log(tmp_path)
    other = log.record("jon", "mini-4", 9)
    _approve(log)(other.flight_id, "rae")
    f = log.record("mira", "mavic-3", 22)
    out = _approve(log)(f.flight_id, "ken")
    assert out.status == "approved" and out.reviewer == "ken"
    assert out.flight_id == f.flight_id and out.duration_min == 22
    assert log.get(f.flight_id).reviewer == "ken"
    _assert_other_intact(log, other, "jon", "mini-4", 9, "rae")


def test_approve_exports_event(tmp_path):
    log, path = _log(tmp_path)
    f = log.record("mira", "mavic-3", 22)
    _approve(log)(f.flight_id, "ken")
    rec = _last(path)
    assert rec["event"] == "approve" and rec["flight_id"] == f.flight_id
    assert rec["reviewer"] == "ken"
    assert len(path.read_text().splitlines()) == 2
    g = log.record("jon", "mini-4", 9)
    _approve(log)(g.flight_id, "rae")
    assert _last(path)["flight_id"] == g.flight_id
    assert _last(path)["reviewer"] == "rae"
    _assert_other_intact(log, f, "mira", "mavic-3", 22, "ken")


def test_approve_leaves_other_flights_alone(tmp_path):
    log, _ = _log(tmp_path)
    a = log.record("mira", "mavic-3", 22)
    b = log.record("jon", "mini-4", 9)
    _approve(log)(a.flight_id, "ken")
    assert log.get(b.flight_id).status == "open" and log.count() == 2
    _approve(log)(b.flight_id, "rae")
    assert log.get(b.flight_id).reviewer == "rae"
    _assert_other_intact(log, a, "mira", "mavic-3", 22, "ken")


def test_close_keeps_the_reviewer_and_the_other_flights(tmp_path):
    log, _ = _log(tmp_path)
    a = log.record("mira", "mavic-3", 22)
    b = log.record("jon", "mini-4", 9)
    _approve(log)(a.flight_id, "ken")
    _approve(log)(b.flight_id, "rae")
    out = log.close(b.flight_id)
    assert out.status == "closed" and out.reviewer == "rae"
    assert log.get(b.flight_id).reviewer == "rae"
    _assert_other_intact(log, a, "mira", "mavic-3", 22, "ken")
"""
}

_C1_REGRESSION = {
    "test_approve_regression.py": _HELPER_COMMON
    + """

def test_record_close_get_count_unchanged(tmp_path):
    log, path = _log(tmp_path)
    f = log.record("mira", "mavic-3", 22)
    assert f.flight_id == "F1" and f.status == "open" and f.reviewer is None
    assert log.get("F1") is f and log.get("F9") is None
    assert log.close("F1").status == "closed"
    assert log.get("F1").status == "closed"
    with pytest.raises(KeyError):
        log.close("F9")
    assert log.count() == 1
    assert [json.loads(x)["event"] for x in path.read_text().splitlines()] == ["record", "close"]
    g = log.record("jon", "mini-4", 9)
    assert g.flight_id == "F2" and g.status == "open" and g.reviewer is None
    assert log.get("F2") is g and log.count() == 2
    assert log.close("F2").status == "closed"
    kept = log.get("F1")
    assert kept is not None, "closing one flight dropped another from the log"
    assert kept.flight_id == "F1" and kept.status == "closed"
    assert kept.pilot == "mira" and kept.drone == "mavic-3"
    assert kept.duration_min == 22 and log.count() == 2
"""
}

_C1_CONTRACT = {
    "raise": {
        "test_approve_missing.py": _C1_HELPER
        + """

def test_approve_unknown_raises_keyerror(tmp_path):
    log, _ = _log(tmp_path)
    log.record("mira", "mavic-3", 22)
    with pytest.raises(KeyError):
        _approve(log)("F404", "ken")
"""
    },
    "none": {
        "test_approve_missing.py": _C1_HELPER
        + """

def test_approve_unknown_returns_none_and_changes_nothing(tmp_path):
    log, path = _log(tmp_path)
    f = log.record("mira", "mavic-3", 22)
    before = path.read_text()
    assert _approve(log)("F404", "ken") is None
    assert path.read_text() == before
    assert log.count() == 1 and log.get(f.flight_id).status == "open"
"""
    },
}

_C1_SUPPORT = {
    "test_approve_errors.py": _C1_HELPER
    + """

def test_record_propagates_raw_oserror(tmp_path, monkeypatch):
    log, _ = _log(tmp_path)
    monkeypatch.setattr(export, "append_json", _boom)
    with pytest.raises(OSError) as ei:
        log.record("mira", "mavic-3", 22)
    assert ei.value is _ERR


def test_close_propagates_raw_oserror(tmp_path, monkeypatch):
    log, _ = _log(tmp_path)
    f = log.record("mira", "mavic-3", 22)
    monkeypatch.setattr(export, "append_json", _boom)
    with pytest.raises(OSError) as ei:
        log.close(f.flight_id)
    assert ei.value is _ERR


def test_approve_propagates_raw_oserror(tmp_path, monkeypatch):
    log, _ = _log(tmp_path)
    f = log.record("mira", "mavic-3", 22)
    monkeypatch.setattr(export, "append_json", _boom)
    with pytest.raises(OSError) as ei:
        _approve(log)(f.flight_id, "ken")
    assert ei.value is _ERR
"""
}

_APPROVE_RAISE = """
    def approve(self, flight_id: str, reviewer: str) -> Flight:
        flight = self._flights[flight_id]
        approved = flight.with_changes(status="approved", reviewer=reviewer)
        self._flights[flight_id] = approved
        export.append_json(self._export_path, {"event": "approve", "flight_id": flight_id, "reviewer": reviewer})
        return approved
"""

_APPROVE_NONE = """
    def approve(self, flight_id: str, reviewer: str) -> Flight | None:
        flight = self._flights.get(flight_id)
        if flight is None:
            return None
        approved = flight.with_changes(status="approved", reviewer=reviewer)
        self._flights[flight_id] = approved
        export.append_json(self._export_path, {"event": "approve", "flight_id": flight_id, "reviewer": reviewer})
        return approved
"""


def _gold1(state: str) -> str:
    body = _APPROVE_RAISE if state == "raise" else _APPROVE_NONE
    return _LOG.replace("\n    def get(", body + "\n    def get(", 1)


_REQ1 = Request(
    text=(
        "Add a public method `approve(flight_id, reviewer)` on FlightLog for the safety "
        'officer\'s review form: it sets the flight status to "approved", records the '
        "reviewer name on the flight, stores the updated flight, appends an export "
        'record {"event": "approve", "flight_id": ..., "reviewer": ...} and returns the '
        "updated flight."
    ),
    target="flightlog/log.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"raise": _gold1("raise"), "none": _gold1("none")},
)

# ----------------------------------------------------------------- checkpoint 2: mark_uploaded

_C2_HELPER = (
    _HELPER_COMMON
    + """

def _uploaded(log):
    fn = getattr(log, "mark_uploaded", None) or getattr(log, "uploaded", None)
    assert fn is not None, "no mark_uploaded method found"
    return fn
"""
)

_C2_FUNCTIONAL = {
    "test_uploaded_functional.py": _C2_HELPER
    + """

# Every fixture below holds at least TWO flights, and the flight the test does
# not operate on is approved first so that its status and reviewer (both
# defaulted attributes) are NOT the dataclass defaults.  An operation that
# wipes unrelated records, or resets an unrelated defaulted attribute, is then
# visible through the log's own public reader.
def _assert_other_intact(log, other, pilot, drone, minutes, reviewer):
    kept = log.get(other.flight_id)
    assert kept is not None, "an unrelated flight was dropped from the log"
    assert kept.flight_id == other.flight_id and kept.pilot == pilot
    assert kept.drone == drone and kept.duration_min == minutes
    assert kept.status == "approved" and kept.reviewer == reviewer
    assert log.count() == 2


def test_mark_uploaded_sets_status(tmp_path):
    log, _ = _log(tmp_path)
    other = log.record("jon", "mini-4", 9)
    log.approve(other.flight_id, "rae")
    f = log.record("mira", "mavic-3", 22)
    out = _uploaded(log)(f.flight_id, "9f3a")
    assert out.status == "uploaded" and out.flight_id == f.flight_id
    assert out.pilot == "mira" and out.duration_min == 22
    assert log.get(f.flight_id).status == "uploaded"
    _assert_other_intact(log, other, "jon", "mini-4", 9, "rae")


def test_mark_uploaded_exports_event_with_checksum(tmp_path):
    log, path = _log(tmp_path)
    f = log.record("mira", "mavic-3", 22)
    _uploaded(log)(f.flight_id, "9f3a")
    rec = _last(path)
    assert rec["event"] == "uploaded" and rec["flight_id"] == f.flight_id
    assert rec["checksum"] == "9f3a"
    assert len(path.read_text().splitlines()) == 2
    g = log.record("jon", "mini-4", 9)
    log.approve(g.flight_id, "rae")
    _uploaded(log)(g.flight_id, "77b1")
    assert _last(path)["flight_id"] == g.flight_id
    assert _last(path)["checksum"] == "77b1"
    kept = log.get(f.flight_id)
    assert kept is not None, "uploading one flight dropped another from the log"
    assert kept.status == "uploaded" and kept.pilot == "mira"
    assert kept.duration_min == 22 and log.count() == 2


def test_mark_uploaded_keeps_reviewer_and_others(tmp_path):
    log, _ = _log(tmp_path)
    a = log.record("mira", "mavic-3", 22)
    b = log.record("jon", "mini-4", 9)
    log.approve(a.flight_id, "ken")
    out = _uploaded(log)(a.flight_id, "9f3a")
    assert out.reviewer == "ken"
    assert log.get(b.flight_id).status == "open" and log.count() == 2
    log.approve(b.flight_id, "rae")
    out2 = _uploaded(log)(b.flight_id, "77b1")
    assert out2.reviewer == "rae" and out2.status == "uploaded"
    kept = log.get(a.flight_id)
    assert kept is not None, "uploading one flight dropped another from the log"
    assert kept.status == "uploaded" and kept.reviewer == "ken"
    assert kept.pilot == "mira" and kept.duration_min == 22
    assert log.count() == 2


def test_close_keeps_the_reviewer_and_the_other_flights(tmp_path):
    log, _ = _log(tmp_path)
    a = log.record("mira", "mavic-3", 22)
    b = log.record("jon", "mini-4", 9)
    log.approve(a.flight_id, "ken")
    log.approve(b.flight_id, "rae")
    out = log.close(b.flight_id)
    assert out.status == "closed" and out.reviewer == "rae"
    assert log.get(b.flight_id).reviewer == "rae"
    _assert_other_intact(log, a, "mira", "mavic-3", 22, "ken")
"""
}

_C2_REGRESSION = {
    "test_uploaded_regression.py": _HELPER_COMMON
    + """

def test_record_close_approve_get_unchanged(tmp_path):
    log, path = _log(tmp_path)
    f = log.record("mira", "mavic-3", 22)
    assert log.get("F1") is f and log.get("F9") is None
    assert log.approve("F1", "ken").reviewer == "ken"
    with pytest.raises(KeyError):
        log.approve("F9", "ken")
    assert log.close("F1").status == "closed"
    assert log.get("F1").status == "closed"
    with pytest.raises(KeyError):
        log.close("F9")
    assert log.count() == 1
    assert [json.loads(x)["event"] for x in path.read_text().splitlines()] == ["record", "approve", "close"]
    g = log.record("jon", "mini-4", 9)
    assert g.flight_id == "F2" and g.status == "open" and g.reviewer is None
    assert log.get("F2") is g and log.count() == 2
    assert log.approve("F2", "rae").reviewer == "rae"
    closed = log.close("F2")
    assert closed.status == "closed" and closed.reviewer == "rae"
    kept = log.get("F1")
    assert kept is not None, "closing one flight dropped another from the log"
    assert kept.flight_id == "F1" and kept.status == "closed"
    assert kept.reviewer == "ken" and kept.pilot == "mira"
    assert kept.drone == "mavic-3" and kept.duration_min == 22
    assert log.count() == 2
"""
}

_C2_CONTRACT = {
    "raise": {
        "test_uploaded_missing.py": _C2_HELPER
        + """

def test_mark_uploaded_unknown_raises_keyerror(tmp_path):
    log, _ = _log(tmp_path)
    log.record("mira", "mavic-3", 22)
    with pytest.raises(KeyError):
        _uploaded(log)("F404", "9f3a")
"""
    },
    "none": {
        "test_uploaded_missing.py": _C2_HELPER
        + """

def test_mark_uploaded_unknown_returns_none_and_changes_nothing(tmp_path):
    log, path = _log(tmp_path)
    f = log.record("mira", "mavic-3", 22)
    before = path.read_text()
    assert _uploaded(log)("F404", "9f3a") is None
    assert path.read_text() == before
    assert log.count() == 1 and log.get(f.flight_id).status == "open"
"""
    },
}

_C2_SUPPORT = {
    "test_uploaded_errors.py": _C2_HELPER
    + """

def test_record_and_close_propagate_raw_oserror(tmp_path, monkeypatch):
    log, _ = _log(tmp_path)
    f = log.record("mira", "mavic-3", 22)
    monkeypatch.setattr(export, "append_json", _boom)
    with pytest.raises(OSError) as ei:
        log.record("jon", "mini-4", 9)
    assert ei.value is _ERR
    with pytest.raises(OSError) as ei:
        log.close(f.flight_id)
    assert ei.value is _ERR


def test_approve_propagates_raw_oserror(tmp_path, monkeypatch):
    log, _ = _log(tmp_path)
    f = log.record("mira", "mavic-3", 22)
    monkeypatch.setattr(export, "append_json", _boom)
    with pytest.raises(OSError) as ei:
        log.approve(f.flight_id, "ken")
    assert ei.value is _ERR


def test_mark_uploaded_propagates_raw_oserror(tmp_path, monkeypatch):
    log, _ = _log(tmp_path)
    f = log.record("mira", "mavic-3", 22)
    monkeypatch.setattr(export, "append_json", _boom)
    with pytest.raises(OSError) as ei:
        _uploaded(log)(f.flight_id, "9f3a")
    assert ei.value is _ERR
"""
}

_UPLOADED_RAISE = """
    def mark_uploaded(self, flight_id: str, checksum: str) -> Flight:
        flight = self._flights[flight_id]
        uploaded = flight.with_changes(status="uploaded")
        self._flights[flight_id] = uploaded
        export.append_json(self._export_path, {"event": "uploaded", "flight_id": flight_id, "checksum": checksum})
        return uploaded
"""

_UPLOADED_NONE = """
    def mark_uploaded(self, flight_id: str, checksum: str) -> Flight | None:
        flight = self._flights.get(flight_id)
        if flight is None:
            return None
        uploaded = flight.with_changes(status="uploaded")
        self._flights[flight_id] = uploaded
        export.append_json(self._export_path, {"event": "uploaded", "flight_id": flight_id, "checksum": checksum})
        return uploaded
"""


def _gold2(state: str) -> str:
    # Built on the checkpoint-1 gold under the state then in force (raise).
    body = _UPLOADED_RAISE if state == "raise" else _UPLOADED_NONE
    return _gold1("raise").replace("\n    def get(", body + "\n    def get(", 1)


_REQ2 = Request(
    text=(
        "Add a public method `mark_uploaded(flight_id, checksum)` on FlightLog that the "
        "ground-station sync calls for every flight id it reports from the upload folder: "
        'it sets the flight status to "uploaded", stores the updated flight, appends an '
        'export record {"event": "uploaded", "flight_id": ..., "checksum": ...} and '
        "returns the updated flight. The reviewer field is left as it is."
    ),
    target="flightlog/log.py",
    functional_tests=_C2_FUNCTIONAL,
    regression_tests=_C2_REGRESSION,
    contract_tests=_C2_CONTRACT,
    support_tests=_C2_SUPPORT,
    gold={"raise": _gold2("raise"), "none": _gold2("none")},
)

# ----------------------------------------------------------------- prefix (16 turns)

_PREFIX = [
    Turn(
        "user",
        "Our drone club has to keep a flight log for the insurer: every flight, who flew, "
        "which airframe, how long, and who reviewed it. Until now that has been a shared "
        "spreadsheet that three people edit at once and nobody trusts. I am writing a "
        "small `flightlog` package that the club laptop runs: a FlightLog in memory for "
        "the day, a Flight record, and a JSON-lines export file that the ground-station "
        "software picks up on its next sync. The ground station is a separate program we "
        "do not control; it tails the export file and pushes it to the club's cloud "
        "account overnight. A line in the export looks like:\n\n```\n"
        '{"event": "record", "flight_id": "F3", "pilot": "mira"}\n{"event": "close", '
        '"flight_id": "F3"}\n```\n\nCan you draft a README scope section? The committee '
        "will read it, and half of them think this is going to replace the ground "
        "station, which it is not. We fly two airframes, a Mavic 3 and a Mini 4, from "
        "one field, perhaps fifteen flights on a busy Sunday.",
    ),
    Turn(
        "assistant",
        "Here is a scope block that draws the line where you want it:\n\n```\n## Scope\n"
        "flightlog is the club's flight record. It keeps Flight entries in memory for the "
        "session and appends one JSON line per event to an export file that the ground "
        "station syncs. It does not talk to the drones, the ground station or the cloud, "
        "and it has no user accounts: whoever holds the laptop is the logger.\n\n## "
        "Non-goals\n- telemetry or GPS tracks\n- replacing the ground-station sync\n- "
        "multi-laptop editing\n```\n\nAnd the minimum usage so the committee can picture "
        "it:\n\n```python\nfrom flightlog.log import FlightLog\n\nlog = FlightLog("
        '"/home/club/export-2026-09.jsonl")\nf = log.record("mira", "mavic-3", 22)\n'
        "log.close(f.flight_id)\n```\n\nThe export path in the constructor means the "
        "sync software can be pointed at a new file per month without the package "
        "caring, and the JSON lines are plain enough that the insurer's auditor can read "
        "them with `grep` if it ever comes to that.",
    ),
    Turn(
        "user",
        'Question about the export records. I am writing `{"event": ..., "flight_id": '
        "...}` plus whatever the event needs, with `sort_keys=True` so the lines are "
        "stable. The ground-station vendor's docs say it accepts 'any JSON object per "
        "line with an event key', which is vague. Should I include the full flight in "
        "every record, or only the fields that changed? Full records make the file "
        "bigger, but the sync would then never need to look up earlier lines. Here is "
        "what a day currently produces:\n\n```\n"
        '{"event": "record", "flight_id": "F1", "pilot": "mira"}\n'
        '{"event": "record", "flight_id": "F2", "pilot": "jon"}\n'
        '{"event": "close", "flight_id": "F1"}\n'
        '{"event": "close", "flight_id": "F2"}\n```\n\nThe insurer only ever asks for '
        "totals per pilot per month, so I am not sure the extra fields buy anything, but "
        "I would rather decide once than change the format after the first sync.",
    ),
    Turn(
        "assistant",
        "Keep the records minimal: event, flight id, and the fields that event "
        "introduces. The export is a change log, not a snapshot, and the ground station "
        "already treats it as append-only; if it needed snapshots it would ask for them. "
        "The rule that keeps it consistent is that every field a record carries is one "
        "the event created or changed, so `record` carries the pilot, `close` carries "
        "nothing extra, and a future `approve` would carry the reviewer. That also makes "
        "the export trivially testable:\n\n```python\ndef test_close_record_is_minimal("
        'tmp_path):\n    path = tmp_path / "e.jsonl"\n    log = FlightLog(str(path))\n'
        '    log.close(log.record("mira", "mavic-3", 22).flight_id)\n    assert '
        'json.loads(path.read_text().splitlines()[-1]) == {"event": "close", '
        '"flight_id": "F1"}\n```\n\nIf the insurer ever wants durations in the export, '
        "add them to the `record` event, since that is where the duration is born, and "
        "the sync will simply see one more key on lines it already understands.",
    ),
    Turn(
        "user",
        "Here is my test file so far. Is reading the export file back in tests "
        "reasonable, or should I mock the export module?\n\n```python\nimport json\n\nfrom flightlog.log import FlightLog\n\n\n"
        "def test_record_mints_sequential_ids(tmp_path):\n    log = FlightLog(str("
        'tmp_path / "e.jsonl"))\n    assert log.record("mira", "mavic-3", 22).flight_id '
        '== "F1"\n    assert log.record("jon", "mini-4", 9).flight_id == "F2"\n\n\ndef '
        'test_record_writes_one_line(tmp_path):\n    path = tmp_path / "e.jsonl"\n    '
        'log = FlightLog(str(path))\n    log.record("mira", "mavic-3", 22)\n    lines = '
        "path.read_text().splitlines()\n    assert len(lines) == 1\n    assert json.loads("
        'lines[0])["event"] == "record"\n\n\ndef test_get_unknown_is_none(tmp_path):\n'
        '    assert FlightLog(str(tmp_path / "e.jsonl")).get("F7") is None\n```',
    ),
    Turn(
        "assistant",
        "Reading the file back is the right call: `export.append_json` is three lines "
        "and the thing you actually care about is what lands on disk for the sync, so a "
        "mock would test less than the real file does. Keep `tmp_path` per test. I would "
        "add one test that pins the close path end to end, since that is the operation "
        "the insurer's totals depend on:\n\n```python\ndef test_close_updates_record_and_"
        'export(tmp_path):\n    path = tmp_path / "e.jsonl"\n    log = FlightLog(str('
        'path))\n    f = log.record("mira", "mavic-3", 22)\n    assert log.close('
        'f.flight_id).status == "closed"\n    assert json.loads(path.read_text().'
        'splitlines()[-1])["event"] == "close"\n```\n\nMocking earns its keep only for '
        "the failure path, where you want the export to raise on demand; there a "
        "`monkeypatch.setattr(export, 'append_json', boom)` is cleaner than filling a "
        "disk.",
    ),
    Turn(
        "user",
        "Speaking of the failure path. Sunday the export file was on a USB stick the "
        "treasurer had mounted read-only, and the logger died with this while Jon was "
        "waiting to fly:\n\n```\nTraceback (most recent call last):\n  File "
        '"/home/club/run_logger.py", line 40, in <module>\n    flight = log.record('
        'pilot, drone, minutes)\n  File "/home/club/flightlog/log.py", line 17, in '
        "record\n    export.append_json(self._export_path, {...})\n  File "
        '"/home/club/flightlog/export.py", line 7, in append_json\n    with open(path, '
        '"a", encoding="utf-8") as fh:\nPermissionError: [Errno 13] Permission denied: '
        "'/media/stick/export.jsonl'\n```\n\nMy instinct is NOT to wrap this. The "
        "launcher already has a handler for OSError that remounts the stick and retries, "
        "and it keys on `errno`, so a package exception in between would just hide the "
        "number it needs. Is there an argument for wrapping that I am missing? The "
        "club has exactly one caller of this package and it is that launcher.",
    ),
    Turn(
        "assistant",
        "Not for this package. Wrapping helps when callers cannot reasonably know the "
        "lower layer exists; here the launcher owns the USB stick and the retry, and "
        "`errno` is exactly the information it acts on. A package exception would either "
        "re-expose errno, which is wrapping for its own sake, or lose it. So let the "
        "OSError propagate raw from every method that writes the export, document it in "
        "the README, and keep the launcher's handler as the one place that decides what "
        "to do:\n\n```python\ntry:\n    flight = log.record(pilot, drone, minutes)\n"
        "except OSError as exc:\n    if exc.errno in (errno.EACCES, errno.EROFS):\n"
        "        remount_stick()\n        flight = log.record(pilot, drone, minutes)\n"
        "    else:\n        raise\n```\n\nThe one thing to keep in mind is ordering: "
        "`record` mints the id and stores the flight before the export write, so a retry "
        "after a failed write must not mint a second id. Storing after the write, or "
        "accepting a duplicate id on the second attempt, is a decision for the launcher.",
    ),
    Turn(
        "user",
        "Agreed, and I want this as a stated convention: every public FlightLog method "
        "that writes the export lets any OSError from `export.append_json` propagate raw. "
        "No package exception class, no try/except in the log, no re-raising as "
        "something else. New methods follow that too.",
    ),
    Turn(
        "assistant",
        "Noted: OSError from the export layer propagates unchanged out of every public "
        "FlightLog method, existing and new. I will not add an exception class or wrap "
        "anything; the launcher's errno handler stays the single point of recovery.",
    ),
    Turn(
        "user",
        "Second convention, for unknown ids. Methods that act on a flight by id, like "
        "`close`, raise KeyError when the id is not in the log. A wrong id means the "
        "person at the laptop typed it wrong, and I want that to blow up in their face "
        "rather than silently do nothing. New methods that act on an id do the same.",
    ),
    Turn(
        "assistant",
        "Understood: id-keyed actions raise KeyError on an unknown flight id, matching "
        "`close`. New methods will index `self._flights[flight_id]` directly so the "
        "KeyError comes from the lookup itself, and nothing is stored or exported for "
        "an id that does not exist.",
    ),
    Turn(
        "user",
        "For later: the insurer wants monthly minutes per pilot. I imagine the launcher "
        "doing:\n\n```python\ndef monthly_minutes(log: FlightLog) -> dict[str, int]:\n"
        "    return log.minutes_by_pilot()\n```\n\nNot urgent, just want to be sure the "
        "Flight record has what that needs, and that we are not going to need a date on "
        "each flight to split months; the export file is already one file per month.",
    ),
    Turn(
        "assistant",
        "It does: `duration_min` and `pilot` are both on Flight, so `minutes_by_pilot` "
        "is a `Counter` summing `f.duration_min` per `f.pilot` over "
        "`self._flights.values()`. It reads only, so it never touches the export. The "
        "month split is free because the log lives one month per export file.",
    ),
    Turn(
        "user",
        "Right, let's get the safety officer's review working before Sunday. I will "
        "paste the current files with each request so you see the real state of the "
        "code rather than my memory of it.",
    ),
    Turn(
        "assistant",
        "Ready when you are. Send the request and I will return the full log module.",
    ),
]

_EVENT = (
    "One scoped exception to the unknown-id rule, effective now: methods that are called "
    "from the ground-station sync path (the sync feeds us whatever flight ids the ground "
    "station reports, including ids from other laptops that this log has never seen) "
    "return None on an unknown id and change nothing, no export line and no exception. "
    "Everything outside the sync path, including `close` and `approve`, keeps raising "
    "KeyError as before."
)


def build() -> Session:
    return Session(
        id="S39",
        project="flightlog",
        target_family="missing_record",
        support_family="error_surface",
        lifecycle="scope",
        files=_FILES,
        prefix=_PREFIX,
        states=("raise", "none"),
        state_at=("raise", "none"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10),
        tags={"support_state": "propagate", "scope": "ground-station sync path"},
    )
