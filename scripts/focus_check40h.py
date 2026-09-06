#!/usr/bin/env python3
"""Check40h closure: frozen routing plus masking at every skill change."""

from __future__ import annotations

import argparse
import copy
import fcntl
import gc
import hashlib
import json
import os
import random
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import focus_check40f as inherited  # noqa: E402

base, dose, prior = inherited.base, inherited.dose, inherited.prior
OUT = ROOT / "results/quick-checks/check40h"
SEED, LIMIT, N = 40070, 1800, 24
ARMS = ("M", "Z", "Tprime")
STEPS = (
    "SET",
    "HOLD",
    "SWITCH",
    "HOLD_AFTER_SWITCH",
    "BACK",
    "HOLD_AFTER_BACK",
    "CLEAR",
)
SCORED, PREFIX = STEPS, STEPS[:2]
TARGET = {**inherited.TARGET, "HOLD_AFTER_BACK": "JavaScript"}
generation = inherited.generation
fork_session = inherited.fork_session


def write(name, value):
    base.write_json(OUT / name, value)


def projection(n):
    previous = json.loads((inherited.OUT / "summary.json").read_text())
    requests = n * 20  # fresh OFF + shared2 + two branches*5 + text7
    rows = [
        json.loads(s)
        for s in (inherited.OUT / "records.jsonl").read_text().splitlines()
    ]
    actual = [r for r in rows if "shared_from_generation" not in r]
    load = json.loads((inherited.OUT / "runtime.json").read_text())["load_seconds"]
    per_request = sum(r["seconds"] for r in actual) / len(actual)
    return dict(
        episodes=n,
        generations=requests,
        token_cap=64,
        capped_tokens=requests * 64,
        load_seconds=load,
        measured_seconds_per_request=per_request,
        reserve_factor=1.25,
        seconds=(load + requests * per_request) * 1.25,
        cap_seconds=LIMIT,
        basis=(
            "check40f measured load and generation seconds; "
            "estimate, not worst-case cap"
        ),
        reference_gpu_seconds=previous["gpu_seconds"],
    )


def reading(n):
    return f"""# Check40h — release closure, masks at every change

Unregistered descriptive quick check; frozen before generation, seed40070,
24 episodes, Qwen3-30B-A3B bf16, greedy, alpha3, 64-token caps. Fit/train-on:
none. Profile-on: frozen check40b's32 cued competence replies; alpha3 was
selected in exploratory40c and explicitly requested here. Evaluated-on: fresh
synthetic arithmetic expressions disjoint from40b/40d/40f; nothing fit or tuned,
no evaluation benchmarks or sealed inputs read.

SET(JS) -> HOLD -> SWITCH(Python) -> HOLD_AFTER_SWITCH -> BACK(JS) ->
HOLD_AFTER_BACK -> CLEAR(OFF, Python default). No extra NEUTRAL turn. Fresh OFF
on each CLEAR task precedes arms. M/Z share exact SET/HOLD KV and replies, then
branch; each branch keeps its own subsequent generations. Tprime denotes T′.
M: JS bias at SET/HOLD/BACK/HOLD_AFTER_BACK, Python at SWITCH/HOLD_AFTER_SWITCH,
OFF at CLEAR. Z: same as M except OFF at SWITCH/HOLD_AFTER_SWITCH; this is the
mask+OFF SWITCH control. T′: bias OFF throughout, explicit Use JavaScript/Python
on every corresponding non-CLEAR request. No cue or cancellation at CLEAR.
All three arms mask all earlier assistant code-turn bodies at SWITCH, BACK,
and CLEAR (including broken replies, fences included, EOS/headers excluded).
Masks persist, so each change adds every body produced since the last change.
At T′ CLEAR also mask ALL prior cue-bearing USER TURNS, including their request,
role header and closure/newline, retaining assistant headers and closures.
This conservative cue-turn interpretation removes every direct text cue carrier.
No placeholders, text-history rebuild, position renumbering or downstream KV
recomputation. Reuse40f's exact every-forward 2D key mask and absolute RoPE IDs;
masked KV columns remain allocated. Surviving downstream KV can carry traces.

Fixed reading: CLOSED-RELEASE iff M valid Python>=20/24 at SWITCH, valid
JavaScript>=20/24 at BACK, valid Python>=20/24 at CLEAR, broken<=2/24 at EVERY
step, AND >=20 paired episodes have BACK JS, HOLD_AFTER_BACK JS and CLEAR Python.
The paired condition conservatively operationalizes 'after real reestablished
JS': an aggregate default cannot substitute for actual release. PARTIAL iff
at least one of SWITCH/BACK/CLEAR meets its target>=20 and broken<=2 but the
full rule fails; otherwise NOT. INCOMPLETE takes precedence if unfinished.
Z and T′ are reported separately and never rescue M. If Z SWITCH Python>=20/24,
masking alone restores the DEFAULT: any need for a new routing term is confined
to the non-default direction (and that direction's success must be measured).
Report all per-step parser languages/breakage/coarse checks, paired transitions,
fence loss (bare among all and valid outputs), R3-style ambiguous expression
echoes, OK imitation, family/token/arrow diagnostics. Parsers/coarse checker
unchanged from40f; code not executed. This tests arithmetic surface syntax,
not autonomous skill maintenance or general release across tasks.

Cost: {projection(n)["generations"]} actual generations, {projection(n)["seconds"]:.2f}s
projection from40f measured per-request time and load plus25% reserve; estimated,
not a worst-case64-token guarantee. Cooperative cap1800s (0.5 GPU-h) includes
load, kernel checks and cleanup; no signals or outcome retries. Foreground only,
wait for other RUNNING.flags/compute, pid2705 exempt and never touched; require
>=68GiB available. Own RUNNING.flag removed on cleanup. Pinned .venv runtime,
raw slot0 contract on all48 gates, inherited grouped_mm/OFF and CPU mask tests.

Results PENDING.
"""


def session_new():
    return dict(masked=[], bodies=[], replacements={}, cue_turns=[])


def bias_for(arm, step, biases):
    if arm in ("Tprime", "fresh-OFF") or step == "CLEAR":
        return None
    if step in ("SWITCH", "HOLD_AFTER_SWITCH"):
        return None if arm == "Z" else biases["python"]
    return biases["js"]


def cue_for(arm, step):
    return TARGET[step] if arm == "Tprime" and step != "CLEAR" else None


def cue_span(tokenizer, messages, r):
    user = tokenizer.apply_chat_template(
        [messages[-1]],
        tokenize=True,
        return_dict=False,
        add_generation_prompt=False,
        enable_thinking=False,
    )
    ids = r["input_token_ids"]
    offsets = [
        i for i in range(len(ids) - len(user) + 1) if ids[i : i + len(user)] == user
    ]
    assert len(offsets) == 1, "Cue-bearing user turn must have one exact token span"
    start = len(r["cache_prefix_token_ids"]) + offsets[0]
    return [start, start + len(user)]


def mask_change(engine, session, arm, step, bias):
    if arm == "fresh-OFF" or step not in ("SWITCH", "BACK", "CLEAR"):
        return None
    event = inherited.mask_answers(engine, session, False, bias)
    cues = (
        copy.deepcopy(session["cue_turns"])
        if arm == "Tprime" and step == "CLEAR"
        else []
    )
    session["masked"] = sorted(
        set(session["masked"]) | {p for b, e in cues for p in range(b, e)}
    )
    event.update(cue_turns=cues, after=session["masked"])
    return event


def decision(arms, n, complete, paired):
    assert n == N
    if not complete:
        return "INCOMPLETE", {}
    cells = {
        s: arms["M"][s]["valid"].get(TARGET[s], 0) >= 20 and arms["M"][s]["broken"] <= 2
        for s in ("SWITCH", "BACK", "CLEAR")
    }
    passes = dict(
        cells,
        every_step_breakage=all(arms["M"][s]["broken"] <= 2 for s in STEPS),
        reestablished_js_release=paired >= 20,
    )
    return (
        "CLOSED-RELEASE"
        if all(passes.values())
        else "PARTIAL"
        if any(cells.values())
        else "NOT"
    ), passes


def summarize(rows, n, complete=False):
    arms = {
        a: {
            s: dose.aggregate([r for r in rows if r["arm"] == a and r["step"] == s])
            for s in STEPS
        }
        for a in ARMS
    }
    transitions, diagnostics, paired = {}, {}, {}
    for a in ARMS:
        bank = {(r["episode"], r["step"]): r for r in rows if r["arm"] == a}
        transitions[a], diagnostics[a] = {}, {}
        for left, right in zip(STEPS, STEPS[1:], strict=False):
            transitions[a][f"{left}->{right}"] = dict(
                Counter(
                    " -> ".join(
                        bank[e, s]["score"]["valid_language"] or "broken"
                        for s in (left, right)
                    )
                    for e in range(n)
                    if (e, left) in bank and (e, right) in bank
                )
            )
        paired[a] = sum(
            all(
                (e, s) in bank and bank[e, s]["score"]["valid_language"] == lang
                for s, lang in (
                    ("BACK", "JavaScript"),
                    ("HOLD_AFTER_BACK", "JavaScript"),
                    ("CLEAR", "Python"),
                )
            )
            for e in range(n)
        )
        for s in STEPS:
            rs = [r for r in bank.values() if r["step"] == s]
            diagnostics[a][s] = dict(
                bare=sum(r["fence_label"] == "(bare)" for r in rs),
                bare_valid=sum(
                    r["fence_label"] == "(bare)"
                    and r["score"]["valid_language"] is not None
                    for r in rs
                ),
                ambiguous_episodes=[
                    r["episode"] for r in rs if r["score"]["language"] == "ambiguous"
                ],
                expression_echo_episodes=[
                    r["episode"] for r in rs if r["expression_echo"]
                ],
                ok_episodes=[r["episode"] for r in rs if r["text"].strip() == "OK"],
            )
    verdict, passes = decision(arms, n, complete, paired["M"])
    actual = [r for r in rows if "shared_from_generation" not in r]
    return dict(
        reading=verdict,
        passes=passes,
        complete=complete,
        episodes=n,
        arms=arms,
        transitions=transitions,
        diagnostics=diagnostics,
        paired_reestablished_js_release=paired,
        z_default_restored=arms["Z"]["SWITCH"]["valid"].get("Python", 0) >= 20,
        records=len(rows),
        generations=len(actual),
        generated_tokens=sum(len(r["generated_token_ids"]) for r in actual),
        fresh_off=dose.aggregate([r for r in rows if r["arm"] == "fresh-OFF"]),
    )


def expression_echo(text, task):
    code = base.extract_code(text)[0]
    return "".join(code.split()).rstrip(";") == "".join(task["expression"].split())


def make_tasks(n):
    banks = json.loads((prior.OLD / "banks.json").read_text())
    used = {t["expression"] for bank in banks.values() for t in bank}
    used.update(
        t["expression"]
        for e in json.loads((prior.OUT / "tasks.json").read_text())
        for t in e.values()
    )
    used.update(
        t["expression"]
        for e in json.loads((inherited.OUT / "tasks.json").read_text())
        for t in e.values()
    )
    rng = random.Random(SEED)
    shapes = ("(({a}+{b})*({c}-{d}))", "(({a}*{b})+({c}*{d}))", "(({a}-{b})-({c}+{d}))")
    tasks = []
    for e in range(n):
        episode = {}
        for j, s in enumerate(SCORED):
            family = (e + j) % 3
            while True:
                expr = shapes[family].format(
                    **{c: rng.randrange(2, 40) for c in "abcd"}
                )
                if expr not in used:
                    break
            used.add(expr)
            name = f"solve_release_{e}_{j}"
            episode[s] = dict(
                id=name,
                name=name,
                expression=expr,
                family=f"screen_{family}",
                witness=r"[+*\-]",
                prompt=(
                    f"For the arithmetic expression {expr}, provide a solution. "
                    f"If writing a function, name it {name}."
                ),
            )
        tasks.append(episode)
    return tasks


def cpu_checks():
    import torch
    from transformers import AutoTokenizer, Qwen3MoeConfig, Qwen3MoeForCausalLM

    checks = inherited.cpu_checks()
    torch.manual_seed(SEED)
    tok = AutoTokenizer.from_pretrained(base.MODEL, local_files_only=True)
    cfg = Qwen3MoeConfig(
        vocab_size=len(tok),
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
    cfg._attn_implementation = "sdpa"
    engine = base.Engine.__new__(base.Engine)
    engine.model = Qwen3MoeForCausalLM(cfg).eval()
    engine.torch, engine.device, engine.tokenizer = torch, torch.device("cpu"), tok
    engine.deadline, engine.eos = time.monotonic() + 300, set()
    engine.hooks = base.RouterHooks(
        [layer.mlp.gate for layer in engine.model.model.layers]
    )
    biases = dict(js=torch.tensor([[0.0, 0.0, 0.0, 10.0]] * 2))
    biases["python"] = -biases["js"]
    tasks = make_tasks(N)
    for a in ARMS:
        session, history = session_new(), None
        for s in STEPS:
            bias = bias_for(a, s, biases)
            before_tokens = list(session.get("token_ids", []))
            event = mask_change(engine, session, a, s, bias)
            if s in ("SWITCH", "BACK", "CLEAR"):
                assert len(event["bodies"]) == {"SWITCH": 2, "BACK": 4, "CLEAR": 6}[s]
                expected = {p for b, e in session["bodies"] for p in range(b, e)}
                if a == "Tprime" and s == "CLEAR":
                    assert len(event["cue_turns"]) == 6
                    expected.update(
                        p for b, e in session["cue_turns"] for p in range(b, e)
                    )
                else:
                    assert event["cue_turns"] == []
                assert event["after"] == sorted(expected)
                assert before_tokens == session["token_ids"]
                if a == "Tprime" and s == "CLEAR":
                    # Exercise combined cue+answer mask through real SDPA, including
                    # a nonvacuous corrupted-KV invariance check before CLEAR.
                    def logits(state, mask):
                        kwargs = dict(
                            input_ids=torch.tensor([[7, 8]]),
                            past_key_values=inherited.clone_cache(state["past"]),
                            use_cache=True,
                        )
                        inherited.mask_kwargs(torch, kwargs, mask)
                        with torch.inference_mode():
                            return engine.model(**kwargs).logits

                    expected_logits = logits(session, session["masked"])
                    poison = fork_session(session)
                    for layer in poison["past"].layers:
                        layer.keys[:, :, session["masked"]] = 1e4
                        layer.values[:, :, session["masked"]] = -1e4
                    assert torch.equal(
                        expected_logits, logits(poison, session["masked"])
                    )
                    assert not torch.equal(expected_logits, logits(session, []))
            else:
                assert event is None
            messages = base.messages_for(tasks[0][s], cue_for(a, s), history)
            r = generation(engine, messages, bias, session, cap=2)
            assert all(
                t["masked"] == session["masked"] for t in r["mask_forward_trace"]
            )
            assert r["bias_sha256"] == prior.digest_bias(bias)
            begin = len(r["cache_prefix_token_ids"]) + len(r["input_token_ids"])
            session["bodies"].append(
                [begin, begin + len(r["generated_token_ids"]) - int(r["eos"])]
            )
            if cue_for(a, s):
                span = cue_span(tok, messages, r)
                assert "Use " + TARGET[s] + "." in tok.decode(
                    session["token_ids"][span[0] : span[1]]
                )
                assert span[1] < begin  # assistant generation header survives
                session["cue_turns"].append(span)
            history = messages + [dict(role="assistant", content=r["text"])]
    engine.hooks.close()
    arms = {a: {s: dict(valid={TARGET[s]: 20}, broken=2) for s in STEPS} for a in ARMS}
    assert decision(arms, N, True, 20)[0] == "CLOSED-RELEASE"
    assert decision(arms, N, True, 19)[0] == "PARTIAL"
    arms["M"]["HOLD_AFTER_BACK"]["broken"] = 3
    assert decision(arms, N, True, 20)[0] == "PARTIAL"
    for s in ("SWITCH", "BACK", "CLEAR"):
        arms["M"][s]["valid"] = {TARGET[s]: 19}
    assert decision(arms, N, True, 20)[0] == "NOT"
    assert decision(arms, N, False, 20)[0] == "INCOMPLETE"
    assert not torch.cuda.is_initialized()
    return dict(
        inherited=checks,
        every_change_mask_schedule=True,
        full_cue_turn_spans=True,
        combined_mask_real_sdpa_invariance=True,
        combined_mask_nonvacuous=True,
        exact_bias_schedule=True,
        paired_and_breakage_verdict_boundaries=True,
        cuda_initialized=False,
    )


def prepare():
    import torch

    assert not (OUT / "records.jsonl").exists(), "No outcome overwrite"
    n = N
    assert projection(n)["seconds"] < LIMIT
    checks = cpu_checks()
    write("cpu.json", checks)
    write("tasks.json", make_tasks(n))
    write(
        "projection.json",
        dict(selected=projection(n)),
    )
    frozen = torch.load(
        prior.OLD / "frozen-biases.pt", map_location="cpu", weights_only=True
    )
    biases = dict(js=frozen["correct"] * 0.75, python=frozen["swapped"] * 0.75)
    old = torch.load(prior.OUT / "biases.pt", map_location="cpu", weights_only=True)
    assert all(torch.equal(biases[k], old[k]) for k in biases)
    torch.save(biases, OUT / "biases.pt")
    (OUT / "prewritten-reading.md").write_text(reading(n))
    (OUT / "README.md").write_text(reading(n))
    paths = [
        Path(__file__),
        *(
            ROOT / f"scripts/focus_check{s}.py"
            for s in ("40", "40b", "40c", "40d", "40f")
        ),
        *(
            OUT / name
            for name in (
                "prewritten-reading.md",
                "tasks.json",
                "projection.json",
                "biases.pt",
            )
        ),
        inherited.OUT / "tasks.json",
        inherited.OUT / "summary.json",
        inherited.OUT / "records.jsonl",
        inherited.OUT / "runtime.json",
        prior.OLD / "frozen-biases.pt",
        prior.OLD / "banks.json",
        prior.OUT / "tasks.json",
        prior.OUT / "biases.pt",
    ]
    write(
        "freeze.json",
        dict(
            utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            runtime=dose.runtime(),
            files={str(p): base.sha(p) for p in paths},
        ),
    )
    print(json.dumps(dict(cpu=checks, projection=projection(n))), flush=True)


def verify_freeze():
    for path, digest in json.loads((OUT / "freeze.json").read_text())["files"].items():
        assert base.sha(Path(path)) == digest, path


def run():
    import torch

    verify_freeze()
    dose.runtime()
    assert not (OUT / "records.jsonl").exists(), "No retries or overwrite"
    with (ROOT / ".review.lock").open("a") as lock:
        while True:
            resource = prior.resources()
            if resource["ready"]:
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    resource["review_lock_busy"] = True
                else:
                    resource = prior.resources()
                    if resource["ready"]:
                        break
                    fcntl.flock(lock, fcntl.LOCK_UN)
            print(json.dumps(dict(status="WAIT", **resource)), flush=True)
            time.sleep(45)
        verify_freeze()
        write("resources.json", resource)
        flag = OUT / "RUNNING.flag"
        with flag.open("x") as stream:
            stream.write(json.dumps(dict(pid=os.getpid(), check="40h")) + "\n")
        tasks = json.loads((OUT / "tasks.json").read_text())
        biases = torch.load(OUT / "biases.pt", map_location="cpu", weights_only=True)
        rows, engine, session, shared = [], None, None, None
        start = time.monotonic()
        base.GPU_SECONDS, base.SEED = LIMIT, SEED
        complete, reason = False, "interrupted"
        journal = (OUT / "records.jsonl").open("x")

        def append(r):
            r["id"] = len(rows)
            journal.write(json.dumps(r) + "\n")
            journal.flush()
            rows.append(r)
            print(
                json.dumps(
                    dict(
                        n=len(rows),
                        generation=r["generation"],
                        episode=r["episode"],
                        arm=r["arm"],
                        step=r["step"],
                        language=r["score"]["valid_language"],
                        elapsed=time.monotonic() - start,
                    )
                ),
                flush=True,
            )

        def request(e, arm, step, history, session):
            task = prior.NEUTRAL if step == "NEUTRAL" else tasks[e][step]
            bias = bias_for(arm, step, biases)
            event = mask_change(engine, session, arm, step, bias)
            messages = base.messages_for(task, cue_for(arm, step), history)
            r = generation(engine, messages, bias, session)
            r.update(
                generation=sum("shared_from_generation" not in row for row in rows),
                episode=e,
                arm=arm,
                step=step,
                task_id=task["id"],
                family=task.get("family", "neutral"),
                target=TARGET[step],
                cue=cue_for(arm, step),
                expression_echo=expression_echo(r["text"], task),
                alpha=3 if bias is not None else 0,
                mask_event=event,
                score=base.score(r["text"], task, r["truncated"]),
            )
            r.update(dose.report_fields(r, engine.tokenizer))
            assert r["bias_sha256"] == prior.digest_bias(bias)
            if session is not None and step != "NEUTRAL":
                begin = len(r["cache_prefix_token_ids"]) + len(r["input_token_ids"])
                end = begin + len(r["generated_token_ids"]) - int(r["eos"])
                assert begin < end, "Empty answer body; invalid masking run"
                session["bodies"].append([begin, end])
            r["cue_turn_span"] = (
                cue_span(engine.tokenizer, messages, r) if cue_for(arm, step) else None
            )
            if r["cue_turn_span"] is not None:
                session["cue_turns"].append(r["cue_turn_span"])
            append(r)
            if r["cost_stopped"]:
                raise base.BudgetStop("cooperative token budget")
            return messages + [dict(role="assistant", content=r["text"])]

        try:
            engine = base.Engine(start)
            write(
                "runtime.json",
                dict(
                    dose.runtime(),
                    load_seconds=engine.load_seconds,
                    raw_slot_verified_layers=sum(
                        dose.raw_contract(g) for g in engine.hooks.gates
                    ),
                ),
            )
            kernel = engine.verify_kernel()
            write("kernel.json", kernel)
            assert kernel["adopted"]
            for e in range(len(tasks)):
                request(e, "fresh-OFF", "CLEAR", None, None)
                history, shared = None, session_new()
                offset = len(rows)
                for step in PREFIX:
                    history = request(e, "M", step, history, shared)
                prefix_rows = rows[offset:]
                for arm in ARMS[:2]:
                    session, branch = fork_session(shared), copy.deepcopy(history)
                    if arm != "M":
                        for source in prefix_rows:
                            row = copy.deepcopy(source)
                            row.update(
                                arm=arm, shared_from_generation=source["generation"]
                            )
                            append(row)
                    for step in STEPS[2:]:
                        branch = request(e, arm, step, branch, session)
                    session = None
                shared = None
                session, history = session_new(), None
                for step in STEPS:
                    history = request(e, "Tprime", step, history, session)
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
            result.update(reason=reason, cap_seconds=LIMIT)
            session, shared = None, None
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
            print(
                json.dumps(
                    {k: result[k] for k in ("reading", "reason", "gpu_seconds")}
                ),
                flush=True,
            )


def audit():
    import torch
    from transformers import AutoTokenizer

    verify_freeze()
    tokenizer = AutoTokenizer.from_pretrained(base.MODEL, local_files_only=True)
    tasks = json.loads((OUT / "tasks.json").read_text())
    assert tasks == make_tasks(len(tasks))
    rows = [
        json.loads(line) for line in (OUT / "records.jsonl").read_text().splitlines()
    ]
    biases = torch.load(OUT / "biases.pt", map_location="cpu", weights_only=True)
    histories, sessions, generations = {}, {}, {}
    for i, r in enumerate(rows):
        assert r["id"] == i
        e, a, s = r["episode"], r["arm"], r["step"]
        key = e, a
        state = sessions.setdefault(
            key, dict(tokens=[], bodies=[], masked=[], replacements={}, cue_turns=[])
        )
        task = prior.NEUTRAL if s == "NEUTRAL" else tasks[e][s]
        messages = base.messages_for(task, cue_for(a, s), histories.get(key))
        assert r["history"] == messages
        assert r["score"] == base.score(r["text"], task, r["truncated"])
        assert r["expression_echo"] == expression_echo(r["text"], task)
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
        assert r["rendered_input_token_ids"] == rendered
        ids = (
            rendered
            if not state["tokens"]
            else tokenizer.encode("\n", add_special_tokens=False)
            + tokenizer.apply_chat_template(
                [messages[-1]],
                tokenize=True,
                return_dict=False,
                add_generation_prompt=True,
                enable_thinking=False,
            )
        )
        assert (
            r["input_token_ids"] == ids
            and r["cache_prefix_token_ids"] == state["tokens"]
        )
        assert (
            r["cache_prefix_sha256"]
            == hashlib.sha256(json.dumps(state["tokens"]).encode()).hexdigest()
        )
        assert r["bias_sha256"] == prior.digest_bias(bias_for(a, s, biases))
        event = r["mask_event"]
        if a in ARMS and s in ("SWITCH", "BACK", "CLEAR"):
            assert (
                event["bodies"] == state["bodies"]
                and event["before"] == state["masked"]
            )
            assert event["absolute_length"] == len(state["tokens"])
            masked = set(state["masked"]) | {
                p for b, end in state["bodies"] for p in range(b, end)
            }
            assert not event["placeholders"]
            cues = state["cue_turns"] if a == "Tprime" and s == "CLEAR" else []
            assert event["cue_turns"] == cues
            masked.update(p for b, end in cues for p in range(b, end))
            state["masked"] = sorted(masked)
            assert event["after"] == state["masked"]
        else:
            assert event is None
        assert r["masked_positions"] == state["masked"]
        assert r["placeholder_token_ids_by_position"] == state["replacements"]
        trace = r["mask_forward_trace"]
        position = len(state["tokens"])
        lengths = [len(ids)] + [1] * (
            len(r["generated_token_ids"]) + len(r["appended_terminal_token_ids"])
        )
        if a == "fresh-OFF":
            lengths = (
                lengths[:-1]
                if r["eos"] or len(r["generated_token_ids"]) == 64
                else lengths
            )
        assert [t["length"] for t in trace] == lengths
        for t in trace:
            assert t == dict(start=position, length=t["length"], masked=state["masked"])
            position += t["length"]
        if "shared_from_generation" in r:
            source = generations[r["shared_from_generation"]]
            assert {
                k: v
                for k, v in r.items()
                if k not in ("id", "arm", "shared_from_generation")
            } == {k: v for k, v in source.items() if k not in ("id", "arm")}
        else:
            assert r["generation"] == len(generations)
            generations[r["generation"]] = r
        expected_cue_span = cue_span(tokenizer, messages, r) if cue_for(a, s) else None
        assert r["cue_turn_span"] == expected_cue_span
        if expected_cue_span is not None:
            state["cue_turns"].append(expected_cue_span)
        if a != "fresh-OFF":
            begin = len(state["tokens"]) + len(ids)
            if s != "NEUTRAL":
                state["bodies"].append(
                    [begin, begin + len(r["generated_token_ids"]) - int(r["eos"])]
                )
            state["tokens"] += (
                ids + r["generated_token_ids"] + r["appended_terminal_token_ids"]
            )
            histories[key] = messages + [dict(role="assistant", content=r["text"])]
    summary = json.loads((OUT / "summary.json").read_text())
    rebuilt = summarize(rows, len(tasks), summary["complete"])
    assert all(summary[k] == v for k, v in rebuilt.items())
    if summary["complete"]:
        assert len(rows) == len(tasks) * 22
        assert len(generations) == projection(len(tasks))["generations"]
        assert all(
            arms[s]["n"] == len(tasks)
            for arms in summary["arms"].values()
            for s in STEPS
        )
    assert not torch.cuda.is_initialized()
    result = dict(
        records=len(rows),
        generations=len(generations),
        scores_and_tokens=True,
        histories_and_absolute_positions=True,
        mask_events_and_every_forward=True,
        cue_turn_positions_and_context=True,
        shared_prefix_exact=True,
        bias_schedule=True,
        fresh_disjoint_tasks=True,
        summary_reading=True,
        freeze=True,
    )
    write("audit.json", result)
    print(json.dumps(result), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("prepare", "run", "audit", "test", "resources"),
        required=True,
    )
    args = parser.parse_args()
    if args.mode == "resources":
        print(json.dumps(prior.resources()))
    elif args.mode == "test":
        print(json.dumps(cpu_checks()))
    else:
        globals()[args.mode]()


if __name__ == "__main__":
    main()
