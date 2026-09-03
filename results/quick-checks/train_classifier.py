"""Train the generic remember-me classifier (rule / fact / none) on hand-written data.

Features: bge-small-en-v1.5 CLS embedding of "[role] context ||| text" (context optional) + one-hot role.
Model: multinomial logistic regression (torch, CPU). Train = data/classifier/{kimi,kimi-ctx}/*.jsonl + *-enrich.jsonl
with review patches applied; validation = data/classifier/heldout/* (author-disjoint, never trained on).
Outputs: data/classifier/model/{clf.pt, metrics.json}. Never reads data/bench.
Usage: python3 train_classifier.py [--no-heldout-required]
"""
import glob, json, os, sys, time, hashlib
os.environ["CUDA_VISIBLE_DEVICES"] = ""
import torch
from transformers import AutoTokenizer, AutoModel

ROOT = "/home/bmarti44/stencil-llm/data/classifier"
LABELS = ["none", "rule", "fact"]; ROLES = ["user", "assistant", "tool", "system"]


def load(paths):
    rows = []
    for p in paths:
        for ln in open(p):
            ln = ln.strip()
            if ln:
                o = json.loads(ln)
                if o.get("label") in LABELS and o.get("role") in ROLES and isinstance(o.get("text"), str):
                    rows.append(o)
    return rows


train = load(sorted(glob.glob(f"{ROOT}/kimi/*.jsonl") + glob.glob(f"{ROOT}/kimi-ctx/*.jsonl") + glob.glob(f"{ROOT}/*-enrich.jsonl")))
patches = {}
for p in glob.glob(f"{ROOT}/review/*-patch.jsonl"):
    for ln in open(p):
        if ln.strip():
            o = json.loads(ln); patches[(o.get("source"), o.get("text"))] = o
dropped = relabelled = 0
fixed = []
for o in train:
    pt = patches.get((o.get("source"), o["text"]))
    if pt:
        if pt.get("drop"):
            dropped += 1; continue
        if pt.get("new_label") in LABELS:
            o["label"] = pt["new_label"]; relabelled += 1
    fixed.append(o)
train = fixed
# dedupe on text
seen = set(); train = [o for o in train if not (o["text"].strip().lower() in seen or seen.add(o["text"].strip().lower()))]
heldout = load(sorted(glob.glob(f"{ROOT}/heldout/*.jsonl")))
print(f"train {len(train)} (dropped {dropped}, relabelled {relabelled}); heldout {len(heldout)}")
if not heldout and "--no-heldout-required" not in sys.argv:
    sys.exit("no held-out set yet")

name = "BAAI/bge-small-en-v1.5"
tk = AutoTokenizer.from_pretrained(name); enc = AutoModel.from_pretrained(name).eval()


def texts(rows):
    return [f"[{o['role']}] " + (o.get("context", "") + " ||| " if o.get("context") else "") + o["text"] for o in rows]


@torch.no_grad()
def embed(rows, bs=64):
    out = []
    T = texts(rows)
    for i in range(0, len(T), bs):
        b = tk(T[i:i + bs], padding=True, truncation=True, max_length=256, return_tensors="pt")
        h = enc(**b).last_hidden_state[:, 0]
        out.append(torch.nn.functional.normalize(h, dim=-1))
    E = torch.cat(out)
    R = torch.tensor([[float(o["role"] == r) for r in ROLES] for o in rows])
    return torch.cat([E, R], 1)


t0 = time.time()
Xtr, Xho = embed(train), (embed(heldout) if heldout else None)
ytr = torch.tensor([LABELS.index(o["label"]) for o in train]); yho = torch.tensor([LABELS.index(o["label"]) for o in heldout]) if heldout else None
print(f"embedded in {time.time()-t0:.0f}s; dim {Xtr.shape[1]}")
torch.manual_seed(0)
W = torch.nn.Linear(Xtr.shape[1], 3)
opt = torch.optim.LBFGS(W.parameters(), lr=0.5, max_iter=300)
cw = torch.tensor([1.0, 1.0, 1.0])


def closure():
    opt.zero_grad()
    loss = torch.nn.functional.cross_entropy(W(Xtr), ytr, weight=cw) + 1e-3 * (W.weight ** 2).sum()
    loss.backward(); return loss


opt.step(closure)


def report(X, y, rows, tag):
    with torch.no_grad():
        p = W(X).argmax(1)
    acc = float((p == y).float().mean()); res = {"n": len(rows), "acc": acc, "per_class": {}, "per_source": {}}
    for k, lab in enumerate(LABELS):
        tp = int(((p == k) & (y == k)).sum()); fp = int(((p == k) & (y != k)).sum()); fn = int(((p != k) & (y == k)).sum())
        res["per_class"][lab] = {"precision": tp / max(1, tp + fp), "recall": tp / max(1, tp + fn), "n": int((y == k).sum())}
    srcs = sorted({(o.get("source") or "").split(":")[0] for o in rows})
    for s in srcs:
        idx = torch.tensor([i for i, o in enumerate(rows) if (o.get("source") or "").split(":")[0] == s])
        res["per_source"][s] = {"n": len(idx), "acc": float((p[idx] == y[idx]).float().mean())}
    hard = torch.tensor([i for i, o in enumerate(rows) if o.get("hard") is True])
    if len(hard):
        res["hard_acc"] = float((p[hard] == y[hard]).float().mean())
    print(tag, json.dumps(res, indent=None)[:1200])
    return res


metrics = {"train": report(Xtr, ytr, train, "TRAIN")}
if heldout:
    metrics["heldout"] = report(Xho, yho, heldout, "HELDOUT")
os.makedirs(f"{ROOT}/model", exist_ok=True)
torch.save({"weight": W.weight.detach(), "bias": W.bias.detach(), "labels": LABELS, "roles": ROLES, "encoder": name}, f"{ROOT}/model/clf.pt")
metrics["train_sha"] = hashlib.sha256("\n".join(sorted(o["text"] for o in train)).encode()).hexdigest()
json.dump(metrics, open(f"{ROOT}/model/metrics.json", "w"), indent=1)
print("saved", f"{ROOT}/model/clf.pt")
