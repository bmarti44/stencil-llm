# ruff: noqa: E501
"""S37: river gauges — missing_record (target, stable) x return_shape (support)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""rivergauge package."""\n'

_MODEL = '''"""Gauge records as plain dicts."""


def new_gauge(gauge_id, river, site):
    return {"gauge_id": gauge_id, "river": river, "site": site, "readings": [], "threshold_m": None, "status": "live"}
'''

_NETWORK = '''"""In-memory register of the staff gauges the group maintains."""

from rivergauge.model import new_gauge


class GaugeNetwork:
    def __init__(self):
        self._gauges = {}
        self._n = 0

    def install(self, river, site):
        self._n += 1
        gauge = new_gauge(f"G{self._n}", river, site)
        self._gauges[gauge["gauge_id"]] = gauge
        return gauge

    def find(self, gauge_id):
        return self._gauges.get(gauge_id)

    def add_reading(self, gauge_id, level_m):
        gauge = self._gauges[gauge_id]
        gauge["readings"].append(level_m)
        return gauge
'''

_ALERTS = '''"""Flood-watch helpers over a gauge record."""


def above_threshold(gauge):
    if gauge["threshold_m"] is None or not gauge["readings"]:
        return False
    return gauge["readings"][-1] >= gauge["threshold_m"]
'''

_FILES = {
    "rivergauge/__init__.py": _INIT,
    "rivergauge/model.py": _MODEL,
    "rivergauge/network.py": _NETWORK,
    "rivergauge/alerts.py": _ALERTS,
}

# ----------------------------------------------------------------- checkpoint 1: set_threshold

_C1_FUNCTIONAL = {
    "test_set_threshold_functional.py": """from rivergauge.alerts import above_threshold
from rivergauge.network import GaugeNetwork


def test_set_threshold_updates_and_stores():
    net = GaugeNetwork()
    gauge = net.install("Wharfe", "Otley bridge")
    out = net.set_threshold(gauge["gauge_id"], 2.4)
    assert out["threshold_m"] == 2.4
    assert net.find(gauge["gauge_id"])["threshold_m"] == 2.4


def test_set_threshold_keeps_readings_and_feeds_alerts():
    net = GaugeNetwork()
    gauge = net.install("Aire", "Kildwick")
    net.add_reading(gauge["gauge_id"], 1.1)
    net.add_reading(gauge["gauge_id"], 2.6)
    out = net.set_threshold(gauge["gauge_id"], 2.5)
    assert out["readings"] == [1.1, 2.6] and out["site"] == "Kildwick"
    assert above_threshold(out) is True
"""
}

_C1_REGRESSION = {
    "test_set_threshold_regression.py": """import pytest

from rivergauge.alerts import above_threshold
from rivergauge.network import GaugeNetwork


def test_install_find_add_reading_unchanged():
    net = GaugeNetwork()
    gauge = net.install("Wharfe", "Otley bridge")
    assert gauge["gauge_id"] == "G1" and gauge["readings"] == [] and gauge["status"] == "live"
    assert net.find("G1") is gauge
    assert net.find("G9") is None
    assert net.add_reading("G1", 0.8)["readings"] == [0.8]
    assert above_threshold(gauge) is False
    with pytest.raises(KeyError):
        net.add_reading("G9", 0.5)
"""
}

_C1_CONTRACT = {
    "raise": {
        "test_set_threshold_missing.py": """import pytest

from rivergauge.network import GaugeNetwork


def test_set_threshold_unknown_raises_keyerror():
    net = GaugeNetwork()
    net.install("Wharfe", "Otley bridge")
    with pytest.raises(KeyError):
        net.set_threshold("G99", 2.0)
"""
    },
    "none": {
        "test_set_threshold_missing.py": """from rivergauge.network import GaugeNetwork


def test_set_threshold_unknown_returns_none_and_changes_nothing():
    net = GaugeNetwork()
    gauge = net.install("Wharfe", "Otley bridge")
    assert net.set_threshold("G99", 2.0) is None
    assert net.find("G99") is None
    assert net.find(gauge["gauge_id"])["threshold_m"] is None
"""
    },
}

_C1_SUPPORT = {
    "test_set_threshold_shape.py": """from dataclasses import is_dataclass

from rivergauge.network import GaugeNetwork


def test_set_threshold_returns_plain_dict():
    net = GaugeNetwork()
    gauge = net.install("Wharfe", "Otley bridge")
    out = net.set_threshold(gauge["gauge_id"], 2.4)
    assert type(out) is dict
    assert not is_dataclass(out)
"""
}

_LOOKUP = {
    "raise": "        gauge = self._gauges[gauge_id]\n",
    "none": (
        "        gauge = self._gauges.get(gauge_id)\n"
        "        if gauge is None:\n"
        "            return None\n"
    ),
}


def _gold1(state: str) -> str:
    return (
        _NETWORK.rstrip("\n")
        + "\n\n    def set_threshold(self, gauge_id, level_m):\n"
        + _LOOKUP[state]
        + '        gauge["threshold_m"] = level_m\n'
        "        return gauge\n"
    )


_REQ1 = Request(
    text=(
        "Add a public method `set_threshold(gauge_id, level_m)` on GaugeNetwork: it sets "
        "the gauge's flood-watch threshold in metres (the level the alerts helper compares "
        "against) and returns the gauge record."
    ),
    target="rivergauge/network.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"raise": _gold1("raise"), "none": _gold1("none")},
)

# ----------------------------------------------------------------- checkpoint 2: decommission

_C2_FUNCTIONAL = {
    "test_decommission_functional.py": """from rivergauge.network import GaugeNetwork


def test_decommission_marks_retired_and_stores():
    net = GaugeNetwork()
    gauge = net.install("Wharfe", "Otley bridge")
    out = net.decommission(gauge["gauge_id"])
    assert out["status"] == "retired"
    assert net.find(gauge["gauge_id"])["status"] == "retired"


def test_decommission_keeps_readings_and_threshold():
    net = GaugeNetwork()
    gauge = net.install("Aire", "Kildwick")
    net.add_reading(gauge["gauge_id"], 1.4)
    net.set_threshold(gauge["gauge_id"], 2.5)
    out = net.decommission(gauge["gauge_id"])
    assert out["readings"] == [1.4] and out["threshold_m"] == 2.5
    assert out["gauge_id"] == gauge["gauge_id"] and out["river"] == "Aire"
"""
}

_C2_REGRESSION = {
    "test_decommission_regression.py": """import pytest

from rivergauge.network import GaugeNetwork


def test_install_find_add_reading_set_threshold_unchanged():
    net = GaugeNetwork()
    gauge = net.install("Wharfe", "Otley bridge")
    assert net.find("G1") is gauge and net.find("G9") is None
    assert net.add_reading("G1", 0.8)["readings"] == [0.8]
    assert net.set_threshold("G1", 2.0)["threshold_m"] == 2.0
    with pytest.raises(KeyError):
        net.add_reading("G9", 0.5)
    with pytest.raises(KeyError):
        net.set_threshold("G9", 2.0)
"""
}

_C2_CONTRACT = {
    "raise": {
        "test_decommission_missing.py": """import pytest

from rivergauge.network import GaugeNetwork


def test_decommission_unknown_raises_keyerror():
    net = GaugeNetwork()
    net.install("Wharfe", "Otley bridge")
    with pytest.raises(KeyError):
        net.decommission("G99")
"""
    },
    "none": {
        "test_decommission_missing.py": """from rivergauge.network import GaugeNetwork


def test_decommission_unknown_returns_none_and_changes_nothing():
    net = GaugeNetwork()
    gauge = net.install("Wharfe", "Otley bridge")
    assert net.decommission("G99") is None
    assert net.find("G99") is None
    assert net.find(gauge["gauge_id"])["status"] == "live"
"""
    },
}

_C2_SUPPORT = {
    "test_decommission_shape.py": """from dataclasses import is_dataclass

from rivergauge.network import GaugeNetwork


def test_decommission_returns_plain_dict():
    net = GaugeNetwork()
    gauge = net.install("Wharfe", "Otley bridge")
    out = net.decommission(gauge["gauge_id"])
    assert type(out) is dict
    assert not is_dataclass(out)
"""
}


def _gold2(state: str) -> str:
    # Built on the checkpoint-1 gold under the state then in force (raise).
    return (
        _gold1("raise").rstrip("\n")
        + "\n\n    def decommission(self, gauge_id):\n"
        + _LOOKUP[state]
        + '        gauge["status"] = "retired"\n'
        "        return gauge\n"
    )


_REQ2 = Request(
    text=(
        "Add a public method `decommission(gauge_id)` on GaugeNetwork for a gauge that has "
        'been removed from the river: it sets the status to "retired", keeps the readings '
        "and threshold for the archive, and returns the gauge record."
    ),
    target="rivergauge/network.py",
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
        "I help run a volunteer river-watch group in the Dales. We maintain eleven staff "
        "gauges, and once a week whoever walks past one texts "
        "me the level. I type them into a spreadsheet and, when a river is high, phone the "
        "two farms downstream. I want to replace the spreadsheet with a small package, "
        "rivergauge: an in-memory GaugeNetwork with one record per gauge and a script that "
        "prints the weekly state:\n\n```\n$ python -m rivergauge.weekly\nG1  Wharfe  Otley "
        "bridge   1.9m  (watch 2.4m)\nG2  Aire    Kildwick       2.6m  (watch 2.5m)  HIGH\n"
        "G3  Nidd    Pateley        0.7m  (watch -)\n```\n\nCould you draft the README scope "
        "section? The parish council heard about it and asked whether it would send flood "
        "warnings to residents, and I need to say clearly that the Environment Agency does "
        "that and we are a handful of people with a notebook.",
    ),
    Turn(
        "assistant",
        "A scope section that draws the line without sounding dismissive:\n\n```\n## Scope\n"
        "rivergauge keeps an in-memory register of the staff gauges the group maintains, "
        "the readings volunteers report and the watch threshold agreed for each site, so "
        "the coordinator can print a weekly summary and see which rivers are high. It is a "
        "notebook for the group's own readings. Official flood warnings come from the "
        "Environment Agency; this tool does not send alerts to anyone and stores nothing "
        "between runs on its own.\n\n## Non-goals\n- public flood warnings or notifications\n"
        "- telemetry or automatic gauges\n- forecasting\n```\n\nAnd a usage block:\n\n"
        "```python\nfrom rivergauge.network import GaugeNetwork\n\nnet = GaugeNetwork()\n"
        'gauge = net.install("Wharfe", "Otley bridge")\nnet.add_reading(gauge["gauge_id"], '
        '1.9)\nprint(gauge["readings"])\n```\n\nThe sentence about the Environment Agency '
        "is the one to quote to the council, and the usage block shows them how little "
        "the tool actually does.",
    ),
    Turn(
        "user",
        "Readings. I'm keeping every reading in a list on the gauge record rather than just "
        "the latest level, because the farms sometimes ask 'is it rising or falling' and "
        "the answer needs the last two or three. But the list grows forever and one of the "
        "other volunteers thinks a list of floats inside a dict is 'not a real data model'. "
        "Is this fine for eleven gauges and fifty-two readings a year each? The texts I get "
        "look like this, for context:\n\n```\nOtley bridge 1.9 (Sun 10am, steady)\nKildwick "
        "2.6 rising fast\nPateley 0.7\n```\n\nso the level is the only number I can rely on; "
        "the rest is commentary I do not want to model. Some weeks a gauge gets no text at "
        "all, so the list is not one-per-week either; it is just the readings we got. The "
        "farms only ever ask about the latest one and the one before it.",
    ),
    Turn(
        "assistant",
        "For that volume a list of floats in the record is exactly right: a year is 52 "
        "numbers per gauge, and 'rising or falling' is `readings[-1] - readings[-2]` with no "
        "machinery. A 'real data model' would earn its keep if you needed timestamps, "
        "observers or corrections, and the texts show you do not. Keep the commentary out "
        "of the data and put the trend in the weekly script:\n\n```python\ndef trend("
        'readings):\n    if len(readings) < 2:\n        return "-"\n    delta = readings[-1] '
        '- readings[-2]\n    return "rising" if delta > 0.05 else "falling" if delta < -0.05 '
        'else "steady"\n```\n\nIf the list ever matters, archive it once a year by writing '
        "the record out as JSON and starting fresh; the shape does not need to change. The "
        "volunteer who wants a real model can be pointed at that archive file.",
    ),
    Turn(
        "user",
        "I wrote the alert tests first because the farms only care about one question. "
        "Are these the right cases?\n\n```python\nfrom rivergauge.alerts "
        "import above_threshold\nfrom rivergauge.model import new_gauge\n\n\ndef test_latest_"
        'at_threshold_is_high():\n    gauge = new_gauge("G1", "Aire", "Kildwick")\n    gauge['
        '"threshold_m"] = 2.5\n    gauge["readings"] = [1.1, 2.5]\n    assert above_'
        "threshold(gauge) is True\n\n\ndef test_below_threshold_is_not_high():\n    gauge = "
        'new_gauge("G1", "Aire", "Kildwick")\n    gauge["threshold_m"] = 2.5\n    gauge['
        '"readings"] = [2.6, 2.4]\n    assert above_threshold(gauge) is False\n\n\ndef test_'
        'no_threshold_is_never_high():\n    gauge = new_gauge("G1", "Nidd", "Pateley")\n    '
        'gauge["readings"] = [3.0]\n    assert above_threshold(gauge) is False\n```',
    ),
    Turn(
        "assistant",
        "Those are the three cases that matter and the second is the important one: only "
        "the latest reading decides, so a river that has dropped is no longer HIGH. The "
        "helper stays a pure function of the record, no network import, which is why the "
        "tests can build a gauge with `new_gauge` and poke the fields. One boundary worth "
        "pinning is 'at threshold counts as high', which your first test does with 2.5 == "
        "2.5; leave a comment on it so nobody later changes `>=` to `>` for tidiness. A "
        "fourth test for a gauge with a threshold but no readings would round it out:\n\n"
        '```python\ndef test_no_readings_is_not_high():\n    gauge = new_gauge("G1", "Nidd", '
        '"Pateley")\n    gauge["threshold_m"] = 1.0\n    assert above_threshold(gauge) is '
        "False\n```\n\nThe second test is the one that matters most: only the latest "
        "reading decides, so a river that has dropped stops showing HIGH.",
    ),
    Turn(
        "user",
        "That fourth test would have caught what I hit on Sunday with a brand-new gauge:\n\n"
        "```\n$ python -m rivergauge.weekly\nTraceback (most recent call last):\n  File "
        '"rivergauge/weekly.py", line 12, in <module>\n    flag = "HIGH" if gauge["readings"]'
        '[-1] >= gauge["threshold_m"] else ""\nIndexError: list index out of range\n```\n\n'
        "The weekly script was doing its own comparison instead of calling the helper, "
        "which is my fault. Should the script ever touch `readings` directly, or should "
        "everything go through helpers in alerts.py? I want a rule I can follow at 7am "
        "with a phone full of texts. The same script also prints the watch level next to "
        "each gauge, and a new gauge has no watch level until we agree one with the farms, "
        "which can take a month of conversations in the pub.",
    ),
    Turn(
        "assistant",
        "Rule: the script formats, helpers decide. Anything that answers a question about a "
        "gauge (is it high, what is the latest level, is it rising) is a function in "
        "`alerts.py` that takes the record and handles the empty case; the script only "
        "prints what they return. Your traceback becomes two helpers and a print:\n\n"
        '```python\ndef latest(gauge):\n    return gauge["readings"][-1] if gauge["readings"]'
        ' else None\n\n\nflag = "HIGH" if above_threshold(gauge) else ""\n```\n\nEvery helper '
        "gets the no-readings and no-threshold tests, and the script never indexes a list "
        "or compares against a threshold it has not checked for None. The 'watch -' column "
        "in your printout is exactly that None rendered as a dash, and the helper that "
        "renders it is the only place that knows the dash exists.",
    ),
    Turn(
        "user",
        "Conventions before the next features. First, return shape: public GaugeNetwork "
        "methods return the gauge record as a plain dict, the same shape `new_gauge` builds "
        "and the weekly script and helpers read. No dataclasses, no tuples. A method that "
        "changes a gauge returns that gauge so the script can print it straight away.",
    ),
    Turn(
        "assistant",
        "Noted: every public GaugeNetwork method returns the plain gauge dict (or None from "
        "a lookup that finds nothing), never a dataclass or tuple. Methods that change a "
        "gauge mutate the stored dict in place and return that same dict, so the weekly "
        "script can print whatever a method returns. Nothing public will return a bare "
        "level or a tuple of fields.",
    ),
    Turn(
        "user",
        "Second, unknown gauge ids: an action on an id that is not in the network raises "
        "KeyError, as `add_reading` does. `find` returns None; actions raise. A reading typed "
        "against a wrong id is a reading lost, and I want to know at once, on Sunday "
        "morning with the texts still on my phone, not in December.",
    ),
    Turn(
        "assistant",
        "Understood: actions on an unknown gauge id raise KeyError, matching `add_reading`, "
        "while `find` stays a None-returning lookup. New methods will index "
        "`self._gauges[gauge_id]` directly so the KeyError names the id, with no separate "
        "existence check in front of it. A mistyped id on a Sunday then fails on the "
        "first reading rather than after the whole batch.",
    ),
    Turn(
        "user",
        "For later: the Environment Agency publishes a CSV of its own gauges and one of the "
        "volunteers wants to show their reading next to ours where sites overlap. That would "
        "be a separate import script reading their CSV, not a change to the record shape. "
        "Their Kildwick gauge is a hundred metres upstream of ours, so the numbers will "
        "never quite agree, which is fine as long as the printout says whose number is "
        "whose.",
    ),
    Turn(
        "assistant",
        "Agreed, that is a script-side join on site name: their number goes in a column of "
        "the printout, not into our record. Nothing in the current shape needs to change for "
        "it, and the small disagreement between the two gauges is worth showing rather "
        "than hiding; the farms trust the board they can see from the lane.",
    ),
    Turn(
        "user",
        "For reference the network tests that exist today are these, plus the alert ones:"
        "\n\n```python\nimport pytest\n\nfrom rivergauge.network import GaugeNetwork\n\n\ndef "
        'test_install_sequential_ids():\n    net = GaugeNetwork()\n    assert net.install("a", '
        '"b")["gauge_id"] == "G1"\n    assert net.install("c", "d")["gauge_id"] == "G2"\n\n\n'
        "def test_add_reading_unknown_raises():\n    with pytest.raises(KeyError):\n        "
        'GaugeNetwork().add_reading("G1", 1.0)\n```',
    ),
    Turn(
        "assistant",
        "Good baseline; I will keep those green and add tests beside each new method. Send "
        "the first request with the current files and I will return the full network "
        "module, existing methods untouched and the new one added at the end of the "
        "class, plus a note on the tests I would add beside it.",
    ),
]

_EVENT = (
    "Small note, nothing to change in the package: the Environment Agency has reordered "
    "the columns in its gauge CSV (site now comes before river). My import script outside "
    "this package handles it, so carry on as before."
)


def build() -> Session:
    return Session(
        id="S37",
        project="rivergauge",
        target_family="missing_record",
        support_family="return_shape",
        lifecycle="stable",
        files=_FILES,
        prefix=_PREFIX,
        states=("raise", "none"),
        state_at=("raise", "raise"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10),
    )
