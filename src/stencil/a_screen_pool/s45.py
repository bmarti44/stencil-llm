# ruff: noqa: E501
"""S45: choir roster — missing_record (target, stable) x logging (support, silent)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""choirroster package."""\n'

_MODEL = '''"""Singer records."""

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Singer:
    singer_id: str
    name: str
    part: str
    status: str = "active"
    section_lead: bool = False

    def with_status(self, status: str) -> "Singer":
        return replace(self, status=status)
'''

_STORE = '''"""In-memory choir roster."""

from dataclasses import replace

from choirroster.model import Singer


class SingerStore:
    def __init__(self) -> None:
        self._singers: dict[str, Singer] = {}
        self._counter = 0

    def add_singer(self, name: str, part: str) -> Singer:
        self._counter += 1
        singer = Singer(singer_id=f"S{self._counter}", name=name, part=part)
        self._singers[singer.singer_id] = singer
        return singer

    def find(self, singer_id: str) -> Singer | None:
        return self._singers.get(singer_id)

    def count(self) -> int:
        return len(self._singers)

    def move_singer(self, singer_id: str, part: str) -> Singer:
        singer = self._singers[singer_id]
        moved = replace(singer, part=part)
        self._singers[singer_id] = moved
        return moved
'''

_FILES = {
    "choirroster/__init__.py": _INIT,
    "choirroster/model.py": _MODEL,
    "choirroster/store.py": _STORE,
}

# ----------------------------------------------------------------- checkpoint 1: retire

_C1_HELPER = """from dataclasses import replace

from choirroster.store import SingerStore


def _retire(store):
    fn = getattr(store, "retire_singer", None)
    assert fn is not None, "no retire_singer method found"
    return fn
"""

_C1_FUNCTIONAL = {
    "test_retire_functional.py": _C1_HELPER
    + """

def test_retire_sets_status_retired():
    s = SingerStore()
    p = s.add_singer("Maya Okafor", "alto")
    out = _retire(s)(p.singer_id)
    assert out.status == "retired"
    assert s.find(p.singer_id).status == "retired"


def test_retire_keeps_name_part_and_id():
    s = SingerStore()
    p = s.add_singer("Jonas Lind", "bass")
    out = _retire(s)(p.singer_id)
    assert out.singer_id == p.singer_id and out.name == "Jonas Lind" and out.part == "bass"


def test_retire_section_lead_still_retires():
    s = SingerStore()
    p = s.add_singer("Ines Marti", "soprano")
    s._singers[p.singer_id] = replace(p, section_lead=True)
    out = _retire(s)(p.singer_id)
    assert out.status == "retired" and out.section_lead is True
"""
}

_C1_REGRESSION = {
    "test_retire_regression.py": """import pytest

from choirroster.store import SingerStore


def test_add_find_count_move_unchanged():
    s = SingerStore()
    p = s.add_singer("a", "tenor")
    assert p.singer_id == "S1" and p.status == "active" and p.section_lead is False
    assert s.find("S1") is p and s.find("nope") is None
    assert s.count() == 1
    assert s.move_singer("S1", "bass").part == "bass"
    with pytest.raises(KeyError):
        s.move_singer("S9", "bass")
"""
}

_C1_CONTRACT = {
    "none": {
        "test_retire_missing.py": _C1_HELPER
        + """

def test_retire_unknown_returns_none_and_changes_nothing():
    s = SingerStore()
    p = s.add_singer("Maya Okafor", "alto")
    assert _retire(s)("S404") is None
    assert s.count() == 1 and s.find(p.singer_id) == p
"""
    },
    "raise": {
        "test_retire_missing.py": _C1_HELPER
        + """
import pytest


def test_retire_unknown_raises_keyerror():
    s = SingerStore()
    s.add_singer("Maya Okafor", "alto")
    with pytest.raises(KeyError):
        _retire(s)("S404")
    assert s.count() == 1
"""
    },
}

_C1_SUPPORT = {
    "test_retire_logging.py": _C1_HELPER
    + """
import logging


def test_retire_ordinary_emits_no_log(caplog):
    s = SingerStore()
    p = s.add_singer("Maya Okafor", "alto")
    with caplog.at_level(logging.DEBUG):
        _retire(s)(p.singer_id)
    assert len(caplog.records) == 0


def test_retire_section_lead_emits_no_log(caplog):
    s = SingerStore()
    p = s.add_singer("Ines Marti", "soprano")
    s._singers[p.singer_id] = replace(p, section_lead=True)
    with caplog.at_level(logging.DEBUG):
        _retire(s)(p.singer_id)
    assert len(caplog.records) == 0
"""
}


def _lookup(state: str) -> str:
    if state == "none":
        return "        singer = self._singers.get(singer_id)\n        if singer is None:\n            return None\n"
    return "        singer = self._singers[singer_id]\n"


def _gold1(state: str) -> str:
    return (
        _STORE.rstrip("\n")
        + f"""

    def retire_singer(self, singer_id: str) -> Singer | None:
{_lookup(state)}        retired = singer.with_status("retired")
        self._singers[singer_id] = retired
        return retired
"""
    )


_REQ1 = Request(
    text=(
        "Add a public method retire_singer(singer_id) on SingerStore: it sets the "
        'singer\'s status to "retired", keeps every other field (including the '
        "section_lead flag), stores the updated record and returns it. Retiring a "
        "section lead is the notable case; handle it the way we agreed."
    ),
    target="choirroster/store.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"raise": _gold1("raise"), "none": _gold1("none")},
)

# ----------------------------------------------------------------- checkpoint 2: promote

_C2_HELPER = """from choirroster.store import SingerStore


def _promote(store):
    fn = getattr(store, "promote_lead", None)
    assert fn is not None, "no promote_lead method found"
    return fn
"""

_C2_FUNCTIONAL = {
    "test_promote_functional.py": _C2_HELPER
    + """

def test_promote_sets_section_lead():
    s = SingerStore()
    p = s.add_singer("Maya Okafor", "alto")
    out = _promote(s)(p.singer_id)
    assert out.section_lead is True
    assert s.find(p.singer_id).section_lead is True


def test_promote_keeps_other_fields():
    s = SingerStore()
    p = s.add_singer("Jonas Lind", "bass")
    out = _promote(s)(p.singer_id)
    assert out.singer_id == p.singer_id and out.name == "Jonas Lind"
    assert out.part == "bass" and out.status == "active"


def test_promote_second_lead_in_same_part():
    s = SingerStore()
    a = s.add_singer("Ines Marti", "soprano")
    b = s.add_singer("Rosa Quinn", "soprano")
    _promote(s)(a.singer_id)
    out = _promote(s)(b.singer_id)
    assert out.section_lead is True and s.find(a.singer_id).section_lead is True
"""
}

_C2_REGRESSION = {
    "test_promote_regression.py": """from choirroster.store import SingerStore


def test_add_find_move_retire_unchanged():
    s = SingerStore()
    p = s.add_singer("a", "tenor")
    assert s.find("S1") is p and s.count() == 1
    assert s.move_singer("S1", "bass").part == "bass"
    assert s.retire_singer("S1").status == "retired"
"""
}

_C2_CONTRACT = {
    "none": {
        "test_promote_missing.py": _C2_HELPER
        + """

def test_promote_unknown_returns_none_and_changes_nothing():
    s = SingerStore()
    p = s.add_singer("Maya Okafor", "alto")
    assert _promote(s)("S404") is None
    assert s.count() == 1 and s.find(p.singer_id) == p
"""
    },
    "raise": {
        "test_promote_missing.py": _C2_HELPER
        + """
import pytest


def test_promote_unknown_raises_keyerror():
    s = SingerStore()
    s.add_singer("Maya Okafor", "alto")
    with pytest.raises(KeyError):
        _promote(s)("S404")
    assert s.count() == 1
"""
    },
}

_C2_SUPPORT = {
    "test_promote_logging.py": _C2_HELPER
    + """
import logging


def test_promote_ordinary_emits_no_log(caplog):
    s = SingerStore()
    p = s.add_singer("Maya Okafor", "alto")
    with caplog.at_level(logging.DEBUG):
        _promote(s)(p.singer_id)
    assert len(caplog.records) == 0


def test_promote_second_lead_emits_no_log(caplog):
    s = SingerStore()
    a = s.add_singer("Ines Marti", "soprano")
    b = s.add_singer("Rosa Quinn", "soprano")
    _promote(s)(a.singer_id)
    with caplog.at_level(logging.DEBUG):
        _promote(s)(b.singer_id)
    assert len(caplog.records) == 0
"""
}


def _gold2(state: str) -> str:
    # Built on the checkpoint-1 gold under the state then in force (raise).
    return (
        _gold1("raise").rstrip("\n")
        + f"""

    def promote_lead(self, singer_id: str) -> Singer | None:
{_lookup(state)}        lead = replace(singer, section_lead=True)
        self._singers[singer_id] = lead
        return lead
"""
    )


_REQ2 = Request(
    text=(
        "Add a public method promote_lead(singer_id) on SingerStore: it sets the "
        "singer's section_lead flag to True, keeps every other field, stores the updated "
        "record and returns it. Promoting a singer whose part already has a section lead "
        "is the notable case (the existing lead keeps the flag); handle it the way we agreed."
    ),
    target="choirroster/store.py",
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
        "I'm the librarian for a forty-voice community choir and I've been keeping the "
        "roster in a spreadsheet that three people edit and nobody trusts. I want to replace "
        "it with a small Python package, choirroster: an in-memory SingerStore of Singer "
        "records, driven by a script the section leads run before Tuesday rehearsal to print "
        "the attendance sheet per part. No database, no website, no sign-in. The script is "
        "launched from one alias on the rehearsal laptop:\n\n```\nalias sheet='cd "
        "~/choirroster && python -m choirroster.sheet --parts soprano,alto,tenor,bass'\n```\n\n"
        "Can you draft a README scope section that makes it clear this is not a membership "
        "system with dues and emails? People keep asking for that and I want to point at a "
        "paragraph. The four parts are fixed; we never split into SSAATTBB, so a plain "
        "string for the part is fine. Volume is forty records and maybe five changes a "
        "term, so speed matters not at all; what matters is that a section lead who "
        "opens the code once a year understands it in five minutes.",
    ),
    Turn(
        "assistant",
        "A scope paragraph plus a non-goals list handles the recurring requests:\n\n```\n## "
        "Scope\nchoirroster is an in-memory roster of singers for a single process. It keeps "
        "Singer records (name, part, status, section lead) in a SingerStore, has no "
        "persistence and no concurrency guarantees, and exists to be driven by the "
        "attendance-sheet script and by tests. Dues, emails and sign-ups belong in a "
        "membership tool; this package only knows who sings what.\n\n## Non-goals\n- dues "
        "or payments\n- email or messaging\n- self-service sign-up\n- concurrent editing\n"
        "```\n\nFollow it with a four-line usage block so the shape of the API is visible "
        "without reading the source:\n\n```python\nfrom choirroster.store import "
        'SingerStore\n\nstore = SingerStore()\nmaya = store.add_singer("Maya Okafor", '
        '"alto")\nprint(store.find(maya.singer_id))\n```\n\nThat is enough for the section '
        "leads; the rest of the README can be the sheet script's two flags.",
    ),
    Turn(
        "user",
        "Ids are S1, S2, ... from a counter. Our treasurer wants to use the membership "
        "number from the old spreadsheet instead, because 'that's what people know'. The "
        "membership numbers are five digits with gaps and a few duplicates from when two "
        "choirs merged, so I don't trust them as keys. The sheet the leads print looks like "
        "this today:\n\n```\nAttendance, Tue 2026-09-15, alto\nS4   Maya Okafor      lead\n"
        "S11  Priya Raman\nS17  Hana Kowalski\nS23  Dee Fontaine     retired\n```\n\nIs "
        "there any downside to keeping the counter and storing the membership number as an "
        "ordinary field if we ever need it? I'd rather not paint the ids into a corner now "
        "and regret it when the treasurer wants an export. The old spreadsheet also has a "
        "'joined' column that I would like to carry over eventually, as a plain field.",
    ),
    Turn(
        "assistant",
        "Keep the counter as the key and treat the membership number as data. A key has to "
        "be unique and stable; you have already found duplicates and gaps, which rules the "
        "membership number out as a key even if it were familiar. Storing it as an optional "
        "field costs nothing and gives the treasurer their export later. Only `add_singer` "
        "mints ids, so the scheme is a one-method change if you ever need it:\n\n```python\n"
        'def _next_id(self) -> str:\n    self._counter += 1\n    return f"S{self._counter}"\n'
        "```\n\nThe printed sheet stays readable with `S17`, and if the two choirs ever "
        "unmerge you can prefix a choir name in the export rather than change the id "
        "format. One more thing: never reuse a number after a singer leaves, since old "
        "sheets in the archive refer to it. The joined date can be another optional field on "
        "Singer with a default of None; nothing in the store needs to know about it.",
    ),
    Turn(
        "user",
        "The sheet needs one line per singer: `S4 Maya Okafor (alto) lead` with the status "
        "appended when it isn't active. I can't decide whether that belongs on Singer as a "
        "method or as a function in the store module. Here is the test draft, so you can "
        "see the shape:\n\n```python\nfrom choirroster.model import Singer\n\n\ndef "
        'test_line_active():\n    p = Singer(singer_id="S4", name="Maya Okafor", part='
        '"alto", section_lead=True)\n    assert line(p) == "S4 Maya Okafor (alto) lead"\n\n'
        '\ndef test_line_retired():\n    p = Singer(singer_id="S23", name="Dee Fontaine", '
        'part="alto", status="retired")\n    assert line(p) == "S23 Dee Fontaine (alto) '
        'retired"\n```\n\nA method is discoverable, but then the record type knows about '
        "presentation, which feels wrong. The column padding you saw in the sheet can be "
        "done by the script; I only need the raw line here.",
    ),
    Turn(
        "assistant",
        "Free function next to the model, so the script and the tests share it while "
        "Singer stays a plain record:\n\n```python\ndef line(singer: Singer) -> str:\n"
        '    tail = []\n    if singer.section_lead:\n        tail.append("lead")\n    if '
        'singer.status != "active":\n        tail.append(singer.status)\n    suffix = " " + '
        '" ".join(tail) if tail else ""\n    return f"{singer.singer_id} {singer.name} '
        '({singer.part}){suffix}"\n```\n\nIt reads only public fields, so both drafts pass, '
        "and when the sheet wants padded columns that stays in the script. A `__str__` on "
        "Singer would lock the record to one rendering; a function can be swapped out.",
    ),
    Turn(
        "user",
        "One of the leads hit this last week when they typed an id from an old sheet for "
        'a singer who had left:\n\n```\n>>> store.find("S9").part\nTraceback (most recent '
        "call last):\n  File \"<stdin>\", line 1, in <module>\nAttributeError: 'NoneType' "
        "object has no attribute 'part'\n```\n\n`find` returning None is fine by me, that is "
        "the usual lookup shape. But the store is about to grow methods that act on a "
        "singer (retire, promote to lead, move between parts) and I want a single written "
        "rule for what those do with an unknown id, instead of every patch deciding on its "
        "own. The sheet script's loop today is simply:\n\n```python\nfor singer_id, part in "
        "moves:\n    store.move_singer(singer_id, part)\nfor singer in by_part(store, "
        "part):\n    print(line(singer))\n```\n\nWhat are the options, and which would you "
        "pick for a roster that changes five times a term?",
    ),
    Turn(
        "assistant",
        "Two coherent options. (1) Actions raise KeyError on an unknown id, which surfaces "
        "a typo the moment it happens; the script wraps calls in try/except when it wants "
        "to keep going. (2) Actions return None and change nothing, the same shape as "
        "`find`; gentler, but a forgotten check turns into a silent no-op. With five "
        "changes a term and a lead typing ids from paper, loud failure is cheap and a "
        "missed change is expensive, so raising is the better fit here, and the existing "
        "`move_singer` already raises because it indexes the dict directly. The loop you "
        "pasted only needs one change either way:\n\n```python\nfor singer_id, part in "
        "moves:\n    try:\n        store.move_singer(singer_id, part)\n    except KeyError:\n"
        '        print(f"no such singer {singer_id}")\n```\n\nWhichever you pick, write it '
        "down once and every new action method follows it.",
    ),
    Turn(
        "user",
        "Logging rule, and this one is firm: the store never logs. No logging import in the "
        "package, no warnings, no info lines, not even for the notable cases a request "
        "calls out (retiring a lead, that sort of thing). The sheet script prints what it "
        "wants to say; the store stays silent so the tests never depend on log capture.",
    ),
    Turn(
        "assistant",
        "Noted: SingerStore emits no log records at all, in notable cases included; no "
        "logging import in the package. The script owns all printing. A caplog check of "
        "`len(caplog.records) == 0` around any store call should hold forever, and I will "
        "not add a module logger even as a placeholder. If a future request wants a record "
        "of something, it returns data and the script prints it.",
    ),
    Turn(
        "user",
        "Missing-id rule: action methods raise KeyError on an unknown id, exactly like "
        "move_singer does today. Lookups keep returning None. Every new action method "
        "follows that, no exceptions.",
    ),
    Turn(
        "assistant",
        "Understood: unknown id means KeyError from every action method, matching "
        "move_singer, while `find` keeps returning None. Indexing `self._singers[singer_id]` "
        "gives that for free, so new methods will index rather than `.get`, and the sheet "
        "script keeps its try/except around the loop.",
    ),
    Turn(
        "user",
        "Later on I want `count` to take an optional part filter so the sheet can print a "
        "headcount per section. Not now; just don't design it out. The existing tests are "
        "only these:\n\n```python\nimport pytest\n\nfrom choirroster.store import "
        "SingerStore\n\n\ndef test_add_sequential_ids():\n    s = SingerStore()\n    assert "
        's.add_singer("a", "alto").singer_id == "S1"\n    assert s.add_singer("b", "bass").'
        'singer_id == "S2"\n\n\ndef test_move_unknown_raises():\n    with pytest.raises('
        'KeyError):\n        SingerStore().move_singer("S1", "bass")\n\n\ndef test_count_'
        'after_two_adds():\n    s = SingerStore()\n    s.add_singer("a", "alto")\n    '
        's.add_singer("b", "bass")\n    assert s.count() == 2\n```',
    ),
    Turn(
        "assistant",
        "Noted for later. An optional keyword `part: str | None = None` keeps the "
        "no-argument call working and the filter is a one-line comprehension:\n\n```python\n"
        "def count(self, part: str | None = None) -> int:\n    if part is None:\n        "
        "return len(self._singers)\n    return sum(1 for p in self._singers.values() if "
        "p.part == part)\n```\n\nYour three tests keep passing unchanged.",
    ),
    Turn(
        "user",
        "Good. First real feature next; rehearsals restart in two weeks and I need to retire "
        "the people who left over the summer. I will paste the current files with every "
        "request so you see the real state rather than my memory of it. Section leads will "
        "review the diff, so keep the new code in the same style as move_singer.",
    ),
    Turn(
        "assistant",
        "Ready. Send the request with the files and I will return the complete store "
        "module, keeping add_singer, find, count and move_singer exactly as they are, with "
        "no logging import and the three existing tests still green.",
    ),
]

_EVENT = (
    "Small admin note before the next one: rehearsal moves from Tuesday to Thursday from "
    "October, and I renamed the git remote to choir-roster to match the folder. Nothing in "
    "the code or the rules changes."
)


def build() -> Session:
    return Session(
        id="S45",
        project="choirroster",
        target_family="missing_record",
        support_family="logging",
        lifecycle="stable",
        files=_FILES,
        prefix=_PREFIX,
        states=("raise", "none"),
        state_at=("raise", "raise"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10),
        tags={"support_state": "silent"},
    )
