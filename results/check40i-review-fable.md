# Check 40i accuracy review (fable, one round, CPU only)

Reviewed at commit 42a6e145. Sources: results/quick-checks/check40i/{README.md,
prewritten-reading.md, summary.json, records.jsonl, audit.json, validation.json,
independent-reading.json, freeze.json, projection.json, resources.json,
runtime.json, ledger.md, biases.pt, tasks.json, report.py};
scripts/focus_check40i.py (sha 3bcdb9c6... matches freeze.json; inherited
focus_check40h.py ac510cf6..., focus_check40f.py e7ac0394..., scorer
focus_check40.py 1888a757... all unchanged since my 40h review);
results/check40h-review-fable.md; check40b/{frozen-biases.pt, banks.json};
quick-checks index line and WORKLOG entry. No model launched; no sealed
inputs read. Every number below was recomputed from records.jsonl with my own
parsers (regex fence extraction, ast.parse, node --check, own return-AST
coarse check) — not by re-running the repo's scorer.

## 1. What the raw records show

Counts. All 28 README table cells (JS/Python/broken/coarse/fenced/bare/
missing-paren) reproduce exactly from my independent parse: 672 rows, 480
actual generations (24 x [4 shared prefix + 3 branches x 3 + 7 OFF]), 14152
tokens, truncated 0, cost-stopped 0, EOS 480/480. Zero disagreements between
my language label and the recorded `valid_language` on any of the 672 rows.
Fenced 480/480 actual; 0 bare, 0 ambiguous, 0 echo, 0 "OK", 0 broken in any
arm at any step. Missing-closing-paren defect: 0 rows (the 40b `swapped` /
40h M-SWITCH defect did not recur; consistent with 40h, where the defect
appeared only under the negated-JS bias, which 40i does not use).

Reading applied mechanically. prewritten-reading.md sha fbc7ba40... matches
freeze.json; the README is byte-identical to it up to "Results PENDING."
`decision()` (script lines 132-155) implements exactly the frozen thresholds;
summary.json `passes` has all eight conditions True; report.py recounts
independently and asserts `verdict == summary["reading"]`
(independent-reading.json agrees). Verdict CLOSED-RELEASE follows from the
code, not from prose.

Schedule (from `bias_sha256`/`alpha` on every row). JS bias bda3d63e (=
0.75 x 40b `correct`, bit-equal to 40h's js tensor) at SET/HOLD in all
biased arms; none at SWITCH/HOLD_AFTER_SWITCH/CLEAR in every arm; at
BACK/HOLD_AFTER_BACK: Z = bda3d63e (JS), Zc = none, S = 7b6f685e (0.75 x
40b `shuffled`: a per-layer permutation of the JS vector, identical row norms,
cos 0.02 to JS). OFF: none everywhere, alpha 0. No negated-JS ("Python")
bias appears anywhere in this run.

Masks. Events fire only at SWITCH (2 bodies), BACK (4), CLEAR (6) in Z/Zc/S;
never in OFF; never at HOLD steps (which carry the previous set unchanged).
For all 72 events per arm, `mask_event.bodies` equals the body spans I
rebuilt from the records ([cache_prefix + input, +generated - EOS) of every
previous assistant turn), `masked_positions` equals their union,
placeholders and cue_turns are empty, `downstream_recomputed` False,
`retained_text_unchanged` True. `mask_forward_trace` carries the masked set
for every forward (ep0 Z CLEAR: 29 forwards). Ep0 Z masked 54/107/162 at
SWITCH/BACK/CLEAR. Same position-preserving eviction as 40f/40h.

Control isolation. The 192 shared-prefix rows (Zc, S SET..HOLD_AFTER_SWITCH)
are byte-identical to the Z rows except id/arm/shared_from_generation. At
BACK, `input_sha256` and `masked_positions` are identical across Z/Zc/S in
24/24 episodes: the three BACK cells differ only in the bias tensor. Z BACK
text differs from Zc BACK text in 24/24 episodes (the bias always changes
the output, even in ep 2 where the language did not flip: Z wrote
`((30+35)*(26-13))` JS-style spacing inside Python; Zc/S wrote
`(30 + 35) * (26 - 13)`); Zc and S BACK texts coincide in 17/24, i.e. the
shuffled vector behaves like no bias for language.

Real re-entries and releases. Z: SWITCH Python 24/24 from SET-JS + HOLD-JS
in 24/24 (paired real SWITCH releases 24); BACK JS 23/24, all 23 from a
SWITCH-Python + HOLD_AFTER_SWITCH-Python state (real re-entries 23); CLEAR
Python 24/24, with BACK-JS + HOLD_AFTER_BACK-JS + CLEAR-Python in 23/24
(paired real CLEAR releases 23); the full 7-step target chain holds in 23/24.
The one miss is ep 2 (screen_0 family at BACK), Python at BACK and
HOLD_AFTER_BACK, then Python at CLEAR — a persistence episode, not a release,
so the README's "outside the paired criterion 1/24" is correct. Across
40h-Z (seed 40070, miss ep 0) and 40i-Z (seed 40080, miss ep 2) the
non-default re-entry floor is 1/24 at each seed.

Tasks. 168 fresh expressions, all distinct, 0 overlap with 40d/40f/40h
tasks.json (472 expressions) and 0 overlap with 40b banks.json. Families
balanced 56/56/56 in Z. Same generator as 40h with only the seed changed.

Cost. Per-row seconds sum 923.55 + load 373.52 + overhead 22.23 = 1319.30 s
= summary gpu_seconds; 21.99/30 GPU-min, 0.3665 GPU-h, no overrun. Mean
1.92 s per generation. Note: the brief I was given says "9/30 GPU-min"; the
artifacts say 21.99/30 including load (15.4 min generation alone). The
artifacts are right; correct the number wherever "9" was written.

Freeze/process. validation.json: freeze bb42c4e6 precedes inference,
midpoint 924f2ef1 is an exact prefix, freeze hashes match (I re-hashed the
four scripts), raw exit 0, flag absent. Commit 42a6e145 only removes a stray
.pyc. Index line and WORKLOG entry are literal restatements of the table; no
overclaim found in either.

## 2. Answers to the posed questions

(a) Is the release rule CLOSED as a development finding for this pair on
this trunk? Yes. The rule "enter/re-enter non-default = routing bias + mask
of outputs made under the previous skill; return to default = bias OFF +
mask; opposite-direction bias unnecessary" now has every clause measured
on a fresh seed under a schedule frozen before inference, with a decision
function fixed in advance and met on all eight conditions:
- return to default = Z SWITCH 24/24 and Z CLEAR 24/24 (mask + OFF), plus
  Zc/S CLEAR 24/24 — five separate mask+OFF cells across 40h/40i, 168/168;
- enter non-default = SET 24/24 (bias, empty history);
- re-enter non-default from a real default state = Z BACK 23/24 (bias +
  mask over four Python bodies), 40h-Z 23/24 on the other seed;
- bias necessary at re-entry = Zc 0/24 (OFF + mask, identical KV and mask)
  and S 0/24 (shuffled direction, identical norm): the 23 vs 0 discordant
  pairs are decisive at n = 24, and the direction, not the perturbation
  magnitude, carries it;
- opposite-direction bias unnecessary = Z SWITCH 24/24 and CLEAR 24/24
  without it; "adds breakage" remains the 40h M-vs-Z observation (4 vs 0,
  p = 0.125) and is not re-tested here, so keep it phrased as "unnecessary;
  40h suggests harmful", not "harmful";
- competence preserved: 0 broken, 0 bare, coarse 24/24 in all 28 cells.
The 1/24 re-entry miss recurred at both seeds; the rule should be stated
with that floor ("~23/24 at alpha 3"), not as "always".

(b) What it does NOT show.
- One pair (JS vs the Python default), one trunk (Qwen3-30B-A3B, this
  transformers build), one bias construction (40b competence profile, 0.75
  scale, alpha 3 from 40c), greedy decoding, 64-token caps.
- Two seeds only across 40h/40i, 24 episodes each, one Z-primary run;
  controls at BACK are single-seed (40i) and single-direction.
- Synthetic arithmetic expressions with a fixed function-name template; the
  measured "skill" is surface language syntax of a one-line return. Nothing
  here speaks to skills that are not a fenced-language choice, to longer
  outputs, or to tasks where the two skills' outputs are not near-isomorphic.
- Masking is position-preserving KV key eviction of whole assistant bodies
  in a research harness, with headers/closures and downstream KV retained;
  it is not a serving-time attention mask and has not been shown equivalent
  to one. Zc/S share Z's prefix, so the isolation is of the bias, not of the
  mask; there is still no bias-only (no mask) BACK cell at this seed (40d
  covers it for the earlier bias).
- No classifier or register in the loop: every SET/SWITCH/BACK/CLEAR event
  was scheduled by the script, not detected. HOLD steps run with the bias
  still on and the model's own previous answer visible, so maintenance
  without the bias is not measured (the README says this).
- No statement about an independently profiled Python direction, about
  alpha sensitivity, or about what the retained non-body KV contributes
  (ep 2 persistence is unexplained; in 40h the persisting episode was ep 0).
- The "shuffled" control shows that a same-norm random-permutation vector
  does nothing; it does not show that arbitrary same-norm directions do
  nothing.

(c) The one generality test that now justifies a bounded run. The specific
unresolved claim is: "the rule is a property of the routing-bias mechanism,
not of the JS-vs-Python pair." Every positive result so far is on one pair
whose bias was built once (40b). The deferred check 40g — a second language
family (Go is the sensible choice: statically typed, brace syntax, a
distinct `func`/`:=`/package surface, and a different default-distance from
Python than JS) — is the right single test. It needs: a fresh 40b-style
competence profile for Go on this trunk (positive control: SET Go >= 20/24
with an empty history and <= 2 broken, otherwise the pair is ineligible and
the run says nothing about the rule), then the same Z schedule with the Go
bias in place of JS and the same Zc (OFF + mask) BACK control, fresh seed,
same 20/2/4 thresholds, same decision function. Projected cost from 40i:
~22 GPU-min including load for 480 generations; add the profiling pass.
If Go SET, BACK and CLEAR meet the bars with Zc at <= 4, the rule is a
mechanism property across two families; if SET passes but BACK fails, the
finding is pair-specific and the closure should say so. Do not run further
JS/Python seeds; they cannot answer this question.

## 3. Findings list

- none (verified): all 28 cells, both parsers, coarse checks, bias digests
  per arm/step, 216 mask events against rebuilt body spans, shared-prefix
  identity (192 rows), BACK context identity across Z/Zc/S (24/24), paired
  counts (24/23/23), real re-entries (23), fence loss (0), missing-paren
  defect (0), task disjointness (0 overlap), freeze hashes, decision logic,
  cost arithmetic.
- low: the brief's "9/30 GPU-min" figure is wrong; the artifact says
  21.99/30 (15.4 min generation + 6.2 min load). Use the artifact number.
- low: the 1/24 BACK miss recurred at both seeds (40h ep 0, 40i ep 2); state
  the rule with its ~23/24 floor rather than as unconditional. Verdict
  CLOSED-RELEASE stands as frozen; it is a development finding for this
  pair on this trunk, not a general result.
