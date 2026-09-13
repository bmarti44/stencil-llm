# ruff: noqa: E501
"""S20: donation pledges — validation (target, reinstatement) x return_shape (support)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""pledgebook package."""\n'

_MODEL = '''"""Campaign and pledge records."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Campaign:
    campaign_id: str
    name: str
    goal: int


@dataclass(frozen=True)
class Pledge:
    pledge_id: str
    campaign_id: str
    donor: str
    amount: int
'''

_REPORT = '''"""Progress lines for the weekly mailing."""

from pledgebook.model import Campaign, Pledge


def progress_line(campaign: Campaign, pledges: list[Pledge]) -> str:
    total = sum(p.amount for p in pledges)
    return f"{campaign.name}: {total}/{campaign.goal}"
'''

_BOOK_HEAD = '''"""Pledge table (storage layer) and the public pledge-book operations."""

from pledgebook.model import Campaign, Pledge


class PledgeTable:
    def __init__(self) -> None:
        self._campaigns: dict[str, Campaign] = {}
        self._pledges: dict[str, Pledge] = {}

    def insert_campaign(self, campaign: Campaign) -> None:
        self._campaigns[campaign.campaign_id] = campaign

    def get_campaign(self, campaign_id: str) -> Campaign:
        return self._campaigns[campaign_id]

    def pledges_for(self, campaign_id: str) -> list[Pledge]:
        return [p for p in self._pledges.values() if p.campaign_id == campaign_id]

    def next_id(self, prefix: str) -> str:
        return f"{prefix}{len(self._campaigns) + len(self._pledges) + 1}"
'''

_OPEN_CAMPAIGN = """

def open_campaign(table: PledgeTable, name: str, goal: int) -> Campaign:
    if goal <= 0:
        raise ValueError("goal must be positive")
    campaign = Campaign(table.next_id("C"), name, goal)
    table.insert_campaign(campaign)
    return campaign
"""

_BOOK = _BOOK_HEAD + _OPEN_CAMPAIGN

_FILES = {
    "pledgebook/__init__.py": _INIT,
    "pledgebook/model.py": _MODEL,
    "pledgebook/report.py": _REPORT,
    "pledgebook/book.py": _BOOK,
}

_AMOUNT_CHECK = '        if pledge.amount <= 0:\n            raise ValueError("amount must be positive")\n'
_GOAL_CHECK_METHOD = (
    '        if goal <= 0:\n            raise ValueError("goal must be positive")\n'
)
_GOAL_CHECK_FN = (
    '    if goal <= 0:\n        raise ValueError("goal must be positive")\n'
)
_AMOUNT_CHECK_FN = (
    '    if amount <= 0:\n        raise ValueError("amount must be positive")\n'
)


def _insert_pledge(state: str) -> str:
    check = _AMOUNT_CHECK if state == "storage" else ""
    return (
        "\n    def insert_pledge(self, pledge: Pledge) -> None:\n"
        + check
        + "        self._pledges[pledge.pledge_id] = pledge\n"
    )


def _record_pledge(state: str) -> str:
    check = _AMOUNT_CHECK_FN if state == "api" else ""
    return (
        "\n\ndef record_pledge(table: PledgeTable, campaign_id: str, donor: str, amount: int) -> Pledge:\n"
        "    table.get_campaign(campaign_id)\n"
        + check
        + '    pledge = Pledge(table.next_id("P"), campaign_id, donor, amount)\n'
        "    table.insert_pledge(pledge)\n"
        "    return pledge\n"
    )


def _update_goal(state: str) -> str:
    check = _GOAL_CHECK_METHOD if state == "storage" else ""
    return (
        "\n    def update_goal(self, campaign_id: str, goal: int) -> Campaign:\n"
        + check
        + "        campaign = replace(self._campaigns[campaign_id], goal=goal)\n"
        "        self._campaigns[campaign_id] = campaign\n"
        "        return campaign\n"
    )


def _adjust_goal(state: str) -> str:
    check = _GOAL_CHECK_FN if state == "api" else ""
    return (
        "\n\ndef adjust_goal(table: PledgeTable, campaign_id: str, goal: int) -> Campaign:\n"
        + check
        + "    return table.update_goal(campaign_id, goal)\n"
    )


def _gold1(state: str) -> str:
    return _BOOK_HEAD + _insert_pledge(state) + _OPEN_CAMPAIGN + _record_pledge(state)


def _gold2(state: str) -> str:
    # Built on the checkpoint-1 gold under the state then in force (storage).
    head = _BOOK_HEAD.replace(
        "from pledgebook.model import Campaign, Pledge\n",
        "from dataclasses import replace\n\nfrom pledgebook.model import Campaign, Pledge\n",
        1,
    )
    return (
        head
        + _insert_pledge("storage")
        + _update_goal(state)
        + _OPEN_CAMPAIGN
        + _record_pledge("storage")
        + _adjust_goal(state)
    )


# ----------------------------------------------------------------- checkpoint 1: record_pledge

_C1_FUNCTIONAL = {
    "test_pledge_functional.py": """import pytest

from pledgebook.book import PledgeTable, open_campaign, record_pledge
from pledgebook.model import Pledge


def _setup():
    t = PledgeTable()
    c = open_campaign(t, "new roof", 5000)
    return t, c


def test_record_pledge_stores_and_returns_pledge():
    t, c = _setup()
    p = record_pledge(t, c.campaign_id, "ann", 250)
    assert p.donor == "ann" and p.amount == 250 and p.campaign_id == c.campaign_id
    assert p.pledge_id.startswith("P")
    assert t.pledges_for(c.campaign_id) == [p]


def test_two_pledges_get_distinct_ids():
    t, c = _setup()
    a = record_pledge(t, c.campaign_id, "ann", 100)
    b = record_pledge(t, c.campaign_id, "bo", 75)
    assert a.pledge_id != b.pledge_id
    assert sum(p.amount for p in t.pledges_for(c.campaign_id)) == 175


def test_unknown_campaign_raises_keyerror():
    t, _ = _setup()
    with pytest.raises(KeyError):
        record_pledge(t, "C99", "ann", 10)


def test_nonpositive_amount_raises_valueerror_and_stores_nothing():
    t, c = _setup()
    for bad in (0, -20):
        with pytest.raises(ValueError):
            record_pledge(t, c.campaign_id, "ann", bad)
    assert t.pledges_for(c.campaign_id) == []


def test_table_has_insert_pledge():
    t, c = _setup()
    t.insert_pledge(Pledge("P7", c.campaign_id, "cy", 40))
    assert [p.pledge_id for p in t.pledges_for(c.campaign_id)] == ["P7"]
"""
}

_C1_REGRESSION = {
    "test_pledge_regression.py": """import pytest

from pledgebook.book import PledgeTable, open_campaign
from pledgebook.report import progress_line


def test_open_campaign_and_lookups_unchanged():
    t = PledgeTable()
    c = open_campaign(t, "bells", 1200)
    assert c.campaign_id == "C1" and t.get_campaign("C1") is c
    with pytest.raises(ValueError):
        open_campaign(t, "bad", 0)
    with pytest.raises(KeyError):
        t.get_campaign("C9")
    assert progress_line(c, t.pledges_for("C1")) == "bells: 0/1200"
"""
}

_C1_CONTRACT = {
    "api": {
        "test_pledge_validation.py": """import pytest

from pledgebook.book import PledgeTable, open_campaign, record_pledge
from pledgebook.model import Pledge


def test_public_function_rejects_nonpositive_amount():
    t = PledgeTable()
    c = open_campaign(t, "roof", 500)
    for bad in (0, -5):
        with pytest.raises(ValueError):
            record_pledge(t, c.campaign_id, "ann", bad)
    assert t.pledges_for(c.campaign_id) == []


def test_table_trusts_callers_on_amount():
    t = PledgeTable()
    c = open_campaign(t, "roof", 500)
    t.insert_pledge(Pledge("P9", c.campaign_id, "ann", 0))
    assert [p.pledge_id for p in t.pledges_for(c.campaign_id)] == ["P9"]
"""
    },
    "storage": {
        "test_pledge_validation.py": """import pytest

from pledgebook.book import PledgeTable, open_campaign, record_pledge
from pledgebook.model import Pledge


def test_table_rejects_nonpositive_amount():
    t = PledgeTable()
    c = open_campaign(t, "roof", 500)
    for bad in (0, -5):
        with pytest.raises(ValueError):
            t.insert_pledge(Pledge("P9", c.campaign_id, "ann", bad))
    assert t.pledges_for(c.campaign_id) == []


def test_public_function_passes_invalid_amount_through(monkeypatch):
    t = PledgeTable()
    c = open_campaign(t, "roof", 500)
    seen = []
    real = t.insert_pledge

    def spy(pledge):
        seen.append(pledge.amount)
        return real(pledge)

    monkeypatch.setattr(t, "insert_pledge", spy)
    with pytest.raises(ValueError):
        record_pledge(t, c.campaign_id, "ann", -5)
    assert seen == [-5]
"""
    },
}

_C1_SUPPORT = {
    "test_pledge_shape.py": """from pledgebook.book import PledgeTable, open_campaign, record_pledge
from pledgebook.model import Pledge


def test_record_pledge_returns_dataclass_not_dict():
    t = PledgeTable()
    c = open_campaign(t, "roof", 500)
    out = record_pledge(t, c.campaign_id, "ann", 30)
    assert isinstance(out, Pledge)
    assert not isinstance(out, dict)
"""
}

_REQ1 = Request(
    text=(
        "Add pledging. Give PledgeTable an `insert_pledge(pledge)` method that stores a "
        "Pledge under its pledge_id, and add a public function `record_pledge(table, "
        "campaign_id, donor, amount)` that looks up the campaign (an unknown id raises "
        'KeyError), mints a pledge id with prefix "P", stores the pledge and returns it. '
        "An amount of zero or less is invalid and must raise ValueError."
    ),
    target="pledgebook/book.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"api": _gold1("api"), "storage": _gold1("storage")},
)

# ----------------------------------------------------------------- checkpoint 2: adjust_goal

_C2_FUNCTIONAL = {
    "test_goal_functional.py": """import pytest

from pledgebook.book import PledgeTable, adjust_goal, open_campaign


def _setup():
    t = PledgeTable()
    c = open_campaign(t, "new roof", 500)
    return t, c


def test_adjust_goal_updates_and_returns_campaign():
    t, c = _setup()
    out = adjust_goal(t, c.campaign_id, 800)
    assert out.goal == 800 and out.campaign_id == c.campaign_id and out.name == "new roof"
    assert t.get_campaign(c.campaign_id).goal == 800


def test_adjust_goal_unknown_raises_keyerror():
    t, _ = _setup()
    with pytest.raises(KeyError):
        adjust_goal(t, "C99", 800)


def test_adjust_goal_nonpositive_raises_and_keeps_old_goal():
    t, c = _setup()
    for bad in (0, -1):
        with pytest.raises(ValueError):
            adjust_goal(t, c.campaign_id, bad)
    assert t.get_campaign(c.campaign_id).goal == 500


def test_table_has_update_goal():
    t, c = _setup()
    out = t.update_goal(c.campaign_id, 900)
    assert out.goal == 900 and t.get_campaign(c.campaign_id).goal == 900
"""
}

_C2_REGRESSION = {
    "test_goal_regression.py": """import pytest

from pledgebook.book import PledgeTable, open_campaign, record_pledge
from pledgebook.report import progress_line


def test_campaigns_and_pledges_unchanged():
    t = PledgeTable()
    c = open_campaign(t, "bells", 1200)
    p = record_pledge(t, c.campaign_id, "ann", 200)
    assert t.pledges_for(c.campaign_id) == [p]
    with pytest.raises(ValueError):
        record_pledge(t, c.campaign_id, "ann", 0)
    with pytest.raises(ValueError):
        open_campaign(t, "bad", -1)
    with pytest.raises(KeyError):
        record_pledge(t, "C9", "ann", 5)
    assert progress_line(c, t.pledges_for(c.campaign_id)) == "bells: 200/1200"
"""
}

_C2_CONTRACT = {
    "api": {
        "test_goal_validation.py": """import pytest

from pledgebook.book import PledgeTable, adjust_goal, open_campaign


def test_public_function_rejects_nonpositive_goal():
    t = PledgeTable()
    c = open_campaign(t, "roof", 500)
    for bad in (0, -3):
        with pytest.raises(ValueError):
            adjust_goal(t, c.campaign_id, bad)
    assert t.get_campaign(c.campaign_id).goal == 500


def test_table_trusts_callers_on_goal():
    t = PledgeTable()
    c = open_campaign(t, "roof", 500)
    out = t.update_goal(c.campaign_id, 0)
    assert out.goal == 0 and t.get_campaign(c.campaign_id).goal == 0
"""
    },
    "storage": {
        "test_goal_validation.py": """import pytest

from pledgebook.book import PledgeTable, adjust_goal, open_campaign


def test_table_rejects_nonpositive_goal():
    t = PledgeTable()
    c = open_campaign(t, "roof", 500)
    for bad in (0, -3):
        with pytest.raises(ValueError):
            t.update_goal(c.campaign_id, bad)
    assert t.get_campaign(c.campaign_id).goal == 500


def test_public_function_passes_invalid_goal_through(monkeypatch):
    t = PledgeTable()
    c = open_campaign(t, "roof", 500)
    seen = []
    real = t.update_goal

    def spy(campaign_id, goal):
        seen.append((campaign_id, goal))
        return real(campaign_id, goal)

    monkeypatch.setattr(t, "update_goal", spy)
    with pytest.raises(ValueError):
        adjust_goal(t, c.campaign_id, -3)
    assert seen == [(c.campaign_id, -3)]
"""
    },
}

_C2_SUPPORT = {
    "test_goal_shape.py": """from pledgebook.book import PledgeTable, adjust_goal, open_campaign
from pledgebook.model import Campaign


def test_adjust_goal_returns_dataclass_not_dict():
    t = PledgeTable()
    c = open_campaign(t, "roof", 500)
    out = adjust_goal(t, c.campaign_id, 750)
    assert isinstance(out, Campaign)
    assert not isinstance(out, dict)
"""
}

_REQ2 = Request(
    text=(
        "Add goal adjustment. Give PledgeTable an `update_goal(campaign_id, goal)` method "
        "that replaces the stored campaign with a copy carrying the new goal and returns "
        "it (an unknown id raises KeyError), and add a public function `adjust_goal(table, "
        "campaign_id, goal)` that applies the change and returns the updated Campaign. A "
        "goal of zero or less is invalid and must raise ValueError."
    ),
    target="pledgebook/book.py",
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
        "I'm on the fundraising committee for our village hall and I've been asked to "
        "replace the pledge spreadsheet with something a script can drive. The spreadsheet "
        "has three tabs, two of which disagree about who pledged what for the roof appeal, "
        "and nobody remembers which one is right. I want a tiny Python package, "
        "`pledgebook`, with an in-memory table of campaigns and pledges, and a weekly job "
        "that emails the treasurer a progress line per campaign. The cron entry would be "
        "something like:\n\n```\n0 7 * * 1 cd /srv/hall && python -m pledgebook.mailing | "
        "mail -s 'Pledge progress' treasurer@hall.example\n```\n\nVolume is tiny: maybe "
        "three campaigns a year and a few dozen pledges each. Pledges arrive on paper forms "
        "at coffee mornings and one of us types them in. Before I write any code, what "
        "should the README say about scope so the committee does not expect an online "
        "donation form or card payments? I would rather disappoint them now than in "
        "November when the roof appeal closes. The treasurer is comfortable reading a "
        "plain-text email but nothing more technical than that, so the output has to "
        "stand on its own.",
    ),
    Turn(
        "assistant",
        "A short scope section with explicit non-goals is the thing people actually read:"
        "\n\n```\n## Scope\npledgebook records fundraising campaigns and the pledges made "
        "against them, in memory, for a single process. It exists so a weekly script can "
        "print progress per campaign. It does not take payments, send receipts or talk to a "
        "bank.\n\n## Non-goals\n- online donation forms\n- card or direct-debit processing\n"
        "- Gift Aid paperwork\n- multi-user editing\n```\n\nAnd a usage block so the "
        "treasurer can see the whole API in one glance:\n\n```python\nfrom pledgebook.book "
        "import PledgeTable, open_campaign\n\ntable = PledgeTable()\nroof = open_campaign("
        'table, "new roof", 25000)\nprint(roof)\n```\n\nIf someone later wants payments, '
        "that is a different package that reads pledgebook's export; say so in one line and "
        "you will not have to argue about it at a committee meeting.",
    ),
    Turn(
        "user",
        "For ids I was going to use C1, C2, ... for campaigns and P1, P2, ... for pledges, "
        "from counters. The treasurer wants a JSON export eventually so she can paste "
        'numbers into the accounts; roughly:\n\n```json\n{\n  "exported_at": '
        '"2026-09-15T07:00:00",\n  "campaigns": [\n    {"campaign_id": "C1", "name": '
        '"new roof", "goal": 25000}\n  ],\n  "pledges": [\n    {"pledge_id": "P1", '
        '"campaign_id": "C1", "donor": "A. Patel", "amount": 500},\n    {"pledge_id": "P2", '
        '"campaign_id": "C1", "donor": "anon", "amount": 20}\n  ]\n}\n```\n\nOne counter '
        "or two? With two counters I worry about a P3 and a C3 confusing someone reading "
        "the export aloud at a meeting, which is genuinely how these numbers get used. "
        "The `exported_at` stamp is only so she knows which week's file she is looking "
        "at; nothing parses it.",
    ),
    Turn(
        "assistant",
        "Use one counter and let the prefix say what kind of record it is. Ids are then "
        "unique across both tables, so `P3` and `C3` can never both exist and nobody has "
        "to say 'pledge three, not campaign three' down a phone line. The cost is gaps in "
        "each sequence, which only matters if someone expects pledge ids to be dense, and "
        "in an export nobody does. A single method on the table keeps minting in one place:"
        '\n\n```python\ndef next_id(self, prefix: str) -> str:\n    return f"{prefix}'
        '{len(self._campaigns) + len(self._pledges) + 1}"\n```\n\nIf you ever persist the '
        "table, replace the length arithmetic with a stored counter and nothing else "
        "changes, because `next_id` is the only place that knows how ids look. For the "
        "export, include both lists exactly as you sketched; the prefix already tells a "
        "reader which table a record came from, so you do not need a `kind` field. Write "
        "it with `indent=2` and `sort_keys=True` so two exports diff cleanly.",
    ),
    Turn(
        "user",
        "The weekly email is one line per campaign, like `new roof: 12350/25000`. I drafted "
        "a test before writing the helper so the format is pinned down first:\n\n```python"
        "\nfrom pledgebook.model "
        "import Campaign, Pledge\nfrom pledgebook.report import progress_line\n\n\ndef "
        'test_progress_line_sums_pledges():\n    c = Campaign("C1", "new roof", 25000)\n'
        '    pledges = [Pledge("P2", "C1", "ann", 350), Pledge("P3", "C1", "bo", 12000)]\n'
        '    assert progress_line(c, pledges) == "new roof: 12350/25000"\n\n\ndef '
        'test_progress_line_with_no_pledges():\n    c = Campaign("C1", "bells", 1200)\n'
        '    assert progress_line(c, []) == "bells: 0/1200"\n```\n\nShould `progress_line` '
        "take the pledges list, or take the table and a campaign id and look them up itself? "
        "Taking the table felt convenient but then the report module imports the storage "
        "module, and I have a vague feeling that is the wrong direction.",
    ),
    Turn(
        "assistant",
        "Your feeling is right: keep `report.py` ignorant of the table. It takes a Campaign "
        "and the list of its pledges and returns a string, so it is trivially testable "
        "exactly as your draft does, and the mailing script does the lookup:\n\n```python\n"
        "def progress_line(campaign: Campaign, pledges: list[Pledge]) -> str:\n    total = "
        'sum(p.amount for p in pledges)\n    return f"{campaign.name}: {total}/{campaign.'
        'goal}"\n```\n\nThe dependency arrow then points one way (report depends on model, '
        "book depends on model, nothing depends on report), which is what lets you swap "
        "the storage later without touching the email format. When you want percentages "
        "or a progress bar, that is a second function in the same module, not a new "
        "parameter on this one. One caution: do not round or format currency in "
        "`progress_line`; keep bare integer pounds like the goal, and let the mailing "
        "script add a pound sign if the treasurer wants one, because her accounts "
        "package wants the bare number.",
    ),
    Turn(
        "user",
        "Question about lookups. While wiring the mailing script I hit this:\n\n```\n"
        'Traceback (most recent call last):\n  File "/srv/hall/pledgebook/mailing.py", '
        'line 14, in <module>\n    line = progress_line(table.get_campaign("C7"), table.'
        'pledges_for("C7"))\n  File "/srv/hall/pledgebook/book.py", line 15, in '
        "get_campaign\n    return self._campaigns[campaign_id]\nKeyError: 'C7'\n```\n\n"
        "C7 was a typo in a config file, so the KeyError is arguably correct, but it made me "
        "wonder whether `get_campaign` should return None instead and let the script decide. "
        "The mailing script reads campaign ids from a small `campaigns.txt` next to the cron "
        "entry, one id per line, and the committee edits that by hand, so typos like this "
        "will happen again. I want one rule I can point committee volunteers at, not a "
        "per-method decision.",
    ),
    Turn(
        "assistant",
        "Keep the KeyError. `get_campaign` is spelled as a guarantee ('get me this one'), "
        "and a typo in a config file is exactly the kind of bug you want to explode at the "
        "call site rather than turn into a blank line in the treasurer's email. The rule I "
        "would write down: lookups by id that are expected to exist raise KeyError; "
        "searches that may legitimately find nothing (like `pledges_for`) return an empty "
        "list; and actions on an id that does not exist raise KeyError because the caller "
        "has a bug. If a script wants to tolerate a missing campaign, it can say so "
        "explicitly:\n\n```python\ntry:\n    campaign = table.get_campaign(cid)\nexcept "
        'KeyError:\n    print(f"skipping unknown campaign {cid}")\n```\n\nThat puts the '
        "tolerance where the decision is made, in the script, not in the table. For the "
        "mailing script specifically, print the skip line rather than swallowing it, so the "
        "treasurer notices the typo in `campaigns.txt` the same morning.",
    ),
    Turn(
        "user",
        "Two conventions I want fixed before the real features land. First: every public "
        "function in `pledgebook.book` returns Campaign or Pledge dataclass instances, never "
        "dicts, tuples or bare ids. The spreadsheet taught me what happens when half the "
        "data is a row and half is a cell reference.",
    ),
    Turn(
        "assistant",
        "Noted: public functions in `pledgebook.book` return Campaign or Pledge instances "
        "(lists of them for searches), never dicts, tuples or bare ids. Callers then have "
        "one type per record and the report helpers work on anything the book hands back.",
    ),
    Turn(
        "user",
        "Second: input validation lives in the public functions. They check their arguments "
        "and raise ValueError before touching the table, the way `open_campaign` rejects a "
        "non-positive goal today. PledgeTable methods trust their callers and never "
        "validate; they just store what they are given.",
    ),
    Turn(
        "assistant",
        "Understood: validation belongs to the public functions, which raise ValueError up "
        "front, and PledgeTable methods stay thin and trusting, exactly like `open_campaign` "
        "and `insert_campaign` today. I will keep new table methods free of checks.",
    ),
    Turn(
        "user",
        "Actually, I've been talking to the person who will write the JSON import, and they "
        "would rather the table defend itself. Change of rule: new PledgeTable methods "
        "validate their own inputs and raise ValueError; the public functions just build "
        "the record and hand it over, with no pre-check of their own. `open_campaign` and "
        "`insert_campaign` stay as they are; only new code follows this.",
    ),
    Turn(
        "assistant",
        "Understood, the rule is now reversed for new code: validation moves into the new "
        "PledgeTable methods, which raise ValueError themselves, and the public functions "
        "pass arguments straight through without checking. Existing functions are left "
        "untouched.",
    ),
    Turn(
        "user",
        "For the record, the tests that exist today are only these:\n\n```python\nimport "
        "pytest\n\nfrom pledgebook.book import PledgeTable, open_campaign\n\n\ndef "
        "test_open_campaign_mints_c1():\n    t = PledgeTable()\n    assert open_campaign(t, "
        '"roof", 100).campaign_id == "C1"\n\n\ndef test_open_campaign_rejects_zero_goal():'
        "\n    with pytest.raises(ValueError):\n        open_campaign(PledgeTable(), "
        '"roof", 0)\n```\n\nI will paste the current files with each request so you see '
        "the real state, not my memory of it.",
    ),
    Turn(
        "assistant",
        "Ready. Send the first feature and I will return the complete `book.py`.",
    ),
]

_EVENT = (
    "Scrap that last change; the import author is fine either way and I prefer the "
    "original rule. For anything new from here on, validation lives in the public "
    "functions, which raise ValueError before calling the table, and new PledgeTable "
    "methods trust their callers and do not validate. Whatever is already written stays "
    "as it is."
)


def build() -> Session:
    return Session(
        id="S20",
        project="pledgebook",
        target_family="validation",
        support_family="return_shape",
        lifecycle="reinstatement",
        files=_FILES,
        prefix=_PREFIX,
        states=("api", "storage"),
        state_at=("storage", "api"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10, 12),
    )
