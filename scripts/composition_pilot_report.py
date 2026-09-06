"""CPU-only report from same-run DEV journal; never reopens episode content."""

import argparse
import hashlib
import json
import statistics
from pathlib import Path

ARMS = ("R", "N", "T", "O")
KINDS = ("language", "style", "format", "process")


def readlines(path):
    return (
        [json.loads(line) for line in path.read_text().splitlines()]
        if path.exists()
        else []
    )


def distribution(values):
    return (
        dict(
            n=len(values),
            min=min(values),
            median=statistics.median(values),
            mean=statistics.mean(values),
            max=max(values),
        )
        if values
        else None
    )


def report(out):
    run = json.loads((out / "run.json").read_text())
    rows = readlines(out / "records.jsonl")
    episodes = readlines(out / "episodes.jsonl")
    invariance = (
        json.loads((out / "batch-invariance.json").read_text())
        if (out / "batch-invariance.json").exists()
        else {"passed": False}
    )
    mode = run.get("selected_mode", "sequential")
    for r in rows:
        r["_detail"] = r["oracle_checker_results"][0]
    main = [r for r in rows if r["_detail"]["mode"] == mode]
    costs = {}
    for m in ("sequential", "batch"):
        interrupted = {
            r["_detail"]["episode"]
            for r in rows
            if r["_detail"]["mode"] == m
            and r["_detail"]["measurements"]["deadline_hit"]
        }
        complete = [
            e
            for e in episodes
            if e["mode"] == m and e["complete"] and e["episode"] not in interrupted
        ]
        observed = [e for e in episodes if e["mode"] == m and e["rounds"] > 0]
        if not observed:
            costs[m] = None
            continue
        complete_available = bool(complete)
        basis = complete or observed
        # Registered c is the largest completed episode cost. Also disclose
        # length-normalized (32 round) projection if only short batch is measured.
        c = {
            a: max(
                (e["arm_seconds"][a] if m == "sequential" else e["wall_seconds"] / 4)
                for e in basis
            )
            for a in ARMS
        }
        normalized = {
            a: max(
                (e["arm_seconds"][a] if m == "sequential" else e["wall_seconds"] / 4)
                * 32
                / e["rounds"]
                for e in basis
            )
            for a in ARMS
        }
        spent, load = run["gpu_held_seconds"], run.get("load_seconds", 0)

        def project(cs, full=False, spent=spent, load=load):
            allocated = (
                64 * sum(cs.values())
                if full
                else 64 * (cs["R"] + cs["N"]) + 16 * (cs["T"] + cs["O"])
            )
            return (spent + load + 1.25 * allocated) / 3600

        costs[m] = dict(
            max_full_episode_seconds=c if complete_available else None,
            observed_prefix_seconds=c,
            observed_prefix_nested_lower_bound_hours=project(c),
            observed_prefix_full_four_lower_bound_hours=project(c, True),
            completed_episode_cost_available=complete_available,
            normalized_32_round_seconds=normalized,
            registered_nested_hours=project(c) if complete_available else None,
            full_four_by_64_hours=project(c, True) if complete_available else None,
            normalized_nested_hours=project(normalized),
            normalized_full_four_by_64_hours=project(normalized, True),
            long_episode_measured=any(e["rounds"] == 32 for e in basis),
            usable=m == "sequential" or invariance["passed"],
            policy=(
                "spent + measured load + 1.25 * [64(cR+cN)+16(cT+cO)]; "
                "full4 also reported; no optional actuator"
            ),
            limitation=(
                "Batch amortization assumes four occupied lanes; "
                "if invariance fails these numbers are diagnostic only."
            ),
        )
    per_arm = {}
    endpoints = []
    manifest = []
    for row in rows:
        detail = row["_detail"]
        for item in detail["hidden"]:
            path = out / item["path"]
            assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
            manifest.append(
                dict(
                    **item,
                    episode=detail["episode"],
                    round=detail["round"],
                    arm=detail["arm"],
                    mode=detail["mode"],
                )
            )
    for arm in ARMS:
        chosen = [r for r in main if r["_detail"]["arm"] == arm]
        lengths = [r["output_token_count"] for r in chosen]
        relapse = {}
        for kind in KINDS:
            eligible = [
                r for r in chosen if r["_detail"]["outcome"]["denominators"][kind]
            ]
            numerator = sum(r["_detail"]["outcome"]["relapse"][kind] for r in eligible)
            eps = sorted(
                {
                    r["_detail"]["episode"]
                    for r in eligible
                    if r["_detail"]["outcome"]["relapse"][kind]
                }
            )
            relapse[kind] = dict(
                relapse=numerator,
                opportunities=len(eligible),
                episodes=eps,
                rate=numerator / len(eligible) if eligible else None,
                violations=sum(
                    r["_detail"]["outcome"]["violations"][kind] for r in chosen
                ),
                applicable_turns=len(chosen),
                attempted=sum(
                    r["_detail"]["outcome"]["attempted_relapse"][kind] for r in eligible
                ),
                prior_trait_opportunities=sum(
                    r["_detail"]["outcome"]["prior_trait_present"][kind]
                    for r in eligible
                ),
            )
        pressure = []
        for ep in sorted({r["_detail"]["episode"] for r in chosen}):
            er = [r for r in chosen if r["_detail"]["episode"] == ep]
            receipt = next(
                e for e in episodes if e["episode"] == ep and e["mode"] == mode
            )
            nband = sum(100 <= r["output_token_count"] <= 300 for r in er[:10])
            pressure.append(
                dict(episode=ep, first_ten_in_band=nband, eligible=nband == 10)
            )
            last = er[-1]["_detail"]["outcome"]
            endpoints.append(
                dict(
                    episode=ep,
                    arm=arm,
                    rounds=len(er),
                    scheduled=receipt["scheduled_rounds"],
                    complete=receipt["complete"],
                    final_success=last["success"] if receipt["complete"] else None,
                    stale_execution=any(
                        any(r["_detail"]["outcome"]["relapse"].values()) for r in er
                    ),
                    wrong_skill=any(
                        r["_detail"]["outcome"]["violations"]["wrong_family"]
                        for r in er
                    ),
                    breakage=any(
                        r["_detail"]["outcome"]["violations"]["breakage"] for r in er
                    ),
                    final_violations=last["violations"],
                )
            )
        measurements = [r["_detail"]["measurements"] for r in chosen]
        prefill = sum(x["prefill_seconds"] for x in measurements)
        decode = sum(x["decode_seconds"] for x in measurements)
        per_arm[arm] = dict(
            rounds=len(chosen),
            max_context_tokens=max((r["input_token_count"] for r in chosen), default=0),
            own_body_tokens=distribution(lengths),
            executed_batches=sum(
                bool(r["_detail"]["execution"]["executed"]) for r in chosen
            ),
            max_physical_cache_tokens=max(
                (r["_detail"]["measurements"]["cache_physical_tokens"] for r in chosen),
                default=0,
            ),
            in_band=sum(100 <= n <= 300 for n in lengths),
            pressure=pressure,
            truncations=sum(bool(r["truncated"]) for r in chosen),
            relapse=relapse,
            seconds_per_round=distribution([r["wall_seconds"] for r in chosen]),
            prefill_tokens=sum(x["prefill_tokens"] for x in measurements),
            prefill_seconds=prefill,
            decode_tokens=sum(x["generated_forward_tokens"] for x in measurements),
            decode_seconds=decode,
            prefill_tokens_per_second=sum(x["prefill_tokens"] for x in measurements)
            / prefill
            if prefill
            else None,
            decode_tokens_per_second=sum(
                x["generated_forward_tokens"] for x in measurements
            )
            / decode
            if decode
            else None,
        )
    # Actual shared batch timings counted once, not once per lane.
    performance = {}
    for m in ("sequential", "batch"):
        mr = [r for r in rows if r["_detail"]["mode"] == m]
        groups = {}
        for r in mr:
            d = r["_detail"]
            key = (d["episode"], d["round"], d["arm"] if m == "sequential" else "batch")
            groups.setdefault(key, []).append(d["measurements"])
        pf = sum(g[0]["prefill_seconds"] for g in groups.values())
        dec = sum(g[0]["decode_seconds"] for g in groups.values())
        performance[m] = dict(
            prefill_tokens=sum(
                r["_detail"]["measurements"]["prefill_tokens"] for r in mr
            ),
            decode_tokens=sum(
                r["_detail"]["measurements"]["generated_forward_tokens"] for r in mr
            ),
            prefill_seconds=pf,
            decode_seconds=dec,
        )
        p = performance[m]
        p["prefill_tok_s"] = p["prefill_tokens"] / pf if pf else None
        p["decode_tok_s"] = p["decode_tokens"] / dec if dec else None
    failed = []
    completed = {e["episode"] for e in episodes if e["mode"] == mode and e["complete"]}
    if not {"slab-dev-00", "slab-dev-01", "slab-dev-06", "slab-dev-07"} <= completed:
        failed.append("incomplete fixed four-episode fallback")
    cost = costs.get(mode)
    if (
        cost is None
        or not cost["long_episode_measured"]
        or cost["registered_nested_hours"] is None
        or cost["registered_nested_hours"] > 12
        or not cost["usable"]
    ):
        failed.append("measured cost / long-episode projection")
    if any(r["input_token_count"] + 512 > 32768 for r in rows):
        failed.append("context margin")
    if any(
        e.get("event") == "paired_context_rejection"
        for e in readlines(out / "events.jsonl")
    ):
        failed.append("paired context admission")
    truncated = sum(bool(r["truncated"]) for r in main)
    if not main or truncated / len(main) > 0.02:
        failed.append("truncation >2%")
    r = per_arm["R"]
    if (
        not r["rounds"]
        or r["in_band"] / r["rounds"] < 0.75
        or sum(x["eligible"] for x in r["pressure"]) < 0.75 * len(r["pressure"])
    ):
        failed.append(
            "R pressure (75% bodies and 75% episodes with ten prior in-band bodies)"
        )
    if not any(
        all(
            per_arm[a]["relapse"][k]["opportunities"] > 0
            for k in ("style", "format", "process")
        )
        for a in ARMS
    ):
        failed.append("nonzero style/format/process opportunities")
    if run["status"] != "finished" or run["gpu_held_seconds"] > 5400:
        failed.append("consumer/deadline")
    if any(r["_detail"]["measurements"]["deadline_hit"] for r in rows):
        failed.append("cooperative deadline interrupted diagnostic comparison")
    trigger = []
    for k in KINDS:
        v = per_arm["R"]["relapse"][k]
        o = per_arm["O"]["relapse"][k]
        if (
            v["opportunities"] >= 20
            and v["rate"] >= 0.15
            and len(v["episodes"]) >= 2
            and len(o["episodes"]) >= 2
        ):
            trigger.append(k)
    summary = dict(
        reading="INELIGIBLE" if failed else "ELIGIBLE",
        failures=failed,
        run=run,
        selected_mode=mode,
        complete_episodes=sorted(completed),
        rows=len(rows),
        primary_rows=len(main),
        per_arm=per_arm,
        endpoints=endpoints,
        cost_projections=costs,
        performance=performance,
        batch_invariance=invariance,
        contingent_mask_trigger=bool(trigger),
        trigger_kinds=trigger,
        language=(
            "zero relapse opportunities by design; live-rule violations still scored"
        ),
        hidden_files=len(manifest),
        incomplete_hidden_means=sum(
            not r["_detail"]["measurements"]["hidden_complete"] for r in rows
        ),
    )
    (out / "summary.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n"
    )
    (out / "hidden-manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n"
    )
    # Exact same-run text and token IDs; no missing provenance reconstructed.
    golden = []
    for r in main:
        d = r["_detail"]
        if d["arm"] == "R" and d["episode"] == "slab-dev-00":
            golden.append(
                dict(
                    round=d["round"],
                    text=r["rendered_messages"],
                    utf8_sha256=hashlib.sha256(
                        r["rendered_messages"].encode()
                    ).hexdigest(),
                    prompt_ids=r["rendered_token_ids"],
                    output=r["output"],
                    output_ids=r["output_token_ids"],
                    eos=r["eos"],
                    truncated=r["truncated"],
                )
            )
    if golden:
        path = out / "renderer-golden.jsonl"
        path.write_text(
            "".join(
                json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n" for x in golden
            )
        )
        summary["renderer_golden_sha256"] = hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
    summary["max_context_all_calls"] = {
        a: max(
            (r["input_token_count"] for r in rows if r["_detail"]["arm"] == a),
            default=0,
        )
        for a in ARMS
    }
    summary["max_physical_cache_all_calls"] = {
        a: max(
            (
                r["_detail"]["measurements"]["cache_physical_tokens"]
                for r in rows
                if r["_detail"]["arm"] == a
            ),
            default=0,
        )
        for a in ARMS
    }
    summary["unrun_dev_episodes"] = [
        f"slab-dev-{i:02}" for i in range(8) if f"slab-dev-{i:02}" not in completed
    ]
    summary["diagnostic_batch"] = {}
    for a in ARMS:
        chosen = [
            r
            for r in rows
            if r["_detail"]["mode"] == "batch" and r["_detail"]["arm"] == a
        ]
        summary["diagnostic_batch"][a] = dict(
            rounds=len(chosen),
            executed_batches=sum(
                bool(r["_detail"]["execution"]["executed"]) for r in chosen
            ),
            max_context=max((r["input_token_count"] for r in chosen), default=0),
            own_body_tokens=distribution([r["output_token_count"] for r in chosen]),
            truncations=sum(bool(r["truncated"]) for r in chosen),
            deadline_interrupted=any(
                r["_detail"]["measurements"]["deadline_hit"] for r in chosen
            ),
            final_checker_success=chosen[-1]["_detail"]["outcome"]["success"]
            if chosen
            else None,
            breakage=any(
                r["_detail"]["outcome"]["violations"]["breakage"] for r in chosen
            ),
            wrong_skill=any(
                r["_detail"]["outcome"]["violations"]["wrong_family"] for r in chosen
            ),
            stale_execution=any(
                any(r["_detail"]["outcome"]["relapse"].values()) for r in chosen
            ),
        )
    (out / "summary.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                k: summary[k]
                for k in (
                    "reading",
                    "failures",
                    "complete_episodes",
                    "rows",
                    "contingent_mask_trigger",
                    "cost_projections",
                )
            },
            indent=2,
        )
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "results/quick-checks/composition-pilot",
    )
    report(parser.parse_args().out)


if __name__ == "__main__":
    main()
