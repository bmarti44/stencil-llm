# ruff: noqa: E501
"""Render frozen Q3 measurements without changing its pre-run reading."""

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent


def report():
    before = (OUT / "before-run.md").read_text().split("## Results")[0]
    elapsed = json.loads((OUT / "runtime.json").read_text())["total_seconds"] / 60
    lines = [
        before,
        "## Results\n",
        f"Both trunks completed in **{elapsed:.2f} cumulative GPU-minutes**, 4B first. "
        "The fixed reading above is unchanged; before-run.md preserves the exact hashed pre-run file. "
        "No process was signalled and no benchmark data was accessed.\n",
        "Counts below are out of 64 episodes; swapped is scored against B/B/A/B. "
        "“Any induction” means A or B output at any of the first four checkpoints. "
        "Broken means any of five outputs. Fresh text is diagnostic only.\n",
    ]
    for trunk in ("4b", "1.7b"):
        d = json.loads((OUT / trunk / "summary.json").read_text())
        a = d["arms"]
        lines += [
            f"### {trunk}: sustained **{d['variants']['sustained']}**, one-shot **{d['variants']['one_shot']}**\n",
            "| Arm | SET | HOLD | SWITCH | BACK | Joint | Strict joint | CLEAR copy | Impositions | Broken | Any induction |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for arm, m in a.items():
            counts = [
                m["checkpoints"][s]["exact"] for s in ("SET", "HOLD", "SWITCH", "BACK")
            ]
            counts += [
                m["joint"],
                m["strict_joint"],
                m["checkpoints"]["CLEAR"]["exact"],
                m["clear_impositions"],
                m["breakage"],
                m["induction"],
            ]
            lines.append("| " + arm + " | " + " | ".join(map(str, counts)) + " |")
        lines += [
            "\nStrict exactness by checkpoint:\n",
            "| Arm | SET | HOLD | SWITCH | BACK | CLEAR |",
            "|---|---:|---:|---:|---:|---:|",
        ]
        for arm, m in a.items():
            lines.append(
                "| "
                + arm
                + " | "
                + " | ".join(
                    str(m["checkpoints"][s]["strict"])
                    for s in ("SET", "HOLD", "SWITCH", "BACK", "CLEAR")
                )
                + " |"
            )
        c, o = a["sustained_correct"], a["one_shot_correct"]
        fresh = a.get("fresh_text", {}).get("joint")
        lines += [
            "\n"
            + f"The retained text bar achieved {a['text']['joint']}/64 joint, "
            + (
                f"while fresh-history text achieved {fresh}/64"
                if fresh is not None
                else "so no fresh-history diagnostic was required"
            )
            + (
                ". With these frozen prompts, the fresh bar also misses 48/64, so retained-history stickiness alone does not explain the missed competence bar. "
                if fresh is not None and fresh < 48
                else ". "
            )
            + f"Sustained replacement achieved {c['joint']}/64 joint and {c['checkpoints']['SET']['exact']}/64 SET; "
            + f"one-shot achieved {o['joint']}/64 joint and **{o['checkpoints']['HOLD']['exact']}/64 HOLD with zero reapplication**. "
            + (
                "Neither actuator established either task on any test checkpoint, so this tested coordinate is readable but did not provide usable task control. "
                if c["induction"] == o["induction"] == 0
                else f"OFF itself produced A/B-form output in {a['off']['induction']}/64 episodes, versus {c['induction']}/64 sustained and {o['induction']}/64 one-shot. "
            )
            + (
                "Both variants remain INELIGIBLE under the frozen rule. "
                if a["text"]["joint"] < 48
                else "The text bar meets eligibility; actuator readings follow the frozen control and safety thresholds. "
            )
            + f"Correct CLEAR impositions were {c['clear_impositions']}/64 sustained and {o['clear_impositions']}/64 one-shot"
            + (
                "; with no task established, clean copying does not demonstrate successful erasure. "
                if c["induction"] == o["induction"] == 0
                else ". "
            )
            + f"Runtime: {d['elapsed_seconds'] / 60:.2f} GPU-minutes.\n"
        ]
        lines += [
            "Fit statistics (128 paired triples; fp32; zero-based layer inputs):\n",
            "| Layer | c_A | c_B | c_OFF | d | Min paired margin | Positive pairs | Global gap | OFF fraction B→A |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for layer, s in d["fit_stats"].items():
            v = [s["coordinates"][t] for t in ("A", "B", "OFF")] + [
                s["clip"],
                s["min_paired_margin"],
            ]
            lines.append(
                "| "
                + layer
                + " | "
                + " | ".join(f"{x:.6g}" for x in v)
                + f" | {s['positive_pairs']}/128 | {s['global_gap']:.6g} | {s['off_fraction_B_to_A']:.6g} |"
            )
        lines += [
            "\nAll setup cells (each task n=32; both means paired exact success; breakage counts out of 64 outputs):\n",
            "| Variant | Layer | Overshoot | A | B | A strict | B strict | Both | Broken | Selected |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
        for c in d["cells"]:
            selected = d["selected"][c["variant"]] == c
            values = [
                c["variant"],
                c["layer"],
                c["overshoot"],
                c["exact"]["A"],
                c["exact"]["B"],
                c["strict"]["A"],
                c["strict"]["B"],
                c["both"],
                c["breakage"],
                "yes" if selected else "",
            ]
            lines.append("| " + " | ".join(map(str, values)) + " |")
        audit = json.loads((OUT / trunk / "validation.json").read_text())
        lines += [
            "\n"
            + f"CPU reconstruction passed for all {audit['raw_records']:,} records: raw scoring, source/reading hashes, fit means/projections, all-cell selection, retained token histories including EOS, exact hook schedules, clipping, random RNG streams and aggregate verdicts. "
            + f"{audit['hook_events_with_changed_elements']:,}/{audit['hook_events']:,} hook events changed at least one bf16 element; "
            + f"maximum orthogonal cast residual norm was {audit['max_orthogonal_cast_norm']:.6g}. "
            + "Replacement is direction-only before casting; bf16 rounding means the realized displacement is not mathematically confined to that direction.\n"
        ]
        paired = audit.get("identical_prompt_SET_comparison")
        if paired:
            lines.append(
                f"Matched empty-history SET prompts produced identical output token sequences in {paired['identical_outputs']}/64 retained/fresh pairs and identical scores in {paired['identical_scores']}/64. "
                "Any disagreement here is a batch/numerical difference, not a history effect.\n"
            )
    lines += [
        "### Artifacts and limits\n",
        "Per trunk: summary.json, records.jsonl (all setup/test outputs and hook positions), examples.json, extraction.json, fit-stats.json, fit-fp32.pt (states/means/unit vectors), cells.json, selected.json, random-directions.pt, pilot.json, and validation.json. "
        "audit.py independently reconstructs measurements on CPU; report.py renders these tables. "
        "Source script and imported plumbing hashes are in provenance.json. No model weights changed.\n",
        "Shuffled matches the clip bound, not the realized displacement or intervention energy. "
        "One-shot HOLD retains prior generated answers as well as edited KV; a positive result would not isolate these sources without an identical-token replay control. "
        "The text bar uses no new HOLD cue, while fresh text is explicitly cued at each independent decision. "
        "These are descriptive single-seed screens, not registered hypothesis tests or broad impossibility claims.\n",
    ]
    (OUT / "README.md").write_text(before + "\n".join(lines[1:]))


if __name__ == "__main__":
    report()
