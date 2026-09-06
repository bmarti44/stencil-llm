# Check 40f accuracy review (fable, one round, CPU only)

Reviewed at commit abdaeb26. Sources: results/quick-checks/check40f/{README.md,
summary.json, records.jsonl, audit.json, cpu.json, freeze.json, projection.json,
prewritten-reading.md, report.py, ledger.md}; scripts/focus_check40f.py (sha
e7ac0394... matches freeze.json and is unchanged between anchor e570e74c and
abdaeb26); scripts/focus_check40.py (scorer); context check40d/39/35 READMEs.
No model launched; no sealed inputs read. Every number below was recomputed
from records.jsonl.

## 1. What the raw records show

Counts. All README/summary cells reproduce exactly from records (864 rows, 648
actual generations = 24 x (1 fresh-OFF + 3 shared prefix + 4 arms x 4 steps +
7 T); 14406 generated tokens; truncated 0; cost_stopped 0; cap 64). Fresh OFF
CLEAR default Python 24/24. gpu_seconds 1376.87 = sum of per-row seconds
(976.7) + load (393.9) + overhead; projection 5058 s was a large overestimate
(15 tok/s assumed; actual is faster). Cost claim is accurate.

Mask implementation (verified from `mask_event`, `masked_positions`,
`mask_forward_trace`). `session["bodies"]` records, for every non-NEUTRAL
turn, the span [first generated token, EOS) — i.e. the whole assistant reply on
a code request, fences included, EOS and the `<|im_start|>assistant\n<think>\n\n</think>\n\n` header excluded. `mask_answers` is invoked only when
`step in ("SWITCH","CLEAR")` (script line 593). So:
- SWITCH event masks 2 bodies (SET, HOLD). Ep0: positions 92-118, 209-234 → 53
  columns. Verified `after == union(bodies)` on sampled episodes.
- BACK: `mask_event` is None in all 96 R2/R3/R4/T rows; `masked_positions`
  stays at the SWITCH-time set (53 in ep0). So BACK was run with the two JS
  answers masked and the SWITCH/HOLD_AFTER_SWITCH Python answers fully visible.
- CLEAR event masks all 5 bodies (SET, HOLD, SWITCH, HOLD_AFTER_SWITCH, BACK);
  ep0 → 146 columns. Nothing else is ever masked; the NEUTRAL "OK" bodies, user
  turns, headers and closures stay visible at every step.
- Every forward (prefill, each decode step, EOS closure) carries the 2D key
  mask with those absolute positions zeroed; position_ids are absolute. "Masks
  persist after each event; later answers remain visible until next event" is
  exactly what the records show.
- R4 placeholder: `.` (token 13) is forwarded at the body's first position
  (originally the "```" token), directly after the empty-think header, with the
  current bias (python at SWITCH, none at CLEAR); only that one KV column is
  overwritten; the remaining body columns stay masked. Ep0 placeholder forwards:
  pos 92 with 0 masked, pos 209 with 26 masked (body 1 minus its placeholder) —
  consistent with `masked - {start}`. At CLEAR three more placeholders are
  added at 296/358/420 (the R4 "." replies), so the masked set does not grow.

Why R2 BACK stayed Python (23 Python, 1 broken, JS 0/24). At BACK the model
sees two empty assistant turns (masked JS answers), then two visible fenced
Python answers, under a JS bias. That is the same situation as R1 SWITCH and
check 40d's primary SWITCH (bias flip against visible own answers, 0/24 and
0/32): the alpha-3 bias never overrides visible own-history. The frozen design
text "BACK ensures CLEAR starts after renewed JS" assumed bias-only BACK would
work, which 40d had already shown it does not. The CLEAR cell was therefore
predictably degenerate before the run.

R3 as control. R3 keeps the JS bias and applies the same masks. It is a fair
"mask alone, no routing change" control for SWITCH, and it is informative in a
way the README under-reads: the 6 "broken" replies are not garbage. At SWITCH
they are bare echoes of the expression (`((23-25)-(36+36))`), parsed by both
ast.parse and node → "ambiguous" → broken. The same 6 episodes (0,3,9,12,18,21)
are broken at every later step: all six are the subtraction-shape family at
SWITCH (screen_2, 6/8), and the echo answer stays visible so it is copied
forward. At CLEAR (all bodies masked, JS bias still on) 4 of the 6 reply "OK"
— the only assistant body still visible is the NEUTRAL "OK". Also, after
masking, fences drop: R3 SWITCH 7/18 valid JS are bare (unfenced) functions and
R3 CLEAR 14/18; T SWITCH 13/24, T BACK 13/24, T CLEAR 24/24 bare. R2 (Python
bias) keeps fences 24/24. So the mask leaves a visible "assistant answered with
nothing" pattern that the model partly imitates (short/bare/echo/OK replies);
the bias hides this when it is aligned with the default. This is the check-35
lesson ("deleting answers does not remove every history carrier") plus a new
one: the hole itself is a carrier.

R4 placeholder failure vs check 39. Here the placeholder "." sits in an
assistant turn whose user prompt is the same code-request template as the
target turn; system prompt says "Answer the request concisely… No examples or
extra explanation", suffix "Give only the requested answer." Two consecutive
turns of (code request → ".") are a perfect in-context rule and the model
follows it 24/24 (". <eos>"). Each "." reply then becomes another visible "."
turn (no repair), so HOLD_AFTER_SWITCH/BACK/CLEAR 24/24 are not independent
failures. In check 39 the periods replaced integer-sort operand answers while
the release request was a different, explicit instruction (copy; "Cancel the
earlier sorting instruction") and the neutral requests explicitly asked for
copying; imitation was 0/64 there. The difference is task/instruction
specificity, not the mechanics: here the request that must be answered has no
explicit format instruction and looks identical to the requests that got ".".
The R4 CLEAR count is also wrong to read as a placeholder test — by CLEAR the
history holds five "." turns.

Parsers. score(): fenced/unfenced code → ast.parse and `node --check`; exactly
one parse → language; both → ambiguous; neither → invalid; empty → empty; all
flags → broken. Checked: R2 ep23 SWITCH/HAS/BACK missing ")" → invalid in both
(and the malformed shape is copied across the three visible turns, then fixed
at CLEAR once masked); T ep19 CLEAR "solve_release_19_5() {…}" (no `function`)
→ invalid in both; R3 echoes → ambiguous; R3 "OK" → empty; R3 `solve_x = () =>
…` and `(() => {…})()` → valid JS. First-token/fence tables reproduce. No
scoring error found.

Freeze. prewritten-reading.md is byte-identical to the README up to "Results
PENDING."; thresholds (20/1/3 for n=24) and the pass logic in `decision()`
match the reading; independent-reading.json agrees.

## 2. Answers to the posed questions

(a) Rule "every change of governing skill = routing change + mask of outputs
produced under the previous skill". Established by these arms for ONE
transition only: JS → Python at SWITCH. There, routing alone fails (R1 0/24),
mask alone under the old routing fails (R3 Python 0/24), both together succeed
(R2 23/24). Two caveats keep it from being the general rule: (i) Python is the
model's fresh default (24/24), so "mask + Python bias" is not separable from
"mask + nothing" — there is no mask+OFF cell at SWITCH, and R2 CLEAR (mask+OFF)
gives Python 24/24, i.e. R3 shows the OLD routing must be removed, not that the
NEW routing must be added; (ii) the non-default direction was never run with a
mask: BACK (Python → JS) had routing change only and failed 0/24. The nearest
evidence for routing+mask in the non-default direction is R3 SWITCH itself (JS
bias + masked holes → JS 18/24, 6 echoes), weaker than SET (24/24). The missing
cells are therefore: BACK with mask (the real test of the rule), CLEAR from a
JS actually reestablished by masked BACK, and a mask+OFF cell at SWITCH to
isolate the routing term.

(b) T CLEAR (bias off, all bodies masked, JS 23/24). It does not show that a
bias-set skill needs more than mask+OFF to clear; it shows that in T the skill
is carried by user text ("Use JavaScript." is in the SET/HOLD/BACK user turns,
the last visible instruction being BACK's), and masking assistant bodies leaves
those carriers intact. "Clear" must remove or counter whatever carries the
skill: for a bias-set skill that is bias-off + mask (R2 CLEAR 24/24, but
degenerate — see (a)); for a text-set skill it means masking the cue-bearing
user turns or an explicit cancel (check 39 style). So yes, clear needs a mask —
of the carrier, which in T is not the outputs.

(c) Overclaims. The headline "RELEASE WORKS" and the index/WORKLOG line
"RELEASE WORKS by fixed rule (R2)" are literally true under the frozen reading
but the reading was built on a false premise (bias-only BACK would restore
JS), making CLEAR a persistence-of-default cell; the README body says this
plainly, the headline and index line do not. Under-reported: R3's breakage is
6 persistent echo/OK episodes, not scattered failures; masking alone produces
a visible empty-turn residue with format side-effects (fence loss 13/24 in T,
OK/echo imitation in R3) — the README's tables contain this but the text calls
them "failures" and moves on. Not overclaimed: masking implementation,
persistence semantics, cost, parser behaviour, HOLD_AFTER_SWITCH (properly
qualified as bias + visible answers). Minor: "R4 … CLEAR 24 invalid period
copies" should say the CLEAR failure is inherited from SWITCH (five "." turns
visible), not an independent placeholder result.

(d) Closure test. The claim cannot stand as a release rule; it stands as "at
SWITCH, JS→Python(default) needs both the bias flip and the mask; neither
alone works". One 24-episode rerun is the right closure and is cheap (~10-15
GPU-min at the measured rate): arm R2' = R2 schedule with masks at every
change (SWITCH, BACK, CLEAR); arm R3' = same masks, JS bias unchanged (control
at BACK is then trivial, so instead run the control at SWITCH as mask+OFF to
isolate the routing term); decisive cells are BACK JS ≥20/24 (non-default
direction with routing+mask) and CLEAR Python ≥20/24 following a real JS BACK.
Report fence loss and echo/OK imitation as named diagnostics, since they are
the mask's residue. Drop R4 (the period placeholder is refuted for same-template
code turns) and keep T only if its CLEAR also masks the cue-bearing user turns.

## 3. Findings list

- medium: CLEAR cell degenerate by design (bias-only BACK contradicts 40d);
  headline/index line carry "RELEASE WORKS" without that qualification.
- medium: rule (a) is shown only for the default-coincident direction with no
  mask+OFF cell; non-default direction with mask untested.
- low: R3 breakage mis-described as generic failures; it is 6 persistent
  echo/OK-imitation episodes, family-clustered at onset, plus fence loss after
  masking in uncued arms — a mask residue worth naming.
- low: R4 HAS/BACK/CLEAR counts are inherited from the SWITCH failure.
- none: masking semantics, positions, parsers, counts, cost all verified.
