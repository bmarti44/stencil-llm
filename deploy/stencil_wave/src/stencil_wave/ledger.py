# ruff: noqa: E501
"""The ledger: the held set of instructions found in the USER turns of a
rendered chat context, each mapped to ATTENTION KEY COLUMNS.

Port of the research module ``stencil.ledger`` (build_ledger / select /
render_text_ledger) with one deliberate generalization: an entry carries
``columns`` — the key positions its emphasis targets in the layer's
current K/V — rather than only a prompt span. Today those columns are
exactly the entry's token span in the context (``range(a, b)``); a later
ledger version that pins entries as KV-cache slots surviving context
eviction only has to hand out different column indices. Nothing below
the ledger (see ``attention.py``) knows about prompt strings.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from . import salience as _salience

TEXT_LEDGER_HEADER = "Earlier user instructions restated verbatim:"
USER_OPEN = "<|im_start|>user\n"
TURN_CLOSE = "<|im_end|>"


@dataclass
class Entry:
    text: str
    span: tuple[int, int]            # token span in the rendered context (a, b)
    turn_introduced: int             # 1-based user turn that stated it
    columns: tuple[int, ...]         # key columns this entry's emphasis targets
    key: object | None = None        # pooled layer-20 residual over the columns (torch tensor)
    held: bool = False               # eligible for selection this call
    selected: bool = False           # chosen by the controller this call
    score: float | None = None       # controller cos score at selection time
    status: str = "unknown"
    provenance: str = "salience"

    def to_record(self) -> dict:
        return {"text": self.text, "span": list(self.span), "turn_introduced": self.turn_introduced,
                "n_columns": len(self.columns), "held": self.held, "selected": self.selected,
                "score": self.score, "status": self.status, "provenance": self.provenance}


@dataclass
class Ledger:
    """What ``WaveModel.generate`` did with the ledger on the last call."""
    entries: list[Entry] = field(default_factory=list)
    current_turn: int = 0
    hold: str = "aged"
    top_k: int = 2
    dose: float = 0.0
    layers: tuple[int, ...] = ()
    active: bool = False             # was any bias applied at all
    biased_tokens: int = 0

    @property
    def held(self) -> list[Entry]:
        return [e for e in self.entries if e.held]

    @property
    def selected(self) -> list[Entry]:
        """Selected entries in RANK order (controller score desc, ledger order on ties)."""
        idx = [i for i, e in enumerate(self.entries) if e.selected]
        return [self.entries[i] for i in sorted(idx, key=lambda i: (-(self.entries[i].score or 0.0), i))]

    @property
    def columns(self) -> list[tuple[int, ...]]:
        """One column group per selected entry (groups are summed if they overlap)."""
        return [e.columns for e in self.selected]

    def to_dict(self) -> dict:
        return {"current_turn": self.current_turn, "hold": self.hold, "top_k": self.top_k, "dose": self.dose,
                "layers": list(self.layers), "active": self.active, "biased_tokens": self.biased_tokens,
                "entries": [e.to_record() for e in self.entries]}

    def render(self) -> str:
        lines = [f"ledger: {len(self.entries)} entries, {len(self.held)} held, {len(self.selected)} selected"
                 f" (turn {self.current_turn}, hold={self.hold}, top_k={self.top_k}, dose={self.dose},"
                 f" layers={self.layers[0]}-{self.layers[-1]}, active={self.active}, biased_tokens={self.biased_tokens})"
                 if self.layers else f"ledger: {len(self.entries)} entries (no bias layers)"]
        for i, e in enumerate(self.entries):
            flag = "*" if e.selected else ("+" if e.held else " ")
            sc = "" if e.score is None else f" score={e.score:+.3f}"
            lines.append(f"  {flag} [{i}] turn {e.turn_introduced} cols {e.span[0]}:{e.span[1]}{sc}  {e.text!r}")
        return "\n".join(lines)

    __str__ = render


def user_turns(context: str) -> list[tuple[int, int]]:
    """Char ranges of every user message body in a rendered ChatML context."""
    turns, cursor = [], 0
    while True:
        start = context.find(USER_OPEN, cursor)
        if start < 0:
            return turns
        content_start = start + len(USER_OPEN)
        content_end = context.find(TURN_CLOSE, content_start)
        if content_end < 0:
            raise ValueError("unterminated user turn")
        turns.append((content_start, content_end))
        cursor = content_end + 1


def build_ledger(offsets: Sequence[tuple[int, int]], context: str,
                 classify: Callable[[str], bool] | None = None,
                 segment: Callable[[str], list[tuple[int, int]]] | None = None) -> list[Entry]:
    """Segment every USER turn into sentences, keep the instructions, map each
    to its token span (clamped to the enclosing user message) in the
    context's own coordinates. ``offsets`` are the tokenizer's char offsets
    for ``context`` (one (start, end) per token). Keys are pooled later by
    the model from the same forward that generates."""
    classify = classify or _salience.is_instruction
    segment = segment or _salience.split_sentences
    entries: list[Entry] = []
    for turn, (cs, ce) in enumerate(user_turns(context), start=1):
        content = context[cs:ce]
        for at, end in segment(content):
            sentence = content[at:end]
            if not sentence.strip() or not classify(sentence):
                continue
            s_abs, e_abs = cs + at, min(cs + end, ce)
            toks = [i for i, (a, b) in enumerate(offsets) if a < e_abs and b > s_abs and a >= cs and b <= ce]
            if not toks:
                continue
            span = (toks[0], toks[-1] + 1)
            entries.append(Entry(sentence, span, turn, tuple(range(*span))))
    return entries


def select(entries: Sequence[Entry], query_h20, ctrl, top_k: int = 2) -> list[Entry]:
    """Top-k entries by the controller score cos(W_q q, W_k key); ties broken
    by ledger order. Records each entry's score; returns the chosen entries."""
    import torch

    if not entries:
        return []
    if any(e.key is None for e in entries):
        raise ValueError("select() needs pooled keys")
    with torch.no_grad():
        keys = torch.stack([e.key for e in entries]).float().to(query_h20.device)
        scores = ctrl.scores(query_h20, keys).tolist()
    for e, s in zip(entries, scores, strict=True):
        e.score = float(s)
    order = sorted(range(len(entries)), key=lambda i: (-scores[i], i))
    return [entries[i] for i in order[:top_k]]


def render_text_ledger(entries: Sequence[Entry]) -> str:
    """The textual baseline: the same entries restated verbatim."""
    if not entries:
        return ""
    return TEXT_LEDGER_HEADER + "\n" + "\n".join(f"- {e.text}" for e in entries)
