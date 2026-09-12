"""Focal delivery of session conventions (direction rev 2, 2026-09-12).

Pure-Python, model-free pieces used by the CPU kill criteria and by the
in-generation runtime (:mod:`stencil.focal_runtime`):

* :func:`rule_family` / :func:`rule_phase` type a convention sentence by the
  syntactic unit it governs and by the *decision point* inside that unit (header
  vs body), using only the unit vocabulary of the MemoryCode checker
  (``vendor/memorycode/code/extract_objects.py``).  They never look at item data.
* :func:`unit_starts` is an incremental detector over a partial output (markdown
  with fenced Python blocks, or bare Python): the character offset of every line
  that opens a governed unit, its kind, and the identifier once it is visible.
  It also reports ``body`` starts: the first line of a ``def``/``class`` body.
* :func:`strip_spans` removes inserted spans so that scoring never sees delivered
  text.  :func:`count_echoes` counts model-authored lines that copy a cue (reported,
  never removed from the scored output).

Trigger kinds and the families they serve:

==========  ======================================================================
kind        families (header phase unless noted)
==========  ======================================================================
function    function, function argument, function decorator, function annotation;
            body phase: function try, function assert, function docstring
method      method, method decorator, method annotation; body phase: method try,
            method assert, method docstring
init        attribute (delivered at the body of ``__init__``; other dunder methods
            receive no method rules, matching the checker's scope)
class       class, class decorator
variable    variable
import      import
any         comment (delivered once, with the first cue of any kind)
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
    "attribute": "init",
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

BODY_FAMILIES = {
    "function try",
    "function assert",
    "function docstring",
    "method try",
    "method assert",
    "method docstring",
    "attribute",
}

# Ordered keyword tests: the first match wins.
_TYPING: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\battribute", re.I), "init"),
    (re.compile(r"\bclass(es)?\b", re.I), "class"),
    (re.compile(r"\bmethods?\b", re.I), "method"),
    (re.compile(r"\b(argument|parameter)s?\b", re.I), "function"),
    (re.compile(r"\bfunction", re.I), "function"),
    (re.compile(r"\bvariable", re.I), "variable"),
    (re.compile(r"\bimport", re.I), "import"),
    (re.compile(r"\bcomment", re.I), "any"),
]
_BODY_WORDS = re.compile(r"\b(docstring|try\b|assert|attribute)", re.I)


def rule_family(text: str) -> str:
    """Trigger kind for a convention sentence; ``"any"`` when no unit is named."""
    for pat, kind in _TYPING:
        if pat.search(text):
            return kind
    return "any"


def rule_phase(text: str) -> str:
    """``"body"`` for docstring / try / assert / attribute rules, else ``"header"``."""
    return "body" if _BODY_WORDS.search(text) else "header"


@dataclass(frozen=True)
class UnitStart:
    offset: int  # character offset of the line start in the full text
    line: int  # 0-based line index in the full text
    kind: str  # function | method | class | variable | import | body | decorated
    indent: int
    name: str = ""  # identifier when visible ("" while still being written)
    parent: str = ""  # body: kind of the unit whose body starts here
    parent_name: str = ""


_FENCE = re.compile(r"^\s*```")
_DEF = re.compile(r"^(\s*)(async\s+)?def\s+(\w*)")
_CLASS = re.compile(r"^(\s*)class\s+(\w*)")
_DECO = re.compile(r"^(\s*)@\w")
_IMPORT = re.compile(r"^(\s*)(import\s+\w|from\s+[\w.]+\s+import\b)")
_ASSIGN = re.compile(r"^(\s*)([A-Za-z_][\w]*)\s*(:\s*[^=]+)?=(?!=)")
_HEADER_END = re.compile(r":\s*(#.*)?$")


def triple_toggle(line: str) -> bool:
    """True if ``line`` (scanned outside a multi-line string) toggles triple-quoted
    string state: counts triple quotes outside single-line strings and comments."""
    i = 0
    n = 0
    quote: str | None = None
    while i < len(line):
        c = line[i]
        if quote is None:
            if c == "#":
                break
            if line.startswith('"""', i) or line.startswith("'''", i):
                n += 1
                i += 3
                continue
            if c in "\"'":
                quote = c
        else:
            if c == "\\":
                i += 2
                continue
            if c == quote:
                quote = None
        i += 1
    return n % 2 == 1


def _bracket_delta(stripped: str) -> int:
    opens = stripped.count("(") + stripped.count("[") + stripped.count("{")
    closes = stripped.count(")") + stripped.count("]") + stripped.count("}")
    return opens - closes


def _in_class(stack: list[tuple[int, str]], indent: int) -> bool:
    for ind, kind in reversed(stack):
        if ind < indent:
            return kind == "class"
    return False


def unit_starts(text: str, fenced: bool | None = None) -> list[UnitStart]:
    """Line starts that open a governed unit in ``text`` (complete or partial).

    ``fenced=None`` auto-detects: if the text contains a code fence, only fenced
    regions are scanned; otherwise the whole text is treated as Python.  Decorator
    lines fire the unit they decorate (the first decorator line fires; the header
    that follows does not fire again; its name is filled in when visible).  A
    ``body`` start is reported for the first non-blank, non-comment line after a
    ``def``/``class`` header line ending with ``:``, with ``parent``/``parent_name``.
    Lines inside triple-quoted strings, after a backslash continuation or inside
    open brackets never open a unit.
    """
    if fenced is None:
        fenced = "```" in text
    out: list[UnitStart] = []
    in_code = not fenced
    in_string = False
    pending_deco: int | None = None
    stack: list[tuple[int, str]] = []
    awaiting_body: tuple[str, str, int] | None = None
    continuation = False
    depth = 0
    offset = 0
    for i, raw in enumerate(text.split("\n")):
        line = raw.rstrip("\r")
        start = offset
        offset += len(raw) + 1
        if fenced and _FENCE.match(line):
            in_code = not in_code
            in_string = False
            pending_deco = None
            awaiting_body = None
            continuation = False
            depth = 0
            stack.clear()
            continue
        if not in_code:
            continue
        if in_string:
            if triple_toggle(line):
                in_string = False
            continue
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if continuation or depth > 0:
            continuation = stripped.endswith("\\")
            depth = max(depth + _bracket_delta(stripped), 0)
            if triple_toggle(line):
                in_string = True
            continue
        indent = len(line) - len(line.lstrip())
        if awaiting_body is not None:
            pk, pn, pi = awaiting_body
            awaiting_body = None
            if indent > pi:
                out.append(UnitStart(start, i, "body", indent, "", pk, pn))
        while stack and stack[-1][0] >= indent:
            stack.pop()
        kind = None
        name = ""
        if _DECO.match(line):
            if pending_deco is None:
                pending_deco = indent
                out.append(UnitStart(start, i, "decorated", indent))
            kind = "decorated"
        elif m := _CLASS.match(line):
            kind = "class"
            name = m.group(2)
        elif m := _DEF.match(line):
            kind = "method" if _in_class(stack, indent) else "function"
            name = m.group(3)
        elif _IMPORT.match(line):
            kind = "import"
        elif _ASSIGN.match(line):
            kind = "variable"
        if kind in ("class", "function", "method"):
            if pending_deco is not None and out and out[-1].kind == "decorated":
                prev = out[-1]
                out[-1] = UnitStart(prev.offset, prev.line, kind, prev.indent, name)
            else:
                out.append(UnitStart(start, i, kind, indent, name))
            pending_deco = None
            stack.append((indent, "class" if kind == "class" else "def"))
            if _HEADER_END.search(stripped):
                awaiting_body = (kind, name, indent)
        elif kind in ("import", "variable"):
            pending_deco = None
            out.append(UnitStart(start, i, kind, indent))
        elif kind is None:
            pending_deco = None
        if triple_toggle(line):
            in_string = True
        continuation = stripped.endswith("\\")
        depth = max(_bracket_delta(stripped), 0)
    return out


def code_line_count(text: str, fenced: bool | None = None) -> tuple[bool, int, int]:
    """``(insertable, n_code_lines, last_indent)`` for a partial output ending at a
    line boundary: whether a comment line may be inserted here (inside code, not
    inside a string, not after a backslash continuation, not inside open brackets),
    how many complete non-blank, non-comment code lines precede the position, and
    the indentation of the last such line."""
    if fenced is None:
        fenced = "```" in text
    in_code = not fenced
    in_string = False
    n = 0
    last_indent = 0
    continuation = False
    depth = 0
    for line in text.split("\n")[:-1]:
        if fenced and _FENCE.match(line):
            in_code = not in_code
            in_string = False
            continuation = False
            depth = 0
            continue
        if not in_code:
            continue
        if in_string:
            if triple_toggle(line):
                in_string = False
            continue
        st = line.strip()
        if not st or st.startswith("#"):
            continue
        if not st.startswith(('"""', "'''")):
            n += 1
            last_indent = len(line) - len(line.lstrip())
        if triple_toggle(line):
            in_string = True
        continuation = st.endswith("\\")
        depth = max(depth + _bracket_delta(st), 0)
    ok = in_code and not in_string and not continuation and depth == 0
    return ok, n, last_indent


def strip_spans(text: str, spans: list[tuple[int, int]]) -> str:
    """Remove ``[a, b)`` character spans (inserted text) from ``text``."""
    keep = []
    pos = 0
    for a, b in sorted(spans):
        keep.append(text[pos:a])
        pos = max(pos, b)
    keep.append(text[pos:])
    return "".join(keep)


def count_echoes(text: str, cue_prefixes: tuple[str, ...]) -> int:
    """Model-authored lines starting with a cue prefix (imitation); reported only."""
    return sum(1 for line in text.split("\n") if line.strip().startswith(cue_prefixes))


_HEADER = re.compile(r"^\s*(async\s+def\s+|def\s+|class\s+|import\s+|from\s+|@)")


def header_keyword(line: str) -> str:
    """The unit keyword the model had started on ``line`` (``"def"``, ``"class"``,
    ``"import"``, ``"from"``, ``"@"``, ``"async def"``) without trailing space (the
    model's next token carries its own leading space); empty for assignments (the
    name itself is what a variable rule governs)."""
    m = _HEADER.match(line)
    if not m:
        return ""
    return re.sub(r"\s+", " ", m.group(1)).rstrip()
