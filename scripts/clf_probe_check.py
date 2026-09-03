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

POST_PREFILL_TOTALS = {
    "full": 44,
    "evicted": 14,
    "clf_pinned": 33,
    "clf_pinned_echo": 46,
    "clf_control": 17,
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
    import g0_oracle
    import ledger_kv_probe as probe

    from stencil.causal_moments import score_row_constraints

    scores_path = Path(args.scores).resolve()
    scores = json.loads(scores_path.read_text())
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

    arm_specs = (
        ("full", "full"),
        ("evicted", "evicted"),
        ("clf_pinned", "pinned"),
        ("clf_pinned_echo", "pinned_echo"),
        ("clf_control", "pinned_control"),
    )
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
            {"span": candidate[0], "origin_turn": candidate[2]}
            for candidate in selected
        ]
        aged, keep = clamp(probe, tokenizer, context, aged, keep)
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
        arm_rows = {}
        for name, probe_arm in arm_specs:
            is_echo = name == "clf_pinned_echo"
            generated = probe.run_arm(
                model,
                tokenizer,
                echo_ids if is_echo else ids,
                probe_arm,
                keep,
                echo_range if is_echo else (low, high),
                0.0,
                args.max_new,
                args.deadline,
                control_keep=control,
                eviction_timing=args.eviction_timing,
            )
            passed = sum(score_row_constraints(score_row, generated["text"])[:n_aged])
            totals[name] += passed
            arm_rows[name] = {
                "aged_pass": passed,
                "pinned_cols": generated["pinned_cols"],
                "truncated": generated["truncated"],
                "degenerate": probe.is_degenerate(generated),
            }
        rows.append({"session": record["session"], "n_aged": n_aged, "arms": arm_rows})
        print(
            f"session {record['session']:02d}: "
            + " ".join(
                f"{name}={arm_rows[name]['aged_pass']}/{n_aged}"
                for name, _ in arm_specs
            ),
            flush=True,
        )

    output = {
        "eviction_timing": args.eviction_timing,
        "scores": str(scores_path),
        "scores_sha256": hashlib.sha256(scores_path.read_bytes()).hexdigest(),
        "threshold": args.threshold,
        "sessions": len(rows),
        "totals": totals,
        "post_prefill_totals": POST_PREFILL_TOTALS,
        "elapsed_seconds": time.monotonic() - started,
        "rows": rows,
    }
    outdir = ROOT / "results/qwen" / args.out
    outdir.mkdir(parents=True, exist_ok=True)
    probe.atomic_json(outdir / "clf-probe.json", output)
    report_fields = ("eviction_timing", "totals", "post_prefill_totals")
    print(json.dumps({key: output[key] for key in report_fields}, indent=1))


if __name__ == "__main__":
    main()
