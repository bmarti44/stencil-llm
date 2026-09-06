"""One authorized v8 diagnostic; frozen runtime, no eligibility decision or fitting."""

from __future__ import annotations

import argparse
import json
import random
import subprocess
import time
from collections import Counter
from types import SimpleNamespace

from scripts import focus3_gate as g
from scripts import focus3_gate_v5 as v5
from scripts import focus3_gate_v6 as v6
from scripts import focus3_gate_v8 as v8
from stencil import focus3 as f

OUT = g.ROOT / "results/quick-checks/focus3-gate/diag"
V8 = v8.OUT
ARMS = ("C", "C'", "O", "N", "T")
CAP_SECONDS = 7200


def read(path):
    return json.loads(path.read_text())


def configure():
    g.OUT = OUT
    # Only the flag location changes; classifier and runtime are unmodified.
    v8.OUT = OUT


def sources():
    paths = [
        g.ROOT / name
        for name in (
            "scripts/focus3_gate_diag.py",
            "scripts/focus3_gate.py",
            "scripts/focus3_gate_v5.py",
            "scripts/focus3_gate_v6.py",
            "scripts/focus3_gate_v8.py",
            "src/stencil/focus3.py",
            "src/stencil/focus2.py",
            "src/stencil/qwen3.py",
            "tests/test_focus3_gate_diag.py",
            "models/qwen3-4b-hf/config.json",
            "models/qwen3-4b-hf/tokenizer.json",
            "models/qwen3-4b.pt",
        )
    ]
    paths += [v6.BANK, V8 / "freeze.json", V8 / "recipe-freeze.json"]
    for directory in (v6.MODELS / "seed0", v8.a.MODELS / "seed0"):
        paths += [p for p in directory.rglob("*") if p.is_file()]
    return {str(p.relative_to(g.ROOT)): g.digest(p) for p in sorted(paths)}


def prepare():
    assert not (OUT / "freeze.json").exists()
    v8.verify_freeze()
    # Verify the inherited trunk against its original committed freeze.
    original = read(OUT.parent / "freeze.json")["hashes"]
    hashes = sources()
    for path in (
        "models/qwen3-4b.pt",
        "models/qwen3-4b-hf/config.json",
        "models/qwen3-4b-hf/tokenizer.json",
    ):
        assert hashes[path] == original[path], path
    registration = (OUT / "RESULTS.md").read_text()
    (OUT / "registration.md").write_text(registration)
    g.write(
        OUT / "freeze.json",
        dict(
            hashes=hashes,
            registration_sha256=g.digest(OUT / "registration.md"),
            created=time.time(),
            bank_seed=30322,
            arms=ARMS,
            gpu_cap=CAP_SECONDS,
            fit_train_tune="NONE",
            policies=v6.policies(),
            admission_bound="positive_proposal",
            key_identity=True,
            strict_lifecycle=True,
            admission_threshold=0.95,
        ),
    )
    print("Diagnostic sources and existing checkpoints frozen", flush=True)


def verify():
    receipt = read(OUT / "freeze.json")
    assert receipt["hashes"] == sources(), "diagnostic source/model drift"
    assert receipt["registration_sha256"] == g.digest(OUT / "registration.md")
    for name in ("freeze.json", "registration.md"):
        assert v5.committed_bytes(OUT / name) == (OUT / name).read_bytes()


def false_rows(records):
    """Match applied admissions to registered events through the v5 consumer."""
    result = []
    by_turn = {r["turn_index"]: r for r in records}
    for action in v5.unauthorized(records)["details"]:
        if action["label"] != "admit":
            continue
        rec = by_turn[action["turn_index"]]
        start = rec["turn"]["text"].index(action["span"])
        rid = f"{rec['turn_index']}:{start}"
        row = next(r for r in rec["trace"]["after"] if r["id"] == rid)
        admission = next(a for a in rec["trace"]["admissions"] if a["start"] == start)
        result.append(
            dict(
                episode=rec["episode"],
                family=rec["family"],
                arm=rec["arm"],
                admitted_turn=rec["turn_index"],
                row=row,
                probability_rule=admission["probabilities"][1],
                category="one-shot payload request"
                if "Sort request" in row["text"]
                else "inert quote"
                if rec["turn"]["hard_none"]
                else "other",
            )
        )
    return result


def exposures(records, admission):
    return [
        r
        for r in records
        if r["turn_index"] >= admission["admitted_turn"]
        and any(row["id"] == admission["row"]["id"] for row in r["live"])
    ]


def projection(elapsed, durations, setup_exposures):
    # C' gets the same conservative exposure allowance; max episode duration
    # includes six generations and CPU classification, with 25% headroom.
    rows = {}
    for n in (64, 48):
        gate = 1.25 * max(durations) * n * len(ARMS)
        probe_count = setup_exposures * (n / 16) * 2
        probes = 1.25 * max(durations) / 6 * probe_count
        rows[str(n)] = dict(
            gate_seconds=gate,
            probe_count=probe_count,
            probe_seconds=probes,
            total_seconds=elapsed + gate + probes,
        )
    selected = next(
        (n for n in (64, 48) if rows[str(n)]["total_seconds"] <= CAP_SECONDS - 30), 0
    )
    return dict(
        n=selected,
        alternatives=rows,
        elapsed=elapsed,
        durations=durations,
        setup_exposures=setup_exposures,
        written_before_gate=True,
        selection_basis="resource only",
    )


def summarize(episodes, records):
    metrics = {}
    for ep in episodes:
        metrics[ep["id"]] = {}
        for arm in ARMS:
            rr = [r for r in records if r["episode"] == ep["id"] and r["arm"] == arm]
            assert len(rr) == len(ep["turns"])
            value = f.episode_metrics(rr)
            if arm in ("C", "C'"):
                value["false_admission"] = bool(false_rows(rr))
            else:
                value["false_admission"] = None
            if arm in ("N", "T"):
                for key in ("exact", "false_retirement", "contradictory"):
                    value[key] = None
            metrics[ep["id"]][arm] = value
    groups = {"pooled": episodes}
    groups.update(
        {
            family: [e for e in episodes if e["family"] == family]
            for family in g.FAMILIES
        }
    )
    counts, unauthorized = {}, {}
    for family, es in groups.items():
        counts[family], unauthorized[family] = {}, {}
        for arm in ARMS:
            values = [metrics[e["id"]][arm] for e in es]
            counts[family][arm] = {
                key: None if values[0][key] is None else sum(v[key] for v in values)
                for key in values[0]
            }
            if arm in ("C", "C'"):
                rr = [
                    r
                    for r in records
                    if r["arm"] == arm and r["episode"] in {e["id"] for e in es}
                ]
                unauthorized[family][arm] = v5.unauthorized(rr)
    contrasts = {}
    for reference in ("O", "T"):
        contrasts[reference] = {}
        for endpoint in ("stale", "final_success", "broken"):
            contrasts[reference][endpoint] = dict(
                c_minus_reference=counts["pooled"]["C"][endpoint]
                - counts["pooled"][reference][endpoint],
                c_only=sum(
                    m["C"][endpoint] and not m[reference][endpoint]
                    for m in metrics.values()
                ),
                reference_only=sum(
                    m[reference][endpoint] and not m["C"][endpoint]
                    for m in metrics.values()
                ),
            )
    return dict(
        diagnostic=True,
        episodes=metrics,
        counts=counts,
        family_support={k: len(es) for k, es in groups.items()},
        unauthorized=unauthorized,
        contrasts=contrasts,
        pair_diagnostics={
            arm: g.diagnostics([dict(r, arm="C") for r in records if r["arm"] == arm])
            for arm in ("C", "C'")
        },
        record_count=len(records),
        masking=False,
    )


def remove_rendered_row(rec, rid):
    rows = [SimpleNamespace(**r) for r in rec["live"]]
    assert f.render(rec["turn"]["text"], rows) == rec["rendered_request"]
    kept = [r for r in rows if r.id != rid]
    assert len(rows) - len(kept) == 1
    return f.render(rec["turn"]["text"], kept)


def semantic_answer(text):
    try:
        return g.focus2.parse_json(text)
    except (ValueError, TypeError, RecursionError):
        return text.strip()


def probe_name(admission, turn_index):
    return (
        f"{admission['episode']}_{admission['arm']}_"
        f"{admission['row']['id'].replace(':', '-')}_{turn_index}.json"
    )


def probe(trunk, rr, admission, rec):
    rendered = remove_rendered_row(rec, admission["row"]["id"])
    history = [r["generation"] for r in rr if r["turn_index"] < rec["turn_index"]]
    generation = trunk.answer(history, rendered)
    score = f.score(
        rec["turn"], generation["text"], generation["output_ids"], generation["eos"]
    )
    result = dict(
        episode=rec["episode"],
        arm=rec["arm"],
        row_id=admission["row"]["id"],
        turn_index=rec["turn_index"],
        rendered_request=rendered,
        generation=generation,
        score=score,
        original_record=f"gate/records/{rec['episode']}_{rec['arm']}_{rec['turn_index']}.json",
        prior_history="exact original candidate pair_ids; no probe feedback",
        token_changed=(generation["output_ids"], generation["eos"])
        != (rec["generation"]["output_ids"], rec["generation"]["eos"]),
        text_changed=generation["text"] != rec["generation"]["text"],
        semantic_changed=semantic_answer(generation["text"])
        != semantic_answer(rec["generation"]["text"]),
        score_changes={
            k: dict(original=v, without_row=score[k])
            for k, v in rec["score"].items()
            if v != score[k]
        },
    )
    g.write(OUT / "probes" / probe_name(admission, rec["turn_index"]), result)
    return result


def effects(records):
    details = []
    for arm in ("C", "C'"):
        for episode in sorted({r["episode"] for r in records}):
            rr = sorted(
                [r for r in records if r["episode"] == episode and r["arm"] == arm],
                key=lambda r: r["turn_index"],
            )
            for admission in false_rows(rr):
                turns = []
                for rec in rr[admission["admitted_turn"] :]:
                    rid = admission["row"]["id"]
                    rendered = any(row["id"] == rid for row in rec["live"])
                    path = OUT / "probes" / probe_name(admission, rec["turn_index"])
                    pp = read(path) if path.exists() else None
                    turns.append(
                        dict(
                            turn_index=rec["turn_index"],
                            rendered=rendered,
                            later_than_admission=rec["turn_index"]
                            > admission["admitted_turn"],
                            row_status=next(
                                row["status"]
                                for row in rec["trace"]["after"]
                                if row["id"] == rid
                            ),
                            answer=rec["generation"]["text"],
                            score=rec["score"],
                            references={
                                a: dict(
                                    answer=r["generation"]["text"], score=r["score"]
                                )
                                for a in ("O", "N", "T")
                                for r in records
                                if r["episode"] == episode
                                and r["arm"] == a
                                and r["turn_index"] == rec["turn_index"]
                            },
                            probe=None
                            if pp is None
                            else dict(
                                path=str(path.relative_to(OUT)),
                                **{
                                    k: pp[k]
                                    for k in (
                                        "token_changed",
                                        "text_changed",
                                        "semantic_changed",
                                        "score_changes",
                                    )
                                },
                            ),
                        )
                    )
                details.append(dict(admission, turns=turns))
    totals = {}
    for arm in ("C", "C'"):
        aa = [d for d in details if d["arm"] == arm]
        tt = [t for d in aa for t in d["turns"] if t["rendered"]]
        pp = [t["probe"] for t in tt if t["probe"] is not None]
        totals[arm] = dict(
            false_admissions=len(aa),
            categories=dict(Counter(d["category"] for d in aa)),
            exposed_row_turns=len(tt),
            completed_probes=len(pp),
            unmeasured_probes=len(tt) - len(pp),
            token_changes=sum(p["token_changed"] for p in pp),
            text_changes=sum(p["text_changed"] for p in pp),
            semantic_changes=sum(p["semantic_changed"] for p in pp),
            score_changes=sum(bool(p["score_changes"]) for p in pp),
            admissions_with_semantic_effect=sum(
                any(t["probe"] and t["probe"]["semantic_changed"] for t in d["turns"])
                for d in aa
            ),
            never_rendered=sum(not any(t["rendered"] for t in d["turns"]) for d in aa),
        )
    return dict(
        totals=totals,
        details=details,
        estimand="current recap row removal conditional on original history",
    )


def run():
    verify()
    assert not (OUT / "started.json").exists(), "one-shot diagnostic already started"
    saved_setup = [read(p) for p in sorted((V8 / "records").glob("*.json"))]
    setup_exposures = sum(
        len(exposures(rr, a))
        for ep in sorted({r["episode"] for r in saved_setup})
        for rr in [[r for r in saved_setup if r["episode"] == ep]]
        for a in false_rows(rr)
    )
    configure()
    with v8.claim_gpu():
        started = time.monotonic()
        g.write(
            OUT / "started.json",
            dict(
                time=time.time(),
                commit=subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=g.ROOT, text=True
                ).strip(),
                freeze_sha256=g.digest(OUT / "freeze.json"),
                diagnostic=True,
            ),
        )
        trunk, records, selected = None, [], []
        result = dict(diagnostic=True, completion="not started")
        try:
            clf = v8.classifier()
            trunk = g.Trunk(started + CAP_SECONDS - 30)
            bank = read(v6.BANK)
            setup, durations = [], []
            for ep in bank["setup"]:
                t = time.monotonic()
                setup.extend(g.run_episode(ep, "O", trunk, clf, "setup"))
                durations.append(time.monotonic() - t)
                print(
                    json.dumps(
                        dict(
                            stage="O setup",
                            episode=ep["id"],
                            elapsed=time.monotonic() - started,
                        )
                    ),
                    flush=True,
                )
            selection = projection(
                time.monotonic() - started, durations, setup_exposures
            )
            selection["O_setup_final_success"] = sum(
                f.episode_metrics([r for r in setup if r["episode"] == e["id"]])[
                    "final_success"
                ]
                for e in bank["setup"]
            )
            g.write(OUT / "selection.json", selection)
            print(json.dumps(dict(selection=selection)), flush=True)
            if not selection["n"]:
                result.update(completion="resource projection prevented gate")
                return
            per_family = selection["n"] // 4
            counts = Counter()
            for ep in bank["gate"]:
                if counts[ep["family"]] < per_family:
                    selected.append(ep)
                    counts[ep["family"]] += 1
            g.write(OUT / "selected-episodes.json", [e["id"] for e in selected])
            rng = random.Random(30303)
            for ep in selected:
                arms = list(ARMS)
                rng.shuffle(arms)
                for arm in arms:
                    clf.thresholds = v6.policies()[arm if arm == "C'" else "C"][
                        "policy"
                    ]["thresholds"]
                    records.extend(g.run_episode(ep, arm, trunk, clf, "gate"))
                    print(
                        json.dumps(
                            dict(
                                stage="gate",
                                episode=ep["id"],
                                arm=arm,
                                elapsed=time.monotonic() - started,
                            )
                        ),
                        flush=True,
                    )
            result.update(
                summarize(selected, records),
                completion="five arms complete; probes running",
            )
            g.write(OUT / "summary.json", result)
            for ep in selected:
                for arm in ("C", "C'"):
                    rr = [
                        r
                        for r in records
                        if r["episode"] == ep["id"] and r["arm"] == arm
                    ]
                    for admission in false_rows(rr):
                        for rec in exposures(rr, admission):
                            probe(trunk, rr, admission, rec)
                print(
                    json.dumps(
                        dict(
                            stage="false admission probes",
                            episode=ep["id"],
                            elapsed=time.monotonic() - started,
                        )
                    ),
                    flush=True,
                )
            result["completion"] = "five arms and all exposed-row probes complete"
        except TimeoutError as exc:
            result.update(completion="cooperative resource stop", reason=str(exc))
        except Exception as exc:
            result.update(
                completion="exception; retained partial work", reason=repr(exc)
            )
            raise
        finally:
            g.write(OUT / "false-admission-effects.json", effects(records))
            if trunk is not None:
                result["peak_gpu_bytes"] = trunk.backend.peak_memory
                trunk.backend.close()
            result.update(
                gpu_held_seconds=time.monotonic() - started,
                completed_gate_records=len(records),
                diagnostic=True,
            )
            g.write(OUT / "summary.json", result)
            print(
                json.dumps(
                    {
                        k: v
                        for k, v in result.items()
                        if k
                        in ("completion", "gpu_held_seconds", "completed_gate_records")
                    }
                ),
                flush=True,
            )


def audit():
    verify()
    bank = read(v6.BANK)
    selected_ids = read(OUT / "selected-episodes.json")
    episodes = [e for e in bank["gate"] if e["id"] in selected_ids]
    records = []
    tok = g.focus2.load_tokenizer(g.ROOT / "models/qwen3-4b-hf/tokenizer.json")
    encode = lambda text: g.focus2.encode(tok, text)  # noqa: E731
    system = encode("<|im_start|>system\n" + g.SYSTEM + "<|im_end|>\n")
    for ep in episodes:
        for arm in ARMS:
            clf = v5.SavedClassifier()
            clf.key_identity = clf.strict_lifecycle = True
            clf.admission_bound = "positive_proposal"
            clf.thresholds = v6.policies()[arm if arm == "C'" else "C"]["policy"][
                "thresholds"
            ]
            rt, oracle = f.Runtime(clf), f.Oracle()
            history = []
            for ti, turn in enumerate(ep["turns"]):
                r = read(OUT / "gate/records" / f"{ep['id']}_{arm}_{ti}.json")
                g.validate_record(r)
                assert r["turn"] == turn
                assert r["gold_trace"] == oracle.update(
                    turn["text"], ti, turn["events"]
                )
                assert r["score"] == f.score(
                    turn,
                    r["generation"]["text"],
                    r["generation"]["output_ids"],
                    r["generation"]["eos"],
                )
                if arm in ("C", "C'"):
                    clf.record = r
                    trace = rt.update(turn["text"], ti)
                    for pair in trace["pairs"]:
                        pair["gold"] = g.gold_pair_label(pair["input"], turn)
                    assert trace == r["trace"]
                    live = rt.register.live(rt.task, turn["kind"])
                    assert [f.wire(row) for row in live] == r["live"]
                    assert r["agreement"] == f.agreement(
                        live,
                        oracle.register.live(oracle.task, turn["kind"]),
                        ep["gold_keys"],
                    )

                def prompt_ids(rendered, history=history):
                    prefix = encode(
                        "<|im_start|>user\n" + rendered + "<|im_end|>\n"
                        "<|im_start|>assistant\n<think>\n\n</think>\n\n"
                    )
                    return system + [i for h in history for i in h["pair_ids"]] + prefix

                assert r["generation"]["prompt_ids"] == prompt_ids(
                    r["rendered_request"]
                )
                for path in (OUT / "probes").glob(f"{ep['id']}_{arm}_*_{ti}.json"):
                    pp = read(path)
                    rendered = remove_rendered_row(r, pp["row_id"])
                    assert pp["rendered_request"] == rendered
                    assert pp["generation"]["prompt_ids"] == prompt_ids(rendered)
                    gg = pp["generation"]
                    assert pp["score"] == f.score(
                        turn, gg["text"], gg["output_ids"], gg["eos"]
                    )
                    assert pp["token_changed"] == (
                        (gg["output_ids"], gg["eos"])
                        != (r["generation"]["output_ids"], r["generation"]["eos"])
                    )
                    assert pp["text_changed"] == (gg["text"] != r["generation"]["text"])
                    assert pp["semantic_changed"] == (
                        semantic_answer(gg["text"])
                        != semantic_answer(r["generation"]["text"])
                    )
                    assert pp["score_changes"] == {
                        k: dict(original=v, without_row=pp["score"][k])
                        for k, v in r["score"].items()
                        if v != pp["score"][k]
                    }
                history.append(r["generation"])
                records.append(r)
    summary = read(OUT / "summary.json")
    assert all(summary[k] == v for k, v in summarize(episodes, records).items())
    assert read(OUT / "false-admission-effects.json") == effects(records)
    assert not any(key in summary for key in ("verdict", "terms"))
    assert summary["gpu_held_seconds"] <= CAP_SECONDS
    assert not (OUT / "RUNNING.flag").exists()
    g.write(
        OUT / "audit.json",
        dict(
            records=len(records),
            runtime_saved_score_replay=True,
            metrics_recomputed=True,
            arm_and_probe_history_reconstructed=True,
            probe_scores_recomputed=True,
            frozen_hashes_verified=True,
            diagnostic_no_gate_label=True,
        ),
    )
    print("Diagnostic saved-record verification complete", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True, choices=("prepare", "run", "audit"))
    globals()[parser.parse_args().mode]()


if __name__ == "__main__":
    main()
