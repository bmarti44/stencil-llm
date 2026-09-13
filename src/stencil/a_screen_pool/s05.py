# ruff: noqa: E501
"""S05: gym memberships — naming (target, stable) x return_shape (support)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""gymroll package."""\n'

_MODEL = '''"""Membership records."""

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Member:
    member_id: str
    name: str
    plan: str
    status: str = "active"
    renewals: int = 0

    def with_status(self, status: str) -> "Member":
        return replace(self, status=status)
'''

_ROLL = '''"""In-memory membership roll."""

from gymroll.model import Member

PLANS = ("monthly", "annual", "student")


class MemberRoll:
    def __init__(self) -> None:
        self._members: dict[str, Member] = {}
        self._counter = 0

    def member_enroll(self, name: str, plan: str = "monthly") -> Member:
        self._counter += 1
        member = Member(member_id=f"M{self._counter}", name=name, plan=plan)
        self._members[member.member_id] = member
        return member

    def find(self, member_id: str) -> Member | None:
        return self._members.get(member_id)

    def count(self) -> int:
        return len(self._members)
'''

_FILES = {
    "gymroll/__init__.py": _INIT,
    "gymroll/model.py": _MODEL,
    "gymroll/roll.py": _ROLL,
}

# ----------------------------------------------------------------- checkpoint 1: freeze

_C1_HELPER = """from gymroll.model import Member
from gymroll.roll import MemberRoll


def _freeze(roll):
    fn = getattr(roll, "member_freeze", None) or getattr(roll, "freeze_member", None)
    assert fn is not None, "no freeze method found"
    return fn
"""

_C1_FUNCTIONAL = {
    "test_freeze_functional.py": _C1_HELPER
    + """

from dataclasses import replace


def test_freeze_sets_status_frozen():
    r = MemberRoll()
    m = r.member_enroll("Priya", "annual")
    other = r.member_enroll("Ines", "monthly")
    out = _freeze(r)(m.member_id)
    assert out.status == "frozen"
    assert r.find(m.member_id).status == "frozen"
    assert r.find(other.member_id) == other
    assert r.count() == 2


def test_freeze_keeps_name_plan_renewals():
    r = MemberRoll()
    m = r.member_enroll("Tomasz", "student")
    other = r.member_enroll("Ines", "monthly")
    out = _freeze(r)(m.member_id)
    assert out.member_id == m.member_id
    assert out.name == "Tomasz" and out.plan == "student" and out.renewals == 0
    assert r.find(other.member_id) == other
    assert r.count() == 2


def test_freeze_keeps_nondefault_attributes_of_both_records():
    # two members, both holding NON-DEFAULT values for the defaulted
    # attributes (status, renewals); freezing one must touch nothing else
    r = MemberRoll()
    a = r.member_enroll("Priya", "annual")
    b = r.member_enroll("Ines", "monthly")
    r._members[a.member_id] = replace(r.find(a.member_id), renewals=3)
    seeded = replace(r.find(b.member_id), renewals=7, status="frozen")
    r._members[b.member_id] = seeded
    out = _freeze(r)(a.member_id)
    assert out.status == "frozen" and out.renewals == 3
    got = r.find(a.member_id)
    assert got.renewals == 3 and got.name == "Priya" and got.plan == "annual"
    kept = r.find(b.member_id)
    assert kept is not None and kept.renewals == 7
    assert kept.status == "frozen" and kept.name == "Ines"
    assert kept.plan == "monthly" and kept == seeded
    assert r.count() == 2


def test_freeze_unknown_raises_keyerror():
    r = MemberRoll()
    r.member_enroll("Priya", "annual")
    r.member_enroll("Ines", "monthly")
    try:
        _freeze(r)("M999")
    except KeyError:
        assert r.count() == 2
        return
    raise AssertionError("expected KeyError for an unknown member")
"""
}

_C1_REGRESSION = {
    "test_freeze_regression.py": """from gymroll.roll import PLANS, MemberRoll


def test_enroll_and_find_unchanged():
    r = MemberRoll()
    m = r.member_enroll("Priya")
    assert m.member_id == "M1" and m.plan == "monthly" and m.status == "active"
    assert r.find("M1") is m
    assert r.find("nope") is None
    assert r.count() == 1
    assert PLANS == ("monthly", "annual", "student")


def test_enroll_keeps_every_earlier_member():
    r = MemberRoll()
    a = r.member_enroll("Priya", "annual")
    b = r.member_enroll("Ines", "monthly")
    c = r.member_enroll("Tomasz", "student")
    assert r.find("M1") is a and r.find("M2") is b and r.find("M3") is c
    assert [m.plan for m in (a, b, c)] == ["annual", "monthly", "student"]
    assert r.count() == 3
"""
}

_C1_CONTRACT = {
    "noun_verb": {
        "test_freeze_naming.py": """from gymroll.roll import MemberRoll


def test_freeze_is_noun_verb():
    assert hasattr(MemberRoll, "member_freeze")
    assert not hasattr(MemberRoll, "freeze_member")
"""
    },
    "verb_noun": {
        "test_freeze_naming.py": """from gymroll.roll import MemberRoll


def test_freeze_is_verb_noun():
    assert hasattr(MemberRoll, "freeze_member")
    assert not hasattr(MemberRoll, "member_freeze")
"""
    },
}

_C1_SUPPORT = {
    "test_freeze_shape.py": _C1_HELPER
    + """

def test_freeze_returns_member_dataclass_not_dict():
    r = MemberRoll()
    m = r.member_enroll("Priya")
    out = _freeze(r)(m.member_id)
    assert isinstance(out, Member)
    assert not isinstance(out, dict)
"""
}


def _gold1(name: str) -> str:
    return (
        _ROLL.rstrip("\n")
        + f"""

    def {name}(self, member_id: str) -> Member:
        member = self._members[member_id]
        frozen = member.with_status("frozen")
        self._members[member_id] = frozen
        return frozen
"""
    )


_REQ1 = Request(
    text=(
        "Add a public method on MemberRoll that freezes a membership by member id: it sets "
        'the status to "frozen", stores the updated member and returns it. An unknown id '
        "raises KeyError."
    ),
    target="gymroll/roll.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"noun_verb": _gold1("member_freeze"), "verb_noun": _gold1("freeze_member")},
)

# ----------------------------------------------------------------- checkpoint 2: renew

_C2_HELPER = """from gymroll.model import Member
from gymroll.roll import MemberRoll


def _renew(roll):
    fn = getattr(roll, "member_renew", None) or getattr(roll, "renew_member", None)
    assert fn is not None, "no renew method found"
    return fn


def _freeze(roll):
    return getattr(roll, "member_freeze", None) or getattr(roll, "freeze_member", None)
"""

_C2_FUNCTIONAL = {
    "test_renew_functional.py": _C2_HELPER
    + """

def test_renew_increments_renewals():
    r = MemberRoll()
    m = r.member_enroll("Priya", "annual")
    other = r.member_enroll("Ines", "monthly")
    out = _renew(r)(m.member_id)
    assert out.renewals == 1 and out.status == "active"
    assert r.find(m.member_id).renewals == 1
    assert r.find(other.member_id) == other
    assert r.count() == 2


def test_renew_reactivates_frozen_and_accumulates():
    r = MemberRoll()
    m = r.member_enroll("Tomasz", "student")
    other = r.member_enroll("Ines", "monthly")
    out = _renew(r)(m.member_id)
    assert out.renewals == 1
    _freeze(r)(m.member_id)
    out = _renew(r)(m.member_id)
    assert out.status == "active" and out.renewals == 2
    assert out.name == "Tomasz" and out.plan == "student"
    assert r.find(other.member_id) == other
    assert r.count() == 2


def test_renew_leaves_a_nondefault_neighbour_untouched():
    # two members; the neighbour holds NON-DEFAULT values for both defaulted
    # attributes (status "frozen", renewals 1) and the operated record holds a
    # non-default renewal count before the renewal under test
    r = MemberRoll()
    a = r.member_enroll("Priya", "annual")
    b = r.member_enroll("Ines", "monthly")
    _renew(r)(b.member_id)
    _freeze(r)(b.member_id)
    _renew(r)(a.member_id)
    out = _renew(r)(a.member_id)
    assert out.renewals == 2 and out.status == "active"
    assert r.find(a.member_id).renewals == 2
    kept = r.find(b.member_id)
    assert kept is not None and kept.status == "frozen" and kept.renewals == 1
    assert kept.name == "Ines" and kept.plan == "monthly"
    assert r.count() == 2


def test_renew_unknown_raises_keyerror():
    r = MemberRoll()
    r.member_enroll("Priya", "annual")
    r.member_enroll("Ines", "monthly")
    try:
        _renew(r)("M999")
    except KeyError:
        assert r.count() == 2
        return
    raise AssertionError("expected KeyError for an unknown member")
"""
}

_C2_REGRESSION = {
    "test_renew_regression.py": """from gymroll.roll import MemberRoll


def _freeze(roll):
    return getattr(roll, "member_freeze", None) or getattr(roll, "freeze_member", None)


def test_enroll_find_freeze_unchanged():
    r = MemberRoll()
    m = r.member_enroll("Priya", "annual")
    assert r.find("M1") is m and r.count() == 1
    assert _freeze(r)(m.member_id).status == "frozen"


def test_freeze_keeps_the_other_members_and_the_count():
    r = MemberRoll()
    a = r.member_enroll("Priya", "annual")
    b = r.member_enroll("Ines", "monthly")
    assert _freeze(r)(b.member_id).status == "frozen"
    kept = r.find(a.member_id)
    assert kept is not None and kept == a
    assert kept.status == "active" and kept.renewals == 0
    assert kept.name == "Priya" and kept.plan == "annual"
    assert r.find(b.member_id).status == "frozen"
    assert r.count() == 2
"""
}

_C2_CONTRACT = {
    "noun_verb": {
        "test_renew_naming.py": """from gymroll.roll import MemberRoll


def test_renew_is_noun_verb():
    assert hasattr(MemberRoll, "member_renew")
    assert not hasattr(MemberRoll, "renew_member")
"""
    },
    "verb_noun": {
        "test_renew_naming.py": """from gymroll.roll import MemberRoll


def test_renew_is_verb_noun():
    assert hasattr(MemberRoll, "renew_member")
    assert not hasattr(MemberRoll, "member_renew")
"""
    },
}

_C2_SUPPORT = {
    "test_renew_shape.py": _C2_HELPER
    + """

def test_renew_returns_member_dataclass_not_dict():
    r = MemberRoll()
    m = r.member_enroll("Priya")
    out = _renew(r)(m.member_id)
    assert isinstance(out, Member)
    assert not isinstance(out, dict)
"""
}


def _gold2(name: str) -> str:
    # Built on the checkpoint-1 gold under the state then in force (noun_verb).
    body = (
        _gold1("member_freeze").rstrip("\n")
        + f"""

    def {name}(self, member_id: str) -> Member:
        member = self._members[member_id]
        renewed = replace(member, status="active", renewals=member.renewals + 1)
        self._members[member_id] = renewed
        return renewed
"""
    )
    return body.replace(
        "from gymroll.model import Member\n",
        "from dataclasses import replace\n\nfrom gymroll.model import Member\n",
        1,
    )


_REQ2 = Request(
    text=(
        "Add a public method on MemberRoll that renews a membership by member id: it sets "
        'the status back to "active", increments the renewals counter by one, stores the '
        "updated member and returns it. An unknown id raises KeyError."
    ),
    target="gymroll/roll.py",
    functional_tests=_C2_FUNCTIONAL,
    regression_tests=_C2_REGRESSION,
    contract_tests=_C2_CONTRACT,
    support_tests=_C2_SUPPORT,
    gold={"noun_verb": _gold2("member_renew"), "verb_noun": _gold2("renew_member")},
)

# ----------------------------------------------------------------- prefix (16 turns)

_PREFIX = [
    Turn(
        "user",
        "I run the front desk at a small climbing gym and I'm replacing our membership "
        "spreadsheet with a tiny Python package: an in-memory MemberRoll, a Member record, "
        "and two scripts, one that the check-in tablet calls to confirm a fob is active and "
        "one that prints the month's renewals for the bookkeeper. About four hundred members "
        "on three plans (monthly, annual, student). Persistence is a JSON dump at closing; "
        "no database, no web app, no payments. The tablet call is literally:\n\n```\n"
        "python -m gymroll.checkin --fob 00A3F2 && echo OPEN || echo SEE-DESK\n```\n\nso the "
        "package just has to expose enough for that to work. Can you sketch what the README "
        "should say about scope? The owner has already asked whether it will 'do class "
        "bookings' and I want a written no before it grows into that. Speed is irrelevant "
        "at our size; what matters is that the two other desk staff, neither of whom "
        "programs for a living, can read the code and not be surprised by it.",
    ),
    Turn(
        "assistant",
        "A short scope section plus explicit non-goals is what to hand the owner:\n\n```\n"
        "## Scope\ngymroll is an in-memory membership roll for a single gym in a single "
        "process. It keeps Member records in a MemberRoll, has no persistence beyond the "
        "closing-time JSON dump and no concurrency guarantees, and is meant for the desk "
        "and tablet scripts, not as a service.\n\n## Non-goals\n- class bookings or "
        "timetables\n- payments and direct debits\n- access-control hardware\n- member "
        "logins\n```\n\nThe non-goals list is what people actually read. A usage block sets "
        "the tone for the API:\n\n```python\nfrom gymroll.roll import MemberRoll\n\nroll = "
        'MemberRoll()\nm = roll.member_enroll("Priya", plan="annual")\nprint(roll.find('
        "m.member_id))\n```\n\nIf class bookings ever happen, they are a separate package "
        "that references member ids; saying that now is much cheaper than carving it out "
        "later. Also state `Requires Python 3.11+`, since the tablet image is old.",
    ),
    Turn(
        "user",
        "Good. Ids are M1, M2, ... from a counter. The owner wants the member id to be the "
        "fob number so the tablet can skip a lookup, but fobs get lost and reissued, and a "
        "couple of members share a family fob. I think fob is an attribute, not identity. "
        'The closing dump I have in mind is:\n\n```json\n{\n  "gym": "crux",\n  '
        '"dumped_at": "2026-09-14T22:00:00",\n  "members": [\n    {"member_id": "M1", '
        '"name": "Priya", "plan": "annual", "status": "active", "renewals": 2, "fob": '
        '"00A3F2"},\n    {"member_id": "M2", "name": "Tomasz", "plan": "student", '
        '"status": "frozen"}\n  ]\n}\n```\n\nAm I right to '
        "push back, and is there a cheap way to give the owner the fast fob lookup anyway?",
    ),
    Turn(
        "assistant",
        "You are right. An id should never carry a fact that can change, and a fob is "
        "exactly that: lost, reissued, shared. Keep the counter as identity and the fob as "
        "data, and give the roll a fob index so the tablet gets its fast lookup without the "
        "id lying:\n\n```python\ndef find_by_fob(self, fob: str) -> Member | None:\n    "
        "member_id = self._fobs.get(fob)\n    return None if member_id is None else "
        "self._members[member_id]\n```\n\nwhere `self._fobs: dict[str, str]` is updated "
        "whenever a fob is assigned. Counters stay short in logs and on the desk screen, "
        "and only `member_enroll` mints ids, so if persistence changes later there is one "
        "place to touch:\n\n```python\ndef _next_id(self) -> str:\n    self._counter += 1\n"
        '    return f"M{self._counter}"\n```\n\nThe shared family fob then maps to whichever '
        "member you choose as primary, which is a policy decision, not a schema one.",
    ),
    Turn(
        "user",
        "I want a helper that formats a member for the desk screen, like `M3 Priya "
        "[annual] active` or `M3 Priya [annual] frozen (2 renewals)`. Method on Member or "
        "free function next to it? A method is discoverable, but then the record knows "
        "about presentation. Here is my test draft so you can see the shape I'm after:\n\n"
        "```python\nimport pytest\n\nfrom gymroll.model import Member\n\n\n@pytest.fixture\n"
        'def priya():\n    return Member(member_id="M3", name="Priya", plan="annual")\n\n\n'
        'def test_summary_active(priya):\n    assert summary(priya) == "M3 Priya [annual] '
        'active"\n\n\ndef test_summary_frozen_with_renewals():\n    m = Member(member_id='
        '"M3", name="Priya", plan="annual", status="frozen", renewals=2)\n    assert '
        'summary(m) == "M3 Priya [annual] frozen (2 renewals)"\n```',
    ),
    Turn(
        "assistant",
        "Put it next to the model as a plain function so the scripts and tests share it "
        "without Member learning about presentation:\n\n```python\ndef summary(member: "
        'Member) -> str:\n    tail = f" ({member.renewals} renewals)" if member.renewals '
        'else ""\n    return f"{member.member_id} {member.name} [{member.plan}] '
        '{member.status}{tail}"\n```\n\nIt reads only public fields, so it stays trivially '
        "testable, and if the desk screen later wants colour or column alignment that "
        "lives in the script. A `__str__` on Member would tie the record to one rendering "
        "forever, and the JSON dump needs its own serializer anyway. Both of your tests "
        "pass against that as written; I would add one for a single renewal so the plural "
        "is pinned (`(1 renewals)` is ugly and you should decide now whether to special-case "
        "it):\n\n```python\ndef test_summary_single_renewal():\n    m = Member("
        'member_id="M3", name="Priya", plan="annual", renewals=1)\n    assert summary(m) == '
        '"M3 Priya [annual] active (1 renewal)"\n```',
    ),
    Turn(
        "user",
        "We'll special-case it. Next: should `find` raise on a missing id or return None? "
        "Right now it returns None and the caller checks. I want one rule I can point the "
        "other desk staff at. This is what one of them hit last week assuming `find` "
        'raises:\n\n```\n>>> roll.find("M41").plan\nTraceback (most recent call last):\n'
        "  File \"<stdin>\", line 1, in <module>\nAttributeError: 'NoneType' object has no "
        "attribute 'plan'\n```\n\nThe usual None-propagation trap; she had typed M41 for "
        "M14 and spent a while convinced the dump had not loaded. The desk log from that "
        "afternoon, for colour:\n\n```\n2026-09-09 16:02:11 INFO  gymroll: loaded dump "
        "2026-09-08.json (412 members)\n2026-09-09 16:40:51 ERROR shell: AttributeError: "
        "'NoneType' object has no attribute 'plan'\n```",
    ),
    Turn(
        "assistant",
        "Returning None from `find` is the usual lookup contract: the name says 'try to "
        "find', and callers branch on the result. Methods that *act* on a member "
        "(freezing, renewing, cancelling) are different: acting on an id that does not "
        "exist is a caller bug, so raising KeyError there is the clearer signal and it "
        "surfaces in tests immediately. So the rule is: lookups return None, actions raise "
        "KeyError. Keep `find` as it is, and callers that need a hard failure can wrap it:"
        "\n\n```python\ndef require(roll, member_id):\n    member = roll.find(member_id)\n"
        "    if member is None:\n        raise KeyError(member_id)\n    return member\n```"
        "\n\nThe traceback you pasted becomes a KeyError('M41') at the call site, which "
        "says the id was wrong rather than the dump; the log line showing 412 members "
        "loaded forty minutes earlier was the other clue. Put the rule in the README under "
        "a `Lookups and actions` heading so the next hire reads it before the shell does.",
    ),
    Turn(
        "user",
        "Agreed, actions raise KeyError on unknown ids. Two conventions to fix now so the "
        "code stays uniform. First: public MemberRoll methods always return Member "
        "dataclass instances, never dicts or tuples, even for convenience. The spreadsheet "
        "exporter I wrote returned dicts and every caller grew a `.get('plan')`.",
    ),
    Turn(
        "assistant",
        "Noted: every public MemberRoll method returns Member instances (or None from "
        "lookups), never dicts or tuples. Callers stay on one type, we can add fields to "
        "Member without breaking them, and the summary helper works on anything the roll "
        "hands back.",
    ),
    Turn(
        "user",
        "Second: method naming. Public roll methods are named noun_verb, like "
        "member_enroll, because the desk staff think in terms of 'member, then what "
        "happens to them'. Anything new follows that pattern.",
    ),
    Turn(
        "assistant",
        "Understood: noun_verb for public MemberRoll methods, matching member_enroll. I "
        "will name new methods that way; private helpers stay free-form since they are not "
        "part of the API. If a verb is ambiguous, for example whether pausing a membership "
        "is member_freeze or member_pause, I will use the verb the request itself uses.",
    ),
    Turn(
        "user",
        "One more for later: I'd like `count` to take an optional plan filter so the "
        "bookkeeper's script can print per-plan totals. Not now. For reference, the tests "
        "that exist today are only these:\n\n```python\nfrom gymroll.roll import MemberRoll"
        "\n\n\ndef test_enroll_assigns_sequential_ids():\n    r = MemberRoll()\n    assert "
        'r.member_enroll("a").member_id == "M1"\n    assert r.member_enroll("b").member_id '
        '== "M2"\n\n\ndef test_find_missing_returns_none():\n    assert MemberRoll().find('
        '"M1") is None\n```',
    ),
    Turn(
        "assistant",
        "Noted for later. An optional keyword `plan: str | None = None` keeps the current "
        "no-argument call working:\n\n```python\ndef count(self, plan: str | None = None) "
        "-> int:\n    if plan is None:\n        return len(self._members)\n    return "
        "sum(1 for m in self._members.values() if m.plan == plan)\n```",
    ),
    Turn(
        "user",
        "Right. Let's get the first real feature in; two members are travelling next month "
        "and want their memberships frozen before then. I will paste the current files with "
        "each request so you always see the real state rather than my memory of it.",
    ),
    Turn(
        "assistant",
        "Ready when you are. Send the request and I will return the full roll module.",
    ),
]

_EVENT = (
    "Quick aside before the next one: the owner approved the new tablet for the front "
    "desk, so the check-in script will get a bigger screen to print to. No change to the "
    "package; I just wanted you to know the summary line can be a bit longer later."
)


def build() -> Session:
    return Session(
        id="S05",
        project="gymroll",
        target_family="naming",
        support_family="return_shape",
        lifecycle="stable",
        files=_FILES,
        prefix=_PREFIX,
        states=("noun_verb", "verb_noun"),
        state_at=("noun_verb", "noun_verb"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10),
    )
