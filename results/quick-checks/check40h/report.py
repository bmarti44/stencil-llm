#!/usr/bin/env python3
"""Render the frozen closure result from audited check40h records."""

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent


def main():
    summary = json.loads((OUT / "summary.json").read_text())
    audit = json.loads((OUT / "audit.json").read_text())
    rows = [
        json.loads(line) for line in (OUT / "records.jsonl").read_text().splitlines()
    ]
    assert audit["records"] == len(rows) == summary["records"]
    prewritten = (OUT / "prewritten-reading.md").read_text()
    lines = [
        f"**Result: {summary['reading']}.**",
        "",
        f"Complete: {summary['complete']}; {summary['reason']}.",
        "",
        "| Arm | Step | JS | Python | Broken | Coarse task | Bare (valid) | "
        "Ambiguous / exact echoes |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for arm, steps in summary["arms"].items():
        for step, cell in steps.items():
            diag = summary["diagnostics"][arm][step]
            coarse = sum(
                r["score"]["valid_task"]
                for r in rows
                if r["arm"] == arm and r["step"] == step
            )
            lines.append(
                f"| {arm} | {step} | {cell['valid'].get('JavaScript', 0)} | "
                f"{cell['valid'].get('Python', 0)} | {cell['broken']} | "
                f"{coarse} | "
                f"{diag['bare']} ({diag['bare_valid']}) | "
                f"{len(diag['ambiguous_episodes'])} / "
                f"{len(diag['expression_echo_episodes'])} |"
            )
    lines += [
        "",
        "Every scheduled cell has denominator24. Coarse task means the unchanged",
        "parser plus expression-preservation check, not execution of generated code.",
        "",
        f"Frozen M conditions: `{json.dumps(summary['passes'], sort_keys=True)}`.",
        f"Paired BACK JS + HOLD_AFTER_BACK JS + CLEAR Python: "
        f"M {summary['paired_reestablished_js_release']['M']}/24, "
        f"Z {summary['paired_reestablished_js_release']['Z']}/24, "
        f"T′ {summary['paired_reestablished_js_release']['Tprime']}/24.",
        "",
        f"Fresh OFF CLEAR: {summary['fresh_off']['valid'].get('Python', 0)}/24 Python.",
        "",
    ]
    if summary["z_default_restored"]:
        lines += [
            "Z meets20/24 Python at SWITCH: masking plus removal of the old bias",
            "restores the DEFAULT without a new Python routing term. Any need for",
            "a new routing term is confined to the non-default direction; assess",
            "its reliability using M BACK and its breakage above.",
            "",
        ]
    else:
        lines += [
            "Z does not meet20/24 Python at SWITCH; masking plus OFF did not",
            "restore the default at the fixed descriptive bar.",
            "",
        ]
    lines += [
        "Fence loss and R3-style echoes are separate diagnostics, not unnamed",
        "parser failures. The table reports all bare outputs and bare valid outputs;",
        "ambiguous means both language parsers accept the extracted code.",
        "",
    ]
    for arm in summary["arms"]:
        for step in ("SWITCH", "BACK", "CLEAR"):
            d = summary["diagnostics"][arm][step]
            lines.append(
                f"- {arm} {step}: ambiguous episodes {d['ambiguous_episodes']}; "
                f"exact expression echoes {d['expression_echo_episodes']}; "
                f"OK replies {d['ok_episodes']}."
            )
    broken = [r for r in rows if r["score"]["broken"]]
    if broken:
        lines += [
            "",
            "Broken reply inventory (literal text; "
            "shared prefix records identified in JSONL):",
            "",
        ]
        for r in broken:
            flags = [k for k, v in r["score"]["flags"].items() if v]
            lines.append(
                f"- Episode{r['episode']} {r['arm']} {r['step']}, {r['family']}, "
                f"{flags}: `{json.dumps(r['text'], ensure_ascii=False)}`"
            )
    actual = [r for r in rows if "shared_from_generation" not in r]
    lines += [
        "",
        f"{summary['records']} records / {summary['generations']} actual generations / "
        f"{summary['generated_tokens']} generated tokens. Truncated actual generations "
        f"{sum(r['truncated'] for r in actual)}; cost-stopped "
        f"{sum(r['cost_stopped'] for r in actual)}.",
        f"GPU time including load/checks/cleanup: {summary['gpu_seconds']:.3f}/1800s "
        f"({summary['gpu_seconds'] / 60:.2f}/30min); "
        f"overrun {summary['cap_overrun_seconds']:.3f}s.",
        "",
        "Audit: every score/token/history/bias, shared prefix, cue span, mask event,",
        "prefill/decode/closure mask and absolute position replayed on CPU. Summary",
        "and fixed decision reconstructed. All48 raw router contracts and adopted",
        "grouped_mm/OFF equality checked in runtime artifacts. Frozen recipe",
        "`3f1a8aac` precedes inference. No fitting, sealed input, signal, background",
        "launch or push. RUNNING.flag removed after cleanup.",
        "",
        "Interpretation remains limited to these arithmetic surface-syntax tasks.",
        "All body masks retain headers/closures and stale downstream KV. T′ CLEAR",
        "also removes six complete cue-bearing user turns, including their requests;",
        "it therefore changes more prompt content than M/Z. HOLD co-occurs with",
        "current bias and visible new answers and does not isolate maintenance.",
        "",
    ]
    (OUT / "README.md").write_text(
        prewritten.replace("Results PENDING.", "\n".join(lines))
    )


if __name__ == "__main__":
    main()
