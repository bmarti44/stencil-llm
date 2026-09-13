"""Development blocks for the scoped-instruction-compilation diagnostic.

Astra's forward review (results/reviews/2026-09-13-a-screen-forward-astra.md)
recommends scoped instruction compilation at a 28% artifact-success forecast --
the first direction above Brian's 25% bar -- and makes step 1 a CPU-only
instrument: sixteen development blocks whose executable oracle rejects five
trivial policies.  The strict gate it states is

    gold and valid alternatives pass; every shortcut fails its designated
    contrasts; source metadata cannot reach the automatic arm.

Failure of that gate means repair the fixture, not experiment on the model.

The semantics the resolver implements are frozen in
`results/scoped/SEMANTICS.md` and are NOT re-derived here.

Nothing in this module reads `data/bench/`, touches the GPU, or looks at any
model outcome.  `python -c "import stencil.scoped_blocks"` does no work.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import sys
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path

VALUES = ("raise", "none", "default")
BASELINE = "default"  # the documented package baseline; see SEMANTICS.md
KINDS = ("lookup", "bulk")

PRESENT = {"alpha": 11, "beta": 22}
MISSING = "gamma"
DEFAULT_VALUE = 0


# --------------------------------------------------------------- data model


@dataclass(frozen=True)
class Event:
    """One authoritative message, and the event it carries (possibly none)."""

    id: str
    text: str
    # set | replace | cancel | reinstate | obligate | release | noise
    kind: str = "noise"
    scope: str = "*"
    fn_kind: str | None = None  # None = every operation
    value: str | None = None
    ref: str | None = None
    name: str | None = None  # obligation name
    # scopes this message explicitly clears ("for the whole package, compat
    # included"); applied before the message's own event
    clears: tuple[str, ...] = ()

    def __post_init__(self):
        assert self.kind in (
            "set", "replace", "cancel", "reinstate", "obligate", "release", "noise"
        ), self.kind
        if self.kind in ("set", "replace"):
            assert self.value in VALUES, (self.id, self.value)
        if self.kind == "reinstate":
            assert self.ref, self.id
        if self.kind in ("obligate", "release"):
            assert self.name, self.id
        assert self.fn_kind in (None, *KINDS), self.fn_kind


@dataclass(frozen=True)
class Case:
    """One applicability case: add one function at one path.

    `expect_value` and `expect_note` are FROZEN BY HAND from the block's public
    message wording.  The oracle reads them; it never asks the resolver.  Astra
    found that `gold_candidate()` and `evaluate()` both took their expectation
    from `resolve()`, so agreement between them validated nothing -- a wrong
    resolver was simply believed twice.  The gate asserts that `resolve()`
    reproduces these authored values, which is a real check in the direction
    that matters.
    """

    name: str
    path: str  # "core" | "compat" | "compat.legacy"
    fn_kind: str  # lookup | bulk
    fname: str
    expect_value: str = ""
    expect_note: bool = False

    def __post_init__(self):
        assert self.expect_value in VALUES, (self.name, self.expect_value)


@dataclass(frozen=True)
class Block:
    id: str
    family: str
    precedent: str  # the missing-entry value the ENTERING code implements
    history: tuple[Event, ...]
    cases: tuple[Case, Case]
    defeats: tuple[str, ...]  # the shortcut policies this block is built to defeat
    note: str = ""
    entering_obligations: tuple[str, ...] = ()


# ------------------------------------------------------------- the resolver


def _specificity(scope: str, fn_kind: str | None) -> tuple[int, int]:
    depth = 0 if scope == "*" else len(scope.split("."))
    return (depth, 1 if fn_kind else 0)


def _matches(scope: str, fn_kind: str | None, path: str, kind: str) -> bool:
    if scope != "*" and path != scope and not path.startswith(scope + "."):
        return False
    return fn_kind is None or fn_kind == kind


def live_state(history) -> tuple[dict, dict]:
    """Fold the history into (live policies, live obligation supports).

    Obligations are keyed by (name, scope) and map to the EVENT that supports
    them, so a name with two supports keeps them apart: releasing one leaves the
    other standing.  Astra's finding 8 -- selecting supports by name alone let a
    released package-wide statement keep appearing next to a live compat one.
    """
    live: dict[tuple[str, str | None], Event] = {}
    obligations: dict[tuple[str, str], Event] = {}
    by_id = {e.id: e for e in history}
    for e in history:
        key = (e.scope, e.fn_kind)
        for scope in e.clears:
            for live_key in [k for k in live if k[0] == scope]:
                live.pop(live_key)
        if e.kind in ("set", "replace"):
            live[key] = e
        elif e.kind == "cancel":
            live.pop(key, None)  # never revives what it replaced
        elif e.kind == "reinstate":
            ref = by_id[e.ref]
            assert ref.kind in ("set", "replace"), (e.id, e.ref)
            live[(ref.scope, ref.fn_kind)] = ref
        elif e.kind == "obligate":
            obligations[(e.name, e.scope)] = e
        elif e.kind == "release":
            obligations.pop((e.name, e.scope), None)
    return live, obligations


def resolve(history, path: str, kind: str) -> tuple[str, tuple[str, ...], bool]:
    """(policy value, obligations, ambiguous) for one request."""
    live, obligations = live_state(history)
    hits = [
        e for (scope, fk), e in live.items()
        if _matches(scope, fk, path, kind)
    ]
    ambiguous = False
    if hits:
        best = max(_specificity(e.scope, e.fn_kind) for e in hits)
        top = [e for e in hits if _specificity(e.scope, e.fn_kind) == best]
        ambiguous = len({e.value for e in top}) > 1
        value = top[-1].value
    else:
        value = BASELINE
    obs = tuple(sorted({n for (n, scope) in obligations
                        if _matches(scope, None, path, kind)}))
    return value, obs, ambiguous


# ------------------------------------------------- the project and renderer


SUPPORT = '''\
"""Shared helpers.  Nothing here depends on the missing-entry policy."""


class MissingEntry(KeyError):
    """Raised when a lookup finds no entry and the policy says to raise."""


DEFAULT = {default}
CALLS = []


def note(name):
    """Record that a public function ran."""
    CALLS.append(name)
'''

INIT = '''\
"""{pkg}: rate tables for the billing pipeline.

Unless an instruction says otherwise, a missing entry yields DEFAULT.
"""
'''

MODULE_HEAD = '''\
"""{mod} rate lookups."""

from {dots}_support import DEFAULT, MissingEntry, note

'''

# path -> file inside the package.  `compat` is a real subpackage so that
# `compat.legacy` is a real nested scope and not a naming convention.
FILES = {
    "__init__": "__init__.py",
    "_support": "_support.py",
    "core": "core.py",
    "compat": "compat/__init__.py",
    "compat.legacy": "compat/legacy.py",
}
CODE_PATHS = ("core", "compat", "compat.legacy")


def render_impl(fname: str, kind: str, value: str, obligations,
                style: str = "gold") -> str:
    """The implementation a correct answer has to be BEHAVIOURALLY equal to.

    `style` selects between behaviourally identical spellings; the oracle must
    accept every one of them, which is what makes it a behavioural oracle and
    not a text comparison.
    """
    assert value in VALUES, value
    assert style in ("gold", "alt1", "alt2"), style
    sig = "table, key" if kind == "lookup" else "table, keys"
    out = [f"def {fname}({sig}):"]
    if "note" in obligations:
        out.append(f"    note({fname!r})")
    if kind == "lookup":
        if value == "raise":
            body = {
                "gold": ["    if key not in table:",
                         "        raise MissingEntry(key)",
                         "    return table[key]"],
                "alt1": ["    try:",
                         "        return table[key]",
                         "    except KeyError:",
                         "        raise MissingEntry(key) from None"],
                "alt2": ["    found = table.get(key, MissingEntry)",
                         "    if found is MissingEntry:",
                         "        raise MissingEntry(key)",
                         "    return found"],
            }[style]
        elif value == "none":
            body = {
                "gold": ["    return table.get(key)"],
                "alt1": ["    if key in table:",
                         "        return table[key]",
                         "    return None"],
                "alt2": ["    for candidate, found in table.items():",
                         "        if candidate == key:",
                         "            return found",
                         "    return None"],
            }[style]
        else:
            body = {
                "gold": ["    return table.get(key, DEFAULT)"],
                "alt1": ["    if key not in table:",
                         "        return DEFAULT",
                         "    return table[key]"],
                "alt2": ["    try:",
                         "        return table[key]",
                         "    except KeyError:",
                         "        return DEFAULT"],
            }[style]
    else:
        if value == "raise":
            body = {
                "gold": ["    out = []",
                         "    for key in keys:",
                         "        if key not in table:",
                         "            raise MissingEntry(key)",
                         "        out.append(table[key])",
                         "    return out"],
                "alt1": ["    for key in keys:",
                         "        if key not in table:",
                         "            raise MissingEntry(key)",
                         "    return [table[key] for key in keys]"],
                "alt2": ["    out = []",
                         "    for key in keys:",
                         "        try:",
                         "            out.append(table[key])",
                         "        except KeyError:",
                         "            raise MissingEntry(key) from None",
                         "    return out"],
            }[style]
        elif value == "none":
            body = {
                "gold": ["    return [table.get(key) for key in keys]"],
                "alt1": ["    out = []",
                         "    for key in keys:",
                         "        out.append(table[key] if key in table else None)",
                         "    return out"],
                "alt2": ["    out = []",
                         "    for key in keys:",
                         "        try:",
                         "            out.append(table[key])",
                         "        except KeyError:",
                         "            out.append(None)",
                         "    return out"],
            }[style]
        else:
            body = {
                "gold": ["    return [table.get(key, DEFAULT) for key in keys]"],
                "alt1": ["    out = []",
                         "    for key in keys:",
                         "        out.append(table[key] if key in table else DEFAULT)",
                         "    return out"],
                "alt2": ["    out = []",
                         "    for key in keys:",
                         "        try:",
                         "            out.append(table[key])",
                         "        except KeyError:",
                         "            out.append(DEFAULT)",
                         "    return out"],
            }[style]
    return "\n".join(out + body) + "\n"


ENTERING_FUNCS = (("lookup_price", "lookup"), ("gather_prices", "bulk"))


def entering_project(block: Block) -> dict[str, str]:
    """The repository both cases of the block start from.

    `core` and `compat` receive IDENTICAL bodies, so local code precedent is
    matched across the two applicability cases and cannot decide either of
    them.
    """
    mods = {
        "__init__": INIT.format(pkg="rates"),
        "_support": SUPPORT.format(default=DEFAULT_VALUE),
    }
    for path in CODE_PATHS:
        dots = "." if FILES[path].count("/") == 0 else ".."
        src = MODULE_HEAD.format(mod=path, dots=dots)
        for fname, kind in ENTERING_FUNCS:
            src += "\n" + render_impl(
                fname, kind, block.precedent, block.entering_obligations
            )
        mods[path] = src
    return mods


# ------------------------------------------------------------- the executor


class Candidate:
    """What an arm (or a shortcut policy) produces: edits to module sources."""

    def __init__(self, edits: dict[str, str], label: str = ""):
        self.edits = dict(edits)
        self.label = label


def apply_candidate(project: dict[str, str], candidate: Candidate) -> dict[str, str]:
    out = dict(project)
    out.update(candidate.edits)
    return out


def append_function(project: dict[str, str], module: str,
                    source: str) -> dict[str, str]:
    base = project[module]
    return {module: base + "\n" + source}


_BUILD = 0


def build(project: dict[str, str]):
    """Import the project as a real package and return its modules.

    The gate's candidates all come from `render_impl`, i.e. from this file, so
    they are trusted and run in process.  Model output is untrusted and goes
    through the repository's existing sandboxed execution path instead; this
    function is never the sandbox.
    """
    global _BUILD
    _BUILD += 1
    name = f"_scoped_blk_{_BUILD}"
    tmp = tempfile.mkdtemp(prefix="scoped-")
    root = Path(tmp) / name
    root.mkdir()
    for mod, src in project.items():
        target = root / FILES[mod]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(src)
    sys.path.insert(0, tmp)
    try:
        pkg = importlib.import_module(name)
        mods = {
            mod: importlib.import_module(f"{name}.{mod}")
            for mod in project if mod != "__init__"
        }
        mods["__init__"] = pkg
    finally:
        sys.path.remove(tmp)
        for key in [k for k in sys.modules if k.startswith(name)]:
            del sys.modules[key]
    return pkg, mods


MIXED = ("beta", MISSING, "alpha")


class _Probe(dict):
    """A table that records every access on the SAME timeline as note().

    Astra's finding 2: the obligation suite checked only membership in CALLS on
    a present-key call, so a function that logged after reading the table, or
    never logged on a failed lookup, passed.  Sharing one timeline makes
    "logs before it touches the table" observable.
    """

    def __init__(self, data, log):
        super().__init__(data)
        self._log = log

    def _seen(self, key):
        self._log.append(("access", key))

    def __getitem__(self, key):
        self._seen(key)
        return super().__getitem__(key)

    def get(self, key, *default):
        self._seen(key)
        return super().get(key, *default)

    def __contains__(self, key):
        self._seen(key)
        return super().__contains__(key)

    def __iter__(self):
        self._seen("*")
        return super().__iter__()

    def items(self):
        self._seen("*")
        return super().items()

    def keys(self):
        self._seen("*")
        return super().keys()


def _classify(got, support) -> str:
    if got is None:
        return "none"
    if got == support.DEFAULT:
        return "default"
    return f"other:{got!r}"


def observe(fn, kind: str, support) -> str:
    """Which of the three policy values does this function actually implement?

    Observed by RUNNING it.  The bulk case uses a MIXED batch and checks the
    present entries, their order and the result length, because Astra showed a
    function returning `[None]` for a three-key batch -- losing two present
    entries -- classified as `none` and passed every suite.  A raise is only a
    raise if it names the key that was missing.
    """
    try:
        if kind == "lookup":
            got = fn(_dict(), MISSING)
        else:
            got = fn(_dict(), list(MIXED))
    except support.MissingEntry as exc:
        if not exc.args or exc.args[0] != MISSING:
            return f"raise:wrong-key:{exc.args[:1]}"
        return "raise"
    except Exception as exc:  # noqa: BLE001 - any other failure is not a policy
        return f"error:{type(exc).__name__}"
    if kind == "lookup":
        return _classify(got, support)
    if not isinstance(got, list):
        return f"other:not-a-list:{type(got).__name__}"
    if len(got) != len(MIXED):
        return f"other:length-{len(got)}"
    if got[0] != PRESENT["beta"] or got[2] != PRESENT["alpha"]:
        return f"other:present-entries-lost:{got!r}"
    return _classify(got[1], support)


def _dict():
    return dict(PRESENT)


def present_behaviour_ok(fn, kind: str) -> bool:
    """Present keys come back correctly -- checked for NEW and EXISTING functions.

    Astra's finding 2: preservation compared only missing-entry classifications,
    so a new function that rebound an existing one to a broken lambda passed.
    """
    try:
        if kind == "lookup":
            return (fn(_dict(), "alpha") == PRESENT["alpha"]
                    and fn(_dict(), "beta") == PRESENT["beta"])
        empty = fn(_dict(), [])
        got = fn(_dict(), ["beta", "alpha"])
        return (isinstance(empty, list) and empty == []
                and isinstance(got, list) and got == [PRESENT["beta"],
                                                      PRESENT["alpha"]])
    except Exception:  # noqa: BLE001
        return False


def note_timeline(fn, kind: str, support, fname: str, key):
    """(logged, logged before any table access) for one invocation."""
    del support.CALLS[:]
    probe = _Probe(PRESENT, support.CALLS)
    try:
        fn(probe, key if kind == "lookup" else [key])
    except Exception:  # noqa: BLE001 - a raising policy still has to have logged
        pass
    timeline = list(support.CALLS)
    logged = fname in timeline
    if not logged:
        return False, False
    first_access = next((i for i, e in enumerate(timeline)
                         if isinstance(e, tuple)), len(timeline))
    return True, timeline.index(fname) < first_access


SUITES = ("functional", "contract", "preservation", "obligation")


def evaluate(block: Block, case: Case, candidate: Candidate) -> dict[str, bool]:
    """The hidden acceptance oracle: four executable suites.

    Its requirement is the case's HAND-FROZEN `expect_value` / `expect_note`, not
    anything the resolver computes, and it reads only observed behaviour of the
    built package -- never `render_impl`, the history, or the candidate's source
    text.
    """
    want_value, want_note = case.expect_value, case.expect_note
    project = apply_candidate(entering_project(block), candidate)
    scores = dict.fromkeys(SUITES, False)
    try:
        _pkg, mods = build(project)
    except Exception:  # noqa: BLE001
        return scores
    support = mods["_support"]
    fn = getattr(mods[case.path], case.fname, None)
    if fn is None:
        return scores

    # 1. functional: present keys come back, whatever the missing-entry policy is
    scores["functional"] = present_behaviour_ok(fn, case.fn_kind)

    # 2. applicable contract: the missing-entry behaviour the instructions require
    scores["contract"] = observe(fn, case.fn_kind, support) == want_value

    # 3. preservation: the ENTERING repository still behaves as it entered, in
    #    its present-key behaviour as well as its missing-entry policy.
    ok = True
    for path in CODE_PATHS:
        mod = mods[path]
        for fname, kind in ENTERING_FUNCS:
            existing = getattr(mod, fname, None)
            if existing is None:
                ok = False
                continue
            if not present_behaviour_ok(existing, kind):
                ok = False
            if observe(existing, kind, support) != block.precedent:
                ok = False
            logged, _order = note_timeline(existing, kind, support, fname, "alpha")
            if logged != ("note" in block.entering_obligations):
                ok = False
    scores["preservation"] = ok

    # 4. the obligation, on BOTH paths and in the right order.  "First statement"
    #    is syntactic and this oracle cannot see syntax, so the observable
    #    requirement is: it logs, before it touches the table, on a successful
    #    lookup AND on a missing one.
    hit = note_timeline(fn, case.fn_kind, support, case.fname, "alpha")
    miss = note_timeline(fn, case.fn_kind, support, case.fname, MISSING)
    if want_note:
        scores["obligation"] = all(hit) and all(miss)
    else:
        scores["obligation"] = not hit[0] and not miss[0]
    return scores


def passes(block: Block, case: Case, candidate: Candidate) -> bool:
    return all(evaluate(block, case, candidate).values())


# ----------------------------------------------------- candidates and policies


def _expected(case: Case) -> tuple[str, tuple[str, ...]]:
    return case.expect_value, (("note",) if case.expect_note else ())


def gold_candidate(block: Block, case: Case, style: str = "gold") -> Candidate:
    value, obs = _expected(case)
    project = entering_project(block)
    src = render_impl(case.fname, case.fn_kind, value, obs, style)
    return Candidate(append_function(project, case.path, src), f"gold/{style}")


def value_candidate(block: Block, case: Case, value: str, obs=()) -> Candidate:
    project = entering_project(block)
    src = render_impl(case.fname, case.fn_kind, value, obs)
    return Candidate(append_function(project, case.path, src), f"value/{value}")


def _policy_events(history):
    return [e for e in history if e.kind in ("set", "replace")]


def p_always_newest(block: Block, case: Case) -> str:
    """The most recent statement that names a value, whatever its scope."""
    events = _policy_events(block.history)
    return events[-1].value if events else BASELINE


def p_always_oldest(block: Block, case: Case) -> str:
    events = _policy_events(block.history)
    return events[0].value if events else BASELINE


def p_flip_on_cancel(block: Block, case: Case) -> str:
    """Any message using cancellation language flips back to the previous value.

    This is the heuristic UK drafting guidance explicitly rejects ("repealing a
    repeal does not revive the original enactment"), and the one a two-valued
    policy universe would make look competent.
    """
    events = _policy_events(block.history)
    value = events[0].value if events else BASELINE
    seen = []
    for e in block.history:
        if e.kind in ("set", "replace"):
            seen.append(e.value)
            value = e.value
        elif any(cue in e.text.lower() for cue in CANCEL_CUES) and len(seen) >= 2:
            value = seen[-2]
            seen = seen[:-1]
    return value


CANCEL_CUES = ("cancel", "drop the", "no longer", "not keeping", "withdraw",
               "scrap", "stop enforcing", "not enforcing")
MISSING_CUES = ("missing", "absent", "not in the table", "isn't in the table",
                "no entry", "isn't there")
VALUE_CUES = (("missingentry", "raise"), ("raise", "raise"), ("raising", "raise"),
              ("none", "none"), ("default", "default"))


def p_recency_general(block: Block, case: Case) -> str:
    """The nearest preceding message that reads like a missing-entry statement.

    Scope-blind and event-blind: it reads text, so a decoy in another part of
    the product (a CLI flag, a docs sentence) captures it.
    """
    for e in reversed(block.history):
        low = e.text.lower()
        if not any(cue in low for cue in MISSING_CUES):
            continue
        if e.value:
            return e.value
        for token, value in VALUE_CUES:
            if token in low:
                return value
    return BASELINE


SHORTCUTS = {
    "always_newest": p_always_newest,
    "always_oldest": p_always_oldest,
    "flip_on_cancel": p_flip_on_cancel,
    "recency_general": p_recency_general,
}


# The five trivial policies are all scope-blind, and a block whose two cases need
# different values refutes any scope-blind policy automatically.  That makes the
# uniform 16/16 defeat matrix cheap evidence.  These two RIVALS are scope-aware
# and wrong in exactly the way the literature warns about, so they pass some
# blocks and fail others -- which is what shows the instrument discriminates
# between semantics rather than merely refusing everything.


def p_scoped_recency(block: Block, case: Case) -> str:
    """Correct scoping, but the most RECENT applicable statement wins instead of
    the most SPECIFIC one."""
    live, _ = live_state(block.history)
    order = {e.id: i for i, e in enumerate(block.history)}
    hits = [e for (scope, fk), e in live.items()
            if _matches(scope, fk, case.path, case.fn_kind)]
    if not hits:
        return BASELINE
    return max(hits, key=lambda e: order[e.id]).value


def p_cancel_revives(block: Block, case: Case) -> str:
    """Correct scoping and specificity, but cancelling a policy revives the one
    it replaced -- the heuristic UK drafting guidance rejects."""
    live: dict[tuple[str, str | None], Event] = {}
    stacks: dict[tuple[str, str | None], list[Event]] = {}
    by_id = {e.id: e for e in block.history}
    for e in block.history:
        key = (e.scope, e.fn_kind)
        for scope in e.clears:
            for k in [k for k in live if k[0] == scope]:
                live.pop(k)
        if e.kind in ("set", "replace"):
            stacks.setdefault(key, []).append(e)
            live[key] = e
        elif e.kind == "cancel":
            stack = stacks.get(key, [])
            if stack:
                stack.pop()
            if stack:
                live[key] = stack[-1]  # the revival this policy wrongly performs
            else:
                live.pop(key, None)
        elif e.kind == "reinstate":
            ref = by_id[e.ref]
            live[(ref.scope, ref.fn_kind)] = ref
            stacks.setdefault((ref.scope, ref.fn_kind), []).append(ref)
    hits = [e for (scope, fk), e in live.items()
            if _matches(scope, fk, case.path, case.fn_kind)]
    if not hits:
        return BASELINE
    best = max(_specificity(e.scope, e.fn_kind) for e in hits)
    return [e for e in hits if _specificity(e.scope, e.fn_kind) == best][-1].value


def p_reinstate_first(block: Block, case: Case) -> str:
    """Correct in every respect except that reinstatement restores the FIRST
    policy ever stated at that scope, ignoring which statement was referenced."""
    live: dict[tuple[str, str | None], Event] = {}
    first: dict[tuple[str, str | None], Event] = {}
    by_id = {e.id: e for e in block.history}
    for e in block.history:
        key = (e.scope, e.fn_kind)
        for scope in e.clears:
            for k in [k for k in live if k[0] == scope]:
                live.pop(k)
        if e.kind in ("set", "replace"):
            first.setdefault(key, e)
            live[key] = e
        elif e.kind == "cancel":
            live.pop(key, None)
        elif e.kind == "reinstate":
            ref = by_id[e.ref]
            rkey = (ref.scope, ref.fn_kind)
            live[rkey] = first.get(rkey, ref)  # the mistake
    hits = [e for (scope, fk), e in live.items()
            if _matches(scope, fk, case.path, case.fn_kind)]
    if not hits:
        return BASELINE
    best = max(_specificity(e.scope, e.fn_kind) for e in hits)
    return [e for e in hits if _specificity(e.scope, e.fn_kind) == best][-1].value


RIVALS = {
    "scoped_recency": p_scoped_recency,
    "cancel_revives": p_cancel_revives,
    "reinstate_first": p_reinstate_first,
}
SHORTCUTS.update(RIVALS)

# `obligation_global` gets the POLICY right and the obligation's SCOPE wrong, so
# it is handled where obligations are chosen rather than where values are.
OBLIGATION_POLICIES = ("obligation_global",)


def _policy_result(block: Block, case: Case, policy: str):
    """(value, obligations) for one policy.  Every policy answers both, because
    a shortcut can be wrong about either."""
    value, obs = _expected(case)
    if policy in ("copy_existing", "rollback"):
        return value, obs
    if policy == "obligation_global":
        names = {name for (name, _scope) in live_state(block.history)[1]}
        return value, tuple(sorted(names))
    return SHORTCUTS[policy](block, case), obs


def shortcut_candidate(block: Block, case: Case, policy: str) -> Candidate:
    """`copy_existing` and `rollback` are structural, the rest choose a value."""
    project = entering_project(block)
    value, obs = _policy_result(block, case, policy)
    if policy == "copy_existing":
        # Copy the entering implementation in this very module, obligations and all.
        src = render_impl(case.fname, case.fn_kind, block.precedent,
                          block.entering_obligations)
        return Candidate(append_function(project, case.path, src), policy)
    if policy == "rollback":
        # Whole-state rollback to the reinstated moment: the resolved value is
        # even correct, but every module is rewritten to it and every obligation
        # added since is rolled back with it.  git revert records a reversal; it
        # does not delete the ancestry, and neither may a correct answer.
        rolled = replace(block, precedent=value, entering_obligations=())
        project = entering_project(rolled)
        src = render_impl(case.fname, case.fn_kind, value, ())
        edits = dict(project)
        edits.update(append_function(project, case.path, src))
        return Candidate(edits, policy)
    src = render_impl(case.fname, case.fn_kind, value, obs)
    return Candidate(append_function(project, case.path, src), policy)


POLICIES = (*SHORTCUTS, *OBLIGATION_POLICIES, "copy_existing", "rollback")
TRIVIAL = ("always_newest", "always_oldest", "flip_on_cancel", "recency_general",
           "copy_existing", "rollback")
REQUIRED_FIVE = ("always_newest", "always_oldest", "flip_on_cancel",
                 "copy_existing", "recency_general")


# --------------------------------------------------------- the model's view


LABEL_KEYS = ("kind", "scope", "fn_kind", "value", "ref", "name", "id",
              "family", "defeats", "precedent", "history", "cases", "note")


def arm_payload(block: Block, case: Case, variant: str = "revised") -> dict:
    """Exactly what an arm may see.  No event labels, no gold, no applicability.

    Astra's gate: "source metadata cannot reach the automatic arm".
    """
    assert variant in ("revised", "direct", "irrelevant"), variant
    return {
        "messages": [{"role": "user", "text": e.text}
                     for e in history_variant(block, variant)],
        "repo": entering_project(block),
        "request": {
            "module": FILES[case.path],
            "function": case.fname,
            "signature": "table, key" if case.fn_kind == "lookup" else "table, keys",
            "text": _request_text(case),
        },
    }


def _request_text(case: Case) -> str:
    where = FILES[case.path]
    if case.fn_kind == "lookup":
        return (f"Add {case.fname}(table, key) to {where}: it returns the entry "
                f"for key from table.")
    # The container is part of the public contract: Astra found a correct
    # tuple-returning answer failing an unstated list requirement.
    return (f"Add {case.fname}(table, keys) to {where}: it returns a list of the "
            f"entries for keys from table, in the same order as keys.")


CONVENTIONS = """How instructions work in this project:
- An instruction governs work done after it. Existing code is not rewritten
  unless the instruction says so.
- When two instructions could both apply, the more specific one wins: a rule for
  one package or file beats a package-wide rule, and a rule naming one kind of
  operation beats one that names none.
- Cancelling an instruction removes it. It does not bring back whatever that
  instruction replaced: what applies next is the next rule that still covers this
  code, or the package default if there is none.
- An instruction can explicitly put an earlier one back into force.
"""


def history_variant(block: Block, variant: str):
    """The economics contrast: the same final rule, reached three ways.

    Gonc,alves, Libgober and Willis compare retracted information with both
    never-presented information and informationally equivalent DIRECT
    information; holding the repository and the requested edit fixed makes the
    executable gap attributable to processing the history.
    """
    if variant == "revised":
        return list(block.history)
    live, obligations = live_state(block.history)
    direct = []
    for i, ((scope, fn_kind), e) in enumerate(sorted(
            live.items(), key=lambda kv: _specificity(*kv[0]))):
        direct.append(Event(id=f"d{i}", kind="set", scope=scope, fn_kind=fn_kind,
                            value=e.value, text=_direct_text(scope, fn_kind, e.value)))
    for i, (name, scope) in enumerate(sorted(obligations)):
        direct.append(Event(id=f"do{i}", kind="obligate", name=name, scope=scope,
                            text=OBLIGATION_TEXT[name]))
    if variant == "direct":
        return direct
    padded = []
    for i, e in enumerate(direct):
        padded.append(e)
        padded.append(Event(id=f"n{i}", text=NOISE[i % len(NOISE)]))
    return padded


SCOPE_WORDS = {"*": "across the package", "core": "inside core.py",
               "compat": "inside compat.py", "compat.legacy": "inside the legacy"
                                                              " part of compat.py"}
VALUE_WORDS = {
    "raise": "a key that isn't in the table must raise MissingEntry",
    "none": "a key that isn't in the table comes back as None",
    "default": "a key that isn't in the table comes back as DEFAULT",
}
OBLIGATION_TEXT = {
    "note": "Every public function in the package calls note() with its own "
            "name as its first statement, so the audit log stays complete.",
}
NOISE = (
    "Keep the commit subject lines under seventy characters.",
    "We're standardising on double quotes in this package.",
    "The changelog entry goes in the pull request body, not a file.",
    "Type annotations are optional here; don't add them just for style.",
)


def _direct_text(scope: str, fn_kind: str | None, value: str) -> str:
    op = "" if fn_kind is None else f" for {fn_kind} operations"
    return f"{SCOPE_WORDS[scope].capitalize()}{op}, {VALUE_WORDS[value]}."


# ------------------------------------------------------------------ manifest


def block_digest(block: Block) -> str:
    payload = json.dumps({
        "id": block.id, "family": block.family, "precedent": block.precedent,
        "history": [e.__dict__ for e in block.history],
        "cases": [c.__dict__ for c in block.cases],
        "entering_obligations": list(block.entering_obligations),
    }, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


# ------------------------------------------------- the oracle-reminder arm


def resolve_events(history, path: str, kind: str):
    """(the statement that establishes the live policy, the obligation statements).

    The reminder quotes SOURCE TEXT.  Astra's constraint on the diagnostic arm:
    "The oracle supplies the instruction, not code, expected test outputs, or a
    gold patch."  Nothing here is derived from the answer -- for a reinstated
    rule this returns the ORIGINAL statement, which is what the reinstatement
    refers to.
    """
    live, obligations = live_state(history)
    hits = [e for (scope, fk), e in live.items() if _matches(scope, fk, path, kind)]
    winner = None
    if hits:
        best = max(_specificity(e.scope, e.fn_kind) for e in hits)
        winner = [e for e in hits if _specificity(e.scope, e.fn_kind) == best][-1]
    ob_events = [e for (_name, scope), e in obligations.items()
                 if _matches(scope, None, path, kind)]
    ob_events.sort(key=lambda e: [x.id for x in history].index(e.id))
    return winner, ob_events


BASELINE_LINE = ("No instruction in this session covers this file and operation, "
                 "so the package's documented default applies.")


def oracle_reminder(block: Block, case: Case, history=None) -> str:
    """The compact action cue: which instruction applies HERE, and its source."""
    history = list(block.history if history is None else history)
    index = {e.id: i for i, e in enumerate(history)}
    winner, obligations = resolve_events(history, case.path, case.fn_kind)
    lines = ["Instruction in force for this edit:"]
    if winner is None:
        lines.append(f"- {BASELINE_LINE}")
    else:
        lines.append(f'- message {index[winner.id] + 1}: "{winner.text}"')
    for e in obligations:
        lines.append(f'- message {index[e.id] + 1}: "{e.text}"')
    return "\n".join(lines)


def rescue_prompts(block: Block, case: Case, token_len, budget: int,
                   variant: str = "revised") -> dict:
    """Both conditions at an EQUAL total token count.

    Condition `off` is ordinary recency packing.  Condition `oracle` renders the
    reminder immediately before the request and shortens the history window by
    exactly the reminder's token count, so the two prompts have the same size and
    the comparison is not a context-length comparison.  `token_len` is a callable
    so this is testable without a tokenizer.
    """
    history = list(history_variant(block, variant))
    request = _request_text(case)
    project = entering_project(block)
    # The package docstring carries the documented default, and the conventions
    # state the protocol the hidden oracle enforces.  Astra's finding 3: without
    # the docstring, C4/core asks the model to follow documentation it was never
    # shown.  Both are task specification and go to BOTH conditions identically.
    head = (f"You are editing the `rates` package.\n\n"
            f"__init__.py:\n```python\n{project['__init__']}```\n\n"
            f"{CONVENTIONS}\n"
            f"{FILES[case.path]}:\n```python\n{project[case.path]}```\n")
    tail = f"\n{request}\nReply with the single new function and nothing else.\n"
    reminder = oracle_reminder(block, case, history)

    def pack(extra: str) -> tuple[str, list[int]]:
        fixed = token_len(head + extra + tail)
        kept, used = [], fixed
        for i in range(len(history) - 1, -1, -1):
            line = f"message {i + 1}: {history[i].text}\n"
            cost = token_len(line)
            if used + cost > budget:
                break
            used += cost
            kept.append(i)
        kept.reverse()
        body = "".join(f"message {i + 1}: {history[i].text}\n" for i in kept)
        return head + body + extra + tail, kept

    off, off_kept = pack("")
    on, on_kept = pack("\n" + reminder + "\n")
    return {
        "off": {"prompt": off, "kept": off_kept, "tokens": token_len(off)},
        "oracle": {"prompt": on, "kept": on_kept, "tokens": token_len(on),
                   "reminder": reminder},
    }
