#!/usr/bin/env python3
"""Disclosed, bounded norm-matched SUM/PRODUCT routing follow-up."""

# ruff: noqa: E501
from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import random
import re
import subprocess
import time

import focus_check43 as prior

base = prior.base
ROOT = base.ROOT
OUT = ROOT / "results/quick-checks/check43b"
OLD = ROOT / "results/quick-checks/check43"
LANG = ROOT / "results/quick-checks/check40b"
SETUP_LIMIT = 1440
FINAL_LIMIT = 2700
ARMS = prior.ARMS
READING = """# Check43b — frozen reading and execution choices

Unregistered, disclosed, authorized quick check; no fitting or training.
Profile-on: all 32 committed check43 cued Python donor outputs, without filtering.
Select-on: the existing eight check43 Python setup prompts (development reuse).
Evaluate-on: fresh generated banks seeds 96063/96064, Python and JavaScript,
with four prompt formulations; no fit/profile/setup prompt overlap. Same reduction
families recur, so this tests new instances/formulations, not new task families.
Sanity-on: first eight frozen check40c uncued tasks, deliberately reused positive
controls with frozen check40b JS bias times 3/4 (its stored tensor is alpha4).
No evaluation benchmark or sealed input is used. All weights stay frozen.

Teacher-force all existing donor non-EOS outputs. Save raw router logits at EVERY
generated token, plus decoded token/absolute-position maps. Locate each identity literal d after its accumulator assignment (a or acc);
assert literal 0/1. Pair1 first diverges at the variable name, not identity. Report d-2,
d-1,d,d+1 and operator positions. Primary direction uses equal-example means over
[d-2,d-1,d] (two predictors plus the identity token itself). The identity token's
own router logits condition on that literal and predict its successor; they do
not predict the literal. Save all-generated and identity-only directions as
DIAGNOSTICS ONLY. No outcome-driven position/direction selection.
b=(mean_SUM-mean_PRODUCT)/2, expert-center, zero outside layers 7–34.
Sustain the bias on prefill and every decode prediction, as in check43.

Finite setup grid: this ONE primary direction, target band Frobenius norms equal
to frozen JS alpha2 then alpha3 restricted to layers7–34 (~6.8058,10.2087).
At each norm run +b, -b, stable shuffled +b and -b, eight prompts each. Shuffle
uses one expert permutation per layer, seed96062, held fixed across doses/tasks.
Run neutral OFF on all eight BEFORE any selection or setup bias. Run the eight
JS alpha3 sanity requests in the SAME engine; require >=6 valid unbroken JS/8,
otherwise INVALID and no concept conclusion. Save actual dispatch/mixture changes.
Norm equality calibrates magnitude only, and does not assume equal efficacy.
The ~9x figure refers to 6.81/0.722; the alpha3 band is 10.21 (~14.13x old unit).

CONCEPT SELECTED if -b executable PRODUCT>=6/8, malformed<=1/8 and shuffled-minus
PRODUCT<=1/8. Safe qualification additionally requires +b SUM>=6/8 and malformed
<=1/8, both shuffle signs malformed<=1/8, and paired addressed success>=6/8.
Select the FIRST safe cell in low-to-high order after completing the fixed grid.
MARGINAL if any -b has >=3/8 executable PRODUCT but no cell is selected; otherwise
CLOSE concept-level routing on this trunk operationally under this tested recipe.
If the core SELECTED criterion holds but safety fails, disclose SELECTED/NO SAFE
SET and stop; no final is allowed without a safe cell. No dose/direction rescue.

If safe: commit one chosen tensor/hash/dose and setup records BEFORE fresh final.
Final: 8 tasks per seed/language (32), seven arms +b/-b/shuffled+/shuffled-/OFF/
text-SUM/text-PRODUCT; score complete executable functions using unchanged check43
bounded interpreter. Report paired address specificity against swapped, stable
shuffle and OFF, exact one-sided McNemar with Holm, seed/language cells and newly
malformed outputs. Inherit check43 final gates: paired>=24/32, each language>=12/16,
each seed/language>=5/8, advantage>=8/32 over each comparator with Holm p<=.05,
newly malformed<=1/32 per sign, text competence>=15/16 per language/operation,
OFF/shuffle well-formed>=30/32. Collateral: 16 separately authored explicit-cue
tasks, OFF and both signs; require no new task failure versus OFF. Report final
PASS/FAIL/INELIGIBLE separately from the setup reading; no final-based selection.

Cap includes load, kernel, profiling and cleanup: 1440 seconds for setup; increase
to 2700 only after safe selection for final. Cooperative deadlines, no signals.
Before each phase project remaining generations at the slowest measured rate
with 25% reserve: 96 tokens/request for setup; for final, max(64, observed mean
concept-output length), bounded above by the unchanged 96-token request cap; stop INCOMPLETE/COST if over budget. No regeneration/resume.
Foreground only; atomically publish RUNNING.flag under .review.lock after checking
other flags and .venv compute processes; ignore Brian's permanent llama-server.
Delete our flag after natural cleanup. Explicit path commits; no push.
"""


def write(name, value):
    base.write_json(OUT / name, value)


def fresh_banks():
    old = json.loads((OLD / "banks.json").read_text())
    bank = dict(setup=old["setup"], final=[], collateral=[])
    for split, seeds, n in [("final", (96063, 96064), 8), ("collateral", (96065,), 8)]:
        for seed in seeds:
            rng = random.Random(seed)
            for language in base.LANGS:
                for i in range(n):
                    t = dict(old["setup"][i])
                    t.update(
                        id=f"{split}-{seed}-{language}-{i}",
                        seed=seed,
                        language=language,
                        name=f"fold_b_{rng.randrange(100000, 999999)}",
                        arg=f"xs_{rng.randrange(100, 999)}",
                        lo=rng.randint(1, 3),
                        hi=rng.randint(4, 7),
                    )
                    selection = {
                        "whole": "all entries",
                        "prefix": f"the first {t['hi']} entries",
                        "suffix": f"entries beginning at index {t['lo']} through the end",
                        "slice": f"entries at indices {t['lo']} inclusive to {t['hi']} exclusive",
                    }[t["family"]]
                    forms = [
                        f"Write a complete {language} function {t['name']}({t['arg']}) that returns a scalar reduction of {selection}.",
                        f"In {language}, implement {t['name']} with integer-list argument {t['arg']}. Reduce {selection} to one scalar.",
                        f"Provide {language} function {t['name']}, taking the integer list {t['arg']}: accumulate {selection} in order and return one scalar.",
                        f"Define {t['name']} in {language}. Its sole parameter {t['arg']} is an integer list; return a scalar reduction over {selection}.",
                    ]
                    t["prompt"] = (
                        forms[i % 4]
                        + " Use an explicit loop and accumulator. Do not use built-in reductions, imports, I/O or input mutation. Lists have length 0 to 8 with bounded integers. Indices are zero-based; clip endpoints to the list. Return only the complete function within 96 tokens."
                    )
                    t["inputs"] = (
                        [[], [0], [2], [-3], [1, 1, 1], [0, 2, -3], [-2, -2, 3]]
                        + [
                            [rng.randint(-3, 3) for _ in range(k)]
                            for k in range(9)
                            for _ in range(3)
                        ]
                        + [[2] * k for k in range(9)]
                    )
                    if split == "collateral":
                        t["operation"] = prior.OPS[(i // 4) % 2]
                    bank[split].append(t)
    prompts = [t["prompt"] for ts in bank.values() for t in ts]
    assert len(set(prompts)) == len(prompts) == 56
    assert not (
        {t["prompt"] for ts in old.values() for t in ts}
        & {t["prompt"] for k in ("final", "collateral") for t in bank[k]}
    )
    return bank


def profile_positions(a, b, tokenizer):
    positions = []
    for ids, literal in ((a, "0"), (b, "1")):
        matches = [
            i
            for i, token in enumerate(ids)
            if tokenizer.decode([token]) == literal
            and re.search(r"\n +[A-Za-z_]\w*\s*=\s*$", tokenizer.decode(ids[:i]))
        ]
        assert len(matches) == 1, matches
        positions.append(matches[0])
    assert positions[0] == positions[1] and positions[0] >= 2, positions
    return positions[0]


def direction(raw, torch):
    b = (raw[0] - raw[1]) / 2
    b -= b.mean(-1, keepdim=True)
    b[:7] = 0
    b[35:] = 0
    return b.float()


def cell_summary(rows, dose):
    rs = [r for r in rows if r["phase"] == "setup" and r["dose"] == dose]
    out = {
        a: {
            k: sum(r["score"][k] for r in rs if r["arm"] == a)
            for k in ("SUM", "PRODUCT", "malformed")
        }
        for a in ARMS[:4]
    }
    lookup = {(r["task_id"], r["arm"]): r["score"] for r in rs}
    out["paired"] = sum(
        lookup[t, "plus"]["SUM"] and lookup[t, "minus"]["PRODUCT"]
        for t in {r["task_id"] for r in rs}
    )
    out["concept_selected"] = (
        out["minus"]["PRODUCT"] >= 6
        and out["minus"]["malformed"] <= 1
        and out["shuffle-minus"]["PRODUCT"] <= 1
    )
    out["safe"] = (
        out["concept_selected"]
        and out["plus"]["SUM"] >= 6
        and max(out[a]["malformed"] for a in ARMS[:4]) <= 1
        and out["paired"] >= 6
    )
    return out


def final_summary(rows, bank):
    # Unchanged check43 science gates; adapt only the two fresh seed labels.
    mapped = dict(
        bank,
        final=[
            dict(t, seed={96063: 95063, 96064: 95064}[t["seed"]]) for t in bank["final"]
        ],
    )
    result = prior.final_summary(rows, mapped)
    result["cells"] = {
        k.replace("95063", "96063").replace("95064", "96064"): v
        for k, v in result["cells"].items()
    }
    return result


def prepare():
    import torch
    from transformers import AutoTokenizer

    OUT.mkdir(exist_ok=True)
    assert not (OUT / "records.jsonl").exists()
    bank = fresh_banks()
    write("banks.json", bank)
    (OUT / "prewritten-reading.md").write_text(READING)
    sanity = json.loads(
        (ROOT / "results/quick-checks/check40c/tasks.json").read_text()
    )[:8]
    write("sanity-tasks.json", sanity)
    tokenizer = AutoTokenizer.from_pretrained(base.MODEL, local_files_only=True)
    donors = [
        json.loads(x)
        for x in (OLD / "records.jsonl").read_text().splitlines()
        if json.loads(x)["phase"] == "donor"
    ]
    pairs = {(r["task_id"], r["arm"]): r for r in donors}
    ds = [
        profile_positions(
            pairs[t["id"], "SUM"]["generated_token_ids"],
            pairs[t["id"], "PRODUCT"]["generated_token_ids"],
            tokenizer,
        )
        for t in json.loads((OLD / "banks.json").read_text())["donor"]
    ]
    js = (
        torch.load(LANG / "frozen-biases.pt", map_location="cpu", weights_only=True)[
            "correct"
        ].float()
        / 4
    )
    norms = [float((js[7:35] * a).norm()) for a in (2, 3)]
    write(
        "cpu.json",
        dict(
            checker=prior.cpu_tests(
                dict(
                    bank,
                    final=[
                        dict(t, seed={96063: 95063, 96064: 95064}[t["seed"]])
                        for t in bank["final"]
                    ],
                )
            ),
            router=prior.cpu_router_test(),
            donor_divergences=ds,
            target_norms=norms,
        ),
    )
    files = [
        __file__,
        ROOT / "scripts/focus_check43.py",
        ROOT / "scripts/focus_check40.py",
        ROOT / "scripts/focus_check40b.py",
        ROOT / "scripts/focus_check40c.py",
        OLD / "records.jsonl",
        OLD / "banks.json",
        LANG / "frozen-biases.pt",
        OUT / "banks.json",
        OUT / "sanity-tasks.json",
        OUT / "prewritten-reading.md",
    ]
    write(
        "recipe-freeze.json",
        dict(
            files={
                str(p.resolve().relative_to(ROOT)): base.sha(p)
                for p in map(type(OUT), files)
            },
            target_norms=norms,
        ),
    )
    print("CPU preparation PASS", norms, ds, flush=True)


def ready():
    flags = [str(p) for p in (ROOT / "results/quick-checks").glob("*/RUNNING.flag")]
    ps = subprocess.check_output(["ps", "-eo", "pid,args"], text=True).splitlines()
    others = [
        p
        for p in ps
        if ".venv/" in p
        and "python" in p
        and int(p.split()[0]) != os.getpid()
        and not any(x in p for x in ("/bin/bash", "bash -c"))
    ]
    return dict(flags=flags, other_python=others, ready=not flags and not others)


@contextlib.contextmanager
def reservation():
    while True:
        with (ROOT / ".review.lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                state = ready()
                if state["ready"]:
                    with (OUT / "RUNNING.flag").open("x") as f:
                        f.write(json.dumps(dict(pid=os.getpid(), check="43b")))
                    break
            except BlockingIOError:
                state = dict(review_lock=True)
        print(json.dumps(state), flush=True)
        time.sleep(30)
    try:
        yield
    finally:
        (OUT / "RUNNING.flag").unlink()


def run():
    import torch

    torch.set_num_threads(4)
    prior.verified.runtime()
    prior.validate_commit(json.loads((OUT / "recipe-freeze.json").read_text()))
    assert not (OUT / "records.jsonl").exists(), "No regeneration"
    with reservation():
        execute(torch)


def execute(torch):
    bank = json.loads((OUT / "banks.json").read_text())
    sanity = json.loads((OUT / "sanity-tasks.json").read_text())
    start = time.monotonic()
    base.GPU_SECONDS = SETUP_LIMIT - 20
    base.SEED = 96061
    rows, engine, audit = [], None, None
    summary = dict(reading="INCOMPLETE", reason="interrupted")
    journal = (OUT / "records.jsonl").open("x")

    def request(task, phase, arm, bias=None, dose=None, op=None):
        audit.reset()
        messages = (
            base.messages_for(task) if phase == "sanity" else prior.messages(task, op)
        )
        r, _ = engine.generate(messages, bias=bias, cap=64 if phase == "sanity" else 96)
        scorer = base.score if phase == "sanity" else prior.score
        r.update(
            id=len(rows),
            task_id=task["id"],
            seed=task.get("seed"),
            language=task.get("language"),
            phase=phase,
            arm=arm,
            dose=dose,
            dispatch=audit.finish(),
            score=scorer(r["text"], task, r["truncated"] or r["cost_stopped"]),
            allocation_seconds=time.monotonic() - start,
        )
        journal.write(json.dumps(r) + "\n")
        journal.flush()
        os.fsync(journal.fileno())
        rows.append(r)
        print(
            json.dumps(
                dict(
                    event=phase,
                    id=r["id"],
                    arm=arm,
                    dose=dose,
                    score={
                        k: v
                        for k, v in r["score"].items()
                        if k in ("SUM", "PRODUCT", "malformed", "language", "broken")
                    },
                    elapsed=time.monotonic() - start,
                )
            ),
            flush=True,
        )
        if r["cost_stopped"]:
            raise base.BudgetStop("token deadline")
        return r

    def admit(stage, remaining, limit, extra=0):
        rates = [len(r["generated_token_ids"]) / r["seconds"] for r in rows]
        rate = min(rates)
        concept = [
            len(r["generated_token_ids"]) for r in rows if r["phase"] != "sanity"
        ]
        estimate_tokens = (
            96 if limit == SETUP_LIMIT else max(64, sum(concept) / len(concept))
        )
        projection = (
            time.monotonic()
            - start
            + 1.25 * (remaining * estimate_tokens / rate + extra)
        )
        record = dict(
            stage=stage,
            elapsed=time.monotonic() - start,
            remaining=remaining,
            estimated_tokens_per_request=estimate_tokens,
            rate=rate,
            projection=projection,
            limit=limit,
        )
        with (OUT / "cost.jsonl").open("a") as f:
            f.write(json.dumps(record) + "\n")
        if projection > limit - 20:
            raise base.BudgetStop(f"projection refusal {stage}: {projection}")

    try:
        engine = base.Engine(start)
        for p in engine.model.parameters():
            p.requires_grad_(False)
        write("kernel.json", engine.verify_kernel())
        assert json.loads((OUT / "kernel.json").read_text())["adopted"]
        raw_count = sum(prior.verified.raw_contract(g) for g in engine.hooks.gates)
        assert raw_count == 48
        write(
            "runtime.json",
            dict(
                **prior.verified.runtime(),
                load_seconds=engine.load_seconds,
                raw_slot_layers=raw_count,
                pid=os.getpid(),
                weights=base.weights_ready(),
            ),
        )
        audit = prior.DispatchAudit(engine)
        # Measure actual uncued OFF before profiling, biased setup, or selection.
        for t in bank["setup"]:
            request(t, "OFF-baseline", "OFF")
        write(
            "off-default.json",
            {
                k: sum(r["score"][k] for r in rows)
                for k in ("SUM", "PRODUCT", "malformed")
            },
        )
        admit("after-OFF", 72, SETUP_LIMIT, extra=80)
        js = (
            torch.load(
                LANG / "frozen-biases.pt", map_location="cpu", weights_only=True
            )["correct"].float()
            * 0.75
        )
        for t in sanity:
            request(t, "sanity", "JS-alpha3", js)
        sanity_rows = [r for r in rows if r["phase"] == "sanity"]
        good = sum(
            r["score"]["language"] == "JavaScript" and not r["score"]["broken"]
            for r in sanity_rows
        )
        summary["sanity_JS"] = good
        if good < 6:
            summary.update(reading="INVALID", reason="same-runtime JS sanity below 6/8")
            return
        donors = [
            json.loads(x)
            for x in (OLD / "records.jsonl").read_text().splitlines()
            if json.loads(x)["phase"] == "donor"
        ]
        pairs = {(r["task_id"], r["arm"]): r for r in donors}
        all_means, windows, identities, maps = {}, {}, {}, []
        (OUT / "profiles").mkdir()
        for r in donors:
            if time.monotonic() > engine.deadline - 60:
                raise base.BudgetStop("profile deadline")
            gen = [x for x in r["generated_token_ids"] if x not in engine.eos]
            d = profile_positions(
                pairs[r["task_id"], "SUM"]["generated_token_ids"],
                pairs[r["task_id"], "PRODUCT"]["generated_token_ids"],
                engine.tokenizer,
            )
            ids = r["input_token_ids"] + gen
            assert (
                engine.tokenizer.apply_chat_template(
                    r["history"],
                    tokenize=True,
                    return_dict=False,
                    add_generation_prompt=True,
                    enable_thinking=False,
                )
                == r["input_token_ids"]
            )
            offset = len(r["input_token_ids"])
            collected = {}

            def capture(i, collected=collected, offset=offset):
                def hook(module, args, out):
                    collected[i] = out[0][offset:].detach().cpu()

                return hook

            handles = [
                g.register_forward_hook(capture(i), prepend=True)
                for i, g in enumerate(engine.hooks.gates)
            ]
            try:
                with torch.inference_mode():
                    engine.model(
                        input_ids=torch.tensor([ids], device=engine.device),
                        use_cache=False,
                        logits_to_keep=1,
                    )
            finally:
                for h in handles:
                    h.remove()
            raw = torch.stack([collected[i] for i in range(48)])
            assert raw.shape == (48, len(gen), 128) and torch.isfinite(raw).all()
            key = (r["task_id"], r["arm"])
            all_means[key] = raw.double().mean(1)
            windows[key] = raw[:, d - 2 : d + 1].double().mean(1)
            identities[key] = raw[:, d].double()
            info = dict(
                task_id=r["task_id"],
                operation=r["arm"],
                donor_record_id=r["id"],
                input_token_ids=r["input_token_ids"],
                generated_token_ids=gen,
                identity_index=d,
                primary_indices=list(range(d - 2, d + 1)),
                around=[
                    dict(
                        index=i,
                        absolute=offset + i,
                        token_id=gen[i],
                        token=engine.tokenizer.decode([gen[i]]),
                    )
                    for i in range(d - 2, d + 2)
                ],
                operator_indices=[
                    i
                    for i in range(len(gen))
                    if "+=" in engine.tokenizer.decode([gen[i]])
                    or "*=" in engine.tokenizer.decode([gen[i]])
                ],
            )
            maps.append(info)
            torch.save(
                dict(**info, raw_generated_logits=raw),
                OUT / "profiles" / f"{r['arm']}-{r['task_id']}.pt",
            )
            print(
                json.dumps(
                    dict(
                        event="profile",
                        donor=r["id"],
                        d=d,
                        elapsed=time.monotonic() - start,
                    )
                ),
                flush=True,
            )
        write("profile-positions.json", maps)
        derived = {}
        for name, source in [
            ("window", windows),
            ("all-generated", all_means),
            ("identity", identities),
        ]:
            means = torch.stack(
                [
                    torch.stack(
                        [v for (task, op), v in source.items() if op == o]
                    ).mean(0)
                    for o in prior.OPS
                ]
            )
            derived[name] = dict(means=means, bias=direction(means, torch))
        b = derived["window"]["bias"]
        generator = torch.Generator().manual_seed(96062)
        perm = torch.stack(
            [torch.randperm(128, generator=generator) for _ in range(48)]
        )
        shuffled = b.gather(1, perm)
        norms = json.loads((OUT / "recipe-freeze.json").read_text())["target_norms"]
        torch.save(
            dict(derived=derived, permutations=perm, shuffle=shuffled),
            OUT / "profiles.pt",
        )
        write(
            "magnitude.json",
            dict(
                unit_window_norm=float(b.norm()),
                unit_identity_norm=float(derived["identity"]["bias"].norm()),
                unit_all_generated_norm=float(derived["all-generated"]["bias"].norm()),
                target_norms=norms,
                old_prompt_unit_norm=0.7224128246,
                JS_alpha3_all_norm=float(js.norm()),
                JS_alpha3_band_norm=float(js[7:35].norm()),
                scales=[n / float(b.norm()) for n in norms],
                per_layer_unit_norm=b.norm(dim=1).tolist(),
                per_layer_JS_alpha3_norm=js.norm(dim=1).tolist(),
            ),
        )
        admit("after-profiles", 64, SETUP_LIMIT)
        grid = []
        for dose, norm in zip((2, 3), norms, strict=True):
            bias = b * (norm / b.norm())
            shuffle = shuffled * (norm / b.norm())
            for arm, tensor in zip(
                ARMS[:4], (bias, -bias, shuffle, -shuffle), strict=True
            ):
                for t in bank["setup"]:
                    request(t, "setup", arm, tensor, dose)
            grid.append(dict(dose=dose, norm=norm, **cell_summary(rows, dose)))
            write("grid.json", grid)
        safe = next((g for g in grid if g["safe"]), None)
        core = any(g["concept_selected"] for g in grid)
        summary.update(
            reading="CONCEPT SELECTED"
            if core
            else "MARGINAL"
            if max(g["minus"]["PRODUCT"] for g in grid) >= 3
            else "CLOSE",
            grid=grid,
            safe_cell=safe,
        )
        if safe is None:
            summary["reason"] = "NO SAFE SET; final and collateral not run"
            return
        engine.deadline = start + FINAL_LIMIT - 20
        admit("before-final", 272, FINAL_LIMIT)
        chosen = b * (safe["norm"] / b.norm())
        shuffled = shuffled * (safe["norm"] / b.norm())
        torch.save(
            dict(
                plus=chosen,
                minus=-chosen,
                shuffle_plus=shuffled,
                shuffle_minus=-shuffled,
            ),
            OUT / "selected.pt",
        )
        write(
            "final-freeze.json",
            dict(
                cell=safe,
                files={
                    str(p.relative_to(ROOT)): base.sha(p)
                    for p in (
                        OUT / "selected.pt",
                        OUT / "records.jsonl",
                        OUT / "banks.json",
                        OUT / "recipe-freeze.json",
                    )
                },
                records=len(rows),
            ),
        )
        paths = [
            str(p.relative_to(ROOT))
            for p in OUT.rglob("*")
            if p.is_file() and p.name not in ("RUNNING.flag", "console.log")
        ]
        subprocess.run(["git", "add", "-f", "--", *paths], cwd=ROOT, check=True)
        subprocess.run(
            [
                "git",
                "commit",
                "-m",
                "check43b freeze safe setup choice before fresh final",
                "--",
                *paths,
            ],
            cwd=ROOT,
            check=True,
        )
        tensors = dict(
            zip(
                ARMS,
                (chosen, -chosen, shuffled, -shuffled, None, None, None),
                strict=True,
            )
        )
        for t in bank["final"]:
            for arm in ARMS:
                request(
                    t,
                    "final",
                    arm,
                    tensors[arm],
                    safe["dose"],
                    arm[5:] if arm.startswith("text-") else None,
                )
        for t in bank["collateral"]:
            for arm in ("OFF", "plus", "minus"):
                request(
                    t, "collateral", arm, tensors[arm], safe["dose"], t["operation"]
                )
        summary["final"] = final_summary(rows, bank)
    except base.BudgetStop as exc:
        summary.update(reading="INCOMPLETE/COST", reason=str(exc))
    except Exception as exc:
        summary.update(reading="INVALID", reason=repr(exc))
        raise
    finally:
        journal.close()
        if audit is not None:
            audit.close()
        if engine is not None:
            engine.hooks.close()
            summary["peak_allocated_GiB"] = torch.cuda.max_memory_allocated() / 2**30
            del engine
        torch.cuda.empty_cache()
        summary.update(
            allocation_seconds=time.monotonic() - start,
            records=len(rows),
            tokens=sum(len(r["generated_token_ids"]) for r in rows),
        )
        write("summary.json", summary)
        print(json.dumps(summary), flush=True)


def audit_records():
    bank = json.loads((OUT / "banks.json").read_text())
    tasks = {t["id"]: t for ts in bank.values() for t in ts}
    tasks.update(
        {t["id"]: t for t in json.loads((OUT / "sanity-tasks.json").read_text())}
    )
    rows = [json.loads(x) for x in (OUT / "records.jsonl").read_text().splitlines()]
    for i, r in enumerate(rows):
        assert r["id"] == i
        scorer = base.score if r["phase"] == "sanity" else prior.score
        assert (
            scorer(r["text"], tasks[r["task_id"]], r["truncated"] or r["cost_stopped"])
            == r["score"]
        )
        assert (
            hashlib.sha256(json.dumps(r["input_token_ids"]).encode()).hexdigest()
            == r["input_sha256"]
        )
        assert not r["retained_kv"] and not r["cache_prefix_token_ids"]
        assert all(v["consumer_mismatches"] == 0 for v in r["dispatch"].values())
        if r["phase"] != "sanity":
            assert all(
                v["changed_route_tokens"] == 0 and v["changed_weight_tokens"] == 0
                for k, v in r["dispatch"].items()
                if not 7 <= int(k.split("-")[0]) <= 34
            )
        if r["arm"] == "OFF" or r["arm"].startswith("text-"):
            assert all(
                v["changed_route_tokens"] == 0 and v["changed_weight_tokens"] == 0
                for v in r["dispatch"].values()
            )
    summary = json.loads((OUT / "summary.json").read_text())
    for cell in summary.get("grid", []):
        assert all(cell[k] == v for k, v in cell_summary(rows, cell["dose"]).items())
    if "final" in summary:
        assert final_summary(rows, bank) == summary["final"]
    write(
        "audit.json",
        dict(
            records=len(rows),
            all_scores_recomputed=True,
            all_input_hashes=True,
            consumer_mismatches=0,
            outside_band_changes=0,
            reading=summary["reading"],
        ),
    )
    print("Audit PASS", len(rows))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("prepare", "run", "audit"), required=True)
    args = parser.parse_args()
    {"prepare": prepare, "run": run, "audit": audit_records}[args.mode]()


if __name__ == "__main__":
    main()
