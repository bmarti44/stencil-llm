# ruff: noqa: E501
"""S12: room booking — naming (target, reinstatement) x logging=warn (support)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""roomdesk package."""\n'

_MODEL = '''"""Room and booking records."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Room:
    room_id: str
    name: str
    capacity: int


@dataclass(frozen=True)
class Booking:
    booking_id: str
    room_id: str
    day: str
    hour: int
    who: str
'''

_STORE = '''"""In-memory room desk."""

import logging

from roomdesk.model import Booking, Room

log = logging.getLogger("roomdesk")


class RoomDesk:
    def __init__(self) -> None:
        self._rooms: dict[str, Room] = {}
        self._bookings: dict[str, Booking] = {}
        self._counter = 0

    def add_room(self, name: str, capacity: int) -> Room:
        room = Room(room_id=f"R{len(self._rooms) + 1}", name=name, capacity=capacity)
        self._rooms[room.room_id] = room
        return room

    def find_room(self, room_id: str) -> Room | None:
        return self._rooms.get(room_id)

    def list_bookings(self, room_id: str) -> list[Booking]:
        return [b for b in self._bookings.values() if b.room_id == room_id]
'''

_FILES = {
    "roomdesk/__init__.py": _INIT,
    "roomdesk/model.py": _MODEL,
    "roomdesk/store.py": _STORE,
}

# ----------------------------------------------------------------- checkpoint 1: book a slot

_C1_HELPER = """import logging

import pytest

from roomdesk.model import Booking
from roomdesk.store import RoomDesk


def _book(desk):
    fn = getattr(desk, "book_room", None) or getattr(desk, "room_book", None)
    assert fn is not None, "no booking method found"
    return fn


def _desk():
    d = RoomDesk()
    d.add_room("Aurora", 6)
    d.add_room("Birch", 12)
    return d


def _pkg_records(caplog):
    return [r for r in caplog.records if r.name.startswith("roomdesk")]
"""

_C1_FUNCTIONAL = {
    "test_book_functional.py": _C1_HELPER
    + """

def test_book_free_slot_stores_and_returns_booking():
    d = _desk()
    out = _book(d)("R1", "2026-09-15", 10, "mira")
    assert isinstance(out, Booking)
    assert (out.room_id, out.day, out.hour, out.who) == ("R1", "2026-09-15", 10, "mira")
    assert d.list_bookings("R1") == [out]


def test_book_ids_are_sequential():
    d = _desk()
    a = _book(d)("R1", "2026-09-15", 9, "mira")
    b = _book(d)("R2", "2026-09-15", 9, "tom")
    assert a.booking_id == "B1" and b.booking_id == "B2"


def test_book_taken_slot_is_refused_and_stores_nothing():
    d = _desk()
    first = _book(d)("R1", "2026-09-15", 10, "mira")
    assert _book(d)("R1", "2026-09-15", 10, "tom") is None
    assert d.list_bookings("R1") == [first]


def test_book_same_hour_other_room_or_day_is_fine():
    d = _desk()
    _book(d)("R1", "2026-09-15", 10, "mira")
    assert _book(d)("R2", "2026-09-15", 10, "tom") is not None
    assert _book(d)("R1", "2026-09-16", 10, "tom") is not None


def test_book_unknown_room_raises_keyerror():
    d = _desk()
    with pytest.raises(KeyError):
        _book(d)("R9", "2026-09-15", 10, "mira")


def test_book_keeps_the_other_rooms_booking():
    d = _desk()
    keep = _book(d)("R2", "2026-09-15", 10, "tom")
    out = _book(d)("R1", "2026-09-15", 10, "mira")
    assert out is not None
    assert d.list_bookings("R2") == [keep], "booking dropped another room's"
    assert d.list_bookings("R1") == [out]
    total = len(d.list_bookings("R1")) + len(d.list_bookings("R2"))
    assert total == 2, "booking changed the number of bookings stored"
    assert d.find_room("R1") is not None
    assert d.find_room("R2") is not None
"""
}

_C1_REGRESSION = {
    "test_book_regression.py": """from roomdesk.store import RoomDesk


def test_add_find_list_unchanged():
    d = RoomDesk()
    r = d.add_room("Aurora", 6)
    assert r.room_id == "R1" and r.capacity == 6
    assert d.find_room("R1") is r and d.find_room("R2") is None
    assert d.list_bookings("R1") == []
    r2 = d.add_room("Birch", 12)
    assert r2.room_id == "R2" and r2.capacity == 12
    assert r2.name == "Birch"
    assert d.find_room("R2") is r2
    assert d.find_room("R1") is r, "adding a room dropped the first one"
    assert d.list_bookings("R2") == []
"""
}

_C1_CONTRACT = {
    "verb_noun": {
        "test_book_naming.py": """from roomdesk.store import RoomDesk


def test_book_is_verb_noun():
    assert hasattr(RoomDesk, "book_room")
    assert not hasattr(RoomDesk, "room_book")
"""
    },
    "noun_verb": {
        "test_book_naming.py": """from roomdesk.store import RoomDesk


def test_book_is_noun_verb():
    assert hasattr(RoomDesk, "room_book")
    assert not hasattr(RoomDesk, "book_room")
"""
    },
}

_C1_SUPPORT = {
    "test_book_logging.py": _C1_HELPER
    + """

def test_refused_booking_warns_exactly_once(caplog):
    d = _desk()
    _book(d)("R1", "2026-09-15", 10, "mira")
    caplog.clear()
    with caplog.at_level(logging.DEBUG, logger="roomdesk"):
        assert _book(d)("R1", "2026-09-15", 10, "tom") is None
    recs = _pkg_records(caplog)
    assert len(recs) == 1
    assert recs[0].levelno == logging.WARNING


def test_successful_booking_logs_nothing(caplog):
    d = _desk()
    caplog.clear()
    with caplog.at_level(logging.DEBUG, logger="roomdesk"):
        assert _book(d)("R1", "2026-09-15", 10, "mira") is not None
    assert _pkg_records(caplog) == []
"""
}


def _gold1(name: str) -> str:
    return (
        _STORE.rstrip("\n")
        + f"""

    def {name}(self, room_id: str, day: str, hour: int, who: str) -> Booking | None:
        if room_id not in self._rooms:
            raise KeyError(room_id)
        for other in self._bookings.values():
            if other.room_id == room_id and other.day == day and other.hour == hour:
                log.warning("refused: %s already booked on %s at %d", room_id, day, hour)
                return None
        self._counter += 1
        booking = Booking(f"B{{self._counter}}", room_id, day, hour, who)
        self._bookings[booking.booking_id] = booking
        return booking
"""
    )


_REQ1 = Request(
    text=(
        "Add a public method on RoomDesk that books a room: it takes the room id, the "
        "day as an ISO date string, the hour (an int) and the person's name, creates a "
        'Booking with the next id ("B1", "B2", ...), stores it and returns it. If that '
        "room already has a booking for the same day and hour, the request is refused: "
        "nothing is stored and the method returns None. An unknown room id raises "
        "KeyError."
    ),
    target="roomdesk/store.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"verb_noun": _gold1("book_room"), "noun_verb": _gold1("room_book")},
)

# ----------------------------------------------------------------- checkpoint 2: move a booking

_C2_HELPER = """import logging

import pytest

from roomdesk.store import RoomDesk


def _book(desk):
    return getattr(desk, "book_room", None) or getattr(desk, "room_book", None)


def _move(desk):
    fn = getattr(desk, "move_booking", None) or getattr(desk, "booking_move", None)
    assert fn is not None, "no move method found"
    return fn


def _desk():
    d = RoomDesk()
    d.add_room("Aurora", 6)
    d.add_room("Birch", 12)
    return d


def _pkg_records(caplog):
    return [r for r in caplog.records if r.name.startswith("roomdesk")]
"""

_C2_FUNCTIONAL = {
    "test_move_functional.py": _C2_HELPER
    + """

def test_move_to_free_slot_updates_and_returns():
    d = _desk()
    b = _book(d)("R1", "2026-09-15", 10, "mira")
    out = _move(d)(b.booking_id, "2026-09-16", 14)
    assert (out.booking_id, out.room_id, out.day, out.hour, out.who) == (
        b.booking_id, "R1", "2026-09-16", 14, "mira"
    )
    assert d.list_bookings("R1") == [out]


def test_move_to_taken_slot_is_refused_and_changes_nothing():
    d = _desk()
    a = _book(d)("R1", "2026-09-15", 10, "mira")
    b = _book(d)("R1", "2026-09-15", 11, "tom")
    assert _move(d)(b.booking_id, "2026-09-15", 10) is None
    assert d.list_bookings("R1") == [a, b]


def test_move_onto_own_slot_is_allowed():
    d = _desk()
    b = _book(d)("R1", "2026-09-15", 10, "mira")
    assert _move(d)(b.booking_id, "2026-09-15", 10) == b


def test_move_ignores_other_rooms():
    d = _desk()
    _book(d)("R2", "2026-09-15", 10, "tom")
    b = _book(d)("R1", "2026-09-15", 11, "mira")
    assert _move(d)(b.booking_id, "2026-09-15", 10) is not None


def test_move_unknown_booking_raises_keyerror():
    d = _desk()
    with pytest.raises(KeyError):
        _move(d)("B9", "2026-09-15", 10)


def test_move_keeps_the_other_bookings_and_the_total():
    d = _desk()
    keep = _book(d)("R2", "2026-09-15", 10, "tom")
    same_room = _book(d)("R1", "2026-09-15", 9, "ana")
    b = _book(d)("R1", "2026-09-15", 11, "mira")
    out = _move(d)(b.booking_id, "2026-09-16", 14)
    assert out is not None
    assert (out.day, out.hour, out.who) == ("2026-09-16", 14, "mira")
    assert d.list_bookings("R2") == [keep], "moving dropped another room's"
    assert d.list_bookings("R1") == [same_room, out]
    total = len(d.list_bookings("R1")) + len(d.list_bookings("R2"))
    assert total == 3, "moving changed the number of bookings stored"
    assert d.find_room("R1") is not None
    assert d.find_room("R2") is not None
"""
}

_C2_REGRESSION = {
    "test_move_regression.py": """from roomdesk.store import RoomDesk


def _book(desk):
    return getattr(desk, "book_room", None) or getattr(desk, "room_book", None)


def test_add_find_book_unchanged():
    d = RoomDesk()
    r = d.add_room("Aurora", 6)
    assert d.find_room("R1") is r
    b = _book(d)("R1", "2026-09-15", 10, "mira")
    assert b.booking_id == "B1" and d.list_bookings("R1") == [b]
    assert _book(d)("R1", "2026-09-15", 10, "tom") is None
    r2 = d.add_room("Birch", 12)
    assert d.find_room("R2") is r2 and r2.capacity == 12
    assert d.find_room("R1") is r, "adding a room dropped the first one"
    c = _book(d)("R2", "2026-09-15", 10, "tom")
    assert c.booking_id == "B2" and c.who == "tom"
    assert d.list_bookings("R2") == [c]
    assert d.list_bookings("R1") == [b], "booking dropped another room's"
"""
}

_C2_CONTRACT = {
    "verb_noun": {
        "test_move_naming.py": """from roomdesk.store import RoomDesk


def test_move_is_verb_noun():
    assert hasattr(RoomDesk, "move_booking")
    assert not hasattr(RoomDesk, "booking_move")
"""
    },
    "noun_verb": {
        "test_move_naming.py": """from roomdesk.store import RoomDesk


def test_move_is_noun_verb():
    assert hasattr(RoomDesk, "booking_move")
    assert not hasattr(RoomDesk, "move_booking")
"""
    },
}

_C2_SUPPORT = {
    "test_move_logging.py": _C2_HELPER
    + """

def test_refused_move_warns_exactly_once(caplog):
    d = _desk()
    _book(d)("R1", "2026-09-15", 10, "mira")
    b = _book(d)("R1", "2026-09-15", 11, "tom")
    caplog.clear()
    with caplog.at_level(logging.DEBUG, logger="roomdesk"):
        assert _move(d)(b.booking_id, "2026-09-15", 10) is None
    recs = _pkg_records(caplog)
    assert len(recs) == 1
    assert recs[0].levelno == logging.WARNING


def test_successful_move_logs_nothing(caplog):
    d = _desk()
    b = _book(d)("R1", "2026-09-15", 10, "mira")
    caplog.clear()
    with caplog.at_level(logging.DEBUG, logger="roomdesk"):
        assert _move(d)(b.booking_id, "2026-09-16", 9) is not None
    assert _pkg_records(caplog) == []
"""
}


def _gold2(name: str) -> str:
    # Built on the checkpoint-1 gold under the state then in force (noun_verb).
    return (
        _gold1("room_book")
        .replace(
            "import logging\n",
            "import logging\nfrom dataclasses import replace\n",
            1,
        )
        .rstrip("\n")
        + f"""

    def {name}(self, booking_id: str, day: str, hour: int) -> Booking | None:
        booking = self._bookings[booking_id]
        for other in self._bookings.values():
            if (
                other.booking_id != booking_id
                and other.room_id == booking.room_id
                and other.day == day
                and other.hour == hour
            ):
                log.warning("refused: %s already booked on %s at %d", booking.room_id, day, hour)
                return None
        moved = replace(booking, day=day, hour=hour)
        self._bookings[booking_id] = moved
        return moved
"""
    )


_REQ2 = Request(
    text=(
        "Add a public method on RoomDesk that moves an existing booking to another time: "
        "it takes the booking id, the new day (ISO date string) and the new hour, keeps "
        "the same room and person, stores the updated booking under the same id and "
        "returns it. If another booking in that room already occupies the new day and "
        "hour, the move is refused: nothing changes and the method returns None (moving "
        "a booking onto its own current slot is allowed). An unknown booking id raises "
        "KeyError."
    ),
    target="roomdesk/store.py",
    functional_tests=_C2_FUNCTIONAL,
    regression_tests=_C2_REGRESSION,
    contract_tests=_C2_CONTRACT,
    support_tests=_C2_SUPPORT,
    gold={"verb_noun": _gold2("move_booking"), "noun_verb": _gold2("booking_move")},
)

# ----------------------------------------------------------------- prefix (16 turns)

_PREFIX = [
    Turn(
        "user",
        "Our co-working floor has four meeting rooms and a whiteboard by the kitchen "
        "where people write their name in a grid. It works until someone wipes a column. "
        "I want to replace the whiteboard with a small package, roomdesk, that a Slack "
        "bot will drive: add rooms, book a slot, move a slot, print the day. The bot is "
        "someone else's; my job is the library underneath, and it must be boring. "
        "Bookings are whole hours on a given day, no recurring meetings, no half hours, "
        "no approvals. Around forty bookings a day at most. The bot's morning message "
        "today looks like this, which is what the grid on the whiteboard has always "
        "looked like:\n\n```\nMon 15 Sep\n        09  10  11  12  13  14  15  16  17\n"
        "Aurora  --  MR  MR  --  --  TK  --  --  --\nBirch   JS  --  --  --  PL  PL  PL  "
        "--  --\n```\n\nCan you draft the README scope so the bot author knows what to "
        "expect and what not to ask for? For scale, the rooms are:\n\n```\nR1  Aurora"
        "   6 seats   screen\nR2  Birch   12 seats   screen, whiteboard\nR3  Cedar    4 "
        "seats   phone booth\nR4  Dune     8 seats   whiteboard\n```\n\nand opening hours "
        "are 9 to 18, though I would rather the library not know that.",
    ),
    Turn(
        "assistant",
        "Here is a scope section written for the bot author:\n\n```\n## Scope\nroomdesk "
        "is an in-memory booking desk for a single process. It keeps Room and Booking "
        "records in a RoomDesk: whole-hour slots on a given day, one booking per room "
        "per slot, no recurrence, no approvals, no notifications. It is a library for "
        "the bot and for tests; the bot owns persistence (a JSON dump per day is "
        "enough) and all of the conversation.\n\n## Invariants\n- a room has at most one "
        "booking per day and hour\n- refused requests change nothing\n\n## Non-goals\n- "
        "recurring meetings\n- half-hour or multi-hour slots (book two hours as two "
        "bookings)\n- calendar sync\n```\n\nThe invariants block is short on purpose; "
        "those are the two things the bot author will rely on and the two things the "
        "tests should pin. Everything else in the README can change without "
        "anyone needing to be told.",
    ),
    Turn(
        "user",
        "Good. Room ids are R1, R2, ... minted from the number of rooms, and booking ids "
        "will be B1, B2, ... from a counter. The bot author wants the booking id in the "
        "Slack reply so people can say 'move B17 to 3pm'. Someone suggested composite "
        "keys like `R1/2026-09-15/10` instead of a counter, since that is what uniquely "
        "identifies a slot anyway. That seems clever but I am suspicious of clever. "
        "Also, days are ISO strings rather than date objects because the bot gets text "
        "and I did not want to parse in two places; is that a mistake I will regret?",
    ),
    Turn(
        "assistant",
        "Be suspicious. A slot key stops identifying a booking the moment the booking "
        "moves, and 'move B17 to 3pm' is exactly the sentence that breaks it: after the "
        "move, B17 would have to change its own id. Keep a counter id for bookings and "
        "treat (room, day, hour) as a uniqueness constraint, not an identity. ISO date "
        "strings are fine for now; they sort correctly, compare with `==`, and the bot "
        "is the only producer. The moment you need 'next week' arithmetic, parse at the "
        "boundary with `date.fromisoformat` and keep the string in Booking, so the "
        "library does not have to change. One thing to pin in a test: the string must "
        "be the canonical `YYYY-MM-DD`; `2026-9-5` would silently become a different "
        "key from `2026-09-05`, so the bot should normalise before calling in. The "
        "normalisation is two lines at the bot's edge:\n\n```python\nday = "
        "date.fromisoformat(text).isoformat()  # raises on junk, canonicalises the rest\n"
        "```\n\nand the library can then assert nothing about the format at all.",
    ),
    Turn(
        "user",
        "Noted on normalising in the bot. What should happen when a slot is already "
        "taken? The whiteboard just had a fight; the bot has to say something. My "
        "instinct is that it is not an error, it is a normal answer ('no'), so the "
        "method should return None and the bot turns that into a message. But my "
        "colleague says anything that fails to do what was asked should raise, and "
        "points at how `dict.pop` on a missing key behaves without a default. Here is "
        "what the bot author sketched, for context:\n\n```python\nbooking = desk.book(...)"
        '\nif booking is None:\n    reply(f"{room.name} is taken at {hour}:00, try '
        '{suggest(desk, room, day)}")\nelse:\n    reply(f"Booked {room.name} {day} '
        '{hour}:00 as {booking.booking_id}")\n```',
    ),
    Turn(
        "assistant",
        "Your instinct is right for this domain. A taken slot is an expected outcome of "
        "a booking attempt, roughly as common as success at peak hours, and the bot has "
        "a friendly thing to say about it; that is a return value, not an exception. "
        "Exceptions are for things the caller got wrong: an unknown room id or booking "
        "id is a bot bug or a typo, and raising KeyError there fails loudly at the right "
        "line. So the split is: refusals (slot taken) return None and change nothing; "
        "lookups (`find_room`) return None when missing; actions on an unknown id raise "
        "KeyError. The `suggest` helper the bot author wants is a query over "
        "`list_bookings` and belongs in the bot, since 'nearest free hour' is a "
        "conversation policy rather than a desk rule. The `dict.pop` analogy cuts the "
        "other way: `pop` has a default argument precisely because callers usually "
        "know that a miss is normal.",
    ),
    Turn(
        "user",
        "Agreed. Refusals return None, actions on unknown ids raise KeyError. For the "
        "day grid I wrote this in the bot-side script, using only `list_bookings`; tell "
        "me if anything here should be in the library instead:\n\n```python\nHOURS = "
        "range(9, 18)\n\n\ndef grid(desk: RoomDesk, rooms: list[Room], day: str) -> "
        'str:\n    lines = ["        " + "  ".join(f"{h:02d}" for h in HOURS)]\n    for '
        "room in rooms:\n        taken = {b.hour: b.who for b in desk.list_bookings("
        "room.room_id) if b.day == day}\n        cells = [initials(taken[h]) if h in "
        'taken else "--" for h in HOURS]\n        lines.append(f"{room.name:<8}" + "  "'
        '.join(cells))\n    return "\\n".join(lines)\n```',
    ),
    Turn(
        "assistant",
        "That is the right side of the line. The grid is presentation: opening hours, "
        "initials, column widths are all things the bot decides and the library should "
        "not know. The only library-shaped thing in there is filtering bookings by day, "
        "and even that is a one-line comprehension over `list_bookings`, so it does not "
        "earn a method yet. If a second consumer appears (a wall display, say), add an "
        "optional `day` filter to `list_bookings` at that point. Keep `HOURS` in the "
        "bot; the library should accept any int hour so a late event can be booked "
        "without a code change. The `initials` helper is the one piece I would test on "
        'its own, because names like "Mary-Jane O\'Neil" will show up:\n\n```python\n'
        'def initials(who: str) -> str:\n    parts = [p for p in who.replace("-", " ")'
        '.split() if p]\n    return "".join(p[0].upper() for p in parts[:2]) or "??"\n'
        "```\n\nTwo characters keeps the columns aligned, and `??` for an empty name is "
        "better than an exception in the morning message.",
    ),
    Turn(
        "user",
        "Two conventions before the real methods land. First, logging: when a public "
        "RoomDesk method refuses a request (a slot already taken, and the same for any "
        "refusal we add later), it emits exactly one `logging.warning` through the "
        "module logger `roomdesk` and nothing else. Successful operations log nothing "
        "at all, not even debug; the bot is chatty enough. I want to grep the log for "
        "WARNING and count the fights.",
    ),
    Turn(
        "assistant",
        "Understood: every refusal in a public RoomDesk method logs exactly one warning "
        "on the `roomdesk` logger (one record, not one per loop iteration), and the "
        "success path emits no record at any level. KeyError on an unknown id is not a "
        "refusal, it is a caller error, so it raises without logging.",
    ),
    Turn(
        "user",
        "Second, naming: public RoomDesk methods are verb_noun, like add_room and "
        "list_bookings. New methods follow that pattern so the class reads as a list of "
        "actions.",
    ),
    Turn(
        "assistant",
        "Noted: verb_noun for new public RoomDesk methods, matching add_room, find_room "
        "and list_bookings. Private helpers can be named freely. Where the verb is "
        "ambiguous I will use the verb the request itself uses.",
    ),
    Turn(
        "user",
        "Actually, wait. The bot author's own codebase names everything noun_verb "
        "(message_send, channel_join) and they asked whether roomdesk could match so "
        "autocomplete groups by the thing being acted on. Let's try it: from now on, "
        "new public RoomDesk methods are noun_verb. Existing names such as add_room "
        "stay as they are.",
    ),
    Turn(
        "assistant",
        "Switching: new public RoomDesk methods are noun_verb from now on (for example "
        "room_book, booking_cancel). add_room, find_room and list_bookings keep their "
        "names. If you decide against it later, say so and I will go back to verb_noun "
        "for anything new.",
    ),
    Turn(
        "user",
        "The tests that exist today are only these; I will paste the current files with "
        "each request so you see the real state:\n\n```python\nfrom roomdesk.store "
        "import RoomDesk\n\n\ndef test_add_room_mints_sequential_ids():\n    d = "
        'RoomDesk()\n    assert d.add_room("Aurora", 6).room_id == "R1"\n    assert '
        'd.add_room("Birch", 12).room_id == "R2"\n\n\ndef test_find_room_missing_is_none'
        '():\n    assert RoomDesk().find_room("R1") is None\n\n\ndef '
        'test_list_bookings_empty():\n    d = RoomDesk()\n    d.add_room("Aurora", 6)\n'
        '    assert d.list_bookings("R1") == []\n```',
    ),
    Turn(
        "assistant",
        "Good. Send the first request and I will return the complete store module, "
        "keeping add_room, find_room and list_bookings exactly as they are.",
    ),
]

_EVENT = (
    "Scrap the noun_verb idea; the bot author changed their mind after seeing "
    "add_room next to it and it reads badly. Back to the original rule: new public "
    "RoomDesk methods are verb_noun. Whatever has already been added keeps its current "
    "name; only new methods follow verb_noun again."
)


def build() -> Session:
    return Session(
        id="S12",
        project="roomdesk",
        target_family="naming",
        support_family="logging",
        lifecycle="reinstatement",
        files=_FILES,
        prefix=_PREFIX,
        states=("verb_noun", "noun_verb"),
        state_at=("noun_verb", "verb_noun"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10, 12),
    )
