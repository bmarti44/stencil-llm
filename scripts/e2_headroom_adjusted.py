# ruff: noqa
"""Re-derive within-turn, family/mix/length-adjusted Multi-IF aging headroom."""

import bisect
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def combined_sha(paths):
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def turn_doc(row, turn):
    ids = json.loads(row[f"turn_{turn}_instruction_id_list"])
    kwargs = [json.loads(value) for value in json.loads(row[f"turn_{turn}_kwargs"])]
    return ids, kwargs


def quantile_thresholds(values):
    ordered = sorted(values)
    return [ordered[round(q * (len(ordered) - 1))] for q in (0.25, 0.5, 0.75)]


def rate(rows, aged):
    selected = [row["pass"] for row in rows if row["aged"] is aged]
    return sum(selected) / len(selected), len(selected)


def main():
    from stencil.e2_multiif import adjusted_aging_gap, is_diagnostic_key

    data_path = ROOT / "data" / "bench" / "multiif_en.jsonl"
    base_dir = ROOT / "results" / "qwen" / "b4-multiif-base"
    rows = [json.loads(line) for line in data_path.read_text().splitlines()]
    records = [json.loads((base_dir / f"conv-{i:03d}.json").read_text()) for i in range(len(rows))]
    if len(rows) != 909 or any(record["ci"] != i for i, record in enumerate(records)):
        raise RuntimeError("registered base cohort incomplete or reordered")
    length_thresholds = {
        turn: quantile_thresholds(
            [record["gen"][str(turn)]["n"] for record in records if str(turn) in record["gen"]]
        )
        for turn in (2, 3)
    }
    result = {}
    for turn in (2, 3):
        cells = []
        for row, record in zip(rows, records, strict=True):
            if str(turn) not in record["scores"]:
                continue
            ids, _ = turn_doc(row, turn)
            previous_ids, _ = turn_doc(row, turn - 1)
            scores = record["scores"][str(turn)]["inst_level_strict_acc"]
            if len(ids) != len(scores) or ids[: len(previous_ids)] != previous_ids:
                raise RuntimeError("Multi-IF cumulative instruction order changed")
            length_bin = bisect.bisect_right(
                length_thresholds[turn], record["gen"][str(turn)]["n"]
            )
            for index, (family, passed) in enumerate(zip(ids, scores, strict=True)):
                cells.append(
                    {
                        "conversation": record["ci"],
                        "aged": index < len(previous_ids),
                        "pass": bool(passed),
                        "family": family,
                        "length_bin": length_bin,
                    }
                )
        fresh_rate, fresh_n = rate(cells, False)
        aged_rate, aged_n = rate(cells, True)
        result[str(turn)] = {
            "raw": {
                "fresh_n": fresh_n,
                "fresh_rate": fresh_rate,
                "aged_n": aged_n,
                "aged_rate": aged_rate,
                "fresh_minus_aged_points": (fresh_rate - aged_rate) * 100,
            },
            "adjusted": adjusted_aging_gap(cells),
            "length_quartile_thresholds_tokens": length_thresholds[turn],
        }
    base_paths = [base_dir / f"conv-{i:03d}.json" for i in range(909)]
    output = {
        "status": "PRE_EVAL_HEADROOM_REDERIVATION",
        "method": "within-turn direct standardization on instruction-family x response-length-quartile common support",
        "conversations": len(rows),
        "diagnostic_conversations": sum(is_diagnostic_key(row["key"]) for row in rows),
        "primary_conversations": sum(not is_diagnostic_key(row["key"]) for row in rows),
        "data_sha256": sha(data_path),
        "base_records_sha256": combined_sha(base_paths),
        "runner_sha256": sha(Path(__file__)),
        "analysis_module_sha256": sha(ROOT / "src" / "stencil" / "e2_multiif.py"),
        "turns": result,
    }
    out_path = ROOT / "results" / "qwen" / "multiif-headroom-adjusted.json"
    out_path.write_text(json.dumps(output, indent=1))
    print(json.dumps(output, indent=1))


if __name__ == "__main__":
    main()
