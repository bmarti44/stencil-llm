#!/usr/bin/env python3
"""Check 41b: decision-position gradient readout and first-T-token MLP intervention."""

# ruff: noqa: E501
from __future__ import annotations

import argparse
import fcntl
import importlib.util
import json
import random
import threading
import time
from collections import Counter
from pathlib import Path

ROOT = Path("/home/bmarti44/stencil-llm")
OUT = ROOT / "results/quick-checks/check41b"
SEED, LIMIT, CAP = 41042, 5400, 256
KS, GAINS, TS = (50, 200, 800), (1, 3, 8), (1, 4, 16)
ARMS = ("correct", "swapped", "shuffled", "OFF", "text-cue")
TOKENS = {
    "JavaScript": ["function", "const", "let", "//", "async"],
    "Python": ["def", "import", "class", "#", "from"],
}
READING = """# Quick check 41b — causal decision-position neurons (2026-09-05)

Prewritten reading, frozen before model execution; seed 41042; dense Qwen3-4B.
Data lineage: no fitting, training, parameter updates or benchmark input reads.
Gradient readout on 32 uncued synthetic fit tasks; cued JS/Python and uncued
activations from those same tasks only. Cell selection on 8 separate setup tasks;
evaluation on 32 fresh uncued tasks, disjoint IDs and full prompts. The check41
operation bank/parser/checkers are reused; operation families overlap. New check41b
function names prevent exact prompt overlap with previous checks. No sealed input.

Decision position is the final prompt position predicting generated token 1.
c = logsumexp(logits of literal JS tokens function,const,let,//,async) minus
logsumexp(logits of literal Python tokens def,import,class,#,from). Each literal
must encode as one token, with no leading whitespace variants. Preserve token IDs,
per-task top-1 defaults, actual first tokens and first eight tokens. A code fence
can be the actual first token: do not silently move the readout to a later token.
For all 36 layers, use the actual SiLU(gate)*up input to down_proj. Average
x * dc/dx at that position over 32 uncued tasks; save per-task gradients, x and
attributions, plus cued-minus-uncued differences and language-cued means. Rank by
absolute signed mean attribution, stable flat-index ties; k in {50,200,800}.
Report sign/layer distributions and intersections with all check41 frequency sets.

Grid: 8 setup tasks x [k={50,200,800}, T={1,4,16}, multiplicative g={1,3,8}
or cued-mean clamp (no g)] = 36 cells, 288 generations. Positive attribution
neurons multiply by 1+g and negative by 1-g toward JS; swapped reverses sign.
Clamp sets selected neurons to their fit-task cued-JS mean; swapped uses the
cued-Python mean. Shuffled selects random other neurons matched per-layer sign
counts, with their own cued means for clamp. Exactly the first T token-predicting
positions are modified: final prompt position then T-1 decode positions; release
from prediction T+1 onward. Earlier cached changes persist naturally after release.
Pick most valid JS, then least breakage; residual ties lower k, lower T,
multiplicative before clamp, lower gain. Freeze before any screen output.

Screen: all 32 fresh SET tasks, each in correct/swapped/shuffled/OFF/text-cue arms.
If correct SET >=12/32, extend first 16 SET trajectories with their own retained
histories through HOLD/SWITCH/BACK/CLEAR on rotated screen tasks. Reapply first-T
intervention on each active request; SWITCH targets Python, BACK JavaScript,
CLEAR has no intervention or new cue. OFF never has a cue; text-cue explicitly
names the target each active request. No neutral step required in this check.
Parse language, reuse coarse task check and breakage; generated programs never run.
Log c and paired OFF shift for fresh SET, plus same-history unmodified c/shift on
every request (text-cue shift compared with identical history minus current cue).

FIXED READING: POSSIBLE if correct valid JavaScript >=20/32, correct breakage <=2/32,
and shuffled valid JavaScript <=4/32 at SET. Otherwise MARGINAL if correct valid
JavaScript >=12/32; else NOT POSSIBLE. An incomplete screen is PARTIAL, never a
negative finding. On NOT POSSIBLE state plainly: the language decision is not
carried by identifiable MLP neurons at the decision position on this trunk under
this registered selector and intervention. This bounded result cannot exclude
other contrast definitions, sites or distributed representations.

Foreground only; no process signals. Wait behind check41 and check40b, check40b
RUNNING.flag included; poll resources every 600 seconds. Queue on .review.lock
to serialize with the existing check42 waiter. Write our RUNNING.flag only when
holding the GPU slot, remove on exit. 5400-second allocation cap including model
load, pilot, attribution and generation. Cooperative per-forward/per-token stop,
30-second cleanup reserve. No outcome-based redesign or rerun of the screen.
CPU tests verify autograd and first-T hooks through real tiny Qwen3 consumers.
The first setup generation is the charged pilot; record timing and full-design
projection before the remaining matrix. If the projection exceeds the cap, stop
with PARTIAL instead of shrinking the design after seeing outcomes.
"""


def plumbing():
    spec = importlib.util.spec_from_file_location(
        "check41_reuse", ROOT / "scripts/focus_check41.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def bank(base):
    rng = random.Random(SEED)
    rows = []
    for variant in range(3):
        for family, description, witness in base.TASKS:
            name = f"{family}_c41b_{variant + 1}"
            rows.append(
                dict(
                    id=name,
                    name=name,
                    family=family,
                    witness=witness,
                    prompt=f"Write a function named {name} that "
                    + description.format(n=rng.randrange(3, 20))
                    + ".",
                )
            )
    rng.shuffle(rows)
    result = dict(fit=rows[:32], setup=rows[32:40], screen=rows[40:72])
    assert len({r["prompt"] for group in result.values() for r in group}) == 72
    return result


def cells():
    return [
        dict(k=k, T=t, variant=v, gain=g)
        for k in KS
        for t in TS
        for v, gains in [("multiply", GAINS), ("clamp", (0,))]
        for g in gains
    ]


def choose(rows):
    return min(
        rows,
        key=lambda c: (
            -c["javascript"],
            c["broken"],
            c["k"],
            c["T"],
            c["variant"] != "multiply",
            c["gain"],
        ),
    )


def verdict(arms):
    if any(arms[a]["n"] != 32 for a in ARMS):
        return "PARTIAL"
    c, s = arms["correct"], arms["shuffled"]
    if c["javascript"] >= 20 and c["broken"] <= 2 and s["javascript"] <= 4:
        return "POSSIBLE"
    return "MARGINAL" if c["javascript"] >= 12 else "NOT POSSIBLE"


class Hooks:
    def __init__(self, projections):
        self.capture = False
        self.xs = {}
        self.action = None
        self.position = 0
        self.counts = Counter()
        self.handles = [
            p.register_forward_pre_hook(self.hook(i)) for i, p in enumerate(projections)
        ]

    def hook(self, layer):
        def apply(module, inputs):
            x = inputs[0]
            if self.capture:
                self.xs[layer] = x
            a = self.action
            if a is None or self.position >= a["T"] or layer not in a["layers"]:
                return None
            indices, values = a["layers"][layer]
            y = x.clone()
            if a["variant"] == "multiply":
                y[:, -1, indices] = x[:, -1, indices] * values
            else:
                y[:, -1, indices] = values
            self.counts[(layer, self.position)] += 1
            return (y,) + inputs[1:]

        return apply

    def close(self):
        for h in self.handles:
            h.remove()


class Engine:
    def __init__(self, p, start):
        import torch
        from transformers import AutoTokenizer, Qwen3ForCausalLM

        self.torch, self.p = torch, p
        torch.set_num_threads(4)
        torch.manual_seed(SEED)
        self.deadline = start + LIMIT
        self.device = torch.device("cuda:0")
        self.cap = CAP
        self.tokenizer = AutoTokenizer.from_pretrained(p.MODEL, local_files_only=True)
        self.model = (
            Qwen3ForCausalLM.from_pretrained(
                p.MODEL,
                dtype=torch.bfloat16,
                attn_implementation="sdpa",
                local_files_only=True,
            )
            .to(self.device)
            .eval()
        )
        self.model.requires_grad_(False)
        self.hooks = Hooks([layer_idx.mlp.down_proj for layer_idx in self.model.model.layers])
        self.shape = (len(self.model.model.layers), self.model.config.intermediate_size)
        self.ids = {}
        for lang, literals in TOKENS.items():
            encoded = [
                self.tokenizer.encode(t, add_special_tokens=False) for t in literals
            ]
            assert all(len(x) == 1 for x in encoded), encoded
            self.ids[lang] = [x[0] for x in encoded]
        assert len(set(sum(self.ids.values(), []))) == 10
        eos = self.model.generation_config.eos_token_id
        self.eos = set(eos if isinstance(eos, list) else [eos]) | {
            self.tokenizer.eos_token_id
        }
        self.load_seconds = time.monotonic() - start

    def budget(self):
        if time.monotonic() >= self.deadline - 30:
            raise self.p.BudgetStop("cooperative 30-second cleanup reserve")

    def contrast(self, logits):
        z = logits[0, -1].float()
        return z[self.ids["JavaScript"]].logsumexp(0) - z[self.ids["Python"]].logsumexp(
            0
        )

    def input_ids(self, messages):
        return self.torch.tensor(
            [self.p.encode_messages(self.tokenizer, messages)], device=self.device
        )

    def decision(self, messages, gradient=False):
        self.budget()
        torch, h = self.torch, self.hooks
        h.action, h.capture, h.xs = None, True, {}
        ids = self.input_ids(messages)
        with torch.enable_grad() if gradient else torch.no_grad():
            embeds = (
                self.model.get_input_embeddings()(ids).detach().requires_grad_(gradient)
            )
            result = self.model(inputs_embeds=embeds, use_cache=False, logits_to_keep=1)
            c = self.contrast(result.logits)
            xs = [h.xs[i] for i in range(self.shape[0])]
            x = torch.stack([v[0, -1].detach().float().cpu() for v in xs])
            data = dict(x=x)
            if gradient:
                assert c.requires_grad and all(v.requires_grad for v in xs)
                grads = torch.autograd.grad(c, xs, allow_unused=False)
                grad = torch.stack([v[0, -1].detach().float().cpu() for v in grads])
                assert torch.isfinite(grad).all() and torch.count_nonzero(grad) > 0
                data.update(gradient=grad, attribution=x * grad)
            top = int(result.logits[0, -1].argmax())
            record = dict(
                c=float(c.detach()),
                top1_id=top,
                top1=self.tokenizer.decode([top]),
                input_token_ids=ids[0].tolist(),
                history=messages,
            )
        h.xs, h.capture = {}, False
        return record, data

    def generate(self, messages, action=None, baseline_messages=None):
        self.budget()
        torch, h = self.torch, self.hooks
        started = time.monotonic()
        ids = self.input_ids(messages)
        h.action, h.capture, h.counts = None, False, Counter()
        generated, ended = [], False
        with torch.inference_mode():
            baseline = self.model(
                input_ids=self.input_ids(baseline_messages or messages),
                use_cache=False,
                logits_to_keep=1,
            )
            c_off = float(self.contrast(baseline.logits))
            default_top = int(baseline.logits[0, -1].argmax())
            del baseline
            h.action, h.position = action, 0
            result = self.model(input_ids=ids, use_cache=True, logits_to_keep=1)
            c = float(self.contrast(result.logits))
            for i in range(self.cap):
                self.budget()
                token = int(result.logits[0, -1].argmax())
                generated.append(token)
                if token in self.eos:
                    ended = True
                    break
                if i + 1 < self.cap:
                    h.position = i + 1
                    result = self.model(
                        input_ids=torch.tensor([[token]], device=self.device),
                        past_key_values=result.past_key_values,
                        use_cache=True,
                        logits_to_keep=1,
                    )
            if self.device.type == "cuda":
                torch.cuda.synchronize()
        counts = [
            {"layer": layer_idx, "prediction_index": pos, "calls": n}
            for (layer_idx, pos), n in sorted(h.counts.items())
        ]
        if action:
            expected = min(action["T"], len(generated))
            assert all(
                h.counts[(layer_idx, pos)] == 1
                for layer_idx in action["layers"]
                for pos in range(expected)
            )
            assert len(h.counts) == len(action["layers"]) * expected
        h.action = None
        return dict(
            text=self.tokenizer.decode(generated, skip_special_tokens=True),
            generated_token_ids=generated,
            first_token_id=generated[0],
            first_token=self.tokenizer.decode(generated[:1]),
            first_eight_tokens=[self.tokenizer.decode([t]) for t in generated[:8]],
            default_top1_id=default_top,
            default_top1=self.tokenizer.decode([default_top]),
            c=c,
            c_same_history_off=c_off,
            c_shift=c - c_off,
            intervention_calls=counts,
            input_token_ids=ids[0].tolist(),
            history=messages,
            eos=ended,
            truncated=not ended and len(generated) == self.cap,
            seconds=time.monotonic() - started,
        )


def select(attribution, reference):
    import torch

    layers, width = attribution.shape
    flat = attribution.flatten()
    order = torch.argsort(flat.abs(), descending=True, stable=True)
    sets = {}
    for k in KS:
        indices = order[:k].tolist()
        signs = [1 if flat[i] > 0 else -1 for i in indices]
        assert all(flat[i] != 0 for i in indices)
        gen = torch.Generator().manual_seed(SEED + k)
        shuffled = []
        occupied = set(indices)
        for idx in indices:
            layer = idx // width
            while True:
                candidate = layer * width + int(torch.randint(width, (), generator=gen))
                if candidate not in occupied:
                    occupied.add(candidate)
                    shuffled.append(candidate)
                    break
        sets[str(k)] = dict(
            indices=indices,
            signs=signs,
            shuffled_indices=shuffled,
            layer_counts=[
                dict(
                    layer=layer_idx,
                    positive=sum(
                        i // width == layer_idx and s > 0
                        for i, s in zip(indices, signs, strict=True)
                    ),
                    negative=sum(
                        i // width == layer_idx and s < 0
                        for i, s in zip(indices, signs, strict=True)
                    ),
                )
                for layer_idx in range(layers)
            ],
            frequency_overlap={
                rk: {
                    lang: dict(
                        intersection=len(set(indices) & set(neurons)),
                        fraction_of_causal=len(set(indices) & set(neurons)) / k,
                        fraction_of_frequency=len(set(indices) & set(neurons))
                        / len(neurons),
                    )
                    for lang, neurons in v["flat_indices"].items()
                }
                for rk, v in reference["correct"].items()
            },
        )
    return sets


def action(engine, cell, selected, means, arm, target="JavaScript"):
    if arm in ("OFF", "text-cue") or target is None:
        return None
    torch = engine.torch
    direction = (1 if target == "JavaScript" else -1) * (-1 if arm == "swapped" else 1)
    indices = selected["shuffled_indices" if arm == "shuffled" else "indices"]
    result = dict(T=cell["T"], variant=cell["variant"], layers={})
    width = engine.shape[1]
    for layer_idx in sorted({i // width for i in indices}):
        pairs = [
            (i, s)
            for i, s in zip(indices, selected["signs"], strict=True)
            if i // width == layer_idx
        ]
        idx = torch.tensor([i % width for i, s in pairs], device=engine.device)
        if cell["variant"] == "multiply":
            values = torch.tensor(
                [1 + direction * cell["gain"] * s for i, s in pairs],
                device=engine.device,
                dtype=engine.model.dtype,
            )
        else:
            mean = means["JavaScript" if direction > 0 else "Python"].flatten()
            values = mean[[i for i, s in pairs]].to(
                device=engine.device, dtype=engine.model.dtype
            )
        result["layers"][layer_idx] = (idx, values)
    return result


def aggregate(rows):
    return dict(
        n=len(rows),
        javascript=sum(r["score"]["valid_language"] == "JavaScript" for r in rows),
        python=sum(r["score"]["valid_language"] == "Python" for r in rows),
        task_check=sum(r["score"]["valid_task"] for r in rows),
        javascript_task=sum(
            r["score"]["valid_task"] and r["score"]["valid_language"] == "JavaScript"
            for r in rows
        ),
        broken=sum(r["score"]["broken"] for r in rows),
        first_tokens=dict(Counter(r["first_token"] for r in rows)),
        mean_c=sum(r["c"] for r in rows) / len(rows) if rows else None,
        mean_c_shift=sum(r["c_shift"] for r in rows) / len(rows) if rows else None,
    )


def report(p, rows, start, reason, selected):
    arms = {
        a: aggregate([r for r in rows if r["phase"] == "screen" and r["arm"] == a])
        for a in ARMS
    }
    off = {
        r["task_id"]: r for r in rows if r["phase"] == "screen" and r["arm"] == "OFF"
    }
    for a in ARMS:
        pairs = [
            r
            for r in rows
            if r["phase"] == "screen" and r["arm"] == a and r["task_id"] in off
        ]
        arms[a]["paired_off_mean_c_shift"] = (
            sum(r["c"] - off[r["task_id"]]["c"] for r in pairs) / len(pairs)
            if pairs
            else None
        )
    stages = {
        a: {
            s: aggregate(
                [
                    r
                    for r in rows
                    if r["phase"] == "history" and r["arm"] == a and r["step"] == s
                ]
            )
            for s in ("HOLD", "SWITCH", "BACK", "CLEAR")
        }
        for a in ARMS
    }
    result = dict(
        reading=verdict(arms),
        arms=arms,
        history=stages,
        history_triggered=arms["correct"]["javascript"] >= 12,
        history_complete=all(stages[a][s]["n"] == 16 for a in ARMS for s in stages[a]),
        selected=selected,
        stop_reason=reason,
        gpu_seconds=time.monotonic() - start,
        cap_seconds=LIMIT,
        records=len(rows),
        records_sha256=p.sha(OUT / "records.jsonl"),
    )
    p.write_json(OUT / "summary.json", result)
    table = [
        "\nObserved results\n",
        f"**{result['reading']}**; GPU allocation {result['gpu_seconds']:.1f}/5400 seconds. Stop: {reason}.",
        "\n| Arm | Valid JS | Broken | Coarse task | Mean c | Mean c shift |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for a, v in arms.items():
        table.append(
            f"| {a} | {v['javascript']}/{v['n']} | {v['broken']}/{v['n']} | {v['task_check']}/{v['n']} | {v['mean_c']} | {v['mean_c_shift']} |"
        )
    if result["reading"] == "NOT POSSIBLE":
        table.append(
            "\nThe language decision is not carried by identifiable MLP neurons at the decision position on this trunk under this registered selector and intervention. This result is bounded to the tested contrast and construction."
        )
    table += [
        f"\nFrozen cell: `{json.dumps(selected)}`.",
        f"\nRetained-history trigger: {result['history_triggered']}; complete: {result['history_complete']}.",
        "\nTask checks are the reused coarse syntax/operation witnesses, not executed semantic tests. Attribution arrays and per-task records preserve the gradient readout; neuron-sets.json gives signed layer distributions and check41 overlaps.",
    ]
    (OUT / "README.md").write_text(READING + "\n" + "\n".join(table) + "\n")
    return result


def run(p):
    import numpy as np
    import torch

    assert not (OUT / "records.jsonl").exists(), "Refuse overwrite of model outcomes"
    freeze = json.loads((OUT / "freeze.json").read_text())
    for path, digest in freeze.items():
        assert p.sha(ROOT / path) == digest, path
    tasks = json.loads((OUT / "banks.json").read_text())
    start, rows, chosen, reason, engine = time.monotonic(), [], None, "complete", None
    journal = (OUT / "records.jsonl").open("x")

    def request(
        task, phase, arm, step, episode, cell=None, sets=None, means=None, history=None
    ):
        target = (
            "Python" if step == "SWITCH" else None if step == "CLEAR" else "JavaScript"
        )
        cue = target if arm == "text-cue" else None
        messages = p.base.messages_for(task, cue, history)
        rec = engine.generate(
            messages,
            action(engine, cell, sets, means, arm, target) if cell else None,
            baseline_messages=p.base.messages_for(task, None, history),
        )
        rec.update(
            phase=phase,
            arm=arm,
            step=step,
            episode=episode,
            task_id=task["id"],
            target=target,
            cue=cue,
            cell=cell,
        )
        rec["score"] = p.score(rec["text"], task, rec["truncated"])
        required = (
            "text",
            "generated_token_ids",
            "first_token",
            "c",
            "c_shift",
            "score",
            "history",
            "intervention_calls",
        )
        assert all(k in rec for k in required)
        journal.write(json.dumps(rec) + "\n")
        journal.flush()
        rows.append(rec)
        print(
            json.dumps(
                dict(
                    event="record",
                    n=len(rows),
                    phase=phase,
                    arm=arm,
                    step=step,
                    language=rec["score"]["valid_language"],
                    c_shift=rec["c_shift"],
                    elapsed=time.monotonic() - start,
                )
            ),
            flush=True,
        )
        return rec

    try:
        engine = Engine(p, start)
        p.write_json(
            OUT / "runtime.json",
            dict(
                torch=torch.__version__,
                model_class=type(engine.model).__name__,
                shape=engine.shape,
                dtype=str(engine.model.dtype),
                token_sets=engine.ids,
                load_seconds=engine.load_seconds,
            ),
        )
        (OUT / "attributions").mkdir(exist_ok=True)
        accum = torch.zeros(engine.shape, dtype=torch.float64)
        means = {
            lang: torch.zeros(engine.shape, dtype=torch.float64)
            for lang in ("uncued", "JavaScript", "Python")
        }
        decisions = (OUT / "decision-records.jsonl").open("x")
        for i, task in enumerate(tasks["fit"]):
            raw, data = engine.decision(p.base.messages_for(task), gradient=True)
            accum += data["attribution"].double()
            means["uncued"] += data["x"].double()
            arrays = {k: v.numpy() for k, v in data.items()}
            cued = {}
            for lang in ("JavaScript", "Python"):
                cued[lang], d = engine.decision(p.base.messages_for(task, lang))
                means[lang] += d["x"].double()
                arrays[lang + "_x"] = d["x"].numpy()
                arrays[lang + "_difference"] = (d["x"] - data["x"]).numpy()
            np.savez_compressed(OUT / "attributions" / f"{i:02d}.npz", **arrays)
            # Decode actual uncued first tokens once, retaining complete raw output and parser scores.
            generated = request(task, "fit", "OFF", "SET", i)
            assert generated["first_token_id"] == raw["top1_id"]
            decisions.write(
                json.dumps(
                    dict(
                        task_id=task["id"],
                        uncued=raw,
                        cued=cued,
                        first_tokens=generated["first_eight_tokens"],
                        artifact=f"attributions/{i:02d}.npz",
                    )
                )
                + "\n"
            )
            decisions.flush()
        decisions.close()
        attribution = (accum / 32).float()
        means = {k: (v / 32).float() for k, v in means.items()}
        np.savez_compressed(
            OUT / "attributions" / "aggregate.npz",
            attribution=attribution.numpy(),
            **{k + "_mean": v.numpy() for k, v in means.items()},
            **{
                k + "_difference": (v - means["uncued"]).numpy()
                for k, v in means.items()
                if k != "uncued"
            },
        )
        reference = json.loads(
            (ROOT / "results/quick-checks/check41/neuron-sets.json").read_text()
        )
        sets = select(attribution, reference)
        p.write_json(
            OUT / "neuron-sets.json",
            dict(
                shape=engine.shape,
                correct=sets,
                frequency_reference_sha256=p.sha(
                    ROOT / "results/quick-checks/check41/neuron-sets.json"
                ),
            ),
        )
        grid = []
        for ci, cell in enumerate(cells()):
            rs = []
            for i, task in enumerate(tasks["setup"]):
                rs.append(
                    request(
                        task,
                        "grid",
                        "correct",
                        "SET",
                        i,
                        cell,
                        sets[str(cell["k"])],
                        means,
                    )
                )
                if ci == 0 and i == 0:
                    worst = max(r["seconds"] for r in rows)
                    mean_seconds = sum(r["seconds"] for r in rows) / len(rows)
                    estimate = (
                        time.monotonic()
                        - start
                        + 1.25 * mean_seconds * (288 - 1 + 160 + 320)
                    )
                    projection = dict(
                        pilot_seconds=rs[0]["seconds"],
                        worst_fit_or_pilot_seconds=worst,
                        mean_fit_or_pilot_seconds=mean_seconds,
                        pilot_tokens=len(rs[0]["generated_token_ids"]),
                        projected_seconds_with_optional_history=estimate,
                        peak_memory_bytes=torch.cuda.max_memory_allocated(),
                        cap_seconds=LIMIT,
                    )
                    p.write_json(OUT / "projection.json", projection)
                    with (ROOT / "plan/LEDGER.md").open("a") as ledger:
                        ledger.write(
                            f"\n2026-09-05 — check41b PILOT: {json.dumps(projection)}; fixed design, cooperative cap, no outcome redesign.\n"
                        )
                    if estimate > LIMIT:
                        raise p.BudgetStop("pilot projects full design beyond cap")
            grid.append(dict(**cell, **aggregate(rs)))
            p.write_json(OUT / "grid.json", dict(cells=grid, frozen=False))
        chosen = {k: choose(grid)[k] for k in ("k", "T", "variant", "gain")}
        p.write_json(
            OUT / "grid.json",
            dict(cells=grid, selected=chosen, frozen=True, screen_records_at_freeze=0),
        )
        selected = sets[str(chosen["k"])]
        starts = {}
        for i, task in enumerate(tasks["screen"]):
            for arm in ARMS:
                starts[(i, arm)] = request(
                    task, "screen", arm, "SET", i, chosen, selected, means
                )
        correct = aggregate(
            [r for r in rows if r["phase"] == "screen" and r["arm"] == "correct"]
        )
        if correct["javascript"] >= 12:
            for i in range(16):
                for arm in ARMS:
                    r = starts[(i, arm)]
                    history = r["history"] + [dict(role="assistant", content=r["text"])]
                    for step, offset in [
                        ("HOLD", 7),
                        ("SWITCH", 14),
                        ("BACK", 21),
                        ("CLEAR", 28),
                    ]:
                        r = request(
                            tasks["screen"][(i + offset) % 32],
                            "history",
                            arm,
                            step,
                            i,
                            chosen,
                            selected,
                            means,
                            history,
                        )
                        history = r["history"] + [
                            dict(role="assistant", content=r["text"])
                        ]
    except p.BudgetStop as exc:
        reason = str(exc)
    except Exception as exc:
        reason = f"ERROR {type(exc).__name__}: {exc}"
        raise
    finally:
        journal.close()
        if engine:
            engine.hooks.close()
        result = report(p, rows, start, reason, chosen)
        print(json.dumps(result), flush=True)


def readiness(p):
    live = []
    for path in Path("/proc").iterdir():
        if not path.name.isdigit():
            continue
        try:
            args = (path / "cmdline").read_bytes().split(b"\0")
        except OSError:
            continue
        if (
            any(
                Path(x.decode(errors="replace")).name
                in ("focus_check41.py", "focus_check40b.py")
                for x in args
            )
            and b"--mode" in args
            and b"run" in args
        ):
            live.append(int(path.name))
    flag = (ROOT / "results/quick-checks/check40b/RUNNING.flag").exists()
    gpu = p.base.gpu_pids()
    return dict(
        utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        priority_processes=live,
        check40b_flag=flag,
        gpu_pids=gpu,
        ready=not live and not flag and not gpu,
    )


def prepare(p):
    OUT.mkdir(parents=True, exist_ok=True)
    assert not (OUT / "records.jsonl").exists()
    (OUT / "README.md").write_text(
        READING + "\nPENDING — prewritten before model execution.\n"
    )
    (OUT / "prewritten-reading.md").write_text(READING)
    p.write_json(OUT / "banks.json", bank(p.base))
    paths = [
        "scripts/focus_check41b.py",
        "scripts/focus_check41.py",
        "results/quick-checks/check41/check40-source.py.txt",
        "results/quick-checks/check41b/prewritten-reading.md",
        "results/quick-checks/check41b/banks.json",
    ]
    p.write_json(OUT / "freeze.json", {path: p.sha(ROOT / path) for path in paths})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["test", "prepare", "run"], required=True)
    args = parser.parse_args()
    p = plumbing()
    if args.mode == "test":
        cpu_tests(p)
    elif args.mode == "prepare":
        prepare(p)
    else:
        # Blocking flock is acquired in a thread so resource polling/heartbeats
        # remain foreground and no process is launched or signaled. Queue fairness
        # keeps the preexisting nonblocking check42 waiter behind this request.
        lock = (ROOT / ".review.lock").open("a")
        acquired = threading.Event()

        def acquire():
            fcntl.flock(lock, fcntl.LOCK_EX)
            acquired.set()

        threading.Thread(target=acquire, daemon=True).start()
        receipts = []
        while True:
            state = readiness(p)
            state["lock_acquired"] = acquired.is_set()
            receipts.append(state)
            print(json.dumps(state), flush=True)
            if state["ready"] and acquired.is_set():
                break
            for _ in range(10):
                time.sleep(60)
                print(
                    "Waiting; next resource poll on the 600-second cadence.", flush=True
                )
        try:
            # Staged script is installed only after earlier quick checks release the lock.
            destination = ROOT / "scripts/focus_check41b.py"
            if Path(__file__).resolve() != destination:
                destination.write_bytes(Path(__file__).read_bytes())
            prepare(p)
            p.write_json(OUT / "gpu-readiness.json", receipts)
            with (ROOT / "plan/LEDGER.md").open("a") as ledger:
                ledger.write(
                    "\n2026-09-05 — check41b WRITE-AHEAD: direct user-authorized foreground causal-neuron check; archived protocol read. No fit/train. Gradient readout 32 synthetic tasks, select 8 setup, evaluate 32 distinct prompts; seed 41042. Fixed reading in check41b/prewritten-reading.md; no sealed reads, signals or push; 5400-second cooperative cap.\n"
                )
            (OUT / "RUNNING.flag").write_text(str(__import__("os").getpid()) + "\n")
            run(p)
        finally:
            (OUT / "RUNNING.flag").unlink(missing_ok=True)
            lock.close()


def cpu_tests(p):
    import torch
    from transformers import AutoTokenizer, Qwen3Config, Qwen3ForCausalLM

    torch.set_num_threads(2)
    torch.manual_seed(SEED)
    config = Qwen3Config(
        hidden_size=16,
        intermediate_size=32,
        num_hidden_layers=2,
        num_attention_heads=2,
        num_key_value_heads=1,
        head_dim=8,
        vocab_size=32,
    )
    model = Qwen3ForCausalLM(config).eval().requires_grad_(False)

    class Tokenizer:
        def apply_chat_template(self, *args, **kwargs):
            return [1, 2, 3]

        def decode(self, ids, **kwargs):
            return " ".join(map(str, ids))

    engine = Engine.__new__(Engine)
    engine.torch, engine.p, engine.device = torch, p, torch.device("cpu")
    engine.model, engine.tokenizer, engine.cap = model, Tokenizer(), 6
    engine.ids = {"JavaScript": [4, 5, 6, 7, 8], "Python": [9, 10, 11, 12, 13]}
    engine.shape = (2, 32)
    engine.deadline = time.monotonic() + 300
    engine.eos = {1000}
    engine.hooks = Hooks([layer_idx.mlp.down_proj for layer_idx in model.model.layers])
    messages = [dict(role="user", content="fixture")]
    raw, data = engine.decision(messages, gradient=True)
    assert (
        torch.isfinite(data["attribution"]).all()
        and data["attribution"].abs().max() > 0
    )
    flat = int(data["attribution"].abs().argmax())
    layer, neuron = divmod(flat, 32)
    eps = 0.01

    def evaluate(gain):
        engine.hooks.position = 0
        engine.hooks.action = dict(
            T=1,
            variant="multiply",
            layers={layer: (torch.tensor([neuron]), torch.tensor([1 + gain]))},
        )
        with torch.no_grad():
            return float(
                engine.contrast(
                    model(input_ids=torch.tensor([[1, 2, 3]]), use_cache=False).logits
                )
            )

    finite = (evaluate(eps) - evaluate(-eps)) / (2 * eps)
    assert abs(finite - float(data["attribution"].flatten()[flat])) < 2e-5, (
        finite,
        data["attribution"].flatten()[flat],
    )
    engine.hooks.action = None
    before = engine.generate(messages)
    selected = dict(indices=[0, 35], signs=[1, -1], shuffled_indices=[1, 36])
    means = {"JavaScript": torch.ones(2, 32) * 3, "Python": torch.ones(2, 32) * -3}
    for variant in ("multiply", "clamp"):
        for t in (1, 4, 16):
            cell = dict(k=2, T=t, variant=variant, gain=3)
            a = action(engine, cell, selected, means, "correct")
            r = engine.generate(messages, a)
            assert {c["prediction_index"] for c in r["intervention_calls"]} == set(
                range(min(t, 6))
            )
            assert r["c_shift"] != 0
            assert engine.hooks.action is None
    after = engine.generate(messages)
    assert (
        before["generated_token_ids"] == after["generated_token_ids"]
        and before["c"] == after["c"]
    )
    engine.hooks.action = None
    with torch.no_grad():
        original = model(input_ids=torch.tensor([[1, 2, 3]]), use_cache=False).logits
        engine.hooks.action = action(
            engine, dict(T=1, variant="clamp", gain=0), selected, means, "correct"
        )
        engine.hooks.position = 0
        changed = model(input_ids=torch.tensor([[1, 2, 3]]), use_cache=False).logits
    assert torch.equal(original[:, :-1], changed[:, :-1]) and not torch.equal(
        original[:, -1], changed[:, -1]
    )
    engine.hooks.close()
    tok = AutoTokenizer.from_pretrained(p.MODEL, local_files_only=True)
    encoded = {
        lang: [tok.encode(t, add_special_tokens=False) for t in ts]
        for lang, ts in TOKENS.items()
    }
    assert all(len(ids) == 1 for ts in encoded.values() for ids in ts)
    assert len({ids[0] for ts in encoded.values() for ids in ts}) == 10
    assert len(cells()) == 36
    b = bank(p.base)
    assert [len(b[k]) for k in ("fit", "setup", "screen")] == [32, 8, 32]
    refs = {
        "correct": {
            "200": {
                "flat_indices": {
                    "Python": list(range(200)),
                    "JavaScript": list(range(200, 400)),
                }
            }
        }
    }
    attr = torch.randn(4, 1024)
    sets = select(attr, refs)
    for k, v in sets.items():
        assert len(v["indices"]) == int(k) and len(set(v["shuffled_indices"])) == int(k)
        assert not set(v["indices"]) & set(v["shuffled_indices"])
        assert [i // 1024 for i in v["indices"]] == [
            i // 1024 for i in v["shuffled_indices"]
        ]
        assert all(
            s == int(torch.sign(attr.flatten()[i]))
            for i, s in zip(v["indices"], v["signs"], strict=True)
        )
    arms = {a: dict(n=32, javascript=0, broken=0) for a in ARMS}
    assert verdict(arms) == "NOT POSSIBLE"
    arms["correct"]["javascript"] = 12
    assert verdict(arms) == "MARGINAL"
    arms["correct"]["javascript"] = 20
    assert verdict(arms) == "POSSIBLE"
    arms["shuffled"]["javascript"] = 5
    assert verdict(arms) == "MARGINAL"
    arms["OFF"]["n"] = 31
    assert verdict(arms) == "PARTIAL"
    task = dict(name="square", witness=r"\*")
    assert (
        p.score("function square(x) { return x*x; }", task)["valid_language"]
        == "JavaScript"
    )
    assert p.score("def square(x):\n    return x*x", task)["valid_language"] == "Python"
    print(
        json.dumps(
            dict(
                status="PASS",
                checks=[
                    "nonvacuous gradient finite difference",
                    "first-T production decode counts 1/4/16",
                    "clamp and scaling affect c",
                    "unchanged earlier prompt positions",
                    "OFF restored after release",
                    "literal tokenization",
                    "36-cell grid and 32/8/32 disjoint bank",
                    "signed layer-matched shuffled sets",
                    "fixed reading boundaries",
                    "real parsers",
                ],
                token_sets=encoded,
                finite_difference=finite,
                attribution=float(data["attribution"].flatten()[flat]),
            )
        )
    )


if __name__ == "__main__":
    main()
