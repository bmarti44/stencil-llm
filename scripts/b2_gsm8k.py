# ruff: noqa
"""B2 do-no-harm, GSM8K leg (v3.1/v3.2 FROZEN protocol): FULL test set
(1319); 4-shot, demos = pinned train rows 0-3 VERBATIM (incl. their
"#### n" lines); one user message
"Question: {q}\nAnswer: {a}\n\n" x4 + "Question: {q_test}\nAnswer:";
pinned chat template; KV-cached greedy; max_new 1024; EOS
{151645,151643}; no other stop strings; 300s per-prompt registered
timeout (recorded truncated-timeout, partial scored as-is); extractor:
LAST match of -?[0-9][0-9,]*\.?[0-9]* after removing "$", commas
stripped, trailing "." stripped, Decimal equality vs the "#### " gold;
no match / invalid Decimal = WRONG. Atomic per-item records; resume
skips completed items after provenance verification.

CTRL=<path>|none  ARM=<name>  SMOKE=<n items>
"""
import json
import hashlib
import os
import re
import sys
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401
import torch
from tokenizers import Tokenizer

from stencil.bench import generate_cached, make_wave_bias_fn
from stencil.qwen3 import Qwen3
from stencil.wave import WaveController

CTRL = os.environ.get("CTRL", "none")
ARM = os.environ.get("ARM", "base" if CTRL == "none" else "wave")
SMOKE = int(os.environ.get("SMOKE", "0"))
TIMEOUT_S = 300
NUM_RE = re.compile(r"-?[0-9][0-9,]*\.?[0-9]*")

PINNED_TRUNK = "13bfabb5592c7b35383a56471fba1c74c771f57587322e60faaabb96268b2829"


def extract(text):
    matches = NUM_RE.findall(text.replace("$", ""))
    if not matches:
        return None
    s = matches[-1].replace(",", "").rstrip(".")
    try:
        return Decimal(s)
    except InvalidOperation:
        return None


def gold_value(answer_text):
    tail = answer_text.split("####")[-1].strip()
    return extract(tail)


def main():
    man = json.loads((ROOT / "data" / "bench" / "pins-manifest.json").read_text())
    for name in ("gsm8k_test.jsonl", "gsm8k_demos.jsonl"):
        actual = hashlib.sha256((ROOT / "data" / "bench" / name).read_bytes()).hexdigest()
        assert actual == man["converted_sha256"][name], f"hash mismatch: {name}"
    mt = hashlib.sha256((ROOT / "models" / "qwen3-1.7b.pt").read_bytes()).hexdigest()
    assert mt == PINNED_TRUNK
    ctrl_sha = "none"
    if CTRL != "none":
        ctrl_sha = hashlib.sha256(Path(CTRL).read_bytes()).hexdigest()

    tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
    m = Qwen3()
    m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
    m = m.to(torch.bfloat16).cuda().eval()
    ctrl = None
    if CTRL != "none":
        ctrl = WaveController().cuda()
        ctrl.load_state_dict(torch.load(CTRL, map_location="cpu"))
        ctrl = ctrl.eval()

    demos = [json.loads(line) for line in open(ROOT / "data" / "bench" / "gsm8k_demos.jsonl")]
    prefix = "".join(f"Question: {d['question']}\nAnswer: {d['answer']}\n\n" for d in demos)
    rows = [json.loads(line) for line in open(ROOT / "data" / "bench" / "gsm8k_test.jsonl")]
    assert len(rows) == 1319
    if SMOKE:
        rows = rows[:SMOKE]

    outdir = ROOT / "results" / "qwen" / f"b2-gsm8k-{ARM}"
    outdir.mkdir(parents=True, exist_ok=True)
    meta = {"arm": ARM, "ctrl": CTRL, "ctrl_sha256": ctrl_sha, "trunk_sha256": mt,
            "data_sha256": man["converted_sha256"]["gsm8k_test.jsonl"],
            "demos_sha256": man["converted_sha256"]["gsm8k_demos.jsonl"],
            "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    meta_p = outdir / "meta.json"
    if meta_p.exists():
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
        user_msg = prefix + f"Question: {r['question']}\nAnswer:"
        state = {}
        bias_fn = make_wave_bias_fn(ctrl, state) if ctrl is not None else None
        t0 = time.time()
        text, n_gen, truncated = generate_cached(m, tok, user_msg, bias_fn=bias_fn)
        wall = time.time() - t0
        timeout = wall > TIMEOUT_S
        pred = extract(text)
        gold = gold_value(r["answer"])
        assert gold is not None, f"gold unparseable at {i}"
        right = pred is not None and pred == gold
        n_right += right
        rec = {"i": i, "right": bool(right), "pred": (str(pred) if pred is not None else None),
               "gold": str(gold), "n_gen": n_gen, "truncated": bool(truncated),
               "timeout": bool(timeout), "wall_s": round(wall, 1), "response": text}
        tmp = rec_p.with_suffix(".tmp")
        tmp.write_text(json.dumps(rec, ensure_ascii=False))
        tmp.rename(rec_p)
        if i % 50 == 0:
            print(f"{i}/{len(rows)} acc {n_right / (i + 1):.4f}", flush=True)
    summary = {"arm": ARM, "n": len(rows), "right": n_right, "acc": round(n_right / len(rows), 6), **meta}
    (outdir / "summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
