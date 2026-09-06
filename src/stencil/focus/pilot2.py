"""Day5b one-load DEV gate/re-pilot; run with python -m stencil.focus.pilot2."""

import argparse
import fcntl
import gc
import hashlib
import json
import os
import struct
import subprocess
import tempfile
import time
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

from scripts import composition_pilot as pilot

from .loop import DecodeResult, generate_once
from .pilot_recovery import FROZEN, ROOT
from .retained_decode import RetainedDecoder
from .slab import bank

OUT = ROOT / "results/quick-checks/composition-pilot-2"
EXPERTS_IMPLEMENTATION = "grouped_mm"


def lines(path):
    return (
        [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []
    )


def renderer_check():
    """Replay the real consumer using frozen inputs/feedback, isolating layout."""
    from tokenizers import Tokenizer

    from .slab import TOKENIZER_PATH

    golden = lines(FROZEN / "renderer-golden.jsonl")
    rows = [
        r
        for r in lines(FROZEN / "records.jsonl")
        if (
            r["oracle_checker_results"][0]["mode"],
            r["oracle_checker_results"][0]["arm"],
        )
        == ("sequential", "R")
    ]
    tok = Tokenizer.from_file(str(TOKENIZER_PATH))
    decoded = tok.decode(golden[0]["prompt_ids"], skip_special_tokens=False)
    system = decoded.split("<|im_start|>system\n", 1)[1].split("<|im_end|>\n", 1)[0]
    assert len(golden) == len(rows) == 16
    with tempfile.TemporaryDirectory() as temp:
        lane = pilot.Lane(Path(temp), bank()[0], "R", "golden")
        # Freeze original feedback, rather than executing with the amended parser.
        lane.session.journal._checker = lambda row: []
        for i, (g, original) in enumerate(zip(golden, rows, strict=True)):
            lane.prepare(i)
            lane.session.request = replace(lane.session.request, system=system)

            def decoder(req, g=g):
                assert req.text.encode() == g["text"].encode()
                assert list(req.prompt_ids) == g["prompt_ids"]
                assert hashlib.sha256(req.text.encode()).hexdigest() == g["utf8_sha256"]
                return DecodeResult(
                    g["output"], tuple(g["output_ids"]), g["eos"], g["truncated"]
                )

            generate_once(lane.session, lane.messages, decoder, tools=pilot.TOOL_SCHEMA)
            lane.feedback = original["oracle_checker_results"][0]["execution"]
    return dict(
        passed=True,
        prompts=16,
        original_system_and_feedback=True,
        golden_sha256=pilot.sha(FROZEN / "renderer-golden.jsonl"),
        renderer_sha256=pilot.sha(ROOT / "src/stencil/focus/renderer.py"),
    )


def token_bytes(ids, eos):
    seq = list(ids) + ([] if eos is None else [eos])
    return struct.pack("<" + "q" * len(seq), *seq)


def parity(model, tokenizer, out, deadline):
    frozen = [
        r
        for r in lines(FROZEN / "records.jsonl")
        if r["oracle_checker_results"][0]["mode"] == "sequential"
    ]
    assert len(frozen) == 64
    backends, records = {}, []
    try:
        for index, row in enumerate(frozen):
            if time.monotonic() >= deadline - 60:
                break
            detail = row["oracle_checker_results"][0]
            arm = detail["arm"]
            req = SimpleNamespace(prompt_ids=tuple(row["rendered_token_ids"]))
            backend = backends.get(arm)
            reset = (
                backend is None
                or req.prompt_ids[: len(backend.consumed[0])] != backend.consumed[0]
            )
            if reset:
                if backend is not None:
                    backend.close()
                backend = RetainedDecoder(model, tokenizer, deadline=deadline - 30)
                backends[arm] = backend
                for handle in backend.handles:
                    handle.remove()
                backend.handles = []
            backend.handles = [
                model.model.layers[layer - 1].register_forward_hook(
                    backend._hook(layer)
                )
                for layer in backend.layers
            ]
            try:
                result, measures = backend([req])
            finally:
                for handle in backend.handles:
                    handle.remove()
                backend.handles = []
            result, measure = result[0], measures[0]
            hidden = []
            import numpy as np

            for key in ("prompt_hidden", "generated_mean"):
                array = measure.pop(key)
                path = out / "hidden" / "parity" / f"{index:02}-{key}.npy"
                path.parent.mkdir(parents=True, exist_ok=True)
                np.save(path, array, allow_pickle=False)
                hidden.append(
                    dict(
                        path=str(path.relative_to(out)),
                        sha256=pilot.sha(path),
                        shape=list(array.shape),
                        dtype=str(array.dtype),
                        layers=list(pilot.LAYERS),
                    )
                )
            actual = list(result.output_ids) + (
                [] if result.eos is None else [result.eos]
            )
            expected = row["output_token_ids"] + (
                [] if row["eos"] is None else [row["eos"]]
            )
            same = token_bytes(result.output_ids, result.eos) == token_bytes(
                row["output_token_ids"], row["eos"]
            )
            first = (
                next(
                    (
                        i
                        for i, (a, b) in enumerate(zip(actual, expected, strict=False))
                        if a != b
                    ),
                    min(len(actual), len(expected)),
                )
                if not same
                else None
            )
            record = dict(
                index=index,
                arm=arm,
                round=detail["round"],
                source_row=index,
                prompt_ids=row["rendered_token_ids"],
                output_ids=list(result.output_ids),
                output=result.text,
                eos=result.eos,
                truncated=result.truncated,
                identical=same,
                cache_reset=reset,
                first_divergence=first,
                expected_at_first=expected[first : first + 8]
                if first is not None
                else [],
                actual_at_first=actual[first : first + 8] if first is not None else [],
                expected_length=len(expected),
                actual_length=len(actual),
                measurements=measure,
                hidden=hidden,
            )
            pilot.append(out / "parity-records.jsonl", record)
            records.append(record)
            print(
                json.dumps(
                    dict(
                        gate=index + 1,
                        identical=same,
                        first_divergence=first,
                        tok_s=measure["generated_forward_tokens"]
                        / max(measure["decode_seconds"], 1e-9),
                    )
                ),
                flush=True,
            )
            if measure["deadline_hit"]:
                break
    finally:
        for backend in backends.values():
            backend.close()
    divergences = [r["index"] for r in records if not r["identical"]]
    complete = len(records) == 64 and not any(
        r["measurements"]["deadline_hit"] for r in records
    )
    result = dict(
        complete=complete,
        compared=len(records),
        divergences=len(divergences),
        divergent_indices=divergences,
        passed=complete and len(divergences) <= 1,
        policy="all64 complete, <=1 divergence with disclosed first-position analysis",
        frozen_records_sha256=pilot.sha(FROZEN / "records.jsonl"),
    )
    pilot.write(out / "parity.json", result)
    return result


def run_episode(
    out, episode, model, tokenizer, deadline, arms=("R", "N", "T"), stub=False
):
    # Reuse the frozen consumer, callbacks and hidden writer; sequential only.
    old = pilot.ARMS
    original_gate = pilot.paired_context_gate
    # Existing admission API requires four labels. Pad absent lanes with the
    # maximum active bound: identical cap decision, no fictitious trajectory.
    pilot.paired_context_gate = lambda bounds: original_gate(
        {a: bounds.get(a, max(bounds.values())) for a in ("R", "N", "T", "O")}
    )
    pilot.ARMS = arms
    try:
        lanes, receipt = pilot.run_episode(
            out, episode, model, tokenizer, "sequential", deadline, stub=stub
        )
    finally:
        pilot.ARMS = old
        pilot.paired_context_gate = original_gate
    # Original helper allocated non-generate overhead across four lanes. Correct
    # the receipt to the actual lane count without changing decode or renderer.
    overhead = receipt["preparation_overhead_seconds"]
    receipt["arm_seconds"] = {
        lane.arm: sum(r["wall_seconds"] for r in lane.rows) + overhead / len(arms)
        for lane in lanes
    }
    receipt["complete"] &= not any(
        r["oracle_checker_results"][0]["measurements"].get("deadline_hit")
        for lane in lanes
        for r in lane.rows
    )
    receipts = lines(out / "episodes.jsonl")
    receipts[-1] = receipt
    (out / "episodes.jsonl").write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in receipts)
    )
    return receipt


def run(out, experts):
    import torch
    from transformers import AutoTokenizer, Qwen3MoeForCausalLM

    out.mkdir(parents=True, exist_ok=True)
    if (out / "run.json").exists():
        raise ValueError("fresh run required")
    recipe = json.loads((out / "recipe.json").read_text())
    for rel, digest in recipe["source_hashes"].items():
        assert pilot.sha(ROOT / rel) == digest, rel
    lock = (ROOT / ".review.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    flag = out / "RUNNING.flag"
    flags = list((ROOT / "results/quick-checks").glob("*/RUNNING.flag"))
    if flags:
        raise RuntimeError(f"Other Stencil flags: {flags}")
    processes = subprocess.check_output(
        [
            "nvidia-smi",
            "--query-compute-apps=pid,process_name",
            "--format=csv,noheader",
        ],
        text=True,
    )
    if any("python" in line for line in processes.splitlines()):
        raise RuntimeError("Other GPU Python process present")
    flag.write_text(f"{os.getpid()} Day5b {time.time()}\n")
    with (ROOT / ".stencil-owned-pids").open("a") as registry:
        registry.write(f"{os.getpid()}\n")
    start = time.monotonic()
    deadline = start + 7200
    receipt = dict(
        started_at=time.time(),
        cap_seconds=7200,
        experts_implementation=experts,
        status="running",
        selected_mode="sequential",
    )
    pilot.write(out / "run.json", receipt)
    model = None
    try:
        torch.set_num_threads(8)
        torch.manual_seed(20260906)
        tokenizer = AutoTokenizer.from_pretrained(
            ROOT / "models/qwen3-30b-a3b-hf", local_files_only=True
        )
        model = Qwen3MoeForCausalLM.from_pretrained(
            ROOT / "models/qwen3-30b-a3b-hf",
            dtype=torch.bfloat16,
            device_map={"": 0},
            attn_implementation="sdpa",
            experts_implementation=experts,
            local_files_only=True,
        ).eval()
        receipt["load_seconds"] = time.monotonic() - start
        pilot.write(out / "run.json", receipt)
        gate = parity(model, tokenizer, out, deadline)
        if not gate["passed"]:
            receipt["status"] = "parity_stop"
            return
        episodes = bank()
        completed = []
        for arms in (("R", "N", "T"), ("O",)):
            if arms == ("O",) and len(completed) != 8:
                break
            for index in pilot.ORDER:
                prior = lines(out / "episodes.jsonl")
                rate = max(
                    (
                        e["wall_seconds"] / e["rounds"] / len(e["arm_seconds"])
                        for e in prior
                        if e["rounds"]
                    ),
                    default=0,
                )
                needed = 1.25 * rate * len(episodes[index].turns) * len(arms) + 60
                if time.monotonic() + needed >= deadline:
                    pilot.append(
                        out / "events.jsonl",
                        dict(
                            event="fixed_order_budget_stop",
                            next_episode=episodes[index].episode_id,
                            arms=arms,
                            required_seconds=needed,
                            remaining_seconds=deadline - time.monotonic(),
                        ),
                    )
                    break
                ep = run_episode(out, episodes[index], model, tokenizer, deadline, arms)
                if not ep["complete"]:
                    break
                if len(arms) == 3:
                    completed.append(index)
        receipt["status"] = "finished"
    except BaseException as exc:
        receipt.update(status="error", error=repr(exc))
        raise
    finally:
        if model is not None:
            del model
        gc.collect()
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
        receipt.update(
            gpu_held_seconds=time.monotonic() - start,
            finished_at=time.time(),
            peak_cuda_bytes=torch.cuda.max_memory_allocated(),
        )
        pilot.write(out / "run.json", receipt)
        flag.unlink(missing_ok=True)
        fcntl.flock(lock, fcntl.LOCK_UN)
        lock.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument(
        "--experts-implementation",
        choices=("grouped_mm", "eager"),
        default=EXPERTS_IMPLEMENTATION,
    )
    args = parser.parse_args()
    run(args.out, args.experts_implementation)


if __name__ == "__main__":
    main()
