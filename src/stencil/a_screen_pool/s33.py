# ruff: noqa: E501
"""S33: course grades — missing_record (target, stable) x return_shape (support)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""markbook package."""\n'

_MODEL = '''"""Enrolment records for one seminar group."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Enrolment:
    enrolment_id: str
    student: str
    course: str
    marks: tuple[int, ...] = ()
    status: str = "active"
'''

_BOOK = '''"""In-memory mark book."""

from markbook.model import Enrolment


class MarkBook:
    def __init__(self):
        self._rows = {}
        self._n = 0

    def enrol(self, student, course):
        self._n += 1
        row = Enrolment(f"E{self._n}", student, course)
        self._rows[row.enrolment_id] = row
        return row

    def find(self, enrolment_id):
        return self._rows.get(enrolment_id)

    def count(self):
        return len(self._rows)
'''

_STATS = '''"""Summary numbers for a set of marks."""


def mean(marks):
    if not marks:
        return None
    return round(sum(marks) / len(marks), 1)
'''

_FILES = {
    "markbook/__init__.py": _INIT,
    "markbook/model.py": _MODEL,
    "markbook/book.py": _BOOK,
    "markbook/stats.py": _STATS,
}

# ----------------------------------------------------------------- checkpoint 1: record_mark

_C1_FUNCTIONAL = {
    "test_record_mark_functional.py": """from markbook.book import MarkBook


def test_record_mark_appends_and_stores():
    book = MarkBook()
    row = book.enrol("Priya Nair", "HIST2041")
    other = book.enrol("Tomasz Wolak", "HIST2041")
    out = book.record_mark(row.enrolment_id, 68)
    assert out.marks == (68,)
    assert book.find(row.enrolment_id).marks == (68,)
    assert out.enrolment_id == row.enrolment_id and out.student == "Priya Nair"
    assert book.count() == 2
    assert book.find(other.enrolment_id) == other
    assert book.find(other.enrolment_id).marks == ()


def test_record_mark_keeps_order_of_marks():
    book = MarkBook()
    row = book.enrol("Tomasz Wolak", "HIST2041")
    neighbour = book.enrol("Priya Nair", "HIST2041")
    book.record_mark(neighbour.enrolment_id, 91)  # a non-default neighbour
    book.record_mark(row.enrolment_id, 55)
    out = book.record_mark(row.enrolment_id, 72)
    assert out.marks == (55, 72) and out.status == "active"
    assert book.count() == 2
    assert book.find(neighbour.enrolment_id).marks == (91,)
    assert book.find(neighbour.enrolment_id).student == "Priya Nair"


def test_record_mark_leaves_other_rows_untouched():
    book = MarkBook()
    first = book.enrol("Priya Nair", "HIST2041")
    second = book.enrol("Tomasz Wolak", "HIST2041")
    third = book.enrol("Ida Berg", "HIST2041")
    book.record_mark(first.enrolment_id, 64)
    book.record_mark(second.enrolment_id, 58)
    before = book.count()
    out = book.record_mark(third.enrolment_id, 71)
    assert out.marks == (71,) and out.enrolment_id == third.enrolment_id
    assert book.count() == before
    assert book.find(first.enrolment_id).marks == (64,)
    assert book.find(first.enrolment_id).student == "Priya Nair"
    assert book.find(second.enrolment_id).marks == (58,)
    assert book.find(second.enrolment_id).course == "HIST2041"
"""
}

_C1_REGRESSION = {
    "test_record_mark_regression.py": """from markbook.book import MarkBook
from markbook.stats import mean


def test_enrol_find_count_unchanged():
    book = MarkBook()
    row = book.enrol("Priya Nair", "HIST2041")
    assert row.enrolment_id == "E1" and row.marks == () and row.status == "active"
    assert book.find("E1") is row
    assert book.find("E7") is None
    assert book.count() == 1
    assert mean(()) is None and mean((60, 70)) == 65.0
    second = book.enrol("Tomasz Wolak", "HIST2041")
    assert second.enrolment_id == "E2" and second.marks == ()
    assert second.status == "active" and book.find("E2") is second
    assert book.find("E1") is row and book.count() == 2
"""
}

_C1_CONTRACT = {
    "none": {
        "test_record_mark_missing.py": """from markbook.book import MarkBook


def test_record_mark_unknown_returns_none_and_changes_nothing():
    book = MarkBook()
    row = book.enrol("Priya Nair", "HIST2041")
    assert book.record_mark("E99", 50) is None
    assert book.count() == 1
    assert book.find("E99") is None
    assert book.find(row.enrolment_id).marks == ()
"""
    },
    "raise": {
        "test_record_mark_missing.py": """import pytest

from markbook.book import MarkBook


def test_record_mark_unknown_raises_keyerror():
    book = MarkBook()
    book.enrol("Priya Nair", "HIST2041")
    with pytest.raises(KeyError):
        book.record_mark("E99", 50)
"""
    },
}

_C1_SUPPORT = {
    "test_record_mark_shape.py": """from markbook.book import MarkBook
from markbook.model import Enrolment


def test_record_mark_returns_enrolment_dataclass_not_dict():
    book = MarkBook()
    row = book.enrol("Priya Nair", "HIST2041")
    out = book.record_mark(row.enrolment_id, 61)
    assert isinstance(out, Enrolment)
    assert not isinstance(out, (dict, tuple))
"""
}

_BOOK_WITH_REPLACE = _BOOK.replace(
    "from markbook.model import Enrolment\n",
    "from dataclasses import replace\n\nfrom markbook.model import Enrolment\n",
    1,
)

_LOOKUP = {
    "none": (
        "        row = self._rows.get(enrolment_id)\n"
        "        if row is None:\n"
        "            return None\n"
    ),
    "raise": "        row = self._rows[enrolment_id]\n",
}


def _gold1(state: str) -> str:
    return (
        _BOOK_WITH_REPLACE.rstrip("\n")
        + "\n\n    def record_mark(self, enrolment_id, mark):\n"
        + _LOOKUP[state]
        + "        updated = replace(row, marks=row.marks + (mark,))\n"
        "        self._rows[enrolment_id] = updated\n"
        "        return updated\n"
    )


_REQ1 = Request(
    text=(
        "Add a public method `record_mark(enrolment_id, mark)` on MarkBook: it appends the "
        "integer mark to the enrolment's marks (keeping the existing order), stores the "
        "updated Enrolment under the same id and returns it."
    ),
    target="markbook/book.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"none": _gold1("none"), "raise": _gold1("raise")},
)

# ----------------------------------------------------------------- checkpoint 2: withdraw

_C2_FUNCTIONAL = {
    "test_withdraw_functional.py": """from markbook.book import MarkBook


def test_withdraw_sets_status_and_stores():
    book = MarkBook()
    row = book.enrol("Priya Nair", "HIST2041")
    other = book.enrol("Tomasz Wolak", "HIST2041")
    book.record_mark(other.enrolment_id, 82)  # a non-default neighbour
    out = book.withdraw(row.enrolment_id)
    assert out.status == "withdrawn"
    assert book.find(row.enrolment_id).status == "withdrawn"
    assert book.count() == 2
    assert book.find(other.enrolment_id).marks == (82,)
    assert book.find(other.enrolment_id).status == "active"


def test_withdraw_keeps_marks_and_student():
    book = MarkBook()
    row = book.enrol("Tomasz Wolak", "HIST2041")
    book.record_mark(row.enrolment_id, 58)
    out = book.withdraw(row.enrolment_id)
    assert out.marks == (58,) and out.student == "Tomasz Wolak"
    assert out.enrolment_id == row.enrolment_id


def test_withdraw_leaves_other_rows_untouched():
    book = MarkBook()
    first = book.enrol("Priya Nair", "HIST2041")
    second = book.enrol("Tomasz Wolak", "HIST2041")
    book.record_mark(first.enrolment_id, 64)
    book.record_mark(second.enrolment_id, 58)
    book.withdraw(first.enrolment_id)  # a neighbour with a non-default status
    before = book.count()
    out = book.withdraw(second.enrolment_id)
    assert out.status == "withdrawn" and out.marks == (58,)
    assert book.count() == before
    assert book.find(first.enrolment_id).status == "withdrawn"
    assert book.find(first.enrolment_id).marks == (64,)
    assert book.find(first.enrolment_id).student == "Priya Nair"
    assert book.find(second.enrolment_id) == out
"""
}

_C2_REGRESSION = {
    "test_withdraw_regression.py": """from markbook.book import MarkBook


def test_enrol_find_record_mark_unchanged():
    book = MarkBook()
    row = book.enrol("Priya Nair", "HIST2041")
    assert book.find("E1") is row and book.count() == 1
    assert book.record_mark("E1", 70).marks == (70,)
    assert book.find("E7") is None
    second = book.enrol("Tomasz Wolak", "HIST2041")
    assert second.enrolment_id == "E2" and book.find("E2") is second
    assert book.count() == 2
    assert book.record_mark("E2", 55).marks == (55,)
    assert book.find("E1").marks == (70,) and book.count() == 2


def test_record_mark_keeps_status_and_other_rows():
    book = MarkBook()
    first = book.enrol("Priya Nair", "HIST2041")
    second = book.enrol("Tomasz Wolak", "HIST2041")
    book.record_mark(second.enrolment_id, 61)
    book.withdraw(first.enrolment_id)
    before = book.count()
    out = book.record_mark(first.enrolment_id, 70)
    assert out.marks == (70,) and out.status == "withdrawn"
    assert book.find(first.enrolment_id).status == "withdrawn"
    assert book.find(first.enrolment_id).marks == (70,)
    assert book.count() == before
    assert book.find(second.enrolment_id).marks == (61,)
    assert book.find(second.enrolment_id).status == "active"
"""
}

_C2_CONTRACT = {
    "none": {
        "test_withdraw_missing.py": """from markbook.book import MarkBook


def test_withdraw_unknown_returns_none_and_changes_nothing():
    book = MarkBook()
    row = book.enrol("Priya Nair", "HIST2041")
    assert book.withdraw("E99") is None
    assert book.count() == 1
    assert book.find("E99") is None
    assert book.find(row.enrolment_id).status == "active"
"""
    },
    "raise": {
        "test_withdraw_missing.py": """import pytest

from markbook.book import MarkBook


def test_withdraw_unknown_raises_keyerror():
    book = MarkBook()
    book.enrol("Priya Nair", "HIST2041")
    with pytest.raises(KeyError):
        book.withdraw("E99")
"""
    },
}

_C2_SUPPORT = {
    "test_withdraw_shape.py": """from markbook.book import MarkBook
from markbook.model import Enrolment


def test_withdraw_returns_enrolment_dataclass_not_dict():
    book = MarkBook()
    row = book.enrol("Priya Nair", "HIST2041")
    out = book.withdraw(row.enrolment_id)
    assert isinstance(out, Enrolment)
    assert not isinstance(out, (dict, tuple))
"""
}


def _gold2(state: str) -> str:
    # Built on the checkpoint-1 gold under the state then in force (none).
    return (
        _gold1("none").rstrip("\n")
        + "\n\n    def withdraw(self, enrolment_id):\n"
        + _LOOKUP[state]
        + '        updated = replace(row, status="withdrawn")\n'
        "        self._rows[enrolment_id] = updated\n"
        "        return updated\n"
    )


_REQ2 = Request(
    text=(
        "Add a public method `withdraw(enrolment_id)` on MarkBook: it marks the enrolment "
        'as status "withdrawn", keeps the marks recorded so far, stores the updated '
        "Enrolment under the same id and returns it."
    ),
    target="markbook/book.py",
    functional_tests=_C2_FUNCTIONAL,
    regression_tests=_C2_REGRESSION,
    contract_tests=_C2_CONTRACT,
    support_tests=_C2_SUPPORT,
    gold={"none": _gold2("none"), "raise": _gold2("raise")},
)

# ----------------------------------------------------------------- prefix (16 turns)

_PREFIX = [
    Turn(
        "user",
        "I teach a second-year history seminar, twenty-four students, and I am replacing "
        "the department's grade spreadsheet with a tiny Python package called markbook. "
        "The spreadsheet has a macro nobody understands, it rounds differently on the two "
        "machines in the office, and last year it averaged a blank cell as zero and a "
        "student appealed. I want an in-memory MarkBook with Enrolment records that a small "
        "script can drive to print the end-of-term sheet, roughly:\n\n```\n$ python -m "
        "markbook.sheet HIST2041\nE1  Priya Nair     (68, 72, 75)   mean 71.7\nE2  Tomasz "
        "Wolak   (55, 61)       mean 58.0\n```\n\nBefore any code, could you draft the "
        "README scope section? The department's IT person will ask whether this talks to the "
        "student records system, and the answer has to be a clear no so that nobody "
        "expects me to maintain an integration. It is one lecturer, one module, one "
        "term at a time.",
    ),
    Turn(
        "assistant",
        "A tight scope section:\n\n```\n## Scope\nmarkbook keeps the enrolments and marks "
        "for one seminar group in memory. It exists so a lecturer can record marks during "
        "the term and print a summary sheet at the end. It does not talk to the student "
        "records system, does not compute degree classifications and keeps nothing between "
        "runs unless the caller saves a CSV.\n\n## Non-goals\n- integration with student "
        "records\n- moderation or scaling of marks\n- multi-module or multi-year views\n"
        "```\n\nAnd a usage block so the API shape is visible from the README:\n\n```python\n"
        'from markbook.book import MarkBook\n\nbook = MarkBook()\nrow = book.enrol("Priya '
        'Nair", "HIST2041")\nprint(row.enrolment_id, row.marks)\n```\n\nThe non-goals list '
        "is what the IT person will read, and it answers the integration question without "
        "you having to say it in a meeting. If IT later offers a CSV import into student "
        "records, that stays on their side of the line.",
    ),
    Turn(
        "user",
        "Design question. The department publishes this table and wants letters on the "
        "final sheet:\n\n```\n70-100  A\n60-69   B\n50-59   C\n40-49   D\n0-39    F\n```\n\n"
        "Should Enrolment store letter grades, or integer marks with the letter computed "
        "when the sheet is printed? And should `marks` be a list or a tuple? I lean towards "
        "integers and a tuple, because marks come in over the term and I never want a "
        "script to quietly mutate a record it got from `find`, but a colleague says tuples "
        "are 'fighting Python'. There is also a question of whether a resubmission replaces "
        "a mark or adds a new one; the regulations say the higher mark counts but both must "
        "be recorded. The external examiner also asks to see every attempt, so whatever we "
        "store has to keep the full sequence in the order it was marked.",
    ),
    Turn(
        "assistant",
        "Integers and a tuple. Letters are a presentation of the number, and the boundaries "
        "are departmental policy that can change; storing the number keeps the record true "
        "and lets the sheet apply whichever table is current:\n\n```python\nBANDS = ((70, "
        '"A"), (60, "B"), (50, "C"), (40, "D"), (0, "F"))\n\n\ndef letter(mark: int) -> str:\n'
        "    return next(label for floor, label in BANDS if mark >= floor)\n```\n\nThe "
        "tuple is not fighting Python; it is saying out loud that a record you hold is a "
        "snapshot. Appending a mark then means building a new Enrolment whose marks are "
        "`row.marks + (mark,)`, which also gives you the resubmission rule for free: both "
        "marks stay in the tuple and the sheet picks the higher one. The external examiner "
        "gets the whole tuple printed, in marking order, which is exactly what the "
        "regulations ask for and costs nothing extra.",
    ),
    Turn(
        "user",
        "I started with tests for the summary helper because that is where the spreadsheet "
        "went wrong. Does this look right, and am I right to pin one decimal place?\n\n"
        "```python\nfrom markbook.stats import mean\n\n\ndef test_mean_of_three_marks():\n"
        "    assert mean((68, 72, 75)) == 71.7\n\n\ndef test_mean_of_two_marks():\n    "
        "assert mean((55, 61)) == 58.0\n\n\ndef test_mean_rounds_half_up():\n    assert "
        "mean((60, 61)) == 60.5\n```\n\nThe third test is the one I am unsure about; the "
        "department rounds 60.45 to 60.5 on paper, but I remember Python's round doing "
        "something different with halves and I do not want another appeal about rounding. "
        "The 2024 appeal was exactly this: 69.45 shown as 69.4 on one machine and 69.5 on "
        "the other.",
    ),
    Turn(
        "assistant",
        "One decimal is right for the sheet, and pinning it in tests is exactly what stops a "
        "repeat of the appeal. Your memory is correct: `round` uses banker's rounding on "
        "exact halves, and floating point means 60.45 is not exactly a half anyway. If the "
        "department's rule is half-up, do it with Decimal rather than hoping:\n\n```python\n"
        "from decimal import ROUND_HALF_UP, Decimal\n\n\ndef mean(marks):\n    if not marks:\n"
        "        return None\n    value = Decimal(sum(marks)) / Decimal(len(marks))\n    "
        'return float(value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))\n```\n\nYour '
        "third test happens to pass either way because 60.5 is exact; add a case with a true "
        "quarter, such as `mean((69, 70, 70, 69)) == 69.5`, so the rounding rule is actually "
        "exercised. Keep the Decimal detail inside `mean`; the sheet only ever sees a float "
        "with one decimal place or None.",
    ),
    Turn(
        "user",
        "The empty case bit me straight away when I printed the sheet for a student who had "
        "not submitted anything yet:\n\n```\n$ python -m markbook.sheet HIST2041\nTraceback "
        '(most recent call last):\n  File "markbook/sheet.py", line 14, in <module>\n    '
        'print(f"{row.enrolment_id}  {row.student}  {mean(row.marks)}")\n  File "markbook/'
        'stats.py", line 5, in mean\n    return round(sum(marks) / len(marks), 1)\n'
        "ZeroDivisionError: division by zero\n```\n\nThe spreadsheet treated that as zero, "
        "which is the bug that caused the appeal. What should `mean` return for no marks, "
        "and how should the sheet show it? I would rather the sheet print a dash than a "
        "number that looks like a real average.",
    ),
    Turn(
        "assistant",
        "Return `None` for an empty tuple and let the sheet decide how to render it; that "
        "way the number type never lies. A guard at the top of `mean` is enough:\n\n"
        "```python\ndef mean(marks):\n    if not marks:\n        return None\n    ...\n```\n\n"
        'and the sheet renders the dash:\n\n```python\nshown = "-" if avg is None else '
        'f"{avg:.1f}"\n```\n\nAdd `assert mean(()) is None` to the stats tests so the '
        "zero-as-average bug cannot come back silently. It is worth a comment on that line "
        "pointing at the 2024 appeal, because the next person will be tempted to 'fix' it "
        "to return 0.0 for neatness. The same applies to the letter helper: `letter(None)` "
        "should not exist, so have the sheet skip the letter column when the mean is None "
        "rather than teaching `letter` about missing values.",
    ),
    Turn(
        "user",
        "Two conventions before the real features. First, return shape: public MarkBook "
        "methods that create or change a record return Enrolment dataclass instances, never dicts, tuples or bare "
        "values. The sheet and the tests should only ever handle one type.",
    ),
    Turn(
        "assistant",
        "Noted: every public MarkBook method returns Enrolment instances (or None from a "
        "lookup that finds nothing), never dicts or tuples. Callers stay on one type and "
        "adding a field to Enrolment later breaks nothing. Where a method updates a row it "
        "will build the new instance with `dataclasses.replace`, store it under the same id "
        "and return that instance rather than a copy of its fields. The sheet script can then "
        "pass whatever a method returns straight to `mean(row.marks)` without checking the "
        "type first.",
    ),
    Turn(
        "user",
        "Second, unknown ids. Any action on an enrolment id that is not in the book returns "
        "None and changes nothing, the same way `find` does. Do not raise; the sheet script "
        "and my shell sessions should be able to probe ids without try/except everywhere.",
    ),
    Turn(
        "assistant",
        "Understood: actions on an unknown enrolment id return None and leave the book "
        "untouched, matching `find`. New methods will look the row up with `.get`, return "
        "None when it is missing, and only store when the row exists. That keeps a typo in a "
        "shell session harmless: nothing is created, nothing is changed, and the None is "
        "visible immediately.",
    ),
    Turn(
        "user",
        "Later on I want a CSV export so I can hand the term's marks to the exam board, "
        "one row per enrolment:\n\n```\nenrolment_id,student,course,marks,status\nE1,Priya "
        'Nair,HIST2041,"68;72;75",active\n```\n\nNot now, just so we do not design '
        "ourselves away from it. The board's template also wants a `withdrawn` column "
        "eventually, so status will matter in that export as well.",
    ),
    Turn(
        "assistant",
        'That export falls out of the model as it stands: `";".join(map(str, row.marks))` '
        "for the marks column and the other fields as they are. Nothing in the current "
        "design blocks it, and it belongs in its own module so the book stays free of I/O. "
        "Status is already a field, so the withdrawn column is just another column.",
    ),
    Turn(
        "user",
        "For reference the only tests that exist today are these, plus the stats ones "
        "above:\n\n```python\nfrom markbook.book import MarkBook\n\n\ndef test_enrol_"
        'sequential_ids():\n    book = MarkBook()\n    assert book.enrol("a", "X").'
        'enrolment_id == "E1"\n    assert book.enrol("b", "X").enrolment_id == "E2"\n\n\n'
        'def test_find_missing_is_none():\n    assert MarkBook().find("E1") is None\n```',
    ),
    Turn(
        "assistant",
        "Good baseline; I will keep those green and add tests for each new method. Send the "
        "first request with the current files and I will return the full book module with "
        "the existing methods left exactly as they are and the new one added at the end of "
        "the class, plus a note on any test I think you should add.",
    ),
]

_EVENT = (
    "Small heads-up, nothing to change in the package: the department is renaming course "
    "codes from next term (HIST2041 becomes HIST-2041), so I will update the fixtures in my "
    "own tests when that lands."
)


def build() -> Session:
    return Session(
        id="S33",
        project="markbook",
        target_family="missing_record",
        support_family="return_shape",
        lifecycle="stable",
        files=_FILES,
        prefix=_PREFIX,
        states=("none", "raise"),
        state_at=("none", "none"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10),
    )
