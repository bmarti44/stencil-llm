# ruff: noqa
"""B3 dev-200 GENERATION adherence gate (v4.1, registered before this
run): five arms generate on the dev-200 synthetic prompts (B4 decoding:
pinned template, cached greedy, max_new 1024, 300s deadline); metric =
strict-prompt adherence (ALL of a row's constraints pass the VENDORED
checkers, per-row random.seed(key)); GATE: each wave seed must exceed
base by >= +2.0 points; proxies reported, not gated. Atomic records."""
import json, hashlib, random, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401
import torch
from tokenizers import Tokenizer
from stencil.bench import generate_cached, make_wave_bias_fn
from stencil.qwen3 import Qwen3
from stencil.wave import WaveController

sys.path.insert(0, str(ROOT / "vendor"))
import langdetect
langdetect.DetectorFactory.seed = 0
from ifeval import instructions_registry

ARMS = [("base", None), ("wave-s0", "results/qwen/b3-ce-s0.pt"),
        ("proxy-s0", "results/qwen/b3-proxy-s0.pt"),
        ("wave-s1", "results/qwen/b3-ce-s1.pt"),
        ("proxy-s1", "results/qwen/b3-proxy-s1.pt")]

tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
m = Qwen3()
m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
m = m.to(torch.bfloat16).cuda().eval()
rows = [json.loads(line) for line in open(ROOT / "data" / "b3" / "dev-200.jsonl")]
assert len(rows) == 200

def adherent(row, text):
    random.seed(row["key"])
    for iid, kw in zip(row["instruction_id_list"], row["kwargs"]):
        inst = instructions_registry.INSTRUCTION_DICT[iid](iid)
        inst.build_description(**{k: v for k, v in kw.items() if v})
        if not (text.strip() and inst.check_following(text)):
            return False
    return True

outdir = ROOT / "results" / "qwen" / "b3-dev-gate"
outdir.mkdir(parents=True, exist_ok=True)
acc = {}
for name, path in ARMS:
    ctrl = None
    if path is not None:
        ctrl = WaveController().cuda()
        ctrl.load_state_dict(torch.load(ROOT / path, map_location="cpu"))
        ctrl = ctrl.eval()
    n_ok = 0
    for i, r in enumerate(rows):
        rec_p = outdir / f"{name}-{i:03d}.json"
        if rec_p.exists():
            n_ok += json.loads(rec_p.read_text())["adherent"]
            continue
        bias_fn = make_wave_bias_fn(ctrl, {}) if ctrl is not None else None
        text, n, trunc, timeout = generate_cached(m, tok, r["prompt"], bias_fn=bias_fn, deadline_s=300)
        ok = adherent(r, text)
        n_ok += ok
        tmp = rec_p.with_suffix(".tmp")
        tmp.write_text(json.dumps({"i": i, "adherent": bool(ok), "n_gen": n,
                                   "truncated": bool(trunc), "timeout": bool(timeout),
                                   "response": text}, ensure_ascii=False))
        tmp.rename(rec_p)
        if i % 50 == 0:
            print(f"[{name}] {i}/200 adh {n_ok/(i+1):.3f}", flush=True)
    acc[name] = n_ok / 200
    print(f"[{name}] adherence {acc[name]:.4f}", flush=True)

gate = {"adherence": {k: round(v, 4) for k, v in acc.items()},
        "gate_wave_s0": bool(acc["wave-s0"] - acc["base"] >= 0.02),
        "gate_wave_s1": bool(acc["wave-s1"] - acc["base"] >= 0.02)}
gate["PASS"] = gate["gate_wave_s0"] and gate["gate_wave_s1"]
print(json.dumps(gate, indent=1))
(ROOT / "results" / "qwen" / "b3-dev-gate.json").write_text(json.dumps(gate, indent=1))
