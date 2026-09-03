"""kimi-k3 third pass: the SCOPE distinction (LABELS.md v2). Usage: kimi_gen_scope.py <domain> <n> <seed> <out.jsonl>"""
import json, re, sys, time, urllib.request

domain, n, seed, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
SPEC = f"""You are writing training data for a small classifier that decides, for ONE sentence from a conversation with an AI
assistant, whether the assistant must REMEMBER it for later turns. This pass is entirely about SCOPE.

Labels (exactly one):
- "rule": (1) conversation-scoped instructions ("from now on", "always", "never", "whenever"), AND (2) TASK-scoped
  constraints — a constraint on HOW the piece of work in progress must be written or done (a document, code, a plan,
  a story, an email thread, a spreadsheet): "keep the whole thing short", "no bullet points", "open with a one-line
  heading", "use tabs in this file", "end every section with a question", "write it in the second person",
  "cite two sources", "use British spelling in this report". (Exemplars rewritten 2026-09-03 after fable's check-22
  review F3: the earlier version carried specifics lifted from the dev probe; rows echoing them are dropped.) These are rules because they PERSIST while the same
  work continues in later turns ("now extend it", "revise the piece", "add a closing section", "fix the next
  function") — even when the sentence does not say "from now on". Also rule changes/cancellations.
- "fact": durable information needed later (ids, names, numbers, dates, decisions, states).
- "none": a request to DO a piece of work ("Write a short account of X.", "Summarize this.", "Now add a closing
  section.", "Fix the failing test."), questions, chit-chat, assistant prose, tool output, acknowledgements, AND
  constraints EXPLICITLY scoped to a single reply ("just for this one answer, use bullets", "this time only, keep it
  short", "for this message, reply in French").
The hard line: "Keep this summary under 100 words." (constraint on the work) = rule; "Summarize this in under 100
words." can go either way — treat the constraint clause as rule when it is a separate sentence, and the whole
sentence as rule when the constraint is its main content; "Just this once, keep it under 100 words." = none.

Output: JSON Lines only, no prose, no code fences. Fields: "text" (4-40 words, natural, varied, sometimes sloppy),
"role" (user|assistant|tool|system), "label", "domain": "{domain}", "hard" (true when the scope is subtle), "why"
(3-12 words). Optional "context": 1-2 preceding sentences with speaker prefixes when the scope depends on them.
Requirements: domain = {domain}; exactly {n} objects; roughly 45% rule (at least half of them TASK-scoped constraints
with NO scope words), 15% fact, 40% none (at least half of the none rows are one-off work requests or explicitly
single-reply constraints that look like rules). Include continuations ("now extend...", "revise...") as none. Do NOT
copy or paraphrase any public benchmark (IFEval, Multi-IF, BFCL, tau-bench); invent everything. Variation seed: {seed}."""
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
    if not o or o.get("label") not in ("rule", "fact", "none") or not isinstance(o.get("text"), str) or o.get("role") not in ("user", "assistant", "tool", "system"):
        bad += 1; continue
    o["domain"] = domain; o["source"] = f"kimi-k3-scope:{domain}:{seed}"
    rows.append(o)
with open(out, "w") as f:
    for o in rows:
        f.write(json.dumps(o, ensure_ascii=False) + "\n")
print(f"[scope] {domain} seed={seed}: {len(rows)} rows ({bad} rejected) in {time.time()-t0:.0f}s")
