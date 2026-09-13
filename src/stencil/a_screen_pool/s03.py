# ruff: noqa: E501
"""S03: library loans — naming (target, scope) x return_shape (support)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""loandesk package."""\n'

_MODEL = '''"""Loan and fine records."""

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Loan:
    loan_id: str
    patron: str
    title: str
    due_day: int
    status: str = "out"

    def with_status(self, status: str) -> "Loan":
        return replace(self, status=status)


@dataclass(frozen=True)
class Fine:
    fine_id: str
    patron: str
    cents: int
    status: str = "owed"
'''

_DESK = '''"""In-memory loan desk."""

from loandesk.model import Loan


class LoanDesk:
    def __init__(self) -> None:
        self._loans: dict[str, Loan] = {}
        self._counter = 0

    def checkout_book(self, patron: str, title: str, due_day: int) -> Loan:
        self._counter += 1
        loan = Loan(loan_id=f"L{self._counter}", patron=patron, title=title, due_day=due_day)
        self._loans[loan.loan_id] = loan
        return loan

    def find(self, loan_id: str) -> Loan | None:
        return self._loans.get(loan_id)

    def count(self) -> int:
        return len(self._loans)
'''

_FINES = '''"""In-memory fine ledger."""

from loandesk.model import Fine


class FineLedger:
    def __init__(self) -> None:
        self._fines: dict[str, Fine] = {}
        self._counter = 0

    def record_fine(self, patron: str, cents: int) -> Fine:
        self._counter += 1
        fine = Fine(fine_id=f"F{self._counter}", patron=patron, cents=cents)
        self._fines[fine.fine_id] = fine
        return fine

    def find(self, fine_id: str) -> Fine | None:
        return self._fines.get(fine_id)

    def owed(self, patron: str) -> int:
        return sum(f.cents for f in self._fines.values() if f.patron == patron and f.status == "owed")
'''

_FILES = {
    "loandesk/__init__.py": _INIT,
    "loandesk/model.py": _MODEL,
    "loandesk/desk.py": _DESK,
    "loandesk/fines.py": _FINES,
}

# ----------------------------------------------------------------- checkpoint 1: return

_C1_HELPER = """from loandesk.desk import LoanDesk
from loandesk.model import Loan


def _return(desk):
    fn = getattr(desk, "return_book", None) or getattr(desk, "book_return", None)
    assert fn is not None, "no return method found"
    return fn
"""

_C1_FUNCTIONAL = {
    "test_return_functional.py": _C1_HELPER
    + """

def test_return_sets_status_returned():
    d = LoanDesk()
    loan = d.checkout_book("ana", "Dune", 30)
    other = d.checkout_book("ben", "Emma", 12)
    out = _return(d)(loan.loan_id)
    assert out.status == "returned"
    assert d.find(loan.loan_id).status == "returned"
    assert d.count() == 2
    assert d.find(other.loan_id) == other
    assert d.find(other.loan_id).status == "out"


def test_return_keeps_patron_title_due():
    d = LoanDesk()
    loan = d.checkout_book("ben", "Emma", 12)
    kept = d.checkout_book("cal", "Ada", 7)
    out = _return(d)(loan.loan_id)
    assert out.loan_id == loan.loan_id
    assert out.patron == "ben" and out.title == "Emma" and out.due_day == 12
    assert d.find(kept.loan_id) == kept and d.count() == 2
    assert d.find(kept.loan_id).title == "Ada" and d.find(kept.loan_id).due_day == 7


def test_return_unknown_raises_keyerror():
    d = LoanDesk()
    try:
        _return(d)("L999")
    except KeyError:
        return
    raise AssertionError("expected KeyError for an unknown loan")


def test_return_leaves_other_loans_untouched():
    d = LoanDesk()
    first = d.checkout_book("ana", "Dune", 30)
    second = d.checkout_book("ben", "Emma", 12)
    third = d.checkout_book("cal", "Ada", 7)
    _return(d)(second.loan_id)  # a neighbour carrying a non-default status
    before = d.count()
    out = _return(d)(third.loan_id)
    assert out.loan_id == third.loan_id and out.status == "returned"
    assert d.count() == before
    assert d.find(first.loan_id) == first and d.find(first.loan_id).status == "out"
    assert d.find(second.loan_id).status == "returned"
    assert d.find(second.loan_id).patron == "ben"
    assert d.find(second.loan_id).title == "Emma"
    assert d.find(third.loan_id) == out
"""
}

_C1_REGRESSION = {
    "test_return_regression.py": """from loandesk.desk import LoanDesk
from loandesk.fines import FineLedger


def test_checkout_and_find_unchanged():
    d = LoanDesk()
    loan = d.checkout_book("ana", "Dune", 30)
    assert loan.loan_id == "L1" and loan.status == "out"
    assert d.find("L1") is loan
    assert d.find("nope") is None
    assert d.count() == 1
    second = d.checkout_book("ben", "Emma", 12)
    assert second.loan_id == "L2" and second.status == "out"
    assert d.find("L2") is second
    assert d.find("L1") is loan and d.count() == 2


def test_fines_untouched():
    f = FineLedger()
    fine = f.record_fine("ana", 250)
    assert fine.fine_id == "F1" and f.owed("ana") == 250
    second = f.record_fine("ben", 125)
    assert second.fine_id == "F2" and second.status == "owed"
    assert f.find("F1") is fine and f.find("F2") is second
    assert f.owed("ana") == 250 and f.owed("ben") == 125
"""
}

_C1_CONTRACT = {
    "verb_noun": {
        "test_return_naming.py": """from loandesk.desk import LoanDesk


def test_return_is_verb_noun():
    assert hasattr(LoanDesk, "return_book")
    assert not hasattr(LoanDesk, "book_return")
"""
    },
    "noun_verb": {
        "test_return_naming.py": """from loandesk.desk import LoanDesk


def test_return_is_noun_verb():
    assert hasattr(LoanDesk, "book_return")
    assert not hasattr(LoanDesk, "return_book")
"""
    },
}

_C1_SUPPORT = {
    "test_return_shape.py": _C1_HELPER
    + """

def test_return_returns_loan_dataclass_not_dict():
    d = LoanDesk()
    loan = d.checkout_book("ana", "Dune", 30)
    out = _return(d)(loan.loan_id)
    assert isinstance(out, Loan)
    assert not isinstance(out, dict)
"""
}


def _gold1(name: str) -> str:
    return (
        _DESK.rstrip("\n")
        + f"""

    def {name}(self, loan_id: str) -> Loan:
        loan = self._loans[loan_id]
        returned = loan.with_status("returned")
        self._loans[loan_id] = returned
        return returned
"""
    )


_REQ1 = Request(
    text=(
        "Add a public method on LoanDesk that returns a book by loan id: it sets the loan's "
        'status to "returned", stores the updated loan and returns it. An unknown id raises '
        "KeyError."
    ),
    target="loandesk/desk.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"verb_noun": _gold1("return_book"), "noun_verb": _gold1("book_return")},
)

# ----------------------------------------------------------------- checkpoint 2: waive

_C2_HELPER = """from loandesk.fines import FineLedger
from loandesk.model import Fine


def _waive(ledger):
    fn = getattr(ledger, "waive_fine", None) or getattr(ledger, "fine_waive", None)
    assert fn is not None, "no waive method found"
    return fn
"""

_C2_FUNCTIONAL = {
    "test_waive_functional.py": _C2_HELPER
    + """

def test_waive_sets_status_waived():
    f = FineLedger()
    fine = f.record_fine("ana", 250)
    other = f.record_fine("ben", 75)
    out = _waive(f)(fine.fine_id)
    assert out.status == "waived"
    assert f.find(fine.fine_id).status == "waived"
    assert f.find(other.fine_id) == other
    assert f.find(other.fine_id).status == "owed"
    assert f.owed("ben") == 75


def test_waive_removes_from_owed_total():
    f = FineLedger()
    a = f.record_fine("ana", 250)
    f.record_fine("ana", 100)
    out = _waive(f)(a.fine_id)
    assert out.cents == 250 and out.patron == "ana"
    assert f.owed("ana") == 100


def test_waive_unknown_raises_keyerror():
    f = FineLedger()
    try:
        _waive(f)("F999")
    except KeyError:
        return
    raise AssertionError("expected KeyError for an unknown fine")


def test_waive_leaves_other_fines_untouched():
    f = FineLedger()
    first = f.record_fine("ana", 250)
    second = f.record_fine("ben", 75)
    third = f.record_fine("cal", 40)
    _waive(f)(first.fine_id)  # a neighbour carrying a non-default status
    out = _waive(f)(second.fine_id)
    assert out.fine_id == second.fine_id and out.status == "waived"
    assert f.find(first.fine_id).status == "waived"
    assert f.find(first.fine_id).cents == 250 and f.find(first.fine_id).patron == "ana"
    assert f.find(third.fine_id) == third
    assert f.find(third.fine_id).status == "owed"
    assert f.owed("ana") == 0 and f.owed("ben") == 0 and f.owed("cal") == 40
"""
}

_C2_REGRESSION = {
    "test_waive_regression.py": """from loandesk.desk import LoanDesk
from loandesk.fines import FineLedger


def _return(desk):
    return getattr(desk, "return_book", None) or getattr(desk, "book_return", None)


def test_desk_and_return_unchanged():
    d = LoanDesk()
    loan = d.checkout_book("ana", "Dune", 30)
    assert d.find("L1") is loan and d.count() == 1
    assert _return(d)(loan.loan_id).status == "returned"
    other = d.checkout_book("ben", "Emma", 12)
    assert d.count() == 2 and d.find("L2") is other
    assert _return(d)(other.loan_id).status == "returned"
    assert d.count() == 2
    assert d.find("L1").status == "returned" and d.find("L1").patron == "ana"
    assert d.find("L1").title == "Dune" and d.find("L1").due_day == 30


def test_record_find_owed_unchanged():
    f = FineLedger()
    fine = f.record_fine("ben", 75)
    assert fine.fine_id == "F1" and fine.status == "owed"
    assert f.find("F1") is fine and f.find("F9") is None
    assert f.owed("ben") == 75 and f.owed("ana") == 0
    other = f.record_fine("ana", 300)
    assert other.fine_id == "F2" and other.status == "owed"
    assert f.find("F2") is other and f.find("F1") is fine
    assert f.owed("ana") == 300 and f.owed("ben") == 75
"""
}

_C2_CONTRACT = {
    "verb_noun": {
        "test_waive_naming.py": """from loandesk.fines import FineLedger


def test_waive_is_verb_noun():
    assert hasattr(FineLedger, "waive_fine")
    assert not hasattr(FineLedger, "fine_waive")
"""
    },
    "noun_verb": {
        "test_waive_naming.py": """from loandesk.fines import FineLedger


def test_waive_is_noun_verb():
    assert hasattr(FineLedger, "fine_waive")
    assert not hasattr(FineLedger, "waive_fine")
"""
    },
}

_C2_SUPPORT = {
    "test_waive_shape.py": _C2_HELPER
    + """

def test_waive_returns_fine_dataclass_not_dict():
    f = FineLedger()
    fine = f.record_fine("ana", 250)
    out = _waive(f)(fine.fine_id)
    assert isinstance(out, Fine)
    assert not isinstance(out, dict)
"""
}


def _gold2(name: str) -> str:
    # Request 2 targets fines.py; the checkpoint-1 gold (desk.py, verb_noun) is untouched.
    body = (
        _FINES.rstrip("\n")
        + f"""

    def {name}(self, fine_id: str) -> Fine:
        fine = self._fines[fine_id]
        waived = replace(fine, status="waived")
        self._fines[fine_id] = waived
        return waived
"""
    )
    return body.replace(
        "from loandesk.model import Fine\n",
        "from dataclasses import replace\n\nfrom loandesk.model import Fine\n",
        1,
    )


_REQ2 = Request(
    text=(
        "Add a public method on FineLedger that waives a fine by id: it sets the fine's "
        'status to "waived" (so it no longer counts toward what the patron owes), stores '
        "the updated fine and returns it. An unknown id raises KeyError."
    ),
    target="loandesk/fines.py",
    functional_tests=_C2_FUNCTIONAL,
    regression_tests=_C2_REGRESSION,
    contract_tests=_C2_CONTRACT,
    support_tests=_C2_SUPPORT,
    gold={"verb_noun": _gold2("waive_fine"), "noun_verb": _gold2("fine_waive")},
)

# ----------------------------------------------------------------- prefix (16 turns)

_PREFIX = [
    Turn(
        "user",
        "I'm building a small loan-desk package for the community library at the church "
        "hall. Two volunteers a day, a laptop at the desk, about three hundred books, and "
        "the current system is a ring binder. I want an in-memory LoanDesk with Loan records "
        "and a separate FineLedger for the overdue fines, driven by a couple of scripts: one "
        "that prints today's due list, one that prints who owes what. Persistence is a JSON "
        "file we write at closing time; no database, no web app. The closing script is "
        "roughly:\n\n```\n#!/bin/sh\ncd /home/desk/loandesk && python -m loandesk.closeout "
        "--out state/$(date +%F).json\n```\n\nCould you sketch what the README should say "
        "about scope? The parish council has already asked whether it will 'do the "
        "catalogue' and I want a written answer that it will not, so the volunteers stop "
        "promising things.",
    ),
    Turn(
        "assistant",
        "A short scope section plus explicit non-goals is the thing to show the council:"
        "\n\n```\n## Scope\nloandesk tracks loans and fines for a single lending desk in a "
        "single process. It keeps Loan records in a LoanDesk and Fine records in a "
        "FineLedger, has no persistence beyond the closing-time JSON snapshot and no "
        "concurrency guarantees, and is meant for the desk scripts, not as a service.\n\n"
        "## Non-goals\n- a catalogue or search\n- reservations and holds\n- patron accounts "
        "or logins\n- printing receipts\n```\n\nA usage block sets expectations for the API:"
        "\n\n```python\nfrom loandesk.desk import LoanDesk\n\ndesk = LoanDesk()\nloan = "
        'desk.checkout_book("ana", "Dune", due_day=30)\nprint(desk.find(loan.loan_id))\n'
        "```\n\nIf the catalogue question comes back, the honest answer is that a catalogue "
        "is a different package with different data, and this one can import it later. "
        "Add a `Requires Python 3.11+` line as well; the desk laptop is on whatever Ubuntu "
        "shipped and `str | None` will be the first thing to break.",
    ),
    Turn(
        "user",
        "Good. Ids are L1, L2, ... for loans and F1, F2, ... for fines, from counters. One "
        "volunteer wants the loan id to embed the patron's library-card number so she can "
        "read it off the binder without a lookup. I understand the wish but I think it "
        "mixes two things. The snapshot I have in mind is only:\n\n```json\n{\n  "
        '"desk": "st-marks",\n  "closed_at": "2026-09-14T17:00:00",\n  "loans": [\n'
        '    {"loan_id": "L1", "patron": "ana", "title": "Dune", "due_day": 30, '
        '"status": "out"},\n    {"loan_id": "L2", "patron": "ben", "title": "Emma", '
        '"due_day": 12, "status": "returned"}\n  ]\n}\n```\n\nIs there a '
        "sensible middle ground, or do I just say no? I would rather not have this argument "
        "again every time a new volunteer joins, so whatever we pick goes in the README.",
    ),
    Turn(
        "assistant",
        "Say no to embedding, and yes to the underlying need. Keep the counter as identity "
        "and carry the card number as data: a `patron` field already exists, and the due "
        "list script can print `L14  ana (card 0231)  Dune  due day 30` by joining the two. "
        "Counters stay short in logs and in the binder, and only `checkout_book` mints "
        "ids, so if persistence changes there is one place to touch:\n\n```python\n"
        'def _next_id(self) -> str:\n    self._counter += 1\n    return f"L{self._counter}"'
        "\n```\n\nA composite id like `0231-L14` looks convenient until a card is reissued "
        "or a loan is moved to a family member, at which point the id lies. Ids should "
        "never carry facts that can change. If you want the binder to stay readable, print "
        "the card number in the due list and on the return slip; that costs one join and "
        "no schema.",
    ),
    Turn(
        "user",
        "I want a helper that formats a loan for the due list, like `L3 Dune -> ana (due "
        "day 30)`. Method on Loan or free function next to it? A method is discoverable, "
        "but then a record type knows about presentation. Here is the test draft so you "
        "can see the shape:\n\n```python\nimport pytest\n\nfrom loandesk.model import Loan"
        '\n\n\n@pytest.fixture\ndef loan():\n    return Loan(loan_id="L3", patron="ana", '
        'title="Dune", due_day=30)\n\n\ndef test_summary_out(loan):\n    assert summary('
        'loan) == "L3 Dune -> ana (due day 30)"\n\n\ndef test_summary_returned(loan):\n'
        '    assert summary(loan.with_status("returned")) == "L3 Dune -> ana (returned)"\n'
        "```\n\nThe due-list script would then be a loop over `desk.all()` (which we do "
        "not have yet) filtered to status out and sorted by due_day, printing one summary "
        "per line.",
    ),
    Turn(
        "assistant",
        "Put it next to the model as a plain function so the scripts and tests share it "
        "without Loan learning about presentation:\n\n```python\ndef summary(loan: Loan) "
        '-> str:\n    tail = "returned" if loan.status == "returned" else f"due day '
        '{loan.due_day}"\n    return f"{loan.loan_id} {loan.title} -> {loan.patron} '
        '({tail})"\n```\n\nIt reads only public fields, so it stays trivially testable, '
        "and if the due list later wants column alignment that lives in the script. A "
        "`__str__` on Loan would tie the record to one rendering forever, and the JSON "
        "snapshot needs its own serializer regardless. Both of your tests pass against "
        "that as written. For `all()`, `list(self._loans.values())` in insertion order is "
        "enough, and the script sorts:\n\n```python\nfor loan in sorted(desk.all(), key="
        'lambda loan: loan.due_day):\n    if loan.status == "out":\n        print(summary('
        "loan))\n```",
    ),
    Turn(
        "user",
        "We'll add it with the due-list script. Next: should `find` raise on a missing id "
        "or return None? Right now both LoanDesk.find and FineLedger.find return None and "
        "the caller checks. I want one rule to point volunteers at. This is what one of "
        'them hit last week assuming `find` raises:\n\n```\n>>> desk.find("L9").title\n'
        'Traceback (most recent call last):\n  File "<stdin>", line 1, in <module>\n'
        "AttributeError: 'NoneType' object has no attribute 'title'\n```\n\nThe usual "
        "None-propagation trap; she had typed L9 for L6 and spent a while convinced the "
        "desk was corrupted. The desk log from that afternoon:\n\n```\n2026-09-09 14:12:03 "
        "INFO  desk: loaded state/2026-09-08.json (41 loans, 6 fines)\n2026-09-09 14:40:51 "
        "ERROR shell: AttributeError: 'NoneType' object has no attribute 'title'\n```",
    ),
    Turn(
        "assistant",
        "Returning None from `find` is the usual lookup contract: the name says 'try to "
        "find', and callers branch on the result. Methods that *act* on a record "
        "(returning a book, waiving a fine, renewing) are different: acting on an id that "
        "does not exist is a caller bug, so raising KeyError there is the clearer signal "
        "and it surfaces in tests immediately. So the rule is: lookups return None, "
        "actions raise KeyError, on both the desk and the ledger. Keep `find` as it is, "
        "and callers that need a hard failure can wrap it:\n\n```python\ndef require(desk, "
        "loan_id):\n    loan = desk.find(loan_id)\n    if loan is None:\n        raise "
        "KeyError(loan_id)\n    return loan\n```\n\nThe traceback you pasted becomes a "
        "KeyError('L9') at the call site, which tells the volunteer the id was wrong "
        "rather than the desk. The same rule covers the ledger: `find` returns None, and "
        "anything that changes a fine raises KeyError on an unknown id.",
    ),
    Turn(
        "user",
        "Agreed, actions raise KeyError on unknown ids. Two conventions I want to fix now "
        "so the code stays uniform. First: public LoanDesk and FineLedger methods always "
        "return Loan or Fine dataclass instances, never dicts or tuples, even for "
        "convenience. The binder-import script I wrote returned dicts and every caller "
        "grew a `.get('status')`.",
    ),
    Turn(
        "assistant",
        "Noted: every public LoanDesk method returns Loan instances and every public "
        "FineLedger method returns Fine instances (or None from lookups), never dicts or "
        "tuples. Callers stay on one type per module, and the summary helper works on "
        "anything the desk hands back.",
    ),
    Turn(
        "user",
        "Second: method naming. Public methods across the package are named verb_noun, "
        "like checkout_book and record_fine. Anything new follows that pattern so the API "
        "reads as a list of things the desk does.",
    ),
    Turn(
        "assistant",
        "Understood: verb_noun for public methods on both LoanDesk and FineLedger, "
        "matching checkout_book and record_fine. I will name new methods that way; private "
        "helpers can stay free-form. If a verb is ambiguous, for example whether handing a "
        "book back is return_book or checkin_book, I will use the verb the request uses.",
    ),
    Turn(
        "user",
        "One more for later: I'd like `count` to take an optional status filter so the "
        "closing script can print out-versus-returned totals. Not now. For reference, the "
        "tests that exist today are only these:\n\n```python\nfrom loandesk.desk import "
        "LoanDesk\n\n\ndef test_checkout_assigns_sequential_ids():\n    d = LoanDesk()\n"
        '    assert d.checkout_book("ana", "Dune", 30).loan_id == "L1"\n    assert '
        'd.checkout_book("ben", "Emma", 12).loan_id == "L2"\n\n\ndef '
        'test_find_missing_returns_none():\n    assert LoanDesk().find("L1") is None\n'
        "```",
    ),
    Turn(
        "assistant",
        "Noted for later. An optional keyword `status: str | None = None` keeps the "
        "current no-argument call working:\n\n```python\ndef count(self, status: str | "
        "None = None) -> int:\n    if status is None:\n        return len(self._loans)\n"
        "    return sum(1 for loan in self._loans.values() if loan.status == status)\n```",
    ),
    Turn(
        "user",
        "Right. Let's get the first real feature in; the desk opens Tuesday and returning "
        "books has to work by then. I will paste the current files with each request so "
        "you always see the real state rather than my memory of it.",
    ),
    Turn(
        "assistant",
        "Ready when you are. Send the request and I will return the full module.",
    ),
]

_EVENT = (
    "One scoped exception to the naming rule, effective now: in the fines module "
    "(FineLedger only), new public methods are named noun_verb, for example fine_waive "
    "or fine_settle, because the treasurer's ledger spreadsheet lists operations that way "
    "and she reads the code. LoanDesk and everything else stays verb_noun. Existing method "
    "names stay as they are."
)


def build() -> Session:
    return Session(
        id="S03",
        project="loandesk",
        target_family="naming",
        support_family="return_shape",
        lifecycle="scope",
        files=_FILES,
        prefix=_PREFIX,
        states=("verb_noun", "noun_verb"),
        state_at=("verb_noun", "noun_verb"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10),
    )
