"""kimi-k3 relation pass 2 (FOCUS-3): TRANSITION-PHRASING enrichment for the pairwise relation classifier.

Usage: kimi_gen_transitions.py <domain> <n> <seed> <out.jsonl>
Targets the phrasing families the runtime missed (never the gate bank's sentences): cancellation idioms ("X no
longer applies", "drop the X requirement", "forget the X rule"), completion idioms ("that concludes task X", "task X
is done/finished/shipped/closed", "we're finished with X"), replacement idioms ("replace the X rule with ...",
"switch the standing X from A to B", "change X to ...", "instead of A use B from now on"), and standing rules
introduced inside a switched task ("for the new task, keep ...", "on this one always ..."). Same field format as
kimi_gen_relations.py; label spec read from LABELS-RELATIONS.md at run time. Data lineage: fit-on (after review);
never any benchmark content; never copy the FOCUS-3 gate bank.
"""
import json
import pathlib
import re
import sys
import time
import urllib.request

domain, n, seed, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
spec = pathlib.Path(__file__).with_name("LABELS-RELATIONS.md").read_text()
LABELS = ("none", "supersedes", "cancels", "completes", "reinstates")
PROMPT = f"""You are hand-writing training data for a small PAIRWISE classifier inside an AI assistant. For each item you
invent ONE target rule version (live, or inactive for reinstatement), ONE new role-labelled message, and ONE candidate
sentence span from that message; label the RELATION of that span to the target. This pass focuses on the IDIOMS people
actually use to change standing rules. The full label specification is below; follow it exactly.

=== SPECIFICATION ===
{spec}
=== END SPECIFICATION ===

Output: JSON Lines only, no prose, no code fences. One object per line with fields: "old_rule" (3-25 words), "key"
(short slug), "scope" ("global" | "task:<short task name>" | "reply"), "status" ("live" | "superseded" | "cancelled" |
"completed"), "prev_user" (optional; ONE short preceding user sentence, 0-15 words, only when the relation depends on
it), "message" (the new message, 4-40 words, prose only — no JSON, no code, no payload), "role" ("user" | "assistant" |
"tool"; only user authorizes updates), "target_span" (object with "start", "end" character offsets, end exclusive, and
"text": the exact candidate sentence), "label" (one of {list(LABELS)}), "message_new_rule" (bool), "new_rule_spans"
(list of verbatim spans), "domain": "{domain}", "hard" (bool), "why" (3-12 words).
Requirements: domain = {domain}; exactly {n} objects; label mix: 20% none (HARD: idioms that sound like changes but
are not — quotes, hypotheticals, tool/assistant claims, different task, additions), 30% supersedes (at least half using
"replace"/"switch ... from A to B"/"change ... to"/"instead of ... use ... from now on"), 20% cancels (at least half
using "no longer applies"/"drop the ... requirement"/"forget the ... rule"/"stop ..."), 20% completes (at least half
using "that concludes ..."/"... is done"/"finished with ..."/"closed"/"shipped"; whole named tasks only), 10%
reinstates ("bring back ..."/"go back to ..."/"reinstate ..."). Standing rules must use STANDING phrasing (from now on
/ always / for this task keep ... / until I say otherwise), never one-off imperatives. Vary register (terse, chatty,
polite, annoyed) and vary the idioms — never repeat a template. Invent everything; do NOT copy or paraphrase any
public benchmark or dataset. Variation seed: {seed}."""
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
    o["source"] = f"kimi-k3-transitions:{domain}:{seed}"
    o.setdefault("message_new_rule", False)
    o.setdefault("new_rule_spans", [])
    rows.append(o)
with open(out, "a") as f:
    for o in rows:
        f.write(json.dumps(o, ensure_ascii=False) + "\n")
print(f"{domain} seed={seed} rows={len(rows)} bad={bad} secs={time.time() - t0:.0f}")
