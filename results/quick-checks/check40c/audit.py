#!/usr/bin/env python3
"""CPU reconstruction of check40c records; no model generation."""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path("/home/bmarti44/stencil-llm")
sys.path.insert(0, str(ROOT / "scripts"))


def main():
    import focus_check40c as c
    import torch
    from transformers import AutoTokenizer

    c.runtime()
    c.verify_freeze()
    old_freeze = json.loads((c.OLD / "freeze.json").read_text())
    for name in ("scripts/focus_check40.py", "scripts/focus_check40b.py"):
        assert c.base.sha(ROOT / name) == old_freeze["files"][name]
    out = c.OUT
    tokenizer = AutoTokenizer.from_pretrained(c.base.MODEL, local_files_only=True)
    tasks = {t["id"]: t for t in json.loads((out / "tasks.json").read_text())}
    rows = [
        json.loads(line) for line in (out / "records.jsonl").read_text().splitlines()
    ]
    refs = json.loads((out / "reference-records.json").read_text())
    old = {
        r["id"]: r
        for r in map(json.loads, (c.OLD / "records.jsonl").read_text().splitlines())
    }
    biases = torch.load(
        c.OLD / "frozen-biases.pt", weights_only=True, map_location="cpu"
    )
    arms = {a: (alpha, k) for a, alpha, k in c.ARMS}
    seen = set()
    reference_changes = {"arm", "source_arm", "source_record_id", "reference", "family"}
    for r in refs:
        source = old[r["source_record_id"]]
        fields = c.report_fields(r, tokenizer)
        for key, value in source.items():
            if key not in reference_changes:
                assert r[key] == value, (key, r["source_record_id"])
        assert source["phase"] == "screen" and source["arm"] in ("correct", "OFF")
        assert r["source_arm"] == source["arm"]
        assert r["arm"] == (
            "OFF_reference" if source["arm"] == "OFF" else "alpha4_sustained_reference"
        )
        assert r["reference"]
        for key, value in fields.items():
            assert r[key] == value
    for i, r in enumerate(rows):
        assert r["id"] == i and not r["reference"]
        alpha, k = arms[r["arm"]]
        assert (r["alpha"], r["first_k"]) == (alpha, k)
        pair = (r["arm"], r["task_id"])
        assert pair not in seen
        seen.add(pair)
        assert r["token_cap"] == 64 and len(r["generated_token_ids"]) <= 64
        assert not r["cost_stopped"]
        expected_bias = biases["correct"] * (alpha / 4)
        digest = hashlib.sha256(expected_bias.float().numpy().tobytes()).hexdigest()
        assert r["bias_sha256"] == digest
        trace = r["prediction_trace"]
        assert len(trace) == len(r["generated_token_ids"])
        for j, call in enumerate(trace, 1):
            assert call == dict(
                predicts_generated_token=j,
                bias_active=k is None or j <= k,
                input_tokens=len(r["input_token_ids"]) if j == 1 else 1,
            )
    for r in rows + refs:
        task = tasks[r["task_id"]]
        assert r["family"] == task["family"]
        assert r["text"] == tokenizer.decode(
            r["generated_token_ids"], skip_special_tokens=True
        )
        assert r["history"] == c.base.messages_for(task)
        ids = tokenizer.apply_chat_template(
            r["history"],
            tokenize=True,
            return_dict=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        assert r["input_token_ids"] == r["rendered_input_token_ids"] == ids
        assert r["input_sha256"] == hashlib.sha256(json.dumps(ids).encode()).hexdigest()
        assert not r["retained_kv"] and not r["cache_prefix_token_ids"]
        assert r["score"] == c.base.score(r["text"], task, r["truncated"])
        for key, value in c.report_fields(r, tokenizer).items():
            assert r[key] == value
    assert len(rows) == 128 and len(refs) == 64 and len(seen) == 128
    summary = json.loads((out / "summary.json").read_text())
    for arm, cell in summary["arms"].items():
        records = [r for r in rows + refs if r["arm"] == arm]
        assert len(records) == len({r["task_id"] for r in records}) == cell["n"] == 32
        assert cell == c.aggregate(records)
        assert cell["js"] == sum(
            r["score"]["valid_language"] == "JavaScript" for r in records
        )
        assert cell["broken"] == sum(any(r["score"]["flags"].values()) for r in records)
    qualifying = [
        a
        for a in arms
        if summary["arms"][a]["js"] >= 20 and summary["arms"][a]["broken"] <= 2
    ]
    assert summary["reading"] == ("POSSIBLE" if qualifying else "NO QUALIFYING CELL")
    assert summary["selected_cell"] == (qualifying[0] if qualifying else None)
    assert summary["records"] == 128 and summary["reference_records"] == 64
    assert summary["generated_tokens"] == sum(
        len(r["generated_token_ids"]) for r in rows
    )
    assert summary["gpu_seconds"] < 1800 and summary["cap_overrun_seconds"] == 0
    sustained = {r["task_id"]: r for r in refs if r["source_arm"] == "correct"}
    paired = {}
    for a, (_, k) in arms.items():
        if k is None:
            continue
        records = [r for r in rows if r["arm"] == a]
        paired[a] = dict(
            complete_token_sequences_identical=sum(
                r["generated_token_ids"]
                == sustained[r["task_id"]]["generated_token_ids"]
                for r in records
            ),
            broken_to_valid_python=sum(
                sustained[r["task_id"]]["score"]["broken"]
                and r["score"]["valid_language"] == "Python"
                for r in records
            ),
            first_k_identical_to_recorded_sustained=sum(
                r["generated_token_ids"][:k]
                == sustained[r["task_id"]]["generated_token_ids"][:k]
                for r in records
            ),
            broken_to_unbroken=sum(
                sustained[r["task_id"]]["score"]["broken"] and not r["score"]["broken"]
                for r in records
            ),
            unbroken_to_broken=sum(
                not sustained[r["task_id"]]["score"]["broken"] and r["score"]["broken"]
                for r in records
            ),
            js_to_python=sum(
                sustained[r["task_id"]]["score"]["valid_language"] == "JavaScript"
                and r["score"]["valid_language"] == "Python"
                for r in records
            ),
        )
    result = dict(
        passed=True,
        new_records=128,
        reference_records=64,
        reference_fields_byte_values_preserved=True,
        no_reference_regeneration=True,
        scores_reproduced=True,
        token_text_prompt_replay=True,
        bias_hashes_verified=True,
        schedule_traces_verified=True,
        summary_and_reading_recomputed=True,
        freeze_verified=True,
        inherited_sources_match_40b=True,
        paired_first_k=paired,
        cuda_initialized=torch.cuda.is_initialized(),
    )
    assert not result["cuda_initialized"]
    c.write("audit.json", result)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
