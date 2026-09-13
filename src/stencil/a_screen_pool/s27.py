# ruff: noqa: E501
"""S27: film festival — validation (target, scope) x error_surface=propagate (support)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""festival package."""\n'

_MODEL = '''"""Festival records."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Film:
    title: str
    director: str
    minutes: int = 0


@dataclass(frozen=True)
class Screening:
    screening_id: str
    title: str
    room: str
    start: str
'''

_AUDIT = '''"""Audit log: one line per change."""

from pathlib import Path


def append_line(path: Path, line: str) -> None:
    with Path(path).open("a") as fh:
        fh.write(line + "\\n")
'''


def _films(
    store_extra: str = "", api_extra: str = "", use_replace: bool = False
) -> str:
    rep = "from dataclasses import replace\n\n" if use_replace else ""
    return f'''"""Film catalogue: store and public operations."""

{rep}from festival.audit import append_line
from festival.model import Film


class FilmStore:
    def __init__(self, log_path) -> None:
        self._log_path = log_path
        self._films: dict[str, Film] = {{}}

    def put(self, film: Film) -> Film:
        self._films[film.title] = film
        append_line(self._log_path, f"film {{film.title}}")
        return film

    def get(self, title: str) -> Film | None:
        return self._films.get(title)
{store_extra}

def register_film(store: FilmStore, title: str, director: str) -> Film:
    if not title.strip() or not director.strip():
        raise ValueError("title and director must be non-empty")
    return store.put(Film(title=title, director=director))
{api_extra}'''


def _schedule(
    store_extra: str = "", api_extra: str = "", use_replace: bool = False
) -> str:
    rep = "from dataclasses import replace\n\n" if use_replace else ""
    return f'''"""Screening schedule: store and public operations."""

{rep}from festival.audit import append_line
from festival.model import Screening


class ScreeningStore:
    def __init__(self, log_path) -> None:
        self._log_path = log_path
        self._screenings: dict[str, Screening] = {{}}
        self._counter = 0

    def add(self, title: str, room: str, start: str) -> Screening:
        self._counter += 1
        s = Screening(f"SC{{self._counter}}", title, room, start)
        self._screenings[s.screening_id] = s
        append_line(self._log_path, f"screening {{s.screening_id}} {{title}}")
        return s

    def get(self, screening_id: str) -> Screening | None:
        return self._screenings.get(screening_id)
{store_extra}

def book_screening(store: ScreeningStore, title: str, room: str, start: str) -> Screening:
    if not room.strip() or len(start) != 5 or start[2] != ":":
        raise ValueError("room must be non-empty and start HH:MM")
    return store.add(title, room, start)
{api_extra}'''


_FILES = {
    "festival/__init__.py": _INIT,
    "festival/model.py": _MODEL,
    "festival/audit.py": _AUDIT,
    "festival/films.py": _films(),
    "festival/schedule.py": _schedule(),
}

# ----------------------------------------------------------------- checkpoint 1: set_runtime (films.py)

_V_RUNTIME_STORE = '        if minutes <= 0:\n            raise ValueError("minutes must be positive")\n'
_V_RUNTIME_API = (
    '    if minutes <= 0:\n        raise ValueError("minutes must be positive")\n'
)


def _store_runtime(validate: bool) -> str:
    return (
        "\n    def put_runtime(self, title: str, minutes: int) -> Film:\n"
        + (_V_RUNTIME_STORE if validate else "")
        + """        updated = replace(self._films[title], minutes=minutes)
        self._films[title] = updated
        append_line(self._log_path, f"runtime {title} {minutes}")
        return updated
"""
    )


def _api_runtime(validate: bool) -> str:
    return (
        "\n\ndef set_runtime(store: FilmStore, title: str, minutes: int) -> Film:\n"
        + (_V_RUNTIME_API if validate else "")
        + "    return store.put_runtime(title, minutes)\n"
    )


def _gold1(state: str) -> str:
    api = state == "api"
    return _films(_store_runtime(not api), _api_runtime(api), use_replace=True)


_C1_SETUP = """import pytest

from festival.films import FilmStore, register_film, set_runtime
from festival.model import Film


def _store(tmp_path):
    store = FilmStore(tmp_path / "films.log")
    register_film(store, "Slow River", "A. Okafor")
    register_film(store, "Night Shift", "L. Berg")
    return store
"""

_C1_FUNCTIONAL = {
    "test_runtime_functional.py": _C1_SETUP
    + """

def test_set_runtime_updates_and_returns_film(tmp_path):
    store = _store(tmp_path)
    out = set_runtime(store, "Slow River", 96)
    assert isinstance(out, Film)
    assert out.minutes == 96 and out.director == "A. Okafor"
    assert store.get("Slow River").minutes == 96


def test_set_runtime_appends_log_line(tmp_path):
    store = _store(tmp_path)
    set_runtime(store, "Night Shift", 112)
    lines = (tmp_path / "films.log").read_text().splitlines()
    assert lines[-1] == "runtime Night Shift 112"
    assert len(lines) == 3


def test_set_runtime_rejects_zero(tmp_path):
    store = _store(tmp_path)
    with pytest.raises(ValueError):
        set_runtime(store, "Slow River", 0)
    assert store.get("Slow River").minutes == 0
    assert len((tmp_path / "films.log").read_text().splitlines()) == 2


def test_set_runtime_unknown_title_raises_keyerror(tmp_path):
    store = _store(tmp_path)
    with pytest.raises(KeyError):
        set_runtime(store, "Unlisted", 90)
"""
}

_C1_REGRESSION = {
    "test_runtime_regression.py": """import pytest

from festival.films import FilmStore, register_film


def test_register_and_get_unchanged(tmp_path):
    store = FilmStore(tmp_path / "films.log")
    f = register_film(store, "Slow River", "A. Okafor")
    assert store.get("Slow River") is f and f.minutes == 0
    assert store.get("nope") is None
    assert (tmp_path / "films.log").read_text() == "film Slow River\\n"


def test_register_still_validates_in_public_function(tmp_path):
    store = FilmStore(tmp_path / "films.log")
    with pytest.raises(ValueError):
        register_film(store, "", "A. Okafor")
    with pytest.raises(ValueError):
        register_film(store, "Slow River", " ")
"""
}

_C1_CONTRACT = {
    "api": {
        "test_runtime_validation.py": _C1_SETUP
        + """

def test_public_set_runtime_raises_on_nonpositive(tmp_path):
    store = _store(tmp_path)
    with pytest.raises(ValueError):
        set_runtime(store, "Slow River", -5)


def test_store_put_runtime_trusts_its_argument(tmp_path):
    store = _store(tmp_path)
    out = store.put_runtime("Slow River", -5)
    assert out.minutes == -5
    assert store.get("Slow River").minutes == -5
"""
    },
    "storage": {
        "test_runtime_validation.py": _C1_SETUP
        + """

def test_store_put_runtime_raises_on_nonpositive(tmp_path):
    store = _store(tmp_path)
    with pytest.raises(ValueError):
        store.put_runtime("Slow River", -5)
    assert store.get("Slow River").minutes == 0


def test_public_set_runtime_delegates_without_precheck(tmp_path, monkeypatch):
    store = _store(tmp_path)
    calls = []

    def spy(self, *args, **kwargs):
        calls.append(args + tuple(kwargs.values()))
        return self._films["Slow River"]

    monkeypatch.setattr(FilmStore, "put_runtime", spy)
    set_runtime(store, "Slow River", -5)
    assert len(calls) == 1 and -5 in calls[0]
"""
    },
}

_C1_SUPPORT = {
    "test_runtime_errors.py": """import shutil

import pytest

from festival.films import FilmStore, register_film, set_runtime


def test_set_runtime_lets_os_error_propagate_raw(tmp_path):
    folder = tmp_path / "logs"
    folder.mkdir()
    store = FilmStore(folder / "films.log")
    register_film(store, "Slow River", "A. Okafor")
    shutil.rmtree(folder)
    with pytest.raises(FileNotFoundError) as info:
        set_runtime(store, "Slow River", 96)
    assert type(info.value) is FileNotFoundError


def test_set_runtime_no_error_on_healthy_log(tmp_path):
    store = FilmStore(tmp_path / "films.log")
    register_film(store, "Slow River", "A. Okafor")
    assert set_runtime(store, "Slow River", 96).minutes == 96
"""
}

_REQ1 = Request(
    text=(
        "Add `set_runtime(store, title, minutes)` to festival/films.py: it records the "
        "running time of a registered film and returns the updated Film, via a new store "
        "method `FilmStore.put_runtime(title, minutes)` that swaps in the record and "
        "appends the audit line `runtime <title> <minutes>`. A non-positive running time "
        "is invalid and is rejected with ValueError before anything is stored or logged; "
        "an unknown title raises KeyError."
    ),
    target="festival/films.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"api": _gold1("api"), "storage": _gold1("storage")},
)

# ----------------------------------------------------------------- checkpoint 2: assign_room (schedule.py)

_V_ROOM_STORE = '        if not room.strip():\n            raise ValueError("room must be non-empty")\n'
_V_ROOM_API = (
    '    if not room.strip():\n        raise ValueError("room must be non-empty")\n'
)


def _store_room(validate: bool) -> str:
    return (
        "\n    def put_room(self, screening_id: str, room: str) -> Screening:\n"
        + (_V_ROOM_STORE if validate else "")
        + """        updated = replace(self._screenings[screening_id], room=room)
        self._screenings[screening_id] = updated
        append_line(self._log_path, f"room {screening_id} {room}")
        return updated
"""
    )


def _api_room(validate: bool) -> str:
    return (
        "\n\ndef assign_room(store: ScreeningStore, screening_id: str, room: str) -> Screening:\n"
        + (_V_ROOM_API if validate else "")
        + "    return store.put_room(screening_id, room)\n"
    )


def _gold2(state: str) -> str:
    # Different target file from checkpoint 1; films.py keeps its checkpoint-1 gold (api).
    api = state == "api"
    return _schedule(_store_room(not api), _api_room(api), use_replace=True)


_C2_SETUP = """import pytest

from festival.model import Screening
from festival.schedule import ScreeningStore, assign_room, book_screening


def _store(tmp_path):
    store = ScreeningStore(tmp_path / "schedule.log")
    book_screening(store, "Slow River", "Odeon 1", "18:30")
    book_screening(store, "Night Shift", "Odeon 2", "21:00")
    return store
"""

_C2_FUNCTIONAL = {
    "test_room_functional.py": _C2_SETUP
    + """

def test_assign_room_updates_and_returns_screening(tmp_path):
    store = _store(tmp_path)
    out = assign_room(store, "SC1", "Rialto")
    assert isinstance(out, Screening)
    assert out.room == "Rialto" and out.start == "18:30" and out.title == "Slow River"
    assert store.get("SC1").room == "Rialto"


def test_assign_room_appends_log_line(tmp_path):
    store = _store(tmp_path)
    assign_room(store, "SC2", "Rialto")
    lines = (tmp_path / "schedule.log").read_text().splitlines()
    assert lines[-1] == "room SC2 Rialto" and len(lines) == 3


def test_assign_room_rejects_blank(tmp_path):
    store = _store(tmp_path)
    with pytest.raises(ValueError):
        assign_room(store, "SC1", "  ")
    assert store.get("SC1").room == "Odeon 1"
    assert len((tmp_path / "schedule.log").read_text().splitlines()) == 2


def test_assign_room_unknown_id_raises_keyerror(tmp_path):
    store = _store(tmp_path)
    with pytest.raises(KeyError):
        assign_room(store, "SC9", "Rialto")
"""
}

_C2_REGRESSION = {
    "test_room_regression.py": """import pytest

from festival.films import FilmStore, register_film, set_runtime
from festival.schedule import ScreeningStore, book_screening


def test_book_and_get_unchanged(tmp_path):
    store = ScreeningStore(tmp_path / "schedule.log")
    s = book_screening(store, "Slow River", "Odeon 1", "18:30")
    assert s.screening_id == "SC1" and store.get("SC1") is s
    assert store.get("SC9") is None
    with pytest.raises(ValueError):
        book_screening(store, "Slow River", "", "18:30")
    with pytest.raises(ValueError):
        book_screening(store, "Slow River", "Odeon 1", "6pm")
    assert (tmp_path / "schedule.log").read_text() == "screening SC1 Slow River\\n"


def test_films_module_unchanged(tmp_path):
    store = FilmStore(tmp_path / "films.log")
    register_film(store, "Slow River", "A. Okafor")
    assert set_runtime(store, "Slow River", 96).minutes == 96
    with pytest.raises(ValueError):
        set_runtime(store, "Slow River", 0)
"""
}

_C2_CONTRACT = {
    "api": {
        "test_room_validation.py": _C2_SETUP
        + """

def test_public_assign_room_raises_on_blank(tmp_path):
    store = _store(tmp_path)
    with pytest.raises(ValueError):
        assign_room(store, "SC1", "")


def test_store_put_room_trusts_its_argument(tmp_path):
    store = _store(tmp_path)
    out = store.put_room("SC1", "")
    assert out.room == ""
    assert store.get("SC1").room == ""
"""
    },
    "storage": {
        "test_room_validation.py": _C2_SETUP
        + """

def test_store_put_room_raises_on_blank(tmp_path):
    store = _store(tmp_path)
    with pytest.raises(ValueError):
        store.put_room("SC1", "")
    assert store.get("SC1").room == "Odeon 1"


def test_public_assign_room_delegates_without_precheck(tmp_path, monkeypatch):
    store = _store(tmp_path)
    calls = []

    def spy(self, *args, **kwargs):
        calls.append(args + tuple(kwargs.values()))
        return self._screenings["SC1"]

    monkeypatch.setattr(ScreeningStore, "put_room", spy)
    assign_room(store, "SC1", "")
    assert len(calls) == 1 and "" in calls[0]
"""
    },
}

_C2_SUPPORT = {
    "test_room_errors.py": """import shutil

import pytest

from festival.schedule import ScreeningStore, assign_room, book_screening


def test_assign_room_lets_os_error_propagate_raw(tmp_path):
    folder = tmp_path / "logs"
    folder.mkdir()
    store = ScreeningStore(folder / "schedule.log")
    book_screening(store, "Slow River", "Odeon 1", "18:30")
    shutil.rmtree(folder)
    with pytest.raises(FileNotFoundError) as info:
        assign_room(store, "SC1", "Rialto")
    assert type(info.value) is FileNotFoundError


def test_assign_room_no_error_on_healthy_log(tmp_path):
    store = ScreeningStore(tmp_path / "schedule.log")
    book_screening(store, "Slow River", "Odeon 1", "18:30")
    assert assign_room(store, "SC1", "Rialto").room == "Rialto"
"""
}

_REQ2 = Request(
    text=(
        "Add `assign_room(store, screening_id, room)` to festival/schedule.py: it moves "
        "an existing screening to another room and returns the updated Screening, via a "
        "new store method `ScreeningStore.put_room(screening_id, room)` that swaps in the "
        "record and appends the audit line `room <screening_id> <room>`. A blank room "
        "(empty or whitespace only) is invalid and is rejected with ValueError before "
        "anything is stored or logged; an unknown screening id raises KeyError."
    ),
    target="festival/schedule.py",
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
        "I coordinate programming for a small documentary festival, four days, three "
        "venues, about sixty screenings. Every year the programme lives in a spreadsheet "
        "that three volunteers edit at once and every year something gets double-booked. "
        "I want a small Python package, `festival`, with two in-memory stores, one for the "
        "film catalogue and one for the screening schedule, each appending a one-line "
        "audit record to a plain text log whenever anything changes, so I can reconstruct "
        "who did what when the printed programme disagrees with the website, which "
        "happened four times last edition. The scripts "
        "are run by hand from a shared laptop. Nothing else: no web app, no database, no "
        "ticketing. The audit log I have in mind looks like:\n\n```\nfilm Slow River\n"
        "film Night Shift\nscreening SC1 Slow River\nscreening SC2 Night Shift\n"
        "```\n\nCan you write the README scope section so the volunteers know this is a "
        "bookkeeping tool and not a ticketing system? Someone asks for seat maps every "
        "single year, and every year I explain that we do not have the data for it.",
    ),
    Turn(
        "assistant",
        "Here is a scope section that draws the line clearly:\n\n```\n## Scope\nfestival "
        "keeps the film catalogue and the screening schedule for one edition in memory and "
        "appends an audit line to a text log on every change. It is driven by small "
        "scripts run from the programming laptop. It does not sell tickets, does not know "
        "about seats and does not talk to the website; the website exports come from the "
        "audit log.\n\n## Non-goals\n- ticketing or seat maps\n- concurrent editing\n- "
        "venue capacity checks\n```\n\nA usage block so the volunteers see the shape:\n\n"
        "```python\nfrom festival.films import FilmStore, register_film\nfrom "
        "festival.schedule import ScreeningStore, book_screening\n\nfilms = FilmStore("
        '"films.log")\nregister_film(films, "Slow River", "A. Okafor")\nsched = '
        'ScreeningStore("schedule.log")\nbook_screening(sched, "Slow River", "Odeon 1", '
        '"18:30")\n```\n\nThe shared `append_line` helper in `audit.py` is the only place '
        "that touches a file, so both stores log the same way, and the website export is "
        "a separate script that reads the two logs and never imports the stores.",
    ),
    Turn(
        "user",
        "Two stores rather than one: is that overkill? The argument for one store is one "
        "log file and one object to pass around. The argument for two is that the "
        "catalogue is finalised in June by the selection committee while the schedule "
        "changes right up to the opening night, and different volunteers own each. I also "
        "want to be able to hand the schedule store to the programme importer, which reads "
        "the venue's CSV and creates screenings in bulk, without giving it the catalogue. "
        "The CSV looks like:\n\n```\nscreening_id,title,room,start\n,Slow River,Odeon 1,"
        "18:30\n,Night Shift,Odeon 2,21:00\n,Harbour Light,Rialto,16:00\n```\n\nwith the "
        "id column left blank because the store mints ids. Last year the same sheet had "
        "eleven rows with hand-typed ids and two of them collided, which is how a Q&A "
        "ended up printed against the wrong film.",
    ),
    Turn(
        "assistant",
        "Two stores is the right split, and your reasons are the good ones: different "
        "lifecycles, different owners, and the importer needs only one of them. Two log "
        "files is a feature rather than a cost, because the catalogue log will be a few "
        "dozen lines and the schedule log will be hundreds, and nobody wants to grep one "
        "for the other. The stores can share nothing but the dataclasses in `model.py` and "
        "the audit helper; `Screening` refers to a film by title string rather than holding "
        "a `Film`, so the schedule store never needs the catalogue. Minting ids in "
        "`ScreeningStore.add` as `SC1`, `SC2`, ... in insertion order makes the importer "
        "trivial:\n\n```python\nfor row in csv.DictReader(fh):\n    book_screening(store, "
        'row["title"], row["room"], row["start"])\n```\n\nand the ids in the audit log '
        "match the ids on the printed programme, which is what the volunteers will search "
        "for. The importer stays about fifteen lines, and if the venue ever changes the CSV "
        "columns only the `DictReader` keys move. Hand-typed ids go away entirely, so the "
        "collision you saw last year cannot recur.",
    ),
    Turn(
        "user",
        "Screening ids as SC1, SC2 is fine. For start times I am storing the string "
        '"18:30" rather than a time object because that is what the venue sends and what '
        "gets printed; converting both ways felt like asking for an off-by-timezone bug. "
        "Here is the test I wrote for the format check, which is the only real rule on "
        "screenings so far:\n\n```python\nimport pytest\n\nfrom festival.schedule import "
        'ScreeningStore, book_screening\n\n\n@pytest.mark.parametrize("start", ["6pm", '
        '"18.30", "1830", "18:3"])\ndef test_book_rejects_bad_start(tmp_path, start):\n'
        '    store = ScreeningStore(tmp_path / "schedule.log")\n    with pytest.raises('
        'ValueError):\n        book_screening(store, "Slow River", "Odeon 1", start)\n'
        "```\n\nIs a string the wrong call here? The venue's own system prints times as "
        "`18h30` in its French export and `18:30` in the English one, and the volunteers "
        "have already pasted both into the sheet at least once.",
    ),
    Turn(
        "assistant",
        "A string is the right call for this tool. The value is never used for arithmetic, "
        "it is printed and compared, and the venue's own format is the source of truth. "
        "The `HH:MM` check in `book_screening` guards against the copy-paste variants your "
        'test lists, and if someone later needs ordering, `"18:30" < "21:00"` compares '
        "correctly as strings because the format is fixed-width, so the printed programme "
        "can be sorted with a plain `sorted(key=lambda s: s.start)`. The one thing a string "
        "does not give you is validation that 25:99 is impossible; if that ever bites, a "
        '`datetime.strptime(start, "%H:%M")` inside the same check is a one-line '
        "upgrade with no change to the stored value. I would leave the test as it is and "
        'add a positive case so a refactor cannot accidentally reject `"09:05"`:\n\n'
        "```python\ndef test_book_accepts_morning_slot(tmp_path):\n    store = "
        'ScreeningStore(tmp_path / "schedule.log")\n    s = book_screening(store, '
        '"Harbour Light", "Rialto", "09:05")\n    assert s.start == "09:05" and '
        's.screening_id == "SC1"\n```',
    ),
    Turn(
        "user",
        "Now the thing I actually want to settle before we add more operations. On the "
        "first run from the shared laptop, the log folder did not exist yet and this came "
        'out:\n\n```\n$ python -m festival.book "Slow River" "Odeon 1" 18:30\nTraceback '
        '(most recent call last):\n  File "/opt/festival/festival/book.py", line 16, in '
        '<module>\n    main()\n  File "/opt/festival/festival/book.py", line 12, in main\n'
        '    book_screening(store, args.title, args.room, args.start)\n  File "/opt/'
        'festival/festival/schedule.py", line 19, in add\n    append_line(self._log_path, '
        'f"screening {s.screening_id} {title}")\n  File "/opt/festival/festival/'
        'audit.py", line 7, in append_line\n    with Path(path).open("a") as fh:\n'
        "FileNotFoundError: [Errno 2] No such file or directory: '/srv/fest/2026/"
        "schedule.log'\n```\n\nA colleague wants me to catch that and raise a `FestivalError` "
        "instead. I am not convinced; the scripts are wrapped by a runner that already "
        "prints the errno and the path in red. What would you do? For what it is worth, "
        "the runner is about twenty lines: it parses `--log-dir`, builds the two stores, "
        "and calls the script's `main`, catching nothing.",
    ),
    Turn(
        "assistant",
        "For this tool I would leave it raw. The failure is a file-system failure, the "
        "runner already presents `OSError` well, and a package exception would only "
        "hide the errno behind a second layer that the volunteers then have to unwrap. "
        "Wrapping earns its keep when callers need to catch one type regardless of "
        "cause, or when the underlying error is something a script author would not "
        "recognise; neither applies to `FileNotFoundError` on a log path. The traceback "
        "you pasted names the exact file and the exact line, which is precisely what "
        "the person at the laptop needs. If you want a friendlier first-run experience, "
        "the runner can create the folder before it launches anything:\n\n```python\n"
        "Path(args.log_dir).mkdir(parents=True, exist_ok=True)\n```\n\nThat fixes the "
        "cause instead of dressing up the symptom, and the package stays a thin layer "
        "over plain file appends. Nothing in the package needs to change for that.",
    ),
    Turn(
        "user",
        "Agreed, written rule: the package does not wrap file errors. Any OSError from "
        "writing the audit log propagates raw and unchanged out of the public operations, "
        "and there is no package exception class. Every operation in both modules, "
        "existing and new.",
    ),
    Turn(
        "assistant",
        "Noted: file errors propagate raw. No operation in `films.py` or `schedule.py` "
        "catches `OSError` from `append_line`, no `FestivalError` exists, and a "
        "`FileNotFoundError` from a missing log folder reaches the caller as that type.",
    ),
    Turn(
        "user",
        "The other rule is where argument checks live. Validation goes in the public "
        "functions, `register_film`, `book_screening` and whatever we add next: they raise "
        "ValueError on bad input, and the store classes trust their arguments and never "
        "check anything.",
    ),
    Turn(
        "assistant",
        "Understood: validation belongs to the public functions in each module, which "
        "raise ValueError before touching the store; `FilmStore` and `ScreeningStore` "
        "methods do no checking, so a store method called directly with a bad value "
        "simply stores and logs it. New operations follow the same split.",
    ),
    Turn(
        "user",
        "The film test so far, for the record:\n\n```python\ndef test_register_rejects_"
        'blank_director(tmp_path):\n    store = FilmStore(tmp_path / "films.log")\n    '
        'with pytest.raises(ValueError):\n        register_film(store, "Slow River", '
        '" ")\n```',
    ),
    Turn(
        "assistant",
        "That pins the check to the public function. I would add one for the lookup "
        "contract too: `get` returns None, while actions on an unknown title or id raise "
        "KeyError.",
    ),
    Turn(
        "user",
        "Good. Running times are arriving from the committee, and the venue will want "
        "room changes on the schedule after that. I will paste the current files with each "
        "request.",
    ),
    Turn(
        "assistant",
        "Ready. I will return the complete module you name and leave the other untouched.",
    ),
]

_EVENT = (
    "One scoped exception to the validation rule, effective now: in the schedule module "
    "(festival/schedule.py) validation lives in ScreeningStore itself. New store methods "
    "there raise ValueError on bad input and the public functions in schedule.py just call "
    "through, with no pre-check of their own, because the programme importer calls the "
    "schedule store directly. book_screening keeps its check where it is, and films.py is "
    "unaffected: validation there stays in the public functions."
)


def build() -> Session:
    return Session(
        id="S27",
        project="festival",
        target_family="validation",
        support_family="error_surface",
        lifecycle="scope",
        files=_FILES,
        prefix=_PREFIX,
        states=("api", "storage"),
        state_at=("api", "storage"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10),
    )
