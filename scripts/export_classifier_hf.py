"""Export the registered sentence classifier (data/classifier/model/ft) to a Hub repo.

Release 0 of plan/BACK-ON-TRACK-PLAN.md. Converts encoder + head.pt into one
``trust_remote_code`` checkpoint (``modeling_stencil.py`` is a copy of
src/stencil/hf_sentence_classifier.py), then verifies on every held-out sentence that
the exported model reproduces the registered scorer's argmax, logging the max-abs
logit drift. ``--push`` is only honoured after a passing verification.

usage: uv run python scripts/export_classifier_hf.py --out results/release0/hf-export
       [--push --repo bmarti44/assistant-memory-sentence-classifier]
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

MODEL_DIR = ROOT / "data" / "classifier" / "model" / "ft"
HELDOUT_DIR = ROOT / "data" / "classifier" / "heldout"
HELDOUT_FILES = [
    "fable-scope-validation.jsonl",
    "fable-validation.jsonl",
    "opus-heldout.jsonl",
    "sol-heldout.jsonl",
]
CARD = ROOT / "data" / "classifier" / "MODEL_CARD.md"
MODELING = ROOT / "src" / "stencil" / "hf_sentence_classifier.py"
MAX_LENGTH = 192  # registered scoring length (src/stencil/selector_v2.py)


def load_heldout() -> list[dict]:
    rows = []
    for name in HELDOUT_FILES:
        with open(HELDOUT_DIR / name, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    rows.append(json.loads(line))
    return rows


def reference_logits(tokenizer, encoder, saved, rows, torch):
    """Registered scoring path (selector_v2.ClassifierScorer), full logits."""
    roles = list(saved["roles"])
    head = torch.nn.Sequential(
        torch.nn.Dropout(0.1),
        torch.nn.Linear(int(saved["hidden"]) + len(roles), len(saved["labels"])),
    )
    head.load_state_dict(saved["head"])
    head.eval()
    out = []
    with torch.no_grad():
        for start in range(0, len(rows), 64):
            chunk = rows[start : start + 64]
            batch = tokenizer(
                [r.get("context") or "(no context)" for r in chunk],
                [f"[{r['role']}] {r['text']}" for r in chunk],
                padding=True,
                truncation="longest_first",
                max_length=MAX_LENGTH,
                return_tensors="pt",
            )
            hidden = encoder(**batch).last_hidden_state[:, 0]
            role_vec = torch.tensor(
                [[float(r["role"] == c) for c in roles] for r in chunk]
            )
            out.append(head(torch.cat([hidden, role_vec], dim=1)))
    return torch.cat(out)


def export(out: Path, torch, transformers) -> dict:
    from stencil.hf_sentence_classifier import (
        StencilSentenceClassifier,
        StencilSentenceClassifierConfig,
    )

    tokenizer = transformers.AutoTokenizer.from_pretrained(MODEL_DIR / "encoder")
    encoder = transformers.AutoModel.from_pretrained(MODEL_DIR / "encoder").eval()
    saved = torch.load(MODEL_DIR / "head.pt", map_location="cpu", weights_only=True)
    roles, labels = list(saved["roles"]), list(saved["labels"])
    hidden = int(saved["hidden"])
    weight = saved["head"]["1.weight"]  # [n_labels, hidden + n_roles]
    bias = saved["head"]["1.bias"]

    config = StencilSentenceClassifierConfig(
        roles=roles,
        default_role="user",
        num_labels=len(labels),
        id2label={i: lab for i, lab in enumerate(labels)},
        label2id={lab: i for i, lab in enumerate(labels)},
        **{
            k: v
            for k, v in encoder.config.to_dict().items()
            if k not in {"architectures", "id2label", "label2id", "model_type"}
        },
    )
    config.architectures = ["StencilSentenceClassifier"]
    config.auto_map = {
        "AutoConfig": "modeling_stencil.StencilSentenceClassifierConfig",
        "AutoModelForSequenceClassification": (
            "modeling_stencil.StencilSentenceClassifier"
        ),
    }
    model = StencilSentenceClassifier(config)
    missing, unexpected = model.bert.load_state_dict(encoder.state_dict(), strict=False)
    unexpected = [k for k in unexpected if not k.startswith("pooler.")]
    if missing or unexpected:
        raise RuntimeError(
            f"encoder weight mismatch: missing={missing} unexpected={unexpected}"
        )
    with torch.no_grad():
        model.classifier.weight.copy_(weight[:, :hidden])
        model.classifier.bias.copy_(bias)
        model.role_bias.copy_(weight[:, hidden:].T.contiguous())
    model.eval()

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    model.save_pretrained(out, safe_serialization=True)
    tokenizer.save_pretrained(out)
    shutil.copy(MODELING, out / "modeling_stencil.py")
    if CARD.exists():
        shutil.copy(CARD, out / "README.md")

    rows = load_heldout()
    ref = reference_logits(tokenizer, encoder, saved, rows, torch)
    reloaded = transformers.AutoModelForSequenceClassification.from_pretrained(
        out, trust_remote_code=True
    ).eval()
    got = []
    with torch.no_grad():
        for start in range(0, len(rows), 64):
            chunk = rows[start : start + 64]
            batch = tokenizer(
                [r.get("context") or "(no context)" for r in chunk],
                [f"[{r['role']}] {r['text']}" for r in chunk],
                padding=True,
                truncation="longest_first",
                max_length=MAX_LENGTH,
                return_tensors="pt",
            )
            role_ids = torch.tensor([roles.index(r["role"]) for r in chunk])
            got.append(reloaded(**batch, role_ids=role_ids).logits)
    got = torch.cat(got)
    pred = got.argmax(-1)
    truth = torch.tensor([labels.index(r["label"]) for r in rows])
    report = {
        "n_heldout": len(rows),
        "argmax_identical": bool((pred == ref.argmax(-1)).all()),
        "max_abs_logit_drift": float((got - ref).abs().max()),
        "heldout_accuracy": float((pred == truth).float().mean()),
        "labels": labels,
        "roles": roles,
        "head_sha256_source": str(MODEL_DIR / "head.pt"),
    }
    (out / "verification.json").write_text(json.dumps(report, indent=1))
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--push", action="store_true")
    parser.add_argument(
        "--repo", default="bmarti44/assistant-memory-sentence-classifier"
    )
    args = parser.parse_args(argv)
    import torch
    import transformers

    report = export(args.out, torch, transformers)
    print(json.dumps(report, indent=1))
    if not report["argmax_identical"]:
        print("EXPORT REJECTED: argmax differs from the registered scorer")
        return 1
    if args.push:
        from huggingface_hub import HfApi

        api = HfApi()
        api.create_repo(args.repo, repo_type="model", exist_ok=True, private=False)
        api.upload_folder(
            folder_path=str(args.out),
            repo_id=args.repo,
            repo_type="model",
            ignore_patterns=["verification.json"],
            commit_message="Release 0: assistant-memory sentence classifier",
        )
        print(f"pushed to https://huggingface.co/{args.repo}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
