# ruff: noqa: E501
"""S17: classroom attendance — validation (target, stable) x return_shape (support, dataclass)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""rollcall package."""\n'

_MODEL = '''"""Attendance records."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Student:
    student_id: str
    name: str


@dataclass(frozen=True)
class Mark:
    student_id: str
    day: str
    status: str
    excuse: str | None = None
'''

_BOOK_HEAD = '''"""Attendance book: storage layer (AttendanceBook) and public functions."""
{extra_imports}
from rollcall.model import Mark, Student


class AttendanceBook:
    """Storage layer: keeps records, knows nothing about what is a valid value."""

    def __init__(self) -> None:
        self._students: dict[str, Student] = {{}}
        self._marks: dict[tuple[str, str], Mark] = {{}}
        self._next = 1

    def put_student(self, name: str) -> Student:
        student = Student(student_id=f"S{{self._next}}", name=name)
        self._next += 1
        self._students[student.student_id] = student
        return student

    def get_student(self, student_id: str) -> Student | None:
        return self._students.get(student_id)

    def student_count(self) -> int:
        return len(self._students)


def enroll(book: AttendanceBook, name: str) -> Student:
    """Public entry point: checks the input, then stores."""
    if not name.strip():
        raise ValueError("student name must not be blank")
    return book.put_student(name.strip())
'''

_BOOK = _BOOK_HEAD.format(extra_imports="")

_FILES = {
    "rollcall/__init__.py": _INIT,
    "rollcall/model.py": _MODEL,
    "rollcall/book.py": _BOOK,
}

# ----------------------------------------------------------------- checkpoint 1: record_mark

_C1_FUNCTIONAL = {
    "test_mark_functional.py": """import pytest

from rollcall.book import AttendanceBook, enroll, record_mark


def _book():
    b = AttendanceBook()
    s = enroll(b, "Aisha Khan")
    return b, s


def test_record_mark_stores_and_returns_mark():
    b, s = _book()
    out = record_mark(b, s.student_id, "2026-09-14", "present")
    assert out.student_id == s.student_id and out.day == "2026-09-14"
    assert out.status == "present" and out.excuse is None
    assert b.get_mark(s.student_id, "2026-09-14") == out


def test_record_mark_overwrites_same_day():
    b, s = _book()
    record_mark(b, s.student_id, "2026-09-14", "absent")
    out = record_mark(b, s.student_id, "2026-09-14", "late")
    assert out.status == "late"
    assert b.get_mark(s.student_id, "2026-09-14").status == "late"


@pytest.mark.parametrize("bad", ["sleeping", "", "Present", "PRESENT "])
def test_record_mark_rejects_unknown_status(bad):
    b, s = _book()
    with pytest.raises(ValueError):
        record_mark(b, s.student_id, "2026-09-14", bad)
    assert b.get_mark(s.student_id, "2026-09-14") is None


def test_record_mark_unknown_student_raises_keyerror():
    b = AttendanceBook()
    with pytest.raises(KeyError):
        record_mark(b, "S99", "2026-09-14", "present")
"""
}

_C1_REGRESSION = {
    "test_mark_regression.py": """import pytest

from rollcall.book import AttendanceBook, enroll


def test_enroll_validates_and_stores():
    b = AttendanceBook()
    s = enroll(b, "  Ben Ortiz ")
    assert s.student_id == "S1" and s.name == "Ben Ortiz"
    assert b.get_student("S1") is s and b.student_count() == 1
    with pytest.raises(ValueError):
        enroll(b, "   ")
    assert b.student_count() == 1


def test_put_student_stores_without_checking():
    b = AttendanceBook()
    s = b.put_student("")
    assert s.name == "" and b.get_student(s.student_id) is s
"""
}

_C1_CONTRACT = {
    "api": {
        "test_mark_validation.py": """import pytest

from rollcall.book import AttendanceBook, enroll, record_mark


def test_public_function_rejects_and_storage_does_not():
    b = AttendanceBook()
    s = enroll(b, "Aisha Khan")
    with pytest.raises(ValueError):
        record_mark(b, s.student_id, "2026-09-14", "sleeping")
    # the storage layer stores whatever it is given
    out = b.put_mark(s.student_id, "2026-09-14", "sleeping")
    assert out.status == "sleeping"
    assert b.get_mark(s.student_id, "2026-09-14").status == "sleeping"
"""
    },
    "storage": {
        "test_mark_validation.py": """import pytest

from rollcall.book import AttendanceBook, enroll, record_mark


def test_storage_rejects_directly():
    b = AttendanceBook()
    s = enroll(b, "Aisha Khan")
    with pytest.raises(ValueError):
        b.put_mark(s.student_id, "2026-09-14", "sleeping")
    assert b.get_mark(s.student_id, "2026-09-14") is None


def test_public_function_passes_invalid_value_through(monkeypatch):
    b = AttendanceBook()
    s = enroll(b, "Aisha Khan")
    seen = []

    def spy(self, student_id, day, status):
        seen.append((student_id, day, status))
        return None

    monkeypatch.setattr(AttendanceBook, "put_mark", spy)
    record_mark(b, s.student_id, "2026-09-14", "sleeping")
    assert seen == [(s.student_id, "2026-09-14", "sleeping")]
"""
    },
}

_C1_SUPPORT = {
    "test_mark_shape.py": """from dataclasses import is_dataclass

from rollcall.book import AttendanceBook, enroll, record_mark
from rollcall.model import Mark


def test_record_mark_returns_mark_dataclass_not_dict():
    b = AttendanceBook()
    s = enroll(b, "Aisha Khan")
    out = record_mark(b, s.student_id, "2026-09-14", "present")
    assert isinstance(out, Mark) and is_dataclass(out)
    assert not isinstance(out, dict)
"""
}

_STORAGE1_API = """
    def put_mark(self, student_id: str, day: str, status: str) -> Mark:
        if student_id not in self._students:
            raise KeyError(student_id)
        mark = Mark(student_id=student_id, day=day, status=status)
        self._marks[(student_id, day)] = mark
        return mark

    def get_mark(self, student_id: str, day: str) -> Mark | None:
        return self._marks.get((student_id, day))
"""

_STORAGE1_STORAGE = """
    def put_mark(self, student_id: str, day: str, status: str) -> Mark:
        if status not in STATUSES:
            raise ValueError(f"unknown attendance status: {status!r}")
        if student_id not in self._students:
            raise KeyError(student_id)
        mark = Mark(student_id=student_id, day=day, status=status)
        self._marks[(student_id, day)] = mark
        return mark

    def get_mark(self, student_id: str, day: str) -> Mark | None:
        return self._marks.get((student_id, day))
"""

_PUBLIC1_API = '''

def record_mark(book: AttendanceBook, student_id: str, day: str, status: str) -> Mark:
    """Public entry point: checks the status, then stores."""
    if status not in STATUSES:
        raise ValueError(f"unknown attendance status: {status!r}")
    return book.put_mark(student_id, day, status)
'''

_PUBLIC1_STORAGE = """

def record_mark(book: AttendanceBook, student_id: str, day: str, status: str) -> Mark:
    return book.put_mark(student_id, day, status)
"""


def _assemble(storage_methods: str, public_functions: str) -> str:
    head = _BOOK_HEAD.format(extra_imports="").replace(
        "from rollcall.model import Mark, Student\n",
        'from rollcall.model import Mark, Student\n\nSTATUSES = ("present", "absent", "late")\n',
        1,
    )
    before, after = head.split("\n\ndef enroll(", 1)
    return (
        before.rstrip("\n")
        + "\n"
        + storage_methods
        + "\n\ndef enroll("
        + after.rstrip("\n")
        + "\n"
        + public_functions
    )


_GOLD1 = {
    "api": _assemble(_STORAGE1_API, _PUBLIC1_API),
    "storage": _assemble(_STORAGE1_STORAGE, _PUBLIC1_STORAGE),
}

_REQ1 = Request(
    text=(
        "Add attendance marks. On AttendanceBook add `put_mark(student_id, day, status)` "
        "that stores a Mark for that student and ISO day (overwriting any earlier mark "
        "for the same day) and returns it, raising KeyError for an unknown student, plus "
        "`get_mark(student_id, day)` returning the stored Mark or None. Add a public "
        "function `record_mark(book, student_id, day, status)` that records a mark. The "
        'only valid statuses are exactly "present", "absent" and "late"; anything else '
        "is invalid input and must raise ValueError without storing anything."
    ),
    target="rollcall/book.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold=_GOLD1,
)

# ----------------------------------------------------------------- checkpoint 2: excuse_absence

_C2_FUNCTIONAL = {
    "test_excuse_functional.py": """import pytest

from rollcall.book import AttendanceBook, enroll, excuse_absence, record_mark


def _book():
    b = AttendanceBook()
    s = enroll(b, "Aisha Khan")
    record_mark(b, s.student_id, "2026-09-14", "absent")
    return b, s


def test_excuse_sets_reason_and_stores():
    b, s = _book()
    out = excuse_absence(b, s.student_id, "2026-09-14", "dentist")
    assert out.excuse == "dentist" and out.status == "absent"
    assert b.get_mark(s.student_id, "2026-09-14") == out


@pytest.mark.parametrize("bad", ["", "   ", "\\t"])
def test_excuse_rejects_blank_reason(bad):
    b, s = _book()
    with pytest.raises(ValueError):
        excuse_absence(b, s.student_id, "2026-09-14", bad)
    assert b.get_mark(s.student_id, "2026-09-14").excuse is None


def test_excuse_strips_reason():
    b, s = _book()
    out = excuse_absence(b, s.student_id, "2026-09-14", "  family event ")
    assert out.excuse == "family event"


def test_excuse_without_mark_raises_keyerror():
    b, s = _book()
    with pytest.raises(KeyError):
        excuse_absence(b, s.student_id, "2026-09-15", "dentist")
"""
}

_C2_REGRESSION = {
    "test_excuse_regression.py": """import pytest

from rollcall.book import AttendanceBook, enroll, record_mark


def test_enroll_and_record_mark_unchanged():
    b = AttendanceBook()
    s = enroll(b, "Ben Ortiz")
    assert b.student_count() == 1
    with pytest.raises(ValueError):
        enroll(b, " ")
    m = record_mark(b, s.student_id, "2026-09-14", "late")
    assert b.get_mark(s.student_id, "2026-09-14") == m and m.excuse is None
    assert b.get_student("nope") is None
    with pytest.raises(ValueError):
        record_mark(b, s.student_id, "2026-09-14", "sleeping")
    assert b.get_mark(s.student_id, "2026-09-14").status == "late"
"""
}

_C2_CONTRACT = {
    "api": {
        "test_excuse_validation.py": """import pytest

from rollcall.book import AttendanceBook, enroll, excuse_absence, record_mark


def test_public_function_rejects_and_storage_does_not():
    b = AttendanceBook()
    s = enroll(b, "Aisha Khan")
    record_mark(b, s.student_id, "2026-09-14", "absent")
    with pytest.raises(ValueError):
        excuse_absence(b, s.student_id, "2026-09-14", "   ")
    # the storage layer stores whatever it is given
    out = b.put_excuse(s.student_id, "2026-09-14", "   ")
    assert out.excuse == "   "
    assert b.get_mark(s.student_id, "2026-09-14").excuse == "   "
"""
    },
    "storage": {
        "test_excuse_validation.py": """import pytest

from rollcall.book import AttendanceBook, enroll, excuse_absence, record_mark


def _book():
    b = AttendanceBook()
    s = enroll(b, "Aisha Khan")
    record_mark(b, s.student_id, "2026-09-14", "absent")
    return b, s


def test_storage_rejects_directly():
    b, s = _book()
    with pytest.raises(ValueError):
        b.put_excuse(s.student_id, "2026-09-14", "   ")
    assert b.get_mark(s.student_id, "2026-09-14").excuse is None


def test_public_function_passes_invalid_value_through(monkeypatch):
    b, s = _book()
    seen = []

    def spy(self, student_id, day, reason):
        seen.append((student_id, day, reason))
        return None

    monkeypatch.setattr(AttendanceBook, "put_excuse", spy)
    excuse_absence(b, s.student_id, "2026-09-14", "   ")
    assert seen == [(s.student_id, "2026-09-14", "   ")]
"""
    },
}

_C2_SUPPORT = {
    "test_excuse_shape.py": """from dataclasses import is_dataclass

from rollcall.book import AttendanceBook, enroll, excuse_absence, record_mark
from rollcall.model import Mark


def test_excuse_returns_mark_dataclass_not_dict():
    b = AttendanceBook()
    s = enroll(b, "Aisha Khan")
    record_mark(b, s.student_id, "2026-09-14", "absent")
    out = excuse_absence(b, s.student_id, "2026-09-14", "dentist")
    assert isinstance(out, Mark) and is_dataclass(out)
    assert not isinstance(out, dict)
"""
}

_STORAGE2_API = """
    def put_excuse(self, student_id: str, day: str, reason: str) -> Mark:
        mark = self._marks[(student_id, day)]
        excused = replace(mark, excuse=reason)
        self._marks[(student_id, day)] = excused
        return excused
"""

_STORAGE2_STORAGE = """
    def put_excuse(self, student_id: str, day: str, reason: str) -> Mark:
        if not reason.strip():
            raise ValueError("excuse reason must not be blank")
        mark = self._marks[(student_id, day)]
        excused = replace(mark, excuse=reason.strip())
        self._marks[(student_id, day)] = excused
        return excused
"""

_PUBLIC2_API = '''

def excuse_absence(book: AttendanceBook, student_id: str, day: str, reason: str) -> Mark:
    """Public entry point: checks the reason, then stores."""
    if not reason.strip():
        raise ValueError("excuse reason must not be blank")
    return book.put_excuse(student_id, day, reason.strip())
'''

_PUBLIC2_STORAGE = """

def excuse_absence(book: AttendanceBook, student_id: str, day: str, reason: str) -> Mark:
    return book.put_excuse(student_id, day, reason)
"""


def _gold2(state: str) -> str:
    # Built on the checkpoint-1 gold under the state then in force (api).
    base = _GOLD1["api"]
    storage = _STORAGE2_API if state == "api" else _STORAGE2_STORAGE
    public = _PUBLIC2_API if state == "api" else _PUBLIC2_STORAGE
    before, after = base.split("\n\ndef enroll(", 1)
    text = (
        before.rstrip("\n")
        + "\n"
        + storage
        + "\n\ndef enroll("
        + after.rstrip("\n")
        + "\n"
        + public
    )
    return text.replace(
        "from rollcall.model import Mark, Student\n",
        "from dataclasses import replace\n\nfrom rollcall.model import Mark, Student\n",
        1,
    )


_REQ2 = Request(
    text=(
        "Add excuses for absences. On AttendanceBook add `put_excuse(student_id, day, "
        "reason)` that stores the existing Mark for that student and day with its excuse "
        "set to the reason and returns the updated Mark, raising KeyError when there is "
        "no mark for that day. Add a public function `excuse_absence(book, student_id, "
        "day, reason)` that records the excuse with surrounding whitespace stripped. A "
        "blank or whitespace-only reason is invalid input and must raise ValueError "
        "without changing the mark."
    ),
    target="rollcall/book.py",
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
        "I teach a year-five class and our school's attendance system is a paper "
        "register that the office retypes every Friday. I want a small package, "
        "rollcall, that I can drive from a couple of scripts on the classroom laptop: "
        "enrol the thirty kids at the start of term, take the register each morning, "
        "and print a weekly summary that the office can paste in. No database and no "
        "network; the scripts load and save a JSON file. Here is my README draft:\n\n"
        "```\n# rollcall\n\nIn-memory attendance for one class. Students get ids S1, S2, "
        "... when enrolled. A mark is one student on one ISO day with a status. The "
        "package does no I/O; `register.py` and `summary.py` load and save "
        "`attendance.json`.\n```\n\nThe part I am least sure about is structure. I have "
        "one module, book.py, with an AttendanceBook class that holds the dicts and a "
        "few module-level functions (enroll so far) that the scripts call. Is mixing a "
        "class and functions in one file a smell, or is it fine at this size?",
    ),
    Turn(
        "assistant",
        "At this size it is fine, and the split you have is a useful one as long as it "
        "is deliberate: the class is the storage layer (it knows how to keep records "
        "and nothing about what makes a record sensible) and the module-level functions "
        "are the public entry points the scripts call. Write that down in the two "
        "docstrings so a reader knows which layer they are in:\n\n```python\nclass "
        'AttendanceBook:\n    """Storage layer: keeps records, knows nothing about what '
        'is a valid value."""\n\n\ndef enroll(book: AttendanceBook, name: str) -> '
        'Student:\n    """Public entry point: checks the input, then stores."""\n```\n\n'
        "If the file grows past a screen or two, the class moves to `storage.py` and "
        "the functions stay in `book.py`, and nothing the scripts import changes. I "
        "would also add a non-goals list to the README (no timetable, no parent "
        "contact details, no multi-class support) because those are the three things "
        "colleagues will ask for first. A two-line usage block (`book = "
        'AttendanceBook()` then `enroll(book, "Aisha Khan")`) helps the office too.',
    ),
    Turn(
        "user",
        "Good, I have added those docstrings. Here is the model, two frozen "
        "dataclasses:\n\n```python\n@dataclass(frozen=True)\nclass Student:\n    "
        "student_id: str\n    name: str\n\n\n@dataclass(frozen=True)\nclass Mark:\n    "
        "student_id: str\n    day: str\n    status: str\n    excuse: str | None = None\n"
        "```\n\nThe excuse field is there because the office wants a reason recorded "
        "against an absence, and I would rather have it on the Mark than in a separate "
        "table. Days are ISO strings like 2026-09-14 because that is what the JSON file "
        "holds and comparing strings sorts correctly. Status will be one of present, "
        "absent or late, and the office is strict that those are the only three words "
        "they accept. Does keying marks on (student_id, day) make sense, or should a "
        "student hold a list of marks? The JSON file the office wants is flat, one "
        'object per mark:\n\n```json\n{"student_id": "S1", "day": "2026-09-14", '
        '"status": "absent", "excuse": "dentist"}\n```',
    ),
    Turn(
        "assistant",
        "Keying on `(student_id, day)` is the right shape: a mark is naturally unique "
        "per student per day, overwriting is free (taking the register twice on the "
        "same morning should replace, not duplicate), and the weekly summary is a "
        "single pass over `self._marks.values()` filtered by day range. A list per "
        "student would force you to search it on every correction. Keep the excuse on "
        "the Mark; it is a property of that day's absence and nothing else. The storage "
        "methods for marks will look just like the student ones:\n\n```python\ndef "
        "get_mark(self, student_id: str, day: str) -> Mark | None:\n    return "
        "self._marks.get((student_id, day))\n```\n\nand the `excuse` default of None "
        "lets `dataclasses.replace(mark, excuse=reason)` produce the excused record "
        "without touching the status, which keeps present and late marks from ever "
        "carrying an excuse by accident. The flat JSON you showed is exactly "
        "`[asdict(m) for m in book.marks()]`, so the dict-of-marks structure needs no "
        "reshaping at all on the way out, and loading is the reverse comprehension.",
    ),
    Turn(
        "user",
        "Here are the tests I have today, all green:\n\n```python\nimport pytest\n\nfrom "
        "rollcall.book import AttendanceBook, enroll\n\n\ndef "
        "test_enroll_assigns_sequential_ids():\n    b = AttendanceBook()\n    assert "
        'enroll(b, "Aisha Khan").student_id == "S1"\n    assert enroll(b, "Ben Ortiz").'
        'student_id == "S2"\n\n\ndef test_enroll_strips_name():\n    b = AttendanceBook()\n'
        '    assert enroll(b, "  Ben Ortiz ").name == "Ben Ortiz"\n\n\ndef '
        "test_enroll_rejects_blank_name():\n    b = AttendanceBook()\n    with "
        'pytest.raises(ValueError):\n        enroll(b, "   ")\n    assert b.student_count()'
        " == 0\n\n\ndef test_get_student_missing_returns_none():\n    assert "
        'AttendanceBook().get_student("S9") is None\n```\n\nOne of the parents is a '
        "developer and asked why `put_student` does not reject a blank name itself. I "
        "did not have a crisp answer beyond 'that is what enroll is for'. She pointed "
        "at this, which she thinks proves the store is 'unsafe':\n\n```\n>>> book."
        "put_student(\"\")\nStudent(student_id='S1', name='')\n```",
    ),
    Turn(
        "assistant",
        "The crisp answer is that you have chosen where validation lives and it is the "
        "public entry point. `enroll` is the door the scripts come through; it checks "
        "the input and raises ValueError with a message a teacher can read, and "
        "`put_student` is a dumb store that writes what it is given. That split means "
        "the storage class can be loaded from JSON without re-validating thirty names, "
        "and it means there is exactly one place to look for the rules. It is a choice, "
        "not a law: the other design puts the checks in the storage methods and lets "
        "the public functions pass values straight through. Either is defensible; what "
        "matters is that the project does one of them consistently and that a test "
        "pins it:\n\n```python\ndef test_put_student_stores_without_checking():\n    b = "
        'AttendanceBook()\n    s = b.put_student("")\n    assert s.name == ""\n```\n\n'
        "That test documents the layering so the next person does not 'fix' it by "
        "adding a second check in the store.",
    ),
    Turn(
        "user",
        "That is the answer I will give. One more question about the public functions: "
        "what should they hand back? `enroll` returns the Student dataclass today, and "
        "`register.py` then prints `student.name`. Another teacher who saw it asked why "
        "not return a plain dict so it can go straight into json.dump. Here is the bit "
        "of `register.py` that made her ask:\n\n```python\nfor name in names:\n    "
        'student = enroll(book, name)\n    rows.append({"student_id": '
        'student.student_id, "name": student.name})\njson.dump(rows, fh, indent=2)\n'
        "```\n\nIt does feel like a lot of ceremony to get from a Student to a dict and "
        "back again, so I want to decide this once. The same question will come up for "
        "marks, where the summary script will want to count statuses, and for anything "
        "else we add, so whatever we pick should be the rule for every public function "
        "rather than a per-function judgement call. I would also like the answer to "
        "hold for the storage methods, so that `put_student` and its future siblings "
        "hand back the same kind of object the public functions do.",
    ),
    Turn(
        "assistant",
        "Return the dataclass. The conversion ceremony is one line, "
        "`dataclasses.asdict(student)`, and it belongs in the script that owns the JSON "
        "file, not in the library. What you get in exchange is that every public "
        "function returns a typed record: field access is checked by your editor, a "
        "typo like `student.nmae` fails loudly instead of returning None from "
        '`.get()`, equality works in tests (`assert book.get_student("S1") == '
        "student`), and adding a field later does not break callers. Dicts also invite "
        "callers to mutate the record in place, which is the bug frozen dataclasses "
        "exist to prevent. The script becomes:\n\n```python\nrows = [asdict(enroll(book, "
        "name)) for name in names]\njson.dump(rows, fh, indent=2)\n```\n\nwhich is "
        "shorter than what you have now, so the ceremony argument goes the other way. "
        "For the summary script, `Counter(m.status for m in marks)` works on records "
        "just as well as on dicts, so nothing downstream gets harder.",
    ),
    Turn(
        "user",
        "Settled then: public functions in rollcall return the model dataclass "
        "instances (Student, Mark), never dicts or tuples, and the scripts convert with "
        "asdict when they need JSON. That applies to everything we add from here.",
    ),
    Turn(
        "assistant",
        "Noted: every public function returns Student or Mark instances (or None from "
        "lookups), never a dict or tuple, and JSON conversion stays in the scripts with "
        "`asdict`. That keeps callers on one type per record, and the storage methods "
        "return the same dataclasses so the two layers agree.",
    ),
    Turn(
        "user",
        "And let's keep the validation layering exactly as it is today: input checks "
        "live in the public functions, which raise ValueError; the AttendanceBook "
        "storage methods store what they are given and never raise ValueError on "
        "values. New features follow the same split.",
    ),
    Turn(
        "assistant",
        "Understood: validation stays in the public entry points, raising ValueError "
        "with a readable message, and the AttendanceBook methods remain plain stores "
        "that accept whatever they are handed. New storage methods get no value checks; "
        "new public functions do the checking before calling the store. The "
        "`put_student` test you have pins that split, and I will keep it green.",
    ),
    Turn(
        "user",
        "For later: the weekly summary. The office wants one line per student with "
        "counts, like `S3 Aisha Khan present 4 absent 1 late 0`. I imagine:\n\n```python\n"
        "def summary(book, days):\n    for student in book.students():\n        counts = "
        "Counter(m.status for m in book.marks_for(student.student_id) if m.day in days)\n"
        "```\n\nwhere `students()` and `marks_for()` do not exist yet.",
    ),
    Turn(
        "assistant",
        "That will drop in once marks exist: `students()` is `list(self._students."
        "values())` and `marks_for` is a comprehension over `self._marks.values()` "
        "filtered on student id. Both are lookups, so they return records or lists and "
        "never raise. Both will return dataclass instances like everything else.",
    ),
    Turn(
        "user",
        "Right, let's get marks in before Monday's register. I will paste the current "
        "files with each request so you see the true state rather than my memory of it.",
    ),
    Turn(
        "assistant",
        "Ready. Send the request with the files and I will return the complete book "
        "module.",
    ),
]

_EVENT = (
    "Small scheduling note before the next piece: the school has moved the register to "
    "8:50 instead of 9:00 from next week, so `register.py` will run a bit earlier. "
    "Nothing changes for the package itself."
)


def build() -> Session:
    return Session(
        id="S17",
        project="rollcall",
        target_family="validation",
        support_family="return_shape",
        lifecycle="stable",
        files=_FILES,
        prefix=_PREFIX,
        states=("api", "storage"),
        state_at=("api", "api"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10),
    )
