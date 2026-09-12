"""Focal delivery pieces: rule typing, incremental unit-start detection, stripping."""

from stencil.focal import FAMILY_KIND, rule_family, rule_phase, strip_spans, unit_starts


def test_rule_family_uses_the_named_unit():
    assert rule_family("always use all UPPERCASE for class names") == "class"
    assert rule_family("include 'chx' in function argument names") == "function"
    assert rule_family("include 'chx' in method names") == "method"
    assert rule_family("start attribute names with 'n_'") == "init"
    assert rule_phase("start attribute names with 'n_'") == "body"
    assert rule_phase("always include try statements in methods") == "body"
    assert rule_phase("include 'chx' in method names") == "header"
    assert rule_family("always add a comment above assignments") == "any"
    assert rule_family("reply in French") == "any"
    kinds = {"function", "method", "init", "class", "variable", "import", "any"}
    assert set(FAMILY_KIND.values()) == kinds


CODE = '''import os
from typing import List

@dataclass
class Foo:
    """A docstring with def inside
    def not_a_unit(): pass
    """
    x = 1

    @property
    def m(self):
        y = 2
        return y

def f(a, b):
    s = "def also_not_a_unit():"
    return a + b
'''


def test_unit_starts_bare_python():
    starts = unit_starts(CODE)
    kinds = [(u.line, u.kind) for u in starts]
    assert kinds == [
        (0, "import"),
        (1, "import"),
        (3, "class"),  # the decorator line fires the decorated class
        (5, "body"),  # first body line of the class (the docstring)
        (8, "variable"),
        (10, "method"),  # decorator line fires the method
        (12, "body"),
        (12, "variable"),
        (15, "function"),
        (16, "body"),
        (16, "variable"),
    ]
    names = {(u.line, u.kind): (u.name, u.parent, u.parent_name) for u in starts}
    assert names[(3, "class")] == ("Foo", "", "")
    assert names[(10, "method")] == ("m", "", "")
    assert names[(12, "body")] == ("", "method", "m")
    assert names[(16, "body")] == ("", "function", "f")


def test_unit_starts_fenced_only_scans_code():
    prose = "Sure, here is the code:\n\ndef prose_not_code():\n```python\n"
    text = prose + CODE + "```\ndone"
    fired = unit_starts(text)
    assert all(u.line >= 4 for u in fired)
    assert [u.kind for u in fired][:3] == ["import", "import", "class"]


LEXER_CODE = "\n".join(
    [
        "x = \"'''\"",  # single-line string holding a triple quote: no toggle
        'y = 1  # """ in a comment',
        "z = f(a,",
        "    b=1)",  # inside brackets: not an assignment start
        "w = 1 + \\",
        "    def_not = 2",  # backslash continuation: not a unit
        "def g():",
        "    pass",
        "",
    ]
)


def test_unit_starts_lexer_edge_cases():
    kinds = [(u.line, u.kind) for u in unit_starts(LEXER_CODE)]
    assert kinds == [
        (0, "variable"),
        (1, "variable"),
        (2, "variable"),
        (4, "variable"),
        (6, "function"),
        (7, "body"),
    ]


def test_unit_starts_is_incremental_prefix_stable():
    full = unit_starts(CODE)
    for cut in range(1, len(CODE)):
        partial = unit_starts(CODE[:cut])
        # every firing on a prefix is a firing on the full text at the same offset
        assert all(any(p.offset == q.offset for q in full) for p in partial)


def test_strip_spans_removes_inserted_text():
    text = "a" + "# rule\n" + "def f(): pass"
    assert strip_spans(text, [(1, 8)]) == "adef f(): pass"
