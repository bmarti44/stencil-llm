#!/usr/bin/env python3
"""Fresh authored programming competence: frozen JS router additivity, check40k."""

from __future__ import annotations

import argparse
import fcntl
import gc
import hashlib
import json
import math
import os
import subprocess
import time
from collections import Counter
from pathlib import Path

import focus_check40j as j

base, e, i, dose = j.base, j.e, j.i, j.dose
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/quick-checks/check40k"
SEED, LIMIT, CAP = 401107, 2700, 768
ARMS = ["text-only", "text+bias", "text+shuffled-bias", "OFF"]
READING = """# Check40k — task competence beyond a rendered JavaScript rule

Prewritten 2026-09-06 before GPU work; recipe committed before inference.
Data lineage: fit-on = nothing in this check; calibrate-on = eight authored DEV
programming tasks only; evaluated-on = 32 remaining authored tasks, opened once.
All 40 are freshly invented here; no public benchmark or recorded benchmark
responses used. Inherited actuator lineage: check40b competence profiles, unchanged
check40g alpha-3 JS tensor, same tensor hash as check40j. No new bias fitting/tuning.
Hidden means tests are committed for audit but never supplied to the model.

Qwen3-30B-A3B HF bf16, inherited check40 RouterHooks, all 48 layers,
prefill+decode, greedy, thinking disabled, independent fresh sessions, cap 768.
Exact check40j literal user-line "Live rules: (1) Write all code in JavaScript."
prepended to the current request; check40e system and suffix unchanged. As recorded
in 40j, this literal differs from the repository renderer's Active user rules JSON.
Arms: text-only | text+bias | text+shuffled-bias | OFF. Each evaluation task gets
all four arms, order rotated by task index to balance timing. 128 final generations.
Shuffled control: torch CPU generator seed 401107, independent randperm(128) per
layer, fixed for the whole run. Exactly preserves each layer's multiset and norm.

DEV target: 4..6 of 8 task successes (integer realization of 40..75%). DEV uses
text-only. If outside range, adjust DEV task difficulty only while retaining this
single model load and total resource cap; preserve all earlier DEV versions and
records. No evaluation outcomes may inform any adjustment. Freeze the calibrated
recipe in a local commit before opening the 32 evaluation tasks. If calibration
cannot qualify within budget, stop as INCOMPLETE; do not evaluate at ceiling.
The 32 evaluation tasks are fixed before GPU work and never changed from DEV.
A non-ceiling DEV result does not guarantee non-ceiling held-out performance;
if text-only is at 32/32 report the ceiling limitation without a replacement run.

Primary success = all four hidden Node tests pass. Language, syntax, inherited
40i broken flags (empty/invalid/ambiguous/fences/truncation/repetition), and token
counts are separate outcomes: broken is NOT silently added to the success endpoint.
Node executes extracted code in a fresh vm context per case, 200ms VM timeout;
JSON-normalized values compared by deepStrictEqual. Undefined/non-JSON outputs fail.
Input mutation checked for tasks explicitly requesting nonmutation. Python syntax
is recognized but is not executed: OFF success is JavaScript-task success, not a
language-neutral competence estimate. Semantic errors alone do not count as broken.

PRE-WRITTEN READINGS, fixed:
R1 "ship by default": bias wins-losses >=5/32, losses <=2, exact one-sided sign
p<=.05, shuffled wins-losses <=2, and bias broken <= text-only broken. Register
default-on consequence only for this certified authored JS task family.
R2 "no benefit": wins-losses <=1 -> behind flag, 40j decision stands.
R3 "harm": losses-wins >=3 -> stays off; record harm.
R4 otherwise -> INCONCLUSIVE at n=32, no enlargement.
Ambiguity resolved before outcomes: test R3 BEFORE R2 because literal R2 includes
large harms; retain literal R2 elsewhere (including net loss of two). R1 first,
then R3, then R2, then R4. Incomplete runs never receive a substantive reading.
Exact one-sided p = sum(comb(w+l,k), k=w..w+l)/2**(w+l), or 1 with no discordants.
Examples computed by prepare: 6-0=.015625,7-1=.03515625,9-2=.03271484375 qualify;
6-1=.0625,7-2=.08984375,8-2=.0546875 do not. The supplied 7-1=.031 was approximate
and incorrect; use the exact .03515625, which still qualifies.
Report wins/losses/ties for both paired contrasts, exact one/two-sided p and paired
95% difference CI: Bonferroni union of two 97.5% Clopper-Pearson marginal intervals
for win/loss probabilities, [win.lower-loss.upper,win.upper-loss.lower]. This is
conservative, not an equivalence test; rates also get exact 95% CP intervals.

Resource: one load, 45 GPU-minutes including load, DEV, idle/calibration and cleanup.
Cooperative token deadline with reserve, no signals. DEV measured throughput gives
an evaluation projection before opening; stop if projected total exceeds cap.
Coordinate with all quick-check RUNNING.flag files and review lock; pid2705 exempt.
No prior artifact rewrites, benchmark reads, background launches, signals or push.

Results pending.
"""
NODE = r"""
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const q=JSON.parse(fs.readFileSync(0,'utf8')); const results=[];
for (const t of q.tests) {
  const box=vm.createContext({});
  try {
    new vm.Script(q.code).runInContext(box,{timeout:200});
    box.__args=JSON.parse(JSON.stringify(t.args));
    const before=JSON.stringify(box.__args);
    const value=new vm.Script(q.name+'(...__args)').runInContext(box,{timeout:200});
    assert.deepStrictEqual(JSON.parse(JSON.stringify(value)),t.expected);
    if(q.no_mutation) assert.strictEqual(JSON.stringify(box.__args),before);
    results.push({pass:true});
  } catch(err) { results.push({pass:false,error:String(err).slice(0,240)}); }
}
process.stdout.write(JSON.stringify(results));
"""


def write(name, value):
    base.write_json(OUT / name, value)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def bank():
    return json.loads((OUT / "tasks.json").read_text())


def sign(w, losses):
    return (
        sum(math.comb(w + losses, k) for k in range(w, w + losses + 1))
        / 2 ** (w + losses)
        if w + losses
        else 1.0
    )


def score(text, task, truncated=False):
    syntax = base.score(text, dict(task, witness=r"."), truncated)
    code, _ = base.extract_code(text)
    proc = subprocess.run(
        ["node", "-e", NODE],
        input=json.dumps(
            dict(
                code=code,
                name=task["name"],
                tests=task["tests"],
                no_mutation="mutat" in task["prompt"],
            )
        ),
        text=True,
        capture_output=True,
        check=True,
    )
    tests = json.loads(proc.stdout)
    return dict(
        success=all(t["pass"] for t in tests),
        tests=tests,
        language=syntax["language"],
        syntax_valid=any(syntax["parsers"].values()),
        js_syntax_valid=syntax["parsers"]["JavaScript"],
        broken=syntax["broken"],
        flags=syntax["flags"],
    )


def pair(rows, arm):
    by = {(r["task_id"], r["arm"]): r["score"]["success"] for r in rows}
    w = losses = t = both = 0
    for task_id in sorted({r["task_id"] for r in rows}):
        if (task_id, arm) not in by or (task_id, "text-only") not in by:
            continue
        a, b = by[task_id, arm], by[task_id, "text-only"]
        w += a and not b
        losses += b and not a
        t += a == b
        both += a and b
    n = w + losses + t
    ci = None
    if n:
        wc, lc = j.cp(w, n, 0.025), j.cp(losses, n, 0.025)
        ci = [wc[0] - lc[1], wc[1] - lc[0]]
    return dict(
        wins=w,
        losses=losses,
        ties=t,
        both_success=both,
        both_failure=t - both,
        n=n,
        difference=(w - losses) / n if n else None,
        ci95_conservative=ci,
        sign_p_one_sided=sign(w, losses),
        sign_p_two_sided=min(1, 2 * sign(max(w, losses), min(w, losses))),
    )


def summarize(rows, complete=False):
    rows = [r for r in rows if r["phase"] == "eval"]
    arms = {}
    for a in ARMS:
        rs = [r for r in rows if r["arm"] == a]
        k = sum(r["score"]["success"] for r in rs)
        arms[a] = dict(
            n=len(rs),
            success=k,
            ci95=j.cp(k, len(rs)) if rs else None,
            broken=sum(r["score"]["broken"] for r in rs),
            languages=dict(Counter(r["score"]["language"] for r in rs)),
            syntax_valid=sum(r["score"]["syntax_valid"] for r in rs),
            js_syntax_valid=sum(r["score"]["js_syntax_valid"] for r in rs),
            truncated=sum(r["truncated"] for r in rs),
            tokens=sum(len(r["generated_token_ids"]) for r in rs),
        )
    p, s = pair(rows, "text+bias"), pair(rows, "text+shuffled-bias")
    w, losses = p["wins"], p["losses"]
    r1 = (
        w - losses >= 5
        and losses <= 2
        and p["sign_p_one_sided"] <= 0.05
        and s["wins"] - s["losses"] <= 2
        and arms["text+bias"]["broken"] <= arms["text-only"]["broken"]
    )
    reading = (
        "INCOMPLETE"
        if not complete
        else "R1"
        if r1
        else "R3"
        if losses - w >= 3
        else "R2"
        if w - losses <= 1
        else "R4"
    )
    return dict(
        complete=complete,
        reading=reading,
        arms=arms,
        primary=p,
        shuffled=s,
        ceiling=complete and arms["text-only"]["success"] == 32,
        consequence="default-on for certified authored JS task family"
        if reading == "R1"
        else "actuator stays off; harm"
        if reading == "R3"
        else "actuator remains behind flag",
    )


def cpu_checks():
    tasks = bank()
    assert len(tasks) == 40 and len({t["id"] for t in tasks}) == 40
    assert Counter(t["split"] for t in tasks) == {"dev": 8, "eval": 32}
    assert all(
        4 <= len(t["tests"]) <= 8
        and t["prompt"].startswith("Write a function named " + t["name"] + " that ")
        for t in tasks
    )
    assert all(
        len(c["args"]) > 0 and "expected" in c for t in tasks for c in t["tests"]
    )
    refs = json.loads((OUT / "reference-solutions.json").read_text())
    assert set(refs) == {t["id"] for t in tasks}
    for task in tasks:
        assert score(refs[task["id"]], task)["success"], task["id"]
    examples = {
        (6, 0): 0.015625,
        (7, 1): 0.03515625,
        (9, 2): 0.03271484375,
        (6, 1): 0.0625,
        (7, 2): 0.08984375,
        (8, 2): 0.0546875,
    }
    assert all(sign(*k) == v for k, v in examples.items())
    fixture = dict(
        name="fixture",
        prompt="do not mutate inputs",
        tests=[dict(args=[[1, 2]], expected=[2, 3])],
    )
    assert score("function fixture(xs){return xs.map(x=>x+1)}", fixture)["success"]
    for bad in [
        "function fixture(xs){return [2,4]}",
        "function fixture(xs){xs[0]=2;return [2,3]}",
        "function fixture(xs){while(true){}}",
        "function fixture(xs){return undefined}",
    ]:
        assert not score(bad, fixture)["success"]
    assert score("function fixture(xs){return xs.map(x=>x+1)}", fixture, True)["broken"]
    assert not score("def fixture(xs):\n return [x+1 for x in xs]", fixture)["success"]
    assert (
        score("def fixture(xs):\n return [x+1 for x in xs]", fixture)["language"]
        == "Python"
    )
    assert not score("function fixture(xs){return [2,4]}", fixture)["broken"]
    # Explicit consequence boundaries through the consumer, including overlapping R2/R3.
    for w, losses, sw, expected in [
        (6, 0, 0, "R1"),
        (7, 1, 0, "R1"),
        (9, 2, 0, "R1"),
        (6, 1, 0, "R4"),
        (7, 2, 0, "R4"),
        (8, 2, 0, "R4"),
        (6, 0, 3, "R4"),
        (0, 3, 0, "R3"),
        (0, 0, 0, "R2"),
    ]:
        rs = []
        for k in range(32):
            for a in ARMS:
                success = (
                    (w <= k < w + losses)
                    if a == "text-only"
                    else (k < w)
                    if a == "text+bias"
                    else (w <= k < w + losses or k < sw)
                    if a == "text+shuffled-bias"
                    else False
                )
                rs.append(
                    dict(
                        task_id=str(k),
                        phase="eval",
                        arm=a,
                        score=dict(
                            success=success,
                            broken=False,
                            language="JavaScript",
                            syntax_valid=True,
                            js_syntax_valid=True,
                        ),
                        truncated=False,
                        generated_token_ids=[],
                    )
                )
        assert summarize(rs, True)["reading"] == expected, (w, losses, sw)
    return dict(
        task_count=40,
        tests=160,
        node_consumer=True,
        deadline_vm=True,
        sign_examples={f"{w}-{losses}": p for (w, losses), p in examples.items()},
        reading_boundaries=True,
    )


def prepare():
    import torch

    assert not (OUT / "records.jsonl").exists()
    checks = cpu_checks()
    bias = torch.load(j.BIAS, map_location="cpu", weights_only=True)
    old = json.loads((j.OUT / "freeze.json").read_text())
    assert i.prior.digest_bias(bias) == old["tensor_sha256"]
    gen = torch.Generator().manual_seed(SEED)
    perm = torch.stack([torch.randperm(128, generator=gen) for _ in range(48)])
    shuffled = bias.gather(1, perm)
    assert torch.equal(bias.sort(dim=1).values, shuffled.sort(dim=1).values)
    assert not torch.equal(bias, shuffled)
    torch.save(shuffled, OUT / "shuffled-bias.pt")
    write("permutations.json", perm.tolist())
    (OUT / "README.md").write_text(READING)
    (OUT / "prewritten-reading.md").write_text(READING)
    write("cpu.json", checks)
    paths = [
        Path(__file__),
        OUT / "tasks.json",
        OUT / "reference-solutions.json",
        OUT / "prewritten-reading.md",
        OUT / "shuffled-bias.pt",
        OUT / "permutations.json",
        j.BIAS,
    ]
    paths += sorted((ROOT / "scripts").glob("focus_check40*.py"))
    paths += [ROOT / "scripts/focus_check43.py"]
    write(
        "freeze.json",
        dict(
            recipe_commit=None,
            stage="recipe",
            seed=SEED,
            cap=CAP,
            tensor_sha256=i.prior.digest_bias(bias),
            shuffled_sha256=i.prior.digest_bias(shuffled),
            eval_tasks_sha256=digest([t for t in bank() if t["split"] == "eval"]),
            files={str(p.relative_to(ROOT)): base.sha(p) for p in paths},
        ),
    )
    print("CPU preparation PASS", flush=True)


def verify():
    f = json.loads((OUT / "freeze.json").read_text())
    for path, sha in f["files"].items():
        assert base.sha(ROOT / path) == sha, path
    return f


def git_commit(paths, message):
    subprocess.run(["git", "add", "-f", "--", *paths], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", message, "--", *paths], cwd=ROOT, check=True)
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


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
    for path in f["files"]:
        assert (
            subprocess.check_output(["git", "show", f"{recipe}:{path}"], cwd=ROOT)
            == (ROOT / path).read_bytes()
        ), path
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
        stream.write(json.dumps(dict(pid=os.getpid(), check="40k")) + "\n")
    start = time.monotonic()
    base.GPU_SECONDS = LIMIT - 15
    base.SEED = SEED
    engine = None
    rows = []
    complete = False
    reason = "interrupted"
    dev_round = 0
    journal = (OUT / "records.jsonl").open("x")
    f["recipe_commit"] = recipe
    write("freeze.json", f)
    write("resources.json", status)
    bias = torch.load(j.BIAS, map_location="cpu", weights_only=True)
    shuffled = torch.load(
        OUT / "shuffled-bias.pt", map_location="cpu", weights_only=True
    )

    def request(task, arm, phase):
        active = (
            bias
            if arm == "text+bias"
            else shuffled
            if arm == "text+shuffled-bias"
            else None
        )
        r = i.generation(
            engine, j.messages(task, arm), active, i.session_new(), cap=CAP
        )
        r.update(
            id=len(rows),
            phase=phase,
            arm=arm,
            task_id=task["id"],
            task_sha256=digest(task),
            dev_round=dev_round if phase == "dev" else None,
            score=score(r["text"], task, r["truncated"]),
            token_count=len(r["generated_token_ids"]),
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
                    arm=arm,
                    task=task["id"],
                    success=r["score"]["success"],
                    broken=r["score"]["broken"],
                    tokens=r["token_count"],
                    elapsed=round(time.monotonic() - start, 2),
                )
            ),
            flush=True,
        )
        if r["cost_stopped"]:
            raise base.BudgetStop("cooperative deadline")

    try:
        engine = base.Engine(start)
        write("runtime.json", dict(dose.runtime(), load_seconds=engine.load_seconds))
        kernel = engine.verify_kernel()
        write("kernel.json", kernel)
        assert kernel["adopted"] and len(engine.hooks.gates) == 48
        assert all(dose.raw_contract(g) for g in engine.hooks.gates)
        while True:
            dev = [t for t in bank() if t["split"] == "dev"]
            write(f"dev-tasks-{dev_round}.json", dev)
            for t in dev:
                request(t, "text-only", "dev")
            dr = [
                r for r in rows if r["phase"] == "dev" and r["dev_round"] == dev_round
            ]
            passed = sum(r["score"]["success"] for r in dr)
            # Conservative observed mean plus 30% for longer evaluation answers.
            projection = (
                time.monotonic()
                - start
                + 128 * sum(r["seconds"] for r in dr) / 8 * 1.3
                + 45
            )
            receipt = dict(
                round=dev_round,
                success=passed,
                n=8,
                qualified=4 <= passed <= 6,
                projected_total_seconds=projection,
            )
            write(f"dev-summary-{dev_round}.json", receipt)
            print(json.dumps(dict(calibration=receipt)), flush=True)
            if 4 <= passed <= 6:
                break
            write(
                "calibration-needed.json",
                dict(
                    receipt,
                    instruction=(
                        "DEV-only revision permitted; commit tasks+freeze then "
                        "write calibration-control.json with next_round"
                    ),
                ),
            )
            while not (OUT / "calibration-control.json").exists():
                if time.monotonic() - start > LIMIT - 90:
                    raise base.BudgetStop("DEV calibration unresolved within cap")
                time.sleep(2)
            control = json.loads((OUT / "calibration-control.json").read_text())
            (OUT / "calibration-control.json").unlink()
            if control.get("stop"):
                raise base.BudgetStop("DEV calibration stopped")
            dev_round += 1
            assert control["next_round"] == dev_round
            f = verify()
            assert (
                digest([t for t in bank() if t["split"] == "eval"])
                == f["eval_tasks_sha256"]
            )
        if projection > LIMIT:
            raise base.BudgetStop("DEV measured projection exceeds 45 minutes")
        f.update(stage="evaluation-frozen", calibration=receipt)
        write("freeze.json", f)
        paths = [
            str((OUT / x).relative_to(ROOT))
            for x in [
                "freeze.json",
                f"dev-tasks-{dev_round}.json",
                f"dev-summary-{dev_round}.json",
                "records.jsonl",
            ]
        ]
        evaluation_commit = git_commit(
            paths, "Freeze check40k DEV calibration before one-shot evaluation"
        )
        f["evaluation_freeze_commit"] = evaluation_commit
        write("freeze.json", f)
        assert (
            digest([t for t in bank() if t["split"] == "eval"])
            == f["eval_tasks_sha256"]
        )
        write("evaluation-started.json", dict(commit=evaluation_commit, opens=1))
        for k, t in enumerate(t for t in bank() if t["split"] == "eval"):
            for arm in ARMS[k % 4 :] + ARMS[: k % 4]:
                request(t, arm, "eval")
            write("summary.json", summarize(rows))
        complete = True
        reason = "all 128 evaluation generations complete"
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
        result = summarize(rows, complete)
        result.update(
            reason=reason,
            gpu_seconds=time.monotonic() - start,
            cap_seconds=LIMIT,
            generations=len(rows),
            recipe_commit=recipe,
            dev_rounds=dev_round + 1,
        )
        write("summary.json", result)
        flag.unlink()
        fcntl.flock(lock, fcntl.LOCK_UN)
        print(
            json.dumps({k: result[k] for k in ["reading", "reason", "gpu_seconds"]}),
            flush=True,
        )


def audit():
    import torch
    from transformers import AutoTokenizer

    f = verify()
    cpu_checks()
    tok = AutoTokenizer.from_pretrained(base.MODEL, local_files_only=True)
    rows = [json.loads(x) for x in (OUT / "records.jsonl").read_text().splitlines()]
    tasks = {t["id"]: t for t in bank()}
    for k, r in enumerate(rows):
        task = tasks[r["task_id"]]
        if r["phase"] == "dev":
            task = next(
                t
                for t in json.loads(
                    (OUT / f"dev-tasks-{r['dev_round']}.json").read_text()
                )
                if t["id"] == r["task_id"]
            )
        assert r["id"] == k and r["task_sha256"] == digest(task)
        assert r["score"] == score(r["text"], task, r["truncated"])
        assert r["text"] == tok.decode(
            r["generated_token_ids"], skip_special_tokens=True
        )
        assert r["token_count"] == len(r["generated_token_ids"]) <= CAP
        assert r["history"] == j.messages(task, r["arm"])
        assert r["input_token_ids"] == tok.apply_chat_template(
            r["history"],
            tokenize=True,
            return_dict=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        assert r["cache_prefix_token_ids"] == []
        expected = (
            f["tensor_sha256"]
            if r["arm"] == "text+bias"
            else f["shuffled_sha256"]
            if r["arm"] == "text+shuffled-bias"
            else None
        )
        assert r["bias_sha256"] == expected
        assert all(not x["masked"] for x in r["mask_forward_trace"])
        assert r["mask_forward_trace"][0]["length"] == len(r["input_token_ids"])
        assert len(r["mask_forward_trace"]) == 1 + len(r["generated_token_ids"]) + len(
            r["appended_terminal_token_ids"]
        )
    p = torch.tensor(json.loads((OUT / "permutations.json").read_text()))
    b = torch.load(j.BIAS, map_location="cpu", weights_only=True)
    sh = torch.load(OUT / "shuffled-bias.pt", map_location="cpu", weights_only=True)
    assert torch.equal(b.gather(1, p), sh)
    summary = json.loads((OUT / "summary.json").read_text())
    assert all(summary[k] == v for k, v in summarize(rows, summary["complete"]).items())
    if summary["complete"]:
        er = [r for r in rows if r["phase"] == "eval"]
        assert len(er) == 128 and len({(r["task_id"], r["arm"]) for r in er}) == 128
        assert all(a["n"] == 32 for a in summary["arms"].values())
        assert summary["gpu_seconds"] <= LIMIT
        assert 4 <= f["calibration"]["success"] <= 6
        assert json.loads((OUT / "evaluation-started.json").read_text())["opens"] == 1
    write(
        "audit.json",
        dict(
            records=len(rows),
            scores=True,
            tokens=True,
            prompts=True,
            biases=True,
            freeze=True,
            summary=True,
            paired=True,
        ),
    )
    print("Saved-record audit PASS", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "run", "audit"])
    globals()[parser.parse_args().mode]()
