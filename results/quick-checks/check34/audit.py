#!/usr/bin/env python3
"""CPU-only verification of check-34 records, lineage and fixed readings."""


def main():
    import hashlib
    import json
    import sys
    from collections import defaultdict
    from pathlib import Path

    ROOT = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(ROOT / "scripts"))
    import focus_check34 as c

    from stencil.function_vectors import repeated_4gram_fraction

    out = c.OUT / "4b"
    s = json.loads((out / "summary.json").read_text())
    rows = [
        json.loads(line) for line in (out / "records.jsonl").read_text().splitlines()
    ]
    bank = json.loads((out / "episodes.json").read_text())
    assert s["status"] == "complete"
    assert c.sha(ROOT / "scripts/focus_check34.py") == s["script_sha256"]
    # Verify the prewritten bytes, excluding the appended Results section.
    reading = (c.OUT / "README.md").read_text().split("## Results\n")[0]
    assert hashlib.sha256(reading.encode()).hexdigest() == s["reading_sha256"]
    assert c.banks() == bank
    assert len(rows) == s["records_count"]
    assert len({(r["part"], r["arm"], r["episode"], r["step"]) for r in rows}) == len(
        rows
    )
    for k, v in c.aggregate(rows).items():
        assert v == s[k], k
    hist = defaultdict(list)
    from tokenizers import Tokenizer

    tok = Tokenizer.from_file(str(ROOT / "models/qwen3-4b-hf/tokenizer.json"))
    for r in rows:
        key = (r["part"], r["arm"], r["episode"])
        ids = hist[key]
        if r.get("prefix_token_ids"):
            assert not ids
            ids.extend(r["prefix_token_ids"])
        ids.extend(r.get("filler_token_ids", []))
        ids.extend(r["prompt_token_ids"])
        ids.extend(r["generated_token_ids"])
        if r["eos_token_id"] is not None:
            ids.append(r["eos_token_id"])
        ids.extend(r["trailing_token_ids"])
        assert len(ids) == r["cache_length_after"], key
        assert (
            hashlib.sha256(json.dumps(ids).encode()).hexdigest() == r["history_sha256"]
        ), key
        assert (
            tok.decode(r["generated_token_ids"], skip_special_tokens=False) == r["text"]
        )
        resc = c.score(
            r["text"],
            r["values"],
            truncated=r["eos_token_id"] is None,
            rep4=repeated_4gram_fraction(r["generated_token_ids"]),
        )
        assert resc == r["score"], key
        if r["part"] == "single":
            assert r["target"] == ("OFF" if r["arm"] == "off" else r["arm"][-1])
            assert r["donor_episode"] == (
                (r["episode"] + 1) % 64
                if r["arm"].startswith("shuffled")
                else r["episode"]
            )
        elif r["part"] == "retained":
            initial = r["arm"][-1]
            targets = [initial, initial, "B" if initial == "A" else "A", initial, "OFF"]
            assert r["target"] == targets[c.STEPS.index(r["step"])]
        else:
            final = "A" if r["arm"] == "A_after_B" else "B"
            target = final if r["step"] == "final" else "B" if final == "A" else "A"
            assert r["target"] == r["user_cue"] == target
        ep = r["episode"]
        expected = (
            bank["single"][ep]
            if r["part"] == "single"
            else bank["retained"][ep * 5 + c.STEPS.index(r["step"])]
            if r["part"] == "retained"
            else bank["stick_final"][ep]
            if r["step"] == "final"
            else bank["stick_prior"][ep * 3 + int(r["step"][-1]) - 1]
        )
        assert r["values"] == expected, key
        if r["part"] == "retained":
            if r["step"] == "HOLD":
                assert (
                    r["packet_write"] is None
                    and r["hold_columns_bitwise_retained"] is True
                )
                assert len(r["filler_token_ids"]) == 128 + len(
                    tok.encode(c.USER).ids
                ) + len(tok.encode("<|im_end|>\n").ids)
            if r["step"] == "CLEAR":
                assert r["clear_columns_bitwise_restored"] is True
        if r.get("packet_write"):
            w = r["packet_write"]
            assert w["positions"] == list(range(64, 76)) and w["copied_bitwise"]
            assert w["layers"] == list(
                range(12 if r["arm"].startswith("layers_ge12") else 0, 36)
            )
        if r["part"] == "stickiness":
            cue_ids = tok.encode(c.CUES[r["user_cue"]]).ids
            query = r["prompt_token_ids"]
            assert query[len(tok.encode(c.USER).ids) :][: len(cue_ids)] == cue_ids
            if r.get("prefix_token_ids"):
                assert r["prefix_token_ids"] == tok.encode(c.BASE + "<|im_end|>\n").ids
    assert len([r for r in rows if r["part"] == "single"]) == 832
    assert len([r for r in rows if r["part"] == "stickiness"]) == 576
    assert (
        len([r for r in rows if r["part"] == "retained"])
        == len(s["retained_eligible_directions"]) * 160
    )
    single = {(r["arm"], r["episode"]): r for r in rows if r["part"] == "single"}
    token_identity = {
        t: sum(
            single[f"all_{t}", e]["generated_token_ids"]
            == single[f"text_{t}", e]["generated_token_ids"]
            for e in range(64)
        )
        for t in ("A", "B")
    }
    retained = defaultdict(list)
    for r in rows:
        if r["part"] == "retained":
            retained[r["arm"]].append(r)
    donors = [
        json.loads(line) for line in (out / "donors.jsonl").read_text().splitlines()
    ]
    assert len(donors) == 192
    assert len({(d["episode"], d["task"]) for d in donors}) == 192
    layout = json.loads((out / "layout.json").read_text())
    for d in donors:
        assert d["prefix_token_ids"][:64] == layout["contexts"][d["episode"]]
        assert d["prefix_token_ids"][64:72] == tok.encode(c.CUES[d["task"]]).ids
        assert d["prefix_token_ids"][72:] == tok.encode(" The context is ready").ids
        assert not any(ch.isdigit() for ch in tok.decode(d["prefix_token_ids"]))
    validation = dict(
        donor_records_verified=192,
        status="passed",
        records=len(rows),
        unique_histories=len(hist),
        all_scores_recomputed=True,
        all_histories_lengths_hashes_verified=True,
        operand_lineage_verified=True,
        prewritten_reading_hash_verified=True,
        script_hash_verified=True,
        all_layer_vs_text_generated_token_identity=token_identity,
        part_counts={
            p: sum(r["part"] == p for r in rows)
            for p in ("single", "stickiness", "retained")
        },
        hold_retained=sum(r.get("hold_columns_bitwise_retained") is True for r in rows),
        clear_restored=sum(
            r.get("clear_columns_bitwise_restored") is True for r in rows
        ),
    )
    c.write_json(out / "validation.json", validation)
    print(json.dumps(validation, indent=2))


if __name__ == "__main__":
    main()
