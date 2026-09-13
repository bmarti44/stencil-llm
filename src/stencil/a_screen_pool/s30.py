# ruff: noqa: E501
"""S30: apartment maintenance — validation (target, replacement) x logging=warn (support)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""fixlist package."""\n'

_MODEL = '''"""Work-order records."""

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkOrder:
    order_id: str
    unit: str
    description: str
    priority: str = "normal"
    contractor: str = ""
'''


def _book(
    store_extra: str = "",
    api_extra: str = "",
    extra_imports: str = "",
    logger: str = "",
) -> str:
    return f'''"""Order book: store and public operations."""

{extra_imports}from fixlist.model import WorkOrder
{logger}

class OrderBook:
    def __init__(self) -> None:
        self._orders: dict[str, WorkOrder] = {{}}
        self._counter = 0

    def open(self, unit: str, description: str) -> WorkOrder:
        if not unit.strip() or not description.strip():
            raise ValueError("unit and description must be non-empty")
        self._counter += 1
        order = WorkOrder(f"W{{self._counter}}", unit, description)
        self._orders[order.order_id] = order
        return order

    def get(self, order_id: str) -> WorkOrder | None:
        return self._orders.get(order_id)

    def for_unit(self, unit: str) -> list[WorkOrder]:
        return [o for o in self._orders.values() if o.unit == unit]
{store_extra}

def open_order(book: OrderBook, unit: str, description: str) -> WorkOrder:
    return book.open(unit, description)
{api_extra}'''


_FILES = {
    "fixlist/__init__.py": _INIT,
    "fixlist/model.py": _MODEL,
    "fixlist/book.py": _book(),
}

_IMPORTS = "import logging\nfrom dataclasses import replace\n\n"
_LOGGER = "\nlogger = logging.getLogger(__name__)\n"

# ----------------------------------------------------------------- checkpoint 1: set_priority

_V_PRI_STORE = '        if priority not in ("low", "normal", "urgent"):\n            raise ValueError("priority must be low, normal or urgent")\n'
_V_PRI_API = '    if priority not in ("low", "normal", "urgent"):\n        raise ValueError("priority must be low, normal or urgent")\n'


def _store_pri(validate: bool) -> str:
    return (
        "\n    def put_priority(self, order_id: str, priority: str) -> WorkOrder:\n"
        + (_V_PRI_STORE if validate else "")
        + """        old = self._orders[order_id]
        if priority == "urgent" and old.priority != "urgent":
            logger.warning("order %s raised to urgent", order_id)
        updated = replace(old, priority=priority)
        self._orders[order_id] = updated
        return updated
"""
    )


def _api_pri(validate: bool) -> str:
    return (
        "\n\ndef set_priority(book: OrderBook, order_id: str, priority: str) -> WorkOrder:\n"
        + (_V_PRI_API if validate else "")
        + "    return book.put_priority(order_id, priority)\n"
    )


def _gold1(state: str) -> str:
    api = state == "api"
    return _book(_store_pri(not api), _api_pri(api), _IMPORTS, _LOGGER)


_C1_SETUP = """import pytest

from fixlist.book import OrderBook, open_order, set_priority
from fixlist.model import WorkOrder


def _book():
    book = OrderBook()
    open_order(book, "4B", "kitchen tap drips")
    open_order(book, "2A", "hallway light out")
    return book
"""

_C1_FUNCTIONAL = {
    "test_priority_functional.py": _C1_SETUP
    + """

def test_set_priority_updates_and_returns_order():
    book = _book()
    out = set_priority(book, "W1", "low")
    assert isinstance(out, WorkOrder)
    assert out.priority == "low" and out.unit == "4B" and out.description == "kitchen tap drips"
    assert book.get("W1").priority == "low"


def test_raise_to_urgent_still_applies():
    book = _book()
    out = set_priority(book, "W2", "urgent")
    assert out.priority == "urgent" and book.get("W2").priority == "urgent"


def test_set_priority_rejects_unknown_level():
    book = _book()
    with pytest.raises(ValueError):
        set_priority(book, "W1", "asap")
    assert book.get("W1").priority == "normal"


def test_set_priority_unknown_id_raises_keyerror():
    book = _book()
    with pytest.raises(KeyError):
        set_priority(book, "W9", "low")
"""
}

_C1_REGRESSION = {
    "test_priority_regression.py": """import pytest

from fixlist.book import OrderBook, open_order


def test_open_get_for_unit_unchanged():
    book = OrderBook()
    o = open_order(book, "4B", "kitchen tap drips")
    assert o.order_id == "W1" and book.get("W1") is o
    assert o.priority == "normal" and o.contractor == ""
    assert book.get("W9") is None
    open_order(book, "4B", "window latch broken")
    assert [x.order_id for x in book.for_unit("4B")] == ["W1", "W2"]


def test_open_still_validates_in_store():
    book = OrderBook()
    with pytest.raises(ValueError):
        book.open("4B", "")
    with pytest.raises(ValueError):
        open_order(book, " ", "tap")
    assert book.for_unit("4B") == []
"""
}

_C1_CONTRACT = {
    "api": {
        "test_priority_validation.py": _C1_SETUP
        + """

def test_public_set_priority_raises_on_unknown_level():
    book = _book()
    with pytest.raises(ValueError):
        set_priority(book, "W1", "asap")


def test_store_put_priority_trusts_its_argument():
    book = _book()
    out = book.put_priority("W1", "asap")
    assert out.priority == "asap"
    assert book.get("W1") is out
"""
    },
    "storage": {
        "test_priority_validation.py": _C1_SETUP
        + """

def test_store_put_priority_raises_on_unknown_level():
    book = _book()
    with pytest.raises(ValueError):
        book.put_priority("W1", "asap")
    assert book.get("W1").priority == "normal"


def test_public_set_priority_delegates_without_precheck(monkeypatch):
    book = _book()
    calls = []

    def spy(self, *args, **kwargs):
        calls.append(args + tuple(kwargs.values()))
        return self._orders["W1"]

    monkeypatch.setattr(OrderBook, "put_priority", spy)
    set_priority(book, "W1", "asap")
    assert len(calls) == 1 and "asap" in calls[0]
"""
    },
}

_C1_SUPPORT = {
    "test_priority_logging.py": """import logging

from fixlist.book import OrderBook, open_order, set_priority


def _warnings(caplog):
    return [r for r in caplog.records if r.levelno == logging.WARNING]


def test_raise_to_urgent_emits_exactly_one_warning(caplog):
    book = OrderBook()
    open_order(book, "4B", "kitchen tap drips")
    with caplog.at_level(logging.DEBUG):
        set_priority(book, "W1", "urgent")
    assert len(_warnings(caplog)) == 1


def test_other_priority_changes_emit_no_warning(caplog):
    book = OrderBook()
    open_order(book, "4B", "kitchen tap drips")
    with caplog.at_level(logging.DEBUG):
        set_priority(book, "W1", "low")
        set_priority(book, "W1", "normal")
    assert _warnings(caplog) == []
"""
}

_REQ1 = Request(
    text=(
        "Add `set_priority(book, order_id, priority)` to fixlist/book.py: it changes the "
        "priority of an existing work order and returns the updated WorkOrder, via a new "
        "store method `OrderBook.put_priority(order_id, priority)` that swaps in the "
        'updated record. The only valid priorities are "low", "normal" and "urgent"; '
        "anything else is invalid and is rejected with ValueError; an unknown order id "
        'raises KeyError. Raising an order to "urgent" from a lower priority is the '
        "notable case; it still applies."
    ),
    target="fixlist/book.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"api": _gold1("api"), "storage": _gold1("storage")},
)

# ----------------------------------------------------------------- checkpoint 2: assign_contractor

_V_CON_STORE = '        if not contractor.strip():\n            raise ValueError("contractor must be non-empty")\n'
_V_CON_API = '    if not contractor.strip():\n        raise ValueError("contractor must be non-empty")\n'


def _store_con(validate: bool) -> str:
    return (
        "\n    def put_contractor(self, order_id: str, contractor: str) -> WorkOrder:\n"
        + (_V_CON_STORE if validate else "")
        + """        old = self._orders[order_id]
        if old.contractor and old.contractor != contractor:
            logger.warning("order %s reassigned from %s", order_id, old.contractor)
        updated = replace(old, contractor=contractor)
        self._orders[order_id] = updated
        return updated
"""
    )


def _api_con(validate: bool) -> str:
    return (
        "\n\ndef assign_contractor(book: OrderBook, order_id: str, contractor: str) -> WorkOrder:\n"
        + (_V_CON_API if validate else "")
        + "    return book.put_contractor(order_id, contractor)\n"
    )


def _gold2(state: str) -> str:
    # Built on the checkpoint-1 gold under the state then in force (storage).
    api = state == "api"
    return _book(
        _store_pri(True) + _store_con(not api),
        _api_pri(False) + _api_con(api),
        _IMPORTS,
        _LOGGER,
    )


_C2_SETUP = """import pytest

from fixlist.book import OrderBook, assign_contractor, open_order, set_priority
from fixlist.model import WorkOrder


def _book():
    book = OrderBook()
    open_order(book, "4B", "kitchen tap drips")
    set_priority(book, "W1", "low")
    open_order(book, "2A", "hallway light out")
    return book
"""

_C2_FUNCTIONAL = {
    "test_contractor_functional.py": _C2_SETUP
    + """

def test_assign_contractor_updates_and_returns_order():
    book = _book()
    out = assign_contractor(book, "W1", "Reyes Plumbing")
    assert isinstance(out, WorkOrder)
    assert out.contractor == "Reyes Plumbing" and out.priority == "low" and out.unit == "4B"
    assert book.get("W1").contractor == "Reyes Plumbing"


def test_reassignment_still_applies():
    book = _book()
    assign_contractor(book, "W2", "Sparks Electrical")
    out = assign_contractor(book, "W2", "Delta Electric")
    assert out.contractor == "Delta Electric"


def test_assign_contractor_rejects_blank():
    book = _book()
    with pytest.raises(ValueError):
        assign_contractor(book, "W1", "  ")
    assert book.get("W1").contractor == ""


def test_assign_contractor_unknown_id_raises_keyerror():
    book = _book()
    with pytest.raises(KeyError):
        assign_contractor(book, "W9", "Reyes Plumbing")
"""
}

_C2_REGRESSION = {
    "test_contractor_regression.py": """import pytest

from fixlist.book import OrderBook, open_order, set_priority


def test_open_get_priority_unchanged():
    book = OrderBook()
    o = open_order(book, "4B", "kitchen tap drips")
    assert book.get("W1") is o and book.for_unit("4B") == [o]
    assert set_priority(book, "W1", "urgent").priority == "urgent"
    with pytest.raises(ValueError):
        book.put_priority("W1", "asap")
    with pytest.raises(ValueError):
        book.open("", "tap")
"""
}

_C2_CONTRACT = {
    "api": {
        "test_contractor_validation.py": _C2_SETUP
        + """

def test_public_assign_contractor_raises_on_blank():
    book = _book()
    with pytest.raises(ValueError):
        assign_contractor(book, "W1", "")


def test_store_put_contractor_trusts_its_argument():
    book = _book()
    out = book.put_contractor("W1", "")
    assert out.contractor == ""
    assert book.get("W1") is out
"""
    },
    "storage": {
        "test_contractor_validation.py": _C2_SETUP
        + """

def test_store_put_contractor_raises_on_blank():
    book = _book()
    with pytest.raises(ValueError):
        book.put_contractor("W1", "")


def test_public_assign_contractor_delegates_without_precheck(monkeypatch):
    book = _book()
    calls = []

    def spy(self, *args, **kwargs):
        calls.append(args + tuple(kwargs.values()))
        return self._orders["W1"]

    monkeypatch.setattr(OrderBook, "put_contractor", spy)
    assign_contractor(book, "W1", "")
    assert len(calls) == 1 and "" in calls[0]
"""
    },
}

_C2_SUPPORT = {
    "test_contractor_logging.py": """import logging

from fixlist.book import OrderBook, assign_contractor, open_order


def _warnings(caplog):
    return [r for r in caplog.records if r.levelno == logging.WARNING]


def test_reassignment_emits_exactly_one_warning(caplog):
    book = OrderBook()
    open_order(book, "4B", "kitchen tap drips")
    assign_contractor(book, "W1", "Reyes Plumbing")
    with caplog.at_level(logging.DEBUG):
        assign_contractor(book, "W1", "Delta Plumbing")
    assert len(_warnings(caplog)) == 1


def test_first_assignment_and_same_contractor_emit_no_warning(caplog):
    book = OrderBook()
    open_order(book, "4B", "kitchen tap drips")
    with caplog.at_level(logging.DEBUG):
        assign_contractor(book, "W1", "Reyes Plumbing")
        assign_contractor(book, "W1", "Reyes Plumbing")
    assert _warnings(caplog) == []
"""
}

_REQ2 = Request(
    text=(
        "Add `assign_contractor(book, order_id, contractor)` to fixlist/book.py: it "
        "records which contractor is handling an existing work order and returns the "
        "updated WorkOrder, via a new store method "
        "`OrderBook.put_contractor(order_id, contractor)` that swaps in the updated "
        "record. A blank contractor name (empty or whitespace only) is invalid and is "
        "rejected with ValueError; an unknown order id raises KeyError. Reassigning an "
        "order that already has a different contractor is the notable case; it still "
        "applies and the new name wins."
    ),
    target="fixlist/book.py",
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
        "I manage a 24-unit apartment block for a small landlord and the repair requests "
        "arrive as texts, emails and notes under my door. I want a small Python package, "
        "`fixlist`, that keeps work orders in memory for the current quarter and drives a "
        "couple of scripts: open an order from the terminal, list what is open for a "
        "unit, and print the weekly sheet I hand to the contractors on Monday. No web "
        "portal for tenants yet, no accounting, no photos. The Monday sheet looks like:\n\n"
        "```\nW1   4B  kitchen tap drips          normal   Reyes Plumbing\nW2   2A  "
        "hallway light out           urgent   -\nW3   4B  window latch broken         low   "
        "   -\n```\n\nCan you draft the README scope section? The landlord keeps asking "
        "whether it will invoice contractors, and the honest answer is that a spreadsheet "
        "does that fine and this is only about not losing requests. "
        "The block has two regular contractors, Reyes Plumbing and Sparks Electrical, and a rotating cast for everything else, so the sheet is also how I remember who I already called.",
    ),
    Turn(
        "assistant",
        "A short scope block does it:\n\n```\n## Scope\nfixlist keeps the current "
        "quarter's work orders in memory as WorkOrder records (id, unit, description, "
        "priority, contractor) inside an OrderBook and exposes a few functions the "
        "manager's scripts call. It is a to-do list for repairs: it does not invoice, does "
        "not store photos and has no tenant-facing surface.\n\n## Non-goals\n- invoicing "
        "or contractor payments\n- photo attachments\n- tenant portal\n```\n\nA usage "
        "block:\n\n```python\nfrom fixlist.book import OrderBook, open_order\n\nbook = "
        'OrderBook()\no = open_order(book, "4B", "kitchen tap drips")\nprint(o.order_id, '
        'book.for_unit("4B"))\n```\n\nThe Monday sheet is a formatting job over '
        "`for_unit` for each unit, so it stays in the script and the package never learns "
        "about column widths. "
        "When the portal eventually arrives it can call the same functions; nothing in the scope section has to change for that.",
    ),
    Turn(
        "user",
        "Ids as W1, W2 from a counter: contractors quote the id back on their invoices, "
        "so it must not change once printed. But I sometimes open an order and then realise "
        "it duplicates one from last week. Should the package try to detect duplicates by "
        "unit plus description, or is that my job? My current open script is only:\n\n"
        '```python\nbook = OrderBook()\nfor line in open("orders.txt"):\n    unit, desc '
        '= line.rstrip("\\n").split("\\t", 1)\n    o = open_order(book, unit, desc)\n'
        "    print(o.order_id, o.unit, o.description)\n```\n\nwhich rebuilds the book from "
        "the tab-separated file every time, so the ids are stable as long as I only ever "
        "append to that file. "
        "Appending is the one discipline I trust myself with; editing lines in the middle is how the 3C leak got lost last year. "
        "The file is about two hundred lines by the end of a quarter, and I start a fresh one each January so the counter never gets silly.",
    ),
    Turn(
        "assistant",
        "Leave duplicate detection to you, at least for now. Two orders for '4B kitchen "
        "tap drips' three weeks apart are legitimately two visits, and a package rule "
        "that merges them would be wrong as often as right. The append-only file already "
        "gives you stable ids, which is the property the contractors care about. If you "
        "want a nudge rather than a rule, the open script can print the existing open "
        "orders for the unit before it adds a new one:\n\n```python\nfor existing in "
        'book.for_unit(unit):\n    print("  already open:", existing.order_id, '
        "existing.description)\n```\n\nThat is a script decision, not a package one, and "
        "it keeps `open` doing exactly one thing. If a real duplicate lands, a later "
        "'close as duplicate' operation is the honest fix, and it keeps the id history "
        "intact for the invoices. "
        "Contractors who quote W12 on a bill should always find W12 in the file, even if W12 turned out to be the same tap as W9. "
        "The invoice reconciliation stays a spreadsheet job, exactly as the scope section promises.",
    ),
    Turn(
        "user",
        "Priority levels: I want three, low, normal and urgent, as plain strings rather "
        "than an Enum, because the orders file is typed by hand and I do not want to "
        "explain `Priority.URGENT` to the weekend cover. Here is the test I drafted for "
        "the default:\n\n```python\nfrom fixlist.book import OrderBook, open_order\n\n\n"
        "def test_new_order_defaults_to_normal():\n    book = OrderBook()\n    o = "
        'open_order(book, "4B", "kitchen tap drips")\n    assert o.priority == "normal"\n'
        '    assert o.contractor == ""\n\n\ndef test_for_unit_keeps_insertion_order():\n'
        '    book = OrderBook()\n    open_order(book, "4B", "tap")\n    open_order(book, '
        '"2A", "light")\n    open_order(book, "4B", "latch")\n    assert [o.order_id for o '
        'in book.for_unit("4B")] == ["W1", "W3"]\n```\n\nAnything wrong with strings here?'
        " The weekend cover is usually a neighbour who knows how to open a terminal and nothing more, and the orders file is the only thing she edits. She will type "
        "`urgent`, not `Priority.URGENT`, and I want the tool to meet her there.",
    ),
    Turn(
        "assistant",
        "Strings are fine for three well-known values that people type by hand, and both "
        "tests are good. The cost of strings is that a typo like 'urgnet' is not caught "
        "by the type, so the place that accepts a priority has to check membership "
        "against the three names; that is one line and it gives a better message than an "
        "Enum's `ValueError: 'urgnet' is not a valid Priority` would. Keep the three names "
        "in one tuple in the module so the check and any future listing share it. For "
        "the Monday sheet, sorting by priority is a small map:\n\n```python\nRANK = "
        '{"urgent": 0, "normal": 1, "low": 2}\nrows.sort(key=lambda o: (RANK[o.priority], '
        "o.order_id))\n```\n\nwhich again lives in the script. "
        "If a fourth level ever appears, 'emergency' say, it goes into the tuple and the rank map and nowhere else, and the test for rejecting unknown levels keeps protecting the typo case.",
    ),
    Turn(
        "user",
        "Now the thing that made me start this. Two weeks ago a leak in 3C was logged as "
        "normal on Friday and became urgent on Saturday when the ceiling in 2C started "
        "dripping. Nobody noticed the upgrade until Monday because the change went into "
        "the file with no trace. Here is what the weekend cover saw when she re-ran the "
        "open script after editing the priority by hand:\n\n```\n$ python -m fixlist.open "
        "< orders.txt\nW7 3C bathroom ceiling stain\nW8 2C water dripping from light "
        "fitting\n```\n\nThat is all: two lines, no hint that W7 had been bumped. I do not "
        "want the package to block anything, but I want that kind of change to leave a "
        "mark that a script can surface without me writing print statements in the "
        "store. "
        "The landlord's question afterwards was 'when did it become urgent', and I could not answer it from anything the tool had produced. "
        "The line in the file had simply gone from `3C\tbathroom ceiling stain\tnormal` to `3C\tbathroom ceiling stain\turgent` at some point on Saturday.",
    ),
    Turn(
        "assistant",
        "The right mechanism is a single `logging.warning` from the module logger at the "
        "point where the package knows the change is notable, which is inside the "
        "operation that has both the old and new values in hand. The scripts then decide "
        "what to do with it: the open script can leave logging unconfigured and stay "
        "quiet, and the Monday sheet script can route warnings to stderr with one "
        "`logging.basicConfig(level=logging.WARNING)` call so a bumped order shows up "
        "next to the table. Tests can count the records with `caplog`. Keeping it to "
        "exactly one record per notable change matters: if the same change logged twice, "
        "or logged an info as well, the count stops meaning anything and people start "
        "filtering it out. "
        "The landlord's 'when did it become urgent' then has an answer: the Monday sheet run prints the warning with a timestamp from the logging format. "
        "One record per change also means the weekly count of warnings is a meaningful number on its own. "
        'In the sheet script that is `logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(message)s")`.',
    ),
    Turn(
        "user",
        "Agreed, and let's make it a rule: when an operation hits a condition we have "
        "called notable, it emits exactly one logging.warning through the module logger, "
        "nothing more, and the ordinary path emits no log record at all. Every operation "
        "that names a notable case follows that, existing or new.",
    ),
    Turn(
        "assistant",
        "Noted: notable conditions produce exactly one WARNING record from the module "
        "logger and ordinary calls produce none. New operations that name a notable case "
        "emit that single warning and are otherwise silent, so a `caplog` count of one is "
        "the contract. "
        "The scripts choose whether anyone sees it. "
        "Nothing else in the package touches logging.",
    ),
    Turn(
        "user",
        "Validation rule, so it is written down: the checks live in OrderBook itself. Its "
        "methods raise ValueError on bad input, the way `open` does now, and the public "
        "functions in book.py just pass through without any pre-check of their own. New "
        "operations follow the same split.",
    ),
    Turn(
        "assistant",
        "Understood: validation belongs to the OrderBook methods, which raise ValueError, "
        "and the public functions delegate without checking, so the error surfaces from "
        "the store call. New operations follow the same split: a store method called "
        "directly with a bad value raises, and the public function adds nothing. "
        "`open` and `open_order` are the template. "
        "Lookups keep returning None; actions on an unknown id raise KeyError.",
    ),
    Turn(
        "user",
        "For reference, the validation tests that exist today, both against the store:\n\n"
        "```python\ndef test_open_rejects_blank_unit():\n    with pytest.raises(ValueError)"
        ':\n        OrderBook().open(" ", "tap")\n\n\ndef test_open_rejects_blank_'
        "description():\n    with pytest.raises(ValueError):\n        OrderBook().open("
        '"4B", "")\n```',
    ),
    Turn(
        "assistant",
        "Both pin the check to the store. A third through `open_order` with the same bad "
        "input would pin that the public function lets the store's ValueError through "
        "rather than catching it, which is the other half of the split. "
        "It is the half that tends to erode when someone adds a friendly check 'just in case'.",
    ),
    Turn(
        "user",
        "Good. First feature: changing the priority of an existing order, since the 3C "
        "case will happen again. After that, recording which contractor has an order, for "
        "the Monday sheet. I will paste the current files with each request.",
    ),
    Turn(
        "assistant",
        "Ready. Send the request with the files and I will return the complete book "
        "module, keeping `open`, `get`, `for_unit` and `open_order` as they are. "
        "I will keep the three priority names in one place.",
    ),
]

_EVENT = (
    "Change of convention, effective now: validation moves up into the public functions in "
    "book.py. New public functions raise ValueError on bad input themselves, and the new "
    "OrderBook methods trust their arguments and do no checking. Existing methods keep "
    "their checks where they are; only new operations follow the new split. The reason is "
    "the tenant portal we are adding calls the public functions only, and we want its error "
    "messages to come from one place."
)


def build() -> Session:
    return Session(
        id="S30",
        project="fixlist",
        target_family="validation",
        support_family="logging",
        lifecycle="replacement",
        files=_FILES,
        prefix=_PREFIX,
        states=("storage", "api"),
        state_at=("storage", "api"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10),
    )
