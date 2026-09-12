"""Focal delivery control loop on a scripted CPU backend (no model, no GPU)."""

from pathlib import Path

import pytest

from stencil.focal import strip_spans
from stencil.focal_runtime import CUE_PREFIX, FocalGenerator

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
        lines = [ln for ln in text.split("\n") if CUE_PREFIX not in ln]
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
    g = FocalGenerator(be, tok, rules=rules, eos_ids=(151645,), max_new_tokens=600)
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
    # cues sit directly above their unit, at the unit's indentation
    lines = r.text.split("\n")
    i = lines.index("    def m(self, a):")
    assert lines[i - 1] == f"    {CUE_PREFIX}method names contain 'chx'"
    assert (
        r.generated_ids == tok.encode(TARGET, add_special_tokens=False)
        or len(r.generated_ids) >= len(tok.encode(TARGET, add_special_tokens=False)) - 2
    )
