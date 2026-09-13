# ruff: noqa: E501
"""S29: fleet fuel logs — validation (target, stable) x logging=warn (support)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""fuellog package."""\n'

_MODEL = '''"""Fuel log records."""

from dataclasses import dataclass


@dataclass(frozen=True)
class FuelEntry:
    entry_id: str
    plate: str
    litres: float
    odometer_km: int
    price_cents: int = 0
'''


def _journal(
    store_extra: str = "", api_extra: str = "", extra_imports: str = ""
) -> str:
    return f'''"""Fuel journal: store and public operations."""

{extra_imports}from fuellog.model import FuelEntry


class FuelLog:
    def __init__(self) -> None:
        self._entries: dict[str, FuelEntry] = {{}}
        self._counter = 0

    def add(self, plate: str, litres: float, odometer_km: int) -> FuelEntry:
        self._counter += 1
        e = FuelEntry(f"F{{self._counter}}", plate, litres, odometer_km)
        self._entries[e.entry_id] = e
        return e

    def get(self, entry_id: str) -> FuelEntry | None:
        return self._entries.get(entry_id)

    def litres_for(self, plate: str) -> float:
        return sum(e.litres for e in self._entries.values() if e.plate == plate)
{store_extra}

def record_fill(fuel_log: FuelLog, plate: str, litres: float, odometer_km: int) -> FuelEntry:
    if litres <= 0:
        raise ValueError("litres must be positive")
    if odometer_km < 0:
        raise ValueError("odometer must not be negative")
    return fuel_log.add(plate, litres, odometer_km)
{api_extra}'''


_FILES = {
    "fuellog/__init__.py": _INIT,
    "fuellog/model.py": _MODEL,
    "fuellog/journal.py": _journal(),
}

_IMPORTS = "import logging\nfrom dataclasses import replace\n\n"
_LOGGER = "\nlogger = logging.getLogger(__name__)\n"

# ----------------------------------------------------------------- checkpoint 1: correct_odometer

_V_ODO_STORE = '        if odometer_km < 0:\n            raise ValueError("odometer must not be negative")\n'
_V_ODO_API = '    if odometer_km < 0:\n        raise ValueError("odometer must not be negative")\n'


def _store_odo(validate: bool) -> str:
    return (
        "\n    def put_odometer(self, entry_id: str, odometer_km: int) -> FuelEntry:\n"
        + (_V_ODO_STORE if validate else "")
        + """        old = self._entries[entry_id]
        if abs(odometer_km - old.odometer_km) > 1000:
            logger.warning("odometer correction on %s moves reading by more than 1000 km", entry_id)
        updated = replace(old, odometer_km=odometer_km)
        self._entries[entry_id] = updated
        return updated
"""
    )


def _api_odo(validate: bool) -> str:
    return (
        "\n\ndef correct_odometer(fuel_log: FuelLog, entry_id: str, odometer_km: int) -> FuelEntry:\n"
        + (_V_ODO_API if validate else "")
        + "    return fuel_log.put_odometer(entry_id, odometer_km)\n"
    )


def _gold1(state: str) -> str:
    api = state == "api"
    return _journal(_store_odo(not api), _api_odo(api), _IMPORTS).replace(
        "from fuellog.model import FuelEntry\n",
        "from fuellog.model import FuelEntry\n" + _LOGGER,
        1,
    )


_C1_SETUP = """import pytest

from fuellog.journal import FuelLog, correct_odometer, record_fill
from fuellog.model import FuelEntry


def _log():
    fl = FuelLog()
    record_fill(fl, "KX61 VAN", 42.5, 118400)
    record_fill(fl, "KX61 VAN", 38.0, 118910)
    return fl
"""

_C1_FUNCTIONAL = {
    "test_odometer_functional.py": _C1_SETUP
    + """

def test_correct_odometer_updates_and_returns_entry():
    fl = _log()
    out = correct_odometer(fl, "F2", 118950)
    assert isinstance(out, FuelEntry)
    assert out.odometer_km == 118950 and out.litres == 38.0 and out.plate == "KX61 VAN"
    assert fl.get("F2").odometer_km == 118950


def test_large_correction_still_applies():
    fl = _log()
    out = correct_odometer(fl, "F1", 128400)
    assert out.odometer_km == 128400
    assert fl.get("F1").odometer_km == 128400


def test_correct_odometer_rejects_negative():
    fl = _log()
    with pytest.raises(ValueError):
        correct_odometer(fl, "F1", -1)
    assert fl.get("F1").odometer_km == 118400


def test_correct_odometer_unknown_id_raises_keyerror():
    fl = _log()
    with pytest.raises(KeyError):
        correct_odometer(fl, "F9", 100)
"""
}

_C1_REGRESSION = {
    "test_odometer_regression.py": """import pytest

from fuellog.journal import FuelLog, record_fill


def test_record_get_litres_unchanged():
    fl = FuelLog()
    e = record_fill(fl, "KX61 VAN", 42.5, 118400)
    assert e.entry_id == "F1" and fl.get("F1") is e and e.price_cents == 0
    assert fl.get("F9") is None
    record_fill(fl, "KX61 VAN", 38.0, 118910)
    record_fill(fl, "LD19 VAN", 50.0, 20100)
    assert fl.litres_for("KX61 VAN") == 80.5


def test_record_fill_still_validates_in_public_function():
    fl = FuelLog()
    with pytest.raises(ValueError):
        record_fill(fl, "KX61 VAN", 0, 118400)
    with pytest.raises(ValueError):
        record_fill(fl, "KX61 VAN", 40.0, -5)
    assert fl.add("KX61 VAN", 0, -5).litres == 0
"""
}

_C1_CONTRACT = {
    "api": {
        "test_odometer_validation.py": _C1_SETUP
        + """

def test_public_correct_odometer_raises_on_negative():
    fl = _log()
    with pytest.raises(ValueError):
        correct_odometer(fl, "F1", -20)


def test_store_put_odometer_trusts_its_argument():
    fl = _log()
    out = fl.put_odometer("F1", -20)
    assert out.odometer_km == -20
    assert fl.get("F1") is out
"""
    },
    "storage": {
        "test_odometer_validation.py": _C1_SETUP
        + """

def test_store_put_odometer_raises_on_negative():
    fl = _log()
    with pytest.raises(ValueError):
        fl.put_odometer("F1", -20)
    assert fl.get("F1").odometer_km == 118400


def test_public_correct_odometer_delegates_without_precheck(monkeypatch):
    fl = _log()
    calls = []

    def spy(self, *args, **kwargs):
        calls.append(args + tuple(kwargs.values()))
        return self._entries["F1"]

    monkeypatch.setattr(FuelLog, "put_odometer", spy)
    correct_odometer(fl, "F1", -20)
    assert len(calls) == 1 and -20 in calls[0]
"""
    },
}

_C1_SUPPORT = {
    "test_odometer_logging.py": """import logging

from fuellog.journal import FuelLog, correct_odometer, record_fill


def _warnings(caplog):
    return [r for r in caplog.records if r.levelno == logging.WARNING]


def test_large_correction_emits_exactly_one_warning(caplog):
    fl = FuelLog()
    record_fill(fl, "KX61 VAN", 42.5, 118400)
    with caplog.at_level(logging.DEBUG):
        correct_odometer(fl, "F1", 121000)
    assert len(_warnings(caplog)) == 1


def test_small_correction_emits_no_warning(caplog):
    fl = FuelLog()
    record_fill(fl, "KX61 VAN", 42.5, 118400)
    with caplog.at_level(logging.DEBUG):
        correct_odometer(fl, "F1", 118450)
        correct_odometer(fl, "F1", 119400)
    assert _warnings(caplog) == []
"""
}

_REQ1 = Request(
    text=(
        "Add `correct_odometer(fuel_log, entry_id, odometer_km)` to fuellog/journal.py: it "
        "replaces the odometer reading of an existing entry and returns the updated "
        "FuelEntry, via a new store method `FuelLog.put_odometer(entry_id, odometer_km)` "
        "that swaps in the updated record. A negative reading is invalid and is rejected "
        "with ValueError; an unknown entry id raises KeyError. A correction that moves "
        "the reading by more than 1,000 km from the stored value is the notable case; it "
        "still applies."
    ),
    target="fuellog/journal.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"api": _gold1("api"), "storage": _gold1("storage")},
)

# ----------------------------------------------------------------- checkpoint 2: set_price

_V_PRICE_STORE = '        if price_cents <= 0:\n            raise ValueError("price must be positive")\n'
_V_PRICE_API = (
    '    if price_cents <= 0:\n        raise ValueError("price must be positive")\n'
)


def _store_price(validate: bool) -> str:
    return (
        "\n    def put_price(self, entry_id: str, price_cents: int) -> FuelEntry:\n"
        + (_V_PRICE_STORE if validate else "")
        + """        if price_cents > 300:
            logger.warning("price on %s is above 300 cents per litre", entry_id)
        updated = replace(self._entries[entry_id], price_cents=price_cents)
        self._entries[entry_id] = updated
        return updated
"""
    )


def _api_price(validate: bool) -> str:
    return (
        "\n\ndef set_price(fuel_log: FuelLog, entry_id: str, price_cents: int) -> FuelEntry:\n"
        + (_V_PRICE_API if validate else "")
        + "    return fuel_log.put_price(entry_id, price_cents)\n"
    )


def _gold2(state: str) -> str:
    # Built on the checkpoint-1 gold under the state then in force (api).
    api = state == "api"
    return _journal(
        _store_odo(False) + _store_price(not api),
        _api_odo(True) + _api_price(api),
        _IMPORTS,
    ).replace(
        "from fuellog.model import FuelEntry\n",
        "from fuellog.model import FuelEntry\n" + _LOGGER,
        1,
    )


_C2_SETUP = """import pytest

from fuellog.journal import FuelLog, correct_odometer, record_fill, set_price
from fuellog.model import FuelEntry


def _log():
    fl = FuelLog()
    record_fill(fl, "KX61 VAN", 42.5, 118400)
    correct_odometer(fl, "F1", 118420)
    record_fill(fl, "LD19 VAN", 50.0, 20100)
    return fl
"""

_C2_FUNCTIONAL = {
    "test_price_functional.py": _C2_SETUP
    + """

def test_set_price_updates_and_returns_entry():
    fl = _log()
    out = set_price(fl, "F1", 179)
    assert isinstance(out, FuelEntry)
    assert out.price_cents == 179 and out.odometer_km == 118420 and out.litres == 42.5
    assert fl.get("F1").price_cents == 179


def test_high_price_still_applies():
    fl = _log()
    out = set_price(fl, "F2", 345)
    assert out.price_cents == 345 and fl.get("F2").price_cents == 345


def test_set_price_rejects_nonpositive():
    fl = _log()
    with pytest.raises(ValueError):
        set_price(fl, "F1", 0)
    assert fl.get("F1").price_cents == 0


def test_set_price_unknown_id_raises_keyerror():
    fl = _log()
    with pytest.raises(KeyError):
        set_price(fl, "F9", 179)
"""
}

_C2_REGRESSION = {
    "test_price_regression.py": """import pytest

from fuellog.journal import FuelLog, correct_odometer, record_fill


def test_record_get_litres_correct_unchanged():
    fl = FuelLog()
    e = record_fill(fl, "KX61 VAN", 42.5, 118400)
    assert fl.get("F1") is e and fl.litres_for("KX61 VAN") == 42.5
    assert correct_odometer(fl, "F1", 118420).odometer_km == 118420
    with pytest.raises(ValueError):
        correct_odometer(fl, "F1", -1)
    with pytest.raises(ValueError):
        record_fill(fl, "KX61 VAN", 0, 1)
"""
}

_C2_CONTRACT = {
    "api": {
        "test_price_validation.py": _C2_SETUP
        + """

def test_public_set_price_raises_on_nonpositive():
    fl = _log()
    with pytest.raises(ValueError):
        set_price(fl, "F1", -3)


def test_store_put_price_trusts_its_argument():
    fl = _log()
    out = fl.put_price("F1", -3)
    assert out.price_cents == -3
    assert fl.get("F1") is out
"""
    },
    "storage": {
        "test_price_validation.py": _C2_SETUP
        + """

def test_store_put_price_raises_on_nonpositive():
    fl = _log()
    with pytest.raises(ValueError):
        fl.put_price("F1", -3)
    assert fl.get("F1").price_cents == 0


def test_public_set_price_delegates_without_precheck(monkeypatch):
    fl = _log()
    calls = []

    def spy(self, *args, **kwargs):
        calls.append(args + tuple(kwargs.values()))
        return self._entries["F1"]

    monkeypatch.setattr(FuelLog, "put_price", spy)
    set_price(fl, "F1", -3)
    assert len(calls) == 1 and -3 in calls[0]
"""
    },
}

_C2_SUPPORT = {
    "test_price_logging.py": """import logging

from fuellog.journal import FuelLog, record_fill, set_price


def _warnings(caplog):
    return [r for r in caplog.records if r.levelno == logging.WARNING]


def test_high_price_emits_exactly_one_warning(caplog):
    fl = FuelLog()
    record_fill(fl, "KX61 VAN", 42.5, 118400)
    with caplog.at_level(logging.DEBUG):
        set_price(fl, "F1", 301)
    assert len(_warnings(caplog)) == 1


def test_ordinary_price_emits_no_warning(caplog):
    fl = FuelLog()
    record_fill(fl, "KX61 VAN", 42.5, 118400)
    with caplog.at_level(logging.DEBUG):
        set_price(fl, "F1", 179)
        set_price(fl, "F1", 300)
    assert _warnings(caplog) == []
"""
}

_REQ2 = Request(
    text=(
        "Add `set_price(fuel_log, entry_id, price_cents)` to fuellog/journal.py: it records "
        "the pump price per litre, in cents, on an existing entry and returns the updated "
        "FuelEntry, via a new store method `FuelLog.put_price(entry_id, price_cents)` "
        "that swaps in the updated record. A price that is not positive is invalid and is "
        "rejected with ValueError; an unknown entry id raises KeyError. A price above 300 "
        "cents per litre is the notable case; it still applies."
    ),
    target="fuellog/journal.py",
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
        "I look after six delivery vans for a bakery and the fuel receipts live in a "
        "glovebox until someone types them into a spreadsheet at month end, usually me. "
        "I want a small Python package, `fuellog`, that keeps fuel entries in memory for "
        "one month and drives two scripts: one that takes entries from a text file the "
        "drivers fill in on the depot laptop, and one that prints litres per van so I can "
        "spot the one that is drinking. No database, no app on the drivers' phones, no "
        "telematics integration, which the leasing company keeps pitching. The drivers' "
        "file is one line per fill:\n\n```\nKX61 VAN,42.5,118400\nKX61 VAN,38.0,118910\n"
        "LD19 VAN,50.0,20100\n```\n\nplate, litres, odometer in km. Can you draft the README "
        "scope section so the owner understands this is a bookkeeping helper and not a "
        "tracking system? He has asked twice whether it will show where the vans are.",
    ),
    Turn(
        "assistant",
        "Here is a scope section that draws that line:\n\n```\n## Scope\nfuellog keeps "
        "one month of fuel entries in memory as FuelEntry records (id, plate, litres, "
        "odometer, price) inside a FuelLog and exposes a few functions the depot scripts "
        "call. It reads what drivers type and sums it; it does not know where a van is, "
        "does not talk to fuel cards and has no persistence beyond the CSV the report "
        "script writes.\n\n## Non-goals\n- vehicle tracking or telematics\n- fuel-card "
        "reconciliation\n- multi-month history\n```\n\nA usage block for the scripts:\n\n"
        "```python\nfrom fuellog.journal import FuelLog, record_fill\n\nfl = FuelLog()\n"
        'record_fill(fl, "KX61 VAN", 42.5, 118400)\nprint(fl.litres_for("KX61 VAN"))\n```'
        "\n\nThe owner's question answers itself once the non-goals list says tracking is "
        "out; the package never sees a location, and the leasing company's telematics "
        "pitch can be answered with a link to that section.",
    ),
    Turn(
        "user",
        "Entry ids F1, F2 from a counter versus keying on plate plus odometer: the "
        "drivers sometimes fill twice in one day and occasionally write the same odometer "
        "reading on both receipts because they forgot to look. I want two entries in that "
        "case, not one overwriting the other, which argues for the counter. But the "
        "report script wants to say 'F14 looks wrong' and F14 means nothing to a driver. "
        "The report today is roughly:\n\n```python\nfor plate in sorted({e.plate for e in "
        'fl.all()}):\n    print(f"{plate:<10} {fl.litres_for(plate):>8.1f} L")\n```\n\nand '
        "I would like the anomaly line to point at something a driver can find in the "
        "glovebox. The drivers are Priya, Tom and whoever is covering, and none of them "
        "will ever open the spreadsheet, so whatever the report says has to make sense "
        "read aloud at the depot.",
    ),
    Turn(
        "assistant",
        "Counter ids are right for the reason you give: two fills are two entries even "
        "when the driver wrote the same reading twice, and a natural key would silently "
        "merge them. The report can be driver-friendly without changing the id: when it "
        "flags an entry, print the plate, the litres and the odometer alongside the id, "
        'since that triple is what the paper receipt shows:\n\n```python\nprint(f"{e.'
        'entry_id}: {e.plate} {e.litres:.1f} L at {e.odometer_km} km looks wrong")\n```'
        "\n\nThe id then serves the person correcting the entry, who needs an exact "
        "handle, and the receipt details serve the driver, who needs to recognise it. "
        "Keep `add` minting `F{n}` in insertion order so the ids match the order of lines "
        "in the drivers' file, which is the order the receipts sit in the glovebox. Read "
        "aloud, 'F14, KX61, forty-two and a half litres at 118,400' is enough for Tom to "
        "find the slip, and the id is still there for whoever edits the file.",
    ),
    Turn(
        "user",
        "Litres as float and odometer as int: I went back and forth. Pumps show two "
        "decimals of litres, odometers are whole kilometres. Here is the test I drafted "
        "for the sum per van, which is the only arithmetic the package does:\n\n```python\n"
        "from fuellog.journal import FuelLog, record_fill\n\n\ndef test_litres_for_sums_"
        'one_plate():\n    fl = FuelLog()\n    record_fill(fl, "KX61 VAN", 42.5, 118400)\n'
        '    record_fill(fl, "KX61 VAN", 38.0, 118910)\n    record_fill(fl, "LD19 VAN", '
        '50.0, 20100)\n    assert fl.litres_for("KX61 VAN") == 80.5\n\n\ndef test_litres_'
        'for_unknown_plate_is_zero():\n    assert FuelLog().litres_for("ZZ99 ZZZ") == 0\n'
        "```\n\nIs float going to bite me on the equality in the first test?",
    ),
    Turn(
        "assistant",
        "Not with those values: 42.5 and 38.0 are exactly representable and their sum is "
        "exactly 80.5, so the assertion is safe. Where float bites is a sum like 0.1 + "
        "0.2, and pump readings with two decimals can produce that. Two ways to stay "
        "safe: keep float and compare with `pytest.approx` in tests, or store "
        "centilitres as an int the way you would store cents. For a bakery's six vans "
        "the report rounds to one decimal anyway, so float plus `approx` is fine and "
        "keeps the drivers' file human-readable. Odometer as int is unambiguous. I would "
        "add one test with an awkward pair, `12.34 + 56.78`, asserting `approx(69.12)`, "
        "so nobody later 'fixes' the sum to an exact comparison and gets a surprise:\n\n"
        "```python\ndef test_litres_for_awkward_floats():\n    fl = FuelLog()\n    "
        'record_fill(fl, "MV07 VAN", 12.34, 500)\n    record_fill(fl, "MV07 VAN", '
        '56.78, 900)\n    assert fl.litres_for("MV07 VAN") == pytest.approx(69.12)\n```',
    ),
    Turn(
        "user",
        "Something I want to handle deliberately rather than by accident. Last month a "
        "driver typed 181400 instead of 118400 and the report printed a per-van "
        "consumption that was obviously nonsense, but only because I happened to look. "
        "I traced it and the entry is fine as data, it is just wrong. The report run "
        "looked like this:\n\n```\n$ python -m fuellog.report april.txt\nKX61 VAN     80.5 "
        "L over 63000 km\nLD19 VAN     50.0 L over 0 km\nMV07 VAN    121.0 L over 812 km\n"
        "```\n\nA 63,000 km month on a bakery van is impossible. I do not want the package "
        "to reject the entry, because sometimes the odometer really was replaced, but I "
        "want the fact that something odd happened to be visible somewhere other than my "
        "eyes, ideally in the same terminal where the report runs.",
    ),
    Turn(
        "assistant",
        "The distinction you are drawing is the right one: invalid input, like a negative "
        "reading, is a ValueError and the entry never lands; an implausible-but-legal "
        "input lands and gets flagged. The flag should not be a print, because the "
        "package is used by two scripts with different outputs, and it should not be an "
        "exception, because the entry is legal. A single `logging.warning` from the "
        "module logger is the standard answer: the report script can route it to stderr "
        "or a file with one `logging.basicConfig` call, tests can count it with "
        "`caplog`, and nothing else in the package changes. The threshold for 'odd' "
        "belongs in the operation that has the data at hand, and it should be named in "
        "the request for that operation, not hidden in a constant somewhere. In the "
        "report script the wiring is one line:\n\n```python\nlogging.basicConfig(level="
        'logging.WARNING, format="%(levelname)s %(message)s")\n```\n\nso the flag '
        "appears on stderr next to the table without the package knowing about stderr.",
    ),
    Turn(
        "user",
        "Agreed, rule: when an operation hits a condition we have called notable, it "
        "emits exactly one logging.warning through the module logger, not two, not an "
        "info, and nothing at all on the ordinary path. Every operation that names a "
        "notable case, existing or new, follows that.",
    ),
    Turn(
        "assistant",
        "Noted: notable conditions produce exactly one WARNING record from the module "
        "logger and ordinary calls produce no records. New operations that name a notable "
        "case emit that single warning and are otherwise silent, so a `caplog` count of "
        "one is the contract.",
    ),
    Turn(
        "user",
        "The validation rule, so it is written down: input checks live in the public "
        "functions in journal.py, the ones scripts call. `record_fill` and anything new "
        "raise ValueError on bad input, and FuelLog stays a plain store that trusts its "
        "arguments and never checks them.",
    ),
    Turn(
        "assistant",
        "Understood: validation belongs to the public functions, which raise ValueError "
        "before touching the store, and FuelLog methods do no checking of their own, so a "
        "store method called directly with a bad value simply stores it. New operations "
        "follow the same split.",
    ),
    Turn(
        "user",
        "For reference, the validation tests that exist today:\n\n```python\ndef "
        "test_record_rejects_zero_litres():\n    with pytest.raises(ValueError):\n        "
        'record_fill(FuelLog(), "KX61 VAN", 0, 118400)\n\n\ndef test_record_rejects_'
        "negative_odometer():\n    with pytest.raises(ValueError):\n        record_fill("
        'FuelLog(), "KX61 VAN", 40.0, -5)\n```',
    ),
    Turn(
        "assistant",
        "Both pin the check to the public function. A third, `test_add_trusts_arguments`, "
        'calling `FuelLog().add("KX61 VAN", 0, -5)` and asserting it stores, would pin '
        "the other half of the split so nobody later adds checks to the store by habit.",
    ),
    Turn(
        "user",
        "Good. First real feature: correcting an odometer reading after the fact, since "
        "the 181400 case will happen again. Then pump prices, because the owner wants "
        "cost per van. I will paste the current files with each request.",
    ),
    Turn(
        "assistant",
        "Ready. Send the request with the files and I will return the complete journal "
        "module, keeping `add`, `get`, `litres_for` and `record_fill` as they are.",
    ),
]

_EVENT = (
    "Side note before the next one: the owner wants the month-end CSV sorted by plate and "
    "then by entry id, and the litres column with one decimal. That is all in the report "
    "script; nothing in the package changes for it."
)


def build() -> Session:
    return Session(
        id="S29",
        project="fuellog",
        target_family="validation",
        support_family="logging",
        lifecycle="stable",
        files=_FILES,
        prefix=_PREFIX,
        states=("api", "storage"),
        state_at=("api", "api"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10),
    )
