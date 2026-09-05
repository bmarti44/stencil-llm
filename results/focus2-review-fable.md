# FOCUS-2 review (fable, one round, CPU-only) — DRAFT v2 text (7d0c244) + harness v1 (8f4b76c, handoff cec15fa, a1eb646)

Scope: LEDGER-PLAN.md "## FOCUS-2 ... (DRAFT v2)" and the CPU handoff appended after it;
scripts/focus2.py, src/stencil/focus2.py (2588 lines, read in full), tests/test_focus2.py;
results/quick-checks/check3{7,8,9}/README.md and check39/4b/summary.json; my own
check34/35/36/38 and focus-synthesis reviews (disposition faithfulness). CPU only, no model
or GPU process launched, foreground only, no process signalled; sealed IFEval input and
BFCL cohort contents not opened; no repo edit besides this file.

Tests run (foreground, `set -o pipefail`):
`CUDA_VISIBLE_DEVICES='' uv run pytest -q tests/test_focus2.py tests/test_eval_data_separation.py tests/test_sealed_guard.py`
-> **66 passed, 1 warning (pre-existing scripts/b2_gsm8k.py SyntaxWarning) in 210 s, exit 0.**

## VERDICT

**(A) Text, registration readiness: UNSOUND as written — two gates are unreachable or
fail on chance by construction (A1 critical, A2 high); SOUND-WITH-FIXES once A1–A3 are
applied.** The evidence binding is honest (check 39 receipt, check 37 STOP not pooled,
check 38 placement inside the request, complete pairs, pre-registered eviction bound);
every number I traced reproduces. The text-restate template is the strongest fair text
alternative and its hash reproduces. But the safety composite cannot pass: the binding
assistant-fact category compares an arm that has had the memo deleted against one that
still has it (P(pass) ~ 1e-10 at any plausible recall rate), and the other three collateral
categories use a raw count-or-tie comparison whose per-category pass probability is ~0.53–0.59
under NO true harm. As registered, the run's headline status is FAIL-SAFETY before any
GPU minute is spent.

**(B) Harness, readiness for competence + pilot on the real trunk: SOUND-WITH-FIXES.** The
code implements v2 faithfully (including A1/A2, which is the problem) and refuses to run
without committed readings/hashes/receipt; no outcome leaks into prompts, edits or
scheduling other than the registered third-breakage stop; no benchmark file is touched.
One blocker: preflight demands git membership and `git show` content equality for every
dependency including the 8.0 GB `models/qwen3-4b.pt` and the 11 MB tokenizer, both
gitignored (B1 high). Two mediums (tool role out of Qwen3 template, B2; safety stop applied
inside the timing pilot, B3).

Fixes are exact and small; none changes the hypothesis.

## Part A — text

### A1 (critical, unreachable gate) — Collateral safety: assistant-authored facts

Text: "Collateral/unchanged constraints: ... assistant-authored facts (n=64 ...) Each
category must have no greater observed failure count under both than text-restate ... A
cost in any category fails safety even if primary control improves. No exemption for
expected assistant-fact loss".

Both/eviction-only replace the SET body — the only place the memo exists — with "." at
SWITCH; NEUTRAL2 then asks for it with "No external copy ... returned to the model after
eviction". Both therefore fails assistant_fact in every source-valid episode except by
six-letter chance; text-restate retains the body. The gate `failures(both) <= failures(text)`
passes only if text-restate also fails all 64: P = (1-q)^64 = 1e-10 at recall q=0.3,
1e-45 at q=0.8. The code enforces exactly this (`decisions`: `passes = candidate <=
comparator`, `safety["passes"] &= all(...)`; test_mechanism_strata_and_binding_fact_cost
asserts `primary_pass and status == "FAIL-SAFETY"` for one extra assistant-fact failure).
So the registered decision is FAIL-SAFETY whenever eviction does what it is designed to do.
This is not "a cost printed next to the benefit" (my F12) — it is a predetermined verdict,
and a 6 GPU-h run cannot inform it.

Fix (text): in the Collateral paragraph replace "Each category must have no greater
observed failure count under both than text-restate; publish discordances, exact harm
tests and intervals. A cost in any category fails safety even if primary control improves.
No exemption for expected assistant-fact loss; print that cost next to the benefit." with:
"User facts, tool facts and the unchanged constraint are binding: for each, with h=both
fails/text-restate valid and r=converse, require one-sided exact McNemar harm p>.05 AND
h-r<=2 (net, the check-39 form; the three tests are reported unadjusted, each must pass).
Assistant-authored facts are the disclosed, pre-registered cost of eviction, NOT a binding
gate: publish paired failure counts, discordances, exact harm p and interval by source
validity, and print that cost in the same table as the primary benefit; the headline claim
must carry the sentence 'eviction forfeits assistant-authored content it removes (x/64 vs
y/64)'. No PASS wording may omit it."
Fix (code): in `decisions`, compute `passes` for user_fact/tool_fact/constraint as
`complete and len(selected)==fixed_n and table["p"]>0.05 and table["b"]-table["c"]<=2`;
for assistant_fact set `passes=None` and exclude it from `safety["passes"]`; add
`report["disclosed_cost"]["assistant_fact"]` with the paired table. Test: hand table with
both failing 64/64 assistant facts and text-restate 10/64 -> status not FAIL-SAFETY, cost
row present; user_fact h=5,r=1 -> FAIL-SAFETY; h=4,r=2 -> passes.

### A2 (high, fails on chance) — Raw count-or-tie comparisons and the raw h<=2 cap

(i) The three remaining collateral categories as written ("no greater observed failure
count") have, under a true null of no harm, per-category pass probability P(h<=r) =
0.564/0.541/0.529 at failure rates 2%/5%/10% with independent discordance (0.59/0.56/0.54
half-correlated). Three categories jointly ~0.17. The exact numbers are in the table below.
The fix in A1 (McNemar p>.05 AND net h-r<=2) gives ~0.95 x ~0.74 per category at a 5%
failure rate; if the author prefers a single screen, McNemar alone (0.95 per category).

(ii) F6 raw cap h<=2 on breakage (my own F6 proposal, which I now correct): with five
scored answers per arm-episode, per-episode breakage is ~5x the per-answer rate. Under
independent discordance the pass probability is 0.86 at 0.1%/answer, **0.54 at 0.2%,
0.27 at 0.3%, 0.05 at 0.5%** (E[h] = 1.3/2.5/3.8/6.2). Development per-answer breakage in
text arms is 0.3–0.8% (check 35 TEXT 1/128, check 38 1/320, check 39 intact 8/256
answers); the placeholder arm in check 39 was 0/256 answers (one-sided 95% upper bound
1.16%/answer). The registered gate therefore passes or fails on the unmeasured tail of
the both-arm's breakage rate, and the matching "third irreversible newly-broken both-only
episode -> stop scheduling" rule fires with probability 0.46/0.73/0.95 at 0.2/0.3/0.5%
per answer, ending the run as FAIL-SAFETY with incomplete denominators. The McNemar part
of F6 is fine (P(p>.05) >= 0.97 throughout).

Fix (text, F6 and Stop rules): replace "h<=2/256" with "h<=5/256" and report the
one-sided exact 95% upper bound "0/256 -> 1.1634%, 5/256 -> 4.0626%"; replace "On the
third irreversible newly-broken both-only episode" with "On the sixth". Pass probability
under no true harm becomes 0.96/0.82/0.42 at 0.2/0.3/0.5% per answer. (A net form h-r<=2
is the alternative; "irreversible" is then undefined for the stop, so keep the raw stop at
6.) Fix (code): `decisions`: `safety["b"] <= 5`; `run_episodes`: `if new_broken >= 6`.
Tests: hand tables at h=5 pass / h=6 fail; scheduling stop at the sixth both-only broken
episode, not the third; `exact_upper(5,256)` == 0.040626 (I recomputed
`exact_upper(0,256)`=1.1634% and `exact_upper(2,256)`=2.4387% as registered).

### A3 (high, false stop on noise) — Competence gate: 12 cells at >=56/64

56/64 per skill/direction was my F5 (single-cell reasoning). v2 applies it to 8 skill
cells plus 4 default cells, all required. Exact binomial: P(one cell >=56/64) =
0.640/0.813/0.932/0.996 at true rates 0.88/0.90/0.92/0.95, so P(all 12) =
**0.005/0.084/0.430/0.948**, P(8 skill cells) = 0.028/0.192/0.570/0.965. Measured
single-shot competence on this trunk for sorting is 0.84–0.92 (check 31 27/32, check 35 SET
29/32, check 34 text_A 59/64), so the leg is INELIGIBLE-by-noise with probability >~0.5
at the sort family's own measured rate, and "any miss stops this four-family leg" makes
that terminal. Default cells are safe (copy 64/64 in development).
Fix (text): ">=52/64 exact live-task/schema successes in every skill cell (81%, exact
one-sided 95% lower bound 0.71) and >=56/64 on each default cell". P(all 12) at 0.90 =
0.887, at 0.92 = 0.982; the Y ceiling at 90% per-answer competence is already 0.59, so
the bar loses nothing the endpoint needs. Fix (code): `competence_gate`: threshold 52 for
skill cells, 56 for "default"; test_competence_boundaries updated to 51/52 and 55/56.

### A4 (medium, reachability disclosed but not quantified) — both vs placement-only

The text pre-registers that eviction's gain over inside-request placement is "at most
5/32 ... and the expected eviction gain is smaller", yet requires a Holm-adjusted
significant both>placement-only contrast for PASS. Exact power (N=256, Holm worst-case
x3 / unadjusted): true gain 2 pts: 0.05–0.09 / 0.13–0.21; 3 pts: 0.10–0.21 / 0.21–0.38;
5 pts: 0.26–0.60 / 0.44–0.78 (discordance 0.25–0.10). So a real 3-point eviction effect
yields FAIL ~85% of the time. This is a registered design choice (kimi K3, retained), and
the readings already say a null "is not evidence of absence or established power"; I ask
only that the sentence be made concrete: append to "Pre-registered expectation": "At a
true 3-point both-minus-placement-only gain the primary contrast has ~0.1–0.2 power at
N=256 (exact, Holm); a FAIL on that contrast is expected under the pre-registered
expectation and is read as 'no demonstrated extra mechanism', never as evidence of
absence." No code change.

### A5 (low) — Minor text items

- "Replies are generated once in an isolated neutral context" — the harness generates
  the identical delay reply three times per delayed episode (DELAY0/1/2, same empty
  context, greedy): 384 redundant 512-token prefills, ~10 GPU-min. Say "generated once
  per delay slot" or generate once and replay (B4).
- The receipt certifies body replacement under a retained cue; FOCUS-2 additionally
  deletes retired cue text from earlier user messages (in-request cues at BACK/CLEAR,
  system-slot cue at SWITCH) in all arms. Add "cue retirement inside earlier user turns is
  an uncertified, arm-shared edit" to the repair-dependency paragraph.
- Preregistration e24afd4 precedes the check-39 launch by 8 s (04:43:02-04:00 vs
  08:43:10Z). It is a valid git anchor; state the margin so it is not read as a rounding.
- check 38's cost line: 8.02 GPU-min reproduces (README line 53).

### Evidence binding — verified

- Template bytes hash to 2658b026...e8e7 (recomputed from the four registered lines, no
  trailing LF); `RECAP_HASH` in code matches; template present in 2ea04e9 and 7d0c244.
- v2 section at 7d0c244 hashes to PINS.v2_section_sha256 and is byte-identical to HEAD's
  section (the handoff append is outside `v2_section`'s slice).
- check36-review SHA 4819d6..., check38-review 44bc88..., check39 summary e5b906... all
  reproduce from the working tree; `repair_gate(real summary.json)` -> True with b=0, c=4,
  p=1 per mode, releases 60/59 vs 59/58, neutral 64/64; check 37 README carries STOP and is
  not pooled anywhere in text or code (`historical_check37="STOP (not pooled; not a v2
  veto)"` is reporting only).
- Check 38 numbers in the prior-ordering paragraph (2/32, 1/32, 11/32 +10/0, 27/32 vs
  11/32 16/0, 31->12->2, T2 12/32, off 64/64) match my check38 review section 1–3.
- Placement is inside the request message in placement-only/both/text-restate
  (`History.request` puts the cue part before the input part in the same user message;
  `validate` rejects a cue-only user turn: "separate moved-cue turn").
- Complete pairs: `validate` rejects any historical user or tool turn without an assistant
  closure; delays are user+assistant pairs with the actual reply.
- Pre-registered eviction bound and expectation text are byte-bound into readings.txt.

### Disposition faithfulness of my findings

Synthesis F1–F3, F5 (bar, but see A3), F6 (form, but see A2), F7 (Multi-IF cut), F8
(prospective check-39 anchor, no retroactive claim), F9 (placeholder imitation = breakage,
`score.placeholder`), F10 (active-cue scope sentence), F11 (both-correct strata,
`decisions.strata.both_correct` + mechanism reading), F13 (complete pairs): faithful.
F12: over-applied — I asked for a separately reported collateral cost "not in the primary
endpoint"; v1 disposition made it a "binding cost gate", which A1 shows is a predetermined
FAIL. Check-38 (a)(b)(c) and section 2.1–2.4: faithfully incorporated, including the
deferred no-answer readout and the run-time-copy caveat. Nothing attributed to me that I
did not say, except "binding" on F12.

## Part B — harness (commit 8f4b76c)

Implements v2: five arms with in-request placement (`current_cue`), event/scope map from
part scopes assigned at construction only (no answer content consulted; `History`
docstring holds), placeholder repair = whole body incl. thinking prefill -> [13] with
header/EOS/closure retained (matches check 37 `Engine.repair` placeholder branch as bound
by check 39; `require(p["ids"])` guards vacuous removal), two unscreened shared priors
forked to all arms (`episode`), four families with executable checkers and imposition
flags, competence/pilot/run/analyze, refusal chain in `preflight` (REGISTERED, review
APPROVED with 0 open high/critical bound to the section hash, launch receipt committed at
HEAD binding one output dir, freeze-commit membership + hashes, `RUNTIME_SOURCES` equal to
frozen bytes, `verify_evidence` anchors/chronology/receipt/STOP), exact McNemar + Holm
(`holm` verified on [.01,.03,.02] -> [.03,.04,.04]), F9/F11/F12, cost cap with pilot
projection 1.25x(256xworst+load) and per-decode-step checks, durable per-request records
(`atomic_json`, hash-named, verified on read), analysis that re-renders every prefill and
recomputes every score from the raw record (`validate_records`). Banks: 768/16/256,
memo 64/256 final (4 per cell) and 16/16 pilot (disclosed); zero semantic-fingerprint
collisions; delay text is exactly 512 tokens; "." is [13]; RNG namespace matches the
registered string. No file under data/bench is referenced; test_eval_data_separation and
test_sealed_guard pass.

### B1 (high, cannot run) — Preflight requires git membership of the 8 GB weights

`preflight` -> `member()` for every manifest file, including `model`
(`config["weights_path"]`, i.e. models/qwen3-4b.pt, 8,045,060,683 bytes) and `tokenizer`
(models/qwen3-4b-hf/tokenizer.json): `git ls-files --error-unmatch`, clean status, and
`git show <commit>:<path>` byte equality. Both paths are gitignored (.gitignore:241-242),
`git ls-files models` lists six unrelated files. The freeze is therefore impossible without
committing the weights, and the fixture only passes because it commits fake marker files.
The handoff discloses this ("final freeze must satisfy that contract") but that contract
is unmeetable and would require editing the frozen generator after freeze (INVALID).
Fix: split `member()` into `tracked_member` (current behaviour) and `hashed_asset`
(exists, not symlink, SHA-256 equals manifest, size recorded; used for manifest roles
`model`, `tokenizer`, `model_config`, `tokenizer_config`, `qwen_default_config` when the
path is gitignored per `git check-ignore`); manifest records `{"path","sha256","bytes",
"tracked": false}`; `preflight` still requires the config/tokenizer_config JSON hashes.
Test: fixture with `.gitignore` covering the model marker -> preflight passes with matching
hash and fails on a one-byte change.

### B2 (medium, renderer validity) — `tool` role is not a Qwen3 chat-template rendering

`initial_history` emits `<|im_start|>tool\n{"tool_fact":87}<|im_end|>\n`. Qwen3-4B's
tokenizer_config chat_template renders tool results as
`<|im_start|>user\n<tool_response>\n{content}\n</tool_response><|im_end|>\n` (and expects a
`<tools>` schema block in the system prompt for tool calls). The v2 text requires "valid
tool-call/return groups" through "one valid chat renderer". The mismatch is arm-shared, so
no primary contrast is biased, but tool_fact recall (a binding safety category) is
measured under an out-of-template role that the model may treat as noise, and the "valid
tool-call/return closure" claim is not what the artifact renders. Fix: render the tool
return as a user message wrapped in `<tool_response>` per the template (keep `kind`
"tool_return"/scope "tool-fact"), and add the minimal `<tools>` declaration to the
system base text; freeze the new strings. Test: rendered ids equal the hard-coded
template rendering for one fixture; `validate` still rejects an unanswered tool group.

### B3 (medium, pilot is "timing only") — Third-breakage stop applied inside the pilot

`run_episodes` counts both-only breakage in every stage; a third such pilot episode (of
16) returns FAIL-SAFETY, no certificate is written, and `run` preflight then refuses
("incomplete/bad stage certificate") — an outcome-based stop at n=16 in a stage the text
registers as "Timing only; no outcome-based changes". With A2's rates this fires with
non-trivial probability. Fix: apply the stop only when `ep["bank"] == "final"`; pilot
records still carry the flags for disclosure. Test: pilot with 3 both-only broken
episodes completes with a PASS timing certificate.

### B4 (low) — Cuts / over-engineering

- Generate the delay reply once per episode (or once per bank, it is context-free and
  greedy) and replay into DELAY0/1/2; saves 384 prefills.
- `member()` reads and `git show`s each dependency twice (content + hash); after B1 this
  only matters for the tokenizer.
- `atomic_json`'s hard-link publication and directory fsync are fine but the
  `refusing output overwrite/retry` also forbids resuming an interrupted run; that matches
  the text ("Resource/cap/interruption -> INCOMPLETE") — state in the handoff that there
  is deliberately no resume.
- 2588 lines for the module is heavy but every block maps to a registered clause; no
  dead code found.

### Leak / benchmark / reproducibility audit

- Outcome use during execution: only `run_episodes`' both-only breakage counter (the
  registered stop) and `memo_source(priors[0])` as a scoring source; neither enters any
  prompt, edit or schedule. `intervene` uses part kinds/scopes only.
- No read of data/bench or BFCL paths anywhere in the three files (grep); tests
  test_eval_data_separation / test_sealed_guard pass.
- Reproducibility: banks are pure functions of the registered seed strings; template
  manifest binds every rendered string and its token ids; records carry input ids, layout
  and edit maps; `analyze` re-renders and re-scores. The one unreproducible element is B1
  (no valid freeze can exist).

## Power numbers (exact, CPU, scratchpad/power.py)

both vs text-restate, N=256, true gain 8 points, one-sided exact McNemar at .05 plus
b-c>=13 (all three required):

| discordance | unadjusted | Holm x2 | Holm x3 (worst) | P(b-c>=13) alone |
|---|---|---|---|---|
| 0.15 | 0.907 | 0.897 | 0.869 | 0.907 |
| 0.25 | 0.796 | 0.696 | 0.636 | 0.844 |

Under the registered rule the 13-net magnitude gate, not the test, binds at low
discordance; at 0.25 discordance the Holm-adjusted test binds. Component contrasts at
small true gains: see A4. Breakage gate and competence gate pass probabilities: A2, A3.

## Findings summary

| # | Severity | Where | Issue |
|---|---|---|---|
| A1 | critical | Collateral paragraph; `decisions` | assistant-fact binding gate is unpassable by construction (P~1e-10); verdict predetermined FAIL-SAFETY |
| A2 | high | Collateral, F6, Stop rules | raw count-or-tie collateral gates pass ~0.53–0.59 each under null; raw h<=2 / third-breakage stop pass 0.54/0.27 at 0.2/0.3%-per-answer breakage |
| A3 | high | Competence gate | 12 cells at >=56/64 pass jointly 0.08/0.43 at true 0.90/0.92 — sort family is measured at 0.84–0.92 |
| B1 | high | `preflight`/`member` | requires git-tracked 8 GB weights + tokenizer; both gitignored; no valid freeze possible |
| A4 | medium | Expectation paragraph | both>placement-only power 0.1–0.2 at the expected 3-point gain; state it |
| B2 | medium | `initial_history` | `tool` role not a Qwen3 template rendering; tool_fact category measured off-template |
| B3 | medium | `run_episodes` | breakage stop fires inside the timing-only pilot and kills the leg |
| A5/B4 | low | various | triple delay generation; uncertified cue retirement note; 8-s prereg margin; no-resume disclosure |

VERDICT (A): UNSOUND as registered-to-be (A1, A2, A3 make the decision predetermined or
noise-driven); SOUND-WITH-FIXES after the three exact text edits above.
VERDICT (B): SOUND-WITH-FIXES — B1 must be fixed before any freeze; B2/B3 before
competence/pilot; the A1–A3 code changes must land in the same pre-freeze commit so the
frozen generator equals the executed one.
