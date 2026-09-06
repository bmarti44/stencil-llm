"""CPU-only audit and diagnostic costs of the frozen-prompt Day5b parity gate."""

import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
from tokenizers import Tokenizer

from scripts.composition_pilot import sha, write

from .pilot2 import OUT, lines, token_bytes
from .pilot_recovery import FROZEN, ROOT
from .slab import TOKENIZER_PATH


def audit(out=OUT):
    rows = lines(out / "parity-records.jsonl")
    frozen = [
        r
        for r in lines(FROZEN / "records.jsonl")
        if r["oracle_checker_results"][0]["mode"] == "sequential"
    ]
    assert len(rows) == len(frozen) == 64
    recipe = json.loads((out / "recipe.json").read_text())
    for path, expected in recipe["source_hashes"].items():
        if path == "tests/fixtures/slab_manifest.json":
            original = subprocess.check_output(
                ["git", "show", f"a3fd8613:{path}"], cwd=ROOT
            )
            assert hashlib.sha256(original).hexdigest() == expected
            old = json.loads(original)
            current = json.loads((ROOT / path).read_text())
            # Only post-run prompt/generator metadata may differ; episode,
            # hidden and turn hashes must remain exactly the frozen values.
            for key in ("system_sha256", "generator_sha256"):
                current[key] = old[key]
            for family in ("dev", "eval"):
                for before, after in zip(
                    old["banks"][family], current["banks"][family], strict=True
                ):
                    for key in ("system_sha256", "public_sha256"):
                        after[key] = before[key]
            assert current == old
        else:
            assert sha(ROOT / path) == expected, path
    assert sha(FROZEN / "records.jsonl") == recipe["frozen_records_sha256"]
    assert sha(FROZEN / "renderer-golden.jsonl") == recipe["renderer_golden_sha256"]
    tokenizer = Tokenizer.from_file(str(TOKENIZER_PATH))
    prior = {}
    differences = []
    hidden_count = 0
    for index, (r, f) in enumerate(zip(rows, frozen, strict=True)):
        assert r["index"] == r["source_row"] == index
        assert r["prompt_ids"] == f["rendered_token_ids"]
        assert (r["arm"], r["round"]) == (
            f["oracle_checker_results"][0]["arm"],
            f["oracle_checker_results"][0]["round"],
        )
        assert (
            tokenizer.decode(r["output_ids"], skip_special_tokens=False) == r["output"]
        )
        assert len(r["output_ids"]) + (r["eos"] is not None) <= 512
        measure = r["measurements"]
        assert not measure["deadline_hit"]
        n = measure["generated_forward_tokens"]
        assert 0 < n <= len(r["output_ids"])
        assert measure["hidden_complete"] == (n == len(r["output_ids"]))
        consumed = prior.get(r["arm"])
        reset = consumed is None or r["prompt_ids"][: len(consumed)] != consumed
        assert r["cache_reset"] == reset
        prior[r["arm"]] = r["prompt_ids"] + r["output_ids"][:n]
        same = token_bytes(r["output_ids"], r["eos"]) == token_bytes(
            f["output_token_ids"], f["eos"]
        )
        assert same == r["identical"]
        if not same:
            expected = f["output_token_ids"] + ([] if f["eos"] is None else [f["eos"]])
            actual = r["output_ids"] + ([] if r["eos"] is None else [r["eos"]])
            first = next(
                (
                    i
                    for i, (a, b) in enumerate(zip(actual, expected, strict=False))
                    if a != b
                ),
                min(len(actual), len(expected)),
            )
            assert first == r["first_divergence"]
            differences.append(
                dict(
                    index=index,
                    arm=r["arm"],
                    round=r["round"],
                    first_token=first,
                    expected_window=tokenizer.decode(
                        expected[max(0, first - 8) : first + 16],
                        skip_special_tokens=False,
                    ),
                    actual_window=tokenizer.decode(
                        actual[max(0, first - 8) : first + 16],
                        skip_special_tokens=False,
                    ),
                )
            )
        else:
            assert r["first_divergence"] is None
        assert len(r["hidden"]) == 2
        for h in r["hidden"]:
            path = out / h["path"]
            a = np.load(path, allow_pickle=False)
            assert list(a.shape) == h["shape"] == [5, 2048]
            assert str(a.dtype) == h["dtype"] == "float16"
            assert h["layers"] == [8, 16, 24, 32, 40]
            assert np.isfinite(a).all() and np.any(a)
            assert sha(path) == h["sha256"]
            hidden_count += 1
    run = json.loads((out / "run.json").read_text())
    assert run["status"] == "parity_stop" and run["gpu_held_seconds"] <= 7200
    assert not (out / "RUNNING.flag").exists()
    gate = json.loads((out / "parity.json").read_text())
    assert gate["divergences"] == len(differences) > 1 and not gate["passed"]
    assert not lines(out / "records.jsonl")
    elapsed = sum(r["measurements"]["batch_wall_seconds"] for r in rows)
    outside = max(0, run["gpu_held_seconds"] - run["load_seconds"] - elapsed)
    arms = {}
    for arm in "RNTO":
        chosen = [r for r in rows if r["arm"] == arm]
        m = [r["measurements"] for r in chosen]
        decode = sum(x["decode_seconds"] for x in m)
        prefill = sum(x["prefill_seconds"] for x in m)
        call_seconds = sum(x["batch_wall_seconds"] for x in m)
        arms[arm] = dict(
            calls=len(chosen),
            divergences=sum(not r["identical"] for r in chosen),
            first_divergences=[
                r["first_divergence"] for r in chosen if not r["identical"]
            ],
            decode_tok_s=sum(x["generated_forward_tokens"] for x in m) / decode,
            prefill_tok_s=sum(x["prefill_tokens"] for x in m) / prefill,
            seconds_per_call=call_seconds / len(chosen),
            truncations=sum(r["truncated"] for r in chosen),
            max_context=max(len(r["prompt_ids"]) for r in chosen),
            diagnostic_episode_seconds=call_seconds + outside / 4,
        )
    old = json.loads((FROZEN / "run.json").read_text())["gpu_held_seconds"]
    c = {a: r["diagnostic_episode_seconds"] for a, r in arms.items()}
    project = (
        old
        + run["gpu_held_seconds"]
        + run["load_seconds"]
        + 1.25 * (64 * (c["R"] + c["N"]) + 16 * (c["T"] + c["O"]))
    ) / 3600
    report = dict(
        verified_rows=64,
        source_hashes_verified=len(recipe["source_hashes"]),
        hidden_files=hidden_count,
        partial_generated_means=sum(
            not r["measurements"]["hidden_complete"] for r in rows
        ),
        identical=64 - len(differences),
        divergent=len(differences),
        first_difference_analysis=differences,
        no_logit_margin_measurement=True,
        per_arm=arms,
        cache_resets=sum(r["cache_reset"] for r in rows),
        diagnostic_frozen_16_round_projection_hours=project,
        cost_limitation=(
            "Failed parity; old interface and 16 rounds only. Not amended-pilot "
            "feasibility or a long-episode certificate. No batching credit."
        ),
        postrun_metadata_refresh=["tests/fixtures/slab_manifest.json"],
        outside_decoder_seconds=outside,
        parity_records_sha256=sha(out / "parity-records.jsonl"),
    )
    write(out / "gate-analysis.json", report)
    write(
        out / "audit.json",
        dict(
            verified_rows=64,
            hidden_files=hidden_count,
            literal_ids_and_first_positions_verified=True,
            cache_prefix_resets_verified=True,
            source_hashes_verified=True,
            hidden_hashes_shapes_finite_nonzero=True,
            audit_source_sha256=sha(Path(__file__)),
            parity_records_sha256=report["parity_records_sha256"],
        ),
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    audit()
