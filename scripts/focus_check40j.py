#!/usr/bin/env python3
"""Check40j: fixed rendering-by-router screen, retained OFF imitation histories."""

from __future__ import annotations

import argparse
import ast
import fcntl
import gc
import hashlib
import json
import os
import random
import subprocess
import time
from collections import Counter
from pathlib import Path

import focus_check40g as g
import focus_check40i as i

base, e, dose = g.base, g.e, g.e.dose
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/quick-checks/check40j"
SEED, N, LIMIT = 401006, 16, 2700
RULE = "Live rules: (1) Write all code in JavaScript."
ARMS = {
    "P1": ["OFF", "text-only", "bias-only", "text+bias"],
    "P2": ["text-only", "text+mask", "text+bias", "text+bias+mask"],
}
BIAS = ROOT / "results/quick-checks/check40g/js-control-bias.pt"
READING = """# Check40j — rendered-rule additivity screen

Prewritten 2026-09-06, before GPU work. Data lineage: fit-on = nothing (no fitting
anywhere in this check); evaluated-on = 16 fresh synthetic arithmetic tasks only,
with 96 further fresh expressions used only to generate OFF histories. No benchmark
data. The inherited frozen actuator was profiled previously on40b competence;
no new profiling, fitting, selection, tuning or outcome-based retries.

Seed401006; same three expression families/40e operand range40..89 and EXACT40e
zero-argument prompt/system/suffix. Names and expressions fresh; disjoint from all
40e/40g screen items. Each of16 target tasks is reused across BOTH phases/arms.
Qwen3-30B-A3B HF bf16; identical40 RouterHooks, alpha3 JS tensor loaded directly
from40g/js-control-bias.pt, all48 layers, prefill+decode, greedy, cap64 tokens.
One model load; 45 GPU-minute total cap includes load/kernel validation/cleanup.
224 generations: P1 4x16; OFF history 6x16; P2 4x16. No enlargement.

P1: OFF | text-only | bias-only | text+bias, fresh session each cell.
P2: generate six consecutive OFF answers per task using further fresh expressions;
retain actual tokens/KV, then fork identical cache prefix into text-only | text+mask |
text+bias | text+bias+mask for the seventh (target) request. Retain all OFF outcomes
without selection/replacement; report how many really are Python. If histories
are not all Python, disclose the weaker achieved pressure; do not regenerate.
Mask is40i.mask_change(...,'Z','SWITCH',...), i.e. persistent key masking of all six
assistant bodies incl fences/broken replies, excluding EOS/headers; absolute
positions preserved, no recomputation or replacement. Downstream KV can carry traces.

Literal user-authorized text: "Live rules: (1) Write all code in JavaScript."
Placed as this line + newline BEFORE the current request in the current user turn.
Placement reference: src/stencil/focus3.py:render (line258), which prepends live
rules before the current request. IMPORTANT format discrepancy: the committed
renderer actually emits an Active user rules JSON block, NOT the literal above;
no source renderer contains 'Live rules:'. This check follows Brian's exact literal
cue, copying only prepend placement; it is not byte-identical current FOCUS-3 output.
No additional cue or wrapper is added. Existing40e system and suffix remain.

Executable language/answer scorer:40g.score with js_control=True (Python AST
arithmetic evaluation; Node TypeScript-parser/VM JavaScript execution). Broken:
40i/base.score flags (empty, invalid/ambiguous, fence error, truncation, repetition),
reported independently of executable correctness. Full both scorer records retained.
JS correct requires40g executable correctness AND not40i broken; Python count uses
40i valid_language. Semantic-only failures are reported separately. Fence labels and
first tokens are diagnostic, not language evidence.

PRE-WRITTEN READINGS (fixed):
R1 "rendering suffices": text-only >=14/16 in BOTH phases -> the lever adds nothing
measurable at this pressure; actuator not in default shipping, rendering-only primary.
R2 "lever earns its place": P2 text-only <=10/16 AND text+bias+mask >=text-only+4
with breakage <=1/16 -> retain actuator in composed arm; larger C-vs-R justified.
R3 anything else -> INCONCLUSIVE at n=16; record and stop. No enlargement.
Incomplete/budget-stopped runs are INCOMPLETE, never assigned R1/R2/R3.
Diagnostic only: P1 bias-only versus40g3/8, and P1 text+bias versus text-only.
Report paired tables; P2 combined-vs-text exact win/loss/tie counts, exact binomial
sign p (descriptive), Clopper-Pearson95% intervals for each success rate and
conditional win fraction among discordants. Paired gain CI: conservative95% interval
from Bonferroni97.5% CP marginal intervals for win and loss probabilities. n=16 is a
screen, not an equivalence or population-level no-benefit proof.

Resource estimate:40i480 generations took1319.6s;224 at same per-generation cost
plus full cold-load reserve300s is916s, well below2700s; not a worst-case guarantee.
Cooperative request/token deadline with cleanup reserve; no signals, background
launch, benchmark reads, further profiling, push or modifications to prior artifacts.

Results pending.
"""


def write(name, value):
    base.write_json(OUT / name, value)


def sha_ids(ids):
    return hashlib.sha256(json.dumps(ids).encode()).hexdigest()


def tasks():
    rng, seen, result = random.Random(SEED), set(), []

    def collect(v):
        if isinstance(v, dict):
            if "expression" in v:
                seen.add(v["expression"])
            for x in v.values():
                collect(x)
        elif isinstance(v, list):
            for x in v:
                collect(x)

    for p in [e.OUT / "banks.json", g.OUT / "banks.json"]:
        collect(json.loads(p.read_text()))
    for k in range(N * 7):
        while True:
            a, b, c, d = rng.sample(range(40, 90), 4)
            expr = [
                f"(({a}+{b})*({c}-{d}))",
                f"(({a}*{b})+({c}*{d}))",
                f"(({a}-{b})-({c}+{d}))",
            ][k % 3]
            if expr not in seen:
                break
        seen.add(expr)
        name = f"solve_j_{k:03d}"
        result.append(
            dict(
                id=name,
                name=name,
                pair="P1",
                js_control=True,
                expression=expr,
                expected=e.arithmetic(ast.parse(expr, mode="eval").body),
                witness=r"return",
                prompt=(
                    f"Write a zero-argument function named {name} that returns {expr}."
                ),
            )
        )
    return [
        dict(target=result[j * 7], history=result[j * 7 + 1 : j * 7 + 7])
        for j in range(N)
    ]


def messages(task, arm, history=None):
    value = base.messages_for(task, history=history)
    if "text" in arm:
        value[-1]["content"] = RULE + "\n" + value[-1]["content"]
    return value


def score(text, task, truncated):
    executable = g.score(text, task, truncated)
    syntax = base.score(text, task, truncated)
    return dict(
        executable=executable,
        syntax=syntax,
        broken=syntax["broken"],
        python=syntax["valid_language"] == "Python",
        js_correct=executable["valid_skill"] == "JavaScript" and not syntax["broken"],
    )


def cp(k, n, alpha=0.05):
    from scipy.stats import beta

    return [
        float(beta.ppf(alpha / 2, k, n - k + 1)) if k else 0.0,
        float(beta.ppf(1 - alpha / 2, k + 1, n - k)) if k < n else 1.0,
    ]


def summarize(rows, complete=False):
    from scipy.stats import binomtest

    arms, paired = {}, {}
    for phase, names in ARMS.items():
        arms[phase] = {}
        paired[phase] = []
        for arm in names:
            cell = [r for r in rows if r["phase"] == phase and r["arm"] == arm]
            js = sum(r["score"]["js_correct"] for r in cell)
            arms[phase][arm] = dict(
                n=len(cell),
                js_correct=js,
                python=sum(r["score"]["python"] for r in cell),
                broken=sum(r["score"]["broken"] for r in cell),
                semantic_failures=sum(
                    not r["score"]["executable"]["semantic"] for r in cell
                ),
                js_ci95=cp(js, len(cell)) if cell else None,
                fence_labels=dict(Counter(r["fence_label"] for r in cell)),
                first_tokens=dict(Counter(r["first_token"] for r in cell)),
            )
        for ep in range(N):
            paired[phase].append(
                dict(
                    episode=ep,
                    arms={
                        r["arm"]: dict(
                            js_correct=r["score"]["js_correct"],
                            python=r["score"]["python"],
                            broken=r["score"]["broken"],
                            fence=r["fence_label"],
                            first_token=r["first_token"],
                        )
                        for r in rows
                        if r["phase"] == phase and r["episode"] == ep
                    },
                )
            )
    wins = losses = ties = both = 0
    for p in paired["P2"]:
        a = p["arms"]
        if "text-only" in a and "text+bias+mask" in a:
            x, y = a["text+bias+mask"]["js_correct"], a["text-only"]["js_correct"]
            wins += x and not y
            losses += y and not x
            ties += x == y
            both += x and y
    n = wins + losses + ties
    gain_ci = None
    if n:
        win_ci, loss_ci = cp(wins, n, 0.025), cp(losses, n, 0.025)
        gain_ci = [win_ci[0] - loss_ci[1], win_ci[1] - loss_ci[0]]
    a, b = arms["P1"]["text-only"], arms["P2"]["text-only"]
    c = arms["P2"]["text+bias+mask"]
    reading = (
        "INCOMPLETE"
        if not complete
        else "R1"
        if a["js_correct"] >= 14 and b["js_correct"] >= 14
        else "R2"
        if b["js_correct"] <= 10
        and c["js_correct"] >= b["js_correct"] + 4
        and c["broken"] <= 1
        else "R3"
    )
    histories = [r for r in rows if r["phase"] == "history"]
    return dict(
        complete=complete,
        reading=reading,
        arms=arms,
        paired=paired,
        paired_sign=dict(
            wins=wins,
            losses=losses,
            ties=ties,
            both_success=both,
            both_failure=ties - both,
            gain=(wins - losses) / n if n else None,
            gain_ci95_conservative=gain_ci,
            conditional_win_ci95=cp(wins, wins + losses)
            if wins + losses
            else [0.0, 1.0],
            sign_p_two_sided=float(binomtest(wins, wins + losses).pvalue)
            if wins + losses
            else 1.0,
        ),
        history=dict(
            n=len(histories),
            python=sum(r["score"]["python"] for r in histories),
            broken=sum(r["score"]["broken"] for r in histories),
        ),
        generations=len(rows),
    )


def verify():
    f = json.loads((OUT / "freeze.json").read_text())
    for path, digest in f["files"].items():
        assert base.sha(ROOT / path) == digest, path
    return f


def prepare():
    import torch
    from transformers import AutoTokenizer

    assert not (OUT / "records.jsonl").exists()
    bank = tasks()
    tok = AutoTokenizer.from_pretrained(base.MODEL, local_files_only=True)
    task = bank[0]["target"]
    assert messages(task, "OFF") == e.messages(task)
    assert (
        messages(task, "text-only")[-1]["content"]
        == RULE + "\n" + e.messages(task)[-1]["content"]
    )
    for lang, code in [
        ("Python", f"def {task['name']}():\n    return {task['expression']}"),
        ("JavaScript", f"function {task['name']}() {{ return {task['expression']}; }}"),
    ]:
        s = score(code, task, False)
        assert not s["broken"] and s["executable"]["valid_skill"] == lang
        assert score(code[:-1] + "@", task, False)["broken"]
    checks = i.cpu_checks()
    bias = torch.load(BIAS, map_location="cpu", weights_only=True)
    assert torch.equal(
        bias,
        torch.load(
            ROOT / "results/quick-checks/check40c/selected-bias.pt",
            map_location="cpu",
            weights_only=True,
        )
        * 1.5,
    )
    control = json.loads((g.OUT / "records.jsonl").read_text().splitlines()[0])
    assert i.prior.digest_bias(bias) == control["bias_sha256"]
    assert len(tok.encode(messages(task, "text-only")[-1]["content"])) < 128
    write("tasks.json", bank)
    (OUT / "README.md").write_text(READING)
    (OUT / "prewritten-reading.md").write_text(READING)
    write("cpu.json", dict(inherited=checks, scorer_and_prompt=True, tensor_equal=True))
    paths = [
        Path(__file__),
        BIAS,
        OUT / "tasks.json",
        OUT / "prewritten-reading.md",
        ROOT / "src/stencil/focus3.py",
        e.OUT / "banks.json",
        g.OUT / "banks.json",
    ]
    paths += [
        ROOT / f"scripts/focus_check{s}.py"
        for s in ["40", "40b", "40c", "40d", "40e", "40f", "40g", "40h", "40i", "43"]
    ]
    write(
        "freeze.json",
        dict(
            recipe_commit=None,
            seed=SEED,
            tensor_sha256=i.prior.digest_bias(bias),
            tensor_file_sha256=base.sha(BIAS),
            files={str(p.relative_to(ROOT)): base.sha(p) for p in paths},
        ),
    )
    print("CPU preparation PASS", flush=True)


def run():
    import torch

    frozen = verify()
    assert not (OUT / "records.jsonl").exists(), "No retry/overwrite"
    recipe = subprocess.check_output(
        ["git", "log", "-1", "--format=%H", "--", "scripts/focus_check40j.py"],
        cwd=ROOT,
        text=True,
    ).strip()
    assert (
        subprocess.check_output(
            ["git", "show", f"{recipe}:scripts/focus_check40j.py"], cwd=ROOT
        )
        == Path(__file__).read_bytes()
    )
    frozen["recipe_commit"] = recipe
    write("freeze.json", frozen)
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
    verify()
    flag = OUT / "RUNNING.flag"
    with flag.open("x") as stream:
        stream.write(json.dumps(dict(pid=os.getpid(), check="40j")) + "\n")
    write("resources.json", status)
    start = time.monotonic()
    base.GPU_SECONDS, base.SEED = LIMIT - 15, SEED
    engine = session = shared = None
    rows, complete, reason = [], False, "interrupted"
    journal = (OUT / "records.jsonl").open("x")
    bank = json.loads((OUT / "tasks.json").read_text())
    bias = torch.load(BIAS, map_location="cpu", weights_only=True)

    def request(task, phase, arm, ep, session, history=None):
        active = bias if "bias" in arm else None
        event = (
            i.mask_change(engine, session, "Z", "SWITCH", active)
            if "mask" in arm
            else None
        )
        msg = messages(task, arm, history)
        r = i.generation(engine, msg, active, session, cap=64)
        r.update(
            id=len(rows),
            phase=phase,
            arm=arm,
            episode=ep,
            task=task,
            mask_event=event,
            score=score(r["text"], task, r["truncated"]),
        )
        r.update(dose.report_fields(r, engine.tokenizer))
        assert r["bias_sha256"] == i.prior.digest_bias(active)
        assert all(t["masked"] == session["masked"] for t in r["mask_forward_trace"])
        begin = len(r["cache_prefix_token_ids"]) + len(r["input_token_ids"])
        end = begin + len(r["generated_token_ids"]) - int(r["eos"])
        if end > begin:
            session["bodies"].append([begin, end])
        required = [
            "generated_token_ids",
            "input_token_ids",
            "cache_prefix_token_ids",
            "cache_prefix_sha256",
            "bias_sha256",
            "mask_forward_trace",
            "mask_event",
            "first_token",
            "fence_label",
            "score",
            "task",
            "history",
        ]
        assert all(k in r for k in required)
        journal.write(json.dumps(r) + "\n")
        journal.flush()
        rows.append(r)
        print(
            json.dumps(
                dict(
                    n=len(rows),
                    phase=phase,
                    arm=arm,
                    episode=ep,
                    js=r["score"]["js_correct"],
                    broken=r["score"]["broken"],
                    elapsed=round(time.monotonic() - start, 2),
                )
            ),
            flush=True,
        )
        if r["cost_stopped"]:
            raise base.BudgetStop("cooperative deadline")
        return msg + [dict(role="assistant", content=r["text"])]

    try:
        engine = base.Engine(start)
        write("runtime.json", dict(dose.runtime(), load_seconds=engine.load_seconds))
        kernel = engine.verify_kernel()
        write("kernel.json", kernel)
        assert kernel["adopted"]
        assert len(engine.hooks.gates) == 48
        assert all(dose.raw_contract(gate) for gate in engine.hooks.gates)
        for ep, item in enumerate(bank):
            for arm in ARMS["P1"]:
                session = i.session_new()
                request(item["target"], "P1", arm, ep, session)
                session = None
        for ep, item in enumerate(bank):
            shared, history = i.session_new(), None
            for task in item["history"]:
                history = request(task, "history", "OFF", ep, shared, history)
            assert len(shared["bodies"]) == 6
            for arm in ARMS["P2"]:
                session = i.fork_session(shared)
                request(item["target"], "P2", arm, ep, session, history)
                session = None
            shared = None
            write("summary.json", summarize(rows))
        complete, reason = True, "all 224 generations complete"
    except base.BudgetStop as exc:
        reason = str(exc)
    except Exception as exc:
        reason = repr(exc)
        raise
    finally:
        journal.close()
        session = shared = None
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
            recipe_commit=recipe,
            peak_allocated_gib=torch.cuda.max_memory_allocated() / 2**30,
        )
        write("summary.json", result)
        flag.unlink()
        print(
            json.dumps({k: result[k] for k in ["reading", "reason", "gpu_seconds"]}),
            flush=True,
        )


def audit():
    from transformers import AutoTokenizer

    verify()
    tok = AutoTokenizer.from_pretrained(base.MODEL, local_files_only=True)
    rows = [json.loads(x) for x in (OUT / "records.jsonl").read_text().splitlines()]
    assert tasks() == json.loads((OUT / "tasks.json").read_text())
    bank = tasks()
    for n, r in enumerate(rows):
        assert r["id"] == n
        assert r["score"] == score(r["text"], r["task"], r["truncated"])
        assert r["text"] == tok.decode(
            r["generated_token_ids"], skip_special_tokens=True
        )
        assert r["cache_prefix_sha256"] == sha_ids(r["cache_prefix_token_ids"])
        assert r["input_sha256"] == sha_ids(r["input_token_ids"])
        assert all(r[k] == v for k, v in dose.report_fields(r, tok).items())
        active = "bias" in r["arm"]
        assert r["bias_sha256"] == (verify()["tensor_sha256"] if active else None)
        prefix = []
        history = None
        bodies = []
        if r["phase"] != "P1":
            prior = [
                x
                for x in rows[:n]
                if x["phase"] == "history" and x["episode"] == r["episode"]
            ]
            for x in prior:
                begin = len(prefix) + len(x["input_token_ids"])
                bodies.append(
                    [begin, begin + len(x["generated_token_ids"]) - int(x["eos"])]
                )
                prefix += (
                    x["input_token_ids"]
                    + x["generated_token_ids"]
                    + x["appended_terminal_token_ids"]
                )
                history = x["history"] + [dict(role="assistant", content=x["text"])]
        assert r["cache_prefix_token_ids"] == prefix
        assert r["history"] == messages(r["task"], r["arm"], history)
        assert r["rendered_input_token_ids"] == tok.apply_chat_template(
            r["history"],
            tokenize=True,
            return_dict=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        ids = (
            r["rendered_input_token_ids"]
            if not prefix
            else tok.encode("\n", add_special_tokens=False)
            + tok.apply_chat_template(
                [r["history"][-1]],
                tokenize=True,
                return_dict=False,
                add_generation_prompt=True,
                enable_thinking=False,
            )
        )
        assert r["input_token_ids"] == ids
        masked = (
            sorted({p for b, end in bodies for p in range(b, end)})
            if "mask" in r["arm"]
            else []
        )
        assert r["masked_positions"] == masked
        if masked:
            assert r["mask_event"]["bodies"] == bodies and len(bodies) == 6
            assert r["mask_event"]["absolute_length"] == len(prefix)
            assert not r["mask_event"]["placeholders"]
        else:
            assert r["mask_event"] is None
        position = len(prefix)
        lengths = [len(ids)] + [1] * (
            len(r["generated_token_ids"]) + len(r["appended_terminal_token_ids"])
        )
        assert [t["length"] for t in r["mask_forward_trace"]] == lengths
        for trace in r["mask_forward_trace"]:
            assert trace == dict(start=position, length=trace["length"], masked=masked)
            position += trace["length"]
        assert r["task"] in [
            bank[r["episode"]]["target"],
            *bank[r["episode"]]["history"],
        ]
    summary = json.loads((OUT / "summary.json").read_text())
    assert all(summary[k] == v for k, v in summarize(rows, summary["complete"]).items())
    if summary["complete"]:
        assert len(rows) == 224 and summary["gpu_seconds"] <= LIMIT
        assert all(
            v["n"] == 16 for phase in summary["arms"].values() for v in phase.values()
        )
        assert summary["history"]["n"] == 96
    write(
        "audit.json",
        dict(
            records=len(rows),
            scores=True,
            tokens=True,
            cache_prefixes=True,
            every_forward_mask=True,
            summary=True,
            freeze=True,
        ),
    )
    print("Saved-record audit PASS", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "run", "audit"])
    globals()[parser.parse_args().mode]()
