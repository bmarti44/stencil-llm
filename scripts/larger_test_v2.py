"""Frozen Amendment 6 pilot/evaluation launcher. No import-time execution."""

import argparse
import concurrent.futures as cf
import fcntl
import hashlib
import json
import os
import time
import traceback
from pathlib import Path
from urllib.request import urlopen

import composition_pilot7 as p
import composition_pilot8_driver as d
import larger_test as previous

from stencil.focus import slab2_v2 as s

ROOT = p.ROOT
PIN = Path(__file__).resolve().parents[1]
dump, cmd, hashobj = p.dump, p.cmd, p.hashobj


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def factory(e, arm, turn):
    count = 0

    def decode(rendered):
        nonlocal count
        count += 1
        if count > 2:
            raise ValueError("more than one repair")
        return p.factory(e, arm, turn, phase=f"main-attempt{count}")(rendered)

    # Driver requests a decoder each call, so counters belong to transport keys,
    # assigned from existing immutable receipts, with one sequential lane per key.
    first = p.LOCAL / "http" / "main-attempt1" / e.episode_id / arm / f"{turn}.json"
    count = int(first.exists())
    return decode


def collect(out, episodes, registration, control, pilot):
    rows = []
    for path in sorted((out / "local/main").glob("*/*/raw.jsonl")):
        rows.extend(json.loads(line) for line in path.read_text().splitlines())
    for arm in "RNTQ":
        body = "".join(
            json.dumps(r, separators=(",", ":")) + "\n" for r in rows if r["arm"] == arm
        )
        assert len(body.encode()) <= 10_000_000
        (out / f"records-{arm}.jsonl").write_text(body)
    deterministic = (out / "determinism.json").exists() and not json.loads(
        (out / "determinism.json").read_text()
    )["mismatches"]
    if pilot:
        result = s.pilot_reading(rows, episodes, deterministic=deterministic)
    else:
        result = s.larger_reading(
            rows,
            episodes,
            registration["q_ids"],
            cpu_control=control,
            calibrated=registration.get("dev_calibrated") is True,
        )
        if (
            not deterministic
            or not (out / "reproducibility.json").exists()
            or not json.loads((out / "reproducibility.json").read_text()).get(
                "complete"
            )
        ):
            result["failures"].append("determinism or reproducibility incomplete")
            result["reading"] = "INCOMPLETE"
    dump(out / "summary.json", result)
    return result


def run_groups(out, episodes, registration, pilot):
    indexed = {e.episode_id: e for e in episodes}
    groups = []
    for group in registration["pilot_schedule" if pilot else "schedule"]:
        if time.time() >= p.END - (300 if pilot else 1500):
            break
        start = time.time()
        errors = []
        with cf.ThreadPoolExecutor(4) as pool:
            futures = [
                pool.submit(
                    d.run_q if group["arm"] == "Q" else d.run_lane,
                    out / "local/main" / eid / group["arm"],
                    indexed[eid],
                    group["arm"],
                    factory,
                    freeze_receipt=indexed[eid].manifest()["episode_sha256"],
                )
                for eid in group["ids"]
            ]
            for f in futures:
                try:
                    f.result()
                except Exception as exc:
                    errors.append(repr(exc))
        groups.append(dict(**group, seconds=time.time() - start, errors=errors))
        dump(out / "groups.json", groups)
        print(json.dumps(groups[-1]), flush=True)
        if errors:
            break
        if not pilot and group["id"] == registration["replay_after_group"]:
            previous.OUT = out
            previous.replay_control(registration)
    return groups


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pinned-sha", required=True)
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--cpu-smoke", action="store_true")
    args = parser.parse_args()
    sha = cmd(["git", "-C", str(PIN), "rev-parse", "HEAD"])
    assert sha == args.pinned_sha and PIN != ROOT
    cmd(["git", "-C", str(PIN), "diff", "HEAD", "--exit-code"])
    assert all(
        Path(m.__file__).resolve().is_relative_to(PIN) for m in (s, d, p, previous)
    )
    registration = json.loads((PIN / "results/larger-test-v2/freeze.json").read_text())
    for name, expected in registration["source_hashes"].items():
        assert digest(PIN / name) == expected, name
    if args.cpu_smoke:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            result = d.run_lane(
                Path(tmp) / "lane", s.generate_episode(), "R", d.stub_factory
            )
            assert len(result["records"]) == 16 and all(
                s.file_written(r) for r in result["records"]
            )
        print("Frozen scoped consumer CPU smoke PASS", flush=True)
        return
    out = ROOT / (
        "results/quick-checks/composition-pilot-8"
        if args.pilot
        else "results/larger-test-v2"
    )
    out.mkdir(parents=True, exist_ok=True)
    marker = out / ("pilot-opened.json" if args.pilot else "evaluation-opened.json")
    assert not marker.exists(), "refuse reopened run"
    if not args.pilot:
        calibration = json.loads(
            (PIN / "results/larger-test-v2/dev-calibration.json").read_text()
        )
        assert (
            registration["dev_calibrated"] is True and calibration["eligible"] is True
        )
        assert (
            digest(PIN / "results/larger-test-v2/dev-calibration.json")
            == registration["calibration_sha256"]
        )
    with marker.open("x") as f:
        json.dump(dict(sha=sha, time=time.time()), f)
    episodes = s.bank("dev" if args.pilot else "eval")
    assert {
        e.episode_id: e.manifest()["episode_sha256"] for e in episodes
    } == registration["dev_episode_hashes" if args.pilot else "episode_hashes"]
    control = previous.composition_control(episodes)
    assert control["episode_count"] == len(episodes)
    dump(out / "composition-control.json", control)
    dump(
        out / "pin-verification.json",
        dict(sha=sha, pin=str(PIN), source_hashes=registration["source_hashes"]),
    )
    p.OUT, p.LOCAL, p.PIN, p.SHA, p.s, p.d = out, out / "local", PIN, sha, s, d
    flag = (
        out / "RUNNING.flag"
        if args.pilot
        else ROOT / "results/quick-checks/larger-test-v2/RUNNING.flag"
    )
    flag.parent.mkdir(parents=True, exist_ok=True)
    with (ROOT / ".stencil-owned-pids").open("a") as f:
        f.write(str(os.getpid()) + "\n")
    queued = time.time()
    while True:
        with (ROOT / ".review.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            flags = list((ROOT / "results/quick-checks").glob("*/RUNNING.flag"))
            gpu = cmd(
                [
                    "nvidia-smi",
                    "--query-compute-apps=pid,process_name",
                    "--format=csv,noheader",
                ]
            )
            busy = [
                line
                for line in gpu.splitlines()
                if line.strip()
                and "llama-server" not in line
                and not line.strip().startswith("2705,")
            ]
            if not flags and not busy:
                p.START = time.time()
                p.END = p.START + (5400 if args.pilot else 41400)
                with flag.open("x") as f:
                    json.dump(
                        dict(pid=os.getpid(), sha=sha, start=p.START, deadline=p.END), f
                    )
                break
        print("Waiting for Stencil compute/flags", flush=True)
        time.sleep(15)
    name = f"stencil-amendment6-{int(p.START)}"
    command = list(registration["container_command"])
    command[command.index("--name") + 1] = name
    dump(
        out / "launch.json",
        dict(
            command=command,
            sha=sha,
            start=p.START,
            deadline=p.END,
            queue_seconds=p.START - queued,
        ),
    )
    launched = False
    try:
        container = cmd(command)
        launched = True
        dump(out / "container.json", dict(name=name, id=container))
        while time.time() < p.END - 300:
            assert (
                cmd(["docker", "inspect", "--format", "{{.State.Status}}", name])
                == "running"
            )
            try:
                with urlopen("http://127.0.0.1:18088/health", timeout=2) as response:
                    if response.status == 200:
                        break
            except Exception:
                pass
            time.sleep(3)
        else:
            raise TimeoutError("startup deadline")
        dump(out / "ready.json", dict(load_seconds=time.time() - p.START))
        print("Server ready; determinism first", flush=True)
        p.gate()
        run_groups(out, episodes, registration, args.pilot)
    except Exception:
        (out / "error.txt").write_text(traceback.format_exc())
        print(traceback.format_exc(), flush=True)
    finally:
        try:
            if launched:
                stopped = cmd(["docker", "stop", "-t", "20", name])
                (out / "server.log").write_text(
                    cmd(["docker", "logs", "--timestamps", name]) + "\n"
                )
                removed = cmd(["docker", "rm", name])
                dump(
                    out / "cleanup.json", dict(name=name, stop=stopped, remove=removed)
                )
        finally:
            held = time.time() - p.START
            dump(
                out / "lifecycle.json",
                dict(
                    start=p.START,
                    end=time.time(),
                    gpu_held_seconds=held,
                    budget_seconds=5400 if args.pilot else 41400,
                ),
            )
            flag.unlink(missing_ok=True)
        summary = collect(out, episodes, registration, control["passed"], args.pilot)
        if held > (5400 if args.pilot else 41400):
            summary["reading"] = "STOP" if args.pilot else "INCOMPLETE"
            summary["failures"].append("GPU-held deadline")
            dump(out / "summary.json", summary)
        dump(
            out / "local-hashes.json",
            {
                str(x.relative_to(out)): dict(bytes=x.stat().st_size, sha256=digest(x))
                for x in (out / "local").rglob("*")
                if x.is_file()
            },
        )
        print(
            json.dumps(dict(reading=summary["reading"], failures=summary["failures"])),
            flush=True,
        )


if __name__ == "__main__":
    main()
