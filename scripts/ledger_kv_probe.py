# ruff: noqa
"""LEDGER-KV feasibility probe (registered in LEDGER-PLAN.md, section LEDGER-KV).

Synthetic multi-turn corpus (data/b3/mt-train-300.jsonl; Multi-IF never
read). Turns 1..T-1 are generated natively (base) to build history; at the
LAST turn the prior history is EVICTED from the KV cache after prefill and
the arms differ only in what survives:
  full            — nothing evicted (ceiling)
  evicted         — all prior turns dropped, nothing pinned
  pinned          — prior turns dropped EXCEPT the aged constraint clauses' K/V
  pinned_wave     — pinned + uniform pre-softmax bias (dose) on the pinned
                    columns at WAVE_LAYERS during decode
Scored on the last turn's AGED constraints (origin turn < last) with the
vendored checkers; degeneracy = truncation / repeated-4gram fraction.
Per-session atomic records from the first session."""
import argparse
import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401

OPENER = "<|im_start|>assistant\n<think>\n\n</think>\n\n"
ARMS = ("full", "evicted", "pinned", "pinned_control", "pinned_wave")
DEGENERATE_REP4 = 0.5  # registered degeneracy definition: repeated-4gram frac > 0.5 OR truncated

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def atomic_json(path, value):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=1))
    tmp.rename(path)

def repeated_4gram_frac(ids):
    if len(ids) < 8:
        return 0.0
    grams = [tuple(ids[i:i + 4]) for i in range(len(ids) - 3)]
    return 1.0 - len(set(grams)) / len(grams)

def matched_control_spans(keep, evict_range):
    """same-width windows inside the evicted region, disjoint from every
    constraint span and from each other, nearest FOLLOWING each span
    (falls back to nearest preceding)."""
    taken = [tuple(k) for k in keep]
    out = []
    for s, e in keep:
        w = e - s
        cand = None
        for start in list(range(e, evict_range[1] - w + 1)) + list(range(s - w, evict_range[0] - 1, -1)):
            if start < evict_range[0]:
                continue
            if all(start + w <= a or start >= b for a, b in taken):
                cand = (start, start + w)
                break
        if cand is None:
            continue
        taken.append(cand)
        out.append(cand)
    return out


def is_degenerate(g):
    return bool(g["truncated"] or g["rep4"] > DEGENERATE_REP4)


def run_arm(m, tok, ids, arm, keep, evict_range, dose, max_new, deadline_s, control_keep=()):
    import torch

    from stencil.bench import EOS, WAVE_LAYERS
    from stencil.qwen3 import KVCache
    cache = KVCache()
    out = []
    t0 = time.monotonic()
    timed_out = False
    with torch.no_grad():
        logits = m(torch.tensor([ids], device="cuda"), cache=cache)
        cols = []
        if arm != "full":
            pins = {"evicted": (), "pinned": keep, "pinned_wave": keep, "pinned_control": control_keep}[arm]
            imap = cache.evict(evict_range[0], evict_range[1], keep=pins)
            cols = sorted({imap[o] for s, e in pins for o in range(s, e) if o in imap})
        nxt = int(logits[0, -1].argmax())
        while nxt not in EOS and len(out) < max_new:
            if time.monotonic() - t0 > deadline_s:
                timed_out = True
                break
            out.append(nxt)
            ab = None
            if arm == "pinned_wave" and cols:
                row = torch.zeros(1, cache.k[0].shape[2] + 1, device="cuda")
                row[0, cols] = dose
                ab = {L: row for L in WAVE_LAYERS}
            logits = m(torch.tensor([[nxt]], device="cuda"), cache=cache, attn_bias=ab)
            nxt = int(logits[0, -1].argmax())
    return {
        "text": tok.decode(out), "n": len(out), "truncated": len(out) >= max_new,
        "timed_out": timed_out, "rep4": repeated_4gram_frac(out),
        "pinned_cols": len(cols), "cache_cols": int(cache.k[0].shape[2]),
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sessions", type=int, default=20)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--max-new", type=int, default=320)
    ap.add_argument("--deadline", type=float, default=300.0)
    ap.add_argument("--dose", type=float, default=3.0)
    ap.add_argument("--out", default="ledger-kv-probe")
    args = ap.parse_args()
    import torch
    from tokenizers import Tokenizer

    from stencil.causal_moments import score_row_constraints
    from stencil.e2 import constraint_span_records
    from stencil.qwen3 import Qwen3

    data_path = ROOT / "data" / "b3" / "mt-train-300.jsonl"
    model_path = ROOT / "models" / "qwen3-1.7b.pt"
    sessions = [json.loads(l) for l in data_path.read_text().splitlines()][args.start:args.start + args.sessions]
    outdir = ROOT / "results" / "qwen" / args.out
    outdir.mkdir(parents=True, exist_ok=True)
    meta = {"schema": 1, "corpus": str(data_path.relative_to(ROOT)), "corpus_sha256": sha(data_path),
            "model_sha256": sha(model_path), "runner_sha256": sha(__file__),
            "qwen3_sha256": sha(ROOT / "src/stencil/qwen3.py"), "arms": list(ARMS),
            "dose": args.dose, "max_new": args.max_new, "deadline": args.deadline,
            "position_policy": "no_reindex_positions_continue", "degenerate_def": f"truncated or rep4>{DEGENERATE_REP4}", "history_decode": "raw_context_greedy"}
    mp = outdir / "meta.json"
    if mp.exists():
        if json.loads(mp.read_text()) != meta:
            raise RuntimeError("resume provenance mismatch")
    else:
        atomic_json(mp, meta)

    tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
    m = Qwen3()
    m.load_state_dict(torch.load(model_path, map_location="cpu"), strict=True)
    m = m.to(torch.bfloat16).cuda().eval()

    for si, sess in enumerate(sessions, start=args.start):
        rp = outdir / f"session-{si:03d}.json"
        if rp.exists():
            continue
        turns = sess["turns"]
        history = ""
        for turn in turns[:-1]:
            ctx = history + f"<|im_start|>user\n{turn['prompt']}<|im_end|>\n" + OPENER
            # verifier (2026-09-01): generate_cached wraps in TMPL -> double
            # scaffold; decode the raw context instead
            g = run_arm(m, tok, tok.encode(ctx).ids, "full", [], None, 0.0, args.max_new, args.deadline)
            text = g["text"]
            history += f"<|im_start|>user\n{turn['prompt']}<|im_end|>\n<|im_start|>assistant\n{text}<|im_end|>\n"
        last = turns[-1]
        context = history + f"<|im_start|>user\n{last['prompt']}<|im_end|>\n" + OPENER
        ids = tok.encode(context).ids
        enc = tok.encode(context)
        recs = constraint_span_records(tok, context)
        T_last = len(turns)
        keep = [tuple(r["span"]) for r in recs if r["origin_turn"] < T_last]
        # evict from the first token of turn-1 content to the token where the
        # LAST user turn's marker begins
        last_marker = context.rfind("<|im_start|>user\n")
        first_content = context.find("<|im_start|>user\n") + len("<|im_start|>user\n")
        tok_first = next(i for i, (a, b) in enumerate(enc.offsets) if b > first_content)
        tok_last = next(i for i, (a, b) in enumerate(enc.offsets) if b > last_marker)
        evict_range = (tok_first, tok_last)
        control_keep = matched_control_spans(keep, evict_range)
        row = {"key": int(sess["key"]) * 10 + T_last,
               "instruction_id_list": last["instruction_id_list"], "kwargs": last["kwargs"]}
        # aged constraints = those whose clause originates in an earlier turn;
        # map by order: the corpus lists are cumulative in introduction order
        n_aged = sum(1 for r in recs if r["origin_turn"] < T_last)
        arms = {}
        for arm in ARMS:
            g = run_arm(m, tok, ids, arm, keep, evict_range, args.dose, args.max_new, args.deadline, control_keep=control_keep)
            g["degenerate"] = is_degenerate(g)
            scores = score_row_constraints(row, g["text"])
            g["scores"] = list(scores)
            g["aged_pass"] = sum(scores[:n_aged])
            g["aged_n"] = n_aged
            arms[arm] = g
        rec = {"session": si, "key": sess["key"], "topic": sess["topic"], "n_turns": T_last,
               "evict_range": evict_range, "keep": keep, "control_keep": control_keep, "n_aged": n_aged,
               "context_tokens": len(ids), "arms": arms}
        atomic_json(rp, rec)
        print(f"session {si} aged={n_aged} " + " ".join(f"{a}={arms[a]['aged_pass']}/{n_aged}(rep4={arms[a]['rep4']:.2f},n={arms[a]['n']})" for a in ARMS), flush=True)

    records = [json.loads(p.read_text()) for p in sorted(outdir.glob("session-*.json"))]
    summ = {**meta, "sessions": len(records)}
    for a in ARMS:
        p = sum(r["arms"][a]["aged_pass"] for r in records); n = sum(r["n_aged"] for r in records)
        summ[a] = {"aged_pass": p, "aged_n": n, "rate": p / max(1, n),
                   "trunc": sum(r["arms"][a]["truncated"] for r in records),
                   "timeout": sum(r["arms"][a]["timed_out"] for r in records),
                   "mean_rep4": sum(r["arms"][a]["rep4"] for r in records) / max(1, len(records)),
                   "degenerate": sum(is_degenerate(r["arms"][a]) for r in records)}
    gap = summ["full"]["rate"] - summ["evicted"]["rate"]
    summ["gap_full_minus_evicted"] = gap
    summ["recovered_frac_pinned"] = (summ["pinned"]["rate"] - summ["evicted"]["rate"]) / gap if gap > 0 else None
    summ["recovered_frac_pinned_wave"] = (summ["pinned_wave"]["rate"] - summ["evicted"]["rate"]) / gap if gap > 0 else None
    atomic_json(outdir / "summary.json", summ)
    print(json.dumps({k: v for k, v in summ.items() if k in ARMS or k.startswith(("gap", "recovered"))}, indent=1))

if __name__ == "__main__":
    main()
