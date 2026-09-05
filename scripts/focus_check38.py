#!/usr/bin/env python3
"""Disclosed check 38: text-only role, recency, and demonstration separator."""

# ruff: noqa: E402, E501, I001
from __future__ import annotations

import argparse
import fcntl
import json
import os
import subprocess
import time
from pathlib import Path

from focus_check36 import Engine, Budget, ids_sha
from focus_check34 import ROOT, CUES, USER, score, wilson, gpu_pids, sha, write_json, StopRun

OUT = ROOT / "results/quick-checks/check38"
SOURCE = ROOT / "results/quick-checks/check36/4b"
ARMS = ("T1", "T2", "T3", "T4", "R3")
SEED, MAX_NEW = 38038, 48


def read_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def sources():
    histories = {r["episode"]: r for r in read_rows(SOURCE / "histories.jsonl")}
    reference = {(r["episode"], r["step"]): r for r in read_rows(SOURCE / "records.jsonl") if r["arm"] == "R3"}
    prior = {(r["episode"], r["step"]): r for r in read_rows(ROOT / "results/quick-checks/check35/4b/records.jsonl") if r["arm"] == "S1"}
    assert len(histories) == 32 and len(reference) == 64 and len(prior) == 192
    for ep, h in histories.items():
        assert ids_sha(h["token_ids"]) == h["source_hold_sha256"] == prior[ep, "HOLD"]["history_sha256"]
        for step in ("SWITCH", "BACK"):
            assert reference[ep, step]["values"] == prior[ep, step]["values"]
    return histories, reference, prior


def layout(eng, h, prior, ep, arm, task, continuation=()):
    """Rebuild from recorded token spans; only explicit text edits are allowed."""
    history = h["token_ids"]
    end = eng.enc("<|im_end|>\n")
    assert history[76:76 + len(end)] == end
    body = history[76 + len(end):]
    if arm == "T2":
        # Remove complete SET/HOLD exchanges, preserving exactly the filler turn.
        set_end = len(prior[ep, "SET"]["positions_after"])
        hold_start = len(prior[ep, "HOLD"]["positions_before_request"])
        body = history[set_end:hold_start]
        assert body == eng.enc(USER) + eng.filler + end
    system_cue = arm in ("T2", "R3") or (arm == "T3" and task == "A")
    prefix = history[:64] + (eng.enc(CUES[task]) if system_cue else []) + history[72:76] + end
    event = eng.enc(USER + CUES[task] + "<|im_end|>\n")
    if arm == "T1":
        prefix += event
    result = prefix + body + list(continuation)
    if arm == "T4":
        result += event
    return result


def cell(rows):
    result = {"n": len(rows)}
    for mode in ("value_exact", "strict_exact"):
        c = {"A": 0, "B": 0, "copy": 0, "other": 0}
        for r in rows:
            matches = r["score"][mode]
            label = next((label for key, label in (("A", "A"), ("B", "B"), ("OFF", "copy")) if matches[key]), "other")
            c[label] += 1
        result[mode] = c
        result[mode + "_wilson95"] = {k: wilson(v, len(rows)) for k, v in c.items()} if rows else {}
    result["breakage"] = sum(r["score"]["breakage"] for r in rows)
    result["breakage_wilson95"] = wilson(result["breakage"], len(rows)) if rows else None
    return result


def aggregate(rows):
    arms = {a: {s: cell([r for r in rows if r["arm"] == a and r["step"] == s]) for s in ("SWITCH", "BACK")} for a in ARMS}
    complete = all(c["n"] == 32 for a in arms.values() for c in a.values())
    result = dict(arms=arms, complete=complete, readings=None)
    if not complete:
        return result
    def proportion(arm, key):
        k = arms[arm]["SWITCH"]["value_exact"][key]
        return dict(arm=arm, label=key, k=k, n=32, wilson95=wilson(k, 32))
    def contrast(left, right):
        x, y = proportion(left, "B"), proportion(right, "B")
        lx, ux = wilson(x["k"], 32, 0.975)
        ly, uy = wilson(y["k"], 32, 0.975)
        paired = {a: {r["episode"]: r["score"]["value_exact"]["B"] for r in rows if r["arm"] == a and r["step"] == "SWITCH"} for a in (left, right)}
        gains = sum(paired[left][ep] and not paired[right][ep] for ep in range(32))
        losses = sum(paired[right][ep] and not paired[left][ep] for ep in range(32))
        return dict(left=x, right=y, delta_count=x["k"]-y["k"], delta_fraction=(x["k"]-y["k"])/32,
                    conservative_wilson_based95=[max(-1, lx-uy), min(1, ux-ly)], paired_gains=gains, paired_losses=losses,
                    threshold_met=x["k"]-y["k"] >= 12)
    a, b = proportion("T3", "A"), proportion("T2", "B")
    result["readings"] = dict(ROLE=contrast("T1", "R3"), PATTERN=dict(T3_A=a, T2_B=b, threshold_met=a["k"] >= 24 and b["k"] >= 24), RECENCY=contrast("T4", "T1"))
    result["ascending_default_prior"] = proportion("T2", "A")
    return result


def generate(eng, prefix, query, values):
    """Use check36's ordinary text-prefill path, then single-sequence greedy decode."""
    from stencil.function_vectors import repeated_4gram_fraction

    s = eng.session()
    eng.prefill(s, prefix)
    logits = eng.forward_batch([query], s["cache"])
    output, eos = [], None
    for _ in range(MAX_NEW):
        token = int(logits[0, -1].argmax())
        if token in eng.eos:
            eos = token
            break
        output.append(token)
        if len(output) < MAX_NEW:
            logits = eng.forward_batch([[token]], s["cache"])
    text = eng.tok.decode(output, skip_special_tokens=False)
    trailing = ([eos] if eos is not None else eng.enc("<|im_end|>")) + eng.enc("\n")
    result = dict(text=text, generated_token_ids=output, eos_token_id=eos, trailing_token_ids=trailing,
                  score=score(text, values, truncated=eos is None, rep4=repeated_4gram_fraction(output)))
    del s, logits
    return result


def cpu_check():
    import torch
    from types import SimpleNamespace
    from tokenizers import Tokenizer

    h, reference, prior = sources()
    eng = Engine(None, Tokenizer.from_file(str(ROOT / "models/qwen3-4b-hf/tokenizer.json")), SimpleNamespace(n_layer=2), torch, SimpleNamespace(check=lambda: None))
    for ep in range(32):
        for arm in ARMS:
            for step, task in (("SWITCH", "B"), ("BACK", "A")):
                ids = layout(eng, h[ep], prior, ep, arm, task)
                txt = eng.tok.decode(ids, skip_special_tokens=False)
                assert txt.count("<|im_start|>") == txt.count("<|im_end|>")
                assert txt.count("<|im_start|>assistant") == (0 if arm == "T2" else 2)
                assert CUES["A" if task == "B" else "B"] not in txt
                assert txt.count(CUES[task]) == (0 if arm == "T3" and step == "SWITCH" else 1)
                assert eng.query(reference[ep, step]["values"]) == reference[ep, step]["prompt_token_ids"]
                if arm == "R3":
                    expected = h[ep]["token_ids"][:]
                    expected[64:72] = eng.enc(CUES[task])
                    assert ids == expected
                if arm != "T2":
                    for previous in ("SET", "HOLD"):
                        answer = prior[ep, previous]["generated_token_ids"]
                        assert any(ids[i:i+len(answer)] == answer for i in range(len(ids)-len(answer)+1))
    # Exercise decoding cap, EOS and scoring through the actual generation consumer.
    eng.device = "cpu"
    eng.prefill = lambda s, ids: None
    class FakeModel:
        def __init__(self, tokens):
            self.tokens = iter(tokens)
        def __call__(self, *args):
            logits = torch.zeros(1, 1, 151646)
            logits[0, 0, next(self.tokens)] = 1
            return logits
    values = [3, 1, 2]
    eng.forward_batch = FakeModel(eng.enc("[1, 2, 3]") + [eng.tok.token_to_id("<|im_end|>")])
    r = generate(eng, [], [], values)
    assert r["score"]["strict_exact"]["A"] and r["eos_token_id"] is not None
    eng.forward_batch = FakeModel([eng.enc("x")[0]] * MAX_NEW)
    r = generate(eng, [], [], values)
    assert len(r["generated_token_ids"]) == MAX_NEW and r["eos_token_id"] is None and r["score"]["breakage"]
    assert aggregate([])["readings"] is None
    print("CPU checks passed: 32 source hashes, 320 layouts/cue placements, exact R3 histories, retained answers, actual greedy cap/EOS/scorer")


def run():
    active = gpu_pids()
    utilization = subprocess.check_output(["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"], text=True).strip()
    if active or any(int(v.strip()) != 0 for v in utilization.splitlines()):
        raise RuntimeError(f"GPU busy: apps={sorted(active)}, utilization={utilization}; abort without signals")
    out = OUT / "4b"
    assert not (out / "summary.json").exists() and not (out / "records.jsonl").exists(), "Refusing overwrite"
    histories, reference, prior = sources()
    import torch
    from tokenizers import Tokenizer
    from stencil.qwen3 import Qwen3, Qwen3Config

    (out / "prewritten-reading.md").write_bytes((OUT / "README.md").read_bytes())
    budget, rows = Budget(), []
    data = dict(status="running", seed=SEED, trunk="Qwen3-4B", pid=os.getpid(), gpu_cap_minutes=15,
                started_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), initial_gpu_compute_apps=[], initial_gpu_utilization=utilization,
                max_new_tokens=MAX_NEW, precision="bf16", hf_compatible=True, greedy=True, thinking_disabled=True,
                lineage="fit-on=none; evaluated-on=32 recorded check36/check35 S1 synthetic histories/lists; no benchmarks, fitting or training",
                prior_exchanges=2, t3_back_placement="old system slot", text_prefill_only=True,
                reading_sha256=sha(out / "prewritten-reading.md"), source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                source_hashes={str(p.relative_to(ROOT)): sha(p) for p in (Path(__file__), ROOT / "scripts/focus_check36.py", ROOT / "scripts/focus_check35.py", ROOT / "scripts/focus_check34.py", ROOT / "scripts/focus_check32_kv.py", SOURCE / "histories.jsonl", SOURCE / "records.jsonl", ROOT / "results/quick-checks/check35/4b/records.jsonl")})
    def save():
        data.update(aggregate(rows), records_count=len(rows), elapsed_seconds=time.monotonic()-budget.started)
        write_json(out / "summary.json", data)
    save()
    try:
        cfg = Qwen3Config.from_hf(ROOT / "models/qwen3-4b-hf/config.json")
        tok = Tokenizer.from_file(str(ROOT / "models/qwen3-4b-hf/tokenizer.json"))
        with torch.device("meta"):
            model = Qwen3(cfg)
        weights = torch.load(ROOT / "models/qwen3-4b.pt", mmap=True, map_location="cpu", weights_only=True)
        model.load_state_dict(weights, strict=True, assign=True)
        del weights
        for module in model.modules():
            if hasattr(module, "hf_compatible"):
                module.hf_compatible = True
        model = model.to(device="cuda", dtype=torch.bfloat16).eval().requires_grad_(False)
        torch.manual_seed(SEED)
        eng = Engine(model, tok, cfg, torch, budget)
        with torch.inference_mode():
            for ep in range(32):
                start = time.monotonic()
                for arm in ARMS:
                    continuation = []
                    for step, task in (("SWITCH", "B"), ("BACK", "A")):
                        values = reference[ep, step]["values"]
                        prefix = layout(eng, histories[ep], prior, ep, arm, task, continuation)
                        query = reference[ep, step]["prompt_token_ids"]
                        r = generate(eng, prefix, query, values)
                        r.update(episode=ep, arm=arm, step=step, target=task, values=values, prefill_token_ids=prefix,
                                 prompt_token_ids=query, source_history_sha256=histories[ep]["source_hold_sha256"],
                                 prefill_sha256=ids_sha(prefix), prompt_text=tok.decode(prefix+query, skip_special_tokens=False))
                        assert len(r["generated_token_ids"]) <= MAX_NEW
                        if arm == "R3":
                            ref = reference[ep, step]
                            r["check36_r3_tokens_equal"] = (r["generated_token_ids"] == ref["generated_token_ids"] and r["eos_token_id"] == ref["eos_token_id"])
                        with (out / "records.jsonl").open("a") as f:
                            f.write(json.dumps(r, allow_nan=False)+"\n")
                        rows.append(r)
                        continuation = query + r["generated_token_ids"] + r["trailing_token_ids"]
                data["peak_cuda_allocated_bytes"] = torch.cuda.max_memory_allocated()
                if ep == 0:
                    elapsed = time.monotonic()-start
                    data["pilot"] = dict(seconds_per_episode=elapsed, projected_total_minutes=(time.monotonic()-budget.started+31*elapsed)/60)
                save()
                print(json.dumps(dict(episode=ep+1, minutes=data["elapsed_seconds"]/60, switch_B={a:data["arms"][a]["SWITCH"]["value_exact"]["B"] for a in ARMS}, pilot=data["pilot"])), flush=True)
            data["status"] = "complete"
            data["r3_replicate_equal_outputs"] = sum(r.get("check36_r3_tokens_equal", False) for r in rows)
    except StopRun as exc:
        data.update(status="partial", stop_reason=str(exc))
    except Exception as exc:
        data.update(status="error", error=repr(exc))
        raise
    finally:
        save()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        cpu_check()
    if args.run:
        with (ROOT / ".review.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            run()
