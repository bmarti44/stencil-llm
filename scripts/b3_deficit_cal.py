# ruff: noqa
"""v4.5 tau calibration (ONE SHOT, registered): base + frozen grid
tau {0.10,0.20,0.30,0.45} x b_max {3.0,6.0} on cal-v45 (200 rows).
Selection: highest adherence; ties -> LOWER intervention rate.
Per-item atomic records for every arm. Seed-0 Wq/Wk only."""
import json, random, sys, hashlib
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401
import torch
from tokenizers import Tokenizer
from stencil.bench import TMPL, generate_deficit
from stencil.qwen3 import Qwen3
from stencil.wave import WaveController

sys.path.insert(0, str(ROOT / "vendor"))
import langdetect
langdetect.DetectorFactory.seed = 0
from ifeval import instructions_registry

GRID = [(t, b) for t in (0.10, 0.20, 0.30, 0.45) for b in (3.0, 6.0)]

tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
m = Qwen3()
m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
m = m.to(torch.bfloat16).cuda().eval()
ctrl = WaveController(beta_max=1.0).cuda()
ctrl.load_state_dict(torch.load(ROOT / "results" / "qwen" / "b3-ce-s0.pt", map_location="cpu"))
ctrl = ctrl.eval()
rows = [json.loads(line) for line in open(ROOT / "data" / "b3" / "cal-v45.jsonl")]
assert len(rows) == 200


def prompt_spans_of(row):
    ptxt = TMPL.format(p=row["prompt"])
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


def adherent(row, text):
    random.seed(row["key"])
    for iid, kw in zip(row["instruction_id_list"], row["kwargs"]):
        inst = instructions_registry.INSTRUCTION_DICT[iid](iid)
        inst.build_description(**{k: v for k, v in kw.items() if v})
        if not (text.strip() and inst.check_following(text)):
            return False
    return True


outdir = ROOT / "results" / "qwen" / "b3-deficit-cal"
outdir.mkdir(parents=True, exist_ok=True)


def run_arm(name, tau, b_max):
    n_ok, n_interv, n_steps = 0, 0, 0
    for i, r in enumerate(rows):
        rec_p = outdir / f"{name}-{i:03d}.json"
        if rec_p.exists():
            rec = json.loads(rec_p.read_text())
            n_ok += rec["adherent"]; n_interv += rec["n_interventions"]; n_steps += rec["n_gen"]
            continue
        if tau is None:
            from stencil.bench import generate_cached
            text, n, tr, to = generate_cached(m, tok, r["prompt"], deadline_s=300)
            log = []
        else:
            text, n, tr, to, log = generate_deficit(
                m, tok, r["prompt"], ctrl, prompt_spans_of(r), tau, b_max, deadline_s=300)
        ok = adherent(r, text)
        n_ok += ok; n_steps += n
        n_int = len(log)  # steps with a selected span (intervention opportunity)
        n_interv += n_int
        rec = {"i": i, "adherent": bool(ok), "n_gen": n, "truncated": bool(tr),
               "timeout": bool(to), "n_interventions": n_int, "response": text}
        tmp = rec_p.with_suffix(".tmp"); tmp.write_text(json.dumps(rec, ensure_ascii=False)); tmp.rename(rec_p)
        if i % 50 == 0:
            print(f"[{name}] {i}/200 adh {n_ok/(i+1):.3f}", flush=True)
    return {"adherence": n_ok / 200, "interventions_per_token": (n_interv / max(1, n_steps))}


results = {"base": run_arm("base", None, None)}
print("[base]", results["base"], flush=True)
for tau, bm in GRID:
    name = f"t{int(tau*100):02d}-b{int(bm)}"
    results[name] = {"tau": tau, "b_max": bm, **run_arm(name, tau, bm)}
    print(f"[{name}]", results[name], flush=True)
grid = {k: v for k, v in results.items() if k != "base"}
best = max(grid, key=lambda k: (grid[k]["adherence"], -grid[k]["interventions_per_token"]))
out = {"results": results, "selected": best,
       "ctrl_sha256": hashlib.sha256((ROOT / "results" / "qwen" / "b3-ce-s0.pt").read_bytes()).hexdigest()}
(ROOT / "results" / "qwen" / "b3-deficit-cal.json").write_text(json.dumps(out, indent=1))
print(json.dumps({k: v for k, v in out.items() if k != "results"}, indent=1))
