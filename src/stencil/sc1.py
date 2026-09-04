"""SC1 v2: source-only retention packages and audited execution primitives.

No benchmark loaders, fitting, model initialization or IO at import time.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import time
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from stencil.bfcl import (
    CONTROL_MARKERS,
    _chunk_char_span,
    _columns_to_spans,
    _token_span,
    _tool_line_spans,
)
from stencil.selector_v2 import split_sentence_spans

VERSION = "SC1-v2.1"
HEADER = "Earlier context restated verbatim:"
OPENER = "<|im_start|>assistant\n<think>\n\n</think>\n\n"
MAX_PREFIX = 2048
MAX_QUERY = 1024
MAX_INPUT = 8192 + MAX_PREFIX + MAX_QUERY + 256
LIMIT = 256
DEADLINE = 300
COST_CAP = 8 * 3600
INTERVENTIONS = (
    "scope_resolver",
    "digest",
    "attention_amplification",
    "residual_steering",
)


def canonical(value):
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    )


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_json(path, value, *, exclusive=False):
    """Durable atomic publication; exclusive rows can never overwrite outputs."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (canonical(value) + "\n").encode()
    temp = path.with_name(path.name + f".{os.getpid()}.tmp")
    with temp.open("xb") as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())
    try:
        if exclusive:
            os.link(temp, path)
            temp.unlink()
        else:
            os.replace(temp, path)
        fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        temp.unlink(missing_ok=True)


def token_ids(tokenizer, text):
    return list(tokenizer.encode(text, add_special_tokens=False).ids)


def window_geometry(P, H):
    if not 0 <= P <= H:
        raise ValueError("invalid renderer geometry")
    R = max(P, H - 1024)
    C = R - P
    return {
        "P": P,
        "H": H,
        "R": R,
        "C": C,
        "B": min(256, C // 4),
        "evict_range": [P, R],
    }


def render_episode(episode, tokenizer, insertion=""):
    """Frozen Qwen message serialization with coordinates recorded as it is built.

    Tools are general schemas in the system block. SC1 overrides native XML call
    framing with the contract's single bare JSON call. Group consecutive tool
    results as in the Qwen template, retaining their semantic source roles.
    Token boundaries come from ONE encoding's offsets, never text searching.
    """
    system = episode["system"]
    tools = episode["tools"]
    if tools:
        system += (
            "\n\n# Tools\n<tools>\n"
            + "\n".join(canonical(t) for t in tools)
            + "\n</tools>"
        )
        system += (
            '\nReturn exactly one bare JSON call: {"name": "operation", '
            '"arguments": {}}. No XML, fences or commentary.'
        )
    text = f"<|im_start|>system\n{system}<|im_end|>\n"
    prefix_end = len(text)
    locations = []
    turns = episode["turns"]
    for i, message in enumerate(turns):
        role, content = message["role"], message["text"]
        if role not in {"user", "tool", "assistant"} or not isinstance(content, str):
            raise ValueError("invalid public message")
        pool_start = len(text)
        if role == "tool":
            if i == 0 or turns[i - 1]["role"] != "tool":
                text += "<|im_start|>user"
            text += "\n<tool_response>\n"
        else:
            text += f"<|im_start|>{role}\n"
        start = len(text)
        text += content
        end = len(text)
        if role == "tool":
            text += "\n</tool_response>"
            if i == len(turns) - 1 or turns[i + 1]["role"] != "tool":
                text += "<|im_end|>\n"
        else:
            text += "<|im_end|>\n"
        locations.append(
            {
                "role": role,
                "content": content,
                "message_index": i,
                "start": start,
                "end": end,
                "pool_start": pool_start,
                "pool_end": len(text),
            }
        )
    history_end = len(text)
    final = (
        f"<|im_start|>user\n{insertion}{episode['final_request']}<|im_end|>\n{OPENER}"
    )
    text += final
    encoding = tokenizer.encode(text, add_special_tokens=False)

    def boundary(char):
        if any(a < char < b for a, b in encoding.offsets):
            raise ValueError("renderer token crosses semantic boundary")
        return sum(b <= char for a, b in encoding.offsets if b > a)

    layout = window_geometry(boundary(prefix_end), boundary(history_end))
    layout.update(
        text=text,
        ids=list(encoding.ids),
        offsets=list(encoding.offsets),
        locations=locations,
        final_text=final,
        final_char_start=history_end,
        prefix_char_end=prefix_end,
        public={k: episode[k] for k in ("system", "tools", "turns", "final_request")},
    )
    if layout["P"] > MAX_PREFIX or len(token_ids(tokenizer, final)) > MAX_QUERY + 256:
        raise ValueError("prefix/query exceeds frozen grammar bounds")
    if len(layout["ids"]) + LIMIT > 40960:
        raise ValueError("40960-position guard")
    return layout


def build_sc1_candidates(layout, tokenizer):
    """Common UNSCORED U, using exactly the frozen LEG A piece segmentation."""
    encoding = type("SourceEncoding", (), {"offsets": layout["offsets"]})()
    decoder = (
        tokenizer.get_added_tokens_decoder()
        if hasattr(tokenizer, "get_added_tokens_decoder")
        else {}
    )
    special = set(decoder)
    candidates, excluded, seen = [], [], set()
    for location in layout["locations"]:
        role, content = location["role"], location["content"]
        index = location["message_index"]
        if role not in {"user", "tool"}:
            excluded.append({"message_index": index, "reason": "role"})
            continue
        pieces = split_sentence_spans(content)
        if role == "tool":
            pieces = [
                (a + s, a + e)
                for a, b in _tool_line_spans(content)
                for s, e in split_sentence_spans(content[a:b])
            ]
        if not pieces:
            excluded.append({"message_index": index, "reason": "sentence_filter"})
        for piece in pieces:
            chunks = _chunk_char_span(tokenizer, content, piece, 128)
            if not chunks:
                excluded.append({"message_index": index, "reason": "empty_tokens"})
            for a, b in chunks:
                a, b = a + location["start"], b + location["start"]
                span = _token_span(encoding, a, b)
                row = {
                    "id": f"{role}:{index}:{a}:{b}",
                    "text": layout["text"][a:b],
                    "role": role,
                    "message_index": index,
                    "char_span": [a, b],
                    "span": list(span or ()),
                }
                reason = None
                if span is None:
                    reason = "unmapped"
                elif span[0] < layout["P"] or span[1] > layout["R"]:
                    reason = (
                        "straddle"
                        if span[0] < layout["R"] < span[1]
                        or span[0] < layout["P"] < span[1]
                        else "outside_old"
                    )
                elif any(
                    m in row["text"] for m in CONTROL_MARKERS
                ) or special.intersection(token_ids(tokenizer, row["text"])):
                    reason = "control_or_special_token"
                elif row["id"] in seen:
                    reason = "duplicate"
                if reason:
                    excluded.append({**row, "reason": reason})
                else:
                    seen.add(row["id"])
                    candidates.append(row)
    return candidates, excluded


def rank_rule(candidates):
    return sorted(
        (
            {
                "candidate": c,
                "key": [
                    0 if c["role"] == "user" else 1,
                    -c["message_index"],
                    -c["char_span"][0],
                    c["char_span"][1],
                ],
            }
            for c in candidates
        ),
        key=lambda r: r["key"],
    )


def rank_clf(candidates, scorer):
    if scorer is None:
        raise ValueError("clf requires frozen scorer")
    before = getattr(scorer, "scorer_truncated_candidates", 0)
    ranked = []
    for role in ("user", "tool"):
        rows = [c for c in candidates if c["role"] == role]
        for start in range(0, len(rows), 64):
            batch = rows[start : start + 64]
            scores = scorer(
                [c["text"] for c in batch], role=role, contexts=[""] * len(batch)
            )
            if len(scores) != len(batch):
                raise ValueError("wrong score count")
            for c, score in zip(batch, scores, strict=True):
                s = float(score)
                if not math.isfinite(s) or not 0 <= s <= 1:
                    raise ValueError("invalid classifier score")
                ranked.append(
                    {
                        "candidate": c,
                        "score": s,
                        "key": [
                            -s if s >= 0.5 else math.inf,
                            -c["message_index"],
                            *c["char_span"],
                        ],
                    }
                )
    return sorted(ranked, key=lambda r: r["key"]), getattr(
        scorer, "scorer_truncated_candidates", before
    ) - before


def admit_whole_spans(ranked, evict_range, B):
    low, high = evict_range
    if B < 0:
        raise ValueError("negative budget")
    columns, admitted, skips = set(), [], []
    for item in ranked:
        row = item["candidate"]
        a, b = row["span"]
        if not low <= a < b <= high:
            raise ValueError("candidate outside eviction range")
        proposed = columns | set(range(a, b))
        if not all(math.isfinite(k) for k in item["key"]):
            skips.append({"id": row["id"], "reason": "ineligible"})
        elif len(proposed) > B:
            skips.append({"id": row["id"], "reason": "budget"})
        else:
            admitted.append(row)
            columns = proposed
    return {
        "admitted": admitted,
        "pins": [list(s) for s in _columns_to_spans(sorted(columns))],
        "columns": sorted(columns),
        "skips": skips,
    }


def build_sc1_echo(admitted, layout, tokenizer, E=256):
    entries, omitted = [], []
    base = len(token_ids(tokenizer, layout["final_text"]))

    def serialize(rows):
        return (
            HEADER
            + "\n"
            + "\n".join(
                f"- {r['role']} turn {r['message_index']}: "
                + json.dumps(r["text"], ensure_ascii=False)
                for r in rows
            )
        )

    text, insertion, count, increase = "", "", 0, 0
    for row in sorted(admitted, key=lambda r: (*r["span"], *r["char_span"])):
        candidate = serialize([*entries, row])
        if any(marker in candidate for marker in CONTROL_MARKERS):
            raise AssertionError("chat control in echo")
        new_insertion = candidate + "\n\n"
        final = layout["final_text"].replace(
            "<|im_start|>user\n", "<|im_start|>user\n" + new_insertion, 1
        )
        new_count = len(token_ids(tokenizer, new_insertion))
        new_increase = len(token_ids(tokenizer, final)) - base
        if new_count <= E and new_increase <= E:
            entries.append(row)
            text, insertion, count, increase = (
                candidate,
                new_insertion,
                new_count,
                new_increase,
            )
        else:
            omitted.append(row["id"])
    return {
        "text": text,
        "insertion": insertion,
        "entries": entries,
        "omitted": omitted,
        "tokens": count,
        "increase": increase,
        "omission_rate": len(omitted) / len(admitted) if admitted else 0,
        "by_role": {
            role: {
                "pinned": sum(c["role"] == role for c in admitted),
                "echoed": sum(c["role"] == role for c in entries),
            }
            for role in ("user", "tool")
        },
    }


def select_policy(layout, tokenizer, arm, scorer=None):
    start = time.monotonic()
    candidates, exclusions = build_sc1_candidates(layout, tokenizer)
    built = time.monotonic()
    truncations = 0
    if arm == "clf":
        ranked, truncations = rank_clf(candidates, scorer)
    elif arm == "rule":
        ranked = rank_rule(candidates)
    elif arm in {"full", "evicted"}:
        ranked = []
    else:
        raise ValueError("unknown arm")
    scored = time.monotonic()
    admission = admit_whole_spans(ranked, layout["evict_range"], layout["B"])
    admitted = time.monotonic()
    echo = build_sc1_echo(admission["admitted"], layout, tokenizer)
    end = time.monotonic()
    # JSON cannot encode infinity; preserve the registered sentinel explicitly.
    serial_rank = [
        {**r, "key": [k if math.isfinite(k) else "+infinity" for k in r["key"]]}
        for r in ranked
    ]
    return {
        "candidates": candidates,
        "candidate_hash": digest(candidates),
        "exclusions": exclusions,
        "rank": serial_rank,
        "admission": admission,
        "echo": echo,
        "scorer_truncations": truncations,
        "span_lengths": [c["span"][1] - c["span"][0] for c in candidates],
        "latency": {
            "candidate": built - start,
            "scoring": scored - built,
            "admission": admitted - scored,
            "echo": end - admitted,
        },
    }


@dataclass
class InterventionCounter:
    counts: dict = field(default_factory=lambda: dict.fromkeys(INTERVENTIONS, 0))

    def invoke(self, name, fn, *args, **kwargs):
        if name not in self.counts:
            raise ValueError("unknown intervention")
        self.counts[name] += 1
        self.assert_zero()
        return fn(*args, **kwargs)

    def assert_zero(self):
        if any(self.counts.values()):
            raise RuntimeError("SC1 intervention counter nonzero; INVALID")

    def forward(self, model, tokens, *, cache, **kwargs):
        for key in ("inj", "residual_hook"):
            if kwargs.get(key) is not None:
                self.invoke("residual_steering", lambda: None)
        for key in ("attn_bias", "bias_hook", "deficit_hook"):
            if kwargs.get(key) is not None:
                self.invoke("attention_amplification", lambda: None)
        self.assert_zero()
        return model(tokens, cache=cache, **kwargs)


def prefill_sc1(model, cache, tokens, *, history_end, evict_range, pins, interventions):
    from stencil.qwen3 import prefill_with_eviction

    if cache.length or any(k is not None for k in cache.k):
        raise AssertionError("SC1 requires a fresh KV cache")
    interventions.assert_zero()
    low, high = evict_range if evict_range is not None else (0, 0)
    retained = [
        i
        for i in range(history_end)
        if not low <= i < high or any(a <= i < b for a, b in pins)
    ]

    def forward(ids, *, cache, **kwargs):
        out = interventions.forward(model, ids, cache=cache, **kwargs)
        width = (
            history_end
            if cache.length == history_end
            else len(retained) + cache.length - history_end
        )
        for k, v in zip(cache.k, cache.v, strict=True):
            if k is None or v is None or k.shape[2] != width or v.shape[2] != width:
                raise AssertionError("per-layer cache width mismatch")
        return out

    logits, mapping, before, after = prefill_with_eviction(
        forward,
        cache,
        tokens,
        history_end=history_end,
        evict_range=evict_range,
        keep=pins,
        eviction_timing="pre-query",
    )
    if evict_range is not None and list(mapping) != retained:
        raise AssertionError("eviction position map mismatch")
    if cache.length != tokens.shape[1]:
        raise AssertionError("absolute RoPE counter changed")
    return logits, {
        "before": before,
        "after_eviction": after,
        "retained_positions": retained,
        "layers": [
            {
                "width": k.shape[2],
                "positions": retained + list(range(history_end, cache.length)),
            }
            for k in cache.k
        ],
        "absolute_length": cache.length,
    }


def output_flags(text, ids, schema_valid, tokenizer):
    normalized = " ".join(unicodedata.normalize("NFKC", text).casefold().split())
    tokens = token_ids(tokenizer, normalized)
    repeated = any(
        all(tokens[i : i + 4] == tokens[i + 4 * j : i + 4 * j + 4] for j in range(1, 8))
        for i in range(max(0, len(tokens) - 31))
    )
    invalid = not schema_valid
    truncated = len(ids) >= 256 and invalid
    return {
        "I": invalid,
        "T": truncated,
        "R": repeated,
        "F": invalid or truncated or repeated,
    }


def mcnemar(b, c):
    if min(b, c) < 0 or int(b) != b or int(c) != c:
        raise ValueError("nonnegative integer cells required")
    return sum(math.comb(b + c, j) for j in range(b, b + c + 1)) / 2 ** (b + c)


def binomial_mass(n, k, p):
    return math.comb(n, k) * p**k * (1 - p) ** (n - k)


def exact_power(N=256, q=0.20, delta=0.05):
    if not 0 < q <= 1 or not -q <= delta <= q:
        raise ValueError("invalid power cell")
    test = joint = 0.0
    win = (q + delta) / (2 * q)
    for m in range(N + 1):
        prob_m = binomial_mass(N, m, q)
        for b in range(m + 1):
            if mcnemar(b, m - b) <= 0.05:
                mass = prob_m * binomial_mass(m, b, win)
                test += mass
                if 2 * b - m >= 13:
                    joint += mass
    return {"N": N, "q": q, "delta": delta, "test": test, "joint": joint}


def clopper_pearson(k, n, confidence=0.975):
    if not 0 <= k <= n or n <= 0:
        raise ValueError("invalid binomial count")
    tail = (1 - confidence) / 2

    def quantile(target, start):
        low, high = 0.0, 1.0
        for _ in range(60):
            mid = (low + high) / 2
            survival = sum(binomial_mass(n, j, mid) for j in range(start, n + 1))
            if survival < target:
                low = mid
            else:
                high = mid
        return (low + high) / 2

    return (
        0.0 if k == 0 else quantile(tail, k),
        1.0 if k == n else quantile(1 - tail, k + 1),
    )


def analyze_pairs(pairs):
    if len(pairs) != 256 or len({r["id"] for r in pairs}) != 256:
        raise ValueError("analysis requires exactly 256 unique complete pairs")
    cells, corruption = Counter(), Counter()
    U = K = 0
    latency = {a: 0.0 for a in ("clf", "rule")}
    flags = {a: Counter() for a in latency}
    subgroups = {}
    for row in pairs:
        if set(row["arms"]) != {"clf", "rule"}:
            raise ValueError("incomplete pair")
        clf, rule = row["arms"]["clf"], row["arms"]["rule"]
        cells[f"{int(clf['success'])}{int(rule['success'])}"] += 1
        corruption[f"{int(clf['corruption'])}{int(rule['corruption'])}"] += 1
        U += bool(clf["flags"]["F"] and not rule["flags"]["F"])
        K += bool(clf["corruption"] and not rule["corruption"])
        for arm in latency:
            latency[arm] += row["arms"][arm]["latency"]["total"] / 256
            flags[arm].update({k: int(v) for k, v in row["arms"][arm]["flags"].items()})
        for factor, value in row.get("assignments", {}).items():
            group = subgroups.setdefault(
                f"{factor}={value}", {"n": 0, "clf": 0, "rule": 0}
            )
            group["n"] += 1
            group["clf"] += clf["success"]
            group["rule"] += rule["success"]
    b, c = cells["10"], cells["01"]
    p = mcnemar(b, c)
    lb, ub = clopper_pearson(b, 256)
    lc, uc = clopper_pearson(c, 256)
    gates = {
        "i": p <= 0.05 and b - c >= 13,
        "ii": U <= 2,
        "iii": K == 0,
        "iv": latency["clf"] <= 1.25 * latency["rule"],
    }
    return {
        "status": "COMPLETE",
        "N": 256,
        "b": b,
        "c": c,
        "D_hat": (b - c) / 256,
        "p": p,
        "cells": {k: cells[k] for k in ("00", "01", "10", "11")},
        "interval": [lb - uc, ub - lc],
        "rates": {"clf": (b + cells["11"]) / 256, "rule": (c + cells["11"]) / 256},
        "U": U,
        "K": K,
        "flags": flags,
        "corruption_cells": dict(corruption),
        "corruption_totals": {
            "clf": corruption["10"] + corruption["11"],
            "rule": corruption["01"] + corruption["11"],
        },
        "mean_latency": latency,
        "gates": gates,
        "subgroups": subgroups,
        "adopt": "clf" if all(gates.values()) else "rule",
        "conclusion": "learned advantage demonstrated"
        if all(gates.values())
        else "no worthwhile learned advantage demonstrated",
    }


@dataclass
class CostMeter:
    spent: float = 0.0
    estimates: dict = field(
        default_factory=lambda: {"prefill": 0.0, "token": 0.0, "cpu": 0.0, "check": 0.0}
    )
    remaining_initialization: float = 0.0
    samples: list = field(default_factory=list)

    def project(self, remaining):
        e = self.estimates
        return (
            self.spent
            + self.remaining_initialization
            + remaining
            * 1.25
            * (e["prefill"] + 256 * e["token"] + e["cpu"] + e["check"])
        )

    def can_start(self, remaining):
        return self.spent + DEADLINE <= COST_CAP and self.project(remaining) <= COST_CAP

    def observe(self, timing, measured_length, maximum_length=MAX_INPUT):
        if measured_length <= 0 or any(
            not math.isfinite(v) or v < 0 for v in timing.values()
        ):
            raise ValueError("invalid timing sample")
        r = max(1.0, maximum_length / measured_length)
        scaled = {
            "prefill": timing["prefill"] * r * r,
            "token": timing["token"] * r,
            "cpu": timing["cpu"],
            "check": timing["check"],
        }
        self.estimates = {k: max(self.estimates[k], scaled[k]) for k in scaled}
        self.samples.append(
            {
                "measured_length": measured_length,
                "maximum_length": maximum_length,
                "r": r,
                "raw": timing,
                "scaled": scaled,
            }
        )


class RunStore:
    """Append-only attempt log plus immutable arm files. No partial inference API."""

    def __init__(self, root, manifest_id):
        self.root, self.manifest_id = Path(root), manifest_id
        self.root.mkdir(parents=True, exist_ok=True)
        self.journal = self.root / "attempts.jsonl"

    def arm_path(self, episode, arm):
        if any(
            c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
            for c in episode
        ):
            raise ValueError("unsafe episode ID")
        if arm not in {"clf", "rule", "full", "evicted"}:
            raise ValueError("unknown arm")
        return self.root / f"{episode}.{arm}.json"

    def events(self):
        rows = (
            [json.loads(line) for line in self.journal.read_text().splitlines()]
            if self.journal.exists()
            else []
        )
        previous = None
        for row in rows:
            payload = {k: v for k, v in row.items() if k != "hash"}
            if (
                row["manifest_id"] != self.manifest_id
                or row["previous"] != previous
                or digest(payload) != row["hash"]
            ):
                raise RuntimeError("journal hash/manifest mismatch")
            previous = row["hash"]
        return rows

    def append(self, event):
        events = self.events()
        row = {
            **event,
            "manifest_id": self.manifest_id,
            "previous": events[-1]["hash"] if events else None,
        }
        row["hash"] = digest(row)
        with self.journal.open("a") as f:
            f.write(canonical(row) + "\n")
            f.flush()
            os.fsync(f.fileno())

    def start(self, episode, arm, attempt):
        if self.arm_path(episode, arm).exists():
            raise RuntimeError("completed arm cannot be retried")
        self.pending(episode, [arm])
        self.append(
            {
                "event": "start",
                "episode_id": episode,
                "arm": arm,
                "attempt_id": attempt,
                "wall_start": time.time(),
            }
        )

    def complete(self, row):
        path = self.arm_path(row["episode_id"], row["arm"])
        if path.exists():
            raise RuntimeError("completed arm is immutable")
        if row["manifest_id"] != self.manifest_id:
            raise RuntimeError("manifest mismatch")
        events = [e for e in self.events() if e.get("attempt_id") == row["attempt_id"]]
        if not events or events[-1]["event"] != "start":
            raise RuntimeError("completion without matching started attempt")
        # Write-ahead completion binds exact bytes even if the host dies at publication.
        expected = hashlib.sha256((canonical(row) + "\n").encode()).hexdigest()
        self.append(
            {
                "event": "completion_prepared",
                "episode_id": row["episode_id"],
                "arm": row["arm"],
                "attempt_id": row["attempt_id"],
                "output_hash": expected,
                "row": row,
            }
        )
        atomic_json(path, row, exclusive=True)
        self.append(
            {
                "event": "completed",
                "episode_id": row["episode_id"],
                "arm": row["arm"],
                "attempt_id": row["attempt_id"],
                "output_hash": expected,
            }
        )

    def interrupt(self, episode, arm, attempt, reason, elapsed, evidence=None):
        if (
            reason not in {"host_loss", "process_loss", "device_loss", "resource_loss"}
            or elapsed < 0
        ):
            raise ValueError("not an infrastructure interruption")
        active = [e for e in self.events() if e.get("attempt_id") == attempt]
        if (
            not active
            or active[-1]["event"] != "start"
            or self.arm_path(episode, arm).exists()
        ):
            raise RuntimeError("only a genuinely missing attempt can be interrupted")
        self.append(
            {
                "event": "interrupted",
                "episode_id": episode,
                "arm": arm,
                "attempt_id": attempt,
                "reason": reason,
                "elapsed": elapsed,
                "evidence": evidence,
            }
        )

    def pending(self, episode, arms):
        pending = []
        events = self.events()
        for arm in arms:
            path = self.arm_path(episode, arm)
            history = [
                e
                for e in events
                if e.get("episode_id") == episode and e.get("arm") == arm
            ]
            prepared = [e for e in history if e["event"] == "completion_prepared"]
            if prepared and not path.exists():
                atomic_json(path, prepared[-1]["row"], exclusive=True)
            if path.exists():
                completed = [
                    e
                    for e in history
                    if e["event"] in {"completed", "completion_prepared"}
                ]
                if not completed or file_hash(path) != completed[-1]["output_hash"]:
                    raise RuntimeError("completed output hash mismatch")
            elif history and history[-1]["event"] == "start":
                raise RuntimeError(
                    "missing arm requires journaled external interruption evidence"
                )
            else:
                pending.append(arm)
        return pending

    def prior_elapsed(self, episode, arm):
        return sum(
            e["elapsed"]
            for e in self.events()
            if e["event"] == "interrupted"
            and e["episode_id"] == episode
            and e["arm"] == arm
        )

    def write_pair(self, episode, arms, assignments):
        if self.pending(episode, arms):
            raise RuntimeError("cannot publish incomplete pair")
        row = {
            "id": episode,
            "manifest_id": self.manifest_id,
            "assignments": assignments,
            "arms": {
                a: json.loads(self.arm_path(episode, a).read_text()) for a in arms
            },
        }
        path = self.root / f"{episode}.pair.json"
        if path.exists():
            if json.loads(path.read_text()) != row:
                raise RuntimeError("paired output hash mismatch")
        else:
            atomic_json(path, row, exclusive=True)
        return row


class QwenBackend:
    """Future model execution adapter. Instantiated only after all launch gates."""

    def __init__(self, root, trunk):
        import torch

        from stencil.qwen3 import Qwen3, Qwen3Config

        cfg = Qwen3Config.from_hf(Path(root) / f"models/qwen3-{trunk}-hf/config.json")
        self.model = Qwen3(cfg)
        state = torch.load(
            Path(root) / f"models/qwen3-{trunk}.pt",
            map_location="cpu",
            weights_only=True,
        )
        self.model.load_state_dict(state, strict=True)
        for module in self.model.modules():
            if hasattr(module, "hf_compatible"):
                module.hf_compatible = True
        self.model.to(torch.bfloat16).cuda().eval()
        torch.use_deterministic_algorithms(True)
        self.device = torch.device("cuda")
        self.eos = {151645, 151643}

    def generate(self, layout, pins, arm, interventions, deadline_at):
        import torch

        from stencil.qwen3 import KVCache

        cache = KVCache(self.model.cfg)
        ids = torch.tensor([layout["ids"]], device=self.device)
        generated, steps = [], []
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.synchronize()
        begin = time.monotonic()
        if begin >= deadline_at:
            return {
                "ids": [],
                "cache": None,
                "prefill": 0.0,
                "generation": 0.0,
                "worst_token": 0.0,
                "failure": "timeout",
                "peak_device_bytes": 0,
            }
        with torch.inference_mode():
            logits, audit = prefill_sc1(
                self.model,
                cache,
                ids,
                history_end=layout["H"],
                evict_range=None if arm == "full" else layout["evict_range"],
                pins=pins,
                interventions=interventions,
            )
            torch.cuda.synchronize()
            prefill_end = time.monotonic()
            failure = None
            for _ in range(256):
                if time.monotonic() >= deadline_at:
                    failure = "timeout"
                    break
                step = time.monotonic()
                token = int(logits[0, -1].argmax().item())
                generated.append(token)
                if token in self.eos:
                    steps.append(time.monotonic() - step)
                    break
                if len(generated) == 256:
                    steps.append(time.monotonic() - step)
                    break
                logits = interventions.forward(
                    self.model, torch.tensor([[token]], device=self.device), cache=cache
                )
                torch.cuda.synchronize()
                steps.append(time.monotonic() - step)
                expected_width = audit["layers"][0]["width"] + len(generated)
                if any(
                    k.shape[2] != expected_width or v.shape[2] != expected_width
                    for k, v in zip(cache.k, cache.v, strict=True)
                ):
                    raise AssertionError("generation cache pin persistence violated")
        end = time.monotonic()
        if end > deadline_at:
            failure = "timeout"
        interventions.assert_zero()
        audit["generation_absolute_length"] = cache.length
        audit["generation_layer_widths"] = [k.shape[2] for k in cache.k]
        return {
            "ids": generated,
            "cache": audit,
            "prefill": prefill_end - begin,
            "generation": end - prefill_end,
            "worst_token": max(steps, default=0.0),
            "failure": failure,
            "peak_device_bytes": torch.cuda.max_memory_allocated(),
        }


ARM_FIELDS = {
    "manifest_id",
    "episode_id",
    "episode_hash",
    "arm",
    "order",
    "attempt_id",
    "raw_output",
    "token_ids",
    "selection",
    "geometry",
    "cache",
    "latency",
    "allocated_seconds",
    "flags",
    "corruption",
    "success",
    "checker",
    "failure",
    "interventions",
    "peak_host_bytes",
    "peak_device_bytes",
    "input_tokens",
    "initialization_id",
    "override_errors",
    "exact_id_errors",
}


def run_arm(
    episode,
    arm,
    tokenizer,
    backend,
    scorer,
    *,
    manifest_id,
    order,
    attempt_id,
    initialization_id,
    prior_elapsed=0.0,
):
    import resource

    from stencil.sc1_episodes import run_checker

    start = time.monotonic()
    layout = render_episode(episode, tokenizer)
    rendered = time.monotonic()
    audit = InterventionCounter()
    selection = select_policy(layout, tokenizer, arm, scorer)
    prompt = render_episode(episode, tokenizer, selection["echo"]["insertion"])
    if (
        prompt["ids"][: layout["H"]] != layout["ids"][: layout["H"]]
        or prompt["H"] != layout["H"]
    ):
        raise AssertionError("echo changed original history IDs/positions")
    generated = backend.generate(
        prompt, selection["admission"]["pins"], arm, audit, start + DEADLINE
    )
    visible_ids = generated["ids"]
    if visible_ids and visible_ids[-1] in {151645, 151643}:
        visible_ids = visible_ids[:-1]
    text = tokenizer.decode(visible_ids, skip_special_tokens=False)
    check_start = time.monotonic()
    verdict = run_checker(episode, text)
    check_end = time.monotonic()
    flags = output_flags(text, generated["ids"], verdict["schema_valid"], tokenizer)
    failure = generated["failure"]
    if check_end - start > DEADLINE:
        failure = "timeout"
    audit.assert_zero()
    latency = {
        **selection["latency"],
        "render": rendered - start,
        "prefill": generated["prefill"],
        "generation": generated["generation"],
        "worst_token": generated["worst_token"],
        "check": check_end - check_start,
        "prior_attempts": prior_elapsed,
        "total": check_end - start + prior_elapsed,
    }
    failed = set(verdict["failed_obligations"])
    row = {
        "manifest_id": manifest_id,
        "episode_id": episode["id"],
        "episode_hash": digest(episode),
        "arm": arm,
        "order": order,
        "attempt_id": attempt_id,
        "raw_output": text,
        "token_ids": generated["ids"],
        "selection": selection,
        "geometry": {k: layout[k] for k in ("P", "H", "R", "C", "B", "evict_range")},
        "cache": generated["cache"],
        "latency": latency,
        "allocated_seconds": check_end - start,
        "flags": flags,
        "corruption": verdict["corruption"],
        "success": verdict["success"] and failure is None,
        "checker": verdict,
        "failure": failure,
        "interventions": audit.counts,
        "peak_host_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
        "peak_device_bytes": generated["peak_device_bytes"],
        "input_tokens": len(prompt["ids"]),
        "initialization_id": initialization_id,
        "override_errors": sorted(
            p["id"]
            for p in episode["obligations"]
            if p.get("error_class") == "override" and p["id"] in failed
        ),
        "exact_id_errors": sorted(
            p["id"]
            for p in episode["obligations"]
            if p.get("error_class") == "exact_id" and p["id"] in failed
        ),
    }
    if set(row) != ARM_FIELDS:
        raise AssertionError("per-arm writer missing registered fields")
    return row
