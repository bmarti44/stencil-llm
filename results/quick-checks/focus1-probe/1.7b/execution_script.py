#!/usr/bin/env python3
"""UNREGISTERED quick check 31; never an input to registered FOCUS-1 selection."""

# ruff: noqa: I001
from __future__ import annotations

import argparse
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
sys.path.insert(0, str(ROOT / "src"))
OUT = ROOT / "results/quick-checks/focus1-probe"
SEED = 31031
LAYERS = (12, 16, 20)
ALPHAS = (0.5, 1.0, 2.0)
TASKS = ("asc", "desc")
MAX_NEW = 48
TEMPLATE = (
    "<|im_start|>user\n{prompt}<|im_end|>\n"
    "<|im_start|>assistant\n<think>\n\n</think>\n\n"
)
LINEAGE = (
    "UNREGISTERED quick check 31. Vector fit-on: 32 synthetic operand triples "
    "from probe seed 31031; evaluated-on: separate 32 competence and 16 steering "
    "lists, disjoint by unordered operand set. No benchmark inputs or recorded "
    "benchmark responses. No fitting, training, or selection for registered "
    "FOCUS-1; best-cell choice is descriptive within this probe only."
)


def write_json(path, payload):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def banks():
    rng = random.Random(SEED)
    seen = set()
    result = {}
    for name, count in (("competence", 32), ("vectors", 32), ("steering", 16)):
        rows = []
        while len(rows) < count:
            values = rng.sample(range(-20, 21), rng.randint(5, 8))
            key = tuple(sorted(values))
            if key in seen or values in (sorted(values), sorted(values, reverse=True)):
                continue
            seen.add(key)
            rows.append(values)
        result[name] = rows
    return result


def prompt(values, task):
    order = "ascending" if task == "asc" else "descending"
    instruction = (
        "Process these integers."
        if task == "off"
        else f"Sort these integers in {order} order."
    )
    return f"{instruction} Output only a JSON array. Integers: {json.dumps(values)}"


def score(text, values, *, truncated=False, rep4=0.0):
    try:
        parsed = json.loads(text)
        valid = isinstance(parsed, list) and all(type(x) is int for x in parsed)
    except (json.JSONDecodeError, ValueError):
        parsed, valid = None, False
    label = "other"
    if valid:
        if parsed == sorted(values):
            label = "asc"
        elif parsed == sorted(values, reverse=True):
            label = "desc"
        elif parsed == values:
            label = "copy"
    repetition = rep4 > 0.2 or (valid and len(parsed) != len(set(parsed)))
    return dict(
        label=label,
        parsed=parsed,
        invalid_json=not valid,
        truncated=truncated,
        repetition=repetition,
        breakage=not valid or truncated or repetition,
    )


def aggregate(rows, task=None, injected_task=None):
    counts = Counter(r["score"]["label"] for r in rows)
    n = len(rows)
    result = dict(
        n=n,
        counts={key: counts[key] for key in (*TASKS, "copy", "other")},
        rates={
            key: counts[key] / n if n else None for key in (*TASKS, "copy", "other")
        },
    )
    for flag in ("invalid_json", "truncated", "repetition", "breakage"):
        count = sum(r["score"][flag] for r in rows)
        result[flag] = dict(count=count, rate=count / n if n else None)
    result["copy_or_other_rate"] = (counts["copy"] + counts["other"]) / n if n else None
    if task:
        other = "desc" if task == "asc" else "asc"
        result.update(
            target_task=task,
            follows_target_count=counts[task],
            follows_target_rate=counts[task] / n if n else None,
            follows_other_rate=counts[other] / n if n else None,
            injected_task=injected_task,
            follows_injected_task_rate=(
                counts[injected_task] / n if n and injected_task else None
            ),
        )
    return result


def gpu_pids():
    output = subprocess.check_output(
        ["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"], text=True
    )
    return {int(line.strip()) for line in output.splitlines() if line.strip()}


class StopProbe(RuntimeError):
    pass


class Budget:
    def __init__(self, minutes):
        self.started = time.monotonic()
        self.deadline = self.started + 60 * minutes
        self.last_check = 0.0

    def check(self):
        now = time.monotonic()
        if now >= self.deadline:
            raise StopProbe(
                "30 GPU-minute wall-clock budget exhausted; partial results"
            )
        if now - self.last_check >= 5:
            self.last_check = now
            others = gpu_pids() - {os.getpid()}
            if others:
                raise StopProbe(f"Other GPU compute process appeared: {sorted(others)}")


def make_summary(data):
    summary = {k: v for k, v in data.items() if k not in ("records", "banks")}
    records = data["records"]
    summary["competence"] = {
        task: aggregate(
            [
                r
                for r in records
                if r["stage"] == "competence" and r["prompt_task"] == task
            ],
            task if task != "off" else None,
        )
        for task in (*TASKS, "off")
    }
    off = [r for r in records if r["stage"] == "steering_off"]
    summary["steering_off"] = aggregate(off)
    cells = []
    for layer in LAYERS:
        for alpha in ALPHAS:
            cell = dict(layer=layer, alpha=alpha, tasks={})
            for task in TASKS:
                other = "desc" if task == "asc" else "asc"

                def pick(injected, layer=layer, alpha=alpha):
                    return [
                        r
                        for r in records
                        if r["stage"] == "steering"
                        and r["layer"] == layer
                        and r["alpha"] == alpha
                        and r["injected_task"] == injected
                    ]

                arms = dict(
                    correct=aggregate(pick(task), task, task),
                    swapped=aggregate(pick(other), task, other),
                    OFF=aggregate(off, task),
                )
                for arm, injected in (("correct", task), ("swapped", other)):
                    treated = {r["example"]: r for r in pick(injected)}
                    pairs = [
                        (treated[r["example"]], r)
                        for r in off
                        if r["example"] in treated
                    ]
                    arms[arm]["paired_vs_OFF"] = dict(
                        n=len(pairs),
                        wins=sum(
                            a["score"]["label"] == task and b["score"]["label"] != task
                            for a, b in pairs
                        ),
                        losses=sum(
                            a["score"]["label"] != task and b["score"]["label"] == task
                            for a, b in pairs
                        ),
                    )
                cell["tasks"][task] = arms
            correct = [cell["tasks"][t]["correct"] for t in TASKS]
            cell["complete"] = all(r["n"] == 16 for r in correct) and len(off) == 16
            cell["both_target_threshold"] = cell["complete"] and all(
                r["follows_target_count"] >= 12 and r["breakage"]["count"] <= 1
                for r in correct
            )
            cells.append(cell)
    summary["cells"] = cells
    complete = [c for c in cells if c["complete"]]

    # Shared layer/alpha ranked by weaker task, total target hits, lower breakage.
    def rank(cell):
        arms = [cell["tasks"][t]["correct"] for t in TASKS]
        return (
            min(a["follows_target_count"] for a in arms),
            sum(a["follows_target_count"] for a in arms),
            -sum(a["breakage"]["count"] for a in arms),
        )

    safe_pass = [c for c in complete if c["both_target_threshold"]]
    best = max(safe_pass or complete, key=rank) if complete else None
    summary["best_cell"] = best
    summary["reading"] = (
        "FEASIBLE"
        if safe_pass
        else "MARGINAL"
        if data["status"] != "complete" or (best and rank(best)[0] >= 8)
        else "INFEASIBLE"
    )
    summary["reading_rule"] = (
        "FEASIBLE: same layer/alpha correct arms achieve both tasks >=12/16, "
        "each breakage <=1/16. OFF and paired flips reported separately; a task "
        "already the default need not improve. Otherwise MARGINAL if weaker-task "
        "success >=8/16 or run partial; INFEASIBLE otherwise. Descriptive only."
    )
    summary["delay"] = {
        task: aggregate(
            [
                r
                for r in records
                if r["stage"] == "delay" and r["injected_task"] == task
            ],
            task,
            task,
        )
        for task in TASKS
    }
    return summary


def run(args):
    # All heavy imports and GPU operations remain behind main().
    from stencil import determinism  # noqa: F401

    import torch
    from tokenizers import Tokenizer

    from stencil.function_vectors import mean_difference, repeated_4gram_fraction
    from stencil.qwen3 import KVCache, Qwen3, Qwen3Config

    out = OUT / args.trunk
    if (out / "summary.json").exists():
        raise RuntimeError(f"Refusing to overwrite existing run: {out}")
    active = gpu_pids()
    if active:
        raise RuntimeError(f"GPU is busy before launch: {sorted(active)}")
    out.mkdir(parents=True, exist_ok=True)
    data = dict(
        trunk=args.trunk,
        seed=SEED,
        lineage=LINEAGE,
        status="running",
        banks=banks(),
        records=[],
        vector_stats={},
        pid=os.getpid(),
        numerics="hf_compatible=True on trunk, blocks, and all RMSNorms; bf16 weights",
        vector_dtype="float32; addition computed in fp32 then cast to residual dtype",
        layers=list(LAYERS),
        layer_indexing="zero-based layer-input residual",
        alphas=list(ALPHAS),
        max_new_tokens=MAX_NEW,
        greedy=True,
        prompt_template=TEMPLATE,
        budget_minutes=30,
        arm_reuse=(
            "Each actual vector generation reused as correct/swapped; "
            "OFF reused across cells"
        ),
        delay_semantics=(
            "Prompt final-position hook only; no decode hook; prompt KV retained"
        ),
        source_commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    )
    write_json(
        out / "examples.json", dict(seed=SEED, lineage=LINEAGE, banks=data["banks"])
    )
    budget = Budget(30)

    def save():
        data["elapsed_seconds"] = time.monotonic() - budget.started
        if torch.cuda.is_initialized():
            data["peak_cuda_allocated_bytes"] = torch.cuda.max_memory_allocated()
        write_json(out / "summary.json", make_summary(data))

    def log(message):
        print(
            f"[{time.monotonic() - budget.started:.1f}s] {args.trunk}: {message}",
            flush=True,
        )

    try:
        save()
        config_dir = ROOT / f"models/qwen3-{args.trunk}-hf"
        cfg = Qwen3Config.from_hf(config_dir / "config.json")
        tokenizer = Tokenizer.from_file(str(config_dir / "tokenizer.json"))
        eos = {tokenizer.token_to_id(t) for t in ("<|im_end|>", "<|endoftext|>")}
        assert None not in eos
        with torch.device("meta"):
            model = Qwen3(cfg)
        weights = torch.load(
            ROOT / f"models/qwen3-{args.trunk}.pt",
            map_location="cpu",
            weights_only=True,
            mmap=True,
        )
        model.load_state_dict(weights, strict=True, assign=True)
        del weights
        for module in model.modules():
            if hasattr(module, "hf_compatible"):
                module.hf_compatible = True
        model = model.to(device="cuda", dtype=torch.bfloat16).eval()
        model.requires_grad_(False)
        torch.manual_seed(SEED)
        assert all(p.dtype == torch.bfloat16 for p in model.parameters())
        budget.check()
        log("model loaded; starting competence")
        vectors = {}

        def tokens(values, task):
            return torch.tensor(
                [tokenizer.encode(TEMPLATE.format(prompt=prompt(values, task))).ids],
                device="cuda",
            )

        def generate(values, task, *, vector=None, layer=None, alpha=None, delay=False):
            started = time.monotonic()
            budget.check()
            cache = KVCache(cfg)
            ids = tokens(values, task)
            hook_calls = []

            def hook(position):
                if vector is None or (delay and position > 0):
                    return None

                def inject(hidden):
                    hook_calls.append(position)
                    result = hidden.clone()
                    result[:, -1, :] = (hidden[:, -1, :].float() + alpha * vector).to(
                        hidden.dtype
                    )
                    return result

                return layer, inject

            output = []
            with torch.inference_mode():
                logits = model(ids, cache=cache, residual_hook=hook(0))
                next_id = int(logits[0, -1].argmax())
                while next_id not in eos and len(output) < MAX_NEW:
                    budget.check()
                    output.append(next_id)
                    if len(output) == MAX_NEW:
                        break
                    logits = model(
                        torch.tensor([[next_id]], device="cuda"),
                        cache=cache,
                        residual_hook=hook(len(output)),
                    )
                    next_id = int(logits[0, -1].argmax())
            truncated = len(output) == MAX_NEW
            text = tokenizer.decode(output, skip_special_tokens=False)
            rep4 = repeated_4gram_fraction(output)
            expected_hooks = (
                []
                if vector is None
                else [0]
                if delay
                else list(range(len(output) if truncated else len(output) + 1))
            )
            assert hook_calls == expected_hooks, (hook_calls, expected_hooks)
            return dict(
                text=text,
                generated_token_ids=output,
                n_generated=len(output),
                prompt_token_ids=ids[0].tolist(),
                prompt=prompt(values, task),
                rep4=rep4,
                hook_positions=hook_calls,
                elapsed_seconds=time.monotonic() - started,
                score=score(text, values, truncated=truncated, rep4=rep4),
            )

        def record(stage, index, values, task="off", **kwargs):
            metadata = {k: kwargs[k] for k in ("layer", "alpha") if k in kwargs}
            injected = kwargs.pop("injected_task", None)
            row = dict(
                id=len(data["records"]),
                stage=stage,
                example=index,
                values=values,
                prompt_task=task,
                injected_task=injected,
                **metadata,
                **generate(values, task, **kwargs),
            )
            data["records"].append(row)
            with (out / "records.jsonl").open("a") as stream:
                stream.write(json.dumps(row, allow_nan=False) + "\n")
            if len(data["records"]) == 1:
                data["pilot"] = dict(
                    seconds=row["elapsed_seconds"],
                    tokens=row["n_generated"],
                    projected_432_generation_seconds=432 * row["elapsed_seconds"],
                    tokens_per_second=row["n_generated"] / row["elapsed_seconds"],
                )
                log(f"pilot: {data['pilot']}")
            if len(data["records"]) % 16 == 0:
                save()
                log(f"{stage}: {len(data['records'])} generations recorded")

        for index, values in enumerate(data["banks"]["competence"]):
            for task in (*TASKS, "off"):
                record("competence", index, values, task)
        log("extracting 32 operand-paired triples")
        states = {task: {layer: [] for layer in LAYERS} for task in (*TASKS, "off")}
        extraction_records = []
        for index, values in enumerate(data["banks"]["vectors"]):
            for task in (*TASKS, "off"):
                budget.check()
                ids = tokens(values, task)
                with torch.inference_mode():
                    logits, captured = model(ids, capture_hidden=LAYERS)
                for layer in LAYERS:
                    states[task][layer].append(
                        captured[layer][0, -1].float().cpu().clone()
                    )
                extraction_records.append(
                    dict(
                        example=index,
                        task=task,
                        values=values,
                        prompt=prompt(values, task),
                        prompt_token_ids=ids[0].tolist(),
                    )
                )
                del logits, captured
            if (index + 1) % 8 == 0:
                torch.save(states, out / "extraction-states.pt")
                write_json(out / "extraction.json", extraction_records)
                log(f"extracted {index + 1}/32 triples")
        for layer in LAYERS:
            for task in TASKS:
                vectors[task, layer] = mean_difference(
                    states[task][layer], states["off"][layer]
                ).cuda()
                assert vectors[task, layer].dtype == torch.float32
                assert torch.isfinite(vectors[task, layer]).all()
                assert torch.count_nonzero(vectors[task, layer])
            data["vector_stats"][str(layer)] = dict(
                asc_norm=float(vectors["asc", layer].norm()),
                desc_norm=float(vectors["desc", layer].norm()),
                cosine=float(
                    torch.nn.functional.cosine_similarity(
                        vectors["asc", layer], vectors["desc", layer], dim=0
                    )
                ),
            )
        torch.save(
            {f"{task}:{layer}": v.cpu() for (task, layer), v in vectors.items()},
            out / "vectors.pt",
        )
        save()
        log(f"vector stats: {data['vector_stats']}")
        for index, values in enumerate(data["banks"]["steering"]):
            record("steering_off", index, values)
        for layer in LAYERS:
            for alpha in ALPHAS:
                for task in TASKS:
                    for index, values in enumerate(data["banks"]["steering"]):
                        record(
                            "steering",
                            index,
                            values,
                            vector=vectors[task, layer],
                            injected_task=task,
                            layer=layer,
                            alpha=alpha,
                        )
                cell = next(
                    c
                    for c in make_summary(data)["cells"]
                    if c["layer"] == layer and c["alpha"] == alpha
                )
                log(
                    f"L={layer} alpha={alpha}: "
                    + str(
                        {
                            t: (
                                cell["tasks"][t]["correct"]["follows_target_count"],
                                cell["tasks"][t]["correct"]["breakage"]["count"],
                            )
                            for t in TASKS
                        }
                    )
                )
        best = make_summary(data)["best_cell"]
        data["delay_cell"] = dict(layer=best["layer"], alpha=best["alpha"])
        for task in TASKS:
            for index, values in enumerate(data["banks"]["steering"]):
                record(
                    "delay",
                    index,
                    values,
                    vector=vectors[task, best["layer"]],
                    injected_task=task,
                    delay=True,
                    **data["delay_cell"],
                )
        data["status"] = "complete"
    except StopProbe as exc:
        data.update(status="partial", stop_reason=str(exc))
        log(str(exc))
    except Exception as exc:
        data.update(status="error", stop_reason=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        save()
        log(f"{data['status']}; {make_summary(data)['reading']}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trunk", choices=("1.7b", "4b"), required=True)
    args = parser.parse_args(argv)
    run(args)


if __name__ == "__main__":
    main()
