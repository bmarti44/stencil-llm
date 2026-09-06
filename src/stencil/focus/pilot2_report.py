"""CPU report for Day5b, including gate-only stops without invented pilot metrics."""

import json

from scripts.composition_pilot import write

from .pilot2 import OUT, lines
from .pilot_recovery import FROZEN


def report(out=OUT):
    run = json.loads((out / "run.json").read_text())
    gate = (
        json.loads((out / "parity.json").read_text())
        if (out / "parity.json").exists()
        else dict(passed=False, complete=False)
    )
    rows, parity, episodes = (
        lines(out / "records.jsonl"),
        lines(out / "parity-records.jsonl"),
        lines(out / "episodes.jsonl"),
    )
    manifest = [
        dict(h, source="parity", index=r["index"]) for r in parity for h in r["hidden"]
    ]
    per_arm, endpoints, costs = {}, [], {}
    eligible_episodes = set()
    for arm in "RNTO":
        chosen = [r for r in rows if r["oracle_checker_results"][0]["arm"] == arm]
        ds = [r["oracle_checker_results"][0] for r in chosen]
        relapse = {}
        for kind in ("language", "style", "format", "process"):
            eligible = [
                d
                for d in ds
                if d["outcome"]["denominators"][kind]
                and d["outcome"]["prior_trait_present"][kind]
            ]
            eligible_episodes.update(d["episode"] for d in eligible)
            relapse[kind] = dict(
                numerator=sum(d["outcome"]["relapse"][kind] for d in eligible),
                denominator=len(eligible),
                relapsing_episodes=sorted(
                    {d["episode"] for d in eligible if d["outcome"]["relapse"][kind]}
                ),
                violations=sum(d["outcome"]["violations"][kind] for d in ds),
            )
        dec = sum(d["measurements"]["decode_seconds"] for d in ds)
        toks = sum(d["measurements"]["generated_forward_tokens"] for d in ds)
        per_arm[arm] = dict(
            calls=len(chosen),
            executed_calls=sum(bool(d["execution"]["executed"]) for d in ds),
            executed_tools=sum(len(d["execution"]["executed"]) for d in ds),
            truncation=sum(bool(r["truncated"]) for r in chosen),
            seconds_per_call=sum(r["wall_seconds"] for r in chosen) / len(chosen)
            if chosen
            else None,
            decode_tok_s=toks / dec if dec else None,
            decode_seconds=dec,
            decode_tokens=toks,
            max_context=max((r["input_token_count"] for r in chosen), default=None),
            in_band=sum(100 <= r["output_token_count"] <= 300 for r in chosen),
            relapse=relapse,
        )
        for episode in sorted({d["episode"] for d in ds}):
            er = [
                r
                for r in chosen
                if r["oracle_checker_results"][0]["episode"] == episode
            ]
            receipt = next(
                e
                for e in episodes
                if e["episode"] == episode and arm in e["arm_seconds"]
            )
            last = er[-1]["oracle_checker_results"][0]["outcome"]
            endpoints.append(
                dict(
                    episode=episode,
                    arm=arm,
                    complete=receipt["complete"],
                    final_success=last["success"] if receipt["complete"] else None,
                    final_integration=last["integration"]
                    if receipt["complete"]
                    else None,
                )
            )
        complete = [
            e["arm_seconds"][arm]
            for e in episodes
            if e["complete"] and arm in e["arm_seconds"]
        ]
        if complete:
            costs[arm] = max(complete)
        for d in ds:
            manifest.extend(
                dict(h, source="pilot", episode=d["episode"], arm=arm, round=d["round"])
                for h in d["hidden"]
            )
    from .pilot2 import pilot

    for h in manifest:
        assert pilot.sha(out / h["path"]) == h["sha256"]
    write(out / "hidden-manifest.json", manifest)
    o_proxy = "O" not in costs and "R" in costs
    if o_proxy:
        costs["O"] = costs["R"]
    old_spent = json.loads((FROZEN / "run.json").read_text())["gpu_held_seconds"]
    projection = (
        (
            old_spent
            + run["gpu_held_seconds"]
            + run.get("load_seconds", 0)
            + 1.25 * (64 * (costs["R"] + costs["N"]) + 16 * (costs["T"] + costs["O"]))
        )
        / 3600
        if len(costs) == 4
        else None
    )
    total = len(rows)
    executed = sum(a["executed_calls"] for a in per_arm.values())
    truncated = sum(a["truncation"] for a in per_arm.values())
    failures = []
    if projection is not None and projection > 12:
        failures.append("projection >12 GPU-h")
    if total and truncated / total > 0.02:
        failures.append("truncation >2%")
    if total and executed / total < 0.9:
        failures.append("executed-call rate <90%")
    complete = {
        e["episode"]
        for e in episodes
        if e["complete"] and set("RNT") <= set(e["arm_seconds"])
    }
    fallback = {f"slab-dev-{i:02}" for i in (0, 1, 6, 7)} <= complete
    if fallback and len(eligible_episodes) < 2:
        failures.append("executed-trait denominators in fewer than2 episodes")
    trigger = []
    for k, v in per_arm["R"]["relapse"].items():
        o = per_arm["O"]["relapse"][k]
        if (
            v["denominator"] >= 20
            and v["numerator"] / v["denominator"] >= 0.15
            and len(v["relapsing_episodes"]) >= 2
            and len(o["relapsing_episodes"]) >= 2
        ):
            trigger.append(k)
    reading = (
        "INELIGIBLE"
        if failures
        else "ELIGIBLE"
        if gate["passed"]
        and fallback
        and projection is not None
        and run["status"] == "finished"
        else "INCOMPLETE"
    )
    gt = sum(r["measurements"]["generated_forward_tokens"] for r in parity)
    gs = sum(r["measurements"]["decode_seconds"] for r in parity)
    summary = dict(
        reading=reading,
        failures=failures,
        run=run,
        gate=gate,
        parity_decode_tok_s=gt / gs if gs else None,
        parity_seconds_per_call=sum(
            r["measurements"]["batch_wall_seconds"] for r in parity
        )
        / len(parity)
        if parity
        else None,
        per_arm=per_arm,
        endpoints=endpoints,
        executed_trait_episodes=sorted(eligible_episodes),
        complete_episodes=sorted(complete),
        projection_hours=projection,
        projection_arm_seconds=costs,
        O_is_R_cost_proxy=o_proxy,
        prior_pilot_spent_seconds=old_spent,
        mask_trigger=bool(trigger),
        trigger_kinds=trigger,
        hidden_files=len(manifest),
    )
    write(out / "summary.json", summary)
    interpretation = (
        "No re-pilot launched: parity gate did not pass. Competence, relapse, "
        "context and cost projection are unavailable, not zero-performance findings."
        if not rows
        else "Per-arm measurements and episode endpoints are in summary.json; success "
        "includes every obligation; integration measures executable competence."
    )
    projected = projection if projection is not None else "UNAVAILABLE"
    trigger_reading = "MET" if trigger else "NOT ESTABLISHED"
    body = f"""# Composition DEV re-pilot — {reading}

Fit/train none; frozen DEV-00 parity and authored DEV only. No evaluation or
benchmark reads. Sequential, bf16 SDPA/{run["experts_implementation"]}, cap512;
renderer layout and T obligations unchanged, actuator OFF. One load; no signals/push.

Parity: {gate.get("compared", len(parity))}/64 prompts completed;
{gate.get("divergences", "unavailable")} divergent. Gate passed: {gate["passed"]}.
Exact prompt/output IDs, body+EOS byte comparisons and zero-based first-divergence
positions are in [parity-records.jsonl](parity-records.jsonl).
Gate decode throughput: {summary["parity_decode_tok_s"]} tok/s;
seconds/call: {summary["parity_seconds_per_call"]} (includes prefill).
GPU-held wall: {run["gpu_held_seconds"]:.3f}/7200 seconds, including load
{run.get("load_seconds", 0):.3f} seconds. Status: {run["status"]}.

Re-pilot calls: {total}; executed responses: {executed}; truncations: {truncated}.
{interpretation}

Projection R/Nx64 + O/Tx16: {projected} GPU-h.
Formula: prior pilot spent + this run spent + measured reload +
1.25*[64(cR+cN)+16(cT+cO)], divided by3600; c=max completed episode cost.
O=R cost proxy used: {o_proxy}; no batching credit. Both lengths must be measured.
Failing observed items: {failures}. Completed R/N/T episodes: {sorted(complete)}.
DEV mask trigger: {trigger_reading}; kinds={trigger};
O-unrun cannot establish it.

[summary.json](summary.json) contains per-kind violations and executed-trait
numerators/denominators, final success/integration, seconds/call, truncation,
executed calls, token band and max context. Unrun measurements are null/empty.
[renderer-check.json](renderer-check.json) verifies16 frozen original-input prompts.
[hidden-manifest.json](hidden-manifest.json) hashes {len(manifest)} local arrays,
layers8/16/24/32/40, last-prompt-token/generated-mean; arrays remain out of git.
Gate partial means at cap/deadline retain exact forward counts in their records.
CPU recovery is separate: [prior pilot amendment](../composition-pilot/README.md).
"""
    if run.get("error"):
        body += "\nRuntime error: `" + run["error"] + "`. No automatic eager retry.\n"
    (out / "README.md").write_text(body)
    print(
        json.dumps(
            {
                k: summary[k]
                for k in (
                    "reading",
                    "failures",
                    "gate",
                    "parity_decode_tok_s",
                    "projection_hours",
                )
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    report()
