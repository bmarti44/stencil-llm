# ruff: noqa: E501
"""Saved DEV reporting only; no model execution or endpoint changes."""

import json
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent
PIN = Path("/tmp/stencil-pilot7-pinned")


def main():
    sys.path[:0] = [str(PIN / "src"), str(PIN / "scripts")]
    from stencil.focus import slab2 as s
    from stencil.focus import slab2_endpoint as ep

    summary = json.loads((OUT / "main-summary.json").read_text())
    rows = [
        json.loads(x) for x in (OUT / "main-records.jsonl").read_text().splitlines()
    ]
    episodes = s.bank()
    fixture = json.loads(
        (PIN / "tests/fixtures/slab2_pilot6_registers.json").read_text()
    )
    cells = {(r["episode_id"], r["turn"]) for r in fixture["rows"] if r["matched"]}
    recomputed = ep.pilot_reading(
        rows,
        episodes,
        ep.strict_floor(rows),
        ep.projection(summary["lane_seconds"], summary["load_seconds"]),
        cells,
        deterministic=True,
    )
    for key, value in recomputed.items():
        assert summary[key] == value, key
    life = json.loads((OUT / "lifecycle.json").read_text())
    assert life["gpu_held_seconds"] <= 5400
    for a, m in summary["per_arm"].items():
        rr = [r for r in rows if r["arm"] == a]
        m["joint_final_descriptive"] = sum(
            s.file_written(r)
            and r["outcome"]["integration"]
            and r["outcome"]["report_ok"]
            and not any(
                r["outcome"]["diagnostics"][k]
                for k in (*s.TRAITS, "breakage", "wrong_family")
            )
            for r in rr
            if r["turn"] == 15
        )
        m["breakage_episodes_descriptive"] = sum(
            any(
                r["outcome"]["diagnostics"]["breakage"]
                for r in rr
                if r["episode_id"] == e.episode_id
            )
            for e in episodes
        )
        cc = [r for r in rr if r["outcome"]["applicable"]["format"]]
        m["all_compact"] = dict(
            total=len(cc),
            ready_emissions=sum("delivery=ready" in r["output"] for r in cc),
            format_adherence=sum(
                s.file_written(r) and r["outcome"]["satisfied"]["format"] for r in cc
            ),
        )
        m["max_prompt"] = max(r["prompt_tokens"] for r in rr)
        m["output_tokens"] = sum(r["output_tokens"] for r in rr)
        m["reference_tokens"] = sum(
            len(s.qwen_encode(s.reference(e, r["turn"])))
            for r in rr
            for e in episodes
            if e.episode_id == r["episode_id"]
        )
        m["model_reference_x"] = m["output_tokens"] / m["reference_tokens"]
    summary["gpu_held_seconds"] = life["gpu_held_seconds"]
    summary["joint_final_status"] = "descriptive only, never a gate"
    summary["data_lineage"] = (
        "fit-on none; evaluated-on eight authored DEV episodes only"
    )
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    c = summary["compact_control"]
    lines = [
        f"# Composition pilot 7 — {summary['reading']}",
        "",
        "Fit-on: none. Evaluated-on: eight authored DEV episodes; no benchmark or larger-bank model execution.",
        "",
        (
            "The larger 64-episode test is authorized on the per-obligation change-round endpoint; it was not launched."
            if summary["reading"] == "ELIGIBLE"
            else "Failing items: "
            + ", ".join(summary["failures"])
            + ". The larger test is not authorized by this re-pilot."
        ),
        "",
        f"Fixed pilot-6 compact control: R delivery=ready **{c['ready_emissions']}/34** (limit2), format adherence **{c['format_adherence']}/34** (minimum26). These are the same34 cells, without outcome-dependent rematching. CPU re-render control: contradiction removed on all34 matched and all35 scheduled compact registers.",
        "",
        "| Arm | Written | Round0 written | Executing lanes | Caps | All35 compact format | All35 ready emissions | Joint final (descriptive) | Breakage episodes (descriptive) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for a, m in summary["per_arm"].items():
        cc = m["all_compact"]
        lines.append(
            f"| {a} | {m['executed_rounds']}/128 | {m['round0_executing_lanes']}/8 | {m['executing_lanes']}/8 | {m['caps']}/128 | {cc['format_adherence']}/{cc['total']} | {cc['ready_emissions']}/{cc['total']} | {m['joint_final_descriptive']}/8 | {m['breakage_episodes_descriptive']}/8 |"
        )
    lines += [
        "",
        "Primary: per-obligation change-round adherence conditional on paired parsed writes. Changes within an episode are averaged before one episode sign enters the exact one-sided R>N test; Holm across three families. Nonwrites are reported, with failed-attempt sensitivity in summary.json. DEV significance is descriptive and does not gate eligibility.",
        "",
        "| Obligation | R adhered/written changes | N | T | Q | Paired episodes | R wins / N wins | One-sided p | Holm p |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for k, f in summary["primary"]["families"].items():
        counts = {
            a: f"{sum(e['satisfied'][a] for e in f['episodes'])}/{sum(e['written_denominators'][a] for e in f['episodes'])}"
            for a in ep.ARMS
        }
        lines.append(
            f"| {k} | {counts['R']} | {counts['N']} | {counts['T']} | {counts['Q']} | {f['n']} | {f['wins']} / {f['losses']} | {f['p']:.6f} | {f['holm_p']:.6f} |"
        )
    lines += [
        "",
        f"Computable endpoint: {summary['primary']['computable_families']}/3 families in >=6 episodes; {summary['primary']['computable_episodes']}/8 episodes each have >=2 measured families.",
        "",
        "| Strict T floor | Satisfied/applicable | Eligible | Retirement-opportunity episodes |",
        "|---|---:|---|---:|",
    ]
    for k, f in summary["floor"]["traits"].items():
        lines.append(
            f"| {k} | {f['passed']}/{f['total']} | {f['eligible']} | {len(f['opportunity_episodes'])} |"
        )
    lines += [
        "",
        "Floor uses all scheduled T attempts, nonwrites as failures; indent counts at/after first supersede including reinstatement. Style and language adherence are independent of runtime/semantic breakage. delivery_scope is removed from every arm. Joint final uses the same four traits for all arms and is descriptive only.",
        "",
        "Q is a **fresh-context reference**, using gold prerequisite files without feedback, not a capability ceiling. O is omitted: its rendering is byte-identical to R; pilot6 already recorded128/128 identical outputs. That replication cost0.587 projected GPU-h.",
        "",
        f"Measured larger-test projection: **{summary['projected_gpu_hours']:.2f} GPU-h** (limit12). Formula `(load+1.25*(64*(R+N+Q)+16*T))/3600`; fixed same-arm C4 lane allocations, startup once. Pilot6's identical R/O timing spread suggests roughly4% timing noise; unrounded measurements decide the gate.",
        "",
        f"Actual GPU-held: {life['gpu_held_seconds']:.1f}/5400s including startup, determinism and cleanup. Startup {summary['load_seconds']:.1f}s. Determinism D=0/8, exact body IDs/EOS/cap under forward/reverse C4. Max prompt+cap: {max(m['max_prompt'] for m in summary['per_arm'].values())}+2048 <=32768.",
        "",
        f"Pinned CPU-green SHA: `{summary['pinned_sha']}`; isolated `{PIN}`. Required CPU suite and CLI smoke passed before GPU launch. Saved-response audit verifies all512 prompts/payloads and record fields; own container and flag removed. No host process signals or push.",
        "",
        "Artifacts: [summary](summary.json), [records](main-records.jsonl), [saved-response audit](audit.json), [registration](registration.md), [CPU validation](cpu-validation.log), [determinism](determinism.json), [lifecycle](lifecycle.json), [local hashes](local-hashes.json). Records are below10MB; full HTTP and loop journals are local and hash-indexed.",
    ]
    (OUT / "README.md").write_text("\n".join(lines) + "\n")
    print(
        json.dumps(
            dict(
                reading=summary["reading"],
                compact=c,
                projection=summary["projected_gpu_hours"],
            )
        )
    )


if __name__ == "__main__":
    main()
