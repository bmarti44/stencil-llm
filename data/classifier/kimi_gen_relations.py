"""kimi-k3 relation pass (FOCUS-3, data/classifier/LABELS-RELATIONS.md).

Usage: kimi_gen_relations.py <domain> <n> <seed> <out.jsonl>
Hand-written by kimi-k3 in a fresh session per call; the label spec is read from LABELS-RELATIONS.md at run time so
the prompt always follows the committed spec. Never any benchmark content. Data lineage: fit-on = these rows (after
review patches); evaluated-on = author-disjoint held-out (separate pass); disjoint from every benchmark.
"""
import json
import pathlib
import re
import sys
import time
import urllib.request

domain, n, seed, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
SPEC_FILE = pathlib.Path(__file__).with_name("LABELS-RELATIONS.md")
spec = SPEC_FILE.read_text()
LABELS = ("none", "supersedes", "cancels", "completes", "reinstates")
PROMPT = f"""You are hand-writing training data for a small PAIRWISE classifier inside an AI assistant. For each item you
invent ONE live rule the assistant is currently following and ONE new user message, and you label the RELATION of the
message to that rule. The full label specification is below; follow it exactly.

=== SPECIFICATION ===
{spec}
=== END SPECIFICATION ===

Output: JSON Lines only, no prose, no code fences. One object per line with fields:
"old_rule" (the live rule text, 3-25 words), "key" (short slug of what the rule governs, e.g. "ordering", "language",
"heading"), "scope" (one of "global" | "task:<short task name>" | "reply"), "status" ("live" | "superseded" | "cancelled" |
"completed"), "prev_user" (optional: the previous user turn, 0-30 words, when the relation depends on it),
"message" (the new user message, 4-45 words, natural, varied, sometimes sloppy or indirect), "label" (one of
{list(LABELS)}), "message_new_rule" (true when the message ALSO introduces a new durable rule), "new_rule_spans"
(list of the verbatim admitted spans, empty when none), "domain": "{domain}", "hard" (true when the relation is subtle:
mismatched scope, reported speech, hypotheticals, partial overlap), "why" (3-12 words).
Requirements: domain = {domain}; exactly {n} objects; label mix roughly 40% none (at least half of them HARD negatives
that look like changes but are not: quotes, hypotheticals, tool/other-party claims, different key, different task,
continuations), 25% supersedes, 15% cancels, 10% completes, 10% reinstates; at least a third of the rules task-scoped
and a third global; about a quarter of messages carry message_new_rule=true. Vary the register (terse, chatty,
polite, annoyed). Invent everything; do NOT copy or paraphrase any public benchmark or dataset. Variation seed: {seed}."""
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
    ok = (o and o.get("label") in LABELS and isinstance(o.get("old_rule"), str)
          and isinstance(o.get("message"), str) and isinstance(o.get("scope"), str))
    if not ok:
        bad += 1
        continue
    o["domain"] = domain
    o["source"] = f"kimi-k3-relations:{domain}:{seed}"
    o.setdefault("message_new_rule", False)
    o.setdefault("new_rule_spans", [])
    rows.append(o)
with open(out, "a") as f:
    for o in rows:
        f.write(json.dumps(o, ensure_ascii=False) + "\n")
print(f"{domain} seed={seed} rows={len(rows)} bad={bad} secs={time.time() - t0:.0f}")
