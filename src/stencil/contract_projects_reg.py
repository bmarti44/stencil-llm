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


def registered_tasks() -> list[Task]:
    return inventory_tasks() + mailer_tasks() + catalog_tasks() + auth_tasks()
