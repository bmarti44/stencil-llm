# ruff: noqa
"""Deterministic reproduction audit of the sealed run (sol checkpoint-iv
HIGHs 1/3). NOT a second attempt: identical policy, seeds, decoding —
every regenerated output is verified against the sealed run's recorded
hash prefixes before any new statistic is emitted. Emits: full-length
sha256 per work, per-work paired parse/exec records, and per-type
(incl. comment-class) adherence per arm.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401
import torch

import w_seal as S  # model/ctrl loading is inside main(); reuse run_arm + constants
from stencil.qwen3 import Qwen3
from stencil.t2_sessions import generate_t2
from stencil.wave import WaveController
from tokenizers import Tokenizer


def main():
    sealed = json.loads((ROOT / "results" / "qwen" / "w-seal.json").read_text())
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
    out = {"paired": {a: {} for a in arms}, "hashes_full": {a: {} for a in arms},
           "per_type": {a: {} for a in arms}}
    for k, seed in enumerate(S.SEEDS):
        sess = generate_t2(seed, 20, S.SPLIT, interference="s0")
        for arm in arms:
            rs, _, _ = S.run_arm(m, tok, ctrls.get(arm), sess, arm)
            for r in rs:
                key = f"{seed}:{r.turn}"
                # rebuild the full code hash and check the sealed prefix
                code_hash = None
                # re-derive code from scoring is not possible; recompute hash via run_arm's own hashing:
                # (run_arm returned hashes in the seal; here recompute from r.code)
                code_hash = hashlib.sha256(r.code.encode()).hexdigest()
                if not code_hash.startswith(sealed["work_hashes"][arm][key]):
                    mismatches += 1
                out["hashes_full"][arm][key] = code_hash
                out["paired"][arm][key] = {"parse": r.parse, "exec": r.exec_ok}
                for o in sess.opportunities:
                    if o.turn == r.turn and o.cell == "active":
                        d = out["per_type"][arm].setdefault(o.moment_class, {"adh": 0, "n": 0})
                        d["n"] += 1
                        d["adh"] += bool(r.per_opportunity.get(o.opportunity_id, {}).get("adherent"))
        if k % 12 == 0:
            print(f"  {k}/96 sessions, mismatches {mismatches}", flush=True)
    out["hash_mismatches"] = mismatches
    out["reproduction_exact"] = mismatches == 0
    for a in arms:
        for ty, d in out["per_type"][a].items():
            d["adherence"] = round(d["adh"] / max(1, d["n"]), 4)
    (ROOT / "results" / "qwen" / "w-seal-audit.json").write_text(json.dumps(out))
    print(f"REPRODUCTION {'EXACT' if mismatches == 0 else f'MISMATCH x{mismatches}'}", flush=True)
    print("per-type (wave):", json.dumps(out["per_type"]["wave"]), flush=True)
    print("saved results/qwen/w-seal-audit.json", flush=True)


if __name__ == "__main__":
    main()
