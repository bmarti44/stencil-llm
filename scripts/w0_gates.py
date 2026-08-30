# ruff: noqa
"""G-W0b/c gates + binding ablation battery (INTERNAL-WAVE-PLAN v3/v3.1).

CKPT env selects the trained controller (w0-ce.pt default; w0-proxy.pt
for the matched control's descriptive gates). Computes:
- G-W0b: canonical-token CE on seed 13,400,000 (all its works), trained
  vs INIT controller: trained moment... (registered: full canonical CE)
  must fall >= 50% vs the init controller's biased forward? Registered
  text: "canonical-token CE on seed 13,400,000 falls >= 50%" — baseline
  = zero-field (base) CE, trained-wave CE must be <= 50% of it.
- G-W0c: held (13,400,040..47) canonical CE improvement >= 10% vs zero
  field, plus the BINDING ablations (each must reproduce < 90% of the
  CE gain): K-permutation (WHERE), gain-sequence permutation (WHEN),
  uniform field at matched gain (selectivity).
Also emits the gain histogram artifact.
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401
import torch
import torch.nn.functional as F
from tokenizers import Tokenizer

from stencil.qwen3 import Qwen3
from stencil.t2_runner import LAYERS, prompt_at
from stencil.t2_sessions import generate_t2
from stencil.wave import WaveController
from stencil.wave_ref import canonical_code

NEUTRAL = "[checker] (no feedback available this session)"
CKPT = os.environ.get("CKPT", "w0-ce.pt")
HELD = [13_400_040 + i for i in range(8)]

tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
m = Qwen3()
m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
m = m.to(torch.bfloat16).cuda().eval()


def work_tensors(sess, wt):
    ptxt = prompt_at(sess, wt, "dev").replace(
        "[checker] (deterministic feedback on the previous submission is inserted here at run time)", NEUTRAL)
    enc = tok.encode(ptxt)
    P = len(enc.ids)
    code_ids = tok.encode(canonical_code(sess, wt)).ids
    return torch.tensor([enc.ids + code_ids], device="cuda"), P


def ce_with_field(full, P, field):
    T = full.shape[1]
    with torch.no_grad():
        if field is None:
            logits = m(full)[0].float()
        else:
            bias = torch.zeros(T, T, device="cuda")
            bias[P - 1:T - 1, :P] = field
            logits = m(full, attn_bias={L: bias for L in LAYERS})[0].float()
        return float(F.cross_entropy(logits[P - 1:T - 1], full[0, P:]))


def eval_seeds(wave, seeds, g_perm=None):
    """returns dict of mean CEs: zero, wave, kperm, gainperm, uniform;
    collects gain histogram."""
    out = {k: [] for k in ("zero", "wave", "kperm", "gainperm", "uniform")}
    gains = []
    rng = torch.Generator().manual_seed(0)
    for seed in seeds:
        sess = generate_t2(seed, 20, "dev", interference="s0")
        for wt in sess.work_turns:
            full, P = work_tensors(sess, wt)
            T = full.shape[1]
            with torch.no_grad():
                h = m(full, return_hidden=20)[0].float()
                K = h[:P]
                H = h[P - 1:T - 1]
                field = wave.field(H, K)
                g = wave.gain(H)
                gains += g.tolist()
                # ablations
                perm = torch.randperm(P, generator=rng).cuda()
                f_kperm = field[:, perm]
                rowperm = torch.randperm(field.shape[0], generator=rng).cuda()
                sm = field / g[:, None].clamp(min=1e-9)
                f_gainperm = g[rowperm][:, None] * sm
                f_uniform = g[:, None] * torch.ones_like(field)
            out["zero"].append(ce_with_field(full, P, None))
            out["wave"].append(ce_with_field(full, P, field))
            out["kperm"].append(ce_with_field(full, P, f_kperm))
            out["gainperm"].append(ce_with_field(full, P, f_gainperm))
            out["uniform"].append(ce_with_field(full, P, f_uniform))
    means = {k: sum(v) / len(v) for k, v in out.items()}
    hist = torch.histc(torch.tensor(gains), bins=10, min=0.0, max=2.0).tolist()
    return means, hist


def main():
    wave = WaveController().cuda()
    wave.load_state_dict(torch.load(ROOT / "results" / "qwen" / CKPT, map_location="cpu"))
    wave.eval()
    rep = {"ckpt": CKPT}
    # G-W0b overfit-1
    sess0 = generate_t2(13_400_000, 20, "dev", interference="s0")
    b_zero, b_wave = [], []
    for wt in sess0.work_turns:
        full, P = work_tensors(sess0, wt)
        T = full.shape[1]
        with torch.no_grad():
            h = m(full, return_hidden=20)[0].float()
            field = wave.field(h[P - 1:T - 1], h[:P])
        b_zero.append(ce_with_field(full, P, None))
        b_wave.append(ce_with_field(full, P, field))
    rep["overfit1"] = {"zero": round(sum(b_zero) / len(b_zero), 4),
                       "wave": round(sum(b_wave) / len(b_wave), 4)}
    rep["G_W0b"] = rep["overfit1"]["wave"] <= 0.5 * rep["overfit1"]["zero"]
    # G-W0c held + ablations
    means, hist = eval_seeds(wave, HELD)
    gain_ce = means["zero"] - means["wave"]
    rep["held"] = {k: round(v, 4) for k, v in means.items()}
    rep["held_improve"] = round(gain_ce / means["zero"], 4)
    rep["G_W0c_ce"] = rep["held_improve"] >= 0.10
    abl = {}
    for k in ("kperm", "gainperm", "uniform"):
        frac = (means["zero"] - means[k]) / gain_ce if gain_ce > 0 else float("inf")
        abl[k] = round(frac, 4)
    rep["ablation_gain_fraction"] = abl
    rep["binding"] = {k: abl[k] < 0.90 for k in abl}
    rep["uniform_closes_W0"] = abl["uniform"] >= 0.90
    rep["gain_histogram_0_2"] = hist
    rep["ALL"] = bool(rep["G_W0b"] and rep["G_W0c_ce"] and not rep["uniform_closes_W0"])
    print(json.dumps(rep, indent=1), flush=True)
    (ROOT / "results" / "qwen" / f"w0-gates-{CKPT.replace('.pt','')}.json").write_text(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
