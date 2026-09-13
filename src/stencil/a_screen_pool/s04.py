# ruff: noqa: E501
"""S04: parking permits — naming (target, reinstatement) x return_shape (support)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""permitlot package."""\n'

_MODEL = '''"""Permit records."""

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Permit:
    permit_id: str
    plate: str
    zone: str
    expires_day: int
    status: str = "active"

    def with_status(self, status: str) -> "Permit":
        return replace(self, status=status)
'''

_LOT = '''"""In-memory permit register for one residents' lot."""

from permitlot.model import Permit


def normalize_plate(plate: str) -> str:
    return plate.replace(" ", "").upper()


class PermitLot:
    def __init__(self) -> None:
        self._permits: dict[str, Permit] = {}
        self._counter = 0

    def issue_permit(self, plate: str, zone: str, expires_day: int) -> Permit:
        self._counter += 1
        permit = Permit(f"P{self._counter}", normalize_plate(plate), zone, expires_day)
        self._permits[permit.permit_id] = permit
        return permit

    def find(self, permit_id: str) -> Permit | None:
        return self._permits.get(permit_id)

    def count(self) -> int:
        return len(self._permits)
'''

_FILES = {
    "permitlot/__init__.py": _INIT,
    "permitlot/model.py": _MODEL,
    "permitlot/lot.py": _LOT,
}

# ----------------------------------------------------------------- checkpoint 1: revoke

_C1_HELPER = """from permitlot.lot import PermitLot
from permitlot.model import Permit


def _revoke(lot):
    fn = getattr(lot, "revoke_permit", None) or getattr(lot, "permit_revoke", None)
    assert fn is not None, "no revoke method found"
    return fn
"""

_C1_FUNCTIONAL = {
    "test_revoke_functional.py": _C1_HELPER
    + """

def test_revoke_sets_status_revoked():
    lot = PermitLot()
    p = lot.issue_permit("ab12 cde", "north", 120)
    out = _revoke(lot)(p.permit_id)
    assert out.status == "revoked"
    assert lot.find(p.permit_id).status == "revoked"


def test_revoke_keeps_plate_zone_expiry():
    lot = PermitLot()
    p = lot.issue_permit("zz9 abc", "south", 45)
    out = _revoke(lot)(p.permit_id)
    assert out.permit_id == p.permit_id
    assert out.plate == "ZZ9ABC" and out.zone == "south" and out.expires_day == 45


def test_revoke_unknown_raises_keyerror():
    lot = PermitLot()
    try:
        _revoke(lot)("P999")
    except KeyError:
        return
    raise AssertionError("expected KeyError for an unknown permit")
"""
}

_C1_REGRESSION = {
    "test_revoke_regression.py": """from permitlot.lot import PermitLot, normalize_plate


def test_issue_find_normalize_unchanged():
    lot = PermitLot()
    p = lot.issue_permit("ab12 cde", "north", 120)
    assert p.permit_id == "P1" and p.plate == "AB12CDE" and p.status == "active"
    assert lot.find("P1") is p
    assert lot.find("nope") is None
    assert lot.count() == 1
    assert normalize_plate(" x y 1 ") == "XY1"
"""
}

_C1_CONTRACT = {
    "verb_noun": {
        "test_revoke_naming.py": """from permitlot.lot import PermitLot


def test_revoke_is_verb_noun():
    assert hasattr(PermitLot, "revoke_permit")
    assert not hasattr(PermitLot, "permit_revoke")
"""
    },
    "noun_verb": {
        "test_revoke_naming.py": """from permitlot.lot import PermitLot


def test_revoke_is_noun_verb():
    assert hasattr(PermitLot, "permit_revoke")
    assert not hasattr(PermitLot, "revoke_permit")
"""
    },
}

_C1_SUPPORT = {
    "test_revoke_shape.py": _C1_HELPER
    + """

def test_revoke_returns_permit_dataclass_not_dict():
    lot = PermitLot()
    p = lot.issue_permit("ab12 cde", "north", 120)
    out = _revoke(lot)(p.permit_id)
    assert isinstance(out, Permit)
    assert not isinstance(out, dict)
"""
}


def _gold1(name: str) -> str:
    return (
        _LOT.rstrip("\n")
        + f"""

    def {name}(self, permit_id: str) -> Permit:
        permit = self._permits[permit_id]
        revoked = permit.with_status("revoked")
        self._permits[permit_id] = revoked
        return revoked
"""
    )


_REQ1 = Request(
    text=(
        "Add a public method on PermitLot that revokes a permit by id: it sets the status "
        'to "revoked", stores the updated permit and returns it. An unknown id raises '
        "KeyError."
    ),
    target="permitlot/lot.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"verb_noun": _gold1("revoke_permit"), "noun_verb": _gold1("permit_revoke")},
)

# ----------------------------------------------------------------- checkpoint 2: extend

_C2_HELPER = """from permitlot.lot import PermitLot
from permitlot.model import Permit


def _extend(lot):
    fn = getattr(lot, "extend_permit", None) or getattr(lot, "permit_extend", None)
    assert fn is not None, "no extend method found"
    return fn
"""

_C2_FUNCTIONAL = {
    "test_extend_functional.py": _C2_HELPER
    + """

def test_extend_adds_days():
    lot = PermitLot()
    p = lot.issue_permit("ab12 cde", "north", 120)
    out = _extend(lot)(p.permit_id, 30)
    assert out.expires_day == 150
    assert lot.find(p.permit_id).expires_day == 150


def test_extend_twice_accumulates_and_keeps_rest():
    lot = PermitLot()
    p = lot.issue_permit("zz9 abc", "south", 10)
    _extend(lot)(p.permit_id, 5)
    out = _extend(lot)(p.permit_id, 7)
    assert out.expires_day == 22
    assert out.plate == "ZZ9ABC" and out.zone == "south" and out.status == "active"


def test_extend_unknown_raises_keyerror():
    lot = PermitLot()
    try:
        _extend(lot)("P999", 30)
    except KeyError:
        return
    raise AssertionError("expected KeyError for an unknown permit")
"""
}

_C2_REGRESSION = {
    "test_extend_regression.py": """from permitlot.lot import PermitLot


def _revoke(lot):
    return getattr(lot, "revoke_permit", None) or getattr(lot, "permit_revoke", None)


def test_issue_find_revoke_unchanged():
    lot = PermitLot()
    p = lot.issue_permit("ab12 cde", "north", 120)
    assert lot.find("P1") is p and lot.count() == 1 and p.plate == "AB12CDE"
    assert _revoke(lot)(p.permit_id).status == "revoked"
"""
}

_C2_CONTRACT = {
    "verb_noun": {
        "test_extend_naming.py": """from permitlot.lot import PermitLot


def test_extend_is_verb_noun():
    assert hasattr(PermitLot, "extend_permit")
    assert not hasattr(PermitLot, "permit_extend")
"""
    },
    "noun_verb": {
        "test_extend_naming.py": """from permitlot.lot import PermitLot


def test_extend_is_noun_verb():
    assert hasattr(PermitLot, "permit_extend")
    assert not hasattr(PermitLot, "extend_permit")
"""
    },
}

_C2_SUPPORT = {
    "test_extend_shape.py": _C2_HELPER
    + """

def test_extend_returns_permit_dataclass_not_dict():
    lot = PermitLot()
    p = lot.issue_permit("ab12 cde", "north", 120)
    out = _extend(lot)(p.permit_id, 30)
    assert isinstance(out, Permit)
    assert not isinstance(out, dict)
"""
}


def _gold2(name: str) -> str:
    # Built on the checkpoint-1 gold under the state then in force (noun_verb).
    body = (
        _gold1("permit_revoke").rstrip("\n")
        + f"""

    def {name}(self, permit_id: str, days: int) -> Permit:
        permit = self._permits[permit_id]
        extended = replace(permit, expires_day=permit.expires_day + days)
        self._permits[permit_id] = extended
        return extended
"""
    )
    return body.replace(
        "from permitlot.model import Permit\n",
        "from dataclasses import replace\n\nfrom permitlot.model import Permit\n",
        1,
    )


_REQ2 = Request(
    text=(
        "Add a public method on PermitLot that extends a permit: it takes the permit id "
        "and a number of days, adds the days to the permit's expiry day, stores the "
        "updated permit and returns it. An unknown id raises KeyError."
    ),
    target="permitlot/lot.py",
    functional_tests=_C2_FUNCTIONAL,
    regression_tests=_C2_REGRESSION,
    contract_tests=_C2_CONTRACT,
    support_tests=_C2_SUPPORT,
    gold={"verb_noun": _gold2("extend_permit"), "noun_verb": _gold2("permit_extend")},
)

# ----------------------------------------------------------------- prefix (16 turns)

_PREFIX = [
    Turn(
        "user",
        "I'm putting together a small package for the residents' parking permits at our "
        "building. The lot office has a spreadsheet, a laminated list on the barrier post "
        "and a lot of arguments. I want an in-memory PermitLot with Permit records, "
        "driven by two scripts: one that prints the currently valid plates for the guard, "
        "one that lists permits expiring in the next week. Persistence is a JSON dump the "
        "office runs nightly; no database, no web page. The guard's script is only:\n\n```"
        "\n0 6 * * * cd /opt/permitlot && python -m permitlot.valid --zone north > "
        "/var/lib/permitlot/north.txt\n```\n\nCan you sketch what the README should say "
        "about scope? The office manager has already asked whether it will 'do the "
        "payments' and I want the answer in writing before anyone assumes otherwise. There "
        "are about two hundred permits across two zones, north and south, and the office "
        "issues or renews maybe five a day, so performance is irrelevant; what matters is "
        "that the two office staff can read the code and not be surprised by it.",
    ),
    Turn(
        "assistant",
        "A short scope section plus explicit non-goals is what to show the office manager:"
        "\n\n```\n## Scope\npermitlot is an in-memory register of parking permits for a "
        "single lot in a single process. It keeps Permit records in a PermitLot, has no "
        "persistence beyond the nightly JSON dump and no concurrency guarantees, and is "
        "meant for the office scripts, not as a service.\n\n## Non-goals\n- payments or "
        "invoicing\n- barrier or camera integration\n- resident accounts or logins\n- "
        "multiple lots in one register\n```\n\nThe non-goals list is what people actually "
        "read. A usage block sets the tone for the API:\n\n```python\nfrom permitlot.lot "
        'import PermitLot\n\nlot = PermitLot()\np = lot.issue_permit("AB12 CDE", "north", '
        "expires_day=120)\nprint(lot.find(p.permit_id))\n```\n\nIf payments ever land they "
        "belong in a separate package that references permit ids, not in this one. Add a "
        "`Requires Python 3.11+` line too; the office PC is on whatever came with it and "
        "`str | None` will otherwise be the first support call.",
    ),
    Turn(
        "user",
        "Good. I'm representing expiry as a day number (days since the office's epoch, "
        "1 January this year) rather than a datetime, because the scripts only ever ask "
        "'is it still valid today' and 'does it expire within seven days', and I don't "
        "want timezone handling in a package this small. The nightly dump looks like:\n\n"
        '```json\n{\n  "lot": "elm-court",\n  "dumped_at": "2026-09-14T23:00:00",\n'
        '  "epoch": "2026-01-01",\n  "permits": [\n    {"permit_id": "P1", "plate": '
        '"AB12CDE", "zone": "north", "expires_day": 120, "status": "active"},\n'
        '    {"permit_id": "P2", "plate": "ZZ9ABC", "zone": "south", "expires_day": 45, '
        '"status": "expired"}\n  ]\n}\n```\n\nIs a bare int going to bite me later, or is '
        "it fine as long as the epoch is written into the dump?",
    ),
    Turn(
        "assistant",
        "A day number is fine for this package as long as three things hold: the epoch is "
        "written into every dump (you already do), the conversion lives in one helper, and "
        "nothing in the package ever calls `date.today()` itself. Have the scripts compute "
        "today's day number once and pass it in:\n\n```python\nfrom datetime import date\n"
        "\nEPOCH = date(2026, 1, 1)\n\n\ndef day_number(d: date) -> int:\n    return "
        "(d - EPOCH).days\n```\n\nThen `lot.valid_on(day)` and `lot.expiring_within(day, "
        "7)` are pure functions of their arguments, which keeps the tests deterministic "
        "and means the guard's script and the expiry script cannot disagree about what "
        "'today' is. Year rollover is a script problem, not a package problem: bump the "
        "epoch in the dump and renumber on load. Ints also sort and compare without any "
        "tz surprises, which is the actual reason to prefer them here. Write the epoch "
        "into the README next to the dump format so nobody guesses it.",
    ),
    Turn(
        "user",
        "Plates are a mess in the spreadsheet: `AB12 CDE`, `ab12cde`, `AB12  CDE` with two "
        "spaces. I added `normalize_plate` in lot.py so `issue_permit` stores the canonical "
        "form. Should the lookup script normalize too, or should there be a `find_by_plate` "
        "that does it? Here is my test draft for the helper, so you can see what I "
        "consider canonical:\n\n```python\nimport pytest\n\nfrom permitlot.lot import "
        'normalize_plate\n\n\n@pytest.mark.parametrize("raw", ["AB12 CDE", "ab12cde", '
        '"AB12  CDE", " ab12 cde "])\ndef test_normalize_plate_collapses(raw):\n    assert '
        'normalize_plate(raw) == "AB12CDE"\n\n\ndef test_normalize_plate_keeps_digits():\n'
        '    assert normalize_plate("zz9 abc") == "ZZ9ABC"\n```\n\nThe guard only ever sees '
        "the canonical form on the printed list, so whatever we decide here is what he "
        "compares against by eye when a car pulls up.",
    ),
    Turn(
        "assistant",
        "Both. Keep `normalize_plate` public so scripts can canonicalise input at the "
        "edge, and give the lot a plate lookup that normalises internally so nobody has to "
        "remember:\n\n```python\ndef find_by_plate(self, plate: str) -> Permit | None:\n"
        "    wanted = normalize_plate(plate)\n    for permit in self._permits.values():\n"
        "        if permit.plate == wanted:\n            return permit\n    return None\n"
        "```\n\nA linear scan is fine at a few hundred permits; if the lot grows, keep a "
        "plate index next to the id dict. Your parametrised tests pass against the current "
        "helper as written. One more case worth adding is a plate with a hyphen "
        "(`AB12-CDE`), since the DVLA style and the office style differ; decide now whether "
        "hyphens are stripped and pin it with a test:\n\n```python\ndef "
        'test_normalize_plate_strips_hyphen():\n    assert normalize_plate("AB12-CDE") == '
        '"AB12CDE"\n```\n\nThe helper then becomes `plate.replace(" ", "").replace("-", '
        '"").upper()`, still one line.',
    ),
    Turn(
        "user",
        "We'll strip hyphens; I'll add the test. Next: should `find` raise on a missing id "
        "or return None? Right now it returns None and the caller checks. I want one rule "
        "for the office staff who read this code. This is what one of them hit assuming "
        '`find` raises:\n\n```\n>>> lot.find("P7").plate\nTraceback (most recent call '
        "last):\n  File \"<stdin>\", line 1, in <module>\nAttributeError: 'NoneType' object "
        "has no attribute 'plate'\n```\n\nThe usual None-propagation trap; he had typed P7 "
        "for P1 and concluded the dump had not loaded. The office log from that morning, "
        "for colour:\n\n```\n2026-09-10 08:01:14 INFO  permitlot: loaded dump "
        "2026-09-09.json (203 permits)\n2026-09-10 08:27:40 ERROR shell: AttributeError: 'NoneType' "
        "object has no attribute 'plate'\n```",
    ),
    Turn(
        "assistant",
        "Returning None from `find` is the usual lookup contract: the name says 'try to "
        "find', and callers branch on the result. Methods that *act* on a permit "
        "(revoking, extending, transferring) are different: acting on an id that does not "
        "exist is a caller bug, so raising KeyError there is the clearer signal and it "
        "surfaces in tests immediately. So the rule is: lookups return None, actions raise "
        "KeyError. Keep `find` as it is, and callers that need a hard failure can wrap it:"
        "\n\n```python\ndef require(lot, permit_id):\n    permit = lot.find(permit_id)\n"
        "    if permit is None:\n        raise KeyError(permit_id)\n    return permit\n```"
        "\n\nThe traceback you pasted becomes a KeyError('P7') at the call site, which "
        "says the id was wrong rather than the dump. The log shows the load succeeded "
        "twenty minutes earlier with 203 permits, which is the other clue he would have "
        "had if the error had named the key.",
    ),
    Turn(
        "user",
        "Agreed, actions raise KeyError on unknown ids. Two conventions to fix now so the "
        "code stays uniform. First: public PermitLot methods always return Permit "
        "dataclass instances, never dicts or tuples, even for convenience. The old "
        "spreadsheet exporter returned dicts and every caller grew a `.get('plate')`.",
    ),
    Turn(
        "assistant",
        "Noted: every public PermitLot method returns Permit instances (or None from "
        "lookups), never dicts or tuples. Callers stay on one type, and we can add fields "
        "to Permit without breaking them.",
    ),
    Turn(
        "user",
        "Second: method naming. Public lot methods are named verb_noun, like "
        "issue_permit. Anything new follows that pattern so the API reads as a list of "
        "things the office does to a permit.",
    ),
    Turn(
        "assistant",
        "Understood: verb_noun for public PermitLot methods, matching issue_permit. I will "
        "name new methods that way; private helpers and module-level functions like "
        "normalize_plate stay as they are. If a verb is ambiguous, I will use the verb the "
        "request itself uses.",
    ),
    Turn(
        "user",
        "Update on naming: I showed the API to the lot-office team and they want it to "
        "read like the columns on their permit form, noun first. So, effective now, new "
        "public PermitLot methods are named noun_verb (permit_revoke, permit_extend "
        "style), not verb_noun. Existing names like issue_permit stay as they are; only "
        "new methods follow the new pattern.",
    ),
    Turn(
        "assistant",
        "Understood: from now on new public PermitLot methods are noun_verb, for example "
        "permit_revoke, while issue_permit and find keep their current names. I will "
        "follow that for anything I add.",
    ),
    Turn(
        "user",
        "For reference, the tests that exist today are only these:\n\n```python\nfrom "
        "permitlot.lot import PermitLot\n\n\ndef test_issue_assigns_sequential_ids():\n"
        '    lot = PermitLot()\n    assert lot.issue_permit("a", "north", 1).permit_id == '
        '"P1"\n    assert lot.issue_permit("b", "north", 1).permit_id == "P2"\n\n\ndef '
        'test_find_missing_returns_none():\n    assert PermitLot().find("P1") is None\n```'
        "\n\nLet's get the first real feature in; I will paste the current files with each "
        "request so you always see the real state.",
    ),
    Turn(
        "assistant",
        "Ready when you are. Send the request and I will return the full lot module.",
    ),
]

_EVENT = (
    "Naming again, sorry: the office manager overruled the team and we are going back to "
    "the original convention. Effective now, new public PermitLot methods are named "
    "verb_noun (revoke_permit, extend_permit style); the noun_verb change is withdrawn. "
    "Existing method names stay as they are, whatever pattern they follow."
)


def build() -> Session:
    return Session(
        id="S04",
        project="permitlot",
        target_family="naming",
        support_family="return_shape",
        lifecycle="reinstatement",
        files=_FILES,
        prefix=_PREFIX,
        states=("verb_noun", "noun_verb"),
        state_at=("noun_verb", "verb_noun"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10, 12),
    )
