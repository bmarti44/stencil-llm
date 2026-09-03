"""CPU: score every sentence of every prior user turn in the 20 H1' sessions with the FINE-TUNED classifier
(pair input: preceding sentences of the same turn as context). Writes clf_scores.json for clf_probe_check.py."""
import glob, json, os, re, sys
os.environ["CUDA_VISIBLE_DEVICES"] = ""
import torch
from tokenizers import Tokenizer
from transformers import AutoTokenizer, AutoModel

ROOT = "/home/bmarti44/stencil-llm"; S = sys.argv[1]
tok = Tokenizer.from_file(ROOT + "/models/qwen3-1.7b-hf/tokenizer.json")
FT = ROOT + "/data/classifier/model/ft"
tk = AutoTokenizer.from_pretrained(FT + "/encoder"); enc = AutoModel.from_pretrained(FT + "/encoder").eval()
hd = torch.load(FT + "/head.pt"); ROLES, LABELS = hd["roles"], hd["labels"]
head = torch.nn.Sequential(torch.nn.Dropout(0.1), torch.nn.Linear(hd["hidden"] + len(ROLES), 3)); head.load_state_dict(hd["head"]); head.eval()
sys.path.insert(0, S)
from clf_score_sessions import split_sentences, user_turns  # noqa: E402  (same splitter as the frozen-encoder scorer)


@torch.no_grad()
def score(pairs, role="user"):
    t = tk([a if a else "(no context)" for a, _ in pairs], [f"[{role}] {b}" for _, b in pairs], padding=True, truncation="only_first", max_length=192, return_tensors="pt")
    h = enc(**t).last_hidden_state[:, 0]
    R = torch.tensor([[float(role == r) for r in ROLES]] * len(pairs))
    p = torch.softmax(head(torch.cat([h, R], 1)), -1)
    return (p[:, LABELS.index("rule")] + p[:, LABELS.index("fact")]).tolist()


out = {}
for p in sorted(glob.glob(ROOT + "/results/qwen/ledger-kv-probe-h1p/session-*.json")):
    r = json.load(open(p)); context = tok.decode(r["context_token_ids"], skip_special_tokens=False)
    rows = []
    for t, (a, b) in enumerate(user_turns(context)[:-1], start=1):
        sents = [(a + s, a + e, context[a + s:a + e].strip()) for s, e in split_sentences(context[a:b])]
        if not sents:
            continue
        pairs = []
        for i, (_, _, txt) in enumerate(sents):
            prev = " ".join("user: " + s[2] for s in sents[max(0, i - 2):i])
            pairs.append((prev, txt))
        for (ca, cb, _), pr in zip(sents, score(pairs)):
            rows.append([ca, cb, pr, t])
    out[str(r["session"])] = rows
json.dump(out, open(S + "/clf_scores.json", "w")); print("scored", sum(len(v) for v in out.values()), "sentences (fine-tuned)")
