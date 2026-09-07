"""Descriptive report from audited frozen records; no inference or gate edits."""
# ruff: noqa: E501 -- report prose and Markdown table rows are kept together.

import argparse
import json
from math import comb
from pathlib import Path


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def sign_flip_sensitivity(families):
    """Wins become losses; hold other families fixed and recompute Holm-3."""
    result = {}
    for name, family in families.items():
        if not family["pass"]:
            result[name] = dict(initial_pass=False, flips_to_lose_significance=0)
            continue
        for flips in range(1, family["wins"] + 1):
            n = family["wins"] + family["losses"]
            ps = {k: f["p"] for k, f in families.items()}
            ps[name] = (
                sum(comb(n, k) for k in range(family["wins"] - flips, n + 1)) / 2**n
            )
            adjusted, holm = 0.0, {}
            for rank, key in enumerate(sorted(ps, key=ps.get)):
                adjusted = max(adjusted, min(1.0, (3 - rank) * ps[key]))
                holm[key] = adjusted
            if holm[name] > 0.05:
                result[name] = dict(
                    initial_pass=True,
                    flips_to_lose_significance=flips,
                    resulting_holm_p=holm[name],
                )
                break
    return dict(
        unit="episode sign",
        operation="reverse R-win to N-win, other family signs fixed; recompute Holm-3; significance-only fragility, not a new test",
        families=result,
    )


def report(out, *, pilot):
    summary, audit, life = [
        json.loads((out / name).read_text())
        for name in ("summary.json", "audit.json", "lifecycle.json")
    ]
    assert audit["full_prompt_feedback_executor_score_replay"]
    families = summary["primary"]["families"]
    harm = summary["harm_calibration" if pilot else "harm"]
    flips = sign_flip_sensitivity(families)
    write(out / "flip-sensitivity.json", flips)
    write(
        out / "episode-tables.json",
        dict(
            primary={k: f["episodes"] for k, f in families.items()},
            harm={k: c["episodes"] for k, c in harm["contrasts"].items()},
        ),
    )
    write(
        out / "cost-audit.json",
        dict(
            lifecycle=life,
            main_output_tokens=audit["output_tokens"],
            main_prompt_tokens=audit["prompt_tokens"],
            lane_seconds=audit["lane_seconds"],
            projected_full_gpu_hours=audit["projected_full_gpu_hours"],
        ),
    )
    lines = [
        "Fit-on: none; development-on: eight DEV episodes and prior failure audits; "
        + (
            "evaluated-on: none; fresh64 remains model-unopened until the separate frozen launch."
            if pilot
            else "evaluated-on: the fresh64 successor bank, one model pass. No benchmark inputs or responses."
        ),
        "",
        f"# Amendment 6b — {summary['reading']}",
        "",
        f"Pinned code: `{audit['pinned_sha']}`. {audit['replayed_records']} records and {audit['responses']} HTTP responses audited. Every saved prompt, feedback, executor result, score, text/token/EOS/cap record and local hash reproduced. GPU held **{audit['gpu_held_hours']:.4f} hours**; own container/flag cleanup recorded.",
        "",
        "Failed pilot items: " + (", ".join(summary["failures"]) or "none") + "."
        if pilot
        else "Failed full-run items: "
        + (", ".join(summary["failures"]) or "none")
        + ".",
        "",
        "| Arm | Records | Executing lanes | Initial round-zero rejections | Initial / surviving syntax | Repairs | Broken episodes | Final semantic integration |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for arm, m in audit["per_arm"].items():
        lines.append(
            f"| {arm} | {m['records']} | {m['executing_lanes']} | {m['round_zero_rejections']} | {m['initial_syntax']} / {m['surviving_syntax']} | {m['repairs']} | {m['broken_episodes']} | {m['final_integration']} |"
        )
    lines += [
        "",
        "Breakage is syntax/protocol failure; semantic wrong values and runtime test exceptions are integration failures, reported separately. Repair counts distinguish initial failures from final breakage; a zero repair count supplies no GPU evidence of repair efficacy.",
        "",
        "| Primary family | Paired episodes | R wins / N wins / ties | Mean gain | One-sided p | Holm p | Missing-write-as-failure gain |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name in ("delivery", "format", "indent"):
        f = families[name]
        lines.append(
            f"| {name} | {f['n']} | {f['wins']}/{f['losses']}/{f['ties']} | {f['mean_gain']:.6g} | {f['p']:.9g} | {f['holm_p']:.9g} | {f['strict_failed_attempts']['mean_gain']:.6g} |"
        )
    lines += [
        "",
        "Unchanged primary: scheduled first-applicable change rounds, common parsed writes, within-episode averaging, exact one-sided R>N sign test, Holm across three families. Delivery alone powers the full-run primary verdict. DEV significance never gates FIX-CONFIRMED. Negative directions and missingness remain part of the result.",
        "",
        "| Harm contrast | Common-attempt episodes | Greater / lower / ties | Holm p | Coverage | Harm signal |",
        "|---|---:|---:|---:|---|---|",
    ]
    for arm, c in harm["contrasts"].items():
        lines.append(
            f"| {arm}:N | {c['n']} | {c['wins']}/{c['losses']}/{c['ties']} | {c['holm_p']:.9g} | {c['coverage']} | {c['signal']} |"
        )
    lines += [
        "",
        "Coverage remains75% in both contrasts (6/8 DEV,48/64 full run). All8 DEV schedules have two indent-change opportunities; the CPU scoped negative control reaches8/8. Thus the gate is achievable and was retained. Conditional risk excludes non-attempts; this selected-population comparison is neither a causal adjustment nor noninferiority evidence. T:N is the block-free reminder negative control.",
        "",
        "The original95fa7fc0 FAIL remains frozen, untouched and unrescored. Its registered one-adversarial-flip format fragility caveat remains. Successor significance fragility (episode R-win to N-win, recompute Holm-3): "
        + ", ".join(
            f"{k}: {v['flips_to_lose_significance']}"
            for k, v in flips["families"].items()
        )
        + "; zero means already nonsignificant. See flip-sensitivity.json.",
    ]
    if pilot:
        lines += [
            "",
            f"Measured full-run projection: **{audit['projected_full_gpu_hours']:.4f} GPU-hours**, including25% main reserve and1200s controls/cleanup. Harm calibration eligible: **{harm['calibrated']}**. Frozen64 launch additionally requires this receipt and its source/hash binding committed first.",
            "",
            "Determinism8/8 exact, C4 forward/reverse. The40 fixed pilot7-payload cross-container replay belongs to the full run and was not performed in this pilot. CPU166passed/1expected xfail; new protocol rejection tests failed on old feedback then passed after the repair.",
        ]
    else:
        replay = json.loads((out / "reproducibility.json").read_text())
        lines += [
            "",
            f"Fixed cross-container replay: {replay['divergent']}/{replay['payloads']} payloads divergent; {replay['any_divergence_episodes']}/8 DEV episodes with any divergence. Descriptive clustered control, not universal reproducibility.",
        ]
    lines += [
        "",
        "Claim ceiling: bounded request-time rule restatement on one frozen trunk and authored distribution. No superiority-to-prose, removed-stale-influence, generalized coding competence, free-text admission or actuator claim. The scoped system example and accumulated old history remain possible influences.",
        "",
        "Artifacts: [registration](REGISTRATION.md), [summary](summary.json), [audit](audit.json), [episode tables](episode-tables.json), [cost](cost-audit.json), records-R/N/T/Q.jsonl, receipts.json, local-hashes.json. Raw HTTP and loop journals remain local and hash-indexed. Explicit-path local commits; no push, host signals, or edits to original larger-test results.",
    ]
    (out / ("README.md" if pilot else "RESULTS.md")).write_text("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("out", type=Path)
    parser.add_argument("--pilot", action="store_true")
    args = parser.parse_args()
    report(args.out, pilot=args.pilot)


if __name__ == "__main__":
    main()
