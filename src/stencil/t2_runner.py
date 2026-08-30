# ruff: noqa: E501
"""T2 arm runner + scorers (CONTRACT v3).

Registered policies implemented here:
- target function = FIRST FunctionDef in the turn's output (v2 policy);
- scorers: ast (parse gate, docstring opener, per-arg annotations, name
  prefix), source_text (the '# reviewed' comment rule — AST discards
  comments), exec (subprocess operation test);
- adherence is computed on ACTIVE cells; stale-action per the v3 numerator/
  denominator; absent/cleared cells feed false-press metrics only;
- environment feedback names the violated obligation TYPE only (never the
  value — no second memory channel beyond the surviving ledger);
- arms: base, reinsertion (== pinned under v3, recorded), oracle, and
  selector arms via injected timing/address callables;
- spotlight: attn_bias beta=2 layers 20-27, current prediction row, on the
  governing ledger-sentence token span.
"""
from __future__ import annotations

import ast
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass

import torch

from .qwen_task import CODE_REQUESTS
from .t2_sessions import SENT, SENT_UNSEEN_FMT, T2Session, ledger_text, prompt_at

OP_TESTS = {"sum": (3, 5, 8), "max": (3, 5, 5), "mul": (3, 5, 15), "sub": (9, 4, 5)}
LAYERS = tuple(range(20, 28))
BETA = 2.0


@dataclass
class WorkResult:
    turn: int
    code: str
    parse: bool
    exec_ok: bool
    per_opportunity: dict  # opportunity_id -> {"adherent": bool|None, "stale_action": bool|None, "value_used": str|None}


def _first_fn(code: str):
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None, None
    fns = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    return (tree, fns[0]) if fns else (tree, None)


def _ann(a):
    return getattr(a.annotation, "id", None) if a.annotation else None


def score_work(code: str, sess: T2Session, turn: int) -> WorkResult:
    tree, fn = _first_fn(code)
    parse = tree is not None
    res: dict = {}
    exec_ok = False
    if fn is not None:
        x, y, want = OP_TESTS[sess.ops[turn]]
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(code + f"\nimport sys\nsys.exit(0 if {fn.name}({x}, {y}) == {want} else 3)\n")
            path = f.name
        try:
            r = subprocess.run([sys.executable, path], timeout=5, capture_output=True)
            exec_ok = r.returncode == 0
        except Exception:
            pass
    for o in (op for op in sess.opportunities if op.turn == turn):
        entry = {"adherent": None, "stale_action": None, "value_used": None}
        if fn is None:
            if o.cell == "active":
                entry["adherent"] = False
            res[o.opportunity_id] = entry
            continue
        if o.moment_class == "prefix":
            m = re.match(r"([A-Za-z0-9]+)_", fn.name)
            entry["value_used"] = m.group(1) if m else None
        elif o.moment_class == "doc":
            doc = ast.get_docstring(fn)
            entry["value_used"] = doc.split()[0] if doc and doc.split() else None
        elif o.moment_class == "hint":
            idx = 0 if o.target_object == "arg:a" else 1
            args = fn.args.args
            entry["value_used"] = _ann(args[idx]) if len(args) > idx else None
        elif o.moment_class == "comment":
            seg = ast.get_source_segment(code, fn) or ""
            lines = [ln.strip() for ln in seg.split("\n") if ln.strip()]
            entry["value_used"] = "# reviewed" if lines and lines[-1] == "# reviewed" else None
        if o.cell == "active":
            entry["adherent"] = entry["value_used"] == o.expected
        if o.superseded:
            entry["stale_action"] = entry["value_used"] in o.superseded and entry["value_used"] != o.expected
        res[o.opportunity_id] = entry
    return WorkResult(turn=turn, code=code, parse=parse, exec_ok=exec_ok, per_opportunity=res)


def feedback_text(wr: WorkResult, sess: T2Session) -> str:
    if not wr.parse:
        return "[checker] previous submission: syntax error."
    bad = sorted({
        o.moment_class for o in sess.opportunities
        if o.turn == wr.turn and wr.per_opportunity.get(o.opportunity_id, {}).get("adherent") is False
    })
    if not bad:
        return "[checker] previous submission: all checks passed."
    return "[checker] previous submission violates the current standard(s): " + ", ".join(bad) + "."


def ledger_sentence_spans(prompt_text: str, sess: T2Session, turn: int, split: str, tok) -> dict:
    """Char->token spans of each ledger sentence in THIS prompt."""
    led = sess.ledger_at[turn]
    spans = {}
    enc = tok.encode(prompt_text)
    for ty, v in led.items():
        if ty == "comment":
            sent = " Every function body must end with the comment '# reviewed'."
        else:
            tmpl = SENT_UNSEEN_FMT.get(ty) if split in ("val", "final") and ty in SENT_UNSEEN_FMT else SENT[ty]
            sent = " " + tmpl.format(v=v)
        c = prompt_text.find(sent)
        if c < 0:
            continue
        cols = [i for i, (a, b) in enumerate(enc.offsets) if a < c + len(sent) and b > c]
        if cols:
            spans[ty] = (cols[0], cols[-1] + 1)
    return spans


def run_session(model, tok, sess: T2Session, split: str, arm: str,
                timing=None, address=None, max_new: int = 120,
                press_log: list | None = None) -> list[WorkResult]:
    """arm in {base, reinsertion, oracle, structured, selector};
    timing/address callables for selector arms. "structured" is the
    PRESS-PLAN deployment baseline and is IDENTICAL to "oracle" here by
    construction: _oracle_moment is a parser detector over generated
    text (no ground truth) and ledger_sentence_spans only contains
    ACTIVE ledger types — parser timing + active-ledger eligibility +
    authoritative span. press_log (H2): one entry per applied press,
    {"work_turn", "step", "type", "span"}."""
    results = []
    feedback: dict[int, str] = {}
    for wt in sess.work_turns:
        ptxt = prompt_at(sess, wt, split)
        for et, ftxt in feedback.items():
            if et < wt:
                ptxt = ptxt.replace("[checker] (deterministic feedback on the previous submission is inserted here at run time)", ftxt, 1)
        if arm == "reinsertion":
            led = ledger_text(sess.ledger_at[wt], unseen_fmt=(split in ("val", "final")))
            marker = sess.turns[wt].text
            ptxt = ptxt.replace(marker, "(Reminder) " + led + "\n" + marker, 1)
        ids = tok.encode(ptxt).ids
        spans = ledger_sentence_spans(ptxt, sess, wt, split, tok) if arm in ("oracle", "structured", "selector") else {}
        toks = torch.tensor([ids], device="cuda")
        outs = []
        text = ""
        for step in range(max_new):
            ab = None
            if arm in ("oracle", "structured") and spans:
                key = _oracle_moment(text[-80:])
                if key is not None and key in spans:
                    t = toks.shape[1]
                    bias = torch.zeros(t, t, device="cuda")
                    bias[-1:, spans[key][0]:spans[key][1]] = BETA
                    ab = {L: bias for L in LAYERS}
                    if press_log is not None:
                        press_log.append({"work_turn": wt, "step": step, "type": key, "span": spans[key]})
            elif arm == "selector" and spans and timing is not None:
                key = timing(model, toks, text)
                if key is not None:
                    key = address(model, toks, ptxt, spans, key) if address is not None else key
                    if key is not None and key in spans:
                        t = toks.shape[1]
                        bias = torch.zeros(t, t, device="cuda")
                        bias[-1:, spans[key][0]:spans[key][1]] = BETA
                        ab = {L: bias for L in LAYERS}
                        if press_log is not None:
                            press_log.append({"work_turn": wt, "step": step, "type": key, "span": spans[key]})
            nxt = int(model(toks, attn_bias=ab)[0, -1].argmax())
            outs.append(nxt)
            toks = torch.cat([toks, torch.tensor([[nxt]], device="cuda")], dim=1)
            text = tok.decode(outs)
            if "```" in text[-6:]:
                break
        code = text.split("```")[0]
        wr = score_work(code, sess, wt)
        results.append(wr)
        # feedback lands in the next env turn after wt
        for i in range(wt + 1, len(sess.turns)):
            if sess.turns[i].kind == "env":
                feedback[i] = feedback_text(wr, sess)
                break
    return results


def run_policy_session(model, tok, prompt_text, ledger_spans, policy,
                       threshold, press_log=None, max_new=120,
                       beta=BETA, layers=LAYERS):
    """PRESS-PLAN H1/H2 primitive: generate one work with an autonomous
    span-level policy. The policy callable returns
    (candidate_span | None, diagnostics) with diagnostics["score"]; the
    RUNNER applies the registered guards in order — numeric threshold,
    then ledger membership — applies the surviving span verbatim, and
    appends one press-log entry per step:
    {"step", "pre_guard", "rejected", "applied"} with rejected in
    {None, "below-threshold", "out-of-ledger"}. The certification
    failure event (plan: pre-structural-guard) is derivable as
    pre_guard is not None and rejected != "below-threshold"."""
    ids = tok.encode(prompt_text).ids
    try:
        device = next(model.parameters()).device
    except (AttributeError, StopIteration, TypeError):
        device = "cpu"
    toks = torch.tensor([ids], device=device)
    outs, text = [], ""
    for i in range(max_new):
        span, diag = policy(model, toks, prompt_text, text)
        entry = {"step": i, "pre_guard": span, "rejected": None, "applied": None}
        ab = None
        if span is not None:
            if float(diag["score"]) <= threshold:
                entry["rejected"] = "below-threshold"
            elif not any(s <= span[0] and span[1] <= e for s, e in ledger_spans.values()):
                entry["rejected"] = "out-of-ledger"
            else:
                entry["applied"] = span
                t = toks.shape[1]
                bias = torch.zeros(t, t, device=toks.device)
                bias[-1:, span[0]:span[1]] = beta
                ab = {L: bias for L in layers}
        if press_log is not None:
            press_log.append(entry)
        nxt = int(model(toks, attn_bias=ab)[0, -1].argmax())
        outs.append(nxt)
        toks = torch.cat([toks, torch.tensor([[nxt]], device=toks.device)], dim=1)
        text = tok.decode(outs)
        if "```" in text[-6:]:
            break
    return text.split("```")[0]


def _oracle_moment(tail_text):
    if re.search(r"\bdef\s*$", tail_text):
        return "prefix"
    if re.search(r'"""\s*$', tail_text) and tail_text.count('"""') % 2 == 1:
        return "doc"
    if re.search(r"def\s+\w+\s*\([^)]*:\s*$", tail_text):
        return "hint"
    return None


assert CODE_REQUESTS  # imported for op keys used by generator
