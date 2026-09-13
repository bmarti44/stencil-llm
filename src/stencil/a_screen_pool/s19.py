# ruff: noqa: E501
"""S19: board-game lending — validation (target, scope) x return_shape (support, dataclass)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""meepleshelf package."""\n'

_MODEL = '''"""Catalogue and loan records."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Game:
    game_id: str
    title: str
    min_players: int
    rating: int | None = None


@dataclass(frozen=True)
class Loan:
    game_id: str
    borrower: str
    days: int
'''

_SHELF_HEAD = '''"""Game shelf: storage layer (Shelf) and public functions."""
{extra_imports}
from meepleshelf.model import Game, Loan


class Shelf:
    """Storage layer: keeps records and does not judge their values."""

    def __init__(self) -> None:
        self._games: dict[str, Game] = {{}}
        self._loans: dict[str, Loan] = {{}}
        self._next = 1

    def put_game(self, title: str, min_players: int) -> Game:
        game = Game(game_id=f"G{{self._next}}", title=title, min_players=min_players)
        self._next += 1
        self._games[game.game_id] = game
        return game

    def get_game(self, game_id: str) -> Game | None:
        return self._games.get(game_id)

    def get_loan(self, game_id: str) -> Loan | None:
        return self._loans.get(game_id)
{storage_methods}

def add_game(shelf: Shelf, title: str, min_players: int) -> Game:
    """Public entry point: checks the input, then stores."""
    if not title.strip():
        raise ValueError("game title must not be blank")
    if min_players < 1:
        raise ValueError("min_players must be at least 1")
    return shelf.put_game(title.strip(), min_players)
{public_functions}'''

_SHELF = _SHELF_HEAD.format(extra_imports="", storage_methods="", public_functions="")

_FILES = {
    "meepleshelf/__init__.py": _INIT,
    "meepleshelf/model.py": _MODEL,
    "meepleshelf/shelf.py": _SHELF,
}

# ----------------------------------------------------------------- checkpoint 1: rate_game

_C1_FUNCTIONAL = {
    "test_rate_functional.py": """import pytest

from meepleshelf.shelf import Shelf, add_game, rate_game

# The shelf always holds a SECOND game, "G1", already rated 5 -- so its
# rating is NOT the dataclass default.  Any operation that drops unrelated
# records, or resets an unrelated defaulted attribute, is then visible.
OTHER = "G1"


def _shelf():
    s = Shelf()
    other = add_game(s, "Azul", 4)
    rate_game(s, other.game_id, 5)
    g = add_game(s, "Carcassonne", 2)
    return s, g


def _assert_other_intact(s):
    kept = s.get_game(OTHER)
    assert kept is not None, "an unrelated game was dropped from the shelf"
    assert kept.game_id == OTHER and kept.title == "Azul"
    assert kept.min_players == 4 and kept.rating == 5


def test_rate_game_stores_and_returns_rated_game():
    s, g = _shelf()
    out = rate_game(s, g.game_id, 4)
    assert out.rating == 4 and out.game_id == g.game_id
    assert out.title == "Carcassonne" and out.min_players == 2
    assert s.get_game(g.game_id) == out
    _assert_other_intact(s)


def test_rate_game_overwrites_previous_rating():
    s, g = _shelf()
    rate_game(s, g.game_id, 2)
    assert rate_game(s, g.game_id, 5).rating == 5
    assert s.get_game(g.game_id).rating == 5
    _assert_other_intact(s)


@pytest.mark.parametrize("bad", [0, 6, -1, 42])
def test_rate_game_rejects_out_of_range(bad):
    s, g = _shelf()
    with pytest.raises(ValueError):
        rate_game(s, g.game_id, bad)
    assert s.get_game(g.game_id).rating is None
    _assert_other_intact(s)


@pytest.mark.parametrize("edge", [1, 5])
def test_rate_game_accepts_bounds(edge):
    s, g = _shelf()
    assert rate_game(s, g.game_id, edge).rating == edge
    assert s.get_game(g.game_id).rating == edge
    _assert_other_intact(s)


def test_rate_game_unknown_raises_keyerror():
    s, g = _shelf()
    with pytest.raises(KeyError):
        rate_game(s, "G99", 3)
    _assert_other_intact(s)
    assert s.get_game(g.game_id) is not None
    assert s.get_game(g.game_id).rating is None
"""
}

_C1_REGRESSION = {
    "test_rate_regression.py": """import pytest

from meepleshelf.shelf import Shelf, add_game


def test_add_game_validates_and_stores():
    s = Shelf()
    g = add_game(s, "  Azul ", 2)
    assert g.game_id == "G1" and g.title == "Azul" and g.rating is None
    assert s.get_game("G1") is g and s.get_game("G2") is None
    with pytest.raises(ValueError):
        add_game(s, "   ", 2)
    with pytest.raises(ValueError):
        add_game(s, "Solo", 0)
    assert s.get_game("G2") is None
    h = add_game(s, "Hive", 2)
    assert h.game_id == "G2" and h.title == "Hive" and h.rating is None
    assert s.get_game("G2") is h
    assert s.get_game("G1") is g and s.get_game("G1").rating is None


def test_put_game_stores_without_checking():
    s = Shelf()
    first = s.put_game("Azul", 4)
    g = s.put_game("", 0)
    assert g.title == "" and g.min_players == 0 and s.get_game(g.game_id) is g
    kept = s.get_game(first.game_id)
    assert kept is not None, "an unrelated game was dropped from the shelf"
    assert kept is first and kept.title == "Azul" and kept.min_players == 4


def test_get_loan_missing_returns_none():
    assert Shelf().get_loan("G1") is None
    s = Shelf()
    add_game(s, "Azul", 4)
    add_game(s, "Hive", 2)
    assert s.get_loan("G1") is None and s.get_loan("G2") is None
"""
}

_C1_CONTRACT = {
    "api": {
        "test_rate_validation.py": """import pytest

from meepleshelf.shelf import Shelf, add_game, rate_game


def test_public_function_rejects_and_storage_does_not():
    s = Shelf()
    g = add_game(s, "Carcassonne", 2)
    with pytest.raises(ValueError):
        rate_game(s, g.game_id, 9)
    # the storage layer stores whatever it is given
    out = s.put_rating(g.game_id, 9)
    assert out.rating == 9
    assert s.get_game(g.game_id).rating == 9
"""
    },
    "storage": {
        "test_rate_validation.py": """import pytest

from meepleshelf.shelf import Shelf, add_game, rate_game


def test_storage_rejects_directly():
    s = Shelf()
    g = add_game(s, "Carcassonne", 2)
    with pytest.raises(ValueError):
        s.put_rating(g.game_id, 9)
    assert s.get_game(g.game_id).rating is None


def test_public_function_passes_invalid_value_through(monkeypatch):
    s = Shelf()
    g = add_game(s, "Carcassonne", 2)
    seen = []

    def spy(self, game_id, stars):
        seen.append((game_id, stars))
        return None

    monkeypatch.setattr(Shelf, "put_rating", spy)
    rate_game(s, g.game_id, 9)
    assert seen == [(g.game_id, 9)]
"""
    },
}

_C1_SUPPORT = {
    "test_rate_shape.py": """from dataclasses import is_dataclass

from meepleshelf.model import Game
from meepleshelf.shelf import Shelf, add_game, rate_game


def test_rate_game_returns_game_dataclass_not_dict():
    s = Shelf()
    g = add_game(s, "Carcassonne", 2)
    out = rate_game(s, g.game_id, 4)
    assert isinstance(out, Game) and is_dataclass(out)
    assert not isinstance(out, dict)
"""
}

_STORAGE1_API = """
    def put_rating(self, game_id: str, stars: int) -> Game:
        game = self._games[game_id]
        rated = replace(game, rating=stars)
        self._games[game_id] = rated
        return rated
"""

_STORAGE1_STORAGE = """
    def put_rating(self, game_id: str, stars: int) -> Game:
        if not 1 <= stars <= 5:
            raise ValueError(f"rating must be 1 to 5 stars, got {stars}")
        game = self._games[game_id]
        rated = replace(game, rating=stars)
        self._games[game_id] = rated
        return rated
"""

_PUBLIC1_API = '''

def rate_game(shelf: Shelf, game_id: str, stars: int) -> Game:
    """Public entry point: checks the rating, then stores."""
    if not 1 <= stars <= 5:
        raise ValueError(f"rating must be 1 to 5 stars, got {stars}")
    return shelf.put_rating(game_id, stars)
'''

_PUBLIC1_STORAGE = """

def rate_game(shelf: Shelf, game_id: str, stars: int) -> Game:
    return shelf.put_rating(game_id, stars)
"""

_IMPORTS = "\nfrom dataclasses import replace\n"

_GOLD1 = {
    "api": _SHELF_HEAD.format(
        extra_imports=_IMPORTS,
        storage_methods=_STORAGE1_API,
        public_functions=_PUBLIC1_API,
    ),
    "storage": _SHELF_HEAD.format(
        extra_imports=_IMPORTS,
        storage_methods=_STORAGE1_STORAGE,
        public_functions=_PUBLIC1_STORAGE,
    ),
}

_REQ1 = Request(
    text=(
        "Add star ratings to the catalogue. On Shelf add `put_rating(game_id, stars)` "
        "that stores the game with its rating set to stars and returns the updated "
        "Game, raising KeyError for an unknown game. Add a public function "
        "`rate_game(shelf, game_id, stars)` that rates a game. A rating outside 1 to 5 "
        "inclusive is invalid input and must raise ValueError without changing the game."
    ),
    target="meepleshelf/shelf.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold=_GOLD1,
)

# ----------------------------------------------------------------- checkpoint 2: lend_game

_C2_FUNCTIONAL = {
    "test_lend_functional.py": """import pytest

from meepleshelf.shelf import Shelf, add_game, lend_game, rate_game

# The shelf always holds a SECOND game, "G1", already rated 5 and already
# out on loan -- so neither its rating (a defaulted attribute) nor its loan
# is the default.  Any operation that drops unrelated records, or resets an
# unrelated defaulted attribute, is then visible.
OTHER = "G1"


def _shelf():
    s = Shelf()
    other = add_game(s, "Azul", 4)
    rate_game(s, other.game_id, 5)
    lend_game(s, other.game_id, "Pia", 21)
    g = add_game(s, "Carcassonne", 2)
    return s, g


def _assert_other_intact(s):
    kept = s.get_game(OTHER)
    assert kept is not None, "an unrelated game was dropped from the shelf"
    assert kept.game_id == OTHER and kept.title == "Azul"
    assert kept.min_players == 4 and kept.rating == 5
    loan = s.get_loan(OTHER)
    assert loan is not None, "an unrelated loan was dropped from the shelf"
    assert loan.game_id == OTHER and loan.borrower == "Pia" and loan.days == 21


def test_lend_game_stores_and_returns_loan():
    s, g = _shelf()
    out = lend_game(s, g.game_id, "Noor", 14)
    assert out.game_id == g.game_id and out.borrower == "Noor" and out.days == 14
    assert s.get_loan(g.game_id) == out
    _assert_other_intact(s)


def test_lend_game_replaces_existing_loan():
    s, g = _shelf()
    lend_game(s, g.game_id, "Noor", 7)
    out = lend_game(s, g.game_id, "Sam", 21)
    assert s.get_loan(g.game_id) == out and out.borrower == "Sam"
    _assert_other_intact(s)


@pytest.mark.parametrize("bad", [0, -3, 29, 365])
def test_lend_game_rejects_out_of_range_days(bad):
    s, g = _shelf()
    with pytest.raises(ValueError):
        lend_game(s, g.game_id, "Noor", bad)
    assert s.get_loan(g.game_id) is None
    _assert_other_intact(s)


@pytest.mark.parametrize("edge", [1, 28])
def test_lend_game_accepts_bounds(edge):
    s, g = _shelf()
    assert lend_game(s, g.game_id, "Noor", edge).days == edge
    assert s.get_loan(g.game_id).days == edge
    _assert_other_intact(s)


def test_lend_game_unknown_raises_keyerror():
    s, g = _shelf()
    with pytest.raises(KeyError):
        lend_game(s, "G99", "Noor", 7)
    _assert_other_intact(s)
    assert s.get_game(g.game_id) is not None and s.get_loan(g.game_id) is None
"""
}

_C2_REGRESSION = {
    "test_lend_regression.py": """import pytest

from meepleshelf.shelf import Shelf, add_game, rate_game


def test_add_and_rate_unchanged():
    s = Shelf()
    g = add_game(s, "Azul", 2)
    other = add_game(s, "Hive", 2)
    assert rate_game(s, other.game_id, 4).rating == 4
    with pytest.raises(ValueError):
        add_game(s, "Solo", 0)
    assert rate_game(s, g.game_id, 3).rating == 3
    with pytest.raises(ValueError):
        rate_game(s, g.game_id, 7)
    assert s.get_game(g.game_id).rating == 3
    kept = s.get_game(other.game_id)
    assert kept is not None, "rating one game dropped another from the shelf"
    assert kept.title == "Hive" and kept.min_players == 2 and kept.rating == 4
    assert s.put_rating(g.game_id, 7).rating == 7
    kept = s.get_game(other.game_id)
    assert kept is not None and kept.rating == 4 and kept.title == "Hive"
    assert s.get_game(g.game_id).rating == 7
    assert s.put_game("", 0).title == ""
    assert s.get_game(g.game_id) is not None
    assert s.get_game(other.game_id) is not None
    assert s.get_game(other.game_id).rating == 4
"""
}

_C2_CONTRACT = {
    "api": {
        "test_lend_validation.py": """import pytest

from meepleshelf.shelf import Shelf, add_game, lend_game


def test_public_function_rejects_and_storage_does_not():
    s = Shelf()
    g = add_game(s, "Carcassonne", 2)
    with pytest.raises(ValueError):
        lend_game(s, g.game_id, "Noor", 90)
    # the storage layer stores whatever it is given
    out = s.put_loan(g.game_id, "Noor", 90)
    assert out.days == 90
    assert s.get_loan(g.game_id) == out
"""
    },
    "storage": {
        "test_lend_validation.py": """import pytest

from meepleshelf.shelf import Shelf, add_game, lend_game


def test_storage_rejects_directly():
    s = Shelf()
    g = add_game(s, "Carcassonne", 2)
    with pytest.raises(ValueError):
        s.put_loan(g.game_id, "Noor", 90)
    assert s.get_loan(g.game_id) is None


def test_public_function_passes_invalid_value_through(monkeypatch):
    s = Shelf()
    g = add_game(s, "Carcassonne", 2)
    seen = []

    def spy(self, game_id, borrower, days):
        seen.append((game_id, borrower, days))
        return None

    monkeypatch.setattr(Shelf, "put_loan", spy)
    lend_game(s, g.game_id, "Noor", 90)
    assert seen == [(g.game_id, "Noor", 90)]
"""
    },
}

_C2_SUPPORT = {
    "test_lend_shape.py": """from dataclasses import is_dataclass

from meepleshelf.model import Loan
from meepleshelf.shelf import Shelf, add_game, lend_game


def test_lend_game_returns_loan_dataclass_not_dict():
    s = Shelf()
    g = add_game(s, "Carcassonne", 2)
    out = lend_game(s, g.game_id, "Noor", 14)
    assert isinstance(out, Loan) and is_dataclass(out)
    assert not isinstance(out, dict)
"""
}

_STORAGE2_API = """
    def put_loan(self, game_id: str, borrower: str, days: int) -> Loan:
        if game_id not in self._games:
            raise KeyError(game_id)
        loan = Loan(game_id=game_id, borrower=borrower, days=days)
        self._loans[game_id] = loan
        return loan
"""

_STORAGE2_STORAGE = """
    def put_loan(self, game_id: str, borrower: str, days: int) -> Loan:
        if not 1 <= days <= 28:
            raise ValueError(f"loan length must be 1 to 28 days, got {days}")
        if game_id not in self._games:
            raise KeyError(game_id)
        loan = Loan(game_id=game_id, borrower=borrower, days=days)
        self._loans[game_id] = loan
        return loan
"""

_PUBLIC2_API = '''

def lend_game(shelf: Shelf, game_id: str, borrower: str, days: int) -> Loan:
    """Public entry point: checks the loan length, then stores."""
    if not 1 <= days <= 28:
        raise ValueError(f"loan length must be 1 to 28 days, got {days}")
    return shelf.put_loan(game_id, borrower, days)
'''

_PUBLIC2_STORAGE = """

def lend_game(shelf: Shelf, game_id: str, borrower: str, days: int) -> Loan:
    return shelf.put_loan(game_id, borrower, days)
"""


def _gold2(state: str) -> str:
    # Built on the checkpoint-1 gold under the state then in force (api).
    storage = _STORAGE2_API if state == "api" else _STORAGE2_STORAGE
    public = _PUBLIC2_API if state == "api" else _PUBLIC2_STORAGE
    return _SHELF_HEAD.format(
        extra_imports=_IMPORTS,
        storage_methods=_STORAGE1_API + storage,
        public_functions=_PUBLIC1_API + public,
    )


_REQ2 = Request(
    text=(
        "Add lending. On Shelf add `put_loan(game_id, borrower, days)` that stores a "
        "Loan for that game (replacing any current loan for it) and returns it, raising "
        "KeyError for an unknown game. Add a public function `lend_game(shelf, game_id, "
        "borrower, days)` that lends a game out. A loan length outside 1 to 28 days "
        "inclusive is invalid input and must raise ValueError without storing anything."
    ),
    target="meepleshelf/shelf.py",
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
        "Our neighbourhood board-game group has about eighty games in a cupboard at the "
        "community hall and lends them out between meetups, tracked in a notebook that "
        "has now gone missing twice. I want a small package, meepleshelf, that a couple "
        "of scripts can drive from the laptop that lives in the cupboard: add games to "
        "the catalogue, rate them after a session, and lend them out to members with a "
        "return date. In-memory only, the scripts load and save a JSON file, no web "
        "anything. Here is the README draft:\n\n```\n# meepleshelf\n\nCatalogue and "
        "lending for a game group's shared shelf. Games get ids G1, G2, ... when added "
        "and keep them. A game can be on loan to at most one member at a time. The "
        "package does no I/O; `shelf.py` (the script, badly named, will rename) loads "
        "and saves `shelf.json`.\n```\n\nI already have the catalogue half started. The "
        "lending half is the part that actually matters to the group, since that is "
        "where the notebook failed us, but I want the catalogue solid first. The "
        "cupboard laptop is an old Chromebook running Linux, so plain Python and a JSON "
        "file are about the limit of what I want to maintain there.",
    ),
    Turn(
        "assistant",
        "Sensible order: catalogue first gives lending something to point at. Two "
        "README additions I would make now: rename the script to `cupboard.py` or "
        "similar before anyone imports the wrong `shelf`, and list the non-goals so "
        "the group's enthusiasts do not file requests for a BoardGameGeek sync in week "
        "one:\n\n```\n## Non-goals\n- reservations and waiting lists\n- late fees\n- "
        "syncing with any online database\n\n## Layout\n`meepleshelf/model.py` holds "
        "the frozen records (Game, Loan). `meepleshelf/shelf.py` holds the `Shelf` "
        "storage class and the public functions the scripts call.\n```\n\nThat layout "
        "line matters more than it looks: the class is the storage layer and the "
        "module-level functions are the entry points, and saying so in the README and "
        "in both docstrings stops the two from blurring together as the file grows. A "
        "usage block finishes it:\n\n```python\nfrom meepleshelf.shelf import Shelf, "
        'add_game\n\nshelf = Shelf()\ngame = add_game(shelf, "Carcassonne", 2)\n'
        "print(game.game_id)  # G1\n```",
    ),
    Turn(
        "user",
        "Renamed to cupboard.py. Here is the model, two frozen dataclasses:\n\n```python\n"
        "@dataclass(frozen=True)\nclass Game:\n    game_id: str\n    title: str\n    "
        "min_players: int\n    rating: int | None = None\n\n\n@dataclass(frozen=True)\n"
        "class Loan:\n    game_id: str\n    borrower: str\n    days: int\n```\n\nRating "
        "is the group's own one-to-five stars after a session, None until someone "
        "rates it. A Loan is keyed by game in the Shelf because a game can only be out "
        "once; `days` is the loan length and the script works out the due date from "
        "the save timestamp. Is it odd that Loan does not carry a start date? I keep "
        "going back and forth: a date in the record is self-describing, but then the "
        "package needs to know about today, and I want it to stay pure so the tests "
        "never depend on the clock. The group has agreed loans run one to four weeks, "
        "so `days` will be small integers, and a return date printed on the meetup "
        "email is enough for people to remember.",
    ),
    Turn(
        "assistant",
        "Keeping the clock out of the package is the right instinct, and it is exactly "
        "why `days` rather than a due date belongs on Loan: the record says what was "
        "agreed, the script that knows the time turns it into a date when it saves or "
        "renders. Tests then construct loans with no freezegun or fake clock. If you "
        "later want the start date persisted, the script can write it next to the "
        "record in the JSON without the package ever reading it. For the storage "
        "class, keying loans by `game_id` in a dict gives you the one-loan-per-game "
        "rule for free (a second lend replaces the first) and a `get_loan(game_id)` "
        "lookup that returns None when the game is on the shelf:\n\n```python\ndef "
        "get_loan(self, game_id: str) -> Loan | None:\n    return self._loans.get("
        "game_id)\n```\n\nReturning is then `self._loans.pop(game_id)`, which is a nice "
        "sign the structure fits the problem. Ratings live on Game rather than in a "
        "separate table because there is one group opinion per game, not one per "
        "member; `dataclasses.replace(game, rating=stars)` produces the rated record.",
    ),
    Turn(
        "user",
        "Here is the test file for the catalogue as it stands, all green:\n\n```python\n"
        "import pytest\n\nfrom meepleshelf.shelf import Shelf, add_game\n\n\ndef "
        "test_add_assigns_sequential_ids():\n    s = Shelf()\n    assert add_game(s, "
        '"Azul", 2).game_id == "G1"\n    assert add_game(s, "Catan", 3).game_id == "G2"'
        "\n\n\ndef test_add_rejects_blank_title():\n    with pytest."
        'raises(ValueError):\n        add_game(Shelf(), "  ", 2)\n\n\ndef '
        "test_add_rejects_zero_players():\n    with pytest.raises(ValueError):\n        "
        'add_game(Shelf(), "Solo", 0)\n```\n\nOne of the members reviewed '
        "it and asked why `put_game` happily accepts a blank title when `add_game` "
        "refuses one. I said the check belongs at the door, but I could not say why "
        "the store should not also check. This is the exact exchange, more or less:\n\n"
        "```\n>>> s.put_game(\"\", 0)\nGame(game_id='G1', title='', min_players=0, "
        'rating=None)\n>>> add_game(s, "", 0)\nValueError: game title must not be '
        "blank\n```",
    ),
    Turn(
        "assistant",
        "The why is: one check, in one place, with one message. `add_game` is the door "
        "the scripts use, it validates and raises ValueError with words a member can "
        "read, and `put_game` is a plain store that writes what it is handed, so "
        "loading eighty games from JSON does not re-run eighty validations and there "
        "is exactly one place to look when a rule changes. The other design, checks in "
        "the storage methods with the public functions passing values through, is "
        "also coherent; what is not coherent is doing both, because then a rule "
        "change has to be made twice and the two copies drift. Pin the choice with a "
        "test that reads oddly on purpose:\n\n```python\ndef "
        "test_put_game_stores_without_checking():\n    s = Shelf()\n    g = s.put_game("
        '"", 0)\n    assert g.title == "" and g.min_players == 0\n```\n\nWhen your '
        "member asks again, that test is the answer: the store is trusting by design, "
        "and the REPL transcript you pasted is the intended behaviour, not a bug.",
    ),
    Turn(
        "user",
        "That test is in. Next: what should the public functions return? Right now "
        "`add_game` hands back the Game dataclass and `cupboard.py` does this to save "
        'it:\n\n```python\ngames = [asdict(g) for g in shelf.games()]\njson.dump({"games'
        '": games}, fh, indent=2)\n```\n\nA member who writes JavaScript for a living '
        "suggested the functions should just return dicts so the JSON step disappears "
        "and the web page he wants to build some day can consume them directly. I am "
        "not building a web page, but I do not want to pick a shape now that I regret "
        "when the lending code arrives, since Loan records will go through the same "
        "save and print paths. For what it is worth, here is the print path in "
        "`cupboard.py` today:\n\n```python\nfor game in shelf.games():\n    stars = "
        '"-" if game.rating is None else "*" * game.rating\n    print(f"{game.game_id:4} '
        '{game.title:30} {game.min_players}+ {stars}")\n```\n\nwhich is attribute '
        "access all the way down, and I would not enjoy rewriting it with subscripts.",
    ),
    Turn(
        "assistant",
        "Return the dataclasses. `asdict` is one call at the boundary, and what you "
        "get for it is a typed record everywhere else: `game.title` is checked by the "
        "editor, `loan.dyas` fails loudly instead of quietly returning None from "
        '`.get()`, equality works in tests (`assert shelf.get_loan("G1") == loan`), '
        "and frozen records cannot be mutated by a script that holds a stale copy. The "
        "future web page is served by the same `asdict` at the same boundary, so "
        "nothing is lost. The save path you pasted already handles Loan records "
        "without change:\n\n```python\nloans = [asdict(loan) for loan in shelf.loans()]\n"
        "```\n\nand the print path is a `str.format` over attributes, which reads "
        "better than dict subscripts anyway, as your `cupboard.py` loop already shows. "
        "If the JavaScript page ever happens, `json.dumps([asdict(g) for g in games])` "
        "is its whole API. The only discipline dataclasses ask for is that every "
        "public function returns the same record type for the same kind of thing, "
        "which one short test per function can pin.",
    ),
    Turn(
        "user",
        "Settled: public functions in meepleshelf return the model dataclass instances "
        "(Game, Loan), never dicts or tuples, and the scripts convert with asdict when "
        "they save. That is the rule for everything we add.",
    ),
    Turn(
        "assistant",
        "Noted: every public function returns Game or Loan instances (or None from "
        "lookups), never a dict or tuple, with JSON conversion left to the scripts. "
        "That keeps callers on one type per record.",
    ),
    Turn(
        "user",
        "And keep the validation layering exactly as it is today: input checks live in "
        "the public functions, which raise ValueError; the Shelf storage methods store "
        "what they are given and never raise ValueError on values. New features follow "
        "the same split.",
    ),
    Turn(
        "assistant",
        "Understood: validation stays in the public entry points, raising ValueError "
        "with a readable message, and the Shelf methods remain trusting stores. New "
        "storage methods get no value checks; new public functions check before "
        "calling the store, and the `put_game` test keeps that split honest.",
    ),
    Turn(
        "user",
        "For later: the meetup email wants a 'what is out' list. Roughly:\n\n```python\n"
        "for loan in shelf.loans():\n    game = shelf.get_game(loan.game_id)\n    print("
        'f"{game.title} - {loan.borrower} ({loan.days} days)")\n```\n\nwhere `loans()` '
        "does not exist yet.",
    ),
    Turn(
        "assistant",
        "That drops in once loans exist: `loans()` is `list(self._loans.values())`, a "
        "lookup that never raises, and the title comes from the catalogue side as you "
        "have it.",
    ),
    Turn(
        "user",
        "Right, let's finish the catalogue with ratings before the next meetup. I will "
        "paste the current files with each request so you see the true state rather "
        "than my memory of it.",
    ),
    Turn(
        "assistant",
        "Ready. Send the request with the files and I will return the complete shelf "
        "module.",
    ),
]

_EVENT = (
    "Scoped exception to the validation rule, effective now: for the lending features "
    "(lending a game out, returning it, extending a loan), value validation lives in "
    "the Shelf storage methods themselves, which raise ValueError, and the public loan "
    "functions pass values straight through with no check of their own. The catalogue "
    "side (add_game, rate_game and any future catalogue function) is unaffected and "
    "keeps validating in the public function; existing code stays exactly as it is."
)


def build() -> Session:
    return Session(
        id="S19",
        project="meepleshelf",
        target_family="validation",
        support_family="return_shape",
        lifecycle="scope",
        files=_FILES,
        prefix=_PREFIX,
        states=("api", "storage"),
        state_at=("api", "storage"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10),
    )
