"""Focal delivery control loop on a scripted CPU backend (no model, no GPU)."""

from pathlib import Path

import pytest

from stencil.focal import strip_spans
from stencil.focal_runtime import CUE_LINE_PREFIX, CUE_PREFIX, FocalGenerator

HUB = Path(__file__).resolve().parents[1] / "deploy/stencil_focus/build/hub-4b"


@pytest.fixture(scope="module")
def tok():
    if not HUB.exists():
        pytest.skip("package build not present")
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(str(HUB))


class Scripted:
    """A 'model' that writes ``target`` no matter what: its next token continues the
    target from the decoded text so far with cue lines removed.  It sees inserted
    tokens like a real model would (they enter the sequence)."""

    def __init__(self, tok, target: str, eos: int):
        self.tok = tok
        self.target = target
        self.eos = eos
        self.seq: list[int] = []
        self.prompt: list[int] = []
        self.crops: list[int] = []

    def prefill(self, prompt_ids):
        self.prompt = list(prompt_ids)
        self.seq = []

    def _visible(self) -> str:
        text = self.tok.decode(self.seq, skip_special_tokens=True)
        lines = [
            ln
            for ln in text.split("\n")
            if CUE_PREFIX not in ln and CUE_LINE_PREFIX not in ln
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
    def m(self, a):
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


def test_focal_inserts_typed_cues_and_strips_back_to_target(tok):
    rules = [
        ("function", "function names contain 'chx'"),
        ("method", "method names contain 'chx'"),
        ("class", "class names are UPPERCASE"),
        ("any", "comment every assignment"),
        ("variable", "variable names start with vr_"),
    ]
    be = Scripted(tok, TARGET, eos=151645)
    g = FocalGenerator(
        be,
        tok,
        rules=rules,
        eos_ids=(151645,),
        max_new_tokens=600,
        deliver="every",
        cooldown_lines=0,
    )
    r = g.generate([1, 2, 3])
    assert r.ended_by_eos
    kinds = [e["kind"] for e in r.events]
    # the import has no rule of its own but carries the one-time 'any' rule
    assert kinds == ["import", "class", "method", "variable", "function"]
    assert r.events[0]["rules"] == ["comment every assignment"]
    # the 'any' rule rides along with the first delivered unit only
    assert sum("comment every assignment" in e["rules"] for e in r.events) == 1
    assert strip_spans(r.text, r.inserted_spans) == TARGET
    assert r.inserted_tokens == sum(e["inserted_tokens"] for e in r.events)
    # cues sit directly above their unit, at the unit's indentation, and the header
    # keyword is re-fed (kept in the output, counted separately)
    lines = r.text.split("\n")
    i = lines.index("    def m(self, a):")
    assert lines[i - 1] == f"    {CUE_LINE_PREFIX}method names contain 'chx'"
    assert r.refed_tokens > 0
    assert [e["refed_keyword"] for e in r.events][:3] == ["import", "class", "def"]
    target_len = len(tok.encode(TARGET, add_special_tokens=False))
    assert len(r.generated_ids) + r.refed_tokens >= target_len - 2


def test_periodic_control_inserts_at_line_boundaries_without_rollback(tok):
    rules = [("function", "function names contain 'chx'"), ("class", "UPPERCASE")]
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
    assert all(e["rolled_back_tokens"] == 0 for e in r.events)
    assert all("adjacent_to_unit" in e for e in r.events)
    assert strip_spans(r.text, r.inserted_spans) == TARGET
    assert not be.crops


def test_deliver_first_cues_each_kind_once(tok):
    rules = [("variable", "variable names start with vr_"), ("method", "m rule")]
    be = Scripted(tok, TARGET, eos=151645)
    g = FocalGenerator(be, tok, rules=rules, eos_ids=(151645,), max_new_tokens=600)
    r = g.generate([1, 2, 3])
    assert [e["kind"] for e in r.events] == ["method", "variable"]
    assert strip_spans(r.text, r.inserted_spans) == TARGET


def test_strip_echoes_removes_copied_cue_lines():
    from stencil.focal import strip_echoes

    cue = {f"{CUE_PREFIX}x"}
    text = f"a\n{CUE_PREFIX}x\n  {CUE_PREFIX}x\nb"
    assert strip_echoes(text, cue) == ("a\nb", 2)


def test_header_keyword():
    from stencil.focal import header_keyword

    assert header_keyword("    async  def  f(") == "async def"
    assert header_keyword("@dataclass") == "@"
    assert header_keyword("from typing import X") == "from"
    assert header_keyword("x = 1") == ""


def test_code_line_count_ignores_docstrings_and_comments():
    from stencil.focal import code_line_count

    text = 'x = 1\n"""doc\n# not code\nstill doc\n"""\n# comment\ny = 2\n'
    assert code_line_count(text) == (True, 2, 0)
    assert code_line_count('x = 1\n"""open\n')[0] is False


def test_block_style_cue_and_deliver_every_first_kind_has_no_cooldown(tok):
    rules = [("function", "f rule"), ("method", "m rule")]
    be = Scripted(tok, TARGET, eos=151645)
    g = FocalGenerator(
        be,
        tok,
        rules=rules,
        eos_ids=(151645,),
        max_new_tokens=600,
        deliver="every",
        cooldown_lines=50,
        cue_style="block",
    )
    r = g.generate([1, 2, 3])
    # first delivery of each kind ignores the cooldown; the ``def f`` after ``m``
    # is a different kind so it is still delivered
    assert [e["kind"] for e in r.events] == ["method", "function"]
    assert f"{CUE_PREFIX}m rule" in r.text
    assert strip_spans(r.text, r.inserted_spans) == TARGET
