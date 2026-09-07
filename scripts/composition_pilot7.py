"""User-scoped pilot orchestration; pinned science source, bounded owned server."""

import concurrent.futures as cf
import fcntl
import hashlib
import json
import os
import subprocess
import threading
import time
import traceback
from pathlib import Path
from urllib.request import Request, urlopen

import composition_pilot5 as d

from stencil.focus import slab2_endpoint as ep

ROOT = Path("/home/bmarti44/stencil-llm")
OUT = ROOT / "results/quick-checks/composition-pilot-7"
PIN = Path(__file__).resolve().parents[1]
SHA = None

s = d.s
assert s.REPLY_CAP == 2048
LOCAL = OUT / "local"
END = float("inf")
LOCK = threading.Lock()
TIMINGS = {}


def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n")


def hashobj(x):
    return hashlib.sha256(
        json.dumps(x, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()


def cmd(args):
    p = subprocess.run(
        args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    if p.returncode:
        raise RuntimeError(f"{args[:3]}: {p.stdout}")
    return p.stdout.strip()


def factory(e, arm, turn, phase="main"):
    key = f"{phase}/{e.episode_id}/{arm}/{turn}"

    def transport(payload):
        if time.time() >= END - 180:
            raise TimeoutError("cooperative stop-new-work boundary")
        begin = time.time()
        receipt = dict(key=key, started=begin, request=payload)
        path = LOCAL / "http" / (key + ".json")
        dump(path, receipt)
        try:
            req = Request(
                "http://127.0.0.1:18088/v1/completions",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
            )
            with urlopen(req, timeout=min(1200, END - time.time() - 60)) as r:
                receipt["response"] = json.load(r)
            return receipt["response"]
        except Exception as exc:
            receipt["error"] = repr(exc)
            raise
        finally:
            receipt["ended"] = time.time()
            receipt["seconds"] = receipt["ended"] - begin
            dump(path, receipt)
            with LOCK:
                TIMINGS[key] = {k: receipt[k] for k in ("started", "ended", "seconds")}

    base = d.VLLMDecoder("http://127.0.0.1:18088/v1", "/model", transport)

    def decode(rendered):
        result = base(rendered)
        receipt = dict(
            key=key,
            prompt_sha256=hashobj(list(rendered.prompt_ids)),
            output_sha256=hashobj([list(result.output_ids), result.eos]),
            text_sha256=hashlib.sha256(result.text.encode()).hexdigest()
            if hasattr(result, "text")
            else None,
            timing=TIMINGS[key],
        )
        dump(OUT / "receipts" / (key + ".json"), receipt)
        return result

    return decode


def rows_for(phase):
    rows = []
    for p in sorted((LOCAL / phase).glob("slab2-dev-*/*/raw.jsonl")):
        for line in p.read_text().splitlines():
            row = json.loads(line)
            key = f"{phase}/{row['episode_id']}/{row['arm']}/{row['turn']}"
            row["output_sha256"] = hashobj([row["output_ids"], row["eos"]])
            row["text_sha256"] = hashlib.sha256(row["output"].encode()).hexdigest()
            row["timing"] = TIMINGS.get(key)
            row["file_written"] = s.file_written(row)
            rows.append(row)
    with (OUT / f"{phase}-records.jsonl").open("w") as f:
        for row in rows:
            f.write(json.dumps(row, separators=(",", ":")) + "\n")
    return rows


def summarize(phase, groups, load, n):
    rows = rows_for(phase)
    for row in rows:
        row["file_written"] = s.file_written(row)
    assert (OUT / f"{phase}-records.jsonl").stat().st_size <= 10_000_000
    byarm = {a: [r for r in rows if r["arm"] == a] for a in "QRNT"}
    floor = ep.strict_floor(rows) if len(byarm["T"]) == 128 else None
    if floor:
        dump(OUT / f"{phase}-floor.json", floor)
    costs = {
        a: sum(g["seconds"] for g in groups if g["arm"] == a) / 8
        for a in ep.ARMS
        if sum(g["lanes"] for g in groups if g["arm"] == a) == 8
    }
    projection = ep.projection(costs, load) if len(costs) == 4 else None
    fixture = json.loads(
        (PIN / "tests/fixtures/slab2_pilot6_registers.json").read_text()
    )
    cells = {(r["episode_id"], r["turn"]) for r in fixture["rows"] if r["matched"]}
    deterministic = (OUT / "determinism.json").exists() and not json.loads(
        (OUT / "determinism.json").read_text()
    )["mismatches"]
    summary = ep.pilot_reading(
        rows, s.bank(), floor, projection, cells, deterministic=deterministic
    )
    summary.update(
        phase=phase,
        n_rounds=n,
        lane_seconds=costs,
        groups=groups,
        load_seconds=load,
        pinned_sha=SHA,
        arm_roles=dict(
            Q="fresh-context reference", R="register", N="history", T="oracle text"
        ),
        O="dropped; byte-identical R replication documented in pilot6",
    )
    dump(OUT / f"{phase}-summary.json", summary)
    return summary


def run_phase(phase, n, load):
    episodes = s.bank(n_rounds=n)
    groups = []
    phase_start = time.time()
    for arm in "QRNT":
        for offset in (0, 4):
            if time.time() >= END - 180:
                return summarize(phase, groups, load, n)
            started = time.time()
            errors = []
            with cf.ThreadPoolExecutor(4) as pool:
                futs = [
                    pool.submit(
                        d.run_q if arm == "Q" else d.run_lane,
                        LOCAL / phase / e.episode_id / arm,
                        e,
                        arm,
                        lambda e, a, i: factory(e, a, i, phase),
                        n_rounds=n,
                    )
                    for e in episodes[offset : offset + 4]
                ]
                for f in futs:
                    try:
                        f.result()
                    except Exception as exc:
                        errors.append(repr(exc))
            groups.append(
                dict(
                    arm=arm,
                    offset=offset,
                    lanes=4 if not errors else 0,
                    seconds=time.time() - started,
                    errors=errors,
                )
            )
            dump(OUT / f"{phase}-groups.json", groups)
            print(
                json.dumps(
                    dict(
                        phase=phase,
                        arm=arm,
                        offset=offset,
                        elapsed=time.time() - START,
                        errors=errors,
                    )
                ),
                flush=True,
            )
            if errors:
                return summarize(phase, groups, load, n)
    overhead = max(0, time.time() - phase_start - sum(g["seconds"] for g in groups))
    for g in groups:
        g["seconds"] += overhead / len(groups)
    return summarize(phase, groups, load, n)


def gate():
    episodes = s.bank()
    prompts = {}

    class Captured(Exception):
        pass

    for e in episodes:

        def capture(e, a, i):
            def decode(rendered):
                prompts[e.episode_id] = rendered
                raise Captured()

            return decode

        try:
            d.run_lane(LOCAL / "capture" / e.episode_id / "R", e, "R", capture)
        except Captured:
            pass
    answers = {}
    for label, order in [
        ("forward", list(range(8))),
        ("reverse", list(reversed(range(8)))),
    ]:
        for off in (0, 4):
            ids = order[off : off + 4]
            with cf.ThreadPoolExecutor(4) as pool:
                futs = {
                    i: pool.submit(
                        factory(episodes[i], "R", 0, "gate-" + label),
                        prompts[episodes[i].episode_id],
                    )
                    for i in ids
                }
                for i, f in futs.items():
                    r = f.result()
                    answers[label, i] = dict(
                        ids=list(r.output_ids), eos=r.eos, truncated=r.truncated
                    )
    mismatches = [i for i in range(8) if answers["forward", i] != answers["reverse", i]]
    dump(
        OUT / "determinism.json",
        dict(
            prompts=8,
            concurrency=4,
            forward=list(range(8)),
            reverse=list(reversed(range(8))),
            mismatches=mismatches,
            outputs={f"{k[0]}-{k[1]}": v for k, v in answers.items()},
        ),
    )
    if mismatches:
        raise RuntimeError("determinism gate failed")


START = 0


def main():
    global START, END, SHA
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--pinned-sha", required=True)
    parser.add_argument("--cpu-smoke", action="store_true")
    args_cli = parser.parse_args()
    SHA = args_cli.pinned_sha
    assert cmd(["git", "-C", str(PIN), "rev-parse", "HEAD"]) == SHA
    cmd(["git", "-C", str(PIN), "diff", "HEAD", "--exit-code"])
    assert all(
        Path(module.__file__).resolve().is_relative_to(PIN) for module in (s, d, ep)
    )
    if args_cli.cpu_smoke:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            e = s.generate_episode("dev", 0)
            lane = d.run_lane(Path(tmp) / "lane", e, "R", d.stub_factory)
            assert len(lane["records"]) == 16 and all(
                r["execution"]["executed"] for r in lane["records"]
            )
        print("CPU pinned lane/cap2048 smoke PASS")
        return
    assert not (OUT / "launch.json").exists(), "refuse overwrite of launched pilot"
    with (ROOT / ".stencil-owned-pids").open("a") as f:
        f.write(str(os.getpid()) + "\n")
    while True:
        with (ROOT / ".review.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            others = list((ROOT / "results/quick-checks").glob("*/RUNNING.flag"))
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
                if line.strip() and not line.strip().startswith("2705,")
            ]
            if not others and not busy:
                START = time.time()
                END = START + 5400
                with (OUT / "RUNNING.flag").open("x") as f:
                    json.dump(dict(pid=os.getpid(), start=START, deadline=END), f)
                break
        print("Waiting for Stencil GPU availability", flush=True)
        time.sleep(15)
    name = f"stencil-pilot7-{int(START)}"
    args = json.loads(
        (ROOT / "results/quick-checks/vllm-qual/attempts.json").read_text()
    )[0]["command"]
    args[args.index("--name") + 1] = name
    args[args.index("-p") + 1] = "127.0.0.1:18088:8000"
    dump(
        OUT / "launch.json",
        dict(
            command=args,
            pinned_sha=SHA,
            source=s.__file__,
            system_sha256=hashobj(s.SYSTEM_PROMPT),
            cap=2048,
            start=START,
        ),
    )
    launched = False
    try:
        container = cmd(args)
        launched = True
        dump(OUT / "container.json", dict(name=name, id=container))
        while time.time() < END - 180:
            if (
                cmd(["docker", "inspect", "--format", "{{.State.Status}}", name])
                != "running"
            ):
                raise RuntimeError("server exited at startup")
            try:
                with urlopen("http://127.0.0.1:18088/health", timeout=2) as r:
                    if r.status == 200:
                        break
            except Exception:
                pass
            time.sleep(3)
        else:
            raise TimeoutError("startup deadline")
        load = time.time() - START
        dump(OUT / "ready.json", dict(load_seconds=load, ready=time.time()))
        print(f"Server ready after {load:.3f}s", flush=True)
        gate()
        print("Determinism 8/8 exact", flush=True)
        summary = run_phase("main", 16, load)
        dump(OUT / "summary.json", summary)
    except Exception:
        (OUT / "error.txt").write_text(traceback.format_exc())
        raise
    finally:
        if launched:
            stop = cmd(["docker", "stop", "-t", "20", name])
            (OUT / "server.log").write_text(
                cmd(["docker", "logs", "--timestamps", name]) + "\n"
            )
            remove = cmd(["docker", "rm", name])
            dump(OUT / "cleanup.json", dict(name=name, stop=stop, remove=remove))
        held = time.time() - START
        dump(
            OUT / "lifecycle.json",
            dict(
                start=START, end=time.time(), gpu_held_seconds=held, budget_seconds=5400
            ),
        )
        if (OUT / "summary.json").exists() and held > 5400:
            summary = json.loads((OUT / "summary.json").read_text())
            summary["reading"] = "INELIGIBLE"
            summary["failures"].append("actual GPU-held budget>5400s")
            dump(OUT / "summary.json", summary)
        (OUT / "RUNNING.flag").unlink(missing_ok=True)
        manifest = {
            str(p.relative_to(OUT)): dict(
                bytes=p.stat().st_size,
                sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
            )
            for p in LOCAL.rglob("*")
            if p.is_file()
        }
        dump(OUT / "local-hashes.json", manifest)


if __name__ == "__main__":
    main()
