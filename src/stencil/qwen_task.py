# ruff: noqa: E501
"""Open-content focus task for the Qwen rung (QWEN-PLAN P0/P1).

Minimal by design: obligations are key -> open multi-token value pairs
("deploy target" -> "staging-cluster-7 in eu-west-2"), stated in plain text,
queried later with exact-match scoring on the value string. Values are
composed from pools deterministically, so held-out values never appear in
training and are genuinely multi-token. Deletion (not windowing) provides
provable unreachability at this rung: a query chunk that no longer contains
the obligation text has zero causal path to it except the wire.
"""
from __future__ import annotations

from dataclasses import dataclass

import torch

FIELDS = [
    "deploy target", "log directory", "review branch", "alert channel",
    "test command", "backup host", "config file", "release tag",
]
ADJ = ["primary", "staging", "legacy", "fallback", "canary", "shadow", "pinned", "sandbox"]
NOUN = ["cluster", "bucket", "node", "gateway", "registry", "queue", "volume", "shard"]
SUFFIX = ["eu-west-2", "us-east-1", "zone-c", "rack-14", "tier-3", "ring-0", "cell-9", "pod-x7"]
FILLER = [
    "The team discussed unrelated scheduling questions for a while.",
    "Several log lines scrolled past without anything notable.",
    "A colleague shared a link about an upcoming conference.",
    "Routine maintenance chatter continued in the background.",
    "Someone asked about lunch plans and the thread drifted.",
    "An old ticket was closed as duplicate after a short debate.",
]


@dataclass
class QwenSession:
    text: str                       # full stream (obligations + filler + query)
    query_text: str                 # the query-only tail (post-deletion form)
    field: str
    value: str                      # exact expected answer string
    obligations: list[tuple[str, str]]


def _value(g: torch.Generator) -> str:
    def pick(pool: list[str]) -> str:
        return pool[int(torch.randint(0, len(pool), (1,), generator=g))]
    return f"{pick(ADJ)}-{pick(NOUN)}-{int(torch.randint(10, 99, (1,), generator=g))}.{pick(SUFFIX)}"


def generate(seed: int, n_obligations: int = 4, n_filler: int = 6) -> QwenSession:
    g = torch.Generator().manual_seed(seed)
    fields = [FIELDS[int(i)] for i in torch.randperm(len(FIELDS), generator=g)[:n_obligations]]
    obligations = [(f, _value(g)) for f in fields]
    lines = ["Note: the demo field is sample-item-00.zone-a."]
    lines += [f"Note: the {f} is {v}." for f, v in obligations]
    for _ in range(n_filler):
        lines.append(FILLER[int(torch.randint(0, len(FILLER), (1,), generator=g))])
    qi = int(torch.randint(0, n_obligations, (1,), generator=g))
    field, value = obligations[qi]
    query = (
        "Q: What is the demo field? Answer with the exact value only.\n"
        "A: The demo field is sample-item-00.zone-a.\n"
        f"Q: What is the {field}? Answer with the exact value only.\n"
        f"A: The {field} is"
    )
    return QwenSession(
        text=" ".join(lines) + "\n" + query,
        query_text=query,
        field=field,
        value=value,
        obligations=obligations,
    )


@dataclass
class DriftSession:
    """Multi-chunk session: obligations set in chunk 0, updated/cleared in
    chunk 1, queried in chunk 2 after both evidence chunks are deleted.
    Each chunk is a list of (line_text, slot_id_or_None, kind) with kind in
    {"set", "update", "clear", "filler"}."""

    chunks: list[list[tuple[str, int | None, str]]]
    queries: list[tuple[str, str, str | None]]  # (field, current_value, stale_value_or_None)
    query_parts: list[str]


def generate_drift(seed: int, n_obligations: int = 4) -> DriftSession:
    g = torch.Generator().manual_seed(seed)

    def pick(pool: list[str]) -> str:
        return pool[int(torch.randint(0, len(pool), (1,), generator=g))]

    fields = [FIELDS[int(i)] for i in torch.randperm(len(FIELDS), generator=g)[:n_obligations]]
    current = {f: _value(g) for f in fields}
    stale: dict[str, str] = {}
    c0: list[tuple[str, int | None, str]] = []
    for f in fields:
        c0.append((f"Note: the {f} is {current[f]}.", FIELDS.index(f), "set"))
    for _ in range(3):
        c0.append((pick(FILLER), None, "filler"))
    # chunk 1: 2 updates + 1 clear + filler
    upd = [fields[int(i)] for i in torch.randperm(n_obligations, generator=g)[:2]]
    clear_f = next(f for f in fields if f not in upd)
    c1: list[tuple[str, int | None, str]] = [(pick(FILLER), None, "filler")]
    for f in upd:
        stale[f] = current[f]
        current[f] = _value(g)
        c1.append((f"Update: the {f} is now {current[f]}.", FIELDS.index(f), "update"))
        c1.append((pick(FILLER), None, "filler"))
    c1.append((f"The {clear_f} note is obsolete; disregard it.", FIELDS.index(clear_f), "clear"))
    # queries: one updated field (stale trap) + one untouched field
    untouched = [f for f in fields if f not in upd and f != clear_f]
    q_fields = [upd[0], untouched[0] if untouched else upd[1]]
    parts = [
        "Q: What is the demo field? Answer with the exact value only.\n"
        "A: The demo field is sample-item-00.zone-a.\n"
    ]
    queries = []
    for f in q_fields:
        parts.append(f"Q: What is the {f}? Answer with the exact value only.\nA: The {f} is")
        queries.append((f, current[f], stale.get(f)))
    return DriftSession(chunks=[c0, c1], queries=queries, query_parts=parts)
