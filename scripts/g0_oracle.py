#!/usr/bin/env python3
"""G0 label-free counterfactual salience oracle and 30+30 pilot.

The tool corpus renderer follows the Qwen3/BFCL harness convention: tool
schemas are JSON objects inside ``<tools>`` in the system turn, and every gold
call is canonical JSON inside ``<tool_call>``.  Attention policy scores are
the mean natural attention mass received by a span over heads, current-user
query-token rows, and trunk layers 20--27.
"""

from __future__ import annotations

import argparse
import contextlib
import gzip
import hashlib
import json
import math
import os
import random
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from stencil.g0 import (  # noqa: E402
    ROLES,
    SEED,
    assert_g0_record,
    bm25_rank,
    build_candidate_spans,
    ensure_g0_path,
    match_null_spans,
    policy_recovery,
)

OUT = ROOT / "results/qwen/g0-pilot"
DATA = ROOT / "data/g0"
CHAT_REPO = "OpenAssistant/oasst2"
CHAT_REV = "179dd21fc55192153d94adb0e0ce8f69e222bf75"
CHAT_FILE = "2023-11-05_oasst2_ready.trees.jsonl.gz"
TOOL_REPO = "Salesforce/APIGen-MT-5k"
TOOL_REV = "abc4a517d67c541f85f6470cbd8fd3186b36830e"
TOOL_FILE = "apigen-mt_5k.json"
LICENSES = {"chat": "Apache-2.0", "tool": "CC-BY-NC-4.0"}
MAX_REFERENCE = 256
MAX_CONTEXT = 16_000
EOS = {151645, 151643}


def atomic_json(path: Path, value: Any) -> None:
    ensure_g0_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".tmp-{os.getpid()}")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)


def atomic_jsonl(path: Path, rows: list[dict]) -> None:
    ensure_g0_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".tmp-{os.getpid()}")
    with temporary.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    os.replace(temporary, path)


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_jsonl(path: Path) -> list[dict]:
    ensure_g0_path(path)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def _hf_download(repo: str, filename: str, revision: str) -> Path:
    from huggingface_hub import hf_hub_download

    return Path(
        hf_hub_download(
            repo_id=repo, filename=filename, repo_type="dataset", revision=revision
        )
    )


def _oasst_branches(path: Path) -> list[dict]:
    branches = []

    def visit(node: dict, path_nodes: list[dict]) -> None:
        branch = [*path_nodes, node]
        replies = node.get("replies") or []
        if not replies:
            assistants = sum(item.get("role") == "assistant" for item in branch)
            if (
                assistants >= 3
                and branch[-1].get("role") == "assistant"
                and all(item.get("lang") == "en" for item in branch)
            ):
                messages = [
                    {
                        "role": "user" if item["role"] == "prompter" else "assistant",
                        "content": item["text"],
                    }
                    for item in branch[:-1]
                ]
                branches.append(
                    {
                        "corpus": "chat",
                        "id": f"{branch[0]['message_id']}:{branch[-1]['message_id']}",
                        "turn": len(messages),
                        "messages": messages,
                        "reference": None,
                        "reference_token_ids": None,
                    }
                )
        for reply in replies:
            visit(reply, branch)

    with gzip.open(path, "rt") as handle:
        for line in handle:
            visit(json.loads(line)["prompt"], [])
    return branches


def render_call(value: str | dict) -> str:
    call = json.loads(value) if isinstance(value, str) else value
    rendered = {"name": call["name"], "arguments": call.get("arguments", {})}
    return "<tool_call>\n" + json.dumps(rendered, sort_keys=True) + "\n</tool_call>"


def _tool_dialogues(path: Path) -> list[dict]:
    rows = json.loads(path.read_text())
    dialogues = []
    for row_index, row in enumerate(rows):
        conversations = row["conversations"]
        targets = []
        for index, message in enumerate(conversations):
            if message["from"] != "function_call":
                continue
            prior_assistant = sum(
                item["from"] in {"gpt", "function_call"}
                for item in conversations[:index]
            )
            real_outputs = sum(
                item["from"] == "observation"
                and bool(str(item.get("value", "")).strip())
                for item in conversations[:index]
            )
            if prior_assistant >= 3 and real_outputs:
                targets.append(index)
        if not targets:
            continue
        target = targets[-1]
        messages = []
        role_map = {
            "human": "user",
            "gpt": "assistant",
            "function_call": "assistant",
            "observation": "tool",
        }
        for item in conversations[:target]:
            content = (
                render_call(item["value"])
                if item["from"] == "function_call"
                else str(item.get("value", ""))
            )
            messages.append({"role": role_map[item["from"]], "content": content})
        reference = render_call(conversations[target]["value"])
        dialogues.append(
            {
                "corpus": "tool",
                "id": f"apigen-{row_index}:{target}",
                "turn": len(messages),
                "messages": messages,
                "tools": json.loads(row["tools"]),
                "reference": reference,
                "reference_token_ids": None,
            }
        )
    return dialogues


def prepare_subsets() -> dict:
    chat_source = _hf_download(CHAT_REPO, CHAT_FILE, CHAT_REV)
    tool_source = _hf_download(TOOL_REPO, TOOL_FILE, TOOL_REV)
    rng = random.Random(SEED)
    chat = _oasst_branches(chat_source)
    tool = _tool_dialogues(tool_source)
    rng.shuffle(chat)
    rng.shuffle(tool)
    chat, tool = chat[:30], tool[:30]
    atomic_jsonl(DATA / "chat.jsonl", chat)
    atomic_jsonl(DATA / "tool.jsonl", tool)
    manifest = {
        "seed": SEED,
        "draw_procedure": (
            "enumerate eligible records in upstream order; Python "
            "random.Random(20260903) "
            "shuffle; take first 30"
        ),
        "subsets": {
            "chat": {
                "dataset": CHAT_REPO,
                "revision": CHAT_REV,
                "upstream_file": CHAT_FILE,
                "license": LICENSES["chat"],
                "n": len(chat),
                "sha256": file_sha(DATA / "chat.jsonl"),
                "ids": [row["id"] for row in chat],
            },
            "tool": {
                "dataset": TOOL_REPO,
                "revision": TOOL_REV,
                "upstream_file": TOOL_FILE,
                "license": LICENSES["tool"],
                "n": len(tool),
                "sha256": file_sha(DATA / "tool.jsonl"),
                "ids": [row["id"] for row in tool],
            },
        },
    }
    atomic_json(DATA / "MANIFEST.json", manifest)
    return manifest


def _tool_system(tools: list[dict]) -> str:
    body = "\n".join(json.dumps(tool, sort_keys=True) for tool in tools)
    return (
        "# Tools\n\nYou may call one or more functions to assist with the user "
        "query.\n\n"
        "You are provided with function signatures within <tools></tools> XML tags:\n"
        f"<tools>\n{body}\n</tools>\n\nFor each function call, return a json object "
        "with function name and arguments within <tool_call></tool_call> XML tags:\n"
        '<tool_call>\n{"name": <function-name>, "arguments": <args-json-object>}\n'
        "</tool_call>"
    )


def render_context(row: dict, tokenizer) -> tuple[str, list[dict], list[int]]:
    messages = [dict(item) for item in row["messages"]]
    if row["corpus"] == "tool":
        messages.insert(0, {"role": "system", "content": _tool_system(row["tools"])})

    def render(items: list[dict]) -> tuple[str, list[tuple[int, int]]]:
        parts = []
        locations = []
        cursor = 0
        for item in items:
            prefix = f"<|im_start|>{item['role']}\n"
            suffix = "<|im_end|>\n"
            parts.extend((prefix, item["content"], suffix))
            start = cursor + len(prefix)
            end = start + len(item["content"])
            locations.append((start, end))
            cursor += len(prefix) + len(item["content"]) + len(suffix)
        tail = "<|im_start|>assistant\n<think>\n\n</think>\n\n"
        return "".join(parts) + tail, locations

    while True:
        prompt, locations = render(messages)
        encoding = tokenizer.encode(prompt)
        if len(encoding.ids) <= MAX_CONTEXT:
            break
        removable = next(
            (i for i, item in enumerate(messages[:-1]) if item["role"] != "system"),
            None,
        )
        if removable is None:
            raise ValueError(
                f"{row['id']} cannot fit protected schema under {MAX_CONTEXT}"
            )
        del messages[removable]
    annotated = []
    for turn, (item, (char_start, char_end)) in enumerate(
        zip(messages, locations, strict=True)
    ):
        columns = [
            i
            for i, (left, right) in enumerate(encoding.offsets)
            if left < char_end and right > char_start
        ]
        if not columns:
            continue
        annotated.append(
            {
                **item,
                "token_start": columns[0],
                "token_end": columns[-1] + 1,
                "turn": turn,
            }
        )
    current_user = next(
        (item for item in reversed(annotated) if item["role"] == "user"), annotated[-1]
    )
    query_columns = list(range(current_user["token_start"], current_user["token_end"]))
    return prompt, annotated, query_columns


def load_model():
    import torch
    from tokenizers import Tokenizer

    from stencil import determinism  # noqa: F401
    from stencil.qwen3 import Qwen3

    tokenizer = Tokenizer.from_file(str(ROOT / "models/qwen3-1.7b-hf/tokenizer.json"))
    model = Qwen3()
    model.load_state_dict(
        torch.load(
            ROOT / "models/qwen3-1.7b.pt", map_location="cpu", weights_only=True
        ),
        strict=True,
    )
    return model.to(torch.bfloat16).cuda().eval(), tokenizer


def clone_cache(source):
    from stencil.qwen3 import KVCache

    result = KVCache(source.cfg)
    result.length = source.length
    result.k = [tensor.clone() for tensor in source.k]
    result.v = [tensor.clone() for tensor in source.v]
    return result


@contextlib.contextmanager
def attention_capture(
    spans: list[dict], query_columns: list[int], sink: dict[int, list[float]]
):
    """Capture explicit-trunk softmaxes without changing trunk source or outputs."""
    import torch.nn.functional as functional

    original = functional.softmax
    layer = -1

    def wrapped(input_tensor, dim=None, *args, **kwargs):
        nonlocal layer
        result = original(input_tensor, dim, *args, **kwargs)
        if dim == -1 and input_tensor.ndim == 4 and input_tensor.shape[-2] > 1:
            layer += 1
            if 20 <= layer <= 27:
                queries = [q for q in query_columns if q < result.shape[-2]]
                values = []
                for span in spans:
                    lo, hi = span["start"], min(span["end"], result.shape[-1])
                    mass = (
                        result[0, :, queries, lo:hi].sum(-1).mean()
                        if queries and hi > lo
                        else 0.0
                    )
                    values.append(float(mass))
                sink[layer] = values
        return result

    functional.softmax = wrapped
    try:
        yield
    finally:
        functional.softmax = original


def _teacher_force(model, base_cache, first_logits, reference_ids: list[int], drop=()):
    import torch
    import torch.nn.functional as functional

    cache = clone_cache(base_cache)
    for lo, hi in sorted(drop, reverse=True):
        cache.evict(lo, hi)
    losses, top = [], []
    logits = first_logits
    with torch.no_grad():
        for index, target in enumerate(reference_ids):
            row = logits[0, -1].float()
            losses.append(
                float(
                    functional.cross_entropy(
                        row[None], torch.tensor([target], device=row.device)
                    )
                )
            )
            top.append(int(row.argmax()))
            if index + 1 < len(reference_ids):
                logits = model(torch.tensor([[target]], device="cuda"), cache=cache)
    return sum(losses) / len(losses), top


def _generate_reference(
    model, tokenizer, context_ids: list[int]
) -> tuple[str, list[int]]:
    import torch

    from stencil.qwen3 import KVCache

    cache = KVCache()
    output = []
    with torch.no_grad():
        logits = model(torch.tensor([context_ids], device="cuda"), cache=cache)
        token = int(logits[0, -1].argmax())
        while token not in EOS and len(output) < MAX_REFERENCE:
            output.append(token)
            logits = model(torch.tensor([[token]], device="cuda"), cache=cache)
            token = int(logits[0, -1].argmax())
    return tokenizer.decode(output), output


def _fit_budget(order: list[int], spans: list[dict], budget: int) -> list[int]:
    kept, used = [], 0
    for index in order:
        cost = spans[index]["n_tok"]
        if used + cost <= budget:
            kept.append(index)
            used += cost
    return kept


def _salience_scores(spans: list[dict], texts: list[str]) -> list[float]:
    from stencil.salience2 import extract_instructions

    scores = []
    for span, text in zip(spans, texts, strict=True):
        if span["role"] not in {"user", "system"}:
            scores.append(float("-inf"))
            continue
        found = extract_instructions(text, backend="linguistic")
        scores.append(max((item.score for item in found), default=float("-inf")))
    return scores


def score_policies(
    spans: list[dict],
    nulls: list[dict],
    context_ids: list[int],
    tokenizer,
    query: str,
    attention: list[float],
) -> tuple[dict, int]:
    count = max(1, math.ceil(len(spans) * 0.25))
    best = sorted(range(len(spans)), key=lambda i: (-spans[i]["utility"], i))[:count]
    budget = sum(spans[i]["n_tok"] for i in best)
    texts = [
        tokenizer.decode(context_ids[span["start"] : span["end"]]) for span in spans
    ]
    salience_scores = _salience_scores(spans, texts)
    orders = {
        "role_rule": sorted(
            range(len(spans)),
            key=lambda i: (
                0
                if spans[i]["role"] == "system"
                else 1
                if spans[i]["role"] == "user"
                else 2,
                -spans[i]["turn"],
                i,
            ),
        ),
        "recent_sinks": sorted(
            range(len(spans)),
            key=lambda i: (0 if spans[i]["start"] < 4 else 1, -spans[i]["end"], i),
        ),
        "archive_bm25": bm25_rank(texts, query),
        "salience2": sorted(range(len(spans)), key=lambda i: (-salience_scores[i], i)),
        "attention_mass": sorted(range(len(spans)), key=lambda i: (-attention[i], i)),
    }
    utilities = [span["utility"] for span in spans]
    null_utilities = [span["utility"] for span in nulls]
    policies = {}
    for name, order in orders.items():
        kept = _fit_budget(order, spans, budget)
        policies[name] = {
            "kept_span_idx": kept,
            **policy_recovery(utilities, kept, null_utilities),
        }
    return policies, budget


def _call_validity(
    tokenizer, token_ids: list[int], reference: str
) -> tuple[bool, bool]:
    decoded = tokenizer.decode(token_ids)
    matches = re.findall(r"<tool_call>\s*(.*?)\s*</tool_call>", decoded, re.DOTALL)
    try:
        parsed = [json.loads(item) for item in matches]
        expected = [
            json.loads(item)
            for item in re.findall(
                r"<tool_call>\s*(.*?)\s*</tool_call>", reference, re.DOTALL
            )
        ]
    except json.JSONDecodeError:
        return False, False
    return bool(parsed), parsed == expected


def run_dialogue(model, tokenizer, row: dict) -> dict:
    import torch

    from stencil.qwen3 import KVCache

    started = time.monotonic()
    prompt, messages, query_columns = render_context(row, tokenizer)
    context_ids = tokenizer.encode(prompt).ids
    spans = build_candidate_spans(messages, tokenizer, seed=SEED, max_spans=12)
    nulls = match_null_spans(spans, messages, tokenizer, seed=SEED)
    capture: dict[int, list[float]] = {}
    cache = KVCache()
    with torch.no_grad(), attention_capture(spans, query_columns, capture):
        prompt_logits = model(torch.tensor([context_ids], device="cuda"), cache=cache)
    if row["reference_token_ids"] is None:
        reference_ids = tokenizer.encode(row["reference"]).ids
    else:
        reference_ids = list(row["reference_token_ids"])
    if not reference_ids:
        raise ValueError(f"empty reference for {row['id']}")
    nll_full, full_top = _teacher_force(model, cache, prompt_logits, reference_ids)
    attention = [
        sum(capture[layer][i] for layer in sorted(capture)) / len(capture)
        if capture
        else 0.0
        for i in range(len(spans))
    ]

    def measure(span: dict) -> dict:
        nll, top = _teacher_force(
            model, cache, prompt_logits, reference_ids, [(span["start"], span["end"])]
        )
        result = {
            **span,
            "utility": nll - nll_full,
            "top1_agree": sum(a == b for a, b in zip(top, full_top, strict=True))
            / len(top),
        }
        if row["corpus"] == "tool":
            result["argmax_parse"], result["argmax_match"] = _call_validity(
                tokenizer, top, row["reference"]
            )
        return result

    measured_spans = [measure(span) for span in spans]
    measured_nulls = [measure(span) for span in nulls]
    top3 = sorted(
        range(len(measured_spans)), key=lambda i: (-measured_spans[i]["utility"], i)
    )[:3]
    joint_nll, _ = _teacher_force(
        model,
        cache,
        prompt_logits,
        reference_ids,
        [(measured_spans[i]["start"], measured_spans[i]["end"]) for i in top3],
    )
    query_text = next(
        item["content"] for item in reversed(messages) if item["role"] == "user"
    )
    policies, budget = score_policies(
        measured_spans, measured_nulls, context_ids, tokenizer, query_text, attention
    )
    strip_fields = {"message_idx", "turn", "age", "length_bucket", "age_bucket"}
    for group in (measured_spans, measured_nulls):
        for span in group:
            for field in strip_fields:
                span.pop(field, None)
    record = {
        "corpus": row["corpus"],
        "id": row["id"],
        "turn": row["turn"],
        "n_context_tokens": len(context_ids),
        "spans": measured_spans,
        "nulls": measured_nulls,
        "joint": {
            "span_idx": top3,
            "utility": joint_nll - nll_full,
            "sum_utility": sum(measured_spans[i]["utility"] for i in top3),
        },
        "policies": policies,
        "seconds": time.monotonic() - started,
        "nll_full": nll_full,
        "budget_tokens": budget,
        "reference_tokens": len(reference_ids),
    }
    assert_g0_record(record)
    return record


def _percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    lo, hi = math.floor(position), math.ceil(position)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (position - lo)


def summarize(records: list[dict]) -> dict:
    summary: dict[str, Any] = {"utility": {}, "policy_recovery": {}, "seconds": {}}
    for corpus in ("chat", "tool"):
        corpus_records = [record for record in records if record["corpus"] == corpus]
        summary["utility"][corpus] = {}
        for role in (*ROLES, "all"):
            pairs = [
                (span, null)
                for record in corpus_records
                for span, null in zip(record["spans"], record["nulls"], strict=True)
                if role == "all" or span["role"] == role
            ]
            values = [span["utility"] for span, _ in pairs]
            null_values = [null["utility"] for _, null in pairs]
            null_p90 = _percentile(null_values, 0.9)
            summary["utility"][corpus][role] = {
                "n": len(values),
                "mean": sum(values) / len(values) if values else 0.0,
                "median": _percentile(values, 0.5),
                "p90": _percentile(values, 0.9),
                "null_mean": sum(null_values) / len(null_values)
                if null_values
                else 0.0,
                "null_median": _percentile(null_values, 0.5),
                "null_p90": null_p90,
                "fraction_gt_null_p90": sum(value > null_p90 for value in values)
                / len(values)
                if values
                else 0.0,
            }
        summary["policy_recovery"][corpus] = {}
        for name in (
            "role_rule",
            "recent_sinks",
            "archive_bm25",
            "salience2",
            "attention_mass",
        ):
            rows = [record["policies"][name] for record in corpus_records]
            summary["policy_recovery"][corpus][name] = {
                "recovery": sum(row["recovery"] for row in rows) / len(rows)
                if rows
                else 0.0,
                "recovery_null_adj": sum(row["recovery_null_adj"] for row in rows)
                / len(rows)
                if rows
                else 0.0,
                "by_role": {},
            }
            for role in ROLES:
                raw, adjusted = [], []
                for record in corpus_records:
                    indices = [
                        i
                        for i, span in enumerate(record["spans"])
                        if span["role"] == role
                    ]
                    utilities = [record["spans"][i]["utility"] for i in indices]
                    nulls = [record["nulls"][i]["utility"] for i in indices]
                    kept_global = set(record["policies"][name]["kept_span_idx"])
                    kept_local = [j for j, i in enumerate(indices) if i in kept_global]
                    value = policy_recovery(utilities, kept_local, nulls)
                    raw.append(value["recovery"])
                    adjusted.append(value["recovery_null_adj"])
                summary["policy_recovery"][corpus][name]["by_role"][role] = {
                    "recovery": sum(raw) / len(raw) if raw else 0.0,
                    "recovery_null_adj": sum(adjusted) / len(adjusted)
                    if adjusted
                    else 0.0,
                }
        seconds = [record["seconds"] for record in corpus_records]
        summary["seconds"][corpus] = {
            "mean": sum(seconds) / len(seconds) if seconds else 0.0,
            "max": max(seconds, default=0.0),
        }
    return summary


def gpu_is_idle() -> bool:
    result = subprocess.run(
        ["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"],
        check=True,
        capture_output=True,
        text=True,
    )
    return not result.stdout.strip()


def _refresh_manifest() -> dict:
    manifest = json.loads((DATA / "MANIFEST.json").read_text())
    for corpus in ("chat", "tool"):
        path = DATA / f"{corpus}.jsonl"
        rows = load_jsonl(path)
        manifest["subsets"][corpus]["sha256"] = file_sha(path)
        manifest["subsets"][corpus]["ids"] = [row["id"] for row in rows]
    atomic_json(DATA / "MANIFEST.json", manifest)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--corpus", choices=("chat", "tool", "both"), default="both")
    args = parser.parse_args(argv)
    if not 1 <= args.limit <= 30:
        parser.error("--limit must be in [1, 30]")
    if not (DATA / "MANIFEST.json").exists():
        prepare_subsets()
    if args.prepare_only:
        return 0
    if not gpu_is_idle():
        print("GPU is busy; no work started", file=sys.stderr)
        return 2
    model, tokenizer = load_model()
    corpora = ("chat", "tool") if args.corpus == "both" else (args.corpus,)
    records_dir = OUT / "records"
    all_records = []
    for corpus in corpora:
        subset_path = DATA / f"{corpus}.jsonl"
        rows = load_jsonl(subset_path)
        for row_index, row in enumerate(rows[: args.limit]):
            prompt, _, _ = render_context(row, tokenizer)
            if corpus == "chat" and row["reference_token_ids"] is None:
                text, token_ids = _generate_reference(
                    model, tokenizer, tokenizer.encode(prompt).ids
                )
                row["reference"] = text
                row["reference_token_ids"] = token_ids
                rows[row_index] = row
                atomic_jsonl(subset_path, rows)
            elif row["reference_token_ids"] is None:
                row["reference_token_ids"] = tokenizer.encode(row["reference"]).ids
                rows[row_index] = row
                atomic_jsonl(subset_path, rows)
            record_path = records_dir / f"{corpus}-{row_index:02d}.json"
            if record_path.exists():
                record = json.loads(record_path.read_text())
                assert_g0_record(record)
            else:
                record = run_dialogue(model, tokenizer, row)
                atomic_json(record_path, record)
            all_records.append(record)
            print(
                f"{corpus} {row_index + 1}/{args.limit}: {record['seconds']:.1f}s",
                flush=True,
            )
    manifest = _refresh_manifest()
    existing = sorted(records_dir.glob("*.json")) if records_dir.exists() else []
    complete_records = [json.loads(path.read_text()) for path in existing]
    atomic_json(OUT / "summary.json", summarize(complete_records))
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    meta = {
        "commit": commit,
        "model_sha": file_sha(ROOT / "models/qwen3-1.7b.pt"),
        "corpus_shas": {
            corpus: manifest["subsets"][corpus]["sha256"] for corpus in ("chat", "tool")
        },
        "seed": SEED,
        "ids": {
            corpus: manifest["subsets"][corpus]["ids"] for corpus in ("chat", "tool")
        },
        "renderer": (
            "Qwen3 non-thinking template; schemas in system <tools>; canonical "
            "sorted-key "
            "JSON calls in <tool_call>"
        ),
        "attention_policy": (
            "mean natural mass over heads, query-token rows, layers 20-27"
        ),
        "salience2_lineage": (
            "shipped linguistic weights; refit 2026-09-02 on b3 synthetic only; "
            "commit e19f67f"
        ),
    }
    atomic_json(OUT / "meta.json", meta)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
