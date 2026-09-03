#!/usr/bin/env python3
"""GPU-deferred extraction and dev-grid selection for function vectors."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from stencil.function_vectors import (  # noqa: E402
    build_minimal_pairs,
    combine_vectors,
    cosine_similarity_report,
    generate_injected,
    mean_difference,
)

LAYERS = (8, 12, 16, 20, 24)
GRID_LAYERS = (12, 16, 20)
GRID_ALPHAS = (0.5, 1.0, 2.0)
N_PER_TYPE = 32
PROMPT_TEMPLATE = (
    "<|im_start|>user\n{prompt}<|im_end|>\n"
    "<|im_start|>assistant\n<think>\n\n</think>\n\n"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, value) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def load_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def probe_constraint_types() -> tuple[str, ...]:
    corpus_path = ROOT / "data/b3/mt-train-300.jsonl"
    corpus = {row["key"]: row for row in load_rows(corpus_path)}
    types = set()
    records = sorted((ROOT / "results/qwen/ledger-kv-probe-h1p").glob("session-*.json"))
    if len(records) != 20:
        raise RuntimeError(f"expected 20 probe records, found {len(records)}")
    for path in records:
        record = json.loads(path.read_text())
        turn = corpus[record["key"]]["turns"][record["n_turns"] - 1]
        types.update(turn["combo"][: record["n_aged"]])
    return tuple(sorted(types))


def load_model():
    import g0_oracle

    return g0_oracle.load_model()


def encode_prompt(tokenizer, prompt: str) -> torch.Tensor:
    ids = tokenizer.encode(PROMPT_TEMPLATE.format(prompt=prompt)).ids
    return torch.tensor([ids], dtype=torch.long)


def extract(args) -> None:
    from stencil import determinism  # noqa: F401

    determinism.assert_gpu_free_or_owned()
    source_path = ROOT / "data/b3/train-v43.jsonl"
    constraint_types = probe_constraint_types()
    pairs = build_minimal_pairs(
        load_rows(source_path), constraint_types, n_per_type=args.n_per_type
    )
    model, tokenizer = load_model()
    layers = tuple(args.layers)
    states = {
        (constraint_type, layer): {"with": [], "without": []}
        for constraint_type in constraint_types
        for layer in layers
    }
    for constraint_type in constraint_types:
        for pair in pairs[constraint_type]:
            for variant in ("with", "without"):
                tokens = encode_prompt(tokenizer, pair[f"{variant}_prompt"]).to(
                    next(model.parameters()).device
                )
                with torch.no_grad():
                    _logits, captured = model(tokens, capture_hidden=layers)
                for layer in layers:
                    states[(constraint_type, layer)][variant].append(
                        captured[layer][0, -1].float().cpu()
                    )
    vectors = {
        key: mean_difference(value["with"], value["without"])
        for key, value in states.items()
    }
    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    payload = {
        "vectors": {
            f"{constraint_type}:{layer}": vector
            for (constraint_type, layer), vector in vectors.items()
        },
        "layers": layers,
        "constraint_types": constraint_types,
        "n_per_type": args.n_per_type,
    }
    torch.save(payload, outdir / "vectors.pt")
    atomic_json(outdir / "pairs.json", pairs)
    report = {
        "status": "extracted",
        "source": str(source_path),
        "source_sha256": sha256(source_path),
        "probe_source": "results/qwen/ledger-kv-probe-h1p/session-*.json",
        "constraint_types": list(constraint_types),
        "pair_counts": {key: len(value) for key, value in pairs.items()},
        "layers": list(layers),
        "norms": {
            f"{constraint_type}:{layer}": float(vector.float().norm())
            for (constraint_type, layer), vector in vectors.items()
        },
        "cosine_similarity_between_types": cosine_similarity_report(vectors, layers),
    }
    atomic_json(outdir / "report.json", report)


def load_vectors(path: Path):
    payload = torch.load(path, map_location="cpu", weights_only=True)
    vectors = {}
    for key, vector in payload["vectors"].items():
        constraint_type, layer = key.rsplit(":", 1)
        vectors[(constraint_type, int(layer))] = vector
    return vectors, payload


def grid(args) -> None:
    from stencil import determinism  # noqa: F401

    determinism.assert_gpu_free_or_owned()
    vectors, payload = load_vectors(Path(args.vectors))
    rows = load_rows(ROOT / "data/b3/train-v43.jsonl")[:4]
    model, tokenizer = load_model()
    results = {}
    for layer in GRID_LAYERS:
        for alpha in GRID_ALPHAS:
            outputs = []
            for row in rows:
                vector, unknown = combine_vectors(vectors, row["combo"], layer)
                token_ids = tokenizer.encode(
                    PROMPT_TEMPLATE.format(prompt=row["prompt"])
                ).ids
                generated = generate_injected(
                    model,
                    tokenizer,
                    token_ids,
                    evict_range=None,
                    vector=vector,
                    alpha=alpha,
                    layer=layer,
                    clear_after=None,
                    max_new=args.max_new,
                    deadline_s=args.deadline,
                )
                degenerate = not generated["truncated"] and generated["rep4"] > 0.5
                outputs.append(
                    {
                        "key": row["key"],
                        "unknown_types": unknown,
                        "degenerate": bool(degenerate),
                        "truncated": generated["truncated"],
                        "timed_out": generated["timed_out"],
                        "rep4": generated["rep4"],
                    }
                )
            results[f"a{alpha}-l{layer}"] = {
                "alpha": alpha,
                "layer": layer,
                "degenerate": sum(item["degenerate"] for item in outputs),
                "outputs": outputs,
            }
    eligible = [value for value in results.values() if value["degenerate"] == 0]
    if not eligible:
        raise RuntimeError("no non-degenerate function-vector grid cell")
    selected = max(eligible, key=lambda item: (item["alpha"], -item["layer"]))
    output = {
        "status": "selected_before_probe",
        "selection_rule": (
            "largest alpha with 0/4 degenerate outputs; ties choose smallest layer"
        ),
        "alphas": list(GRID_ALPHAS),
        "layers": list(GRID_LAYERS),
        "dev_keys": [row["key"] for row in rows],
        "vectors": str(Path(args.vectors).resolve()),
        "vector_constraint_types": list(payload["constraint_types"]),
        "selected": {"alpha": selected["alpha"], "layer": selected["layer"]},
        "results": results,
    }
    atomic_json(Path(args.out), output)


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    extract_parser = subparsers.add_parser("extract")
    extract_parser.add_argument(
        "--out", default=str(ROOT / "results/qwen/fv-vectors")
    )
    extract_parser.add_argument("--n-per-type", type=int, default=N_PER_TYPE)
    extract_parser.add_argument("--layers", type=int, nargs="+", default=LAYERS)
    extract_parser.set_defaults(run=extract)
    grid_parser = subparsers.add_parser("grid")
    grid_parser.add_argument(
        "--vectors", default=str(ROOT / "results/qwen/fv-vectors/vectors.pt")
    )
    grid_parser.add_argument(
        "--out", default=str(ROOT / "results/qwen/fv-vectors/grid.json")
    )
    grid_parser.add_argument("--max-new", type=int, default=512)
    grid_parser.add_argument("--deadline", type=float, default=300.0)
    grid_parser.set_defaults(run=grid)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    args.run(args)


if __name__ == "__main__":
    main()
