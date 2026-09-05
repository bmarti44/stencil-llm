#!/usr/bin/env python3
"""Unregistered Q4: operand-free four-column KV extraction and retained episodes."""

# ruff: noqa: I001, E402, E501
from __future__ import annotations

import argparse
import ast
import gc
import hashlib
import json
import os
import random
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from focus1_probe import gpu_pids, score as strict_score, write_json

OUT = ROOT / "results/quick-checks/check32-kv"
SEED, N, MAX_NEW = 32040, 64, 64
ARMS = ("correct", "swapped", "shuffled", "off", "text", "layers_ge12")
STEPS = ("SET", "HOLD", "SWITCH", "BACK", "CLEAR")
TARGETS = ("A", "A", "B", "A", "OFF")
CUES = {
    "A": "Sort the numbers from smallest to largest.",
    "B": "Write the numbers in reverse order.",
}
BASE = "<|im_start|>system\nRespond with only a JSON array of integers.\n"
USER = "<|im_start|>user\n"
ASSISTANT = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
LINEAGE = (
    "Fit-on=none; extraction only: 32 operand/answer-free cue paraphrases "
    "per A/B/OFF. Evaluation: 320 distinct synthetic operand sets, seed "
    "32040, disjoint from extraction. No benchmarks, fitting or training."
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def episodes():
    rng, seen, bank = random.Random(SEED), set(), []
    for ep in range(N):
        lists = []
        while len(lists) < 5:
            v = rng.sample(range(-20, 21), rng.randint(5, 8))
            key = tuple(sorted(v))
            if key in seen or v in (sorted(v), sorted(v, reverse=True)):
                continue
            seen.add(key)
            lists.append(v)
        bank.append(dict(episode=ep, values=lists))
    return bank


def paraphrases():
    starts = {
        "A": [
            "Sort the numbers",
            "Arrange the integers",
            "Order the values",
            "Reorder the numbers",
            "Sort the given integers",
            "Arrange the supplied values",
            "Order the provided numbers",
            "Reorder the integer list",
        ],
        "B": [
            "Write the numbers",
            "Write the integers",
            "Return the values",
            "Return the numbers",
            "Present the given integers",
            "Present the supplied values",
            "Write the provided numbers",
            "Return the integer list",
        ],
        "OFF": [
            "The context is available",
            "The conversation is open",
            "The session is ready",
            "This is a neutral message",
            "The interface is available",
            "The exchange is open",
            "The text is present",
            "This is a background note",
        ],
    }
    endings = {
        "A": [
            "from smallest to largest.",
            "in ascending numerical order.",
            "from least to greatest.",
            "in increasing numerical order.",
        ],
        "B": [
            "in reverse input order.",
            "in the reverse of their given order.",
            "with the last input first and the first input last.",
            "by reversing their original sequence.",
        ],
        "OFF": [
            "for this session.",
            "in this conversation.",
            "at the present time.",
            "within this exchange.",
        ],
    }
    rng = random.Random(SEED + 100000)
    result = {}
    for task in starts:
        result[task] = [f"{a} {b}" for a in starts[task] for b in endings[task]]
        rng.shuffle(result[task])
        assert len(set(result[task])) == 32
        assert all(not re.search(r"\d", s) for s in result[task])
    return result


def score(text, values, *, truncated=False, rep4=0.0):
    strict = strict_score(text, values, truncated=truncated, rep4=rep4)
    parsed = None
    # Exactly one bracketed list; never silently accept multiple candidate answers.
    candidates = re.findall(r"\[[^\[\]]*\]", text)
    if len(candidates) == 1:
        try:
            candidate = ast.literal_eval(candidates[0])
            if isinstance(candidate, list) and all(
                type(v) is int
                or (isinstance(v, str) and re.fullmatch(r"[+-]?\d+", v.strip()))
                for v in candidate
            ):
                parsed = [int(v) for v in candidate]
        except (ValueError, SyntaxError, TypeError):
            pass
    expected = {"A": sorted(values), "B": list(reversed(values)), "OFF": values}
    label = next((t for t, v in expected.items() if parsed == v), "other")
    repetition = rep4 > 0.2 or (parsed is not None and len(set(parsed)) != len(parsed))
    strict_valid = not strict["invalid_json"] and not strict["integer_schema_invalid"]
    return dict(
        parsed=parsed,
        label=label,
        value_exact={t: parsed == v for t, v in expected.items()},
        strict_exact={
            t: strict_valid and strict["parsed"] == v for t, v in expected.items()
        },
        truncated=truncated,
        repetition=repetition,
        breakage=truncated or repetition or parsed is None,
        strict=strict,
        rep4=rep4,
    )


def summarize(records):
    result = {}
    for arm in ARMS:
        rows = [r for r in records if r["arm"] == arm]
        grouped = {}
        for r in rows:
            grouped.setdefault(r["episode"], {})[r["step"]] = r
        full = [g for g in grouped.values() if len(g) == 5]
        target = ("B", "B", "A", "B") if arm == "swapped" else TARGETS[:4]
        counts = {}
        for step, task in zip(STEPS, (*target, "OFF"), strict=True):
            chosen = [r for r in rows if r["step"] == step]
            counts[step] = dict(
                n=len(chosen),
                target=task,
                exact=sum(r["score"]["value_exact"][task] for r in chosen),
                strict=sum(r["score"]["strict_exact"][task] for r in chosen),
            )
        result[arm] = dict(
            completed_episodes=len(full),
            decisions=counts,
            joint=sum(
                all(
                    g[s]["score"]["value_exact"][t]
                    for s, t in zip(STEPS[:4], target, strict=True)
                )
                for g in full
            ),
            strict_joint=sum(
                all(
                    g[s]["score"]["strict_exact"][t]
                    for s, t in zip(STEPS[:4], target, strict=True)
                )
                for g in full
            ),
            any_induction=sum(
                any(g[s]["score"]["label"] in ("A", "B") for s in STEPS[:4])
                for g in full
            ),
            breakage=sum(any(r["score"]["breakage"] for r in g.values()) for g in full),
            clear_impositions=sum(
                g["CLEAR"]["score"]["label"] in ("A", "B") for g in full
            ),
            hold_no_writes=all(
                r["packet_write"] is None for r in rows if r["step"] == "HOLD"
            ),
        )
    return result


def verdict(arms):
    if any(a["completed_episodes"] != N for a in arms.values()):
        return "PARTIAL"
    c, s, noise = arms["correct"], arms["swapped"], arms["shuffled"]
    if arms["text"]["joint"] < 48:
        return "INELIGIBLE"
    if (
        c["joint"] >= 40
        and s["joint"] >= 40
        and noise["any_induction"] <= 8
        and c["breakage"] <= 2
        and c["clear_impositions"] <= 2
    ):
        return "PASS"
    if c["decisions"]["SET"]["exact"] >= 32 and noise["any_induction"] <= 8:
        return "MARGINAL"
    return "FAIL"


class StopRun(RuntimeError):
    pass


class Budget:
    def __init__(self):
        self.started = time.monotonic()
        self.last_check = 0

    def check(self):
        now = time.monotonic()
        if now - self.started >= 5400:
            raise StopRun("90 GPU-minute total cap reached; partial results retained")
        if now - self.last_check > 5:
            self.last_check = now
            active = gpu_pids() - {os.getpid()}
            if active:
                raise StopRun(f"Foreign compute process appeared: {sorted(active)}")


class Engine:
    def __init__(self, model, tok, cfg, torch, budget):
        from stencil.qwen3 import KVCache

        self.model, self.tok, self.cfg = model, tok, cfg
        self.torch, self.budget, self.Cache = torch, budget, KVCache
        self.device = "cuda"
        self.eos = {tok.token_to_id(t) for t in ("<|im_end|>", "<|endoftext|>")}
        assert None not in self.eos
        self.suffix = self.enc(" The context is ready")
        assert len(self.suffix) == 4
        self.positions = list(range(80, 84))
        filler = (
            "The room has a window. Light falls across the wall. "
            "There is a quiet table nearby. The day continues calmly. "
        )
        self.filler = self.enc(filler * 20)[:128]
        assert len(self.filler) == 128
        self.packet, self.stats = {}, {}

    def enc(self, text):
        return self.tok.encode(text).ids

    def prefix(self, cue=""):
        ids = self.enc(BASE + cue)
        assert len(ids) <= 80
        return ids + self.enc(" ") * (80 - len(ids)) + self.suffix

    def forward(self, ids, cache, batch=2):
        from stencil.qwen3 import prefill_with_eviction

        self.budget.check()
        tokens = self.torch.tensor([ids] * batch, device=self.device)
        result, _, _, _ = prefill_with_eviction(
            self.model, cache, tokens, history_end=0, evict_range=None
        )
        assert cache.length == cache.k[0].shape[2]
        return result

    def extract(self, out):
        donor_records = []
        for task, cues in paraphrases().items():
            sums = None
            for i, cue in enumerate(cues):
                cache = self.Cache(self.cfg)
                ids = self.prefix(cue)
                self.forward(ids, cache, batch=1)
                kv = [
                    [
                        getattr(cache, kind)[layer][:, :, 80:84].float().cpu().clone()
                        for layer in range(self.cfg.n_layer)
                    ]
                    for kind in ("k", "v")
                ]
                if sums is None:
                    sums = kv
                else:
                    for x in range(2):
                        for layer in range(self.cfg.n_layer):
                            sums[x][layer].add_(kv[x][layer])
                donor_records.append(
                    dict(
                        task=task,
                        prompt_id=f"extract/{task}/{i}",
                        cue=cue,
                        prompt_token_ids=ids,
                        edit_positions=self.positions,
                    )
                )
                with (out / "extraction.jsonl").open("a") as f:
                    f.write(json.dumps(donor_records[-1]) + "\n")
            self.packet[task] = [[v.div_(32) for v in layer] for layer in sums]
            assert all(
                self.torch.isfinite(v).all() for ls in self.packet[task] for v in ls
            )
            print(f"extracted {task}: 32 operand-free cues", flush=True)
        for layer in range(self.cfg.n_layer):
            stats = {}
            for task in self.packet:
                stats[task] = {
                    kind: float(self.packet[task][i][layer].norm())
                    for i, kind in enumerate(("k", "v"))
                }
            a = self.torch.cat([self.packet["A"][i][layer].flatten() for i in range(2)])
            b = self.torch.cat([self.packet["B"][i][layer].flatten() for i in range(2)])
            stats["cosine_A_B"] = float(
                self.torch.nn.functional.cosine_similarity(a, b, dim=0)
            )
            self.stats[str(layer)] = stats
        self.torch.save(self.packet, out / "packets-fp32.pt")
        write_json(out / "packet-stats.json", self.stats)
        self.packet = {
            t: [[v.cuda().to(self.torch.bfloat16) for v in layer] for layer in ls]
            for t, ls in self.packet.items()
        }
        return donor_records

    def edit(self, cache, packet, row=0, start_layer=0):
        for i, kind in enumerate(("k", "v")):
            for layer in range(start_layer, self.cfg.n_layer):
                getattr(cache, kind)[layer][row : row + 1, :, 80:84].copy_(
                    packet[i][layer]
                )

    def random_packets(self, episode):
        generator = self.torch.Generator(device="cpu").manual_seed(
            SEED + 900000 + episode
        )
        packets, norms = {}, {}
        for task in ("A", "B"):
            packets[task] = [[], []]
            norms[task] = {}
            for layer in range(self.cfg.n_layer):
                norms[task][str(layer)] = {}
                for i, kind in enumerate(("k", "v")):
                    reference = self.packet[task][i][layer].float().cpu()
                    noise = self.torch.randn(reference.shape, generator=generator)
                    noise.mul_(reference.norm() / noise.norm())
                    value = noise.to(device=self.device, dtype=self.torch.bfloat16)
                    packets[task][i].append(value)
                    norms[task][str(layer)][kind] = dict(
                        reference_norm=float(reference.norm()),
                        fp32_random_norm=float(noise.norm()),
                        applied_norm=float(value.float().norm()),
                    )
        return packets, norms

    def audit(self, cache):
        audit = []
        for layer in range(self.cfg.n_layer):
            row = dict(layer=layer)
            for kind in ("k", "v"):
                kv = getattr(cache, kind)[layer]
                delta = (kv[0].float() - kv[1].float()).abs()
                outside = self.torch.cat([delta[:, :80], delta[:, 84:]], dim=1)
                row[kind] = dict(
                    all_max_abs=float(delta.max()),
                    packet_max_abs=float(delta[:, 80:84].max()),
                    outside_max_abs=float(outside.max()),
                    all_bitwise_equal=self.torch.equal(kv[0], kv[1]),
                    packet_bitwise_equal=self.torch.equal(
                        kv[0, :, 80:84], kv[1, :, 80:84]
                    ),
                )
            audit.append(row)
        return audit

    def run_episode(self, entry, arm, emit):
        from stencil.function_vectors import repeated_4gram_fraction

        ep = entry["episode"]
        cache = self.Cache(self.cfg)
        start_layer = 12 if arm == "layers_ge12" else 0
        prefix = self.prefix(CUES["A"] if arm == "text" else "")
        self.forward(prefix, cache)
        # OFF shadow is a teacher-forced, same-layout clean OFF replay.
        if arm != "text":
            self.edit(cache, self.packet["OFF"], row=1, start_layer=start_layer)
        noise, noise_norms = self.random_packets(ep) if arm == "shuffled" else ({}, {})
        packet_snapshot = None
        all_ids = list(prefix)
        for index, (step, task, values) in enumerate(
            zip(STEPS, TARGETS, entry["values"], strict=True)
        ):
            begun = time.monotonic()
            before = cache.length
            write = None
            if arm != "text" and step != "HOLD" and (arm != "off" or step == "SET"):
                actual = (
                    "OFF"
                    if arm == "off" or task == "OFF"
                    else ("B" if task == "A" else "A")
                    if arm == "swapped"
                    else task
                )
                packet = (
                    noise[actual]
                    if arm == "shuffled" and actual != "OFF"
                    else self.packet[actual]
                )
                self.edit(cache, packet, start_layer=start_layer)
                write = dict(
                    task=actual,
                    positions=self.positions,
                    layers=list(range(start_layer, self.cfg.n_layer)),
                    kind="random"
                    if arm == "shuffled" and actual != "OFF"
                    else "extracted",
                )
            if step == "SET":
                packet_snapshot = [
                    [v[0:1, :, 80:84].clone() for v in getattr(cache, kind)]
                    for kind in ("k", "v")
                ]
            audit = self.audit(cache) if step == "CLEAR" else None
            filler_ids = []
            if step == "HOLD":
                filler_ids = (
                    self.enc(USER)
                    + self.filler
                    + self.enc("<|im_end|>\n<|im_start|>assistant\nNoted.<|im_end|>\n")
                )
                self.forward(filler_ids, cache)
                all_ids.extend(filler_ids)
                assert write is None
                assert all(
                    self.torch.equal(v[0:1, :, 80:84], packet_snapshot[i][layer])
                    for i, kind in enumerate(("k", "v"))
                    for layer, v in enumerate(getattr(cache, kind))
                )
            instruction = (
                "Copy these integers in the given order."
                if step == "CLEAR"
                else "Process these integers."
            )
            if arm == "text" and step in ("SWITCH", "BACK"):
                instruction = CUES[task]
            prompt = (
                instruction
                + " Output only a JSON array. Integers: "
                + json.dumps(values)
            )
            query = self.enc(
                ("<|im_end|>\n" if index == 0 else "") + USER + prompt + ASSISTANT
            )
            logits = self.forward(query, cache)
            all_ids.extend(query)
            output, eos_id = [], None
            next_id = int(logits[0, -1].argmax())
            # Unlike a terminal generation, every emitted token (including EOS) is cached.
            while len(output) < MAX_NEW:
                if next_id in self.eos:
                    eos_id = next_id
                    self.forward([next_id], cache)
                    all_ids.append(next_id)
                    break
                output.append(next_id)
                logits = self.forward([next_id], cache)
                all_ids.append(next_id)
                next_id = int(logits[0, -1].argmax())
            truncated = eos_id is None
            if truncated:
                # Explicitly close a capped answer; do not pretend this EOS was generated.
                forced_end = self.tok.token_to_id("<|im_end|>")
                self.forward([forced_end], cache)
                all_ids.append(forced_end)
            else:
                forced_end = None
            newline = self.enc("\n")
            self.forward(newline, cache)
            all_ids.extend(newline)
            text = self.tok.decode(output, skip_special_tokens=False)
            assert cache.length == len(all_ids)
            hold_retained = None
            if step == "HOLD":
                hold_retained = all(
                    self.torch.equal(v[0:1, :, 80:84], packet_snapshot[i][layer])
                    for i, kind in enumerate(("k", "v"))
                    for layer, v in enumerate(getattr(cache, kind))
                )
                assert hold_retained
            emit(
                dict(
                    episode=ep,
                    arm=arm,
                    step=step,
                    target=task,
                    values=values,
                    prompt_id=f"ep{ep:02d}/{step}",
                    prefix_token_ids=prefix if index == 0 else None,
                    prompt=prompt,
                    prompt_token_ids=query,
                    filler_token_ids=filler_ids,
                    generated_token_ids=output,
                    eos_token_id=eos_id,
                    forced_end_token_id=forced_end,
                    trailing_token_ids=newline,
                    text=text,
                    score=score(
                        text,
                        values,
                        truncated=truncated,
                        rep4=repeated_4gram_fraction(output),
                    ),
                    packet_write=write,
                    edit_positions=self.positions,
                    packet_norms_file="packet-stats.json",
                    random_packet_norms=noise_norms if index == 0 else None,
                    hold_packet_bitwise_retained=hold_retained,
                    clear_residual_audit=audit,
                    audit_baseline="identical text replay"
                    if arm == "text"
                    else "OFF exact-token replay",
                    cache_length_before=before,
                    cache_length_after=cache.length,
                    history_sha256=hashlib.sha256(
                        json.dumps(all_ids).encode()
                    ).hexdigest(),
                    elapsed_seconds=time.monotonic() - begun,
                )
            )


def run_trunk(trunk, budget):
    import torch
    from tokenizers import Tokenizer
    from stencil.qwen3 import Qwen3, Qwen3Config

    out = OUT / trunk
    out.mkdir(parents=True, exist_ok=True)
    if (out / "summary.json").exists():
        raise RuntimeError(f"Refusing overwrite: {out}")
    begun = time.monotonic()
    records = []
    data = dict(
        trunk=trunk,
        seed=SEED,
        lineage=LINEAGE,
        status="running",
        pid=os.getpid(),
        source_commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        script_sha256=sha(Path(__file__)),
        reading_sha256=sha(OUT / "README.md"),
        numerics="bf16 frozen weights, hf_compatible=True, fp32 packet means; batch 2",
        max_new_tokens=MAX_NEW,
        budget_total_minutes=90,
        packet_positions=list(range(80, 84)),
        audit_semantics="simultaneous batch-row OFF replay, identical tokens and call boundaries",
    )

    def save():
        data["elapsed_seconds"] = time.monotonic() - begun
        data["total_elapsed_seconds"] = time.monotonic() - budget.started
        data["arms"] = summarize(records)
        data["verdict"] = verdict(data["arms"])
        data["records_count"] = len(records)
        if torch.cuda.is_initialized():
            data["peak_cuda_allocated_bytes"] = torch.cuda.max_memory_allocated()
        audits = [
            r["clear_residual_audit"] for r in records if r["clear_residual_audit"]
        ]
        data["audit_count"] = len(audits)
        data["residuals"] = {}
        for arm in ARMS:
            selected = [
                r["clear_residual_audit"]
                for r in records
                if r["arm"] == arm and r["clear_residual_audit"]
            ]
            if selected:
                data["residuals"][arm] = [
                    dict(
                        layer=layer,
                        **{
                            kind: {
                                field: max(a[layer][kind][field] for a in selected)
                                for field in (
                                    "all_max_abs",
                                    "packet_max_abs",
                                    "outside_max_abs",
                                )
                            }
                            for kind in ("k", "v")
                        },
                    )
                    for layer in range(len(selected[0]))
                ]
        write_json(out / "summary.json", data)

    def emit(row):
        records.append(row)
        with (out / "records.jsonl").open("a") as f:
            f.write(json.dumps(row, allow_nan=False) + "\n")
        if len(records) % 30 == 0:
            save()
            print(
                f"{trunk}: {len(records)}/1920 decisions, "
                f"{data['elapsed_seconds'] / 60:.2f} min",
                flush=True,
            )

    save()
    try:
        budget.check()
        cfgdir = ROOT / f"models/qwen3-{trunk}-hf"
        cfg = Qwen3Config.from_hf(cfgdir / "config.json")
        tok = Tokenizer.from_file(str(cfgdir / "tokenizer.json"))
        with torch.device("meta"):
            model = Qwen3(cfg)
        weights = torch.load(
            ROOT / f"models/qwen3-{trunk}.pt",
            mmap=True,
            map_location="cpu",
            weights_only=True,
        )
        model.load_state_dict(weights, strict=True, assign=True)
        del weights
        for module in model.modules():
            if hasattr(module, "hf_compatible"):
                module.hf_compatible = True
        model = model.to(device="cuda", dtype=torch.bfloat16).eval()
        model.requires_grad_(False)
        torch.manual_seed(SEED)
        torch.cuda.reset_peak_memory_stats()
        engine = Engine(model, tok, cfg, torch, budget)
        bank = episodes()
        write_json(out / "episodes.json", bank)
        data["filler_body_token_ids"] = engine.filler
        data["filler_body_text"] = tok.decode(engine.filler)
        data["layers"] = cfg.n_layer
        with torch.inference_mode():
            engine.extract(out)
            data["packet_stats"] = engine.stats
            data["packets_sha256"] = sha(out / "packets-fp32.pt")
            save()
            for entry in bank:
                episode_started = time.monotonic()
                for arm in ARMS:
                    engine.run_episode(entry, arm, emit)
                if entry["episode"] == 0:
                    seconds = time.monotonic() - episode_started
                    data["pilot"] = dict(
                        seconds_per_six_arm_episode=seconds,
                        projected_64_episode_seconds=seconds * N,
                        peak_bytes=torch.cuda.max_memory_allocated(),
                    )
                    save()
                    print(f"{trunk} pilot: {data['pilot']}", flush=True)
        data["status"] = "complete"
    except StopRun as error:
        data["status"], data["stop_reason"] = "partial", str(error)
        print(str(error), flush=True)
    except Exception as error:
        data["status"], data["error"] = "error", repr(error)
        raise
    finally:
        save()
    return data


def report():
    path = OUT / "README.md"
    original = path.read_text().split("## Results\n")[0]
    lines = ["## Results", ""]
    for trunk in ("4b", "1.7b"):
        summary_path = OUT / trunk / "summary.json"
        if not summary_path.exists():
            lines += [
                f"### {trunk}",
                "",
                "**PARTIAL** — trunk not started within the shared cap.",
                "",
            ]
            continue
        s = json.loads(summary_path.read_text())
        if s.get("status") == "aborted_before_gpu":
            lines += [
                f"### {trunk}: **NOT RUN**",
                "",
                s["stop_reason"],
                "",
                "No packet, task or residual measurements; zero GPU-minutes.",
                "",
            ]
            continue
        lines += [
            f"### {trunk}: **{s['verdict']}**",
            "",
            "| Arm | n | SET | HOLD (no reapply) | SWITCH | BACK | Joint | Strict joint | CLEAR copy | Impositions | Breakage | Any induction |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for name, a in s["arms"].items():
            d = a["decisions"]
            values = [
                name,
                a["completed_episodes"],
                *(d[t]["exact"] for t in STEPS[:4]),
                a["joint"],
                a["strict_joint"],
                d["CLEAR"]["exact"],
                a["clear_impositions"],
                a["breakage"],
                a["any_induction"],
            ]
            lines.append("| " + " | ".join(map(str, values)) + " |")
        lines += [
            "",
            "Counts use each arm’s completed episodes; decision denominators for partial runs are in summary.json. Swapped target is B/B/A/B; other task columns target A/A/B/A. Any induction means either task on any of the first four decisions.",
            "",
        ]
        c, t = s["arms"]["correct"], s["arms"]["text"]
        lines += [
            f"The operand-free packet completed {c['joint']}/{c['completed_episodes']} full task sequences; HOLD alone was {c['decisions']['HOLD']['exact']}/{c['decisions']['HOLD']['n']} with zero reapplications. The text-cue bar completed {t['joint']}/{t['completed_episodes']}. CLEAR imposed a task in {c['clear_impositions']} episodes. The fixed reading is **{s['verdict']}**; this test therefore "
            + (
                "supports transferable retained task state on this trunk, subject to the residual audit."
                if s["verdict"] == "PASS"
                else "does not establish reliable set/hold/switch/clear by this extracted packet."
            )
            + f" Runtime: {s['elapsed_seconds'] / 60:.2f} GPU-minutes.",
            "",
        ]
        lines += [
            "Per-layer residual maxima over CLEAR episodes (exact-token OFF replay):",
            "",
            "| Arm | Max restored K | Max restored V | Max outside K | Max outside V |",
            "|---|---:|---:|---:|---:|",
        ]
        for arm, audit in s.get("residuals", {}).items():
            vals = [
                max(r[k][f] for r in audit)
                for f in ("packet_max_abs", "outside_max_abs")
                for k in ("k", "v")
            ]
            lines.append(
                "| " + arm + " | " + " | ".join(f"{v:.6g}" for v in vals) + " |"
            )
        lines += [
            "",
            "Every layer is retained in summary.json and each CLEAR record. Zero restored-column difference does not imply zero downstream residual. Packet norms and cosines for every layer are in packet-stats.json; extraction cue IDs and exact tokens are in extraction.jsonl; packet tensors are in packets-fp32.pt.",
            "",
        ]
        if s.get("stop_reason"):
            lines += [s["stop_reason"], ""]
    path.write_text(original + "\n".join(lines) + "\n")


def self_test():
    assert len(episodes()) == 64
    flat = [v for e in episodes() for v in e["values"]]
    assert len({tuple(sorted(v)) for v in flat}) == 320
    for values in flat:
        assert len({tuple(values), tuple(sorted(values)), tuple(reversed(values))}) == 3
    values = [4, -2, 7, 0, 1]
    for text in (
        "[-2,0,1,4,7]",
        '```json\n["-2", "0", "1", "4", "7"]\n```',
        "Here: [-2, 0, 1, 4, 7].",
    ):
        assert score(text, values)["label"] == "A"
    assert score("[1,0,7,-2,4]", values)["label"] == "B"
    assert score("[2,0,1,4,7]", values)["label"] == "other"
    assert score("[-2,0,1,4,7] [4,-2,7,0,1]", values)["breakage"]
    assert score("[True,0,1,4,7]", values)["breakage"]
    assert score("[1,1]", values)["breakage"]
    assert not score('["-2","0","1","4","7"]', values)["strict_exact"]["A"]
    assert len(paraphrases()["OFF"]) == 32
    # Exercise real cache writes, retained columns and residual audits on CPU.
    import torch
    from types import SimpleNamespace
    from stencil.qwen3 import KVCache

    engine = object.__new__(Engine)
    engine.torch, engine.cfg = torch, SimpleNamespace(n_layer=2)
    cache = KVCache(engine.cfg)
    cache.k = [torch.zeros(2, 1, 90, 3) for _ in range(2)]
    cache.v = [v.clone() for v in cache.k]
    packet = [[torch.ones(1, 1, 4, 3) * (i + 1) for _ in range(2)] for i in range(2)]
    engine.edit(cache, packet)
    audit = engine.audit(cache)
    assert audit[0]["k"]["packet_max_abs"] == 1
    assert audit[0]["k"]["outside_max_abs"] == 0
    engine.edit(cache, packet, row=1)
    assert all(
        r["k"]["all_bitwise_equal"] and r["v"]["all_bitwise_equal"]
        for r in engine.audit(cache)
    )
    cache.k[1][0, :, 85] = 3
    assert engine.audit(cache)[1]["k"]["outside_max_abs"] == 3
    assert engine.audit(cache)[1]["k"]["packet_bitwise_equal"]
    # Boundary checks through the actual verdict consumer.
    arms = {
        a: dict(
            completed_episodes=64,
            joint=40,
            any_induction=0,
            breakage=0,
            clear_impositions=0,
            decisions={"SET": {"exact": 40}},
        )
        for a in ARMS
    }
    arms["text"]["joint"] = 48
    assert verdict(arms) == "PASS"
    arms["correct"]["joint"] = 39
    assert verdict(arms) == "MARGINAL"
    arms["shuffled"]["any_induction"] = 9
    assert verdict(arms) == "FAIL"
    arms["text"]["joint"] = 47
    assert verdict(arms) == "INELIGIBLE"
    arms["off"]["completed_episodes"] = 63
    assert verdict(arms) == "PARTIAL"
    # Run all five retained decisions through the production engine on a fake CPU trunk.
    from tokenizers import Tokenizer

    tok = Tokenizer.from_file(str(ROOT / "models/qwen3-4b-hf/tokenizer.json"))
    answer = tok.encode("[4, -2, 7, 0, 1]").ids
    eos_id = tok.token_to_id("<|im_end|>")

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
                        .expand(-1, 1, -1, 3)
                        .clone()
                    )
                    if old is not None:
                        new += old.mean(dim=(1, 2, 3), keepdim=True) * 0.001
                    getattr(cache, kind)[layer] = (
                        new if old is None else torch.cat((old, new), dim=2)
                    )
            cache.length += length
            if length > 1:
                self.cursor = 0
            next_id = answer[self.cursor] if self.cursor < len(answer) else eos_id
            self.cursor += 1
            logits = torch.zeros(batch, 1, eos_id + 1)
            logits[:, :, next_id] = 1
            return logits

    fake = Engine(
        FakeModel(),
        tok,
        SimpleNamespace(n_layer=14),
        torch,
        SimpleNamespace(check=lambda: None),
    )
    fake.device = "cpu"
    fake.packet = {
        task: [
            [torch.full((1, 1, 4, 3), float(i + offset)) for _ in range(14)]
            for i in range(2)
        ]
        for task, offset in (("A", 1), ("B", 3), ("OFF", 0))
    }
    captured = []
    for arm in ARMS:
        fake.run_episode(episodes()[0], arm, captured.append)
    assert len(captured) == 30
    for arm in ARMS:
        rows = [r for r in captured if r["arm"] == arm]
        assert [r["step"] for r in rows] == list(STEPS)
        assert rows[1]["packet_write"] is None
        assert rows[1]["hold_packet_bitwise_retained"]
        assert len(rows[1]["filler_token_ids"]) > 128
        assert all(r["eos_token_id"] == eos_id for r in rows)
        assert all(r["generated_token_ids"] == answer for r in rows)
        assert all(r["forced_end_token_id"] is None for r in rows)
        assert all(
            a["k"]["packet_bitwise_equal"] and a["v"]["packet_bitwise_equal"]
            for a in rows[-1]["clear_residual_audit"]
        )
    assert summarize(captured)["correct"]["completed_episodes"] == 1
    assert verdict(summarize(captured)) == "PARTIAL"
    print(
        "CPU self-test passed: scorer, banks, cache edits/audit, verdict boundaries, "
        "all six complete fake-trunk retained-cache episodes"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    if args.report:
        report()
    if args.run:
        active = gpu_pids()
        if active:
            raise RuntimeError(f"GPU busy; aborting without signals: {sorted(active)}")
        budget = Budget()
        for trunk in ("4b", "1.7b"):
            result = run_trunk(trunk, budget)
            gc.collect()
            import torch

            torch.cuda.empty_cache()
            if result["status"] != "complete":
                break
        report()


if __name__ == "__main__":
    main()
