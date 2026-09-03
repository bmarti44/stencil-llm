"""kimi-k3 relabel pass under LABELS.md v2: every existing training row labelled "none" is re-judged in batches of
80; rows that are TASK-scoped constraints on the work in progress become "rule". Writes a patch file
data/classifier/review/scope-v2-patch.jsonl ({"source","text","new_label":"rule","reason"}) — applied by the
trainer like the reviewer patches. Idempotent per batch (skips batches already in the patch)."""
import glob, json, sys, time, urllib.request

R = "/home/bmarti44/stencil-llm/data/classifier"
OUT = R + "/review/scope-v2-patch.jsonl"
rows = []
for p in sorted(glob.glob(R + "/kimi/*.jsonl") + glob.glob(R + "/kimi-ctx/*.jsonl") + glob.glob(R + "/*-enrich.jsonl") + glob.glob(R + "/heldout/*.jsonl")):
    for ln in open(p):
        if ln.strip():
            o = json.loads(ln)
            if o.get("label") == "none" and o.get("role") in ("user", "system", "assistant"):
                rows.append({"source": o.get("source"), "text": o["text"]})
done = set()
try:
    for ln in open(OUT):
        if ln.strip():
            o = json.loads(ln); done.add(o.get("batch"))
except FileNotFoundError:
    pass
print("none-rows to re-judge:", len(rows), "batches done:", len(done), flush=True)
SPEC = """Label spec v2 (SCOPE): a sentence is a "rule" if it is (1) a conversation-scoped instruction ("from now on",
"always", "never"), OR (2) a TASK-scoped constraint on HOW the piece of work in progress must be written or done —
e.g. "keep it under 90 words", "no bullet points", "begin with a title", "use tabs in this file", "write it in the
second person", "cite two sources", "end with a P.S." — because such constraints persist while the same work
continues in later turns even without scope words. It stays "none" if it is a request to DO work ("Write a short
account of X.", "Summarize this.", "Now add a closing section."), a question, chit-chat, prose, tool output, an
acknowledgement, or a constraint EXPLICITLY limited to one reply ("just this once", "this time only", "for this
message"). Ambiguous sentences that mix a task with a constraint ("Summarize this in under 100 words") count as
"rule" when the constraint is the main content, else "none".

Below are sentences currently labelled "none". Output ONLY the ids (one per line) of the sentences that must become
"rule" under spec v2. If none, output the single line NONE."""
with open(OUT, "a") as f:
    for bi in range(0, len(rows), 80):
        if bi in done:
            continue
        batch = rows[bi:bi + 80]
        listing = "\n".join(f"{i}\t{o['text']}" for i, o in enumerate(batch))
        body = json.dumps({"model": "kimi-k3:cloud", "prompt": SPEC + "\n\n" + listing, "stream": False, "think": False,
                           "options": {"num_predict": 2000, "temperature": 0.0}}).encode()
        req = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=body, headers={"Content-Type": "application/json"})
        for attempt in range(3):
            try:
                resp = json.load(urllib.request.urlopen(req, timeout=1200)).get("response", ""); break
            except Exception as e:  # noqa: BLE001
                print("retry", bi, attempt, e, file=sys.stderr); time.sleep(15); resp = ""
        ids = set()
        for ln in resp.splitlines():
            ln = ln.strip().split("\t")[0].strip(" .-*")
            if ln.isdigit():
                ids.add(int(ln))
        n = 0
        for i in sorted(ids):
            if 0 <= i < len(batch):
                f.write(json.dumps({"source": batch[i]["source"], "text": batch[i]["text"], "new_label": "rule", "reason": "spec v2: task-scoped constraint", "batch": bi}) + "\n"); n += 1
        if not ids:
            f.write(json.dumps({"batch": bi, "note": "no flips"}) + "\n")
        f.flush()
        print(f"batch {bi}: {n} flipped to rule", flush=True)
print("RELABEL_DONE", flush=True)
