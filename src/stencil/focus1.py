"""Prospective FOCUS-1 v2: synthetic inputs, retained-KV execution and audit.

No model imports or artifact reads occur at import time. Only ``load_backend``
can initialize a real trunk; the CLI calls it after the evidence consumer.
The DRAFT is not a registration. All paths and scientific constants are fixed.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import math
import os
import random
import re
import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

import torch

from stencil.function_vectors import (
    make_residual_hook,
    mean_difference,
    repeated_4gram_fraction,
)
from stencil.sc1_episodes import json_equal, parse_json

ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT_ROOT = ROOT / "results/qwen/focus1-v2"
MODEL_INPUTS = (
    "models/qwen3-1.7b.pt",
    "models/qwen3-1.7b-hf/config.json",
    "models/qwen3-1.7b-hf/tokenizer.json",
    "models/qwen3-1.7b-hf/tokenizer_config.json",
    "models/qwen3-1.7b-hf/generation_config.json",
)
CODE_INPUTS = (
    "scripts/focus1.py",
    "src/stencil/focus1.py",
    "src/stencil/qwen3.py",
    "src/stencil/function_vectors.py",
    "src/stencil/sc1_episodes.py",
    "src/stencil/sc1.py",
)
REVIEWED_HASH = "746b354436a2007984f394fa995c68c6a455312c80bc4493dca9f9bc5f0e67fb"
DRAFT_HEADING = "## FOCUS-1 — SET/HOLD/SWITCH/CLEAR SCREEN ON FROZEN QWEN (DRAFT v2"
SKETCH_END = (
    "10. Claim oscillation only after a measured win over nonoscillatory controls; "
    "obtain a separate registration/budget before any training.\n"
)
VERSION = "focus1-v2:20260904"
ALPHA = 1 / 60
CAP = 21600.0
EOS = (151645, 151643)
LAYERS = (12, 16, 20)
CELLS = tuple((a, layer) for a in (0.5, 1.0, 2.0) for layer in LAYERS)
PHASES = ("SET", "HOLD", "SWITCH", "BACK")
MAIN_ARMS = ("correct", "swapped", "shuffled", "OFF")
INTERVENTIONS = ("correct", "swapped", "CLEAR", "KEEP", "replay")
TEST_ARMS = (*MAIN_ARMS, "CLEAR", "KEEP", "replay", "transient")
USER = "<|im_start|>user\n"
TAIL = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
SEPARATOR = "\n\n"
NEUTRAL = "The room is quiet. The light is steady. "
COST_CLASSES = (
    "load",
    "check",
    "persistence",
    "extraction",
    "canonical",
    "retained",
    "clear",
    "keep",
    "replay",
    "certification",
    "transient",
)


class Invalid(ValueError):
    """Integrity defect: no scientific verdict can be inferred."""


class Incomplete(RuntimeError):
    """Allocation or infrastructure prevented completion."""


class StopRun(RuntimeError):
    """An observed endpoint or safety floor is already impossible."""


def require(condition, reason):
    if not condition:
        raise Invalid(reason)


def canonical(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode()


def digest(value):
    return hashlib.sha256(
        value if isinstance(value, bytes) else canonical(value)
    ).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def seed(split, episode, purpose):
    require(split in ("extraction", "setup", "test"), "unknown split")
    require(type(episode) is int and episode >= 0, "episode seed must be nonnegative")
    require(
        purpose
        in (
            *[f"sort{i}" for i in range(4)],
            "copy0",
            "copy1",
            "randomA",
            "randomB",
            "armorder",
        ),
        "unknown seed purpose",
    )
    return int.from_bytes(
        hashlib.sha256(f"{VERSION}:{split}:{episode}:{purpose}".encode()).digest(),
        "big",
    )


def validate_operands(values):
    require(isinstance(values, list) and 5 <= len(values) <= 8, "operand length")
    require(all(type(x) is int and -9 <= x <= 9 for x in values), "operand domain")
    require(len(set(values)) == len(values), "duplicate operands")
    require(
        values not in (sorted(values), sorted(values, reverse=True)), "sorted input"
    )


def generate_banks():
    banks, seen = {}, set()
    for split, count in (("extraction", 64), ("setup", 32), ("test", 64)):
        rows = []
        for i in range(count):
            length = 5 + i // (count // 4)
            row = dict(
                episode=i,
                split=split,
                length=length,
                initial="AB"[i % 2],
                donor=i ^ 1,
                lists={},
                rejections={},
            )
            purposes = (
                ("sort0",)
                if split == "extraction"
                else ("sort0", "sort1", "sort2", "sort3", "copy0", "copy1")
            )
            for purpose in purposes:
                rng = random.Random(seed(split, i, purpose))
                rejected = 0
                while True:
                    values = rng.sample(range(-9, 10), length)
                    rng.shuffle(values)
                    key = tuple(sorted(values))
                    if (
                        values not in (sorted(values), sorted(values, reverse=True))
                        and key not in seen
                    ):
                        break
                    rejected += 1
                seen.add(key)
                row["lists"][purpose] = values
                row["rejections"][purpose] = rejected
            rows.append(row)
        banks[split] = rows
    validate_banks(banks)
    return banks


def validate_banks(banks):
    seen = set()
    for split, count in (("extraction", 64), ("setup", 32), ("test", 64)):
        rows = banks[split]
        require(len(rows) == count, f"{split} bank size")
        for i, row in enumerate(rows):
            require(row["episode"] == i and row["split"] == split, "bank order")
            require(row["length"] == 5 + i // (count // 4), "length balance")
            require(
                row["initial"] == "AB"[i % 2] and row["donor"] == i ^ 1,
                "task/donor balance",
            )
            purposes = (
                {"sort0"}
                if split == "extraction"
                else {"sort0", "sort1", "sort2", "sort3", "copy0", "copy1"}
            )
            require(set(row["lists"]) == purposes, "list inventory")
            for values in row["lists"].values():
                validate_operands(values)
                require(len(values) == row["length"], "assigned length")
                key = tuple(sorted(values))
                require(key not in seen, "global unordered operand-set collision")
                seen.add(key)


def other(task):
    require(task in ("A", "B"), "enum must be A or B")
    return "B" if task == "A" else "A"


def schedule(initial):
    return (initial, initial, other(initial), initial)


def target(values, task):
    require(task in ("A", "B", "OFF"), "invalid target enum")
    return list(values) if task == "OFF" else sorted(values, reverse=task == "B")


def prompt(values, task=None, *, copy=False):
    order = "ascending" if task == "A" else "descending"
    prefix = (
        "Copy these integers in exactly the given order."
        if copy
        else "Process these integers."
        if task is None
        else f"Sort these integers in {order} order."
    )
    return f"{prefix} Output only a JSON array. Integers: {json.dumps(values)}"


def extraction_prompts(row):
    values = row["lists"]["sort0"]
    return {
        task: prompt(values, None if task == "OFF" else task)
        for task in ("A", "B", "OFF")
    }


def encode(tokenizer, text):
    result = tokenizer.encode(text)
    ids = result.ids if hasattr(result, "ids") else result
    require(
        isinstance(ids, list) and ids and all(type(x) is int and x >= 0 for x in ids),
        "tokenizer IDs",
    )
    return ids


def tokenizer_facts(tokenizer):
    require(tokenizer.token_to_id("<|im_end|>") == EOS[0], "pinned im_end EOS")
    require(tokenizer.token_to_id("<|endoftext|>") == EOS[1], "pinned endoftext EOS")
    delay = encode(tokenizer, NEUTRAL * 128)[:128]
    require(
        len(delay) == 128 and not set(delay).intersection(EOS), "exact 128 neutral IDs"
    )
    return dict(
        delay_ids=delay,
        delay_sha256=digest(delay),
        eos=list(EOS),
        user=USER,
        tail=TAIL,
        separator=SEPARATOR,
        segmentation="user + delay IDs + (separator + current prompt + tail)",
    )


def layout(tokenizer, values, *, phase="SET", task=None, copy=False, retained=False):
    facts = tokenizer_facts(tokenizer)
    prefix = encode(tokenizer, ("\n" if retained else "") + USER)
    delayed = phase in ("HOLD", "BACK") and not copy
    body = (SEPARATOR if delayed else "") + prompt(values, task, copy=copy) + TAIL
    ids = prefix + (facts["delay_ids"] if delayed else []) + encode(tokenizer, body)
    return dict(
        ids=ids,
        sha256=digest(ids),
        delay_ids=facts["delay_ids"] if delayed else [],
        phase=phase,
        retained=retained,
        copy=copy,
    )


def bank_layouts(tokenizer, rows):
    result = {}
    for row in rows:
        i = str(row["episode"])
        result[i] = {}
        for purpose, values in row["lists"].items():
            variants = {"absent": layout(tokenizer, values)}
            if purpose.startswith("sort"):
                phase = PHASES[int(purpose[-1])]
                variants = {
                    "main": layout(tokenizer, values, phase=phase),
                    "transient": layout(tokenizer, values, phase=phase, retained=True),
                    **{t: layout(tokenizer, values, task=t) for t in ("A", "B")},
                    "absent": layout(tokenizer, values),
                }
            else:
                variants = {
                    "fresh": layout(tokenizer, values, copy=True),
                    "retained": layout(tokenizer, values, copy=True, retained=True),
                }
            result[i][purpose] = variants
        if row["split"] == "extraction":
            triple = result[i]["sort0"]
            require(
                len({triple[k]["ids"][-1] for k in ("A", "B", "absent")}) == 1,
                "extraction triples have different final wrapper tokens",
            )
    return result


def normalize_pair(a, b, off):
    require(len(a) == len(b) == len(off) and bool(off), "paired extraction states")
    raw = {}
    for task, states in (("A", a), ("B", b)):
        require(
            all(x.shape == y.shape for x, y in zip(states, off, strict=True)),
            "paired layer-input shapes",
        )
        differences = [
            x.detach().float() - y.detach().float()
            for x, y in zip(states, off, strict=True)
        ]
        raw[task] = mean_difference(
            differences, [torch.zeros_like(x) for x in differences]
        )
    norms = {task: float(v.norm()) for task, v in raw.items()}
    require(
        all(math.isfinite(n) and n > 0 for n in norms.values()),
        "zero/nonfinite vector norms",
    )
    require(
        all(v.ndim == 1 and bool(torch.isfinite(v).all()) for v in raw.values()),
        "vector shape/finite",
    )
    rho = sum(norms.values()) / 2
    vectors = {task: (rho * v / norms[task]).float() for task, v in raw.items()}
    cosine = float(
        torch.nn.functional.cosine_similarity(vectors["A"], vectors["B"], dim=0)
    )
    return vectors, dict(
        raw_norms=norms,
        rho=rho,
        cosine=cosine,
        normalized_norms={t: float(v.norm()) for t, v in vectors.items()},
    )


def hook(vector, alpha, layer, position, events):
    if vector is None:
        return None
    require(bool(torch.isfinite(vector).all()), "nonfinite injection")
    return make_residual_hook(
        vector, alpha=alpha, layer=layer, generated_position=position, event_sink=events
    )


def random_directions(split, episode, width, rho):
    result = {}
    for task in ("A", "B"):
        rng = random.Random(seed(split, episode, "random" + task))
        v = torch.tensor([rng.gauss(0, 1) for _ in range(width)], dtype=torch.float32)
        require(
            bool(torch.isfinite(v).all()) and float(v.norm()) > 0,
            "invalid random direction",
        )
        result[task] = rho * v / v.norm()
    return result


def score_reply(
    text, tokens, expected, *, deadline=False, exception=None, old_target=None
):
    valid = False
    value = None
    try:
        value = parse_json(text)
        valid = isinstance(value, list) and len(value) == len(expected) and bool(value)
        valid = valid and all(
            not isinstance(x, bool)
            and isinstance(x, (int, float, Decimal))
            and Decimal(str(x)).is_finite()
            and Decimal(str(x)) == Decimal(str(x)).to_integral_value()
            for x in value
        )
    except (ValueError, TypeError, ArithmeticError):
        pass
    eos = bool(tokens) and tokens[-1] in EOS
    truncation = (len(tokens) >= 64 and not eos) or deadline
    rep = repeated_4gram_fraction(tokens)
    return dict(
        I=not valid,
        T=bool(truncation),
        R=rep > 0.5,
        rep4=rep,
        broken=bool(not valid or truncation or rep > 0.5 or exception),
        exact=bool(valid and json_equal(value, expected)),
        imposition=bool(
            valid and old_target is not None and json_equal(value, old_target)
        ),
        eos=eos,
        deadline=bool(deadline),
    )


def mcnemar(b, c):
    require(type(b) is int and type(c) is int and min(b, c) >= 0, "discordant counts")
    return (
        sum(math.comb(b + c, j) for j in range(b, b + c + 1)) / 2 ** (b + c)
        if b + c
        else 1.0
    )


def binomial_lower(n, k, p):
    require(0 <= p <= 1 and 0 <= k <= n, "binomial arguments")
    return math.fsum(math.comb(n, j) * p**j * (1 - p) ** (n - j) for j in range(k + 1))


def paired(left, right):
    require(len(left) == len(right), "paired denominators")
    table = Counter((bool(a), bool(b)) for a, b in zip(left, right, strict=True))
    b, c = table[True, False], table[False, True]
    return dict(
        both=table[True, True],
        neither=table[False, False],
        b=b,
        c=c,
        net=b - c,
        n=len(left),
        p=mcnemar(b, c),
    )


def copy_pairs(clear, replay, keep):
    require(all(len(x) == 2 for x in (clear, replay, keep)), "two-query copy pairs")
    return dict(
        C=all(clear),
        P=all(replay),
        K=all(keep),
        H=any(not c and p for c, p in zip(clear, replay, strict=True)),
        pairs=[dict(clear=c, replay=p) for c, p in zip(clear, replay, strict=True)],
    )


def endpoints(rows, *, prerequisites=True, cap_overrun=False):
    require(
        all(
            type(r["episode"]) is int
            and 0 <= r["episode"] < 64
            and r["initial"] in ("A", "B")
            for r in rows
        ),
        "episode/stratum identity",
    )
    require(
        len(rows) <= 64 and len({r["episode"] for r in rows}) == len(rows),
        "episode inventory",
    )
    n, missing = len(rows), 64 - len(rows)
    counts = {
        k: sum(bool(r[k]) for r in rows)
        for k in ("S", "O", "W", "V", "R", "C", "P", "H", "K")
    }
    strata = {
        t: {
            "n": sum(r["initial"] == t for r in rows),
            **{
                k: sum(bool(r[k]) for r in rows if r["initial"] == t)
                for k in ("S", "O", "W")
            },
        }
        for t in ("A", "B")
    }
    require(all(s["n"] <= 32 for s in strata.values()), "stratum denominators")
    tables = {
        a + "-" + b: paired([r[a] for r in rows], [r[b] for r in rows])
        for a, b in (("S", "O"), ("W", "V"), ("W", "R"), ("C", "K"))
    }
    broken = {
        arm: sum(bool(r["broken"].get(arm, False)) for r in rows) for arm in TEST_ARMS
    }
    reasons, labels = [], []
    integrity = all(r["integrity"] for r in rows)
    for task, values in strata.items():
        if values["O"] >= 24:
            labels.append("default-coincident:" + task)
    if sum(r["keep_imposition"] for r in rows) < 8:
        labels.append("CLEAR-UNCHALLENGED")
    for k in ("S", "W"):
        if counts[k] + missing < 48:
            reasons.append(k + " count <48/64")
        for task, values in strata.items():
            if values[k] + 32 - values["n"] < 24:
                reasons.append(k + " stratum " + task + " <24/32")
    for name in ("S-O", "W-V", "W-R"):
        if tables[name]["net"] + missing < 16:
            reasons.append(name + " net <16")
    if counts["R"]:
        reasons.append("shuffled complete schedule >0/64")
    if counts["H"] > 1:
        reasons.append("residual harm >1/64")
    if any(r["clear_imposition"] for r in rows):
        reasons.append("CLEAR old-task imposition")
    reasons += [arm + " breakage >1/64" for arm in INTERVENTIONS if broken[arm] > 1]
    tests = {}
    if not missing:
        tests = {name: tables[name]["p"] for name in ("S-O", "W-V", "W-R")}
        tests.update(
            harm=binomial_lower(64, counts["H"], 0.1),
            shuffled=binomial_lower(64, counts["R"], 0.1),
        )
        reasons += [name + " exact p >1/60" for name, p in tests.items() if p > ALPHA]
    else:
        for value in tables.values():
            value.pop("p")
    state = (
        "FAIL" if reasons else "INCOMPLETE" if missing or not prerequisites else "PASS"
    )
    if not integrity:
        state = "INVALID"
        reasons.append("non-vacuity/integrity")
    if cap_overrun:
        state = "INCOMPLETE" if state != "INVALID" else state
        reasons.append("allocation cap overrun")
    if not prerequisites:
        reasons.append("missing preceding stage evidence")
    return dict(
        state=state,
        reasons=reasons,
        labels=labels,
        n=n,
        missing=missing,
        counts=counts,
        strata=strata,
        tables=tables,
        tests=tests,
        broken=broken,
        alpha_family=ALPHA,
        denominators=dict(episodes=64, per_task=32),
        keep_impositions=sum(r["keep_imposition"] for r in rows),
        clear_impositions=sum(r["clear_imposition"] for r in rows),
    )


class Store:
    """Small exclusive-write files and fsynced hash-chain JSONL logs."""

    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self._tails = {}

    def path(self, name):
        require(
            re.fullmatch(r"[A-Za-z0-9_.-]+", name) is not None, "external artifact path"
        )
        path = self.root / name
        require(
            path.resolve().parent == self.root and not path.is_symlink(),
            "artifact symlink",
        )
        return path

    def write(self, name, value):
        try:
            with self.path(name).open("xb") as handle:
                handle.write(canonical(value) + b"\n")
                handle.flush()
                os.fsync(handle.fileno())
        except FileExistsError as exc:
            raise Invalid("refuse overwrite: " + name) from exc

    def read(self, name):
        try:
            return json.loads(self.path(name).read_bytes())
        except (OSError, ValueError) as exc:
            raise Invalid("missing/malformed artifact: " + name) from exc

    def read_log(self, name):
        path = self.path(name + ".jsonl")
        if not path.exists():
            return []
        raw = path.read_bytes()
        require(not raw or raw.endswith(b"\n"), "incomplete JSONL persistence")
        previous, seen, rows = "0" * 64, set(), []
        for line in raw.splitlines():
            try:
                row = json.loads(line)
                hashed = row.pop("sha256")
                require(
                    row["previous_sha256"] == previous and digest(row) == hashed,
                    "record hash chain",
                )
                require(row["attempt_id"] not in seen, "duplicate attempt ID")
                seen.add(row["attempt_id"])
                row["sha256"] = hashed
                rows.append(row)
                previous = hashed
            except (ValueError, KeyError, TypeError) as exc:
                raise Invalid("malformed/tampered record log: " + name) from exc
        return rows

    def append(self, name, value):
        path = self.path(name + ".jsonl")
        if name not in self._tails:
            rows = self.read_log(name)
            self._tails[name] = [
                rows[-1]["sha256"] if rows else "0" * 64,
                {r["attempt_id"] for r in rows},
                path.stat().st_size if path.exists() else 0,
            ]
        previous, seen, size = self._tails[name]
        require(
            (path.stat().st_size if path.exists() else 0) == size,
            "concurrent log mutation",
        )
        require(value["attempt_id"] not in seen, "duplicate attempt ID")
        row = dict(value, previous_sha256=previous)
        row["sha256"] = digest(row)
        encoded = canonical(row) + b"\n"
        with path.open("ab") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        self._tails[name] = [
            row["sha256"],
            seen | {value["attempt_id"]},
            size + len(encoded),
        ]
        return row


def remaining_work(stage):
    work = Counter(canonical=1024, clear=128, keep=128, replay=128, transient=64)
    if stage == "run":
        return dict(work)
    work.update(
        certification=512, canonical=9 * 64, clear=9 * 128, keep=9 * 128, replay=9 * 128
    )
    if stage == "select":
        return dict(work)
    work.update(extraction=192)
    if stage == "extract":
        return dict(work)
    work.update(canonical=128, clear=64)
    return dict(work)


@dataclass
class Budget:
    spent: float
    rates: dict
    clock: object = time.monotonic
    origin: float = field(init=False)
    frozen_deadline: float | None = None

    def __post_init__(self):
        self.origin = self.clock()
        require(
            all(math.isfinite(v) and v >= 0 for v in self.rates.values()),
            "invalid timing rates",
        )

    @property
    def elapsed(self):
        return self.spent + self.clock() - self.origin

    @property
    def deadline(self):
        return self.frozen_deadline or min(300.0, 4 * self.attempt_estimate)

    @property
    def attempt_estimate(self):
        return (
            max(
                self.rates[k]
                for k in COST_CLASSES
                if k not in ("load", "check", "persistence")
            )
            + self.rates["check"]
            + self.rates["persistence"]
        )

    def observe(self, kind, duration):
        require(
            kind in COST_CLASSES and math.isfinite(duration) and duration >= 0,
            "cost class",
        )
        self.rates[kind] = max(self.rates.get(kind, 0), duration)

    def project(self, work, reloads):
        overhead = self.rates["check"] + self.rates["persistence"]
        require(overhead >= 0, "timing overhead")
        return (
            self.elapsed
            + reloads * self.rates["load"]
            + 1.25 * sum((self.rates[k] + overhead) * n for k, n in work.items())
        )

    def reserve(self, work, reloads, *, loading=False):
        reservation = self.deadline + (self.rates["load"] if loading else 0)
        if (
            self.elapsed > CAP
            or self.project(work, reloads) > CAP
            or self.elapsed + reservation > CAP
        ):
            raise Incomplete(
                "cumulative allocation projection/deadline reservation exceeds 21600s"
            )

    def check(self, started):
        return self.elapsed >= CAP or self.clock() - started >= self.deadline


def tensor_hash(tensor):
    tensor = tensor.detach().cpu().contiguous()
    return digest(
        dict(
            shape=list(tensor.shape),
            dtype=str(tensor.dtype),
            bytes=tensor.view(torch.uint8).numpy().tobytes().hex(),
        )
    )


def cache_hash(cache):
    return digest(
        dict(
            length=cache.length,
            k=[tensor_hash(t) for t in cache.k],
            v=[tensor_hash(t) for t in cache.v],
        )
    )


@dataclass
class History:
    cache: object
    tokens: list
    events: list = field(default_factory=list)


def check_history(history, *, nonempty=True):
    cache = history.cache
    require(
        cache.length == len(history.tokens),
        "cache history/final-token omission or secret rebuild",
    )
    require(bool(history.tokens) or not nonempty, "empty token history")
    require(len(cache.k) == len(cache.v) == cache.cfg.n_layer, "cache layer inventory")
    for k, v in zip(cache.k, cache.v, strict=True):
        if not history.tokens and not nonempty:
            require(k is None and v is None, "nonempty initial cache")
        else:
            require(
                k is not None and v is not None and k.numel() > 0 and v.numel() > 0,
                "empty K/V",
            )
            require(
                k.shape == v.shape and k.shape[2] == len(history.tokens),
                "post-query eviction/cache positions",
            )
            require(
                bool(torch.isfinite(k).all()) and bool(torch.isfinite(v).all()),
                "nonfinite K/V",
            )


def clone_history(source):
    check_history(source, nonempty=False)
    cache = type(source.cache)(source.cache.cfg)
    cache.length = source.cache.length
    cache.k = [x.clone() if x is not None else None for x in source.cache.k]
    cache.v = [x.clone() if x is not None else None for x in source.cache.v]
    out = History(cache, list(source.tokens), [dict(e) for e in source.events])
    for a, b in zip(
        (*source.cache.k, *source.cache.v), (*cache.k, *cache.v), strict=True
    ):
        require(a is None or a.data_ptr() != b.data_ptr(), "aliased cache clone")
    return out


def compare_caches(left, right, *, layer=None):
    check_history(left)
    check_history(right)
    require(left.tokens == right.tokens, "replay history mismatch/stale operands")
    rows = []
    for i, (ak, av, bk, bv) in enumerate(
        zip(left.cache.k, left.cache.v, right.cache.k, right.cache.v, strict=True)
    ):
        require(
            ak.shape == bk.shape and av.shape == bv.shape, "cache comparison shapes"
        )
        rows.append(
            dict(
                layer=i,
                k=float((ak.float() - bk.float()).abs().max()),
                v=float((av.float() - bv.float()).abs().max()),
            )
        )
    if layer is not None:
        require(
            any(e.get("alpha", 0) != 0 and e.get("norm", 0) > 0 for e in left.events),
            "absent nonzero-dose hook events",
        )
        require(0 <= layer < len(rows), "affected layer range")
        require(
            all(r["k"] > 0 and r["v"] > 0 for r in rows[layer:]),
            "vacuous affected-layer K/V residuals",
        )
    return rows


class Backend:
    """A trunk, tokenizer and KV factory; fake trunks use the same consumer."""

    def __init__(self, model, tokenizer, cache_factory, *, device="cpu", prefill=None):
        self.model, self.tokenizer = model, tokenizer
        self.cache_factory, self.device, self.prefill = cache_factory, device, prefill

    def empty(self):
        return History(self.cache_factory(), [])

    def forward(
        self, history, ids, *, vector=None, alpha=0, layer=12, position=0, capture=None
    ):
        require(bool(ids), "empty forward tokens")
        before = len(history.tokens)
        events = []
        residual = hook(vector, alpha, layer, position, events)
        kwargs = dict(residual_hook=residual)
        if capture is not None:
            kwargs["capture_hidden"] = capture
        tensor = torch.tensor([ids], dtype=torch.long, device=self.device)
        with torch.no_grad():
            if self.prefill is not None and capture is None:
                result, _, _, _ = self.prefill(
                    self.model,
                    history.cache,
                    tensor,
                    history_end=0,
                    evict_range=None,
                    eviction_timing="pre-query",
                    current_forward_kwargs=kwargs,
                )
            else:
                result = self.model(tensor, cache=history.cache, **kwargs)
        history.tokens.extend(ids)
        for event in events:
            event.update(
                alpha=alpha,
                norm=float(vector.norm()),
                absolute_position=before + len(ids) - 1,
                vector_sha256=tensor_hash(vector),
            )
        history.events.extend(events)
        require(
            residual is None or len(events) == 1,
            "missing/duplicate actual hook invocation",
        )
        check_history(history)
        return result

    def teacher_force(self, tokens):
        history = self.empty()
        self.forward(history, tokens)
        require(not history.events, "OFF replay was hooked")
        return history

    def canonical(self, ids, arms):
        """No prior decision history; every arm has independent equal prompt KV."""
        require(
            len(ids) > 1 and len(set(arms)) == len(arms), "canonical branch inventory"
        )
        prefix = self.teacher_force(ids[:-1])
        clones = {arm: clone_history(prefix) for arm in arms}
        probes, hashes = {}, {}
        all_pointers = set()
        for arm, history in clones.items():
            require(history.tokens == ids[:-1], "canonical prompt IDs")
            for tensor in (*history.cache.k, *history.cache.v):
                require(
                    tensor.data_ptr() not in all_pointers, "mutating/aliased arm caches"
                )
                all_pointers.add(tensor.data_ptr())
            require(
                all(r["k"] == r["v"] == 0 for r in compare_caches(prefix, history)),
                "unequal canonical KV",
            )
            scratch = clone_history(history)
            logits = self.forward(scratch, ids[-1:])
            probes[arm] = logits[0, -1].detach().float().cpu()
            hashes[arm] = cache_hash(history.cache)
        first = probes[arms[0]]
        require(
            all(torch.equal(first, p) for p in probes.values()),
            "unequal unhooked first-decision logits",
        )
        require(len(set(hashes.values())) == 1, "canonical cache hash mismatch")
        return clones, dict(
            prompt_ids=ids,
            prompt_sha256=digest(ids),
            position=len(ids) - 1,
            prefix_kv_sha256=hashes[arms[0]],
            unhooked_logits_sha256=tensor_hash(first),
            matched_arms=list(arms),
        )

    def decode(
        self,
        history,
        suffix,
        *,
        vector=None,
        alpha=0,
        layer=12,
        deadline=300,
        clock=time.monotonic,
        cap_check=lambda: False,
        audit_cache=False,
    ):
        """Retain actual history, including the final emitted token (also EOS)."""
        started = clock()
        tokens, exception, timed_out, first = [], None, False, None
        integrity_error = None
        before_tokens, before_events = list(history.tokens), len(history.events)
        self.first_history = None
        try:
            require(suffix, "empty current prompt")
            if len(suffix) > 1:
                self.forward(history, suffix[:-1])
            if cap_check() or clock() - started >= deadline:
                timed_out = True
            else:
                logits = self.forward(
                    history, suffix[-1:], vector=vector, alpha=alpha, layer=layer
                )
                first = logits[0, -1].detach().float().cpu()
                require(
                    bool(torch.isfinite(first).all()), "nonfinite first-decision logits"
                )
                if audit_cache:
                    self.first_history = clone_history(history)
                for j in range(64):
                    if cap_check() or clock() - started >= deadline:
                        timed_out = True
                        break
                    token = int(logits[0, -1].argmax())
                    tokens.append(token)
                    # Feeding the final generated token is essential for forks.
                    logits = self.forward(
                        history,
                        [token],
                        vector=vector,
                        alpha=alpha,
                        layer=layer,
                        position=j + 1,
                    )
                    if token in EOS:
                        break
            check_history(history)
            require(
                history.tokens == before_tokens + suffix + tokens or timed_out,
                "final generated token omitted",
            )
        except Invalid as exc:
            integrity_error = str(exc)
            exception = f"Invalid: {exc}"
        except Exception as exc:
            exception = f"{type(exc).__name__}: {exc}"
        timed_out = timed_out or cap_check() or clock() - started >= deadline
        try:
            final_hash = cache_hash(history.cache) if history.tokens else None
        except (AttributeError, TypeError, Invalid):
            final_hash = None
        scored_tokens = tokens[:-1] if tokens and tokens[-1] in EOS else tokens
        text = self.tokenizer.decode(scored_tokens, skip_special_tokens=False)
        output = dict(
            tokens=tokens,
            text=text,
            eos=tokens[-1] if tokens and tokens[-1] in EOS else None,
            deadline=timed_out,
            exception=exception,
            integrity_error=integrity_error,
            elapsed=clock() - started,
            hook_events=history.events[before_events:],
            history_before=before_tokens,
            history_after=list(history.tokens),
            prompt_ids=list(suffix),
            final_kv_sha256=final_hash,
            final_position=history.cache.length,
            cache_layers=history.cache.cfg.n_layer,
            first_logits_sha256=tensor_hash(first) if first is not None else None,
        )
        return output, first


RECORD_FIELDS = {
    "attempt_id",
    "kind",
    "mode",
    "split",
    "episode",
    "phase",
    "arm",
    "initial",
    "source",
    "recipient",
    "donor",
    "source_enum",
    "recipient_enum",
    "donor_enum",
    "inputs",
    "expected",
    "recipient_target",
    "donor_target",
    "old_target",
    "vector",
    "layout",
    "matching",
    "output",
    "score",
    "comparison",
    "binding",
    "cost",
}


class Engine:
    """Schedule actual trunk calls; persist each answer before inspecting gates."""

    def __init__(
        self, backend, store, mode, binding, *, budget=None, work=None, reloads=0
    ):
        self.backend, self.store, self.mode, self.binding = (
            backend,
            store,
            mode,
            binding,
        )
        self.budget = budget or Budget(0, dict.fromkeys(COST_CLASSES, 1.0))
        self.work, self.reloads = Counter(work or {}), reloads
        self.rows = []
        self.stop_callback = None
        self.serial = ""
        self.preparation_seconds = 0.0

    def answer(
        self,
        row,
        phase,
        arm,
        history,
        ids,
        *,
        task,
        layer=12,
        alpha=0,
        vector=None,
        purpose=None,
        matching=None,
        comparison=None,
        kind="canonical",
    ):
        self.budget.reserve(self.work, self.reloads)
        started = self.budget.clock() - self.preparation_seconds
        preparation = self.preparation_seconds
        self.preparation_seconds = 0.0
        purpose = purpose or "sort" + str(PHASES.index(phase))
        values = row["lists"][purpose]
        initial = row["initial"]
        recipient_enum = (
            schedule(initial)[PHASES.index(phase)] if phase in PHASES else initial
        )
        donor_enum = other(recipient_enum)
        copy = purpose.startswith("copy")
        expected = target(values, "OFF" if copy else task)
        attempt_id = f"{self.mode}:{self.serial}:{row['episode']}:{phase}:{arm}"
        self.store.append(
            "attempts",
            dict(
                attempt_id=attempt_id,
                mode=self.mode,
                split=row["split"],
                episode=row["episode"],
                phase=phase,
                arm=arm,
                inputs=values,
                prompt_ids=ids,
                source_enum=task,
                binding=self.binding,
                started=started,
                charged_seconds=self.budget.elapsed,
            ),
        )
        output, logits = self.backend.decode(
            history,
            ids,
            vector=vector,
            alpha=alpha,
            layer=layer,
            deadline=max(0, self.budget.deadline - preparation),
            clock=self.budget.clock,
            cap_check=lambda: self.budget.elapsed >= CAP,
            audit_cache=arm in ("CLEAR", "replay") and comparison is not None,
        )
        checks_started = self.budget.clock()
        old_target = target(values, initial) if copy else None
        score = score_reply(
            output["text"],
            output["tokens"],
            expected,
            deadline=output["deadline"],
            exception=output["exception"],
            old_target=old_target,
        )
        score.update(
            recipient=score_reply(
                output["text"], output["tokens"], target(values, recipient_enum)
            )["exact"],
            donor=score_reply(
                output["text"], output["tokens"], target(values, donor_enum)
            )["exact"],
        )
        record = dict(
            attempt_id=attempt_id,
            kind="answer",
            mode=self.mode,
            split=row["split"],
            episode=row["episode"],
            phase=phase,
            arm=arm,
            initial=initial,
            source=row["donor"] if arm in ("transplant", "swapped") else row["episode"],
            recipient=row["episode"],
            donor=row["donor"],
            source_enum=task,
            recipient_enum=recipient_enum,
            donor_enum=donor_enum,
            inputs=values,
            expected=expected,
            recipient_target=target(values, recipient_enum),
            donor_target=target(values, donor_enum),
            old_target=old_target,
            vector=dict(
                layer=layer,
                alpha=alpha if vector is not None else 0,
                norm=float(vector.norm()) if vector is not None else 0,
                sha256=tensor_hash(vector) if vector is not None else None,
            ),
            layout=dict(
                ids=output["history_before"] + ids,
                sha256=digest(output["history_before"] + ids),
                positions=list(range(len(output["history_before"] + ids))),
            ),
            matching=matching,
            output=output,
            score=score,
            comparison=comparison,
            binding=self.binding,
            cost=dict(
                kind=kind,
                started=started,
                seconds=self.budget.clock() - started,
                charged_seconds=self.budget.elapsed,
            ),
        )
        require(RECORD_FIELDS <= record.keys(), "missing per-decision record fields")
        self.budget.observe("check", self.budget.clock() - checks_started)
        persistence = self.budget.clock()
        self.store.append(self.mode, record)
        self.budget.observe("persistence", self.budget.clock() - persistence)
        self.budget.observe(kind, self.budget.clock() - started)
        self.work[kind] = max(0, self.work[kind] - 1)
        self.rows.append(record)
        if output["integrity_error"]:
            raise Invalid(output["integrity_error"])
        if output["exception"]:
            raise Incomplete(output["exception"])
        if self.stop_callback:
            self.stop_callback(self.rows)
        return record, logits

    def main_decisions(self, row, vectors, alpha, layer, *, certification=False):
        result, histories = {}, {}
        correct_schedule = schedule(row["initial"])
        donor_schedule = schedule(other(row["initial"]))  # before any list read
        require(row["donor"] != row["episode"], "donor/recipient IDs")
        arms = (
            ("correct", "swapped", "transplant", "sham") if certification else MAIN_ARMS
        )
        order = list(arms)
        random.Random(seed(row["split"], row["episode"], "armorder")).shuffle(order)
        randoms = (
            None
            if certification
            else random_directions(
                row["split"],
                row["episode"],
                vectors["A"].numel(),
                float(vectors["A"].norm()),
            )
        )
        for j, phase in enumerate(PHASES):
            self.budget.reserve(self.work, self.reloads)
            prepare_started = self.budget.clock()
            own, donor = correct_schedule[j], donor_schedule[j]
            enums = {
                "correct": own,
                "swapped": donor,
                "transplant": donor,
                "sham": own,
                "shuffled": own,
                "OFF": "OFF",
            }
            ids = layout(
                self.backend.tokenizer, row["lists"]["sort" + str(j)], phase=phase
            )["ids"]
            clones, matching = self.backend.canonical(ids, order)
            self.preparation_seconds = self.budget.clock() - prepare_started
            for arm in order:
                task = enums[arm]
                vector = (
                    None
                    if arm == "OFF"
                    else (randoms if arm == "shuffled" else vectors)[task]
                )
                record, _ = self.answer(
                    row,
                    phase,
                    arm,
                    clones[arm],
                    ids[-1:],
                    task=task,
                    vector=vector,
                    alpha=alpha,
                    layer=layer,
                    matching=matching,
                    kind="certification" if certification else "canonical",
                )
                result[phase, arm] = record
                if arm == "correct" and phase in ("SET", "BACK"):
                    histories[phase] = clones[arm]
            if certification:
                for a, b in (("transplant", "swapped"), ("sham", "correct")):
                    require(
                        result[phase, a]["output"]["tokens"]
                        == result[phase, b]["output"]["tokens"],
                        f"certification {phase} {a}!={b}; no next-cell rescue",
                    )
        return result, histories

    def transient(self, row, source, layer):
        history = clone_history(source)
        ids = layout(
            self.backend.tokenizer, row["lists"]["sort1"], phase="HOLD", retained=True
        )["ids"]
        record, _ = self.answer(
            row,
            "HOLD",
            "transient",
            history,
            ids,
            task=row["initial"],
            layer=layer,
            kind="transient",
        )
        require(not record["output"]["hook_events"], "transient hook must remain OFF")
        return record

    def neutral(self, row, source, vectors, alpha, layer, *, keep=True):
        check_history(source)
        require(source.events, "neutral fork lacks actual steered history")
        clear, retained_keep = clone_history(source), clone_history(source)
        require(
            cache_hash(clear.cache)
            == cache_hash(retained_keep.cache)
            == cache_hash(source.cache),
            "CLEAR/KEEP did not fork actual steered cache",
        )
        results = []
        for j in range(2):
            self.budget.reserve(self.work, self.reloads)
            prepare_started = self.budget.clock()
            replay = self.backend.teacher_force(clear.tokens)
            deltas = compare_caches(clear, replay, layer=layer)
            prior = list(clear.tokens)
            ids = layout(
                self.backend.tokenizer,
                row["lists"]["copy" + str(j)],
                copy=True,
                retained=True,
            )["ids"]
            comparison = dict(
                history_sha256=digest(prior),
                history_ids=prior,
                retained_kv_sha256=cache_hash(clear.cache),
                replay_kv_sha256=cache_hash(replay.cache),
                kv_deltas=deltas,
                source_events=source.events,
                source_tokens=source.tokens,
                source_kv_sha256=cache_hash(source.cache),
                nonvacuous=True,
            )
            self.preparation_seconds = self.budget.clock() - prepare_started
            c, c_logits = self.answer(
                row,
                f"copy{j}",
                "CLEAR",
                clear,
                ids,
                task="OFF",
                layer=layer,
                purpose=f"copy{j}",
                comparison=comparison,
                kind="clear",
            )
            clear_first = self.backend.first_history
            p, p_logits = self.answer(
                row,
                f"copy{j}",
                "replay",
                replay,
                ids,
                task="OFF",
                layer=layer,
                purpose=f"copy{j}",
                comparison=comparison,
                kind="replay",
            )
            query_deltas = compare_caches(
                clear_first, self.backend.first_history, layer=layer
            )
            audit = dict(
                attempt_id=c["attempt_id"] + ":pair",
                kind="pair",
                mode=self.mode,
                episode=row["episode"],
                initial=row["initial"],
                phase=f"copy{j}",
                clear_id=c["attempt_id"],
                replay_id=p["attempt_id"],
                copy_pair=[c["score"]["exact"], p["score"]["exact"]],
                imposition_pair=[c["score"]["imposition"], p["score"]["imposition"]],
                token_equal=c["output"]["tokens"] == p["output"]["tokens"],
                first_logit_delta=float((c_logits - p_logits).abs().max())
                if c_logits is not None and p_logits is not None
                else None,
                comparison=comparison,
                binding=self.binding,
            )
            audit["query_kv_deltas"] = query_deltas
            require(
                audit["first_logit_delta"] is not None,
                "missing first-decision logit audit",
            )
            self.store.append(self.mode, audit)
            self.rows.append(audit)
            if self.stop_callback:
                self.stop_callback(self.rows)
            results.extend([c, p])
            if keep:
                k, _ = self.answer(
                    row,
                    f"copy{j}",
                    "KEEP",
                    retained_keep,
                    ids,
                    task=row["initial"],
                    vector=vectors[row["initial"]],
                    alpha=alpha,
                    layer=layer,
                    purpose=f"copy{j}",
                    kind="keep",
                )
                results.append(k)
        return results, retained_keep

    def keep_only(self, row, source, vectors, alpha, layer):
        history = clone_history(source)
        result = []
        for j in range(2):
            ids = layout(
                self.backend.tokenizer,
                row["lists"]["copy" + str(j)],
                copy=True,
                retained=True,
            )["ids"]
            record, _ = self.answer(
                row,
                f"copy{j}",
                "KEEP",
                history,
                ids,
                task=row["initial"],
                vector=vectors[row["initial"]],
                alpha=alpha,
                layer=layer,
                purpose=f"copy{j}",
                kind="keep",
            )
            result.append(record)
        return result


def reviewed_section():
    ledger = (ROOT / "LEDGER-PLAN.md").read_bytes()
    start = ledger.index(DRAFT_HEADING.encode())
    end = ledger.index(SKETCH_END.encode(), start) + len(SKETCH_END.encode())
    section = ledger[start:end]
    require(digest(section) == REVIEWED_HASH, "reviewed FOCUS-1 v2 draft bytes changed")
    return section


def fingerprints():
    return {name: file_hash(ROOT / name) for name in (*MODEL_INPUTS, *CODE_INPUTS)}


def load_tokenizer():
    from tokenizers import Tokenizer

    config = json.loads((ROOT / MODEL_INPUTS[4]).read_bytes())
    require(set(config["eos_token_id"]) == set(EOS), "generation config EOS facts")
    return Tokenizer.from_file(str(ROOT / MODEL_INPUTS[2]))


def generate_only(store, *, tokenizer=None):
    require(
        not store.path("bank.json").exists(), "bank exists; no replacement generation"
    )
    require(not any(store.root.iterdir()), "generation root must be empty")
    banks = generate_banks()
    tokenizer = tokenizer or load_tokenizer()
    facts = tokenizer_facts(tokenizer)
    layouts = {split: bank_layouts(tokenizer, rows) for split, rows in banks.items()}
    binding = dict(
        version=VERSION,
        python=sys.version,
        reviewed_section_sha256=digest(reviewed_section()),
        inputs=fingerprints(),
        tokenizer=facts,
        prompts=dict(
            user=USER,
            tail=TAIL,
            separator=SEPARATOR,
            neutral=NEUTRAL,
            visible=prompt([1, 0, -1, 3, 2], "A"),
            absent=prompt([1, 0, -1, 3, 2]),
            copy=prompt([1, 0, -1, 3, 2], copy=True),
        ),
        constants=dict(
            layers=list(LAYERS),
            cells=[list(x) for x in CELLS],
            eos=list(EOS),
            max_new=64,
            delay=128,
            cap=CAP,
            alpha_family=ALPHA,
        ),
        lineage=(
            "fit-on:new synthetic extraction only; selection:setup only; "
            "evaluated-on:disjoint test"
        ),
        splits={},
    )
    for split in banks:
        value = dict(rows=banks[split], layouts=layouts[split])
        store.write(split + ".json", value)
        binding["splits"][split] = dict(
            count=len(banks[split]), sha256=file_hash(store.path(split + ".json"))
        )
    store.write("bank.json", binding)
    return dict(
        state="INCOMPLETE",
        reasons=["CPU banks generated; draft is not registered"],
        bank_sha256=file_hash(store.path("bank.json")),
        counts={k: len(v) for k, v in banks.items()},
    )


def evidence_path(store, value, name):
    require(value is not None, "missing " + name + " evidence")
    path = Path(value)
    require(
        path == store.path(name + ".json") and not path.is_symlink(),
        "external/unpinned " + name + " path",
    )
    return store.read(name + ".json")


def registration_evidence(store, registration, bfcl):
    reg = evidence_path(store, registration, "registration")
    required = {
        "reviewed_section_sha256",
        "registered_section_sha256",
        "section_start",
        "section_end",
        "textual_deltas",
        "review",
        "bank_sha256",
        "status",
        "preflight_id",
    }
    require(required <= reg.keys(), "missing registration hash/delta binding")
    require(reg["status"] == "REGISTERED", "a draft is not registered")
    draft = reviewed_section()
    require(
        reg["reviewed_section_sha256"] == digest(draft), "registration reviewed hash"
    )
    ledger = (ROOT / "LEDGER-PLAN.md").read_bytes()
    start, end = reg["section_start"], reg["section_end"]
    require(
        type(start) is int and type(end) is int and 0 <= start < end <= len(ledger),
        "registered byte boundaries",
    )
    registered = ledger[start:end]
    heading = registered.splitlines()[0].decode()
    require(
        heading.startswith("## FOCUS-1 ")
        and "REGISTERED" in heading
        and "DRAFT" not in heading
        and "NOT" not in heading,
        "section is not actually marked REGISTERED",
    )
    require(
        registered.endswith(SKETCH_END.encode()),
        "registered section final sketch boundary",
    )
    require(
        reg["registered_section_sha256"] == digest(registered),
        "registered section hash",
    )
    delta = list(
        difflib.unified_diff(
            draft.decode().splitlines(keepends=True),
            registered.decode().splitlines(keepends=True),
            fromfile="reviewed-v2",
            tofile="registered-v2",
        )
    )
    require(
        reg["textual_deltas"] == delta, "registration must list exact textual deltas"
    )
    review = reg["review"]
    require(
        review.get("registered_section_sha256") == digest(registered)
        and review.get("open_high") == 0
        and review.get("open_critical") == 0
        and review.get("science_changes_reviewed") is True
        and isinstance(review.get("evidence_sha256"), str)
        and re.fullmatch("[0-9a-f]{64}", review["evidence_sha256"]),
        "missing science review binding",
    )

    # Science deltas require a new matching implementation/review. This consumer
    # accepts only a registration marking/date/state edit of the frozen science.
    def science(text):
        return [
            s
            for s in text.decode().splitlines()
            if s and not s.startswith(("## FOCUS-1 ", "STATE:"))
        ]

    require(
        science(registered) == science(draft),
        "science delta needs matching reviewed implementation",
    )
    require(
        reg["bank_sha256"] == file_hash(store.path("bank.json")),
        "registration bank hash",
    )
    completion = evidence_path(store, bfcl, "bfcl-completion")
    require(
        isinstance(reg["preflight_id"], str)
        and re.fullmatch(
            r"results/qwen/bfcl[A-Za-z0-9_-]*preflight[A-Za-z0-9_-]*",
            reg["preflight_id"],
        ),
        "registration must identify the existing BFCL preflight",
    )
    require(completion.get("preflight_id") == reg["preflight_id"], "BFCL job identity")
    require(
        completion.get("terminal_status") in ("completed", "failed", "cancelled")
        and type(completion.get("exit_code")) is int
        and bool(completion.get("recorded_at"))
        and bool(completion.get("terminal_record")),
        "BFCL recorded terminal status required; vanished process is not evidence",
    )
    return dict(
        registration=file_hash(store.path("registration.json")),
        bfcl=file_hash(store.path("bfcl-completion.json")),
        bank=file_hash(store.path("bank.json")),
        registered_section=digest(registered),
    )


def check_bank(store, tokenizer=None, *, test=False):
    manifest = store.read("bank.json")
    require(
        manifest["version"] == VERSION and manifest["python"] == sys.version,
        "generator/Python changed",
    )
    require(
        manifest["reviewed_section_sha256"] == digest(reviewed_section()),
        "protocol changed",
    )
    require(
        manifest["inputs"] == fingerprints(),
        "code/config/trunk/tokenizer hashes changed",
    )
    require(
        manifest["constants"]
        == dict(
            layers=list(LAYERS),
            cells=[list(x) for x in CELLS],
            eos=list(EOS),
            max_new=64,
            delay=128,
            cap=CAP,
            alpha_family=ALPHA,
        ),
        "scientific constants changed",
    )
    require(manifest["splits"]["test"]["count"] == 64, "test count")
    loaded = {}
    for split in ("extraction", "setup", "test") if test else ("extraction", "setup"):
        require(
            file_hash(store.path(split + ".json"))
            == manifest["splits"][split]["sha256"],
            "bank/layout changed: " + split,
        )
        value = store.read(split + ".json")
        require(
            len(value["rows"]) == manifest["splits"][split]["count"], "partition count"
        )
        if tokenizer is not None:
            require(
                bank_layouts(tokenizer, value["rows"]) == value["layouts"],
                "token layouts changed",
            )
        loaded[split] = value["rows"]
    if tokenizer is not None:
        require(
            manifest["tokenizer"] == tokenizer_facts(tokenizer),
            "tokenizer/delay facts changed",
        )
    return manifest, loaded


def allocation_state(store, now=None):
    rows = store.read_log("allocation")
    active, spent = None, 0.0
    for row in rows:
        if row["kind"] == "start":
            require(active is None, "overlapping allocation intervals")
            active = row
        elif row["kind"] == "end":
            require(
                active is not None and row["stage"] == active["stage"],
                "allocation interval pairing",
            )
            require(row["seconds"] >= 0, "negative allocation")
            spent += row["seconds"]
            active = None
        elif row["kind"] == "overrun":
            spent = max(spent, row["charged_seconds"], CAP + 0.000001)
        else:
            raise Invalid("allocation record kind")
    if active is not None:
        spent += max(0, (time.time() if now is None else now) - active["wall_time"])
    return spent, active


def stage_manifest(store, stage, binding):
    result = store.read(stage + ".json")
    require(result["binding"] == binding, stage + " binding changed")
    log = store.read_log(stage)
    require(
        result["records_sha256"] == file_hash(store.path(stage + ".jsonl")),
        stage + " records changed",
    )
    require(result["record_count"] == len(log), stage + " missing records")
    terminal = [
        r
        for r in store.read_log("allocation")
        if r["stage"] == stage and r["kind"] == "end"
    ]
    require(
        len(terminal) == 1
        and terminal[0]["manifest_sha256"] == file_hash(store.path(stage + ".json")),
        stage + " immutable manifest hash/terminal evidence",
    )
    return result


def cumulative_rates(store, initial):
    rates = dict(initial)
    for row in store.read_log("allocation"):
        for kind, value in row.get("rates", {}).items():
            require(
                kind in COST_CLASSES and math.isfinite(value) and value >= 0,
                "allocation timing rate",
            )
            rates[kind] = max(rates.get(kind, 0), value)
    return rates


def preflight(store, stage, registration, bfcl):
    binding = registration_evidence(store, registration, bfcl)
    manifest, banks = check_bank(store)
    del manifest
    spent, active = allocation_state(store)
    if active is not None:
        raise Incomplete("interrupted allocation stays charged; no resumption/retry")
    if spent >= CAP:
        raise Incomplete("allocation cap exhausted")
    for row in store.read_log("allocation"):
        require(row["stage"] != stage, "duplicate stage attempt; no retries/resumption")
    timing, competence, extraction, selection = None, None, None, None
    if stage != "timing":
        timing = stage_manifest(store, "timing", binding)
        require(
            timing["state"] == "READY" and set(timing["rates"]) == set(COST_CLASSES),
            "missing successful timing evidence",
        )
        require(
            all(math.isfinite(v) and v > 0 for v in timing["rates"].values()),
            "vacuous timing rates",
        )
    if stage in ("extract", "select", "run"):
        competence = stage_manifest(store, "competence", binding)
        require(
            competence["state"] == "READY",
            "competence not successful; INELIGIBLE has no fallback",
        )
    if stage in ("select", "run"):
        extraction = stage_manifest(store, "extract", binding)
        require(extraction["state"] == "READY", "missing extraction evidence")
    if stage == "run":
        selection = stage_manifest(store, "select", binding)
        require(
            selection["state"] == "READY"
            and selection["certification"]["state"] == "READY",
            "missing selection/certification; FAIL-ACTUATOR has no fallback",
        )
        require(
            selection["certification"]["decisions"] == 512,
            "incomplete setup certification",
        )
        require(
            selection["frozen_artifacts"]
            == {
                s: file_hash(store.path(s + ".json"))
                for s in (
                    "bank",
                    "registration",
                    "bfcl-completion",
                    "timing",
                    "competence",
                    "extract",
                )
            },
            "selection frozen artifact hashes changed",
        )
        validate_selection(store, selection, extraction)
        # Run may open test contents only after the complete frozen chain passed;
        # its content hash is checked before model import/loading.
        _, banks = check_bank(store, test=True)
    return dict(
        binding=binding,
        banks=banks,
        spent=spent,
        timing=timing,
        competence=competence,
        extraction=extraction,
        selection=selection,
    )


def validate_selection(store, selection_result, extraction):
    selected = selection_result["selected"]
    require(
        (selected["alpha"], selected["layer"]) in CELLS, "unregistered selected cell"
    )
    require(
        selection_result["vectors"] == extraction["vectors"][str(selected["layer"])],
        "selection changed extracted vectors",
    )
    require(
        selection_result["stats"] == extraction["stats"][str(selected["layer"])],
        "selected vector statistics changed",
    )
    vectors = {
        t: torch.tensor(v, dtype=torch.float32)
        for t, v in selection_result["vectors"].items()
    }
    require(
        set(vectors) == {"A", "B"}
        and all(
            v.ndim == 1 and bool(torch.isfinite(v).all()) and float(v.norm()) > 0
            for v in vectors.values()
        ),
        "frozen vector pair",
    )
    require(
        selection_result["vector_sha256"]
        == {t: tensor_hash(v) for t, v in vectors.items()},
        "frozen vector bytes",
    )
    require(
        all(
            math.isclose(
                float(v.norm()), selection_result["stats"]["rho"], rel_tol=1e-6
            )
            for v in vectors.values()
        ),
        "common pair norm",
    )
    expected_labels = (
        ["HIGH-COLLINEARITY"] if selection_result["stats"]["cosine"] > 0.9 else []
    )
    require(selection_result["labels"] == expected_labels, "collinearity label changed")
    cert = [
        r
        for r in store.read_log("select")
        if r.get("kind") == "answer"
        and r["attempt_id"].startswith("select:certification:")
    ]
    require(len(cert) == 512, "missing certification decisions")
    lookup = {(r["episode"], r["phase"], r["arm"]): r for r in cert}
    inventory = {
        (i, p, a)
        for i in range(32)
        for p in PHASES
        for a in ("correct", "swapped", "transplant", "sham")
    }
    require(set(lookup) == inventory, "certification phase/arm inventory")
    for i in range(32):
        for phase in PHASES:
            for a, b in (("transplant", "swapped"), ("sham", "correct")):
                require(
                    lookup[i, phase, a]["output"]["tokens"]
                    == lookup[i, phase, b]["output"]["tokens"],
                    "certification token mismatch",
                )


def load_backend(tokenizer):
    """Future GPU operation. Never reached by generation/help/analyze."""
    os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
    torch.use_deterministic_algorithms(True)
    from stencil.qwen3 import KVCache, Qwen3, prefill_with_eviction

    model = Qwen3()
    model.load_state_dict(
        torch.load(ROOT / MODEL_INPUTS[0], map_location="cpu", weights_only=True),
        strict=True,
    )
    model.requires_grad_(False)
    model = model.to(dtype=torch.bfloat16, device="cuda").eval()
    return Backend(
        model,
        tokenizer,
        lambda: KVCache(model.cfg),
        device="cuda",
        prefill=prefill_with_eviction,
    )


def competence(engine, rows):
    scores = {
        task: dict(visible=0, schema=0, absent_exact=0, n=0) for task in ("A", "B")
    }
    copies = []
    for task in ("A", "B"):
        engine.serial = task
        for original in rows:
            row = dict(original, initial=task)
            for arm, visible in (("visible", True), ("OFF", False)):
                ids = layout(
                    engine.backend.tokenizer,
                    row["lists"]["sort0"],
                    task=task if visible else None,
                )["ids"]
                history = engine.backend.empty()
                record, _ = engine.answer(row, "SET", arm, history, ids, task=task)
                if visible:
                    scores[task]["visible"] += (
                        record["score"]["exact"] and not record["score"]["broken"]
                    )
                else:
                    scores[task]["schema"] += not record["score"]["I"]
                    scores[task]["absent_exact"] += record["score"]["exact"]
            scores[task]["n"] += 1
    engine.serial = "copy"
    for row in rows:
        history, pair = engine.backend.empty(), []
        for j in range(2):
            ids = layout(
                engine.backend.tokenizer,
                row["lists"][f"copy{j}"],
                copy=True,
                retained=bool(j),
            )["ids"]
            record, _ = engine.answer(
                row,
                f"copy{j}",
                "OFF",
                history,
                ids,
                task="OFF",
                purpose=f"copy{j}",
                kind="clear",
            )
            pair.append(record["score"]["exact"] and not record["score"]["broken"])
        copies.append(all(pair))
    passed = (
        all(
            v["visible"] >= 29 and v["schema"] >= 31 and v["n"] == 32
            for v in scores.values()
        )
        and sum(copies) == 32
    )
    return dict(
        state="READY" if passed else "INELIGIBLE",
        tasks=scores,
        copy_pairs=dict(exact=sum(copies), n=len(copies)),
        reasons=[]
        if passed
        else ["frozen 1.7B skill/OFF-copy/OFF-schema competence failed"],
    )


def extract_vectors(engine, rows):
    states = {layer: {t: [] for t in ("A", "B", "OFF")} for layer in LAYERS}
    for row in rows:
        for task in ("A", "B", "OFF"):
            engine.budget.reserve(engine.work, engine.reloads)
            started = engine.budget.clock()
            ids = layout(
                engine.backend.tokenizer,
                row["lists"]["sort0"],
                task=None if task == "OFF" else task,
            )["ids"]
            history = engine.backend.empty()
            record = dict(
                attempt_id=f"extract:{row['episode']}:{task}",
                kind="extraction",
                split="extraction",
                episode=row["episode"],
                task=task,
                inputs=row["lists"]["sort0"],
                prompt_ids=ids,
                prompt_sha256=digest(ids),
                final_token=ids[-1],
                layer_inputs=None,
                hook_events=[],
                exception=None,
                binding=engine.binding,
                seconds=engine.budget.clock() - started,
                charged_seconds=engine.budget.elapsed,
            )
            engine.store.append("attempts", record)
            try:
                _, captured = engine.backend.forward(history, ids, capture=LAYERS)
                require(not history.events, "extraction hook contamination")
                require(set(captured) == set(LAYERS), "missing layer-INPUT captures")
                layer_states = {
                    str(layer): captured[layer][0, -1].detach().float().cpu().tolist()
                    for layer in LAYERS
                }
                for layer in LAYERS:
                    states[layer][task].append(
                        torch.tensor(layer_states[str(layer)], dtype=torch.float32)
                    )
                record["layer_inputs"] = layer_states
            except Exception as exc:
                record.update(
                    exception=f"{type(exc).__name__}: {exc}",
                    seconds=engine.budget.clock() - started,
                    charged_seconds=engine.budget.elapsed,
                )
                engine.store.append(engine.mode, record)
                engine.rows.append(record)
                if isinstance(exc, Invalid):
                    raise
                raise Incomplete(record["exception"]) from exc
            record.update(
                seconds=engine.budget.clock() - started,
                charged_seconds=engine.budget.elapsed,
            )
            engine.store.append(engine.mode, record)
            engine.rows.append(record)
            engine.budget.observe("extraction", engine.budget.clock() - started)
            engine.work["extraction"] -= 1
    vectors, stats, invalid_layers = {}, {}, {}
    for layer, values in states.items():
        try:
            v, s = normalize_pair(values["A"], values["B"], values["OFF"])
            vectors[str(layer)] = {task: vector.tolist() for task, vector in v.items()}
            stats[str(layer)] = s
        except Invalid as exc:
            invalid_layers[str(layer)] = str(exc)
    return dict(
        state="READY" if vectors else "INVALID",
        vectors=vectors,
        stats=stats,
        invalid_layers=invalid_layers,
        reasons=[] if vectors else ["all layers invalid"],
    )


def selection(engine, rows, extraction):
    outcomes = []
    for cell_index, (alpha, layer) in enumerate(CELLS):
        engine.serial = f"{alpha}:{layer}"
        if str(layer) not in extraction["vectors"]:
            outcomes.append(dict(alpha=alpha, layer=layer, state="INVALID-LAYER"))
            continue
        vectors = {
            task: torch.tensor(v, dtype=torch.float32)
            for task, v in extraction["vectors"][str(layer)].items()
        }
        report = {
            t: dict(
                sort=0,
                sort_broken=0,
                joint_copy=0,
                harm=0,
                clear_impositions=0,
                clear_broken=0,
                replay_broken=0,
                keep_broken=0,
                sort_n=0,
                neutral_n=0,
                keep_n=0,
                denominator=32,
            )
            for t in ("A", "B")
        }
        sources = {}
        failed = None
        for task in ("A", "B"):
            engine.serial = f"{alpha}:{layer}:{task}"
            for original in rows:
                row = dict(original, initial=task)
                ids = layout(engine.backend.tokenizer, row["lists"]["sort0"])["ids"]
                history = engine.backend.empty()
                record, _ = engine.answer(
                    row,
                    "SET",
                    "correct",
                    history,
                    ids,
                    task=task,
                    vector=vectors[task],
                    alpha=alpha,
                    layer=layer,
                )
                sources[task, row["episode"]] = history
                r = report[task]
                r["sort"] += record["score"]["exact"] and not record["score"]["broken"]
                r["sort_broken"] += record["score"]["broken"]
                r["sort_n"] += 1
                if r["sort"] + 32 - r["sort_n"] < 29:
                    failed = "sort <29/32"
                elif r["sort_broken"] > 1:
                    failed = "sort breakage >1/32"
                if failed:
                    break
            if failed:
                break
        if not failed:
            for task in ("A", "B"):
                engine.serial = f"{alpha}:{layer}:{task}"
                for original in rows:
                    row = dict(original, initial=task)
                    records, _ = engine.neutral(
                        row,
                        sources[task, row["episode"]],
                        vectors,
                        alpha,
                        layer,
                        keep=False,
                    )
                    c = [x for x in records if x["arm"] == "CLEAR"]
                    p = [x for x in records if x["arm"] == "replay"]
                    pairs = copy_pairs(
                        [x["score"]["exact"] for x in c],
                        [x["score"]["exact"] for x in p],
                        [False, False],
                    )
                    r = report[task]
                    r["neutral_n"] += 1
                    r["joint_copy"] += pairs["C"] and pairs["P"]
                    r["harm"] += pairs["H"]
                    r["clear_impositions"] += any(x["score"]["imposition"] for x in c)
                    r["clear_broken"] += any(x["score"]["broken"] for x in c)
                    r["replay_broken"] += any(x["score"]["broken"] for x in p)
                    if (
                        r["joint_copy"] + 32 - r["neutral_n"] < 31
                        or r["harm"] > 1
                        or r["clear_impositions"]
                    ):
                        failed = "CLEAR/replay joint pairs/harm/imposition"
                    elif r["clear_broken"] > 1 or r["replay_broken"] > 1:
                        failed = "CLEAR/replay breakage"
                    if failed:
                        break
                if failed:
                    break
        if not failed:
            for task in ("A", "B"):
                engine.serial = f"{alpha}:{layer}:{task}"
                for original in rows:
                    row = dict(original, initial=task)
                    records = engine.keep_only(
                        row, sources[task, row["episode"]], vectors, alpha, layer
                    )
                    r = report[task]
                    r["keep_n"] += 1
                    r["keep_broken"] += any(x["score"]["broken"] for x in records)
                    if r["keep_broken"] > 1:
                        failed = "KEEP breakage >1/32"
                        break
                if failed:
                    break
        outcomes.append(
            dict(
                alpha=alpha,
                layer=layer,
                state="REJECTED" if failed else "ELIGIBLE",
                reason=failed,
                tasks=report,
            )
        )
        # Refund unexecuted cells only after an outcome-blind scheduling branch.
        future_cells = 0 if not failed else 8 - cell_index
        engine.work = Counter(remaining_work("run"))
        engine.work.update(
            certification=512,
            canonical=future_cells * 64,
            clear=future_cells * 128,
            replay=future_cells * 128,
            keep=future_cells * 128,
        )
        if failed:
            continue
        engine.serial = "certification"
        start = len(engine.rows)
        for row in rows:
            donor = rows[row["donor"]]
            # Enums captured without inspecting either operand list.
            own_enum, donor_enum = row["initial"], donor["initial"]
            require(other(own_enum) == donor_enum, "donor enum pairing")
            require(
                all(row["lists"][p] != donor["lists"][p] for p in row["lists"]),
                "donor operands must differ",
            )
            engine.main_decisions(row, vectors, alpha, layer, certification=True)
        cert = engine.rows[start:]
        require(
            len(cert) == 512,
            "certification must cover all 32 episodes/four phases/four arms",
        )
        return dict(
            state="READY",
            selected=dict(alpha=alpha, layer=layer),
            cells=outcomes,
            vectors={t: v.tolist() for t, v in vectors.items()},
            vector_sha256={t: tensor_hash(v) for t, v in vectors.items()},
            stats=extraction["stats"][str(layer)],
            trunk_shape=dict(
                n_layer=engine.backend.model.cfg.n_layer,
                d_model=engine.backend.model.cfg.d_model,
            ),
            labels=["HIGH-COLLINEARITY"]
            if extraction["stats"][str(layer)]["cosine"] > 0.9
            else [],
            certification=dict(
                state="READY",
                decisions=len(cert),
                broken={
                    a: sum(
                        any(
                            r["score"]["broken"]
                            for r in cert
                            if r["episode"] == i and r["arm"] == a
                        )
                        for i in range(32)
                    )
                    for a in ("correct", "swapped", "transplant", "sham")
                },
            ),
            frozen_artifacts={
                s: file_hash(engine.store.path(s + ".json"))
                for s in (
                    "bank",
                    "registration",
                    "bfcl-completion",
                    "timing",
                    "competence",
                    "extract",
                )
            },
            reasons=[],
        )
    return dict(
        state="FAIL-ACTUATOR",
        cells=outcomes,
        reasons=["no eligible cell; no automatic fallback"],
    )


def episode_rows(records):
    """Aggregate one observation per complete recipient episode, never per arm."""
    result = []
    for i in range(64):
        answers = [
            r for r in records if r.get("kind") == "answer" and r["episode"] == i
        ]
        lookup = {(r["phase"], r["arm"]): r for r in answers}
        require(len(lookup) == len(answers), "duplicate phase/arm decision")
        inventory = {(phase, arm) for phase in PHASES for arm in MAIN_ARMS}
        inventory |= {
            (f"copy{j}", arm) for j in range(2) for arm in ("CLEAR", "KEEP", "replay")
        }
        inventory.add(("HOLD", "transient"))
        require(
            set(lookup) <= inventory,
            "test contains transplant/sham or unknown decision",
        )
        if set(lookup) != inventory:
            continue

        def succeeds(arm, phases, target_name, lookup=lookup):
            return all(
                lookup[p, arm]["score"][target_name]
                and not lookup[p, arm]["score"]["broken"]
                for p in phases
            )

        copies = {
            arm: [lookup[f"copy{j}", arm]["score"]["exact"] for j in range(2)]
            for arm in ("CLEAR", "replay", "KEEP")
        }
        pairs = copy_pairs(copies["CLEAR"], copies["replay"], copies["KEEP"])
        audits = [r for r in records if r.get("kind") == "pair" and r["episode"] == i]
        result.append(
            dict(
                episode=i,
                initial=answers[0]["initial"],
                S=succeeds("correct", PHASES[:2], "recipient"),
                O=succeeds("OFF", PHASES[:2], "recipient"),
                W=succeeds("swapped", PHASES, "donor"),
                V=succeeds("OFF", PHASES, "donor"),
                R=succeeds("shuffled", PHASES, "recipient")
                or succeeds("shuffled", PHASES, "donor"),
                **pairs,
                clear_imposition=any(
                    lookup[f"copy{j}", "CLEAR"]["score"]["imposition"] for j in range(2)
                ),
                keep_imposition=any(
                    lookup[f"copy{j}", "KEEP"]["score"]["imposition"] for j in range(2)
                ),
                integrity=len(audits) == 2
                and all(r["comparison"]["nonvacuous"] for r in audits),
                broken={
                    arm: any(r["score"]["broken"] for r in answers if r["arm"] == arm)
                    for arm in TEST_ARMS
                },
            )
        )
    return result


def reliability(records):
    groups = {}
    for r in records:
        if r.get("kind") != "answer":
            continue
        key = f"{r['arm']}:{r['phase']}:{r['initial']}"
        v = groups.setdefault(
            key,
            dict(
                n=0,
                exact=0,
                recipient=0,
                donor=0,
                schema=0,
                broken=0,
                I=0,
                T=0,
                R=0,
                impositions=0,
            ),
        )
        v["n"] += 1
        for metric in ("exact", "recipient", "donor", "broken", "I", "T", "R"):
            v[metric] += bool(r["score"][metric])
        v["schema"] += not r["score"]["I"]
        v["impositions"] += r["score"]["imposition"]
    return groups


def impossible(records):
    answers = [r for r in records if r.get("kind") == "answer"]
    for arm in INTERVENTIONS:
        if (
            len(
                {
                    r["episode"]
                    for r in answers
                    if r["arm"] == arm and r["score"]["broken"]
                }
            )
            >= 2
        ):
            return arm + " second broken episode"
    if any(r["arm"] == "CLEAR" and r["score"]["imposition"] for r in answers):
        return "CLEAR old-task imposition"
    harmed = {
        r["episode"]
        for r in records
        if r.get("kind") == "pair" and r["copy_pair"] == [False, True]
    }
    if len(harmed) > 1:
        return "second residual-harm episode"
    # A single known failed checkpoint makes its conjunction unattainable for
    # that episode, even before its remaining decisions have been scheduled.
    for arm, phases, metric in (
        ("correct", PHASES[:2], "recipient"),
        ("swapped", PHASES, "donor"),
    ):
        failed = {
            r["episode"]: r["initial"]
            for r in answers
            if r["arm"] == arm
            and r["phase"] in phases
            and (r["score"]["broken"] or not r["score"].get(metric, False))
        }
        if len(failed) > 16 or any(
            sum(t == task for t in failed.values()) > 8 for task in ("A", "B")
        ):
            return arm + " episode/stratum count floor unattainable"
    complete = episode_rows(records)
    verdict = endpoints(complete)
    return "; ".join(verdict["reasons"]) if verdict["state"] == "FAIL" else None


def run_test(engine, rows, selection_result):
    vectors = {
        t: torch.tensor(v, dtype=torch.float32)
        for t, v in selection_result["vectors"].items()
    }
    alpha, layer = (selection_result["selected"][k] for k in ("alpha", "layer"))

    def stop(records):
        reason = impossible(records)
        if reason:
            raise StopRun(reason)

    engine.stop_callback = stop
    for row in rows:
        _, histories = engine.main_decisions(row, vectors, alpha, layer)
        engine.transient(row, histories["SET"], layer)
        engine.neutral(row, histories["BACK"], vectors, alpha, layer)
        stop(engine.rows)
    validate_run_records(
        engine.rows,
        rows,
        bank_layouts(engine.backend.tokenizer, rows),
        selection_result,
        engine.binding,
    )
    verdict = endpoints(
        episode_rows(engine.rows), cap_overrun=engine.budget.elapsed > CAP
    )
    verdict["reliability"] = reliability(engine.rows)
    verdict["labels"] += selection_result["labels"]
    return verdict


def validate_run_records(records, rows, layouts, selection_result, binding):
    selected = selection_result["selected"]
    expected_keys = (
        {(p, a) for p in PHASES for a in MAIN_ARMS}
        | {(f"copy{j}", a) for j in range(2) for a in ("CLEAR", "KEEP", "replay")}
        | {("HOLD", "transient")}
    )
    seen, by_id = set(), {}
    for record in records:
        require(record["binding"] == binding, "record manifest binding changed")
        if record["kind"] == "pair":
            continue
        require(
            record["kind"] == "answer" and RECORD_FIELDS <= record.keys(),
            "malformed decision record",
        )
        i, phase, arm = record["episode"], record["phase"], record["arm"]
        require(
            type(i) is int and 0 <= i < 64 and (phase, arm) in expected_keys,
            "record inventory",
        )
        require((i, phase, arm) not in seen, "duplicate decision record")
        seen.add((i, phase, arm))
        by_id[record["attempt_id"]] = record
        row, out = rows[i], record["output"]
        purpose = phase if phase.startswith("copy") else f"sort{PHASES.index(phase)}"
        values = row["lists"][purpose]
        own = (
            row["initial"]
            if phase.startswith("copy")
            else schedule(row["initial"])[PHASES.index(phase)]
        )
        donor = other(own)
        require(
            record["inputs"] == values
            and record["initial"] == row["initial"]
            and record["split"] == "test"
            and record["mode"] == "run",
            "stale operands/source split",
        )
        require(
            record["recipient"] == i
            and record["donor"] == row["donor"]
            and record["recipient_enum"] == own
            and record["donor_enum"] == donor,
            "source/recipient/donor mapping",
        )
        expected_enum = (
            "OFF"
            if arm in ("OFF", "CLEAR", "replay")
            else donor
            if arm == "swapped"
            else own
        )
        require(
            record["source_enum"] == expected_enum
            and record["source"] == (row["donor"] if arm == "swapped" else i),
            "operand-blind enum/source mapping",
        )
        expected = target(
            values,
            "OFF"
            if phase.startswith("copy") or arm == "OFF"
            else donor
            if arm == "swapped"
            else own,
        )
        require(
            record["expected"] == expected
            and record["recipient_target"] == target(values, own)
            and record["donor_target"] == target(values, donor),
            "comparison inputs",
        )
        tokens = out["tokens"]
        require(
            isinstance(tokens, list)
            and all(type(t) is int and t >= 0 for t in tokens)
            and len(tokens) <= 64,
            "raw generated tokens",
        )
        require(not any(t in EOS for t in tokens[:-1]), "tokens after EOS")
        require(
            out["eos"] == (tokens[-1] if tokens and tokens[-1] in EOS else None),
            "raw EOS fact",
        )
        score = score_reply(
            out["text"],
            tokens,
            expected,
            deadline=out["deadline"],
            exception=out["exception"],
            old_target=target(values, row["initial"])
            if phase.startswith("copy")
            else None,
        )
        score.update(
            recipient=score_reply(out["text"], tokens, target(values, own))["exact"],
            donor=score_reply(out["text"], tokens, target(values, donor))["exact"],
        )
        require(score == record["score"], "tampered scores")
        full_prompt = out["history_before"] + out["prompt_ids"]
        require(
            record["layout"]["ids"] == full_prompt
            and record["layout"]["sha256"] == digest(full_prompt),
            "prompt/layout hash",
        )
        require(
            record["layout"]["positions"] == list(range(len(full_prompt))),
            "absolute positions",
        )
        require(
            out["history_after"] == full_prompt + tokens
            and out["final_position"] == len(full_prompt) + len(tokens),
            "omitted final token/secret rebuild",
        )
        require(
            bool(out["final_kv_sha256"]) and bool(out["first_logits_sha256"]),
            "missing cache/logit evidence",
        )
        on = arm in ("correct", "swapped", "shuffled", "KEEP")
        events = out["hook_events"]
        if on:
            require(
                record["vector"]["alpha"] == selected["alpha"]
                and record["vector"]["layer"] == selected["layer"],
                "dose/layer changed",
            )
            require(
                record["vector"]["norm"] > 0 and len(events) == len(tokens) + 1,
                "absent hook calls",
            )
            require(
                [e["generated_position"] for e in events]
                == list(range(len(tokens) + 1)),
                "decode hook schedule",
            )
            require(
                [e["absolute_position"] for e in events]
                == list(range(len(full_prompt) - 1, len(full_prompt) + len(tokens))),
                "last-position hook placement",
            )
            require(
                all(
                    e["alpha"] == selected["alpha"]
                    and e["norm"] > 0
                    and e["vector_sha256"] == record["vector"]["sha256"]
                    for e in events
                ),
                "actual hook/dose binding",
            )
            if "vectors" in selection_result:
                vector = (
                    random_directions(
                        "test",
                        i,
                        selection_result["trunk_shape"]["d_model"],
                        float(torch.tensor(selection_result["vectors"]["A"]).norm()),
                    )[own]
                    if arm == "shuffled"
                    else torch.tensor(
                        selection_result["vectors"][expected_enum], dtype=torch.float32
                    )
                )
                require(
                    record["vector"]["sha256"] == tensor_hash(vector),
                    "random/selected vector changed across episode",
                )
        else:
            require(
                not events and record["vector"]["alpha"] == 0, "OFF hook contamination"
            )
        frozen = layouts[str(i)][purpose]
        if arm in MAIN_ARMS:
            ids = frozen["main"]["ids"]
            require(
                full_prompt == ids and out["history_before"] == ids[:-1],
                "earlier main-arm prompts/replies",
            )
            match = record["matching"]
            require(
                match
                and match["prompt_ids"] == ids
                and match["position"] == len(ids) - 1
                and set(match["matched_arms"]) == set(MAIN_ARMS),
                "unmatched canonical branches",
            )
    lookup = {(r["episode"], r["phase"], r["arm"]): r for r in by_id.values()}
    for record in by_id.values():
        i, phase, arm, out = (
            record["episode"],
            record["phase"],
            record["arm"],
            record["output"],
        )
        if arm in MAIN_ARMS:
            matches = [
                r["matching"]
                for r in by_id.values()
                if r["episode"] == i and r["phase"] == phase and r["arm"] in MAIN_ARMS
            ]
            require(
                len({digest(m) for m in matches}) == 1,
                "canonical equality witness changed",
            )
            continue
        source_phase = "SET" if arm == "transient" else "BACK"
        source = lookup.get((i, source_phase, "correct"))
        require(source is not None, "missing steered fork source")
        prior = source["output"]["history_after"]
        if phase == "copy1":
            previous_arm = "CLEAR" if arm == "replay" else arm
            previous = lookup.get((i, "copy0", previous_arm))
            require(previous is not None, "missing actual first neutral reply")
            prior = previous["output"]["history_after"]
        require(
            out["history_before"] == prior,
            "query-two replay used its own reply or lost retained history",
        )
        purpose = "sort1" if arm == "transient" else phase
        variant = "transient" if arm == "transient" else "retained"
        require(
            out["prompt_ids"] == layouts[str(i)][purpose][variant]["ids"],
            "retained prompt/delay layout",
        )
        if arm in ("CLEAR", "replay"):
            c = record["comparison"]
            require(
                c
                and c["nonvacuous"]
                and c["history_ids"] == prior
                and c["history_sha256"] == digest(prior),
                "missing residual comparison",
            )
            require(
                c["source_tokens"] == source["output"]["history_after"]
                and c["source_kv_sha256"] == source["output"]["final_kv_sha256"],
                "secret rebuild/source mismatch",
            )
            if phase == "copy0":
                require(
                    c["retained_kv_sha256"] == source["output"]["final_kv_sha256"],
                    "CLEAR source cache rebuilt",
                )
            else:
                require(
                    c["retained_kv_sha256"]
                    == lookup[i, "copy0", "CLEAR"]["output"]["final_kv_sha256"],
                    "second CLEAR query cache rebuilt",
                )
            require(
                c["source_events"]
                and all(e["alpha"] != 0 and e["norm"] > 0 for e in c["source_events"]),
                "vacuous source events",
            )
            deltas = c["kv_deltas"]
            require(
                len(deltas) == out["cache_layers"]
                and len(deltas) > selected["layer"]
                and [d["layer"] for d in deltas] == list(range(len(deltas))),
                "every-layer K/V audit",
            )
            require(
                all(
                    math.isfinite(d[k]) and d[k] >= 0
                    for d in deltas
                    for k in ("k", "v")
                ),
                "invalid K/V deltas",
            )
            require(
                all(d["k"] > 0 and d["v"] > 0 for d in deltas[selected["layer"] :]),
                "vacuous affected-layer residuals",
            )
    pairs_seen = set()
    for record in records:
        if record["kind"] != "pair":
            continue
        require(
            (record["episode"], record["phase"]) not in pairs_seen,
            "duplicate neutral audit",
        )
        pairs_seen.add((record["episode"], record["phase"]))
        c, p = by_id.get(record["clear_id"]), by_id.get(record["replay_id"])
        require(c is not None and p is not None, "missing paired decisions")
        require(
            c["arm"] == "CLEAR"
            and p["arm"] == "replay"
            and c["episode"] == p["episode"] == record["episode"]
            and c["phase"] == p["phase"] == record["phase"],
            "mismatched neutral audit",
        )
        require(
            record["copy_pair"] == [c["score"]["exact"], p["score"]["exact"]]
            and record["imposition_pair"]
            == [c["score"]["imposition"], p["score"]["imposition"]]
            and record["token_equal"]
            == (c["output"]["tokens"] == p["output"]["tokens"]),
            "paired score/token audit",
        )
        require(
            record["first_logit_delta"] is not None
            and math.isfinite(record["first_logit_delta"])
            and record["first_logit_delta"] >= 0,
            "missing/nonfinite logit delta",
        )
        deltas = record["query_kv_deltas"]
        require(
            len(deltas) == c["output"]["cache_layers"]
            and [d["layer"] for d in deltas] == list(range(len(deltas)))
            and all(
                math.isfinite(d[k]) and d[k] >= 0 for d in deltas for k in ("k", "v")
            )
            and all(d["k"] > 0 and d["v"] > 0 for d in deltas[selected["layer"] :]),
            "missing/vacuous first-decision K/V audit",
        )


def analyze(store):
    records = store.read_log("run")
    spent, active = allocation_state(store)
    base = endpoints([])
    base.update(
        reasons=["no complete test attempt"],
        reliability=reliability(records),
        observed_decisions=sum(r.get("kind") == "answer" for r in records),
    )
    if not records:
        # Preserve earlier terminal failure states without opening test contents.
        for stage in ("select", "extract", "competence", "timing"):
            if store.path(stage + ".json").exists():
                binding = registration_evidence(
                    store,
                    store.path("registration.json"),
                    store.path("bfcl-completion.json"),
                )
                previous = stage_manifest(store, stage, binding)
                if previous["state"] in (
                    "INVALID",
                    "INELIGIBLE",
                    "FAIL-ACTUATOR",
                    "INCOMPLETE",
                ):
                    base.update(
                        state=previous["state"], reasons=previous.get("reasons", [])
                    )
                base["reliability"] = reliability(store.read_log(stage))
                base["stage_scores"] = previous
                break
        return base
    binding = registration_evidence(
        store, store.path("registration.json"), store.path("bfcl-completion.json")
    )
    selection_result = stage_manifest(store, "select", binding)
    require(
        selection_result["state"] == "READY"
        and selection_result["certification"]["decisions"] == 512,
        "missing selection/certification",
    )
    for stage in ("timing", "competence", "extract"):
        require(
            stage_manifest(store, stage, binding)["state"] == "READY",
            "missing preceding " + stage,
        )
    require(
        selection_result["frozen_artifacts"]
        == {
            s: file_hash(store.path(s + ".json"))
            for s in (
                "bank",
                "registration",
                "bfcl-completion",
                "timing",
                "competence",
                "extract",
            )
        },
        "frozen artifacts changed",
    )
    validate_selection(store, selection_result, store.read("extract.json"))
    manifest, banks = check_bank(store, test=True)
    del manifest
    layouts = store.read("test.json")["layouts"]
    validate_run_records(records, banks["test"], layouts, selection_result, binding)
    complete = episode_rows(records)
    verdict = endpoints(complete, cap_overrun=spent > CAP)
    verdict.update(
        reliability=reliability(records),
        observed_decisions=base["observed_decisions"],
        missing_decisions=1472 - base["observed_decisions"],
        allocated_seconds=spent,
        per_query_pairs=[r for r in records if r["kind"] == "pair"],
    )
    verdict["labels"] += selection_result["labels"]
    failure = impossible(records)
    if failure and verdict["state"] != "INVALID":
        verdict["state"] = "FAIL"
        verdict["reasons"].append(failure)
    if active or not store.path("run.json").exists():
        if verdict["state"] == "PASS":
            verdict.update(
                state="INCOMPLETE",
                reasons=["missing terminal test attempt/allocation evidence"],
            )
    else:
        summary = stage_manifest(store, "run", binding)
        if summary["state"] in ("INVALID", "INCOMPLETE"):
            verdict.update(state=summary["state"], reasons=summary["reasons"])
    return verdict


def timing_smoke(engine, rows):
    """Cost measurements only; deliberately no eligibility scoring/selection."""
    tokenizer = engine.backend.tokenizer
    # Choose longest layouts by frozen setup tokens only, never by outputs.
    row = max(
        rows,
        key=lambda r: sum(
            len(layout(tokenizer, v, phase="BACK")["ids"]) for v in r["lists"].values()
        ),
    )
    width = engine.backend.model.cfg.d_model
    vectors = {"A": torch.zeros(width), "B": torch.zeros(width)}
    vectors["A"][0], vectors["B"][1] = 1, 1
    # Smoke directions are disposable basis vectors, never extracted or eligible.
    layer, alpha = 20, 2.0
    engine.serial = "smoke"
    for task in ("A", "B", "OFF"):
        started = engine.budget.clock()
        ids = layout(
            engine.backend.tokenizer,
            row["lists"]["sort0"],
            task=None if task == "OFF" else task,
        )["ids"]
        engine.backend.forward(engine.backend.empty(), ids, capture=LAYERS)
        elapsed = engine.budget.clock() - started
        engine.store.append(
            "timing",
            dict(
                attempt_id="timing:extraction:" + task,
                kind="cost",
                cost_class="extraction",
                seconds=elapsed,
                binding=engine.binding,
            ),
        )
        engine.budget.observe("extraction", elapsed)
    _, histories = engine.main_decisions(row, vectors, alpha, layer)
    engine.transient(row, histories["SET"], layer)
    engine.neutral(row, histories["BACK"], vectors, alpha, layer)
    engine.serial = "smoke-certification"
    engine.main_decisions(row, vectors, alpha, layer, certification=True)
    # Pad with tokenizer IDs from setup JSON operands to measure 64 decode
    # positions even if greedy smoke replies ended early. This is teacher-forced
    # cost measurement, never an answer, competence score, or direction fit.
    sort_layout = max(
        (
            layout(tokenizer, r["lists"][f"sort{j}"], phase="BACK")["ids"]
            for r in rows
            for j in range(4)
        ),
        key=len,
    )
    copy_layout = max(
        (
            layout(tokenizer, r["lists"][f"copy{j}"], copy=True, retained=True)["ids"]
            for r in rows
            for j in range(2)
        ),
        key=len,
    )
    hold_layout = max(
        (
            layout(tokenizer, r["lists"]["sort1"], phase="HOLD", retained=True)["ids"]
            for r in rows
        ),
        key=len,
    )
    generated = (encode(tokenizer, json.dumps(row["lists"]["sort0"])) * 64)[:64]
    for kind in (
        "canonical",
        "retained",
        "clear",
        "keep",
        "replay",
        "certification",
        "transient",
    ):
        started = engine.budget.clock()
        history_ids = (
            sort_layout
            if kind in ("canonical", "certification")
            else (
                sort_layout + generated + hold_layout
                if kind == "transient"
                else sort_layout + generated + copy_layout + generated + copy_layout
            )
        )
        if kind in ("canonical", "certification"):
            clones, _ = engine.backend.canonical(history_ids, MAIN_ARMS)
            history = clones["correct"]
            engine.backend.forward(history, history_ids[-1:])
        else:
            history = engine.backend.teacher_force(history_ids)
        for j, token in enumerate(generated):
            if engine.budget.elapsed >= CAP or engine.budget.clock() - started >= 300:
                raise Incomplete("timing smoke cooperative deadline")
            engine.backend.forward(
                history,
                [token],
                vector=vectors["A"]
                if kind in ("canonical", "certification", "keep")
                else None,
                alpha=alpha,
                layer=layer,
                position=j,
            )
        elapsed = engine.budget.clock() - started
        engine.store.append(
            "timing",
            dict(
                attempt_id="timing:worst:" + kind,
                kind="cost",
                cost_class=kind,
                seconds=elapsed,
                prompt_ids=history_ids,
                teacher_forced_ids=generated,
                hook_events=history.events,
                final_kv_sha256=cache_hash(history.cache),
                binding=engine.binding,
                formal_score=False,
            ),
        )
        engine.budget.observe(kind, engine.budget.clock() - started)
    peak = (
        int(torch.cuda.max_memory_allocated())
        if engine.backend.device == "cuda"
        else None
    )
    require(
        set(engine.budget.rates) == set(COST_CLASSES),
        "timing smoke missing cost classes",
    )
    engine.budget.reserve(remaining_work("competence"), reloads=4)
    return dict(
        state="READY",
        reasons=[],
        rates=engine.budget.rates,
        deadline=min(300, 4 * engine.budget.attempt_estimate),
        peak_memory_bytes=peak,
        formal_competence=False,
        bootstrap="first smoke uses cumulative cap and 300s cooperative checks",
    )


def execute_stage(
    store,
    stage,
    registration,
    bfcl,
    *,
    backend_factory=None,
    tokenizer_factory=None,
    clock=time.monotonic,
    wall_clock=time.time,
):
    started_wall, started = wall_clock(), clock()
    evidence = preflight(store, stage, registration, bfcl)
    rates = cumulative_rates(
        store,
        evidence["timing"]["rates"]
        if evidence["timing"]
        else dict.fromkeys(COST_CLASSES, 0.0),
    )
    budget = Budget(
        evidence["spent"] + clock() - started,
        rates,
        clock=clock,
        frozen_deadline=evidence["timing"]["deadline"] if evidence["timing"] else 300.0,
    )
    work = remaining_work(
        stage if stage in ("extract", "select", "run") else "competence"
    )
    reloads = {"timing": 4, "competence": 3, "extract": 2, "select": 1, "run": 0}[stage]
    if stage != "timing":
        budget.reserve(work, reloads + 1, loading=True)
    store.append(
        "allocation",
        dict(
            attempt_id=stage + ":start",
            kind="start",
            stage=stage,
            wall_time=started_wall,
            binding=evidence["binding"],
        ),
    )
    engine, result = None, None
    try:
        checkpoint = clock()
        tokenizer = (tokenizer_factory or load_tokenizer)()
        check_bank(store, tokenizer, test=stage == "run")
        verification_seconds = clock() - checkpoint
        if budget.elapsed >= CAP:
            raise Incomplete("preload checks exhausted allocation")
        load_start = clock()
        backend = (backend_factory or load_backend)(tokenizer)
        budget.observe(
            "load", clock() - load_start + verification_seconds + checkpoint - started
        )
        if budget.elapsed >= CAP or (stage == "timing" and clock() - load_start > 300):
            raise Incomplete("load exceeded complete next-attempt reservation")
        if stage != "timing":
            budget.reserve(work, reloads)
        engine = Engine(
            backend,
            store,
            stage,
            evidence["binding"],
            budget=budget,
            work={} if stage == "timing" else work,
            reloads=0 if stage == "timing" else reloads,
        )
        if stage == "timing":
            result = timing_smoke(engine, evidence["banks"]["setup"])
        elif stage == "competence":
            result = competence(engine, evidence["banks"]["setup"])
        elif stage == "extract":
            result = extract_vectors(engine, evidence["banks"]["extraction"])
        elif stage == "select":
            result = selection(
                engine, evidence["banks"]["setup"], evidence["extraction"]
            )
        else:
            result = run_test(engine, evidence["banks"]["test"], evidence["selection"])
    except (Invalid, Incomplete, StopRun) as exc:
        result = dict(
            state="INVALID"
            if isinstance(exc, Invalid)
            else "FAIL"
            if isinstance(exc, StopRun)
            else "INCOMPLETE",
            reasons=[str(exc)],
        )
    except Exception as exc:
        result = dict(state="INCOMPLETE", reasons=[f"{type(exc).__name__}: {exc}"])
    finally:
        rows = store.read_log(stage)
        if not store.path(stage + ".jsonl").exists():
            store.append(
                stage,
                dict(
                    attempt_id=stage + ":exception",
                    kind="exception",
                    binding=evidence["binding"],
                    exception=result,
                    charged_seconds=budget.elapsed,
                ),
            )
            rows = store.read_log(stage)
        result.update(
            binding=evidence["binding"],
            records_sha256=file_hash(store.path(stage + ".jsonl")),
            record_count=len(rows),
            rates=dict(budget.rates),
            reliability=reliability(rows),
        )
        if stage == "run" and result["state"] != "PASS":
            observed = episode_rows(rows)
            result.update(
                n=len(observed),
                missing=64 - len(observed),
                scores=endpoints(observed),
                observed_decisions=sum(r.get("kind") == "answer" for r in rows),
            )
        if budget.elapsed > CAP:
            result.update(
                state="INVALID" if result["state"] == "INVALID" else "INCOMPLETE",
                reasons=[*result.get("reasons", []), "allocation cap overrun"],
            )
        store.write(stage + ".json", result)
        # Reserve closing persistence; an observed overrun also gets a permanent
        # marker, so a summary written just before it cannot revive PASS.
        closing_reserve = 1.25 * budget.rates["persistence"]
        charged_seconds = clock() - started + closing_reserve
        store.append(
            "allocation",
            dict(
                attempt_id=stage + ":end",
                kind="end",
                stage=stage,
                wall_time=wall_clock(),
                seconds=charged_seconds,
                closing_persistence_reserve=closing_reserve,
                manifest_sha256=file_hash(store.path(stage + ".json")),
                binding=evidence["binding"],
                rates=dict(budget.rates),
            ),
        )
        if budget.elapsed > CAP or evidence["spent"] + charged_seconds > CAP:
            store.append(
                "allocation",
                dict(
                    attempt_id=stage + ":overrun",
                    kind="overrun",
                    stage=stage,
                    charged_seconds=max(
                        budget.elapsed, evidence["spent"] + charged_seconds
                    ),
                ),
            )
            result.update(
                state="INVALID" if result["state"] == "INVALID" else "INCOMPLETE",
                reasons=[
                    *result.get("reasons", []),
                    "allocation cap overrun including persistence",
                ],
            )
    return result
