"""Exp 2a: wave utilization screen on fresh episodes (plan/BACK-ON-TRACK-PLAN.md).

Five arms on identical prompts (correct live ledger supplied every request):
  base                 no intervention
  prose                oracle current-rule restatement ("(Reminder) ..." as the sealed
                       reinsertion arm, t2_runner.build_arm_prompt)
  fixed_bias           beta=2 peak-normalised pre-softmax bias on ALL live ledger
                       sentence spans at every step, layers 20-27 (fixed-bias baseline
                       in the PASTA/SpotLight family; not a reproduction of SpotLight)
  wave                 results/qwen/w0-ce.pt continuous field
  wave_where_shuffled  the wave field computed exactly as `wave`, then permuted across
                       all P prompt positions by a permutation fixed per (episode, work)
                       (removes WHERE, keeps WHEN and dose)

Evaluator: ONE full-prefix forward per generated token; the layer-20 features feed the
controller through `bias_hook` inside the same pass (the sealed evaluator ran two
passes per token). `--qualify` compares the two paths on 8 dev sessions.

Primary estimand: per-episode joint success (every active opportunity adherent AND
reference tests pass on three frozen inputs, `score_work_multi`). Contrasts: wave vs
prose, wave vs fixed_bias, wave vs wave_where_shuffled; exact McNemar, Holm over 3.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

ARMS = ("base", "prose", "fixed_bias", "wave", "wave_where_shuffled")
CONTRASTS = (("wave", "prose"), ("wave", "fixed_bias"), ("wave", "wave_where_shuffled"))
SEED0 = 14_700_000
SPLIT = "final"
NEUTRAL = "[checker] (no feedback available this session)"
FEEDBACK_SLOT = (
    "[checker] (deterministic feedback on the previous submission is inserted "
    "here at run time)"
)
BETA_FIXED = 2.0
MAX_NEW = 120
BREAKAGE_LIMIT = 0.05
CKPT = ROOT / "results" / "qwen" / "w0-ce.pt"


def load_stack():
    import torch
    from tokenizers import Tokenizer

    from stencil import determinism
    from stencil.qwen3 import Qwen3
    from stencil.wave import WaveController

    determinism.assert_gpu_free_or_owned()
    tok = Tokenizer.from_file(str(ROOT / "models/qwen3-1.7b-hf/tokenizer.json"))
    m = Qwen3()
    m.load_state_dict(
        torch.load(
            ROOT / "models/qwen3-1.7b.pt", map_location="cpu", weights_only=True
        ),
        strict=True,
    )
    m = m.to(torch.bfloat16).cuda().eval()
    ctrl = WaveController().cuda()
    ctrl.load_state_dict(torch.load(CKPT, map_location="cpu", weights_only=True))
    return tok, m, ctrl.eval()


def _prompt(sess, wt, split, arm):
    from stencil.t2_runner import build_arm_prompt

    ptxt = build_arm_prompt(
        sess, wt, split, "reinsertion" if arm == "prose" else "base"
    )
    return ptxt.replace(FEEDBACK_SLOT, NEUTRAL)


def _fixed_row(spans, P):
    import torch

    e = torch.full((P,), -6.0)
    for start, end in spans.values():
        e[start:end] = 6.0
    sm = torch.softmax(e, dim=-1)
    return (BETA_FIXED * sm / sm.max()).cuda()


def generate(m, tok, ctrl, sess, wt, split, arm, *, two_pass=False, perm_seed=None):
    """One work turn under one arm. Returns (code, gains, logit_trace)."""
    import torch

    from stencil.t2_runner import LAYERS, ledger_sentence_spans

    ptxt = _prompt(sess, wt, split, arm)
    enc = tok.encode(ptxt)
    P = len(enc.ids)
    toks = torch.tensor([enc.ids], device="cuda")
    spans = (
        ledger_sentence_spans(ptxt, sess, wt, split, tok) if arm == "fixed_bias" else {}
    )
    fixed_row = _fixed_row(spans, P) if arm == "fixed_bias" and spans else None
    perm = None
    if arm == "wave_where_shuffled":
        g = torch.Generator().manual_seed(int(perm_seed))
        perm = torch.randperm(P, generator=g).cuda()
    gen, text, gains, trace = [], "", [], []
    K_two = None
    with torch.no_grad():
        if two_pass and arm in ("wave", "wave_where_shuffled"):
            K_two = m(toks, return_hidden=20)[0].float()[:P]
        for _ in range(MAX_NEW):
            t = toks.shape[1]
            hook = None
            ab = None
            if arm == "fixed_bias" and fixed_row is not None:
                bias = torch.zeros(t, t, device="cuda")
                bias[-1, :P] = fixed_row
                ab = {L: bias for L in LAYERS}
            elif arm in ("wave", "wave_where_shuffled"):
                if two_pass:
                    h_t = m(toks, return_hidden=20)[0, -1].float()
                    row = ctrl(h_t, K_two)
                    if perm is not None:
                        row = row[perm]
                    gains.append(float(row.max()))
                    bias = torch.zeros(t, t, device="cuda")
                    bias[-1, :P] = row
                    ab = {L: bias for L in LAYERS}
                else:

                    def _hook(x, _P=P, _perm=perm, _t=t):
                        h = x[0].float()
                        row = ctrl(h[-1], h[:_P])
                        if _perm is not None:
                            row = row[_perm]
                        gains.append(float(row.max()))
                        bias = torch.zeros(_t, _t, device="cuda")
                        bias[-1, :_P] = row
                        return {L: bias for L in LAYERS}

                    hook = (20, _hook)
            logits = m(toks, attn_bias=ab, bias_hook=hook)[0, -1]
            trace.append(logits.float().cpu())
            nxt = int(logits.argmax())
            gen.append(nxt)
            toks = torch.cat([toks, torch.tensor([[nxt]], device="cuda")], dim=1)
            text = tok.decode(gen)
            if "```" in text[-6:]:
                break
    return text.split("```")[0], gains, trace


def episode_record(m, tok, ctrl, seed, split, arms, works):
    from stencil.t2_runner import score_work_multi
    from stencil.t2_sessions import generate_t2

    sess = generate_t2(seed, 20, split, interference="s0")
    turns = sess.work_turns if works == "all" else sess.work_turns[:2]
    record = {"seed": seed, "split": split, "work_turns": turns, "arms": {}}
    for arm in arms:
        arm_rec = {"works": {}, "joint_success": True, "gains": []}
        for wt in turns:
            code, gains, _ = generate(
                m, tok, ctrl, sess, wt, split, arm, perm_seed=seed * 100 + wt
            )
            wr = score_work_multi(code, sess, wt)
            active = [
                o for o in sess.opportunities if o.turn == wt and o.cell == "active"
            ]
            adherent = [
                bool(wr.per_opportunity.get(o.opportunity_id, {}).get("adherent"))
                for o in active
            ]
            arm_rec["works"][str(wt)] = {
                "code": code,
                "code_sha16": hashlib.sha256(code.encode()).hexdigest()[:16],
                "parse": wr.parse,
                "exec_ok": wr.exec_ok,
                "active_types": [o.moment_class for o in active],
                "adherent": adherent,
                "per_opportunity": wr.per_opportunity,
            }
            arm_rec["gains"] += gains
            if not (wr.parse and wr.exec_ok and all(adherent)):
                arm_rec["joint_success"] = False
        record["arms"][arm] = arm_rec
    return record


def _mcnemar(pairs):
    from scipy.stats import binomtest

    b = sum(1 for a, c in pairs if a and not c)  # first wins
    c = sum(1 for a, c in pairs if c and not a)  # second wins
    p = binomtest(b, b + c, 0.5, alternative="two-sided").pvalue if b + c else 1.0
    p_one = binomtest(b, b + c, 0.5, alternative="greater").pvalue if b + c else 1.0
    return {
        "first_only": b,
        "second_only": c,
        "p_two_sided": float(p),
        "p_one_sided": float(p_one),
    }


def _holm(pvalues: dict, alpha=0.05) -> dict:
    ordered = sorted(pvalues, key=lambda k: pvalues[k])
    out, ok = {}, True
    for rank, name in enumerate(ordered):
        cutoff = alpha / (len(ordered) - rank)
        ok = bool(ok and float(pvalues[name]) <= cutoff)
        out[name] = {"p": float(pvalues[name]), "cutoff": cutoff, "passed": ok}
    return out


def summarize(outdir: Path) -> dict:
    import numpy as np

    records = [json.loads(p.read_text()) for p in sorted(outdir.glob("ep-*.json"))]
    n = len(records)
    arms = [a for a in ARMS if all(a in r["arms"] for r in records)]
    joint = {a: [r["arms"][a]["joint_success"] for r in records] for a in arms}
    adherence = {}
    for a in arms:
        vals = []
        for r in records:
            bits = [b for w in r["arms"][a]["works"].values() for b in w["adherent"]]
            vals.append(100.0 * sum(bits) / len(bits) if bits else 0.0)
        adherence[a] = vals
    rng = np.random.default_rng(0)

    def boot(diffs):
        arr = np.asarray(diffs)
        means = [arr[rng.integers(0, len(arr), len(arr))].mean() for _ in range(10_000)]
        return {
            "mean": float(arr.mean()),
            "ci95": [
                float(np.percentile(means, 2.5)),
                float(np.percentile(means, 97.5)),
            ],
        }

    contrasts = {}
    for a, b in CONTRASTS:
        if a in joint and b in joint:
            key = f"{a}_vs_{b}"
            contrasts[key] = {
                "joint": _mcnemar(list(zip(joint[a], joint[b], strict=True))),
                "adherence_points": boot(
                    [x - y for x, y in zip(adherence[a], adherence[b], strict=True)]
                ),
            }
    holm = _holm({k: v["joint"]["p_one_sided"] for k, v in contrasts.items()})
    breakage = {}
    if "base" in arms:
        base_works = {
            (r["seed"], wt): w
            for r in records
            for wt, w in r["arms"]["base"]["works"].items()
        }
        for a in arms:
            if a == "base":
                continue
            broken = 0
            for r in records:
                for wt, w in r["arms"][a]["works"].items():
                    bw = base_works[(r["seed"], wt)]
                    if (bw["parse"] and not w["parse"]) or (
                        bw["exec_ok"] and not w["exec_ok"]
                    ):
                        broken += 1
            breakage[a] = {
                "paired_broken": broken,
                "works": len(base_works),
                "fraction": broken / max(1, len(base_works)),
            }
    all_pass = bool(holm) and all(v["passed"] for v in holm.values())
    wave_break_ok = breakage.get("wave", {}).get("fraction", 1.0) <= BREAKAGE_LIMIT
    if all_pass and wave_break_ok:
        verdict = (
            "PASS: all three contrasts positive at Holm-adjusted p<=.05 "
            "and breakage within limit"
        )
    elif (
        "wave_vs_wave_where_shuffled" in holm
        and not holm["wave_vs_wave_where_shuffled"]["passed"]
    ):
        verdict = (
            "NOT-DEMONSTRATED-WHERE: spatial contribution not demonstrated; "
            "no further wave spend"
        )
    elif any(
        k in holm and not holm[k]["passed"]
        for k in ("wave_vs_prose", "wave_vs_fixed_bias")
    ):
        verdict = (
            "NOT-DEMONSTRATED-BASELINE: advantage over the tested baselines "
            "not demonstrated; "
            "no further wave spend"
        )
    else:
        verdict = "INSUFFICIENT EVIDENCE: descriptive only; no further wave spend"
    if all_pass and not wave_break_ok:
        verdict = "NOT PASS: contrasts positive but breakage exceeds the 5% limit"
    harm = [k for k, v in contrasts.items() if v["adherence_points"]["ci95"][1] < 0]
    summary = {
        "n_episodes": n,
        "arms": arms,
        "joint_success": {a: sum(v) for a, v in joint.items()},
        "mean_adherence_points": {a: float(np.mean(v)) for a, v in adherence.items()},
        "contrasts": contrasts,
        "holm": holm,
        "breakage_excess_over_base": breakage,
        "demonstrated_harm_contrasts": harm,
        "verdict": verdict,
        "competence_harm_disclosure": (
            "w0-ce reduced MMLU 48.05->45.83 (175 degradations / 57 improvements) and "
            "failed GSM8K noninferiority (WORKLOG.md:1586,1613)"
        ),
    }
    (outdir / "summary.json").write_text(json.dumps(summary, indent=1))
    return summary


def qualify(m, tok, ctrl, outdir: Path) -> dict:
    """Single-pass vs two-pass evaluator on 8 dev sessions: logit drift + agreement."""
    import torch

    from stencil.t2_runner import score_work_multi
    from stencil.t2_sessions import generate_t2

    rows = []
    for seed in range(13_690_000, 13_690_008):
        sess = generate_t2(seed, 20, "dev", interference="s0")
        for wt in sess.work_turns:
            code_a, _, trace_a = generate(m, tok, ctrl, sess, wt, "dev", "wave")
            code_b, _, trace_b = generate(
                m, tok, ctrl, sess, wt, "dev", "wave", two_pass=True
            )
            steps = min(len(trace_a), len(trace_b))
            drift = (
                max(float((trace_a[i] - trace_b[i]).abs().max()) for i in range(steps))
                if steps
                else 0.0
            )
            wa, wb = (
                score_work_multi(code_a, sess, wt),
                score_work_multi(code_b, sess, wt),
            )
            rows.append(
                {
                    "seed": seed,
                    "wt": wt,
                    "identical_code": code_a == code_b,
                    "max_abs_logit_drift": drift,
                    "adherence_agree": wa.per_opportunity == wb.per_opportunity,
                    "exec_agree": wa.exec_ok == wb.exec_ok,
                }
            )
            print(json.dumps(rows[-1]), flush=True)
    report = {
        "n_works": len(rows),
        "identical_code": sum(r["identical_code"] for r in rows),
        "adherence_agree": sum(r["adherence_agree"] for r in rows),
        "max_abs_logit_drift": max(r["max_abs_logit_drift"] for r in rows),
        "coresident_note": "peak memory measured separately by timing_pilot",
        "rows": rows,
        "cuda_peak_allocated_gb": torch.cuda.max_memory_allocated() / 2**30,
    }
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "qualification.json").write_text(json.dumps(report, indent=1))
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=ROOT / "results" / "wave-screen")
    parser.add_argument("--arms", nargs="+", default=list(ARMS), choices=ARMS)
    parser.add_argument("--episodes", type=int, default=64)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--works", choices=["all", "first2"], default="all")
    parser.add_argument("--split", default=SPLIT)
    parser.add_argument("--qualify", action="store_true")
    parser.add_argument("--summarize", action="store_true")
    args = parser.parse_args(argv)
    if args.summarize:
        print(json.dumps(summarize(args.out), indent=1))
        return 0
    tok, m, ctrl = load_stack()
    if args.qualify:
        report = qualify(m, tok, ctrl, args.out)
        print(json.dumps({k: v for k, v in report.items() if k != "rows"}, indent=1))
        return 0
    args.out.mkdir(parents=True, exist_ok=True)
    seeds = [SEED0 + i for i in range(args.episodes)]
    stop = (
        len(seeds) if args.limit is None else min(len(seeds), args.start + args.limit)
    )
    for seed in seeds[args.start : stop]:
        path = args.out / f"ep-{seed}.json"
        if path.exists():
            continue
        started = time.monotonic()
        record = episode_record(m, tok, ctrl, seed, args.split, args.arms, args.works)
        record["seconds"] = time.monotonic() - started
        tmp = path.with_suffix(".partial")
        tmp.write_text(json.dumps(record, indent=1))
        tmp.replace(path)
        print(
            f"episode {seed}: "
            + " ".join(
                f"{a}={int(r['joint_success'])}" for a, r in record["arms"].items()
            )
            + f" seconds={record['seconds']:.1f}",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
