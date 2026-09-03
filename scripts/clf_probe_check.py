"""Re-run the 20-session classifier-selector probe with selectable eviction timing."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

PRE_QUERY_BASELINE_TOTALS = {
    "full": 44,
    "evicted": 10,
    "clf_pinned": 41,
    "clf_pinned_echo": 46,
    "clf_control": 13,
}
CALIBRATION_PATH = ROOT / "results/qwen/b3-deficit-cal.json"
ARM_SPECS = (
    ("full", "full"),
    ("evicted", "evicted"),
    ("clf_pinned", "pinned"),
    ("clf_pinned_echo", "pinned_echo"),
    ("clf_control", "pinned_control"),
    ("clf_pinned_wave", "pinned"),
    ("clf_pinned_wave_conf", "pinned"),
    ("clf_pinned_echo_wave", "pinned_echo"),
    ("fv_inject", "evicted"),
    ("fv_inject_echo", "pinned_echo"),
    ("fv_clear", "evicted"),
)
WAVE_ARMS = {
    "clf_pinned_wave",
    "clf_pinned_wave_conf",
    "clf_pinned_echo_wave",
}
FV_ARMS = {"fv_inject", "fv_inject_echo", "fv_clear"}
KILL_RULE_ARMS = WAVE_ARMS | FV_ARMS


def load_wave_calibration(path=CALIBRATION_PATH):
    path = Path(path)
    raw = json.loads(path.read_text())
    selected = raw["selected"]
    row = raw["results"][selected]
    return {
        "selected": selected,
        "tau": float(row["tau"]),
        "b_max": float(row["b_max"]),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def confidence_cap(probability, b_max):
    if not 0.5 <= probability <= 1.0:
        raise ValueError("confidence-scaled wave requires P(keep) in [0.5, 1.0]")
    return b_max * (probability - 0.5) / 0.5


def arm_configuration(
    name,
    *,
    ids,
    echo_ids,
    evict_range,
    echo_evict_range,
    keep,
    selected,
    tau,
    b_max,
    eviction_timing,
):
    probe_arm = dict(ARM_SPECS)[name]
    is_echo = name in {
        "clf_pinned_echo",
        "clf_pinned_echo_wave",
        "fv_inject_echo",
    }
    deficit_spans = []
    if name in WAVE_ARMS:
        deficit_spans = [
            (
                span,
                confidence_cap(probability, b_max)
                if name == "clf_pinned_wave_conf"
                else b_max,
            )
            for span, probability, _turn in selected
        ]
    return {
        "probe_arm": probe_arm,
        "ids": echo_ids if is_echo else ids,
        "evict_range": echo_evict_range if is_echo else evict_range,
        "keep": keep,
        "deficit_spans": deficit_spans,
        "deficit_tau": tau if deficit_spans else None,
        "confidence_scaled": name == "clf_pinned_wave_conf",
        "eviction_timing": eviction_timing,
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--scores", required=True)
    parser.add_argument(
        "--eviction-timing",
        choices=("pre-query", "post-prefill"),
        default="pre-query",
    )
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--max-new", type=int, default=512)
    parser.add_argument("--deadline", type=float, default=300.0)
    parser.add_argument("--out", default="ledger-kv-probe-prequery")
    parser.add_argument(
        "--vectors", default=str(ROOT / "results/qwen/fv-vectors/vectors.pt")
    )
    parser.add_argument(
        "--fv-grid", default=str(ROOT / "results/qwen/fv-vectors/grid.json")
    )
    return parser.parse_args(argv)


def clamp(probe, tokenizer, context, aged, keep):
    while aged:
        try:
            probe.echo_context(tokenizer, context, aged)
            return aged, keep
        except ValueError:
            bad = next(
                record
                for record in aged
                if _echo_invalid(probe, tokenizer, context, record)
            )
            aged = [record for record in aged if record is not bad]
            keep = [span for span in keep if span != tuple(bad["span"])]
    return aged, keep


def _echo_invalid(probe, tokenizer, context, record):
    try:
        probe.echo_context(tokenizer, context, [record])
    except ValueError:
        return True
    return False


def main(argv=None):
    args = parse_args(argv)
    import function_vectors as fv_script
    import g0_oracle
    import ledger_kv_probe as probe

    from stencil.causal_moments import score_row_constraints
    from stencil.function_vectors import (
        combine_vectors,
        function_vector_summary,
        generate_injected,
    )

    scores_path = Path(args.scores).resolve()
    scores = json.loads(scores_path.read_text())
    calibration = load_wave_calibration()
    vectors_path = Path(args.vectors).resolve()
    grid_path = Path(args.fv_grid).resolve()
    vectors, vector_payload = fv_script.load_vectors(vectors_path)
    grid = json.loads(grid_path.read_text())
    if grid.get("status") != "selected_before_probe":
        raise ValueError("function-vector grid must be selected before probe")
    fv_alpha = float(grid["selected"]["alpha"])
    fv_layer = int(grid["selected"]["layer"])
    model, tokenizer = g0_oracle.load_model()
    corpus_path = ROOT / "data/b3/mt-train-300.jsonl"
    corpus = {
        row["key"]: row
        for row in (json.loads(line) for line in corpus_path.read_text().splitlines())
    }
    source_dir = ROOT / "results/qwen/ledger-kv-probe-h1p"
    source_records = [
        json.loads(path.read_text())
        for path in sorted(source_dir.glob("session-*.json"))
    ]
    if len(source_records) != 20:
        raise RuntimeError(f"expected 20 source sessions, found {len(source_records)}")

    arm_specs = ARM_SPECS
    totals = {name: 0 for name, _ in arm_specs}
    rows = []
    started = time.monotonic()
    for record in source_records:
        ids = record["context_token_ids"]
        low, high = record["evict_range"]
        context = tokenizer.decode(ids, skip_special_tokens=False)
        encoding = tokenizer.encode(context)
        if encoding.ids != ids:
            raise AssertionError("source context does not token-round-trip")
        candidates = []
        for char_start, char_end, probability, turn in scores[str(record["session"])]:
            token_span = probe._token_span(encoding, char_start, char_end)
            if token_span:
                start, end = max(low, token_span[0]), min(high, token_span[1])
                if end > start and probability >= args.threshold:
                    candidates.append(((start, end), probability, turn))
        selected = sorted(candidates, key=lambda candidate: -candidate[1])
        keep = sorted(candidate[0] for candidate in selected)
        aged = [
            {
                "span": candidate[0],
                "probability": candidate[1],
                "origin_turn": candidate[2],
            }
            for candidate in selected
        ]
        aged, keep = clamp(probe, tokenizer, context, aged, keep)
        selected = [
            (tuple(item["span"]), item["probability"], item["origin_turn"])
            for item in aged
        ]
        control = probe.matched_control_spans(keep, (low, high)) if keep else []
        if aged:
            echoed, _, _ = probe.echo_context(tokenizer, context, aged)
            echo_ids, echo_range = probe.tokenized_eviction_range(tokenizer, echoed)
        else:
            echo_ids, echo_range = ids, (low, high)

        session = corpus[record["key"]]
        last = session["turns"][-1]
        score_row = {
            "key": int(session["key"]) * 10 + record["n_turns"],
            "instruction_id_list": last["instruction_id_list"],
            "kwargs": last["kwargs"],
        }
        n_aged = record["n_aged"]
        aged_types = session["turns"][record["n_turns"] - 1]["combo"][:n_aged]
        if len(aged_types) != n_aged:
            raise AssertionError("aged constraint type count mismatch")
        fv_vector, unknown_types = combine_vectors(vectors, aged_types, fv_layer)
        arm_rows = {}
        for name, _probe_arm in arm_specs:
            configured = arm_configuration(
                name,
                ids=ids,
                echo_ids=echo_ids,
                evict_range=(low, high),
                echo_evict_range=echo_range,
                keep=keep,
                selected=selected,
                tau=calibration["tau"],
                b_max=calibration["b_max"],
                eviction_timing=args.eviction_timing,
            )
            if name in FV_ARMS:
                fv_keep = keep if name == "fv_inject_echo" else ()
                generated = generate_injected(
                    model,
                    tokenizer,
                    configured["ids"],
                    evict_range=configured["evict_range"],
                    keep=fv_keep,
                    vector=fv_vector,
                    alpha=fv_alpha,
                    layer=fv_layer,
                    clear_after=64 if name == "fv_clear" else None,
                    max_new=args.max_new,
                    deadline_s=args.deadline,
                )
                generated["invalid_output"] = probe.invalid_output(generated["text"])
            else:
                generated = probe.run_arm(
                    model,
                    tokenizer,
                    configured["ids"],
                    configured["probe_arm"],
                    configured["keep"],
                    configured["evict_range"],
                    0.0,
                    args.max_new,
                    args.deadline,
                    control_keep=control,
                    eviction_timing=configured["eviction_timing"],
                    deficit_spans=configured["deficit_spans"],
                    deficit_tau=configured["deficit_tau"],
                )
            scores_for_arm = list(
                score_row_constraints(score_row, generated["text"])[:n_aged]
            )
            passed = sum(scores_for_arm)
            totals[name] += passed
            arm_rows[name] = {
                "aged_pass": passed,
                "pinned_cols": generated["pinned_cols"],
                "truncated": generated["truncated"],
                "timed_out": generated["timed_out"],
                "degenerate": (
                    not generated["truncated"] and generated["rep4"] > 0.5
                ),
                "invalid": generated["invalid_output"],
                "scores": scores_for_arm,
            }
        rows.append({
            "session": record["session"],
            "n_aged": n_aged,
            "aged_constraint_types": aged_types,
            "unknown_vector_constraints": len(unknown_types),
            "unknown_vector_types": unknown_types,
            "arms": arm_rows,
        })
        print(
            f"session {record['session']:02d}: "
            + " ".join(
                f"{name}={arm_rows[name]['aged_pass']}/{n_aged}"
                for name, _ in arm_specs
            ),
            flush=True,
        )

    safety = {
        name: {
            "truncated": sum(row["arms"][name]["truncated"] for row in rows),
            "timeout": sum(row["arms"][name]["timed_out"] for row in rows),
            "degenerate": sum(row["arms"][name]["degenerate"] for row in rows),
            "invalid": sum(row["arms"][name]["invalid"] for row in rows),
        }
        for name, _ in arm_specs
    }
    output = {
        "eviction_timing": args.eviction_timing,
        "scores": str(scores_path),
        "scores_sha256": hashlib.sha256(scores_path.read_bytes()).hexdigest(),
        "threshold": args.threshold,
        "calibration": calibration,
        "sessions": len(rows),
        "totals": totals,
        "safety": safety,
        "wave_kill_rule": "degenerate > 2/20 kills the arm",
        "wave_killed": {
            name: safety[name]["degenerate"] > 2
            for name in KILL_RULE_ARMS
        },
        "pre_query_baseline_totals": PRE_QUERY_BASELINE_TOTALS,
        "function_vectors": {
            "vectors": str(vectors_path),
            "vectors_sha256": hashlib.sha256(vectors_path.read_bytes()).hexdigest(),
            "grid": str(grid_path),
            "grid_sha256": hashlib.sha256(grid_path.read_bytes()).hexdigest(),
            "constraint_types": list(vector_payload["constraint_types"]),
            "alpha": fv_alpha,
            "layer": fv_layer,
            "clear_after_generated_tokens": 64,
        },
        "elapsed_seconds": time.monotonic() - started,
        "rows": rows,
    }
    output.update(
        function_vector_summary(
            rows,
            totals=totals,
            killed=output["wave_killed"],
        )
    )
    outdir = ROOT / "results/qwen" / args.out
    outdir.mkdir(parents=True, exist_ok=True)
    probe.atomic_json(outdir / "clf-probe.json", output)
    report_fields = (
        "eviction_timing",
        "totals",
        "safety",
        "wave_killed",
        "pre_query_baseline_totals",
        "function_vectors",
        "preregistered_reading",
        "paired_fv_inject_vs_evicted",
        "paired_fv_inject_echo_vs_clf_pinned_echo",
        "unknown_vector_constraints",
        "reading",
    )
    print(json.dumps({key: output[key] for key in report_fields}, indent=1))


if __name__ == "__main__":
    main()
