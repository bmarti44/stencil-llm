#!/usr/bin/env python3
"""Frozen check40e: router SET transfer to TypeScript and SQL, no fitting."""

from __future__ import annotations

import argparse
import ast
import fcntl
import gc
import json
import os
import random
import re
import shutil
import sqlite3
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path("/home/bmarti44/stencil-llm")
sys.path.insert(0, str(ROOT / "scripts"))
import focus_check40 as base  # noqa: E402
import focus_check40c as dose  # noqa: E402

OUT = ROOT / "results/quick-checks/check40e"
SEED = 40050
LIMIT = 3600
PAIRS = {"P1": ("Python", "TypeScript"), "P2": ("JSON", "SQL")}
ARMS = ("correct", "swapped", "shuffled", "OFF", "text-cue")
TS_LIB = Path(shutil.which("tsc")).resolve().parents[1] / "lib/typescript.js"
NODE_CHECK = r"""
const fs=require('fs'), ts=require(process.argv[1]), vm=require('vm');
const {code,name}=JSON.parse(fs.readFileSync(0,'utf8'));
try {
 const src=ts.createSourceFile(
  'answer.ts',code,ts.ScriptTarget.Latest,true,ts.ScriptKind.TS);
 if(src.parseDiagnostics.length || src.statements.length!==1)
  throw Error('syntax/statements');
 const f=src.statements[0];
 if(!ts.isFunctionDeclaration(f) || f.name?.text!==name || f.parameters.length ||
    f.modifiers?.length || !f.body || f.body.statements.length!==1 ||
    !ts.isReturnStatement(f.body.statements[0])) throw Error('restricted function');
 function expr(n) {
  if(ts.isNumericLiteral(n)) return true;
  if(ts.isParenthesizedExpression(n)) return expr(n.expression);
  if(ts.isPrefixUnaryExpression(n))
   return [ts.SyntaxKind.PlusToken,ts.SyntaxKind.MinusToken]
    .includes(n.operator)&&expr(n.operand);
  return ts.isBinaryExpression(n)&&[ts.SyntaxKind.PlusToken,
   ts.SyntaxKind.MinusToken,ts.SyntaxKind.AsteriskToken]
   .includes(n.operatorToken.kind)&&expr(n.left)&&expr(n.right);
 }
 if(!expr(f.body.statements[0].expression)) throw Error('restricted expression');
 let annotations=0;
 function visit(n){ if(n.type) annotations++; ts.forEachChild(n,visit); } visit(f);
 if(f.type && f.type.kind!==ts.SyntaxKind.NumberKeyword)
  throw Error('non-number annotation');
 const js=ts.transpileModule(code,
  {compilerOptions:{target:ts.ScriptTarget.ES2022}}).outputText;
 new vm.Script(js); // JS parser after TS annotation removal
 const value=vm.runInNewContext(js+'\n'+name+'()'); // bounded, arithmetic-only AST
 process.stdout.write(JSON.stringify({valid:true,annotations,value,js}));
} catch(e) { process.stdout.write(JSON.stringify({valid:false,error:String(e)})); }
"""
READING = """# Check40e — does router bias generalize beyond languages?

Unregistered user-authorized quick check, 2026-09-05, seed40050. Fit/train: none.
Profile-on: 16 synthetic competence tasks per pair, each cued both ways, all replies
used without success filtering. Evaluate-on: 32 new tasks per pair, disjoint input
values/statements from competence; no benchmark/sealed IFEval/BFCL inputs read.
P1 Python vs TypeScript: Go/gofmt absent on CPU, so use requested TS fallback.
P2 JSON rows vs SQL: tiny table and filter, both outputs semantically executable.
P1 inherits check40 system prompt; P2 uses its format-neutral concise counterpart
because the inherited system explicitly requests a function. Uncued P2 asks for
matching rows as a list (no JSON language cue); text cue explicitly overrides format.
OFF distribution is generated and reported first per pair, without prompt selection.

Frozen before outcomes: Qwen3-30B-A3B bf16, same loader, tuple-aware raw-router
hook, greedy fresh KV, thinking disabled, cap64, alpha3 sustained on all prefill
and decode positions/all48 layers. No grid, cap rescue, retries or outcome tuning.
Competence16 per side requires >=14 semantically correct unbroken addressed replies;
otherwise pair INELIGIBLE and no bias screen. Profiles are token-weighted mean raw
router logits at generated non-EOS own positions via teacher forcing of exactly
those32 replies. Bias=3*(side profile - two-side mean); swapped opposite direction;
shuffled expert-index permutation per layer seed40052 with matched per-layer norms.
Report all layer top8 IDs/intersection fractions. Inherit 40b same-experts gate:
if overlap>90% in EVERY layer, pair INELIGIBLE; no alternative profile selection.
Screen32 uncued tasks: OFF first, then correct/swapped/shuffled/text-cue per task.
P1 target TypeScript; P2 target SQL. Text cue visible, no bias. Other arms uncued.

Executable checkers: P1 Python AST or installed TS parser plus type-annotation
presence, transpile to JS, JS parser and execution of one arithmetic-only named
zero-argument function. Allowed arithmetic: integers, parentheses, unary +/- and
binary +,-,*. Require exact requested name and numeric answer; no fence-label
credit. Untyped valid JS is recorded separately and outside the paired checker.
P2 parse JSON list of objects with exactly integer id/value fields, or restrict SQL
to SELECT * / id,value FROM items WHERE one numeric comparison (optional ORDER BY
id, optional semicolon), then execute via in-memory SQLite. Compare row multisets
to an independently computed Python reference. No arbitrary generated-code exec.
Breakage = truncation, fence error, invalid/out-of-pair syntax, or wrong semantics.
This stronger semantic bar is deliberate; raw identity and semantic counts separate.
GENERALIZES iff correct addressed AND semantically correct >=20/32, correct
breakage<=2/32, shuffled addressed AND semantically correct<=4/32. Else MARGINAL
iff correct>=12/32, else NOT. Ineligible/incomplete are reported literally. If
resource-only projection requires16 tasks, thresholds scale to10/16,1/16,2/16;
MARGINAL6/16; label any such reading reduced exploratory screen. No data selection.
OFF default fails descriptively if expected side<20/32; report absence of a clear
default and paired flips, do not redesign prompts or claim paired flips from target
outputs already present OFF. Non-language transfer is stated independently of P1.

Cost: 64 competence +320 screen generations and64 teacher-forced profiles.
Prior measured conservative15.05 tokens/s; cap-based total with load600s,
1s per generation/profile and25% reserve: (600+384*64/15.05+448)*1.25=3351.196s
(<3600s). Both32-task screens provisioned; after competence use measured slowest
capped generation estimate (including prefill) for resource-only reduction before
any screen. Cooperative per-token deadline reserves cleanup; never signal/terminate.
Charge model load, kernel checks, profiles, checkers and cleanup to one GPU hour.
Foreground only; coordinate all quick-check RUNNING.flag files under review lock,
wait for other compute users; Brian pid2705 exempt and never touched. No push.
"""


def write(name, obj):
    base.write_json(OUT / name, obj)


def bank():
    rng = random.Random(SEED)
    result = {}
    for pair in PAIRS:
        result[pair] = {}
        for split, n in [("competence", 16), ("screen", 32)]:
            tasks = []
            for i in range(n):
                tid = f"{pair}_{split}_{i:02d}"
                if pair == "P1":
                    vals = rng.sample(
                        range(2, 35) if split == "competence" else range(40, 90), 4
                    )
                    a, b, c, d = vals
                    expr = [
                        f"(({a}+{b})*({c}-{d}))",
                        f"(({a}*{b})+({c}*{d}))",
                        f"(({a}-{b})-({c}+{d}))",
                    ][i % 3]
                    name = f"solve_{split}_{i:02d}"
                    task = dict(
                        id=tid,
                        pair=pair,
                        name=name,
                        expression=expr,
                        expected=arithmetic(ast.parse(expr, mode="eval").body),
                        prompt=f"Write a zero-argument function named {name} that returns {expr}.",  # noqa: E501
                    )
                else:
                    values = sorted(
                        rng.sample(
                            range(1, 35) if split == "competence" else range(40, 99), 3
                        )
                    )
                    rng.shuffle(values)
                    rows = [dict(id=j + 1, value=v) for j, v in enumerate(values)]
                    op = (">", "<", ">=", "<=")[i % 4]
                    threshold = sorted(values)[1]
                    task = dict(
                        id=tid, pair=pair, rows=rows, op=op, threshold=threshold
                    )
                    task["expected"] = [
                        r for r in rows if compare(r["value"], op, threshold)
                    ]
                    task["prompt"] = (
                        f"Table items (columns id, value):\n{json.dumps(rows, separators=(',', ':'))}\nReturn the matching rows as a list where value {op} {threshold}. Keep both columns."  # noqa: E501
                    )
                tasks.append(task)
            result[pair][split] = tasks
    return result


def arithmetic(node):
    if isinstance(node, ast.Constant) and type(node.value) is int:
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        v = arithmetic(node.operand)
        return v if isinstance(node.op, ast.UAdd) else -v
    if isinstance(node, ast.BinOp) and isinstance(
        node.op, (ast.Add, ast.Sub, ast.Mult)
    ):
        a, b = arithmetic(node.left), arithmetic(node.right)
        return (
            a + b
            if isinstance(node.op, ast.Add)
            else a - b
            if isinstance(node.op, ast.Sub)
            else a * b
        )
    raise ValueError("outside arithmetic grammar")


def compare(a, op, b):
    return {
        ">": a > b,
        "<": a < b,
        ">=": a >= b,
        "<=": a <= b,
        "=": a == b,
        "!=": a != b,
        "<>": a != b,
    }[op]


def messages(task, cue=None):
    if task["pair"] == "P1":
        return base.messages_for(task, cue)
    suffix = (
        ""
        if cue is None
        else (
            " Answer with a SQL query instead of a row list."
            if cue == "SQL"
            else " Answer with a JSON list of row objects."
        )
    )
    return [
        dict(
            role="system",
            content="Answer the request concisely. Follow the requested answer format. No examples or extra explanation.",  # noqa: E501
        ),
        dict(role="user", content=task["prompt"] + suffix + base.SUFFIX),
    ]


def score(text, task, truncated=False):
    code, fence = base.extract_code(text)
    identity, semantic, detail = "invalid", False, {}
    if task["pair"] == "P1":
        try:
            tree = ast.parse(code)
            assert len(tree.body) == 1
            f = tree.body[0]
            assert isinstance(f, ast.FunctionDef) and f.name == task["name"]
            assert not f.args.args and not f.args.posonlyargs and not f.args.kwonlyargs
            assert (
                f.args.vararg is None and f.args.kwarg is None and not f.decorator_list
            )
            assert len(f.body) == 1 and isinstance(f.body[0], ast.Return)
            value = arithmetic(f.body[0].value)
            identity, semantic = "Python", value == task["expected"]
            detail = dict(value=value)
        except (SyntaxError, AssertionError, ValueError, TypeError):
            proc = subprocess.run(
                [shutil.which("node"), "-e", NODE_CHECK, str(TS_LIB)],
                input=json.dumps(dict(code=code, name=task["name"])),
                text=True,
                capture_output=True,
                check=True,
            )
            detail = json.loads(proc.stdout)
            if detail["valid"]:
                identity = "TypeScript" if detail["annotations"] else "JavaScript"
                semantic = detail["value"] == task["expected"]
    else:
        try:
            value = json.loads(code)
            assert isinstance(value, list)
            assert all(
                isinstance(r, dict)
                and set(r) == {"id", "value"}
                and all(type(v) is int for v in r.values())
                for r in value
            )
            identity = "JSON"
            semantic = Counter((r["id"], r["value"]) for r in value) == Counter(
                (r["id"], r["value"]) for r in task["expected"]
            )
            detail = dict(rows=value)
        except (ValueError, AssertionError, TypeError):
            pattern = r"\s*SELECT\s+(\*|id\s*,\s*value)\s+FROM\s+items\s+WHERE\s+(?:value)\s*(>=|<=|<>|!=|=|>|<)\s*(-?\d+)\s*(?:ORDER\s+BY\s+id(?:\s+ASC)?)?\s*;?\s*"  # noqa: E501
            if re.fullmatch(pattern, code, re.I):
                with sqlite3.connect(":memory:") as db:
                    db.execute("CREATE TABLE items (id INTEGER, value INTEGER)")
                    db.executemany(
                        "INSERT INTO items VALUES (?,?)",
                        [(r["id"], r["value"]) for r in task["rows"]],
                    )
                    value = db.execute(code).fetchall()
                identity = "SQL"
                semantic = Counter(value) == Counter(
                    (r["id"], r["value"]) for r in task["expected"]
                )
                detail = dict(rows=[list(v) for v in value])
    broken = bool(
        truncated or fence or identity not in PAIRS[task["pair"]] or not semantic
    )
    return dict(
        identity=identity,
        semantic=bool(semantic),
        broken=broken,
        valid_skill=None if broken else identity,
        fence_error=fence,
        detail=detail,
    )


def aggregate(rows, target):
    return dict(
        n=len(rows),
        identity=dict(Counter(r["score"]["identity"] for r in rows)),
        valid=dict(Counter(r["score"]["valid_skill"] or "broken" for r in rows)),
        target=sum(r["score"]["valid_skill"] == target for r in rows),
        broken=sum(r["score"]["broken"] for r in rows),
        semantic=sum(r["score"]["semantic"] for r in rows),
        truncated=sum(r["truncated"] for r in rows),
    )


def verdict(arms, n):
    if n not in (16, 32) or any(arms[a]["n"] != n for a in ARMS):
        return "PARTIAL"
    c, s = arms["correct"], arms["shuffled"]
    if (
        c["target"] >= n * 20 / 32
        and c["broken"] <= n * 2 / 32
        and s["target"] <= n * 4 / 32
    ):
        return "GENERALIZES"
    return "MARGINAL" if c["target"] >= n * 12 / 32 else "NOT"


def cpu_checks():
    assert not shutil.which("go") and not shutil.which("gofmt"), (
        "P1 fallback must match preflight"
    )
    b = bank()
    count = 0
    for pair, splits in b.items():
        assert not (
            {t["prompt"] for t in splits["competence"]}
            & {t["prompt"] for t in splits["screen"]}
        )
        for task in splits["competence"] + splits["screen"]:
            if pair == "P1":
                codes = {
                    "Python": f"def {task['name']}():\n    return {task['expression']}",
                    "TypeScript": f"function {task['name']}(): number {{ return {task['expression']}; }}",  # noqa: E501
                }
            else:
                codes = {
                    "JSON": json.dumps(task["expected"]),
                    "SQL": f"SELECT id, value FROM items WHERE value {task['op']} {task['threshold']};",  # noqa: E501
                }
            for skill, code in codes.items():
                s = score(code, task)
                assert s["valid_skill"] == skill, (s, task)
                assert score(code, task, True)["broken"]
                assert score("```x\n" + code, task)["broken"]
                count += 1
    p1, p2 = b["P1"]["competence"][0], b["P2"]["competence"][0]
    assert (
        score(f"function {p1['name']}() {{ return {p1['expression']}; }}", p1)[
            "identity"
        ]
        == "JavaScript"
    )
    assert score(f"def {p1['name']}():\n    return 0", p1)["broken"]
    assert score("SELECT * FROM items WHERE value > -999", p2)["broken"]
    assert score("SELECT * FROM items; DROP TABLE items;", p2)["broken"]
    assert score('[{"id":true,"value":1}]', p2)["broken"]
    cells = {a: dict(n=32, target=0, broken=0) for a in ARMS}
    cells["correct"]["target"] = 20
    assert verdict(cells, 32) == "GENERALIZES"
    cells["shuffled"]["target"] = 5
    assert verdict(cells, 32) == "MARGINAL"
    cells["correct"]["target"] = 11
    assert verdict(cells, 32) == "NOT"
    return dict(
        canonical_cases=count,
        negative_fixtures=True,
        boundaries=True,
        go=shutil.which("go"),
        gofmt=shutil.which("gofmt"),
        typescript_library=str(TS_LIB),
        typescript_sha256=base.sha(TS_LIB),
        node=subprocess.check_output(["node", "--version"], text=True).strip(),
        real_consumer=dose.cpu_checks(),
    )


def prepare():
    OUT.mkdir(parents=True, exist_ok=True)
    assert not (OUT / "records.jsonl").exists()
    write("cpu.json", cpu_checks())
    write("banks.json", bank())
    (OUT / "prewritten-reading.md").write_text(READING)
    write(
        "projection.json",
        dict(
            generations=384,
            profiles=64,
            capped_tokens=24576,
            prior_tps=15.05,
            projected_seconds=(600 + 384 * 64 / 15.05 + 448) * 1.25,
            cap_seconds=LIMIT,
        ),
    )
    files = [
        Path(__file__),
        ROOT / "scripts/focus_check40.py",
        ROOT / "scripts/focus_check40c.py",
        OUT / "banks.json",
        OUT / "prewritten-reading.md",
        TS_LIB,
    ]
    write("freeze.json", dict(seed=SEED, files={str(p): base.sha(p) for p in files}))
    print("CPU checker/real-router tests PASS; pre-outcome freeze ready.", flush=True)


def verify():
    for p, digest in json.loads((OUT / "freeze.json").read_text())["files"].items():
        assert base.sha(Path(p)) == digest, p


def profiles(engine, records, pair):
    import torch

    means, per_task = [], []
    for skill in PAIRS[pair]:
        total, count = None, 0
        for r in records:
            if r["arm"] != skill:
                continue
            if time.monotonic() >= engine.deadline - 30:
                raise base.BudgetStop("profile reserve")
            gen = [t for t in r["generated_token_ids"] if t not in engine.eos]
            assert gen
            ids = r["input_token_ids"] + gen
            h = engine.hooks
            h.reset_capture()
            h.capture_slice = slice(len(r["input_token_ids"]), len(ids))
            h.capture, h.bias = True, None
            with torch.inference_mode():
                engine.model(
                    input_ids=torch.tensor([ids], device=engine.device),
                    use_cache=False,
                    logits_to_keep=1,
                )
            torch.cuda.synchronize()
            h.capture, h.capture_slice = False, None
            assert all(c == len(gen) for c in h.counts)
            sums = h.sums.cpu().clone()
            item = dict(
                record_id=r["id"],
                task_id=r["task_id"],
                skill=skill,
                count=len(gen),
                logit_sums=sums,
            )
            per_task.append(item)
            directory = OUT / "profiles"
            directory.mkdir(exist_ok=True)
            torch.save(item, directory / f"{pair}-{skill}-{r['task_id']}.pt")
            total = sums if total is None else total + sums
            count += len(gen)
        means.append(total / count)
    means = torch.stack(means).float()
    normal, shuffle = base.make_biases(means, seed=SEED + 2)
    assert torch.allclose(normal.norm(dim=-1), shuffle.norm(dim=-1))
    biases = dict(correct=3 * normal[1], swapped=3 * normal[0], shuffled=3 * shuffle[1])
    layers = []
    for layer_index in range(means.shape[1]):
        top = [torch.topk(p[layer_index], 8).indices.tolist() for p in means]
        layers.append(
            dict(
                layer=layer_index,
                top_experts=dict(zip(PAIRS[pair], top, strict=True)),
                overlap=len(set(top[0]) & set(top[1])) / 8,
            )
        )
    stats = dict(
        layers=layers,
        mean_overlap=sum(layer["overlap"] for layer in layers) / len(layers),
        same_experts=all(layer["overlap"] > 0.90 for layer in layers),
    )
    torch.save(
        dict(
            means=means,
            normal=normal,
            shuffled=shuffle,
            per_task=per_task,
            biases=biases,
        ),
        OUT / f"{pair}-profiles.pt",
    )
    write(f"{pair}-profile-statistics.json", stats)
    write(
        f"{pair}-profile-freeze.json",
        dict(
            records_at_freeze=len(records),
            alpha=3,
            profile_sha256=base.sha(OUT / f"{pair}-profiles.pt"),
            screen_bias_records_at_freeze=0,
        ),
    )
    return biases, stats


def ready():
    flags = sorted(
        str(p) for p in (ROOT / "results/quick-checks").glob("*/RUNNING.flag")
    )
    gpu = [p for p in base.gpu_pids() if int(p) != 2705]
    available = (
        int(re.search(r"MemAvailable:\s+(\d+)", Path("/proc/meminfo").read_text())[1])
        * 1024
    )
    return dict(
        flags=flags,
        other_gpu_pids=gpu,
        mem_available_gib=available / 2**30,
        ready=not flags and not gpu and available > 70 * 2**30,
    )


def run():
    import torch

    verify()
    assert not (OUT / "records.jsonl").exists(), "No outcome overwrite/retry"
    lock = (ROOT / ".review.lock").open("a")
    while True:
        status = ready()
        print(json.dumps(status), flush=True)
        if status["ready"]:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                if ready()["ready"]:
                    break
                fcntl.flock(lock, fcntl.LOCK_UN)
            except BlockingIOError:
                pass
        time.sleep(60)
    flag = OUT / "RUNNING.flag"
    with flag.open("x") as f:
        f.write(str(os.getpid()) + "\n")
    start = time.monotonic()
    base.GPU_SECONDS, base.SEED = LIMIT, SEED
    engine = None
    rows = []
    summary = dict(pairs={}, reading="PARTIAL", cap_seconds=LIMIT)
    journal = (OUT / "records.jsonl").open("x")
    b = json.loads((OUT / "banks.json").read_text())

    def request(task, phase, arm, cue=None, bias=None):
        r, _ = engine.generate(messages(task, cue), bias=bias, cap=64)
        r.update(
            id=len(rows),
            pair=task["pair"],
            task_id=task["id"],
            phase=phase,
            arm=arm,
            cue=cue,
            alpha=3 if bias is not None else None,
            score=score(r["text"], task, r["truncated"]),
        )
        assert not r["retained_kv"] and len(r["history"]) == 2
        journal.write(json.dumps(r) + "\n")
        journal.flush()
        rows.append(r)
        print(
            json.dumps(
                dict(
                    n=len(rows),
                    pair=task["pair"],
                    phase=phase,
                    arm=arm,
                    skill=r["score"]["valid_skill"],
                    broken=r["score"]["broken"],
                    elapsed=time.monotonic() - start,
                )
            ),
            flush=True,
        )
        if r["cost_stopped"]:
            raise base.BudgetStop("cooperative generation deadline")
        return r

    try:
        engine = base.Engine(start)
        runtime = dose.runtime()
        runtime.update(
            load_seconds=engine.load_seconds,
            raw_slot_verified_layers=sum(
                dose.raw_contract(g) for g in engine.hooks.gates
            ),
            model=str(base.MODEL),
            seed=SEED,
        )
        write("runtime.json", runtime)
        kernel = engine.verify_kernel()
        write("kernel.json", kernel)
        assert kernel["adopted"]
        eligible = {}
        for pair, sides in PAIRS.items():
            comp = [
                request(t, "competence", side, cue=side)
                for side in sides
                for t in b[pair]["competence"]
            ]
            counts = {
                side: sum(
                    r["arm"] == side and r["score"]["valid_skill"] == side for r in comp
                )
                for side in sides
            }
            summary["pairs"][pair] = dict(
                competence=counts, reading="INELIGIBLE", arms={}
            )
            write("summary.json", summary)
            if min(counts.values()) >= 14:
                biases, stats = profiles(engine, comp, pair)
                summary["pairs"][pair]["profile_statistics"] = stats
                if not stats["same_experts"]:
                    eligible[pair] = biases
        elapsed = time.monotonic() - start
        # Capped duration includes actual prompt prefill; no outcome enters sizing.
        capped = max(
            r["seconds"] * 64 / max(1, len(r["generated_token_ids"])) for r in rows
        )
        n = 32
        projected = (
            elapsed
            + 1.25 * ((len(eligible) * 4 + len(PAIRS)) * n * (capped + 0.15))
            + 30
        )
        if projected > LIMIT:
            n = 16
            projected = (
                elapsed
                + 1.25 * ((len(eligible) * 4 + len(PAIRS)) * n * (capped + 0.15))
                + 30
            )
        write(
            "measured-projection.json",
            dict(
                elapsed=elapsed,
                capped_generation_seconds=capped,
                screen_n=n,
                projected_seconds=projected,
                eligible_pairs=list(eligible),
                peak_allocated_gib=torch.cuda.max_memory_allocated() / 2**30,
            ),
        )
        if projected > LIMIT:
            raise base.BudgetStop("16-task screen does not fit measured projection")
        for pair in PAIRS:
            target = PAIRS[pair][1]
            # OFF shown even when competence failed; no intervention on ineligible pair.
            for t in b[pair]["screen"][:n]:
                request(t, "screen", "OFF")
            off = aggregate(
                [
                    r
                    for r in rows
                    if r["pair"] == pair
                    and r["phase"] == "screen"
                    and r["arm"] == "OFF"
                ],
                target,
            )
            write(f"{pair}-OFF-default.json", off)
            print("OFF DEFAULT " + pair + " " + json.dumps(off), flush=True)
            if pair not in eligible:
                summary["pairs"][pair]["arms"]["OFF"] = off
                continue
            for t in b[pair]["screen"][:n]:
                for arm in ("correct", "swapped", "shuffled", "text-cue"):
                    request(
                        t,
                        "screen",
                        arm,
                        cue=target if arm == "text-cue" else None,
                        bias=eligible[pair].get(arm),
                    )
            arms = {
                a: aggregate(
                    [
                        r
                        for r in rows
                        if r["pair"] == pair
                        and r["phase"] == "screen"
                        and r["arm"] == a
                    ],
                    target,
                )
                for a in ARMS
            }
            summary["pairs"][pair].update(
                arms=arms, reading=verdict(arms, n), screen_n=n
            )
            write("summary.json", summary)
        summary["reading"] = "COMPLETE"
    except base.BudgetStop as exc:
        summary["reason"] = str(exc)
    except Exception as exc:
        summary["reason"] = repr(exc)
        raise
    finally:
        journal.close()
        if engine is not None:
            summary["peak_allocated_gib"] = torch.cuda.max_memory_allocated() / 2**30
            engine.hooks.close()
            del engine
            gc.collect()
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        summary.update(
            gpu_seconds=time.monotonic() - start,
            records=len(rows),
            generated_tokens=sum(len(r["generated_token_ids"]) for r in rows),
        )
        summary["cap_overrun_seconds"] = max(0, summary["gpu_seconds"] - LIMIT)
        write("summary.json", summary)
        flag.unlink()
        lock.close()
        print(json.dumps(summary), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["prepare", "run", "test"], required=True)
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare()
    elif args.mode == "test":
        print(json.dumps(cpu_checks()))
    else:
        run()


if __name__ == "__main__":
    main()
