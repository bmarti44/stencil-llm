# ruff: noqa: E501
"""S08: chess ratings — naming (target, reinstatement) x error_surface=wrap (support)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""ratingbook package."""\n'

_MODEL = '''"""Player records and the package error."""

from dataclasses import dataclass, replace


class RatingBookError(Exception):
    """Anything that went wrong underneath RatingBook's public API."""


@dataclass(frozen=True)
class Player:
    player_id: str
    name: str
    rating: int = 1500
    games: int = 0

    def with_rating(self, rating: int) -> "Player":
        return replace(self, rating=rating, games=self.games + 1)
'''

_ELO = '''"""Elo arithmetic and result-sheet parsing."""

K = 32
SCORES = {"1-0": 1.0, "0-1": 0.0, "1/2-1/2": 0.5}


def parse_score(text: str) -> float:
    key = text.strip()
    if key not in SCORES:
        raise ValueError(f"bad result: {text!r}")
    return SCORES[key]


def parse_line(line: str) -> tuple[str, str, str]:
    parts = line.split()
    if len(parts) != 3:
        raise ValueError(f"bad result line: {line!r}")
    return parts[0], parts[1], parts[2]


def expected(rating: int, opponent: int) -> float:
    return 1.0 / (1.0 + 10 ** ((opponent - rating) / 400))


def adjust(rating: int, opponent: int, score: float) -> int:
    return round(rating + K * (score - expected(rating, opponent)))
'''

_STORE = '''"""In-memory rating book."""

from ratingbook.model import Player


class RatingBook:
    def __init__(self) -> None:
        self._players: dict[str, Player] = {}
        self._counter = 0

    def add_player(self, name: str, rating: int = 1500) -> Player:
        self._counter += 1
        player = Player(player_id=f"P{self._counter}", name=name, rating=rating)
        self._players[player.player_id] = player
        return player

    def find(self, player_id: str) -> Player | None:
        return self._players.get(player_id)

    def count(self) -> int:
        return len(self._players)
'''

_FILES = {
    "ratingbook/__init__.py": _INIT,
    "ratingbook/model.py": _MODEL,
    "ratingbook/elo.py": _ELO,
    "ratingbook/store.py": _STORE,
}

# ----------------------------------------------------------------- checkpoint 1: record a game

_C1_HELPER = """import pytest

from ratingbook.model import RatingBookError
from ratingbook.store import RatingBook


def _record(book):
    fn = getattr(book, "record_game", None) or getattr(book, "game_record", None)
    assert fn is not None, "no record method found"
    return fn


def _book():
    b = RatingBook()
    b.add_player("Ana", 1600)
    b.add_player("Bo", 1400)
    return b
"""

_C1_FUNCTIONAL = {
    "test_record_functional.py": _C1_HELPER
    + """

def test_white_win_moves_both_ratings():
    b = _book()
    w, bl = _record(b)("P1", "P2", "1-0")
    assert (w.rating, bl.rating) == (1608, 1392)
    assert b.find("P1").rating == 1608 and b.find("P2").rating == 1392
    assert w.games == 1 and bl.games == 1


def test_draw_between_equals_changes_nothing_but_games():
    b = RatingBook()
    b.add_player("x")
    b.add_player("y")
    w, bl = _record(b)("P1", "P2", "1/2-1/2")
    assert w.rating == 1500 and bl.rating == 1500
    assert w.games == 1 and bl.games == 1


def test_black_win_equal_ratings():
    b = RatingBook()
    b.add_player("x")
    b.add_player("y")
    w, bl = _record(b)("P1", "P2", "0-1")
    assert (w.rating, bl.rating) == (1484, 1516)


def test_unknown_player_raises_keyerror():
    b = _book()
    with pytest.raises(KeyError):
        _record(b)("P1", "P9", "1-0")


def test_bad_result_leaves_ratings_untouched():
    b = _book()
    with pytest.raises(Exception):
        _record(b)("P1", "P2", "2-0")
    assert b.find("P1").rating == 1600 and b.find("P2").rating == 1400
    assert b.find("P1").games == 0
"""
}

_C1_REGRESSION = {
    "test_record_regression.py": """from ratingbook.elo import adjust, parse_score
from ratingbook.store import RatingBook


def test_add_find_count_unchanged():
    b = RatingBook()
    p = b.add_player("Ana")
    assert p.player_id == "P1" and p.rating == 1500 and p.games == 0
    assert b.find("P1") is p
    assert b.find("P7") is None
    assert b.count() == 1


def test_elo_helpers_unchanged():
    assert parse_score(" 1-0 ") == 1.0
    assert adjust(1500, 1500, 1.0) == 1516
"""
}

_C1_CONTRACT = {
    "verb_noun": {
        "test_record_naming.py": """from ratingbook.store import RatingBook


def test_record_is_verb_noun():
    assert hasattr(RatingBook, "record_game")
    assert not hasattr(RatingBook, "game_record")
"""
    },
    "noun_verb": {
        "test_record_naming.py": """from ratingbook.store import RatingBook


def test_record_is_noun_verb():
    assert hasattr(RatingBook, "game_record")
    assert not hasattr(RatingBook, "record_game")
"""
    },
}

_C1_SUPPORT = {
    "test_record_errors.py": _C1_HELPER
    + """

def test_bad_result_is_wrapped_in_package_error():
    b = _book()
    with pytest.raises(RatingBookError) as info:
        _record(b)("P1", "P2", "2-0")
    assert not isinstance(info.value, ValueError)
    assert isinstance(info.value.__cause__, ValueError)
"""
}


def _gold1(name: str) -> str:
    return (
        _STORE.replace(
            "from ratingbook.model import Player\n",
            "from ratingbook.elo import adjust, parse_score\n"
            "from ratingbook.model import Player, RatingBookError\n",
            1,
        ).rstrip("\n")
        + f"""

    def {name}(self, white_id: str, black_id: str, result: str) -> tuple[Player, Player]:
        white = self._players[white_id]
        black = self._players[black_id]
        try:
            score = parse_score(result)
        except ValueError as exc:
            raise RatingBookError(str(exc)) from exc
        new_white = white.with_rating(adjust(white.rating, black.rating, score))
        new_black = black.with_rating(adjust(black.rating, white.rating, 1.0 - score))
        self._players[white_id] = new_white
        self._players[black_id] = new_black
        return new_white, new_black
"""
    )


_REQ1 = Request(
    text=(
        "Add a public method on RatingBook that records one game: it takes the white "
        "player's id, the black player's id and the result string as written on the "
        'sheet ("1-0", "0-1" or "1/2-1/2"), updates both players with the Elo helpers in '
        "elo.py (white scores the parsed value, black scores one minus it), stores the "
        "updated players and returns them as a (white, black) tuple. An unknown id "
        "raises KeyError. A result that does not parse must leave both players untouched."
    ),
    target="ratingbook/store.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"verb_noun": _gold1("record_game"), "noun_verb": _gold1("game_record")},
)

# ----------------------------------------------------------------- checkpoint 2: import a sheet

_C2_HELPER = """import pytest

from ratingbook.model import RatingBookError
from ratingbook.store import RatingBook


def _import(book):
    fn = getattr(book, "import_results", None) or getattr(book, "results_import", None)
    assert fn is not None, "no import method found"
    return fn


def _book():
    b = RatingBook()
    b.add_player("Ana", 1600)
    b.add_player("Bo", 1400)
    b.add_player("Cy", 1500)
    return b
"""

_C2_FUNCTIONAL = {
    "test_import_functional.py": _C2_HELPER
    + """

def test_import_records_each_line_in_order():
    b = _book()
    n = _import(b)(["P1 P2 1-0", "", "P2 P3 1/2-1/2"])
    assert n == 2
    assert b.find("P1").rating == 1608
    assert b.find("P2").games == 2
    assert b.find("P3").games == 1


def test_import_empty_sheet_is_zero():
    b = _book()
    assert _import(b)([]) == 0
    assert b.find("P1").games == 0


def test_import_unknown_player_raises_keyerror():
    b = _book()
    with pytest.raises(KeyError):
        _import(b)(["P1 P9 1-0"])


def test_import_stops_at_bad_line_after_applying_earlier_ones():
    b = _book()
    with pytest.raises(Exception):
        _import(b)(["P1 P2 1-0", "P2 P3"])
    assert b.find("P1").games == 1
    assert b.find("P3").games == 0
"""
}

_C2_REGRESSION = {
    "test_import_regression.py": """from ratingbook.store import RatingBook


def _record(book):
    return getattr(book, "record_game", None) or getattr(book, "game_record", None)


def test_add_find_record_unchanged():
    b = RatingBook()
    b.add_player("Ana", 1600)
    b.add_player("Bo", 1400)
    assert b.count() == 2 and b.find("P3") is None
    w, bl = _record(b)("P1", "P2", "0-1")
    assert (w.rating, bl.rating) == (1576, 1424)
"""
}

_C2_CONTRACT = {
    "verb_noun": {
        "test_import_naming.py": """from ratingbook.store import RatingBook


def test_import_is_verb_noun():
    assert hasattr(RatingBook, "import_results")
    assert not hasattr(RatingBook, "results_import")
"""
    },
    "noun_verb": {
        "test_import_naming.py": """from ratingbook.store import RatingBook


def test_import_is_noun_verb():
    assert hasattr(RatingBook, "results_import")
    assert not hasattr(RatingBook, "import_results")
"""
    },
}

_C2_SUPPORT = {
    "test_import_errors.py": _C2_HELPER
    + """

def test_bad_line_is_wrapped_in_package_error():
    b = _book()
    with pytest.raises(RatingBookError) as info:
        _import(b)(["P1 P2"])
    assert not isinstance(info.value, ValueError)
    assert isinstance(info.value.__cause__, ValueError)


def test_bad_result_inside_line_is_wrapped_in_package_error():
    b = _book()
    with pytest.raises(RatingBookError):
        _import(b)(["P1 P2 3-0"])
"""
}


def _gold2(name: str) -> str:
    # Built on the checkpoint-1 gold under the state then in force (noun_verb).
    return (
        _gold1("game_record")
        .replace(
            "from ratingbook.elo import adjust, parse_score\n",
            "from ratingbook.elo import adjust, parse_line, parse_score\n",
            1,
        )
        .rstrip("\n")
        + f"""

    def {name}(self, lines: list[str]) -> int:
        done = 0
        for line in lines:
            if not line.strip():
                continue
            try:
                white_id, black_id, result = parse_line(line)
            except ValueError as exc:
                raise RatingBookError(str(exc)) from exc
            self.game_record(white_id, black_id, result)
            done += 1
        return done
"""
    )


_REQ2 = Request(
    text=(
        "Add a public method on RatingBook that imports a whole result sheet: it takes a "
        'list of text lines of the form "<white_id> <black_id> <result>" (use parse_line '
        "from elo.py), skips blank lines, records each game through the existing "
        "game-recording method in order, and returns how many games it recorded. A "
        "malformed line stops the import at that point; games before it stay recorded. "
        "An unknown id raises KeyError."
    ),
    target="ratingbook/store.py",
    functional_tests=_C2_FUNCTIONAL,
    regression_tests=_C2_REGRESSION,
    contract_tests=_C2_CONTRACT,
    support_tests=_C2_SUPPORT,
    gold={
        "verb_noun": _gold2("import_results"),
        "noun_verb": _gold2("results_import"),
    },
)

# ----------------------------------------------------------------- prefix (16 turns)

_PREFIX = [
    Turn(
        "user",
        "I run the Tuesday club at the library and I've been keeping everyone's Elo in a "
        "spreadsheet that three people edit and nobody trusts. I want to replace it with a "
        "tiny Python package, ratingbook, that the arbiter can drive from a script after "
        "each round: add players, record results, print standings. No database, no web "
        "page, no FIDE sync. About forty members, maybe sixty games a week in the busy "
        "season. Here's the sheet format the arbiter already writes by hand, one line per "
        "board, which I'd like to keep because people are used to it:\n\n```\n# round 3, "
        "14 Sep\nP4  P11  1-0\nP7  P2   1/2-1/2\nP9  P13  0-1\n```\n\nCan you draft the "
        "README scope paragraph so nobody expects a tournament manager? I want to say "
        "clearly what it does, what it never will do, and that the sheet is the only input "
        "format we promise to keep stable.",
    ),
    Turn(
        "assistant",
        "Something like this keeps it honest:\n\n```\n## Scope\nratingbook keeps club Elo "
        "ratings in memory for a single process. It knows players, results and the K=32 "
        "Elo update, and it reads the arbiter's plain-text result sheet. It is a library "
        "for scripts and tests, not a tournament manager: no pairings, no rounds, no "
        "tie-breaks, no persistence beyond what your script writes out.\n\n## Stable "
        "input\nThe result sheet (`white black result`, one board per line, `#` comments) "
        "is the only input format we promise to keep.\n\n## Non-goals\n- pairings and "
        "Swiss systems\n- FIDE/ECF rating export\n- web UI\n```\n\nThe 'stable input' "
        "section is worth keeping separate from scope, because it is the one promise the "
        "arbiter actually relies on. A usage snippet rounds it out:\n\n```python\nfrom "
        "ratingbook.store import RatingBook\n\nbook = RatingBook()\nana = book.add_player("
        '"Ana", 1600)\nprint(ana.player_id, ana.rating)  # P1 1600\n```',
    ),
    Turn(
        "user",
        "Good. On the Elo arithmetic: I put `expected` and `adjust` in elo.py with K=32 "
        "and `round()`. A member who teaches maths says we should carry floats and only "
        "round for display, otherwise the ratings drift. Is he right enough that I should "
        "change it before anything depends on it? Here is what I have:\n\n```python\ndef "
        "expected(rating: int, opponent: int) -> float:\n    return 1.0 / (1.0 + 10 ** "
        "((opponent - rating) / 400))\n\n\ndef adjust(rating: int, opponent: int, score: "
        "float) -> int:\n    return round(rating + K * (score - expected(rating, "
        "opponent)))\n```\n\nThe old spreadsheet rounded after every game too, so the "
        "numbers would at least match what people have on the wall.",
    ),
    Turn(
        "assistant",
        "He is right that rounding after every game loses information, but for a club list "
        "the drift is a few points over a season and it is exactly what the spreadsheet did, "
        "so matching the wall matters more. Integer ratings also make tests exact: "
        "`adjust(1500, 1500, 1.0) == 1516` and `adjust(1600, 1400, 1.0) == 1608` are "
        "facts you can assert, while floats need tolerances everywhere. Keep ints. If "
        "drift ever bothers people, the fix is to store a float `rating_exact` alongside "
        "and keep `rating` as its rounded view, which is additive and does not break the "
        "sheet or the tests. One thing to pin now: `round()` in Python is banker's "
        "rounding, so `round(1500.5)` is 1500, not 1501. Write that into a test so nobody "
        "'fixes' it later.",
    ),
    Turn(
        "user",
        "Noted on banker's rounding. Player ids: I mint P1, P2, ... from a counter in "
        "`add_player`. The arbiter writes those ids on the sheet by hand, so they must "
        "stay short. Someone suggested using the membership number instead, which is a "
        "six-digit thing from the national body that half the juniors do not have yet. I "
        "would rather not. Also, should `find` raise or return None for an unknown id? "
        "This is what bit me in the first script:\n\n```\nTraceback (most recent call "
        'last):\n  File "standings.py", line 12, in <module>\n    print(book.find("P14")'
        ".rating)\nAttributeError: 'NoneType' object has no attribute 'rating'\n```\n\n"
        "That happened because a junior had been typed in as P14 on the sheet but never "
        "added to the book, which will keep happening.",
    ),
    Turn(
        "assistant",
        "Keep the counter ids; short ids that fit on a paper sheet are the whole point, and "
        "a membership number can be an optional field on Player later. For lookups, the "
        "usual split is: `find` returns None because its name promises a search, while "
        "methods that *act* on a player (recording a game, retiring a player) raise "
        "KeyError on an unknown id, because acting on a ghost is a caller bug and should "
        "fail loudly at the sheet line that caused it. Your traceback then becomes "
        "`KeyError: 'P14'` raised from the record call, which tells the arbiter exactly "
        "what to fix. If the standings script wants a hard failure from a lookup it can "
        "wrap it:\n\n```python\ndef require(book, player_id):\n    p = book.find("
        "player_id)\n    if p is None:\n        raise KeyError(player_id)\n    return p\n"
        "```",
    ),
    Turn(
        "user",
        "Agreed: lookups return None, actions raise KeyError. Next, the sheet parser. I "
        "wrote `parse_score` and `parse_line` in elo.py and they raise ValueError on junk. "
        "Here is my test draft; tell me if the cases are the right ones or if I'm "
        "missing an obvious one:\n\n```python\nimport pytest\n\nfrom ratingbook.elo "
        "import parse_line, parse_score\n\n\ndef test_parse_score_variants():\n    assert "
        'parse_score("1-0") == 1.0\n    assert parse_score(" 0-1 ") == 0.0\n    assert '
        'parse_score("1/2-1/2") == 0.5\n\n\ndef test_parse_score_rejects_junk():\n    '
        'with pytest.raises(ValueError):\n        parse_score("2-0")\n\n\ndef '
        'test_parse_line_splits_three_fields():\n    assert parse_line("P4  P11  1-0") '
        '== ("P4", "P11", "1-0")\n\n\ndef test_parse_line_rejects_two_fields():\n    '
        'with pytest.raises(ValueError):\n        parse_line("P4 P11")\n```',
    ),
    Turn(
        "assistant",
        "Those are the right cases. Two more worth adding: a result written with a letter "
        "x (`1-0x` is how some people mark a forfeit win) should be rejected until we "
        "decide what forfeits mean for ratings, and a line with four fields (someone adds "
        "the board number) should also raise rather than silently taking the first three. "
        "Both are one-liners:\n\n```python\ndef test_parse_score_rejects_forfeit_mark():\n"
        '    with pytest.raises(ValueError):\n        parse_score("1-0x")\n\n\ndef '
        "test_parse_line_rejects_four_fields():\n    with pytest.raises(ValueError):\n"
        '        parse_line("3 P4 P11 1-0")\n```\n\nComment lines starting with `#` are '
        "a sheet-level concern, so whatever reads the sheet should strip them before "
        "calling `parse_line`, rather than teaching the parser about comments.",
    ),
    Turn(
        "user",
        "Two conventions I want written down before we add real methods. First, the "
        "error surface: anything that fails underneath a public RatingBook method, "
        "parsing a result, a bad sheet line, a file that will not open, gets wrapped in "
        "RatingBookError (it is already in model.py). Callers of the public API never see "
        "a raw ValueError or OSError; they catch one package exception. Chain the original "
        "with `from exc` so the cause is still there for debugging.",
    ),
    Turn(
        "assistant",
        "Understood: public RatingBook methods wrap lower-layer failures (parsing, I/O) in "
        "RatingBookError with `raise RatingBookError(...) from exc`, so the standings "
        "script catches one type and the cause stays on `__cause__`. KeyError for an "
        "unknown player id is not a lower-layer failure, it is the method's own contract, "
        "so it stays a plain KeyError.",
    ),
    Turn(
        "user",
        "Second, naming: public RatingBook methods are verb_noun, like add_player. New "
        "methods follow the same pattern so the class reads as a list of things the "
        "arbiter can do.",
    ),
    Turn(
        "assistant",
        "Noted: verb_noun for new public RatingBook methods, matching add_player. Private "
        "helpers can be named freely. Where the verb is ambiguous I will use the verb the "
        "request itself uses.",
    ),
    Turn(
        "user",
        "Actually, I have been reading the style guide our other club project uses and "
        "they went noun_verb for store classes (player_add, game_record) so that "
        "autocomplete groups methods by the thing they touch. Let's try that here: from "
        "now on, new public RatingBook methods are noun_verb. Existing names such as "
        "add_player stay as they are.",
    ),
    Turn(
        "assistant",
        "Switching: new public RatingBook methods are noun_verb from now on (for example "
        "game_record, player_retire). add_player, find and count keep their names. If you "
        "decide against it later, say so and I will go back to verb_noun for anything "
        "new.",
    ),
    Turn(
        "user",
        "One more thing for later, not now: standings. The arbiter wants a sorted list "
        "for the notice board, highest rating first, ties by name. Roughly:\n\n```python\n"
        "def standings(book: RatingBook) -> list[str]:\n    players = sorted(book.all(), "
        'key=lambda p: (-p.rating, p.name))\n    return [f"{i + 1:2d}. {p.name:<20} '
        '{p.rating}  ({p.games} games)" for i, p in enumerate(players)]\n```\n\nwhere '
        "`all()` does not exist yet. The only tests that exist today are these:\n\n"
        "```python\nfrom ratingbook.store import RatingBook\n\n\ndef "
        'test_add_player_mints_sequential_ids():\n    b = RatingBook()\n    assert b.add_player("Ana").player_id == "P1"\n'
        '    assert b.add_player("Bo", 1700).rating == 1700\n\n\ndef '
        'test_find_missing_is_none():\n    assert RatingBook().find("P1") is None\n```',
    ),
    Turn(
        "assistant",
        "Noted for later. `all()` would be `list(self._players.values())` in insertion "
        "order, and the standings sort you sketched is right; provisional players (fewer "
        "than, say, five games) usually get an asterisk, which is a display concern for "
        "the script. Send the first real request whenever you are ready and I will return "
        "the complete store module.",
    ),
]

_EVENT = (
    "Scrap the noun_verb experiment, it reads badly next to add_player. Back to the "
    "original rule: new public RatingBook methods are verb_noun. Whatever has already "
    "been added keeps its current name; only new methods follow verb_noun again."
)


def build() -> Session:
    return Session(
        id="S08",
        project="ratingbook",
        target_family="naming",
        support_family="error_surface",
        lifecycle="reinstatement",
        files=_FILES,
        prefix=_PREFIX,
        states=("verb_noun", "noun_verb"),
        state_at=("noun_verb", "verb_noun"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10, 12),
    )
