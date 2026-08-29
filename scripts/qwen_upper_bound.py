# ruff: noqa: E501
"""P0 admission: with the task state fully VISIBLE, frozen Qwen3-1.7B must
answer >=80% exact-match (greedy). Else the benchmark tests model incapacity."""
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil.qwen3 import Qwen3  # noqa: E402
from stencil.qwen_task import generate  # noqa: E402


def load_tok():
    tok_cfg = ROOT / "models" / "qwen3-1.7b-hf"
    sys.path.insert(0, str(ROOT / "src"))
    # minimal: reuse HF tokenizer via tokenizers package if present, else worker
    from tokenizers import Tokenizer
    return Tokenizer.from_file(str(tok_cfg / "tokenizer.json"))


def main() -> None:
    tok = load_tok()
    m = Qwen3()
    m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=False)
    m = m.to(torch.bfloat16).cuda().eval()
    hits = 0
    n = 32
    with torch.no_grad():
        for i in range(n):
            s = generate(9_000_000 + i)
            ids = tok.encode(s.text).ids
            toks = torch.tensor([ids], device="cuda")
            outs = []
            for _ in range(24):
                nxt = int(m(toks)[0, -1].argmax())
                outs.append(nxt)
                toks = torch.cat([toks, torch.tensor([[nxt]], device="cuda")], dim=1)
            text = tok.decode(outs)
            first_line = text.strip().split("\n")[0].strip().rstrip(".")
            ok = first_line == s.value
            hits += ok
            print(f"ex {i}: {'HIT' if ok else 'miss'} ({s.field} -> {s.value})", flush=True)
    print(f"VISIBLE-TASK UPPER BOUND: {hits}/{n} = {hits/n:.2f} (gate >= 0.80)")


if __name__ == "__main__":
    main()
