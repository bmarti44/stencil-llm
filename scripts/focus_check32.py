#!/usr/bin/env python3
"""Unregistered check 32: fixed skill bank and deterministic external slot latch."""

# ruff: noqa: I001

from __future__ import annotations

import argparse
import ast
import gc
import hashlib
import json
import os
import random
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
OUT = ROOT / "results/quick-checks/check32"
SEED = 32032
N = 64
MAX_NEW = 64
ARMS = (
    "address",
    "spotlight",
    "reminder",
    "removed",
    "wrong",
    "wrong_spotlight",
    "off",
)
STEPS = ("SET", "HOLD", "SWITCH", "BACK", "CLEAR")
TASKS = ("A", "A", "B", "A", None)
DESC = {"A": "Sort ascending.", "B": "Reverse input order."}
USER = "<|im_start|>user\n"
ASSISTANT = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
LINEAGE = (
    "Unregistered check 32. Fit-on=nothing; evaluated-on=320 fresh seed-32032 "
    "synthetic operand sets, paired across arms/trunks, no unordered-set reuse. "
    "No benchmark inputs/responses, fitting, training, or parameter selection."
)


def write_json(path, data):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")
    tmp.replace(path)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def episodes():
    rng = random.Random(SEED)
    seen, result = set(), []
    for episode in range(N):
        slot_a = rng.choice((1, 2))
        order = rng.sample([1, 2], 2)
        values = []
        while len(values) < 5:
            v = rng.sample(range(-20, 21), rng.randint(5, 8))
            key = tuple(sorted(v))
            if key in seen or v in (sorted(v), sorted(v, reverse=True)):
                continue
            seen.add(key)
            values.append(v)
        result.append(
            dict(
                episode=episode,
                slot_to_skill={str(slot_a): "A", str(3 - slot_a): "B"},
                bank_order=order,
                values=values,
                arm_order=rng.sample(list(ARMS), len(ARMS)),
            )
        )
    return result


def score(text, values, task, *, truncated=False, rep4=0.0):
    strict = False
    try:
        obj = json.loads(text)
        strict = isinstance(obj, list) and all(type(v) is int for v in obj)
    except (ValueError, TypeError):
        pass
    clean = text.strip()
    fence = re.fullmatch(r"```(?:json|python)?\s*\n?(.*?)\n?```", clean, re.S)
    if fence:
        clean = fence[1].strip()
    parsed = None
    try:
        obj = ast.literal_eval(clean)
        if isinstance(obj, list) and all(
            type(v) is int or (isinstance(v, str) and re.fullmatch(r"[+-]?\d+", v))
            for v in obj
        ):
            parsed = [int(v) for v in obj]
    except (ValueError, SyntaxError, TypeError):
        pass
    repetition = rep4 > 0.2 or (parsed is not None and len(parsed) != len(set(parsed)))
    broken = parsed is None or truncated or repetition
    answers = {"A": sorted(values), "B": list(reversed(values)), "copy": values}
    label = next((k for k, v in answers.items() if parsed == v), "other")
    expected = answers[task or "copy"]
    return dict(
        parsed=parsed,
        label=label,
        expected=expected,
        correct=parsed == expected and not broken,
        strict_correct=strict and parsed == expected and not broken,
        strict_schema=strict,
        invalid_values=parsed is None,
        truncated=truncated,
        repetition=repetition,
        breakage=broken,
        clear_imposition=task is None and label in ("A", "B"),
    )


def summarize(data, records):
    result = dict(data)
    arms = {}
    for arm in ARMS:
        rows = [r for r in records if r["arm"] == arm]
        grouped = {}
        for r in rows:
            grouped.setdefault(r["episode"], []).append(r)
        complete = [rs for rs in grouped.values() if len(rs) == 5]
        checkpoints = {}
        for step in STEPS:
            rs = [r for r in rows if r["checkpoint"] == step]
            checkpoints[step] = dict(
                n=len(rs),
                correct=sum(r["score"]["correct"] for r in rs),
                strict_correct=sum(r["score"]["strict_correct"] for r in rs),
                breakage=sum(r["score"]["breakage"] for r in rs),
                impositions=sum(r["score"]["clear_imposition"] for r in rs),
            )
        arms[arm] = dict(
            n_decisions=len(rows),
            complete_episodes=len(complete),
            all_correct=sum(
                all(r["score"]["correct"] for r in rs[:4]) for rs in complete
            ),
            strict_all_correct=sum(
                all(r["score"]["strict_correct"] for r in rs[:4]) for rs in complete
            ),
            broken_episodes=sum(
                any(r["score"]["breakage"] for r in rs) for rs in complete
            ),
            clear_impositions=checkpoints["CLEAR"]["impositions"],
            checkpoints=checkpoints,
            token_totals={
                k: sum(r["token_counts"][k] for r in rows)
                for k in (
                    "bank",
                    "address",
                    "reminder",
                    "common",
                    "filler",
                    "generated",
                )
            },
            decision_seconds=sum(r["latency_seconds"] for r in rows),
            context_seconds=sum(r["context_seconds"] for r in rows),
            spotlight_forward_calls=sum(r["spotlight_forward_calls"] for r in rows),
        )
    result["arms"] = arms
    complete = all(a["complete_episodes"] == N for a in arms.values())
    candidates = {}
    for arm, wrong in (("address", "wrong"), ("spotlight", "wrong_spotlight")):
        a, bar = arms[arm], arms["reminder"]
        conditions = dict(
            floor=a["all_correct"] >= 48,
            reminder_ratio=10 * a["all_correct"] >= 9 * bar["all_correct"],
            breakage=a["broken_episodes"] <= 1,
            clear=a["clear_impositions"] <= bar["clear_impositions"],
            wrong_at_or_below_off=arms[wrong]["all_correct"]
            <= arms["off"]["all_correct"],
        )
        verdict = (
            "INCOMPLETE"
            if not complete
            else "PASS"
            if all(conditions.values())
            else "MARGINAL"
            if a["all_correct"] >= 32
            else "FAIL"
        )
        candidates[arm] = dict(verdict=verdict, conditions=conditions)
    result["candidates"] = candidates
    result["verdict"] = next(
        v
        for v in ("INCOMPLETE", "PASS", "MARGINAL", "FAIL")
        if any(c["verdict"] == v for c in candidates.values())
    )
    return result


def gpu_pids():
    output = subprocess.check_output(
        ["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"], text=True
    )
    return {int(s.strip()) for s in output.splitlines() if s.strip()}


class StopProbe(RuntimeError):
    pass


class Budget:
    def __init__(self):
        self.started = time.monotonic()
        self.deadline = self.started + 90 * 60
        self.last_check = 0.0

    def check(self):
        now = time.monotonic()
        # Reserve five seconds for flushing, unloading and summaries.
        if now >= self.deadline - 5:
            raise StopProbe("90 cumulative GPU-minute cap; partial results")
        if now - self.last_check >= 5:
            self.last_check = now
            others = gpu_pids() - {os.getpid()}
            if others:
                raise StopProbe(f"Other GPU compute process appeared: {sorted(others)}")


class Engine:
    """Retained-cache adaptation of focus1_probe and SELECTOR's span spotlight."""

    def __init__(self, model, tok, cfg, budget, device="cuda"):
        from stencil.ctrb import uniform_span_bias
        from stencil.qwen3 import KVCache
        from stencil.qwen_task import FILLER
        from stencil.t2_runner import BETA, LAYERS

        self.model, self.tok, self.budget, self.device = model, tok, budget, device
        self.cache_type, self.cfg = KVCache, cfg
        self.bias_fn, self.beta, self.layers = uniform_span_bias, BETA, LAYERS
        self.eos = {tok.token_to_id(t) for t in ("<|im_end|>", "<|endoftext|>")}
        assert (
            None not in self.eos and self.beta == 2 and max(self.layers) < cfg.n_layer
        )
        self.filler = self.encode(" ".join(FILLER) * 10)[:128]
        assert len(self.filler) == 128

    def encode(self, text):
        return self.tok.encode(text).ids

    def forward(self, ids, span=None):
        import torch

        self.budget.check()
        bias = None
        if span is not None:
            b = self.bias_fn(
                len(ids),
                self.cache.length + len(ids),
                span,
                amount=self.beta,
                device=self.device,
            )
            assert int(torch.count_nonzero(b)) == span[1] - span[0]
            bias = dict.fromkeys(self.layers, b)
            self.calls += 1
        logits = self.model(
            torch.tensor([ids], device=self.device), cache=self.cache, attn_bias=bias
        )
        self.history.extend(ids)
        assert self.cache.length == len(self.history)
        assert all(k.shape[2] == len(self.history) for k in self.cache.k)
        return logits

    def start(self, ep, arm):
        started = time.monotonic()
        self.cache, self.history, self.calls = self.cache_type(self.cfg), [], 0
        self.spans, self.bank = {}, ""
        bank_ids, wrapper_ids = [], []
        if arm != "removed":
            entries = [
                f"Skill {slot}: {DESC[ep['slot_to_skill'][str(slot)]]}"
                for slot in ep["bank_order"]
            ]
            self.bank = " ".join(entries)
            enc = self.tok.encode(self.bank)
            wrapper_ids = self.encode("<|im_start|>system\n")
            # Same sentence-character overlap -> token-column construction as
            # qwen_task's ledger_spans and t2_runner.ledger_sentence_spans.
            for slot, entry in zip(ep["bank_order"], entries, strict=True):
                lo = self.bank.index(entry)
                cols = [
                    i
                    for i, (a, b) in enumerate(enc.offsets)
                    if a < lo + len(entry) and b > lo
                ]
                assert cols
                self.spans[slot] = (
                    len(wrapper_ids) + cols[0],
                    len(wrapper_ids) + cols[-1] + 1,
                )
            bank_ids = enc.ids
            self.forward(wrapper_ids + bank_ids + self.encode("<|im_end|>\n"))
        return dict(
            bank=len(bank_ids),
            common=len(self.history) - len(bank_ids),
            seconds=time.monotonic() - started,
        )

    def decision(self, ep, arm, index, setup):
        from stencil.function_vectors import repeated_4gram_fraction

        context_started = time.monotonic()
        before_context = len(self.history)
        filler_ids = []
        if index == 1:
            filler_ids = (
                self.encode(USER)
                + self.filler
                + self.encode(ASSISTANT + "Noted.<|im_end|>\n")
            )
            self.forward(filler_ids)
        context_seconds = (
            time.monotonic() - context_started + (setup["seconds"] if index == 0 else 0)
        )
        task, values = TASKS[index], ep["values"][index]
        slot = next((int(s) for s, t in ep["slot_to_skill"].items() if t == task), None)
        if arm in ("wrong", "wrong_spotlight") and slot is not None:
            slot = 3 - slot
        if arm in ("off", "reminder"):
            slot = None
        address = f"Use skill {slot}." if slot is not None else ""
        reminder = DESC[task] if arm == "reminder" and task is not None else ""
        request = (
            "Process these integers."
            if task
            else "Copy these integers in the given order."
        )
        request += f" Output only a JSON array. Integers: {json.dumps(values)}"
        address_ids, reminder_ids = self.encode(address), self.encode(reminder)
        cue_ids = address_ids + reminder_ids
        prompt_ids = (
            self.encode(USER)
            + cue_ids
            + self.encode(("\n" if cue_ids else "") + request + ASSISTANT)
        )
        span = (
            self.spans[slot]
            if arm in ("spotlight", "wrong_spotlight") and slot
            else None
        )
        calls_before = self.calls
        started = time.monotonic()
        logits = self.forward(prompt_ids, span)
        generated, terminal = [], None
        for _ in range(MAX_NEW):
            nxt = int(logits[0, -1].argmax())
            # Feed ALL tokens, including terminal EOS, into the same cache.
            logits = self.forward([nxt], span)
            if nxt in self.eos:
                terminal = nxt
                break
            generated.append(nxt)
        truncated = terminal is None
        closure = self.encode("<|im_end|>\n" if truncated else "\n")
        self.forward(closure)
        text = self.tok.decode(generated, skip_special_tokens=False)
        rep4 = repeated_4gram_fraction(generated)
        latency = time.monotonic() - started
        active_calls = self.calls - calls_before
        assert active_calls == (
            1 + len(generated) + (terminal is not None) if span else 0
        )
        return dict(
            episode=ep["episode"],
            arm=arm,
            checkpoint=STEPS[index],
            target=task,
            values=values,
            slot_to_skill=ep["slot_to_skill"],
            bank_order=ep["bank_order"],
            bank=self.bank,
            bank_token_spans=self.spans,
            latch_slot=slot,
            address=address,
            reminder=reminder,
            request=request,
            spotlight_span=span,
            spotlight_layers=list(self.layers) if span else [],
            beta=self.beta if span else 0,
            spotlight_forward_calls=active_calls,
            prompt_token_ids=prompt_ids,
            filler_token_ids=filler_ids,
            generated_token_ids=generated,
            terminal_token_id=terminal,
            closing_token_ids=closure,
            text=text,
            rep4=rep4,
            score=score(text, values, task, truncated=truncated, rep4=rep4),
            cache_before_context=before_context,
            cache_after=len(self.history),
            history_sha256=hashlib.sha256(
                json.dumps(self.history).encode()
            ).hexdigest(),
            context_seconds=context_seconds,
            latency_seconds=latency,
            token_counts=dict(
                bank=setup["bank"] if index == 0 else 0,
                address=len(address_ids),
                reminder=len(reminder_ids),
                filler=len(filler_ids),
                generated=len(generated) + (terminal is not None),
                common=len(prompt_ids)
                - len(cue_ids)
                + len(closure)
                + (setup["common"] if index == 0 else 0),
            ),
        )


def run_trunk(trunk, examples, budget, pre_reading_sha):
    from stencil import determinism  # noqa: F401

    import torch
    from tokenizers import Tokenizer

    from stencil.qwen3 import Qwen3, Qwen3Config

    out = OUT / trunk
    out.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    data = dict(
        trunk=trunk,
        seed=SEED,
        lineage=LINEAGE,
        status="running",
        pid=os.getpid(),
        started_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        source_commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        source_sha256={
            str(p.relative_to(ROOT)): sha(p)
            for p in (
                Path(__file__),
                ROOT / "src/stencil/qwen3.py",
                ROOT / "src/stencil/ctrb.py",
                ROOT / "src/stencil/t2_runner.py",
                ROOT / "src/stencil/qwen_task.py",
            )
        },
        pre_run_reading_sha256=pre_reading_sha,
        max_new_tokens=MAX_NEW,
        numerics="frozen bf16; hf_compatible on trunk, blocks and norms; greedy",
        cumulative_budget_minutes=90,
    )
    records, model, engine = [], None, None

    def save():
        data["elapsed_seconds"] = time.monotonic() - started
        data["cumulative_elapsed_seconds"] = time.monotonic() - budget.started
        data["peak_cuda_allocated_bytes"] = (
            torch.cuda.max_memory_allocated() if torch.cuda.is_initialized() else 0
        )
        write_json(out / "summary.json", summarize(data, records))

    def log(msg):
        print(f"[{time.monotonic() - budget.started:.1f}s] {trunk}: {msg}", flush=True)

    try:
        save()
        budget.check()
        config_dir = ROOT / f"models/qwen3-{trunk}-hf"
        cfg = Qwen3Config.from_hf(config_dir / "config.json")
        tok = Tokenizer.from_file(str(config_dir / "tokenizer.json"))
        data["config"] = vars(cfg)
        data["tokenizer_sha256"] = sha(config_dir / "tokenizer.json")
        with torch.device("meta"):
            model = Qwen3(cfg)
        weights = torch.load(
            ROOT / f"models/qwen3-{trunk}.pt",
            map_location="cpu",
            weights_only=True,
            mmap=True,
        )
        model.load_state_dict(weights, strict=True, assign=True)
        del weights
        for module in model.modules():
            if hasattr(module, "hf_compatible"):
                module.hf_compatible = True
        model = model.to(device="cuda", dtype=torch.bfloat16).eval()
        model.requires_grad_(False)
        torch.manual_seed(SEED)
        torch.cuda.reset_peak_memory_stats()
        engine = Engine(model, tok, cfg, budget)
        data["filler_body_token_ids"] = engine.filler
        data["filler_body_text"] = tok.decode(engine.filler)
        log("model loaded; 64 episodes x 7 arms x 5 decisions")
        with (
            torch.inference_mode(),
            (out / "records.jsonl").open("x", buffering=1) as stream,
        ):
            for ep in examples:
                ep_started = time.monotonic()
                for arm in ep["arm_order"]:
                    setup = engine.start(ep, arm)
                    for index in range(5):
                        row = engine.decision(ep, arm, index, setup)
                        row["id"] = len(records)
                        # Preserve the first-history prefix for exact replay.
                        if index == 0:
                            row["bank_prefix_token_ids"] = engine.history[
                                : row["cache_before_context"]
                            ]
                        stream.write(json.dumps(row, allow_nan=False) + "\n")
                        stream.flush()
                        records.append(row)
                    budget.check()
                ep_seconds = time.monotonic() - ep_started
                if ep["episode"] == 0:
                    data["pilot"] = dict(
                        seconds=ep_seconds,
                        decisions=35,
                        tokens=sum(r["token_counts"]["generated"] for r in records),
                        projected_trunk_seconds=64 * ep_seconds,
                        peak_cuda_allocated_bytes=torch.cuda.max_memory_allocated(),
                    )
                    log(f"first-episode pilot {data['pilot']}")
                save()
                counts = {
                    a: v["all_correct"]
                    for a, v in summarize(data, records)["arms"].items()
                }
                log(f"episode {ep['episode'] + 1}/64; complete-correct {counts}")
        data["status"] = "complete"
    except StopProbe as exc:
        data["status"], data["stop_reason"] = "partial", str(exc)
        log(str(exc))
    except Exception as exc:
        data["status"], data["stop_reason"] = "error", repr(exc)
        raise
    finally:
        save()
        del engine, model
        gc.collect()
        torch.cuda.empty_cache()
    log(f"{data['status']}: {summarize(data, records)['verdict']}")
    return data["status"]


def self_test():
    # Pure CPU checks of parsing, controls, exact retained-cache boundaries and
    # real uniform_span_bias consumer, using a tiny scripted fake trunk.
    from stencil import determinism  # noqa: F401

    import torch
    from tokenizers import Tokenizer

    from stencil.qwen3 import Qwen3Config

    v = [3, -1, 2, -4, 0]
    for text in (
        "[-4,-1,0,2,3]",
        '["-4","-1","0","2","3"]',
        '```json\n["-4", "-1", "0", "2", "3"]\n```',
    ):
        assert score(text, v, "A")["correct"]
    for text in (
        "[true, -1, 0, 2, 3]",
        "[3.0, -1, 2, -4, 0]",
        "[-4,-1,0,2,2]",
        "answer: [-4,-1,0,2,3]",
    ):
        assert not score(text, v, "A")["correct"]
    assert not score("[-4,-1,0,2,3]", v, "A", truncated=True)["correct"]
    assert score("[-4,-1,0,2,3]", v, None)["clear_imposition"]
    eps = episodes()
    flat = [v for ep in eps for v in ep["values"]]
    assert len({tuple(sorted(v)) for v in flat}) == 320
    assert all(len({tuple(v), tuple(sorted(v)), tuple(reversed(v))}) == 3 for v in flat)
    tok = Tokenizer.from_file(str(ROOT / "models/qwen3-1.7b-hf/tokenizer.json"))
    cfg = Qwen3Config.from_hf(ROOT / "models/qwen3-1.7b-hf/config.json")

    class Unlimited:
        def check(self):
            pass

    class Fake:
        def __call__(self, tokens, *, cache, attn_bias):
            cache.length += tokens.shape[1]
            for i in range(cfg.n_layer):
                cache.k[i] = torch.zeros(1, 1, cache.length, 1)
            logits = torch.zeros(1, 1, tok.get_vocab_size())
            logits[0, 0, tok.token_to_id("<|im_end|>")] = 1
            return logits

    engine = Engine(Fake(), tok, cfg, Unlimited(), device="cpu")
    records = []
    for arm in ARMS:
        setup = engine.start(eps[0], arm)
        for index in range(5):
            row = engine.decision(eps[0], arm, index, setup)
            assert row["terminal_token_id"] is not None
            assert row["cache_after"] == sum(row["token_counts"].values()) + row[
                "cache_before_context"
            ] - (setup["bank"] + setup["common"] if index == 0 else 0)
            if index == 4:
                assert (
                    row["address"] == row["reminder"] == ""
                    and row["spotlight_forward_calls"] == 0
                )
            records.append(row)
    summary = summarize({}, records)
    assert summary["verdict"] == "INCOMPLETE"
    assert all(a["complete_episodes"] == 1 for a in summary["arms"].values())
    # Exercise the verdict consumer at the exact 90%-of-bar boundary.
    full = []
    for ep in range(64):
        for row in records:
            r = dict(row, episode=ep)
            count = {"address": 58, "spotlight": 57, "reminder": 64}.get(r["arm"], 0)
            r["score"] = dict(
                row["score"],
                correct=ep < count,
                strict_correct=ep < count,
                breakage=False,
                clear_imposition=False,
            )
            full.append(r)
    s = summarize({}, full)
    assert s["candidates"]["address"]["verdict"] == "PASS"
    assert s["candidates"]["spotlight"]["verdict"] == "MARGINAL"
    print(
        "CPU self-test passed: scorer, operands, cache/EOS/filler, "
        "spotlight/CLEAR, verdict boundaries"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    active = gpu_pids()
    if active:
        raise RuntimeError(f"GPU busy before launch; abort: {sorted(active)}")
    for trunk in ("4b", "1.7b"):
        if (OUT / trunk / "summary.json").exists():
            raise RuntimeError(f"Refusing to overwrite existing {trunk} results")
    reading = OUT / "README.md"
    frozen = OUT / "pre-run-reading.md"
    if frozen.exists():
        raise RuntimeError("Refusing to replace frozen pre-run reading")
    frozen.write_bytes(reading.read_bytes())
    examples = episodes()
    write_json(
        OUT / "episodes.json", dict(seed=SEED, lineage=LINEAGE, episodes=examples)
    )
    budget = Budget()
    for trunk in ("4b", "1.7b"):
        status = run_trunk(trunk, examples, budget, sha(frozen))
        if status != "complete":
            if trunk == "4b":
                (OUT / "1.7b").mkdir(exist_ok=True)
                write_json(
                    OUT / "1.7b/summary.json",
                    dict(
                        trunk="1.7b",
                        status="not_run",
                        verdict="INCOMPLETE",
                        reason="Primary trunk did not complete; see 4b/summary.json",
                    ),
                )
            break
    print(
        f"Total GPU wall-minutes: {(time.monotonic() - budget.started) / 60:.3f}",
        flush=True,
    )


if __name__ == "__main__":
    main()
