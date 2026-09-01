# ruff: noqa
"""E2 causal-moment harvest on SYNTHETIC multi-turn sessions
(EVF-PLAN E2; the gate NEVER trains on Multi-IF content).

For each synthetic session (data/b3/mt-train-300.jsonl):
  * roll turns 1..3 natively (gate silent) building the session history,
    capturing CTRB trajectory features at every step of the LATER turns
    (the aging regime the headroom map identifies);
  * pick the highest-conflict eligible moments in turns 2-3;
  * at each, branch A=0 (native) vs A=1 (one registered burst) and roll
    both to the turn's end; score the CUMULATIVE constraints with the
    vendored checkers; label helpful/harmful/neutral by utility delta.

Atomic per-moment records from the first row (playbook). Resumable.
"""
import argparse, json, hashlib, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--sessions", type=int, default=120)
    p.add_argument("--per-turn-moments", type=int, default=2)
    p.add_argument("--turn-max-new", type=int, default=320)
    p.add_argument("--deadline", type=float, default=300.0)
    p.add_argument("--out", default="e2-moments")
    return p.parse_args()


OPENER = "<|im_start|>assistant\n<think>\n\n</think>\n\n"


def main():
    args = parse_args()
    import torch
    from tokenizers import Tokenizer

    from stencil.causal_moments import label_causal_moment, score_row_constraints
    from stencil.ctrb import HazardGate, constraint_spans_in_context, generate_ctrb
    from stencil.qwen3 import Qwen3
    from stencil.wave import WaveController

    tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
    m = Qwen3()
    m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
    m = m.to(torch.bfloat16).cuda().eval()
    ctrl = WaveController(beta_max=1.0).cuda()
    ctrl.load_state_dict(torch.load(ROOT / "results" / "qwen" / "b3-ce-s0.pt", map_location="cpu"))
    ctrl = ctrl.eval()

    sessions = [json.loads(line) for line in open(ROOT / "data" / "b3" / "mt-train-300.jsonl")]
    sessions = sessions[: args.sessions]
    outdir = ROOT / "results" / "qwen" / args.out
    outdir.mkdir(parents=True, exist_ok=True)
    meta = {"corpus": "mt-train-300.jsonl",
            "corpus_sha256": hashlib.sha256((ROOT / "data" / "b3" / "mt-train-300.jsonl").read_bytes()).hexdigest(),
            "ctrl_sha256": hashlib.sha256((ROOT / "results" / "qwen" / "b3-ce-s0.pt").read_bytes()).hexdigest(),
            "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "sessions": args.sessions, "per_turn_moments": args.per_turn_moments}
    meta_p = outdir / "meta.json"
    if meta_p.exists():
        assert json.loads(meta_p.read_text()) == meta, "resume provenance mismatch"
    else:
        tmp = meta_p.with_suffix(".tmp"); tmp.write_text(json.dumps(meta, indent=1)); tmp.rename(meta_p)

    silent = HazardGate.constant(0.0)
    t0 = time.time()
    n_moments = 0
    for si, sess in enumerate(sessions):
        done = sorted(outdir.glob(f"m-{si:04d}-*.json"))
        if done:
            n_moments += len(done)
            continue
        history = ""
        turn_texts = []
        for ti, turn in enumerate(sess["turns"]):
            # full conversation context for this turn
            history_now = history + f"<|im_start|>user\n{turn['prompt']}<|im_end|>\n"
            ctx = history_now + OPENER
            # FULL-CONTEXT coordinates (E2 retraction fix): every constraint
            # in the conversation is a candidate, so aged constraints from
            # earlier turns are selectable — the aging regime we target.
            spans = constraint_spans_in_context(tok, ctx)
            if not spans:
                break
            # native roll with feature trace (gate silent -> bitwise base)
            res = generate_ctrb(m, tok, ctx, ctrl, spans, silent,
                                max_new=args.turn_max_new, deadline_s=args.deadline,
                                draft_tokens=0, collect_prefixes=True, raw_context=True)
            turn_texts.append(res.text)
            history = history_now + f"<|im_start|>assistant\n{res.text}<|im_end|>\n"
            if ti == 0:
                continue  # aging regime lives in turns 2-3
            eligible = [r for r in res.trace if r["features"] is not None]
            if not eligible:
                continue
            eligible.sort(key=lambda r: -(r["features"][1] + r["features"][2]))
            picked = sorted(eligible[: args.per_turn_moments], key=lambda r: r["step"])
            row = {"key": sess["key"] * 10 + ti,
                   "instruction_id_list": turn["instruction_id_list"],
                   "kwargs": turn["kwargs"]}
            for rec in picked:
                lab = label_causal_moment(
                    model=m, tokenizer=tok, prompt=ctx, prefix_ids=rec["prefix_ids"],
                    selected_span=tuple(spans[rec["selected_span"]]),
                    score_fn=lambda text: score_row_constraints(row, text),
                    max_new=args.turn_max_new, deadline_s=args.deadline,
                    raw_context=True)
                out = {"session": si, "turn": ti + 1, "step": rec["step"],
                       "features": list(rec["features"]), "span": list(spans[rec["selected_span"]]),
                       "label": lab.label, "utility_delta": lab.utility_delta,
                       "native_scores": list(lab.native_scores),
                       "burst_scores": list(lab.burst_scores),
                       "combo": turn["combo"], "topic": sess["topic"],
                       "new_combo": turn["new_combo"]}
                p = outdir / f"m-{si:04d}-{ti+1}-{rec['step']:04d}.json"
                tmp = p.with_suffix(".tmp"); tmp.write_text(json.dumps(out, ensure_ascii=False)); tmp.rename(p)
                n_moments += 1
        if si % 5 == 0:
            print(f"session {si}/{len(sessions)} moments={n_moments} ({time.time()-t0:.0f}s)", flush=True)
    labs = [json.loads(p.read_text())["label"] for p in outdir.glob("m-*.json")]
    from collections import Counter
    print(json.dumps({"moments": len(labs), "labels": dict(Counter(labs))}, indent=1))


if __name__ == "__main__":
    main()
