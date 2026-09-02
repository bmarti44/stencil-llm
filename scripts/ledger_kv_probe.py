# ruff: noqa
"""LEDGER-KV feasibility probe (registered in LEDGER-PLAN.md, section LEDGER-KV).

Synthetic multi-turn corpus (data/b3/mt-train-300.jsonl; Multi-IF never
read). Turns 1..T-1 are generated natively (base) to build history; at the
LAST turn the prior history is EVICTED from the KV cache after prefill and
the arms differ only in what survives:
  full                — nothing evicted (ceiling)
  evicted             — all prior turns dropped, nothing pinned
  pinned              — prior turns dropped EXCEPT aged constraint-clause K/V
  pinned_control      — exactly the same deduplicated column mass, non-constraint
  pinned_wave_d0.5    — pinned + 0.5 pre-softmax bias on pinned columns
  pinned_wave_d1.0    — pinned + 1.0 pre-softmax bias on pinned columns
  pinned_wave_d3.0    — pinned + 3.0 pre-softmax bias on pinned columns
Scored on the last turn's AGED constraints (origin turn < last) with the
vendored checkers; degeneracy = truncation / repeated-4gram fraction.
Per-session atomic records from the first session."""
import argparse
import hashlib
import json
import random
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401

OPENER = "<|im_start|>assistant\n<think>\n\n</think>\n\n"
BASE_ARMS = ("full", "evicted", "pinned", "pinned_control")
DEFAULT_DOSES = (0.5, 1.0, 3.0)
DEGENERATE_REP4 = 0.5  # registered degeneracy definition: repeated-4gram frac > 0.5 OR truncated
WAVE_KILL_RULE = "degenerate sessions > 2/20 at best dose"


def dose_label(dose):
    return str(float(dose))


def arm_names(doses):
    return BASE_ARMS + tuple(f"pinned_wave_d{dose_label(dose)}" for dose in doses)


def parse_args(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--sessions", type=int, default=20)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--max-new", type=int, default=512)
    ap.add_argument("--deadline", type=float, default=300.0)
    ap.add_argument("--dose", type=float, nargs="+", default=list(DEFAULT_DOSES))
    ap.add_argument("--out", default="ledger-kv-probe")
    return ap.parse_args(argv)

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def tree_sha(root):
    root = Path(root)
    files = sorted(p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc")
    digest = hashlib.sha256()
    for path in files:
        digest.update(str(path.relative_to(root)).encode()); digest.update(b"\0")
        digest.update(path.read_bytes()); digest.update(b"\0")
    return digest.hexdigest()


def provenance_manifest():
    files = {
        "determinism.py": ROOT / "src/stencil/determinism.py",
        "tokenizer.json": ROOT / "models/qwen3-1.7b-hf/tokenizer.json",
        "bench.py": ROOT / "src/stencil/bench.py",
        "ctrb.py": ROOT / "src/stencil/ctrb.py",
        "qwen3.py": ROOT / "src/stencil/qwen3.py",
        "ledger_kv_probe.py": Path(__file__).resolve(),
        "salience2.py": ROOT / "src/stencil/salience2.py",
        "salience2_weights.json": ROOT / "src/stencil/salience2_weights.json",
        "salience2_hybrid.json": ROOT / "src/stencil/salience2_hybrid.json",
        "salience2_probe.npz": ROOT / "src/stencil/salience2_probe.npz",
    }
    out = {name: sha(path) for name, path in files.items()}
    out["vendor/ifeval"] = tree_sha(ROOT / "vendor/ifeval")
    return out


def build_meta(*, doses, max_new, deadline, artifact_hashes=None):
    return {
        "schema": 3,
        "arms": list(arm_names(doses)),
        "doses": [float(dose) for dose in doses],
        "max_new": max_new,
        "deadline": deadline,
        "position_policy": "no_reindex_positions_continue",
        "degenerate_def": f"truncated or rep4>{DEGENERATE_REP4}",
        "history_decode": "raw_context_greedy",
        "wave_kill_rule": WAVE_KILL_RULE,
        "provenance": provenance_manifest(),
        **(artifact_hashes or {}),
    }

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
    """Position-match exactly the deduplicated surviving-column mass."""
    lo, hi = evict_range
    pinned = {column for start, end in keep for column in range(max(lo, start), min(hi, end))}
    available = set(range(lo, hi)) - pinned
    if len(available) < len(pinned):
        raise RuntimeError(f"cannot match {len(pinned)} pinned columns with only {len(available)} controls")
    chosen = set()
    for target in sorted(pinned):
        candidate = min(available, key=lambda col: (abs(col - target), col < target, col))
        chosen.add(candidate)
        available.remove(candidate)
    ordered = sorted(chosen)
    spans = []
    for column in ordered:
        if spans and spans[-1][1] == column:
            spans[-1] = (spans[-1][0], column + 1)
        else:
            spans.append((column, column + 1))
    assert len({i for start, end in spans for i in range(start, end)}) == len(pinned)
    return spans


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
            pins = (() if arm == "evicted" else control_keep if arm == "pinned_control" else keep)
            imap = cache.evict(evict_range[0], evict_range[1], keep=pins)
            cols = sorted({imap[o] for s, e in pins for o in range(s, e) if o in imap})
        nxt = int(logits[0, -1].argmax())
        while nxt not in EOS and len(out) < max_new:
            if time.monotonic() - t0 > deadline_s:
                timed_out = True
                break
            out.append(nxt)
            ab = None
            if arm.startswith("pinned_wave_d") and cols:
                row = torch.zeros(1, cache.k[0].shape[2] + 1, device="cuda")
                row[0, cols] = dose
                ab = {L: row for L in WAVE_LAYERS}
            logits = m(torch.tensor([[nxt]], device="cuda"), cache=cache, attn_bias=ab)
            nxt = int(logits[0, -1].argmax())
    return {
        "text": tok.decode(out), "n": len(out), "truncated": len(out) >= max_new,
        "timed_out": timed_out, "rep4": repeated_4gram_frac(out),
        "generated_token_ids": list(out),
        "pinned_cols": len(cols), "cache_cols": int(cache.k[0].shape[2]),
    }


def session_record(*, session, key, topic, n_turns, evict_range, keep, control_keep,
                   n_aged, history_token_ids, context_token_ids, arms):
    pinned_columns = {i for start, end in keep for i in range(start, end)}
    control_columns = {i for start, end in control_keep for i in range(start, end)}
    if len(control_columns) != len(pinned_columns):
        raise AssertionError(
            f"pinned_control column mismatch: {len(control_columns)} != {len(pinned_columns)}"
        )
    if control_columns & pinned_columns:
        raise AssertionError("pinned_control overlaps pinned constraint columns")
    record = {
        "session": session,
        "key": key,
        "topic": topic,
        "n_turns": n_turns,
        "evict_range": list(evict_range),
        "keep": [list(span) for span in keep],
        "control_keep": [list(span) for span in control_keep],
        "n_aged": n_aged,
        "history_token_ids": list(history_token_ids),
        "context_token_ids": list(context_token_ids),
        "arms": arms,
    }
    if any("generated_token_ids" not in branch for branch in arms.values()):
        raise AssertionError("every arm must record generated_token_ids")
    return record


def _percentile(sorted_values, q):
    if not sorted_values:
        return None
    index = (len(sorted_values) - 1) * q
    lower = int(index)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = index - lower
    return sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight


def paired_bootstrap_pinned_minus_control(records, *, n_resamples=2000, seed=0):
    """Session-paired percentile bootstrap of pinned minus exact control."""
    diffs = []
    for record in records:
        n = record["arms"]["pinned"]["aged_n"]
        pinned = record["arms"]["pinned"]["scores"][:n]
        control = record["arms"]["pinned_control"]["scores"][:n]
        if len(pinned) != len(control) or not pinned:
            raise ValueError("paired non-empty aged score vectors required")
        diffs.append(sum(float(a) - float(b) for a, b in zip(pinned, control, strict=True)) / len(pinned))
    if not diffs:
        return {"mean": None, "lower": None, "upper": None, "n_sessions": 0,
                "confidence": 0.95, "resamples": n_resamples, "seed": seed}
    rng = random.Random(seed)
    draws = sorted(sum(diffs[rng.randrange(len(diffs))] for _ in diffs) / len(diffs)
                   for _ in range(n_resamples))
    return {
        "mean": sum(diffs) / len(diffs),
        "lower": _percentile(draws, 0.025),
        "upper": _percentile(draws, 0.975),
        "n_sessions": len(diffs),
        "confidence": 0.95,
        "resamples": n_resamples,
        "seed": seed,
        "unit": "session",
    }

def main():
    determinism.assert_gpu_free_or_owned()
    args = parse_args()
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
    doses = tuple(args.dose)
    arms_registered = arm_names(doses)
    meta = build_meta(
        doses=doses,
        max_new=args.max_new,
        deadline=args.deadline,
        artifact_hashes={
            "corpus": str(data_path.relative_to(ROOT)),
            "corpus_sha256": sha(data_path),
            "model_sha256": sha(model_path),
            "qwen3_sha256": sha(ROOT / "src/stencil/qwen3.py"),
        },
    )
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
        history_ids = tok.encode(history).ids
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
        pinned_count = len({i for start, end in keep for i in range(start, end)})
        control_count = len({i for start, end in control_keep for i in range(start, end)})
        assert control_count == pinned_count, f"session {si}: control {control_count} != pinned {pinned_count}"
        row = {"key": int(sess["key"]) * 10 + T_last,
               "instruction_id_list": last["instruction_id_list"], "kwargs": last["kwargs"]}
        # aged constraints = those whose clause originates in an earlier turn;
        # map by order: the corpus lists are cumulative in introduction order
        n_aged = sum(1 for r in recs if r["origin_turn"] < T_last)
        arms = {}
        for arm in arms_registered:
            dose = float(arm.rsplit("_d", 1)[1]) if arm.startswith("pinned_wave_d") else 0.0
            g = run_arm(m, tok, ids, arm, keep, evict_range, dose, args.max_new, args.deadline, control_keep=control_keep)
            g["degenerate"] = is_degenerate(g)
            scores = score_row_constraints(row, g["text"])
            g["scores"] = list(scores)
            g["aged_pass"] = sum(scores[:n_aged])
            g["aged_n"] = n_aged
            arms[arm] = g
        assert arms["pinned"]["pinned_cols"] == arms["pinned_control"]["pinned_cols"]
        rec = session_record(
            session=si, key=sess["key"], topic=sess["topic"], n_turns=T_last,
            evict_range=evict_range, keep=keep, control_keep=control_keep, n_aged=n_aged,
            history_token_ids=history_ids, context_token_ids=ids, arms=arms,
        )
        rec["context_tokens"] = len(ids)
        atomic_json(rp, rec)
        print(f"session {si} aged={n_aged} " + " ".join(f"{a}={arms[a]['aged_pass']}/{n_aged}(rep4={arms[a]['rep4']:.2f},n={arms[a]['n']})" for a in arms_registered), flush=True)

    records = [json.loads(p.read_text()) for p in sorted(outdir.glob("session-*.json"))]
    summ = {**meta, "sessions": len(records)}
    for a in arms_registered:
        p = sum(r["arms"][a]["aged_pass"] for r in records); n = sum(r["n_aged"] for r in records)
        summ[a] = {"aged_pass": p, "aged_n": n, "rate": p / max(1, n),
                   "trunc": sum(r["arms"][a]["truncated"] for r in records),
                   "timeout": sum(r["arms"][a]["timed_out"] for r in records),
                   "mean_rep4": sum(r["arms"][a]["rep4"] for r in records) / max(1, len(records)),
                   "degenerate": sum(is_degenerate(r["arms"][a]) for r in records)}
    gap = summ["full"]["rate"] - summ["evicted"]["rate"]
    summ["gap_full_minus_evicted"] = gap
    summ["recovered_frac_pinned"] = (summ["pinned"]["rate"] - summ["evicted"]["rate"]) / gap if gap > 0 else None
    wave_arms = [a for a in arms_registered if a.startswith("pinned_wave_d")]
    best_wave = max(wave_arms, key=lambda a: (summ[a]["rate"], -summ[a]["degenerate"]))
    summ["wave_best_dose_arm"] = best_wave
    summ["wave_killed"] = summ[best_wave]["degenerate"] > 2
    summ["recovered_frac_pinned_wave_best_dose"] = (summ[best_wave]["rate"] - summ["evicted"]["rate"]) / gap if gap > 0 else None
    summ["paired_bootstrap_pinned_minus_control"] = paired_bootstrap_pinned_minus_control(records)
    atomic_json(outdir / "summary.json", summ)
    print(json.dumps({k: v for k, v in summ.items() if k in arms_registered or k.startswith(("gap", "recovered", "paired", "wave_"))}, indent=1))

if __name__ == "__main__":
    main()
