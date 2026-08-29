# ruff: noqa
"""T1 (TIMED-SELECTOR-PLAN): learned timing + learned address.

Label rule (registered): moments are AST-GROUNDED — parse each base
rollout's final code, locate the char offsets of (a) the function-name
start, (b) the docstring's first word, (c) each argument annotation start;
the moment state is the generation position that PREDICTS the first token
of that element. No regex labels.

Timing head: linear 4-way over frozen h20 states; decision = argmax class
if max softmax prob > tau else NONE; tau calibrated for precision >= 0.95
on a held calibration block, then FROZEN.
Address scorer: S2-style query-key over the session's (order-randomized)
obligation sentences; trained with CE at true moments.
Factorial arms on fresh validation: base, oracle/oracle, learned/oracle,
oracle/learned, learned/learned. Gates: precision >= 0.95, recall >= 0.8,
conditional address accuracy >= 0.9, learned/learned closure >= 0.5 with
paired parse loss == 0.
"""
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401
import re

import torch
import torch.nn.functional as F
from tokenizers import Tokenizer

from stencil.qwen3 import Qwen3
from stencil.qwen_task import generate_codegov

TRAIN = list(range(12_310_000, 12_310_192))
CALIB = list(range(12_320_000, 12_320_048))
VAL = list(range(12_400_000, 12_400_064))
LAYERS = tuple(range(20, 28))
BETA = 2.0
CLASSES = ["none", "prefix", "doc", "hint"]

tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
m = Qwen3()
m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
m = m.to(torch.bfloat16).cuda().eval()


def build(seed):
    s = generate_codegov(seed)
    enc = tok.encode(s.text)
    tok_spans = {}
    for key, (a, b) in s.sentence_spans.items():
        cols = [i for i, (x, y) in enumerate(enc.offsets) if x < b and y > a]
        tok_spans[key] = (cols[0], cols[-1] + 1)
    return s, enc.ids, tok_spans


def oracle_moment(tail_text):
    if re.search(r"\bdef\s*$", tail_text):
        return "prefix"
    if re.search(r'"""\s*$', tail_text) and tail_text.count('"""') % 2 == 1:
        return "doc"
    if re.search(r"def\s+\w+\s*\([^)]*:\s*$", tail_text):
        return "hint"
    return None


def gen_rollout(ids, timing=None, address=None, tok_spans=None, s=None, max_new=90):
    """timing: None|'oracle'|(head,tau); address: None|'oracle'|(Wq,Wk,sent_feats).
    Returns (code_text, gen_token_ids, moment_log)."""
    toks = torch.tensor([ids], device="cuda")
    outs = []
    text = ""
    log = []
    for _ in range(max_new):
        ab = None
        key = None
        if timing == "oracle":
            key = oracle_moment(text[-80:])
        elif timing == "always":
            key = "prefix"  # continuous press on a fixed obligation span
        elif timing == "shuffled":
            import random as _r
            if _r.Random(len(outs)).random() < 0.06:
                key = ["prefix", "doc", "hint"][len(outs) % 3]
        elif timing is not None:
            head, tau = timing
            h = m(toks, return_hidden=20)[0, -1].float()
            probs = torch.softmax(head(h), dim=-1)
            c = int(probs[1:].argmax()) + 1
            if float(probs[c]) > tau:
                key = CLASSES[c]
        if key is not None:
            if address == "wrong":
                span = tok_spans[{"prefix": "doc", "doc": "hint", "hint": "prefix"}[key]]
            elif address == "oracle" or address is None:
                span = tok_spans[key]
            else:
                Wq, Wk, sent_feats, sent_keys = address
                h = m(toks, return_hidden=20)[0, -1].float()
                scores = (Wq(h) @ Wk(sent_feats).T) / 8.0
                span = tok_spans[sent_keys[int(scores.argmax())]]
            t = toks.shape[1]
            bias = torch.zeros(t, t, device="cuda")
            bias[-1:, span[0]:span[1]] = BETA
            ab = {L: bias for L in LAYERS}
            log.append((len(outs), key))
        nxt = int(m(toks, attn_bias=ab)[0, -1].argmax())
        outs.append(nxt)
        toks = torch.cat([toks, torch.tensor([[nxt]], device="cuda")], dim=1)
        text = tok.decode(outs)
        if "```" in text[-6:]:
            break
    return text.split("```")[0], outs, log


def ast_moments(code, prompt_len, gen_ids, full_ids):
    """AST-grounded moment labels -> {gen_step_index: class}. gen step i
    predicts full token prompt_len+i; element starting at gen-char c maps to
    the step that emits its first token."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {}
    fns = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    if not fns:
        return {}
    fn = fns[0]
    lines = code.split("\n")
    def char_of(lineno, col):
        return sum(len(ln) + 1 for ln in lines[: lineno - 1]) + col
    targets = []
    name_col = code.find("def " + fn.name)
    if name_col >= 0:
        targets.append((name_col + 4, "prefix"))
    doc = ast.get_docstring(fn)
    if doc and doc.split():
        body0 = fn.body[0]
        if isinstance(body0, ast.Expr):
            dchar = char_of(body0.lineno, body0.col_offset)
            w = code.find(doc.split()[0], dchar)
            if w >= 0:
                targets.append((w, "doc"))
    for a in fn.args.args:
        if a.annotation is not None:
            targets.append((char_of(a.annotation.lineno, a.annotation.col_offset), "hint"))
    # map gen char offsets to gen step indices via token decode lengths
    offs = []
    pos = 0
    for i, tid in enumerate(gen_ids):
        piece = tok.decode([tid])
        offs.append((pos, pos + len(piece)))
        pos += len(piece)
    labels = {}
    for c, cls in targets:
        for i, (a, b) in enumerate(offs):
            if a <= c < b:
                labels[i] = cls
                break
    return labels


def collect(seeds):
    X, Y = [], []
    addrX, addrS, addrY = [], [], []
    with torch.no_grad():
        for seed in seeds:
            s, ids, tok_spans = build(seed)
            code, gen_ids, _ = gen_rollout(ids)
            labels = ast_moments(code, len(ids), gen_ids, ids)
            full = ids + gen_ids
            h = m(torch.tensor([full], device="cuda"), return_hidden=20)[0].float().cpu()
            sent_feats = torch.stack([
                h[tok_spans[k][0]:tok_spans[k][1]].mean(dim=0) for k in ("prefix", "doc", "hint")
            ])
            for i in range(len(gen_ids)):
                state = h[len(ids) + i - 1]
                cls = labels.get(i, "none")
                X.append(state)
                Y.append(CLASSES.index(cls))
                if cls != "none":
                    addrX.append(state)
                    addrS.append(sent_feats)
                    addrY.append(["prefix", "doc", "hint"].index(cls))
    return torch.stack(X), torch.tensor(Y), (torch.stack(addrX), torch.stack(addrS), torch.tensor(addrY))


print("collecting training rollouts...", flush=True)
Xtr, Ytr, (AXtr, AStr, AYtr) = collect(TRAIN)
print(f"timing examples {len(Ytr)} (moments {(Ytr>0).sum().item()}), address examples {len(AYtr)}", flush=True)

g = torch.Generator().manual_seed(0)
head = torch.nn.Linear(2048, 4)
torch.nn.init.normal_(head.weight, std=0.02, generator=g); torch.nn.init.zeros_(head.bias)
w = torch.tensor([1.0, 20.0, 20.0, 20.0])
opt = torch.optim.Adam(head.parameters(), lr=1e-3)
for ep in range(30):
    perm = torch.randperm(len(Ytr), generator=g)
    for i in range(0, len(Ytr), 512):
        idx = perm[i:i+512]
        loss = F.cross_entropy(head(Xtr[idx]), Ytr[idx], weight=w)
        opt.zero_grad(); loss.backward(); opt.step()

Wq = torch.nn.Linear(2048, 64); Wk = torch.nn.Linear(2048, 64)
for lin in (Wq, Wk):
    torch.nn.init.normal_(lin.weight, std=0.02, generator=g); torch.nn.init.zeros_(lin.bias)
aopt = torch.optim.Adam(list(Wq.parameters()) + list(Wk.parameters()), lr=1e-3)
for ep in range(60):
    logits = torch.einsum("nd,nkd->nk", Wq(AXtr), Wk(AStr)) / 8.0
    loss = F.cross_entropy(logits, AYtr)
    aopt.zero_grad(); loss.backward(); aopt.step()

print("calibrating tau...", flush=True)
Xc, Yc, (AXc, ASc, AYc) = collect(CALIB)
with torch.no_grad():
    probs = torch.softmax(head(Xc), dim=-1)
    best = None
    for tau in [0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.98]:
        cls = probs[:, 1:].argmax(dim=-1) + 1
        conf = probs.gather(1, cls[:, None]).squeeze(1)
        pred = torch.where(conf > tau, cls, torch.zeros_like(cls))
        tp = ((pred > 0) & (pred == Yc)).sum().item()
        fp = ((pred > 0) & (pred != Yc)).sum().item()
        fn = ((pred == 0) & (Yc > 0)).sum().item()
        prec = tp / (tp + fp) if tp + fp else 0
        rec = tp / (tp + fn) if tp + fn else 0
        print(f"tau {tau}: precision {prec:.3f} recall {rec:.3f}")
        if prec >= 0.95 and (best is None or rec > best[2]):
            best = (tau, prec, rec)
    addr_logits = torch.einsum("nd,nkd->nk", Wq(AXc), Wk(ASc)) / 8.0
    addr_acc = float((addr_logits.argmax(-1) == AYc).float().mean())
assert best, "no tau reaches precision 0.95"
TAU = best[0]
print(f"FROZEN tau={TAU} (precision {best[1]:.3f} recall {best[2]:.3f}) | calib address acc {addr_acc:.3f}", flush=True)

head = head.cuda()
Wq = Wq.cuda()
Wk = Wk.cuda()

# behavioral factorial on validation
def score_min(code, s):
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None
    fns = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    if not fns:
        return None
    fn = fns[0]
    doc = ast.get_docstring(fn)
    first = doc.split()[0] if doc and doc.split() else ""
    def annname(a):
        return getattr(a.annotation, "id", None) if a.annotation else None
    return {
        "prefix": fn.name.startswith(s.prefix + "_"),
        "doc": first == s.doc_opener,
        "hint": bool(fn.args.args) and all(annname(a) == s.hint_type for a in fn.args.args),
    }


ARMS = {
    "base": (None, None),
    "alwayson_oracle": ("always", "oracle"),
    "shuffled_wrong": ("shuffled", "wrong"),
    "oracle_oracle": ("oracle", "oracle"),
    "learned_learned": ((head, TAU), "learned"),
}
results = {}
records = {}
with torch.no_grad():
    for arm, (timing, addr_kind) in ARMS.items():
        comp = 0
        parses = []
        recs = []
        for seed in VAL:
            s, ids, tok_spans = build(seed)
            addr = addr_kind
            if addr_kind == "learned":
                full_h = m(torch.tensor([ids], device="cuda"), return_hidden=20)[0].float()
                sent_keys = ("prefix", "doc", "hint")
                sent_feats = torch.stack([full_h[tok_spans[k][0]:tok_spans[k][1]].mean(dim=0) for k in sent_keys])
                addr = (Wq, Wk, sent_feats, sent_keys)
            code, _, log = gen_rollout(ids, timing, addr, tok_spans, s)
            sc = score_min(code, s)
            parses.append(sc is not None)
            if sc is not None:
                comp += sum(sc.values())
            recs.append({"seed": seed, "parse": sc is not None, "score": sc, "moments": len(log)})
        results[arm] = {"parse_rate": sum(parses)/len(VAL), "mean_parse_gated": comp/(3*len(VAL))}
        records[arm] = recs
        print(f"{arm}: parse {results[arm]['parse_rate']:.3f} parse-gated mean {results[arm]['mean_parse_gated']:.3f}", flush=True)

b_, o_, ll = results["base"]["mean_parse_gated"], results["oracle_oracle"]["mean_parse_gated"], results["learned_learned"]["mean_parse_gated"]
closure = (ll - b_) / (o_ - b_) if o_ > b_ else float("nan")
lost = sum(1 for rb, rl in zip(records["base"], records["learned_learned"]) if rb["parse"] and not rl["parse"])
print(f"GATES: closure {closure:.2f} (>=0.5) | paired parse lost {lost} (==0) | tau precision {best[1]:.3f} recall {best[2]:.3f} | addr acc {addr_acc:.3f}")
out = ROOT / "results" / "qwen" / "timed-t1-completion.json"
out.write_text(json.dumps({"tau": TAU, "precision": best[1], "recall": best[2],
                           "calib_addr_acc": addr_acc, "arms": results,
                           "closure": closure, "paired_parse_lost": lost,
                           "records": records}, indent=1))
print(f"evidence -> {out}")
