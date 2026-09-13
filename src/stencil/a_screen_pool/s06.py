# ruff: noqa: E501
"""S06: seed catalog — naming (target, replacement) x return_shape (support)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""seedbin package."""\n'

_MODEL = '''"""Seed packet records."""

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Packet:
    packet_id: str
    variety: str
    quantity: int
    year: int
    status: str = "in_stock"

    def with_quantity(self, quantity: int) -> "Packet":
        return replace(self, quantity=quantity)
'''

_BIN = '''"""In-memory seed catalog for the allotment society's seed library."""

from seedbin.model import Packet


class SeedBin:
    def __init__(self) -> None:
        self._packets: dict[str, Packet] = {}
        self._counter = 0

    def packet_add(self, variety: str, quantity: int, year: int) -> Packet:
        self._counter += 1
        packet = Packet(f"K{self._counter}", variety, quantity, year)
        self._packets[packet.packet_id] = packet
        return packet

    def find(self, packet_id: str) -> Packet | None:
        return self._packets.get(packet_id)

    def count(self) -> int:
        return len(self._packets)
'''

_FILES = {
    "seedbin/__init__.py": _INIT,
    "seedbin/model.py": _MODEL,
    "seedbin/bin.py": _BIN,
}

# ----------------------------------------------------------------- checkpoint 1: sow

_C1_HELPER = """from seedbin.bin import SeedBin
from seedbin.model import Packet


def _sow(bin_):
    fn = getattr(bin_, "packet_sow", None) or getattr(bin_, "sow_packet", None)
    assert fn is not None, "no sow method found"
    return fn
"""

_C1_FUNCTIONAL = {
    "test_sow_functional.py": _C1_HELPER
    + """

def test_sow_reduces_quantity():
    b = SeedBin()
    p = b.packet_add("Cherokee Purple tomato", 40, 2025)
    out = _sow(b)(p.packet_id, 15)
    assert out.quantity == 25 and out.status == "in_stock"
    assert b.find(p.packet_id).quantity == 25


def test_sow_to_zero_marks_empty_and_clamps():
    b = SeedBin()
    p = b.packet_add("Painted Mountain corn", 10, 2024)
    out = _sow(b)(p.packet_id, 12)
    assert out.quantity == 0 and out.status == "empty"
    assert out.variety == "Painted Mountain corn" and out.year == 2024


def test_sow_unknown_raises_keyerror():
    b = SeedBin()
    try:
        _sow(b)("K999", 1)
    except KeyError:
        return
    raise AssertionError("expected KeyError for an unknown packet")
"""
}

_C1_REGRESSION = {
    "test_sow_regression.py": """from seedbin.bin import SeedBin


def test_add_and_find_unchanged():
    b = SeedBin()
    p = b.packet_add("Blue Lake bean", 30, 2025)
    assert p.packet_id == "K1" and p.quantity == 30 and p.status == "in_stock"
    assert b.find("K1") is p
    assert b.find("nope") is None
    assert b.count() == 1
"""
}

_C1_CONTRACT = {
    "noun_verb": {
        "test_sow_naming.py": """from seedbin.bin import SeedBin


def test_sow_is_noun_verb():
    assert hasattr(SeedBin, "packet_sow")
    assert not hasattr(SeedBin, "sow_packet")
"""
    },
    "verb_noun": {
        "test_sow_naming.py": """from seedbin.bin import SeedBin


def test_sow_is_verb_noun():
    assert hasattr(SeedBin, "sow_packet")
    assert not hasattr(SeedBin, "packet_sow")
"""
    },
}

_C1_SUPPORT = {
    "test_sow_shape.py": _C1_HELPER
    + """

def test_sow_returns_packet_dataclass_not_dict():
    b = SeedBin()
    p = b.packet_add("x", 5, 2025)
    out = _sow(b)(p.packet_id, 2)
    assert isinstance(out, Packet)
    assert not isinstance(out, dict)
"""
}


def _gold1(name: str) -> str:
    body = (
        _BIN.rstrip("\n")
        + f"""

    def {name}(self, packet_id: str, count: int) -> Packet:
        packet = self._packets[packet_id]
        left = max(0, packet.quantity - count)
        status = "empty" if left == 0 else packet.status
        sown = replace(packet, quantity=left, status=status)
        self._packets[packet_id] = sown
        return sown
"""
    )
    return body.replace(
        "from seedbin.model import Packet\n",
        "from dataclasses import replace\n\nfrom seedbin.model import Packet\n",
        1,
    )


_REQ1 = Request(
    text=(
        "Add a public method on SeedBin that records sowing from a packet: it takes the "
        "packet id and the number of seeds sown, reduces the packet's quantity by that "
        'number (never below zero), sets the status to "empty" when the quantity reaches '
        "zero, stores the updated packet and returns it. An unknown id raises KeyError."
    ),
    target="seedbin/bin.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"noun_verb": _gold1("packet_sow"), "verb_noun": _gold1("sow_packet")},
)

# ----------------------------------------------------------------- checkpoint 2: retire

_C2_HELPER = """from seedbin.bin import SeedBin
from seedbin.model import Packet


def _retire(bin_):
    fn = getattr(bin_, "retire_packet", None) or getattr(bin_, "packet_retire", None)
    assert fn is not None, "no retire method found"
    return fn
"""

_C2_FUNCTIONAL = {
    "test_retire_functional.py": _C2_HELPER
    + """

def test_retire_sets_status_retired():
    b = SeedBin()
    p = b.packet_add("Cherokee Purple tomato", 40, 2021)
    out = _retire(b)(p.packet_id)
    assert out.status == "retired"
    assert b.find(p.packet_id).status == "retired"


def test_retire_keeps_quantity_variety_year():
    b = SeedBin()
    p = b.packet_add("Painted Mountain corn", 10, 2020)
    out = _retire(b)(p.packet_id)
    assert out.packet_id == p.packet_id
    assert out.quantity == 10 and out.variety == "Painted Mountain corn" and out.year == 2020


def test_retire_unknown_raises_keyerror():
    b = SeedBin()
    try:
        _retire(b)("K999")
    except KeyError:
        return
    raise AssertionError("expected KeyError for an unknown packet")
"""
}

_C2_REGRESSION = {
    "test_retire_regression.py": """from seedbin.bin import SeedBin


def _sow(bin_):
    return getattr(bin_, "packet_sow", None) or getattr(bin_, "sow_packet", None)


def test_add_find_sow_unchanged():
    b = SeedBin()
    p = b.packet_add("Blue Lake bean", 30, 2025)
    assert b.find("K1") is p and b.count() == 1
    out = _sow(b)(p.packet_id, 30)
    assert out.quantity == 0 and out.status == "empty"
"""
}

_C2_CONTRACT = {
    "noun_verb": {
        "test_retire_naming.py": """from seedbin.bin import SeedBin


def test_retire_is_noun_verb():
    assert hasattr(SeedBin, "packet_retire")
    assert not hasattr(SeedBin, "retire_packet")
"""
    },
    "verb_noun": {
        "test_retire_naming.py": """from seedbin.bin import SeedBin


def test_retire_is_verb_noun():
    assert hasattr(SeedBin, "retire_packet")
    assert not hasattr(SeedBin, "packet_retire")
"""
    },
}

_C2_SUPPORT = {
    "test_retire_shape.py": _C2_HELPER
    + """

def test_retire_returns_packet_dataclass_not_dict():
    b = SeedBin()
    p = b.packet_add("x", 5, 2019)
    out = _retire(b)(p.packet_id)
    assert isinstance(out, Packet)
    assert not isinstance(out, dict)
"""
}


def _gold2(name: str) -> str:
    # Built on the checkpoint-1 gold under the state then in force (noun_verb).
    return (
        _gold1("packet_sow").rstrip("\n")
        + f"""

    def {name}(self, packet_id: str) -> Packet:
        packet = self._packets[packet_id]
        retired = replace(packet, status="retired")
        self._packets[packet_id] = retired
        return retired
"""
    )


_REQ2 = Request(
    text=(
        "Add a public method on SeedBin that retires a packet by id (seed too old to "
        'trust): it sets the status to "retired", leaves the quantity as it is, stores the '
        "updated packet and returns it. An unknown id raises KeyError."
    ),
    target="seedbin/bin.py",
    functional_tests=_C2_FUNCTIONAL,
    regression_tests=_C2_REGRESSION,
    contract_tests=_C2_CONTRACT,
    support_tests=_C2_SUPPORT,
    gold={"noun_verb": _gold2("packet_retire"), "verb_noun": _gold2("retire_packet")},
)

# ----------------------------------------------------------------- prefix (16 turns)

_PREFIX = [
    Turn(
        "user",
        "I look after the seed library at our allotment society and I'm replacing the "
        "shoebox-and-notebook system with a tiny Python package: an in-memory SeedBin, a "
        "Packet record per envelope, and two scripts, one that prints what we have for the "
        "spring swap and one that lists packets older than three years so we can test "
        "germination. Roughly two hundred packets, mostly tomatoes, beans and squash. "
        "Persistence is a JSON dump after each Saturday session; no database, no website. "
        "The swap script is only:\n\n```\npython -m seedbin.stocklist --year 2026 > "
        "stock/spring-2026.txt\n```\n\nso the package just has to expose enough for that. "
        "Can you sketch what the README should say about scope? Someone on the committee "
        "has already asked whether it will 'track members' seed donations' and I want a "
        "written no before it turns into a membership system. Speed is irrelevant at two "
        "hundred packets; what matters is that the Saturday volunteers can read the code "
        "without surprises.",
    ),
    Turn(
        "assistant",
        "A short scope section plus explicit non-goals is what to give the committee:\n\n"
        "```\n## Scope\nseedbin is an in-memory catalog of seed packets for one seed "
        "library in a single process. It keeps Packet records in a SeedBin, has no "
        "persistence beyond the Saturday JSON dump and no concurrency guarantees, and is "
        "meant for the stocklist scripts, not as a service.\n\n## Non-goals\n- member "
        "records or donation credits\n- germination test results\n- planting calendars\n- "
        "photos or growing notes\n```\n\nThe non-goals list is what people actually read. "
        "A usage block sets the tone for the API:\n\n```python\nfrom seedbin.bin import "
        'SeedBin\n\nbin_ = SeedBin()\np = bin_.packet_add("Cherokee Purple tomato", 40, '
        "year=2025)\nprint(bin_.find(p.packet_id))\n```\n\nIf donation tracking ever "
        "happens it is a separate package that references packet ids; saying so now is "
        "cheaper than carving it out later. Add `Requires Python 3.11+` as well; the shed "
        "laptop is elderly and `str | None` will be the first thing to break.",
    ),
    Turn(
        "user",
        "Good. Ids are K1, K2, ... from a counter. A committee member wants the id to be "
        "the variety name plus year, like "
        "`cherokee-purple-2025`, so the envelope label is the id. I think that mixes two "
        "things: we often have two envelopes of the same variety and year from different "
        "donors. The Saturday dump I have in mind:\n\n```json\n{\n  "
        '"library": "hillside-allotments",\n  "dumped_at": "2026-09-12T13:00:00",\n  '
        '"packets": [\n    {"packet_id": "K1", "variety": "Cherokee Purple tomato", '
        '"quantity": 40, "year": 2025, "status": "in_stock"},\n    {"packet_id": "K2", '
        '"variety": "Painted Mountain corn", "quantity": 0, "year": 2024, "status": '
        '"empty"}\n  ]\n}\n```\n\nAm I right to push back, and what goes on the envelope '
        "label instead?",
    ),
    Turn(
        "assistant",
        "You are right. An id should never carry facts that can collide or change, and "
        "variety-plus-year does both: two donors, one variety, one year. Keep the counter "
        "as identity and print the label from the record, id first:\n\n```\nK14  Cherokee "
        "Purple tomato  2025  (40)\n```\n\nCounters stay short in the notebook and on the "
        "envelope, and only `packet_add` mints ids, so if persistence changes later there "
        "is one place to touch:\n\n```python\ndef _next_id(self) -> str:\n    "
        'self._counter += 1\n    return f"K{self._counter}"\n```\n\nIf the committee wants '
        "to find every envelope of a variety, that is a filter over the values, not a "
        "property of the id:\n\n```python\ndef by_variety(self, variety: str) -> "
        "list[Packet]:\n    return [p for p in self._packets.values() if p.variety == "
        "variety]\n```\n\nThe donor, if you want to keep it, is another field on Packet "
        "and another column on the label, never part of the id.",
    ),
    Turn(
        "user",
        "I want a helper that formats a packet for the label printer, like `K3 Cherokee "
        "Purple tomato 2025 (40)` or `K3 Cherokee Purple tomato 2025 (empty)`. Method on "
        "Packet or free function next to it? A method is discoverable, but then the record "
        "knows about presentation. Here is my test draft so you can see the shape I'm "
        "after:\n\n```python\nimport pytest\n\nfrom seedbin.model import Packet\n\n\n"
        '@pytest.fixture\ndef tomato():\n    return Packet(packet_id="K3", variety='
        '"Cherokee Purple tomato", quantity=40, year=2025)\n\n\ndef test_label_in_stock('
        'tomato):\n    assert label(tomato) == "K3 Cherokee Purple tomato 2025 (40)"\n\n\n'
        "def test_label_empty(tomato):\n    p = tomato.with_quantity(0)\n    assert "
        'label(p) == "K3 Cherokee Purple tomato 2025 (empty)"\n```\n\nThe label printer '
        "takes plain text over USB, one line per envelope, so whatever this returns is "
        "what ends up glued to the packet.",
    ),
    Turn(
        "assistant",
        "Put it next to the model as a plain function so the scripts and tests share it "
        "without Packet learning about presentation:\n\n```python\ndef label(packet: "
        'Packet) -> str:\n    qty = str(packet.quantity) if packet.quantity else "empty"\n'
        '    return f"{packet.packet_id} {packet.variety} {packet.year} ({qty})"\n```\n\n'
        "It reads only public fields, so it stays trivially testable, and if the label "
        "printer later wants a fixed width or a barcode that lives in the script. A "
        "`__str__` on Packet would tie the record to one rendering forever, and the JSON "
        "dump needs its own serializer anyway. Both of your tests pass against that as "
        "written; note the second one keys off quantity rather than status, which is the "
        "right choice for a label because the two can disagree for a moment while a "
        "session is being typed in. If the printer ever needs a fixed width, pad in the "
        'script with `f"{label(p):<48}"` rather than here.',
    ),
    Turn(
        "user",
        "Fair. Next: should `find` raise on a missing id or return None? Right now it "
        "returns None and the caller checks. I want one rule I can point the other "
        "volunteers at. This is what one of them hit last Saturday assuming `find` raises:"
        '\n\n```\n>>> bin_.find("K71").variety\nTraceback (most recent call last):\n  File '
        "\"<stdin>\", line 1, in <module>\nAttributeError: 'NoneType' object has no "
        "attribute 'variety'\n```\n\nThe usual None-propagation trap; she had typed K71 "
        "for K17 and spent a while convinced the dump had not loaded. The shed log from "
        "that session:\n\n```\n2026-09-05 10:31:02 INFO  seedbin: loaded dump "
        "2026-08-29.json (203 packets)\n2026-09-05 10:58:40 ERROR shell: AttributeError: "
        "'NoneType' object has no attribute 'variety'\n```",
    ),
    Turn(
        "assistant",
        "Returning None from `find` is the usual lookup contract: the name says 'try to "
        "find', and callers branch on the result. Methods that *act* on a packet (sowing, "
        "retiring, splitting) are different: acting on an id that does not exist is a "
        "caller bug, so raising KeyError there is the clearer signal and it surfaces in "
        "tests immediately. So the rule is: lookups return None, actions raise KeyError. "
        "Keep `find` as it is, and callers that need a hard failure can wrap it:\n\n"
        "```python\ndef require(bin_, packet_id):\n    packet = bin_.find(packet_id)\n    "
        "if packet is None:\n        raise KeyError(packet_id)\n    return packet\n```\n\n"
        "The traceback you pasted becomes a KeyError('K71') at the call site, which says "
        "the id was wrong rather than the dump; the log line showing 203 packets loaded "
        "half an hour earlier was the other clue.",
    ),
    Turn(
        "user",
        "Agreed, actions raise KeyError on unknown ids. Two conventions to fix now so the "
        "code stays uniform. First: public SeedBin methods always return Packet dataclass "
        "instances, never dicts or tuples, even for convenience. The notebook importer I "
        "wrote returned dicts and every caller grew a `.get('quantity')`.",
    ),
    Turn(
        "assistant",
        "Noted: every public SeedBin method returns Packet instances (or None from "
        "lookups), never dicts or tuples. Callers stay on one type, we can add fields to "
        "Packet without breaking them, and the label helper works on anything the bin "
        "hands back.",
    ),
    Turn(
        "user",
        "Second: method naming. Public bin methods are named noun_verb, like packet_add, "
        "because the volunteers think 'packet, then what happens to it'. Anything new "
        "follows that pattern.",
    ),
    Turn(
        "assistant",
        "Understood: noun_verb for public SeedBin methods, matching packet_add. I will "
        "name new methods that way; private helpers stay free-form since they are not part "
        "of the API. If a verb is ambiguous, for example whether taking seeds out is "
        "packet_sow or packet_draw, I will use the verb the request itself uses.",
    ),
    Turn(
        "user",
        "One more for later: I'd like `count` to take an optional status filter so the "
        "stocklist can print in-stock versus empty totals. Not now. For reference, the "
        "tests that exist today are only these:\n\n```python\nfrom seedbin.bin import "
        "SeedBin\n\n\ndef test_add_assigns_sequential_ids():\n    b = SeedBin()\n    assert "
        'b.packet_add("a", 1, 2025).packet_id == "K1"\n    assert b.packet_add("b", 1, '
        '2025).packet_id == "K2"\n\n\ndef test_find_missing_returns_none():\n    assert '
        'SeedBin().find("K1") is None\n```',
    ),
    Turn(
        "assistant",
        "Noted for later. An optional keyword `status: str | None = None` keeps the "
        "current no-argument call working:\n\n```python\ndef count(self, status: str | "
        "None = None) -> int:\n    if status is None:\n        return len(self._packets)\n"
        "    return sum(1 for p in self._packets.values() if p.status == status)\n```",
    ),
    Turn(
        "user",
        "Right. Let's get the first real feature in; sowing starts next weekend and I want "
        "the quantities to go down as people take seeds. I will paste the current files "
        "with each request so you always see the real state rather than my memory of it.",
    ),
    Turn(
        "assistant",
        "Ready when you are. Send the request and I will return the full bin module.",
    ),
]

_EVENT = (
    "Change of convention, effective now: new public SeedBin methods are named verb_noun "
    "(for example retire_packet style), not noun_verb; the committee wants the API to "
    "read as a list of actions. Existing method names stay as they are; only new methods "
    "follow the new pattern."
)


def build() -> Session:
    return Session(
        id="S06",
        project="seedbin",
        target_family="naming",
        support_family="return_shape",
        lifecycle="replacement",
        files=_FILES,
        prefix=_PREFIX,
        states=("noun_verb", "verb_noun"),
        state_at=("noun_verb", "verb_noun"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10),
    )
