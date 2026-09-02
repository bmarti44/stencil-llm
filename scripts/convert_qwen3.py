# ruff: noqa: E501
"""Convert Qwen3 dense HF checkpoints to the hand-rolled trunk format."""

import argparse
import json
import mmap
import struct
import subprocess
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from stencil.qwen3 import Qwen3, Qwen3Config  # noqa: E402

DTYPES = {"BF16": torch.bfloat16, "F32": torch.float32, "F16": torch.float16}
MODEL_PATHS = {
    "1.7b": (
        ROOT / "models/qwen3-1.7b-hf",
        ROOT / "models/qwen3-1.7b.pt",
        ROOT / "tests/fixtures/qwen3_parity.pt",
    ),
    "4b": (
        ROOT / "models/qwen3-4b-hf",
        ROOT / "models/qwen3-4b.pt",
        ROOT / "tests/fixtures/qwen3-4b_parity.pt",
    ),
}

LEGACY_BATTERY = [
    "The capital of France is",
    "def fibonacci(n):",
    "Water boils at a temperature of",
    'New rule: reply to "cat" with "dog". cat ->',
    "The opposite of hot is",
    "1, 2, 3, 4, 5,",
    "Once upon a time there was a",
    "import torch\nimport numpy as",
]
BATTERY_4B = [
    f"{prompt}\nVariation {variation}:"
    for variation in range(4)
    for prompt in LEGACY_BATTERY
]

ORACLE_WORKER = r"""
import json, sys, torch
from transformers import AutoModelForCausalLM, AutoTokenizer
tok = AutoTokenizer.from_pretrained(sys.argv[1])
model = AutoModelForCausalLM.from_pretrained(sys.argv[1], torch_dtype=torch.bfloat16).cuda().eval()
out = {}
for i, prompt in enumerate(json.load(open(sys.argv[2]))):
    ids = tok(prompt, return_tensors="pt").input_ids.cuda()
    with torch.no_grad():
        logits = model(ids).logits[0, -1].float().cpu()
    out[str(i)] = {"prompt": prompt, "ids": ids[0].tolist(), "logits": logits.tolist()}
torch.save(out, sys.argv[3])
"""


def parse_safetensors(path: Path) -> dict[str, torch.Tensor]:
    out = {}
    with path.open("rb") as fh, mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_COPY) as raw:
        (hlen,) = struct.unpack("<Q", raw[:8])
        header = json.loads(raw[8 : 8 + hlen])
        for name, meta in header.items():
            if name == "__metadata__":
                continue
            lo, hi = meta["data_offsets"]
            t = torch.frombuffer(
                raw,
                dtype=DTYPES[meta["dtype"]],
                count=(hi - lo) // DTYPES[meta["dtype"]].itemsize,
                offset=8 + hlen + lo,
            )
            out[name] = t.view(meta["shape"]).clone()
    return out


def remap(name: str, cfg: Qwen3Config) -> str | None:
    if name == "lm_head.weight":
        return None if cfg.tie_word_embeddings else name
    name = name.removeprefix("model.")
    return name.replace("self_attn.", "").replace("mlp.", "")


def resolve_paths(
    model: str, hf_dir: Path | None, out: Path | None
) -> tuple[Path, Path, Path]:
    default_hf, default_out, fixture = MODEL_PATHS[model]
    return hf_dir or default_hf, out or default_out, fixture


def convert(hf_dir: Path, out: Path) -> Qwen3Config:
    cfg = Qwen3Config.from_hf(hf_dir / "config.json")
    ours: dict[str, torch.Tensor] = {}
    tied_head = None
    for shard in sorted(hf_dir.glob("*.safetensors")):
        for name, tensor in parse_safetensors(shard).items():
            if name == "lm_head.weight" and cfg.tie_word_embeddings:
                tied_head = tensor
                continue
            ours[remap(name, cfg)] = tensor
    if not ours:
        raise FileNotFoundError(f"no safetensors shards found in {hf_dir}")
    if tied_head is not None:
        assert torch.equal(tied_head, ours["embed_tokens.weight"]), "tied lm_head differs from embeddings"

    # Meta construction validates exact key coverage without allocating a
    # second full checkpoint-sized parameter set on CPU.
    with torch.device("meta"):
        model = Qwen3(cfg)
    expected = model.state_dict()
    missing = expected.keys() - ours.keys()
    unexpected = ours.keys() - expected.keys()
    assert not missing and not unexpected, (missing, unexpected)
    wrong_shapes = {
        name: (tuple(ours[name].shape), tuple(expected[name].shape))
        for name in expected.keys() & ours.keys()
        if ours[name].shape != expected[name].shape
    }
    assert not wrong_shapes, wrong_shapes
    out.parent.mkdir(parents=True, exist_ok=True)
    torch.save(ours, out)
    print(f"saved {len(ours)} tensors to {out}")
    return cfg


def capture_parity(
    model_name: str,
    hf_dir: Path,
    out: Path,
    fixture_path: Path,
    cfg: Qwen3Config,
) -> None:
    battery = LEGACY_BATTERY if model_name == "1.7b" else BATTERY_4B
    scratch = ROOT / "models" / "qwen3-oracle"
    scratch.mkdir(exist_ok=True)
    (scratch / "prompts.json").write_text(json.dumps(battery))
    (scratch / "worker.py").write_text(ORACLE_WORKER)
    subprocess.run(
        [
            "uv", "run", "--isolated", "--with", "transformers==4.51.0",
            "--with", "accelerate", "python", str(scratch / "worker.py"),
            str(hf_dir), str(scratch / "prompts.json"), str(scratch / "oracle.pt"),
        ],
        check=True,
    )
    oracle = torch.load(scratch / "oracle.pt", map_location="cpu")
    model = Qwen3(cfg)
    model.load_state_dict(torch.load(out, map_location="cpu"), strict=True)
    model = model.to(torch.bfloat16).cuda().eval()
    fixture = {}
    worst = 0.0
    with torch.no_grad():
        for key, entry in oracle.items():
            ids = torch.tensor([entry["ids"]], device="cuda")
            ref = torch.tensor(entry["logits"])
            got = model(ids)[0, -1].float().cpu()
            err = float((got - ref).abs().max())
            worst = max(worst, err)
            assert int(got.argmax()) == int(ref.argmax()), f"top-1 disagreement for {entry['prompt']!r}"
            fixture[key] = {
                "prompt": entry["prompt"],
                "ids": entry["ids"],
                "last_logits": got,
            }
    print(f"worst max|err| = {worst:.4f}")
    torch.save(fixture, fixture_path)
    print(f"saved {len(fixture)}-prompt parity fixture to {fixture_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=MODEL_PATHS, default="1.7b")
    parser.add_argument("--hf-dir", type=Path, help="HF checkpoint directory")
    parser.add_argument("--out", type=Path, help="converted state-dict path")
    parser.add_argument("--skip-parity", action="store_true", help="convert without using the GPU")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    hf_dir, out, fixture = resolve_paths(args.model, args.hf_dir, args.out)
    cfg = convert(hf_dir, out)
    if not args.skip_parity:
        capture_parity(args.model, hf_dir, out, fixture, cfg)


if __name__ == "__main__":
    main()
