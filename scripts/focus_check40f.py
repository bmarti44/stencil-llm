#!/usr/bin/env python3
"""Disclosed 40f: frozen router release with position-preserving answer masking."""

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
import focus_check40 as base  # noqa: E402
import focus_check40c as dose  # noqa: E402
import focus_check40d as prior  # noqa: E402

OUT = ROOT / "results/quick-checks/check40f"
SEED, LIMIT = 40060, 5400
ARMS = ("R1", "R2", "R3", "R4", "T")
STEPS = ("SET", "NEUTRAL", "HOLD", "SWITCH", "HOLD_AFTER_SWITCH", "BACK", "CLEAR")
SCORED = tuple(s for s in STEPS if s != "NEUTRAL")
PREFIX = STEPS[:3]
TARGET = {**prior.TARGET, "HOLD_AFTER_SWITCH": "Python"}


def write(name, value):
    base.write_json(OUT / name, value)


def projection(n):
    # Three shared prefix requests + 4*4 continuations + 7 text + fresh OFF.
    requests = 27 * n
    placeholders = 5 * n  # two old code bodies at SWITCH, three new at CLEAR.
    seconds = (393.89 + requests * (64 / 15 + 1) + placeholders * 2) * 1.25
    return dict(
        episodes=n,
        generations=requests,
        token_cap=64,
        capped_tokens=requests * 64,
        tokens_per_second=15,
        load_seconds=393.89,
        prefill_seconds_per_request=1,
        placeholder_forwards=placeholders,
        seconds_per_placeholder=2,
        reserve_factor=1.25,
        seconds=seconds,
        cap_seconds=LIMIT,
    )


def reading(n):
    return f"""# Check 40f — RELEASE: router bias + prior-answer masking

Unregistered, disclosed. Fixed before generation, seed40060, Qwen3-30B-A3B bf16,
greedy, alpha3, cap64. Fit/train-on: none. Frozen directions from check40b's32
cued competence replies, alpha3 selected in exploratory40c then explicitly
requested here. Evaluated-on: {n} new synthetic episodes, same three arithmetic
families, expressions disjoint from40b/40d. No benchmarks or sealed inputs.

Schedule: SET(JS) -> NEUTRAL(OK) -> HOLD(JS) -> SWITCH(Python) ->
HOLD_AFTER_SWITCH(Python sustained) -> BACK(JS) -> CLEAR(OFF). Code prompts
are distinct and uncued except T. BACK ensures CLEAR starts after renewed JS.
R1-R4 share one actual generated SET/NEUTRAL/HOLD prefix, then branch exact
copies of its KV and text. Each continuation retains its own generated history.
Fresh OFF on the CLEAR task precedes the arms. Shared prefix rows identify their
source generation; shared generations are counted once in cost.

R1: bias changes only. R2: bias changes + mask ALL prior assistant code bodies
at SWITCH and again at CLEAR. R3: same masks, JS bias unchanged throughout.
R4: R2 plus a one-line neutral `.` body in each masked answer's original first
body position. T: bias OFF; Use JavaScript at SET/HOLD/BACK, Use Python at
SWITCH/HOLD_AFTER_SWITCH; uncued NEUTRAL/CLEAR; same mask events as R2.
Masks persist after each event; later answers remain visible until next event.
Assistant code body means generated tokens on code-request turns, excluding EOS;
keep all user/system tokens, assistant headers/empty think prefix, turn closures
and neutral pairs, even if code was broken. Nothing removed from text history.

Mask implementation: 2D key attention mask at every prefill/decode/closure,
zeros for those exact absolute positions. Full KV columns and absolute RoPE
positions remain. Old downstream KV is NOT recomputed and may carry traces of
masked answers. R4 forwards `.` at the body's original first position using its
surviving causal prefix and current bias, replaces only that KV column, masks
the rest of the body; literal history and original token provenance retained.
Previously inserted placeholders survive subsequent events; no cue in them.
No history rebuild, position renumbering, learned value, tuning or outcome retry.

Fixed reading: RELEASE WORKS iff the SAME R2 or R4 has valid unbroken Python
>=26/32 at BOTH SWITCH/CLEAR, <=2/32 broken at both, and R3 valid Python <=4/32
at BOTH events. PARTIAL iff at least one event passes in R2/R4 with its R3
control and breakage bars, but no arm passes both. Else NOT. INCOMPLETE takes
precedence if execution unfinished. For selected24, conservative equivalents:
Python>=20/24, broken<=1/24, R3<=3/24. HOLD_AFTER_SWITCH reported separately.
Also report SET/HOLD/BACK success, actual JS->Python paired transitions, fresh
OFF defaults, all parser/coarse/family/first-token/fence/arrow diagnostics.
These thresholds are descriptive, not a registered existence test. Release
requires masking in addition to routing only if combined arms meet bars while
R1 fails; R3 reports whether masking alone suffices under sustained JS bias.
If JS was not induced/reestablished, distinguish defaults from actual release.

Cost: select{n} before outcomes. 32 capped projection{projection(32)["seconds"]:.2f}s;
24 capped projection{projection(24)["seconds"]:.2f}s. {projection(n)["generations"]}
generations, cap64, 15tok/s, load393.89s (40d), 1s/request prefill, 2s per
placeholder forward, 25% reserve; total{projection(n)["seconds"]:.2f}s <5400s.
Cooperative deadline including load/kernel/cleanup; no signals. Foreground;
review-lock/other RUNNING.flag/GPU check, pid2705 exempt, >=68GiB MemAvailable.
Commit recipe before GPU run; pin .venv transformers5.16.1, raw slot0 contract
all48 gates, inherited grouped_mm dispatch/OFF test, CPU real mask consumer test.

Results PENDING.
"""


def make_tasks(n):
    banks = json.loads((prior.OLD / "banks.json").read_text())
    used = {t["expression"] for bank in banks.values() for t in bank}
    used.update(
        t["expression"]
        for e in json.loads((prior.OUT / "tasks.json").read_text())
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


def bias_for(arm, step, biases):
    if arm in ("T", "fresh-OFF") or (step == "CLEAR" and arm != "R3"):
        return None
    return biases[
        "python" if step in ("SWITCH", "HOLD_AFTER_SWITCH") and arm != "R3" else "js"
    ]


def cue_for(arm, step):
    return TARGET[step] if arm == "T" and step not in ("NEUTRAL", "CLEAR") else None


def session_new():
    return dict(masked=[], bodies=[], replacements={})


def clone_cache(cache, end=None):
    # DynamicLayer.update concatenates; these independent layer objects never
    # mutate original tensors. Clone explicitly to make branch ownership clear.
    result = copy.copy(cache)
    result.layers = []
    for layer in cache.layers:
        new = copy.copy(layer)
        new.keys = layer.keys[:, :, :end].clone()
        new.values = layer.values[:, :, :end].clone()
        result.layers.append(new)
    return result


def fork_session(session):
    result = copy.deepcopy({k: v for k, v in session.items() if k != "past"})
    result["past"] = clone_cache(session["past"])
    return result


def mask_kwargs(torch, kwargs, masked):
    past = kwargs.get("past_key_values")
    start = past.get_seq_length() if past is not None else 0
    length = kwargs["input_ids"].shape[1]
    device = kwargs["input_ids"].device
    mask = torch.ones((1, start + length), dtype=torch.long, device=device)
    drops = sorted(p for p in masked if p < start + length)
    if drops:
        mask[0, drops] = 0
    kwargs["attention_mask"] = mask
    kwargs["position_ids"] = torch.arange(start, start + length, device=device)[None]
    return dict(start=start, length=length, masked=drops)


def generation(engine, messages, bias, session, cap=64):
    trace = []
    masked = session["masked"] if session is not None else []

    def inject(model, args, kwargs):
        trace.append(mask_kwargs(engine.torch, kwargs, masked))
        return args, kwargs

    handle = engine.model.register_forward_pre_hook(inject, with_kwargs=True)
    try:
        row, _ = engine.generate(messages, bias=bias, session=session, cap=cap)
    finally:
        handle.remove()
    row["mask_forward_trace"] = trace
    row["masked_positions"] = list(masked)
    row["placeholder_token_ids_by_position"] = (
        dict(session["replacements"]) if session else {}
    )
    return row


def mask_answers(engine, session, placeholder, bias):
    torch = engine.torch
    spans = session["bodies"]
    assert spans and all(start < end for start, end in spans), "Vacuous mask"
    before = list(session["masked"])
    replacements = session["replacements"]
    masked = set(before)
    for start, end in spans:
        masked.update(range(start, end))
    masked.difference_update(int(p) for p in replacements)
    new_replacements = []
    cache = session["past"]
    original_length = cache.get_seq_length()
    if placeholder:
        tokens = engine.tokenizer.encode(".", add_special_tokens=False)
        assert len(tokens) == 1, "One original body position for neutral period"
        engine.hooks.bias = (
            None if bias is None else bias.to(engine.device, torch.bfloat16)
        )
        try:
            for start, _end in spans:
                if str(start) in replacements:
                    continue
                if time.monotonic() >= engine.deadline - 30:
                    raise base.BudgetStop("placeholder deadline reserve")
                prefix = clone_cache(cache, start)
                kwargs = dict(
                    input_ids=torch.tensor([tokens], device=engine.device),
                    past_key_values=prefix,
                    use_cache=True,
                    logits_to_keep=1,
                )
                trace = mask_kwargs(torch, kwargs, masked - {start})
                with torch.inference_mode():
                    output = engine.model(**kwargs)
                    for old, new in zip(
                        cache.layers, output.past_key_values.layers, strict=True
                    ):
                        old.keys[:, :, start : start + 1] = new.keys[:, :, -1:]
                        old.values[:, :, start : start + 1] = new.values[:, :, -1:]
                replacements[str(start)] = tokens[0]
                masked.discard(start)
                new_replacements.append(
                    dict(position=start, token_ids=tokens, forward=trace)
                )
                del prefix, output
        finally:
            engine.hooks.bias = None
    session["masked"] = sorted(masked)
    assert cache.get_seq_length() == original_length
    return dict(
        bodies=copy.deepcopy(spans),
        before=before,
        after=session["masked"],
        absolute_length=original_length,
        placeholders=new_replacements,
        retained_text_unchanged=True,
        downstream_recomputed=False,
    )


def decision(arms, n, complete):
    if not complete:
        return "INCOMPLETE", {}
    target, broken, control = (26, 2, 4) if n == 32 else (20, 1, 3)
    passes = {
        a: {
            s: arms[a][s]["valid"].get("Python", 0) >= target
            and arms[a][s]["broken"] <= broken
            and arms["R3"][s]["valid"].get("Python", 0) <= control
            for s in ("SWITCH", "CLEAR")
        }
        for a in ("R2", "R4")
    }
    verdict = (
        "RELEASE WORKS"
        if any(all(p.values()) for p in passes.values())
        else "PARTIAL"
        if any(any(p.values()) for p in passes.values())
        else "NOT"
    )
    return verdict, passes


def summarize(rows, n, complete=False):
    arms = {
        a: {
            s: dose.aggregate([r for r in rows if r["arm"] == a and r["step"] == s])
            for s in STEPS
        }
        for a in ARMS
    }
    verdict, passes = decision(arms, n, complete)
    transitions = {}
    for a in ARMS:
        bank = {(r["episode"], r["step"]): r for r in rows if r["arm"] == a}
        transitions[a] = {}
        for left, right in zip(SCORED, SCORED[1:], strict=False):
            counts = Counter()
            for e in range(n):
                if (e, left) in bank and (e, right) in bank:
                    langs = [
                        bank[e, s]["score"]["valid_language"] or "broken"
                        for s in (left, right)
                    ]
                    counts[" -> ".join(langs)] += 1
            transitions[a][f"{left}->{right}"] = dict(counts)
    actual = [r for r in rows if "shared_from_generation" not in r]
    return dict(
        reading=verdict,
        passes=passes,
        complete=complete,
        episodes=n,
        arms=arms,
        transitions=transitions,
        records=len(rows),
        generations=len(actual),
        generated_tokens=sum(len(r["generated_token_ids"]) for r in actual),
        fresh_off=dose.aggregate([r for r in rows if r["arm"] == "fresh-OFF"]),
    )


def cpu_checks():
    import torch
    from transformers import AutoTokenizer, Qwen3MoeConfig, Qwen3MoeForCausalLM

    torch.set_num_threads(2)
    inherited = dose.cpu_checks()
    torch.manual_seed(SEED)
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
    cfg._attn_implementation = "sdpa"
    engine = base.Engine.__new__(base.Engine)
    engine.model = Qwen3MoeForCausalLM(cfg).eval()
    engine.torch, engine.device = torch, torch.device("cpu")
    engine.deadline, engine.eos = time.monotonic() + 300, set()
    real = AutoTokenizer.from_pretrained(base.MODEL, local_files_only=True)

    class Tokenizer:
        def apply_chat_template(self, *args, **kwargs):
            return [1 + i % 62 for i in real.apply_chat_template(*args, **kwargs)]

        def encode(self, *args, **kwargs):
            return [1 + i % 62 for i in real.encode(*args, **kwargs)]

        def decode(self, ids, **kwargs):
            return str(ids)

        def convert_tokens_to_ids(self, token):
            return 63

    engine.tokenizer = Tokenizer()
    engine.hooks = base.RouterHooks(
        [layer.mlp.gate for layer in engine.model.model.layers]
    )
    bias = torch.tensor([[0.0, 0.0, 0.0, 10.0]] * 2)
    session = session_new()
    messages = base.messages_for(prior.NEUTRAL)
    r = generation(engine, messages, bias, session, cap=3)
    start = len(r["input_token_ids"])
    session["bodies"] = [[start, start + 3]]
    assert r["appended_terminal_token_ids"] == [63]
    unmasked = fork_session(session)
    original_ids = session["token_ids"][:]
    old = clone_cache(session["past"])
    event = mask_answers(engine, session, False, bias)
    assert event["after"] == list(range(start, start + 3))
    assert session["token_ids"] == original_ids
    assert all(
        torch.equal(a.keys, b.keys) and torch.equal(a.values, b.values)
        for a, b in zip(old.layers, session["past"].layers, strict=True)
    )

    # Real SDPA consumer: corrupt masked K/V; logits must be bitwise unchanged.
    def logits(s):
        kwargs = dict(
            input_ids=torch.tensor([[7, 8]]),
            past_key_values=clone_cache(s["past"]),
            use_cache=True,
        )
        mask_kwargs(torch, kwargs, s["masked"])
        with torch.inference_mode():
            return engine.model(**kwargs).logits

    expected = logits(session)
    corrupted = fork_session(session)
    for layer in corrupted["past"].layers:
        layer.keys[:, :, session["masked"]] = 1e4
        layer.values[:, :, session["masked"]] = -1e4
    assert torch.equal(expected, logits(corrupted))
    assert not torch.equal(expected, logits(unmasked)), "Mask has no measured effect"
    # Compare actual masking against physical eviction with absolute positions.
    sparse = clone_cache(session["past"])
    survive = [p for p in range(len(original_ids)) if p not in session["masked"]]
    for layer in sparse.layers:
        layer.keys = layer.keys[:, :, survive].clone()
        layer.values = layer.values[:, :, survive].clone()
    with torch.inference_mode():
        sparse_logits = engine.model(
            input_ids=torch.tensor([[7, 8]]),
            past_key_values=sparse,
            position_ids=torch.tensor([[len(original_ids), len(original_ids) + 1]]),
            use_cache=True,
        ).logits
    torch.testing.assert_close(expected, sparse_logits, atol=1e-7, rtol=1e-5)
    # Actual base generator: masks on multi-token prefill, decode, appended EOS.
    messages += [dict(role="assistant", content=r["text"])]
    messages = base.messages_for(prior.NEUTRAL, history=messages)
    r = generation(engine, messages, -bias, session, cap=2)
    assert all(t["masked"] == event["after"] for t in r["mask_forward_trace"])
    assert r["mask_forward_trace"][0]["start"] == len(original_ids)
    assert r["mask_forward_trace"][-1]["length"] == 1
    # Placeholder writes only the first body column, preserves all other K/V.
    p = fork_session(unmasked)
    before = clone_cache(p["past"])
    mask_answers(engine, p, True, None)
    assert p["masked"] == [start + 1, start + 2]
    assert p["token_ids"] == original_ids and p["replacements"]
    keep = [i for i in range(len(original_ids)) if i != start]
    for a, b in zip(before.layers, p["past"].layers, strict=True):
        assert torch.equal(a.keys[:, :, keep], b.keys[:, :, keep])
        assert torch.equal(a.values[:, :, keep], b.values[:, :, keep])
    assert not torch.equal(
        before.layers[0].values[:, :, start], p["past"].layers[0].values[:, :, start]
    )
    engine.hooks.close()
    arms = {a: {s: dict(valid={"Python": 26}, broken=0) for s in STEPS} for a in ARMS}
    for s in STEPS:
        arms["R3"][s]["valid"] = {"Python": 4}
    assert decision(arms, 32, True)[0] == "RELEASE WORKS"
    for a in ("R2", "R4"):
        arms[a]["CLEAR"]["broken"] = 3
    assert decision(arms, 32, True)[0] == "PARTIAL"
    arms["R3"]["SWITCH"]["valid"]["Python"] = 5
    assert decision(arms, 32, True)[0] == "NOT"
    assert decision(arms, 32, False)[0] == "INCOMPLETE"
    assert projection(24)["seconds"] <= LIMIT < projection(32)["seconds"]
    assert not torch.cuda.is_initialized()
    return dict(
        inherited=inherited,
        real_sdpa_mask_consumed=True,
        poisoned_masked_kv_bitwise_invariant=True,
        physical_eviction_equivalent=True,
        positions_preserved=True,
        generation_decode_closure_masked=True,
        placeholder_only_first_body_column=True,
        literal_history_preserved=True,
        verdict_boundaries=True,
        cuda_initialized=False,
    )


def prepare():
    import torch

    assert not (OUT / "records.jsonl").exists(), "No outcome overwrite"
    n = 32 if projection(32)["seconds"] <= LIMIT else 24
    checks = cpu_checks()
    write("cpu.json", checks)
    write("tasks.json", make_tasks(n))
    write(
        "projection.json",
        dict(full=projection(32), fallback=projection(24), selected=projection(n)),
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
        *(ROOT / f"scripts/focus_check{s}.py" for s in ("40", "40b", "40c", "40d")),
        *(
            OUT / name
            for name in (
                "prewritten-reading.md",
                "tasks.json",
                "projection.json",
                "biases.pt",
            )
        ),
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
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        resource = prior.resources()
        write("resources.json", resource)
        if not resource["ready"]:
            print(json.dumps(dict(status="WAIT", **resource)), flush=True)
            return
        flag = OUT / "RUNNING.flag"
        with flag.open("x") as stream:
            stream.write(json.dumps(dict(pid=os.getpid(), check="40f")) + "\n")
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
            event = None
            if arm in ("R2", "R3", "R4", "T") and step in ("SWITCH", "CLEAR"):
                event = mask_answers(engine, session, arm == "R4", bias)
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
                    history = request(e, "R1", step, history, shared)
                prefix_rows = rows[offset:]
                for arm in ARMS[:4]:
                    session, branch = fork_session(shared), copy.deepcopy(history)
                    if arm != "R1":
                        for source in prefix_rows:
                            row = copy.deepcopy(source)
                            row.update(
                                arm=arm, shared_from_generation=source["generation"]
                            )
                            append(row)
                    for step in STEPS[3:]:
                        branch = request(e, arm, step, branch, session)
                    session = None
                shared = None
                session, history = session_new(), None
                for step in STEPS:
                    history = request(e, "T", step, history, session)
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
            key, dict(tokens=[], bodies=[], masked=[], replacements={})
        )
        task = prior.NEUTRAL if s == "NEUTRAL" else tasks[e][s]
        messages = base.messages_for(task, cue_for(a, s), histories.get(key))
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
        if a in ("R2", "R3", "R4", "T") and s in ("SWITCH", "CLEAR"):
            assert (
                event["bodies"] == state["bodies"]
                and event["before"] == state["masked"]
            )
            assert event["absolute_length"] == len(state["tokens"])
            masked = set(state["masked"]) | {
                p for b, end in state["bodies"] for p in range(b, end)
            }
            if a == "R4":
                new_positions = [
                    b
                    for b, end in state["bodies"]
                    if str(b) not in state["replacements"]
                ]
                assert [v["position"] for v in event["placeholders"]] == new_positions
                for replacement in event["placeholders"]:
                    b = replacement["position"]
                    assert replacement["token_ids"] == tokenizer.encode(
                        ".", add_special_tokens=False
                    )
                    expected_mask = sorted(
                        p
                        for p in masked
                        if p < b and str(p) not in state["replacements"]
                    )
                    assert replacement["forward"] == dict(
                        start=b, length=1, masked=expected_mask
                    )
                    state["replacements"][str(b)] = replacement["token_ids"][0]
            else:
                assert not event["placeholders"]
            masked.difference_update(int(p) for p in state["replacements"])
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
        assert len(rows) == len(tasks) * 36
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
        placeholder_positions_and_context=True,
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
