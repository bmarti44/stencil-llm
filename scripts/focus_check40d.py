#!/usr/bin/env python3
"""Unregistered frozen-router retained-history control check; no fitting."""

from __future__ import annotations

import argparse
import fcntl
import gc
import hashlib
import json
import os
import random
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import focus_check40 as base  # noqa: E402
import focus_check40c as dose  # noqa: E402

OUT = ROOT / "results/quick-checks/check40d"
OLD = ROOT / "results/quick-checks/check40b"
ARMS = ("correct", "shuffled", "OFF", "text-cue", "alpha2")
STEPS = ("SET", "NEUTRAL", "HOLD", "SWITCH", "BACK", "CLEAR")
SCORED = tuple(s for s in STEPS if s != "NEUTRAL")
TARGET = dict(
    SET="JavaScript",
    HOLD="JavaScript",
    SWITCH="Python",
    BACK="JavaScript",
    CLEAR="Python",
    NEUTRAL=None,
)
SEED = 40043
LIMIT = 7200
NEUTRAL = dict(id="neutral", prompt="Reply only OK.", name="", witness="")


def write(name, value):
    base.write_json(OUT / name, value)


def projection(n):
    requests = n * (len(ARMS) * len(STEPS) + 1)
    return dict(
        episodes=n,
        generations=requests,
        token_cap=64,
        capped_tokens=requests * 64,
        tokens_per_second=15,
        load_seconds=377.61,
        prefill_seconds_per_request=1,
        reserve_factor=1.25,
        seconds=(377.61 + requests * (64 / 15 + 1)) * 1.25,
    )


def reading(n):
    p = projection(n)
    return f"""# Check 40d — SET / HOLD / SWITCH / BACK / CLEAR

Unregistered, disclosed, 2026-09-05. Qwen3-30B-A3B bf16, greedy, 64-token
caps, unchanged 40b/40c router hook and frozen JS/Python profiles. Fit/train-on:
none. Profile-on: committed 40b's 32 cued competence replies; original dose
selection on eight setup tasks, 40c exploratory dose comparison on its reused
32 screen tasks. Evaluated-on: {n} new synthetic retained-history episodes,
five distinct expressions per episode, disjoint from those prior expressions.
Same three screen expression families; no benchmark or sealed inputs.

## Fixed pre-run design and reading

Primary alpha 3 sustained is the orchestrator's explicit override: 40c's clean
maximum was JS32/32, broken0; alpha 2 was the script's first-eligible pick
(JS25/32, broken0) and is a separate secondary arm here. No dose selection here.
SET JS bias/task1 -> neutral non-code user+generated-assistant pair under JS
bias -> HOLD JS bias/task2 -> SWITCH Python bias/task3 -> BACK JS bias/task4 ->
CLEAR bias OFF/task5. Every task request is new and uncued except text-cue.
Each arm retains its own complete user+assistant pairs AND actual KV cache;
new tokens receive the current bias, old KV is never recomputed. All 48 layers,
prefill and decode including turn-ending tokens. Bias stays JS across the delay.
An ended or capped response is retained literally; capped answers get the
inherited im_end closure. No replacement, replay, truncation or history reset.

Arms in fixed order: correct alpha3 schedule; shuffled independent within-layer
permutations of alpha3 JS bias at EVERY step including NEUTRAL and CLEAR
(matched per-layer norm, fixed seed {SEED}, frozen before outcomes); OFF throughout;
text-cue without bias ("Use JavaScript." at SET/HOLD/BACK, "Use Python." at
SWITCH, no cue at NEUTRAL/CLEAR); correct schedule alpha2 secondary. No instruction
persists in a hidden prompt. Fresh OFF CLEAR baseline once per episode precedes
all arms, for paired imposition = valid JS at CLEAR where fresh OFF is Python.
The retained OFF arm separately measures uncued-history defaults.

CONTROLLABLE iff correct valid unbroken JS >=26/32 at SET, HOLD, BACK,
valid unbroken Python >=26/32 at SWITCH and CLEAR, correct broken <=2/32 at
EVERY scored step, and shuffled valid JS <=4/32 everywhere (including the delay).
PARTIAL iff SET/HOLD/BACK meet target and breakage bars, shuffled passes, but
SWITCH or CLEAR target/breakage fails; name each failed release step.
Otherwise NOT CONTROLLABLE. Incomplete execution is INCOMPLETE, without a
behavioral verdict. If pre-run cost selects 24 episodes, use conservative
integer equivalents: >=ceil(26*24/32)=20, <=floor(2*24/32)=1 broken,
<=floor(4*24/32)=3 shuffled, disclosing changed denominators before any run.
Secondary and text arms never rescue the primary reading.

Score unchanged Python ast and Node --check parsers, coarse task check,
breakage/truncation flags, first token/first three/fence; report per-step tables,
per-family breakage, => replies and literal -> substrings (may be annotations),
and paired adjacent-language transition counts. Coarse checker can miss valid
arrow assignments; no generated programs executed. Neutral pair gets parser
and token diagnostics plus literal OK adherence, excluded from code breakage
bars because it explicitly requests non-code. This is a history/release check
on arithmetic surface syntax, not autonomous state maintenance or transfer.

## Frozen cost and execution

32-episode capped projection = {projection(32)["seconds"]:.2f} s;
24-episode fallback = {projection(24)["seconds"]:.2f} s. Select {n} before running.
{p["generations"]} generations = {n}*(5 arms*6 including neutral +1 fresh CLEAR),
{p["capped_tokens"]} capped tokens /15 tok/s +377.61 s prior measured load
+1 s/request prefill allowance, all times multiplied by 1.25 reserve =
{p["seconds"]:.2f} s ({p["seconds"] / 3600:.4f} GPU-h), cap 7200 s including load,
kernel checks and cleanup. Cooperative per-forward/token stop, no signals;
blocking operations may overrun and must be disclosed. No outcome retries.
Pinned PYTHONNOUSERSITE=1 .venv/bin/python -s -B; require transformers5.16.1
from .venv and verify every router slot0 equals raw F.linear before generation.
Reuse grouped_mm dispatch/OFF equality check. Foreground only; acquire shared
review lock, require no other Stencil RUNNING.flag or GPU compute process except
Brian's pid2705, and >=68 GiB system MemAvailable. Publish own RUNNING.flag while
running, remove on normal/exception cleanup. Never touch or signal any process.

## Results

PENDING; no outcome observed.
"""


def make_tasks(n):
    previous = json.loads((OLD / "banks.json").read_text())
    used = {t["expression"] for bank in previous.values() for t in bank}
    rng = random.Random(SEED)
    shapes = ("(({a}+{b})*({c}-{d}))", "(({a}*{b})+({c}*{d}))", "(({a}-{b})-({c}+{d}))")
    episodes = []
    for episode in range(n):
        tasks = {}
        for j, step in enumerate(SCORED):
            family = (episode + j) % 3
            while True:
                expr = shapes[family].format(
                    **{c: rng.randrange(2, 40) for c in "abcd"}
                )
                if expr not in used:
                    break
            used.add(expr)
            name = f"solve_history_{episode}_{j}"
            tasks[step] = dict(
                id=name,
                name=name,
                family=f"screen_{family}",
                expression=expr,
                witness=r"[+*\-]",
                prompt=(
                    f"For the arithmetic expression {expr}, provide a solution. "
                    f"If writing a function, name it {name}."
                ),
            )
        episodes.append(tasks)
    return episodes


def bias_for(arm, step, episode, biases):
    if arm == "shuffled":
        return biases["shuffled"][episode, STEPS.index(step)]
    if arm in ("correct", "alpha2") and step != "CLEAR":
        direction = biases["python"] if step == "SWITCH" else biases["js"]
        return direction if arm == "correct" else direction * (2 / 3)
    return None


def cue_for(arm, step):
    return (
        TARGET[step] if arm == "text-cue" and step not in ("NEUTRAL", "CLEAR") else None
    )


def digest_bias(bias):
    return (
        None
        if bias is None
        else hashlib.sha256(bias.float().numpy().tobytes()).hexdigest()
    )


def decision(arms, n, complete):
    if not complete:
        return "INCOMPLETE", ["execution did not finish"]
    target, broken, shuffled = (26, 2, 4) if n == 32 else (20, 1, 3)
    passes = {
        s: arms["correct"][s]["valid"].get(TARGET[s], 0) >= target
        and arms["correct"][s]["broken"] <= broken
        for s in SCORED
    }
    control = all(arms["shuffled"][s]["js"] <= shuffled for s in STEPS)
    if all(passes.values()) and control:
        return "CONTROLLABLE", []
    failures = [s for s in SCORED if not passes[s]] + ([] if control else ["shuffled"])
    if control and all(passes[s] for s in ("SET", "HOLD", "BACK")):
        return "PARTIAL", failures
    return "NOT CONTROLLABLE", failures


def summarize(rows, n, complete=False):
    arms = {
        a: {
            s: dose.aggregate([r for r in rows if r["arm"] == a and r["step"] == s])
            for s in STEPS
        }
        for a in ARMS
    }
    verdict, failures = decision(arms, n, complete)
    defaults = {r["episode"]: r for r in rows if r["arm"] == "fresh-OFF"}
    imposition = {}
    transitions = {}
    for arm in ARMS:
        clear = [r for r in rows if r["arm"] == arm and r["step"] == "CLEAR"]
        eligible = [
            r
            for r in clear
            if defaults[r["episode"]]["score"]["valid_language"] == "Python"
        ]
        imposition[arm] = dict(
            python_default_pairs=len(eligible),
            js_impositions=sum(
                r["score"]["valid_language"] == "JavaScript" for r in eligible
            ),
        )
        by_key = {(r["episode"], r["step"]): r for r in rows if r["arm"] == arm}
        transitions[arm] = {}
        for left, right in zip(SCORED, SCORED[1:], strict=False):
            counts = Counter()
            for e in range(n):
                if (e, left) in by_key and (e, right) in by_key:
                    left_language, right_language = (
                        by_key[e, s]["score"]["valid_language"] or "broken"
                        for s in (left, right)
                    )
                    counts[f"{left_language} -> {right_language}"] += 1
            transitions[arm][f"{left}->{right}"] = dict(counts)
    return dict(
        reading=verdict,
        failed_conditions=failures,
        complete=complete,
        episodes=n,
        arms=arms,
        clear_imposition=imposition,
        transitions=transitions,
        fresh_off=dose.aggregate(list(defaults.values())),
        records=len(rows),
        generated_tokens=sum(len(r["generated_token_ids"]) for r in rows),
        neutral_ok={
            a: sum(
                r["text"].strip() == "OK"
                for r in rows
                if r["arm"] == a and r["step"] == "NEUTRAL"
            )
            for a in ARMS
        },
    )


def cpu_checks():
    import torch
    from transformers import AutoTokenizer, Qwen3MoeConfig, Qwen3MoeForCausalLM

    torch.set_num_threads(2)
    checks = dose.cpu_checks()
    cfg = Qwen3MoeConfig(
        vocab_size=64,
        hidden_size=16,
        intermediate_size=32,
        moe_intermediate_size=8,
        num_hidden_layers=2,
        num_attention_heads=2,
        num_key_value_heads=1,
        head_dim=8,
        num_experts=4,
        num_experts_per_tok=2,
    )
    engine = base.Engine.__new__(base.Engine)
    engine.model = Qwen3MoeForCausalLM(cfg).eval()
    engine.torch, engine.device = torch, torch.device("cpu")
    engine.deadline, engine.eos = time.monotonic() + 300, set()
    real_tokenizer = AutoTokenizer.from_pretrained(base.MODEL, local_files_only=True)

    class Tokenizer:
        def apply_chat_template(self, *args, **kwargs):
            return [
                1 + i % 62 for i in real_tokenizer.apply_chat_template(*args, **kwargs)
            ]

        def encode(self, *args, **kwargs):
            return [1 + i % 62 for i in real_tokenizer.encode(*args, **kwargs)]

        def decode(self, ids, **kwargs):
            return str(ids)

        def convert_tokens_to_ids(self, token):
            return 63

    engine.tokenizer = Tokenizer()
    engine.hooks = base.RouterHooks(
        [layer.mlp.gate for layer in engine.model.model.layers]
    )
    biases = dict(js=torch.tensor([[0.0, 0.0, 0.0, 10.0]] * 2))
    biases["python"] = -biases["js"]
    biases["shuffled"] = biases["js"].expand(1, 6, 2, 4).clone()
    history, session, prefix, observed = None, {}, [], []
    handles = [
        g.register_forward_pre_hook(
            lambda m, a: observed.append(
                None if engine.hooks.bias is None else engine.hooks.bias.clone()
            )
        )
        for g in engine.hooks.gates
    ]
    for step in STEPS:
        observed.clear()
        bias = bias_for("correct", step, 0, biases)
        messages = base.messages_for(NEUTRAL, history=history)
        r, _ = engine.generate(messages, bias=bias, cap=2, session=session)
        assert r["cache_prefix_token_ids"] == prefix
        assert r["retained_kv"] and r["appended_terminal_token_ids"] == [63]
        assert len(messages) % 2 == 0
        assert observed and all(
            (x is None)
            if bias is None
            else torch.equal(x.float(), bias.bfloat16().float())
            for x in observed
        )
        prefix = prefix + r["input_token_ids"] + r["generated_token_ids"] + [63]
        assert session["past"].get_seq_length() == len(prefix)
        history = messages + [dict(role="assistant", content=r["text"])]
    for h in handles:
        h.remove()
    engine.hooks.close()
    arms = {
        a: {s: dict(valid={TARGET[s]: 26}, broken=0, js=0) for s in STEPS} for a in ARMS
    }
    assert decision(arms, 32, True)[0] == "CONTROLLABLE"
    arms["correct"]["CLEAR"]["valid"] = {"Python": 25}
    assert decision(arms, 32, True) == ("PARTIAL", ["CLEAR"])
    arms["correct"]["SET"]["broken"] = 3
    assert decision(arms, 32, True)[0] == "NOT CONTROLLABLE"
    assert decision(arms, 32, False)[0] == "INCOMPLETE"
    assert cue_for("text-cue", "CLEAR") is None
    assert bias_for("shuffled", "CLEAR", 0, biases) is not None
    assert projection(32)["seconds"] < LIMIT
    assert not torch.cuda.is_initialized()
    return dict(
        checks,
        retained_real_consumer=True,
        complete_pairs=True,
        switch_back_clear_observed_at_gates=True,
        capped_pair_closure=True,
        verdict_boundaries=True,
        cuda_initialized=False,
    )


def prepare():
    import torch

    assert not (OUT / "records.jsonl").exists(), "Refuse outcome overwrite"
    n = 32 if projection(32)["seconds"] <= LIMIT else 24
    assert projection(n)["seconds"] <= LIMIT
    checks = cpu_checks()
    OUT.mkdir(parents=True, exist_ok=True)
    write("cpu.json", checks)
    write(
        "projection.json",
        dict(full=projection(32), fallback=projection(24), selected=projection(n)),
    )
    write("tasks.json", make_tasks(n))
    frozen = torch.load(OLD / "frozen-biases.pt", map_location="cpu", weights_only=True)
    js, py = frozen["correct"] * 0.75, frozen["swapped"] * 0.75
    assert torch.allclose(py, -js, atol=3e-6, rtol=0)
    generator = torch.Generator().manual_seed(SEED)
    shuffled = torch.stack(
        [
            torch.stack(
                [
                    torch.stack(
                        [
                            row[torch.randperm(len(row), generator=generator)]
                            for row in js
                        ]
                    )
                    for _ in STEPS
                ]
            )
            for _ in range(n)
        ]
    )
    assert torch.allclose(shuffled.norm(dim=-1), js.norm(dim=-1).expand(n, 6, 48))
    torch.save(dict(js=js, python=py, shuffled=shuffled), OUT / "biases.pt")
    for name in ("README.md", "prewritten-reading.md"):
        (OUT / name).write_text(reading(n))
    paths = [
        Path(__file__),
        ROOT / "scripts/focus_check40.py",
        ROOT / "scripts/focus_check40b.py",
        ROOT / "scripts/focus_check40c.py",
        OUT / "prewritten-reading.md",
        OUT / "tasks.json",
        OUT / "projection.json",
        OUT / "biases.pt",
        OLD / "frozen-biases.pt",
        OLD / "banks.json",
    ]
    write(
        "freeze.json",
        dict(
            utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            runtime=dose.runtime(),
            files={str(p): base.sha(p) for p in paths},
        ),
    )
    print(json.dumps(dict(checks=checks, projection=projection(n))), flush=True)


def verify_freeze():
    for name, digest in json.loads((OUT / "freeze.json").read_text())["files"].items():
        assert base.sha(Path(name)) == digest, name


def resources():
    result = subprocess.run(
        [
            "nvidia-smi",
            "--query-compute-apps=pid,process_name,used_memory",
            "--format=csv,noheader",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    gpu = [line.split(",", 2) for line in result.stdout.splitlines() if line.strip()]
    blockers = [row for row in gpu if int(row[0]) != 2705]
    mem = dict(
        line.split(":", 1) for line in Path("/proc/meminfo").read_text().splitlines()
    )
    available = int(mem["MemAvailable"].split()[0]) / 2**20
    flags = [str(p) for p in (ROOT / "results/quick-checks").glob("*/RUNNING.flag")]
    return dict(
        utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        gpu=gpu,
        blockers=blockers,
        flags=flags,
        available_gib=available,
        ready=not blockers and not flags and available >= 68,
    )


def run():
    import torch

    verify_freeze()
    dose.runtime()
    assert not (OUT / "records.jsonl").exists(), "No retries or overwrite"
    lock = (ROOT / ".review.lock").open("a")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock.close()
        print("WAIT: repository lock occupied", flush=True)
        return
    resource = resources()
    write("resources.json", resource)
    if not resource["ready"]:
        lock.close()
        print(json.dumps(dict(status="WAIT", **resource)), flush=True)
        return
    tasks = json.loads((OUT / "tasks.json").read_text())
    biases = torch.load(OUT / "biases.pt", map_location="cpu", weights_only=True)
    flag = OUT / "RUNNING.flag"
    with flag.open("x") as f:
        f.write(str(os.getpid()) + "\n")
    rows, engine, session = [], None, None
    start = time.monotonic()
    base.GPU_SECONDS = LIMIT
    complete, reason = False, "interrupted"
    journal = (OUT / "records.jsonl").open("x")

    def request(task, arm, step, episode, history=None, session=None):
        bias = None if arm == "fresh-OFF" else bias_for(arm, step, episode, biases)
        cue = cue_for(arm, step)
        messages = base.messages_for(task, cue=cue, history=history)
        r, _ = engine.generate(messages, bias=bias, cap=64, session=session)
        r.update(
            id=len(rows),
            arm=arm,
            step=step,
            episode=episode,
            task_id=task["id"],
            family=task.get("family", "neutral"),
            target=TARGET[step],
            cue=cue,
            alpha=2 if arm == "alpha2" else 3 if arm in ("correct", "shuffled") else 0,
            bias_active=bias is not None,
            score=base.score(r["text"], task, r["truncated"]),
        )
        r.update(dose.report_fields(r, engine.tokenizer))
        assert r["bias_sha256"] == digest_bias(bias)
        journal.write(json.dumps(r) + "\n")
        journal.flush()
        rows.append(r)
        print(
            json.dumps(
                dict(
                    n=len(rows),
                    episode=episode,
                    arm=arm,
                    step=step,
                    language=r["score"]["valid_language"],
                    broken=r["score"]["broken"],
                    elapsed=time.monotonic() - start,
                )
            ),
            flush=True,
        )
        if r["cost_stopped"]:
            raise base.BudgetStop("cooperative token budget")
        return messages + [dict(role="assistant", content=r["text"])]

    try:
        engine = base.Engine(start)
        runtime = dose.runtime()
        runtime.update(
            load_seconds=engine.load_seconds,
            raw_slot_verified_layers=sum(
                dose.raw_contract(g) for g in engine.hooks.gates
            ),
        )
        write("runtime.json", runtime)
        kernel = engine.verify_kernel()
        write("kernel.json", kernel)
        assert kernel["adopted"]
        for episode, episode_tasks in enumerate(tasks):
            request(episode_tasks["CLEAR"], "fresh-OFF", "CLEAR", episode)
            for arm in ARMS:
                history, session = None, {}
                for step in STEPS:
                    task = NEUTRAL if step == "NEUTRAL" else episode_tasks[step]
                    history = request(task, arm, step, episode, history, session)
                session = None
            write("summary.json", summarize(rows, len(tasks)))
        complete, reason = True, "all scheduled generations complete"
    except base.BudgetStop as exc:
        reason = str(exc)
    except Exception as exc:
        reason = repr(exc)
        raise
    finally:
        journal.close()
        result = summarize(rows, len(tasks), complete)
        result.update(reason=reason, cap_seconds=LIMIT, token_cap=64)
        session = None
        if engine is not None:
            result["peak_allocated_gib"] = torch.cuda.max_memory_allocated() / 2**30
            engine.hooks.close()
            del engine
        gc.collect()
        if torch.cuda.is_initialized():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        result["gpu_seconds"] = time.monotonic() - start
        result["cap_overrun_seconds"] = max(0, result["gpu_seconds"] - LIMIT)
        write("summary.json", result)
        flag.unlink()
        lock.close()
        print(
            json.dumps(
                dict(
                    reading=result["reading"],
                    reason=reason,
                    gpu_seconds=result["gpu_seconds"],
                )
            ),
            flush=True,
        )


def audit():
    import torch
    from transformers import AutoTokenizer

    verify_freeze()
    tokenizer = AutoTokenizer.from_pretrained(base.MODEL, local_files_only=True)
    rows = [
        json.loads(line) for line in (OUT / "records.jsonl").read_text().splitlines()
    ]
    tasks = json.loads((OUT / "tasks.json").read_text())
    biases = torch.load(OUT / "biases.pt", map_location="cpu", weights_only=True)
    history, prefixes = {}, {}
    for r in rows:
        e, a, s = r["episode"], r["arm"], r["step"]
        task = NEUTRAL if s == "NEUTRAL" else tasks[e][s]
        key = (e, a)
        messages = base.messages_for(task, cue_for(a, s), history.get(key))
        assert r["history"] == messages
        assert r["score"] == base.score(r["text"], task, r["truncated"])
        assert (
            tokenizer.decode(r["generated_token_ids"], skip_special_tokens=True)
            == r["text"]
        )
        assert all(r[k] == v for k, v in dose.report_fields(r, tokenizer).items())
        rendered = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            return_dict=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        assert rendered == r["rendered_input_token_ids"]
        prefix = prefixes.get(key, [])
        assert prefix == r["cache_prefix_token_ids"]
        expected = rendered
        if prefix:
            expected = tokenizer.encode(
                "\n", add_special_tokens=False
            ) + tokenizer.apply_chat_template(
                [messages[-1]],
                tokenize=True,
                return_dict=False,
                add_generation_prompt=True,
                enable_thinking=False,
            )
        assert expected == r["input_token_ids"]
        bias = None if a == "fresh-OFF" else bias_for(a, s, e, biases)
        assert digest_bias(bias) == r["bias_sha256"]
        assert r["retained_kv"] == (a != "fresh-OFF")
        if a != "fresh-OFF":
            history[key] = messages + [dict(role="assistant", content=r["text"])]
            prefixes[key] = (
                prefix
                + expected
                + r["generated_token_ids"]
                + r["appended_terminal_token_ids"]
            )
    summary = json.loads((OUT / "summary.json").read_text())
    rebuilt = summarize(rows, len(tasks), summary["complete"])
    assert all(summary[k] == v for k, v in rebuilt.items())
    expected_order = [
        (e, a, s)
        for e in range(len(tasks))
        for a, steps in [("fresh-OFF", ("CLEAR",))] + [(a, STEPS) for a in ARMS]
        for s in steps
    ]
    assert [(r["episode"], r["arm"], r["step"]) for r in rows] == expected_order[
        : len(rows)
    ]
    if summary["complete"]:
        assert len(rows) == len(expected_order)
    result = dict(
        records=len(rows),
        parsers_reproduced=True,
        token_text=True,
        histories_and_actual_kv_prefixes=True,
        bias_schedule=True,
        aggregates_and_reading=True,
        freeze=True,
        cuda_initialized=torch.cuda.is_initialized(),
    )
    assert not result["cuda_initialized"]
    write("audit.json", result)
    print(json.dumps(result), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("prepare", "run", "test", "audit", "resources"),
        required=True,
    )
    args = parser.parse_args()
    if args.mode == "test":
        print(json.dumps(cpu_checks()))
    elif args.mode == "resources":
        print(json.dumps(resources()))
    else:
        globals()[args.mode]()


if __name__ == "__main__":
    main()
