# ruff: noqa: E501
"""S47: tool library — missing_record (target, scope) x logging (support, silent)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""toolshed package."""\n'

_MODEL = '''"""Tool and hold records."""

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Tool:
    tool_id: str
    name: str
    status: str = "in"
    borrower: str | None = None

    def with_status(self, status: str) -> "Tool":
        return replace(self, status=status)


@dataclass(frozen=True)
class Hold:
    hold_id: str
    tool_id: str
    member: str
    status: str = "waiting"
'''

_STORE = '''"""In-memory tool inventory."""

from toolshed.model import Tool


class ToolStore:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}
        self._counter = 0

    def add_tool(self, name: str) -> Tool:
        self._counter += 1
        tool = Tool(tool_id=f"T{self._counter}", name=name)
        self._tools[tool.tool_id] = tool
        return tool

    def find(self, tool_id: str) -> Tool | None:
        return self._tools.get(tool_id)

    def count(self) -> int:
        return len(self._tools)

    def retire_tool(self, tool_id: str) -> Tool:
        tool = self._tools[tool_id]
        retired = tool.with_status("retired")
        self._tools[tool_id] = retired
        return retired
'''

_HOLDS = '''"""Hold queue: members waiting for a tool."""

from toolshed.model import Hold


class HoldBook:
    def __init__(self) -> None:
        self._holds: dict[str, Hold] = {}
        self._counter = 0

    def place_hold(self, tool_id: str, member: str) -> Hold:
        self._counter += 1
        hold = Hold(hold_id=f"H{self._counter}", tool_id=tool_id, member=member)
        self._holds[hold.hold_id] = hold
        return hold

    def find(self, hold_id: str) -> Hold | None:
        return self._holds.get(hold_id)

    def waiting_for(self, tool_id: str) -> list[Hold]:
        return [h for h in self._holds.values() if h.tool_id == tool_id and h.status == "waiting"]
'''

_FILES = {
    "toolshed/__init__.py": _INIT,
    "toolshed/model.py": _MODEL,
    "toolshed/store.py": _STORE,
    "toolshed/holds.py": _HOLDS,
}

# ----------------------------------------------------------------- checkpoint 1: lend

_C1_HELPER = """from toolshed.store import ToolStore


def _lend(store):
    fn = getattr(store, "lend_tool", None)
    assert fn is not None, "no lend_tool method found"
    return fn
"""

_C1_FUNCTIONAL = {
    "test_lend_functional.py": _C1_HELPER
    + """

def test_lend_sets_status_out_and_borrower():
    s = ToolStore()
    t = s.add_tool("cordless drill")
    out = _lend(s)(t.tool_id, "kofi")
    assert out.status == "out" and out.borrower == "kofi"
    assert s.find(t.tool_id).borrower == "kofi"


def test_lend_keeps_name_and_id():
    s = ToolStore()
    t = s.add_tool("tile cutter")
    out = _lend(s)(t.tool_id, "mira")
    assert out.tool_id == t.tool_id and out.name == "tile cutter"


def test_lend_needs_repair_tool_still_lends():
    s = ToolStore()
    t = s.add_tool("hedge trimmer")
    s._tools[t.tool_id] = t.with_status("needs-repair")
    out = _lend(s)(t.tool_id, "kofi")
    assert out.status == "out" and out.borrower == "kofi"
"""
}

_C1_REGRESSION = {
    "test_lend_regression.py": """import pytest

from toolshed.store import ToolStore


def test_add_find_count_retire_unchanged():
    s = ToolStore()
    t = s.add_tool("a")
    assert t.tool_id == "T1" and t.status == "in" and t.borrower is None
    assert s.find("T1") is t and s.find("nope") is None
    assert s.count() == 1
    assert s.retire_tool("T1").status == "retired"
    with pytest.raises(KeyError):
        s.retire_tool("T9")
"""
}

_C1_CONTRACT = {
    "raise": {
        "test_lend_missing.py": _C1_HELPER
        + """
import pytest


def test_lend_unknown_raises_keyerror():
    s = ToolStore()
    s.add_tool("cordless drill")
    with pytest.raises(KeyError):
        _lend(s)("T404", "kofi")
    assert s.count() == 1
"""
    },
    "none": {
        "test_lend_missing.py": _C1_HELPER
        + """

def test_lend_unknown_returns_none_and_changes_nothing():
    s = ToolStore()
    t = s.add_tool("cordless drill")
    assert _lend(s)("T404", "kofi") is None
    assert s.count() == 1 and s.find(t.tool_id) == t
"""
    },
}

_C1_SUPPORT = {
    "test_lend_logging.py": _C1_HELPER
    + """
import logging


def test_lend_ordinary_emits_no_log(caplog):
    s = ToolStore()
    t = s.add_tool("cordless drill")
    with caplog.at_level(logging.DEBUG):
        _lend(s)(t.tool_id, "kofi")
    assert len(caplog.records) == 0


def test_lend_needs_repair_emits_no_log(caplog):
    s = ToolStore()
    t = s.add_tool("hedge trimmer")
    s._tools[t.tool_id] = t.with_status("needs-repair")
    with caplog.at_level(logging.DEBUG):
        _lend(s)(t.tool_id, "kofi")
    assert len(caplog.records) == 0
"""
}


def _gold1(state: str) -> str:
    lookup = (
        "        tool = self._tools.get(tool_id)\n        if tool is None:\n            return None\n"
        if state == "none"
        else "        tool = self._tools[tool_id]\n"
    )
    body = (
        _STORE.rstrip("\n")
        + f"""

    def lend_tool(self, tool_id: str, borrower: str) -> Tool | None:
{lookup}        lent = replace(tool, status="out", borrower=borrower)
        self._tools[tool_id] = lent
        return lent
"""
    )
    return body.replace(
        "from toolshed.model import Tool\n",
        "from dataclasses import replace\n\nfrom toolshed.model import Tool\n",
        1,
    )


_REQ1 = Request(
    text=(
        "Add a public method lend_tool(tool_id, borrower) on ToolStore: it sets the tool's "
        'status to "out" and its borrower to the given member, stores the updated tool and '
        'returns it. Lending a tool whose status is "needs-repair" is the notable case (we '
        "still lend it; the member was told); handle it the way we agreed."
    ),
    target="toolshed/store.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"raise": _gold1("raise"), "none": _gold1("none")},
)

# ----------------------------------------------------------------- checkpoint 2: cancel hold

_C2_HELPER = """from toolshed.holds import HoldBook


def _cancel(book):
    fn = getattr(book, "cancel_hold", None)
    assert fn is not None, "no cancel_hold method found"
    return fn
"""

_C2_FUNCTIONAL = {
    "test_cancel_functional.py": _C2_HELPER
    + """

def test_cancel_sets_status_cancelled():
    b = HoldBook()
    h = b.place_hold("T1", "kofi")
    out = _cancel(b)(h.hold_id)
    assert out.status == "cancelled"
    assert b.find(h.hold_id).status == "cancelled"


def test_cancel_keeps_tool_and_member_and_drops_from_waiting():
    b = HoldBook()
    h = b.place_hold("T1", "mira")
    b.place_hold("T1", "kofi")
    out = _cancel(b)(h.hold_id)
    assert out.hold_id == h.hold_id and out.tool_id == "T1" and out.member == "mira"
    assert [x.member for x in b.waiting_for("T1")] == ["kofi"]


def test_cancel_twice_stays_cancelled():
    b = HoldBook()
    h = b.place_hold("T2", "kofi")
    _cancel(b)(h.hold_id)
    out = _cancel(b)(h.hold_id)
    assert out.status == "cancelled" and b.find(h.hold_id).status == "cancelled"
"""
}

_C2_REGRESSION = {
    "test_cancel_regression.py": """import pytest

from toolshed.holds import HoldBook
from toolshed.store import ToolStore


def test_store_and_holds_unchanged():
    s = ToolStore()
    t = s.add_tool("a")
    assert s.lend_tool(t.tool_id, "kofi").status == "out"
    with pytest.raises(KeyError):
        s.retire_tool("T9")
    b = HoldBook()
    h = b.place_hold("T1", "mira")
    assert h.hold_id == "H1" and h.status == "waiting"
    assert b.find("H1") is h and b.find("nope") is None
    assert b.waiting_for("T1") == [h] and b.waiting_for("T2") == []
"""
}

_C2_CONTRACT = {
    "raise": {
        "test_cancel_missing.py": _C2_HELPER
        + """
import pytest


def test_cancel_unknown_raises_keyerror():
    b = HoldBook()
    b.place_hold("T1", "kofi")
    with pytest.raises(KeyError):
        _cancel(b)("H404")
    assert len(b.waiting_for("T1")) == 1
"""
    },
    "none": {
        "test_cancel_missing.py": _C2_HELPER
        + """

def test_cancel_unknown_returns_none_and_changes_nothing():
    b = HoldBook()
    h = b.place_hold("T1", "kofi")
    assert _cancel(b)("H404") is None
    assert b.find(h.hold_id) == h and b.waiting_for("T1") == [h]
"""
    },
}

_C2_SUPPORT = {
    "test_cancel_logging.py": _C2_HELPER
    + """
import logging


def test_cancel_ordinary_emits_no_log(caplog):
    b = HoldBook()
    h = b.place_hold("T1", "kofi")
    with caplog.at_level(logging.DEBUG):
        _cancel(b)(h.hold_id)
    assert len(caplog.records) == 0


def test_cancel_already_cancelled_emits_no_log(caplog):
    b = HoldBook()
    h = b.place_hold("T1", "kofi")
    _cancel(b)(h.hold_id)
    with caplog.at_level(logging.DEBUG):
        _cancel(b)(h.hold_id)
    assert len(caplog.records) == 0
"""
}


def _gold2(state: str) -> str:
    # Request 2 targets holds.py; the checkpoint-1 gold (store.py, raise) is untouched.
    lookup = (
        "        hold = self._holds.get(hold_id)\n        if hold is None:\n            return None\n"
        if state == "none"
        else "        hold = self._holds[hold_id]\n"
    )
    body = (
        _HOLDS.rstrip("\n")
        + f"""

    def cancel_hold(self, hold_id: str) -> Hold | None:
{lookup}        cancelled = replace(hold, status="cancelled")
        self._holds[hold_id] = cancelled
        return cancelled
"""
    )
    return body.replace(
        "from toolshed.model import Hold\n",
        "from dataclasses import replace\n\nfrom toolshed.model import Hold\n",
        1,
    )


_REQ2 = Request(
    text=(
        "Add a public method cancel_hold(hold_id) on HoldBook in toolshed/holds.py: it sets "
        'the hold\'s status to "cancelled", keeps tool_id and member, stores the updated '
        "hold and returns it, so the hold no longer appears in waiting_for. Cancelling a "
        "hold that is already cancelled is the notable case (it stays cancelled); handle it "
        "the way we agreed."
    ),
    target="toolshed/holds.py",
    functional_tests=_C2_FUNCTIONAL,
    regression_tests=_C2_REGRESSION,
    contract_tests=_C2_CONTRACT,
    support_tests=_C2_SUPPORT,
    gold={"raise": _gold2("raise"), "none": _gold2("none")},
)

# ----------------------------------------------------------------- prefix (16 turns)

_PREFIX = [
    Turn(
        "user",
        "I volunteer at a neighbourhood tool library: about two hundred tools in a shed, "
        "members borrow for a week, and there is a waiting list for the popular ones. The "
        "whole thing runs on a clipboard and a shared spreadsheet that is wrong by Friday. "
        "I want a small Python package, toolshed, with an in-memory ToolStore for the "
        "inventory and a HoldBook for the waiting list, driven by a script the Saturday "
        "volunteer runs at opening to print who is waiting for what. No database, no web "
        "app, no member logins. The script is launched by one alias on the shed laptop:\n\n"
        "```\nalias opening='cd ~/toolshed && python -m toolshed.opening --holds --overdue'"
        "\n```\n\nCould you draft a README scope section that heads off requests for "
        "barcodes, fines and an online catalogue? The volunteers rotate, so the code has "
        "to be readable by someone who sees it twice a year. Volume is maybe forty loans "
        "and ten holds on a busy Saturday, so nothing needs to be fast; the record has to "
        "be right when a member turns up asking whether the tile cutter is back.",
    ),
    Turn(
        "assistant",
        "A scope section plus a non-goals list covers the recurring requests:\n\n```\n## "
        "Scope\ntoolshed is an in-memory register for a single tool library. It keeps Tool "
        "records in a ToolStore and Hold records in a HoldBook, for one process, with no "
        "persistence and no concurrency guarantees. It exists to be driven by the opening "
        "script and by tests: it knows which tools exist, who has them and who is waiting. "
        "Nothing else.\n\n## Non-goals\n- barcodes or label printing\n- fines or payments\n"
        "- an online catalogue or reservations page\n- member accounts\n```\n\nAnd a short "
        "usage block so the API's shape is visible without reading the source:\n\n```python\n"
        "from toolshed.holds import HoldBook\nfrom toolshed.store import ToolStore\n\nstore = "
        'ToolStore()\ndrill = store.add_tool("cordless drill")\nholds = HoldBook()\nholds.'
        'place_hold(drill.tool_id, "kofi")\nprint(holds.waiting_for(drill.tool_id))\n```',
    ),
    Turn(
        "user",
        "Ids: tools are T1, T2, ... and holds are H1, H2, ... each from its own counter. A "
        "volunteer suggested using the tool's shelf code (like B3-07) as the id since that "
        "is what is painted on the shelf. But tools move shelves when we reorganise, and two "
        "identical drills share a shelf code. The opening sheet currently prints:\n\n```\n"
        "Opening, Sat 2026-09-19\nHOLDS\nH14  T27  tile cutter     mira     waiting\nH15  "
        "T27  tile cutter     kofi     waiting\nH16  T3   cordless drill  ada      waiting\n"
        "OVERDUE\nT27  tile cutter     out to: ben   since 2026-09-05\n```\n\nIs there a "
        "downside to keeping the counters and storing the shelf code as an ordinary field "
        "later? I don't want to repaint ids onto two hundred tools if we change our minds.",
    ),
    Turn(
        "assistant",
        "Keep the counters. An id must be unique and stable; shelf codes are neither, as "
        "you found with the two drills and the reorganisations. The shelf code is a "
        "location fact about a tool and belongs in a field, where it can change without "
        "anything else noticing. Only `add_tool` and `place_hold` mint ids, so a scheme "
        "change later is two one-line edits:\n\n```python\ndef _next_id(self) -> str:\n    "
        'self._counter += 1\n    return f"T{self._counter}"\n```\n\nThe opening sheet already '
        "prints the tool name next to the id, which gives volunteers the context they want. "
        "Never reuse a number after a tool is retired, because old sheets in the folder "
        "refer to it; if persistence arrives, persist both counters with the records so a "
        "restart never mints T1 twice.",
    ),
    Turn(
        "user",
        "The sheet needs a one-line renderer per hold, roughly `H14 T27 tile cutter mira "
        "waiting`, which means the renderer needs the tool name from the store as well as "
        "the hold. Function in the holds module taking both, or a method on Hold that is "
        "passed the store? Here is my test draft:\n\n```python\nfrom toolshed.model import "
        'Hold, Tool\n\n\ndef test_hold_line_waiting():\n    h = Hold(hold_id="H14", tool_id='
        '"T27", member="mira")\n    t = Tool(tool_id="T27", name="tile cutter")\n    assert '
        'hold_line(h, t) == "H14 T27 tile cutter mira waiting"\n\n\ndef test_hold_line_'
        'cancelled():\n    h = Hold(hold_id="H15", tool_id="T27", member="kofi", status='
        '"cancelled")\n    t = Tool(tool_id="T27", name="tile cutter")\n    assert hold_line('
        'h, t) == "H15 T27 tile cutter kofi cancelled"\n```\n\nI would rather Hold not know '
        "about ToolStore at all, but I want to hear the trade-off.",
    ),
    Turn(
        "assistant",
        "Free function taking both records, in the holds module, so neither record type "
        "knows about the other's store:\n\n```python\ndef hold_line(hold: Hold, tool: Tool) "
        '-> str:\n    return f"{hold.hold_id} {hold.tool_id} {tool.name} {hold.member} '
        '{hold.status}"\n```\n\nBoth drafts pass as written. The script does the join "'
        "(`store.find(hold.tool_id)`) because it is the only place that holds both objects; "
        "a method on Hold that takes a ToolStore would couple the model to the store and "
        "make the model tests need a store fixture for no gain. Column alignment stays in "
        "the script, as it does for the tools section. If a hold ever needs a placed-on "
        "date, that becomes a field on Hold and the line gains one token at the end.",
    ),
    Turn(
        "user",
        "A volunteer typed a hold id from last week's sheet on Saturday and got this:\n\n"
        '```\n>>> holds.find("H9").member\nTraceback (most recent call last):\n  File '
        "\"<stdin>\", line 1, in <module>\nAttributeError: 'NoneType' object has no "
        "attribute 'member'\n```\n\n`find` returning None is fine, that is the usual lookup "
        "shape. But both classes are about to grow methods that act on a record (lend a "
        "tool, return it, cancel a hold, fulfil a hold), and I want one written rule for "
        "what an action does with an unknown id rather than each patch choosing. The "
        "opening script's loop today is:\n\n```python\nfor tool_id in returned:\n    "
        "store.retire_tool(tool_id) if broken(tool_id) else None\nfor hold in "
        "holds.waiting_for(tool_id):\n    print(hold_line(hold, store.find(hold.tool_id)))\n"
        "```\n\nWhat are the options, and which fits a shed where ids are read off paper?",
    ),
    Turn(
        "assistant",
        "Two coherent options. (1) Actions raise KeyError on an unknown id, so a typo "
        "surfaces the moment it happens and the script wraps calls it wants to survive in "
        "try/except. (2) Actions return None and change nothing, matching `find`; gentler, "
        "but a forgotten check becomes a silent no-op and the sheet is wrong without anyone "
        "knowing. The existing `retire_tool` already raises because it indexes the dict. "
        "For an inventory where a missed retirement means lending a broken tool, loud is "
        "safer; the loop you pasted only needs:\n\n```python\ntry:\n    store.retire_tool("
        'tool_id)\nexcept KeyError:\n    print(f"no such tool {tool_id}")\n```\n\nWhichever '
        "you pick, write it down once and every new action method in both classes follows "
        "it; mixing the two styles in one package is the worst outcome.",
    ),
    Turn(
        "user",
        "Logging rule, and it is firm: the package never logs. No logging import anywhere, "
        "no warnings, no info lines, not even for the notable cases a request calls out "
        "(lending something flagged for repair, cancelling twice, that sort of thing). The "
        "opening script prints whatever needs saying; the store and the hold book stay "
        "silent so tests never depend on log capture.",
    ),
    Turn(
        "assistant",
        "Noted: ToolStore and HoldBook emit no log records at all, notable cases included, "
        "and the package has no logging import. The script owns all printing. A caplog "
        "check of `len(caplog.records) == 0` around any call should hold forever, and I "
        "will not add a module logger even as a placeholder; anything worth saying comes "
        "back as data for the script to print.",
    ),
    Turn(
        "user",
        "Missing-id rule: action methods raise KeyError on an unknown id, exactly like "
        "retire_tool does today, in both ToolStore and HoldBook. Lookups keep returning "
        "None. Every new action method follows that.",
    ),
    Turn(
        "assistant",
        "Understood: unknown id means KeyError from every action method in both classes, "
        "matching retire_tool, while `find` keeps returning None. Indexing the dict "
        "directly gives that for free, so new methods will index rather than `.get`, and the "
        "opening script keeps its try/except around each action call.",
    ),
    Turn(
        "user",
        "Later I want `count` on ToolStore to take an optional status so the sheet can say "
        "how many tools are out. Not now. The tests that exist today are only these:\n\n"
        "```python\nimport pytest\n\nfrom toolshed.holds import HoldBook\nfrom toolshed.store "
        "import ToolStore\n\n\ndef test_add_sequential_ids():\n    s = ToolStore()\n    "
        'assert s.add_tool("a").tool_id == "T1"\n    assert s.add_tool("b").tool_id == "T2"\n'
        "\n\ndef test_retire_unknown_raises():\n    with pytest.raises(KeyError):\n        "
        'ToolStore().retire_tool("T1")\n\n\ndef test_waiting_for_filters_by_tool():\n    b = '
        'HoldBook()\n    b.place_hold("T1", "mira")\n    b.place_hold("T2", "kofi")\n    '
        'assert [h.member for h in b.waiting_for("T1")] == ["mira"]\n```',
    ),
    Turn(
        "assistant",
        "Noted for later. An optional `status: str | None = None` keyword keeps the "
        "no-argument call working:\n\n```python\ndef count(self, status: str | None = None) "
        "-> int:\n    if status is None:\n        return len(self._tools)\n    return sum(1 "
        "for t in self._tools.values() if t.status == status)\n```\n\nYour three tests keep "
        "passing unchanged.",
    ),
    Turn(
        "user",
        "Let's get the first feature in: lending. Saturday is in four days and the "
        "clipboard is full. I will paste the current files with every request so you see "
        "the real state rather than my memory of it; keep new code in the same style as "
        "retire_tool so the diff is easy for the next volunteer to read on the shed laptop.",
    ),
    Turn(
        "assistant",
        "Ready. Send the request with the files and I will return the complete target "
        "module, keeping add_tool, find, count and retire_tool exactly as they are, with no "
        "logging import and your three existing tests still green without any edits on "
        "your side.",
    ),
]

_EVENT = (
    "Scoped exception to the missing-id rule: holds are typed from paper slips and the "
    "slips are often stale, so for HoldBook (toolshed/holds.py) new action methods return "
    "None on an unknown hold id and change nothing. ToolStore keeps raising KeyError as "
    "before; this applies to the hold book only."
)


def build() -> Session:
    return Session(
        id="S47",
        project="toolshed",
        target_family="missing_record",
        support_family="logging",
        lifecycle="scope",
        files=_FILES,
        prefix=_PREFIX,
        states=("raise", "none"),
        state_at=("raise", "none"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10),
        tags={"support_state": "silent"},
    )
