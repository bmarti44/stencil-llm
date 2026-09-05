#!/usr/bin/env python3
"""Unregistered check 34: actual cue-column transplant; user-turn stickiness."""

# ruff: noqa: E402, E501, I001
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path
from statistics import NormalDist

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from focus_check32_kv import (
    Engine as CacheEngine,
    BASE,
    USER,
    ASSISTANT,
    score as old_score,
)
from focus1_probe import gpu_pids, write_json

OUT = ROOT / "results/quick-checks/check34"
SEED, MAX_NEW = 34034, 64
CUES = {
    "A": "Sort the numbers from smallest to largest.",
    "B": "Sort the numbers from largest to smallest.",
    "OFF": "The room has a window and table.",
}
STEPS = ("SET", "HOLD", "SWITCH", "BACK", "CLEAR")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def score(text, values, **kw):
    result = old_score(text, values, **kw)
    expected = {"A": sorted(values), "B": sorted(values, reverse=True), "OFF": values}
    strict = result["strict"]
    valid = not strict["invalid_json"] and not strict["integer_schema_invalid"]
    result["value_exact"] = {t: result["parsed"] == v for t, v in expected.items()}
    result["strict_exact"] = {
        t: valid and strict["parsed"] == v for t, v in expected.items()
    }
    result["label"] = next(
        (t for t, ok in result["value_exact"].items() if ok), "other"
    )
    # The reused strict parser has old task-specific fields; keep only parser diagnostics.
    result["strict"] = {
        k: v
        for k, v in strict.items()
        if k in ("parsed", "invalid_json", "integer_schema_invalid")
    }
    return result


def banks():
    rng, seen, result = random.Random(SEED), set(), {}
    for name, count in [
        ("single", 64),
        ("retained", 160),
        ("stick_final", 64),
        ("stick_prior", 192),
    ]:
        rows = []
        while len(rows) < count:
            v = rng.sample(range(-20, 21), rng.randint(5, 8))
            key = tuple(sorted(v))
            if key in seen or v in (sorted(v), sorted(v, reverse=True)):
                continue
            seen.add(key)
            rows.append(v)
        result[name] = rows
    return result


def wilson(k, n, confidence=0.95):
    z = NormalDist().inv_cdf((1 + confidence) / 2)
    p, d = k / n, 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [max(0.0, c - h), min(1.0, c + h)]


def counts(rows):
    return dict(
        n=len(rows),
        exact=sum(r["score"]["value_exact"][r["target"]] for r in rows),
        strict=sum(r["score"]["strict_exact"][r["target"]] for r in rows),
        **{
            t: sum(r["score"]["label"] == t for r in rows)
            for t in ("A", "B", "OFF", "other")
        },
        breakage=sum(r["score"]["breakage"] for r in rows),
    )


def aggregate(rows):
    groups = defaultdict(list)
    for r in rows:
        groups[(r["part"], r["arm"], r["step"])].append(r)
    single = {a: counts(rs) for (p, a, _), rs in groups.items() if p == "single"}
    verdict = "PARTIAL"
    if all(single.get(a, {}).get("n") == 64 for a in ("all_A", "all_B", "off")):
        a, b, off = (single[k] for k in ("all_A", "all_B", "off"))
        if (
            min(a["exact"], b["exact"]) >= 40
            and max(a["breakage"], b["breakage"]) <= 2
            and off["A"] + off["B"] <= 4
        ):
            verdict = "POSITIVE"
        elif max(a["exact"], b["exact"]) <= 8:
            verdict = "NEGATIVE"
    stick = {
        a: counts(rs)
        for (p, a, s), rs in groups.items()
        if p == "stickiness" and s == "final"
    }
    sr = {"verdict": "PARTIAL", "arms": stick}
    if len(stick) == 3 and all(v["n"] == 64 for v in stick.values()):
        x, y = stick["B_fresh"]["exact"], stick["B_after_A"]["exact"]
        for v in stick.values():
            v["wilson95"] = wilson(v["exact"], 64)
        lx, ux = wilson(x, 64, 0.975)
        ly, uy = wilson(y, 64, 0.975)
        paired = {
            a: {r["episode"]: r["score"]["value_exact"][r["target"]] for r in rs}
            for (p, a, s), rs in groups.items()
            if p == "stickiness" and s == "final"
        }
        sr.update(
            difference=(x - y) / 64,
            difference_wilson_bonferroni95=[lx - uy, ux - ly],
            fresh_only=sum(
                paired["B_fresh"][e] and not paired["B_after_A"][e] for e in range(64)
            ),
            history_only=sum(
                not paired["B_fresh"][e] and paired["B_after_A"][e] for e in range(64)
            ),
            verdict="REAL" if x >= 48 and (x - y) / 64 >= 0.15 else "NOT SUPPORTED",
        )
    sr["prior_turns"] = {
        a: counts(
            [
                r
                for r in rows
                if r["part"] == "stickiness" and r["arm"] == a and r["step"] != "final"
            ]
        )
        for a in ("B_after_A", "A_after_B")
    }
    retained = {}
    for arm in ("all_A", "all_B"):
        rs = [r for r in rows if r["part"] == "retained" and r["arm"] == arm]
        if rs:
            ep = defaultdict(list)
            for r in rs:
                ep[r["episode"]].append(r)
            retained[arm] = dict(
                steps={s: counts([r for r in rs if r["step"] == s]) for s in STEPS},
                completed=sum(len(v) == 5 for v in ep.values()),
                joint=sum(
                    len(v) == 5
                    and all(r["score"]["value_exact"][r["target"]] for r in v[:4])
                    for v in ep.values()
                ),
            )
    return dict(single=single, part1_verdict=verdict, stickiness=sr, retained=retained)


class StopRun(RuntimeError):
    pass


class Budget:
    def __init__(self):
        self.started, self.checked = time.monotonic(), 0

    def check(self):
        now = time.monotonic()
        if now - self.started > 45 * 60 - 10:
            raise StopRun("45 GPU-minute cap; completed rows preserved")
        if now - self.checked > 5:
            self.checked = now
            other = gpu_pids() - {os.getpid()}
            if other:
                raise StopRun(
                    f"Foreign compute appeared: {sorted(other)}; exiting without signals"
                )


class Engine(CacheEngine):
    def __init__(self, *args):
        super().__init__(*args)
        self.positions = list(range(64, 76))
        self.batch_id = 0

    def context(self, episode):
        subjects = ("room", "garden", "hall", "path", "window", "table", "wall", "sky")
        a, b = subjects[episode // 8], subjects[episode % 8]
        ids = self.enc(BASE + f"The {a} is quiet. The {b} is still.\n")
        assert len(ids) <= 64
        return ids + self.enc(" ") * (64 - len(ids))

    def prefix(self, episode, task):
        cue = self.enc(CUES[task])
        assert len(cue) == 8
        return self.context(episode) + cue + self.suffix

    def session(self):
        return dict(cache=self.Cache(self.cfg), history=[])

    def forward_batch(self, ids, cache):
        from stencil.qwen3 import prefill_with_eviction

        self.budget.check()
        logits, _, _, _ = prefill_with_eviction(
            self.model,
            cache,
            self.torch.tensor(ids, device=self.device),
            history_end=0,
            evict_range=None,
        )
        assert cache.length == cache.k[0].shape[2]
        return logits

    def jobs(self, jobs, generate=True):
        from stencil.function_vectors import repeated_4gram_fraction

        grouped = defaultdict(list)
        for j in jobs:
            grouped[(j["session"]["cache"].length, len(j["ids"]))].append(j)
        for pool in grouped.values():
            for lo in range(0, len(pool), 8):
                batch = pool[lo : lo + 8]
                sessions = [j["session"] for j in batch]
                cache = self.Cache(self.cfg)
                cache.length = sessions[0]["cache"].length
                if cache.length:
                    for kind in ("k", "v"):
                        for layer in range(self.cfg.n_layer):
                            getattr(cache, kind)[layer] = self.torch.cat(
                                [getattr(s["cache"], kind)[layer] for s in sessions]
                            )
                self.batch_id += 1
                logits = self.forward_batch([j["ids"] for j in batch], cache)
                for j in batch:
                    j["session"]["history"].extend(j["ids"])
                    j["batch_id"] = self.batch_id
                if generate:
                    outputs, ends, alive = (
                        [[] for _ in batch],
                        [None] * len(batch),
                        [True] * len(batch),
                    )
                    for _ in range(MAX_NEW):
                        nxt = logits[:, -1].argmax(-1).tolist()
                        for i, token in enumerate(nxt):
                            if alive[i]:
                                sessions[i]["history"].append(token)
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
                for row, session in enumerate(sessions):
                    result = self.Cache(self.cfg)
                    result.length = len(session["history"])
                    for kind in ("k", "v"):
                        for layer in range(self.cfg.n_layer):
                            getattr(result, kind)[layer] = getattr(cache, kind)[layer][
                                row : row + 1, :, : result.length
                            ].clone()
                    session["cache"] = result
                del logits, cache

    def capture(self, cache):
        return [
            [
                getattr(cache, k)[layer][:, :, 64:76].clone()
                for layer in range(self.cfg.n_layer)
            ]
            for k in ("k", "v")
        ]

    def edit(self, cache, packet, kind="both", start=0):
        changed = {}
        for i, name in enumerate(("k", "v")):
            if kind not in ("both", name):
                continue
            diffs = []
            for layer in range(start, self.cfg.n_layer):
                view = getattr(cache, name)[layer][:, :, 64:76]
                diffs.append(
                    float((view.float() - packet[i][layer].float()).abs().max())
                )
                view.copy_(packet[i][layer])
                assert self.torch.equal(view, packet[i][layer])
            changed[name] = diffs
        return dict(
            kinds=kind,
            layers=list(range(start, self.cfg.n_layer)),
            positions=self.positions,
            copied_bitwise=True,
            max_abs_changes_per_layer=changed,
        )

    def same(self, cache, packet):
        return all(
            self.torch.equal(getattr(cache, k)[layer][:, :, 64:76], packet[i][layer])
            for i, k in enumerate(("k", "v"))
            for layer in range(self.cfg.n_layer)
        )

    def query(self, values, task=None):
        cue = CUES[task] + " " if task else ""
        return self.enc(
            USER
            + cue
            + "Process these integers. Output only a JSON array. Integers: "
            + json.dumps(values)
            + ASSISTANT
        )

    def answer(self, sessions, metadata, emit):
        jobs = [
            dict(session=s, ids=self.query(m["values"], m.get("user_cue")), **m)
            for s, m in zip(sessions, metadata, strict=True)
        ]
        self.jobs(jobs)
        for j in jobs:
            s = j["session"]
            ending = (
                []
                if j["eos_token_id"] is not None
                else [self.tok.token_to_id("<|im_end|>")]
            ) + self.enc("\n")
            self.jobs([dict(session=s, ids=ending)], generate=False)
            record = {k: v for k, v in j.items() if k not in ("session", "ids")}
            record.update(
                prompt_token_ids=j["ids"],
                trailing_token_ids=ending,
                cache_length_after=s["cache"].length,
                history_sha256=hashlib.sha256(
                    json.dumps(s["history"]).encode()
                ).hexdigest(),
            )
            emit(record)


def run():
    active = gpu_pids()
    if active:
        raise RuntimeError(f"GPU busy: {sorted(active)}; aborted without signals")
    if (ROOT / ".review.lock").exists():
        raise RuntimeError("Review lock exists; refusing edits/run")
    out = OUT / "4b"
    if (out / "summary.json").exists() or (out / "records.jsonl").exists():
        raise RuntimeError("Refusing to overwrite prior run")
    import torch
    from tokenizers import Tokenizer
    from stencil.qwen3 import Qwen3, Qwen3Config

    budget = Budget()
    rows = []
    data = dict(
        status="running",
        seed=SEED,
        trunk="Qwen3-4B",
        pid=os.getpid(),
        source_commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        script_sha256=sha(Path(__file__)),
        reading_sha256=sha(OUT / "README.md"),
        started_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        lineage="fit-on=none; operand-free donor extraction; fresh seed-34034 synthetic evaluation only",
        numerics="bf16 hf_compatible=True, greedy, pad-free batches <=8",
        max_new_tokens=MAX_NEW,
        initial_gpu_compute_apps=[],
        gpu_cap_minutes=45,
    )

    def save():
        data.update(aggregate(rows))
        data.update(
            records_count=len(rows), elapsed_seconds=time.monotonic() - budget.started
        )
        if torch.cuda.is_initialized():
            data["peak_cuda_allocated_bytes"] = torch.cuda.max_memory_allocated()
        write_json(out / "summary.json", data)

    def emit(r):
        rows.append(r)
        with (out / "records.jsonl").open("a") as f:
            f.write(json.dumps(r, allow_nan=False) + "\n")
        if len(rows) % 32 == 0:
            save()
            print(
                f"{len(rows)} records, {data['elapsed_seconds'] / 60:.2f} min",
                flush=True,
            )

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
        bank = banks()
        write_json(out / "episodes.json", bank)
        write_json(
            out / "layout.json",
            dict(
                cues=CUES,
                cue_positions=list(range(64, 72)),
                suffix_positions=list(range(72, 76)),
                filler_body_token_ids=eng.filler,
                contexts=[eng.context(e) for e in range(64)],
            ),
        )
        donors = {}
        with torch.inference_mode():
            for ep in range(64):
                sessions = [eng.session() for _ in range(3)]
                tasks = ("A", "B", "OFF")
                eng.jobs(
                    [
                        dict(session=s, ids=eng.prefix(ep, t))
                        for s, t in zip(sessions, tasks, strict=True)
                    ],
                    False,
                )
                for s, t in zip(sessions, tasks, strict=True):
                    donors[ep, t] = eng.capture(s["cache"])
                    r = dict(
                        episode=ep,
                        task=t,
                        prefix_token_ids=s["history"],
                        packet_sha256=hashlib.sha256(
                            b"".join(
                                v.cpu().view(torch.uint8).numpy().tobytes()
                                for ls in donors[ep, t]
                                for v in ls
                            )
                        ).hexdigest(),
                    )
                    with (out / "donors.jsonl").open("a") as f:
                        f.write(json.dumps(r) + "\n")
            print("192 operand-free donor/filler prefixes captured", flush=True)
            single_start = time.monotonic()
            for ep, values in enumerate(bank["single"]):
                arms = [("off", "OFF")] + [
                    (a, t)
                    for a in (
                        "all",
                        "shuffled",
                        "text",
                        "layers_ge12",
                        "k_only",
                        "v_only",
                    )
                    for t in ("A", "B")
                ]
                sessions = [eng.session() for _ in arms]
                eng.jobs(
                    [
                        dict(session=s, ids=eng.prefix(ep, t if a == "text" else "OFF"))
                        for s, (a, t) in zip(sessions, arms, strict=True)
                    ],
                    False,
                )
                meta = []
                for s, (a, t) in zip(sessions, arms, strict=True):
                    donor_ep = (ep + 1) % 64 if a == "shuffled" else ep
                    write = None
                    if a not in ("off", "text"):
                        write = eng.edit(
                            s["cache"],
                            donors[donor_ep, t],
                            kind={"k_only": "k", "v_only": "v"}.get(a, "both"),
                            start=12 if a == "layers_ge12" else 0,
                        )
                    closing = eng.enc("<|im_end|>\n")
                    eng.jobs([dict(session=s, ids=closing)], False)
                    meta.append(
                        dict(
                            part="single",
                            episode=ep,
                            arm="off" if a == "off" else f"{a}_{t}",
                            step="single",
                            target=t,
                            values=values,
                            donor_episode=donor_ep,
                            packet_write=write,
                            prefix_token_ids=eng.prefix(ep, t if a == "text" else "OFF")
                            + closing,
                        )
                    )
                eng.answer(sessions, meta, emit)
                if ep == 0:
                    seconds = time.monotonic() - single_start
                    data["pilot"] = dict(
                        seconds_per_13_arm_episode=seconds,
                        projected_single_seconds=64 * seconds,
                        peak_bytes=torch.cuda.max_memory_allocated(),
                    )
                    save()
                    print(f"Pilot: {data['pilot']}", flush=True)
            data["single_seconds"] = time.monotonic() - single_start
            save()
            print(f"Single-shot: {data['part1_verdict']}; {data['single']}", flush=True)
            stick_start = time.monotonic()
            for ep, values in enumerate(bank["stick_final"]):
                sessions = [eng.session() for _ in range(3)]
                prefix = eng.enc(BASE + "<|im_end|>\n")
                eng.jobs([dict(session=s, ids=prefix) for s in sessions], False)
                for turn in range(3):
                    pv = bank["stick_prior"][ep * 3 + turn]
                    eng.answer(
                        sessions[1:],
                        [
                            dict(
                                part="stickiness",
                                episode=ep,
                                arm=a,
                                step=f"prior{turn + 1}",
                                target=t,
                                user_cue=t,
                                values=pv,
                                prefix_token_ids=prefix if turn == 0 else None,
                            )
                            for a, t in [("B_after_A", "A"), ("A_after_B", "B")]
                        ],
                        emit,
                    )
                eng.answer(
                    sessions,
                    [
                        dict(
                            part="stickiness",
                            episode=ep,
                            arm=a,
                            step="final",
                            target=t,
                            user_cue=t,
                            values=values,
                            prefix_token_ids=prefix if a == "B_fresh" else None,
                        )
                        for a, t in [
                            ("B_fresh", "B"),
                            ("B_after_A", "B"),
                            ("A_after_B", "A"),
                        ]
                    ],
                    emit,
                )
            data["stickiness_seconds"] = time.monotonic() - stick_start
            save()
            print(f"Stickiness: {data['stickiness']}", flush=True)
            eligible = [
                t for t in ("A", "B") if data["single"][f"all_{t}"]["exact"] >= 24
            ]
            data["retained_eligible_directions"] = eligible
            for ep in range(32):
                sessions = [eng.session() for _ in eligible]
                if not sessions:
                    break
                prefix = eng.prefix(ep, "OFF")
                eng.jobs([dict(session=s, ids=prefix) for s in sessions], False)
                original = [eng.capture(s["cache"]) for s in sessions]
                snapshots = [None] * len(sessions)
                for index, step in enumerate(STEPS):
                    meta = []
                    for i, (s, initial) in enumerate(
                        zip(sessions, eligible, strict=True)
                    ):
                        target = (
                            "OFF"
                            if step == "CLEAR"
                            else ("B" if initial == "A" else "A")
                            if step == "SWITCH"
                            else initial
                        )
                        write, retained = None, None
                        if step != "HOLD":
                            packet = (
                                original[i] if step == "CLEAR" else donors[ep, target]
                            )
                            write = eng.edit(s["cache"], packet)
                            snapshots[i] = eng.capture(s["cache"])
                        filler = eng.enc("<|im_end|>\n") if step == "SET" else []
                        if step == "HOLD":
                            filler = (
                                eng.enc(USER) + eng.filler + eng.enc("<|im_end|>\n")
                            )
                        if filler:
                            eng.jobs([dict(session=s, ids=filler)], False)
                        if step == "HOLD":
                            retained = eng.same(s["cache"], snapshots[i])
                            assert retained
                        meta.append(
                            dict(
                                part="retained",
                                episode=ep,
                                arm=f"all_{initial}",
                                step=step,
                                target=target,
                                values=bank["retained"][ep * 5 + index],
                                packet_write=write,
                                prefix_token_ids=prefix if step == "SET" else None,
                                filler_token_ids=filler,
                                hold_columns_bitwise_retained=retained,
                                clear_columns_bitwise_restored=eng.same(
                                    s["cache"], original[i]
                                )
                                if step == "CLEAR"
                                else None,
                            )
                        )
                    eng.answer(sessions, meta, emit)
            data["status"] = "complete"
    except StopRun as exc:
        data.update(status="partial", stop_reason=str(exc))
        print(str(exc), flush=True)
    except Exception as exc:
        data.update(status="error", error=repr(exc))
        raise
    finally:
        save()
    print(
        f"Finished: {data['status']}, {data['elapsed_seconds'] / 60:.2f} GPU-min",
        flush=True,
    )


def self_test():
    values = [4, -2, 7, 0, 1]
    assert score("[7,4,1,0,-2]", values)["label"] == "B"
    assert score("[1,0,7,-2,4]", values)["label"] == "other"
    assert score('Here: ["7", "4", "1", "0", "-2"]', values)["value_exact"]["B"]
    assert not score('Here: ["7", "4", "1", "0", "-2"]', values)["strict_exact"]["B"]
    assert score("[true,0,1,4,7]", values)["breakage"]
    b = banks()
    flat = [tuple(sorted(v)) for rows in b.values() for v in rows]
    assert len(flat) == len(set(flat)) == 480
    assert abs(wilson(32, 64)[0] - (1 - wilson(32, 64)[1])) < 1e-12
    import torch
    from types import SimpleNamespace
    from tokenizers import Tokenizer
    from stencil.qwen3 import KVCache

    tok = Tokenizer.from_file(str(ROOT / "models/qwen3-4b-hf/tokenizer.json"))
    eng = Engine(
        None,
        tok,
        SimpleNamespace(n_layer=14),
        torch,
        SimpleNamespace(check=lambda: None),
    )
    eng.device = "cpu"
    assert len({tuple(eng.context(e)) for e in range(64)}) == 64
    assert all(len(eng.prefix(e, t)) == 76 for e in range(64) for t in CUES)
    cache = KVCache(eng.cfg)
    cache.k = [torch.zeros(1, 1, 80, 2) for _ in range(14)]
    cache.v = [v.clone() for v in cache.k]
    packet = [[torch.ones(1, 1, 12, 2) * (i + 1) for _ in range(14)] for i in range(2)]
    eng.edit(cache, packet, kind="k", start=12)
    assert (
        cache.k[12][0, 0, 64, 0] == 1
        and cache.v[12].count_nonzero() == 0
        and cache.k[11].count_nonzero() == 0
    )
    eng.edit(cache, packet)
    assert eng.same(cache, packet) and cache.k[0][:, :, :64].count_nonzero() == 0
    answer = tok.encode("[7,4,1,0,-2]").ids
    eos = tok.token_to_id("<|im_end|>")

    class FakeModel:
        def __init__(self):
            self.cursor = 0

        def __call__(self, tokens, *, cache):
            batch, length = tokens.shape
            for layer in range(cache.cfg.n_layer):
                for kind in ("k", "v"):
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
            if length > 1:
                self.cursor = 0
            nxt = answer[self.cursor] if self.cursor < len(answer) else eos
            self.cursor += 1
            logits = torch.zeros(batch, 1, eos + 1)
            logits[:, :, nxt] = 1
            return logits

    eng.model = FakeModel()
    sessions = [eng.session(), eng.session()]
    eng.jobs(
        [dict(session=session, ids=eng.prefix(0, "OFF")) for session in sessions], False
    )
    originals = [eng.capture(session["cache"]) for session in sessions]
    captured = []
    for step in STEPS:
        for i, session in enumerate(sessions):
            if step != "HOLD":
                eng.edit(session["cache"], originals[i] if step == "CLEAR" else packet)
            else:
                eng.jobs([dict(session=session, ids=eng.filler)], False)
                assert eng.same(session["cache"], packet)
        eng.answer(
            sessions,
            [
                dict(
                    values=values,
                    target="B",
                    part="retained",
                    arm=f"all_{t}",
                    episode=0,
                    step=step,
                )
                for t in ("A", "B")
            ],
            captured.append,
        )
        assert all(
            session["cache"].length == len(session["history"]) for session in sessions
        )
    assert len(captured) == 10 and all(r["score"]["label"] == "B" for r in captured)
    assert all(r["eos_token_id"] == eos for r in captured)
    assert all(
        eng.same(session["cache"], original)
        for session, original in zip(sessions, originals, strict=True)
    )
    rows = []
    for arm, target, success in [
        ("all_A", "A", 40),
        ("all_B", "B", 40),
        ("off", "OFF", 64),
    ]:
        for ep in range(64):
            out = (
                sorted(values, reverse=target == "B")
                if ep < success and target != "OFF"
                else values
            )
            rows.append(
                dict(
                    part="single",
                    arm=arm,
                    step="single",
                    episode=ep,
                    target=target,
                    score=score(json.dumps(out), values),
                )
            )
    assert aggregate(rows)["part1_verdict"] == "POSITIVE"
    rows[39]["score"] = score(json.dumps(values), values)
    assert aggregate(rows)["part1_verdict"] == "PARTIAL"
    for r in rows:
        if r["arm"] != "off" and r["episode"] >= 8:
            r["score"] = score(json.dumps(values), values)
    assert aggregate(rows)["part1_verdict"] == "NEGATIVE"
    assert aggregate(rows[:-1])["part1_verdict"] == "PARTIAL"
    print(
        "CPU checks passed: descending scorer, 480 disjoint lists, token layout, actual cache edits, "
        "Wilson arithmetic, verdict boundaries, batched five-step retained generation with EOS/history accounting"
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", action="store_true")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    if args.self_test:
        self_test()
    if args.run:
        run()


if __name__ == "__main__":
    main()
