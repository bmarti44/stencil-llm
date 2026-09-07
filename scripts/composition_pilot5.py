"""SLAB-2 DEV driver. CPU stubs and vLLM use the identical loop/executor path.

The GPU owner supplies an already-held vLLM server and its measured load time.
No model/server launch, process management, or evaluation content is performed.
Completion API: https://docs.vllm.ai/en/latest/serving/openai_compatible_server/
"""

import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request as HTTPRequest
from urllib.request import urlopen

from stencil.focus import slab2 as s
from stencil.focus.journal import Journal
from stencil.focus.loop import DecodeResult, Message, Session, generate_once
from stencil.focus.register import Register
from stencil.focus.renderer import Request, compact


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n")


class VLLMDecoder:
    """Token-ID completion transport; server must return actual generated IDs."""

    def __init__(self, endpoint, model, transport=None):
        self.endpoint, self.model = endpoint.rstrip("/"), model
        self.transport = transport or self._post

    def _post(self, payload):
        request = HTTPRequest(
            self.endpoint + "/completions",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=300) as response:
            return json.load(response)

    def __call__(self, rendered):
        if len(rendered.prompt_ids) + s.REPLY_CAP > 32768:
            raise ValueError("context gate")
        started = time.monotonic()
        response = self.transport(
            dict(
                model=self.model,
                prompt=list(rendered.prompt_ids),
                max_tokens=s.REPLY_CAP,
                temperature=0,
                seed=20260906,
                return_token_ids=True,
            )
        )
        choice = response["choices"][0]
        ids = choice.get("token_ids")
        if ids is None or choice["finish_reason"] not in {"stop", "length"}:
            raise ValueError("vLLM requires token_ids and terminal finish_reason")
        if len(ids) != response["usage"]["completion_tokens"]:
            raise ValueError("vLLM token accounting mismatch")
        # loop appends EOS separately; keep it out of output_ids to avoid a
        # duplicated conversation terminator in every subsequent prompt.
        eos = None
        terminal_ids = {
            s.qwen_encode(token)[0] for token in ("<|im_end|>", "<|endoftext|>")
        }
        if choice["finish_reason"] == "stop" and ids and ids[-1] in terminal_ids:
            eos, ids = ids[-1], ids[:-1]
        return DecodeResult(
            choice["text"],
            tuple(ids),
            eos=eos,
            truncated=choice["finish_reason"] == "length",
            gpu_held_seconds=time.monotonic() - started,
        )


def run_lane(directory, episode, arm, decoder_factory, *, n_rounds=16):
    """Factory receives DEV episode/arm/turn; real adapter ignores these values."""
    s.validate_rounds(n_rounds)
    if (
        episode.family != "dev"
        or len(episode.turns) != n_rounds
        or arm not in "RNTO"
        or len(arm) != 1
    ):
        raise ValueError("matching DEV lane required")
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=False)
    s.materialize(episode, root / "workspace")
    executor = s.Executor(root / "workspace", episode)
    session = Session(
        Register(defaults=episode.defaults, task_handles={"A", "B"}),
        Request("", "tool_call"),
        Journal(root / "loop.jsonl"),
    )
    rows, feedback = [], None
    for i, turn in enumerate(episode.turns):
        session.request = Request(
            "",
            "tool_call",
            turn.task,
            encode=s.qwen_encode,
            system=s.SYSTEM_PROMPT,
            max_tokens=32768 - s.REPLY_CAP,
            rule_mode=arm,
            rule_text=turn.t_text,
            template_id=episode.template_id,
        )
        messages = []
        if feedback is not None:
            messages.append(Message(f"tool{i}", "tool", "", tool_results=(feedback,)))
        messages.append(
            Message(f"m{i}", "user", turn.request, turn.events, adopted=True)
        )
        decoded = None
        prompt_tokens = None

        def decode(rendered, i=i):
            nonlocal decoded, prompt_tokens
            prompt_tokens = len(rendered.prompt_ids)
            if prompt_tokens + s.REPLY_CAP > 32768:
                raise ValueError("context gate")
            decoded = decoder_factory(episode, arm, i)(rendered)
            if (
                not isinstance(decoded, DecodeResult)
                or decoded.truncated is None
                or decoded.output_ids is None
            ):
                raise ValueError("decoder must report truncation and output IDs")
            return decoded

        output, _ = generate_once(session, messages, decode)
        feedback = executor.run(output, i, truncated=decoded.truncated)
        row = dict(
            episode_id=episode.episode_id,
            arm=arm,
            turn=i,
            truncated=decoded.truncated,
            output_tokens=len(decoded.output_ids) + int(decoded.eos is not None),
            eos=decoded.eos,
            prompt_tokens=prompt_tokens,
            execution=feedback,
            outcome=s.check(episode, i, executor, eligible_traits=None),
        )
        with (root / "raw.jsonl").open("a") as stream:
            stream.write(compact(row) + "\n")
        rows.append(row)
    return dict(
        episode_id=episode.episode_id,
        arm=arm,
        records=rows,
        output_tokens=sum(row["output_tokens"] for row in rows),
    )


def rescore(records, floor):
    """Use saved exact per-round checks, never a later workspace snapshot."""
    scored = json.loads(json.dumps(records))
    eligible = floor["eligible_traits"]
    for row in scored:
        outcome = row["outcome"]
        outcome.update(
            floor_pending=False,
            relapse={
                k: outcome["raw_relapse"][k] if outcome["observed"] else None
                for k in eligible
            },
            success=bool(
                outcome["observed"]
                and outcome["integration"]
                and outcome["report_ok"]
                and not any(
                    outcome["diagnostics"][k]
                    for k in (*eligible, "breakage", "wrong_family")
                )
            ),
        )
    return scored


def run_pilot(
    out,
    decoder_factory,
    *,
    cpu_stub=False,
    n_rounds=16,
    prior_projection=None,
    load_seconds=0,
    max_workers=s.MAX_WORKERS,
    clock=time.monotonic,
):
    s.validate_rounds(n_rounds)
    if max_workers != s.MAX_WORKERS:
        raise ValueError("pilot and registered run require max_workers=4")
    if (
        n_rounds == 12
        and not cpu_stub
        and not (prior_projection is not None and 12 < prior_projection <= 15)
    ):
        raise ValueError("12 rounds require measured 16-round cost fallback")
    if load_seconds < 0:
        raise ValueError("negative load seconds")
    started = clock()
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    # O DEV lanes measure O cost directly; R/N/T are the scientific pilot rows.
    episodes = s.bank(n_rounds=n_rounds)
    write(
        out / "registration.json",
        dict(
            n_rounds=n_rounds,
            max_workers=max_workers,
            cpu_stub=cpu_stub,
            prior_projection=prior_projection,
            load_seconds=load_seconds,
            source_sha256=s.hashlib.sha256(Path(s.__file__).read_bytes()).hexdigest(),
            driver_sha256=s.hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            manifests=[e.manifest() for e in episodes],
            lane_seconds_definition=(
                "GPU-held group wall / concurrently held lanes; "
                "overhead allocated equally"
            ),
        ),
    )
    lanes, charged = [], 0.0
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        for arm in "RNTO":
            for offset in range(0, 8, max_workers):
                group = episodes[offset : offset + max_workers]
                group_start = clock()
                futures = [
                    pool.submit(
                        run_lane,
                        out / e.episode_id / arm,
                        e,
                        arm,
                        decoder_factory,
                        n_rounds=n_rounds,
                    )
                    for e in group
                ]
                completed = [future.result() for future in futures]
                wall = clock() - group_start
                charged += wall
                for lane in completed:
                    lane.update(
                        lane_seconds=None if cpu_stub else wall / len(group),
                        cpu_group_seconds=wall if cpu_stub else None,
                        concurrent_lanes=len(group),
                    )
                lanes.extend(completed)
                write(
                    out / "progress.json",
                    dict(completed_lanes=len(lanes), n_rounds=n_rounds),
                )
    records = [row for lane in lanes for row in lane["records"]]
    floor = s.freeze_t_floor([r for r in records if r["arm"] == "T"], n_rounds)
    write(out / "floor.json", floor)  # Must precede any scoring.
    write(out / "scored.json", rescore(records, floor))
    held = clock() - started
    overhead = max(0, held - charged) / len(lanes)
    if not cpu_stub:
        for lane in lanes:
            lane["lane_seconds"] += overhead
    costs = (
        {
            a: sum(lane["lane_seconds"] for lane in lanes if lane["arm"] == a) / 8
            for a in "RNTO"
        }
        if not cpu_stub
        else None
    )
    projection = (
        s.measured_projection(costs, load_seconds=load_seconds, max_workers=max_workers)
        if costs
        else None
    )
    summary = dict(
        n_rounds=n_rounds,
        cpu_stub=cpu_stub,
        max_workers=max_workers,
        gpu_held_seconds=None if cpu_stub else held,
        lane_seconds=costs,
        projected_gpu_hours=projection,
        lanes=[{k: v for k, v in lane.items() if k != "records"} for lane in lanes],
        output_tokens_per_arm={
            a: [lane["output_tokens"] for lane in lanes if lane["arm"] == a]
            for a in "RNTO"
        },
        largest_reply_tokens=max(r["output_tokens"] for r in records),
        reading=s.pilot5_reading(
            [r for r in records if r["arm"] in "RNT"], floor, projection, n_rounds
        ),
    )
    write(out / "summary.json", summary)
    return summary


def stub_factory(episode, arm, turn):
    text = s.reference(episode, turn)
    return lambda rendered: DecodeResult(
        text, tuple(s.qwen_encode(text)), truncated=False
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cpu-stub", action="store_true")
    parser.add_argument("--endpoint", default="http://127.0.0.1:8000/v1")
    parser.add_argument("--model")
    parser.add_argument("--load-seconds", type=float)
    parser.add_argument("--n-rounds", type=int, choices=(16, 12), default=16)
    parser.add_argument("--prior-projection", type=float)
    args = parser.parse_args()
    if not args.cpu_stub and (not args.model or args.load_seconds is None):
        parser.error("GPU owner must supply --model and measured --load-seconds")
    decoder = None if args.cpu_stub else VLLMDecoder(args.endpoint, args.model)
    summary = run_pilot(
        args.out,
        stub_factory if args.cpu_stub else lambda e, a, i: decoder,
        cpu_stub=args.cpu_stub,
        n_rounds=args.n_rounds,
        prior_projection=args.prior_projection,
        load_seconds=args.load_seconds or 0,
    )
    print(compact(summary["reading"]))


if __name__ == "__main__":
    main()
