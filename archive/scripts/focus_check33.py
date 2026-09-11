#!/usr/bin/env python3
"""Unregistered Q3: bounded replacement of the A-versus-B residual coordinate."""

# ruff: noqa: I001, E402
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import random
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from focus1_probe import TEMPLATE, gpu_pids, write_json
from focus_check32_kv import score

OUT = ROOT / "results/quick-checks/check33"
SEED = 33033
LAYERS = (8, 12, 16, 20)
VARIANTS = ("sustained", "one_shot")
STEPS = ("SET", "HOLD", "SWITCH", "BACK", "CLEAR")
TASKS = ("A", "A", "B", "A", "OFF")
ARMS = tuple(
    f"{v}_{a}" for v in VARIANTS for a in ("correct", "swapped", "shuffled")
) + ("off", "text")
MAX_NEW = 64


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seed(name):
    return (
        int.from_bytes(hashlib.sha256(f"{SEED}:{name}".encode()).digest()[:8], "big")
        >> 1
    )


def banks():
    seen, data = set(), {}
    for trunk in ("4b", "1.7b"):
        data[trunk] = {}
        for split, count in (("fit", 128), ("setup", 32), ("test", 320)):
            rng, rows = random.Random(seed(f"{trunk}:{split}")), []
            while len(rows) < count:
                v = rng.sample(range(-20, 21), rng.randint(5, 8))
                key = tuple(sorted(v))
                if key in seen or v in (sorted(v), sorted(v, reverse=True)):
                    continue
                seen.add(key)
                rows.append(v)
            data[trunk][split] = rows
    return data


def prompt(values, task="OFF", clear=False):
    instruction = {
        "A": "Sort these integers in ascending order.",
        "B": "Reverse these integers in their input order.",
        "OFF": "Process these integers.",
    }[task]
    if clear:
        instruction = "Copy these integers in the given order."
    return f"{instruction} Output only a JSON array. Integers: {json.dumps(values)}"


class StopProbe(RuntimeError):
    pass


class Budget:
    def __init__(self):
        self.started = time.monotonic()
        self.last_check = 0

    def check(self):
        if time.monotonic() - self.started >= 90 * 60 - 10:
            raise StopProbe("90 cumulative GPU-minute cap; partial output preserved")
        if time.monotonic() - self.last_check >= 5:
            self.last_check = time.monotonic()
            others = gpu_pids() - {os.getpid()}
            if others:
                raise StopProbe(f"Foreign compute apps appeared: {sorted(others)}")


def aggregate(rows):
    groups = defaultdict(dict)
    for r in rows:
        groups[r["episode"]][r["checkpoint"]] = r
    full = [g for g in groups.values() if len(g) == 5]
    return dict(
        n=len(full),
        checkpoints={
            s: dict(
                n=sum(s in g for g in groups.values()),
                exact=sum(
                    g[s]["score"]["value_exact"][g[s]["target"]]
                    for g in groups.values()
                    if s in g
                ),
                strict=sum(
                    g[s]["score"]["strict_exact"][g[s]["target"]]
                    for g in groups.values()
                    if s in g
                ),
                breakage=sum(
                    g[s]["score"]["breakage"] for g in groups.values() if s in g
                ),
            )
            for s in STEPS
        },
        joint=sum(
            all(g[s]["score"]["value_exact"][g[s]["target"]] for s in STEPS[:4])
            for g in full
        ),
        strict_joint=sum(
            all(g[s]["score"]["strict_exact"][g[s]["target"]] for s in STEPS[:4])
            for g in full
        ),
        breakage=sum(any(r["score"]["breakage"] for r in g.values()) for g in full),
        induction=sum(
            any(g[s]["score"]["label"] in ("A", "B") for s in STEPS[:4]) for g in full
        ),
        clear_impositions=sum(g["CLEAR"]["score"]["label"] in ("A", "B") for g in full),
    )


def reading(arms, variant):
    names = [f"{variant}_{a}" for a in ("correct", "swapped", "shuffled")]
    if any(arms.get(k, {}).get("n") != 64 for k in [*names, "text", "off"]):
        return "PARTIAL"
    c, w, r = (arms[k] for k in names)
    if arms["text"]["joint"] < 48:
        return "INELIGIBLE"
    if (
        c["joint"] >= 40
        and w["joint"] >= 40
        and r["induction"] <= 8
        and r["breakage"] <= 8
        and c["breakage"] <= 2
        and c["clear_impositions"] <= 2
    ):
        return "PASS"
    if c["checkpoints"]["SET"]["exact"] >= 32 and r["induction"] <= 8:
        return "MARGINAL"
    return "FAIL"


class Engine:
    """Pad-free batched forwards; persist only each row's actual retained history."""

    def __init__(self, model, tok, cfg, budget):
        from stencil.qwen3 import KVCache
        from stencil.qwen_task import FILLER

        self.model, self.tok, self.cfg, self.budget = model, tok, cfg, budget
        self.Cache = KVCache
        self.eos = {tok.token_to_id(t) for t in ("<|im_end|>", "<|endoftext|>")}
        assert None not in self.eos
        self.filler = self.encode(" ".join(FILLER) * 10)[:128]
        assert len(self.filler) == 128
        self.batch_id = 0

    def encode(self, text):
        return self.tok.encode(text).ids

    def session(self):
        return dict(cache=self.Cache(self.cfg), history=[])

    def packed(self, sessions):
        import torch

        cache = self.Cache(self.cfg)
        cache.length = sessions[0]["cache"].length
        assert all(
            s["cache"].length == cache.length == len(s["history"]) for s in sessions
        )
        if cache.length:
            for i in range(self.cfg.n_layer):
                for name in ("k", "v"):
                    getattr(cache, name)[i] = torch.cat(
                        [getattr(s["cache"], name)[i] for s in sessions]
                    )
        return cache

    def unpack(self, sessions, cache, lengths):
        for row, (session, length) in enumerate(zip(sessions, lengths, strict=True)):
            result = self.Cache(self.cfg)
            result.length = length
            for i in range(self.cfg.n_layer):
                for name in ("k", "v"):
                    getattr(result, name)[i] = getattr(cache, name)[i][
                        row : row + 1, :, :length
                    ].clone()
            session["cache"] = result
            assert length == len(session["history"])

    def hook(self, jobs, phase, absolute, alive=None):
        import torch

        enabled = [
            j.get("control") is not None
            and (phase == "prompt" or j["control"]["variant"] == "sustained")
            and (alive is None or alive[i])
            for i, j in enumerate(jobs)
        ]
        if not any(enabled):
            return None
        layer = next(
            j["control"]["layer"] for j, on in zip(jobs, enabled, strict=True) if on
        )
        assert all(
            j["control"]["layer"] == layer
            for j, on in zip(jobs, enabled, strict=True)
            if on
        )

        def apply(hidden):
            result = hidden.clone()
            for i, (j, on) in enumerate(zip(jobs, enabled, strict=True)):
                if not on:
                    continue
                ctrl = j["control"]
                indices = (
                    range(hidden.shape[1])
                    if phase == "filler"
                    else [hidden.shape[1] - 1]
                )
                for pos in indices:
                    h = hidden[i, pos].float()
                    u = ctrl["u"]
                    before = h @ u
                    delta = (ctrl["coordinate"] - before).clamp(
                        -ctrl["clip"], ctrl["clip"]
                    )
                    intended = h + delta * u
                    result[i, pos] = intended.to(hidden.dtype)
                    actual = result[i, pos].float() - h
                    orth = actual - (actual @ u) * u
                    j["hook_positions"].append(
                        dict(
                            phase=phase,
                            position=absolute + pos,
                            layer=layer,
                            before=float(before),
                            target=ctrl["coordinate"],
                            delta=float(delta),
                            clip=ctrl["clip"],
                            after=float(result[i, pos].float() @ u),
                            orthogonal_cast_norm=float(orth.norm()),
                            changed_elements=int(torch.count_nonzero(actual)),
                        )
                    )
            return result

        return layer, apply

    def forward(self, ids, cache, hook=None):
        import torch

        self.budget.check()
        return self.model(
            torch.tensor(ids, device="cuda"), cache=cache, residual_hook=hook
        )

    def run_jobs(self, jobs, generate=True, phase="prompt"):
        from stencil.function_vectors import repeated_4gram_fraction

        grouped = defaultdict(list)
        for j in jobs:
            c = j.get("control")
            grouped[
                (j["session"]["cache"].length, len(j["ids"]), c["layer"] if c else -1)
            ].append(j)
        for pool in grouped.values():
            for lo in range(0, len(pool), 8):
                batch = pool[lo : lo + 8]
                started = time.monotonic()
                self.batch_id += 1
                sessions = [j["session"] for j in batch]
                cache = self.packed(sessions)
                initial = cache.length
                logits = self.forward(
                    [j["ids"] for j in batch], cache, self.hook(batch, phase, initial)
                )
                for j in batch:
                    j["session"]["history"].extend(j["ids"])
                    j.setdefault("batch_ids", []).append(self.batch_id)
                if generate:
                    outputs, terminal = [[] for _ in batch], [None for _ in batch]
                    alive = [True for _ in batch]
                    for _ in range(MAX_NEW):
                        nxt = logits[:, -1].argmax(-1).tolist()
                        feed_alive = alive.copy()
                        for i, token in enumerate(nxt):
                            if not alive[i]:
                                continue
                            if token in self.eos:
                                terminal[i] = token
                                alive[i] = False
                                sessions[i]["history"].append(token)
                            elif len(outputs[i]) < MAX_NEW:
                                outputs[i].append(token)
                                sessions[i]["history"].append(token)
                            else:
                                alive[i] = False
                                feed_alive[i] = False
                        if not any(feed_alive):
                            break
                        logits = self.forward(
                            [[v] for v in nxt],
                            cache,
                            self.hook(batch, "decode", cache.length, feed_alive),
                        )
                        if not any(alive):
                            break
                    for i, j in enumerate(batch):
                        j["text"] = self.tok.decode(
                            outputs[i], skip_special_tokens=False
                        )
                        j["generated_token_ids"] = outputs[i]
                        j["terminal_token_id"] = terminal[i]
                        j["score"] = score(
                            j["text"],
                            j["values"],
                            truncated=terminal[i] is None,
                            rep4=repeated_4gram_fraction(outputs[i]),
                        )
                self.unpack(sessions, cache, [len(s["history"]) for s in sessions])
                for j in batch:
                    j["batch_seconds"] = time.monotonic() - started
                del logits, cache


def fit(engine, bank, out):
    import torch

    states = {t: {layer: [None] * 128 for layer in LAYERS} for t in ("A", "B", "OFF")}
    groups = defaultdict(list)
    extraction = []
    for i, v in enumerate(bank):
        for task in states:
            ids = engine.encode(TEMPLATE.format(prompt=prompt(v, task)))
            r = dict(example=i, task=task, values=v, prompt_token_ids=ids)
            extraction.append(r)
            groups[len(ids)].append(r)
    write_json(out / "extraction.json", extraction)
    for pool in groups.values():
        for lo in range(0, len(pool), 8):
            batch = pool[lo : lo + 8]
            engine.budget.check()
            logits, captured = engine.model(
                torch.tensor([r["prompt_token_ids"] for r in batch], device="cuda"),
                capture_hidden=LAYERS,
            )
            for row, r in enumerate(batch):
                for layer in LAYERS:
                    states[r["task"]][layer][r["example"]] = (
                        captured[layer][row, -1].float().cpu().clone()
                    )
            del logits, captured
    tensors, stats = {}, {}
    for layer in LAYERS:
        hs = {t: torch.stack(states[t][layer]) for t in states}
        means = {t: h.mean(0) for t, h in hs.items()}
        contrast = means["A"] - means["B"]
        assert torch.isfinite(contrast).all() and contrast.norm() > 0
        u = contrast / contrast.norm()
        cs = {t: float(u @ m) for t, m in means.items()}
        projections = {t: (h @ u).tolist() for t, h in hs.items()}
        margins = hs["A"] @ u - hs["B"] @ u
        tensors[layer] = dict(u=u, means=means, states=hs)
        stats[str(layer)] = dict(
            coordinates=cs,
            clip=abs(cs["A"] - cs["B"]),
            min_paired_margin=float(margins.min()),
            positive_pairs=int((margins > 0).sum()),
            global_gap=min(projections["A"]) - max(projections["B"]),
            off_fraction_B_to_A=(cs["OFF"] - cs["B"]) / (cs["A"] - cs["B"]),
            projections=projections,
        )
    torch.save(tensors, out / "fit-fp32.pt")
    write_json(out / "fit-stats.json", stats)
    return {layer: tensors[layer]["u"].cuda() for layer in LAYERS}, stats


def control(variant, cell, task, directions, stats, random_u=None):
    layer = cell["layer"]
    s = stats[str(layer)]
    c = s["coordinates"]
    return dict(
        variant=variant,
        layer=layer,
        u=directions[layer] if random_u is None else random_u,
        coordinate=c[task] + cell["overshoot"] * (c[task] - c["OFF"]),
        clip=s["clip"],
    )


def serializable(job):
    return {k: v for k, v in job.items() if k not in ("session", "control")}


def append(out, row):
    with (out / "records.jsonl").open("a") as f:
        f.write(json.dumps(row, allow_nan=False) + "\n")


def setup(engine, bank, directions, stats, out, log):
    cells, chosen = [], {}
    for variant in VARIANTS:
        for layer in LAYERS:
            for overshoot in (0.0, 0.5):
                cell = dict(variant=variant, layer=layer, overshoot=overshoot)
                jobs = []
                for i, values in enumerate(bank):
                    for task in ("A", "B"):
                        jobs.append(
                            dict(
                                stage="setup",
                                example=i,
                                values=values,
                                target=task,
                                **cell,
                                ids=engine.encode(
                                    TEMPLATE.format(prompt=prompt(values))
                                ),
                                session=engine.session(),
                                hook_positions=[],
                                control=control(variant, cell, task, directions, stats),
                            )
                        )
                cell_started = time.monotonic()
                engine.run_jobs(jobs)
                cell_seconds = time.monotonic() - cell_started
                scores = {
                    t: sum(
                        j["score"]["value_exact"][t] for j in jobs if j["target"] == t
                    )
                    for t in ("A", "B")
                }
                strict = {
                    t: sum(
                        j["score"]["strict_exact"][t] for j in jobs if j["target"] == t
                    )
                    for t in ("A", "B")
                }
                both = sum(
                    all(
                        j["score"]["value_exact"][j["target"]]
                        for j in jobs
                        if j["example"] == i
                    )
                    for i in range(32)
                )
                cell.update(
                    exact=scores,
                    strict=strict,
                    both=both,
                    breakage=sum(j["score"]["breakage"] for j in jobs),
                    n=32,
                )
                cell["seconds"] = cell_seconds
                cells.append(cell)
                if len(cells) == 1:
                    write_json(
                        out / "pilot.json",
                        dict(
                            decisions=64,
                            seconds=cell_seconds,
                            projected_3904_decisions_seconds=cell_seconds * 61,
                            note="Setup projection; retained batches differ.",
                        ),
                    )
                for j in jobs:
                    append(out, serializable(j))
                write_json(out / "cells.json", cells)
                log(
                    f"setup {variant} L{layer} overshoot={overshoot}: {scores}, "
                    f"both={both}, breakage={cell['breakage']}"
                )
        chosen[variant] = max(
            [c for c in cells if c["variant"] == variant],
            key=lambda c: (
                c["both"],
                -c["breakage"],
                min(c["exact"].values()),
                sum(c["exact"].values()),
                -c["layer"],
                -c["overshoot"],
            ),
        )
    write_json(out / "selected.json", chosen)
    return cells, chosen


def test(engine, bank, directions, stats, chosen, out, log, arms=ARMS):
    import torch

    rows, random_tensors = [], {}
    for base in range(0, 64, 8):
        sessions = {
            (ep, arm): engine.session() for ep in range(base, base + 8) for arm in arms
        }
        random_dirs = {}
        for ep, arm in sessions:
            if arm.endswith("_shuffled"):
                variant = arm.removesuffix("_shuffled")
                gen = torch.Generator().manual_seed(
                    seed(f"{out.name}:{variant}:shuffled:{ep}")
                )
                u = torch.randn(engine.cfg.d_model, generator=gen, dtype=torch.float32)
                u /= u.norm()
                random_tensors[f"{ep}:{variant}"] = u
                random_dirs[ep, arm] = u.cuda()
        for index, step in enumerate(STEPS):
            jobs = []
            for (ep, arm), session in sessions.items():
                target = TASKS[index]
                if arm.endswith("_swapped") and target != "OFF":
                    target = "B" if target == "A" else "A"
                variant = next((v for v in VARIANTS if arm.startswith(v + "_")), None)
                ctrl = None
                if variant and index != 4 and (variant == "sustained" or index != 1):
                    ctrl = control(
                        variant,
                        chosen[variant],
                        target,
                        directions,
                        stats,
                        random_dirs.get((ep, arm)),
                    )
                cue = (
                    target
                    if arm == "fresh_text" or (arm == "text" and index in (0, 2, 3))
                    else "OFF"
                )
                values = bank[ep * 5 + index]
                j = dict(
                    stage="test",
                    episode=ep,
                    arm=arm,
                    checkpoint=step,
                    target=target,
                    values=values,
                    cue=cue,
                    session=session,
                    control=ctrl,
                    hook_positions=[],
                    cache_before=session["cache"].length,
                    context_token_ids=[],
                    ids=engine.encode(
                        TEMPLATE.format(prompt=prompt(values, cue, clear=index == 4))
                    ),
                )
                jobs.append(j)
            if index == 1 and arms != ("fresh_text",):
                # Split wrapper/filler/acknowledgement; hook only the filler.
                for text, is_filler in (
                    ("<|im_start|>user\n", False),
                    (None, True),
                    (
                        "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\nNoted.<|im_end|>\n",
                        False,
                    ),
                ):
                    subjobs = []
                    for j in jobs:
                        ids = engine.filler if is_filler else engine.encode(text)
                        j["context_token_ids"].extend(ids)
                        subjobs.append(
                            dict(
                                session=j["session"],
                                ids=ids,
                                control=j["control"] if is_filler else None,
                                hook_positions=j["hook_positions"],
                            )
                        )
                    engine.run_jobs(subjobs, generate=False, phase="filler")
            engine.run_jobs(jobs)
            closure_jobs = []
            for j in jobs:
                closure = engine.encode(
                    "\n" if j["terminal_token_id"] is not None else "<|im_end|>\n"
                )
                j["closing_token_ids"] = closure
                closure_jobs.append(
                    dict(
                        session=j["session"],
                        ids=closure,
                        control=None,
                        hook_positions=[],
                    )
                )
            engine.run_jobs(closure_jobs, generate=False)
            for j in jobs:
                j["cache_after"] = j["session"]["cache"].length
                j["history_sha256"] = hashlib.sha256(
                    json.dumps(j["session"]["history"]).encode()
                ).hexdigest()
                row = serializable(j)
                rows.append(row)
                append(out, row)
            if arms == ("fresh_text",):
                sessions = {(ep, arm): engine.session() for ep, arm in sessions}
        log(f"test {arms}: {base + 8}/64 episodes")
        write_json(
            out
            / (
                "fresh-text-progress.json"
                if arms == ("fresh_text",)
                else "test-progress.json"
            ),
            {arm: aggregate([r for r in rows if r["arm"] == arm]) for arm in arms},
        )
    if random_tensors:
        torch.save(random_tensors, out / "random-directions.pt")
    return rows


def run_trunk(trunk, bank, budget):
    from stencil import determinism  # noqa: F401
    import torch
    from tokenizers import Tokenizer
    from stencil.qwen3 import Qwen3, Qwen3Config

    out = OUT / trunk
    out.mkdir()
    started = time.monotonic()
    summary = dict(
        trunk=trunk,
        seed=SEED,
        status="running",
        pid=os.getpid(),
        source_commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        script_sha256=sha(Path(__file__)),
        pre_reading_sha256=sha(OUT / "before-run.md"),
        started_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        layer_indexing="zero-based layer input",
        budget_minutes_total=90,
        lineage=(
            "Extraction on fit only; selection on setup only; test disjoint "
            "by unordered operand set, across trunks too. No training or "
            "benchmark access."
        ),
        numerics=(
            "greedy; bf16 HF-compatible; fp32 extraction/replacement; "
            "pad-free batches <=8"
        ),
    )
    write_json(out / "examples.json", bank)
    write_json(out / "summary.json", summary)
    (out / "records.jsonl").touch()

    def log(message):
        print(
            f"[{(time.monotonic() - budget.started) / 60:.2f} total min] "
            f"{trunk}: {message}",
            flush=True,
        )

    try:
        budget.check()
        config_dir = ROOT / f"models/qwen3-{trunk}-hf"
        cfg = Qwen3Config.from_hf(config_dir / "config.json")
        tok = Tokenizer.from_file(str(config_dir / "tokenizer.json"))
        with torch.device("meta"):
            model = Qwen3(cfg)
        weights = torch.load(
            ROOT / f"models/qwen3-{trunk}.pt",
            mmap=True,
            weights_only=True,
            map_location="cpu",
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
        engine = Engine(model, tok, cfg, budget)
        with torch.inference_mode():
            directions, stats = fit(engine, bank["fit"], out)
            summary["fit_stats"] = stats
            log("128 paired triples extracted at all four layers")
            cells, chosen = setup(engine, bank["setup"], directions, stats, out, log)
            summary.update(cells=cells, selected=chosen)
            write_json(out / "summary.json", summary)
            rows = test(engine, bank["test"], directions, stats, chosen, out, log)
            arms = {
                arm: aggregate([r for r in rows if r["arm"] == arm]) for arm in ARMS
            }
            if arms["text"]["joint"] < 48:
                log(
                    f"retained text joint {arms['text']['joint']}/64; "
                    "running fixed fresh-history diagnostic"
                )
                fresh = test(
                    engine,
                    bank["test"],
                    directions,
                    stats,
                    chosen,
                    out,
                    log,
                    ("fresh_text",),
                )
                arms["fresh_text"] = aggregate(fresh)
            summary.update(
                arms=arms,
                variants={v: reading(arms, v) for v in VARIANTS},
                status="complete",
            )
    except StopProbe as exc:
        summary.update(status="partial", stop_reason=str(exc))
        log(str(exc))
    except Exception as exc:
        summary.update(status="error", stop_reason=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        records = [
            json.loads(line)
            for line in (out / "records.jsonl").read_text().splitlines()
        ]
        summary["arms"] = {
            arm: aggregate(
                [r for r in records if r["stage"] == "test" and r["arm"] == arm]
            )
            for arm in (*ARMS, "fresh_text")
            if any(r.get("arm") == arm for r in records)
        }
        summary["variants"] = {v: reading(summary["arms"], v) for v in VARIANTS}
        summary["elapsed_seconds"] = time.monotonic() - started
        summary["total_budget_elapsed_seconds"] = time.monotonic() - budget.started
        summary["peak_cuda_allocated_bytes"] = torch.cuda.max_memory_allocated()
        write_json(out / "summary.json", summary)
        log(f"{summary['status']}; {summary['variants']}")
    del model, engine, directions
    gc.collect()
    torch.cuda.empty_cache()
    return summary["status"]


def self_test():
    import torch
    from types import SimpleNamespace
    from stencil.qwen3 import KVCache

    # Exercise the actual batch consumer with unequal EOS lengths, then a
    # retained-history continuation. Fake KV stores token IDs for exact audits.
    engine = Engine.__new__(Engine)
    engine.cfg = SimpleNamespace(n_layer=1)
    engine.Cache = KVCache
    engine.eos, engine.batch_id = {8}, 0
    engine.tok = SimpleNamespace(decode=lambda ids, **kw: str(ids))

    def fake_forward(ids, cache, hook=None):
        tokens = torch.tensor(ids)
        hidden = torch.zeros((*tokens.shape, 3))
        if hook:
            hook[1](hidden)
        values = tokens[:, None, :, None].float()
        for name in ("k", "v"):
            old = getattr(cache, name)[0]
            getattr(cache, name)[0] = (
                values if old is None else torch.cat((old, values), dim=2)
            )
        cache.length += tokens.shape[1]
        logits = torch.zeros((*tokens.shape, 10))
        for row in range(len(ids)):
            first = int(cache.k[0][row, 0, 0, 0])
            nxt = 8 if cache.length >= first + 2 else 7
            logits[row, -1, nxt] = 1
        return logits

    engine.forward = fake_forward
    jobs = [
        dict(
            session=engine.session(),
            ids=[i, 0],
            values=[1, 2],
            hook_positions=[],
            control=dict(
                layer=0,
                variant="sustained",
                u=torch.tensor([1.0, 0.0, 0.0]),
                coordinate=2.0,
                clip=1.0,
            ),
        )
        for i in (1, 3)
    ]
    engine.run_jobs(jobs)
    for j, n in zip(jobs, (1, 3), strict=True):
        assert j["generated_token_ids"] == [7] * n
        assert j["terminal_token_id"] == 8
        assert j["session"]["history"] == j["ids"] + [7] * n + [8]
        assert j["session"]["cache"].k[0].flatten().tolist() == j["session"]["history"]
        assert [h["position"] for h in j["hook_positions"]] == list(range(1, n + 3))
        assert all(
            h["delta"] == 1 and h["after"] == 1 and h["orthogonal_cast_norm"] == 0
            for h in j["hook_positions"]
        )
        j.update(ids=[0], control=None)
    engine.run_jobs(jobs, generate=False)
    assert [j["session"]["history"][-1] for j in jobs] == [0, 0]
    pulse = dict(
        hook_positions=[],
        control=dict(
            layer=0,
            variant="one_shot",
            u=torch.tensor([1.0, 0.0, 0.0]),
            coordinate=2.0,
            clip=1.0,
        ),
    )
    assert engine.hook([pulse], "decode", 10) is None
    assert engine.hook([pulse], "filler", 10) is None
    before = torch.randn(1, 4, 3)
    after = engine.hook([pulse], "prompt", 0)[1](before)
    assert torch.equal(before[:, :3], after[:, :3])
    assert torch.equal(before[:, :, 1:], after[:, :, 1:])
    data = banks()
    all_values = [v for b in data.values() for split in b.values() for v in split]
    assert len(all_values) == 960
    assert len({tuple(sorted(v)) for v in all_values}) == 960
    v = [4, -2, 7, 0, 1]
    for text in (
        "[-2,0,1,4,7]",
        '```json\n["-2", "0", "1", "4", "7"]\n```',
        "Answer: [-2,0,1,4,7]",
    ):
        assert score(text, v)["value_exact"]["A"]
    assert score("[1,0,7,-2,4]", v)["value_exact"]["B"]
    assert score("[1,0,7,-2,4] [4,-2,7,0,1]", v)["breakage"]
    a = dict(
        n=64,
        joint=40,
        induction=8,
        breakage=2,
        clear_impositions=2,
        checkpoints={"SET": {"exact": 40}},
    )
    arms = {k: dict(a) for k in ARMS}
    arms["text"]["joint"] = 48
    assert reading(arms, "one_shot") == "PASS"
    arms["one_shot_correct"]["joint"] = 39
    assert reading(arms, "one_shot") == "MARGINAL"
    arms["one_shot_shuffled"]["induction"] = 9
    assert reading(arms, "one_shot") == "FAIL"
    arms["text"]["joint"] = 47
    assert reading(arms, "one_shot") == "INELIGIBLE"
    arms["one_shot_correct"]["n"] = 63
    assert reading(arms, "one_shot") == "PARTIAL"
    print("CPU bank, scorer and fixed-reading boundary checks passed.", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    if args.run:
        active = gpu_pids()
        if active:
            raise RuntimeError(f"GPU busy; aborting: {sorted(active)}")
        if any((OUT / t).exists() for t in ("4b", "1.7b")):
            raise RuntimeError("Refusing to overwrite existing trunk artifacts")
        (OUT / "before-run.md").write_bytes((OUT / "README.md").read_bytes())
        budget = Budget()
        data = banks()
        for trunk in ("4b", "1.7b"):
            if run_trunk(trunk, data[trunk], budget) != "complete":
                break
        write_json(
            OUT / "runtime.json",
            dict(total_seconds=time.monotonic() - budget.started, cap_seconds=5400),
        )


if __name__ == "__main__":
    main()
