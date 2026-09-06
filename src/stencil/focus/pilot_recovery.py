"""CPU-only replay of frozen DEV00 outputs under the registered parser."""

import json
import tempfile
from pathlib import Path

from .slab import Executor, check, generate_episode, materialize

ROOT = Path(__file__).resolve().parents[3]
FROZEN = ROOT / "results/quick-checks/composition-pilot"


def recover():
    rows = [json.loads(x) for x in (FROZEN / "records.jsonl").read_text().splitlines()]
    episode = generate_episode("dev", 0)
    executors, records = {}, []
    with tempfile.TemporaryDirectory() as temp:
        for index, row in enumerate(rows):
            detail = row["oracle_checker_results"][0]
            assert detail["episode"] == episode.episode_id
            key = (detail["mode"], detail["arm"])
            if key not in executors:
                path = Path(temp).joinpath(*key)
                materialize(episode, path)
                executors[key] = Executor(
                    path, json.loads((path / "public_tests.json").read_text())
                )
            executor = executors[key]
            execution = executor.run(row["output"])
            execution.pop("wall_seconds")
            # Diagnostic only: preserve claims inside discarded verbose wrappers.
            claims = [
                v
                for t in execution["tolerances"]
                if t["tolerance"] == "lift_report"
                for v in (
                    t["dropped"].get("verbose", [])
                    if isinstance(t["dropped"].get("verbose"), list)
                    else []
                )
                if isinstance(v, dict) and "delivery" in v
            ]
            rules = dict(episode.turns[detail["round"]].live)
            unscoped = "delivery" not in rules and bool(claims)
            records.append(
                dict(
                    source_row=index,
                    mode=key[0],
                    arm=key[1],
                    round=detail["round"],
                    execution=execution,
                    dropped_delivery_claims=claims,
                    dropped_unscoped_delivery=unscoped,
                    artifact_hashes=executor.hashes(),
                    outcome=check(
                        episode,
                        detail["round"],
                        row["output"],
                        executor,
                        truncated=row["truncated"],
                    ),
                )
            )
    summary = {}
    for mode, arm in executors:
        chosen = [r for r in records if (r["mode"], r["arm"]) == (mode, arm)]
        summary[f"{mode}/{arm}"] = dict(
            rows=len(chosen),
            executed_calls=sum(bool(r["execution"]["executed"]) for r in chosen),
            executed_tools=sum(len(r["execution"]["executed"]) for r in chosen),
            dropped_unscoped_delivery=sum(
                r["dropped_unscoped_delivery"] for r in chosen
            ),
            final_success=chosen[-1]["outcome"]["success"],
            final_integration=chosen[-1]["outcome"]["integration"],
            violations={
                k: sum(r["outcome"]["violations"][k] for r in chosen)
                for k in chosen[0]["outcome"]["violations"]
            },
            relapse={
                k: dict(
                    numerator=sum(
                        r["outcome"]["relapse"][k] and r["outcome"]["denominators"][k]
                        for r in chosen
                    ),
                    denominator=sum(
                        bool(
                            r["outcome"]["denominators"][k]
                            and r["outcome"]["prior_trait_present"][k]
                        )
                        for r in chosen
                    ),
                )
                for k in chosen[0]["outcome"]["relapse"]
            },
        )
    return dict(
        rows=len(records),
        executed_calls=sum(bool(r["execution"]["executed"]) for r in records),
        per_lane=summary,
    ), records


def main():
    summary, records = recover()
    (FROZEN / "recovered-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    (FROZEN / "recovered-records.jsonl").write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in records)
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
