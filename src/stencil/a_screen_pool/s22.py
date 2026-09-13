# ruff: noqa: E501
"""S22: shift scheduling — validation (target, replacement) x error_surface (support)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '''"""rotaplan package."""


class RotaError(Exception):
    """Raised when the shift journal cannot be written."""
'''

_MODEL = '''"""Worker and shift records."""

from dataclasses import dataclass

DAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


@dataclass(frozen=True)
class Worker:
    name: str
    max_hours: int


@dataclass(frozen=True)
class Shift:
    shift_id: str
    worker: str
    day: str
    hours: int
'''

_JOURNAL = '''"""Append-only shift journal on disk."""


def append_entry(path: str, line: str) -> None:
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(line + "\\n")
'''

_ROSTER_HEAD = '''"""Shift table (storage layer) and the public rota operations."""

from rotaplan import RotaError, journal
from rotaplan.model import Shift, Worker


class ShiftTable:
    def __init__(self, journal_path: str | None = None) -> None:
        self.journal_path = journal_path
        self._workers: dict[str, Worker] = {}
        self._shifts: dict[str, Shift] = {}

    def _journal(self, line: str) -> None:
        if self.journal_path is None:
            return
        try:
            journal.append_entry(self.journal_path, line)
        except OSError as exc:
            raise RotaError(f"journal write failed: {exc}") from exc

    def insert_worker(self, worker: Worker) -> None:
        self._workers[worker.name] = worker
        self._journal(f"worker {worker.name}")

    def get_worker(self, name: str) -> Worker:
        return self._workers[name]

    def get_shift(self, shift_id: str) -> Shift:
        return self._shifts[shift_id]

    def next_shift_id(self) -> str:
        return f"S{len(self._shifts) + 1}"
'''

_ADD_WORKER = """

def add_worker(table: ShiftTable, name: str, max_hours: int) -> Worker:
    if max_hours <= 0:
        raise ValueError("max_hours must be positive")
    worker = Worker(name, max_hours)
    table.insert_worker(worker)
    return worker
"""

_ROSTER = _ROSTER_HEAD + _ADD_WORKER

_FILES = {
    "rotaplan/__init__.py": _INIT,
    "rotaplan/model.py": _MODEL,
    "rotaplan/journal.py": _JOURNAL,
    "rotaplan/roster.py": _ROSTER,
}


def _insert_shift(state: str) -> str:
    check = (
        '        if not 1 <= shift.hours <= 12:\n            raise ValueError("hours must be between 1 and 12")\n'
        if state == "storage"
        else ""
    )
    return (
        "\n    def insert_shift(self, shift: Shift) -> None:\n"
        + check
        + "        self._shifts[shift.shift_id] = shift\n"
        '        self._journal(f"shift {shift.shift_id}")\n'
    )


def _assign_shift(state: str) -> str:
    check = (
        '    if not 1 <= hours <= 12:\n        raise ValueError("hours must be between 1 and 12")\n'
        if state == "api"
        else ""
    )
    return (
        "\n\ndef assign_shift(table: ShiftTable, worker: str, day: str, hours: int) -> Shift:\n"
        "    table.get_worker(worker)\n"
        + check
        + "    shift = Shift(table.next_shift_id(), worker, day, hours)\n"
        "    table.insert_shift(shift)\n"
        "    return shift\n"
    )


def _update_shift(state: str) -> str:
    check = (
        '        if shift.day not in DAYS:\n            raise ValueError("day must be one of DAYS")\n'
        if state == "storage"
        else ""
    )
    return (
        "\n    def update_shift(self, shift: Shift) -> None:\n"
        "        self._shifts[shift.shift_id]\n"
        + check
        + "        self._shifts[shift.shift_id] = shift\n"
        '        self._journal(f"move {shift.shift_id} {shift.day}")\n'
    )


def _move_shift(state: str) -> str:
    check = (
        '    if day not in DAYS:\n        raise ValueError("day must be one of DAYS")\n'
        if state == "api"
        else ""
    )
    return (
        "\n\ndef move_shift(table: ShiftTable, shift_id: str, day: str) -> Shift:\n"
        + check
        + "    moved = replace(table.get_shift(shift_id), day=day)\n"
        "    table.update_shift(moved)\n"
        "    return moved\n"
    )


def _gold1(state: str) -> str:
    return _ROSTER_HEAD + _insert_shift(state) + _ADD_WORKER + _assign_shift(state)


def _gold2(state: str) -> str:
    # Built on the checkpoint-1 gold under the state then in force (api).
    head = _ROSTER_HEAD.replace(
        "from rotaplan import RotaError, journal\nfrom rotaplan.model import Shift, Worker\n",
        "from dataclasses import replace\n\nfrom rotaplan import RotaError, journal\nfrom rotaplan.model import DAYS, Shift, Worker\n",
        1,
    )
    return (
        head
        + _insert_shift("api")
        + _update_shift(state)
        + _ADD_WORKER
        + _assign_shift("api")
        + _move_shift(state)
    )


# ----------------------------------------------------------------- checkpoint 1: assign_shift

_C1_FUNCTIONAL = {
    "test_shift_functional.py": """import pytest

from rotaplan.model import Shift
from rotaplan.roster import ShiftTable, add_worker, assign_shift


def _setup(path=None):
    t = ShiftTable(journal_path=path)
    add_worker(t, "ann", 40)
    return t


def test_assign_shift_stores_and_returns_shift():
    t = _setup()
    s = assign_shift(t, "ann", "mon", 8)
    assert s.worker == "ann" and s.day == "mon" and s.hours == 8
    assert s.shift_id.startswith("S") and t.get_shift(s.shift_id) == s


def test_two_shifts_get_distinct_ids():
    t = _setup()
    a = assign_shift(t, "ann", "mon", 8)
    b = assign_shift(t, "ann", "tue", 4)
    assert a.shift_id != b.shift_id


def test_assign_shift_journals_the_shift(tmp_path):
    t = _setup(str(tmp_path / "rota.log"))
    s = assign_shift(t, "ann", "wed", 6)
    lines = (tmp_path / "rota.log").read_text().splitlines()
    assert lines == ["worker ann", f"shift {s.shift_id}"]


def test_unknown_worker_raises_keyerror():
    t = _setup()
    with pytest.raises(KeyError):
        assign_shift(t, "zed", "mon", 8)


def test_hours_out_of_range_raise_and_store_nothing():
    t = _setup()
    for bad in (0, 13, -2):
        with pytest.raises(ValueError):
            assign_shift(t, "ann", "mon", bad)
    with pytest.raises(KeyError):
        t.get_shift("S1")


def test_table_has_insert_shift():
    t = _setup()
    t.insert_shift(Shift("S7", "ann", "fri", 5))
    assert t.get_shift("S7").day == "fri"
"""
}

_C1_REGRESSION = {
    "test_shift_regression.py": """import pytest

from rotaplan import RotaError
from rotaplan.roster import ShiftTable, add_worker


def test_add_worker_unchanged(tmp_path):
    t = ShiftTable(journal_path=str(tmp_path / "rota.log"))
    w = add_worker(t, "ann", 40)
    assert t.get_worker("ann") is w and w.max_hours == 40
    assert (tmp_path / "rota.log").read_text() == "worker ann\\n"
    with pytest.raises(ValueError):
        add_worker(t, "bo", 0)
    with pytest.raises(KeyError):
        t.get_worker("zed")
    t.journal_path = str(tmp_path)
    with pytest.raises(RotaError):
        add_worker(t, "cy", 10)
"""
}

_C1_CONTRACT = {
    "api": {
        "test_shift_validation.py": """import pytest

from rotaplan.model import Shift
from rotaplan.roster import ShiftTable, add_worker, assign_shift


def test_public_function_rejects_hours_out_of_range():
    t = ShiftTable()
    add_worker(t, "ann", 40)
    for bad in (0, 13):
        with pytest.raises(ValueError):
            assign_shift(t, "ann", "mon", bad)
    with pytest.raises(KeyError):
        t.get_shift("S1")


def test_table_trusts_callers_on_hours():
    t = ShiftTable()
    t.insert_shift(Shift("S9", "ann", "mon", 0))
    assert t.get_shift("S9").hours == 0
"""
    },
    "storage": {
        "test_shift_validation.py": """import pytest

from rotaplan.model import Shift
from rotaplan.roster import ShiftTable, add_worker, assign_shift


def test_table_rejects_hours_out_of_range():
    t = ShiftTable()
    for bad in (0, 13):
        with pytest.raises(ValueError):
            t.insert_shift(Shift("S9", "ann", "mon", bad))
    with pytest.raises(KeyError):
        t.get_shift("S9")


def test_public_function_passes_invalid_hours_through(monkeypatch):
    t = ShiftTable()
    add_worker(t, "ann", 40)
    seen = []
    real = t.insert_shift

    def spy(shift):
        seen.append(shift.hours)
        return real(shift)

    monkeypatch.setattr(t, "insert_shift", spy)
    with pytest.raises(ValueError):
        assign_shift(t, "ann", "mon", 13)
    assert seen == [13]
"""
    },
}

_C1_SUPPORT = {
    "test_shift_errors.py": """import pytest

from rotaplan import RotaError
from rotaplan.roster import ShiftTable, add_worker, assign_shift


def test_journal_failure_is_wrapped_in_rota_error(tmp_path):
    t = ShiftTable()
    add_worker(t, "ann", 40)
    t.journal_path = str(tmp_path)  # a directory: appending raises OSError
    with pytest.raises(RotaError) as ei:
        assign_shift(t, "ann", "mon", 8)
    assert not isinstance(ei.value, OSError)
    assert isinstance(ei.value.__cause__, OSError)
"""
}

_REQ1 = Request(
    text=(
        "Add shifts. Give ShiftTable an `insert_shift(shift)` method that stores a Shift "
        "under its shift_id and journals the line `shift <shift_id>`, and add a public "
        "function `assign_shift(table, worker, day, hours)` that checks the worker exists "
        "(an unknown name raises KeyError), mints an id with next_shift_id, stores the "
        "shift and returns it. Hours outside 1 to 12 inclusive are invalid and must raise "
        "ValueError."
    ),
    target="rotaplan/roster.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"api": _gold1("api"), "storage": _gold1("storage")},
)

# ----------------------------------------------------------------- checkpoint 2: move_shift

_C2_FUNCTIONAL = {
    "test_move_functional.py": """import pytest

from dataclasses import replace

from rotaplan.roster import ShiftTable, add_worker, assign_shift, move_shift


def _setup(path=None):
    t = ShiftTable(journal_path=path)
    add_worker(t, "ann", 40)
    s = assign_shift(t, "ann", "mon", 8)
    return t, s


def test_move_shift_changes_day_and_returns_shift():
    t, s = _setup()
    out = move_shift(t, s.shift_id, "thu")
    assert out.day == "thu" and out.shift_id == s.shift_id and out.hours == 8
    assert t.get_shift(s.shift_id).day == "thu"


def test_move_shift_journals_the_move(tmp_path):
    t, s = _setup(str(tmp_path / "rota.log"))
    move_shift(t, s.shift_id, "sat")
    lines = (tmp_path / "rota.log").read_text().splitlines()
    assert lines[-1] == f"move {s.shift_id} sat"


def test_move_unknown_shift_raises_keyerror():
    t, _ = _setup()
    with pytest.raises(KeyError):
        move_shift(t, "S99", "tue")


def test_move_to_bad_day_raises_and_keeps_old_day():
    t, s = _setup()
    for bad in ("funday", "Monday", ""):
        with pytest.raises(ValueError):
            move_shift(t, s.shift_id, bad)
    assert t.get_shift(s.shift_id).day == "mon"


def test_table_has_update_shift():
    t, s = _setup()
    t.update_shift(replace(s, day="sun"))
    assert t.get_shift(s.shift_id).day == "sun"
    with pytest.raises(KeyError):
        t.update_shift(replace(s, shift_id="S99"))
"""
}

_C2_REGRESSION = {
    "test_move_regression.py": """import pytest

from rotaplan import RotaError
from rotaplan.roster import ShiftTable, add_worker, assign_shift


def test_workers_and_shifts_unchanged(tmp_path):
    t = ShiftTable(journal_path=str(tmp_path / "rota.log"))
    add_worker(t, "ann", 40)
    s = assign_shift(t, "ann", "mon", 8)
    assert t.get_shift(s.shift_id) == s
    assert (tmp_path / "rota.log").read_text().splitlines() == ["worker ann", f"shift {s.shift_id}"]
    with pytest.raises(ValueError):
        assign_shift(t, "ann", "mon", 13)
    with pytest.raises(KeyError):
        assign_shift(t, "zed", "mon", 8)
    t.journal_path = str(tmp_path)
    with pytest.raises(RotaError):
        assign_shift(t, "ann", "tue", 4)
"""
}

_C2_CONTRACT = {
    "api": {
        "test_move_validation.py": """import pytest

from dataclasses import replace

from rotaplan.roster import ShiftTable, add_worker, assign_shift, move_shift


def _setup():
    t = ShiftTable()
    add_worker(t, "ann", 40)
    return t, assign_shift(t, "ann", "mon", 8)


def test_public_function_rejects_bad_day():
    t, s = _setup()
    for bad in ("funday", ""):
        with pytest.raises(ValueError):
            move_shift(t, s.shift_id, bad)
    assert t.get_shift(s.shift_id).day == "mon"


def test_table_trusts_callers_on_day():
    t, s = _setup()
    t.update_shift(replace(s, day="funday"))
    assert t.get_shift(s.shift_id).day == "funday"
"""
    },
    "storage": {
        "test_move_validation.py": """import pytest

from dataclasses import replace

from rotaplan.roster import ShiftTable, add_worker, assign_shift, move_shift


def _setup():
    t = ShiftTable()
    add_worker(t, "ann", 40)
    return t, assign_shift(t, "ann", "mon", 8)


def test_table_rejects_bad_day():
    t, s = _setup()
    for bad in ("funday", ""):
        with pytest.raises(ValueError):
            t.update_shift(replace(s, day=bad))
    assert t.get_shift(s.shift_id).day == "mon"


def test_public_function_passes_bad_day_through(monkeypatch):
    t, s = _setup()
    seen = []
    real = t.update_shift

    def spy(shift):
        seen.append(shift.day)
        return real(shift)

    monkeypatch.setattr(t, "update_shift", spy)
    with pytest.raises(ValueError):
        move_shift(t, s.shift_id, "funday")
    assert seen == ["funday"]
"""
    },
}

_C2_SUPPORT = {
    "test_move_errors.py": """import pytest

from rotaplan import RotaError
from rotaplan.roster import ShiftTable, add_worker, assign_shift, move_shift


def test_journal_failure_is_wrapped_in_rota_error(tmp_path):
    t = ShiftTable()
    add_worker(t, "ann", 40)
    s = assign_shift(t, "ann", "mon", 8)
    t.journal_path = str(tmp_path)  # a directory: appending raises OSError
    with pytest.raises(RotaError) as ei:
        move_shift(t, s.shift_id, "tue")
    assert not isinstance(ei.value, OSError)
    assert isinstance(ei.value.__cause__, OSError)
"""
}

_REQ2 = Request(
    text=(
        "Add moving a shift to another day. Give ShiftTable an `update_shift(shift)` "
        "method that replaces the stored shift with the same shift_id (an unknown id "
        "raises KeyError) and journals `move <shift_id> <day>`, and add a public function "
        "`move_shift(table, shift_id, day)` that builds the moved copy of the shift, stores "
        "it through update_shift and returns the updated Shift. A day that is not one of "
        "DAYS is invalid and must raise ValueError."
    ),
    target="rotaplan/roster.py",
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
        "I manage the rota for a small independent bookshop: five part-timers, open seven "
        "days, and a paper grid on the staff-room wall that gets rewritten in pencil every "
        "time someone swaps. I want a small Python package, `rotaplan`, that keeps workers "
        "and shifts in memory and appends every change to a plain-text journal file so I "
        "can see who moved what when the inevitable 'I never agreed to Saturday' happens. "
        "A script prints the week:\n\n```\ncd /srv/shop && python -m rotaplan.week "
        "--journal /srv/shop/rota.log > /srv/shop/week.txt\n```\n\nWe are talking maybe "
        "thirty shifts a week and a handful of swaps. I do not want a database, a web page "
        "or anything that needs a login. Could you sketch the README scope section so the "
        "owner does not start asking for payroll integration? She has asked twice already "
        "about exporting hours to the accountant, and I want a polite written no. The "
        "part-timers are Ann, Bo, Cy, Dee and Eli; none of them will ever run the script "
        "themselves, so the output has to be readable on the wall, not in a terminal.",
    ),
    Turn(
        "assistant",
        "A scope section with a firm non-goals list does the polite-no for you:\n\n```\n## "
        "Scope\nrotaplan keeps the week's workers and shifts in memory for one process and "
        "appends every change to a plain-text journal. It is a library for small scripts, "
        "not a service, and it has no persistence beyond the journal.\n\n## Non-goals\n- "
        "payroll or hours export to accounting software\n- holiday requests or approvals\n- "
        "a web or phone interface\n- multi-user editing\n```\n\nAnd the usage block:\n\n"
        "```python\nfrom rotaplan.roster import ShiftTable, add_worker\n\ntable = ShiftTable("
        'journal_path="/srv/shop/rota.log")\nann = add_worker(table, "ann", 20)\nprint(ann)'
        "\n```\n\nIf the accountant question comes back, point at the journal: it is plain "
        "text and anyone can total hours from it with a spreadsheet, which is a different "
        "project. The `week.txt` output is what goes on the wall; keep the package's job "
        "to producing it and leave printing and pinning to humans. Keep the README to one "
        "screen; the owner will read it on her phone, if at all.",
    ),
    Turn(
        "user",
        "The journal is the bit I care about most. Right now `insert_worker` appends "
        "`worker ann` and I was going to keep every line as a short verb followed by ids. "
        "Here is what the file looks like after a test run:\n\n```\nworker ann\nworker bo\n"
        "worker cy\nshift S1\nshift S2\nswap S2 bo\n```\n\nI deliberately do not write the "
        "full record, just enough to reconstruct who touched what. Is that a mistake? A "
        "friend said I should write JSON lines so a script can parse it, but the point is "
        "that a human reads it on a Monday morning with coffee, and `shift S2` is easier on "
        'the eyes than `{"op": "shift", "id": "S2"}`. The journal is append-only and '
        "never rewritten; the week script will read current state from a JSON dump I add "
        "later, so replaying the journal is a debugging tool, not the source of truth. "
        "Also, should the table write the journal itself or should the public functions "
        "do it after the table call?",
    ),
    Turn(
        "assistant",
        "Short verb-plus-ids lines are a good fit for a human-first log; keep them. If a "
        "script ever needs to parse the journal the format is still regular (`verb id "
        "[arg]`), so `line.split()` gets you there without JSON. Put the write inside the "
        "table, not in the public functions: every mutation goes through a table method, so "
        "the journal cannot miss one, and tests can point `journal_path` at a temp file and "
        "read it back. A single private helper keeps the `None` check in one place:\n\n"
        "```python\ndef _journal(self, line: str) -> None:\n    if self.journal_path is "
        "None:\n        return\n    journal.append_entry(self.journal_path, line)\n```\n\n"
        'Then `insert_worker` is `self._journal(f"worker {worker.name}")` and a new '
        "method is one more call. The public functions stay about building records and "
        "never about files. Keeping the journal as an audit trail rather than the source "
        "of truth is the right split: an append-only file answers 'who changed this', and "
        "the JSON dump can carry the state without either file pretending to be the other.",
    ),
    Turn(
        "user",
        "Speaking of files, this happened when I pointed the journal at a path on the NAS "
        "that was not mounted yet:\n\n```\nTraceback (most recent call last):\n  File "
        '"/srv/shop/rotaplan/week.py", line 18, in <module>\n    add_worker(table, name, '
        'hours)\n  File "/srv/shop/rotaplan/roster.py", line 27, in add_worker\n    table.'
        'insert_worker(worker)\n  File "/srv/shop/rotaplan/roster.py", line 17, in '
        'insert_worker\n    journal.append_entry(self.journal_path, f"worker {worker.name}")'
        '\n  File "/srv/shop/rotaplan/journal.py", line 5, in append_entry\n    with open('
        'path, "a", encoding="utf-8") as fh:\nFileNotFoundError: [Errno 2] No such file or '
        "directory: '/mnt/nas/shop/rota.log'\n```\n\nThe NAS is mounted by a systemd unit "
        "that sometimes races the cron job, so this will recur. The script caller had no "
        "idea that `add_worker` could raise a file error. I would like callers to catch "
        "one thing.",
    ),
    Turn(
        "assistant",
        "Then give the package one exception class and translate at the boundary where the "
        "file is touched. `RotaError` in `rotaplan/__init__.py`, and `_journal` becomes:\n\n"
        "```python\ntry:\n    journal.append_entry(self.journal_path, line)\nexcept OSError "
        'as exc:\n    raise RotaError(f"journal write failed: {exc}") from exc\n```\n\nThe '
        "`from exc` keeps the original FileNotFoundError as `__cause__`, so the traceback "
        "still shows the NAS path, but the script only has to catch `RotaError`. Because "
        "every table method writes through `_journal`, every public function inherits the "
        "translation for free; nobody has to remember to wrap anything in a new method, "
        "they just call `self._journal(...)` as before. Two details worth fixing now: "
        "catch `OSError` specifically rather than `Exception`, so a genuine bug in the "
        "journal code still surfaces as itself, and put the failing path in the message, "
        "because the person reading `week.err` on Monday will not have the traceback. "
        "Keep `RotaError` a plain `Exception` subclass, not an `OSError` subclass, so "
        "nothing upstream can accidentally treat it as a file error.",
    ),
    Turn(
        "user",
        "Good. Days: I want `mon`..`sun` lowercase as a fixed tuple in `model.py`, "
        "`DAYS`, so the week printer can iterate it in order. The week printer draft:\n\n"
        "```python\nfrom rotaplan.model import DAYS\n\n\ndef print_week(shifts):\n    "
        "for day in DAYS:\n        todays = [s for s in shifts if s.day == day]\n        "
        'names = ", ".join(f"{s.worker}({s.hours}h)" for s in todays)\n        print(f"'
        "{day}: {names or '-'}\")\n```\n\nAnd workers have a weekly `max_hours` so the "
        "owner can see who is near their contract limit. I'm not enforcing the limit in "
        "code yet; she wants to be able to go over it in a pinch and just see a warning "
        "on the printout. The day strings are lowercase because the JSON dump will be "
        "edited by hand occasionally and I do not want `Mon` and `mon` to be different "
        "days. Shifts carry an integer `hours` rather than start and end times, because "
        "the shop opens 9 to 6 and nobody cares about the exact slot, only the total.",
    ),
    Turn(
        "assistant",
        "That all fits. `DAYS` as a module-level tuple gives you ordering and membership in "
        "one object, and keeping `max_hours` advisory is the right call for a shop where "
        "the owner overrides the rules weekly; the printer can mark overs with an asterisk:"
        "\n\n```python\nused = sum(s.hours for s in shifts if s.worker == w.name)\nflag = "
        '" *" if used > w.max_hours else ""\nprint(f"{w.name}: {used}/{w.max_hours}h{flag}")'
        "\n```\n\nIf you later do want to enforce it, that is a new public function that "
        "checks totals, not a change to the existing ones, so nothing you write now paints "
        "you in. Integer hours instead of start and end times is a good simplification for "
        "a shop with one opening pattern; if a second location with different hours ever "
        "appears, that is the moment to add times, and `hours` can be derived from them. "
        "The lowercase `DAYS` tuple also gives you a cheap membership test for hand-edited "
        "dumps, which is worth more than it looks.",
    ),
    Turn(
        "user",
        "Two conventions to fix before the real features land. First, errors: any file or "
        "I/O failure underneath a public function in `rotaplan.roster` surfaces as "
        "`RotaError`, raised `from` the original OSError, never as a raw OSError. That is "
        "the rule for everything the table does, existing and new, so the week script can "
        "catch one thing and write one line to `week.err`.",
    ),
    Turn(
        "assistant",
        "Noted: I/O failures from the journal are wrapped in `RotaError` with the original "
        "OSError chained as the cause, for every table operation. New methods write through "
        "`_journal` so they inherit the wrapping; I will not let a raw OSError escape.",
    ),
    Turn(
        "user",
        "Second, validation: it lives in the public functions. They check their arguments "
        "and raise ValueError before calling the table, the way `add_worker` rejects "
        "non-positive max_hours today. ShiftTable methods trust their callers and do not "
        "validate; they store what they are given and write the journal line.",
    ),
    Turn(
        "assistant",
        "Understood: validation belongs to the public functions in `roster.py`, which raise "
        "ValueError up front, and ShiftTable methods stay thin and trusting like "
        "`insert_worker`. New table methods will store and journal only.",
    ),
    Turn(
        "user",
        "For later, not now: I'd like a `hours_for(worker)` total on the table so the "
        "printer does not have to sum shifts itself. Just parking the thought.",
    ),
    Turn(
        "assistant",
        "Parked. It will be a one-line sum over `self._shifts.values()` filtered by worker, "
        "and the printer switches to it without any other change.",
    ),
    Turn(
        "user",
        "For the record, the only test that exists today is:\n\n```python\nfrom "
        "rotaplan.roster import ShiftTable, add_worker\n\n\ndef "
        'test_add_worker_registers_name():\n    t = ShiftTable()\n    add_worker(t, "ann", '
        '20)\n    assert t.get_worker("ann").max_hours == 20\n```\n\nI will paste the '
        "current files with each request.",
    ),
    Turn(
        "assistant",
        "Ready. Send the first feature and I will return the complete `roster.py`.",
    ),
]

_EVENT = (
    "Change of convention, effective now: new ShiftTable methods validate their own "
    "inputs and raise ValueError themselves, and new public functions pass their "
    "arguments straight through to the table with no pre-check of their own. Whatever "
    "is already written stays as it is; only new code follows the new rule."
)


def build() -> Session:
    return Session(
        id="S22",
        project="rotaplan",
        target_family="validation",
        support_family="error_surface",
        lifecycle="replacement",
        files=_FILES,
        prefix=_PREFIX,
        states=("api", "storage"),
        state_at=("api", "storage"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10),
    )
