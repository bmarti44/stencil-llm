# ruff: noqa: E501
"""S09: plant watering — naming (target, stable) x error_surface=propagate (support)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""plantcare package."""\n'

_MODEL = '''"""Plant records and the package error base class."""

from dataclasses import dataclass, replace
from datetime import date


class PlantCareError(Exception):
    """Base class for errors the package raises on its own behalf."""


@dataclass(frozen=True)
class Plant:
    plant_id: str
    name: str
    interval_days: int
    last_watered: date | None = None

    def watered_on(self, day: date) -> "Plant":
        return replace(self, last_watered=day)
'''

_SCHEDULE = '''"""Date and interval parsing plus due-date arithmetic."""

from datetime import date, timedelta

from plantcare.model import Plant

UNITS = {"d": 1, "w": 7}


def parse_date(text: str) -> date:
    return date.fromisoformat(text.strip())


def parse_interval(text: str) -> int:
    key = text.strip().lower()
    if len(key) < 2 or key[-1] not in UNITS or not key[:-1].isdigit():
        raise ValueError(f"bad interval: {text!r}")
    days = int(key[:-1]) * UNITS[key[-1]]
    if days <= 0:
        raise ValueError(f"interval must be positive: {text!r}")
    return days


def due_on(plant: Plant) -> date | None:
    if plant.last_watered is None:
        return None
    return plant.last_watered + timedelta(days=plant.interval_days)
'''

_STORE = '''"""In-memory plant register."""

from plantcare.model import Plant


class PlantStore:
    def __init__(self) -> None:
        self._plants: dict[str, Plant] = {}
        self._counter = 0

    def add_plant(self, name: str, interval_days: int = 7) -> Plant:
        self._counter += 1
        plant = Plant(plant_id=f"L{self._counter}", name=name, interval_days=interval_days)
        self._plants[plant.plant_id] = plant
        return plant

    def find(self, plant_id: str) -> Plant | None:
        return self._plants.get(plant_id)

    def count(self) -> int:
        return len(self._plants)
'''

_FILES = {
    "plantcare/__init__.py": _INIT,
    "plantcare/model.py": _MODEL,
    "plantcare/schedule.py": _SCHEDULE,
    "plantcare/store.py": _STORE,
}

# ----------------------------------------------------------------- checkpoint 1: record a watering

_C1_HELPER = """from datetime import date

import pytest

from plantcare.model import PlantCareError
from plantcare.store import PlantStore


def _record(store):
    fn = getattr(store, "record_watering", None) or getattr(store, "watering_record", None)
    assert fn is not None, "no record method found"
    return fn
"""

_C1_FUNCTIONAL = {
    "test_record_functional.py": _C1_HELPER
    + """

def _two(store, name, interval):
    # A keeper plant plus the plant under test. The keeper already carries a
    # non-default last_watered, so a reply that rebuilds the whole mapping or
    # resets an unrelated defaulted field cannot hide behind a bare fixture.
    keeper = store.add_plant("keeper", 5)
    _record(store)(keeper.plant_id, "2026-08-01")
    target = store.add_plant(name, interval)
    return keeper, target


def _check_keeper(store, keeper):
    kept = store.find(keeper.plant_id)
    assert kept is not None, "the other plant was dropped"
    assert kept.name == "keeper" and kept.interval_days == 5
    assert kept.last_watered == date(2026, 8, 1)
    assert store.count() == 2


def test_record_sets_last_watered_and_stores():
    s = PlantStore()
    keeper, p = _two(s, "monstera", 10)
    out = _record(s)(p.plant_id, "2026-09-10")
    assert out.last_watered == date(2026, 9, 10)
    assert s.find(p.plant_id).last_watered == date(2026, 9, 10)
    _check_keeper(s, keeper)


def test_record_keeps_name_interval_and_id():
    s = PlantStore()
    keeper, p = _two(s, "fern", 3)
    out = _record(s)(p.plant_id, " 2026-09-11 ")
    assert out.plant_id == p.plant_id and out.name == "fern" and out.interval_days == 3
    back = s.find(p.plant_id)
    assert back.name == "fern" and back.interval_days == 3
    _check_keeper(s, keeper)


def test_record_later_date_overwrites_earlier():
    s = PlantStore()
    keeper, p = _two(s, "basil", 2)
    _record(s)(p.plant_id, "2026-09-01")
    out = _record(s)(p.plant_id, "2026-09-05")
    assert out.last_watered == date(2026, 9, 5)
    assert s.find(p.plant_id).last_watered == date(2026, 9, 5)
    _check_keeper(s, keeper)


def test_record_unknown_plant_raises_keyerror():
    s = PlantStore()
    keeper, _p = _two(s, "cactus", 30)
    with pytest.raises(KeyError):
        _record(s)("L42", "2026-09-10")
    _check_keeper(s, keeper)


def test_record_bad_date_leaves_plant_untouched():
    s = PlantStore()
    keeper, p = _two(s, "cactus", 30)
    with pytest.raises(Exception):
        _record(s)(p.plant_id, "10/09/2026")
    assert s.find(p.plant_id).last_watered is None
    _check_keeper(s, keeper)
"""
}

_C1_REGRESSION = {
    "test_record_regression.py": """from datetime import date

from plantcare.model import Plant
from plantcare.schedule import due_on, parse_date, parse_interval
from plantcare.store import PlantStore


def test_add_find_count_unchanged():
    s = PlantStore()
    p = s.add_plant("monstera")
    assert p.plant_id == "L1" and p.interval_days == 7 and p.last_watered is None
    assert s.find("L1") is p and s.find("L9") is None
    assert s.count() == 1


def test_store_keeps_every_plant_it_is_given():
    s = PlantStore()
    a = s.add_plant("fern", 3)
    b = s.add_plant("monstera")
    assert (a.plant_id, b.plant_id) == ("L1", "L2")
    assert s.find("L1") is a and s.find("L2") is b
    assert s.count() == 2
    assert b.interval_days == 7 and b.last_watered is None


def test_schedule_helpers_unchanged():
    assert parse_date("2026-09-10") == date(2026, 9, 10)
    assert parse_interval("2w") == 14
    p = Plant("L1", "x", 5, date(2026, 9, 1))
    assert due_on(p) == date(2026, 9, 6)
"""
}

_C1_CONTRACT = {
    "verb_noun": {
        "test_record_naming.py": """from plantcare.store import PlantStore


def test_record_is_verb_noun():
    assert hasattr(PlantStore, "record_watering")
    assert not hasattr(PlantStore, "watering_record")
"""
    },
    "noun_verb": {
        "test_record_naming.py": """from plantcare.store import PlantStore


def test_record_is_noun_verb():
    assert hasattr(PlantStore, "watering_record")
    assert not hasattr(PlantStore, "record_watering")
"""
    },
}

_C1_SUPPORT = {
    "test_record_errors.py": _C1_HELPER
    + """

def test_bad_date_propagates_raw_valueerror():
    s = PlantStore()
    p = s.add_plant("cactus", 30)
    with pytest.raises(ValueError) as info:
        _record(s)(p.plant_id, "10/09/2026")
    assert type(info.value) is ValueError
    assert not isinstance(info.value, PlantCareError)
"""
}


def _gold1(name: str) -> str:
    return (
        _STORE.replace(
            "from plantcare.model import Plant\n",
            "from plantcare.model import Plant\nfrom plantcare.schedule import parse_date\n",
            1,
        ).rstrip("\n")
        + f"""

    def {name}(self, plant_id: str, day_text: str) -> Plant:
        plant = self._plants[plant_id]
        watered = plant.watered_on(parse_date(day_text))
        self._plants[plant_id] = watered
        return watered
"""
    )


_REQ1 = Request(
    text=(
        "Add a public method on PlantStore that records a watering: it takes a plant id "
        "and the date as ISO text (use parse_date from schedule.py), sets last_watered to "
        "that date, stores the updated plant and returns it. An unknown id raises "
        "KeyError. Text that is not a date must leave the plant untouched."
    ),
    target="plantcare/store.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={
        "verb_noun": _gold1("record_watering"),
        "noun_verb": _gold1("watering_record"),
    },
)

# ----------------------------------------------------------------- checkpoint 2: change the interval

_C2_HELPER = """from datetime import date

import pytest

from plantcare.model import PlantCareError
from plantcare.store import PlantStore


def _set_interval(store):
    fn = getattr(store, "set_interval", None) or getattr(store, "interval_set", None)
    assert fn is not None, "no interval method found"
    return fn
"""

_C2_FUNCTIONAL = {
    "test_interval_functional.py": _C2_HELPER
    + """

def _record(store):
    fn = getattr(store, "record_watering", None) or getattr(
        store, "watering_record", None
    )
    assert fn is not None, "no record method found"
    return fn


def _two(store, name, interval):
    # A keeper plant plus the plant under test, both already watered: the
    # interval change must not drop the keeper nor reset last_watered.
    keeper = store.add_plant("keeper", 5)
    _record(store)(keeper.plant_id, "2026-08-01")
    target = store.add_plant(name, interval)
    _record(store)(target.plant_id, "2026-08-02")
    return keeper, target


def _check_keeper(store, keeper):
    kept = store.find(keeper.plant_id)
    assert kept is not None, "the other plant was dropped"
    assert kept.name == "keeper" and kept.interval_days == 5
    assert kept.last_watered == date(2026, 8, 1)
    assert store.count() == 2


def test_interval_in_days():
    s = PlantStore()
    keeper, p = _two(s, "monstera", 7)
    out = _set_interval(s)(p.plant_id, "10d")
    assert out.interval_days == 10
    assert s.find(p.plant_id).interval_days == 10
    assert s.find(p.plant_id).last_watered == date(2026, 8, 2)
    _check_keeper(s, keeper)


def test_interval_in_weeks_and_case():
    s = PlantStore()
    keeper, p = _two(s, "fern", 7)
    assert _set_interval(s)(p.plant_id, " 2W ").interval_days == 14
    assert s.find(p.plant_id).interval_days == 14
    assert s.find(p.plant_id).last_watered == date(2026, 8, 2)
    _check_keeper(s, keeper)


def test_interval_keeps_other_fields():
    s = PlantStore()
    keeper, p = _two(s, "basil", 2)
    before = s.find(p.plant_id)
    out = _set_interval(s)(p.plant_id, "3d")
    assert out.plant_id == before.plant_id and out.name == "basil"
    assert out.last_watered == before.last_watered
    back = s.find(p.plant_id)
    assert back.name == "basil" and back.plant_id == before.plant_id
    assert back.last_watered == date(2026, 8, 2)
    _check_keeper(s, keeper)


def test_interval_unknown_plant_raises_keyerror():
    s = PlantStore()
    keeper, _p = _two(s, "cactus", 30)
    with pytest.raises(KeyError):
        _set_interval(s)("L42", "3d")
    _check_keeper(s, keeper)


def test_interval_bad_text_leaves_plant_untouched():
    s = PlantStore()
    keeper, p = _two(s, "cactus", 30)
    for bad in ("ten days", "0d", "3m"):
        with pytest.raises(Exception):
            _set_interval(s)(p.plant_id, bad)
    assert s.find(p.plant_id).interval_days == 30
    assert s.find(p.plant_id).last_watered == date(2026, 8, 2)
    _check_keeper(s, keeper)
"""
}

_C2_REGRESSION = {
    "test_interval_regression.py": """from datetime import date

from plantcare.store import PlantStore


def _record(store):
    return getattr(store, "record_watering", None) or getattr(store, "watering_record", None)


def test_add_find_record_unchanged():
    s = PlantStore()
    p = s.add_plant("monstera", 10)
    assert s.find("L1") is p and s.count() == 1
    assert _record(s)("L1", "2026-09-10").last_watered == date(2026, 9, 10)


def test_record_watering_keeps_the_other_plants():
    s = PlantStore()
    a = s.add_plant("fern", 3)
    b = s.add_plant("monstera", 10)
    _record(s)(a.plant_id, "2026-09-01")
    out = _record(s)(b.plant_id, "2026-09-10")
    assert out.last_watered == date(2026, 9, 10)
    assert s.count() == 2
    kept = s.find(a.plant_id)
    assert kept is not None, "the other plant was dropped"
    assert kept.name == "fern" and kept.interval_days == 3
    assert kept.last_watered == date(2026, 9, 1)
"""
}

_C2_CONTRACT = {
    "verb_noun": {
        "test_interval_naming.py": """from plantcare.store import PlantStore


def test_interval_is_verb_noun():
    assert hasattr(PlantStore, "set_interval")
    assert not hasattr(PlantStore, "interval_set")
"""
    },
    "noun_verb": {
        "test_interval_naming.py": """from plantcare.store import PlantStore


def test_interval_is_noun_verb():
    assert hasattr(PlantStore, "interval_set")
    assert not hasattr(PlantStore, "set_interval")
"""
    },
}

_C2_SUPPORT = {
    "test_interval_errors.py": _C2_HELPER
    + """

def test_bad_interval_propagates_raw_valueerror():
    s = PlantStore()
    p = s.add_plant("cactus", 30)
    with pytest.raises(ValueError) as info:
        _set_interval(s)(p.plant_id, "ten days")
    assert type(info.value) is ValueError
    assert not isinstance(info.value, PlantCareError)
"""
}


def _gold2(name: str) -> str:
    # Built on the checkpoint-1 gold under the state then in force (verb_noun).
    return (
        _gold1("record_watering")
        .replace(
            "from plantcare.model import Plant\n",
            "from dataclasses import replace\n\nfrom plantcare.model import Plant\n",
            1,
        )
        .replace(
            "from plantcare.schedule import parse_date\n",
            "from plantcare.schedule import parse_date, parse_interval\n",
            1,
        )
        .rstrip("\n")
        + f"""

    def {name}(self, plant_id: str, interval_text: str) -> Plant:
        plant = self._plants[plant_id]
        updated = replace(plant, interval_days=parse_interval(interval_text))
        self._plants[plant_id] = updated
        return updated
"""
    )


_REQ2 = Request(
    text=(
        "Add a public method on PlantStore that changes a plant's watering interval: it "
        'takes a plant id and the interval as text like "10d" or "2w" (use parse_interval '
        "from schedule.py), stores the plant with the new interval_days and returns it, "
        "keeping last_watered and everything else as they were. An unknown id raises "
        "KeyError. Text that does not parse must leave the plant untouched."
    ),
    target="plantcare/store.py",
    functional_tests=_C2_FUNCTIONAL,
    regression_tests=_C2_REGRESSION,
    contract_tests=_C2_CONTRACT,
    support_tests=_C2_SUPPORT,
    gold={"verb_noun": _gold2("set_interval"), "noun_verb": _gold2("interval_set")},
)

# ----------------------------------------------------------------- prefix (16 turns)

_PREFIX = [
    Turn(
        "user",
        "I have about thirty houseplants across two flats and a shared office, and the "
        "watering has become a mess: my partner waters the ones I already did, the office "
        "ones dry out over long weekends. I want a small package, plantcare, that a "
        "Raspberry Pi in the hallway drives with a cron job: it keeps the plant list, "
        "records waterings, and prints what is due today on a little e-ink display. The "
        "cron line is just:\n\n```\n0 7 * * * cd /home/pi/plantcare && python -m "
        "plantcare.today >> /home/pi/today.log 2>&1\n```\n\nNo web app, no phone push, "
        "no sensors for now; the moisture-probe project can come later if this works. "
        "Could you write the README scope section so my partner, who is a better "
        "programmer than me and will inevitably want to add a database, understands "
        "what this is and is not?",
    ),
    Turn(
        "assistant",
        "Here is a scope block that says it plainly:\n\n```\n## Scope\nplantcare is an "
        "in-memory plant register for a single process. It keeps Plant records in a "
        "PlantStore, records watering dates, and computes what is due from each plant's "
        "interval. It is a library for scripts and tests; persistence is whatever your "
        "script does with the data (a JSON dump is plenty for thirty plants).\n\n## "
        "Non-goals\n- a database or a service\n- moisture sensors and automation\n- "
        "notifications beyond the display script\n```\n\nThe JSON dump line is aimed at "
        "your partner: it concedes that persistence exists while keeping it out of the "
        "library. A usage snippet helps too:\n\n```python\nfrom plantcare.store import "
        'PlantStore\n\nstore = PlantStore()\nfern = store.add_plant("fern", '
        "interval_days=3)\nprint(store.find(fern.plant_id))\n```",
    ),
    Turn(
        "user",
        "Good. I wrote schedule.py with `parse_date`, `parse_interval` and `due_on`. "
        "`parse_interval` takes '10d' or '2w' because that is how we talk about it "
        "('the fern is every 3d'), and I made it reject zero and anything without a "
        "unit. Is it a mistake to have the parsing helpers raise ValueError, or should "
        "they return None like `find` does? Here is my test draft for the helpers:\n\n"
        "```python\nimport pytest\nfrom datetime import date\n\nfrom plantcare.schedule "
        "import parse_date, parse_interval\n\n\ndef test_parse_date_iso():\n    assert "
        'parse_date(" 2026-09-10 ") == date(2026, 9, 10)\n\n\ndef '
        'test_parse_interval_units():\n    assert parse_interval("10d") == 10\n    assert '
        'parse_interval("2W") == 14\n\n\n@pytest.mark.parametrize("bad", ["", "d", "3m", '
        '"0d", "ten days"])\ndef test_parse_interval_rejects(bad):\n    with pytest.raises'
        "(ValueError):\n        parse_interval(bad)\n```",
    ),
    Turn(
        "assistant",
        "Raising is right for parsers. `find` returns None because 'not found' is a "
        "normal outcome of a search; a string that is not a date is not a normal outcome, "
        "it is bad input, and a None would just move the failure to wherever the None is "
        "used. Your test cases are good; I would add a negative number (`-3d`) and a "
        "float (`1.5w`) to the reject list, both of which `isdigit()` already refuses, so "
        "the tests document the behaviour rather than change it:\n\n```python\n"
        '@pytest.mark.parametrize("bad", ["", "d", "3m", "0d", "ten days", "-3d", '
        '"1.5w"])\n```\n\n`parse_date` delegates to `date.fromisoformat`, which raises '
        "ValueError itself with a clear message, so there is nothing to add there. For "
        "the record, the message you get is the one worth asserting on if you ever want "
        'to:\n\n```\n>>> parse_date("10/09/2026")\nTraceback (most recent call last):\n'
        "  ...\nValueError: Invalid isoformat string: '10/09/2026'\n```\n\nwhich already "
        "names the offending text, so nothing in plantcare needs to repeat it.",
    ),
    Turn(
        "user",
        "Plant ids: I mint L1, L2, ... from a counter. My partner says they should be "
        "slugs from the name ('fern-kitchen') because the display script prints them. "
        "But we have three ferns and I do not want to invent a naming scheme. Should the "
        "id be a slug? Related: yesterday's display script died like this because I "
        "typed an id that does not exist into today.py:\n\n```\nTraceback (most recent "
        'call last):\n  File "/home/pi/plantcare/plantcare/today.py", line 9, in '
        '<module>\n    print(store.find("L31").name)\nAttributeError: '
        "'NoneType' object has no attribute 'name'\n```\n\nThat is my fault, but I would "
        "like a rule so that a typo fails at the right place next time. For scale, the "
        "whole plant list today is:\n\n```\nL1  fern (kitchen)      3d\nL2  monstera   "
        "        10d\nL3  basil              2d\nL4  cactus             30d\nL5  fern "
        "(office)       4d\nL6  pothos             7d\n```\n\nplus two dozen more like "
        "them, so whatever we choose has to be something I can write on a plant label "
        "with a marker.",
    ),
    Turn(
        "assistant",
        "Keep the counter ids. Slugs from names collide (three ferns), change when a plant "
        "is renamed, and the display can print `name` next to the id anyway. The rule "
        "for typos is the usual split: `find` is a search, so it returns None and the "
        "caller branches; methods that *act* on a plant (recording a watering, changing "
        "its interval) take an id that must exist, so they raise KeyError on an unknown "
        "one. Then a typo in today.py fails at the action with `KeyError: 'L31'` "
        "instead of a NoneType attribute error three lines later. If the display script "
        "wants a hard failure from a lookup, a two-line wrapper does it:\n\n```python\n"
        "def require(store, plant_id):\n    plant = store.find(plant_id)\n    if plant is "
        "None:\n        raise KeyError(plant_id)\n    return plant\n```",
    ),
    Turn(
        "user",
        "Agreed: lookups return None, actions raise KeyError. The display script needs "
        "'what is due today'. I was going to write it in today.py rather than the store, "
        "roughly:\n\n```python\ndef due_today(store: PlantStore, today: date) -> "
        "list[Plant]:\n    out = []\n    for plant in store.all():\n        due = "
        "due_on(plant)\n        if due is None or due <= today:\n            out.append("
        "plant)\n    return sorted(out, key=lambda p: p.name)\n```\n\nNever-watered "
        "plants count as due, which I think is right for a new plant. Does that belong "
        "in the store or in the script? And `all()` does not exist yet either.",
    ),
    Turn(
        "assistant",
        "Keep it in the script for now. The store's job is to hold plants and apply "
        "actions to them; 'due today' is a query with a policy in it (never-watered "
        "counts as due, sort by name) that the display owns. If a second consumer needs "
        "the same query, move it into schedule.py as a pure function over a list of "
        "plants, still not a store method. `all()` returning `list(self._plants.values())` "
        "in insertion order is a fine addition when you need it. One nit on your draft: "
        "`due <= today` treats a plant due today as due, which matches the display's "
        "purpose, but if you later add a 'due tomorrow' preview, compute it from `due_on` "
        "rather than adding a second flag to Plant. The display line itself can stay "
        "dumb:\n\n```python\nfor plant in due_today(store, date.today()):\n    when = "
        'plant.last_watered.isoformat() if plant.last_watered else "never"\n    '
        'print(f"{plant.plant_id:<4} {plant.name:<14} last {when}")\n```\n\nE-ink '
        "panels are slow to refresh, so printing once a morning from cron is the right "
        "cadence; do not be tempted to poll.",
    ),
    Turn(
        "user",
        "Two conventions before the real methods land. First, the error surface: "
        "PlantStore methods do not wrap or translate errors from below. If parse_date "
        "or parse_interval raises ValueError, that same ValueError comes straight out of "
        "the store method; no catching, no re-raising as PlantCareError, no custom "
        "message. PlantCareError stays in model.py for errors the package itself "
        "defines, not as a wrapper. I want tracebacks to point at the parser.",
    ),
    Turn(
        "assistant",
        "Understood: public PlantStore methods let lower-layer exceptions propagate raw. "
        "A ValueError from parse_date or parse_interval passes through unchanged, and I "
        "will not catch it or wrap it in PlantCareError. KeyError for an unknown plant "
        "id is the store's own contract and stays a plain KeyError too.",
    ),
    Turn(
        "user",
        "Second, naming: public PlantStore methods are verb_noun, like add_plant. New "
        "methods follow that pattern so the class reads as a list of actions.",
    ),
    Turn(
        "assistant",
        "Noted: verb_noun for new public PlantStore methods, matching add_plant. Private "
        "helpers can be named freely. Where the verb is ambiguous I will use the verb the "
        "request itself uses.",
    ),
    Turn(
        "user",
        "For later, not now: a JSON dump and load so the Pi survives a reboot. The "
        'shape I have in mind is:\n\n```json\n{\n  "plants": [\n    {"plant_id": '
        '"L1", "name": "fern", "interval_days": 3, "last_watered": "2026-09-10"},\n'
        '    {"plant_id": "L2", "name": "monstera", "interval_days": 10, '
        '"last_watered": null}\n  ]\n}\n```\n\nThe counter would need to be restored '
        "from the highest id so we do not mint L1 twice.",
    ),
    Turn(
        "assistant",
        "That shape is fine. Restoring the counter from `max(int(id[1:]))` is right, and "
        "it is worth a test that loads two plants and then adds a third to check it gets "
        "L3. Dates as ISO strings with null for never-watered round-trip cleanly through "
        "`date.isoformat()` and `parse_date`.",
    ),
    Turn(
        "user",
        "The tests that exist today are only these; I will paste the current files with "
        "each request so you see the real state:\n\n```python\nfrom plantcare.store "
        "import PlantStore\n\n\ndef test_add_plant_mints_sequential_ids():\n    s = "
        'PlantStore()\n    assert s.add_plant("fern", 3).plant_id == "L1"\n    assert '
        's.add_plant("monstera").interval_days == 7\n\n\ndef '
        'test_find_missing_is_none():\n    assert PlantStore().find("L1") is None\n```',
    ),
    Turn(
        "assistant",
        "Good. Send the first request and I will return the complete store module, "
        "keeping add_plant, find and count exactly as they are.",
    ),
]

_EVENT = (
    "Side note while I think of it: my partner wants to name the plants after "
    "composers instead of species, so the fixtures in the tests will get renamed at "
    "some point. Nothing for you to change in the code."
)


def build() -> Session:
    return Session(
        id="S09",
        project="plantcare",
        target_family="naming",
        support_family="error_surface",
        lifecycle="stable",
        files=_FILES,
        prefix=_PREFIX,
        states=("verb_noun", "noun_verb"),
        state_at=("verb_noun", "verb_noun"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10),
    )
