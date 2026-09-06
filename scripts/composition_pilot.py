"""DEV-only composition pilot. No evaluation episode construction or benchmark IO."""

import argparse
import hashlib
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path

from stencil.focus.journal import FIELDS, Journal
from stencil.focus.loop import DecodeResult, Message, Session
from stencil.focus.register import Register
from stencil.focus.renderer import Request, compact
from stencil.focus.retained_decode import RetainedDecoder
from stencil.focus.slab import (
    SYSTEM_PROMPT,
    TOOL_SCHEMA,
    Executor,
    bank,
    check,
    materialize,
    paired_context_gate,
    qwen_encode,
    reference,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/quick-checks/composition-pilot"
ARMS = ("R", "N", "T", "O")
ORDER = (0, 1, 6, 7, 2, 3, 4, 5)
LAYERS = (8, 16, 24, 32, 40)
WRITE_LOCK = threading.Lock()


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, sort_keys=True, indent=2, allow_nan=False) + "\n")


def append(path, obj):
    with WRITE_LOCK, path.open("a") as stream:
        stream.write(compact(obj) + "\n")
        stream.flush()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PilotJournal(Journal):
    def __init__(self, lane):
        self.lane = lane
        super().__init__(lane.directory / "journal.jsonl", checker=self.finish)

    def finish(self, row):
        lane = self.lane
        assert set(row) == FIELDS
        if row["output"] is None:
            return []
        feedback = lane.executor.run(row["output"])
        outcome = check(
            lane.episode,
            lane.round,
            row["output"],
            lane.executor,
            truncated=row["truncated"],
        )
        lane.feedback = feedback
        measurement = lane.measurement.copy()
        measurement["prior_own_tokens"] = sum(
            r["output_token_count"] for r in lane.rows
        )
        measurement["prior_substantial_bodies"] = sum(
            100 <= r["output_token_count"] <= 300 for r in lane.rows
        )
        changes = [t.index for t in lane.episode.turns[: lane.round + 1] if t.events]
        measurement["turns_since_lifecycle_event"] = lane.round - max(
            changes, default=0
        )
        hidden = []
        if "prompt_hidden" in measurement:
            import numpy as np

            for key in ("prompt_hidden", "generated_mean"):
                array = measurement.pop(key)
                path = (
                    lane.out
                    / "hidden"
                    / lane.mode
                    / lane.episode.episode_id
                    / lane.arm
                    / f"{lane.round:02}-{key}.npy"
                )
                path.parent.mkdir(parents=True, exist_ok=True)
                np.save(path, array, allow_pickle=False)
                hidden.append(
                    dict(
                        path=str(path.relative_to(lane.out)),
                        sha256=sha(path),
                        shape=list(array.shape),
                        dtype=str(array.dtype),
                        layers=list(LAYERS),
                    )
                )
        detail = dict(
            episode=lane.episode.episode_id,
            arm=lane.arm,
            mode=lane.mode,
            round=lane.round,
            outcome=outcome,
            execution=feedback,
            artifact_hashes=lane.executor.hashes(),
            measurements=measurement,
            hidden=hidden,
            paired_gate=lane.gate,
        )
        # The same writer captures checks, exact output and all v2 provenance.
        full = dict(row, oracle_checker_results=[detail])
        append(lane.out / "records.jsonl", full)
        lane.rows.append(full)
        if lane.arm == "R":
            append(
                lane.directory / "rendered.jsonl",
                dict(
                    round=lane.round,
                    text=row["rendered_messages"],
                    utf8_sha256=hashlib.sha256(
                        row["rendered_messages"].encode()
                    ).hexdigest(),
                ),
            )
        return [detail]


class Lane:
    def __init__(self, out, episode, arm, mode):
        self.out, self.episode, self.arm, self.mode = out, episode, arm, mode
        self.directory = out / mode / episode.episode_id / arm
        self.directory.mkdir(parents=True, exist_ok=False)
        materialize(episode, self.directory / "workspace")
        self.executor = Executor(
            self.directory / "workspace",
            json.loads((self.directory / "workspace/public_tests.json").read_text()),
        )
        self.round, self.feedback, self.measurement, self.rows = 0, None, {}, []
        self.session = Session(
            Register(defaults=episode.defaults, task_handles={"A", "B"}),
            Request("", "tool_call"),
            PilotJournal(self),
        )

    def prepare(self, index):
        self.round = index
        t = self.episode.turns[index]
        self.session.request = Request(
            "",
            "tool_call",
            t.task,
            system=SYSTEM_PROMPT,
            encode=qwen_encode,
            max_tokens=32768 - 512,
            template_id=self.episode.template_id,
            rule_mode=self.arm,
            rule_text=t.t_text,
        )
        messages = []
        if self.feedback:
            messages.append(
                Message(
                    f"tool{index}",
                    "tool",
                    "",
                    tool_results=tuple(self.feedback["results"]),
                    executed_tool_calls=tuple(self.feedback["executed"]),
                    artifact_hashes=tuple(self.executor.hashes().items()),
                )
            )
        messages.append(Message(f"m{index}", "user", t.request, t.events, adopted=True))
        self.messages = messages
        # Conservative pre-render bound, including system, retained history,
        # transport and 2048 tokens for all live rows/tombstones/chat delimiters.
        # Actual rendered length is checked against it in the dispatch callback.
        transport = compact(
            [
                dict(
                    role=m.role,
                    **(
                        {"tool_results": m.tool_results}
                        if m.tool_results
                        else {"text": m.text}
                    ),
                )
                for m in messages
            ]
        )
        self.bound = (
            len(self.session.history_ids)
            + len(qwen_encode(SYSTEM_PROMPT))
            + len(qwen_encode(transport))
            + len(qwen_encode(t.t_text))
            + 2048
        )
        return self.bound


def dispatch(model, lane, decoder):
    return model.generate(
        custom_generate=str(ROOT / "models/stencil-package"),
        trust_remote_code=True,
        local_files_only=True,
        session=lane.session,
        new_messages=lane.messages,
        decoder=decoder,
        tools=TOOL_SCHEMA,
        actuator="off",
        max_new_tokens=512,
    )


def run_episode(out, episode, model, tokenizer, mode, deadline, stub=False):
    lanes = [Lane(out, episode, arm, mode) for arm in ARMS]
    backends = (
        []
        if stub
        else [
            RetainedDecoder(
                model,
                tokenizer,
                lanes=4 if mode == "batch" else 1,
                deadline=deadline - 20,
            )
            for _ in range(1 if mode == "batch" else 4)
        ]
    )
    # Sequential backends share a model; only one hook set may be active per call.
    if not stub and mode != "batch":
        for backend in backends:
            backend.close()
    episode_start = time.monotonic()
    try:
        for index in range(len(episode.turns)):
            if time.monotonic() >= deadline - 45:
                break
            bounds = {lane.arm: lane.prepare(index) for lane in lanes}
            allowed = paired_context_gate(bounds)  # MUST precede every arm render.
            gate = dict(
                bounds=bounds,
                allowed=allowed,
                policy="conservative pre-render token bound; actual<=bound asserted",
            )
            for lane in lanes:
                lane.gate = gate
            if not allowed:
                append(
                    out / "events.jsonl",
                    dict(
                        event="paired_context_rejection",
                        episode=episode.episode_id,
                        mode=mode,
                        round=index,
                        **gate,
                    ),
                )
                break
            if mode == "batch":
                rendered = [None] * 4
                results = [None] * 4
                errors = []

                def compute(rendered=rendered, results=results, errors=errors):
                    try:
                        if stub:
                            text = reference(episode, lanes[0].round)
                            decoded = [
                                DecodeResult(text, qwen_encode(text), truncated=False)
                            ] * 4
                            measures = [dict(cpu_stub=True)] * 4
                        else:
                            decoded, measures = backends[0](rendered)
                        for i, lane in enumerate(lanes):
                            results[i] = decoded[i]
                            lane.measurement = measures[i]
                    except BaseException as exc:
                        errors.append(exc)

                barrier = threading.Barrier(4, action=compute)

                def worker(
                    i,
                    rendered=rendered,
                    results=results,
                    errors=errors,
                    barrier=barrier,
                ):
                    lane = lanes[i]

                    def decoder(req):
                        assert len(req.prompt_ids) <= lane.bound
                        rendered[i] = req
                        barrier.wait()
                        if errors:
                            raise errors[0]
                        return tool_calls(results[i])

                    try:
                        return dispatch(model, lane, decoder)
                    except BaseException:
                        barrier.abort()
                        raise

                with ThreadPoolExecutor(max_workers=4) as pool:
                    list(pool.map(worker, range(4)))
            else:
                for i, lane in enumerate(lanes):

                    def decoder(req, i=i, lane=lane, index=index):
                        assert len(req.prompt_ids) <= lane.bound
                        if stub:
                            text = reference(episode, index)
                            lane.measurement = dict(cpu_stub=True)
                            return tool_calls(
                                DecodeResult(text, qwen_encode(text), truncated=False)
                            )
                        backend = backends[i]
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
                        lane.measurement = measures[0]
                        return tool_calls(result[0])

                    dispatch(model, lane, decoder)
            print(
                compact(
                    dict(
                        mode=mode,
                        episode=episode.episode_id,
                        round=index,
                        tokens=[lane.rows[-1]["output_token_count"] for lane in lanes],
                        seconds=round(time.monotonic() - episode_start, 2),
                    )
                ),
                flush=True,
            )
            if any(lane.measurement.get("deadline_hit") for lane in lanes):
                break
    finally:
        for backend in backends:
            backend.close()
    wall = time.monotonic() - episode_start
    arm_costs = {lane.arm: sum(r["wall_seconds"] for r in lane.rows) for lane in lanes}
    outside_calls = max(0.0, wall - sum(arm_costs.values())) if mode != "batch" else 0.0
    receipt = dict(
        episode=episode.episode_id,
        mode=mode,
        rounds=len(lanes[0].rows),
        scheduled_rounds=len(episode.turns),
        wall_seconds=wall,
        complete=all(len(lane.rows) == len(episode.turns) for lane in lanes),
        arm_seconds={
            a: seconds + outside_calls / 4 for a, seconds in arm_costs.items()
        },
        preparation_overhead_seconds=outside_calls,
    )
    append(out / "episodes.jsonl", receipt)
    return lanes, receipt


def tool_calls(result):
    try:
        calls = json.loads(result.text).get("calls", [])
    except (ValueError, AttributeError):
        calls = []
    return replace(
        result, attempted_tool_calls=tuple(calls) if isinstance(calls, list) else ()
    )


def cpu(out):
    import torch
    from transformers import Qwen3MoeConfig, Qwen3MoeForCausalLM

    # Tiny CPU model exercises real HF custom_generate dispatch with stub outputs.
    torch.set_num_threads(2)
    model = Qwen3MoeForCausalLM(
        Qwen3MoeConfig(
            vocab_size=256,
            hidden_size=16,
            intermediate_size=16,
            moe_intermediate_size=8,
            num_hidden_layers=1,
            num_attention_heads=2,
            num_key_value_heads=1,
            head_dim=8,
            num_experts=2,
            num_experts_per_tok=1,
        )
    )
    episodes = bank()
    for index in ORDER[:4]:
        lanes, receipt = run_episode(
            out, episodes[index], model, None, "cpu", float("inf"), stub=True
        )
        assert receipt["complete"]
        assert all(
            r["oracle_checker_results"][0]["outcome"]["success"]
            for lane in lanes
            for r in lane.rows
        )
    _, batch_receipt = run_episode(
        out, episodes[0], model, None, "batch", float("inf"), stub=True
    )
    assert batch_receipt["complete"]
    write(
        out / "cpu-summary.json",
        dict(
            passed=True,
            episodes=[episodes[i].manifest() for i in ORDER[:4]],
            fields=sorted(FIELDS),
            rows=sum(len(episodes[i].turns) * 4 for i in ORDER[:4]) + 64,
        ),
    )


def run(out):
    import fcntl
    import subprocess

    import torch
    from transformers import AutoTokenizer, Qwen3MoeForCausalLM

    out.mkdir(parents=True, exist_ok=True)
    if (out / "records.jsonl").exists():
        raise ValueError("fresh GPU records required")
    recipe = json.loads((out / "recipe.json").read_text())
    for relative, expected in recipe["source_hashes"].items():
        if sha(ROOT / relative) != expected:
            raise ValueError(f"frozen source drift: {relative}")
    lock = (ROOT / ".review.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    flags = list((ROOT / "results/quick-checks").glob("*/RUNNING.flag"))
    if flags:
        raise ValueError(f"other Stencil flag: {flags}")
    processes = subprocess.check_output(
        [
            "nvidia-smi",
            "--query-compute-apps=pid,process_name",
            "--format=csv,noheader",
        ],
        text=True,
    )
    if any("python" in line for line in processes.splitlines()):
        raise ValueError("other GPU python present")
    flag = out / "RUNNING.flag"
    flag.write_text(f"composition-pilot {time.time()}\n")
    start = time.monotonic()
    deadline = start + 5400
    receipt = dict(started_at=time.time(), cap_seconds=5400, status="running")
    write(out / "run.json", receipt)
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
            experts_implementation="eager",
            local_files_only=True,
        ).eval()
        load_seconds = time.monotonic() - start
        receipt["load_seconds"] = load_seconds
        episodes = bank()
        # Required same-episode comparison is frozen first, regardless of scores.
        seq, seq_receipt = run_episode(
            out, episodes[0], model, tokenizer, "sequential", deadline
        )
        batch, batch_receipt = run_episode(
            out, episodes[0], model, tokenizer, "batch", deadline
        )
        comparisons = []
        for s, b in zip(seq, batch, strict=True):
            comparisons.append(
                dict(
                    arm=s.arm,
                    sequential_rounds=len(s.rows),
                    batch_rounds=len(b.rows),
                    identical=len(s.rows) == len(b.rows) == len(episodes[0].turns)
                    and all(
                        x["output"].encode() == y["output"].encode()
                        and x["eos"] == y["eos"]
                        for x, y in zip(s.rows, b.rows, strict=False)
                    ),
                    differing_rounds=[
                        i
                        for i, (x, y) in enumerate(zip(s.rows, b.rows, strict=False))
                        if x["output"].encode() != y["output"].encode()
                        or x["eos"] != y["eos"]
                    ],
                )
            )
        invariant = all(x["identical"] for x in comparisons)
        write(
            out / "batch-invariance.json",
            dict(
                passed=invariant,
                comparisons=comparisons,
                policy=(
                    "batch used prospectively only if all four full DEV-00 "
                    "trajectories match; otherwise sequential"
                ),
            ),
        )
        mode = "batch" if invariant else "sequential"
        receipt["selected_mode"] = mode
        for index in ORDER[1:]:
            if time.monotonic() >= deadline - 180:
                break
            # No outcome selection. Reserve based on worst observed per-round wall,
            # with 25% overhead. Decline an episode if it cannot finish in cap.
            prior = [
                json.loads(line)
                for line in (out / "episodes.jsonl").read_text().splitlines()
            ]
            rate = max(
                r["wall_seconds"] / r["rounds"]
                for r in prior
                if r["mode"] == mode and r["rounds"]
            )
            required = 1.25 * rate * len(episodes[index].turns) + 60
            if required > deadline - time.monotonic():
                append(
                    out / "events.jsonl",
                    dict(
                        event="fixed_order_budget_stop",
                        next_episode=episodes[index].episode_id,
                        required_seconds=required,
                        remaining_seconds=deadline - time.monotonic(),
                    ),
                )
                break
            _, ep = run_episode(out, episodes[index], model, tokenizer, mode, deadline)
            if not ep["complete"]:
                break
        receipt["status"] = "finished"
    except BaseException as exc:
        receipt.update(status="error", error=repr(exc))
        raise
    finally:
        if model is not None:
            del model
        import gc

        gc.collect()
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
        receipt.update(
            gpu_held_seconds=time.monotonic() - start,
            finished_at=time.time(),
            peak_cuda_bytes=torch.cuda.max_memory_allocated(),
        )
        write(out / "run.json", receipt)
        flag.unlink(missing_ok=True)
        fcntl.flock(lock, fcntl.LOCK_UN)
        lock.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["cpu", "run"], required=True)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    (cpu if args.mode == "cpu" else run)(args.out)


if __name__ == "__main__":
    main()
