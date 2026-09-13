# ruff: noqa: E501
"""S02: ticketing — naming (target, replacement) x return_shape (support)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""ticketing package."""\n'

_MODEL = '''"""Ticket records."""

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Ticket:
    ticket_id: str
    title: str
    status: str = "open"
    assignee: str | None = None

    def with_status(self, status: str) -> "Ticket":
        return replace(self, status=status)
'''

_STORE = '''"""In-memory ticket store."""

from ticketing.model import Ticket


class TicketStore:
    def __init__(self) -> None:
        self._tickets: dict[str, Ticket] = {}
        self._counter = 0

    def open_ticket(self, title: str) -> Ticket:
        self._counter += 1
        ticket = Ticket(ticket_id=f"T{self._counter}", title=title)
        self._tickets[ticket.ticket_id] = ticket
        return ticket

    def find(self, ticket_id: str) -> Ticket | None:
        return self._tickets.get(ticket_id)

    def count(self) -> int:
        return len(self._tickets)
'''

_FILES = {
    "ticketing/__init__.py": _INIT,
    "ticketing/model.py": _MODEL,
    "ticketing/store.py": _STORE,
}

# ----------------------------------------------------------------- checkpoint 1: close

_C1_HELPER = """from ticketing.model import Ticket
from ticketing.store import TicketStore


def _close(store):
    fn = getattr(store, "close_ticket", None) or getattr(store, "ticket_close", None)
    assert fn is not None, "no close method found"
    return fn
"""

_C1_FUNCTIONAL = {
    "test_close_functional.py": _C1_HELPER
    + """

def test_close_sets_status_closed():
    s = TicketStore()
    t = s.open_ticket("printer jams")
    out = _close(s)(t.ticket_id)
    assert out.status == "closed"
    assert s.find(t.ticket_id).status == "closed"


def test_close_keeps_title_and_id():
    s = TicketStore()
    t = s.open_ticket("vpn down")
    out = _close(s)(t.ticket_id)
    assert out.ticket_id == t.ticket_id and out.title == "vpn down"


def test_close_unknown_raises_keyerror():
    s = TicketStore()
    try:
        _close(s)("T999")
    except KeyError:
        return
    raise AssertionError("expected KeyError for an unknown ticket")
"""
}

_C1_REGRESSION = {
    "test_close_regression.py": """from ticketing.store import TicketStore


def test_open_and_find_unchanged():
    s = TicketStore()
    t = s.open_ticket("a")
    assert t.ticket_id == "T1" and t.status == "open"
    assert s.find("T1") is t
    assert s.find("nope") is None
    assert s.count() == 1
"""
}

_C1_CONTRACT = {
    "verb_noun": {
        "test_close_naming.py": """from ticketing.store import TicketStore


def test_close_is_verb_noun():
    assert hasattr(TicketStore, "close_ticket")
    assert not hasattr(TicketStore, "ticket_close")
"""
    },
    "noun_verb": {
        "test_close_naming.py": """from ticketing.store import TicketStore


def test_close_is_noun_verb():
    assert hasattr(TicketStore, "ticket_close")
    assert not hasattr(TicketStore, "close_ticket")
"""
    },
}

_C1_SUPPORT = {
    "test_close_shape.py": _C1_HELPER
    + """

def test_close_returns_ticket_dataclass_not_dict():
    s = TicketStore()
    t = s.open_ticket("x")
    out = _close(s)(t.ticket_id)
    assert isinstance(out, Ticket)
    assert not isinstance(out, dict)
"""
}


def _gold1(name: str) -> str:
    return (
        _STORE.rstrip("\n")
        + f"""

    def {name}(self, ticket_id: str) -> Ticket:
        ticket = self._tickets[ticket_id]
        closed = ticket.with_status("closed")
        self._tickets[ticket_id] = closed
        return closed
"""
    )


_REQ1 = Request(
    text=(
        "Add a public method on TicketStore that closes a ticket by id: it sets the "
        'status to "closed", stores the updated ticket and returns it. An unknown id '
        "raises KeyError."
    ),
    target="ticketing/store.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"verb_noun": _gold1("close_ticket"), "noun_verb": _gold1("ticket_close")},
)

# ----------------------------------------------------------------- checkpoint 2: assign

_C2_HELPER = """from ticketing.model import Ticket
from ticketing.store import TicketStore


def _assign(store):
    fn = getattr(store, "assign_ticket", None) or getattr(store, "ticket_assign", None)
    assert fn is not None, "no assign method found"
    return fn
"""

_C2_FUNCTIONAL = {
    "test_assign_functional.py": _C2_HELPER
    + """

def test_assign_sets_assignee():
    s = TicketStore()
    t = s.open_ticket("printer jams")
    out = _assign(s)(t.ticket_id, "dana")
    assert out.assignee == "dana"
    assert s.find(t.ticket_id).assignee == "dana"


def test_assign_keeps_status_and_title():
    s = TicketStore()
    t = s.open_ticket("vpn down")
    out = _assign(s)(t.ticket_id, "lee")
    assert out.status == "open" and out.title == "vpn down"


def test_assign_unknown_raises_keyerror():
    s = TicketStore()
    try:
        _assign(s)("T999", "dana")
    except KeyError:
        return
    raise AssertionError("expected KeyError for an unknown ticket")
"""
}

_C2_REGRESSION = {
    "test_assign_regression.py": """from ticketing.store import TicketStore


def _close(store):
    return getattr(store, "close_ticket", None) or getattr(store, "ticket_close", None)


def test_open_find_close_unchanged():
    s = TicketStore()
    t = s.open_ticket("a")
    assert s.find("T1") is t and s.count() == 1
    assert _close(s)(t.ticket_id).status == "closed"
"""
}

_C2_CONTRACT = {
    "verb_noun": {
        "test_assign_naming.py": """from ticketing.store import TicketStore


def test_assign_is_verb_noun():
    assert hasattr(TicketStore, "assign_ticket")
    assert not hasattr(TicketStore, "ticket_assign")
"""
    },
    "noun_verb": {
        "test_assign_naming.py": """from ticketing.store import TicketStore


def test_assign_is_noun_verb():
    assert hasattr(TicketStore, "ticket_assign")
    assert not hasattr(TicketStore, "assign_ticket")
"""
    },
}

_C2_SUPPORT = {
    "test_assign_shape.py": _C2_HELPER
    + """

def test_assign_returns_ticket_dataclass_not_dict():
    s = TicketStore()
    t = s.open_ticket("x")
    out = _assign(s)(t.ticket_id, "dana")
    assert isinstance(out, Ticket)
    assert not isinstance(out, dict)
"""
}


def _gold2(name: str) -> str:
    # Built on the checkpoint-1 gold under the state then in force (verb_noun).
    return (
        _gold1("close_ticket").rstrip("\n")
        + f"""

    def {name}(self, ticket_id: str, assignee: str) -> Ticket:
        ticket = self._tickets[ticket_id]
        assigned = replace(ticket, assignee=assignee)
        self._tickets[ticket_id] = assigned
        return assigned
"""
    )


def _gold2_full(name: str) -> str:
    body = _gold2(name)
    return body.replace(
        "from ticketing.model import Ticket\n",
        "from dataclasses import replace\n\nfrom ticketing.model import Ticket\n",
        1,
    )


_REQ2 = Request(
    text=(
        "Add a public method on TicketStore that assigns a ticket to a person: it takes "
        "the ticket id and the assignee name, stores the updated ticket with that "
        "assignee and returns it. An unknown id raises KeyError."
    ),
    target="ticketing/store.py",
    functional_tests=_C2_FUNCTIONAL,
    regression_tests=_C2_REGRESSION,
    contract_tests=_C2_CONTRACT,
    support_tests=_C2_SUPPORT,
    gold={
        "verb_noun": _gold2_full("assign_ticket"),
        "noun_verb": _gold2_full("ticket_assign"),
    },
)

# ----------------------------------------------------------------- prefix (16 turns)

_PREFIX = [
    Turn(
        "user",
        "I'm setting up a tiny ticketing package for our helpdesk rotation. Nothing fancy: "
        "an in-memory store, a Ticket record, maybe a CLI later. Three of us rotate weekly "
        "and we keep losing track of who promised what, so I want something a script can "
        "drive from a cron job that prints the open list every morning. Can you sketch what "
        "the README should say about scope so people don't expect a database or a web UI? "
        "I'd rather set expectations early than field feature requests for Jira. The cron "
        "side is just:\n\n```\n0 9 * * 1-5 cd /srv/helpdesk && python -m ticketing.report "
        ">> /var/log/helpdesk-report.log 2>&1\n```\n\nso the package only has to expose "
        "enough for that script to build the list. The three of us on the rotation are "
        "Dana, Lee and me; tickets come in by email and someone types them into the store "
        "at standup, so volume is maybe ten a week. Speed is irrelevant; clarity of the "
        "API is everything, because whoever is on rotation is usually half-distracted.",
    ),
    Turn(
        "assistant",
        "A short scope section works well:\n\n```\n## Scope\nticketing is an in-memory "
        "helpdesk tracker for a single process. It keeps Ticket records in a TicketStore, "
        "has no persistence and no concurrency guarantees, and is meant for scripts and "
        "tests, not as a service. If you need shared state across machines, export the "
        "tickets and load them into a real tracker.\n\n## Non-goals\n- web UI\n- "
        "multi-user editing\n- attachments\n```\n\nThat sets expectations without promising "
        "a roadmap, and the non-goals list is what people actually read. A usage block "
        "helps too:\n\n```python\nfrom ticketing.store import TicketStore\n\nstore = "
        'TicketStore()\nt = store.open_ticket("printer jams")\nprint(store.find(t.'
        "ticket_id))\n```",
    ),
    Turn(
        "user",
        "Good. For ticket ids I'm using T1, T2, ... from a counter. Is there any reason to "
        "prefer uuids here? The tickets never leave the process, but someone on the team "
        "said counters are a smell because two stores would collide. I don't plan to have "
        "two stores, but I also don't want to repaint the ids later if we do add a JSON "
        "export for the morning report. The export I have in mind is nothing more than:\n\n"
        '```json\n{\n  "store": "helpdesk",\n  "exported_at": "2026-09-14T09:00:00",\n'
        '  "tickets": [\n    {"ticket_id": "T1", "title": "printer jams", "status": '
        '"open", "assignee": null},\n    {"ticket_id": "T2", "title": "vpn down", '
        '"status": "closed", "assignee": "dana"}\n  ]\n}\n```',
    ),
    Turn(
        "assistant",
        "For a single-process, in-memory store the counter is fine and much easier to read "
        "in logs and tests: `T14` in a chat message beats a 36-character uuid. Uuids only "
        "earn their keep when ids must be unique across processes or after restarts. If a "
        "JSON export lands, the export can carry a store name alongside the id "
        "(`helpdesk/T14`), which solves the two-stores worry without changing the id "
        "format, and a reader can still tell at a glance which ticket came first. Keep the "
        "counter; if persistence arrives later you can switch the id "
        "generator in one place because only `open_ticket` mints ids:\n\n```python\ndef "
        '_next_id(self) -> str:\n    self._counter += 1\n    return f"T{self._counter}"\n'
        "```\n\nIf you ever do need cross-store uniqueness, that method becomes "
        '`f"{self.name}/T{self._counter}"` and nothing else changes.',
    ),
    Turn(
        "user",
        "I want a small helper that formats a ticket for a one-line summary in the CLI, "
        "something like `T3 [open] printer jams (dana)`. Where should it live, and should "
        "it be a method on Ticket or a free function? I keep going back and forth: a method "
        "is discoverable, but then Ticket knows about presentation, which feels wrong for a "
        "record type. Here is the test draft I have so far, so you can see the shape I am "
        "after:\n\n```python\nimport pytest\n\nfrom ticketing.model import Ticket\n\n\n"
        '@pytest.fixture\ndef open_ticket():\n    return Ticket(ticket_id="T3", title='
        '"printer jams")\n\n\ndef test_summary_open(open_ticket):\n    assert summary('
        'open_ticket) == "T3 [open] printer jams"\n\n\ndef test_summary_assigned('
        'open_ticket):\n    t = Ticket(ticket_id="T3", title="printer jams", '
        'assignee="dana")\n    assert summary(t) == "T3 [open] printer jams (dana)"'
        "\n```",
    ),
    Turn(
        "assistant",
        "Put it next to the model as a plain function so the CLI and tests can share it "
        "without Ticket learning about presentation:\n\n```python\ndef summary(ticket: "
        'Ticket) -> str:\n    who = f" ({ticket.assignee})" if ticket.assignee else ""\n'
        '    return f"{ticket.ticket_id} [{ticket.status}] {ticket.title}{who}"\n```\n\n'
        "It reads only public fields, so it stays trivially testable, and if the CLI later "
        "wants colour or column alignment that lives in the CLI module, not here. A "
        "`__str__` on Ticket would tie the record to one rendering forever.",
    ),
    Turn(
        "user",
        "We'll add that when the CLI lands. Another question: should `find` raise on a "
        "missing id or return None? Right now it returns None and the caller checks. I've "
        "seen both styles argued for, and I want one rule I can point people at instead of "
        "deciding per method every time. For context, this is what a caller currently hits "
        'when it assumes `find` raises:\n\n```\n>>> store.find("T9").status\n'
        'Traceback (most recent call last):\n  File "<stdin>", line 1, in <module>\n'
        "AttributeError: 'NoneType' object has no attribute 'status'\n```\n\nWhich is "
        "the usual None-propagation trap, and I would rather the rule be written down than "
        "rediscovered by each person on the rotation.",
    ),
    Turn(
        "assistant",
        "Returning None from `find` is the usual lookup contract: the name says 'try to "
        "find', and callers branch on the result. Methods that *act* on a ticket (closing, "
        "assigning, reopening) are different: acting on an id that does not exist is a "
        "caller bug, so raising KeyError there is the clearer signal and it surfaces in "
        "tests immediately. So the rule is: lookups return None, actions raise KeyError. "
        "Keep `find` as it is, and callers that need a hard failure can wrap it:\n\n"
        "```python\ndef require(store, ticket_id):\n    ticket = store.find(ticket_id)\n"
        "    if ticket is None:\n        raise KeyError(ticket_id)\n    return ticket\n```"
        "\n\nThat keeps the None-propagation trap out of the morning report script, and the "
        "traceback you pasted becomes a KeyError('T9') at the call site, which is the "
        "message the person on rotation actually needs.",
    ),
    Turn(
        "user",
        "Agreed, actions raise KeyError on unknown ids. Two conventions I want to fix now "
        "so the code stays uniform. First: public TicketStore methods always return Ticket "
        "dataclass instances, never dicts or tuples, even for convenience (find may return None and count() stays an int). I got burned on "
        "the last project where half the API returned dicts and every caller had a "
        "`.get('status')` sprinkled around.",
    ),
    Turn(
        "assistant",
        "Noted: every public TicketStore method returns Ticket instances (or None from "
        "lookups), never dicts or tuples. That keeps callers on one type, lets us add "
        "fields to Ticket without breaking them, and means the summary helper works on "
        "anything the store hands back.",
    ),
    Turn(
        "user",
        "Second: method naming. Public store methods are named verb_noun, like "
        "open_ticket. Anything new follows that pattern so the API reads as a list of "
        "actions.",
    ),
    Turn(
        "assistant",
        "Understood: verb_noun for public TicketStore methods, matching open_ticket. I "
        "will name new methods that way, and private helpers can stay free-form since "
        "they are not part of the API. If a name is ambiguous, for example whether a "
        "method that marks a ticket closed is close_ticket or resolve_ticket, I will pick "
        "the verb the request itself uses.",
    ),
    Turn(
        "user",
        "One more thing for later: I'd like `count` to eventually take an optional status "
        "filter, so the morning report can print open versus closed totals. Not now, just "
        "noting it so we don't paint ourselves into a corner. The report script would then "
        'be roughly:\n\n```python\ndef main(store: TicketStore) -> None:\n    print(f"open: '
        "{store.count(status='open')}  closed: {store.count(status='closed')}\")\n    for "
        'ticket in store.all():\n        if ticket.status == "open":\n            print('
        "summary(ticket))\n```\n\nwhere `all()` is another thing we do not have yet. For reference, the tests that "
        "exist today are only these:\n\n```python\nfrom ticketing.store import TicketStore"
        "\n\n\ndef test_open_assigns_sequential_ids():\n    s = TicketStore()\n    assert "
        's.open_ticket("a").ticket_id == "T1"\n    assert s.open_ticket("b").ticket_id '
        '== "T2"\n\n\ndef test_find_missing_returns_none():\n    assert TicketStore().'
        'find("T1") is None\n\n\ndef test_count_after_two_opens():\n    s = TicketStore()\n'
        '    s.open_ticket("a")\n    s.open_ticket("b")\n    assert s.count() == 2\n```',
    ),
    Turn(
        "assistant",
        "Noted for later. When it comes, an optional keyword `status: str | None = None` "
        "keeps the current no-argument call working, and the filter is a one-line "
        "comprehension over the stored tickets:\n\n```python\ndef count(self, status: str | "
        "None = None) -> int:\n    if status is None:\n        return len(self._tickets)\n"
        "    return sum(1 for t in self._tickets.values() if t.status == status)\n```\n\n"
        "`all()` would return `list(self._tickets.values())` in insertion order, which is "
        "also creation order because ids are minted sequentially.",
    ),
    Turn(
        "user",
        "Right. Let's get the first real feature in; the rotation starts Monday and I want "
        "closing tickets to work before then. I will paste the current files with each "
        "request so you always see the real state rather than my memory of it.",
    ),
    Turn(
        "assistant",
        "Ready when you are. Send the request and I will return the full store module.",
    ),
]

_EVENT = (
    "Change of convention, effective now: new public TicketStore methods are named "
    "noun_verb (for example ticket_close style), not verb_noun. Existing method names "
    "stay as they are; only new methods follow the new pattern."
)


def build() -> Session:
    return Session(
        id="S02",
        project="ticketing",
        target_family="naming",
        support_family="return_shape",
        lifecycle="replacement",
        files=_FILES,
        prefix=_PREFIX,
        states=("verb_noun", "noun_verb"),
        state_at=("verb_noun", "noun_verb"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10),
    )
