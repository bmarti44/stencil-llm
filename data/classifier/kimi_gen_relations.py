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
invent ONE target rule version (live, or inactive for reinstatement), ONE new role-labelled message, and ONE candidate
sentence span from that message; label the RELATION of that span to the target. Include the whole message as context.
The full label specification is below; follow it exactly. This pass emits pair rows only; message-only admission
rows (old_rule=null, label=null) are authored separately.

=== SPECIFICATION ===
{spec}
=== END SPECIFICATION ===

Output: JSON Lines only, no prose, no code fences. One object per line with fields:
"old_rule" (the target version's rule text, 3-25 words), "key" (short slug of what the rule governs, e.g. "ordering", "language",
"heading"), "scope" (one of "global" | "task:<short task name>" | "reply"), "status" ("live" | "superseded" | "cancelled" |
"completed"), "prev_user" (optional: the previous user turn, 0-30 words, when the relation depends on it),
"message" (the new message, 4-45 words, natural, varied, sometimes sloppy or indirect), "role" ("user" | "assistant" |
"tool"; only user authorizes updates), "target_span" (object with "start", "end" character offsets, end exclusive,
and "text": the exact candidate sentence in message), "label" (one of
{list(LABELS)}), "message_new_rule" (false unless a SEPARATE admitted span introduces a new durable key), "new_rule_spans"
(list of the verbatim admitted spans, empty when none), "domain": "{domain}", "hard" (true when the relation is subtle:
different task, reported speech, hypotheticals, partial overlap), "why" (3-12 words).
Requirements: domain = {domain}; exactly {n} objects; label mix roughly one-third none and one-sixth each supersedes,
cancels, completes, reinstates (2,000 none and 1,000 per positive label per 6,000 fit pairs). At least 40% of none
are HARD negatives that look like changes but are not: same-domain near-key compatible additions, quotes,
hypotheticals, tool/other-party claims, different subject/key, wrong task, continuations. Include compatible addition
on a live task (none + new-rule), and reinstates vs supersedes with a changed value. Mismatched scope means an update
for a DIFFERENT task; a narrower task update against a same-key global rule can supersede on the intersection.
Single-reply constraints are none for EVERY pair and for persistent admission; never create temporary exceptions.
Completes closes a whole named task only, never a sub-unit. On reinstatement the inactive target receives reinstates
and the live same-key target receives none; shadowing is derived. At least a third of target rules are task-scoped
and a third global, within valid label cells; reply-scoped targets supply negatives only. About a quarter of messages
carry message_new_rule=true, only with a separate admitted span. Vary the register (terse, chatty,
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

# Review disposition (2026-09-05, results/focus3-design-review-fable.md): L1 accepted
# (key/conflict semantics from runtime spec); L2 accepted (live reinstatement target
# is none); L3 accepted (wrong-task wording, reply negatives); L4 accepted (one-third
# none, >=40% hard, separate admission pass; held-out power and binding gate in spec);
# L6 accepted (development-only illustrations); L7 accepted (both hard cases).
# D1 accepted, D2 accepted, D4 accepted, D7 accepted and D8 accepted in the design;
# D3 accepted here too (candidate span against target version, including inactive).
# D5 accepted-with-change (task-resume warning retained, reply expiry cut in design);
# D6 accepted-with-change (no numbered D6 exists; review section 2 packaging applied
# in design). No L5 exists. Cuts accepted for one-reply mechanics and sub-unit
# completes; reinstates retained as Brian requested. No findings refuted.
