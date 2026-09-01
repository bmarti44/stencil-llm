# EVF — Predictive Reactivation / Expected Value of Focus (the WHEN program)

Authorized by Brian 2026-08-31 ("kill what is currently running and run
this new program instead — red/green TDD, deterministic proof it's
implemented correctly"), superseding the v4.5 confirmation mid-run (its
partial records are retained untouched under results/qwen/
b3-deficit-conf-s0/; the seed-0 sealed attempt is recorded ABANDONED-
BY-RULING, not failed). Design: sol xhigh spec, results/
b3-when-design-sol.md. BENCH-WAVE-PLAN.md machinery (data freezes,
verifier vendoring, stats) is inherited; the single-turn stop-loss is
superseded by this authorization.

## The isolated bottleneck (established)

Amplitude solved (2x force = 0 extra repairs). WHERE solved (K-perm
kills the benefit). WHEN is open: the psi<tau attention trigger makes
12 bad calls per 15 good; oracle WHEN ceiling +7.5pts vs +1.5 harvested.

## Phase E0 — the decisive pilot probe (kill-fast; THIS phase only is
authorized to run before its gate reports)

Data: the recorded calibration discordants (t30-b3 vs base, 15 repairs
+ 12 regressions) + concordant controls, from
results/qwen/b3-deficit-cal/ per-item records. No new generation on any
frozen evaluation stream; teacher-forced feature passes only.

Per discordant row:
1. Find the FIRST divergence token between the base and wave responses
   (shared prefix p; the WHEN decision that mattered happened there).
2. Teacher-force prompt+shared-prefix through the trunk once; cache at
   the divergence point (and at 2 matched control points in concordant
   rows): h20; decoder entropy, top-1 margin and their deltas over the
   last 5 tokens; the frozen wave's rule-readout features (per-span q/k
   scores: max, margin between top-2 spans); natural attention-mass
   summary on the governing span (layers 20-27 mean).
3. One additional weak-focus forward (the selected t30-b3 field scaled
   to b=1.0 on the governing span) at the same prefix; cache
   KL(P1||P0), JS divergence, and the obligation-token probability
   shift (mean delta log-prob of the row's obligation-span tokens).
4. Labels: repair=1, regression=0 (verifier-derived, offline).

Probe: L2-regularized logistic regression (deterministic solver, fixed
seed), leave-one-topic-out AND leave-one-constraint-family-out folds.

GATE E0 (registered): held-out repair recall r+ >= 0.60 with
regression fire-rate r- <= 0.25 on the 15/12 anatomy, in BOTH fold
schemes. KILL immediately if: focused-vs-native divergence features are
indistinguishable between repairs and regressions AND obligation/
readout features add no held-out discrimination; or performance
disappears under family holdout; or the probe works only via constraint
type or response position.

## Phase E1 (only if E0 passes; separate go)

Recurrent obligation tracker (GRU 128/rule) + two-stage firing
(eligibility screen -> one-token counterfactual -> calibrated
lower-confidence-bound EVF > 0), bursts <= 4 tokens + refractory;
labels from offline verifier-scored counterfactual rollouts; safe-dose
interval requirement (a BROAD non-harmful tau/threshold plateau, not
one winning scalar) and behavioral gates per sol's spec sections
(offline discrimination, safe-dose, behavioral) — registered in full
before any E1 training run.

## Process

Red/green TDD throughout: every component gets a failing test first;
deterministic proof = bitwise-identical feature extraction across two
runs, fixed-seed probe fits, and fixture-exact tests for divergence
finding and label derivation. Reviews: sol + fable on the E0 result
before any E1 work. Playbook governs (per-item records from the first
row of anything evaluative; git add -f for results; smoke before
sealing).

## E0 verdict + REGISTERED post-Multi-IF decision rule (sol post-mortem,
registered BEFORE Multi-IF results are seen; 2026-08-31)

E0: KILLED per its registered criterion (fable: all numbers bitwise-
verified, zero findings). Post-mortem (results/e0-corrections-sol.md):
the question was causally blurred (policy-divergence labels, not
moment-level treatment effects), plus family-grouping and omitted-
controls flaws. NEVER: E0-with-more-rows; further tuning on the 27;
E1 as originally specced.

DECISION RULE for the running Multi-IF (base / deficit-wave /
static25), registered now:
1. static25 helps late turns, deficit-wave does not -> actuator has
   multi-turn value, WHEN is the blocker: launch the causal-moment
   protocol (frozen moment, branch A=0/A=1 single burst, deterministic
   rollout to verifier endpoint, ITE labels helpful/harmful/neutral;
   identical replayed base histories; session/topic + changed-family
   splits; the FIXED three-feature conflict probe (margin_delta5,
   attn_mass_span, entropy_delta5) is the pre-registered primary
   mechanistic endpoint).
2. deficit-wave helps -> do NOT build EVF; replicate + characterize
   the simple gate in its arena first.
3. neither helps but an oracle chooser over recorded arm outputs shows
   substantial late-turn lift -> timing headroom exists; run the
   causal-moment branches next (policy-level oracle is only a screen).
4. neither helps and the oracle has negligible lift -> do not fund a
   larger WHEN learner; establish moment-level actuator headroom first.
Caveat registered: each arm consumes its own history, so late-turn arm
differences are NOT clean local treatment effects; any training
anatomy must replay identical base histories before branching.

## E2 — CTRB training + clean Multi-IF evaluation (Brian-approved design,
registered 2026-08-31; supersedes the four-branch rule's arm comparisons)

CONTAMINATION RULE (Brian's question, registered): the gate NEVER trains
on Multi-IF content. Design:
- Multi-IF wave arms CANCELLED (the base arm completes: it is the paired
  baseline + turn-decay headroom map + the frozen histories the EVAL
  replays — never training data).
- TRAINING CORPUS: synthetic multi-turn sessions from the v4.3 generator
  extended to Multi-IF's SHAPE (turn 1 task+constraints; later turns add
  constraints while earlier ones bind), own topics/phrasings/values,
  mechanical leak firewall vs Multi-IF (kwargs/phrase/topic checks as
  registered for the 541). Causal-moment harvest: conflict-guided
  sampling (CTRB features), late-turn emphasis, A=0/A=1 branches, ITE
  labels; identical replayed histories per sol's protocol.
- GATE TRAINING: CTRB hazard gate on causal labels; family/topic/
  session holdout; the registered discrimination + safe-dose gates from
  the WHEN spec apply before any benchmark exposure.
- EVALUATION (one shot, paired vs the recorded base arm): CTRB-gated
  wave on Multi-IF. SECONDARY SPLIT registered NOW: conversations with
  key hash mod 9 == 0 (~100) are the disclosed in-distribution
  diagnostic slice; the PRIMARY claim is staked entirely on the
  remaining ~809 untouched conversations. Metrics: per-turn-index +
  pooled strict metrics; primary = late-turn (turn 3) strict-prompt
  paired delta with exact McNemar.
- Reviews: sol + fable on the synthetic corpus AND the trained gate
  evidence before the evaluation runs.

## E2 endpoint re-registration (kimi CRITICAL-1 + HIGH-2; registered
2026-09-01 BEFORE any gate training, replacing the E2 endpoints above)

Motivating claim CORRECTED: the Multi-IF strict-prompt decay is
conjunction arithmetic (independence prediction 0.686/0.497/0.290 vs
observed 0.711/0.513/0.321). The registered headroom is the
CONSTRAINT-AGING effect measured in results/qwen/multiif-headroom-map
.json: a turn-1 constraint decays 0.770 (fresh) -> 0.719 (t2) ->
0.661 (t3); turn-2 0.795 -> 0.747. Target = recovering aged-constraint
compliance, ~5-11pts, NOT the 38pt strict-prompt drop.

ENDPOINTS (replacing "late-turn strict-prompt"):
- CO-PRIMARY 1 (causal, confound-free): REPLAYED-HISTORY evaluation —
  for each conversation, replay the BASE arm's recorded turns 1..k-1
  verbatim as history, then generate turn k (k in {2,3}) with and
  without the gate. Identical inputs; the only difference is the
  intervention. Paired exact McNemar on AGED-CONSTRAINT compliance
  (constraints whose origin turn < k), alpha 0.05 one-sided.
- CO-PRIMARY 2: same design, per-constraint inst-level paired McNemar
  over ALL constraints at turn k (escapes conjunction mechanics).
- SECONDARY (policy-level, disclosed as confounded by own-history
  shaping): own-history three-turn run, strict-prompt + inst-level.
- CONTROLS registered: response length and truncation rates per arm/
  turn reported alongside every endpoint (kimi's length confound); an
  intervention-count log per turn; gate-silent rows must be BITWISE
  identical to base (the CTRB harm guarantee, asserted in the artifact).
- The ~100-conversation diagnostic slice remains disclosed and excluded
  from all primary claims.
GATE: co-primary 1 must show a positive paired delta on aged
constraints with p < 0.05 AND no excess truncation/timeouts; co-primary
2 reported with it. Failure = honest negative; the arena question is
then answered for this actuator.

## E2 amendments from kimi round-2 (CRITICAL-1 + HIGH-1/2/3), registered
2026-09-01 BEFORE any Multi-IF contact

1. EFFECT FLOOR restored on co-primary 1 (was dropped — the B4 discipline
   must apply to the endpoint that matters most): net aged-constraint
   recovery >= +2.0 points AND one-sided p < 0.05. Significance alone
   cannot pass the gate.
2. CLUSTER-AWARE INFERENCE: constraints within a conversation share a
   history and a response, so per-constraint McNemar is anti-conservative.
   Registered: conversation-level co-primary (any/all aged constraints
   recovered per conversation) AND a cluster bootstrap by conversation
   reported beside the per-constraint test.
3. ABLATION ARMS (a positive that does not beat BOTH is not evidence for
   conflict-triggered WHEN, only for "some spotlight"): (a) PERIODIC
   trigger at the gate's measured firing rate, no conflict features;
   (b) FIXED-SPAN always-oldest-user-turn bursts. If runtime forbids
   both, the claim is scoped to "the CTRB package" explicitly.
4. HEADROOM RE-DERIVATION before the 5-11pt target is quoted again:
   WITHIN-TURN fresh-vs-aged, mix- and length-adjusted, from the recorded
   base arm (kimi's back-out suggests within-turn-3 aging may be ~2pts,
   not 11 — the cross-turn comparison confounds aging with turn-3 global
   difficulty).
5. PRE-EVAL GATE AUDIT on the synthetic holdout with registered acceptable
   ranges: firing rate per turn, span-selection by turn origin, burst-count
   distribution. A gate that degenerates to "always boost the oldest user
   turn" is caught here, not after the eval.
6. PARAMETER FREEZE before any Multi-IF contact, diagnostic slice included
   (or the slice is dropped).
7. RE-APPEND POSITIVE CONTROL (MMMT-IF style): aged instructions restated
   fresh in the replayed history. No training; bounds what focus/retrieval
   recovery could EVER deliver on this harness, calibrating any wave
   positive as a fraction of addressable headroom.
8. The SINGLE-TURN question is formally recorded as UNANSWERED (the v4.5
   confirmation was abandoned by ruling at ~100/1024, not failed). "Pivot"
   does not mean "failed"; reviving the claim requires completing that run.
Also noted (kimi MEDIUM): _native_draft_confirms uses uncached full
forwards while the committed trajectory is KV-cached — the WHEN decision
runs on a numerically different path than the one committed (our own KV
characterization: drift up to 1.107 logits vs margins as low as 0.103).
To be characterized or the draft-confirm disabled before the eval.
