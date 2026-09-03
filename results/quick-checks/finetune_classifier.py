"""Fine-tune bge-small-en-v1.5 end-to-end as a 3-way sentence(-pair) classifier: segment A = context (or empty),
segment B = "[role] text". Train = kimi + kimi-ctx + *-enrich with patches (item-level policy); validation =
heldout/* per source (never trained on). Saves to data/classifier/model/ft/. Never reads data/bench.
Usage: python3 finetune_classifier.py [epochs] [device]"""
import glob, json, os, sys, time, random
import torch
from transformers import AutoTokenizer, AutoModel

EPOCHS = int(sys.argv[1]) if len(sys.argv) > 1 else 3
DEV = sys.argv[2] if len(sys.argv) > 2 else ("cuda" if torch.cuda.is_available() else "cpu")
ROOT = "/home/bmarti44/stencil-llm/data/classifier"
LABELS = ["none", "rule", "fact"]; ROLES = ["user", "assistant", "tool", "system"]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def load(paths):
    rows = []
    for p in paths:
        for ln in open(p):
            if ln.strip():
                o = json.loads(ln)
                if o.get("label") in LABELS and o.get("role") in ROLES and isinstance(o.get("text"), str):
                    rows.append(o)
    return rows


train = load(sorted(glob.glob(f"{ROOT}/kimi/*.jsonl") + glob.glob(f"{ROOT}/kimi-ctx/*.jsonl") + glob.glob(f"{ROOT}/*-enrich.jsonl")))
patches = {}; skipped = 0
for p in glob.glob(f"{ROOT}/review/*-patch.jsonl"):
    for ln in open(p):
        if ln.strip():
            o = json.loads(ln); reason = (o.get("reason") or "").lower()
            if o.get("drop") and ("mirrors bench" in reason or "benchmark-taxonomy" in reason):
                skipped += 1; continue
            patches[(o.get("source"), o.get("text"))] = o
import re
fixed = []
for o in train:
    pt = patches.get((o.get("source"), o["text"]))
    if pt:
        if pt.get("drop"):
            continue
        if pt.get("new_label") in LABELS: o["label"] = pt["new_label"]
        if pt.get("new_role") in ROLES: o["role"] = pt["new_role"]
    if "context" in o:
        o["text"] = re.sub(r"^(?:user|assistant|tool|system)\s*:\s*", "", o["text"].strip(), flags=re.I)
        ctx = (o.get("context") or "").strip(); core = re.sub(r"^(?:user|assistant|tool|system)\s*:\s*", "", ctx, flags=re.I)
        if not ctx or core.strip().lower() == o["text"].strip().lower():
            o["context"] = ""
    fixed.append(o)
seen = set(); train = [o for o in fixed if not ((o["text"].strip().lower(), o["label"], o["role"]) in seen or seen.add((o["text"].strip().lower(), o["label"], o["role"])))]
heldout = load(sorted(glob.glob(f"{ROOT}/heldout/*.jsonl")))
print(f"train {len(train)} (taxonomy-category drops not applied: {skipped}); heldout {len(heldout)}; device {DEV}", flush=True)

name = "BAAI/bge-small-en-v1.5"
tk = AutoTokenizer.from_pretrained(name)
enc = AutoModel.from_pretrained(name)


class Clf(torch.nn.Module):
    def __init__(self):
        super().__init__(); self.enc = enc; self.head = torch.nn.Sequential(torch.nn.Dropout(0.1), torch.nn.Linear(enc.config.hidden_size + len(ROLES), 3))

    def forward(self, batch, roles):
        h = self.enc(**batch).last_hidden_state[:, 0]
        return self.head(torch.cat([h, roles], 1))


def batches(rows, bs, shuffle):
    idx = list(range(len(rows)))
    if shuffle: random.shuffle(idx)
    for i in range(0, len(idx), bs):
        chunk = [rows[j] for j in idx[i:i + bs]]
        a = [(o.get("context") or "") for o in chunk]; b = [f"[{o['role']}] {o['text']}" for o in chunk]
        # pair encoding: context (may be empty) as segment A, target as segment B
        t = tk([x if x else "(no context)" for x in a], b, padding=True, truncation="only_first", max_length=192, return_tensors="pt")
        roles = torch.tensor([[float(o["role"] == r) for r in ROLES] for o in chunk])
        y = torch.tensor([LABELS.index(o["label"]) for o in chunk])
        yield {k: v.to(DEV) for k, v in t.items()}, roles.to(DEV), y.to(DEV), chunk


torch.manual_seed(0); random.seed(0)
model = Clf().to(DEV)
opt = torch.optim.AdamW(model.parameters(), lr=3e-5, weight_decay=0.01)
steps = EPOCHS * ((len(train) + 31) // 32); sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / (0.06 * steps)) * max(0.0, (steps - s) / steps))


def evaluate(rows, tag):
    model.eval(); preds = []
    with torch.no_grad():
        for b, r, y, chunk in batches(rows, 64, False):
            preds += model(b, r).argmax(1).tolist()
    model.train()
    res = {"n": len(rows), "acc": sum(p == LABELS.index(o["label"]) for p, o in zip(preds, rows)) / len(rows), "per_source": {}, "per_class": {}}
    for s in sorted({(o.get("source") or "").split(":")[0] for o in rows}):
        ii = [i for i, o in enumerate(rows) if (o.get("source") or "").split(":")[0] == s]
        res["per_source"][s] = {"n": len(ii), "acc": sum(preds[i] == LABELS.index(rows[i]["label"]) for i in ii) / len(ii)}
    for k, lab in enumerate(LABELS):
        tp = sum(1 for p, o in zip(preds, rows) if p == k and o["label"] == lab); fp = sum(1 for p, o in zip(preds, rows) if p == k and o["label"] != lab); fn = sum(1 for p, o in zip(preds, rows) if p != k and o["label"] == lab)
        res["per_class"][lab] = {"precision": tp / max(1, tp + fp), "recall": tp / max(1, tp + fn)}
    hard = [i for i, o in enumerate(rows) if o.get("hard") is True]
    if hard: res["hard_acc"] = sum(preds[i] == LABELS.index(rows[i]["label"]) for i in hard) / len(hard)
    print(tag, json.dumps(res)[:900], flush=True); return res


t0 = time.time(); step = 0
for ep in range(EPOCHS):
    tot = 0.0; n = 0
    for b, r, y, _ in batches(train, 32, True):
        loss = torch.nn.functional.cross_entropy(model(b, r), y)
        opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step(); sched.step(); step += 1
        tot += float(loss) * len(y); n += len(y)
    print(f"epoch {ep+1}/{EPOCHS} loss {tot/n:.4f} elapsed {time.time()-t0:.0f}s", flush=True)
    metrics = evaluate(heldout, f"HELDOUT ep{ep+1}")
os.makedirs(f"{ROOT}/model/ft", exist_ok=True)
model.cpu(); model.enc.save_pretrained(f"{ROOT}/model/ft/encoder"); tk.save_pretrained(f"{ROOT}/model/ft/encoder")
torch.save({"head": model.head.state_dict(), "labels": LABELS, "roles": ROLES, "hidden": enc.config.hidden_size}, f"{ROOT}/model/ft/head.pt")
json.dump({"heldout": metrics, "epochs": EPOCHS, "train_n": len(train)}, open(f"{ROOT}/model/ft/metrics.json", "w"), indent=1)
print("saved", f"{ROOT}/model/ft", flush=True)
