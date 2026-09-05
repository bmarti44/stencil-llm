#!/usr/bin/env python3
"""Disclosed check 36: replay check35 S1 histories and recompute downstream KV."""

# ruff: noqa: E402, E501, I001
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

from focus_check35 import Engine as PreviousEngine
from focus_check35 import ROOT, CUES, USER, StopRun, counts, gpu_pids, sha, write_json

OUT = ROOT / "results/quick-checks/check36"
SOURCE = ROOT / "results/quick-checks/check35/4b"
SEED = 36036
ARMS = ("R1", "R2", "R3", "R4", "R5")


def ids_sha(ids):
    return hashlib.sha256(json.dumps(ids).encode()).hexdigest()


def source_rows():
    rows = [
        json.loads(line) for line in (SOURCE / "records.jsonl").read_text().splitlines()
    ]
    selected = {(r["episode"], r["step"]): r for r in rows if r["arm"] == "S1"}
    assert len(selected) == 32 * 6
    return selected


def aggregate(rows):
    arms = {
        a: {
            s: counts([r for r in rows if r["arm"] == a and r["step"] == s])
            for s in ("SWITCH", "BACK")
        }
        for a in ARMS
    }
    complete = all(v["n"] == 32 for a in arms.values() for v in a.values())
    verdict = "PARTIAL"
    if complete:
        r2, r3 = (arms[a]["SWITCH"]["exact"] for a in ("R2", "R3"))
        verdict = (
            "STALE_DOWNSTREAM"
            if min(r2, r3) >= 26
            else "UNFAITHFUL_TRANSPLANT"
            if r3 >= 26 and r2 <= 8
            else "PRECEDENCE_PATTERN"
            if max(r2, r3) <= 8
            else "INCONCLUSIVE"
        )
    return dict(arms=arms, complete=complete, verdict=verdict)


class Budget:
    def __init__(self):
        self.started, self.checked = time.monotonic(), 0

    def check(self):
        now = time.monotonic()
        if now - self.started >= 15 * 60 - 10:
            raise StopRun("15 GPU-minute cap; completed records preserved")
        if now - self.checked >= 5:
            self.checked = now
            other = gpu_pids() - {os.getpid()}
            if other:
                raise StopRun(
                    f"Foreign GPU compute {sorted(other)}; exiting without signals"
                )


class Engine(PreviousEngine):
    def prefill(self, s, ids):
        if ids:
            self.jobs([dict(session=s, ids=ids)], False)

    def replay(self, ep, source):
        s = self.session()
        s.update(
            episode=ep, arm="source_S1", variant="shared", step="SET", operations=[]
        )
        self.prefill(s, self.prefix(ep, "OFF"))
        self.write(s, self.donor(ep, "A", 64), list(range(64, 76)), f"{ep}/A/64")
        self.prefill(s, self.enc("<|im_end|>\n"))
        for step in ("SET", "HOLD"):
            if step == "HOLD":
                self.prefill(s, self.enc(USER) + self.filler + self.enc("<|im_end|>\n"))
            r = source[ep, step]
            assert s["positions"] == r["positions_before_request"]
            assert self.query(r["values"]) == r["prompt_token_ids"]
            self.prefill(s, r["prompt_token_ids"])
            for token in r["generated_token_ids"] + (
                [r["eos_token_id"]] if r["eos_token_id"] is not None else []
            ):
                self.prefill(s, [token])
            self.prefill(s, r["trailing_token_ids"])
            s["answers"] = r["answer_positions_retained"][:]
            assert s["positions"] == r["positions_after"]
            assert ids_sha(s["history"]) == r["history_sha256"]
        assert s["positions"] == source[ep, "SWITCH"]["positions_before_request"]
        self.operation(
            s,
            "source_replay",
            s["positions"][:],
            history_sha256=ids_sha(s["history"]),
            set_and_hold_hashes_verified=True,
        )
        return s

    def recompute(self, s):
        history, positions = s["history"][:], s["positions"][:]
        absolute = s["cache"].length
        retained = [p for p in positions if p >= 76]
        assert retained and positions[:76] == list(range(76))
        prefix = self.capture_at(s, list(range(76)))
        for ki, kind in enumerate(("k", "v")):
            setattr(s["cache"], kind, [v.clone() for v in prefix[ki]])
        s["cache"].length = 76
        s["positions"], s["history"] = list(range(76)), history[:76]
        spans = []
        for p in retained:
            if not spans or p != spans[-1][-1] + 1:
                spans.append([])
            spans[-1].append(p)
        for span in spans:
            s["cache"].length = span[0]
            self.prefill(s, [history[p] for p in span])
        s["history"] = history
        s["cache"].length = absolute
        assert s["positions"] == positions
        after = self.capture_at(s, list(range(76)))
        assert all(
            self.equal(x, y)
            for a, b in zip(prefix, after, strict=True)
            for x, y in zip(a, b, strict=True)
        )
        self.operation(
            s,
            "recompute_downstream",
            retained,
            replay_token_ids=[history[p] for p in retained],
            spans=[[span[0], span[-1] + 1] for span in spans],
            prefix_bitwise_unchanged=True,
            history_sha256=ids_sha(history),
            absolute_position_unchanged=True,
        )

    def intervene(self, s, task):
        arm = s["arm"]
        s["operations"] = []
        if arm == "R3":
            history = s["history"][:]
            history[64:76] = self.enc(CUES[task]) + self.suffix
            assert len(s["positions"]) == len(history)
            s["cache"] = self.Cache(self.cfg)
            s["history"], s["positions"] = [], []
            self.prefill(s, history)
            self.operation(
                s,
                "text_rebuild",
                s["positions"][:],
                replay_token_ids=history,
                history_sha256=ids_sha(history),
            )
        elif arm == "R5":
            self.append(s, task)
        else:
            self.write(
                s,
                self.donor(s["episode"], task, 64),
                list(range(64, 76)),
                f"{s['episode']}/{task}/64",
            )
            if arm == "R4":
                self.evict_answers(s)
            if arm in ("R2", "R4"):
                self.recompute(s)

    def compare(self, x, y):
        assert x["positions"] == y["positions"]
        assert x["history"][:64] == y["history"][:64]
        assert x["history"][76:] == y["history"][76:]
        result = {}
        for kind in ("k", "v"):
            result[kind] = []
            for a, b in zip(
                getattr(x["cache"], kind), getattr(y["cache"], kind), strict=True
            ):
                delta = a.float() - b.float()
                result[kind].append(
                    dict(
                        bitwise_equal=self.equal(a, b),
                        max_abs=float(delta.abs().max()),
                        rms=float(delta.square().mean().sqrt()),
                    )
                )
        return result


def run():
    active = gpu_pids()
    utilization = subprocess.check_output(
        ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
        text=True,
    ).strip()
    if active or any(int(v.strip()) != 0 for v in utilization.splitlines()):
        raise RuntimeError(
            f"GPU busy: apps={sorted(active)}, utilization={utilization}; abort without signals"
        )
    assert not (ROOT / ".review.lock").exists()
    out = OUT / "4b"
    assert not (out / "summary.json").exists(), "Refusing overwrite"
    source = source_rows()
    import torch
    from tokenizers import Tokenizer
    from stencil.qwen3 import Qwen3, Qwen3Config

    budget, rows = Budget(), []
    reading = (OUT / "README.md").read_bytes()
    (out / "prewritten-reading.md").write_bytes(reading)
    data = dict(
        status="running",
        seed=SEED,
        trunk="Qwen3-4B",
        pid=os.getpid(),
        initial_gpu_compute_apps=[],
        initial_gpu_utilization=utilization,
        gpu_cap_minutes=15,
        reading_sha256=sha(out / "prewritten-reading.md"),
        started_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        source_commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        lineage="fit-on=none; evaluated-on=reused check35 S1 synthetic lists and recorded answers; no benchmarks",
        source_hashes={
            str(p.relative_to(ROOT)): sha(p)
            for p in (
                Path(__file__),
                ROOT / "scripts/focus_check35.py",
                ROOT / "scripts/focus_check34.py",
                SOURCE / "records.jsonl",
                SOURCE / "episodes.json",
                SOURCE / "layout.json",
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

    def emit(record):
        assert all(
            k in record
            for k in (
                "episode",
                "arm",
                "step",
                "text",
                "generated_token_ids",
                "prompt_token_ids",
                "positions_after",
                "score",
                "operation_ids",
            )
        )
        rows.append(record)
        with (out / "records.jsonl").open("a") as f:
            f.write(json.dumps(record, allow_nan=False) + "\n")

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
        with torch.inference_mode():
            for ep in range(32):
                started = time.monotonic()
                base = eng.replay(ep, source)
                with (out / "histories.jsonl").open("a") as f:
                    f.write(
                        json.dumps(
                            dict(
                                episode=ep,
                                token_ids=base["history"],
                                positions=base["positions"],
                                answer_positions=base["answers"],
                                source_hold_sha256=source[ep, "HOLD"]["history_sha256"],
                            )
                        )
                        + "\n"
                    )
                sessions = []
                for arm in ARMS:
                    s = eng.fork(base)
                    s.update(arm=arm, step="SWITCH", user_cue=None, operations=[])
                    sessions.append(s)
                del base
                for step, task in (("SWITCH", "B"), ("BACK", "A")):
                    for s in sessions:
                        s["step"] = step
                        eng.intervene(s, task)
                    if step == "SWITCH":
                        compare = eng.compare(sessions[1], sessions[2])
                        with (out / "equivalence.jsonl").open("a") as f:
                            f.write(
                                json.dumps(dict(episode=ep, step=step, kv=compare))
                                + "\n"
                            )
                    eng.answer35(sessions, source[ep, step]["values"], emit)
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
                    json.dumps(
                        dict(
                            episode=ep + 1,
                            records=len(rows),
                            minutes=data["elapsed_seconds"] / 60,
                            switch={
                                a: data["arms"][a]["SWITCH"]["exact"] for a in ARMS
                            },
                            pilot=data["pilot"],
                        )
                    ),
                    flush=True,
                )
                eng.donors.clear()
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
    eng = Engine(
        None,
        Tokenizer.from_file(str(ROOT / "models/qwen3-4b-hf/tokenizer.json")),
        SimpleNamespace(n_layer=2),
        torch,
        SimpleNamespace(check=lambda: None),
    )
    eng.device = "cpu"
    calls = []

    class FakeModel:
        def __call__(self, tokens, *, cache):
            calls.append((cache.length, tokens.tolist()[0]))
            for kind in ("k", "v"):
                for layer in range(cache.cfg.n_layer):
                    new = tokens.float().view(1, 1, -1, 1)
                    old = getattr(cache, kind)[layer]
                    getattr(cache, kind)[layer] = (
                        new if old is None else torch.cat((old, new), 2)
                    )
            cache.length += tokens.shape[1]
            return torch.zeros(1, 1, 1)

    eng.model = FakeModel()
    ops = []
    eng.operation = lambda *args, **kw: ops.append((args, kw))
    s = eng.session()
    eng.prefill(s, list(range(100)))
    s["answers"] = [80, 81, 85, 99]
    eng.evict_answers(s)
    calls.clear()
    eng.recompute(s)
    assert calls == [
        (76, list(range(76, 80))),
        (82, [82, 83, 84]),
        (86, list(range(86, 99))),
    ]
    assert s["history"] == list(range(100)) and s["cache"].length == 100
    assert s["positions"] == [p for p in range(100) if p not in (80, 81, 85, 99)]
    assert s["cache"].k[0].flatten().tolist() == s["positions"]
    eng.prefill(s, [123])
    assert s["positions"][-1] == 100 and s["history"][-1] == 123
    assert not aggregate([])["complete"] and aggregate([])["verdict"] == "PARTIAL"
    source = source_rows()
    for ep in range(32):
        history = eng.prefix(ep, "OFF") + eng.enc("<|im_end|>\n")
        for step in ("SET", "HOLD"):
            if step == "HOLD":
                history += eng.enc(USER) + eng.filler + eng.enc("<|im_end|>\n")
            r = source[ep, step]
            history += r["prompt_token_ids"] + r["generated_token_ids"]
            if r["eos_token_id"] is not None:
                history.append(r["eos_token_id"])
            history += r["trailing_token_ids"]
            assert ids_sha(history) == r["history_sha256"]
        assert len(history) == len(source[ep, "SWITCH"]["positions_before_request"])
    print(
        "check36 CPU checks passed: all 64 source hashes; actual sparse recompute consumer preserves tokens, gaps, trailing gap and next position"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    if args.run:
        run()
