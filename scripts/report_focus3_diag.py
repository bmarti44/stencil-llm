"""Write descriptive diagnostic reports from saved records, without inference."""

from __future__ import annotations

from scripts import focus3_gate_diag as d


def table(headers, rows):
    return (
        "\n".join(
            [
                "| " + " | ".join(headers) + " |",
                "| " + " | ".join(["---"] * len(headers)) + " |",
                *["| " + " | ".join(map(str, row)) + " |" for row in rows],
            ]
        )
        + "\n"
    )


def escaped(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def rate(value, n):
    return "n/a" if value is None else f"{value}/{n}"


def run():
    summary = d.read(d.OUT / "summary.json")
    selection = d.read(d.OUT / "selection.json")
    effects = d.read(d.OUT / "false-admission-effects.json")
    assert summary["completion"] == "five arms and all exposed-row probes complete"
    n = selection["n"]
    projected_seconds = selection["alternatives"][str(n)]["total_seconds"]
    report = (d.OUT / "registration.md").read_text()
    report += "\n## Diagnostic observations — 2026-09-06\n\n"
    report += (
        f"All **{n} episodes × five arms × six requests = {n * 30} gate records** "
        "completed, plus 96 O setup records. No 48 fallback was needed. "
        f"O setup final success was {selection['O_setup_final_success']}/16; "
        "this was reported descriptively and did not select the cohort. "
        f"The pre-gate projection was {projected_seconds:.3f}s. "
        f"Actual GPU-held time was **{summary['gpu_held_seconds']:.3f}s "
        f"({summary['gpu_held_seconds'] / 60:.2f} minutes; "
        f"{summary['gpu_held_seconds'] / 3600:.3f} GPU-h)** of 7200s, including "
        "load, setup, classification, generation, probes and cleanup. "
        f"Peak PyTorch allocation was {summary['peak_gpu_bytes'] / 2**30:.3f}GiB.\n\n"
        "The registered v8 eligibility stop remains unmet. These are development "
        "diagnostics for admission-detector redesign, with no gate label assigned.\n\n"
    )
    report += (
        "C finished 57/64 episodes successfully, compared with O’s 63/64 and "
        "T’s 31/64. C was register-exact in 38/64 episodes. Its 25 false "
        "admissions occurred in 21 episodes; all were rendered at least once. "
        "C′ finished 58/64 successfully but was register-exact in 32/64, with "
        "seven extra unauthorized supersedes actions.\n\n"
        "In each candidate arm, seven of 25 false rows changed at least one "
        "answer when removed from the current recap: 11/110 exposed row-turns "
        "(10%), including 9/85 later-turn exposures. Five probes repaired task "
        "success and three lost success. These are conditional current-render "
        "effects, not the total effect of never admitting a row.\n\n"
    )
    headers = [
        "Arm",
        "Register exact",
        "Stale",
        "Final success",
        "False retirement",
        "False ADMISSION",
        "Breakage",
        "Contradictory recap",
    ]
    keys = [
        "exact",
        "stale",
        "final_success",
        "false_retirement",
        "false_admission",
        "broken",
        "contradictory",
    ]
    report += "### Episode readings\n\n"
    report += (
        "Each endpoint is an episode count, with every task answer included "
        "in register-exact. False retirement includes missing/changed gold "
        "rows and initial admission misses. False ADMISSION is a separate "
        "episode indicator; action counts appear below. N/T register "
        "endpoints are not applicable under the inherited v3 reading.\n\n"
    )
    for family in ("pooled", *d.g.FAMILIES):
        support = summary["family_support"][family]
        report += f"**{family} ({support} episodes)**\n\n"
        report += (
            table(
                headers,
                [
                    [arm]
                    + [
                        rate(summary["counts"][family][arm][key], support)
                        for key in keys
                    ]
                    for arm in d.ARMS
                ],
            )
            + "\n"
        )
    report += "### Unauthorized runtime actions\n\n"
    rows = []
    for family in ("pooled", *d.g.FAMILIES):
        arms = summary["unauthorized"][family]
        for arm, value in arms.items():
            rows.append(
                [
                    family,
                    arm,
                    value["applications"],
                    value["records"],
                    *[
                        value["per_label"].get(k, 0)
                        for k in (
                            "admit",
                            "supersedes",
                            "cancels",
                            "completes",
                            "reinstates",
                        )
                    ],
                ]
            )
    report += (
        table(
            [
                "Family",
                "Arm",
                "Actions",
                "Affected turns",
                "Admit",
                "Supersede",
                "Cancel",
                "Complete",
                "Reinstate",
            ],
            rows,
        )
        + "\n"
    )
    report += (
        "Actions are matched one-to-one to exact registered label, source "
        "span and target. False admissions are counted independently of "
        "false retirements; falsely retiring a spurious row is still an "
        "unauthorized action. Raw action details and pair confusions are "
        "in [summary.json](summary.json).\n\n"
    )
    report += "### Descriptive paired contrasts\n\n"
    rows = []
    for reference, values in summary["contrasts"].items():
        for endpoint in ("stale", "final_success", "broken"):
            v = values[endpoint]
            delta = v["c_minus_reference"]
            rows.append(
                [
                    f"C vs {reference}",
                    endpoint,
                    f"{delta:+d}",
                    f"{100 * delta / n:+.2f}pp",
                    rate(abs(delta), n),
                    v["c_only"],
                    v["reference_only"],
                ]
            )
    report += (
        table(
            [
                "Pair",
                "Endpoint",
                "C minus reference",
                "Difference",
                "Absolute distance",
                "C only",
                "Reference only",
            ],
            rows,
        )
        + "\n"
    )
    report += (
        "For stale/breakage a positive difference is worse; for final "
        "success it is better. Discordances are paired episodes, not "
        "population inference. The C-vs-O difference combines all runtime "
        "errors and their histories; it does not isolate admission alone.\n\n"
    )
    report += "### What false admissions did to answers\n\n"
    rows = []
    cost = {}
    for arm, values in effects["totals"].items():
        probes = [
            d.read(d.OUT / t["probe"]["path"])
            for case in effects["details"]
            if case["arm"] == arm
            for t in case["turns"]
            if t["probe"]
        ]
        cost[arm] = {}
        for key in ("success", "stale", "broken", "task", "constraint"):
            changes = [
                p["score_changes"][key] for p in probes if key in p["score_changes"]
            ]
            cost[arm][key] = dict(
                false_to_true=sum(
                    not v["original"] and v["without_row"] for v in changes
                ),
                true_to_false=sum(
                    v["original"] and not v["without_row"] for v in changes
                ),
            )
        rows.append(
            [
                arm,
                values["false_admissions"],
                values["categories"].get("one-shot payload request", 0),
                values["categories"].get("inert quote", 0),
                values["categories"].get("other", 0),
                values["exposed_row_turns"],
                values["completed_probes"],
                values["token_changes"],
                values["text_changes"],
                values["semantic_changes"],
                values["score_changes"],
                values["admissions_with_semantic_effect"],
            ]
        )
    report += (
        table(
            [
                "Arm",
                "False rows",
                "Payload requests",
                "Inert quotes",
                "Other",
                "Rendered row-turns",
                "Probes",
                "Token changes",
                "Text changes",
                "Semantic changes",
                "Score changes",
                "Rows with semantic effect",
            ],
            rows,
        )
        + "\n"
    )
    report += (
        table(
            [
                "Arm",
                "Endpoint",
                "Original false → without-row true",
                "Original true → without-row false",
            ],
            [
                [arm, key, v["false_to_true"], v["true_to_false"]]
                for arm, values in cost.items()
                for key, v in values.items()
            ],
        )
        + "\n"
    )
    report += (
        "Each probe removes one spurious row from the current recap and "
        "preserves the candidate’s exact original earlier user/assistant "
        "tokens. A semantic change compares parsed JSON values, falling "
        "back to stripped text on non-JSON replies; token/format changes "
        "are also reported separately. Multiple probes may concern the "
        "same answer, so row-turn counts are not independent answers. "
        "Success false→true identifies an immediate cost of that rendered "
        "row under the existing history; success true→false identifies an "
        "immediate benefit. These probes do not estimate the full causal "
        "effect of never admitting the row or changing prior history.\n\n"
        "Every case and downstream answer is in "
        "[false-admissions.md](false-admissions.md), with machine-readable "
        "[effects](false-admission-effects.json) and linked raw probe "
        "prompts/tokens/answers. All exposed-row probes completed; "
        "unrendered row-turns were logged without claiming no historical "
        "effect. Probe outputs never entered an arm’s history.\n\n"
    )
    category_rows = []
    for arm in ("C", "C'"):
        for category in ("one-shot payload request", "inert quote"):
            cases = [
                c
                for c in effects["details"]
                if c["arm"] == arm and c["category"] == category
            ]
            probes = [t["probe"] for c in cases for t in c["turns"] if t["probe"]]
            category_rows.append(
                [
                    arm,
                    category,
                    len(cases),
                    len(probes),
                    sum(p["semantic_changed"] for p in probes),
                    sum(bool(p["score_changes"]) for p in probes),
                ]
            )
    report += (
        table(
            [
                "Arm",
                "False-admission category",
                "Rows",
                "Probes",
                "Semantic changes",
                "Score changes",
            ],
            category_rows,
        )
        + "\n"
    )
    temporal = {}
    for arm in ("C", "C'"):
        temporal[arm] = {}
        for later in (False, True):
            turns = [
                t
                for case in effects["details"]
                if case["arm"] == arm
                for t in case["turns"]
                if t["probe"] and t["later_than_admission"] == later
            ]
            temporal[arm]["later turns" if later else "admission turn"] = dict(
                probes=len(turns),
                semantic_changes=sum(t["probe"]["semantic_changed"] for t in turns),
                score_changes=sum(bool(t["probe"]["score_changes"]) for t in turns),
            )
    report += (
        table(
            [
                "Arm",
                "Timing",
                "Exposed-row probes",
                "Semantic changes",
                "Score changes",
            ],
            [
                [
                    arm,
                    timing,
                    values["probes"],
                    values["semantic_changes"],
                    values["score_changes"],
                ]
                for arm, timings in temporal.items()
                for timing, values in timings.items()
            ],
        )
        + "\n"
    )
    d.g.write(d.OUT / "temporal-probe-summary.json", temporal)
    report += "### Runtime and history diagnostics\n\n"
    records = [d.read(p) for p in sorted((d.OUT / "gate/records").glob("*.json"))]
    runtime_rows = []
    for arm in d.ARMS:
        rr = [r for r in records if r["arm"] == arm]
        runtime_rows.append(
            [
                arm,
                sum(r["un_release"]["task_return"] for r in rr),
                sum(r["un_release"]["reactivated_output_columns"] for r in rr),
                sum(r["un_release"]["masked_columns"] for r in rr),
                sum(r["generation"]["eos"] is None for r in rr),
                sum(r["trace"].get("overflow", False) for r in rr),
                sum(r["trace"].get("admitted_beside_live", 0) for r in rr)
                if arm in ("C", "C'")
                else "n/a",
            ]
        )
    report += (
        table(
            [
                "Arm",
                "Task returns",
                "Reactivated own-output columns",
                "Masked columns",
                "Capped replies",
                "Classifier overflow turns",
                "Admitted beside live",
            ],
            runtime_rows,
        )
        + "\n"
    )
    report += (
        "Reactivated columns describe restored task applicability in the "
        "full history; no attention masking or mask un-release occurred. "
        "Admitted-beside-live includes legitimate rows and is separate "
        "from false admissions and contradictory recaps.\n\n"
    )
    parity = d.read(d.OUT / "setup-runtime-parity.json")
    assert parity["compared_records"] == parity["exact_trace_matches"] == 96
    assert not parity["mismatches"]
    report += (
        "All 96 newly recorded O-setup candidate traces exactly match the "
        "committed v8 CPU traces, including classifier outputs and actions "
        "([runtime parity](setup-runtime-parity.json)).\n\n"
    )
    report += "### Verification and artifacts\n\n"
    audit = d.read(d.OUT / "audit.json")
    independent = d.read(d.OUT / "independent-audit.json")
    report += (
        f"Saved-score runtime replay verified {audit['records']} gate records. "
        f"The second calculation checked {independent['token_sequences_checked']} "
        "full prompt/output token sequences and "
        f"{independent['classifier_softmax_checks']} "
        "raw-logit softmax vectors, reconstructed O/N/T rendering, matched "
        "traces to records and recomputed scores and resource selection. "
        "This was a separate calculation in the same agent session, not an "
        "independent reviewer. [Audit method](audit-method.md), "
        "[runtime audit](audit.json), [second calculation](independent-audit.json).\n\n"
        "Registration/source/checkpoint freeze commit 6041e2d7 precedes O setup. "
        "The frozen runtime and checkpoint hashes match. The foreground process "
        "removed its own RUNNING.flag on natural exit. No fitting, tuning, "
        "masking, process signals, termination, benchmark/sealed reads or push. "
        "Prior committed results stand.\n"
    )
    (d.OUT / "RESULTS.md").write_text(report)
    d.g.write(d.OUT / "probe-endpoint-changes.json", cost)
    cases = [
        "# Per-false-admission downstream effects\n",
        "Conditional current-recap probes; original arm histories remain fixed. "
        "For each turn, success/stale/broken is abbreviated S/T/B with 1=true.\n",
    ]
    for case in effects["details"]:
        row = case["row"]
        cases.append(f"## {case['episode']} · {case['arm']} · row {row['id']}\n")
        cases.append(
            f"Category: {case['category']}; P(rule)={case['probability_rule']:.10f}; "
            f"scope={row['scope']}; kind={row['kind']}.\n"
        )
        cases.append("Source: `" + escaped(row["text"]).replace("`", "\\`") + "`\n")
        rows = []
        for turn in case["turns"]:
            pp = turn["probe"]
            rows.append(
                [
                    turn["turn_index"],
                    turn["row_status"],
                    turn["rendered"],
                    f"{int(turn['score']['success'])}/{int(turn['score']['stale'])}/{int(turn['score']['broken'])}",
                    "not exposed"
                    if not turn["rendered"]
                    else "unmeasured"
                    if pp is None
                    else (
                        f"tokens={int(pp['token_changed'])}, "
                        f"semantic={int(pp['semantic_changed'])}"
                    ),
                    "" if pp is None else f"[raw probe]({pp['path']})",
                ]
            )
        cases.append(
            table(
                [
                    "Turn",
                    "Row status",
                    "Rendered",
                    "Original S/T/B",
                    "Changed without row",
                    "Record",
                ],
                rows,
            )
        )
        for turn in case["turns"]:
            ti = turn["turn_index"]
            cases.append(f"**Turn {ti} answers**\n")
            answers = [(case["arm"], turn["answer"], turn["score"])]
            answers += [
                (arm, r["answer"], r["score"]) for arm, r in turn["references"].items()
            ]
            if turn["probe"]:
                pp = d.read(d.OUT / turn["probe"]["path"])
                answers.append(
                    ("without this row", pp["generation"]["text"], pp["score"])
                )
            cases.append(
                table(
                    ["Arm", "Answer", "S/T/B"],
                    [
                        [
                            arm,
                            escaped(answer),
                            f"{int(score['success'])}/{int(score['stale'])}/{int(score['broken'])}",
                        ]
                        for arm, answer, score in answers
                    ],
                )
            )
    (d.OUT / "false-admissions.md").write_text("\n".join(cases))
    print("Wrote diagnostic results and every false-admission case", flush=True)


if __name__ == "__main__":
    run()
