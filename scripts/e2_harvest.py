# ruff: noqa
"""Corrected E2 causal harvest on the synthetic multi-turn corpus.

This is the post-Opus runner registered in EVF-PLAN.md.  Each candidate
moment shares one replayed native branch across four treatment arms and is
written inside an atomic whole-session record.  Multi-IF is never read here.
"""

import argparse
import hashlib
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401

OPENER = "<|im_start|>assistant\n<think>\n\n</think>\n\n"
SCHEMA_FIELDS = (
    "session", "turn", "step", "features", "response_position",
    "selected_span", "selected_origin", "topic", "changed_family",
    "label", "utility_delta", "native", "arms",
)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--sessions", type=int, default=300)
    p.add_argument("--top-moments", type=int, default=4)
    p.add_argument("--temporal-moments", type=int, default=4)
    p.add_argument("--turn-max-new", type=int, default=320)
    p.add_argument("--deadline", type=float, default=300.0)
    p.add_argument("--out", default="e2-corrected-harvest")
    return p.parse_args()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_json(path: Path, value):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=1))
    tmp.rename(path)


def branch_record(branch, scores, prefix_len):
    from stencil.e2 import make_branch_record

    return make_branch_record(
        branch.response,
        scores,
        prefix_len + len(branch.continuation_ids),
        branch.truncated,
        branch.timed_out,
    )


def summarize(records):
    labels = Counter()
    by_arm = defaultdict(Counter)
    utility = Counter()
    trunc = Counter()
    timeout = Counter()
    for session in records:
        for rec in session["moments"]:
            labels[rec["label"]] += 1
            for arm, branch in rec["arms"].items():
                by_arm[arm][branch["label_vs_native"]] += 1
                utility[arm] += branch["utility_delta"]
                trunc[arm] += int(branch["truncated"])
                timeout[arm] += int(branch["timed_out"])
            trunc["native"] += int(rec["native"]["truncated"])
            timeout["native"] += int(rec["native"]["timed_out"])
    moments = sum(labels.values())
    return {
        "sessions": len(records),
        "moments": moments,
        "labels": dict(sorted(labels.items())),
        "by_arm_labels": {a: dict(sorted(c.items())) for a, c in sorted(by_arm.items())},
        "utility_sum": dict(sorted(utility.items())),
        "truncations": dict(sorted(trunc.items())),
        "timeouts": dict(sorted(timeout.items())),
        "certification_counts_met": labels["helpful"] >= 100 and labels["harmful"] >= 100,
    }


def main():
    args = parse_args()
    import torch
    from tokenizers import Tokenizer

    from stencil.causal_moments import (
        rollout_arms_from_prefix_exact,
        score_row_constraints,
    )
    from stencil.ctrb import HazardGate, generate_ctrb
    from stencil.e2 import (
        arm_specs,
        constraint_span_records,
        make_moment_record,
        matched_nonconstraint_spans,
        select_candidate_records,
    )
    from stencil.qwen3 import Qwen3
    from stencil.wave import WaveController

    data_path = ROOT / "data" / "b3" / "mt-train-300.jsonl"
    model_path = ROOT / "models" / "qwen3-1.7b.pt"
    controller_path = ROOT / "results" / "qwen" / "b3-ce-s0.pt"
    sessions = [json.loads(line) for line in data_path.read_text().splitlines()]
    if not (1 <= args.sessions <= len(sessions)):
        raise ValueError(f"sessions must be in [1,{len(sessions)}]")
    sessions = sessions[: args.sessions]

    outdir = ROOT / "results" / "qwen" / args.out
    outdir.mkdir(parents=True, exist_ok=True)
    meta = {
        "schema": 3,
        "schema_fields": list(SCHEMA_FIELDS),
        "corpus": str(data_path.relative_to(ROOT)),
        "corpus_sha256": sha(data_path),
        "model_sha256": sha(model_path),
        "controller_sha256": sha(controller_path),
        "runner_sha256": sha(Path(__file__)),
        "e2_module_sha256": sha(ROOT / "src" / "stencil" / "e2.py"),
        "ctrb_sha256": sha(ROOT / "src" / "stencil" / "ctrb.py"),
        "causal_moments_sha256": sha(ROOT / "src" / "stencil" / "causal_moments.py"),
        "sessions": args.sessions,
        "top_moments": args.top_moments,
        "temporal_moments": args.temporal_moments,
        "turn_max_new": args.turn_max_new,
        "deadline": args.deadline,
        "nominal_arm": "sustained_all",
        "nominal_dose": 3.0,
        "branch_replay": "exact_kv_prompt_once_then_tokenwise",
    }
    meta_path = outdir / "meta.json"
    if meta_path.exists():
        if json.loads(meta_path.read_text()) != meta:
            raise RuntimeError("resume provenance mismatch")
    else:
        atomic_json(meta_path, meta)

    tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
    model = Qwen3()
    model.load_state_dict(torch.load(model_path, map_location="cpu"), strict=True)
    model = model.to(torch.bfloat16).cuda().eval()
    ctrl = WaveController(beta_max=1.0).cuda()
    ctrl.load_state_dict(torch.load(controller_path, map_location="cpu"))
    ctrl = ctrl.eval()
    silent = HazardGate.constant(0.0)
    started = time.monotonic()

    for session_i, sess in enumerate(sessions):
        record_path = outdir / f"session-{session_i:03d}.json"
        if record_path.exists():
            continue
        history = ""
        moments = []
        turn_summaries = []
        for turn_i, turn in enumerate(sess["turns"], start=1):
            history_now = history + f"<|im_start|>user\n{turn['prompt']}<|im_end|>\n"
            context = history_now + OPENER
            span_records = constraint_span_records(tok, context)
            spans = [tuple(x["span"]) for x in span_records]
            if not spans:
                raise RuntimeError(f"session {session_i} turn {turn_i}: no constraint spans")
            native_generation = generate_ctrb(
                model,
                tok,
                context,
                ctrl,
                spans,
                silent,
                max_new=args.turn_max_new,
                deadline_s=args.deadline,
                draft_tokens=0,
                collect_prefixes=True,
                raw_context=True,
            )
            history = history_now + (
                f"<|im_start|>assistant\n{native_generation.text}<|im_end|>\n"
            )
            turn_summaries.append(
                {
                    "turn": turn_i,
                    "native_response_sha256": hashlib.sha256(native_generation.text.encode()).hexdigest(),
                    "native_n_generated": native_generation.n_generated,
                    "span_records": span_records,
                }
            )
            if turn_i == 1:
                continue

            candidates = select_candidate_records(
                native_generation.trace,
                top_k=args.top_moments,
                temporal_k=args.temporal_moments,
            )
            row = {
                "key": int(sess["key"]) * 10 + turn_i,
                "instruction_id_list": turn["instruction_id_list"],
                "kwargs": turn["kwargs"],
            }
            aged_indices = [i for i, x in enumerate(span_records) if x["is_aged"]]
            width = sum(b - a for a, b in spans)
            control_spans = matched_nonconstraint_spans(
                total_len=len(tok.encode(context).ids), spans=spans, width=width
            )
            for candidate in candidates:
                prefix_ids = candidate["prefix_ids"]
                selected = int(candidate["selected_span"])
                specs = arm_specs(
                    spans,
                    selected_span=selected,
                    aged_indices=aged_indices,
                    control_spans=control_spans,
                )
                rollouts = rollout_arms_from_prefix_exact(
                    model=model,
                    tokenizer=tok,
                    prompt=context,
                    prefix_ids=prefix_ids,
                    arm_specs=specs,
                    max_new=args.turn_max_new,
                    deadline_s=args.deadline,
                    raw_context=True,
                )
                native = rollouts.pop("native")
                if native.response != native_generation.text:
                    raise RuntimeError(
                        f"session {session_i} turn {turn_i} step {candidate['step']}: "
                        "exact KV native branch diverged from committed trajectory"
                    )
                native_scores = score_row_constraints(row, native.response)
                native_record = branch_record(native, native_scores, len(prefix_ids))
                branches = {}
                for arm, focused in rollouts.items():
                    focused_scores = score_row_constraints(row, focused.response)
                    branches[arm] = branch_record(focused, focused_scores, len(prefix_ids))
                moment = make_moment_record(
                    session=session_i,
                    turn=turn_i,
                    step=candidate["step"],
                    features=candidate["features"],
                    response_position=candidate["step"] / max(1, native_generation.n_generated - 1),
                    selected_span=selected,
                    selected_origin=span_records[selected]["origin_turn"],
                    topic=sess["topic"],
                    changed_family=turn["new_combo"],
                    native=native_record,
                    arms=branches,
                )
                if tuple(moment) != SCHEMA_FIELDS:
                    raise RuntimeError("registered moment field list changed")
                moments.append(moment)

        record = {
            "session": session_i,
            "key": sess["key"],
            "topic": sess["topic"],
            "turns": turn_summaries,
            "moments": moments,
        }
        if not moments:
            raise RuntimeError(f"session {session_i}: vacuous moment record")
        atomic_json(record_path, record)
        if session_i % 2 == 0:
            counts = Counter(x["label"] for x in moments)
            print(
                f"session {session_i + 1}/{len(sessions)} moments={len(moments)} "
                f"labels={dict(counts)} elapsed={time.monotonic() - started:.0f}s",
                flush=True,
            )

    records = [json.loads(p.read_text()) for p in sorted(outdir.glob("session-*.json"))]
    if len(records) != args.sessions:
        raise RuntimeError("harvest record count does not match registration")
    summary = {**meta, **summarize(records)}
    atomic_json(outdir / "summary.json", summary)
    print(json.dumps(summary, indent=1), flush=True)


if __name__ == "__main__":
    main()
