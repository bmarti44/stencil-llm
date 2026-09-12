"""Focal delivery of session conventions (direction rev 2, 2026-09-12).

Pure-Python, model-free pieces used by the CPU kill criteria and, later, by the
in-generation runtime:

* :func:`rule_family` types a convention sentence by the syntactic unit it governs,
  using only the unit vocabulary of the MemoryCode checker
  (``vendor/memorycode/code/extract_objects.py``: functions, methods, classes,
  variables, attributes, arguments, decorators, annotations, imports, docstrings,
  comments, try/assert).  It never looks at item data.
* :func:`unit_starts` is an incremental detector: given the text generated so far
  (markdown with fenced Python blocks, or bare Python), it returns the character
  offset of the start of every line that opens a governed unit, with the unit's
  trigger kind.  It is deliberately line based (a partial output is rarely
  parsable) and ignores lines inside triple-quoted strings and outside code fences.
* :func:`strip_spans` removes inserted spans (recorded by offset) so that scoring
  never sees delivered text.

Trigger kinds and the families they serve:

==========  ======================================================================
kind        families
==========  ======================================================================
function    function, function argument, function decorator, function annotation,
            function try, function assert, function docstring
method      method, attribute, method decorator, method annotation, method try,
            method assert, method docstring
class       class, class decorator
variable    variable
import      import
any         comment (delivered once, at the first unit of any kind)
==========  ======================================================================
"""

from __future__ import annotations

import re
from dataclasses import dataclass

FAMILY_KIND: dict[str, str] = {
    "function": "function",
    "function argument": "function",
    "function decorator": "function",
    "function annotation": "function",
    "function try": "function",
    "function assert": "function",
    "function docstring": "function",
    "method": "method",
    "attribute": "method",
    "method decorator": "method",
    "method annotation": "method",
    "method try": "method",
    "method assert": "method",
    "method docstring": "method",
    "class": "class",
    "class decorator": "class",
    "variable": "variable",
    "import": "import",
    "comment": "any",
}

# Ordered keyword tests: the first match wins.  "function argument" must precede
# "function"; "method"/"attribute" must precede "function" because method rules
# say "method names"; decorators/annotations/docstrings are typed by their carrier.
_TYPING: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bclass(es)?\b", re.I), "class"),
    (re.compile(r"\b(method|attribute)s?\b", re.I), "method"),
    (re.compile(r"\b(argument|parameter)s?\b", re.I), "function"),
    (re.compile(r"\bfunction", re.I), "function"),
    (re.compile(r"\bvariable", re.I), "variable"),
    (re.compile(r"\bimport", re.I), "import"),
    (re.compile(r"\bcomment", re.I), "any"),
]


def rule_family(text: str) -> str:
    """Trigger kind for a convention sentence; ``"any"`` when no unit is named."""
    for pat, kind in _TYPING:
        if pat.search(text):
            return kind
    return "any"


@dataclass(frozen=True)
class UnitStart:
    offset: int  # character offset of the line start in the full text
    line: int  # 0-based line index in the full text
    kind: str  # function | method | class | variable | import
    indent: int


_FENCE = re.compile(r"^\s*```")
_DEF = re.compile(r"^(\s*)(async\s+)?def\s+\w")
_CLASS = re.compile(r"^(\s*)class\s+\w")
_DECO = re.compile(r"^(\s*)@\w")
_IMPORT = re.compile(r"^(\s*)(import\s+\w|from\s+[\w.]+\s+import\b)")
_ASSIGN = re.compile(r"^(\s*)([A-Za-z_][\w]*)\s*(:\s*[^=]+)?=(?!=)")
_TRIPLE = re.compile(r'"""|\'\'\'')


def _in_class(stack: list[tuple[int, str]], indent: int) -> bool:
    for ind, kind in reversed(stack):
        if ind < indent:
            return kind == "class"
    return False


def unit_starts(text: str, fenced: bool | None = None) -> list[UnitStart]:
    """Line starts that open a governed unit in ``text`` (complete or partial).

    ``fenced=None`` auto-detects: if the text contains a code fence, only fenced
    regions are scanned; otherwise the whole text is treated as Python.  Decorator
    lines fire the unit they decorate (the first decorator line fires; the ``def``
    or ``class`` that follows a decorator does not fire again).
    """
    if fenced is None:
        fenced = "```" in text
    out: list[UnitStart] = []
    in_code = not fenced
    in_string = False
    pending_deco: int | None = None  # indent of an open decorator group
    stack: list[tuple[int, str]] = []  # (indent, kind) of enclosing def/class
    offset = 0
    for i, raw in enumerate(text.split("\n")):
        line = raw.rstrip("\r")
        start = offset
        offset += len(raw) + 1
        if fenced and _FENCE.match(line):
            in_code = not in_code
            in_string = False
            pending_deco = None
            stack.clear()
            continue
        if not in_code:
            continue
        if in_string:
            if len(_TRIPLE.findall(line)) % 2 == 1:
                in_string = False
            continue
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        while stack and stack[-1][0] >= indent:
            stack.pop()
        kind = None
        if _DECO.match(line):
            if pending_deco is None:
                pending_deco = indent
                # the decorated unit's kind is unknown until its header; fire as
                # "decorated" resolved below when the header arrives
                out.append(UnitStart(start, i, "decorated", indent))
            kind = "decorated"
        elif _CLASS.match(line):
            kind = "class"
        elif _DEF.match(line):
            kind = "method" if _in_class(stack, indent) else "function"
        elif _IMPORT.match(line):
            kind = "import"
        elif _ASSIGN.match(line):
            kind = "variable"
        if kind in ("class", "function", "method"):
            if pending_deco is not None and out and out[-1].kind == "decorated":
                out[-1] = UnitStart(out[-1].offset, out[-1].line, kind, out[-1].indent)
            else:
                out.append(UnitStart(start, i, kind, indent))
            pending_deco = None
            stack.append((indent, "class" if kind == "class" else "def"))
        elif kind in ("import", "variable"):
            pending_deco = None
            out.append(UnitStart(start, i, kind, indent))
        elif kind is None:
            pending_deco = None
        if len(_TRIPLE.findall(line)) % 2 == 1:
            in_string = True
    return out


def strip_spans(text: str, spans: list[tuple[int, int]]) -> str:
    """Remove ``[a, b)`` character spans (inserted text) from ``text``."""
    keep = []
    pos = 0
    for a, b in sorted(spans):
        keep.append(text[pos:a])
        pos = max(pos, b)
    keep.append(text[pos:])
    return "".join(keep)
