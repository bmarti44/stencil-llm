"""Independent saved-record recount; no model calls or original held-out file reads."""

import hashlib
import json
import math
import re
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def read(path):
    return [json.loads(s) for s in path.read_text().splitlines() if s.strip()]


def matches(pred, gold, mode):
    states = {0}
    for p in pred:
        options = []
        for j, g in enumerate(gold):
            edge = (
                (p["start"], p["end"]) == (g["start"], g["end"])
                if mode == "exact"
                else min(p["end"], g["end"]) > max(p["start"], g["start"])
            )
            if edge:
                options.append(1 << j)
        states |= {mask | bit for mask in states for bit in options if not mask & bit}
    return max(mask.bit_count() for mask in states)


def main():
    summary = json.loads((OUT / "summary.json").read_text())
    snapshot = read(OUT / "evaluation-bank.jsonl")[1:]
    receipt = json.loads((OUT / "evaluation-start.json").read_text())
    assert (
        hashlib.sha256((OUT / "evaluation-bank.jsonl").read_bytes()).hexdigest()
        == receipt["source_sha256"]
    )
    threshold = json.loads(
        (ROOT / "data/classifier/model/admission-v1/seed0/threshold.json").read_text()
    )["threshold"]
    total = 0
    for bank in ("heldout", "setup"):
        records = read(OUT / f"{bank}-records.jsonl")
        if bank == "heldout":
            assert [r["input"] for r in records] == snapshot
        for arm in ("C", "B"):
            result = summary[bank][arm]
            for mode in ("exact", "overlap"):
                counts = []
                for r in records:
                    p, g = r[arm]["accepted"], r["input"]["standing_rules"]
                    tp = matches(p, g, mode)
                    counts.append((tp, len(p), len(g)))
                    assert tp == r[arm]["score"][mode]["tp"]
                    for span in p:
                        assert (
                            r["input"]["message"][span["start"] : span["end"]]
                            == span["text"]
                        )
                tp, n_pred, n_gold = (sum(c[i] for c in counts) for i in range(3))
                actual = result[mode]
                assert (actual["tp"], actual["fp"], actual["fn"]) == (
                    tp,
                    n_pred - tp,
                    n_gold - tp,
                )
                assert actual["precision"] == (tp / n_pred if n_pred else None)
                assert actual["recall"] == (tp / n_gold if n_gold else None)
                assert actual["macro_positive_message_recall"] == statistics.mean(
                    t / g for t, p, g in counts if g
                )
                assert actual["macro_predicted_message_precision"] == statistics.mean(
                    t / p for t, p, g in counts if p
                )
            for family in (
                "payload",
                "quoted",
                "non_user",
                "tool",
                "assistant",
                "all_negative",
            ):
                rate = result[family]
                n, k, u = rate["n"], rate["errors"], rate["upper95_one_sided"]
                if n and k < n:
                    cdf = sum(
                        math.comb(n, j) * u**j * (1 - u) ** (n - j)
                        for j in range(k + 1)
                    )
                    assert abs(cdf - 0.05) < 1e-10
        for r in records:
            row, a, b = r["input"], r["C"], r["B"]
            selected = [
                s
                for s, p in zip(a["spans"], a["probabilities"], strict=True)
                if row["role"] == "user" and p is not None and p >= threshold
            ]
            assert [(s["start"], s["end"]) for s in selected] == [
                (s["start"], s["end"]) for s in a["accepted"]
            ]
            spans = [
                (m.start(), m.group())
                for m in re.finditer(r"\S.*?(?:[.!?](?=\s|$)|$)", row["message"])
            ]
            assert len(spans) == len(b["proposals"])
            selected = [
                (start, start + len(text))
                for (start, text), p in zip(spans, b["proposals"], strict=True)
                if row["role"] == "user"
                and not p["overflow"]
                and p["probabilities"][1] >= 0.95
            ]
            assert selected == [(s["start"], s["end"]) for s in b["accepted"]]
            for p in b["proposals"]:
                if not p["overflow"]:
                    exps = [math.exp(x - max(p["logits"])) for x in p["logits"]]
                    assert all(
                        abs(x / sum(exps) - q) < 1e-12
                        for x, q in zip(exps, p["probabilities"], strict=True)
                    )
        total += len(records)
    assert total == 426
    assert summary["reading"] == "NO-GO"
    assert summary["heldout"]["C"]["overlap"]["recall"] < 0.85
    out = dict(
        status="PASS",
        records=total,
        arm_predictions=2 * total,
        independent_bitmask_span_matching=True,
        macro_recomputed=True,
        probability_cutoffs_verified=True,
        B_softmax_verified=True,
        CP_binomial_CDF_verified=True,
        input_snapshot_verified=True,
        new_inference=False,
    )
    (OUT / "independent-audit.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out))


if __name__ == "__main__":
    main()
