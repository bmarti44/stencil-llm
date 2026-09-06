"""CPU-only consumer and saved-record audit; no generations or fitting."""

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path("/home/bmarti44/stencil-llm")
sys.path.insert(0, str(ROOT / "scripts"))
import focus_check40e as check
import torch
from transformers import AutoTokenizer


def main():
    check.verify()
    out = check.OUT
    rows = [json.loads(s) for s in (out / "records.jsonl").read_text().splitlines()]
    summary = json.loads((out / "summary.json").read_text())
    banks = json.loads((out / "banks.json").read_text())
    tasks = {
        t["id"]: t for splits in banks.values() for ts in splits.values() for t in ts
    }
    tok = AutoTokenizer.from_pretrained(check.base.MODEL, local_files_only=True)
    assert summary["reading"] == "COMPLETE"
    assert summary["records"] == len(rows)
    assert summary["generated_tokens"] == sum(
        len(r["generated_token_ids"]) for r in rows
    )
    assert summary["gpu_seconds"] <= check.LIMIT
    assert not (out / "RUNNING.flag").exists()
    for i, r in enumerate(rows):
        assert r["id"] == i
        task = tasks[r["task_id"]]
        assert r["score"] == check.score(r["text"], task, r["truncated"]), i
        assert (
            tok.decode(r["generated_token_ids"], skip_special_tokens=True) == r["text"]
        )
        assert r["history"] == check.messages(task, r["cue"])
        ids = tok.apply_chat_template(
            r["history"],
            tokenize=True,
            return_dict=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        assert ids == r["input_token_ids"] == r["rendered_input_token_ids"]
        assert not r["retained_kv"] and not r["cache_prefix_token_ids"]
        assert r["token_cap"] == 64 and len(r["generated_token_ids"]) <= 64
        assert r["alpha"] == (3 if r["bias_sha256"] else None)
    pairs = {}
    for pair, sides in check.PAIRS.items():
        result = summary["pairs"][pair]
        comp = [r for r in rows if r["pair"] == pair and r["phase"] == "competence"]
        counts = {
            s: sum(r["arm"] == s and r["score"]["valid_skill"] == s for r in comp)
            for s in sides
        }
        assert len(comp) == 32 and counts == result["competence"]
        for side in sides:
            assert {r["task_id"] for r in comp if r["arm"] == side} == {
                t["id"] for t in banks[pair]["competence"]
            }
        n = result.get("screen_n", 32)
        arms = {
            a: check.aggregate(
                [
                    r
                    for r in rows
                    if r["pair"] == pair and r["phase"] == "screen" and r["arm"] == a
                ],
                sides[1],
            )
            for a in check.ARMS
        }
        if result["reading"] == "INELIGIBLE":
            pairs[pair] = dict(reading="INELIGIBLE", competence=counts, arms=arms)
            continue
        assert result["arms"] == arms
        assert result["reading"] == check.verdict(arms, n)
        tensor = torch.load(
            out / f"{pair}-profiles.pt", map_location="cpu", weights_only=True
        )
        means = []
        assert len(tensor["per_task"]) == 32
        for side in sides:
            items = [p for p in tensor["per_task"] if p["skill"] == side]
            assert len(items) == 16
            total = None
            for p in items:
                r = rows[p["record_id"]]
                assert (
                    r["phase"] == "competence"
                    and r["arm"] == side
                    and r["pair"] == pair
                )
                # EOS list comes from saved generated text tokenization boundary;
                # every complete greedy reply ends in tokenizer EOS for this model.
                assert p["count"] == len(r["generated_token_ids"]) - int(r["eos"])
                saved = torch.load(
                    out / "profiles" / f"{pair}-{side}-{p['task_id']}.pt",
                    map_location="cpu",
                    weights_only=True,
                )
                assert torch.equal(saved["logit_sums"], p["logit_sums"])
                total = p["logit_sums"] if total is None else total + p["logit_sums"]
            means.append(total / sum(p["count"] for p in items))
        means = torch.stack(means).float()
        assert torch.equal(means, tensor["means"])
        normal, shuffle = check.base.make_biases(means, seed=40052)
        assert torch.equal(normal, tensor["normal"]) and torch.equal(
            shuffle, tensor["shuffled"]
        )
        assert torch.allclose(normal.norm(dim=-1), shuffle.norm(dim=-1))
        expected = {
            "correct": normal[1] * 3,
            "swapped": normal[0] * 3,
            "shuffled": shuffle[1] * 3,
        }
        for a, bias in expected.items():
            assert torch.equal(bias, tensor["biases"][a])
        stats = json.loads((out / f"{pair}-profile-statistics.json").read_text())
        for layer in stats["layers"]:
            k = layer["layer"]
            top = [torch.topk(p[k], 8).indices.tolist() for p in means]
            assert layer["top_experts"] == dict(zip(sides, top, strict=True))
            assert layer["overlap"] == len(set(top[0]) & set(top[1])) / 8
        receipt = json.loads((out / f"{pair}-profile-freeze.json").read_text())
        assert receipt["profile_sha256"] == check.base.sha(out / f"{pair}-profiles.pt")
        screen = [r for r in rows if r["pair"] == pair and r["phase"] == "screen"]
        by = {(r["task_id"], r["arm"]): r for r in screen}
        assert len(by) == 5 * n
        assert max(r["id"] for r in screen if r["arm"] == "OFF") < min(
            r["id"] for r in screen if r["arm"] != "OFF"
        )
        for r in screen:
            bias = expected.get(r["arm"])
            digest = (
                None
                if bias is None
                else hashlib.sha256(bias.numpy().tobytes()).hexdigest()
            )
            assert r["bias_sha256"] == digest
            assert r["cue"] == (sides[1] if r["arm"] == "text-cue" else None)
        flips = sum(
            by[t["id"], "OFF"]["score"]["valid_skill"] == sides[0]
            and by[t["id"], "correct"]["score"]["valid_skill"] == sides[1]
            for t in banks[pair]["screen"][:n]
        )
        pairs[pair] = dict(
            reading=result["reading"],
            competence=counts,
            arms=arms,
            paired_default_to_target_flips=flips,
            clear_default=arms["OFF"]["valid"].get(sides[0], 0) >= n * 20 / 32,
        )
    audit = dict(
        status="PASS",
        records=len(rows),
        pairs=pairs,
        source_freeze=True,
        profile_reconstruction=True,
        consumer_scores=True,
        token_and_prompt_provenance=True,
        cuda_initialized=torch.cuda.is_initialized(),
    )
    assert not audit["cuda_initialized"]
    check.write("audit.json", audit)
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
