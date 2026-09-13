"""Mutation-audit the candidate-A scorer (registration section 14.8).

Answers the question the Astra re-review called the whole issue: can a
session score J = 1 while the repository is actually wrong?  Seven classes of
plausible reply damage are applied one at a time to the gold of BOTH
checkpoints of every SCREEN slot, and each mutation must be caught by some
suite of that checkpoint.  The audit found 12 undetected mutations in
pre-existing operations that no regression test pinned, then 65 more as
classes were added; after those were pinned it runs at 0.  A new slot or a
changed regression test must keep it at 0.

Round 5, F1: the update-site classes (4-6) resolved a site's record type from
the first argument's VARIABLE NAME and silently skipped what it could not
resolve, so 13 sites across eight slots were never mutated and 11 more -- the
``replace(self._entries[entry_id], ...)`` and ``replace(table.get_shift(id),
...)`` forms -- were never even matched.  One of the skipped sites hid an
undetected identity corruption.  Sites are now found in the AST and typed by
local inference (assignment, mapping annotation, method return annotation,
parameter annotation, naming convention), every resolution is validated
against the keywords the call already passes, and an UNRESOLVED site is a
visible failure, never a silent skip.

Round 5, F2: only checkpoint 2 was mutated, so a wrong FIRST repository that
the ordinary second gold repairs scored J = 1 (S01's allocator reset in
``scale_recipe``).  Both checkpoints are mutated and scored now.

Usage: ``uv run python scripts/a_screen_mutate.py``; exit 1 if any mutation
is undetected or any update site cannot be typed.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from collections.abc import Iterator
from dataclasses import dataclass, field

from stencil import a_screen as A
from stencil.a_screen_pool import available_slots, load


def record_classes(files: dict[str, str]) -> dict[str, dict[str, str | None]]:
    """``{ClassName: {field: default or None}}`` for every dataclass in the project.

    Round 4, low: an earlier version pooled every default across every record type, so a
    mutation could name a field the updated type does not have.  That fails with
    "unexpected keyword argument", which detects a wrong keyword rather than an erased
    attribute, and `stencil.contracts.run_tests` returns pytest's short summary
    ("1 failed in 0.02s"), so the distinction is invisible downstream.  Fields are
    associated with their own class here and emitted only for that class.
    """
    out: dict[str, dict[str, str | None]] = {}
    for src in files.values():
        for m in re.finditer(
            r"@dataclass[^\n]*\nclass (\w+)[^\n]*:\n((?:    [^\n]*\n|\n)+)", src
        ):
            fields: dict[str, str | None] = {}
            for line in m.group(2).split("\n"):
                fm = re.match(r"    (\w+): [^=\n]+?(?: = (.+))?$", line)
                if fm and not line.strip().startswith("def "):
                    fields[fm.group(1)] = fm.group(2).strip() if fm.group(2) else None
            if fields:
                out[m.group(1)] = fields
    return out


def class_of(
    var: str, classes: dict[str, dict[str, str | None]] | set[str]
) -> str | None:
    """The record class a local variable holds, by this pool's naming convention
    (``hold`` -> ``Hold``, ``recipe`` -> ``Recipe``).  The weakest of the resolution
    rules in ``_Types``, used only when no assignment, annotation or return type
    types the name; a resolution it produces is still validated against the keywords
    the call passes, so a wrong guess surfaces as UNRESOLVED rather than as a mutant
    naming a foreign field."""
    for name in classes:
        if var.lower() == name.lower() or var.lower().endswith("_" + name.lower()):
            return name
    return None


# Round 7, low: dropping an ambiguous name from the env was not enough -- ``_expr_type``
# fell back to ``class_of``, so ``a = B(); replace(a, ...); a = A()`` resolved as A
# while the updated object is B.  Recorded ambiguity is now a VALUE in the env that no
# resolution rule may see past, so such a site is UNRESOLVED and the audit exits 1.
AMBIGUOUS = "\x00ambiguous"


def defaulted_fields(files: dict[str, str]) -> list[tuple[str, str]]:
    """(field, default) for every dataclass attribute in the project that has a default.
    Resetting one of these is how a reply silently erases an unrelated attribute."""
    out = []
    for cls in record_classes(files).values():
        for fname, default in cls.items():
            if default is not None:
                out.append((fname, default))
    return out


def required_fields(files: dict[str, str]) -> list[str]:
    """Every dataclass attribute with NO default — the record's identity and its
    other mandatory data.  Round 4's S01 escape changed one of these during an
    update (``replace(recipe, recipe_id=tag, ...)``): tags, servings, title and the
    neighbours were all preserved, so every suite passed while the record's own id
    had been replaced.  Audited separately from the defaulted fields."""
    out = []
    for src in files.values():
        if "@dataclass" not in src:
            continue
        for m in re.finditer(r"\n    (\w+): [^\n=]+(?= *\n)", src):
            name = m.group(1)
            if name not in out:
                out.append(name)
    return out


def counters(src: str) -> list[str]:
    """Attributes the target increments to allocate new ids (``self._counter += 1``).
    Resetting one disturbs no record already stored, so a fixture that only checks
    existing records cannot see it: the NEXT insertion silently reuses a live id and
    overwrites an earlier record (round 4)."""
    return sorted({m.group(1) for m in re.finditer(r"self\.(_\w+) \+= 1", src)})


# ------------------------------------------------------- round 5 F1: site typing


@dataclass
class Types:
    """Everything needed to type an update site's first argument, collected from ALL
    project files so a call can be typed across module boundaries.

    ``names`` is every class in the project (records and storage classes alike, because
    ``self`` and a storage handle must resolve before their attributes can).  ``attrs``
    maps (class, attribute) to the class the attribute CONTAINS (``self._shifts:
    dict[str, Shift]`` -> ``Shift``), which is what both ``self._shifts[k]`` and
    ``self._shifts.get(k)`` evaluate to.  ``returns`` maps (class, method) to its return
    annotation's class, which types the ``replace(table.get_shift(id), ...)`` form."""

    names: set[str] = field(default_factory=set)
    attrs: dict[tuple[str, str], str] = field(default_factory=dict)
    returns: dict[tuple[str, str], str] = field(default_factory=dict)


def _ann_type(node: ast.AST | None, names: set[str]) -> str | None:
    """The project class an annotation denotes: ``Shift``, ``Shift | None`` and
    ``dict[str, Shift]`` all denote ``Shift``."""
    if node is None:
        return None
    for sub in ast.walk(node):
        if isinstance(sub, ast.Name) and sub.id in names:
            return sub.id
        if isinstance(sub, ast.Constant) and sub.value in names:
            return str(sub.value)  # a string annotation: "Shift"
    return None


def build_types(files: dict[str, str]) -> Types:
    """Collect class names, attribute types and method return types from every file."""
    trees = {p: ast.parse(src) for p, src in files.items() if p.endswith(".py")}
    t = Types()
    for tree in trees.values():
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                t.names.add(node.name)
    for tree in trees.values():
        for cls in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
            for node in ast.walk(cls):
                if isinstance(node, ast.AnnAssign):
                    a = _self_attr(node.target)
                    got = _ann_type(node.annotation, t.names)
                    if a and got:
                        t.attrs[(cls.name, a)] = got
            for fn in cls.body:
                if isinstance(fn, ast.FunctionDef):
                    got = _ann_type(fn.returns, t.names)
                    if got:
                        t.returns[(cls.name, fn.name)] = got
    # A slot with no type hints at all (S33) annotates neither its mapping nor its
    # methods, so the only evidence of what ``self._rows`` holds is what the class
    # STORES in it.  Three passes because an env needs the attribute types that a
    # later pass infers.
    for _ in range(3):
        for tree in trees.values():
            for cls_name, fn in _scopes(tree):
                if cls_name is None:
                    continue
                env = _env(fn, cls_name, t)
                for node in ast.walk(fn):
                    if not isinstance(node, ast.Assign):
                        continue
                    for tgt in node.targets:
                        if not isinstance(tgt, ast.Subscript):
                            continue
                        attr = _self_attr(tgt.value)
                        got = _expr_type(node.value, t, env)
                        if attr and got and (cls_name, attr) not in t.attrs:
                            t.attrs[(cls_name, attr)] = got
    return t


def _root_name(node: ast.AST | None) -> str | None:
    """The variable an expression is built from: ``replace(order, note=x)`` ->
    ``order``."""
    while node is not None:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute | ast.Subscript):
            node = node.value
        elif isinstance(node, ast.Call):
            # a METHOD call's record is its receiver (``rec.with_note(x)`` -> ``rec``);
            # a plain call's is its first argument (``replace(rec, note=x)`` -> ``rec``)
            node = (
                node.func.value
                if isinstance(node.func, ast.Attribute)
                else (node.args[0] if node.args else node.func)
            )
        else:
            return None
    return None


def whole_record_writers(files: dict[str, str], names: set[str]) -> set[str]:
    """Every record class a CALLER can store whole, so it can put a record carrying any
    field value into the project's state.

    Three conditions, all needed.  The method must be PUBLIC (a private helper is not
    reachable from a suite); it must assign an expression of that class into one of
    its own attributes (``self._orders[order.order_id] = order``); and that expression
    must derive from one of the method's own PARAMETERS.  The last condition separates
    S35's ``OrderBook.save(order)``, which stores whatever the caller hands it, from
    the 40 slots whose public methods store a record they BUILT themselves and then
    store it: a caller cannot choose a field value through those, so a reset of an
    otherwise unwritten defaulted field is unobservable there.  Types come from the
    same machinery the update sites use, so a parameter typed only by this pool's
    naming convention still resolves.
    """
    t = build_types(files)
    out: set[str] = set()
    for src in files.values():
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for cls_name, fn in _scopes(tree):
            if cls_name is None or fn.name.startswith("_"):
                continue
            env = _env(fn, cls_name, t)
            params = set()
            for arg in list(fn.args.args) + list(fn.args.kwonlyargs):
                if arg.arg == "self":
                    continue
                params.add(arg.arg)
                # a parameter annotated or named for a record class can be the payload
                got = _ann_type(arg.annotation, names) or class_of(arg.arg, names)
                if got:
                    env.setdefault(arg.arg, got)
            for node in ast.walk(fn):
                if not isinstance(node, ast.Assign):
                    continue
                got = _expr_type(node.value, t, env)
                if got not in names or _root_name(node.value) not in params:
                    continue
                for tgt in node.targets:
                    base = tgt.value if isinstance(tgt, ast.Subscript) else tgt
                    if _self_attr(base):
                        out.add(got)
    return out


def writable_fields(
    files: dict[str, str], classes: dict[str, dict[str, str | None]]
) -> dict[str, set[str]]:
    """{ClassName: {defaulted fields some code here can actually set}}.

    Round 5 F2 asks for the corruption checks at both checkpoints "where they change
    publicly reachable behavior".  A DEFAULTED field that nothing in the project assigns
    is at its default on every record that can exist, so resetting it to that default
    leaves the repository behaving identically: no public suite can detect it, and
    demanding detection would force a fixture to seed state through private storage or
    force the project source to grow a writer it has no use for.  S32's ``Loan.status``
    and ``Loan.condition`` are only written by the operation request 2 adds, so at
    checkpoint 1 they are not writable; at checkpoint 2 they are, and the mutants are
    emitted and must be caught.

    A field counts as writable if any code passes it by keyword (``status=``, including
    through a ``with_status``/``with_changes`` helper) or constructs the record with
    enough positional arguments to reach it.

    Round 6 F7: a class with a WHOLE-RECORD PUBLIC WRITER has every defaulted field
    writable, whatever the project source happens to pass.  ``OrderBook.save(order)``
    stores an arbitrary ``Order``, so ``book.save(replace(order, note="no nuts"))`` sets
    ``Order.note`` from outside the project and a reset of it in ``ready`` IS publicly
    reachable.  The keyword scan alone missed that and dropped two real S35 mutants.
    """
    out = {cls: set() for cls in classes}
    for cls in whole_record_writers(files, set(classes)):
        out[cls] = {f for f, d in classes[cls].items() if d is not None}
    for src in files.values():
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            for kw in node.keywords:
                if kw.arg:
                    for cls, fields in classes.items():
                        if kw.arg in fields and fields[kw.arg] is not None:
                            out[cls].add(kw.arg)
            if isinstance(node.func, ast.Name) and node.func.id in classes:
                names = list(classes[node.func.id])
                for field_name in names[: len(node.args)]:
                    if classes[node.func.id][field_name] is not None:
                        out[node.func.id].add(field_name)
    return out


def _self_attr(node: ast.AST) -> str | None:
    """``self._tools`` -> ``_tools``, anything else -> ``None``."""
    if (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "self"
    ):
        return node.attr
    return None


def _expr_type(node: ast.AST | None, t: Types, env: dict[str, str]) -> str | None:
    """The project class an expression evaluates to, or ``None``."""
    if node is None:
        return None
    if isinstance(node, ast.Name):
        got = env.get(node.id)
        if got == AMBIGUOUS:
            return None  # round 7: ambiguity overrides every later resolution rule
        return got or class_of(node.id, t.names)
    if isinstance(node, ast.Attribute):
        base = _expr_type(node.value, t, env)
        return t.attrs.get((base, node.attr)) if base else None
    if isinstance(node, ast.Subscript):  # self._shifts[k] -> the contained class
        return _expr_type(node.value, t, env)
    if isinstance(node, ast.Call):
        fn = node.func
        if isinstance(fn, ast.Name):
            if fn.id in t.names:
                return fn.id
            if fn.id == "replace" and node.args:
                return _expr_type(node.args[0], t, env)
            return None
        if isinstance(fn, ast.Attribute):
            if fn.attr.startswith("with_") or fn.attr == "get":
                return _expr_type(fn.value, t, env)
            if fn.attr == "replace" and node.args:  # dataclasses.replace(...)
                return _expr_type(node.args[0], t, env)
            base = _expr_type(fn.value, t, env)
            return t.returns.get((base, fn.attr)) if base else None
    return None


def _scopes(tree: ast.Module) -> list[tuple[str | None, ast.FunctionDef]]:
    """(enclosing class or None, function) for every function in the module."""
    out, seen = [], set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for fn in node.body:
                if isinstance(fn, ast.FunctionDef):
                    out.append((node.name, fn))
                    seen.add(id(fn))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and id(node) not in seen:
            out.append((None, node))
    return out


def _env(fn: ast.FunctionDef, cls: str | None, t: Types) -> dict[str, str]:
    """Types of the locals and parameters of one function.  Three passes because
    ``ast.walk`` is breadth-first: a name assigned inside an ``if`` can be read by a
    statement the walk reaches first.

    Round 6, Astra's general-soundness note: the passes read assignments from the
    WHOLE function, so ``old = A(...); replace(old, ...); old = B(...)`` typed ``old``
    as ``B`` while the call updates an ``A``.  A name assigned TWO different classes in
    one function is therefore dropped from the env rather than resolved to the last
    one; the site is then UNRESOLVED and the audit fails loudly instead of mutating a
    field of the wrong class.  No frozen site is affected (0 unresolved)."""
    env: dict[str, str] = {}
    if cls:
        env["self"] = cls
    for arg in list(fn.args.args) + list(fn.args.kwonlyargs):
        got = _ann_type(arg.annotation, t.names)
        if got:
            env[arg.arg] = got
    ambiguous: set[str] = set()
    for _ in range(3):
        for node in ast.walk(fn):
            target = value = None
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                target = node.target.id
                got = _ann_type(node.annotation, t.names)
                if got:
                    env[target] = got
                    continue
                value = node.value
            elif (
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
            ):
                target, value = node.targets[0].id, node.value
            if target is None:
                continue
            got = _expr_type(value, t, env)
            if got and got != AMBIGUOUS:
                if env.get(target, got) not in (got, AMBIGUOUS):
                    ambiguous.add(target)
                env[target] = AMBIGUOUS if target in ambiguous else got
    return {k: (AMBIGUOUS if k in ambiguous else v) for k, v in env.items()}


@dataclass
class Site:
    """One update call in the source: ``replace(rec, ...)`` or ``rec.with_X(...)``."""

    start: int  # offset of the call
    end: int  # offset just past the call
    insert_at: int  # offset just past the first argument
    text: str  # the call's source
    helper: bool  # a with_X(...) site, which is mutated by wrapping
    cls: str | None  # the record class being updated, None = UNRESOLVED
    already: set[str]  # fields this call sets on purpose
    why: str  # the reason a resolution was rejected, for the report
    where: str  # the function the call is in, so a report names the operation


def _line_offsets(src: str) -> list[int]:
    offs, pos = [0], 0
    for line in src.splitlines(keepends=True):
        pos += len(line)
        offs.append(pos)
    return offs


def update_sites(
    src: str, classes: dict[str, dict[str, str | None]], t: Types
) -> list[Site]:
    """Every record-update call in ``src``, each typed or explicitly unresolved.

    A ``replace`` whose first argument is a literal is ``str.replace`` and is not a
    record update at all, so it is dropped rather than reported.  A resolution is
    REJECTED when the call already passes a keyword the resolved class does not have:
    that is the signature of a mis-resolution, and emitting its fields would produce
    mutants that fail with "unexpected keyword argument" -- a detected wrong keyword
    rather than an erased attribute."""
    if not src.isascii():
        raise ValueError("non-ASCII source: byte and character offsets diverge")
    tree = ast.parse(src)
    offs = _line_offsets(src)

    def off(node: ast.AST, end: bool = False) -> int:
        line = node.end_lineno if end else node.lineno
        col = node.end_col_offset if end else node.col_offset
        return offs[line - 1] + col

    sites: list[Site] = []
    for cls_name, fn in _scopes(tree):
        env = _env(fn, cls_name, t)
        for node in ast.walk(fn):
            if not isinstance(node, ast.Call):
                continue
            f = node.func
            first: ast.AST | None = None
            helper = False
            suffix = ""
            if isinstance(f, ast.Name) and f.id == "replace" and node.args:
                first = node.args[0]
            elif isinstance(f, ast.Attribute) and f.attr == "replace" and node.args:
                first = node.args[0]
            elif isinstance(f, ast.Attribute) and f.attr.startswith("with_"):
                first, helper = f.value, True
                suffix = f.attr[len("with_") :]
            if first is None:
                continue
            if isinstance(first, ast.Constant):
                continue  # str.replace(" ", "-"), not a record update
            already = {kw.arg for kw in node.keywords if kw.arg}
            cls = _expr_type(first, t, env)
            why = ""
            if cls is None:
                why = f"cannot type {ast.get_source_segment(src, first)!r}"
            elif cls not in classes:
                why = f"{cls} is not a record class"
                cls = None
            elif not already <= set(classes[cls]):
                why = f"{cls} has none of {sorted(already - set(classes[cls]))}"
                cls = None
            elif helper and suffix in classes[cls]:
                already.add(suffix)  # ``with_status(...)`` sets ``status`` on purpose
            sites.append(
                Site(
                    start=off(node),
                    end=off(node, end=True),
                    insert_at=off(first, end=True),
                    text=ast.get_source_segment(src, node) or "",
                    helper=helper,
                    cls=cls,
                    already=already,
                    why=why,
                    where=fn.name,
                )
            )
    return sites


def mutants(
    src: str,
    classes: dict[str, dict[str, str | None]],
    t: Types,
    writable: dict[str, set[str]] | None = None,
) -> Iterator[tuple[str, str]]:
    """Each (label, mutated source).  Seven classes a plausible reply can produce, all
    of which leave the repository wrong: a lookup that starts raising; a write-back that
    is gone; a write-back that REPLACES the whole mapping and so deletes unrelated
    records; an update that resets an unrelated defaulted attribute, at a ``replace(``
    call site and again through a ``with_X(...)`` record helper; an update that changes
    a REQUIRED field, so the record keeps every other value but loses its identity; and
    a reset of the id allocator, which corrupts the next insertion rather than any
    record already stored.  The last two are round 4's demonstrated escapes."""
    for m in re.finditer(r"\.get\((\w+)\)", src):
        yield (
            f"get->[] @{m.start()}",
            src[: m.start()] + f"[{m.group(1)}]" + src[m.end() :],
        )
    for m in re.finditer(r"\n(\s+)(self\._(\w+)\[(\w+)\] = (\w+))\n", src):
        yield (
            f"drop write-back @{m.start()}",
            src[: m.start()] + "\n" + src[m.end() :],
        )
        indent, mapping, key, val = m.group(1), m.group(3), m.group(4), m.group(5)
        yield (
            f"write-back replaces the whole mapping @{m.start()}",
            src[: m.start()]
            + f"\n{indent}self._{mapping} = {{{key}: {val}}}\n"
            + src[m.end() :],
        )
    # Classes 4-6: an update that keeps the visible change but additionally resets an
    # unrelated DEFAULTED attribute, or replaces a REQUIRED one (typically the record's
    # own id -- round 4's S01 escape).  A ``replace(`` site takes the extra keyword
    # directly; a ``rec.with_X(...)`` helper site has no keyword list, so the call is
    # WRAPPED, with an explicit import prepended so the mutant always compiles and a
    # failure means the suites caught the change, not a NameError (group-8 agent report,
    # round 3).  Unresolved sites are reported by main(), never skipped silently.
    for site in update_sites(src, classes, t):
        if site.cls is None:
            continue
        can_set = (writable or {}).get(site.cls)
        for fname, default in classes[site.cls].items():
            if fname in site.already:
                continue  # the call already sets this field on purpose
            if default is not None and can_set is not None and fname not in can_set:
                continue  # nothing at this checkpoint can make it non-default
            value = default if default is not None else '"_audit"'
            what = "reset" if default is not None else "set required"
            kind = "helper " if site.helper else ""
            if site.helper:
                mutated = (
                    "import dataclasses as _audit_dc\n"
                    + src[: site.start]
                    + f"_audit_dc.replace({site.text}, {fname}={value})"
                    + src[site.end :]
                )
            else:
                mutated = (
                    src[: site.insert_at] + f", {fname}={value}" + src[site.insert_at :]
                )
            yield (
                f"{kind}{what} {site.cls}.{fname} to {value} "
                f"in {site.where} @{site.start}",
                mutated,
            )

    # Class 7 (round 4): reset the id allocator at the top of a method that is not
    # itself the allocator.  Nothing already stored changes, so only a fixture that
    # CREATES a record after the update can see the new record reuse a live id.
    # Restricted to methods that already WRITE state: a reply might plausibly clobber a
    # counter while editing an update operation, but not inside a pure reader, and
    # generating the reader cases would inflate the count without adding coverage.
    for counter in counters(src):
        for m in re.finditer(r"\n    def (\w+)\(self[^\n]*\n", src):
            name = m.group(1)
            if name.startswith("_"):
                continue
            end = src.find("\n    def ", m.end())
            body = src[m.end() : end if end != -1 else len(src)]
            if f"self.{counter} += 1" in body or f"self.{counter} =" in body:
                continue  # this IS the allocator, or already assigns it
            if not re.search(r"self\._\w+(\[[^\]]*\])? *=|\.append\(|\.write", body):
                continue  # a pure reader: not a plausible place for a reply to do this
            yield (
                f"reset allocator self.{counter} in {name} @{m.start()}",
                src[: m.end()] + f"        self.{counter} = 0\n" + src[m.end() :],
            )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--slots", default="", help="comma-separated subset, default all 48"
    )
    a = ap.parse_args()
    slots = a.slots.split(",") if a.slots else available_slots()
    undetected: list[tuple[str, str, str]] = []
    unresolved: list[str] = []
    total = 0
    for slot in slots:
        s = load(slot)
        for k in (1, 2):
            # at checkpoint 1 only request 1's target has been written by the model;
            # at checkpoint 2 both targets carry a reply (round 5 F2)
            paths = (
                [s.requests[0].target]
                if k == 1
                else sorted({r.target for r in s.requests})
            )
            fk = A.gold_files(s, k)
            base = A.score_checkpoint(s, k, fk)
            if not base["all"]:
                print(f"{slot}@{k}: GOLD FAILS, cannot audit")
                undetected.append((f"{slot}@{k}", "-", "gold fails"))
                continue
            classes = record_classes(fk)
            types = build_types(fk)
            writable = writable_fields(fk, classes)
            for path in paths:
                for site in update_sites(fk[path], classes, types):
                    if site.cls is None:
                        unresolved.append(
                            f"{slot}@{k} {path}: {site.text} -- {site.why}"
                        )
                for label, mut in mutants(fk[path], classes, types, writable):
                    if mut == fk[path]:
                        continue
                    total += 1
                    try:
                        res = A.score_checkpoint(s, k, {**fk, path: mut})
                    except Exception as exc:  # a crash is a detection, but say so
                        print(
                            f"{slot}@{k} {path} {label}: scorer raised "
                            f"{type(exc).__name__}"
                        )
                        continue
                    if res["all"]:
                        undetected.append((f"{slot}@{k}", path, label))
        print(f"{slot}: done ({total} mutations so far)")
    print(
        f"\nmutations applied: {total}   UNDETECTED: {len(undetected)}   "
        f"UNRESOLVED SITES: {len(unresolved)}"
    )
    for slot, path, label in undetected:
        print(f"   UNDETECTED {slot} {path} {label}")
    for line in unresolved:
        print(f"   UNRESOLVED {line}")
    if undetected or unresolved:
        sys.exit(1)


if __name__ == "__main__":
    main()
