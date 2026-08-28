# ruff: noqa: E501
"""Natural-language instruction-tracking task for the GPT-2 retrofit.

Deterministic by construction: every random choice comes from the registered
named streams; every answer is exactly one GPT-2 token; answers never appear
in the input (loss/eval use a separate target array at the `->` position).

Sequence layout (1024 tokens, window 64):
  [instruction zone: 4 rules stated]  [filler ... updates ... filler]
  [demo zone: 2 throwaway in-window rules + worked examples]
  [query zone: `word ->` lines for the 4 slots]
Rule statements: `New rule: reply to "cat" with "dog".`
Updates:        `Update: reply to "cat" with "bird" now.`
Queries:        `cat ->`  (target = the single token ` bird`; input next
                token is the newline — the answer is never written).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import torch

from .determinism import named_generator

ROOT = Path(__file__).resolve().parent.parent.parent
TOK_DIR = ROOT / "models" / "tokenizer"


class BPE:
    """Minimal GPT-2 byte-level BPE (encode only), from vocab.json + merges.txt."""

    def __init__(self, tok_dir: Path = TOK_DIR) -> None:
        self.encoder: dict[str, int] = json.loads((tok_dir / "vocab.json").read_text())
        merges = (tok_dir / "merges.txt").read_text().splitlines()[1:]
        self.ranks = {tuple(m.split()): i for i, m in enumerate(merges) if m}
        bs = list(range(33, 127)) + list(range(161, 173)) + list(range(174, 256))
        cs = bs[:]
        n = 0
        for b in range(256):
            if b not in bs:
                bs.append(b)
                cs.append(256 + n)
                n += 1
        self.byte_enc = {b: chr(c) for b, c in zip(bs, cs, strict=True)}

    def _bpe(self, token: str) -> list[str]:
        parts = list(token)
        while len(parts) > 1:
            pairs = [(self.ranks.get((a, b), 1 << 30), i) for i, (a, b) in enumerate(zip(parts, parts[1:], strict=False))]
            rank, i = min(pairs)
            if rank == 1 << 30:
                break
            parts = parts[:i] + [parts[i] + parts[i + 1]] + parts[i + 2 :]
        return parts

    def encode(self, text: str) -> list[int]:
        import re

        pat = re.compile(r"'s|'t|'re|'ve|'m|'ll|'d| ?[A-Za-z]+| ?[0-9]+| ?[^\sA-Za-z0-9]+|\s+(?!\S)|\s+")
        ids: list[int] = []
        for piece in pat.findall(text):
            mapped = "".join(self.byte_enc[b] for b in piece.encode("utf-8"))
            ids.extend(self.encoder[p] for p in self._bpe(mapped))
        return ids


# Vetted pools: every " word" must encode to exactly ONE token (verified by
# test_vocab_single_token). Slot words are the queried words; answer words the
# possible mappings (k=8 per slot, drawn per sequence).
SLOT_WORDS = ["cat", "sun", "red", "king"]
ANSWER_WORDS = [
    "dog", "moon", "blue", "queen", "bird", "star", "green", "prince",
    "fish", "rain", "gold", "lord", "horse", "snow", "black", "wolf",
]
DEMO_PAIRS = [("pen", "ink"), ("day", "night")]
FILLER = [
    "The weather stayed calm through the long afternoon.",
    "A quiet street ran past the old stone bridge.",
    "Several boats drifted slowly along the river.",
    "The market opened early and closed before dark.",
    "A light wind moved across the open field.",
    "The library kept its doors open until evening.",
    "Trains passed the station twice every hour.",
    "The garden wall needed paint after the winter.",
]


@dataclass
class NLSequence:
    tokens: list[int]
    targets: list[int]          # -1 except at answer positions
    query_positions: list[int]  # position of the '->' token per query
    query_slots: list[int]
    active_answer: list[str]
    rule_statement_pos: list[int]   # last statement token-position per slot
    updates_absorbed: list[int]


def _rule_text(slot_word: str, answer: str, update: bool) -> str:
    if update:
        return f'Update: reply to "{slot_word}" with "{answer}" now.'
    return f'New rule: reply to "{slot_word}" with "{answer}".'


def generate(
    seed_data: int,
    *,
    family: str = "train",
    n_updates: int = 3,
    seq_len: int = 1024,
    bpe: BPE | None = None,
) -> NLSequence:
    """One deterministic sequence. Streams: cues (choices), delays (gaps)."""
    bpe = bpe or BPE()
    g_c = named_generator(seed_data, "cues")
    g_d = named_generator(seed_data, "delays")
    g_f = named_generator(seed_data, "distractors")

    def choice(n: int, g: torch.Generator) -> int:
        return int(torch.randint(0, n, (1,), generator=g))

    # per-slot answer assignment (initial rules)
    active = {}
    used: set[int] = set()
    toks: list[int] = []
    stmt_pos: dict[int, int] = {}
    events: list[tuple[int, int]] = []  # (token_pos, slot)
    near = family == "near"
    for s in range(len(SLOT_WORDS)):
        a = choice(16, g_c)
        while a in used:
            a = (a + 1) % 16
        used.add(a)
        active[s] = ANSWER_WORDS[a]
    if not near:
        for s, w in enumerate(SLOT_WORDS):
            text = _rule_text(w, active[s], update=False) + " "
            stmt_pos[s] = len(toks)
            toks += bpe.encode(text)
            events.append((stmt_pos[s], s))

    gap_bounds = {"train": (2, 6), "drought": (8, 14), "burst": (1, 2), "near": (2, 6)}[family]

    def filler_until(target_len: int) -> None:
        while len(toks) < target_len:
            toks.extend(bpe.encode(FILLER[choice(len(FILLER), g_f)] + " "))

    # updates spread through the middle zone
    updates_done = 0
    middle_end = seq_len - 220
    if near:
        # curriculum family: pure filler, then every rule stated right before
        # the demo/query zone — all distances well inside the receptive field.
        filler_until(middle_end - 80)
        for s, w in enumerate(SLOT_WORDS):
            stmt_pos[s] = len(toks)
            toks += bpe.encode(_rule_text(w, active[s], update=False) + " ")
            events.append((stmt_pos[s], s))
        n_updates = 0
    for _ in range(n_updates):
        gap_sentences = choice(gap_bounds[1] - gap_bounds[0] + 1, g_d) + gap_bounds[0]
        for _ in range(gap_sentences):
            toks.extend(bpe.encode(FILLER[choice(len(FILLER), g_f)] + " "))
        if len(toks) >= middle_end - 30:
            break
        s = choice(4, g_c)
        a = choice(16, g_c)
        active[s] = ANSWER_WORDS[a]
        stmt_pos[s] = len(toks)
        toks += bpe.encode(_rule_text(SLOT_WORDS[s], active[s], update=True) + " ")
        events.append((stmt_pos[s], s))
        updates_done += 1
    filler_until(middle_end)

    # demo zone: throwaway rules + worked examples (format teaching, in-window)
    # The demo answer IS written (worked example) and also carries loss at the
    # '->' position — format supervision, no rule leakage (disjoint pools).
    targets = [-1] * seq_len
    for w, a in DEMO_PAIRS:
        head = bpe.encode(f'New rule: reply to "{w}" with "{a}". {w} ->')
        demo_p = len(toks) + len(head) - 1
        toks += head
        ans_id = bpe.encode(" " + a)
        assert len(ans_id) == 1
        if demo_p < seq_len - 1:
            targets[demo_p] = ans_id[0]
        toks += ans_id + bpe.encode(".\n")

    # query zone: one query per slot, order drawn
    order = torch.randperm(4, generator=g_c).tolist()
    qpos: list[int] = []
    qslots: list[int] = []
    answers: list[str] = []
    for s in order:
        line = bpe.encode(f"{SLOT_WORDS[s]} ->")
        if len(toks) + len(line) + 1 >= seq_len:
            break
        toks += line
        p = len(toks) - 1  # the '->' token position: logits[p] predicts answer
        qpos.append(p)
        qslots.append(s)
        answers.append(active[s])
        ans_id = bpe.encode(" " + active[s])
        assert len(ans_id) == 1, f"answer not single-token: {active[s]}"
        targets[p] = ans_id[0]
        toks += bpe.encode("\n")
    filler_until(seq_len)
    toks = toks[:seq_len]

    return NLSequence(
        tokens=toks,
        targets=targets[:seq_len],
        query_positions=qpos,
        query_slots=qslots,
        active_answer=answers,
        rule_statement_pos=[stmt_pos[s] for s in range(4)],
        updates_absorbed=[updates_done] * len(qpos),
    )


def batch(
    seeds: list[int], *, family: str = "train", n_updates: int = 3, bpe: BPE | None = None
) -> tuple[torch.Tensor, torch.Tensor, list[NLSequence]]:
    bpe = bpe or BPE()
    seqs = [generate(s, family=family, n_updates=n_updates, bpe=bpe) for s in seeds]
    toks = torch.tensor([s.tokens for s in seqs], dtype=torch.long)
    tgts = torch.tensor([s.targets for s in seqs], dtype=torch.long)
    return toks, tgts, seqs
