# ruff: noqa
"""B0.1 provenance + parity (BENCH-WAVE v2.2 criteria, frozen):
records repo revision + sha256 of config/tokenizer/index/shards/.pt;
verifies our pinned chat-template f-string and trunk behavior against
transformers 4.51.0 loading the exact local snapshot in an ISOLATED
env (convert_qwen3 oracle pattern). PASS: template token ids bitwise
equal on every fixture; top-1 equal on every fixture; finite logits;
max_abs_error <= 0.5.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401
import torch
from tokenizers import Tokenizer

from stencil.qwen3 import Qwen3

FIXTURES = [
    "Write your response in all capital letters.\n\nDescribe a sunny day.",
    "Answer with fewer than 40 words. What is a linked list?",
    "Your entire output must be valid JSON. List two fruits.",
    "Include the keyword 'harvest' at least twice. Write about autumn.",
]
# pinned non-thinking single-turn template (v1.1; verified vs HF below)
TMPL = "<|im_start|>user\n{p}<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"

ORACLE = r"""
import json, sys
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
snap = sys.argv[1]
fixtures = json.loads(sys.argv[2])
tok = AutoTokenizer.from_pretrained(snap)
model = AutoModelForCausalLM.from_pretrained(snap, torch_dtype=torch.bfloat16).cuda().eval()
out = []
for p in fixtures:
    msgs = [{"role": "user", "content": p}]
    text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    ids = tok(text, return_tensors="pt").input_ids
    with torch.no_grad():
        logits = model(ids.cuda()).logits[0, -1].float().cpu()
    out.append({"template_text": text, "ids": ids[0].tolist(),
                "top1": int(logits.argmax()), "logits_slice": logits[:2000].tolist()})
print(json.dumps(out))
"""


def main():
    hf = ROOT / "models" / "qwen3-1.7b-hf"
    rec = {"revision": "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e", "hashes": {}}
    for f in ["config.json", "tokenizer.json", "tokenizer_config.json",
              "model.safetensors.index.json", "model-00001-of-00002.safetensors",
              "model-00002-of-00002.safetensors"]:
        fp = hf / f
        if fp.exists():
            rec["hashes"][f] = hashlib.sha256(fp.read_bytes()).hexdigest()
    rec["hashes"]["qwen3-1.7b.pt"] = hashlib.sha256((ROOT / "models" / "qwen3-1.7b.pt").read_bytes()).hexdigest()

    scratch = Path("/tmp/claude-1000/-home-bmarti44-stencil-llm/a88136df-3902-46b9-a661-86e0dc1bb53f/scratchpad")
    (scratch / "b0_oracle.py").write_text(ORACLE)
    r = subprocess.run(["uv", "run", "--isolated", "--no-project", "--with", "transformers==4.51.0",
                        "--with", "accelerate", "python", str(scratch / "b0_oracle.py"),
                        str(hf), json.dumps(FIXTURES)],
                       capture_output=True, text=True, timeout=1200)
    if r.returncode != 0:
        sys.exit(f"oracle failed: {r.stderr[-800:]}")
    oracle = json.loads(r.stdout.strip().split("\n")[-1])

    tok = Tokenizer.from_file(str(hf / "tokenizer.json"))
    m = Qwen3()
    m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
    m = m.to(torch.bfloat16).cuda().eval()
    checks = []
    worst = 0.0
    for p, o in zip(FIXTURES, oracle):
        ours_text = TMPL.format(p=p)
        ids = tok.encode(ours_text).ids
        template_ok = ours_text == o["template_text"]
        ids_ok = ids == o["ids"]
        with torch.no_grad():
            logits = m(torch.tensor([ids], device="cuda"))[0, -1].float().cpu()
        top1_ok = int(logits.argmax()) == o["top1"]
        err = float((logits[:2000] - torch.tensor(o["logits_slice"])).abs().max())
        worst = max(worst, err)
        finite = bool(torch.isfinite(logits).all())
        checks.append({"template_ok": template_ok, "ids_ok": ids_ok,
                       "top1_ok": top1_ok, "max_abs_err_slice": round(err, 4), "finite": finite})
    rec["checks"] = checks
    rec["worst_err"] = round(worst, 4)
    rec["PASS"] = all(c["template_ok"] and c["ids_ok"] and c["top1_ok"] and c["finite"] for c in checks) and worst <= 0.5
    print(json.dumps(rec["checks"], indent=1), flush=True)
    print("worst_err", rec["worst_err"], "PASS", rec["PASS"], flush=True)
    (ROOT / "results" / "qwen" / "b0-identity.json").write_text(json.dumps(rec, indent=1))


if __name__ == "__main__":
    main()
