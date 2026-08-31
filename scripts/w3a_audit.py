# ruff: noqa
"""W3a reproduction audit (sol W3-results HIGH 3): regenerate all five
arms on the W3a seeds deterministically; match every regenerated code's
FULL sha256 against w3a.json's recorded full hashes (full-hash equality
is establishable this time); emit the registered per-work paired
parse/exec records. Does NOT overwrite w3a.json.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401
import torch
from tokenizers import Tokenizer

import w3a as S
from stencil.qwen3 import Qwen3
from stencil.t2_sessions import generate_t2
from stencil.wave import WaveController


def main():
    sealed = json.loads((ROOT / "results" / "qwen" / "w3a.json").read_text())
    tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
    m = Qwen3()
    m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
    m = m.to(torch.bfloat16).cuda().eval()
    ctrls = {}
    for name in ("wave", "proxy"):
        c = WaveController().cuda()
        c.load_state_dict(torch.load(ROOT / "results" / "qwen" / f"w0-{'ce' if name == 'wave' else 'proxy'}.pt", map_location="cpu"))
        ctrls[name] = c.eval()
    arms = ["base", "wave", "proxy", "oracle", "reinsertion"]
    mismatches = 0
    out = {"paired": {a: {} for a in arms}}
    for k, seed in enumerate(S.SEEDS):
        sess = generate_t2(seed, 20, "dev", interference="s0c")
        for arm in arms:
            rs, hs, _ = S.run_arm(m, tok, ctrls.get(arm), sess, arm)
            for r in rs:
                key = f"{seed}:{r.turn}"
                full_hash = hashlib.sha256(r.code.encode()).hexdigest()
                if full_hash != sealed["work_hashes"][arm][key]:
                    mismatches += 1
                out["paired"][arm][key] = {"parse": r.parse, "exec": r.exec_ok}
        if k % 12 == 0:
            print(f"  {k}/96, mismatches {mismatches}", flush=True)
    out["full_hash_mismatches"] = mismatches
    out["reproduction_full_hash_exact"] = mismatches == 0
    # recompute broken counts from the emitted records vs the sealed aggregates
    base = out["paired"]["base"]
    check = {}
    for arm in arms[1:]:
        broken = sum(1 for kk in out["paired"][arm] if
                     (base[kk]["parse"] and not out["paired"][arm][kk]["parse"]) or
                     (base[kk]["exec"] and not out["paired"][arm][kk]["exec"]))
        check[arm] = {"recomputed_broken": broken, "sealed_broken": sealed[arm]["paired_broken"],
                      "match": broken == sealed[arm]["paired_broken"]}
    out["broken_check"] = check
    (ROOT / "results" / "qwen" / "w3a-audit.json").write_text(json.dumps(out))
    print(f"FULL-HASH {'EXACT' if mismatches == 0 else f'MISMATCH x{mismatches}'}", flush=True)
    print(json.dumps(check, indent=1), flush=True)
    print("saved results/qwen/w3a-audit.json", flush=True)


if __name__ == "__main__":
    main()
