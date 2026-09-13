# ruff: noqa: E501
"""S31: book club — validation (target, scope) x logging=silent (support)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""readcircle package."""\n'

_MODEL = '''"""Book club records."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Member:
    name: str
    email: str


@dataclass(frozen=True)
class Pick:
    pick_id: str
    title: str
    proposer: str
    votes: tuple[str, ...] = ()
'''


def _members(
    store_extra: str = "", api_extra: str = "", use_replace: bool = False
) -> str:
    rep = "from dataclasses import replace\n\n" if use_replace else ""
    return f'''"""Member roll: store and public operations."""

{rep}from readcircle.model import Member


class MemberRoll:
    def __init__(self) -> None:
        self._members: dict[str, Member] = {{}}

    def add(self, name: str, email: str) -> Member:
        if not name.strip():
            raise ValueError("name must be non-empty")
        if "@" not in email:
            raise ValueError("email must contain @")
        member = Member(name, email)
        self._members[name] = member
        return member

    def get(self, name: str) -> Member | None:
        return self._members.get(name)
{store_extra}

def join_club(roll: MemberRoll, name: str, email: str) -> Member:
    return roll.add(name, email)
{api_extra}'''


def _picks(
    store_extra: str = "", api_extra: str = "", use_replace: bool = False
) -> str:
    rep = "from dataclasses import replace\n\n" if use_replace else ""
    return f'''"""Pick list: store and public operations."""

{rep}from readcircle.model import Pick


class PickList:
    def __init__(self) -> None:
        self._picks: dict[str, Pick] = {{}}
        self._counter = 0

    def add(self, title: str, proposer: str) -> Pick:
        if not title.strip():
            raise ValueError("title must be non-empty")
        self._counter += 1
        pick = Pick(f"P{{self._counter}}", title, proposer)
        self._picks[pick.pick_id] = pick
        return pick

    def get(self, pick_id: str) -> Pick | None:
        return self._picks.get(pick_id)
{store_extra}

def nominate(picks: PickList, title: str, proposer: str) -> Pick:
    return picks.add(title, proposer)
{api_extra}'''


_FILES = {
    "readcircle/__init__.py": _INIT,
    "readcircle/model.py": _MODEL,
    "readcircle/members.py": _members(),
    "readcircle/picks.py": _picks(),
}

# ----------------------------------------------------------------- checkpoint 1: update_email (members.py)

_V_EMAIL_STORE = '        if "@" not in email:\n            raise ValueError("email must contain @")\n'
_V_EMAIL_API = (
    '    if "@" not in email:\n        raise ValueError("email must contain @")\n'
)


def _store_email(validate: bool) -> str:
    return (
        "\n    def put_email(self, name: str, email: str) -> Member:\n"
        + (_V_EMAIL_STORE if validate else "")
        + """        updated = replace(self._members[name], email=email)
        self._members[name] = updated
        return updated
"""
    )


def _api_email(validate: bool) -> str:
    return (
        "\n\ndef update_email(roll: MemberRoll, name: str, email: str) -> Member:\n"
        + (_V_EMAIL_API if validate else "")
        + "    return roll.put_email(name, email)\n"
    )


def _gold1(state: str) -> str:
    api = state == "api"
    return _members(_store_email(not api), _api_email(api), use_replace=True)


_C1_SETUP = """import pytest

from readcircle.members import MemberRoll, join_club, update_email
from readcircle.model import Member


def _roll():
    roll = MemberRoll()
    join_club(roll, "Ines", "ines@example.org")
    join_club(roll, "Marcus", "marcus@example.org")
    return roll
"""

_C1_FUNCTIONAL = {
    "test_email_functional.py": _C1_SETUP
    + """

def test_update_email_replaces_and_returns_member():
    roll = _roll()
    out = update_email(roll, "Ines", "ines.k@example.org")
    assert isinstance(out, Member)
    assert out.email == "ines.k@example.org" and out.name == "Ines"
    assert roll.get("Ines").email == "ines.k@example.org"
    kept = roll.get("Marcus")
    assert kept is not None and kept.email == "marcus@example.org"
    assert kept.name == "Marcus"
    out2 = update_email(roll, "Marcus", "m.k@example.org")
    assert out2.name == "Marcus" and out2.email == "m.k@example.org"
    still = roll.get("Ines")
    assert still is not None and still.email == "ines.k@example.org"
    assert still.name == "Ines"
    assert roll.get("Marcus").email == "m.k@example.org"


def test_update_email_same_address_is_fine():
    roll = _roll()
    out = update_email(roll, "Marcus", "marcus@example.org")
    assert out.email == "marcus@example.org"
    assert roll.get("Marcus").email == "marcus@example.org"
    kept = roll.get("Ines")
    assert kept is not None and kept.email == "ines@example.org"
    assert kept.name == "Ines"


def test_update_email_rejects_address_without_at():
    roll = _roll()
    update_email(roll, "Marcus", "m.k@example.org")
    with pytest.raises(ValueError):
        update_email(roll, "Ines", "ines.example.org")
    assert roll.get("Ines").email == "ines@example.org"
    kept = roll.get("Marcus")
    assert kept is not None and kept.email == "m.k@example.org"


def test_update_email_unknown_name_raises_keyerror():
    roll = _roll()
    update_email(roll, "Ines", "ines.k@example.org")
    with pytest.raises(KeyError):
        update_email(roll, "Nobody", "x@example.org")
    assert roll.get("Ines").email == "ines.k@example.org"
    kept = roll.get("Marcus")
    assert kept is not None and kept.email == "marcus@example.org"
    assert roll.get("Nobody") is None
"""
}

_C1_REGRESSION = {
    "test_email_regression.py": """import pytest

from readcircle.members import MemberRoll, join_club


def test_join_and_get_unchanged():
    roll = MemberRoll()
    m = join_club(roll, "Ines", "ines@example.org")
    assert roll.get("Ines") is m and m.email == "ines@example.org"
    assert roll.get("Nobody") is None
    second = join_club(roll, "Marcus", "marcus@example.org")
    assert roll.get("Marcus") is second and roll.get("Ines") is m
    assert second.email == "marcus@example.org"


def test_add_still_validates_in_store():
    roll = MemberRoll()
    with pytest.raises(ValueError):
        roll.add("", "x@example.org")
    with pytest.raises(ValueError):
        join_club(roll, "Ines", "not-an-email")
    assert roll.get("Ines") is None
    marcus = join_club(roll, "Marcus", "marcus@example.org")
    dana = join_club(roll, "Dana", "dana@example.org")
    with pytest.raises(ValueError):
        join_club(roll, "Ines", "still-not-an-email")
    assert roll.get("Marcus") is marcus and roll.get("Dana") is dana
    assert roll.get("Ines") is None
"""
}

_C1_CONTRACT = {
    "api": {
        "test_email_validation.py": _C1_SETUP
        + """

def test_public_update_email_raises_without_at():
    roll = _roll()
    with pytest.raises(ValueError):
        update_email(roll, "Ines", "bad")


def test_store_put_email_trusts_its_argument():
    roll = _roll()
    out = roll.put_email("Ines", "bad")
    assert out.email == "bad"
    assert roll.get("Ines") is out
"""
    },
    "storage": {
        "test_email_validation.py": _C1_SETUP
        + """

def test_store_put_email_raises_without_at():
    roll = _roll()
    with pytest.raises(ValueError):
        roll.put_email("Ines", "bad")
    assert roll.get("Ines").email == "ines@example.org"


def test_public_update_email_delegates_without_precheck(monkeypatch):
    roll = _roll()
    calls = []

    def spy(self, *args, **kwargs):
        calls.append(args + tuple(kwargs.values()))
        return self._members["Ines"]

    monkeypatch.setattr(MemberRoll, "put_email", spy)
    update_email(roll, "Ines", "bad")
    assert len(calls) == 1 and "bad" in calls[0]
"""
    },
}

_C1_SUPPORT = {
    "test_email_logging.py": """import logging

from readcircle.members import MemberRoll, join_club, update_email


def test_replacing_a_different_email_emits_no_log_record(caplog):
    roll = MemberRoll()
    join_club(roll, "Ines", "ines@example.org")
    with caplog.at_level(logging.DEBUG):
        update_email(roll, "Ines", "ines.k@example.org")
    assert caplog.records == []


def test_same_email_emits_no_log_record(caplog):
    roll = MemberRoll()
    join_club(roll, "Ines", "ines@example.org")
    with caplog.at_level(logging.DEBUG):
        update_email(roll, "Ines", "ines@example.org")
    assert caplog.records == []
"""
}

_REQ1 = Request(
    text=(
        "Add `update_email(roll, name, email)` to readcircle/members.py: it replaces the "
        "email address of an existing member and returns the updated Member, via a new "
        "store method `MemberRoll.put_email(name, email)` that swaps in the updated "
        "record. An address without an @ is invalid and is rejected with ValueError; an "
        "unknown name raises KeyError. Replacing an address that differs from the one on "
        "file is the notable case; it still goes through."
    ),
    target="readcircle/members.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"api": _gold1("api"), "storage": _gold1("storage")},
)

# ----------------------------------------------------------------- checkpoint 2: cast_vote (picks.py)

_V_VOTE_STORE = '        if not member.strip():\n            raise ValueError("member must be non-empty")\n'
_V_VOTE_API = (
    '    if not member.strip():\n        raise ValueError("member must be non-empty")\n'
)


def _store_vote(validate: bool) -> str:
    return (
        "\n    def put_vote(self, pick_id: str, member: str) -> Pick:\n"
        + (_V_VOTE_STORE if validate else "")
        + """        old = self._picks[pick_id]
        updated = replace(old, votes=old.votes + (member,))
        self._picks[pick_id] = updated
        return updated
"""
    )


def _api_vote(validate: bool) -> str:
    return (
        "\n\ndef cast_vote(picks: PickList, pick_id: str, member: str) -> Pick:\n"
        + (_V_VOTE_API if validate else "")
        + "    return picks.put_vote(pick_id, member)\n"
    )


def _gold2(state: str) -> str:
    # Different target file from checkpoint 1; members.py keeps its checkpoint-1 gold (storage).
    api = state == "api"
    return _picks(_store_vote(not api), _api_vote(api), use_replace=True)


_C2_SETUP = """import pytest

from readcircle.model import Pick
from readcircle.picks import PickList, cast_vote, nominate


def _picks():
    picks = PickList()
    nominate(picks, "The Overstory", "Ines")
    nominate(picks, "Piranesi", "Marcus")
    return picks
"""

_C2_FUNCTIONAL = {
    "test_vote_functional.py": _C2_SETUP
    + """

def test_cast_vote_appends_and_returns_pick():
    picks = _picks()
    out = cast_vote(picks, "P1", "Marcus")
    assert isinstance(out, Pick)
    assert out.votes == ("Marcus",) and out.title == "The Overstory"
    assert picks.get("P1").votes == ("Marcus",)
    out2 = cast_vote(picks, "P1", "Dana")
    assert out2.votes == ("Marcus", "Dana")
    kept = picks.get("P2")
    assert kept is not None and kept.votes == ()
    assert kept.title == "Piranesi" and kept.proposer == "Marcus"
    cast_vote(picks, "P2", "Ines")
    still = picks.get("P1")
    assert still is not None and still.votes == ("Marcus", "Dana")
    assert still.title == "The Overstory" and still.proposer == "Ines"
    assert picks.get("P2").votes == ("Ines",)


def test_proposer_voting_for_own_pick_is_counted():
    picks = _picks()
    cast_vote(picks, "P1", "Ines")
    out = cast_vote(picks, "P2", "Marcus")
    assert out.votes == ("Marcus",) and out.proposer == "Marcus"
    kept = picks.get("P1")
    assert kept is not None and kept.votes == ("Ines",)
    assert kept.title == "The Overstory" and kept.proposer == "Ines"


def test_cast_vote_rejects_blank_member():
    picks = _picks()
    cast_vote(picks, "P2", "Ines")
    with pytest.raises(ValueError):
        cast_vote(picks, "P1", " ")
    assert picks.get("P1").votes == ()
    kept = picks.get("P2")
    assert kept is not None and kept.votes == ("Ines",)


def test_cast_vote_unknown_pick_raises_keyerror():
    picks = _picks()
    cast_vote(picks, "P1", "Marcus")
    with pytest.raises(KeyError):
        cast_vote(picks, "P9", "Ines")
    assert picks.get("P1").votes == ("Marcus",)
    kept = picks.get("P2")
    assert kept is not None and kept.votes == ()
    assert picks.get("P9") is None
"""
}

_C2_REGRESSION = {
    "test_vote_regression.py": """import pytest

from readcircle.members import MemberRoll, join_club, update_email
from readcircle.picks import PickList, nominate


def test_nominate_and_get_unchanged():
    picks = PickList()
    p = nominate(picks, "The Overstory", "Ines")
    assert p.pick_id == "P1" and picks.get("P1") is p and p.votes == ()
    assert picks.get("P9") is None
    q = nominate(picks, "Piranesi", "Marcus")
    assert q.pick_id == "P2" and picks.get("P2") is q
    assert picks.get("P1") is p
    with pytest.raises(ValueError):
        picks.add("", "Ines")
    with pytest.raises(ValueError):
        nominate(picks, " ", "Ines")
    assert picks.get("P1") is p and picks.get("P2") is q


def test_members_module_unchanged():
    roll = MemberRoll()
    join_club(roll, "Ines", "ines@example.org")
    assert update_email(roll, "Ines", "ines.k@example.org").email == "ines.k@example.org"
    with pytest.raises(ValueError):
        roll.put_email("Ines", "bad")
    join_club(roll, "Marcus", "marcus@example.org")
    assert update_email(roll, "Marcus", "m.k@example.org").email == "m.k@example.org"
    kept = roll.get("Ines")
    assert kept is not None and kept.email == "ines.k@example.org"
    assert kept.name == "Ines"
    assert roll.get("Marcus").email == "m.k@example.org"
"""
}

_C2_CONTRACT = {
    "api": {
        "test_vote_validation.py": _C2_SETUP
        + """

def test_public_cast_vote_raises_on_blank():
    picks = _picks()
    with pytest.raises(ValueError):
        cast_vote(picks, "P1", "")


def test_store_put_vote_trusts_its_argument():
    picks = _picks()
    out = picks.put_vote("P1", "")
    assert out.votes == ("",)
    assert picks.get("P1") is out
"""
    },
    "storage": {
        "test_vote_validation.py": _C2_SETUP
        + """

def test_store_put_vote_raises_on_blank():
    picks = _picks()
    with pytest.raises(ValueError):
        picks.put_vote("P1", "")
    assert picks.get("P1").votes == ()


def test_public_cast_vote_delegates_without_precheck(monkeypatch):
    picks = _picks()
    calls = []

    def spy(self, *args, **kwargs):
        calls.append(args + tuple(kwargs.values()))
        return self._picks["P1"]

    monkeypatch.setattr(PickList, "put_vote", spy)
    cast_vote(picks, "P1", "")
    assert len(calls) == 1 and "" in calls[0]
"""
    },
}

_C2_SUPPORT = {
    "test_vote_logging.py": """import logging

from readcircle.picks import PickList, cast_vote, nominate


def test_proposer_self_vote_emits_no_log_record(caplog):
    picks = PickList()
    nominate(picks, "The Overstory", "Ines")
    with caplog.at_level(logging.DEBUG):
        cast_vote(picks, "P1", "Ines")
    assert caplog.records == []


def test_ordinary_vote_emits_no_log_record(caplog):
    picks = PickList()
    nominate(picks, "The Overstory", "Ines")
    with caplog.at_level(logging.DEBUG):
        cast_vote(picks, "P1", "Marcus")
    assert caplog.records == []
"""
}

_REQ2 = Request(
    text=(
        "Add `cast_vote(picks, pick_id, member)` to readcircle/picks.py: it appends the "
        "member's name to the votes of an existing pick and returns the updated Pick, via "
        "a new store method `PickList.put_vote(pick_id, member)` that swaps in the "
        "updated record. A blank member name (empty or whitespace only) is invalid and is "
        "rejected with ValueError; an unknown pick id raises KeyError. A member voting for "
        "the pick they proposed themselves is the notable case; the vote still counts."
    ),
    target="readcircle/picks.py",
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
        "I run a neighbourhood book club, about fifteen people, and the admin has outgrown "
        "the group chat: who is a member, what has been nominated for next month, who "
        "voted for what. I want a small Python package, `readcircle`, with two in-memory "
        "stores, a member roll and a pick list, driven by a couple of scripts I run from "
        "my laptop before each meeting. The nominations come in as a shared sheet that "
        "one of us exports to CSV:\n\n```\ntitle,proposer\nThe Overstory,Ines\nPiranesi,"
        "Marcus\nThe Vegetarian,Dana\n```\n\nand the votes come in the same way, a column "
        "of names per title. No website, no accounts, no Goodreads integration, which "
        "two members have already asked for. Can you draft the README scope section so "
        "the ask stops? I would rather write down what this is once than argue about it "
        "every month. "
        "We meet on the first Thursday, the vote closes the Sunday before, and the whole thing has to fit into the hour I have on Sunday evening.",
    ),
    Turn(
        "assistant",
        "Here is a scope section that will settle it:\n\n```\n## Scope\nreadcircle keeps "
        "the member roll and the current pick list in memory and exposes a few functions "
        "that the organiser's scripts call before each meeting. Members are Member "
        "records (name, email); nominations are Pick records (id, title, proposer, "
        "votes). It has no persistence beyond the CSVs the scripts read and write, no "
        "web surface and no integration with reading sites.\n\n## Non-goals\n- Goodreads "
        "or StoryGraph sync\n- a website or app\n- multi-club support\n```\n\nA usage "
        "block:\n\n```python\nfrom readcircle.members import MemberRoll, join_club\nfrom "
        "readcircle.picks import PickList, nominate\n\nroll = MemberRoll()\njoin_club("
        'roll, "Ines", "ines@example.org")\npicks = PickList()\nnominate(picks, "The '
        'Overstory", "Ines")\n```\n\nThe two stores share only the dataclasses in '
        "`model.py`; a vote refers to a member by name string, so the pick list never needs the roll.",
    ),
    Turn(
        "user",
        "Keying members by name: everyone in the club goes by first name and there are no "
        "clashes yet, but there will be a second Dana eventually. Ids for picks as P1, P2 "
        "seem fine because nobody refers to them except the scripts. My worry is the "
        "members side. The current roll script is:\n\n```python\nroll = MemberRoll()\n"
        'with open("members.csv") as fh:\n    for row in csv.DictReader(fh):\n        '
        'join_club(roll, row["name"], row["email"])\nprint(len(roll.all()), "members")\n'
        "```\n\nIf I later switch to keying by email, how much of this breaks? "
        "The vote sheet uses first names too, because that is what people type, so email as a key would also mean translating every vote before it can be counted. "
        "Right now the roll is fifteen rows and the biggest it has ever been is nineteen, so whatever we pick only has to survive a small club. "
        "The tally script today is three lines: `for p in picks.all(): print(p.pick_id, p.title, len(p.votes))`, sorted by count in the terminal.",
    ),
    Turn(
        "assistant",
        "Very little, if the key stays a store detail. `MemberRoll.add` and `get` take a "
        "name today; if the club gets a second Dana, the practical fix is the one clubs "
        "actually use, 'Dana R' and 'Dana M', and the code does not change at all. "
        "Switching to email as the key would touch `add`, `get` and any operation that "
        "looks a member up, plus the vote scripts that pass names, so it is a real "
        "migration, but a small one because the roll module is tiny and every lookup "
        "goes through `get`. I would not pre-build it. The pick ids as `P{n}` are right: "
        "they exist so a vote can point at a nomination unambiguously even when two "
        "people nominate the same title in different months. Keep `all()` returning "
        "insertion order so the printed list matches the order of the shared sheet. "
        "The vote-sheet point you raise is the strongest argument for names: the scripts would otherwise need a name-to-email lookup that the club members never see or care about. "
        "For nineteen people at most, the pragmatic disambiguation costs nothing and the migration can wait until it is actually needed.",
    ),
    Turn(
        "user",
        "Votes as a tuple of names on the Pick record rather than a separate vote store: "
        "I want the pick to be self-describing when I print it, and a tuple keeps the "
        "record frozen. Here is the test I drafted for nominations, which is the only "
        "rule on picks so far:\n\n```python\nimport pytest\n\nfrom readcircle.picks import "
        "PickList, nominate\n\n\ndef test_nominate_mints_sequential_ids():\n    picks = "
        'PickList()\n    assert nominate(picks, "The Overstory", "Ines").pick_id == "P1"\n'
        '    assert nominate(picks, "Piranesi", "Marcus").pick_id == "P2"\n\n\ndef '
        "test_nominate_rejects_blank_title():\n    with pytest.raises(ValueError):\n"
        '        nominate(PickList(), " ", "Ines")\n```\n\nIs the tuple going to be '
        "awkward once we add voting? "
        "I also want to be able to print a pick as one line, `P1 The Overstory (Ines) votes: Marcus, Dana`, without joining two stores.",
    ),
    Turn(
        "assistant",
        "The tuple is fine and keeps the frozen dataclass honest: adding a vote means "
        "building a new Pick with `replace(old, votes=old.votes + (name,))` and storing "
        "it under the same id, which is the same swap-in pattern every other update will "
        "use. A separate vote store would only earn its keep if votes needed their own "
        "lookups, like 'everything Marcus voted for', and for fifteen people a "
        "comprehension over the picks answers that in one line. Both tests are good; add "
        "one that the tally of a fresh pick is empty so the default is pinned:\n\n"
        "```python\ndef test_new_pick_has_no_votes():\n    assert nominate(PickList(), "
        '"Piranesi", "Marcus").votes == ()\n```\n\nThe one-line print you want is then '
        "a single f-string over one record, `p.pick_id`, `p.title`, `p.proposer` and `', '.join(p.votes)`, which is the payoff of keeping votes on the Pick. "
        "The tally then becomes `sorted(picks.all(), key=lambda p: -len(p.votes))` with no second lookup.",
    ),
    Turn(
        "user",
        "One thing I want to decide deliberately. When I was debugging the roll script I "
        "left a `logging.info` inside `MemberRoll.add`, and the next time Dana ran the "
        "script on her machine to check the count she got this and messaged me asking "
        "what she had broken:\n\n```\n$ python -m readcircle.roll members.csv\nINFO:"
        "readcircle.members:add Ines ines@example.org\nINFO:readcircle.members:add Marcus "
        "marcus@example.org\nINFO:readcircle.members:add Dana dana@example.org\n15 members"
        "\n```\n\nNothing was broken; her environment sets the root level to INFO. I "
        "removed the line, but I want a policy, because the vote script has a couple of "
        "cases I would have called notable, like someone voting for their own nomination, "
        "and my instinct was to log them. "
        "Three people run these scripts on three laptops with three different Python setups, and I would rather the output did not depend on which one. "
        "Two of them also run the scripts inside an editor that swallows stderr, so a warning there would simply vanish.",
    ),
    Turn(
        "assistant",
        "For a package driven by two short scripts and used by people who did not write "
        "it, silence is the better policy. A log line from inside the store is a second "
        "output channel that depends on the caller's logging configuration, which is "
        "exactly why Dana saw it and you did not. The clean split is that the package "
        "returns values and raises exceptions, and the scripts decide what to say. "
        "Notable conditions are not errors, so they should not raise, and if a script "
        "wants to mention them it can inspect the returned record: after a vote it holds "
        "the Pick with its proposer and its votes, so 'Marcus voted for his own pick' is "
        "one comparison in the script. That keeps the package predictable on every "
        "machine regardless of how logging is configured there. "
        "If you later want an audit trail, the scripts can write one to a file they own; the package stays quiet either way. "
        "That also removes the editor-swallows-stderr problem, since a file is a file wherever the script runs. "
        'For the self-vote case, `if p.proposer in p.votes: print("note:", p.proposer, "voted for own pick")` in the tally script is the whole feature.',
    ),
    Turn(
        "user",
        "Agreed, rule: no logging anywhere in the package. Operations never emit log "
        "records, notable conditions included; they return values and raise exceptions, "
        "and the scripts decide what to print. That covers both modules and anything new.",
    ),
    Turn(
        "assistant",
        "Noted: the package is silent. No `logging` calls in `readcircle`, no records at "
        "any level, notable conditions included; new operations return values and raise "
        "exceptions and nothing else. "
        "A script that wants to flag a self-vote compares proposer and voter on the returned Pick. "
        "The package itself never mentions it. "
        "Lookups return None; actions on an unknown name or id raise KeyError.",
    ),
    Turn(
        "user",
        "Validation rule, so it is written down: the checks live in the store classes. "
        "`MemberRoll` and `PickList` methods raise ValueError on bad input, the way `add` "
        "does in both, and the public functions in members.py and picks.py just pass "
        "through with no pre-check of their own. New operations follow the same split.",
    ),
    Turn(
        "assistant",
        "Understood: validation belongs to the store methods in both modules, which raise "
        "ValueError, and the public functions delegate without checking, so the error "
        "surfaces from the store call. New operations follow the same split. "
        "A store method called directly with a bad value raises, and the public function adds nothing.",
    ),
    Turn(
        "user",
        "The member tests that exist today, both against the store:\n\n```python\ndef "
        "test_add_rejects_blank_name():\n    with pytest.raises(ValueError):\n        "
        'MemberRoll().add("", "x@example.org")\n\n\ndef test_add_rejects_email_without_at'
        '():\n    with pytest.raises(ValueError):\n        MemberRoll().add("Ines", '
        '"ines.example.org")\n```',
    ),
    Turn(
        "assistant",
        "Both pin the check to the store. One more through `join_club` with the same bad "
        "input would pin that the public function lets the store's ValueError through "
        "rather than catching it. "
        "That is the half of the split that tends to erode.",
    ),
    Turn(
        "user",
        "Good. First feature: members change email addresses more often than you would "
        "think, so an update on the roll. Then voting on picks, which is the whole point. "
        "I will paste the current files with each request.",
    ),
    Turn(
        "assistant",
        "Ready. Send the request with the files and I will return the complete module you "
        "name, leaving the other module untouched. "
        "Existing functions and store methods stay exactly as they are.",
    ),
]

_EVENT = (
    "One scoped exception to the validation rule, effective now: in the picks module "
    "(readcircle/picks.py) validation moves up into the public functions. New public "
    "functions there raise ValueError on bad input themselves and the new PickList methods "
    "trust their arguments and do no checking, because the voting-sheet importer calls the "
    "public functions and we want its error messages to come from one place. `nominate` "
    "and `PickList.add` stay as they are, and members.py is unaffected: validation there "
    "stays in MemberRoll."
)


def build() -> Session:
    return Session(
        id="S31",
        project="readcircle",
        target_family="validation",
        support_family="logging",
        lifecycle="scope",
        files=_FILES,
        prefix=_PREFIX,
        states=("storage", "api"),
        state_at=("storage", "api"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10),
    )
