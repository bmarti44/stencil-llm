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


def all_tasks() -> list[Task]:
    return kvstore_tasks() + fileio_tasks()
