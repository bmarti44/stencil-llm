# ruff: noqa: E501
"""S23: warehouse bins — validation (target, scope) x error_surface (support)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""binrack package."""\n'

_MODEL = '''"""Bin records."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Bin:
    bin_id: str
    aisle: str
    capacity: int
    quantity: int = 0
'''

_MOVEMENTS = '''"""Append-only stock movement log on disk."""


def append_movement(path: str, line: str) -> None:
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(line + "\\n")
'''

_RACK_HEAD = '''"""Bin table (storage layer) and the public rack operations."""

from dataclasses import replace

from binrack import movements
from binrack.model import Bin


class BinTable:
    def __init__(self, movements_path: str | None = None) -> None:
        self.movements_path = movements_path
        self._bins: dict[str, Bin] = {}

    def _record(self, line: str) -> None:
        if self.movements_path is not None:
            movements.append_movement(self.movements_path, line)

    def insert_bin(self, bin_: Bin) -> None:
        if bin_.capacity <= 0:
            raise ValueError("capacity must be positive")
        self._bins[bin_.bin_id] = bin_
        self._record(f"new {bin_.bin_id}")

    def get_bin(self, bin_id: str) -> Bin:
        return self._bins[bin_id]

    def next_id(self) -> str:
        return f"B{len(self._bins) + 1}"
'''

_ADD_BIN = """

def add_bin(table: BinTable, aisle: str, capacity: int) -> Bin:
    bin_ = Bin(table.next_id(), aisle, capacity)
    table.insert_bin(bin_)
    return bin_
"""

_RACK = _RACK_HEAD + _ADD_BIN

_FILES = {
    "binrack/__init__.py": _INIT,
    "binrack/model.py": _MODEL,
    "binrack/movements.py": _MOVEMENTS,
    "binrack/rack.py": _RACK,
}


def _add_stock(state: str) -> str:
    check = (
        '        if qty <= 0:\n            raise ValueError("qty must be positive")\n'
        if state == "storage"
        else ""
    )
    return (
        "\n    def add_stock(self, bin_id: str, qty: int) -> Bin:\n"
        "        current = self._bins[bin_id]\n"
        + check
        + "        updated = replace(current, quantity=current.quantity + qty)\n"
        "        self._bins[bin_id] = updated\n"
        '        self._record(f"in {bin_id} {qty}")\n'
        "        return updated\n"
    )


def _receive_stock(state: str) -> str:
    check = (
        '    if qty <= 0:\n        raise ValueError("qty must be positive")\n'
        if state == "api"
        else ""
    )
    return (
        "\n\ndef receive_stock(table: BinTable, bin_id: str, qty: int) -> Bin:\n"
        + check
        + "    return table.add_stock(bin_id, qty)\n"
    )


def _remove_stock(state: str) -> str:
    check = (
        "        if qty <= 0 or qty > current.quantity:\n"
        '            raise ValueError("qty must be positive and no more than on hand")\n'
        if state == "storage"
        else ""
    )
    return (
        "\n    def remove_stock(self, bin_id: str, qty: int) -> Bin:\n"
        "        current = self._bins[bin_id]\n"
        + check
        + "        updated = replace(current, quantity=current.quantity - qty)\n"
        "        self._bins[bin_id] = updated\n"
        '        self._record(f"out {bin_id} {qty}")\n'
        "        return updated\n"
    )


def _pick_stock(state: str) -> str:
    check = (
        "    if qty <= 0 or qty > table.get_bin(bin_id).quantity:\n"
        '        raise ValueError("qty must be positive and no more than on hand")\n'
        if state == "api"
        else ""
    )
    return (
        "\n\ndef pick_stock(table: BinTable, bin_id: str, qty: int) -> Bin:\n"
        + check
        + "    return table.remove_stock(bin_id, qty)\n"
    )


def _gold1(state: str) -> str:
    return _RACK_HEAD + _add_stock(state) + _ADD_BIN + _receive_stock(state)


def _gold2(state: str) -> str:
    # Built on the checkpoint-1 gold under the state then in force (storage).
    return (
        _RACK_HEAD
        + _add_stock("storage")
        + _remove_stock(state)
        + _ADD_BIN
        + _receive_stock("storage")
        + _pick_stock(state)
    )


# ----------------------------------------------------------------- checkpoint 1: receive_stock

_C1_FUNCTIONAL = {
    "test_receive_functional.py": """import pytest

from binrack.rack import BinTable, add_bin, receive_stock


def _setup(path=None):
    t = BinTable(movements_path=path)
    b = add_bin(t, "A1", 100)
    return t, b


def test_receive_stock_adds_quantity_and_returns_bin():
    t, b = _setup()
    other = add_bin(t, "A2", 50)
    receive_stock(t, other.bin_id, 7)
    out = receive_stock(t, b.bin_id, 30)
    assert out.quantity == 30 and out.bin_id == b.bin_id and out.capacity == 100
    assert t.get_bin(b.bin_id).quantity == 30
    kept = t.get_bin(other.bin_id)
    assert kept.quantity == 7 and kept.aisle == "A2" and kept.capacity == 50
    assert t.get_bin(b.bin_id).aisle == "A1"
    assert t.next_id() == "B3"


def test_receive_stock_accumulates():
    t, b = _setup()
    other = add_bin(t, "A2", 50)
    receive_stock(t, other.bin_id, 7)
    receive_stock(t, b.bin_id, 30)
    out = receive_stock(t, b.bin_id, 12)
    assert out.quantity == 42
    assert t.get_bin(b.bin_id).quantity == 42
    kept = t.get_bin(other.bin_id)
    assert kept.quantity == 7 and kept.capacity == 50
    assert t.next_id() == "B3"


def test_receive_stock_records_movement(tmp_path):
    t, b = _setup(str(tmp_path / "moves.log"))
    receive_stock(t, b.bin_id, 5)
    lines = (tmp_path / "moves.log").read_text().splitlines()
    assert lines == [f"new {b.bin_id}", f"in {b.bin_id} 5"]
    other = add_bin(t, "A2", 50)
    receive_stock(t, other.bin_id, 9)
    later = (tmp_path / "moves.log").read_text().splitlines()
    assert later[-2:] == [f"new {other.bin_id}", f"in {other.bin_id} 9"]
    assert t.get_bin(b.bin_id).quantity == 5
    assert t.get_bin(other.bin_id).quantity == 9
    assert t.next_id() == "B3"


def test_receive_unknown_bin_raises_keyerror():
    t, b = _setup()
    other = add_bin(t, "A2", 50)
    receive_stock(t, other.bin_id, 7)
    with pytest.raises(KeyError):
        receive_stock(t, "B99", 5)
    assert t.get_bin(other.bin_id).quantity == 7
    assert t.get_bin(b.bin_id).quantity == 0
    assert t.next_id() == "B3"


def test_receive_nonpositive_qty_raises_and_changes_nothing():
    t, b = _setup()
    other = add_bin(t, "A2", 50)
    receive_stock(t, other.bin_id, 7)
    for bad in (0, -3):
        with pytest.raises(ValueError):
            receive_stock(t, b.bin_id, bad)
    assert t.get_bin(b.bin_id).quantity == 0
    kept = t.get_bin(other.bin_id)
    assert kept.quantity == 7 and kept.capacity == 50
    assert t.next_id() == "B3"


def test_table_has_add_stock():
    t, b = _setup()
    other = add_bin(t, "A2", 50)
    t.add_stock(other.bin_id, 9)
    out = t.add_stock(b.bin_id, 7)
    assert out.quantity == 7 and t.get_bin(b.bin_id).quantity == 7
    kept = t.get_bin(other.bin_id)
    assert kept.quantity == 9 and kept.capacity == 50
    assert t.next_id() == "B3"
"""
}

_C1_REGRESSION = {
    "test_receive_regression.py": """import pytest

from binrack.rack import BinTable, add_bin


def test_add_bin_unchanged(tmp_path):
    t = BinTable(movements_path=str(tmp_path / "moves.log"))
    b = add_bin(t, "A1", 100)
    assert b.bin_id == "B1" and b.quantity == 0 and t.get_bin("B1") is b
    assert (tmp_path / "moves.log").read_text() == "new B1\\n"
    second = add_bin(t, "A2", 50)
    assert second.bin_id == "B2" and t.get_bin("B2") is second
    assert t.get_bin("B1") is b and t.next_id() == "B3"
    assert (tmp_path / "moves.log").read_text() == "new B1\\nnew B2\\n"
    with pytest.raises(ValueError):
        add_bin(t, "A2", 0)
    with pytest.raises(KeyError):
        t.get_bin("B9")
    t.movements_path = str(tmp_path)
    with pytest.raises(OSError):
        add_bin(t, "A3", 10)
"""
}

_C1_CONTRACT = {
    "api": {
        "test_receive_validation.py": """import pytest

from binrack.rack import BinTable, add_bin, receive_stock


def test_public_function_rejects_nonpositive_qty():
    t = BinTable()
    b = add_bin(t, "A1", 100)
    for bad in (0, -3):
        with pytest.raises(ValueError):
            receive_stock(t, b.bin_id, bad)
    assert t.get_bin(b.bin_id).quantity == 0


def test_table_trusts_callers_on_qty():
    t = BinTable()
    b = add_bin(t, "A1", 100)
    out = t.add_stock(b.bin_id, 0)
    assert out.quantity == 0
    out = t.add_stock(b.bin_id, -3)
    assert out.quantity == -3 and t.get_bin(b.bin_id).quantity == -3
"""
    },
    "storage": {
        "test_receive_validation.py": """import pytest

from binrack.rack import BinTable, add_bin, receive_stock


def test_table_rejects_nonpositive_qty():
    t = BinTable()
    b = add_bin(t, "A1", 100)
    for bad in (0, -3):
        with pytest.raises(ValueError):
            t.add_stock(b.bin_id, bad)
    assert t.get_bin(b.bin_id).quantity == 0


def test_public_function_passes_invalid_qty_through(monkeypatch):
    t = BinTable()
    b = add_bin(t, "A1", 100)
    seen = []
    real = t.add_stock

    def spy(bin_id, qty):
        seen.append((bin_id, qty))
        return real(bin_id, qty)

    monkeypatch.setattr(t, "add_stock", spy)
    with pytest.raises(ValueError):
        receive_stock(t, b.bin_id, -3)
    assert seen == [(b.bin_id, -3)]
"""
    },
}

_C1_SUPPORT = {
    "test_receive_errors.py": """import pytest

from binrack.rack import BinTable, add_bin, receive_stock


def test_movement_log_failure_propagates_raw_oserror(tmp_path):
    t = BinTable()
    b = add_bin(t, "A1", 100)
    t.movements_path = str(tmp_path)  # a directory: appending raises OSError
    with pytest.raises(OSError) as ei:
        receive_stock(t, b.bin_id, 5)
    assert type(ei.value).__module__ == "builtins"
"""
}

_REQ1 = Request(
    text=(
        "Add receiving. Give BinTable an `add_stock(bin_id, qty)` method that replaces the "
        "stored bin with a copy whose quantity is increased by qty, records the movement "
        "`in <bin_id> <qty>` and returns the updated bin (an unknown id raises KeyError), "
        "and add a public function `receive_stock(table, bin_id, qty)` that applies it and "
        "returns the updated Bin. A qty of zero or less is invalid and must raise "
        "ValueError."
    ),
    target="binrack/rack.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"api": _gold1("api"), "storage": _gold1("storage")},
)

# ----------------------------------------------------------------- checkpoint 2: pick_stock

_C2_FUNCTIONAL = {
    "test_pick_functional.py": """import pytest

from binrack.rack import BinTable, add_bin, pick_stock, receive_stock


def _setup(path=None):
    t = BinTable(movements_path=path)
    b = add_bin(t, "A1", 100)
    receive_stock(t, b.bin_id, 40)
    return t, b


def test_pick_stock_reduces_quantity_and_returns_bin():
    t, b = _setup()
    other = add_bin(t, "A2", 50)
    receive_stock(t, other.bin_id, 12)
    out = pick_stock(t, b.bin_id, 15)
    assert out.quantity == 25 and out.bin_id == b.bin_id
    assert t.get_bin(b.bin_id).quantity == 25
    kept = t.get_bin(other.bin_id)
    assert kept.quantity == 12 and kept.aisle == "A2" and kept.capacity == 50
    assert t.get_bin(b.bin_id).capacity == 100
    assert t.next_id() == "B3"


def test_pick_whole_bin_leaves_zero():
    t, b = _setup()
    other = add_bin(t, "A2", 50)
    receive_stock(t, other.bin_id, 12)
    assert pick_stock(t, b.bin_id, 40).quantity == 0
    assert t.get_bin(b.bin_id).quantity == 0
    assert t.get_bin(other.bin_id).quantity == 12
    assert t.next_id() == "B3"


def test_pick_stock_records_movement(tmp_path):
    t, b = _setup(str(tmp_path / "moves.log"))
    other = add_bin(t, "A2", 50)
    receive_stock(t, other.bin_id, 12)
    pick_stock(t, b.bin_id, 3)
    lines = (tmp_path / "moves.log").read_text().splitlines()
    assert lines[-1] == f"out {b.bin_id} 3"
    assert t.get_bin(other.bin_id).quantity == 12
    assert t.next_id() == "B3"


def test_pick_unknown_bin_raises_keyerror():
    t, b = _setup()
    other = add_bin(t, "A2", 50)
    receive_stock(t, other.bin_id, 12)
    with pytest.raises(KeyError):
        pick_stock(t, "B99", 1)
    assert t.get_bin(other.bin_id).quantity == 12
    assert t.get_bin(b.bin_id).quantity == 40
    assert t.next_id() == "B3"


def test_pick_invalid_qty_raises_and_changes_nothing():
    t, b = _setup()
    other = add_bin(t, "A2", 50)
    receive_stock(t, other.bin_id, 12)
    for bad in (0, -1, 41):
        with pytest.raises(ValueError):
            pick_stock(t, b.bin_id, bad)
    assert t.get_bin(b.bin_id).quantity == 40
    kept = t.get_bin(other.bin_id)
    assert kept.quantity == 12 and kept.capacity == 50
    assert t.next_id() == "B3"


def test_table_has_remove_stock():
    t, b = _setup()
    other = add_bin(t, "A2", 50)
    receive_stock(t, other.bin_id, 12)
    out = t.remove_stock(b.bin_id, 10)
    assert out.quantity == 30 and t.get_bin(b.bin_id).quantity == 30
    kept = t.get_bin(other.bin_id)
    assert kept.quantity == 12 and kept.capacity == 50
    assert t.next_id() == "B3"
"""
}

_C2_REGRESSION = {
    "test_pick_regression.py": """import pytest

from binrack.rack import BinTable, add_bin, receive_stock


def test_bins_and_receiving_unchanged(tmp_path):
    t = BinTable(movements_path=str(tmp_path / "moves.log"))
    b = add_bin(t, "A1", 100)
    assert receive_stock(t, b.bin_id, 20).quantity == 20
    assert (tmp_path / "moves.log").read_text().splitlines() == ["new B1", "in B1 20"]
    second = add_bin(t, "A2", 50)
    assert receive_stock(t, second.bin_id, 9).quantity == 9
    kept = t.get_bin(b.bin_id)
    assert kept.quantity == 20 and kept.capacity == 100 and kept.aisle == "A1"
    assert t.get_bin(second.bin_id).quantity == 9 and t.next_id() == "B3"
    with pytest.raises(ValueError):
        receive_stock(t, b.bin_id, 0)
    with pytest.raises(ValueError):
        add_bin(t, "A2", -1)
    with pytest.raises(KeyError):
        receive_stock(t, "B9", 1)
    t.movements_path = str(tmp_path)
    with pytest.raises(OSError):
        receive_stock(t, b.bin_id, 1)
"""
}

_C2_CONTRACT = {
    "api": {
        "test_pick_validation.py": """import pytest

from binrack.rack import BinTable, add_bin, pick_stock, receive_stock


def _setup():
    t = BinTable()
    b = add_bin(t, "A1", 100)
    receive_stock(t, b.bin_id, 40)
    return t, b


def test_public_function_rejects_invalid_qty():
    t, b = _setup()
    for bad in (0, -1, 41):
        with pytest.raises(ValueError):
            pick_stock(t, b.bin_id, bad)
    assert t.get_bin(b.bin_id).quantity == 40


def test_table_trusts_callers_on_qty():
    t, b = _setup()
    out = t.remove_stock(b.bin_id, 0)
    assert out.quantity == 40
    out = t.remove_stock(b.bin_id, 41)
    assert out.quantity == -1 and t.get_bin(b.bin_id).quantity == -1
"""
    },
    "storage": {
        "test_pick_validation.py": """import pytest

from binrack.rack import BinTable, add_bin, pick_stock, receive_stock


def _setup():
    t = BinTable()
    b = add_bin(t, "A1", 100)
    receive_stock(t, b.bin_id, 40)
    return t, b


def test_table_rejects_invalid_qty():
    t, b = _setup()
    for bad in (0, -1, 41):
        with pytest.raises(ValueError):
            t.remove_stock(b.bin_id, bad)
    assert t.get_bin(b.bin_id).quantity == 40


def test_public_function_passes_invalid_qty_through(monkeypatch):
    t, b = _setup()
    seen = []
    real = t.remove_stock

    def spy(bin_id, qty):
        seen.append((bin_id, qty))
        return real(bin_id, qty)

    monkeypatch.setattr(t, "remove_stock", spy)
    with pytest.raises(ValueError):
        pick_stock(t, b.bin_id, 0)
    assert seen == [(b.bin_id, 0)]
"""
    },
}

_C2_SUPPORT = {
    "test_pick_errors.py": """import pytest

from binrack.rack import BinTable, add_bin, pick_stock, receive_stock


def test_movement_log_failure_propagates_raw_oserror(tmp_path):
    t = BinTable()
    b = add_bin(t, "A1", 100)
    receive_stock(t, b.bin_id, 40)
    t.movements_path = str(tmp_path)  # a directory: appending raises OSError
    with pytest.raises(OSError) as ei:
        pick_stock(t, b.bin_id, 5)
    assert type(ei.value).__module__ == "builtins"
"""
}

_REQ2 = Request(
    text=(
        "Add picking. Give BinTable a `remove_stock(bin_id, qty)` method that replaces the "
        "stored bin with a copy whose quantity is reduced by qty, records the movement "
        "`out <bin_id> <qty>` and returns the updated bin (an unknown id raises KeyError), "
        "and add a public function `pick_stock(table, bin_id, qty)` that applies it and "
        "returns the updated Bin. A qty of zero or less, or more than the bin currently "
        "holds, is invalid and must raise ValueError."
    ),
    target="binrack/rack.py",
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
        "I look after the stockroom for a bicycle co-op: about eighty bins on four aisles, "
        "inner tubes and brake pads and the like, counted by hand on a clipboard. The "
        "clipboard gets lost. I want a small Python package, `binrack`, that keeps bins in "
        "memory and appends every stock movement to a plain-text file, so that when a count "
        "is off we can read back what happened. The nightly job is just:\n\n```\ncd /srv/"
        "coop && python -m binrack.count --movements /srv/coop/moves.log > /srv/coop/"
        "count.txt\n```\n\nMovements are maybe twenty a day. No barcode scanners, no "
        "database, no web page, and definitely no integration with the till, which is a "
        "1990s cash register. Could you draft the README scope so the committee does not "
        "expect a stock-control system? Last year someone suggested buying an ERP and I "
        "would like this to be the thing that makes that conversation unnecessary. The "
        "volunteers who will run the nightly job are comfortable with a terminal but not "
        "with Python, so the command line has to be the whole interface.",
    ),
    Turn(
        "assistant",
        "Scope plus non-goals, then a tiny usage block:\n\n```\n## Scope\nbinrack holds the "
        "stockroom's bins in memory for one process and appends every stock movement to a "
        "plain-text log. It is a library for small scripts, not a stock-control system, and "
        "the log is its only persistence.\n\n## Non-goals\n- barcode or scanner input\n- "
        "purchasing, reordering or supplier records\n- till or sales integration\n- "
        "multi-user editing\n```\n\n```python\nfrom binrack.rack import BinTable, add_bin\n\n"
        'table = BinTable(movements_path="/srv/coop/moves.log")\nb = add_bin(table, "A1", '
        "100)\nprint(b)\n```\n\nThe ERP conversation ends when you can show the committee a "
        "readable movement log and a count that matches it; keep the package small enough "
        "that a volunteer can read the whole thing in ten minutes. A one-line install note "
        "(`pip install -e .` in the co-op laptop's venv) saves you a support conversation "
        "with whoever runs it next year, and a dated 'last reviewed' line tells them "
        "whether to trust it.",
    ),
    Turn(
        "user",
        "The movement log format I have so far is one short line per event, verb first, "
        "then ids and numbers:\n\n```\nnew B1\nnew B2\nin B1 40\nin B2 12\nout B1 3\n```\n\n"
        "Human-readable on purpose; the co-op volunteers are not programmers. Aisle labels "
        "are painted on the floor and never change, so they are plain strings. The nightly "
        "job will read current state from a JSON dump I add later; the movement log is an "
        "audit trail, append-only and never rewritten. Bins have an aisle label like `A1` "
        "or `C4`, a capacity that is the physical size, and a quantity that starts at zero "
        "when the bin is created; stock arrives from suppliers in boxes and leaves when a "
        "member buys or borrows something. I put the write inside `BinTable` through a "
        "`_record` helper so no mutation can forget it. "
        "Is that the right place, or should the public functions record after the fact? "
        "I'm slightly worried about the table knowing about files at all, but the "
        "alternative seemed to be remembering to log in every public function.",
    ),
    Turn(
        "assistant",
        "Inside the table is right. Every mutation goes through a table method, so the log "
        "cannot miss one, and tests can point `movements_path` at a temp file and read it "
        "back; the public functions stay about building records. The `None` check living "
        "in one helper is the whole cost:\n\n```python\ndef _record(self, line: str) -> "
        "None:\n    if self.movements_path is not None:\n        movements.append_movement("
        "self.movements_path, line)\n```\n\nThe format is good: `verb id [number]` is "
        "regular enough that `line.split()` parses it if a script ever needs to, and a "
        "volunteer can read it without a key. Keep the verbs short and past-proof: `in` "
        "and `out` rather than `received` and `picked`, so the log does not change when the "
        "wording of the public functions does. Starting quantity at zero and adding stock "
        "as a separate movement is right too: every bin then has a `new` line followed by "
        "`in` lines, which reads naturally when a volunteer replays it.",
    ),
    Turn(
        "user",
        "This happened on the first real run, when the shared drive was not mounted:\n\n```"
        '\nTraceback (most recent call last):\n  File "/srv/coop/binrack/count.py", line '
        '22, in <module>\n    add_bin(table, aisle, cap)\n  File "/srv/coop/binrack/rack.py"'
        ', line 32, in add_bin\n    table.insert_bin(bin_)\n  File "/srv/coop/binrack/'
        'rack.py", line 20, in insert_bin\n    self._record(f"new {bin_.bin_id}")\n  File '
        '"/srv/coop/binrack/rack.py", line 14, in _record\n    movements.append_movement('
        'self.movements_path, line)\n  File "/srv/coop/binrack/movements.py", line 5, in '
        'append_movement\n    with open(path, "a", encoding="utf-8") as fh:\n'
        "FileNotFoundError: [Errno 2] No such file or directory: '/mnt/share/coop/moves.log'"
        "\n```\n\nHonestly I think that is the correct outcome. Should I wrap it in some "
        "`BinrackError`, or leave the OSError alone?",
    ),
    Turn(
        "assistant",
        "Leave it alone. The traceback already says exactly what went wrong and where, the "
        "caller is a script you control, and `except OSError` at the top of that script is "
        "one line:\n\n```python\ntry:\n    main()\nexcept OSError as exc:\n    sys.exit("
        'f"movement log unavailable: {exc}")\n```\n\nA package exception class earns its '
        "keep when callers need to treat several unrelated failures uniformly or when you "
        "want to hide the implementation; neither applies to a stockroom log. Wrapping "
        "would also bury the errno and the path one level deeper, which is the opposite of "
        "what a volunteer debugging a mount needs. If you ever add a second failure source "
        "(say a network call) you can revisit, but not before. For what it is worth, the "
        "usual 'why is the count wrong' investigation in a stockroom like this turns out to "
        "be a box counted twice; a movement log shows a doubled `in` line in about ten "
        "seconds, which is why the log matters more than the code around it. Make the "
        "script's exit message name the path so a volunteer knows which mount to check.",
    ),
    Turn(
        "user",
        "Good, that matches my instinct. Here is the counting script draft so you can see "
        "how bins are consumed; it only reads:\n\n```python\nfrom binrack.rack import "
        "BinTable\n\n\ndef print_count(table: BinTable, bin_ids: list[str]) -> None:\n    "
        "for bin_id in bin_ids:\n        b = table.get_bin(bin_id)\n        pct = 100 * "
        'b.quantity // b.capacity\n        print(f"{b.bin_id} {b.aisle} {b.quantity}/'
        '{b.capacity} ({pct}%)")\n```\n\nCapacity is a soft number, the physical size of '
        "the bin; I am not going to stop anyone overfilling it because volunteers do cram "
        "tubes in. The bin ids are also what volunteers write on the masking tape on the "
        "front of each bin, so `B12` has to be stable for the life of the bin; renumbering "
        "is off the table even when a bin is retired, which is why I mint ids from a "
        "counter and never reuse them. Is there anything in that loop you would change "
        "before I build on it?",
    ),
    Turn(
        "assistant",
        "Only one thing: `get_bin` raises KeyError for an unknown id, which is right for the "
        "table, but the count script is the one place a stale id list is plausible, so "
        "catch it there and keep going rather than losing the whole printout:\n\n```python\n"
        'try:\n    b = table.get_bin(bin_id)\nexcept KeyError:\n    print(f"{bin_id} '
        'unknown")\n    continue\n```\n\nThe percentage as integer division is fine for a '
        "stockroom, and leaving capacity advisory is sensible; if a future count wants to "
        "flag overfilled bins, that is an asterisk in this script, not a rule in the table. "
        "Never reusing ids is exactly right when they are written on physical tape; a "
        "retired bin can keep its id behind a `retired` flag later, and the counter never "
        "goes backwards. The `pct` division is safe as written because `insert_bin` "
        "already rejects a zero capacity, so the loop cannot divide by zero on any bin "
        "the table accepted. If you want the printout sorted by aisle, sort the id list "
        "in the script before the loop rather than adding ordering to the table; the "
        "table's job is to answer for one id at a time.",
    ),
    Turn(
        "user",
        "Two conventions to fix before the real features land. First, errors: file and I/O "
        "failures from the movement log propagate raw. No `BinrackError`, no wrapping, no "
        "catching inside `binrack.rack`; a caller sees the original OSError. That covers "
        "everything the table does, existing and new.",
    ),
    Turn(
        "assistant",
        "Noted: the movement log's OSError propagates unchanged through every table method "
        "and public function; no package exception class, no try/except around the write. "
        "New methods call `self._record(...)` and let failures fall through.",
    ),
    Turn(
        "user",
        "Second, validation: it lives in the table. `BinTable` methods check their own "
        "inputs and raise ValueError, the way `insert_bin` rejects a non-positive capacity "
        "today. Public functions build the arguments and hand them straight to the table "
        "with no pre-check of their own.",
    ),
    Turn(
        "assistant",
        "Understood: the table defends itself. New BinTable methods validate and raise "
        "ValueError, and public functions in `rack.py` pass arguments through without a "
        "separate check, matching `insert_bin` and `add_bin` as they are now.",
    ),
    Turn(
        "user",
        "For later: I'd like a `low_stock(threshold)` query on the table that lists bins "
        "under a quantity, so the nightly job can print a shopping list, and an "
        "`aisle_totals()` that sums quantities per aisle for the same printout. Not yet.",
    ),
    Turn(
        "assistant",
        "Noted for later. Both are read-only queries over the stored bins, one a filtered "
        "list of Bin and one a dict of aisle to total; neither touches the movement log, "
        "since nothing changes.",
    ),
    Turn(
        "user",
        "For the record, the tests that exist today are just these:\n\n```python\nimport "
        "pytest\n\nfrom binrack.rack import BinTable, add_bin\n\n\ndef "
        'test_add_bin_mints_b1():\n    assert add_bin(BinTable(), "A1", 50).bin_id == "B1"'
        "\n\n\ndef test_add_bin_rejects_zero_capacity():\n    with pytest.raises(ValueError)"
        ':\n        add_bin(BinTable(), "A1", 0)\n```\n\nI will paste the current files '
        "with each request so you see the real state.",
    ),
    Turn(
        "assistant",
        "Ready. Send the first feature and I will return the complete `rack.py`.",
    ),
]

_EVENT = (
    "One scoped change before the next feature. For the outbound side only, meaning any "
    "operation that takes stock out of a bin, validation lives in the public function: "
    "it raises ValueError before calling the table, and the table method for that "
    "operation trusts its caller and does not validate. Inbound operations and everything "
    "else keep validating in the table as they do now."
)


def build() -> Session:
    return Session(
        id="S23",
        project="binrack",
        target_family="validation",
        support_family="error_surface",
        lifecycle="scope",
        files=_FILES,
        prefix=_PREFIX,
        states=("storage", "api"),
        state_at=("storage", "api"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10),
    )
