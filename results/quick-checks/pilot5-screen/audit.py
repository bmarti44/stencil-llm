"""CPU-only replay of every saved screen call against the pinned loop/HTTP payload."""

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

PIN = Path("/tmp/stencil-pilot5-screen-pinned")
OUT = Path("/home/bmarti44/stencil-llm/results/quick-checks/pilot5-screen")
SHA = "4ab3e21884e0e5decd6d4fd78607abd6a69cf95d"


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

    s = d.s
    assert Path(s.__file__).resolve().is_relative_to(PIN)
    s.REPLY_CAP = 1024
    s.SYSTEM_PROMPT = s.SYSTEM_PROMPT.replace("2048", "1024")
    saved = [json.loads(x) for x in (OUT / "records.jsonl").read_text().splitlines()]
    indexed = {(r["episode_id"], r["arm"], r["turn"]): r for r in saved}
    assert len(indexed) == len(saved) == 72
    receipts = []

    class PlannedEnd(Exception):
        pass

    def factory(e, arm, turn):
        key = (e.episode_id, arm, turn)
        if key not in indexed:
            raise PlannedEnd()
        path = OUT / "local/http" / e.episode_id / arm / f"{turn}.json"
        receipt = json.loads(path.read_text())

        def transport(payload):
            assert payload == receipt["request"], key
            response = receipt["response"]
            row = indexed[key]
            assert row["truncated"] == (
                response["choices"][0]["finish_reason"] == "length"
            )
            assert row["output_tokens"] == response["usage"]["completion_tokens"]
            receipts.append(
                dict(
                    episode_id=e.episode_id,
                    arm=arm,
                    turn=turn,
                    http_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                    prompt_sha256=s.digest(payload["prompt"]),
                    output_sha256=s.digest([row["output_ids"], row["eos"]]),
                    http_seconds=receipt["end"] - receipt["start"],
                )
            )
            return response

        return d.VLLMDecoder("http://unused/v1", "/model", transport)

    with tempfile.TemporaryDirectory(prefix="stencil-screen-audit-") as tmp:
        root = Path(tmp)
        for e in s.bank()[:2]:
            for arm in "RNTQ":
                try:
                    (d.run_q if arm == "Q" else d.run_lane)(
                        root / e.episode_id / arm, e, arm, factory
                    )
                except PlannedEnd:
                    assert e.episode_id == "slab2-dev-01"
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
    summary = json.loads((OUT / "summary.json").read_text())
    reading = s.screen_reading(saved)
    assert reading["reading"] == summary["reading"] == "SCREEN-NOT-PASS"
    for arm, values in reading["per_arm"].items():
        assert all(summary["per_arm"][arm][k] == v for k, v in values.items())
    # Prior pilot5 reference denominator omitted EOS; retain both conventions.
    factors = {}
    episodes = {e.episode_id: e for e in s.bank()[:2]}
    for arm in "RNTQ":
        rows = [r for r in saved if r["arm"] == arm]
        reference = sum(
            len(s.qwen_encode(s.reference(episodes[r["episode_id"]], r["turn"])))
            for r in rows
        )
        output = sum(r["output_tokens"] for r in rows)
        assert summary["per_arm"][arm]["reference_tokens"] == reference + len(rows)
        assert summary["per_arm"][arm]["x_factor"] == output / (reference + len(rows))
        factors[arm] = dict(
            output_tokens=output,
            reference_tokens_without_eos=reference,
            pilot5_comparable_x=output / reference,
            eos_balanced_x=output / (reference + len(rows)),
        )
    assert not (OUT / "RUNNING.flag").exists()
    life = json.loads((OUT / "lifecycle.json").read_text())
    assert life["gpu_held_seconds"] <= 900
    name = json.loads((OUT / "container.json").read_text())["name"]
    assert not subprocess.check_output(
        ["docker", "ps", "-a", "--filter", f"name=^{name}$", "--format", "{{.Names}}"],
        text=True,
    ).strip()
    with (OUT / "journals-index.jsonl").open("w") as f:
        for row in receipts:
            f.write(json.dumps(row, separators=(",", ":")) + "\n")
    report = dict(
        x_factors=factors,
        pinned_sha=SHA,
        replayed_records=len(replay),
        prompt_payload_mismatches=0,
        record_field_mismatches=0,
        reading=reading["reading"],
        gpu_held_seconds=life["gpu_held_seconds"],
        own_container_absent=True,
        own_flag_absent=True,
        records_bytes=(OUT / "records.jsonl").stat().st_size,
    )
    (OUT / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
