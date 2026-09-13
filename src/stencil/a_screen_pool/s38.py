# ruff: noqa: E501
"""S38: museum tickets — missing_record (target, replacement) x error_surface (support, wrap)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '''"""museum_tickets package."""


class TicketsError(Exception):
    """Raised when the ticket journal cannot be written."""
'''

_MODEL = '''"""Ticket records."""

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Ticket:
    ticket_id: str
    holder: str
    exhibition: str
    status: str = "issued"

    def with_status(self, status: str) -> "Ticket":
        return replace(self, status=status)
'''

_JOURNAL = '''"""Append-only text journal for the treasurer."""


def append_line(path: str, line: str) -> None:
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(line + "\\n")
'''

_DESK = '''"""Front-desk ticket operations."""

from museum_tickets import TicketsError, journal
from museum_tickets.model import Ticket


class TicketDesk:
    def __init__(self, journal_path: str) -> None:
        self._journal_path = journal_path
        self._tickets: dict[str, Ticket] = {}
        self._counter = 0

    def issue(self, holder: str, exhibition: str) -> Ticket:
        self._counter += 1
        ticket = Ticket(ticket_id=f"M{self._counter}", holder=holder, exhibition=exhibition)
        self._tickets[ticket.ticket_id] = ticket
        self._record(f"issue {ticket.ticket_id} {exhibition}")
        return ticket

    def void(self, ticket_id: str) -> Ticket | None:
        ticket = self._tickets.get(ticket_id)
        if ticket is None:
            return None
        voided = ticket.with_status("void")
        self._tickets[ticket_id] = voided
        self._record(f"void {ticket_id}")
        return voided

    def lookup(self, ticket_id: str) -> Ticket | None:
        return self._tickets.get(ticket_id)

    def count(self) -> int:
        return len(self._tickets)

    def _record(self, line: str) -> None:
        try:
            journal.append_line(self._journal_path, line)
        except OSError as exc:
            raise TicketsError(f"journal write failed: {exc}") from exc
'''

_FILES = {
    "museum_tickets/__init__.py": _INIT,
    "museum_tickets/model.py": _MODEL,
    "museum_tickets/journal.py": _JOURNAL,
    "museum_tickets/desk.py": _DESK,
}

# ----------------------------------------------------------------- checkpoint 1: admit

_C1_HELPER = """import pytest

from museum_tickets import TicketsError, journal
from museum_tickets.model import Ticket
from museum_tickets.desk import TicketDesk


def _admit(desk):
    fn = getattr(desk, "admit", None) or getattr(desk, "admit_ticket", None)
    assert fn is not None, "no admit method found"
    return fn


def _desk(tmp_path):
    return TicketDesk(str(tmp_path / "journal.log")), tmp_path / "journal.log"
"""

_C1_FUNCTIONAL = {
    "test_admit_functional.py": _C1_HELPER
    + """

def test_admit_sets_status_and_stores(tmp_path):
    d, _ = _desk(tmp_path)
    t = d.issue("ana", "bronze age")
    out = _admit(d)(t.ticket_id)
    assert out.status == "admitted"
    assert out.ticket_id == t.ticket_id and out.holder == "ana"
    assert d.lookup(t.ticket_id).status == "admitted"


def test_admit_appends_journal_line(tmp_path):
    d, path = _desk(tmp_path)
    t = d.issue("ana", "bronze age")
    _admit(d)(t.ticket_id)
    lines = path.read_text().splitlines()
    assert lines[-1] == f"admit {t.ticket_id}"
    assert len(lines) == 2


def test_admit_does_not_touch_other_tickets(tmp_path):
    d, _ = _desk(tmp_path)
    a = d.issue("ana", "bronze age")
    b = d.issue("bo", "maps")
    _admit(d)(a.ticket_id)
    assert d.lookup(b.ticket_id).status == "issued"
    assert d.count() == 2
    assert d.lookup(b.ticket_id) == b
    assert d.lookup(b.ticket_id).holder == "bo"
    assert d.lookup(b.ticket_id).exhibition == "maps"


def test_admit_keeps_a_voided_neighbour_and_the_count(tmp_path):
    # the neighbour carries a NON-DEFAULT status ("void" rather than the
    # "issued" default), so an update that rewrites or drops unrelated
    # records is visible through the desk's own reader
    d, path = _desk(tmp_path)
    a = d.issue("ana", "bronze age")
    b = d.issue("bo", "maps")
    d.void(b.ticket_id)
    out = _admit(d)(a.ticket_id)
    assert out.status == "admitted"
    kept = d.lookup(b.ticket_id)
    assert kept is not None and kept.status == "void"
    assert kept.holder == "bo" and kept.exhibition == "maps"
    assert d.lookup(a.ticket_id).status == "admitted"
    assert d.lookup(a.ticket_id).holder == "ana"
    assert d.count() == 2
    assert path.read_text().splitlines() == [
        "issue M1 bronze age",
        "issue M2 maps",
        "void M2",
        "admit M1",
    ]
"""
}

_C1_REGRESSION = {
    "test_admit_regression.py": """from museum_tickets.desk import TicketDesk


def test_issue_lookup_void_count_unchanged(tmp_path):
    path = tmp_path / "j.log"
    d = TicketDesk(str(path))
    t = d.issue("ana", "bronze age")
    assert t.ticket_id == "M1" and t.status == "issued"
    assert d.lookup("M1") is t and d.lookup("M9") is None
    assert d.void("M9") is None
    assert d.void("M1").status == "void"
    assert d.lookup("M1").status == "void"
    assert d.count() == 1
    assert path.read_text().splitlines() == ["issue M1 bronze age", "void M1"]


def test_void_keeps_the_other_tickets_and_the_count(tmp_path):
    # two tickets; the one left alone carries a NON-DEFAULT status
    path = tmp_path / "two.log"
    d = TicketDesk(str(path))
    a = d.issue("ana", "bronze age")
    b = d.issue("bo", "maps")
    assert d.void(a.ticket_id).status == "void"
    assert d.void(b.ticket_id).status == "void"
    kept = d.lookup(a.ticket_id)
    assert kept is not None and kept.status == "void"
    assert kept.holder == "ana" and kept.exhibition == "bronze age"
    assert d.lookup(b.ticket_id).status == "void"
    assert d.lookup(b.ticket_id).holder == "bo"
    assert d.count() == 2
    assert path.read_text().splitlines() == [
        "issue M1 bronze age",
        "issue M2 maps",
        "void M1",
        "void M2",
    ]
"""
}

_C1_CONTRACT = {
    "none": {
        "test_admit_missing.py": _C1_HELPER
        + """

def test_admit_unknown_returns_none_and_changes_nothing(tmp_path):
    d, path = _desk(tmp_path)
    t = d.issue("ana", "bronze age")
    before = path.read_text()
    assert _admit(d)("M404") is None
    assert path.read_text() == before
    assert d.count() == 1 and d.lookup(t.ticket_id).status == "issued"
"""
    },
    "raise": {
        "test_admit_missing.py": _C1_HELPER
        + """

def test_admit_unknown_raises_keyerror(tmp_path):
    d, _ = _desk(tmp_path)
    d.issue("ana", "bronze age")
    with pytest.raises(KeyError):
        _admit(d)("M404")
"""
    },
}

_C1_SUPPORT = {
    "test_admit_errors.py": _C1_HELPER
    + """

def _broken(path, line):
    raise OSError(28, "No space left on device")


def test_issue_wraps_journal_oserror(tmp_path, monkeypatch):
    d, _ = _desk(tmp_path)
    monkeypatch.setattr(journal, "append_line", _broken)
    with pytest.raises(TicketsError) as ei:
        d.issue("ana", "bronze age")
    assert isinstance(ei.value.__cause__, OSError)


def test_void_wraps_journal_oserror(tmp_path, monkeypatch):
    d, _ = _desk(tmp_path)
    t = d.issue("ana", "bronze age")
    monkeypatch.setattr(journal, "append_line", _broken)
    with pytest.raises(TicketsError):
        d.void(t.ticket_id)


def test_admit_wraps_journal_oserror(tmp_path, monkeypatch):
    d, _ = _desk(tmp_path)
    t = d.issue("ana", "bronze age")
    monkeypatch.setattr(journal, "append_line", _broken)
    with pytest.raises(TicketsError) as ei:
        _admit(d)(t.ticket_id)
    assert isinstance(ei.value.__cause__, OSError)
"""
}

_ADMIT_NONE = """
    def admit(self, ticket_id: str) -> Ticket | None:
        ticket = self._tickets.get(ticket_id)
        if ticket is None:
            return None
        admitted = ticket.with_status("admitted")
        self._tickets[ticket_id] = admitted
        self._record(f"admit {ticket_id}")
        return admitted
"""

_ADMIT_RAISE = """
    def admit(self, ticket_id: str) -> Ticket:
        ticket = self._tickets[ticket_id]
        admitted = ticket.with_status("admitted")
        self._tickets[ticket_id] = admitted
        self._record(f"admit {ticket_id}")
        return admitted
"""


def _gold1(state: str) -> str:
    body = _ADMIT_NONE if state == "none" else _ADMIT_RAISE
    return _DESK.replace("\n    def lookup(", body + "\n    def lookup(", 1)


_REQ1 = Request(
    text=(
        "Add a public method `admit(ticket_id)` on TicketDesk for the door scanner: it "
        'sets the ticket status to "admitted", stores the updated ticket, appends the '
        "journal line `admit <ticket_id>` and returns the updated ticket."
    ),
    target="museum_tickets/desk.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"none": _gold1("none"), "raise": _gold1("raise")},
)

# ----------------------------------------------------------------- checkpoint 2: refund

_C2_HELPER = """import pytest

from museum_tickets import TicketsError, journal
from museum_tickets.model import Ticket
from museum_tickets.desk import TicketDesk


def _refund(desk):
    fn = getattr(desk, "refund", None) or getattr(desk, "refund_ticket", None)
    assert fn is not None, "no refund method found"
    return fn


def _desk(tmp_path):
    return TicketDesk(str(tmp_path / "journal.log")), tmp_path / "journal.log"
"""

_C2_FUNCTIONAL = {
    "test_refund_functional.py": _C2_HELPER
    + """

def test_refund_sets_status_and_stores(tmp_path):
    d, _ = _desk(tmp_path)
    t = d.issue("ana", "bronze age")
    out = _refund(d)(t.ticket_id)
    assert out.status == "refunded"
    assert out.ticket_id == t.ticket_id and out.exhibition == "bronze age"
    assert d.lookup(t.ticket_id).status == "refunded"


def test_refund_appends_journal_line(tmp_path):
    d, path = _desk(tmp_path)
    t = d.issue("ana", "bronze age")
    _refund(d)(t.ticket_id)
    lines = path.read_text().splitlines()
    assert lines[-1] == f"refund {t.ticket_id}"
    assert len(lines) == 2


def test_refund_leaves_other_tickets_alone(tmp_path):
    d, _ = _desk(tmp_path)
    a = d.issue("ana", "bronze age")
    b = d.issue("bo", "maps")
    _refund(d)(b.ticket_id)
    assert d.lookup(a.ticket_id).status == "issued"
    assert d.count() == 2
    assert d.lookup(a.ticket_id) == a
    assert d.lookup(a.ticket_id).holder == "ana"
    assert d.lookup(a.ticket_id).exhibition == "bronze age"


def test_refund_keeps_an_admitted_neighbour_and_the_count(tmp_path):
    # the neighbour carries a NON-DEFAULT status ("admitted" rather than
    # the "issued" default), so an update that rewrites or drops unrelated
    # records is visible through the desk's own reader
    d, path = _desk(tmp_path)
    a = d.issue("ana", "bronze age")
    b = d.issue("bo", "maps")
    d.admit(a.ticket_id)
    out = _refund(d)(b.ticket_id)
    assert out.status == "refunded"
    kept = d.lookup(a.ticket_id)
    assert kept is not None and kept.status == "admitted"
    assert kept.holder == "ana" and kept.exhibition == "bronze age"
    assert d.lookup(b.ticket_id).status == "refunded"
    assert d.lookup(b.ticket_id).holder == "bo"
    assert d.count() == 2
    assert path.read_text().splitlines() == [
        "issue M1 bronze age",
        "issue M2 maps",
        "admit M1",
        "refund M2",
    ]
"""
}

_C2_REGRESSION = {
    "test_refund_regression.py": """from museum_tickets.desk import TicketDesk


def test_issue_lookup_void_admit_unchanged(tmp_path):
    path = tmp_path / "j.log"
    d = TicketDesk(str(path))
    t = d.issue("ana", "bronze age")
    assert d.lookup("M1") is t and d.lookup("M9") is None
    assert d.void("M9") is None
    assert d.admit("M1").status == "admitted"
    assert d.admit("M9") is None
    assert d.void("M1").status == "void"
    assert d.lookup("M1").status == "void"
    assert d.count() == 1
    assert path.read_text().splitlines() == ["issue M1 bronze age", "admit M1", "void M1"]


def test_void_and_admit_keep_the_other_tickets(tmp_path):
    # two tickets; the one left alone carries a NON-DEFAULT status
    path = tmp_path / "two.log"
    d = TicketDesk(str(path))
    a = d.issue("ana", "bronze age")
    b = d.issue("bo", "maps")
    assert d.admit(a.ticket_id).status == "admitted"
    assert d.void(b.ticket_id).status == "void"
    kept = d.lookup(a.ticket_id)
    assert kept is not None and kept.status == "admitted"
    assert kept.holder == "ana" and kept.exhibition == "bronze age"
    assert d.lookup(b.ticket_id).status == "void"
    assert d.lookup(b.ticket_id).holder == "bo"
    assert d.count() == 2
    assert path.read_text().splitlines() == [
        "issue M1 bronze age",
        "issue M2 maps",
        "admit M1",
        "void M2",
    ]
"""
}

_C2_CONTRACT = {
    "none": {
        "test_refund_missing.py": _C2_HELPER
        + """

def test_refund_unknown_returns_none_and_changes_nothing(tmp_path):
    d, path = _desk(tmp_path)
    t = d.issue("ana", "bronze age")
    before = path.read_text()
    assert _refund(d)("M404") is None
    assert path.read_text() == before
    assert d.count() == 1 and d.lookup(t.ticket_id).status == "issued"
"""
    },
    "raise": {
        "test_refund_missing.py": _C2_HELPER
        + """

def test_refund_unknown_raises_keyerror(tmp_path):
    d, _ = _desk(tmp_path)
    d.issue("ana", "bronze age")
    with pytest.raises(KeyError):
        _refund(d)("M404")
"""
    },
}

_C2_SUPPORT = {
    "test_refund_errors.py": _C2_HELPER
    + """

def _broken(path, line):
    raise OSError(28, "No space left on device")


def test_issue_and_void_wrap_journal_oserror(tmp_path, monkeypatch):
    d, _ = _desk(tmp_path)
    t = d.issue("ana", "bronze age")
    monkeypatch.setattr(journal, "append_line", _broken)
    with pytest.raises(TicketsError):
        d.issue("bo", "maps")
    with pytest.raises(TicketsError):
        d.void(t.ticket_id)


def test_admit_wraps_journal_oserror(tmp_path, monkeypatch):
    d, _ = _desk(tmp_path)
    t = d.issue("ana", "bronze age")
    monkeypatch.setattr(journal, "append_line", _broken)
    with pytest.raises(TicketsError):
        d.admit(t.ticket_id)


def test_refund_wraps_journal_oserror(tmp_path, monkeypatch):
    d, _ = _desk(tmp_path)
    t = d.issue("ana", "bronze age")
    monkeypatch.setattr(journal, "append_line", _broken)
    with pytest.raises(TicketsError) as ei:
        _refund(d)(t.ticket_id)
    assert isinstance(ei.value.__cause__, OSError)
"""
}

_REFUND_NONE = """
    def refund(self, ticket_id: str) -> Ticket | None:
        ticket = self._tickets.get(ticket_id)
        if ticket is None:
            return None
        refunded = ticket.with_status("refunded")
        self._tickets[ticket_id] = refunded
        self._record(f"refund {ticket_id}")
        return refunded
"""

_REFUND_RAISE = """
    def refund(self, ticket_id: str) -> Ticket:
        ticket = self._tickets[ticket_id]
        refunded = ticket.with_status("refunded")
        self._tickets[ticket_id] = refunded
        self._record(f"refund {ticket_id}")
        return refunded
"""


def _gold2(state: str) -> str:
    # Built on the checkpoint-1 gold under the state then in force (none).
    body = _REFUND_NONE if state == "none" else _REFUND_RAISE
    return _gold1("none").replace("\n    def lookup(", body + "\n    def lookup(", 1)


_REQ2 = Request(
    text=(
        "Add a public method `refund(ticket_id)` on TicketDesk for the cash desk: it sets "
        'the ticket status to "refunded", stores the updated ticket, appends the journal '
        "line `refund <ticket_id>` and returns the updated ticket."
    ),
    target="museum_tickets/desk.py",
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
        "I volunteer at a small local museum, two rooms and a rotating exhibition, and "
        "the front desk still sells tickets out of a paper book. The treasurer wants a "
        "line-by-line record she can reconcile against the cash box at month end, so I am "
        "writing a tiny `museum_tickets` package: a TicketDesk that mints ticket ids, a "
        "Ticket record and an append-only journal file that every ticket action writes a "
        "line to. No database, no web app, it runs on the old laptop at the desk. The "
        "journal is just text, one line per action, so she can open it in Notepad:\n\n"
        "```\nissue M1 bronze age\nissue M2 bronze age\nvoid M2\nissue M3 maps\n```\n\n"
        "Can you draft the README scope section so the other volunteers know what this "
        "is and is not? Two of them keep asking whether it will take card payments, and "
        "the answer is no, the card terminal is a separate device, we only record that a "
        "ticket was issued. The exhibitions this season are the bronze age hoard and the "
        "old county maps, so there are only ever two or three exhibition names in play.",
    ),
    Turn(
        "assistant",
        "Something like this keeps it honest:\n\n```\n## Scope\nmuseum_tickets records "
        "which tickets the front desk issued, voided or admitted, in memory for the day "
        "and in an append-only journal file for the treasurer. It does not take payments, "
        "print tickets or talk to the card terminal. One process, one desk, one journal "
        "file.\n\n## Non-goals\n- payments or receipts\n- seat or timeslot booking\n- "
        "syncing between laptops\n```\n\nA usage block right after it stops the questions "
        "about how to run it:\n\n```python\nfrom museum_tickets.desk import TicketDesk\n\n"
        'desk = TicketDesk("/home/desk/journal-2026-09.log")\nt = desk.issue("ana", '
        '"bronze age")\nprint(t.ticket_id, t.status)\n```\n\nThe journal path in the '
        "constructor is deliberate: the treasurer can point it at a fresh file each month "
        "and the package never needs to know what month it is.",
    ),
    Turn(
        "user",
        "Good. On ids: I mint M1, M2, ... from a counter, and the counter restarts every "
        "morning when the laptop boots, because the desk is in memory. That means the "
        "journal has M1 repeated every day. The treasurer says that is fine because she "
        "reconciles per day and the file name carries the date, but I wonder whether I "
        "should prefix the date into the id, like 0914-M1, to be safe. Here is what a "
        "two-day journal looks like at the moment:\n\n```\nissue M1 bronze age\nissue "
        "M2 maps\nvoid M1\nissue M1 bronze age\nissue M2 bronze age\n```\n\nThe fourth "
        "line is a new day, but nothing in the file says so. Would a date prefix be "
        "over-engineering for two rooms and a rotating exhibition, or is this the sort of "
        "thing I will regret in March when she asks which M1 was voided? The launcher "
        'script currently opens the journal with `open(path, "a")` once per line, so '
        "adding a day marker there would be easy if that is the better answer.",
    ),
    Turn(
        "assistant",
        "You will regret it, but not because of the ids. The fix is a day marker in the "
        "journal, not a longer id: write one `day 2026-09-14` line when the desk starts "
        "and the plain M1 ids become unambiguous within the file, while every ticket the "
        "volunteers say out loud stays short. A date prefix in the id would leak into "
        "every message and test for a problem that only the reconciliation has. If you "
        "do want it later, only `issue` mints ids, so it is a one-line change:\n\n"
        '```python\ndef _next_id(self) -> str:\n    self._counter += 1\n    return f"M{'
        'self._counter}"\n```\n\nand the day marker is a single `journal.append_line('
        'path, f"day {date.today()}")` in whatever starts the desk for the morning, '
        "which can live in the launcher script rather than in TicketDesk itself. The "
        "treasurer's reconciliation then reads: find the `day` line, count `issue` lines "
        "until the next `day` line, subtract `void` lines, compare with the cash box.",
    ),
    Turn(
        "user",
        "I have started on tests for issue and the journal. This is the draft; I want to "
        "check the shape before I write more of them, because I tend to over-test the "
        "file format and under-test the behaviour:\n\n```python\nfrom museum_tickets.desk "
        "import TicketDesk\n\n\ndef test_issue_mints_sequential_ids(tmp_path):\n    d = "
        'TicketDesk(str(tmp_path / "j.log"))\n    assert d.issue("ana", "maps").ticket_id '
        '== "M1"\n    assert d.issue("bo", "maps").ticket_id == "M2"\n\n\ndef '
        'test_issue_writes_one_journal_line(tmp_path):\n    path = tmp_path / "j.log"\n'
        '    d = TicketDesk(str(path))\n    d.issue("ana", "bronze age")\n    assert '
        'path.read_text().splitlines() == ["issue M1 bronze age"]\n\n\ndef '
        "test_lookup_unknown_is_none(tmp_path):\n    d = TicketDesk(str(tmp_path / "
        '"j.log"))\n    assert d.lookup("M7") is None\n```\n\nIs `tmp_path` per test the '
        "right way to get a fresh journal, or should the desk accept a file object?",
    ),
    Turn(
        "assistant",
        "The tests are the right shape: one behaviour each, and the journal assertion "
        "checks the whole file rather than a substring, which is what catches an "
        "accidental double write. Keep `tmp_path`; a fresh path per test is exactly the "
        "isolation you want and it exercises the real `open(..., 'a')` call, which a file "
        "object passed in would not. The one thing I would add is a test that the journal "
        "line and the in-memory record agree after a void:\n\n```python\ndef "
        'test_void_updates_record_and_journal(tmp_path):\n    path = tmp_path / "j.log"\n'
        '    d = TicketDesk(str(path))\n    t = d.issue("ana", "maps")\n    assert '
        'd.void(t.ticket_id).status == "void"\n    assert path.read_text().splitlines()'
        '[-1] == "void M1"\n```\n\nThat pins the two things the treasurer actually '
        "relies on: the record changed and the file says so. Resist testing the exact "
        "bytes of the whole journal in every test; one test that pins the line format "
        "is enough, and the rest can check only the last line.",
    ),
    Turn(
        "user",
        "Now the thing that actually bit us on Saturday. The laptop's home directory "
        "filled up with photos someone copied over, and the desk crashed mid-morning "
        "with this, straight from the launcher script:\n\n```\nTraceback (most recent "
        'call last):\n  File "/home/desk/run_desk.py", line 31, in <module>\n    '
        'desk.issue(holder, exhibition)\n  File "/home/desk/museum_tickets/desk.py", '
        'line 16, in issue\n    journal.append_line(self._journal_path, f"issue '
        '{ticket.ticket_id} {exhibition}")\n  File "/home/desk/museum_tickets/journal.py", '
        'line 6, in append_line\n    fh.write(line + "\\n")\nOSError: [Errno 28] No space '
        "left on device\n```\n\nThe volunteer on the desk had no idea what any of that "
        "meant and just kept selling paper tickets. I want callers, meaning the launcher "
        "and a future CLI, to see one package exception with a plain message instead of "
        "whatever the OS throws. How would you structure that without try/except "
        "sprinkled through every method?",
    ),
    Turn(
        "assistant",
        "Define one exception class in the package and funnel every journal write "
        "through a single private method that translates:\n\n```python\nclass "
        'TicketsError(Exception):\n    """Raised when the ticket journal cannot be '
        'written."""\n```\n\n```python\ndef _record(self, line: str) -> None:\n    try:\n'
        "        journal.append_line(self._journal_path, line)\n    except OSError as "
        'exc:\n        raise TicketsError(f"journal write failed: {exc}") from exc\n```'
        "\n\n`issue` and `void` call `_record` instead of `journal.append_line` "
        "directly, so the try/except exists exactly once, and `from exc` keeps the "
        "original errno in the chained traceback for whoever debugs the laptop. The "
        "launcher then catches TicketsError and prints one line the volunteer can read, "
        "such as 'journal write failed, tell the treasurer', instead of the stack dump. "
        "The in-memory record is still updated before the write, which is fine for a "
        "one-desk tool: the volunteer can keep admitting people and the treasurer "
        "re-derives the missing lines from the paper stubs.",
    ),
    Turn(
        "user",
        "That is the convention from now on, and I want it stated plainly: every public "
        "TicketDesk method that writes the journal wraps any OSError from the journal in "
        "TicketsError, raised `from` the original, and callers never see a raw OSError. "
        "New methods go through `_record` so this stays true.",
    ),
    Turn(
        "assistant",
        "Noted: public TicketDesk methods that touch the journal surface journal I/O "
        "failures only as TicketsError chained from the OSError, never raw. I will route "
        "every new journal write through `_record` so the wrapping is uniform.",
    ),
    Turn(
        "user",
        "Second convention, about unknown ids. Methods that act on a ticket by id, like "
        "`void`, return None when the id is not in the desk and change nothing, no "
        "journal line, no exception. Volunteers mistype ids constantly and I would rather "
        "the launcher print 'no such ticket' than crash. New methods follow that.",
    ),
    Turn(
        "assistant",
        "Understood: actions keyed by ticket id return None on an unknown id and leave "
        "both the desk and the journal untouched, matching `void`. New methods will check "
        "with `self._tickets.get(...)` first and return None before any journal write.",
    ),
    Turn(
        "user",
        "For later, not now: the treasurer would like a daily summary at close, counts "
        "per exhibition and per status. I imagine the launcher doing roughly:\n\n"
        "```python\ndef close_of_day(desk: TicketDesk) -> None:\n    for name, n in "
        'desk.totals_by_exhibition().items():\n        print(f"{name}: {n}")\n```\n\n'
        "Just flagging it so nothing we do now makes that awkward. I also want the "
        "summary to show void and admitted counts separately, since the treasurer only "
        "counts money for tickets that were neither voided nor refunded, and the "
        "status field seems to be enough for that.",
    ),
    Turn(
        "assistant",
        "Nothing so far blocks it. `totals_by_exhibition` is a `Counter` over "
        "`self._tickets.values()` keyed by exhibition, and a status variant is the same "
        "with `t.status`. Both are reads, so they never touch the journal and never need "
        "`_record`. Status counts follow the same pattern:\n\n```python\ndef "
        "totals_by_status(self) -> dict[str, int]:\n    return dict(Counter(t.status for t "
        "in self._tickets.values()))\n```\n\nSo close-of-day is two dict prints.",
    ),
    Turn(
        "user",
        "Right, let's get the door scanner working before Saturday. I will paste the "
        "current files with each request so you see the real state of the code rather "
        "than my memory of it.",
    ),
    Turn(
        "assistant",
        "Ready when you are. Send the request and I will return the full desk module.",
    ),
]

_EVENT = (
    "Change of convention, effective now: new TicketDesk methods that act on a ticket "
    "id raise KeyError when the id is unknown, instead of returning None. The treasurer "
    "wants mistyped ids to fail loudly in the launcher. `void` and `admit` keep their "
    "current behaviour; only new methods follow the new rule."
)


def build() -> Session:
    return Session(
        id="S38",
        project="museum_tickets",
        target_family="missing_record",
        support_family="error_surface",
        lifecycle="replacement",
        files=_FILES,
        prefix=_PREFIX,
        states=("none", "raise"),
        state_at=("none", "raise"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10),
        tags={"support_state": "wrap"},
    )
