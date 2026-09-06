"""kimi-k3 ADMISSION pass (FOCUS-3): message-level standing-rule extraction data.

Usage: kimi_gen_admission.py <domain> <n> <seed> <out.jsonl>
Each row is a MESSAGE with its standing-rule spans (possibly none) and flags, in the same format as
data/classifier/heldout/fable-admission-heldout.jsonl (author-disjoint held-out; never copied). Hand-written by
kimi-k3 in a fresh session per call. Never any benchmark content; never the FOCUS-3 gate bank sentences.
Data lineage: fit-on (after review) for the admission detector; evaluated-on = fable-admission-heldout (untouched).
"""
import json
import pathlib
import re
import sys
import time
import urllib.request

domain, n, seed, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
labels = pathlib.Path(__file__).with_name("LABELS.md").read_text()
PROMPT = f"""You are hand-writing training data for a small detector inside an AI assistant. For each item you invent ONE
message in a conversation and mark which sentences (if any) state a STANDING RULE: a constraint that governs the
assistant's FUTURE outputs until it is changed ("from now on", "always", "never", "for this task keep ...", "until I say
otherwise", "must", "going forward", "whenever", or a bare durable constraint like "every reply ends with a summary").
Everything else is NOT a standing rule: one-off requests (even imperative ones), requests that carry DATA (lists, JSON,
CSV, YAML, code, logs, quoted text) to be processed now, single-reply constraints ("just this once", "for this reply"),
quoted or reported text that mentions a rule (samples, docs, logs, "the tool said", fiction, hypotheticals,
questions, hedged proposals), and anything said by a tool or the assistant. Background definitions:
=== LABELS ===
{labels[:3000]}
=== END ===
Output: JSON Lines only, no prose, no code fences. One object per line: "domain": "{domain}", "role" ("user" |
"tool" | "assistant"; only user messages can contain standing rules), "message" (1-4 sentences of natural prose; may
embed data/JSON/CSV/code/quotes), "standing_rules" (list of objects {{"text": exact verbatim span from the message,
"key": short slug of what it governs, "scope": "global" | "task:<short task name>"}}; empty list when none),
"one_off_request" (true if the message asks for work to be done now), "quoted_or_reported" (true if the message
contains quoted/reported/inert rule-like text), "hard" (true when the case is subtle), "why" (3-12 words).
Requirements: exactly {n} objects; PASS-3 EMPHASIS (measured miss families): ~40% standing rules WITHOUT any cue phrase (no "from now on/always/never/must/going forward" — bare durable constraints stated plainly, e.g. "Replies end with a summary line."), ~30% TWO or THREE rules in ONE sentence as a list (spans = the individual clauses), ~15% a rule plus a payload request, ~15% one-off/quoted negatives that contain cue words. Original mix guidance for reference: ~35% exactly one standing rule (vary phrasing widely; sometimes buried after
chit-chat or after a data payload), ~10% two standing rules, ~30% one-off requests WITH data payloads and NO rule
(make many of them contain the words always/never/must/sort/order INSIDE the data or the request without making a
rule), ~15% quoted/reported/inert rule-like text that is NOT an instruction, ~10% a standing rule AND a payload
request in the same message (span must be exactly the rule sentence). Vary register (terse, chatty, polite,
annoyed). Invent everything; do NOT copy or paraphrase any public benchmark or dataset. Variation seed: {seed}."""
body = json.dumps({"model": "kimi-k3:cloud", "prompt": PROMPT, "stream": False, "think": False,
                   "options": {"num_predict": 16000, "temperature": 0.9, "seed": seed}}).encode()
req = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=body,
                             headers={"Content-Type": "application/json"})
t0 = time.time()
for attempt in range(3):
    try:
        r = json.load(urllib.request.urlopen(req, timeout=3600))
        break
    except Exception as e:  # noqa: BLE001
        print("retry", attempt, e, file=sys.stderr)
        time.sleep(20)
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
    ok = (o and isinstance(o.get("message"), str) and isinstance(o.get("standing_rules"), list)
          and o.get("role") in ("user", "tool", "assistant"))
    if not ok:
        bad += 1
        continue
    spans = []
    for s in o["standing_rules"]:
        if not isinstance(s, dict) or not isinstance(s.get("text"), str):
            continue
        start = o["message"].find(s["text"])
        if start < 0:
            continue
        s["start"], s["end"] = start, start + len(s["text"])
        spans.append(s)
    o["standing_rules"] = spans
    o["domain"] = domain
    o["source"] = f"kimi-k3-admission:{domain}:{seed}"
    rows.append(o)
with open(out, "a") as f:
    for o in rows:
        f.write(json.dumps(o, ensure_ascii=False) + "\n")
print(f"{domain} seed={seed} rows={len(rows)} bad={bad} secs={time.time() - t0:.0f}")
