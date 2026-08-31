# ruff: noqa
"""B4 — THE SEALED FIVE-ARM IFEval JOB (v4.1: ONE entry point, ONE seal).

Checkpoint-iii round-2 rebuild (sol FINDING-1/2, fable FINDING-1/3/4):
- HARD-CODED arm table: five registered arms in fixed order, each bound
  to its selected controller file AND its expected sha256 (from the B3
  training records). No env-configurable arms. A sixth arm cannot
  exist: the seal manifest is global and the table is closed.
- GLOBAL seal: results/qwen/b4/.started + manifest.json cover the
  whole five-arm job; resume requires byte-exact manifest equality
  (any drift in trunk/tokenizer/module/verifier-tree/controller/data/
  runner hashes fail-closes).
- REAL 300s per-prompt deadline inside generation (runaway backstop,
  ~5.6x the admission's worst case); a timed-out partial response is
  scored as-is with the timeout flag in the record and all reporting.
- Gain telemetry includes the PREFILL'S SCORED ROW (first response
  token) as row 1 of the histogram source.

SINGLE-USE INVARIANT: this is the ONLY code allowed to generate on the
541. Per-item records are atomic (temp+rename) from the first item;
resume skips completed items only.
"""
import json
import hashlib
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401
import torch
from tokenizers import Tokenizer

from stencil.bench import (
    aggregate,
    generate_cached,
    load_ifeval,
    make_wave_bias_fn,
    provenance_pins,
    score_response,
)
from stencil.qwen3 import Qwen3
from stencil.wave import WaveController

TIMEOUT_S = 300
DATA_SHA = "67ffeee0fcb87c317c5b08a2de85557b4a7e96ada6178aa645b4954fe4b53d49"

# THE closed arm table (fixed order; controller hashes from the B3 records)
ARMS = [
    ("base", None, None),
    ("wave-s0", "results/qwen/b3-ce-s0.pt",
     "0e2574ffd431406f7ffba15e9940e42d7f141c27566d6b02110b38acebb6c524"),
    ("proxy-s0", "results/qwen/b3-proxy-s0.pt",
     "26988a952e8ef119233b41c67af8fe01adeba800e40fea835b7467c2f81a7c99"),
    ("wave-s1", "results/qwen/b3-ce-s1.pt",
     "e028b63f95623fe9d35b4f89eed07ab51effdcde6cc380370d4ac95dc4bcd631"),
    ("proxy-s1", "results/qwen/b3-proxy-s1.pt",
     "93f343723b52cea2b17e38193cd7e511ac8d6835e33fb2e715149359f954bf33"),
]


def build_manifest():
    pins = provenance_pins(ROOT, extra_files=[p for _, p, _ in ARMS if p]
                           + ["data/bench/ifeval_input_data.jsonl", "scripts/b4_ifeval.py"])
    assert pins["data/bench/ifeval_input_data.jsonl"] == DATA_SHA, "541 hash mismatch"
    for name, path, want in ARMS:
        if path is not None:
            assert pins[path] == want, f"controller hash mismatch for {name}: {pins[path]}"
    return {"arms": [[n, p, h] for n, p, h in ARMS], "timeout_s": TIMEOUT_S,
            "max_new": 1024, "pins": pins}


def run_arm(m, tok, rows, name, ctrl, outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    per_prompt = []
    for idx, r in enumerate(rows):
        rec_p = outdir / f"item-{idx:03d}.json"
        if rec_p.exists():
            per_prompt.append(json.loads(rec_p.read_text())["scores"])
            continue
        gains = []
        if ctrl is not None:
            state = {}
            inner = make_wave_bias_fn(ctrl, state)

            def bias_fn(h20, P, past):
                row = inner(h20, P, past)
                if past == 0 and "prefill_field" in state:
                    gains.append(float(ctrl.gain(h20[0, P - 1:P].float())))
                elif past > 0:
                    gains.append(float(ctrl.gain(h20[0, -1:].float())))
                return row
        else:
            bias_fn = None
        t0 = time.time()
        text, n_gen, truncated, timeout = generate_cached(
            m, tok, r["prompt"], bias_fn=bias_fn, deadline_s=TIMEOUT_S)
        wall = time.time() - t0
        scores = score_response(r, text)
        per_prompt.append(scores)
        rec = {"idx": idx, "key": r["key"], "scores": scores, "response": text,
               "n_gen": n_gen, "truncated": bool(truncated), "timeout": bool(timeout),
               "wall_s": round(wall, 1),
               "gain_mean": (round(sum(gains) / len(gains), 4) if gains else None),
               "gain_max": (round(max(gains), 4) if gains else None),
               "gain_min": (round(min(gains), 4) if gains else None)}
        tmp = rec_p.with_suffix(".tmp")
        tmp.write_text(json.dumps(rec, ensure_ascii=False))
        tmp.rename(rec_p)
        if idx % 25 == 0:
            agg = aggregate(per_prompt)
            print(f"[{name}] {idx}/541 strict-prompt {agg['prompt_level_strict_acc']:.4f}", flush=True)
    summary = {"arm": name, **aggregate(per_prompt), "n": len(rows)}
    (outdir / "summary.json").write_text(json.dumps(summary, indent=1))
    print(f"[{name}] " + json.dumps(summary), flush=True)


def main():
    manifest = build_manifest()
    jobdir = ROOT / "results" / "qwen" / "b4"
    jobdir.mkdir(parents=True, exist_ok=True)
    man_p = jobdir / "manifest.json"
    started = jobdir / ".started"
    if started.exists():
        assert man_p.exists() and json.loads(man_p.read_text()) == manifest, \
            "resume provenance mismatch — refusing (one sealed five-arm attempt)"
        print("RESUMING sealed job (provenance verified)", flush=True)
    else:
        started.write_text(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        tmp = man_p.with_suffix(".tmp")
        tmp.write_text(json.dumps(manifest, indent=1))
        tmp.rename(man_p)

    tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
    m = Qwen3()
    m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
    m = m.to(torch.bfloat16).cuda().eval()
    rows = load_ifeval(ROOT / "data" / "bench" / "ifeval_input_data.jsonl")
    assert len(rows) == 541

    for name, path, _ in ARMS:
        ctrl = None
        if path is not None:
            ctrl = WaveController().cuda()
            ctrl.load_state_dict(torch.load(ROOT / path, map_location="cpu"))
            ctrl = ctrl.eval()
        run_arm(m, tok, rows, name, ctrl, jobdir / name)
    print("B4 SEALED JOB COMPLETE", flush=True)


if __name__ == "__main__":
    main()
