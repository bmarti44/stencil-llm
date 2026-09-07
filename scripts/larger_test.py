"""Amendment 5 one-shot runner; no work at import, evaluation only after freeze."""

import argparse
import concurrent.futures as cf
import fcntl
import hashlib
import json
import os
import time
import traceback
from dataclasses import asdict, replace
from pathlib import Path
from urllib.request import Request as HTTPRequest
from urllib.request import urlopen

import composition_pilot7 as p

from stencil.focus.register import Entry, Evidence, Register, Scope, Source
from stencil.focus.renderer import Request, render

ROOT = p.ROOT
PIN = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/larger-test"
FLAG = ROOT / "results/quick-checks/larger-test/RUNNING.flag"
s, d, ep = p.s, p.d, p.ep
dump, cmd, hashobj = p.dump, p.cmd, p.hashobj


def digest_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def entry(x):
    return Entry(
        **{
            **x,
            "scope": Scope(**x["scope"]),
            "source": Source(**x["source"]),
            "evidence": Evidence(**x["evidence"]) if x["evidence"] else None,
        }
    )


def composition_control(episodes):
    historical = json.loads(
        (PIN / "tests/fixtures/slab2_pilot6_registers.json").read_text()
    )["rows"]
    expected = json.loads(
        (
            PIN / "results/quick-checks/composition-pilot-7/composition-control.json"
        ).read_text()
    )
    hashes = {(x["episode_id"], x["turn"]): x["new_sha256"] for x in expected["rows"]}
    receipts = []
    for row in historical:
        j = row["saved"]
        reg = Register.replay(
            tuple(entry(x) for x in j["register_events"]),
            defaults=tuple(entry(x) for x in j["defaults"]),
            task_handles={"A", "B"},
            event_generations=j["event_generations"],
            generation=row["turn"],
        )
        assert (
            json.loads(json.dumps([asdict(v) for v in reg.versions]))
            == j["after_versions"]
        )
        text = render(reg, Request("", **j["request_bindings"])).text.split(
            "\nCurrent user request:\n"
        )[0]
        assert "trailer delivery=" not in text
        assert all(x["key"] != "delivery" for x in json.loads(text.splitlines()[1]))
        assert (
            hashlib.sha256(text.encode()).hexdigest()
            == hashes[row["episode_id"], row["turn"]]
        )
    for e in episodes:
        reg = Register(defaults=e.defaults, task_handles={"A", "B"})
        for t in e.turns:
            reg = replace(reg, generation=t.index).apply(t.events)
            if dict(t.live)["format"] != "compact":
                continue
            request = Request("", "tool_call", t.task)
            text = render(reg, request).text
            replay = Register.replay(
                reg.events,
                defaults=e.defaults,
                task_handles={"A", "B"},
                event_generations=reg.event_generations,
                generation=t.index,
            )
            assert render(replay, request).text == text
            assert "trailer delivery=" not in text
            assert all(x["key"] != "delivery" for x in json.loads(text.splitlines()[1]))
            receipts.append(
                dict(
                    episode_id=e.episode_id,
                    turn=t.index,
                    sha256=hashlib.sha256(text.encode()).hexdigest(),
                )
            )
    assert len(historical) == 35 and receipts
    return dict(
        passed=True,
        historical_hashes_exact=35,
        scheduled_compact=len(receipts),
        episode_count=len({x["episode_id"] for x in receipts}),
        rows=receipts,
    )


def replay_control(registration):
    """Fixed pilot-7 requests, new container, C4 midpoint; never generate a DEV lane."""
    results = []

    def one(item):
        source = ROOT / item["path"]
        assert digest_file(source) == item["file_sha256"]
        old = json.loads(source.read_text())
        payload = old["request"]
        assert hashobj(payload) == item["request_sha256"]
        begin = time.time()
        receipt = dict(request=payload, source=item, started=begin)
        path = p.LOCAL / "reproducibility" / (item["id"].replace("/", "_") + ".json")
        dump(path, receipt)
        if time.time() >= p.END - 1500:
            raise TimeoutError("reproducibility deadline reserve")
        req = HTTPRequest(
            "http://127.0.0.1:18088/v1/completions",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urlopen(req, timeout=min(1200, p.END - time.time() - 180)) as response:
            receipt["response"] = json.load(response)
        receipt["ended"] = time.time()
        dump(path, receipt)

        def signature(response):
            c = response["choices"][0]
            return {k: c[k] for k in ("text", "token_ids", "finish_reason")}

        old_sig, new_sig = signature(old["response"]), signature(receipt["response"])
        return dict(
            id=item["id"],
            episode_id=item["id"].split("/")[0],
            identical=old_sig == new_sig,
            old_sha256=hashobj(old_sig),
            new_sha256=hashobj(new_sig),
            request_sha256=hashobj(payload),
            seconds=receipt["ended"] - begin,
        )

    fixed = registration["reproducibility"]
    for offset in range(0, len(fixed), 4):
        with cf.ThreadPoolExecutor(4) as pool:
            results.extend(pool.map(one, fixed[offset : offset + 4]))
        dump(OUT / "reproducibility.json", dict(complete=False, rows=results))
    divergent = sum(not x["identical"] for x in results)
    episode_ids = sorted({x["episode_id"] for x in results})
    byepisode = {
        e: sum(not x["identical"] for x in results if x["episode_id"] == e) / 5
        for e in episode_ids
    }
    report = dict(
        complete=len(results) == 40,
        payloads=len(results),
        divergent=divergent,
        divergence_rate=divergent / len(results),
        episode_divergence_rates=byepisode,
        episode_mean_divergence=sum(byepisode.values()) / len(byepisode),
        any_divergence_episodes=sum(v > 0 for v in byepisode.values()),
        rows=results,
        interpretation=(
            "cross-container pilot7-to-larger; descriptive, not a gate; "
            "no independent-cell inference"
        ),
    )
    dump(OUT / "reproducibility.json", report)
    return report


def collect(episodes, registration, control):
    rows = []
    for file in sorted((p.LOCAL / "main").glob("slab2-eval-*/*/raw.jsonl")):
        for line in file.read_text().splitlines():
            r = json.loads(line)
            r["output_sha256"] = hashobj([r["output_ids"], r["eos"]])
            r["text_sha256"] = hashlib.sha256(r["output"].encode()).hexdigest()
            r["file_written"] = s.file_written(r)
            key = f"main/{r['episode_id']}/{r['arm']}/{r['turn']}"
            r["timing"] = p.TIMINGS.get(key)
            rows.append(r)
    # Separate arm files; records precede all aggregate computation.
    for arm in "RNTQ":
        body = "".join(
            json.dumps(r, separators=(",", ":")) + "\n" for r in rows if r["arm"] == arm
        )
        assert len(body.encode()) <= 10_000_000
        (OUT / f"records-{arm}.jsonl").write_text(body)
    result = ep.larger_reading(
        rows, episodes, registration["q_ids"], cpu_control=control
    )
    dump(OUT / "summary.json", result)
    return result


def run_bank(episodes, registration):
    groups = []
    indexed = {e.episode_id: e for e in episodes}
    for group in registration["schedule"]:
        if time.time() >= p.END - 1500:
            break
        arm = group["arm"]
        start = time.time()
        errors = []
        with cf.ThreadPoolExecutor(4) as pool:
            futures = [
                pool.submit(
                    d.run_q if arm == "Q" else d.run_lane,
                    p.LOCAL / "main" / eid / arm,
                    indexed[eid],
                    arm,
                    p.factory,
                    freeze_receipt=registration["episode_hashes"][eid],
                )
                for eid in group["ids"]
            ]
            for future in futures:
                try:
                    future.result()
                except Exception as exc:
                    errors.append(repr(exc))
        groups.append(
            dict(
                **group,
                started=start,
                ended=time.time(),
                seconds=time.time() - start,
                errors=errors,
            )
        )
        dump(OUT / "groups.json", groups)
        print(json.dumps(groups[-1]), flush=True)
        if errors:
            break
        if group["id"] == registration["replay_after_group"]:
            replay_control(registration)
    return groups


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pinned-sha", required=True)
    parser.add_argument("--cpu-smoke", action="store_true")
    args = parser.parse_args()
    sha = cmd(["git", "-C", str(PIN), "rev-parse", "HEAD"])
    assert sha == args.pinned_sha
    cmd(["git", "-C", str(PIN), "diff", "HEAD", "--exit-code"])
    assert PIN != ROOT and all(
        Path(m.__file__).resolve().is_relative_to(PIN) for m in (s, d, ep, p)
    )
    p.OUT, p.LOCAL, p.PIN, p.SHA = OUT, OUT / "local", PIN, sha
    registration = json.loads((PIN / "results/larger-test/freeze.json").read_text())
    for name, value in registration["source_hashes"].items():
        assert digest_file(PIN / name) == value
    if args.cpu_smoke:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            result = d.run_lane(
                Path(tmp) / "lane", s.generate_episode(), "R", d.stub_factory
            )
            assert len(result["records"]) == 16
        print("Pinned DEV CPU consumer smoke PASS", flush=True)
        return
    assert not (OUT / "evaluation-opened.json").exists(), "one-shot bank already opened"
    dump(
        OUT / "evaluation-opened.json",
        dict(
            pinned_sha=sha,
            time=time.time(),
            registration_sha256=digest_file(PIN / "results/larger-test/freeze.json"),
        ),
    )
    episodes = s.bank(family="eval")
    assert {
        e.episode_id: e.manifest()["episode_sha256"] for e in episodes
    } == registration["episode_hashes"]
    control = composition_control(episodes)
    dump(OUT / "composition-control.json", control)
    for item in registration["reproducibility"]:
        assert digest_file(ROOT / item["path"]) == item["file_sha256"]
    dump(
        OUT / "pin-verification.json",
        dict(
            sha=sha,
            pin=str(PIN),
            clean=True,
            source_hashes=registration["source_hashes"],
            bank_hash=hashobj(registration["episode_hashes"]),
        ),
    )
    with (ROOT / ".stencil-owned-pids").open("a") as f:
        f.write(str(os.getpid()) + "\n")
    queued = time.time()
    FLAG.parent.mkdir(parents=True, exist_ok=True)
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
                p.END = p.START + 41400
                with FLAG.open("x") as f:
                    json.dump(
                        dict(pid=os.getpid(), start=p.START, deadline=p.END, sha=sha), f
                    )
                break
        print("Waiting for Stencil flag/compute clearance", flush=True)
        time.sleep(15)
    name = f"stencil-larger5-{int(p.START)}"
    command = list(registration["container_command"])
    command[command.index("--name") + 1] = name
    dump(
        OUT / "launch.json",
        dict(
            command=command,
            pinned_sha=sha,
            start=p.START,
            deadline=p.END,
            queue_seconds=p.START - queued,
        ),
    )
    launched = False
    try:
        container = cmd(command)
        launched = True
        dump(OUT / "container.json", dict(name=name, id=container))
        while time.time() < p.END - 1500:
            if (
                cmd(["docker", "inspect", "--format", "{{.State.Status}}", name])
                != "running"
            ):
                raise RuntimeError("server exited at startup")
            try:
                with urlopen("http://127.0.0.1:18088/health", timeout=2) as response:
                    if response.status == 200:
                        break
            except Exception:
                pass
            time.sleep(3)
        else:
            raise TimeoutError("startup deadline")
        dump(OUT / "ready.json", dict(load_seconds=time.time() - p.START))
        print("Server ready; pre-run C4 forward/reverse determinism", flush=True)
        p.gate()
        run_bank(episodes, registration)
    except Exception:
        (OUT / "error.txt").write_text(traceback.format_exc())
        print(traceback.format_exc(), flush=True)
    finally:
        try:
            if launched:
                stopped = cmd(["docker", "stop", "-t", "20", name])
                (OUT / "server.log").write_text(
                    cmd(["docker", "logs", "--timestamps", name]) + "\n"
                )
                removed = cmd(["docker", "rm", name])
                dump(
                    OUT / "cleanup.json", dict(name=name, stop=stopped, remove=removed)
                )
        finally:
            ended = time.time()
            dump(
                OUT / "lifecycle.json",
                dict(
                    start=p.START,
                    end=ended,
                    gpu_held_seconds=ended - p.START,
                    budget_seconds=41400,
                    hard_limit_seconds=43200,
                ),
            )
            FLAG.unlink(missing_ok=True)
        result = collect(episodes, registration, control["passed"])
        dump(
            OUT / "local-hashes.json",
            {
                str(x.relative_to(OUT)): dict(
                    bytes=x.stat().st_size, sha256=digest_file(x)
                )
                for x in p.LOCAL.rglob("*")
                if x.is_file()
            },
        )
        print(
            json.dumps(
                dict(reading=result["reading"], records=result["actual_records"])
            ),
            flush=True,
        )


if __name__ == "__main__":
    main()
