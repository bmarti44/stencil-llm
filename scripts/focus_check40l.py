#!/usr/bin/env python3
"""Check40l: fixed dev-derived competence router direction, two doses."""

from __future__ import annotations

import argparse
import fcntl
import gc
import json
import os
import subprocess
import time
from pathlib import Path

import focus_check40k as k

base, j, i, e, dose = k.base, k.j, k.i, k.e, k.dose
ROOT = k.ROOT
OUT = ROOT / "results/quick-checks/check40l"
LIMIT, CAP, SEED = 2700, 768, 401207
ARMS = ["text+competence-1of3", "text+competence-2of3", "text+shuffled-2of3"]
READING = """# Check40l — competence direction and dose response

Prewritten before inference. ARM A is cut per fable's check40k review; R2
is unreachable. ARM B only: 24 text-only DEV generations, then 96 generations
on the same 32 check40k evaluation tasks. Second look disclosed; no selection,
fitting, training, tuning or task changes from evaluation outcomes.
Data lineage: fit-on = 8 check40k DEV + 16 fresh authored DEV replies, profile
only; evaluated-on = check40k's 32 disjoint evaluation tasks, second look.
Hidden Node tests never enter prompts. Frozen references validate all DEV tests.

Same unchanged check40k scorer, check40j literal text-only rule line, generation
function, bf16 trunk, greedy/non-thinking, cap768, all48 layers/prefill+decode,
fresh sessions. Reuse committed 40k text-only records iff every frozen harness
file and runtime recipe matches; if bytes differ rerun baseline within cap.
Teacher-force each DEV's actual non-EOS generated tokens at their OWN positions
(prompt length through final generated position, not predecessor positions).
Save raw logits [48,tokens,128] per reply in the same run. Across-expert centre
in float64 at each token; mean tokens within each reply, then mean passing
replies minus mean failing replies (equal reply weight). This interprets the
requested mean over replies literally; 40b instead token-weighted its classes.
Require >=6 passing and >=6 failing replies, else INELIGIBLE B without evaluation.
No DEV revision/resampling. This association is a candidate competence direction,
not a known-correct oracle; difficulty, length and output style may confound it.
Norm-match EACH layer to 1/3 and 2/3 of the frozen 40k alpha3 tensor's layer norm;
thus also matching global norms. No layer selection; zero direction => ineligible.
Shuffle larger-dose expert entries independently per layer, seed401207. One
larger-dose shuffled control is used for both registered competence contrasts.
Freeze tensors and profile before evaluation. Rotate three-arm order by task index.

Prewritten readings, R1 first: any competence arm wins-losses>=5, losses<=2,
exact one-sided sign p<=.05, and shuffled does NOT meet that same improvement
criterion => R1: reopen actuator line as competence actuator, registered follow-up
required, not shipping. No multiplicity adjustment (exploratory two-dose screen).
R2 dose-only unreachable because ARM A cut. R3: both tested competence doses
have losses-wins>=3 (40k's descriptive harm bar), and neither qualifies R1 =>
CLOSED for this tested family: router-logit bias on this trunk does not improve
task competence beyond a rendered rule; magnitude harms. This is restricted to
these tested directions/doses/tasks, not all conceivable biases or a proven
monotonic dose law. Anything else R4 INCONCLUSIVE, record, no enlargement.
INELIGIBLE/INCOMPLETE supersede substantive readings. Breakage reported separately.
Paired exact one- and two-sided sign tests, wins/losses/ties, pass counts with
95% CP CIs; paired difference CI uses check40k's conservative Bonferroni CP bounds.
A non-significant effect is not evidence of equivalence or harmlessness.

One model load, cap2700 seconds including load/profiling/freezing/cleanup;
cooperative deadline, no signals. Coordinate RUNNING.flag and review lock;
Brian's pid2705 exempt. Explicit-path local commits, no push.
"""


def read(name):
    return json.loads((OUT / name).read_text())


def write(name, obj):
    base.write_json(OUT / name, obj)


def baseline():
    return [
        dict(r, source="check40k/records.jsonl")
        for r in map(json.loads, (k.OUT / "records.jsonl").read_text().splitlines())
        if r["phase"] == "eval" and r["arm"] == "text-only"
    ]


def qualifies(p):
    return (
        p["wins"] - p["losses"] >= 5
        and p["losses"] <= 2
        and p["sign_p_one_sided"] <= 0.05
    )


def summarize(rows, complete=False, eligible=True):
    er = [r for r in rows if r["phase"] == "eval"]
    arms = {}
    for a in ["text-only"] + ARMS:
        rs = [r for r in er if r["arm"] == a]
        n = len(rs)
        passed = sum(r["score"]["success"] for r in rs)
        arms[a] = dict(
            n=n,
            success=passed,
            ci95=j.cp(passed, n) if n else None,
            broken=sum(r["score"]["broken"] for r in rs),
            truncated=sum(r["truncated"] for r in rs),
            tokens=sum(len(r["generated_token_ids"]) for r in rs),
        )
    pairs = {a: k.pair(er, a) for a in ARMS}
    verdict = "INCOMPLETE" if not complete else "R4"
    if not eligible:
        verdict = "INELIGIBLE B"
    elif complete:
        if any(qualifies(pairs[a]) for a in ARMS[:2]) and not qualifies(pairs[ARMS[2]]):
            verdict = "R1"
        elif all(pairs[a]["losses"] - pairs[a]["wins"] >= 3 for a in ARMS[:2]):
            verdict = "R3"
    return dict(
        complete=complete,
        eligible=eligible,
        reading=verdict,
        R2_reachable=False,
        arms=arms,
        paired=pairs,
    )


def build_bias(means, passed, target):
    import torch

    assert sum(passed) >= 6 and len(passed) - sum(passed) >= 6
    centered = means.double() - means.double().mean(-1, keepdim=True)
    yes = torch.tensor(passed, dtype=torch.bool)
    direction = centered[yes].mean(0) - centered[~yes].mean(0)
    assert torch.isfinite(direction).all() and (direction.norm(dim=1) > 0).all()
    unit = direction / direction.norm(dim=1, keepdim=True)
    low = (unit * target.double().norm(dim=1, keepdim=True) / 3).float()
    high = (unit * target.double().norm(dim=1, keepdim=True) * 2 / 3).float()
    gen = torch.Generator().manual_seed(SEED)
    perm = torch.stack([torch.randperm(128, generator=gen) for _ in range(48)])
    return direction, {ARMS[0]: low, ARMS[1]: high, ARMS[2]: high.gather(1, perm)}, perm


def cpu_checks():
    import torch

    dev = read("dev-tasks.json")
    tasks = read("tasks.json")
    refs = read("reference-solutions.json")
    assert len(dev) == 24 and len(tasks) == 32
    assert len({t["id"] for t in dev + tasks}) == 56
    assert dev[:8] == [t for t in k.bank() if t["split"] == "dev"]
    assert tasks == [t for t in k.bank() if t["split"] == "eval"]
    for t in dev:
        assert len(t["tests"]) >= 4 and k.score(refs[t["id"]], t)["success"], t["id"]
    assert len(baseline()) == 32
    x = torch.arange(12 * 48 * 128, dtype=torch.float64).reshape(12, 48, 128) % 17
    target = torch.ones(48, 128)
    d, b, p = build_bias(x, [True] * 6 + [False] * 6, target)
    assert torch.allclose(d.mean(-1), torch.zeros(48, dtype=torch.float64), atol=1e-12)
    for a, f in zip(ARMS, [1 / 3, 2 / 3, 2 / 3], strict=True):
        assert torch.allclose(b[a].norm(dim=1), target.norm(dim=1) * f, atol=1e-6)
    assert torch.equal(b[ARMS[1]].gather(1, p), b[ARMS[2]])
    assert qualifies(dict(wins=7, losses=1, sign_p_one_sided=k.sign(7, 1)))
    assert not qualifies(dict(wins=6, losses=1, sign_p_one_sided=k.sign(6, 1)))
    # Exercise the reading consumer on complete paired fixtures.
    for w, losses, sw, sl, expected in [
        (6, 0, 0, 0, "R1"),
        (6, 0, 6, 0, "R4"),
        (0, 3, 0, 0, "R3"),
        (0, 0, 0, 0, "R4"),
    ]:
        rows = []
        for idx in range(32):
            for a in ["text-only"] + ARMS:
                success = (
                    idx < losses
                    if a == "text-only"
                    else (losses <= idx < losses + w)
                    if a in ARMS[:2]
                    else ((idx < losses and idx >= sl) or losses <= idx < losses + sw)
                )
                rows.append(
                    dict(
                        task_id=str(idx),
                        arm=a,
                        phase="eval",
                        score=dict(success=success, broken=False),
                        truncated=False,
                        generated_token_ids=[],
                    )
                )
        assert summarize(rows, True)["reading"] == expected
    return dict(
        dev=24,
        eval=32,
        reference_tests=sum(len(t["tests"]) for t in dev),
        profile_math=True,
        reading_consumer=True,
    )


def prepare():
    assert not (OUT / "records.jsonl").exists()
    checks = cpu_checks()
    old = json.loads((k.OUT / "freeze.json").read_text())
    mismatches = [
        p
        for p, s in old["files"].items()
        if p.startswith("scripts/") and base.sha(ROOT / p) != s
    ]
    assert not mismatches, f"Harness changed; baseline rerun required: {mismatches}"
    (OUT / "prewritten-reading.md").write_text(READING)
    (OUT / "README.md").write_text(READING)
    write("cpu.json", checks)
    paths = [
        Path(__file__),
        OUT / "dev-tasks.json",
        OUT / "tasks.json",
        OUT / "reference-solutions.json",
        OUT / "prewritten-reading.md",
        k.OUT / "records.jsonl",
        k.OUT / "freeze.json",
        k.OUT / "runtime.json",
    ]
    paths += [ROOT / p for p in old["files"] if p.startswith("scripts/")]
    paths += [j.BIAS]
    write(
        "freeze.json",
        dict(
            stage="recipe",
            files={str(p.relative_to(ROOT)): base.sha(p) for p in paths},
            baseline_reused=True,
            baseline_harness_mismatches=mismatches,
            seed=SEED,
        ),
    )
    print("CPU preparation PASS", flush=True)


def verify():
    f = read("freeze.json")
    for p, s in f["files"].items():
        assert base.sha(ROOT / p) == s, p
    return f


def profile(engine, r):
    import torch

    generated = [t for t in r["generated_token_ids"] if t not in engine.eos]
    assert generated
    start = len(r["input_token_ids"])
    ids = r["input_token_ids"] + generated
    logits = [None] * 48

    def capture(layer):
        def hook(g, inputs, output):
            assert logits[layer] is None
            raw = output[0] if isinstance(output, tuple) else output
            logits[layer] = raw[start : len(ids)].detach().cpu().clone()
            assert logits[layer].shape == (len(generated), 128)

        return hook

    engine.hooks.bias = None
    engine.hooks.capture = False
    handles = [
        g.register_forward_hook(capture(layer))
        for layer, g in enumerate(engine.hooks.gates)
    ]
    try:
        with torch.inference_mode():
            engine.model(
                input_ids=torch.tensor([ids], device=engine.device),
                use_cache=False,
                logits_to_keep=1,
            )
        torch.cuda.synchronize()
    finally:
        for handle in handles:
            handle.remove()
    raw = torch.stack(logits)
    assert torch.isfinite(raw).all()
    item = dict(
        task_id=r["task_id"],
        record_id=r["id"],
        generated_token_ids=generated,
        positions=list(range(start, len(ids))),
        raw_logits=raw,
    )
    (OUT / "profiles").mkdir(exist_ok=True)
    torch.save(item, OUT / "profiles" / f"{r['task_id']}.pt")
    x = raw.double()
    return (x - x.mean(-1, keepdim=True)).mean(1)


def run():
    import torch

    f = verify()
    assert not (OUT / "records.jsonl").exists(), "No repeated run"
    recipe = subprocess.check_output(
        [
            "git",
            "log",
            "-1",
            "--format=%H",
            "--",
            str(Path(__file__).relative_to(ROOT)),
        ],
        cwd=ROOT,
        text=True,
    ).strip()
    for p in f["files"]:
        assert (
            subprocess.check_output(["git", "show", f"{recipe}:{p}"], cwd=ROOT)
            == (ROOT / p).read_bytes()
        ), p
    lock = (ROOT / ".review.lock").open("a")
    while True:
        status = e.ready()
        if status["ready"]:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                pass
            else:
                if e.ready()["ready"]:
                    break
                fcntl.flock(lock, fcntl.LOCK_UN)
        print(json.dumps(dict(wait=status)), flush=True)
        time.sleep(45)
    flag = OUT / "RUNNING.flag"
    with flag.open("x") as stream:
        stream.write(json.dumps(dict(pid=os.getpid(), check="40l")) + "\n")
    start = time.monotonic()
    base.GPU_SECONDS = LIMIT - 20
    base.SEED = k.SEED
    engine = None
    rows = []
    means = []
    complete = False
    eligible = True
    reason = "interrupted"
    journal = (OUT / "records.jsonl").open("x")
    write("resources.json", status)
    f["recipe_commit"] = recipe
    write("freeze.json", f)

    def request(t, arm, phase, active=None):
        r = i.generation(
            engine, j.messages(t, "text-only"), active, i.session_new(), cap=CAP
        )
        r.update(
            id=len(rows),
            phase=phase,
            arm=arm,
            task_id=t["id"],
            task_sha256=k.digest(t),
            score=k.score(r["text"], t, r["truncated"]),
        )
        r.update(dose.report_fields(r, engine.tokenizer))
        assert r["bias_sha256"] == i.prior.digest_bias(active)
        assert all(not x["masked"] for x in r["mask_forward_trace"])
        journal.write(json.dumps(r) + "\n")
        journal.flush()
        rows.append(r)
        print(
            json.dumps(
                dict(
                    n=len(rows),
                    phase=phase,
                    task=t["id"],
                    arm=arm,
                    success=r["score"]["success"],
                    tokens=len(r["generated_token_ids"]),
                    elapsed=round(time.monotonic() - start, 2),
                )
            ),
            flush=True,
        )
        if r["cost_stopped"]:
            raise base.BudgetStop("cooperative deadline")
        return r

    try:
        engine = base.Engine(start)
        runtime = dose.runtime()
        prior = json.loads((k.OUT / "runtime.json").read_text())
        assert all(runtime[key] == prior[key] for key in runtime), (
            "Runtime drift; baseline reuse forbidden"
        )
        write("runtime.json", dict(runtime, load_seconds=engine.load_seconds))
        kernel = engine.verify_kernel()
        write("kernel.json", kernel)
        assert kernel["adopted"] and all(
            dose.raw_contract(g) for g in engine.hooks.gates
        )
        for t in read("dev-tasks.json"):
            r = request(t, "text-only", "dev")
            if time.monotonic() - start > LIMIT - 45:
                raise base.BudgetStop("profile deadline")
            means.append(profile(engine, r))
        passed = [r["score"]["success"] for r in rows]
        eligible = sum(passed) >= 6 and 24 - sum(passed) >= 6
        write(
            "dev-summary.json",
            dict(passing=sum(passed), failing=24 - sum(passed), eligible=eligible),
        )
        if not eligible:
            reason = "Need >=6 passing and >=6 failing DEV replies"
            return
        target = torch.load(j.BIAS, map_location="cpu", weights_only=True)
        direction, biases, perm = build_bias(torch.stack(means), passed, target)
        torch.save(
            dict(
                reply_means=torch.stack(means),
                passed=passed,
                direction=direction,
                biases=biases,
                permutations=perm,
            ),
            OUT / "competence-profile.pt",
        )
        write(
            "profile-statistics.json",
            dict(
                pooling="equal reply weighted",
                passing=sum(passed),
                failing=24 - sum(passed),
                target_layer_norms=target.double().norm(dim=1).tolist(),
                norms={a: b.double().norm(dim=1).tolist() for a, b in biases.items()},
                global_norms={a: b.double().norm().item() for a, b in biases.items()},
                target_global_norm=target.double().norm().item(),
            ),
        )
        projection = (
            time.monotonic()
            - start
            + 96 * sum(r["seconds"] for r in rows) / 24 * 1.3
            + 45
        )
        write("projection.json", dict(projected_total_seconds=projection, cap=LIMIT))
        if projection > LIMIT:
            raise base.BudgetStop("DEV projection exceeds cap")
        f.update(
            stage="profile-frozen",
            profile_sha256=base.sha(OUT / "competence-profile.pt"),
            bias_hashes={a: i.prior.digest_bias(b) for a, b in biases.items()},
        )
        write("freeze.json", f)
        paths = [
            str(p.relative_to(ROOT))
            for p in OUT.rglob("*")
            if p.is_file() and p.name not in ["RUNNING.flag", "run.log"]
        ]
        commit = k.git_commit(
            paths,
            "Freeze check40l DEV competence profiles before second-look evaluation",
        )
        write(
            "evaluation-started.json",
            dict(profile_commit=commit, second_look=True, opens=1),
        )
        for idx, t in enumerate(read("tasks.json")):
            for arm in ARMS[idx % 3 :] + ARMS[: idx % 3]:
                request(t, arm, "eval", biases[arm])
            write("summary.json", summarize(rows + baseline()))
        complete = True
        reason = "All 24 DEV and 96 evaluation generations complete"
    except base.BudgetStop as exc:
        reason = str(exc)
    except Exception as exc:
        reason = repr(exc)
        raise
    finally:
        journal.close()
        if engine is not None:
            engine.hooks.close()
            del engine
        gc.collect()
        if torch.cuda.is_initialized():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        result = summarize(rows + baseline(), complete, eligible)
        result.update(
            reason=reason,
            gpu_seconds=time.monotonic() - start,
            cap_seconds=LIMIT,
            generations=len(rows),
            recipe_commit=recipe,
        )
        write("summary.json", result)
        flag.unlink()
        fcntl.flock(lock, fcntl.LOCK_UN)
        print(json.dumps(result), flush=True)


def audit():
    import torch
    from transformers import AutoTokenizer

    f = verify()
    cpu_checks()
    rows = list(map(json.loads, (OUT / "records.jsonl").read_text().splitlines()))
    tasks = {t["id"]: t for t in read("dev-tasks.json") + read("tasks.json")}
    tok = AutoTokenizer.from_pretrained(base.MODEL, local_files_only=True)
    dev = [r for r in rows if r["phase"] == "dev"]
    means = []
    for idx, r in enumerate(rows):
        t = tasks[r["task_id"]]
        assert r["id"] == idx and r["task_sha256"] == k.digest(t)
        assert r["score"] == k.score(r["text"], t, r["truncated"])
        assert r["history"] == j.messages(t, "text-only")
        assert r["text"] == tok.decode(
            r["generated_token_ids"], skip_special_tokens=True
        )
        assert r["input_token_ids"] == tok.apply_chat_template(
            r["history"],
            tokenize=True,
            return_dict=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        assert len(r["generated_token_ids"]) <= CAP and not r["cache_prefix_token_ids"]
        assert all(not x["masked"] for x in r["mask_forward_trace"])
        assert r["bias_sha256"] == (
            None if r["phase"] == "dev" else f["bias_hashes"][r["arm"]]
        )
        if r["phase"] == "dev":
            p = torch.load(OUT / "profiles" / f"{r['task_id']}.pt", weights_only=True)
            x = p["raw_logits"].double()
            n = x.shape[1]
            assert x.shape == (48, n, 128) and n > 0 and torch.isfinite(x).all()
            assert (
                p["record_id"] == idx
                and p["generated_token_ids"] == r["generated_token_ids"][:n]
            )
            assert p["positions"] == list(
                range(len(r["input_token_ids"]), len(r["input_token_ids"]) + n)
            )
            means.append((x - x.mean(-1, keepdim=True)).mean(1))
    if f["stage"] == "profile-frozen":
        assert base.sha(OUT / "competence-profile.pt") == f["profile_sha256"]
        p = torch.load(OUT / "competence-profile.pt", weights_only=True)
        target = torch.load(j.BIAS, map_location="cpu", weights_only=True)
        direction, biases, perm = build_bias(
            torch.stack(means), [r["score"]["success"] for r in dev], target
        )
        assert torch.equal(direction, p["direction"]) and torch.equal(
            perm, p["permutations"]
        )
        for a, b in biases.items():
            assert (
                torch.equal(b, p["biases"][a])
                and i.prior.digest_bias(b) == f["bias_hashes"][a]
            )
        for a, scale in zip(ARMS, [1 / 3, 2 / 3, 2 / 3], strict=True):
            assert torch.allclose(
                biases[a].double().norm(dim=1),
                target.double().norm(dim=1) * scale,
                rtol=1e-6,
            )
    summary = read("summary.json")
    expected = summarize(rows + baseline(), summary["complete"], summary["eligible"])
    assert all(summary[key] == v for key, v in expected.items())
    if summary["complete"]:
        assert len(rows) == 120 and len(dev) == 24
        assert all(a["n"] == 32 for a in summary["arms"].values())
        assert len({(r["task_id"], r["arm"]) for r in rows}) == 120
        assert summary["gpu_seconds"] <= LIMIT
        assert read("evaluation-started.json")["opens"] == 1
    # Independently rescore the reused baseline with the unchanged consumer.
    for r in baseline():
        assert r["score"] == k.score(r["text"], tasks[r["task_id"]], r["truncated"])
    write(
        "paired.json",
        [
            dict(
                task_id=t["id"],
                outcomes={
                    r["arm"]: r["score"]["success"]
                    for r in rows + baseline()
                    if r["phase"] == "eval" and r["task_id"] == t["id"]
                },
            )
            for t in read("tasks.json")
        ],
    )
    write(
        "audit.json",
        dict(
            records=len(rows),
            baseline_records=32,
            scorer=True,
            prompts=True,
            tokens=True,
            profile_recomputed=True,
            bias_norms=True,
            freeze=True,
            summary=True,
        ),
    )
    print("Saved-record audit PASS", flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["prepare", "run", "audit"])
    globals()[p.parse_args().mode]()
