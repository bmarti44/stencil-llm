"""In-generation focal delivery: typed convention cues at the decision point.

The generator runs an ordinary greedy loop and, whenever the incremental detector
(:func:`stencil.focal.unit_starts`) reports a governed decision point, rolls the
generation back to the start of that line, delivers the applicable rules, and lets
the model regenerate the line.  Two delivery channels:

* ``channel="comment"``: one compact comment line is inserted above the line
  (``# For this function: r1; r2``), then the header keyword the model had already
  started (``def``, ``class``, ``import``, ``@``) is re-fed so the model completes
  the unit instead of continuing the comment; when a delivered rule asks for a
  decorator and none was started, only the indentation is re-fed so ``@`` stays
  possible.  Inserted text is recorded as character spans of the output.
* ``channel="user"``: nothing enters the code; the prompt is rebuilt with the
  accumulated reminders appended to the user request (``rebuild_prompt``), the
  retained code prefix is re-prefilled, and generation continues.

Decision points: header (name, arguments, annotations, decorators) at the unit
start; body (docstring, try, assert, attributes) at the first body line of the
unit.  Rules of kind ``init`` (attributes) are delivered at ``__init__``'s body;
other dunder methods receive no method rules (the checker's scope).

Backend interface (narrow, so the control logic is testable on CPU):

* ``prefill(prompt_ids, prefix_ids=())``: prompt, then already-known post-prompt
  tokens;
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

CUE_PREFIX = "# For this "
CUE_PREFIXES = (CUE_PREFIX, "# Convention: ", "# Apply here: ")
LABELS = {
    "function": "function",
    "method": "method",
    "class": "class",
    "import": "import",
    "variable": "assignment",
    "body:function": "function body",
    "body:method": "method body",
    "body:init": "__init__ body",
}


@dataclass
class FocalResult:
    text: str
    generated_ids: list[int]  # model-selected tokens retained in the output
    inserted_spans: list[tuple[int, int]]  # [a, b) char spans in ``text`` (cues)
    inserted_tokens: int
    refed_tokens: int = 0  # keywords / indentation re-fed after a cue
    steps: int = 0  # autoregressive selections, monotonic (includes rolled back)
    discarded_tokens: int = 0  # selections rolled back
    prompt_tokens: int = 0  # final prompt length (user channel: rebuilt prompt)
    reminders: list[str] = field(default_factory=list)  # user-channel packets
    events: list[dict] = field(default_factory=list)
    ended_by_eos: bool = False
    timed_out: bool = False
    truncated: bool = False
    context_exceeded: bool = False
    seconds: float = 0.0


def cue_line(label: str, rules: list[str], indent: int) -> str:
    body = "; ".join(r.strip().rstrip(".") for r in rules)
    return f"{' ' * indent}{CUE_PREFIX}{label}: {body}\n"


def cue_packet(label: str, rules: list[str]) -> str:
    body = "; ".join(r.strip().rstrip(".") for r in rules)
    return f"For the {label} you are about to write: {body}."


def _is_dunder(name: str) -> bool:
    return len(name) > 4 and name.startswith("__") and name.endswith("__")


class FocalGenerator:
    """Greedy generation with focal delivery of typed rules.

    ``rules``: ``(kind, phase, text)`` triples (kind in function / method / init /
    class / variable / import / any; phase in header / body).  ``deliver="first"``
    delivers each (kind, phase) packet once (dose-matched with a once-before
    reminder); ``"every"`` at every decision point subject to ``cooldown_lines``
    complete code lines since the previous delivery of the same packet and
    ``max_per_rule``.  ``phased=False`` delivers body rules at the header instead.
    ``max_new_tokens`` bounds autoregressive selections (monotonic); ``max_context``
    bounds prompt + retained + inserted tokens.  ``policy="periodic"`` is the
    repetition-matched control (the same packets, at line boundaries every
    ``period_lines`` code lines regardless of the next line).
    """

    def __init__(
        self,
        backend,
        tokenizer,
        rules,
        max_new_tokens: int = 1536,
        max_context: int = 4096,
        eos_ids: tuple[int, ...] = (),
        deadline_seconds: float | None = None,
        max_insertions: int = 40,
        policy: str = "aligned",
        period_lines: int = 8,
        deliver: str = "first",
        cooldown_lines: int = 3,
        max_per_rule: int = 3,
        refeed: str = "auto",
        phased: bool = True,
        channel: str = "comment",
        rebuild_prompt=None,
    ) -> None:
        if policy not in ("aligned", "periodic"):
            raise ValueError(policy)
        if deliver not in ("first", "every"):
            raise ValueError(deliver)
        if refeed not in ("auto", "keyword", "indent"):
            raise ValueError(refeed)
        if channel not in ("comment", "user"):
            raise ValueError(channel)
        if channel == "user" and rebuild_prompt is None:
            raise ValueError("channel='user' needs rebuild_prompt(packets) -> ids")
        self.backend = backend
        self.tok = tokenizer
        self.rules = [
            (r[0], r[1], r[2]) if len(r) == 3 else (r[0], "header", r[1]) for r in rules
        ]
        self.max_new_tokens = max_new_tokens
        self.max_context = max_context
        self.eos_ids = set(eos_ids)
        self.deadline = deadline_seconds
        self.max_insertions = max_insertions
        self.policy = policy
        self.period_lines = period_lines
        self.deliver = deliver
        self.cooldown_lines = cooldown_lines
        self.max_per_rule = max_per_rule
        self.refeed = refeed
        self.phased = phased
        self.channel = channel
        self.rebuild_prompt = rebuild_prompt

    # -- packet selection ---------------------------------------------------
    def _packet(self, kind: str, phase: str, counts: dict) -> list[str]:
        if self.phased:
            sel = [t for k, p, t in self.rules if k == kind and p == phase]
        else:
            sel = (
                [t for k, p, t in self.rules if k == kind] if phase == "header" else []
            )
        return [t for t in sel if counts.get(t, 0) < self.max_per_rule]

    def _any_rules(self) -> list[str]:
        return [t for k, _, t in self.rules if k == "any"]

    # -- main loop -------------------------------------------------------------
    def generate(self, prompt_ids: list[int]) -> FocalResult:
        t0 = time.time()
        prompt_ids = list(prompt_ids)
        self.backend.prefill(prompt_ids)
        # pieces: ordered ("gen"|"ins"|"keep", ids); the sequence after the prompt
        # is their concatenation.  "ins" = cue text (stripped before scoring);
        # "keep" = re-fed remainder/keyword/indent (kept in the output).  Rollback
        # removes trailing generated tokens only, never past a non-gen piece.
        pieces: list[tuple[str, list[int]]] = []
        delivered: set[tuple[int, str]] = set()
        packets_done: set[tuple[str, str]] = set()
        counts: dict[str, int] = {}
        last_ins_line: dict[tuple[str, str], int] = {}
        delivered_lines: set[int] = set()
        any_done = False
        events: list[dict] = []
        reminders: list[str] = []
        n_ins_tokens = 0
        n_refed = 0
        n_insertions = 0
        steps = 0
        discarded = 0
        ended = timed_out = context_exceeded = False
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

        def n_gen() -> int:
            return sum(len(p) for k, p in pieces if k == "gen")

        while steps < self.max_new_tokens:
            if self.deadline is not None and time.time() - t0 > self.deadline:
                timed_out = True
                break
            if (
                len(prompt_ids) + sum(len(p) for _, p in pieces) + len(pending)
                >= self.max_context
            ):
                context_exceeded = True
                break
            nxt = self.backend.step(pending)
            steps += 1
            if nxt in self.eos_ids:
                pending = []
                ended = True
                break
            pending = [nxt]
            if pieces and pieces[-1][0] == "gen":
                pieces[-1][1].append(nxt)
            else:
                pieces.append(("gen", [nxt]))
            if n_insertions >= self.max_insertions:
                continue
            ids = flat()
            text = decode(ids)

            # ---------------------------------------------------------- periodic
            if self.policy == "periodic":
                if not text.endswith("\n"):
                    continue
                ok, n_lines, indent = code_line_count(text)
                if not ok or n_lines == 0 or n_lines % self.period_lines:
                    continue
                if n_lines in delivered_lines:
                    continue
                delivered_lines.add(n_lines)
                packet = [
                    t for _, _, t in self.rules if counts.get(t, 0) < self.max_per_rule
                ]
                if not packet:
                    continue
                block = cue_line("code", packet, indent)
                insert_ids = self.tok.encode(block, add_special_tokens=False)
                pieces.append(("ins", list(insert_ids)))
                pending = pending + list(insert_ids)
                n_ins_tokens += len(insert_ids)
                n_insertions += 1
                for t in packet:
                    counts[t] = counts.get(t, 0) + 1
                events.append(
                    {
                        "kind": "periodic",
                        "phase": "periodic",
                        "line": text.count("\n"),
                        "offset": len(text),
                        "rolled_back_tokens": 0,
                        "inserted_tokens": len(insert_ids),
                        "refed_keyword": "",
                        "rules": packet,
                    }
                )
                continue

            # ----------------------------------------------------------- aligned
            fired = None
            packet: list[str] = []
            label = ""
            key: tuple[str, str] | None = None
            for u in unit_starts(text):
                if u.kind == "decorated":
                    continue
                if u.kind == "body":
                    pkind = u.parent
                    if pkind == "method" and u.parent_name == "__init__":
                        pkind = "init"
                        phase_kind = "init"
                    elif pkind == "method" and _is_dunder(u.parent_name):
                        delivered.add((u.offset, "body"))
                        continue
                    else:
                        phase_kind = pkind
                    if pkind not in ("function", "method", "init"):
                        delivered.add((u.offset, "body"))
                        continue
                    if (u.offset, "body") in delivered:
                        continue
                    k = (phase_kind, "body")
                    if k in packets_done and self.deliver == "first":
                        delivered.add((u.offset, "body"))
                        continue
                    packet = self._packet(phase_kind, "body", counts)
                    if not packet:
                        delivered.add((u.offset, "body"))
                        continue
                    fired, key, label = u, k, LABELS[f"body:{phase_kind}"]
                    break
                if (u.offset, u.kind) in delivered:
                    continue
                if u.kind in ("function", "method", "class"):
                    # wait until the identifier is visible so dunder methods can be
                    # classified before rolling back (the whole line is regenerated)
                    line_text = text[u.offset :].split("\n")[0]
                    complete = (
                        "(" in line_text or ":" in line_text or "\n" in text[u.offset :]
                    )
                    if not u.name or not complete:
                        continue
                    if u.kind == "method" and _is_dunder(u.name):
                        delivered.add((u.offset, u.kind))
                        continue
                k = (u.kind, "header")
                if k in packets_done and self.deliver == "first":
                    delivered.add((u.offset, u.kind))
                    continue
                packet = self._packet(u.kind, "header", counts)
                if not packet:
                    delivered.add((u.offset, u.kind))
                    continue
                fired, key, label = u, k, LABELS[u.kind]
                break
            if fired is None:
                continue
            assert key is not None
            if self.deliver == "every" and key in packets_done:
                _, n_lines, _ = code_line_count(text[: fired.offset])
                if n_lines - last_ins_line.get(key, -(10**9)) < self.cooldown_lines:
                    delivered.add((fired.offset, fired.kind))
                    continue
            extra = [] if any_done else self._any_rules()
            full_packet = packet + extra
            # largest token prefix whose decode ends at or before the line start
            cut = len(ids)
            while cut > 0 and len(decode(ids[:cut])) > fired.offset:
                cut -= 1
            if cut < floor():
                delivered.add((fired.offset, fired.kind))
                continue
            kept_text = decode(ids[:cut])
            remainder = text[len(kept_text) : fired.offset]
            fired_line = text[fired.offset :].split("\n")[0]
            keyword = header_keyword(fired_line) if fired.kind != "body" else ""
            if self.refeed == "indent" or (
                self.refeed == "auto"
                and keyword != "@"
                and any("decorator" in t for t in full_packet)
            ):
                keyword = ""
            n_before = n_gen()
            removed = len(ids) - cut
            while removed > 0:
                k_, p = pieces[-1]
                assert k_ == "gen"
                if len(p) <= removed:
                    removed -= len(p)
                    pieces.pop()
                else:
                    del p[len(p) - removed :]
                    removed = 0
            discarded += n_before - n_gen()
            self.backend.crop(cut)

            if self.channel == "comment":
                block = cue_line(label, full_packet, fired.indent)
                keep_text = " " * fired.indent + keyword
                rem_ids = (
                    self.tok.encode(remainder, add_special_tokens=False)
                    if remainder
                    else []
                )
                ins_ids = self.tok.encode(block, add_special_tokens=False)
                keep_ids = (
                    self.tok.encode(keep_text, add_special_tokens=False)
                    if keep_text
                    else []
                )
                if rem_ids:
                    pieces.append(("keep", list(rem_ids)))
                pieces.append(("ins", list(ins_ids)))
                if keep_ids:
                    pieces.append(("keep", list(keep_ids)))
                pending = list(rem_ids) + list(ins_ids) + list(keep_ids)
                n_ins_tokens += len(ins_ids)
                n_refed += len(keep_ids) + len(rem_ids)
                inserted = len(ins_ids)
                new_offset = len(kept_text) + len(remainder) + len(block)
            else:
                reminders.append(cue_packet(label, full_packet))
                prefix_text = kept_text + remainder + " " * fired.indent + keyword
                prefix_ids = self.tok.encode(prefix_text, add_special_tokens=False)
                prompt_ids = list(self.rebuild_prompt(list(reminders)))
                self.backend.prefill(prompt_ids, prefix_ids)
                pieces = [("keep", list(prefix_ids))] if prefix_ids else []
                pending = []
                n_refed += len(prefix_ids) - cut if len(prefix_ids) > cut else 0
                inserted = 0
                new_offset = len(prefix_text) - len(" " * fired.indent + keyword)
            n_insertions += 1
            packets_done.add(key)
            any_done = any_done or bool(extra)
            for t in full_packet:
                counts[t] = counts.get(t, 0) + 1
            last_ins_line[key] = code_line_count(kept_text + remainder)[1]
            delivered.add((new_offset, fired.kind))
            events.append(
                {
                    "kind": fired.kind,
                    "phase": key[1],
                    "packet_kind": key[0],
                    "line": fired.line,
                    "offset": fired.offset,
                    "name": fired.name or fired.parent_name,
                    "rolled_back_tokens": n_before - n_gen(),
                    "inserted_tokens": inserted,
                    "refed_keyword": keyword,
                    "rules": full_packet,
                }
            )

        ids = flat()
        text = decode(ids)
        spans = []
        acc: list[int] = []
        for k, p in pieces:
            a = len(decode(acc))
            acc = acc + p
            b = len(decode(acc))
            if k == "ins":
                spans.append((a, b))
        if self.policy == "periodic":
            starts = {u.offset for u in unit_starts(text)}
            for e, sp in zip(events, spans):
                e["adjacent_to_unit"] = sp[1] in starts
        gen_ids = [i for k, p in pieces if k == "gen" for i in p]
        return FocalResult(
            text=text,
            generated_ids=gen_ids,
            inserted_spans=spans,
            inserted_tokens=n_ins_tokens,
            refed_tokens=n_refed,
            steps=steps,
            discarded_tokens=discarded,
            prompt_tokens=len(prompt_ids),
            reminders=reminders,
            events=events,
            ended_by_eos=ended,
            timed_out=timed_out,
            truncated=(
                not ended
                and not timed_out
                and not context_exceeded
                and steps >= self.max_new_tokens
            ),
            context_exceeded=context_exceeded,
            seconds=time.time() - t0,
        )


class HFBackend:
    """``transformers`` causal LM backend with a croppable ``DynamicCache``."""

    def __init__(self, model) -> None:
        self.model = model
        self.cache = None
        self.prompt: list[int] = []
        self.seq: list[int] = []  # post-prompt tokens present in the cache
        self._refeed: list[int] = []  # tokens whose KV was dropped, to re-feed
        self._next = None

    def _forward(self, ids: list[int]) -> int:
        import torch

        t = torch.tensor([ids], device=self.model.device)
        with torch.no_grad():
            out = self.model(t, past_key_values=self.cache, use_cache=True)
        self.cache = out.past_key_values
        return int(out.logits[0, -1].argmax())

    def prefill(self, prompt_ids: list[int], prefix_ids=()) -> None:
        from transformers import DynamicCache

        self.cache = DynamicCache()
        self.prompt = list(prompt_ids)
        self.seq = list(prefix_ids)
        self._refeed = []
        self._next = self._forward(self.prompt + self.seq)

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
        total = len(self.prompt) + len(self.seq)
        remove = total - (keep - 1)
        if remove > 0:
            self.cache.crop(-remove)
        last = (self.prompt + self.seq)[keep - 1]
        self.seq = self.seq[:n]
        self._refeed = [last]
        self._next = None
