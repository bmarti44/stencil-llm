#!/usr/bin/env python3
"""Check 37: preread synthetic assistant-history repair, no fitting."""

# ruff: noqa: E402, E501, I001
from __future__ import annotations

import argparse
import copy
import json
import os
import random
import subprocess
import time
from pathlib import Path

from focus_check35 import Engine as PreviousEngine
from focus_check35 import ROOT, CUES, USER, StopRun, gpu_pids, sha, write_json
from focus_check32_kv import BASE, ASSISTANT

OUT = ROOT / "results/quick-checks/check37"
SEED = 9053701
ARMS = ("intact", "body_eos", "whole_pair", "placeholder")
MODES = ("surviving", "rebuilt")
STEPS = ("RELEASE1", "RELEASE2", "NEUTRAL1", "NEUTRAL2")
CUE = CUES["A"] + " Apply this rule to subsequent integer requests until I cancel it."
CANCEL = "Cancel the earlier sorting instruction. For subsequent requests, copy the integers in their original input order."


def bank():
    rng, seen, rows = random.Random(SEED), set(), []
    while len(rows) < 32 * 6:
        v = rng.sample(range(-20, 21), rng.randint(5, 8))
        key = tuple(sorted(v))
        if key in seen or v in (sorted(v), sorted(v, reverse=True)):
            continue
        seen.add(key)
        rows.append(v)
    return [rows[i : i + 6] for i in range(0, len(rows), 6)]


def aggregate(rows):
    arms, indexed = {}, {}
    for arm in ARMS:
        for mode in MODES:
            rs = [r for r in rows if r["arm"] == arm and r["mode"] == mode]
            indexed[arm, mode] = {(r["episode"], r["step"]): r for r in rs}
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
                )
            arms[f"{arm}/{mode}"] = dict(
                steps=steps,
                broken_episodes=sorted({r["episode"] for r in rs if r["broken"]}),
            )
    complete = all(s["n"] == 32 for a in arms.values() for s in a["steps"].values())
    gates = {}
    for mode in MODES:
        p, baseline = (arms[f"{a}/{mode}"] for a in ("placeholder", "intact"))
        additional = sorted(
            set(p["broken_episodes"]) - set(baseline["broken_episodes"])
        )
        losses = {
            s: baseline["steps"][s]["success"] - p["steps"][s]["success"]
            for s in STEPS[:2]
        }
        copies = {s: p["steps"][s]["success"] for s in STEPS[2:]}
        gates[mode] = dict(
            additional_broken_episodes=additional,
            active_success_losses=losses,
            neutral_copies=copies,
            passes=complete
            and not additional
            and max(losses.values()) <= 1
            and min(copies.values()) >= 26,
        )
    comparisons = {}
    for arm in ARMS:
        comparisons[arm] = {}
        for step in STEPS:
            pairs = [
                (indexed[arm, "surviving"][e, step], indexed[arm, "rebuilt"][e, step])
                for e in range(32)
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


class Budget:
    def __init__(self):
        self.started, self.checked = time.monotonic(), 0

    def check(self):
        now = time.monotonic()
        if now - self.started >= 30 * 60 - 20:
            raise StopRun("30 GPU-minute cap; cooperative exit, records preserved")
        if now - self.checked >= 5:
            self.checked = now
            other = gpu_pids() - {os.getpid()}
            if other:
                raise StopRun(
                    f"Foreign GPU compute {sorted(other)}; exit without signals"
                )


class Engine(PreviousEngine):
    def prefill(self, s, ids):
        if ids:
            self.jobs([dict(session=s, ids=ids)], False)
        assert len(s["history"]) == len(s["positions"])

    def event(self, s, text):
        # Fixed event acknowledgement, never part of the removable request pairs.
        self.prefill(
            s,
            self.enc(USER + text + "<|im_end|>\n<|im_start|>assistant\n.<|im_end|>\n"),
        )

    def rebuild(self, s):
        result = {k: copy.deepcopy(v) for k, v in s.items() if k != "cache"}
        result.update(
            cache=self.Cache(self.cfg), history=[], positions=[], mode="rebuilt"
        )
        pairs = list(zip(s["positions"], s["history"], strict=True))
        lo = 0
        while lo < len(pairs):
            hi = lo + 1
            while hi < len(pairs) and pairs[hi][0] == pairs[hi - 1][0] + 1:
                hi += 1
            result["cache"].length = pairs[lo][0]
            self.prefill(result, [token for _, token in pairs[lo:hi]])
            lo = hi
        result["cache"].length = s["cache"].length
        assert (
            result["history"] == s["history"] and result["positions"] == s["positions"]
        )
        return result

    def repair(self, s):
        arm, old = s["arm"], s["positions"][:]
        assert len(old) == len(s["history"])
        drop, replacements = set(), []
        for turn in s["turns"]:
            if turn["edited"]:
                continue
            if arm == "body_eos":
                drop.update(turn["generated_and_eos"])
            elif arm == "whole_pair":
                drop.update(turn["pair"])
            elif arm == "placeholder":
                body = turn["body"]
                assert body and all(p in old for p in body)
                first = body[0]
                index = old.index(first)
                prefix = self.Cache(self.cfg)
                prefix.length = first
                for kind in ("k", "v"):
                    setattr(
                        prefix,
                        kind,
                        [v[:, :, :index].clone() for v in getattr(s["cache"], kind)],
                    )
                self.forward_batch([self.enc(".")], prefix)
                for kind in ("k", "v"):
                    for layer in range(self.cfg.n_layer):
                        getattr(s["cache"], kind)[layer][:, :, index : index + 1] = (
                            getattr(prefix, kind)[layer][:, :, -1:]
                        )
                s["history"][index] = self.enc(".")[0]
                drop.update(body[1:])
                replacements.append(first)
                del prefix
            turn["edited"] = True
        drop &= set(old)
        survivors = [i for i, p in enumerate(old) if p not in drop]
        before = [[v.clone() for v in getattr(s["cache"], kind)] for kind in ("k", "v")]
        absolute = s["cache"].length
        if drop:
            mapping = s["cache"].evict(
                0, len(old), keep=[(i, i + 1) for i in survivors]
            )
            assert mapping == {i: j for j, i in enumerate(survivors)}
        assert s["cache"].length == absolute
        for ki, kind in enumerate(("k", "v")):
            for layer in range(self.cfg.n_layer):
                assert self.equal(
                    getattr(s["cache"], kind)[layer], before[ki][layer][:, :, survivors]
                )
        s["positions"] = [old[i] for i in survivors]
        s["history"] = [s["history"][i] for i in survivors]
        s["answers"] = [p for p in s["answers"] if p not in drop]
        self.operation(
            s,
            "repair",
            sorted(drop),
            replacements=replacements,
            retained_positions=s["positions"],
            retained_token_ids=s["history"],
            turns=copy.deepcopy(s["turns"]),
            survivors_bitwise_after_replacement=True,
            absolute_position_unchanged=True,
        )

    def answer(self, sessions, values, emit):
        jobs = []
        for s in sessions:
            neutral = s["step"].startswith("NEUTRAL")
            request = (
                "Copy these integers in their original input order. Output only a JSON array. Integers: "
                if neutral
                else "Process these integers. Output only a JSON array. Integers: "
            )
            user = self.enc(USER + request + json.dumps(values))
            header = self.enc("<|im_end|>\n<|im_start|>assistant\n")
            thinking = self.enc("<think>\n\n</think>\n\n")
            ids = user + header + thinking
            assert ids == self.enc(USER + request + json.dumps(values) + ASSISTANT)
            jobs.append(
                dict(
                    session=s,
                    ids=ids,
                    values=values,
                    start=s["cache"].length,
                    body_start=s["cache"].length + len(user) + len(header),
                    history_before=s["history"][:],
                    positions_before=s["positions"][:],
                )
            )
        self.jobs(jobs)
        for j in jobs:
            s = j["session"]
            generated_start = j["start"] + len(j["ids"])
            generated_end = generated_start + len(j["generated_token_ids"])
            closure = self.tok.token_to_id("<|im_end|>")
            # Preserve raw EOS in scores; normalize only future history closure.
            if j["eos_token_id"] != closure:
                self.prefill(s, [closure])
            end_position = s["positions"][-1]
            self.prefill(s, self.enc("\n"))
            turn = dict(
                pair=list(range(j["start"], s["cache"].length)),
                body=list(range(j["body_start"], end_position)),
                generated_and_eos=list(range(generated_start, end_position + 1)),
                closure=end_position,
                edited=False,
            )
            s["turns"].append(turn)
            strict = j["score"]["strict"]
            valid = not strict["invalid_json"] and not strict["integer_schema_invalid"]
            broken = not valid or j["score"]["breakage"] or j["eos_token_id"] != closure
            target = "OFF" if s["step"].startswith("NEUTRAL") else "A"
            r = {k: v for k, v in j.items() if k not in ("session", "ids")}
            r.update(
                episode=s["episode"],
                arm=s["arm"],
                mode=s["mode"],
                step=s["step"],
                target=target,
                prompt_token_ids=j["ids"],
                history_after=s["history"][:],
                positions_after=s["positions"][:],
                turn=turn,
                cache_length_after=s["cache"].length,
                operation_ids=s["operations"][:],
                strict_valid=valid,
                broken=broken,
                success=not broken and j["score"]["strict_exact"][target],
                generated_body_end=generated_end,
            )
            emit(r)


def run():
    active = gpu_pids()
    utilization = subprocess.check_output(
        ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
        text=True,
    ).strip()
    if active or any(int(v) for v in utilization.splitlines()):
        raise RuntimeError(
            f"GPU busy: {sorted(active)}, utilization={utilization}; abort without signals"
        )
    assert not (ROOT / ".review.lock").exists()
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
        trunk="Qwen3-4B",
        gpu_cap_minutes=30,
        pid=os.getpid(),
        initial_gpu_compute_apps=[],
        initial_gpu_utilization=utilization,
        started_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        lineage="fit-on=none; evaluated-on=192 fresh seed-9053701 synthetic lists; no benchmark contents",
        placeholder_token_ids=placeholder,
        placeholder_cpu_verified=True,
        source_commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        source_hashes={
            str(p.relative_to(ROOT)): sha(p)
            for p in (
                Path(__file__),
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
        episodes = bank()
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
            for ep in range(32):
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
                            time.monotonic() - budget.started + duration * 31
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
    import torch
    from types import SimpleNamespace
    from tokenizers import Tokenizer
    from focus_check35 import self_test as previous_test

    previous_test()
    tok = Tokenizer.from_file(str(ROOT / "models/qwen3-4b-hf/tokenizer.json"))
    assert tok.encode(".").ids == [13] and tok.decode([13]) == "."
    eng = Engine(
        None,
        tok,
        SimpleNamespace(n_layer=2),
        torch,
        SimpleNamespace(check=lambda: None),
    )
    eng.device = "cpu"
    calls = []

    class FakeModel:
        def __call__(self, tokens, *, cache):
            calls.append((cache.length, tokens.tolist()))
            batch, length = tokens.shape
            for kind in ("k", "v"):
                for layer in range(cache.cfg.n_layer):
                    old = getattr(cache, kind)[layer]
                    new = tokens.float().view(batch, 1, length, 1)
                    getattr(cache, kind)[layer] = (
                        new if old is None else torch.cat((old, new), 2)
                    )
            cache.length += length
            logits = torch.zeros(batch, 1, max(eng.eos) + 1)
            logits[:, :, tok.token_to_id("<|im_end|>")] = 1
            return logits

    eng.model = FakeModel()
    eng.operation = lambda *args, **kwargs: None
    base = eng.session()
    base.update(
        episode=0,
        arm="shared",
        mode="shared",
        variant="shared",
        step="SET",
        operations=[],
        turns=[],
    )
    eng.prefill(base, eng.enc(BASE + "<|im_end|>\n"))
    eng.event(base, CUE)
    event_positions = base["positions"][:]
    smoke = []
    eng.answer([base], [3, 1, 2, 0, 4], smoke.append)
    assert smoke[0]["broken"] and not smoke[0]["success"]
    for arm in ARMS:
        s = eng.fork(base)
        s["arm"] = arm
        absolute = s["cache"].length
        eng.repair(s)
        assert s["positions"][: len(event_positions)] == event_positions
        if arm == "whole_pair":
            assert s["positions"] == event_positions
        if arm == "placeholder":
            text = tok.decode(s["history"], skip_special_tokens=False)
            assert text.endswith("<|im_start|>assistant\n.<|im_end|>\n")
        rebuilt = eng.rebuild(s)
        assert rebuilt["cache"].length == absolute
        assert rebuilt["cache"].k[0].flatten().tolist() == s["history"]
        assert eng.equal(s["cache"].k[0], rebuilt["cache"].k[0])
        s["step"] = "RELEASE1"
        eng.answer([s], [2, 4, 0, 3, 1], smoke.append)
        assert s["turns"][-1]["pair"][0] == absolute
        eng.repair(s)
        eng.rebuild(s)
    assert (
        len(bank()) == 32
        and len({tuple(sorted(v)) for ep in bank() for v in ep}) == 192
    )
    assert aggregate([])["verdict"] == "INCOMPLETE"
    fixtures = [
        dict(
            episode=e,
            arm=a,
            mode=m,
            step=s,
            strict_valid=True,
            success=True,
            broken=False,
            target="A" if s.startswith("RELEASE") else "OFF",
            score={"value_exact": {"A": True, "OFF": True}},
            generated_token_ids=[1],
            eos_token_id=2,
        )
        for e in range(32)
        for a in ARMS
        for m in MODES
        for s in STEPS
    ]
    assert aggregate(fixtures)["verdict"] == "PROCEED_PLACEHOLDER"
    for r in fixtures:
        if r["arm"] == "placeholder" and r["step"] == "RELEASE2" and r["episode"] < 2:
            r["success"] = False
    assert aggregate(fixtures)["verdict"] == "STOP"
    for r in fixtures:
        r["success"] = True
        if r["arm"] == "placeholder" and r["step"] == "NEUTRAL2" and r["episode"] < 7:
            r["success"] = False
    assert aggregate(fixtures)["verdict"] == "STOP"
    for r in fixtures:
        r["success"] = True
    fixtures[-1]["broken"] = True
    assert aggregate(fixtures)["verdict"] == "STOP"
    print(
        "check37 CPU checks passed: one-token period; real generation/repair/rebuild consumer; sparse and trailing positions; strict breakage; gate boundaries; 192 unique inputs"
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
