"""CPU-only independent record and history audit for check39."""

# ruff: noqa: E501
import ast
import hashlib
import json
import math
import random
import re
import subprocess
from pathlib import Path

from tokenizers import Tokenizer

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "results/quick-checks/check39/4b"
STEPS = ("RELEASE1", "RELEASE2", "NEUTRAL1", "NEUTRAL2")
ARMS = ("intact", "placeholder")
MODES = ("surviving", "rebuilt")


def main():
    summary = json.loads((OUT / "summary.json").read_text())
    assert (
        summary["status"] == "complete"
        and summary["n"] == 64
        and summary["seed"] == 39039
    )
    rows = [
        json.loads(line) for line in (OUT / "records.jsonl").read_text().splitlines()
    ]
    ops = [
        json.loads(line) for line in (OUT / "operations.jsonl").read_text().splitlines()
    ]
    episodes = json.loads((OUT / "episodes.json").read_text())
    layout = json.loads((OUT / "layout.json").read_text())
    tok = Tokenizer.from_file(str(ROOT / "models/qwen3-4b-hf/tokenizer.json"))

    def enc(text):
        return tok.encode(text).ids

    end = tok.token_to_id("<|im_end|>")
    assert enc(".") == [13]
    assert len(rows) == 1152 and len(ops) == 384
    assert len(episodes) == 64 and all(len(ep) == 6 for ep in episodes)
    old = json.loads(
        (ROOT / "results/quick-checks/check37/4b/episodes.json").read_text()
    )
    sets = {tuple(sorted(v)) for ep in episodes for v in ep}
    assert len(sets) == 384 and not sets & {tuple(sorted(v)) for ep in old for v in ep}
    rng, drawn, seen = random.Random(39039), [], set()
    while len(drawn) < 384:
        v = rng.sample(range(-20, 21), rng.randint(5, 8))
        key = tuple(sorted(v))
        if key in seen or v in (sorted(v), sorted(v, reverse=True)):
            continue
        seen.add(key)
        drawn.append(v)
    assert drawn == [v for ep in episodes for v in ep]
    for name, digest in summary["source_hashes"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    frozen = subprocess.check_output(
        [
            "git",
            "show",
            summary["source_commit"] + ":results/quick-checks/check39/README.md",
        ],
        cwd=ROOT,
    )
    assert frozen == (OUT / "prewritten-reading.md").read_bytes()
    source = subprocess.check_output(
        ["git", "show", summary["source_commit"] + ":scripts/focus_check39.py"],
        cwd=ROOT,
    )
    assert source == (ROOT / "scripts/focus_check39.py").read_bytes()
    ix = {(r["episode"], r["arm"], r["mode"], r["step"]): r for r in rows}
    assert len(ix) == len(rows)
    for r in rows:
        text, tokens = r["text"], r["generated_token_ids"]
        assert text == tok.decode(tokens, skip_special_tokens=False)
        try:
            strict = json.loads(text)
            valid = isinstance(strict, list) and all(type(x) is int for x in strict)
        except (ValueError, TypeError):
            strict, valid = None, False
        candidate = None
        candidates = re.findall(r"\[[^\[\]]*\]", text)
        if len(candidates) == 1:
            try:
                raw = ast.literal_eval(candidates[0])
                if isinstance(raw, list) and all(
                    type(x) is int
                    or (isinstance(x, str) and re.fullmatch(r"[+-]?\d+", x.strip()))
                    for x in raw
                ):
                    candidate = [int(x) for x in raw]
            except (ValueError, SyntaxError, TypeError):
                pass
        grams = [tuple(tokens[i : i + 4]) for i in range(len(tokens) - 3)]
        repetition = (len(tokens) >= 8 and 1 - len(set(grams)) / len(grams) > 0.2) or (
            candidate is not None and len(set(candidate)) != len(candidate)
        )
        broken = (
            not valid or repetition or candidate is None or r["eos_token_id"] != end
        )
        target = r["values"] if r["step"].startswith("NEUTRAL") else sorted(r["values"])
        assert r["strict_valid"] == valid and r["broken"] == broken
        assert r["success"] == (not broken and strict == target)
        assert r["score"]["parsed"] == candidate
        for name, expected in {
            "A": sorted(r["values"]),
            "B": sorted(r["values"], reverse=True),
            "OFF": r["values"],
        }.items():
            assert r["score"]["value_exact"][name] == (candidate == expected)
            assert r["score"]["strict_exact"][name] == (valid and strict == expected)
        step_index = ("SET", "HOLD", *STEPS).index(r["step"])
        assert r["values"] == episodes[r["episode"]][step_index]
        assert len(r["history_before"]) == len(r["positions_before"])
        assert len(r["history_after"]) == len(r["positions_after"])
        assert r["positions_after"] == sorted(set(r["positions_after"]))
        tail = r["prompt_token_ids"] + tokens
        if r["eos_token_id"] is not None:
            tail += [r["eos_token_id"]]
        if r["eos_token_id"] != end:
            tail += [end]
        tail += enc("\n")
        assert r["history_after"] == r["history_before"] + tail
        assert r["positions_after"] == r["positions_before"] + list(
            range(r["start"], r["start"] + len(tail))
        )
        assert r["cache_length_after"] == r["positions_after"][-1] + 1
        assert (
            r["history_after"][r["positions_after"].index(r["turn"]["closure"])] == end
        )

    opix = {(o["episode"], o["arm"], o["step"]): o for o in ops}
    assert len(opix) == 384 and [o["id"] for o in ops] == list(range(384))
    structure_count = 0
    for ep in range(64):
        setup = [ix[ep, "shared", "shared", s] for s in ("SET", "HOLD")]
        cue_pair = (
            "<|im_start|>user\n"
            + layout["cue"]
            + "<|im_end|>\n<|im_start|>assistant\n.<|im_end|>\n"
        )
        assert setup[0]["history_before"] == enc(layout["base"] + "<|im_end|>\n") + enc(
            cue_pair
        )
        assert setup[1]["history_before"] == setup[0]["history_after"]
        for arm in ARMS:
            prev = setup[-1]
            for i, step in enumerate(STEPS):
                r = ix[ep, arm, "surviving", step]
                shadow = ix[ep, arm, "rebuilt", step]
                for field in (
                    "history_before",
                    "positions_before",
                    "prompt_token_ids",
                    "start",
                ):
                    assert r[field] == shadow[field], (ep, arm, step, field)
                if step == "NEUTRAL2":
                    assert r["history_before"] == prev["history_after"]
                    assert r["positions_before"] == prev["positions_after"]
                else:
                    op = opix[ep, arm, step]
                    prior_map = dict(
                        zip(prev["positions_after"], prev["history_after"], strict=True)
                    )
                    new_turns = [x["turn"] for x in setup] if i == 0 else [prev["turn"]]
                    drop, replacements = set(), []
                    if arm == "placeholder":
                        for t in new_turns:
                            replacements.append(t["body"][0])
                            prior_map[t["body"][0]] = 13
                            drop.update(t["body"][1:])
                        for p in drop:
                            del prior_map[p]
                    assert op["positions"] == sorted(drop)
                    assert op["replacements"] == replacements
                    assert op["retained_positions"] == list(prior_map)
                    assert op["retained_token_ids"] == list(prior_map.values())
                    assert op["absolute_next"] == prev["cache_length_after"]
                    assert (
                        op["survivors_bitwise_after_replacement"]
                        and op["absolute_position_unchanged"]
                    )
                    hist, pos = list(prior_map.values()), list(prior_map)
                    if step == "NEUTRAL1":
                        event = enc(
                            "<|im_start|>user\n"
                            + layout["cancel"]
                            + "<|im_end|>\n<|im_start|>assistant\n.<|im_end|>\n"
                        )
                        hist += event
                        pos += list(
                            range(op["absolute_next"], op["absolute_next"] + len(event))
                        )
                    assert r["history_before"] == hist and r["positions_before"] == pos
                    rendered = tok.decode(hist, skip_special_tokens=False)
                    # Every retained message is a closed user/assistant/system turn.
                    messages = re.findall(
                        r"<\|im_start\|>(system|user|assistant)\n(.*?)<\|im_end\|>\n",
                        rendered,
                        re.S,
                    )
                    assert (
                        "".join(
                            "<|im_start|>" + role + "\n" + body + "<|im_end|>\n"
                            for role, body in messages
                        )
                        == rendered
                    )
                    assert [role for role, _ in messages] == ["system"] + [
                        "user",
                        "assistant",
                    ] * ((len(messages) - 1) // 2)
                    structure_count += 1
                prev = r

    cells, comparisons = {}, {}
    for arm in ARMS:
        comparisons[arm] = {}
        for mode in MODES:
            rr = [r for r in rows if r["arm"] == arm and r["mode"] == mode]
            steps = {}
            for step in STEPS:
                rs = [r for r in rr if r["step"] == step]
                assert len(rs) == 64
                steps[step] = dict(
                    n=64,
                    valid=sum(r["strict_valid"] for r in rs),
                    success=sum(r["success"] for r in rs),
                    value_exact=sum(r["score"]["value_exact"][r["target"]] for r in rs),
                    broken=sum(r["broken"] for r in rs),
                    placeholder_imitation=sum(r["text"].strip() == "." for r in rs),
                    empty=sum(not r["text"].strip() for r in rs),
                )
            cells[arm + "/" + mode] = dict(
                steps=steps,
                broken_episodes=sorted({r["episode"] for r in rr if r["broken"]}),
            )
        for step in STEPS:
            pairs = [
                (ix[e, arm, "surviving", step], ix[e, arm, "rebuilt", step])
                for e in range(64)
            ]
            comparisons[arm][step] = dict(
                n=64,
                identical_outputs=sum(
                    (a["generated_token_ids"], a["eos_token_id"])
                    == (b["generated_token_ids"], b["eos_token_id"])
                    for a, b in pairs
                ),
                surviving_only_success=sum(
                    a["success"] and not b["success"] for a, b in pairs
                ),
                rebuilt_only_success=sum(
                    b["success"] and not a["success"] for a, b in pairs
                ),
            )
    assert cells == summary["arms"] and comparisons == summary["comparisons"]
    passes = []
    for mode in MODES:
        p, intact = [cells[a + "/" + mode] for a in ("placeholder", "intact")]
        ps, ins = set(p["broken_episodes"]), set(intact["broken_episodes"])
        b, c = len(ps - ins), len(ins - ps)
        pvalue = sum(math.comb(b + c, k) for k in range(b, b + c + 1)) / 2 ** (b + c)
        g = summary["gates"][mode]
        assert g["placeholder_only_broken"] == sorted(ps - ins)
        assert g["intact_only_broken"] == sorted(ins - ps)
        assert g["both_broken"] == sorted(ps & ins) and g["neither_broken"] == 64 - len(
            ps | ins
        )
        assert g["mcnemar_worse_one_sided_p"] == pvalue and g["discordant_net"] == b - c
        losses = {
            s: intact["steps"][s]["success"] - p["steps"][s]["success"]
            for s in STEPS[:2]
        }
        assert losses == g["active_success_losses"]
        safety = b - c <= 2 and pvalue >= 0.05
        active = mode == "rebuilt" or max(losses.values()) <= 2
        neutral = all(
            cells[a + "/" + mode]["steps"][s]["success"] >= 56
            for a in ARMS
            for s in STEPS[2:]
        )
        assert (safety, active, neutral) == (
            g["safety_pass"],
            g["active_pass"],
            g["neutral_pass"],
        )
        passes.append(safety and active and neutral)
        assert g["passes"] == passes[-1]
    assert summary["verdict"] == ("PROCEED_PLACEHOLDER" if all(passes) else "STOP")
    setup_cells = {}
    for s in ("SET", "HOLD"):
        rs = [r for r in rows if r["step"] == s]
        setup_cells[s] = dict(
            n=len(rs),
            valid=sum(r["strict_valid"] for r in rs),
            success=sum(r["success"] for r in rs),
            value_exact=sum(r["score"]["value_exact"]["A"] for r in rs),
            broken=sum(r["broken"] for r in rs),
        )
    audit = dict(
        status="passed",
        records=len(rows),
        scored_records=1024,
        shared_setup_records=128,
        edit_records=len(ops),
        paired_histories=512,
        structurally_valid_snapshots=structure_count,
        unique_sets=384,
        disjoint_from_check37=True,
        seed_stream_reproduced=True,
        independent_scores_and_gates=True,
        source_and_preregistration_hashes_verified=True,
        setup_cells=setup_cells,
        artifact_sha256={
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(OUT.iterdir())
            if p.name not in ("audit.json",) and p.is_file()
        },
    )
    (OUT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
