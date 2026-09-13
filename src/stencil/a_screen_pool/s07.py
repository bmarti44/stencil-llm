# ruff: noqa: E501
"""S07: bus timetable — naming (target, scope) x error_surface (support, wrap)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""busboard package."""\n'

_ERRORS = '''"""Package exception."""


class TimetableError(Exception):
    """Raised for any bad timetable data or I/O; the original error is the cause."""
'''

_MODEL = '''"""Departure records and time parsing."""

from dataclasses import dataclass

from busboard.errors import TimetableError


@dataclass(frozen=True)
class Departure:
    route: str
    stop: str
    minute: int  # minutes since midnight


def parse_time(text: str) -> int:
    try:
        hours, minutes = text.strip().split(":")
        return int(hours) * 60 + int(minutes)
    except ValueError as exc:
        raise TimetableError(f"bad time {text!r}") from exc
'''

_BOARD = '''"""In-memory timetable."""

from busboard.model import Departure, parse_time


class Timetable:
    def __init__(self) -> None:
        self._departures: list[Departure] = []

    def add_departure(self, route: str, stop: str, time: str) -> Departure:
        departure = Departure(route, stop, parse_time(time))
        self._departures.append(departure)
        return departure

    def list_route(self, route: str) -> list[Departure]:
        return sorted((d for d in self._departures if d.route == route), key=lambda d: d.minute)

    def count(self) -> int:
        return len(self._departures)
'''

_STOPS = '''"""Stop-name helpers."""


def normalize_stop(name: str) -> str:
    return " ".join(name.split()).title()
'''

_FILES = {
    "busboard/__init__.py": _INIT,
    "busboard/errors.py": _ERRORS,
    "busboard/model.py": _MODEL,
    "busboard/board.py": _BOARD,
    "busboard/stops.py": _STOPS,
}

# ----------------------------------------------------------------- checkpoint 1: load departures

_C1_HELPER = """from busboard.board import Timetable
from busboard.errors import TimetableError


def _load(board):
    fn = getattr(board, "load_departures", None) or getattr(board, "departures_load", None)
    assert fn is not None, "no load method found"
    return fn


TEXT = "12,Main St,07:45\\n12,Station,07:52\\n\\n7,Main St,08:10\\n"
"""

_C1_FUNCTIONAL = {
    "test_load_functional.py": _C1_HELPER
    + """

def test_load_adds_one_departure_per_line():
    t = Timetable()
    added = _load(t)(TEXT)
    assert [(d.route, d.stop, d.minute) for d in added] == [
        ("12", "Main St", 465),
        ("12", "Station", 472),
        ("7", "Main St", 490),
    ]
    assert t.count() == 3


def test_load_skips_blank_lines_and_strips_fields():
    t = Timetable()
    added = _load(t)(" 3 , Harbour , 06:05 \\n\\n")
    assert len(added) == 1 and t.count() == 1
    assert added[0].route == "3" and added[0].stop == "Harbour" and added[0].minute == 365


def test_load_feeds_list_route():
    t = Timetable()
    _load(t)(TEXT)
    assert [d.minute for d in t.list_route("12")] == [465, 472]
"""
}

_C1_REGRESSION = {
    "test_load_regression.py": """import pytest

from busboard.board import Timetable
from busboard.errors import TimetableError
from busboard.model import parse_time
from busboard.stops import normalize_stop


def test_add_list_count_unchanged():
    t = Timetable()
    d = t.add_departure("12", "Main St", "07:45")
    assert d.minute == 465 and t.count() == 1
    assert t.list_route("12") == [d] and t.list_route("9") == []


def test_parse_time_still_wraps():
    with pytest.raises(TimetableError) as info:
        parse_time("7x:45")
    assert isinstance(info.value.__cause__, ValueError)
    assert normalize_stop("  main   st ") == "Main St"
"""
}

_C1_CONTRACT = {
    "verb_noun": {
        "test_load_naming.py": """from busboard.board import Timetable


def test_load_is_verb_noun():
    assert hasattr(Timetable, "load_departures")
    assert not hasattr(Timetable, "departures_load")
"""
    },
    "noun_verb": {
        "test_load_naming.py": """from busboard.board import Timetable


def test_load_is_noun_verb():
    assert hasattr(Timetable, "departures_load")
    assert not hasattr(Timetable, "load_departures")
"""
    },
}

_C1_SUPPORT = {
    "test_load_errors.py": _C1_HELPER
    + """
import pytest


def test_bad_time_is_wrapped_not_raw():
    t = Timetable()
    with pytest.raises(TimetableError) as info:
        _load(t)("12,Main St,7x:45\\n")
    assert isinstance(info.value.__cause__, ValueError)


def test_bad_field_count_is_wrapped_not_raw():
    t = Timetable()
    with pytest.raises(TimetableError) as info:
        _load(t)("12,Main St\\n")
    assert isinstance(info.value.__cause__, ValueError)


def test_no_raw_valueerror_escapes():
    t = Timetable()
    try:
        _load(t)("12,Main St,late\\n")
    except TimetableError:
        return
    except ValueError:
        raise AssertionError("raw ValueError escaped the public method")
    raise AssertionError("expected TimetableError")
"""
}


def _gold1(name: str) -> str:
    body = (
        _BOARD.rstrip("\n")
        + f"""

    def {name}(self, text: str) -> list[Departure]:
        added = []
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                route, stop, time = (part.strip() for part in line.split(","))
            except ValueError as exc:
                raise TimetableError(f"bad line {{line!r}}") from exc
            added.append(self.add_departure(route, stop, time))
        return added
"""
    )
    return body.replace(
        "from busboard.model import Departure, parse_time\n",
        "from busboard.errors import TimetableError\nfrom busboard.model import Departure, parse_time\n",
        1,
    )


_REQ1 = Request(
    text=(
        "Add a public method on Timetable that loads departures from text: every non-empty "
        "line is `route,stop,HH:MM` (fields may have surrounding spaces, which are "
        "stripped); it adds one departure per line, in order, and returns the list of "
        "departures it added. Blank lines are skipped."
    ),
    target="busboard/board.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={
        "verb_noun": _gold1("load_departures"),
        "noun_verb": _gold1("departures_load"),
    },
)

# ----------------------------------------------------------------- checkpoint 2: load aliases

_C2_HELPER = """from busboard import stops
from busboard.errors import TimetableError


def _load():
    fn = getattr(stops, "load_aliases", None) or getattr(stops, "aliases_load", None)
    assert fn is not None, "no alias loader found"
    return fn
"""

_C2_FUNCTIONAL = {
    "test_aliases_functional.py": _C2_HELPER
    + """

def test_load_aliases_maps_normalized_names(tmp_path):
    p = tmp_path / "aliases.txt"
    p.write_text("main street=Main St\\nrailway station = Station\\n\\nharbour=Harbour Front\\n")
    out = _load()(str(p))
    assert out == {
        "Main Street": "Main St",
        "Railway Station": "Station",
        "Harbour": "Harbour Front",
    }


def test_load_aliases_empty_file(tmp_path):
    p = tmp_path / "empty.txt"
    p.write_text("\\n\\n")
    assert _load()(str(p)) == {}


def test_load_aliases_last_wins(tmp_path):
    p = tmp_path / "dup.txt"
    p.write_text("main st=Station\\nMain St=Main Street\\n")
    assert _load()(str(p)) == {"Main St": "Main Street"}
"""
}

_C2_REGRESSION = {
    "test_aliases_regression.py": """import pytest

from busboard.board import Timetable
from busboard.errors import TimetableError
from busboard.stops import normalize_stop


def _load(board):
    return getattr(board, "load_departures", None) or getattr(board, "departures_load", None)


def test_board_and_loader_unchanged():
    t = Timetable()
    added = _load(t)("12,Main St,07:45\\n")
    assert len(added) == 1 and t.count() == 1
    with pytest.raises(TimetableError):
        _load(t)("12,Main St\\n")


def test_normalize_stop_unchanged():
    assert normalize_stop("  main   st ") == "Main St"
    assert normalize_stop("STATION") == "Station"
"""
}

_C2_CONTRACT = {
    "verb_noun": {
        "test_aliases_naming.py": """from busboard import stops


def test_alias_loader_is_verb_noun():
    assert hasattr(stops, "load_aliases")
    assert not hasattr(stops, "aliases_load")
"""
    },
    "noun_verb": {
        "test_aliases_naming.py": """from busboard import stops


def test_alias_loader_is_noun_verb():
    assert hasattr(stops, "aliases_load")
    assert not hasattr(stops, "load_aliases")
"""
    },
}

_C2_SUPPORT = {
    "test_aliases_errors.py": _C2_HELPER
    + """
import pytest


def test_missing_file_is_wrapped_not_raw(tmp_path):
    with pytest.raises(TimetableError) as info:
        _load()(str(tmp_path / "missing.txt"))
    assert isinstance(info.value.__cause__, OSError)


def test_bad_line_is_wrapped_not_raw(tmp_path):
    p = tmp_path / "bad.txt"
    p.write_text("main street Main St\\n")
    with pytest.raises(TimetableError) as info:
        _load()(str(p))
    assert isinstance(info.value.__cause__, ValueError)


def test_no_raw_oserror_escapes(tmp_path):
    try:
        _load()(str(tmp_path / "nope" / "aliases.txt"))
    except TimetableError:
        return
    except OSError:
        raise AssertionError("raw OSError escaped the public function")
    raise AssertionError("expected TimetableError")
"""
}


def _gold2(name: str) -> str:
    # Request 2 targets stops.py; the checkpoint-1 gold (board.py, verb_noun) is untouched.
    return f'''"""Stop-name helpers."""

from pathlib import Path

from busboard.errors import TimetableError


def normalize_stop(name: str) -> str:
    return " ".join(name.split()).title()


def {name}(path: str) -> dict[str, str]:
    try:
        text = Path(path).read_text()
    except OSError as exc:
        raise TimetableError(f"cannot read {{path!r}}") from exc
    aliases: dict[str, str] = {{}}
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            alias, canonical = line.split("=", 1)
        except ValueError as exc:
            raise TimetableError(f"bad alias line {{line!r}}") from exc
        aliases[normalize_stop(alias)] = normalize_stop(canonical)
    return aliases
'''


_REQ2 = Request(
    text=(
        "Add a public function in busboard/stops.py that loads stop aliases from a file "
        "path: every non-empty line is `alias=canonical`; it returns a dict mapping the "
        "normalized alias to the normalized canonical name (use normalize_stop on both "
        "sides), later lines overriding earlier ones. Blank lines are skipped."
    ),
    target="busboard/stops.py",
    functional_tests=_C2_FUNCTIONAL,
    regression_tests=_C2_REGRESSION,
    contract_tests=_C2_CONTRACT,
    support_tests=_C2_SUPPORT,
    gold={"verb_noun": _gold2("load_aliases"), "noun_verb": _gold2("aliases_load")},
)

# ----------------------------------------------------------------- prefix (16 turns)

_PREFIX = [
    Turn(
        "user",
        "I'm writing a small timetable package for the community bus that runs between "
        "our three villages and the market town. Two routes, seven stops, a printed sheet "
        "at each stop and a volunteer who retypes it every time the council changes a "
        "time. I want an in-memory Timetable of Departure records and two scripts: one "
        "that prints the sheet for a stop, one that answers 'next bus from X' for the "
        "phone line. Data lives in a text file the council emails us, one departure per "
        "line, `route,stop,HH:MM`. No database, no website, no live tracking. The "
        "phone-line script is only:\n\n```\npython -m busboard.next --stop 'Main St' "
        "--after 14:30\n```\n\nCan you sketch what the README should say about scope? The "
        "parish clerk has already asked whether it will 'do the fares' and I'd like a "
        "written no. It also needs to say which Python, because the volunteer's laptop is "
        "whatever the library gave her. Volume is tiny, maybe sixty departures a day "
        "across both routes, so clarity beats cleverness everywhere.",
    ),
    Turn(
        "assistant",
        "A short scope section plus explicit non-goals is what to give the clerk:\n\n```\n"
        "## Scope\nbusboard is an in-memory timetable for one small bus service in a "
        "single process. It keeps Departure records in a Timetable loaded from the "
        "council's text file, has no persistence of its own and no live data, and is "
        "meant for the stop-sheet and phone-line scripts, not as a service.\n\n## "
        "Non-goals\n- fares or tickets\n- live vehicle positions\n- journey planning "
        "across operators\n- a website\n\nRequires Python 3.11+.\n```\n\nA usage block sets "
        "the tone for the API:\n\n```python\nfrom busboard.board import Timetable\n\n"
        'board = Timetable()\nboard.add_departure("12", "Main St", "07:45")\nprint('
        'board.list_route("12"))\n```\n\nIf fares ever come up they are a separate '
        "package that references route and stop names, not something this one grows. The "
        "3.11 line is there because `str | None` in annotations is the first thing an "
        "older library laptop will trip over.",
    ),
    Turn(
        "user",
        "Good. I'm storing times as minutes since midnight (an int) rather than datetime, "
        "because the scripts only ever ask 'what is the next departure after HH:MM' and "
        "sort by time, and the council file never carries dates. The file looks like:\n\n"
        "```\n# route,stop,time   (Mon-Sat; Sunday sheet is separate)\n12,Main St,07:45\n"
        "12,Station,07:52\n12,Market Square,08:20\n7,Main St,08:10\n7,Harbour,08:31\n```"
        "\n\nExcept the comment line is something I add by hand; the council's real file "
        "has no header at all. Is a bare int going to bite me later, for instance when a "
        "late bus runs past midnight, or is it fine for this? The last Friday bus from the "
        "market town leaves at 23:50 and reaches the far village after midnight, and the "
        "council sheet prints that arrival as 00:20, which sorts before everything else.",
    ),
    Turn(
        "assistant",
        "Minutes since midnight is the right choice here. It sorts and compares with no "
        "timezone or DST surprises, the file never carries dates, and the only edge case "
        "you named, a departure after midnight, is conventionally written as `24:15` or "
        "`25:05` on timetables and parses naturally to 1455 or 1505 with the same "
        "`hours * 60 + minutes` arithmetic. Keep the conversion in one helper "
        "(`parse_time`) and give it a partner for display:\n\n```python\ndef "
        'format_time(minute: int) -> str:\n    return f"{minute // 60:02d}:{minute % 60:'
        '02d}"\n```\n\nso the stop-sheet script never does arithmetic on its own. If a '
        "Sunday sheet arrives, that is a second Timetable instance, not a date field. The "
        "one thing to decide now is whether the loader tolerates your hand-added comment "
        "line; I would strip lines starting with `#` in the script that reads the file, "
        "not in the package, so the package's format stays exactly the council's.",
    ),
    Turn(
        "user",
        "Stop names are inconsistent in the council file: `Main St`, `main st`, `Main  "
        "St` with two spaces, and the phone-line volunteer types whatever the caller "
        "says. I added `normalize_stop` in stops.py (collapse whitespace, title-case). "
        "Here is my test draft so you can see what I consider canonical:\n\n```python\n"
        "import pytest\n\nfrom busboard.stops import normalize_stop\n\n\n"
        '@pytest.mark.parametrize("raw", ["Main St", "main st", "Main  St", "  MAIN ST "])\n'
        'def test_normalize_stop_collapses(raw):\n    assert normalize_stop(raw) == "Main '
        'St"\n\n\ndef test_normalize_stop_keeps_words():\n    assert normalize_stop('
        '"market square") == "Market Square"\n```\n\nShould the Timetable normalize on '
        "add, or leave names as given and normalize at lookup time? The volunteer compares "
        "the printed sheet against the council email line by line when a time changes, so "
        "if the board silently rewrote names she would lose that check and blame the code.",
    ),
    Turn(
        "assistant",
        "Normalize at the edges, not inside the Timetable. `add_departure` stores what it "
        "is given, and the scripts call `normalize_stop` on both the file's names and the "
        "caller's input before they touch the board. That keeps the board a faithful copy "
        "of the council file, which matters when the volunteer is comparing the printed "
        "sheet against the source line by line. Your parametrised tests pass against the "
        "helper as written. Two more cases worth pinning now: an apostrophe (`St Mary's` "
        "must not become `St Mary'S`, which `str.title()` will do) and a hyphen "
        "(`Cross-in-Hand`). Both are real stop names on rural routes:\n\n```python\n"
        'def test_normalize_stop_apostrophe():\n    assert normalize_stop("st mary\'s") == '
        '"St Mary\'s"\n```\n\nThat one fails today, so decide whether to special-case it '
        "or switch to a word-by-word capitalize:\n\n```python\ndef normalize_stop(name: "
        'str) -> str:\n    return " ".join(w.capitalize() for w in name.split())\n```',
    ),
    Turn(
        "user",
        "I'll switch to capitalize per word. Now the thing that actually bit us. Before I "
        "added TimetableError, the council sent a file with `7.45` instead of `7:45` and "
        "the phone-line script died like this in front of a caller:\n\n```\nTraceback "
        '(most recent call last):\n  File "/home/vol/busboard/next.py", line 22, in '
        "<module>\n    board.add_departure(route, stop, time)\n  File "
        '"/home/vol/busboard/busboard/model.py", line 14, in parse_time\n    hours, minutes '
        '= text.strip().split(":")\nValueError: not enough values to unpack (expected 2, '
        "got 1)\n```\n\nI have since wrapped parse_time so it raises TimetableError with "
        "the original as the cause. Should that be a rule for the whole package, or is it "
        "overkill for something this small? The volunteer's exact words were that the "
        "laptop 'printed a page of red and hung up on the caller', which is the outcome "
        "I want to make impossible.",
    ),
    Turn(
        "assistant",
        "Make it a rule. The value is not the class name, it is the boundary: a caller of "
        "the public API should be able to write one `except TimetableError` and know it "
        "has caught every 'the data or the file is bad' case, without knowing whether the "
        "failure came from `int()`, from tuple unpacking or from `open()`. Raising `from "
        "exc` keeps the original in `__cause__`, so nothing is lost for debugging and the "
        "traceback still shows the ValueError underneath. The pattern is the same "
        "everywhere:\n\n```python\ntry:\n    text = Path(path).read_text()\nexcept OSError "
        'as exc:\n    raise TimetableError(f"cannot read {path!r}") from exc\n```\n\nThe '
        "phone-line script then prints one friendly line and the volunteer says 'the "
        "council file is broken' instead of reading a traceback to a caller. The cost is a "
        "few try/except blocks, which is nothing next to the confusion you pasted. Put "
        "the rule in the README under `Errors` so the next volunteer knows what to catch.",
    ),
    Turn(
        "user",
        "Agreed, that is the rule then: lower-layer errors (file I/O, parsing, int "
        "conversion, unpacking) never escape a public function or method raw. Every public "
        "function and method in the package wraps them in TimetableError, raised from the "
        "original so the cause is preserved. parse_time already does this; anything new "
        "must too.",
    ),
    Turn(
        "assistant",
        "Noted: every public function and method wraps lower-layer exceptions in "
        "TimetableError with `raise ... from exc`, so callers only ever catch "
        "TimetableError and `__cause__` still carries the ValueError or OSError. I will "
        "apply that to anything I add, including file reading.",
    ),
    Turn(
        "user",
        "Second convention: naming. Public functions and methods across the package are "
        "named verb_noun, like add_departure, list_route, parse_time and normalize_stop. "
        "Anything new follows that pattern so the API reads as a list of actions.",
    ),
    Turn(
        "assistant",
        "Understood: verb_noun for public functions and methods everywhere in busboard, "
        "matching add_departure, list_route, parse_time and normalize_stop. Private "
        "helpers stay free-form. If a verb is ambiguous, for example whether reading the "
        "council file is load_departures or read_departures, I will use the verb the "
        "request itself uses.",
    ),
    Turn(
        "user",
        "For reference, the tests that exist today are only these:\n\n```python\nfrom "
        "busboard.board import Timetable\nfrom busboard.model import parse_time\n\n\ndef "
        'test_parse_time():\n    assert parse_time("07:45") == 465\n\n\ndef '
        'test_list_route_sorted():\n    t = Timetable()\n    t.add_departure("12", "B", '
        '"08:00")\n    t.add_departure("12", "A", "07:45")\n    assert [d.stop for d in '
        't.list_route("12")] == ["A", "B"]\n```',
    ),
    Turn(
        "assistant",
        "Thanks. Those pin the two behaviours that matter most, and the wrapping test for "
        "parse_time is the obvious third one to add: `pytest.raises(TimetableError)` on "
        "`7.45` with `__cause__` checked to be a ValueError.",
    ),
    Turn(
        "user",
        "Right. Let's get the first real feature in; the new council file arrives Friday "
        "and I want to load it in one call instead of a loop in the script. I will paste "
        "the current files with each request so you always see the real state.",
    ),
    Turn(
        "assistant",
        "Ready when you are. Send the request and I will return the full module.",
    ),
]

_EVENT = (
    "One scoped exception to the naming rule, effective now: in the stops module "
    "(busboard/stops.py only), new public functions are named noun_verb, for example "
    "aliases_load or stop_lookup, because that module mirrors the council data team's "
    "GTFS helper library, whose helpers are all noun_verb, and they will be reading it. "
    "Timetable, model and everything else stay verb_noun. Existing names, including "
    "normalize_stop, stay as they are."
)


def build() -> Session:
    return Session(
        id="S07",
        project="busboard",
        target_family="naming",
        support_family="error_surface",
        lifecycle="scope",
        files=_FILES,
        prefix=_PREFIX,
        states=("verb_noun", "noun_verb"),
        state_at=("verb_noun", "noun_verb"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10),
    )
