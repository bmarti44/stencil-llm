"""CPU audit of saved scoped-run receipts through the frozen real consumer."""

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

import composition_pilot8_driver as d

from stencil.focus import slab2_v2 as s
from stencil.focus.loop import DecodeResult


def read(path):
    return json.loads(path.read_text())


def dump(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def audit(out, *, pilot):
    rows = [
        json.loads(line)
        for arm in "RNTQ"
        for line in (out / f"records-{arm}.jsonl").read_text().splitlines()
    ]
    index = {(r["episode_id"], r["arm"], r["turn"]): r for r in rows}
    assert len(index) == len(rows)
    pin = read(out / "pin-verification.json")
    root = Path(s.__file__).resolve().parents[3]
    assert Path(d.__file__).resolve().is_relative_to(root), "driver outside frozen pin"
    for name, expected in pin["source_hashes"].items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == expected, name
    episodes = s.bank("dev" if pilot else "eval")
    deterministic = not read(out / "determinism.json")["mismatches"]
    summary = read(out / "summary.json")
    rebuilt = (
        s.pilot_reading(rows, episodes, deterministic=deterministic)
        if pilot
        else s.larger_reading(
            rows,
            episodes,
            [e.episode_id for e in episodes[:16]],
            cpu_control=read(out / "composition-control.json")["passed"],
            calibrated=read(root / "results/larger-test-v2/freeze.json")[
                "dev_calibrated"
            ],
        )
    )
    assert rebuilt == summary, "frozen reading mismatch"
    counts = dict(responses=0, replayed_records=0, output_tokens=0, prompt_tokens=0)
    per_arm = {}
    for arm in "RNTQ":
        selected = [r for r in rows if r["arm"] == arm]
        per_arm[arm] = dict(
            records=len(selected),
            executing_lanes=len(
                {r["episode_id"] for r in selected if s.file_written(r)}
            ),
            repairs=sum(r["repairs_used"] for r in selected),
            initial_syntax=sum(
                r["attempts"][0]["execution"].get("category") == "syntax_error"
                for r in selected
            ),
            surviving_syntax=sum(
                r["execution"].get("category") == "syntax_error" for r in selected
            ),
            round_zero_rejections=sum(
                r["turn"] == 0 and bool(r["attempts"][0]["execution"].get("category"))
                for r in selected
            ),
            broken_episodes=len(
                {
                    r["episode_id"]
                    for r in selected
                    if r["outcome"]["diagnostics"]["breakage"]
                }
            ),
            final_integration=sum(
                r["turn"] == 15 and r["outcome"]["integration"] for r in selected
            ),
        )
    calls = {}

    def factory(e, arm, turn):
        def decode(rendered):
            key = (e.episode_id, arm, turn)
            attempt = calls.get(key, 0)
            calls[key] = attempt + 1
            row = index[key]
            saved = row["attempts"][attempt]
            receipt = read(
                out
                / "local/http"
                / f"main-attempt{attempt + 1}"
                / e.episode_id
                / arm
                / f"{turn}.json"
            )
            request, response = receipt["request"], receipt["response"]
            assert list(rendered.prompt_ids) == request["prompt"], key
            assert len(rendered.prompt_ids) + s.REPLY_CAP <= 32768
            assert (
                request["max_tokens"] == 2048
                and request["temperature"] == 0
                and request["seed"] == 20260906
            )
            choice = response["choices"][0]
            ids = saved["output_ids"] + (
                [saved["eos"]] if saved["eos"] is not None else []
            )
            assert choice["text"] == saved["output"]
            assert choice["token_ids"] == ids
            assert len(ids) == response["usage"]["completion_tokens"]
            assert (choice["finish_reason"] == "length") == saved["truncated"]
            counts["responses"] += 1
            counts["output_tokens"] += len(ids)
            counts["prompt_tokens"] += len(rendered.prompt_ids)
            return DecodeResult(
                saved["output"],
                tuple(saved["output_ids"]),
                eos=saved["eos"],
                truncated=saved["truncated"],
            )

        return decode

    with tempfile.TemporaryDirectory(prefix="slab2-v2-replay-") as tmp:
        for e in episodes:
            for arm in "RNTQ":
                selected = [
                    r
                    for r in rows
                    if r["episode_id"] == e.episode_id and r["arm"] == arm
                ]
                if not selected:
                    continue
                assert len(selected) == 16, "partial lane: cannot claim complete replay"
                replay = (d.run_q if arm == "Q" else d.run_lane)(
                    Path(tmp) / e.episode_id / arm,
                    e,
                    arm,
                    factory,
                    freeze_receipt=e.manifest()["episode_sha256"],
                )
                raw = [
                    json.loads(line)
                    for line in (out / "local/main" / e.episode_id / arm / "raw.jsonl")
                    .read_text()
                    .splitlines()
                ]
                assert (
                    replay["records"]
                    == raw
                    == sorted(selected, key=lambda r: r["turn"])
                ), (e.episode_id, arm)
                counts["replayed_records"] += len(raw)
    assert counts["replayed_records"] == len(rows)
    for relative, expected in read(out / "local-hashes.json").items():
        path = out / relative
        assert path.stat().st_size == expected["bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected["sha256"]
    groups = read(out / "groups.json")
    lane_seconds = (
        {a: sum(g["seconds"] for g in groups if g["arm"] == a) / 8 for a in "RNTQ"}
        if pilot and len(groups) == 8
        else None
    )
    projection = (
        (
            read(out / "ready.json")["load_seconds"]
            + 1.25 * (64 * sum(lane_seconds[a] for a in "RNT") + 16 * lane_seconds["Q"])
            + 1200
        )
        / 3600
        if lane_seconds
        else None
    )
    result = dict(
        **counts,
        per_arm=per_arm,
        frozen_reading_equal=True,
        full_prompt_feedback_executor_score_replay=True,
        local_hashes_verified=True,
        pinned_sha=pin["sha"],
        lane_seconds=lane_seconds,
        projected_full_gpu_hours=projection,
        gpu_held_hours=read(out / "lifecycle.json")["gpu_held_seconds"] / 3600,
    )
    dump(out / "audit.json", result)
    print(json.dumps(result, indent=2))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("out", type=Path)
    parser.add_argument("--pilot", action="store_true")
    args = parser.parse_args()
    audit(args.out, pilot=args.pilot)


if __name__ == "__main__":
    main()
