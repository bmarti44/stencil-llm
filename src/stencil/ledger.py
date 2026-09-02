# ruff: noqa: E501
"""LEDGER component B (LEDGER-PLAN.md): the held set of instructions.

Entries are explicit and auditable: text, token span in the FULL
context's coordinates (clamped to the enclosing user message — the
coordinate-frame bug that invalidated E2 is guarded by a decode-and-
compare test), pooled trunk key (h20 mean over the span), turn
introduced, status ("unknown" until E3's probe fills it).

Salience (component A, ``stencil.salience``) is imported LAZILY and is
expected to expose ``is_instruction(sentence: str) -> bool``.  When it is
unavailable a documented cue heuristic is used and every entry carries
``provenance="heuristic"``; ``is_automatic`` is then False and such a run
is NOT the registered automatic condition.

Selection reuses the existing WaveController's W_q/W_k; emphasis is the
sustained uniform attention bias (ctrb.uniform_span_bias over layers
20-27) that the E2/obligation-gate actuator validated.
"""
from __future__ import annotations

import re
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

TEXT_LEDGER_HEADER = "Earlier user instructions restated verbatim:"
# Documented fallback cues (used ONLY when stencil.salience is unavailable).
HEURISTIC_CUES = (
    "constraint:", "your response", "your answer", "your entire response",
    "should ", "must ", "do not ", "don't ", "avoid ", "include ", "make sure",
    "at least ", "at most ", "no more than", "less than ", "fewer than ", "exactly ",
    "wrap ", "end with", "end your", "start with", "begin with", "finish with",
    "highlight", "in all lowercase", "in all capital", "in english", "in markdown",
    "use ", "answer with", "respond with", "written in", "the letter ", "the word ",
    "paragraph", "bullet", "postscript", "p.s.", "title", "placeholder", "section",
)


@dataclass
class Entry:
    text: str
    span: tuple[int, int]
    key: object | None
    turn_introduced: int
    status: str = "unknown"
    provenance: str = "salience"
    instruction_ids: list[str] = field(default_factory=list)  # linkage (LEDGER-PLAN amendment)

    def to_record(self) -> dict:
        return {"text": self.text, "span": list(self.span), "turn_introduced": self.turn_introduced,
                "status": self.status, "provenance": self.provenance, "has_key": self.key is not None,
                "instruction_ids": list(self.instruction_ids)}


_SPLIT = re.compile(r"(?<=[.!?])\s+(?=\S)|(?<=[.!?][\"')\]])\s+(?=\S)")


def segment_char_spans(text: str) -> list[tuple[int, int]]:
    """Fallback segmenter (used ONLY when stencil.salience is unavailable):
    newline-first, then terminator-boundary split; a fragment that is only a
    closing quote/bracket EXTENDS the previous span.  Spans are computed
    from match offsets, never re-searched in the text — re-searching a
    concatenated fragment crashed on conversation 769 (sol, 2026-09-01)."""
    spans: list[tuple[int, int]] = []
    for line in re.finditer(r"[^\r\n]+", text):
        ls = line.start()
        pieces, cursor = [], 0
        for m in _SPLIT.finditer(line.group()):
            pieces.append((cursor, m.start()))
            cursor = m.end()
        pieces.append((cursor, len(line.group())))
        for a, b in pieces:
            seg = line.group()[a:b]
            lead = len(seg) - len(seg.lstrip())
            trail = len(seg) - len(seg.rstrip())
            if b - trail <= a + lead:
                continue
            a_abs, b_abs = ls + a + lead, ls + b - trail
            if spans and re.fullmatch(r'["\')\]]+', text[a_abs:b_abs]):
                spans[-1] = (spans[-1][0], b_abs)
            else:
                spans.append((a_abs, b_abs))
    return spans


def segment_sentences(text: str) -> list[str]:
    """The sentences of ``segment_char_spans`` (fallback path only)."""
    return [text[a:b] for a, b in segment_char_spans(text)]


def heuristic_is_instruction(sentence: str) -> bool:
    low = sentence.lower()
    return any(cue in low for cue in HEURISTIC_CUES)


SANITY_PROBE = (  # a classifier that cannot separate these is untrained/over-inclusive
    ("It fell all night on the tin roof and the gutters overflowed.", False),
    ("Do not use any commas in your response.", True),
)


@dataclass(frozen=True)
class Salience:
    classify: Callable[[str], bool]
    segment: Callable[[str], list[tuple[int, int]]]  # char spans within a turn
    provenance: str                                  # "salience" | "heuristic"
    note: str = ""


def resolve_salience(salience: Callable[[str], bool] | None = None) -> Salience:
    """Never silent: the documented heuristic is used only when
    ``stencil.salience.is_instruction`` is unavailable OR fails the sanity
    probe (an untrained classifier admits every sentence); ``note`` says why."""
    if salience is not None:
        return Salience(salience, segment_char_spans, "salience")
    try:
        import importlib
        module = importlib.import_module("stencil.salience")  # lazy: component A may not exist yet
        fn = module.is_instruction
    except (ImportError, AttributeError) as exc:
        return Salience(heuristic_is_instruction, segment_char_spans, "heuristic",
                        f"stencil.salience unavailable ({exc.__class__.__name__})")
    is_trained = getattr(module, "is_trained", None)
    if is_trained is not None and not is_trained():
        return Salience(heuristic_is_instruction, segment_char_spans, "heuristic",
                        "stencil.salience reports an untrained model")
    try:
        probe_ok = all(bool(fn(sentence)) == want for sentence, want in SANITY_PROBE)
    except RuntimeError:  # the module refuses to score with an untrained model
        probe_ok = False
    if not probe_ok:
        return Salience(heuristic_is_instruction, segment_char_spans, "heuristic",
                        "stencil.salience failed the sanity probe (untrained or over-inclusive)")
    segment = getattr(module, "split_sentences", None) or segment_char_spans
    return Salience(fn, segment, "salience")


def is_automatic(entries: Sequence[Entry]) -> bool:
    """True iff every entry was admitted by the salience classifier (the
    registered 'automatically' condition)."""
    return all(e.provenance == "salience" for e in entries)


def _user_turns(context: str) -> list[tuple[int, int]]:
    marker = "<|im_start|>user\n"
    turns, cursor = [], 0
    while True:
        start = context.find(marker, cursor)
        if start < 0:
            return turns
        content_start = start + len(marker)
        content_end = context.find("<|im_end|>", content_start)
        if content_end < 0:
            raise ValueError("unterminated user turn")
        turns.append((content_start, content_end))
        cursor = content_end + 1


def build_ledger(tokenizer, context: str, model=None, salience=None) -> list[Entry]:
    """Segment every USER turn of a pre-rendered context into sentences,
    keep the instructions, map each to token span in ``context``'s own
    coordinates (clamped to the user message), pool h20 keys if a model
    is given.  ``salience`` is a resolved ``Salience`` (the runner's path:
    classifier AND segmenter travel together), a bare classifier (fallback
    segmenter — test/stub use only), or None (resolve the default)."""
    sal = salience if isinstance(salience, Salience) else resolve_salience(salience)
    enc = tokenizer.encode(context)
    entries: list[Entry] = []
    for turn, (cs, ce) in enumerate(_user_turns(context), start=1):
        content = context[cs:ce]
        for at, end in sal.segment(content):
            sentence = content[at:end]
            if not sentence.strip() or not sal.classify(sentence):
                continue
            s_abs, e_abs = cs + at, min(cs + end, ce)
            toks = [i for i, (a, b) in enumerate(enc.offsets) if a < e_abs and b > s_abs and a >= cs and b <= ce]
            if not toks:
                continue
            entries.append(Entry(sentence, (toks[0], toks[-1] + 1), None, turn, provenance=sal.provenance))
    if model is not None and entries:
        import torch
        device = next(model.parameters()).device
        with torch.no_grad():
            _, h20 = model(torch.tensor([enc.ids], device=device), capture_hidden=20)
        for e in entries:
            a, b = e.span
            e.key = h20[0, a:b].float().mean(0)
    return entries


def instruction_origins(id_lists_by_turn: dict[int, Sequence[str]], current_turn: int) -> list[dict]:
    """Multi-IF instruction_id_list is CUMULATIVE per turn (turn t = turn t-1's
    list + the ids introduced at t), so the origin turn of the constraint at
    position j is the first turn whose list reaches j.  Positional, so a
    family that recurs across turns is still attributed to its own turn."""
    turns = sorted(t for t in id_lists_by_turn if t <= current_turn)
    if current_turn not in id_lists_by_turn:
        raise ValueError("current turn has no instruction list")
    prev: list[str] = []
    origin_of: list[int] = []
    for t in turns:
        ids = list(id_lists_by_turn[t])
        if ids[: len(prev)] != prev:
            raise ValueError(f"instruction lists are not cumulative at turn {t}")
        origin_of.extend([t] * (len(ids) - len(prev)))
        prev = ids
    return [{"index": j, "id": iid, "origin_turn": origin_of[j], "aged": origin_of[j] < current_turn,
             "entry_indices": []}
            for j, iid in enumerate(prev)]


def link_entries(entries: Sequence[Entry], tokenizer, context: str, origins: Sequence[dict]) -> str:
    """Record on each entry the instruction ids whose constraint it covers and
    on each origin the entry indices that cover it.  Uses
    ``e2.constraint_span_records`` (token-span overlap; the k-th marked
    constraint of a turn is that turn's k-th introduced id) when the context
    carries "Constraint:" markers; Multi-IF carries none, so it falls back to
    ORIGIN-TURN granularity (every entry of a turn links to every id that
    turn introduced).  Returns the granularity used ("constraint_span" |
    "origin_turn") so the record discloses it."""
    from stencil.e2 import constraint_span_records

    for e in entries:
        e.instruction_ids = []
    for o in origins:
        o["entry_indices"] = []
    by_turn: dict[int, list[dict]] = {}
    for o in origins:
        by_turn.setdefault(o["origin_turn"], []).append(o)
    records = constraint_span_records(tokenizer, context)
    if records:
        seen: dict[int, int] = {}
        for r in records:
            k = seen.get(r["origin_turn"], 0)
            seen[r["origin_turn"]] = k + 1
            ids_here = by_turn.get(r["origin_turn"], [])
            if k >= len(ids_here):
                continue  # more markers than registered ids: leave the extra unlinked
            o = ids_here[k]
            ra, rb = r["span"]
            for i, e in enumerate(entries):
                a, b = e.span
                # a marked constraint span runs up to the NEXT marker, so a neighbouring
                # entry's leading-space token overlaps it: require >= half the entry
                if 2 * max(0, min(b, rb) - max(a, ra)) >= (b - a):
                    e.instruction_ids.append(o["id"])
                    o["entry_indices"].append(i)
        return "constraint_span"
    for i, e in enumerate(entries):
        for o in by_turn.get(e.turn_introduced, []):
            e.instruction_ids.append(o["id"])
            o["entry_indices"].append(i)
    return "origin_turn"


def matched_nonledger_control(*, total_len: int, selected: Sequence[tuple[int, int]],
                              ledger_spans: Sequence[tuple[int, int]],
                              user_turns: Sequence[tuple[int, int]]) -> tuple[list[tuple[int, int] | None], list[str]]:
    """The specificity control (LEDGER-PLAN amendment): for each SELECTED span
    a window of the SAME width, disjoint from EVERY ledger entry (selected or
    not, aged or fresh) and from the other control windows, at the nearest
    position — inside the same user turn when possible ("same_turn"), else
    any user turn ("other_user_turn"), else anywhere ("outside_user_turns").
    Same dose is applied by the caller.  ``e2.mass_matched_nonconstraint_control``
    is the diffuse-complement control sol rejected and is NOT used.

    NEVER raises for an impossible window (sol round 2: conversation 145
    turn 2 — aged widths 34 and 19, longest non-ledger run 31 — crashed the
    arm in both selection orders): that span gets control ``None`` and tier
    ``"none"``; the caller records ``control_incomplete`` and excludes the
    turn from the neural-vs-specificity comparison.  Both lists align with
    ``selected``."""
    blocked = [False] * total_len
    for a, b in ledger_spans:
        if not 0 <= a < b <= total_len:
            raise ValueError("ledger span outside context")
        for i in range(a, b):
            blocked[i] = True
    control: list[tuple[int, int] | None] = []
    tiers: list[str] = []

    def free(a, b):
        return 0 <= a and b <= total_len and not any(blocked[a:b])

    for (sa, sb) in selected:
        w = sb - sa
        if w <= 0:
            raise ValueError("empty selected span")
        home = [t for t in user_turns if t[0] <= sa and sb <= t[1]]
        candidates = (
            ("same_turn", home),
            ("other_user_turn", [t for t in user_turns if t not in home]),
            ("outside_user_turns", [(0, total_len)]),
        )
        found = None
        for tier, regions in candidates:
            starts = sorted({s for (ra, rb) in regions for s in range(ra, rb - w + 1)},
                            key=lambda s: (abs(s - sa), s))
            for s in starts:
                if free(s, s + w):
                    found = (tier, (s, s + w))
                    break
            if found:
                break
        if found is None:  # disclosed, not fatal
            control.append(None)
            tiers.append("none")
            continue
        tier, (a, b) = found
        for i in range(a, b):
            blocked[i] = True
        control.append((a, b))
        tiers.append(tier)
    return control, tiers


def select(entries: Sequence[Entry], query_h20, ctrl, top_k: int = 2) -> list[Entry]:
    """Top-k entries by the EXISTING WaveController score cos(W_q q, W_k key);
    ties broken by ledger order. Returns the Entry objects themselves."""
    import torch
    import torch.nn.functional as F

    if not entries:
        return []
    if any(e.key is None for e in entries):
        raise ValueError("select() needs pooled keys; build the ledger with a model")
    with torch.no_grad():
        keys = torch.stack([e.key for e in entries]).float().to(query_h20.device)
        q = F.normalize(ctrl.W_q(query_h20.float().reshape(1, -1)), dim=-1)
        k = F.normalize(ctrl.W_k(keys), dim=-1)
        scores = (q @ k.T)[0].tolist()
    order = sorted(range(len(entries)), key=lambda i: (-scores[i], i))
    return [entries[i] for i in order[:top_k]]


def render_text_ledger(entries: Sequence[Entry]) -> str:
    if not entries:
        return ""
    return TEXT_LEDGER_HEADER + "\n" + "\n".join(f"- {e.text}" for e in entries)


def parse_text_ledger(text: str) -> list[str]:
    lines = text.splitlines()
    if not lines or lines[0] != TEXT_LEDGER_HEADER:
        return []
    return [line[2:] for line in lines[1:]]


def text_ledger_context(context: str, entries: Sequence[Entry]) -> str:
    """The TEXTUAL arm: the same entries re-appended verbatim inside the
    final user message, before the assistant turn."""
    rendered = render_text_ledger(entries)
    if not rendered:
        return context
    cut = context.rfind("<|im_end|>")
    if cut < 0 or context.rfind("<|im_start|>user") > cut:
        raise ValueError("context must end with a closed user turn")
    return context[:cut] + "\n\n" + rendered + context[cut:]


def context_tokens_added(tokenizer, base_context: str, arm_context: str) -> int:
    return len(tokenizer.encode(arm_context).ids) - len(tokenizer.encode(base_context).ids)


@dataclass(frozen=True)
class SustainedResult:
    text: str
    n_generated: int
    truncated: bool
    timed_out: bool
    spans: tuple[tuple[int, int], ...]
    biased_tokens: int
    select_scores: tuple = field(default=())
    prompt_tokens: int = 0            # MEASURED length of the context actually sent
    ids: tuple[int, ...] = field(default=())  # generated token ids (bitwise comparisons)


def generate_sustained(model, tokenizer, context: str, *, spans=None, select_fn=None,
                       dose: float = 3.0, max_new: int = 1024, deadline_s: float | None = None) -> SustainedResult:
    """KV-cached greedy generation over a RAW context with a sustained
    uniform bias (dose, layers 20-27) over ``spans`` — fixed, or chosen
    ONCE by ``select_fn(query_h20)`` from the prefill's final-row h20
    (query = current h20; the bias then persists for the whole response).
    Empty spans -> no hook is ever installed -> bitwise the base path."""
    import torch

    from stencil.bench import EOS, WAVE_LAYERS
    from stencil.ctrb import uniform_span_bias
    from stencil.qwen3 import KVCache

    if (spans is None) == (select_fn is None):
        raise ValueError("give exactly one of spans / select_fn")
    ids = tokenizer.encode(context).ids
    P = len(ids)
    device = next(model.parameters()).device
    cache = KVCache()
    out: list[int] = []
    chosen: list[tuple[int, int]] = [tuple(s) for s in spans] if spans is not None else []
    for a, b in chosen:
        if not 0 <= a < b <= P:
            raise ValueError("span outside the prompt")

    def hook_factory(past):
        def hook(h20):
            if past == 0 and select_fn is not None:
                chosen.extend(tuple(s) for s in select_fn(h20[0, P - 1].float()))
            if not chosen or dose == 0.0:
                return None
            total = past + h20.shape[1]
            row = None
            for sp in chosen:
                b = uniform_span_bias(h20.shape[1], total, sp, amount=dose, device=h20.device)
                row = b if row is None else row + b
            return {layer: row for layer in WAVE_LAYERS}
        return (20, hook)

    active = select_fn is not None or (bool(chosen) and dose != 0.0)
    t0 = time.monotonic()
    timed_out = False
    biased = 0
    with torch.no_grad():
        logits = model(torch.tensor([ids], device=device), cache=cache,
                       bias_hook=hook_factory(0) if active else None)
        active = bool(chosen) and dose != 0.0
        nxt = int(logits[0, -1].argmax())
        while nxt not in EOS and len(out) < max_new:
            if deadline_s is not None and time.monotonic() - t0 > deadline_s:
                timed_out = True
                break
            out.append(nxt)
            biased += int(active)
            logits = model(torch.tensor([[nxt]], device=device), cache=cache,
                           bias_hook=hook_factory(cache.length) if active else None)
            nxt = int(logits[0, -1].argmax())
    return SustainedResult(tokenizer.decode(out), len(out), len(out) >= max_new, timed_out,
                           tuple(chosen), biased, prompt_tokens=P, ids=tuple(out))


def paired_drop_table(reference: Sequence[bool], candidate: Sequence[bool]) -> dict:
    """n10 = reference right / candidate wrong (a DROP), n01 = converse."""
    if len(reference) != len(candidate):
        raise ValueError("paired outcomes must align")
    n10 = sum(1 for r, c in zip(reference, candidate, strict=True) if r and not c)
    n01 = sum(1 for r, c in zip(reference, candidate, strict=True) if c and not r)
    return {"n10": n10, "n01": n01, "n": len(reference)}


def non_inferiority_summary(reference: Sequence[bool], candidate: Sequence[bool], *, margin_points: float = 2.0) -> dict:
    """Registered primary: Tango one-sided 95% upper bound on the candidate's
    per-constraint accuracy DROP vs the reference, in points; non-inferior
    iff bound < margin (strict). Raw counts included so a reviewer can
    recompute."""
    from stencil.stats import tango_upper_bound

    table = paired_drop_table(reference, candidate)
    n = table["n"]
    out = {**table, "margin_points": margin_points,
           "drop_points": (100.0 * (table["n10"] - table["n01"]) / n) if n else None,
           "upper_bound_points": None, "non_inferior": None, "error": None}
    if n == 0:
        out["error"] = "no paired cells"
        return out
    try:
        ub = 100.0 * tango_upper_bound(table["n10"], table["n01"], n)
    except (ValueError, RuntimeError) as exc:  # fail-closed, disclosed
        out["error"] = str(exc)
        return out
    out["upper_bound_points"] = ub
    out["non_inferior"] = bool(ub < margin_points)
    return out
