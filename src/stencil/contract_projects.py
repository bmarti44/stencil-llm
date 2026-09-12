# ruff: noqa: E501
"""Authored projects for the contract-domain tasks (proposal rev 5 §2).

Each project exposes ``tasks()`` returning one :class:`Task` per combination of
contract states it supports.  Gold solutions are authored per state so the self-check
(``tests/test_contracts.py``) can verify that every contract test discriminates: the
gold for state A passes A's contract tests and fails B's, while both pass the
functional tests.

Families implemented so far (two of the eight in the schema; the rest follow the same
pattern): ``missing-record policy`` (``none`` | ``raise``), ``return shape``
(``dataclass`` | ``dict``), ``error surface`` (``wrap`` | ``propagate``),
``logging policy`` (``warn`` | ``silent``).  Data lineage: authored 2026-09-13 for this
program; evaluated-on only; nothing from ``data/bench/`` or MemoryCode.
"""

from __future__ import annotations

from itertools import product

from stencil.contracts import ContractState, Task

# ----------------------------------------------------------------------------- kvstore

_KV_RECORDS = '''"""In-memory record store."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Record:
    key: str
    value: int
    tags: tuple[str, ...] = ()


class RecordStore:
    def __init__(self) -> None:
        self._items: dict[str, Record] = {}

    def add(self, record: Record) -> None:
        self._items[record.key] = record

    def get(self, key: str) -> Record | None:
        return self._items.get(key)

    def keys(self) -> list[str]:
        return sorted(self._items)
'''

_KV_INIT = '"""store package."""\n\nfrom store.records import Record, RecordStore\n\n__all__ = ["Record", "RecordStore"]\n'

_KV_FUNCTIONAL = """from store.records import Record, RecordStore


def _store():
    s = RecordStore()
    s.add(Record("a", 1, ("x",)))
    s.add(Record("b", 2))
    return s


def test_get_many_present_keys_in_order():
    s = _store()
    out = s.get_many(["b", "a"])
    assert len(out) == 2
    vals = [o["value"] if isinstance(o, dict) else o.value for o in out]
    assert vals == [2, 1]


def test_get_many_empty():
    assert _store().get_many([]) == []


def test_existing_api_unchanged():
    s = _store()
    assert s.get("a").value == 1 and s.get("zz") is None and s.keys() == ["a", "b"]
"""

_KV_CONTRACT_MISSING = {
    "none": """from store.records import Record, RecordStore


def test_missing_key_yields_none():
    s = RecordStore()
    s.add(Record("a", 1))
    out = s.get_many(["a", "missing"])
    assert len(out) == 2 and out[1] is None
""",
    "raise": """import pytest

from store.records import Record, RecordStore


def test_missing_key_raises_keyerror():
    s = RecordStore()
    s.add(Record("a", 1))
    with pytest.raises(KeyError):
        s.get_many(["a", "missing"])
""",
}

_KV_CONTRACT_SHAPE = {
    "dataclass": """from store.records import Record, RecordStore


def test_items_are_record_instances():
    s = RecordStore()
    s.add(Record("a", 1, ("t",)))
    (o,) = s.get_many(["a"])
    assert isinstance(o, Record) and o.tags == ("t",)
""",
    "dict": """from store.records import Record, RecordStore


def test_items_are_plain_dicts():
    s = RecordStore()
    s.add(Record("a", 1, ("t",)))
    (o,) = s.get_many(["a"])
    assert type(o) is dict and o == {"key": "a", "value": 1, "tags": ["t"]}
""",
}

_KV_TEXT = {
    (
        "missing-record policy",
        "none",
    ): "Lookups of missing records return None; never raise for a missing key.",
    (
        "missing-record policy",
        "raise",
    ): "Lookups of missing records raise KeyError; never return None for a missing key.",
    (
        "return shape",
        "dataclass",
    ): "Public store methods return Record instances, never dicts.",
    (
        "return shape",
        "dict",
    ): "Public store methods return plain dicts with keys key, value, tags (tags as a list), never dataclass instances.",
}


def _kv_gold(missing: str, shape: str) -> str:
    if shape == "dataclass":
        conv = "rec"
    else:
        conv = '{"key": rec.key, "value": rec.value, "tags": list(rec.tags)}'
    if missing == "none":
        body = f"""        out = []
        for key in keys:
            rec = self._items.get(key)
            out.append(None if rec is None else {conv})
        return out"""
    else:
        body = f"""        out = []
        for key in keys:
            if key not in self._items:
                raise KeyError(key)
            rec = self._items[key]
            out.append({conv})
        return out"""
    return (
        _KV_RECORDS.rstrip("\n")
        + f"""

    def get_many(self, keys: list[str]) -> list:
{body}
"""
    )


def kvstore_tasks() -> list[Task]:
    tasks = []
    for missing, shape in product(("none", "raise"), ("dataclass", "dict")):
        contracts = [
            ContractState(
                "missing-record policy",
                missing,
                _KV_TEXT[("missing-record policy", missing)],
            ),
            ContractState("return shape", shape, _KV_TEXT[("return shape", shape)]),
        ]
        tasks.append(
            Task(
                id=f"kvstore-{missing}-{shape}",
                project="kvstore",
                files={"store/__init__.py": _KV_INIT, "store/records.py": _KV_RECORDS},
                target="store/records.py",
                request=(
                    "Add a method `get_many(self, keys: list[str]) -> list` to RecordStore "
                    "that returns one result per key, in the order given."
                ),
                contracts=contracts,
                functional_tests={"tests/test_get_many.py": _KV_FUNCTIONAL},
                contract_tests={
                    "tests/test_contract_missing.py": _KV_CONTRACT_MISSING[missing],
                    "tests/test_contract_shape.py": _KV_CONTRACT_SHAPE[shape],
                },
                gold=_kv_gold(missing, shape),
            )
        )
    return tasks


# ------------------------------------------------------------------------------ fileio

_IO_ERRORS = '''"""Application errors."""


class AppError(Exception):
    """Raised for any failure the application reports to its caller."""
'''

_IO_MODULE = '''"""File helpers."""

import logging

from app.errors import AppError

log = logging.getLogger("app.io")


def read_config(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()
'''

_IO_INIT = '"""app package."""\n'

_IO_FUNCTIONAL = """from app.io import read_all, read_config


def test_read_all_returns_contents_in_order(tmp_path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("A")
    b.write_text("B")
    assert read_all([str(b), str(a)]) == ["B", "A"]


def test_read_all_empty():
    assert read_all([]) == []


def test_read_config_unchanged(tmp_path):
    p = tmp_path / "c.cfg"
    p.write_text("x=1")
    assert read_config(str(p)) == "x=1"
"""

_IO_CONTRACT_ERR = {
    "wrap": """import pytest

from app.errors import AppError
from app.io import read_all


def test_missing_file_is_wrapped_in_apperror(tmp_path):
    with pytest.raises(AppError):
        read_all([str(tmp_path / "nope.txt")])
""",
    "propagate": """import pytest

from app.errors import AppError
from app.io import read_all


def test_missing_file_propagates_oserror(tmp_path):
    with pytest.raises(OSError) as ei:
        read_all([str(tmp_path / "nope.txt")])
    assert not isinstance(ei.value, AppError)
""",
}

_IO_CONTRACT_LOG = {
    "warn": """import logging

import pytest

from app.io import read_all


def test_missing_file_logs_warning_with_path(tmp_path, caplog):
    missing = str(tmp_path / "nope.txt")
    with caplog.at_level(logging.WARNING, logger="app.io"):
        try:
            read_all([missing])
        except Exception:
            pass
    recs = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert recs, "expected a WARNING record"
    assert any(getattr(r, "path", None) == missing for r in recs)
""",
    "silent": """import logging

from app.io import read_all


def test_missing_file_logs_nothing(tmp_path, caplog):
    missing = str(tmp_path / "nope.txt")
    with caplog.at_level(logging.DEBUG):
        try:
            read_all([missing])
        except Exception:
            pass
    assert not caplog.records
""",
}

_IO_TEXT = {
    (
        "error surface",
        "wrap",
    ): "I/O failures are reported by raising app.errors.AppError (chain the original); never let OSError escape public functions.",
    (
        "error surface",
        "propagate",
    ): "I/O failures propagate as the original OSError; never wrap them in AppError.",
    (
        "logging policy",
        "warn",
    ): "On a failed file operation, log once at WARNING on the module logger with the file path in the record's extra field `path`.",
    (
        "logging policy",
        "silent",
    ): "Public functions never log; leave logging to the caller.",
}


def _io_gold(err: str, logp: str) -> str:
    log_line = (
        '            log.warning("failed to read %s", path, extra={"path": path})\n'
        if logp == "warn"
        else ""
    )
    if err == "wrap":
        handler = f"""        try:
            with open(path, encoding="utf-8") as fh:
                out.append(fh.read())
        except OSError as exc:
{log_line}            raise AppError(f"cannot read {{path}}") from exc"""
    else:
        handler = f"""        try:
            with open(path, encoding="utf-8") as fh:
                out.append(fh.read())
        except OSError:
{log_line}            raise"""
    return (
        _IO_MODULE.rstrip("\n")
        + f"""


def read_all(paths: list[str]) -> list[str]:
    out: list[str] = []
    for path in paths:
{handler}
    return out
"""
    )


def fileio_tasks() -> list[Task]:
    tasks = []
    for err, logp in product(("wrap", "propagate"), ("warn", "silent")):
        contracts = [
            ContractState("error surface", err, _IO_TEXT[("error surface", err)]),
            ContractState("logging policy", logp, _IO_TEXT[("logging policy", logp)]),
        ]
        tasks.append(
            Task(
                id=f"fileio-{err}-{logp}",
                project="fileio",
                files={
                    "app/__init__.py": _IO_INIT,
                    "app/errors.py": _IO_ERRORS,
                    "app/io.py": _IO_MODULE,
                },
                target="app/io.py",
                request=(
                    "Add a function `read_all(paths: list[str]) -> list[str]` to app/io.py "
                    "that reads each file and returns their contents in the order given."
                ),
                contracts=contracts,
                functional_tests={"tests/test_read_all.py": _IO_FUNCTIONAL},
                contract_tests={
                    "tests/test_contract_error.py": _IO_CONTRACT_ERR[err],
                    "tests/test_contract_logging.py": _IO_CONTRACT_LOG[logp],
                },
                gold=_io_gold(err, logp),
            )
        )
    return tasks


# ------------------------------------------------------------------------------- users
# families: validation entry (api | storage), naming contract (verb_noun | noun_verb)

_US_STORAGE = '''"""User storage."""


class UserStore:
    def __init__(self) -> None:
        self._users: dict[str, dict] = {}
        self.saves = 0

    def save(self, user: dict) -> None:
        if "@" not in user.get("email", ""):
            raise ValueError("invalid email")
        self.saves += 1
        self._users[user["name"]] = dict(user)

    def load(self, name: str) -> dict | None:
        u = self._users.get(name)
        return dict(u) if u else None
'''

_US_API = '''"""Public user API."""

from svc.storage import UserStore


def create_user(store: UserStore, name: str, email: str) -> dict:
    if "@" not in email:
        raise ValueError("invalid email")
    user = {"name": name, "email": email}
    store.save(user)
    return user
'''

_US_INIT = '"""svc package."""\n'

_US_FUNCTIONAL = """import pytest

from svc import api
from svc.storage import UserStore


def _update():
    fn = getattr(api, "update_email", None) or getattr(api, "email_update", None)
    assert fn is not None, "no update function found"
    return fn


def test_update_changes_stored_email():
    store = UserStore()
    api.create_user(store, "ann", "ann@x.io")
    _update()(store, "ann", "ann@y.io")
    assert store.load("ann")["email"] == "ann@y.io"


def test_update_unknown_user_raises_keyerror():
    store = UserStore()
    with pytest.raises(KeyError):
        _update()(store, "nobody", "a@b.c")


def test_create_unchanged():
    store = UserStore()
    assert api.create_user(store, "bo", "bo@x.io")["email"] == "bo@x.io"
"""

_US_CONTRACT_VALID = {
    "api": """import pytest

from svc import api
from svc.storage import UserStore


def test_bad_email_rejected_before_storage():
    fn = getattr(api, "update_email", None) or getattr(api, "email_update", None)

    class Spy(UserStore):
        def __init__(self):
            super().__init__()
            self.calls = []

        def save(self, user):
            self.calls.append(dict(user))
            return super().save(user)

    spy = Spy()
    api.create_user(spy, "ann", "ann@x.io")
    spy.calls.clear()
    with pytest.raises(ValueError):
        fn(spy, "ann", "not-an-email")
    assert not spy.calls, "storage must not be reached with invalid input"
""",
    "storage": """import pytest

from svc import api
from svc.storage import UserStore


def test_bad_email_rejected_by_storage_not_api():
    fn = getattr(api, "update_email", None) or getattr(api, "email_update", None)
    store = UserStore()
    api.create_user(store, "ann", "ann@x.io")

    class Spy(UserStore):
        def __init__(self):
            super().__init__()
            self.calls = []

        def save(self, user):
            self.calls.append(dict(user))
            return super().save(user)

    spy = Spy()
    api.create_user(spy, "ann", "ann@x.io")
    with pytest.raises(ValueError):
        fn(spy, "ann", "not-an-email")
    assert spy.calls and spy.calls[-1]["email"] == "not-an-email", (
        "the API must pass the value through; validation belongs to storage"
    )
""",
}

_US_CONTRACT_NAME = {
    "verb_noun": """from svc import api


def test_public_name_is_verb_noun():
    assert hasattr(api, "update_email") and not hasattr(api, "email_update")
""",
    "noun_verb": """from svc import api


def test_public_name_is_noun_verb():
    assert hasattr(api, "email_update") and not hasattr(api, "update_email")
""",
}

_US_TEXT = {
    (
        "validation entry",
        "api",
    ): "Input validation happens at the public API boundary: public functions raise ValueError on invalid input before touching storage.",
    (
        "validation entry",
        "storage",
    ): "Input validation happens in the storage layer only: public API functions pass values through unchanged and never validate themselves.",
    (
        "naming contract",
        "verb_noun",
    ): "Public API function names are verb_noun (e.g. create_user, delete_user).",
    (
        "naming contract",
        "noun_verb",
    ): "Public API function names are noun_verb (e.g. user_create, user_delete); create_user is grandfathered.",
}


def _us_gold(valid: str, name: str) -> str:
    fn = "update_email" if name == "verb_noun" else "email_update"
    check = (
        '    if "@" not in email:\n        raise ValueError("invalid email")\n'
        if valid == "api"
        else ""
    )
    return (
        _US_API.rstrip("\n")
        + f"""


def {fn}(store: UserStore, name: str, email: str) -> dict:
{check}    user = store.load(name)
    if user is None:
        raise KeyError(name)
    user["email"] = email
    store.save(user)
    return user
"""
    )


def users_tasks() -> list[Task]:
    tasks = []
    for valid, name in product(("api", "storage"), ("verb_noun", "noun_verb")):
        contracts = [
            ContractState(
                "validation entry", valid, _US_TEXT[("validation entry", valid)]
            ),
            ContractState("naming contract", name, _US_TEXT[("naming contract", name)]),
        ]
        tasks.append(
            Task(
                id=f"users-{valid}-{name}",
                project="users",
                files={
                    "svc/__init__.py": _US_INIT,
                    "svc/storage.py": _US_STORAGE,
                    "svc/api.py": _US_API,
                },
                target="svc/api.py",
                request=(
                    "Add a public function to svc/api.py that changes an existing user's "
                    "email: it takes (store, name, email), raises KeyError if the user does "
                    "not exist, saves the updated user and returns it."
                ),
                contracts=contracts,
                functional_tests={"tests/test_update.py": _US_FUNCTIONAL},
                contract_tests={
                    "tests/test_contract_validation.py": _US_CONTRACT_VALID[valid],
                    "tests/test_contract_naming.py": _US_CONTRACT_NAME[name],
                },
                gold=_us_gold(valid, name),
            )
        )
    return tasks


# ------------------------------------------------------------------------------ config
# families: dependency choice (json | orjson), immutability (frozen | inplace)

_CF_MODEL = {
    "frozen": '''"""Configuration model."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    name: str
    debug: bool = False
    retries: int = 3
''',
    "inplace": '''"""Configuration model."""

from dataclasses import dataclass


@dataclass
class Config:
    name: str
    debug: bool = False
    retries: int = 3
''',
}

_CF_LOADER = {
    "json": '''"""Configuration loading."""

import json
from dataclasses import asdict

from cfg.model import Config


def load_config(path: str) -> Config:
    with open(path, encoding="utf-8") as fh:
        return Config(**json.load(fh))


def dump_config(config: Config, path: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(asdict(config), fh)
''',
    "orjson": '''"""Configuration loading."""

from dataclasses import asdict

from cfg.model import Config

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


def load_config(path: str) -> Config:
    with open(path, "rb") as fh:
        return Config(**_loads(fh.read()))


def dump_config(config: Config, path: str) -> None:
    with open(path, "wb") as fh:
        fh.write(_dumps(asdict(config)))
''',
}

_CF_INIT = '"""cfg package."""\n'

_CF_FUNCTIONAL = """from cfg.loader import dump_config, load_config, with_value
from cfg.model import Config


def test_with_value_sets_field():
    c = Config("svc")
    c2 = with_value(c, "retries", 9)
    assert c2.retries == 9 and c2.name == "svc"


def test_with_value_unknown_field_raises():
    import pytest

    with pytest.raises((AttributeError, KeyError, ValueError, TypeError)):
        with_value(Config("svc"), "nope", 1)


def test_roundtrip_unchanged(tmp_path):
    p = tmp_path / "c.json"
    dump_config(Config("svc", True, 5), str(p))
    assert load_config(str(p)) == Config("svc", True, 5)
"""

_CF_CONTRACT_DEP = {
    "json": """import sys
import types

import pytest


def test_orjson_never_used(tmp_path, monkeypatch):
    fake = types.ModuleType("orjson")

    def boom(*a, **k):
        raise AssertionError("orjson must not be used")

    fake.dumps = boom
    fake.loads = boom
    monkeypatch.setitem(sys.modules, "orjson", fake)
    for m in [m for m in sys.modules if m.startswith("cfg")]:
        monkeypatch.delitem(sys.modules, m)
    from cfg.loader import dump_config, load_config, with_value
    from cfg.model import Config

    p = tmp_path / "c.json"
    c = with_value(Config("svc"), "debug", True)
    dump_config(c, str(p))
    assert load_config(str(p)).debug is True
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
    for m in [m for m in sys.modules if m.startswith("cfg")]:
        monkeypatch.delitem(sys.modules, m)
    from cfg.loader import dump_config, load_config, with_value
    from cfg.model import Config

    p = tmp_path / "c.json"
    dump_config(with_value(Config("svc"), "debug", True), str(p))
    assert load_config(str(p)).debug is True
    assert "dumps" in calls and "loads" in calls


def test_falls_back_to_json_without_orjson(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "orjson", None)
    for m in [m for m in sys.modules if m.startswith("cfg")]:
        monkeypatch.delitem(sys.modules, m)
    from cfg.loader import dump_config, load_config
    from cfg.model import Config

    p = tmp_path / "c.json"
    dump_config(Config("svc", retries=1), str(p))
    assert load_config(str(p)).retries == 1
""",
}

_CF_CONTRACT_IMM = {
    "frozen": """from cfg.loader import with_value
from cfg.model import Config


def test_with_value_returns_new_object_and_leaves_original():
    c = Config("svc")
    c2 = with_value(c, "debug", True)
    assert c2 is not c and c.debug is False and c2.debug is True
""",
    "inplace": """from cfg.loader import with_value
from cfg.model import Config


def test_with_value_mutates_in_place_and_returns_same_object():
    c = Config("svc")
    c2 = with_value(c, "debug", True)
    assert c2 is c and c.debug is True
""",
}

_CF_TEXT = {
    (
        "dependency choice",
        "json",
    ): "JSON handling uses the standard library json module only; never import or use orjson.",
    (
        "dependency choice",
        "orjson",
    ): "JSON handling goes through the module's orjson-backed helpers (_loads/_dumps, which fall back to json); never call json directly from public functions.",
    (
        "immutability",
        "frozen",
    ): "Config objects are immutable: functions that change a setting return a new Config and never mutate their argument.",
    (
        "immutability",
        "inplace",
    ): "Config objects are mutable: functions that change a setting update the given Config in place and return that same object.",
}


def _cf_gold(dep: str, imm: str) -> str:
    if imm == "frozen":
        body = """    if not hasattr(config, key):
        raise AttributeError(key)
    return replace(config, **{key: value})"""
        imp = "from dataclasses import replace\n"
    else:
        body = """    if not hasattr(config, key):
        raise AttributeError(key)
    setattr(config, key, value)
    return config"""
        imp = ""
    return (
        imp
        + _CF_LOADER[dep].rstrip("\n")
        + f"""


def with_value(config: Config, key: str, value) -> Config:
{body}
"""
    )


def config_tasks() -> list[Task]:
    tasks = []
    for dep, imm in product(("json", "orjson"), ("frozen", "inplace")):
        contracts = [
            ContractState(
                "dependency choice", dep, _CF_TEXT[("dependency choice", dep)]
            ),
            ContractState("immutability", imm, _CF_TEXT[("immutability", imm)]),
        ]
        tasks.append(
            Task(
                id=f"config-{dep}-{imm}",
                project="config",
                files={
                    "cfg/__init__.py": _CF_INIT,
                    "cfg/model.py": _CF_MODEL[imm],
                    "cfg/loader.py": _CF_LOADER[dep],
                },
                target="cfg/loader.py",
                request=(
                    "Add a function `with_value(config: Config, key: str, value) -> Config` "
                    "to cfg/loader.py that sets the named setting to the value and returns "
                    "the resulting Config; an unknown key raises AttributeError."
                ),
                contracts=contracts,
                functional_tests={"tests/test_with_value.py": _CF_FUNCTIONAL},
                contract_tests={
                    "tests/test_contract_dependency.py": _CF_CONTRACT_DEP[dep],
                    "tests/test_contract_immutability.py": _CF_CONTRACT_IMM[imm],
                },
                gold=_cf_gold(dep, imm),
            )
        )
    return tasks


def all_tasks() -> list[Task]:
    return kvstore_tasks() + fileio_tasks() + users_tasks() + config_tasks()
