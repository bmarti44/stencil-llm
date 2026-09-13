# ruff: noqa: E501
"""S36: volunteer hours — missing_record (target, reinstatement) x return_shape (support)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""volhours package."""\n'

_MODEL = '''"""Volunteer records as plain dicts."""


def new_volunteer(volunteer_id, name):
    return {"volunteer_id": volunteer_id, "name": name, "hours": 0.0, "role": "general", "active": True}
'''

_ROSTER = '''"""In-memory volunteer roster."""

from volhours.model import new_volunteer


class Roster:
    def __init__(self):
        self._people = {}
        self._n = 0

    def join(self, name):
        self._n += 1
        person = new_volunteer(f"V{self._n}", name)
        self._people[person["volunteer_id"]] = person
        return person

    def find(self, volunteer_id):
        return self._people.get(volunteer_id)

    def log_hours(self, volunteer_id, hours):
        person = self._people[volunteer_id]
        person["hours"] += hours
        return person
'''

_TIERS = '''"""Recognition tiers for the annual thank-you letters."""


def tier(person):
    hours = person["hours"]
    return "gold" if hours >= 100 else "silver" if hours >= 50 else "bronze"
'''

_FILES = {
    "volhours/__init__.py": _INIT,
    "volhours/model.py": _MODEL,
    "volhours/roster.py": _ROSTER,
    "volhours/tiers.py": _TIERS,
}

# ----------------------------------------------------------------- checkpoint 1: set_role

_C1_FUNCTIONAL = {
    "test_set_role_functional.py": """from volhours.roster import Roster


def test_set_role_updates_and_stores():
    roster = Roster()
    person = roster.join("Amara Boateng")
    out = roster.set_role(person["volunteer_id"], "driver")
    assert out["role"] == "driver"
    assert roster.find(person["volunteer_id"])["role"] == "driver"


def test_set_role_keeps_hours_name_and_active():
    roster = Roster()
    person = roster.join("Rob Whitfield")
    roster.log_hours(person["volunteer_id"], 3.5)
    out = roster.set_role(person["volunteer_id"], "sorter")
    assert out["hours"] == 3.5 and out["name"] == "Rob Whitfield"
    assert out["active"] is True and out["volunteer_id"] == person["volunteer_id"]
"""
}

_C1_REGRESSION = {
    "test_set_role_regression.py": """import pytest

from volhours.roster import Roster
from volhours.tiers import tier


def test_join_find_log_hours_unchanged():
    roster = Roster()
    person = roster.join("Amara Boateng")
    assert person["volunteer_id"] == "V1" and person["role"] == "general"
    assert roster.find("V1") is person
    assert roster.find("V9") is None
    assert roster.log_hours("V1", 2.0)["hours"] == 2.0
    assert tier(person) == "bronze"
    with pytest.raises(KeyError):
        roster.log_hours("V9", 1.0)
"""
}

_C1_CONTRACT = {
    "raise": {
        "test_set_role_missing.py": """import pytest

from volhours.roster import Roster


def test_set_role_unknown_raises_keyerror():
    roster = Roster()
    roster.join("Amara Boateng")
    with pytest.raises(KeyError):
        roster.set_role("V99", "driver")
"""
    },
    "none": {
        "test_set_role_missing.py": """from volhours.roster import Roster


def test_set_role_unknown_returns_none_and_changes_nothing():
    roster = Roster()
    person = roster.join("Amara Boateng")
    assert roster.set_role("V99", "driver") is None
    assert roster.find("V99") is None
    assert roster.find(person["volunteer_id"])["role"] == "general"
"""
    },
}

_C1_SUPPORT = {
    "test_set_role_shape.py": """from dataclasses import is_dataclass

from volhours.roster import Roster


def test_set_role_returns_plain_dict():
    roster = Roster()
    person = roster.join("Amara Boateng")
    out = roster.set_role(person["volunteer_id"], "driver")
    assert type(out) is dict
    assert not is_dataclass(out)
"""
}

_LOOKUP = {
    "raise": "        person = self._people[volunteer_id]\n",
    "none": (
        "        person = self._people.get(volunteer_id)\n"
        "        if person is None:\n"
        "            return None\n"
    ),
}


def _gold1(state: str) -> str:
    return (
        _ROSTER.rstrip("\n")
        + "\n\n    def set_role(self, volunteer_id, role):\n"
        + _LOOKUP[state]
        + '        person["role"] = role\n'
        "        return person\n"
    )


_REQ1 = Request(
    text=(
        "Add a public method `set_role(volunteer_id, role)` on Roster: it sets the "
        'volunteer\'s role to the given string (for example "driver" or "sorter") and '
        "returns the volunteer record."
    ),
    target="volhours/roster.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"raise": _gold1("raise"), "none": _gold1("none")},
)

# ----------------------------------------------------------------- checkpoint 2: retire

_C2_FUNCTIONAL = {
    "test_retire_functional.py": """from volhours.roster import Roster


def test_retire_marks_inactive_and_stores():
    roster = Roster()
    person = roster.join("Amara Boateng")
    out = roster.retire(person["volunteer_id"])
    assert out["active"] is False
    assert roster.find(person["volunteer_id"])["active"] is False


def test_retire_keeps_hours_and_role():
    roster = Roster()
    person = roster.join("Rob Whitfield")
    roster.log_hours(person["volunteer_id"], 12.0)
    roster.set_role(person["volunteer_id"], "driver")
    out = roster.retire(person["volunteer_id"])
    assert out["hours"] == 12.0 and out["role"] == "driver"
    assert out["volunteer_id"] == person["volunteer_id"]
"""
}

_C2_REGRESSION = {
    "test_retire_regression.py": """import pytest

from volhours.roster import Roster


def test_join_find_log_hours_set_role_unchanged():
    roster = Roster()
    person = roster.join("Amara Boateng")
    assert roster.find("V1") is person and roster.find("V9") is None
    assert roster.log_hours("V1", 2.0)["hours"] == 2.0
    assert roster.set_role("V1", "sorter")["role"] == "sorter"
    assert roster.set_role("V9", "sorter") is None
    with pytest.raises(KeyError):
        roster.log_hours("V9", 1.0)
"""
}

_C2_CONTRACT = {
    "raise": {
        "test_retire_missing.py": """import pytest

from volhours.roster import Roster


def test_retire_unknown_raises_keyerror():
    roster = Roster()
    roster.join("Amara Boateng")
    with pytest.raises(KeyError):
        roster.retire("V99")
"""
    },
    "none": {
        "test_retire_missing.py": """from volhours.roster import Roster


def test_retire_unknown_returns_none_and_changes_nothing():
    roster = Roster()
    person = roster.join("Amara Boateng")
    assert roster.retire("V99") is None
    assert roster.find("V99") is None
    assert roster.find(person["volunteer_id"])["active"] is True
"""
    },
}

_C2_SUPPORT = {
    "test_retire_shape.py": """from dataclasses import is_dataclass

from volhours.roster import Roster


def test_retire_returns_plain_dict():
    roster = Roster()
    person = roster.join("Amara Boateng")
    out = roster.retire(person["volunteer_id"])
    assert type(out) is dict
    assert not is_dataclass(out)
"""
}


def _gold2(state: str) -> str:
    # Built on the checkpoint-1 gold under the state then in force (none).
    return (
        _gold1("none").rstrip("\n")
        + "\n\n    def retire(self, volunteer_id):\n"
        + _LOOKUP[state]
        + '        person["active"] = False\n'
        "        return person\n"
    )


_REQ2 = Request(
    text=(
        "Add a public method `retire(volunteer_id)` on Roster for volunteers who have "
        "stepped down: it marks the record inactive (active = False), keeps the hours and "
        "role for the records, and returns the volunteer record."
    ),
    target="volhours/roster.py",
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
        "I coordinate volunteers at a community food pantry and I'm building a small "
        "package, volhours, to replace the paper sign-in sheets we add up by hand every "
        "December for the thank-you letters. Roughly forty volunteers, hours logged from "
        "the sheets once a week, and at year end we need a total per person and a "
        "recognition tier. I want an in-memory Roster that my weekly script drives, and a "
        "printout like:\n\n```\n$ python -m volhours.yearend\nV1  Amara Boateng   112.5h  "
        "gold\nV2  Rob Whitfield    38.0h  bronze\nV3  Sunita Rao       61.0h  silver\n"
        "```\n\nCan you draft a README scope section? The trustees asked whether this "
        "will do rota scheduling and DBS-check tracking, and I need a paragraph that says "
        "no in a way that does not sound like I am refusing to help. It is a tally of hours "
        "and nothing more, run by one person on a laptop.",
    ),
    Turn(
        "assistant",
        "Here is a scope section that says no politely by saying what it is:\n\n```\n## "
        "Scope\nvolhours keeps an in-memory roster of volunteers and the hours each has "
        "given, so the coordinator can log a week's sign-in sheets and print the year-end "
        "totals and recognition tiers. It is a tally, not a volunteer management system: "
        "it holds no contact details, no rota and no compliance records, and it stores "
        "nothing between runs on its own.\n\n## Non-goals\n- rota or shift scheduling\n- "
        "DBS or training records\n- contact details or messaging\n```\n\nA usage block "
        "shows the API shape:\n\n```python\nfrom volhours.roster import Roster\n\nroster = "
        'Roster()\nperson = roster.join("Amara Boateng")\nroster.log_hours(person['
        '"volunteer_id"], 4.0)\nprint(person["hours"])\n```\n\nTrustees tend to read the '
        "non-goals list first, and 'no contact details' usually ends the compliance "
        "question on its own. The usage block also shows the treasurer what a record "
        "looks like without opening the JSON.",
    ),
    Turn(
        "user",
        "Records. I've gone with plain dicts built by `new_volunteer` rather than a class, "
        "partly because the weekly script writes the roster out as JSON so the treasurer "
        "can open it, and partly because two of the other coordinators know just enough "
        "Python to read a dict and no more. Is that a defensible choice or am I storing up "
        'trouble? The JSON file currently looks like:\n\n```json\n[\n  {"volunteer_id": '
        '"V1", "name": "Amara Boateng", "hours": 112.5, "role": "driver", "active": true},\n'
        '  {"volunteer_id": "V2", "name": "Rob Whitfield", "hours": 38.0, "role": "general", '
        '"active": true}\n]\n```\n\nand I would like the in-memory records to be exactly '
        "that shape so there is no translation step either way. The treasurer only wants "
        "to open it once a year to check the gold-tier list against the letters.",
    ),
    Turn(
        "assistant",
        "Defensible, given who reads it. Dicts that match the JSON exactly mean `json.dump` "
        "and `json.load` are the whole persistence layer, and your co-coordinators can "
        "open the file and understand it. The trouble to guard against is shape drift: a "
        "record missing a key because it was built by hand. Keep `new_volunteer` as the "
        "only constructor and the shape stays fixed; loading can normalise old files by "
        "merging defaults:\n\n```python\ndef load(rows):\n    return [{**new_volunteer(r["
        '"volunteer_id"], r["name"]), **r} for r in rows]\n```\n\nThat way a file written '
        'before `role` existed still loads with `role: "general"`, and the in-memory '
        "record is always the full shape. Your two co-coordinators can then rely on every "
        "key being present without learning what a default is. The one thing to avoid is "
        "building a record dict by hand anywhere else in the package or the scripts.",
    ),
    Turn(
        "user",
        "I wrote the tier tests first because the thresholds come from the trustees and "
        "they will argue about them:\n\n```python\nfrom volhours.model import new_volunteer\n"
        "from volhours.tiers import tier\n\n\ndef test_bronze_below_fifty():\n    person = "
        'new_volunteer("V1", "a")\n    person["hours"] = 49.5\n    assert tier(person) == '
        '"bronze"\n\n\ndef test_silver_at_fifty():\n    person = new_volunteer("V1", "a")\n'
        '    person["hours"] = 50.0\n    assert tier(person) == "silver"\n\n\ndef test_gold_'
        'at_hundred():\n    person = new_volunteer("V1", "a")\n    person["hours"] = 100.0\n'
        '    assert tier(person) == "gold"\n```\n\nIs it worth a fourth test for someone '
        "with zero hours, or is that covered? Last year a volunteer who had joined in "
        "November got a letter saying 'thank you for your 0 hours' and it was awkward. She "
        "laughed it off but the trustees did not.",
    ),
    Turn(
        "assistant",
        "The boundaries are covered; the zero case is not really a tier question, it is a "
        "letters question. `tier` should stay a pure mapping from hours to a label, and the "
        "year-end script should skip anyone below a floor rather than teaching `tier` about "
        'awkwardness:\n\n```python\nfor person in roster.all():\n    if person["hours"] < '
        "1.0:\n        continue\n    print(line(person))\n```\n\nA fourth test that pins `tier` "
        "at 0.0 returning `bronze` is still cheap and documents that the function itself "
        "has no floor. Put the skip threshold in the script with a comment referencing the "
        "November letter so the next coordinator understands why it exists. Keeping the "
        "floor out of `tier` also means the trustees can argue about thresholds without the "
        "letter logic being tangled up in it. If the thresholds change, only the two "
        "numbers in `tier` and the three boundary tests move.",
    ),
    Turn(
        "user",
        "Loading last year's file blew up on the first record:\n\n```\n>>> tier(rows[0])\n"
        'Traceback (most recent call last):\n  File "<stdin>", line 1, in <module>\n  File '
        '"volhours/tiers.py", line 5, in tier\n    hours = person["hours"]\nKeyError: '
        "'hours'\n```\n\nIt turns out the 2024 file used `total_hours` and the 2025 one "
        "used `hours`, because I renamed it midway and never converted the old file. Should "
        "`tier` tolerate both spellings, or should loading fix the record before anything "
        "else sees it? I would rather not sprinkle `.get` calls through every helper. There "
        "are only three helpers today but I can see there being a dozen by next December, "
        "and each one tolerating two spellings is exactly the kind of mess the spreadsheet "
        "already is.",
    ),
    Turn(
        "assistant",
        "Fix it at the boundary. Helpers like `tier` should trust the record shape, and the "
        "loader is the one place that knows about old spellings:\n\n```python\nRENAMED = "
        '{"total_hours": "hours"}\n\n\ndef load(rows):\n    out = []\n    for r in rows:\n'
        "        r = {RENAMED.get(k, k): v for k, v in r.items()}\n        out.append({**new_"
        'volunteer(r["volunteer_id"], r["name"]), **r})\n    return out\n```\n\nThat handles '
        'the 2024 file once, and every helper keeps the plain `person["hours"]` access '
        "that your co-coordinators can read. Add one test that loads a 2024-shaped row and "
        "asserts `hours` is present, so the rename cannot bite a third time. The `RENAMED` "
        "table is also where any future rename goes, with the year it happened in a "
        "comment.",
    ),
    Turn(
        "user",
        "Conventions, then, before more features. First, return shape: public Roster "
        "methods return the volunteer record as a plain dict, the exact shape "
        "`new_volunteer` builds and the JSON file holds. No dataclasses, no tuples. If a "
        "method changes a record it returns that record, so the weekly script can dump it "
        "straight to the file.",
    ),
    Turn(
        "assistant",
        "Noted: every public Roster method returns the plain record dict (or None from a "
        "lookup that finds nothing), never a dataclass or tuple. Methods that change a "
        "record mutate the stored dict in place and return that same dict, so the weekly "
        "script can write it straight back out as JSON. Nothing public will return a bare "
        "number or a tuple of fields.",
    ),
    Turn(
        "user",
        "Second, unknown ids: an action on a volunteer id that is not in the roster raises "
        "KeyError, as `log_hours` does. Lookups like `find` return None; actions raise. "
        "Hours typed against a wrong id are hours lost, so I want the traceback. My weekly "
        "script wraps the whole sheet in one try/except and prints the offending row.",
    ),
    Turn(
        "assistant",
        "Understood: actions on an unknown volunteer id raise KeyError, matching "
        "`log_hours`, while `find` stays a None-returning lookup. New methods will index "
        "`self._people[volunteer_id]` directly so the KeyError names the id, with no "
        "separate existence check in front of it. The weekly script's try/except around "
        "the sheet then catches exactly the row that was mistyped.",
    ),
    Turn(
        "user",
        "Actually, change that after this week's session. The new sign-in app exports ids "
        "that do not always match ours yet, and my import script now checks results rather "
        "than catching exceptions. So for new Roster actions from now on: an unknown id "
        "returns None and changes nothing. `log_hours` stays exactly as it is, since the "
        "hours import still goes through the old path and its try/except.",
    ),
    Turn(
        "assistant",
        "Got it: new Roster actions return None on an unknown volunteer id and leave the "
        "roster untouched; `log_hours` keeps raising as before. New methods will use "
        "`.get`, return None when the id is missing, and only touch the record when it "
        "exists. The import script checks for None and logs the unmatched id, so nothing "
        "is lost silently on that path either.",
    ),
    Turn(
        "user",
        "For reference the only roster tests today are these, plus the tier ones:\n\n"
        "```python\nimport pytest\n\nfrom volhours.roster import Roster\n\n\ndef test_join_"
        'sequential_ids():\n    roster = Roster()\n    assert roster.join("a")["volunteer_id"]'
        ' == "V1"\n    assert roster.join("b")["volunteer_id"] == "V2"\n\n\ndef test_log_'
        "hours_unknown_raises():\n    with pytest.raises(KeyError):\n        Roster().log_"
        'hours("V1", 1.0)\n```',
    ),
    Turn(
        "assistant",
        "Good baseline; I will keep those green and add tests next to each new method. Send "
        "the first request with the current files and I will return the full roster "
        "module, existing methods untouched and the new one added at the end of the "
        "class, plus a note on the tests I would add beside it.",
    ),
]

_EVENT = (
    "Reverting the unknown-id change: the sign-in app now exports our ids exactly, and the "
    "None results were hiding a bad mapping for two weeks. From now on new Roster actions "
    "raise KeyError on an unknown volunteer id again, like `log_hours`. What is already in "
    "the roster stays as it is."
)


def build() -> Session:
    return Session(
        id="S36",
        project="volhours",
        target_family="missing_record",
        support_family="return_shape",
        lifecycle="reinstatement",
        files=_FILES,
        prefix=_PREFIX,
        states=("raise", "none"),
        state_at=("none", "raise"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10, 12),
    )
