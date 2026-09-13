# ruff: noqa: E501
"""S14: wine cellar — naming (target, replacement) x logging (support, warn)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""cellarbook package."""\n'

_MODEL = '''"""Bottle records."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Bottle:
    bottle_id: str
    label: str
    vintage: int
    rack: str = "unsorted"
    status: str = "stored"
'''

_CELLAR_HEAD = '''"""In-memory cellar inventory."""

import logging
{extra_imports}
from cellarbook.model import Bottle

log = logging.getLogger(__name__)


class Cellar:
    def __init__(self) -> None:
        self._bottles: dict[str, Bottle] = {{}}
        self._serial = 0

    def bottle_add(self, label: str, vintage: int) -> Bottle:
        self._serial += 1
        bottle = Bottle(bottle_id=f"B{{self._serial:03d}}", label=label, vintage=vintage)
        self._bottles[bottle.bottle_id] = bottle
        return bottle

    def bottle_find(self, bottle_id: str) -> Bottle | None:
        return self._bottles.get(bottle_id)

    def bottle_count(self) -> int:
        return len(self._bottles)
'''

_CELLAR = _CELLAR_HEAD.format(extra_imports="")

_FILES = {
    "cellarbook/__init__.py": _INIT,
    "cellarbook/model.py": _MODEL,
    "cellarbook/cellar.py": _CELLAR,
}

# ----------------------------------------------------------------- checkpoint 1: move

_C1_HELPER = """import logging

from cellarbook.cellar import Cellar


def _move(cellar):
    fn = getattr(cellar, "bottle_move", None) or getattr(cellar, "move_bottle", None)
    assert fn is not None, "no move method found"
    return fn
"""

_C1_FUNCTIONAL = {
    "test_move_functional.py": _C1_HELPER
    + """

def test_move_sets_rack_and_stores():
    c = Cellar()
    b = c.bottle_add("Ridge Zinfandel", 2018)
    out = _move(c)(b.bottle_id, "A3")
    assert out.rack == "A3"
    assert c.bottle_find(b.bottle_id).rack == "A3"


def test_move_keeps_label_vintage_status():
    c = Cellar()
    b = c.bottle_add("Chablis 1er Cru", 2020)
    out = _move(c)(b.bottle_id, "C1")
    assert out.bottle_id == b.bottle_id
    assert out.label == "Chablis 1er Cru" and out.vintage == 2020
    assert out.status == "stored"


def test_move_to_same_rack_is_noop():
    c = Cellar()
    b = c.bottle_add("Barolo", 2016)
    _move(c)(b.bottle_id, "A1")
    out = _move(c)(b.bottle_id, "A1")
    assert out.rack == "A1" and c.bottle_find(b.bottle_id) == out


def test_move_unknown_raises_keyerror():
    c = Cellar()
    try:
        _move(c)("B999", "A1")
    except KeyError:
        return
    raise AssertionError("expected KeyError for an unknown bottle")
"""
}

_C1_REGRESSION = {
    "test_move_regression.py": """from cellarbook.cellar import Cellar


def test_add_find_count_unchanged():
    c = Cellar()
    b = c.bottle_add("Riesling", 2021)
    assert b.bottle_id == "B001" and b.rack == "unsorted" and b.status == "stored"
    assert c.bottle_find("B001") is b
    assert c.bottle_find("B002") is None
    assert c.bottle_count() == 1
"""
}

_C1_CONTRACT = {
    "noun_verb": {
        "test_move_naming.py": """from cellarbook.cellar import Cellar


def test_move_is_noun_verb():
    assert hasattr(Cellar, "bottle_move")
    assert not hasattr(Cellar, "move_bottle")
"""
    },
    "verb_noun": {
        "test_move_naming.py": """from cellarbook.cellar import Cellar


def test_move_is_verb_noun():
    assert hasattr(Cellar, "move_bottle")
    assert not hasattr(Cellar, "bottle_move")
"""
    },
}

_C1_SUPPORT = {
    "test_move_logging.py": _C1_HELPER
    + """

def test_same_rack_move_warns_exactly_once(caplog):
    c = Cellar()
    b = c.bottle_add("Barolo", 2016)
    _move(c)(b.bottle_id, "A1")
    with caplog.at_level(logging.DEBUG):
        _move(c)(b.bottle_id, "A1")
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1, [r.getMessage() for r in caplog.records]
"""
}


def _gold1(name: str) -> str:
    return (
        _CELLAR_HEAD.format(extra_imports="from dataclasses import replace\n").rstrip(
            "\n"
        )
        + f"""

    def {name}(self, bottle_id: str, rack: str) -> Bottle:
        bottle = self._bottles[bottle_id]
        if bottle.rack == rack:
            log.warning("bottle %s is already in rack %s", bottle_id, rack)
            return bottle
        moved = replace(bottle, rack=rack)
        self._bottles[bottle_id] = moved
        return moved
"""
    )


_REQ1 = Request(
    text=(
        "Add a public method on Cellar that moves a bottle to a rack: it takes the bottle "
        "id and the rack name, stores the updated bottle with that rack and returns it. "
        "An unknown id raises KeyError. Moving a bottle to the rack it is already in is "
        "the notable no-op case: nothing changes and the bottle is returned as is."
    ),
    target="cellarbook/cellar.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"noun_verb": _gold1("bottle_move"), "verb_noun": _gold1("move_bottle")},
)

# ----------------------------------------------------------------- checkpoint 2: drink

_C2_HELPER = """import logging

from cellarbook.cellar import Cellar


def _drink(cellar):
    fn = getattr(cellar, "drink_bottle", None) or getattr(cellar, "bottle_drink", None)
    assert fn is not None, "no drink method found"
    return fn
"""

_C2_FUNCTIONAL = {
    "test_drink_functional.py": _C2_HELPER
    + """

def test_drink_sets_status_and_stores():
    c = Cellar()
    b = c.bottle_add("Ridge Zinfandel", 2018)
    out = _drink(c)(b.bottle_id)
    assert out.status == "drunk"
    assert c.bottle_find(b.bottle_id).status == "drunk"


def test_drink_keeps_label_vintage_rack():
    c = Cellar()
    b = c.bottle_add("Chablis 1er Cru", 2020)
    out = _drink(c)(b.bottle_id)
    assert out.label == "Chablis 1er Cru" and out.vintage == 2020
    assert out.rack == "unsorted"


def test_drink_twice_is_noop():
    c = Cellar()
    b = c.bottle_add("Barolo", 2016)
    first = _drink(c)(b.bottle_id)
    out = _drink(c)(b.bottle_id)
    assert out == first and c.bottle_find(b.bottle_id) == first


def test_drink_unknown_raises_keyerror():
    c = Cellar()
    try:
        _drink(c)("B999")
    except KeyError:
        return
    raise AssertionError("expected KeyError for an unknown bottle")
"""
}

_C2_REGRESSION = {
    "test_drink_regression.py": """from cellarbook.cellar import Cellar


def _move(cellar):
    return getattr(cellar, "bottle_move", None) or getattr(cellar, "move_bottle", None)


def test_add_find_count_move_unchanged():
    c = Cellar()
    b = c.bottle_add("Riesling", 2021)
    assert b.bottle_id == "B001" and c.bottle_find("B001") is b
    assert c.bottle_count() == 1
    assert _move(c)(b.bottle_id, "D2").rack == "D2"
"""
}

_C2_CONTRACT = {
    "noun_verb": {
        "test_drink_naming.py": """from cellarbook.cellar import Cellar


def test_drink_is_noun_verb():
    assert hasattr(Cellar, "bottle_drink")
    assert not hasattr(Cellar, "drink_bottle")
"""
    },
    "verb_noun": {
        "test_drink_naming.py": """from cellarbook.cellar import Cellar


def test_drink_is_verb_noun():
    assert hasattr(Cellar, "drink_bottle")
    assert not hasattr(Cellar, "bottle_drink")
"""
    },
}

_C2_SUPPORT = {
    "test_drink_logging.py": _C2_HELPER
    + """

def test_drinking_drunk_bottle_warns_exactly_once(caplog):
    c = Cellar()
    b = c.bottle_add("Barolo", 2016)
    _drink(c)(b.bottle_id)
    with caplog.at_level(logging.DEBUG):
        _drink(c)(b.bottle_id)
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1, [r.getMessage() for r in caplog.records]
"""
}


def _gold2(name: str) -> str:
    # Built on the checkpoint-1 gold under the state then in force (noun_verb).
    return (
        _gold1("bottle_move").rstrip("\n")
        + f"""

    def {name}(self, bottle_id: str) -> Bottle:
        bottle = self._bottles[bottle_id]
        if bottle.status == "drunk":
            log.warning("bottle %s was already drunk", bottle_id)
            return bottle
        drunk = replace(bottle, status="drunk")
        self._bottles[bottle_id] = drunk
        return drunk
"""
    )


_REQ2 = Request(
    text=(
        "Add a public method on Cellar that marks a bottle as drunk: it takes the bottle "
        'id, stores the updated bottle with status "drunk" and returns it. An unknown id '
        "raises KeyError. Marking a bottle that is already drunk is the notable no-op "
        "case: nothing changes and the bottle is returned as is."
    ),
    target="cellarbook/cellar.py",
    functional_tests=_C2_FUNCTIONAL,
    regression_tests=_C2_REGRESSION,
    contract_tests=_C2_CONTRACT,
    support_tests=_C2_SUPPORT,
    gold={"noun_verb": _gold2("bottle_drink"), "verb_noun": _gold2("drink_bottle")},
)

# ----------------------------------------------------------------- prefix (16 turns)

_PREFIX = [
    Turn(
        "user",
        "I keep a spreadsheet of the bottles in the cellar under the stairs and it has "
        "finally become unmanageable: about two hundred bottles, six racks, and every "
        "time we drink one I forget to update the row. I want a tiny Python package, "
        "cellarbook, that a couple of scripts can drive: add a bottle when a case "
        "arrives, find it later, and eventually print what is ready to drink. No "
        "database, no web page, it runs on the laptop in the kitchen. Here is the "
        "README I started; tell me whether the scope section says enough:\n\n```\n# "
        "cellarbook\n\nA single-process inventory for a home wine cellar. Bottles get a "
        "serial id (B001, B002, ...) when they are added and keep it for life. The "
        "package is a library plus a couple of scripts; state lives in memory for the "
        "duration of a script run and is loaded/saved by the scripts, not by the "
        "library.\n```\n\nThe racks are lettered A to F, each with a dozen numbered "
        "slots, so a rack name looks like A3 or F11. Vintage is a plain year.",
    ),
    Turn(
        "assistant",
        "The scope section is honest and short, which is the right size. Two things I "
        "would add: say explicitly that ids are never reused (so a script that drank B042 "
        "last year can still refer to it), and name the load/save format the scripts will "
        "use even if it is just JSON, because that is the first question anyone reads a "
        "README to answer. Something like:\n\n```\n## Persistence\nThe library does not "
        "read or write files. `scripts/load.py` and `scripts/save.py` round-trip a JSON "
        "list of bottles; ids are stable and never reused.\n\n## Non-goals\n- multiple "
        "cellars\n- prices and valuations\n- a web or phone UI\n```\n\nThat also keeps the "
        "core `Cellar` class free of I/O, which makes it trivial to test: a test builds a "
        "`Cellar()`, adds a few bottles and asserts on what comes back. The JSON shape "
        'can be the dataclass fields verbatim:\n\n```json\n[{"bottle_id": "B001", '
        '"label": "Riesling", "vintage": 2021, "rack": "unsorted", "status": '
        '"stored"}]\n```',
    ),
    Turn(
        "user",
        "Serial ids it is. For the record type I have a frozen dataclass with bottle_id, "
        'label, vintage, rack and status. Status starts as "stored"; the only other '
        'value I foresee is "drunk", and maybe "gifted" some day. Rack starts as '
        '"unsorted" because bottles arrive in a case and sit on the floor until I find '
        "them a slot. Is a frozen dataclass the right call, or will I regret it the first "
        "time I want to update a rack? My worry is that I end up with `replace()` calls "
        "everywhere and the code reads like a functional-programming exercise. The "
        "alternative is a mutable dataclass and methods on Cellar that poke at fields. "
        "For what it is worth, the scripts only ever read bottles; every change goes "
        "through Cellar, so mutability outside the class would never be needed. The "
        "current model file is just:\n\n```python\n@dataclass(frozen=True)\nclass "
        "Bottle:\n    bottle_id: str\n    label: str\n    vintage: int\n    rack: str = "
        '"unsorted"\n    status: str = "stored"\n```',
    ),
    Turn(
        "assistant",
        "Keep it frozen. The pattern that keeps it readable is: every state change is a "
        "Cellar method that looks the bottle up, builds the new record with "
        "`dataclasses.replace`, stores it under the same id and returns it. One "
        "`replace()` per method is not a burden, and frozen records mean a script that "
        "holds an old Bottle cannot silently mutate the inventory. It also makes equality "
        "and hashing free, so tests can write `assert cellar.bottle_find(b.bottle_id) == "
        "expected` without comparing field by field. Here is the skeleton I would use for "
        "any change method:\n\n```python\ndef _update(self, bottle_id: str, **changes) -> "
        "Bottle:\n    bottle = self._bottles[bottle_id]\n    updated = replace(bottle, "
        "**changes)\n    self._bottles[bottle_id] = updated\n    return updated\n```\n\n"
        "although with only two or three change methods I would inline the lookup.",
    ),
    Turn(
        "user",
        "Here is the test file I have for the current class, so you can see where the "
        "code stands. Everything passes today:\n\n```python\nfrom cellarbook.cellar import "
        "Cellar\n\n\ndef test_add_assigns_padded_serial_ids():\n    c = Cellar()\n    "
        'assert c.bottle_add("Riesling", 2021).bottle_id == "B001"\n    assert '
        'c.bottle_add("Chablis", 2020).bottle_id == "B002"\n\n\ndef '
        'test_new_bottle_is_unsorted_and_stored():\n    b = Cellar().bottle_add("Barolo", '
        '2016)\n    assert b.rack == "unsorted"\n    assert b.status == "stored"\n\n\ndef '
        'test_find_missing_returns_none():\n    assert Cellar().bottle_find("B404") is '
        "None\n```\n\n"
        "Should `bottle_find` raise instead of returning None? The load script calls it "
        "in a loop and a None check feels sloppy there.",
    ),
    Turn(
        "assistant",
        "Leave `bottle_find` returning None: its name promises a lookup that might miss, "
        "and the loop in the load script is exactly the caller that wants to branch rather "
        "than catch. The methods that *act* on a bottle (moving it, drinking it) are the "
        "ones that should raise KeyError on an unknown id, because acting on a bottle "
        "that does not exist is a bug in the caller, not a normal outcome. That gives you "
        "a rule people can remember: lookups return None, actions raise KeyError. If the "
        "load script wants a hard failure it can wrap the lookup:\n\n```python\ndef "
        "require(cellar: Cellar, bottle_id: str) -> Bottle:\n    bottle = "
        "cellar.bottle_find(bottle_id)\n    if bottle is None:\n        raise "
        "KeyError(bottle_id)\n    return bottle\n```\n\nYour tests are fine as they are; "
        "the padded serial test in particular is worth keeping because the padding is "
        "what makes `sorted()` on ids do the right thing.",
    ),
    Turn(
        "user",
        "Agreed on lookups vs actions. One thing bit me yesterday while I was hacking on "
        "the save script: I had a typo in a rack name and the script happily 'moved' a "
        "bottle to rack 'A3 ' with a trailing space. No error, no message, and I only "
        "noticed when the rack listing had two A3 groups. I do not want the library to "
        "validate rack names (the racks will change when we rebuild the shelving), but I "
        "do want to hear about the odd cases. Here is what the listing looked like, for "
        "colour:\n\n```\nA3\n  B017 Ridge Zinfandel 2018\n  B031 Chablis 1er Cru 2020\n"
        "A3 \n  B044 Barolo 2016\nunsorted\n  B052 Riesling 2021\n```\n\nSo the question "
        "is really: how should a library like this talk to me about things that are not "
        "errors but are probably not what I meant?",
    ),
    Turn(
        "assistant",
        "The standard answer for a library is the `logging` module: create one module "
        "logger with `log = logging.getLogger(__name__)` and emit `log.warning(...)` for "
        "conditions that are legal but suspicious. The library never configures logging "
        "itself (no handlers, no `basicConfig`), so it stays quiet by default and the "
        "kitchen-laptop scripts decide where warnings go, for example:\n\n```python\n"
        'import logging\n\nlogging.basicConfig(level=logging.WARNING, format="%(levelname)'
        's %(name)s: %(message)s")\n```\n\nThat prints `WARNING cellarbook.cellar: bottle '
        "B044 is already in rack A3` and nothing else. The trailing-space rack is a good "
        "example of something the caller should hear about once, in a log line, rather "
        "than something the library should refuse. Tests can assert on it with pytest's "
        "`caplog` fixture, which records every emitted record:\n\n```python\ndef "
        'test_same_rack_warns(caplog):\n    c = Cellar()\n    b = c.bottle_add("Barolo", '
        "2016)\n    with caplog.at_level(logging.DEBUG):\n        ...  # the no-op call\n"
        '    assert [r.levelname for r in caplog.records] == ["WARNING"]\n```',
    ),
    Turn(
        "user",
        "Let's fix that as a convention then: when a Cellar method hits a notable but "
        "harmless condition (the request being a no-op, like moving a bottle to where it "
        "already is), it emits exactly one logging.warning through the module logger. "
        "Not two, not a warning plus an info, and nothing at debug level either. The "
        "normal path stays silent.",
    ),
    Turn(
        "assistant",
        "Noted: for the notable no-op conditions a Cellar method emits exactly one "
        "`log.warning` via `logging.getLogger(__name__)`, and no other record of any level; "
        "the normal path logs nothing. I will keep the message short and include the "
        "bottle id so the line is useful on its own.",
    ),
    Turn(
        "user",
        "Naming next. The existing public methods are bottle_add, bottle_find and "
        "bottle_count, noun first then verb, so everything about bottles sorts together "
        "in the editor's completion list. New public Cellar methods follow that same "
        "noun_verb pattern.",
    ),
    Turn(
        "assistant",
        "Understood: noun_verb for public Cellar methods, matching bottle_add and "
        "bottle_find. New public methods get the same shape, so a method that moves a "
        "bottle would be bottle_move, and private helpers can be named freely because "
        "they are not part of the API.",
    ),
    Turn(
        "user",
        "Something for later: I would like a 'ready to drink' report that takes a "
        "drinking window per label, but I do not have the windows typed in yet. Just "
        "noting it. The report would be roughly:\n\n```python\ndef ready(cellar: Cellar, "
        "windows: dict[str, tuple[int, int]], year: int) -> list[Bottle]:\n    out = []\n"
        "    for bottle in cellar.bottle_all():\n        lo, hi = windows.get(bottle.label, "
        "(0, 9999))\n        if lo <= year - bottle.vintage <= hi:\n            "
        "out.append(bottle)\n    return out\n```\n\nwhere bottle_all does not exist yet.",
    ),
    Turn(
        "assistant",
        "That will drop in cleanly when the windows exist. `bottle_all` would return "
        "`list(self._bottles.values())`, which is insertion order and therefore serial "
        "order, so the report is already sorted by id without extra work. I would leave "
        "the window lookup outside the library as you have it.",
    ),
    Turn(
        "user",
        "Right, let's get the first real change in. A case arrived on Saturday and I "
        "want to be able to slot bottles into racks properly before the next one. I will "
        "paste the current files with each request so you see the true state.",
    ),
    Turn(
        "assistant",
        "Ready. Send the request with the files and I will return the complete cellar "
        "module.",
    ),
]

_EVENT = (
    "Change of convention, effective now: new public Cellar methods are named verb_noun "
    "(move_bottle style), not noun_verb. Existing method names stay exactly as they are; "
    "only new methods follow the new pattern."
)


def build() -> Session:
    return Session(
        id="S14",
        project="cellarbook",
        target_family="naming",
        support_family="logging",
        lifecycle="replacement",
        files=_FILES,
        prefix=_PREFIX,
        states=("noun_verb", "verb_noun"),
        state_at=("noun_verb", "verb_noun"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10),
    )
