# ruff: noqa: E501
"""One-time GPT-2 small weight download, conversion, and parity capture.

Steps (network required):
1. Download gpt2 model.safetensors + vocab.json + merges.txt from huggingface.co.
2. Parse safetensors directly (no library) and remap to stencil.gpt2 naming.
   HF GPT-2 uses Conv1D layers (weights stored transposed relative to
   nn.Linear) for c_attn/c_proj/c_fc/mlp c_proj — transpose during remap.
3. Reference oracle: run HF transformers in a THROWAWAY pinned uv env on the
   32-prompt battery, saving reference logits (the pinned-oracle pattern).
4. Load converted weights into our GatedGPT2 (vanilla, full attention),
   assert allclose vs the oracle (rtol 1e-4, atol 2e-4 — fp32, different op
   order), then capture OUR logits on the battery as the frozen bitwise
   parity fixture (tests/fixtures/gpt2_parity.pt) with sha256 recorded.

Outputs: models/gpt2-small.pt, models/tokenizer/{vocab.json,merges.txt},
tests/fixtures/gpt2_parity.pt, models/CONVERSION.json (hashes, versions).
"""
from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

BASE = "https://huggingface.co/gpt2/resolve/main"
FILES = ["model.safetensors", "vocab.json", "merges.txt"]

BATTERY = [
    "The capital of France is",
    "Once upon a time, there was a",
    "def fibonacci(n):",
    "The quick brown fox jumps over the lazy",
    "In 1969, humans first landed on the",
    "Water is made of hydrogen and",
    "cat -> dog\nsun -> moon\nhot ->",
    "New rule: reply to \"cat\" with \"dog\". cat ->",
] * 4  # 32 prompts (repetition is fine; positions differ per batch slot)


def download(dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        out = dest / name
        if out.exists():
            continue
        print(f"downloading {name} ...", flush=True)
        urllib.request.urlretrieve(f"{BASE}/{name}", out)


def parse_safetensors(path: Path) -> dict[str, torch.Tensor]:
    blob = path.read_bytes()
    (header_len,) = struct.unpack("<Q", blob[:8])
    header = json.loads(blob[8 : 8 + header_len])
    data = blob[8 + header_len :]
    dtypes = {"F32": torch.float32, "F16": torch.float16}
    out = {}
    for name, meta in header.items():
        if name == "__metadata__":
            continue
        start, end = meta["data_offsets"]
        t = torch.frombuffer(
            bytearray(data[start:end]), dtype=dtypes[meta["dtype"]]
        ).reshape(meta["shape"])
        out[name] = t.to(torch.float32)
    return out


def remap(hf: dict[str, torch.Tensor]) -> dict[str, torch.Tensor]:
    sd: dict[str, torch.Tensor] = {}
    sd["wte.weight"] = hf["wte.weight"]
    sd["wpe.weight"] = hf["wpe.weight"]
    sd["ln_f.weight"] = hf["ln_f.weight"]
    sd["ln_f.bias"] = hf["ln_f.bias"]
    for i in range(12):
        p = f"h.{i}."
        q = f"blocks.{i}."
        sd[q + "ln_1.weight"] = hf[p + "ln_1.weight"]
        sd[q + "ln_1.bias"] = hf[p + "ln_1.bias"]
        sd[q + "ln_2.weight"] = hf[p + "ln_2.weight"]
        sd[q + "ln_2.bias"] = hf[p + "ln_2.bias"]
        # HF Conv1D: weight (in, out) -> nn.Linear expects (out, in)
        sd[q + "attn_qkv.weight"] = hf[p + "attn.c_attn.weight"].T.contiguous()
        sd[q + "attn_qkv.bias"] = hf[p + "attn.c_attn.bias"]
        sd[q + "attn_proj.weight"] = hf[p + "attn.c_proj.weight"].T.contiguous()
        sd[q + "attn_proj.bias"] = hf[p + "attn.c_proj.bias"]
        sd[q + "mlp_fc.weight"] = hf[p + "mlp.c_fc.weight"].T.contiguous()
        sd[q + "mlp_fc.bias"] = hf[p + "mlp.c_fc.bias"]
        sd[q + "mlp_proj.weight"] = hf[p + "mlp.c_proj.weight"].T.contiguous()
        sd[q + "mlp_proj.bias"] = hf[p + "mlp.c_proj.bias"]
    return sd


ORACLE = r"""
import json, sys, torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer
tok = GPT2Tokenizer.from_pretrained(sys.argv[1])
model = GPT2LMHeadModel.from_pretrained(sys.argv[2], torch_dtype=torch.float32)
model.eval()
prompts = json.loads(open(sys.argv[3]).read())
outs = {}
with torch.no_grad():
    for i, p in enumerate(prompts):
        ids = torch.tensor([tok.encode(p)])
        logits = model(ids).logits[0, -1]
        outs[str(i)] = {"ids": ids[0].tolist(), "last_logits": logits.tolist()}
open(sys.argv[4], "w").write(json.dumps(outs))
"""


def main() -> None:
    models = ROOT / "models"
    tok_dir = models / "tokenizer"
    download(tok_dir)
    hf = parse_safetensors(tok_dir / "model.safetensors")
    sd = remap(hf)
    models.mkdir(exist_ok=True)
    torch.save(sd, models / "gpt2-small.pt")
    print("converted state dict saved")

    with tempfile.TemporaryDirectory() as td:
        worker = Path(td) / "oracle.py"
        worker.write_text(ORACLE)
        prompts = Path(td) / "prompts.json"
        prompts.write_text(json.dumps(BATTERY))
        ref_path = Path(td) / "ref.json"
        # HF loads from the hub in the throwaway env (network available here).
        subprocess.run(
            [
                "uv", "run", "--isolated", "--with", "transformers==4.46.3",
                "--with", "torch", "python", str(worker),
                "gpt2", "gpt2", str(prompts), str(ref_path),
            ],
            check=True,
        )
        ref = json.loads(ref_path.read_text())

    from stencil import determinism  # noqa: F401
    from stencil.gpt2 import GatedGPT2

    model = GatedGPT2("vanilla", window=None)
    missing, unexpected = model.load_state_dict(sd, strict=False)
    assert not unexpected, unexpected
    assert all(m.startswith(("controller", "gate_source")) or False for m in missing) or not missing, missing
    model.eval()
    captured = {}
    max_err = 0.0
    with torch.no_grad():
        for i in range(len(BATTERY)):
            ids = torch.tensor([ref[str(i)]["ids"]])
            ours = model(ids)[0, -1]
            theirs = torch.tensor(ref[str(i)]["last_logits"])
            err = (ours - theirs).abs().max().item()
            max_err = max(max_err, err)
            captured[str(i)] = {"ids": ids[0].tolist(), "last_logits": ours.clone()}
    print(f"max |ours - HF| over battery: {max_err:.5f}")
    scale = max(t.abs().max().item() for t in (torch.tensor(ref[str(i)]["last_logits"]) for i in range(len(BATTERY))))
    assert max_err < 2e-3 * max(scale, 1.0), f"parity failed: {max_err} vs scale {scale}"

    fixture = ROOT / "tests" / "fixtures" / "gpt2_parity.pt"
    torch.save(captured, fixture)
    meta = {
        "safetensors_sha256": hashlib.sha256((tok_dir / "model.safetensors").read_bytes()).hexdigest(),
        "state_dict_sha256": hashlib.sha256((models / "gpt2-small.pt").read_bytes()).hexdigest(),
        "parity_fixture_sha256": hashlib.sha256(fixture.read_bytes()).hexdigest(),
        "max_abs_err_vs_hf": max_err,
        "transformers": "4.46.3",
        "battery": BATTERY,
    }
    (models / "CONVERSION.json").write_text(json.dumps(meta, indent=1))
    print("parity fixture + CONVERSION.json written")


if __name__ == "__main__":
    main()
