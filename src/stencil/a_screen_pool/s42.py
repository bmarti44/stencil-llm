# ruff: noqa: E501
"""S42: beekeeping hives — missing_record (target, replacement) x error_surface (support, wrap)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '''"""apiary package: the club's hive records."""


class ApiaryError(Exception):
    """Raised when the hive logbook cannot be written."""
'''

_MODEL = '''"""Hive records."""

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Hive:
    hive_id: str
    site: str
    queen_year: int
    status: str = "active"
    note: str | None = None

    def with_changes(self, **changes) -> "Hive":
        return replace(self, **changes)
'''

_LOGBOOK = '''"""Append-only logbook required by the regional bee inspector."""


def append_line(path: str, line: str) -> None:
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(line + "\\n")
'''

_YARD = '''"""The bee yard: every hive the club keeps."""

from apiary import ApiaryError, logbook
from apiary.model import Hive


class Yard:
    def __init__(self, logbook_path: str) -> None:
        self._logbook_path = logbook_path
        self._hives: dict[str, Hive] = {}
        self._counter = 0

    def add_hive(self, site: str, queen_year: int) -> Hive:
        self._counter += 1
        hive = Hive(f"H{self._counter}", site, queen_year)
        self._hives[hive.hive_id] = hive
        self._log(f"add {hive.hive_id} {site} {queen_year}")
        return hive

    def requeen(self, hive_id: str, year: int) -> Hive:
        hive = self._hives[hive_id]
        requeened = hive.with_changes(queen_year=year)
        self._hives[hive_id] = requeened
        self._log(f"requeen {hive_id} {year}")
        return requeened

    def get(self, hive_id: str) -> Hive | None:
        return self._hives.get(hive_id)

    def count(self) -> int:
        return len(self._hives)

    def _log(self, line: str) -> None:
        try:
            logbook.append_line(self._logbook_path, line)
        except OSError as exc:
            raise ApiaryError(f"logbook write failed: {exc}") from exc
'''

_FILES = {
    "apiary/__init__.py": _INIT,
    "apiary/model.py": _MODEL,
    "apiary/logbook.py": _LOGBOOK,
    "apiary/yard.py": _YARD,
}

_HELPER_COMMON = """import pytest

from apiary import ApiaryError, logbook
from apiary.model import Hive
from apiary.yard import Yard


def _yard(tmp_path):
    path = tmp_path / "logbook.txt"
    return Yard(str(path)), path


def _boom(path, line):
    raise OSError(28, "No space left on device")
"""

# ----------------------------------------------------------------- checkpoint 1: record_treatment

_C1_HELPER = (
    _HELPER_COMMON
    + """

def _treat(yard):
    fn = getattr(yard, "record_treatment", None) or getattr(yard, "treat", None)
    assert fn is not None, "no record_treatment method found"
    return fn
"""
)

_C1_FUNCTIONAL = {
    "test_treatment_functional.py": _C1_HELPER
    + """

def test_record_treatment_sets_status_and_note(tmp_path):
    y, _ = _yard(tmp_path)
    h = y.add_hive("orchard", 2025)
    out = _treat(y)(h.hive_id, "oxalic acid dribble")
    assert out.status == "treated" and out.note == "oxalic acid dribble"
    assert out.hive_id == h.hive_id and out.queen_year == 2025
    assert y.get(h.hive_id).status == "treated"


def test_record_treatment_writes_logbook_line(tmp_path):
    y, path = _yard(tmp_path)
    h = y.add_hive("orchard", 2025)
    _treat(y)(h.hive_id, "oxalic acid dribble")
    lines = path.read_text().splitlines()
    assert lines[-1] == f"treat {h.hive_id} oxalic acid dribble" and len(lines) == 2


def test_record_treatment_leaves_other_hives_alone(tmp_path):
    y, _ = _yard(tmp_path)
    a = y.add_hive("orchard", 2025)
    b = y.add_hive("allotment", 2024)
    _treat(y)(a.hive_id, "formic strip")
    assert y.get(b.hive_id).status == "active" and y.get(b.hive_id).note is None
    assert y.count() == 2
"""
}

_C1_REGRESSION = {
    "test_treatment_regression.py": _HELPER_COMMON
    + """

def test_add_requeen_get_count_unchanged(tmp_path):
    y, path = _yard(tmp_path)
    h = y.add_hive("orchard", 2025)
    assert h.hive_id == "H1" and h.status == "active" and h.note is None
    assert y.get("H1") is h and y.get("H9") is None
    assert y.requeen("H1", 2026).queen_year == 2026
    with pytest.raises(KeyError):
        y.requeen("H9", 2026)
    assert y.count() == 1
    assert path.read_text().splitlines() == ["add H1 orchard 2025", "requeen H1 2026"]
"""
}

_C1_CONTRACT = {
    "raise": {
        "test_treatment_missing.py": _C1_HELPER
        + """

def test_record_treatment_unknown_raises_keyerror(tmp_path):
    y, _ = _yard(tmp_path)
    y.add_hive("orchard", 2025)
    with pytest.raises(KeyError):
        _treat(y)("H404", "formic strip")
"""
    },
    "none": {
        "test_treatment_missing.py": _C1_HELPER
        + """

def test_record_treatment_unknown_returns_none_and_changes_nothing(tmp_path):
    y, path = _yard(tmp_path)
    h = y.add_hive("orchard", 2025)
    before = path.read_text()
    assert _treat(y)("H404", "formic strip") is None
    assert path.read_text() == before
    assert y.count() == 1 and y.get(h.hive_id).status == "active"
"""
    },
}

_C1_SUPPORT = {
    "test_treatment_errors.py": _C1_HELPER
    + """

def test_add_hive_wraps_logbook_oserror(tmp_path, monkeypatch):
    y, _ = _yard(tmp_path)
    monkeypatch.setattr(logbook, "append_line", _boom)
    with pytest.raises(ApiaryError) as ei:
        y.add_hive("orchard", 2025)
    assert isinstance(ei.value.__cause__, OSError)


def test_requeen_wraps_logbook_oserror(tmp_path, monkeypatch):
    y, _ = _yard(tmp_path)
    h = y.add_hive("orchard", 2025)
    monkeypatch.setattr(logbook, "append_line", _boom)
    with pytest.raises(ApiaryError):
        y.requeen(h.hive_id, 2026)


def test_record_treatment_wraps_logbook_oserror(tmp_path, monkeypatch):
    y, _ = _yard(tmp_path)
    h = y.add_hive("orchard", 2025)
    monkeypatch.setattr(logbook, "append_line", _boom)
    with pytest.raises(ApiaryError) as ei:
        _treat(y)(h.hive_id, "formic strip")
    assert isinstance(ei.value.__cause__, OSError)
"""
}

_TREAT_RAISE = """
    def record_treatment(self, hive_id: str, note: str) -> Hive:
        hive = self._hives[hive_id]
        treated = hive.with_changes(status="treated", note=note)
        self._hives[hive_id] = treated
        self._log(f"treat {hive_id} {note}")
        return treated
"""

_TREAT_NONE = """
    def record_treatment(self, hive_id: str, note: str) -> Hive | None:
        hive = self._hives.get(hive_id)
        if hive is None:
            return None
        treated = hive.with_changes(status="treated", note=note)
        self._hives[hive_id] = treated
        self._log(f"treat {hive_id} {note}")
        return treated
"""


def _gold1(state: str) -> str:
    body = _TREAT_RAISE if state == "raise" else _TREAT_NONE
    return _YARD.replace("\n    def get(", body + "\n    def get(", 1)


_REQ1 = Request(
    text=(
        "Add a public method `record_treatment(hive_id, note)` on Yard for the varroa "
        'treatment round: it sets the hive status to "treated", stores the note text on '
        "the hive, writes the logbook line `treat <hive_id> <note>` and returns the "
        "updated hive."
    ),
    target="apiary/yard.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"raise": _gold1("raise"), "none": _gold1("none")},
)

# ----------------------------------------------------------------- checkpoint 2: retire

_C2_HELPER = (
    _HELPER_COMMON
    + """

def _retire(yard):
    fn = getattr(yard, "retire", None) or getattr(yard, "retire_hive", None)
    assert fn is not None, "no retire method found"
    return fn
"""
)

_C2_FUNCTIONAL = {
    "test_retire_functional.py": _C2_HELPER
    + """

def test_retire_sets_status(tmp_path):
    y, _ = _yard(tmp_path)
    h = y.add_hive("orchard", 2025)
    out = _retire(y)(h.hive_id)
    assert out.status == "retired" and out.hive_id == h.hive_id
    assert out.site == "orchard" and out.queen_year == 2025
    assert y.get(h.hive_id).status == "retired"


def test_retire_writes_logbook_line(tmp_path):
    y, path = _yard(tmp_path)
    h = y.add_hive("orchard", 2025)
    _retire(y)(h.hive_id)
    lines = path.read_text().splitlines()
    assert lines[-1] == f"retire {h.hive_id}" and len(lines) == 2


def test_retire_keeps_note_and_other_hives(tmp_path):
    y, _ = _yard(tmp_path)
    a = y.add_hive("orchard", 2025)
    b = y.add_hive("allotment", 2024)
    y.record_treatment(a.hive_id, "formic strip")
    out = _retire(y)(a.hive_id)
    assert out.note == "formic strip"
    assert y.get(b.hive_id).status == "active" and y.count() == 2
"""
}

_C2_REGRESSION = {
    "test_retire_regression.py": _HELPER_COMMON
    + """

def test_add_requeen_treatment_get_unchanged(tmp_path):
    y, path = _yard(tmp_path)
    h = y.add_hive("orchard", 2025)
    assert y.get("H1") is h and y.get("H9") is None
    assert y.record_treatment("H1", "formic strip").status == "treated"
    with pytest.raises(KeyError):
        y.record_treatment("H9", "formic strip")
    assert y.requeen("H1", 2026).queen_year == 2026
    with pytest.raises(KeyError):
        y.requeen("H9", 2026)
    assert y.count() == 1
    assert path.read_text().splitlines() == ["add H1 orchard 2025", "treat H1 formic strip", "requeen H1 2026"]
"""
}

_C2_CONTRACT = {
    "raise": {
        "test_retire_missing.py": _C2_HELPER
        + """

def test_retire_unknown_raises_keyerror(tmp_path):
    y, _ = _yard(tmp_path)
    y.add_hive("orchard", 2025)
    with pytest.raises(KeyError):
        _retire(y)("H404")
"""
    },
    "none": {
        "test_retire_missing.py": _C2_HELPER
        + """

def test_retire_unknown_returns_none_and_changes_nothing(tmp_path):
    y, path = _yard(tmp_path)
    h = y.add_hive("orchard", 2025)
    before = path.read_text()
    assert _retire(y)("H404") is None
    assert path.read_text() == before
    assert y.count() == 1 and y.get(h.hive_id).status == "active"
"""
    },
}

_C2_SUPPORT = {
    "test_retire_errors.py": _C2_HELPER
    + """

def test_add_and_requeen_wrap_logbook_oserror(tmp_path, monkeypatch):
    y, _ = _yard(tmp_path)
    h = y.add_hive("orchard", 2025)
    monkeypatch.setattr(logbook, "append_line", _boom)
    with pytest.raises(ApiaryError):
        y.add_hive("allotment", 2024)
    with pytest.raises(ApiaryError):
        y.requeen(h.hive_id, 2026)


def test_record_treatment_wraps_logbook_oserror(tmp_path, monkeypatch):
    y, _ = _yard(tmp_path)
    h = y.add_hive("orchard", 2025)
    monkeypatch.setattr(logbook, "append_line", _boom)
    with pytest.raises(ApiaryError):
        y.record_treatment(h.hive_id, "formic strip")


def test_retire_wraps_logbook_oserror(tmp_path, monkeypatch):
    y, _ = _yard(tmp_path)
    h = y.add_hive("orchard", 2025)
    monkeypatch.setattr(logbook, "append_line", _boom)
    with pytest.raises(ApiaryError) as ei:
        _retire(y)(h.hive_id)
    assert isinstance(ei.value.__cause__, OSError)
"""
}

_RETIRE_RAISE = """
    def retire(self, hive_id: str) -> Hive:
        hive = self._hives[hive_id]
        retired = hive.with_changes(status="retired")
        self._hives[hive_id] = retired
        self._log(f"retire {hive_id}")
        return retired
"""

_RETIRE_NONE = """
    def retire(self, hive_id: str) -> Hive | None:
        hive = self._hives.get(hive_id)
        if hive is None:
            return None
        retired = hive.with_changes(status="retired")
        self._hives[hive_id] = retired
        self._log(f"retire {hive_id}")
        return retired
"""


def _gold2(state: str) -> str:
    # Built on the checkpoint-1 gold under the state then in force (raise).
    body = _RETIRE_RAISE if state == "raise" else _RETIRE_NONE
    return _gold1("raise").replace("\n    def get(", body + "\n    def get(", 1)


_REQ2 = Request(
    text=(
        "Add a public method `retire(hive_id)` on Yard for colonies that died out or "
        'were combined: it sets the hive status to "retired", stores the updated hive, '
        "writes the logbook line `retire <hive_id>` and returns the updated hive. The "
        "note and queen year are left as they are."
    ),
    target="apiary/yard.py",
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
        "I keep the records for a beekeeping club with about thirty hives spread over "
        "three sites: an orchard, an allotment and a field behind the church. The "
        "regional bee inspector can turn up with a day's notice and wants a written "
        "record per hive of when it was added, when it was requeened and what it was "
        "treated with, and until now that has been a battered notebook in the shed and "
        "a spreadsheet nobody updates. I am writing a small `apiary` package: a Yard "
        "that mints hive ids, a Hive record and an append-only logbook file that is the "
        "thing the inspector actually reads. One line per action, plain text:\n\n```\n"
        "add H1 orchard 2025\nadd H2 allotment 2024\nrequeen H2 2026\n```\n\nCould you "
        "draft the README scope section? Two members want it to track honey yield and "
        "sales, and I would like the first paragraph to say that is out of scope before "
        "it becomes a feature request. The club is twelve people, most of whom will "
        "only ever run a command the treasurer emails them.",
    ),
    Turn(
        "assistant",
        "Here is a scope block that draws the line at the inspector's needs:\n\n```\n## "
        "Scope\napiary is the club's hive register. It keeps Hive records in memory for "
        "the running process and appends one plain-text line per action to a logbook "
        "file the bee inspector can read as-is. It records additions, requeening and "
        "treatments. It does not track honey, sales, equipment or members, and it has no "
        "user interface beyond the command line.\n\n## Non-goals\n- honey yield or "
        "sales\n- equipment inventory\n- multi-user editing\n```\n\nAnd the usage block, "
        "which is also the mental model for the CLI:\n\n```python\nfrom apiary.yard "
        'import Yard\n\nyard = Yard("/home/club/logbook-2026.txt")\nh = yard.add_hive('
        '"orchard", 2025)\nyard.requeen(h.hive_id, 2026)\n```\n\nThe logbook path in '
        "the constructor keeps the season rollover out of the package: the treasurer "
        "starts a new file each spring and the old ones stay readable forever. "
        "The inspector can be handed last year's file without any tooling at all.",
    ),
    Turn(
        "user",
        "About the logbook line format. I went with `<action> <id> [fields]` and free "
        "text at the end where a treatment note goes. The inspector asked whether the "
        "site should appear on every line so she can filter one apiary with `grep`, "
        "and whether dates belong on the line. Here is a realistic fortnight:\n\n```\n"
        "add H1 orchard 2025\nadd H2 allotment 2024\nrequeen H2 2026\nadd H3 church "
        "2025\nrequeen H1 2026\n```\n\nRepeating the site on requeen lines is cheap, "
        "but then every future action needs it and the format stops being minimal. "
        "Dates I am tempted to add now, because 'when was H2 requeened' is exactly "
        "the inspector's question. Is there a rule that decides what goes on a line, "
        "or is this just taste? I would like to settle it before the inspector's visit, "
        "because she will keep whatever format she sees first as the reference copy.",
    ),
    Turn(
        "assistant",
        "There is a rule, and it answers both questions. A line carries the action, "
        "the id, and only the fields that action introduced or changed: `add` carries "
        "site and queen year because they are born there, `requeen` carries the new "
        "year and nothing else. Filtering one site is then a two-step `grep`, which is "
        "fine for thirty hives. Dates are different: they are not a field of the hive, "
        "they are a property of the write, so add them in one place, the private "
        "method every line goes through, and every line gets a timestamp without any "
        "action knowing about it:\n\n```python\ndef _log(self, line: str) -> None:\n"
        "    stamp = date.today().isoformat()\n    logbook.append_line(self."
        '_logbook_path, f"{stamp} {line}")\n```\n\nI would leave the stamp out until '
        "the tests for the plain format are stable, then add it in that one method. "
        "The inspector then gets her dates, the site filter stays a grep, and no action "
        "method ever learns about either.",
    ),
    Turn(
        "user",
        "Here is my test file so far. I want to check the style before writing more; "
        "in particular whether reading the logbook back is reasonable or whether the "
        "`logbook` module should be mocked:\n\n```python\nfrom apiary.yard import Yard"
        "\n\n\ndef test_add_hive_mints_sequential_ids(tmp_path):\n    y = Yard(str("
        'tmp_path / "log.txt"))\n    assert y.add_hive("orchard", 2025).hive_id == '
        '"H1"\n    assert y.add_hive("allotment", 2024).hive_id == "H2"\n\n\ndef '
        'test_add_hive_writes_one_line(tmp_path):\n    path = tmp_path / "log.txt"\n'
        '    y = Yard(str(path))\n    y.add_hive("orchard", 2025)\n    assert '
        'path.read_text().splitlines() == ["add H1 orchard 2025"]\n\n\ndef '
        "test_get_unknown_is_none(tmp_path):\n    assert Yard(str(tmp_path / "
        '"log.txt")).get("H7") is None\n```\n\nA member who codes for a living '
        "says to mock the filesystem.",
    ),
    Turn(
        "assistant",
        "Read the real file. `logbook.append_line` is three lines and the bytes on disk "
        "are the whole point of the package; a mock would prove only that the mock was "
        "called. Keep `tmp_path` so every test starts with an empty logbook. Add one "
        "end-to-end test for requeen, since that is the action the inspector asks about "
        "most:\n\n```python\ndef test_requeen_updates_record_and_logbook(tmp_path):\n"
        '    path = tmp_path / "log.txt"\n    y = Yard(str(path))\n    h = y.add_hive('
        '"orchard", 2025)\n    assert y.requeen(h.hive_id, 2026).queen_year == 2026\n'
        '    assert path.read_text().splitlines()[-1] == "requeen H1 2026"\n```\n\n'
        "Mocking earns its keep only on the failure path, where the write has to fail "
        "on demand; `monkeypatch.setattr(logbook, 'append_line', boom)` does that "
        "without filling a disk, and because the yard imports the module rather than "
        "the function, the patch reaches every method.",
    ),
    Turn(
        "user",
        "That failure path is real. The shed laptop keeps the logbook on an SD card, "
        "and on Sunday the card was full of photos. The treasurer's script died with "
        'this:\n\n```\nTraceback (most recent call last):\n  File "/home/club/'
        'run_yard.py", line 27, in <module>\n    yard.requeen(hive_id, year)\n  File '
        '"/home/club/apiary/yard.py", line 22, in requeen\n    logbook.append_line('
        'self._logbook_path, f"requeen {hive_id} {year}")\n  File "/home/club/apiary/'
        'logbook.py", line 6, in append_line\n    fh.write(line + "\\n")\nOSError: '
        "[Errno 28] No space left on device\n```\n\nThe treasurer is not a programmer "
        "and rang me in a panic. I want callers, meaning that script and a future CLI, "
        "to see one package exception with a plain message they can catch, but I do "
        "not want try/except pasted into every method. What is the cleanest shape?",
    ),
    Turn(
        "assistant",
        "One exception class in the package and one private method every logbook "
        "write goes through:\n\n```python\nclass ApiaryError(Exception):\n    "
        '"""Raised when the hive logbook cannot be written."""\n```\n\n```python\ndef '
        "_log(self, line: str) -> None:\n    try:\n        logbook.append_line(self."
        "_logbook_path, line)\n    except OSError as exc:\n        raise ApiaryError("
        'f"logbook write failed: {exc}") from exc\n```\n\n`add_hive` and `requeen` '
        "call `_log` instead of `logbook.append_line`, so the try/except exists exactly "
        "once, and `from exc` keeps the errno in the chained traceback for whoever "
        "debugs the SD card. The script then catches ApiaryError and prints "
        "'logbook not written, free some space and try again', which is the message "
        "the treasurer needed. The record is stored before the write, so a retry "
        "after freeing space re-logs the same change rather than losing it, which is "
        "the right direction for a record the inspector audits.",
    ),
    Turn(
        "user",
        "That is the convention, and I want it stated: every public Yard method that "
        "writes the logbook wraps any OSError from `logbook.append_line` in ApiaryError, "
        "raised `from` the original, and callers never see a raw OSError. New methods "
        "go through `_log` so this holds automatically.",
    ),
    Turn(
        "assistant",
        "Noted: public Yard methods that touch the logbook surface I/O failures only as "
        "ApiaryError chained from the OSError, never raw. Every new logbook write goes "
        "through `_log`.",
    ),
    Turn(
        "user",
        "Second convention, for unknown ids. Methods that act on a hive by id, like "
        "`requeen`, raise KeyError when the id is not in the yard. A wrong id typed at "
        "the shed laptop is a mistake I want to hear about immediately, not a silent "
        "no-op that leaves the inspector's record wrong. New methods that act on an "
        "id do the same.",
    ),
    Turn(
        "assistant",
        "Understood: id-keyed actions raise KeyError on an unknown hive id, matching "
        "`requeen`. New methods will index `self._hives[hive_id]` directly so nothing "
        "is stored or logged for an id that does not exist.",
    ),
    Turn(
        "user",
        "For later: the inspector would like a per-site summary, hives per site and "
        "the oldest queen at each. I imagine the script doing:\n\n```python\nfor site, "
        'n in yard.hives_by_site().items():\n    print(f"{site}: {n}")\n```\n\nNot '
        "now, just checking the Hive record already has what that needs, and that "
        "queen year as a plain int is enough for 'oldest queen'. "
        "She also asked whether the summary could list retired hives separately.",
    ),
    Turn(
        "assistant",
        "It does: `site` and `queen_year` are both on Hive, so `hives_by_site` is a "
        "`Counter` over `h.site` and the oldest queen per site is a `min` of "
        "`queen_year` over the same grouping. Both only read, so neither touches the "
        "logbook. A plain int year is enough unless the inspector wants months. "
        "Retired hives are a status filter on the same loop.",
    ),
    Turn(
        "user",
        "Right, let's get the autumn treatment round recorded before the inspector's "
        "visit. I will paste the current files with each request so you see the real "
        "state of the code rather than my memory of it.",
    ),
    Turn(
        "assistant",
        "Ready when you are. Send the request and I will return the full yard module.",
    ),
]

_EVENT = (
    "Change of convention, effective now: new Yard methods that act on a hive id return "
    "None when the id is unknown and change nothing (no logbook line, no exception) "
    "instead of raising KeyError. The field tablet app now sends ids read from scanned "
    "hive labels, and a smudged label arrives as junk that must not crash the round. "
    "`requeen` and `record_treatment` keep their current behaviour; only new methods "
    "follow the new rule."
)


def build() -> Session:
    return Session(
        id="S42",
        project="apiary",
        target_family="missing_record",
        support_family="error_surface",
        lifecycle="replacement",
        files=_FILES,
        prefix=_PREFIX,
        states=("raise", "none"),
        state_at=("raise", "none"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10),
        tags={"support_state": "wrap"},
    )
