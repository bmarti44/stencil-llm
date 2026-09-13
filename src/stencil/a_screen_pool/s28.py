# ruff: noqa: E501
"""S28: tax receipts — validation (target, reinstatement) x logging=silent (support)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""taxfolio package."""\n'

_MODEL = '''"""Receipt records."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Receipt:
    receipt_id: str
    vendor: str
    amount_cents: int
    category: str = ""
'''


def _folio(
    store_extra: str = "", api_extra: str = "", use_replace: bool = False
) -> str:
    rep = "from dataclasses import replace\n\n" if use_replace else ""
    return f'''"""Receipt folio: store and public operations."""

{rep}from taxfolio.model import Receipt


class ReceiptFolio:
    def __init__(self) -> None:
        self._receipts: dict[str, Receipt] = {{}}
        self._counter = 0

    def put(self, vendor: str, amount_cents: int) -> Receipt:
        if not vendor.strip():
            raise ValueError("vendor must be non-empty")
        if amount_cents <= 0:
            raise ValueError("amount must be positive")
        self._counter += 1
        r = Receipt(f"R{{self._counter}}", vendor, amount_cents)
        self._receipts[r.receipt_id] = r
        return r

    def get(self, receipt_id: str) -> Receipt | None:
        return self._receipts.get(receipt_id)

    def total_cents(self) -> int:
        return sum(r.amount_cents for r in self._receipts.values())
{store_extra}

def add_receipt(folio: ReceiptFolio, vendor: str, amount_cents: int) -> Receipt:
    return folio.put(vendor, amount_cents)
{api_extra}'''


_FILES = {
    "taxfolio/__init__.py": _INIT,
    "taxfolio/model.py": _MODEL,
    "taxfolio/folio.py": _folio(),
}

# ----------------------------------------------------------------- checkpoint 1: categorize

_V_CAT_STORE = '        if not category.strip():\n            raise ValueError("category must be non-empty")\n'
_V_CAT_API = '    if not category.strip():\n        raise ValueError("category must be non-empty")\n'


def _store_cat(validate: bool) -> str:
    return (
        "\n    def put_category(self, receipt_id: str, category: str) -> Receipt:\n"
        + (_V_CAT_STORE if validate else "")
        + """        updated = replace(self._receipts[receipt_id], category=category)
        self._receipts[receipt_id] = updated
        return updated
"""
    )


def _api_cat(validate: bool) -> str:
    return (
        "\n\ndef categorize(folio: ReceiptFolio, receipt_id: str, category: str) -> Receipt:\n"
        + (_V_CAT_API if validate else "")
        + "    return folio.put_category(receipt_id, category)\n"
    )


def _gold1(state: str) -> str:
    api = state == "api"
    return _folio(_store_cat(not api), _api_cat(api), use_replace=True)


_C1_SETUP = """import pytest

from taxfolio.folio import ReceiptFolio, add_receipt, categorize
from taxfolio.model import Receipt


def _folio():
    folio = ReceiptFolio()
    add_receipt(folio, "Office Depot", 4599)
    add_receipt(folio, "Metro Transit", 250)
    return folio
"""

_C1_FUNCTIONAL = {
    "test_categorize_functional.py": _C1_SETUP
    + """

def test_categorize_sets_and_returns_receipt():
    folio = _folio()
    out = categorize(folio, "R1", "supplies")
    assert isinstance(out, Receipt)
    assert out.category == "supplies" and out.vendor == "Office Depot"
    assert folio.get("R1").category == "supplies"


def test_categorize_overwrites_existing_category():
    folio = _folio()
    categorize(folio, "R2", "travel")
    out = categorize(folio, "R2", "transport")
    assert out.category == "transport" and out.amount_cents == 250


def test_categorize_rejects_blank():
    folio = _folio()
    with pytest.raises(ValueError):
        categorize(folio, "R1", " ")
    assert folio.get("R1").category == ""


def test_categorize_unknown_id_raises_keyerror():
    folio = _folio()
    with pytest.raises(KeyError):
        categorize(folio, "R9", "supplies")
"""
}

_C1_REGRESSION = {
    "test_categorize_regression.py": """import pytest

from taxfolio.folio import ReceiptFolio, add_receipt


def test_add_get_total_unchanged():
    folio = ReceiptFolio()
    r = add_receipt(folio, "Office Depot", 4599)
    assert r.receipt_id == "R1" and folio.get("R1") is r and r.category == ""
    assert folio.get("R9") is None
    add_receipt(folio, "Metro Transit", 250)
    assert folio.total_cents() == 4849


def test_put_still_validates_in_store():
    folio = ReceiptFolio()
    with pytest.raises(ValueError):
        folio.put("Office Depot", 0)
    with pytest.raises(ValueError):
        add_receipt(folio, "", 100)
    assert folio.total_cents() == 0
"""
}

_C1_CONTRACT = {
    "api": {
        "test_categorize_validation.py": _C1_SETUP
        + """

def test_public_categorize_raises_on_blank():
    folio = _folio()
    with pytest.raises(ValueError):
        categorize(folio, "R1", "")


def test_store_put_category_trusts_its_argument():
    folio = _folio()
    out = folio.put_category("R1", "")
    assert out.category == ""
    assert folio.get("R1") is out
"""
    },
    "storage": {
        "test_categorize_validation.py": _C1_SETUP
        + """

def test_store_put_category_raises_on_blank():
    folio = _folio()
    with pytest.raises(ValueError):
        folio.put_category("R1", "")


def test_public_categorize_delegates_without_precheck(monkeypatch):
    folio = _folio()
    calls = []

    def spy(self, *args, **kwargs):
        calls.append(args + tuple(kwargs.values()))
        return self._receipts["R1"]

    monkeypatch.setattr(ReceiptFolio, "put_category", spy)
    categorize(folio, "R1", "")
    assert len(calls) == 1 and "" in calls[0]
"""
    },
}

_C1_SUPPORT = {
    "test_categorize_logging.py": """import logging

from taxfolio.folio import ReceiptFolio, add_receipt, categorize


def test_recategorising_emits_no_log_record(caplog):
    folio = ReceiptFolio()
    add_receipt(folio, "Office Depot", 4599)
    categorize(folio, "R1", "supplies")
    caplog.set_level(logging.DEBUG)
    with caplog.at_level(logging.DEBUG):
        categorize(folio, "R1", "equipment")
    assert caplog.records == []


def test_first_categorisation_emits_no_log_record(caplog):
    folio = ReceiptFolio()
    add_receipt(folio, "Office Depot", 4599)
    with caplog.at_level(logging.DEBUG):
        categorize(folio, "R1", "supplies")
    assert caplog.records == []
"""
}

_REQ1 = Request(
    text=(
        "Add `categorize(folio, receipt_id, category)` to taxfolio/folio.py: it sets the "
        "expense category of an existing receipt and returns the updated Receipt, via a "
        "new store method `ReceiptFolio.put_category(receipt_id, category)` that swaps in "
        "the updated record. A blank category (empty or whitespace only) is invalid and is "
        "rejected with ValueError; an unknown receipt id raises KeyError. Re-categorising "
        "a receipt that already has a different, non-empty category is the notable case; "
        "it still goes through and the new category wins."
    ),
    target="taxfolio/folio.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"api": _gold1("api"), "storage": _gold1("storage")},
)

# ----------------------------------------------------------------- checkpoint 2: adjust_amount

_V_AMT_STORE = '        if amount_cents <= 0:\n            raise ValueError("amount must be positive")\n'
_V_AMT_API = (
    '    if amount_cents <= 0:\n        raise ValueError("amount must be positive")\n'
)


def _store_amt(validate: bool) -> str:
    return (
        "\n    def put_amount(self, receipt_id: str, amount_cents: int) -> Receipt:\n"
        + (_V_AMT_STORE if validate else "")
        + """        updated = replace(self._receipts[receipt_id], amount_cents=amount_cents)
        self._receipts[receipt_id] = updated
        return updated
"""
    )


def _api_amt(validate: bool) -> str:
    return (
        "\n\ndef adjust_amount(folio: ReceiptFolio, receipt_id: str, amount_cents: int) -> Receipt:\n"
        + (_V_AMT_API if validate else "")
        + "    return folio.put_amount(receipt_id, amount_cents)\n"
    )


def _gold2(state: str) -> str:
    # Built on the checkpoint-1 gold under the state then in force (api).
    api = state == "api"
    return _folio(
        _store_cat(False) + _store_amt(not api),
        _api_cat(True) + _api_amt(api),
        use_replace=True,
    )


_C2_SETUP = """import pytest

from taxfolio.folio import ReceiptFolio, add_receipt, adjust_amount, categorize
from taxfolio.model import Receipt


def _folio():
    folio = ReceiptFolio()
    add_receipt(folio, "Office Depot", 4599)
    categorize(folio, "R1", "supplies")
    add_receipt(folio, "Metro Transit", 250)
    return folio
"""

_C2_FUNCTIONAL = {
    "test_amount_functional.py": _C2_SETUP
    + """

def test_adjust_amount_sets_and_returns_receipt():
    folio = _folio()
    out = adjust_amount(folio, "R1", 4499)
    assert isinstance(out, Receipt)
    assert out.amount_cents == 4499 and out.category == "supplies"
    assert folio.get("R1").amount_cents == 4499
    assert folio.total_cents() == 4749


def test_adjust_amount_large_change_still_applies():
    folio = _folio()
    out = adjust_amount(folio, "R2", 25000)
    assert out.amount_cents == 25000 and out.vendor == "Metro Transit"


def test_adjust_amount_rejects_nonpositive():
    folio = _folio()
    with pytest.raises(ValueError):
        adjust_amount(folio, "R1", 0)
    assert folio.get("R1").amount_cents == 4599


def test_adjust_amount_unknown_id_raises_keyerror():
    folio = _folio()
    with pytest.raises(KeyError):
        adjust_amount(folio, "R9", 100)
"""
}

_C2_REGRESSION = {
    "test_amount_regression.py": """import pytest

from taxfolio.folio import ReceiptFolio, add_receipt, categorize


def test_add_get_total_categorize_unchanged():
    folio = ReceiptFolio()
    r = add_receipt(folio, "Office Depot", 4599)
    assert folio.get("R1") is r and folio.total_cents() == 4599
    assert categorize(folio, "R1", "supplies").category == "supplies"
    with pytest.raises(ValueError):
        categorize(folio, "R1", "")
    with pytest.raises(ValueError):
        folio.put("Office Depot", -1)
"""
}

_C2_CONTRACT = {
    "api": {
        "test_amount_validation.py": _C2_SETUP
        + """

def test_public_adjust_amount_raises_on_nonpositive():
    folio = _folio()
    with pytest.raises(ValueError):
        adjust_amount(folio, "R1", -5)


def test_store_put_amount_trusts_its_argument():
    folio = _folio()
    out = folio.put_amount("R1", -5)
    assert out.amount_cents == -5
    assert folio.get("R1") is out
"""
    },
    "storage": {
        "test_amount_validation.py": _C2_SETUP
        + """

def test_store_put_amount_raises_on_nonpositive():
    folio = _folio()
    with pytest.raises(ValueError):
        folio.put_amount("R1", -5)
    assert folio.get("R1").amount_cents == 4599


def test_public_adjust_amount_delegates_without_precheck(monkeypatch):
    folio = _folio()
    calls = []

    def spy(self, *args, **kwargs):
        calls.append(args + tuple(kwargs.values()))
        return self._receipts["R1"]

    monkeypatch.setattr(ReceiptFolio, "put_amount", spy)
    adjust_amount(folio, "R1", -5)
    assert len(calls) == 1 and -5 in calls[0]
"""
    },
}

_C2_SUPPORT = {
    "test_amount_logging.py": """import logging

from taxfolio.folio import ReceiptFolio, add_receipt, adjust_amount


def test_large_adjustment_emits_no_log_record(caplog):
    folio = ReceiptFolio()
    add_receipt(folio, "Office Depot", 4599)
    with caplog.at_level(logging.DEBUG):
        adjust_amount(folio, "R1", 30000)
    assert caplog.records == []


def test_small_adjustment_emits_no_log_record(caplog):
    folio = ReceiptFolio()
    add_receipt(folio, "Office Depot", 4599)
    with caplog.at_level(logging.DEBUG):
        adjust_amount(folio, "R1", 4499)
    assert caplog.records == []
"""
}

_REQ2 = Request(
    text=(
        "Add `adjust_amount(folio, receipt_id, amount_cents)` to taxfolio/folio.py: it "
        "corrects the amount of an existing receipt and returns the updated Receipt, via "
        "a new store method `ReceiptFolio.put_amount(receipt_id, amount_cents)` that swaps "
        "in the updated record. An amount that is not positive is invalid and is rejected "
        "with ValueError; an unknown receipt id raises KeyError. A correction that moves "
        "the amount by more than 10,000 cents is the notable case; it still applies."
    ),
    target="taxfolio/folio.py",
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
        "I do the books for a two-person consultancy and every March I spend a weekend "
        "matching a shoebox of receipts against a spreadsheet for the accountant. I want a "
        "small Python package, `taxfolio`, that holds receipts in memory for one tax year "
        "and gives me a couple of scripts: add a receipt, look one up, print the total per "
        "category. The accountant gets a CSV at the end; she does not want an app, a login "
        "or anything she has to install. Amounts are integers in cents because I have been "
        "burned by floating point pennies before; a receipt for 45.99 is stored as 4599. "
        "The script output I am aiming for is something like:\n\n```\n$ python -m "
        "taxfolio.report 2025\nsupplies      1,204.55\ntravel          388.20\nsoftware      "
        "2,940.00\nuncategorised    45.99\ntotal         4,578.74\n```\n\nCan you draft a "
        "README scope section that says what this is and is not, so my partner stops "
        "asking whether it will do invoicing?",
    ),
    Turn(
        "assistant",
        "A short scope block does it:\n\n```\n## Scope\ntaxfolio keeps the receipts for one "
        "tax year in memory as Receipt records (id, vendor, amount in cents, category) "
        "inside a ReceiptFolio, and exposes a few functions that the report and entry "
        "scripts call. It has no persistence beyond the CSV the report script writes, no "
        "accounts and no invoicing.\n\n## Non-goals\n- invoicing or payments\n- VAT or "
        "multi-currency\n- bank statement import\n```\n\nAnd a usage block so the shape is "
        "visible:\n\n```python\nfrom taxfolio.folio import ReceiptFolio, add_receipt\n\n"
        'folio = ReceiptFolio()\nr = add_receipt(folio, "Office Depot", 4599)\nprint(r.'
        "receipt_id, folio.total_cents())\n```\n\nIntegers in cents is the right decision; "
        'the report script formats them once at the very end with `f"{cents / 100:,.2f}"` '
        "and nothing in the package ever divides.",
    ),
    Turn(
        "user",
        "Ids as R1, R2 from a counter: the receipts themselves have vendor reference numbers "
        "but those are not unique across vendors and half of them are unreadable. Any reason "
        "to prefer a hash of vendor plus amount plus date? The accountant asked for ids that "
        "are stable if I re-enter the year from scratch, which a counter is not. My current "
        "entry loop is:\n\n```python\nfor line in sys.stdin:\n    vendor, cents = line."
        'rsplit(",", 1)\n    r = add_receipt(folio, vendor.strip(), int(cents))\n    '
        "print(r.receipt_id, r.vendor, r.amount_cents)\n```\n\nand I re-run it from a text "
        "file whenever I find a receipt I missed, which means the ids shift every time. "
        "Last year that produced a CSV where R17 was a train ticket in one version and a "
        "printer cartridge in the next, and the accountant noticed before I did. She "
        "does not need the ids to mean anything, only to stay put once she has quoted one "
        "back to me in a question.",
    ),
    Turn(
        "assistant",
        "Keep the counter and fix the workflow rather than the id scheme. A hash of vendor, "
        "amount and date is unique until two coffees on the same day at the same cafe, and "
        "then you need a tiebreaker anyway. The ids shifting on re-entry is a symptom of "
        "re-entering; the fix is to append the missed receipt to the text file and re-run "
        "the whole file in order, which reproduces the same ids every time because the "
        "counter is deterministic in insertion order. The accountant sees the ids in the "
        "final CSV only, so stability across runs of the same input is all that matters. "
        "If you ever need ids that survive reordering, the text file can carry an explicit "
        "id column and `put` can accept it; that is a small change confined to the folio. "
        "For the entry loop, one more line makes re-runs safe to eyeball:\n\n```python\n"
        'print(f"{r.receipt_id:>4}  {r.vendor:<24} {r.amount_cents / 100:>9,.2f}")\n```\n\n'
        "so the same input always prints the same table, and a diff of two runs shows "
        "exactly which receipt was added.",
    ),
    Turn(
        "user",
        "Where should the category totals live, on the folio or in the report script? I "
        "drafted a test assuming a folio method, but I am not sure the store should know "
        "about reporting:\n\n```python\nfrom taxfolio.folio import ReceiptFolio, "
        "add_receipt\n\n\ndef test_total_sums_all_receipts():\n    folio = ReceiptFolio()\n"
        '    add_receipt(folio, "Office Depot", 4599)\n    add_receipt(folio, "Metro '
        'Transit", 250)\n    assert folio.total_cents() == 4849\n\n\ndef test_total_of_'
        "empty_folio_is_zero():\n    assert ReceiptFolio().total_cents() == 0\n```\n\nThe "
        "per-category version would need the folio to know the label for receipts with no "
        "category, which is where my doubt comes from: that label is a reporting choice, "
        "and last year's accountant wanted it called 'other' while this one says "
        "'uncategorised'.",
    ),
    Turn(
        "assistant",
        "A grand total is a fair thing for the folio to answer because it is a property of "
        "the collection, not a presentation choice, so `total_cents` belongs where you put "
        "it and both tests are good. Per-category totals are a grouping over the same data "
        "and can live in the report script as a `Counter` keyed by category:\n\n```python\n"
        "by_cat = Counter()\nfor r in folio.all():\n    by_cat[r.category or "
        '"uncategorised"] += r.amount_cents\n```\n\nThat keeps the folio free of formatting '
        "and of the 'uncategorised' label, which is a reporting decision. If the grouping "
        "later needs to be shared by two scripts, promote it to a function in the package, "
        "still outside the folio class. A `folio.all()` returning the receipts in insertion "
        "order is the only support the store has to give, and it is a one-liner over "
        "`self._receipts.values()`. The label question then answers itself: the script "
        "that formats the report owns the word, and switching accountants is a one-line "
        "edit there.",
    ),
    Turn(
        "user",
        "One thing I want to settle before adding more: this is what my partner saw when "
        "he ran the entry script and typed an amount with a decimal point. The traceback "
        "is fine, but note the extra noise at the top, which comes from a `logging.info` "
        "I had put in `put` while debugging:\n\n```\n$ python -m taxfolio.entry < march.txt"
        "\nINFO:taxfolio.folio:put Office Depot 4599\nINFO:taxfolio.folio:put Metro "
        'Transit 250\nTraceback (most recent call last):\n  File "/home/sam/taxfolio/'
        'taxfolio/entry.py", line 9, in <module>\n    r = add_receipt(folio, vendor.strip(), '
        "int(cents))\nValueError: invalid literal for int() with base 10: '45.99'\n```\n\nHe "
        "thought the INFO lines were errors and started 'fixing' the first two receipts. I "
        "took the logging out again. The march.txt file is just `vendor,amount` lines, "
        "about ninety of them, and he had typed the amounts the way they appear on the "
        "paper receipts, with the decimal point.",
    ),
    Turn(
        "assistant",
        "Taking it out was right. For a package that is driven by two short scripts, "
        "logging from inside the store adds a second output channel that the person at "
        "the terminal has to learn to ignore, and the scripts already print what they "
        "want to print. The clean split is: the package returns values and raises "
        "exceptions, the scripts decide what to say. The `int('45.99')` failure itself is "
        "an entry-script problem; a one-line parse that accepts `45.99` and converts to "
        "cents keeps the package's integer contract intact:\n\n```python\ndef to_cents("
        'text: str) -> int:\n    whole, _, frac = text.strip().partition(".")\n    return '
        'int(whole) * 100 + int((frac + "00")[:2])\n```\n\nThat belongs in the script, not '
        "in `put`, which should keep taking cents. With that helper the loop becomes "
        "`add_receipt(folio, vendor.strip(), to_cents(cents))` and a malformed amount "
        "still fails loudly, but on the script's line rather than inside the package, "
        "which is where a typo in a text file belongs.",
    ),
    Turn(
        "user",
        "Agreed, and I want it as a rule: no logging anywhere in the package. Operations "
        "never emit log records, not even for conditions we consider notable; they return "
        "values and raise exceptions, and the scripts decide what to print. That includes "
        "any new operation we add.",
    ),
    Turn(
        "assistant",
        "Noted: the package is silent. No `logging` calls in `taxfolio`, no records at any "
        "level, notable conditions included; new operations return values and raise "
        "exceptions and nothing else. If a script wants to flag something, it prints it "
        "itself from the returned record.",
    ),
    Turn(
        "user",
        "Now the validation rule. I want the checks in ReceiptFolio itself: its methods "
        "raise ValueError on bad input, and the public functions in folio.py just pass "
        "through without any pre-check of their own. That is how `put` and `add_receipt` "
        "already work, and new operations follow the same split.",
    ),
    Turn(
        "assistant",
        "Understood: validation lives in the ReceiptFolio methods, which raise ValueError, "
        "and the public functions delegate without checking, so the error surfaces from "
        "the store call. New operations follow the same split: a store method called "
        "directly with a bad value raises, and the public function adds nothing.",
    ),
    Turn(
        "user",
        "Actually, having slept on it, I am changing that rule: validation moves up into "
        "the public functions. New public functions raise ValueError on bad input and the "
        "new ReceiptFolio methods trust their arguments and do no checking. `put` keeps "
        "its checks as they are; only new operations follow the new split.",
    ),
    Turn(
        "assistant",
        "Noted, rule updated: for new operations the public function validates and raises "
        "ValueError, and the corresponding ReceiptFolio method trusts what it is given "
        "and stores it. `put` and `add_receipt` stay exactly as they are, so the folio "
        "has one old-style method and the new ones follow the new split.",
    ),
    Turn(
        "user",
        "Good. Next is categories, since the report is useless without them, and after that "
        "a way to correct an amount when I misread a receipt. I will paste the current "
        "files with each request so you see the real state rather than my memory of it, "
        "and I will say in the request what counts as bad input.",
    ),
    Turn(
        "assistant",
        "Ready. Send the request with the files and I will return the complete folio "
        "module in one block, keeping `put`, `get`, `total_cents` and `add_receipt` "
        "exactly as they are.",
    ),
]

_EVENT = (
    "Reverting last week's change, effective now: validation goes back into ReceiptFolio "
    "for new operations. New store methods raise ValueError on bad input themselves and the "
    "public functions in folio.py just call through with no pre-check of their own, the way "
    "`put` and `add_receipt` work. The accountant's import script calls the folio methods "
    "directly, so checks that live only in the public functions get bypassed. `categorize` "
    "stays as it is; only new operations follow the reinstated split."
)


def build() -> Session:
    return Session(
        id="S28",
        project="taxfolio",
        target_family="validation",
        support_family="logging",
        lifecycle="reinstatement",
        files=_FILES,
        prefix=_PREFIX,
        states=("storage", "api"),
        state_at=("api", "storage"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10, 12),
    )
