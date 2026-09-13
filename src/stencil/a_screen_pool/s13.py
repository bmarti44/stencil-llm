# ruff: noqa: E501
"""S13: pet vaccinations — naming (target, stable) x logging=silent (support)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""vaxbook package."""\n'

_MODEL = '''"""Pet and shot records."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Pet:
    pet_id: str
    name: str
    species: str


@dataclass(frozen=True)
class Shot:
    pet_id: str
    vaccine: str
    given_on: date
'''

_STORE = '''"""In-memory vaccination book."""

import logging
from datetime import date

from vaxbook.model import Pet, Shot

log = logging.getLogger("vaxbook")  # used by the CLI front end only


class VaxBook:
    def __init__(self) -> None:
        self._pets: dict[str, Pet] = {}
        self._shots: dict[str, list[Shot]] = {}

    def add_pet(self, name: str, species: str) -> Pet:
        pet = Pet(pet_id=f"A{len(self._pets) + 1}", name=name, species=species)
        self._pets[pet.pet_id] = pet
        self._shots[pet.pet_id] = []
        return pet

    def find_pet(self, pet_id: str) -> Pet | None:
        return self._pets.get(pet_id)

    def list_shots(self, pet_id: str) -> list[Shot]:
        return list(self._shots[pet_id])
'''

_FILES = {
    "vaxbook/__init__.py": _INIT,
    "vaxbook/model.py": _MODEL,
    "vaxbook/store.py": _STORE,
}

# ----------------------------------------------------------------- checkpoint 1: record a shot

_C1_HELPER = """import logging
from datetime import date

import pytest

from vaxbook.model import Shot
from vaxbook.store import VaxBook


def _record(book):
    fn = getattr(book, "record_shot", None) or getattr(book, "shot_record", None)
    assert fn is not None, "no record method found"
    return fn


def _book():
    b = VaxBook()
    b.add_pet("Biscuit", "dog")
    b.add_pet("Nori", "cat")
    return b


def _pkg_records(caplog):
    return [r for r in caplog.records if r.name.startswith("vaxbook")]
"""

_C1_FUNCTIONAL = {
    "test_record_functional.py": _C1_HELPER
    + """

def test_record_appends_shot_and_returns_true():
    b = _book()
    assert _record(b)("A1", "rabies", date(2026, 3, 2)) is True
    assert b.list_shots("A1") == [Shot("A1", "rabies", date(2026, 3, 2))]
    assert b.list_shots("A2") == []


def test_record_keeps_order_of_entry():
    b = _book()
    _record(b)("A1", "rabies", date(2026, 3, 2))
    _record(b)("A1", "lepto", date(2026, 1, 9))
    assert [s.vaccine for s in b.list_shots("A1")] == ["rabies", "lepto"]


def test_record_duplicate_is_skipped_and_returns_false():
    b = _book()
    _record(b)("A1", "rabies", date(2026, 3, 2))
    assert _record(b)("A1", "rabies", date(2026, 3, 2)) is False
    assert len(b.list_shots("A1")) == 1


def test_record_same_vaccine_other_date_is_not_duplicate():
    b = _book()
    _record(b)("A1", "rabies", date(2025, 3, 2))
    assert _record(b)("A1", "rabies", date(2026, 3, 2)) is True
    assert len(b.list_shots("A1")) == 2


def test_record_unknown_pet_raises_keyerror():
    b = _book()
    with pytest.raises(KeyError):
        _record(b)("A9", "rabies", date(2026, 3, 2))
"""
}

_C1_REGRESSION = {
    "test_record_regression.py": """import pytest

from vaxbook.store import VaxBook


def test_add_find_list_unchanged():
    b = VaxBook()
    p = b.add_pet("Biscuit", "dog")
    assert p.pet_id == "A1" and p.species == "dog"
    assert b.find_pet("A1") is p and b.find_pet("A2") is None
    assert b.list_shots("A1") == []
    with pytest.raises(KeyError):
        b.list_shots("A2")
"""
}

_C1_CONTRACT = {
    "verb_noun": {
        "test_record_naming.py": """from vaxbook.store import VaxBook


def test_record_is_verb_noun():
    assert hasattr(VaxBook, "record_shot")
    assert not hasattr(VaxBook, "shot_record")
"""
    },
    "noun_verb": {
        "test_record_naming.py": """from vaxbook.store import VaxBook


def test_record_is_noun_verb():
    assert hasattr(VaxBook, "shot_record")
    assert not hasattr(VaxBook, "record_shot")
"""
    },
}

_C1_SUPPORT = {
    "test_record_logging.py": _C1_HELPER
    + """

def test_duplicate_shot_logs_nothing(caplog):
    b = _book()
    _record(b)("A1", "rabies", date(2026, 3, 2))
    caplog.clear()
    with caplog.at_level(logging.DEBUG, logger="vaxbook"):
        assert _record(b)("A1", "rabies", date(2026, 3, 2)) is False
    assert _pkg_records(caplog) == []


def test_new_shot_logs_nothing(caplog):
    b = _book()
    caplog.clear()
    with caplog.at_level(logging.DEBUG, logger="vaxbook"):
        assert _record(b)("A1", "rabies", date(2026, 3, 2)) is True
    assert _pkg_records(caplog) == []
"""
}


def _gold1(name: str) -> str:
    return (
        _STORE.rstrip("\n")
        + f"""

    def {name}(self, pet_id: str, vaccine: str, given_on: date) -> bool:
        shots = self._shots[pet_id]
        shot = Shot(pet_id, vaccine, given_on)
        if shot in shots:
            return False
        shots.append(shot)
        return True
"""
    )


_REQ1 = Request(
    text=(
        "Add a public method on VaxBook that records a shot: it takes the pet id, the "
        "vaccine name and the date given (a date object), appends a Shot to that pet's "
        "history and returns True. If the pet already has a shot with the same vaccine "
        "on the same date, it is a duplicate entry: record nothing and return False. An "
        "unknown pet id raises KeyError."
    ),
    target="vaxbook/store.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"verb_noun": _gold1("record_shot"), "noun_verb": _gold1("shot_record")},
)

# ----------------------------------------------------------------- checkpoint 2: merge two pets

_C2_HELPER = """import logging
from datetime import date

import pytest

from vaxbook.model import Shot
from vaxbook.store import VaxBook


def _record(book):
    return getattr(book, "record_shot", None) or getattr(book, "shot_record", None)


def _merge(book):
    fn = getattr(book, "merge_pets", None) or getattr(book, "pets_merge", None)
    assert fn is not None, "no merge method found"
    return fn


def _book():
    b = VaxBook()
    b.add_pet("Biscuit", "dog")
    b.add_pet("Biscuit (dup)", "dog")
    _record(b)("A1", "rabies", date(2026, 3, 2))
    _record(b)("A2", "rabies", date(2026, 3, 2))
    _record(b)("A2", "lepto", date(2026, 1, 9))
    return b


def _pkg_records(caplog):
    return [r for r in caplog.records if r.name.startswith("vaxbook")]
"""

_C2_FUNCTIONAL = {
    "test_merge_functional.py": _C2_HELPER
    + """

def test_merge_moves_new_shots_and_returns_count():
    b = _book()
    assert _merge(b)("A2", "A1") == 1
    assert b.list_shots("A1") == [
        Shot("A1", "rabies", date(2026, 3, 2)),
        Shot("A1", "lepto", date(2026, 1, 9)),
    ]


def test_merge_removes_source_pet():
    b = _book()
    _merge(b)("A2", "A1")
    assert b.find_pet("A2") is None
    with pytest.raises(KeyError):
        b.list_shots("A2")
    assert b.find_pet("A1") is not None


def test_merge_with_nothing_new_returns_zero():
    b = VaxBook()
    b.add_pet("x", "cat")
    b.add_pet("y", "cat")
    _record(b)("A1", "fvrcp", date(2026, 2, 1))
    _record(b)("A2", "fvrcp", date(2026, 2, 1))
    assert _merge(b)("A2", "A1") == 0
    assert len(b.list_shots("A1")) == 1


def test_merge_unknown_pet_raises_keyerror_and_changes_nothing():
    b = _book()
    with pytest.raises(KeyError):
        _merge(b)("A9", "A1")
    with pytest.raises(KeyError):
        _merge(b)("A2", "A9")
    assert b.find_pet("A2") is not None and len(b.list_shots("A1")) == 1
"""
}

_C2_REGRESSION = {
    "test_merge_regression.py": """from datetime import date

from vaxbook.store import VaxBook


def _record(book):
    return getattr(book, "record_shot", None) or getattr(book, "shot_record", None)


def test_add_find_record_unchanged():
    b = VaxBook()
    p = b.add_pet("Biscuit", "dog")
    assert b.find_pet("A1") is p and b.list_shots("A1") == []
    assert _record(b)("A1", "rabies", date(2026, 3, 2)) is True
    assert _record(b)("A1", "rabies", date(2026, 3, 2)) is False
    assert len(b.list_shots("A1")) == 1
"""
}

_C2_CONTRACT = {
    "verb_noun": {
        "test_merge_naming.py": """from vaxbook.store import VaxBook


def test_merge_is_verb_noun():
    assert hasattr(VaxBook, "merge_pets")
    assert not hasattr(VaxBook, "pets_merge")
"""
    },
    "noun_verb": {
        "test_merge_naming.py": """from vaxbook.store import VaxBook


def test_merge_is_noun_verb():
    assert hasattr(VaxBook, "pets_merge")
    assert not hasattr(VaxBook, "merge_pets")
"""
    },
}

_C2_SUPPORT = {
    "test_merge_logging.py": _C2_HELPER
    + """

def test_merge_with_skipped_duplicates_logs_nothing(caplog):
    b = _book()
    caplog.clear()
    with caplog.at_level(logging.DEBUG, logger="vaxbook"):
        assert _merge(b)("A2", "A1") == 1
    assert _pkg_records(caplog) == []


def test_merge_without_duplicates_logs_nothing(caplog):
    b = VaxBook()
    b.add_pet("x", "cat")
    b.add_pet("y", "cat")
    _record(b)("A2", "fvrcp", date(2026, 2, 1))
    caplog.clear()
    with caplog.at_level(logging.DEBUG, logger="vaxbook"):
        assert _merge(b)("A2", "A1") == 1
    assert _pkg_records(caplog) == []
"""
}


def _gold2(name: str) -> str:
    # Built on the checkpoint-1 gold under the state then in force (verb_noun).
    return (
        _gold1("record_shot").rstrip("\n")
        + f"""

    def {name}(self, source_id: str, target_id: str) -> int:
        source_shots = self._shots[source_id]
        target_shots = self._shots[target_id]
        moved = 0
        for shot in source_shots:
            carried = Shot(target_id, shot.vaccine, shot.given_on)
            if carried in target_shots:
                continue
            target_shots.append(carried)
            moved += 1
        del self._shots[source_id]
        del self._pets[source_id]
        return moved
"""
    )


_REQ2 = Request(
    text=(
        "Add a public method on VaxBook that merges one pet record into another (the "
        "clinic keeps registering the same animal twice): it takes the source pet id and "
        "the target pet id, carries every shot of the source over to the target (re-keyed "
        "to the target id, appended in the source's order), skipping any that the target "
        "already has with the same vaccine and date, then removes the source pet and its "
        "history entirely, and returns how many shots were carried over. If either id is "
        "unknown, raise KeyError and change nothing."
    ),
    target="vaxbook/store.py",
    functional_tests=_C2_FUNCTIONAL,
    regression_tests=_C2_REGRESSION,
    contract_tests=_C2_CONTRACT,
    support_tests=_C2_SUPPORT,
    gold={"verb_noun": _gold2("merge_pets"), "noun_verb": _gold2("pets_merge")},
)

# ----------------------------------------------------------------- prefix (16 turns)

_PREFIX = [
    Turn(
        "user",
        "I volunteer at a small animal rescue and our vaccination records live in a "
        "paper binder plus a spreadsheet that disagrees with it. I want a tiny package, "
        "vaxbook, that a command-line tool drives: register an animal, record a shot, "
        "print what is due, and a report for the inspector who visits twice a year. No "
        "web app, no database; the CLI reads and writes one JSON file in the shared "
        "folder. About a hundred and twenty animals through the door per year, a few "
        "hundred shots. The inspector's report needs to look like the binder page she "
        "is used to:\n\n```\nA17  Biscuit   dog   rabies     2026-03-02\nA17  Biscuit   "
        "dog   lepto      2026-01-09\nA23  Nori      cat   fvrcp      2026-02-14\n```\n\n"
        "Could you draft the README scope so the other volunteers, two of whom can "
        "program a little, understand what the library does and what the CLI does, and "
        "do not try to add a database? The CLI I have in mind is nothing more than:\n\n"
        "```\n$ vaxbook add-pet Biscuit dog\nA17\n$ vaxbook shot A17 rabies 2026-03-02\n"
        "$ vaxbook due --days 365\nA23  Nori  fvrcp  last 2025-02-14\n$ vaxbook report "
        "> inspector-2026-09.txt\n```\n\nwith the JSON file path coming from an "
        "environment variable so the shared folder can move.",
    ),
    Turn(
        "assistant",
        "A scope section that separates the two layers:\n\n```\n## Scope\nvaxbook is an "
        "in-memory vaccination book for a single process. The library (vaxbook.store) "
        "keeps Pet and Shot records in a VaxBook and answers questions about them; it "
        "knows nothing about files, terminals or the inspector. The CLI (vaxbook.cli) "
        "loads the JSON file, calls the library, prints, and saves. Persistence is the "
        "CLI's job and the JSON file in the shared folder is the only copy; back it up.\n"
        "\n## Non-goals\n- a database or a server\n- reminders by email or text\n- "
        "veterinary advice (which vaccine when is the vet's call, we only record)\n```\n\n"
        "The last non-goal matters: the moment 'due' logic appears, someone will ask the "
        "program to decide schedules, and that is a liability the rescue should not "
        "take on in software.",
    ),
    Turn(
        "user",
        "Good point about schedules; 'due' will just be 'more than N days since the "
        "last shot of that vaccine' with N from a config the vet signs off. Ids: A1, "
        "A2, ... minted from the number of pets, because the binder already uses A-"
        "numbers and volunteers write them on the kennel cards. One volunteer wants the "
        "microchip number as the id. Most of our intake does not have a chip until we "
        "pay for it, so I said no. Dates: I am taking `date` objects in the library and "
        "parsing ISO strings in the CLI. Here is a test draft for the model so you can "
        "see what I am thinking:\n\n```python\nfrom datetime import date\n\nfrom "
        "vaxbook.model import Pet, Shot\n\n\ndef test_shot_equality_is_by_value():\n    a "
        '= Shot("A1", "rabies", date(2026, 3, 2))\n    b = Shot("A1", "rabies", '
        "date(2026, 3, 2))\n    assert a == b\n\n\ndef test_pet_is_frozen():\n    p = "
        'Pet("A1", "Biscuit", "dog")\n    try:\n        p.name = "x"\n    except '
        'Exception:\n        return\n    raise AssertionError("Pet should be frozen")\n```',
    ),
    Turn(
        "assistant",
        "Keep the A-numbers; an id that is already on the kennel card and in the binder "
        "beats a chip number that half the animals do not have yet. The chip can be an "
        "optional field on Pet later. Taking `date` objects in the library and parsing at "
        "the CLI boundary is right: the library stays testable with plain values and "
        "there is exactly one place that knows the input format. Your tests are good; "
        "the value-equality one is more important than it looks, because 'the same shot "
        "recorded twice' is going to be defined as equality of Shot, and a test that "
        "pins that definition protects the duplicate rule. Tighten the frozen test to "
        "`pytest.raises(dataclasses.FrozenInstanceError)` so a different exception does "
        "not pass by accident:\n\n```python\nimport dataclasses\n\nimport pytest\n\n\n"
        'def test_pet_is_frozen():\n    p = Pet("A1", "Biscuit", "dog")\n    with '
        'pytest.raises(dataclasses.FrozenInstanceError):\n        p.name = "x"\n```',
    ),
    Turn(
        "user",
        "Duplicates are the real problem. The same animal gets registered twice when "
        "two volunteers do intake on the same day, and the same shot gets typed in "
        "twice when the binder and the spreadsheet are both copied in. What should "
        "happen when a duplicate shot is recorded? Throw? Ignore? Here is the failure "
        "I got from the spreadsheet importer when I tried to be strict:\n\n```\n"
        'Traceback (most recent call last):\n  File "import_sheet.py", line 44, in '
        "<module>\n    book.add_shot(row.pet_id, row.vaccine, row.given_on)\n  File "
        '"/srv/rescue/vaxbook/store.py", line 29, in add_shot\n    raise ValueError(f"'
        'duplicate shot for {pet_id}: {vaccine} on {given_on}")\nValueError: duplicate '
        "shot for A17: rabies on 2026-03-02\n```\n\nwhich killed the import after 40 of "
        "300 rows. (That add_shot was a prototype; I deleted it.)",
    ),
    Turn(
        "assistant",
        "Treat a duplicate shot as a normal outcome, not an error. It is expected every "
        "time the binder and the spreadsheet are both imported, so the method should "
        "record nothing and tell the caller with a boolean: True if it was new, False if "
        "it was already there. The importer then counts the Falses and reports 'skipped "
        "260 duplicates' instead of dying on the first one. Exceptions stay for caller "
        "mistakes: an unknown pet id is a typo on a kennel card or a bug in the importer, "
        "and raising KeyError there stops the import at the row that needs a human. So: "
        "duplicates return False, lookups (`find_pet`) return None when missing, actions "
        "on an unknown id raise KeyError. The duplicate-animal problem is a separate "
        "operation (merging two pet records) and will need the same 'skip what the "
        "target already has' rule. For the importer, the loop then reads:\n\n```python\n"
        "skipped = sum(not record(book, row) for row in rows)\n```\n\nwhich is the "
        "whole duplicate policy in one line, with no exception handling around it.",
    ),
    Turn(
        "user",
        "Agreed on all three. Another thing: I left a module logger `log = "
        "logging.getLogger('vaxbook')` in store.py from the first draft. The CLI uses "
        "that logger name to write its own progress lines ('loaded 118 pets') so the "
        "inspector report script can turn them off. Should the library itself log "
        "anything, for example when it skips a duplicate? The importer would then get "
        "that for free instead of counting Falses.",
    ),
    Turn(
        "assistant",
        "Let the CLI own all logging. If the library logs on a skipped duplicate, every "
        "importer run prints hundreds of lines that nobody asked for, tests fill with "
        "caplog assertions, and the CLI's 'quiet' flag has to reach into the library. "
        "The boolean already carries the information; the importer can log its own "
        "summary once. Keeping the logger object in store.py is fine as long as the "
        "library does not call it: it gives the CLI a stable name to configure. If you "
        "want that intention visible, a short comment on the `log` line saying it is for "
        "the CLI front end is enough.",
    ),
    Turn(
        "user",
        "Two conventions before the real methods land. First, logging: the library is "
        "silent. Public VaxBook methods emit no log records at all, at any level, for "
        "any outcome, including the notable ones like a skipped duplicate or a merge "
        "that carried nothing over. The `log` object stays in store.py for the CLI's "
        "use only. If a test captures the `vaxbook` logger during a library call, it "
        "must see zero records.",
    ),
    Turn(
        "assistant",
        "Understood: public VaxBook methods never log, not on success, not on a skipped "
        "duplicate, not at debug level; outcomes are reported through return values and "
        "exceptions only. The `vaxbook` logger remains for the CLI to configure and use. "
        "KeyError on an unknown id raises without logging.",
    ),
    Turn(
        "user",
        "Second, naming: public VaxBook methods are verb_noun, like add_pet, find_pet "
        "and list_shots. New methods follow that pattern so the class reads as a list of "
        "actions.",
    ),
    Turn(
        "assistant",
        "Noted: verb_noun for new public VaxBook methods, matching add_pet, find_pet and "
        "list_shots. Private helpers can be named freely. Where the verb is ambiguous I "
        "will use the verb the request itself uses.",
    ),
    Turn(
        "user",
        "For later, not now: the JSON shape the CLI saves. I have it as a list of pets "
        'each with a list of shots:\n\n```json\n{\n  "pets": [\n    {"pet_id": "A17", '
        '"name": "Biscuit", "species": "dog",\n     "shots": [{"vaccine": "rabies", '
        '"given_on": "2026-03-02"}]}\n  ]\n}\n```\n\nThe CLI would rebuild the book by '
        "calling add_pet in order and then the shot-recording method per shot.",
    ),
    Turn(
        "assistant",
        "That shape is fine and rebuilding through the public methods is the right "
        "call: it means the duplicate rule applies on load too, so a hand-edited file "
        "with a repeated shot heals itself. Assert that add_pet returns the saved pet_id "
        "during the rebuild so a deleted pet cannot silently shift the A-numbers.",
    ),
    Turn(
        "user",
        "The tests that exist today are only these; I will paste the current files with "
        "each request so you see the real state:\n\n```python\nimport pytest\n\nfrom "
        "vaxbook.store import VaxBook\n\n\ndef test_add_pet_mints_sequential_ids():\n    "
        'b = VaxBook()\n    assert b.add_pet("Biscuit", "dog").pet_id == "A1"\n    assert '
        'b.add_pet("Nori", "cat").pet_id == "A2"\n\n\ndef test_find_pet_missing_is_none'
        '():\n    assert VaxBook().find_pet("A1") is None\n\n\ndef '
        "test_list_shots_unknown_pet_raises():\n    with pytest.raises(KeyError):\n"
        '        VaxBook().list_shots("A1")\n```',
    ),
    Turn(
        "assistant",
        "Good. Send the first request and I will return the complete store module, "
        "keeping add_pet, find_pet and list_shots exactly as they are.",
    ),
]

_EVENT = (
    "Side note: the receptionist at the partner clinic asked whether species should "
    "be a fixed list rather than free text. I said we will keep free text for now and "
    "clean it up in the CLI if it becomes a problem. Nothing for you to change."
)


def build() -> Session:
    return Session(
        id="S13",
        project="vaxbook",
        target_family="naming",
        support_family="logging",
        lifecycle="stable",
        files=_FILES,
        prefix=_PREFIX,
        states=("verb_noun", "noun_verb"),
        state_at=("verb_noun", "verb_noun"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10),
    )
