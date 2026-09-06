#!/usr/bin/env python3
"""Disclosed check40g: same-harness generality controls, one model load."""

# ruff: noqa: E501
from __future__ import annotations

import argparse
import ast
import copy
import fcntl
import gc
import json
import os
import random
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import focus_check40e as e  # noqa: E402
import focus_check40i as i  # noqa: E402
from focus_check43 import DispatchAudit, cpu_router_test  # noqa: E402

base = e.base
OUT = ROOT / "results/quick-checks/check40g"
GO = Path.home() / ".local/lib/check40g-go/go/bin/go"
GOFMT = GO.with_name("gofmt")
SEED, LIMIT = 40060, 3600
ARMS = ("OFF", "correct", "swapped", "shuffled", "text-cue")
READING = """# Check40g prewritten reading

Unregistered, disclosed user-authorized development follow-up, 2026-09-06.
Fit/train: none. Profile-on: committed 40e competence replies for TS; fresh
synthetic 16-task cued competence banks for JSON/SQL and Python/Go, both sides,
all replies without success filtering. Evaluate-on: committed first16 40e P1
screen tasks (disclosed reuse for TS), fresh disjoint SQL/Go screen32 and Go
release168 expressions. No evaluation benchmark or sealed IFEval/BFCL input read.
No fitting, training, checkpoint selection, prompt rescue, or outcome-based tuning.

One bf16 Qwen3-30B-A3B load, inherited40e messages/Engine/greedy cap64,
sustained router bias on all48 layers and prefill/decode. Kernel parity required.
First: 1.5 * committed40c selected-bias (=alpha3 JS) on first8 40e P1 screen;
>=6/8 executable JS required; otherwise INVALID and STOP all inference.
TS: committed40e body direction alpha4.5 and6; first3 generated own positions
(one-based tokens1-3, including fence label) re-teacher-forced from the SAME32
committed competence replies; fence direction total Frobenius norm15.7 at alpha3.
Each TS configuration uses correct/shuffled/OFF/text-cue on first16 P1 screen;
OFF/text-cue shared across configurations. No best-dose selection. These are
16-task diagnostics: report raw counts; cannot meet the fixed20/32 GENERALIZES
bar, and do not silently extrapolate to32. MARGINAL if >=12 addressed successes,
else NOT under the literal reading, explicitly qualified as a16-task diagnostic.

P2 exact header: SQL table name: items (columns id INTEGER, value INTEGER). Rows:
Thresholds are integers strictly between sorted row values; both strict operators
< and >. Cued competence16 each side, >=14/16 BOTH required, then body profiles
and five-arm uncued screen32. Bias=3*(target mean - two-side mean), swapped=-bias,
shuffled seed40062 per-layer expert permutation; profiles token-weighted raw logits.
Go fresh40b-style cued competence16 each side: Python16/16 and Go>=14/16 required;
then same profile construction, scaled at alpha3 to exact frozen JS alpha3 band
Frobenius norm. Five-arm screen32. No inherited overlap veto added to user gates.
Go checker: gofmt parser, restricted zero-argument integer-return function,
optional package line, independently evaluate bounded +,-,* integer expression.
CPU go vet validates canonical functions; no arbitrary generated program executed.
All languages require exact name and arithmetic/table semantics, valid fence and
no truncation. JS positive control uses40e TS parser/transpiler with JS admitted.

Each32-task pair GENERALIZES iff correct addressed skill success>=20/32,
correct-only broken vs paired OFF<=2/32, shuffled addressed success<=4/32;
else MARGINAL iff correct>=12/32, else NOT. Absolute breakage also reported.
No competent screen => INELIGIBLE; interrupted => INCOMPLETE, no null claim.
If Go SET correct>=20/32 with ABSOLUTE broken<=2, run24 retained-history episodes:
Z SET/HOLD Go bias; SWITCH/HOLD_AFTER_SWITCH OFF; BACK/HOLD_AFTER_BACK Go bias;
CLEAR OFF. At SWITCH/BACK/CLEAR mask all preceding assistant bodies, preserve
positions and remaining KV. Zc and S share Z prefix through HOLD_AFTER_SWITCH;
Zc BACK biasOFF, S BACK shuffled; OFF full retained-history baseline.
Use EXACT40i decision function with Go renamed to JavaScript only in its input
count dictionaries: three Z SWITCH/BACK/CLEAR cells>=20 target and<=2 broken,
every Z step<=2 broken, paired switch and clear releases>=20, Zc/S BACK<=4 Go.
Report Go release separately from SET; mechanism generality requires Go closure.

Per-record consumed-dispatch counts/fractions for every layer, prefill/decode,
against unbiased router output at same hidden state (not counterfactual OFF path).
Records journaled immediately; profile statistics/bias tensors saved before screen.
One foreground allocation including load/checks/profiles/scoring/cleanup<=3600s.
Cooperative token deadline reserves cleanup; no process signals or termination.
Maximum generations:8+128TS+32SQLcomp+160SQL+32Gocomp+160Go+480release=1000.
Prior40i measured mean1.924s/generation +load374s; budget estimate with25% compute
reserve and150s profiles/checkers:374+1.25*(1000*1.924+150)=2966.5s. Instrumentation
may cost more: preserve exact task counts, cooperate at deadline and label incomplete.
Flags coordinated under short review lock; no other Stencil compute, pid2705 exempt.
Explicit pathspec commits, results force-added, no push.
"""


def write(name, value):
    base.write_json(OUT / name, value)


def score(text, task, truncated=False):
    if task["pair"] != "Go":
        s = e.score(text, task, truncated)
        if task.get("js_control"):
            s["broken"] = bool(
                truncated
                or s["fence_error"]
                or not s["semantic"]
                or s["identity"] not in ("Python", "JavaScript")
            )
            s["valid_skill"] = None if s["broken"] else s["identity"]
        return s
    py = e.score(text, dict(task, pair="P1"), truncated)
    if py["identity"] == "Python":
        return py
    code, fence = base.extract_code(text)
    detail, semantic, identity = {}, False, "invalid"
    match = re.fullmatch(
        r"\s*(?:package\s+\w+\s+)?func\s+"
        + re.escape(task["name"])
        + r"\s*\(\s*\)\s+(?:int|int64|int32)\s*\{\s*return\s+([\d\s()+*\-]+)\s*;?\s*\}\s*",
        code,
    )
    if match:
        proc = subprocess.run([str(GOFMT)], input=code, text=True, capture_output=True)
        detail["gofmt_exit"] = proc.returncode
        if proc.returncode == 0:
            try:
                value = e.arithmetic(ast.parse(match[1].strip(), mode="eval").body)
                identity, semantic = "Go", value == task["expected"]
                detail["value"] = value
            except (SyntaxError, ValueError, TypeError):
                pass
    broken = bool(truncated or fence or identity != "Go" or not semantic)
    return dict(
        identity=identity,
        semantic=semantic,
        broken=broken,
        valid_skill=None if broken else identity,
        fence_error=fence,
        detail=detail,
    )


def banks():
    old = json.loads((e.OUT / "banks.json").read_text())
    result = {"TS": old["P1"], "P2": {}, "Go": {}}
    rng = random.Random(SEED)
    for split, n in [("competence", 16), ("screen", 32)]:
        sql, go = [], []
        for j in range(n):
            values = rng.sample(
                range(2, 35) if split == "competence" else range(40, 99), 3
            )
            values = [v * 2 for v in values]
            rows = [dict(id=k + 1, value=v) for k, v in enumerate(values)]
            ordered = sorted(values)
            threshold = (ordered[j % 2] + ordered[j % 2 + 1]) // 2
            assert ordered[j % 2] < threshold < ordered[j % 2 + 1]
            op = (">", "<")[j % 2]
            t = dict(
                id=f"P2_{split}_{j:02d}",
                pair="P2",
                rows=rows,
                op=op,
                threshold=threshold,
            )
            t["expected"] = [r for r in rows if e.compare(r["value"], op, threshold)]
            t["prompt"] = (
                f"SQL table name: items (columns id INTEGER, value INTEGER). Rows:\n{json.dumps(rows, separators=(',', ':'))}\nReturn the matching rows as a list where value {op} {threshold}. Keep both columns."
            )
            sql.append(t)
            a, b, c, d = rng.sample(
                range(102, 135) if split == "competence" else range(140, 190), 4
            )
            expr = [
                f"(({a}+{b})*({c}-{d}))",
                f"(({a}*{b})+({c}*{d}))",
                f"(({a}-{b})-({c}+{d}))",
            ][j % 3]
            name = f"solve_{split}_{j:02d}"
            go.append(
                dict(
                    id=f"Go_{split}_{j:02d}",
                    pair="Go",
                    name=name,
                    expression=expr,
                    expected=e.arithmetic(ast.parse(expr, mode="eval").body),
                    prompt=f"Write a zero-argument function named {name} that returns {expr}.",
                )
            )
        result["P2"][split], result["Go"][split] = sql, go
    old_seed = i.SEED
    i.SEED = SEED + 3
    try:
        release = i.make_tasks(24)
    finally:
        i.SEED = old_seed
    old_i = {
        t["expression"]
        for episode in json.loads((i.OUT / "tasks.json").read_text())
        for t in episode.values()
    }
    for episode in release:
        for t in episode.values():
            assert t["expression"] not in old_i
            t.update(
                pair="Go",
                expected=e.arithmetic(ast.parse(t["expression"], mode="eval").body),
            )
    result["release"] = release
    return result


def screen_summary(rows, phase, target, n, arm_names=ARMS):
    selected = [r for r in rows if r["phase"] == phase]
    arms = {
        a: e.aggregate([r for r in selected if r["arm"] == a], target)
        for a in arm_names
    }
    paired = {a: 0 for a in arm_names}
    off = {r["task_id"]: r for r in selected if r["arm"] == "OFF"}
    for r in selected:
        if r["task_id"] in off:
            paired[r["arm"]] += int(
                r["score"]["broken"] and not off[r["task_id"]]["score"]["broken"]
            )
    complete = all(a["n"] == n for a in arms.values())
    reading = "INCOMPLETE"
    if complete:
        c, s = arms["correct"]["target"], arms["shuffled"]["target"]
        reading = (
            "GENERALIZES"
            if n == 32 and c >= 20 and paired["correct"] <= 2 and s <= 4
            else "MARGINAL"
            if c >= 12
            else "NOT"
        )
    return dict(
        arms=arms,
        correct_only_breakage=paired,
        reading=reading,
        n=n,
        diagnostic=n == 16,
    )


def profile(engine, records, sides, name, fence=False, target_norm=None):
    import torch

    means, items = [], []
    for side in sides:
        total, count = None, 0
        for r in records:
            if r["arm"] != side:
                continue
            if time.monotonic() >= engine.deadline - 45:
                raise base.BudgetStop("profile cleanup reserve")
            gen = [t for t in r["generated_token_ids"] if t not in engine.eos]
            assert len(gen) >= 3
            ids = r["input_token_ids"] + gen
            start = len(r["input_token_ids"])
            stop = start + 3 if fence else len(ids)
            hook = engine.hooks
            hook.reset_capture()
            hook.capture_slice, hook.capture, hook.bias = slice(start, stop), True, None
            with torch.inference_mode():
                engine.model(
                    input_ids=torch.tensor([ids], device=engine.device),
                    use_cache=False,
                    logits_to_keep=1,
                )
            torch.cuda.synchronize()
            hook.capture, hook.capture_slice = False, None
            assert all(c == stop - start for c in hook.counts)
            sums = hook.sums.cpu().clone()
            items.append(
                dict(
                    record_id=r["id"],
                    skill=side,
                    positions=[start, stop],
                    generated_token_ids=gen[:3] if fence else gen,
                    count=stop - start,
                    logit_sums=sums,
                )
            )
            total = sums if total is None else total + sums
            count += stop - start
        assert count > 0
        means.append(total / count)
    means = torch.stack(means).float()
    normal, shuffled = base.make_biases(means, seed=SEED + 2)
    bias, shuffle = 3 * normal[1], 3 * shuffled[1]
    scale = 1.0 if target_norm is None else target_norm / float(bias.norm())
    bias, shuffle = bias * scale, shuffle * scale
    biases = dict(correct=bias, swapped=-bias, shuffled=shuffle)
    torch.save(
        dict(means=means, normal=normal, per_task=items, biases=biases, scale=scale),
        OUT / f"{name}-profiles.pt",
    )
    layers = []
    for layer in range(48):
        top = [torch.topk(p[layer], 8).indices.tolist() for p in means]
        layers.append(
            dict(
                layer=layer,
                top_experts=dict(zip(sides, top, strict=True)),
                overlap=len(set(top[0]) & set(top[1])) / 8,
            )
        )
    write(
        f"{name}-profile-freeze.json",
        dict(
            sha256=base.sha(OUT / f"{name}-profiles.pt"),
            norm=float(bias.norm()),
            scale=scale,
            alpha=3,
            fence_first_three=fence,
            layers=layers,
            screen_records_at_freeze=0,
        ),
    )
    return biases


def cpu_checks(bank):
    checks = 0
    for pair in ("TS", "P2", "Go"):
        for split in ("competence", "screen"):
            for t in bank[pair][split]:
                if pair == "P2":
                    codes = {
                        "JSON": json.dumps(t["expected"]),
                        "SQL": f"SELECT * FROM items WHERE value {t['op']} {t['threshold']};",
                    }
                else:
                    codes = {
                        "Python": f"def {t['name']}():\n    return {t['expression']}"
                    }
                    codes["Go" if pair == "Go" else "TypeScript"] = (
                        f"func {t['name']}() int {{ return {t['expression']} }}"
                        if pair == "Go"
                        else f"function {t['name']}(): number {{ return {t['expression']}; }}"
                    )
                for lang, code in codes.items():
                    assert score(code, t)["valid_skill"] == lang, (code, score(code, t))
                    assert score(code, t, True)["broken"]
                    checks += 1
    t = bank["Go"]["competence"][0]
    for bad in [
        f"func {t['name']}() int {{ return 0 }}",
        f"func {t['name']}() int {{ return evil() }}",
        f"func wrong() int {{ return {t['expression']} }}",
    ]:
        assert score(bad, t)["broken"]
    with tempfile.TemporaryDirectory(prefix="check40g-vet-") as tmp:
        p = Path(tmp) / "fixture.go"
        p.write_text(
            "package fixture\n"
            + "\n".join(
                f"func {t['name']}() int {{ return {t['expression']} }}"
                for t in bank["Go"]["competence"]
            )
        )
        fmt = subprocess.run([str(GOFMT), "-w", str(p)], capture_output=True, text=True)
        vet = subprocess.run(
            [str(GO), "vet", str(p)],
            capture_output=True,
            text=True,
            env=dict(os.environ, GOTOOLCHAIN="local"),
        )
        assert fmt.returncode == vet.returncode == 0, (fmt.stderr, vet.stderr)
    # Exact40i decision code; only input labels are mapped for Go.
    arms = {
        a: {s: dict(valid={i.TARGET[s]: 24}, broken=0) for s in i.STEPS} for a in i.ARMS
    }
    for a in ("Zc", "S"):
        arms[a]["BACK"]["valid"] = {"Python": 24}
    assert i.decision(arms, 24, True, 24, 24)[0] == "CLOSED-RELEASE"
    arms["Z"]["BACK"]["valid"] = {"JavaScript": 19}
    assert i.decision(arms, 24, True, 24, 24)[0] == "PARTIAL"
    return dict(
        canonical_cases=checks,
        negative_checks=True,
        go_version=subprocess.check_output([str(GO), "version"], text=True).strip(),
        gofmt_exit=fmt.returncode,
        go_vet_exit=vet.returncode,
        go_provenance=json.loads((GO.parents[2] / "provenance.json").read_text()),
        dispatch_consumer=cpu_router_test(),
        release_decision_boundaries=True,
    )


def prepare():
    OUT.mkdir(exist_ok=True)
    assert not (OUT / "records.jsonl").exists()
    b = banks()
    write("banks.json", b)
    (OUT / "prewritten-reading.md").write_text(READING)
    write("cpu.json", cpu_checks(b))
    files = [
        Path(__file__),
        ROOT / "scripts/focus_check40.py",
        ROOT / "scripts/focus_check40c.py",
        ROOT / "scripts/focus_check40e.py",
        ROOT / "scripts/focus_check40f.py",
        ROOT / "scripts/focus_check40h.py",
        ROOT / "scripts/focus_check40i.py",
        ROOT / "scripts/focus_check43.py",
        OUT / "banks.json",
        OUT / "prewritten-reading.md",
        e.OUT / "records.jsonl",
        e.OUT / "P1-profiles.pt",
        ROOT / "results/quick-checks/check40c/selected-bias.pt",
    ]
    write("freeze.json", {str(p.relative_to(ROOT)): base.sha(p) for p in files})
    print("CPU PASS; recipe frozen", flush=True)


def release_summary(rows, complete):
    selected = [r for r in rows if r["phase"] == "release"]
    arms = {
        arm: {
            step: e.aggregate(
                [r for r in selected if r["arm"] == arm and r["step"] == step], "Go"
            )
            for step in i.STEPS
        }
        for arm in i.ARMS
    }
    paired, switched, chains = {}, {}, {}
    for arm in i.ARMS:
        bank = {(r["episode"], r["step"]): r for r in selected if r["arm"] == arm}

        def count(sequence, bank=bank):
            return sum(
                all(
                    (ep, step) in bank
                    and bank[ep, step]["score"]["valid_skill"] == skill
                    for step, skill in sequence
                )
                for ep in range(24)
            )

        paired[arm] = count(
            [("BACK", "Go"), ("HOLD_AFTER_BACK", "Go"), ("CLEAR", "Python")]
        )
        switched[arm] = count([("SET", "Go"), ("HOLD", "Go"), ("SWITCH", "Python")])
        chains[arm] = count(
            [
                (step, "Go" if i.TARGET[step] == "JavaScript" else "Python")
                for step in i.STEPS
            ]
        )
    mapped = copy.deepcopy(arms)
    for steps in mapped.values():
        for cell in steps.values():
            cell["valid"]["JavaScript"] = cell["valid"].pop("Go", 0)
    verdict, passes = i.decision(mapped, 24, complete, paired["Z"], switched["Z"])
    return dict(
        reading=verdict,
        passes=passes,
        complete=complete,
        episodes=24,
        arms=arms,
        paired_clear_release=paired,
        paired_switch_release=switched,
        full_chains=chains,
        records=len(selected),
        decision_function="unchanged focus_check40i.decision; Go counts mapped to its JavaScript label",
    )


def run():
    import torch

    freeze = json.loads((OUT / "freeze.json").read_text())
    for path, digest in freeze.items():
        assert base.sha(ROOT / path) == digest, path
    assert not (OUT / "records.jsonl").exists(), "No retry/overwrite"
    lock = (ROOT / ".review.lock").open("a")
    while True:
        status = e.ready()
        print(json.dumps(status), flush=True)
        if status["ready"]:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                pass
            else:
                if e.ready()["ready"]:
                    break
                fcntl.flock(lock, fcntl.LOCK_UN)
        time.sleep(45)
    flag = OUT / "RUNNING.flag"
    with flag.open("x") as f:
        f.write(json.dumps(dict(pid=os.getpid(), check="40g")) + "\n")
    write("resources.json", status)
    start = time.monotonic()
    base.GPU_SECONDS, base.SEED = LIMIT - 15, SEED
    engine, audit, session, shared = None, None, None, None
    rows = []
    summary = dict(reading="INCOMPLETE", pairs={}, cap_seconds=LIMIT)
    journal = (OUT / "records.jsonl").open("x")
    bank = json.loads((OUT / "banks.json").read_text())

    def append(r):
        r["id"] = len(rows)
        journal.write(json.dumps(r) + "\n")
        journal.flush()
        rows.append(r)
        print(
            json.dumps(
                dict(
                    n=len(rows),
                    phase=r["phase"],
                    arm=r["arm"],
                    step=r.get("step"),
                    skill=r["score"]["valid_skill"],
                    broken=r["score"]["broken"],
                    elapsed=time.monotonic() - start,
                )
            ),
            flush=True,
        )

    def request(
        task,
        phase,
        arm,
        cue=None,
        bias=None,
        alpha=None,
        history=None,
        session=None,
        episode=None,
        step=None,
    ):
        messages = (
            e.messages(task, cue)
            if task["pair"] == "P2"
            else base.messages_for(task, cue, history)
        )
        event = (
            i.mask_change(engine, session, arm, step, bias)
            if phase == "release"
            else None
        )
        audit.reset()
        if phase == "release":
            r = i.generation(engine, messages, bias, session)
        else:
            r, _ = engine.generate(messages, bias=bias, cap=64)
        dispatch = audit.finish()
        for v in dispatch.values():
            v["route_change_fraction"] = v["changed_route_tokens"] / v["tokens"]
        r.update(
            phase=phase,
            arm=arm,
            task_id=task["id"],
            pair=task["pair"],
            cue=cue,
            alpha=alpha,
            score=score(r["text"], task, r["truncated"]),
            dispatch=dispatch,
        )
        if phase == "release":
            r.update(
                episode=episode,
                step=step,
                mask_event=event,
                expression_echo=i.expression_echo(r["text"], task),
                generation=sum("shared_from_generation" not in r for r in rows),
            )
            r.update(e.dose.report_fields(r, engine.tokenizer))
            begin = len(r["cache_prefix_token_ids"]) + len(r["input_token_ids"])
            end = begin + len(r["generated_token_ids"]) - int(r["eos"])
            assert begin < end
            session["bodies"].append([begin, end])
            r["cue_turn_span"] = None
        append(r)
        if r["cost_stopped"]:
            raise base.BudgetStop("cooperative token deadline")
        return (
            messages + [dict(role="assistant", content=r["text"])]
            if phase == "release"
            else r
        )

    def screen(pair, tasks, biases, phase, alpha=3):
        for arm in ARMS:
            for t in tasks:
                request(
                    t,
                    phase,
                    arm,
                    cue=pair if arm == "text-cue" else None,
                    bias=biases.get(arm),
                    alpha=alpha if arm in biases else 0,
                )
        return screen_summary(rows, phase, pair, len(tasks))

    try:
        engine = base.Engine(start)
        write(
            "runtime.json",
            dict(
                e.dose.runtime(),
                load_seconds=engine.load_seconds,
                model=str(base.MODEL),
                seed=SEED,
            ),
        )
        kernel = engine.verify_kernel()
        write("kernel.json", kernel)
        assert kernel["adopted"]
        audit = DispatchAudit(engine)
        js = torch.load(
            ROOT / "results/quick-checks/check40c/selected-bias.pt",
            map_location="cpu",
            weights_only=True,
        )
        if isinstance(js, dict):
            raise ValueError(f"Unexpected selected-bias keys: {list(js)}")
        js = 1.5 * js
        torch.save(js, OUT / "js-control-bias.pt")
        controls = [
            request(
                dict(t, js_control=True),
                "positive-control",
                "correct",
                bias=js,
                alpha=3,
            )
            for t in bank["TS"]["screen"][:8]
        ]
        valid = sum(r["score"]["valid_skill"] == "JavaScript" for r in controls)
        summary["positive_control"] = dict(
            javascript=valid, n=8, passed=valid >= 6, norm=float(js.norm())
        )
        write("summary.json", summary)
        if valid < 6:
            summary["reading"] = "INVALID"
            summary["reason"] = (
                "Same40e-harness frozen JS positive control failed; no further inference"
            )
            return
        write(
            "measured-projection.json",
            dict(
                elapsed=time.monotonic() - start,
                control_mean_seconds=sum(r["seconds"] for r in controls) / 8,
                estimated_remaining_generations=992,
                projected_seconds=time.monotonic()
                - start
                + 1.25 * (992 * sum(r["seconds"] for r in controls) / 8 + 150),
                peak_allocated_gib=torch.cuda.max_memory_allocated() / 2**30,
                policy="fixed counts; cooperative deadline; incomplete if exhausted",
            ),
        )
        # Fence profile reuses exact committed replies; no fresh TS outcomes influence extraction.
        prior = [
            json.loads(line)
            for line in (e.OUT / "records.jsonl").read_text().splitlines()
        ]
        prior = [r for r in prior if r["pair"] == "P1" and r["phase"] == "competence"]
        assert len(prior) == 32
        fence = profile(engine, prior, ("Python", "TypeScript"), "TS-fence", True, 15.7)
        old = torch.load(
            e.OUT / "P1-profiles.pt", map_location="cpu", weights_only=True
        )["biases"]
        configs = {
            "TS-alpha4.5": {a: b * 1.5 for a, b in old.items()},
            "TS-alpha6": {a: b * 2 for a, b in old.items()},
            "TS-fence": fence,
        }
        ts_tasks = bank["TS"]["screen"][:16]
        shared_ts = []
        for arm in ("OFF", "text-cue"):
            for t in ts_tasks:
                shared_ts.append(
                    request(
                        t,
                        "TS-shared",
                        arm,
                        cue="TypeScript" if arm == "text-cue" else None,
                    )
                )
        for phase, biases in configs.items():
            for source in shared_ts:
                r = copy.deepcopy(source)
                r.update(phase=phase, shared_from_generation=source["id"])
                append(r)
            alpha = {"TS-alpha4.5": 4.5, "TS-alpha6": 6, "TS-fence": 3}[phase]
            for arm in ("correct", "shuffled"):
                for t in ts_tasks:
                    request(t, phase, arm, bias=biases[arm], alpha=alpha)
            summary["pairs"][phase] = screen_summary(
                rows,
                phase,
                "TypeScript",
                16,
                ("OFF", "correct", "shuffled", "text-cue"),
            )
            write("summary.json", summary)
        for pair, sides in [("P2", ("JSON", "SQL")), ("Go", ("Python", "Go"))]:
            comp = [
                request(t, pair + "-competence", side, cue=side)
                for side in sides
                for t in bank[pair]["competence"]
            ]
            counts = {
                side: sum(
                    r["arm"] == side and r["score"]["valid_skill"] == side for r in comp
                )
                for side in sides
            }
            eligible = (
                counts[sides[0]] >= (16 if pair == "Go" else 14)
                and counts[sides[1]] >= 14
            )
            summary["pairs"][pair] = dict(
                competence=counts,
                reading="INELIGIBLE" if not eligible else "INCOMPLETE",
            )
            write("summary.json", summary)
            if not eligible:
                continue
            biases = profile(
                engine,
                comp,
                sides,
                pair,
                target_norm=float(js.norm()) if pair == "Go" else None,
            )
            result = screen(sides[1], bank[pair]["screen"], biases, pair + "-screen")
            summary["pairs"][pair].update(result)
            write("summary.json", summary)
            if (
                pair != "Go"
                or result["arms"]["correct"]["target"] < 20
                or result["arms"]["correct"]["broken"] > 2
            ):
                continue
            release_biases = dict(js=biases["correct"], shuffled=biases["shuffled"])
            for ep, tasks in enumerate(bank["release"]):
                shared, history = i.session_new(), None
                offset = len(rows)
                for step in i.PREFIX:
                    bias = i.bias_for("Z", step, release_biases)
                    history = request(
                        tasks[step],
                        "release",
                        "Z",
                        bias=bias,
                        alpha=3 if bias is not None else 0,
                        history=history,
                        session=shared,
                        episode=ep,
                        step=step,
                    )
                prefix = rows[offset:]
                for arm in i.ARMS[:3]:
                    session, branch = i.fork_session(shared), copy.deepcopy(history)
                    if arm != "Z":
                        for source in prefix:
                            r = copy.deepcopy(source)
                            r.update(
                                arm=arm, shared_from_generation=source["generation"]
                            )
                            append(r)
                    for step in i.STEPS[4:]:
                        bias = i.bias_for(arm, step, release_biases)
                        branch = request(
                            tasks[step],
                            "release",
                            arm,
                            bias=bias,
                            alpha=3 if bias is not None else 0,
                            history=branch,
                            session=session,
                            episode=ep,
                            step=step,
                        )
                    session = None
                shared = None
                session, history = i.session_new(), None
                for step in i.STEPS:
                    history = request(
                        tasks[step],
                        "release",
                        "OFF",
                        alpha=0,
                        history=history,
                        session=session,
                        episode=ep,
                        step=step,
                    )
                session = None
                write("release-summary.json", release_summary(rows, False))
            summary["release"] = release_summary(rows, True)
            write("release-summary.json", summary["release"])
        summary["reading"] = "COMPLETE"
    except base.BudgetStop as exc:
        summary["reason"] = str(exc)
    except Exception as exc:
        summary["reason"] = repr(exc)
        raise
    finally:
        journal.close()
        session, shared = None, None
        if audit is not None:
            audit.close()
            audit = None
        if engine is not None:
            summary["peak_allocated_gib"] = torch.cuda.max_memory_allocated() / 2**30
            engine.hooks.close()
            engine = None
        gc.collect()
        if torch.cuda.is_initialized():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        actual = [r for r in rows if "shared_from_generation" not in r]
        summary.update(
            records=len(rows),
            generations=len(actual),
            generated_tokens=sum(len(r["generated_token_ids"]) for r in actual),
            gpu_seconds=time.monotonic() - start,
        )
        summary["cap_overrun_seconds"] = max(0, summary["gpu_seconds"] - LIMIT)
        write("summary.json", summary)
        flag.unlink()
        lock.close()
        print(
            json.dumps({k: summary[k] for k in ("reading", "gpu_seconds", "records")}),
            flush=True,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "run"])
    args = parser.parse_args()
    prepare() if args.mode == "prepare" else run()
