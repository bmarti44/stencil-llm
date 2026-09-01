# ruff: noqa: E501
"""The obligation-state gate (R3b) — deterministic, training-free.

Empirical basis (564 harvested causal moments, WORKLOG 2026-09-01):
the six registered model-state features carried no held-out signal
(AUC 0.46-0.54 by session/topic/family); obligation state reaches
0.70-0.76 on the same splits. The rule below is the best computable
policy found: +2.6pts over 72 turns, cluster-bootstrap CI [+1, +12],
P(net<=0)=0.018 — versus fire-always +1.7 with a CI spanning zero.

Three conditions, each with a measured justification:
 1. OUTSTANDING FIXABLE: an unsatisfied constraint whose family the
    actuator can actually repair (postscript 7/7, placeholders 20/38,
    kw_exist 28/69; vs title 0/31, caps 3/56, n_words_max 2/69).
 2. NO LIVE WORD CAP: sustained focus lengthens responses near the
    limit (86.5 -> 92.4 words); word caps account for 25 of 57 total
    breaks. Live-cap turns are 6 helpful / 23 harmful.
 3. PAST THE POSITION FLOOR: fixes are available at any onset, but
    breaks concentrate early (10/5/2/0 by response quartile), so
    firing late avoids whole-response rewrites.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

# families the actuator demonstrably repairs (fix rate >= ~10%)
FIXABLE_FAMILIES = frozenset({
    "detectable_content:postscript",
    "detectable_content:number_placeholders",
    "keywords:existence",
    "keywords:frequency",
    "detectable_format:number_bullet_lists",
})

# instruction ids that VETO firing when live (harm engine)
VETO_INSTRUCTION_IDS = frozenset({"length_constraints:number_words"})

POSITION_FLOOR = 0.5          # registered: fire only past half the expected response
DEFAULT_EXPECTED_TOKENS = 320  # fallback when no prior-turn length is known


def is_veto(instruction_id: str, kwargs: dict) -> bool:
    """A live UPPER-BOUND word limit vetoes firing; a lower bound does not
    (only the cap is the harm engine — 'at least N words' cannot be
    violated by adding content)."""
    if instruction_id not in VETO_INSTRUCTION_IDS:
        return False
    relation = (kwargs or {}).get("relation")
    return relation == "less than"


def position_proxy(tokens_so_far: int, expected_total: int | None) -> float:
    """Oracle-free position estimate: tokens emitted so far over the
    EXPECTED total (previous turn's native length, or the registered
    default). Never uses the final length of the response in flight."""
    total = expected_total if expected_total else DEFAULT_EXPECTED_TOKENS
    if total <= 0:
        return 1.0
    return min(1.0, max(0.0, tokens_so_far / total))


def outstanding_constraints(row: dict, partial_text: str) -> list[tuple[str, dict]]:
    """Constraints NOT yet satisfied by the text generated so far, judged
    by the VENDORED checkers (the same code that scores the benchmark).
    Deterministic: the per-row seed pin is applied, as in scoring."""
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent.parent
    if str(root / "vendor") not in sys.path:
        sys.path.insert(0, str(root / "vendor"))
    import langdetect
    langdetect.DetectorFactory.seed = 0
    from ifeval import instructions_registry

    random.seed(row["key"])
    out = []
    for iid, kw in zip(row["instruction_id_list"], row["kwargs"], strict=True):
        inst = instructions_registry.INSTRUCTION_DICT[iid](iid)
        inst.build_description(**{k: v for k, v in (kw or {}).items() if v})
        satisfied = bool(partial_text.strip()) and inst.check_following(partial_text)
        if not satisfied:
            out.append((iid, kw or {}))
    return out


@dataclass(frozen=True)
class GateDecision:
    fire: bool
    reason: str


def should_fire(*, outstanding, live, position: float,
                position_floor: float = POSITION_FLOOR) -> GateDecision:
    """The frozen R3b policy. `outstanding` and `live` are lists of
    (instruction_id, kwargs); `position` is the oracle-free proxy.
    position_floor is explicit so callers cannot silently diverge from
    the policy they think they configured."""
    if any(is_veto(iid, kw) for iid, kw in live):
        return GateDecision(False, "veto_word_cap")
    if not any(iid in FIXABLE_FAMILIES for iid, _ in outstanding):
        return GateDecision(False, "no_outstanding_fixable")
    if position < position_floor:
        return GateDecision(False, "too_early")
    return GateDecision(True, "fire")


@dataclass
class GatedResult:
    text: str
    n_generated: int
    truncated: bool
    timed_out: bool
    fired: bool
    fire_step: int | None
    decisions: list


def generate_gated(model, tokenizer, prompt: str, row: dict, *,
                   expected_total: int | None = None,
                   position_floor: float = POSITION_FLOOR,
                   check_every: int = 8, dose: float = 3.0,
                   max_new: int = 1024, deadline_s: float | None = None,
                   raw_context: bool = False, spans=None):
    """Cached greedy generation with the obligation gate.

    Every `check_every` tokens the vendored checkers are run on the text
    so far; when the frozen R3b policy says fire, a SUSTAINED bias over
    all instruction spans switches on for the remainder (the actuator
    Opus validated). Before that the model is bitwise untouched.
    """
    import time

    import torch

    from stencil.bench import EOS, TMPL, WAVE_LAYERS
    from stencil.ctrb import constraint_spans_in_context, uniform_span_bias
    from stencil.qwen3 import KVCache

    context = prompt if raw_context else TMPL.format(p=prompt)
    if spans is None:
        spans = constraint_spans_in_context(tokenizer, context)
    ids = tokenizer.encode(context).ids
    cache = KVCache()
    out, decisions = [], []
    fired, fire_step = False, None
    live = list(zip(row["instruction_id_list"], row["kwargs"], strict=True))
    t0 = time.monotonic()
    timed_out = False

    def hook_factory(past):
        def hook(h20):
            total = past + h20.shape[1]
            row_bias = None
            for sp in spans:
                b = uniform_span_bias(h20.shape[1], total, tuple(sp),
                                      amount=dose, device=h20.device)
                row_bias = b if row_bias is None else row_bias + b
            if row_bias is None:
                return None
            return {layer: row_bias for layer in WAVE_LAYERS}
        return (20, hook)

    with torch.no_grad():
        logits = model(torch.tensor([ids], device="cuda"), cache=cache)
        nxt = int(logits[0, -1].argmax())
        while nxt not in EOS and len(out) < max_new:
            if deadline_s is not None and time.monotonic() - t0 > deadline_s:
                timed_out = True
                break
            out.append(nxt)
            if not fired and len(out) % check_every == 0:
                partial = tokenizer.decode(out)
                outstanding = outstanding_constraints(row, partial)
                pos = position_proxy(len(out), expected_total)
                d = should_fire(outstanding=outstanding, live=live, position=pos,
                                position_floor=position_floor)
                decisions.append({"step": len(out), "reason": d.reason,
                                  "position": round(pos, 4),
                                  "n_outstanding": len(outstanding)})
                if d.fire:
                    fired, fire_step = True, len(out)
            hook = hook_factory(cache.length) if fired else None
            logits = model(torch.tensor([[nxt]], device="cuda"), cache=cache,
                           bias_hook=hook)
            nxt = int(logits[0, -1].argmax())
    return GatedResult(tokenizer.decode(out), len(out), len(out) >= max_new,
                       timed_out, fired, fire_step, decisions)
