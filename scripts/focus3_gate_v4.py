#!/usr/bin/env python3
"""New FOCUS-3 v4 registration; CPU admission stop precedes any GPU use."""

from __future__ import annotations

import argparse
import json
import os
import random
import subprocess
import time

from scripts import focus3_gate as g
from scripts import focus3_gate_v3 as v3
from stencil import focus3 as f

OUT = g.ROOT / "results/quick-checks/focus3-gate/v4"
PARENT = OUT.parent

DEV = g.ROOT / "data/classifier/model/relations/calibration/gpu-seed0-dev.npz"
STANDING, CANCEL, COMPLETE, OVERRIDE = v3.STANDING, v3.CANCEL, v3.COMPLETE, v3.OVERRIDE

V4_READING = """# FOCUS-3 gate v4 — pre-written reading (2026-09-06)

User-authorized repair; fit/train NONE. Frozen ft and seed0 relations models
unchanged, historical admission lineage caveats retained. Calibration-on: ONLY
committed GPU seed0 DEV logits, original scenario-disjoint576-row split.
Evaluation-on: unchanged v3 templates, fresh lists30321 setup/30322 gate (16/64).
These are reused development wordings, not independent-author or new scenarios.
The three known misses ARE in setup and gate; report without editing the bank.
Enrichment3 originals +90 handwritten relatives is evaluation-derived development
material for a LATER refit ONLY, excluded from current calibration/inference.
No sealed IFEval/BFCL inputs, fitting, background launches, signals or push.

RUNTIME VALUES, registered before calibration or setup: status passes through
live/superseded/cancelled/completed; scope global or task:<visible semantic name>;
metadata {"key": semantic sort-order/tag/instruction}, no opaque key/version/task_id.
Relation message = entire prose prefix before Sort request/payload block, keeping
all prose sentences; no pairs for payload-only sentences. Original exact span
start/end offsets remain. prev_user = last sentence of previous user's prose
prefix or None (not earlier sentences in this message). Admission classifier
still gets its original spans and up-to-three preceding prefixed sentences.
Pair rendering is checked against trainer normalize_row/render_pair on fixtures.
Positive label thresholds .94/.50/.50/.50 and admission .95 unchanged.
None guard = linear90th percentile DEV gold-none P(none); if >5% DEV positives
meet >=cutoff, use linear95th. If95th still violates5%, stop, never retune.
Chosen cutoff and denominators recorded in calibration.json before setup.
Same-kind positive target with highest proposed-label probability wins; stable
source-order ties. Broad task closure considers all kinds and retains atomic
whole-task completion. Existing scope/status guards and no-positive admission
requirement retained. No new key/scope outcome rescue.

PRE-GATE CPU STOP: all36 gold admissions (initial order16, tag16, switched task4)
and >=11/12 gold transitions, applied to correct source row with exact source
retirement/replacement state; no overflow; all96 setup records required.
Report per-label gold/proposed/applied and recall, gold-none pair confusion and
P(none) quantiles, plus none-pair probabilities on gold-admit spans. Report known
phrasing membership, never exclude it. Failure INELIGIBLE-ADMISSION, zero GPU/gate.
If eligible: O competence>=15/16 with unchanged v2 cues and C preflight recheck.
Then exactly64 C/O/N/T episodes, no48 fallback or outcome-based retries.

V3 gate readings unchanged: C exact>=48/64 and>=12/16 per family; absolute C/O
stale distance<=4/64 and final success distance<=4/64; C false retirement<=2/64
(including missing admissions), broken<=2/64; stale C<T; no contradictory recaps.
All1536 gate records required. N descriptive. No masking; same greedy cap64,
trunk, renderer/defaults, checkers, raw records/history and endpoint semantics.

Fresh10800 GPU-held seconds includes load/setup/classification/generation.
After O setup, elapsed+1.25*slowest_episode*64*4 must be<=10770s or INCOMPLETE.
Wait for all quick-check RUNNING.flags and other compute jobs to clear; Brian's
permanent llama-server pid2705 is exempt and untouched. Atomically claim own
v4/RUNNING.flag under review lock; remove own flag on natural exit only.
Foreground, cooperative cap, never terminate or signal a process.
All sources/model/bank/reading/calibration hashes committed before setup scores.
Same-run records/traces/diagnostics, summary, audit and outcome retained.
"""


def configure():
    g.OUT = OUT
    g.gpu_ready = gpu_ready


def source_hashes():
    hashes = g.sources()
    for p in (
        g.ROOT / "scripts/focus3_gate_v4.py",
        g.ROOT / "scripts/focus3_gate_v3.py",
        g.ROOT / "scripts/train_relations.py",
        g.ROOT / "tests/test_focus3_gate_v4.py",
        g.ROOT / "data/classifier/relations/astra-enrich-2.jsonl",
        OUT / "calibration.json",
        OUT / "registration.md",
        DEV,
    ):
        hashes[str(p.relative_to(g.ROOT))] = g.digest(p)
    return hashes


def calibration_rule(logits, labels, overflow):
    import numpy as np

    logits, labels = np.asarray(logits), np.asarray(labels)
    assert logits.shape == (len(labels), 5) and np.isfinite(logits).all()
    assert not np.asarray(overflow).any(), "DEV overflow: calibration undefined"
    ex = np.exp(logits - logits.max(axis=1, keepdims=True))
    pn = (ex / ex.sum(axis=1, keepdims=True))[:, 0]
    none, positive = pn[labels == 0], pn[labels != 0]
    assert len(none) and len(positive)
    candidates = []
    for q in (0.90, 0.95):
        cutoff = float(np.quantile(none, q, method="linear"))
        count = int((positive >= cutoff).sum())
        candidates.append(
            dict(
                quantile=q,
                threshold=cutoff,
                positive_as_none=count,
                positive_total=len(positive),
                positive_rate=count / len(positive),
                none_admitted=int((none >= cutoff).sum()),
                none_total=len(none),
            )
        )
    chosen = candidates[0] if candidates[0]["positive_rate"] <= 0.05 else candidates[1]
    return dict(
        chosen=chosen,
        candidates=candidates,
        eligible=chosen["positive_rate"] <= 0.05,
        gold_none_quantiles=quantiles(none),
        positive_quantiles=quantiles(positive),
    )


def calibrate():
    import numpy as np

    assert not (OUT / "calibration.json").exists()
    manifest = json.loads(
        (g.ROOT / "data/classifier/model/relations/manifest.json").read_text()
    )
    assert g.digest(DEV) == manifest["artifact_sha256"]["calibration/gpu-seed0-dev.npz"]
    committed = subprocess.check_output(
        ["git", "show", "HEAD:" + str(DEV.relative_to(g.ROOT))], cwd=g.ROOT
    )
    assert committed == DEV.read_bytes()
    z = np.load(DEV, allow_pickle=False)
    result = calibration_rule(z["logits"], z["labels"], z["overflow"])
    result.update(
        source=str(DEV.relative_to(g.ROOT)),
        source_sha256=g.digest(DEV),
        split_sha256=str(z["split_sha256"]),
        rows=len(z["labels"]),
        registration_sha256=g.digest(OUT / "registration.md"),
    )
    g.write(OUT / "calibration.json", result)
    print(json.dumps(result), flush=True)


def quantiles(values):
    import numpy as np

    v = list(values)
    return dict(
        n=len(v),
        values={
            str(q): float(np.quantile(v, q, method="linear"))
            for q in (0, 0.1, 0.5, 0.9, 0.95, 0.98, 1)
        }
        if v
        else {},
    )


def gpu_ready():
    flags = sorted(
        str(p.relative_to(g.ROOT))
        for p in (g.ROOT / "results/quick-checks").rglob("RUNNING.flag")
    )
    query = subprocess.check_output(
        [
            "nvidia-smi",
            "--query-compute-apps=pid,process_name",
            "--format=csv,noheader",
        ],
        text=True,
    )
    other = [
        line
        for line in query.splitlines()
        if line.strip() and line.split(",", 1)[0].strip() != "2705"
    ]
    return not flags and not other, dict(
        flags=flags, compute=query.strip(), other_compute=other, exempt_pid=2705
    )


def author_fixture():
    # Exact v3 authoring, including all three known misses; only list seeds vary.
    return json.loads((PARENT / "v3/authoring.json").read_text())


def prepare():
    configure()
    assert not (OUT / "freeze.json").exists()
    calibration = json.loads((OUT / "calibration.json").read_text())
    assert calibration["eligible"]
    assert f.NONE_PAIR_THRESHOLD == calibration["chosen"]["threshold"]
    fixture = author_fixture()
    bank = g.build_bank(fixture, setup_seed=30321, gate_seed=30322)
    for episodes in bank.values():
        for ep in episodes:
            for ti, turn in enumerate(ep["turns"]):
                for event in turn["events"]:
                    if "target" in event:
                        rid = f"{ti}:{turn['text'].index(event['span'])}"
                        ep["gold_keys"][rid] = ep["gold_keys"][event["target"]]
    g.validate_bank(bank)
    g.write(OUT / "authoring.json", fixture)
    g.write(OUT / "bank.json", bank)
    (OUT / "README.md").write_text(V4_READING)
    (OUT / "RESULTS.md").write_text(
        V4_READING + "\n## Outcome\n\nPENDING; no setup/gate inference yet.\n"
    )
    g.write(
        OUT / "freeze.json",
        dict(
            version=4,
            seed=30322,
            setup_seed=30321,
            hashes=source_hashes(),
            reading=V4_READING,
            cap=g.CAP,
            gpu_cap=g.BUDGET,
            created=time.time(),
        ),
    )
    print(json.dumps(dict(state="V4_CPU_READY", setup=16, gate=64)), flush=True)


def verify_freeze():
    configure()
    freeze = json.loads((OUT / "freeze.json").read_text())
    assert freeze["hashes"] == source_hashes(), "frozen drift"
    for name in ("README.md", "freeze.json", "bank.json", "authoring.json"):
        data = subprocess.check_output(
            ["git", "show", "HEAD:" + str((OUT / name).relative_to(g.ROOT))], cwd=g.ROOT
        )
        assert data == (OUT / name).read_bytes(), name
    return freeze


def event_checks(turn, ti, trace, gold_trace):
    checks = v3.event_checks(turn, ti, trace, gold_trace)
    for c, event in zip(checks, turn["events"], strict=True):
        if "target" in event:
            rid = event["target"]
            source = next((r for r in trace["after"] if r["id"] == rid), None)
            gold_source = next(r for r in gold_trace["after"] if r["id"] == rid)
            fields = ("id", "text", "scope", "kind", "version", "status")
            c["source_state_matches"] = source is not None and all(
                source[k] == gold_source[k] for k in fields
            )
            c["gold_source_id"] = rid
            c["passed"] = c["passed"] and c["source_state_matches"]
    return checks


def transition_diagnostics(records):
    pairs = [p for r in records for p in r["trace"]["pairs"]]
    table = {}
    for label in f.LABELS[1:]:
        events = [c for r in records for c in r["event_checks"] if c["label"] == label]
        gold_pairs = [p for p in pairs if p["gold"] == label]
        applied = sum(c["passed"] for c in events)
        table[label] = dict(
            gold=len(events),
            paired=len(gold_pairs),
            proposed=sum(p["proposed"] == label for p in gold_pairs),
            applied=applied,
            recall=applied / len(events) if events else None,
        )
    none = [p for p in pairs if p["gold"] == "none"]
    admitted = [
        p["probabilities"][0]
        for r in records
        for p in r["trace"]["pairs"]
        if any(
            e["label"] == "admit" and e["span"] == p["input"]["target_span"]["text"]
            for e in r["turn"]["events"]
        )
    ]
    known = [
        ("supersedes", "Replace the sorting rule"),
        ("cancels", "no longer applies"),
        ("completes", "That concludes task"),
    ]
    return dict(
        per_label=table,
        gold_none=dict(
            total=len(none),
            proposed_positive=sum(p["proposed"] != "none" for p in none),
            applied_positive=sum(p["applied"] != "none" for p in none),
            guard_admitted=sum(
                p["probabilities"][0] >= f.NONE_PAIR_THRESHOLD for p in none
            ),
            p_none=quantiles(p["probabilities"][0] for p in none),
        ),
        gold_admit_pair_p_none=quantiles(admitted),
        known_phrasings=[
            dict(
                episode=r["episode"],
                span=c["span"],
                label=c["label"],
                passed=c["passed"],
            )
            for r in records
            for c in r["event_checks"]
            if any(c["label"] == label and text in c["span"] for label, text in known)
        ],
    )


def eligibility_summary(records):
    checks = [c for r in records for c in r["event_checks"]]
    groups = dict(
        initial_order=[c for c in checks if c["initial_order"]],
        admissions=[c for c in checks if c["label"] == "admit"],
        transitions=[c for c in checks if c["label"] in f.LABELS[1:]],
    )
    counts = {
        k: dict(passed=sum(c["passed"] for c in v), total=len(v))
        for k, v in groups.items()
    }
    complete = len(records) == 96 and len({r["episode"] for r in records}) == 16
    eligible = (
        complete
        and counts["initial_order"] == dict(passed=16, total=16)
        and counts["admissions"] == dict(passed=36, total=36)
        and counts["transitions"]["total"] == 12
        and counts["transitions"]["passed"] >= 11
        and not any(r["trace"]["overflow"] for r in records)
    )
    return dict(
        eligible=eligible,
        counts=counts,
        complete=complete,
        records=len(records),
        diagnostics=transition_diagnostics(records),
        failures=[
            dict(episode=r["episode"], turn_index=r["turn_index"], **c)
            for r in records
            for c in r["event_checks"]
            if not c["passed"]
        ],
    )


def preflight():
    freeze = verify_freeze()
    assert not (OUT / "setup-admission/started.json").exists(), (
        "one-shot setup already started"
    )
    g.write(
        OUT / "setup-admission/started.json",
        dict(
            time=time.time(),
            pid=os.getpid(),
            commit=subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=g.ROOT, text=True
            ).strip(),
        ),
    )
    bank = json.loads((OUT / "bank.json").read_text())
    classifier = f.FrozenClassifier()
    records = []
    started = time.monotonic()
    for ep in bank["setup"]:
        runtime, oracle = f.Runtime(classifier), f.Oracle()
        traces = []
        for ti, turn in enumerate(ep["turns"]):
            trace = runtime.update(turn["text"], ti)
            gold_trace = oracle.update(turn["text"], ti, turn["events"])
            for p in trace["pairs"]:
                p["gold"] = g.gold_pair_label(p["input"], turn)
            record = dict(
                episode=ep["id"],
                family=ep["family"],
                arm="C",
                turn_index=ti,
                turn=turn,
                trace=trace,
                gold_trace=gold_trace,
                live=[
                    f.wire(r) for r in runtime.register.live(runtime.task, turn["kind"])
                ],
                gold_live=[
                    f.wire(r) for r in oracle.register.live(oracle.task, turn["kind"])
                ],
                agreement=f.agreement(
                    runtime.register.live(runtime.task, turn["kind"]),
                    oracle.register.live(oracle.task, turn["kind"]),
                    ep["gold_keys"],
                ),
                event_checks=event_checks(turn, ti, trace, gold_trace),
            )
            assert len(trace["admissions"]) == len(f.sentences(turn["text"]))
            assert all(
                "model_input" in a and len(a["probabilities"]) == 3
                for a in trace["admissions"]
            )
            g.write(OUT / "setup-admission/records" / f"{ep['id']}_C_{ti}.json", record)
            records.append(record)
            traces.append(record)
            g.write(OUT / "setup-admission/traces" / f"{ep['id']}_C.json", traces)
        print(
            json.dumps(
                dict(
                    stage="setup-admission",
                    episode=ep["id"],
                    missed=sum(
                        not c["passed"] for r in traces for c in r["event_checks"]
                    ),
                )
            ),
            flush=True,
        )
    result = eligibility_summary(records)
    result.update(
        cpu_seconds=time.monotonic() - started,
        freeze_sha256=g.digest(OUT / "freeze.json"),
    )
    g.write(OUT / "setup-admission/summary.json", result)
    if not result["eligible"]:
        g.write(
            OUT / "summary.json",
            dict(
                verdict="INELIGIBLE-ADMISSION",
                reason="setup C gold event miss",
                admission=result,
                gpu_held_seconds=0.0,
                gate_records=0,
                generation_records=0,
                no_masking=True,
                freeze_sha256=g.digest(OUT / "freeze.json"),
            ),
        )
    assert freeze["hashes"] == source_hashes()
    print(
        json.dumps(
            dict(
                eligible=result["eligible"],
                counts=result["counts"],
                diagnostics=result["diagnostics"],
                cpu_seconds=result["cpu_seconds"],
            )
        ),
        flush=True,
    )


def run():
    verify_freeze()
    admission = json.loads((OUT / "setup-admission/summary.json").read_text())
    assert admission["eligible"], "INELIGIBLE-ADMISSION: gate prohibited"
    assert not (OUT / "started.json").exists()
    bank = json.loads((OUT / "bank.json").read_text())
    with g.claim_gpu():
        started = time.monotonic()
        g.write(
            OUT / "started.json",
            dict(
                time=time.time(),
                pid=os.getpid(),
                commit=subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=g.ROOT, text=True
                ).strip(),
            ),
        )
        trunk = None
        summary = dict(verdict="INCOMPLETE")
        try:
            classifier = f.FrozenClassifier()
            trunk = g.Trunk(started + g.BUDGET - 30)
            setup, durations, checks = [], [], []
            for ep in bank["setup"]:
                t = time.monotonic()
                rr = g.run_episode(ep, "O", trunk, classifier, "setup")
                durations.append(time.monotonic() - t)
                setup.extend(rr)
                for r in rr:
                    checks.append(
                        dict(
                            r,
                            event_checks=event_checks(
                                r["turn"], r["turn_index"], r["trace"], r["gold_trace"]
                            ),
                        )
                    )
            competence = sum(
                f.episode_metrics([r for r in setup if r["episode"] == e["id"]])[
                    "final_success"
                ]
                for e in bank["setup"]
            )
            selection = dict(
                competence=competence,
                required=15,
                n=64,
                durations=durations,
                projection=time.monotonic() - started + 1.25 * max(durations) * 64 * 4,
                admission=eligibility_summary(checks),
                written_before_gate=True,
            )
            g.write(OUT / "selection.json", selection)
            if not selection["admission"]["eligible"]:
                summary = dict(verdict="INELIGIBLE-ADMISSION", selection=selection)
            elif competence < 15:
                summary = dict(
                    verdict="INELIGIBLE", reason="setup competence", selection=selection
                )
            elif selection["projection"] > g.BUDGET - 30:
                summary = dict(
                    verdict="INCOMPLETE", reason="cost projection", selection=selection
                )
            else:
                records = []
                rng = random.Random(30303)
                for ep in bank["gate"]:
                    arms = list(g.ARMS)
                    rng.shuffle(arms)
                    for arm in arms:
                        records.extend(
                            g.run_episode(ep, arm, trunk, classifier, "gate")
                        )
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
                summary = f.summarize(bank["gate"], records, 64)
                summary.update(
                    diagnostics=g.diagnostics(records),
                    selection=selection,
                    record_count=len(records),
                    peak_gpu_bytes=trunk.backend.peak_memory,
                )
                if any(r["trace"].get("overflow", False) for r in records):
                    summary.update(
                        verdict="FAIL", reason="classifier fail-open overflow"
                    )
        except TimeoutError as exc:
            summary = dict(verdict="INCOMPLETE", reason=str(exc))
        except Exception as exc:
            summary = dict(verdict="FAIL", reason=repr(exc))
            raise
        finally:
            if trunk is not None:
                trunk.backend.close()
            summary.update(
                gpu_held_seconds=time.monotonic() - started,
                no_masking=True,
                admission=admission,
                freeze_sha256=g.digest(OUT / "freeze.json"),
            )
            g.write(OUT / "summary.json", summary)
            print(json.dumps(summary), flush=True)
    verify_freeze()


def audit():
    import numpy as np

    from scripts import train_relations as trainer

    verify_freeze()
    z = np.load(DEV, allow_pickle=False)
    calibration = json.loads((OUT / "calibration.json").read_text())
    rebuilt = calibration_rule(z["logits"], z["labels"], z["overflow"])
    assert all(calibration[k] == value for k, value in rebuilt.items())
    assert f.NONE_PAIR_THRESHOLD == calibration["chosen"]["threshold"]
    bank = json.loads((OUT / "bank.json").read_text())
    g.validate_bank(bank)
    records = []

    class Replay:
        record = None

        def relations(self, pairs):
            saved = self.record["trace"]["pairs"]
            assert pairs == [p["input"] for p in saved]
            return [
                {
                    k: v
                    for k, v in p.items()
                    if k not in ("input", "proposed", "applied", "gold")
                }
                for p in saved
            ]

        def admission(self, spans, previous):
            saved = self.record["trace"]["admissions"]
            assert spans == [p["span"] for p in saved]
            return [
                {k: v for k, v in p.items() if k not in ("span", "start", "accepted")}
                for p in saved
            ]

    for ep in bank["setup"]:
        oracle = f.Oracle()
        replay = Replay()
        runtime = f.Runtime(replay)
        previous = ""
        before = []
        traces = []
        for ti, turn in enumerate(ep["turns"]):
            r = json.loads(
                (
                    OUT / "setup-admission/records" / f"{ep['id']}_C_{ti}.json"
                ).read_text()
            )
            assert r["turn"] == turn and r["trace"]["before"] == before
            for pair in r["trace"]["pairs"]:
                value = pair["input"]
                rule = value["old_rule"]
                assert set(rule) == {"text", "status", "scope", "key"}
                assert rule["status"] in {
                    "live",
                    "superseded",
                    "cancelled",
                    "completed",
                }
                assert rule["scope"] == "global" or rule["scope"].startswith("task:")
                assert rule["key"] in {"sort-order", "tag", "instruction"}
                normalized = trainer.normalize_row(
                    dict(value, label=pair["gold"], author="astra")
                )
                assert not normalized["span_offsets_repaired"]
                assert list(f.pair_input(value)) == pair["model_input"]
                assert f.pair_input(value) == trainer.render_pair(normalized)
                assert (
                    value["prev_user"] is None
                    or len(f.sentences(value["prev_user"])) == 1
                )
            for prediction in r["trace"]["pairs"] + r["trace"]["admissions"]:
                assert not prediction["overflow"]
                logits = np.array(prediction["logits"], dtype=np.float64)
                p = np.exp(logits - logits.max())
                np.testing.assert_allclose(
                    p / p.sum(), prediction["probabilities"], atol=1e-12, rtol=1e-12
                )
            replay.record = r
            replayed = runtime.update(turn["text"], ti)
            for p in replayed["pairs"]:
                p["gold"] = g.gold_pair_label(p["input"], turn)
            assert replayed == r["trace"], (ep["id"], ti, "runtime replay")
            assert r["gold_trace"] == oracle.update(turn["text"], ti, turn["events"])
            assert r["event_checks"] == event_checks(
                turn, ti, r["trace"], r["gold_trace"]
            )
            cc = runtime.register.live(runtime.task, turn["kind"])
            oo = oracle.register.live(oracle.task, turn["kind"])
            assert r["live"] == [f.wire(row) for row in cc]
            assert r["gold_live"] == [f.wire(row) for row in oo]
            assert r["agreement"] == f.agreement(cc, oo, ep["gold_keys"])
            expected = f.admission_inputs(
                [s for _, s in f.sentences(turn["text"])], previous
            )
            assert [a["model_input"] for a in r["trace"]["admissions"]] == [
                list(p) for p in expected
            ]
            before, previous = r["trace"]["after"], turn["text"]
            records.append(r)
            traces.append(r)
        assert traces == json.loads(
            (OUT / "setup-admission/traces" / f"{ep['id']}_C.json").read_text()
        )
    actual = json.loads((OUT / "setup-admission/summary.json").read_text())
    assert all(actual[k] == v for k, v in eligibility_summary(records).items())
    summary = json.loads((OUT / "summary.json").read_text())
    if not actual["eligible"]:
        assert summary["verdict"] == "INELIGIBLE-ADMISSION"
        assert not (OUT / "started.json").exists() and not (OUT / "gate").exists()
        assert summary["gpu_held_seconds"] == 0
    else:
        # Parent audit accepts its historical hash set, which is a strict subset
        # of v4's fully verified hash set. Keep the saved freeze untouched.
        original_sources = g.sources
        try:
            hashes = source_hashes()
            g.sources = lambda: hashes
            g.audit()
        finally:
            g.sources = original_sources
    result = dict(
        audit="PASS",
        setup_admission_records=len(records),
        admission_counts=actual["counts"],
        verdict=summary["verdict"],
        source_hashes_match=True,
        runtime_value_and_trainer_parity=True,
        probabilities_recomputed_from_logits=True,
        dev_calibration_recomputed=True,
        setup_pairs=sum(len(r["trace"]["pairs"]) for r in records),
    )
    g.write(OUT / "audit.json", result)
    print(json.dumps(result), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        required=True,
        choices=(
            "calibrate",
            "prepare",
            "preflight",
            "ready",
            "run",
            "audit",
        ),
    )
    args = parser.parse_args()
    configure()
    if args.mode == "ready":
        print(json.dumps(g.gpu_ready()))
    else:
        globals()[args.mode]()


if __name__ == "__main__":
    main()
