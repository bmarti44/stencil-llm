# ruff: noqa
"""Synthetic holdout safe-dose and firing audit before Multi-IF contact."""

import argparse
import hashlib
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401

OPENER = "<|im_start|>assistant\n<think>\n\n</think>\n\n"
DOSES = (2.25, 3.0, 3.75)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sessions", type=int, default=60)
    parser.add_argument("--turn-max-new", type=int, default=320)
    parser.add_argument("--deadline", type=float, default=300.0)
    parser.add_argument("--gate", default="e2-hazard-gate.json")
    parser.add_argument("--out", default="e2-pre-eval-audit")
    return parser.parse_args()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_json(path, value):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=1))
    tmp.rename(path)


def branch_record(result, scores):
    return {
        "scores": [bool(x) for x in scores],
        "n_generated": result.n_generated,
        "truncated": result.truncated,
        "timed_out": result.timed_out,
        "response_sha256": hashlib.sha256(result.text.encode()).hexdigest(),
        "response": result.text,
    }


def main():
    args = parse_args()
    import torch
    from tokenizers import Tokenizer

    from stencil.causal_moments import score_row_constraints
    from stencil.ctrb import HazardGate
    from stencil.e2 import user_turn_span_records
    from stencil.e2_policy import generate_e2_policy
    from stencil.e2_stats import (
        audit_reasons,
        mcnemar_one_sided,
        safe_dose_reasons,
        summarize_policy_audit,
    )
    from stencil.qwen3 import Qwen3
    from stencil.wave import WaveController

    gate_path = ROOT / "results" / "qwen" / args.gate
    gate_report = json.loads(gate_path.read_text())
    if not gate_report.get("gate_pass") or gate_report.get("status") != "PASS":
        raise RuntimeError("certified passing hazard gate required")
    frozen = gate_report["gate"]
    gate = HazardGate(
        tuple(frozen["mean"]),
        tuple(frozen["scale"]),
        tuple(frozen["weights"]),
        float(frozen["bias"]),
    )

    data_path = ROOT / "data" / "b3" / "mt-dev-60.jsonl"
    model_path = ROOT / "models" / "qwen3-1.7b.pt"
    controller_path = ROOT / "results" / "qwen" / "b3-ce-s0.pt"
    sessions = [json.loads(line) for line in data_path.read_text().splitlines()]
    if not 1 <= args.sessions <= len(sessions):
        raise ValueError("invalid session count")
    sessions = sessions[: args.sessions]
    outdir = ROOT / "results" / "qwen" / args.out
    outdir.mkdir(parents=True, exist_ok=True)
    meta = {
        "schema": 1,
        "corpus": str(data_path.relative_to(ROOT)),
        "corpus_sha256": sha(data_path),
        "gate_sha256": sha(gate_path),
        "model_sha256": sha(model_path),
        "controller_sha256": sha(controller_path),
        "runner_sha256": sha(Path(__file__)),
        "policy_sha256": sha(ROOT / "src" / "stencil" / "e2_policy.py"),
        "stats_sha256": sha(ROOT / "src" / "stencil" / "e2_stats.py"),
        "sessions": args.sessions,
        "turn_max_new": args.turn_max_new,
        "deadline": args.deadline,
        "doses": list(DOSES),
        "threshold": frozen["threshold"],
    }
    meta_path = outdir / "meta.json"
    if meta_path.exists():
        if json.loads(meta_path.read_text()) != meta:
            raise RuntimeError("audit resume provenance mismatch")
    else:
        atomic_json(meta_path, meta)

    tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
    model = Qwen3()
    model.load_state_dict(torch.load(model_path, map_location="cpu"), strict=True)
    model = model.to(torch.bfloat16).cuda().eval()
    ctrl = WaveController(beta_max=1.0).cuda()
    ctrl.load_state_dict(torch.load(controller_path, map_location="cpu"))
    ctrl = ctrl.eval()

    for session_i, session in enumerate(sessions):
        record_path = outdir / f"session-{session_i:03d}.json"
        if record_path.exists():
            continue
        history = ""
        audit_rows = []
        for turn_i, turn in enumerate(session["turns"], start=1):
            history_now = history + f"<|im_start|>user\n{turn['prompt']}<|im_end|>\n"
            context = history_now + OPENER
            span_records = user_turn_span_records(tok, context)
            native = generate_e2_policy(
                model, tok, context, ctrl, span_records,
                mode="native", max_new=args.turn_max_new,
                deadline_s=args.deadline, raw_context=True)
            history = history_now + f"<|im_start|>assistant\n{native.text}<|im_end|>\n"
            if turn_i == 1:
                continue
            row = {
                "key": int(session["key"]) * 10 + turn_i,
                "instruction_id_list": turn["instruction_id_list"],
                "kwargs": turn["kwargs"],
            }
            native_scores = score_row_constraints(row, native.text)
            gated = generate_e2_policy(
                model, tok, context, ctrl, span_records,
                mode="ctrb", gate=gate, threshold=float(frozen["threshold"]),
                dose=3.0, max_new=args.turn_max_new,
                deadline_s=args.deadline, raw_context=True)
            events = [event for event in gated.interventions if event["kind"] == "onset"]
            fired = bool(events)
            if len(events) > 1:
                raise RuntimeError("sustained gate emitted multiple onsets")
            if not fired and gated.token_ids != native.token_ids:
                raise RuntimeError("gate-silent row is not bitwise native")
            gated_scores = score_row_constraints(row, gated.text)
            doses = {}
            if fired:
                onset = int(events[0]["start"])
                for dose in DOSES:
                    result = generate_e2_policy(
                        model, tok, context, ctrl, span_records,
                        mode="periodic", periodic_onset=onset, dose=dose,
                        max_new=args.turn_max_new, deadline_s=args.deadline,
                        raw_context=True)
                    scores = score_row_constraints(row, result.text)
                    doses[str(dose)] = branch_record(result, scores)
                if doses["3.0"]["response_sha256"] != hashlib.sha256(gated.text.encode()).hexdigest():
                    raise RuntimeError("forced nominal-dose replay differs from gated action")
            audit_rows.append(
                {
                    "session": session_i,
                    "key": session["key"],
                    "turn": turn_i,
                    "fired": fired,
                    "onset_count": len(events),
                    "onset": events[0]["start"] if fired else None,
                    "selected_origin": events[0]["selected_origin"] if fired else None,
                    "silent_identical": fired or gated.token_ids == native.token_ids,
                    "native": branch_record(native, native_scores),
                    "gate": branch_record(gated, gated_scores),
                    "gate_biased_tokens": gated.biased_tokens,
                    "doses": doses,
                }
            )
        if not audit_rows:
            raise RuntimeError("vacuous audit session")
        atomic_json(
            record_path,
            {"session": session_i, "key": session["key"], "rows": audit_rows},
        )
        print(f"audit session {session_i + 1}/{len(sessions)}", flush=True)

    session_records = [
        json.loads(path.read_text()) for path in sorted(outdir.glob("session-*.json"))
    ]
    if len(session_records) != args.sessions:
        raise RuntimeError("partial audit")
    rows = [row for record in session_records for row in record["rows"]]
    audit_input = [
        {
            "turn": row["turn"],
            "fired": row["fired"],
            "onset_count": row["onset_count"],
            "selected_origin": row["selected_origin"],
            "silent_identical": row["silent_identical"],
        }
        for row in rows
    ]
    firing = summarize_policy_audit(audit_input)
    decision_payload = [
        (row["session"], row["turn"], row["fired"], row["onset"], row["selected_origin"])
        for row in rows
    ]
    decision_hash = hashlib.sha256(json.dumps(decision_payload).encode()).hexdigest()
    safe = {}
    for dose in DOSES:
        improvements = regressions = net = 0
        native_trunc = arm_trunc = native_timeout = arm_timeout = 0
        for row in rows:
            base = row["native"]
            arm = row["doses"].get(str(dose), base)
            for b, a in zip(base["scores"], arm["scores"], strict=True):
                improvements += int(not b and a)
                regressions += int(b and not a)
                net += int(a) - int(b)
            native_trunc += int(base["truncated"])
            arm_trunc += int(arm["truncated"])
            native_timeout += int(base["timed_out"])
            arm_timeout += int(arm["timed_out"])
        safe[str(dose)] = {
            "improvements": improvements,
            "regressions": regressions,
            "net_utility": net,
            "benefit_p_one_sided": mcnemar_one_sided(improvements, regressions),
            "harm_p_one_sided": mcnemar_one_sided(regressions, improvements),
            "native_truncations": native_trunc,
            "arm_truncations": arm_trunc,
            "native_timeouts": native_timeout,
            "arm_timeouts": arm_timeout,
            "decision_hash": decision_hash,
        }
    reasons = audit_reasons(firing) + safe_dose_reasons(safe)
    starts = {
        turn: [int(row["onset"]) for row in rows if row["turn"] == turn and row["fired"]]
        for turn in (2, 3)
    }
    periodic = {
        str(turn): {
            "rate": firing["by_turn"][str(turn)]["fire_rate"],
            "onset": round(statistics.median(starts[turn])) if starts[turn] else None,
        }
        for turn in (2, 3)
    }
    summary = {
        **meta,
        "firing_audit": firing,
        "safe_dose": safe,
        "periodic_schedule": periodic,
        "gate_pass": not reasons,
        "failure_reasons": reasons,
    }
    atomic_json(outdir / "summary.json", summary)
    print(json.dumps(summary, indent=1), flush=True)
    if reasons:
        raise SystemExit(2)
    freeze = {
        "status": "FROZEN_BEFORE_MULTIIF",
        "gate_report": str(gate_path.relative_to(ROOT)),
        "gate_report_sha256": sha(gate_path),
        "audit_summary": str((outdir / "summary.json").relative_to(ROOT)),
        "audit_summary_sha256": sha(outdir / "summary.json"),
        "model_sha256": sha(model_path),
        "controller_sha256": sha(controller_path),
        "threshold": frozen["threshold"],
        "weights": frozen["weights"],
        "mean": frozen["mean"],
        "scale": frozen["scale"],
        "bias": frozen["bias"],
        "dose": 3.0,
        "draft_tokens": 0,
        "periodic_schedule": periodic,
        "policy_sha256": meta["policy_sha256"],
        "stats_sha256": meta["stats_sha256"],
    }
    atomic_json(ROOT / "results" / "qwen" / "e2-freeze.json", freeze)


if __name__ == "__main__":
    main()
