import json, math
from pathlib import Path
import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.stats import beta


def main():
    ROOT = Path(__file__).resolve().parents[3]
    OUT = ROOT / "results/quick-checks/check44c"
    summary = json.loads((OUT / "summary.json").read_text())
    checked = 0

    def match(pred, gold, mode):
        if not pred or not gold:
            return []
        a = np.array(
            [
                [
                    int(
                        (p["start"] == g["start"] and p["end"] == g["end"])
                        if mode == "exact"
                        else min(p["end"], g["end"]) > max(p["start"], g["start"])
                    )
                    for g in gold
                ]
                for p in pred
            ]
        )
        x, y = linear_sum_assignment(a, maximize=True)
        return [(int(i), int(j)) for i, j in zip(x, y) if a[i, j]]

    def merged(r, t, low):
        row = r["input"]
        c = r["C2"]
        if row["role"] != "user":
            return []
        out = [
            (s["start"], s["end"])
            for s, p in zip(c["spans"], c["probabilities"])
            if p >= t
        ]
        if c["overflow"]:
            return out
        for s in r["B"]["accepted"]:
            if any(min(s["end"], y) > max(s["start"], x) for x, y in out):
                continue
            m = max(
                (
                    p[1] + p[2]
                    for (x, y), p in zip(c["token_offsets"], c["token_probabilities"])
                    if y > x and min(s["end"], y) > max(s["start"], x)
                ),
                default=0,
            )
            if m >= low:
                out.append((s["start"], s["end"]))
        return out

    for name in ["heldout3", "heldout2", "setup"]:
        rows = [
            json.loads(x)
            for x in (OUT / f"{name}-records.jsonl").read_text().splitlines()
        ]
        for r in rows:
            checked += 1
            c = r["C2"]
            text = r["input"]["message"]
            assert (
                len(c["token_offsets"])
                == len(c["token_probabilities"])
                == c["token_counts"][0]
            )
            assert all(
                len(v) == 3
                and all(math.isfinite(x) and 0 <= x <= 1 for x in v)
                and abs(sum(v) - 1) < 1e-12
                for v in c["token_probabilities"]
            )
            for a in ["C2", "C2+B"]:
                assert all(
                    text[p["start"] : p["end"]] == p["text"] for p in r[a]["accepted"]
                )
        for a in ["C2", "C2+B"]:
            for mode in ["exact", "overlap"]:
                counts = dict(tp=0, fp=0, fn=0)
                rec = []
                prec = []
                for r in rows:
                    p, g = r[a]["accepted"], r["input"]["standing_rules"]
                    tp = len(match(p, g, mode))
                    counts["tp"] += tp
                    counts["fp"] += len(p) - tp
                    counts["fn"] += len(g) - tp
                    if g:
                        rec.append(tp / len(g))
                    if p:
                        prec.append(tp / len(p))
                actual = summary[name][a][mode]
                for k, v in counts.items():
                    assert actual[k] == v, (name, a, mode, k)
                if rec:
                    assert (
                        abs(
                            actual["macro_positive_message_recall"]
                            - sum(rec) / len(rec)
                        )
                        < 1e-12
                    )
                if prec:
                    assert (
                        abs(
                            actual["macro_predicted_message_precision"]
                            - sum(prec) / len(prec)
                        )
                        < 1e-12
                    )
            for f in ["payload", "quoted", "non_user", "all_negative"]:
                selected = (
                    [
                        r
                        for r in rows
                        if (
                            not r["input"]["standing_rules"]
                            and bool(r["input"].get("one_off_request"))
                        )
                        if f == "payload"
                    ]
                    if f == "payload"
                    else []
                )
                if f == "quoted":
                    selected = [
                        r
                        for r in rows
                        if not r["input"]["standing_rules"]
                        and r["input"].get("quoted_or_reported")
                    ]
                if f == "non_user":
                    selected = [r for r in rows if r["input"]["role"] != "user"]
                if f == "all_negative":
                    selected = [r for r in rows if not r["input"]["standing_rules"]]
                k = sum(bool(r[a]["accepted"]) for r in selected)
                n = len(selected)
                actual = summary[name][a][f]
                assert (actual["errors"], actual["n"]) == (k, n)
                bound = float(beta.ppf(0.95, k + 1, n - k)) if k < n else 1.0
                if n:
                    assert abs(bound - actual["upper95_one_sided"]) < 1e-10
        if name == "setup":
            for a in ["C2", "C2+B"]:
                counts = {"admit": 0, "supersedes": 0}
                false = 0
                for r in rows:
                    p, g = r[a]["accepted"], r["input"]["standing_rules"]
                    pairs = match(p, g, "overlap")
                    false += len(pairs) < len(p)
                    for _, j in pairs:
                        counts[g[j]["event"]] += 1
                assert false == summary[name][a]["false_admission_turns"]["errors"]
                for key, value in counts.items():
                    assert value == summary[name][a]["events"][key]["recovered"]

    for seed in [0, 1, 2]:
        rows = json.loads((OUT / f"seed{seed}-dev-records.json").read_text())
        z = json.loads(
            (
                ROOT / f"data/classifier/model/admission-v2/seed{seed}/threshold.json"
            ).read_text()
        )
        empty = [r for r in rows if not r["input"]["standing_rules"]]
        budget = math.floor(0.02 * len(empty))
        values = sorted(
            {0.0, math.nextafter(1.0, math.inf)}
            | {p for r in rows for p in r["C2"]["probabilities"]}
        )
        chosen = next(
            t
            for t in values
            if sum(
                r["input"]["role"] == "user"
                and any(p >= t for p in r["C2"]["probabilities"])
                for r in empty
            )
            <= budget
        )
        assert chosen == z["t"]
        lows = {0.0, math.nextafter(1.0, math.inf)}
        for r in rows:
            for s in r["B"]["accepted"]:
                lows.add(
                    max(
                        (
                            p[1] + p[2]
                            for (x, y), p in zip(
                                r["C2"]["token_offsets"], r["C2"]["token_probabilities"]
                            )
                            if y > x and min(y, s["end"]) > max(x, s["start"])
                        ),
                        default=0,
                    )
                )
        low = next(
            v
            for v in sorted(lows)
            if sum(bool(merged(r, chosen, v)) for r in empty) <= budget
        )
        assert low == z["t_low"]
        for r in rows:
            assert merged(r, chosen, low) == [
                (p["start"], p["end"]) for p in r["C2+B"]["accepted"]
            ]
    receipt = dict(
        passed=True,
        evaluation_records=checked,
        dev_records=3 * len(rows),
        independent_matching="scipy linear_sum_assignment max cardinality (different algorithm)",
        CP="scipy beta.ppf .95",
        checks=[
            "exact/overlap counts and macro P/R",
            "family counts and CP upper bounds",
            "setup events and unmatched turns",
            "finite token probabilities and substring identity",
            "all three DEV thresholds and C-then-B unions",
        ],
        inference_reruns=0,
    )
    (OUT / "independent-audit.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(receipt)


if __name__ == "__main__":
    main()
