# ruff: noqa
"""Frozen one-shot E2 Multi-IF replayed-history evaluation."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="e2-multiif-replay")
    parser.add_argument("--deadline", type=float, default=300.0)
    return parser.parse_args()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def combined_sha(paths):
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.name.encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def atomic_json(path, value):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=1))
    tmp.rename(path)


def main():
    args = parse_args()
    import torch
    from tokenizers import Tokenizer

    sys.path.insert(0, str(ROOT / "vendor"))
    import langdetect

    langdetect.DetectorFactory.seed = 0

    from stencil.bench import MAX_NEW
    from stencil.ctrb import HazardGate
    from stencil.e2 import user_turn_span_records
    from stencil.e2_multiif import (
        analyze_replay_records,
        base_branch,
        build_replay_context,
        is_diagnostic_key,
        policy_branch,
        score_turn,
        turn_doc,
    )
    from stencil.e2_policy import generate_e2_policy
    from stencil.e2_stats import periodic_assignment
    from stencil.qwen3 import Qwen3
    from stencil.wave import WaveController

    freeze_path = ROOT / "results" / "qwen" / "e2-freeze.json"
    freeze = json.loads(freeze_path.read_text())
    if freeze.get("status") != "FROZEN_BEFORE_MULTIIF":
        raise RuntimeError("passing pre-evaluation freeze required")
    expected = {
        "eval_runner_sha256": sha(Path(__file__)),
        "multiif_module_sha256": sha(ROOT / "src" / "stencil" / "e2_multiif.py"),
        "policy_sha256": sha(ROOT / "src" / "stencil" / "e2_policy.py"),
        "stats_sha256": sha(ROOT / "src" / "stencil" / "e2_stats.py"),
    }
    for key, value in expected.items():
        if freeze.get(key) != value:
            raise RuntimeError(f"post-freeze code drift: {key}")

    gate_path = ROOT / freeze["gate_report"]
    gate_report = json.loads(gate_path.read_text())
    frozen_gate = gate_report["gate"]
    gate = HazardGate(
        tuple(frozen_gate["mean"]),
        tuple(frozen_gate["scale"]),
        tuple(frozen_gate["weights"]),
        float(frozen_gate["bias"]),
    )
    data_path = ROOT / "data" / "bench" / "multiif_en.jsonl"
    model_path = ROOT / "models" / "qwen3-1.7b.pt"
    controller_path = ROOT / "results" / "qwen" / "b3-ce-s0.pt"
    base_dir = ROOT / "results" / "qwen" / "b4-multiif-base"
    headroom_path = ROOT / "results" / "qwen" / "multiif-headroom-adjusted.json"
    if freeze.get("headroom_sha256") != sha(headroom_path):
        raise RuntimeError("post-freeze headroom artifact drift")
    if freeze.get("multiif_data_sha256") != sha(data_path):
        raise RuntimeError("post-freeze Multi-IF data drift")
    manifest = json.loads((ROOT / "data" / "bench" / "pins-manifest.json").read_text())
    if sha(data_path) != manifest["converted_sha256"]["multiif_en.jsonl"]:
        raise RuntimeError("Multi-IF data provenance mismatch")
    rows = [json.loads(line) for line in data_path.read_text().splitlines()]
    if len(rows) != 909:
        raise RuntimeError("registered Multi-IF cohort must contain 909 conversations")
    base_paths = [base_dir / f"conv-{i:03d}.json" for i in range(909)]
    base_records = [json.loads(path.read_text()) for path in base_paths]
    if any(record["ci"] != i for i, record in enumerate(base_records)):
        raise RuntimeError("base record order mismatch")

    outdir = ROOT / "results" / "qwen" / args.out
    outdir.mkdir(parents=True, exist_ok=True)
    meta = {
        "schema": 1,
        "freeze_sha256": sha(freeze_path),
        "data_sha256": sha(data_path),
        "base_records_sha256": combined_sha(base_paths),
        "headroom_sha256": sha(headroom_path),
        "model_sha256": sha(model_path),
        "controller_sha256": sha(controller_path),
        **expected,
        "conversations": 909,
        "primary_conversations": sum(not is_diagnostic_key(row["key"]) for row in rows),
        "diagnostic_conversations": sum(is_diagnostic_key(row["key"]) for row in rows),
        "max_new": MAX_NEW,
        "deadline": args.deadline,
        "arms": ["ctrb", "periodic", "fixed_oldest", "positive_control"],
    }
    meta_path = outdir / "meta.json"
    if meta_path.exists():
        if json.loads(meta_path.read_text()) != meta:
            raise RuntimeError("evaluation resume provenance mismatch")
    else:
        atomic_json(meta_path, meta)

    tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
    model = Qwen3()
    model.load_state_dict(torch.load(model_path, map_location="cpu"), strict=True)
    model = model.to(torch.bfloat16).cuda().eval()
    ctrl = WaveController(beta_max=1.0).cuda()
    ctrl.load_state_dict(torch.load(controller_path, map_location="cpu"))
    ctrl = ctrl.eval()

    for ci, (row, base_record) in enumerate(zip(rows, base_records, strict=True)):
        record_path = outdir / f"conv-{ci:03d}.json"
        if record_path.exists():
            continue
        present = [turn for turn in (1, 2, 3) if row[f"turn_{turn}_prompt"]]
        prompts = [turn_doc(row, turn)[0] for turn in present]
        base_responses = [base_record["responses"][str(turn)] for turn in present]
        turns = {}
        for turn in [value for value in present if value >= 2]:
            context = build_replay_context(
                prompts, base_responses, turn=turn, positive_control=False
            )
            span_records = user_turn_span_records(tok, context)
            base = base_branch(base_record, turn)
            _, previous_ids, _ = turn_doc(row, turn - 1)
            _, current_ids, _ = turn_doc(row, turn)
            if current_ids[: len(previous_ids)] != previous_ids:
                raise RuntimeError("cumulative instruction order changed")

            ctrb = generate_e2_policy(
                model, tok, context, ctrl, span_records,
                mode="ctrb", gate=gate, threshold=float(freeze["threshold"]),
                dose=float(freeze["dose"]), max_new=MAX_NEW,
                deadline_s=args.deadline, raw_context=True)
            ctrb_branch = policy_branch(ctrb, score_turn(row, turn, ctrb.text))
            if not ctrb.interventions and ctrb.text != base["response"]:
                raise RuntimeError(f"conv {ci} turn {turn}: silent CTRB differs from base")

            fixed = generate_e2_policy(
                model, tok, context, ctrl, span_records,
                mode="fixed_oldest", gate=gate,
                threshold=float(freeze["threshold"]), dose=float(freeze["dose"]),
                max_new=MAX_NEW, deadline_s=args.deadline, raw_context=True)
            fixed_branch = policy_branch(fixed, score_turn(row, turn, fixed.text))
            if not fixed.interventions and fixed.text != base["response"]:
                raise RuntimeError(f"conv {ci} turn {turn}: silent fixed differs from base")

            periodic_spec = freeze["periodic_schedule"][str(turn)]
            periodic_onset = periodic_assignment(
                row["key"], turn,
                rate=float(periodic_spec["rate"]),
                onset=int(periodic_spec["onset"]),
            )
            if periodic_onset is None:
                periodic_branch = dict(base)
            else:
                periodic = generate_e2_policy(
                    model, tok, context, ctrl, span_records,
                    mode="periodic", periodic_onset=periodic_onset,
                    dose=float(freeze["dose"]), max_new=MAX_NEW,
                    deadline_s=args.deadline, raw_context=True)
                periodic_branch = policy_branch(
                    periodic, score_turn(row, turn, periodic.text)
                )

            positive_context = build_replay_context(
                prompts, base_responses, turn=turn, positive_control=True
            )
            positive_spans = user_turn_span_records(tok, positive_context)
            positive = generate_e2_policy(
                model, tok, positive_context, ctrl, positive_spans,
                mode="native", max_new=MAX_NEW,
                deadline_s=args.deadline, raw_context=True)
            positive_branch = policy_branch(
                positive, score_turn(row, turn, positive.text)
            )
            turns[str(turn)] = {
                "context_sha256": hashlib.sha256(context.encode()).hexdigest(),
                "aged_count": len(previous_ids),
                "base": base,
                "arms": {
                    "ctrb": ctrb_branch,
                    "periodic": periodic_branch,
                    "fixed_oldest": fixed_branch,
                    "positive_control": positive_branch,
                },
            }
        if not turns:
            raise RuntimeError(f"conversation {ci}: no evaluable late turns")
        atomic_json(
            record_path,
            {
                "ci": ci,
                "key": row["key"],
                "diagnostic": is_diagnostic_key(row["key"]),
                "turns": turns,
            },
        )
        print(f"eval conversation {ci + 1}/909", flush=True)

    records = [
        json.loads((outdir / f"conv-{i:03d}.json").read_text()) for i in range(909)
    ]
    primary = analyze_replay_records(records, diagnostic=False)
    diagnostic = analyze_replay_records(records, diagnostic=True)
    summary = {**meta, "primary": primary, "diagnostic": diagnostic}
    atomic_json(outdir / "summary.json", summary)
    print(json.dumps(summary, indent=1), flush=True)
    if not primary["gate_pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
