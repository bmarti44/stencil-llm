"""[WRITE-TIME PER-TURN 4B EXTRACTION] THE MODEL AS ITS OWN SELECTOR (write-time extraction, read-time re-injection), on the 20 H1' sessions.

At the last turn, before answering, the SAME frozen 1.7B model is asked to list, verbatim, every instruction or
constraint from earlier in the conversation that still applies. Each listed line is matched back to a sentence
span of the prior history (token-overlap >= 0.5 or normalized substring). Those spans become the focus set:
pinned through eviction and echoed before the final user turn (the registered H1' pinned_echo mechanism), plus a
no-echo pinned arm and an exact-column control. No training, no lexicon, no benchmark-specific rule.
Compare with H1' recorded: full 44, evicted 14, finder pinned 37, finder pinned_echo 48, echo_only 37, control 18.
"""
import glob, json, re, sys, time
from pathlib import Path

ROOT = Path("/home/bmarti44/stencil-llm")
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts"))
import torch  # noqa: E402
import g0_oracle as G  # noqa: E402
import ledger_kv_probe as P  # noqa: E402
from stencil.causal_moments import score_row_constraints  # noqa: E402

model, tok = G.load_model()
from stencil.qwen3 import Qwen3, Qwen3Config, KVCache  # noqa: E402
CFG4 = Qwen3Config.from_hf(ROOT / "models/qwen3-4b-hf/config.json")
big = Qwen3(CFG4)
big.load_state_dict(torch.load(ROOT / "models/qwen3-4b.pt", map_location="cpu", weights_only=True), strict=True)
big = big.to(torch.bfloat16).cuda().eval()
END = tok.token_to_id("<|im_end|>")


def extract_4b(ctx_ids, max_new=256):
    cache = KVCache(CFG4); out = []
    with torch.no_grad():
        logits = big(torch.tensor([ctx_ids], device="cuda"), cache=cache)
        for _ in range(max_new):
            nxt = int(logits[0, -1].argmax())
            if nxt == END:
                break
            out.append(nxt)
            logits = big(torch.tensor([[nxt]], device="cuda"), cache=cache)
    return tok.decode(out, skip_special_tokens=True)

corpus = {r["key"]: r for r in (json.loads(l) for l in open(ROOT / "data/b3/mt-train-300.jsonl"))}
recs = [json.load(open(p)) for p in sorted(glob.glob(str(ROOT / "results/qwen/ledger-kv-probe-h1p/session-*.json")))]
ASK = ("Here is one message from a user:\n\n<<<\n{turn}\n>>>\n\nQuote verbatim, one per line and with no commentary, every "
       "sentence in this message that states an instruction, rule, or constraint the assistant must keep following in "
       "later replies. If there are none, reply: NONE.")


def words(s):
    return re.findall(r"[a-z0-9']+", s.lower())


def sentence_spans(enc, context, lo, hi):
    c0, c1 = enc.offsets[lo][0], enc.offsets[hi - 1][1]
    out = []
    for m in re.finditer(r"[^.!?\n]+[.!?]?", context[c0:c1]):
        a, b = c0 + m.start(), c0 + m.end()
        if len(re.findall(r"[A-Za-z]", m.group(0))) < 2:
            continue
        ts = P._token_span(enc, a, b)
        if ts:
            s, e = max(lo, ts[0]), min(hi, ts[1])
            if e > s:
                out.append((s, e, m.group(0).strip()))
    return out


def overlap(a, b):
    return max(0, min(a[1], b[1]) - max(a[0], b[0]))


tot = {"full": 0, "evicted": 0, "finder": 0, "finder_echo": 0, "echo_only": 0, "SELF_pinned": 0, "SELF_pinned_echo": 0, "SELF_control": 0, "n": 0}
cov = []; extras = []; rows = []; t0 = time.time()
for r in recs:
    ids = r["context_token_ids"]; lo, hi = r["evict_range"]
    context = tok.decode(ids, skip_special_tokens=False); enc = tok.encode(context); assert enc.ids == ids
    uturns = P._user_turns(context)
    # extraction prompt: everything before the last user turn, then the ASK
    lines = []
    for (a, b) in uturns[:-1]:  # WRITE-TIME: each prior user turn alone, at the time it arrived
        ask_ctx = f"<|im_start|>user\n{ASK.format(turn=context[a:b])}<|im_end|>\n" + P.OPENER
        text4 = extract_4b(tok.encode(ask_ctx).ids)
        lines += [re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", ln).strip().strip('"“”') for ln in text4.splitlines() if "NONE" not in ln]
    lines = [ln for ln in lines if len(words(ln)) >= 3]
    spans = sentence_spans(enc, context, lo, hi)
    matched = {}
    for ln in lines:
        lw = set(words(ln)); norm = " ".join(words(ln))
        best, bs = None, 0.0
        for s, e, txt in spans:
            sw = set(words(txt)); j = len(lw & sw) / max(1, len(lw | sw))
            if norm and norm in " ".join(words(txt)):
                j = max(j, 0.99)
            if j > bs:
                best, bs = (s, e), j
        if best and bs >= 0.5:
            matched[best] = max(matched.get(best, 0), bs)
    keep = sorted(matched)
    # origin turn for each span (1-based user turn containing its first token)
    def origin(s):
        ch = enc.offsets[s][0]
        for t, (a, b) in enumerate(uturns, start=1):
            if a <= ch < b:
                return t
        return 1
    aged = [{"span": (s, e), "origin_turn": origin(s)} for s, e in keep]
    keepc = [tuple(k) for k in r["keep"]]; Bk = sum(e - s for s, e in keepc)
    cov.append(sum(sum(overlap(c, s) for s in keep) for c in keepc) / Bk)
    extras.append(sum(1 for s in keep if not any(overlap(s, c) for c in keepc)))
    n_pin = len({i for a, b in keep for i in range(a, b)})
    sess = corpus[r["key"]]; last = sess["turns"][-1]
    row = {"key": int(sess["key"]) * 10 + r["n_turns"], "instruction_id_list": last["instruction_id_list"], "kwargs": last["kwargs"]}
    n_aged = r["n_aged"]; out = {}
    control = P.matched_control_spans(keep, (lo, hi)) if keep else []
    # drop spans the H1' echo renderer cannot clamp (reminder sentence / bare "Constraint" tail); keep the rest
    while aged:
        try:
            echoed, _, _ = P.echo_context(tok, context, aged); break
        except ValueError as err:
            bad = None
            for a in aged:
                try:
                    P.echo_context(tok, context, [a])
                except ValueError:
                    bad = a; break
            if bad is None:
                raise err
            aged = [a for a in aged if a is not bad]; keep = [k for k in keep if k != tuple(bad["span"])]
    if aged:
        echo_ids, echo_ev = P.tokenized_eviction_range(tok, echoed)
    else:
        echo_ids, echo_ev = ids, (lo, hi)
    for arm, arm_ids, ev, ck in (("pinned", ids, (lo, hi), ()), ("pinned_echo", echo_ids, echo_ev, ()), ("pinned_control", ids, (lo, hi), control)):
        gg = P.run_arm(model, tok, arm_ids, arm, keep, ev, 0.0, 512, 300.0, control_keep=ck)
        sc = list(score_row_constraints(row, gg["text"]))
        out[arm] = {"aged_pass": sum(sc[:n_aged]), "n": gg["n"], "truncated": gg.get("truncated"), "degenerate": P.is_degenerate(gg), "pinned_cols": gg.get("pinned_cols")}
    h = {a: r["arms"][a]["aged_pass"] for a in ("full", "evicted", "pinned", "pinned_echo", "echo_only", "pinned_control")}
    rows.append({"session": r["session"], "n_aged": n_aged, "extracted_lines": lines, "matched": keep, "n_pin": n_pin, "finder_cols": r["arms"]["pinned"]["pinned_cols"],
                 "coverage": cov[-1], "extras": extras[-1], "h1p": h, "SELF": out})
    tot["n"] += n_aged; tot["full"] += h["full"]; tot["evicted"] += h["evicted"]; tot["finder"] += h["pinned"]; tot["finder_echo"] += h["pinned_echo"]; tot["echo_only"] += h["echo_only"]
    tot["SELF_pinned"] += out["pinned"]["aged_pass"]; tot["SELF_pinned_echo"] += out["pinned_echo"]["aged_pass"]; tot["SELF_control"] += out["pinned_control"]["aged_pass"]
    print(f"s{r['session']:02d} aged={n_aged} lines={len(lines)} matched={len(keep)} cols={n_pin}(finder {r['arms']['pinned']['pinned_cols']}) cov={cov[-1]:.2f} extras={extras[-1]} | full={h['full']} finder={h['pinned']} finder_echo={h['pinned_echo']} | SELF pinned={out['pinned']['aged_pass']} echo={out['pinned_echo']['aged_pass']} (trunc={out['pinned_echo']['truncated']},degen={out['pinned_echo']['degenerate']}) ctrl={out['pinned_control']['aged_pass']}", flush=True)
print(f"elapsed {time.time()-t0:.0f}s")
print(f"COVERAGE mean {sum(cov)/len(cov):.3f} sessions>=0.8: {sum(c>=0.8 for c in cov)}/20  extras total {sum(extras)}")
print("TOTALS:", json.dumps(tot))
json.dump(rows, open(Path(__file__).with_name("self_extract_turn_rows.json"), "w"), indent=1)
