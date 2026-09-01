# ruff: noqa
"""Multi-IF replayed-history evaluation of the OBLIGATION-STATE gate.

Reuses sol's frozen replay harness (identical replayed base histories,
silent-equals-base assertions, diagnostic-slice separation) and swaps
the policy for the deterministic obligation gate (src/stencil/
obligation_gate.py) — no hazard model, no training.

ARMS (frozen before any Multi-IF contact):
  obligation      : the R3b rule (outstanding fixable family, no live
                    word cap, past the position floor) -> sustained
                    bias over all user-turn instruction spans.
  specificity     : identical FIRING SCHEDULE, but the bias lands on
                    mass-matched NON-instruction tokens. The treatment
                    must beat this or the effect is generic perturbation.
  positive_control: aged instructions restated verbatim in the replayed
                    history (bounds what focus recovery could ever give).
ENDPOINTS: per-constraint paired exact McNemar on (a) FRESH constraints
(introduced this turn) and (b) AGED constraints, plus the all-constraint
net co-reported under the same floor so a fresh gain cannot hide aged
loss; conversation-cluster bootstrap alongside; length/truncation and
firing-rate controls recorded per arm.
"""
import argparse, hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="e2-obligation-replay")
    p.add_argument("--conversations", type=int, default=0, help="0 = all")
    p.add_argument("--diagnostic-only", action="store_true",
                   help="restrict to the disclosed diagnostic slice (primary claim untouched)")
    p.add_argument("--deadline", type=float, default=300.0)
    return p.parse_args()


def atomic_json(path, value):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=1))
    tmp.rename(path)


def main():
    args = parse_args()
    import torch
    from tokenizers import Tokenizer

    import langdetect
    langdetect.DetectorFactory.seed = 0

    from stencil.bench import MAX_NEW
    from stencil.e2 import mass_matched_nonconstraint_control, user_turn_span_records
    from stencil.e2_multiif import (
        base_branch, build_replay_context, is_diagnostic_key, score_turn, turn_doc,
    )
    from stencil.obligation_gate import generate_gated
    from stencil.qwen3 import Qwen3

    tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
    m = Qwen3()
    m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
    m = m.to(torch.bfloat16).cuda().eval()

    rows = [json.loads(line) for line in open(ROOT / "data" / "bench" / "multiif_en.jsonl")]
    base_dir = ROOT / "results" / "qwen" / "b4-multiif-base"
    outdir = ROOT / "results" / "qwen" / args.out
    outdir.mkdir(parents=True, exist_ok=True)

    meta = {
        "policy": "obligation_gate_R3b",
        "gate_sha256": hashlib.sha256((ROOT / "src" / "stencil" / "obligation_gate.py").read_bytes()).hexdigest(),
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "data_sha256": hashlib.sha256((ROOT / "data" / "bench" / "multiif_en.jsonl").read_bytes()).hexdigest(),
        "trunk_sha256": hashlib.sha256((ROOT / "models" / "qwen3-1.7b.pt").read_bytes()).hexdigest(),
        "arms": ["obligation", "specificity", "positive_control"],
        "diagnostic_only": bool(args.diagnostic_only),
    }
    meta_p = outdir / "meta.json"
    if meta_p.exists():
        assert json.loads(meta_p.read_text()) == meta, "resume provenance mismatch"
    else:
        atomic_json(meta_p, meta)

    todo = []
    for ci, row in enumerate(rows):
        diag = is_diagnostic_key(row["key"])
        if args.diagnostic_only and not diag:
            continue
        todo.append((ci, row))
    if args.conversations:
        todo = todo[: args.conversations]
    print(f"conversations to evaluate: {len(todo)}", flush=True)

    for n, (ci, row) in enumerate(todo):
        rec_p = outdir / f"conv-{ci:03d}.json"
        if rec_p.exists():
            continue
        base_record = json.loads((base_dir / f"conv-{ci:03d}.json").read_text())
        present = [t for t in (1, 2, 3) if row[f"turn_{t}_prompt"]]
        prompts = [turn_doc(row, t)[0] for t in present]
        base_responses = [base_record["responses"][str(t)] for t in present]
        turns = {}
        for turn in [v for v in present if v >= 2]:
            context = build_replay_context(prompts, base_responses, turn=turn,
                                           positive_control=False)
            spans = [tuple(r["span"]) for r in user_turn_span_records(tok, context)]
            base = base_branch(base_record, turn)
            _, prev_ids, _ = turn_doc(row, turn - 1)
            _, cur_ids, cur_kwargs = turn_doc(row, turn)
            scoring_row = {"key": row["key"], "instruction_id_list": cur_ids,
                           "kwargs": cur_kwargs}
            expected = base_record["gen"][str(turn - 1)]["n"]

            gated = generate_gated(m, tok, context, scoring_row, spans=spans,
                                   expected_total=expected, max_new=MAX_NEW,
                                   deadline_s=args.deadline, raw_context=True)
            if not gated.fired and gated.text != base["response"]:
                raise RuntimeError(f"conv {ci} turn {turn}: silent gate differs from base")

            ctrl_spans, ctrl_dose = mass_matched_nonconstraint_control(
                total_len=len(tok.encode(context).ids),
                spans=[tuple(s) for s in spans], target_dose=3.0)
            spec = generate_gated(m, tok, context, scoring_row,
                                  spans=[tuple(s) for s in ctrl_spans],
                                  dose=ctrl_dose, expected_total=expected,
                                  max_new=MAX_NEW, deadline_s=args.deadline,
                                  raw_context=True)

            pos_ctx = build_replay_context(prompts, base_responses, turn=turn,
                                           positive_control=True)
            pos_spans = [tuple(r["span"]) for r in user_turn_span_records(tok, pos_ctx)]
            positive = generate_gated(m, tok, pos_ctx, scoring_row, spans=pos_spans,
                                      expected_total=expected, max_new=MAX_NEW,
                                      deadline_s=args.deadline,
                                      raw_context=True, position_floor=2.0)  # native

            def branch(g):
                sc = score_turn(row, turn, g.text)
                return {"scores": list(sc["inst_level_strict_acc"]),
                        "strict": bool(sc["prompt_level_strict_acc"]),
                        "n_generated": g.n_generated, "truncated": bool(g.truncated),
                        "timed_out": bool(g.timed_out), "fired": bool(g.fired),
                        "fire_step": g.fire_step,
                        "decisions": g.decisions[:40], "response": g.text}

            turns[str(turn)] = {
                "aged_count": len(prev_ids), "n_constraints": len(cur_ids),
                "base": base,
                "arms": {"obligation": branch(gated), "specificity": branch(spec),
                         "positive_control": branch(positive)},
            }
        atomic_json(rec_p, {"ci": ci, "key": row["key"],
                            "diagnostic": is_diagnostic_key(row["key"]), "turns": turns})
        if n % 10 == 0:
            print(f"eval {n + 1}/{len(todo)} (conv {ci})", flush=True)
    print("OBLIGATION EVAL COMPLETE", flush=True)


if __name__ == "__main__":
    main()
