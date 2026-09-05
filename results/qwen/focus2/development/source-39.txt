#!/usr/bin/env python3
"""Check 39: fresh paired eviction-repair rerun with prospective safety gates."""

# ruff: noqa: E402, E501, I001
from __future__ import annotations

import argparse
import copy
import fcntl
import json
import math
import os
import random
import subprocess
import time
from pathlib import Path

from focus_check37 import Engine, Budget, ROOT, BASE, CUE, CANCEL, MODES, STEPS
from focus_check37 import StopRun, gpu_pids, sha, write_json

OUT = ROOT / "results/quick-checks/check39"
SEED, N = 39039, 64
ARMS = ("intact", "placeholder")


def assert_review_idle():
    # An existing lock file is harmless; an actual held advisory lock blocks.
    with (ROOT / ".review.lock").open("a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(handle, fcntl.LOCK_UN)


def bank():
    prior = json.loads(
        (ROOT / "results/quick-checks/check37/4b/episodes.json").read_text()
    )
    old = {tuple(sorted(v)) for ep in prior for v in ep}
    rng, seen, rows = random.Random(SEED), set(), []
    while len(rows) < N * 6:
        v = rng.sample(range(-20, 21), rng.randint(5, 8))
        key = tuple(sorted(v))
        if key in seen or v in (sorted(v), sorted(v, reverse=True)):
            continue
        seen.add(key)
        rows.append(v)
    # Verify freshness without changing the draw stream or screening outcomes.
    assert not seen & old, "Bank overlaps check37; abort before GPU load"
    return [rows[i : i + 6] for i in range(0, len(rows), 6)]


def mcnemar_worse(b, c):
    """Exact upper tail: b=placeholder-only broken, c=intact-only broken."""
    assert b >= 0 and c >= 0
    n = b + c
    return sum(math.comb(n, k) for k in range(b, n + 1)) / 2**n


def aggregate(rows):
    arms, indexed = {}, {}
    for arm in ARMS:
        for mode in MODES:
            rs = [r for r in rows if r["arm"] == arm and r["mode"] == mode]
            ix = {(r["episode"], r["step"]): r for r in rs}
            assert len(ix) == len(rs), "Duplicate paired record"
            assert all(0 <= e < N and s in STEPS for e, s in ix)
            indexed[arm, mode] = ix
            steps = {}
            for step in STEPS:
                chosen = [r for r in rs if r["step"] == step]
                steps[step] = dict(
                    n=len(chosen),
                    valid=sum(r["strict_valid"] for r in chosen),
                    success=sum(r["success"] for r in chosen),
                    value_exact=sum(
                        r["score"]["value_exact"][r["target"]] for r in chosen
                    ),
                    broken=sum(r["broken"] for r in chosen),
                    placeholder_imitation=sum(r["text"].strip() == "." for r in chosen),
                    empty=sum(not r["text"].strip() for r in chosen),
                )
            arms[f"{arm}/{mode}"] = dict(
                steps=steps,
                broken_episodes=sorted({r["episode"] for r in rs if r["broken"]}),
            )
    complete = all(s["n"] == N for a in arms.values() for s in a["steps"].values())
    gates = {}
    for mode in MODES:
        p, baseline = (arms[f"{a}/{mode}"] for a in ("placeholder", "intact"))
        pb, ib = set(p["broken_episodes"]), set(baseline["broken_episodes"])
        b, c = len(pb - ib), len(ib - pb)
        losses = {
            s: baseline["steps"][s]["success"] - p["steps"][s]["success"]
            for s in STEPS[:2]
        }
        copies = {
            a: {s: arms[f"{a}/{mode}"]["steps"][s]["success"] for s in STEPS[2:]}
            for a in ARMS
        }
        pvalue = mcnemar_worse(b, c)
        safety = b - c <= 2 and pvalue >= 0.05
        active = mode == "rebuilt" or max(losses.values()) <= 2
        neutral = all(v >= 56 for arm in copies.values() for v in arm.values())
        gates[mode] = dict(
            placeholder_only_broken=sorted(pb - ib),
            intact_only_broken=sorted(ib - pb),
            both_broken=sorted(pb & ib),
            neither_broken=N - len(pb | ib),
            discordant_net=b - c,
            mcnemar_worse_one_sided_p=pvalue,
            safety_pass=safety,
            active_success_losses=losses,
            active_gate_applies=mode == "surviving",
            active_pass=active,
            neutral_copies=copies,
            neutral_pass=neutral,
            passes=complete and safety and active and neutral,
        )
    comparisons = {}
    for arm in ARMS:
        comparisons[arm] = {}
        for step in STEPS:
            pairs = [
                (indexed[arm, "surviving"][e, step], indexed[arm, "rebuilt"][e, step])
                for e in range(N)
                if (e, step) in indexed[arm, "surviving"]
                and (e, step) in indexed[arm, "rebuilt"]
            ]
            comparisons[arm][step] = dict(
                n=len(pairs),
                identical_outputs=sum(
                    (x["generated_token_ids"], x["eos_token_id"])
                    == (y["generated_token_ids"], y["eos_token_id"])
                    for x, y in pairs
                ),
                surviving_only_success=sum(
                    x["success"] and not y["success"] for x, y in pairs
                ),
                rebuilt_only_success=sum(
                    y["success"] and not x["success"] for x, y in pairs
                ),
            )
    proceed = complete and all(g["passes"] for g in gates.values())
    return dict(
        arms=arms,
        complete=complete,
        gates=gates,
        comparisons=comparisons,
        verdict="PROCEED_PLACEHOLDER"
        if proceed
        else "STOP"
        if complete
        else "INCOMPLETE",
        preselected_larger_test_variant="placeholder" if proceed else None,
    )


def run():
    episodes = bank()
    active = gpu_pids()
    utilization = subprocess.check_output(
        ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
        text=True,
    ).strip()
    if active or any(int(v) for v in utilization.splitlines()):
        raise RuntimeError(
            f"GPU busy: {sorted(active)}, utilization={utilization}; abort without signals"
        )
    assert_review_idle()
    out = OUT / "4b"
    assert not (out / "summary.json").exists(), "Refusing overwrite"
    import torch
    from tokenizers import Tokenizer
    from stencil.qwen3 import Qwen3, Qwen3Config

    tok = Tokenizer.from_file(str(ROOT / "models/qwen3-4b-hf/tokenizer.json"))
    placeholder = tok.encode(".").ids
    assert len(placeholder) == 1 and tok.decode(placeholder) == "."
    out.mkdir(parents=True, exist_ok=True)
    (out / "prewritten-reading.md").write_bytes((OUT / "README.md").read_bytes())
    budget, rows = Budget(), []
    data = dict(
        status="running",
        seed=SEED,
        n=N,
        trunk="Qwen3-4B",
        gpu_cap_minutes=30,
        pid=os.getpid(),
        initial_gpu_compute_apps=[],
        initial_gpu_utilization=utilization,
        started_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        lineage="fit-on=none; evaluated-on=384 fresh seed-39039 synthetic lists; no benchmark contents",
        placeholder_token_ids=placeholder,
        placeholder_cpu_verified=True,
        source_commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        source_hashes={
            str(p.relative_to(ROOT)): sha(p)
            for p in (
                Path(__file__),
                ROOT / "scripts/focus_check37.py",
                ROOT / "results/quick-checks/check37/4b/episodes.json",
                ROOT / "scripts/focus_check35.py",
                ROOT / "scripts/focus_check34.py",
                ROOT / "scripts/focus_check32_kv.py",
                out / "prewritten-reading.md",
            )
        },
    )

    def save():
        data.update(
            aggregate(rows),
            records_count=len(rows),
            elapsed_seconds=time.monotonic() - budget.started,
        )
        write_json(out / "summary.json", data)

    def emit(r):
        assert all(
            k in r
            for k in (
                "history_before",
                "positions_before",
                "text",
                "score",
                "turn",
                "success",
                "broken",
            )
        )
        rows.append(r)
        with (out / "records.jsonl").open("a") as f:
            f.write(json.dumps(r, allow_nan=False) + "\n")

    save()
    try:
        cfg = Qwen3Config.from_hf(ROOT / "models/qwen3-4b-hf/config.json")
        with torch.device("meta"):
            model = Qwen3(cfg)
        weights = torch.load(
            ROOT / "models/qwen3-4b.pt",
            mmap=True,
            map_location="cpu",
            weights_only=True,
        )
        model.load_state_dict(weights, strict=True, assign=True)
        del weights
        for module in model.modules():
            if hasattr(module, "hf_compatible"):
                module.hf_compatible = True
        model = (
            model.to(device="cuda", dtype=torch.bfloat16).eval().requires_grad_(False)
        )
        torch.manual_seed(SEED)
        eng = Engine(model, tok, cfg, torch, budget)
        eng.out, eng.op_id = out, 0
        write_json(out / "episodes.json", episodes)
        write_json(
            out / "layout.json",
            dict(
                cue=CUE,
                cancel=CANCEL,
                base=BASE,
                placeholder_token_ids=placeholder,
                thinking_disabled=True,
                max_new_tokens=64,
                precision="bf16",
                hf_compatible=True,
            ),
        )
        with torch.inference_mode():
            for ep in range(N):
                started = time.monotonic()
                base = eng.session()
                base.update(
                    episode=ep,
                    arm="shared",
                    mode="shared",
                    variant="shared",
                    step="SET",
                    operations=[],
                    turns=[],
                )
                eng.prefill(base, eng.enc(BASE + "<|im_end|>\n"))
                eng.event(base, CUE)
                for i, step in enumerate(("SET", "HOLD")):
                    base["step"] = step
                    eng.answer([base], episodes[ep][i], emit)
                sessions = []
                for arm in ARMS:
                    s = eng.fork(base)
                    s.update(arm=arm, mode="surviving")
                    sessions.append(s)
                del base
                for i, step in enumerate(STEPS):
                    pairs = []
                    for s in sessions:
                        s.update(step=step, operations=[])
                        if step != "NEUTRAL2":
                            eng.repair(s)
                        if step == "NEUTRAL1":
                            eng.event(s, CANCEL)
                        rebuilt = eng.rebuild(s)
                        assert rebuilt["cache"].length == s["cache"].length
                        pairs.extend((s, rebuilt))
                    eng.answer(pairs, episodes[ep][i + 2], emit)
                    del pairs, rebuilt
                data["peak_cuda_allocated_bytes"] = torch.cuda.max_memory_allocated()
                if ep == 0:
                    duration = time.monotonic() - started
                    data["pilot"] = dict(
                        seconds_per_episode=duration,
                        projected_total_minutes=(
                            time.monotonic() - budget.started + duration * (N - 1)
                        )
                        / 60,
                    )
                save()
                print(
                    json.dumps(
                        dict(
                            episode=ep + 1,
                            records=len(rows),
                            minutes=data["elapsed_seconds"] / 60,
                            pilot=data["pilot"],
                        )
                    ),
                    flush=True,
                )
                if ep == 0 and data["pilot"]["projected_total_minutes"] >= 29.5:
                    raise StopRun("Pilot projects beyond cap; no further episodes")
                del sessions, s
            data["status"] = "complete"
    except StopRun as exc:
        data.update(status="partial", stop_reason=str(exc))
    except Exception as exc:
        data.update(status="error", error=repr(exc))
        raise
    finally:
        save()
    print(
        json.dumps(
            dict(
                status=data["status"],
                verdict=data["verdict"],
                minutes=data["elapsed_seconds"] / 60,
            )
        ),
        flush=True,
    )


def self_test():
    from focus_check37 import self_test as previous_test

    previous_test()
    assert len(bank()) == N
    assert len({tuple(sorted(v)) for ep in bank() for v in ep}) == N * 6
    assert mcnemar_worse(0, 0) == 1
    assert mcnemar_worse(1, 1) == 0.75
    assert mcnemar_worse(4, 0) == 0.0625
    assert mcnemar_worse(5, 0) == 0.03125
    fixtures = [
        dict(
            episode=e,
            arm=a,
            mode=m,
            step=s,
            text="[1]",
            strict_valid=True,
            success=True,
            broken=False,
            target="A" if s.startswith("RELEASE") else "OFF",
            score={"value_exact": {"A": True, "OFF": True}},
            generated_token_ids=[1],
            eos_token_id=2,
        )
        for e in range(N)
        for a in ARMS
        for m in MODES
        for s in STEPS
    ]
    assert aggregate([])["verdict"] == "INCOMPLETE"
    assert aggregate(fixtures)["verdict"] == "PROCEED_PLACEHOLDER"

    def changed(predicate, field):
        rows = copy.deepcopy(fixtures)
        for row in rows:
            if predicate(row):
                row[field] = not row[field]
        return aggregate(rows)

    for count, expected in ((2, "PROCEED_PLACEHOLDER"), (3, "STOP")):
        result = changed(
            lambda r, count=count: (
                r["arm"] == "placeholder"
                and r["episode"] < count
                and r["step"] == "RELEASE1"
            ),
            "broken",
        )
        assert result["verdict"] == expected
        result = changed(
            lambda r, count=count: (
                r["arm"] == "placeholder"
                and r["mode"] == "surviving"
                and r["episode"] < count
                and r["step"] == "RELEASE2"
            ),
            "success",
        )
        assert result["verdict"] == expected
    result = changed(
        lambda r: (
            r["arm"] == "placeholder"
            and r["mode"] == "rebuilt"
            and r["step"] == "RELEASE1"
        ),
        "success",
    )
    assert result["verdict"] == "PROCEED_PLACEHOLDER"
    # User's net rule permits b=3, c=1; raw b<=2 would incorrectly reject.
    result = changed(
        lambda r: (
            r["step"] == "RELEASE1"
            and (
                (r["arm"] == "placeholder" and r["episode"] < 3)
                or (r["arm"] == "intact" and r["episode"] == 3)
            )
        ),
        "broken",
    )
    assert result["verdict"] == "PROCEED_PLACEHOLDER"
    for arm in ARMS:
        for mode in MODES:
            for step in STEPS[2:]:
                for count, expected in ((8, "PROCEED_PLACEHOLDER"), (9, "STOP")):
                    result = changed(
                        lambda r, arm=arm, mode=mode, step=step, count=count: (
                            r["arm"] == arm
                            and r["mode"] == mode
                            and r["step"] == step
                            and r["episode"] < count
                        ),
                        "success",
                    )
                    assert result["verdict"] == expected
    try:
        aggregate(fixtures + fixtures[:1])
    except AssertionError:
        pass
    else:
        raise AssertionError("Duplicate record accepted")
    print(
        "check39 CPU checks passed: inherited engine; fresh bank; exact paired tails; net, active and copy boundaries; completeness"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    if args.run:
        run()
