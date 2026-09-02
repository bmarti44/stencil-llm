#!/usr/bin/env python
# ruff: noqa: E501
"""Upload the stencil_wave add-on weights + model card to the HuggingFace Hub.

DRY RUN BY DEFAULT: lists what would be uploaded, verifies the files, and
prints the model card. Pass --push (and have a write token: `huggingface-cli
login` or HF_TOKEN) to actually upload.

    python scripts/push_to_hub.py --repo <org>/stencil-wave-qwen3-1.7b [--push]

Uploads ONLY the add-on (controller.safetensors ~1 MB, salience_weights.json,
config.json, README.md model card). The Qwen3-1.7B trunk itself is not
re-uploaded; the package always loads it from Qwen/Qwen3-1.7B at the pinned
revision.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent / "src" / "stencil_wave"
CARD = HERE.parent / "MODEL_CARD.md"


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build_staging(staging: Path) -> list[Path]:
    sys.path.insert(0, str(PKG.parent))
    from stencil_wave import REVISION, __version__
    from stencil_wave.attention import WAVE_LAYERS
    from stencil_wave.controller import N_PARAMS, WaveController
    from stencil_wave.model import MODEL_ID, TRANSFORMERS_PIN
    from stencil_wave.salience import load_model

    staging.mkdir(parents=True, exist_ok=True)
    files = []
    for name in ("controller.safetensors", "salience_weights.json"):
        src = PKG / "weights" / name
        dst = staging / name
        dst.write_bytes(src.read_bytes())
        files.append(dst)
    ctrl = WaveController.load(staging / "controller.safetensors")
    assert sum(p.numel() for p in ctrl.parameters()) == N_PARAMS
    load_model(staging / "salience_weights.json")  # raises if untrained / mismatched
    config = {
        "package": "stencil-wave", "version": __version__,
        "base_model": MODEL_ID, "base_model_revision": REVISION, "transformers": TRANSFORMERS_PIN,
        "controller": {"file": "controller.safetensors", "params": N_PARAMS, "arch": "W_q/W_k 2048->64, w_g 2048->1",
                       "sha256": sha256(staging / "controller.safetensors")},
        "salience": {"file": "salience_weights.json", "sha256": sha256(staging / "salience_weights.json")},
        "actuation": {"capture_layer": 20, "bias_layers": list(WAVE_LAYERS), "dose": 3.0, "top_k": 2, "hold": "aged",
                      "bias": "additive pre-softmax, fp32, last query row, over selected entries' key columns"},
    }
    (staging / "config.json").write_text(json.dumps(config, indent=1) + "\n")
    files.append(staging / "config.json")
    (staging / "README.md").write_text(CARD.read_text())
    files.append(staging / "README.md")
    return files


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="Hub repo id, e.g. <org>/stencil-wave-qwen3-1.7b")
    ap.add_argument("--push", action="store_true", help="actually upload (default: dry run)")
    ap.add_argument("--staging", default=str(HERE.parent / "build" / "hub"))
    ap.add_argument("--private", action="store_true")
    args = ap.parse_args()

    files = build_staging(Path(args.staging))
    print(f"repo: {args.repo}  ({'PUSH' if args.push else 'DRY RUN'})")
    for f in files:
        print(f"  {f.name:24s} {f.stat().st_size:>9d} B  sha256={sha256(f)[:16]}")
    if not args.push:
        print("\n--- model card ---\n" + CARD.read_text())
        print("dry run: nothing uploaded (add --push).")
        return 0
    try:
        from huggingface_hub import HfApi
    except ImportError:
        print("huggingface_hub is not installed: pip install 'stencil-wave[hub]'", file=sys.stderr)
        return 2
    api = HfApi()
    who = api.whoami()
    print(f"authenticated as {who.get('name')}")
    api.create_repo(args.repo, repo_type="model", exist_ok=True, private=args.private)
    info = api.upload_folder(folder_path=args.staging, repo_id=args.repo, repo_type="model",
                             commit_message="stencil_wave add-on weights + model card")
    print("uploaded:", info)
    return 0


if __name__ == "__main__":
    sys.exit(main())
