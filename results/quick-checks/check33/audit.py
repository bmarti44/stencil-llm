# ruff: noqa: E402
"""CPU-only reconstruction of Q3 raw scores, histories, hook schedule and selection."""

import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
import focus_check33 as q


def audit(trunk, partial=False):
    import torch
    from tokenizers import Tokenizer

    from stencil.function_vectors import repeated_4gram_fraction

    out = q.OUT / trunk
    summary = json.loads((out / "summary.json").read_text())
    bank = json.loads((out / "examples.json").read_text())
    assert bank == q.banks()[trunk]
    assert summary["script_sha256"] == q.sha(ROOT / "scripts/focus_check33.py")
    assert summary["pre_reading_sha256"] == q.sha(q.OUT / "before-run.md")
    tok = Tokenizer.from_file(str(ROOT / f"models/qwen3-{trunk}-hf/tokenizer.json"))
    tensors = torch.load(out / "fit-fp32.pt", weights_only=True, map_location="cpu")
    fit = json.loads((out / "fit-stats.json").read_text())
    for layer, tensor in tensors.items():
        means = {t: h.mean(0) for t, h in tensor["states"].items()}
        assert all(torch.equal(means[t], tensor["means"][t]) for t in means)
        u = means["A"] - means["B"]
        u /= u.norm()
        assert torch.equal(u, tensor["u"])
        coords = {t: float(u @ m) for t, m in means.items()}
        assert coords == fit[str(layer)]["coordinates"]
        p = {t: (h @ u).tolist() for t, h in tensor["states"].items()}
        assert p == fit[str(layer)]["projections"]
        # Match the run's fp32 subtraction, including its rounding at L20.
        margin = float((torch.tensor(p["A"]) - torch.tensor(p["B"])).min())
        assert margin == fit[str(layer)]["min_paired_margin"]
    extraction = json.loads((out / "extraction.json").read_text())
    assert len(extraction) == 384
    for r in extraction:
        assert r["values"] == bank["fit"][r["example"]]
        assert (
            r["prompt_token_ids"]
            == tok.encode(
                q.TEMPLATE.format(prompt=q.prompt(r["values"], r["task"]))
            ).ids
        )
    rows = [
        json.loads(line) for line in (out / "records.jsonl").read_text().splitlines()
    ]
    history, setup = defaultdict(list), defaultdict(list)
    max_orth, nonzero, hooked = 0.0, 0, 0
    for r in rows:
        generated = r["generated_token_ids"]
        assert tok.decode(generated, skip_special_tokens=False) == r["text"]
        rescored = q.score(
            r["text"],
            r["values"],
            truncated=r["terminal_token_id"] is None,
            rep4=repeated_4gram_fraction(generated),
        )
        assert rescored == r["score"]
        if r["stage"] == "setup":
            key = (r["variant"], r["layer"], r["overshoot"])
            setup[key].append(r)
            assert r["values"] == bank["setup"][r["example"]]
            variant, step, arm = r["variant"], "SET", "correct"
            before_prompt = 0
            layer, over = r["layer"], r["overshoot"]
            assert (
                r["ids"]
                == tok.encode(q.TEMPLATE.format(prompt=q.prompt(r["values"]))).ids
            )
        else:
            step, arm = r["checkpoint"], r["arm"]
            index = q.STEPS.index(step)
            assert r["values"] == bank["test"][r["episode"] * 5 + index]
            target = q.TASKS[index]
            if arm.endswith("_swapped") and target != "OFF":
                target = "B" if target == "A" else "A"
            assert r["target"] == target
            cue = (
                target
                if arm == "fresh_text" or (arm == "text" and index in (0, 2, 3))
                else "OFF"
            )
            assert r["cue"] == cue
            assert (
                r["ids"]
                == tok.encode(
                    q.TEMPLATE.format(
                        prompt=q.prompt(r["values"], cue, clear=index == 4)
                    )
                ).ids
            )
            key = (r["episode"], arm)
            if arm == "fresh_text":
                history[key] = []
            h = history[key]
            assert r["cache_before"] == len(h)
            h.extend(r["context_token_ids"])
            before_prompt = len(h)
            h.extend(r["ids"])
            h.extend(generated)
            if r["terminal_token_id"] is not None:
                assert r["terminal_token_id"] in (
                    tok.token_to_id("<|im_end|>"),
                    tok.token_to_id("<|endoftext|>"),
                )
                h.append(r["terminal_token_id"])
            h.extend(r["closing_token_ids"])
            assert r["cache_after"] == len(h)
            assert (
                r["history_sha256"]
                == hashlib.sha256(json.dumps(h).encode()).hexdigest()
            )
            variant = next((v for v in q.VARIANTS if arm.startswith(v + "_")), None)
            if variant:
                cell = summary["selected"][variant]
                layer, over = cell["layer"], cell["overshoot"]
        active = (
            variant
            and step != "CLEAR"
            and not (variant == "one_shot" and step == "HOLD")
        )
        expected = []
        if active:
            if step == "HOLD":
                wrapper = len(tok.encode("<|im_start|>user\n").ids)
                expected.extend(
                    ("filler", r["cache_before"] + wrapper + p) for p in range(128)
                )
            expected.append(("prompt", before_prompt + len(r["ids"]) - 1))
            if variant == "sustained":
                expected.extend(
                    ("decode", before_prompt + len(r["ids"]) + i)
                    for i in range(
                        len(generated) + (r["terminal_token_id"] is not None)
                    )
                )
        assert [(h["phase"], h["position"]) for h in r["hook_positions"]] == expected
        for h in r["hook_positions"]:
            hooked += 1
            s = fit[str(layer)]
            c = s["coordinates"]
            target = c[r["target"]] + over * (c[r["target"]] - c["OFF"])
            assert (
                h["target"] == target and h["clip"] == s["clip"] and h["layer"] == layer
            )
            # GPU subtraction is float32; allow its rounding in CPU scalar replay.
            delta = max(-s["clip"], min(s["clip"], target - h["before"]))
            assert abs(delta - h["delta"]) < 1e-4
            assert abs(h["delta"]) <= s["clip"] + 1e-5
            nonzero += h["changed_elements"] > 0
            max_orth = max(max_orth, h["orthogonal_cast_norm"])
    cells = json.loads((out / "cells.json").read_text())
    assert len(cells) == 16
    for cell in cells:
        rs = setup[cell["variant"], cell["layer"], cell["overshoot"]]
        assert len(rs) == 64
        assert cell["exact"] == {
            t: sum(r["score"]["value_exact"][t] for r in rs if r["target"] == t)
            for t in ("A", "B")
        }
        assert cell["both"] == sum(
            all(r["score"]["value_exact"][r["target"]] for r in rs if r["example"] == i)
            for i in range(32)
        )
        assert cell["breakage"] == sum(r["score"]["breakage"] for r in rs)
    for variant in q.VARIANTS:
        best = max(
            [c for c in cells if c["variant"] == variant],
            key=lambda c: (
                c["both"],
                -c["breakage"],
                min(c["exact"].values()),
                sum(c["exact"].values()),
                -c["layer"],
                -c["overshoot"],
            ),
        )
        assert summary["selected"][variant] == best
    for arm, a in ({} if partial else summary["arms"]).items():
        assert a == q.aggregate([r for r in rows if r.get("arm") == arm])
    if not partial:
        assert summary["variants"] == {
            v: q.reading(summary["arms"], v) for v in q.VARIANTS
        }
    randoms = (
        {}
        if partial
        else torch.load(
            out / "random-directions.pt", weights_only=True, map_location="cpu"
        )
    )
    assert partial or len(randoms) == 128
    for key, u in randoms.items():
        ep, variant = key.split(":")
        gen = torch.Generator().manual_seed(q.seed(f"{trunk}:{variant}:shuffled:{ep}"))
        expected = torch.randn(len(u), generator=gen)
        expected /= expected.norm()
        assert torch.equal(u, expected)
    result = dict(
        status="partial audit passed" if partial else "passed",
        raw_records=len(rows),
        setup_records=1024,
        test_records=len(rows) - 1024,
        hook_events=hooked,
        hook_events_with_changed_elements=nonzero,
        max_orthogonal_cast_norm=max_orth,
        checks=[
            "split lineage",
            "raw scores",
            "fit means/projections",
            "all-cell selection",
            "retained histories including EOS",
            "exact hook schedules",
            "clip/targets",
            "summary aggregates/verdicts",
            "independent random RNG",
        ],
    )
    if partial:
        result["checks"] = result["checks"][:-2]
    elif "fresh_text" in summary["arms"]:
        sets = {
            (r["arm"], r["episode"]): r
            for r in rows
            if r.get("arm") in ("text", "fresh_text") and r["checkpoint"] == "SET"
        }
        pairs = [(sets["text", ep], sets["fresh_text", ep]) for ep in range(64)]
        assert all(
            a["ids"] == b["ids"] and a["cache_before"] == b["cache_before"] == 0
            for a, b in pairs
        )
        result["identical_prompt_SET_comparison"] = dict(
            n=64,
            identical_prompts_and_empty_histories=True,
            identical_outputs=sum(
                a["generated_token_ids"] == b["generated_token_ids"] for a, b in pairs
            ),
            identical_scores=sum(a["score"] == b["score"] for a, b in pairs),
            note="Batch membership can differ; differences cannot be history effects.",
        )
    q.write_json(
        out / ("validation-partial.json" if partial else "validation.json"), result
    )
    print(trunk, result)


if __name__ == "__main__":
    partial = "--partial" in sys.argv
    for trunk in [a for a in sys.argv[1:] if a != "--partial"] or ("4b", "1.7b"):
        audit(trunk, partial)
