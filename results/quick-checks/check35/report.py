"""Render complete fixed-design tables from audited check-35 artifacts."""

# ruff: noqa: E501
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    s = json.loads((HERE / "4b/summary.json").read_text())
    assert s["status"] == "complete"
    assert json.loads((HERE / "4b/validation.json").read_text())["status"] == "passed"
    lines = [
        "\n## Results\n",
        f"Completed all 32 paired episodes in **{s['elapsed_seconds'] / 60:.2f}/45 GPU-minutes**; "
        f"**{s['records_count']:,} scored records**, with CLEAR variants branched from identical post-BACK caches.",
        "\n### SET through BACK (shared by each arm’s CLEAR variants)\n",
        "| Arm | Step | n | Target exact | Strict exact | A | B | Copy | Other | Breakage |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    defaults = {
        "S1": "c1",
        "S2": "c1",
        "S3": "c2",
        "S4": "c2",
        "S5": "c2",
        "TEXT": "text",
    }
    for arm, variant in defaults.items():
        for step in ("SET", "HOLD", "SWITCH", "BACK"):
            c = s["arms"][f"{arm}/{variant}"]["steps"][step]
            lines.append(
                f"| {arm} | {step} | "
                + " | ".join(
                    str(c[k])
                    for k in (
                        "n",
                        "exact",
                        "strict",
                        "A",
                        "B",
                        "OFF",
                        "other",
                        "breakage",
                    )
                )
                + " |"
            )
    lines += [
        "\n### CLEAR and subsequent neutral request\n",
        "c1 = restore all address slots; c2 = restore all slots plus answer eviction; "
        "c3 = append neutral OFF columns only. TEXT restores the initial slot and adds the real neutral sentence. "
        "The NEUTRAL request has no additional operation. All denominators are 32.",
        "\n| Arm / variant | Step | Copy exact | Strict copy | A | B | Other | Impositions (A+B) | Breakage |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for arm, a in s["arms"].items():
        for step in ("CLEAR", "NEUTRAL"):
            c = a["steps"][step]
            lines.append(
                f"| {arm} | {step} | {c['exact']} | {c['strict']} | {c['A']} | {c['B']} | {c['other']} | {c['A'] + c['B']} | {c['breakage']} |"
            )
    lines += [
        "\n### Fixed readings and joint outcomes\n",
        "| Arm / variant | SWITCH B | BACK A | Broken SWITCH/BACK episodes | Solves SWITCH | Solves CLEAR | Joint first five | Joint all six |",
        "|---|---:|---:|---:|---|---|---:|---:|",
    ]
    for arm, a in s["arms"].items():
        lines.append(
            f"| {arm} | {a['steps']['SWITCH']['exact']}/32 | {a['steps']['BACK']['exact']}/32 | {a['switch_back_broken_episodes']}/32 | {'YES' if a['solves_switch'] else 'NO'} | {'YES' if a['solves_clear'] else 'NO'} | {a['joint_five']}/32 | {a['joint_six']}/32 |"
        )
    control = s["arms"]["S4/c2"]["steps"]["SWITCH"]
    lines += [
        f"\nS4 release-only control: **{control['A']}/32 still A**, {control['B']}/32 B, {control['OFF']}/32 copy, {control['other']}/32 other. "
        f"Release interpretation: **{'VALID under the fixed control rule' if s['release_reading_valid'] else 'VOID under the fixed control rule'}**.",
        "\nA/B/copy/other are mutually exclusive; breakage is an overlapping flag. "
        "Joint first five requires exact A/A/B/A/copy, even for S4; joint all six also requires the second copy. "
        "The CLEAR rule measures absence of exact task imposition; copy and breakage columns expose cases where other outputs would meet that rule.",
        "\n### Conclusion\n",
        "**TEXT solves SWITCH; none of the cache arms solves SWITCH, and no arm solves CLEAR.** SET/HOLD remained positive at 29/32 and 31/32 in every arm. The S1 baseline reproduced check 34’s 3/32 SWITCH result, with 28/32 still A. A recent address alone (S2) switched 0/32: all 32 still produced A. Eviction plus original-address overwrite (S3) reached 12/32 SWITCH but only 18/32 BACK. Eviction plus a recent address (S5) reached 9/32 SWITCH and 30/32 BACK. TEXT reached 27/32 SWITCH and 29/32 BACK with one broken SWITCH/BACK episode, meeting the fixed rule. The S4 control retained A in 27/32 SWITCH requests and produced B in zero.\n\nRestoring filler plus evicting answers produced far fewer observed CLEAR impositions than restoration alone, but did not meet the two-request rule. S2/c2 had 3/32 impositions at CLEAR and **6/32 on the next neutral request**; S5/c2 had 3/32 then **5/32**. S3/c2 had **4/32** at CLEAR and 1/32 next, missing the initial limit. Appending OFF alone left 22–32/32 impositions at CLEAR and 23–32/32 next across S2/S3/S5. Joint exact SET+HOLD+SWITCH+BACK+CLEAR was best for S5/c2 at **8/32**, then S3/c2 at **3/32**; every other arm/variant was 0/32. Adding the second copy to the joint criterion leaves those counts unchanged.\n\nThese tested cache operations do not provide reliable switch-and-clear control. The observed reduction in sorting after answer eviction is consistent with prior answers contributing to persistence, but deleting answers does not remove every history carrier: retained query, assistant-header and other downstream K/V were computed under the old task. Recurrence on the second copy makes that limitation visible. The recent-slot result applies to the explicitly described operand-free system-prefix donor placed before the next user request; it does not rule out every possible address layout. CLEAR here targets copying through the same cue-absent Process request as check 34, without an explicit copy instruction.",
        "\n### Validation and scope\n",
        "The CPU audit recomputed all scores and summaries, checked fresh operand banks and exact prompts, "
        "replayed the specified interventions, and reconstructed absolute/physical positions, answer spans, "
        "token histories and their hashes for every episode and CLEAR fork. Runtime assertions checked raw "
        "bytes of every copied/appended address and every survivor of writes/evictions. HOLD checks made "
        "zero writes. Donor extraction tokens, destination-matched RoPE offsets, and raw bf16 packet "
        "hashes are recorded; donor tensors were held in memory and are not a persisted tensor archive.",
        "\nCPU tests covered check 34’s scorer and retained generation plus sparse-cache generation, append "
        "and eviction through the actual check-35 consumer. Lint and import-side-effect tests passed. "
        "The executed-script and prewritten-reading hashes are verified; the prewritten section is byte-preserved.",
        "\nArtifacts: [summary](4b/summary.json), [per-step records](4b/records.jsonl), "
        "[exact writes and evictions](4b/operations.jsonl), [donor provenance](4b/donors.jsonl), "
        "[lists](4b/episodes.json), [layout](4b/layout.json), [validation](4b/validation.json), "
        "[CPU audit](audit.py), [foreground log](4b/run.log).",
    ]
    p = HERE / "README.md"
    original = p.read_text().split("\n## Results\n")[0]
    p.write_text(original + "\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
