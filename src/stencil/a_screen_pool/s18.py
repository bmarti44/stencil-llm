# ruff: noqa: E501
"""S18: weather stations — validation (target, replacement) x return_shape (support, dict)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""gaugenet package."""\n'

_UNITS = '''"""Unit helpers for station readings."""


def c_to_f(temp_c: float) -> float:
    return round(temp_c * 9 / 5 + 32, 1)


def mm_to_in(mm: float) -> float:
    return round(mm / 25.4, 2)
'''

_STATIONS_HEAD = '''"""Station registry and readings: storage layer (StationLog) and public functions."""

import re

STATION_ID = re.compile(r"^[A-Z]{{3}}[0-9]{{2}}$")


class StationLog:
    """Storage layer: keeps plain dict records and does not judge their values."""

    def __init__(self) -> None:
        self._stations: dict[str, dict] = {{}}
        self._readings: list[dict] = []

    def put_station(self, station_id: str, name: str) -> dict:
        station = {{"station_id": station_id, "name": name}}
        self._stations[station_id] = station
        return station

    def get_station(self, station_id: str) -> dict | None:
        return self._stations.get(station_id)

    def station_count(self) -> int:
        return len(self._stations)
{storage_methods}

def register_station(log: StationLog, station_id: str, name: str) -> dict:
    """Public entry point: checks the input, then stores."""
    if not STATION_ID.match(station_id):
        raise ValueError(f"bad station id {{station_id!r}}: expected three letters and two digits")
    if not name.strip():
        raise ValueError("station name must not be blank")
    return log.put_station(station_id, name.strip())
{public_functions}'''

_STATIONS = _STATIONS_HEAD.format(storage_methods="", public_functions="")

_FILES = {
    "gaugenet/__init__.py": _INIT,
    "gaugenet/units.py": _UNITS,
    "gaugenet/stations.py": _STATIONS,
}

# ----------------------------------------------------------------- checkpoint 1: record_temperature

_C1_FUNCTIONAL = {
    "test_temp_functional.py": """import pytest

from gaugenet.stations import StationLog, record_temperature, register_station

HRB01 = {"station_id": "HRB01", "name": "Harbour mouth"}
MST07 = {"station_id": "MST07", "name": "Moor street"}


def _log():
    # TWO stations; every test below records against the first one
    log = StationLog()
    register_station(log, "HRB01", "Harbour mouth")
    register_station(log, "MST07", "Moor street")
    return log


def test_record_temperature_stores_and_returns_reading():
    log = _log()
    out = record_temperature(log, "HRB01", "2026-09-14T06:00", 12.5)
    assert out["station_id"] == "HRB01" and out["at"] == "2026-09-14T06:00"
    assert out["temp_c"] == 12.5
    assert log.readings_for("HRB01") == [out]
    assert log.get_station("HRB01") == HRB01
    assert log.get_station("MST07") == MST07
    assert log.readings_for("MST07") == []
    assert log.station_count() == 2


def test_readings_kept_in_order():
    log = _log()
    a = record_temperature(log, "HRB01", "2026-09-14T06:00", 12.5)
    b = record_temperature(log, "HRB01", "2026-09-14T07:00", 13.0)
    assert log.readings_for("HRB01") == [a, b]
    assert log.readings_for("HRB02") == []
    assert log.get_station("MST07") == MST07
    assert log.station_count() == 2


@pytest.mark.parametrize("bad", [-90.5, 60.1, -273.15, 999.0])
def test_record_temperature_rejects_out_of_range(bad):
    log = _log()
    with pytest.raises(ValueError):
        record_temperature(log, "HRB01", "2026-09-14T06:00", bad)
    assert log.readings_for("HRB01") == []
    assert log.get_station("HRB01") == HRB01
    assert log.get_station("MST07") == MST07
    assert log.station_count() == 2


@pytest.mark.parametrize("edge", [-90.0, 60.0, 0.0])
def test_record_temperature_accepts_bounds(edge):
    log = _log()
    assert record_temperature(log, "HRB01", "2026-09-14T06:00", edge)["temp_c"] == edge
    assert log.get_station("MST07") == MST07
    assert log.station_count() == 2


def test_record_temperature_unknown_station_raises_keyerror():
    log = _log()
    with pytest.raises(KeyError):
        record_temperature(log, "XXX99", "2026-09-14T06:00", 10.0)
    assert log.station_count() == 2


def test_registering_a_station_keeps_the_earlier_ones():
    log = _log()
    third = register_station(log, "VLY11", "Valley floor")
    assert log.get_station("HRB01") == HRB01
    assert log.get_station("MST07") == MST07
    assert log.get_station("VLY11") is third
    assert log.station_count() == 3
"""
}

_C1_REGRESSION = {
    "test_temp_regression.py": """import pytest

from gaugenet.stations import StationLog, register_station
from gaugenet.units import c_to_f, mm_to_in


def test_register_validates_and_stores():
    log = StationLog()
    st = register_station(log, "HRB01", " Harbour mouth ")
    assert st == {"station_id": "HRB01", "name": "Harbour mouth"}
    assert log.get_station("HRB01") is st and log.station_count() == 1
    assert log.get_station("nope") is None
    with pytest.raises(ValueError):
        register_station(log, "hrb01", "lower case id")
    with pytest.raises(ValueError):
        register_station(log, "HRB02", "  ")
    assert log.station_count() == 1


def test_put_station_stores_without_checking():
    log = StationLog()
    kept = register_station(log, "HRB01", "Harbour mouth")
    assert log.put_station("nope", "")["station_id"] == "nope"
    assert log.get_station("HRB01") is kept and log.station_count() == 2


def test_register_keeps_every_earlier_station():
    log = StationLog()
    a = register_station(log, "HRB01", "Harbour mouth")
    b = register_station(log, "MST07", "Moor street")
    assert log.get_station("HRB01") is a and log.get_station("MST07") is b
    assert log.station_count() == 2
    c = register_station(log, "VLY11", "Valley floor")
    assert log.get_station("HRB01") is a and log.get_station("MST07") is b
    assert log.get_station("VLY11") is c
    assert log.station_count() == 3


def test_units_unchanged():
    assert c_to_f(20) == 68.0 and mm_to_in(25.4) == 1.0
"""
}

_C1_CONTRACT = {
    "api": {
        "test_temp_validation.py": """import pytest

from gaugenet.stations import StationLog, record_temperature, register_station


def test_public_function_rejects_and_storage_does_not():
    log = StationLog()
    register_station(log, "HRB01", "Harbour mouth")
    with pytest.raises(ValueError):
        record_temperature(log, "HRB01", "2026-09-14T06:00", 75.0)
    # the storage layer stores whatever it is given
    out = log.put_reading("HRB01", "2026-09-14T06:00", 75.0)
    assert out["temp_c"] == 75.0
    assert log.readings_for("HRB01") == [out]
"""
    },
    "storage": {
        "test_temp_validation.py": """import pytest

from gaugenet.stations import StationLog, record_temperature, register_station


def test_storage_rejects_directly():
    log = StationLog()
    register_station(log, "HRB01", "Harbour mouth")
    with pytest.raises(ValueError):
        log.put_reading("HRB01", "2026-09-14T06:00", 75.0)
    assert log.readings_for("HRB01") == []


def test_public_function_passes_invalid_value_through(monkeypatch):
    log = StationLog()
    register_station(log, "HRB01", "Harbour mouth")
    seen = []

    def spy(self, station_id, at, temp_c):
        seen.append((station_id, at, temp_c))
        return None

    monkeypatch.setattr(StationLog, "put_reading", spy)
    record_temperature(log, "HRB01", "2026-09-14T06:00", 75.0)
    assert seen == [("HRB01", "2026-09-14T06:00", 75.0)]
"""
    },
}

_C1_SUPPORT = {
    "test_temp_shape.py": """from dataclasses import is_dataclass

from gaugenet.stations import StationLog, record_temperature, register_station


def test_record_temperature_returns_plain_dict():
    log = StationLog()
    register_station(log, "HRB01", "Harbour mouth")
    out = record_temperature(log, "HRB01", "2026-09-14T06:00", 12.5)
    assert type(out) is dict
    assert not is_dataclass(out)
"""
}

_STORAGE1_API = """
    def put_reading(self, station_id: str, at: str, temp_c: float) -> dict:
        if station_id not in self._stations:
            raise KeyError(station_id)
        reading = {"station_id": station_id, "at": at, "temp_c": temp_c}
        self._readings.append(reading)
        return reading

    def readings_for(self, station_id: str) -> list[dict]:
        return [r for r in self._readings if r["station_id"] == station_id]
"""

_STORAGE1_STORAGE = """
    def put_reading(self, station_id: str, at: str, temp_c: float) -> dict:
        if not -90.0 <= temp_c <= 60.0:
            raise ValueError(f"temperature {temp_c} C is outside the plausible range")
        if station_id not in self._stations:
            raise KeyError(station_id)
        reading = {"station_id": station_id, "at": at, "temp_c": temp_c}
        self._readings.append(reading)
        return reading

    def readings_for(self, station_id: str) -> list[dict]:
        return [r for r in self._readings if r["station_id"] == station_id]
"""

_PUBLIC1_API = '''

def record_temperature(log: StationLog, station_id: str, at: str, temp_c: float) -> dict:
    """Public entry point: checks the value, then stores."""
    if not -90.0 <= temp_c <= 60.0:
        raise ValueError(f"temperature {temp_c} C is outside the plausible range")
    return log.put_reading(station_id, at, temp_c)
'''

_PUBLIC1_STORAGE = """

def record_temperature(log: StationLog, station_id: str, at: str, temp_c: float) -> dict:
    return log.put_reading(station_id, at, temp_c)
"""

_GOLD1 = {
    "api": _STATIONS_HEAD.format(
        storage_methods=_STORAGE1_API, public_functions=_PUBLIC1_API
    ),
    "storage": _STATIONS_HEAD.format(
        storage_methods=_STORAGE1_STORAGE, public_functions=_PUBLIC1_STORAGE
    ),
}

_REQ1 = Request(
    text=(
        "Add temperature readings. On StationLog add `put_reading(station_id, at, "
        "temp_c)` that appends a reading dict with keys station_id, at and temp_c and "
        "returns it (KeyError for an unknown station), and `readings_for(station_id)` "
        "returning that station's readings in the order recorded (empty list if none). "
        "Add a public function `record_temperature(log, station_id, at, temp_c)` that "
        "records one reading. A temperature outside -90.0 to 60.0 C inclusive is "
        "invalid input and must raise ValueError without storing anything."
    ),
    target="gaugenet/stations.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold=_GOLD1,
)

# ----------------------------------------------------------------- checkpoint 2: record_rainfall

_C2_FUNCTIONAL = {
    "test_rain_functional.py": """import pytest

from gaugenet.stations import StationLog, record_rainfall, register_station

HRB01 = {"station_id": "HRB01", "name": "Harbour mouth"}
MST07 = {"station_id": "MST07", "name": "Moor street"}


def _log():
    # TWO stations; every test below records against the first one
    log = StationLog()
    register_station(log, "HRB01", "Harbour mouth")
    register_station(log, "MST07", "Moor street")
    return log


def test_record_rainfall_stores_and_returns_reading():
    log = _log()
    out = record_rainfall(log, "HRB01", "2026-09-14T06:00", 3.4)
    assert out["station_id"] == "HRB01" and out["at"] == "2026-09-14T06:00"
    assert out["rain_mm"] == 3.4
    assert log.readings_for("HRB01") == [out]
    assert log.get_station("HRB01") == HRB01
    assert log.get_station("MST07") == MST07
    assert log.readings_for("MST07") == []
    assert log.station_count() == 2


def test_rainfall_and_temperature_share_the_order():
    log = _log()
    a = record_rainfall(log, "HRB01", "2026-09-14T06:00", 0.0)
    b = record_rainfall(log, "HRB01", "2026-09-14T07:00", 1.2)
    assert log.readings_for("HRB01") == [a, b]
    assert log.get_station("MST07") == MST07
    assert log.station_count() == 2


@pytest.mark.parametrize("bad", [-0.1, -5.0, 500.1])
def test_record_rainfall_rejects_out_of_range(bad):
    log = _log()
    with pytest.raises(ValueError):
        record_rainfall(log, "HRB01", "2026-09-14T06:00", bad)
    assert log.readings_for("HRB01") == []
    assert log.get_station("HRB01") == HRB01
    assert log.get_station("MST07") == MST07
    assert log.station_count() == 2


@pytest.mark.parametrize("edge", [0.0, 500.0])
def test_record_rainfall_accepts_bounds(edge):
    log = _log()
    assert record_rainfall(log, "HRB01", "2026-09-14T06:00", edge)["rain_mm"] == edge
    assert log.get_station("MST07") == MST07
    assert log.station_count() == 2


def test_record_rainfall_unknown_station_raises_keyerror():
    log = _log()
    with pytest.raises(KeyError):
        record_rainfall(log, "XXX99", "2026-09-14T06:00", 1.0)
    assert log.station_count() == 2


def test_registering_a_station_keeps_the_earlier_ones():
    log = _log()
    third = register_station(log, "VLY11", "Valley floor")
    assert log.get_station("HRB01") == HRB01
    assert log.get_station("MST07") == MST07
    assert log.get_station("VLY11") is third
    assert log.station_count() == 3
"""
}

_C2_REGRESSION = {
    "test_rain_regression.py": """import pytest

from gaugenet.stations import StationLog, record_temperature, register_station

HRB01 = {"station_id": "HRB01", "name": "Harbour mouth"}
MST07 = {"station_id": "MST07", "name": "Moor street"}


def test_register_and_temperature_unchanged():
    log = StationLog()
    register_station(log, "HRB01", "Harbour mouth")
    other = register_station(log, "MST07", "Moor street")
    with pytest.raises(ValueError):
        register_station(log, "HRB1", "short id")
    r = record_temperature(log, "HRB01", "2026-09-14T06:00", 12.5)
    assert log.readings_for("HRB01") == [r]
    with pytest.raises(ValueError):
        record_temperature(log, "HRB01", "2026-09-14T07:00", 61.0)
    assert log.readings_for("HRB01") == [r]
    assert log.put_reading("HRB01", "2026-09-14T08:00", 61.0)["temp_c"] == 61.0
    assert log.get_station("MST07") is other and log.get_station("MST07") == MST07
    assert log.get_station("HRB01") == HRB01
    assert log.readings_for("MST07") == []
    assert log.station_count() == 2


def test_register_keeps_every_earlier_station():
    log = StationLog()
    a = register_station(log, "HRB01", "Harbour mouth")
    b = register_station(log, "MST07", "Moor street")
    assert log.get_station("HRB01") is a and log.get_station("MST07") is b
    assert log.station_count() == 2
    c = register_station(log, "VLY11", "Valley floor")
    assert log.get_station("HRB01") is a and log.get_station("MST07") is b
    assert log.get_station("VLY11") is c
    assert log.station_count() == 3
"""
}

_C2_CONTRACT = {
    "api": {
        "test_rain_validation.py": """import pytest

from gaugenet.stations import StationLog, record_rainfall, register_station


def test_public_function_rejects_and_storage_does_not():
    log = StationLog()
    register_station(log, "HRB01", "Harbour mouth")
    with pytest.raises(ValueError):
        record_rainfall(log, "HRB01", "2026-09-14T06:00", -2.0)
    # the storage layer stores whatever it is given
    out = log.put_rainfall("HRB01", "2026-09-14T06:00", -2.0)
    assert out["rain_mm"] == -2.0
    assert log.readings_for("HRB01") == [out]
"""
    },
    "storage": {
        "test_rain_validation.py": """import pytest

from gaugenet.stations import StationLog, record_rainfall, register_station


def test_storage_rejects_directly():
    log = StationLog()
    register_station(log, "HRB01", "Harbour mouth")
    with pytest.raises(ValueError):
        log.put_rainfall("HRB01", "2026-09-14T06:00", -2.0)
    assert log.readings_for("HRB01") == []


def test_public_function_passes_invalid_value_through(monkeypatch):
    log = StationLog()
    register_station(log, "HRB01", "Harbour mouth")
    seen = []

    def spy(self, station_id, at, rain_mm):
        seen.append((station_id, at, rain_mm))
        return None

    monkeypatch.setattr(StationLog, "put_rainfall", spy)
    record_rainfall(log, "HRB01", "2026-09-14T06:00", -2.0)
    assert seen == [("HRB01", "2026-09-14T06:00", -2.0)]
"""
    },
}

_C2_SUPPORT = {
    "test_rain_shape.py": """from dataclasses import is_dataclass

from gaugenet.stations import StationLog, record_rainfall, register_station


def test_record_rainfall_returns_plain_dict():
    log = StationLog()
    register_station(log, "HRB01", "Harbour mouth")
    out = record_rainfall(log, "HRB01", "2026-09-14T06:00", 3.4)
    assert type(out) is dict
    assert not is_dataclass(out)
"""
}

_STORAGE2_API = """
    def put_rainfall(self, station_id: str, at: str, rain_mm: float) -> dict:
        if station_id not in self._stations:
            raise KeyError(station_id)
        reading = {"station_id": station_id, "at": at, "rain_mm": rain_mm}
        self._readings.append(reading)
        return reading
"""

_STORAGE2_STORAGE = """
    def put_rainfall(self, station_id: str, at: str, rain_mm: float) -> dict:
        if not 0.0 <= rain_mm <= 500.0:
            raise ValueError(f"rainfall {rain_mm} mm is outside the plausible range")
        if station_id not in self._stations:
            raise KeyError(station_id)
        reading = {"station_id": station_id, "at": at, "rain_mm": rain_mm}
        self._readings.append(reading)
        return reading
"""

_PUBLIC2_API = '''

def record_rainfall(log: StationLog, station_id: str, at: str, rain_mm: float) -> dict:
    """Public entry point: checks the value, then stores."""
    if not 0.0 <= rain_mm <= 500.0:
        raise ValueError(f"rainfall {rain_mm} mm is outside the plausible range")
    return log.put_rainfall(station_id, at, rain_mm)
'''

_PUBLIC2_STORAGE = """

def record_rainfall(log: StationLog, station_id: str, at: str, rain_mm: float) -> dict:
    return log.put_rainfall(station_id, at, rain_mm)
"""


def _gold2(state: str) -> str:
    # Built on the checkpoint-1 gold under the state then in force (api).
    storage = _STORAGE2_API if state == "api" else _STORAGE2_STORAGE
    public = _PUBLIC2_API if state == "api" else _PUBLIC2_STORAGE
    return _STATIONS_HEAD.format(
        storage_methods=_STORAGE1_API + storage,
        public_functions=_PUBLIC1_API + public,
    )


_REQ2 = Request(
    text=(
        "Add rainfall readings. On StationLog add `put_rainfall(station_id, at, "
        "rain_mm)` that appends a reading dict with keys station_id, at and rain_mm to "
        "the same readings list as temperatures and returns it (KeyError for an unknown "
        "station). Add a public function `record_rainfall(log, station_id, at, rain_mm)` "
        "that records one rainfall reading. A rainfall amount below 0.0 or above 500.0 "
        "mm is invalid input and must raise ValueError without storing anything."
    ),
    target="gaugenet/stations.py",
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
        "Our sailing club runs three cheap weather stations along the estuary and the "
        "readings arrive as lines in a text file that a Raspberry Pi appends to every "
        "ten minutes. I want to replace the shell script that parses it with a small "
        "Python package, gaugenet: register the stations, record readings, and let a "
        "cron job build the table for the club noticeboard. Everything runs on the one "
        "Pi, no database. Here is the README so far:\n\n```\n# gaugenet\n\nIn-memory "
        "station registry and readings for a handful of estuary weather stations. "
        "Station ids are three letters and two digits (HRB01, PTL02). Readings are "
        "timestamped to the minute. `ingest.py` feeds the Pi's log file into a "
        "StationLog; `board.py` renders the noticeboard table.\n```\n\nThe raw lines look "
        "like this:\n\n```\n2026-09-14T06:00 HRB01 T 12.5\n2026-09-14T06:00 PTL02 T "
        "11.9\n2026-09-14T06:10 HRB01 R 0.2\n```\n\nT is Celsius, R is millimetres of rain.",
    ),
    Turn(
        "assistant",
        "That is a good scope statement; the two scripts and the id format are the "
        "things people need to know. I would add the boundary explicitly so nobody "
        "later puts file handling inside the package:\n\n```\n## Persistence\nThe "
        "library does no I/O. `ingest.py` reads the Pi log and calls the public "
        "functions; `board.py` reads the StationLog it builds and writes "
        "`noticeboard.txt`.\n\n## Non-goals\n- wind and pressure (not measured)\n- "
        "forecasts\n- more than one club\n```\n\nFor the code, I would keep one module "
        "with a `StationLog` class that stores records and module-level public "
        "functions (`register_station`, and soon the readings) that the scripts call. "
        "The class is the storage layer, the functions are the entry points, and each "
        "gets a docstring saying so. `ingest.py` then becomes a loop that splits each "
        "line on whitespace and dispatches on the T or R column:\n\n```python\nat, "
        'station_id, kind, value = line.split()\nif kind == "T":\n    '
        "record_temperature(log, station_id, at, float(value))\n```",
    ),
    Turn(
        "user",
        "Here is where the module stands, with the one public function we have and a "
        'regex for ids:\n\n```python\nSTATION_ID = re.compile(r"^[A-Z]{3}[0-9]{2}$")\n\n'
        "\nclass StationLog:\n    def put_station(self, station_id: str, name: str) -> "
        'dict:\n        station = {"station_id": station_id, "name": name}\n        '
        "self._stations[station_id] = station\n        return station\n\n\ndef "
        "register_station(log: StationLog, station_id: str, name: str) -> dict:\n    if "
        "not STATION_ID.match(station_id):\n        raise ValueError(...)\n    if not "
        'name.strip():\n        raise ValueError("station name must not be blank")\n    '
        "return log.put_station(station_id, name.strip())\n```\n\nThe split you "
        "describe is what I did by instinct, but I want to hear the argument for it. "
        "Why not have `put_station` reject a bad id itself, so the store can never hold "
        "junk? The regex is strict on purpose: the Pi once logged `hrb01` after a "
        "firmware update and the shell script created a fourth station.",
    ),
    Turn(
        "assistant",
        "The argument for checking in the public function is that the public function "
        "is the only door the scripts use, so every bad value is caught exactly once, "
        "with a message written for the person running `ingest.py`, and the storage "
        "class stays a plain container that can be filled from a saved file without "
        "re-checking three hundred readings. It is a choice, not a law; the other "
        "design puts the checks in the storage methods and lets the public functions "
        "pass values straight through, which is better when several entry points share "
        "one store. Whichever you pick, do it consistently and pin it with a test so "
        "nobody adds a second copy of the check in the other layer:\n\n```python\ndef "
        "test_put_station_stores_without_checking():\n    log = StationLog()\n    assert "
        'log.put_station("nope", "")["station_id"] == "nope"\n```\n\nThat test reads '
        "oddly to a newcomer, which is exactly why it is useful: it says the store is "
        "deliberately trusting. Your lower-case `hrb01` story is a point for the "
        "public-function design too: the ingest loop is where a bad id can be reported "
        "with the line number, which the store does not know.",
    ),
    Turn(
        "user",
        "Understood, and that test is in. Here is the rest of the test file, all "
        "passing:\n\n```python\nimport pytest\n\nfrom gaugenet.stations import "
        "StationLog, register_station\n\n\ndef test_register_stores_station():\n    log "
        '= StationLog()\n    st = register_station(log, "HRB01", "Harbour mouth")\n    '
        'assert st["station_id"] == "HRB01"\n    assert log.get_station("HRB01") is st\n'
        "\n\ndef test_register_rejects_bad_id():\n    with pytest.raises(ValueError):\n"
        '        register_station(StationLog(), "hrb01", "lower case")\n\n\ndef '
        "test_register_rejects_blank_name():\n    with pytest.raises(ValueError):\n"
        '        register_station(StationLog(), "HRB02", "  ")\n\n\ndef '
        "test_get_station_missing_returns_none():\n    assert StationLog().get_station("
        '"PTL02") is None\n```\n\nNext I need to decide the shape of a reading before I '
        "write any of that code. Plain dict, dataclass, namedtuple? `board.py` will "
        "format them into a fixed-width table and `ingest.py` will dump a JSON snapshot "
        "of the day, so whatever we pick needs to be cheap at both ends.",
    ),
    Turn(
        "assistant",
        "For this package I would return plain dicts everywhere, and you are already "
        "doing that for stations. The reason is what the records are for: they go "
        "straight from `ingest.py` into `json.dump` for the day's snapshot and straight "
        "from `board.py` into a `str.format` template, and a dict does both with no "
        "conversion. A dataclass would buy attribute access and a type for the editor, "
        "but you would pay `asdict()` at every boundary and the Pi scripts are the "
        "only callers. Keep the keys fixed and documented so callers can rely on them:"
        '\n\n```python\n{"station_id": "HRB01", "at": "2026-09-14T06:00", "temp_c"'
        ": 12.5}\n```\n\nThe one discipline dicts need is that every public function "
        "returns the same shape for the same kind of record, which a short test can "
        "pin with `type(out) is dict` and a check on the key set. Lists of readings "
        "are then lists of dicts, and lookups return a dict or None.",
    ),
    Turn(
        "user",
        "Dicts it is. Now, ranges. Last winter a station sent `T 812.3` for an hour "
        "when its sensor cable got wet, and the shell script cheerfully averaged it "
        "into the daily figure on the noticeboard, so the club thought the estuary had "
        "boiled. I want physically implausible readings rejected before they get "
        "anywhere near the log. This is the kind of line that came through:\n\n```\n"
        "2026-01-19T03:10 PTL02 T 812.3\n2026-01-19T03:20 PTL02 T 812.3\n2026-01-19T03:30 "
        "PTL02 T -4.1\n```\n\nThe met office's world extremes are roughly -90 to 60 "
        "Celsius, so anything outside that is certainly a fault. Should a rejected "
        "reading raise, or be silently skipped? Skipping feels friendlier for a cron "
        "job, but I worry we would never find out that a sensor has died.",
    ),
    Turn(
        "assistant",
        "Raise ValueError, and let `ingest.py` decide what to do with it. A library "
        "that silently skips is a library that hides sensor faults, which is the wet-"
        "cable story with the noticeboard replaced by a log nobody reads. Raising "
        "means the ingest loop can count the rejects and print a one-line note:\n\n```"
        "python\nrejected = 0\nfor line in lines:\n    try:\n        dispatch(log, line)\n"
        '    except ValueError as exc:\n        rejected += 1\n        print(f"skip: '
        '{exc}")\nprint(f"{rejected} readings rejected")\n```\n\nUse an inclusive '
        "range so the boundary values are accepted, and put the limits in the error "
        "message so the note is self-explanatory. Rainfall will want its own range "
        "later (zero to a few hundred millimetres), and the same pattern applies. The "
        "count of rejects per run is also the cheapest possible sensor-health check: "
        "if PTL02 rejects six readings in an hour, someone should go and look at the "
        "cable before the next storm.",
    ),
    Turn(
        "user",
        "Settled then: public functions in gaugenet return plain dicts with fixed, "
        "documented keys, never dataclasses or tuples, and that is the rule for every "
        "record type we add.",
    ),
    Turn(
        "assistant",
        "Noted: every public function returns a plain dict with a fixed key set (or None "
        "from lookups, or a list of dicts), never a dataclass or tuple. I will document "
        "the keys in each function's docstring.",
    ),
    Turn(
        "user",
        "And keep the validation layering as it is today: input checks live in the "
        "public functions, which raise ValueError; the StationLog storage methods store "
        "what they are given and never raise ValueError on values. New features follow "
        "the same split.",
    ),
    Turn(
        "assistant",
        "Understood: validation stays in the public entry points, raising ValueError "
        "with the limits in the message, and the StationLog methods remain trusting "
        "stores. New storage methods get no value checks; new public functions check "
        "before calling the store.",
    ),
    Turn(
        "user",
        "For later: `board.py` wants the latest reading per station plus a daily "
        "minimum and maximum. Roughly:\n\n```python\nfor st in log.stations():\n    "
        'temps = [r["temp_c"] for r in log.readings_for(st["station_id"]) if '
        '"temp_c" in r]\n    print(st["name"], min(temps), max(temps), temps[-1])\n```'
        "\n\nwhere `stations()` does not exist yet.",
    ),
    Turn(
        "assistant",
        "That will work once readings exist. `stations()` is `list(self._stations."
        "values())`, and keeping temperature and rainfall in one readings list with "
        "different keys is fine because the comprehension filters on the key.",
    ),
    Turn(
        "user",
        "Right, let's get temperature readings in; the noticeboard has been blank since "
        "the shell script broke. I will paste the current files with each request so "
        "you see the true state rather than my memory of it.",
    ),
    Turn(
        "assistant",
        "Ready. Send the request with the files and I will return the complete stations "
        "module.",
    ),
]

_EVENT = (
    "Change of convention for new code, effective now: value validation lives in the "
    "StationLog storage methods themselves, which raise ValueError, and the public "
    "functions just pass values through and let that propagate with no separate check "
    "of their own. Existing functions (register_station and the temperature code you "
    "just wrote) stay exactly as they are; only new features follow the new split."
)


def build() -> Session:
    return Session(
        id="S18",
        project="gaugenet",
        target_family="validation",
        support_family="return_shape",
        lifecycle="replacement",
        files=_FILES,
        prefix=_PREFIX,
        states=("api", "storage"),
        state_at=("api", "storage"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10),
    )
