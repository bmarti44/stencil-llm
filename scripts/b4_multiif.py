# ruff: noqa
"""Multi-IF English runner (EXPLORATORY, registered v3.1/v3.2): all 909
conversations x 3 turns = 2727 turns; each arm consumes ITS OWN prior
responses; history serialization = prior turns as user/assistant blocks
WITHOUT think tags, final turn opens with the pinned assistant opener;
turn t scored with turn t's instruction list/kwargs (the dataset's
lists are already cumulative); per-turn-index (n=909) + pooled
(n=2727) four metrics. Scoring seed pin: random.seed(stable hash of
"key:turn") per scored turn (mirror of the IFEval per-row pin).
Atomic per-conversation records; hash-verified resume.

ARM=<name> CTRL=<path>|none SMOKE=<n conversations>
"""
import json
import hashlib
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401
import torch
from tokenizers import Tokenizer

from stencil.bench import EOS, MAX_NEW, aggregate, make_wave_bias_fn
from stencil.qwen3 import KVCache, Qwen3
from stencil.wave import WaveController

sys.path.insert(0, str(ROOT / "vendor"))
import langdetect

langdetect.DetectorFactory.seed = 0
from ifeval import utils as ifeval_utils  # noqa: E402

ARM = os.environ["ARM"]
CTRL = os.environ.get("CTRL", "none")
SMOKE = int(os.environ.get("SMOKE", "0"))
OPENER = "<|im_start|>assistant\n<think>\n\n</think>\n\n"


def seed_of(key, turn):
    return int(hashlib.sha256(f"{key}:{turn}".encode()).hexdigest()[:8], 16)


def turn_doc(row, t):
    """(prompt_content, instruction_id_list, kwargs list) for turn t (1-3)."""
    p = json.loads(row[f"turn_{t}_prompt"])["content"]
    ids = json.loads(row[f"turn_{t}_instruction_id_list"])
    kws = [json.loads(k) for k in json.loads(row[f"turn_{t}_kwargs"])]
    return p, ids, kws


def score_turn(row, t, response):
    import random
    p, ids, kws = turn_doc(row, t)
    random.seed(seed_of(row["key"], t))
    doc = {"key": 0, "prompt": p, "instruction_id_list": ids, "kwargs": kws}
    return ifeval_utils.process_results(doc, [response])


def gen(m, tok, ctrl, history_text):
    """cached greedy over an explicit conversation string (history +
    pinned opener already appended by the caller)."""
    ids = tok.encode(history_text).ids
    cache = KVCache()
    out = []
    state = {}
    bias_fn = make_wave_bias_fn(ctrl, state) if ctrl is not None else None

    def hook_for(past, P):
        if bias_fn is None:
            return None
        def hook(h20):
            row = bias_fn(h20, P, past)
            if row is None:
                return None
            from stencil.bench import WAVE_LAYERS
            return {layer: row for layer in WAVE_LAYERS}
        return (20, hook)

    P = len(ids)
    with torch.no_grad():
        logits = m(torch.tensor([ids], device="cuda"), cache=cache, bias_hook=hook_for(0, P))
        nxt = int(logits[0, -1].argmax())
        while nxt not in EOS and len(out) < MAX_NEW:
            out.append(nxt)
            logits = m(torch.tensor([[nxt]], device="cuda"), cache=cache,
                       bias_hook=hook_for(cache.length, P))
            nxt = int(logits[0, -1].argmax())
    return tok.decode(out), len(out), len(out) >= MAX_NEW


def main():
    man = json.loads((ROOT / "data" / "bench" / "pins-manifest.json").read_text())
    data_p = ROOT / "data" / "bench" / "multiif_en.jsonl"
    data_sha = hashlib.sha256(data_p.read_bytes()).hexdigest()
    assert data_sha == man["converted_sha256"]["multiif_en.jsonl"]
    trunk_sha = hashlib.sha256((ROOT / "models" / "qwen3-1.7b.pt").read_bytes()).hexdigest()
    ctrl_sha = "none" if CTRL == "none" else hashlib.sha256(Path(CTRL).read_bytes()).hexdigest()

    tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
    m = Qwen3()
    m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
    m = m.to(torch.bfloat16).cuda().eval()
    ctrl = None
    if CTRL != "none":
        ctrl = WaveController().cuda()
        ctrl.load_state_dict(torch.load(CTRL, map_location="cpu"))
        ctrl = ctrl.eval()

    rows = [json.loads(line) for line in open(data_p)]
    assert len(rows) == 909
    if SMOKE:
        rows = rows[:SMOKE]

    outdir = ROOT / "results" / "qwen" / f"b4-multiif-{ARM}"
    outdir.mkdir(parents=True, exist_ok=True)
    meta = {"arm": ARM, "ctrl": CTRL, "ctrl_sha256": ctrl_sha, "trunk_sha256": trunk_sha,
            "data_sha256": data_sha,
            "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    meta_p = outdir / "meta.json"
    if meta_p.exists():
        assert json.loads(meta_p.read_text()) == meta, "resume provenance mismatch"
    else:
        tmp = meta_p.with_suffix(".tmp")
        tmp.write_text(json.dumps(meta, indent=1))
        tmp.rename(meta_p)

    per_turn = {1: [], 2: [], 3: []}
    for ci, row in enumerate(rows):
        rec_p = outdir / f"conv-{ci:03d}.json"
        if rec_p.exists():
            rec = json.loads(rec_p.read_text())
            for t in (1, 2, 3):
                per_turn[t].append(rec["scores"][str(t)])
            continue
        history = ""
        rec = {"ci": ci, "key": row["key"], "scores": {}, "responses": {}, "gen": {}}
        for t in (1, 2, 3):
            p, _, _ = turn_doc(row, t)
            history += f"<|im_start|>user\n{p}<|im_end|>\n"
            text, n, trunc = gen(m, tok, ctrl, history + OPENER)
            rec["responses"][str(t)] = text
            rec["gen"][str(t)] = {"n": n, "truncated": bool(trunc)}
            rec["scores"][str(t)] = score_turn(row, t, text)
            per_turn[t].append(rec["scores"][str(t)])
            history += f"<|im_start|>assistant\n{text}<|im_end|>\n"
        tmp = rec_p.with_suffix(".tmp")
        tmp.write_text(json.dumps(rec, ensure_ascii=False))
        tmp.rename(rec_p)
        if ci % 20 == 0:
            print(f"{ci}/{len(rows)}", flush=True)
    summary = {"arm": ARM, **meta}
    for t in (1, 2, 3):
        summary[f"turn{t}"] = aggregate(per_turn[t])
    summary["pooled"] = aggregate(per_turn[1] + per_turn[2] + per_turn[3])
    (outdir / "summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps({k: v for k, v in summary.items() if k.startswith(("turn", "pooled"))}, indent=1))


if __name__ == "__main__":
    main()
