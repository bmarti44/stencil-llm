# ruff: noqa: E501
"""S11: invoice numbering — naming (target, scope) x error_surface=propagate (support)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""invoiceseq package."""\n'

_MODEL = '''"""Invoice records and the package error base class."""

from dataclasses import dataclass, replace


class InvoiceSeqError(Exception):
    """Base class for errors the package raises on its own behalf."""


@dataclass(frozen=True)
class Invoice:
    number: str
    customer: str
    amount_cents: int
    status: str = "issued"

    def with_status(self, status: str) -> "Invoice":
        return replace(self, status=status)
'''

_NUMBERING = '''"""Invoice number format: INV-<year>-<4-digit sequence>."""

import re

PATTERN = re.compile(r"INV-(\\d{4})-(\\d{4})")


def format_number(year: int, seq: int) -> str:
    return f"INV-{year}-{seq:04d}"


def parse_number(text: str) -> str:
    m = PATTERN.fullmatch(text.strip().upper())
    if m is None:
        raise ValueError(f"bad invoice number: {text!r}")
    return m.group(0)
'''

_STORE = '''"""In-memory invoice register for one accounting year."""

from invoiceseq.model import Invoice
from invoiceseq.numbering import format_number


class InvoiceStore:
    def __init__(self, year: int) -> None:
        self._year = year
        self._invoices: dict[str, Invoice] = {}
        self._seq = 0

    def add_invoice(self, customer: str, amount_cents: int) -> Invoice:
        self._seq += 1
        inv = Invoice(format_number(self._year, self._seq), customer, amount_cents)
        self._invoices[inv.number] = inv
        return inv

    def find(self, number: str) -> Invoice | None:
        return self._invoices.get(number)

    def count(self) -> int:
        return len(self._invoices)
'''

_ARCHIVE = '''"""Year-end archive shared with the bookkeeping tool."""

from invoiceseq.model import Invoice


class InvoiceArchive:
    def __init__(self) -> None:
        self._items: dict[str, Invoice] = {}

    def find(self, number: str) -> Invoice | None:
        return self._items.get(number)

    def count(self) -> int:
        return len(self._items)
'''

_FILES = {
    "invoiceseq/__init__.py": _INIT,
    "invoiceseq/model.py": _MODEL,
    "invoiceseq/numbering.py": _NUMBERING,
    "invoiceseq/store.py": _STORE,
    "invoiceseq/archive.py": _ARCHIVE,
}

# ----------------------------------------------------------------- checkpoint 1: void (store)

_C1_HELPER = """import pytest

from invoiceseq.model import InvoiceSeqError
from invoiceseq.store import InvoiceStore


def _void(store):
    fn = getattr(store, "void_invoice", None) or getattr(store, "invoice_void", None)
    assert fn is not None, "no void method found"
    return fn


def _store():
    s = InvoiceStore(2026)
    s.add_invoice("Acme", 12000)
    s.add_invoice("Birch & Co", 4550)
    return s
"""

_C1_FUNCTIONAL = {
    "test_void_functional.py": _C1_HELPER
    + """

def test_void_sets_status_and_stores():
    s = _store()
    out = _void(s)("INV-2026-0002")
    assert out.status == "void"
    assert s.find("INV-2026-0002").status == "void"
    assert s.find("INV-2026-0001").status == "issued"
    kept = s.find("INV-2026-0001")
    assert kept is not None and kept.customer == "Acme"
    assert kept.amount_cents == 12000
    assert s.count() == 2


def test_void_accepts_printed_variants():
    s = _store()
    out = _void(s)("  inv-2026-0001 ")
    assert out.number == "INV-2026-0001" and out.status == "void"


def test_void_keeps_customer_and_amount():
    s = _store()
    out = _void(s)("INV-2026-0001")
    assert out.customer == "Acme" and out.amount_cents == 12000
    stored = s.find("INV-2026-0001")
    assert stored.customer == "Acme" and stored.amount_cents == 12000
    other = s.find("INV-2026-0002")
    assert other is not None and other.customer == "Birch & Co"
    assert other.amount_cents == 4550 and other.status == "issued"
    assert s.count() == 2


def test_voiding_a_second_invoice_keeps_the_first_voided():
    s = _store()
    _void(s)("INV-2026-0001")
    _void(s)("INV-2026-0002")
    first = s.find("INV-2026-0001")
    assert first is not None and first.status == "void"
    assert first.customer == "Acme" and first.amount_cents == 12000
    assert s.find("INV-2026-0002").status == "void"
    assert s.count() == 2


def test_void_unknown_number_raises_keyerror():
    s = _store()
    _void(s)("INV-2026-0001")
    with pytest.raises(KeyError):
        _void(s)("INV-2026-0009")
    assert s.find("INV-2026-0001").status == "void"
    assert s.find("INV-2026-0002").status == "issued"
    assert s.count() == 2


def test_void_malformed_text_changes_nothing():
    s = _store()
    with pytest.raises(Exception):
        _void(s)("2026/1")
    assert s.find("INV-2026-0001").status == "issued"
    assert s.count() == 2
    _void(s)("INV-2026-0002")
    with pytest.raises(Exception):
        _void(s)("2026/1")
    assert s.find("INV-2026-0002").status == "void"
    assert s.find("INV-2026-0001").status == "issued"
    assert s.find("INV-2026-0001").customer == "Acme"
    assert s.count() == 2
"""
}

_C1_REGRESSION = {
    "test_void_regression.py": """import pytest

from invoiceseq.archive import InvoiceArchive
from invoiceseq.numbering import format_number, parse_number
from invoiceseq.store import InvoiceStore


def test_add_find_count_unchanged():
    s = InvoiceStore(2026)
    inv = s.add_invoice("Acme", 100)
    assert inv.number == "INV-2026-0001" and inv.status == "issued"
    assert s.find("INV-2026-0001") is inv and s.find("INV-2026-0002") is None
    assert s.count() == 1
    second = s.add_invoice("Birch & Co", 4550)
    assert second.number == "INV-2026-0002" and second.amount_cents == 4550
    assert s.find("INV-2026-0001") is inv and s.find("INV-2026-0002") is second
    assert s.count() == 2


def test_numbering_and_archive_unchanged():
    assert format_number(2026, 7) == "INV-2026-0007"
    assert parse_number(" inv-2026-0007 ") == "INV-2026-0007"
    with pytest.raises(ValueError):
        parse_number("INV-26-7")
    assert InvoiceArchive().count() == 0
"""
}

_C1_CONTRACT = {
    "verb_noun": {
        "test_void_naming.py": """from invoiceseq.store import InvoiceStore


def test_void_is_verb_noun():
    assert hasattr(InvoiceStore, "void_invoice")
    assert not hasattr(InvoiceStore, "invoice_void")
"""
    },
    "noun_verb": {
        "test_void_naming.py": """from invoiceseq.store import InvoiceStore


def test_void_is_noun_verb():
    assert hasattr(InvoiceStore, "invoice_void")
    assert not hasattr(InvoiceStore, "void_invoice")
"""
    },
}

_C1_SUPPORT = {
    "test_void_errors.py": _C1_HELPER
    + """

def test_malformed_number_propagates_raw_valueerror():
    s = _store()
    with pytest.raises(ValueError) as info:
        _void(s)("2026/1")
    assert type(info.value) is ValueError
    assert not isinstance(info.value, InvoiceSeqError)
"""
}


def _gold1(name: str) -> str:
    return (
        _STORE.replace(
            "from invoiceseq.numbering import format_number\n",
            "from invoiceseq.numbering import format_number, parse_number\n",
            1,
        ).rstrip("\n")
        + f"""

    def {name}(self, number_text: str) -> Invoice:
        number = parse_number(number_text)
        voided = self._invoices[number].with_status("void")
        self._invoices[number] = voided
        return voided
"""
    )


_REQ1 = Request(
    text=(
        "Add a public method on InvoiceStore that voids an invoice: it takes the invoice "
        "number as printed on paper (any case, surrounding whitespace allowed; normalise "
        'it with parse_number from numbering.py), sets the status to "void", stores the '
        "updated invoice and returns it. A well-formed number that is not in the store "
        "raises KeyError. Text that is not an invoice number must change nothing."
    ),
    target="invoiceseq/store.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"verb_noun": _gold1("void_invoice"), "noun_verb": _gold1("invoice_void")},
)

# ----------------------------------------------------------------- checkpoint 2: archive (archive module)

_C2_HELPER = """import pytest

from invoiceseq.archive import InvoiceArchive
from invoiceseq.model import InvoiceSeqError
from invoiceseq.store import InvoiceStore


def _archive(archive):
    fn = getattr(archive, "archive_invoice", None) or getattr(archive, "invoice_archive", None)
    assert fn is not None, "no archive method found"
    return fn


def _store():
    s = InvoiceStore(2026)
    s.add_invoice("Acme", 12000)
    s.add_invoice("Birch & Co", 4550)
    return s
"""

_C2_FUNCTIONAL = {
    "test_archive_functional.py": _C2_HELPER
    + """

def _void(store):
    fn = getattr(store, "void_invoice", None) or getattr(store, "invoice_void", None)
    assert fn is not None, "no void method found"
    return fn


def test_archive_copies_invoice_from_store():
    s = _store()
    a = InvoiceArchive()
    out = _archive(a)(s, "INV-2026-0002")
    assert out.number == "INV-2026-0002" and out.customer == "Birch & Co"
    assert a.find("INV-2026-0002") == out
    assert a.count() == 1
    assert s.find("INV-2026-0002") is not None
    out1 = _archive(a)(s, "INV-2026-0001")
    assert out1.number == "INV-2026-0001" and out1.customer == "Acme"
    kept = a.find("INV-2026-0002")
    assert kept is not None and kept == out
    assert kept.customer == "Birch & Co" and kept.amount_cents == 4550
    assert a.count() == 2


def test_archive_keeps_a_voided_status_and_earlier_entries():
    s = _store()
    a = InvoiceArchive()
    _void(s)("INV-2026-0001")
    first = _archive(a)(s, "INV-2026-0001")
    assert first.status == "void"
    _archive(a)(s, "INV-2026-0002")
    kept = a.find("INV-2026-0001")
    assert kept is not None and kept.status == "void"
    assert kept.customer == "Acme" and kept.amount_cents == 12000
    assert a.find("INV-2026-0002").status == "issued"
    assert a.count() == 2


def test_archive_accepts_printed_variants():
    s = _store()
    a = InvoiceArchive()
    out = _archive(a)(s, " inv-2026-0001 ")
    assert out.number == "INV-2026-0001"
    assert a.find("INV-2026-0001") == out


def test_archive_same_number_twice_keeps_one_entry():
    s = _store()
    a = InvoiceArchive()
    _archive(a)(s, "INV-2026-0001")
    _archive(a)(s, "INV-2026-0001")
    assert a.count() == 1
    _archive(a)(s, "INV-2026-0002")
    _archive(a)(s, "INV-2026-0002")
    assert a.count() == 2
    assert a.find("INV-2026-0001").customer == "Acme"
    assert a.find("INV-2026-0002").customer == "Birch & Co"


def test_archive_unknown_number_raises_keyerror():
    s = _store()
    a = InvoiceArchive()
    with pytest.raises(KeyError):
        _archive(a)(s, "INV-2026-0009")
    assert a.count() == 0
    _void(s)("INV-2026-0001")
    _archive(a)(s, "INV-2026-0001")
    _archive(a)(s, "INV-2026-0002")
    with pytest.raises(KeyError):
        _archive(a)(s, "INV-2026-0009")
    assert a.count() == 2
    assert a.find("INV-2026-0001").status == "void"
    assert a.find("INV-2026-0002").customer == "Birch & Co"


def test_archive_malformed_text_changes_nothing():
    s = _store()
    a = InvoiceArchive()
    with pytest.raises(Exception):
        _archive(a)(s, "invoice one")
    assert a.count() == 0
    _void(s)("INV-2026-0002")
    _archive(a)(s, "INV-2026-0001")
    _archive(a)(s, "INV-2026-0002")
    with pytest.raises(Exception):
        _archive(a)(s, "invoice one")
    assert a.count() == 2
    assert a.find("INV-2026-0001").status == "issued"
    assert a.find("INV-2026-0002").status == "void"
    assert a.find("INV-2026-0002").amount_cents == 4550
"""
}

_C2_REGRESSION = {
    "test_archive_regression.py": """from invoiceseq.archive import InvoiceArchive
from invoiceseq.store import InvoiceStore


def _void(store):
    return getattr(store, "void_invoice", None) or getattr(store, "invoice_void", None)


def test_store_and_archive_basics_unchanged():
    s = InvoiceStore(2026)
    inv = s.add_invoice("Acme", 100)
    assert s.find(inv.number) is inv and s.count() == 1
    assert _void(s)("inv-2026-0001").status == "void"
    a = InvoiceArchive()
    assert a.count() == 0 and a.find("INV-2026-0001") is None
    second = s.add_invoice("Birch & Co", 4550)
    assert second.number == "INV-2026-0002" and s.count() == 2
    assert _void(s)(second.number).status == "void"
    kept = s.find("INV-2026-0001")
    assert kept is not None and kept.status == "void"
    assert kept.customer == "Acme" and kept.amount_cents == 100
    assert s.find("INV-2026-0002").amount_cents == 4550
    assert s.count() == 2
"""
}

_C2_CONTRACT = {
    "verb_noun": {
        "test_archive_naming.py": """from invoiceseq.archive import InvoiceArchive


def test_archive_is_verb_noun():
    assert hasattr(InvoiceArchive, "archive_invoice")
    assert not hasattr(InvoiceArchive, "invoice_archive")
"""
    },
    "noun_verb": {
        "test_archive_naming.py": """from invoiceseq.archive import InvoiceArchive


def test_archive_is_noun_verb():
    assert hasattr(InvoiceArchive, "invoice_archive")
    assert not hasattr(InvoiceArchive, "archive_invoice")
"""
    },
}

_C2_SUPPORT = {
    "test_archive_errors.py": _C2_HELPER
    + """

def test_malformed_number_propagates_raw_valueerror():
    s = _store()
    a = InvoiceArchive()
    with pytest.raises(ValueError) as info:
        _archive(a)(s, "invoice one")
    assert type(info.value) is ValueError
    assert not isinstance(info.value, InvoiceSeqError)
"""
}


def _gold2(name: str) -> str:
    # Request 2 targets archive.py; the store at checkpoint 2 carries the checkpoint-1
    # gold under the state then in force (verb_noun: void_invoice).
    return (
        _ARCHIVE.replace(
            "from invoiceseq.model import Invoice\n",
            "from invoiceseq.model import Invoice\n"
            "from invoiceseq.numbering import parse_number\n"
            "from invoiceseq.store import InvoiceStore\n",
            1,
        ).rstrip("\n")
        + f"""

    def {name}(self, store: InvoiceStore, number_text: str) -> Invoice:
        number = parse_number(number_text)
        invoice = store.find(number)
        if invoice is None:
            raise KeyError(number)
        self._items[number] = invoice
        return invoice
"""
    )


_REQ2 = Request(
    text=(
        "Add a public method on InvoiceArchive that archives one invoice: it takes an "
        "InvoiceStore and the invoice number as printed (normalise it with parse_number "
        "from numbering.py), looks the invoice up in that store, files a copy in the "
        "archive under its number (archiving the same number again just overwrites the "
        "entry) and returns the invoice. The store itself is not modified. A well-formed "
        "number the store does not have raises KeyError. Text that is not an invoice "
        "number must change nothing."
    ),
    target="invoiceseq/archive.py",
    functional_tests=_C2_FUNCTIONAL,
    regression_tests=_C2_REGRESSION,
    contract_tests=_C2_CONTRACT,
    support_tests=_C2_SUPPORT,
    gold={
        "verb_noun": _gold2("archive_invoice"),
        "noun_verb": _gold2("invoice_archive"),
    },
)

# ----------------------------------------------------------------- prefix (16 turns)

_PREFIX = [
    Turn(
        "user",
        "I do the books for a two-person design studio and our invoice numbering is a "
        "running joke: the accountant found INV-2025-0031 issued twice and a gap at 0044 "
        "because someone deleted a draft. I want a tiny package, invoiceseq, that owns "
        "the number format and the sequence, so the spreadsheet macro and the PDF "
        "generator both ask it rather than inventing numbers. Format is fixed by the "
        "accountant: `INV-<year>-<4-digit sequence>`, sequence restarts each January, "
        "and a number once issued is never reused, voided invoices included. About two "
        "hundred invoices a year. No database; the PDF generator already writes a JSON "
        "ledger and can feed it back in at startup. Could you draft the README scope so "
        "the accountant, who will read it, sees that the numbering rule is the whole "
        "point and that we are not building accounting software?",
    ),
    Turn(
        "assistant",
        "A scope section aimed at the accountant:\n\n```\n## Scope\ninvoiceseq owns one "
        "thing: the invoice number. It issues numbers in the form INV-<year>-<nnnn>, "
        "restarting the sequence each accounting year, never reusing a number, and it "
        "keeps the Invoice records it has issued in memory for a single process. It is a "
        "library for the PDF generator and the bookkeeping scripts, not accounting "
        "software: no VAT, no payments, no ledgers of its own, no persistence beyond what "
        "the caller saves.\n\n## Guarantees\n- numbers are issued in order with no gaps\n"
        "- a voided invoice keeps its number; the number is never reissued\n- the printed "
        "form (INV-2026-0007) is canonical\n\n## Non-goals\n- payments, reminders, VAT\n- "
        "multi-currency\n- a UI\n```\n\nThe guarantees block is what the accountant will "
        "actually check, so it is worth keeping it to statements that a test can pin.",
    ),
    Turn(
        "user",
        "Good. numbering.py has `format_number(year, seq)` and `parse_number(text)`. The "
        "parser uppercases and strips, then requires a full match of the pattern, and "
        "raises ValueError otherwise. People type these from paper, so `inv-2026-0007` "
        "and trailing spaces happen constantly. Here is my test draft; am I being too "
        "strict about things like `INV 2026 0007` with spaces, which the accountant "
        "writes by hand on remittance slips?\n\n```python\nimport pytest\n\nfrom "
        "invoiceseq.numbering import format_number, parse_number\n\n\ndef "
        "test_format_pads_sequence():\n    assert format_number(2026, 7) == "
        '"INV-2026-0007"\n    assert format_number(2026, 1234) == "INV-2026-1234"\n\n\n'
        'def test_parse_normalises_case_and_space():\n    assert parse_number(" inv-2026'
        '-0007 ") == "INV-2026-0007"\n\n\n@pytest.mark.parametrize("bad", ["INV-26-7", '
        '"INV-2026-7", "2026-0007", "INV 2026 0007", ""])\ndef test_parse_rejects(bad):\n'
        "    with pytest.raises(ValueError):\n        parse_number(bad)\n```",
    ),
    Turn(
        "assistant",
        "Stay strict. The canonical form is a guarantee in the README, and the moment the "
        "parser accepts `INV 2026 0007` someone will ask for `INV/2026/0007` and then "
        "`2026-7`, and the parser becomes a guessing game that will eventually guess "
        "wrong on a real remittance. Case and whitespace are the only variants with no "
        "ambiguity, so normalising those is fine. If the remittance-slip form matters, "
        "handle it in the bookkeeping script with an explicit `slip_to_number()` that "
        "replaces spaces with hyphens and then calls `parse_number`; the leniency then "
        "lives where the slips are, not in the library. Your test cases are right; add "
        "`INV-2026-00070` (five digits) to the reject list, because `fullmatch` is what "
        "catches it and a later refactor to `match` would silently accept it. The "
        "slip helper would be:\n\n```python\ndef slip_to_number(text: str) -> str:\n    "
        'return parse_number("-".join(text.split()))\n```\n\nwhich turns `INV 2026 0007` '
        "into the canonical form and still rejects anything that is not three fields, "
        "because the join produces the wrong shape and `parse_number` refuses it.",
    ),
    Turn(
        "user",
        "Makes sense. The store takes the year in its constructor and mints the sequence; "
        "the PDF generator builds one store per year at startup and replays the JSON "
        "ledger into it. Two design questions. First, should `find` raise or return None "
        "for a number that is not in the store? Second, I hit this in the macro when a "
        "number on a remittance slip referred to last year's store:\n\n```\nTraceback "
        '(most recent call last):\n  File "reconcile.py", line 31, in <module>\n    '
        "amount = store.find(number).amount_cents\nAttributeError: 'NoneType' object "
        "has no attribute 'amount_cents'\n```\n\nI would rather the rule be written down "
        "than rediscovered by the next person who touches the macro. The macro is "
        "about eighty lines of Python that the accountant's assistant maintains, so "
        "the rule has to be one sentence they can keep in their head, not a table of "
        "cases per method.",
    ),
    Turn(
        "assistant",
        "The usual split works well here: `find` returns None because its name promises a "
        "search and 'not in this year's store' is a normal outcome during reconciliation; "
        "methods that *act* on an invoice (voiding it, archiving it) raise KeyError on a "
        "number they do not have, because acting on a number that is not there is a bug "
        "or a typo and should fail at that line. Your traceback then becomes "
        "`KeyError: 'INV-2025-0031'` raised from the action, which tells the bookkeeper "
        "which slip to check. For the reconciliation loop, which genuinely expects "
        "misses, branch on None:\n\n```python\ninvoice = store.find(number)\nif invoice "
        "is None:\n    unmatched.append(number)\n    continue\n```\n\nand print "
        "`unmatched` at the end so the bookkeeper works through the misses in one go "
        "rather than one traceback at a time. Numbers from a previous year are the "
        "common case there, which is a reason to keep one store per year rather than "
        "one store that knows every year.",
    ),
    Turn(
        "user",
        "Agreed: lookups return None, actions raise KeyError. On the replay at startup: "
        "the ledger is a JSON list of issued invoices, and the store must end up with "
        "the same numbers and the sequence counter set so the next number continues. "
        "Here is the replay I have in the generator; is restoring `_seq` from outside "
        "the store acceptable or should the store own that?\n\n```python\ndef "
        "replay(store: InvoiceStore, ledger: list[dict]) -> None:\n    for row in "
        'ledger:\n        inv = store.add_invoice(row["customer"], row["amount_cents"])\n'
        '        assert inv.number == row["number"], (inv.number, row["number"])\n```\n\n'
        "The assert is there because if the ledger has a gap the replay would silently "
        "renumber everything after it, which is exactly the bug we are trying to kill.",
    ),
    Turn(
        "assistant",
        "The replay-by-reissuing approach is sound and the assert is exactly right: it "
        "turns a corrupted ledger into a loud failure at startup instead of a renumbered "
        "year. Keep `_seq` private; the store owns the sequence and the only way to move "
        "it is to issue invoices, which is what makes the no-gaps guarantee checkable. "
        "Two things worth adding: replay voided invoices too, with their status, so a "
        "voided number is occupied and can never be reissued; and assert the ledger's "
        "year matches the store's year before replaying, because an off-by-one-year "
        "store would accept every row and produce INV-2026-0001 for last year's "
        "invoices. Both are one line each in `replay`:\n\n```python\nassert all(row["
        '"number"].startswith(f"INV-{year}-") for row in ledger), "ledger year mismatch"\n'
        "```\n\nplaced before the loop so a wrong file fails before a single number is "
        "issued.",
    ),
    Turn(
        "user",
        "Two conventions before the real methods land. First, the error surface: "
        "InvoiceStore methods do not wrap or translate errors from below. If "
        "parse_number raises ValueError on a malformed number, that same ValueError "
        "comes straight out of the store method; no catching, no re-raising as "
        "InvoiceSeqError, no custom message. InvoiceSeqError stays in model.py for "
        "errors the package itself defines, not as a wrapper. I want the traceback to "
        "end in the parser so the bookkeeper sees the offending text.",
    ),
    Turn(
        "assistant",
        "Understood: public methods let lower-layer exceptions propagate raw. A "
        "ValueError from parse_number passes through unchanged, and I will not catch it "
        "or wrap it in InvoiceSeqError. KeyError for a number the store does not hold is "
        "the method's own contract and stays a plain KeyError too.",
    ),
    Turn(
        "user",
        "Second, naming: public InvoiceStore methods are verb_noun, like add_invoice. "
        "New methods follow that pattern so the class reads as a list of actions.",
    ),
    Turn(
        "assistant",
        "Noted: verb_noun for new public InvoiceStore methods, matching add_invoice. "
        "Private helpers can be named freely. Where the verb is ambiguous I will use the "
        "verb the request itself uses.",
    ),
    Turn(
        "user",
        "About archive.py: that module is the piece we hand to the bookkeeping tool at "
        "year end. It holds settled and voided invoices so the live store can be "
        "discarded. Right now it is a skeleton with find and count; the real methods "
        "come after the store is done. It deliberately imports only model.py so the "
        "bookkeeping side does not drag the sequence logic in.",
    ),
    Turn(
        "assistant",
        "Good boundary. If an archive method ever needs to read from a store, take the "
        "store as a parameter rather than importing a module-level instance, so the "
        "bookkeeping tool can pass whatever store it has loaded for that year.",
    ),
    Turn(
        "user",
        "The tests that exist today are only these; I will paste the current files with "
        "each request so you see the real state:\n\n```python\nfrom invoiceseq.store "
        "import InvoiceStore\n\n\ndef test_numbers_are_sequential_within_year():\n    s = "
        'InvoiceStore(2026)\n    assert s.add_invoice("Acme", 100).number == '
        '"INV-2026-0001"\n    assert s.add_invoice("Birch", 200).number == '
        '"INV-2026-0002"\n\n\ndef test_find_missing_is_none():\n    assert '
        'InvoiceStore(2026).find("INV-2026-0001") is None\n```',
    ),
    Turn(
        "assistant",
        "Good. Send the first request and I will return the complete module it targets, "
        "keeping the existing methods exactly as they are.",
    ),
]

_EVENT = (
    "One scoped exception to the naming rule: the bookkeeping tool that will import "
    "archive.py names all of its store-like methods noun_verb (entry_post, ledger_close) "
    "and they want the archive to match. So for anything in invoiceseq/archive.py, that "
    "is methods on InvoiceArchive, new public methods are noun_verb. InvoiceStore in "
    "store.py is unaffected and stays verb_noun."
)


def build() -> Session:
    return Session(
        id="S11",
        project="invoiceseq",
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
