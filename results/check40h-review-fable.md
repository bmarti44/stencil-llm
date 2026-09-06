# Check 40h accuracy review (fable, one round, CPU only)

Reviewed at commit 6e1ccb84. Sources: results/quick-checks/check40h/{README.md,
summary.json, records.jsonl, audit.json, freeze.json, prewritten-reading.md,
independent-reading.json, report.py, ledger.md, biases.pt, runtime.json};
scripts/focus_check40h.py (sha ac510cf6... matches freeze.json; inherited
focus_check40f.py e7ac0394... and scorer focus_check40.py 1888a757... unchanged
since my 40f review); results/check40f-review-fable.md; check40b README and
records for the breakage comparison; quick-checks index and WORKLOG lines. No
model launched; no sealed inputs read. Every number below was recomputed from
records.jsonl.

## 1. What the raw records show

Counts. All 21 README table cells (JS/Python/broken/coarse/bare/ambiguous/echo)
reproduce exactly: 528 rows, 480 actual generations (24 x [1 fresh-OFF + 2
shared prefix + 2 branches x 5 + 7 T']), 14603 tokens, truncated 0,
cost-stopped 0. The 48 Z prefix rows are byte-identical to their M sources
apart from id/arm. Paired BACK-JS + HOLD_AFTER_BACK-JS + CLEAR-Python: M 19,
Z 23, T' 24. Fresh-OFF Python 24/24. gpu_seconds 1347.6 = per-row seconds
956.9 + load 368.3 + overhead. Prewritten reading is byte-identical to the
README up to "Results PENDING."; `decision()` implements the frozen thresholds
and the reading is PARTIAL by that code (SWITCH fails on broken 4 > 2, BACK
fails on 19 < 20, CLEAR passes; paired 19 < 20).

Bias schedule (from `bias_sha256`/`alpha` on every row). M: JS bias
(bda3d63e) at SET/HOLD/BACK/HOLD_AFTER_BACK, Python bias (d76e878f) at
SWITCH/HOLD_AFTER_SWITCH, none at CLEAR. Z: identical except none at
SWITCH/HOLD_AFTER_SWITCH. T' and fresh-OFF: none everywhere. Note what the
"Python bias" is: biases.pt holds js = 0.75 x 40b `correct` and python = 0.75 x
40b `swapped`, and the two tensors have cosine -1.000 (bit-level near-negation,
(48,128), |max| 2.79). So "Python bias" throughout 40b-40h means the negated
JS direction, not an independently profiled Python routing term. This matters
for the reading of M's breakage below.

Mask schedule (from `mask_event`, `masked_positions`, `mask_forward_trace`).
Events fire only at SWITCH (2 bodies), BACK (4 bodies), CLEAR (6 bodies) in all
three arms; HOLD steps carry the previous set unchanged; placeholders empty
everywhere. T' CLEAR additionally masks the six cue-bearing user turns
(ep0: 6 spans of ~55 tokens each; 502 of ~600 positions masked, leaving only
the system prompt, assistant headers/closures and the CLEAR request visible).
Body spans are [first generated token, EOS): fences in, EOS and
`<|im_start|>assistant...` header out, as in 40f. The audit script replays all
of this and I spot-checked ep0 in all three arms (M masked 55/113/165, Z
55/105/157, T' 65/115/502 at SWITCH/BACK/CLEAR).

M's 4 SWITCH breaks (ep 2, 5, 10, 14). All four omit the final `)` of an
otherwise correct fenced Python function, and all four repeat the identical
defect at HOLD_AFTER_SWITCH (the broken reply is visible there). They are NOT
the 40b C-family neighbours: 40b's Dart-style `int f() {}` and `->` arrow
replies were the JS-bias (`correct`) arm's breakage. They are exactly 40b's
`swapped`-arm defect (3/32 there, all `(a*b)+(c*d` with the closing paren
dropped). Here 3/4 onset in the same sum-of-products family screen_1 and 1/4
in screen_0. Decisive paired comparison: Z runs the same four episodes from the
same KV prefix with the same prompt and only the bias changed (OFF), and
produces the correct closed-paren Python in all four; Z SWITCH is 24/24 with 0
broken. Discordant pairs 4 vs 0 (exact binomial two-sided p = 0.125). So the
negated-JS bias is the cause of the breakage, and it buys nothing: the
default is already restored by mask + OFF.

M's 5 BACK Python-persistence episodes (ep 0, 3, 5, 8, 20). Fenced, valid
Python at BACK, HOLD_AFTER_BACK and CLEAR; no JS at any later step, so they are
counted at CLEAR as Python-persistence, not release (the README's "19 real +
5 persistence" split is correct). Only ep 5 is one of the broken episodes; the
other three broken episodes (2, 10, 14) recover JS at BACK. In Z the same
schedule at BACK (JS bias + 4 bodies masked) fails on ep 0 only; ep 3, 5, 8,
20 all return JS. Discordant pairs 4 vs 0 again (p = 0.125). At BACK the visible
context is identical in M and Z except for KV columns computed under the Python
bias in M: the SWITCH/HOLD_AFTER_SWITCH EOS closures and the HOLD_AFTER_SWITCH
user turn + assistant header (prefilled under the current bias). The bodies
themselves are masked in both. So the extra persistence in M is carried by
non-body KV computed under the opposite-direction bias — the README's
"surviving downstream KV can carry traces" made concrete. This is the third
place (after 40b swapped, and M SWITCH here) where the negated bias costs
something.

Z BACK 23/24. Non-default direction, JS bias + mask of all four Python bodies,
from a Python state established by mask + OFF: JS 23, Python 1 (ep 0, the
same episode that persists in M), broken 0, fences 24/24, coarse 24/24.
HOLD_AFTER_BACK repeats it (bias + visible own JS answer). CLEAR (OFF + 6
bodies masked) then gives Python 24/24 with 23 paired real releases. This is
the cell I asked for in the 40f review and it passes the 20/24, <=2 broken
bar that the frozen rule applied to M.

Fence loss. M and Z: 0 bare replies in 336. T': 3 bare valid replies (ep 13
BACK and HOLD_AFTER_BACK, JS function; ep 5 CLEAR, a Python lambda, which the
unchanged coarse checker rejects for lacking `return` — the README says so).
The 40f residue (T SWITCH/BACK 13/24 bare, R3 CLEAR 14/18, echo/OK imitation)
essentially did not recur. The schedule differences are: no NEUTRAL "OK" turn
in 40h (40f kept the short "OK" bodies visible), masks at BACK too, and T'
cue-turn masks at CLEAR. Consistent with my 40f reading that the visible
short "OK" body was the imitation carrier, but 40h does not isolate it; treat
fence loss as schedule-sensitive, not as absent in general.

Parsers/scorer. score() unchanged from 40f (sha match); audit re-scores every
row. Spot checks: the eight missing-paren replies are invalid in both parsers;
the bare lambda is ast-valid Python, node-invalid; the two bare JS functions are
node-valid, ast-invalid. No ambiguous, echo, OK, empty or truncated outputs in
any arm. No scoring error found.

## 2. Answers to the posed questions

(a) Does Z establish the rule "to return to the default: mask + bias OFF; to
enter or re-enter a non-default skill: bias + mask; an opposite-direction
bias is unnecessary and adds breakage"? Within this task, yes, and each
clause has its own cell: return-to-default = Z SWITCH 24/24 and Z/M CLEAR
24/24 (mask + OFF, three separate cells, 72/72); enter/re-enter non-default =
SET 24/24 (bias, empty history) and Z BACK 23/24 (bias + mask over a real
Python history); unnecessary = Z SWITCH 24/24 without the Python term;
adds breakage = M SWITCH 4/24 broken vs Z 0/24 on identical prefixes, plus M's
extra BACK persistence (5 vs 1). The two M-vs-Z differences are each 4 vs 0
discordant pairs, p = 0.125 — directionally consistent, not individually
significant at n = 24. The rule is also not shown to be "necessary": there is
still no mask-only (bias unchanged) BACK cell here, but 40f R3 (JS bias
unchanged, masks, 18/24 JS with 6 echoes) and 40d (bias-only BACK 0/24)
already cover the neither-alone cases for this direction.

(b) The frozen PARTIAL label is correct and should stand: the reading was
frozen on M, M fails the breakage bar at SWITCH and misses 20 at BACK, and Z
was pre-registered as a control that never rescues M. But the honest
statement of what 40h found is not "release closure is partial"; it is "the
prescribed M schedule is the wrong schedule, and the pre-registered control
is the right one." Z is a full 24-episode arm with its own frozen schedule,
same seed and tasks, fully audited, meeting every literal M threshold
(SWITCH 24, BACK 23, CLEAR 24, broken 0 at every step, paired 23). That is
sufficient to state the operational rule as a development finding now, with
the caveats in (c). It is not sufficient to call release CLOSED: the rule was
identified in the same run that would confirm it, and Z's decisive cell has
n = 24 at one seed with a 1/24 persistence floor that the same episode shows
in M. A rerun with Z as the primary frozen schedule, fresh seed, same 20/2
thresholds, decisive cells BACK JS >= 20 and paired release >= 20, is the
right closure. It is cheap (~10 GPU-min at the measured 2 s/request without
the M branch and T'), and should keep one mask-only control at BACK (JS bias
unchanged is trivial there, so use OFF + mask at BACK to show the non-default
direction needs the bias) — that is the one cell the rule still lacks.

(c) Overclaims to avoid.
- Single seed, one language pair, one task shape (arithmetic surface
  syntax), greedy, alpha 3 from 40c; 24 episodes; nothing here speaks to
  skills that are not a fenced-language choice.
- "Python bias" is the negated JS direction. The breakage claim is about an
  opposite-direction bias built by sign flip; it does not show that a
  separately profiled Python term would break.
- M's breaks are the 40b swapped missing-paren defect, family-clustered
  (3/4 screen_1), not the C-family (Dart/arrow) neighbours of 40b's JS arm;
  do not merge the two breakage modes in prose.
- M vs Z differences are 4 vs 0 discordant pairs (p = 0.125) each; say
  "consistent with", not "shows", until the rerun.
- Fence loss did not recur, but its absence is schedule-dependent (no
  NEUTRAL "OK" turn); do not claim the mask residue of 40f is gone.
- T' 24/24 is a language-target bar with the cue-bearing user turns masked
  at CLEAR (502 of ~600 positions), i.e. almost a fresh prompt; it is a
  text-carrier control, not a competing "text bar" for release, and its
  CLEAR coarse is 23/24 (lambda). Do not present T' as evidence that text
  cues release more cleanly than bias.
- Masks retain headers/closures and stale downstream KV; the persistence
  analysis above is inference from which columns differ, not an ablation.
- The index/WORKLOG lines are literal and do not overclaim; the README's
  "assess [the non-default direction's] reliability using M BACK" line is
  the frozen text and is now misleading — Z BACK is the cleaner measurement
  of that direction, and the next writeup should say so explicitly.

## 3. Findings list

- none (verified): counts, schedules, masks, parsers, cost, freeze, shared
  prefix identity, paired counts, verdict logic all reproduce.
- low: README's frozen "assess ... using M BACK" sentence is superseded by
  the run's own Z arm; the result paragraph should point at Z BACK for the
  non-default direction.
- low: the "Python bias" naming hides that it is -JS (cos -1); state this
  wherever the breakage of the opposite-direction bias is discussed.
- low: M-vs-Z breakage and persistence effects are p = 0.125 each at n = 24;
  a fresh-seed rerun with Z primary (plus an OFF + mask BACK control) is the
  honest closure. Verdict PARTIAL stands as frozen.
