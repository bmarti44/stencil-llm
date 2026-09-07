"""Amendment-3 eight-lane screen; owned container, cooperative 900s budget.

Fit-on none; evaluated-on first two authored DEV episodes only. No eval bank.
Run from a clean pinned checkout with --sha FULL_SHA --out ABSOLUTE_DIRECTORY.
"""

import argparse
import concurrent.futures as cf
import fcntl
import hashlib
import json
import os
import subprocess
import threading
import time
from pathlib import Path
from urllib.request import Request, urlopen

import composition_pilot5 as d

s = d.s


def command(args):
    result = subprocess.run(
        args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=True
    )
    return result.stdout.strip()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def run(args):
    pin = Path(__file__).resolve().parents[1]
    root, out = Path(args.root), Path(args.out)
    assert pin != root and out.is_absolute()
    assert command(["git", "-C", str(pin), "rev-parse", "HEAD"]) == args.sha
    command(["git", "-C", str(pin), "diff", "HEAD", "--exit-code"])
    assert Path(s.__file__).resolve().is_relative_to(pin)
    # User's pilot-5 cap; no import-time mutation.
    s.REPLY_CAP = 1024
    s.SYSTEM_PROMPT = s.SYSTEM_PROMPT.replace("2048", "1024")
    episodes = s.bank()[:2]
    references = {
        e.episode_id: sum(len(s.qwen_encode(s.reference(e, j))) + 1 for j in range(16))
        for e in episodes
    }
    out.mkdir(parents=True, exist_ok=True)
    if (out / "launch.json").exists():
        raise ValueError("screen already launched; do not overwrite")
    with (root / ".stencil-owned-pids").open("a") as stream:
        stream.write(str(os.getpid()) + "\n")
    with (root / ".review.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        flags = list((root / "results/quick-checks").glob("*/RUNNING.flag"))
        if flags:
            raise RuntimeError(f"wait for other Stencil flags: {flags}")
        gpu = command(
            [
                "nvidia-smi",
                "--query-compute-apps=pid,process_name",
                "--format=csv,noheader",
            ]
        )
        if any(
            line.strip() and not line.strip().startswith("2705,")
            for line in gpu.splitlines()
        ):
            raise RuntimeError("other GPU compute: " + gpu)
        start = time.monotonic()
        deadline = start + 900
        with (out / "RUNNING.flag").open("x") as stream:
            json.dump(
                dict(pid=os.getpid(), start=time.time(), budget_seconds=900), stream
            )
    name = f"stencil-pilot5-screen-{os.getpid()}"
    launch = json.loads(
        (root / "results/quick-checks/vllm-qual/attempts.json").read_text()
    )[0]["command"]
    launch[launch.index("--name") + 1] = name
    launch[launch.index("-p") + 1] = "127.0.0.1:18086:8000"
    write(
        out / "launch.json",
        dict(
            command=launch,
            pinned_sha=args.sha,
            source=s.__file__,
            system_sha256=hashlib.sha256(s.SYSTEM_PROMPT.encode()).hexdigest(),
            cap=s.REPLY_CAP,
            gpu_exception=dict(
                pid=2705,
                owner="Brian",
                reason="permanent llama-server, user authorized coexistence",
            ),
            references=references,
            budget_seconds=900,
            concurrency=4,
            groups=["dev00 RNTQ", "dev01 RNTQ"],
        ),
    )
    stopping = threading.Lock()
    stopped = threading.Event()
    finished = threading.Event()
    launched = False
    groups = []
    errors = []

    def stop_owned():
        with stopping:
            if not stopped.is_set():
                result = command(["docker", "stop", "-t", "10", name])
                write(
                    out / "stop.json",
                    dict(result=result, elapsed=time.monotonic() - start),
                )
                stopped.set()

    def watchdog():
        if not finished.wait(max(0, deadline - time.monotonic() - 25)):
            try:
                stop_owned()
            except Exception as exc:
                write(out / "watchdog-error.json", dict(error=repr(exc)))

    def factory(e, arm, turn):
        def transport(payload):
            remaining = deadline - time.monotonic()
            if remaining < 55 or stopped.is_set():
                raise TimeoutError("cooperative stop-new-work boundary")
            path = out / "local/http" / e.episode_id / arm / f"{turn}.json"
            receipt = dict(request=payload, start=time.time())
            write(path, receipt)
            try:
                request = Request(
                    "http://127.0.0.1:18086/v1/completions",
                    data=json.dumps(payload).encode(),
                    headers={"Content-Type": "application/json"},
                )
                with urlopen(request, timeout=min(120, remaining - 30)) as response:
                    receipt["response"] = json.load(response)
                return receipt["response"]
            except Exception as exc:
                receipt["error"] = repr(exc)
                raise
            finally:
                receipt["end"] = time.time()
                write(path, receipt)

        return d.VLLMDecoder("http://127.0.0.1:18086/v1", "/model", transport)

    try:
        container = command(launch)
        launched = True
        write(out / "container.json", dict(name=name, id=container))
        watcher = threading.Thread(target=watchdog, daemon=True)
        watcher.start()
        while time.monotonic() < deadline - 55:
            if (
                command(["docker", "inspect", "--format", "{{.State.Status}}", name])
                != "running"
            ):
                raise RuntimeError("owned server exited")
            try:
                with urlopen("http://127.0.0.1:18086/health", timeout=2) as response:
                    if response.status == 200:
                        break
            except Exception:
                pass
            time.sleep(2)
        else:
            raise TimeoutError("startup budget exhausted")
        write(out / "ready.json", dict(load_seconds=time.monotonic() - start))
        print(f"Server ready at {time.monotonic() - start:.1f}s", flush=True)
        for e in episodes:
            begun = time.monotonic()
            with cf.ThreadPoolExecutor(4) as pool:
                futures = {
                    arm: pool.submit(
                        d.run_q if arm == "Q" else d.run_lane,
                        out / "local/lanes" / e.episode_id / arm,
                        e,
                        arm,
                        factory,
                    )
                    for arm in "RNTQ"
                }
                for arm, future in futures.items():
                    try:
                        future.result()
                    except Exception as exc:
                        errors.append(
                            dict(episode_id=e.episode_id, arm=arm, error=repr(exc))
                        )
            groups.append(
                dict(episode_id=e.episode_id, seconds=time.monotonic() - begun)
            )
            print(
                json.dumps(
                    dict(groups=groups, elapsed=time.monotonic() - start, errors=errors)
                ),
                flush=True,
            )
            if errors:
                break
    except Exception as exc:
        errors.append(dict(error=repr(exc)))
    finally:
        if launched:
            stop_owned()
            (out / "server.log").write_text(
                command(["docker", "logs", "--timestamps", name]) + "\n"
            )
            write(
                out / "cleanup.json",
                dict(name=name, removed=command(["docker", "rm", name])),
            )
        finished.set()
        write(
            out / "lifecycle.json",
            dict(gpu_held_seconds=time.monotonic() - start, budget_seconds=900),
        )
        (out / "RUNNING.flag").unlink(missing_ok=True)
        rows = [
            json.loads(line)
            for path in sorted((out / "local/lanes").glob("*/*/raw.jsonl"))
            for line in path.read_text().splitlines()
        ]
        with (out / "records.jsonl").open("w") as stream:
            for row in rows:
                row["file_written"] = s.file_written(row)
                stream.write(json.dumps(row, separators=(",", ":")) + "\n")
        assert (out / "records.jsonl").stat().st_size <= 10_000_000
        summary = s.screen_reading(rows)
        summary.update(groups=groups, errors=errors, pinned_sha=args.sha)
        for arm, metric in summary["per_arm"].items():
            rr = [r for r in rows if r["arm"] == arm]
            denominator = sum(
                len(s.qwen_encode(s.reference(e, r["turn"]))) + 1
                for r in rr
                for e in episodes
                if e.episode_id == r["episode_id"]
            )
            metric.update(
                output_tokens=sum(r["output_tokens"] for r in rr),
                reference_tokens=denominator,
                largest_reply=max((r["output_tokens"] for r in rr), default=0),
            )
            metric["x_factor"] = (
                metric["output_tokens"] / denominator if denominator else None
            )
        write(out / "summary.json", summary)
        write(
            out / "local-hashes.json",
            {
                str(p.relative_to(out)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in (out / "local").rglob("*")
                if p.is_file()
            },
        )
        print(json.dumps(summary), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--root", default="/home/bmarti44/stencil-llm")
    run(parser.parse_args())


if __name__ == "__main__":
    main()
