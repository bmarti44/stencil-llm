# ruff: noqa: E501, B023
# Sealed check-49 script (results/quick-checks/README.md): the late-binding lambdas
# and long task strings are part of the recorded run and are left exactly as run.
"""Frozen Check49 two-LoRA experiment. CPU prepare, then one cooperative GPU run.

No benchmark inputs, imports with side effects, checkpoint selection or cache reuse.
"""

from __future__ import annotations

import argparse
import ast
import contextlib
import hashlib
import json
import math
import os
import random
import re
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/quick-checks/check49"
BASE = ROOT / "models/qwen3-4b-hf"
ADAPTERS = ROOT / "data/classifier/model/focus-lora-4b"
SYSTEM = "Return only one complete function with the requested name. Use a fenced code block. No explanation or examples."
RULES = {
    "python": "Live rules: (1) Write all code in Python.",
    "js": "Live rules: (1) Write all code in JavaScript.",
}
MODES = ["python", "js"]
STAGES = ["SET", "HOLD", "SWITCH", "BACK", "CLEAR"]
NEUTRAL = [
    {
        "role": "user",
        "content": "Pause for a note: the meeting is on Thursday. Acknowledge with OK.",
    },
    {"role": "assistant", "content": "OK"},
]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def write(p, obj):
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def journal(name, obj):
    with (OUT / name).open("a") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def messages(task, history=(), mode=None):
    return [
        {"role": "system", "content": SYSTEM + ("\n" + RULES[mode] if mode else "")},
        *history,
        {"role": "user", "content": task["prompt"]},
    ]


def render(tok, msgs):
    return tok.apply_chat_template(
        msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False
    )


def task(split, family, index, description, args, py, js, inputs, oracle):
    name = f"{split}_{family}_{index}"
    return dict(
        id=name,
        split=split,
        family=family,
        prompt=f"Implement {name}({args}): {description}",
        references={
            "python": f"```python\ndef {name}({args}):\n    {py}\n```",
            "js": f"```javascript\nfunction {name}({args}) {{ {js} }}\n```",
        },
        name=name,
        cases=[dict(args=x, expected=oracle(*x)) for x in inputs],
    )


def training():
    rows = []
    arrays = [[], [0], [-5, 0, 2, 2, 9], [3, 1, 8], [-2, -1], [12, 6]]
    for k in range(1, 9):
        specs = [
            (
                "offset",
                f"For integer n return n plus {k}.",
                "n",
                f"return n + {k}",
                f"return n + {k};",
                [[x] for x in [-9, 0, 2, 11]],
                lambda n: n + k,
            ),
            (
                "scale",
                f"For integer n return n times {k + 1}.",
                "n",
                f"return n * {k + 1}",
                f"return n * {k + 1};",
                [[x] for x in [-3, 0, 7]],
                lambda n: n * (k + 1),
            ),
            (
                "floor",
                f"For integer n return {k} if n is smaller than {k}, otherwise n.",
                "n",
                f"return max(n, {k})",
                f"return Math.max(n, {k});",
                [[x] for x in [-3, k, k + 1]],
                lambda n: max(n, k),
            ),
            (
                "cap",
                f"For integer n return {k} if n exceeds {k}, otherwise n.",
                "n",
                f"return min(n, {k})",
                f"return Math.min(n, {k});",
                [[x] for x in [-3, k, k + 1]],
                lambda n: min(n, k),
            ),
            (
                "greater",
                f"Return whether integer n is strictly greater than {k}.",
                "n",
                f"return n > {k}",
                f"return n > {k};",
                [[x] for x in [-1, k, k + 1]],
                lambda n: n > k,
            ),
            (
                "substitute",
                f"Replace each occurrence of {k} in integer array xs with zero; preserve order.",
                "xs",
                f"return [0 if x == {k} else x for x in xs]",
                f"return xs.map(x => x === {k} ? 0 : x);",
                [[x] for x in arrays + [[k, k, 0]]],
                lambda xs: [0 if x == k else x for x in xs],
            ),
            (
                "filter",
                f"Keep only integers in xs strictly smaller than {k}, preserving order.",
                "xs",
                f"return [x for x in xs if x < {k}]",
                f"return xs.filter(x => x < {k});",
                [[x] for x in arrays],
                lambda xs: [x for x in xs if x < k],
            ),
            (
                "count",
                f"Count occurrences of integer {k} in array xs.",
                "xs",
                f"return xs.count({k})",
                f"return xs.filter(x => x === {k}).length;",
                [[x] for x in arrays + [[k, k]]],
                lambda xs: xs.count(k),
            ),
            (
                "sumshift",
                f"Return sum of integer array xs plus {k}; empty gives {k}.",
                "xs",
                f"return sum(xs) + {k}",
                f"return xs.reduce((s,x) => s+x, {k});",
                [[x] for x in arrays],
                lambda xs: sum(xs) + k,
            ),
            (
                "head",
                f"Return first {k} elements of xs (all if shorter).",
                "xs",
                f"return xs[:{k}]",
                f"return xs.slice(0, {k});",
                [[x] for x in arrays],
                lambda xs: xs[:k],
            ),
            (
                "tail",
                f"Drop first {k} elements of xs, returning the rest.",
                "xs",
                f"return xs[{k}:]",
                f"return xs.slice({k});",
                [[x] for x in arrays],
                lambda xs: xs[k:],
            ),
            (
                "repeat",
                f"Return a string consisting of string s repeated {k} times.",
                "s",
                f"return s * {k}",
                f"return s.repeat({k});",
                [[x] for x in ["", "ab", "X"]],
                lambda s: s * k,
            ),
            (
                "pad",
                f"Append {k} zeros to array xs.",
                "xs",
                f"return xs + [0] * {k}",
                f"return xs.concat(Array({k}).fill(0));",
                [[x] for x in arrays],
                lambda xs: xs + [0] * k,
            ),
            (
                "distance",
                f"Return absolute distance of integer n from {k}.",
                "n",
                f"return abs(n - {k})",
                f"return Math.abs(n - {k});",
                [[x] for x in [-4, k, k + 9]],
                lambda n: abs(n - k),
            ),
            (
                "branch",
                f"For integer n return n-{k} when n is even, otherwise n+{k}.",
                "n",
                f"return n - {k} if n % 2 == 0 else n + {k}",
                f"return n % 2 === 0 ? n-{k} : n+{k};",
                [[x] for x in [-3, -2, 0, 5]],
                lambda n: n - k if n % 2 == 0 else n + k,
            ),
            (
                "empty",
                f"Return array xs unchanged if nonempty, otherwise [{k}].",
                "xs",
                f"return xs if xs else [{k}]",
                f"return xs.length ? xs : [{k}];",
                [[x] for x in arrays],
                lambda xs: xs if xs else [k],
            ),
        ]
        for spec in specs:
            rows.append(task("fit", spec[0], k, *spec[1:]))
    return rows


def setup():
    specs = [
        (
            "square",
            "Return the square of integer n.",
            "n",
            "return n*n",
            "return n*n;",
            [[-3], [0], [7]],
            lambda n: n**2,
        ),
        (
            "reverse",
            "Return array xs in reverse order.",
            "xs",
            "return xs[::-1]",
            "return xs.slice().reverse();",
            [[[]], [[1]], [[1, 2, 4]]],
            lambda xs: list(reversed(xs)),
        ),
        (
            "join",
            "Join strings in xs with a colon; empty gives an empty string.",
            "xs",
            'return ":".join(xs)',
            'return xs.join(":");',
            [[[]], [["a"]], [["a", "", "b"]]],
            lambda xs: ":".join(xs),
        ),
        (
            "negate",
            "Return each integer in xs with its sign reversed.",
            "xs",
            "return [-x for x in xs]",
            "return xs.map(x => -x);",
            [[[]], [[0, -1, 3]]],
            lambda xs: [-x for x in xs],
        ),
        (
            "between",
            "Return whether integer n is between integers a and b inclusive; assume a <= b.",
            "n,a,b",
            "return a <= n <= b",
            "return a <= n && n <= b;",
            [[0, 0, 2], [2, 0, 2], [3, 0, 2], [-1, 0, 2]],
            lambda n, a, b: n in range(a, b + 1),
        ),
        (
            "lengths",
            "Return lengths of the ASCII strings in xs.",
            "xs",
            "return [len(s) for s in xs]",
            "return xs.map(s => s.length);",
            [[[]], [["", "cat", "a"]]],
            lambda xs: [len(s) for s in xs],
        ),
        (
            "product",
            "Return product of all integers in xs; empty gives 1.",
            "xs",
            "p = 1\n    for x in xs: p *= x\n    return p",
            "let p=1; for (const x of xs) p*=x; return p;",
            [[[]], [[0, 2]], [[-1, 3, 2]]],
            lambda xs: math.prod(xs),
        ),
        (
            "ends",
            "Return true if ASCII string s begins and ends with the same character; empty gives false.",
            "s",
            "return bool(s) and s[0] == s[-1]",
            "return s.length > 0 && s[0] === s[s.length-1];",
            [[""], ["a"], ["aba"], ["ab"]],
            lambda s: len(s) > 0 and s[0] == s[-1],
        ),
    ]
    return [task("setup", s[0], 0, *s[1:]) for s in specs]


def evaluation():
    episodes = []
    arrays = [[], [0], [2, 2, -1, 4], [3, 1, 3, 2, 1], [-3, -1, -2], [1, 4, 9, 16]]
    for family in range(12):
        tasks = []
        for i in range(6):
            k = i + 2
            if family == 0:
                spec = (
                    "prefix",
                    f"Return running sums of integer xs, each increased by {k}.",
                    "xs",
                    f"s = {k}\n    out = []\n    for x in xs:\n        s += x\n        out.append(s)\n    return out",
                    f"let s={k}; return xs.map(x => (s+=x));",
                    [[x] for x in arrays],
                    lambda xs: [sum(xs[: j + 1]) + k for j in range(len(xs))],
                )
            elif family == 1:
                spec = (
                    "rotate",
                    f"Rotate xs left by {k} positions modulo its length; empty stays empty.",
                    "xs",
                    f"if not xs: return []\n    n = {k} % len(xs)\n    return xs[n:] + xs[:n]",
                    f"if (!xs.length) return []; const n={k}%xs.length; return xs.slice(n).concat(xs.slice(0,n));",
                    [[x] for x in arrays],
                    lambda xs: xs[k % len(xs) :] + xs[: k % len(xs)] if xs else [],
                )
            elif family == 2:
                spec = (
                    "unique",
                    f"Return first occurrences of distinct integers in xs in order, stopping after {k} distinct values.",
                    "xs",
                    f"out = []\n    for x in xs:\n        if x not in out and len(out) < {k}: out.append(x)\n    return out",
                    f"const out=[]; for (const x of xs) if (!out.includes(x) && out.length<{k}) out.push(x); return out;",
                    [[x] for x in arrays],
                    lambda xs: list(dict.fromkeys(xs))[:k],
                )
            elif family == 3:
                spec = (
                    "gaps",
                    f"Return consecutive differences xs[j+1]-xs[j], each multiplied by {k}.",
                    "xs",
                    f"return [(b-a)*{k} for a,b in zip(xs,xs[1:])]",
                    f"return xs.slice(1).map((x,i) => (x-xs[i])*{k});",
                    [[x] for x in arrays],
                    lambda xs: [
                        (xs[j + 1] - xs[j]) * k for j in range(max(0, len(xs) - 1))
                    ],
                )
            elif family == 4:
                spec = (
                    "chunks",
                    f"Partition xs into consecutive arrays of length {k}; keep the last shorter array. Empty gives [].",
                    "xs",
                    f"return [xs[j:j+{k}] for j in range(0,len(xs),{k})]",
                    f"const out=[]; for (let j=0;j<xs.length;j+={k}) out.push(xs.slice(j,j+{k})); return out;",
                    [[x] for x in arrays + [list(range(11))]],
                    lambda xs: [xs[j : j + k] for j in range(0, len(xs), k)],
                )
            elif family == 5:
                spec = (
                    "runs",
                    f"Count nonempty runs of consecutive equal values in xs, then multiply the count by {k}; empty gives zero.",
                    "xs",
                    f"return sum(j == 0 or x != xs[j-1] for j,x in enumerate(xs))*{k}",
                    f"return xs.reduce((s,x,j) => s+(j===0 || x!==xs[j-1] ? {k}:0),0);",
                    [[x] for x in arrays + [[1, 1, 2, 2, 1]]],
                    lambda xs: (
                        len([j for j in range(len(xs)) if j == 0 or xs[j] != xs[j - 1]])
                        * k
                    ),
                )
            elif family == 6:
                spec = (
                    "indices",
                    f"Return indices of elements strictly larger than both their neighbors in integer array xs; ignore first/last, then add {k} to each index.",
                    "xs",
                    f"return [j+{k} for j in range(1,len(xs)-1) if xs[j]>xs[j-1] and xs[j]>xs[j+1]]",
                    f"const out=[]; for(let j=1;j<xs.length-1;j++) if(xs[j]>xs[j-1] && xs[j]>xs[j+1]) out.push(j+{k}); return out;",
                    [[x] for x in arrays + [[1, 3, 1, 4, 0]]],
                    lambda xs: [
                        j + k
                        for j in range(1, len(xs) - 1)
                        if xs[j] > max(xs[j - 1], xs[j + 1])
                    ],
                )
            elif family == 7:
                spec = (
                    "windows",
                    f"Return sums of every contiguous window of length {k} in integer array xs; none if too short.",
                    "xs",
                    f"return [sum(xs[j:j+{k}]) for j in range(len(xs)-{k}+1)]",
                    f"const out=[]; for(let j=0;j+{k}<=xs.length;j++) out.push(xs.slice(j,j+{k}).reduce((a,b)=>a+b,0)); return out;",
                    [[x] for x in arrays + [list(range(10))]],
                    lambda xs: [sum(xs[j : j + k]) for j in range(len(xs) - k + 1)],
                )
            elif family == 8:
                spec = (
                    "alternate",
                    f"Return alternating sum of xs, starting plus at index zero, then add {k}; empty returns {k}.",
                    "xs",
                    f"return {k} + sum(x if j%2==0 else -x for j,x in enumerate(xs))",
                    f"return xs.reduce((s,x,j)=>s+(j%2===0 ? x:-x),{k});",
                    [[x] for x in arrays],
                    lambda xs: sum(xs[::2]) - sum(xs[1::2]) + k,
                )
            elif family == 9:
                spec = (
                    "flatten",
                    f"Flatten array of integer arrays xss one level, keeping only inner arrays of length at least {k}.",
                    "xss",
                    f"return [x for xs in xss if len(xs)>={k} for x in xs]",
                    f"return xss.filter(xs=>xs.length>={k}).flat();",
                    [[[]], [[[], [1, 2], [3]]], [[list(range(8)), [9, 9]]]],
                    lambda xss: sum([xs for xs in xss if len(xs) >= k], []),
                )
            elif family == 10:
                spec = (
                    "signruns",
                    f"Return the length of the longest consecutive run of strictly positive integers in xs, multiplied by {k}. Empty gives 0.",
                    "xs",
                    f"best = run = 0\n    for x in xs:\n        run = run+1 if x>0 else 0\n        best = max(best,run)\n    return best*{k}",
                    f"let best=0,run=0; for(const x of xs) {{run=x>0 ? run+1:0; best=Math.max(best,run);}} return best*{k};",
                    [[x] for x in arrays + [[1, 2, 0, 3, 4, 5]]],
                    lambda xs: (
                        max(
                            [0]
                            + [
                                b - a
                                for a in range(len(xs))
                                for b in range(a + 1, len(xs) + 1)
                                if all(x > 0 for x in xs[a:b])
                            ]
                        )
                        * k
                    ),
                )
            else:
                spec = (
                    "histogram",
                    f"Return an array of {k} counts: element r counts nonnegative integers x in xs whose remainder modulo {k} is r; ignore negatives.",
                    "xs",
                    f"return [sum(x>=0 and x%{k}==r for x in xs) for r in range({k})]",
                    f"const out=Array({k}).fill(0); for(const x of xs) if(x>=0) out[x%{k}]++; return out;",
                    [[x] for x in arrays],
                    lambda xs: [
                        len([x for x in xs if x >= 0 and x % k == r]) for r in range(k)
                    ],
                )
            tasks.append(task("eval", spec[0], i, *spec[1:]))
        episodes.append(dict(id=family, initial=MODES[family % 2], tasks=tasks))
    return episodes


def sentinels():
    # Structured non-code work, unrelated to fitting. Exact answers, no LLM judge.
    pairs = [
        (
            "Sort these words alphabetically: pear, apple, plum. Return only a JSON array.",
            ["apple", "pear", "plum"],
        ),
        ("Convert 02:15 to minutes after midnight. Return only a JSON integer.", 135),
        (
            "Which word is a color: chair, blue, road? Return only the answer as a JSON string.",
            "blue",
        ),
        ("Count letters in the word planet. Return only a JSON integer.", 6),
        ("Select the largest: 18, 7, 24, 3. Return only a JSON integer.", 24),
        ("Write the next month after April. Return only a JSON string.", "May"),
        ("Is every square a rectangle? Return only a JSON boolean.", True),
        (
            'Replace cat with dog in "cat sat". Return only the resulting JSON string.',
            "dog sat",
        ),
    ]
    return [
        dict(id=f"sentinel_{i}", prompt=p, expected=a, mode=MODES[i % 2])
        for i, (p, a) in enumerate(pairs)
    ]


def extract(text):
    m = re.fullmatch(r"\s*```(python|javascript|js)\s*\n(.*?)\n```\s*", text, re.S)
    if m:
        return ("js" if m[1] in ("js", "javascript") else "python"), m[2], True
    # Syntax can still be measured for a bare function, presentation fails.
    lang = (
        "python"
        if re.search(r"^\s*def\s", text)
        else "js"
        if re.search(r"^\s*(function|const|let)\s", text)
        else "unknown"
    )
    return lang, text.strip(), False


def execute(task, text):
    lang, code, presentation = extract(text)
    result = dict(
        language=lang, presentation=presentation, syntax=False, semantics=False
    )
    if lang == "unknown":
        return result
    if lang == "python":
        try:
            ast.parse(code)
            result["syntax"] = True
            env = {}
            ticks = 0

            def trace(frame, event, arg):
                nonlocal ticks
                ticks += 1
                if ticks > 20000:
                    raise RuntimeError("cooperative instruction budget")
                return trace

            old = sys.gettrace()
            try:
                sys.settrace(trace)
                exec(compile(code, "<candidate>", "exec"), env)
                got = [
                    env[task["name"]](*json.loads(json.dumps(c["args"])))
                    for c in task["cases"]
                ]
            finally:
                sys.settrace(old)
            result["semantics"] = json.dumps(got, sort_keys=True) == json.dumps(
                [c["expected"] for c in task["cases"]], sort_keys=True
            )
        except Exception as e:
            result["error"] = type(e).__name__ + ": " + str(e)[:180]
    else:
        # vm timeout throws within node; no OS process is signalled.
        program = """const vm=require('vm'),fs=require('fs'); const d=JSON.parse(fs.readFileSync(0,'utf8'));
let r={syntax:false,semantics:false}; try {new vm.Script(d.code);r.syntax=true;
const ctx={};vm.createContext(ctx);new vm.Script(d.code+';globalThis.__f='+d.name).runInContext(ctx,{timeout:500});
ctx.cases=d.cases;new vm.Script('globalThis.got=cases.map(c=>__f(...c.args))').runInContext(ctx,{timeout:500});
r.semantics=JSON.stringify(ctx.got)===JSON.stringify(d.cases.map(c=>c.expected));
} catch(e){r.error=String(e).slice(0,180);}process.stdout.write(JSON.stringify(r));"""
        p = subprocess.run(
            ["node", "-e", program],
            input=json.dumps(dict(code=code, name=task["name"], cases=task["cases"])),
            text=True,
            capture_output=True,
        )
        if p.returncode:
            raise RuntimeError(p.stderr)
        result.update(json.loads(p.stdout))
    return result


def prepare():
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(BASE, local_files_only=True)
    data = dict(
        fit=training(), setup=setup(), episodes=evaluation(), sentinels=sentinels()
    )
    banks = [
        data["fit"],
        data["setup"],
        [t for e in data["episodes"] for t in e["tasks"]],
    ]
    assert len(data["fit"]) == 128
    families = [{r["family"] for r in bank} for bank in banks]
    assert all(not families[i] & families[j] for i in range(3) for j in range(i))
    lengths, checked, mutants = [], 0, 0
    for bank in banks:
        for t in bank:
            for mode, ref in t["references"].items():
                n = len(tok.encode(ref, add_special_tokens=False))
                assert n <= 96, (t["id"], mode, n)
                lengths.append(n)
                score = execute(t, ref)
                assert score["semantics"] and score["presentation"], (t["id"], score)
                # Wrong constant and opposite-language valid reference exercise same consumer.
                wrong = (
                    "```python\ndef " + t["name"] + "(*args):\n    return None\n```"
                    if mode == "python"
                    else "```javascript\nfunction "
                    + t["name"]
                    + "(...args) { return null; }\n```"
                )
                assert not execute(t, wrong)["semantics"]
                other = execute(t, t["references"][MODES[1 - MODES.index(mode)]])
                assert other["semantics"] and other["language"] != mode
                mutants += 2
                if bank is data["fit"]:
                    pre = tok.encode(render(tok, messages(t)), add_special_tokens=False)
                    target = tok.encode(ref + tok.eos_token, add_special_tokens=False)
                    assert len(pre) + len(target) <= 256
                checked += 1
    # Failure taxonomy consumer witnesses.
    t = data["setup"][0]
    assert not execute(t, "```python\ndef broken(\n```")["syntax"]
    assert not execute(t, t["references"]["python"].replace("n*n", "n+1"))["semantics"]
    assert not execute(
        t, t["references"]["python"].split("\n", 1)[1].rsplit("\n", 1)[0]
    )["presentation"]
    write(OUT / "data.json", data)
    assets = {
        str(p.relative_to(ROOT)): sha(p) for p in sorted(BASE.iterdir()) if p.is_file()
    }
    contract = dict(
        seed=0,
        rank=8,
        alpha=8,
        dropout=0,
        targets=["q_proj", "v_proj"],
        batch=8,
        epoch=1,
        lr=1e-4,
        weight_decay=0.01,
        seq_cap=256,
        output_cap=96,
        fit_cap_s=600,
        gpu_cap_s=3600,
        cleanup_reserve_s=120,
        baseline_calls=24,
        mechanism_calls=16,
        total_calls=272,
        thinking=False,
        dtype="bfloat16",
        attention="sdpa",
        frozen_files=assets,
    )
    write(OUT / "contract.json", contract)
    write(
        OUT / "cpu-validation.json",
        dict(
            checked_references=checked,
            wrong_and_stale_mutants=mutants,
            max_reference_tokens=max(lengths),
            family_disjoint=True,
            fit_examples_per_mode=128,
            data_sha256=sha(OUT / "data.json"),
            code_sha256=sha(Path(__file__)),
        ),
    )
    print(json.dumps(json.loads((OUT / "cpu-validation.json").read_text())), flush=True)


class Stop(Exception):
    def __init__(self, status, reason):
        self.status, self.reason = status, reason


@contextlib.contextmanager
def pristine(model):
    """Bypass every LoRA wrapper, invoking the untouched original base layers."""
    from peft.tuners.lora.layer import LoraLayer

    saved = []
    for module in model.modules():
        if isinstance(module, LoraLayer):
            saved.append((module, module.forward))
            module.forward = module.base_layer.forward
    try:
        yield
    finally:
        for module, forward in saved:
            module.forward = forward


def run():
    import gc

    import peft
    import torch
    import transformers
    from peft import LoraConfig, get_peft_model
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        StoppingCriteria,
        StoppingCriteriaList,
    )

    validation = json.loads((OUT / "cpu-validation.json").read_text())
    assert validation["data_sha256"] == sha(OUT / "data.json")
    assert validation["code_sha256"] == sha(Path(__file__))
    assert not (OUT / "summary.json").exists(), "one shot: existing summary"
    assert not ADAPTERS.exists(), "never overwrite adapters"
    flags = list((ROOT / "results/quick-checks").glob("*/RUNNING.flag"))
    assert not flags, flags
    # CUDA ownership preflight without matching command text embedded in Codex prompts.
    for proc in Path("/proc").glob("[0-9]*"):
        try:
            parts = (proc / "cmdline").read_bytes().split(b"\0")
            exe = parts[0].decode()
            assert not (
                ".venv" in exe and "python" in exe and int(proc.name) != os.getpid()
            ), ("other python", proc.name, exe)
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            pass
    flag = OUT / "RUNNING.flag"
    with flag.open("x") as f:
        f.write(json.dumps(dict(pid=os.getpid(), check=49, start=time.time())))
    with (ROOT / ".stencil-owned-pids").open("a") as f:
        f.write(str(os.getpid()) + "\n")
    start = time.monotonic()
    summary = dict(
        status="INCOMPLETE",
        reason="run not completed",
        runtime=dict(
            torch=torch.__version__,
            transformers=transformers.__version__,
            peft=peft.__version__,
        ),
        calls=0,
    )
    model = None
    records = []
    training_log = []
    base_digests = {}
    torch.manual_seed(0)
    random.seed(0)
    torch.set_num_threads(8)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.use_deterministic_algorithms(True)
    data = json.loads((OUT / "data.json").read_text())
    contract = json.loads((OUT / "contract.json").read_text())

    def remaining():
        return 3600 - (time.monotonic() - start)

    def guard():
        if remaining() < 120:
            raise Stop("INCOMPLETE", "cooperative total deadline / cleanup reserve")

    class Deadline(StoppingCriteria):
        def __call__(self, input_ids, scores, **kwargs):
            return remaining() < 120

    def digest_tensor(t):
        return hashlib.sha256(
            t.contiguous().view(torch.uint8).cpu().numpy().tobytes()
        ).hexdigest()

    def select(mode):
        if mode is None:
            return model.disable_adapter()
        model.set_adapter(mode)
        return contextlib.nullcontext()

    def generation(t, msgs, mode, label, expected=None):
        guard()
        assert len(records) < 272
        model.eval()
        ids = tok(render(tok, msgs), return_tensors="pt", add_special_tokens=False).to(
            "cuda"
        )
        torch.cuda.synchronize()
        begin = time.monotonic()
        events = []

        def forward_begin(module, args):
            event = torch.cuda.Event(enable_timing=True)
            event.record()
            events.append([event, None])

        def forward_end(module, args, output):
            event = torch.cuda.Event(enable_timing=True)
            event.record()
            events[-1][1] = event

        pre_hook = model.get_base_model().register_forward_pre_hook(forward_begin)
        post_hook = model.get_base_model().register_forward_hook(forward_end)
        with select(mode), torch.inference_mode():
            # No past_key_values are passed: rebuild literal history on EVERY request.
            out = model.generate(
                **ids,
                max_new_tokens=96,
                do_sample=False,
                use_cache=True,
                pad_token_id=tok.eos_token_id,
                eos_token_id=tok.eos_token_id,
                stopping_criteria=StoppingCriteriaList([Deadline()]),
                return_dict_in_generate=True,
            )
        pre_hook.remove()
        post_hook.remove()
        torch.cuda.synchronize()
        elapsed = time.monotonic() - begin
        forward_ms = [a.elapsed_time(b) for a, b in events]
        # HF delegates generate to the base model; if top-level PEFT hooks are bypassed,
        # the registered hook target below is the actual generating trunk.

        generated = out.sequences[0, ids.input_ids.shape[1] :].tolist()
        text = tok.decode(generated, skip_special_tokens=True)
        capped = len(generated) >= 96 and generated[-1] != tok.eos_token_id
        score = (
            execute(t, text)
            if "cases" in t
            else dict(
                semantics=False, language="noncode", syntax=True, presentation=True
            )
        )
        if "cases" not in t:
            try:
                score["semantics"] = json.loads(text) == t["expected"]
            except (ValueError, TypeError):
                pass
        r = dict(
            id=label,
            task_id=t["id"],
            mode=mode,
            expected=expected,
            messages=msgs,
            input_ids=ids.input_ids[0].tolist(),
            token_ids=generated,
            text=text,
            input_tokens=ids.input_ids.shape[1],
            output_tokens=len(generated),
            seconds=elapsed,
            truncated=capped,
            **score,
        )
        r["prefill_seconds"] = forward_ms[0] / 1000 if forward_ms else None
        r["decode_seconds"] = sum(forward_ms[1:]) / 1000 if forward_ms else None
        assert forward_ms, "nonvacuous forward timing"
        r["success"] = (
            score["semantics"]
            and (expected is None or score["language"] == expected)
            and not capped
        )
        r["rule_carrier_positions"] = (
            (
                len(tok.encode(render(tok, msgs), add_special_tokens=False))
                - len(
                    tok.encode(
                        render(tok, [dict(msgs[0], content=SYSTEM), *msgs[1:]]),
                        add_special_tokens=False,
                    )
                )
            )
            if msgs[0]["content"].startswith(SYSTEM + "\nLive rules:")
            else 0
        )
        records.append(r)
        journal("records.jsonl", r)
        print(
            json.dumps(
                dict(
                    call=len(records),
                    id=label,
                    language=r["language"],
                    semantics=r["semantics"],
                    seconds=round(elapsed, 3),
                )
            ),
            flush=True,
        )
        guard()
        return r

    def replay(r, mode=None, bypass=False):
        ids = torch.tensor([r["input_ids"] + r["token_ids"]], device="cuda")
        with (
            select(mode),
            pristine(model) if bypass else contextlib.nullcontext(),
            torch.inference_mode(),
        ):
            logits = model(input_ids=ids, use_cache=False).logits[
                :, len(r["input_ids"]) - 1 : -1
            ]
        return digest_tensor(logits), logits.argmax(-1)[0].tolist()

    try:
        tok = AutoTokenizer.from_pretrained(BASE, local_files_only=True)
        tok.pad_token = tok.eos_token
        trunk = AutoModelForCausalLM.from_pretrained(
            BASE,
            local_files_only=True,
            dtype=torch.bfloat16,
            attn_implementation="sdpa",
        ).to("cuda")
        cfg = LoraConfig(
            r=8,
            lora_alpha=8,
            lora_dropout=0,
            target_modules=["q_proj", "v_proj"],
            bias="none",
            task_type="CAUSAL_LM",
        )
        model = get_peft_model(
            trunk, cfg, adapter_name="python", autocast_adapter_dtype=False
        )
        model.add_adapter("js", cfg)
        for n, p in model.named_parameters():
            if "lora_" in n:
                p.data = p.data.to(torch.bfloat16)
            else:
                p.requires_grad_(False)
                base_digests[n] = digest_tensor(p)
        model.eval()
        summary["load_and_base_hash_s"] = time.monotonic() - start
        summary["adapter_parameter_count"] = {
            m: sum(
                p.numel()
                for n, p in model.named_parameters()
                if "lora_" in n and f".{m}." in n
            )
            for m in MODES
        }
        baseline = []
        for mode in ["python", "js", None]:
            for i, t in enumerate(data["setup"]):
                baseline.append(
                    generation(
                        t, messages(t, mode=mode), None, f"baseline/{mode}/{i}", mode
                    )
                )
        floors = {
            m: sum(
                r["success"] for r in baseline if r["id"].startswith(f"baseline/{m}/")
            )
            for m in MODES
        }
        floors["default_python"] = sum(
            r["language"] == "python"
            for r in baseline
            if r["id"].startswith("baseline/None/")
        )
        summary["setup_floors"] = floors
        # Capture pristine teacher-forced logits on 16 baseline greedy completions pre-fit.
        parity_rows = baseline[:8] + baseline[16:24]
        initial_replay = {r["id"]: replay(r, bypass=True)[0] for r in parity_rows}
        if min(floors.values()) < 7:
            raise Stop(
                "INELIGIBLE", "unmodified setup language/competence floor failed"
            )
        fit_start = time.monotonic()
        fit_times = []
        for mode in MODES:
            model.set_adapter(mode)
            model.train()
            model.config.use_cache = False
            params = [p for p in model.parameters() if p.requires_grad]
            assert params and all(
                "lora_" in n for n, p in model.named_parameters() if p.requires_grad
            )
            optimizer = torch.optim.AdamW(params, lr=1e-4, weight_decay=0.01)
            rows = list(data["fit"])
            random.Random(0).shuffle(rows)
            for step in range(16):
                guard()
                if (
                    time.monotonic() - fit_start + (max(fit_times) if fit_times else 0)
                    > 595
                ):
                    raise Stop(
                        "INCOMPLETE",
                        "600-second combined fitting ceiling; no final checkpoints",
                    )
                batch = []
                for t in rows[step * 8 : (step + 1) * 8]:
                    prefix = tok.encode(
                        render(tok, messages(t)), add_special_tokens=False
                    )
                    target = tok.encode(
                        t["references"][mode] + tok.eos_token, add_special_tokens=False
                    )
                    batch.append((prefix + target, [-100] * len(prefix) + target))
                width = max(len(x[0]) for x in batch)
                assert width <= 256
                x = torch.tensor(
                    [a + [tok.pad_token_id] * (width - len(a)) for a, b in batch],
                    device="cuda",
                )
                y = torch.tensor(
                    [b + [-100] * (width - len(b)) for a, b in batch], device="cuda"
                )
                mask = torch.tensor(
                    [[1] * len(a) + [0] * (width - len(a)) for a, b in batch],
                    device="cuda",
                )
                torch.cuda.synchronize()
                begin = time.monotonic()
                optimizer.zero_grad(set_to_none=True)
                loss = model(
                    input_ids=x, attention_mask=mask, labels=y, use_cache=False
                ).loss
                assert torch.isfinite(loss)
                loss.backward()
                grads = [p.grad for p in params]
                assert all(g is not None and torch.isfinite(g).all() for g in grads)
                norm = sum(float(g.float().square().sum()) for g in grads) ** 0.5
                assert norm > 0
                assert all(
                    p.grad is None
                    for n, p in model.named_parameters()
                    if "lora_" not in n
                )
                optimizer.step()
                torch.cuda.synchronize()
                seconds = time.monotonic() - begin
                fit_times.append(seconds)
                log = dict(
                    mode=mode,
                    step=step,
                    loss=float(loss),
                    grad_norm=norm,
                    seconds=seconds,
                    examples=8,
                )
                training_log.append(log)
                journal("fit.jsonl", log)
                print(json.dumps(dict(fit=log)), flush=True)
                if len(fit_times) == 1:
                    fit_projection = seconds * 32 + 15
                    summary["fit_projection_s"] = fit_projection
                    if fit_projection > 600:
                        raise Stop(
                            "INELIGIBLE",
                            "measured first-step full fitting projection exceeds600s; pilot discarded",
                        )
                if time.monotonic() - fit_start > 600:
                    raise Stop(
                        "INCOMPLETE", "600-second combined fitting ceiling exceeded"
                    )
            optimizer.zero_grad(set_to_none=True)
            del optimizer, loss, x, y, mask
        summary["fit_seconds"] = time.monotonic() - fit_start
        model.eval()
        model.config.use_cache = True
        for mode in MODES:
            # PEFT writes named subfolders; move files to the registered per-mode paths.
            destination = ADAPTERS / mode
            model.save_pretrained(
                destination, selected_adapters=[mode], safe_serialization=True
            )
            nested = destination / mode
            if nested.exists():
                for p in nested.iterdir():
                    p.rename(destination / p.name)
                nested.rmdir()
        summary["adapter_files"] = {
            str(p.relative_to(ROOT)): dict(bytes=p.stat().st_size, sha256=sha(p))
            for p in sorted(ADAPTERS.rglob("*"))
            if p.is_file()
        }
        write(OUT / "adapter-manifest.json", summary["adapter_files"])
        summary["fit_and_save_seconds"] = time.monotonic() - fit_start
        if summary["fit_and_save_seconds"] > 600:
            raise Stop(
                "INCOMPLETE", "combined fit/save exceeded600s; adapters not qualified"
            )
        parity = []
        for r in parity_rows:
            off, tokens = replay(r)
            bypass, btokens = replay(r, bypass=True)
            on, _ = replay(r, mode="js")
            parity.append(
                dict(
                    id=r["id"],
                    initial_hash=initial_replay[r["id"]],
                    off_hash=off,
                    pristine_hash=bypass,
                    on_hash=on,
                    off_pristine_equal=off == bypass == initial_replay[r["id"]],
                    greedy_token_equal=tokens == r["token_ids"] == btokens,
                    on_effect=on != off,
                )
            )
        write(OUT / "parity.json", parity)
        summary["parity"] = dict(
            count=len(parity),
            logit_diffs=sum(not r["off_pristine_equal"] for r in parity),
            token_diffs=sum(not r["greedy_token_equal"] for r in parity),
            on_effects=sum(r["on_effect"] for r in parity),
        )
        # Mechanism setup: five-decision literal histories then three fresh prompts per mode.
        mechanism = []
        for mode in MODES:
            hist = []
            other = MODES[1 - MODES.index(mode)]
            schedule = [mode, mode, other, mode, None]
            for i, t in enumerate(data["setup"]):
                if i == 1:
                    hist += NEUTRAL
                selected = schedule[i] if i < 5 else mode
                r = generation(
                    t,
                    messages(t, hist if i < 5 else []),
                    selected,
                    f"mechanism/{mode}/{i}",
                    selected,
                )
                mechanism.append(r)
                if i < 5:
                    hist += [
                        dict(role="user", content=t["prompt"]),
                        dict(role="assistant", content=r["text"]),
                    ]
        # Measured worst full setup history; conservatively extend token latency to cap96.
        worst = max(
            r["seconds"] * 96 / max(1, r["output_tokens"]) for r in baseline + mechanism
        )
        remaining_calls = 272 - len(records)
        projection = time.monotonic() - start + 1.25 * remaining_calls * worst + 120
        summary["evaluation_preflight"] = dict(
            spent_s=time.monotonic() - start,
            worst_cap96_call_s=worst,
            remaining_calls=remaining_calls,
            projected_total_s=projection,
            formula="spent + 1.25*remaining_calls*worst(seconds*96/output_tokens) +120",
        )
        write(OUT / "preflight.json", summary)
        if projection > 3600:
            raise Stop(
                "INELIGIBLE",
                "measured worst setup trajectory cost projection exceeds3600s",
            )
        # Adapter and complete CPU freeze already recorded; no evaluations used above.
        for ep in data["episodes"]:
            a = ep["initial"]
            b = MODES[1 - MODES.index(a)]
            schedule = [a, a, b, a, None]
            mclear_history = None
            for arm in ["M", "T", "X"]:
                hist = []
                for i, stage in enumerate(STAGES):
                    if stage == "HOLD":
                        hist += NEUTRAL
                    t = ep["tasks"][i]
                    desired = schedule[i]
                    selected = (
                        desired
                        if arm == "M"
                        else MODES[1 - MODES.index(desired)]
                        if arm == "X" and desired
                        else None
                    )
                    msgs = messages(t, hist, desired if arm == "T" else None)
                    r = generation(
                        t, msgs, selected, f"episode/{ep['id']}/{arm}/{stage}", desired
                    )
                    if arm == "M" and stage == "CLEAR":
                        mclear_history = list(hist)
                    hist += [
                        dict(role="user", content=t["prompt"]),
                        dict(role="assistant", content=r["text"]),
                    ]
            generation(
                ep["tasks"][5],
                messages(ep["tasks"][5], NEUTRAL),
                a,
                f"cold/{ep['id']}",
                a,
            )
            t = ep["tasks"][4]
            generation(t, messages(t), None, f"fresh/{ep['id']}")
            generation(t, messages(t, mclear_history), None, f"replay/{ep['id']}")
        for t in data["sentinels"]:
            for mode in [None, t["mode"]]:
                # Same task-specific JSON output contract; adapter must not impose coding.
                msgs = [
                    dict(
                        role="system",
                        content="Follow the requested output format exactly.",
                    ),
                    dict(role="user", content=t["prompt"]),
                ]
                generation(t, msgs, mode, f"sentinel/{t['id']}/{mode}")
        assert len(records) == 272
        summary.update(analyze(records, summary["parity"]))
    except Stop as e:
        summary.update(status=e.status, reason=e.reason)
    except Exception as e:
        import traceback

        summary.update(
            status="INCOMPLETE", reason=repr(e), traceback=traceback.format_exc()
        )
        print(summary["traceback"], flush=True)
    finally:
        if model is not None:
            with model.disable_adapter():
                summary["trunk_tensor_hash_diffs"] = [
                    n
                    for n, p in model.named_parameters()
                    if n in base_digests and digest_tensor(p) != base_digests[n]
                ]
                summary["trunk_gradient_nonnull"] = [
                    n
                    for n, p in model.named_parameters()
                    if "lora_" not in n and p.grad is not None
                ]
            # Disable all carriers before releasing our reference to the model.
            model.base_model.disable_adapter_layers()
        summary["fit_steps"] = len(training_log)
        summary["calls"] = len(records)
        if "fit_seconds" not in summary and training_log:
            summary["partial_fit_step_seconds"] = sum(
                r["seconds"] for r in training_log
            )
        model = None
        if "trunk" in locals():
            del trunk
        gc.collect()
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
        summary["peak_allocated_bytes"] = torch.cuda.max_memory_allocated()
        summary["base_file_hash_diffs"] = [
            p for p, h in contract["frozen_files"].items() if sha(ROOT / p) != h
        ]
        summary["gpu_held_seconds"] = time.monotonic() - start
        if summary["gpu_held_seconds"] > 3600:
            summary.update(status="INCOMPLETE", reason="total3600s exceeded")
        summary["cleanup_completed"] = True
        write(OUT / "summary.json", summary)
        flag.unlink()
        print(json.dumps(summary), flush=True)


def analyze(records, parity):
    by = {r["id"]: r for r in records}
    active = {
        arm: [
            all(by[f"episode/{i}/{arm}/{s}"]["success"] for s in STAGES[:4])
            for i in range(12)
        ]
        for arm in ["M", "T", "X"]
    }
    counts = {a: sum(v) for a, v in active.items()}
    wins = sum(m and not x for m, x in zip(active["M"], active["X"]))
    losses = sum(x and not m for m, x in zip(active["M"], active["X"]))
    n = wins + losses
    p = sum(math.comb(n, k) for k in range(wins, n + 1)) / 2**n if n else 1.0
    harms = []
    for i in range(12):
        for stage in STAGES:
            m = by[f"episode/{i}/M/{stage}"]
            t = by[f"episode/{i}/T/{stage}"]
            if (
                t["semantics"]
                and not t["truncated"]
                and (not m["semantics"] or m["truncated"])
            ):
                harms.append(m["id"])
    for i in range(8):
        off = by[f"sentinel/sentinel_{i}/None"]
        on = by[f"sentinel/sentinel_{i}/{MODES[i % 2]}"]
        if off["semantics"] and not on["success"]:
            harms.append(on["id"])
    clear = []
    for i in range(12):
        m = by[f"episode/{i}/M/CLEAR"]
        f = by[f"fresh/{i}"]
        r = by[f"replay/{i}"]
        initial = MODES[i % 2]
        clear.append(
            dict(
                episode=i,
                success=m["semantics"]
                and not m["truncated"]
                and f["semantics"]
                and not f["truncated"]
                and m["language"] == f["language"],
                stale=m["language"] == initial and f["language"] != initial,
                replay_equal=m["token_ids"] == r["token_ids"],
            )
        )
    cold = sum(by[f"cold/{i}"]["success"] for i in range(12))
    timing = {
        a: sum(
            r["seconds"]
            for r in records
            if re.match(r"episode/\d+/" + a + "/", r["id"])
        )
        for a in ["M", "T", "X"]
    }
    carriers = {
        a: sum(
            r["rule_carrier_positions"]
            for r in records
            if re.match(r"episode/\d+/" + a + "/", r["id"])
        )
        for a in ["M", "T", "X"]
    }
    savings = 1 - carriers["M"] / carriers["T"] if carriers["T"] else 0
    bars = dict(
        full_records=len(records) == 272,
        mechanism=counts["M"] >= 10
        and cold >= 10
        and counts["M"] - counts["X"] >= 3
        and p <= 0.05,
        competence=not harms and counts["M"] >= counts["T"],
        clear=sum(x["success"] for x in clear) >= 11
        and not any(x["stale"] or not x["replay_equal"] for x in clear)
        and parity["logit_diffs"] == parity["token_diffs"] == 0
        and parity["on_effects"] > 0,
        shipping=counts["M"] > counts["T"]
        or (
            counts["M"] >= counts["T"]
            and savings >= 0.5
            and timing["M"] <= 1.1 * timing["T"]
        ),
    )
    seconds = sorted(r["seconds"] for r in records)
    return dict(
        status="GO" if all(bars.values()) else "NO-GO",
        reason="all five registered conditions"
        if all(bars.values())
        else "registered conditions failed",
        bars=bars,
        all_active=counts,
        cold=cold,
        paired_M_X=dict(wins=wins, losses=losses, p=p),
        paired_harms=harms,
        clear_records=clear,
        trajectory_seconds=timing,
        rule_carrier_positions=carriers,
        rule_carrier_savings=savings,
        total_input_tokens=sum(r["input_tokens"] for r in records),
        total_output_tokens=sum(r["output_tokens"] for r in records),
        latency_p50=statistics.median(seconds),
        latency_p95=seconds[math.ceil(0.95 * len(seconds)) - 1],
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=["prepare", "run"])
    args = p.parse_args()
    if args.command == "prepare":
        prepare()
    else:
        run()


if __name__ == "__main__":
    main()
