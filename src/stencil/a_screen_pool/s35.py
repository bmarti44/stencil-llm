# ruff: noqa: E501
"""S35: bakery orders — missing_record (target, scope) x return_shape (support)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""bakeorders package."""\n'

_MODEL = '''"""Counter pre-orders."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Order:
    order_id: str
    customer: str
    item: str
    qty: int
    paid_p: int = 0
    status: str = "placed"
    note: str = ""
'''

_ORDERS = '''"""In-memory order book for the bakery counter."""

from dataclasses import replace

from bakeorders.model import Order


class OrderBook:
    def __init__(self):
        self._orders = {}
        self._n = 0

    def place(self, customer, item, qty, paid_p=0):
        self._n += 1
        order = Order(f"O{self._n}", customer, item, qty, paid_p)
        self._orders[order.order_id] = order
        return order

    def find(self, order_id):
        return self._orders.get(order_id)

    def save(self, order):
        self._orders[order.order_id] = order

    def ready(self, order_id):
        order = self._orders.get(order_id)
        if order is None:
            return None
        updated = replace(order, status="ready")
        self.save(updated)
        return updated
'''

_REFUNDS = '''"""Refund operations: money goes back to the customer against an order."""

REASONS = ("stale", "wrong_item", "late")


def refundable(order):
    return order.paid_p > 0 and order.status != "refunded"
'''

_FILES = {
    "bakeorders/__init__.py": _INIT,
    "bakeorders/model.py": _MODEL,
    "bakeorders/orders.py": _ORDERS,
    "bakeorders/refunds.py": _REFUNDS,
}

# ----------------------------------------------------------------- checkpoint 1: collect

_C1_FUNCTIONAL = {
    "test_collect_functional.py": """from bakeorders.orders import OrderBook


def test_collect_sets_status_and_stores():
    book = OrderBook()
    order = book.place("Mrs Okafor", "sourdough", 2, 900)
    out = book.collect(order.order_id)
    assert out.status == "collected"
    assert book.find(order.order_id).status == "collected"


def test_collect_keeps_customer_item_and_payment():
    book = OrderBook()
    order = book.place("Dev", "birthday cake", 1, 2400)
    book.ready(order.order_id)
    out = book.collect(order.order_id)
    assert out.customer == "Dev" and out.item == "birthday cake"
    assert out.qty == 1 and out.paid_p == 2400 and out.order_id == order.order_id
"""
}

_C1_REGRESSION = {
    "test_collect_regression.py": """from bakeorders.orders import OrderBook
from bakeorders.refunds import refundable


def test_place_find_save_ready_unchanged():
    book = OrderBook()
    order = book.place("Mrs Okafor", "sourdough", 2, 900)
    assert order.order_id == "O1" and order.status == "placed" and order.note == ""
    assert book.find("O1") is order
    assert book.find("O9") is None
    assert book.ready("O1").status == "ready"
    assert book.ready("O9") is None
    assert refundable(book.find("O1")) is True
"""
}

_C1_CONTRACT = {
    "none": {
        "test_collect_missing.py": """from bakeorders.orders import OrderBook


def test_collect_unknown_returns_none_and_changes_nothing():
    book = OrderBook()
    order = book.place("Mrs Okafor", "sourdough", 2, 900)
    assert book.collect("O99") is None
    assert book.find("O99") is None
    assert book.find(order.order_id).status == "placed"
"""
    },
    "raise": {
        "test_collect_missing.py": """import pytest

from bakeorders.orders import OrderBook


def test_collect_unknown_raises_keyerror():
    book = OrderBook()
    book.place("Mrs Okafor", "sourdough", 2, 900)
    with pytest.raises(KeyError):
        book.collect("O99")
"""
    },
}

_C1_SUPPORT = {
    "test_collect_shape.py": """from bakeorders.model import Order
from bakeorders.orders import OrderBook


def test_collect_returns_order_dataclass_not_dict():
    book = OrderBook()
    order = book.place("Mrs Okafor", "sourdough", 2, 900)
    out = book.collect(order.order_id)
    assert isinstance(out, Order)
    assert not isinstance(out, (dict, tuple))
"""
}

_LOOKUP_BOOK = {
    "none": (
        "        order = self._orders.get(order_id)\n"
        "        if order is None:\n"
        "            return None\n"
    ),
    "raise": "        order = self._orders[order_id]\n",
}


def _gold1(state: str) -> str:
    return (
        _ORDERS.rstrip("\n")
        + "\n\n    def collect(self, order_id):\n"
        + _LOOKUP_BOOK[state]
        + '        updated = replace(order, status="collected")\n'
        "        self.save(updated)\n"
        "        return updated\n"
    )


_REQ1 = Request(
    text=(
        "Add a public method `collect(order_id)` on OrderBook for when the customer picks "
        'the order up: it marks the order status "collected", saves the updated Order '
        "under the same id and returns it."
    ),
    target="bakeorders/orders.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"none": _gold1("none"), "raise": _gold1("raise")},
)

# ----------------------------------------------------------------- checkpoint 2: refund

_C2_FUNCTIONAL = {
    "test_refund_functional.py": """from bakeorders.orders import OrderBook
from bakeorders.refunds import refund, refundable


def test_refund_marks_refunded_clears_payment_and_stores():
    book = OrderBook()
    order = book.place("Mrs Okafor", "sourdough", 2, 900)
    out = refund(book, order.order_id, "stale")
    assert out.status == "refunded" and out.paid_p == 0 and out.note == "stale"
    assert book.find(order.order_id).status == "refunded"
    assert refundable(book.find(order.order_id)) is False


def test_refund_keeps_identity_and_item():
    book = OrderBook()
    order = book.place("Dev", "birthday cake", 1, 2400)
    book.collect(order.order_id)
    out = refund(book, order.order_id, "wrong_item")
    assert out.order_id == order.order_id and out.customer == "Dev"
    assert out.item == "birthday cake" and out.qty == 1
"""
}

_C2_REGRESSION = {
    "test_refund_regression.py": """from bakeorders.orders import OrderBook
from bakeorders.refunds import REASONS, refundable


def test_book_and_helpers_unchanged():
    book = OrderBook()
    order = book.place("Mrs Okafor", "sourdough", 2, 900)
    assert book.find("O1") is order and book.find("O9") is None
    assert book.ready("O1").status == "ready"
    assert book.collect("O1").status == "collected"
    assert book.ready("O9") is None and book.collect("O9") is None
    assert refundable(book.find("O1")) is True
    assert REASONS == ("stale", "wrong_item", "late")
"""
}

_C2_CONTRACT = {
    "none": {
        "test_refund_missing.py": """from bakeorders.orders import OrderBook
from bakeorders.refunds import refund


def test_refund_unknown_returns_none_and_changes_nothing():
    book = OrderBook()
    order = book.place("Mrs Okafor", "sourdough", 2, 900)
    assert refund(book, "O99", "stale") is None
    assert book.find("O99") is None
    assert book.find(order.order_id).paid_p == 900
    assert book.find(order.order_id).status == "placed"
"""
    },
    "raise": {
        "test_refund_missing.py": """import pytest

from bakeorders.orders import OrderBook
from bakeorders.refunds import refund


def test_refund_unknown_raises_keyerror():
    book = OrderBook()
    book.place("Mrs Okafor", "sourdough", 2, 900)
    with pytest.raises(KeyError):
        refund(book, "O99", "stale")
"""
    },
}

_C2_SUPPORT = {
    "test_refund_shape.py": """from bakeorders.model import Order
from bakeorders.orders import OrderBook
from bakeorders.refunds import refund


def test_refund_returns_order_dataclass_not_dict():
    book = OrderBook()
    order = book.place("Mrs Okafor", "sourdough", 2, 900)
    out = refund(book, order.order_id, "late")
    assert isinstance(out, Order)
    assert not isinstance(out, (dict, tuple))
"""
}

_LOOKUP_REFUND = {
    "none": (
        "    order = book.find(order_id)\n    if order is None:\n        return None\n"
    ),
    "raise": (
        "    order = book.find(order_id)\n"
        "    if order is None:\n"
        "        raise KeyError(order_id)\n"
    ),
}


def _gold2(state: str) -> str:
    # Request 2 targets refunds.py; the book already carries the checkpoint-1 gold (none).
    base = _REFUNDS.replace(
        '"""Refund operations: money goes back to the customer against an order."""\n',
        '"""Refund operations: money goes back to the customer against an order."""\n\n'
        "from dataclasses import replace\n",
        1,
    )
    return (
        base.rstrip("\n")
        + "\n\n\ndef refund(book, order_id, reason):\n"
        + _LOOKUP_REFUND[state]
        + '    refunded = replace(order, status="refunded", paid_p=0, note=reason)\n'
        "    book.save(refunded)\n"
        "    return refunded\n"
    )


_REQ2 = Request(
    text=(
        "Add a public function `refund(book, order_id, reason)` to refunds.py: it marks the "
        'order status "refunded", sets paid_p to 0 (the cash goes back across the counter), '
        "stores the reason in the order's note, saves the updated Order in the book and "
        "returns it."
    ),
    target="bakeorders/refunds.py",
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
        "I run a small bakery and I'm writing a package called bakeorders to track counter "
        "pre-orders: birthday cakes, big sourdough orders for the Saturday cafe, that sort "
        "of thing. Today it is a clipboard by the till, and twice this month a cake was "
        "baked twice because two of us wrote the same order on different pages. I want an "
        "in-memory OrderBook that my morning script can print the day's list from, "
        "something like:\n\n```\n$ python -m bakeorders.today\nO1  Mrs Okafor   sourdough x2"
        "      paid £9.00   [placed]\nO2  Dev          birthday cake x1  paid £24.00  "
        "[ready]\n```\n\nCould you draft the README scope section first? My accountant "
        "heard 'orders' and asked whether it does VAT and end-of-day till reconciliation, "
        "and the answer is emphatically no; it is a list of who ordered what and whether "
        "they have picked it up. I bake, I do not want to run a point-of-sale system.",
    ),
    Turn(
        "assistant",
        "A scope section that keeps the accountant calm:\n\n```\n## Scope\nbakeorders is "
        "an in-memory list of counter pre-orders for one shop: who ordered what, how many, "
        "what they paid up front and whether the order is placed, ready, collected or "
        "refunded. A script prints today's list from it. It is not a till, does no VAT or "
        "reconciliation and stores nothing between runs on its own.\n\n## Non-goals\n- "
        "point-of-sale or card payments\n- VAT, receipts or accounting exports\n- stock "
        "and ingredients\n```\n\nAnd a usage block:\n\n```python\nfrom bakeorders.orders "
        'import OrderBook\n\nbook = OrderBook()\norder = book.place("Mrs Okafor", '
        '"sourdough", 2, paid_p=900)\nprint(order.order_id, order.status)\n```\n\nThe '
        "status list in the scope paragraph doubles as the lifecycle documentation. If the "
        "accountant wants numbers, the honest answer is that a script can sum `paid_p` "
        "over the day, and that is the whole extent of it.",
    ),
    Turn(
        "user",
        "Money. I've stored what the customer paid up front as `paid_p`, an integer number "
        "of pence, because I remembered floats being a bad idea for money. But the clipboard "
        "says things like 'paid £9' and my script will have to print pounds, so I keep "
        "wondering whether a float in pounds would just be simpler for a shop this size. "
        "Here is the current clipboard page for flavour:\n\n```\nSat 14th\nMrs Okafor  2x "
        "sourdough      paid 9.00\nDev         bday cake (choc) paid 24  READY\nLena        "
        "6x cinnamon      not paid\n```\n\nThe 'not paid' rows matter because those are the "
        "ones we can just give away at closing without a refund conversation. Refunds are "
        "the other thing the clipboard gets wrong: a crossed-out line does not say whether "
        "the money actually went back. Last month I found two such lines and had no idea "
        "whether either customer had been paid.",
    ),
    Turn(
        "assistant",
        "Keep pence. The clipboard shows exactly why: '9.00' and '24' are the same kind of "
        "number written two ways, and a float would happily store 8.999999 after one "
        "subtraction. Integer pence never drift, comparisons are exact, and formatting for "
        "the sheet is one helper:\n\n```python\ndef pounds(pence: int) -> str:\n    return "
        'f"£{pence // 100}.{pence % 100:02d}"\n```\n\n`paid_p == 0` then cleanly means '
        "'not paid', which gives your closing-time rule for free: an order with no payment "
        "needs no refund. If you later want a total for the day, `sum(o.paid_p for o in "
        "orders)` is exact, which is more than the clipboard can say. A refund then sets "
        "`paid_p` back to zero and records why, so the crossed-out line becomes a status "
        "and a reason instead of a guess. The reason list can stay a small tuple in the "
        "refund module.",
    ),
    Turn(
        "user",
        "I wrote tests for the little `refundable` helper before writing the refund code "
        "itself, because that is the part where mistakes cost real money. Do these cover "
        "the right cases?\n\n```python\nfrom bakeorders.model import Order\nfrom bakeorders."
        "refunds import refundable\n\n\ndef test_paid_order_is_refundable():\n    order = "
        'Order("O1", "Mrs Okafor", "sourdough", 2, paid_p=900)\n    assert refundable(order) '
        'is True\n\n\ndef test_unpaid_order_is_not_refundable():\n    order = Order("O2", '
        '"Lena", "cinnamon", 6)\n    assert refundable(order) is False\n\n\ndef test_already_'
        'refunded_is_not_refundable_again():\n    order = Order("O3", "Dev", "birthday '
        'cake", 1, paid_p=2400, status="refunded")\n    assert refundable(order) is False\n'
        "```\n\nThe third case is the one that actually happened: a customer got a refund "
        "from me and then from my partner an hour later.",
    ),
    Turn(
        "assistant",
        "Those three are the right cases and the third is the important one; keep it, and "
        "consider a fourth that pins the boundary, `paid_p=1` is refundable, so nobody later "
        "changes `> 0` to `>= 100` thinking pence under a pound are noise. The helper is "
        "pure, takes an Order and returns a bool, which is why it can live in `refunds.py` "
        "without importing the book. When the refund operation itself arrives it should "
        "consult `refundable` first and set the status so that the double-refund case is "
        "structurally impossible rather than a matter of remembering. A test on the "
        "operation can then reuse your third case end to end:\n\n```python\ndef test_"
        'second_refund_is_rejected(book):\n    order = book.place("Dev", "birthday cake", '
        '1, paid_p=2400)\n    first = refund(book, order.order_id, "late")\n    assert '
        "refundable(first) is False\n```\n\nwhich reads like the incident it prevents, and "
        "fails loudly if anyone ever lets a second refund through.",
    ),
    Turn(
        "user",
        "I tried to dump the day's orders to a file so my partner could see them from the "
        "kitchen laptop and got this:\n\n```\n>>> json.dump(list(book._orders.values()), "
        'f)\nTraceback (most recent call last):\n  File "<stdin>", line 1, in <module>\n  '
        'File "/usr/lib/python3.12/json/__init__.py", line 179, in dump\n    for chunk in '
        "iterable:\n  ...\nTypeError: Object of type Order is not JSON serializable\n```\n\n"
        "Is the frozen dataclass fighting me here, or am I holding it wrong? I like that the "
        "records cannot be edited by accident, but if sharing them means a pile of "
        "conversion code I would rather know now. My partner does not write Python and will "
        "only ever open the file in a text editor to see what is due.",
    ),
    Turn(
        "assistant",
        "You are holding it almost right; `json` just does not know dataclasses. "
        "`dataclasses.asdict` converts each record and the rest is unchanged:\n\n```python\n"
        "from dataclasses import asdict\n\njson.dump([asdict(o) for o in orders], f)\n```\n\n"
        "That is the whole conversion layer, and it lives in the export script, not in the "
        "model. Reading back is `Order(**row)` per row. Keep the dataclass frozen; the "
        "kitchen laptop gets a snapshot file and the book stays the only place an order "
        "changes. Also, give the book an `all()` method so the script does not reach into "
        "`_orders`. The export then becomes a three-line script your partner can run from "
        "a desktop shortcut, and the kitchen laptop never needs the package installed to "
        "read the file.",
    ),
    Turn(
        "user",
        "Two conventions before the next features. First, return shape: public OrderBook "
        "methods and the refund functions return Order dataclass instances, never dicts or "
        "tuples. The today-script and the tests only ever handle Order, and anything that "
        "changes an order hands back the updated Order it just saved.",
    ),
    Turn(
        "assistant",
        "Noted: every public operation, on the book or in the refund module, returns Order "
        "instances (or None from a lookup that finds nothing), never dicts or tuples. "
        "Updates are built with `dataclasses.replace`, saved through the book and returned "
        "as the same instance. Nothing public will hand back a bare status string or a "
        "tuple of fields. If an operation needs to report more than the order, the extra "
        "goes in a field on Order rather than in a second return value.",
    ),
    Turn(
        "user",
        "Second, unknown order ids: an action on an id that is not in the book returns None "
        "and changes nothing, the way `ready` and `find` already behave. No raising. I am "
        "usually typing ids off the clipboard with flour on my hands and a traceback at the "
        "counter is not what I want. Nothing gets created for a mistyped id either; the "
        "book is only ever changed for an order that is already in it.",
    ),
    Turn(
        "assistant",
        "Understood: actions on an unknown order id return None and leave the book "
        "untouched, matching `ready` and `find`. New operations will look the order up with "
        "`find`, return None when it is missing and only save when it exists. A typo at "
        "the counter then does nothing at all, and the None is the only sign of it.",
    ),
    Turn(
        "user",
        "Something for later: I'd like the today-script to group by pickup slot (morning, "
        "afternoon), which means an optional slot field on Order at some point. Not now; "
        "just do not design against it. The Saturday cafe orders would all be morning, "
        "and the birthday cakes are nearly always afternoon collections. The clipboard has "
        "a pencil line across the middle of the page for this today.",
    ),
    Turn(
        "assistant",
        'That is a defaulted field on Order (`slot: str = ""`) and a `sorted(..., key=)` '
        "in the script; nothing in the current shape resists it, and `replace` keeps working "
        "when the field lands. The today-script would then print two headed sections "
        "instead of one list, with the pencil line replaced by a heading per slot.",
    ),
    Turn(
        "user",
        "For reference, the tests that exist right now are the three refundable ones above "
        "plus these:\n\n```python\nfrom bakeorders.orders import OrderBook\n\n\ndef test_"
        'place_sequential_ids():\n    book = OrderBook()\n    assert book.place("a", "x", 1)'
        '.order_id == "O1"\n    assert book.place("b", "y", 1).order_id == "O2"\n\n\ndef '
        'test_ready_unknown_is_none():\n    assert OrderBook().ready("O1") is None\n```',
    ),
    Turn(
        "assistant",
        "Good baseline; I will keep those green and add tests for each new operation. Send "
        "the first request with the current files and I will return the full target "
        "module, existing code left exactly as it is and the new operation added at the "
        "end, plus a note on the tests I would add for it.",
    ),
]

_EVENT = (
    "One scoped exception to the unknown-id convention, effective now: for anything in "
    "refunds.py, meaning operations that hand money back against an order, an unknown "
    "order id raises KeyError. A refund against an order that does not exist must never "
    "fail quietly, because cash leaves the till. Everything in orders.py keeps returning "
    "None as before."
)


def build() -> Session:
    return Session(
        id="S35",
        project="bakeorders",
        target_family="missing_record",
        support_family="return_shape",
        lifecycle="scope",
        files=_FILES,
        prefix=_PREFIX,
        states=("none", "raise"),
        state_at=("none", "raise"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10),
    )
