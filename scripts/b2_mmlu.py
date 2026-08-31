# ruff: noqa
"""B2 do-no-harm, MMLU-Redux leg (v3.1/v3.2 FROZEN protocol):
error_type=="ok" items ONLY (5330); zero-shot; prompt
"Question: {q}\nA. ..\nB. ..\nC. ..\nD. ..\nAnswer:" through the pinned
chat template; single KV-cached prefill per item per arm; score =
log-softmax at the final position over the four single tokens
{" A":362, " B":425, " C":356, " D":422}; argmax vs gold; exact-float
ties = WRONG (fail-closed). Wave arm: bias_hook biases the SCORED
final row only (registered). Records: atomic temp+rename per item;
resume skips completed items after hash verification (fail-closed).

CTRL=<path to controller .pt>|none  ARM=<name>  (base: CTRL=none)
Gate (vs an existing base run): Tango upper bound < 0.5pt margin.
"""
import json
import hashlib
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401
import torch
import torch.nn.functional as F
from tokenizers import Tokenizer

from stencil.bench import TMPL, wave_hook_for_prefill
from stencil.qwen3 import KVCache, Qwen3
from stencil.wave import WaveController

CTRL = os.environ.get("CTRL", "none")
ARM = os.environ.get("ARM", "base" if CTRL == "none" else "wave")
SMOKE = int(os.environ.get("SMOKE", "0"))
CHOICE_TOKENS = [362, 425, 356, 422]  # " A" " B" " C" " D" (asserted below)

PINNED = {
    "data/bench/mmlu_redux_2.jsonl": None,  # filled from manifest
    "models/qwen3-1.7b.pt": "13bfabb5592c7b35383a56471fba1c74c771f57587322e60faaabb96268b2829",
}


def item_prompt(r):
    c = r["choices"]
    return (f"Question: {r['question']}\nA. {c[0]}\nB. {c[1]}\nC. {c[2]}\nD. {c[3]}\nAnswer:")


def main():
    man = json.loads((ROOT / "data" / "bench" / "pins-manifest.json").read_text())
    data_sha = man["converted_sha256"]["mmlu_redux_2.jsonl"]
    actual = hashlib.sha256((ROOT / "data" / "bench" / "mmlu_redux_2.jsonl").read_bytes()).hexdigest()
    assert actual == data_sha, "dataset hash mismatch"
    mt = hashlib.sha256((ROOT / "models" / "qwen3-1.7b.pt").read_bytes()).hexdigest()
    assert mt == PINNED["models/qwen3-1.7b.pt"], "trunk hash mismatch"
    ctrl_sha = "none"
    if CTRL != "none":
        ctrl_sha = hashlib.sha256(Path(CTRL).read_bytes()).hexdigest()

    tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
    for s, tid in zip([" A", " B", " C", " D"], CHOICE_TOKENS):
        ids = tok.encode(s).ids
        assert ids == [tid], f"choice token drifted: {s} -> {ids}"

    m = Qwen3()
    m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
    m = m.to(torch.bfloat16).cuda().eval()
    ctrl = None
    if CTRL != "none":
        ctrl = WaveController().cuda()
        ctrl.load_state_dict(torch.load(CTRL, map_location="cpu"))
        ctrl = ctrl.eval()

    rows = [json.loads(line) for line in open(ROOT / "data" / "bench" / "mmlu_redux_2.jsonl")]
    rows = [r for r in rows if r["error_type"] == "ok"]
    assert len(rows) == 5330
    if SMOKE:
        rows = rows[:SMOKE]

    outdir = ROOT / "results" / "qwen" / f"b2-mmlu-{ARM}"
    outdir.mkdir(parents=True, exist_ok=True)
    meta = {"arm": ARM, "ctrl": CTRL, "ctrl_sha256": ctrl_sha, "data_sha256": data_sha,
            "trunk_sha256": mt, "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    meta_p = outdir / "meta.json"
    if meta_p.exists():  # resume: verify identical provenance (fail-closed)
        assert json.loads(meta_p.read_text()) == meta, "resume provenance mismatch"
    else:
        tmp = meta_p.with_suffix(".tmp")
        tmp.write_text(json.dumps(meta, indent=1))
        tmp.rename(meta_p)

    n_right = 0
    for i, r in enumerate(rows):
        rec_p = outdir / f"item-{i:05d}.json"
        if rec_p.exists():
            n_right += json.loads(rec_p.read_text())["right"]
            continue
        ids = tok.encode(TMPL.format(p=item_prompt(r))).ids
        P = len(ids)
        hook = wave_hook_for_prefill(ctrl, P) if ctrl is not None else None
        with torch.no_grad():
            logits = m(torch.tensor([ids], device="cuda"), cache=KVCache(), bias_hook=hook)[0, -1].float()
        lp = F.log_softmax(logits, dim=-1)[CHOICE_TOKENS]
        vals = lp.tolist()
        top = max(vals)
        pred = vals.index(top)
        tie = vals.count(top) > 1
        right = (not tie) and (pred == r["answer"])
        n_right += right
        rec = {"i": i, "subject": r["subject"], "gold": r["answer"], "pred": pred,
               "tie": tie, "right": bool(right), "logprobs": [round(v, 6) for v in vals]}
        tmp = rec_p.with_suffix(".tmp")
        tmp.write_text(json.dumps(rec))
        tmp.rename(rec_p)
        if i % 500 == 0:
            print(f"{i}/{len(rows)} acc {n_right / (i + 1):.4f}", flush=True)
    summary = {"arm": ARM, "n": len(rows), "right": n_right, "acc": round(n_right / len(rows), 6), **meta}
    (outdir / "summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
