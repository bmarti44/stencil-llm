"""CPU-only raw-record audit; run from the repository root after check36."""

# ruff: noqa: E402
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from focus_check34 import score
from focus_check36 import aggregate, ids_sha
from tokenizers import Tokenizer

from stencil.function_vectors import repeated_4gram_fraction


def read_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def main():
    out = ROOT / "results/quick-checks/check36/4b"
    summary = json.loads((out / "summary.json").read_text())
    rows = read_rows(out / "records.jsonl")
    histories = read_rows(out / "histories.jsonl")
    ops = read_rows(out / "operations.jsonl")
    eq = read_rows(out / "equivalence.jsonl")
    donors = {d["id"]: d for d in read_rows(out / "donors.jsonl")}
    source = {
        (r["episode"], r["arm"], r["step"]): r
        for r in read_rows(ROOT / "results/quick-checks/check35/4b/records.jsonl")
        if r["arm"] in ("S1", "S2") and r["step"] in ("SET", "HOLD", "SWITCH", "BACK")
    }
    layout = json.loads(
        (ROOT / "results/quick-checks/check35/4b/layout.json").read_text()
    )
    tok = Tokenizer.from_file(str(ROOT / "models/qwen3-4b-hf/tokenizer.json"))

    def enc(text):
        return tok.encode(text, add_special_tokens=False).ids

    assert summary["status"] == "complete" and summary["complete"]
    assert len(rows) == 320 and len(histories) == len(eq) == 32
    assert len({(r["episode"], r["arm"], r["step"]) for r in rows}) == 320
    for name, digest in summary["source_hashes"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
    frozen = (out / "prewritten-reading.md").read_bytes()
    assert hashlib.sha256(frozen).hexdigest() == summary["reading_sha256"]
    assert (out.parent / "README.md").read_bytes().startswith(frozen)
    for key, value in aggregate(rows).items():
        assert summary[key] == value
    for r in rows:
        assert r["score"] == score(
            r["text"],
            r["values"],
            truncated=r["eos_token_id"] is None,
            rep4=repeated_4gram_fraction(r["generated_token_ids"]),
        )
        assert r["text"] == tok.decode(
            r["generated_token_ids"], skip_special_tokens=False
        )
        assert r["values"] == source[r["episode"], "S1", r["step"]]["values"]
    by_row = {(r["episode"], r["arm"], r["step"]): r for r in rows}
    by_op = {o["id"]: o for o in ops}
    assert len(by_op) == len(ops)
    for original in histories:
        ep = original["episode"]
        rebuilt = (
            layout["contexts"][ep]
            + enc(layout["cues"]["OFF"])
            + layout["suffix_token_ids"]
            + enc("<|im_end|>\n")
        )
        for prior_step in ("SET", "HOLD"):
            if prior_step == "HOLD":
                rebuilt += (
                    enc("<|im_start|>user\n")
                    + layout["filler_token_ids"]
                    + enc("<|im_end|>\n")
                )
            prior = source[ep, "S1", prior_step]
            rebuilt += prior["prompt_token_ids"] + prior["generated_token_ids"]
            if prior["eos_token_id"] is not None:
                rebuilt.append(prior["eos_token_id"])
            rebuilt += prior["trailing_token_ids"]
            assert ids_sha(rebuilt) == prior["history_sha256"]
        assert rebuilt == original["token_ids"]
        assert (
            ids_sha(original["token_ids"]) == source[ep, "S1", "HOLD"]["history_sha256"]
        )
        assert original["positions"] == source[ep, "S1", "HOLD"]["positions_after"]
        assert (
            original["answer_positions"]
            == source[ep, "S1", "HOLD"]["answer_positions_retained"]
        )
        for arm in ("R1", "R2", "R3", "R4", "R5"):
            history = original["token_ids"][:]
            positions = original["positions"][:]
            answers = original["answer_positions"][:]
            for step, task in (("SWITCH", "B"), ("BACK", "A")):
                r = by_row[ep, arm, step]
                if arm == "R3":
                    history[64:76] = (
                        enc(layout["cues"][task]) + layout["suffix_token_ids"]
                    )
                if arm == "R5":
                    positions += list(range(len(history), len(history) + 12))
                    history += enc(layout["cues"]["OFF"]) + layout["suffix_token_ids"]
                if arm == "R4":
                    positions = [p for p in positions if p not in answers]
                    answers = []
                for oid in r["operation_ids"]:
                    op = by_op[oid]
                    assert (op["episode"], op["arm"], op["step"]) == (ep, arm, step)
                    if op["action"] == "recompute_downstream":
                        expected = [p for p in positions if p >= 76]
                        assert op["positions"] == expected
                        assert op["replay_token_ids"] == [history[p] for p in expected]
                        assert op["history_sha256"] == ids_sha(history)
                        assert (
                            op["prefix_bitwise_unchanged"]
                            and op["absolute_position_unchanged"]
                        )
                    elif op["action"] == "text_rebuild":
                        assert op["replay_token_ids"] == history
                    elif op["action"] in ("write", "append"):
                        donor = donors[op["source"]]
                        assert op["after_sha256"] == donor["packet_sha256"]
                        assert op["positions"] == donor["positions"]
                        assert op["copied_bitwise"] and op["untouched_bitwise"]
                        assert (
                            donor["prefix_token_ids"][64:76]
                            == enc(layout["cues"][task]) + layout["suffix_token_ids"]
                        )
                    elif op["action"] == "evict_answers":
                        assert op["survivor_positions"] == positions
                        assert (
                            op["survivors_bitwise"]
                            and op["absolute_position_unchanged"]
                        )
                    else:
                        raise AssertionError(op["action"])
                assert r["positions_before_request"] == positions
                positions += list(
                    range(len(history), len(history) + len(r["prompt_token_ids"]))
                )
                history += r["prompt_token_ids"]
                generated = r["generated_token_ids"] + (
                    [r["eos_token_id"]] if r["eos_token_id"] is not None else []
                )
                answer_pos = list(range(len(history), len(history) + len(generated)))
                positions += answer_pos
                answers += answer_pos
                history += generated
                if r["eos_token_id"] is None:
                    answers.append(len(history))
                positions += list(
                    range(len(history), len(history) + len(r["trailing_token_ids"]))
                )
                history += r["trailing_token_ids"]
                assert positions == r["positions_after"]
                assert answers == r["answer_positions_retained"]
                assert len(history) == r["cache_length_after"]
                assert ids_sha(history) == r["history_sha256"]
    replication = {}
    for arm, ref in (("R1", "S1"), ("R5", "S2")):
        replication[arm] = {
            step: sum(
                by_row[ep, arm, step]["generated_token_ids"]
                == source[ep, ref, step]["generated_token_ids"]
                for ep in range(32)
            )
            for step in ("SWITCH", "BACK")
        }
    identity = {
        step: sum(
            by_row[ep, "R2", step]["generated_token_ids"]
            == by_row[ep, "R3", step]["generated_token_ids"]
            for ep in range(32)
        )
        for step in ("SWITCH", "BACK")
    }
    assert all(len(e["kv"][k]) == 36 for e in eq for k in ("k", "v"))
    result = dict(
        status="passed",
        records_rescored=len(rows),
        histories_verified=320,
        source_history_hashes_verified=64,
        operations=len(ops),
        donors=len(donors),
        replication_token_identity=replication,
        r2_r3_output_token_identity=identity,
        r2_r3_cache_max_abs={
            k: max(v["max_abs"] for e in eq for v in e["kv"][k]) for k in ("k", "v")
        },
        all_source_and_script_hashes_verified=True,
        prewritten_reading_preserved=True,
        elapsed_gpu_minutes=summary["elapsed_seconds"] / 60,
    )
    assert result["elapsed_gpu_minutes"] < 15
    (out / "validation.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
