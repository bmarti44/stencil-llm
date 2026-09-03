"""Diagnose the fine-tuned classifier's collapse on the probe: score the unique true-constraint sentences under
(a) as-is with context, (b) no context, (c) capitalized first letter, (d) capitalized + no context."""
import glob, json, os, sys
os.environ["CUDA_VISIBLE_DEVICES"] = ""
import torch
from tokenizers import Tokenizer
from transformers import AutoTokenizer, AutoModel

ROOT = "/home/bmarti44/stencil-llm"; S = sys.argv[1]
FT = os.environ.get("FT_DIR", ROOT + "/data/classifier/model/ft")
tk = AutoTokenizer.from_pretrained(FT + "/encoder"); enc = AutoModel.from_pretrained(FT + "/encoder").eval()
hd = torch.load(FT + "/head.pt"); ROLES, LABELS = hd["roles"], hd["labels"]
head = torch.nn.Sequential(torch.nn.Dropout(0.1), torch.nn.Linear(hd["hidden"] + len(ROLES), 3)); head.load_state_dict(hd["head"]); head.eval()
tok = Tokenizer.from_file(ROOT + "/models/qwen3-1.7b-hf/tokenizer.json")


@torch.no_grad()
def score(pairs, role="user"):
    t = tk([a if a else "(no context)" for a, _ in pairs], [f"[{role}] {b}" for _, b in pairs], padding=True, truncation="only_first", max_length=192, return_tensors="pt")
    h = enc(**t).last_hidden_state[:, 0]
    R = torch.tensor([[float(role == r) for r in ROLES]] * len(pairs))
    p = torch.softmax(head(torch.cat([h, R], 1)), -1)
    return (p[:, LABELS.index("rule")] + p[:, LABELS.index("fact")]).tolist()


sents = []
for p in sorted(glob.glob(ROOT + "/results/qwen/ledger-kv-probe-h1p/session-*.json")):
    r = json.load(open(p)); ids = r["context_token_ids"]
    for a, b in r["keep"]:
        s = tok.decode(ids[a:b]).strip()
        if s and s not in sents:
            sents.append(s)
print("unique true constraint sentences:", len(sents))
variants = {
    "as-is, no context": [("", s) for s in sents],
    "as-is, with context": [("user: Write a short account of arranging a pantry shelf for a neighborhood newsletter.", s) for s in sents],
    "capitalized, no context": [("", s[0].upper() + s[1:]) for s in sents],
    "capitalized, with context": [("user: Write a short account of arranging a pantry shelf for a neighborhood newsletter.", s[0].upper() + s[1:]) for s in sents],
}
for name, pairs in variants.items():
    sc = score(pairs)
    print(f"{name:28s} mean P(keep) {sum(sc)/len(sc):.3f}  >=0.5: {sum(x >= 0.5 for x in sc)}/{len(sc)}")
sc = score(variants["as-is, no context"]); sc2 = score(variants["capitalized, no context"])
print("--- lowest as-is (with capitalized score):")
for x, y, s in sorted(zip(sc, sc2, sents))[:10]:
    print(f"  {x:.2f} -> cap {y:.2f} | {s[:90]}")
