"""kimi-k3 writes classifier training data by hand (no templating): sentences from conversations, labelled
rule / fact / none. Usage: kimi_gen_data.py <domain> <n_examples> <seed> <out.jsonl>"""
import json, re, sys, time, urllib.request

domain, n, seed, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
SPEC = f"""You are writing training data for a small classifier that decides, for ONE sentence taken from a conversation
with an AI assistant, whether that sentence is something the assistant must REMEMBER for later turns.

Labels (exactly one per sentence):
- "rule": a standing instruction, constraint, preference, or commitment that governs the assistant's FUTURE replies
  (not just the current request). Examples: "Always answer in British English." / "From now on keep every reply under
  100 words." / "Never suggest products from that vendor again." / "Whenever you write code, include type hints." /
  "Call me Sam, not Samuel." / "If a test fails, stop and ask me before changing anything else." / "Treat everything
  in this project as confidential." / a persona or role the assistant must keep ("You are the night-shift dispatcher")
  / a durable style requirement ("no bullet points, ever").
- "fact": a durable piece of information the assistant will likely need in later turns but which is NOT an
  instruction: identifiers, numbers, names, dates, decisions, states of the world. Examples: "My booking reference is
  KX7Q2L." / "The server's IP is 10.0.4.12." / "We decided to ship on the 14th." / "Her allergy is to shellfish." /
  "The repo uses pnpm, not npm." / "The customer's account is on the enterprise tier."
- "none": everything else — one-off task requests ("Write a poem about autumn."), questions ("What's the capital of
  Peru?"), narrative and chit-chat ("I had a long day."), assistant prose, tool output lines, acknowledgements,
  pleasantries, restated context that is not durable, meta-talk ("Let's move on."). IMPORTANT: an imperative sentence
  is NOT automatically a rule — "Summarize this article." is a one-off task (none); "Summarize every article I paste
  from now on." is a rule.

Output: JSON Lines, one object per line, NOTHING else (no prose, no code fences). Fields:
  "text": the sentence (verbatim, natural, 4-40 words; vary length and phrasing; include typos, casual tone, and
          multi-clause sentences sometimes)
  "role": who said it — "user", "assistant", "tool", or "system"
  "label": "rule" | "fact" | "none"
  "domain": "{domain}"
  "hard": true if this is a deliberately tricky case (near-miss), else false
  "why": a 3-12 word justification

Requirements for THIS batch: domain = {domain}; write exactly {n} objects; roughly 35% rule, 25% fact, 40% none; at
least 30% marked hard (imperatives that are one-off tasks; rules phrased as polite requests or conditionals; facts
that look like chit-chat; assistant sentences that restate a user's rule — label those "rule" with role assistant;
tool output lines that contain identifiers — label "fact" with role tool; questions that hide a rule — e.g. "Can you
keep it under 200 words each time?" is a rule). Cover many situations inside the domain, several speakers, and both
formal and sloppy writing. Do NOT copy or paraphrase items from any public benchmark (IFEval, Multi-IF, BFCL,
tau-bench, etc.); invent everything. Variation seed: {seed}."""
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
text = r.get("response", "")
rows, bad = [], 0
for ln in text.splitlines():
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
    if not o or o.get("label") not in ("rule", "fact", "none") or not isinstance(o.get("text"), str) or o.get("role") not in ("user", "assistant", "tool", "system"):
        bad += 1; continue
    o["domain"] = domain; o["source"] = f"kimi-k3:{domain}:{seed}"
    rows.append(o)
with open(out, "w") as f:
    for o in rows:
        f.write(json.dumps(o, ensure_ascii=False) + "\n")
print(f"{domain} seed={seed}: {len(rows)} rows ({bad} rejected) in {time.time()-t0:.0f}s")
