#!/usr/bin/env python3
"""Disclosed check43: frozen SUM/PRODUCT router SET, bounded AST execution."""

# ruff: noqa: E501
from __future__ import annotations

import argparse
import ast
import contextlib
import fcntl
import hashlib
import json
import math
import os
import random
import subprocess
import time
from pathlib import Path

import focus_check40 as base
import focus_check40c as verified

ROOT = base.ROOT
OUT = ROOT / "results/quick-checks/check43"
LIMIT = 5400
ARMS = (
    "plus",
    "minus",
    "shuffle-plus",
    "shuffle-minus",
    "OFF",
    "text-SUM",
    "text-PRODUCT",
)
OPS = ("SUM", "PRODUCT")
NEUTRAL = "\nReturn only the complete function."
JS_PARSE = """const m={exports:{}};new Function('exports','module',process.binding('natives')['internal/deps/acorn/acorn/dist/acorn'])(m.exports,m);process.stdout.write(JSON.stringify(m.exports.parse(require('fs').readFileSync(0,'utf8'),{ecmaVersion:2022})));"""
CLARIFICATIONS = """
Implementation choices frozen before outcomes: source section 4 items 1–11 below govern.
Prompts name the language, function, list argument and an explicit loop; the only
text-arm addition is the SUM/PRODUCT sentence before the common neutral suffix.
The four profile tokens are the final four user-content tokens, excluding chat
termination and assistant header; their token IDs must match for all 32 donors.
Profiles include all donors, without success filtering, averaged equally per example.
Grid runs all three doses. Select the smallest qualifying dose, freeze it, then
run its OFF/shuffled/text setup controls (40 more generations). No selection on controls.
The first slice-family setup text-SUM generation is the pilot and is reused in
its setup-control cell: no extra scored generation or outcome-dependent replacement.
Conservative cost uses its seconds/token including prefill and dispatch audit,
96 tokens for every remaining request, plus measured profiling costs, 25% reserve.
The historical budget arithmetic is (37632/15+314+600)*1.25/3600 = 1.1885 h.
OFF paired success means its ONE program passes both distinct operation checks;
swapped pairs score minus as SUM and plus as PRODUCT. Shuffled pairs score the
corresponding signs. Each prompt is one unit; one-sided binomial discordance tails
and Holm correction across three comparisons; Wilson 95% intervals are descriptive.
Collateral uses seed95064 after 10000 discarded PRNG draws, with distinct names/prompts.
Collateral tasks are disjoint explicit SUM/PRODUCT reductions balanced by operation,
language and list family; no newly failed task under either sign versus OFF.
JS shadowing/redeclarations and assignments to const are rejected.
Bounded interpreter: entire function body statically allowlisted, including dead
branches; integer arithmetic, variables, slices/indexing, len/range/min/max,
assignments, if, for/while and returns. No imports, arbitrary calls, mutation,
I/O, recursion, comprehensions, nested functions or unsupported constructs. Require
an executed loop on at least one test. 2000 instructions per input, integers within
2**53-1, arrays/ranges <=64, source <=12000 chars. Python AST and existing Node
syntax parser retained; Node's bundled Acorn supplies JS AST without executing output.
Test cases cover every length 0–8 and negative/zero/repeated operands; all execution
results saved. Unsupported, runtime errors, missing return, no executed loop and
truncation are malformed failures; valid wrong arithmetic is a semantic failure.
Fresh KV is empty (hash recorded); non-text arms must have identical input hashes.
Dispatch pre-hooks verify the actual expert consumer indices/weights against the
router tuple and record per-layer changed top-8 sets and mixture weights, separately
for prefill/decode. OFF full greedy output is compared with hooks removed on the
pilot input; this extra instrumentation generation is explicitly budgeted separately
(up to 96 tokens), excluded from the 392 scored matrix and saved in its own record.
All model parameters require_grad=False, inference only. Unhooked OFF replay is
instrumentation, not a replacement. Per-token reserve uses the unchanged consumer's
deadline shifted 30 seconds earlier, giving at least 30 seconds to save/return.
Freeze in two commits: CPU recipe/banks/checker first; profiles, selected dose,
setup records, actual biases and final binding committed before ANY final generation.
Invalid instrumentation -> INVALID; cost/missing required work -> INCOMPLETE;
donor/final text competence or damaged controls -> INELIGIBLE; no safe setup ->
FAIL/NO SAFE SET. Otherwise every PASS gate is conjunctive; missed gate -> FAIL.
No fitting/training, benchmark data, check40/41 banks, sealed inputs, signals or push.
"""


def write(name, value):
    base.write_json(OUT / name, value)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


class Unsupported(ValueError):
    pass


class Returned(Exception):
    def __init__(self, value):
        self.value = value


def require(ok, why="unsupported AST"):
    if not ok:
        raise Unsupported(why)


# Translate both parsers to the same small IR; every branch is visited before use.
def py_expr(n):
    if isinstance(n, ast.Constant):
        require(type(n.value) in (int, bool))
        return ("const", n.value)
    if isinstance(n, ast.Name):
        return ("var", n.id)
    if isinstance(n, ast.BinOp):
        op = {
            ast.Add: "+",
            ast.Sub: "-",
            ast.Mult: "*",
            ast.Mod: "%",
            ast.FloorDiv: "//",
        }
        require(type(n.op) in op)
        return ("bin", op[type(n.op)], py_expr(n.left), py_expr(n.right))
    if isinstance(n, ast.UnaryOp):
        op = {ast.USub: "-", ast.UAdd: "+", ast.Not: "!"}
        require(type(n.op) in op)
        return ("unary", op[type(n.op)], py_expr(n.operand))
    if isinstance(n, ast.Compare):
        op = {
            ast.Lt: "<",
            ast.LtE: "<=",
            ast.Gt: ">",
            ast.GtE: ">=",
            ast.Eq: "==",
            ast.NotEq: "!=",
        }
        require(all(type(o) in op for o in n.ops))
        parts = [n.left] + n.comparators
        return (
            "and",
            [
                ("bin", op[type(o)], py_expr(parts[i]), py_expr(parts[i + 1]))
                for i, o in enumerate(n.ops)
            ],
        )
    if isinstance(n, ast.BoolOp):
        return (
            "and" if isinstance(n.op, ast.And) else "or",
            [py_expr(x) for x in n.values],
        )
    if isinstance(n, ast.Subscript):
        if isinstance(n.slice, ast.Slice):
            return (
                "slice",
                py_expr(n.value),
                *[
                    py_expr(x) if x else ("const", None)
                    for x in (n.slice.lower, n.slice.upper, n.slice.step)
                ],
            )
        return ("index", py_expr(n.value), py_expr(n.slice), "Python")
    if isinstance(n, ast.Call):
        require(
            isinstance(n.func, ast.Name)
            and n.func.id in ("len", "range", "min", "max")
            and not n.keywords
        )
        return ("call", n.func.id, [py_expr(x) for x in n.args])
    raise Unsupported(type(n).__name__)


def py_block(nodes):
    out = []
    for n in nodes:
        if isinstance(n, ast.Assign):
            require(len(n.targets) == 1 and isinstance(n.targets[0], ast.Name))
            out.append(("set", n.targets[0].id, py_expr(n.value)))
        elif isinstance(n, ast.AugAssign):
            require(isinstance(n.target, ast.Name))
            out.append(
                (
                    "set",
                    n.target.id,
                    py_expr(ast.BinOp(left=n.target, op=n.op, right=n.value)),
                )
            )
        elif isinstance(n, ast.Return):
            require(n.value is not None)
            out.append(("return", py_expr(n.value)))
        elif isinstance(n, ast.For):
            require(isinstance(n.target, ast.Name) and not n.orelse)
            out.append(("for", n.target.id, py_expr(n.iter), py_block(n.body)))
        elif isinstance(n, ast.While):
            require(not n.orelse)
            out.append(("while", py_expr(n.test), py_block(n.body)))
        elif isinstance(n, ast.If):
            out.append(("if", py_expr(n.test), py_block(n.body), py_block(n.orelse)))
        else:
            raise Unsupported(type(n).__name__)
    return out


def js_expr(n):
    t = n["type"]
    if t == "Literal":
        require(type(n.get("value")) in (int, bool))
        return ("const", n["value"])
    if t == "Identifier":
        return ("var", n["name"])
    if t == "BinaryExpression":
        op = {"===": "==", "!==": "!="}.get(n["operator"], n["operator"])
        require(op in ("+", "-", "*", "%", "<", "<=", ">", ">=", "==", "!="))
        return (
            "bin",
            "js%" if op == "%" else op,
            js_expr(n["left"]),
            js_expr(n["right"]),
        )
    if t == "LogicalExpression":
        require(n["operator"] in ("&&", "||"))
        return (
            "and" if n["operator"] == "&&" else "or",
            [js_expr(n["left"]), js_expr(n["right"])],
        )
    if t == "UnaryExpression":
        require(n["operator"] in ("-", "+", "!"))
        return ("unary", n["operator"], js_expr(n["argument"]))
    if t == "MemberExpression":
        if n["computed"]:
            return ("index", js_expr(n["object"]), js_expr(n["property"]), "JavaScript")
        require(n["property"]["name"] == "length")
        return ("call", "len", [js_expr(n["object"])])
    if t == "CallExpression":
        c = n["callee"]
        require(c["type"] == "MemberExpression" and not c["computed"])
        if c["property"]["name"] == "slice":
            require(len(n["arguments"]) <= 2)
            args = [js_expr(x) for x in n["arguments"]]
            return (
                "slice",
                js_expr(c["object"]),
                *(args + [("const", None)] * (3 - len(args))),
            )
        require(
            c["object"]["type"] == "Identifier"
            and c["object"]["name"] == "Math"
            and c["property"]["name"] in ("min", "max")
        )
        return ("call", c["property"]["name"], [js_expr(x) for x in n["arguments"]])
    raise Unsupported(t)


def js_block(nodes):
    out = []
    for n in nodes:
        t = n["type"]
        if t == "BlockStatement":
            out.extend(js_block(n["body"]))
        elif t == "VariableDeclaration":
            for d in n["declarations"]:
                require(d["id"]["type"] == "Identifier" and d["init"] is not None)
                out.append(("set", d["id"]["name"], js_expr(d["init"])))
        elif t == "ExpressionStatement":
            x = n["expression"]
            if x["type"] == "UpdateExpression":
                require(
                    x["argument"]["type"] == "Identifier"
                    and x["operator"] in ("++", "--")
                )
                name = x["argument"]["name"]
                out.append(
                    (
                        "set",
                        name,
                        (
                            "bin",
                            "+" if x["operator"] == "++" else "-",
                            ("var", name),
                            ("const", 1),
                        ),
                    )
                )
            else:
                require(
                    x["type"] == "AssignmentExpression"
                    and x["left"]["type"] == "Identifier"
                    and x["operator"] in ("=", "+=", "-=", "*=")
                )
                name, value = x["left"]["name"], js_expr(x["right"])
                out.append(
                    (
                        "set",
                        name,
                        value
                        if x["operator"] == "="
                        else ("bin", x["operator"][0], ("var", name), value),
                    )
                )
        elif t == "ReturnStatement":
            require(n["argument"] is not None)
            out.append(("return", js_expr(n["argument"])))
        elif t == "ForOfStatement":
            left = n["left"]
            require(
                not n["await"]
                and left["type"] == "VariableDeclaration"
                and len(left["declarations"]) == 1
            )
            d = left["declarations"][0]
            require(d["id"]["type"] == "Identifier" and d["init"] is None)
            out.append(
                ("for", d["id"]["name"], js_expr(n["right"]), js_block([n["body"]]))
            )
        elif t == "ForStatement":
            require(
                n["init"] is not None
                and n["test"] is not None
                and n["update"] is not None
            )
            init = (
                n["init"]
                if n["init"]["type"] == "VariableDeclaration"
                else {"type": "ExpressionStatement", "expression": n["init"]}
            )
            out.extend(js_block([init]))
            out.append(
                (
                    "while",
                    js_expr(n["test"]),
                    js_block(
                        [
                            n["body"],
                            {"type": "ExpressionStatement", "expression": n["update"]},
                        ]
                    ),
                )
            )
        elif t == "WhileStatement":
            out.append(("while", js_expr(n["test"]), js_block([n["body"]])))
        elif t == "IfStatement":
            out.append(
                (
                    "if",
                    js_expr(n["test"]),
                    js_block([n["consequent"]]),
                    js_block([n["alternate"]]) if n["alternate"] else [],
                )
            )
        else:
            raise Unsupported(t)
    return out


def parse(code, task):
    require(len(code) <= 12000)
    if task["language"] == "Python":
        tree = ast.parse(code)
        require(len(tree.body) == 1 and isinstance(tree.body[0], ast.FunctionDef))
        f = tree.body[0]
        require(
            f.name == task["name"]
            and not f.decorator_list
            and f.returns is None
            and not f.type_comment
        )
        a = f.args
        require(
            len(a.args) == 1
            and not a.posonlyargs
            and not a.kwonlyargs
            and not a.defaults
            and not a.vararg
            and not a.kwarg
            and a.args[0].annotation is None
        )
        return a.args[0].arg, py_block(f.body)
    proc = subprocess.run(
        ["node", "--check", "-"], input=code, text=True, capture_output=True
    )
    require(proc.returncode == 0, "Node syntax")
    proc = subprocess.run(
        ["node", "-e", JS_PARSE], input=code, text=True, capture_output=True
    )
    require(proc.returncode == 0, "Acorn parse")
    tree = json.loads(proc.stdout)
    require(len(tree["body"]) == 1)
    f = tree["body"][0]
    require(
        f["type"] == "FunctionDeclaration"
        and f["id"]["name"] == task["name"]
        and not f["generator"]
        and not f["async"]
    )
    require(len(f["params"]) == 1 and f["params"][0]["type"] == "Identifier")
    declarations = {f["params"][0]["name"]}
    constants = set()
    assignments = []

    def visit(node):
        if isinstance(node, list):
            for item in node:
                visit(item)
        elif isinstance(node, dict):
            if node.get("type") == "VariableDeclaration":
                for d in node["declarations"]:
                    require(d["id"]["type"] == "Identifier")
                    name = d["id"]["name"]
                    require(name not in declarations, "shadowed/redeclared variable")
                    declarations.add(name)
                    if node["kind"] == "const":
                        constants.add(name)
            if node.get("type") in ("AssignmentExpression", "UpdateExpression"):
                target = node.get("left", node.get("argument"))
                require(target["type"] == "Identifier")
                assignments.append(target["name"])
            for value in node.values():
                visit(value)

    visit(f["body"])
    require(
        all(name in declarations and name not in constants for name in assignments),
        "undeclared/const assignment",
    )

    def scope(node, visible):
        if node is None:
            return
        if isinstance(node, list):
            for item in node:
                scope(item, visible)
            return
        if not isinstance(node, dict):
            return
        kind = node.get("type")
        if kind == "Identifier":
            require(node["name"] in visible, "out-of-scope variable")
        elif kind == "MemberExpression":
            scope(node["object"], visible)
            if node["computed"]:
                scope(node["property"], visible)
        elif kind == "BlockStatement":
            scope(node["body"], set(visible))
        elif kind == "VariableDeclaration":
            for d in node["declarations"]:
                scope(d["init"], visible)
                visible.add(d["id"]["name"])
        elif kind == "ForStatement":
            inner = set(visible)
            scope(node["init"], inner)
            scope(node["test"], inner)
            scope(node["update"], inner)
            scope(node["body"], inner)
        elif kind == "ForOfStatement":
            inner = set(visible)
            scope(node["right"], visible)
            scope(node["left"], inner)
            scope(node["body"], inner)
        else:
            for value in node.values():
                scope(value, visible)

    scope(f["body"], {f["params"][0]["name"], "Math"})
    return f["params"][0]["name"], js_block(f["body"]["body"])


class Interpreter:
    def __init__(self, arg, values):
        self.env = {arg: list(values)}
        self.steps = self.loops = 0

    def tick(self):
        self.steps += 1
        require(self.steps <= 2000, "instruction budget")

    def expr(self, x):
        self.tick()
        t = x[0]
        if t == "const":
            v = x[1]
        elif t == "var":
            v = self.env[x[1]]
        elif t == "bin":
            a, b = self.expr(x[2]), self.expr(x[3])
            require(type(a) is int and type(b) is int)
            op = x[1]
            if op == "+":
                v = a + b
            elif op == "-":
                v = a - b
            elif op == "*":
                v = a * b
            elif op == "%":
                v = a % b
            elif op == "js%":
                v = a - math.trunc(a / b) * b
            elif op == "//":
                v = a // b
            elif op == "<":
                v = a < b
            elif op == "<=":
                v = a <= b
            elif op == ">":
                v = a > b
            elif op == ">=":
                v = a >= b
            elif op == "==":
                v = a == b
            elif op == "!=":
                v = a != b
            else:
                raise Unsupported(op)
        elif t == "unary":
            a = self.expr(x[2])
            require(type(a) in (int, bool))
            v = -a if x[1] == "-" else +a if x[1] == "+" else not a
        elif t in ("and", "or"):
            v = True if t == "and" else False
            for y in x[1]:
                v = self.expr(y)
                if (t == "and" and not v) or (t == "or" and v):
                    break
        elif t == "index":
            a, i = self.expr(x[1]), self.expr(x[2])
            require(isinstance(a, (list, range)) and type(i) is int)
            require(x[3] != "JavaScript" or i >= 0)
            v = a[i]
        elif t == "slice":
            a = self.expr(x[1])
            require(isinstance(a, (list, range)))
            idx = [self.expr(z) for z in x[2:]]
            require(all(z is None or type(z) is int for z in idx))
            v = a[slice(*idx)]
        elif t == "call":
            args = [self.expr(z) for z in x[2]]
            if x[1] == "len":
                require(len(args) == 1 and isinstance(args[0], (list, range)))
                v = len(args[0])
            elif x[1] == "range":
                require(1 <= len(args) <= 3 and all(type(z) is int for z in args))
                v = range(*args)
            else:
                require(len(args) >= 2 and all(type(z) is int for z in args))
                v = (min if x[1] == "min" else max)(args)
        else:
            raise Unsupported(t)
        require(v is None or type(v) in (int, bool) or isinstance(v, (list, range)))
        if type(v) is int:
            require(abs(v) <= 2**53 - 1, "integer bound")
        if isinstance(v, (list, range)):
            require(len(v) <= 64, "array bound")
        return v

    def block(self, nodes):
        for n in nodes:
            self.tick()
            if n[0] == "set":
                self.env[n[1]] = self.expr(n[2])
            elif n[0] == "return":
                raise Returned(self.expr(n[1]))
            elif n[0] == "if":
                self.block(n[2] if self.expr(n[1]) else n[3])
            elif n[0] == "for":
                values = self.expr(n[2])
                require(isinstance(values, (list, range)))
                for v in values:
                    self.tick()
                    self.loops += 1
                    self.env[n[1]] = v
                    self.block(n[3])
            elif n[0] == "while":
                while self.expr(n[1]):
                    self.tick()
                    self.loops += 1
                    self.block(n[2])
            else:
                raise Unsupported(n[0])


def selected(task, values):
    k, j = task["lo"], task["hi"]
    return {
        "whole": values,
        "prefix": values[:j],
        "suffix": values[k:],
        "slice": values[k:j],
    }[task["family"]]


def score(text, task, truncated=False):
    code, error = base.extract_code(text)
    result = dict(code=code, malformed=True, SUM=False, PRODUCT=False, executions=[])
    try:
        require(not error and bool(code) and not truncated, "fence/empty/truncated")
        arg, ir = parse(code, task)
        loop_count = 0
        for values in task["inputs"]:
            vm = Interpreter(arg, values)
            output = None
            try:
                vm.block(ir)
            except Returned as ret:
                output = ret.value
            require(type(output) is int, "no integer return")
            want = selected(task, values)
            expected = dict(SUM=sum(want), PRODUCT=math.prod(want))
            result["executions"].append(
                dict(
                    input=values,
                    output=output,
                    expected=expected,
                    steps=vm.steps,
                    loops=vm.loops,
                )
            )
            loop_count += vm.loops
        require(loop_count > 0, "no executed loop")
        result.update(
            malformed=False,
            **{
                op: all(r["output"] == r["expected"][op] for r in result["executions"])
                for op in OPS
            },
        )
    except (
        Unsupported,
        SyntaxError,
        ValueError,
        KeyError,
        TypeError,
        IndexError,
        ZeroDivisionError,
        OverflowError,
        RecursionError,
    ) as exc:
        result["error"] = str(exc)[:300]
    return result


def banks():
    result = {}
    split_specs = [
        ("donor", 95061, 16, ("Python",)),
        ("setup", 95062, 8, ("Python",)),
        ("final-a", 95063, 8, base.LANGS),
        ("final-b", 95064, 8, base.LANGS),
        ("collateral", 95064, 8, base.LANGS),
    ]
    verbs = ["Write", "Implement", "Provide", "Define"]
    for split, seed, n, langs in split_specs:
        rng = random.Random(seed)
        if split == "collateral":
            for _ in range(10000):
                rng.random()
        result[split] = []
        for lang in langs:
            for i in range(n):
                family = ("whole", "prefix", "suffix", "slice")[i % 4]
                lo, hi = rng.randint(1, 2), rng.randint(4, 6)
                name = f"fold_{split.replace('-', '_')}_{rng.randrange(100000, 999999)}"
                arg = f"items_{rng.randrange(100, 999)}"
                selection = {
                    "whole": "all elements",
                    "prefix": f"the first {hi} elements",
                    "suffix": f"elements from zero-based index {lo} to the end",
                    "slice": f"elements at zero-based indices {lo} (inclusive) through {hi} (exclusive)",
                }[family]
                prompt = f"{verbs[i % 4]} one {lang} function named {name} with one integer-list parameter {arg}. Return a scalar reduction of {selection}, preserving order. Use an explicit loop and an accumulator; no built-in reduction, imports, I/O, or input mutation. Lists have length 0 to 8 and bounded integers. Out-of-range slice endpoints are clipped. Keep the complete function within 96 tokens."
                inputs = [[], [0], [2], [-3], [1, 1, 1], [0, 2, -3], [-2, -2, 3]]
                inputs += [
                    [rng.randint(-3, 3) for _ in range(length)]
                    for length in range(9)
                    for _ in range(3)
                ]
                inputs += [[2] * length for length in range(9)]
                task = dict(
                    id=f"{split}-{lang}-{i}",
                    name=name,
                    arg=arg,
                    family=family,
                    language=lang,
                    seed=seed,
                    lo=lo,
                    hi=hi,
                    prompt=prompt,
                    inputs=inputs,
                )
                if split == "collateral":
                    task["operation"] = OPS[(i // 4) % 2]
                assert any(
                    sum(selected(task, v)) != math.prod(selected(task, v))
                    for v in inputs
                )
                result[split].append(task)
    result["final"] = result.pop("final-a") + result.pop("final-b")
    all_tasks = [t for ts in result.values() for t in ts]
    assert len({t["prompt"] for t in all_tasks}) == len(all_tasks) == 72
    return result


def messages(task, op=None):
    cue = (
        ""
        if op is None
        else f" Compute the {op} of the selected elements; return {0 if op == 'SUM' else 1} for an empty selection."
    )
    return [
        dict(
            role="system",
            content="Return only the requested complete function. No examples or explanation.",
        ),
        dict(role="user", content=task["prompt"] + cue + NEUTRAL),
    ]


def fixture_code(task, op, indexed=False):
    a = task["arg"]
    name = task["name"]
    lo, hi = task["lo"], task["hi"]
    start = str(lo) if task["family"] in ("suffix", "slice") else "0"
    end = str(hi) if task["family"] in ("prefix", "slice") else None
    symbol, identity = ("+", 0) if op == "SUM" else ("*", 1)
    if task["language"] == "Python":
        seq = a if task["family"] == "whole" else f"{a}[{start}:{end or ''}]"
        if indexed:
            return f"def {name}({a}):\n    r = {identity}\n    for i in range({start}, {f'min(len({a}), {end})' if end else f'len({a})'}):\n        r {symbol}= {a}[i]\n    return r"
        return f"def {name}({a}):\n    r = {identity}\n    for x in {seq}:\n        r {symbol}= x\n    return r"
    seq = (
        a
        if task["family"] == "whole"
        else f"{a}.slice({start}{', ' + end if end else ''})"
    )
    if indexed:
        stop = f"Math.min({a}.length, {end})" if end else f"{a}.length"
        return f"function {name}({a}) {{ let r={identity}; for(let i={start}; i<{stop}; i++) {{ r {symbol}= {a}[i]; }} return r; }}"
    return f"function {name}({a}) {{ let r={identity}; for(const x of {seq}) {{ r {symbol}= x; }} return r; }}"


def exact_test(a, b):
    win = sum(x and not y for x, y in zip(a, b, strict=True))
    lose = sum(y and not x for x, y in zip(a, b, strict=True))
    n = win + lose
    return dict(
        wins=win,
        losses=lose,
        p=sum(math.comb(n, k) for k in range(win, n + 1)) / 2**n if n else 1.0,
    )


def wilson(k, n):
    z = 1.959963984540054
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [c - h, c + h]


def final_summary(rows, bank):
    rs = {(r["task_id"], r["arm"]): r["score"] for r in rows if r["phase"] == "final"}
    require(len(rs) == 224, "missing final work")
    vectors = {k: [] for k in ("correct", "shuffled", "swapped", "OFF")}
    text = {f"{lang}-{op}": 0 for lang in base.LANGS for op in OPS}
    valid = {arm: 0 for arm in ARMS}
    new_bad = {arm: 0 for arm in ("plus", "minus")}
    for task in bank["final"]:
        r = {a: rs[task["id"], a] for a in ARMS}
        vectors["correct"].append(r["plus"]["SUM"] and r["minus"]["PRODUCT"])
        vectors["shuffled"].append(
            r["shuffle-plus"]["SUM"] and r["shuffle-minus"]["PRODUCT"]
        )
        vectors["swapped"].append(r["minus"]["SUM"] and r["plus"]["PRODUCT"])
        vectors["OFF"].append(r["OFF"]["SUM"] and r["OFF"]["PRODUCT"])
        for op in OPS:
            text[f"{task['language']}-{op}"] += int(r[f"text-{op}"][op])
        for arm in ARMS:
            valid[arm] += int(not r[arm]["malformed"])
        for arm in new_bad:
            new_bad[arm] += int(r[arm]["malformed"] and not r["OFF"]["malformed"])
    tests = {
        k: exact_test(vectors["correct"], vectors[k])
        for k in ("shuffled", "swapped", "OFF")
    }
    running = 0.0
    for i, (k, v) in enumerate(sorted(tests.items(), key=lambda kv: kv[1]["p"])):
        running = max(running, min(1.0, (3 - i) * v["p"]))
        tests[k]["holm_p"] = running
    counts = {k: sum(v) for k, v in vectors.items()}
    cells = {}
    languages = {}
    for lang in base.LANGS:
        languages[lang] = sum(
            v
            for t, v in zip(bank["final"], vectors["correct"], strict=True)
            if t["language"] == lang
        )
        for seed in (95063, 95064):
            cells[f"{seed}-{lang}"] = sum(
                v
                for t, v in zip(bank["final"], vectors["correct"], strict=True)
                if t["language"] == lang and t["seed"] == seed
            )
    cr = {
        (r["task_id"], r["arm"]): r["score"] for r in rows if r["phase"] == "collateral"
    }
    require(len(cr) == 48, "missing collateral work")
    collateral = {
        a: sum(
            not cr[t["id"], a][t["operation"]] and cr[t["id"], "OFF"][t["operation"]]
            for t in bank["collateral"]
        )
        for a in ("plus", "minus")
    }
    eligible = (
        min(text.values()) >= 15
        and min(valid[a] for a in ("OFF", "shuffle-plus", "shuffle-minus")) >= 30
    )
    gates = dict(
        paired=counts["correct"] >= 24,
        language=min(languages.values()) >= 12,
        cells=min(cells.values()) >= 5,
        malformed=max(new_bad.values()) <= 1,
        advantage=all(counts["correct"] - counts[k] >= 8 for k in tests),
        statistics=all(v["holm_p"] <= 0.05 for v in tests.values()),
        collateral=max(collateral.values()) == 0,
    )
    return dict(
        reading="INELIGIBLE"
        if not eligible
        else "PASS"
        if all(gates.values())
        else "FAIL",
        counts=counts,
        intervals={k: wilson(v, 32) for k, v in counts.items()},
        cells=cells,
        languages=languages,
        text=text,
        valid=valid,
        newly_malformed=new_bad,
        collateral_new_failures=collateral,
        tests=tests,
        gates=gates,
        eligible=eligible,
    )


def cpu_tests(bank):
    checks = []
    for lang in base.LANGS:
        for family in ("whole", "prefix", "suffix", "slice"):
            task = next(
                t
                for t in bank["final"]
                if t["language"] == lang and t["family"] == family
            )
            for op in OPS:
                for indexed in (False, True):
                    code = fixture_code(task, op, indexed)
                    r = score(code, task)
                    assert r[op] and not r["malformed"], (code, r)
                    # Native execution is only this hand-authored fixture, never model output.
                    if lang == "Python":
                        env = {}
                        exec(compile(code, "<hand-written fixture>", "exec"), env)
                        native = [env[task["name"]](list(v)) for v in task["inputs"]]
                    else:
                        source = (
                            code
                            + "\nconsole.log(JSON.stringify("
                            + json.dumps(task["inputs"])
                            + ".map(x=>"
                            + task["name"]
                            + "(x))));"
                        )
                        native = json.loads(
                            subprocess.check_output(["node", "-e", source], text=True)
                        )
                    assert native == [x["output"] for x in r["executions"]]
                    checks.append(
                        dict(
                            language=lang,
                            family=family,
                            operation=op,
                            indexed=indexed,
                            inputs=len(native),
                        )
                    )
            good = fixture_code(task, "SUM")
            assert score(good, task, True)["malformed"]
            assert score(good + "\n" + good, task)["malformed"]
            bad = (
                f"def {task['name']}(x):\n    while True:\n        x = x\n    return 0"
                if lang == "Python"
                else f"function {task['name']}(x) {{while(true){{x=x;}} return 0;}}"
            )
            assert score(bad, task)["malformed"]
            bad = (
                f"def {task['name']}(x):\n    if False:\n        print(x)\n    return 0"
                if lang == "Python"
                else f"function {task['name']}(x) {{if(false){{console.log(x);}} return 0;}}"
            )
            assert score(bad, task)["malformed"]
            bad = (
                f"def {task['name']}(x):\n    x[0]=1\n    return 0"
                if lang == "Python"
                else f"function {task['name']}(x) {{x[0]=1; return 0;}}"
            )
            assert score(bad, task)["malformed"]
    task = next(t for t in bank["final"] if t["language"] == "JavaScript")
    for body in (
        "let r=0; {let z=1;} for(const x of a){r+=x;} return r+z;",
        "const r=0; for(const x of a){r+=x;} return r;",
        "let r=0; for(const x of a){let r=1;} return r;",
    ):
        assert score("function " + task["name"] + "(a){" + body + "}", task)[
            "malformed"
        ]
    assert exact_test([True] * 8, [False] * 8)["p"] == 1 / 256
    assert exact_test([True] * 8, [True] * 8)["p"] == 1
    # End-to-end reading fixtures exercise exact consumer with all required rows.
    rows = []
    for t in bank["final"]:
        for a in ARMS:
            op = "PRODUCT" if a in ("minus", "text-PRODUCT") else "SUM"
            rows.append(
                dict(
                    task_id=t["id"],
                    phase="final",
                    arm=a,
                    score=dict(
                        SUM=op == "SUM", PRODUCT=op == "PRODUCT", malformed=False
                    ),
                )
            )
    for t in bank["collateral"]:
        for a in ("OFF", "plus", "minus"):
            rows.append(
                dict(
                    task_id=t["id"],
                    phase="collateral",
                    arm=a,
                    score={t["operation"]: True},
                )
            )
    assert final_summary(rows, bank)["reading"] == "PASS"
    for r in rows:
        if r["phase"] == "final" and r["arm"] == "minus":
            r["score"].update(SUM=True, PRODUCT=False)
    assert final_summary(rows, bank)["reading"] == "FAIL"
    return dict(
        handwritten_native_parity=checks,
        rejection_tests=True,
        reading_tests=True,
        router_consumer=cpu_router_test(),
    )


def cpu_router_test():
    import torch
    from transformers import Qwen3MoeConfig, Qwen3MoeForCausalLM

    torch.set_num_threads(2)
    torch.manual_seed(95061)
    config = Qwen3MoeConfig(
        vocab_size=64,
        hidden_size=16,
        intermediate_size=32,
        moe_intermediate_size=8,
        num_hidden_layers=2,
        num_attention_heads=2,
        num_key_value_heads=1,
        head_dim=8,
        num_experts=4,
        num_experts_per_tok=2,
    )
    engine = base.Engine.__new__(base.Engine)
    engine.model = Qwen3MoeForCausalLM(config).eval()
    engine.torch, engine.device = torch, torch.device("cpu")
    engine.deadline, engine.eos = time.monotonic() + 120, set()

    class Tokenizer:
        def apply_chat_template(self, *args, **kwargs):
            return [1, 2, 3]

        def decode(self, ids, **kwargs):
            return str(ids)

    engine.tokenizer = Tokenizer()
    engine.hooks = base.RouterHooks(
        [layer.mlp.gate for layer in engine.model.model.layers]
    )
    audit = DispatchAudit(engine)
    messages_ = [dict(role="user", content="fixture")]
    audit.reset()
    off, _ = engine.generate(messages_, cap=4)
    off_stats = audit.finish()
    assert all(
        v["changed_route_tokens"] == 0 and v["changed_weight_tokens"] == 0
        for v in off_stats.values()
    )
    bias = torch.tensor([[0.0, 0.0, 0.0, 10.0]] * 2)
    audit.reset()
    engine.generate(messages_, bias=bias, cap=4)
    on_stats = audit.finish()
    assert sum(v["changed_route_tokens"] for v in on_stats.values()) > 0
    assert all(v["changed_weight_tokens"] > 0 for v in on_stats.values())
    audit.close()
    engine.hooks.close()
    raw, _ = engine.generate(messages_, cap=4)
    assert raw["generated_token_ids"] == off["generated_token_ids"]
    return dict(off_identical=True, dispatch_checked=True, prefill_and_decode=True)


def frozen_files():
    return [
        Path(__file__),
        ROOT / "scripts/focus_check40.py",
        ROOT / "scripts/focus_check40b.py",
        ROOT / "scripts/focus_check40c.py",
        OUT / "banks.json",
        OUT / "prewritten-reading.md",
        OUT / "cpu.json",
        OUT / "runtime-cpu.json",
    ]


def prepare():
    assert not (OUT / "recipe-freeze.json").exists(), "Refuse refreeze"
    bank = banks()
    write("banks.json", bank)
    source = (
        (ROOT / "results/neuron-granularity-research-astra.md")
        .read_text()
        .split("**4. One proposed SET-only screen:")[1]
        .split("**Blunt odds:")[0]
    )
    (OUT / "prewritten-reading.md").write_text(
        "# Check43 — CONCEPT-level SUM/PRODUCT router SET\n\nUnregistered, disclosed. Fit/train: none. Profile: seed95061 Python; dose: disjoint seed95062 Python; evaluate: fresh seeds95063/95064 Python/JS.\n"
        + CLARIFICATIONS
        + "\n## Governing source, verbatim\n\n**4. One proposed SET-only screen:"
        + source
    )
    write("cpu.json", cpu_tests(bank))
    rt = verified.runtime()
    rt.update(
        node=subprocess.check_output(["node", "--version"], text=True).strip(),
        acorn_source_sha256=subprocess.check_output(
            [
                "node",
                "-e",
                "console.log(require('crypto').createHash('sha256').update(process.binding('natives')['internal/deps/acorn/acorn/dist/acorn']).digest('hex'))",
            ],
            text=True,
        ).strip(),
    )
    write("runtime-cpu.json", rt)
    write(
        "projection-initial.json",
        dict(
            generations=392,
            max_tokens=37632,
            source_projected_hours=(37632 / 15 + 314 + 600) * 1.25 / 3600,
            with_instrumentation_replay_hours=((37632 + 96) / 15 + 314 + 600)
            * 1.25
            / 3600,
            cap_seconds=LIMIT,
        ),
    )
    write(
        "recipe-freeze.json",
        dict(
            files={str(p.relative_to(ROOT)): base.sha(p) for p in frozen_files()},
            seeds=[95061, 95062, 95063, 95064],
            layers=[7, 34],
            alpha=[1, 2, 3],
            cap=96,
        ),
    )
    (OUT / "README.md").write_text(
        "# Check43 — SUM/PRODUCT router SET\n\n**CPU READY** — frozen recipe; no model outcomes yet.\n\nSee [prewritten reading](prewritten-reading.md), [CPU checker validation](cpu.json) and [recipe hashes](recipe-freeze.json).\n"
    )
    print("CPU fixtures and recipe freeze ready", flush=True)


class DispatchAudit:
    def __init__(self, engine):
        self.engine = engine
        self.handles = []
        self.active = False
        for i, layer in enumerate(engine.model.model.layers):
            self.handles.append(
                layer.mlp.gate.register_forward_hook(self.before(i), prepend=True)
            )
            self.handles.append(layer.mlp.gate.register_forward_hook(self.after(i)))
            self.handles.append(
                layer.mlp.experts.register_forward_pre_hook(self.consume(i))
            )

    def reset(self):
        self.active = True
        self.original = {}
        self.returned = {}
        self.stats = {}
        self.calls = [0] * len(self.engine.model.model.layers)

    def before(self, i):
        def hook(g, args, out):
            if self.active:
                self.original[i] = (out[1], out[2])

        return hook

    def after(self, i):
        def hook(g, args, out):
            if not self.active:
                return
            self.returned[i] = (out[1], out[2])

        return hook

    def consume(self, i):
        def hook(module, args):
            if not self.active:
                return
            torch = self.engine.torch
            _, idx, w = args
            expected_w, expected_idx = self.returned.pop(i)
            mismatch = (idx != expected_idx).sum() + (w != expected_w).sum()
            ow, oi = self.original.pop(i)
            old = torch.zeros(
                (len(idx), self.engine.model.config.num_experts),
                device=w.device,
                dtype=torch.float32,
            ).scatter_(1, oi, ow.float())
            new = torch.zeros_like(old).scatter_(1, idx, w.float())
            key = f"{i}-" + ("prefill" if self.calls[i] == 0 else "decode")
            self.calls[i] += 1
            values = torch.stack(
                [
                    torch.tensor(len(idx), device=w.device),
                    (idx.sort(-1).values != oi.sort(-1).values).any(-1).sum(),
                    (new - old).abs().sum(),
                    (new != old).any(-1).sum(),
                    mismatch,
                ]
            ).double()
            self.stats[key] = self.stats.get(key, torch.zeros_like(values)) + values

        return hook

    def finish(self):
        self.active = False
        assert (
            not self.original and not self.returned and all(c > 0 for c in self.calls)
        )
        result = {
            k: dict(
                zip(
                    (
                        "tokens",
                        "changed_route_tokens",
                        "mixture_l1_sum",
                        "changed_weight_tokens",
                        "consumer_mismatches",
                    ),
                    v.cpu().tolist(),
                    strict=True,
                )
            )
            for k, v in self.stats.items()
        }
        assert all(v["consumer_mismatches"] == 0 for v in result.values()), (
            "dispatch mismatch"
        )
        return result

    def close(self):
        for h in self.handles:
            h.remove()


def validate_commit(manifest):
    for name, h in manifest["files"].items():
        p = ROOT / name
        assert base.sha(p) == h, f"freeze drift {name}"
        committed = subprocess.check_output(["git", "show", f"HEAD:{name}"], cwd=ROOT)
        assert hashlib.sha256(committed).hexdigest() == h, f"not committed {name}"


def readiness():
    flags = [
        str(p)
        for p in (ROOT / "results/quick-checks").glob("*/RUNNING.flag")
        if p != OUT / "RUNNING.flag"
    ]
    pids = [p for p in base.gpu_pids() if p != "2705" and int(p) != os.getpid()]
    return dict(flags=flags, other_gpu_pids=pids, ready=not flags and not pids)


@contextlib.contextmanager
def reservation():
    while True:
        with (ROOT / ".review.lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                receipt = dict(ready=False, review_lock=True)
            else:
                receipt = readiness()
                if receipt["ready"]:
                    with (OUT / "RUNNING.flag").open("x") as f:
                        f.write(json.dumps(dict(pid=os.getpid(), check=43)))
                    break
        print(json.dumps(receipt), flush=True)
        time.sleep(30)
    try:
        yield
    finally:
        (OUT / "RUNNING.flag").unlink()


def run():
    import torch

    torch.set_num_threads(4)
    verified.runtime()
    validate_commit(json.loads((OUT / "recipe-freeze.json").read_text()))
    assert not (OUT / "records.jsonl").exists(), "Refuse rerun"
    with reservation():
        execute(torch)


def execute(torch):
    bank = json.loads((OUT / "banks.json").read_text())
    rows = []
    projections = []
    start = time.monotonic()
    engine = None
    audit = None
    base.GPU_SECONDS = LIMIT - 30
    base.SEED = 95061
    summary = dict(reading="INCOMPLETE", reason="interrupted")
    journal = (OUT / "records.jsonl").open("x")
    replay_seconds = 0
    rate = 15.0
    profile_seconds = 600.0

    def elapsed():
        return time.monotonic() - start

    def admit(stage):
        remaining = 392 - len(rows)
        projection = elapsed() + 1.25 * (remaining * 96 / rate + profile_seconds)
        projections.append(
            dict(
                stage=stage,
                elapsed=elapsed(),
                remaining=remaining,
                rate=rate,
                profile_seconds=profile_seconds,
                projected_seconds=projection,
            )
        )
        write("cost-updates.json", projections)
        if projection > LIMIT:
            raise base.BudgetStop("1.5 GPU-h projection refusal")

    def request(task, phase, arm, op=None, bias=None, alpha=None):
        audit.reset()
        rec, _ = engine.generate(messages(task, op), bias=bias, cap=96)
        rec.update(
            id=len(rows),
            task_id=task["id"],
            seed=task["seed"],
            language=task["language"],
            family=task["family"],
            phase=phase,
            arm=arm,
            alpha=alpha,
            hook_sha256=base.sha(ROOT / "scripts/focus_check40.py"),
            recipe_sha256=base.sha(OUT / "recipe-freeze.json"),
            dispatch=audit.finish(),
            score=score(rec["text"], task, rec["truncated"] or rec["cost_stopped"]),
            allocation_seconds=elapsed(),
        )
        assert not rec["retained_kv"] and rec["cache_prefix_token_ids"] == []
        journal.write(json.dumps(rec) + "\n")
        journal.flush()
        os.fsync(journal.fileno())
        rows.append(rec)
        print(
            json.dumps(
                dict(
                    event=phase,
                    id=rec["id"],
                    task=task["id"],
                    arm=arm,
                    alpha=alpha,
                    SUM=rec["score"]["SUM"],
                    PRODUCT=rec["score"]["PRODUCT"],
                    malformed=rec["score"]["malformed"],
                    elapsed=elapsed(),
                )
            ),
            flush=True,
        )
        if rec["cost_stopped"]:
            raise base.BudgetStop("per-token deadline")
        return rec

    try:
        engine = base.Engine(start)
        for p in engine.model.parameters():
            p.requires_grad_(False)
        write("kernel.json", engine.verify_kernel())
        assert json.loads((OUT / "kernel.json").read_text())["adopted"]
        assert sum(verified.raw_contract(g) for g in engine.hooks.gates) == 48
        write(
            "runtime-gpu.json",
            dict(
                load_seconds=engine.load_seconds,
                torch=torch.__version__,
                config=engine.model.config.to_dict(),
                pid=os.getpid(),
                weights=base.weights_ready(),
                parameters_frozen=all(
                    not p.requires_grad for p in engine.model.parameters()
                ),
            ),
        )
        audit = DispatchAudit(engine)
        pilot_task = next(t for t in bank["setup"] if t["family"] == "slice")
        pilot = request(pilot_task, "setup-control", "text-SUM", op="SUM")
        rate = len(pilot["generated_token_ids"]) / pilot["seconds"]
        # Full-sequence OFF parity through actual generation, hooks absent.
        audit.close()
        engine.hooks.close()
        replay, _ = engine.generate(messages(pilot_task, "SUM"), cap=96)
        replay_seconds = replay["seconds"]
        write("unhooked-replay.json", replay)
        assert (
            replay["generated_token_ids"] == pilot["generated_token_ids"]
            and replay["input_sha256"] == pilot["input_sha256"]
        ), "OFF output parity"
        engine.hooks = base.RouterHooks(
            [layer.mlp.gate for layer in engine.model.model.layers]
        )
        audit = DispatchAudit(engine)
        write(
            "pilot.json",
            dict(
                record_id=pilot["id"],
                tokens_per_second=rate,
                unhooked_output_identical=True,
                extra_instrumentation_seconds=replay_seconds,
            ),
        )
        admit("after-pilot")
        donor = {
            op: [request(t, "donor", op, op=op) for t in bank["donor"]] for op in OPS
        }
        competence = {op: sum(r["score"][op] for r in donor[op]) for op in OPS}
        write("donor-competence.json", competence)
        summary["donor_competence"] = competence
        if min(competence.values()) < 15:
            summary.update(reading="INELIGIBLE", reason="DONOR COMPETENCE below 15/16")
            return
        pstart = time.monotonic()
        profiles = []
        neutral_ids = None
        for op in OPS:
            examples = []
            for t, r in zip(bank["donor"], donor[op], strict=True):
                if elapsed() > LIMIT - 60:
                    raise base.BudgetStop("profile deadline")
                # Render prefix through end of user text, locating actual suffix IDs.
                ids = r["input_token_ids"]
                end = engine.tokenizer.convert_tokens_to_ids("<|im_end|>")
                stop = max(i for i, x in enumerate(ids) if x == end)
                positions = list(range(stop - 4, stop))
                tokens = [ids[i] for i in positions]
                if neutral_ids is None:
                    neutral_ids = tokens
                assert tokens == neutral_ids and len(tokens) == 4
                h = engine.hooks
                h.reset_capture()
                h.capture = True
                h.capture_slice = slice(stop - 4, stop)
                h.bias = None
                with torch.inference_mode():
                    engine.model(
                        input_ids=torch.tensor([ids], device=engine.device),
                        use_cache=False,
                        logits_to_keep=1,
                    )
                torch.cuda.synchronize()
                h.capture = False
                h.capture_slice = None
                assert h.counts == [4] * 48
                raw = h.sums.cpu() / 4
                examples.append(raw)
                directory = OUT / "profiles"
                directory.mkdir(exist_ok=True)
                torch.save(
                    dict(
                        task_id=t["id"],
                        operation=op,
                        input_token_ids=ids,
                        positions=positions,
                        neutral_token_ids=tokens,
                        logit_sums=h.sums.cpu(),
                        count=4,
                        mean=raw,
                    ),
                    directory / f"{op}-{t['id']}.pt",
                )
            profiles.append(torch.stack(examples).mean(0))
        means = torch.stack(profiles)
        b = (means[0] - means[1]) / 2
        b = b - b.mean(-1, keepdim=True)
        b[:7] = 0
        b[35:] = 0
        b = b.float()
        assert torch.isfinite(b).all() and b.norm() > 0
        gen = torch.Generator().manual_seed(95062)
        shuffled = b.clone()
        perms = []
        for layer_index in range(48):
            perm = torch.randperm(128, generator=gen)
            perms.append(perm)
            shuffled[layer_index] = b[layer_index, perm]
        assert torch.equal(b.sort(-1).values, shuffled.sort(-1).values)
        torch.save(
            dict(
                means=means,
                b=b,
                shuffled=shuffled,
                permutations=torch.stack(perms),
                neutral_token_ids=neutral_ids,
                statistic="last-four-neutral-prompt-tokens; equal example mean",
                layers=[7, 34],
            ),
            OUT / "profiles.pt",
        )
        profile_seconds = 0.0
        write("profile-timing.json", dict(seconds=time.monotonic() - pstart))
        admit("before-grid")
        cells = []
        for alpha in (1, 2, 3):
            grid = []
            for t in bank["setup"]:
                pair = [
                    request(t, "grid", a, bias=sign * alpha * b, alpha=alpha)
                    for a, sign in (("plus", 1), ("minus", -1))
                ]
                grid.append(pair)
            cells.append(
                dict(
                    alpha=alpha,
                    paired=sum(
                        p[0]["score"]["SUM"] and p[1]["score"]["PRODUCT"] for p in grid
                    ),
                    malformed=sum(r["score"]["malformed"] for p in grid for r in p),
                )
            )
            write("grid.json", cells)
        candidates = [
            c["alpha"] for c in cells if c["paired"] >= 6 and c["malformed"] == 0
        ]
        if not candidates:
            summary.update(
                reading="FAIL",
                reason="NO SAFE SET: no alpha has paired >=6/8 and zero malformed",
                grid=cells,
            )
            return
        alpha = min(candidates)
        summary["selected_alpha"] = alpha
        biases = {
            "plus": alpha * b,
            "minus": -alpha * b,
            "shuffle-plus": alpha * shuffled,
            "shuffle-minus": -alpha * shuffled,
        }
        torch.save(biases, OUT / "frozen-biases.pt")
        write(
            "selection.json",
            dict(
                alpha=alpha,
                rule="smallest paired>=6/8; zero malformed",
                final_records=0,
                grid=cells,
            ),
        )
        for t in bank["setup"]:
            for a in (
                "OFF",
                "shuffle-plus",
                "shuffle-minus",
                "text-SUM",
                "text-PRODUCT",
            ):
                if t["id"] == pilot_task["id"] and a == "text-SUM":
                    continue
                request(
                    t,
                    "setup-control",
                    a,
                    op=a[5:] if a.startswith("text-") else None,
                    bias=biases.get(a),
                    alpha=alpha if a in biases else None,
                )
        controls = [r for r in rows if r["phase"] == "setup-control"]
        write(
            "setup-controls.json",
            {
                a: dict(
                    n=sum(r["arm"] == a for r in controls),
                    malformed=sum(
                        r["score"]["malformed"] for r in controls if r["arm"] == a
                    ),
                )
                for a in (
                    "OFF",
                    "shuffle-plus",
                    "shuffle-minus",
                    "text-SUM",
                    "text-PRODUCT",
                )
            },
        )
        assert len(rows) == 120
        admit("before-final-freeze")
        journal.flush()
        os.fsync(journal.fileno())
        # Copy immutable setup journal; live journal will continue after commit.
        (OUT / "setup-records.jsonl").write_bytes((OUT / "records.jsonl").read_bytes())
        paths = [
            p
            for p in OUT.rglob("*")
            if p.is_file()
            and p.name
            not in (
                "RUNNING.flag",
                "records.jsonl",
                "README.md",
                "final-freeze.json",
                "cost-updates.json",
            )
        ]
        write(
            "final-freeze.json",
            dict(
                files={str(p.relative_to(ROOT)): base.sha(p) for p in paths},
                recipe_sha256=base.sha(OUT / "recipe-freeze.json"),
                alpha=alpha,
                final_records=0,
                allocation_seconds=elapsed(),
            ),
        )
        commit_paths = [str(p.relative_to(ROOT)) for p in paths] + [
            "results/quick-checks/check43/final-freeze.json"
        ]
        subprocess.run(["git", "add", "-f", "--", *commit_paths], cwd=ROOT, check=True)
        subprocess.run(
            [
                "git",
                "commit",
                "-m",
                "check43 freeze Python-derived direction and selected dose before final generation",
                "--",
                *commit_paths,
            ],
            cwd=ROOT,
            check=True,
        )
        validate_commit(json.loads((OUT / "final-freeze.json").read_text()))
        write(
            "final-launch.json",
            dict(
                commit=subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
                ).strip(),
                freeze_sha256=base.sha(OUT / "final-freeze.json"),
                final_records=0,
            ),
        )
        admit("final")
        for t in bank["final"]:
            instance = []
            for a in ARMS:
                instance.append(
                    request(
                        t,
                        "final",
                        a,
                        op=a[5:] if a.startswith("text-") else None,
                        bias=biases.get(a),
                        alpha=alpha if a in biases else None,
                    )
                )
            nontext = [r for r in instance if not r["arm"].startswith("text-")]
            assert (
                len({r["input_sha256"] for r in nontext}) == 1
                and len({r["cache_prefix_sha256"] for r in nontext}) == 1
            )
        admit("collateral")
        for t in bank["collateral"]:
            for a in ("OFF", "plus", "minus"):
                request(
                    t,
                    "collateral",
                    a,
                    op=t["operation"],
                    bias=biases.get(a),
                    alpha=alpha if a in biases else None,
                )
        summary.update(final_summary(rows, bank), reason="completed frozen matrix")
    except base.BudgetStop as exc:
        summary.update(reading="INCOMPLETE", reason=str(exc))
    except Exception as exc:
        summary.update(reading="INVALID", reason=repr(exc))
        raise
    finally:
        journal.close()
        if audit is not None:
            audit.close()
        if engine is not None:
            engine.hooks.close()
            summary["peak_allocated_gib"] = torch.cuda.max_memory_allocated() / 2**30
            del engine
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        summary.update(
            gpu_seconds=elapsed(),
            cap_seconds=LIMIT,
            overrun_seconds=max(0, elapsed() - LIMIT),
            records=len(rows),
            generated_tokens=sum(len(r["generated_token_ids"]) for r in rows),
            instrumentation_replay_seconds=replay_seconds,
        )
        write("summary.json", summary)
        print(json.dumps(summary), flush=True)


def audit_records():
    bank = json.loads((OUT / "banks.json").read_text())
    tasks = {t["id"]: t for ts in bank.values() for t in ts}
    rows = [json.loads(x) for x in (OUT / "records.jsonl").read_text().splitlines()]
    for i, r in enumerate(rows):
        assert r["id"] == i
        assert (
            score(r["text"], tasks[r["task_id"]], r["truncated"] or r["cost_stopped"])
            == r["score"]
        )
        assert (
            r["input_sha256"]
            == hashlib.sha256(json.dumps(r["input_token_ids"]).encode()).hexdigest()
        )
        assert len(r["generated_token_ids"]) <= 96
        assert len(r["dispatch"]) >= 48
        if r["arm"] in ("OFF", "text-SUM", "text-PRODUCT", "SUM", "PRODUCT"):
            assert all(
                v["changed_route_tokens"] == 0 and v["changed_weight_tokens"] == 0
                for v in r["dispatch"].values()
            )
    summary = json.loads((OUT / "summary.json").read_text())
    if len(rows) == 392:
        recomputed = final_summary(rows, bank)
        for k, v in recomputed.items():
            assert summary[k] == v, k
    write(
        "audit.json",
        dict(
            records=len(rows),
            all_scores_recomputed=True,
            input_hashes=True,
            off_dispatch_unchanged=True,
            reading=summary["reading"],
        ),
    )
    print("Record audit passed", len(rows), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode", required=True, choices=["prepare", "test", "run", "audit"]
    )
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare()
    elif args.mode == "test":
        print(json.dumps(cpu_tests(banks())))
    elif args.mode == "run":
        run()
    else:
        audit_records()


if __name__ == "__main__":
    main()
