# ruff: noqa: E501
"""One-time Qwen3-1.7B conversion (QWEN-PLAN P0).

Hand-parses the safetensors shards (dependency-free, as in convert_gpt2.py),
remaps to the stencil harness names, verifies tied lm_head, runs a parity
battery against a PINNED HF oracle in an isolated env, and freezes our own
outputs as a bitwise fixture. Writes models/qwen3-1.7b.pt (gitignored) and
tests/fixtures/qwen3_parity.pt.
"""
import json
import struct
import subprocess
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
HF = ROOT / "models" / "qwen3-1.7b-hf"

DTYPES = {"BF16": torch.bfloat16, "F32": torch.float32, "F16": torch.float16}


def parse_safetensors(path: Path) -> dict[str, torch.Tensor]:
    raw = path.read_bytes()
    (hlen,) = struct.unpack("<Q", raw[:8])
    header = json.loads(raw[8 : 8 + hlen])
    out = {}
    for name, meta in header.items():
        if name == "__metadata__":
            continue
        lo, hi = meta["data_offsets"]
        buf = bytearray(raw[8 + hlen + lo : 8 + hlen + hi])
        t = torch.frombuffer(buf, dtype=DTYPES[meta["dtype"]]).view(meta["shape"]).clone()
        out[name] = t
    return out


def remap(name: str) -> str | None:
    if name == "lm_head.weight":
        return None  # tied; verified below
    name = name.removeprefix("model.")
    name = name.replace("self_attn.", "").replace("mlp.", "")
    return name


BATTERY = [
    "The capital of France is",
    "def fibonacci(n):",
    "Water boils at a temperature of",
    "New rule: reply to \"cat\" with \"dog\". cat ->",
    "The opposite of hot is",
    "1, 2, 3, 4, 5,",
    "Once upon a time there was a",
    "import torch\nimport numpy as",
]

ORACLE_WORKER = r"""
import json, sys, torch
from transformers import AutoModelForCausalLM, AutoTokenizer
tok = AutoTokenizer.from_pretrained(sys.argv[1])
model = AutoModelForCausalLM.from_pretrained(sys.argv[1], torch_dtype=torch.bfloat16).cuda().eval()
out = {}
for prompt in json.load(open(sys.argv[2])):
    ids = tok(prompt, return_tensors="pt").input_ids.cuda()
    with torch.no_grad():
        logits = model(ids).logits[0, -1].float().cpu()
    out[prompt] = {"ids": ids[0].tolist(), "logits": logits.tolist()}
torch.save(out, sys.argv[3])
"""


def main() -> None:
    sd: dict[str, torch.Tensor] = {}
    for shard in sorted(HF.glob("*.safetensors")):
        sd.update(parse_safetensors(shard))
    assert torch.equal(sd["lm_head.weight"], sd["model.embed_tokens.weight"]), "lm_head not tied"
    ours = {}
    for name, t in sd.items():
        new = remap(name)
        if new is not None:
            ours[new] = t
    from stencil.qwen3 import Qwen3

    model = Qwen3()
    missing, unexpected = model.load_state_dict(ours, strict=False)
    assert not missing and not unexpected, (missing, unexpected)
    torch.save(ours, ROOT / "models" / "qwen3-1.7b.pt")
    print(f"saved {len(ours)} tensors")

    # oracle battery (pinned env)
    scratch = ROOT / "models" / "qwen3-oracle"
    scratch.mkdir(exist_ok=True)
    (scratch / "prompts.json").write_text(json.dumps(BATTERY))
    (scratch / "worker.py").write_text(ORACLE_WORKER)
    subprocess.run(
        ["uv", "run", "--isolated", "--with", "transformers==4.51.0", "--with", "accelerate",
         "python", str(scratch / "worker.py"), str(HF), str(scratch / "prompts.json"),
         str(scratch / "oracle.pt")],
        check=True,
    )
    oracle = torch.load(scratch / "oracle.pt", map_location="cpu")

    model = model.to(torch.bfloat16).cuda().eval()
    fixture = {}
    worst = 0.0
    with torch.no_grad():
        for prompt, entry in oracle.items():
            ids = torch.tensor([entry["ids"]], device="cuda")
            ref = torch.tensor(entry["logits"])
            got = model(ids)[0, -1].float().cpu()
            err = float((got - ref).abs().max())
            worst = max(worst, err)
            top_ok = int(got.argmax()) == int(ref.argmax())
            print(f"max|err| {err:.4f} top1 {'OK' if top_ok else 'MISMATCH'} :: {prompt[:40]!r}")
            assert top_ok, "top-1 disagreement with oracle"
            fixture[prompt] = {"ids": entry["ids"], "last_logits": got}
    print(f"worst max|err| = {worst:.4f}")
    torch.save(fixture, ROOT / "tests" / "fixtures" / "qwen3_parity.pt")
    print("bitwise fixture frozen")


if __name__ == "__main__":
    main()
