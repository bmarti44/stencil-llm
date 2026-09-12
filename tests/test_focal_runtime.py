"""Focal delivery control loop on a scripted CPU backend (no model, no GPU)."""

from pathlib import Path

import pytest

from stencil.focal import count_echoes, strip_spans
from stencil.focal_runtime import CUE_PREFIX, CUE_PREFIXES, FocalGenerator

HUB = Path(__file__).resolve().parents[1] / "deploy/stencil_focus/build/hub-4b"


@pytest.fixture(scope="module")
def tok():
    if not HUB.exists():
        pytest.skip("package build not present")
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(str(HUB))


class Scripted:
    """A 'model' that writes ``target`` no matter what: its next token continues the
    target from the decoded post-prompt text with cue lines removed.  It sees
    inserted tokens like a real model would (they enter the sequence)."""

    def __init__(self, tok, target: str, eos: int):
        self.tok = tok
        self.target = target
        self.eos = eos
        self.seq: list[int] = []
        self.prompt: list[int] = []
        self.crops: list[int] = []
        self.prefills: list[list[int]] = []

    def prefill(self, prompt_ids, prefix_ids=()):
        self.prompt = list(prompt_ids)
        self.seq = list(prefix_ids)
        self.prefills.append(list(prompt_ids))

    def _visible(self) -> str:
        text = self.tok.decode(self.seq, skip_special_tokens=True)
        lines = [
            ln for ln in text.split("\n") if not ln.strip().startswith(CUE_PREFIXES)
        ]
        return "\n".join(lines)

    def step(self, feed):
        self.seq.extend(feed)
        done = self._visible()
        assert self.target.startswith(done), (done, self.target)
        rest = self.target[len(done) :]
        if not rest:
            return self.eos
        return self.tok.encode(rest, add_special_tokens=False)[0]

    def crop(self, n):
        self.crops.append(n)
        self.seq = self.seq[:n]


TARGET = """Here is the code:
```python
import os

class Foo:
    def __init__(self, a):
        self.a = a

    def m(self, a):
        \"\"\"doc\"\"\"
        x = 1
        return x

def f(b):
    return b
```
"""


def test_plain_loop_reproduces_target_without_rules(tok):
    be = Scripted(tok, TARGET, eos=151645)
    g = FocalGenerator(be, tok, rules=[], eos_ids=(151645,), max_new_tokens=400)
    r = g.generate([1, 2, 3])
    assert r.text == TARGET
    assert r.ended_by_eos and not r.inserted_spans and not r.events
    assert r.steps == len(r.generated_ids) + 1  # + the EOS selection


RULES = [
    ("function", "header", "function names contain 'chx'"),
    ("method", "header", "method names contain 'chx'"),
    ("method", "body", "always include try statements in methods"),
    ("init", "body", "attribute names end with '_s'"),
    ("class", "header", "class names are UPPERCASE"),
    ("any", "header", "comment every assignment"),
    ("variable", "header", "variable names start with vr_"),
]


def test_focal_first_delivers_each_packet_once_at_its_decision_point(tok):
    be = Scripted(tok, TARGET, eos=151645)
    g = FocalGenerator(be, tok, rules=RULES, eos_ids=(151645,), max_new_tokens=600)
    r = g.generate([1, 2, 3])
    assert r.ended_by_eos
    got = [(e["packet_kind"], e["phase"], e["name"]) for e in r.events]
    assert got == [
        ("class", "header", "Foo"),
        ("init", "body", "__init__"),  # attribute rules at __init__'s body only
        ("method", "header", "m"),  # __init__ received no method-header rules
        ("method", "body", "m"),
        ("variable", "header", ""),
        ("function", "header", "f"),
    ]
    # the one-time 'any' rule rides with the first cue only
    assert sum("comment every assignment" in e["rules"] for e in r.events) == 1
    assert strip_spans(r.text, r.inserted_spans) == TARGET
    assert r.inserted_tokens == sum(e["inserted_tokens"] for e in r.events)
    lines = r.text.split("\n")
    i = lines.index("    def m(self, a):")
    assert lines[i - 1] == f"    {CUE_PREFIX}method: method names contain 'chx'"
    j = lines.index('        """doc"""')
    assert lines[j - 1].startswith(
        f"        {CUE_PREFIX}method body: always include try"
    )
    assert [e["refed_keyword"] for e in r.events] == ["class", "", "def", "", "", "def"]
    assert count_echoes(strip_spans(r.text, r.inserted_spans), CUE_PREFIXES) == 0
    assert r.steps > len(r.generated_ids) and r.discarded_tokens > 0


def test_unphased_delivers_body_rules_at_the_header(tok):
    be = Scripted(tok, TARGET, eos=151645)
    g = FocalGenerator(
        be, tok, rules=RULES, eos_ids=(151645,), max_new_tokens=600, phased=False
    )
    r = g.generate([1, 2, 3])
    m = [e for e in r.events if e["packet_kind"] == "method"]
    assert len(m) == 1 and m[0]["phase"] == "header"
    assert "always include try statements in methods" in m[0]["rules"]
    assert strip_spans(r.text, r.inserted_spans) == TARGET


def test_auto_refeed_leaves_room_for_a_decorator(tok):
    rules = [("function", "header", "add the '@retry' decorator to all functions")]
    be = Scripted(tok, TARGET, eos=151645)
    g = FocalGenerator(be, tok, rules=rules, eos_ids=(151645,), max_new_tokens=600)
    r = g.generate([1, 2, 3])
    assert [e["refed_keyword"] for e in r.events] == [""]
    assert strip_spans(r.text, r.inserted_spans) == TARGET


def test_user_channel_rebuilds_prompt_and_keeps_code_clean(tok):
    calls = []

    def rebuild(packets):
        calls.append(list(packets))
        return [7, 7, 7] + list(range(len(packets)))

    be = Scripted(tok, TARGET, eos=151645)
    g = FocalGenerator(
        be,
        tok,
        rules=RULES,
        eos_ids=(151645,),
        max_new_tokens=600,
        channel="user",
        rebuild_prompt=rebuild,
    )
    r = g.generate([1, 2, 3])
    assert r.text == TARGET and not r.inserted_spans
    assert len(calls) == len(r.events) == 6
    assert len(calls[-1]) == 6 and calls[-1][0].startswith(
        "For the class you are about"
    )
    assert r.prompt_tokens == 3 + 6
    assert be.prefills[-1] == [7, 7, 7, 0, 1, 2, 3, 4, 5]


def test_periodic_control_inserts_at_safe_line_boundaries(tok):
    rules = [("function", "header", "f rule"), ("class", "header", "c rule")]
    be = Scripted(tok, TARGET, eos=151645)
    g = FocalGenerator(
        be,
        tok,
        rules=rules,
        eos_ids=(151645,),
        max_new_tokens=600,
        policy="periodic",
        period_lines=3,
    )
    r = g.generate([1, 2, 3])
    assert r.ended_by_eos
    assert r.events and all(e["kind"] == "periodic" for e in r.events)
    assert all("adjacent_to_unit" in e for e in r.events)
    assert strip_spans(r.text, r.inserted_spans) == TARGET
    assert not be.crops


def test_context_budget_stops_generation(tok):
    be = Scripted(tok, TARGET, eos=151645)
    g = FocalGenerator(
        be, tok, rules=[], eos_ids=(151645,), max_new_tokens=600, max_context=20
    )
    r = g.generate([1, 2, 3])
    assert r.context_exceeded and not r.truncated
    assert 3 + len(r.generated_ids) <= 20


def test_header_keyword_and_line_count():
    from stencil.focal import code_line_count, header_keyword, triple_toggle

    assert header_keyword("    async  def  f(") == "async def"
    assert header_keyword("@dataclass") == "@"
    assert header_keyword("from typing import X") == "from"
    assert header_keyword("x = 1") == ""
    text = 'x = 1\n"""doc\n# not code\nstill doc\n"""\n# comment\ny = 2\n'
    assert code_line_count(text) == (True, 2, 0)
    assert code_line_count('x = 1\n"""open\n')[0] is False
    assert code_line_count("x = 1 + \\\n")[0] is False
    assert code_line_count("f(a,\n")[0] is False
    assert triple_toggle("x = \"'''\"") is False
    assert triple_toggle('s = """') is True
    assert triple_toggle('# """') is False
