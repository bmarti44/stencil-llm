# ruff: noqa: E501
"""T2 session generator (TIMED-SELECTOR-PLAN, CONTRACT v3).

Scripted multi-turn sessions: user turns author the ledger (set/update/
clear), work turns request code, environment feedback is deterministic
checker text, distractor turns quote superseded/conflicting values, and
compactions truncate conversation turns while the LIVE LEDGER SURVIVES for
every arm (v3: the wire is tested on selection; memory is the ledger's job).

Every work turn emits immutable opportunity records:
(opportunity-id, session, turn, obligation-id, target-object, moment-class,
active-expected-value, superseded-values, scorer-id) with counterfactual
cell in {active, absent, cleared, stale_only}.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import torch

from .qwen_task import (
    CODE_PREFIXES,
    CODE_REQUESTS,
    DOC_OPENERS,
    FILLER,
    HINT_TYPES,
)

TYPES = ["prefix", "doc", "hint"]
STRATA = {20: 8, 40: 12, 60: 16}  # turns -> surviving-K at compaction (v3)
COMPACTION_TURNS = {20: [12], 40: [16, 30], 60: [18, 36, 50]}

SENT = {
    "prefix": "All function names must start with '{v}_'.",
    "doc": "Every docstring must begin with the word '{v}'.",
    "hint": "All function arguments must be type-hinted as {v}.",
}
SENT_UNSEEN_FMT = {  # held-out FORMAT of the trained naming type (val/final)
    "prefix": "Use the naming scheme {v}_* for every function you define.",
}
POOLS = {"prefix": CODE_PREFIXES, "doc": DOC_OPENERS, "hint": HINT_TYPES}


@dataclass
class Turn:
    kind: str            # user_set|user_update|user_clear|work|env|distractor
    text: str
    obligation: tuple | None = None  # (type, value) for authoring turns


@dataclass
class Opportunity:
    opportunity_id: str
    turn: int
    obligation_id: str
    target_object: str    # function name or "arg:<name>"
    moment_class: str     # prefix|doc|hint|comment
    cell: str             # active|absent|cleared|stale_only
    expected: str | None  # active value (None unless cell == active)
    superseded: list[str] = field(default_factory=list)
    scorer_id: str = "ast"


@dataclass
class T2Session:
    seed: int
    stratum: int
    turns: list[Turn]
    work_turns: list[int]
    fn_names: dict[int, str]           # work turn -> requested function name
    ops: dict[int, str]                # work turn -> operation key
    ledger_at: dict[int, dict]         # work turn -> {type: value} (live)
    superseded_at: dict[int, dict]     # work turn -> {type: [values]}
    opportunities: list[Opportunity]
    compaction_turns: list[int]
    held_out: dict                      # val/final extras


def _pick(pool, g):
    return pool[int(torch.randint(0, len(pool), (1,), generator=g))]


def ledger_text(ledger: dict, unseen_fmt: bool = False) -> str:
    lines = ["Current coding standards (authoritative):"]
    for ty in TYPES:
        if ty in ledger:
            tmpl = SENT_UNSEEN_FMT.get(ty) if unseen_fmt and ty == "prefix" else SENT[ty]
            lines.append(" " + (tmpl or SENT[ty]).format(v=ledger[ty]))
    if "comment" in ledger:
        lines.append(" Every function body must end with the comment '# reviewed'.")
    return "".join(lines)


def generate_t2(seed: int, stratum: int = 20, split: str = "dev", interference: str = "v3") -> T2Session:
    g = torch.Generator().manual_seed(seed)
    n_turns = stratum
    turns: list[Turn] = []
    ledger: dict = {}
    superseded: dict = {ty: [] for ty in TYPES}
    cleared: set = set()
    opportunities: list[Opportunity] = []
    work_turns, fn_names, ops = [], {}, {}
    ledger_at, superseded_at = {}, {}
    held_out = {}
    fn_counter = 0

    # scripted schedule: derive a deterministic turn plan
    # guarantee counterfactual coverage: first work turn happens with only 2
    # of 3 types set (one 'absent'), one type is cleared mid-session, updates
    # create stale material quoted by distractors.
    order = [TYPES[int(i)] for i in torch.randperm(3, generator=g)]
    plan: list[tuple] = []
    plan.append(("user_set", order[0]))               # t0
    plan.append(("user_set", order[1]))               # t1 (cleared at t4; its set text ages out at compaction)
    plan.append(("work", None))                       # t2: order[2] ABSENT
    plan.append(("env", None))                        # t3
    plan.append(("user_clear", order[1]))             # t4: cleared pre-compaction-window
    plan.append(("user_set", order[2]))               # t5
    plan.append(("user_update", order[0]))            # t6: creates stale value
    plan.append(("distractor", order[0]))             # t7: quotes it (visible)
    plan.append(("work", None))                       # t8: order[0] active; order[1] stale_only (t1 visible pre-compaction)
    plan.append(("env", None))                        # t9
    plan.append(("filler", None))                     # t10
    plan.append(("filler", None))                     # t11
    plan.append(("work", None))                       # t12+: post-compaction (stratum 20: ct=12) — order[1] CLEARED (t1/t4 aged out of window)
    plan.append(("env", None))
    if split in ("val", "final"):
        plan.append(("user_set_comment", None))
        plan.append(("work", None))                   # held-out comment type active
        plan.append(("env", None))
    while len(plan) < n_turns - 2:
        r = float(torch.rand((), generator=g))
        if r < 0.25:
            ty = _pick(TYPES, g)
            plan.append(("user_update", ty) if ty in ledger or True else ("user_set", ty))
        elif r < 0.45:
            plan.append(("distractor", _pick(TYPES, g)))
        elif r < 0.7:
            plan.append(("work", None))
            plan.append(("env", None))
        else:
            plan.append(("filler", None))
    plan = plan[:n_turns]

    if interference == "s0":
        plan2 = []
        for step in plan:
            if step[0] == "work":
                plan2.append(("s0_note", None))
                plan2.append(("s0_note", None))
            plan2.append(step)
        plan = plan2  # session lengthens by 2 turns per work (registered delta)
    for ti, (kind, ty) in enumerate(plan):
        if kind == "user_set" and ty is not None:
            v = _pick(POOLS[ty], g)
            ledger[ty] = v
            cleared.discard(ty)
            turns.append(Turn("user_set", f"From now on: {SENT[ty].format(v=v)}", (ty, v)))
        elif kind == "user_set_comment":
            ledger["comment"] = "# reviewed"
            held_out["comment"] = True
            turns.append(Turn("user_set", "New standard: every function body must end with the comment '# reviewed'.", ("comment", "# reviewed")))
        elif kind == "user_update" and ty is not None:
            if ty in ledger:
                superseded[ty].append(ledger[ty])
            old = ledger.get(ty)
            v = _pick([x for x in POOLS[ty] if x != old], g)
            ledger[ty] = v
            cleared.discard(ty)
            turns.append(Turn("user_update", f"Update: {SENT[ty].format(v=v)} (replaces the earlier rule.)", (ty, v)))
        elif kind == "user_clear" and ty is not None:
            if ty in ledger:
                superseded[ty].append(ledger.pop(ty))
            cleared.add(ty)
            turns.append(Turn("user_clear", f"The {ty} standard no longer applies; disregard it.", (ty, None)))
        elif kind == "distractor" and ty is not None:
            # conflict invariant (registered): emitted note value never equals
            # the currently-active value for its type
            fake = _pick([x for x in POOLS[ty] if x != ledger.get(ty)], g)
            quoted = superseded[ty][-1] if superseded[ty] and float(torch.rand((), generator=g)) < 0.6 else fake
            if interference == "s0":
                # T2b: bare format-identical note, no de-authorizing framing
                turns.append(Turn("distractor", f"Note: {SENT[ty].format(v=quoted)}"))
            else:
                turns.append(Turn("distractor", f"(An old thread note said: {SENT[ty].format(v=quoted)} That thread is not authoritative.)"))
        elif kind == "s0_note":
            # T2b scheduler guarantee: one genuinely-conflicting note for an
            # active type (two such steps precede each work turn)
            active = [k for k in TYPES if k in ledger]
            if active:
                ty3 = active[int(torch.randint(0, len(active), (1,), generator=g))]
                val = _pick([x for x in POOLS[ty3] if x != ledger[ty3]], g)
                turns.append(Turn("distractor", f"Note: {SENT[ty3].format(v=val)}"))
            else:
                turns.append(Turn("distractor", _pick(FILLER, g)))
        elif kind == "work":
            req, op = CODE_REQUESTS[int(torch.randint(0, len(CODE_REQUESTS), (1,), generator=g))]
            fn = f"task{fn_counter}"
            fn_counter += 1
            work_turns.append(ti)
            fn_names[ti] = fn
            ops[ti] = op
            ledger_at[ti] = dict(ledger)
            superseded_at[ti] = {k: list(v) for k, v in superseded.items()}
            turns.append(Turn("work", f"Task: {req} Answer with only the code.\n```python\n"))
            # surviving window at this work turn (same rule as prompt_at)
            K = STRATA[stratum]
            lo = 0
            for ct in COMPACTION_TURNS[stratum]:
                if ti >= ct:
                    lo = max(lo, ct - K)
            window = " ".join(tn.text for tn in turns[lo: ti + 1])
            for ty2 in TYPES:
                if ty2 in ledger:
                    cell = "active"
                else:
                    # full formatted-sentence match (fable T2b clearance:
                    # bare-value substrings collide with unrelated text)
                    visible_stale = any(
                        SENT[ty2].format(v=v) in window for v in superseded[ty2]
                    )
                    if visible_stale:
                        cell = "stale_only"
                    elif ty2 in cleared:
                        cell = "cleared"
                    else:
                        cell = "absent"
                targets = ["a", "b"] if ty2 == "hint" else [fn]
                for tgt in targets:
                    opportunities.append(Opportunity(
                        opportunity_id=f"{seed}-{ti}-{ty2}-{tgt}",
                        turn=ti, obligation_id=ty2,
                        target_object=(f"arg:{tgt}" if ty2 == "hint" else tgt),
                        moment_class=ty2, cell=cell,
                        expected=ledger.get(ty2),
                        superseded=list(superseded[ty2]),
                    ))
            if "comment" in ledger:
                opportunities.append(Opportunity(
                    opportunity_id=f"{seed}-{ti}-comment-{fn}", turn=ti,
                    obligation_id="comment", target_object=fn,
                    moment_class="comment", cell="active",
                    expected="# reviewed", scorer_id="source_text",
                ))
        elif kind == "env":
            turns.append(Turn("env", "[checker] (deterministic feedback on the previous submission is inserted here at run time)"))
        else:
            turns.append(Turn("distractor", _pick(FILLER, g)))

    return T2Session(
        seed=seed, stratum=stratum, turns=turns, work_turns=work_turns,
        fn_names=fn_names, ops=ops, ledger_at=ledger_at,
        superseded_at=superseded_at, opportunities=opportunities,
        compaction_turns=COMPACTION_TURNS[stratum], held_out=held_out,
    )


def prompt_at(sess: T2Session, work_turn: int, split: str = "dev") -> str:
    """The v3 context rule: live ledger ALWAYS survives; conversation turns
    truncate to the last K at each registered compaction turn."""
    K = STRATA[sess.stratum]
    # registered rule: at each compaction turn ct, conversation truncates to
    # the last K turns (turns >= ct - K survive); the live ledger survives
    # unconditionally and is re-serialized at the top of every prompt.
    lo = 0
    for ct in sess.compaction_turns:
        if work_turn >= ct:
            lo = max(lo, ct - K)
    convo = []
    for i in range(max(0, lo), work_turn + 1):
        convo.append(sess.turns[i].text)
    led = ledger_text(sess.ledger_at[work_turn], unseen_fmt=(split in ("val", "final")))
    return led + "\n\n" + "\n".join(convo)
