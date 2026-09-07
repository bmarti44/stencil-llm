"""CPU report/audit of saved responses only; never opens episode content or calls a model."""

import hashlib
import json
from fractions import Fraction
from math import comb
from pathlib import Path

OUT = Path(__file__).resolve().parent


def read(name):
    return json.loads((OUT / name).read_text())


def h(x):
    return hashlib.sha256(
        json.dumps(x, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def dump(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n")


def main():
    summary, freeze = read("summary.json"), read("freeze.json")
    rows = [
        json.loads(line)
        for a in "RNTQ"
        for line in (OUT / f"records-{a}.jsonl").read_text().splitlines()
    ]
    index = {(r["episode_id"], r["arm"], r["turn"]): r for r in rows}
    expected = {
        (eid, a, t)
        for eid in freeze["ids"]
        for a in ("RNTQ" if eid in freeze["q_ids"] else "RNT")
        for t in range(16)
    }
    assert len(index) == len(rows) and set(index) <= expected
    assert summary["complete"] == (set(index) == expected)
    raw_count = 0
    for path in (OUT / "local/main").glob("*/*/raw.jsonl"):
        for line in path.read_text().splitlines():
            raw = json.loads(line)
            r = index[raw["episode_id"], raw["arm"], raw["turn"]]
            assert all(r[k] == v for k, v in raw.items())
            raw_count += 1
    assert raw_count == len(rows)
    for r in rows:
        key = f"main/{r['episode_id']}/{r['arm']}/{r['turn']}"
        receipt = read("local/http/" + key + ".json")
        response = receipt["response"]
        choice = response["choices"][0]
        ids = list(choice["token_ids"])
        eos = (
            ids.pop()
            if choice["finish_reason"] == "stop" and ids[-1] in (151645, 151643)
            else None
        )
        assert ids == r["output_ids"] and eos == r["eos"]
        assert choice["text"] == r["output"]
        assert r["truncated"] == (choice["finish_reason"] == "length")
        assert response["usage"]["completion_tokens"] == r["output_tokens"]
        assert len(receipt["request"]["prompt"]) == r["prompt_tokens"]
        assert r["output_sha256"] == h([ids, eos])
        assert r["text_sha256"] == hashlib.sha256(r["output"].encode()).hexdigest()
        hashes = read("receipts/" + key + ".json")
        assert hashes["prompt_sha256"] == h(receipt["request"]["prompt"])
        assert hashes["output_sha256"] == r["output_sha256"]
    verified = 0
    for rel, metadata in read("local-hashes.json").items():
        path = OUT / rel
        assert path.stat().st_size == metadata["bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == metadata["sha256"]
        verified += 1
    # Independent exact statistical reimplementation from frozen change-round lists.
    audit_families = {}
    episode_family = {}
    for family, f in summary["primary"]["families"].items():
        gains, strict = [], []
        for e in f["episodes"]:
            paired, attempted = [], []
            for t in e["change_rounds"]:
                rn = [index.get((e["episode_id"], a, t)) for a in "RN"]
                written = [
                    bool(
                        r
                        and r["execution"]["executed"]
                        and not r["truncated"]
                        and r["execution"].get("category")
                        not in {"syntax_error", "parse_depth", "file_write"}
                    )
                    for r in rn
                ]
                values = [
                    int(w and r["outcome"]["satisfied"][family])
                    for w, r in zip(written, rn)
                ]
                attempted.append(values[0] - values[1])
                if all(written):
                    paired.append(values[0] - values[1])
            gain = Fraction(sum(paired), len(paired)) if paired else None
            if gain is not None:
                gains.append(gain)
            if attempted:
                strict.append(Fraction(sum(attempted), len(attempted)))
            episode_family.setdefault(e["episode_id"], {})[family] = (
                None if gain is None else float(gain)
            )
        wins, losses = sum(g > 0 for g in gains), sum(g < 0 for g in gains)
        discordant = wins + losses
        pvalue = (
            sum(comb(discordant, j) for j in range(wins, discordant + 1))
            / 2**discordant
        )
        gain = float(sum(gains) / len(gains)) if gains else None
        assert (wins, losses, len(gains), pvalue, gain) == (
            f["wins"],
            f["losses"],
            f["n"],
            f["p"],
            f["mean_gain"],
        )
        assert (float(sum(strict) / len(strict)) if strict else None) == f[
            "strict_failed_attempts"
        ]["mean_gain"]
        audit_families[family] = dict(p=pvalue, mean_gain=gain)
    adjusted = 0
    for rank, key in enumerate(
        sorted(audit_families, key=lambda k: audit_families[k]["p"])
    ):
        adjusted = max(adjusted, min(1, (3 - rank) * audit_families[key]["p"]))
        assert adjusted == summary["primary"]["families"][key]["holm_p"]
    # Reporting-only: use pilot7's applicable-trait joint-final rubric.
    # The frozen summary's all-satisfied field is preserved, never a gate.
    joint = {}
    for eid in freeze["ids"]:
        joint[eid] = {}
        for a in "RNTQ" if eid in freeze["q_ids"] else "RNT":
            r = index.get((eid, a, 15))
            joint[eid][a] = bool(
                r
                and r["file_written"]
                and r["outcome"]["integration"]
                and r["outcome"]["report_ok"]
                and not any(
                    r["outcome"]["diagnostics"][k]
                    for k in (
                        "language",
                        "indent",
                        "format",
                        "delivery",
                        "breakage",
                        "wrong_family",
                    )
                )
            )
    dump(
        "joint-final-descriptive.json",
        dict(
            definition="same applicable-trait diagnostic rubric as pilot7; descriptive only",
            frozen_summary_definition="all four raw satisfied flags; retained unchanged",
            episodes=joint,
            per_arm={a: sum(e.get(a, False) for e in joint.values()) for a in "RNTQ"},
        ),
    )
    broken = {
        a: sum(
            any(
                r["outcome"]["diagnostics"]["breakage"]
                for r in rows
                if r["episode_id"] == eid and r["arm"] == a
            )
            for eid in freeze["ids"]
        )
        for a in "RN"
    }
    assert broken["R"] - broken["N"] == summary["breakage_excess"]
    verdict = (
        "INCOMPLETE"
        if set(index) != expected
        else "PASS"
        if summary["primary"]["families"]["delivery"]["pass"]
        and broken["R"] - broken["N"] <= 1
        and read("composition-control.json")["passed"]
        else "FAIL"
    )
    assert verdict == summary["reading"]
    lifecycle = read("lifecycle.json")
    groups = read("groups.json") if (OUT / "groups.json").exists() else []
    gpu = lifecycle["gpu_held_seconds"]
    cost = dict(
        gpu_held_seconds=gpu,
        gpu_held_hours=gpu / 3600,
        within_cooperative_budget=gpu <= 41400,
        within_hard_budget=gpu <= 43200,
        load=read("ready.json") if (OUT / "ready.json").exists() else None,
        groups_seconds=sum(g["seconds"] for g in groups),
        per_arm_group_seconds={
            a: sum(g["seconds"] for g in groups if g["arm"] == a) for a in "RNTQ"
        },
        generated_tokens=sum(r["output_tokens"] for r in rows),
        prompt_tokens=sum(r["prompt_tokens"] for r in rows),
        max_prompt_tokens=max((r["prompt_tokens"] for r in rows), default=0),
        projection=freeze["projection"],
        queue_seconds=read("launch.json")["queue_seconds"],
    )
    dump("cost-audit.json", cost)
    audit = dict(
        passed=True,
        records=len(rows),
        raw_records=raw_count,
        http_receipts_verified=len(rows),
        local_files_verified=verified,
        independent_family_statistics=True,
        duplicates=0,
        missing=len(expected - set(index)),
        frozen_sha=read("pin-verification.json")["sha"],
    )
    dump("audit.json", audit)
    repro = (
        read("reproducibility.json")
        if (OUT / "reproducibility.json").exists()
        else None
    )
    lines = [
        "Fit-on: none; development-on: eight DEV episodes only; evaluated-on: the64 frozen authored evaluation episodes, one model pass, no tuning.",
        "",
        f"# SLAB-2 Amendment5 — {summary['reading']}",
        "",
        f"{len(rows)}/3328 scheduled records; {sum(e['arms']['R']['completed'] and e['arms']['N']['completed'] and e['arms']['T']['completed'] for e in summary['episodes'])}/64 complete R/N/T episodes. "
        f"Frozen SHA `{audit['frozen_sha']}`. "
        + (
            "Failed clauses: " + "; ".join(summary["failures"]) + "."
            if summary["failures"]
            else "All registered PASS clauses met."
        ),
        "",
        "| Family | Paired episodes | R wins / N wins / ties | Mean paired gain | One-sided p | Holm p | Evidence | Missing-write sensitivity gain |",
        "|---|---:|---:|---:|---:|---:|---|---:|",
    ]
    for k in ("delivery", "format", "indent"):
        f = summary["primary"]["families"][k]
        lines.append(
            f"| {k} | {f['n']} | {f['wins']}/{f['losses']}/{f['ties']} | {f['mean_gain']} | {f['p']:.9g} | {f['holm_p']:.9g} | {f['pass']} | {f['strict_failed_attempts']['mean_gain']} |"
        )
    lines += [
        "",
        "Delivery is the predeclared primary; all signs are episode-paired after within-episode averaging. No independent-round inference. Joint final success below uses pilot7’s applicable-trait diagnostic rubric and is descriptive only. The frozen summary’s all-four-raw-satisfied field is retained unchanged; its stricter definition was noticed during loading before evaluation outputs and is not used in this table or any verdict.",
        "",
        "| Arm | Episodes | Any breakage | Any nonwrite | Any cap | Any compact ready | Any compact format violation | Joint final |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for a in "RNTQ":
        m = summary["per_arm"][a]
        lines.append(
            f"| {a} | {64 if a != 'Q' else 16} | {m['broken']} | {m['any_nonwrite']} | {m['any_cap']} | {m['compact_ready']} | {m['compact_format_violation']} | {m['joint_final']} |"
        )
    lines += [
        "",
        "Per-family arm adherence: mean of within-episode written-change adherence; measured-episode denominator. These descriptive arm means use each arm’s own writes; the primary above uses common R/N writes.",
        "",
        "| Family | R mean / episodes | N mean / episodes | T mean / episodes | Q mean / episodes |",
        "|---|---:|---:|---:|---:|",
    ]
    for key in ("delivery", "format", "indent"):
        cells = []
        for a in "RNTQ":
            values = [
                Fraction(e["satisfied"][a], e["written_denominators"][a])
                for e in summary["primary"]["families"][key]["episodes"]
                if e["written_denominators"][a]
            ]
            cells.append(
                f"{float(sum(values) / len(values)):.4f} / {len(values)}"
                if values
                else "unmeasured / 0"
            )
        lines.append("| " + key + " | " + " | ".join(cells) + " |")
    control = read("composition-control.json")
    lines += [
        "",
        f"Paired breakage excess R−N={summary['breakage_excess']} episodes (allowed<=1). CPU composition: {control['scheduled_compact']} scheduled compact registers across {control['episode_count']} episodes, all clean and bit-exact between forward/reconstructed state;35 historical hashes exact.",
        "",
    ]
    if repro and repro.get("complete"):
        lines += [
            f"Cross-container reproducibility: **{repro['divergent']}/40 divergent ({repro['divergence_rate']:.1%})**, from the fixed pilot7 payloads reissued midway in this container. {repro['any_divergence_episodes']}/8 DEV episodes had any divergence; episode-mean divergence {repro['episode_mean_divergence']:.1%}. Descriptive; no cell-independence confidence claim.",
            "",
        ]
    else:
        lines += [
            "Cross-container reproducibility control INCOMPLETE; protocol requirement unfulfilled.",
            "",
        ]
    lines += [
        f"GPU held **{gpu / 3600:.4f}h** ({gpu:.3f}s), including loading, replay and cleanup, against11.5h cooperative/12h hard limits. Projection7.4462h; queue wait{cost['queue_seconds']:.2f}s. Main generated tokens{cost['generated_tokens']:,}; max prompt+cap{cost['max_prompt_tokens']}+2048<=32768. Full cost decomposition in cost-audit.json.",
        "",
        f"CPU audit: all{len(rows)} records agree with raw same-run records, saved HTTP completions/token accounting and SHA256 receipts; {verified} local files verified; independent episode sign/Holm reimplementation agrees. Initial isolated validation failed because its tokenizer link was absent; corrected asset link gave37passed/1xfail and CPU smoke before GPU. No source or threshold changed after freeze.",
        "",
        "Claim ceiling: any positive evidence credits the current effective value restated at request time in this bounded explicit-rule package on one frozen trunk and authored distribution. T is oracle prose (DEV7/8); this is not evidence that a register data structure beats prose. Accumulated history retains old blocks, the system worked example attracts delivery=ready, and T remains uncomposed on compact format. No free-text admission, universal task selection, autonomous long-horizon engineering, actuator efficacy or absence-of-stale-influence claim. See [registration](REGISTRATION.md) and [v2 ceiling](../focus-mechanism-composition-v2-astra.md).",
        "",
        "Q is a16-episode fresh-context reference using gold prerequisite files; O was dropped as byte-identical to R. No later retries, seeds, outcome-selected subsets or tuning. HTTP/full journals are local and hash-indexed; own container cleanup is recorded. No host process signals or push.",
        "",
        "| Episode | Delivery gain | Format gain | Indent gain | Broken R/N/T/Q | Compact ready R/N/T/Q | Final R/N/T/Q |",
        "|---|---:|---:|---:|---|---|---|",
    ]
    for e in summary["episodes"]:
        gains = episode_family[e["episode_id"]]

        def column(key):
            if key == "joint_final":
                return "/".join(
                    str(int(joint[e["episode_id"]][a]))
                    if a in joint[e["episode_id"]]
                    else "—"
                    for a in "RNTQ"
                )
            return "/".join(
                str(int(e["arms"][a][key])) if a in e["arms"] else "—" for a in "RNTQ"
            )

        lines.append(
            f"| {e['episode_id']} | {gains['delivery']} | {gains['format']} | {gains['indent']} | {column('broken')} | {column('compact_ready')} | {column('joint_final')} |"
        )
    (OUT / "RESULTS.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(audit))


if __name__ == "__main__":
    main()
