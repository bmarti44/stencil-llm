# ruff: noqa: E501
"""S41: trail reports — missing_record (target, stable) x error_surface (support, propagate)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""trail_reports package: volunteer trail-condition reports."""\n'

_MODEL = '''"""Report records."""

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Report:
    report_id: str
    trail: str
    reporter: str
    condition: str
    status: str = "open"
    crew: str | None = None

    def with_changes(self, **changes) -> "Report":
        return replace(self, **changes)
'''

_FEED = '''"""Public feed file that the parks website reads."""


def publish(path: str, line: str) -> None:
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(line + "\\n")
'''

_BOARD = '''"""The report board."""

from trail_reports import feed
from trail_reports.model import Report


class ReportBoard:
    def __init__(self, feed_path: str) -> None:
        self._feed_path = feed_path
        self._reports: dict[str, Report] = {}
        self._counter = 0

    def file_report(self, trail: str, reporter: str, condition: str) -> Report:
        self._counter += 1
        report = Report(f"R{self._counter}", trail, reporter, condition)
        self._reports[report.report_id] = report
        feed.publish(self._feed_path, f"new {report.report_id} {trail}: {condition}")
        return report

    def close(self, report_id: str) -> Report | None:
        report = self._reports.get(report_id)
        if report is None:
            return None
        closed = report.with_changes(status="closed")
        self._reports[report_id] = closed
        feed.publish(self._feed_path, f"closed {report_id}")
        return closed

    def get(self, report_id: str) -> Report | None:
        return self._reports.get(report_id)

    def count(self) -> int:
        return len(self._reports)
'''

_FILES = {
    "trail_reports/__init__.py": _INIT,
    "trail_reports/model.py": _MODEL,
    "trail_reports/feed.py": _FEED,
    "trail_reports/board.py": _BOARD,
}

_HELPER_COMMON = """import pytest

from trail_reports import feed
from trail_reports.board import ReportBoard
from trail_reports.model import Report


def _board(tmp_path):
    path = tmp_path / "feed.txt"
    return ReportBoard(str(path)), path


_ERR = OSError(5, "Input/output error")


def _boom(path, line):
    raise _ERR
"""

# ----------------------------------------------------------------- checkpoint 1: assign_crew

_C1_HELPER = (
    _HELPER_COMMON
    + """

def _assign(board):
    fn = getattr(board, "assign_crew", None) or getattr(board, "assign", None)
    assert fn is not None, "no assign_crew method found"
    return fn
"""
)

_C1_FUNCTIONAL = {
    "test_assign_functional.py": _C1_HELPER
    + """

def test_assign_crew_sets_status_and_crew(tmp_path):
    b, _ = _board(tmp_path)
    r = b.file_report("ridge loop", "ines", "tree down at km 3")
    out = _assign(b)(r.report_id, "saturday crew")
    assert out.status == "assigned" and out.crew == "saturday crew"
    assert out.report_id == r.report_id and out.condition == "tree down at km 3"
    assert b.get(r.report_id).crew == "saturday crew"


def test_assign_crew_publishes_feed_line(tmp_path):
    b, path = _board(tmp_path)
    r = b.file_report("ridge loop", "ines", "tree down at km 3")
    _assign(b)(r.report_id, "saturday crew")
    lines = path.read_text().splitlines()
    assert lines[-1] == f"assigned {r.report_id} saturday crew" and len(lines) == 2


def test_assign_crew_leaves_other_reports_alone(tmp_path):
    b, _ = _board(tmp_path)
    a = b.file_report("ridge loop", "ines", "tree down")
    c = b.file_report("creek path", "omar", "washout")
    _assign(b)(a.report_id, "saturday crew")
    assert b.get(c.report_id).status == "open" and b.get(c.report_id).crew is None
    assert b.count() == 2
"""
}

_C1_REGRESSION = {
    "test_assign_regression.py": _HELPER_COMMON
    + """

def test_file_close_get_count_unchanged(tmp_path):
    b, path = _board(tmp_path)
    r = b.file_report("ridge loop", "ines", "tree down")
    assert r.report_id == "R1" and r.status == "open" and r.crew is None
    assert b.get("R1") is r and b.get("R9") is None
    assert b.close("R9") is None
    assert b.close("R1").status == "closed"
    assert b.get("R1").status == "closed"
    assert b.count() == 1
    assert path.read_text().splitlines() == ["new R1 ridge loop: tree down", "closed R1"]
"""
}

_C1_CONTRACT = {
    "none": {
        "test_assign_missing.py": _C1_HELPER
        + """

def test_assign_crew_unknown_returns_none_and_changes_nothing(tmp_path):
    b, path = _board(tmp_path)
    r = b.file_report("ridge loop", "ines", "tree down")
    before = path.read_text()
    assert _assign(b)("R404", "saturday crew") is None
    assert path.read_text() == before
    assert b.count() == 1 and b.get(r.report_id).status == "open"
"""
    },
    "raise": {
        "test_assign_missing.py": _C1_HELPER
        + """

def test_assign_crew_unknown_raises_keyerror(tmp_path):
    b, _ = _board(tmp_path)
    b.file_report("ridge loop", "ines", "tree down")
    with pytest.raises(KeyError):
        _assign(b)("R404", "saturday crew")
"""
    },
}

_C1_SUPPORT = {
    "test_assign_errors.py": _C1_HELPER
    + """

def test_file_report_propagates_raw_oserror(tmp_path, monkeypatch):
    b, _ = _board(tmp_path)
    monkeypatch.setattr(feed, "publish", _boom)
    with pytest.raises(OSError) as ei:
        b.file_report("ridge loop", "ines", "tree down")
    assert ei.value is _ERR


def test_close_propagates_raw_oserror(tmp_path, monkeypatch):
    b, _ = _board(tmp_path)
    r = b.file_report("ridge loop", "ines", "tree down")
    monkeypatch.setattr(feed, "publish", _boom)
    with pytest.raises(OSError) as ei:
        b.close(r.report_id)
    assert ei.value is _ERR


def test_assign_crew_propagates_raw_oserror(tmp_path, monkeypatch):
    b, _ = _board(tmp_path)
    r = b.file_report("ridge loop", "ines", "tree down")
    monkeypatch.setattr(feed, "publish", _boom)
    with pytest.raises(OSError) as ei:
        _assign(b)(r.report_id, "saturday crew")
    assert ei.value is _ERR
"""
}

_ASSIGN_NONE = """
    def assign_crew(self, report_id: str, crew: str) -> Report | None:
        report = self._reports.get(report_id)
        if report is None:
            return None
        assigned = report.with_changes(status="assigned", crew=crew)
        self._reports[report_id] = assigned
        feed.publish(self._feed_path, f"assigned {report_id} {crew}")
        return assigned
"""

_ASSIGN_RAISE = """
    def assign_crew(self, report_id: str, crew: str) -> Report:
        report = self._reports[report_id]
        assigned = report.with_changes(status="assigned", crew=crew)
        self._reports[report_id] = assigned
        feed.publish(self._feed_path, f"assigned {report_id} {crew}")
        return assigned
"""


def _gold1(state: str) -> str:
    body = _ASSIGN_NONE if state == "none" else _ASSIGN_RAISE
    return _BOARD.replace("\n    def get(", body + "\n    def get(", 1)


_REQ1 = Request(
    text=(
        "Add a public method `assign_crew(report_id, crew)` on ReportBoard for the "
        'coordinator: it sets the report status to "assigned", records the crew name on '
        "the report, stores the updated report, publishes the feed line "
        "`assigned <report_id> <crew>` and returns the updated report."
    ),
    target="trail_reports/board.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"none": _gold1("none"), "raise": _gold1("raise")},
)

# ----------------------------------------------------------------- checkpoint 2: reopen

_C2_HELPER = (
    _HELPER_COMMON
    + """

def _reopen(board):
    fn = getattr(board, "reopen", None) or getattr(board, "reopen_report", None)
    assert fn is not None, "no reopen method found"
    return fn
"""
)

_C2_FUNCTIONAL = {
    "test_reopen_functional.py": _C2_HELPER
    + """

def test_reopen_resets_status_condition_and_crew(tmp_path):
    b, _ = _board(tmp_path)
    r = b.file_report("ridge loop", "ines", "tree down")
    b.assign_crew(r.report_id, "saturday crew")
    b.close(r.report_id)
    out = _reopen(b)(r.report_id, "tree back across the trail")
    assert out.status == "open" and out.crew is None
    assert out.condition == "tree back across the trail"
    assert out.report_id == r.report_id and out.reporter == "ines"
    assert b.get(r.report_id).status == "open"


def test_reopen_publishes_feed_line(tmp_path):
    b, path = _board(tmp_path)
    r = b.file_report("ridge loop", "ines", "tree down")
    b.close(r.report_id)
    _reopen(b)(r.report_id, "tree back")
    lines = path.read_text().splitlines()
    assert lines[-1] == f"reopened {r.report_id}: tree back" and len(lines) == 3


def test_reopen_leaves_other_reports_alone(tmp_path):
    b, _ = _board(tmp_path)
    a = b.file_report("ridge loop", "ines", "tree down")
    c = b.file_report("creek path", "omar", "washout")
    b.close(a.report_id)
    _reopen(b)(a.report_id, "again")
    assert b.get(c.report_id).status == "open" and b.count() == 2
"""
}

_C2_REGRESSION = {
    "test_reopen_regression.py": _HELPER_COMMON
    + """

def test_file_close_assign_get_unchanged(tmp_path):
    b, path = _board(tmp_path)
    r = b.file_report("ridge loop", "ines", "tree down")
    assert b.get("R1") is r and b.get("R9") is None
    assert b.assign_crew("R1", "saturday crew").crew == "saturday crew"
    assert b.assign_crew("R9", "saturday crew") is None
    assert b.close("R9") is None
    assert b.close("R1").status == "closed"
    assert b.get("R1").status == "closed"
    assert b.count() == 1
    assert path.read_text().splitlines() == [
        "new R1 ridge loop: tree down",
        "assigned R1 saturday crew",
        "closed R1",
    ]
"""
}

_C2_CONTRACT = {
    "none": {
        "test_reopen_missing.py": _C2_HELPER
        + """

def test_reopen_unknown_returns_none_and_changes_nothing(tmp_path):
    b, path = _board(tmp_path)
    r = b.file_report("ridge loop", "ines", "tree down")
    before = path.read_text()
    assert _reopen(b)("R404", "again") is None
    assert path.read_text() == before
    assert b.count() == 1 and b.get(r.report_id).condition == "tree down"
"""
    },
    "raise": {
        "test_reopen_missing.py": _C2_HELPER
        + """

def test_reopen_unknown_raises_keyerror(tmp_path):
    b, _ = _board(tmp_path)
    b.file_report("ridge loop", "ines", "tree down")
    with pytest.raises(KeyError):
        _reopen(b)("R404", "again")
"""
    },
}

_C2_SUPPORT = {
    "test_reopen_errors.py": _C2_HELPER
    + """

def test_file_report_and_close_propagate_raw_oserror(tmp_path, monkeypatch):
    b, _ = _board(tmp_path)
    r = b.file_report("ridge loop", "ines", "tree down")
    monkeypatch.setattr(feed, "publish", _boom)
    with pytest.raises(OSError) as ei:
        b.file_report("creek path", "omar", "washout")
    assert ei.value is _ERR
    with pytest.raises(OSError) as ei:
        b.close(r.report_id)
    assert ei.value is _ERR


def test_assign_crew_propagates_raw_oserror(tmp_path, monkeypatch):
    b, _ = _board(tmp_path)
    r = b.file_report("ridge loop", "ines", "tree down")
    monkeypatch.setattr(feed, "publish", _boom)
    with pytest.raises(OSError) as ei:
        b.assign_crew(r.report_id, "saturday crew")
    assert ei.value is _ERR


def test_reopen_propagates_raw_oserror(tmp_path, monkeypatch):
    b, _ = _board(tmp_path)
    r = b.file_report("ridge loop", "ines", "tree down")
    b.close(r.report_id)
    monkeypatch.setattr(feed, "publish", _boom)
    with pytest.raises(OSError) as ei:
        _reopen(b)(r.report_id, "again")
    assert ei.value is _ERR
"""
}

_REOPEN_NONE = """
    def reopen(self, report_id: str, condition: str) -> Report | None:
        report = self._reports.get(report_id)
        if report is None:
            return None
        reopened = report.with_changes(status="open", condition=condition, crew=None)
        self._reports[report_id] = reopened
        feed.publish(self._feed_path, f"reopened {report_id}: {condition}")
        return reopened
"""

_REOPEN_RAISE = """
    def reopen(self, report_id: str, condition: str) -> Report:
        report = self._reports[report_id]
        reopened = report.with_changes(status="open", condition=condition, crew=None)
        self._reports[report_id] = reopened
        feed.publish(self._feed_path, f"reopened {report_id}: {condition}")
        return reopened
"""


def _gold2(state: str) -> str:
    # Built on the checkpoint-1 gold under the state then in force (none).
    body = _REOPEN_NONE if state == "none" else _REOPEN_RAISE
    return _gold1("none").replace("\n    def get(", body + "\n    def get(", 1)


_REQ2 = Request(
    text=(
        "Add a public method `reopen(report_id, condition)` on ReportBoard for when a "
        'closed problem comes back: it sets the report status to "open", replaces the '
        "condition text with the new one, clears the crew (back to None), stores the "
        "updated report, publishes the feed line `reopened <report_id>: <condition>` and "
        "returns the updated report."
    ),
    target="trail_reports/board.py",
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
        "I coordinate volunteer trail maintenance for a county park: hikers report a "
        "tree down or a washout, I match the report to a Saturday crew, and the parks "
        "office wants the public to see what is open and what is being worked on. Right "
        "now that is a WhatsApp group and my memory. I am writing a small "
        "`trail_reports` package: a ReportBoard in memory, a Report record, and a plain "
        "feed file that the parks website already knows how to read, one line per "
        "event, newest at the bottom. The website's include is dumb, it literally shows "
        "the last twenty lines:\n\n```\nnew R1 ridge loop: tree down at km 3\nnew R2 "
        "creek path: washout below the footbridge\nclosed R1\n```\n\nCan you draft the "
        "README scope section? The parks office thinks this is going to be an app with "
        "a map and photos, and the volunteers think it is a rota. It is neither, and I "
        "would like the first paragraph to make that clear before the next meeting. "
        "Volume is maybe five reports a week in summer and none in January.",
    ),
    Turn(
        "assistant",
        "A scope block that sets both expectations:\n\n```\n## Scope\ntrail_reports "
        "keeps the list of reported trail problems and what the volunteer crews are "
        "doing about them. It holds Report records in memory for the running process "
        "and appends one plain line per event to a feed file the parks website "
        "displays. It has no map, no photos, no accounts and no rota; crews are just a "
        "name on a report.\n\n## Non-goals\n- maps or GPS\n- photo uploads\n- "
        "scheduling volunteers\n```\n\nAnd the usage block for the README:\n\n```python\n"
        "from trail_reports.board import ReportBoard\n\nboard = ReportBoard("
        '"/var/www/trails/feed.txt")\nr = board.file_report("ridge loop", "ines", '
        '"tree down at km 3")\nboard.close(r.report_id)\n```\n\nPassing the feed path '
        "in means the website's include never changes and you can point tests at a "
        "temporary file. The runner the parks office already has can call these "
        "three methods from a cron job or a tiny form; nothing else is needed for "
        "the first season, and the non-goals list is what people will actually read.",
    ),
    Turn(
        "user",
        "Feed line format: I went with `<event> <id> [rest]`, and the free text after "
        "the colon is whatever the reporter typed. The parks office wants to know if "
        "the trail name should be on every line so a reader of the last twenty lines "
        "can tell what `closed R1` refers to without scrolling. Here is a realistic "
        "week:\n\n```\nnew R1 ridge loop: tree down at km 3\nnew R2 creek path: washout "
        "below the footbridge\nnew R3 ridge loop: loose steps at the overlook\nclosed "
        "R1\nclosed R3\n```\n\nRepeating the trail on `closed` lines is easy, but then "
        "every future event line needs it too and the format stops being minimal. Is "
        "there a sensible rule for what goes on a line, or is this a taste question? "
        "I would like to settle it now because the include is cached by the website "
        "for an hour and reformatting old lines later is not an option. "
        "The reporters are hikers, so the free text after the colon can be anything "
        "from 'muddy' to three sentences about a bridge.",
    ),
    Turn(
        "assistant",
        "There is a rule that answers it and keeps the format minimal: a line carries "
        "the event, the id, and only the fields that event introduced or changed. `new` "
        "carries trail and condition because that is where they are born; `closed` "
        "carries nothing extra because nothing but the status changed. If the website "
        "wants trail names on every line, that is a rendering concern, and the include "
        "can be replaced by a tiny script that joins on the id. The rule also makes the "
        "format testable one line at a time:\n\n```python\ndef test_closed_line_is_bare("
        'tmp_path):\n    path = tmp_path / "feed.txt"\n    b = ReportBoard(str(path))\n'
        '    b.close(b.file_report("ridge loop", "ines", "tree down").report_id)\n    '
        'assert path.read_text().splitlines()[-1] == "closed R1"\n```\n\nA future '
        "`assigned` line would carry the crew name, since that is what it changes, and "
        "a `reopened` line would carry the new condition text for the same reason. "
        "Free text stays after the colon so a reader can always split on the first one.",
    ),
    Turn(
        "user",
        "Here is my test file so far. I want to know whether reading the feed file back "
        "in tests is fine or whether I should mock `feed.publish`:\n\n```python\nfrom "
        "trail_reports.board import ReportBoard\n\n\ndef test_file_report_mints_"
        'sequential_ids(tmp_path):\n    b = ReportBoard(str(tmp_path / "feed.txt"))\n'
        '    assert b.file_report("ridge loop", "ines", "tree down").report_id == "R1"\n'
        '    assert b.file_report("creek path", "omar", "washout").report_id == "R2"\n\n'
        "\ndef test_file_report_writes_one_line(tmp_path):\n    path = tmp_path / "
        '"feed.txt"\n    b = ReportBoard(str(path))\n    b.file_report("ridge loop", '
        '"ines", "tree down")\n    assert path.read_text().splitlines() == ["new R1 '
        'ridge loop: tree down"]\n\n\ndef test_get_unknown_is_none(tmp_path):\n    '
        'assert ReportBoard(str(tmp_path / "feed.txt")).get("R7") is None\n```\n\nThe '
        "parks IT person suggested mocking everything, which I am reluctant to do.",
    ),
    Turn(
        "assistant",
        "Read the real file. `feed.publish` is three lines and what matters is the "
        "bytes the website will show; a mock would only prove the mock was called. "
        "Keep `tmp_path` so each test starts with an empty feed. I would add one "
        "end-to-end test for close, since that is the event the public watches "
        "for:\n\n```python\ndef test_close_updates_record_and_feed(tmp_path):\n    path "
        '= tmp_path / "feed.txt"\n    b = ReportBoard(str(path))\n    r = b.file_report('
        '"ridge loop", "ines", "tree down")\n    assert b.close(r.report_id).status == '
        '"closed"\n    assert path.read_text().splitlines()[-1] == "closed R1"\n```\n\n'
        "Mocking is for the failure path only, where you want `publish` to raise on "
        "demand: `monkeypatch.setattr(feed, 'publish', boom)` does that cleanly, and "
        "because the board imports the module rather than the function, the patch is "
        "seen by every method without any test-only hooks in the board. "
        "Keep the mock tests in their own file so the format tests stay readable.",
    ),
    Turn(
        "user",
        "About that failure path. On Sunday the web server's disk filled up and the "
        "board crashed with this from the little runner script the parks office "
        'uses:\n\n```\nTraceback (most recent call last):\n  File "/opt/trails/'
        'runner.py", line 44, in <module>\n    board.close(report_id)\n  File "/opt/'
        'trails/trail_reports/board.py", line 25, in close\n    feed.publish(self.'
        '_feed_path, f"closed {report_id}")\n  File "/opt/trails/trail_reports/feed.py", '
        'line 6, in publish\n    fh.write(line + "\\n")\nOSError: [Errno 28] No space '
        "left on device\n```\n\nThe parks IT person actually liked this: their runner "
        "already catches OSError, checks `errno`, and pages the on-call when it is "
        "ENOSPC. They asked me NOT to wrap it in a custom exception because their "
        "handler would stop matching. Is there any reason to overrule them? My only "
        "worry is that volunteers running the board on their own laptop will see a "
        "bare traceback, but they are not the audience for this package.",
    ),
    Turn(
        "assistant",
        "No. Their handler is the one place in the system that knows what to do with a "
        "disk-full, and it keys on `errno`, which a wrapper would either hide or have to "
        "re-expose. The package has one caller and that caller wants the raw OSError, so "
        "let it propagate from every method that writes the feed and say so in the "
        "README. Their runner stays as it is:\n\n```python\ntry:\n    board.close("
        "report_id)\nexcept OSError as exc:\n    if exc.errno == errno.ENOSPC:\n        "
        "page_on_call('trails feed disk full')\n    raise\n```\n\nOne ordering note: "
        "`close` stores the updated report before publishing, so after a failed write "
        "the board says closed and the feed does not. For a public feed that is the "
        "safer direction, since the website under-reports rather than shows a closure "
        "that never happened in the board. If the runner retries `close` after the "
        "page, the second call finds the report already closed and simply publishes "
        "the line, which is exactly the recovery you want. "
        "Say so in the README next to the propagate note so nobody adds a wrapper later.",
    ),
    Turn(
        "user",
        "Agreed, and I want it as a stated convention: every public ReportBoard method "
        "that writes the feed lets any OSError from `feed.publish` propagate raw. No "
        "package exception class, no try/except in the board, no re-raising as "
        "something else. New methods follow that too.",
    ),
    Turn(
        "assistant",
        "Noted: OSError from the feed layer propagates unchanged out of every public "
        "ReportBoard method, existing and new. No exception class, no wrapping; the "
        "runner's errno handler remains the single point of recovery.",
    ),
    Turn(
        "user",
        "Second convention, for unknown ids. Methods that act on a report by id, like "
        "`close`, return None when the id is not on the board and change nothing: no "
        "feed line, no exception. Volunteers read ids off a whiteboard photo and get "
        "them wrong constantly; the runner prints 'no such report' and moves on. New "
        "methods that act on an id do the same.",
    ),
    Turn(
        "assistant",
        "Understood: id-keyed actions return None on an unknown report id and leave "
        "both the board and the feed untouched, matching `close`. New methods will look "
        "up with `self._reports.get(report_id)` and return None before any write.",
    ),
    Turn(
        "user",
        "For later: the parks office would like a count of open reports per trail on "
        "the website. I imagine the runner doing:\n\n```python\nfor trail, n in "
        'board.open_by_trail().items():\n    print(f"{trail}: {n} open")\n```\n\nNot '
        "now, just want to be sure the Report record has what that needs. The parks "
        "office would also like the oldest open report per trail, for nagging "
        "the crews, and I assume that is a read too.",
    ),
    Turn(
        "assistant",
        "It does: `trail` and `status` are both on Report, so `open_by_trail` is a "
        "`Counter` over `r.trail` for reports with `status == 'open'`. It only reads, "
        "so it never touches the feed. Oldest open per trail is a `min` over the same "
        "filter keyed on the sequential id, since ids are minted in filing order.",
    ),
    Turn(
        "user",
        "Right, let's get crew assignment working before Saturday. I will paste the "
        "current files with each request so you see the real state of the code rather "
        "than my memory of it.",
    ),
    Turn(
        "assistant",
        "Ready when you are. Send the request and I will return the full board module.",
    ),
]

_EVENT = (
    "Small update from the parks office, nothing that changes the code: the feed file "
    "stays at /var/www/trails/feed.txt for the rest of the season, the Saturday crew "
    "has a new lead called Sam, and the website include will start showing the last "
    "thirty lines instead of twenty from next week."
)


def build() -> Session:
    return Session(
        id="S41",
        project="trail_reports",
        target_family="missing_record",
        support_family="error_surface",
        lifecycle="stable",
        files=_FILES,
        prefix=_PREFIX,
        states=("none", "raise"),
        state_at=("none", "none"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10),
        tags={"support_state": "propagate"},
    )
