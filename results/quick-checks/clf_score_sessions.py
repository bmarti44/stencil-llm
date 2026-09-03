"""CPU (system python): score every sentence of every prior user turn in the 20 H1' sessions with the classifier.
Writes clf_scores.json: {session: [[char_a, char_b, prob_keep, turn], ...]} (char offsets in the decoded context)."""
import glob, json, os, re, sys
os.environ["CUDA_VISIBLE_DEVICES"] = ""
import torch
from tokenizers import Tokenizer
from transformers import AutoTokenizer, AutoModel
ROOT = "/home/bmarti44/stencil-llm"; S = sys.argv[1]
tok = Tokenizer.from_file(ROOT + "/models/qwen3-1.7b-hf/tokenizer.json")
clf = torch.load(ROOT + "/data/classifier/model/clf.pt")
etk = AutoTokenizer.from_pretrained(clf["encoder"]); enc_model = AutoModel.from_pretrained(clf["encoder"]).eval()
ROLES, LABELS = clf["roles"], clf["labels"]
def user_turns(context):
    marker = "<|im_start|>user\n"; out = []; cur = 0
    while True:
        i = context.find(marker, cur)
        if i < 0: return out
        s = i + len(marker); e = context.find("<|im_end|>", s); out.append((s, e)); cur = e + 1
@torch.no_grad()
def score(sents, role="user"):
    b = etk([f"[{role}] " + s for s in sents], padding=True, truncation=True, max_length=256, return_tensors="pt")
    h = torch.nn.functional.normalize(enc_model(**b).last_hidden_state[:, 0], dim=-1)
    R = torch.tensor([[float(role == r) for r in ROLES]] * len(sents))
    p = torch.softmax(torch.cat([h, R], 1) @ clf["weight"].T + clf["bias"], -1)
    return (p[:, LABELS.index("rule")] + p[:, LABELS.index("fact")]).tolist()
out = {}
for p in sorted(glob.glob(ROOT + "/results/qwen/ledger-kv-probe-h1p/session-*.json")):
    r = json.load(open(p)); context = tok.decode(r["context_token_ids"], skip_special_tokens=False)
    rows = []
    for t, (a, b) in enumerate(user_turns(context)[:-1], start=1):
        sents = [(a + m.start(), a + m.end(), m.group(0).strip()) for m in re.finditer(r"[^.!?\n]+[.!?]?", context[a:b]) if len(re.findall(r"[A-Za-z]", m.group(0))) >= 2]
        if sents:
            for (ca, cb, _), pr in zip(sents, score([s[2] for s in sents])):
                rows.append([ca, cb, pr, t])
    out[str(r["session"])] = rows
json.dump(out, open(S + "/clf_scores.json", "w")); print("scored", sum(len(v) for v in out.values()), "sentences")
