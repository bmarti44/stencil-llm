"""Exp 1: echo-only arms on a 128-source Multi-IF subset (REGISTRATION.md alongside).

Phases (all deterministic, all resumable):
  --phase select     write selection.json (128 sources, seed 0, no outcome use)
  --phase replay     replay clf_pinned_echo on the first 8 selected conversations
  --phase run        generate clf_echo_only and role_echo_only per conversation
  --phase summarize  D1/D2/D3 with bootstrap intervals and exact sign tests

Reuses run_arm / _score_fields / context_layout / _entries from scripts/multiif_evict.py
and render_text_ledger / text_ledger_context from stencil.ledger. Data lineage:
evaluated on the exposed 909 records; nothing is fit on any benchmark outcome.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

SOURCE_DIR = ROOT / "results" / "qwen" / "multiif-evict-909-prequery-v2"
OUT_DIR = ROOT / "results" / "qwen" / "multiif-echo-only-128"
DATA = ROOT / "data" / "bench" / "multiif_en.jsonl"
N_SOURCES = 128
N_REPLAY = 8
ECHO_BUDGET = 256  # tokens, including the header line
MARGIN = 2.0
NEW_ARMS = ("clf_echo_only", "role_echo_only")
OLD_ARMS = ("full", "evicted", "clf_pinned", "clf_pinned_echo", "role_pinned")


def _evict():
    spec = importlib.util.spec_from_file_location(
        "multiif_evict", ROOT / "scripts" / "multiif_evict.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_records() -> dict[int, dict]:
    records = {}
    for path in sorted(SOURCE_DIR.glob("conv-*.json")):
        record = json.loads(path.read_text())
        records[int(record["ci"])] = record
    return records


def first_user_message(tokenizer, ids) -> str:
    context = tokenizer.decode(ids, skip_special_tokens=False)
    start = context.find("<|im_start|>user\n")
    end = context.find("<|im_end|>", start)
    if start < 0 or end < 0:
        raise ValueError("first user turn not found")
    return context[start + len("<|im_start|>user\n") : end]


def phase_select(tokenizer, records) -> dict:
    groups: dict[str, list[int]] = {}
    for ci, record in sorted(records.items()):
        digest = hashlib.sha256(
            first_user_message(tokenizer, record["context_token_ids"]).encode()
        ).hexdigest()
        groups.setdefault(digest, []).append(ci)
    sources = sorted(groups)
    chosen = random.Random(0).sample(sources, N_SOURCES)
    selection = {
        "schema": 2,
        "seed": 0,
        "n_sources_total": len(sources),
        "pairs": sum(1 for v in groups.values() if len(v) == 2),
        "singletons": sum(1 for v in groups.values() if len(v) == 1),
        "selected": [
            {
                "source": digest,
                "ci": min(groups[digest]),
                "key": records[min(groups[digest])]["key"],
            }
            for digest in chosen
        ],
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "selection.json").write_text(json.dumps(selection, indent=1))
    return selection


def load_selection() -> list[dict]:
    return json.loads((OUT_DIR / "selection.json").read_text())["selected"]


def load_model():
    import torch
    from tokenizers import Tokenizer

    from stencil import determinism
    from stencil.qwen3 import Qwen3

    determinism.assert_gpu_free_or_owned()
    tokenizer = Tokenizer.from_file(str(ROOT / "models/qwen3-1.7b-hf/tokenizer.json"))
    model = Qwen3()
    model.load_state_dict(
        torch.load(ROOT / "models/qwen3-1.7b.pt", map_location="cpu", weights_only=True)
    )
    return tokenizer, model.to(torch.bfloat16).cuda().eval()


def phase_replay(evict, tokenizer, model, records, args) -> dict:
    rows = []
    for item in load_selection()[:N_REPLAY]:
        record = records[item["ci"]]
        started = time.monotonic()
        generated = evict.run_arm(
            model,
            tokenizer,
            record["echo_context_token_ids"],
            evict_range=tuple(record["evict_range"]),
            keep=[tuple(s) for s in record["classifier_spans"]],
            max_new=args.max_new,
            deadline=args.deadline,
        )
        saved = record["arms"]["clf_pinned_echo"]["generated_token_ids"]
        rows.append(
            {
                "ci": item["ci"],
                "identical": generated["generated_token_ids"] == saved,
                "n_saved": len(saved),
                "n_new": len(generated["generated_token_ids"]),
                "seconds": time.monotonic() - started,
            }
        )
        print(f"replay ci={item['ci']} identical={rows[-1]['identical']}", flush=True)
    report = {
        "n": len(rows),
        "identical": sum(r["identical"] for r in rows),
        "rows": rows,
    }
    (OUT_DIR / "replay.json").write_text(json.dumps(report, indent=1))
    return report


def role_echo_entries(evict, tokenizer, record) -> tuple[list, int]:
    """Newest-first prior-user sentences within ECHO_BUDGET rendered tokens."""
    from stencil.ledger import render_text_ledger

    candidates = sorted(
        record["selector_candidates"],
        key=lambda c: (int(c["turn"]), int(c["span"][0])),
        reverse=True,
    )
    chosen: list[dict] = []
    for candidate in candidates:
        trial = sorted(
            chosen + [candidate], key=lambda c: (int(c["turn"]), int(c["span"][0]))
        )
        rendered = render_text_ledger(evict._entries(trial))
        if len(tokenizer.encode(rendered).ids) > ECHO_BUDGET:
            break
        chosen = trial
    rendered = render_text_ledger(evict._entries(chosen)) if chosen else ""
    return chosen, len(tokenizer.encode(rendered).ids) if rendered else 0


def phase_run(evict, tokenizer, model, records, rows, args) -> None:
    from stencil.ledger import text_ledger_context

    selected = load_selection()
    stop = (
        len(selected)
        if args.limit is None
        else min(len(selected), args.start + args.limit)
    )
    for item in selected[args.start : stop]:
        ci = item["ci"]
        out_path = OUT_DIR / f"conv-{ci:03d}.json"
        if out_path.exists():
            continue
        record = records[ci]
        row = rows[ci]
        turn = record["last_turn"]
        started = time.monotonic()
        arms = {}
        # clf_echo_only: identical echo context to clf_pinned_echo, zero pins
        arms["clf_echo_only"] = evict.run_arm(
            model,
            tokenizer,
            record["echo_context_token_ids"],
            evict_range=tuple(record["evict_range"]),
            keep=[],
            max_new=args.max_new,
            deadline=args.deadline,
        )
        # role_echo_only: newest-first sentences within the standalone budget
        context = tokenizer.decode(
            record["context_token_ids"], skip_special_tokens=False
        )
        chosen, echo_tokens = role_echo_entries(evict, tokenizer, record)
        echo_context = text_ledger_context(context, evict._entries(chosen))
        layout = evict.context_layout(tokenizer, echo_context)
        if list(layout["evict_range"]) != list(record["evict_range"]):
            raise AssertionError(f"ci={ci}: role echo changed eviction coordinates")
        arms["role_echo_only"] = evict.run_arm(
            model,
            tokenizer,
            layout["context_token_ids"],
            evict_range=tuple(layout["evict_range"]),
            keep=[],
            max_new=args.max_new,
            deadline=args.deadline,
        )
        for generated in arms.values():
            generated["scores"] = evict._score_fields(row, turn, generated["text"])
            generated["safety"] = {
                k: generated.pop(k)
                for k in ("timed_out", "truncated", "degenerate", "invalid")
            }
        out = {
            "schema": 2,
            "ci": ci,
            "key": record["key"],
            "source": item["source"],
            "last_turn": turn,
            "evict_range": record["evict_range"],
            "role_echo": {
                "sentences": [
                    c["text"]
                    for c in sorted(
                        chosen, key=lambda c: (int(c["turn"]), int(c["span"][0]))
                    )
                ],
                "n_candidates": len(record["selector_candidates"]),
                "rendered_tokens": echo_tokens,
                "budget": ECHO_BUDGET,
            },
            "arms": arms,
            "seconds": time.monotonic() - started,
        }
        evict.atomic_json(out_path, out)
        aged = len(out["arms"]["clf_echo_only"]["scores"]["aged"])
        print(
            f"conversation {ci}: "
            + " ".join(
                f"{n}={sum(a['scores']['aged'])}/{aged}" for n, a in arms.items()
            )
            + f" seconds={out['seconds']:.1f}",
            flush=True,
        )


def _rate(arm_record) -> float:
    bits = [bool(b) for b in arm_record["scores"]["aged"]]
    return 100.0 * sum(bits) / len(bits)


def _sign_test(diffs) -> dict:
    from scipy.stats import binomtest

    pos = sum(1 for d in diffs if d > 0)
    neg = sum(1 for d in diffs if d < 0)
    n = pos + neg
    p = binomtest(pos, n, 0.5, alternative="two-sided").pvalue if n else 1.0
    return {"wins": pos, "losses": neg, "discordant": n, "p_two_sided": p}


def _bootstrap(diffs, seed=0, reps=10_000) -> dict:
    import numpy as np

    arr = np.asarray(diffs, dtype=float)
    rng = np.random.default_rng(seed)
    means = np.array(
        [arr[rng.integers(0, len(arr), len(arr))].mean() for _ in range(reps)]
    )
    return {
        "mean": float(arr.mean()),
        "ci95": [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))],
    }


def phase_summarize(records) -> dict:
    selected = load_selection()
    new = {}
    for item in selected:
        path = OUT_DIR / f"conv-{item['ci']:03d}.json"
        if path.exists():
            new[item["ci"]] = json.loads(path.read_text())
    complete = [item["ci"] for item in selected if item["ci"] in new]
    rates = {
        ci: {
            **{arm: _rate(records[ci]["arms"][arm]) for arm in OLD_ARMS},
            **{arm: _rate(new[ci]["arms"][arm]) for arm in NEW_ARMS},
        }
        for ci in complete
    }
    estimands = {
        "D1_clf_pinned_echo_minus_clf_echo_only": ("clf_pinned_echo", "clf_echo_only"),
        "D2_role_pinned_minus_role_echo_only": ("role_pinned", "role_echo_only"),
        "D3_role_echo_only_minus_clf_echo_only": ("role_echo_only", "clf_echo_only"),
    }
    contrasts = {}
    for name, (a, b) in estimands.items():
        diffs = [rates[ci][a] - rates[ci][b] for ci in complete]
        contrasts[name] = {
            **_bootstrap(diffs),
            "sign_test": _sign_test(diffs),
            "n": len(diffs),
        }
    arm_means = (
        {
            arm: sum(rates[ci][arm] for ci in complete) / len(complete)
            for arm in OLD_ARMS + NEW_ARMS
        }
        if complete
        else {}
    )

    def safety(arm, ci):
        rec = new[ci]["arms"][arm] if arm in NEW_ARMS else records[ci]["arms"][arm]
        return rec["safety"]

    safety_excess = {}
    for arm in OLD_ARMS[1:] + NEW_ARMS:
        safety_excess[arm] = {
            k: sum(safety(arm, ci)[k] for ci in complete)
            - sum(safety("full", ci)[k] for ci in complete)
            for k in ("invalid", "degenerate", "truncated", "timed_out")
        }
    d1 = contrasts["D1_clf_pinned_echo_minus_clf_echo_only"]["ci95"]
    d3 = contrasts["D3_role_echo_only_minus_clf_echo_only"]["ci95"]
    if d1[0] > MARGIN:
        d1_reading = "PINS EARN THEIR PLACE (interval above +2)"
    elif d1[1] < MARGIN:
        d1_reading = "PINS DISPENSABLE AT 2-POINT MARGIN (interval below +2)"
    else:
        d1_reading = (
            "INSUFFICIENT EVIDENCE AT N=128 (interval straddles +2); "
            "text-only on cost grounds"
        )
    if d1[1] < 0:
        d1_reading += "; DEMONSTRATED HARM: pins reduce aged compliance"
    if d3[0] > 0:
        d3_reading = "ROLE RULE DEFAULT (interval above 0)"
    elif d3[1] < 0:
        d3_reading = "CLASSIFIER DEFAULT (interval below 0)"
    else:
        d3_reading = (
            "ROLE RULE DEFAULT ON COST GROUNDS (interval covers 0); classifier optional"
        )
    summary = {
        "schema": 2,
        "n_selected": len(selected),
        "n_complete": len(complete),
        "complete": len(complete) == len(selected),
        "arm_mean_aged_points": arm_means,
        "contrasts": contrasts,
        "safety_excess_over_full": safety_excess,
        "readings": {"D1": d1_reading, "D3": d3_reading},
        "margin_points": MARGIN,
    }
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=1))
    manifest = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(OUT_DIR.glob("*.json"))
        if p.name != "manifest.json"
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=1))
    return summary


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--phase", required=True, choices=["select", "replay", "run", "summarize"]
    )
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--max-new", type=int, default=512)
    parser.add_argument("--deadline", type=float, default=300.0)
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    evict = _evict()
    records = load_records()
    if args.phase == "summarize":
        print(json.dumps(phase_summarize(records), indent=1))
        return 0
    if args.phase == "select":
        from tokenizers import Tokenizer

        tokenizer = Tokenizer.from_file(
            str(ROOT / "models/qwen3-1.7b-hf/tokenizer.json")
        )
        selection = phase_select(tokenizer, records)
        print(
            json.dumps(
                {k: v for k, v in selection.items() if k != "selected"}, indent=1
            )
        )
        return 0
    tokenizer, model = load_model()
    if args.phase == "replay":
        report = phase_replay(evict, tokenizer, model, records, args)
        print(json.dumps({k: v for k, v in report.items() if k != "rows"}))
        return 0
    rows = {i: json.loads(line) for i, line in enumerate(DATA.read_text().splitlines())}
    phase_run(evict, tokenizer, model, records, rows, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
