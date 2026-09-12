"""Focal delivery pieces: rule typing, incremental unit-start detection, stripping."""

from stencil.focal import FAMILY_KIND, rule_family, strip_spans, unit_starts


def test_rule_family_uses_the_named_unit():
    assert rule_family("always use all UPPERCASE for class names") == "class"
    assert rule_family("include 'chx' in function argument names") == "function"
    assert rule_family("include 'chx' in method names") == "method"
    assert rule_family("start attribute names with 'n_'") == "method"
    assert rule_family("always add a comment above assignments") == "any"
    assert rule_family("reply in French") == "any"
    kinds = {"function", "method", "class", "variable", "import", "any"}
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
    kinds = [(u.line, u.kind) for u in unit_starts(CODE)]
    assert kinds == [
        (0, "import"),
        (1, "import"),
        (3, "class"),  # the decorator line fires the decorated class
        (8, "variable"),
        (10, "method"),  # decorator line fires the method
        (12, "variable"),
        (15, "function"),
        (16, "variable"),
    ]


def test_unit_starts_fenced_only_scans_code():
    prose = "Sure, here is the code:\n\ndef prose_not_code():\n```python\n"
    text = prose + CODE + "```\ndone"
    fired = unit_starts(text)
    assert all(u.line >= 4 for u in fired)
    assert [u.kind for u in fired][:3] == ["import", "import", "class"]


def test_unit_starts_is_incremental_prefix_stable():
    full = unit_starts(CODE)
    for cut in range(1, len(CODE)):
        partial = unit_starts(CODE[:cut])
        # every firing on a prefix is a firing on the full text at the same offset
        assert all(any(p.offset == q.offset for q in full) for p in partial)


def test_strip_spans_removes_inserted_text():
    text = "a" + "# rule\n" + "def f(): pass"
    assert strip_spans(text, [(1, 8)]) == "adef f(): pass"
