# ruff: noqa
"""Fix theta calibration: theta = max(abstain score) + eps (zero false press
on calib by construction), report live-press retention. Loads saved heads;
regenerates calib features only."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401
import torch
from tokenizers import Tokenizer

from stencil.qwen3 import Qwen3
from stencil.t2_sessions import generate_t2

sys.path.insert(0, str(ROOT / "scripts"))
import t2_train_selector as T

import os
T2B = bool(os.environ.get("T2B"))
NAME = "t2b-selector.pt" if T2B else "t2-selector.pt"
sel = torch.load(ROOT / "results" / "qwen" / NAME, map_location="cpu")
Wq = torch.nn.Linear(2048, 64); Wq.load_state_dict(sel["Wq"])
Wk = torch.nn.Linear(2048, 64); Wk.load_state_dict(sel["Wk"])
live, abstain = [], []
for seed in T.CALIB:
    sess = generate_t2(seed, 20, "dev", interference=("s0" if T2B else "v3"))
    _, _, ad = T.gen_and_collect(sess, "dev", "base")
    with torch.no_grad():
        for s, cf, t, is_live in ad:
            sc = float(((Wq(s) @ Wk(cf).T) / 8.0).max())
            (live if is_live else abstain).append(sc)
THETA = max(abstain) + 1e-6 if abstain else -1e9
kept = sum(1 for sc in live if sc > THETA)
print(f"theta={THETA:.3f}: calib abstain false-press 0/{len(abstain)}, live kept {kept}/{len(live)}")
sel["theta"] = THETA
sel["calib"]["abstain_false_press"] = 0
sel["calib"]["live_kept"] = kept / max(1, len(live))
torch.save(sel, ROOT / "results" / "qwen" / NAME)
print("updated results/qwen/t2-selector.pt")
