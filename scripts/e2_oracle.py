# ruff: noqa
"""THE DECISIVE WHEN TEST (Brian, 2026-09-01): the ORACLE-TIMING ceiling.

For each held-out synthetic multi-turn session (mt-dev-60, dev topics,
never trained on): roll turns natively; find turn-3 constraints that
FAIL natively (headroom); then try a burst at MANY candidate moments
spanning the generation, rolling each to completion. Ask the only
question that matters before building a WHEN learner:

    does ANY moment's burst fix a natively-failing constraint?

max over moments = the ORACLE ceiling a perfect gate could reach.
If oracle ~= native, no timing policy can help and the line closes.
Also sweeps DOSE (registered 1.0 vs stronger 3.0) so a null cannot be
blamed on a too-timid actuator.

Atomic per-item records. Read-only on frozen data.
"""
import argparse, json, hashlib, random, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401

OPENER = "<|im_start|>assistant\n<think>\n\n</think>\n\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sessions", type=int, default=20)
    ap.add_argument("--moments", type=int, default=10, help="candidate burst moments per item")
    ap.add_argument("--doses", default="1.0,3.0")
    ap.add_argument("--arms", default="reg,sustained_all,sustained_aged,control",
                    help="reg=4-tok burst learned span; sustained_all=every step, ALL live constraint spans (Opus winning arm); sustained_aged=every step, aged spans; control=non-constraint tokens matched width/schedule")
    ap.add_argument("--burst-tokens", type=int, default=4)
    ap.add_argument("--turn-max-new", type=int, default=320)
    ap.add_argument("--out", default="e2-oracle")
    args = ap.parse_args()
    doses = [float(x) for x in args.doses.split(",")]

    import torch
    from tokenizers import Tokenizer

    from stencil.causal_moments import rollout_from_prefix, score_row_constraints
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

    sessions = [json.loads(l) for l in open(ROOT / "data" / "b3" / "mt-dev-60.jsonl")][: args.sessions]
    outdir = ROOT / "results" / "qwen" / args.out
    outdir.mkdir(parents=True, exist_ok=True)
    silent = HazardGate.constant(0.0)
    t0 = time.time()

    for si, sess in enumerate(sessions):
        rec_p = outdir / f"s-{si:03d}.json"
        if rec_p.exists():
            continue
        history, ctx, spans, res = "", None, None, None
        turn_records = []
        for ti, turn in enumerate(sess["turns"]):
            ctx = history + f"<|im_start|>user\n{turn['prompt']}<|im_end|>\n" + OPENER
            spans = constraint_spans_in_context(tok, ctx)
            res = generate_ctrb(m, tok, ctx, ctrl, spans, silent, max_new=args.turn_max_new,
                                draft_tokens=0, collect_prefixes=True, raw_context=True)
            history = ctx[: -len(OPENER)] + f"<|im_start|>assistant\n{res.text}<|im_end|>\n"
            turn_records.append((ti, turn, ctx, spans, res))
        # oracle test on the FINAL turn (deepest aging)
        ti, turn, ctx, spans, res = turn_records[-1]
        row = {"key": sess["key"], "instruction_id_list": turn["instruction_id_list"],
               "kwargs": turn["kwargs"]}
        native = score_row_constraints(row, res.text)
        failing = [i for i, ok in enumerate(native) if not ok]
        out = {"session": si, "turn": ti + 1, "n_constraints": len(native),
               "native_scores": list(native), "failing_idx": failing,
               "n_gen": res.n_generated, "trials": []}
        if failing:
            eligible = [r for r in res.trace if r["features"] is not None]
            if eligible:
                # candidates spanning the generation + the conflict-top ones
                idx = sorted({round(k * (len(eligible) - 1) / max(1, args.moments - 1))
                              for k in range(args.moments)})
                cands = [eligible[i] for i in idx]
                top = sorted(eligible, key=lambda r: -(r["features"][1] + r["features"][2]))[:3]
                for r in top:
                    if r not in cands:
                        cands.append(r)
                arms = args.arms.split(",")
                n_ctx = len(tok.encode(ctx).ids)
                # aged spans = constraints stated before the final user turn
                last_user = ctx.rfind("<|im_start|>user")
                cut_tok = len(tok.encode(ctx[:last_user]).ids) if last_user > 0 else 0
                aged = [sp for sp in spans if sp[1] <= cut_tok] or spans[:1]
                # control: non-constraint window of matched total width
                width = sum(b - a for a, b in spans)
                ctrl_start = max(0, cut_tok - width - 8)
                control = [(ctrl_start, ctrl_start + width)] if ctrl_start > 0 else []
                for rec in cands:
                    for dose in doses:
                        for arm in arms:
                            if arm == "reg":
                                sel, steps = [tuple(spans[rec["selected_span"]])], args.burst_tokens
                            elif arm == "sustained_all":
                                sel, steps = [tuple(x) for x in spans], 10**6
                            elif arm == "sustained_aged":
                                sel, steps = [tuple(x) for x in aged], 10**6
                            elif arm == "control":
                                if not control:
                                    continue
                                sel, steps = [tuple(x) for x in control], 10**6
                            else:
                                continue
                            roll = rollout_from_prefix(
                                model=m, tokenizer=tok, prompt=ctx,
                                prefix_ids=rec["prefix_ids"], selected_span=sel[0],
                                extra_spans=sel[1:], burst=True, dose=dose,
                                burst_tokens=steps, max_new=args.turn_max_new,
                                raw_context=True)
                            sc = score_row_constraints(row, roll.response)
                            out["trials"].append({"step": rec["step"], "arm": arm,
                                                  "dose": dose, "scores": list(sc),
                                                  "n_pass": sum(sc)})
        best = max([t["n_pass"] for t in out["trials"]], default=sum(native))
        out["native_pass"] = sum(native)
        out["oracle_best_pass"] = max(best, sum(native))
        out["oracle_gain"] = out["oracle_best_pass"] - out["native_pass"]
        tmp = rec_p.with_suffix(".tmp"); tmp.write_text(json.dumps(out, ensure_ascii=False)); tmp.rename(rec_p)
        print(f"s{si}: native {out['native_pass']}/{len(native)} oracle {out['oracle_best_pass']} "
              f"gain +{out['oracle_gain']} trials={len(out['trials'])} ({time.time()-t0:.0f}s)", flush=True)

    from stencil.e2 import summarize_oracle_records
    recs = [json.loads(p.read_text()) for p in sorted(outdir.glob("s-*.json"))]
    summary = summarize_oracle_records(recs, args.arms.split(","))
    (ROOT / "results" / "qwen" / f"{args.out}-summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
