"""Replay saved DEV HTTP payloads and output checks without GPU or generation."""

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

PIN = Path("/tmp/stencil-pilot7-pinned")
OUT = Path(__file__).resolve().parent
SHA = "24ed80a49edcea3359d0c45d361daf7fdf761745"


def main():
    assert (
        subprocess.check_output(
            ["git", "-C", str(PIN), "rev-parse", "HEAD"], text=True
        ).strip()
        == SHA
    )
    subprocess.run(["git", "-C", str(PIN), "diff", "HEAD", "--exit-code"], check=True)
    sys.path[:0] = [str(PIN / "src"), str(PIN / "scripts")]
    import composition_pilot5 as d

    from stencil.focus import slab2_endpoint as ep

    s = d.s
    assert Path(s.__file__).resolve().is_relative_to(PIN)
    receipts = []
    reports = {}
    for phase, n in [("main", 16), ("fallback", 12)]:
        path = OUT / f"{phase}-records.jsonl"
        if not path.exists():
            continue
        saved = [json.loads(x) for x in path.read_text().splitlines()]
        indexed = {(r["episode_id"], r["arm"], r["turn"]): r for r in saved}
        assert len(indexed) == len(saved)

        class PlannedEnd(Exception):
            pass

        def factory(e, arm, turn, indexed=indexed, phase=phase):
            key = (e.episode_id, arm, turn)
            if key not in indexed:
                raise PlannedEnd()
            raw = OUT / "local/http" / phase / e.episode_id / arm / f"{turn}.json"
            receipt = json.loads(raw.read_text())

            def transport(payload):
                assert payload == receipt["request"], key
                response = receipt["response"]
                row = indexed[key]
                assert row["truncated"] == (
                    response["choices"][0]["finish_reason"] == "length"
                )
                assert row["output_tokens"] == response["usage"]["completion_tokens"]
                assert row["output_sha256"] == s.digest([row["output_ids"], row["eos"]])
                assert (
                    row["text_sha256"]
                    == hashlib.sha256(row["output"].encode()).hexdigest()
                )
                receipts.append(
                    dict(
                        phase=phase,
                        episode_id=e.episode_id,
                        arm=arm,
                        turn=turn,
                        http_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),
                        prompt_sha256=s.digest(payload["prompt"]),
                        output_sha256=row["output_sha256"],
                        http_seconds=receipt["seconds"],
                    )
                )
                return response

            return d.VLLMDecoder("http://unused/v1", "/model", transport)

        with tempfile.TemporaryDirectory(prefix="stencil-pilot7-audit-") as tmp:
            root = Path(tmp)
            for e in s.bank(n_rounds=n):
                for arm in "QRNT":
                    try:
                        (d.run_q if arm == "Q" else d.run_lane)(
                            root / e.episode_id / arm, e, arm, factory, n_rounds=n
                        )
                    except PlannedEnd:
                        pass
            replay = [
                json.loads(x)
                for p in root.glob("*/*/raw.jsonl")
                for x in p.read_text().splitlines()
            ]
            assert len(replay) == len(saved)
            for row in replay:
                original = indexed[row["episode_id"], row["arm"], row["turn"]]
                for key, value in row.items():
                    assert original[key] == value, (
                        row["episode_id"],
                        row["arm"],
                        row["turn"],
                        key,
                    )
                assert original["file_written"] == s.file_written(row)
        summary = json.loads((OUT / f"{phase}-summary.json").read_text())
        metrics = s.execution_summary(saved, arms="QRNT")
        for arm, v in metrics.items():
            assert all(summary["per_arm"][arm][k] == value for k, value in v.items())
        if summary["floor"]:
            assert ep.strict_floor(saved) == summary["floor"]
        if summary["projected_gpu_hours"]:
            assert (
                ep.projection(summary["lane_seconds"], summary["load_seconds"])
                == summary["projected_gpu_hours"]
            )
        reports[phase] = dict(
            replayed_records=len(replay),
            prompt_payload_mismatches=0,
            record_field_mismatches=0,
            records_bytes=path.stat().st_size,
        )
        assert path.stat().st_size <= 10_000_000
    gate = json.loads((OUT / "determinism.json").read_text())
    assert not gate["mismatches"] and gate["prompts"] == 8 and gate["concurrency"] == 4
    for i in range(8):
        assert gate["outputs"][f"forward-{i}"] == gate["outputs"][f"reverse-{i}"]
    hashes = json.loads((OUT / "local-hashes.json").read_text())
    for rel, v in hashes.items():
        raw = (OUT / rel).read_bytes()
        assert (
            len(raw) == v["bytes"] and hashlib.sha256(raw).hexdigest() == v["sha256"]
        ), rel
    assert not (OUT / "RUNNING.flag").exists()
    life = json.loads((OUT / "lifecycle.json").read_text())
    assert life["gpu_held_seconds"] <= 5400
    name = json.loads((OUT / "container.json").read_text())["name"]
    assert not subprocess.check_output(
        ["docker", "ps", "-a", "--filter", f"name=^{name}$", "--format", "{{.Names}}"],
        text=True,
    ).strip()
    with (OUT / "journals-index.jsonl").open("w") as f:
        for row in receipts:
            f.write(json.dumps(row, separators=(",", ":")) + "\n")
    report = dict(
        pinned_sha=SHA,
        phases=reports,
        determinism_mismatches=0,
        hashed_local_files=len(hashes),
        gpu_held_seconds=life["gpu_held_seconds"],
        own_container_absent=True,
        own_flag_absent=True,
    )
    (OUT / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
