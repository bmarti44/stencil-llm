#!/usr/bin/env python3
"""New FOCUS-3 v3 registration; CPU admission stop precedes any GPU use."""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import subprocess
import time

from scripts import focus3_gate as g
from stencil import focus3 as f

OUT = g.ROOT / "results/quick-checks/focus3-gate/v3"
PARENT = OUT.parent
STANDING = (
    "From now on, for task {task_a} keep the payload sorted in {direction} order.",
    "Always sort payloads in {direction} order for task {task_a}.",
    "For task {task_a}, the payload must be in {direction} order "
    "until I say otherwise.",
    "Whenever you sort for task {task_a}, use {direction} order.",
    "For task {task_a}, always sort the payload in {direction} order.",
    "Going forward, keep every payload for task {task_a} in {direction} order.",
    "Each time you handle a payload for task {task_a}, sort it in {direction} order.",
    "Use {direction} order for all payloads in task {task_a} from now on.",
)
CANCEL = (
    "Cancel the sorting rule for task {task_a}.",
    "Drop the ordering requirement for task {task_a}.",
    "The sorting rule for task {task_a} no longer applies.",
    "Stop following the earlier sorting rule for task {task_a}.",
)
COMPLETE = (
    "Task {task_a} is complete.",
    "We are finished with task {task_a}.",
    "Task {task_a} is done now.",
    "That concludes task {task_a}.",
)
OVERRIDE = (
    "From now on, use {opposite} order instead of {direction} order for task {task_a}.",
    "Replace the sorting rule for task {task_a}: always use {opposite} order.",
    "For task {task_a}, switch the standing order from {direction} to {opposite}.",
    "For task {task_a}, keep all payloads in {opposite} order from now on instead.",
)
V3_READING = """# FOCUS-3 gate v3 — pre-written reading (2026-09-06)

New user-authorized registration after the v2 bank/spec mismatch. Fit/train/tune:
NONE. Fit-on: existing ft and seed0 relations checkpoints, with the historical
admission development-influence caveats in LABELS.md. Evaluated-on: new synthetic
v3 prose/values, setup seed30311 and gate seed30312. No sealed/benchmark inputs.
Astra re-authors inherited gpt-5.5 scenarios: no independent-author claim for v3.
All eight standing paraphrases are fixed before CPU probe scores and used without
score-based selection. Both directions of v2 and all eight are reported. Runtime
admission segment A is the latest up-to-three preceding user sentences, each with
user: prefix, including earlier sentences of this message; segment B stays
[user] target. Previous-user context matches the available user-only runtime API.
Relation encoding, thresholds .94/.50/.50/.50, admission .95/none-pair .98,
splitter, checkers, request/schema/default-row renderer, greedy cap64 and no
masking are unchanged. Every scored span is logged, even if a relation consumes it.
No outcome-based rescue, filtering, fitting, threshold change or repeat gate.

Bank: 16 setup (4/family), 64 gate (16/family), same four families, six requests
per episode, separate seeded lists. Natural varied standing instructions, overrides,
cancellations, completions, switches/returns; hard-none and prose checks retained.
All bank/source/checkpoint hashes and this reading commit before setup inference.
Diagnostic probe is authorized development inspection, not selection or fitting.

PRE-GATE STOP, first on CPU: replay C and O through all 16 setup episodes using
ordinary user messages only in C. Initial gold ordering admissions must be16/16.
Also require every gold standing admission (tags and new tasks) and replacement,
and every gold cancellation/completion (8 events), to apply to the actual gold
source row. A missing target or merely out-of-scope live target is not retired.
Check exact source text/scope/kind/version/status against O at each gold event.
Any miss -> INELIGIBLE-ADMISSION; stop before loading the trunk or opening gate
inference. Retain all setup per-turn records and traces, including probabilities.
No generated-response metrics are claimed for this CPU eligibility replay.
If eligible, wait for GPU/flags/lock to clear, claim own RUNNING.flag, run O setup
competence>=15/16 using v2 cues; otherwise INELIGIBLE. Recheck C eligibility on
that setup's traces before gate. No retries or setup-selected bank changes.

C/O/N/T definitions, exact state comparison at EVERY task answer (including
initial admission and default rows), scoring, and v2 endpoint readings unchanged.
PASS requires all: C register-exact>=48/64 and>=12/16 in each family; absolute
C/O stale-execution distance<=4/64 and final-success distance<=4/64; C false
retirements<=2/64 (includes missing gold admissions); C breakage<=2/64; C stale<T
stale; zero contradictory recaps; all1536 gate records. N descriptive. No population
or statistical superiority claim. O receives gold events only, never answers.

Fresh cap10800 GPU-held seconds includes load, setup, classification and generation.
V2's measured64 projection3505s fits; conservative original cap projection9454s.
After16 O setup episodes, project elapsed+1.25*slowest_episode*64*4; above10770s
stops INCOMPLETE. Exactly64 or none: no48 fallback in this registration. Deadline
checked cooperatively, no signals/termination/background launches. Empty compute
list and all quick-check RUNNING.flags required under brief .review.lock claim;
write/remove only own flag. Missing work/budget INCOMPLETE; overflow/invariant FAIL.

Same-run artifacts: CPU probe table, setup-admission records/traces/summary,
setup/gate records and traces if eligible (all v2 raw prompt/token/EOS/score,
probabilities/logits/model inputs, gold/applied state, provenance, timing fields),
summary, audits and RESULTS.md. Pre-written reading stays above appended outcome.
"""


def configure():
    g.OUT = OUT


def source_hashes():
    hashes = g.sources()
    for p in (
        g.ROOT / "scripts/focus3_gate_v3.py",
        g.ROOT / "tests/test_focus3_gate_v3.py",
        OUT / "probe.json",
        OUT / "probe.md",
        OUT / "probe-recipe.json",
        OUT / "probe-original.json",
    ):
        hashes[str(p.relative_to(g.ROOT))] = g.digest(p)
    return hashes


def probe():
    configure()
    OUT.mkdir(parents=True, exist_ok=True)
    assert not (OUT / "probe.json").exists(), "probe already exists"
    templates = (
        "For task {task_a}, sort the payload in {direction} order.",
    ) + STANDING
    # Durable pre-score recipe; all eight enter the bank regardless of scores.
    g.write(
        OUT / "probe-recipe.json",
        dict(
            templates=templates,
            task="Inventory",
            tag=73,
            directions=["ascending", "descending"],
            selection=False,
        ),
    )
    classifier = f.FrozenClassifier()
    rows = []
    preceding = [
        "Work on task Inventory.",
        "For every sorting request in this conversation, keep tag equal to 73.",
    ]
    for direction in ("ascending", "descending"):
        for i, template in enumerate(templates):
            sentence = template.format(task_a="Inventory", direction=direction)
            faithful = classifier.admission(preceding + [sentence], "")[-1]
            legacy = classifier.infer(
                "ft", [("(no context)", "[user] " + sentence)], 192
            )[0]
            rows.append(
                dict(
                    template=i,
                    direction=direction,
                    sentence=sentence,
                    faithful=faithful,
                    legacy=legacy,
                )
            )
    g.write(OUT / "probe.json", dict(rows=rows, fit=False, selected=False))
    lines = [
        "# CPU admission diagnostic (not a selection)",
        "",
        "Both directions; P(rule), frozen cutoff 0.95. All eight paraphrases retained.",
        "",
        "| Sentence | Training-faithful context | V2 no-context |",
        "|---|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['sentence']} | {r['faithful']['probabilities'][1]:.6f} "
            f"| {r['legacy']['probabilities'][1]:.6f} |"
        )
    (OUT / "probe.md").write_text("\n".join(lines) + "\n")
    print((OUT / "probe.md").read_text(), flush=True)


def probe_original():
    """Same diagnostic on the first actual v2 task ID; never select bank forms."""
    assert not (OUT / "probe-original.json").exists()
    ep = json.loads((PARENT / "bank.json").read_text())["gate"][0]
    turn = ep["turns"][0]
    preceding = [s for _, s in f.sentences(turn["text"])][:2]
    classifier = f.FrozenClassifier()
    rows = []
    templates = (
        "For task {task_a}, sort the payload in {direction} order.",
    ) + STANDING
    for direction in ("ascending", "descending"):
        for i, template in enumerate(templates):
            sentence = template.format(task_a=turn["task"], direction=direction)
            rows.append(
                dict(
                    template=i,
                    direction=direction,
                    sentence=sentence,
                    faithful=classifier.admission(preceding + [sentence], "")[-1],
                    legacy=classifier.infer(
                        "ft", [("(no context)", "[user] " + sentence)], 192
                    )[0],
                )
            )
    g.write(
        OUT / "probe-original.json",
        dict(
            episode=ep["id"],
            preceding=preceding,
            rows=rows,
            selected=False,
            reason="Check task-name dependence using first v2 episode; no selection.",
        ),
    )
    print(
        json.dumps(
            [
                dict(
                    template=r["template"],
                    direction=r["direction"],
                    faithful=r["faithful"]["probabilities"][1],
                    legacy=r["legacy"]["probabilities"][1],
                )
                for r in rows
            ]
        )
    )


def author_fixture():
    fixture = json.loads((PARENT / "authoring.json").read_text())
    fixture.update(
        author_role="gpt-6-astra v3 re-author",
        authoring_seed=30311,
        lineage_declaration=(
            "Inherited scenarios, all eight pre-score standing forms retained; "
            "no fitting or selection."
        ),
    )
    fixture["setup_families"] = {}
    for fi, family in enumerate(g.FAMILIES):
        key = family.replace("-", "_")
        for split, n in (("setup", 4), ("gate", 16)):
            templates = []
            for i in range(n):
                base = (
                    fixture["setup_templates"][fi]
                    if split == "setup"
                    else fixture["families"][key][i % 4]
                )
                t = copy.deepcopy(base)
                # Every family covers all eight in gate; all eight appear in setup.
                t["id"] = f"v3_{split}_{fi}_{i:02}"
                t["initial_rule_template"] = STANDING[(fi * 4 + i) % 8]
                if family == "override":
                    t["change_template"] = OVERRIDE[i % 4]
                elif family == "cancel":
                    t["change_template"] = CANCEL[i % 4]
                elif family == "complete-and-move-on":
                    t["completion_template"] = COMPLETE[i % 4]
                    t["change_template"] = (
                        COMPLETE[i % 4]
                        + (" Work on" if i % 2 == 0 else " Switch to")
                        + " task {task_b}."
                    )
                else:
                    t["secondary_rule_template"] = (
                        STANDING[(fi * 4 + i + 1) % 8]
                        .replace("{task_a}", "{task_b}")
                        .replace("{direction}", "{opposite}")
                    )
                    t["change_template"] = (
                        ("Switch to" if i % 2 == 0 else "Work on")
                        + " task {task_b}. "
                        + t["secondary_rule_template"]
                    )
                    t["turn_templates"][-1] = (
                        "Return to" if i % 2 == 0 else "Work on"
                    ) + " task {task_a}; {final_request}"
                templates.append(t)
            if split == "setup":
                fixture["setup_families"][key] = templates
            else:
                fixture["families"][key] = templates
    return fixture


def prepare():
    configure()
    assert not (OUT / "freeze.json").exists()
    fixture = author_fixture()
    bank = g.build_bank(fixture, setup_seed=30311, gate_seed=30312)
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
    (OUT / "README.md").write_text(V3_READING)
    (OUT / "RESULTS.md").write_text(
        V3_READING + "\n## Outcome\n\nPENDING; no setup/gate inference yet.\n"
    )
    g.write(
        OUT / "freeze.json",
        dict(
            version=3,
            seed=30312,
            setup_seed=30311,
            hashes=source_hashes(),
            reading=V3_READING,
            cap=g.CAP,
            gpu_cap=g.BUDGET,
            created=time.time(),
        ),
    )
    print(json.dumps(dict(state="V3_CPU_READY", setup=16, gate=64)), flush=True)


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
    checks = []
    for event in turn["events"]:
        label = event["label"]
        rid = (
            event["target"]
            if label in ("cancels", "completes")
            else f"{ti}:{turn['text'].index(event['span'])}"
        )
        expected = next(r for r in gold_trace["after"] if r["id"] == rid)
        actual = next((r for r in trace["after"] if r["id"] == rid), None)
        fields = ("id", "text", "scope", "kind", "version", "status")
        matches = actual is not None and all(actual[k] == expected[k] for k in fields)
        applied = any(
            p["label"] == label
            and (
                p.get("target") == event["target"]
                if "target" in event
                else p.get("span") == event["span"]
            )
            for p in trace["applied"]
        )
        checks.append(
            dict(
                label=label,
                target=rid,
                span=event["span"],
                passed=matches and applied,
                state_matches=matches,
                applied=applied,
                expected=expected,
                actual=actual,
                initial_order=ti == 0
                and event.get("gold_key", "").startswith("order:"),
            )
        )
    return checks


def eligibility_summary(records):
    checks = [c for r in records for c in r["event_checks"]]
    groups = {
        "initial_order": [c for c in checks if c["initial_order"]],
        "standing": [c for c in checks if c["label"] in ("admit", "supersedes")],
        "retirements": [c for c in checks if c["label"] in ("cancels", "completes")],
    }
    counts = {
        k: dict(passed=sum(c["passed"] for c in v), total=len(v))
        for k, v in groups.items()
    }
    complete = len(records) == 96 and len({r["episode"] for r in records}) == 16
    eligible = (
        complete
        and counts["initial_order"]["total"] == 16
        and counts["standing"]["total"] == 40
        and counts["retirements"]["total"] == 8
        and all(c["passed"] for c in checks)
        and not any(r["trace"]["overflow"] for r in records)
    )
    return dict(
        eligible=eligible,
        counts=counts,
        complete=complete,
        records=len(records),
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
    verify_freeze()
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
        # of v3's fully verified hash set. Keep the saved freeze untouched.
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
    )
    g.write(OUT / "audit.json", result)
    print(json.dumps(result), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        required=True,
        choices=(
            "probe",
            "probe_original",
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
