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

## TRUNK SIZE DECISION (Brian, 2026-09-02): prepare Qwen3-4B in parallel; do not slow the ladder
Current ladder (H1′, 909 text_ledger confirmation) stays on Qwen3-1.7B where harnesses and fixtures exist. In
parallel, the trunk is generalized to Qwen3 dense sizes (brief tools/codex-agents/qwen3-4b-trunk.md) with a
bitwise 1.7B regression gate, and Qwen/Qwen3-4B is converted and parity-checked so the AGENTIC stage (benchmark
registered after the 2026-09-02 research round) can run on 4B, where base tool competence is less likely to mask
the mechanism. Cost note: 4B is ~2x slower per token; budgets are re-estimated per benchmark before launch.

## PUBLISH-GATE BENCHMARKS (registered 2026-09-02 after the fable/sol/kimi research round; results/agentic-bench-synthesis.md)
Leg A (agentic): BFCL V3 multi-turn (Apache-2.0; predefined user turns; executable verifier; simulator-free), sealed
stratified 64-case cohort (16 × base / missing_params / missing_functions / long_context), hashed before any run; a
DISJOINT 32-case dev slice for preflights. Arms: base | ledger (automatic finder + KV pin + echo, the H1′ mechanism) |
random-span control (token-matched echo from prior user turns, same template, same pin budget). Trunk: the smallest
Qwen3 that passes the competence preflight (≥ 15% multi-turn pass on the dev slice; 1.7B is expected to floor at
~8–10%; Qwen3-4B prepared in parallel). Primary: paired-by-episode LB(ledger − control) > 0, cluster-robust, one-sided
α = 0.025 (Holm with Leg B). Safety: ROUND 7 + tool-call validity excess ≥ −2 pts + echo-copy exclusion.
Leg B (long-horizon instruction retention under native pressure): the registered S2 buried-constraint set extended to
≥ 8k tokens of context before the query (native eviction), same three arms, same estimand; plus the already-registered
Multi-IF 909 text_ledger confirmation. RULER variable-tracking 8k/16k as a reported-only sanity leg.
Preflights before the sealed cohort: base competence (dev slice), finder recall ≥ 0.80 on 100 labelled BFCL
instruction/schema spans, BASE-vs-BASE rerun variance. Blockers: OpenAI-compatible chat/tool shim for the trunk;
non-thinking mode fixed and disclosed; Qwen3-4B parity.
Falsifier: LB(ledger − control) ≤ 0 on Leg A at registered n with safety intact; or ledger beats base but not control;
or the gain vanishes under native pressure. A Multi-IF-only pass is insufficient for the word "agentic".
Excluded and why: VerIFY (dataset unreleased), Lost-in-Conversation and tau2 (need an LLM user/shard simulator; no
OpenAI key; simulator noise in a confirmatory run), HANDBOOK/SOP-Bench (frontier floor; SOP-Bench CC-BY-NC),
LongMemEval/LoCoMo (facts not instructions; > trained context; LoCoMo CC-BY-NC), SEQUOR (LLM judge; license unknown).

## GENERALIZING SELECTION — G0 PILOT (registered 2026-09-02, before any run)
Data lineage: fit/select-on = OASST2 (chat) + APIGen-MT-5k (tool) subsets under data/g0/, hashed; evaluated-on = Multi-IF, BFCL V3, S2 (data/bench/). Disjoint by construction and enforced by tests/test_eval_data_separation.py + the Bash guard (commit e19f67f).
Trigger: Brian, "we need to do something that generalizes." Evidence: every selector so far was hand-built for one
benchmark's instruction style (salience2 coverage 0.98 on Multi-IF, recall 0.065 on BFCL sentences against a
mechanical retention oracle); the selective-regex draft was withdrawn 2:1 (results/agentic-salience-review-*.md);
deep web research by fable/sol/kimi (results/research-generalizing-*.md, synthesis in
results/research-generalizing-synthesis.md) established: attention heavy-hitters fail on delayed need (SCBench),
learned write-time policies transfer only when measured leave-one-corpus-out, label-free model-derived importance
exists (KVzip), protocol invariants are protected by role, and Miller's selection is read-time.
Program (in order; each step gated on the previous): G0 audit → zero-training policies scored by oracle recovery →
G1 learned ranker ONLY if no zero-training policy recovers ≥ 0.80 of oracle utility on BOTH corpora.
G0 oracle (label-free, deployment-matched): utility(span) = mean teacher-forced NLL on later REFERENCE tokens with
the span's KV columns evicted (QwenFocusCache.evict) minus NLL full. CORPUS SEPARATION (Brian, 2026-09-02: "if you train
on the results of the eval, isn't that going to invalidate everything?"): the gate benchmarks (Multi-IF, BFCL V3)
are EVALUATION ONLY — nothing is fit, chosen, or tuned on them, including the choice among zero-parameter
policies. The oracle, policy selection, and any learning use only DISJOINT public corpora: a generic multi-turn chat
corpus (OASST2 English branches; reference = the base model's own greedy response, self-distillation) and a generic
tool-use corpus with gold calls (APIGen-MT-5k, fallback ToolACE; reference = gold assistant tool calls), fetched and
hashed before use with licenses recorded (data/g0/MANIFEST.json). The generalization claim is zero-shot transfer of
a selector chosen entirely elsewhere to two unseen benchmark families with different instruction styles.
Never delete text to simulate eviction; never use answer
literals as the label; position-matched null spans (same role/length/age) are the noise floor.
Pilot (this registration): 30 dialogues per disjoint corpus (chat, tool) on 1.7B, ≤12 candidate + 12 null spans each, top-3 joint-eviction
check; policies (a) role rule, (b) recent+sinks, (c) BM25 archive retrieval with the current turn as query,
(d) salience2 held-out finder, (e) attention mass (predicted-failure control), all at one fixed budget B.
Pilot readouts (reported, gating only the NEXT step): (1) seconds/dialogue (a 1k-dialogue oracle is launched only
if ≤ 6 GPU-h projected); (2) signal exists iff the fraction of candidate spans with utility above the null p90
exceeds 0.10 on both corpora — else G0 is declared uninformative at this granularity and the span unit is
re-registered before any retry; (3) recovery table per policy per corpus. Decision rule after the pilot: if any
zero-training policy recovers ≥ 0.80 (null-adjusted) on both disjoint corpora, it becomes the registered selector,
applied UNCHANGED to the gate benchmarks, and G1 is NOT built; if the best is in [0.50, 0.80), G1 is registered with leave-one-corpus-out floors (AUROC ≥ 0.80 held-out,
recovery ≥ 0.50, beats the best zero-training policy under joint eviction with a paired 95% CI excluding 0); if
< 0.50 for every policy, the mechanism's generality is reported as unsupported and the publish gate stays closed.
Harness precondition for any BFCL arm run (from results/agentic-salience-review-fable.md CRITICAL): system prompt +
tool schemas are never-evictable in EVERY arm; the pin budget covers user/tool columns only; the random-span
control is token-matched from the same role pool as the treatment. The failed finder preflight (78/100) is recorded
as FAILED and superseded by this program; the 100 viewed labels are never reused.

## GENERALIZING SELECTION — G0 PILOT, AMENDMENT v2 (registered 2026-09-02 after fable/kimi/sol review of v1; before any pilot number is read)
Reviews: results/g0-registration-review-{fable,kimi}.md (SOUND-WITH-FIXES) and -sol.md (UNSOUND: three CRITICALs,
all accepted). Amends the v1 text above; where they conflict, v2 governs.
0. DEVELOPMENT LINEAGE (sol G0R-1, CRITICAL; replaces v1's "zero-shot" wording): Multi-IF, BFCL V3, IFEval/IFBench,
   and S2/B3 were inspected before this registration and influenced the candidate policy family, the role
   protections, the salience2 segmenter/floors/backend, and the evaluation harness. They are NOT untouched
   confirmation sets; later Multi-IF/BFCL results are post-development evaluations and are reported as such. G0
   outcome selection is restricted to the frozen data/g0 subsets named in data/g0/MANIFEST.json; no result from
   Multi-IF, BFCL, IFEval/IFBench, S2, or a model response to those sets may alter parameters, thresholds, policy
   eligibility, budget, renderer, or tie-breaks after this amendment. A zero-shot generalization claim requires a
   separately registered benchmark family with no prior data, response, label, checker, template, or policy-design
   contact; it will be named in a later registration BEFORE it is opened (candidates are not listed here to avoid
   contact). S2 is a within-B3 template holdout and is not independent evidence for any B3-trained policy.
1. Lineage correction (fable F1, HIGH — the third leakage path): S2 is NOT under data/bench; it is synthesized from
   data/b3 templates (salience2.synthesize_buried / _BURY_TEMPLATES, template_parity split), the same generator and
   constraint families the salience2 finder was refit on today. S2 is therefore EXCLUDED from any claim involving
   policy (d) and remains a secondary leg only for policies with no fitted parameters. evaluated-on = Multi-IF and
   BFCL V3 (data/bench/). Enforcement adds a CONTENT test (zero 8-gram overlap between every data/g0 text and every
   data/bench prompt; MANIFEST sha re-verified) in tests/test_g0.py; the path scan and Bash guard are defense in depth
   only (fable F4: the guard is bypassable by script name, cp/ln, or shell variables).
2. Policies (d) salience2 finder and (e) attention mass are CONTROLS, ineligible to become the registered selector.
   (d) is fit on data/b3, a synthetic corpus built from the IFEval instruction taxonomy with vendored IFEval checkers
   and hand features encoding those categories; today's "held-out 0.98 coverage on Multi-IF" measured taxonomy match,
   not generalization, and is withdrawn as evidence. The eligible selectors are (a) role rule, (b) recent+sinks,
   (c) query-time archive retrieval — all parameter-free.
3. Budget (fable F10): B = 25% of the evictable columns (age ≥ 1, excluding the protected prefix and columns 0–3),
   computed identically in the pilot and in any later gate run; B never depends on oracle utilities.
4. Spans (fable F6–F8): candidates and nulls have age ≥ 1 (the current turn is protected in every policy); no span
   contains columns 0–3 (attention sinks, protected in every policy); a null shares no column with any candidate or
   other null (drop the candidate if no such window exists). Span→column mapping is asserted on the chat-templated
   token ids with the pinned tokenizer (kimi F2.1); cache restore is checked checksum-identical before each eviction.
   KVCache.evict (src/stencil/qwen3.py:70) retains original RoPE positions with no re-indexing — verified in code.
5. Signal test (kimi F3.1, fable F9): "fraction above null p90 > 0.10" is the null expectation and is withdrawn.
   Signal exists on a corpus iff a one-sided permutation test of median(candidate utility) − median(matched-null
   utility) > 0 rejects at p < 0.05 under a dialogue-clustered bootstrap, AND the fraction of candidates above the
   corpus-pooled, bucket-stratified null p90 is ≥ 0.20 (one-sided 95% null bound at n=360 is 0.126). Assessed and
   reported per corpus; the tool arm is not stopped by a chat-arm failure.
6. Selection vs confirmation (kimi F3.2): the five policies are compared on the 30 pilot dialogues per corpus
   (selection set). The best eligible policy is then CONFIRMED on a fresh, disjoint 70 dialogues per corpus drawn
   from the stored ≤200 subset (ids hashed before the run). Registration of a selector requires, on the confirmation
   set, per-corpus null-adjusted recovery ≥ 0.80 with a dialogue-clustered bootstrap 95% lower bound ≥ 0.70, on BOTH
   corpora; [0.50, 0.80) → G1 registered with leave-one-corpus-out floors; < 0.50 → generality unsupported.
   Recovery is measured by JOINT EVICTION (sol G0R-4, CRITICAL; additive sums of single-span utilities are
   explanatory readouts only and never govern promotion): for each policy, evict exactly the evictable columns it
   would discard at budget B and teacher-force the reference; ΔNLL_policy = NLL_policy − NLL_full;
   ΔNLL_all = NLL(all evictable columns evicted) − NLL_full; recovery(policy) = 1 − ΔNLL_policy / ΔNLL_all, per
   dialogue, clipped to [0, 1], micro-averaged over a corpus with macro reported; dialogues with ΔNLL_all below the
   null-eviction noise (matched random discard set of the same size, 3 draws) are excluded from the average and
   counted. The random-discard set at the same B is the control every policy must beat. Ties among passing policies
   go to the higher min-over-corpora recovery, then simplicity (a) < (b) < (c).
7. Corpora: record the license and origin of each subset in MANIFEST.json (APIGen-MT-5k is CC-BY-NC-4.0, τ-bench
   retail/airline origin, domain-adjacent to BFCL travel_booking — disclosed; ToolACE, Apache-2.0, preferred if its
   dialogues meet the ≥3-turn/tool-output criteria). Greedy chat references use the non-thinking template
   (<think>\n\n</think> prefix) used at scoring. Tool utility is reported on argument-value tokens (primary) and the
   whole call (secondary).
8. Claim wording (fable F5): the candidate policy FAMILY was designed after inspecting Multi-IF and BFCL behaviour;
   the model card discloses this. What may be claimed if (a)/(b)/(c) passes and then holds on Multi-IF and BFCL: "a
   parameter-free read-time retention rule chosen on OASST2/ToolACE also holds on the two development benchmark
   families it was designed around" — a post-development evaluation, not zero-shot transfer (item 0). The word
   "zero-shot" is reserved for the later, separately registered no-contact family. Nothing is claimed for selectors
   with fitted parameters.
10. Deployment matching (sol G0R-6): the protected prefix (system + schemas, columns 0–3) and a fixed recent window
   (the current user turn plus the most recent 256 columns before it) are OUTSIDE the candidate pool, outside the
   null pool, and outside B, in the oracle and in every policy; BM25 and attention-mass queries read only the
   current user turn and rank only spans outside the recent window. Oracle mass is never charged for columns that
   deployment exempts.
11. Naming (sol G0R-7): the measure is "reference-conditioned counterfactual utility" — self-labeled on OASST2 (the
   base model's own greedy path; a local sensitivity measure of support for that path, not trajectory success) and
   gold-conditioned on ToolACE/APIGen (gold continuation tokens are labels of the corpus, not of the benchmarks).
   The pilot's histories (corpus prior turns / gold trajectories) differ from the gate harness's model-rolled
   histories; the cache intervention is matched, the history distribution is not — disclosed in every report.
9. In-flight run: the g0-oracle-pilot coder (brief v1) may complete its 2+2 timing check; any 30+30 records it
   produces under v1 span/budget rules are a pipeline shakedown, reported but NOT evidence. The v2 rules are applied
   by a follow-up brief before the selection and confirmation runs.

## SELECTOR v2 — POST-DEVELOPMENT EVALUATION, LEG B (registered 2026-09-03, before any Multi-IF arm outcome)
Data lineage: SELECTOR fit-on = data/classifier/{kimi, kimi-ctx, kimi-scope, *-enrich} (hand-written by kimi-k3, sol,
Opus; patches in data/classifier/review applied, item-level disjointness policy: exact benchmark phrasings dropped,
plain-language formatting rules kept; the 59-row spec-v2 relabel patch = intersection of Opus and sol approvals);
validation = data/classifier/heldout/* (fable-validation is author-disjoint; opus/sol held-out share authors with
enrichment and are reported as such). DEVELOPMENT/SELECTION set for the mechanism, the spec (v1 -> v2 three scopes),
and every quick check = the b3 probe (results/qwen/ledger-kv-probe-h1p, 20 sessions). The probe shaped the spec
(v1 -> v2) and the KINDS of training examples written after its failures (enrichment contrast pairs; the scope pass),
and — fable check-22 F3 — the v2 spec and the scope-generation prompt carried exemplars lifted from the probe's
misses including their specifics (a 90-word cap, an angle-bracket title, a postscript line); the resulting scope rows
that echo those specifics are dropped (review/scope-exemplar-patch.jsonl) and the exemplars rewritten; no probe
sentence or item-level paraphrase entered any training row (nearest-neighbour audits). The classifier is therefore
"developed with probe feedback"; its dev-probe numbers are development results.
EVALUATED-ON (this leg) = Multi-IF 909 (data/bench/multiif_en.jsonl), a DEVELOPMENT benchmark (it shaped the
mechanism and the spec's constraint types): this is a post-development evaluation, not zero-shot transfer. "Zero-shot"
is reserved for the separately registered no-contact family.
Selector (frozen before this leg): bge-small-en-v1.5 fine-tuned end-to-end, 3 epochs, seed 0 of the FINAL
identical-data run (artifacts data/classifier/model/ft/{encoder/*, head.pt}; sha256 recorded in the harness meta and
in WORKLOG before the first Multi-IF arm); sentences of prior USER turns, split by the registered splitter, scored
WITHOUT context, role "user", keep iff P(rule)+P(fact) >= 0.5 (threshold fixed since check 13). Seeds 1-2 are
reported on the probe only. Dev-probe result (check 22, three seeds): pinned 33/33/33, pin+echo 46/45/44, control 17
(finder 37/48, full 44, evicted 14), at 0.86x the finder's pinned-column count (echo tokens excluded) — pin+echo
matched the full-context BASELINE point estimate (full is a baseline, not a ceiling: echo arms exceed it).
The scope pass (4,954 rows) is reviewed by sol and Opus (review/scope-pass-*-patch.jsonl) before the FINAL run
whose seed-0 artifact is the registered selector.
Harness (scripts/multiif_evict.py; brief tools/codex-agents/multiif-eviction-harness.md): turns 1..T-1 generated by
the base trunk; at the last turn, on identical context ids: full | evicted | clf_pinned | clf_pinned_echo |
clf_control (exact-column, post-clamp) | role_pinned (prior user turns, recency-clipped to the classifier's column
count — the parameter-free comparator). Protected prefix = system prompt + first 4 columns in every arm. Eviction =
everything else before the current user turn. Echo = ledger.text_ledger_context of the selected spans before the final
user <|im_end|>. Generation: greedy, non-thinking template, max_new 512, deadline 300 s. Scoring: vendored checkers;
primary = aged constraints (introduced in turns 1-2, checked at turn 3); all turn-3 constraints secondary.
Registered contrasts (one-sided, cluster-robust by conversation, Holm alpha 0.05 over the three):
C1 clf_pinned_echo − clf_control > 0 (retention with a learned selector beats matched random columns);
C2 clf_pinned − role_pinned > 0 at equal columns (learned selection beats the parameter-free role rule);
C3 clf_pinned_echo − evicted > 0.5 x (full − evicted) (recovers at least half the eviction gap).
Reported, not gated: clf_pinned_echo vs full (ceiling), quoting rate, echo tokens added, columns per arm.
Safety (ROUND 7 integer clause per arm vs full): timeouts 0; truncated <= full + 1; degenerate <= full; invalid <= full.
Any arm breaching safety fails its contrasts regardless of pass counts.
Preflight: --limit 20, seconds/conversation reported; the 909 run only if projected <= 12 GPU-h. Outcome rules:
all three contrasts pass with safety intact -> ADVANCE to Leg A (BFCL, protected-prefix harness) and register the
no-contact family; C1 or C3 fails -> the mechanism's benefit on Multi-IF-style dialogue is reported as unsupported
at this selector quality and the classifier is NOT iterated on Multi-IF results (any further selector work goes back
to the classifier data, never to the benchmark); C2 fails alone -> the role rule is registered as the selector for
this dialogue style (simpler wins) and the classifier remains for BFCL.
Model card lines (verbatim when the time comes): "The selector was trained on hand-written, benchmark-disjoint
sentences; its label spec was developed against a synthetic instruction-following probe; Multi-IF and BFCL results
are post-development evaluations on benchmark families that informed the design; constraint-type overlap with
IFEval is deliberate; no benchmark item or paraphrase entered training."
Artifact hashes (seed 0, FINAL run, commit 48d670e): head.pt 191b3372010e8d151b842d2810b4be9dbd0ff34db7ae7539d6b823c69d4ebe3e; encoder/model.safetensors 2232813597b889355dfbda5607bfc473590385bd96ce382939a9ee154713d830; encoder/tokenizer.json 56827b4e89e42ec568d48462c6c37822da5a783161893deb981b31367bbc6f00; full list in results/quick-checks/ft_final2_s0_sha256.txt. Dev-probe FINAL numbers: pinned 33/33/33, pin+echo 46/45/44, control 17; scope-specific author-disjoint held-out 0.85/0.85/0.83.

### LEG B AMENDMENT 1 (2026-09-03, after the registered 20-conversation preflight, before any further outcome is viewed)
Preflight (results/qwen/multiif-evict-preflight, commit 8018113): 87.4 s/conversation, projected 22.1 GPU-h for
909 > the registered 12 GPU-h cap. The cap is raised to 24 GPU-h: the GPU is otherwise idle and the cost is wall
time, not money; the cohort is NOT cut (a seeded subset after seeing the preflight would be a post-hoc choice).
Preflight arm table (53 aged constraints): full 30, evicted 18, clf_pinned 31, clf_pinned_echo 33, clf_control 22,
role_pinned 29; C1 +17.1 pts (LB −3.1, p 0.09), C2 +1.2 (p 0.76), C3 +18.1 (p 0.05) — none significant at n=20,
as expected; safety: full 0/0/0/0 on 20 conversations, so every other arm fails "degenerate <= full" with 1-3
events; the clause is applied to the 909 counts, unchanged. The full run starts now with the registered
arms/contrasts/threshold/artifacts; records are resumable and are never deleted.

### LEG B AMENDMENT 2 (2026-09-03, before the corrected run's first outcome is viewed)
Eviction timing: the registered harness evicts BEFORE the current user turn is prefilled (commit 5c743f1; sol
EVICT-1 resolved; fable/sol fix reviews SOUND). The post-prefill run (results/qwen/multiif-evict-909, 145/909) is
INVALID-ORDERING and retained. Two-stage prefill is fp32-identical to one-shot (top-1 agreement 1.0; bf16 kernel
differences only, shared by every arm). Dev-probe under the corrected ordering with the registered selector:
full 44 | evicted 10 | clf_pinned 41 | clf_pinned_echo 46 | control 13. Contrasts, safety, threshold, artifacts,
and the 24 GPU-h cap are unchanged. The corrected run writes to results/qwen/multiif-evict-909-prequery.

## SELECTOR v2 — POST-DEVELOPMENT EVALUATION, LEG A (BFCL V3 multi-turn) — v7 (v5 + fable R1-R8 + sol's v5 exact fixes verbatim; decisions (i)-(vii) recorded; REGISTERED 2026-09-03 before any Leg A outcome)
Decisions where sol and fable disagreed (recorded, not split): (i) control-pool shortfall — fable F4 adopted (other-role
fill, recorded as control_role_shortfall, A1 also reported on no-shortfall turns) because dev prior-user pools are 24-308
columns; sol's fail-closed rule applies to recency_pinned and tool_swap_echo (impossible exact match -> that contrast
uninformative). (ii) A3 eligibility — fable F12 adopted (cluster-mean point estimate of full − base > 0, LB reported)
because a test-based gate at k <= 16 makes A3 ineligible by construction. (iii) Sealed exposed-cluster floor — 6 (fable
F10; void probability 10.5% at the dev rate vs 40.2% at 8); disclosed: at k = 6 the smallest sign-flip p is 1/64 = 0.0156 (all six case means strictly positive; a single zero case mean raises it to 1/32 and no Holm step-1/2 rejection is possible), so the first two Holm rejections require six strictly positive case means, while the third step and the A4 family (alpha 0.05) admit up to p = 3/64; at k = 7 one small-magnitude negative case mean can still pass step 1 (2/128 = 0.0156). (iv) Pin overflow — fable F2 adopted (lowest-P pins dropped; comparators built after; total overflow proceeds
identically across arms and stays in the primary) over sol's case-arm safety failure, because the overflow is a property
of the turn, not of the mechanism. (vi) Safety tolerance — fable F16/F24's one-case allowances are adopted over sol's stricter zero-baseline safety inequalities. Safety is counted by case, so the allowance is a prespecified one-case tolerance; the per-turn “2.5-4 points” rationale does not apply and is deleted. (vii) Inferential pass rule — sol's exact paired sign-flip/Holm rule is adopted as the operative decision rule; fable F11's `LB > 0` pass rule is not adopted, and the continuity-corrected clustered LB is descriptive only. (v, superseded wording) Safety allowances — invalid <= full + 1, repeated-call <= full + 1 and the <= 1 guard for degenerate are kept (fable F16/F24) over sol's invalid <= full, unexpected_duplicate_call <= full and no guard, because under case-level counting on a k = 6-16-case primary one event is one case (6-17 points) and full itself is a stochastic single run. Statistics — sol's exact paired sign-flip test over case means (distribution-free) is
the inferential test; fable's continuity-corrected clustered LB is reported beside it.
Data lineage: selector = the LEG B registered artifact (data/classifier/model/ft; sha256 in LEG B); its training data
include tool-role rows written by kimi/sol/Opus, never from BFCL. Model card (F23 verbatim): "The selector was fit on 20,054 hand-written, item-disjoint rows; no BFCL item or item-level paraphrase was used. BFCL was not untouched: its dev labels, schemas/template/checkers, and aggregate non-cohort analyses preceded the final selector and influenced tool-fact labels, protected roles, candidate roles, and harness choices; its dev split also selected the 1.7B/4B trunk by a frozen rule. Aggregate statistics over non-cohort BFCL cases motivated selecting over tool output and the tool-role label in the selector's training spec; the tool-role fact label (2026-09-02 20:28) post-dates the BFCL population analysis (15:30) that motivated it. The 64-case cohort was hashed in advance and its sealed item contents were not opened or executed before the final freeze. LEG A is a post-development, end-to-end comparison of KV retention plus source-labelled text reinjection, not a pure-KV or zero-shot result. Inference-time scoring of BFCL user/tool text applies the frozen selector and performs no fitting. “Repo-level no-contact zero-shot” is reserved for the separately frozen family, and does not assert absence from trunk pretraining."
Experimental design: PRIMARY = TEACHER-FORCED. At the start of every user turn t the KV cache is rebuilt from the
ground-truth history (prefix + turns < t as rendered by the harness: ground-truth calls executed through the vendored
environments, rendered as <tool_call> JSON + <tool_response>; no echo and no arm-generated token from earlier turns);
pins and echoes never persist across turns. Before intervention at turn t, every teacher-forced arm receives byte-
identical rendered source-history ids; arm input ids are not claimed identical after arm-specific eviction, pinning,
control selection, or echo insertion; arms are paired by case and turn. Each arm generates turn t with its own within-
turn tool steps (MAX_STEPS 20, deadline 300 s); turn t is scored by multi_turn_checker on ground_truth[:t] + [the arm's
turn t]. Teacher-forced case all-or-nothing pass = 1 iff every independently branched scored turn passes (reported for
every arm). SECONDARY (reported, never gated): FREE-RUNNING trajectories (BFCL's own protocol) for base and
clf_pinned_echo only — final pass and first-divergence turn; carries no claim.
Eviction (frozen): one decision per user turn t >= 2, at step 0, BEFORE the turn-t user message is prefilled: if
prefix_columns + history_columns > K = 8192, evict the evictable range = all columns after the protected prefix and
before the turn-t user message (located by MESSAGE INDEX, never by the last <|im_start|>user marker), keeping the arm's
pins — a threshold-triggered flush of the evictable range, named as such. Because the cache is rebuilt from ground truth
each turn, history_columns, the eviction decision, the evictable range and the candidate set are identical across arms:
"eviction fired" is a property of the turn. Protected prefix = [0, max(4, system_turn_end)), system_turn_end = end of the
complete system turn including the tool-call output-format contract; schema additions advance it at the next
serialization. The cache persists across the steps of a turn (assistant/tool tokens appended; no re-render and no second eviction). Each arm's within-turn cache may exceed K; per-arm columns and exceedance are recorded. If prefix plus pins plus the echo-bearing turn-t message exceed K, treatment drops whole pins in reverse registered `(P, recency, stable-source)` rank, dropping each pin's corresponding echo entry at the same time, until it fits. Record `pin_overflow` and dropped columns. Build `clf_control`, `tool_swap_echo`, and `recency_pinned` only after that drop; they pin treatment's final registered quantities and never re-evaluate overflow. A comparator may exceed K by its recorded `echo_token_delta`. If prefix plus the original no-echo turn-t message alone exceeds K, drop every pin and corresponding echo entry, record `pin_overflow_total`, and let all non-full arms proceed with zero pins and echo; the turn stays primary. Never drop current-turn or protected-prefix IDs. Two-stage schedule for every arm incl. full. Recorded per turn: evicted, columns before/after, evictable size, pinned columns per role, budget used, echo
tokens, columns after each step.
Selector: candidates = sentences of prior USER messages (registered splitter) and prior TOOL output split newline-first
(empty pieces dropped), each nonempty piece split with the registered sentence splitter, each resulting piece longer than
T = 128 Qwen3 tokens chunked consecutively at token boundaries; no cap on candidates; candidates come only from messages
with index < the turn-t user message. Scored WITHOUT context, role "user"/"tool", by the registered artifact with
truncation="longest_first", max_length 192; candidates whose scoring input exceeds 192 encoder tokens are truncated by
that rule and counted (scorer_truncated_candidates; the harness never aborts on this; measured margin ~11 tokens). keep
iff P(rule)+P(fact) >= 0.5. Pins = kept candidates ranked by (P desc, recency, then stable source order within a
message), added whole while they fit in B = 25% of evictable columns; the first that does not fit ends the fill; B is a
cap. Any candidate whose text contains <|im_, <tool_call, </tool_call, <tool_response or </tool_response, or whose Qwen3
tokenization contains any special or added token id of the trunk tokenizer, is dropped from pins and echo and counted
(echo_dropped_control_tokens); any emitted chat-control echo event is a safety failure. Echo = text_ledger_context with
header "Earlier context restated verbatim:", entries = the arm's pinned spans after any overflow drop (never a candidate that is not pinned; a pin dropped on overflow drops its echo entry, so pin_overflow_total turns carry no echo in any arm), as source-labelled JSON-quoted strings with "user:"/"tool:" prefixes,
most probable first, capped at E = 1,024 tokens (whole spans), inside the turn-t user message, fixed across steps;
treatment and comparators use byte-identical framing.
Column clamp for every comparator: matched spans are admitted whole in match order while they fit. If the next span would exceed the treatment's quota, that next span is admitted only through the Qwen3-token boundary that makes the pinned-column count exact, and its echo entry is that same truncated text. match_impossible is arm-specific: for clf_control, it means the combined disjoint nonselected pool permitted by decision (i) cannot supply the treatment's exact total pinned-column quota under the registered width/age matching rule; a same-role shortage alone is control_role_shortfall, not match_impossible. For recency_pinned, it means the eligible same-role universe cannot supply the treatment's per-role quota; overlap with treatment-selected spans is permitted because recency selection itself determines membership. For tool_swap_echo, it means that a selected TOOL chunk has no disjoint TOOL replacement under the registered width/age match. It is recorded per turn and makes the affected contrast uninformative as a whole, not a turn drop. Comparator echo delta: `abs(echo_token_delta) <= 16` tokens is required. On dev, a larger delta stops preflight. If first encountered in the sealed run, a larger delta makes that comparator's contrast uninformative; no affected turn is selectively excluded.
Arms (teacher-forced): base | clf_pinned (pins, no echo; reported) | clf_pinned_echo (treatment) |
  `clf_control` uses frozen seed 20260903 and disjoint nonselected candidates matched one-to-one on token width and source-turn age, without repetition or rotation. On no-shortfall turns it also matches the treatment's role one-to-one and exact per-role pinned columns. A same-role shortfall may be filled from the other role; such turns match exact total pinned columns, record `control_role_shortfall` and per-role column deltas, remain in the prespecified A1, and are excluded only from the separately reported no-shortfall sensitivity. If the combined same-role and decision-(i) other-role pools cannot supply the exact total pinned-column quota under the registered width/age matching rule, A1 is uninformative. `clf_control` receives the echo of its own spans' decoded text under the common framing and clamp. `recency_pinned` selects the most recent candidates from the same user/tool universe under the treatment's exact per-role pinned-column quota and echo budget, without reading classifier scores; it receives the echo of its own spans' decoded text under the same template and cap, clamped as in `clf_control`; an impossible exact match makes A2 uninformative. |
  tool_swap_echo — every selected USER span kept; each selected TOOL chunk replaced only by a disjoint TOOL chunk matched
  on token width and source-turn age, exact total pinned columns and echo tokens, echo clamped as in clf_control; no
  other-role fallback; an impossible match makes A4 uninformative |
  role_pinned — all prior user columns, no tool output, no echo (REPORTED only) |
  full — no deletion, same two-stage schedule (reference). Turns whose full prompt exceeds 40,960 positions are excluded
  from A3 and counted; at those turns full does not generate (per-turn pass NA; excluded from full's final-pass
  reporting as position_overflow). Any arm whose within-turn cache exceeds 40,960 positions at any step stops generating
  at that step; the turn is a truncated event for that arm and scores fail.
Contrasts — primary unit = per-turn pass under teacher forcing at turns where eviction fired (any category); cluster =
case. If fewer than 6 sealed cases contribute an evicting turn, the leg is INCONCLUSIVE (no contrast evaluated; exposure
counts reported); the same floor applies to each contrast's own k (A3 after the 40,960-position exclusions): a contrast with k < 6 is uninformative (A3: the A3-uninformative outcome rows apply). Inferential test (sol): For each contrast, compute within each case the mean binary turn difference over that contrast's registered primary turns. Use the exact one-sided paired sign-flip p-value over the k case means, enumerating all `2^k` sign assignments, retaining zero-valued case means, and counting test-statistic ties in the upper tail (no mid-p). Apply Holm step-down alpha 0.05 over eligible A1-A3; A4 is a separate alpha-0.05 family. The p-value grid and k are reported; no separate unanimity condition is imposed. If the primary population has k<6, the leg is INCONCLUSIVE. For A3, recompute k after the 40,960-position exclusions; if that A3 population has k<6, A3 is uninformative while the other contrasts proceed. Reported beside it: the LEG B
continuity-corrected clustered lower bound (per-cluster mean, one-sided t on k-1 df, continuity 100/k). A1
clf_pinned_echo − clf_control > 0; A2 clf_pinned_echo − recency_pinned > 0; A3 per-turn difference (clf_pinned_echo −
base) − 0.5 x (full − base) > 0, evaluated only if the cluster-mean point estimate of full − base is > 0 on the A3
population (primary turns minus the 40,960-position exclusions; its LB reported); A4 clf_pinned_echo − tool_swap_echo > 0
(the ONLY tool-source claim). Reported, not gated: teacher-forced case all-or-nothing pass for every arm; free-running final pass and first-divergence turn only for `base` and `clf_pinned_echo`; non-evicting turns (echo-only stratum); `role_pinned` and `recency_pinned - role_pinned`; tool-call validity; echo-copy rate (NO exclusion; this supersedes the echo-copy exclusion at LEDGER-PLAN.md:423 for Leg A because copying a tool-returned identifier is the task); columns and echo tokens per arm and turn; overflow, shortfall, delta and drop events.
Safety (case-level, sol; definitions fable): a case is counted once for a type if any generation sub-step has that
event, on the primary set, per arm vs full: timeouts = 0 (no guard); truncated <= full + 1; degenerate <= full where
degenerate = the harness's 4-gram repetition test evaluated ONLY on non-truncated generations (the truncation short-
circuit is removed before the preflight and unit-tested); invalid <= full + 1 where invalid = a <tool_call> block failing
parse_tool_calls or call_to_python (kept at +1: decisions (v)/(vi)); repeated-call <=
full + 1 where repeated-call = a normalized call identical to an earlier ground-truth or echoed call and absent from the
turn's ground truth; chat-control echo events = 0. Vacuity guard for degenerate only (the +1 types already admit one case at a zero baseline): if full has 0 degenerate cases, degenerate is judged "<= 1" and reported. A breaching treatment arm
(clf_pinned_echo) fails every contrast; a breaching control or comparator arm makes the contrasts that use it
uninformative (recorded); in either case the leg cannot be reported as "supported". This integer case-level clause
replaces the rate-based ROUND 7 fields in src/stencil/bfcl.py:summarize_records.
Preflights (dev slice, all arms, before the sealed cohort; all "final pass" floors are teacher-forced all-or-nothing case pass; the free-running secondary carries no floor): (1) With the 1.7B trunk, `full` teacher-forced case all-or-nothing pass must be at least 5/32 overall and 2/8 on dev `long_context`, and its teacher-forced per-turn pass on the 40 dev `long_context` turns must be at least 6/40. `base` teacher-forced case all-or-nothing pass must be at least 5/32 overall, and its teacher-forced per-turn pass on those 40 turns must be at least 6/40. No free-running metric gates preflight. If any floor fails, use the 4B trunk for the whole leg and re-check every floor once; if any 4B floor fails, stop and label the leg INCONCLUSIVE. Preflight and sealed run use the same trunk. (2) BASE-vs-BASE
bitwise determinism on the first dev id of each category: two fresh environments produce identical generated token ids,
normalized calls, tool outputs and checker traces at every turn. (3) feasibility: at least 4/8 dev long_context cases
pressure-exposed (eviction fired) and at least four exposed case-turns select a tool chunk; otherwise stop without
changing K or refitting, INCONCLUSIVE (a BFCL-driven K change requires a new registration and cannot rescue this leg).
(4) seconds per case and the projected sealed cost for the selected trunk over the 64-case mix; cap 30 GPU-h; if
exceeded, before any sealed outcome is viewed run only base | clf_pinned_echo | clf_control | recency_pinned | full (the
cut removes tool_swap_echo, clf_pinned, role_pinned and the free-running secondary; A4 is declared uninformative, not
failed); if the reduced set is still above 30 GPU-h the leg stops, INCONCLUSIVE; the cohort is never cut. (5) Before the
preflight, record and freeze K, B, T, E, threshold, header, seed, registration hash, harness hash, selector artifact
hash, trunk weights and tokenizer hashes, BFCL data manifest (cohorts.json sha256), chat template hash, vendored checker
hash; any later change re-registers the leg; no preflight evidence may tune these. (6) On every dev generation of every
arm the harness asserts, and the preflight report shows 100%: the complete protected prefix survives eviction; no token
of the turn-t user message or its steps is in cache at the eviction decision; columns_before − evicted + pinned =
columns_after exactly; every candidate comes from a message with index < the turn-t user message; Treatment, `recency_pinned`, and `tool_swap_echo` have equal per-role pinned columns and echo tokens within the clamp. On no-shortfall turns `clf_control` meets the same per-role equality; on `control_role_shortfall` turns it matches exact total pinned columns and the harness asserts and reports the per-role deltas permitted above;
every shortfall/overflow/drop event is recorded. Any assertion failure stops the leg before the sealed run. Report
selected and eligible spans by role, nominal and actual B, capacity rejections, fallback counts, exposed/no-pressure
cases.
Outcome rules: A1 & A3 pass with safety intact -> per-turn benefit under teacher-forced agentic evaluation supported
post-development (the free-running final-pass difference is reported beside it and carries no claim). A3 uninformative
with A1 passing and safety intact -> supported on A1 only, labelled "no measurable full-context headroom on this
cohort"; A3 uninformative with A1 failing -> unsupported. If A1 is uninformative for any registered reason, the primary benefit claim is INCONCLUSIVE and cannot be reported as supported; every other eligible contrast and secondary metric is still reported. If A3 is eligible and either A1 or A3 does not pass, the primary benefit claim is unsupported. A2 non-rejection = "no learned-ranking advantage detected";
recency is preferred only by the registered simplicity rule, not by an equivalence claim. If the selector keeps zero
tool candidates on dev long_context evicting turns, A2 and A4 are declared uninformative before sealed execution
(A1/A3 then test a user-span mechanism only). A4 failing or uninformative -> no tool-source claim. Competence,
invariant, feasibility, or sealed-cluster-floor failure -> INCONCLUSIVE, no sealed inference. Any classifier data
written after this leg is authored without access to BFCL records and nearest-neighbour audited against the dev slice;
selector work never returns to BFCL outcomes. No-contact family for the zero-shot claim, screened by name only:
ToolTalk, CoSQL/SParC, ConvFinQA (fable §5; sol's APIFlow-Bench and Toolathlon by landing page); the registered contact
screen runs before any item is fetched; registered after this leg regardless of outcome.

### LEG A AMENDMENT 1 (2026-09-03, fable v7 confirmation residuals A/B/C, text only; applied in place above before the dev preflight): preflight (6) lead-in deleted so clf_control is not a subject of the per-role equality; model-card timestamp lineage clause restored; safety pointer -> decisions (v)/(vi).

### LEG A AMENDMENT 2 (2026-09-03, sol v7 confirmation residuals, text only; applied in place above before the dev preflight): arm-specific match_impossible definitions and the clamp truncation rule; A1 uninformative -> INCONCLUSIVE; eligible A3 with either A1/A3 failing -> unsupported.

### LEG B AMENDMENT 3 (2026-09-03, before any outcome of the corrected run is viewed)
The corrected run (results/qwen/multiif-evict-909-prequery) crashed at conversation 145/909: the exact-column control
cannot be drawn when the classifier pins more than half of the evictable range (79 pinned vs 68 available columns on a
short history). Registered handling: such a conversation is recorded with control_impossible = true, its clf_control
arm is not run, it is EXCLUDED from contrast C1 and counted (n_control_impossible), and every other arm runs and
scores normally (C2, C3 and all reported metrics keep it). The harness hash changes; per the fail-closed resume rule
the run is RESTARTED in a new directory (multiif-evict-909-prequery-v2) rather than resumed; the 145 records of the
crashed run are retained and labelled superseded (they were produced under the same eviction ordering and selector;
no outcome from them has been viewed or used). Cap, contrasts, safety, threshold and artifacts are unchanged.

### LEG A AMENDMENT 3 (2026-09-03, fable's harness-v4 review F1-F3, text; applied before the dev preflight is read)
1. Matching (F1): comparator matching is NEAREST, not exact — for each selected span, the disjoint nonselected
   candidate of the required role (decision (i) fallback for clf_control) that minimizes |token width difference|
   with ties broken by smallest |source-turn age difference| then stable source order, without reuse; the column
   clamp then makes the total pinned columns exact. match_impossible therefore means only that the eligible pool has
   fewer TOTAL columns than the quota (clf_control: combined pools; recency_pinned: the same-role universe;
   tool_swap_echo: no disjoint tool chunk at all). Dev census (fable): exact-width matching would have voided A1 on
   5-7 of 11 evicting turns; nearest matching is the intended reading.
2. Echo clamp (F2): comparator echo entries are the decoded text of the pinned columns (char-exact where the span is
   untruncated); the echo is clamped TOKEN-EXACTLY to the treatment's echo token count by truncating the last entry
   at a Qwen3 token boundary (mirroring the column clamp), so |echo_token_delta| <= 16 holds by construction; any
   larger delta is a harness assertion failure, not a method failure.
3. Position overflow (F3): a `full` turn whose within-turn cache exceeds 40,960 positions is a truncated event for
   full (pass = 0, counted; never None); summarize_records must never receive None passes.
4. Items already closed by the v5 harness (sealed offsets loader; degenerate on non-truncated only; manifest hash over
   every executing module; certificate) are confirmed as registered; the registration hash is recomputed over the v7 +
   A1 + A2 + A3 text before the preflight certificate is written.

### LEG A AMENDMENT 4 (2026-09-03, fable's harness-v6 review FV6-2/FV6-3, text; applied before the registered preflight)
1. Position overflow, two cases (FV6-2): (a) INITIAL-PROMPT overflow — a turn whose full-arm prompt exceeds 40,960
   positions before generation: full does not generate; per-turn pass NA; the turn is excluded from A3 and from
   full's safety baseline (it is NOT a truncated event for full); recorded as position_overflow_initial. (b) WITHIN-
   TURN overflow — any arm whose cache exceeds 40,960 positions during a turn's steps stops generating at that step:
   truncated event for that arm, scores fail (Amendment 3 unchanged). Dev census: 6 of 11 evicting turns are case (a).
2. Echo clamp completeness (FV6-3): the comparator echo is clamped token-exactly in BOTH directions — truncating the
   last entry when over, and extending the last entry from its source text (never beyond the source span) when
   under; |echo_token_delta| <= 16 is asserted after clamping on dev and sealed paths alike (fail-closed).
3. Per-role column equality of every comparator is asserted on EVERY evicting turn on the sealed path as well as on
   dev (fail-closed; a violation makes the affected contrast uninformative and is recorded), and the preflight report
   lists match_impossible, shortfall and delta counts.

### LEG A AMENDMENT 5 (2026-09-03, sol's harness-v8 review V8-2, text; resolves AMENDMENT 4 item 3 vs decision (i))
Per-role column equality: every comparator on every evicting turn, and clf_control on every NON-shortfall turn, must
match the treatment's exact per-role pinned columns. clf_control on a control_role_shortfall turn (decision (i))
matches the exact TOTAL pinned columns with the per-role deltas recorded. Both conditions are asserted fail-closed on
the dev path (preflight invariants) and on the sealed result path (record schema); a violation makes the affected
contrast uninformative and is recorded. Certificate (V8-1): the preflight certificate is split-invariant — it binds
the frozen constants, harness/module manifest hashes, selector/trunk/tokenizer/template/checker hashes and the DEV
cohort's verified bytes; a sealed run validates the certificate BEFORE reading any sealed byte, then verifies its own
cohort bytes against the sealed offsets index and records them. Competence baseline (V8-3): full's initial-prompt NA
cases are excluded from the preflight competence denominators and reported.

### LEG A AMENDMENT 6 (2026-09-03, fable's harness-v10 review FV10-3, text; before the registered preflight)
Echo-unreachable regime: when, after the two-directional clamp, a comparator's echo cannot reach the treatment's
token count from its matched spans (|echo_token_delta| > 16 after extension), the turn is recorded (echo_delta,
echo_unreachable = true) and the affected comparator's contrast is uninformative for that turn's cluster; it is NOT a
harness assertion failure. Invariant violations of any kind on the dev path fail the preflight (recorded as
invariant_violation, never as match_impossible); on the sealed path they are recorded and make the affected contrast
uninformative. The post-run drift check compares the harness manifest and data hashes, not git provenance; both
provenances are recorded in evidence.

## LEG B OUTCOME (2026-09-04, corrected run results/qwen/multiif-evict-909-prequery-v2, 909 conversations, 2,276 aged constraints)
Arms (aged pass): full 1483 (0.652) | evicted 379 (0.167) | clf_pinned 1302 (0.572) | clf_pinned_echo 1348 (0.592) |
clf_control 747/2263 (0.330; 5 conversations control_impossible, excluded from C1) | role_pinned 1377 (0.605).
Contrasts: C1 clf_pinned_echo − clf_control = +26.8 pts, cluster LB +24.7, p ~ 0 (Holm PASS); C3 half-gap recovery
+18.5, LB +16.7, p ~ 0 (Holm PASS) — recovered fraction (0.592−0.167)/(0.652−0.167) = 0.88; C2 clf_pinned −
role_pinned = −3.5 pts, LB −4.8 (FAIL: the role rule beats the classifier at equal columns).
Safety (integer clause, per arm vs full): timeouts 0 everywhere; truncated 162-187 vs full 208 (ok); degenerate
192-222 vs full 241 (ok); INVALID: clf_pinned 1, clf_pinned_echo 1, role_pinned 1 vs full 0 -> breach of
"invalid <= full" (1 > 0). Quoting (echo-copy) 153 conversations on the echo arm (reported).
REGISTERED VERDICT: the three pinned arms breach the safety clause on a single invalid output each (of 909), so their
contrasts FAIL as registered; the primary benefit claim for Leg B is therefore NOT SUPPORTED under the registered
text. C2's outcome rule applies descriptively: the parameter-free role rule is the better selector for this dialogue
style (simpler wins); the classifier remains the candidate for Leg A.
DISCLOSED, NOT CLAIMED: C1 and C3 pass their statistical tests by wide margins; the safety breach is one event in 909
against a zero baseline — the vacuity that fable (harness review) and sol warned about for Leg A, which registered
"invalid <= full + 1" and a one-event guard. Leg B's clause is not retroactively changed. A future Leg B re-run under
a prospectively registered clause matching Leg A's would be a new registration.
Cost: 75,124 s = 20.9 GPU-h (82.6 s/conversation), under the amended 24 GPU-h cap.
LEG B OUTCOME — addendum (2026-09-04, fable's review, text only): (a) the triggered rule applies — the classifier is
NOT iterated on Multi-IF results; the C2 diagnostic (classifier under-selects turn-2 tail text; identical columns
in 459/909 conversations; −7.1 pts where columns differ) is DISCLOSED and is not used to author classifier data.
(b) The role rule is NOT registered as the selector: C2 did not fail alone (the safety clause also fired), and
role_pinned's budget was borrowed from the classifier; a deployable role rule needs its own registered budget.
(c) The "ADVANCE to Leg A" gate is closed as moot: Leg A was authorized on 2026-09-03 17:41 on its own review
record, before this outcome was viewed. (d) The three invalid outputs are 512-token whitespace/markdown loops after
a "wrap in double quotation marks" constraint (no chat-control tokens anywhere); conversation 534's single
generation is counted in two arms; they are also counted under degenerate. p-values reported as 0.0 are underflow
(t ~ 20, df ~ 900; p < 1e-15). Any future cohort registers an invalid definition that excludes degenerate loops
and carries a one-event guard; no re-scoring of this cohort.

## PROGRAM-REVIEW CLARIFICATIONS (2026-09-04, gpt-6-astra review results/astra-program-review.md; text only, appended; no registered outcome or rule changed)
LEG B (clarifies :554, :587, :590 and the OUTCOME): Leg B was registered before outcomes from this final frozen-selector
run; earlier Multi-IF results informed development. C1 compares selected pins plus echo against a deterministic
equal-column complement control without echo. Full context is a reference baseline, not a ceiling. The echo arm was
6.15 conversation-mean points below full context; its mean 38.11 pinned columns were accompanied by 48.77 added echo
tokens. The failed safety clause was a strict zero-tolerance observed-count rule, not a statistical proof of excess
risk and not a mathematically vacuous test (the word "vacuity" in the OUTCOME is withdrawn in favour of "brittleness").
The registered verdict remains NOT SUPPORTED. Reapplying a different clause to these same outcomes is post hoc.
Source clustering (astra R6, post hoc sensitivity, not a re-registration): 484 source prefixes (425 with two
conversations); source-weighted C1 +26.68 (LB +24.15), C2 -3.37 (LB -4.88), C3 +18.21 (LB +16.16), echo-full -6.38
(LB -8.84): the signal is not an artifact of treating variants as separate conversations.
Two-stage prefill (clarifies :618): two-stage and one-shot fp32 logits differed by at most ~8e-5 with top-1
agreement on the recorded diagnostic; numerical agreement, not bitwise identity; every arm shares the schedule.
LEG A (clarifies :631-632, :681; applies before any sealed inferential use): the sign-flip enumeration is exact
conditional on sign symmetry/exchangeability of case-mean differences; it is NOT a distribution-free test of an
arbitrary zero-mean case-effect distribution (astra counterexample: differences +1/5 w.p. 5/6, -1 w.p. 1/6, mean 0,
all six positive w.p. (5/6)^6 = 0.3349, each such sample gives p = 1/64). Those assumptions have not been established
for this design. A mechanical registered pass must not be presented as assumption-free confirmation of a positive
population mean. Any replacement endpoint or inferential procedure requires a new prospective registration before
sealed outcomes are accessed; the registered dev preflight and its gates are unchanged.
LEG A interpretation (consolidates v7 + amendments 1-6; conservative readings): A1/A3 support concerns only the
registered teacher-forced package comparison and does not establish learned-selection advantage or free-running
agentic benefit. A2 must pass for a conditional learned-ranking claim; its quotas remain classifier-derived, so even
an A2 pass is a within-role ranking diagnostic, not a comparison of independently budgeted selectors. A1/A3 alone
never justify keeping the classifier. Any unusable comparator on a primary turn makes its entire contrast
uninformative (whole-contrast reading of Amendment 6; no affected cluster is selectively removed). A3 uninformative
reasons are reported separately as insufficient eligible cases, nonpositive measured headroom, or reference/method
failure (post_exclusion_k is recorded). Safety is scoped to the claim that uses the breaching comparator; primary
support never means learned-ranking support. The comparator's final echo entry may extend beyond its pinned columns
(Amendment 4): column and echo counts are not identical information pathways. The "no tool candidates selected"
uninformative branch is defensive and effectively unreachable after a passing preflight.
Successor design (recorded, not registered): sole primary = frozen classifier retention plus echo vs a frozen,
independently budgeted role/recency policy plus echo, on independently authored benchmark-free delayed-use episodes;
one prespecified binary outcome per case; exact one-sided McNemar at alpha 0.05 with paired effect interval and a
prespecified worthwhile magnitude; resource ceilings and safety/cost limits frozen before outcomes; failure to
demonstrate superiority is not an equivalence claim.

## SC1 — LEARNED vs RULE SELECTOR, BENCHMARK-FREE FROZEN-POLICY COMPARISON (DRAFT v1, 2026-09-04; NOT YET REGISTERED)
Data lineage: selector = the LEG B/LEG A registered artifact data/classifier/model/ft (frozen files, threshold 0.5,
segmentation unchanged; sha256 as recorded in LEG B). Rule = newly implemented, parameter-free (nothing learned).
Episodes = 256 final + 32 setup, ORIGINAL fictional delayed-use episodes authored under data/sc1/AUTHOR-CONTRACT.md by
authors (kimi-k3, fable, gpt-6-astra, Opus) who receive only the contract; no benchmark item, diagnostic, selector
score, or repo example is shown to any author; authors do not know which policy is expected to win. Disjoint from
every evaluation benchmark family (IFEval, Multi-IF, BFCL, S2/B3) and from the dev probe. Nothing is learned, tuned,
or selected on SC1 outcomes.
Source: results/astra-research-blockers.md §3/§5 (gpt-6-astra, 2026-09-04) and results/astra-program-review.md G1.
Question: does the frozen learned selector, with its own budget, buy final-task success over a frozen parameter-free
rule with the same budget, on histories with mixed user/tool-sourced information and scope changes?
Trunk: Qwen3-4B (prepared; hf_compatible numerics), non-thinking, fixed decoding (temperature 0), <= 256 generated
tokens, one output per arm per episode.
Arms (both: pre-query eviction; protected prefix = system + tool schemas; most recent 1,024 history tokens always
kept; pin cap B = min(256, floor(0.25 x C)) where C = evictable history columns; echo cap E = 256 tokenizer tokens
including header and source labels; identical renderer and tokenizer; scope resolver OFF; digest OFF; all attention
amplification and residual steering OFF with an intervention counter required to be 0):
  clf  — frozen classifier ranks candidate spans (user sentences + 128-token tool chunks) by P(rule)+P(fact);
         admits whole spans in rank order while they fit B, skips oversize spans, continues; echoes admitted spans
         chronologically within E with role/turn labels.
  rule — prior-user spans newest-first, then prior-tool spans newest-first; same admission and echo procedure; reads
         no classifier scores, quotas, counts, or echo lengths; deterministic tie-breaks by source offset.
  Setup-only diagnostics: full (no eviction) and evicted (no pins, no echo).
Setup gate (32 setup episodes, run BEFORE any final outcome is opened): full success >= 24/32 AND (full - evicted)
>= 8/32; timing measured here. If either fails, the final set is NOT run; record "instrument lacks competence /
headroom"; any redesign uses NEW setup and final sources.
Primary (sole confirmatory) estimand: D = P(Y_clf = 1) - P(Y_rule = 1) on a fresh episode from the frozen authoring
mixture; both policies run on every episode from identical scripted histories. b = clf-only passes, c = rule-only
passes, N = 256 (all paired episodes; none excluded). Test H0: D <= 0 vs D > 0, exact one-sided McNemar
p = sum_{j=b}^{b+c} C(b+c, j) 2^{-(b+c)}; p = 1 if b + c = 0; reject at p <= 0.05. Report b, c, both marginal rates,
D_hat = (b - c)/N, and the conservative paired 95% interval [L_b - U_c, U_b - L_c] from two-sided 97.5%
Clopper-Pearson intervals on b/N and c/N. No mid-p, no asymptotics, no outcome-dependent stopping, no selective
reruns, no enlargement of N after outcomes.
Adoption rule (engineering, on the estimate): keep the learned selector only if p <= 0.05 AND b - c >= 13 (>= 5 points)
AND operational limits pass: clf-only invalid/truncated/repetitive episodes (vs rule) <= 2; zero checker-detected
collateral state corruption attributable to clf only. Otherwise the rule is chosen by simplicity, reported as "no
worthwhile learned advantage demonstrated", never "equivalent". Invalid = parser/schema failure; truncated = hit the
generation limit without a complete valid output; repetitive = a normalized 4-token block repeated >= 8 times.
Scoring: generation failures, malformed output, truncation, exhausted budgets score 0 with cause recorded. A
predeclared infrastructure interruption may resume the missing attempt from identical state without changing
completed outputs. An unresolved harness defect invalidates the run; it never permits dropping pairs.
Reported, not gated: success by style/origin/age/scope, override and exact-ID error counts, selector latency, pinned
columns and echo tokens actually used, failure taxonomy, setup-set full/evicted rates.
Power (astra, recomputed on CPU; sampling probabilities, not a claim about SC1's discordance): at N = 256 a true
5-point gain has 78% power at discordance q = 0.10, 51% at q = 0.20; a 10-point gain has 97% at q = 0.20.
Cost cap: 8 GPU-h total (setup + two final arms). Authoring: 256 + 32 episodes, ~40-64 author-hours across authors;
each episode's checker and six mutations validated by an independent reviewer before freezing.
Freeze sequence: (1) contract + this registration reviewed (astra, fable, kimi); (2) harness built and dry-run on
8 synthetic smoke episodes written by the harness coder (never reused); (3) episodes authored, reviewed, hashed;
(4) setup gate; (5) final run, one attempt; (6) outcome recorded against this text. Registration becomes binding at
step (3): after the episode hashes are recorded, no text here changes except by dated amendment before step (5).

## SC1 — LEARNED vs RULE SELECTOR, BENCHMARK-FREE FROZEN-POLICY COMPARISON (DRAFT v2, 2026-09-04; NOT YET REGISTERED; supersedes DRAFT v1, which is preserved above)
Data lineage: fit-on = the previously frozen, development-informed selector corpus; no new fitting or training.
Selector = data/classifier/model/ft, the LEG B/LEG A frozen files and recorded sha256 values, threshold 0.5.
Evaluated-on = 256 newly authored final source episodes; setup = 32 separate new source episodes under the same
authoring law. Neither pool, references, author responses nor outcomes may enter fitting, threshold/prompt
selection or policy revision. Authoring is by fresh contract-only sessions with retained transcripts/provenance,
not the informed sessions that reviewed this design or developed the classifier. Historical probe and benchmark-
family influence on the selector remains disclosed in LEG B/LEG A; this does not repair its training-recipe
provenance. Task-time authoring excludes all benchmark items, derivatives, recorded benchmark responses, probe
diagnostics and repository examples. This claims new evaluation sources without such authoring contact, not
absence of benchmark material from author/trunk pretraining or absence of historical development influence.

Source: results/astra-research-blockers.md §3/§5 and the three results/sc1-review-{astra,fable,kimi}.md reviews.
This section and data/sc1/AUTHOR-CONTRACT.md are prospective v2 text; v1 is preserved above and its contract is
preserved byte-for-byte at data/sc1/AUTHOR-CONTRACT-v1.md. No harness, episodes, manifests or validation results
are asserted to exist by this consolidation. The named functions and checks below are requirements to implement.
Question: does the frozen learned retention-plus-echo package improve executable final-task success over this
independently budgeted, parameter-free role/recency package at the same resource ceilings?

**Scientific freeze, executable freeze, episode freeze.** Stage 1: review and freeze this scientific design and
sanitized author contract BEFORE any setup/final authoring. Freeze the author distribution and exact author
versions/settings/prompts, sampler, source-validation law, policy algorithms, renderer semantics, decoding,
endpoint, N, statistical/engineering gates, failures and cost rules. Stage 1 requires a completed author/version
manifest: for each of kimi-k3, fable, gpt-6-astra and Opus, record provider, immutable served model/version ID,
settings (including temperature, sampling parameters, reasoning effort, output limit and seed support), exact
neutral input template and contract/API-spec hashes. These family/alias names alone are NOT frozen versions.
Unresolved versions/settings prevent registration; they may not be filled opportunistically after authoring or
substituted when a provider changes. Freeze deployment model/tokenizer/configuration and per-attempt limits too.

Stage 2: build the common harness, spec compiler/expander, finite executor, checker/mutation generator and
policy-independent authoring launcher; pass targeted CPU consumer checks on eight disposable original smoke
sources, never reused for setup/final. Freeze executable artifacts and their complete manifest BEFORE production
authoring. This includes original API families and filler pool, source fingerprinting/normalization, renderer,
tokenizer/chat template, segmenter, parser/checker, generator, source-validation criteria, dependencies and harness
commit. Use two of the eight smoke sources for any separately authorized model determinism check (two fresh
processes x two sources x two arms = eight outputs, budgeted below). Smoke work cannot tune the frozen science;
if it reveals the need for a scientific change, reopen Stage 1 prospectively before production exists.

Stage 3: commission the 32 setup and 256 final sources, independently validate them without selector/trunk
feedback, and hash every spec, episode, state trace, reference, checker, mutation/coverage case, review record,
author transcript, seed, split and execution order. Then run the frozen setup competence/headroom gate and cost
projection; launch final execution only on both passing. Record the fixed cohort once, then summarize against
the frozen manifest. No scientific or executable choice may use production source content or setup/final model
outcomes. A dated amendment is not permission to reopen these choices. After setup outcomes open, only editorial
corrections that change no behavior, definition or decision are allowed. Any substantive redesign, including
failed-setup rescue, requires a newly named registration and NEW setup and final sources. An implementation
defect invalidates the affected study; repair cannot justify dropping pairs or rerunning this bank under new code.

**Population, sampler and author boundary.** Each episode is a distinct original semantic source. Independently
draw author with probability 1/4 for each frozen family/version; style editing/tool-work 1/2 each; decisive-fact
origin user/tool 1/2 each; decisive-evidence age OLD/RECENT 3/4 and 1/4; scope continuing/overridden/
cancelled-or-completed/switched 1/4 each. Thus expected final age counts are 192/64 and setup 24/8, not quotas.
Use master seed 20260904 and the contract's SHA-256, pool/index/stream/attempt derivation and bit mappings;
separate streams govern author, each factor, authoring randomness, literals, filler and arm order. Record full
digests and realized marginal/crossed counts. No balancing, author swapping, factor relabelling or correlated
factor selection. Exact inference assumes independent source draws under this fixed mixture; pseudorandom seeds,
source fingerprints and semantic uniqueness checks support the operational audit but do not prove independence.

One fresh isolated session writes one source. Authors receive only the sanitized contract, assigned factors/seeds
and frozen original task/API/spec grammar: no registration, reviews, policy identity/ranking, diagnostics, examples,
benchmark outcomes, tools, repository access, retrieval or previous conversation/project memory. Retain every input,
response, revision and rejection with exact version/settings, session IDs, hashes and task-time-isolation
attestations. The same model family may author in a fresh session; an informed session may not. Feedback covers
source/checker validity only, never which policy benefits. Setup means separate EPISODES/sessions from the SAME
author mixture, not a different author population. No shared setup/final story, entity, identifier, instantiated
task or source graph; shared generic domains, grammar, tool families and disclosed irrelevant filler are allowed.

Freeze the contract's three-attempt source-validity procedure: keep author/factor assignments fixed, increment
only content attempt seeds, retain all rejections, and defer if any assigned slot cannot yield a valid source.
Do not turn repeated retries into selection for model competence. Record domain, task, scenario_gist and normalized
semantic source fingerprint (alpha-renamed typed entities/literals, canonical graph retaining causal dependencies).
Equal fingerprints require sibling rejection; distinct hashes still require signed independent pairwise semantic
review across all 288 sources. Audit entity/identifier collisions and history 8-gram overlap; >=0.05 Jaccard is
a review flag, with shared filler accounted for, not a substitute for the graph audit. Report author/domain counts;
do not impose the proposed domain quotas or disjoint domain strata. If dependence is discovered after freeze,
invalidate the independent-source interpretation without deleting, replacing or relabelling outcome pairs.

The 75:25 age change adopts fable P1's concentration on delayed-use cases while retaining recent cases as a
do-no-harm control. It supersedes the source/astra proposal of 50:50 prospectively. Sharing decisive recent
evidence can dilute the overall gain, but does not guarantee concordance: different old pins/echoes can still
change responses. No empirical discordance q is assumed from that argument, and N is not changed.

**Sources, outputs and private scoring.** The contract defines the complete structured record: IDs/pool/index,
independent assignments/seeds/attempts, author/input provenance, domain/task/scenario_gist, entities and causal
source graph, instruction trajectory and decisive-fact coordinates, distractors/filler manifest, task spec,
pre-decision initial_state and state trace, obligation IDs/predicates, explicit protected_set, complete expected
artifact/state, serialized reference, generated checker and mutation plan/cases, public system/tools/turns/
final_request, layout audit, normalized source fingerprint, distinctness sign-off and validation/coverage records.
Every skeleton is individually authored. The deterministic expander generates lengths, literal placement,
incidental filler, executable checkers and mutations from that single source; it cannot turn renamed templates
into independent episodes. Independently review narrative-to-obligation semantics and compiler behavior per
family, plus each episode's reference/negatives and obligation mapping; a shared generator bug is not evidence
of correctness. Audit role/position/wording markers and shared filler on smoke sources before executable freeze;
do not fit a diagnostic classifier on setup or any evaluation prompts/responses.

Histories contain 12–24 scripted messages and 4,096–8,192 rendered history tokens. The final result is a JSON
patch/small text artifact (<=40 lines), or exactly one allowed in-memory database call. A concrete reference with
all framing must fit 256 generation-tokenizer tokens. OLD evidence, including governing updates, lies wholly
before the retained suffix and is not restated or semantically supplied in the suffix, prefix, schema or final
request. RECENT decisive evidence lies wholly in the suffix. The renderer verifies the assigned age; mismatch
requires source-validity repair, never relabelling. Private literal and semantic leakage checks cover prefix,
tools and final request; general schema keys/syntax are not the tested literals. Tool-origin facts confer no
authority to override user rules. State traces must match public tool returns; hidden snapshots are never inputs.

Renderer allowlist: ONLY system, tools, turns and final_request; all factor labels, source annotations, provenance,
seeds, states, references, checks and mutations are private. The independent reviewer uses the production parser,
executor and checker runner with fresh state to require reference PASS, six DISTINCT APPLICABLE negatives FAIL,
and every obligation/invariant exercised. The six slots are old-ID substitution, cancelled action, wrong entity,
wrong scope, empty output and collateral edit. Predeclare non-applicability and obligation-linked substitutes
(missing required field/object, wrong exact value, forbidden extra output, incomplete artifact/call, in that
priority order); never manufacture scope events or count duplicates/parser-only failures as semantic coverage.
Add cases beyond six for full coverage, a generic safe-response negative on every episode, and a reviewer-built
recency-only negative on every OLD episode. Unchanged state/no-op must fail. Check complete resulting state or
artifact, including non-target creates/deletes, required content, forbidden additions and all protected objects.
Protected sets are explicit and nonempty for BOTH styles: editing protects fields/lines or forbids extra keys/
lines/content; tool-work protects records/fields. Unreachable corrupt states are exercised through the same
final-state checker as supplementary probes, not counted among the six executable output negatives.

The future runner's `--validate` path records each case/verdict/cause and reviewer identity before hashing; model
outputs use that same path. JSON is compared structurally, numbers by value with boolean/type separation,
strings exactly; duplicate keys, unknown fields, non-finite numbers and extra text are invalid. Accept exactly
one bare JSON value/call, with no markdown fences or surrounding commentary, for JSON/call tasks; raw text only
for text tasks. Normalize text line endings to LF, strip trailing horizontal whitespace and collapse blank-line
runs, identically for reference and output. Compare full normalized artifacts and every declared predicate.
The executor implements only frozen finite typed record operations (create/update/delete/get/list), parses and
validates before mutation, and has no eval, network, filesystem task or vendored benchmark environment.

**Trunk, rendering and eviction geometry.** Qwen3-4B, prepared checkpoint, hf_compatible numerics, non-thinking,
temperature 0/greedy, max_new_tokens=256, exactly one output per arm/episode and one call for tool-work. Stage 1
pins exact checkpoint/configuration, dtype, tokenizer/template, EOS IDs, non-thinking opener and deployment;
Stage 2 hashes their actual bytes and dependency versions. Per-attempt deadline is 300 seconds including candidate
extraction, scoring, admission, echo, prefill, generation and checking; ordinary timeout scores zero. A complete
valid result ending exactly at the token/action/time limit is within budget. Use the frozen template's non-thinking
serialization, general tools in the protected system prefix and semantic role/source coordinates from the renderer.
Echo is inserted before the original final request inside that user message, separated by two LF characters.

Let P be the token boundary after the protected system/tools prefix; H the boundary immediately before the final
user message. Both are supplied by the renderer, not inferred with decode/rfind/re-encode. History length = H-P,
including history role delimiters; R=max(P,H-1024). Retain [0,P) and [R,H) in both arms. The removable old range
is [P,R), and C=R-P counts ALL removable history columns before selection, not only candidate columns. Pin cap
B=min(256,floor(C/4)); echo cap E=256 trunk-tokenizer tokens including header, labels, quoting and insertion
separators. Compliant episodes have C=3,072–7,168, hence B=256 always (8.33%–3.57% of removable history).
The fractional branch is dormant on this cohort and exists only for out-of-contract smoke inputs. This is a
single frozen pressure/echo setting, not a working 25% allocation or an optimized budget claim.

Choose TWO-STAGE prefill for both final arms and setup diagnostics: fresh common history prefill, then old-range
eviction retaining the arm's pins, then final query plus echo prefill and generation. Preserve source token IDs,
original RoPE positions and the absolute position counter; do not reindex retained KV or prefill the query/echo
before eviction. Evict on EVERY compliant episode; no inherited BFCL K=8192 pressure trigger. Reuse the audited
KVCache.evict/prefill_with_eviction behavior in src/stencil/qwen3.py, with per-layer width/position assertions,
not the benchmark loader/executor or an implicit full-context fallback. Enforce the 40,960-position guard;
out-of-contract layout fails validation before freeze, never becomes a dropped final pair.

**Common candidates and policy keys.** Implement a NEW pure, UNSCORED `build_sc1_candidates` from source-only
public history and renderer coordinates, without loading/calling a classifier. Freeze the LEG A segmentation
semantics in src/stencil/bfcl.py: prior user text is sentence-split; prior tool text is split into nonempty lines
then sentences; EVERY resulting piece (user and tool) is consecutively chunked at 128 local Qwen tokenizer tokens.
The frozen sentence splitter's filtering, character/token mapping, chat-control and special-token exclusions are
shared. No assistant, prefix, final-request or private metadata candidates. Keep a piece only if its COMPLETE
mapped source interval lies inside [P,R); drop and count straddling pieces, do not clip them. A message straddling
R may contribute fully old pieces. Deduplicate identical source records; record every exclusion reason.

Both arms receive the IDENTICAL candidate list U with the same candidate IDs/source spans and list hash. The
only policy-specific input to common admission is the ranking key, including the classifier's threshold sentinel:
clf scores each U member as P(rule)+P(fact), original role and empty context, frozen encoder longest_first
truncation at 192 tokens, scoring batches of 64; record truncations. For score s>=0.5, ascending key is
(-s, -message_index, source_char_start, source_char_end). For s<0.5, use (+infinity, -message_index,
source_char_start, source_char_end), meaning ineligible for admission. Exactly 0.5 is eligible; invalid/nonfinite
scores are a harness error. This preserves the frozen threshold without changing U or leaking filtered
membership into rule. It is equivalent to clf threshold-filtering before finite-score ranking, NOT disabling
the threshold. Rule's ascending key is (0 for user/1 for tool, -message_index, -source_char_start,
source_char_end); all keys are finite. Unique source coordinates settle ties deterministically.

Rule takes only U, range and B; it reads no scores, classifier path, thresholds, quotas, realized selections,
counts or echo lengths. Construct its pins without loading the classifier; CPU consumer tests must prove the
same result with an unavailable scorer and with constant-0/constant-1 stubs. Per-arm timed work still includes
its own full candidate construction. Sharing an unscored list definition does not grant a free timed cache.

Implement NEW `admit_whole_spans(ranked, evict_range, B)`: scan the entire keyed list once; skip ineligible
infinite keys; admit the complete span iff the union of already admitted source columns and this span has size
<=B; otherwise record the skip and CONTINUE to the end. Never split, clip, pad, borrow a quantity or stop at the
first oversize span. Underfill is allowed. This explicitly supersedes the break-at-first-nonfit behavior of
`budget_history_spans` for SC1; neither that helper nor `role_pinned_spans`, quota-matching helpers or
`clamp_pins_newest_first` implements this policy and none may be reused unchanged.

**Echo selection versus presentation.** Implement NEW `build_sc1_echo`: selection scans that arm's admitted
spans oldest-first by source start/end, independently of admission ranking. Tentatively append each whole entry;
keep it only if the COMPLETE serialized echo and its increase in final-message token count both remain <=E.
Otherwise skip and continue through all admitted spans. Presentation of the retained entries is chronological
in the same source order. This explicitly chooses chronological selection, not ranking-order selection followed
by chronological display. Pins survive even if their echo does not fit. With no emitted entries, emit no header
or insertion separators; never echo an unpinned span. No padding, clipping or cross-arm dose matching.

Exact header: `Earlier context restated verbatim:` followed by LF. Each entry is
`- ROLE turn MESSAGE_INDEX: JSON_QUOTED_TEXT`, LF-separated, with original user/tool role, zero-based message
index and JSON-escaped source text. Quote both roles as data. Count every header/label/quote/separator token,
including the two LF insertion separator, using the frozen tokenizer; retokenize the final rendered message to
verify its increase <=256. Header is present only with at least one complete entry. Reject control-token content
via the shared candidate exclusion and assert none is introduced by the echo serializer. Report omitted pins,
span lengths, pin/echo use and omission rates by source/role. Equal ceilings permit different actual doses.

Scope resolver, digest, attention amplification and residual steering are OFF in both arms. Verify classifier
artifact hashes at runtime; instrument actual intervention entry points and require each per-run counter=0,
not a hard-coded metadata zero. The user-first rule may fill B before reaching tool facts; a stronger
role-interleaved rule is not tested. This is the intended comparator ordering, not a claim of code/dose identity
with the earlier C2 arm, whose borrowed budget was a defect. Do not add an outcome- or timing-selected third arm.

**Execution order, fresh state and setup.** Use the independent `order` stream (first digest bit) for each
episode to choose clf-first/rule-first with probability 1/2, frozen before outputs. For setup, use the analogous
independent order assignment for full/evicted. Each arm starts from fresh mutable harness state, a new KV cache,
no carried logits and a deep copy of the same pre-decision database/artifact; no cache/state crosses arms or
episodes. Read-only resident weights may be shared; initialization policy and warmup costs are frozen and
recorded. Candidate/scorer/echo results cannot be shared as uncharged timed work.

Setup-only diagnostics are full (no eviction, no pins/echo) and evicted (retain prefix and recent suffix, no
pins/echo), one output each on all 32 setup episodes: 64 setup generations. Before any final launch or outcome
opening, require full passes >=24/32 AND full passes minus evicted passes >=8/32. Freeze and commit a setup
summary with the episode/manifest hashes, both counts, pass decision, measured timing and cost projection;
the final launcher must refuse without that valid committed artifact. A failure means NOT RUN: instrument lacks
competence/headroom, not a final comparison or evidence of equivalence. Final output records remain sealed from
analysts until complete; a separate `--summarize` consumer validates all paired IDs and the setup gate before
opening outcomes. No decisions based on partially produced final results.

**Sole confirmatory analysis.** D=P(Y_clf=1)-P(Y_rule=1) for a fresh source episode from the frozen 75:25-age
authoring mixture. Y=1 iff the parser/schema, complete task and every state/artifact obligation/invariant pass.
Both arms run on identical scripted histories. b counts clf-only passes; c counts rule-only passes; N=256
includes all pairs including ties, with none excluded. Test H0:D<=0 versus D>0 by exact one-sided McNemar:
p=sum_{j=b}^{b+c} choose(b+c,j)*2^(-(b+c)); p=1 when b+c=0; reject at p<=0.05. No mid-p, asymptotics,
outcome-dependent stopping, selective retries, new contrasts or enlargement/reduction of N. Report all four
paired cells, marginal rates, b/c, D_hat=(b-c)/256 and the conservative paired 95% interval [L_b-U_c,U_b-L_c]
from separate two-sided 97.5% Clopper-Pearson intervals on b/256 and c/256. Union-bound coverage is >=95%;
the interval is descriptive, need not exclude zero when McNemar rejects, and is not another gate.

**Adoption, flags and corruption.** Only a VALID, COMPLETE study with exactly 256 pairs can choose a package.
Adopt clf only if p<=0.05 AND b-c>=13 (13/256=5.078125 percentage points), AND U<=2, AND K=0, AND the latency
limit below passes. Otherwise choose rule by simplicity and report "no worthwhile learned advantage demonstrated",
never "equivalent" or "rule superior". The 13-net-win requirement is an engineering threshold on the estimate,
not a test of a population advantage exceeding five points. Failure/latency limits are not population safety
or noninferiority proofs.

Per episode i/arm a, invalid I_ia means parser/schema failure (including zero or multiple calls for tool-work).
Truncated T_ia means hitting 256 generated tokens without complete parseable/schema-valid output; a complete
valid output exactly at the cap is not truncated. For repetition only, Unicode NFKC-normalize decoded text,
casefold, collapse whitespace to single spaces and strip boundary whitespace, then tokenize with the frozen
trunk tokenizer without special tokens. Repetitive R_ia means a contiguous four-token block repeats at least
eight consecutive nonoverlapping block positions, starting at ANY token offset. Evaluate ALL three flags on
every generation, including truncated outputs, and record them separately and F_ia=I_ia OR T_ia OR R_ia.
U=sum_i 1[F_i,clf AND NOT F_i,rule] counts each episode at most once; it is neither a difference of marginal
counts nor three allowances. Repetition enters the operational gate even if the task checker accepts output.

Define K_ia as any checker-detected violation of the episode's explicit protected_set or unauthorized change
outside permitted edits, for BOTH editing and tool-work. Tool-work includes protected records/fields and
non-target creations/deletions; editing includes protected artifact fields/lines and forbidden added keys/
lines/content. K=sum_i 1[K_i,clf AND NOT K_i,rule] must be zero. Use observed paired flags, with no subjective
causal attribution. Report both arms' total corruption counts and paired table; common corruption is not zero
corruption. For syntactically parsed editing artifacts, evaluate protected-set predicates even if schema/task
checks fail. Unparseable output is invalid; do not invent a resulting artifact/state. Parser/schema-rejected tool
operations do not mutate state; record I even when there is no resulting corruption.

**Failures, persistence and cost.** Generation failures, malformed/incomplete results and ordinary token/action/
300-second-budget failures score zero with causes retained. Infrastructure interruption is only a journaled
external host/process loss or device/resource loss that prevents completion; completed bad outputs and ordinary
timeouts are not interruptions. Persist every completed arm atomically BEFORE starting another, with raw output,
token IDs, full verdict/causes and manifest ID; write paired rows in the same run when both arms exist. Keep an
append-only attempt/completed-output hash journal. Resume only a genuinely missing interrupted attempt from
identical frozen inputs/state, retaining prior attempts and every completed arm byte. A hash mismatch or unresolved
harness defect means INVALID, never dropped pairs or changed completed outputs. No partial-cohort inference.

Restore the source's engineering latency gate: mean standalone end-to-end clf latency <=1.25 times rule latency
over all 256 final episodes. Use identical boundaries, candidate extraction through checker completion, including
CPU scoring/admission/echo, prefill and generation. Include completed failures at their actual elapsed time;
for an interrupted arm ultimately completed, sum all its attempt times so retries are not free. Record latency
components, peak host/device memory and initialization costs; one-time equal model loading/warmup is reported
separately and counts in the global cap. Decision (2026-09-04): retain this gate because matching pin/echo ceilings
does not bound CPU or total execution cost. Fable's suggested reported-only latency is overruled prospectively;
this is the more conservative adoption criterion requested by astra F8 and permitted by kimi R5.

Cost cap = 8 single-GPU allocated wall-hours for ALL SC1 model execution: smoke, setup, both final arms,
initialization/warmup, interruptions and resumed work. CPU selector work and authoring effort are reported
separately, also included where applicable in end-to-end latency. Scheduled count is eight smoke determinism
outputs + 64 setup outputs + 512 final outputs = 584, plus no hidden exploratory outputs. No extra setup clf/rule
generations are authorized by this design: measure their CPU selection/echo paths there without using scores
to revise sources or policies. Existing reviewers' larger generation counts are estimates, not the run schedule.

At setup, measure full/evicted prefill and generation separately and both CPU selector/echo paths, including
checking. Freeze the projection formula before execution: projected_seconds = spent_allocated_seconds +
remaining_initialization_seconds + 512 * 1.25 * (t_prefill + 256*t_token + t_cpu + t_check). Here t_prefill
and t_token are the respective maximum setup measurements after the length scaling below; t_cpu is the maximum
measured candidate/selector/echo cost across either policy and all setup episodes; t_check is the maximum setup
checker cost. The 1.25 multiplier is a planning reserve, separate from the latency gate. For each setup attempt
let r=max(1, L_max/L_measured), where L counts rendered input tokens and L_max=8,192 plus the frozen maximum
prefix/final-request lengths and 256 echo tokens. Scale that attempt's total two-stage prefill time by r^2 and
its worst completed generation-step time by r before taking the respective maxima; record the denominators and
all terms. If no usable timing sample exists, defer. Concrete maximum prefix/query lengths and the model/tokenizer
limits must be bounded and frozen with the original API grammar before production authoring. During final
execution replace 512 by the number of remaining arm attempts and increase cost maxima if timings are higher;
do not lower the initial setup estimates to reopen a refused budget.

If setup-measured/projected cumulative execution exceeds 8 GPU-h, defer the final study with all sources intact,
status NOT RUN, without shrinking N. Meter cumulative allocation and reproject after each attempt without
opening task outcomes. Reserve the 300-second attempt ceiling before launching each remaining attempt; if it
cannot fit or actual/projected cumulative time exceeds the cap, stop scheduling further attempts and keep
outcomes sealed. An already started attempt ends under its frozen deadline; do not signal other processes.
If this prevents 256 complete pairs, report INCOMPLETE with elapsed cost/completed counts, no confirmatory or
adoption analysis, and no scoring of never-attempted episodes as model failures. Do not silently resume a
cap-exhausted study beyond its budget. Substantive change requires a new registration and new sources.

**Power, effort and claims.** These are the exact CPU enumerations already independently reported by astra and
fable, not new runs or empirical estimates of SC1 discordance. Under M~Binomial(256,q), wins given M=m follow
Binomial(m,(q+D)/(2q)); sum the exact binomial-tail rejection regions. At true overall D=.05, test rejection
probabilities are 78.222% (q=.10), 50.857% (q=.20), 38.22% (q=.30); requiring BOTH p<=.05 and b-c>=13 gives
51.915%, 49.725%, 38.22%. At D=.10, q=.20 they are 97.356% and 96.954%. Thus the joint statistical/size gate
has only about 49.7% probability at a true five-point gain and q=.20, BEFORE setup, flags, corruption and cost
gates. Fewer than five discordances cannot reject (4/4 wins p=.0625; 5/5 p=.03125), and 13/256 is the smallest
integer gain exceeding five points. The exact-test power is not the adoption probability. This is credible for
a substantial approximately ten-point gain; an inconclusive result is legitimate. The q=.10 row is a low-
discordance sensitivity scenario, not a measured or privileged planning truth for the 75:25 mixture. Retain the
standard-library enumeration source/output and hashes in the executable manifest before registration execution;
kimi's analytic approximation corroborates the numbers but does not replace integer enumeration.

Revised authoring estimate: approximately 35–50 author-hours for 288 compact original specs plus deterministic
expansion/reference/checker/mutation generation and independent review. This is conditional and unmeasured,
not a promise that 288 bespoke hand-written checkers fit the budget; a manual approach could cost 80–120 hours
and is not an automatic fallback. Use eight disposable smoke sources to measure source construction, expansion,
positive/negative validation and independent semantic review separately; publish the production projection before
commissioning. If unaffordable, defer before production authoring rather than reducing N, independence or six-
negative coverage. Freeze the spec language/expander and shared filler before production; no setup-trained
bag-of-words separability test is allowed. Do not fit or train anything for SC1.

Report subgroup success by style/origin/age/scope and realized author/factor counts, override/exact-ID errors,
pin columns, echo tokens/omissions, span lengths, scorer truncations, candidate exclusions, latency components,
failure taxonomy, setup full/evicted rates, all gates and costs. Apart from the explicit overall latency gate,
these diagnostics are descriptive, never selection criteria. The estimand concerns these frozen retention-plus-
echo packages on scripted histories at one pressure setting. It does not isolate pure KV recovery, show that
indirect information is absent from surviving KV, establish general scope resolution, compare all rules, or
demonstrate free-running agent benefit or generalization beyond the authored mixture.

**Required implementation handoff (no implementation in this edit).** Freeze the renderer/layout/position
consumer, scorer-free candidate builder, new admission and echo functions, runtime artifact/intervention checks,
isolated executor, shared checker/validation path, order/fresh-state handling, full hash manifest, attempt journal,
setup/final sealing, cost meter and paired row writer before their respective freezes. Each row records manifest/
episode/arm/order/attempt IDs, raw output/tokens, candidate/rank/admission skips, unique pins, echo coverage/tokens,
per-layer cache widths/positions, latency split, allocated time, I/T/R/union, corruption, success and checker
causes/full state diff. Emit completed rows atomically in the same execution, not reconstructed afterward.
CPU tests must exercise actual consumers with fake scorers/caches: threshold equality and ties, oversize then
fitting admission, boundary pieces, echo overflow/empty output, scorer-independent rule, private-field isolation,
two-stage position preservation, reference PASS and obligation-linked negatives FAIL, complete-state corruption,
consecutive versus scattered repeats (including truncated output), flag union, exact-tail edge cases, cost/gate
refusal and interrupted-second-arm resume preserving first-arm bytes. Freeze script/output hashes for power
arithmetic too. Separate model determinism smoke is a future budgeted prerequisite, not a run authorized here.
No benchmark-cohort tests or full suite is needed for this text-only consolidation.

**Review disposition (text acceptance, not a claim of implementation or reviewer closure).** Astra F1, F3, F4,
F5, F6, F7, F8: accepted; F2: accepted-with-change (75:25 age replaces 50:50); F9: accepted-with-change (35–50 h
spec/expander estimate, measured smoke projection required). Fable V1, V2, V6, V7, F3, F5, C1, C2, C6, P2:
accepted; V3: accepted-with-change (astra/kimi chronological skip-and-continue echo selection overrules
admission-order/stop-on-overflow, preserving the source's literal shared chronology); V4: accepted-with-change
(episode union retained, reported-only latency refuted in favor of the source's cost gate); V5: accepted-with-
change (tool-only corruption overruled by astra/kimi's explicit editing protected set); V8: accepted-with-change
(G1 closes, low discordance is an honest non-adoption result, not a loophole); F1: accepted-with-change (identical
unscored U and key-only policy difference, but threshold-irrelevant recommendation refuted because 0.5 is frozen;
ineligible rank sentinel preserves it); F2, F4: accepted-with-change (structural/dose limitations disclosed, no
guaranteed tool starvation or fixed echo loss, no optional third arm); C3: accepted-with-change (gists/fingerprints,
collisions and semantic audit accepted; domain caps, disjoint domains and hard overlap cutoff refuted because
they alter sampling or reject shared benign filler); C4: accepted-with-change (shared executable validation,
canonicalization and indispensable-literal exclusion, not exclusion of generic schema syntax); C5: accepted-with-
change (measured age validates/repairs its assigned draw, never relabels it); P1: accepted-with-change (75:25
adopted; guaranteed recent concordance and asserted realistic q refuted as unmeasured); P3: accepted-with-change
(spec/expander adopted; fitting a setup diagnostic refuted by lineage/no-training rules); P4: accepted-with-change
(cap/defer accepted, explicit 584 scheduled outputs supersede extrapolated counts). Kimi V1, V2, V3, V5, V6, V7,
V8, F1, F3, C1, C2, C3, C4, P2: accepted; V4: accepted-with-change (astra's earlier three-stage freeze overrules
binding only after episodes); F2: accepted-with-change (chronological whole-entry selection accepted, R8's always-
emitted empty header overruled by astra to avoid an echo when no fact fits); P1: accepted-with-change (use the
astra/fable exact enumeration, retain kimi's approximation caveat); P3: accepted-with-change (timing remeasurement
and defer retained, explicit run counts replace estimates); M1, M2, M3, M4, M5, M6, M7, M8, M9, M10, M11, M12:
accepted as required future harness/manifest/consumer obligations. Kimi replacements R1, R2, R3, R5, R6, R7, R9
are accepted through these clauses; R4 and R8 are accepted-with-change for the stricter freeze and empty-echo
rules just stated. Fable's numbered handoff requirements 1–14 are accepted-with-change to use the registered
threshold, whole-span boundary rule, chronological echo, strict framing, per-arm persistence before paired rows
and budgeted future determinism smoke; no legacy helper behavior or benchmark input is inherited implicitly.
## SC1 AMENDMENT 1 (2026-09-04) — operational and source-validation clauses adopted for DRAFT v2

SC1 AMENDMENT 1 — 2026-09-04. This amendment prospectively adopts the operational and source-validation clauses below for SC1 DRAFT v2. It does not accept a Stage 2 artifact, authorize production authoring, or authorize model execution. Stage 2 acceptance requires the amended science snapshot, reconciled sanitized author contract/grammar, passing consumer regressions and independent disposition of the smoke cue audit. Unresolved requirements below remain freeze blockers. The v2 endpoint, N, factor distribution, policy algorithms, adoption gates and prohibition on outcome-informed revision remain unchanged except where this amendment expressly states otherwise.

Data lineage: fit-on = the previously frozen selector development corpus; no new
fitting. Evaluated-on = newly commissioned, disjoint setup/final sources under the
registered law; these CPU smoke fixtures and their recorded responses are never
production sources or fitting data. No policy/model outcome informed these repairs.
Historical selector-development influence remains disclosed in DRAFT v2 and LEG B/LEG A.

Binding orchestrator decisions (verbatim):

(a) Filler-cue disposition = astra's conservative text C: the contract's relevance rule stays binding; no exception
    for recognizable filler; Stage 2 acceptance requires the independent review of the frozen source/expansion law and
    smoke evidence, which will be performed in the NEXT review round on your output (not a separate round).
    In addition: the expander must never place formulaic filler as the newest eligible old user turn; add that as a
    source law + validator rule + test (so the smoke shortcut astra names is mechanically excluded).
(b) Abandoned-cost disposition = astra's text G (separate reporting; 8 GPU-h cap cumulative per registered study).
(c) Snapshot definition = fable's clause-1 replacement + astra's B (algorithmic: exact concatenation of the SC1 DRAFT
    v2 section, the accepted AMENDMENT 1 text, and the reconciled sanitized author contract; byte ranges and hashes
    recorded); add a `snapshot` producer mode to scripts/sc1.py (V2).
(d) Adopt astra's A, D, E, F, H and fable's precisions for clauses 3, 6, 11 verbatim.

### 1. Registration identity and snapshot

Stage 1 is a JSON object with `status: "REGISTERED"`, a unique `study_id`,
absolute `execution_root`, `trunk: "4b"`, `science_snapshot_path`, `science_hash`,
`science_parts`, `deployment`, and `authors`. `science_parts` contains the three
ordered provenance records emitted by `snapshot`; the companion
`data/sc1/registration-snapshot.json` is also manifest-bound.

`science_snapshot_path` is `data/sc1/registration-snapshot.md`; `science_hash` is its SHA-256. The snapshot is
produced mechanically at freeze time as the exact bytes of LEDGER-PLAN.md from the line beginning
`## SC1 — LEARNED vs RULE SELECTOR, BENCHMARK-FREE FROZEN-POLICY COMPARISON (DRAFT v2` through the end of that
file (which at freeze includes this amendment), immediately followed by the exact bytes of
data/sc1/AUTHOR-CONTRACT.md, with nothing inserted; the two part lengths and the file hash are recorded in the
handoff. It is regenerated, and the executable manifest re-frozen, whenever that ledger section or the contract
changes before Stage 2; after Stage 2 the snapshot is byte-frozen and later LEDGER-PLAN.md entries do not affect
any manifest or test. The Stage 1 JSON file is byte-frozen after registration; its SHA-256 (`registration_hash`)
is bound into the study identity by every consumer.

At Stage 1 freeze, science_snapshot_path is data/sc1/registration-snapshot.md and science_hash is its SHA-256. The snapshot is the exact concatenation, with no inserted bytes, of (1) the SC1 DRAFT v2 section, (2) the accepted SC1 AMENDMENT 1 text, and (3) the reconciled sanitized author contract. Record each source path, source commit, half-open byte range, byte length and SHA-256, in this order, in the Stage 1 registration. Exclude subsequent editorial ledger entries using these frozen boundaries. The executable and production manifests bind these same snapshot bytes and the corresponding author contract/grammar hashes. The eff241b snapshot predates Amendment 1 and must be replaced prospectively; regenerate and verify the executable manifest before accepting Stage 2 or authoring any production source. Snapshot tests use the recorded byte boundaries, not the entire future tail of the live ledger. Only the sanitized contract, assignments and original grammar are sent to authors; the science snapshot and reviews remain private.

The following boundary rule reconciles the mechanical initial through-EOF recipe
above with the three-part law: at this amendment's initial freeze it is the final
ledger section, so both recipes produce identical bytes. The producer locates the
exact DRAFT v2 heading and this amendment heading, uses the v2 bytes up to this
heading and the exact adopted amendment length, then appends the contract bytes.
Later editorial sections are excluded; their presence does not extend a frozen
range. `CUDA_VISIBLE_DEVICES='' uv run python scripts/sc1.py snapshot` records
half-open byte offsets, lengths, SHA-256 values and full source commits for all
three parts. Commit source ranges first; the producer verifies their committed
bytes. It inserts no separator or metadata in the Markdown snapshot. Copy its
`parts` array into Stage 1 `science_parts`; every consumer checks that array against
the executable manifest. The sidecar is provenance, not a fourth snapshot part.

`deployment` must equal the executable manifest block: bfloat16,
hf_compatible, temperature 0, greedy true, max_new_tokens 256, deadline 300,
eos_ids [151645,151643], nonthinking_opener as frozen, one resident initialization
per invocation/no warmup, max_prefix 2048, max_query 1024, position_guard 40960.
Stage 2 hashes the actual 4B checkpoint, tokenizer, configs, executable code,
dependencies, parser, grammar and filler bytes.

`authors` has exactly kimi-k3, fable, gpt-6-astra and Opus keys. Each value includes
`provider`, `immutable_version`, `settings` (temperature, top_p, reasoning_effort,
max_output_tokens, seed_support), exact `neutral_template`, `contract_hash` and
`grammar_hash`.
The provider seed is the unsigned integer represented by the first eight hexadecimal digits of the current content attempt's authoring-stream SHA-256 digest. Retain that mapped value for every attempt. Apply it exactly when the frozen provider supports seeds; otherwise record that it was not applied. Do not substitute the author version, settings or seed mapping.

### 2. Registry and audit receipt

One study has one absolute execution root; relocation is refused. A durable
per-checkout registry at `.git/sc1-studies` binds study and source-fingerprint
ownership; new registrations require new production sources. This is a local
trusted-operator guard, not a global cross-checkout uniqueness service. Each stage
binding publishes an immutable `registration-audit.<stage>.json` with the study
ID digest, registry location/hash, complete entry (including manifest IDs) and
source-owner file hashes, and appends those bytes to WORKLOG.md. The receipt
captures the registry at that binding, not an assertion that mutable registry
bytes never change when another stage is bound. Review that audit before launch.

The receipt is appended to WORKLOG.md by the consumer itself; that append is committed with the run's artifacts.
A CPU registration-binding/audit step and its review must precede model allocation.
Run production consumers only when no coder/reviewer wrapper holds `.review.lock`.

### 3. Exclusive execution-root lock

All determinism/setup/final consumers and analysis (which may recover journals or
publish pairs) acquire a nonblocking exclusive execution-root lock before opening
mutable journals/meters or constructing a backend, and retain ownership through
final durable publication. A second owner is refused immediately; no waiting,
unlinking the lock inode, or process signalling. Root binding alone is insufficient.

The lock is an advisory `flock` on `<execution_root>/.execution.lock`, valid on the executing host only; the registered absolute `execution_root` must be a local filesystem path.

### 4. Source geometry and pressure

Freeze FILLER_VERSION SC1-incidental-v2, the 512-item
subject/verb/place sentence pool and its manifest hash. Sample without replacement
within each episode using the filler seed. Expand designated non-evidence,
non-trace turns round-robin, covering user/assistant/tool roles. Every authored
base and every final rendered history turn is at most 600 tokenizer tokens in
its text (chat delimiters are counted in rendered history, not that text cap).
Designated turns × 600 must exceed 4608 minus rendered base history, with room
for existing base text and whole-sentence packing; typically at least eight turns
are needed. The expander reports base tokens, usable capacity and a lower bound
on total turns needed. The history minimum is checked after each round-robin
batch, so 4608 is a minimum target, not an exact length; eff241b smoke observations were
approximately 4620–4699; these are historical measurements, not an acceptance range. Full acceptance still requires history 4096–8192,
U >= 2B and at least one actual budget skip. No causal evidence is moved or
relabelled to fit. Grammar capacities/complexity limits apply before source freeze.

`filler_turns` are zero-based indices into authored `turns`, excluding the system
prefix. The expander must never place formulaic filler as the newest eligible old
user turn. Define that turn using the common, unscored candidate builder after
expansion: the greatest user message index with at least one complete candidate
piece inside the removable old range; a straddling turn can qualify. If such a
turn exists it must not be filler-designated and none of its text may contain a
sentence from the frozen formulaic pool, including author-supplied base text.
The expander and bank validator reject violations and report the index. They do
not move evidence, silently skip filler placements, or choose a source according
to either policy's retention. A source must be repaired under its original factors.
Retain bank-consumer negative tests for both designated expansion and undesignated
base-text insertion, plus positive checks on all eight frozen smoke sources.

### 5. Induced population and cue disposition

Disclose the induced population: the eff241b smoke design's disclosed filler
occupied over 90% of candidate columns. Most retained rule pieces came from the
newest old user filler turn. OLD retention was therefore strongly determined by
author turn ordering; this setting may chiefly compare rejection of formulaic
filler against user-first recency. This is not a measured classifier advantage
or a general claim about realistic histories. Production authors remain blind.

Report per episode candidate_columns, real_candidate_columns, B, budget skips,
echo omissions, role/position geometry and per-arm pin composition (pieces and
columns from designated filler turns versus other turns). Here "real" means
non-designated-turn provenance, not semantic necessity; original base prose in a
filler turn counts with that turn. The smoke README carries the concrete
role/position/wording audit and measurements.

The eff241b smoke audit documents a potential relevance shortcut: formulaic filler dominates old candidates and occupies the newest eligible old user turn in all eight smoke sources. These fixtures establish mechanical pressure but do not establish compliance with the author contract's prohibition on relevance revealed by marker, role or position alone. That prohibition remains binding. Stage 2 is deferred until an independent review of the frozen source/expansion law and disposable smoke evidence explicitly accepts compliance or a further prospective Stage 1 amendment specifies a narrower population and its claim limits. Any source-law or executable repair occurs before production authoring, uses no policy/model outcomes, preserves factor assignments and is followed by smoke validation and re-freeze. Neither a high U/B ratio, mixed roles nor this disclosure constitutes that acceptance. Do not select or reject a production source according to whether either tested policy retains its evidence.

The next independent review round on this output performs that source/expansion
law and smoke-evidence review; no extra intermediate review round is required.
The new placement guard mechanically excludes the documented newest-old-user
shortcut, but does not certify absence of other role, position or wording cues.
The updated smoke README reports the candidate's measurements and remaining cues.

### 6. Evidence and public tool state

Every decisive fact and trajectory entry is a necessary,
obligation-linked dependency with a unique verbatim public evidence span. Every
trajectory event has user authority in an actual user turn and the assigned
scope. Continuing requires instruction; overridden requires superseded then
update; cancelled-or-completed requires obsolete then cancellation or completion;
switched requires switch then return. The full necessary dependency determines
age. Unsupported structures require repair within the original assignment.

This amendment narrows the author contract's general realistic-JSON-or-plain-text allowance for state-bearing returns. Every state-bearing public JSON block must be exactly the canonical {call,return} envelope on its own line in its chronological tool trace turn, with a return equal to finite-executor replay; no additional state-bearing block is allowed. Inspect complete multiline and nested values without discarding overwritten object members. Duplicate object names in public JSON blocks are invalid and cannot be treated as incidental prose. Incidental plain prose and non-state JSON may surround a valid envelope but may not purport to supply untraced state. Freeze this boundary in the sanitized author grammar and require bank-consumer regressions for duplicate-wrapper and multiline state before Stage 2 acceptance.

Typed answer inventories cover every payload/target literal and its necessary
evidence/obligation links. Independent reviews bind source and public-render hashes.

Only JSON-syntax blocks are mechanically checked; state-like non-JSON prose is a Stage 3 semantic-review item.

### 7. Fingerprints and independence flags

Fingerprints jointly alpha-normalize entities/literal equality classes and
unordered graph permutations. Reject unordered groups above eight entries or
more than 40,320 joint variants before source acceptance. Pair signatures bind
both source IDs/hashes and an independent reviewer session. Source-content hashes
exclude provenance/review to avoid circularity; complete provenance is separately
manifest-bound. Within-pool entity/identifier reuse is a Stage 3 review flag
(fable N8); cross-pool collisions are rejected. Flags do not certify independence.

### 8. Exact numeric law

JSON numbers are compared by exact finite value with booleans distinct; integral decimal spellings satisfy integer schemas. Supported number spellings have at most 1024 lexical coefficient digits, counting every digit before and after the decimal point, including leading and trailing zeros, but excluding sign, decimal point and exponent digits. The stored Decimal exponent must have absolute value at most 4096, and exact canonical serialization must also satisfy the coefficient/exponent limits. Unsupported spellings or construction failures are ordinary parser/schema-invalid outputs, retained and scored once without harness invalidation or retry. Representability is a property of the spelling as well as the value. Wrong-number negatives negate nonzero values exactly without Decimal-context rounding and replace zero with one.

### 9. Text edit permissions and semantic witnesses

Text tasks have `permitted_paths: []` and explicit nonempty zero-based
`editable_lines`. After the production newline/trailing-whitespace/blank-run
normalization, only replacements at those indices are permitted. The original
`initial_state` fixes the line count and every noneditable line. Both reference
and expected artifact must preserve that baseline before freeze; matching an
inconsistent oracle cannot waive permissions. `permitted_edits` is the reserved
implicit invariant. Insertion/deletion or a protected-line change is corruption,
including otherwise schema-invalid parsed text. Wrong values wholly inside an
editable line can fail the task without causing corruption.

Text old-ID/obsolete/cancelled witnesses store raw full artifacts in old_id_work, obsolete_work or cancelled_work on linked public trajectory entries. Compare reference and witness using the production text normalization and ordered line indices, never JSON parsing or JSON string quoting. A witness line is changed when its normalized value differs from the reference at that index; a value already present at another index is still a change. Require a distinct normalized artifact and every changed witness line in the linked event's public evidence, with the applicable assigned scope, schema validity and violation of its linked obligation. A legitimate reordering or repeated-value replacement must not be rejected merely because the set of line values is unchanged. Applicable attacks may not be relabelled inapplicable to bypass this validation.

A text wrong-entity witness includes `line`, `target_id`, `replacement_id`,
`evidence_id`, `output`, and `obligation_ids`: exactly one normalized line replaces
one occurrence of the target ID with a different declared entity ID; both IDs
must occur in the linked public evidence. It must remain schema-valid and violate
its linked obligation. No truly applicable attack may be relabelled inapplicable
to bypass unsupported validation. Six distinct negatives and full invariant
coverage remain required.

### 10. Author transport and retained attempt history

A fresh isolated session writes one source; up to two repairs
resume only that same source's session. No session is reused for another source.
Each cumulative transcript JSON contains `session_id`, `provider`, `version`,
`settings`, `input`, `response` (the exact source object), and `messages` (the exact
alternating user-input/assistant-source pairs for attempts 0 through the current
attempt). No unrecorded prior context is allowed. This transport profile supplies
no system/developer inputs; a provider that necessarily supplies any such input
must expose it for prospective contract/schema reconciliation before registration,
not silently drop it in conversion. CPU tests do not establish provider isolation.

`attempt_history` entries contain zero-based `attempt`, `previous` (prior complete
entry hash, null initially), `feedback` (prior rejection reason, null initially),
`request_hash` (canonical hash of the commissioning_request function envelope),
`transcript_path`, `transcript_hash`, `source_hash`, `decision`, `reason`, and
`reviewer`. Accepted entries may omit reason/reviewer; rejections require both.
Retain all requests, responses, inputs, feedback and decisions; reject missing
attempts or a chain above three. Provenance binds session, exact settings,
prompt/input hashes, provider, transcript and isolation/originality attestations.

Only `*.input.json` is delivered to an author. Its canonical input hash and file
SHA-256 are retained in `*.request.json`; that separate operator envelope holds
private order/setup-order streams and retained prior attempts. Do not send the
operator envelope or repair history files to an author. Exact transport-message
history is validated independently of the private envelope's file packaging.

### 11. Determinism prerequisite

Use the two lexically first frozen smoke IDs in two fresh
processes, with both arms in each process: exactly eight retained observations.
Each cell binds deployment, frozen episode/input, initialization, token IDs and
immutable arm/output hashes; the certificate binds two closed, charged allocation
intervals. Every cell must complete generation without timeout/generation failure
and contain nonempty generated token IDs. Task success is not required; a
nonempty deterministic malformed answer can qualify. Cross-process token/input
equality is required separately for each source/arm cell.

A cell whose total wall time exceeds the 300 s deadline is recorded as `timeout` even if a full token stream was produced and does not qualify.

### 12. Abandoned work and separate cost reporting

No replacement of an incomplete or failed determinism schedule, and no selective additional output, is permitted under its study ID. The prerequisite is deferred or failed, with all retained outputs, incomplete work and allocation evidence preserved. This amendment adopts separate reporting of abandoned-study cost: the eight-hour cap applies cumulatively within each registered study, including its determinism, initialization, interrupted and resumed intervals. A newly named registration requires a new execution root and new production sources under v2; it is not automatic and cannot rescue outcomes from the abandoned bank. Before any restart, record predecessor study IDs, allocation artifact hashes, external loss evidence, abandoned GPU seconds and total cumulative SC1 program effort in WORKLOG.md and the new registration's cost disclosure. Preserve each predecessor's charged ledger; do not present the new ledger as total program cost or claim that all SC1 effort fits within eight hours. No cost reset or selective restart is authorized merely by an interruption.

### 13. Failure records and conservative cost projection

Caught journal-write failures require reconciliation of actual durable bytes
before another append. Retain recovery proof before a separating newline; atomically
prepared outputs already represent completed work and are published on recovery,
never regenerated. Recovery failures propagate with the original durable evidence
intact. Completed bad outputs/timeouts are scored once. Host/device/resource loss
requires external evidence for genuinely missing work; unresolved harness defects
invalidate the study, never cause selective reruns.

R detects periods 1, 2 and 4 using the registered four-token algorithm, not all
possible loops. QwenBackend returns timeout or raises exceptions; GenerationFailure
is currently reachable only from fixtures. RuntimeError messages mentioning
cuda/nccl/device/out of memory are provisionally classified as infrastructure,
including possible harness bugs; operator evidence/judgment is mandatory before
resuming missing work. `analysis.json` includes this failure-taxonomy disclosure.
Only actual attention-amplification and residual-steering entry points have
measured zero counters; scope/digest execution paths are absent, not measured zeros.

This amendment adopts projected_seconds = spent_allocated_seconds + remaining_initialization_seconds + remaining_arm_attempts * 1.25 * (t_prefill + 256*t_token + t_cpu + t_check + t_persistence), with the v2 scaling and retained maxima. t_persistence is the maximum measured arm-persistence overhead; the future initialization reserve is at least the maximum measured invocation initialization. Keep the separate 300-second per-attempt reservation and never lower retained maxima to reopen a refused budget.

Actual Qwen determinism and GPU timing remain unperformed, separately authorized
prerequisites; these CPU artifacts cannot certify either.

<!-- END SC1 AMENDMENT 1 -->

## FOCUS-1 — SET/HOLD/SWITCH/CLEAR SCREEN ON FROZEN QWEN (DRAFT v1, 2026-09-04; NOT YET REGISTERED)
Data lineage — fit-on: separate operand-balanced synthetic extraction examples generated by seeded `scripts/focus1.py`, plus the separate setup slice for selection only; evaluated-on: 64 fresh seeded test episodes, disjoint from extraction/setup; trunk: frozen Qwen3-1.7B. No benchmark under `data/bench`, b3 data/probe/response, SC1 setup/final episode, or existing fitted vector/checkpoint may enter extraction, selection, or generation. No fitting/training is authorized here.
STATE: draft only; Brian shelved SC1 after round-5 repair, with no episode authoring. Next: CPU harness/review under `tools/codex-agents/focus1-harness.md`; GPU execution awaits actual registration and the end of the existing BFCL preflight. This section records the conservative choices below for that review; it does not amend SC1.

**Question and competence.** Can an oracle A/B/OFF address select two existing skills, survive a delay, switch, switch back, and release control on a frozen trunk?
A = ascending sort; B = descending sort; inputs are 5–8 distinct integers in [-9,9], output one JSON array, no prose. Every decision uses fresh operands; ascending, descending, and original order are distinct.
Before extraction/selection, require >=29/32 (90.625%, hence >=90%) exact answers for EACH skill with its cue visible on the 32-episode setup slice, using the same operands for A/B; also require >=31/32 complete two-query neutral-copy pairs with OFF.
These skills are proposed, not yet demonstrated on this trunk. Failure closes FOCUS-1 as INELIGIBLE; 4B is not needed or authorized by this registration. Any 4B attempt requires a new prospective registration, never a test-outcome fallback.

**Synthetic law and freeze.** Seed Python `random.Random` (MT19937) with the big-endian integer SHA-256 of UTF-8 `focus1-v1:20260904:<split>:<episode>:<purpose>`; split is extraction/setup/test, episode is a zero-based decimal index, and purposes are sort0..sort3/copy0/copy1/randomA/randomB/armorder (extraction uses sort0). Freeze Python version, generator, tokenizer and prompt bytes before GPU setup.
Extraction: 64 operand lists, 16 of each length, each appearing identically in A/B/no-cue contexts (operand-balanced contrasts); setup: 32 episodes, 8 per length; test: 64, 16 per length, with 8 initial-A and 8 initial-B per length.
Each setup/test episode has four sorting lists and two neutral-copy lists, all of its assigned length; lengths ascend in equal-sized blocks. Use RNG.sample(range(-9,10),length) then RNG.shuffle; reject sorted/reverse-sorted lists and unordered-set collisions across lists/splits, redrawing only by this outcome-blind law in extraction/setup/test, episode, sort/copy order.
Counterbalance initial addresses by episode index within length; pair opposite-initial-task neighbors as donors. Seeded draw order and rejection counts are manifest-bound; different seeds alone do not certify disjointness.
Generate and hash all banks once in the CPU generation-only step before GPU setup; GPU setup/extract/select never read test inputs. No redrawing after model output, filtering to successful episodes, new tasks, arbitrary-ID recovery, or SC1 authoring machinery.
Cue-visible prompt: `Sort these integers in {ascending|descending} order. Output only a JSON array. Integers: {x}`; cue-absent prompt: `Process these integers. Output only a JSON array. Integers: {x}`; use the existing Qwen non-thinking chat wrapper, greedy decoding, batch 1, max_new=64, existing EOS IDs 151645/151643.
Remove the cue BEFORE tokenization/prefill of measured decisions: no hidden cue-bearing KV, task label in prompt, exemplar, answer, text echo, retrieval, or pin. Operands stay visible; the oracle sets its address out of band, before seeing operands.

**One actuator and one dose.** Choose residual addition only; no gate-vs-vector competition. Reuse `scripts/function_vectors.py`'s extraction/grid pattern and `src/stencil/function_vectors.py`'s `mean_difference` / `make_residual_hook`, replacing the b3-bound data path entirely.
At layer INPUT L in {12,16,20}, capture the final prompt-token state on the extraction A/B/no-cue triples; v_t,L = mean(h_t,L - h_OFF,L), computed in fp32. No gradients, optimizer, trunk updates, or pre-existing vectors.
Set rho_L = (||v_A,L||2 + ||v_B,L||2)/2 and u_t,L = rho_L*v_t,L/||v_t,L||2; nonfinite/zero norms invalidate that layer. Report norms/cosines; only this frozen direction pair can carry the selected task, never operand-dependent vectors.
Candidate grid: alpha in {0.5,1,2}, L in {12,16,20}, lexicographic (alpha,L), at most nine cells. Injection = alpha*u_t,L at the current final prompt position predicting token 1 and each subsequent decoding position; OFF = no hook. Never inject into earlier prompt positions or neutral delay tokens.
Select the FIRST eligible cell on setup only: >=24/32 cue-absent exact sorts per task; >=31/32 complete CLEAR/replay neutral pairs per task; >=4/32 KEEP old-task impositions per task; and <=1/32 episodes with breakage in each evaluated arm. Use each episode's sort0 list for both immediate sorts (also the visible-cue gate), then the CLEAR procedure below with each actual reply replacing BACK; no statistical claim from setup.
Freeze the selected L, alpha, vector bytes, extraction/setup outcomes, seed law, code/trunk/tokenizer hashes, decode settings, prompts, delay and scoring in one manifest before opening test. No eligible cell => FAIL-ACTUATOR, no expanded grid or test run.
Reuse Qwen's `residual_hook` and `prefill_with_eviction` with pre-query ordering; `scripts/clf_probe_check.py --vectors/--fv-grid` is a manifest-consumption example ONLY, never a callable data source. Its old grid choice and clearing score do not govern FOCUS-1.

**Matched episodes, hold and transplant.** Four decisions: SET, HOLD, SWITCH, BACK. Correct-address schedule is (a,a,other(a),a); swapped and transplant schedules are its complement. Both directions occur equally often.
Maintain only the enum A/B/OFF between decisions, not activations/answers/KV from prior sorting replies; hooks are off during delays. D=128 tokenizer tokens from repeated `The room is quiet. The light is steady. `, truncated in token space, processed while the latch survives SET->HOLD and SWITCH->BACK; no intervening cue.
For sorting decisions, build one canonical cue-free neutral-prefix KV, then deep-clone it across arms before processing the identical current prompt; earlier generated answers are excluded from that common prefix. Absolute positions, all K/V tensors, prompt IDs and initial logits are hash/equality checked. Within a reply, generated prefixes may naturally diverge.
Five arms at every sorting decision: correct, swapped, shuffled, OFF, transplant. Shuffled uses per-episode directions r_A/r_B from d_model successive RNG.gauss(0,1) draws on their own streams, rescaled to rho_L, indexed by the correct schedule and held across the delay; zero/nonfinite draws invalidate the fixture, no redraw to make a weak control.
Transplant copies ONLY the opposite-task donor's enum at the matched phase, captured before either current operand list is read; no donor tokens, KV, hidden states, output or answer. Require donor/recipient different operand sets and correct donor-task answers on RECIPIENT operands; sham own-state transplant must reproduce correct-arm tokens on setup.
Shuffled directions preserve dose/norm but destroy the task mapping, adapting `archive/PLAN.md` Phase 4's sham/donor/shuffle logic. Oracle swap and enum transplant are deliberately equivalent interventions, not two independent replications or evidence of learned memory.
Each complete switching success requires all four exact operand-sensitive answers, including delayed HOLD and return at BACK; score partial checkpoints descriptively, never as additional independent samples. This is an externally maintained latch screen, not autonomous persistence or a continuous conversation test.

**CLEAR on genuinely retained KV.** After the correct arm's BACK reply, retain its actual generated tokens and steered K/V (including the last generated token); fork this SAME contaminated snapshot for CLEAR (enum OFF, hook removed) and KEEP (old address/dose remains).
Append two successive neutral prompts: `Copy these integers in exactly the given order. Output only a JSON array. Integers: {z}` using the episode's two fresh unsorted lists. Keep each fork's first neutral reply in its history for the second; no cache eviction, reconstruction, text deletion or reset is permitted in primary CLEAR.
Score exact copy on both queries; separately mark an old-task imposition when an answer equals the old task's sorted version of that query's list. Check both immediate and subsequent neutral work; clearing does not erase already emitted text.
Residual-KV audit: for EACH CLEAR query independently replay its exact token history with OFF from an empty cache (including the actual earlier steered/neutral answer tokens, teacher-forced), then answer the same query. This diagnostic clean replay intentionally changes KV, is not a matched treatment arm, and may not replace the retained-KV result.
Record every-layer K/V max-absolute differences, first-decision logit differences, and full greedy token equality vs this replay; report nonzero residuals even if neutral work succeeds. Assert nonempty caches/tokens and actual nonzero-dose hook events; zero counters or hook removal alone cannot certify clearance.
The existing `generate_injected(clear_after=...)` REBUILDS KV: do not use that clearing path. Failed retained-KV CLEAR cannot be rescued by cache rebuilding. CLEAR establishes behavioral release on these queries, not bitwise erasure of state.

**Scoring and statistical decision (one record per episode, N=64).** Use only SC1 short-output primitives `sc1_episodes.parse_json` / `json_equal`; require array length, finite integral values and no booleans, then exact expected-list equality. Never invoke its episode compiler, evaluator, cohort loaders, or runner.
S_i = correct SET AND HOLD exact; O_i = OFF exact at those same two recipient targets. SET requires sum(S)>=48, >=24/32 in each initial-task stratum, sum(S-O)>=16, and a one-sided exact McNemar win over O.
W_i = BOTH swapped AND transplant arms complete all four DONOR-target answers; V_i = OFF complete on those same donor targets. SWITCH requires sum(W)>=48, >=24/32 per initial task, sum(W-V)>=16, and exact McNemar wins over both V and R below, each with net gain >=16.
R_i = shuffled arm completes EITHER the entire recipient OR entire donor four-answer schedule. Require sum(R)=0 AND exact lower-tail Binomial(64,0.10) p<=alpha_f; this tests a predeclared unacceptable 10% switching rate, never “no significant benefit” or a claimed chance rate.
C_i = retained-KV CLEAR AND its clean replay both copy both neutral lists exactly; K_i = KEEP copies both exactly. CLEAR requires sum(C)>=63, ZERO old-task impositions after CLEAR, net sum(C-K)>=8, an exact McNemar win over K, AND upper-tail Binomial(64,0.90) p<=alpha_f. KEEP must impose the old task on at least 8/64 episodes, ensuring release is tested against active interference.
Three endpoint families use alpha_f=0.05/3=1/60; all tests WITHIN a family are conjunctive, with no favorable-test selection. McNemar p = sum[j=b..b+c] choose(b+c,j)/2^(b+c), b=treatment-only successes, c=control-only; b+c=0 gives p=1. Exact binomial tails include the observed count.
Recomputed boundaries: P(Bin(64,.90)>=63)=0.00956314971305463; P(Bin(64,.10)=0)=0.0011790184577738583; P(McNemar b=8,c=0)=1/256. Count floors grade magnitude; the exact tests establish evidence. Report all paired tables and denominators, including stratum counts, regardless of verdict.
PASS requires competence/selection/integrity gates, ALL three endpoint families, shuffled rejection and safety gates. Any complete valid test failing any requirement is FAIL for this actuator/dose/trunk; no partial PASS or claim that internal focus is impossible.
Claim ceiling on PASS: content-free oracle controllability of demonstrated frozen skills, including externally latched delay, donor-directed switching, switch-back and measured behavioral clearance. No autonomous focus, learned controller, necessary recurrence/oscillation, identified biological circuit, long coding competence or new skill learning.

**Breakage, budget, stop rules and records.** I=empty/unparseable/wrong output schema; T=64-token cap without EOS or deadline; R=existing function-vector repeated-4gram fraction >0.5 (also on truncated outputs); breakage=I OR T OR R. Incorrect sorting/copying in a valid array is task failure, not automatically breakage.
Aggregate breakage as one binary per episode per arm over that arm's evaluated replies; CLEAR/KEEP/replay each have their own arm totals. Require <=1/64 in EVERY arm; valid repeated task impositions are caught by CLEAR/W/R criteria independently. Stop as soon as an arm's second broken episode makes PASS impossible; retain partial data, never drop/replace bad outputs.
GPU cap <=6 GPU-hours =21,600 allocated GPU seconds TOTAL across load, timing, competence, extraction, selection, test, replay/audit and interruptions; CPU drafting/tests now only. No model/GPU launch until BFCL preflight has ended with a recorded terminal status (not necessarily a pass), and this draft is actually registered.
Timing smoke FIRST within `setup`: on setup data cover extraction prefill, longest delayed sort/decode, dirty-KV CLEAR/KEEP and replay; record load time, prefill/decode/check/persistence rates and peak memory. Freeze per-attempt cooperative deadline=min(300s,4*measured worst-case attempt estimate); no external timeout/signal.
Before each mode/attempt project spent + remaining reload costs + 1.25*remaining work at retained worst measured rates; include all nine setup cells until selection stops and both neutral replay queries. Launch only if projection <=21,600s AND a full next deadline/load reservation fits; never relax this cap to the protocol's 2x allowance.
If projection fails, budget expires, competence fails, no cell qualifies, integrity fails, or a stop floor becomes impossible, stop scheduling work. Return normally at cooperative checkpoints; never terminate/signal a process, launch background work, or fit/train anything. No test peeking, optional stopping for success, selective retries, or expanded model/dose search.
An already impossible outcome/safety gate yields FAIL with partial denominators and no final-N p-values; other incomplete/budget/infrastructure runs yield INCOMPLETE with missing counts and charged time. Any actual cap overrun forbids PASS; harness/data-integrity defects => INVALID. Preserve every attempt/exception; no resumption/replacement in v1 or verdict inferred from a broken harness.
One small `scripts/focus1.py` with setup/extract/select/run/analyze modes and `src/stencil/focus1.py` helpers; CPU fake-trunk tests, no new evaluation framework. `setup --generate-only` and `analyze` must never initialize a model; all actual GPU stages are deferred operator work.
Write raw per-decision JSONL DURING each run: episode/split/phase/arm, source and recipient IDs, inputs/expected answers, enum/donor state, vector/hash/norm/dose, prompt/KV/position hashes, raw tokens/text/EOS, hook events, exact scores, I/T/R, CLEAR/replay deltas, timings/charged intervals and exceptions; manifests bind code/data/trunk/selection. Analyze only those records; no fresh generation.
Store under `results/qwen/focus1-v1/`; dry-assert every required field with fake trunks before any real run, preserve completed records before aggregates, force-add registered results when later authorized and verify tracking with `git ls-files`. CPU passing is not GPU timing, competence or a science result.
Reviewers: grade low/medium/high/critical honestly; zero open high/critical before registration, no severity bargaining. Independently recompute arithmetic and audit leakage, matched caches, control non-vacuity, residual-KV clearance and budget; adopt the conservative reading, record unresolved ambiguity here, and close/refute prior findings with evidence without deleting them.

**FOCUS-2 sketch — only if FOCUS-1 PASS; exactly ten lines, NOT REGISTERED:**
1. Adapt `src/stencil/wave.py`'s WaveController/WaveRNN architecture; its positional checkpoint is not a skill selector.
2. Emit A/B/OFF through fixed gain patterns over the FOCUS-1 actuator; keep trunk and direction pair frozen.
3. Generate new separate synthetic training/validation/test examples; exclude every FOCUS-1 evaluation and benchmark response.
4. Reuse `INTERNAL-WAVE-PLAN.md` and `scripts/w0_train.py`/`w1_train.py`'s gradient-through-frozen-trunk recipe as code reference only.
5. Train on canonical short continuations with trunk parameters requires_grad=False, retaining the actuator-to-loss gradient path.
6. Prove finite nonzero controller gradients and detached-actuator failure; never import those top-level training scripts.
7. Normalize hidden-state inputs and recurrent state separately to address the earlier scale mismatch.
8. Compare recurrence with an equally tuned nonrecurrent latch and a stateless controller under identical budgets/actuators.
9. Require matched reset and donor-state transplant dependence for a memory claim; remeasure hold, switch-back, CLEAR and breakage.
10. Claim oscillation only with a measured win over nonoscillatory controls; write a separate registration and budget before training.

## SC1 AMENDMENT 2 (2026-09-04) — expansion law: source-authored incidental content; no reserved filler forms; lawful layouts

Replace the fixed SC1-incidental-v2 subject×verb×place pool and its irrelevant-only
placement law with FILLER_VERSION SC1-source-authored-incidental-v1. There is no
closed sentence/template family reserved for irrelevant padding. Each structured
source supplies incidental_sentences: distinct self-contained authored public
sentences with no cross-sentence causal ordering dependency. Ordered incidental
events belong in authored turn bases. Public forms, roles and eligible positions
must overlap necessary content, so relevance requires the task and causal context.
The compiler never invents decisive facts or incidental prose. The roughly 300–800
token authoring target applies to the causal specification alone, not the required
incidental content; completeness remains mandatory.

The source supplies filler_turns as its lawful ordered layout of at least three
distinct zero-based turns covering user/assistant/tool roles. Necessary evidence
and canonical trace envelopes may share designated turns with incidental prose.
The expander preserves every base and causal event at its authored location,
orders only the source's incidental sentence indices by SHA-256 of the existing
filler seed plus "|" plus the decimal index, and appends without reuse in the
source's round-robin placement order. Skip only turns whose 600-token text cap
would be exceeded, never because of relevance, role ranking or policy retention.
Exhausted authored content or capacity fails rather than inventing more content.
Store the materialized authored-sentence hash, selected indices, seed, placements
and base texts in filler_manifest. This private designation is not a relevance
label. Source review must check the public forms and contextual relevance of both
base and appended content, including any potential untraced state prose.

Preserve source-specific causal text/event order and original factor assignments.
Index 1 must not uniformly identify OLD decisive facts; the newest eligible old
user must sometimes contain necessary content and sometimes incidental content.
The expander does not move evidence or relabel age. Source authors supply lawful
layouts under the assigned age. These obligations are not production factor
balancing quotas, source selection by policy retention, or a relevance exception.

Retain the no-formulaic-newest-user guard: using the common unscored candidate
builder after expansion, the latest user turn with any complete candidate inside
the removable old range (including qualifying straddling turns) must not be
expansion-designated and must contain no sentence from the historical 512-item
formulaic pool, even in its authored base. Its base may be necessary or incidental.
Keep bank-consumer negative tests for designated and undesignated violations.

Preserve the 600-token cap on every turn text, 12–24 turns, rendered-history
acceptance 4096–8192, expansion minimum 4608 checked after each round-robin batch,
capacity accounting (typically at least eight designated turns), U >= 2B and an
actual budget skip. Preserve all remaining endpoint/N/policy/gate and commissioning
laws. Historical candidate counts remain regression evidence, never acceptance
ranges. Keep AUTHOR-CONTRACT-v3.md as the byte-exact pre-repair contract.

The disposable smoke regression must validate matched sources in which the same
public sentence/template is necessary and incidental at the same role and eligible
position, with passing references and failing semantic negatives. Recompute
public-form/role/position contingency tables with the real tokenizer and common
candidate builder. The 318a90c bank must fail: exact-pool form 1,539 negatives and
zero positives; index 1 six positives and zero negatives; newest eligible old
user eight negatives and zero positives. Regenerated OLD smoke must include both
evidence and incidental pieces at index 1 and both necessary and incidental newest
eligible old users, without historical pool prose. These are disposable regression
examples, never production balancing quotas or policy-retention filters. Matched
fixtures do not establish production-wide semantic compliance; independent source
review remains binding before Stage 2 acceptance.

The snapshot producer includes DRAFT v2, every adopted SC1 AMENDMENT N section in
ledger order and the current author contract, using committed byte-range provenance.
It excludes proposals and unrelated editorial ledger entries. After adoption,
regenerate the snapshot, provenance and manifest and obtain independent review.

<!-- END SC1 AMENDMENT 2 -->

## SC1 STATUS (2026-09-04): SHELVED AT STAGE 2 FREEZE

STATE: Brian's ruling adopts the orchestrator's assessments and Amendment 2 above (proposal body verbatim, under Brian's requested heading) and shelves SC1 after this Stage 2 artifact freeze. No production episode authoring, setup runs or final runs are authorized. Freeze commit: `1756465b268add4a3945b75c6015554008525ae8`; manifest SHA-256: `a598392b90b871ed3558c262d3c293f905e08e16b67ae53da0d1a9c257676bb9`; registration snapshot SHA-256: `12a1eab17115032153f21f551e33501461fc2997ce1e7f75b7acf825e1063a8b`. Future resumption must begin with Stage 3 authoring under the reconciled DRAFT v2 + Amendment 1 + Amendment 2 + current data/sc1/AUTHOR-CONTRACT.md contract, use fresh isolated author sessions, and obtain independent cue review of production sources; disposable smoke fixtures do not establish production semantic compliance. The claim remains narrow: this is a frozen CPU harness and disposable regression bank; nothing about SC1 is a result. The next program is FOCUS-1, recorded above as DRAFT v1, not yet registered. Freeze checks passed: committed-source snapshot and smoke manifest regenerated and verified; smoke and bank validation passed all 8 references and rejected all 48 negatives; the exact four-file CPU test command completed with 153 passed, 1 existing xfailed and 1 warning, including all of tests/test_sealed_guard.py as the sole authorized sealed-path reader. Fit-on = none; evaluated-on = disposable SC1 CPU fixtures only, with the sealed guard performing its explicitly authorized integrity checks; no fitting, training, model/GPU process, background job, process signalling or push.

## FOCUS-1 — SET/HOLD/SWITCH/CLEAR SCREEN ON FROZEN QWEN (DRAFT v2, 2026-09-04; NOT YET REGISTERED; supersedes DRAFT v1, preserved above)
Data lineage — fit-on: only new seeded operand-balanced synthetic extraction examples, with separate synthetic setup examples for selection; evaluated-on: 64 fresh test episodes, disjoint from extraction/setup by unordered operand sets and seeds; trunk: frozen Qwen3-1.7B. These are prospective roles; no fitting/training is authorized. Exclude `data/bench`, sealed IFEval/BFCL contents, b3 data/probes/responses, SC1 setup/final episodes and existing fitted vectors/checkpoints from every stage.
STATE: consolidated draft, not registration or reviewer closure. SC1 remains shelved. Next: independent review of these dispositions and the matching CPU harness brief; no model/GPU process until actual registration and recorded terminal evidence for the existing BFCL preflight (success unnecessary). This task authorizes documentation/CPU checks only; foreground only, no process termination/signals, fitting/training or sealed-input reads.

**Question, competence and reliability.** Can an oracle A/B/OFF address control two demonstrated frozen skills with a sustained content-free signal, switch and switch back on fresh operands, and release without residual-KV harm?
A = ascending sort; B = descending sort; each input has 5–8 distinct integers in [-9,9]; output one JSON array without prose. Reject sorted/reverse-sorted inputs so copy, A and B differ. Every decision has fresh operands.
Before extraction/selection, require >=29/32 (90.625%) exact visible-cue answers for EACH skill on the same setup sort0 operands; require 32/32 complete two-query neutral-copy pairs with OFF; additionally run the cue-absent OFF prompt on sort0 separately for each task and require >=31/32 schema-valid integer arrays of query length per task (correctness ungated, reported). Any gate failure => INELIGIBLE; no replacement bank or 4B fallback.
Eligibility does not certify endpoint reliability. Under homogeneous independent per-decision success p, expected SET/SWITCH episode success is p^2/p^4: reaching 0.75 in expectation needs p>=sqrt(0.75)≈0.866025 / p>=0.75^(1/4)≈0.930605, respectively. At p=29/32, probabilities of meeting the respective >=48/64 count floors alone are 0.945636/0.122662; strata/comparisons can only reduce these. Even 32/32 has a one-sided 95% binomial lower bound 0.05^(1/32)≈0.910632. Report per-decision/per-query reliability on every verdict; a reliability FAIL concerns this actuator/dose/trunk, not impossibility of focus.

**Synthetic law and frozen inputs.** Seed Python `random.Random` (MT19937) with the big-endian integer SHA-256 of UTF-8 `focus1-v2:20260904:<split>:<episode>:<purpose>`; split=extraction/setup/test, episode=zero-based decimal, purpose=sort0..sort3/copy0/copy1/randomA/randomB/armorder (extraction uses sort0). Freeze Python version and generator/tokenizer/prompt bytes before GPU setup.
Extraction: 64 lists, 16 per length, identically paired across A/B/OFF; setup: 32 episodes, 8 per length; test: 64, 16 per length, 8 initial-A and 8 initial-B per length. Each setup/test episode has four sort and two copy lists of its assigned length; lengths ascend in equal blocks; alternate initial addresses within length, pairing opposite-address neighbors as donors.
Use RNG.sample(range(-9,10),length), then RNG.shuffle; reject sorted/reverse-sorted lists and unordered-set collisions globally across all lists/splits. Redraw only by this outcome-blind law in extraction/setup/test, episode, sort/copy order; bind draw order/rejection counts. Generate/hash all banks once in CPU generation-only; GPU setup/extract/select may read extraction/setup and test hash/count only, never test contents. No output-based redrawing, filtering, arbitrary-ID recovery or task changes.
Visible prompt: `Sort these integers in {ascending|descending} order. Output only a JSON array. Integers: {x}`; absent: `Process these integers. Output only a JSON array. Integers: {x}`; neutral: `Copy these integers in exactly the given order. Output only a JSON array. Integers: {z}`. Use existing Qwen non-thinking chat wrapper, greedy batch-1 decoding, max_new=64, EOS IDs 151645/151643; verify tokenizer facts before model loading.
Remove task cues BEFORE tokenization/prefill of measured decisions; no cue-bearing KV, task labels in prompts, exemplars, answers, text echo, retrieval or pin. Operands remain visible; the oracle sets the enum before reading operands. Freeze exact token layouts, wrapper/final-token identity across extraction triples, and delay IDs/hashes; tokenizer failures => INVALID, never silent template repair after freeze.

**One actuator, setup selection and certification.** Residual addition only: reuse the extraction/grid pattern in `scripts/function_vectors.py` and `src/stencil/function_vectors.py`'s `mean_difference`/`make_residual_hook`, with no inherited b3 data or decision rule; use Qwen layer-input hooks and pre-query `prefill_with_eviction` semantics.
At layer INPUT L in {12,16,20}, capture final prompt-token states for paired extraction triples; v_t,L=mean(h_t,L-h_OFF,L) in fp32; rho_L=(||v_A,L||2+||v_B,L||2)/2; u_t,L=rho_L*v_t,L/||v_t,L||2, hence both norms equal rho_L. Zero/nonfinite norms invalidate that layer; no gradient, optimizer or trunk update. Report norms/cosines; selected cos(u_A,u_B)>0.9 => HIGH-COLLINEARITY in manifest/verdict, descriptive only; no orthogonalization or replacement contrast.
Grid: alpha={0.5,1,2}, L={12,16,20}, lexicographic (alpha,L), at most nine cells. Inject alpha*u_t,L at the final prompt position predicting token 1 and every subsequent decoding position; OFF=no hook; never inject into earlier prompt positions or delay tokens. Directions never depend on operands.
Select FIRST eligible cell on setup: >=29/32 cue-absent exact sort0 answers per task; >=31/32 episodes per task in which CLEAR and replay BOTH copy BOTH lists exactly; residual-harm count <=1/32 per task, zero CLEAR old-task impositions and the non-vacuity checks below; <=1/32 broken episodes per task in each evaluated intervention arm (correct immediate sort, CLEAR, KEEP, replay). OFF is exercised by competence and reported; shuffled is test-only.
Evaluate sort rate, then sort breakage, then retained-KV CLEAR/replay criteria/breakage, abandoning a cell at its first failed criterion (or when unattainable). Only provisionally eligible cells run KEEP; its breakage floor still applies, but KEEP copy accuracy/impositions are descriptive and never eligibility floors. Each task uses the same sort0 operands and its actual steered reply in place of BACK for the two-query forks. Setup evidence is selection only, not a statistical result.
After selecting, certify on ALL 32 setup episodes and four phases: enum-only opposite-donor transplant must reproduce swapped token IDs bitwise; own-state sham must reproduce correct token IDs bitwise. Run correct/swapped/transplant/sham with matched canonical caches and different donor/recipient operands; capture enums before reading either list. A mismatch => INVALID, no next-cell rescue; report certification scores/breakage. Transplant/sham are absent from test and add no independent samples.
Freeze L, alpha, vector bytes, all extraction/setup outcomes, generator/bank/code/trunk/tokenizer/config hashes, prompts/layouts, decode/delay/scoring and certification in one immutable selection manifest BEFORE opening test. Bind the SHA-256 of the exact reviewed v2 section bytes (heading through final sketch line); later registration quotes that hash and explicitly lists any textual deltas, with scientific changes reviewed before execution. No eligible cell => FAIL-ACTUATOR, no expanded grid/test run.
If asc/desc ends FAIL-ACTUATOR, the designated follow-up skill-pair v2 is ascending sort versus reversing the input order, under a NEW prospective registration/bank/competence screen; this document's DRAFT v2 is a protocol revision, not authorization for that fallback. No prompt-only injection grid or larger trunk may be substituted here.

**Matched decisions and descriptive transient hold.** SET/HOLD/SWITCH/BACK use correct schedule (a,a,other(a),a) and swapped complement. At each decision run exactly four sorting arms: correct, swapped, shuffled, OFF. W measures swapped answers on recipient operands at donor targets; the swapped contrast supplies task-specific evidence.
Main-arm context is frozen: SET/SWITCH=[chat wrapper][current cue-absent prompt]; HOLD/BACK=[chat wrapper][128 neutral tokens][current cue-absent prompt]. Put the neutral tokens at the start of the current user content with a frozen separator; no earlier prompt/reply appears. D=128 tokenizer IDs of repeated `The room is quiet. The light is steady. `, truncated in token space, processed hook-free; only the enum spans decisions. Freeze this layout rather than discarding delay tokens as kimi R5 proposed.
Build canonical cue-free prefix KV, independently deep-clone across the four arms, then process identical current prompts; verify prompt IDs, absolute positions, every K/V tensor and unhooked initial logits equal before intervention. Replies may then diverge. Correct/swapped share only the scheduled address across decisions; no live steered KV is carried into the main HOLD/BACK.
Shuffled uses per-episode independent r_A/r_B from d_model successive RNG.gauss(0,1) draws on randomA/randomB streams, rescaled to rho_L, indexed by correct schedule and fixed throughout the episode; zero/nonfinite draws => INVALID. Seed arm order once; never choose it from outputs. This cheap dose-matched control is near-vacuous for complete bidirectional schedules and does not establish specificity by itself; report its individual checkpoints too.
Descriptive transient-hold arm: fork correct SET's actual steered cache including the last generated token, append the same 128 neutral tokens hook-free and the fresh HOLD cue-absent prompt, and decode with the hook OFF throughout. Report exact HOLD-sort rate by initial task, tokens and breakage; no endpoint/safety stop floor, no independent replication. It is a retained-history probe, distinct from the canonical main HOLD context; no selection/retuning from it.

**Retained-KV CLEAR and replay.** Fork correct BACK's actual steered K/V and generated history, INCLUDING its last generated token, into CLEAR (enum OFF/hook removed) and KEEP (old address/dose ON during both answers). Append the same two successive neutral queries, retaining each fork's first reply for its second. No eviction, cache reconstruction, text deletion or reset in primary CLEAR.
For EACH CLEAR query separately, clean-replay its exact prior token history with OFF from empty KV, teacher-forcing earlier actual steered/neutral answers, then answer that query. Replay is a token-history-matched baseline for residual harm, not a matched-KV intervention or a replacement CLEAR result; its own generated first reply never replaces CLEAR's history at query two.
Per query record copy success and old-task imposition (exact old-address sorted version of that query's fresh list); record all-layer K/V max-absolute deltas, first-decision logit deltas and full greedy token equality against replay. Require nonempty cache/tokens, actual nonzero-dose hook events and nonzero K/V residuals at affected layers >=L in every episode; lower layers may be zero. Missing/vacuous instrumentation => INVALID. Residuals stay reported even when outputs agree.
Never use `generate_injected(clear_after=...)`, which rebuilds KV. Hook removal alone is insufficient; CLEAR establishes behavioral release relative to clean replay on these queries, not bitwise erasure or freedom from textual-history effects.

**Episode endpoints (N=64).** Reuse only `sc1_episodes.parse_json`/`json_equal` short-output primitives; require a nonempty array of query length, finite integral values and no booleans, then compare exact expected list. No SC1 compiler/evaluator/cohort loader/runner. Incorrect order or operands in a valid array is task failure, not automatically schema breakage.
S_i=correct SET AND HOLD exact; O_i=OFF exact at those same recipient targets. SET requires sum(S)>=48, >=24/32 in each initial-task stratum, sum(S-O)>=16 and exact McNemar win over O. Report OFF success per stratum; OFF>=24/32 labels that stratum default-coincident, contributing no SET-specific evidence beyond W; the SET interpretation rests on the other stratum and W.
W_i=swapped completes all four donor-target answers on recipient operands; V_i=OFF completes those donor targets. SWITCH requires sum(W)>=48, >=24/32 per initial task, exact McNemar wins over both V and R, each with net gain >=16. Complete schedules include HOLD and BACK; individual decisions are descriptive, not extra trials.
R_i=shuffled completes EITHER whole recipient OR whole donor schedule. Require sum(R)=0 AND exact lower-tail Binomial(64,0.10) p<=alpha_f; 10% is a predeclared unacceptable rate, not a chance rate. This zero floor binds more tightly than its test; OFF's V is often near zero, so paired/count checks are not separate replications.
C_i=CLEAR copies both neutral lists; P_i=clean replay copies both; H_i=CLEAR fails at least one query whose corresponding replay succeeds; K_i=KEEP copies both. CLEAR requires sum(H)<=1 AND exact lower-tail Binomial(64,0.10) p<=alpha_f, ZERO old-task impositions after CLEAR, and the non-vacuity checks above. Shared CLEAR/replay errors do not count as residual harm; zero impositions and breakage remain hard requirements.
Report sum(C), sum(P), sum(K), all per-query CLEAR/replay pairs, KEEP impositions and paired C-vs-K table descriptively. Remove the C>=63, C-K net/McNemar and KEEP-imposition gates. KEEP imposing on <8/64 episodes labels the CLEAR family CLEAR-UNCHALLENGED (release tested against residual KV only; active interference unestablished); this label is compatible with PASS.
Three families use alpha_f=0.05/3=1/60; tests within each family are conjunctive. Everywhere, exact McNemar win means one-sided p<=alpha_f, p=sum[j=b..b+c] choose(b+c,j)/2^(b+c), with b=treatment-only, c=control-only; b+c=0 => p=1. Binomial tails include the observed count; lower-tail p(h)=sum[j=0..h] choose(64,j)*0.1^j*0.9^(64-j).
Recomputed: p(0)=0.0011790184577738583; p(1)=0.00956314971305463; p(2)=0.03890760910653732, so harm<=1 is the exact passing boundary at 1/60. McNemar(8,0)=1/256; at net gain 16, c=17 gives 0.01641956878213424 (passes), c=18 gives 0.01824170000417991 (fails), correcting fable F11's boundary wording. Floors grade magnitude; paired tests can still bind. Report all tables/denominators even on failure.
PASS needs competence, selection/certification, integrity, all three families, shuffled rejection and intervention safety. Complete valid failure => FAIL for this actuator/dose/trunk; no partial PASS. HIGH-COLLINEARITY, default-coincident and CLEAR-UNCHALLENGED remain visible alongside the verdict.
Claim ceiling: controllability of demonstrated frozen skills with a sustained content-free signal during each answer. All four main decisions are independent forward passes given the enum; HOLD/BACK test robustness to a neutral prefix and reapplication, not transient hold inside the trunk. Only the descriptive transient-hold arm can show hold without reapplication, limited to its retained SET history and fresh HOLD query; it cannot establish autonomous focus, necessary recurrence/oscillation, a learned controller, biological circuitry, long coding competence or new skill learning.

**Breakage, budget, modes and records.** I=empty/unparseable/wrong schema; T=64-token cap without EOS or cooperative deadline; R=existing function-vector repeated-4gram fraction >0.5, including truncated replies. Breakage=I OR T OR R, aggregated once per episode per arm over its replies.
Require <=1/64 broken episodes in each test intervention arm: correct, swapped, CLEAR, KEEP, replay. Stop scheduling on its second broken episode. OFF/shuffled and descriptive transient-hold breakage are reported without this stop/floor; a broken control reply makes its applicable O/V/R episode indicator zero. Valid old-task impositions and failed schedule gates remain failures independently of breakage. No dropping/replacing outputs.
One cumulative cap: 6 GPU-hours=21,600 allocated seconds, including initialization, timing, competence, extraction, selection/certification, test, transient hold, replay/audits, persistence and interruptions. No assumed headroom: timing smoke is the sole cost authority. Foreground only; no GPU launch before registration/BFCL terminal evidence, no fitting/training, signals, external timeouts or background chains.
Timing smoke FIRST within setup, using setup examples, covers extraction prefill, longest canonical and retained-history delayed decode, CLEAR/KEEP/replay, certification, load/check/persistence and peak memory; no competence selection from smoke output. Freeze cooperative attempt deadline=min(300s,4*measured worst-case attempt estimate); return normally at checkpoints.
Before each mode/attempt project spent+remaining reload costs+1.25*remaining work at retained maximum measured rates, including all nine cells until short-circuit/selection, setup certification, both replay queries and transient hold. Launch only if projection<=21,600 AND a full next-attempt deadline/load reservation fits; never decrease maxima, reset budget or use a 2x allowance. Test decode count is 64*(4*4+2+2+2+1)=1472; this is not a runtime estimate.
Competence failure=>INELIGIBLE; no eligible cell=>FAIL-ACTUATOR; integrity/certification defect=>INVALID. An already impossible endpoint/safety floor=>partial FAIL with observed/missing denominators and no fabricated final-N p-values; other budget/infrastructure/incomplete runs=>INCOMPLETE. Any actual cap overrun forbids PASS. No optional success stopping, retries, resumption/replacement or test-outcome fallback in this version.
CLI: `setup --generate-only` creates CPU banks/manifests; future `setup --timing-smoke`, `setup` competence, `extract`, `select` including certification, then `run`; `analyze` consumes persisted records on CPU only. GPU modes reject missing registration/BFCL/timing/prior-stage evidence before model import/loading; generation-only/analyze/help never initialize a model. One small driver `scripts/focus1.py`, helpers `src/stencil/focus1.py`, fake-trunk tests; no new framework.
Write raw per-decision JSONL DURING each run before aggregates: episode/split/phase/arm, source/recipient/donor IDs and enums, inputs/expected answers, vector/hash/norm/dose, prompt/layout/KV/position hashes, raw tokens/text/EOS, hook events/non-vacuity, exact scores/impositions, I/T/R, paired CLEAR/replay deltas, timings/charged intervals and exceptions. Bind protocol/data/code/trunk/selection manifests; preserve every attempt, refuse duplicate IDs/overwrite and analyze only these records.
Store in `results/qwen/focus1-v2/`; fake-trunk smoke must dry-assert every required field and full satisfying/failing verdict paths before any real run. Later authorized registered artifacts require force-add and `git ls-files` verification. CPU checks establish harness behavior only; tokenizer facts, real determinism, competence, residual behavior and measured costs remain unverified here.

**Review disposition** ([fable](results/focus1-review-fable.md), [kimi](results/focus1-review-kimi.md)); accepted means incorporated for re-review, not reviewer closure. Fable F1 accepted (explicit sustained-signal ceiling); F2 accepted (descriptive retained-SET HOLD); F3 accepted (paired content-free lineage retained); F4 accepted (exact neutral-prefix layout); F5 accepted (cheap shuffled retained with narrow interpretation); F6 accepted (KEEP floors removed, CLEAR-UNCHALLENGED); F7 accepted (separate C/P and replay-matched H); F8 accepted (harm lower tail and zero impositions); F9 accepted-with-change (OFF schema gate, intervention-only stop after removing test transplant); F10 accepted (per-stratum default label); F11 accepted-with-change (redundancy disclosed, McNemar boundary corrected, obsolete CLEAR floor removed); F12 accepted-with-change (conjunctive episode power replaces single-decision extrapolation); F13 accepted (asc/desc first, asc/reverse only newly registered follow-up after FAIL-ACTUATOR); F14 accepted (setup-only certification and cell short-circuit; full shuffled retained).
Kimi F1 accepted (ceiling); F2 accepted-with-change (residual harm replaces absolute copy/active-interference gates per fable F6–F8); F3 accepted (setup determinism witness); F4 accepted (checkpoint reporting); H1 accepted-with-change (29/32 selection, 32/32 copy gate and power caveat retained; harm replaces absolute CLEAR success); M1 accepted-with-change (fable's retained neutral prefix is frozen, no prior main-arm history); M2 accepted-with-change (replay is separate from C but necessarily defines H, not audit-only); M3 accepted (reviewed-text hash/delta binding; section under 130 lines); L1 accepted (explicit p threshold); L2 accepted-with-change (setup arms enumerated, certification moved into setup); L3 accepted-with-change (obsolete C-K/KEEP boundary removed); L4 accepted (narrow verdict retained); S1 accepted (asc/desc initial pair); A1 accepted (single fixed actuator/grid); A2 accepted (HIGH-COLLINEARITY marker); A3 accepted (lineage and layer-hook fixtures); C1 accepted-with-change (headroom assertion not adopted without measured timing); C2 accepted-with-change (transplant/short-circuit cuts adopted, 64 extraction lists and delay prefixes retained); C3 accepted (small driver and import guards); C4 accepted-with-change (current formulas recomputed; obsolete CLEAR arithmetic superseded). These choices are flagged for the next independent review; zero open high/critical required before registration, with prior findings preserved and closed/refuted only by reviewers.

**FOCUS-2 sketch — only after FOCUS-1 PASS; ten lines, NOT REGISTERED:**

1. Adapt `src/stencil/wave.py`'s WaveController/WaveRNN; its positional checkpoint is not a skill selector.
2. Emit A/B/OFF through fixed FOCUS-1 directions; freeze trunk and direction pair.
3. Use new separate synthetic training/validation/test examples; exclude all FOCUS-1 evaluation and benchmark responses.
4. Read `INTERNAL-WAVE-PLAN.md` and `scripts/w0_train.py`/`w1_train.py` for the gradient recipe only; never import those top-level training scripts.
5. Train only under a new registration on short continuations, trunk requires_grad=False with actuator-to-loss gradients intact.
6. Prove finite nonzero controller gradients and detached-actuator failure.
7. Normalize hidden-state inputs and recurrent state separately.
8. Compare recurrence with an equally tuned nonrecurrent latch and stateless controller; use transient-hold observations to frame, not prove, signal requirements.
9. Require matched reset/donor-state dependence for a memory claim; remeasure hold, switch-back, CLEAR and breakage.
10. Claim oscillation only after a measured win over nonoscillatory controls; obtain a separate registration/budget before any training.

## FOCUS-1 CPU handoff — 2026-09-04 (completed 2026-09-05 02:28 UTC)

STATE: CPU implementation and fake-trunk checks complete; FOCUS-1 v2 remains DRAFT, UNREGISTERED and scientifically unmeasured. This handoff is outside the reviewed section. Independent review with zero open high/critical findings and actual registration remain prerequisites; the v2 dispositions are not reviewer closure.

- Implementation commit: `d723365cdf857a39dd313338179de71ea5a3feaa`; files: `scripts/focus1.py`, `src/stencil/focus1.py`, `tests/test_focus1.py`. This append-only handoff is committed separately in `LEDGER-PLAN.md`; no push.
- Actual provenance: model `gpt-6-astra`, effort `xhigh`, session `01a06f25-6b08-7d90-9673-c2d9b6e10de3` (environment and wrapper's `thread.started` event agree); log `/home/bmarti44/stencil-llm/results/logs/codex-agent-focus1-harness.log`. Recorded launcher override reason: “Brian 2026-09-04: astra replaces sol for all coder/reviewer roles”.
- Launch-contract conflict: process ancestry proved this session WAS wrapper-launched by `bash tools/run_codex_agent.sh focus1-harness 14400`, through its existing `timeout 14400`, despite the brief requiring a direct session. Neither was launched or signalled by this coder. Its own lock was not waited on or polled. The coder did not edit `WORKLOG.md`; the parent wrapper's unconditional exit-time provenance write remains outside the permitted direct-session contract. Do not represent this as `not wrapper-launched`.
- Data lineage in this session: no fitting/training; CPU arithmetic and fake-trunk evaluation on inline/temporary synthetic fixtures only. Future extraction is restricted to the new paired synthetic bank, selection to setup, and evaluation to the disjoint test bank. No model/GPU process was launched by this coder; no real extraction, timing smoke, competence, calibration, selection or test evaluation ran. No sealed IFEval/BFCL input, b3 data/probe/response, SC1 episodes or existing fitted vector was read; no controller, alternate skill pair or trunk fallback was implemented.
- RED: the targeted file initially failed collection because `stencil.focus1` did not exist. Subsequent behavioral RED regressions exposed duplicate timing/certification attempt IDs, fp32 cancellation when subtracting separate means, missing extraction-exception records, and scoring that hid a non-EOS special token. GREEN: the final exact targeted pytest command passed **66 tests in 113.44 seconds**; the exact Ruff check, CPU CLI `--help`, and scoped `git diff --check` passed. Only `tests/test_focus1.py` was run, never the full suite. The real CLI was exercised with injected fake backends, including all five modes, 1,472 test decodes and 128 per-query CLEAR/replay audits; these are fixture observations, not model results.
- SHA-256, driver `scripts/focus1.py`: `7cbdf50f780ceec2c24c085d9b562a33783b9669e525aff876c177e8df70eb7f`.
- SHA-256, helpers/consumer `src/stencil/focus1.py`: `5151916bafacc9ab0b10045f9916e153cdba9b79cfb3037b19d96d2e3e788647`.
- SHA-256, inline CPU fixtures/tests `tests/test_focus1.py`: `e68470d8e40daad5d3d0d3647851daca9e38168b5f7dceb278d1a5ac1381d591`.
- Reviewed v2 section: 23,197 bytes, 71 lines, SHA-256 `746b354436a2007984f394fa995c68c6a455312c80bc4493dca9f9bc5f0e67fb`, heading through final sketch newline. Its constants and all prior ledger bytes are unchanged; original 199,362-byte ledger SHA-256 was `32d9c3790adde7a63c837188991e80da415b2eb6773bdbf3095bc3f7f2945c7a`.

Implemented CLI: `setup --generate-only` creates banks/layouts/manifests on CPU; `setup --timing-smoke`, `setup`, `extract`, `select` and `run` implement future guarded stages; `analyze` consumes persisted records on CPU. Results use exclusive-write manifests, fsynced hash-chain decision/attempt/allocation logs, immutable terminal manifest hashes, retained maximum costs, cumulative interruption charges and no retries/resumption/overwrite. Model import/loading follows registration, BFCL, prior-stage and frozen-input checks. Extraction computes each fp32 paired difference before averaging through `mean_difference`; the existing shared hook is unchanged.

Deferred operator sequence, NOT EXECUTED: use root `/home/bmarti44/stencil-llm/results/qwen/focus1-v2`. First CPU command is `.venv/bin/python scripts/focus1.py setup --generate-only --out <root>`. Then, only after actual registration and recorded BFCL terminal evidence, run `.venv/bin/python scripts/focus1.py` with modes **`setup --timing-smoke` → `setup` → `extract` → `select` → `run`**, each with `--out <root> --registered-manifest <root>/registration.json --bfcl-completion <root>/bfcl-completion.json`. Finally `.venv/bin/python scripts/focus1.py analyze --out <root>` is CPU-only. These are deferred interfaces, not readiness certification or authorization to run them now.

Registration/evidence interface: `registration.json` binds the reviewed hash above, an actually REGISTERED section's half-open ledger byte interval/hash, exact `difflib.unified_diff` lines (`reviewed-v2` → `registered-v2`), reviewed science-change disposition/evidence hash, bank hash and existing BFCL preflight ID. The current implementation accepts heading/STATE registration edits only; science deltas require matching reviewed code before execution. `bfcl-completion.json` must name the same existing `results/qwen/bfcl…preflight…` job and contain a recorded terminal status, integer exit code, recording time and terminal record. Scientific success is unnecessary. No real evidence was created, no terminal status inferred, and no cohort contents inspected.

Choices and unresolved points for review, with draft thresholds preserved:

- Layout uses separately encoded user-wrapper IDs, exactly 128 neutral IDs where applicable, and a body with frozen `\n\n` separator plus the existing non-thinking assistant suffix. Extraction triples must end in the same wrapper token before loading. Every generated token, including terminal EOS, is fed into the retained cache; non-EOS special tokens remain visible to strict JSON scoring. Review these exact token-boundary and final-token hook conventions before freezing real tokenizer facts.
- Non-vacuity takes the conservative reading: BOTH K and V must differ at EVERY affected layer at/above L for BOTH neutral queries, with deltas recorded before each query and at its first decision. Missing evidence is INVALID, never a clearance pass. Main sort success excludes broken replies, while C/P/K and query-paired harm use exact copies with independent intervention breakage gates. Integral JSON decimals are permitted; booleans, prose and wrong shape are not. These choices are explicit for review, not post-outcome adjustments.
- The first timing smoke necessarily has no prior measured rates: its bootstrap uses the cumulative cap and 300-second cooperative checks, then forecasts all remaining work/reloads from measured retained maxima. Reload cost includes model-file verification; per-attempt check/persistence rates are measured separately, with an additional closing-persistence reserve and permanent overrun marker. CPU fixtures cannot certify real blocking model-load/kernel return, deadline behavior, rates or memory use. Review this bootstrap interpretation before any real GPU invocation.
- Arithmetic wording for review: with N=64, treatment success >=48 and net gain >=16, exhaustive feasible paired tables have maximum McNemar p=`0.01465247336026465` at `(b,c)=(32,16)`, already below 1/60. Thus the draft's “paired tests can still bind” sentence does not hold once these particular count/net floors are enforced. The requested `(33,17)`/`(34,18)` standalone boundaries are correct but cannot also satisfy the >=48/64 treatment floor. All registered tests and thresholds remain implemented unchanged; no science correction was silently applied.

No shared-hook defect or unimplemented actuator/controller dependency was found or substituted. This is a CPU harness handoff, not acceptance of scientific claims: **1.7B skill competence, real determinism, transient hold, CLEAR residual behavior, measured costs and every scientific endpoint remain unmeasured.** Actual registration and BFCL terminal evidence remain prerequisites. No fitting/training, additional coder/reviewer/model, GPU job, watcher, background chain, process signal, external timeout or push was launched by this coder.

## LEG A PREFLIGHT OUTCOME (2026-09-05; registered 1.7B dev preflight, results/qwen/bfcl-v10-preflight, harness v12 = 919ab8a)
Run terminated by infrastructure at case 28/32 (a long-context case): fp32 attention matrix allocation of 71.4 GiB
exceeded the free device memory; the remaining five cases are all long-context and would meet the same limit. 27
cases recorded; every arm (base, clf_pinned, clf_pinned_echo, clf_control, recency_pinned, tool_swap_echo,
role_pinned, full) scored 0 on all 27, including the full-context reference. The registered competence floors (full
case pass >= 5/32 and >= 2/8 long-context; base >= 5/32) are unreachable on this evidence: the 1.7B trunk is not
competent on this task family. DISPOSITION (orchestrator, under Brian's 2026-09-04 ruling adopting the astra
assessments — BFCL secondary): (a) the 1.7B preflight is closed FAILED-COMPETENCE / TERMINATED-INFRASTRUCTURE; no
sealed read occurred; no contrast evaluated. (b) The registered one-shot 4B fallback remains authorized but is DEFERRED
behind FOCUS-1; before any 4B attempt an infrastructure-only amendment (memory-bounded attention for long-context
cases; no scientific clause changed) must be registered and reviewed, because the limit scales with context length,
not trunk size. (c) The preflight records (27 cases) are retained, never re-scored. No GPU-h is spent on BFCL until
FOCUS-1 has run.

## FOCUS-1 STATUS (2026-09-05): ON HOLD, NOT REGISTERED — actuator family infeasible on quick check 31
Quick check 31 (unregistered, disclosed; results/quick-checks/focus1-probe/): oracle A/B/OFF steering with extracted
mean-difference residual vectors induced neither skill in any of 18 cells on either trunk (1.7B or 4B); asc/desc
vectors are near-collinear (cosine 0.89-0.98); 4B is competent with the cue visible (27/32, 30/32), 1.7B is not on
descending (10/32 lenient). The FOCUS-1 DRAFT v2 actuator (same extraction) is therefore not worth registering; the
harness reviews (results/focus1-harness-review-{astra,fable}.md) stand as recorded and their fixes are NOT applied
unless a later quick test revives this actuator. Under Brian's quick-test-first ruling the program proceeds down the
QUEUE in results/quick-checks/README.md (Q2 = content-free slot address over a fixed skill menu, check 32).


## FOCUS-2 — PLACEMENT + EVICTION AT INSTRUCTION CHANGE (DRAFT v1, 2026-09-05; NOT YET REGISTERED)
Data lineage FIRST — fit-on: none; development: checks 31–37 + repair fixtures; evaluated-on: fresh seeded synthetic override episodes in four task families, disjoint from development/competence/pilot inputs. NO benchmark contact in this leg. Multi-IF is CUT per fable F7 (no same-family turn-3 override events); a possible later placement-only do-no-harm check requires its own registration. Never open sealed IFEval inputs or sealed BFCL cohort contents; no fitting/training or benchmark-derived prompts, answers, scores, or tuning.
STATE: drafting only, CPU only; no experiment authorized by this section. Check 36's independent accuracy review is pending; check 37 is external work and its results/files are not read/edited here. This replaces the earlier unregistered learned-controller FOCUS-2 sketches; FOCUS-1's failed actuator is not revived. Conservative choices below go to registration review, not automatic reviewer closure.

Mechanism under test: with an oracle change/scope map derived solely from public instruction events and turn ownership, move the live task instruction to the current user position and remove assistant answers produced under the superseded rule, on frozen Qwen3-4B (bf16, hf_compatible, greedy, thinking disabled, <=64 generated tokens/request). This tests whether stale own demonstrations obstruct new instructions, and whether their removal adds safe control beyond a strong current text reminder. Placement includes role/wording as well as position; attention weights and weight circuits are not measured. Prior ordering evidence is check 34 current cue vs own answers, check 35 current cue vs old cue AND answers together, and check 36 rewritten old cue vs contradictory own answers; it did not isolate current cue vs old cue alone. An ascending default prior may contribute, so directions cannot be pooled away.
Evidence ceiling carried forward: checks 31–33 closed tested induction recipes, not every representation; check 32 encoded instruction presence rather than task identity, whereas check 33 had readability without induction. Check 34 retained HOLD was 32/32 ascending, 23/32 descending, with joint control 3/32 and 5/32. Matched K+V is expected attention arithmetic, not a new hypothesis. Eviction beat only the tested neutral CLEAR reminder, not explicit cancellation/default or text-history editing/re-prefill; check 36's decisive numbers require its own accuracy review before CPU freeze.

Five paired arms (same episode inputs, shared unscreened SET/HOLD answers, exogenous delays, renderer and decoding; later scored answers evolve within each arm):
1. neither: replace the live rule in the original old instruction slot; retain assistant bodies.
2. placement-only: remove that old-slot rule and place the identical new live rule in the current user turn; retain bodies; no refresh at HOLD or neutral request two.
3. eviction-only: old-slot rule update plus check-37-selected repaired removal of all assistant task-response bodies attributed to the superseded event, independent of correctness.
4. both: current-user placement plus the identical repaired removal/scope mask; intervene only at SWITCH, BACK and CLEAR.
5. text-restate: retain bodies; append the following exact template in the current user turn at EVERY scored request, explicitly canceling the superseded rule and restating every live rule/default, including unchanged constraints. Its generosity is deliberate; both-vs-text-restate carries the claim, the other two contrasts test each component's added value.
All arms retire superseded cue/recap text using the same event map; never leave conflicting old cue text selectively in one arm. At CLEAR remove the task cue, leaving the explicit baseline/default rules. Keep user/tool turns, event provenance and assistant closures; no whole-pair deletion in this leg unless that exact policy was check 37's preselection. Do not restore previously evicted answers at BACK. Re-prefill every edited text history from empty KV through one valid chat renderer with contiguous positions; save original-to-edited token maps. This estimates the text-context intervention and makes no recompute-free cache-speed claim.
Text-restate template, verbatim (UTF-8, LF between the four lines, NO trailing LF; braces are literal template slots):
```text
Cancel the superseded task rule: {superseded_rule}.
Your earlier answers under that rule followed a rule that no longer applies; do not imitate your earlier answers; the rules that apply now are:
{live_rules_or_default}
Use earlier facts when requested, while following the current rules for this answer.
```
Template SHA-256: `2658b026d6bd22d4ed460b34c543abc159e4e80ff56f367be4eaf5c035f8e8d7`. Render superseded_rule from the last retired rule (or the fixed string "none" before any change); render live_rules_or_default in fixed order: current task/default, output schema, unchanged tag, then current request obligations. Never insert target answers or collateral fact values into a recap. At CLEAR and neutral request two explicitly say to copy the current payload without the canceled transformation. Commit these bytes and the readings below BEFORE any check 37 result is read; no wording/repair-choice rescue afterward.

Episode generator law (freeze the complete strings, token layouts, checker mutations and generator source before competence/pilot outcomes):
- Final N=256: 64 each for sort direction (ascending/descending), letter case (lower/upper), field selection (left/right), output representation (JSON array/comma-separated string). Each family has 32 episodes per initial direction; cross each direction with zero/512 delay for 16/cell. SWITCH reverses A->B; BACK reverses B->A; publish BOTH actual change directions at each checkpoint.
- Independent SHA-256-derived RNG streams from `focus2-v1:{seed}:{bank}:{family}:{direction}:{delay}:{episode}:{request}:{purpose}`, big-endian digest to Random(MT19937); seed 9053702 for competence and a purpose-disjoint timing pilot, 9053703 for final. No favorable seed searches. Generate deterministically and hash before model loading.
- Sort operands: uniformly sample 4–6 distinct integers from -99..99, random order, reject already ascending/descending. Case: three distinct mixed-case ASCII nonce words, lengths 3–6, ensuring lower/upper/copy differ. Fields: three ordered {left,right} records with distinct integer values, select one column in record order. Representation: 4–6 distinct integers, array vs comma-separated decimal string with no spaces. Default at CLEAR copies the presented payload exactly as a JSON value, without the canceled transform; representation uses an explicit {"items": [...]} input so default differs from either skill.
- Every scored answer uses compact JSON {"answer": <task value>, "tag": <integer episode tag>} without prose or unrequested keys; user/tool facts are distinct two-digit integers; the frozen request may additionally request memo/user_fact/tool_fact/assistant_fact. The unchanged tag and envelope apply throughout, including CLEAR. Fixed-schema task errors are task failures, not automatically structural breakage. Bound all gold replies below 64 tokenizer tokens before freeze.
- Two actual prior answers, SET and HOLD under A, are generated once and shared across all five arms, never screened/replaced. Record each answer's live-task/schema correctness and the both-correct flag before intervention; source failures never remove an episode. Then score SWITCH(B), unrefreshed HOLD(B), BACK(A), CLEAR(default), and neutral request two(default) on fresh payloads. No later success repairs an earlier failed endpoint.
- A delay occurs before each initial HOLD, post-SWITCH HOLD and second neutral request: zero means no pair; 512 means one complete neutral user+actual-assistant pair with exactly 512 tokenizer tokens of user content. Replies are generated once in an isolated neutral context, retained unscreened and replayed identically across arms; report full rendered delay length including assistant and wrapper tokens. No unanswered user turns, empty assistant bodies or cropped replies; neutral pairs are outside the transformed-task scope. This is a controlled replay delay, not a natural-conversation claim.
- All episodes contain later-needed user and tool facts with valid tool-call/return closure; neutral request two asks for both, with no value restated at query time. In exactly 16/64 episodes per family (4 per direction/delay cell), SET also asks the assistant to invent a six-letter ASCII memo; only that actual assistant body contains it, and neutral request two asks for it. No external copy is returned to the model after eviction. Score source-missing/invalid memos as collateral failures on the fixed 64 denominator, never drop them. This deliberately measures eviction's assistant-authored-fact cost.
- Dedup all payload identities within/across competence, pilot, final and development/repair banks using semantic fingerprints (unordered sets for sorting, casefolded words, ordered record pairs, unordered representation values), not seed or episode ID alone; ignore episode IDs/tags and reject permutations preserving the task instance. Before freeze an outcome-free development fingerprint manifest must establish disjointness without reading check 37 outcomes; if unavailable, do not freeze. Do not open benchmark banks or revive SC1 authoring/cohorts.
Competence gate: 64 independent immediate visible-cue fixtures for EACH of the two directions in EACH family (512 total); require >=56/64 exact live-task/schema successes in every cell, reporting directions separately. Also require >=56/64 on each family's 64 fresh default-copy fixtures (256). No family dropping/substitution, prompt edits or retesting after outcomes: any miss is INELIGIBLE and stops this four-family leg.

Primary endpoint Y: episode succeeds iff ALL five post-change answers satisfy the task/default checker and every unchanged constraint, with no structural breakage. Fact-recall subchecks are separate collateral endpoints, excluded from Y (including assistant facts); a missing/wrong fact field alone is not structural breakage, while malformed overall JSON still is. Publish checkpoint/family/direction/delay counts and all fixed denominators.
Decision rule: for both vs EACH of placement-only, eviction-only and text-restate, let b=both succeeds/comparator fails and c=converse. Require b>c and exact one-sided McNemar p=P[Binomial(b+c,0.5)>=b], with p=1 if no discordances; Holm step-down across these three at familywise .05. Also require >=5 percentage points over text-restate (>=13 net episodes/256). Report raw/adjusted p, 2x2 tables, nominal paired 95% difference intervals from inverted paired-score bounds (asymptotic, not exact finite-sample), and all margins. A <5-point component contrast is labeled MARGINAL ADDED CONTROL even if significant; it cannot carry the headline joint-control claim (kimi K3 accepted-with-change; the requested primary gate is retained).
F11 stratification: repeat every primary contrast separately for both-correct versus at-least-one-wrong prior answers, with n, differences, paired intervals and descriptive p-values (no replacement primary test or selective pooling). The both-correct stratum is the stale-demonstration mechanism estimate; a benefit confined to prior-error episodes supports bad-demonstration removal, not stale-correct-demonstration release. Empty strata are uninformative, never a pass. Report ascending/default impositions at CLEAR and neutral request two per initial direction, alongside correct copies and placeholder imitation.

Safety gate vs text-restate: define episode breakage B=any scored output empty, placeholder-only after whitespace stripping, truncated without valid EOS by the 64-token cap, repetitive (an exact token block of period 1–4 repeated >=8 consecutive times), or schema-invalid. Save separate flags; placeholder imitation is breakage, never neutral success. Wrong task values with valid structure remain task failures. EOS on the cap is not truncation.
F6: let h=both broken/text-restate valid and r=converse. Require one-sided paired exact McNemar harm p=P[Binomial(h+r,0.5)>=h]>.05 AND h<=2/256, with all 256 episodes complete. Report paired counts and the one-sided exact 95% upper bound for h/256: 0/256 ->1.1634%, 2/256 ->2.4387%. This operational "not-worse" screen is absence of detected harm plus a count cap, NOT proof of noninferiority/harmlessness.
Collateral/unchanged constraints: separately report paired episode failures for user facts (n=256), tool facts (n=256), assistant-authored facts (n=64, also by source validity), and any unchanged constraint (n=256). Each category must have no greater observed failure count under both than text-restate; publish discordances, exact harm tests and intervals. A cost in any category fails safety even if primary control improves. No exemption for expected assistant-fact loss; print that cost next to the benefit.

Repair dependency: use exactly whatever check 37 preselected, placeholder replacement expected, never the best observed variant. Consume a provenance receipt binding its prewritten selection, reading, code hashes, commit/launch chronology and final decision; do not infer PASS or inspect/select variants here. If check 37 STOPs, this leg DOES NOT RUN. Missing pre-outcome provenance is INVALID, not repaired by a retrospective commit. Its n=32 gate is coarse and can conservatively false-stop; certify structural behavior under an active cue only, not success at instruction changes. The synthetic test measures change behavior.
Cost: HARD cap 6 GPU-h for this leg, including loads, competence, timing pilot, all final generations, delays and retries/diagnostics; check 37 is separately accounted development, never rerun here. Future foreground pilot uses 16 disjoint episodes (one/family/direction/delay), all five arms, recording prefill/decode timing and peak memory. Timing only; no outcome-based changes. Project ALL remaining work by worst measured cell cost with 25% reserve; refuse work if spent+projection exceeds 6 GPU-h. Check budgets cooperatively before loads/prefills and each decode step; no background jobs, external timeouts or process signals.
Stop rules: no run while DRAFT, unresolved check-36 accuracy prerequisite, missing committed readings/hashes/repair receipt, competence miss, check-37 STOP, duplicate/invalid banks, or failed CPU checker/renderer tests. No rescue variants, extra families, controller grids or benchmark stages. On the third irreversible newly-broken both-only episode, stop scheduling (safety cannot pass); preserve records, report FAIL-SAFETY with incomplete denominators, not a complete effect estimate. Resource/cap/interruption -> INCOMPLETE; hash/protocol drift -> INVALID. No signal/termination of any process, including ones launched by this work; no adaptive early efficacy stop or extra sampling.
Prewritten readings (committed before any outcome is accessed): PASS requires competence, all primary comparisons/magnitude and safety, within scope below; significant but <5-point component gains -> PASS with MARGINAL ADDED CONTROL, no headline joint-control claim. Failure to beat placement/text -> no demonstrated extra mechanism (compatible with prompting), not equivalence. Repair STOP/loss of CLEAR gains -> release fragile, do not proceed/promote. Primary benefit plus collateral/breakage failure -> unsafe context management, do not promote. Benefit confined to wrong prior answers -> error-demonstration cleanup; no stale-correct mechanism claim. Other failed contrasts -> FAIL, not a compact-state conclusion; INELIGIBLE/INCOMPLETE/INVALID earn no efficacy claim. A null on the stringent all-five endpoint is not evidence of absence or established power.
Claim ceiling: "context-management mechanism on a frozen trunk; not compact state, not waves"; oracle-managed synthetic episodes only, no autonomous change detection, benchmark transfer, literature priority, Miller weight-circuit selection, or general safety claim. Retained HOLD asymmetry and default priors stay visible. Neither/eviction-only alone cannot carry a headline.

Freeze sequence: (0) commit this draft's exact text-restate bytes/hash and prewritten readings before reading ANY check 37 outcome; record that commit as the earliest immutable anchor, without claiming check 37 itself had prelaunch provenance. (1) After check 36's accuracy review completes, bind its reviewed source hashes; separately validate check 37's committed prewritten choice/reading against launch chronology, then receive its decision, STOP if required, without changing these templates/readings. (2) CPU build/test; freeze generator, ALL cue/default/delay/fact/placement templates and rendered token maps, event masks, checkers/mutations, banks/fingerprints, arm order, model/tokenizer/config hashes, repair receipt and this section snapshot. Registration review must clear the draft before model execution.
(3) Commit the immutable registration snapshot/readings/templates/manifest with SHA-256 of each dependency (exclude the manifest's own hash to avoid self-reference); verify ignored artifacts with git ls-files and content in the named freeze commit. Record freeze commit + manifest hash in an append-only launch receipt before ANY competence/pilot outcome. (4) Run only the frozen competence/pilot gates, then one final run; analyze the same immutable rows. run must refuse DRAFT, uncommitted/dirty/missing/mismatched dependencies or readings, STOP/absent repair or failed/absent competence/pilot gates BEFORE model loading. Bind the section snapshot, not later unrelated LEDGER appends; no --force bypass. Earlier development results are disclosed, never misrepresented as fresh evidence.
Artifacts per generated request in the same run: episode/arm/checkpoint, family/direction/delay, input and emitted token IDs/text/EOS, shared-prior correctness and hash, actual fact source, live-rule/scope/turn/token-position maps, removed body IDs/hashes and replacement tokens, task/constraint/fact/imposition/placeholder/breakage flags, cost/peak-memory and all freeze hashes. Persist raw records before aggregation; analyze verifies completeness, pairing, integrity and recomputes decisions. Partial runs retain original denominators and status; no overwritten/reselected outputs or hidden imputation.

Review disposition (design decisions, not reviewer closure): fable F1 accepted—specific supporting contrasts and role/position limits; F2 accepted—ascending default prior and directional reports; F3 accepted—K+V arithmetic scoped; F4 accepted-with-change—verbatim anti-imitation template hashed/committed before check-37 results are read (its launch already occurred; no false prelaunch claim); F5 accepted—56/64 per skill/direction, conservative all-four-family stop; F6 accepted—paired harm test plus <=2 discordant breakages, recomputed bound; F7 accepted—Multi-IF cut, later placement-only registration separate; F8 accepted-with-change—FOCUS-2 readings committed now, check-37 provenance validated later without editing its files or claiming retroactive preregistration; F9 accepted—placeholder/empty imitation breaks; F10 accepted—repair certifies active-cue structure only; F11 accepted—unscreened prior correctness strata/mechanism estimate; F12 accepted—25% assistant-only facts, separate endpoint and binding cost gate; F13 accepted-with-change—complete replayed neutral pairs, 512 counts user content and actual total is disclosed. Kimi assigns no finding IDs: local K1–K5 map its Exact replacement Fixes 1–5; K6 identifies its unnumbered coarse-repair-gate note. K1 accepted—presence vs identity; K2 accepted—directional retained HOLD/joint rates; K3 accepted-with-change—retain requested >=5-point text gate, label smaller component effects marginal and withhold headline joint-control claim; K4 accepted—check 36 accuracy review prerequisite (also its conditional process finding; check 33 review not asserted); K5 accepted—no later recovery of failed endpoint; K6 accepted—coarse n=32 conservative false-stop acknowledged. No finding refuted.

## FOCUS-2 — PLACEMENT + EVICTION AT INSTRUCTION CHANGE (DRAFT v2, 2026-09-05; NOT YET REGISTERED; supersedes DRAFT v1, preserved above)
Data lineage FIRST — fit-on: none; development: checks 31–39 + repair fixtures; evaluated-on: fresh seeded synthetic override episodes in four task families, disjoint from development/competence/pilot inputs. NO benchmark contact in this leg. Multi-IF is CUT per fable F7 (no same-family turn-3 override events); a possible later placement-only do-no-harm check requires its own registration. Never open sealed IFEval inputs or sealed BFCL cohort contents; no fitting/training or benchmark-derived prompts, answers, scores, or tuning.
STATE: drafting only, CPU only; no experiment authorized by this section. Check 36's independent accuracy prerequisite is satisfied by results/check36-review-fable.md (ACCURATE-WITH-CORRECTIONS); its ordering correction is incorporated through results/check38-review-fable.md. Repair prerequisite is satisfied by check 39's PROCEED_PLACEHOLDER receipt at e30343d, preregistered at e24afd4; check 37 remains STOP under its own rule and is not pooled. This supersedes DRAFT v1 and the earlier unregistered learned-controller FOCUS-2 sketches; FOCUS-1's failed actuator is not revived. Registration review, CPU implementation/checks and the committed freeze remain outstanding; dispositions are not automatic reviewer closure.

Mechanism under test: with an oracle change/scope map derived solely from public instruction events and turn ownership, render the live task rules INSIDE the current request user message (same turn as the task input) and remove assistant answers produced under the superseded rule, on frozen Qwen3-4B (bf16, hf_compatible, greedy, thinking disabled, <=64 generated tokens/request). This tests whether stale own demonstrations obstruct new instructions, and whether their removal adds safe control beyond a strong current text reminder. Placement includes role/wording as well as position; attention weights and weight circuits are not measured. Prior ordering (results/check36-review-fable.md; results/check38-review-fable.md, plain answers (a)(b)(c)): check 36 alone confounded role, recency and demonstrations; check 38 separates the tested contrasts. Before two contrary answers, system/user cues give 2/32 and 1/32 B (no observed role benefit, not proof of no role effect); moving the user cue after the demonstrations gives 11/32 (paired +10/0), below its fixed threshold but evidence of a before/after effect. Inside-request placement gives 27/32 (check 35 TEXT) versus adjacent-turn placement 11/32 (check 38 T4; matched lists, 16/0); this cross-check comparison is not a randomized within-run contrast, has different demo answers/cache construction, and T4 has an unanswered cue turn. Age after demonstrations is untested. Old-system B without demonstrations decays 31->12/32 after one neutral turn (check 34 all_B SET vs check 38 T2, cross-check/different lists/unanswered filler); contrary answers then reduce 12->2/32 (T2 vs R3, paired 10/0). Thus 31->12->2 attributes roughly 19/32 to pre-demo decay and 10/32 to demonstrations, not the whole deficit to own answers. Check 38 T2 gives a sort-present ascending default of 12/32 despite B and no A information; cue-free/demo-free default is copy 64/64 (check 34 off), so T3's 31/32 A is demonstration-driven but does not separate imitation from inferring the old rule. Directions cannot be pooled away.
Evidence ceiling carried forward: checks 31–33 closed tested induction recipes, not every representation; check 32 encoded instruction presence rather than task identity, whereas check 33 had readability without induction. Check 34 retained HOLD was 32/32 ascending, 23/32 descending, with joint control 3/32 and 5/32. Matched K+V is expected attention arithmetic, not a new hypothesis. Eviction beat only the tested neutral CLEAR reminder, not explicit cancellation/default or text-history editing/re-prefill; check 36's decisive numbers are independently verified by results/check36-review-fable.md (reviewed source commit c294688), ACCURATE-WITH-CORRECTIONS: R2/R3 outputs match 64/64, while cache differences are unquantified relative to activation scale. Bind that review SHA-256 4819d670238adc1ae732e19b11958ffd5b1949e59131feacf8c23ac33e45809a and the reviewed source dependencies at freeze.

Five paired arms (same episode inputs, shared unscreened SET/HOLD answers, exogenous delays, renderer and decoding; later scored answers evolve within each arm):
1. neither: replace the live rule in the original old instruction slot; retain assistant bodies.
2. placement-only: remove that old-slot rule and render the identical live rules/default INSIDE the current request user message (cue + task input in the same turn); retain bodies; no refresh at HOLD or neutral request two.
3. eviction-only: old-slot rule update plus check-39-selected placeholder repair of all assistant task-response bodies attributed to the superseded event, independent of correctness.
4. both: live rules/default INSIDE the current request user message (same turn as task input) plus the identical placeholder repair/scope mask; intervene only at SWITCH, BACK and CLEAR.
5. text-restate: retain bodies; render the following exact template INSIDE the current request user message (same turn as task input) at EVERY scored request, explicitly canceling the superseded rule and restating every live rule/default, including unchanged constraints. Its generosity is deliberate; both-vs-text-restate carries the claim, the other two contrasts test each component's added value.
All arms retire superseded cue/recap text using the same event map; never leave conflicting old cue text selectively in one arm. At CLEAR remove the task cue, leaving the explicit baseline/default rules. Keep user/tool turns, event provenance and assistant closures; no whole-pair deletion in this leg. Replace the entire retired assistant body, including empty thinking prefill, with the single-token period "." (check 39 token ID 13), preserving assistant header, im_end and newline. An adjacent-turn placement arm is NOT run: check 38 T4 already records 11/32 under its unanswered-turn limitation. Do not restore previously evicted answers at BACK. Re-prefill every edited text history from empty KV through one valid chat renderer with contiguous positions; save original-to-edited token maps. This estimates the text-context intervention and makes no recompute-free cache-speed claim.
Text-restate template, verbatim (UTF-8, LF between the four lines, NO trailing LF; braces are literal template slots):
```text
Cancel the superseded task rule: {superseded_rule}.
Your earlier answers under that rule followed a rule that no longer applies; do not imitate your earlier answers; the rules that apply now are:
{live_rules_or_default}
Use earlier facts when requested, while following the current rules for this answer.
```
Template SHA-256: `2658b026d6bd22d4ed460b34c543abc159e4e80ff56f367be4eaf5c035f8e8d7`. Render superseded_rule from the last retired rule (or the fixed string "none" before any change); render live_rules_or_default in fixed order: current task/default, output schema, unchanged tag, then current request obligations. Never insert target answers or collateral fact values into a recap. At CLEAR and neutral request two explicitly say to copy the current payload without the canceled transformation. These bytes and the original readings were committed in DRAFT v1 at 2ea04e9 before this drafting work accessed check 37 outcomes; retain that earliest immutable anchor. V2 explicitly incorporates already-observed development checks 38/39 and these review dispositions; commit the v2 readings before any FOCUS-2 competence/pilot/final outcome. No retroactive preregistration claim or later wording/repair-choice rescue.

Episode generator law (freeze the complete strings, token layouts, checker mutations and generator source before competence/pilot outcomes):
- Every historical user turn, including cue/fact events and EVERY delay/filler, belongs to a complete user+assistant pair with valid closure (including valid tool-call/return groups); no unanswered user turns anywhere in history. Only the current request awaits generation. Never render the moved live rules as a separate user turn.
- Final N=256: 64 each for sort direction (ascending/descending), letter case (lower/upper), field selection (left/right), output representation (JSON array/comma-separated string). Each family has 32 episodes per initial direction; cross each direction with zero/512 delay for 16/cell. SWITCH reverses A->B; BACK reverses B->A; publish BOTH actual change directions at each checkpoint.
- Independent SHA-256-derived RNG streams from `focus2-v1:{seed}:{bank}:{family}:{direction}:{delay}:{episode}:{request}:{purpose}`, big-endian digest to Random(MT19937); seed 9053702 for competence and a purpose-disjoint timing pilot, 9053703 for final. No favorable seed searches. Generate deterministically and hash before model loading.
- Sort operands: uniformly sample 4–6 distinct integers from -99..99, random order, reject already ascending/descending. Case: three distinct mixed-case ASCII nonce words, lengths 3–6, ensuring lower/upper/copy differ. Fields: three ordered {left,right} records with distinct integer values, select one column in record order. Representation: 4–6 distinct integers, array vs comma-separated decimal string with no spaces. Default at CLEAR copies the presented payload exactly as a JSON value, without the canceled transform; representation uses an explicit {"items": [...]} input so default differs from either skill.
- Every scored answer uses compact JSON {"answer": <task value>, "tag": <integer episode tag>} without prose or unrequested keys; user/tool facts are distinct two-digit integers; the frozen request may additionally request memo/user_fact/tool_fact/assistant_fact. The unchanged tag and envelope apply throughout, including CLEAR. Fixed-schema task errors are task failures, not automatically structural breakage. Bound all gold replies below 64 tokenizer tokens before freeze.
- Two actual prior answers, SET and HOLD under A, are generated once and shared across all five arms, never screened/replaced. Record each answer's live-task/schema correctness and the both-correct flag before intervention; source failures never remove an episode. Then score SWITCH(B), unrefreshed HOLD(B), BACK(A), CLEAR(default), and neutral request two(default) on fresh payloads. No later success repairs an earlier failed endpoint.
- A delay occurs before each initial HOLD, post-SWITCH HOLD and second neutral request: zero means no pair; 512 means one complete neutral user+actual-assistant pair with exactly 512 tokenizer tokens of user content. Replies are generated once in an isolated neutral context, retained unscreened and replayed identically across arms; report full rendered delay length including assistant and wrapper tokens. No unanswered user turns, empty assistant bodies or cropped replies; neutral pairs are outside the transformed-task scope. This is a controlled replay delay, not a natural-conversation claim.
- All episodes contain later-needed user and tool facts with valid tool-call/return closure; neutral request two asks for both, with no value restated at query time. In exactly 16/64 episodes per family (4 per direction/delay cell), SET also asks the assistant to invent a six-letter ASCII memo; only that actual assistant body contains it, and neutral request two asks for it. No external copy is returned to the model after eviction. Score source-missing/invalid memos as collateral failures on the fixed 64 denominator, never drop them. This deliberately measures eviction's assistant-authored-fact cost.
- Dedup all payload identities within/across competence, pilot, final and development/repair banks using semantic fingerprints (unordered sets for sorting, casefolded words, ordered record pairs, unordered representation values), not seed or episode ID alone; ignore episode IDs/tags and reject permutations preserving the task instance. Before freeze an outcome-free development fingerprint manifest covering checks 31–39 and repair fixtures must establish disjointness without consuming historical responses or scores; disclosed check 37/39 decision receipts are not generation inputs. If unavailable, do not freeze. Do not open benchmark banks or revive SC1 authoring/cohorts.
Competence gate: 64 independent immediate visible-cue fixtures for EACH of the two directions in EACH family (512 total); require >=56/64 exact live-task/schema successes in every cell, reporting directions separately. Also require >=56/64 on each family's 64 fresh default-copy fixtures (256). No family dropping/substitution, prompt edits or retesting after outcomes: any miss is INELIGIBLE and stops this four-family leg.

Pre-registered expectation for the future FOCUS-2 run: both minus placement-only is bounded by the demonstration-attributable share, roughly 10/32 of the historical 29/32 deficit; eviction does not address the roughly 19/32 pre-demo decay. On the historical sort SWITCH comparison, inside-request placement already achieves 27/32, so remaining headroom is at most 5/32 and the expected eviction gain is smaller. These are scoped development-based expectations, not a proved numerical ceiling for the four-family all-five endpoint or an added pass/fail gate. Retain the both-correct mechanism stratum; no new no-answer control arm is added.

Primary endpoint Y: episode succeeds iff ALL five post-change answers satisfy the task/default checker and every unchanged constraint, with no structural breakage. Fact-recall subchecks are separate collateral endpoints, excluded from Y (including assistant facts); a missing/wrong fact field alone is not structural breakage, while malformed overall JSON still is. Publish checkpoint/family/direction/delay counts and all fixed denominators.
Decision rule: for both vs EACH of placement-only, eviction-only and text-restate, let b=both succeeds/comparator fails and c=converse. Require b>c and exact one-sided McNemar p=P[Binomial(b+c,0.5)>=b], with p=1 if no discordances; Holm step-down across these three at familywise .05. Also require >=5 percentage points over text-restate (>=13 net episodes/256). Report raw/adjusted p, 2x2 tables, nominal paired 95% difference intervals from inverted paired-score bounds (asymptotic, not exact finite-sample), and all margins. A <5-point component contrast is labeled MARGINAL ADDED CONTROL even if significant; it cannot carry the headline joint-control claim (kimi K3 accepted-with-change; the requested primary gate is retained).
Secondary readings (fixed even if both fails): report "placement-only >= text-restate" on observed Y rates and "eviction-only vs neither", with paired 2x2 tables, signed differences, nominal paired 95% intervals and descriptive exact one-sided McNemar p-values in the named candidate direction (placement-only or eviction-only). Observed placement parity is not demonstrated noninferiority/equivalence; an eviction-only benefit tests old-slot removal and cannot establish an added benefit over placement. These descriptive comparisons do not enter the three-test primary Holm family, rescue a failed primary/safety gate, or carry the headline claim.
F11 stratification: repeat every primary contrast separately for both-correct versus at-least-one-wrong prior answers, with n, differences, paired intervals and descriptive p-values (no replacement primary test or selective pooling). The both-correct stratum is the stale-demonstration mechanism estimate; a benefit confined to prior-error episodes supports bad-demonstration removal, not stale-correct-demonstration release. Empty strata are uninformative, never a pass. Report ascending/default impositions at CLEAR and neutral request two per initial direction, alongside correct copies and placeholder imitation.

Safety gate vs text-restate: define episode breakage B=any scored output empty, placeholder-only after whitespace stripping, truncated without valid EOS by the 64-token cap, repetitive (an exact token block of period 1–4 repeated >=8 consecutive times), or schema-invalid. Save separate flags; placeholder imitation is breakage, never neutral success. Wrong task values with valid structure remain task failures. EOS on the cap is not truncation.
F6: let h=both broken/text-restate valid and r=converse. Require one-sided paired exact McNemar harm p=P[Binomial(h+r,0.5)>=h]>.05 AND h<=2/256, with all 256 episodes complete. Report paired counts and the one-sided exact 95% upper bound for h/256: 0/256 ->1.1634%, 2/256 ->2.4387%. This operational "not-worse" screen is absence of detected harm plus a count cap, NOT proof of noninferiority/harmlessness.
Collateral/unchanged constraints: separately report paired episode failures for user facts (n=256), tool facts (n=256), assistant-authored facts (n=64, also by source validity), and any unchanged constraint (n=256). Each category must have no greater observed failure count under both than text-restate; publish discordances, exact harm tests and intervals. A cost in any category fails safety even if primary control improves. No exemption for expected assistant-fact loss; print that cost next to the benefit.

Repair dependency: use exactly check 39's preselected placeholder receipt (results/quick-checks/check39/README.md and 4b/summary.json at commit e30343d24cc6e2ad171ae5e44ff2b6d3ea1c18f0; summary SHA-256 e5b906f54be46d7171d6a90eb670b37bdd6621297f2adc069214926a4c76c951), PROCEED_PLACEHOLDER. Preregistration e24afd4b07870b4985d184f4183fea505b72b372 precedes recorded launch 2026-09-05T08:43:10Z; the frozen reading matches that commit and runner/dependency hashes match the receipt. Its prospective rule requires, separately per mode, net discordant breakage b-c<=2 and exact one-sided harm p>=.05, surviving-release losses<=2/64, and both neutral copies>=56/64 in both variants/modes. Placeholder surviving releases 60/59 vs intact 59/58; rebuilt 58/57 vs 59/58 (reported, not active-success-gating); placeholder neutral 64/64 twice in both modes; intact neutral 64/64 surviving, 63/64 then 64/64 rebuilt; broken episodes 0 vs 4 per mode (b=0,c=4,p=1). This satisfies the repair prerequisite; check 37 remains STOP-under-its-rule (results/quick-checks/check37/README.md), not pooled or relabeled. Bind scripts/focus_check39.py and its imported check-37 Engine.repair implementation: whole-body period replacement with closures. Check 39 preserved absolute gaps and diagnostic rebuilt shadows; FOCUS-2 retains its already-declared contiguous text re-prefill, which must be independently validated on CPU before freeze. The receipt certifies active-cue structural behavior plus explicit cancellation only, not instruction-change efficacy, lenient accuracy improvement, or general safety; do not substitute its net b-c rule for FOCUS-2 F6's raw h<=2 cap. Missing/mismatched provenance is INVALID; no variant reselection or rerun.
Cost: HARD cap 6 GPU-h for this leg, including loads, competence, timing pilot, all final generations, delays and retries/diagnostics; checks 37/38/39 are separately accounted development (14.715/8.02/16.591 GPU-min respectively), never rerun here. Future foreground pilot uses 16 disjoint episodes (one/family/direction/delay), all five arms, recording prefill/decode timing and peak memory. Timing only; no outcome-based changes. Project ALL remaining work by worst measured cell cost with 25% reserve; refuse work if spent+projection exceeds 6 GPU-h. Check budgets cooperatively before loads/prefills and each decode step; no background jobs, external timeouts or process signals.
Stop rules: no run while DRAFT, missing/mismatched check-36 accuracy-review binding, missing committed readings/hashes/check-39 PROCEED_PLACEHOLDER receipt, competence miss, check-39 repair STOP/absent/unselected policy, duplicate/invalid banks, or failed CPU checker/renderer tests. The check-36 review and check-39 repair prerequisites are satisfied as recorded above; check-37 STOP remains historical under its own rule and is not a v2 launch veto. No rescue variants, extra families, controller grids or benchmark stages. On the third irreversible newly-broken both-only episode, stop scheduling (safety cannot pass); preserve records, report FAIL-SAFETY with incomplete denominators, not a complete effect estimate. Resource/cap/interruption -> INCOMPLETE; hash/protocol drift -> INVALID. No signal/termination of any process, including ones launched by this work; no adaptive early efficacy stop or extra sampling.
Prewritten readings (v1 anchor retained; v2 committed before any FOCUS-2 outcome, with development outcomes disclosed): PASS requires competence, all primary comparisons/magnitude and safety, within scope below; significant but <5-point component gains -> PASS with MARGINAL ADDED CONTROL, no headline joint-control claim. Failure to beat placement/text -> no demonstrated extra mechanism (compatible with prompting), not equivalence. Repair STOP/loss of CLEAR gains -> release fragile, do not proceed/promote. Primary benefit plus collateral/breakage failure -> unsafe context management, do not promote. Benefit confined to wrong prior answers -> error-demonstration cleanup; no stale-correct mechanism claim. If both fails, still publish the fixed placement-only >= text-restate and eviction-only vs neither secondary readings with their limits above. Other failed contrasts -> FAIL, not a compact-state conclusion; INELIGIBLE/INCOMPLETE/INVALID earn no efficacy claim. A null on the stringent all-five endpoint is not evidence of absence or established power.
Claim ceiling: "context-management mechanism on a frozen trunk; not compact state, not waves"; oracle-managed synthetic episodes only, no autonomous change detection, benchmark transfer, literature priority, Miller weight-circuit selection, or general safety claim. Retained HOLD asymmetry and default priors stay visible. Neither/eviction-only alone cannot carry a headline.

Freeze sequence: (0) Preserve DRAFT v1 commit 2ea04e9 as the earliest immutable text-restate/readings anchor; the exact template bytes/hash are unchanged. Commit this v2 section/readings before any FOCUS-2 outcome, disclosing that checks 37/38/39 are already observed development. (1) Check 36's accuracy review is complete (ACCURATE-WITH-CORRECTIONS); bind its reviewed source hashes and the check-38 interpretive review. Bind check 39's e24afd4 prewritten reading/choice/code and launch chronology to the e30343d PROCEED_PLACEHOLDER receipt; retain check 37 STOP separately without pooling or changing the template. (2) CPU build/test; freeze generator, ALL cue/default/delay/fact/placement templates and rendered token maps, event masks, checkers/mutations, banks/fingerprints, arm order, model/tokenizer/config hashes, repair receipt and this section snapshot. Registration review must clear the draft before model execution.
(3) Commit the immutable registration snapshot/readings/templates/manifest with SHA-256 of each dependency (exclude the manifest's own hash to avoid self-reference); verify ignored artifacts with git ls-files and content in the named freeze commit. Record freeze commit + manifest hash in an append-only launch receipt before ANY competence/pilot outcome. (4) Run only the frozen competence/pilot gates, then one final run; analyze the same immutable rows. run must refuse DRAFT, uncommitted/dirty/missing/mismatched dependencies or readings, STOP/absent repair or failed/absent competence/pilot gates BEFORE model loading. Bind the section snapshot, not later unrelated LEDGER appends; no --force bypass. Earlier development results are disclosed, never misrepresented as fresh evidence.
Artifacts per generated request in the same run: episode/arm/checkpoint, family/direction/delay, input and emitted token IDs/text/EOS, shared-prior correctness and hash, actual fact source, live-rule/scope/turn/token-position maps, removed body IDs/hashes and replacement tokens, task/constraint/fact/imposition/placeholder/breakage flags, cost/peak-memory and all freeze hashes. Persist raw records before aggregation; analyze verifies completeness, pairing, integrity and recomputes decisions. Partial runs retain original denominators and status; no overwritten/reselected outputs or hidden imputation.

Review disposition (design decisions, not reviewer closure): carry forward v1 fable F1–F13 and kimi K1–K6 except the explicit updates here. Fable check-36 ACCURATE-WITH-CORRECTIONS satisfies the independent-accuracy prerequisite; its confounded-ordering interpretation is corrected by check 38. Fable check-38 (a) accepted—31->12->2 decay/demo decomposition, role 2/1, before/after +10/0, inside/adjacent 27/11 and sort-present default 12/32 replace the broad precedence slogan; (b) accepted—cross-check/list/demo/cache differences, unanswered-turn confound, age after demos untested, imitation vs inferred rule unresolved, and T2 whole-turn deletion does not certify placeholder repair; (c) accepted—inside-request placement, demonstration-share/headroom expectation, complete pairs and unchanged both-correct stratum; optional extra no-answer/one-neutral-pair readout deferred to a separate registration to preserve the five-arm/count/cost design. Check 38's reading was fixed by run-time copy/hash, not a prior commit; no false prelaunch anchor. Kimi's four wording fixes in results/focus-synthesis-review-kimi.md: Fix 1 accepted—check 32 presence, not task identity; Fix 2 accepted—retained HOLD 32/32 ascending, 23/32 descending and joint 3/32, 5/32; Fix 3 accepted-with-change per Brian—keep >=5 points over text-restate only, label <5-point component gains MARGINAL ADDED CONTROL and withhold headline joint-control claim; Fix 4 satisfied—check 36 independently reviewed, check 33 review not asserted. Optional Fix 5 remains accepted—later requests cannot recover a failed endpoint. F4/F8 freeze/provenance now bind original anchor 2ea04e9 plus prospective check 39 and this v2; historical check 37's coarse n=32 STOP stands. F6/F9/F11/F12 safety, all other gates, seeds (including the focus2-v1 RNG namespace), families, claim ceiling and freeze sequence (2)–(4) are retained. No finding refuted; independent registration review remains required.

### CPU implementation handoff — 2026-09-05 (write-ahead)

Fit-on: none. Direct foreground Codex implementation under the focus2-harness v2
brief; no wrapper or delegated agent. Tests precede implementation. Only the three
new harness/test paths and this append-only handoff are in scope. DRAFT / NOT
REGISTERED remains in force; no model execution is authorized. Governing legacy
protocol/state files were located under archive/; the current v2 section at
7d0c244 governs this task. Check-36 and check-38 reviews and the outcome-limited
check-39 receipt/reading at e30343d were read; historical runner sources are
inspected only. No historical raw response banks are development inputs.

CPU handoff complete (implementation acceptance only). Code commit:
`8f4b76cb7711ee033dc66fcdc57bc62e1519c7d5`; tracked membership verified for
`scripts/focus2.py`, `src/stencil/focus2.py`, and `tests/test_focus2.py`.
Implemented the five text-history arms, whole-body period replacement with
retained closures and persisted token maps, fixed seeded banks/disjointness,
strict task/collateral/breakage checks, paired primary/secondary/stratified
readings, competence/timing certificates checked against raw records, committed
provenance checks before backend construction, exclusive durable request records,
cooperative budgets/interruption accounting, and CPU analysis. All four modes
were exercised only through injected fake trunks; the real tokenizer was used
locally for delay, closure, complete rendered-template hashes and gold cap checks.
`--prepare-freeze` emits candidates only and cannot register this draft.

Red/green evidence: the initial tests failed at collection because the new helper
module did not exist. Later adversarial refinements recorded 4 failed / 43 passed
in `/tmp/focus2-red-refinements.log` (immediate competence placement, counter
validation, output-directory binding, malformed tool groups), subsequently fixed.
Exact final acceptance outcomes, all foreground from the repo root:

- `CUDA_VISIBLE_DEVICES='' .venv/bin/python -m pytest -q tests/test_focus2.py`
  exited 0: **60 passed in 195.69s**. Log: `/tmp/focus2-acceptance-pytest.log`.
- `CUDA_VISIBLE_DEVICES='' .venv/bin/python scripts/focus2.py --help`
  exited 0. Log: `/tmp/focus2-acceptance-help.log`.
- `.venv/bin/python -m ruff check scripts/focus2.py src/stencil/focus2.py tests/test_focus2.py`
  exited 0, All checks passed. Log: `/tmp/focus2-acceptance-ruff.log`.
- `git diff --check -- scripts/focus2.py src/stencil/focus2.py tests/test_focus2.py LEDGER-PLAN.md`
  exited 0; repeated after this handoff append. No test-runner pipe or full suite.

Actual session metadata from the environment: model `gpt-6-astra`, effort `xhigh`,
Codex session/thread `01a070d8-03f3-7de1-b9ec-c04f7983c289`. Direct foreground
session as required by this brief; no wrapper log exists and no model/effort
relaunch or override was performed. The logs above are actual CPU test/check
logs; temporary Git repositories contain fabricated provenance and receipts.
Fit-on: none. No GPU/model launch, fitting/training, benchmark/sealed-input access,
process signals, background work, additional coder/reviewer/agent launch, or push.
Historical sources and `results/quick-checks/*` were not edited; no real outcome
artifacts were produced. The pre-existing untracked `scripts/focus_check32.py`
was left untouched.

Fixed development material read: check-36 independent accuracy review
`results/check36-review-fable.md` (ACCURATE-WITH-CORRECTIONS, reviewed source
c294688; prerequisite satisfied), check-38 interpretive corrections in
`results/check38-review-fable.md`, and the outcome-limited check-39 README,
4b/summary and prewritten reading at e30343d. Check-39 repair is satisfied as
**PROCEED_PLACEHOLDER**, e24afd4 -> e30343d; its net-discordance repair rule remains
separate from main F6's raw h<=2 and p>.05 gate. Check-37 **STOP remains unchanged,
not pooled and not a v2 launch veto**. Historical runner/repair source inspection
was limited to the authorized implementation dependencies; no historical raw
response banks, SC1 inputs or benchmark metadata were generator inputs.

Limitations and remaining prerequisites: CPU fixtures do not certify a real
FOCUS-2 result, model compatibility, competence, timing, efficacy or safety.
Conservative implementation choices for CPU review: every pilot cell exercises
the memo path for timing, and the third-both-only-breakage scheduling stop is
applied within each stage, without pooling pilot observations into final counts.
The current preflight requires Git membership for every declared dependency,
including model/tokenizer assets; final freeze must satisfy that contract.
Dependency hashes/commit membership and historical launch chronology must be
verified again at freeze; the outcome-free development dedup manifest covering
checks 31–39 plus repair fixtures is still required. Final template/bank/model/
tokenizer/config hashes, independent registration review and a committed freeze
remain outstanding. Preserve original template/readings anchor **2ea04e9**;
v2 readings were already committed at **7d0c244**, before any real FOCUS-2 outcome.
Registration binds an immutable section snapshot and the external launch receipt
binds its manifest/freeze commit and one output directory; later unrelated ledger
appendices do not invalidate the snapshot. **FOCUS-2 remains DRAFT / NOT REGISTERED.**
Next action: CPU review of this implementation and draft, followed by the governed
freeze sequence only when prerequisites are satisfied. No GPU next command is
authorized by this handoff, and no outstanding review is declared closed.

## FOCUS-2 — PLACEMENT + EVICTION AT INSTRUCTION CHANGE (DRAFT v3 = REGISTRATION CANDIDATE, 2026-09-05; supersedes v2, preserved above)
Data lineage FIRST — fit-on: none; development: checks 31–39 + repair fixtures; evaluated-on: fresh seeded synthetic override episodes in four task families, disjoint from development/competence/pilot inputs. NO benchmark contact in this leg. Multi-IF is CUT per fable F7 (no same-family turn-3 override events); a possible later placement-only do-no-harm check requires its own registration. Never open sealed IFEval inputs or sealed BFCL cohort contents; no fitting/training or benchmark-derived prompts, answers, scores, or tuning.
STATE: drafting only, CPU only; no experiment authorized by this section. Check 36's independent accuracy prerequisite is satisfied by results/check36-review-fable.md (ACCURATE-WITH-CORRECTIONS); its ordering correction is incorporated through results/check38-review-fable.md. Repair prerequisite is satisfied by check 39's PROCEED_PLACEHOLDER receipt at e30343d, preregistered at e24afd4; check 37 remains STOP under its own rule and is not pooled. This supersedes DRAFT v1 and the earlier unregistered learned-controller FOCUS-2 sketches; FOCUS-1's failed actuator is not revived. Registration review, CPU implementation/checks and the committed freeze remain outstanding; dispositions are not automatic reviewer closure.

Mechanism under test: with an oracle change/scope map derived solely from public instruction events and turn ownership, render the live task rules INSIDE the current request user message (same turn as the task input) and remove assistant answers produced under the superseded rule, on frozen Qwen3-4B (bf16, hf_compatible, greedy, thinking disabled, <=64 generated tokens/request). This tests whether stale own demonstrations obstruct new instructions, and whether their removal adds safe control beyond a strong current text reminder. Placement includes role/wording as well as position; attention weights and weight circuits are not measured. Prior ordering (results/check36-review-fable.md; results/check38-review-fable.md, plain answers (a)(b)(c)): check 36 alone confounded role, recency and demonstrations; check 38 separates the tested contrasts. Before two contrary answers, system/user cues give 2/32 and 1/32 B (no observed role benefit, not proof of no role effect); moving the user cue after the demonstrations gives 11/32 (paired +10/0), below its fixed threshold but evidence of a before/after effect. Inside-request placement gives 27/32 (check 35 TEXT) versus adjacent-turn placement 11/32 (check 38 T4; matched lists, 16/0); this cross-check comparison is not a randomized within-run contrast, has different demo answers/cache construction, and T4 has an unanswered cue turn. Age after demonstrations is untested. Old-system B without demonstrations decays 31->12/32 after one neutral turn (check 34 all_B SET vs check 38 T2, cross-check/different lists/unanswered filler); contrary answers then reduce 12->2/32 (T2 vs R3, paired 10/0). Thus 31->12->2 attributes roughly 19/32 to pre-demo decay and 10/32 to demonstrations, not the whole deficit to own answers. Check 38 T2 gives a sort-present ascending default of 12/32 despite B and no A information; cue-free/demo-free default is copy 64/64 (check 34 off), so T3's 31/32 A is demonstration-driven but does not separate imitation from inferring the old rule. Directions cannot be pooled away.
Evidence ceiling carried forward: checks 31–33 closed tested induction recipes, not every representation; check 32 encoded instruction presence rather than task identity, whereas check 33 had readability without induction. Check 34 retained HOLD was 32/32 ascending, 23/32 descending, with joint control 3/32 and 5/32. Matched K+V is expected attention arithmetic, not a new hypothesis. Eviction beat only the tested neutral CLEAR reminder, not explicit cancellation/default or text-history editing/re-prefill; check 36's decisive numbers are independently verified by results/check36-review-fable.md (reviewed source commit c294688), ACCURATE-WITH-CORRECTIONS: R2/R3 outputs match 64/64, while cache differences are unquantified relative to activation scale. Bind that review SHA-256 4819d670238adc1ae732e19b11958ffd5b1949e59131feacf8c23ac33e45809a and the reviewed source dependencies at freeze.

Five paired arms (same episode inputs, shared unscreened SET/HOLD answers, exogenous delays, renderer and decoding; later scored answers evolve within each arm):
1. neither: replace the live rule in the original old instruction slot; retain assistant bodies.
2. placement-only: remove that old-slot rule and render the identical live rules/default INSIDE the current request user message (cue + task input in the same turn); retain bodies; no refresh at HOLD or neutral request two.
3. eviction-only: old-slot rule update plus check-39-selected placeholder repair of all assistant task-response bodies attributed to the superseded event, independent of correctness.
4. both: live rules/default INSIDE the current request user message (same turn as task input) plus the identical placeholder repair/scope mask; intervene only at SWITCH, BACK and CLEAR.
5. text-restate: retain bodies; render the following exact template INSIDE the current request user message (same turn as task input) at EVERY scored request, explicitly canceling the superseded rule and restating every live rule/default, including unchanged constraints. Its generosity is deliberate; both-vs-text-restate carries the claim, the other two contrasts test each component's added value.
All arms retire superseded cue/recap text using the same event map; never leave conflicting old cue text selectively in one arm. At CLEAR remove the task cue, leaving the explicit baseline/default rules. Keep user/tool turns, event provenance and assistant closures; no whole-pair deletion in this leg. Replace the entire retired assistant body, including empty thinking prefill, with the single-token period "." (check 39 token ID 13), preserving assistant header, im_end and newline. An adjacent-turn placement arm is NOT run: check 38 T4 already records 11/32 under its unanswered-turn limitation. Do not restore previously evicted answers at BACK. Re-prefill every edited text history from empty KV through one valid chat renderer with contiguous positions; save original-to-edited token maps. This estimates the text-context intervention and makes no recompute-free cache-speed claim.
Text-restate template, verbatim (UTF-8, LF between the four lines, NO trailing LF; braces are literal template slots):
```text
Cancel the superseded task rule: {superseded_rule}.
Your earlier answers under that rule followed a rule that no longer applies; do not imitate your earlier answers; the rules that apply now are:
{live_rules_or_default}
Use earlier facts when requested, while following the current rules for this answer.
```
Template SHA-256: `2658b026d6bd22d4ed460b34c543abc159e4e80ff56f367be4eaf5c035f8e8d7`. Render superseded_rule from the last retired rule (or the fixed string "none" before any change); render live_rules_or_default in fixed order: current task/default, output schema, unchanged tag, then current request obligations. Never insert target answers or collateral fact values into a recap. At CLEAR and neutral request two explicitly say to copy the current payload without the canceled transformation. These bytes and the original readings were committed in DRAFT v1 at 2ea04e9 before this drafting work accessed check 37 outcomes; retain that earliest immutable anchor. V2 explicitly incorporates already-observed development checks 38/39 and these review dispositions; commit the v2 readings before any FOCUS-2 competence/pilot/final outcome. No retroactive preregistration claim or later wording/repair-choice rescue.

Episode generator law (freeze the complete strings, token layouts, checker mutations and generator source before competence/pilot outcomes):
- Every historical user turn, including cue/fact events and EVERY delay/filler, belongs to a complete user+assistant pair with valid closure (including valid tool-call/return groups); no unanswered user turns anywhere in history. Only the current request awaits generation. Never render the moved live rules as a separate user turn.
- Final N=256: 64 each for sort direction (ascending/descending), letter case (lower/upper), field selection (left/right), output representation (JSON array/comma-separated string). Each family has 32 episodes per initial direction; cross each direction with zero/512 delay for 16/cell. SWITCH reverses A->B; BACK reverses B->A; publish BOTH actual change directions at each checkpoint.
- Independent SHA-256-derived RNG streams from `focus2-v1:{seed}:{bank}:{family}:{direction}:{delay}:{episode}:{request}:{purpose}`, big-endian digest to Random(MT19937); seed 9053702 for competence and a purpose-disjoint timing pilot, 9053703 for final. No favorable seed searches. Generate deterministically and hash before model loading.
- Sort operands: uniformly sample 4–6 distinct integers from -99..99, random order, reject already ascending/descending. Case: three distinct mixed-case ASCII nonce words, lengths 3–6, ensuring lower/upper/copy differ. Fields: three ordered {left,right} records with distinct integer values, select one column in record order. Representation: 4–6 distinct integers, array vs comma-separated decimal string with no spaces. Default at CLEAR copies the presented payload exactly as a JSON value, without the canceled transform; representation uses an explicit {"items": [...]} input so default differs from either skill.
- Every scored answer uses compact JSON {"answer": <task value>, "tag": <integer episode tag>} without prose or unrequested keys; user/tool facts are distinct two-digit integers; the frozen request may additionally request memo/user_fact/tool_fact/assistant_fact. The unchanged tag and envelope apply throughout, including CLEAR. Fixed-schema task errors are task failures, not automatically structural breakage. Bound all gold replies below 64 tokenizer tokens before freeze.
- Two actual prior answers, SET and HOLD under A, are generated once and shared across all five arms, never screened/replaced. Record each answer's live-task/schema correctness and the both-correct flag before intervention; source failures never remove an episode. Then score SWITCH(B), unrefreshed HOLD(B), BACK(A), CLEAR(default), and neutral request two(default) on fresh payloads. No later success repairs an earlier failed endpoint.
- A delay occurs before each initial HOLD, post-SWITCH HOLD and second neutral request: zero means no pair; 512 means one complete neutral user+actual-assistant pair with exactly 512 tokenizer tokens of user content. Replies are generated once in an isolated neutral context, retained unscreened and replayed identically across arms; report full rendered delay length including assistant and wrapper tokens. No unanswered user turns, empty assistant bodies or cropped replies; neutral pairs are outside the transformed-task scope. This is a controlled replay delay, not a natural-conversation claim.
- All episodes contain later-needed user and tool facts with valid tool-call/return closure; neutral request two asks for both, with no value restated at query time. In exactly 16/64 episodes per family (4 per direction/delay cell), SET also asks the assistant to invent a six-letter ASCII memo; only that actual assistant body contains it, and neutral request two asks for it. No external copy is returned to the model after eviction. Score source-missing/invalid memos as collateral failures on the fixed 64 denominator, never drop them. This deliberately measures eviction's assistant-authored-fact cost.
- Dedup all payload identities within/across competence, pilot, final and development/repair banks using semantic fingerprints (unordered sets for sorting, casefolded words, ordered record pairs, unordered representation values), not seed or episode ID alone; ignore episode IDs/tags and reject permutations preserving the task instance. Before freeze an outcome-free development fingerprint manifest covering checks 31–39 and repair fixtures must establish disjointness without consuming historical responses or scores; disclosed check 37/39 decision receipts are not generation inputs. If unavailable, do not freeze. Do not open benchmark banks or revive SC1 authoring/cohorts.
Competence gate: 64 independent immediate visible-cue fixtures for EACH of the two directions in EACH family (512 total); require >=52/64 exact live-task/schema successes in every skill cell (81%, exact one-sided 95% lower bound 0.71), reporting directions separately. Also require >=56/64 on each family's 64 fresh default-copy fixtures (256). No family dropping/substitution, prompt edits or retesting after outcomes: any miss is INELIGIBLE and stops this four-family leg.

Pre-registered expectation for the future FOCUS-2 run: both minus placement-only is bounded by the demonstration-attributable share, roughly 10/32 of the historical 29/32 deficit; eviction does not address the roughly 19/32 pre-demo decay. On the historical sort SWITCH comparison, inside-request placement already achieves 27/32, so remaining headroom is at most 5/32 and the expected eviction gain is smaller. These are scoped development-based expectations, not a proved numerical ceiling for the four-family all-five endpoint or an added pass/fail gate. Retain the both-correct mechanism stratum; no new no-answer control arm is added. At a true 3-point both-minus-placement-only gain the primary contrast has ~0.1–0.2 power at N=256 (exact, Holm); a FAIL on that contrast is expected under the pre-registered expectation and is read as 'no demonstrated extra mechanism', never as evidence of absence.

Primary endpoint Y: episode succeeds iff ALL five post-change answers satisfy the task/default checker and every unchanged constraint, with no structural breakage. Fact-recall subchecks are separate collateral endpoints, excluded from Y (including assistant facts); a missing/wrong fact field alone is not structural breakage, while malformed overall JSON still is. Publish checkpoint/family/direction/delay counts and all fixed denominators.
Decision rule: for both vs EACH of placement-only, eviction-only and text-restate, let b=both succeeds/comparator fails and c=converse. Require b>c and exact one-sided McNemar p=P[Binomial(b+c,0.5)>=b], with p=1 if no discordances; Holm step-down across these three at familywise .05. Also require >=5 percentage points over text-restate (>=13 net episodes/256). Report raw/adjusted p, 2x2 tables, nominal paired 95% difference intervals from inverted paired-score bounds (asymptotic, not exact finite-sample), and all margins. A <5-point component contrast is labeled MARGINAL ADDED CONTROL even if significant; it cannot carry the headline joint-control claim (kimi K3 accepted-with-change; the requested primary gate is retained).
Secondary readings (fixed even if both fails): report "placement-only >= text-restate" on observed Y rates and "eviction-only vs neither", with paired 2x2 tables, signed differences, nominal paired 95% intervals and descriptive exact one-sided McNemar p-values in the named candidate direction (placement-only or eviction-only). Observed placement parity is not demonstrated noninferiority/equivalence; an eviction-only benefit tests old-slot removal and cannot establish an added benefit over placement. These descriptive comparisons do not enter the three-test primary Holm family, rescue a failed primary/safety gate, or carry the headline claim.
F11 stratification: repeat every primary contrast separately for both-correct versus at-least-one-wrong prior answers, with n, differences, paired intervals and descriptive p-values (no replacement primary test or selective pooling). The both-correct stratum is the stale-demonstration mechanism estimate; a benefit confined to prior-error episodes supports bad-demonstration removal, not stale-correct-demonstration release. Empty strata are uninformative, never a pass. Report ascending/default impositions at CLEAR and neutral request two per initial direction, alongside correct copies and placeholder imitation.

Safety gate vs text-restate: define episode breakage B=any scored output empty, placeholder-only after whitespace stripping, truncated without valid EOS by the 64-token cap, repetitive (an exact token block of period 1–4 repeated >=8 consecutive times), or schema-invalid. Save separate flags; placeholder imitation is breakage, never neutral success. Wrong task values with valid structure remain task failures. EOS on the cap is not truncation.
F6: let h=both broken/text-restate valid and r=converse. Require one-sided paired exact McNemar harm p=P[Binomial(h+r,0.5)>=h]>.05 AND h<=5/256, with all 256 episodes complete. Report paired counts and the one-sided exact 95% upper bound for h/256: 0/256 ->1.1634%, 5/256 ->4.0626%. This operational "not-worse" screen is absence of detected harm plus a count cap, NOT proof of noninferiority/harmlessness.
Collateral/unchanged constraints: separately report paired episode failures for user facts (n=256), tool facts (n=256), assistant-authored facts (n=64, also by source validity), and any unchanged constraint (n=256). User facts, tool facts and the unchanged constraint are binding: for each, with h=both fails/text-restate valid and r=converse, require one-sided exact McNemar harm p>.05 AND h-r<=2 (net, the check-39 form; the three tests are reported unadjusted, each must pass). Assistant-authored facts are the disclosed, pre-registered cost of eviction, NOT a binding gate: publish paired failure counts, discordances, exact harm p and interval by source validity, and print that cost in the same table as the primary benefit; the headline claim must carry the sentence 'eviction forfeits assistant-authored content it removes (x/64 vs y/64)'. No PASS wording may omit it.

Repair dependency: use exactly check 39's preselected placeholder receipt (results/quick-checks/check39/README.md and 4b/summary.json at commit e30343d24cc6e2ad171ae5e44ff2b6d3ea1c18f0; summary SHA-256 e5b906f54be46d7171d6a90eb670b37bdd6621297f2adc069214926a4c76c951), PROCEED_PLACEHOLDER. Preregistration e24afd4b07870b4985d184f4183fea505b72b372 precedes recorded launch 2026-09-05T08:43:10Z; the frozen reading matches that commit and runner/dependency hashes match the receipt. Its prospective rule requires, separately per mode, net discordant breakage b-c<=2 and exact one-sided harm p>=.05, surviving-release losses<=2/64, and both neutral copies>=56/64 in both variants/modes. Placeholder surviving releases 60/59 vs intact 59/58; rebuilt 58/57 vs 59/58 (reported, not active-success-gating); placeholder neutral 64/64 twice in both modes; intact neutral 64/64 surviving, 63/64 then 64/64 rebuilt; broken episodes 0 vs 4 per mode (b=0,c=4,p=1). This satisfies the repair prerequisite; check 37 remains STOP-under-its-rule (results/quick-checks/check37/README.md), not pooled or relabeled. Bind scripts/focus_check39.py and its imported check-37 Engine.repair implementation: whole-body period replacement with closures. Check 39 preserved absolute gaps and diagnostic rebuilt shadows; FOCUS-2 retains its already-declared contiguous text re-prefill, which must be independently validated on CPU before freeze. The receipt certifies active-cue structural behavior plus explicit cancellation only, not instruction-change efficacy, lenient accuracy improvement, or general safety; do not substitute its net b-c rule for FOCUS-2 F6's raw h<=2 cap. Missing/mismatched provenance is INVALID; no variant reselection or rerun.
Cost: HARD cap 6 GPU-h for this leg, including loads, competence, timing pilot, all final generations, delays and retries/diagnostics; checks 37/38/39 are separately accounted development (14.715/8.02/16.591 GPU-min respectively), never rerun here. Future foreground pilot uses 16 disjoint episodes (one/family/direction/delay), all five arms, recording prefill/decode timing and peak memory. Timing only; no outcome-based changes. Project ALL remaining work by worst measured cell cost with 25% reserve; refuse work if spent+projection exceeds 6 GPU-h. Check budgets cooperatively before loads/prefills and each decode step; no background jobs, external timeouts or process signals.
Stop rules: no run while DRAFT, missing/mismatched check-36 accuracy-review binding, missing committed readings/hashes/check-39 PROCEED_PLACEHOLDER receipt, competence miss, check-39 repair STOP/absent/unselected policy, duplicate/invalid banks, or failed CPU checker/renderer tests. The check-36 review and check-39 repair prerequisites are satisfied as recorded above; check-37 STOP remains historical under its own rule and is not a v2 launch veto. No rescue variants, extra families, controller grids or benchmark stages. On the sixth irreversible newly-broken both-only episode, stop scheduling (safety cannot pass); preserve records, report FAIL-SAFETY with incomplete denominators, not a complete effect estimate. Resource/cap/interruption -> INCOMPLETE; hash/protocol drift -> INVALID. No signal/termination of any process, including ones launched by this work; no adaptive early efficacy stop or extra sampling.
Prewritten readings (v1 anchor retained; v2 committed before any FOCUS-2 outcome, with development outcomes disclosed): PASS requires competence, all primary comparisons/magnitude and safety, within scope below; significant but <5-point component gains -> PASS with MARGINAL ADDED CONTROL, no headline joint-control claim. Failure to beat placement/text -> no demonstrated extra mechanism (compatible with prompting), not equivalence. Repair STOP/loss of CLEAR gains -> release fragile, do not proceed/promote. Primary benefit plus collateral/breakage failure -> unsafe context management, do not promote. Benefit confined to wrong prior answers -> error-demonstration cleanup; no stale-correct mechanism claim. If both fails, still publish the fixed placement-only >= text-restate and eviction-only vs neither secondary readings with their limits above. Other failed contrasts -> FAIL, not a compact-state conclusion; INELIGIBLE/INCOMPLETE/INVALID earn no efficacy claim. A null on the stringent all-five endpoint is not evidence of absence or established power.
Claim ceiling: "context-management mechanism on a frozen trunk; not compact state, not waves"; oracle-managed synthetic episodes only, no autonomous change detection, benchmark transfer, literature priority, Miller weight-circuit selection, or general safety claim. Retained HOLD asymmetry and default priors stay visible. Neither/eviction-only alone cannot carry a headline.

Freeze sequence: (0) Preserve DRAFT v1 commit 2ea04e9 as the earliest immutable text-restate/readings anchor; the exact template bytes/hash are unchanged. Commit this v2 section/readings before any FOCUS-2 outcome, disclosing that checks 37/38/39 are already observed development. (1) Check 36's accuracy review is complete (ACCURATE-WITH-CORRECTIONS); bind its reviewed source hashes and the check-38 interpretive review. Bind check 39's e24afd4 prewritten reading/choice/code and launch chronology to the e30343d PROCEED_PLACEHOLDER receipt; retain check 37 STOP separately without pooling or changing the template. (2) CPU build/test; freeze generator, ALL cue/default/delay/fact/placement templates and rendered token maps, event masks, checkers/mutations, banks/fingerprints, arm order, model/tokenizer/config hashes, repair receipt and this section snapshot. Registration review must clear the draft before model execution.
(3) Commit the immutable registration snapshot/readings/templates/manifest with SHA-256 of each dependency (exclude the manifest's own hash to avoid self-reference); verify ignored artifacts with git ls-files and content in the named freeze commit. Record freeze commit + manifest hash in an append-only launch receipt before ANY competence/pilot outcome. (4) Run only the frozen competence/pilot gates, then one final run; analyze the same immutable rows. run must refuse DRAFT, uncommitted/dirty/missing/mismatched dependencies or readings, STOP/absent repair or failed/absent competence/pilot gates BEFORE model loading. Bind the section snapshot, not later unrelated LEDGER appends; no --force bypass. Earlier development results are disclosed, never misrepresented as fresh evidence.
Artifacts per generated request in the same run: episode/arm/checkpoint, family/direction/delay, input and emitted token IDs/text/EOS, shared-prior correctness and hash, actual fact source, live-rule/scope/turn/token-position maps, removed body IDs/hashes and replacement tokens, task/constraint/fact/imposition/placeholder/breakage flags, cost/peak-memory and all freeze hashes. Persist raw records before aggregation; analyze verifies completeness, pairing, integrity and recomputes decisions. Partial runs retain original denominators and status; no overwritten/reselected outputs or hidden imputation.

Review disposition (design decisions, not reviewer closure): carry forward v1 fable F1–F13 and kimi K1–K6 except the explicit updates here. Fable check-36 ACCURATE-WITH-CORRECTIONS satisfies the independent-accuracy prerequisite; its confounded-ordering interpretation is corrected by check 38. Fable check-38 (a) accepted—31->12->2 decay/demo decomposition, role 2/1, before/after +10/0, inside/adjacent 27/11 and sort-present default 12/32 replace the broad precedence slogan; (b) accepted—cross-check/list/demo/cache differences, unanswered-turn confound, age after demos untested, imitation vs inferred rule unresolved, and T2 whole-turn deletion does not certify placeholder repair; (c) accepted—inside-request placement, demonstration-share/headroom expectation, complete pairs and unchanged both-correct stratum; optional extra no-answer/one-neutral-pair readout deferred to a separate registration to preserve the five-arm/count/cost design. Check 38's reading was fixed by run-time copy/hash, not a prior commit; no false prelaunch anchor. Kimi's four wording fixes in results/focus-synthesis-review-kimi.md: Fix 1 accepted—check 32 presence, not task identity; Fix 2 accepted—retained HOLD 32/32 ascending, 23/32 descending and joint 3/32, 5/32; Fix 3 accepted-with-change per Brian—keep >=5 points over text-restate only, label <5-point component gains MARGINAL ADDED CONTROL and withhold headline joint-control claim; Fix 4 satisfied—check 36 independently reviewed, check 33 review not asserted. Optional Fix 5 remains accepted—later requests cannot recover a failed endpoint. F4/F8 freeze/provenance now bind original anchor 2ea04e9 plus prospective check 39 and this v2; historical check 37's coarse n=32 STOP stands. F6/F9/F11/F12 safety, all other gates, seeds (including the focus2-v1 RNG namespace), families, claim ceiling and freeze sequence (2)–(4) are retained. No finding refuted; independent registration review remains required.

### V3 review dispositions and execution clarifications — 2026-09-05, before outcomes

Brian's combined task authorizes these prospective dispositions. The v2 body above is preserved verbatim except the requested A1–A3 edits and A4 disclosure; these dispositions govern inherited references to v2, its old gates, and its outstanding implementation state. V3 remains a candidate until the required CPU checks pass, real dependencies are verified, the freeze receipt exists, and the separate REGISTERED header/launch receipt are committed. Fit-on: none; evaluation remains the fixed fresh synthetic banks. Reviews and historical check files remain unchanged; these are fix decisions, not a claim that either reviewer re-reviewed the implementation.

- Fable A1 (CRITICAL), accepted: assistant_fact has passes=null and cannot veto safety; report its paired table and source-validity strata as disclosed_cost.assistant_fact alongside primary benefits. Every PASS headline includes “eviction forfeits assistant-authored content it removes (x/64 vs y/64)”, with x/y the both/text-restate failure counts. User_fact/tool_fact/constraint each require complete fixed denominators, exact harm p>.05 AND h-r<=2; unadjusted tests, all binding.
- Fable A2 (HIGH), accepted: F6 uses raw h<=5 and exact harm p>.05, with the sixth final-bank both-only broken episode stopping scheduling. The inherited repair paragraph's F6 “raw h<=2” is superseded by raw h<=5. Check 39's separate net-discordance rule is unchanged. Exact upper bounds: 1.1634% at 0/256 and 4.0626% at 5/256.
- Fable A3 (HIGH), accepted: each of eight skill cells needs >=52/64; each of four default cells still needs >=56/64. Any miss is terminal INELIGIBLE; no retest or family selection.
- Fable A4 (MEDIUM), accepted: the 3-point-gain power disclosure is appended without changing N or the primary Holm family. Its ~0.1–0.2 figure assumes discordance .25–.10 and conservative Holm alpha=.05/3; full joint power is not identified by one contrast.
- Fable A5 (LOW), accepted/disclosed: generate once per delay slot and share across arms (existing DELAY0/1/2 law). Cue retirement inside earlier user turns is an uncertified, arm-shared edit; check 39 certifies the body repair, not that additional edit. Check-39 preregistration e24afd4 at 2026-09-05T08:43:02Z precedes launch 08:43:10Z by eight seconds. Check-38 cost remains 8.02 GPU-min.
- Fable B1 (HIGH) / Astra “Model assets in Git” (MEDIUM), accepted: retain clean Git membership/content for source, readings and registration artifacts. External model/tokenizer/config assets may use a hashed-asset path only when Git ignores them: repository-relative path, non-symlink file, byte size, streaming SHA-256 and source revision in a committed descriptor, tracked=false. Bind and verify small JSON config contents too. No model binary is added to Git; verify assets on CPU before model construction.
- Fable B2 (MEDIUM) / Astra FOCUS2-1 (HIGH), accepted: use Qwen's native user/<tool_response> framing and a minimal frozen <tools> declaration; keep logical tool ownership/scope in metadata. Compare actual renderer call/return token IDs with the pinned local Qwen template, reject the old raw tool-role header, preserve the complete group through interventions.
- Fable B3 (MEDIUM), accepted: the sixth-breakage stop applies only to the final bank. Pilot flags are recorded/disclosed but cannot drive efficacy/safety stopping or sample changes.
- Fable B4 (LOW), disposed: retain once-per-slot delay generation and disclose its full cost; stream external hashes without Git-loading model binaries. Retain atomic durable records. No interrupted-stage resume is registered: stage-to-stage continuation uses verified certificates; resource/cap/interruption ends the attempt INCOMPLETE, preserving partial records/cumulative cost and never regenerating a completed output. No broader retry framework or module refactor.
- Astra FOCUS2-2 (HIGH), accepted using its conservative rule: persist each actual delay response, then require a nonempty visible body and genuinely generated valid terminal before replay. Empty/capped-without-terminal responses cause INVALID before dependent task prefill; resource interruption remains INCOMPLETE. Exclude prohibited histories from the complete-pair law by terminal invalidation of the run, never dropping/redrawing the fixed episode or regenerating a reply. Offline analysis enforces the same predicate. Period acknowledgements and EOS on the cap are allowed; repetitive-delay flags are disclosed without a new threshold. Wrong SET/HOLD answers stay unscreened.
- Astra “Terminal-token repair edge” (MEDIUM), accepted: remove generated endoftext with the retired body, retaining normalized im_end/newline closure and original terminal metadata in raw records/maps. Test EOS/END/capped boundaries against whole-body period repair.
- Astra “Development coverage manifest” (MEDIUM), accepted as a real freeze prerequisite: every checks-31–39/repair label needs nonempty outcome-free fingerprints and per-source input count/hash/source provenance. Empty fabricated coverage cannot freeze. Construct only from deterministic input-generation source or an existing outcome-free manifest, never historical responses/scores, benchmarks or SC1 inputs. If unavailable, stop before freeze.
- Astra “Resume” (MEDIUM), resolved by the explicit one-attempt policy in B4: continue between completed stages only; interrupted stages are INCOMPLETE, never resumed/rerun.
- Astra unnumbered LOW items, accepted: the immutable DRAFT v3 snapshot is promoted by the separate committed registration/launch record. “Compact” is a prompting instruction; score semantic JSON structure/exact values, not whitespace. PASS establishes a relative effect, not absolute reliability; error-only gains retain the error-cleanup reading; no globally optimal reminder claim. No new arm, benchmark stage, prompt search or repair variant.

Implementation closure and freeze verification remain to be evidenced in finding-named CPU tests and the receipt. No real model outcome has been observed in this leg.


## FOCUS-2 REGISTERED (2026-09-05 10:57:09 UTC, commit 8b860952cd190d0ba5aece96f719b50b64726127)

## FOCUS-2b — SORT-ONLY PLACEMENT + EVICTION (DRAFT v1 = REGISTRATION CANDIDATE, 2026-09-05)
Data lineage FIRST — fit-on: none; development: checks 31–39/repair fixtures and the disclosed FOCUS-2 competence diagnosis; evaluated-on: new seeded synthetic sort episodes, disjoint within/across competence, pilot, final and development inputs (including the frozen FOCUS-2 banks). Nothing is fit or trained. No benchmark data; tests/test_sealed_guard.py is the sole permitted sealed-IFEval reader, only for the required guard tests.
STATE: prospective registration candidate under Brian's combined FOCUS-2b task; commit this section before code/freeze and before any new model outcome. FOCUS-2 remains STOPPED/INELIGIBLE at registration 7203294; its outcomes are development evidence, never fresh FOCUS-2b evidence. This section overrides only the explicit differences below; FOCUS-2 DRAFT v3 and its execution clarifications (candidate 1b8216a, freeze 8b86095, registration 7203294) otherwise remain unchanged by reference.

Why this re-registration: results/focus2-competence-diagnosis-fable.md (committed at 7887cce), sections 1, 3, 5–6, identifies an unspecified answer shape in the three new families plus genuine content errors. Sort/descending's 44/64 reflects real ordering errors under -99..99, 4–6 items; check-31/34's smaller-magnitude law yielded 30/32 and 60/64. This association motivates the new law but does not establish causation or predict a guaranteed pass. No rescoring or rescue of FOCUS-2.
Changes vs FOCUS-2 v3:
- SORT ONLY: ascending and descending; retain exact-value/type/schema checking unchanged, including exact integer tag. The other three families are excluded prospectively before this leg's outcomes; no further dropping, substitution or tuning.
- Operand law: rng.sample(range(-20, 21), rng.randint(5, 8)); distinct integers, uniformly random order, reject lists already in ascending or descending form. Semantic unordered-set dedup within/across banks and development is unchanged; any residual collision is INVALID (no redraw/seed search).
- Schema line: 'Output compact JSON of the form {"answer": <JSON array of integers>, "tag": <integer>}; no prose or unrequested keys.' Additional keys remain allowed only when the current request explicitly requests them.
- Default cue: 'Return the payload list unchanged.' at competence/default, CLEAR and NEUTRAL2. Render current request obligations once, including inside any live-rule/placement/recap block; do not duplicate them in that same request. This supersedes inherited default wording only.
- Final N=256 sort episodes: 128 per initial direction; 64 per initial-direction x delay cell (0/512 user-content tokens). SWITCH reverses direction and BACK returns; publish actual A->B and B->A checkpoint directions. Exactly 16/cell (64 total) request the SET assistant memo, preserving its fixed collateral denominator and 25% fraction.
- NEW seeds: competence 9053712, pilot 9053713, final 9053714. SHA-256-derived RNG namespace/stream construction focus2-v1 and request/purpose separation unchanged. Freeze once; never search seeds.
- Competence: 64 immediate visible-cue fixtures per sort direction and 64 fresh default fixtures (192 total). Require >=52/64 for ascending AND >=52/64 for descending, and >=56/64 default. Report each cell; any miss is terminal INELIGIBLE, no retest or prompt/operand edits after outcomes.
- Timing pilot: one episode per family/direction/delay cell now means four disjoint sort episodes, all five arms. Timing only; project all 256 remaining episodes at worst measured cell cost plus 25% reserve, including loads and prior spent time. STOP if spent+projection does not fit 6 GPU-h.

Carried forward from FOCUS-2 v3, unchanged:
- Five arms/order, inside-request placement, shared unscreened SET/PREHOLD responses, oracle event/scope map, interventions at SWITCH/BACK/CLEAR, no refresh at HOLD/NEUTRAL2 except text-restate; no extra arm.
- Exact anti-imitation text-restate template, SHA-256 2658b026d6bd22d4ed460b34c543abc159e4e80ff56f367be4eaf5c035f8e8d7, original v1/readings anchor 2ea04e9. Bind the inherited v3 section/readings separately alongside this immutable section; template slots receive the revised schema/default and single obligations rendering.
- Check-39 PROCEED_PLACEHOLDER receipt at e30343d and prospective e24afd4 anchor; whole retired assistant body becomes token 13 period, preserving closures; complete user+assistant/tool pairs, native Qwen tool framing, contiguous text re-prefill from empty KV, saved token maps. Check-37 STOP remains historical, not pooled.
- Frozen Qwen3-4B bf16/hf_compatible, greedy, thinking disabled, <=64 generated tokens; exact-value checker, all-five Y endpoint, separate collateral endpoints, fixed denominators, raw records before aggregation, independent CPU renderer/checker verification and dependency receipts.
- Primary: both vs placement-only, eviction-only and text-restate; exact one-sided McNemar, three-test Holm .05, positive differences and >=5 points over text-restate (>=13 net episodes/256). Significant component gains <5 points mean MARGINAL ADDED CONTROL, no headline joint-control claim. Paired tables/intervals and the inherited low-power disclosure unchanged.
- Secondary: observed placement-only >= text-restate and eviction-only vs neither, descriptive paired tests/intervals, no equivalence or primary rescue. F11 both-correct versus prior-error strata, per-direction/default impositions, checkpoint/delay breakdowns unchanged.
- F6: both-only breakage h<=5/256 and harm p>.05; sixth final-bank both-only break stops scheduling, FAIL-SAFETY with incomplete denominators. Pilot outcomes do not change sampling/gates. User/tool facts and unchanged constraint require harm p>.05 and net harm h-r<=2, all binding.
- Assistant-fact failures (n=64), source-validity strata and paired harm are disclosed beside primary benefit, not gated. Any PASS must say 'eviction forfeits assistant-authored content it removes (x/64 vs y/64)'.
- Prewritten readings/claim ceiling unchanged: a failed placement/text contrast means no demonstrated extra mechanism, not equivalence/absence; wrong-prior-only benefit means error cleanup; repair/release fragility or unsafe context management is not promoted. Oracle synthetic context management on a frozen trunk; no compact-state, waves, autonomous-change or benchmark-transfer claim.
- HARD 6 GPU-h includes loads, competence, pilot, final and delays; prior FOCUS-2 competence (0.289918 GPU-h) and checks37/38/39 (14.715/8.02/16.591 GPU-min) are separately disclosed development, not rerun. Cooperative budget checks; foreground only; no timeout signals, termination or background launch.
- Commit candidate, CPU code/tests, immutable freeze, then separate REGISTERED header/launch receipt before GPU; verify committed membership/hashes and ignored external asset descriptors as before. Stage-to-stage continuation only with verified certificates. Interrupted stages are terminal INCOMPLETE; never regenerate a completed output. Hash/protocol drift INVALID; no rescue.
Execution: required CUDA-disabled tests/test_focus2.py, tests/test_eval_data_separation.py, tests/test_sealed_guard.py and tests/test_no_side_effect_imports.py plus ruff clean; then freeze/register -> idle-GPU competence -> timing pilot/projection -> 256 x five-arm run -> analyze -> registered OUTCOME/WORKLOG and force-add results/qwen/focus2b/**. Each step is committed with explicit pathspecs, no push. Any failed step stops with a WORKLOG reason. No SC1/check-file edits or process signals.

## FOCUS-2b AMENDMENT 1 (2026-09-05) — collision rejection at generation
Data lineage FIRST — fit-on: none; input-only exclusions from checks 31–39/repair, frozen FOCUS-2 banks, and FOCUS-2b competence/pilot inputs; evaluated-on: fresh synthetic FOCUS-2b banks, disjoint from these exclusions and one another. No model outcome informs this amendment; FOCUS-2b has consumed zero GPU-seconds. Nothing fit or trained; no benchmark data outside the sole permitted sealed-guard test.
Brian's prospective orchestrator decision supersedes only the candidate's residual-collision/no-redraw rule and seeds. The freeze stopped INVALID at f366b05 on final:sort:descending:0:27 BACK [-20,9,17,6,-5], fingerprint f86ae56099ff0e4830019faeb822cd962413cc7b395ef4f259ae3de33228a824, matching check 34; this is input identity, not outcome evidence. Original candidate d6d7be9 and stop receipt remain preserved.
Generate in competence, pilot, final order with the existing family/direction/delay/index/request order. Reject any payload whose semantic fingerprint matches ANY development/competence/pilot input (checks 31–39, FOCUS-2, FOCUS-2b competence/pilot) or any earlier payload in the same or another FOCUS-2b bank. For conservative coverage, include all retired unrun FOCUS-2b candidate inputs as exclusions, as well as all frozen FOCUS-2 inputs. Retired banks are input-only development evidence, never model runs.
For each request, initialize its existing focus2-v1 payload RNG once; attempt 0 is the original draw. On collision, record the rejected payload, fingerprint, zero-based attempt and prior source/episode/request; increment the counter and draw again from that same RNG stream until accepted. Preserve the existing sorted-form rejection law. Store accepted attempt counts and every semantic rejection in the frozen bank; verify them by deterministic regeneration against the frozen outcome-free exclusion manifest. No seed search, prompt change or outcome screening.
NEW fixed seeds: competence 9053715, pilot 9053716, final 9053717. Seeds 9053712/9053713/9053714 from d6d7be9 are retired unrun. Nothing else changes: FOCUS-2b candidate and inherited FOCUS-2 v3 gates, templates, five arms, exact checker, counts, readings, cost cap, one-attempt execution and stop rules are unchanged.
STATE: amendment recorded before code, freeze or any FOCUS-2b outcome. Next step 2': implement and test the exact f86ae560 collision rejection/resampling and within/across-bank uniqueness; run the four-file CUDA-disabled acceptance including tests/test_sealed_guard.py (the ONE permitted sealed reader), plus ruff. Then commit; step 3 freeze and REGISTERED/launch receipt; step 4 idle-GPU competence -> pilot/projection -> run -> analyze; step 5 OUTCOME/WORKLOG and force-add results/qwen/focus2b/**. Foreground only, never signal/terminate processes, no SC1/check edits, no push; any failed required step stops with WORKLOG evidence.

## FOCUS-2b REGISTERED (2026-09-05 11:53:58 UTC, f1d32f1028d3da2553758ea32a8cd498d2e08d3b)

## FOCUS-2c — PAYLOAD RENDERING FIX (DRAFT v1 = REGISTRATION CANDIDATE, 2026-09-05)
Data lineage FIRST — fit-on: none; development: checks 31–39/repair, frozen FOCUS-2/FOCUS-2b inputs and the disclosed FOCUS-2b competence diagnosis; evaluated-on: fresh seeded synthetic FOCUS-2c sort banks, disjoint from development and within/across competence, pilot and final. Nothing fit or trained; no benchmark data. tests/test_sealed_guard.py remains the ONE permitted sealed-IFEval reader, solely for required guard tests.
STATE: prospective candidate under Brian's FOCUS-2c instruction; commit before implementation, freeze or new model outcomes. FOCUS-2b Amendment 1 remains STOPPED/INELIGIBLE (ascending 56/64, descending 48/64, default 64/64; registration 2c18cda); none of its outcomes is reused as FOCUS-2c evidence.
Single experimental change: render ONLY the input payload in 'Process this payload: {payload}' using json.dumps with its default spaced separators (', ', ': '), e.g. '[19, -17, 13, -2, 5]'. Keep compact canonical hashing/artifact serialization and generated-answer instructions unchanged. Re-freeze every rendered string/token map because input tokens change.
Evidence: results/focus2b-competence-diagnosis-fable.md, sections 1–4/6, classifies all 16 descending failures as genuine late-list slips concentrated on negatives. Its pooled historical spaced/bare frame is 270/288 versus compact/wrapper 92/128 (reported p≈5e-9); compact negatives merge into the ',-' token. Frame differences also include wrapper/system wording, so these observations motivate spacing but do not isolate its causal effect. The diagnosis estimates P(clear 52/64)≈0.66; this is development guidance, not a new gate or efficacy claim.
NEW fixed seeds: competence 9053718, pilot 9053719, final 9053720; no seed search. Keep the focus2-v1 request RNG namespace, generation order, same-stream collision rejection and full attempt/rejection logs unchanged from FOCUS-2b Amendment 1. Conservatively exclude ALL frozen FOCUS-2b Amendment 1 inputs as well as its prior exclusions; retired and unrun inputs remain input-only development, never reused outcomes.
Everything else is unchanged from FOCUS-2b Amendment 1 (candidate d6d7be9, amendment 673876c, implementation 87dbf3d, freeze f1d32f1), including its inherited FOCUS-2 v3 and execution clarifications:
- SORT ONLY; -20..20, 5–8 distinct operands, reject either sorted form; schema/wrapper, exact integer tag, system/default cues and once-rendered obligations unchanged.
- 192 competence fixtures: >=52/64 ascending AND >=52/64 descending AND >=56/64 default; any miss is terminal INELIGIBLE. No retest, rescue or wrapper change; the orchestrator alone decides on any later FOCUS-2d.
- Four disjoint timing-pilot episodes, then N=256 sort episodes balanced by initial direction and 0/512-token delay, 64 assistant-memo episodes; all five arms, shared unscreened priors, exact hashed text-restate template, check-39 placeholder repair, complete pairs, contiguous re-prefill and exact checker unchanged.
- All-five Y, three exact McNemar/Holm comparisons, >=5 points over text-restate, secondary readings, F11 strata, F6 h<=5 (sixth final-bank both-only break stops), user/tool/constraint gates and ungated disclosed assistant-fact cost unchanged.
- HARD 6 GPU-h, worst-pilot projection plus 25% reserve, cooperative budget checks, one attempt/no interrupted-stage resume, no completed-output regeneration, original readings/claim ceiling unchanged. Earlier FOCUS-2b competence cost 0.096616 GPU-h is separately disclosed development alongside earlier costs, never pooled.
Execution: commit candidate; minimal rendering/registration changes and token-map regression including ', -' tokenization; required CUDA-disabled four-file acceptance (test_focus2, test_eval_data_separation, test_sealed_guard, test_no_side_effect_imports) and ruff; commit code; CPU freeze and receipts; commit freeze then separate REGISTERED/header/launch receipt before idle-GPU competence -> pilot/projection -> run -> analyze. Mechanical stop rules; on any failed required step stop and record why. Append FOCUS-2c OUTCOME and WORKLOG, force-add results/qwen/focus2c/**, explicit-path commits, no push. Foreground only; never signal/terminate any process; no SC1/check-file edits.

## FOCUS-2c OUTCOME (2026-09-05)
Data lineage — fit-on: none; no new model outcome. STATE: STOPPED AT STEP 2 CPU ACCEPTANCE; candidate 0c8e2ff remains unregistered. The required four-file CUDA-disabled suite exited 1: 90 passed, 1 failed, 1 expected legacy import-inventory xfail, one existing SyntaxWarning, 191.94 seconds. tests/test_focus2.py::test_competence_prompt_is_immediate still asserts compact canonical payload text occurs in the prompt; it expected '[7,13,-20,-19,2]' while the newly spaced renderer emitted '[7, 13, -20, -19, 2]'. This missed test update is an implementation error, not a model competence failure. The new actual-renderer/frozen-token-map regression passed; Ruff passed.
Brian's explicit failed-step stop rule is applied: preserve the attempted implementation and acceptance evidence; no failed-test correction/retest, freeze, REGISTERED header/launch receipt, competence, pilot, final run or analyze. FOCUS-2c consumed 0 GPU-seconds. The input-only exclusion manifest covers 9,630 unique fingerprints, including all 2,012 frozen FOCUS-2b Amendment 1 inputs; no FOCUS-2c bank was frozen or response reused. Artifacts: results/qwen/focus2c/stop-at-cpu/{acceptance.txt,ruff.txt,failure.json} and development/manifest.json.
Registered readings: competence, primary contrasts, secondary readings, F11 strata, breakage/collateral gates and assistant-fact cost are all unmeasured. No efficacy or absence claim is available. Plain language: the spaced rendering was implemented, but the CPU acceptance suite caught a stale test expectation before registration. The experiment did not run. This stop provides no evidence about whether spacing improves competence or whether placement plus eviction helps; FOCUS-2d's competence-failure contingency has not been reached.


## FOCUS-2c REGISTERED (2026-09-05 12:26:25 UTC, 60bfbc8df46a3e839d569d7fe7d35ea45c05e20b)

Brian's 2026-09-05 resume ruling supersedes the earlier CPU stop: the stale compact-payload expectation was updated, all other assertions retained, and required CPU acceptance passed before this registration. The original candidate and previous stop record remain preserved. No FOCUS-2c model outcome precedes this header.

## FOCUS-2c OUTCOME (2026-09-05)

Data lineage FIRST — fit-on: none; evaluated-on: the fresh registered synthetic FOCUS-2c competence bank and attempted timing-pilot prefix only, disjoint from frozen development inputs. No fitting/training, reused FOCUS-2b outcomes or benchmark data beyond the sole authorized sealed-guard acceptance test. This is the terminal outcome of Brian's authorized resume; the earlier CPU-stop outcome remains historical.
STATE: STOPPED / INVALID at step 4 timing pilot. Step 2 accepted at ef09567 (91 passed, 1 expected xfail, 1 existing warning; ruff clean); freeze 60bfbc8df46a3e839d569d7fe7d35ea45c05e20b; registration f965a4d at 2026-09-05 12:26:25 UTC; raw-stage artifacts and audits committed at dbff9b8. The single spaced-payload change, fresh seeds, token maps, immutable inputs, wrapper, checker, gates and one-attempt law stayed frozen.

| Competence cell | Success / 64 | Required | Gate |
|---|---:|---:|---|
| sort/ascending | 63 | 52 | PASS |
| sort/descending | 59 | 52 | PASS |
| sort/default | 64 | 56 | PASS |

Competence CLI exited 0 / COMPLETE, with every one of the 192 atomic record hashes, input/rendering/checker reconstructions, start/end receipts, allocation accounting and the exact PASS certificate verified on CPU. Record-set SHA-256 35d4f466d2dddc8f91812447685930a4d04d19cccaaa8b009d4aa6463be73f61. This establishes competence eligibility for this bank; comparison with older seed banks does not isolate a causal spacing effect.
Timing pilot CLI exited 1 / INVALID after 28 retained records: all 27 requests of pilot:sort:ascending:0:0, then shared DELAY0 of pilot:sort:ascending:512:0. That neutral delay response was nonempty but reached the fixed 64-token cap with eos=null. The registered validator requires a nonempty body AND a generated terminal, so it stopped before replay: "invalid delay: complete pair needs nonempty body and generated terminal; no replay/retry". Generation-loop complete=true at the cap is not a valid complete pair. CPU audit verifies all retained hashes/bindings/costs, validates the first episode's renderer/checker/intervention reconstruction, and reproduces the same terminal INVALID on the whole pilot. No passing pilot certificate or completed four-cell timing projection exists. This is a substantive delay-validity failure, not a competence miss or a six-hour budget failure.
Mechanical stop: no retry, injected terminal, altered generation cap, prompt/seed/arm change, interrupted-stage resume or completed-output regeneration; final 256 x five-arm run and analyze were not invoked. FOCUS-2d's competence-failure contingency was not reached; no successor experiment is launched here.
Registered readings: primary all-five Y contrasts/McNemar/Holm/magnitude, secondary placement-only >= text-restate and eviction-only vs neither, F11 both-correct/prior-error strata, final breakage/collateral gates, directional/checkpoint breakdowns and assistant-fact cost are all unmeasured on the final bank. Pilot responses are retained timing-stage evidence and supply no efficacy, absence, mechanism or safety claim; they are not pooled or promoted into final denominators.
Cost: competence 372.4416761128232 seconds (load 33.17676198389381), pilot 94.6389293950051 seconds (load 31.85609860601835), total 467.0806055078283 seconds = 7.784677 GPU-min = 0.129745 GPU-h of the 6-hour cap. Prior FOCUS-2 0.289918 GPU-h, FOCUS-2b 0.096616 GPU-h and checks37/38/39 14.715/8.02/16.591 GPU-min remain separately disclosed development, not pooled.
Artifacts: results/qwen/focus2c/{freeze/,launch-receipt.json,outputs/competence/,outputs/pilot/,competence-audit.json,pilot-audit.json,*-console.txt}; prior CPU-stop receipts preserved. All 252 files under results/qwen/focus2c were force-added and verified by git ls-files and exact committed byte equality at dbff9b8. No push.
Plain language: the spaced-payload setup cleared all three competence checks. The timing pilot then produced a delay response that ran out of allowed tokens before ending, and the registered rules required stopping. The main experiment did not run, so this result does not show whether placement plus eviction helps. The complete competence result and the invalid pilot prefix are preserved for review without a rescue run.

## FOCUS-2c AMENDMENT 1 (2026-09-05) — delay turn law

Data lineage FIRST — fit-on: none; evaluated-on: the unchanged seeded synthetic FOCUS-2c banks, disjoint from development. No fitting/training or benchmark data. Disclosure: competence and the stopped timing-pilot prefix were observed (OUTCOME ac3cae1); only pilot delay outputs informed this harness amendment, and no final-bank outcome exists. Brian's explicit dated orchestrator ruling authorizes this amendment before any final-bank outcome.
(a) Neutral delay prompts explicitly request a short reply: "Answer in one sentence." Delay generation cap is 160 tokens. Preserve exactly 512 user-content tokenizer tokens by shortening only the neutral padding; freeze the exact amended prompt and token maps.
(b) A delay answer reaching that cap without a generated terminal is regenerated exactly once, greedily/deterministically from the identical isolated prompt and empty cache, at cap 320. Persist both attempts separately with caps, token IDs, terminal, provenance and costs. EOS on either cap is valid. If the second attempt still lacks a terminal, mark the entire episode delay-invalid, exclude it from ALL readings across all arms, and report its identity/count and the resulting denominators; never silently drop it. Empty terminal answers remain INVALID under the unchanged complete-pair predicate. Resource interruption remains INCOMPLETE, not a retry/exclusion.
(c) All other clauses are unchanged from FOCUS-2c / FOCUS-2b Amendment 1 / FOCUS-2 v3. Task responses retain cap 64. Final-bank seed 9053720 and all payloads, tags, facts, memo assignments, directions and delay assignments are unchanged; only delay prompt text changes. Re-freeze all token maps/dependencies and append a new REGISTERED header and launch receipt. No final-bank output has been generated.
The competence certificate STANDS: ascending 63/64, descending 59/64, default 64/64. Competence prompts contain no delay turn and are unchanged. Bind and revalidate the original raw records/certificate on CPU; do NOT rerun competence. Preserve the old freeze and stopped pilot records. Reuse already completed, unchanged pilot task outputs with explicit provenance; never regenerate a completed task output. The amended capped delay is the explicit retry exception.
Operational interpretation before outcomes: exclusion is paired at episode level; eligible n replaces the reading denominator (including memo subset), >=5 percentage points remains the magnitude bar, raw F6 h<=5 and collateral net h-r<=2 remain unchanged. Completion requires all 256 scheduled episodes either fully scored or explicitly delay-invalid. A timing pilot with a delay-invalid cell cannot certify the full-cell cost projection and stops before the final run; no substitute pilot cell. Count the previous 467.0806055078283 GPU-seconds plus all new loads/generations/retries against the SAME 21,600-second cap. Stop rules otherwise mechanical, including the sixth final-bank both-only broken episode; no interrupted-stage resume.
Execution: commit this amendment; implement/test the delay law and carry-forward consumers; required four-file CPU acceptance including the ONE authorized sealed reader tests/test_sealed_guard.py, plus ruff; commit code; re-freeze/commit then REGISTERED/launch-receipt commit; verify idle GPU; foreground pilot -> projection -> run -> analyze; OUTCOME/WORKLOG and force-add results/qwen/focus2c/**. No push, signals, termination, background jobs, SC1/check edits or new benchmark contact.


## FOCUS-2c REGISTERED (2026-09-05 12:54:50 UTC, 658622149ea6589f5ea68e2d9f07921f0899a3b8) — AMENDMENT 1

Delay-law amendment 14f63cc is implemented and CPU-accepted at a09e876; re-freeze manifest e97c205bc54e889605ff7b9e2e9f2faf6bfbe4e4d25f11c60ff8165b0ea5bb87. Original competence certificate stands (63/59/64), CPU revalidated without model execution. All final input content is unchanged except the frozen delay prompt; no final outcome exists before this header. The old pilot prefix and 467.0806055078283 seconds are bound into the carry receipt; 27 completed unchanged responses will be reused. Sole new output directory: results/qwen/focus2c/amendment1/outputs. New pilot launch follows this separate registration commit and idle-GPU verification.

## FOCUS-2c OUTCOME (2026-09-05) — AMENDMENT 1

Data lineage FIRST — fit-on: none; evaluated-on: the unchanged seeded synthetic FOCUS-2c banks and the amended timing-pilot prefix, disjoint from development. Nothing fit/trained; no benchmark contact beyond the sole authorized sealed-guard acceptance test. Prior competence and pilot observations were disclosed prospectively in Amendment 1; no final-bank outcome was generated. Historical OUTCOME entries remain preserved.
STATE: STOPPED / INCOMPLETE at the mechanical timing-pilot cost gate. Amendment 14f63cc; implementation/CPU acceptance a09e876; re-freeze 658622149ea6589f5ea68e2d9f07921f0899a3b8; registration 224b625 at 2026-09-05 12:54:50 UTC; terminal raw artifacts/audit 5a14f4f5ff79f6485e460a886c137e4ec7f6dc0f. Four-file acceptance: 97 passed, 1 expected xfail, 1 existing SyntaxWarning; ruff clean. All bank content and task generation remain unchanged; only the 512-token delay template and its 160/320 cap/retry/exclusion law changed. Re-frozen token maps and manifest e97c205bc54e889605ff7b9e2e9f2faf6bfbe4e4d25f11c60ff8165b0ea5bb87 are committed.

| Standing competence cell | Success / 64 | Required | Gate |
|---|---:|---:|---|
| sort/ascending | 63 | 52 | PASS |
| sort/descending | 59 | 52 | PASS |
| sort/default | 64 | 56 | PASS |

The competence certificate STANDS and was NOT rerun: competence prompts contain no delay turn. All 192 original records, unchanged prompts/checker/model bindings and exact certificate were CPU-revalidated. The completed no-delay pilot episode's 27 responses were carried with original-record hashes and verified inputs; no completed task response was regenerated, and their old allocation was charged exactly once.
Amended pilot CLI exited 1 / INCOMPLETE with 'GPU allocation budget exhausted/projected over cap' after 2/4 cells: ascending/0 carried and ascending/512 generated. It retained 57 records (27 carried, 30 new). All three new delay replies had five body tokens and generated im_end (151645), using cap 160; each complete rendered pair measured 531 tokens. Delay retries: 0. Delay-invalid exclusions: 0. Two descending pilot cells were not scheduled. The new delay law produced complete pairs in this observed prefix; its exhausted-retry/exclusion path was exercised on CPU fixtures, not claimed observed on the GPU.
Budget stop verified independently from durable timestamps: the new cell took at least 74.60514306696132 seconds. The registered worst-cell projection with 25% reserve gives at least 23,910.23040093889 seconds for 256 final episodes plus the next load; adding cumulative time at the last request yields at least 24,481.54566539952 seconds = 6.800429351499867 GPU-h, already above the 6-hour cap before the two remaining pilot cells. Including those cells yields a 24,668.058523066924-second lower bound. The exact in-memory scheduler projection was not serialized; these lower bounds omit initial rendering/final publication and independently establish the same mandatory stop. No complete four-cell pilot certificate exists.
Actual cost: prior competence+stopped pilot 467.0806055078283 seconds; amended pilot 104.40992534789257 seconds including load 29.26769560901448; cumulative 571.4905308557209 seconds = 9.524842 GPU-min = 0.158747 GPU-h. The stop is a projected-cost refusal, not an actual six-hour overrun. Prior FOCUS-2 0.289918 GPU-h, FOCUS-2b 0.096616 GPU-h and checks37/38/39 14.715/8.02/16.591 GPU-min remain separately disclosed development, not pooled.
Registered final readings — primary all-five Y contrasts/McNemar/Holm/magnitude, secondary placement-only >= text-restate and eviction-only vs neither, F11 both-correct/prior-error strata, final breakage/collateral gates, directional/checkpoint breakdowns and assistant-fact cost — are unmeasured. The final 256 x five-arm run and analyze were NOT invoked. Pilot records are timing-stage evidence and do not estimate final efficacy/safety or assistant-fact cost. No rescue, additional pilot sample, cap increase, run resumption, competence retest or completed-output regeneration occurred.
Artifacts: results/qwen/focus2c/amendment1/{freeze/,launch-receipt.json,outputs/pilot/,pilot-audit.json,pilot-audit.py.txt,*-console.txt}; all older FOCUS-2c artifacts preserved. All 333 files under results/qwen/focus2c were force-added and verified against exact committed bytes at 5a14f4f. The audit verifies every retained record's hash/identity/binding, exact renderer/checker/intervention reconstruction, original carry provenance and additive cost accounting. GPU returned cooperatively with no compute processes; no signals, termination, background jobs, SC1/check edits or push.
Plain language: the amended short delay replies ended normally, and the previous competence pass remains valid. The measured pilot cost nevertheless put the registered full experiment above its six-hour budget. The harness therefore stopped before the main experiment, so placement plus eviction has no final efficacy or safety result from this attempt.


## FOCUS-2c AMENDMENT 2 (2026-09-05) — cost cap

Data lineage FIRST — fit-on: none; evaluated-on: the unchanged, frozen synthetic FOCUS-2c final bank, disjoint from development. Nothing fit or trained; no benchmark data. Disclosure: standing competence and Amendment 1's stopped timing-pilot prefix were observed; no final-bank outcome exists. Brian's dated orchestrator ruling explicitly authorizes this cost-only amendment before final outcomes; the original synthesis allocated 10 + 2 GPU-h for this stage.
The cap becomes 8 GPU-h (28,800 seconds) for final run + analyze, with the same worst-cell projection + 25% reserve and cooperative halt-and-preserve behavior. Prior FOCUS-2c cost (571.4905308557209 seconds) remains disclosed and, conservatively, continues to count against the cap. N=256, five arms, endpoints, decision rule, safety, banks, seeds (9053718/9053719/9053720), prompts, token maps, freeze and every science clause remain unchanged.
The authorizing measurement is Amendment 1's committed timing audit (5a14f4f): cumulative-plus-final projection >=24,481.54566539952 seconds = 6.800429351499867 GPU-h. It is a lower bound from durable timestamps, not a complete four-cell pilot certificate; the exact scheduler projection was not serialized. Brian authorizes this measurement directly; no new pilot or completion of the two unscheduled pilot cells. Competence stands at ascending 63/64, descending 59/64, default 64/64; no generation or retest.
Operational interpretation, fixed before final outcomes: retain the scientific freeze at 658622149ea6589f5ea68e2d9f07921f0899a3b8 and its immutable output path. A separately committed and hash-bound cost adapter verifies that freeze and all standing competence/pilot evidence, supplies only the amended cap and pilot authorization, and calls the unchanged final scheduler/analyzer. For conservative scheduling, use the entire amended pilot's non-load allocation (104.40992534789257 - 29.26769560901448 = 75.14222973887809 seconds) as the worst-cell upper bound; it includes both completed cells and publication/unload, thus exceeds the audited 74.60514306696132-second cell lower bound. Apply the unchanged 1.25 * (256 * worst_cell + next_load_estimate) projection. The adapter and launch receipt bind this operational choice without rewriting the frozen scientific sources/configuration or fabricating a passing pilot certificate.
Resume remains the registered one-attempt rule: continue to the unstarted final stage; never resume an interrupted stage, regenerate completed output, change a science clause, or retry a failed required step. The sixth final both-only broken episode stops scheduling. No process signals, termination, background launch, SC1/check edits, delegation or push.
STATE: Amendment 2 write-ahead recorded before adapter implementation, re-registration, launch or any final-bank outcome. Next: CPU-check the cost adapter, commit it with explicit pathspecs; append REGISTERED — AMENDMENT 2 and committed launch receipt; verify idle GPU/no compute process; foreground final run -> analyze only if permitted by the mechanical terminal rule; preserve raw records and append OUTCOME — AMENDMENT 2 plus WORKLOG, force-add results/qwen/focus2c/**. Protected concurrent files results/focus3-design-astra.md and data/classifier/LABELS-RELATIONS.md are outside scope.


## FOCUS-2c REGISTERED — AMENDMENT 2 (2026-09-05 13:15:19 UTC, 2e22e274b443513f05a8cb30a037243465b9c15e)

Amendment commit 129386f; cost-adapter/CPU acceptance commit 2e22e274b443513f05a8cb30a037243465b9c15e; scientific freeze remains 658622149ea6589f5ea68e2d9f07921f0899a3b8, manifest SHA-256 e97c205bc54e889605ff7b9e2e9f2faf6bfbe4e4d25f11c60ff8165b0ea5bb87. All frozen sources/config/assets/banks/token maps and standing original competence certificate CPU-reverified; competence remains 63/59/64. The 57 amended-pilot records, their start/end receipts and committed timing audit at 5a14f4f5ff79f6485e460a886c137e4ec7f6dc0f were hash-verified and renderer/checker-replayed. No competence or pilot rerun and no final-bank outcome exists.
Launch receipt: results/qwen/focus2c/amendment2/launch-receipt.json; it binds the adapter, amendment snapshot, CPU acceptance, frozen output path results/qwen/focus2c/amendment1/outputs and all historical timing records. Authorizing lower-bound projection 24481.54566539952 seconds; conservative worst-cell bound 75.14222973887809 seconds gives final+load+25% reserve 24082.098135952256 seconds, plus prior 571.4905308557209 = 24653.588666807977 seconds (6.848219074113326 GPU-h), below 28,800 seconds. The eight-hour cost override and timing authorization are separately hash-bound in each new record; the science binding is unchanged.
Next: commit this header/receipt, validate it through the adapter, verify idle GPU with no compute processes, then foreground `uv run python scripts/focus2_amendment2.py --mode run --receipt results/qwen/focus2c/amendment2/launch-receipt.json`. Console results/qwen/focus2c/amendment2/run-console.txt. On permitted completion run the same command with `--mode analyze`, persist analysis.json, and append OUTCOME. Same mechanical stop/resume rules; no process signals, background launch or push.


## FOCUS-2c OUTCOME — AMENDMENT 2

2026-09-05. Data lineage FIRST — fit-on: none; evaluated-on: the unchanged registered synthetic FOCUS-2c final bank, disjoint from frozen development. No fitting/training or benchmark data beyond the sole authorized sealed-guard CPU test. Standing competence and amended-pilot observations were disclosed before the cost amendment; no final outcome preceded Amendment 2 or its re-registration. All historical stops remain preserved.

STATE: **FAIL-SAFETY**, mechanical stop after **11/256 final episodes** (55 observed arm-episodes), all ascending-initial-direction with zero delay. The sixth both-only broken episode occurred at final:sort:ascending:0:10; the other 245 episodes were never scheduled. All 297 generated request records are complete, paired, immutable and retained. The scheduler returned cooperatively (registered CLI exit 0 for FAIL-SAFETY); CPU analyze also exited 0 and retained the scientific FAIL-SAFETY terminal, complete=false. No GPU-stage continuation, interrupted-stage resume, retest, output regeneration or rescue.

Provenance: cost amendment 129386f; tested operational adapter 2e22e274b443513f05a8cb30a037243465b9c15e; re-registration/header/receipt cd7d1f1 at 2026-09-05 13:15:19 UTC. Scientific freeze remains 658622149ea6589f5ea68e2d9f07921f0899a3b8, manifest SHA-256 e97c205bc54e889605ff7b9e2e9f2faf6bfbe4e4d25f11c60ff8165b0ea5bb87. Banks, seeds, token maps, templates, task cap, arms, checker, endpoints, safety and decisions are unchanged. Each new record also binds cost-amendment receipt SHA-256 5689899f37423fac9abc2cc443e8099820f2d04de7fad890cbf20e57cb9cd464. Original competence was CPU-verified without generation: ascending 63/64, descending 59/64, default 64/64 PASS. No new pilot: the two-cell Amendment 1 prefix remains historical INCOMPLETE, directly authorized as timing evidence by Brian's ruling, not relabeled a complete passing pilot.

CPU acceptance: exact four required CUDA-disabled files plus the cost-adapter test file, 100 passed and 1 expected legacy import-inventory xfail (1 existing SyntaxWarning), 198.83 seconds; Ruff clean. The adapter preserves the frozen scientific source/configuration and only supplies the explicitly authorized cap/timing preflight to the unchanged scheduler/analyzer. It tested the actual budget, sixth-breakage stop and existing-output refusal. Full frozen asset/source/token-map/competence/pilot verification preceded the launch; the analyzer revalidated raw hashes, pairing, exact rendering/checking and intervention maps. The independent terminal audit confirms the first-11 prefix, complete 27-record episodes, additive cost and the exact first crossing of h=6.

Registered readings below are **descriptive on the safety-stopped n=11 prefix**, not a completed or balanced final matrix. Fixed denominators remain 256 (assistant-memo 64; each initial direction 128); unobserved episodes are not imputed. Paired tests and asymptotic intervals are nominal prefix outputs, not full-N efficacy evidence. The full-denominator upper-h bound is unavailable.

- F6: both has a broken response in 11/11 episodes, text-restate in 5/11; paired [[5,6],[0,0]], h=6, r=0, exact harm p=.015625. The raw h<=5 cap fails irreversibly. The six both-only identities are final:sort:ascending:0:{0,2,3,7,8,10}. Both NEUTRAL2 is schema-invalid in 11/11: all 11 replies are valid JSON objects missing the required tag, with no truncation, empty body, repetitive flag or period placeholder. Both HOLD is schema-invalid in 7/11. These describe measured breakage; no new repair or causal identification is claimed.
- Primary all-five successes: neither 0/11, placement-only 1/11, eviction-only 1/11, both 0/11, text-restate 3/11. Both versus placement-only and eviction-only each has b=0,c=1, delta=-9.09 percentage points, exact p=1 and Holm p=1, nominal paired-score 95% interval [-37.74,19.15] points. Both versus text-restate has b=0,c=3, delta=-27.27 points, exact/Holm p=1, interval [-56.56,5.67] points. No primary pass, >=5-point gain or added-control claim; incomplete coverage precludes the registered full-matrix efficacy conclusion.
- Binding collateral: user-fact, tool-fact and unchanged-constraint failures are each both 11/11 versus text-restate 2/11, h=9,r=0,p=.001953125. All remain nonpassing with incomplete registered denominators. Assistant-fact failures are disclosed, not gated: both 11/11 versus text-restate 10/11, h=1,r=0,p=.5 (fixed n=64). Shared source-validity: 10 missing/invalid memo sources, failures 10/10 versus 10/10; one valid source, failures 1/1 versus 0/1. No statement of 64 observed memo episodes.
- Fixed secondary placement-only >= text-restate: observed false, 1/11 versus 3/11, b=0,c=2, delta=-18.18 points, p=1, nominal interval [-47.70,12.41] points. Eviction-only versus neither: 1/11 versus 0/11, b=1,c=0, delta=+9.09 points, p=.5, interval [-19.15,37.74] points. Descriptive only; neither rescues safety or establishes equivalence/noninferiority.
- F11: both-correct prior stratum n=9 has both/placement-only/eviction-only/text-restate all-five successes 0/1/1/3; prior-error stratum n=2 has 0/0/0/0. Both-minus-placement is -11.11 points versus 0 points in those strata, both p=1. No observed positive stale-correct or error-cleanup gain is established. Descending-initial-direction and 512-token-delay final cells were not reached; no cross-cell generalization.
- SWITCH/HOLD/BACK/CLEAR/NEUTRAL2 success counts, each out of observed 11: neither 6/8/8/0/0; placement-only 9/7/10/11/1; eviction-only 4/8/7/11/8; both 5/1/9/11/0; text-restate 10/11/9/9/6. Default-copy impositions at CLEAR/NEUTRAL2: neither 0/0, placement-only 11/1, eviction-only 11/10, both 11/0, text-restate 9/9; exact ascending/descending/default imposition and checkpoint flag tables are in analysis.json. CLEAR gains cannot recover later failures. Final delay attempts/retries/exclusions are all zero because the stop precedes every delay cell; amended-pilot delay observations stand separately.

Cost: the authorizing prior-audit cumulative-plus-final projection remains >=24,481.54566539952 seconds. The fixed conservative pilot non-load upper bound 75.14222973887809 seconds gave 24,653.588666807977 seconds = 6.848219074113326 hours including prior spend and the unchanged 25% reserve, below 8. Actual final allocation was 700.8917182099539 seconds (load 33.641167658846825); prior FOCUS-2c allocation 571.4905308557209 seconds; cumulative GPU allocation 1272.3822490656748 seconds = 0.3534395136293541 GPU-h. CPU analysis 9.068784174043685 seconds was conservatively charged too, total 1281.4510332397185 seconds = **0.35595862034436626 hours of 8**. The terminal is safety, not a cost refusal. Earlier FOCUS-2 0.289918 GPU-h, FOCUS-2b 0.096616 GPU-h and checks37/38/39 14.715/8.02/16.591 GPU-min remain separately disclosed development.

Artifacts: results/qwen/focus2c/amendment2/{launch-receipt.json,analysis.json,README.md,terminal-audit.json,terminal-audit.py.txt,*-console.txt,acceptance.txt,ruff.txt,gpu-launch.json,section.md}; final raw records and start/end receipts are under results/qwen/focus2c/amendment1/outputs/run, preserving the immutable output-path binding. Stage-4 artifact commit **aebc2ef9df3445070a2338c22aa64fcbc359658e** force-added all FOCUS-2c results. Verified all **646 files** via git ls-files, commit tree membership and exact Git blob hashes; all 333 historical files are unchanged. No original output overwritten, protected concurrent file edited, SC1/check modification, process signal/termination, background job, delegation or push.

Plain language: increasing the cost allowance let the final experiment start, but placement plus eviction quickly violated the registered breakage limit. At the second neutral request it dropped the required tag in every observed episode; the sixth excess broken episode forced a stop. Competence still passes, but this context-management configuration fails its registered safety rule and must not be promoted. The stopped prefix cannot establish how the full 256-episode comparison or unrun conditions would perform. No efficacy, absence, compact-state, waves or benchmark-transfer claim follows. This authorized run is terminal; no further sampling or repair is launched.

## FOCUS-2d — SPLIT CUE (DRAFT v1 = REGISTRATION CANDIDATE, 2026-09-05)
Data lineage FIRST — fit-on: none; development: checks 31–39/repair, all frozen FOCUS-2/2b/2c inputs and the disclosed diagnoses; evaluated-on: fresh synthetic FOCUS-2d sort banks, disjoint from development and within/across competence, pilot and final. Nothing fit or trained; no benchmark contact except the required tests/test_sealed_guard.py, the ONE permitted sealed-IFEval reader.
STATE: prospective candidate under Brian's 2026-09-05 FOCUS-2d ruling; commit before implementation/freeze/model outcomes. FOCUS-2c Amendment 2 remains STOPPED FAIL-SAFETY at 11/256; its stop, raw records and interpretation under its registered rule stand. This is a NEW registration; no prior competence certificate, pilot timing authorization or final-prefix output is reused.

Diagnosis: results/focus2c-safety-diagnosis-fable.md (0fec674) finds all 18 BOTH breaks were terminated, well-formed JSON omitting tag at HOLD/NEUTRAL2. Moving the whole cue retired the persistent schema/tag carrier; placeholder eviction removed the answer exemplars. This was the registered configuration, not a template bug. Separately, non-BOTH breakage was 64-token truncation at NEUTRAL2; the diagnosis's prose says 15 but its arm counts sum to 16 (5+5+3+3), so retain the causal observation without adopting that inconsistent total.
The four prospective changes, and only these, override FOCUS-2c Amendments 1–2:
1. Split the cue: render the unchanged output-schema and Keep tag lines once in the base system segment in ALL five arms for the entire episode. Placement/cue retirement act only on the task-direction/default line; superseded assistant task bodies retain the same registered placeholder eviction. Text-restate restates the task/default rule in its current request using the identical hashed anti-imitation template; its schema/tag also stay in system. Current request obligations remain rendered once as before. No refresh of the changed task rule at HOLD/NEUTRAL2 in placement-only/BOTH.
2. Task/neutral task-answer generation cap becomes 128 tokens, including SET/PREHOLD, competence and NEUTRAL2; record truncation separately. The distinct 512-token delay-pair law stays at 160 tokens with its single 320-token retry and paired episode exclusion, unchanged from FOCUS-2c A1.
3. F6 publishes schema_invalid and truncated as SEPARATE rows (alongside the individual generation flags). Structural breakage/sixth-break stopping counts only invalid JSON, empty, repetitive or truncated output; a placeholder is invalid JSON. Well-formed JSON missing an unchanged field is a collateral-constraint failure, scored in primary Y and the binding unchanged-constraint safety gate, never breakage merely for that omission. Exact task/type/tag and fact checking otherwise unchanged.
4. Re-run all 192 competence fixtures because the system segment changed, then all four timing-pilot cells. NEW fixed seeds: competence 9053721, pilot 9053722, final 9053723; existing focus2-v1 RNG namespace/order, same-stream semantic collision rejection and full attempt logs unchanged. Conservatively exclude every prior frozen 2c input, including its unrun final suffix. HARD 8 GPU-h for this new leg, charging loads, competence, pilot, final/delays and analysis; same worst-cell projection plus 25% reserve and cooperative stops. Prior legs' costs are separately disclosed development, not this leg's outcomes or timing certificate.

Everything else is unchanged from FOCUS-2c A1–A2 and their inherited FOCUS-2b Amendment 1 / FOCUS-2 v3 science and execution clarifications: sort-only -20..20, 5–8 distinct unsorted operands, spaced json.dumps payload rendering, N=256 x five arms balanced by initial direction and 0/512 delay, shared unscreened prior answers, check-39 placeholder repair/closure/token maps, native tool framing, bf16 frozen Qwen3-4B hf_compatible/greedy/thinking-off, no training.
Competence stays >=52/64 per direction AND >=56/64 default; a miss is terminal INELIGIBLE. Primary all-five Y, exact McNemar/three-test Holm .05 and >=5 points over text-restate, secondary readings, F11 strata, fixed/eligible denominators, assistant-fact cost disclosed not gated, F6 h<=5 and p>.05, user/tool/unchanged safety p>.05 and net h-r<=2, prewritten readings and claim ceiling remain unchanged. Pilot flags do not determine efficacy/safety stopping. Sixth final both-only structural break stops scheduling FAIL-SAFETY; no rescue or completed-output regeneration; interrupted stages remain terminal INCOMPLETE.

Design lesson for FOCUS-3: the rendered live-rule block must carry every live obligation. Placement and masking must distinguish changed rules from unchanged constraints, and masking must never remove the only carrier of an unchanged obligation. Keep unchanged schema/tag requirements persistent while testing the changed rule's placement and persistence; preserve this distinction in the renderer, token maps and separate collateral-versus-generation measurements. The stopped 2c configuration provides the evidence for this requirement, not a general finding that placeholder eviction breaks generation.

Execution: commit candidate; minimal split-rendering/F6/cap code and tests; run CUDA_VISIBLE_DEVICES='' uv run pytest -q tests/test_focus2.py tests/test_eval_data_separation.py tests/test_sealed_guard.py tests/test_no_side_effect_imports.py and ruff; commit with explicit pathspecs. CPU freeze/commit, then separate REGISTERED header and launch receipt/commit; verify idle GPU before foreground competence -> pilot -> projection -> run -> analyze. Append FOCUS-2d OUTCOME and WORKLOG; git add -f results/qwen/focus2d/**; no push. Any failed required step stops and is recorded, without correction/retest unless subsequently authorized. Never signal/terminate a process; no background jobs, SC1/check-file edits or changes to data/classifier/relations/*.
