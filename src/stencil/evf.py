# ruff: noqa: E501
"""EVF Phase E0 pilot library (EVF-PLAN.md; red/green TDD).

Pure-python probe machinery is dependency-free and deterministic by
construction (zero-init logistic GD, fixed iteration count). Feature
extraction is a teacher-forced pass through the frozen trunk plus one
weak-focus counterfactual forward — deterministic, proven bitwise by
tests/test_evf_pilot.py.
"""
import json
import math
import random
from pathlib import Path

TMPL = "<|im_start|>user\n{p}<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
WAVE_LAYERS = range(20, 28)


def first_divergence(tok, a, b):
    """index of the first differing TOKEN between texts a and b
    (None if their token id sequences are identical)."""
    ia, ib = tok.encode(a).ids, tok.encode(b).ids
    n = min(len(ia), len(ib))
    for k in range(n):
        if ia[k] != ib[k]:
            return k
    if len(ia) == len(ib):
        return None
    return n


def _load_records(root, arm):
    d = Path(root) / "results" / "qwen" / "b3-deficit-cal"
    base, wave = {}, {}
    for p in d.glob("base-*.json"):
        r = json.loads(p.read_text())
        base[r["i"]] = r
    for p in d.glob(f"{arm}-*.json"):
        r = json.loads(p.read_text())
        wave[r["i"]] = r
    rows = [json.loads(line) for line in open(Path(root) / "data" / "b3" / "cal-v45.jsonl")]
    return base, wave, rows


def load_anatomy(root, arm="t30-b3"):
    """discordant rows (repair label=1 / regression label=0), joined."""
    base, wave, rows = _load_records(root, arm)
    out = []
    for i in sorted(base):
        b, w = base[i], wave[i]
        if b["adherent"] == w["adherent"]:
            continue
        out.append({"row": rows[i], "i": i,
                    "base_response": b["response"], "wave_response": w["response"],
                    "base_adherent": b["adherent"], "wave_adherent": w["adherent"],
                    "label": int(w["adherent"])})
    return out


def load_controls(root, arm="t30-b3", n=30, seed=11):
    """seeded sample of concordant rows (matched control points)."""
    base, wave, rows = _load_records(root, arm)
    conc = [i for i in sorted(base) if base[i]["adherent"] == wave[i]["adherent"]]
    rng = random.Random(seed)
    pick = sorted(rng.sample(conc, n))
    return [{"row": rows[i], "i": i,
             "base_response": base[i]["response"], "wave_response": wave[i]["response"],
             "base_adherent": base[i]["adherent"], "wave_adherent": wave[i]["adherent"]}
            for i in pick]


def load_model(root):
    import torch
    from tokenizers import Tokenizer

    from stencil import determinism  # noqa: F401
    from stencil.qwen3 import Qwen3
    from stencil.wave import WaveController
    root = Path(root)
    tok = Tokenizer.from_file(str(root / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
    m = Qwen3()
    m.load_state_dict(torch.load(root / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
    m = m.to(torch.bfloat16).cuda().eval()
    ctrl = WaveController(beta_max=1.0).cuda()
    ctrl.load_state_dict(torch.load(root / "results" / "qwen" / "b3-ce-s0.pt", map_location="cpu"))
    return m, tok, ctrl.eval()


def constraint_spans_of(tok, prompt):
    ptxt = TMPL.format(p=prompt)
    enc = tok.encode(ptxt)
    spans, start = [], 0
    while True:
        i = ptxt.find("Constraint:", start)
        if i < 0:
            break
        j = ptxt.find("Constraint:", i + 1)
        end = j if j > 0 else ptxt.find("<|im_end|>", i)
        toks = [ti for ti, (a, b) in enumerate(enc.offsets) if a < end and b > i]
        if toks:
            spans.append((toks[0], toks[-1] + 1))
        start = i + 1
    return spans


def extract_features(m, tok, ctrl, item, probe_pos=None):
    """registered E0 feature set at the divergence point (or probe_pos)."""
    import torch
    import torch.nn.functional as F
    row = item["row"]
    k = first_divergence(tok, item["base_response"], item["wave_response"])
    shared = tok.encode(item["base_response"]).ids[: (k if k is not None else 0)]
    if probe_pos is not None:
        shared = shared[:probe_pos]
    p_ids = tok.encode(TMPL.format(p=row["prompt"])).ids
    P = len(p_ids)
    ids = p_ids + shared
    toks = torch.tensor([ids], device="cuda")
    spans = constraint_spans_of(tok, row["prompt"])
    with torch.no_grad():
        logits, h20 = m(toks, capture_hidden=20)
        lp = F.log_softmax(logits[0, -6:].float(), dim=-1)
        probs = lp.exp()
        ents = (-(probs * lp).sum(-1)).tolist()
        tops = probs.topk(2, dim=-1).values
        margins = (tops[:, 0] - tops[:, 1]).tolist()
        # rule readout via the frozen wave's q/k
        q = F.normalize(ctrl.W_q(h20[0, -1:].float()), dim=-1)
        kk = F.normalize(ctrl.W_k(h20[0, :P].float()), dim=-1)
        scores = (q @ kk.T)[0]
        span_scores = sorted((float(scores[a:b].mean()) for a, b in spans), reverse=True) or [0.0]
        best_span = max(spans, key=lambda ab: float(scores[ab[0]:ab[1]].mean())) if spans else (0, 1)
        # natural attention mass on the governing span (layers 20-27, last row)
        pm = torch.zeros(len(ids), dtype=torch.bool, device="cuda")
        pm[best_span[0]:best_span[1]] = True
        sink = {}
        m(toks, attn_probe=(pm, sink))
        attn_mass = sum(sink.values()) / len(sink)
        # weak-focus counterfactual: b=1.0 on the governing span, last row
        T = len(ids)
        bias = torch.zeros(T, T, device="cuda")
        bias[-1, best_span[0]:best_span[1]] = 1.0
        l1 = m(toks, attn_bias={L: bias for L in WAVE_LAYERS})[0, -1].float()
        p0 = F.log_softmax(logits[0, -1].float(), dim=-1)
        p1 = F.log_softmax(l1, dim=-1)
        kl = float((p1.exp() * (p1 - p0)).sum())
        mix = torch.logsumexp(torch.stack([p0, p1]), dim=0) - math.log(2)
        js = 0.5 * float((p0.exp() * (p0 - mix)).sum()) + 0.5 * float((p1.exp() * (p1 - mix)).sum())
        ob_ids = sorted({tid for kkey, sps in row["obligation_spans"].items()
                         for a, b in sps
                         for tid in tok.encode(row["canonical"][a:b]).ids})
        ob_shift = float((p1[ob_ids] - p0[ob_ids]).mean()) if ob_ids else 0.0
    return {
        "entropy": float(ents[-1]), "margin": float(margins[-1]),
        "entropy_delta5": float(ents[-1] - ents[0]), "margin_delta5": float(margins[-1] - margins[0]),
        "readout_top": span_scores[0],
        "readout_margin": span_scores[0] - (span_scores[1] if len(span_scores) > 1 else 0.0),
        "attn_mass_span": float(attn_mass),
        "kl_focus": kl, "js_focus": js, "obligation_shift": ob_shift,
        "rel_pos": len(shared) / max(1, len(shared) + 32),
    }


# --- deterministic probe ----------------------------------------------------

def _standardize(feats):
    keys = sorted(feats[0])
    mu = {k: sum(f[k] for f in feats) / len(feats) for k in keys}
    sd = {k: (sum((f[k] - mu[k]) ** 2 for f in feats) / len(feats)) ** 0.5 or 1.0 for k in keys}
    return keys, mu, sd


def fit_probe(feats, labels, seed=0, l2=1.0, iters=500, lr=0.1):
    """zero-init logistic GD — deterministic (seed kept for signature)."""
    keys, mu, sd = _standardize(feats)
    X = [[(f[k] - mu[k]) / sd[k] for k in keys] for f in feats]
    w = [0.0] * len(keys)
    b = 0.0
    n = len(X)
    for _ in range(iters):
        gw = [l2 * wi / n for wi in w]
        gb = 0.0
        for x, y in zip(X, labels):
            z = sum(wi * xi for wi, xi in zip(w, x)) + b
            p = 1.0 / (1.0 + math.exp(-max(-30, min(30, z))))
            e = p - y
            for j in range(len(w)):
                gw[j] += e * x[j] / n
            gb += e / n
        w = [wi - lr * gi for wi, gi in zip(w, gw)]
        b -= lr * gb
    return {"keys": keys, "mu": mu, "sd": sd, "w": w, "b": b}


def predict(model, f):
    z = sum(wi * (f[k] - model["mu"][k]) / model["sd"][k]
            for wi, k in zip(model["w"], model["keys"])) + model["b"]
    return 1.0 / (1.0 + math.exp(-max(-30, min(30, z))))


def gate_eval(feats, labels, groups, seed=0, threshold=0.5):
    """leave-one-group-out CV; returns held-out repair recall (r_plus)
    and regression fire-rate (r_minus)."""
    preds = {}
    for g in sorted(set(groups)):
        tr = [i for i in range(len(feats)) if groups[i] != g]
        te = [i for i in range(len(feats)) if groups[i] == g]
        if not tr or not te:
            continue
        model = fit_probe([feats[i] for i in tr], [labels[i] for i in tr], seed=seed)
        for i in te:
            preds[i] = predict(model, feats[i]) >= threshold
    pos = [i for i in preds if labels[i] == 1]
    neg = [i for i in preds if labels[i] == 0]
    r_plus = sum(preds[i] for i in pos) / len(pos) if pos else 0.0
    r_minus = sum(preds[i] for i in neg) / len(neg) if neg else 1.0
    return {"r_plus": r_plus, "r_minus": r_minus, "n_pos": len(pos), "n_neg": len(neg)}
