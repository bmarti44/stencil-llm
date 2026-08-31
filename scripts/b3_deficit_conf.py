# ruff: noqa
"""v4.5 CONFIRMATION (ONE SHOT, registered): base + deficit-wave at the
CALIBRATION-SELECTED (tau, b_max) on conf-v45 (1024 rows, prompt- and
topic-disjoint from calibration source distributionally identical dev
topics). GATE: wave >= base + 2.0pts strict adherence AND one-sided
exact McNemar p < 0.05 AND no excess timeouts/truncations. SEED env
picks the controller (0 = gate attempt, 1 = replication). Atomic
per-item records; .started seal per seed (one attempt)."""
import json, random, sys, hashlib, os, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401
import torch
from tokenizers import Tokenizer
from stencil.bench import TMPL, generate_cached, generate_deficit
from stencil.qwen3 import Qwen3
from stencil.stats import mcnemar_exact_one_sided
from stencil.wave import WaveController

sys.path.insert(0, str(ROOT / "vendor"))
import langdetect
langdetect.DetectorFactory.seed = 0
from ifeval import instructions_registry

SEED = int(os.environ.get("SEED", "0"))
CKPT = ROOT / "results" / "qwen" / ("b3-ce-s0.pt" if SEED == 0 else "b3-ce-s1.pt")

cal = json.loads((ROOT / "results" / "qwen" / "b3-deficit-cal.json").read_text())
sel = cal["results"][cal["selected"]]
TAU, BMAX = sel["tau"], sel["b_max"]

tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
m = Qwen3()
m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
m = m.to(torch.bfloat16).cuda().eval()
ctrl = WaveController(beta_max=1.0).cuda()
ctrl.load_state_dict(torch.load(CKPT, map_location="cpu"))
ctrl = ctrl.eval()
rows = [json.loads(line) for line in open(ROOT / "data" / "b3" / "conf-v45.jsonl")]
assert len(rows) == 1024


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


outdir = ROOT / "results" / "qwen" / f"b3-deficit-conf-s{SEED}"
outdir.mkdir(parents=True, exist_ok=True)
started = outdir / ".started"
meta = {"seed": SEED, "tau": TAU, "b_max": BMAX,
        "ctrl_sha256": hashlib.sha256(CKPT.read_bytes()).hexdigest(),
        "data_sha256": hashlib.sha256((ROOT / "data" / "b3" / "conf-v45.jsonl").read_bytes()).hexdigest(),
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
meta_p = outdir / "meta.json"
if started.exists():
    assert meta_p.exists() and json.loads(meta_p.read_text()) == meta, "resume provenance mismatch"
else:
    started.write_text(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    tmp = meta_p.with_suffix(".tmp"); tmp.write_text(json.dumps(meta, indent=1)); tmp.rename(meta_p)

res = {}
for arm in ("base", "wave"):
    n_ok, stats = 0, {"timeout": 0, "truncated": 0}
    for i, r in enumerate(rows):
        rec_p = outdir / f"{arm}-{i:04d}.json"
        if rec_p.exists():
            rec = json.loads(rec_p.read_text())
            n_ok += rec["adherent"]; stats["timeout"] += rec["timeout"]; stats["truncated"] += rec["truncated"]
            continue
        if arm == "base":
            text, n, tr, to = generate_cached(m, tok, r["prompt"], deadline_s=300)
        else:
            text, n, tr, to, _log = generate_deficit(
                m, tok, r["prompt"], ctrl, prompt_spans_of(r), TAU, BMAX, deadline_s=300)
        ok = adherent(r, text)
        n_ok += ok; stats["timeout"] += to; stats["truncated"] += tr
        rec = {"i": i, "adherent": bool(ok), "n_gen": n, "truncated": bool(tr),
               "timeout": bool(to), "response": text}
        tmp = rec_p.with_suffix(".tmp"); tmp.write_text(json.dumps(rec, ensure_ascii=False)); tmp.rename(rec_p)
        if i % 100 == 0:
            print(f"[{arm}] {i}/1024 adh {n_ok/(i+1):.4f}", flush=True)
    res[arm] = {"adherence": n_ok / 1024, **stats}
    print(f"[{arm}] {res[arm]}", flush=True)

b = {json.loads((outdir / f"base-{i:04d}.json").read_text())["i"]:
     json.loads((outdir / f"base-{i:04d}.json").read_text())["adherent"] for i in range(1024)}
w = {json.loads((outdir / f"wave-{i:04d}.json").read_text())["i"]:
     json.loads((outdir / f"wave-{i:04d}.json").read_text())["adherent"] for i in range(1024)}
n01 = sum(1 for i in b if not b[i] and w[i])  # wave fixes
n10 = sum(1 for i in b if b[i] and not w[i])  # wave breaks
p = mcnemar_exact_one_sided(n01, n10)
delta = (n01 - n10) / 1024
gate = {"delta_pts": round(delta * 100, 3), "n_fix": n01, "n_break": n10,
        "mcnemar_one_sided_p": round(p, 6),
        "excess_timeouts": res["wave"]["timeout"] - res["base"]["timeout"],
        "excess_truncated": res["wave"]["truncated"] - res["base"]["truncated"]}
gate["PASS"] = bool(delta >= 0.02 and p < 0.05
                    and gate["excess_timeouts"] <= 2 and gate["excess_truncated"] <= 5)
out = {"arms": res, "gate": gate, **meta}
(ROOT / "results" / "qwen" / f"b3-deficit-conf-s{SEED}.json").write_text(json.dumps(out, indent=1))
print(json.dumps({"arms": res, "gate": gate}, indent=1))
