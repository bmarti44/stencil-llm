import glob, json, os, collections
os.environ["CUDA_VISIBLE_DEVICES"] = ""
import torch
from transformers import AutoTokenizer, AutoModel

print("system torch", torch.__version__, "cuda build:", torch.version.cuda, "| device count (masked):", torch.cuda.device_count())
R = "/home/bmarti44/stencil-llm/data/classifier"
clf = torch.load(R + "/model/clf.pt"); ROLES, LABELS = clf["roles"], clf["labels"]
head = torch.nn.Sequential(torch.nn.Linear(clf["in_dim"], 256), torch.nn.GELU(), torch.nn.Dropout(0.2), torch.nn.Linear(256, 3)) if clf.get("mlp") else torch.nn.Linear(clf["in_dim"], 3)
head.load_state_dict(clf["head"]); head.eval()
tk = AutoTokenizer.from_pretrained(clf["encoder"]); enc = AutoModel.from_pretrained(clf["encoder"]).eval()
rows = [json.loads(l) for l in open(R + "/heldout/fable-validation.jsonl") if l.strip()]
T = [f"[{o['role']}] " + (o.get("context", "") + " ||| " if o.get("context") else "") + o["text"] for o in rows]
with torch.no_grad():
    X = []
    for i in range(0, len(T), 64):
        b = tk(T[i:i + 64], padding=True, truncation=True, max_length=256, return_tensors="pt")
        h = torch.nn.functional.normalize(enc(**b).last_hidden_state[:, 0], dim=-1)
        X.append(torch.cat([h, torch.tensor([[float(o["role"] == r) for r in ROLES] for o in rows[i:i + 64]])], 1))
    P = torch.softmax(head(torch.cat(X)), -1)
pred = [LABELS[i] for i in P.argmax(1).tolist()]
conf = collections.Counter((o["label"], p) for o, p in zip(rows, pred))
print("confusion (true -> pred):", dict(conf))
for key in ("role", "hard"):
    groups = collections.defaultdict(lambda: [0, 0])
    for o, p in zip(rows, pred):
        g = groups[o[key]]; g[1] += 1; g[0] += int(p == o["label"])
    print(key, {k: f"{v[0]}/{v[1]}" for k, v in groups.items()})
ctx = [(o, p) for o, p in zip(rows, pred) if o.get("context")]
print("with-context acc %.2f (n=%d); without %.2f" % (sum(p == o["label"] for o, p in ctx) / max(1, len(ctx)), len(ctx), sum(p == o["label"] for o, p in zip(rows, pred) if not o.get("context")) / max(1, len(rows) - len(ctx))))
print("--- sample errors (true -> pred | text):")
n = 0
for o, p in zip(rows, pred):
    if p != o["label"] and n < 14:
        n += 1; print(f"  {o['label']} -> {p} | [{o['role']}] {o['text'][:110]}")
