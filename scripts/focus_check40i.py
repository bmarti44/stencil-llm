#!/usr/bin/env python3
"""Check40i: fresh-seed primary Z closure, reusing frozen check40h machinery."""

from __future__ import annotations

import argparse
import copy
import fcntl
import gc
import hashlib
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import focus_check40h as h  # noqa: E402

base, dose, prior, inherited = h.base, h.dose, h.prior, h.inherited
OUT = ROOT / "results/quick-checks/check40i"
SEED, LIMIT, N = 40080, 1800, 24
ARMS = ("Z", "Zc", "S", "OFF")
STEPS, TARGET = h.STEPS, h.TARGET
PREFIX = STEPS[:4]
generation, fork_session = h.generation, h.fork_session
session_new, expression_echo, cue_span = h.session_new, h.expression_echo, h.cue_span


def write(name, value):
    base.write_json(OUT / name, value)


def bias_for(arm, step, biases):
    if arm == "OFF" or step in ("SWITCH", "HOLD_AFTER_SWITCH", "CLEAR"):
        return None
    if step in ("BACK", "HOLD_AFTER_BACK"):
        return {"Z": biases["js"], "Zc": None, "S": biases["shuffled"]}[arm]
    return biases["js"]


def cue_for(arm, step):
    return None


def mask_change(engine, session, arm, step, bias):
    return None if arm == "OFF" else h.mask_change(engine, session, arm, step, bias)


def projection(n):
    old = json.loads((h.OUT / "summary.json").read_text())
    return dict(
        episodes=n,
        generations=n * 20,
        token_cap=64,
        seconds=old["gpu_seconds"] * 1.25,
        cap_seconds=LIMIT,
        basis=(
            "40h same 480 generations incl load/cleanup, plus25% reserve; "
            "estimate, not worst-case guarantee"
        ),
    )


def reading(n):
    return f"""# Check40i — Z primary release closure

Unregistered, disclosed descriptive quick check; seed40080,24 fresh episodes,
Qwen3-30B-A3B bf16,greedy,alpha3,64-token caps. Fit/train-on:none.
Profile-on:frozen40b competence replies; alpha3 from exploratory40c, requested
here without tuning. Evaluated-on:fresh synthetic arithmetic expressions,
disjoint from40b/40d/40f/40h. No benchmarks or sealed inputs read.

Fixed BEFORE inference: Z PRIMARY SET(JS bias) -> HOLD -> SWITCH(bias OFF +
mask) -> HOLD_AFTER_SWITCH -> BACK(JS bias + mask) -> HOLD_AFTER_BACK ->
CLEAR(bias OFF + mask). Zc and S share Z's exact first4 replies and KV, then
branch: Zc BACK/HOLD_AFTER_BACK bias OFF; S BACK/HOLD_AFTER_BACK frozen40b
shuffled JS direction scaled to alpha3. Both mask at BACK and CLEAR; both
bias OFF at CLEAR. OFF:no bias or mask, full7-step retained-history arm.
No text cues, NEUTRAL turn, or extra fresh-OFF generation. 672 logical records,
480 actual generations. Each branch retains its own subsequent answers.

Masks reuse40h/40f position-preserving key eviction of ALL previous assistant
code-turn bodies at SWITCH/BACK/CLEAR, including fences and broken replies,
excluding EOS/headers. Persistent masks apply at every forward; no placeholders,
KV recomputation or position renumbering. Surviving downstream KV may carry traces.

Fixed reading:CLOSED-RELEASE iff Z Python>=20/24 at SWITCH, JS>=20/24 at BACK,
Python>=20/24 at CLEAR; Z broken<=2/24 at EVERY step; Zc JS<=4/24 and S JS<=4/24
at BACK. Paired real releases additionally require>=20 episodes with SET JS +
HOLD JS + SWITCH Python and>=20 with BACK JS + HOLD_AFTER_BACK JS + CLEAR Python.
This conservatively fixes the user's paired-real-releases requirement.
PARTIAL iff any primary SWITCH/BACK/CLEAR target>=20 and broken<=2 but the full
conjunction fails; NOT otherwise. INCOMPLETE takes precedence if unfinished.
Controls are reported in full; primary breakage bar applies to Z.
Report fences/bare valid replies, missing-closing-parenthesis defects (broken
code with positive '(' minus ')' balance), other parser breaks, coarse checks,
paired counts and cost. No scorer change; coarse checks do not execute code.

Projected cost:{projection(n)["seconds"]:.2f}s from40h; cooperative cap1800s
(0.5 GPU-h) includes load/kernel checks/cleanup, with request/token reserves.
Foreground only; wait for any other Stencil flag/compute process; Brian pid2705
exempt and never touched. No signals, retries, fitting, background launch or push.
Claim limited to arithmetic language surface syntax under this schedule;
HOLD with current bias and visible own answers does not isolate maintenance.
Prior negated-JS bias is not used; no claim about independently profiled Python.

Results PENDING.
"""


def make_tasks(n):
    # Preserve the40h generator exactly, changing only seed and disjointness.
    previous = h.SEED
    h.SEED = SEED
    try:
        tasks = h.make_tasks(n)
    finally:
        h.SEED = previous
    old = {
        t["expression"]
        for e in json.loads((h.OUT / "tasks.json").read_text())
        for t in e.values()
    }
    fresh = [t["expression"] for e in tasks for t in e.values()]
    assert len(set(fresh)) == n * 7 and not old.intersection(fresh)
    return tasks


def decision(arms, n, complete, paired, switched):
    assert n == N
    if not complete:
        return "INCOMPLETE", {}
    cells = {
        s: arms["Z"][s]["valid"].get(TARGET[s], 0) >= 20 and arms["Z"][s]["broken"] <= 2
        for s in ("SWITCH", "BACK", "CLEAR")
    }
    passes = dict(
        cells,
        every_step_breakage=all(arms["Z"][s]["broken"] <= 2 for s in STEPS),
        paired_switch_release=switched >= 20,
        paired_clear_release=paired >= 20,
        Zc_back_control=arms["Zc"]["BACK"]["valid"].get("JavaScript", 0) <= 4,
        S_back_control=arms["S"]["BACK"]["valid"].get("JavaScript", 0) <= 4,
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
    paired, switched, diagnostics, transitions = {}, {}, {}, {}
    for a in ARMS:
        bank = {(r["episode"], r["step"]): r for r in rows if r["arm"] == a}

        def pairs(sequence, bank=bank):
            return sum(
                all(
                    (e, s) in bank and bank[e, s]["score"]["valid_language"] == lang
                    for s, lang in sequence
                )
                for e in range(n)
            )

        paired[a] = pairs(
            (
                ("BACK", "JavaScript"),
                ("HOLD_AFTER_BACK", "JavaScript"),
                ("CLEAR", "Python"),
            )
        )
        switched[a] = pairs(
            (("SET", "JavaScript"), ("HOLD", "JavaScript"), ("SWITCH", "Python"))
        )
        transitions[a] = {
            f"{left}->{right}": dict(
                Counter(
                    " -> ".join(
                        bank[e, s]["score"]["valid_language"] or "broken"
                        for s in (left, right)
                    )
                    for e in range(n)
                    if (e, left) in bank and (e, right) in bank
                )
            )
            for left, right in zip(STEPS, STEPS[1:], strict=False)
        }
        diagnostics[a] = {}
        for s in STEPS:
            cell = [r for r in bank.values() if r["step"] == s]
            diagnostics[a][s] = dict(
                fenced=sum(r["fence_label"] != "(bare)" for r in cell),
                bare=sum(r["fence_label"] == "(bare)" for r in cell),
                bare_valid=sum(
                    r["fence_label"] == "(bare)"
                    and r["score"]["valid_language"] is not None
                    for r in cell
                ),
                missing_paren_episodes=[
                    r["episode"]
                    for r in cell
                    if r["score"]["broken"]
                    and base.extract_code(r["text"])[0].count("(")
                    > base.extract_code(r["text"])[0].count(")")
                ],
                ambiguous_episodes=[
                    r["episode"] for r in cell if r["score"]["language"] == "ambiguous"
                ],
                expression_echo_episodes=[
                    r["episode"] for r in cell if r["expression_echo"]
                ],
                ok_episodes=[r["episode"] for r in cell if r["text"].strip() == "OK"],
            )
    verdict, passes = decision(arms, n, complete, paired["Z"], switched["Z"])
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
        paired_switch_release=switched,
        records=len(rows),
        generations=len(actual),
        generated_tokens=sum(len(r["generated_token_ids"]) for r in actual),
    )


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
    biases["shuffled"] = biases["js"].roll(1, dims=-1)
    tasks = make_tasks(N)
    for a in ARMS:
        session, history = session_new(), None
        for s in STEPS:
            bias = bias_for(a, s, biases)
            before_tokens = list(session.get("token_ids", []))
            event = mask_change(engine, session, a, s, bias)
            if a != "OFF" and s in ("SWITCH", "BACK", "CLEAR"):
                assert len(event["bodies"]) == {"SWITCH": 2, "BACK": 4, "CLEAR": 6}[s]
                expected = {p for b, e in session["bodies"] for p in range(b, e)}
                assert event["cue_turns"] == []
                assert event["after"] == sorted(expected)
                assert before_tokens == session["token_ids"]
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
    for a in ("Zc", "S"):
        arms[a]["BACK"]["valid"] = {"JavaScript": 4}
    assert decision(arms, N, True, 20, 20)[0] == "CLOSED-RELEASE"
    for paired, switched in ((19, 20), (20, 19)):
        assert decision(arms, N, True, paired, switched)[0] == "PARTIAL"
    for arm in ("Zc", "S"):
        arms[arm]["BACK"]["valid"]["JavaScript"] = 5
        assert decision(arms, N, True, 20, 20)[0] == "PARTIAL"
        arms[arm]["BACK"]["valid"]["JavaScript"] = 4
    arms["Z"]["HOLD_AFTER_BACK"]["broken"] = 3
    assert decision(arms, N, True, 20, 20)[0] == "PARTIAL"
    for s in ("SWITCH", "BACK", "CLEAR"):
        arms["Z"][s]["valid"] = {TARGET[s]: 19}
    assert decision(arms, N, True, 20, 20)[0] == "NOT"
    assert decision(arms, N, False, 20, 20)[0] == "INCOMPLETE"
    assert not torch.cuda.is_initialized()
    return dict(
        inherited=checks,
        every_change_mask_schedule=True,
        off_never_masked=True,
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
    biases = dict(js=frozen["correct"] * 0.75, shuffled=frozen["shuffled"] * 0.75)
    old = torch.load(prior.OUT / "biases.pt", map_location="cpu", weights_only=True)
    assert torch.equal(biases["js"], old["js"])
    assert torch.allclose(biases["js"].norm(dim=-1), biases["shuffled"].norm(dim=-1))
    torch.save(biases, OUT / "biases.pt")
    (OUT / "prewritten-reading.md").write_text(reading(n))
    (OUT / "README.md").write_text(reading(n))
    paths = [
        Path(__file__),
        *(
            ROOT / f"scripts/focus_check{s}.py"
            for s in ("40", "40b", "40c", "40d", "40f", "40h")
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
        h.OUT / "tasks.json",
        h.OUT / "summary.json",
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
            stream.write(json.dumps(dict(pid=os.getpid(), check="40i")) + "\n")
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
                history, shared = None, session_new()
                offset = len(rows)
                for step in PREFIX:
                    history = request(e, "Z", step, history, shared)
                prefix_rows = rows[offset:]
                for arm in ARMS[:3]:
                    session, branch = fork_session(shared), copy.deepcopy(history)
                    if arm != "Z":
                        for source in prefix_rows:
                            row = copy.deepcopy(source)
                            row.update(
                                arm=arm, shared_from_generation=source["generation"]
                            )
                            append(row)
                    for step in STEPS[4:]:
                        branch = request(e, arm, step, branch, session)
                    session = None
                shared = None
                session, history = session_new(), None
                for step in STEPS:
                    history = request(e, "OFF", step, history, session)
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
        if a != "OFF" and s in ("SWITCH", "BACK", "CLEAR"):
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
        assert len(rows) == len(tasks) * 28
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
