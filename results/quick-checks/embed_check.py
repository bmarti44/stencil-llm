"""CPU embedding-similarity retrieval check (bge-small-en-v1.5, cached): rank prior sentences by cosine similarity
to the current message; constraint-token coverage at the finder's budget on the 20 H1' sessions."""
import json, os, sys
os.environ["CUDA_VISIBLE_DEVICES"] = ""
import torch
from transformers import AutoTokenizer, AutoModel

S = sys.argv[1]
data = json.load(open(S + "/embed_inputs.json"))
name = "BAAI/bge-small-en-v1.5"
tk = AutoTokenizer.from_pretrained(name); m = AutoModel.from_pretrained(name).eval()


def emb(texts):
    with torch.no_grad():
        b = tk(texts, padding=True, truncation=True, max_length=256, return_tensors="pt")
        h = m(**b).last_hidden_state[:, 0]
        return torch.nn.functional.normalize(h, dim=-1)


def ov(a, b):
    return max(0, min(a[1], b[1]) - max(a[0], b[0]))


covs = {"embed": [], "embed+instr_query": []}
for d in data:
    spans = d["spans"]; E = emb([s[2] for s in spans]); keep = [tuple(k) for k in d["keep"]]
    Bk = sum(e - s for s, e in keep); B = d["budget"]
    for nm, q in (("embed", d["query"]), ("embed+instr_query", "Instructions, rules and constraints I must keep following when answering: " + d["query"])):
        qv = emb([q]); sc = (E @ qv.T).squeeze(1).tolist()
        got = 0; kept = []
        for i in sorted(range(len(spans)), key=lambda i: -sc[i]):
            s, e = spans[i][0], spans[i][1]
            if got + (e - s) >= B:
                kept.append((s, s + (B - got))); break
            kept.append((s, e)); got += e - s
        covs[nm].append(sum(sum(ov(k, x) for x in kept) for k in keep) / Bk)
for k, v in covs.items():
    print(f"{k:20s} constraint-token coverage at finder budget: mean {sum(v)/len(v):.3f}  sessions>=0.8: {sum(x>=0.8 for x in v)}/20   (BM25 0.369, attention 0.19-0.26, random 0.133)")
