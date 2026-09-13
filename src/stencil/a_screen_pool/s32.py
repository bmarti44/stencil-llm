# ruff: noqa: E501
"""S32: gallery loans — validation (target, reinstatement) x logging (support)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""gallerylend package."""\n'

_MODEL = '''"""Loan records for artworks lent to other institutions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Loan:
    loan_id: str
    artwork: str
    borrower: str
    days: int
    status: str = "out"
    condition: str = ""
'''

_LOANS = '''"""Loan register (storage layer) and the public loan operations."""

import logging

from gallerylend.model import Loan

log = logging.getLogger(__name__)
LONG_LOAN_DAYS = 180


class LoanRegister:
    def __init__(self):
        self._loans = {}
        self._n = 0

    def insert(self, artwork, borrower, days):
        self._n += 1
        loan = Loan(f"L{self._n}", artwork, borrower, days)
        self._loans[loan.loan_id] = loan
        return loan

    def get(self, loan_id):
        return self._loans.get(loan_id)


def lend(register, artwork, borrower, days):
    if days <= 0:
        raise ValueError(f"days must be positive, got {days}")
    if days > LONG_LOAN_DAYS:
        log.warning("long loan: %s to %s for %d days", artwork, borrower, days)
    return register.insert(artwork, borrower, days)
'''

_FILES = {
    "gallerylend/__init__.py": _INIT,
    "gallerylend/model.py": _MODEL,
    "gallerylend/loans.py": _LOANS,
}

# ----------------------------------------------------------------- checkpoint 1: extend

_C1_FUNCTIONAL = {
    "test_extend_functional.py": """import pytest

from gallerylend.loans import LoanRegister, extend, lend


def test_extend_adds_days_and_stores():
    reg = LoanRegister()
    loan = lend(reg, "Nocturne in Grey", "Kunsthalle Bremen", 30)
    out = extend(reg, loan.loan_id, 14)
    assert out.days == 44
    assert reg.get(loan.loan_id).days == 44
    assert out.loan_id == loan.loan_id and out.artwork == "Nocturne in Grey"


def test_extend_keeps_status_and_borrower():
    reg = LoanRegister()
    loan = lend(reg, "Study of Hands", "Ateneum", 60)
    out = extend(reg, loan.loan_id, 7)
    assert out.status == "out" and out.borrower == "Ateneum"


def test_extend_rejects_non_positive_days():
    reg = LoanRegister()
    loan = lend(reg, "Nocturne in Grey", "Kunsthalle Bremen", 30)
    with pytest.raises(ValueError):
        extend(reg, loan.loan_id, 0)
    with pytest.raises(ValueError):
        extend(reg, loan.loan_id, -5)
    assert reg.get(loan.loan_id).days == 30


def test_extend_keeps_the_other_loan_in_the_register():
    reg = LoanRegister()
    keep = lend(reg, "Harbour at Dusk", "Rijksmuseum", 90)
    loan = lend(reg, "Nocturne in Grey", "Kunsthalle Bremen", 30)
    out = extend(reg, loan.loan_id, 14)
    assert out.days == 44 and reg.get(loan.loan_id).days == 44
    kept = reg.get(keep.loan_id)
    assert kept is not None, "extending one loan dropped the other"
    assert kept == keep
    assert kept.days == 90 and kept.artwork == "Harbour at Dusk"
    assert kept.borrower == "Rijksmuseum"
    assert kept.status == "out" and kept.condition == ""
"""
}

_C1_REGRESSION = {
    "test_extend_regression.py": """import pytest

from gallerylend.loans import LoanRegister, lend


def test_lend_get_unchanged():
    reg = LoanRegister()
    loan = lend(reg, "Harbour at Dusk", "Rijksmuseum", 90)
    assert loan.loan_id == "L1" and loan.status == "out"
    assert reg.get("L1") is loan
    assert reg.get("L9") is None
    second = lend(reg, "Study of Hands", "Ateneum", 60)
    assert second.loan_id == "L2" and second.status == "out"
    assert reg.get("L2") is second
    assert reg.get("L1") is loan, "lending again dropped the first loan"
    assert reg.get("L1").days == 90 and reg.get("L1").condition == ""


def test_lend_rejects_non_positive_days():
    with pytest.raises(ValueError):
        lend(LoanRegister(), "x", "y", 0)
"""
}

_C1_CONTRACT = {
    "api": {
        "test_extend_validation.py": """import pytest

from gallerylend.loans import LoanRegister, extend, lend


def test_public_extend_validates_and_register_trusts_its_arguments():
    reg = LoanRegister()
    loan = lend(reg, "Nocturne in Grey", "Kunsthalle Bremen", 30)
    with pytest.raises(ValueError):
        extend(reg, loan.loan_id, 0)
    # the storage layer performs no check: called directly it accepts the same value
    out = reg.extend(loan.loan_id, 0)
    assert out.days == 30
"""
    },
    "storage": {
        "test_extend_validation.py": """import pytest

from gallerylend.loans import LoanRegister, extend, lend


def test_register_extend_validates_and_public_passes_through(monkeypatch):
    reg = LoanRegister()
    loan = lend(reg, "Nocturne in Grey", "Kunsthalle Bremen", 30)
    with pytest.raises(ValueError):
        reg.extend(loan.loan_id, 0)
    calls = []

    def spy(loan_id, extra_days):
        calls.append((loan_id, extra_days))
        raise ValueError("rejected by the register")

    monkeypatch.setattr(reg, "extend", spy)
    with pytest.raises(ValueError):
        extend(reg, loan.loan_id, -3)
    assert calls == [(loan.loan_id, -3)]
"""
    },
}

_C1_SUPPORT = {
    "test_extend_logging.py": """import logging

from gallerylend.loans import LoanRegister, extend, lend


def test_extend_past_long_limit_warns_exactly_once(caplog):
    reg = LoanRegister()
    loan = lend(reg, "Nocturne in Grey", "Kunsthalle Bremen", 100)
    caplog.set_level(logging.DEBUG, logger="gallerylend.loans")
    caplog.clear()
    extend(reg, loan.loan_id, 100)
    assert [r.levelno for r in caplog.records] == [logging.WARNING]


def test_extend_within_limit_logs_nothing(caplog):
    reg = LoanRegister()
    loan = lend(reg, "Study of Hands", "Ateneum", 30)
    caplog.set_level(logging.DEBUG, logger="gallerylend.loans")
    caplog.clear()
    extend(reg, loan.loan_id, 10)
    assert caplog.records == []
"""
}

_LOANS_WITH_REPLACE = _LOANS.replace(
    "import logging\n\nfrom gallerylend.model import Loan\n",
    "import logging\nfrom dataclasses import replace\n\nfrom gallerylend.model import Loan\n",
    1,
)

_REGISTER_EXTEND_TRUSTING = """
    def extend(self, loan_id, extra_days):
        loan = self._loans[loan_id]
        updated = replace(loan, days=loan.days + extra_days)
        self._loans[loan_id] = updated
        return updated
"""

_REGISTER_EXTEND_VALIDATING = """
    def extend(self, loan_id, extra_days):
        if extra_days <= 0:
            raise ValueError(f"extra_days must be positive, got {extra_days}")
        loan = self._loans[loan_id]
        updated = replace(loan, days=loan.days + extra_days)
        self._loans[loan_id] = updated
        return updated
"""

_PUBLIC_EXTEND_VALIDATING = """

def extend(register, loan_id, extra_days):
    if extra_days <= 0:
        raise ValueError(f"extra_days must be positive, got {extra_days}")
    loan = register.extend(loan_id, extra_days)
    if loan.days > LONG_LOAN_DAYS:
        log.warning("long loan: %s now out for %d days", loan.loan_id, loan.days)
    return loan
"""

_PUBLIC_EXTEND_PASSTHROUGH = """

def extend(register, loan_id, extra_days):
    loan = register.extend(loan_id, extra_days)
    if loan.days > LONG_LOAN_DAYS:
        log.warning("long loan: %s now out for %d days", loan.loan_id, loan.days)
    return loan
"""

_SPLIT = "\n\ndef lend("


def _gold1(state: str) -> str:
    head, tail = _LOANS_WITH_REPLACE.split(_SPLIT, 1)
    method = (
        _REGISTER_EXTEND_TRUSTING if state == "api" else _REGISTER_EXTEND_VALIDATING
    )
    public = _PUBLIC_EXTEND_VALIDATING if state == "api" else _PUBLIC_EXTEND_PASSTHROUGH
    return (
        head.rstrip("\n") + "\n" + method + _SPLIT + tail.rstrip("\n") + "\n" + public
    )


_REQ1 = Request(
    text=(
        "Add a public function `extend(register, loan_id, extra_days)` to loans.py: it adds "
        "extra_days to the loan's days, stores the updated Loan in the register and returns "
        "it. extra_days must be positive; zero or negative is invalid input and raises "
        "ValueError. A loan whose total goes past 180 days is the notable condition for "
        "this operation."
    ),
    target="gallerylend/loans.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"api": _gold1("api"), "storage": _gold1("storage")},
)

# ----------------------------------------------------------------- checkpoint 2: take_back

_C2_FUNCTIONAL = {
    "test_take_back_functional.py": """import pytest

from gallerylend.loans import LoanRegister, extend, lend, take_back


def test_take_back_marks_returned_with_condition():
    reg = LoanRegister()
    loan = lend(reg, "Nocturne in Grey", "Kunsthalle Bremen", 30)
    out = take_back(reg, loan.loan_id, "good")
    assert out.status == "returned" and out.condition == "good"
    assert reg.get(loan.loan_id).status == "returned"


def test_take_back_damaged_is_stored():
    reg = LoanRegister()
    loan = lend(reg, "Study of Hands", "Ateneum", 60)
    out = take_back(reg, loan.loan_id, "damaged")
    assert out.condition == "damaged" and out.days == 60


def test_take_back_rejects_unknown_condition():
    reg = LoanRegister()
    loan = lend(reg, "Nocturne in Grey", "Kunsthalle Bremen", 30)
    with pytest.raises(ValueError):
        take_back(reg, loan.loan_id, "lost")
    assert reg.get(loan.loan_id).status == "out"


def test_take_back_keeps_the_other_loan_in_the_register():
    reg = LoanRegister()
    keep = lend(reg, "Harbour at Dusk", "Rijksmuseum", 90)
    loan = lend(reg, "Nocturne in Grey", "Kunsthalle Bremen", 30)
    out = take_back(reg, loan.loan_id, "good")
    assert out.status == "returned" and out.condition == "good"
    assert reg.get(loan.loan_id).condition == "good"
    kept = reg.get(keep.loan_id)
    assert kept is not None, "taking one loan back dropped the other"
    assert kept == keep
    assert kept.status == "out" and kept.condition == ""
    assert kept.days == 90 and kept.borrower == "Rijksmuseum"


def test_a_returned_loan_keeps_its_status_when_extended():
    reg = LoanRegister()
    keep = lend(reg, "Harbour at Dusk", "Rijksmuseum", 90)
    loan = lend(reg, "Study of Hands", "Ateneum", 60)
    take_back(reg, loan.loan_id, "damaged")
    out = extend(reg, loan.loan_id, 7)
    assert out.days == 67
    assert out.status == "returned", "extending reset the loan's status"
    assert out.condition == "damaged", "extending reset the condition"
    stored = reg.get(loan.loan_id)
    assert stored.status == "returned" and stored.condition == "damaged"
    assert stored.days == 67 and stored.borrower == "Ateneum"
    kept = reg.get(keep.loan_id)
    assert kept is not None, "extending one loan dropped the other"
    assert kept == keep and kept.status == "out"
"""
}

_C2_REGRESSION = {
    "test_take_back_regression.py": """import pytest

from gallerylend.loans import LoanRegister, extend, lend


def test_lend_extend_get_unchanged():
    reg = LoanRegister()
    loan = lend(reg, "Harbour at Dusk", "Rijksmuseum", 90)
    assert reg.get("L1") is loan
    assert extend(reg, "L1", 10).days == 100
    with pytest.raises(ValueError):
        extend(reg, "L1", 0)
    with pytest.raises(ValueError):
        lend(reg, "x", "y", -1)
    second = lend(reg, "Study of Hands", "Ateneum", 60)
    assert second.loan_id == "L2" and reg.get("L2") is second
    assert extend(reg, "L2", 5).days == 65
    assert reg.get("L2").days == 65
    kept = reg.get("L1")
    assert kept is not None, "extending one loan dropped the other"
    assert kept.days == 100 and kept.status == "out"
    assert kept.artwork == "Harbour at Dusk" and kept.condition == ""
"""
}

_C2_CONTRACT = {
    "api": {
        "test_take_back_validation.py": """import pytest

from gallerylend.loans import LoanRegister, lend, take_back


def test_public_take_back_validates_and_register_trusts_its_arguments():
    reg = LoanRegister()
    loan = lend(reg, "Nocturne in Grey", "Kunsthalle Bremen", 30)
    with pytest.raises(ValueError):
        take_back(reg, loan.loan_id, "lost")
    # the storage layer performs no check: called directly it accepts the same value
    out = reg.close(loan.loan_id, "lost")
    assert out.status == "returned" and out.condition == "lost"
"""
    },
    "storage": {
        "test_take_back_validation.py": """import pytest

from gallerylend.loans import LoanRegister, lend, take_back


def test_register_close_validates_and_public_passes_through(monkeypatch):
    reg = LoanRegister()
    loan = lend(reg, "Nocturne in Grey", "Kunsthalle Bremen", 30)
    with pytest.raises(ValueError):
        reg.close(loan.loan_id, "lost")
    calls = []

    def spy(loan_id, condition):
        calls.append((loan_id, condition))
        raise ValueError("rejected by the register")

    monkeypatch.setattr(reg, "close", spy)
    with pytest.raises(ValueError):
        take_back(reg, loan.loan_id, "lost")
    assert calls == [(loan.loan_id, "lost")]
"""
    },
}

_C2_SUPPORT = {
    "test_take_back_logging.py": """import logging

from gallerylend.loans import LoanRegister, lend, take_back


def test_damaged_return_warns_exactly_once(caplog):
    reg = LoanRegister()
    loan = lend(reg, "Nocturne in Grey", "Kunsthalle Bremen", 30)
    caplog.set_level(logging.DEBUG, logger="gallerylend.loans")
    caplog.clear()
    take_back(reg, loan.loan_id, "damaged")
    assert [r.levelno for r in caplog.records] == [logging.WARNING]


def test_good_return_logs_nothing(caplog):
    reg = LoanRegister()
    loan = lend(reg, "Study of Hands", "Ateneum", 30)
    caplog.set_level(logging.DEBUG, logger="gallerylend.loans")
    caplog.clear()
    take_back(reg, loan.loan_id, "good")
    assert caplog.records == []
"""
}

_REGISTER_CLOSE_TRUSTING = """
    def close(self, loan_id, condition):
        loan = self._loans[loan_id]
        closed = replace(loan, status="returned", condition=condition)
        self._loans[loan_id] = closed
        return closed
"""

_REGISTER_CLOSE_VALIDATING = """
    def close(self, loan_id, condition):
        if condition not in CONDITIONS:
            raise ValueError(f"condition must be one of {CONDITIONS}, got {condition!r}")
        loan = self._loans[loan_id]
        closed = replace(loan, status="returned", condition=condition)
        self._loans[loan_id] = closed
        return closed
"""

_PUBLIC_TAKE_BACK_VALIDATING = """

def take_back(register, loan_id, condition):
    if condition not in CONDITIONS:
        raise ValueError(f"condition must be one of {CONDITIONS}, got {condition!r}")
    loan = register.close(loan_id, condition)
    if loan.condition == "damaged":
        log.warning("%s came back damaged from %s", loan.loan_id, loan.borrower)
    return loan
"""

_PUBLIC_TAKE_BACK_PASSTHROUGH = """

def take_back(register, loan_id, condition):
    loan = register.close(loan_id, condition)
    if loan.condition == "damaged":
        log.warning("%s came back damaged from %s", loan.loan_id, loan.borrower)
    return loan
"""


def _gold2(state: str) -> str:
    # Built on the checkpoint-1 gold under the state then in force (storage).
    base = _gold1("storage").replace(
        "LONG_LOAN_DAYS = 180\n",
        'LONG_LOAN_DAYS = 180\nCONDITIONS = ("good", "damaged")\n',
        1,
    )
    head, tail = base.split(_SPLIT, 1)
    method = _REGISTER_CLOSE_TRUSTING if state == "api" else _REGISTER_CLOSE_VALIDATING
    public = (
        _PUBLIC_TAKE_BACK_VALIDATING
        if state == "api"
        else _PUBLIC_TAKE_BACK_PASSTHROUGH
    )
    return (
        head.rstrip("\n") + "\n" + method + _SPLIT + tail.rstrip("\n") + "\n" + public
    )


_REQ2 = Request(
    text=(
        "Add a public function `take_back(register, loan_id, condition)` to loans.py: it marks "
        'the loan as status "returned" with the given condition note, stores the updated Loan '
        'and returns it. condition must be one of "good" or "damaged"; any other value is '
        "invalid input and raises ValueError. A work coming back damaged is the notable "
        "condition for this operation."
    ),
    target="gallerylend/loans.py",
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
        "I'm the registrar at a small municipal gallery and I'm replacing the loans "
        "spreadsheet with a tiny Python package, gallerylend. Outgoing loans only: which "
        "artwork went to which institution, for how many days, and whether it is back. The "
        "spreadsheet has burned us twice, once when a filter hid three overdue rows and once "
        "when someone typed the days column as a date. All I want is a LoanRegister that a "
        "script can drive to print the weekly sheet for the director's meeting, roughly:\n\n"
        "```\n$ python -m gallerylend.sheet\nL1  Harbour at Dusk -> Rijksmuseum  90d  [out]\n"
        "L2  Study of Hands -> Ateneum  60d  [out]\n```\n\nCould you draft a README scope "
        "section that makes clear this is not a collections management system? The board "
        "keeps asking whether it will do insurance valuations and condition photography, "
        "and I need a paragraph I can point at. Volume is maybe fifteen loans a year, so I "
        "care about nothing except that the code is obvious to whoever inherits it.",
    ),
    Turn(
        "assistant",
        "Something like this keeps the scope honest:\n\n```\n## Scope\ngallerylend records "
        "outgoing artwork loans for a single gallery in memory: the work, the borrowing "
        "institution, the agreed number of days and whether the work is back. It is a "
        "helper for scripts and tests, not a collections management system, and it keeps "
        "no history beyond the current register.\n\n## Non-goals\n- insurance valuations\n"
        "- condition photography or reports\n- incoming loans\n- persistence across runs\n"
        "```\n\nThe non-goals list is the part the board will actually read. A minimal "
        "usage block underneath sets the tone for the API:\n\n```python\nfrom gallerylend."
        "loans import LoanRegister, lend\n\nregister = LoanRegister()\nloan = lend(register, "
        '"Harbour at Dusk", "Rijksmuseum", 90)\nprint(loan.loan_id, loan.status)\n```\n\n'
        "Fifteen loans a year means every design choice should favour readability over "
        "anything else; there is no performance question to answer.",
    ),
    Turn(
        "user",
        "I've gone with a plain day count rather than start and end dates. My reasoning: "
        "the paperwork always says 'ninety days from dispatch' and dispatch dates slip, so "
        "storing an end date would be storing a guess. But a colleague argued that a count "
        "makes the overdue check impossible without knowing when the clock started. Is a "
        "count defensible, or should Loan carry a `dispatched` date after all? For what it "
        "is worth the loan agreement template we send out reads:\n\n```\nLoan period: "
        "___ days from the date of dispatch, extendable once by written agreement.\n"
        "Condition on return to be noted as GOOD or DAMAGED by the receiving registrar.\n"
        "Extensions beyond 180 days in total require the director's countersignature.\n"
        "```\n\nso days is genuinely the unit everyone signs against, and the dispatch "
        "date lives in the courier paperwork, not in our system. The 180-day line is why "
        "`lend` shouts about long loans: the director wants to know before she has to sign.",
    ),
    Turn(
        "assistant",
        "A count is defensible precisely because it is the unit on the agreement. Storing "
        "an end date would duplicate information that changes whenever dispatch slips, and "
        "the register would then disagree with the signed paper. When you do want an "
        "overdue check, add the dispatch date at that point and compute the deadline "
        "instead of storing it:\n\n```python\nfrom datetime import date, timedelta\n\n"
        "def due(loan, dispatched: date) -> date:\n    return dispatched + timedelta(days="
        "loan.days)\n```\n\nThat keeps `days` as the single source of truth and puts the "
        "dispatch date where it is known, on the caller's side. It also means extending a "
        "loan is just adding to `days`, which matches the 'extendable once' clause in the "
        "template. If you later want the sheet to show days remaining, the same helper "
        "does it without touching the model:\n\n```python\ndef remaining(loan, dispatched: "
        "date, today: date) -> int:\n    return (due(loan, dispatched) - today).days\n```\n\n"
        "Negative means overdue, and the sheet can flag it with a marker rather than a "
        "separate status.",
    ),
    Turn(
        "user",
        "I drafted tests for the sheet line before writing much of the package, because the "
        "director cares about that output more than anything else. Does this shape look "
        "right to you, or am I testing formatting too tightly?\n\n```python\nfrom gallerylend"
        ".model import Loan\nfrom gallerylend.report import line\n\n\ndef test_line_for_"
        'outgoing_loan():\n    loan = Loan(loan_id="L1", artwork="Harbour at Dusk", '
        'borrower="Rijksmuseum", days=90)\n    assert line(loan) == "L1  Harbour at Dusk '
        '-> Rijksmuseum  90d  [out]"\n\n\ndef test_line_for_returned_loan():\n    loan = '
        'Loan(loan_id="L2", artwork="Study of Hands", borrower="Ateneum", days=60, status='
        '"returned")\n    assert line(loan) == "L2  Study of Hands -> Ateneum  60d  '
        '[returned]"\n```\n\nThe two-space gaps are deliberate; the director reads it in a '
        "monospace email.",
    ),
    Turn(
        "assistant",
        "That is the right level: the sheet is the product, so pinning the exact string is "
        "fine, and two tests (one per status) cover the branches without turning into a "
        "formatting suite. If the columns ever need aligning across rows, that becomes a "
        "`sheet(loans)` function that pads, and these tests keep guarding the single-line "
        "shape. One suggestion, add a case with a long artwork title so a future padding "
        "change cannot silently truncate:\n\n```python\ndef test_line_does_not_truncate_"
        'long_titles():\n    loan = Loan(loan_id="L3", artwork="Portrait of the Artist\'s '
        'Mother in a Green Shawl", borrower="Ateneum", days=30)\n    assert "Green Shawl" '
        "in line(loan)\n```\n\nKeep the report module free of any register import so the "
        "tests stay pure functions of a Loan; the sheet script can do the fetching.",
    ),
    Turn(
        "user",
        "I made Loan a frozen dataclass and immediately walked into this while trying to "
        'mark a return:\n\n```\n>>> loan.status = "returned"\nTraceback (most recent call '
        'last):\n  File "<stdin>", line 1, in <module>\n  File "<string>", line 4, in '
        "__setattr__\ndataclasses.FrozenInstanceError: cannot assign to field 'status'\n"
        "```\n\nIs frozen worth the friction here? My instinct says yes because the sheet "
        "script should never be able to mutate a loan by accident, but then every update "
        "has to construct a new Loan and I worry about forgetting a field when we add "
        "`condition` and whatever else the conservators want. The first draft of the return "
        "code, which is what produced that traceback, looked like this:\n\n```python\ndef "
        "mark_returned(register, loan_id):\n    loan = register.get(loan_id)\n    loan.status "
        '= "returned"\n    return loan\n```\n\nand I only noticed because the sheet still '
        "listed the work as out after the courier had signed it back in. That is the sort "
        "of silent wrongness the spreadsheet used to produce, and the whole point of the "
        "rewrite is to make it impossible.",
    ),
    Turn(
        "assistant",
        "Keep it frozen; the friction is exactly the point, and `dataclasses.replace` "
        "removes the forgetting-a-field worry because it copies every field you do not "
        "mention:\n\n```python\nfrom dataclasses import replace\n\nreturned = replace(loan, "
        'status="returned", condition="good")\n```\n\nSo an update is one line, the '
        "register swaps the new instance in under the same id, and any script that holds "
        "the old instance sees a stale but consistent record rather than a half-updated "
        "one. When conservators add fields with defaults, `replace` keeps working "
        "unchanged. Your draft would become:\n\n```python\ndef mark_returned(register, "
        "loan_id):\n    loan = register.get(loan_id)\n    returned = replace(loan, status="
        '"returned")\n    register._loans[loan_id] = returned\n    return returned\n```\n\n'
        "except that the register should own the swap, so give it a method that stores a "
        "replacement under the same id rather than reaching into `_loans` from outside.",
    ),
    Turn(
        "user",
        "Now conventions, because I want them written down before the next feature. "
        "Logging first: a notable condition, the kind the director would want to hear "
        "about, gets exactly one logging.warning from the loans module logger, and nothing "
        "else is logged, no info or debug chatter. `lend` already does this: one warning "
        "when a loan is over 180 days, silence otherwise.",
    ),
    Turn(
        "assistant",
        "Noted: exactly one `log.warning` per notable condition from the `gallerylend."
        "loans` logger, and no other log records at all. New operations that name a "
        "notable case follow `lend` (a single warning, otherwise silent), and I will not "
        "add info or debug lines anywhere. Tests can pin that with caplog: exactly one "
        "WARNING record on the notable path, an empty record list otherwise.",
    ),
    Turn(
        "user",
        "Second, where validation lives: input checks belong in the public functions in "
        "loans.py, which raise ValueError on bad input, and LoanRegister methods trust "
        "their arguments and never validate. `lend` is the model: it rejects a non-positive "
        "day count itself and `insert` just stores what it is given.",
    ),
    Turn(
        "assistant",
        "Understood: validation in the public functions (raise ValueError there), and "
        "LoanRegister methods do no checking of their own. New operations will follow "
        "`lend` and `insert`: the public function rejects bad input before touching the "
        "register, and the register method assumes its arguments are sound.",
    ),
    Turn(
        "user",
        "Change of plan on that second one after this week's review. The conservators want "
        "to call the register directly from their own scripts, so the checks have to sit "
        "where they cannot be skipped: for new operations, validation moves into the "
        "LoanRegister method, which raises ValueError, and the public function just passes "
        "the call through with no pre-check of its own. Leave `lend` and `insert` as they "
        "are.",
    ),
    Turn(
        "assistant",
        "Got it: new operations validate inside the LoanRegister method (ValueError raised "
        "there), and the public function calls straight through without repeating the "
        "check. `lend` and `insert` keep their current split.",
    ),
    Turn(
        "user",
        "For context, the only tests that exist today are these two, so anything new "
        "needs its own:\n\n```python\ndef test_lend_mints_sequential_ids():\n    reg = "
        'LoanRegister()\n    assert lend(reg, "a", "b", 10).loan_id == "L1"\n    assert '
        'lend(reg, "c", "d", 10).loan_id == "L2"\n\n\ndef test_lend_rejects_zero_days():\n'
        '    with pytest.raises(ValueError):\n        lend(LoanRegister(), "a", "b", 0)\n```',
    ),
    Turn(
        "assistant",
        "Thanks, that is a clear baseline. I will keep those passing and add tests for each "
        "new operation. Send the first request whenever you are ready and I will return the "
        "full loans module.",
    ),
]

_EVENT = (
    "Reverting last week's change: the conservators are getting their own wrapper instead, "
    "so the register goes back to being a plain store. For new operations, validation "
    "lives in the public function in loans.py again (raise ValueError there) and "
    "LoanRegister methods trust their arguments. What is already in the register stays "
    "where it is."
)


def build() -> Session:
    return Session(
        id="S32",
        project="gallerylend",
        target_family="validation",
        support_family="logging",
        lifecycle="reinstatement",
        files=_FILES,
        prefix=_PREFIX,
        states=("api", "storage"),
        state_at=("storage", "api"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10, 12),
    )
