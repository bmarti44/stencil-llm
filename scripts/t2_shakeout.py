# ruff: noqa
"""T2 dev shakeout: all arms on dev sessions; headroom check + full metrics."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401
import re

import torch
from tokenizers import Tokenizer

from stencil.qwen3 import Qwen3
from stencil.t2_runner import run_session
from stencil.t2_sessions import generate_t2

sys.path.insert(0, str(ROOT / "scripts"))
from t2_train_selector import candidate_spans  # noqa: E402

N_DEV = 24
DEV = [12_600_000 + i for i in range(N_DEV)]
CLASSES = ["none", "prefix", "doc", "hint"]

tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
m = Qwen3()
m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
m = m.to(torch.bfloat16).cuda().eval()
sel = torch.load(ROOT / "results" / "qwen" / "t2-selector.pt", map_location="cpu")
head = torch.nn.Linear(2048, 4); head.load_state_dict(sel["head"]); head = head.cuda()
Wq = torch.nn.Linear(2048, 64); Wq.load_state_dict(sel["Wq"]); Wq = Wq.cuda()
Wk = torch.nn.Linear(2048, 64); Wk.load_state_dict(sel["Wk"]); Wk = Wk.cuda()
TAU, THETA = sel["tau"], sel["theta"]


def timing(model, toks, text):
    with torch.no_grad():
        h = model(toks, return_hidden=20)[0, -1].float()
        probs = torch.softmax(head(h), dim=-1)
        c = int(probs[1:].argmax()) + 1
        return CLASSES[c] if float(probs[c]) > TAU else None


def address(model, toks, ptxt, spans, key):
    enc = tok.encode(ptxt)
    cands = candidate_spans(ptxt, enc)
    if not cands:
        return None
    with torch.no_grad():
        h_prompt = model(torch.tensor([enc.ids], device="cuda"), return_hidden=20)[0].float()
        cf = torch.stack([h_prompt[c[2][0]:c[2][1]].mean(dim=0) for c in cands])
        s = model(toks, return_hidden=20)[0, -1].float()
        scores = (Wq(s) @ Wk(cf.cuda()).T) / 8.0
        j = int(scores.argmax())
        if float(scores[j]) <= THETA:
            return None
    ty = cands[j][0]
    return ty if ty in spans else None


ARMS = ["base", "reinsertion", "oracle", "selector"]
report = {}
with torch.no_grad():
    for arm in ARMS:
        adh_n = adh_d = stale_n = stale_d = parse_n = works = fpress = 0
        for seed in DEV:
            sess = generate_t2(seed, 20, "dev")
            rs = run_session(m, tok, sess, "dev", arm,
                             timing=timing if arm == "selector" else None,
                             address=address if arm == "selector" else None)
            for r in rs:
                works += 1
                parse_n += r.parse
                for o in sess.opportunities:
                    if o.turn != r.turn:
                        continue
                    e = r.per_opportunity.get(o.opportunity_id, {})
                    if o.cell == "active":
                        adh_d += 1
                        adh_n += bool(e.get("adherent"))
                    if o.superseded:
                        stale_d += 1
                        stale_n += bool(e.get("stale_action"))
        report[arm] = {"adherence": round(adh_n / max(1, adh_d), 3), "n_active": adh_d,
                       "stale_rate": round(stale_n / max(1, stale_d), 3), "n_stale_opp": stale_d,
                       "parse_rate": round(parse_n / max(1, works), 3), "works": works}
        print(arm, report[arm], flush=True)
headroom = report["oracle"]["adherence"] - report["base"]["adherence"]
print(f"HEADROOM (oracle-base): {headroom:+.3f} (binding precondition >= 0.10)")
(ROOT / "results" / "qwen" / "t2-shakeout.json").write_text(json.dumps(report, indent=1))
print("saved results/qwen/t2-shakeout.json")
