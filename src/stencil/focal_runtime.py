"""In-generation focal delivery: insert typed convention cues at governed unit starts.

The generator runs an ordinary greedy loop and, whenever the incremental detector
(:func:`stencil.focal.unit_starts`) reports a new unit start whose kind has rules,
rolls the generation back to the start of that line, feeds a comment block with the
applicable rules, and lets the model regenerate the line.  Inserted text is recorded
as character spans of the final output so that scoring can strip it.

Backend interface (narrow, so the control logic is testable on CPU):

* ``prefill(prompt_ids)``;
* ``step(feed) -> int``: append ``feed`` tokens to the sequence, return the greedy
  next token WITHOUT appending it (the caller feeds it on the next step);
* ``crop(n)``: keep only the first ``n`` post-prompt tokens.

:class:`HFBackend` implements it on a ``transformers`` causal LM with a
``DynamicCache``.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from stencil.focal import code_line_count, header_keyword, unit_starts

CUE_PREFIX = "# Convention: "


@dataclass
class FocalResult:
    text: str
    generated_ids: list[int]  # model tokens only (inserted tokens excluded)
    inserted_spans: list[tuple[int, int]]  # [a, b) char spans in ``text``
    inserted_tokens: int
    refed_tokens: int = 0  # header keywords re-fed after a cue (model-originated)
    events: list[dict] = field(default_factory=list)
    ended_by_eos: bool = False
    timed_out: bool = False
    truncated: bool = False
    seconds: float = 0.0


CUE_LINE_PREFIX = "# Apply here: "


def cue_block(rules: list[str], indent: int, style: str = "line") -> str:
    """``style="block"``: one ``# Convention: ...`` line per rule (imitated by small
    models as a pattern to continue).  ``style="line"``: one compact comment line
    ``# Apply here: r1; r2; ...``."""
    pad = " " * indent
    if style == "block":
        return "".join(f"{pad}{CUE_PREFIX}{r.strip()}\n" for r in rules)
    return (
        f"{pad}{CUE_LINE_PREFIX}"
        + "; ".join(r.strip().rstrip(".") for r in rules)
        + "\n"
    )


class FocalGenerator:
    """Greedy generation with focal delivery of typed rules.

    ``rules`` is a list of ``(kind, text)`` with kind in function / method / class /
    variable / import / any.  ``any`` rules are delivered once, at the first unit of
    any kind.  ``max_insertions`` bounds the number of insertions per generation.
    With ``rules=[]`` the loop is plain greedy decoding.

    ``deliver="first"`` (dose-matched with a once-before reminder) delivers each
    kind's rules once, at the first governed unit of that kind; ``deliver="every"``
    delivers at every governed unit, subject to ``cooldown_lines`` complete code
    lines since the previous insertion and ``max_per_rule`` deliveries per rule.

    ``policy="periodic"`` is the repetition-matched control: the complete rule list
    (every kind, one block) is inserted at the start of the next code line every
    ``period_lines`` complete non-blank code lines, at a line boundary (no rollback)
    and regardless of what the next line turns out to be.  Whether a periodic
    insertion happened to land directly above a unit start is recorded per event.
    """

    def __init__(
        self,
        backend,
        tokenizer,
        rules: list[tuple[str, str]],
        max_new_tokens: int = 1536,
        eos_ids: tuple[int, ...] = (),
        deadline_seconds: float | None = None,
        max_insertions: int = 40,
        policy: str = "aligned",
        period_lines: int = 8,
        deliver: str = "first",
        cooldown_lines: int = 3,
        max_per_rule: int = 3,
        cue_style: str = "line",
    ) -> None:
        self.cue_style = cue_style
        if deliver not in ("first", "every"):
            raise ValueError(deliver)
        self.deliver = deliver
        self.cooldown_lines = cooldown_lines
        self.max_per_rule = max_per_rule
        if policy not in ("aligned", "periodic"):
            raise ValueError(policy)
        self.policy = policy
        self.period_lines = period_lines
        self.backend = backend
        self.tok = tokenizer
        self.rules = list(rules)
        self.max_new_tokens = max_new_tokens
        self.eos_ids = set(eos_ids)
        self.deadline = deadline_seconds
        self.max_insertions = max_insertions

    def _rules_for(
        self, kind: str, any_done: bool, counts: dict
    ) -> tuple[list[str], bool]:
        out = [
            t
            for k, t in self.rules
            if k == kind and counts.get(t, 0) < self.max_per_rule
        ]
        extra = [] if any_done else [t for k, t in self.rules if k == "any"]
        return out + extra, bool(extra)

    def generate(self, prompt_ids: list[int]) -> FocalResult:
        t0 = time.time()
        self.backend.prefill(list(prompt_ids))
        # pieces: ordered ("gen"|"ins"|"keep", ids); the sequence after the prompt is
        # their concatenation.  "ins" = cue text (stripped before scoring); "keep" =
        # the unit's header keyword re-fed after the cue so the model completes the
        # unit instead of continuing the comment block (kept in the output, counted
        # separately).  Rollback removes trailing generated tokens only and never
        # reaches into an inserted piece (``floor``).
        pieces: list[tuple[str, list[int]]] = []
        delivered: set[tuple[int, str]] = set()
        delivered_lines: set[int] = set()
        kinds_done: set[str] = set()
        counts: dict[str, int] = {}
        last_ins_lines = -(10**9)
        any_done = False
        events: list[dict] = []
        n_gen = 0
        n_ins_tokens = 0
        n_refed = 0
        n_insertions = 0
        ended = False
        timed_out = False
        pending: list[int] = []

        def flat() -> list[int]:
            return [i for _, ids in pieces for i in ids]

        def decode(ids: list[int]) -> str:
            return self.tok.decode(ids, skip_special_tokens=True)

        def floor() -> int:
            acc = 0
            f = 0
            for k, p in pieces:
                acc += len(p)
                if k != "gen":
                    f = acc
            return f

        while n_gen < self.max_new_tokens:
            if self.deadline is not None and time.time() - t0 > self.deadline:
                timed_out = True
                break
            nxt = self.backend.step(pending)
            if nxt in self.eos_ids:
                pending = []
                ended = True
                break
            pending = [nxt]
            if pieces and pieces[-1][0] == "gen":
                pieces[-1][1].append(nxt)
            else:
                pieces.append(("gen", [nxt]))
            n_gen += 1
            if n_insertions >= self.max_insertions:
                continue
            ids = flat()
            text = decode(ids)
            if self.policy == "periodic":
                if not text.endswith("\n"):
                    continue
                in_code, n_lines, indent = code_line_count(text)
                if not in_code or n_lines == 0 or n_lines % self.period_lines:
                    continue
                if n_lines in delivered_lines:
                    continue
                delivered_lines.add(n_lines)
                block = cue_block([t for _, t in self.rules], indent, self.cue_style)
                insert_ids = self.tok.encode(block, add_special_tokens=False)
                pieces.append(("ins", list(insert_ids)))
                pending = pending + list(insert_ids)
                n_ins_tokens += len(insert_ids)
                n_insertions += 1
                events.append(
                    {
                        "kind": "periodic",
                        "line": text.count("\n"),
                        "offset": len(text),
                        "rolled_back_tokens": 0,
                        "inserted_tokens": len(insert_ids),
                        "rules": [t for _, t in self.rules],
                    }
                )
                continue
            fired = None
            rules: list[str] = []
            used_any = False
            for u in unit_starts(text):
                if u.kind == "decorated" or (u.offset, u.kind) in delivered:
                    continue
                if u.kind in kinds_done and self.deliver == "first":
                    delivered.add((u.offset, u.kind))
                    continue
                rules, used_any = self._rules_for(u.kind, any_done, counts)
                if not rules:
                    delivered.add((u.offset, u.kind))
                    continue
                fired = u
                break
            if fired is None:
                continue
            if self.deliver == "every" and fired.kind in kinds_done:
                # cooldown applies to repeat deliveries of a kind only
                _, n_lines, _ = code_line_count(text)
                if n_lines - last_ins_lines < self.cooldown_lines:
                    delivered.add((fired.offset, fired.kind))
                    continue
            # largest token prefix whose decode ends at or before the line start
            cut = len(ids)
            while cut > 0 and len(decode(ids[:cut])) > fired.offset:
                cut -= 1
            if cut < floor():
                delivered.add((fired.offset, fired.kind))
                continue
            kept_text = decode(ids[:cut])
            remainder = text[len(kept_text) : fired.offset]
            block = cue_block(rules, fired.indent, self.cue_style)
            insert_ids = self.tok.encode(remainder + block, add_special_tokens=False)
            keyword = header_keyword(text[fired.offset :].split("\n")[0])
            keep_text = " " * fired.indent + keyword if keyword else ""
            keep_ids = (
                self.tok.encode(keep_text, add_special_tokens=False)
                if keep_text
                else []
            )
            removed = len(ids) - cut
            n_gen_before = n_gen
            while removed > 0:
                k, p = pieces[-1]
                assert k == "gen"
                if len(p) <= removed:
                    removed -= len(p)
                    pieces.pop()
                else:
                    del p[len(p) - removed :]
                    removed = 0
            n_gen = sum(len(p) for k, p in pieces if k == "gen")
            self.backend.crop(cut)
            pieces.append(("ins", list(insert_ids)))
            if keep_ids:
                pieces.append(("keep", list(keep_ids)))
            pending = list(insert_ids) + list(keep_ids)
            n_ins_tokens += len(insert_ids)
            n_refed += len(keep_ids)
            n_insertions += 1
            any_done = any_done or used_any
            kinds_done.add(fired.kind)
            for t in rules:
                counts[t] = counts.get(t, 0) + 1
            last_ins_lines = code_line_count(kept_text + remainder)[1]
            delivered.add((len(kept_text) + len(remainder) + len(block), fired.kind))
            events.append(
                {
                    "kind": fired.kind,
                    "line": fired.line,
                    "offset": fired.offset,
                    "rolled_back_tokens": n_gen_before - n_gen,
                    "inserted_tokens": len(insert_ids),
                    "refed_keyword": keyword,
                    "rules": rules,
                }
            )
        ids = flat()
        text = decode(ids)
        if self.policy == "periodic":
            starts = {u.offset for u in unit_starts(text)}
            for e, sp in zip(events, _ins_spans(pieces, decode)):
                e["adjacent_to_unit"] = sp[1] in starts
        spans = []
        acc: list[int] = []
        for k, p in pieces:
            a = len(decode(acc))
            acc = acc + p
            b = len(decode(acc))
            if k == "ins":
                spans.append((a, b))
        gen_ids = [i for k, p in pieces if k == "gen" for i in p]
        return FocalResult(
            text=text,
            generated_ids=gen_ids,
            inserted_spans=spans,
            inserted_tokens=n_ins_tokens,
            refed_tokens=n_refed,
            events=events,
            ended_by_eos=ended,
            timed_out=timed_out,
            truncated=(not ended and not timed_out and n_gen >= self.max_new_tokens),
            seconds=time.time() - t0,
        )


def _ins_spans(pieces, decode) -> list[tuple[int, int]]:
    spans = []
    acc: list[int] = []
    for k, p in pieces:
        a = len(decode(acc))
        acc = acc + p
        b = len(decode(acc))
        if k == "ins":
            spans.append((a, b))
    return spans


class HFBackend:
    """``transformers`` causal LM backend with a croppable ``DynamicCache``."""

    def __init__(self, model) -> None:
        self.model = model
        self.cache = None
        self.prompt: list[int] = []
        self.seq: list[int] = []  # post-prompt tokens present in the cache
        self._refeed: list[int] = []  # tokens whose KV was dropped and must be re-fed

    def _forward(self, ids: list[int]) -> int:
        import torch

        t = torch.tensor([ids], device=self.model.device)
        with torch.no_grad():
            out = self.model(t, past_key_values=self.cache, use_cache=True)
        self.cache = out.past_key_values
        return int(out.logits[0, -1].argmax())

    def prefill(self, prompt_ids: list[int]) -> None:
        from transformers import DynamicCache

        self.cache = DynamicCache()
        self.prompt = list(prompt_ids)
        self.seq = []
        self._refeed = []
        self._next = self._forward(self.prompt)

    def step(self, feed: list[int]) -> int:
        ids = self._refeed + list(feed)
        self._refeed = []
        if ids:
            self.seq.extend(feed)
            self._next = self._forward(ids)
        return self._next

    def crop(self, n: int) -> None:
        # keep n post-prompt tokens; drop one more so the logits at the new end can
        # be recomputed by re-feeding that token on the next step
        keep = len(self.prompt) + n
        remove = len(self.prompt) + len(self.seq) - (keep - 1)
        if remove > 0:
            self.cache.crop(-remove)
        last = (self.prompt + self.seq)[keep - 1]
        self.seq = self.seq[:n]
        self._refeed = [last]
        self._next = None
