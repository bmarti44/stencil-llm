#!/usr/bin/env python3
"""Disclosed check 35: retained cue transplant, recent positions, answer eviction."""

# ruff: noqa: E402, E501, I001
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import random
import subprocess
import time
from collections import defaultdict
from pathlib import Path

from focus_check34 import (
    Engine as PreviousEngine,
    Budget,
    StopRun,
    ROOT,
    CUES,
    USER,
    score,
    counts,
    sha,
    gpu_pids,
    write_json,
)

OUT = ROOT / "results/quick-checks/check35"
SEED = 35035
ARMS = ("S1", "S2", "S3", "S4", "S5", "TEXT")
STEPS = ("SET", "HOLD", "SWITCH", "BACK", "CLEAR", "NEUTRAL")
VARIANTS = {
    "S1": ("c1",),
    "S2": ("c1", "c2", "c3"),
    "S3": ("c1", "c2", "c3"),
    "S4": ("c2",),
    "S5": ("c1", "c2", "c3"),
    "TEXT": ("text",),
}


def bank():
    rng, seen, rows = random.Random(SEED), set(), []
    while len(rows) < 192:
        v = rng.sample(range(-20, 21), rng.randint(5, 8))
        key = tuple(sorted(v))
        if key in seen or v in (sorted(v), sorted(v, reverse=True)):
            continue
        seen.add(key)
        rows.append(v)
    return [rows[i : i + 6] for i in range(0, 192, 6)]


def aggregate(rows):
    result = {}
    for arm in ARMS:
        for variant in VARIANTS[arm]:
            rs = [
                r
                for r in rows
                if r["arm"] == arm and r["variant"] in ("shared", variant)
            ]
            steps = {s: counts([r for r in rs if r["step"] == s]) for s in STEPS}
            eps = defaultdict(dict)
            for r in rs:
                eps[r["episode"]][r["step"]] = r
            complete = all(c["n"] == 32 for c in steps.values())
            broken = sum(
                any(g[s]["score"]["breakage"] for s in ("SWITCH", "BACK") if s in g)
                for g in eps.values()
            )
            result[f"{arm}/{variant}"] = dict(
                steps=steps,
                complete=complete,
                switch_back_broken_episodes=broken,
                solves_switch=complete
                and min(steps[s]["exact"] for s in ("SWITCH", "BACK")) >= 26
                and broken <= 1,
                solves_clear=complete
                and all(
                    steps[s]["A"] + steps[s]["B"] <= 3 for s in ("CLEAR", "NEUTRAL")
                ),
                joint_five=sum(
                    all(
                        s in g and g[s]["score"]["value_exact"][g[s]["target"]]
                        for s in STEPS[:5]
                    )
                    for g in eps.values()
                ),
                joint_six=sum(
                    all(
                        s in g and g[s]["score"]["value_exact"][g[s]["target"]]
                        for s in STEPS
                    )
                    for g in eps.values()
                ),
            )
    control = result["S4/c2"]["steps"]["SWITCH"]
    return dict(
        arms=result, release_reading_valid=control["n"] == 32 and control["A"] >= 26
    )


class Engine(PreviousEngine):
    def session(self):
        return dict(
            cache=self.Cache(self.cfg), history=[], positions=[], answers=[], slots=[]
        )

    def equal(self, x, y):
        assert x.numel() > 0 and x.shape == y.shape
        return self.torch.equal(
            x.contiguous().view(self.torch.uint8), y.contiguous().view(self.torch.uint8)
        )

    def digest(self, packet):
        return hashlib.sha256(
            b"".join(
                x.cpu().contiguous().view(self.torch.uint8).numpy().tobytes()
                for layers in packet
                for x in layers
            )
        ).hexdigest()

    def forward_batch(self, ids, cache):
        self.budget.check()
        return self.model(self.torch.tensor(ids, device=self.device), cache=cache)

    def jobs(self, jobs, generate=True):
        # Reuse check 34's pad-free greedy algorithm, but track physical columns
        # independently from cache.length; eviction must never reset RoPE offset.
        from stencil.function_vectors import repeated_4gram_fraction

        groups = defaultdict(list)
        for j in jobs:
            s = j["session"]
            groups[(s["cache"].length, len(s["positions"]), len(j["ids"]))].append(j)
        for (absolute, physical, _), pool in groups.items():
            for lo in range(0, len(pool), 8):
                batch = pool[lo : lo + 8]
                cache = self.Cache(self.cfg)
                cache.length = absolute
                if physical:
                    for kind in ("k", "v"):
                        for layer in range(self.cfg.n_layer):
                            getattr(cache, kind)[layer] = self.torch.cat(
                                [
                                    getattr(j["session"]["cache"], kind)[layer]
                                    for j in batch
                                ]
                            )
                logits = self.forward_batch([j["ids"] for j in batch], cache)
                self.batch_id += 1
                for j in batch:
                    s = j["session"]
                    s["history"].extend(j["ids"])
                    s["positions"].extend(range(absolute, absolute + len(j["ids"])))
                    j["batch_id"] = self.batch_id
                if generate:
                    outputs, ends, alive = (
                        [[] for _ in batch],
                        [None] * len(batch),
                        [True] * len(batch),
                    )
                    for _ in range(64):
                        nxt = logits[:, -1].argmax(-1).tolist()
                        pos = cache.length
                        for i, token in enumerate(nxt):
                            if alive[i]:
                                s = batch[i]["session"]
                                s["history"].append(token)
                                s["positions"].append(pos)
                                s["answers"].append(pos)
                                if token in self.eos:
                                    ends[i], alive[i] = token, False
                                else:
                                    outputs[i].append(token)
                        logits = self.forward_batch([[t] for t in nxt], cache)
                        if not any(alive):
                            break
                    for i, j in enumerate(batch):
                        j.update(
                            text=self.tok.decode(outputs[i], skip_special_tokens=False),
                            generated_token_ids=outputs[i],
                            eos_token_id=ends[i],
                        )
                        j["score"] = score(
                            j["text"],
                            j["values"],
                            truncated=ends[i] is None,
                            rep4=repeated_4gram_fraction(outputs[i]),
                        )
                for i, j in enumerate(batch):
                    s = j["session"]
                    result = self.Cache(self.cfg)
                    result.length = s["positions"][-1] + 1
                    for kind in ("k", "v"):
                        for layer in range(self.cfg.n_layer):
                            getattr(result, kind)[layer] = getattr(cache, kind)[layer][
                                i : i + 1, :, : len(s["positions"])
                            ].clone()
                    s["cache"] = result
                    assert result.k[0].shape[2] == len(s["positions"])
                del cache, logits

    def capture_at(self, s, positions):
        indices = [s["positions"].index(p) for p in positions]
        return [
            [
                getattr(s["cache"], k)[layer][:, :, indices].clone()
                for layer in range(self.cfg.n_layer)
            ]
            for k in ("k", "v")
        ]

    def operation(self, s, action, positions, **extra):
        record = dict(
            id=self.op_id,
            episode=s["episode"],
            arm=s["arm"],
            variant=s["variant"],
            step=s["step"],
            action=action,
            positions=positions,
            layers=list(range(self.cfg.n_layer)),
            kinds=["k", "v"],
            absolute_next=s["cache"].length,
            **extra,
        )
        self.op_id += 1
        with (self.out / "operations.jsonl").open("a") as f:
            f.write(json.dumps(record) + "\n")
        s["operations"].append(record["id"])

    def write(self, s, packet, positions, source):
        indices = [s["positions"].index(p) for p in positions]
        before = self.capture_at(s, positions)
        keep = [i for i, p in enumerate(s["positions"]) if p not in positions]
        # Advanced indexing returns a copy: assignment must target the cache itself.
        for ki, kind in enumerate(("k", "v")):
            for layer in range(self.cfg.n_layer):
                tensor = getattr(s["cache"], kind)[layer]
                untouched = tensor[:, :, keep].clone()
                tensor[:, :, indices] = packet[ki][layer]
                assert self.equal(tensor[:, :, indices], packet[ki][layer])
                if keep:
                    assert self.equal(tensor[:, :, keep], untouched)
        self.operation(
            s,
            "write",
            positions,
            physical_indices=indices,
            source=source,
            before_sha256=self.digest(before),
            after_sha256=self.digest(packet),
            copied_bitwise=True,
            untouched_bitwise=True,
        )

    def donor(self, ep, task, start):
        key = (ep, task, start)
        if key not in self.donors:
            s = self.session()
            s["cache"].length = start - 64
            assert start >= 64
            ids = self.prefix(ep, task)
            self.jobs([dict(session=s, ids=ids)], False)
            packet = self.capture_at(s, list(range(start, start + 12)))
            self.donors[key] = packet
            record = dict(
                id=f"{ep}/{task}/{start}",
                episode=ep,
                task=task,
                prefix_token_ids=ids,
                prefix_rope_offset=start - 64,
                positions=list(range(start, start + 12)),
                packet_sha256=self.digest(packet),
            )
            with (self.out / "donors.jsonl").open("a") as f:
                f.write(json.dumps(record) + "\n")
        return self.donors[key]

    def append(self, s, task):
        start = s["cache"].length
        positions = list(range(start, start + 12))
        packet = self.donor(s["episode"], task, start)
        filler = self.donor(s["episode"], "OFF", start)
        physical = len(s["positions"])
        for ki, kind in enumerate(("k", "v")):
            for layer in range(self.cfg.n_layer):
                old = getattr(s["cache"], kind)[layer]
                new = self.torch.cat((old, packet[ki][layer]), dim=2)
                assert self.equal(new[:, :, :physical], old)
                assert self.equal(new[:, :, physical:], packet[ki][layer])
                getattr(s["cache"], kind)[layer] = new
        s["cache"].length += 12
        s["positions"].extend(positions)
        s["history"].extend(self.enc(CUES["OFF"]) + self.suffix)
        s["slots"].append(dict(positions=positions, filler=filler))
        self.operation(
            s,
            "append",
            positions,
            physical_indices=list(range(physical, physical + 12)),
            source=f"{s['episode']}/{task}/{start}",
            after_sha256=self.digest(packet),
            copied_bitwise=True,
            untouched_bitwise=True,
        )

    def evict_answers(self, s):
        old_positions = s["positions"][:]
        drop = set(s["answers"]) & set(old_positions)
        indices = [i for i, p in enumerate(old_positions) if p in drop]
        assert indices, "Vacuous answer eviction"
        survivors = [i for i in range(len(old_positions)) if i not in indices]
        before = [[v.clone() for v in getattr(s["cache"], k)] for k in ("k", "v")]
        absolute = s["cache"].length
        keep = [(i, i + 1) for i in survivors]
        mapping = s["cache"].evict(0, len(old_positions), keep=keep)
        assert mapping == {old: new for new, old in enumerate(survivors)}
        assert s["cache"].length == absolute
        for ki, kind in enumerate(("k", "v")):
            for layer in range(self.cfg.n_layer):
                assert self.equal(
                    getattr(s["cache"], kind)[layer], before[ki][layer][:, :, survivors]
                )
        s["positions"] = [old_positions[i] for i in survivors]
        s["answers"] = [p for p in s["answers"] if p not in drop]
        self.operation(
            s,
            "evict_answers",
            sorted(drop),
            physical_indices=indices,
            survivor_positions=s["positions"],
            survivors_bitwise=True,
            absolute_position_unchanged=True,
        )

    def fork(self, s):
        result = {
            k: copy.deepcopy(v) for k, v in s.items() if k not in ("cache", "slots")
        }
        result["slots"] = s["slots"][:]
        result["cache"] = self.Cache(self.cfg)
        result["cache"].length = s["cache"].length
        for kind in ("k", "v"):
            setattr(
                result["cache"], kind, [v.clone() for v in getattr(s["cache"], kind)]
            )
        return result

    def answer35(self, sessions, values, emit):
        jobs = [
            dict(session=s, ids=self.query(values, s.get("user_cue")), values=values)
            for s in sessions
        ]
        before = [list(s["positions"]) for s in sessions]
        self.jobs(jobs)
        for j, positions in zip(jobs, before, strict=True):
            s = j["session"]
            ending = self.enc("\n")
            if j["eos_token_id"] is None:
                s["answers"].append(s["cache"].length)
                ending = [self.tok.token_to_id("<|im_end|>")] + ending
            self.jobs([dict(session=s, ids=ending)], False)
            record = {k: v for k, v in j.items() if k not in ("session", "ids")}
            record.update(
                episode=s["episode"],
                arm=s["arm"],
                variant=s["variant"],
                step=s["step"],
                target="B"
                if s["step"] == "SWITCH"
                else "OFF"
                if s["step"] in ("CLEAR", "NEUTRAL")
                else "A",
                operation_ids=s["operations"],
                prompt_token_ids=j["ids"],
                trailing_token_ids=ending,
                positions_before_request=positions,
                positions_after=s["positions"][:],
                answer_positions_retained=s["answers"][:],
                cache_length_after=s["cache"].length,
                history_sha256=hashlib.sha256(
                    json.dumps(s["history"]).encode()
                ).hexdigest(),
            )
            emit(record)


def run():
    active = gpu_pids()
    if active:
        raise RuntimeError(f"GPU busy: {sorted(active)}; abort without signals")
    assert not (ROOT / ".review.lock").exists()
    out = OUT / "4b"
    assert not (out / "summary.json").exists(), "Refusing overwrite"
    import torch
    from tokenizers import Tokenizer
    from stencil.qwen3 import Qwen3, Qwen3Config

    budget, rows = Budget(), []
    data = dict(
        status="running",
        seed=SEED,
        trunk="Qwen3-4B",
        pid=os.getpid(),
        initial_gpu_compute_apps=[],
        script_sha256=sha(Path(__file__)),
        reused_script_sha256=sha(ROOT / "scripts/focus_check34.py"),
        reading_sha256=sha(OUT / "README.md"),
        started_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        source_commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        lineage="fit-on=none; operand-free extraction; fresh seed-35035 synthetic lists only",
        gpu_cap_minutes=45,
    )

    def save():
        data.update(
            aggregate(rows),
            records_count=len(rows),
            elapsed_seconds=time.monotonic() - budget.started,
        )
        write_json(out / "summary.json", data)

    def emit(r):
        rows.append(r)
        with (out / "records.jsonl").open("a") as f:
            f.write(json.dumps(r, allow_nan=False) + "\n")

    save()
    try:
        cfg = Qwen3Config.from_hf(ROOT / "models/qwen3-4b-hf/config.json")
        tok = Tokenizer.from_file(str(ROOT / "models/qwen3-4b-hf/tokenizer.json"))
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
        eng.out, eng.donors, eng.op_id = out, {}, 0
        lists = bank()
        write_json(out / "episodes.json", lists)
        write_json(
            out / "layout.json",
            dict(
                cues=CUES,
                suffix_token_ids=eng.suffix,
                filler_token_ids=eng.filler,
                contexts=[eng.context(e) for e in range(32)],
                layers=list(range(cfg.n_layer)),
            ),
        )
        with torch.inference_mode():
            for ep in range(32):
                started = time.monotonic()
                sessions = []
                for arm in ARMS:
                    s = eng.session()
                    s.update(
                        episode=ep, arm=arm, variant="shared", step="SET", operations=[]
                    )
                    sessions.append(s)
                eng.jobs(
                    [dict(session=s, ids=eng.prefix(ep, "OFF")) for s in sessions],
                    False,
                )
                for s in sessions:
                    original = eng.capture_at(s, list(range(64, 76)))
                    s["slots"].append(
                        dict(positions=list(range(64, 76)), filler=original)
                    )
                    eng.write(
                        s, eng.donor(ep, "A", 64), list(range(64, 76)), f"{ep}/A/64"
                    )
                eng.jobs(
                    [dict(session=s, ids=eng.enc("<|im_end|>\n")) for s in sessions],
                    False,
                )
                for index, step in enumerate(STEPS[:4]):
                    for s in sessions:
                        s["step"], s["user_cue"] = step, None
                        if step != "SET":
                            s["operations"] = []
                        if step == "HOLD":
                            snap = eng.capture_at(s, list(range(64, 76)))
                            eng.jobs(
                                [
                                    dict(
                                        session=s,
                                        ids=eng.enc(USER)
                                        + eng.filler
                                        + eng.enc("<|im_end|>\n"),
                                    )
                                ],
                                False,
                            )
                            now = eng.capture_at(s, list(range(64, 76)))
                            assert all(
                                eng.equal(x, y)
                                for a, b in zip(snap, now, strict=True)
                                for x, y in zip(a, b, strict=True)
                            )
                            eng.operation(
                                s,
                                "hold_check",
                                list(range(64, 76)),
                                physical_indices=list(range(64, 76)),
                                retained_bitwise=True,
                                writes=0,
                            )
                        elif step in ("SWITCH", "BACK"):
                            task = "B" if step == "SWITCH" else "A"
                            if s["arm"] in ("S3", "S4", "S5"):
                                eng.evict_answers(s)
                            if s["arm"] in ("S2", "S5"):
                                eng.append(s, task)
                            elif s["arm"] in ("S1", "S3"):
                                eng.write(
                                    s,
                                    eng.donor(ep, task, 64),
                                    list(range(64, 76)),
                                    f"{ep}/{task}/64",
                                )
                            elif s["arm"] == "TEXT":
                                s["user_cue"] = task
                    eng.answer35(sessions, lists[ep][index], emit)
                forks = []
                for original in sessions:
                    for variant in VARIANTS[original["arm"]]:
                        s = eng.fork(original)
                        s.update(
                            variant=variant, step="CLEAR", user_cue=None, operations=[]
                        )
                        if variant == "c3":
                            eng.append(s, "OFF")
                        else:
                            if variant == "c2":
                                eng.evict_answers(s)
                            for slot in s["slots"]:
                                eng.write(
                                    s,
                                    slot["filler"],
                                    slot["positions"],
                                    "stored_original_OFF_filler",
                                )
                            if variant == "text":
                                s["user_cue"] = "OFF"
                        forks.append(s)
                eng.answer35(forks, lists[ep][4], emit)
                for s in forks:
                    s.update(step="NEUTRAL", user_cue=None, operations=[])
                eng.answer35(forks, lists[ep][5], emit)
                data["peak_cuda_allocated_bytes"] = torch.cuda.max_memory_allocated()
                if ep == 0:
                    data["pilot"] = dict(
                        seconds_per_episode=time.monotonic() - started,
                        projected_32_episode_minutes=(time.monotonic() - started)
                        * 32
                        / 60,
                    )
                save()
                print(
                    f"episode {ep + 1}/32: {len(rows)} records, {(time.monotonic() - budget.started) / 60:.2f} GPU-min; pilot={data['pilot']}",
                    flush=True,
                )
                eng.donors.clear()
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
            dict(status=data["status"], elapsed_minutes=data["elapsed_seconds"] / 60)
        ),
        flush=True,
    )


def self_test():
    from focus_check34 import self_test as previous_test

    previous_test()
    import torch
    from types import SimpleNamespace
    from tokenizers import Tokenizer

    tok = Tokenizer.from_file(str(ROOT / "models/qwen3-4b-hf/tokenizer.json"))
    eng = Engine(
        None,
        tok,
        SimpleNamespace(n_layer=2),
        torch,
        SimpleNamespace(check=lambda: None),
    )
    eng.device = "cpu"
    s = eng.session()
    s["cache"].length = 100
    s["positions"] = list(range(100))
    s["answers"] = [80, 81, 85]
    for kind in ("k", "v"):
        setattr(
            s["cache"],
            kind,
            [torch.arange(200).reshape(1, 1, 100, 2).float() for _ in range(2)],
        )
    operations = []
    eng.operation = lambda *args, **kw: operations.append((args[1:], kw))
    eng.evict_answers(s)
    assert s["cache"].length == 100 and len(s["positions"]) == 97
    assert s["positions"][80] == 82 and s["cache"].k[0][0, 0, 80, 0] == 164
    packet = [[torch.ones(1, 1, 12, 2) for _ in range(2)] for _ in range(2)]
    eng.write(s, packet, list(range(64, 76)), "test")
    assert s["cache"].k[0][0, 0, 64, 0] == 1
    assert (
        len(bank()) == 32
        and len({tuple(sorted(v)) for ep in bank() for v in ep}) == 192
    )

    # Exercise the actual sparse-cache consumer and generation path after eviction.
    class FakeModel:
        def __call__(self, tokens, *, cache):
            batch, length = tokens.shape
            for kind in ("k", "v"):
                for layer in range(cache.cfg.n_layer):
                    old = getattr(cache, kind)[layer]
                    new = (
                        tokens.float()
                        .view(batch, 1, length, 1)
                        .expand(-1, 1, -1, 2)
                        .clone()
                    )
                    getattr(cache, kind)[layer] = (
                        new if old is None else torch.cat((old, new), dim=2)
                    )
            cache.length += length
            logits = torch.zeros(batch, 1, max(eng.eos) + 1)
            logits[:, :, min(eng.eos)] = 1
            return logits

    eng.model = FakeModel()
    s["history"] = list(range(100))
    j = dict(session=s, ids=[7, 8], values=[3, 1, 2, 0, 4])
    eng.jobs([j])
    assert s["cache"].length == 103 and len(s["positions"]) == 100
    assert s["positions"][-3:] == [100, 101, 102] and s["answers"] == [102]
    assert j["eos_token_id"] == min(eng.eos)
    s["episode"] = 0
    eng.donor = lambda *args: packet
    eng.append(s, "B")
    assert s["cache"].length == 115 and s["positions"][-12:] == list(range(103, 115))
    assert len(s["positions"]) == 112
    eng.evict_answers(s)
    assert s["cache"].length == 115 and 102 not in s["positions"]
    assert not aggregate([])["release_reading_valid"]
    print(
        "check35 CPU checks passed: inherited scorer/generation, actual sparse eviction and writes, bank, empty verdict"
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", action="store_true")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    if args.self_test:
        self_test()
    if args.run:
        run()
