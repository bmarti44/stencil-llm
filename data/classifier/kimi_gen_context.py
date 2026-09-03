"""kimi-k3 second pass: examples WITH preceding context, plus rule changes/expiries and supersession.
Usage: kimi_gen_context.py <domain> <n> <seed> <out.jsonl>"""
import json, re, sys, time, urllib.request

domain, n, seed, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
SPEC = f"""You are writing training data for a small classifier that decides, for ONE sentence in a conversation with an AI
assistant, whether the assistant must REMEMBER it for later turns. This pass focuses on sentences whose meaning
depends on what came just before, and on rules that CHANGE.

Labels (exactly one): "rule" = standing instruction/constraint/preference/persona/commitment governing FUTURE replies
(including a sentence that CHANGES or CANCELS an earlier rule, e.g. "Actually, drop the word limit." or "Forget what
I said about bullets, they're fine now."); "fact" = durable information needed later (ids, names, numbers, dates,
decisions, states), including corrections of earlier facts ("the meeting moved to Thursday"); "none" = one-off
requests, questions, chit-chat, assistant prose, tool output, acknowledgements, and rules that apply ONLY to the
current reply ("just for this one answer, use bullets" -> none).

Output: JSON Lines only, no prose, no code fences. Fields:
  "context": 1-3 preceding sentences from the same conversation (with speaker prefixes like "user:" / "assistant:" /
             "tool:"), needed to interpret the target sentence
  "text": the target sentence (4-40 words)
  "role": "user" | "assistant" | "tool" | "system"
  "label": "rule" | "fact" | "none"
  "domain": "{domain}"
  "hard": true if the label depends on the context or on subtle wording, else false
  "why": 3-12 words

Requirements: domain = {domain}; exactly {n} objects; roughly 35% rule, 25% fact, 40% none; at least 60% hard; include
anaphora ("Do that for all of them going forward."), rule cancellations and modifications, scope words ("this time",
"from now on", "until I say otherwise", "for the rest of this project"), facts that are corrected later, tool outputs
containing identifiers the user later relies on, and assistant sentences that restate or confirm a user's rule
(label "rule", role assistant). Do NOT copy or paraphrase any public benchmark; invent everything. Variation seed: {seed}."""
body = json.dumps({"model": "kimi-k3:cloud", "prompt": SPEC, "stream": False, "think": False,
                   "options": {"num_predict": 16000, "temperature": 0.9, "seed": seed}}).encode()
req = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=body, headers={"Content-Type": "application/json"})
t0 = time.time()
for attempt in range(3):
    try:
        r = json.load(urllib.request.urlopen(req, timeout=3600)); break
    except Exception as e:  # noqa: BLE001
        print("retry", attempt, e, file=sys.stderr); time.sleep(20)
else:
    sys.exit(2)
rows, bad = [], 0
for ln in r.get("response", "").splitlines():
    ln = ln.strip().strip("`")
    if not ln.startswith("{"):
        continue
    try:
        o = json.loads(ln)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", ln)
        try:
            o = json.loads(m.group(0)) if m else None
        except json.JSONDecodeError:
            o = None
    if not o or o.get("label") not in ("rule", "fact", "none") or not isinstance(o.get("text"), str) or o.get("role") not in ("user", "assistant", "tool", "system") or not isinstance(o.get("context"), str):
        bad += 1; continue
    o["domain"] = domain; o["source"] = f"kimi-k3-ctx:{domain}:{seed}"
    rows.append(o)
with open(out, "w") as f:
    for o in rows:
        f.write(json.dumps(o, ensure_ascii=False) + "\n")
print(f"[ctx] {domain} seed={seed}: {len(rows)} rows ({bad} rejected) in {time.time()-t0:.0f}s")
