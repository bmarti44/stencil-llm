import json
from collections import Counter, defaultdict
from pathlib import Path

from tokenizers import Tokenizer


def main():
    root = Path("/home/bmarti44/stencil-llm")
    out = root / "results/quick-checks/focus3-gate"
    bank = json.loads((out / "bank.json").read_text())
    tok = Tokenizer.from_file(str(root / "models/qwen3-4b-hf/tokenizer.json"))

    def enc(s):
        return tok.encode(s, add_special_tokens=False).ids

    system = (
        "Follow the user's currently applicable instructions. "
        "For a payload request with no applicable ordering rule, return the "
        "payload unchanged. Give only the requested answer; no explanation."
    )
    metrics = {}
    confusion = defaultdict(Counter)
    missing = Counter()
    none_changed = Counter()
    latencies = []
    for split in ("setup", "gate"):
        for ep in bank[split]:
            for arm in ("O",) if split == "setup" else ("C", "O", "N", "T"):
                files = sorted(
                    (out / split / "records").glob(ep["id"] + "_" + arm + "_*.json")
                )
                if not files:
                    continue
                assert len(files) == 6, (ep["id"], arm, len(files))
                history = []
                rr = []
                for i, path in enumerate(files):
                    r = json.loads(path.read_text())
                    t = r["turn"]
                    g = r["generation"]
                    assert r["turn_index"] == i and t == ep["turns"][i]
                    assert (
                        tok.decode(g["output_ids"], skip_special_tokens=False)
                        == g["text"]
                    )
                    prefix = enc(
                        "<|im_start|>user\n"
                        + r["rendered_request"]
                        + "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
                    )
                    expected = (
                        enc("<|im_start|>system\n" + system + "<|im_end|>\n")
                        + history
                        + prefix
                    )
                    assert g["prompt_ids"] == expected, (
                        ep["id"],
                        arm,
                        i,
                        "prompt-history",
                    )
                    close = (
                        [g["eos"]] + enc("\n")
                        if g["eos"] == 151645
                        else enc("<|im_end|>\n")
                    )
                    pair = (
                        prefix
                        + g["output_ids"]
                        + ([g["eos"]] if g["eos"] == 151643 else [])
                        + close
                    )
                    assert g["pair_ids"] == pair
                    history += pair
                    assert r["provenance"]["start"] == len(expected)
                    assert r["provenance"]["count"] == len(g["output_ids"]) + int(
                        g["eos"] is not None
                    )
                    assert not r["provenance"]["mask_used"]
                    if t["kind"] == "sort":
                        try:
                            v = json.loads(g["text"])
                        except (ValueError, TypeError):
                            v = None
                        valid = (
                            isinstance(v, dict)
                            and set(v) == {"answer", "tag"}
                            and type(v["tag"]) is int
                            and isinstance(v["answer"], list)
                            and all(type(x) is int for x in v["answer"])
                        )

                        def transform(d, t=t):
                            return (
                                list(t["payload"])
                                if d == "default"
                                else sorted(t["payload"], reverse=d == "descending")
                            )

                        correct = bool(
                            valid and v["answer"] == transform(t["direction"])
                        )
                        tag = bool(valid and v["tag"] == t["tag"])
                        stale = bool(
                            valid
                            and t["post_change"]
                            and any(v["answer"] == transform(d) for d in t["stale"])
                        )
                        assert r["score"]["task"] == correct
                        assert r["score"]["constraint"] == tag
                        assert r["score"]["stale"] == stale
                    if arm == "C" and split == "gate":
                        latencies.append(r["classifier_seconds"])
                        rows = r["trace"]["after"]
                        task = r["selected_task"]
                        kind = t["kind"]
                        live = {}
                        for row in rows:
                            if (
                                row["status"] == "live"
                                and row["scope"] in ("*", task)
                                and row["kind"] in ("all", kind)
                            ):
                                old = live.get(row["key"])
                                if old is None or (
                                    row["provenance_turn"],
                                    row["span_start"],
                                    row["version"],
                                ) > (
                                    old["provenance_turn"],
                                    old["span_start"],
                                    old["version"],
                                ):
                                    live[row["key"]] = row

                        def wire(row):
                            return dict(
                                id=row["id"],
                                version=row["version"],
                                scope=row["scope"],
                                task_id=None if row["scope"] == "*" else row["scope"],
                                text=row["text"],
                            )

                        expected_live = [
                            wire(row)
                            for row in sorted(
                                live.values(),
                                key=lambda row: (row["key"], row["version"]),
                            )
                        ]
                        assert r["live"] == expected_live
                        cc = {json.dumps(row, sort_keys=True) for row in r["live"]}
                        oo = {json.dumps(row, sort_keys=True) for row in r["gold_live"]}
                        assert r["agreement"]["exact"] == (cc == oo)
                        assert r["agreement"]["false_retirement"] == bool(oo - cc)
                        keys = Counter(
                            ep["gold_keys"].get(row["id"], "unmapped:" + row["id"])
                            for row in r["live"]
                        )
                        assert r["agreement"]["contradictory"] == any(
                            c > 1 for c in keys.values()
                        )
                        for p in r["trace"]["pairs"]:
                            confusion[ep["family"]][
                                p["gold"] + "->" + p["applied"]
                            ] += 1
                        for ev in t["events"]:
                            if ev.get("target") and not any(
                                p["input"]["target_id"] == ev["target"]
                                and p["input"]["target_span"]["text"] == ev["span"]
                                for p in r["trace"]["pairs"]
                            ):
                                missing[ep["family"]] += 1
                        if (
                            t["hard_none"]
                            and r["trace"]["before"] != r["trace"]["after"]
                        ):
                            none_changed[ep["family"]] += 1
                    rr.append(r)
                tasks = [r for r in rr if r["turn"]["kind"] == "sort"]
                metrics[(ep["id"], arm)] = dict(
                    stale=any(r["score"]["stale"] for r in tasks),
                    final_success=tasks[-1]["score"]["success"],
                    broken=any(
                        r["score"]["broken"] for r in rr if r["turn"]["post_change"]
                    ),
                    false_retirement=any(
                        r["agreement"]["false_retirement"] for r in tasks
                    ),
                    exact=all(r["agreement"]["exact"] for r in tasks),
                    contradictory=any(r["agreement"]["contradictory"] for r in tasks),
                )
    summary = json.loads((out / "summary.json").read_text())
    if "counts" in summary:
        for group, counts in summary["counts"].items():
            selected = [
                e
                for e in bank["gate"]
                if e["index"] < summary["selection"]["n"] // 4
                and (group == "pooled" or e["family"] == group)
            ]
            for arm, endpoints in counts.items():
                for endpoint, n in endpoints.items():
                    if n is not None:
                        assert n == sum(
                            metrics[(e["id"], arm)][endpoint] for e in selected
                        ), (group, arm, endpoint)
    latencies.sort()
    report = dict(
        independent_audit="PASS",
        gate_records_audited=sum(6 for e, a in metrics if e.startswith("gate_")),
        unexercised_checks=[]
        if latencies
        else [
            "C rendered-state audit",
            "C/O register agreement",
            "gate endpoint totals",
        ],
        complete_episode_arms=len(metrics),
        records=len(metrics) * 6,
        unpaired_gold_relation_events=dict(missing),
        hard_none_state_change_episodes=dict(none_changed),
        pair_confusion={k: dict(v) for k, v in confusion.items()},
        classifier_p50_seconds=latencies[len(latencies) // 2] if latencies else None,
        classifier_p95_seconds=latencies[
            min(len(latencies) - 1, int(len(latencies) * 0.95))
        ]
        if latencies
        else None,
        checks=[
            "raw token decode",
            "full own-pair prompt trajectory",
            "output provenance positions",
            "independent JSON sort/tag discriminators",
        ],
    )
    (out / "independent-audit.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(report, indent=2, sort_keys=True))

    setup_counts = {}
    for family in {e["family"] for e in bank["setup"]}:
        es = [e for e in bank["setup"] if e["family"] == family]
        setup_counts[family] = {
            "n": len(es),
            **{
                k: sum(metrics[(e["id"], "O")][k] for e in es)
                for k in ("stale", "final_success", "broken")
            },
        }
    report["setup_counts"] = setup_counts
    (out / "independent-audit.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )


if __name__ == "__main__":
    main()
