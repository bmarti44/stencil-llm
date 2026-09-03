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
if clf.get("mlp"):
    head = torch.nn.Sequential(torch.nn.Linear(clf["in_dim"], 256), torch.nn.GELU(), torch.nn.Dropout(0.2), torch.nn.Linear(256, 3))
else:
    head = torch.nn.Linear(clf["in_dim"], 3)
head.load_state_dict(clf["head"]); head.eval()

def split_sentences(text):
    """Sentence spans that do not split inside quotes or after single-letter abbreviations (P.P.S.)."""
    out = []; start = 0; i = 0; n = len(text); sq = dq = False
    while i < n:
        ch = text[i]
        if ch == '"':
            dq = not dq
        elif ch == "'":
            if not sq and (i == 0 or not text[i-1].isalnum()):
                sq = True
            elif sq and (i + 1 >= n or not text[i+1].isalnum()):
                sq = False
        if ch in ".!?":
            abbrev = i >= 1 and text[i-1].isalpha() and text[i-1].isupper() and (i < 2 or not text[i-2].isalpha())
            j = i + 1
            while j < n and text[j] in ".!?":
                j += 1
            k = j; s2, d2 = sq, dq
            while k < n and text[k] in "\"')":
                if text[k] == '"': d2 = not d2
                elif text[k] == "'" and s2: s2 = False
                k += 1
            if not abbrev and not s2 and not d2 and (k >= n or text[k].isspace()):
                out.append((start, k)); sq, dq = s2, d2
                start = k
                while start < n and text[start].isspace():
                    start += 1
                i = start; continue
        i += 1
    if start < n:
        out.append((start, n))
    return [(a, b) for a, b in out if b > a and len(re.findall(r"[A-Za-z]", text[a:b])) >= 2]


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
    p = torch.softmax(head(torch.cat([h, R], 1)), -1)
    return (p[:, LABELS.index("rule")] + p[:, LABELS.index("fact")]).tolist()
out = {}
for p in sorted(glob.glob(ROOT + "/results/qwen/ledger-kv-probe-h1p/session-*.json")):
    r = json.load(open(p)); context = tok.decode(r["context_token_ids"], skip_special_tokens=False)
    rows = []
    for t, (a, b) in enumerate(user_turns(context)[:-1], start=1):
        sents = [(a + s, a + e, context[a + s:a + e].strip()) for s, e in split_sentences(context[a:b])]
        if sents:
            for (ca, cb, _), pr in zip(sents, score([s[2] for s in sents])):
                rows.append([ca, cb, pr, t])
    out[str(r["session"])] = rows
json.dump(out, open(S + "/clf_scores.json", "w")); print("scored", sum(len(v) for v in out.values()), "sentences")
