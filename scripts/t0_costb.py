# ruff: noqa
"""T0.3b (t2t3 prereg v3, section C — frozen): wrong-type authoritative
press audit that GATES the T3 grid.

For each (P, g) cell: scheduled presses are defined on the UNPRESSED
base trajectory (step mod P == 0, zero-based within each work turn;
entry = live TYPES-order round-robin by per-turn press count). Pairs are
selected in (seed, work_turn, step) order until >= 200 per cell; each
paired branch applies EXACTLY ONE press (bias beta*g on the scheduled
entry's authoritative span at that step). expected_DeltaU_cell = plain
mean of paired Delta-U; per-press classification (matching-type moment /
wrong-type-at-moment / no-moment) is diagnostic only. U and BROKEN as
T0.3. GRID RULE: grid runs iff any cell's expected Delta-U > 0.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401
import torch
from tokenizers import Tokenizer

from stencil.qwen3 import Qwen3
from stencil.t2_runner import BETA, LAYERS, _oracle_moment, feedback_text, ledger_sentence_spans, prompt_at, score_work
from stencil.t2_sessions import TYPES, generate_t2

SEEDS = [13_000_000 + i for i in range(48)]
CELLS = [(4, 0.5), (4, 1.0), (8, 0.5), (8, 1.0)]
N_PAIRS = 200

tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
m = Qwen3()
m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
m = m.to(torch.bfloat16).cuda().eval()


def gen(ptxt, press=None, max_new=120):
    """press = (step, span, gain)."""
    ids = tok.encode(ptxt).ids
    toks = torch.tensor([ids], device="cuda")
    outs, text = [], ""
    with torch.no_grad():
        for step in range(max_new):
            ab = None
            if press is not None and step == press[0]:
                t = toks.shape[1]
                bias = torch.zeros(t, t, device="cuda")
                bias[-1:, press[1][0]:press[1][1]] = BETA * press[2]
                ab = {L: bias for L in LAYERS}
            nxt = int(m(toks, attn_bias=ab)[0, -1].argmax())
            outs.append(nxt)
            toks = torch.cat([toks, torch.tensor([[nxt]], device="cuda")], dim=1)
            text = tok.decode(outs)
            if "```" in text[-6:]:
                break
    return text.split("```")[0], len(outs)


def U(wr, sess, wt, broken):
    adherent = sum(1 for o in sess.opportunities
                   if o.turn == wt and o.cell == "active"
                   and wr.per_opportunity.get(o.opportunity_id, {}).get("adherent"))
    return adherent - 2 * int(broken)


def main():
    # phase 1: base trajectories (shared across cells) with feedback threading
    base = {}  # (seed, wt) -> dict(ptxt, code, n_steps, wr, u, texts per step)
    for seed in SEEDS:
        sess = generate_t2(seed, 20, "dev", interference="s0")
        feedback = {}
        for wt in sess.work_turns:
            ptxt = prompt_at(sess, wt, "dev")
            for et, ftxt in feedback.items():
                if et < wt:
                    ptxt = ptxt.replace("[checker] (deterministic feedback on the previous submission is inserted here at run time)", ftxt, 1)
            code, n_steps = gen(ptxt)
            wr = score_work(code, sess, wt)
            base[(seed, wt)] = {"sess": sess, "ptxt": ptxt, "code": code,
                                "n": n_steps, "wr": wr, "u": U(wr, sess, wt, False)}
            for i in range(wt + 1, len(sess.turns)):
                if sess.turns[i].kind == "env":
                    feedback[i] = feedback_text(wr, sess)
                    break
    print(f"base trajectories: {len(base)} works", flush=True)

    out = {}
    for P, g in CELLS:
        pairs = []
        # enumerate scheduled presses in (seed, wt, step) order
        for (seed, wt) in sorted(base):
            b = base[(seed, wt)]
            sess = b["sess"]
            live = [ty for ty in TYPES if ty in sess.ledger_at[wt]]
            if not live:
                continue
            spans = ledger_sentence_spans(b["ptxt"], sess, wt, "dev", tok)
            k = 0
            for step in range(0, b["n"], P):
                ty = live[k % len(live)]
                k += 1
                if ty not in spans:
                    continue
                pairs.append((seed, wt, step, ty, spans[ty]))
        pairs = pairs[:N_PAIRS]
        rows = []
        for seed, wt, step, ty, span in pairs:
            b = base[(seed, wt)]
            code, _ = gen(b["ptxt"], press=(step, span, g))
            wr = score_work(code, b["sess"], wt)
            broken = (b["wr"].parse and not wr.parse) or (b["wr"].exec_ok and not wr.exec_ok)
            du = U(wr, b["sess"], wt, broken) - b["u"]
            # classification (diagnostic): does a parser moment of ty occur near step?
            # recompute base text prefix moment
            base_prefix = b["code"]
            moment = _oracle_moment(base_prefix[:max(0, step)][-80:]) if step <= len(base_prefix) else None
            cls = ("matching" if moment == ty else ("wrongtype-at-moment" if moment else "no-moment"))
            rows.append({"seed": seed, "wt": wt, "step": step, "type": ty, "dU": du,
                         "broken": bool(broken), "changed": code != b["code"], "class": cls})
        n = len(rows)
        exp = sum(r["dU"] for r in rows) / max(1, n)
        cell = {"n": n, "expected_dU": round(exp, 4),
                "broken_rate": round(sum(r["broken"] for r in rows) / max(1, n), 4),
                "changed_rate": round(sum(r["changed"] for r in rows) / max(1, n), 4),
                "class_counts": {c: sum(1 for r in rows if r["class"] == c) for c in ("matching", "wrongtype-at-moment", "no-moment")}}
        out[f"P{P}_g{g}"] = cell
        print(f"P={P} g={g}:", json.dumps(cell), flush=True)
    out["grid_runs"] = any(c["expected_dU"] > 0 for k, c in out.items() if isinstance(c, dict))
    (ROOT / "results" / "qwen" / "t0-costb.json").write_text(json.dumps(out, indent=1))
    print("GRID RULE:", "RUNS" if out["grid_runs"] else "SKIPPED — rhythm line closes", flush=True)
    print("saved results/qwen/t0-costb.json", flush=True)


if __name__ == "__main__":
    main()
