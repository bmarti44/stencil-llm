# ruff: noqa: E501
"""S48: farm-share boxes — missing_record (target, reinstatement) x logging (support, warn)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""farmshare package."""\n'

_MODEL = '''"""Weekly farm-share box records."""

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Box:
    box_id: str
    member: str
    week: int
    contents: tuple[str, ...] = ()
    status: str = "packed"

    def with_status(self, status: str) -> "Box":
        return replace(self, status=status)
'''

_STORE = '''"""In-memory pickup-site box register."""

import logging
from dataclasses import replace

from farmshare.model import Box

log = logging.getLogger(__name__)


class BoxStore:
    def __init__(self) -> None:
        self._boxes: dict[str, Box] = {}
        self._counter = 0

    def pack_box(self, member: str, week: int) -> Box:
        self._counter += 1
        box = Box(box_id=f"B{self._counter}", member=member, week=week)
        self._boxes[box.box_id] = box
        return box

    def find(self, box_id: str) -> Box | None:
        return self._boxes.get(box_id)

    def count(self) -> int:
        return len(self._boxes)

    def add_item(self, box_id: str, item: str) -> Box:
        box = self._boxes[box_id]
        filled = replace(box, contents=box.contents + (item,))
        self._boxes[box_id] = filled
        return filled
'''

_FILES = {
    "farmshare/__init__.py": _INIT,
    "farmshare/model.py": _MODEL,
    "farmshare/store.py": _STORE,
}

# ----------------------------------------------------------------- checkpoint 1: collect

_C1_HELPER = """from farmshare.store import BoxStore


def _collect(store):
    fn = getattr(store, "collect_box", None)
    assert fn is not None, "no collect_box method found"
    return fn
"""

_C1_FUNCTIONAL = {
    "test_collect_functional.py": _C1_HELPER
    + """

def _seed_other(store):
    # A SECOND box, filled and collected, so neither its contents nor its
    # status is the dataclass default: an operation that wipes the store, or
    # resets an unrelated defaulted attribute, is then visible.
    other = store.pack_box("ayla", 36)
    store.add_item(other.box_id, "leeks")
    _collect(store)(other.box_id)
    return other


def _assert_other_intact(store, other):
    kept = store.find(other.box_id)
    assert kept is not None, "an unrelated box was dropped from the store"
    assert kept.box_id == other.box_id and kept.member == "ayla"
    assert kept.week == 36 and kept.contents == ("leeks",)
    assert kept.status == "collected"
    assert store.count() == 2


def test_collect_sets_status_collected():
    s = BoxStore()
    other = _seed_other(s)
    b = s.pack_box("hollis", 37)
    out = _collect(s)(b.box_id)
    assert out.status == "collected"
    assert s.find(b.box_id).status == "collected"
    _assert_other_intact(s, other)


def test_collect_keeps_member_week_and_contents():
    s = BoxStore()
    other = _seed_other(s)
    b = s.pack_box("ayla", 37)
    s.add_item(b.box_id, "chard")
    out = _collect(s)(b.box_id)
    assert out.box_id == b.box_id and out.member == "ayla" and out.week == 37
    assert out.contents == ("chard",)
    assert s.find(b.box_id).contents == ("chard",)
    _assert_other_intact(s, other)


def test_collect_twice_stays_collected():
    s = BoxStore()
    other = _seed_other(s)
    b = s.pack_box("hollis", 37)
    _collect(s)(b.box_id)
    out = _collect(s)(b.box_id)
    assert out.status == "collected" and s.find(b.box_id).status == "collected"
    _assert_other_intact(s, other)


def test_add_item_to_a_collected_box_keeps_status_and_siblings():
    s = BoxStore()
    other = _seed_other(s)
    b = s.pack_box("hollis", 37)
    s.add_item(b.box_id, "kale")
    _collect(s)(b.box_id)
    out = s.add_item(b.box_id, "beets")
    assert out.status == "collected"
    assert out.contents == ("kale", "beets")
    assert s.find(b.box_id).status == "collected"
    assert s.find(b.box_id).contents == ("kale", "beets")
    _assert_other_intact(s, other)
"""
}

_C1_REGRESSION = {
    "test_collect_regression.py": """import pytest

from farmshare.store import BoxStore


def test_pack_find_count_add_item_unchanged():
    s = BoxStore()
    b = s.pack_box("hollis", 37)
    assert b.box_id == "B1" and b.status == "packed" and b.contents == ()
    assert s.find("B1") is b and s.find("nope") is None
    assert s.count() == 1
    assert s.add_item("B1", "kale").contents == ("kale",)
    with pytest.raises(KeyError):
        s.add_item("B9", "kale")
    c = s.pack_box("ayla", 36)
    assert c.box_id == "B2" and c.status == "packed" and c.contents == ()
    assert s.find("B2") is c and s.count() == 2
    assert s.add_item("B2", "chard").contents == ("chard",)
    kept = s.find("B1")
    assert kept is not None, "filling one box dropped another from the store"
    assert kept.box_id == "B1" and kept.member == "hollis" and kept.week == 37
    assert kept.contents == ("kale",) and kept.status == "packed"
    assert s.count() == 2
"""
}

_C1_CONTRACT = {
    "raise": {
        "test_collect_missing.py": _C1_HELPER
        + """
import pytest


def test_collect_unknown_raises_keyerror():
    s = BoxStore()
    s.pack_box("hollis", 37)
    with pytest.raises(KeyError):
        _collect(s)("B404")
    assert s.count() == 1
"""
    },
    "none": {
        "test_collect_missing.py": _C1_HELPER
        + """

def test_collect_unknown_returns_none_and_changes_nothing():
    s = BoxStore()
    b = s.pack_box("hollis", 37)
    assert _collect(s)("B404") is None
    assert s.count() == 1 and s.find(b.box_id) == b
"""
    },
}

_C1_SUPPORT = {
    "test_collect_logging.py": _C1_HELPER
    + """
import logging


def test_first_collect_emits_no_log(caplog):
    s = BoxStore()
    b = s.pack_box("hollis", 37)
    with caplog.at_level(logging.DEBUG):
        _collect(s)(b.box_id)
    assert len(caplog.records) == 0


def test_second_collect_emits_exactly_one_warning(caplog):
    s = BoxStore()
    b = s.pack_box("hollis", 37)
    _collect(s)(b.box_id)
    with caplog.at_level(logging.DEBUG):
        _collect(s)(b.box_id)
    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == logging.WARNING
"""
}


def _lookup(state: str) -> str:
    if state == "none":
        return "        box = self._boxes.get(box_id)\n        if box is None:\n            return None\n"
    return "        box = self._boxes[box_id]\n"


def _gold1(state: str) -> str:
    return (
        _STORE.rstrip("\n")
        + f"""

    def collect_box(self, box_id: str) -> Box | None:
{_lookup(state)}        if box.status == "collected":
            log.warning("box %s for %s was already collected", box_id, box.member)
            return box
        collected = box.with_status("collected")
        self._boxes[box_id] = collected
        return collected
"""
    )


_REQ1 = Request(
    text=(
        "Add a public method collect_box(box_id) on BoxStore for the pickup desk: it sets "
        'the box\'s status to "collected", keeps member, week and contents, stores the '
        "updated box and returns it. A box that is already collected is the notable case "
        "(it stays collected and is returned); handle it the way we agreed."
    ),
    target="farmshare/store.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"raise": _gold1("raise"), "none": _gold1("none")},
)

# ----------------------------------------------------------------- checkpoint 2: hold

_C2_HELPER = """from farmshare.store import BoxStore


def _hold(store):
    fn = getattr(store, "hold_box", None)
    assert fn is not None, "no hold_box method found"
    return fn
"""

_C2_FUNCTIONAL = {
    "test_hold_functional.py": _C2_HELPER
    + """

def _seed_other(store):
    # A SECOND box, filled and collected, so neither its contents nor its
    # status is the dataclass default: an operation that wipes the store, or
    # resets an unrelated defaulted attribute, is then visible.
    other = store.pack_box("ayla", 36)
    store.add_item(other.box_id, "leeks")
    store.collect_box(other.box_id)
    return other


def _assert_other_intact(store, other):
    kept = store.find(other.box_id)
    assert kept is not None, "an unrelated box was dropped from the store"
    assert kept.box_id == other.box_id and kept.member == "ayla"
    assert kept.week == 36 and kept.contents == ("leeks",)
    assert kept.status == "collected"
    assert store.count() == 2


def test_hold_sets_status_held():
    s = BoxStore()
    other = _seed_other(s)
    b = s.pack_box("hollis", 38)
    out = _hold(s)(b.box_id)
    assert out.status == "held"
    assert s.find(b.box_id).status == "held"
    _assert_other_intact(s, other)


def test_hold_keeps_member_week_and_contents():
    s = BoxStore()
    other = _seed_other(s)
    b = s.pack_box("ayla", 38)
    s.add_item(b.box_id, "squash")
    out = _hold(s)(b.box_id)
    assert out.box_id == b.box_id and out.member == "ayla" and out.week == 38
    assert out.contents == ("squash",)
    assert s.find(b.box_id).contents == ("squash",)
    _assert_other_intact(s, other)


def test_hold_collected_box_still_holds():
    s = BoxStore()
    other = _seed_other(s)
    b = s.pack_box("hollis", 38)
    s.collect_box(b.box_id)
    out = _hold(s)(b.box_id)
    assert out.status == "held" and s.find(b.box_id).status == "held"
    _assert_other_intact(s, other)


def test_add_item_to_a_held_box_keeps_status_and_siblings():
    s = BoxStore()
    other = _seed_other(s)
    b = s.pack_box("hollis", 38)
    s.add_item(b.box_id, "kale")
    _hold(s)(b.box_id)
    out = s.add_item(b.box_id, "beets")
    assert out.status == "held"
    assert out.contents == ("kale", "beets")
    assert s.find(b.box_id).status == "held"
    assert s.find(b.box_id).contents == ("kale", "beets")
    _assert_other_intact(s, other)
"""
}

_C2_REGRESSION = {
    "test_hold_regression.py": """import pytest

from farmshare.store import BoxStore


def test_pack_find_add_item_collect_unchanged():
    s = BoxStore()
    b = s.pack_box("hollis", 38)
    assert s.find("B1") is b and s.count() == 1
    assert s.add_item("B1", "kale").contents == ("kale",)
    with pytest.raises(KeyError):
        s.add_item("B9", "kale")
    assert s.collect_box("B1").status == "collected"
    c = s.pack_box("ayla", 36)
    assert c.box_id == "B2" and c.status == "packed" and s.count() == 2
    assert s.add_item("B1", "beets").contents == ("kale", "beets")
    assert s.find("B1").status == "collected"
    assert s.collect_box("B2").status == "collected"
    kept = s.find("B1")
    assert kept is not None, "collecting one box dropped another from the store"
    assert kept.box_id == "B1" and kept.member == "hollis" and kept.week == 38
    assert kept.contents == ("kale", "beets") and kept.status == "collected"
    assert s.count() == 2
"""
}

_C2_CONTRACT = {
    "raise": {
        "test_hold_missing.py": _C2_HELPER
        + """
import pytest


def test_hold_unknown_raises_keyerror():
    s = BoxStore()
    s.pack_box("hollis", 38)
    with pytest.raises(KeyError):
        _hold(s)("B404")
    assert s.count() == 1
"""
    },
    "none": {
        "test_hold_missing.py": _C2_HELPER
        + """

def test_hold_unknown_returns_none_and_changes_nothing():
    s = BoxStore()
    b = s.pack_box("hollis", 38)
    assert _hold(s)("B404") is None
    assert s.count() == 1 and s.find(b.box_id) == b
"""
    },
}

_C2_SUPPORT = {
    "test_hold_logging.py": _C2_HELPER
    + """
import logging


def test_hold_packed_box_emits_no_log(caplog):
    s = BoxStore()
    b = s.pack_box("hollis", 38)
    with caplog.at_level(logging.DEBUG):
        _hold(s)(b.box_id)
    assert len(caplog.records) == 0


def test_hold_collected_box_emits_exactly_one_warning(caplog):
    s = BoxStore()
    b = s.pack_box("hollis", 38)
    s.collect_box(b.box_id)
    with caplog.at_level(logging.DEBUG):
        _hold(s)(b.box_id)
    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == logging.WARNING
"""
}


def _gold2(state: str) -> str:
    # Built on the checkpoint-1 gold under the state then in force (none).
    return (
        _gold1("none").rstrip("\n")
        + f"""

    def hold_box(self, box_id: str) -> Box | None:
{_lookup(state)}        if box.status == "collected":
            log.warning("box %s for %s was already collected; holding it anyway", box_id, box.member)
        held = box.with_status("held")
        self._boxes[box_id] = held
        return held
"""
    )


_REQ2 = Request(
    text=(
        "Add a public method hold_box(box_id) on BoxStore for members who skip a week: it "
        'sets the box\'s status to "held", keeps member, week and contents, stores the '
        "updated box and returns it. Holding a box that was already collected is the "
        "notable case (the desk mis-keyed it; hold it anyway); handle it the way we agreed."
    ),
    target="farmshare/store.py",
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
        "I coordinate the pickup site for a small farm share: sixty members, one box each "
        "per week from June to November, collected from a church hall on Wednesday "
        "evenings. Today it is a printed list and a highlighter, and every week two boxes "
        "go home with the wrong person. I want a tiny Python package, farmshare, with an "
        "in-memory BoxStore of Box records and a script the desk volunteer runs at the "
        "start of the evening to print the pickup list. No database, no member portal, no "
        "app. The script is launched from one alias on the desk laptop:\n\n```\nalias "
        "pickup='cd ~/farmshare && python -m farmshare.desk --week $(date +%V)'\n```\n\n"
        "Can you draft a README scope section so nobody expects payments, delivery routing "
        "or an email reminder system? The volunteers change every few weeks, so the code "
        "has to be obvious to someone seeing it for the first time. Volume is sixty boxes "
        "a week, so nothing needs to be fast; the record for a box has to be right when a "
        "member turns up saying they were told theirs would be held.",
    ),
    Turn(
        "assistant",
        "A scope section plus a non-goals list settles the recurring requests:\n\n```\n## "
        "Scope\nfarmshare is an in-memory register of weekly boxes at one pickup site. It "
        "keeps Box records (member, week, contents, status) in a BoxStore for a single "
        "process, has no persistence and no concurrency guarantees, and exists to be driven "
        "by the desk script and by tests. It knows which boxes were packed, what is in "
        "them and whether they were collected; nothing else.\n\n## Non-goals\n- payments "
        "or membership billing\n- delivery routing\n- email or text reminders\n- a member "
        "portal\n```\n\nA short usage block under it makes the API's shape visible without "
        "reading the source:\n\n```python\nfrom farmshare.store import BoxStore\n\nstore = "
        'BoxStore()\nbox = store.pack_box("hollis", week=37)\nstore.add_item(box.box_id, '
        '"chard")\nprint(store.find(box.box_id))\n```',
    ),
    Turn(
        "user",
        "Box ids are B1, B2, ... from a counter. The farmer would like the id to be the "
        "member name plus the week, like hollis-37, because that is what she writes on the "
        "crate. I see the appeal, but two members share a surname, and a member who splits "
        "a share gets two boxes some weeks. The desk list currently prints:\n\n```\nPickup, "
        "week 37, Wed 2026-09-16\nB211  hollis     chard, kale, squash        packed\nB212  "
        "ayla       chard, kale, squash, eggs  collected\nB213  hollis     chard, kale       "
        "         held\n```\n\nIs there a downside to keeping the counter and printing the "
        "member next to it, and storing the crate label as a plain field if she insists? I "
        "do not want to repaint ids on two hundred crates if we change our minds; the crate "
        "label and the id can simply be two different things.",
    ),
    Turn(
        "assistant",
        "Keep the counter. A key must be unique and stable; name-plus-week is neither, as "
        "the shared surname and the split shares show. The crate label is a fact about the "
        "box and belongs in a field, where the farmer can write whatever she likes without "
        "the store caring. Only `pack_box` mints ids, so a scheme change later is a "
        "one-method edit:\n\n```python\ndef _next_id(self) -> str:\n    self._counter += 1\n"
        '    return f"B{self._counter}"\n```\n\nThe desk list already prints the member next '
        "to the id, which gives volunteers the context they want. Never reuse a number "
        "after a week ends, since the paper lists in the folder refer to it; if persistence "
        "ever arrives, persist the counter with the boxes so a restart does not mint B1 "
        "again and confuse anyone holding last week's printed list.",
    ),
    Turn(
        "user",
        "The list needs a one-line renderer per box, roughly `B211 hollis chard, kale, "
        "squash packed`. Method on Box or a function in the store module? I lean function "
        "because Box is a record and should not know how it is printed, but a method is "
        "easier for a volunteer to discover. Test draft:\n\n```python\nfrom farmshare.model "
        'import Box\n\n\ndef test_line_packed():\n    b = Box(box_id="B211", member="hollis", '
        'week=37, contents=("chard", "kale", "squash"))\n    assert line(b) == "B211 hollis '
        'chard, kale, squash packed"\n\n\ndef test_line_empty_box():\n    b = Box(box_id='
        '"B214", member="ren", week=37)\n    assert line(b) == "B214 ren - packed"\n```\n\n'
        "Column padding can stay in the script; I only need the raw line here, and the "
        "farmer reads it on a phone anyway, usually while loading the van before dawn.",
    ),
    Turn(
        "assistant",
        "Free function next to the model, so the script and the tests share it and Box "
        'stays a plain record:\n\n```python\ndef line(box: Box) -> str:\n    what = ", '
        '".join(box.contents) if box.contents else "-"\n    return f"{box.box_id} '
        '{box.member} {what} {box.status}"\n```\n\nBoth drafts pass as written. Padding stays '
        "in the desk script, and a `__str__` on Box would tie the record to one rendering, "
        "which you would regret the first time the farmer wants the week shown too. Add a "
        "third test for a held box once that status exists, so the list never prints a "
        "stale status, and keep the empty-box dash: the farmer reads that as 'nothing "
        "packed yet' rather than as a bug.",
    ),
    Turn(
        "user",
        "A volunteer typed a box id from last week's list on Wednesday and got this:\n\n"
        '```\n>>> store.find("B198").contents\nTraceback (most recent call last):\n  File '
        "\"<stdin>\", line 1, in <module>\nAttributeError: 'NoneType' object has no "
        "attribute 'contents'\n```\n\n`find` returning None is fine, that is the usual "
        "lookup shape. But the store is about to grow methods that act on a box (collect, "
        "hold, swap an item) and I want one written rule for what an action does with an "
        "unknown id rather than each patch deciding. The desk script's loop is currently:"
        "\n\n```python\nfor box_id, item in additions:\n    store.add_item(box_id, item)\n"
        "for box in for_week(store, week):\n    print(line(box))\n```\n\nWhat are the "
        "options, and which fits a desk where ids are read off a paper list by torchlight?",
    ),
    Turn(
        "assistant",
        "Two coherent options. (1) Actions raise KeyError on an unknown id, so a typo "
        "surfaces immediately and the script wraps calls it wants to survive in try/except. "
        "(2) Actions return None and change nothing, matching `find`; gentler, but a "
        "forgotten check becomes a silent no-op and a box goes home wrong without anyone "
        "knowing. The existing `add_item` already raises because it indexes the dict. For "
        "a desk where a missed action means a wrong box, loud is safer; the loop only "
        "needs:\n\n```python\ntry:\n    store.add_item(box_id, item)\nexcept KeyError:\n    "
        'print(f"no such box {box_id}")\n```\n\nWhichever you pick, write it down once and '
        "every new action method follows it; mixing the two styles in one store is the "
        "worst outcome, because then nobody can predict what a call does. Once written "
        "down, I will follow it for every action method you ask for.",
    ),
    Turn(
        "user",
        "Logging rule, since the desk log is what the farmer reads on Thursday: when a "
        "store method hits the notable case a request calls out (collecting twice, holding "
        "a collected box, that kind of thing), it emits exactly one logging.warning through "
        "the module logger; the ordinary path writes no log records at all.",
    ),
    Turn(
        "assistant",
        "Noted: one `log.warning` per notable case on the module logger already in "
        "store.py, and nothing on the ordinary path; no info or debug lines, never two "
        "warnings for one call. Tests can pin it with caplog: `len(caplog.records) == 1` "
        "after the notable call and `== 0` after a normal one, and I will include both "
        "checks whenever I add a notable case, so the desk log stays readable on Thursday.",
    ),
    Turn(
        "user",
        "Missing-id rule: action methods raise KeyError on an unknown id, exactly like "
        "add_item does today. Lookups keep returning None. Every new action method follows "
        "that, and the desk script wraps the calls it wants to survive in try/except so "
        "one bad id does not stop the evening or send anyone home without a box.",
    ),
    Turn(
        "assistant",
        "Understood: unknown id means KeyError from every action method, matching add_item, "
        "while `find` keeps returning None. Indexing `self._boxes[box_id]` gives that for "
        "free, so new methods will index rather than `.get`, and the desk script keeps its "
        "try/except around each action call.",
    ),
    Turn(
        "user",
        "Change of plan after last Wednesday: the KeyError style crashed the desk script "
        "halfway through the list and forty people waited while we restarted it. From now "
        "on, new action methods return None on an unknown id and change nothing. Existing "
        "methods (add_item) keep their current behaviour; only new methods follow the new "
        "rule.",
    ),
    Turn(
        "assistant",
        "Understood, updated rule: new action methods return None on an unknown id and "
        "leave the store untouched; add_item stays as it is, since existing callers rely on it. New methods will use "
        "`self._boxes.get` with an early return rather than indexing, and the desk script "
        "checks the result of every action instead of catching KeyError:\n\n"
        '```python\nif store.collect_box(box_id) is None:\n    print(f"no such box '
        '{box_id}")\n```',
    ),
    Turn(
        "user",
        "For reference these are the only tests that exist today:\n\n```python\nimport "
        "pytest\n\nfrom farmshare.store import BoxStore\n\n\ndef test_pack_sequential_ids():\n"
        '    s = BoxStore()\n    assert s.pack_box("hollis", 37).box_id == "B1"\n    assert '
        's.pack_box("ayla", 37).box_id == "B2"\n\n\ndef test_add_item_unknown_raises():\n    '
        'with pytest.raises(KeyError):\n        BoxStore().add_item("B1", "kale")\n\n\ndef '
        'test_count_after_two_packs():\n    s = BoxStore()\n    s.pack_box("hollis", 37)\n'
        '    s.pack_box("ayla", 37)\n    assert s.count() == 2\n```\n\nI will paste the '
        "current files with each request so you see the real state rather than my memory "
        "of it.",
    ),
    Turn(
        "assistant",
        "Good. Send the first request with the files and I will return the complete store "
        "module, keeping pack_box, find, count and add_item exactly as they are, with the "
        "module logger and the imports untouched so your three existing tests keep passing "
        "without any edits on your side; new code will follow the style of add_item so the diff reads cleanly.",
    ),
]

_EVENT = (
    "Reverting last week's change: with the None style a mis-keyed id silently skipped "
    "two holds and both boxes went home with the wrong people. From now on, new action "
    "methods go back to raising KeyError on an unknown id, like add_item. Methods already "
    "written keep whatever they do now."
)


def build() -> Session:
    return Session(
        id="S48",
        project="farmshare",
        target_family="missing_record",
        support_family="logging",
        lifecycle="reinstatement",
        files=_FILES,
        prefix=_PREFIX,
        states=("raise", "none"),
        state_at=("none", "raise"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10, 12),
        tags={"support_state": "warn"},
    )
