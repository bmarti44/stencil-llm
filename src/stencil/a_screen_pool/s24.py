# ruff: noqa: E501
"""S24: garden plots — validation (target, reinstatement) x error_surface (support)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '''"""allotments package."""


class AllotmentError(Exception):
    """Raised when the site log cannot be written."""
'''

_MODEL = '''"""Plot and watering records."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Plot:
    plot_id: str
    area_m2: int
    tenant: str | None = None
    months: int = 0


@dataclass(frozen=True)
class Watering:
    plot_id: str
    weekday: str
    litres: int
'''

_SITELOG = '''"""Append-only site log on disk."""


def append_line(path: str, line: str) -> None:
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(line + "\\n")
'''

_PLOTS_HEAD = '''"""Plot table (storage layer) and the public allotment operations."""

from allotments import AllotmentError, sitelog
from allotments.model import Plot, Watering


class PlotTable:
    def __init__(self, log_path: str | None = None) -> None:
        self.log_path = log_path
        self._plots: dict[str, Plot] = {}
        self._waterings: list[Watering] = []

    def _log(self, line: str) -> None:
        if self.log_path is None:
            return
        try:
            sitelog.append_line(self.log_path, line)
        except OSError as exc:
            raise AllotmentError(f"site log write failed: {exc}") from exc

    def insert_plot(self, plot: Plot) -> None:
        if plot.area_m2 <= 0:
            raise ValueError("area must be positive")
        self._plots[plot.plot_id] = plot
        self._log(f"plot {plot.plot_id}")

    def get_plot(self, plot_id: str) -> Plot:
        return self._plots[plot_id]

    def waterings_for(self, plot_id: str) -> list[Watering]:
        return [w for w in self._waterings if w.plot_id == plot_id]
'''

_REGISTER_PLOT = """

def register_plot(table: PlotTable, plot_id: str, area_m2: int) -> Plot:
    plot = Plot(plot_id, area_m2)
    table.insert_plot(plot)
    return plot
"""

_PLOTS = _PLOTS_HEAD + _REGISTER_PLOT

_FILES = {
    "allotments/__init__.py": _INIT,
    "allotments/model.py": _MODEL,
    "allotments/sitelog.py": _SITELOG,
    "allotments/plots.py": _PLOTS,
}


def _insert_watering(state: str) -> str:
    check = (
        '        if watering.litres <= 0:\n            raise ValueError("litres must be positive")\n'
        if state == "storage"
        else ""
    )
    return (
        "\n    def insert_watering(self, watering: Watering) -> None:\n"
        + check
        + "        self._waterings.append(watering)\n"
        '        self._log(f"water {watering.plot_id} {watering.weekday} {watering.litres}")\n'
    )


def _schedule_watering(state: str) -> str:
    check = (
        '    if litres <= 0:\n        raise ValueError("litres must be positive")\n'
        if state == "api"
        else ""
    )
    return (
        "\n\ndef schedule_watering(table: PlotTable, plot_id: str, weekday: str, litres: int) -> Watering:\n"
        "    table.get_plot(plot_id)\n"
        + check
        + "    watering = Watering(plot_id, weekday, litres)\n"
        "    table.insert_watering(watering)\n"
        "    return watering\n"
    )


def _set_tenant(state: str) -> str:
    check = (
        '        if not 1 <= months <= 12:\n            raise ValueError("months must be between 1 and 12")\n'
        if state == "storage"
        else ""
    )
    return (
        "\n    def set_tenant(self, plot_id: str, tenant: str, months: int) -> Plot:\n"
        "        current = self._plots[plot_id]\n"
        + check
        + "        plot = replace(current, tenant=tenant, months=months)\n"
        "        self._plots[plot_id] = plot\n"
        '        self._log(f"let {plot_id} {tenant}")\n'
        "        return plot\n"
    )


def _let_plot(state: str) -> str:
    check = (
        '    if not 1 <= months <= 12:\n        raise ValueError("months must be between 1 and 12")\n'
        if state == "api"
        else ""
    )
    return (
        "\n\ndef let_plot(table: PlotTable, plot_id: str, tenant: str, months: int) -> Plot:\n"
        + check
        + "    return table.set_tenant(plot_id, tenant, months)\n"
    )


def _gold1(state: str) -> str:
    return (
        _PLOTS_HEAD
        + _insert_watering(state)
        + _REGISTER_PLOT
        + _schedule_watering(state)
    )


def _gold2(state: str) -> str:
    # Built on the checkpoint-1 gold under the state then in force (api).
    head = _PLOTS_HEAD.replace(
        "from allotments import AllotmentError, sitelog\n",
        "from dataclasses import replace\n\nfrom allotments import AllotmentError, sitelog\n",
        1,
    )
    return (
        head
        + _insert_watering("api")
        + _set_tenant(state)
        + _REGISTER_PLOT
        + _schedule_watering("api")
        + _let_plot(state)
    )


# ----------------------------------------------------------------- checkpoint 1: schedule_watering

_C1_FUNCTIONAL = {
    "test_watering_functional.py": """import pytest

from allotments.model import Watering
from allotments.plots import PlotTable, register_plot, schedule_watering


def _setup(path=None):
    t = PlotTable(log_path=path)
    p = register_plot(t, "12b", 60)
    return t, p


def test_schedule_watering_stores_and_returns_watering():
    t, p = _setup()
    w = schedule_watering(t, p.plot_id, "tue", 40)
    assert w.plot_id == p.plot_id and w.weekday == "tue" and w.litres == 40
    assert t.waterings_for(p.plot_id) == [w]


def test_schedule_watering_appends_in_order():
    t, p = _setup()
    a = schedule_watering(t, p.plot_id, "tue", 40)
    b = schedule_watering(t, p.plot_id, "fri", 25)
    assert t.waterings_for(p.plot_id) == [a, b]


def test_schedule_watering_logs_the_line(tmp_path):
    t, p = _setup(str(tmp_path / "site.log"))
    schedule_watering(t, p.plot_id, "sat", 30)
    lines = (tmp_path / "site.log").read_text().splitlines()
    assert lines == ["plot 12b", "water 12b sat 30"]


def test_schedule_unknown_plot_raises_keyerror():
    t, _ = _setup()
    with pytest.raises(KeyError):
        schedule_watering(t, "99z", "tue", 10)


def test_nonpositive_litres_raises_and_stores_nothing():
    t, p = _setup()
    for bad in (0, -5):
        with pytest.raises(ValueError):
            schedule_watering(t, p.plot_id, "tue", bad)
    assert t.waterings_for(p.plot_id) == []


def test_table_has_insert_watering():
    t, p = _setup()
    t.insert_watering(Watering(p.plot_id, "mon", 15))
    assert [w.litres for w in t.waterings_for(p.plot_id)] == [15]
"""
}

_C1_REGRESSION = {
    "test_watering_regression.py": """import pytest

from allotments import AllotmentError
from allotments.plots import PlotTable, register_plot


def test_register_plot_unchanged(tmp_path):
    t = PlotTable(log_path=str(tmp_path / "site.log"))
    p = register_plot(t, "12b", 60)
    assert t.get_plot("12b") is p and p.tenant is None and p.months == 0
    assert (tmp_path / "site.log").read_text() == "plot 12b\\n"
    with pytest.raises(ValueError):
        register_plot(t, "13a", 0)
    with pytest.raises(KeyError):
        t.get_plot("99z")
    assert t.waterings_for("12b") == []
    t.log_path = str(tmp_path)
    with pytest.raises(AllotmentError):
        register_plot(t, "14c", 30)
"""
}

_C1_CONTRACT = {
    "api": {
        "test_watering_validation.py": """import pytest

from allotments.model import Watering
from allotments.plots import PlotTable, register_plot, schedule_watering


def test_public_function_rejects_nonpositive_litres():
    t = PlotTable()
    p = register_plot(t, "12b", 60)
    for bad in (0, -5):
        with pytest.raises(ValueError):
            schedule_watering(t, p.plot_id, "tue", bad)
    assert t.waterings_for(p.plot_id) == []


def test_table_trusts_callers_on_litres():
    t = PlotTable()
    p = register_plot(t, "12b", 60)
    t.insert_watering(Watering(p.plot_id, "tue", 0))
    assert [w.litres for w in t.waterings_for(p.plot_id)] == [0]
"""
    },
    "storage": {
        "test_watering_validation.py": """import pytest

from allotments.model import Watering
from allotments.plots import PlotTable, register_plot, schedule_watering


def test_table_rejects_nonpositive_litres():
    t = PlotTable()
    p = register_plot(t, "12b", 60)
    for bad in (0, -5):
        with pytest.raises(ValueError):
            t.insert_watering(Watering(p.plot_id, "tue", bad))
    assert t.waterings_for(p.plot_id) == []


def test_public_function_passes_invalid_litres_through(monkeypatch):
    t = PlotTable()
    p = register_plot(t, "12b", 60)
    seen = []
    real = t.insert_watering

    def spy(watering):
        seen.append(watering.litres)
        return real(watering)

    monkeypatch.setattr(t, "insert_watering", spy)
    with pytest.raises(ValueError):
        schedule_watering(t, p.plot_id, "tue", -5)
    assert seen == [-5]
"""
    },
}

_C1_SUPPORT = {
    "test_watering_errors.py": """import pytest

from allotments import AllotmentError
from allotments.plots import PlotTable, register_plot, schedule_watering


def test_site_log_failure_is_wrapped(tmp_path):
    t = PlotTable()
    p = register_plot(t, "12b", 60)
    t.log_path = str(tmp_path)  # a directory: appending raises OSError
    with pytest.raises(AllotmentError) as ei:
        schedule_watering(t, p.plot_id, "tue", 20)
    assert not isinstance(ei.value, OSError)
    assert isinstance(ei.value.__cause__, OSError)
"""
}

_REQ1 = Request(
    text=(
        "Add watering schedules. Give PlotTable an `insert_watering(watering)` method that "
        "appends a Watering to the list and logs the line `water <plot_id> <weekday> "
        "<litres>`, and add a public function `schedule_watering(table, plot_id, weekday, "
        "litres)` that checks the plot exists (an unknown id raises KeyError), stores the "
        "watering and returns it. Litres of zero or less is invalid and must raise "
        "ValueError."
    ),
    target="allotments/plots.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"api": _gold1("api"), "storage": _gold1("storage")},
)

# ----------------------------------------------------------------- checkpoint 2: let_plot

_C2_FUNCTIONAL = {
    "test_tenancy_functional.py": """import pytest

from allotments.plots import PlotTable, let_plot, register_plot


def _setup(path=None):
    t = PlotTable(log_path=path)
    p = register_plot(t, "12b", 60)
    return t, p


def test_let_plot_sets_tenant_and_returns_plot():
    t, p = _setup()
    out = let_plot(t, p.plot_id, "rosa", 6)
    assert out.tenant == "rosa" and out.months == 6
    assert out.plot_id == p.plot_id and out.area_m2 == 60
    assert t.get_plot(p.plot_id).tenant == "rosa"


def test_let_plot_logs_the_line(tmp_path):
    t, p = _setup(str(tmp_path / "site.log"))
    let_plot(t, p.plot_id, "rosa", 12)
    lines = (tmp_path / "site.log").read_text().splitlines()
    assert lines[-1] == "let 12b rosa"


def test_let_unknown_plot_raises_keyerror():
    t, _ = _setup()
    with pytest.raises(KeyError):
        let_plot(t, "99z", "rosa", 6)


def test_months_out_of_range_raises_and_changes_nothing():
    t, p = _setup()
    for bad in (0, 13, -1):
        with pytest.raises(ValueError):
            let_plot(t, p.plot_id, "rosa", bad)
    assert t.get_plot(p.plot_id).tenant is None


def test_table_has_set_tenant():
    t, p = _setup()
    out = t.set_tenant(p.plot_id, "kim", 3)
    assert out.tenant == "kim" and t.get_plot(p.plot_id).months == 3
"""
}

_C2_REGRESSION = {
    "test_tenancy_regression.py": """import pytest

from allotments import AllotmentError
from allotments.plots import PlotTable, register_plot, schedule_watering


def test_plots_and_waterings_unchanged(tmp_path):
    t = PlotTable(log_path=str(tmp_path / "site.log"))
    p = register_plot(t, "12b", 60)
    w = schedule_watering(t, p.plot_id, "tue", 40)
    assert t.waterings_for(p.plot_id) == [w]
    assert (tmp_path / "site.log").read_text().splitlines() == ["plot 12b", "water 12b tue 40"]
    with pytest.raises(ValueError):
        schedule_watering(t, p.plot_id, "tue", 0)
    with pytest.raises(ValueError):
        register_plot(t, "13a", -1)
    with pytest.raises(KeyError):
        schedule_watering(t, "99z", "tue", 5)
    t.log_path = str(tmp_path)
    with pytest.raises(AllotmentError):
        schedule_watering(t, p.plot_id, "fri", 5)
"""
}

_C2_CONTRACT = {
    "api": {
        "test_tenancy_validation.py": """import pytest

from allotments.plots import PlotTable, let_plot, register_plot


def test_public_function_rejects_months_out_of_range():
    t = PlotTable()
    p = register_plot(t, "12b", 60)
    for bad in (0, 13):
        with pytest.raises(ValueError):
            let_plot(t, p.plot_id, "rosa", bad)
    assert t.get_plot(p.plot_id).tenant is None


def test_table_trusts_callers_on_months():
    t = PlotTable()
    p = register_plot(t, "12b", 60)
    out = t.set_tenant(p.plot_id, "rosa", 0)
    assert out.months == 0 and t.get_plot(p.plot_id).tenant == "rosa"
"""
    },
    "storage": {
        "test_tenancy_validation.py": """import pytest

from allotments.plots import PlotTable, let_plot, register_plot


def test_table_rejects_months_out_of_range():
    t = PlotTable()
    p = register_plot(t, "12b", 60)
    for bad in (0, 13):
        with pytest.raises(ValueError):
            t.set_tenant(p.plot_id, "rosa", bad)
    assert t.get_plot(p.plot_id).tenant is None


def test_public_function_passes_invalid_months_through(monkeypatch):
    t = PlotTable()
    p = register_plot(t, "12b", 60)
    seen = []
    real = t.set_tenant

    def spy(plot_id, tenant, months):
        seen.append(months)
        return real(plot_id, tenant, months)

    monkeypatch.setattr(t, "set_tenant", spy)
    with pytest.raises(ValueError):
        let_plot(t, p.plot_id, "rosa", 13)
    assert seen == [13]
"""
    },
}

_C2_SUPPORT = {
    "test_tenancy_errors.py": """import pytest

from allotments import AllotmentError
from allotments.plots import PlotTable, let_plot, register_plot


def test_site_log_failure_is_wrapped(tmp_path):
    t = PlotTable()
    p = register_plot(t, "12b", 60)
    t.log_path = str(tmp_path)  # a directory: appending raises OSError
    with pytest.raises(AllotmentError) as ei:
        let_plot(t, p.plot_id, "rosa", 6)
    assert not isinstance(ei.value, OSError)
    assert isinstance(ei.value.__cause__, OSError)
"""
}

_REQ2 = Request(
    text=(
        "Add tenancies. Give PlotTable a `set_tenant(plot_id, tenant, months)` method that "
        "replaces the stored plot with a copy carrying that tenant and months, logs the "
        "line `let <plot_id> <tenant>` and returns the updated plot (an unknown id raises "
        "KeyError), and add a public function `let_plot(table, plot_id, tenant, months)` "
        "that applies it and returns the updated Plot. Months outside 1 to 12 inclusive "
        "are invalid and must raise ValueError."
    ),
    target="allotments/plots.py",
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
        "I'm secretary of a forty-plot allotment site and the records are a ring binder "
        "plus a shared spreadsheet that two committee members edit differently. I want a "
        "small Python package, `allotments`, that keeps plots and their tenancies in memory "
        "and appends every change to a site log file, so that when a plot-holder says they "
        "never agreed to give up 12b, we can read the log. A monthly script prints the "
        "rent list:\n\n```\ncd /srv/site && python -m allotments.rent --log /srv/site/"
        "site.log > /srv/site/rent-2026-10.txt\n```\n\nForty plots, a dozen changes a "
        "season. No database, no website, no online payments; the treasurer takes cheques. "
        "Could you draft the README scope so the committee stops asking for a members' "
        "portal? I've been asked about it at three consecutive AGMs and I want it in "
        "writing that this is not that. The two committee members who edit the spreadsheet "
        "are both perfectly capable; the problem is the spreadsheet, not the people, so the "
        "tool has to be simpler than the spreadsheet or they will not use it.",
    ),
    Turn(
        "assistant",
        "Say what it is in two sentences and what it is not in a list:\n\n```\n## Scope\n"
        "allotments keeps the site's plots, tenancies and watering schedules in memory for "
        "one process and appends every change to a plain-text site log. It is a library "
        "for small committee scripts, not a members' portal.\n\n## Non-goals\n- online "
        "applications or waiting lists\n- rent collection or payments\n- a website or "
        "member logins\n- multi-user editing\n```\n\n```python\nfrom allotments.plots "
        'import PlotTable, register_plot\n\ntable = PlotTable(log_path="/srv/site/site.'
        'log")\nplot = register_plot(table, "12b", 60)\nprint(plot)\n```\n\nThe portal '
        "request is best answered with the rent list and the log: both are plain text "
        "anyone can email, and neither needs a login. Simpler than the spreadsheet means "
        "one command that prints the rent list and one log file they can open in Notepad; "
        "resist the temptation to add a menu. The rent script can carry the site's rate as "
        "a constant at the top of the file so nobody has to pass it.",
    ),
    Turn(
        "user",
        "Plot ids are the painted numbers on the posts, like `12b` and `7`, so they are "
        "given, not minted. The site log is one short line per change, like `plot 12b` or "
        "`let 12b rosa`, written inside `PlotTable` through a `_log` helper. This happened "
        "when the log was "
        "on a USB stick that had been pulled out:\n\n```\nTraceback (most recent call "
        'last):\n  File "/srv/site/allotments/rent.py", line 19, in <module>\n    '
        'register_plot(table, pid, area)\n  File "/srv/site/allotments/plots.py", line 30, '
        'in register_plot\n    table.insert_plot(plot)\n  File "/srv/site/allotments/plots.'
        'py", line 20, in insert_plot\n    self._log(f"plot {plot.plot_id}")\n  File '
        '"/srv/site/allotments/sitelog.py", line 5, in append_line\n    with open(path, '
        '"a", encoding="utf-8") as fh:\nFileNotFoundError: [Errno 2] No such file or '
        "directory: '/media/usb/site.log'\n```\n\nThe committee member running it was "
        "stuck.",
    ),
    Turn(
        "assistant",
        "Two things. Keep the write inside the table: every mutation passes through a table "
        "method, so the log cannot miss one, and tests point `log_path` at a temp file. "
        "And give the package one exception so the script has one thing to catch and one "
        "message to print. `AllotmentError` in `allotments/__init__.py`, and `_log` "
        "translates at the file boundary:\n\n```python\ntry:\n    sitelog.append_line("
        'self.log_path, line)\nexcept OSError as exc:\n    raise AllotmentError(f"site log '
        'write failed: {exc}") from exc\n```\n\nThe `from exc` keeps the FileNotFoundError '
        "as `__cause__`, so the USB path still shows in a full traceback, but `rent.py` "
        "only needs `except AllotmentError as exc: sys.exit(str(exc))` to print something a "
        "committee member can act on. Every table method that calls `_log` inherits the "
        "translation; a new method does not have to wrap anything itself. Mention "
        "`AllotmentError` in the README usage block so whoever writes the next script "
        "knows it exists and what to catch.",
    ),
    Turn(
        "user",
        "The rent list is one line per let plot. Test draft first, as usual:\n\n```python\n"
        "from allotments.model import Plot\nfrom allotments.rent import rent_line\n\n\ndef "
        'test_rent_line_for_let_plot():\n    p = Plot("12b", 60, tenant="rosa", months=12)'
        '\n    assert rent_line(p, pence_per_m2=25) == "12b rosa 12 months 15.00"\n\n\ndef '
        'test_rent_line_for_vacant_plot():\n    p = Plot("7", 40)\n    assert rent_line(p, '
        'pence_per_m2=25) == "7 vacant"\n```\n\nRent is area times a rate, pro-rated by '
        "months out of twelve; the rate is 25p per square metre per year at the moment, set "
        "at the AGM, so it has to be easy to change once a year without touching the "
        "arithmetic. Should `rent_line` live in `model.py` next to Plot, or in its own "
        "module? It feels like presentation, but it also feels like the one calculation "
        "the whole package exists to do.",
    ),
    Turn(
        "assistant",
        "Own module, `rent.py`, depending only on `model.py`. It is both a calculation and "
        "a rendering, and splitting it lets you test the number separately from the "
        "string:\n\n```python\ndef rent_pence(plot: Plot, pence_per_m2: int) -> int:\n    "
        "return plot.area_m2 * pence_per_m2 * plot.months // 12\n\n\ndef rent_line(plot: "
        'Plot, pence_per_m2: int) -> str:\n    if plot.tenant is None:\n        return f"'
        '{plot.plot_id} vacant"\n    pounds = rent_pence(plot, pence_per_m2) / 100\n    '
        'return f"{plot.plot_id} {plot.tenant} {plot.months} months {pounds:.2f}"\n```\n\n'
        "Integer pence until the last step avoids float drift in the total; the committee "
        "will notice a penny out. Keep `pence_per_m2` as an argument all the way down so "
        "the AGM change is one constant in the rent script; the calculation never needs "
        "to know what year it is.",
    ),
    Turn(
        "user",
        "Question on lookups: `get_plot` raises KeyError on an unknown id. The rent script "
        "reads ids from a file that occasionally contains a plot that was merged into its "
        "neighbour years ago. The id file, `plots.txt`, is one id per line and lives in the "
        "same folder as the log; when plots were merged someone struck the old number "
        "through on paper but the text file was never updated, which is how `14c` is "
        "still in there even though it has been part of `14b` since 2021. I could clean "
        "the file up, but there will be another merge eventually, so I would rather the "
        "code have a policy than rely on the file being right, and the same policy should "
        "apply to any future lookup so nobody has to ask again. Should `get_plot` return "
        "None instead so the script can skip it, or is KeyError right and the script "
        "should catch it? I'd like one rule written down rather than a per-method "
        "judgement.",
    ),
    Turn(
        "assistant",
        "KeyError is right. A merged plot that something still references is exactly the "
        "kind of stale record you want the rent list to shout about, not skip silently. "
        "Rule: `get_*` by id raises KeyError; list-style queries like `waterings_for` "
        "return an empty list; actions on an unknown id raise KeyError because the caller "
        "is confused. The rent script can tolerate it explicitly:\n\n```python\ntry:\n    "
        'plot = table.get_plot(pid)\nexcept KeyError:\n    print(f"{pid} unknown, check '
        'the id file")\n    continue\n```\n\nThat keeps the tolerance in the one script '
        "that needs it and leaves the table honest. As a nicety, the rent script could "
        "also print the ids from `plots.txt` that the table does not know at the end of "
        "the run, `unknown: 14c`, so the file gets cleaned up the first time someone reads "
        "the output; but that is a script concern, and the table should never learn about "
        "merges. The same rule covers the watering list: `waterings_for` on an unknown plot "
        "returns an empty list, because a schedule query finding nothing is a normal "
        "answer, not an error.",
    ),
    Turn(
        "user",
        "Two conventions to fix before the real features. First, errors: any file or I/O "
        "failure underneath a public function in `allotments.plots` surfaces as "
        "`AllotmentError`, raised `from` the original OSError, never as a raw OSError. "
        "That covers everything the table does, existing and new.",
    ),
    Turn(
        "assistant",
        "Noted: site-log I/O failures are wrapped in `AllotmentError` with the original "
        "OSError chained as the cause, for every table operation. New methods write "
        "through `_log` and inherit the wrapping; no raw OSError escapes.",
    ),
    Turn(
        "user",
        "Second, validation: it lives in the table. `PlotTable` methods check their own "
        "inputs and raise ValueError, the way `insert_plot` rejects a non-positive area "
        "today. Public functions build the record and hand it straight to the table with "
        "no pre-check of their own.",
    ),
    Turn(
        "assistant",
        "Understood: the table defends itself. New PlotTable methods validate and raise "
        "ValueError, and public functions in `plots.py` pass arguments through without a "
        "separate check, matching `insert_plot` and `register_plot` as they are now.",
    ),
    Turn(
        "user",
        "Actually, having talked to the person writing the spreadsheet importer, I want to "
        "flip that. New rule: validation lives in the public functions, which raise "
        "ValueError before calling the table, and new PlotTable methods trust their "
        "callers and do not validate. `insert_plot` and `register_plot` stay exactly as "
        "they are; only new code follows this.",
    ),
    Turn(
        "assistant",
        "Understood, reversed for new code: the public functions validate up front and "
        "raise ValueError, and new PlotTable methods store and log only, with no checks. "
        "Existing functions are left untouched.",
    ),
    Turn(
        "user",
        "For the record, the only test that exists today is:\n\n```python\nfrom "
        "allotments.plots import PlotTable, register_plot\n\n\ndef "
        'test_register_plot_keeps_id():\n    assert register_plot(PlotTable(), "12b", 60).'
        'plot_id == "12b"\n```\n\nI will paste the current files with each request.',
    ),
    Turn(
        "assistant",
        "Ready. Send the first feature and I will return the complete `plots.py`.",
    ),
]

_EVENT = (
    "Scrap the flip; the importer author has gone with a different approach and I prefer "
    "the original rule. For anything new from here on, validation lives in the table: new "
    "PlotTable methods check their own inputs and raise ValueError, and new public "
    "functions pass their arguments straight through with no pre-check. Whatever is "
    "already written stays as it is."
)


def build() -> Session:
    return Session(
        id="S24",
        project="allotments",
        target_family="validation",
        support_family="error_surface",
        lifecycle="reinstatement",
        files=_FILES,
        prefix=_PREFIX,
        states=("storage", "api"),
        state_at=("api", "storage"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10, 12),
    )
