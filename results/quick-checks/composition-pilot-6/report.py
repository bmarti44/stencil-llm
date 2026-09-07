"""Saved-record pilot6 diagnostics and reviewable report; no generation."""

import collections
import json
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent
PIN = Path("/tmp/stencil-pilot6-pinned")


def main():
    sys.path[:0] = [str(PIN / "src"), str(PIN / "scripts")]
    import composition_pilot5 as d

    s = d.s
    summary = json.loads((OUT / "summary.json").read_text())
    phase = summary["phase"]
    n = summary["n_rounds"]
    rows = [
        json.loads(x) for x in (OUT / f"{phase}-records.jsonl").read_text().splitlines()
    ]
    episodes = {e.episode_id: e for e in s.bank(n_rounds=n)}
    starts = {
        eid: next(
            t.index
            for t in e.turns
            if any(v.key == "indent" and v.action == "supersedes" for v in t.events)
        )
        for eid, e in episodes.items()
    }
    index = {(r["episode_id"], r["turn"], r["arm"]): r for r in rows}
    comparisons = {}
    for match_arms in ("RNTQ", "RNT", "RNTQO"):
        cells = [
            (eid, j)
            for eid in episodes
            for j in range(n)
            if all(
                (eid, j, a) in index and s.file_written(index[eid, j, a])
                for a in match_arms
            )
        ]
        table = {}
        for scope in ("all_matched", "post_indent_change"):
            selected = [
                (eid, j)
                for eid, j in cells
                if scope == "all_matched" or j >= starts[eid]
            ]
            table[scope] = dict(cells=len(selected), traits={})
            for k in s.TRAITS:
                table[scope]["traits"][k] = {
                    a: dict(
                        passed=sum(
                            index[eid, j, a]["outcome"]["satisfied"][k]
                            for eid, j in selected
                            if index[eid, j, a]["outcome"]["applicable"][k]
                        ),
                        total=sum(
                            index[eid, j, a]["outcome"]["applicable"][k]
                            for eid, j in selected
                        ),
                    )
                    for a in "RNT"
                }
        comparisons[match_arms] = table
    summary["matched_cells"] = comparisons
    summary["pilot5_prior"] = dict(
        scope="R/N/T matched post-change indent",
        R=dict(passed=0, total=9),
        N=dict(passed=8, total=9),
        T=dict(passed=8, total=9),
    )
    for a, v in summary["per_arm"].items():
        rr = [r for r in rows if r["arm"] == a]
        v["relapse_by_trait"] = {
            k: dict(
                numerator=sum(
                    s.file_written(r) and r["outcome"]["raw_relapse"][k] for r in rr
                ),
                denominator=sum(
                    s.file_written(r) and r["outcome"]["trait_denominators"][k]
                    for r in rr
                ),
                prior_trait_present_denominator=sum(
                    s.file_written(r)
                    and r["outcome"]["trait_denominators"][k]
                    and r["outcome"]["prior_trait_present"][k]
                    for r in rr
                ),
            )
            for k in s.TRAITS
        }
        v["relapse_by_kind"] = {
            kind: {
                field: sum(
                    v["relapse_by_trait"][k][field]
                    for k in s.TRAITS
                    if s.TRAITS[k] == kind
                )
                for field in (
                    "numerator",
                    "denominator",
                    "prior_trait_present_denominator",
                )
            }
            for kind in sorted(set(s.TRAITS.values()))
        }
        v["execution_categories"] = dict(
            collections.Counter(r["execution"].get("category", "written") for r in rr)
        )
        v["output_tokens"] = sum(r["output_tokens"] for r in rr)
        v["largest_reply"] = max((r["output_tokens"] for r in rr), default=0)
        v["reference_tokens"] = sum(
            len(s.qwen_encode(s.reference(episodes[r["episode_id"]], r["turn"])))
            for r in rr
        )
        v["model_reference_x"] = (
            v["output_tokens"] / v["reference_tokens"]
            if v["reference_tokens"]
            else None
        )
        v["final_success"] = (
            sum(
                s.file_written(r)
                and r["outcome"]["integration"]
                and r["outcome"]["report_ok"]
                and not any(
                    r["outcome"]["diagnostics"][k]
                    for k in (
                        *summary["floor"]["eligible_traits"],
                        "breakage",
                        "wrong_family",
                    )
                )
                for r in rr
                if r["turn"] == n - 1
            )
            if summary["floor"]
            else None
        )
    summary["r_final_failures"] = [
        dict(
            episode_id=r["episode_id"],
            integration=r["outcome"]["integration"],
            report_ok=r["outcome"]["report_ok"],
            failed_checks=[
                k
                for k in (
                    *summary["floor"]["eligible_traits"],
                    "breakage",
                    "wrong_family",
                )
                if r["outcome"]["diagnostics"][k]
            ],
        )
        for r in rows
        if r["arm"] == "R" and r["turn"] == n - 1
    ]
    summary["lifecycle"] = json.loads((OUT / "lifecycle.json").read_text())
    summary["determinism"] = json.loads((OUT / "determinism.json").read_text())
    summary["audit"] = json.loads((OUT / "audit.json").read_text())
    summary["q_qualified"] = [
        eid
        for eid in episodes
        if all(
            (eid, j, "Q") in index and index[eid, j, "Q"]["outcome"]["success"]
            for j in range(n)
        )
    ]
    if summary["floor"]:
        summary["strict_floor_sensitivity"] = {
            k: dict(
                passed=sum(
                    s.file_written(r) and r["outcome"]["satisfied"][k]
                    for r in rows
                    if r["arm"] == "T"
                    and r["outcome"]["applicable"][k]
                    and (k != "indent" or r["turn"] >= starts[r["episode_id"]])
                ),
                total=v["total"],
            )
            for k, v in summary["floor"]["traits"].items()
        }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    registration = (OUT / "registration.md").read_text()
    lines = [
        f"# Composition pilot 6 — {summary['reading']}",
        "",
        "**Failing gates:** " + ("; ".join(summary["failures"]) or "none") + ".",
        "",
        f"Completed phase: {phase}, {n} rounds, {len(rows)} saved records. Q qualified {len(summary['q_qualified'])}/8. DEV diagnostics only; no fitting or larger-bank execution.",
        "",
        "| Arm | Round0 not written | Lanes executing | Written rounds | Caps | Final success | Model/reference x |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for a in "RNTQO":
        v = summary["per_arm"][a]
        lines.append(
            f"| {a} | {v['round0_format_failures']}/8 | {v['executing_lanes']}/8 | {v['executed_rounds']}/{8 * n} | {v['caps']}/{v['rounds']} | {v['final_success']}/8 | {v['model_reference_x']:.3f} |"
        )
    lines += [
        "",
        "A lane executes when at least one round parses its trailer and writes its file. Per-round execution remains separately reported and gated at90% by this task. Caps, syntax/depth errors and failed writes do not execute. Final success uses the complete frozen T floor; Q qualification instead requires every fresh task to pass all traits. Q final-row success in the table is not Q qualification. Model output includes EOS, reference denominator excludes EOS, matching pilot5 reporting.",
        "",
        "| T trait / kind | Pinned satisfied/applicable | Strict written satisfied/applicable | Qualifies (both) | Opportunity episodes |",
        "|---|---:|---:|---|---:|",
    ]
    if summary["floor"]:
        for k, v in summary["floor"]["traits"].items():
            lines.append(
                f"| {k} / {s.TRAITS[k]} | {v['passed']}/{v['total']} | {summary['strict_floor_sensitivity'][k]['passed']}/{v['total']} | {v['eligible']} | {len(v['opportunity_episodes'])} |"
            )
    lines += [
        "",
        "Indent floor counts applicable rounds at/after the registered first supersede, including reinstatement. Other denominators retain Amendment3 semantics. The pinned checker marks the syntax-error T reply observed and counts its format satisfaction:23/35. Strict written accounting treats that attempt as a failure:22/35. Both pass; all other counts and the eligible-trait set are identical. The gate reading is unchanged under strict accounting. Only indent/style and delivery/process count toward the two-substitution-kind gate.",
        "",
        "**Matched-cell diagnostic.** Pilot5 prior post-change indent: R0/9 vs N8/9 vs T8/9. Matching conditions on execution and is descriptive, not a causal estimate.",
        "",
        "| Matching arms / scope | Cells | Trait | R satisfied/applicable | N | T |",
        "|---|---:|---|---:|---:|---:|",
    ]
    for match in ("RNTQ", "RNT"):
        for scope, table in comparisons[match].items():
            for k, v in table["traits"].items():
                ratios = [f"{v[a]['passed']}/{v[a]['total']}" for a in "RNT"]
                lines.append(
                    f"| {match} / {scope} | {table['cells']} | {k} | {' | '.join(ratios)} |"
                )
    lines += [
        "",
        "All-five-arm matched cells also appear in summary.json. Post-change scope uses each DEV episode’s actual first indent supersede; per-trait applicability is then applied. Zero denominators are unmeasured.",
        "",
        "| Arm | Kind | Relapse / executed-trait opportunities | Prior trait present |",
        "|---|---|---:|---:|",
    ]
    for a in "RNTQO":
        for kind, v in summary["per_arm"][a]["relapse_by_kind"].items():
            lines.append(
                f"| {a} | {kind} | {v['numerator']}/{v['denominator']} | {v['prior_trait_present_denominator']} |"
            )
    p = summary["projected_gpu_hours"]
    life = summary["lifecycle"]
    lines += [
        "",
        "Kind totals sum trait-opportunity cells; each denominator requires a written file and the checker’s retirement opportunity. The numerator additionally requires the prior trait to have appeared. Trait-level counts and original raw checks remain in summary and records. Q has fresh gold prerequisite files, so its prior-history witness can differ from trajectory arms.",
        "",
        f"**Measured larger-test projection: {p:.6f} GPU-h.**"
        if p
        else "**Measured projection: incomplete.**",
        f"GPU held {life['gpu_held_seconds']:.3f}/9000s; startup {summary['load_seconds']:.3f}s. Formula `(load + 1.25*(64*(R+N+Q)+16*(O+T)))/3600`. All five costs measured from fixed same-arm C4 groups, with phase overhead allocated equally. Startup charged once; all pilot replay and cleanup time is included in the9000s actual budget. Prior development cost is excluded from this task’s registered projection.",
    ]
    if (OUT / "fallback.json").exists():
        lines += ["", "Fallback status: " + (OUT / "fallback.json").read_text().strip()]
    elif p and p > 15:
        lines += ["", "Projection >15h: stopped, no fallback."]
    elif p and p <= 12:
        lines += ["", "The (12,15]h fresh12-round fallback was not triggered."]
    lines += [
        "",
        f"Determinism: D={len(summary['determinism']['mismatches'])}/8, exact body token IDs/EOS/cap across forward/reverse C4. Saved-response CPU audit: {sum(v['replayed_records'] for v in summary['audit']['phases'].values())} replies, zero payload or record mismatches. Own container and flag absent; no host process signals or push.",
        "",
        "Artifacts: [summary](summary.json), [records](main-records.jsonl), [audit](audit.json), [HTTP hash index](journals-index.jsonl), [local hashes](local-hashes.json), [server log](server.log), [launcher](run.py). HTTP bodies and workspace/loop journals are local, out of git. Compact records are below10MB.",
        "",
        "---",
        "",
        registration,
    ]
    lines[4:4] = [
        "R final failures: all8 fail the indent check,6 fail format, and3 also have breakage/integration failures. These checker categories overlap; an indent failure does not by itself identify its cause. The single non-write is T DEV04 turn12 (syntax_error). All round0 replies parsed and wrote files.",
        "",
    ]
    (OUT / "README.md").write_text("\n".join(lines).rstrip() + "\n")
    print(
        json.dumps(
            dict(
                reading=summary["reading"],
                failures=summary["failures"],
                projection=p,
                records=len(rows),
            )
        )
    )


if __name__ == "__main__":
    main()
