"""Assemble and push the bmarti44/stencil-focus-qwen3-1.7b model repo.

Layout pushed: the Qwen3-1.7B safetensors + tokenizer files copied from the local
trunk, a config.json with model_type ``stencil_focus`` and ``auto_map`` pointing at
the remote code, the three package modules at the repo root (trust_remote_code),
and README.md (the model card). ``--dry-run`` lists the files without pushing.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
PACKAGE = HERE / "stencil_focus"
MODULES = [
    "configuration_stencil_focus.py",
    "modeling_stencil_focus.py",
    "focus_session.py",
]
TRUNK_FILES = [
    "generation_config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "vocab.json",
    "merges.txt",
]


def assemble(
    trunk: Path, out: Path, stencil_focus: bool = True, card: Path | None = None
) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    written = []
    # weight shards are globbed (1.7B ships two shards, 4B three) plus the index
    shards = sorted(p.name for p in trunk.glob("model*.safetensors"))
    if not shards:
        raise SystemExit(f"no safetensors shards under {trunk}")
    index = trunk / "model.safetensors.index.json"
    names = shards + ([index.name] if index.exists() else []) + TRUNK_FILES
    for name in names:
        target = out / name
        if not target.exists():
            shutil.copy2(trunk / name, target)
        written.append(target)
    config = json.loads((trunk / "config.json").read_text())
    config["architectures"] = ["StencilFocusForCausalLM"]
    config["model_type"] = "stencil_focus"
    config["auto_map"] = {
        "AutoConfig": "configuration_stencil_focus.StencilFocusConfig",
        "AutoModelForCausalLM": "modeling_stencil_focus.StencilFocusForCausalLM",
    }
    config["stencil_focus"] = stencil_focus
    config["focus_window"] = 3584
    config["focus_budget"] = 256
    (out / "config.json").write_text(json.dumps(config, indent=2) + "\n")
    written.append(out / "config.json")
    for name in MODULES:
        shutil.copy2(PACKAGE / name, out / name)
        written.append(out / name)
    card = card or HERE / "MODEL_CARD.md"
    if card.exists():
        shutil.copy2(card, out / "README.md")
        written.append(out / "README.md")
    return written


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--trunk", default=str(HERE.parents[1] / "models/qwen3-1.7b-hf")
    )
    parser.add_argument("--out", default=str(HERE / "build" / "hub"))
    parser.add_argument("--repo", default="bmarti44/stencil-focus-qwen3-1.7b")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--card",
        default=None,
        help="model card to publish as README.md (default MODEL_CARD.md; "
        "MODEL_CARD-4b.md for the Qwen3-4B build)",
    )
    args = parser.parse_args(argv)
    files = assemble(
        Path(args.trunk), Path(args.out), card=Path(args.card) if args.card else None
    )
    for f in files:
        print(f"{f.stat().st_size:>12} {f.relative_to(args.out)}")
    if args.dry_run:
        return 0
    from huggingface_hub import HfApi

    api = HfApi()
    api.create_repo(args.repo, repo_type="model", exist_ok=True)
    api.upload_folder(folder_path=args.out, repo_id=args.repo, repo_type="model")
    print(f"pushed to https://huggingface.co/{args.repo}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
