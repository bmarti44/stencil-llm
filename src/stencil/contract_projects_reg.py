# ruff: noqa: E501
"""REGISTERED competence pre-check task set (proposal rev 5 §3): 32 tasks, eight projects
disjoint from the development projects in :mod:`stencil.contract_projects` (kvstore,
fileio, users, config), each pairing two of the eight contract families in a pairing not
used by the development set.  Authored 2026-09-13 for this program; evaluated-on only;
nothing from ``data/bench/`` or MemoryCode.  Frozen by sha256 in
``results/contracts/REGISTRATION-PRECHECK.md`` before the run.
"""

from __future__ import annotations

from itertools import product

from stencil.contracts import ContractState, Task

# --------------------------------------------------------------------------- inventory
# missing-record policy (none | raise) x immutability (frozen | inplace)

_INV_MODEL = {
    "frozen": '''"""Inventory items."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Item:
    sku: str
    qty: int
    location: str = "main"
''',
    "inplace": '''"""Inventory items."""

from dataclasses import dataclass


@dataclass
class Item:
    sku: str
    qty: int
    location: str = "main"
''',
}

_INV_STOCK = '''"""Stock operations."""

from inventory.model import Item


class Stock:
    def __init__(self) -> None:
        self._items: dict[str, Item] = {}

    def put(self, item: Item) -> None:
        self._items[item.sku] = item

    def find(self, sku: str) -> Item | None:
        return self._items.get(sku)
'''

_INV_INIT = '"""inventory package."""\n'

_INV_FUNCTIONAL = """from inventory.model import Item
from inventory.stock import Stock


def test_adjust_changes_quantity():
    s = Stock()
    s.put(Item("a1", 5))
    out = s.adjust("a1", 3)
    assert out.qty == 8 and s.find("a1").qty == 8


def test_adjust_negative_delta():
    s = Stock()
    s.put(Item("a1", 5))
    assert s.adjust("a1", -2).qty == 3


def test_existing_api_unchanged():
    s = Stock()
    s.put(Item("z", 1, "annex"))
    assert s.find("z").location == "annex" and s.find("nope") is None
"""

_INV_CONTRACT_MISSING = {
    "none": """from inventory.model import Item
from inventory.stock import Stock


def test_adjust_missing_sku_returns_none():
    s = Stock()
    s.put(Item("a1", 5))
    assert s.adjust("missing", 1) is None
""",
    "raise": """import pytest

from inventory.model import Item
from inventory.stock import Stock


def test_adjust_missing_sku_raises_keyerror():
    s = Stock()
    s.put(Item("a1", 5))
    with pytest.raises(KeyError):
        s.adjust("missing", 1)
""",
}

_INV_CONTRACT_IMM = {
    "frozen": """from inventory.model import Item
from inventory.stock import Stock


def test_adjust_returns_new_item_and_keeps_original():
    s = Stock()
    it = Item("a1", 5)
    s.put(it)
    out = s.adjust("a1", 1)
    assert out is not it and it.qty == 5 and out.qty == 6
""",
    "inplace": """from inventory.model import Item
from inventory.stock import Stock


def test_adjust_mutates_same_item():
    s = Stock()
    it = Item("a1", 5)
    s.put(it)
    out = s.adjust("a1", 1)
    assert out is it and it.qty == 6
""",
}

_INV_TEXT = {
    (
        "missing-record policy",
        "none",
    ): "Operations on a missing record return None; never raise for an unknown key.",
    (
        "missing-record policy",
        "raise",
    ): "Operations on a missing record raise KeyError; never return None for an unknown key.",
    (
        "immutability",
        "frozen",
    ): "Item objects are immutable: operations that change an item store and return a new Item and never mutate the existing one.",
    (
        "immutability",
        "inplace",
    ): "Item objects are mutable: operations that change an item update it in place and return that same object.",
}


def _inv_gold(missing: str, imm: str) -> str:
    if missing == "none":
        lookup = """        item = self._items.get(sku)
        if item is None:
            return None"""
    else:
        lookup = """        if sku not in self._items:
            raise KeyError(sku)
        item = self._items[sku]"""
    if imm == "frozen":
        change = """        new = replace(item, qty=item.qty + delta)
        self._items[sku] = new
        return new"""
        imp = "from dataclasses import replace\n\n"
    else:
        change = """        item.qty += delta
        return item"""
        imp = ""
    head = _INV_STOCK.replace(
        '"""Stock operations."""\n\n', '"""Stock operations."""\n\n' + imp
    )
    return (
        head.rstrip("\n")
        + f"""

    def adjust(self, sku: str, delta: int):
{lookup}
{change}
"""
    )


def inventory_tasks() -> list[Task]:
    tasks = []
    for missing, imm in product(("none", "raise"), ("frozen", "inplace")):
        tasks.append(
            Task(
                id=f"inventory-{missing}-{imm}",
                project="inventory",
                files={
                    "inventory/__init__.py": _INV_INIT,
                    "inventory/model.py": _INV_MODEL[imm],
                    "inventory/stock.py": _INV_STOCK,
                },
                target="inventory/stock.py",
                request=(
                    "Add a method `adjust(self, sku: str, delta: int)` to Stock that changes "
                    "the stored quantity of the item with that sku by delta and returns the "
                    "resulting item."
                ),
                contracts=[
                    ContractState(
                        "missing-record policy",
                        missing,
                        _INV_TEXT[("missing-record policy", missing)],
                    ),
                    ContractState(
                        "immutability", imm, _INV_TEXT[("immutability", imm)]
                    ),
                ],
                functional_tests={"tests/test_adjust.py": _INV_FUNCTIONAL},
                contract_tests={
                    "tests/test_contract_missing.py": _INV_CONTRACT_MISSING[missing],
                    "tests/test_contract_immutability.py": _INV_CONTRACT_IMM[imm],
                },
                gold=_inv_gold(missing, imm),
            )
        )
    return tasks


# ------------------------------------------------------------------------------ mailer
# error surface (wrap | propagate) x naming contract (verb_noun | noun_verb)

_ML_ERRORS = '''"""Mailer errors."""


class MailError(Exception):
    """Raised when the mailer cannot deliver."""
'''

_ML_TRANSPORT = '''"""Transport layer (simulated)."""


class Transport:
    def __init__(self, failing: set[str] | None = None) -> None:
        self.failing = failing or set()
        self.sent: list[tuple[str, str]] = []

    def deliver(self, address: str, body: str) -> None:
        if address in self.failing:
            raise ConnectionError(f"cannot reach {address}")
        self.sent.append((address, body))
'''

_ML_API = '''"""Mailer public API."""

from mailer.errors import MailError
from mailer.transport import Transport


def send_message(transport: Transport, address: str, body: str) -> None:
    transport.deliver(address, body)
'''

_ML_INIT = '"""mailer package."""\n'

_ML_FUNCTIONAL = """from mailer import api
from mailer.transport import Transport


def _fn():
    f = getattr(api, "send_batch", None) or getattr(api, "batch_send", None)
    assert f is not None, "no batch function"
    return f


def test_batch_sends_all_in_order():
    t = Transport()
    n = _fn()(t, ["a@x", "b@x"], "hi")
    assert n == 2 and [a for a, _ in t.sent] == ["a@x", "b@x"]


def test_batch_empty():
    assert _fn()(Transport(), [], "hi") == 0


def test_send_message_unchanged():
    t = Transport()
    api.send_message(t, "c@x", "yo")
    assert t.sent == [("c@x", "yo")]
"""

_ML_CONTRACT_ERR = {
    "wrap": """import pytest

from mailer import api
from mailer.errors import MailError
from mailer.transport import Transport


def test_transport_failure_is_wrapped():
    f = getattr(api, "send_batch", None) or getattr(api, "batch_send", None)
    t = Transport(failing={"bad@x"})
    with pytest.raises(MailError):
        f(t, ["a@x", "bad@x"], "hi")
""",
    "propagate": """import pytest

from mailer import api
from mailer.errors import MailError
from mailer.transport import Transport


def test_transport_failure_propagates_raw():
    f = getattr(api, "send_batch", None) or getattr(api, "batch_send", None)
    t = Transport(failing={"bad@x"})
    with pytest.raises(ConnectionError) as ei:
        f(t, ["a@x", "bad@x"], "hi")
    assert not isinstance(ei.value, MailError)
""",
}

_ML_CONTRACT_NAME = {
    "verb_noun": """from mailer import api


def test_name_is_verb_noun():
    assert hasattr(api, "send_batch") and not hasattr(api, "batch_send")
""",
    "noun_verb": """from mailer import api


def test_name_is_noun_verb():
    assert hasattr(api, "batch_send") and not hasattr(api, "send_batch")
""",
}

_ML_TEXT = {
    (
        "error surface",
        "wrap",
    ): "Transport failures are reported by raising mailer.errors.MailError (chain the original); never let ConnectionError escape public functions.",
    (
        "error surface",
        "propagate",
    ): "Transport failures propagate as the original exception; never wrap them in MailError.",
    (
        "naming contract",
        "verb_noun",
    ): "Public mailer functions are named verb_noun (send_message, send_batch).",
    (
        "naming contract",
        "noun_verb",
    ): "New public mailer functions are named noun_verb (batch_send); send_message is grandfathered.",
}


def _ml_gold(err: str, name: str) -> str:
    fn = "send_batch" if name == "verb_noun" else "batch_send"
    if err == "wrap":
        body = """    for address in addresses:
        try:
            transport.deliver(address, body)
        except ConnectionError as exc:
            raise MailError(f"delivery failed for {address}") from exc
    return len(addresses)"""
    else:
        body = """    for address in addresses:
        transport.deliver(address, body)
    return len(addresses)"""
    return (
        _ML_API.rstrip("\n")
        + f"""


def {fn}(transport: Transport, addresses: list[str], body: str) -> int:
{body}
"""
    )


def mailer_tasks() -> list[Task]:
    tasks = []
    for err, name in product(("wrap", "propagate"), ("verb_noun", "noun_verb")):
        tasks.append(
            Task(
                id=f"mailer-{err}-{name}",
                project="mailer",
                files={
                    "mailer/__init__.py": _ML_INIT,
                    "mailer/errors.py": _ML_ERRORS,
                    "mailer/transport.py": _ML_TRANSPORT,
                    "mailer/api.py": _ML_API,
                },
                target="mailer/api.py",
                request=(
                    "Add a public function to mailer/api.py that sends the same body to a "
                    "list of addresses in order using the transport and returns the number "
                    "of addresses given."
                ),
                contracts=[
                    ContractState(
                        "error surface", err, _ML_TEXT[("error surface", err)]
                    ),
                    ContractState(
                        "naming contract", name, _ML_TEXT[("naming contract", name)]
                    ),
                ],
                functional_tests={"tests/test_batch.py": _ML_FUNCTIONAL},
                contract_tests={
                    "tests/test_contract_error.py": _ML_CONTRACT_ERR[err],
                    "tests/test_contract_naming.py": _ML_CONTRACT_NAME[name],
                },
                gold=_ml_gold(err, name),
            )
        )
    return tasks


# ----------------------------------------------------------------------------- catalog
# return shape (dataclass | dict) x dependency choice (json | orjson)

_CT_MODEL = '''"""Catalog entries."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Entry:
    code: str
    title: str
    price: float
'''

_CT_IO = {
    "json": '''"""Catalog persistence."""

import json
from dataclasses import asdict

from catalog.model import Entry


def save_entries(entries: list[Entry], path: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump([asdict(e) for e in entries], fh)
''',
    "orjson": '''"""Catalog persistence."""

from dataclasses import asdict

from catalog.model import Entry

try:
    import orjson as _fastjson
except ImportError:  # pragma: no cover
    _fastjson = None
import json


def _loads(data: bytes):
    if _fastjson is not None:
        return _fastjson.loads(data)
    return json.loads(data.decode("utf-8"))


def _dumps(obj) -> bytes:
    if _fastjson is not None:
        return _fastjson.dumps(obj)
    return json.dumps(obj).encode("utf-8")


def save_entries(entries: list[Entry], path: str) -> None:
    with open(path, "wb") as fh:
        fh.write(_dumps([asdict(e) for e in entries]))
''',
}

_CT_INIT = '"""catalog package."""\n'

_CT_FUNCTIONAL = """from catalog.io import load_entries, save_entries
from catalog.model import Entry


def _val(o, k):
    return o[k] if isinstance(o, dict) else getattr(o, k)


def test_roundtrip(tmp_path):
    p = tmp_path / "c.json"
    save_entries([Entry("a", "Apple", 1.5), Entry("b", "Bean", 0.25)], str(p))
    out = load_entries(str(p))
    assert [_val(o, "code") for o in out] == ["a", "b"]
    assert _val(out[1], "price") == 0.25


def test_load_empty(tmp_path):
    p = tmp_path / "c.json"
    save_entries([], str(p))
    assert load_entries(str(p)) == []
"""

_CT_CONTRACT_SHAPE = {
    "dataclass": """from catalog.io import load_entries, save_entries
from catalog.model import Entry


def test_loaded_items_are_entries(tmp_path):
    p = tmp_path / "c.json"
    save_entries([Entry("a", "Apple", 1.5)], str(p))
    (o,) = load_entries(str(p))
    assert isinstance(o, Entry)
""",
    "dict": """from catalog.io import load_entries, save_entries
from catalog.model import Entry


def test_loaded_items_are_dicts(tmp_path):
    p = tmp_path / "c.json"
    save_entries([Entry("a", "Apple", 1.5)], str(p))
    (o,) = load_entries(str(p))
    assert type(o) is dict and o == {"code": "a", "title": "Apple", "price": 1.5}
""",
}

_CT_CONTRACT_DEP = {
    "json": """import sys
import types


def test_orjson_never_used(tmp_path, monkeypatch):
    fake = types.ModuleType("orjson")

    def boom(*a, **k):
        raise AssertionError("orjson must not be used")

    fake.dumps = boom
    fake.loads = boom
    monkeypatch.setitem(sys.modules, "orjson", fake)
    for m in [m for m in sys.modules if m.startswith("catalog")]:
        monkeypatch.delitem(sys.modules, m)
    from catalog.io import load_entries, save_entries
    from catalog.model import Entry

    p = tmp_path / "c.json"
    save_entries([Entry("a", "Apple", 1.5)], str(p))
    assert len(load_entries(str(p))) == 1
""",
    "orjson": """import json
import sys
import types


def test_orjson_used_when_available(tmp_path, monkeypatch):
    fake = types.ModuleType("orjson")
    calls = []

    def dumps(obj, *a, **k):
        calls.append("dumps")
        return json.dumps(obj).encode()

    def loads(data, *a, **k):
        calls.append("loads")
        return json.loads(data)

    fake.dumps = dumps
    fake.loads = loads
    monkeypatch.setitem(sys.modules, "orjson", fake)
    for m in [m for m in sys.modules if m.startswith("catalog")]:
        monkeypatch.delitem(sys.modules, m)
    from catalog.io import load_entries, save_entries
    from catalog.model import Entry

    p = tmp_path / "c.json"
    save_entries([Entry("a", "Apple", 1.5)], str(p))
    assert len(load_entries(str(p))) == 1
    assert "loads" in calls


def test_falls_back_without_orjson(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "orjson", None)
    for m in [m for m in sys.modules if m.startswith("catalog")]:
        monkeypatch.delitem(sys.modules, m)
    from catalog.io import load_entries, save_entries
    from catalog.model import Entry

    p = tmp_path / "c.json"
    save_entries([Entry("a", "Apple", 1.5)], str(p))
    assert len(load_entries(str(p))) == 1
""",
}

_CT_TEXT = {
    (
        "return shape",
        "dataclass",
    ): "Loading functions return Entry instances, never dicts.",
    (
        "return shape",
        "dict",
    ): "Loading functions return plain dicts with keys code, title, price, never dataclass instances.",
    (
        "dependency choice",
        "json",
    ): "JSON handling uses the standard library json module only; never import or use orjson.",
    (
        "dependency choice",
        "orjson",
    ): "JSON handling goes through the module's orjson-backed helpers (_loads/_dumps, which fall back to json); never call json directly from public functions.",
}


def _ct_gold(shape: str, dep: str) -> str:
    conv = "Entry(**d)" if shape == "dataclass" else "dict(d)"
    if dep == "json":
        body = f"""    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return [{conv} for d in data]"""
    else:
        body = f"""    with open(path, "rb") as fh:
        data = _loads(fh.read())
    return [{conv} for d in data]"""
    return (
        _CT_IO[dep].rstrip("\n")
        + f"""


def load_entries(path: str) -> list:
{body}
"""
    )


def catalog_tasks() -> list[Task]:
    tasks = []
    for shape, dep in product(("dataclass", "dict"), ("json", "orjson")):
        tasks.append(
            Task(
                id=f"catalog-{shape}-{dep}",
                project="catalog",
                files={
                    "catalog/__init__.py": _CT_INIT,
                    "catalog/model.py": _CT_MODEL,
                    "catalog/io.py": _CT_IO[dep],
                },
                target="catalog/io.py",
                request=(
                    "Add a function `load_entries(path: str) -> list` to catalog/io.py that "
                    "reads a file written by save_entries and returns the entries in order."
                ),
                contracts=[
                    ContractState(
                        "return shape", shape, _CT_TEXT[("return shape", shape)]
                    ),
                    ContractState(
                        "dependency choice", dep, _CT_TEXT[("dependency choice", dep)]
                    ),
                ],
                functional_tests={"tests/test_load.py": _CT_FUNCTIONAL},
                contract_tests={
                    "tests/test_contract_shape.py": _CT_CONTRACT_SHAPE[shape],
                    "tests/test_contract_dependency.py": _CT_CONTRACT_DEP[dep],
                },
                gold=_ct_gold(shape, dep),
            )
        )
    return tasks


# -------------------------------------------------------------------------------- auth
# validation entry (api | storage) x logging policy (warn | silent)

_AU_STORE = '''"""Token storage."""


class TokenStore:
    def __init__(self) -> None:
        self._tokens: dict[str, str] = {}

    def put(self, user: str, token: str) -> None:
        if len(token) < 8:
            raise ValueError("token too short")
        self._tokens[user] = token

    def get(self, user: str) -> str | None:
        return self._tokens.get(user)
'''

_AU_API = '''"""Auth public API."""

import logging

from auth.store import TokenStore

log = logging.getLogger("auth.api")


def issue_token(store: TokenStore, user: str, token: str) -> None:
    if len(token) < 8:
        raise ValueError("token too short")
    store.put(user, token)
'''

_AU_INIT = '"""auth package."""\n'

_AU_FUNCTIONAL = """import pytest

from auth import api
from auth.store import TokenStore


def test_rotate_replaces_token():
    s = TokenStore()
    api.issue_token(s, "ann", "abcdefgh")
    api.rotate_token(s, "ann", "ijklmnop")
    assert s.get("ann") == "ijklmnop"


def test_rotate_unknown_user_raises_keyerror():
    with pytest.raises(KeyError):
        api.rotate_token(TokenStore(), "nobody", "ijklmnop")


def test_issue_unchanged():
    s = TokenStore()
    api.issue_token(s, "bo", "abcdefgh")
    assert s.get("bo") == "abcdefgh"
"""

_AU_CONTRACT_VALID = {
    "api": """import pytest

from auth import api
from auth.store import TokenStore


def test_short_token_rejected_before_storage():
    class Spy(TokenStore):
        def __init__(self):
            super().__init__()
            self.calls = []

        def put(self, user, token):
            self.calls.append((user, token))
            return super().put(user, token)

    spy = Spy()
    api.issue_token(spy, "ann", "abcdefgh")
    spy.calls.clear()
    with pytest.raises(ValueError):
        api.rotate_token(spy, "ann", "short")
    assert not spy.calls
""",
    "storage": """import pytest

from auth import api
from auth.store import TokenStore


def test_short_token_rejected_by_storage_not_api():
    class Spy(TokenStore):
        def __init__(self):
            super().__init__()
            self.calls = []

        def put(self, user, token):
            self.calls.append((user, token))
            return super().put(user, token)

    spy = Spy()
    api.issue_token(spy, "ann", "abcdefgh")
    spy.calls.clear()
    with pytest.raises(ValueError):
        api.rotate_token(spy, "ann", "short")
    assert spy.calls == [("ann", "short")]
""",
}

_AU_CONTRACT_LOG = {
    "warn": """import logging

from auth import api
from auth.store import TokenStore


def test_rotation_logs_warning_with_user(caplog):
    s = TokenStore()
    api.issue_token(s, "ann", "abcdefgh")
    with caplog.at_level(logging.WARNING, logger="auth.api"):
        api.rotate_token(s, "ann", "ijklmnop")
    recs = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert recs and any(getattr(r, "user", None) == "ann" for r in recs)
""",
    "silent": """import logging

from auth import api
from auth.store import TokenStore


def test_rotation_logs_nothing(caplog):
    s = TokenStore()
    api.issue_token(s, "ann", "abcdefgh")
    with caplog.at_level(logging.DEBUG):
        api.rotate_token(s, "ann", "ijklmnop")
    assert not caplog.records
""",
}

_AU_TEXT = {
    (
        "validation entry",
        "api",
    ): "Input validation happens at the public API boundary: public functions raise ValueError on invalid input before touching storage.",
    (
        "validation entry",
        "storage",
    ): "Input validation happens in the storage layer only: public API functions pass values through unchanged and never validate themselves.",
    (
        "logging policy",
        "warn",
    ): "Security-relevant operations (issuing or rotating tokens) log once at WARNING on the module logger with the user name in the record's extra field `user`.",
    (
        "logging policy",
        "silent",
    ): "Public functions never log; leave logging to the caller.",
}


def _au_gold(valid: str, logp: str) -> str:
    check = (
        '    if len(token) < 8:\n        raise ValueError("token too short")\n'
        if valid == "api"
        else ""
    )
    logline = (
        '    log.warning("token rotated for %s", user, extra={"user": user})\n'
        if logp == "warn"
        else ""
    )
    return (
        _AU_API.rstrip("\n")
        + f"""


def rotate_token(store: TokenStore, user: str, token: str) -> None:
{check}    if store.get(user) is None:
        raise KeyError(user)
    store.put(user, token)
{logline}"""
    )


def auth_tasks() -> list[Task]:
    tasks = []
    for valid, logp in product(("api", "storage"), ("warn", "silent")):
        tasks.append(
            Task(
                id=f"auth-{valid}-{logp}",
                project="auth",
                files={
                    "auth/__init__.py": _AU_INIT,
                    "auth/store.py": _AU_STORE,
                    "auth/api.py": _AU_API,
                },
                target="auth/api.py",
                request=(
                    "Add a function `rotate_token(store: TokenStore, user: str, token: str) "
                    "-> None` to auth/api.py that replaces an existing user's token; an "
                    "unknown user raises KeyError."
                ),
                contracts=[
                    ContractState(
                        "validation entry", valid, _AU_TEXT[("validation entry", valid)]
                    ),
                    ContractState(
                        "logging policy", logp, _AU_TEXT[("logging policy", logp)]
                    ),
                ],
                functional_tests={"tests/test_rotate.py": _AU_FUNCTIONAL},
                contract_tests={
                    "tests/test_contract_validation.py": _AU_CONTRACT_VALID[valid],
                    "tests/test_contract_logging.py": _AU_CONTRACT_LOG[logp],
                },
                gold=_au_gold(valid, logp),
            )
        )
    return tasks


# ------------------------------------------------------------------------------ ledger
# missing-record policy (none | raise) x naming contract (verb_noun | noun_verb)

_LG_BOOK = '''"""Account ledger."""


class Ledger:
    def __init__(self) -> None:
        self._balances: dict[str, int] = {}

    def open_account(self, name: str, initial: int = 0) -> None:
        self._balances[name] = initial

    def balance(self, name: str) -> int | None:
        return self._balances.get(name)
'''

_LG_INIT = '"""ledger package."""\n'

_LG_FUNCTIONAL = """import pytest

from ledger.book import Ledger


def _fn(book):
    f = getattr(book, "credit_account", None) or getattr(book, "account_credit", None)
    assert f is not None, "no credit method"
    return f


def test_credit_increases_balance():
    b = Ledger()
    b.open_account("ann", 10)
    assert _fn(b)("ann", 5) == 15 and b.balance("ann") == 15


def test_credit_negative_amount_rejected():
    b = Ledger()
    b.open_account("ann", 10)
    with pytest.raises(ValueError):
        _fn(b)("ann", -1)


def test_existing_api_unchanged():
    b = Ledger()
    b.open_account("z", 3)
    assert b.balance("z") == 3 and b.balance("nope") is None
"""

_LG_CONTRACT_MISSING = {
    "none": """from ledger.book import Ledger


def test_credit_unknown_account_returns_none():
    b = Ledger()
    f = getattr(b, "credit_account", None) or getattr(b, "account_credit", None)
    assert f("ghost", 5) is None
""",
    "raise": """import pytest

from ledger.book import Ledger


def test_credit_unknown_account_raises_keyerror():
    b = Ledger()
    f = getattr(b, "credit_account", None) or getattr(b, "account_credit", None)
    with pytest.raises(KeyError):
        f("ghost", 5)
""",
}

_LG_CONTRACT_NAME = {
    "verb_noun": """from ledger.book import Ledger


def test_name_is_verb_noun():
    assert hasattr(Ledger, "credit_account") and not hasattr(Ledger, "account_credit")
""",
    "noun_verb": """from ledger.book import Ledger


def test_name_is_noun_verb():
    assert hasattr(Ledger, "account_credit") and not hasattr(Ledger, "credit_account")
""",
}

_LG_TEXT = {
    (
        "missing-record policy",
        "none",
    ): "Operations on an unknown account return None; never raise for an unknown account name.",
    (
        "missing-record policy",
        "raise",
    ): "Operations on an unknown account raise KeyError; never return None for an unknown account name.",
    (
        "naming contract",
        "verb_noun",
    ): "Ledger method names are verb_noun (open_account, credit_account).",
    (
        "naming contract",
        "noun_verb",
    ): "New Ledger method names are noun_verb (account_credit); open_account is grandfathered.",
}


def _lg_gold(missing: str, name: str) -> str:
    fn = "credit_account" if name == "verb_noun" else "account_credit"
    if missing == "none":
        lookup = """        if name not in self._balances:
            return None"""
    else:
        lookup = """        if name not in self._balances:
            raise KeyError(name)"""
    return (
        _LG_BOOK.rstrip("\n")
        + f"""

    def {fn}(self, name: str, amount: int):
        if amount < 0:
            raise ValueError("amount must be non-negative")
{lookup}
        self._balances[name] += amount
        return self._balances[name]
"""
    )


def ledger_tasks() -> list[Task]:
    tasks = []
    for missing, name in product(("none", "raise"), ("verb_noun", "noun_verb")):
        tasks.append(
            Task(
                id=f"ledger-{missing}-{name}",
                project="ledger",
                files={"ledger/__init__.py": _LG_INIT, "ledger/book.py": _LG_BOOK},
                target="ledger/book.py",
                request=(
                    "Add a method to Ledger that credits an account: it takes (name, amount), "
                    "raises ValueError for a negative amount, adds the amount to the account's "
                    "balance and returns the new balance."
                ),
                contracts=[
                    ContractState(
                        "missing-record policy",
                        missing,
                        _LG_TEXT[("missing-record policy", missing)],
                    ),
                    ContractState(
                        "naming contract", name, _LG_TEXT[("naming contract", name)]
                    ),
                ],
                functional_tests={"tests/test_credit.py": _LG_FUNCTIONAL},
                contract_tests={
                    "tests/test_contract_missing.py": _LG_CONTRACT_MISSING[missing],
                    "tests/test_contract_naming.py": _LG_CONTRACT_NAME[name],
                },
                gold=_lg_gold(missing, name),
            )
        )
    return tasks


# ---------------------------------------------------------------------------- exporter
# error surface (wrap | propagate) x return shape (dataclass | dict)

_EX_ERRORS = '''"""Exporter errors."""


class ExportError(Exception):
    """Raised when an export cannot be completed."""
'''

_EX_MODEL = '''"""Export results."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Report:
    path: str
    rows: int
'''

_EX_WRITER = '''"""CSV export."""

import csv

from exporter.errors import ExportError
from exporter.model import Report


def write_rows(path: str, rows: list[list[str]]) -> int:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        for r in rows:
            w.writerow(r)
    return len(rows)
'''

_EX_INIT = '"""exporter package."""\n'

_EX_FUNCTIONAL = """from exporter.writer import export_table, write_rows


def _val(o, k):
    return o[k] if isinstance(o, dict) else getattr(o, k)


def test_export_writes_and_reports(tmp_path):
    p = tmp_path / "t.csv"
    out = export_table(str(p), [["a", "b"], ["1", "2"]])
    assert _val(out, "rows") == 2 and _val(out, "path") == str(p)
    assert p.read_text().splitlines() == ["a,b", "1,2"]


def test_export_empty(tmp_path):
    p = tmp_path / "e.csv"
    assert _val(export_table(str(p), []), "rows") == 0


def test_write_rows_unchanged(tmp_path):
    p = tmp_path / "w.csv"
    assert write_rows(str(p), [["x"]]) == 1
"""

_EX_CONTRACT_ERR = {
    "wrap": """import pytest

from exporter.errors import ExportError
from exporter.writer import export_table


def test_unwritable_path_is_wrapped(tmp_path):
    with pytest.raises(ExportError):
        export_table(str(tmp_path / "missing_dir" / "t.csv"), [["a"]])
""",
    "propagate": """import pytest

from exporter.errors import ExportError
from exporter.writer import export_table


def test_unwritable_path_propagates_oserror(tmp_path):
    with pytest.raises(OSError) as ei:
        export_table(str(tmp_path / "missing_dir" / "t.csv"), [["a"]])
    assert not isinstance(ei.value, ExportError)
""",
}

_EX_CONTRACT_SHAPE = {
    "dataclass": """from exporter.model import Report
from exporter.writer import export_table


def test_result_is_report(tmp_path):
    out = export_table(str(tmp_path / "t.csv"), [["a"]])
    assert isinstance(out, Report)
""",
    "dict": """from exporter.writer import export_table


def test_result_is_dict(tmp_path):
    p = str(tmp_path / "t.csv")
    out = export_table(p, [["a"]])
    assert type(out) is dict and out == {"path": p, "rows": 1}
""",
}

_EX_TEXT = {
    (
        "error surface",
        "wrap",
    ): "I/O failures are reported by raising exporter.errors.ExportError (chain the original); never let OSError escape public functions.",
    (
        "error surface",
        "propagate",
    ): "I/O failures propagate as the original OSError; never wrap them in ExportError.",
    (
        "return shape",
        "dataclass",
    ): "Public exporter functions return Report instances, never dicts.",
    (
        "return shape",
        "dict",
    ): "Public exporter functions return plain dicts with keys path and rows, never dataclass instances.",
}


def _ex_gold(err: str, shape: str) -> str:
    result = "Report(path, n)" if shape == "dataclass" else '{"path": path, "rows": n}'
    if err == "wrap":
        body = f"""    try:
        n = write_rows(path, rows)
    except OSError as exc:
        raise ExportError(f"cannot export to {{path}}") from exc
    return {result}"""
    else:
        body = f"""    n = write_rows(path, rows)
    return {result}"""
    return (
        _EX_WRITER.rstrip("\n")
        + f"""


def export_table(path: str, rows: list[list[str]]):
{body}
"""
    )


def exporter_tasks() -> list[Task]:
    tasks = []
    for err, shape in product(("wrap", "propagate"), ("dataclass", "dict")):
        tasks.append(
            Task(
                id=f"exporter-{err}-{shape}",
                project="exporter",
                files={
                    "exporter/__init__.py": _EX_INIT,
                    "exporter/errors.py": _EX_ERRORS,
                    "exporter/model.py": _EX_MODEL,
                    "exporter/writer.py": _EX_WRITER,
                },
                target="exporter/writer.py",
                request=(
                    "Add a function `export_table(path: str, rows: list[list[str]])` to "
                    "exporter/writer.py that writes the rows as CSV to the path (reuse "
                    "write_rows) and returns a result describing the path and the number "
                    "of rows written."
                ),
                contracts=[
                    ContractState(
                        "error surface", err, _EX_TEXT[("error surface", err)]
                    ),
                    ContractState(
                        "return shape", shape, _EX_TEXT[("return shape", shape)]
                    ),
                ],
                functional_tests={"tests/test_export.py": _EX_FUNCTIONAL},
                contract_tests={
                    "tests/test_contract_error.py": _EX_CONTRACT_ERR[err],
                    "tests/test_contract_shape.py": _EX_CONTRACT_SHAPE[shape],
                },
                gold=_ex_gold(err, shape),
            )
        )
    return tasks


# ---------------------------------------------------------------------------- settings
# dependency choice (json | orjson) x validation entry (api | storage)

_ST_STORE = '''"""Settings storage."""


class SettingsStore:
    def __init__(self) -> None:
        self._data: dict[str, object] = {}

    def set(self, key: str, value: object) -> None:
        if not key or not key.isidentifier():
            raise ValueError("invalid key")
        self._data[key] = value

    def snapshot(self) -> dict[str, object]:
        return dict(self._data)
'''

_ST_API = {
    "json": '''"""Settings public API."""

import json

from settings.store import SettingsStore


def set_setting(store: SettingsStore, key: str, value: object) -> None:
    if not key or not key.isidentifier():
        raise ValueError("invalid key")
    store.set(key, value)


def export_settings(store: SettingsStore, path: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(store.snapshot(), fh)
''',
    "orjson": '''"""Settings public API."""

from settings.store import SettingsStore

try:
    import orjson as _fastjson
except ImportError:  # pragma: no cover
    _fastjson = None
import json


def _loads(data: bytes):
    if _fastjson is not None:
        return _fastjson.loads(data)
    return json.loads(data.decode("utf-8"))


def _dumps(obj) -> bytes:
    if _fastjson is not None:
        return _fastjson.dumps(obj)
    return json.dumps(obj).encode("utf-8")


def set_setting(store: SettingsStore, key: str, value: object) -> None:
    if not key or not key.isidentifier():
        raise ValueError("invalid key")
    store.set(key, value)


def export_settings(store: SettingsStore, path: str) -> None:
    with open(path, "wb") as fh:
        fh.write(_dumps(store.snapshot()))
''',
}

_ST_INIT = '"""settings package."""\n'

_ST_FUNCTIONAL = """import pytest

from settings import api
from settings.store import SettingsStore


def test_import_loads_all_keys(tmp_path):
    src = SettingsStore()
    api.set_setting(src, "debug", True)
    api.set_setting(src, "retries", 3)
    p = tmp_path / "s.json"
    api.export_settings(src, str(p))
    dst = SettingsStore()
    n = api.import_settings(dst, str(p))
    assert n == 2 and dst.snapshot() == {"debug": True, "retries": 3}


def test_import_empty(tmp_path):
    p = tmp_path / "s.json"
    api.export_settings(SettingsStore(), str(p))
    assert api.import_settings(SettingsStore(), str(p)) == 0
"""

_ST_CONTRACT_DEP = {
    "json": """import sys
import types


def test_orjson_never_used(tmp_path, monkeypatch):
    fake = types.ModuleType("orjson")

    def boom(*a, **k):
        raise AssertionError("orjson must not be used")

    fake.dumps = boom
    fake.loads = boom
    monkeypatch.setitem(sys.modules, "orjson", fake)
    for m in [m for m in sys.modules if m.startswith("settings")]:
        monkeypatch.delitem(sys.modules, m)
    from settings import api
    from settings.store import SettingsStore

    src = SettingsStore()
    api.set_setting(src, "a", 1)
    p = tmp_path / "s.json"
    api.export_settings(src, str(p))
    assert api.import_settings(SettingsStore(), str(p)) == 1
""",
    "orjson": """import json
import sys
import types


def test_orjson_used_when_available(tmp_path, monkeypatch):
    fake = types.ModuleType("orjson")
    calls = []

    def dumps(obj, *a, **k):
        calls.append("dumps")
        return json.dumps(obj).encode()

    def loads(data, *a, **k):
        calls.append("loads")
        return json.loads(data)

    fake.dumps = dumps
    fake.loads = loads
    monkeypatch.setitem(sys.modules, "orjson", fake)
    for m in [m for m in sys.modules if m.startswith("settings")]:
        monkeypatch.delitem(sys.modules, m)
    from settings import api
    from settings.store import SettingsStore

    src = SettingsStore()
    api.set_setting(src, "a", 1)
    p = tmp_path / "s.json"
    api.export_settings(src, str(p))
    assert api.import_settings(SettingsStore(), str(p)) == 1
    assert "loads" in calls


def test_falls_back_without_orjson(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "orjson", None)
    for m in [m for m in sys.modules if m.startswith("settings")]:
        monkeypatch.delitem(sys.modules, m)
    from settings import api
    from settings.store import SettingsStore

    src = SettingsStore()
    api.set_setting(src, "a", 1)
    p = tmp_path / "s.json"
    api.export_settings(src, str(p))
    assert api.import_settings(SettingsStore(), str(p)) == 1
""",
}

_ST_CONTRACT_VALID = {
    "api": """import json

import pytest

from settings import api
from settings.store import SettingsStore


def test_bad_key_rejected_before_storage(tmp_path):
    class Spy(SettingsStore):
        def __init__(self):
            super().__init__()
            self.calls = []

        def set(self, key, value):
            self.calls.append(key)
            return super().set(key, value)

    p = tmp_path / "s.json"
    p.write_text(json.dumps({"ok": 1, "not a key": 2}))
    spy = Spy()
    with pytest.raises(ValueError):
        api.import_settings(spy, str(p))
    assert "not a key" not in spy.calls
""",
    "storage": """import json

import pytest

from settings import api
from settings.store import SettingsStore


def test_bad_key_rejected_by_storage_not_api(tmp_path):
    class Spy(SettingsStore):
        def __init__(self):
            super().__init__()
            self.calls = []

        def set(self, key, value):
            self.calls.append(key)
            return super().set(key, value)

    p = tmp_path / "s.json"
    p.write_text(json.dumps({"not a key": 2}))
    spy = Spy()
    with pytest.raises(ValueError):
        api.import_settings(spy, str(p))
    assert spy.calls == ["not a key"], "the API must pass keys through to storage"
""",
}

_ST_TEXT = {
    (
        "dependency choice",
        "json",
    ): "JSON handling uses the standard library json module only; never import or use orjson.",
    (
        "dependency choice",
        "orjson",
    ): "JSON handling goes through the module's orjson-backed helpers (_loads/_dumps, which fall back to json); never call json directly from public functions.",
    (
        "validation entry",
        "api",
    ): "Input validation happens at the public API boundary: public functions raise ValueError on invalid input before touching storage.",
    (
        "validation entry",
        "storage",
    ): "Input validation happens in the storage layer only: public API functions pass values through unchanged and never validate themselves.",
}


def _st_gold(dep: str, valid: str) -> str:
    if dep == "json":
        load = """    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)"""
    else:
        load = """    with open(path, "rb") as fh:
        data = _loads(fh.read())"""
    check = (
        """        if not key or not key.isidentifier():
            raise ValueError("invalid key")
"""
        if valid == "api"
        else ""
    )
    return (
        _ST_API[dep].rstrip("\n")
        + f"""


def import_settings(store: SettingsStore, path: str) -> int:
{load}
    for key, value in data.items():
{check}        store.set(key, value)
    return len(data)
"""
    )


def settings_tasks() -> list[Task]:
    tasks = []
    for dep, valid in product(("json", "orjson"), ("api", "storage")):
        tasks.append(
            Task(
                id=f"settings-{dep}-{valid}",
                project="settings",
                files={
                    "settings/__init__.py": _ST_INIT,
                    "settings/store.py": _ST_STORE,
                    "settings/api.py": _ST_API[dep],
                },
                target="settings/api.py",
                request=(
                    "Add a function `import_settings(store: SettingsStore, path: str) -> int` "
                    "to settings/api.py that reads a file written by export_settings, stores "
                    "every key/value and returns the number of keys read."
                ),
                contracts=[
                    ContractState(
                        "dependency choice", dep, _ST_TEXT[("dependency choice", dep)]
                    ),
                    ContractState(
                        "validation entry", valid, _ST_TEXT[("validation entry", valid)]
                    ),
                ],
                functional_tests={"tests/test_import.py": _ST_FUNCTIONAL},
                contract_tests={
                    "tests/test_contract_dependency.py": _ST_CONTRACT_DEP[dep],
                    "tests/test_contract_validation.py": _ST_CONTRACT_VALID[valid],
                },
                gold=_st_gold(dep, valid),
            )
        )
    return tasks


# ------------------------------------------------------------------------------- queue
# logging policy (warn | silent) x immutability (frozen | inplace)

_QU_MODEL = {
    "frozen": '''"""Job model."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Job:
    job_id: str
    attempts: int = 0
    state: str = "queued"
''',
    "inplace": '''"""Job model."""

from dataclasses import dataclass


@dataclass
class Job:
    job_id: str
    attempts: int = 0
    state: str = "queued"
''',
}

_QU_QUEUE = '''"""Job queue."""

import logging

from jobs.model import Job

log = logging.getLogger("jobs.queue")


class Queue:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}

    def submit(self, job: Job) -> None:
        self._jobs[job.job_id] = job

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)
'''

_QU_INIT = '"""jobs package."""\n'

_QU_FUNCTIONAL = """import pytest

from jobs.model import Job
from jobs.queue import Queue


def test_retry_increments_attempts_and_requeues():
    q = Queue()
    q.submit(Job("j1", 2, "failed"))
    out = q.retry("j1")
    assert out.attempts == 3 and out.state == "queued"
    assert q.get("j1").attempts == 3 and q.get("j1").state == "queued"


def test_retry_unknown_job_raises_keyerror():
    with pytest.raises(KeyError):
        Queue().retry("nope")


def test_existing_api_unchanged():
    q = Queue()
    q.submit(Job("z"))
    assert q.get("z").state == "queued" and q.get("nope") is None
"""

_QU_CONTRACT_LOG = {
    "warn": """import logging

from jobs.model import Job
from jobs.queue import Queue


def test_retry_logs_warning_with_job_id(caplog):
    q = Queue()
    q.submit(Job("j1", 0, "failed"))
    with caplog.at_level(logging.WARNING, logger="jobs.queue"):
        q.retry("j1")
    recs = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert recs and any(getattr(r, "job_id", None) == "j1" for r in recs)
""",
    "silent": """import logging

from jobs.model import Job
from jobs.queue import Queue


def test_retry_logs_nothing(caplog):
    q = Queue()
    q.submit(Job("j1", 0, "failed"))
    with caplog.at_level(logging.DEBUG):
        q.retry("j1")
    assert not caplog.records
""",
}

_QU_CONTRACT_IMM = {
    "frozen": """from jobs.model import Job
from jobs.queue import Queue


def test_retry_returns_new_job_and_keeps_original():
    q = Queue()
    j = Job("j1", 0, "failed")
    q.submit(j)
    out = q.retry("j1")
    assert out is not j and j.attempts == 0 and out.attempts == 1
""",
    "inplace": """from jobs.model import Job
from jobs.queue import Queue


def test_retry_mutates_same_job():
    q = Queue()
    j = Job("j1", 0, "failed")
    q.submit(j)
    out = q.retry("j1")
    assert out is j and j.attempts == 1
""",
}

_QU_TEXT = {
    (
        "logging policy",
        "warn",
    ): "Retries log once at WARNING on the module logger with the job id in the record's extra field `job_id`.",
    (
        "logging policy",
        "silent",
    ): "Queue methods never log; leave logging to the caller.",
    (
        "immutability",
        "frozen",
    ): "Job objects are immutable: operations that change a job store and return a new Job and never mutate the existing one.",
    (
        "immutability",
        "inplace",
    ): "Job objects are mutable: operations that change a job update it in place and return that same object.",
}


def _qu_gold(logp: str, imm: str) -> str:
    logline = (
        '        log.warning("retrying job %s", job_id, extra={"job_id": job_id})\n'
        if logp == "warn"
        else ""
    )
    if imm == "frozen":
        change = """        new = replace(job, attempts=job.attempts + 1, state="queued")
        self._jobs[job_id] = new
        return new"""
        imp = "from dataclasses import replace\n"
    else:
        change = """        job.attempts += 1
        job.state = "queued"
        return job"""
        imp = ""
    head = _QU_QUEUE.replace("import logging\n", imp + "import logging\n")
    return (
        head.rstrip("\n")
        + f"""

    def retry(self, job_id: str):
        if job_id not in self._jobs:
            raise KeyError(job_id)
        job = self._jobs[job_id]
{logline}{change}
"""
    )


def queue_tasks() -> list[Task]:
    tasks = []
    for logp, imm in product(("warn", "silent"), ("frozen", "inplace")):
        tasks.append(
            Task(
                id=f"queue-{logp}-{imm}",
                project="queue",
                files={
                    "jobs/__init__.py": _QU_INIT,
                    "jobs/model.py": _QU_MODEL[imm],
                    "jobs/queue.py": _QU_QUEUE,
                },
                target="jobs/queue.py",
                request=(
                    "Add a method `retry(self, job_id: str)` to Queue that increments the "
                    'job\'s attempts, sets its state to "queued" and returns the resulting '
                    "job; an unknown job id raises KeyError."
                ),
                contracts=[
                    ContractState(
                        "logging policy", logp, _QU_TEXT[("logging policy", logp)]
                    ),
                    ContractState("immutability", imm, _QU_TEXT[("immutability", imm)]),
                ],
                functional_tests={"tests/test_retry.py": _QU_FUNCTIONAL},
                contract_tests={
                    "tests/test_contract_logging.py": _QU_CONTRACT_LOG[logp],
                    "tests/test_contract_immutability.py": _QU_CONTRACT_IMM[imm],
                },
                gold=_qu_gold(logp, imm),
            )
        )
    return tasks


def registered_tasks() -> list[Task]:
    return (
        inventory_tasks()
        + mailer_tasks()
        + catalog_tasks()
        + auth_tasks()
        + ledger_tasks()
        + exporter_tasks()
        + settings_tasks()
        + queue_tasks()
    )
