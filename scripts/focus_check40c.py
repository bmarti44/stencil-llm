#!/usr/bin/env python3
"""Check40c: frozen router direction, dose and first-token duration screen."""

from __future__ import annotations

import argparse
import fcntl
import inspect
import json
import os
import re
import shutil
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path("/home/bmarti44/stencil-llm")
sys.path.insert(0, str(ROOT / "scripts"))
import focus_check40 as base  # noqa: E402
import focus_check40b as prior  # noqa: E402

OUT = Path(
    os.environ.get("STENCIL_CHECK40C_OUT", str(ROOT / "results/quick-checks/check40c"))
)
OLD = ROOT / "results/quick-checks/check40b"
ARMS = [
    ("alpha2_sustained", 2, None),
    ("alpha3_sustained", 3, None),
    ("alpha4_first3", 4, 3),
    ("alpha4_first8", 4, 8),
]
LIMIT = 1800
READING = """# Check 40c — router dose and first-k generated tokens

Unregistered, disclosed, 2026-09-05. Same Qwen3-30B-A3B, seed 40040,
32 uncued synthetic check40b screen tasks, frozen JS direction, greedy fresh-KV
SET-only requests, inherited prompt, router hook and 64-token cap. No fitting or
training. Profile-on: prior 32 cued competence responses; prior alpha selected on
eight setup tasks. Evaluated-on: same already-observed 32 synthetic screen tasks;
this is an exploratory reuse and cell selection, not a fresh held-out confirmation.
No benchmark or sealed IFEval/BFCL input is read.

## Pre-written reading (fixed before new outcomes)

Four new arms, 32 each: alpha 2 sustained; alpha 3 sustained; alpha 4 first 3
generated tokens then OFF; alpha 4 first 8 then OFF. Recorded check40b alpha 4
sustained and OFF are reference rows only, never regenerated. All 128 generations
run once; no outcome-based retries, cap changes, additional arms or task reduction.
POSSIBLE iff some NEW cell has valid unbroken JavaScript >=20/32 and breakage
<=2/32. Freeze the first qualifying cell in the listed arm order for the next
screen (deterministic tie-break, no subsequent screen authorized here). Otherwise
report the dose curve. If any first-k-only cell reaches JS >=20/32, read this as
the language decision being made in the first tokens and sustained bias driving
syntax breakage; report the actual paired breakage change to qualify that reading.
This comparison retains biased prefill and its KV effects: it does not isolate
decode-only causality or prove a general mechanism.

Token boundary: prefill predicts generated token 1 and uses bias, exactly as 40b.
The forward predicting token j uses bias iff j<=k; forwarding token k to predict
token k+1 is OFF. Count generated tokens including fence pieces, not code tokens.
Sustained uses bias on all prefill positions and decode calls. Same cached prompt
effects persist after OFF. Trace every prediction forward and its active state.

Score using unchanged 40b Python/Node parsers, coarse task check and breakage
flags. Report first token, first three tokens and fence labels; breakage by all
three task families; separately count replies containing JavaScript => arrows
and -> neighbours. Arrow reporting does not repair/change the coarse checker.
Thresholds use valid unbroken JS, not fence labels or coarse task success.

Explicit interpreter: PYTHONNOUSERSITE=1 .venv/bin/python -s -B; require
transformers==5.16.1 imported from .venv. Assert real router tuple slot 0 equals
F.linear(hidden_states, weight) before bias; test consumer/OFF and token boundary
on CPU, then assert raw-slot contract on every model layer before generation.

Expected cost from 40b: 314.04 s load + 128*(6194/224)/15.05 = 549.22 s;
25% reserve gives 686.52 s (<15 minutes). Capped conservative projection:
(314.04 + 128*64/15.05 + 128)*1.25 = 1232.95 s (<0.5 GPU-h).
GPU allocation includes load/kernel checks and cleanup; cooperative per-forward/
per-token deadline, no signals. Foreground only. Poll check41b/check42 RUNNING.flag
and GPU availability every 300 seconds; publish our own RUNNING.flag only while
running and remove after. No process termination, background launch or push.

## Results

PENDING.
"""


def write(name, value):
    base.write_json(OUT / name, value)


def runtime():
    import transformers
    from transformers.models.qwen3_moe.modeling_qwen3_moe import Qwen3MoeTopKRouter

    assert Path(sys.prefix).resolve() == ROOT / ".venv", sys.prefix
    assert transformers.__version__ == "5.16.1"
    assert Path(transformers.__file__).resolve().is_relative_to(ROOT / ".venv")
    return dict(
        python=sys.executable,
        transformers=transformers.__version__,
        transformers_path=transformers.__file__,
        router_source=inspect.getsource(Qwen3MoeTopKRouter.forward),
        router_source_sha256=base.sha(Path(inspect.getfile(Qwen3MoeTopKRouter))),
    )


def raw_contract(gate):
    import torch

    x = (
        torch.arange(
            4 * gate.hidden_dim, device=gate.weight.device, dtype=torch.float32
        )
        .reshape(4, gate.hidden_dim)
        .sin()
        .to(gate.weight.dtype)
    )
    with torch.inference_mode():
        result = gate(x)
        raw = torch.nn.functional.linear(x, gate.weight)
        assert isinstance(result, tuple) and len(result) == 3
        assert torch.equal(result[0], raw), "Slot 0 must be raw linear router logits"
        assert not (
            (result[0] >= 0).all()
            and torch.allclose(
                result[0].float().sum(-1), torch.ones(4, device=x.device)
            )
        )
        probs = torch.softmax(raw, dim=-1, dtype=torch.float32)
        weights, indices = torch.topk(probs, gate.top_k, dim=-1)
        if gate.norm_topk_prob:
            weights = weights / weights.sum(-1, keepdim=True)
        assert torch.equal(result[1], weights.to(raw.dtype))
        assert torch.equal(result[2], indices)
    return True


def generate(engine, task, bias, k, cap=64):
    """Use the unchanged Engine.generate consumer; switch bias before each forward."""
    trace = []
    device_bias = bias.to(device=engine.device, dtype=engine.torch.bfloat16)

    def schedule(module, args, kwargs):
        prediction = len(trace) + 1
        active = k is None or prediction <= k
        engine.hooks.bias = device_bias if active else None
        trace.append(
            dict(
                predicts_generated_token=prediction,
                bias_active=active,
                input_tokens=kwargs["input_ids"].shape[-1],
            )
        )

    handle = engine.model.register_forward_pre_hook(schedule, with_kwargs=True)
    try:
        record, _ = engine.generate(base.messages_for(task), bias=bias, cap=cap)
    finally:
        handle.remove()
        engine.hooks.bias = None
    record["prediction_trace"] = trace
    record["first_k"] = k
    return record


def report_fields(record, tokenizer):
    ids = record["generated_token_ids"]
    code = base.extract_code(record["text"])[0]
    label = re.search(r"```([^\n]*)\n", record["text"])
    return dict(
        first_token_id=ids[0] if ids else None,
        first_token=tokenizer.decode(ids[:1]),
        first_three_token_ids=ids[:3],
        first_three_tokens=tokenizer.decode(ids[:3]),
        fence_label=label[1].strip() if label else "(bare)",
        arrow_function_reply="=>" in code,
        arrow_neighbour_reply="->" in code,
    )


def aggregate(rows):
    result = prior.aggregate(rows)
    result.update(
        breakage_by_family={
            family: dict(
                n=sum(r["family"] == family for r in rows),
                broken=sum(
                    r["family"] == family and r["score"]["broken"] for r in rows
                ),
                js=sum(
                    r["family"] == family
                    and r["score"]["valid_language"] == "JavaScript"
                    for r in rows
                ),
            )
            for family in sorted({r["family"] for r in rows})
        },
        first_tokens=dict(Counter(r["first_token"] for r in rows)),
        first_three_tokens=dict(Counter(r["first_three_tokens"] for r in rows)),
        fence_labels=dict(Counter(r["fence_label"] for r in rows)),
        arrow_function_replies=sum(r["arrow_function_reply"] for r in rows),
        arrow_valid_js=sum(
            r["arrow_function_reply"] and r["score"]["valid_language"] == "JavaScript"
            for r in rows
        ),
        arrow_coarse_pass=sum(
            r["arrow_function_reply"] and r["score"]["valid_task"] for r in rows
        ),
        arrow_neighbour_replies=sum(r["arrow_neighbour_reply"] for r in rows),
    )
    return result


def decision(arms):
    if any(arms[a]["n"] != 32 for a, _, _ in ARMS):
        return "PARTIAL", None
    eligible = [a for a, _, _ in ARMS if arms[a]["js"] >= 20 and arms[a]["broken"] <= 2]
    return ("POSSIBLE", eligible[0]) if eligible else ("NO QUALIFYING CELL", None)


def cpu_checks():
    import torch
    from transformers import Qwen3MoeConfig, Qwen3MoeForCausalLM

    torch.set_num_threads(2)
    runtime()
    torch.manual_seed(40040)
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
    model = Qwen3MoeForCausalLM(cfg).eval()
    engine = base.Engine.__new__(base.Engine)
    engine.model, engine.torch, engine.device = model, torch, torch.device("cpu")
    engine.deadline, engine.eos = time.monotonic() + 300, set()

    class Tokenizer:
        def apply_chat_template(self, *args, **kwargs):
            assert kwargs["return_dict"] is False
            return [1, 2, 3]

        def decode(self, ids, **kwargs):
            return str(ids)

    engine.tokenizer = Tokenizer()
    engine.hooks = base.RouterHooks([layer.mlp.gate for layer in model.model.layers])
    for g in engine.hooks.gates:
        raw_contract(g)
    bias = torch.tensor([[0.0, 0.0, 0.0, 10.0]] * 2)
    task = dict(prompt="CPU fixture")
    baseline, _ = engine.generate(base.messages_for(task), bias=bias, cap=10)
    observed = []
    handles = [
        g.register_forward_pre_hook(
            lambda m, a: observed.append(engine.hooks.bias is not None)
        )
        for g in engine.hooks.gates
    ]
    for k in (None, 3, 8):
        observed.clear()
        r = generate(engine, task, bias, k, cap=10)
        expected = [k is None or i < k for i in range(10)]
        assert [x["bias_active"] for x in r["prediction_trace"]] == expected
        assert observed == [active for active in expected for _ in range(2)]
        if k is None:
            assert r["generated_token_ids"] == baseline["generated_token_ids"]
    for h in handles:
        h.remove()
    engine.hooks.close()
    cells = {a: dict(n=32, js=19, broken=0) for a, _, _ in ARMS}
    assert decision(cells) == ("NO QUALIFYING CELL", None)
    cells[ARMS[0][0]].update(js=20, broken=2)
    assert decision(cells) == ("POSSIBLE", ARMS[0][0])
    cells[ARMS[0][0]]["broken"] = 3
    assert decision(cells)[1] is None
    assert not torch.cuda.is_initialized()
    return dict(
        real_hf_raw_slot=True,
        real_generation_boundary_3_8=True,
        sustained_matches_inherited=True,
        decision_boundaries=True,
        cuda_initialized=False,
    )


def prepare():
    assert not (OUT / "records.jsonl").exists()
    checks = cpu_checks()
    OUT.mkdir(parents=True, exist_ok=True)
    write("cpu.json", checks)
    (OUT / "README.md").write_text(READING)
    (OUT / "prewritten-reading.md").write_text(READING)
    bank = json.loads((OLD / "banks.json").read_text())["screen"]
    assert len(bank) == 32
    write("tasks.json", bank)
    files = [
        Path(__file__).resolve(),
        ROOT / "scripts/focus_check40.py",
        ROOT / "scripts/focus_check40b.py",
        OUT / "tasks.json",
        OUT / "prewritten-reading.md",
        OLD / "frozen-biases.pt",
        OLD / "banks.json",
        OLD / "records.jsonl",
        OLD / "summary.json",
    ]
    write(
        "freeze.json",
        dict(
            utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            runtime=runtime(),
            files={str(p): base.sha(p) for p in files},
        ),
    )
    print(json.dumps(checks), flush=True)


def verify_freeze():
    for name, digest in json.loads((OUT / "freeze.json").read_text())["files"].items():
        assert base.sha(Path(name)) == digest, name


def run():
    global OUT
    import torch

    verify_freeze()
    checks = runtime()
    waiting = []
    lock = (ROOT / ".review.lock").open("a")
    while True:
        flags = [
            str(ROOT / f"results/quick-checks/{c}/RUNNING.flag")
            for c in ("check41b", "check42")
            if (ROOT / f"results/quick-checks/{c}/RUNNING.flag").exists()
        ]
        gpu = base.gpu_pids()
        receipt = dict(
            utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), flags=flags, gpu=gpu
        )
        waiting.append(receipt)
        write("wait.json", waiting)
        print(json.dumps(receipt), flush=True)
        if not flags and not gpu:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                print("Repository lock occupied; wait without signals.", flush=True)
        for _ in range(5):
            time.sleep(60)
            print("Waiting; resource poll interval remains 300 seconds.", flush=True)
    verify_freeze()
    destination = ROOT / "results/quick-checks/check40c"
    if OUT != destination:
        assert not destination.exists(), "Refuse existing output directory"
        shutil.copytree(OUT, destination)
        source = ROOT / "scripts/focus_check40c.py"
        assert not source.exists(), "Refuse source overwrite"
        shutil.copy2(Path(__file__), source)
        old_out = OUT
        OUT = destination
        freeze = json.loads((OUT / "freeze.json").read_text())
        write("prepublish-freeze.json", freeze)
        freeze["files"] = {
            str(
                source
                if Path(name) == Path(__file__).resolve()
                else OUT / Path(name).relative_to(old_out)
                if Path(name).is_relative_to(old_out)
                else Path(name)
            ): digest
            for name, digest in freeze["files"].items()
        }
        write("freeze.json", freeze)
        verify_freeze()
    with (ROOT / "plan/LEDGER.md").open("a") as ledger:
        ledger.write(
            "\n2026-09-05 — check40c WRITE-AHEAD: frozen 40b JS direction, "
            "same 32 exploratory screen tasks; fit/train none, prior profile/setup "
            "disjoint. Four arms and reading frozen in check40c/prewritten-reading.md; "
            "CPU real-HF slot/schedule checks pass. Foreground 1800-second GPU cap, "
            "300-second flag polls; no sealed inputs, signals or push.\n"
        )
    assert not (OUT / "records.jsonl").exists(), "No regeneration or overwrite"
    flag = OUT / "RUNNING.flag"
    with flag.open("x") as f:
        f.write(str(os.getpid()) + "\n")
    rows, references = [], []
    engine = None
    start = time.monotonic()
    base.GPU_SECONDS = LIMIT
    summary = dict(reading="PARTIAL", reason="interrupted", arms={})
    journal = (OUT / "records.jsonl").open("x")
    try:
        engine = base.Engine(start)
        checks.update(
            load_seconds=engine.load_seconds,
            torch=torch.__version__,
            raw_slot_verified_layers=sum(raw_contract(g) for g in engine.hooks.gates),
        )
        write("runtime.json", checks)
        kernel = engine.verify_kernel()
        assert kernel["adopted"]
        write("kernel.json", kernel)
        tasks = json.loads((OUT / "tasks.json").read_text())
        by_id = {t["id"]: t for t in tasks}
        old_rows = [
            json.loads(line)
            for line in (OLD / "records.jsonl").read_text().splitlines()
        ]
        for r in old_rows:
            if r["phase"] == "screen" and r["arm"] in ("correct", "OFF"):
                r = dict(
                    r,
                    source_record_id=r["id"],
                    source_arm=r["arm"],
                    reference=True,
                    arm="alpha4_sustained_reference"
                    if r["arm"] == "correct"
                    else "OFF_reference",
                    family=by_id[r["task_id"]]["family"],
                )
                r.update(report_fields(r, engine.tokenizer))
                references.append(r)
        assert len(references) == 64
        write("reference-records.json", references)
        frozen = torch.load(
            OLD / "frozen-biases.pt", map_location="cpu", weights_only=True
        )["correct"]
        for task in tasks:
            for arm, alpha, k in ARMS:
                r = generate(engine, task, frozen * (alpha / 4), k)
                r.update(
                    id=len(rows),
                    task_id=task["id"],
                    family=task["family"],
                    phase="screen",
                    arm=arm,
                    alpha=alpha,
                    reference=False,
                    score=base.score(r["text"], task, r["truncated"]),
                )
                r.update(report_fields(r, engine.tokenizer))
                assert len(r["history"]) == 2 and not r["retained_kv"]
                journal.write(json.dumps(r) + "\n")
                journal.flush()
                rows.append(r)
                print(
                    json.dumps(
                        dict(
                            n=len(rows),
                            arm=arm,
                            task=task["id"],
                            js=r["score"]["valid_language"],
                            broken=r["score"]["broken"],
                            elapsed=time.monotonic() - start,
                        )
                    ),
                    flush=True,
                )
                if r["cost_stopped"]:
                    raise base.BudgetStop("cooperative generation cap")
        summary["reason"] = "all 128 scheduled generations complete"
    except base.BudgetStop as exc:
        summary["reason"] = str(exc)
    except Exception as exc:
        summary["reason"] = repr(exc)
        raise
    finally:
        journal.close()
        names = [a for a, _, _ in ARMS] + [
            "alpha4_sustained_reference",
            "OFF_reference",
        ]
        summary["arms"] = {
            a: aggregate([r for r in rows + references if r["arm"] == a]) for a in names
        }
        summary["reading"], summary["selected_cell"] = decision(summary["arms"])
        summary.update(
            records=len(rows),
            reference_records=len(references),
            token_cap=64,
            cap_seconds=LIMIT,
            generated_tokens=sum(len(r["generated_token_ids"]) for r in rows),
        )
        if engine is not None:
            summary["peak_allocated_gib"] = torch.cuda.max_memory_allocated() / 2**30
            engine.hooks.close()
            del engine
            import gc

            gc.collect()
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        summary["gpu_seconds"] = time.monotonic() - start
        summary["cap_overrun_seconds"] = max(0, summary["gpu_seconds"] - LIMIT)
        write("summary.json", summary)
        flag.unlink()
        lock.close()
        print(json.dumps(summary), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["prepare", "run", "test"], required=True)
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare()
    elif args.mode == "test":
        print(json.dumps(cpu_checks()))
    else:
        run()


if __name__ == "__main__":
    main()
