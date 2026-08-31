# ruff: noqa
"""B4 — THE SEALED FIVE-ARM IFEval JOB (BENCH-WAVE v2-v3.3 registered).

SINGLE-USE INVARIANT: this script is the ONLY code allowed to generate
model output on the 541, and only under the seal discipline: a .started
marker refuses a second attempt per arm; per-item records are written
atomically (temp+rename) from the FIRST item; resume skips completed
(key, arm) items only after verifying every pinned sha256 (fail-closed).

Arms (env ARM + CTRL): base (CTRL=none), wave-s0, proxy-s0, wave-s1,
proxy-s1 (CTRL=<b3 ckpt path>). Registered decoding: pinned template,
KV-cached greedy, max_new 1024, EOS {151645,151643}, 300s per-prompt
timeout (recorded truncated-timeout; partial scored as-is). Scoring:
vendored verifiers, per-row random.seed(key) pin, four metrics.
Gain telemetry: mean/max response-row gain recorded per item (v3.3
addendum: histograms reported for both arms).
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

from stencil.bench import aggregate, generate_cached, load_ifeval, make_wave_bias_fn, score_response
from stencil.qwen3 import Qwen3
from stencil.wave import WaveController

ARM = os.environ["ARM"]
CTRL = os.environ.get("CTRL", "none")
TIMEOUT_S = 300

PINNED = {
    "models/qwen3-1.7b.pt": "13bfabb5592c7b35383a56471fba1c74c771f57587322e60faaabb96268b2829",
    "data/bench/ifeval_input_data.jsonl": None,  # from manifest at runtime
}


def main():
    man = json.loads((ROOT / "data" / "bench" / "pins-manifest.json").read_text())
    data_p = ROOT / "data" / "bench" / "ifeval_input_data.jsonl"
    data_sha = hashlib.sha256(data_p.read_bytes()).hexdigest()
    assert data_sha == "67ffeee0fcb87c317c5b08a2de85557b4a7e96ada6178aa645b4954fe4b53d49", "541 hash mismatch"
    trunk_sha = hashlib.sha256((ROOT / "models" / "qwen3-1.7b.pt").read_bytes()).hexdigest()
    assert trunk_sha == PINNED["models/qwen3-1.7b.pt"]
    ctrl_sha = "none"
    if CTRL != "none":
        ctrl_sha = hashlib.sha256(Path(CTRL).read_bytes()).hexdigest()

    outdir = ROOT / "results" / "qwen" / f"b4-{ARM}"
    outdir.mkdir(parents=True, exist_ok=True)
    meta = {"arm": ARM, "ctrl": CTRL, "ctrl_sha256": ctrl_sha, "trunk_sha256": trunk_sha,
            "data_sha256": data_sha,
            "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "timeout_s": TIMEOUT_S, "max_new": 1024}
    started = outdir / ".started"
    meta_p = outdir / "meta.json"
    if started.exists():
        # RESUME path only: provenance must match exactly (fail-closed)
        assert meta_p.exists() and json.loads(meta_p.read_text()) == meta, \
            "resume provenance mismatch — refusing (one sealed attempt per arm)"
    else:
        started.write_text(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        tmp = meta_p.with_suffix(".tmp")
        tmp.write_text(json.dumps(meta, indent=1))
        tmp.rename(meta_p)

    tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
    m = Qwen3()
    m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
    m = m.to(torch.bfloat16).cuda().eval()
    ctrl = None
    if CTRL != "none":
        ctrl = WaveController().cuda()
        ctrl.load_state_dict(torch.load(CTRL, map_location="cpu"))
        ctrl = ctrl.eval()

    rows = load_ifeval(data_p)
    assert len(rows) == 541
    per_prompt = []
    for idx, r in enumerate(rows):
        rec_p = outdir / f"item-{idx:03d}.json"
        if rec_p.exists():
            per_prompt.append(json.loads(rec_p.read_text())["scores"])
            continue
        state = {}
        gains = []
        if ctrl is not None:
            base_fn = make_wave_bias_fn(ctrl, state)

            def bias_fn(h20, P, past):
                row = base_fn(h20, P, past)
                if past > 0:
                    gains.append(float(ctrl.gain(h20[0, -1:].float())))
                return row
        else:
            bias_fn = None
        t0 = time.time()
        text, n_gen, truncated = generate_cached(m, tok, r["prompt"], bias_fn=bias_fn)
        wall = time.time() - t0
        scores = score_response(r, text)
        per_prompt.append(scores)
        rec = {"idx": idx, "key": r["key"], "scores": scores, "response": text,
               "n_gen": n_gen, "truncated": bool(truncated),
               "timeout": bool(wall > TIMEOUT_S), "wall_s": round(wall, 1),
               "gain_mean": (round(sum(gains) / len(gains), 4) if gains else None),
               "gain_max": (round(max(gains), 4) if gains else None)}
        tmp = rec_p.with_suffix(".tmp")
        tmp.write_text(json.dumps(rec, ensure_ascii=False))
        tmp.rename(rec_p)
        if idx % 25 == 0:
            agg = aggregate(per_prompt)
            print(f"{idx}/541 strict-prompt {agg['prompt_level_strict_acc']:.4f}", flush=True)
    summary = {"arm": ARM, **aggregate(per_prompt), "n": len(rows), **meta}
    (outdir / "summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
