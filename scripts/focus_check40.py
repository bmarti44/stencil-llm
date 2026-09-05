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
SYSTEM = "Answer the programming request with one concise code block defining the requested function. No examples or explanation."
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

READING = """# Check 40 — brute-force expert routing by programming language

Unregistered, disclosed quick check; Brian's 2026-09-05 brief. Seed 40040.
Fit-on: **none**. Profile extraction averages generated router observations on 32 synthetic cued tasks per language (paired task statements). Dose selection uses 16 separate synthetic tasks. Evaluated-on: 32 competence tasks and 64 fresh screen statements; all four exact-statement sets are disjoint. Task families recur across splits; no benchmark data, fitting, training, or sealed input access.

## Pre-written reading (frozen before any model output)

Competence: at least 28/32 cued, unambiguously parser-valid, unbroken responses in **each** language. Otherwise INELIGIBLE. Coarse task passes reported separately. Record uncued defaults on the same 32. Languages fixed to Python and JavaScript; Go is unavailable.

Profiles: unmodified bf16 router logits (fp64 sums, fp32 saved means) and top-8 selection frequencies at **every generated non-EOS token's own forward position**, including the last token; exclude all prompt and retained-history positions. Pool sums/counts across positions/tasks (longer answers carry more weight); also retain each task's sums/counts. No successful-answer filtering. Center each language against the two-language mean; normalize each layer's difference to RMS 1; multiply by alpha. Zero differences stay zero. Report raw-logit RMS distance, frequency L1 distance, and intersection/8 of each language's top-8 frequency experts per layer. Predefine near-total overlap as >=7/8 at **every** layer: INELIGIBLE, “same experts.” This is an operational top-k screen, not proof of identical routing.

Grid: alpha {0.5,1,2,4} x {all,upper half}; each cell generates both directions on the same independent 16 uncued setup tasks. Rank by both directions reaching >=10/16 valid, unbroken inductions; then lowest total breakage; then largest minimum directional successes; then largest total successes; then smaller alpha, then upper half. Even if no cell reaches both bars, freeze the best cell and perform the screen. Never select using screen outcomes.

Episodes: 64 screen statements; SET uses index e, HOLD e+13, SWITCH e+26, BACK e+39, CLEAR e+52 modulo 64. Thus five different tasks per episode; each statement occurs once at each stage across episodes. Shared task families/reuse limit independence; counts are descriptive. Every arm keeps complete actual user+assistant pairs. After SET generate a neutral “Reply only OK.” pair with bias kept, then HOLD, SWITCH, BACK, CLEAR. Re-render full history and recompute KV each turn; current bias affects **all** router positions in that forward, including history replay. No context eviction, no hidden cache transplant. CLEAR removes bias and supplies a new uncued task in retained history; no cancellation text. A separate fresh OFF response on its exact task defines the paired default.

Arms: correct maps L2/L1/L2 to JavaScript/Python/JavaScript; swapped reverses those addresses; shuffled uses two independent Gaussian directions, centered and matched to each active layer's bias norm, RNG seed 40042; OFF has zero bias; text-cue appends the corresponding language cue at SET/HOLD/SWITCH/BACK and none at CLEAR. Neutral has no language cue. For every arm, requested-language success is measured against the **correct** address, with actual-language counts alongside it. Fixed shuffled vectors, no screen-dependent draws.

Checker: ignore fence language labels, accept exactly one closed code fence (or raw code), parse the whole extracted code with ast.parse and node --check. Count both-parser cases as ambiguous, neither as invalid. Coarse task pass requires the requested named function, a nonstub body, and a pre-written family-specific operation witness; this is a syntactic plausibility check, not semantic correctness or unit-test execution. Reject empty, invalid, ambiguous, unclosed/multiple fences, >=256-token outputs without EOS, and repetition (a nonblank >=8-character line repeated >=4 times or an 8-token span repeated >=6 times) as breakage. Language-identity counts remain separate from valid/unbroken counts and task passes.

POSSIBLE only for a complete screen with correct SET >=40/64 and SWITCH >=40/64 valid, unbroken target-language outputs, <=4/64 correct episodes broken at any scored programming stage, shuffled JavaScript <=8/64 at SET/HOLD/SWITCH/BACK (worst stage), and correct CLEAR impositions <=8/64. Imposition = retained CLEAR is valid JavaScript **and** the paired fresh default is valid Python; report eligible pairs and invalid CLEAR responses. MARGINAL if correct SET >=24/64; otherwise NOT POSSIBLE. Competence / same-experts ineligibility takes precedence. HOLD and BACK and all coarse task passes are reported separately. Incomplete or cost-stopped runs are PARTIAL, never extrapolated to a full-screen verdict; fixed denominators remain 64.

Execution: local Qwen3MoeForCausalLM, bf16, device_map={"":0}, eager MoE implementation, SDPA attention, thinking disabled, greedy single-sequence decoding, max 256 generated tokens. Installed Transformers 5.16.1 router returns (logits, weights, indices); its forward hook adds logits and recomputes softmax/top-k/normalization before the consumer receives the tuple. An OFF hook returns the original object. CPU fake-router/consumer fixtures test effects and exact OFF behavior. Source: [Hugging Face Qwen3MoE documentation](https://huggingface.co/docs/transformers/model_doc/qwen3_moe), and the locally installed router source saved in cpu.json. Routing research note was absent at initial preparation; check again before launch and adopt it before outcomes if it appears.

Four-hour GPU allocation cap starts before model loading; cooperative per-token checks stop further scheduling and persist partial records, without process signals. A 30-second reserve admits no new request close to cap. Blocking load/forward can overrun; measured overrun is reported, never concealed. Foreground only. GPU and downloader are checked every 600 seconds while waiting, without any process termination. All index shards must have structurally complete headers, matching index membership and exact byte lengths; SHA256 must match HF download metadata when supplied. Wait for the model-specific downloader to exit before loading.

## Results

PENDING — CPU preparation; no model output exists.
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
    languages = [lang for lang in LANGS if parsed[lang]]
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
        self.counts = [0] * len(self.gates)

    def hook(self, layer):
        def apply(gate, inputs, output):
            import torch

            tuple_output = isinstance(output, tuple)
            logits = output[0] if tuple_output else output
            if self.capture:
                assert self.sums is not None and logits.shape[0] == 1, (
                    "Capture only actual generated positions, batch 1"
                )
                self.sums[layer].add_(logits.detach().double().sum(0))
                idx = torch.topk(
                    torch.softmax(logits.float(), -1), gate.top_k, -1
                ).indices
                self.freqs[layer].add_(
                    torch.bincount(idx.flatten(), minlength=gate.num_experts)
                )
                self.counts[layer] += logits.shape[0]
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
    rms = centered.square().mean(-1, keepdim=True).sqrt()
    normalized = centered / rms.clamp_min(1e-12)
    gen = torch.Generator(device="cpu").manual_seed(seed)
    random_bias = torch.randn(normalized.shape, generator=gen, dtype=normalized.dtype)
    random_bias -= random_bias.mean(-1, keepdim=True)
    random_bias *= normalized.norm(dim=-1, keepdim=True) / random_bias.norm(
        dim=-1, keepdim=True
    ).clamp_min(1e-12)
    return normalized, random_bias


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
        torch.manual_seed(SEED)
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL, local_files_only=True)
        self.model = Qwen3MoeForCausalLM.from_pretrained(
            MODEL,
            dtype=torch.bfloat16,
            device_map={"": 0},
            attn_implementation="sdpa",
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

    def generate(self, messages, bias=None, capture=False):
        if time.monotonic() >= self.deadline - 30:
            raise BudgetStop("30-second reserve: no new request")
        torch = self.torch
        ids = self.tokenizer.apply_chat_template(
            messages, tokenize=True, add_generation_prompt=True, enable_thinking=False
        )
        inputs = torch.tensor([ids], device="cuda")
        h = self.hooks
        h.bias = None if bias is None else bias.to(device="cuda", dtype=torch.bfloat16)
        h.capture = False
        if capture:
            h.reset_capture()
        generated, ended, cost_stop = [], False, False
        started = time.monotonic()
        with torch.inference_mode():
            result = self.model(input_ids=inputs, use_cache=True, logits_to_keep=1)
            for _ in range(CAP):
                if time.monotonic() >= self.deadline - 2:
                    cost_stop = True
                    break
                token = int(result.logits[0, -1].argmax())
                generated.append(token)
                if token in self.eos:
                    ended = True
                    break
                # The generated token's own router position, not its predictor.
                # The final non-EOS token is also forwarded when profiling.
                if len(generated) < CAP or capture:
                    h.capture = capture
                    result = self.model(
                        input_ids=torch.tensor([[token]], device="cuda"),
                        past_key_values=result.past_key_values,
                        use_cache=True,
                        logits_to_keep=1,
                    )
            torch.cuda.synchronize()
        h.capture = False
        h.bias = None
        text = self.tokenizer.decode(generated, skip_special_tokens=True)
        record = dict(
            text=text,
            generated_token_ids=generated,
            input_token_ids=ids,
            eos=ended,
            truncated=not ended and len(generated) >= CAP,
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


def messages_for(task, cue=None, history=None):
    return list(history or [dict(role="system", content=SYSTEM)]) + [
        dict(role="user", content=task["prompt"] + (f" Use {cue}." if cue else ""))
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
                d["score"]["valid_language"] == "Python" for _, d in paired
            ),
            clear_impositions=sum(
                r["score"]["valid_language"] == "JavaScript"
                and d["score"]["valid_language"] == "Python"
                for r, d in paired
            ),
        )
    complete = (
        all(s["n"] == 64 for a in arms.values() for s in a["steps"].values())
        and len(defaults) == 64
    )
    correct = arms["correct"]
    shuf = max(
        arms["shuffled"]["steps"][s]["valid_languages"].get("JavaScript", 0)
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
        "POSSIBLE": "A fixed router bias can select these two programming languages under this quick-check reading. This does not establish an automatic skill controller or semantic task correctness.",
        "MARGINAL": "Some language steering appeared, but the full feasibility criteria were not met.",
        "NOT POSSIBLE": "This brute-force router-bias construction did not reach the pre-written feasibility threshold.",
        "INELIGIBLE": "The setup gate failed, so this run cannot decide whether routing bias can reliably address these languages.",
        "PARTIAL": "The screen is incomplete. The saved prefix cannot decide feasibility; no full-screen claim is made.",
    }
    lines += [
        "",
        conclusions[summary["verdict"]],
        "",
        "Raw parser decisions, coarse task flags, token IDs, full histories, and timings are in records.jsonl. No generated program was executed.",
        "",
    ]
    (OUT / "README.md").write_text(
        (OUT / "prewritten-reading.md").read_text().split("\n## Results\n", 1)[0] + "\n\n" + "\n".join(lines)
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
    ):
        neutral = step == "NEUTRAL"
        messages = messages_for(task, cue, history)
        rec, prof = engine.generate(messages, bias, capture)
        rec.update(
            phase=phase,
            arm=arm,
            step=step,
            episode=episode,
            task_id=task["id"],
            cue=cue,
            bias_active=bias is not None,
            target=TARGETS.get(step),
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
        journal.write(json.dumps(rec) + "\n")
        journal.flush()
        rows.append(rec)
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
        for i, task in enumerate(b["competence"]):
            for lang in (*LANGS, None):
                request(task, "competence", lang or "OFF", "SET", i, cue=lang)
        for lang in LANGS:
            rs = [r for r in rows if r["phase"] == "competence" and r["arm"] == lang]
            competence[lang] = dict(
                valid=sum(r["score"]["valid_language"] == lang for r in rs),
                task_check=sum(
                    r["score"]["valid_task"] and r["score"]["valid_language"] == lang
                    for r in rs
                ),
                n=len(rs),
            )
        competence["default"] = dict(
            Counter(
                r["score"]["language"]
                for r in rows
                if r["phase"] == "competence" and r["arm"] == "OFF"
            )
        )
        write_json(OUT / "competence.json", competence)
        if any(competence[lang]["valid"] < 28 for lang in LANGS):
            eligibility = (
                "competence: fewer than 28/32 valid in at least one cued language"
            )
            return
        aggregates, per_task = [], []
        for lang in LANGS:
            sums = freq = None
            count = 0
            for i, task in enumerate(b["profile"]):
                rec, p = request(
                    task, "profile", lang, "SET", i, cue=lang, capture=True
                )
                assert p["count"] > 0, "Empty profile generation"
                per_task.append(dict(language=lang, task_id=task["id"], **p))
                sums = (
                    p["logit_sums"].clone() if sums is None else sums + p["logit_sums"]
                )
                freq = (
                    p["frequency_sums"].clone()
                    if freq is None
                    else freq + p["frequency_sums"]
                )
                count += p["count"]
                torch.save(per_task, OUT / "profile-task-sums.pt")
            aggregates.append(
                dict(logits=sums / count, frequencies=freq / count, positions=count)
            )
        profiles = torch.stack([a["logits"] for a in aggregates]).float()
        frequencies = torch.stack([a["frequencies"] for a in aggregates]).float()
        torch.save(
            dict(
                languages=LANGS,
                logits=profiles,
                frequencies=frequencies,
                positions=[a["positions"] for a in aggregates],
            ),
            OUT / "profiles.pt",
        )
        stats = profile_stats(profiles, frequencies)
        write_json(OUT / "profile-statistics.json", stats)
        normal, shuffled = make_biases(profiles)
        torch.save(
            dict(
                languages=LANGS,
                normalized=normal,
                shuffled=shuffled,
                random_seed=SEED + 2,
            ),
            OUT / "biases.pt",
        )
        if stats["same_experts"]:
            eligibility = "same experts: top-8 frequency overlap >=7/8 at every layer"
            return
        grid = []
        for alpha in (0.5, 1, 2, 4):
            for layers in ("all", "upper_half"):
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
        # Paired fresh defaults must be observed for each episode even in a stopped prefix.
        neutral = dict(id="neutral", prompt="Reply only OK.", name="", witness="")
        for e in range(64):
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
                for step in STEPS:
                    task = (
                        neutral
                        if step == "NEUTRAL"
                        else b["screen"][task_indices[step]]
                    )
                    lang = "JavaScript" if step == "NEUTRAL" else TARGETS[step]
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
    assert not torch.equal(shuf[0], -shuf[1])
    zero, rz = make_biases(torch.ones_like(profiles))
    assert torch.count_nonzero(zero) == torch.count_nonzero(rz) == 0
    checks += [
        "normalized centered directions; independent deterministic norm-matched random stream; zero difference safe"
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
    checks += [
        "tiny random HF checkpoint loads with bf16/device_map; actual MoE model bias changes logits; exact OFF restoration"
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
        cuda_initialized=torch.cuda.is_initialized(),
    )


def prepare():
    assert shutil.which("node"), "Node parser required"
    assert not (OUT / "records.jsonl").exists(), "No edits after model outcomes"
    OUT.mkdir(parents=True, exist_ok=True)
    cpu = cpu_tests()
    assert not cpu["cuda_initialized"]
    write_json(OUT / "cpu.json", cpu)
    write_json(OUT / "banks.json", bank())
    (OUT / "prewritten-reading.md").write_text(READING)
    (OUT / "README.md").write_text(READING)
    files = [
        "scripts/focus_check40.py",
        "results/quick-checks/check40/banks.json",
        "results/quick-checks/check40/prewritten-reading.md",
        "results/quick-checks/check40/cpu.json",
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
            audit = summarize(rows, existing["ineligible_reason"])
            for key in audit:
                assert audit[key] == existing[key], (
                    f"Raw-record summary mismatch: {key}"
                )
            b = json.loads((OUT / "banks.json").read_text())
            tasks = {t["id"]: t for split in b.values() for t in split}
            for r in rows:
                if r["step"] != "NEUTRAL":
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
