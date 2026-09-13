# ruff: noqa: E501
"""TRAIN pool for the six-family candidate-A screen: templated counterfactual sessions.

Registration §1/§4 (``results/a-screen/REGISTRATION-A-SCREEN.md``): 576 authored
counterfactual pairs, 16 per (target × support pairing × lifecycle class) cell, each with
an irrelevant-history variant; both directions carry executable gold; the convention shown
by the existing code is counterbalanced within each cell.  Everything here is generated
from one "record store" construction (an entity dataclass, a store with one existing
operation, an optional persistence backend) that is deliberately different from the
hand-authored SCREEN projects; the domains are disjoint from the screen, the pre-check and
the development sets.  Fit-on only; nothing from ``data/bench/``.

The generated :class:`~stencil.a_screen.Session` objects go through the same packing,
scoring and self-checks as the screen sessions (``tests/test_a_screen.py`` samples them;
``scripts/a_train_build.py`` checks all of them and freezes the hash list).
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass

from stencil.a_screen import (
    LIFECYCLES,
    SUPPORT_FAMILIES,
    TARGET_FAMILIES,
    Request,
    Session,
    Turn,
)

# --------------------------------------------------------------------------- domains

# pairing (target, support) -> two domains (pkg, Entity, entity word, store, error cls)
DOMAINS: dict[tuple[str, str], list[dict[str, str]]] = {
    ("naming", "return_shape"): [
        dict(
            pkg="cragbook",
            Entity="Climber",
            entity="climber",
            Store="ClimberBook",
            Err="CragbookError",
            what="a climbing club's member list",
        ),
        dict(
            pkg="scopelog",
            Entity="Telescope",
            entity="telescope",
            Store="TelescopeLog",
            Err="ScopelogError",
            what="an observatory's telescope register",
        ),
    ],
    ("naming", "error_surface"): [
        dict(
            pkg="marinabook",
            Entity="Boat",
            entity="boat",
            Store="BoatBook",
            Err="MarinabookError",
            what="a marina's berth ledger",
        ),
        dict(
            pkg="kilnlog",
            Entity="Firing",
            entity="firing",
            Store="FiringLog",
            Err="KilnlogError",
            what="a pottery studio's kiln firings",
        ),
    ],
    ("naming", "logging"): [
        dict(
            pkg="tankbook",
            Entity="Tank",
            entity="tank",
            Store="TankBook",
            Err="TankbookError",
            what="an aquarium's tank register",
        ),
        dict(
            pkg="scoreshelf",
            Entity="Score",
            entity="score",
            Store="ScoreShelf",
            Err="ScoreshelfError",
            what="an orchestra's sheet-music shelf",
        ),
    ],
    ("validation", "return_shape"): [
        dict(
            pkg="vendtrack",
            Entity="Machine",
            entity="machine",
            Store="MachineTrack",
            Err="VendtrackError",
            what="a vending-machine fleet",
        ),
        dict(
            pkg="printdesk",
            Entity="Plate",
            entity="plate",
            Store="PlateDesk",
            Err="PrintdeskError",
            what="a print shop's job desk",
        ),
    ],
    ("validation", "error_surface"): [
        dict(
            pkg="hothouse",
            Entity="Sensor",
            entity="sensor",
            Store="SensorBoard",
            Err="HothouseError",
            what="a greenhouse's sensor board",
        ),
        dict(
            pkg="ciderloft",
            Entity="Cask",
            entity="cask",
            Store="CaskBook",
            Err="CiderloftError",
            what="a cider cellar's cask book",
        ),
    ],
    ("validation", "logging"): [
        dict(
            pkg="loomdesk",
            Entity="Loom",
            entity="loom",
            Store="LoomDesk",
            Err="LoomdeskError",
            what="a weaving studio's loom desk",
        ),
        dict(
            pkg="forgebook",
            Entity="Anvil",
            entity="anvil",
            Store="AnvilBook",
            Err="ForgebookError",
            what="a blacksmith co-op's anvil book",
        ),
    ],
    ("missing_record", "return_shape"): [
        dict(
            pkg="skatedesk",
            Entity="Skater",
            entity="skater",
            Store="SkaterDesk",
            Err="SkatedeskError",
            what="a roller derby league's skater desk",
        ),
        dict(
            pkg="orchardlog",
            Entity="Tree",
            entity="tree",
            Store="TreeLog",
            Err="OrchardlogError",
            what="an orchard's tree log",
        ),
    ],
    ("missing_record", "error_surface"): [
        dict(
            pkg="pumpbook",
            Entity="Pump",
            entity="pump",
            Store="PumpBook",
            Err="PumpbookError",
            what="a waterworks' pump book",
        ),
        dict(
            pkg="stagelog",
            Entity="Prop",
            entity="prop",
            Store="PropLog",
            Err="StagelogError",
            what="a theatre's prop log",
        ),
    ],
    ("missing_record", "logging"): [
        dict(
            pkg="hangarbook",
            Entity="Glider",
            entity="glider",
            Store="GliderBook",
            Err="HangarbookError",
            what="a gliding club's hangar book",
        ),
        dict(
            pkg="reefdesk",
            Entity="Buoy",
            entity="buoy",
            Store="BuoyDesk",
            Err="ReefdeskError",
            what="a harbour's buoy desk",
        ),
    ],
}

# --------------------------------------------------------------------------- operations


@dataclass(frozen=True)
class Op:
    verb: str
    param: str  # field updated
    ptype: str  # "str" | "int"
    valid: str  # a valid literal
    invalid: str  # an invalid literal
    rule: str  # validity rule in words
    check: str  # python expression over ``value`` that is True when INVALID
    desc: str  # what the operation does


OPS: list[Op] = [
    Op(
        "rename",
        "name",
        "str",
        '"north face"',
        '"   "',
        "must not be blank",
        "not value.strip()",
        "renames it",
    ),
    Op(
        "assign",
        "owner",
        "str",
        '"dana"',
        '""',
        "must not be empty",
        "not value",
        "assigns it to a person",
    ),
    Op(
        "promote",
        "level",
        "int",
        "3",
        "-1",
        "must not be negative",
        "value < 0",
        "sets its level",
    ),
    Op(
        "schedule",
        "slot",
        "int",
        "4",
        "0",
        "must be between 1 and 7 inclusive",
        "not 1 <= value <= 7",
        "books it into a weekday slot",
    ),
    Op(
        "annotate",
        "note",
        "str",
        '"checked"',
        '""',
        "must not be empty",
        "not value",
        "replaces its note",
    ),
    Op(
        "relocate",
        "site",
        "str",
        '"annex"',
        '"  "',
        "must not be blank",
        "not value.strip()",
        "moves it to a site",
    ),
    Op(
        "reprioritize",
        "priority",
        "int",
        "2",
        "-5",
        "must not be negative",
        "value < 0",
        "sets its priority",
    ),
    Op(
        "retag",
        "tag",
        "str",
        '"urgent"',
        '""',
        "must not be empty",
        "not value",
        "adds a tag",
    ),
]
OP_BY_VERB = {o.verb: o for o in OPS}

# --------------------------------------------------------------------------- code


def _model(d: dict[str, str]) -> str:
    return f'''"""{d["Entity"]} records."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class {d["Entity"]}:
    {d["entity"]}_id: str
    name: str
    owner: str = ""
    level: int = 0
    slot: int = 1
    note: str = ""
    site: str = "main"
    priority: int = 0
    tags: tuple[str, ...] = field(default_factory=tuple)
    status: str = "active"
'''


def _backend(d: dict[str, str]) -> str:
    return f'''"""Optional persistence backend for {d["pkg"]}."""


class Backend:
    """Writes records somewhere durable; raises OSError when the sink is unavailable."""

    def __init__(self, failing: bool = False) -> None:
        self.failing = failing
        self.written: list[dict] = []

    def write(self, record: dict) -> None:
        if self.failing:
            raise OSError("sink unavailable")
        self.written.append(dict(record))
'''


def _errors(d: dict[str, str]) -> str:
    return f'''"""Package exceptions for {d["pkg"]}."""


class {d["Err"]}(Exception):
    """Raised by {d["pkg"]} when a lower-level operation fails."""
'''


def _init(d: dict[str, str]) -> str:
    return f'"""{d["pkg"]}: {d["what"]}."""\n'


_STORE_HEAD = '''"""{Entity} store."""

import logging
from dataclasses import asdict, replace

from {pkg}.backend import Backend
from {pkg}.errors import {Err}
from {pkg}.model import {Entity}

log = logging.getLogger(__name__)


class {Store}:
    def __init__(self, backend: Backend | None = None) -> None:
        self._records: dict[str, {Entity}] = {{}}
        self._backend = backend

    def add(self, record: {Entity}) -> None:
        self._records[record.{entity}_id] = record

    def find(self, {entity}_id: str) -> {Entity} | None:
        return self._records.get({entity}_id)
'''


def method_name(op: Op, entity: str, naming: str) -> str:
    return f"{op.verb}_{entity}" if naming == "verb_noun" else f"{entity}_{op.verb}"


def _lower_fn(op: Op) -> str:
    return f"_apply_{op.verb}"


def _effect(op: Op) -> str:
    if op.param == "tag":
        return "replace(record, tags=(*record.tags, value))"
    return f"replace(record, {op.param}=value)"


def op_code(
    op: Op,
    d: dict[str, str],
    naming: str = "verb_noun",
    validation: str = "api",
    missing: str = "raise",
    return_shape: str = "dataclass",
    error_surface: str = "propagate",
    logging_policy: str = "silent",
) -> tuple[str, str]:
    """(module-level lower function, store method) implementing ``op`` under the given
    states.  Unspecified families use the defaults."""
    name = method_name(op, d["entity"], naming)
    ent = d["entity"]
    chk = f'if {op.check}:\n            raise ValueError(f"invalid {op.param}: {{value!r}}")'
    lower_chk = (
        chk.replace("\n            ", "\n        ") if validation == "storage" else ""
    )
    lower = (
        f"def {_lower_fn(op)}(record: {d['Entity']}, value: {op.ptype}) -> {d['Entity']}:\n"
        + (f"    {lower_chk}\n" if lower_chk else "")
        + f"    return {_effect(op)}\n"
    )
    ret_t = d["Entity"] if return_shape == "dataclass" else "dict"
    if missing == "none":
        ret_t += " | None"
    lines = [f"    def {name}(self, {ent}_id: str, {op.param}: {op.ptype}) -> {ret_t}:"]
    lines.append(f"        value = {op.param}")
    if validation == "api":
        lines.append(f"        {chk}")
    lines.append(f"        record = self._records.get({ent}_id)")
    lines.append("        if record is None:")
    lines.append(
        "            return None"
        if missing == "none"
        else f"            raise KeyError({ent}_id)"
    )
    if logging_policy == "warn":
        lines.append('        if record.status == "archived":')
        lines.append(
            f'            log.warning("{op.verb} on archived {ent} %s", {ent}_id)'
        )
    lines.append(f"        updated = {_lower_fn(op)}(record, value)")
    lines.append(f"        self._records[{ent}_id] = updated")
    lines.append("        if self._backend is not None:")
    if error_surface == "wrap":
        lines.append("            try:")
        lines.append("                self._backend.write(asdict(updated))")
        lines.append("            except OSError as exc:")
        lines.append(f"                raise {d['Err']}(str(exc)) from exc")
    else:
        lines.append("            self._backend.write(asdict(updated))")
    lines.append(
        "        return updated"
        if return_shape == "dataclass"
        else "        return asdict(updated)"
    )
    return lower, "\n".join(lines) + "\n"


def store_file(d: dict[str, str], ops: list[tuple[str, str]]) -> str:
    """The store module with the given (lower, method) pairs appended in order."""
    head = _STORE_HEAD.format(**d)
    lowers = "".join("\n\n" + lo for lo, _ in ops)
    methods = "".join("\n" + m for _, m in ops)
    return head + methods + lowers


# --------------------------------------------------------------------------- tests

_HELPER = """import logging

import pytest

from {pkg}.backend import Backend
from {pkg}.errors import {Err}
from {pkg}.model import {Entity}
from {pkg}.store import {Store}


def _op(store, verb):
    fn = getattr(store, f"{{verb}}_{entity}", None) or getattr(store, f"{entity}_{{verb}}", None)
    assert fn is not None, f"no method for {{verb}}"
    return fn


def _get(out, key):
    return out[key] if isinstance(out, dict) else getattr(out, key)


def _store(backend=None):
    s = {Store}(backend)
    s.add({Entity}("x1", "alpha"))
    s.add({Entity}("x2", "beta", status="archived"))
    return s


def _snapshot(store):
    ids = sorted(k for k in vars(store) if not k.startswith("__"))
    rows = {{}}
    for name in ids:
        value = getattr(store, name)
        if isinstance(value, dict):
            rows[name] = sorted(
                (k, repr(v)) for k, v in value.items()
            )
    assert rows, "no record mapping found on the store"
    return rows
"""


def _helper(d: dict[str, str]) -> str:
    return _HELPER.format(**d)


def functional_tests(op: Op, d: dict[str, str]) -> dict[str, str]:
    field = "tags" if op.param == "tag" else op.param
    exp = f"({op.valid},)" if op.param == "tag" else op.valid
    return {
        f"test_{op.verb}_functional.py": _helper(d)
        + f'''

def test_{op.verb}_updates_stored_record():
    s = _store()
    out = _op(s, "{op.verb}")("x1", {op.valid})
    assert _get(out, "{field}") == {exp}
    assert s.find("x1").{field} == {exp}
    assert s.find("x1").name == "alpha" or "{field}" == "name"


def test_{op.verb}_returns_updated_view():
    s = _store()
    out = _op(s, "{op.verb}")("x1", {op.valid})
    assert _get(out, "{d["entity"]}_id") == "x1"


def test_{op.verb}_invalid_value_rejected():
    s = _store()
    with pytest.raises(ValueError):
        _op(s, "{op.verb}")("x1", {op.invalid})
    assert s.find("x1").{field} == {d["Entity"]}("x1", "alpha").{field}
'''
    }


def regression_tests(existing: Op, d: dict[str, str]) -> dict[str, str]:
    field = "tags" if existing.param == "tag" else existing.param
    exp = f"({existing.valid},)" if existing.param == "tag" else existing.valid
    return {
        "test_regression.py": _helper(d)
        + f'''

def test_add_find_and_existing_operation_unchanged():
    s = _store()
    assert s.find("x1").name == "alpha" and s.find("nope") is None
    out = _op(s, "{existing.verb}")("x1", {existing.valid})
    assert _get(out, "{field}") == {exp}
'''
    }


def contract_tests(
    family: str, state: str, op: Op, d: dict[str, str]
) -> dict[str, str]:
    h = _helper(d)
    if family == "naming":
        want = method_name(op, d["entity"], state)
        other = method_name(
            op, d["entity"], "noun_verb" if state == "verb_noun" else "verb_noun"
        )
        body = f'''

def test_{op.verb}_name_is_{state}():
    assert hasattr({d["Store"]}, "{want}")
    assert not hasattr({d["Store"]}, "{other}")
'''
    elif family == "validation":
        lower = _lower_fn(op)
        if state == "api":
            body = f'''
from {d["pkg"]} import store as store_module


def test_{op.verb}_validation_lives_in_the_public_method():
    s = _store()
    with pytest.raises(ValueError):
        _op(s, "{op.verb}")("x1", {op.invalid})
    # the lower layer does not validate: it applies the value as given
    lower = getattr(store_module, "{lower}")
    out = lower({d["Entity"]}("x1", "alpha"), {op.invalid})
    assert isinstance(out, {d["Entity"]})
'''
        else:
            body = f'''
from {d["pkg"]} import store as store_module


def test_{op.verb}_validation_lives_in_the_lower_layer():
    lower = getattr(store_module, "{lower}")
    with pytest.raises(ValueError):
        lower({d["Entity"]}("x1", "alpha"), {op.invalid})
    # the public method relies on the lower layer: an invalid value reaches it
    calls = []
    original = lower

    def spy(record, value):
        calls.append(value)
        return original(record, value)

    import pytest as _pytest

    mp = _pytest.MonkeyPatch()
    mp.setattr(store_module, "{lower}", spy)
    try:
        s = _store()
        with pytest.raises(ValueError):
            _op(s, "{op.verb}")("x1", {op.invalid})
    finally:
        mp.undo()
    assert calls == [{op.invalid}]
'''
    elif family == "missing_record":
        if state == "none":
            body = f'''

def test_{op.verb}_unknown_id_returns_none_without_change():
    s = _store()
    before = _snapshot(s)
    assert _op(s, "{op.verb}")("zz", {op.valid}) is None
    assert _snapshot(s) == before
    assert s.find("zz") is None
'''
        else:
            body = f'''

def test_{op.verb}_unknown_id_raises_keyerror():
    s = _store()
    before = _snapshot(s)
    with pytest.raises(KeyError):
        _op(s, "{op.verb}")("zz", {op.valid})
    assert _snapshot(s) == before
'''
    else:
        raise ValueError(family)
    return {f"test_{op.verb}_{family}.py": h + body}


def support_tests(family: str, state: str, op: Op, d: dict[str, str]) -> dict[str, str]:
    h = _helper(d)
    if family == "return_shape":
        if state == "dataclass":
            body = f'''

def test_{op.verb}_returns_dataclass_instance():
    out = _op(_store(), "{op.verb}")("x1", {op.valid})
    assert isinstance(out, {d["Entity"]}) and not isinstance(out, dict)
'''
        else:
            body = f'''

def test_{op.verb}_returns_plain_dict():
    out = _op(_store(), "{op.verb}")("x1", {op.valid})
    assert isinstance(out, dict) and out["{d["entity"]}_id"] == "x1"
'''
    elif family == "error_surface":
        if state == "wrap":
            body = f'''

def test_{op.verb}_backend_failure_is_wrapped():
    s = _store(Backend(failing=True))
    with pytest.raises({d["Err"]}):
        _op(s, "{op.verb}")("x1", {op.valid})


def test_{op.verb}_backend_success_writes_once():
    b = Backend()
    s = _store(b)
    _op(s, "{op.verb}")("x1", {op.valid})
    assert len(b.written) == 1 and b.written[0]["{d["entity"]}_id"] == "x1"
'''
        else:
            body = f'''

def test_{op.verb}_backend_failure_propagates_raw():
    s = _store(Backend(failing=True))
    with pytest.raises(OSError) as info:
        _op(s, "{op.verb}")("x1", {op.valid})
    assert not isinstance(info.value, {d["Err"]})


def test_{op.verb}_backend_success_writes_once():
    b = Backend()
    s = _store(b)
    _op(s, "{op.verb}")("x1", {op.valid})
    assert len(b.written) == 1 and b.written[0]["{d["entity"]}_id"] == "x1"
'''
    elif family == "logging":
        if state == "warn":
            body = f'''

def test_{op.verb}_on_archived_record_warns_exactly_once(caplog):
    caplog.set_level(logging.DEBUG)
    _op(_store(), "{op.verb}")("x2", {op.valid})
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1


def test_{op.verb}_on_active_record_is_quiet(caplog):
    caplog.set_level(logging.DEBUG)
    _op(_store(), "{op.verb}")("x1", {op.valid})
    assert caplog.records == [], [(r.levelname, r.getMessage()) for r in caplog.records]
'''
        else:
            body = f'''

def test_{op.verb}_never_logs(caplog):
    caplog.set_level(logging.DEBUG)
    s = _store()
    _op(s, "{op.verb}")("x2", {op.valid})
    _op(s, "{op.verb}")("x1", {op.valid})
    assert caplog.records == []
'''
    else:
        raise ValueError(family)
    return {f"test_{op.verb}_{family}.py": h + body}


# --------------------------------------------------------------------------- statements

STATES = {
    "naming": ("verb_noun", "noun_verb"),
    "validation": ("api", "storage"),
    "missing_record": ("raise", "none"),
    "return_shape": ("dataclass", "dict"),
    "error_surface": ("propagate", "wrap"),
    "logging": ("silent", "warn"),
}


def target_statement(family: str, state: str, d: dict[str, str]) -> str:
    e, S = d["entity"], d["Store"]
    return {
        (
            "naming",
            "verb_noun",
        ): f"Convention for {S}: public methods are named verb_noun, like rename_{e}. Every new public method follows that spelling.",
        (
            "naming",
            "noun_verb",
        ): f"Convention for {S}: public methods are named noun_verb, like {e}_rename. Every new public method follows that spelling.",
        (
            "validation",
            "api",
        ): f"Convention for {S}: argument validation lives in the public method itself. For every operation added from now on, the module-level _apply_* helper never validates; it applies whatever value it is given. Operations already in the file keep the arrangement they have (re-review F8: the grandfathered operation validates in its helper, so the convention must not claim that no helper validates).",
        (
            "validation",
            "storage",
        ): f"Convention for {S}: argument validation lives in the module-level _apply_* helper, which raises ValueError. For every operation added from now on, the public method does not pre-check the value; it lets the helper's ValueError propagate. Operations already in the file keep the arrangement they have.",
        (
            "missing_record",
            "raise",
        ): f"Convention for {S}: an operation on an unknown {e} id raises KeyError.",
        (
            "missing_record",
            "none",
        ): f"Convention for {S}: an operation on an unknown {e} id returns None and changes nothing; it never raises.",
    }[(family, state)]


def support_statement(family: str, state: str, d: dict[str, str]) -> str:
    e, S, Err = d["entity"], d["Store"], d["Err"]
    return {
        (
            "return_shape",
            "dataclass",
        ): f"Also fixed from now on: public {S} operations return {d['Entity']} instances, never dicts.",
        (
            "return_shape",
            "dict",
        ): f"Also fixed from now on: public {S} operations return the updated record as a plain dict (dataclasses.asdict), never a {d['Entity']} instance.",
        (
            "error_surface",
            "propagate",
        ): f"Also fixed from now on: when the backend write fails, the OSError propagates raw from {S} operations; nothing wraps it.",
        (
            "error_surface",
            "wrap",
        ): f"Also fixed from now on: when the backend write fails, {S} operations wrap the OSError in {Err} (raise {Err}(str(exc)) from exc) so callers never see a raw OSError.",
        (
            "logging",
            "silent",
        ): f"Also fixed from now on: {S} operations never log anything, not even for archived {e}s; the caller decides what to log.",
        (
            "logging",
            "warn",
        ): f'Also fixed from now on: a {S} operation applied to an archived {e} (status == "archived") emits exactly one logging.warning and then proceeds; active {e}s produce no log record.',
    }[(family, state)]


def _ack(text: str) -> str:
    return f"Understood. {text.split(':', 1)[1].strip() if ':' in text else text} I will follow that in everything I write for this package."


def replacement_text(family: str, new: str, d: dict[str, str]) -> str:
    return (
        "Change of convention, effective now for anything new: "
        + target_statement(family, new, d).split(": ", 1)[1]
        + " Existing methods stay as they are."
    )


def scope_text(family: str, new: str, op2: Op, d: dict[str, str]) -> str:
    field = "tags" if op2.param == "tag" else op2.param
    base = target_statement(family, new, d).split(": ", 1)[1]
    return (
        f"One exception to the {family.replace('_', ' ')} convention: for operations that change the {field} field "
        f"(anything that sets a {d['entity']}'s {field}), {base[0].lower() + base[1:]} Everything else keeps the convention as stated."
    )


def reinstatement_text(family: str, back: str, d: dict[str, str]) -> str:
    return (
        "Let's go back to the earlier convention, effective now for anything new: "
        + target_statement(family, back, d).split(": ", 1)[1]
        + " Methods written under the interim rule stay as they are."
    )


IRRELEVANT = [
    "Small admin note: the weekly sync moved to Thursday at 10:15, same room. Nothing changes for the code.",
    "By the way, I renamed the repository on the forge; the package name and module paths stay exactly the same.",
    "Heads-up that CI now runs on Python 3.12 as well as 3.11. It passed on both with the current files.",
    "I added a CODEOWNERS file so reviews route to me automatically. No change to any convention.",
    "Unrelated: the office printer is finally fixed, so the README can go back to saying 'print the summary' instead of 'email it'.",
    "FYI the demo for the committee is next Tuesday; I will show whatever is on main by Monday evening.",
    "Just noting that I bumped the version in pyproject to 0.2.0 for the next tag. Nothing else touched.",
    "Reminder to self more than to you: the backup of the old spreadsheet lives in the shared drive, folder 'archive-2025'.",
]

# --------------------------------------------------------------------------- chatter

# Six user/assistant pairs of realistic project talk with placeholders; four are drawn
# for turns 0-7 and two short ones for turns 12-15.
_CHATTER: list[tuple[str, str]] = [
    (
        'I\'m starting {pkg}, a small in-process package for {what}. It is deliberately tiny: a frozen {Entity} dataclass, a {Store} that keeps records in a dict, and an optional Backend that writes records somewhere durable. Before we add operations, can you draft the README scope section? I want to head off the \'why not a database\' conversation, and I want the persistence story stated honestly: the Backend is a hook, not a promise.\n\nThe usage I have in mind:\n\n```python\nfrom {pkg}.model import {Entity}\nfrom {pkg}.store import {Store}\n\nbook = {Store}()\nbook.add({Entity}("x1", "alpha"))\nprint(book.find("x1"))\n```',
        "Here is a scope section that says exactly that:\n\n```\n## Scope\n{pkg} keeps {Entity} records for {what} inside one process. Records live in a {Store}; an optional Backend receives each updated record so a caller can persist it, but {pkg} itself has no storage, no locking and no concurrency guarantees.\n\n## Non-goals\n- multi-process access\n- query language\n- schema migrations\n```\n\nThe non-goals list is what people actually read, and it makes the Backend hook look like what it is: a callback with an OSError contract, not a database.",
    ),
    (
        'Question on the model. {Entity} is a frozen dataclass with name, owner, level, slot, note, site, priority, tags and status. Operations will produce updated copies with dataclasses.replace. Someone suggested making it mutable to \'save allocations\'. I don\'t buy it, but give me the argument I can paste into the review thread.\n\nFor reference this is the whole thing:\n\n```python\n@dataclass(frozen=True)\nclass {Entity}:\n    {entity}_id: str\n    name: str\n    owner: str = ""\n    level: int = 0\n    slot: int = 1\n    note: str = ""\n    site: str = "main"\n    priority: int = 0\n    tags: tuple[str, ...] = field(default_factory=tuple)\n    status: str = "active"\n```',
        "The argument is about aliasing, not allocations. With a frozen record, `find` can hand the stored object to a caller and nothing the caller does can change the store; every operation goes through the store and produces a new record, so the store is the single writer. With a mutable record, any caller holding a reference can edit the store silently, and the Backend would never hear about it. The allocation cost is a few hundred bytes per operation on a package whose volume is measured in records per day. Keep it frozen; if profiling ever shows replace() as a hotspot, that is the day to revisit, and it will not come.",
    ),
    (
        'I wrote a first test for add/find and it passes, but I am unsure about the fixture style. Here is what I have:\n\n```python\nimport pytest\n\nfrom {pkg}.model import {Entity}\nfrom {pkg}.store import {Store}\n\n\n@pytest.fixture\ndef book():\n    s = {Store}()\n    s.add({Entity}("x1", "alpha"))\n    s.add({Entity}("x2", "beta", status="archived"))\n    return s\n\n\ndef test_find_returns_stored_record(book):\n    assert book.find("x1").name == "alpha"\n\n\ndef test_find_unknown_is_none(book):\n    assert book.find("nope") is None\n```\n\nShould the archived record be in the default fixture, or is that going to confuse every future test?',
        "Keep it in the fixture. Almost every operation we add will need to be exercised on an active record and an archived one, and having both present by default means each test names what it uses (`x1` active, `x2` archived) instead of building state. The only thing I would change is the fixture name: `book` is fine here, but a helper function `_store()` that returns the populated store is easier to reuse from tests that need their own Backend instance, because a fixture cannot take a constructor argument without indirection. Both are fine; pick one and keep it.",
    ),
    (
        'I hit this while poking at the Backend from the REPL and want to make sure it is expected:\n\n```\n>>> from {pkg}.backend import Backend\n>>> b = Backend(failing=True)\n>>> b.write({{"{entity}_id": "x1"}})\nTraceback (most recent call last):\n  File "<stdin>", line 1, in <module>\n  File "{pkg}/backend.py", line 12, in write\n    raise OSError("sink unavailable")\nOSError: sink unavailable\n```\n\nSo the failing flag really does raise OSError on every write. Is that the right exception type, or should it be something package-specific from the start?',
        "That is expected and OSError is the right type for the Backend itself: it stands in for a disk, a socket or a queue, and those raise OSError subclasses in the standard library. Whether the *store* converts it into a package exception is a separate decision that belongs to the store's contract, not to the backend. The Backend's job is to be honest about the failure; the store's job is to decide what callers of the store see. Keeping those two decisions apart is what lets you change the store's policy later without touching the backend or its tests.",
    ),
    (
        'For the morning report I want a helper that prints one line per record, like `x1 alpha [active] owner=dana level=3`. I keep waffling on where it goes: a method on {Store}, a method on {Entity}, or a free function. What would you do?\n\nDraft:\n\n```python\ndef summary(record):\n    return f"{{record.{entity}_id}} {{record.name}} [{{record.status}}] owner={{record.owner}} level={{record.level}}"\n```',
        'Free function, next to the model. A method on {Entity} would tie the record to one rendering; a method on {Store} would make the store know about presentation. As a free function it reads only public fields, so it works on anything the store hands back, and the report script can import it without importing the store. Your draft is fine; I would only add a `tags=` segment when the tuple is non-empty so the line stays short for untagged records:\n\n```python\ndef summary(record) -> str:\n    tags = f" tags={{\',\'.join(record.tags)}}" if record.tags else ""\n    return f"{{record.{entity}_id}} {{record.name}} [{{record.status}}] owner={{record.owner}} level={{record.level}}{{tags}}"\n```',
    ),
    (
        "One design question before the operations land. Every operation will look the same: look the record up, compute an updated copy, store it, hand it to the backend if there is one, return something. I am tempted to write one generic `_update(id, **changes)` and have every public method be a one-liner. Is that premature?\n\nSketch:\n\n```python\ndef _update(self, {entity}_id, **changes):\n    record = self._records[{entity}_id]\n    updated = replace(record, **changes)\n    self._records[{entity}_id] = updated\n    return updated\n```",
        "It is premature, for one concrete reason: the operations are going to differ in exactly the places your sketch hides. Validation, what happens on an unknown id, whether and how the backend failure is surfaced, whether anything is logged, and what is returned are all policy decisions, and we are about to state them as project conventions that may change. A generic `_update` would either grow flags for every policy or push the policy back into each caller. Write each operation out in full with a small module-level `_apply_<verb>` helper for the pure record transformation; the repetition is the point, because it keeps every policy visible where a reviewer looks.",
    ),
]

_SHORT_CHATTER: list[tuple[str, str]] = [
    (
        "Do we want type hints on the private helpers too, or only on the public surface?",
        "Both. The private helpers are where the record transformation happens and a wrong annotation there is the one a reader most needs to catch. It costs nothing at runtime.",
    ),
    (
        "I will add a CHANGELOG once the first operations land. Any format preference?",
        "Keep a Changelog style: an Unreleased section on top, one bullet per user-visible change, dates in ISO format. No auto-generation from commits; hand-written bullets read better.",
    ),
    (
        "Should the store expose a way to list every record for the report script?",
        "Yes, a plain `all()` returning `list(self._records.values())` in insertion order. It does not need an ordering argument yet; the report can sort.",
    ),
    (
        "Anything to watch for when we add the first operation?",
        "Only that the request text says what the operation does and the conventions we fixed say how; I will apply both and return the whole store module so you can diff it.",
    ),
]

# --------------------------------------------------------------------------- sessions


def _turns(d: dict[str, str], seed: int) -> tuple[list[Turn], list[Turn]]:
    rng = random.Random(seed)
    long = rng.sample(range(len(_CHATTER)), 4)
    short = rng.sample(range(len(_SHORT_CHATTER)), 2)
    head = []
    for i in long:
        u, a = _CHATTER[i]
        eu, ea = _EXT[i]
        head += [
            Turn("user", (u + eu + _EXT2[i]).format(**d)),
            Turn("assistant", (a + ea).format(**d)),
        ]
    tail = []
    for i in short:
        u, a = _SHORT_CHATTER[i]
        tail += [Turn("user", u.format(**d)), Turn("assistant", a.format(**d))]
    return head, tail


def _states_for(
    target: str, lifecycle: str, flip: bool
) -> tuple[tuple[str, str], tuple[str, str]]:
    a, b = STATES[target]
    if flip:
        a, b = b, a
    if lifecycle == "stable":
        return (a, b), (a, a)
    if lifecycle == "reinstatement":
        return (a, b), (b, a)
    return (a, b), (a, b)


def make_session(
    target: str,
    support: str,
    lifecycle: str,
    index: int,
) -> Session:
    """Deterministic session ``index`` (0..15) of one cell."""
    assert (
        target in TARGET_FAMILIES
        and support in SUPPORT_FAMILIES
        and lifecycle in LIFECYCLES
    )
    cell = f"{target}|{support}|{lifecycle}"
    seed = int(hashlib.sha256(f"{cell}|{index}".encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    d = DOMAINS[(target, support)][index % 2]
    flip = bool((index // 2) % 2)  # which state is the initial one
    precedent_matches_current = bool((index // 4) % 2)  # counterbalance
    states, state_at = _states_for(target, lifecycle, flip)
    support_state = STATES[support][(index // 8) % 2]
    verbs = rng.sample([o.verb for o in OPS], 3)
    existing, op1, op2 = (OP_BY_VERB[v] for v in verbs)

    def kw(target_state: str) -> dict[str, str]:
        k = {
            "naming": "naming",
            "validation": "validation",
            "missing_record": "missing",
        }[target]
        s = {
            "return_shape": "return_shape",
            "error_surface": "error_surface",
            "logging": "logging_policy",
        }[support]
        return {k: target_state, s: support_state}

    # the state the existing code shows: "current" = the state in force at checkpoint 2
    current2 = state_at[1]
    stale2 = state_at[0] if lifecycle != "stable" else states[1]
    precedent_state = current2 if precedent_matches_current else stale2
    existing_code = op_code(existing, d, **kw(precedent_state))
    files = {
        f"{d['pkg']}/__init__.py": _init(d),
        f"{d['pkg']}/model.py": _model(d),
        f"{d['pkg']}/backend.py": _backend(d),
        f"{d['pkg']}/errors.py": _errors(d),
        f"{d['pkg']}/store.py": store_file(d, [existing_code]),
    }
    target_path = f"{d['pkg']}/store.py"

    def request(op: Op, prior: list[tuple[str, str]]) -> Request:
        gold = {st: store_file(d, prior + [op_code(op, d, **kw(st))]) for st in states}
        text = (
            f"Add a public method on {d['Store']} that {op.desc}: it takes the {d['entity']} id and the new "
            f"{op.param} ({op.ptype}), stores the updated record, hands it to the backend when one is configured, "
            f"and returns it. A {op.param} that is not valid ({op.rule}) is rejected with ValueError and nothing is stored."
        )
        return Request(
            text=text,
            target=target_path,
            functional_tests=functional_tests(op, d),
            regression_tests=regression_tests(existing, d),
            contract_tests={st: contract_tests(target, st, op, d) for st in states},
            support_tests=support_tests(support, support_state, op, d),
            gold=gold,
        )

    req1 = request(op1, [existing_code])
    req2 = request(op2, [existing_code, op_code(op1, d, **kw(state_at[0]))])

    head, tail = _turns(d, seed)
    sup = support_statement(support, support_state, d)
    if lifecycle == "reinstatement":
        first = target_statement(target, state_at[1], d)  # A, stated first
        interim = replacement_text(target, state_at[0], d)  # then replaced by B
        prefix = (
            head
            + [
                Turn("user", sup),
                Turn("assistant", _ack(sup)),
                Turn("user", first),
                Turn("assistant", _ack(first)),
                Turn("user", interim),
                Turn("assistant", _ack(interim)),
            ]
            + tail[:2]
        )
        rule_turns = (8, 10, 12)
        event = reinstatement_text(target, state_at[1], d)
    else:
        tgt = target_statement(target, state_at[0], d)
        prefix = (
            head
            + [
                Turn("user", sup),
                Turn("assistant", _ack(sup)),
                Turn("user", tgt),
                Turn("assistant", _ack(tgt)),
            ]
            + tail
        )
        rule_turns = (8, 10)
        if lifecycle == "stable":
            event = IRRELEVANT[(seed + 3) % len(IRRELEVANT)]
        elif lifecycle == "replacement":
            event = replacement_text(target, state_at[1], d)
        else:
            event = scope_text(target, state_at[1], op2, d)
    assert len(prefix) == 16
    sid = f"T-{target[:3]}-{support[:3]}-{lifecycle[:3]}-{index:02d}"
    return Session(
        id=sid,
        project=d["pkg"],
        target_family=target,
        support_family=support,
        lifecycle=lifecycle,
        files=files,
        prefix=prefix,
        states=states,
        state_at=state_at,
        event=event,
        requests=(req1, req2),
        rule_turns=rule_turns,
        irrelevant_event=IRRELEVANT[seed % len(IRRELEVANT)],
        tags={
            "support_state": support_state,
            "precedent_state": precedent_state,
            "precedent_matches_current": str(precedent_matches_current),
            "ops": f"{existing.verb},{op1.verb},{op2.verb}",
        },
    )


def train_sessions(per_cell: int = 16) -> list[Session]:
    out = []
    for target in TARGET_FAMILIES:
        for support in SUPPORT_FAMILIES:
            for lifecycle in LIFECYCLES:
                for i in range(per_cell):
                    s = make_session(target, support, lifecycle, i)
                    s.validate()
                    out.append(s)
    return out


# Extra paragraphs appended to the long chatter pairs so the prefix exceeds the packing
# budget at request 1 (registration §5: compaction must occur before both live requests).
_EXT: list[tuple[str, str]] = [
    (
        "\n\nAlso, do you think the README should mention the Backend at all yet? Nobody uses it today, and I do not want to document a feature that is really a placeholder for a future decision about where records end up.",
        "\n\nMention it in one sentence under Scope and no more: 'An optional Backend receives updated records; {pkg} ships an in-memory one for tests.' That tells a reader the hook exists without promising a storage story, and it keeps the README honest when the real sink arrives.",
    ),
    (
        "\n\nThe other pushback was that frozen dataclasses make tests verbose because every fixture has to build a new record instead of tweaking one. I think that is a feature, but I want your take in a sentence I can quote.",
        "\n\nQuote this: 'A test that wants a different record should say so by constructing it; a test that mutates a shared fixture is describing state it never declared.' Verbosity in the fixture is the cost of tests that cannot leak into one another, and dataclasses.replace keeps that cost to one line.",
    ),
    (
        "\n\nOne more on tests: do we want a conftest with the store helper, or should each test module define its own? I lean towards per-module because the helper is four lines and I dislike hunting for fixtures in conftest.",
        "\n\nPer-module for now. Four lines duplicated across a handful of test files is cheaper than a conftest that every reader has to open to understand a test. If the helper grows a Backend argument and a second archived record, that is the moment to centralise it, and not before.",
    ),
    (
        "\n\nRelated: should the Backend record what it was asked to write even when it is failing, so a test can assert the store attempted the write? Right now a failing backend records nothing.",
        "\n\nNo. A failing sink that also remembers the payload is two behaviours in one flag and the tests would start depending on the order of raise versus append. Keep failing as pure failure; a test that cares about the attempt can pass a working backend and inspect written, which is what the success tests already do.",
    ),
    (
        "\n\nAnd for the report itself: sort by priority then id, or just insertion order? The rota people asked for 'important things first' which I take to mean priority descending.",
        "\n\nPriority descending, then id ascending as a tiebreak so the order is stable across runs: `sorted(records, key=lambda r: (-r.priority, r.{entity}_id))`. Insertion order is fine for debugging but the report is for people, and people read top-down.",
    ),
    (
        "\n\nFair. Then a naming question for the helpers: `_apply_rename` reads fine, but for an operation like retag, which appends to a tuple rather than replacing a field, is `_apply_retag` misleading?",
        "\n\nIt is fine. The `_apply_<verb>` prefix says 'the pure transformation for this verb', not 'replace one field'; what it does to the record is the helper's business and its body is three lines long. Consistency of the prefix is worth more than a perfectly descriptive name for one case.",
    ),
]


# Second extension for the user side of each long pair (sizing only).
_EXT2: list[str] = [
    " For context on volume: {what} has a few dozen records and changes a handful of times a week, so anything that makes the code clearer is worth more than anything that makes it faster. I would rather read a long method than a clever one.",
    " I should add that the reviewer who raised this is new to Python and comes from a language where records are mutable by default, so part of the answer is explaining why the immutable style is idiomatic here and not just my preference.",
    " I also want the tests to double as documentation for whoever inherits this, which is why I care more about readable fixtures than about saving lines. If a test needs a comment to be understood, the fixture is probably wrong.",
    " The reason I am asking now is that the persistence decision is the one thing the committee keeps circling back to, and I want to be able to say the code already has a clean seam for it without having committed to any particular sink.",
    " The report is read on phones during the morning walk-through, so one line per record really does have to stay on one line, and anything optional should only appear when it carries information.",
    " I am asking because I have been burned before by a 'generic' update helper that grew eleven keyword flags over a year and eventually needed its own test suite; I would like to hear the counter-argument before I write the same thing again.",
]
