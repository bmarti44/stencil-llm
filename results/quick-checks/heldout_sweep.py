import glob, json, os
os.environ["CUDA_VISIBLE_DEVICES"] = ""
import torch
from transformers import AutoTokenizer, AutoModel

R = "/home/bmarti44/stencil-llm/data/classifier"
clf = torch.load(R + "/model/clf.pt"); ROLES, LABELS = clf["roles"], clf["labels"]
head = torch.nn.Sequential(torch.nn.Linear(clf["in_dim"], 256), torch.nn.GELU(), torch.nn.Dropout(0.2), torch.nn.Linear(256, 3)) if clf.get("mlp") else torch.nn.Linear(clf["in_dim"], 3)
head.load_state_dict(clf["head"]); head.eval()
tk = AutoTokenizer.from_pretrained(clf["encoder"]); enc = AutoModel.from_pretrained(clf["encoder"]).eval()
rows = [json.loads(l) for p in glob.glob(R + "/heldout/*.jsonl") for l in open(p) if l.strip()]
rows = [o for o in rows if o.get("label") in LABELS and o.get("role") in ROLES]
T = [f"[{o['role']}] " + (o.get("context", "") + " ||| " if o.get("context") else "") + o["text"] for o in rows]
with torch.no_grad():
    X = []
    for i in range(0, len(T), 64):
        b = tk(T[i:i + 64], padding=True, truncation=True, max_length=256, return_tensors="pt")
        h = torch.nn.functional.normalize(enc(**b).last_hidden_state[:, 0], dim=-1)
        X.append(torch.cat([h, torch.tensor([[float(o["role"] == r) for r in ROLES] for o in rows[i:i + 64]])], 1))
    P = torch.softmax(head(torch.cat(X)), -1)
keep = P[:, LABELS.index("rule")] + P[:, LABELS.index("fact")]; y = torch.tensor([o["label"] != "none" for o in rows])
print("held-out n", len(rows), "positives", int(y.sum()))
for thr in (0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9):
    pred = keep >= thr; tp = int((pred & y).sum()); fp = int((pred & ~y).sum()); fn = int((~pred & y).sum())
    print(f"thr {thr:.1f}: keep-precision {tp/max(1,tp+fp):.3f} keep-recall {tp/max(1,tp+fn):.3f} none-recall {1-fp/max(1,int((~y).sum())):.3f} kept-frac {float(pred.float().mean()):.2f}")
