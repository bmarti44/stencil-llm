# FOCUS-2c Amendment 2 FAIL-SAFETY — raw-record diagnosis (fable, 2026-09-05)

Scope: independent CPU-only review of the 297 raw records under
`results/qwen/focus2c/amendment1/outputs/run/records/` (11 episodes x 27
records, hash 88306073...), the frozen renderer/checker in
`src/stencil/focus2.py` (freeze 6586221), the registration text
(LEDGER-PLAN.md FOCUS-2c section and its sort-only/Amendment clauses), and the
check 39 / check 35 READMEs. No model was launched; no sealed benchmark file
was opened. Nothing here is a registered reading; the registered terminal
(FAIL-SAFETY, h=6, r=0 at episode index 10) is arithmetically correct and
stands.

## 1. What "broken" actually was

Every one of the 18 broken BOTH-arm outputs (11 at NEUTRAL2, 7 at HOLD) is a
**well-formed, EOS-terminated JSON object that omits the `"tag"` key**. None is
empty, a period placeholder, truncated at the 64-token cap, or repetitive
(all four flags are False in every record; `output_ids` lengths 21-58 < 64).
The checker (`score()`, focus2.py:582-608) requires
`{"answer","tag"} <= keys`, so a missing tag is `schema_invalid`, and
`broken = any(empty, placeholder, schema_invalid, truncated, repetitive)`.
The registered breakage definition ("...or schema-invalid") makes this a
breakage event by construction, so the F6 stop fired on a *key-omission*
failure, not on a generation breakdown.

Classification of all 18 BOTH breaks: **other — valid JSON missing the
required `tag` key** (18/18). Invalid JSON 0, empty 0, truncated 0,
repetitive 0, placeholder imitation 0.

## 2. Verbatim evidence (episode, checkpoint, arm -> output)

Both-arm broken outputs with the same episode's text-restate and
placement-only outputs (eviction-only added because it is the decisive
control). `T`=truncated at cap.

| ep | ckpt | both (BROKEN) | text-restate | placement-only | eviction-only |
|---|---|---|---|---|---|
| 0 | NEUTRAL2 | `{"answer": [-17, 3, -14, 6, -10, -6], "user_fact": 86, "tool_fact": 32, "assistant_fact": "SET MEMO"}` | `{... "tag": 75, "user_fact": 86, ...}` ok | `{"answer": [-17, -14, -10, -6, 3, 6], "tag": 75, ...}` sorted (task fail) | `{"answer": [-17, 3, -14, 6, -10, -6], "tag": 75, ..., "assistant_fact": "SET MEMO"}` ok |
| 1 | HOLD | `{"answer": [-8, -12, -6, -3, 11, 18]}` | `{"answer": [18, 11, -3, -6, -8, -12], "tag": 52}` ok | `{"answer": [-8, -12, -6, -3, 11, 18], "tag": 52}` | `{"answer": [-8, -12, -6, -3, 11, 18], "tag": 52}` |
| 1 | NEUTRAL2 | `{"answer": [-18, -16, -9, 6, -10, 9, 20, -19], "user_fact": 63, "tool_fact": 65, "assistant_fact": "SET MEMO"}` | T at 64 (`..."assistant_fact": "STAY FOC`) | T at 64 | T at 64 (tag present) |
| 2 | NEUTRAL2 | `{"answer": [7, 12, 0, 8, -14, -20, -18], "user_fact": 50, "tool_fact": 85, "assistant_fact": "SET MEMO"}` | ok, tag 31 | ok, tag 31 | ok, tag 31 |
| 3 | HOLD | `{"answer": [-17, -7, 3, 8, 11, 16]}` | `{"answer": [16, 11, 8, 3, -7, -17], "tag": 19}` ok | ok, tag 19 | ok, tag 19 |
| 3 | NEUTRAL2 | `{"answer": [-18, 19, -13, -6, 11, 16], "user_fact": 86, "tool_fact": 75, "assistant_fact": "SET MEMO"}` | ok, tag 19 | sorted, tag 19 | ok, tag 19 |
| 4 | NEUTRAL2 | `{"answer": [7, -2, -12, 12, -6, 15, 17, -17], "user_fact": 34, "tool_fact": 96, "assistant_fact": "SET MEMO"}` | T at 64 | `{"answer": [-17, -12, -8, ...], "user_fact": 34, ...}` **no tag**, sorted | T at 64 (tag present) |
| 5 | HOLD | `{"answer": [11, 7, -5, -12, -13]}` | ok, tag 44 | `{"answer": [-13, -12, -5, 7, 11], "tag": 44}` | ok, tag 44 |
| 5 | NEUTRAL2 | `{"answer": [-19, 1, -20, 20, 14, -17, 5, 17], "user_fact": 13, "tool_fact": 33, "assistant_fact": "SET MEMO"}` | T at 64 | T at 64 | T at 64 |
| 6 | HOLD | `{"answer": [18, 16, 12, 0, -13]}` | ok, tag 76 | `{"answer": [18, 16, 12, 0, -13]}` **no tag** | ok, tag 76 |
| 6 | NEUTRAL2 | `{"answer": [-10, -8, 7, 18, 5, -4, 19, -9], "user_fact": 49, "tool_fact": 85, "assistant_fact": "SET MEMO"}` | T at 64 | `{"answer": [-10, -8, -9, -4, ...], "user_fact": 49, ...}` **no tag** | ok, tag 76 |
| 7 | HOLD | `{"answer": [16, 14, 11, 8, -2, -9]}` | ok, tag 25 | ok, tag 25 | ok, tag 25 |
| 7 | NEUTRAL2 | `{"answer": [-12, 14, 16, 1, -13, 19], "user_fact": 20, "tool_fact": 77, "assistant_fact": "SET MEMO"}` | ok, tag 25 | sorted, tag 25 | ok, tag 25 |
| 8 | NEUTRAL2 | `{"answer": [-13, 9, 10, 1, -1, -15, 11, -8], "user_fact": 49, "tool_fact": 46, "assistant_fact": "SET MEMO"}` | ok, tag 85 | sorted, tag 85 | ok, tag 85 |
| 9 | HOLD | `{"answer": [16, 12, 9, 7, 0, -6, -11, -16]}` | ok, tag 94 | ok, tag 94 | ok, tag 94 |
| 9 | NEUTRAL2 | `{"answer": [17, -10, 11, 12, -19, 15, 4], "user_fact": 39, "tool_fact": 21, "assistant_fact": "SET MEMO"}` | T at 64 | T at 64 | ok, tag 94 |
| 10 | HOLD | `{"answer": [20, 7, 4, 1, -12, -17, -18]}` | ok, tag 11 | ok, tag 11 | ok, tag 11 |
| 10 | NEUTRAL2 | `{"answer": [15, 1, -20, 0, 20, -13], "user_fact": 34, "tool_fact": 23, "assistant_fact": "SET MEMO"}` | ok, tag 11 | sorted, tag 11 | ok, tag 11 |

Two things are visible immediately. (i) The BOTH answer list is *correct* in
every NEUTRAL2 row (payload copied unchanged, facts correct) and in 4/7 HOLD
rows; only the tag is gone. (ii) BOTH and eviction-only produce the same
answer lists and the same `"SET MEMO"` assistant_fact (the memo body was
replaced by "." in both arms, so the model echoes the request phrase); they
differ *only* in the tag key.

Tag presence per checkpoint across the 11 episodes (T = tag present):

```
both            SWITCH TTTTTTTTTTT  HOLD T-T-T---T--  BACK TTTTTTTTTTT  CLEAR TTTTTTTTTTT  NEUTRAL2 -----------
placement-only  SWITCH TTTTTTTTTTT  HOLD TTTTTT-TTTT  BACK TTTTTTTTTTT  CLEAR TTTTTTTTTTT  NEUTRAL2 TTTT-T-TTTT
eviction-only   tag present in all 55 outputs (one NEUTRAL2 cut at the cap mid-memo)
neither / text-restate  tag present in every non-truncated output
```

The tag never drops at SWITCH/BACK/CLEAR (33/33 in BOTH); it drops exactly at
the two unrefreshed checkpoints, HOLD and NEUTRAL2.

## 3. Rendered prompt tails (what the model saw)

Rendered request tail for BOTH at episode 0 NEUTRAL2 (the six "." lines are
the placeholder-replaced assistant bodies; the system turn is the full system
turn — it contains **no rule text at all**):

```
<|im_start|>system
Follow the live task rule. Keep earlier facts for later requests.
<tools>...</tools>
<|im_end|>
... user_fact / tool-call turns ...
<|im_start|>user
Process this payload: [-8, -6, 5, 7, -18, 1, -1, 17]
Additional requested keys: memo. Invent a six-letter ASCII memo and include it as "memo".<|im_end|>
<|im_start|>assistant
.<|im_end|>
<|im_start|>user
Process this payload: [17, -10, -2, 0, -8, -15, 10]
Additional requested keys: none.<|im_end|>
<|im_start|>assistant
.<|im_end|>
<|im_start|>user
Process this payload: [-10, -16, 4, 5, -5, -4, 3]<|im_end|>
<|im_start|>assistant
.<|im_end|>
<|im_start|>user
Process this payload: [-1, -3, -8, 7, -18, -2, 9, 15]
Additional requested keys: none.<|im_end|>
<|im_start|>assistant
.<|im_end|>
<|im_start|>user
Process this payload: [12, 16, 6, -4, -19, -2, 5, 17]<|im_end|>
<|im_start|>assistant
.<|im_end|>
<|im_start|>user
Return the payload list unchanged.
Output compact JSON of the form {"answer": <JSON array of integers>, "tag": <integer>}; no prose or unrequested keys.
Keep tag equal to 75.
Additional requested keys: none.
Process this payload: [9, 8, 18, 16, -3, -8, -18, 19]<|im_end|>
<|im_start|>assistant
<think>

</think>

{"answer": [9, 8, 18, 16, -3, -8, -18, 19], "tag": 75}<|im_end|>
<|im_start|>user
Process this payload: [-17, 3, -14, 6, -10, -6]
Additional requested keys: user_fact, tool_fact, assistant_fact. Retrieve the earlier user and tool facts as user_fact and tool_fact. Retrieve your SET memo as assistant_fact.<|im_end|>
<|im_start|>assistant
<think>

</think>

```
-> `{"answer": [-17, 3, -14, 6, -10, -6], "user_fact": 86, "tool_fact": 32, "assistant_fact": "SET MEMO"}`

Unified diff of the eviction-only prompt -> BOTH prompt for episode 1 HOLD
(the only differences in the whole 418-token request):

```
-Sort the integers from largest to smallest.                      (system turn)
-Output compact JSON of the form {...}; no prose or unrequested keys.
-Keep tag equal to 52.
@@ SWITCH request
-Process this payload: [-20, -13, -3, -6, 3, 12, 14]
-Additional requested keys: none.<|im_end|>
+Sort the integers from largest to smallest.
+Output compact JSON of the form {...}; no prose or unrequested keys.
+Keep tag equal to 52.
+Additional requested keys: none.
+Process this payload: [-20, -13, -3, -6, 3, 12, 14]<|im_end|>
```

So at HOLD and NEUTRAL2 the BOTH arm and the eviction-only arm are identical
except for *where the three rule lines live*: system slot (eviction-only,
tag kept 11/11) versus the previous user turn only (BOTH, tag dropped 7/11 at
HOLD and 11/11 at NEUTRAL2). Between BOTH and placement-only the only
difference is the six "." bodies replacing answers that each carried
`"tag": N` (placement-only tag kept 10/11 and 9/11).

Where the rule text is, by arm and checkpoint (counted over all 297 records):

| arm | rules in current request | rules in system slot |
|---|---|---|
| neither, eviction-only | never | always |
| placement-only, both | SWITCH/BACK/CLEAR only | never |
| text-restate | every checkpoint | never |

This matches the registration exactly: "placement-only: remove that old-slot
rule and place the identical new live rule in the current user turn; retain
bodies; no refresh at HOLD or neutral request two"; "both: current-user
placement plus the identical repaired removal/scope mask; intervene only at
SWITCH, BACK and CLEAR"; code `current_cue()` focus2.py:491. The chat template
is well-formed in every record (roles, `<|im_end|>` closures, empty
`<think>` block on the generated turn, identical across arms).

## 4. Cause

**(c) Combination, by design — not a harness bug and not generic model
fragility.** The "tag" constraint has exactly two carriers in a prompt: the
rule line `Keep tag equal to N` and the `"tag": N` field in prior assistant
answers. Placement removes the rule from every persistent slot (the system cue
is retired and the rule is rendered only inside the event request, so at the
next unrefreshed request it sits one turn back and reads as part of a past
request). Eviction replaces every prior answer with ".", removing the
exemplar carrier. Each arm alone leaves one carrier and mostly keeps the tag;
BOTH removes both, and the model — following the visible current request
literally ("Additional requested keys: user_fact, tool_fact, assistant_fact"
plus the earlier "no prose or unrequested keys") — emits answer + requested
keys and nothing else. The only remaining exemplar (the previous event answer
with its tag) is one turn away and is out-weighed by the current request text.

Evidence against the alternatives:
- (a) rendering of rules alone: placement-only keeps the tag 10/11 at HOLD and
  9/11 at NEUTRAL2, and both of its tag-drops (ep 4, 6 NEUTRAL2; ep 6 HOLD)
  are the same key-omission pattern at reduced rate — the effect is present
  but weak while exemplars remain.
- (b) placeholders alone: eviction-only keeps the tag in all 55 outputs;
  check 39 (placeholder alone, 0 placeholder-only broken episodes of 64) had
  the JSON-array schema in the *system* prompt and a still-active user cue,
  i.e. a persistent format carrier; check 35 c2 (evict all answer columns)
  likewise kept the schema in the system prompt and showed 0-1 breakage per
  32-cell. Both prior checks therefore tested placeholders *with* a carrier
  and are consistent with this diagnosis, not contradicted by it.
- (d) harness rendering bug: the rendered text is byte-consistent with the
  registered templates; no malformed template, missing closure, wrong role
  or duplication is present. One cosmetic asymmetry exists — retiring an
  event cue in the placement arms also removes that request's
  "Additional requested keys: none." line (it was rendered once inside the
  placement block), whereas eviction-only history keeps it — but it is
  shared by placement-only (which keeps the tag), so it is not causal.
- (e) generic fragility: outputs are always terminated, parseable, correct
  in the answer list and facts; the failure is precise and monotone with
  carrier removal.

Check-37/39's "placeholder" was certified against a schema that lived in the
system turn. FOCUS-2c's placement arms moved the *entire* cue — task rule,
schema line and tag line together — out of the system turn. That is the
registered design, so the result is a real finding about the *registered*
BOTH arm: "placement of the whole rule block + placeholder eviction removes
every persistent carrier of an unchanged constraint at unrefreshed requests,
and the model then drops it." It is not evidence that "placement +
placeholder breaks generation".

## 5. A second, separate harness issue: the 64-token cap at NEUTRAL2

All 15 non-BOTH broken outputs are cap truncations at NEUTRAL2 (text-restate
5/11, neither 5/11, placement-only 3/11, eviction-only 3/11), every one of
them valid-looking JSON cut mid-memo or mid-brace. The model emits spaced
JSON (`", "` / `": "`) rather than the compact form the registration bounded
(<64 tokens for compact gold); measured with the frozen tokenizer, the same
content in compact form is 37-49 tokens, spaced it is 56-64+, and 8-element
payloads with three facts overflow. The BOTH arm never truncates *because*
its outputs lack the ~6-token tag field. So the F6 tally is doubly
confounded: h counts key-omission, r is suppressed on one side by
truncation and on the other by the shorter broken output. This also costs
text-restate its all-five endpoint in 5/11 episodes.

## 6. Descriptive prefix numbers (n=11, one cell, not a result)

All-five successes: neither 0, placement-only 1, eviction-only 1, both 0,
text-restate 3. Episodes with any broken output: both 11, placement-only 5
(3 cap, 2 tag-drop + 1 HOLD tag-drop in ep 6), eviction-only 3 (all cap),
neither 5 (all cap), text-restate 5 (all cap). Placement-only therefore
showed the same key-omission breakage at low rate; eviction-only showed
none. CLEAR (rules in the request) was 11/11 for placement-only,
eviction-only and both versus 0/11 for neither — the placement effect the
program is built on is plainly visible at the intervened checkpoint, and
disappears one request later when nothing carries the rules.

## 7. Verdict and the single minimal change

Verdict: real finding about the registered mechanism configuration, driven by
a design gap (no persistent carrier of unchanged constraints in placement
arms) rather than by a harness bug or by inherent model fragility. The
mechanism "move the *changed* rule to the current request; evict stale
answers" was never actually tested, because the intervention also moved the
*unchanged* constraints out of the system turn and then evicted the only
exemplars of them.

Single minimal change for a FOCUS-2d: **split the cue.** Keep the two
unchanged-constraint lines (`Output compact JSON ... no prose or unrequested
keys.` and `Keep tag equal to N.`) in the base system segment in all five
arms for the whole episode, and let placement/eviction act only on the task
line (`Sort ... / Return the payload list unchanged.`). This is one change to
`live_rules()`/the system template, leaves "no refresh at HOLD/NEUTRAL2"
intact (so persistence is still tested), and keeps every arm's unchanged
constraint literally unchanged, as the registration says it should be. It
also makes the arms comparable to check 39/35, where the schema carrier was
in the system turn.

Two lesser corrections that should ride along (not the one minimal change):
raise the generation cap or require compact separators so 8-element NEUTRAL2
replies cannot hit 64 tokens (otherwise r stays artificially suppressed), and
either render "Additional requested keys" outside the retirable cue or
accept the cosmetic asymmetry in writing. If those are not adopted, F6 as
defined cannot distinguish key-omission from generation breakdown; consider
reporting `schema_invalid` and `truncated` as separate rows under F6 rather
than one pooled breakage bit.

Nothing above should be read as a rescue of the terminal: the registered rule
fired correctly on the registered definition, and the stop stands.
