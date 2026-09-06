"""CPU-only report from frozen 40f records; no model invocation."""

import hashlib
import json
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent


def main():
    summary = json.loads((OUT / "summary.json").read_text())
    rows = [
        json.loads(line) for line in (OUT / "records.jsonl").read_text().splitlines()
    ]
    audit = json.loads((OUT / "audit.json").read_text())
    assert audit["records"] == len(rows)
    n = summary["episodes"]
    arms = summary["arms"]
    lines = [
        (OUT / "prewritten-reading.md")
        .read_text()
        .replace("Results PENDING.", "## Results"),
        f"**{summary['reading']}** ({n} episodes; pre-run resource fallback from32).",
        "",
        "**Masking was required in addition to the routing change for successful SWITCH in this comparison.** R2 produced valid Python23/24 at SWITCH and HOLD_AFTER_SWITCH (broken1 each); R1 bias-only produced Python0/24. R3 mask-only under unchanged JS bias produced Python0/24, JS18/24 and broken6/24 at SWITCH/CLEAR; this control does not establish clean JS maintenance. R4's neutral-period replacement failed: all24 replies at SWITCH/CLEAR were invalid period copies.",
        "",
        "**CLEAR meets the frozen output target but is not an independent JS-release success.** R2 CLEAR is valid Python24/24, broken0; its BACK restored JS0/24 (Python23, broken1). Consequently BACK->CLEAR is23 Python->Python plus1 broken->Python, with zero reestablished-JS cases. R2 shows the tested SWITCH benefit and satisfies the specified reading, but a fresh release-from-JS claim at CLEAR remains untested. Text+mask T switches/holds Python24/24 and restores JS24/24 at BACK, yet CLEAR is JS23/24 and broken1, Python0.",
        "",
        "R2 episode23 omitted a closing parenthesis at SWITCH, HOLD_AFTER_SWITCH and BACK, then returned valid Python at CLEAR. T episode19 CLEAR omitted the function keyword. Neither was token-capped. Breakage remains counted without repair. These are surface-syntax results on fresh arithmetic expressions, not general reversible computation control.",
        "",
        "| Arm | Step | N | Valid JS | Valid Python | Broken | Coarse task pass | Truncated | => | -> |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for arm in ("R1", "R2", "R3", "R4", "T"):
        for step in ("SET", "HOLD", "SWITCH", "HOLD_AFTER_SWITCH", "BACK", "CLEAR"):
            a = arms[arm][step]
            lines.append(
                f"| {arm} | {step} | {a['n']} | {a['valid'].get('JavaScript', 0)} | {a['valid'].get('Python', 0)} | {a['broken']} | {a['task_check']} | {a['truncated']} | {a['arrow_function_replies']} | {a['arrow_neighbour_replies']} |"
            )
    lines += [
        "",
        "Fixed combined-arm pass flags: "
        + json.dumps(summary["passes"], sort_keys=True)
        + ".",
        "",
    ]
    for arm in ("R1", "R2", "R3", "R4", "T"):
        counts = ", ".join(
            f"{s} Python{arms[arm][s]['valid'].get('Python', 0)}/{n}"
            for s in ("SWITCH", "HOLD_AFTER_SWITCH", "CLEAR")
        )
        lines.append(f"{arm}: {counts}.")
    lines += [
        "",
        "Interpretation: apply the fixed reading above without replacing it with a post-outcome criterion. Compare R2/R4 with the identical-prefix R1 to assess the added context intervention at SWITCH. R3 measures masking under sustained JS bias; its broken replies are failures, not evidence of successfully maintained JavaScript.",
        "The BACK->CLEAR transitions below determine whether CLEAR is an actual new release or already-Python persistence. A Python CLEAR following a failed JS BACK meets the frozen output-language target but does not independently demonstrate release from reestablished JS. Likewise, a high HOLD_AFTER_SWITCH rate co-occurs with retained Python answers and sustained bias.",
    ]
    fresh = summary["fresh_off"]
    lines += [
        "",
        f"Fresh OFF CLEAR default: Python{fresh['valid'].get('Python', 0)}/{n}, JS{fresh['valid'].get('JavaScript', 0)}/{n}, broken{fresh['broken']}/{n}.",
        "",
        "### Paired language transitions",
        "",
        "| Arm | Transition | Counts |",
        "|---|---|---|",
    ]
    for arm, stages in summary["transitions"].items():
        for stage, counts in stages.items():
            lines.append(f"| {arm} | {stage} | {json.dumps(counts, sort_keys=True)} |")
    lines += [
        "",
        "### Family and output diagnostics",
        "",
        "| Arm | Step | Family | Broken / N |",
        "|---|---|---|---:|",
    ]
    for arm, stages in arms.items():
        for step, values in stages.items():
            if step == "NEUTRAL":
                continue
            for family, counts in values["breakage_by_family"].items():
                lines.append(
                    f"| {arm} | {step} | {family} | {counts['broken']}/{counts['n']} |"
                )
    lines += [
        "",
        "| Arm | Step | First token | First three tokens | Fence labels |",
        "|---|---|---|---|---|",
    ]
    for arm, stages in arms.items():
        for step, values in stages.items():
            fields = [
                json.dumps(values[k], sort_keys=True)
                .replace("`", "&#96;")
                .replace("|", "&#124;")
                for k in ("first_tokens", "first_three_tokens", "fence_labels")
            ]
            lines.append(f"| {arm} | {step} | {' | '.join(fields)} |")
    neutral = {
        a: sum(
            r["text"].strip() == "OK"
            for r in rows
            if r["arm"] == a and r["step"] == "NEUTRAL"
        )
        for a in arms
    }
    flags = Counter(
        k
        for r in rows
        if r["step"] != "NEUTRAL"
        for k, v in r["score"]["flags"].items()
        if v
    )
    lines += [
        "",
        "Neutral literal OK counts (non-code; excluded from code breakage): "
        + json.dumps(neutral, sort_keys=True)
        + ".",
        "Scored breakage flags (includes shared prefix rows): "
        + json.dumps(flags, sort_keys=True)
        + ".",
        "",
        "### Execution and audit",
        "",
        f"{summary['generations']} actual generations, {summary['records']} arm records (shared prefixes identified), {summary['generated_tokens']} generated tokens. GPU allocation {summary['gpu_seconds']:.2f}s = {summary['gpu_seconds'] / 60:.2f}/90min including loading, kernel checks and cleanup; overrun{summary['cap_overrun_seconds']:.2f}s. Peak allocated{summary['peak_allocated_gib']:.2f}GiB. {summary['reason']}.",
        "",
        "Recipe committed at e570e74c before runtime launch; this is an unregistered disclosed quick check with a pre-generation Git anchor, not a registered benchmark. Nothing fit/trained or tuned. No sealed inputs, signals, background launches or push.",
        "",
        "Audit reconstructs every score, decoded output, actual retained token prefix, mask event, placeholder position/context, per-forward mask and absolute position, shared prefix, bias schedule, aggregate and fixed reading on CPU. Tiny real-model SDPA tests establish masked-K/V poisoning invariance and physical-eviction equivalence; retained-position and placeholder-column isolation pass. Runtime verifies raw linear router slot0 on all48 layers, changed expert dispatch, exact OFF logits and grouped_mm adoption. Import guard3 passed/1 known legacy xfail.",
        "",
        "The literal text history remains intact. R2/R3/T mask generated code-answer bodies; R4 substitutes neutral period K/V only in each original first body position, with the other body positions masked. Downstream K/V, user turns, empty think/header tokens, turn closures and neutral pairs remain. T also retains earlier explicit user language cues. Thus masking here is not a complete erasure of all historical language information. HOLD uses sustained bias and retained new answers; it does not isolate bias-only maintenance.",
        "",
        "Artifacts: [records](records.jsonl), [summary](summary.json), [audit](audit.json), [tasks](tasks.json), [frozen reading](prewritten-reading.md), [projection](projection.json), [freeze](freeze.json), [runtime](runtime.json), [kernel](kernel.json), [CPU checks](cpu.json), [resources](resources.json), [run log](run.log), [ledger](ledger.md), [inventory](artifact-inventory.json). `biases.pt`: CPU float32 js/python tensors [48,128], exactly40d alpha3 directions scaled from40b; no learned values.",
    ]
    (OUT / "README.md").write_text("\n".join(lines) + "\n")
    inventory = {
        p.name: dict(
            bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest()
        )
        for p in sorted(OUT.iterdir())
        if p.is_file() and p.name not in ("RUNNING.flag", "artifact-inventory.json")
    }
    (OUT / "artifact-inventory.json").write_text(
        json.dumps(inventory, indent=2, sort_keys=True) + "\n"
    )


if __name__ == "__main__":
    main()
