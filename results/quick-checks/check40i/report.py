#!/usr/bin/env python3
"""Render check40i from audited records; independently recount the fixed reading."""

import ast
import json
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent
ARMS = ("Z", "Zc", "S", "OFF")
STEPS = (
    "SET",
    "HOLD",
    "SWITCH",
    "HOLD_AFTER_SWITCH",
    "BACK",
    "HOLD_AFTER_BACK",
    "CLEAR",
)


def main():
    summary = json.loads((OUT / "summary.json").read_text())
    audit = json.loads((OUT / "audit.json").read_text())
    rows = [
        json.loads(line) for line in (OUT / "records.jsonl").read_text().splitlines()
    ]
    assert len(rows) == summary["records"] == audit["records"]
    bank = {(r["arm"], r["episode"], r["step"]): r for r in rows}
    assert len(bank) == len(rows)
    counts = {}
    for a in ARMS:
        counts[a] = {}
        for s in STEPS:
            cell = [r for r in rows if r["arm"] == a and r["step"] == s]
            count = Counter(r["score"]["valid_language"] or "broken" for r in cell)
            counts[a][s] = dict(count)
            assert count["broken"] == summary["arms"][a][s]["broken"]
            for lang in ("JavaScript", "Python"):
                assert count[lang] == summary["arms"][a][s]["valid"].get(lang, 0)

    def pairs(sequence):
        return sum(
            all(
                ("Z", e, s) in bank
                and bank["Z", e, s]["score"]["valid_language"] == lang
                for s, lang in sequence
            )
            for e in range(24)
        )

    switch_sequence = (
        ("SET", "JavaScript"),
        ("HOLD", "JavaScript"),
        ("SWITCH", "Python"),
    )
    clear_sequence = (
        ("BACK", "JavaScript"),
        ("HOLD_AFTER_BACK", "JavaScript"),
        ("CLEAR", "Python"),
    )
    switch, clear = pairs(switch_sequence), pairs(clear_sequence)
    both = pairs(switch_sequence + clear_sequence)
    assert switch == summary["paired_switch_release"]["Z"]
    assert clear == summary["paired_reestablished_js_release"]["Z"]
    cells = [
        counts["Z"][s].get(lang, 0) >= 20 and counts["Z"][s].get("broken", 0) <= 2
        for s, lang in (
            ("SWITCH", "Python"),
            ("BACK", "JavaScript"),
            ("CLEAR", "Python"),
        )
    ]
    closed = (
        all(cells)
        and switch >= 20
        and clear >= 20
        and all(counts["Z"][s].get("broken", 0) <= 2 for s in STEPS)
        and all(counts[a]["BACK"].get("JavaScript", 0) <= 4 for a in ("Zc", "S"))
    )
    verdict = (
        "INCOMPLETE"
        if not summary["complete"]
        else "CLOSED-RELEASE"
        if closed
        else "PARTIAL"
        if any(cells)
        else "NOT"
    )
    assert verdict == summary["reading"]
    actual = [r for r in rows if "shared_from_generation" not in r]
    assert len(actual) == summary["generations"]
    assert (
        sum(len(r["generated_token_ids"]) for r in actual)
        == summary["generated_tokens"]
    )
    missing = []
    for r in rows:
        # Arithmetic replies contain no parenthesis-bearing string literals.
        if r["score"]["broken"] and r["text"].count("(") > r["text"].count(")"):
            missing.append(r)
    assert len(missing) == sum(
        len(d["missing_paren_episodes"])
        for a in summary["diagnostics"].values()
        for d in a.values()
    )
    # Independently parse all valid Python and missing-parenthesis defects.
    for r in rows:
        text = r["text"].strip()
        code = (
            "\n".join(text.splitlines()[1:-1])
            if text.startswith("```") and text.endswith("```")
            else text
        )
        if r["score"]["valid_language"] == "Python":
            ast.parse(code)
        elif r in missing:
            try:
                ast.parse(code)
            except SyntaxError:
                pass
            else:
                raise AssertionError("Missing-parenthesis diagnosis parsed as Python")
    independent = dict(
        reading=verdict,
        counts=counts,
        paired_switch=switch,
        paired_clear=clear,
        both_paired_releases=both,
        records=len(rows),
        actual_generations=len(actual),
        missing_paren_records=len(missing),
        missing_paren_actual_generations=sum(
            "shared_from_generation" not in r for r in missing
        ),
        all_python_reparsed=True,
    )
    (OUT / "independent-reading.json").write_text(
        json.dumps(independent, indent=2) + "\n"
    )
    lines = [
        f"**Result: {verdict}.**",
        "",
        f"Complete: {summary['complete']}; {summary['reason']}.",
        "",
        f"Z SWITCH Python {counts['Z']['SWITCH'].get('Python', 0)}/24; "
        f"BACK JS {counts['Z']['BACK'].get('JavaScript', 0)}/24; "
        f"CLEAR Python {counts['Z']['CLEAR'].get('Python', 0)}/24.",
        f"Paired real SWITCH releases {switch}/24; paired real CLEAR releases "
        f"{clear}/24; "
        f"both paired releases in the same episode {both}/24 (diagnostic).",
        f"Zc BACK JS {counts['Zc']['BACK'].get('JavaScript', 0)}/24; "
        f"S BACK JS {counts['S']['BACK'].get('JavaScript', 0)}/24.",
        f"Z CLEAR paired-release cases {clear}/24; "
        f"outside the paired criterion {24 - clear}/24.",
        "Z BACK miss episodes: "
        + str(
            [
                e
                for e in range(24)
                if ("Z", e, "BACK") in bank
                and bank["Z", e, "BACK"]["score"]["valid_language"] != "JavaScript"
            ]
        )
        + ".",
        "",
        "| Arm | Step | JS | Python | Broken | Coarse task | Fenced | Bare "
        "(valid) | Missing paren |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for a in ARMS:
        for s in STEPS:
            c = counts[a][s]
            d = summary["diagnostics"][a][s]
            coarse = sum(
                r["score"]["valid_task"]
                for r in rows
                if r["arm"] == a and r["step"] == s
            )
            lines.append(
                f"| {a} | {s} | {c.get('JavaScript', 0)} | {c.get('Python', 0)} | "
                f"{c.get('broken', 0)} | {coarse} | {d['fenced']} | "
                f"{d['bare']} ({d['bare_valid']}) | "
                f"{len(d['missing_paren_episodes'])} |"
            )
    lines += [
        "",
        "Every completed cell has denominator24; shared prefixes are logical "
        "arm records.",
        "Coarse task checks preserve the expression and parse syntax; code is "
        "not executed.",
        "",
        f"Frozen conditions: `{json.dumps(summary['passes'], sort_keys=True)}`.",
        "",
        f"Missing-parenthesis defects: {len(missing)} logical replies, "
        f"{independent['missing_paren_actual_generations']} actual generations, "
        f"{len({r['episode'] for r in missing})} distinct episodes.",
        f"Actual generations: fenced "
        f"{sum(r['fence_label'] != '(bare)' for r in actual)}, "
        f"bare {sum(r['fence_label'] == '(bare)' for r in actual)}, "
        f"ambiguous {sum(r['score']['language'] == 'ambiguous' for r in actual)}, "
        f"expression echoes {sum(r['expression_echo'] for r in actual)}, "
        f"OK replies {sum(r['text'].strip() == 'OK' for r in actual)}.",
    ]
    broken = [r for r in rows if r["score"]["broken"]]
    if broken:
        lines += [
            "",
            "Broken reply inventory (shared prefixes explicitly marked in records):",
            "",
        ]
        for r in broken:
            lines.append(
                f"- Episode{r['episode']} {r['arm']} {r['step']} {r['family']}: "
                f"`{json.dumps(r['text'])}`"
            )
    lines += [
        "",
        f"{len(rows)} records / {len(actual)} actual generations / "
        f"{summary['generated_tokens']} tokens; "
        f"truncated {sum(r['truncated'] for r in actual)}, cost-stopped "
        f"{sum(r['cost_stopped'] for r in actual)}.",
        f"GPU allocation wall cost including load/kernel/cleanup: "
        f"{summary['gpu_seconds']:.3f}/1800s "
        f"({summary['gpu_seconds'] / 60:.2f}/30min; "
        f"{summary['gpu_seconds'] / 3600:.4f} GPU-h). "
        f"Overrun {summary['cap_overrun_seconds']:.3f}s.",
        "",
        "CPU audit replays every score/token/history, bias digest, shared "
        "prefix, body mask,",
        "every forward and absolute position. Independent counts, paired "
        "verdict and Python",
        "parses agree. Recipe commit bb42c4e6 precedes inference; freeze hashes "
        "verified.",
        "No fitting, sealed input, signals, background launch, outcome retries "
        "or push.",
        "Own RUNNING.flag removed on natural completion.",
        "",
        "This reading concerns this fresh synthetic arithmetic language-syntax check.",
        "It does not establish general skill closure or autonomous maintenance. "
        "The Zc/S",
        "comparison isolates the BACK bias after identical masked prefixes; "
        "masks retain",
        "headers/closures and downstream KV. Prior40h PARTIAL remains unchanged.",
        "",
    ]
    prewritten = (OUT / "prewritten-reading.md").read_text()
    (OUT / "README.md").write_text(
        prewritten.replace("Results PENDING.", "\n".join(lines)).rstrip() + "\n"
    )
    print(json.dumps(independent))


if __name__ == "__main__":
    main()
