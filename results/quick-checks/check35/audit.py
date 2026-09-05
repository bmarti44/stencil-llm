"""CPU-only independent record replay; never loads weights or benchmark files."""

# ruff: noqa: E402, E501, I001
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from focus_check35 import ARMS, VARIANTS, STEPS, OUT, aggregate, bank, sha
from focus_check34 import CUES, USER, ASSISTANT, score
from tokenizers import Tokenizer
from stencil.function_vectors import repeated_4gram_fraction


def main():
    out = OUT / "4b"

    def read(name):
        return json.loads((out / name).read_text())

    rows = [
        json.loads(line) for line in (out / "records.jsonl").read_text().splitlines()
    ]
    ops = [
        json.loads(line) for line in (out / "operations.jsonl").read_text().splitlines()
    ]
    donors = [
        json.loads(line) for line in (out / "donors.jsonl").read_text().splitlines()
    ]
    summary, layout = read("summary.json"), read("layout.json")
    assert summary["status"] == "complete"
    assert summary["script_sha256"] == sha(ROOT / "scripts/focus_check35.py")
    assert summary["reused_script_sha256"] == sha(ROOT / "scripts/focus_check34.py")
    reading = (OUT / "README.md").read_text().split("\n## Results\n")[0]
    assert hashlib.sha256(reading.encode()).hexdigest() == summary["reading_sha256"]
    assert len(rows) == 1536 and read("episodes.json") == bank()
    assert [o["id"] for o in ops] == list(range(len(ops)))
    byid = {o["id"]: o for o in ops}
    assert set(byid) == {oid for r in rows for oid in r["operation_ids"]}
    donor_map = {d["id"]: d for d in donors}
    assert len(donor_map) == len(donors)
    tok = Tokenizer.from_file(str(ROOT / "models/qwen3-4b-hf/tokenizer.json"))

    def enc(x):
        return tok.encode(x).ids

    for d in donors:
        ep, task, start = d["episode"], d["task"], d["positions"][0]
        assert (
            d["prefix_token_ids"]
            == layout["contexts"][ep] + enc(CUES[task]) + layout["suffix_token_ids"]
        )
        assert d["prefix_rope_offset"] == start - 64
        assert d["positions"] == list(range(start, start + 12))
    for r in rows:
        assert r["values"] == bank()[r["episode"]][STEPS.index(r["step"])]
        assert r["text"] == tok.decode(
            r["generated_token_ids"], skip_special_tokens=False
        )
        assert r["score"] == score(
            r["text"],
            r["values"],
            truncated=r["eos_token_id"] is None,
            rep4=repeated_4gram_fraction(r["generated_token_ids"]),
        )
    for op in ops:
        assert op["layers"] == layout["layers"] and op["kinds"] == ["k", "v"]
        if op["action"] in ("write", "append"):
            assert (
                op["copied_bitwise"]
                and op["untouched_bitwise"]
                and len(op["positions"]) == 12
            )
            if op["source"] != "stored_original_OFF_filler":
                assert op["after_sha256"] == donor_map[op["source"]]["packet_sha256"]
        elif op["action"] == "evict_answers":
            assert (
                op["positions"]
                and op["survivors_bitwise"]
                and op["absolute_position_unchanged"]
            )
        else:
            assert (
                op["action"] == "hold_check"
                and op["writes"] == 0
                and op["retained_bitwise"]
            )
    replayed = 0
    for ep in range(32):
        for arm in ARMS:
            for variant in VARIANTS[arm]:
                hist = (
                    layout["contexts"][ep]
                    + enc(CUES["OFF"])
                    + layout["suffix_token_ids"]
                )
                positions, answers = list(range(len(hist))), []
                slots = [list(range(64, 76))]
                filler_hashes = {}
                chosen = {
                    r["step"]: r
                    for r in rows
                    if r["episode"] == ep
                    and r["arm"] == arm
                    and r["variant"] in ("shared", variant)
                }
                assert len(chosen) == 6
                for step in STEPS:
                    r = chosen[step]
                    actions = [byid[i]["action"] for i in r["operation_ids"]]
                    if step == "SET":
                        expected_actions = ["write"]
                    elif step == "HOLD":
                        expected_actions = ["hold_check"]
                    elif step in ("SWITCH", "BACK"):
                        expected_actions = (
                            ["evict_answers"] if arm in ("S3", "S4", "S5") else []
                        )
                        expected_actions += (
                            ["append"]
                            if arm in ("S2", "S5")
                            else ["write"]
                            if arm in ("S1", "S3")
                            else []
                        )
                    elif step == "CLEAR":
                        expected_actions = (
                            ["append"]
                            if variant == "c3"
                            else (["evict_answers"] if variant == "c2" else [])
                            + ["write"] * len(slots)
                        )
                    else:
                        expected_actions = []
                    assert actions == expected_actions
                    cue = (
                        (
                            "B"
                            if step == "SWITCH"
                            else "A"
                            if step == "BACK"
                            else "OFF"
                            if step == "CLEAR"
                            else None
                        )
                        if arm == "TEXT"
                        else None
                    )
                    query = (
                        USER
                        + (CUES[cue] + " " if cue else "")
                        + "Process these integers. Output only a JSON array. Integers: "
                        + json.dumps(r["values"])
                        + ASSISTANT
                    )
                    assert r["prompt_token_ids"] == enc(query)
                    if step == "HOLD":
                        filler = (
                            enc(USER) + layout["filler_token_ids"] + enc("<|im_end|>\n")
                        )
                        positions.extend(range(len(hist), len(hist) + len(filler)))
                        hist.extend(filler)
                    for oid in r["operation_ids"]:
                        op = byid[oid]
                        assert (
                            op["episode"],
                            op["arm"],
                            op["variant"],
                            op["step"],
                        ) == (ep, arm, r["variant"], step)
                        ps = op["positions"]
                        if step == "SET":
                            filler_hashes[64] = op["before_sha256"]
                        if op["action"] in ("write", "append") and step in (
                            "SET",
                            "SWITCH",
                            "BACK",
                        ):
                            task = "B" if step == "SWITCH" else "A"
                            assert op["source"] == f"{ep}/{task}/{ps[0]}"
                        if step == "CLEAR" and op["action"] == "write":
                            assert op["after_sha256"] == filler_hashes[ps[0]]

                        if op["action"] == "append":
                            assert ps == list(range(len(hist), len(hist) + 12))
                            assert op["physical_indices"] == list(
                                range(len(positions), len(positions) + 12)
                            )
                            positions.extend(ps)
                            hist.extend(enc(CUES["OFF"]) + layout["suffix_token_ids"])
                            slots.append(ps)
                            filler_hashes[ps[0]] = donor_map[f"{ep}/OFF/{ps[0]}"][
                                "packet_sha256"
                            ]
                            if step == "CLEAR":
                                assert op["source"] == f"{ep}/OFF/{ps[0]}"
                        elif op["action"] == "evict_answers":
                            assert ps == sorted(answers)
                            assert op["physical_indices"] == [
                                positions.index(p) for p in ps
                            ]
                            positions = [p for p in positions if p not in set(ps)]
                            answers = []
                            assert positions == op["survivor_positions"]
                        else:
                            assert op["physical_indices"] == [
                                positions.index(p) for p in ps
                            ]
                            assert ps in slots
                        assert op["absolute_next"] == len(hist)
                    if step == "SET":
                        closing = enc("<|im_end|>\n")
                        positions.extend(range(len(hist), len(hist) + len(closing)))
                        hist.extend(closing)
                    assert r["positions_before_request"] == positions
                    prompt = r["prompt_token_ids"]
                    positions.extend(range(len(hist), len(hist) + len(prompt)))
                    hist.extend(prompt)
                    generated = r["generated_token_ids"] + (
                        [] if r["eos_token_id"] is None else [r["eos_token_id"]]
                    )
                    answers.extend(range(len(hist), len(hist) + len(generated)))
                    positions.extend(range(len(hist), len(hist) + len(generated)))
                    hist.extend(generated)
                    ending = r["trailing_token_ids"]
                    if r["eos_token_id"] is None:
                        answers.append(len(hist))
                    positions.extend(range(len(hist), len(hist) + len(ending)))
                    hist.extend(ending)
                    assert positions == r["positions_after"]
                    assert answers == r["answer_positions_retained"]
                    assert len(hist) == r["cache_length_after"]
                    assert (
                        hashlib.sha256(json.dumps(hist).encode()).hexdigest()
                        == r["history_sha256"]
                    )
                    replayed += 1
    recomputed = aggregate(rows)
    assert recomputed["arms"] == summary["arms"]
    assert recomputed["release_reading_valid"] == summary["release_reading_valid"]
    text_columns = []
    for r in rows:
        if r["arm"] != "TEXT" or r["step"] not in ("SWITCH", "BACK", "CLEAR"):
            continue
        task = {"SWITCH": "B", "BACK": "A", "CLEAR": "OFF"}[r["step"]]
        lo, hi = len(enc(USER)), len(enc(USER + CUES[task]))
        assert r["prompt_token_ids"][lo:hi] == enc(CUES[task])
        physical = len(r["positions_before_request"])
        absolute = r["positions_before_request"][-1] + 1
        text_columns.append(
            dict(
                episode=r["episode"],
                step=r["step"],
                task=task,
                positions=list(range(absolute + lo, absolute + hi)),
                physical_indices=list(range(physical + lo, physical + hi)),
                layers=layout["layers"],
                kinds=["k", "v"],
                token_ids=r["prompt_token_ids"][lo:hi],
                source="natural model forward; no transplant equality claim",
            )
        )
    result = dict(
        natural_text_cue_columns=text_columns,
        status="passed",
        scored_records=len(rows),
        operations=len(ops),
        donors=len(donors),
        replayed_steps_including_shared_forks=replayed,
        all_scores_recomputed=True,
        histories_and_positions_replayed=True,
        hashes_verified=True,
        bitwise_scope="Runtime assertions on written/appended columns and all eviction/write survivors; raw tensors not persisted.",
    )
    (out / "validation.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {k: v for k, v in result.items() if k != "natural_text_cue_columns"},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
