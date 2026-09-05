#!/usr/bin/env python3
"""Disclosed, unregistered check 40. CPU preparation precedes idle-GPU execution."""

# ruff: noqa: E501
from __future__ import annotations

import argparse
import ast
import contextlib
import fcntl
import hashlib
import inspect
import json
import math
import os
import random
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/quick-checks/check40"
MODEL = ROOT / "models/qwen3-30b-a3b-hf"
SEED = 40040
LANGS = ("Python", "JavaScript")
PAIRS = (("Python", "English"), ("Python", "JavaScript"))
SCREEN_N = 64
SUFFIX = "\nGive only the requested answer. Keep it concise and complete."
ARMS = ("correct", "swapped", "shuffled", "OFF", "text-cue")
STEPS = ("SET", "NEUTRAL", "HOLD", "SWITCH", "BACK", "CLEAR")
TARGETS = dict(
    SET="JavaScript",
    HOLD="JavaScript",
    SWITCH="Python",
    BACK="JavaScript",
    CLEAR=None,
    NEUTRAL=None,
)
SYSTEM = "Answer the request concisely. Default to a code block defining the requested function unless the user specifies another format. No examples or extra explanation."
CAP = 256
GPU_SECONDS = 4 * 3600
# Each row supplies a language-free operation and a coarse operation witness.
TASKS = [
    (
        "second_largest",
        "returns the second largest distinct number in a list, or null if absent",
        r"sort|sorted|max|largest",
    ),
    (
        "above_limit",
        "returns the numbers in a list greater than {n}",
        r"filter|for|>|while",
    ),
    ("sum_squares", "returns the sum of squares of the numbers in a list", r"\*|pow"),
    (
        "running_sum",
        "returns the running sums of a list of numbers",
        r"for|reduce|while|accumulate",
    ),
    ("count_even", "counts the even integers in a list", r"%|mod"),
    (
        "deduplicate",
        "removes duplicate values from a list while preserving first occurrence order",
        r"set|Set|includes|in |indexOf",
    ),
    (
        "rotate_right",
        "rotates a list right by {n} positions, handling an empty list",
        r"slice|\[|%",
    ),
    ("chunk_list", "splits a list into chunks of size {n}", r"slice|\["),
    (
        "interleave",
        "interleaves two lists and appends the remaining tail of the longer list",
        r"for|while|zip|flatMap",
    ),
    (
        "merge_sorted",
        "merges two already sorted number lists into one sorted list",
        r"sort|while|for",
    ),
    ("median", "returns the median of a nonempty list of numbers", r"sort|sorted"),
    (
        "nearest",
        "returns the number in a nonempty list closest to {n}",
        r"abs|Math|sort|reduce",
    ),
    (
        "clamp",
        "clamps a number to the inclusive interval from 0 to {n}",
        r"min|max|>|<",
    ),
    (
        "factorial",
        "returns the factorial of a nonnegative integer",
        r"\*|factorial|prod",
    ),
    ("prime", "determines whether an integer is prime", r"%|mod|prime"),
    ("gcd", "returns the greatest common divisor of two positive integers", r"%|gcd"),
    (
        "digit_sum",
        "returns the sum of the decimal digits of an integer",
        r"str|String|%|toString",
    ),
    (
        "binary",
        "returns the base-two string representation of a nonnegative integer",
        r"bin|toString|%|format",
    ),
    (
        "power_two",
        "determines whether a positive integer is a power of two",
        r"&|log|%|/",
    ),
    (
        "divisors",
        "returns all positive divisors of a positive integer in ascending order",
        r"%|mod",
    ),
    (
        "reverse_words",
        "reverses the order of whitespace-separated words in a string",
        r"split|match",
    ),
    ("vowels", "counts vowels in a string without regard to case", r"aeiou|vowel"),
    (
        "palindrome",
        "checks whether a string is a palindrome after ignoring spaces and letter case",
        r"lower|LowerCase|casefold",
    ),
    (
        "initials",
        "returns uppercase initials from the words in a full name",
        r"upper|UpperCase",
    ),
    (
        "longest_word",
        "returns the longest whitespace-separated word in a string",
        r"split|match",
    ),
    (
        "word_count",
        "returns a map of lowercase words to occurrence counts in a string",
        r"split|match|Counter",
    ),
    (
        "compress_spaces",
        "replaces every run of whitespace in a string with a single space and trims the ends",
        r"split|replace|sub",
    ),
    ("prefix", "returns the common prefix of two strings", r"for|while|prefix|zip"),
    (
        "anagrams",
        "determines whether two strings are anagrams, ignoring letter case",
        r"sort|Counter|count|Map",
    ),
    (
        "truncate_text",
        "returns a string unchanged if its length is at most {n}, otherwise its first {n} characters",
        r"slice|\[",
    ),
    ("flatten_once", "flattens a list of lists by one level", r"flat|for|reduce|chain"),
    (
        "transpose",
        "transposes a nonempty rectangular matrix represented as a list of rows",
        r"zip|for|map",
    ),
    ("diagonal", "returns the sum of the main diagonal of a square matrix", r"\["),
    (
        "matrix_add",
        "adds two equally shaped numeric matrices element by element",
        r"\+",
    ),
    (
        "histogram",
        "counts the occurrences of each value in a list",
        r"Counter|Map|for|reduce",
    ),
    ("group_length", "groups a list of words by word length into a map", r"len|length"),
    (
        "invert_map",
        "inverts a map with unique values, exchanging keys and values",
        r"items|entries|keys|for",
    ),
    (
        "pick_keys",
        "returns a new map containing only a supplied list of keys that exist in an input map",
        r"for|filter|reduce",
    ),
    (
        "distance",
        "returns the Euclidean distance between two two-dimensional points",
        r"sqrt|hypot|\*\*|pow",
    ),
    (
        "rectangle",
        "returns whether two axis-aligned rectangles with supplied corner coordinates overlap with positive area",
        r"<|>",
    ),
    (
        "minutes",
        "formats a nonnegative count of minutes as hours followed by a colon and two-digit minutes",
        r"%|divmod",
    ),
    (
        "leap_year",
        "determines whether an integer year is a Gregorian leap year",
        r"%|mod",
    ),
    ("temperature", "converts a temperature from Celsius to Fahrenheit", r"1\.8|9|32"),
    (
        "discount",
        "returns a price after applying a discount of {n} percent",
        r"100|0\.",
    ),
    (
        "balanced",
        "checks whether a string containing only parentheses is balanced",
        r"for|while|reduce",
    ),
    (
        "rle",
        "run-length encodes a string into a list of character-count pairs",
        r"for|while|groupby|reduce",
    ),
    (
        "missing_number",
        "returns the single missing integer from a list containing distinct values from 0 through its length",
        r"sum|reduce|\^|for",
    ),
    (
        "intersection",
        "returns the distinct values shared by two number lists in ascending order",
        r"sort|sorted",
    ),
]

READING = """# Check 40 — brute-force MoE skill routing

Unregistered, disclosed quick check; Brian's 2026-09-05 resume. Seed 40040. This pre-outcome amendment adopts [the research memo](../../moe-routing-research-astra.md). The initial reading remains in commit 531030a; its numerical thresholds remain unchanged.
Fit/train-on: **none**. Profiles average cued synthetic measurements; dose selection uses only the separate setup split. Evaluated-on: fresh authored arithmetic tasks. Four splits have disjoint exact prompts and expression-tree/operator families (32 competence, 32 profile, 16 grid, 64 screen). No benchmark data, recorded benchmark responses, imported expert IDs, or sealed IFEval/BFCL inputs.

## Pre-written reading (frozen before model output)

Pair ranking: (1) Python source versus controlled English description of the same arithmetic tree (memo P1); (2) Python versus JavaScript source for the same tree, retaining Brian's programming-language requirement. Evaluate competence and, if competent, profiles for BOTH pairs; select the first eligible pair, then exactly one grid. No pair substitution after actuator outcomes. The broader P2/P3 alternatives are omitted to retain programming languages within this small budget. Paired inputs and cues are visible only in competence/profile/text controls; screen requests never name a language. Stable system default asks for a function unless another format is requested.

Competence: each mode >=28/32 parser-valid, unbroken responses. Record task correctness separately and uncued default distribution on the same 32. Python uses ast.parse; JavaScript uses node --check. English is parsed through a frozen recursive grammar: integer leaves; “the sum/difference/product of (X) and (Y)”. Code task checks require a named nonstub function and the exact requested return-expression AST; English task checks require the exact tree. No program execution. This is narrow serialization/operand preservation, not general programming competence; failure of this restrictive grammar makes the pair INELIGIBLE.

Primary profile: per-example mean top-8 expert selection frequencies over the final eight IDENTICAL prompt-suffix token IDs, averaged equally over 32 paired examples. The suffix and ordinary assistant header follow the differing user cues; verify suffix equality before accepting profiles. Canonical checker-defined answers are teacher-forced only for measurement, with no outcome filtering. Record answer-position frequencies, mean logits, router mass, and eighth-minus-ninth margins separately as diagnostics. Sigma per layer is the pooled mean within-token logit SD on primary suffix positions. P[s,l,e]=sigma[l]*f[s,l,e]; bias=alpha*(P[s]-mean(P)). No difference-norm amplification, changed top-k, or training. Save per-task statistics and token IDs in the same run.

Report per-layer primary raw-logit RMS distance, frequency L1, and top-8 intersection/8. Preserve the initial eligibility threshold: >=7/8 overlap at EVERY layer means INELIGIBLE “same experts” under this operational statistic. This is not mathematical identity; the memo's additional permutation/reliability gates and new outcome thresholds are not substituted for the user-preserved reading.

Grid: alpha {0.5,1,2,4} x {all,upper half}, both directions on the separate 16-task slice. Rank by both directions >=10/16 valid/unbroken; then lowest total breakage; largest minimum directional successes; largest total successes; smaller alpha; upper half. If no cell reaches both bars, freeze the best and disclose that fact. Never select on screen outcomes.

Episodes: 64 screen statements, five different tasks per episode at offsets {0,13,26,39,52} modulo 64. SET -> neutral “Reply only OK.” pair -> HOLD -> SWITCH -> BACK -> CLEAR. Keep actual complete user/assistant history and incremental KV, including generated terminal tokens. Bias affects NEW request prefill and decode; consume each answer's last sampled token under its original bias, then switch. Never recompute old KV under a new bias. A truncated answer stays in history, with a disclosed structural end marker to close its chat turn. No history eviction or answer replacement. CLEAR supplies a fresh uncued task with bias OFF; compare to its separately generated fresh OFF default.

Arms: correct maps B/A/B at SET/SWITCH/BACK, maintaining B through neutral/HOLD; swapped reverses addresses. Shuffled uses one fixed expert-index permutation per layer applied to both centered profiles (seed 40042), preserving values, norms, and opposition. OFF has no bias. Text-cue adds the current mode cue at SET/HOLD/SWITCH/BACK, none at neutral/CLEAR. Score every arm against the correct address and report actual mode counts.

Breakage: empty/invalid/ambiguous parse, unclosed/multiple fences, 256-token cap without EOS, a nonblank >=8-character line repeated >=4 times, or an 8-token span repeated >=6 times. Valid wrong-tree outputs are task failures, reported separately. English parsing admits the frozen grammar only. Fence labels never establish language identity.

POSSIBLE: complete 64-episode screen, correct SET >=40/64 and SWITCH >=40/64 valid/unbroken addressed outputs, <=4/64 broken correct episodes, shuffled B <=8/64 at its worst SET/HOLD/SWITCH/BACK stage, and correct CLEAR impositions <=8/64. Imposition = valid B after CLEAR where paired fresh default is valid Python. MARGINAL if correct SET >=24/64; otherwise NOT POSSIBLE. Eligibility takes precedence. HOLD/BACK/task checks are separate. These descriptive thresholds do not establish statistical existence or benchmark generalization.

Throughput FIRST: load bf16 Qwen3MoeForCausalLM, SDPA, single GPU, non-thinking, then verify the already-installed grouped_mm expert path against eager and the tuple-aware hook. Require changed expert dispatch under nonzero bias and exact OFF next-token logits; adopt grouped_mm only on compatibility/parity success. No new kernel development or serving engine. Generate THREE 128-token pilot continuations (EOS suppressed only to measure exactly 128; this exception never applies to scored generation). Record each wall-clock tokens/s and use the slowest; time a 2048-token prefill as a conservative retained-context envelope.

Before competence/extraction, project load/pilot + both candidate competence/profile screens + complete dose grid + 64 episodes x five arms x six replies + fresh defaults, at 256 capped tokens/reply, with 25% reserve. Teacher-forced passes and prefill are charged separately. If >4 GPU-h, SCALE to 32 episodes, alpha {1,4}, layers {all}; record measured projection and scaling in this README before proceeding. If still >4 h, STOP with measured throughput and no extraction. Preserve literal initial 64-count thresholds: a scaled run is a disclosed PARTIAL descriptive screen, never promoted to a full-screen POSSIBLE verdict. Recheck a conservative remaining-cost projection before grid and screen; never launch beyond cap.

Four-hour wall allocation starts before load. Cooperative deadline checks between requests/tokens; blocking kernels/load may overrun and any excess is reported. Foreground idle-GPU/download wait only, nvidia-smi polls every 600 seconds; never signal any process. All safetensors index shards must have matching membership, exact complete byte lengths and available HF SHA256 metadata verification; wait until model-specific downloader exits. A retained prompt exceeding the measured 2048-token envelope stops rather than silently extrapolating cost.

**Primary alternative explanation:** profiles may describe tokens produced AFTER a task has already been selected, while task choice lives in shared attention/residual computation. A bias could change syntax or damage processing without selecting a skill. Shared-suffix primary measurements and separate answer-token diagnostics address this risk; even a positive result is only externally maintained oracle control on these synthetic output modes.

## Results

PENDING — CPU amendment; no model output exists.
"""


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)


@contextlib.contextmanager
def review_lock():
    with (ROOT / ".review.lock").open("a") as f:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def bank():
    rng = random.Random(SEED)
    rows = []
    for variant in range(3):
        for family, task, witness in TASKS:
            n = rng.randrange(3, 20)
            name = f"{family}_{variant + 1}"
            rows.append(
                dict(
                    id=name,
                    family=family,
                    name=name,
                    witness=witness,
                    prompt=f"Write a function named {name} that "
                    + task.format(n=n)
                    + ".",
                )
            )
    rng.shuffle(rows)
    result = dict(
        competence=rows[:32], profile=rows[32:64], grid=rows[64:80], screen=rows[80:144]
    )
    assert [len(result[x]) for x in result] == [32, 32, 16, 64]
    assert len({r["prompt"] for r in rows}) == 144
    assert not any(
        re.search(r"python|javascript|\bGo\b", r["prompt"], re.I) for r in rows
    )
    return result


def expression_bank():
    """Authored arithmetic only; disjoint operator/tree families across splits."""
    rng = random.Random(SEED)
    result = {}
    shapes = {
        "competence": ["({a}+{b})", "({a}-{b})", "({a}*{b})"],
        "profile": ["(({a}+{b})*{c})", "(({a}-{b})+{c})", "(({a}*{b})-{c})"],
        "grid": ["({a}*({b}+{c}))", "({a}+({b}-{c}))", "({a}-({b}*{c}))"],
        "screen": [
            "(({a}+{b})*({c}-{d}))",
            "(({a}*{b})+({c}*{d}))",
            "(({a}-{b})-({c}+{d}))",
        ],
    }
    for split, n in (("competence", 32), ("profile", 32), ("grid", 16), ("screen", 64)):
        result[split] = []
        for i in range(n):
            expression = shapes[split][i % 3].format(
                **{x: rng.randrange(2, 40) for x in "abcd"}
            )
            name = f"solve_{split}_{i}"
            result[split].append(
                dict(
                    id=name,
                    name=name,
                    family=f"{split}_{i % 3}",
                    witness=r"[+*\-]",
                    expression=expression,
                    prompt=f"For the arithmetic expression {expression}, provide a solution. If writing a function, name it {name}.",
                )
            )
    assert len({r["prompt"] for rs in result.values() for r in rs}) == 144
    return result


def english_tree(node):
    if isinstance(node, ast.Constant) and type(node.value) is int:
        return str(node.value)
    assert isinstance(node, ast.BinOp)
    op = {ast.Add: "sum", ast.Sub: "difference", ast.Mult: "product"}[type(node.op)]
    return f"the {op} of ({english_tree(node.left)}) and ({english_tree(node.right)})"


def parse_english(text):
    text = text.strip().rstrip(".").lower()
    if re.fullmatch(r"[0-9]+", text):
        return ast.Constant(value=int(text))
    m = re.match(r"the (sum|difference|product) of \(", text)
    if not m:
        raise ValueError("Outside frozen English grammar")
    depth, end = 1, m.end()
    while end < len(text) and depth:
        depth += (text[end] == "(") - (text[end] == ")")
        end += 1
    if depth or not text[end:].startswith(" and (") or not text.endswith(")"):
        raise ValueError("Unbalanced English operands")
    left = parse_english(text[m.end() : end - 1])
    right = parse_english(text[end + 6 : -1])
    op = {"sum": ast.Add, "difference": ast.Sub, "product": ast.Mult}[m[1]]()
    return ast.BinOp(left=left, op=op, right=right)


def canonical(task, lang):
    expr = task["expression"]
    if lang == "English":
        return english_tree(ast.parse(expr, mode="eval").body) + "."
    if lang == "Python":
        return f"def {task['name']}():\n    return {expr}"
    return f"function {task['name']}() {{ return {expr}; }}"


def set_pair(pair):
    global LANGS, TARGETS
    LANGS = tuple(pair)
    TARGETS = dict(
        SET=LANGS[1],
        HOLD=LANGS[1],
        SWITCH=LANGS[0],
        BACK=LANGS[1],
        CLEAR=None,
        NEUTRAL=None,
    )


def extract_code(text):
    if "```" not in text:
        return text.strip(), None
    matches = re.findall(r"```[^\n]*\n(.*?)```", text, re.S)
    if text.count("```") != 2 or len(matches) != 1:
        return "", "fences"
    return matches[0].strip(), None


def score(text, task, truncated=False):
    code, fence_error = extract_code(text)
    parsed = {"Python": False, "JavaScript": False}
    tree = None
    errors = {}
    if code:
        try:
            tree = ast.parse(code)
            parsed["Python"] = True
        except (SyntaxError, ValueError) as exc:
            errors["Python"] = str(exc)[:300]
        proc = subprocess.run(
            [shutil.which("node"), "--check", "-"],
            input=code,
            text=True,
            capture_output=True,
            check=False,
        )
        parsed["JavaScript"] = proc.returncode == 0
        if proc.returncode:
            errors["JavaScript"] = proc.stderr[:300]
    languages = [lang for lang in ("Python", "JavaScript") if parsed[lang]]
    language = (
        languages[0] if len(languages) == 1 else "ambiguous" if languages else "invalid"
    )
    lines = Counter(x.strip() for x in code.splitlines() if len(x.strip()) >= 8)
    words = re.findall(r"\w+|[^\s\w]", code)
    spans = Counter(tuple(words[i : i + 8]) for i in range(max(0, len(words) - 7)))
    repetitive = (
        max(lines.values(), default=0) >= 4 or max(spans.values(), default=0) >= 6
    )
    flags = dict(
        empty=not code,
        invalid=language == "invalid",
        ambiguous=language == "ambiguous",
        fences=bool(fence_error),
        truncated=bool(truncated),
        repetitive=repetitive,
    )
    coarse = False
    if language == "Python":
        funcs = [
            n
            for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            and n.name == task["name"]
        ]
        coarse = any(
            any(
                isinstance(n, ast.Return)
                and n.value is not None
                and not isinstance(n.value, ast.Constant)
                for n in ast.walk(f)
            )
            and any(
                isinstance(
                    n,
                    (
                        ast.Call,
                        ast.BinOp,
                        ast.Compare,
                        ast.For,
                        ast.While,
                        ast.Subscript,
                        ast.If,
                    ),
                )
                for n in ast.walk(f)
            )
            for f in funcs
        )
    elif language == "JavaScript":
        name = re.escape(task["name"])
        defined = re.search(
            r"\bfunction\s+"
            + name
            + r"\s*\(|\b(?:const|let|var)\s+"
            + name
            + r"\s*=\s*(?:function\b|(?:\([^)]*\)|\w+)\s*=>)",
            code,
        )
        nonstub = re.search(
            r"\breturn\s+(?!null\b|undefined\b|true\b|false\b)([^;\n}]+)", code
        )
        meaningful_return = bool(
            nonstub
            and not re.fullmatch(
                r"\s*(?:[\w]+|[\d.]+|[\'\"].*[\'\"])\s*", nonstub.group(1)
            )
        )
        if nonstub and re.fullmatch(r"\s*\w+\s*", nonstub.group(1)):
            meaningful_return = bool(
                re.search(r"\bfor\b|\bwhile\b|\+=|\*=|\.push\(|\.add\(|\bif\s*\(", code)
            )
        arrow_expression = bool(
            re.search(r"=>\s*(?!\{)[^;\n]+(?:\(|\[|\+|\*|>|<|%)", code)
        )
        coarse = bool(defined and (meaningful_return or arrow_expression))
    coarse = bool(coarse and re.search(task["witness"], code))
    if "expression" in task:
        wanted = ast.dump(ast.parse(task["expression"], mode="eval").body)
        if language == "Python":
            returns = [n.value for n in ast.walk(tree) if isinstance(n, ast.Return)]
            coarse = coarse and any(ast.dump(n) == wanted for n in returns)
        elif language == "JavaScript":
            match = re.search(r"return\s+([^;]+);?", code)
            try:
                coarse = (
                    coarse
                    and bool(match)
                    and ast.dump(ast.parse(match[1].strip(), mode="eval").body)
                    == wanted
                )
            except SyntaxError:
                coarse = False
        try:
            parsed_tree = parse_english(text)
            if isinstance(parsed_tree, ast.BinOp):
                language = "English"
                parsed["English"] = True
                flags["invalid"] = flags["ambiguous"] = False
                coarse = ast.dump(parsed_tree) == wanted
        except (ValueError, RecursionError):
            pass
    broken = any(flags.values())
    return dict(
        language=language,
        parsers=parsed,
        parser_errors=errors,
        flags=flags,
        broken=broken,
        valid_language=language if not broken else None,
        task_check=coarse,
        valid_task=coarse and not broken,
        code=code,
    )


class RouterHooks:
    """Tuple-aware gate hooks; consumer receives re-selected experts and weights."""

    def __init__(self, gates):
        self.gates = gates
        self.bias = None
        self.capture = False
        self.capture_slice = None
        self.sums = None
        self.counts = None
        self.freqs = None
        self.handles = [
            g.register_forward_hook(self.hook(i)) for i, g in enumerate(gates)
        ]

    def reset_capture(self):
        import torch

        g = self.gates[0]
        self.sums = torch.zeros(
            len(self.gates), g.num_experts, device=g.weight.device, dtype=torch.float64
        )
        self.freqs = self.sums.clone()
        self.mass = self.sums.clone()
        self.sd = self.sums[:, 0].clone()
        self.margin = self.sd.clone()
        self.counts = [0] * len(self.gates)

    def hook(self, layer):
        def apply(gate, inputs, output):
            import torch

            tuple_output = isinstance(output, tuple)
            logits = output[0] if tuple_output else output
            if self.capture:
                assert self.sums is not None
                observed = (
                    logits if self.capture_slice is None else logits[self.capture_slice]
                )
                assert observed.shape[0] > 0
                self.sums[layer].add_(observed.detach().double().sum(0))
                probs = torch.softmax(observed.float(), -1)
                idx = torch.topk(probs, gate.top_k, -1).indices
                self.freqs[layer].add_(
                    torch.bincount(idx.flatten(), minlength=gate.num_experts)
                )
                self.mass[layer].add_(probs.double().sum(0))
                self.sd[layer].add_(
                    observed.float().std(-1, correction=0).double().sum()
                )
                ranked = observed.float().topk(gate.top_k + 1, -1).values
                self.margin[layer].add_((ranked[:, -2] - ranked[:, -1]).double().sum())
                self.counts[layer] += observed.shape[0]
            if self.bias is None:
                return output
            biased = logits + self.bias[layer].to(dtype=logits.dtype)
            if not tuple_output:
                return biased
            assert len(output) == 3
            probs = torch.softmax(biased, dim=-1, dtype=torch.float32)
            weights, indices = torch.topk(probs, gate.top_k, dim=-1)
            if gate.norm_topk_prob:
                weights = weights / weights.sum(dim=-1, keepdim=True)
            return biased, weights.to(logits.dtype), indices

        return apply

    def close(self):
        for h in self.handles:
            h.remove()


def make_biases(profiles, seed=SEED + 2):
    import torch

    centered = profiles - profiles.mean(0, keepdim=True)
    gen = torch.Generator(device="cpu").manual_seed(seed)
    shuffled = centered.clone()
    for layer in range(centered.shape[1]):
        permutation = torch.randperm(centered.shape[2], generator=gen)
        shuffled[:, layer] = centered[:, layer, permutation]
    return centered, shuffled


def profile_stats(logits, frequencies, k=8):
    import torch

    rows = []
    for i in range(logits.shape[1]):
        a, b = [torch.topk(frequencies[j, i], k).indices.tolist() for j in range(2)]
        overlap = len(set(a) & set(b)) / k
        rows.append(
            dict(
                layer=i,
                logit_rms_distance=float(
                    (logits[0, i] - logits[1, i]).square().mean().sqrt()
                ),
                frequency_l1_distance=float(
                    (frequencies[0, i] - frequencies[1, i]).abs().sum()
                ),
                top_experts=dict(zip(LANGS, (a, b), strict=True)),
                overlap=overlap,
            )
        )
    return dict(layers=rows, same_experts=all(r["overlap"] >= 7 / 8 for r in rows))


def choose_grid(cells):
    def rank(c):
        successes = list(c["successes"].values())
        return (
            -int(min(successes) >= 10),
            c["broken"],
            -min(successes),
            -sum(successes),
            c["alpha"],
            c["layers"] != "upper_half",
        )

    return min(cells, key=rank)


def gpu_pids():
    return (
        subprocess.check_output(
            ["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"],
            text=True,
        )
        .strip()
        .split()
    )


def downloaders():
    found = []
    for p in Path("/proc").iterdir():
        if not p.name.isdigit():
            continue
        try:
            args = (p / "cmdline").read_bytes().split(b"\0")
        except (OSError, PermissionError):
            continue
        if (
            b"download" in args
            and any(b"qwen3-30b-a3b" in a.lower() for a in args)
            and any(
                Path(os.fsdecode(a)).name in ("hf", "huggingface-cli")
                for a in args[:3]
                if a
            )
        ):
            found.append(int(p.name))
    return found


def weights_ready(model=MODEL, hashes=False):
    model = Path(model)
    required = (
        "config.json",
        "model.safetensors.index.json",
        "tokenizer.json",
        "tokenizer_config.json",
    )
    missing = [x for x in required if not (model / x).is_file()]
    if missing:
        return dict(ready=False, missing=missing)
    config = json.loads((model / "config.json").read_text())
    assert config["model_type"] == "qwen3_moe"
    index = json.loads((model / "model.safetensors.index.json").read_text())
    shards = sorted(set(index["weight_map"].values()))
    files = []
    total = 0
    for name in shards:
        path = model / name
        if not path.is_file():
            return dict(ready=False, missing=[name])
        with path.open("rb") as f:
            raw = f.read(8)
            if len(raw) != 8:
                return dict(ready=False, incomplete=name)
            header_size = struct.unpack("<Q", raw)[0]
            if not 2 <= header_size <= 100_000_000:
                return dict(ready=False, incomplete=name)
            try:
                header = json.loads(f.read(header_size))
            except (ValueError, UnicodeDecodeError):
                return dict(ready=False, incomplete=name)
        tensors = {k: v for k, v in header.items() if k != "__metadata__"}
        expected = {k for k, v in index["weight_map"].items() if v == name}
        assert set(tensors) == expected, f"Index membership mismatch: {name}"
        end = 0
        for key, desc in sorted(
            tensors.items(), key=lambda kv: kv[1]["data_offsets"][0]
        ):
            start, stop = desc["data_offsets"]
            sizes = dict(
                BF16=2, F16=2, F32=4, F64=8, I64=8, I32=4, I16=2, I8=1, U8=1, BOOL=1
            )
            assert (
                start == end
                and stop - start == math.prod(desc["shape"]) * sizes[desc["dtype"]]
            ), key
            end = stop
        if path.stat().st_size != 8 + header_size + end:
            return dict(ready=False, incomplete=name)
        total += end
        record = dict(name=name, bytes=path.stat().st_size, tensors=len(tensors))
        if hashes:
            record["sha256"] = sha(path)
            meta = model / ".cache/huggingface/download" / (name + ".metadata")
            if meta.exists():
                etag = meta.read_text().splitlines()[1]
                record["download_etag"] = etag
                if re.fullmatch("[0-9a-f]{64}", etag):
                    assert record["sha256"] == etag, f"Shard hash mismatch: {name}"
        files.append(record)
    assert total == index["metadata"]["total_size"], (total, index["metadata"])
    return dict(
        ready=True,
        shards=files,
        tensor_bytes=total,
        index_sha256=sha(model / "model.safetensors.index.json"),
    )


def wait_ready():
    while True:
        active, downloading = gpu_pids(), downloaders()
        ready = weights_ready()
        print(
            json.dumps(
                dict(
                    event="waiting",
                    utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    gpu_pids=active,
                    download_pids=downloading,
                    weights=ready if not ready["ready"] else "complete",
                )
            ),
            flush=True,
        )
        if not active and not downloading and ready["ready"]:
            checked = weights_ready(hashes=True)
            if not gpu_pids() and not downloaders():
                return checked
        # Foreground cooperative waiting only. No signal / subprocess timeout.
        for _ in range(10):
            time.sleep(60)


class BudgetStop(Exception):
    pass


class Engine:
    def __init__(self, start):
        import torch
        from transformers import AutoTokenizer, Qwen3MoeForCausalLM

        self.start = start
        self.deadline = start + GPU_SECONDS
        self.torch = torch
        self.device = torch.device("cuda:0")
        torch.manual_seed(SEED)
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL, local_files_only=True)
        self.model = Qwen3MoeForCausalLM.from_pretrained(
            MODEL,
            dtype=torch.bfloat16,
            device_map={"": 0},
            attn_implementation="sdpa",
            experts_implementation="eager",
            local_files_only=True,
        ).eval()
        assert all(
            p.device.type == "cuda" and p.device.index == 0
            for p in self.model.parameters()
        )
        assert (
            self.model.config.num_experts == 128
            and self.model.config.num_experts_per_tok == 8
        )
        gates = [layer.mlp.gate for layer in self.model.model.layers]
        assert len(gates) == 48
        self.hooks = RouterHooks(gates)
        eos = self.model.generation_config.eos_token_id
        self.eos = set(eos if isinstance(eos, list) else [eos])
        self.eos.add(self.tokenizer.eos_token_id)
        self.load_seconds = time.monotonic() - start

    def generate(
        self,
        messages,
        bias=None,
        capture=False,
        cap=CAP,
        force_length=False,
        session=None,
    ):
        if time.monotonic() >= self.deadline - 30:
            raise BudgetStop("30-second reserve: no new request")
        torch = self.torch
        ids = self.tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            return_dict=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        rendered_ids = ids
        past = None
        if session is not None and session.get("past") is not None:
            # Qwen re-renders old empty <think> spans differently as history grows.
            # Append the independent new user/header template to the ACTUAL old KV.
            new_turn = self.tokenizer.apply_chat_template(
                [messages[-1]],
                tokenize=True,
                return_dict=False,
                add_generation_prompt=True,
                enable_thinking=False,
            )
            assert ids[-len(new_turn) :] == new_turn, "Unexpected user-turn template"
            ids = self.tokenizer.encode("\n", add_special_tokens=False) + new_turn
            past = session["past"]
            assert past.get_seq_length() == len(session["token_ids"]), (
                "KV provenance length mismatch"
            )
        if past is not None and past.get_seq_length() + len(ids) > 2048:
            raise BudgetStop("Retained input exceeds 2048-token measured cost envelope")
        inputs = torch.tensor([ids], device=self.device)
        h = self.hooks
        h.bias = (
            None if bias is None else bias.to(device=self.device, dtype=torch.bfloat16)
        )
        h.capture = False
        if capture:
            h.reset_capture()
        prefix_ids = list(session.get("token_ids", [])) if session is not None else []
        generated, ended, cost_stop = [], False, False
        appended_terminal = []
        started = time.monotonic()
        with torch.inference_mode():
            result = self.model(
                input_ids=inputs, past_key_values=past, use_cache=True, logits_to_keep=1
            )
            for _ in range(cap):
                if time.monotonic() >= self.deadline - 2:
                    cost_stop = True
                    break
                next_logits = result.logits[0, -1].clone()
                if force_length:
                    next_logits[list(self.eos)] = -float("inf")
                token = int(next_logits.argmax())
                generated.append(token)
                if token in self.eos:
                    ended = True
                    if session is not None:
                        result = self.model(
                            input_ids=torch.tensor([[token]], device=self.device),
                            past_key_values=result.past_key_values,
                            use_cache=True,
                            logits_to_keep=1,
                        )
                    break
                # The generated token's own router position, not its predictor.
                # The final non-EOS token is also forwarded when profiling.
                if len(generated) < cap or capture or session is not None:
                    h.capture = capture
                    result = self.model(
                        input_ids=torch.tensor([[token]], device=self.device),
                        past_key_values=result.past_key_values,
                        use_cache=True,
                        logits_to_keep=1,
                    )
            if self.device.type == "cuda":
                torch.cuda.synchronize()
        if session is not None:
            if not ended:
                # Close the actual truncated/invalid answer without replacing it.
                terminal = self.tokenizer.convert_tokens_to_ids("<|im_end|>")
                appended_terminal = [terminal]
                with torch.inference_mode():
                    result = self.model(
                        input_ids=torch.tensor([[terminal]], device=self.device),
                        past_key_values=result.past_key_values,
                        use_cache=True,
                        logits_to_keep=1,
                    )
            session["past"] = result.past_key_values
            session["token_ids"] = prefix_ids + ids + generated + appended_terminal
            assert session["past"].get_seq_length() == len(session["token_ids"])
        h.capture = False
        h.bias = None
        text = self.tokenizer.decode(generated, skip_special_tokens=True)
        record = dict(
            text=text,
            generated_token_ids=generated,
            input_token_ids=ids,
            eos=ended,
            truncated=not ended and len(generated) >= cap,
            token_cap=cap,
            rendered_input_token_ids=rendered_ids,
            retained_kv=session is not None,
            cache_prefix_token_ids=prefix_ids,
            appended_terminal_token_ids=appended_terminal,
            cache_prefix_sha256=hashlib.sha256(
                json.dumps(prefix_ids).encode()
            ).hexdigest(),
            bias_sha256=hashlib.sha256(bias.float().cpu().numpy().tobytes()).hexdigest()
            if bias is not None
            else None,
            cost_stopped=cost_stop,
            seconds=time.monotonic() - started,
            history=messages,
            input_sha256=hashlib.sha256(json.dumps(ids).encode()).hexdigest(),
        )
        profile = None
        if capture:
            count = len(generated) - int(ended)
            assert all(x == count for x in h.counts), (h.counts, count)
            profile = dict(
                logit_sums=h.sums.cpu(), frequency_sums=h.freqs.cpu(), count=count
            )
            record["profile_positions"] = count
        return record, profile

    def verify_kernel(self):
        """One installed optimized expert path; no engine migration or compilation project."""
        from transformers.integrations.moe import _can_use_grouped_mm

        torch = self.torch
        layer = self.model.model.layers[0].mlp
        device = layer.gate.weight.device
        x = torch.randn(
            4, self.model.config.hidden_size, device=device, dtype=torch.bfloat16
        )
        probe = torch.empty(16, 16, device=device, dtype=torch.bfloat16)
        available = _can_use_grouped_mm(
            probe, probe[None], torch.tensor([16], device=device, dtype=torch.int32)
        )
        evidence = dict(candidate="grouped_mm", available=available, adopted=False)
        with torch.inference_mode():
            baseline = layer.gate(x)
            assert self.hooks.hook(0)(layer.gate, (x,), baseline) is baseline
            bias = torch.zeros(
                len(self.hooks.gates), 128, device=device, dtype=torch.bfloat16
            )
            promoted = int(baseline[0][0].argmin())
            bias[0, promoted] = 100
            self.hooks.bias = bias
            changed = layer.gate(x)
            self.hooks.bias = None
            assert not torch.equal(baseline[2], changed[2])
            assert all(
                torch.equal(a, b) for a, b in zip(baseline, layer.gate(x), strict=True)
            )
            ref_off = layer.experts(x, baseline[2], baseline[1])
            ref_on = layer.experts(x, changed[2], changed[1])
            assert not torch.equal(ref_off, ref_on)
            if available:
                try:
                    self.model.set_experts_implementation("grouped_mm")
                    fast_off = layer.experts(x, baseline[2], baseline[1])
                    fast_on = layer.experts(x, changed[2], changed[1])
                    for a, b in ((ref_off, fast_off), (ref_on, fast_on)):
                        relative = float(
                            (a.float() - b.float()).norm()
                            / a.float().norm().clamp_min(1e-9)
                        )
                        assert relative < 0.03, relative
                    assert not torch.equal(fast_off, fast_on)
                    assert torch.equal(
                        fast_off, layer.experts(x, baseline[2], baseline[1])
                    )
                    evidence.update(adopted=True, relative_error=relative)
                except (RuntimeError, AssertionError, ValueError) as exc:
                    self.model.set_experts_implementation("eager")
                    evidence["rejection"] = str(exc)
            # Real model OFF with/without hooks, then nonzero actuation.
            tokens = torch.tensor([[1, 2, 3]], device=device)
            self.hooks.close()
            baseline_logits = self.model(tokens, use_cache=False).logits
            self.hooks = RouterHooks(
                [layer.mlp.gate for layer in self.model.model.layers]
            )
            assert torch.equal(
                baseline_logits, self.model(tokens, use_cache=False).logits
            )
            self.hooks.bias = bias
            assert not torch.equal(
                baseline_logits, self.model(tokens, use_cache=False).logits
            )
            self.hooks.bias = None
        evidence.update(
            experts_implementation=self.model.get_experts_implementation(),
            nonzero_dispatch_verified=True,
            exact_off_next_logits=True,
        )
        return evidence

    def throughput_pilot(self, journal, rows):
        evidence = self.verify_kernel()
        write_json(OUT / "kernel.json", evidence)
        measurements = []
        for i in range(3):
            messages = [
                dict(role="system", content="Continue the requested sequence."),
                dict(
                    role="user",
                    content=f"Write the integers from {i + 1} through 1000, separated by commas.",
                ),
            ]
            rec, _ = self.generate(messages, cap=128, force_length=True)
            rec.update(
                phase="pilot",
                arm="OFF",
                step="PILOT",
                episode=i,
                task_id=f"pilot_{i}",
                forced_length=True,
                target=None,
                bias_active=False,
                cue=None,
            )
            assert len(rec["generated_token_ids"]) == 128
            rec["tokens_per_second"] = 128 / rec["seconds"]
            measurements.append(rec["tokens_per_second"])
            append_record(journal, rows, rec)
            print(
                json.dumps(
                    dict(event="pilot", trial=i, tokens_per_second=measurements[-1])
                ),
                flush=True,
            )
        # A capped retained episode is <=2048 input tokens on these short carriers.
        ids = self.tokenizer.encode(
            "A neutral unrelated sentence. " * 600, add_special_tokens=False
        )[:2048]
        started = time.monotonic()
        with self.torch.inference_mode():
            self.model(
                input_ids=self.torch.tensor([ids], device="cuda"),
                use_cache=False,
                logits_to_keep=1,
            )
        self.torch.cuda.synchronize()
        prefill = time.monotonic() - started
        elapsed = time.monotonic() - self.start
        full = cost_projection(min(measurements), prefill, elapsed)
        scaled = cost_projection(min(measurements), prefill, elapsed, True)
        decision = full if full["fits"] else scaled
        report = dict(
            trials_tps=measurements,
            conservative_tps=min(measurements),
            prefill_tokens=len(ids),
            prefill_seconds=prefill,
            full=full,
            scaled=scaled,
            selected=decision,
            kernel=evidence,
        )
        write_json(OUT / "throughput.json", report)
        amendment = (
            "\n## Measured throughput decision (before competence/profiles)\n\n"
            + json.dumps(report, indent=2)
            + "\n"
        )
        with (OUT / "README.md").open("a") as f:
            f.write(amendment)
        with (OUT / "run-decisions.md").open("a") as f:
            f.write(amendment)
        if not decision["fits"]:
            raise BudgetStop(
                f"COST STOP: measured {min(measurements):.3f} tokens/s; full {full['seconds'] / 3600:.2f} h; scaled {scaled['seconds'] / 3600:.2f} h exceed 4 GPU-h"
            )
        return decision

    def profile(self, task, lang):
        if time.monotonic() >= self.deadline - 30:
            raise BudgetStop("Profile reserve")
        torch = self.torch
        messages = messages_for(task, lang)
        ids = self.tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            return_dict=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        answer = self.tokenizer.encode(canonical(task, lang), add_special_tokens=False)
        h = self.hooks
        h.bias = None
        result = {}
        started = time.monotonic()
        for label, positions in (
            ("suffix", slice(len(ids) - 8, len(ids))),
            ("answer", slice(len(ids), len(ids) + len(answer))),
        ):
            h.reset_capture()
            h.capture = True
            h.capture_slice = positions
            with torch.inference_mode():
                self.model(
                    input_ids=torch.tensor([ids + answer], device="cuda"),
                    use_cache=False,
                    logits_to_keep=1,
                )
            h.capture = False
            h.capture_slice = None
            count = h.counts[0]
            assert all(n == count for n in h.counts)
            result[label] = dict(
                logits=h.sums.cpu() / count,
                frequencies=h.freqs.cpu() / count,
                mass=h.mass.cpu() / count,
                sd=h.sd.cpu() / count,
                margin=h.margin.cpu() / count,
                count=count,
            )
        result.update(
            prompt_ids=ids,
            answer_ids=answer,
            suffix_ids=ids[-8:],
            canonical=canonical(task, lang),
            seconds=time.monotonic() - started,
        )
        return result


def append_record(journal, rows, record):
    required = {
        "phase",
        "arm",
        "task_id",
        "input_token_ids",
        "generated_token_ids",
        "seconds",
    }
    assert required <= record.keys(), required - record.keys()
    assert isinstance(record["input_token_ids"], list) and all(
        isinstance(t, int) for t in record["input_token_ids"]
    )
    assert record["input_token_ids"], "Empty input provenance"
    if record["phase"] == "profile":
        assert {
            "teacher_forced_token_ids",
            "suffix_ids",
            "canonical",
            "artifact",
        } <= record.keys()
    else:
        assert {
            "text",
            "eos",
            "truncated",
            "cost_stopped",
            "history",
            "input_sha256",
        } <= record.keys()
    journal.write(json.dumps(record) + "\n")
    journal.flush()
    rows.append(record)


def cost_projection(tps, prefill_seconds, elapsed, scaled=False):
    n = 32 if scaled else 64
    grid_cells = 2 if scaled else 8
    # Both pairs screened for competence/profile; only one actuator grid and final.
    competence_requests = 2 * 32 * 3
    profile_forwards = 2 * 32 * 2 * 2
    grid_requests = grid_cells * 16 * 2
    final_requests = n * (5 * 6 + 1)
    generation_requests = competence_requests + grid_requests + final_requests
    decode_tokens = generation_requests * CAP
    seconds = elapsed + 1.25 * (
        decode_tokens / tps + (generation_requests + profile_forwards) * prefill_seconds
    )
    return dict(
        scaled=scaled,
        episodes=n,
        alpha=[1, 4] if scaled else [0.5, 1, 2, 4],
        layers=["all"] if scaled else ["all", "upper_half"],
        competence_requests=competence_requests,
        profile_forwards=profile_forwards,
        grid_requests=grid_requests,
        final_requests=final_requests,
        capped_decode_tokens=decode_tokens,
        seconds=seconds,
        fits=seconds <= GPU_SECONDS,
    )


def messages_for(task, cue=None, history=None):
    content = task["prompt"]
    if cue == "English":
        content += ' Use controlled English: describe the expression recursively as "the sum of (X) and (Y)", "the difference of (X) and (Y)", or "the product of (X) and (Y)"; leaves are integer digits. No code or numerical simplification.'
    elif cue:
        content += f" Use {cue}."
    return list(history or [dict(role="system", content=SYSTEM)]) + [
        dict(role="user", content=content + SUFFIX)
    ]


def summarize(rows, eligibility=None):
    screen = [r for r in rows if r["phase"] == "screen" and r["step"] != "NEUTRAL"]
    defaults = {r["task_id"]: r for r in rows if r["phase"] == "fresh_default"}
    arms = {}
    for arm in ARMS:
        rs = [r for r in screen if r["arm"] == arm]
        steps = {}
        for step in TARGETS:
            if step == "NEUTRAL":
                continue
            selected = [r for r in rs if r["step"] == step]
            steps[step] = dict(
                n=len(selected),
                fixed_n=64,
                language_identity=dict(
                    Counter(r["score"]["language"] for r in selected)
                ),
                valid_languages=dict(
                    Counter(r["score"]["valid_language"] or "broken" for r in selected)
                ),
                success=sum(
                    r["score"]["valid_language"] == TARGETS[step] for r in selected
                )
                if TARGETS[step]
                else None,
                task_check=sum(r["score"]["valid_task"] for r in selected),
                target_task_check=sum(
                    r["score"]["valid_task"]
                    and r["score"]["valid_language"] == TARGETS[step]
                    for r in selected
                )
                if TARGETS[step]
                else None,
                broken=sum(r["score"]["broken"] for r in selected),
            )
        clears = [r for r in rs if r["step"] == "CLEAR"]
        paired = [
            (r, defaults[r["task_id"]]) for r in clears if r["task_id"] in defaults
        ]
        arms[arm] = dict(
            steps=steps,
            broken_episodes=len({r["episode"] for r in rs if r["score"]["broken"]}),
            clear_pairs=len(paired),
            clear_default_python=sum(
                d["score"]["valid_language"] == LANGS[0] for _, d in paired
            ),
            clear_impositions=sum(
                r["score"]["valid_language"] == LANGS[1]
                and d["score"]["valid_language"] == LANGS[0]
                for r, d in paired
            ),
        )
    complete = (
        all(s["n"] == 64 for a in arms.values() for s in a["steps"].values())
        and len(defaults) == 64
    )
    correct = arms["correct"]
    shuf = max(
        arms["shuffled"]["steps"][s]["valid_languages"].get(LANGS[1], 0)
        for s in ("SET", "HOLD", "SWITCH", "BACK")
    )
    possible = (
        complete
        and correct["steps"]["SET"]["success"] >= 40
        and correct["steps"]["SWITCH"]["success"] >= 40
        and correct["broken_episodes"] <= 4
        and shuf <= 8
        and correct["clear_impositions"] <= 8
    )
    verdict = (
        "INELIGIBLE"
        if eligibility
        else "PARTIAL"
        if not complete
        else "POSSIBLE"
        if possible
        else "MARGINAL"
        if correct["steps"]["SET"]["success"] >= 24
        else "NOT POSSIBLE"
    )
    return dict(
        verdict=verdict,
        ineligible_reason=eligibility,
        complete=complete,
        arms=arms,
        shuffled_worst_stage_javascript=shuf,
        record_count=len(rows),
        fixed_n=64,
    )


def save_report(summary):
    write_json(OUT / "summary.json", summary)
    lines = [
        "## Observed results",
        "",
        f"**{summary['verdict']}**; complete screen: {summary['complete']}; GPU allocation: {summary.get('gpu_seconds', 0):.2f} seconds / 14400.",
        "",
    ]
    if summary.get("stop_reason"):
        lines += [str(summary["stop_reason"]), ""]
    if summary.get("ineligible_reason"):
        lines += [str(summary["ineligible_reason"]), ""]
    lines += [
        "| Arm | SET | HOLD | SWITCH | BACK | Broken episodes | CLEAR impositions / paired defaults |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for arm, a in summary["arms"].items():
        s = a["steps"]
        lines.append(
            f"| {arm} | "
            + " | ".join(
                f"{s[x]['success']}/64 (n={s[x]['n']})"
                for x in ("SET", "HOLD", "SWITCH", "BACK")
            )
            + f" | {a['broken_episodes']}/64 | {a['clear_impositions']}/64 ({a['clear_default_python']} Python-default pairs) |"
        )
    lines += [
        "",
        "| Arm/stage | Valid coarse task | Target language + task | Broken | Language identity counts |",
        "|---|---:|---:|---:|---|",
    ]
    for arm, a in summary["arms"].items():
        for step, s in a["steps"].items():
            lines.append(
                f"| {arm}/{step} | {s['task_check']}/64 | {s['target_task_check']} | {s['broken']}/64 | {json.dumps(s['language_identity'])} |"
            )
    if "competence" in summary:
        lines += [
            "",
            "Competence and cue-absent default distribution:",
            "",
            "```json",
            json.dumps(summary["competence"], indent=2),
            "```",
        ]
    if (OUT / "profile-statistics.json").exists():
        stats = json.loads((OUT / "profile-statistics.json").read_text())
        lines += [
            "",
            "| Layer | Raw logit RMS distance | Frequency L1 | Top-8 overlap |",
            "|---|---:|---:|---:|",
        ]
        lines += [
            f"| {r['layer']} | {r['logit_rms_distance']:.6f} | {r['frequency_l1_distance']:.6f} | {r['overlap']:.3f} |"
            for r in stats["layers"]
        ]
    conclusions = {
        "POSSIBLE": "A fixed router bias can select these two output modes under this quick-check reading. This does not establish an automatic skill controller or semantic task correctness.",
        "MARGINAL": "Some language steering appeared, but the full feasibility criteria were not met.",
        "NOT POSSIBLE": "This brute-force router-bias construction did not reach the pre-written feasibility threshold.",
        "INELIGIBLE": "The setup gate failed, so this run cannot decide whether routing bias can reliably address these languages.",
        "PARTIAL": "The screen is incomplete. The saved prefix cannot decide feasibility; no full-screen claim is made.",
    }
    if (OUT / "run-decisions.md").exists():
        lines += [(OUT / "run-decisions.md").read_text()]
    lines += [
        "",
        conclusions[summary["verdict"]],
        "",
        "Raw parser decisions, coarse task flags, token IDs, full histories, and timings are in records.jsonl. No generated program was executed.",
        "",
    ]
    (OUT / "README.md").write_text(
        (OUT / "prewritten-reading.md").read_text().split("\n## Results\n", 1)[0]
        + "\n\n"
        + "\n".join(lines)
    )


def run(weights):
    import torch

    assert not gpu_pids() and not downloaders(), "Resources changed after wait"
    assert not (OUT / "records.jsonl").exists(), (
        "Refuse rerun / overwrite of model outcomes"
    )
    manifest = json.loads((OUT / "freeze.json").read_text())
    for name, digest in manifest["files"].items():
        assert sha(ROOT / name) == digest, f"Pre-outcome freeze drift: {name}"
    cpu = json.loads((OUT / "cpu.json").read_text())
    for path, digest in cpu["source_hashes"].items():
        assert sha(Path(path)) == digest, f"Dependency source drift: {path}"
    write_json(OUT / "weights.json", weights)
    b = json.loads((OUT / "banks.json").read_text())
    rows, competence, eligibility, stop_reason = [], {}, None, None
    start = time.monotonic()
    engine = None
    journal = (OUT / "records.jsonl").open("x")

    def request(
        task,
        phase,
        arm,
        step,
        episode,
        cue=None,
        bias=None,
        history=None,
        capture=False,
        session=None,
    ):
        neutral = step == "NEUTRAL"
        messages = messages_for(task, cue, history)
        rec, prof = engine.generate(messages, bias, capture, session=session)
        rec.update(
            phase=phase,
            arm=arm,
            step=step,
            episode=episode,
            task_id=task["id"],
            cue=cue,
            bias_active=bias is not None,
            target=TARGETS.get(step),
            pair=list(LANGS),
        )
        rec["score"] = (
            score(rec["text"], task, rec["truncated"] or rec["cost_stopped"])
            if not neutral
            else dict(neutral_ok=rec["text"].strip() == "OK")
        )
        if prof is not None:
            profile_path = OUT / "profiles-by-task" / f"{arm}-{task['id']}.pt"
            profile_path.parent.mkdir(exist_ok=True)
            torch.save(prof, profile_path)
        append_record(journal, rows, rec)
        print(
            json.dumps(
                dict(
                    event="record",
                    n=len(rows),
                    phase=phase,
                    arm=arm,
                    step=step,
                    episode=episode,
                    language=rec["score"].get("language"),
                    seconds=round(rec["seconds"], 2),
                    elapsed=round(time.monotonic() - start, 1),
                )
            ),
            flush=True,
        )
        if rec["cost_stopped"]:
            raise BudgetStop("Cooperative per-token deadline")
        return rec, prof

    def admit_remaining(label, remaining_requests):
        pilot = json.loads((OUT / "throughput.json").read_text())
        rates = [
            len(r["generated_token_ids"]) / r["seconds"]
            for r in rows
            if len(r.get("generated_token_ids", [])) >= 64 and r["seconds"] > 0
        ]
        rate = min([pilot["conservative_tps"]] + rates)
        projected = (
            time.monotonic()
            - start
            + 1.25 * remaining_requests * (CAP / rate + pilot["prefill_seconds"])
        )
        report = dict(
            stage=label,
            remaining_requests=remaining_requests,
            tokens_per_second=rate,
            projected_seconds=projected,
        )
        with (OUT / "run-decisions.md").open("a") as f:
            f.write("\nRemaining-cost check: " + json.dumps(report) + "\n")
        if projected > GPU_SECONDS:
            raise BudgetStop(
                f"COST STOP before {label}: remaining projection {projected / 3600:.2f} h"
            )

    try:
        engine = Engine(start)
        write_json(
            OUT / "runtime.json",
            dict(
                torch=torch.__version__,
                load_seconds=engine.load_seconds,
                device_map=engine.model.hf_device_map,
                model_class=type(engine.model).__name__,
                dtype=str(engine.model.dtype),
                eos=sorted(engine.eos),
                seed=SEED,
            ),
        )
        decision = engine.throughput_pilot(journal, rows)
        candidates = []
        for pair_index, pair in enumerate(PAIRS):
            set_pair(pair)
            phase = f"competence_pair{pair_index}"
            for i, task in enumerate(b["competence"]):
                for lang in (*LANGS, None):
                    request(task, phase, lang or "OFF", "SET", i, cue=lang)
            metrics = {}
            for lang in LANGS:
                rs = [r for r in rows if r["phase"] == phase and r["arm"] == lang]
                metrics[lang] = dict(
                    valid=sum(r["score"]["valid_language"] == lang for r in rs),
                    task_check=sum(
                        r["score"]["valid_task"]
                        and r["score"]["valid_language"] == lang
                        for r in rs
                    ),
                    n=len(rs),
                )
            metrics["default"] = dict(
                Counter(
                    r["score"]["language"]
                    for r in rows
                    if r["phase"] == phase and r["arm"] == "OFF"
                )
            )
            competence["/".join(pair)] = metrics
            write_json(OUT / "competence.json", competence)
            candidate = dict(
                pair=list(pair),
                competent=all(metrics[lang]["valid"] >= 28 for lang in LANGS),
            )
            candidates.append(candidate)
            if not candidate["competent"]:
                continue
            per_task = []
            for lang in LANGS:
                for i, task in enumerate(b["profile"]):
                    prof = engine.profile(task, lang)
                    per_task.append(dict(language=lang, task_id=task["id"], **prof))
                    path = (
                        OUT
                        / "profiles-by-task"
                        / f"pair{pair_index}-{lang}-{task['id']}.pt"
                    )
                    path.parent.mkdir(exist_ok=True)
                    torch.save(per_task[-1], path)
                    rec = dict(
                        phase="profile",
                        arm=lang,
                        pair=list(pair),
                        task_id=task["id"],
                        input_token_ids=prof["prompt_ids"],
                        generated_token_ids=[],
                        teacher_forced_token_ids=prof["answer_ids"],
                        suffix_ids=prof["suffix_ids"],
                        canonical=prof["canonical"],
                        seconds=prof["seconds"],
                        artifact=str(path.relative_to(ROOT)),
                    )
                    append_record(journal, rows, rec)
                    print(
                        json.dumps(
                            dict(event="profile", pair=pair, language=lang, task=i)
                        ),
                        flush=True,
                    )
            for i in range(32):
                assert per_task[i]["suffix_ids"] == per_task[32 + i]["suffix_ids"], (
                    "Primary suffix must be identical across cues"
                )
            profiles = torch.stack(
                [
                    torch.stack(
                        [
                            r["suffix"]["logits"]
                            for r in per_task
                            if r["language"] == lang
                        ]
                    ).mean(0)
                    for lang in LANGS
                ]
            ).float()
            frequencies = torch.stack(
                [
                    torch.stack(
                        [
                            r["suffix"]["frequencies"]
                            for r in per_task
                            if r["language"] == lang
                        ]
                    ).mean(0)
                    for lang in LANGS
                ]
            ).float()
            sigma = torch.stack([r["suffix"]["sd"] for r in per_task]).mean(0).float()
            stats = profile_stats(profiles, frequencies)
            normal, shuffled = make_biases(frequencies * sigma[None, :, None])
            candidate.update(
                same_experts=stats["same_experts"],
                profile_path=f"pair{pair_index}-profiles.pt",
            )
            torch.save(
                dict(
                    languages=LANGS,
                    logits=profiles,
                    frequencies=frequencies,
                    sigma=sigma,
                    normal=normal,
                    shuffled=shuffled,
                    per_task=per_task,
                ),
                OUT / candidate["profile_path"],
            )
            write_json(OUT / f"pair{pair_index}-profile-statistics.json", stats)
        eligible = [
            c for c in candidates if c["competent"] and not c.get("same_experts", True)
        ]
        write_json(
            OUT / "pair-selection.json",
            dict(candidates=candidates, selected=eligible[0] if eligible else None),
        )
        if not eligible:
            eligibility = "No candidate passes 28/32 competence in both modes and pre-written top-8 overlap gate"
            return
        selected_pair = eligible[0]
        set_pair(selected_pair["pair"])
        frozen = torch.load(OUT / selected_pair["profile_path"], weights_only=False)
        normal, shuffled = frozen["normal"], frozen["shuffled"]
        torch.save(frozen, OUT / "profiles.pt")
        stats = profile_stats(frozen["logits"], frozen["frequencies"])
        write_json(OUT / "profile-statistics.json", stats)
        torch.save(
            dict(
                languages=LANGS,
                centered=normal,
                shuffled=shuffled,
                random_seed=SEED + 2,
            ),
            OUT / "biases.pt",
        )
        admit_remaining("grid", decision["grid_requests"] + decision["final_requests"])
        grid = []
        for alpha in decision["alpha"]:
            for layers in decision["layers"]:
                directions = normal * alpha
                if layers == "upper_half":
                    directions[:, : directions.shape[1] // 2] = 0
                successes = dict.fromkeys(LANGS, 0)
                broken = 0
                for i, task in enumerate(b["grid"]):
                    for j, lang in enumerate(LANGS):
                        rec, _ = request(
                            task,
                            "grid",
                            f"{alpha}/{layers}/{lang}",
                            "SET",
                            i,
                            bias=directions[j],
                        )
                        successes[lang] += rec["score"]["valid_language"] == lang
                        broken += rec["score"]["broken"]
                grid.append(
                    dict(alpha=alpha, layers=layers, successes=successes, broken=broken)
                )
                write_json(OUT / "grid.json", dict(cells=grid, frozen=False))
        selected = choose_grid(grid)
        write_json(
            OUT / "grid.json",
            dict(
                cells=grid, selected=selected, frozen=True, screen_records_at_freeze=0
            ),
        )
        for directions in (normal, shuffled):
            directions *= selected["alpha"]
            if selected["layers"] == "upper_half":
                directions[:, : directions.shape[1] // 2] = 0
        torch.save(
            dict(correct=normal, shuffled=shuffled, selected=selected),
            OUT / "frozen-biases.pt",
        )
        admit_remaining("screen", decision["final_requests"])
        # Paired fresh defaults must be observed for each episode even in a stopped prefix.
        neutral = dict(id="neutral", prompt="Reply only OK.", name="", witness="")
        for e in range(decision["episodes"]):
            task_indices = dict(
                zip(
                    ("SET", "HOLD", "SWITCH", "BACK", "CLEAR"),
                    ((e + offset) % 64 for offset in (0, 13, 26, 39, 52)),
                    strict=True,
                )
            )
            request(
                b["screen"][task_indices["CLEAR"]], "fresh_default", "OFF", "CLEAR", e
            )
            for arm in ARMS:
                history = [dict(role="system", content=SYSTEM)]
                session = {}
                for step in STEPS:
                    task = (
                        neutral
                        if step == "NEUTRAL"
                        else b["screen"][task_indices[step]]
                    )
                    lang = LANGS[1] if step == "NEUTRAL" else TARGETS[step]
                    bias = cue = None
                    if lang and arm in ("correct", "swapped", "shuffled"):
                        j = LANGS.index(lang)
                        bias = (
                            shuffled[j]
                            if arm == "shuffled"
                            else normal[1 - j if arm == "swapped" else j]
                        )
                    if arm == "text-cue" and step != "NEUTRAL":
                        cue = lang
                    rec, _ = request(
                        task,
                        "screen",
                        arm,
                        step,
                        e,
                        cue=cue,
                        bias=bias,
                        history=history,
                        session=session,
                    )
                    history = rec["history"] + [
                        dict(role="assistant", content=rec["text"])
                    ]
            partial = summarize(rows)
            partial.update(
                competence=competence,
                gpu_seconds=time.monotonic() - start,
                stop_reason="RUNNING",
            )
            write_json(OUT / "summary.json", partial)
    except BudgetStop as exc:
        stop_reason = str(exc)
    except Exception as exc:
        stop_reason = f"ERROR {type(exc).__name__}: {exc}"
        raise
    finally:
        journal.close()
        elapsed = time.monotonic() - start
        summary = summarize(rows, eligibility)
        summary.update(
            competence=competence,
            selected_pair=list(LANGS),
            gpu_seconds=elapsed,
            gpu_cap_seconds=GPU_SECONDS,
            cap_overrun_seconds=max(0, elapsed - GPU_SECONDS),
            stop_reason=stop_reason,
            peak_memory_bytes=torch.cuda.max_memory_allocated()
            if engine is not None
            else None,
            freeze_sha256=sha(OUT / "freeze.json"),
        )
        save_report(summary)
        if engine is not None:
            engine.hooks.close()
        print(json.dumps(summary), flush=True)


def cpu_tests():
    import torch
    from transformers import Qwen3MoeConfig
    from transformers.models.qwen3_moe.modeling_qwen3_moe import Qwen3MoeTopKRouter

    checks = []
    cfg = Qwen3MoeConfig(
        hidden_size=4, num_experts=4, num_experts_per_tok=2, norm_topk_prob=True
    )
    gate = Qwen3MoeTopKRouter(cfg)
    with torch.no_grad():
        gate.weight.copy_(torch.eye(4))
    x = torch.tensor([[4.0, 3.0, 2.0, 1.0]])
    original = gate(x)
    h = RouterHooks([gate])
    off = gate(x)
    assert all(torch.equal(a, b) for a, b in zip(original, off, strict=True))
    assert h.hook(0)(gate, (x,), original) is original
    h.bias = torch.tensor([[0.0, 0.0, 0.0, 10.0]])
    biased = gate(x)
    assert 3 in biased[2][0].tolist() and 3 not in original[2][0].tolist()
    # Actual tuple-consuming weighted fake experts, not just hook output inspection.
    values = torch.tensor([1.0, 10.0, 100.0, 1000.0])

    def consume(output):
        return (values[output[2]] * output[1]).sum(-1)

    assert not torch.equal(consume(original), consume(biased))
    assert torch.allclose(biased[1].sum(-1), torch.ones(1))
    h.bias = None
    assert torch.equal(consume(gate(x)), consume(original))
    h.reset_capture()
    gate(torch.cat((x, x)))
    assert h.counts == [0]
    h.capture = True
    gate(x)
    gate(x * 2)
    assert h.counts == [2] and torch.equal(h.sums[0], (x * 3).double()[0])
    assert h.freqs.sum() == 4
    h.close()
    checks += [
        "actual router tuple consumer changes under bias; OFF restores exactly",
        "capture excludes prefill and counts generated positions",
    ]
    profiles = torch.randn(2, 4, 8, generator=torch.Generator().manual_seed(1))
    normal, shuf = make_biases(profiles)
    assert torch.allclose(normal.norm(dim=-1), shuf.norm(dim=-1))
    assert torch.allclose(normal[0], -normal[1], atol=1e-6)
    assert torch.equal(shuf, make_biases(profiles)[1])
    assert torch.allclose(shuf[0], -shuf[1], atol=1e-6)
    assert torch.equal(normal, profiles - profiles.mean(0, keepdim=True))
    zero, rz = make_biases(torch.ones_like(profiles))
    assert torch.count_nonzero(zero) == torch.count_nonzero(rz) == 0
    checks += [
        "unamplified centered directions; deterministic expert permutations preserve opposition/norm; zero difference safe"
    ]
    task = dict(name="square", witness=r"\*")
    samples = [
        ("def square(x):\n    return x*x", "Python", True, False),
        ("function square(x) { return x*x; }", "JavaScript", True, False),
        ("```javascript\ndef square(x):\n    return x*x\n```", "Python", True, False),
        ("const square = x => x*x;", "JavaScript", True, False),
        ("def square(x):\n    pass", "Python", False, False),
        ("function square(x) { return x; }", "JavaScript", False, False),
        ("def unrelated(x):\n    return x*x", "Python", False, False),
        ("42", "ambiguous", False, True),
        ("", "invalid", False, True),
        ("```python\ndef square(x):\n    return x*x", "invalid", False, True),
        ("function square( {", "invalid", False, True),
    ]
    for text, lang, coarse, broken in samples:
        result = score(text, task)
        assert (result["language"], result["task_check"], result["broken"]) == (
            lang,
            coarse,
            broken,
        ), result
    assert score(samples[0][0], task, True)["broken"]
    assert score("def square(x):\n" + "    print(x)\n" * 6 + "    return x*x", task)[
        "flags"
    ]["repetitive"]
    checks += [
        "parser, misleading fence, JS arrow, stub, unrelated function, ambiguous, empty, syntax, truncation, repetition fixtures"
    ]
    b = bank()
    assert bank() == b
    assert all(len({(e + k) % 64 for k in (0, 13, 26, 39, 52)}) == 5 for e in range(64))
    cells = [
        dict(alpha=1, layers="all", successes=dict(Python=9, JavaScript=16), broken=0),
        dict(alpha=2, layers="all", successes=dict(Python=10, JavaScript=10), broken=3),
    ]
    assert choose_grid(cells)["alpha"] == 2
    assert summarize([])["verdict"] == "PARTIAL"
    assert summarize([], "competence")["verdict"] == "INELIGIBLE"
    # Summary consumer tests include all arms, paired counterfactual and exact thresholds.
    rows = []

    def fake(lang):
        return dict(language=lang, valid_language=lang, valid_task=True, broken=False)

    for e in range(64):
        rows.append(dict(phase="fresh_default", task_id=str(e), score=fake("Python")))
        for arm in ARMS:
            for step in ("SET", "HOLD", "SWITCH", "BACK", "CLEAR"):
                lang = (
                    "Python" if step == "CLEAR" or arm == "shuffled" else TARGETS[step]
                )
                rows.append(
                    dict(
                        phase="screen",
                        arm=arm,
                        episode=e,
                        step=step,
                        task_id=str(e),
                        score=fake(lang),
                    )
                )
    assert summarize(rows)["verdict"] == "POSSIBLE"
    for r in rows:
        if (
            r["phase"] == "screen"
            and r["arm"] == "correct"
            and r["step"] == "CLEAR"
            and r["episode"] < 9
        ):
            r["score"] = fake("JavaScript")
    assert summarize(rows)["verdict"] == "MARGINAL"
    checks += [
        "bank disjointness, history rotations, grid priority, partial verdict, exact summary thresholds, paired CLEAR impositions"
    ]
    with tempfile.TemporaryDirectory() as td:
        model = Path(td)
        write_json(model / "config.json", dict(model_type="qwen3_moe"))
        write_json(model / "tokenizer.json", {})
        write_json(model / "tokenizer_config.json", {})
        write_json(
            model / "model.safetensors.index.json",
            dict(metadata=dict(total_size=4), weight_map=dict(x="shard.safetensors")),
        )
        assert not weights_ready(model)["ready"]
        header = json.dumps(
            dict(x=dict(dtype="F32", shape=[1], data_offsets=[0, 4]))
        ).encode()
        blob = struct.pack("<Q", len(header)) + header + struct.pack("<f", 1.0)
        (model / "shard.safetensors").write_bytes(blob)
        assert weights_ready(model, hashes=True)["ready"]
        (model / "shard.safetensors").write_bytes(blob[:-1])
        assert not weights_ready(model)["ready"]
    checks += [
        "weight-index membership, exact safetensors byte lengths, missing and truncated shard fixtures"
    ]
    eb = expression_bank()
    assert {t["family"] for t in eb["profile"]}.isdisjoint(
        t["family"] for t in eb["screen"]
    )
    for split in eb.values():
        for task in split:
            expected = ast.dump(ast.parse(task["expression"], mode="eval").body)
            assert ast.dump(parse_english(canonical(task, "English"))) == expected
    for task in [split[0] for split in eb.values()]:
        for lang in ("Python", "English", "JavaScript"):
            checked = score(canonical(task, lang), task)
            assert checked["valid_language"] == lang and checked["valid_task"], checked
        wrong = canonical(task, "English").replace("the ", "wrong ", 1)
        assert score(wrong, task)["broken"]
    assert cost_projection(2, 1, 60)["fits"] is False
    assert cost_projection(2, 1, 60, True)["fits"] is False
    assert cost_projection(1000, 0.01, 60)["fits"] is True
    assert (
        cost_projection(10, 1, 60, True)["seconds"]
        < cost_projection(10, 1, 60)["seconds"]
    )
    # Capture ONLY selected suffix positions, with equal-example means and SD.
    gate = Qwen3MoeTopKRouter(cfg)
    with torch.no_grad():
        gate.weight.copy_(torch.eye(4))
    hook = RouterHooks([gate])
    hook.reset_capture()
    hook.capture = True
    hook.capture_slice = slice(1, 3)
    obs = torch.tensor(
        [[100.0, 0, 0, 0], [1.0, 2, 3, 4], [4.0, 3, 2, 1], [0.0, 0, 0, 100]]
    )
    gate(obs)
    assert hook.counts == [2]
    assert torch.equal(hook.sums[0], obs[1:3].double().sum(0))
    assert torch.allclose(hook.sd[0], obs[1:3].std(-1, correction=0).double().sum())
    hook.close()
    checks += [
        "arithmetic lineage/canonical grammar and operands; cost refusal/scaling; suffix-only capture with logit SD"
    ]
    # Tiny random HF model checks the real checkpoint/device-map/consumer path on CPU.
    from transformers import Qwen3MoeForCausalLM

    tiny_cfg = Qwen3MoeConfig(
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
        norm_topk_prob=True,
    )
    torch.manual_seed(SEED)
    with tempfile.TemporaryDirectory() as td:
        Qwen3MoeForCausalLM(tiny_cfg).save_pretrained(td)
        tiny = Qwen3MoeForCausalLM.from_pretrained(
            td, device_map={"": "cpu"}, dtype=torch.bfloat16, attn_implementation="sdpa"
        ).eval()
        tokens = torch.tensor([[1, 2, 3]])
        with torch.inference_mode():
            baseline = tiny(tokens).logits
            hooks = RouterHooks([layer.mlp.gate for layer in tiny.model.layers])
            assert torch.equal(tiny(tokens).logits, baseline)
            hooks.bias = torch.tensor([[0.0, 0.0, 0.0, 10.0]] * 2, dtype=torch.bfloat16)
            assert not torch.equal(tiny(tokens).logits, baseline)
            hooks.bias = None
            assert torch.equal(tiny(tokens).logits, baseline)
            hooks.close()

            class FixtureTokenizer:
                def encode(self, text, add_special_tokens=False):
                    return [4] if text == "\n" else [10 + ord(c) % 32 for c in text]

                def decode(self, ids, skip_special_tokens=True):
                    return "fixture answer"

                def convert_tokens_to_ids(self, token):
                    return 3

                def apply_chat_template(self, messages, **kwargs):
                    ids = []
                    for message in messages:
                        ids += (
                            [2]
                            + self.encode(message["role"] + message["content"])
                            + [3, 4]
                        )
                    return ids + ([5, 6] if kwargs.get("add_generation_prompt") else [])

            engine = Engine.__new__(Engine)
            engine.torch = torch
            engine.device = torch.device("cpu")
            engine.model = tiny
            engine.tokenizer = FixtureTokenizer()
            engine.eos = {3}
            engine.hooks = RouterHooks([layer.mlp.gate for layer in tiny.model.layers])
            engine.deadline = time.monotonic() + 600
            session = {}
            messages = [dict(role="user", content="a")]
            first, _ = engine.generate(
                messages, session=session, cap=4, force_length=True
            )
            old_ids = list(session["token_ids"])
            old_keys = session["past"].layers[0].keys.clone()
            messages += [
                dict(role="assistant", content=first["text"]),
                dict(role="user", content="b"),
            ]
            second, _ = engine.generate(
                messages,
                bias=torch.tensor([[0.0, 0.0, 0.0, 10.0]] * 2),
                session=session,
                cap=4,
                force_length=True,
            )
            assert second["cache_prefix_token_ids"] == old_ids
            assert torch.equal(
                old_keys, session["past"].layers[0].keys[:, :, : old_keys.shape[-2]]
            )
            assert first["appended_terminal_token_ids"] == [3]
            engine.eos = set(range(64))
            natural, _ = engine.generate(
                [dict(role="user", content="c")], session={}, cap=4
            )
            assert (
                natural["eos"]
                and len(natural["generated_token_ids"]) == 1
                and not natural["appended_terminal_token_ids"]
            )
            engine.hooks.close()
    checks += [
        "actual tiny model incremental KV preserves old keys under switched bias; final sampled token consumed; truncated and natural-EOS paths"
    ]
    checks += [
        "tiny random HF checkpoint loads with bf16/device_map; actual MoE model bias changes logits; exact OFF restoration"
    ]
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(MODEL, local_files_only=True)
    task = eb["profile"][0]
    tokenizations = [
        tokenizer.apply_chat_template(
            messages_for(task, lang),
            tokenize=True,
            return_dict=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        for lang in ("Python", "English", "JavaScript")
    ]
    assert isinstance(tokenizations[0], list)
    assert tokenizations[0][-8:] == tokenizations[1][-8:] == tokenizations[2][-8:]
    history = messages_for(task) + [
        dict(role="assistant", content=canonical(task, "Python"))
    ]
    prefix = tokenizer.apply_chat_template(
        history,
        tokenize=True,
        return_dict=False,
        add_generation_prompt=False,
        enable_thinking=False,
    )
    combined = tokenizer.apply_chat_template(
        messages_for(task, history=history),
        tokenize=True,
        return_dict=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )
    new_turn = tokenizer.apply_chat_template(
        [messages_for(task)[-1]],
        tokenize=True,
        return_dict=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )
    assert combined[-len(new_turn) :] == new_turn
    # The old rendering really changes; never use it to replace actual old KV.
    assert combined[: len(prefix)] != prefix
    assert tokenizer.decode(prefix[-2:]) == "<|im_end|>\n"
    import io

    journal = io.StringIO()
    records = []
    fake_record = dict(
        phase="pilot",
        arm="OFF",
        task_id="cpu_fixture",
        input_token_ids=[1],
        generated_token_ids=[2],
        seconds=0.1,
        text="test",
        eos=False,
        truncated=True,
        cost_stopped=False,
        history=[],
        input_sha256="fixture",
    )
    append_record(journal, records, fake_record)
    assert json.loads(journal.getvalue()) == fake_record and records == [fake_record]
    try:
        append_record(journal, records, {"phase": "pilot"})
        raise RuntimeError("Writer accepted missing raw fields")
    except AssertionError:
        pass
    checks += [
        "local tokenizer explicit list return, identical suffix, standalone new-turn template/terminal and historical re-render trap; same-run raw writer contract"
    ]
    import accelerate
    import transformers

    return dict(
        accelerate=accelerate.__version__,
        passed=checks,
        count=len(checks),
        node=subprocess.check_output(["node", "--version"], text=True).strip(),
        python=sys.version,
        go=shutil.which("go"),
        transformers=transformers.__version__,
        router_source=inspect.getsource(Qwen3MoeTopKRouter),
        source_hashes={
            str(Path(inspect.getfile(obj)).resolve()): sha(Path(inspect.getfile(obj)))
            for obj in (
                Qwen3MoeTopKRouter,
                Qwen3MoeForCausalLM,
                __import__(
                    "transformers.integrations.moe",
                    fromlist=["grouped_mm_experts_forward"],
                ).grouped_mm_experts_forward,
            )
        },
        cuda_initialized=torch.cuda.is_initialized(),
    )


def prepare():
    assert shutil.which("node"), "Node parser required"
    assert not (OUT / "records.jsonl").exists(), "No edits after model outcomes"
    OUT.mkdir(parents=True, exist_ok=True)
    cpu = cpu_tests()
    assert not cpu["cuda_initialized"]
    write_json(OUT / "cpu.json", cpu)
    write_json(OUT / "banks.json", expression_bank())
    (OUT / "prewritten-reading.md").write_text(READING)
    (OUT / "README.md").write_text(READING)
    files = [
        "scripts/focus_check40.py",
        "results/quick-checks/check40/banks.json",
        "results/quick-checks/check40/prewritten-reading.md",
        "results/quick-checks/check40/cpu.json",
        "results/moe-routing-research-astra.md",
    ]
    write_json(
        OUT / "freeze.json",
        dict(
            seed=SEED,
            status="UNREGISTERED_PRE_OUTCOME_FREEZE",
            created_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            files={name: sha(ROOT / name) for name in files},
        ),
    )
    summary = summarize([])
    summary.update(
        stop_reason="PREPARED_WAITING_FOR_IDLE_GPU_AND_COMPLETE_WEIGHTS", gpu_seconds=0
    )
    write_json(OUT / "summary.json", summary)
    print(json.dumps(cpu), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode", choices=["prepare", "test", "status", "run", "analyze"], required=True
    )
    parser.add_argument("--wait", action="store_true")
    args = parser.parse_args()
    if args.mode == "test":
        print(json.dumps(cpu_tests(), indent=2))
    elif args.mode == "status":
        print(
            json.dumps(
                dict(
                    gpu_pids=gpu_pids(),
                    downloaders=downloaders(),
                    weights=weights_ready(),
                ),
                indent=2,
            )
        )
    elif args.mode == "prepare":
        with review_lock():
            prepare()
    elif args.mode == "analyze":
        with review_lock():
            rows = [
                json.loads(line)
                for line in (OUT / "records.jsonl").read_text().splitlines()
            ]
            existing = json.loads((OUT / "summary.json").read_text())
            set_pair(existing.get("selected_pair", LANGS))
            audit = summarize(rows, existing["ineligible_reason"])
            for key in audit:
                assert audit[key] == existing[key], (
                    f"Raw-record summary mismatch: {key}"
                )
            b = json.loads((OUT / "banks.json").read_text())
            tasks = {t["id"]: t for split in b.values() for t in split}
            for r in rows:
                if "score" in r and r["step"] != "NEUTRAL":
                    assert (
                        score(
                            r["text"],
                            tasks[r["task_id"]],
                            r["truncated"] or r["cost_stopped"],
                        )
                        == r["score"]
                    )
            write_json(
                OUT / "audit.json",
                dict(passed=True, rescored_records=len(rows), summary_exact=True),
            )
            print("Raw records rescored; summary exactly reproduced.")
    else:
        weights = wait_ready() if args.wait else weights_ready(hashes=True)
        assert weights["ready"] and not gpu_pids() and not downloaders()
        with review_lock():
            run(weights)


if __name__ == "__main__":
    main()
