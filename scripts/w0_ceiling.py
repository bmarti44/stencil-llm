# ruff: noqa
"""W0.05 field-parameterization ceiling (INTERNAL-WAVE-PLAN v3, frozen).

Hand-built oracle fields at oracle moments/spans, exact registered field
equations, feedback_mode=none, seeds 13,400,000..11. Per cell
(param in {A, B}) x (beta in {2, 4}):
  (i)  correct-position moment CE improvement >= 20% vs zero field
       (teacher-forced canonical targets; moment rows = generation rows
       whose next token begins a governed value, from w0-refs alignment);
  (ii) wrong-position degradation >= 5% relative (field on a shuffled
       ledger span);
  (iii) T0.3 validity rule on a 12-session generation replay (oracle
       parser timing, hand field vs base).
Hand-field logits: e = +6.0 on the governing span positions, -6.0
elsewhere; g = beta. A: b = g*softmax(e)/max(softmax(e));
B: b = g*sigmoid(e). Selection: smallest passing, order A2, B2, A4, B4.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401
import torch
import torch.nn.functional as F
from tokenizers import Tokenizer

from stencil.qwen3 import Qwen3
from stencil.t2_runner import LAYERS, _oracle_moment, ledger_sentence_spans, prompt_at, score_work
from stencil.t2_sessions import generate_t2
from stencil.wave_ref import canonical_code

NEUTRAL = "[checker] (no feedback available this session)"
SEEDS = [13_400_000 + i for i in range(12)]
CELLS = [("A", 2.0), ("B", 2.0), ("A", 4.0), ("B", 4.0)]

tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
m = Qwen3()
m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
m = m.to(torch.bfloat16).cuda().eval()


def neutral_prompt(sess, wt):
    return prompt_at(sess, wt, "dev").replace(
        "[checker] (deterministic feedback on the previous submission is inserted here at run time)", NEUTRAL)


def hand_row(P, span, param, beta):
    e = torch.full((P,), -6.0)
    if span is not None:
        e[span[0]:span[1]] = 6.0
    if param == "A":
        sm = torch.softmax(e, dim=-1)
        return beta * sm / sm.max()
    return beta * torch.sigmoid(e)


def moment_rows(sess, wt, ptxt, code_ids, P):
    """generation rows whose NEXT token begins a governed value: derive
    from the canonical code token stream via character positions of the
    name/doc/hint slots (deterministic; simple approach: rows where the
    decoded prefix ends with 'def ' -> prefix moment, opens docstring ->
    doc, annotation colon -> hint)."""
    rows = []
    text = ""
    led = sess.ledger_at[wt]
    for i, tid in enumerate(code_ids):
        key = _oracle_moment(text[-80:])
        if key is not None and key in led:
            rows.append((P - 1 + i, key))
        text += tok.decode([tid])
    return rows


def ce_at_rows(logits, targets, rows):
    sel = torch.tensor([r for r, _ in rows])
    return F.cross_entropy(logits[sel], targets[sel]).item() if len(rows) else float("nan")


def teacher_ce(sess, wt, param, beta, wrong=False):
    ptxt = neutral_prompt(sess, wt)
    enc = tok.encode(ptxt)
    P = len(enc.ids)
    code_ids = tok.encode(canonical_code(sess, wt)).ids
    full = enc.ids + code_ids
    T = len(full)
    spans = ledger_sentence_spans(ptxt, sess, wt, "dev", tok)
    rows = moment_rows(sess, wt, ptxt, code_ids, P)
    if not rows:
        return None
    bias = torch.zeros(T, T)
    for r, key in rows:
        span = spans.get(key)
        if span and wrong:
            width = span[1] - span[0]
            # wrong position = inside the CURRENT task-request sentence
            # (never obligation text; v2 fix — (5,5+width) hit the ledger
            # header and pressed the rules block, invalidating the control)
            c = ptxt.rfind("Task: ")
            cols = [i for i, (a, bnd) in enumerate(enc.offsets) if a >= c and bnd <= c + 40]
            span = (cols[0], cols[0] + width) if cols else (P // 2, P // 2 + width)
        bias[r] = torch.cat([hand_row(P, span, param, beta), torch.zeros(T - P)])
    targets = torch.tensor(full[1:] + [0])
    with torch.no_grad():
        base_logits = m(torch.tensor([full], device="cuda"))[0].float().cpu()
        ab = {L: bias.cuda() for L in LAYERS}
        press_logits = m(torch.tensor([full], device="cuda"), attn_bias=ab)[0].float().cpu()
    return ce_at_rows(base_logits, targets, rows), ce_at_rows(press_logits, targets, rows)


def replay_validity(param, beta):
    """12-session generation replay: oracle parser timing + hand field
    vs base; returns (dU_total, adherence_gain, broken)."""
    tot_du = adh_press = adh_base = 0
    broken = 0
    for seed in SEEDS:
        sess = generate_t2(seed, 20, "dev", interference="s0")
        for wt in sess.work_turns:
            ptxt = neutral_prompt(sess, wt)
            enc = tok.encode(ptxt)
            P = len(enc.ids)
            spans = ledger_sentence_spans(ptxt, sess, wt, "dev", tok)
            outs = {}
            for arm in ("base", "press"):
                toks = torch.tensor([enc.ids], device="cuda")
                gen, text = [], ""
                with torch.no_grad():
                    for _ in range(120):
                        ab = None
                        if arm == "press" and spans:
                            key = _oracle_moment(text[-80:])
                            if key is not None and key in spans:
                                t = toks.shape[1]
                                row = torch.cat([hand_row(P, spans[key], param, beta), torch.zeros(t - P)])
                                bias = torch.zeros(t, t)
                                bias[-1] = row
                                ab = {L: bias.cuda() for L in LAYERS}
                        nxt = int(m(toks, attn_bias=ab)[0, -1].argmax())
                        gen.append(nxt)
                        toks = torch.cat([toks, torch.tensor([[nxt]], device="cuda")], dim=1)
                        text = tok.decode(gen)
                        if "```" in text[-6:]:
                            break
                outs[arm] = score_work(text.split("```")[0], sess, wt)
            b, p = outs["base"], outs["press"]
            broke = (b.parse and not p.parse) or (b.exec_ok and not p.exec_ok)
            broken += broke
            for o in sess.opportunities:
                if o.turn == wt and o.cell == "active":
                    adh_base += bool(b.per_opportunity.get(o.opportunity_id, {}).get("adherent"))
                    adh_press += bool(p.per_opportunity.get(o.opportunity_id, {}).get("adherent"))
            tot_du += (sum(1 for o in sess.opportunities if o.turn == wt and o.cell == "active"
                           and p.per_opportunity.get(o.opportunity_id, {}).get("adherent")) - 2 * broke) - \
                      sum(1 for o in sess.opportunities if o.turn == wt and o.cell == "active"
                          and b.per_opportunity.get(o.opportunity_id, {}).get("adherent"))
    gain = adh_press - adh_base
    valid = tot_du > 0 and tot_du >= 0.8 * gain
    return {"dU_total": tot_du, "adh_gain": gain, "broken": broken, "valid": bool(valid)}


def main():
    report = {}
    chosen = None
    for param, beta in CELLS:
        base_ces, press_ces, wrong_ces = [], [], []
        for seed in SEEDS:
            sess = generate_t2(seed, 20, "dev", interference="s0")
            for wt in sess.work_turns:
                r = teacher_ce(sess, wt, param, beta)
                if r:
                    base_ces.append(r[0]); press_ces.append(r[1])
                rw = teacher_ce(sess, wt, param, beta, wrong=True)
                if rw:
                    wrong_ces.append(rw[1])
        b = sum(base_ces) / len(base_ces)
        p = sum(press_ces) / len(press_ces)
        w = sum(wrong_ces) / len(wrong_ces)
        improve = (b - p) / b
        degrade = (w - b) / b
        cell = {"base_ce": round(b, 4), "press_ce": round(p, 4), "wrong_ce": round(w, 4),
                "improve": round(improve, 4), "wrong_degrade": round(degrade, 4)}
        gates_i = improve >= 0.20
        gates_ii = degrade >= 0.05
        if gates_i and gates_ii:
            cell["replay"] = replay_validity(param, beta)
            cell["pass"] = cell["replay"]["valid"]
        else:
            cell["pass"] = False
        report[f"{param}{int(beta)}"] = cell
        print(f"{param}{int(beta)}:", json.dumps(cell), flush=True)
        if cell["pass"] and chosen is None:
            chosen = f"{param}{int(beta)}"
            break  # smallest-passing in registered order; later cells not run
    report["chosen"] = chosen
    (ROOT / "results" / "qwen" / "w0-ceiling.json").write_text(json.dumps(report, indent=1))
    print("CHOSEN:", chosen if chosen else "NONE — program closes at W0.05", flush=True)


if __name__ == "__main__":
    main()
