"""Independent saved-artifact checks for the FOCUS-3 diagnostic; no inference."""

from __future__ import annotations

import copy
import json
import math
from collections import Counter

from scripts import focus3_gate_diag as d


def run():
    f, g = d.f, d.g
    bank = d.read(d.v6.BANK)
    selected = set(d.read(d.OUT / "selected-episodes.json"))
    tok = g.focus2.load_tokenizer(g.ROOT / "models/qwen3-4b-hf/tokenizer.json")
    encode = lambda s: g.focus2.encode(tok, s)  # noqa: E731
    system = encode("<|im_start|>system\n" + g.SYSTEM + "<|im_end|>\n")
    records, probes, logits_checked, pairs_checked = [], 0, 0, 0
    for split, episodes, arms in (
        ("setup", bank["setup"], ("O",)),
        ("gate", [e for e in bank["gate"] if e["id"] in selected], d.ARMS),
    ):
        for ep in episodes:
            for arm in arms:
                oracle, ever, prior_pairs, traces = f.Oracle(), [], [], []
                for ti, turn in enumerate(ep["turns"]):
                    rec = d.read(
                        d.OUT / split / "records" / f"{ep['id']}_{arm}_{ti}.json"
                    )
                    assert rec["split"] == split and rec["family"] == ep["family"]
                    assert rec["episode"] == ep["id"] and rec["arm"] == arm
                    gold_trace = oracle.update(turn["text"], ti, turn["events"])
                    gold_live = oracle.register.live(oracle.task, turn["kind"])
                    assert rec["gold_trace"] == gold_trace
                    assert rec["gold_live"] == [f.wire(r) for r in gold_live]
                    if arm == "O":
                        live = gold_live
                    elif arm == "N":
                        live = []
                    elif arm == "T":
                        for event in turn["events"]:
                            if event["label"] in ("admit", "supersedes"):
                                rid = f"{ti}:{turn['text'].index(event['span'])}"
                                ever.append(copy.deepcopy(oracle.register.get(rid)))
                        live = [r for r in ever if r.kind in ("all", turn["kind"])]
                    else:
                        live = None  # Candidate checked by exact saved-runtime replay.
                    if live is not None:
                        assert rec["live"] == [f.wire(r) for r in live]
                        assert rec["agreement"] == f.agreement(
                            live, gold_live, ep["gold_keys"]
                        )
                        assert rec["rendered_request"] == f.render(turn["text"], live)
                    raw_generations = [(rec["rendered_request"], rec["generation"])]
                    if split == "gate":
                        for path in (d.OUT / "probes").glob(
                            f"{ep['id']}_{arm}_*_{ti}.json"
                        ):
                            pp = d.read(path)
                            raw_generations.append(
                                (pp["rendered_request"], pp["generation"])
                            )
                            probes += 1
                    for rendered, gg in raw_generations:
                        prefix = encode(
                            "<|im_start|>user\n" + rendered + "<|im_end|>\n"
                            "<|im_start|>assistant\n<think>\n\n</think>\n\n"
                        )
                        assert gg["prompt_ids"] == system + prior_pairs + prefix
                        assert gg["output_start"] == len(gg["prompt_ids"])
                        assert (
                            tok.decode(gg["output_ids"], skip_special_tokens=False)
                            == gg["text"]
                        )
                        eos, output = gg["eos"], gg["output_ids"]
                        assert len(output) <= g.CAP
                        closure = (
                            [eos] + encode("\n")
                            if eos == g.focus2.EOS
                            else encode("<|im_end|>\n")
                        )
                        assert (
                            gg["pair_ids"]
                            == prefix
                            + output
                            + ([eos] if eos == g.focus2.END else [])
                            + closure
                        )
                        pairs_checked += 1
                    prior_pairs += rec["generation"]["pair_ids"]
                    for item in rec["trace"].get("pairs", []) + rec["trace"].get(
                        "admissions", []
                    ):
                        if item["overflow"]:
                            continue
                        logits = item["logits"]
                        ex = [math.exp(x - max(logits)) for x in logits]
                        probabilities = [x / sum(ex) for x in ex]
                        assert all(
                            abs(a - b) < 1e-12
                            for a, b in zip(
                                item["probabilities"], probabilities, strict=True
                            )
                        )
                        logits_checked += 1
                    assert not rec["provenance"]["mask_used"]
                    assert rec["un_release"]["masked_columns"] == 0
                    assert not rec["un_release"]["mask_unrelease"]
                    traces.append(
                        {
                            k: rec[k]
                            for k in (
                                "turn_index",
                                "trace",
                                "gold_trace",
                                "live",
                                "gold_live",
                                "agreement",
                                "un_release",
                            )
                        }
                    )
                    records.append(rec)
                assert traces == d.read(
                    d.OUT / split / "traces" / f"{ep['id']}_{arm}.json"
                )
    gate = [r for r in records if r["split"] == "gate"]
    setup = [r for r in records if r["split"] == "setup"]
    assert len(gate) == len(selected) * 5 * 6
    assert len(setup) == 96
    assert len(list((d.OUT / "gate/records").glob("*.json"))) == len(gate)
    assert len(list((d.OUT / "probes").glob("*.json"))) == probes
    effects = d.read(d.OUT / "false-admission-effects.json")
    assert probes == sum(t["completed_probes"] for t in effects["totals"].values())
    assert all(t["unmeasured_probes"] == 0 for t in effects["totals"].values())
    selection = d.read(d.OUT / "selection.json")
    setup_competence = sum(
        f.episode_metrics([r for r in setup if r["episode"] == ep["id"]])[
            "final_success"
        ]
        for ep in bank["setup"]
    )
    assert selection["O_setup_final_success"] == setup_competence
    recomputed = d.projection(
        selection["elapsed"], selection["durations"], selection["setup_exposures"]
    )
    assert all(selection[k] == v for k, v in recomputed.items())
    raw = dict(
        setup_records=len(setup),
        gate_records=len(gate),
        probe_generations=probes,
        token_sequences_checked=pairs_checked,
        classifier_softmax_checks=logits_checked,
        original_history_only=True,
        oracle_and_naive_reconstructed=True,
        traces_match_records=True,
        O_setup_final_success=setup_competence,
        all_exposures_measured=True,
        resource_selection_recomputed=True,
        family_gate_records=dict(Counter(r["family"] for r in gate)),
    )
    g.write(d.OUT / "independent-audit.json", raw)
    print(json.dumps(raw), flush=True)


if __name__ == "__main__":
    run()
