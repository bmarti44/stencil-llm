# ruff: noqa: E501
"""S46: carpool — missing_record (target, replacement) x logging (support, warn)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""ridepool package."""\n'

_MODEL = '''"""Carpool ride records."""

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Ride:
    ride_id: str
    driver: str
    seats: int
    riders: tuple[str, ...] = ()
    status: str = "open"

    def with_status(self, status: str) -> "Ride":
        return replace(self, status=status)
'''

_STORE = '''"""In-memory carpool board."""

import logging

from ridepool.model import Ride

log = logging.getLogger(__name__)


class RideStore:
    def __init__(self) -> None:
        self._rides: dict[str, Ride] = {}
        self._counter = 0

    def offer_ride(self, driver: str, seats: int) -> Ride:
        self._counter += 1
        ride = Ride(ride_id=f"R{self._counter}", driver=driver, seats=seats)
        self._rides[ride.ride_id] = ride
        return ride

    def find(self, ride_id: str) -> Ride | None:
        return self._rides.get(ride_id)

    def count(self) -> int:
        return len(self._rides)

    def cancel_ride(self, ride_id: str) -> Ride | None:
        ride = self._rides.get(ride_id)
        if ride is None:
            return None
        cancelled = ride.with_status("cancelled")
        self._rides[ride_id] = cancelled
        return cancelled
'''

_FILES = {
    "ridepool/__init__.py": _INIT,
    "ridepool/model.py": _MODEL,
    "ridepool/store.py": _STORE,
}

# ----------------------------------------------------------------- checkpoint 1: join

_C1_HELPER = """from ridepool.store import RideStore


def _join(store):
    fn = getattr(store, "join_ride", None)
    assert fn is not None, "no join_ride method found"
    return fn
"""

_C1_FUNCTIONAL = {
    "test_join_functional.py": _C1_HELPER
    + """

def test_join_adds_rider():
    s = RideStore()
    r = s.offer_ride("nadia", 3)
    out = _join(s)(r.ride_id, "omar")
    assert out.riders == ("omar",)
    assert s.find(r.ride_id).riders == ("omar",)


def test_join_appends_in_order_and_keeps_fields():
    s = RideStore()
    r = s.offer_ride("nadia", 3)
    _join(s)(r.ride_id, "omar")
    out = _join(s)(r.ride_id, "lea")
    assert out.riders == ("omar", "lea")
    assert out.ride_id == r.ride_id and out.driver == "nadia" and out.seats == 3


def test_join_twice_does_not_duplicate():
    s = RideStore()
    r = s.offer_ride("nadia", 3)
    _join(s)(r.ride_id, "omar")
    out = _join(s)(r.ride_id, "omar")
    assert out.riders == ("omar",)
    assert s.find(r.ride_id).riders == ("omar",)
"""
}

_C1_REGRESSION = {
    "test_join_regression.py": """from ridepool.store import RideStore


def test_offer_find_count_cancel_unchanged():
    s = RideStore()
    r = s.offer_ride("nadia", 3)
    assert r.ride_id == "R1" and r.status == "open" and r.riders == ()
    assert s.find("R1") is r and s.find("nope") is None
    assert s.count() == 1
    assert s.cancel_ride("R1").status == "cancelled"
    assert s.cancel_ride("R9") is None
"""
}

_C1_CONTRACT = {
    "none": {
        "test_join_missing.py": _C1_HELPER
        + """

def test_join_unknown_returns_none_and_changes_nothing():
    s = RideStore()
    r = s.offer_ride("nadia", 3)
    assert _join(s)("R404", "omar") is None
    assert s.count() == 1 and s.find(r.ride_id) == r
"""
    },
    "raise": {
        "test_join_missing.py": _C1_HELPER
        + """
import pytest


def test_join_unknown_raises_keyerror():
    s = RideStore()
    s.offer_ride("nadia", 3)
    with pytest.raises(KeyError):
        _join(s)("R404", "omar")
    assert s.count() == 1
"""
    },
}

_C1_SUPPORT = {
    "test_join_logging.py": _C1_HELPER
    + """
import logging


def test_first_join_emits_no_log(caplog):
    s = RideStore()
    r = s.offer_ride("nadia", 3)
    with caplog.at_level(logging.DEBUG):
        _join(s)(r.ride_id, "omar")
    assert len(caplog.records) == 0


def test_repeat_join_emits_exactly_one_warning(caplog):
    s = RideStore()
    r = s.offer_ride("nadia", 3)
    _join(s)(r.ride_id, "omar")
    with caplog.at_level(logging.DEBUG):
        _join(s)(r.ride_id, "omar")
    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == logging.WARNING
"""
}


def _lookup(state: str) -> str:
    if state == "none":
        return "        ride = self._rides.get(ride_id)\n        if ride is None:\n            return None\n"
    return "        ride = self._rides[ride_id]\n"


def _gold1(state: str) -> str:
    return (
        _STORE.rstrip("\n")
        + f"""

    def join_ride(self, ride_id: str, rider: str) -> Ride | None:
{_lookup(state)}        if rider in ride.riders:
            log.warning("rider %s is already on ride %s", rider, ride_id)
            return ride
        joined = replace(ride, riders=ride.riders + (rider,))
        self._rides[ride_id] = joined
        return joined
"""
    )


def _gold1_full(state: str) -> str:
    return _gold1(state).replace(
        "from ridepool.model import Ride\n",
        "from dataclasses import replace\n\nfrom ridepool.model import Ride\n",
        1,
    )


_REQ1 = Request(
    text=(
        "Add a public method join_ride(ride_id, rider) on RideStore: it appends the rider "
        "to the ride's riders tuple (keeping order), stores the updated ride and returns "
        "it. A rider who is already on that ride is the notable case: the riders tuple "
        "stays as it is and the ride is returned; handle it the way we agreed."
    ),
    target="ridepool/store.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"none": _gold1_full("none"), "raise": _gold1_full("raise")},
)

# ----------------------------------------------------------------- checkpoint 2: leave

_C2_HELPER = """from ridepool.store import RideStore


def _leave(store):
    fn = getattr(store, "leave_ride", None)
    assert fn is not None, "no leave_ride method found"
    return fn
"""

_C2_FUNCTIONAL = {
    "test_leave_functional.py": _C2_HELPER
    + """

def test_leave_removes_rider():
    s = RideStore()
    r = s.offer_ride("nadia", 3)
    s.join_ride(r.ride_id, "omar")
    s.join_ride(r.ride_id, "lea")
    out = _leave(s)(r.ride_id, "omar")
    assert out.riders == ("lea",)
    assert s.find(r.ride_id).riders == ("lea",)


def test_leave_keeps_other_fields():
    s = RideStore()
    r = s.offer_ride("nadia", 2)
    s.join_ride(r.ride_id, "omar")
    out = _leave(s)(r.ride_id, "omar")
    assert out.ride_id == r.ride_id and out.driver == "nadia"
    assert out.seats == 2 and out.status == "open" and out.riders == ()


def test_leave_rider_not_on_ride_leaves_riders_unchanged():
    s = RideStore()
    r = s.offer_ride("nadia", 3)
    s.join_ride(r.ride_id, "lea")
    out = _leave(s)(r.ride_id, "omar")
    assert out.riders == ("lea",) and s.find(r.ride_id).riders == ("lea",)
"""
}

_C2_REGRESSION = {
    "test_leave_regression.py": """from ridepool.store import RideStore


def test_offer_find_cancel_join_unchanged():
    s = RideStore()
    r = s.offer_ride("nadia", 3)
    assert s.find("R1") is r and s.count() == 1
    assert s.join_ride("R1", "omar").riders == ("omar",)
    assert s.cancel_ride("R1").status == "cancelled"
    assert s.cancel_ride("R9") is None
"""
}

_C2_CONTRACT = {
    "none": {
        "test_leave_missing.py": _C2_HELPER
        + """

def test_leave_unknown_returns_none_and_changes_nothing():
    s = RideStore()
    r = s.offer_ride("nadia", 3)
    assert _leave(s)("R404", "omar") is None
    assert s.count() == 1 and s.find(r.ride_id) == r
"""
    },
    "raise": {
        "test_leave_missing.py": _C2_HELPER
        + """
import pytest


def test_leave_unknown_raises_keyerror():
    s = RideStore()
    s.offer_ride("nadia", 3)
    with pytest.raises(KeyError):
        _leave(s)("R404", "omar")
    assert s.count() == 1
"""
    },
}

_C2_SUPPORT = {
    "test_leave_logging.py": _C2_HELPER
    + """
import logging


def test_leave_present_rider_emits_no_log(caplog):
    s = RideStore()
    r = s.offer_ride("nadia", 3)
    s.join_ride(r.ride_id, "omar")
    with caplog.at_level(logging.DEBUG):
        _leave(s)(r.ride_id, "omar")
    assert len(caplog.records) == 0


def test_leave_absent_rider_emits_exactly_one_warning(caplog):
    s = RideStore()
    r = s.offer_ride("nadia", 3)
    with caplog.at_level(logging.DEBUG):
        _leave(s)(r.ride_id, "omar")
    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == logging.WARNING
"""
}


def _gold2(state: str) -> str:
    # Built on the checkpoint-1 gold under the state then in force (none).
    return (
        _gold1_full("none").rstrip("\n")
        + f"""

    def leave_ride(self, ride_id: str, rider: str) -> Ride | None:
{_lookup(state)}        if rider not in ride.riders:
            log.warning("rider %s is not on ride %s", rider, ride_id)
            return ride
        left = replace(ride, riders=tuple(r for r in ride.riders if r != rider))
        self._rides[ride_id] = left
        return left
"""
    )


_REQ2 = Request(
    text=(
        "Add a public method leave_ride(ride_id, rider) on RideStore: it removes the rider "
        "from the ride's riders tuple (keeping the order of the others), stores the updated "
        "ride and returns it. A rider who is not on that ride is the notable case: the "
        "riders tuple stays as it is and the ride is returned; handle it the way we agreed."
    ),
    target="ridepool/store.py",
    functional_tests=_C2_FUNCTIONAL,
    regression_tests=_C2_REGRESSION,
    contract_tests=_C2_CONTRACT,
    support_tests=_C2_SUPPORT,
    gold={"none": _gold2("none"), "raise": _gold2("raise")},
)

# ----------------------------------------------------------------- prefix (16 turns)

_PREFIX = [
    Turn(
        "user",
        "Our office has an informal carpool that lives in a group chat and it is a mess: "
        "people forget who offered a seat, drivers leave with empty cars, and every Friday "
        "someone asks 'is anyone going to the north site on Monday?'. I want a tiny Python "
        "package, ridepool, with an in-memory RideStore of Ride records and a script that "
        "posts the day's board to the chat each morning. No database, no auth, no app. The "
        "poster is one cron line:\n\n```\n30 7 * * 1-5 cd /srv/ridepool && python -m "
        "ridepool.board --post >> /var/log/ridepool/board.log 2>&1\n```\n\nSeats are small "
        "integers, riders are just names from the chat, and a ride is either open or "
        "cancelled. Can you draft a README scope section so nobody asks for maps, "
        "payments or push notifications? There are about thirty of us and maybe six rides "
        "a day, so this can be as simple as it sounds; the value is that the board is "
        "right, not that it is fast.",
    ),
    Turn(
        "assistant",
        "A scope section plus a non-goals list settles the feature requests early:\n\n```\n"
        "## Scope\nridepool is an in-memory carpool board for one process. It keeps Ride "
        "records (driver, seats, riders, status) in a RideStore, has no persistence and no "
        "concurrency guarantees, and is driven by the morning board script and by tests. "
        "It knows who offered a ride and who is on it; nothing else.\n\n## Non-goals\n- "
        "maps, routing or distance\n- payments or cost splitting\n- notifications\n- "
        "accounts or sign-in\n```\n\nA short usage block under it shows the API's shape:"
        "\n\n```python\nfrom ridepool.store import RideStore\n\nstore = RideStore()\nride = "
        'store.offer_ride("nadia", seats=3)\nprint(store.find(ride.ride_id))\n```\n\nThat is '
        "enough for the chat crowd; the board script's flags can be the rest of the README.",
    ),
    Turn(
        "user",
        "Ride ids are R1, R2, ... from a counter. One colleague wants the id to be the "
        "driver's initials plus the date, like NB-0915, so it reads nicely in the chat "
        "post. I see the appeal, but two people share initials and a driver sometimes "
        "offers two rides a day. The morning post currently looks like:\n\n```\nRide board, "
        "Mon 2026-09-14\nR41  nadia   3 seats  riders: omar, lea       open\nR42  tomasz  "
        "1 seat   riders: -                cancelled\nR43  priya   2 seats  riders: ben       "
        "     open\n```\n\nIs there a real downside to keeping the counter and just "
        "printing the driver next to it? I want to avoid regretting the id format later "
        "when someone asks for a weekly summary. The chat post is the only place ids are "
        "seen, and people do copy them from old posts, so short beats clever.",
    ),
    Turn(
        "assistant",
        "Keep the counter. An id must be unique and stable; initials-plus-date is neither, "
        "as you have already found with shared initials and double rides. The board already "
        "prints the driver next to the id, which gives readers the context they want "
        "without encoding it in the key. Only `offer_ride` mints ids, so changing the "
        "scheme later is a one-method edit:\n\n```python\ndef _next_id(self) -> str:\n    "
        'self._counter += 1\n    return f"R{self._counter}"\n```\n\nFor a weekly summary the '
        "date is a field, not part of the id; add `offered_on` to Ride when the summary "
        "lands. And never reuse a number after a cancel, since chat history refers to it; if "
        "persistence ever arrives, persist the counter with the rides so a restart does not "
        "mint R1 again and confuse everyone who kept last week's post.",
    ),
    Turn(
        "user",
        "The board needs a one-line renderer per ride, roughly `R41 nadia 3 seats riders: "
        "omar, lea` with the status appended when it isn't open. Method on Ride or a "
        "function in the store module? I lean function, since Ride is a record and should "
        "not know how it is printed, but a method is easier to find. Test draft:\n\n"
        "```python\nfrom ridepool.model import Ride\n\n\ndef test_line_open():\n    r = "
        'Ride(ride_id="R41", driver="nadia", seats=3, riders=("omar", "lea"))\n    assert '
        'line(r) == "R41 nadia 3 seats riders: omar, lea"\n\n\ndef test_line_cancelled_no_'
        'riders():\n    r = Ride(ride_id="R42", driver="tomasz", seats=1, status='
        '"cancelled")\n    assert line(r) == "R42 tomasz 1 seat riders: - cancelled"\n```'
        "\n\nColumn padding can stay in the script; I only need the raw line here.",
    ),
    Turn(
        "assistant",
        "Free function next to the model so the script and tests share it and Ride stays "
        'a plain record:\n\n```python\ndef line(ride: Ride) -> str:\n    seats = "seat" if '
        'ride.seats == 1 else "seats"\n    who = ", ".join(ride.riders) if ride.riders else '
        '"-"\n    tail = "" if ride.status == "open" else f" {ride.status}"\n    return '
        'f"{ride.ride_id} {ride.driver} {ride.seats} {seats} riders: {who}{tail}"\n```\n\n'
        "Both drafts pass as written. Padding stays in the board script, and a `__str__` "
        "on Ride would tie the record to one rendering, which you would regret the first "
        "time the chat wants a different format. Add a third test for an open ride with no "
        "riders yet, since that is the line the board shows most often, and one for a full "
        "ride once that status exists.",
    ),
    Turn(
        "user",
        "Someone typed a ride id from last week's post and got this:\n\n```\n>>> "
        'store.find("R37").riders\nTraceback (most recent call last):\n  File "<stdin>", '
        "line 1, in <module>\nAttributeError: 'NoneType' object has no attribute 'riders'\n"
        "```\n\nI'm happy with `find` returning None, that is the standard lookup shape. "
        "But the store is about to grow methods that act on a ride (join, leave, mark "
        "full) and I want one written rule for what an action does with an unknown id, "
        "instead of every patch picking its own. The board script's loop is currently:\n\n"
        "```python\nfor ride_id in cancellations:\n    store.cancel_ride(ride_id)\nfor ride "
        "in open_rides(store):\n    post(line(ride))\n```\n\nWhat are the options and which "
        "fits a chat where ids get mistyped daily? Whatever we pick, the board must still "
        "post every morning even if one id in the cancellations list is garbage.",
    ),
    Turn(
        "assistant",
        "Two coherent options. (1) Actions return None on an unknown id and change "
        "nothing, matching `find`; the script checks the result and keeps going, at the "
        "cost of silent no-ops when a check is forgotten. (2) Actions raise KeyError, "
        "which surfaces the typo at once but makes the script wrap every action in "
        "try/except. The existing `cancel_ride` already returns None, and for daily typos "
        "from chat the gentle style keeps the board posting; the loop only needs a "
        "result check:\n\n```python\nfor ride_id in cancellations:\n    if "
        'store.cancel_ride(ride_id) is None:\n        post(f"no such ride {ride_id}")\n```'
        "\n\nWhichever you choose, write it down and every new action method follows it; the "
        "worst outcome is a store where half the actions raise and half return None, so "
        "the rule matters more than which one you pick. Once written down, I will follow it "
        "for every action method you ask for.",
    ),
    Turn(
        "user",
        "Logging rule, since the board log is what we read when something looks off: "
        "when a store method hits the notable case a request calls out (joining twice, "
        "leaving a ride you're not on, that kind of thing), it emits exactly one "
        "logging.warning through the module logger; the ordinary path writes no log "
        "records at all.",
    ),
    Turn(
        "assistant",
        "Noted: one `log.warning` per notable case on the module logger already in "
        "store.py, and nothing on the ordinary path; no info or debug lines, never two "
        "warnings for one call. Tests can pin it with caplog: `len(caplog.records) == 1` "
        "after the notable call and `== 0` after a normal one; I will include both checks "
        "whenever I add a notable case.",
    ),
    Turn(
        "user",
        "Missing-id rule: action methods on an unknown id return None and change nothing, "
        "exactly like cancel_ride. Lookups already return None, so the store reads one way "
        "throughout.",
    ),
    Turn(
        "assistant",
        "Understood: unknown id means return None and leave the store untouched, for every "
        "action method, matching cancel_ride. New methods will use `self._rides.get` with "
        "an early return rather than indexing, and the board script keeps its `is None` "
        "check around every action call.",
    ),
    Turn(
        "user",
        "Later I want `count` to take an optional status so the board can say how many "
        "rides are open versus cancelled. Not now. The tests that exist today are only "
        "these:\n\n```python\nfrom ridepool.store import RideStore\n\n\ndef test_offer_"
        'sequential_ids():\n    s = RideStore()\n    assert s.offer_ride("nadia", 3).ride_id '
        '== "R1"\n    assert s.offer_ride("priya", 2).ride_id == "R2"\n\n\ndef test_cancel_'
        'unknown_is_none():\n    assert RideStore().cancel_ride("R1") is None\n\n\ndef '
        'test_count_after_two_offers():\n    s = RideStore()\n    s.offer_ride("nadia", 3)\n'
        '    s.offer_ride("priya", 2)\n    assert s.count() == 2\n```',
    ),
    Turn(
        "assistant",
        "Noted for later. An optional `status: str | None = None` keyword keeps the "
        "no-argument call working:\n\n```python\ndef count(self, status: str | None = None) "
        "-> int:\n    if status is None:\n        return len(self._rides)\n    return sum(1 "
        "for r in self._rides.values() if r.status == status)\n```\n\nYour three tests keep "
        'passing unchanged, and the board can call `count(status="open")` for its header.',
    ),
    Turn(
        "user",
        "Let's get the first feature in; people want to join rides from the board on "
        "Monday. I will paste the current files with every request so you always see the "
        "real state rather than my memory of it. Keep new code in the same style as "
        "cancel_ride so the diff is easy to read in the chat.",
    ),
    Turn(
        "assistant",
        "Ready. Send the request with the files and I will return the complete store "
        "module, keeping offer_ride, find, count and cancel_ride exactly as they are, "
        "with the module logger and imports untouched so your three existing tests stay "
        "green without edits on your side.",
    ),
]

_EVENT = (
    "Change of convention, effective now: after a mistyped id silently dropped three "
    "riders last week, new action methods on RideStore raise KeyError on an unknown id. "
    "Methods already written (cancel_ride, join_ride) keep their current behaviour; only "
    "new methods follow the new rule."
)


def build() -> Session:
    return Session(
        id="S46",
        project="ridepool",
        target_family="missing_record",
        support_family="logging",
        lifecycle="replacement",
        files=_FILES,
        prefix=_PREFIX,
        states=("none", "raise"),
        state_at=("none", "raise"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10),
        tags={"support_state": "warn"},
    )
