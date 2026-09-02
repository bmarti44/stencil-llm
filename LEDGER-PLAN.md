# LEDGER — instruction ledger + selective amplification (Brian's architecture)

Authorized 2026-09-01. Supersedes E3 (obligation probe) as the next build;
E3 remains registered as an optional upgrade to ledger entry STATUS.

## Why

Our controller only ever implemented SELECTION (query the current hidden
state against candidate spans, amplify the best). It had no notion of
WHICH text is an instruction, and no persistent set. On Multi-IF it was
selecting over whole user turns — instruction text mixed with narrative —
and fired 0 times in the smoke. Miller's architecture is an active SET of
task rules with gated admission and demand-driven readout; we built the
readout and skipped the set. The project's own surviving results are
ledger properties: the sealed +18.5 win used a structured ledger, and the
focus state was linearly READABLE (87.5%) and TRANSPLANTABLE.

## Components (three, small, independently testable)

A. SALIENCE — does this sentence state a persistent requirement?
   A small classifier over user-turn sentences. This is the piece that
   generalizes: "is this an imperative constraining future output" is a
   LINGUISTIC property, not a benchmark property (unlike the checker
   dependency that blocked the obligation gate).
   Labels, free: our synthetic corpora are labeled by construction
   (constraint sentences vs task/filler sentences); IFEval 541 +
   Multi-IF give real positives; ordinary narrative sentences from the
   same prompts give negatives.
   Gate A: held-out F1 >= 0.90 on a LEAVE-ONE-CORPUS-OUT split, and
   >= 0.80 on a hand-labeled sample of 100 Multi-IF sentences the
   classifier never saw. Must be honest about false positives — an
   over-inclusive ledger is the failure mode that killed the raw-span
   version.

B. LEDGER — the held set.
   Entries: {text, token span, pooled trunk key (h20 mean over the span),
   turn introduced, status}. Status is OPTIONAL and defaults to "unknown";
   E3's probe can fill it later. The ledger is explicit and auditable by
   construction (Brian's standing requirement: "transplanting the focus
   and auditing it quickly and easily").

C. SELECTION + EMPHASIS — the EXISTING WaveController, unchanged.
   Query = current h20; keys = ledger entry keys; top-k selected; sustained
   bias over the selected entries' spans (the Opus-validated actuator).
   The ONLY change vs today: keys come from the curated ledger instead of
   raw prompt spans.

## The experiment that decides it (registered BEFORE building)

The trivial version of a ledger already works: re-appending instructions
as text is published at +22.3pts on multi-turn IF. Brian's ruling
(2026-09-01) sets the bar precisely: WE DO NOT HAVE TO BEAT TEXT
RE-APPEND. WE HAVE TO MATCH IT FOR FREE, AND AUTOMATICALLY.

  "for free"        = ZERO added context tokens (text re-append pays
                      tokens linear in the number of instructions and
                      grows every turn; the neural ledger pays none).
  "match"           = NON-INFERIORITY, not superiority. Registered test:
                      the existing Tango paired bound (src/stencil/
                      stats.py), margin 2.0 points, one-sided 95%.
                      A tie at zero cost is a WIN.
  "automatically"   = the ledger is built by the salience classifier from
                      raw text. No "Constraint:" markers, no human
                      curation, no per-benchmark verifiers at inference.
                      An arm that needs marked spans does not count.

ARMS (replayed-history harness, identical inputs, single difference):
  1. base                 — recorded native (free, already on disk)
  2. text-ledger          — the SAME ledger entries re-appended verbatim
                            before the assistant turn (the baseline to beat)
  3. neural-ledger        — ledger entries as attention-bias targets,
                            selective amplification, context UNCHANGED
  4. specificity control  — matched bias mass on non-ledger tokens
PRIMARY (registered): NON-INFERIORITY of neural_ledger to text_ledger on
per-constraint paired outcomes — Tango upper bound on the drop < 2.0
points — WITH neural_ledger context cost = 0 added tokens. That is the
result: same compliance, no context paid, no human in the loop.
SECONDARY: neural_ledger vs BASE (it must do something at all) and
text_ledger vs BASE (confirms the ledger contents are right, and
calibrates the addressable headroom on this harness).
Context tokens added MUST be reported per arm.
SCOPE HONESTY: the actuator can only INSERT content; limit/removal/
restructure families are reported separately and excluded from the primary
(measured: insertable families are 18.5% of Multi-IF constraints).
Slice first: the disclosed diagnostic conversations (~113), ~3 GPU-h.

## Build rules

Small. Three files max: src/stencil/salience.py, src/stencil/ledger.py,
scripts/ledger_eval.py. Reuse ctrb/e2/bench helpers; do not re-implement
generation, spans, or scoring. Red/green TDD; NO vacuous tests (assert on
decoded content and bounded properties). No training beyond the salience
classifier. No new corpora unless a gate demands it.

## Brian's rulings, 2026-09-01 (after the first build)

1. SALIENCE-2 — the finder must be far more general. The v1 regex/logistic
   detector (recall ~0.75, misses buried constraints) is a stopgap. Required:
   - BURIED instructions: constraints inside task sentences ("Write a blog
     post with at least 300 words" -> the clause "with at least 300 words").
     Clause-level spans, not sentence-level.
   - NON-ADDITIVE instructions must be DETECTED just as well: prohibitions
     ("do not", "never", "avoid"), limits ("under 90 words", "at most"),
     tone/manner ("be formal", "sound angry"), format ("in JSON", "as a
     list"). Detection is the ledger's job regardless of whether the
     actuator can act on an entry; what to DO with each entry is a separate
     decision (the actuator's insertion-only limit stays a known, separately
     reported boundary).
   - Being welded to Qwen3-1.7B is FINE (Brian) — the finder MAY read the
     trunk's own hidden states (a token-level span probe) rather than regex.
   GATES (registered): recall >= 0.90 AND precision >= 0.90 on a BLIND
   hand-labeled Multi-IF sample at CLAUSE level; leave-one-corpus-out F1
   >= 0.90; and a TRANSFER test on IFBench prompts (a constraint taxonomy
   the finder never trained on) with F1 reported honestly. Hand-labels are
   reviewed by sol (conflict-of-interest rule).

2. DEPLOY — "super easy for people to use". Target: a pip-installable
   package on top of HuggingFace transformers' Qwen/Qwen3-1.7B (not our
   hand-rolled trunk), exposing one entry point (load model -> generate with
   the ledger on), with salience + ledger + controller weights on the HF
   Hub. Must pass a PARITY test against our verified path (logits within the
   registered drift bound; ledger spans identical). transformers==4.51.0 is
   the known-good pin (bitwise template verification, B0).

3. SEQUENCING: the diagnostic slice still runs with the v1 finder once sol
   clears the build — an UNDER-inclusive ledger only weakens the neural arm,
   so a positive is conservative and a negative is informative about the
   architecture rather than the finder. SALIENCE-2 replaces v1 when it
   passes its gates; DEPLOY packages whatever passes.

## LEDGER-KV (Brian, 2026-09-01): the ledger lives in pinned KV slots

Problem with the in-context ledger: entries point at instruction spans that
must still be IN the context window. Under truncation/compaction — the norm
in long agentic sessions — there is nothing to point at, and "zero context
cost" only holds where re-appending is cheap anyway.

Design: when an instruction enters the ledger, PIN its per-layer K/V columns
(the tensors the trunk computed when it first read those tokens) so they
survive eviction. Later turns attend to the pinned slots; the wave amplifies
attention toward the slots of the selected entries. This makes "out of
reach" LITERAL — the regime of the program's one decisive win (+18.5
sealed: information provably beyond attention's reach, carried by the
wave) — and it is what long-horizon agentic use actually needs (turn 3's
rule binding at turn 200 across compactions). Cost ~115 KB per pinned
token over 28 layers; a hundred instruction tokens is negligible.

Known risk: RoPE bakes position into K. A pinned K from position 50
attended from 5000 after eviction has a distorted relative distance.
StreamingLLM-style evidence says trunks tolerate this with sinks, but it
is EMPIRICAL for Qwen3-1.7B.

GATE (feasibility probe, registered before building): on >= 20 synthetic
multi-turn sessions, evict the middle turns from context, pin the ledger
entries' KV, and measure late-turn adherence for (a) evicted-no-pin,
(b) evicted-pinned, (c) evicted-pinned + wave amplification, (d) full
context (ceiling). Pinning must recover a material fraction of the
(d)-(a) gap without degeneracy (perplexity/length checks). If (b) is
degenerate, position-handling (re-indexing pinned K, or a sink) is the
next design question, not more amplification. Sequenced AFTER the
in-context diagnostic slice (the baseline) and reusing its harness.
Deploy must keep bias injection abstract over ATTENTION COLUMNS, not
context spans, so pinned slots drop in later.

## Amendments after sol's verification (2026-09-01, results/ledger-verify-sol.md)

- RETRACTED: "an under-inclusive ledger only weakens the neural arm". It
  weakens BOTH arms, reduces discordance, and makes non-inferiority
  EASIER. Hence primary validity now REQUIRES non-vacuity: text_ledger
  must beat base (n10 > n01 on eligible outcomes) and the ledger must be
  active (>= 1 aged entry selected) on every credited turn.
- ESTIMAND: eligible outcomes = AGED (origin turn < current turn)
  constraints in FIXABLE_FAMILIES only; fresh constraints are excluded
  from the primary (the treatment holds aged entries only).
- CLUSTERING: the primary bound is a CONVERSATION-CLUSTERED one-sided 95%
  upper bound on the mean paired difference (text - neural, points),
  cluster = conversation, via t on the per-conversation mean differences
  (fallback: cluster bootstrap, 2000 resamples, seed 0). Tango on pooled
  cells is reported as descriptive only.
- SLICE STATUS: the ~113-conversation diagnostic slice is a FALSIFICATION
  SCREEN (all-concordant bound already exceeds the margin at n=85); a
  confirmatory NI needs the complete 909-conversation cohort and is a
  separate registered run.
- VALIDITY GATE (primary_claim_valid): complete cohort; registered
  top_k/dose/max_new/deadline; neural context tokens MEASURED per turn (not
  a literal); timeouts+truncations <= 2% per arm; real-salience path
  asserted (segmenter identity check); provenance hashes cover
  salience_weights.json, qwen3.py, ctrb.py, e2.py, stats.py, tokenizer,
  and the vendored verifier tree.
- CONTROL: specificity = width- and position-matched NON-ledger spans at
  the SAME dose (mass_matched_nonconstraint_control from e2.py), reported
  directly against neural (neural - specificity, clustered bound).
- LINKAGE: each ledger entry records the instruction_ids whose constraint
  clause it overlaps (e2.constraint_span_records); credit is only counted
  where the credited constraint's entry was selected.
- top_k=2 and dose 3.0 are FROZEN EXPLORATORY choices; not tuned after
  outcomes are viewed.
- FIX-ROUND readings (2026-09-01, flagged for sol re-verification):
  (i) Multi-IF has no "Constraint:" markers, so entry<->instruction linkage
  is ORIGIN-TURN granularity (entry links to every id its turn introduced);
  disclosed in records as linkage_granularity; mildly lenient to neural.
  (ii) the matched control is ledger.matched_nonledger_control (same-width,
  nearest-position windows disjoint from every entry, same dose), NOT
  e2.mass_matched_nonconstraint_control (which is the diffuse complement).
  (iii) "credit only when selected": an uncredited neural pass scores as a
  FAIL (fail-closed), not an excluded pair; raw rate reported alongside.
- SALIENCE-2 RESULT (2026-09-01, v2b clean refit after the IFEval-training
  breach, see WORKLOG): gate 1 UNMET on two blind Multi-IF draws — recall
  0.854 / 0.884 vs bar 0.90 (precision 0.95 / 0.94); LOCO F1 0.973/0.945
  (met, linguistic backend); IFBench transfer F1 0.68 (reported); buried
  recall 0.88 linguistic / 0.97 trunk-probe. DEFAULT_BACKEND=linguistic
  (CPU-only, deploy-friendly). Unmet gate kept as a strict xfail with the
  numbers. Brian decides: accept 0.88 recall as v2, or fund a third round
  (blind-draw failures are new constructions each time — rule overfit risk).
- LEDGER-KV PROBE RESULT (2026-09-01, 20 synthetic sessions, 56 aged
  constraints, results/qwen/ledger-kv-probe): full 42/56, evicted 16/56,
  pinned 36/56, pinned+wave(3.0) 35/56. Pinning recovers 0.77 of the
  full-evicted gap (paired 14 better / 1 worse), degeneracy 2/20 vs 1/20
  evicted → GATE MET under the no-reindex position policy. The wave dose on
  pinned columns adds NOTHING and degenerates 8/20 (truncations 9 vs 4):
  the pinned MEMORY is the mechanism; amplification of it is harmful here,
  consistent with the always-on-bias finding (B3 dev gate). Pending
  independent verification before any design decision.
- KV PROBE VERIFICATION (fable, 2026-09-01): CONFIRMED with qualifications.
  Evicted arm == true single-turn baseline (0/4 both on s0); dropping the
  turn-1 scaffold collapses output (position-0 sink is load-bearing);
  scoring order verified 20/20; bias row alignment correct; RoPE
  distortion is ZERO here (positions continue; relative distances are the
  true ones) — long-horizon untested (max 761 tokens). Weakened wording:
  degeneracy threshold was unregistered (now: truncated or rep4>0.5, in
  the runner); pinned is as degenerate as full; history turns were decoded
  through a double-wrapped template (fixed: raw-context greedy); the
  same-width non-constraint pin control was n=1 (0/4) — now a registered
  fifth arm (pinned_control). RERUN of the 20 sessions required before the
  result is cited.
- FIX ROUND 2 (2026-09-01, after results/ledger-reverify-sol.md): matched
  control never raises (impossible windows -> tier "none", turn excluded
  from neural-vs-specificity, control_incomplete recorded; conv 145 t2 is
  the one known case); validity gate now checks per-record identity,
  expected turns (1805 for the cohort), arm set, echoed config, <=2%
  timeouts+truncations in EVERY arm, and a NEW registered threshold:
  ledger must have a selected linked entry on a strict MAJORITY of
  eligible constraints; clustered bound = t + one-whole-cluster-flip
  continuity correction (100/k points), chosen by exact simulation
  (plain t and percentile bootstrap both 8.31% false-pass at the
  registered size; corrected 4.90%); wave.py/bench.py/determinism.py
  hashed; preflight dry-constructs every control. Pending sol round 3.
- ROUND 3 (2026-09-01, results/ledger-reverify3-sol.md): crash, provenance,
  bound RESOLVED; validity PARTIAL — majority-selection gate gameable at
  50.03%. RULINGS: (i) selection COVERAGE gate registered at >= 0.90 of
  eligible constraints (diagnostic preflight: 81/85 = 0.953 have a linked
  entry, so attainable); (ii) text_beats_base must hold WITHIN the selected
  subset, and the unselected subset's text-vs-base cells are reported
  separately and must not be all-concordant-failing; (iii) the diagnostic
  slice is REGISTERED AS FALSIFICATION-ONLY: a zero observed difference at
  43 clusters yields a 2.33-point corrected bound > 2.0, so the slice can
  REJECT non-inferiority (or show text/neural vs base effects) but can
  never establish it; positive NI requires the full 909 cohort.
- ROUND 4 (2026-09-01, results/ledger-reverify4-sol.md): coverage gate,
  falsification-only rule, laundering defences all VERIFIED. One HIGH:
  text-beats-base non-vacuity was POOLED; a record with text worse in
  605/908 conversations still validated. RULING: non-vacuity is
  CONVERSATION-CLUSTERED — the registered one-sided 95% LOWER bound
  (same continuity-corrected clustered machinery, sign-flipped) of the
  per-conversation mean (text - base) on SELECTED eligible outcomes must
  be > 0; pooled n01>n10 kept as descriptive only.
- ROUND 5 (2026-09-01, results/ledger-reverify5-sol.md): VERDICT — the
  113-conversation diagnostic slice is LAUNCHABLE as a falsification-only
  screen; the full 909 cohort is NOT until two HIGHs close. RULINGS:
  (i) clustered text-vs-base non-vacuity is over ALL eligible outcomes
  (registered lower bound > 0), with the selected-subset bound retained as
  a second required gate (both must hold); (ii) NEW registered gate:
  conversation-clustered neural-vs-base superiority on all eligible
  outcomes (registered lower bound > 0) — "neural must do something at
  all" is now mechanical, not prose.
- FIX ROUND 5 reading (2026-09-01): the neural-vs-base superiority gate
  uses CREDITED neural (fail-closed on unselected cells), the estimand's
  neural; raw neural would let unselected cells launder the gate. Flagged
  for sol round 6.
- ROUND 6 (2026-09-01, results/ledger-reverify6-sol.md): LAUNCH — the 113
  slice as a falsification-only screen AND the full 909 cohort as the
  confirmatory run. Runner frozen at this commit for both; any further
  edit re-opens verification. GPU sequencing once the GPU is free:
  (1) sealed single-turn confirmation resume (574->1024) + gate;
  (2) 5-arm KV probe rerun (20 sessions); (3) 113 slice; (4) 909 cohort.

## KV PROBE v2 VERIFICATION (2026-09-02, sol xhigh, CPU-only)
Verdict CONFIRMED-WITH-QUALIFICATIONS (results/ledger-kv-verify2-sol.md). Arithmetic exact. Creditable: pinned 31/56 vs evicted 15/56 vs full 41/56 (recovers 0.615 of gap); pinned − control = +0.196 with an approximate (not exact-column) mass match. Not creditable: pinned_wave (degenerate in 13/20 sessions, 12/20 truncations) — consistent with v1: the wave dose on pinned columns degenerates. Open items for the next probe iteration: exact-column control matching, full provenance hash set, token IDs in records, docstring.

## ROUND 7 AMENDMENT — validity gate: truncation cap (registered 2026-09-02, pre-launch of the 909; Brian: "fix the other issues")
Finding (fable, orchestrator-verified): the recorded Multi-IF base arm truncates 185/1805 = 0.1025 of
late turns at max_new=1024 (results/qwen/b4-multiif-base), so the registered "<= 2% timeouts+truncations
in EVERY arm" gate (above, and scripts/ledger_eval.py MAX_TIMEOUT_TRUNCATION_FRACTION) cannot pass for
any arm, base included. The 113 slice confirms it live (base 6.5%, neural 9.3%).
Amendment (replaces the absolute per-arm cap; the 909 does NOT launch until sol re-verifies):
1. Timeouts: absolute cap stays at <= 2% per arm (timeouts are a runner defect, not a model property).
2. Truncations: PREFLIGHT records the base late-turn truncation fraction t_base (descriptive, from the
   recorded base). Each treatment arm must satisfy t_arm - t_base <= +0.02 (excess-over-base
   non-inferiority). A treatment arm that truncates more than +2 pts over base FAILS validity.
3. Scoring rule for truncated turns: a truncated response is scored by the verifier AS IS (it is a
   fail for any constraint it did not complete); truncated turns are NEVER excluded from the denominator.
4. Both t_base and every t_arm are reported in the summary next to the adherence numbers.
Disclosure: this replaces a gate the base arm was already failing before any treatment ran; it is not
a post-hoc loosening in the treatment's favor — a treatment arm still cannot hide degeneration.

## RE-SCOPE + PREREGISTRATION v2 (2026-09-02) — after the single-turn stop-loss
The single-turn IFEval line is CLOSED (data/b3/conf-v45.jsonl confirmation: +0.39 pts, p=0.389, +9
truncations; results/qwen/b3-deficit-conf-s0.json). It is the registered primary negative; no variant
iteration on single-turn IFEval. The sealed file data/bench/ifeval_input_data.jsonl remains unused.
Successor claim (only if the gates below pass): "A target-blind instruction ledger with KV retention
improves compliance with active, aged constraints under context pressure on multi-turn benchmarks,
without increasing stale-constraint adoption, truncation, or validity failures." Not "general
instruction-following improvement"; unamplified pinning is "retention", not "wave", unless amplification
independently beats an exact-column control without degeneration.
Benchmark family (3), Holm-adjusted at one-sided alpha = 0.025 per test:
 P (primary):   Multi-IF 909 cohort, aged FIXABLE constraints, credited neural arm (ledger runner as
                amended by ROUND 7). Gate: clustered lower bound of (neural - base) > 0 on all-eligible;
                text_beats_base; coverage >= 0.90; ROUND 7 validity.
 S1 (secondary): IFBench held-out (constraint taxonomy disjoint from Multi-IF), same estimand; gate:
                paired McNemar one-sided p < 0.025, CI lower bound > 0.
 S2 (secondary): buried-constraint long-context set (data/b3 held-out templates, constraint stated
                >= 2048 tokens before the query); gate as S1.
 Safety gate in EVERY benchmark: truncation excess-over-base <= +2 pts; stale-constraint adoption not
                above base (clustered NI bound < 2.0 as registered).
 Generalization = P passes AND >= 1 of {S1, S2} passes with all safety gates intact; the single-turn
                negative is disclosed as the scope condition in every report and the model card.
 n: P is fixed at 909 (1805 late turns). S1/S2 n set by power analysis at 80% for a +3 pt paired
                effect before either is run; recorded here before launch.

## SALIENCE-2 GATE 1 RE-REGISTRATION (2026-09-02)
Old gate: recall >= 0.90 AND precision >= 0.90 on a BLIND Multi-IF draw. Observed seed-4 blind
TP 76 / FP 5 / FN 10 -> recall 0.884, Wilson 95% [0.80, 0.94]. A third small draw would pass by
sampling noise with P ~ 0.3-0.5 (fable), so it is not a test. New gate 1: Wilson 95% LOWER bound of
recall >= 0.85 AND precision >= 0.90 on ONE blind draw with >= 250 positive constraints, IFEval-free,
drawn and hashed before the finder is run. Budget reconciliation (kimi): the end-to-end surfacing
target is coverage >= 0.90 on the 909 (measured by the runner); the finder gate is a component
floor, not a multiplicative guarantee — recorded so the two are not read as jointly implying 0.81.
Trigger: run the new gate only if the 113 slice / 909 coverage < 0.90; otherwise the finder is
accepted as-is under the coverage gate and gate 1 is reported as "unmet under the old wording,
superseded".

## FOCUS LADDER v1 (registered 2026-09-02, after fable/sol/kimi review of v0 — results/focus-ladder-review-{fable,sol,kimi}.md)
Goal (Brian): a generalized Miller-inspired focus mechanism; fast small proofs before any larger run.
v0 verdicts: fable "run H1 after cuts"; sol "REJECT v0; ACCEPT H1 after cuts; H2 not a gate; H3 needs a
registered cache harness + disjoint confirmation"; kimi "H1 echo = recency not availability; keep echo_only;
cut per-head CI gate and dose grid". v1 adopts every cut.

### H1 (the only rung that runs now) — retention vs re-injection, 20-session KV-probe harness
Harness: scripts/ledger_kv_probe.py, ALL arms in ONE job at the current default max_new=512 (no mixing
with the v2 320-token artifact; the gap is recomputed in-job). Focus set = the harness's marked
"Constraint:" spans → results are labelled "marked/oracle focus", not automatic target-blind selection.
Arms: full | evicted | pinned | pinned_control (exact-column, v3) | echo_only (evicted + echo) | pinned_echo.
Echo = src/stencil/ledger.text_ledger_context rendered byte-for-byte from the aged spans, inserted before
the final user <|im_end|>; chat-control tokens rejected; added token count recorded.
Metrics per arm: aged-constraint pass (56), truncation, timeout, rep4>0.5, degenerate sessions, invalid
output, quoting rate (response reproduces >= 8 consecutive echoed tokens) and a quoting-excluded secondary
pass rate. Safety: absolute timeouts <= 2%; truncation excess over `full` <= +2 pts; degenerate sessions
not above `full` in-job.
Reading (factorial contrasts, in-job gap = full - evicted):
  pinned - evicted        (availability without recency)
  echo_only - evicted     (recency/re-injection without availability)
  pinned_echo - echo_only (what KV residency adds on top of re-injection)
  pinned - pinned_control (specificity)
Decision rules (integer outcomes; every outcome has a reading):
  ADVANCE-RETENTION if pinned > pinned_control AND pinned_echo > echo_only AND pinned_echo recovers
    >= 0.85 of the in-job gap with safety intact.
  RE-INJECTION-ONLY if echo_only recovers >= 0.85 of the gap but pinned_echo <= echo_only: the product is
    text re-injection (already the 113-slice text_ledger result: +2.8 pts pooled, p=0.012).
  FAIL / DO NOT ADVANCE for every other outcome (including recovery in [pinned, 0.85 gap)).
Cost: ~1 GPU-h. Reviewer pass (fable/sol/kimi) on the artifact before any next rung.

### H2 — DROPPED as a gate (self-passes under the null; no valid teacher-forced target). May return later as
a non-gating ranker only after held-out reference continuations exist.

### H3 — trust-region wave on pinned KV: NOT registered yet. Preconditions: H1 ADVANCE-RETENTION, then a
frozen rejection policy (raw-vs-steered top-1 ratio >= 0.5; dose halving; layer-pair drop order; emit-raw
fallback; press/reject counters), CPU formula tests, one frozen-config pilot on the 20-session cache
harness with survival >= 5% and no safety regression. Confirmation, if any, on a hashed cohort disjoint
from any development data, registered with its own n before outcomes are viewed. Not the current 909.

## H1 OUTCOME (2026-09-02): FAIL / DO NOT ADVANCE under the v1 clause; substantive contrasts confirmed
results/qwen/ledger-kv-probe-h1 + results/h1-review-{fable,sol,kimi}.md. pinned_echo 46/56, echo_only 36, pinned 33,
pinned_control 20, evicted 15, full 41; wave-on-pinned not creditable at any dose. Registered safety clause breached
by a single truncation (1/20 vs 0/20 = +5 pts > +2). DISCLOSURE: the clause was written in points on an n=20
session denominator, which is zero-tolerance; the amendment below moves to integer event counts and is
registered BEFORE H1′ runs. H1 is not retroactively passed.

## H1′ — automatic-selection replication (registered 2026-09-02, before any outcome is viewed)
Same 20 sessions, same harness (scripts/ledger_kv_probe.py), max_new 512, one job. Focus set = spans selected
AUTOMATICALLY by the registered salience finder (src/stencil/salience2.py, DEFAULT_BACKEND, hashes in meta) on
the raw history — no "Constraint:" marks are read by the arms. Arms: full | evicted | pinned | pinned_control
(exact-column) | echo_only | pinned_echo | full_echo (fable: does recency help even without eviction?). No
wave-dose arms (killed at H1). Metrics as H1 plus `invalid_output` (empty / non-text / chat-token leakage) and
per-session selection coverage of the marked constraints (reported, not gated: it is the automatic-vs-oracle
bridge). Echo rendered byte-exact by ledger.text_ledger_context from the SELECTED spans; fix the dangling
" Constraint" token bleed fable found (span window ends at the clause boundary).
Safety (integer counts, in-job): timeouts 0; truncation events per arm <= full + 1; degenerate sessions
(rep4 > 0.5) <= full; invalid_output events <= full.
Decision rules identical to H1 (pinned > pinned_control AND pinned_echo > echo_only AND pinned_echo recovers
>= 0.85 of the in-job gap AND safety intact → ADVANCE-RETENTION; echo_only >= 0.85 but pinned_echo <= echo_only
→ RE-INJECTION-ONLY; else FAIL). Additional reading, not a gate: full_echo − full (recency without eviction) and
automatic coverage vs the oracle spans.
Cost ~1 GPU-h. Reviewer pass (fable/sol/kimi) before any next rung. If ADVANCE-RETENTION: next = 909 Multi-IF
text_ledger confirmation under ROUND 7 (already registered), NOT an H3 wave pilot.

## PUBLISH GATE (Brian, 2026-09-02): Hub release `bmarti44/stencil` only after automatic long-horizon agentic benefit is shown
Precondition, all registered before outcomes are viewed: (1) H1′ ADVANCE-RETENTION or RE-INJECTION-ONLY with the
AUTOMATIC finder (no oracle marks); (2) a long-context / long-horizon / agentic benchmark (selection registered
below after the 2026-09-02 research round) on which the automatic mechanism beats the equal-context base with
a clustered lower bound > 0 under ROUND 7 safety, in a run the orchestrator did not tune on; (3) fable/sol/kimi
sign-off on the artifact. The model card must carry the single-turn negative and the "retention/re-injection,
not amplification" qualification. Deploy package: deploy/stencil_wave (empty ledger == OFF bitwise).
