# ruff: noqa
"""Checkpoint-ii required artifacts (sol rulings, no retraining):
1. Per-cell G-W0c CE breakdown from the frozen w0-ce checkpoint: held
   canonical CE (zero vs wave) restricted to MOMENT rows, grouped by the
   moment type's counterfactual cell at that work.
2. Full 24-session proxy/oracle identity: per-work sha256 of generated
   code for both arms; equality counts.
"""
import hashlib
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
from stencil.t2_runner import LAYERS, _oracle_moment, ledger_sentence_spans, prompt_at
from stencil.t2_sessions import generate_t2
from stencil.wave import WaveController
from stencil.wave_ref import canonical_code
import w0_replay  # reuse run_arm/load_ctrl (import safe: work under main())

NEUTRAL = "[checker] (no feedback available this session)"
HELD = [13_400_040 + i for i in range(8)]
DEV = [13_450_000 + i for i in range(24)]
tok = w0_replay.tok
m = w0_replay.m


def per_cell():
    wave = w0_replay.load_ctrl("w0-ce.pt")
    cells = {}
    for seed in HELD:
        sess = generate_t2(seed, 20, "dev", interference="s0")
        for wt in sess.work_turns:
            ptxt = prompt_at(sess, wt, "dev").replace(
                "[checker] (deterministic feedback on the previous submission is inserted here at run time)", NEUTRAL)
            enc = tok.encode(ptxt)
            P = len(enc.ids)
            code_ids = tok.encode(canonical_code(sess, wt)).ids
            full = torch.tensor([enc.ids + code_ids], device="cuda")
            T = full.shape[1]
            cell_of = {o.moment_class: o.cell for o in sess.opportunities if o.turn == wt}
            rows, text = [], ""
            for i, tid in enumerate(code_ids):
                key = _oracle_moment(text[-80:])
                if key is not None and key in cell_of:
                    rows.append((P - 1 + i, cell_of[key]))
                text += tok.decode([tid])
            if not rows:
                continue
            with torch.no_grad():
                h = m(full, return_hidden=20)[0].float()
                field = wave.field(h[P - 1:T - 1], h[:P])
                bias = torch.zeros(T, T, device="cuda")
                bias[P - 1:T - 1, :P] = field
                lz = m(full)[0].float()
                lw = m(full, attn_bias={L: bias for L in LAYERS})[0].float()
            tg = full[0]
            for r, cell in rows:
                d = cells.setdefault(cell, {"zero": [], "wave": []})
                d["zero"].append(float(F.cross_entropy(lz[r][None], tg[r + 1][None])))
                d["wave"].append(float(F.cross_entropy(lw[r][None], tg[r + 1][None])))
    out = {}
    for cell, d in cells.items():
        z, w = sum(d["zero"]) / len(d["zero"]), sum(d["wave"]) / len(d["wave"])
        out[cell] = {"n_rows": len(d["zero"]), "zero_ce": round(z, 4), "wave_ce": round(w, 4),
                     "improve": round((z - w) / z, 4)}
    return out


def identity():
    proxy = w0_replay.load_ctrl("w0-proxy.pt")
    eq = 0
    tot = 0
    pairs = []
    for seed in DEV:
        sess = generate_t2(seed, 20, "dev", interference="s0")
        rp, _ = w0_replay.run_arm(sess, "proxy", proxy)
        ro, _ = w0_replay.run_arm(sess, "oracle", None)
        for a, b in zip(rp, ro):
            ha = hashlib.sha256(a.code.encode()).hexdigest()[:16]
            hb = hashlib.sha256(b.code.encode()).hexdigest()[:16]
            tot += 1
            eq += ha == hb
            pairs.append({"seed": seed, "wt": a.turn, "proxy": ha, "oracle": hb, "eq": ha == hb})
    return {"identical_works": eq, "total_works": tot, "pairs": pairs}


def main():
    out = {"per_cell_G_W0c": per_cell()}
    print(json.dumps(out["per_cell_G_W0c"], indent=1), flush=True)
    ident = identity()
    out["proxy_oracle_identity"] = ident
    print(f"identity: {ident['identical_works']}/{ident['total_works']} works token-identical", flush=True)
    (ROOT / "results" / "qwen" / "w0-addenda.json").write_text(json.dumps(out, indent=1))
    print("saved results/qwen/w0-addenda.json", flush=True)


if __name__ == "__main__":
    main()
