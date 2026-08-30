# TIMED-SELECTOR-PLAN — per-moment governance of code generation (GOVERNING; Brian-approved 2026-08-29)

Successor to AGENTIC-PLAN (stopped at its G1 gate: the always-on oracle is
the registered negative). The timed per-moment spotlight is the research
object, entering with unusually strong development evidence: span-specific
(wrong sentence 16 pts below base), time-specific (random moments = no
effect), fresh-seed stable (+22.9), and its sole validity defect traced to
one detector false positive with a verified one-line fix (parse-gated +20.8
at b=4, validity intact). Reviews: results/agentic-g1-review-sol.md,
results/qwen/g1-fable-review-report.json.

## Registered instruments (before any run)

- **AST-based scorer contract**: ast.parse/compile gate; ast.get_docstring;
  per-argument annotation coverage (unannotated args count as
  non-compliant); named target-function policy; deterministic execution
  test of the requested operation (subprocess, timeout); raw generated
  code in every evidence record. Missed moments and invalid code stay in
  denominators. PAIRED validity criterion with registered tolerance:
  parse-rate degradation 0 cases allowed at the selected config.
- **Session-layout randomization**: obligation order, block position, and
  count randomized per session; held-out obligation TYPES in val/final
  (anti-memorization + anti-regex-distillation, per fable's measured trap:
  fixed template offsets let an address head score ~100% contentlessly).
- **Seed spaces**: dev 12.3M, val 12.4M, final untouched 12.5M.
- Determinism setup imported before torch in every script.

## Phases

**T0 — Oracle confirmation under the honest instruments (half day).**
The timed oracle with the opening-quote moment fix, on FRESH dev seeds,
AST scorer, registered grid b in {2,4}. Gates: parse-gated mean compliance
lift >= +15; paired parse-rate degradation == 0; wrong-sentence and
random-moment controls at their measured signatures (harm / no-effect).

**T1 — Learned timing + learned address (the S2-equivalents).**
Timing head over frozen h20 states: labels {none, prefix, doc, hint} from
the structured generator (NOT from the regex; register the label rule);
trained on both base and oracle rollouts; evaluated on OWN rollouts.
Address scorer as in S2 over randomized layouts. Factorial triage arms
(sol's table): off/off, oracle/oracle, learned/oracle, oracle/learned,
learned/learned, always-on/oracle (known destructive control),
shuffled/wrong (non-vacuity). Plus the parser-timed contentless selector
as a named engineering baseline. Gates: moment precision >= 0.95
(precision primary — one false activation breaks syntax), recall >= 0.8;
conditional address accuracy >= 0.9; learned/learned closes >= 0.5 of the
paired base->oracle gain with parse-rate degradation == 0.

**T2 — Scripted-session benchmark (the former G2, inheriting its full
registration list from results/agentic-g1-review-sol.md "What G2 must
register") -> runtime -> registered comparison -> 7B**, each phase gated
as before; T2 is built only after T1 passes.

## Stop conditions
1. T0 misses (the fix does not survive fresh seeds + honest scoring).
2. T1: learned timing cannot reach precision 0.95 after one registered
   capacity fallback, or learned/learned closure < 0.5 with both factorial
   diagnosings pointing at learning (not wiring).
3. Any unregistered rescue. On stop: full autopsy; the SELECTOR program's
   published results stand unaffected (sol: the short-answer/long-
   generation distinction is mechanistically sound).

## T2 CONTRACT (draft for the registered design review — no runs until both
## reviewers clear it)

**Fixture.** One tiny Python module (2-3 stub functions) + the deterministic
AST/exec checker as the "environment" (hash-pinned). No external tools.

**Sessions (fully scripted, seeded).** Turn types: user instruction turns
(add/update/clear obligations: naming, docstring-opener, annotation-type,
plus one process rule), work requests (write/modify a named function),
deterministic environment feedback (checker findings on the previous work
turn, templated), distractor turns (quoting conflicting/superseded values in
prose), and compaction events at fixed turns (context truncated to the last
K turns; what survives is arm policy). Strata: 20/40/60 turns; obligations
accumulate 6-12 with 2-5 updates incl. one reversal; 1-3 compactions.

**Governance opportunities** are emitted by the GENERATOR (which obligations
apply to each work request), independent of any detector. Scoring: AST/exec
checker; missed moments and invalid code count as nonadherent — denominators
never shrink.

**Arms.** base; selector (T1 learned/learned, retrained on T2 train split,
tau recalibrated on calib split then frozen); oracle selector (ceiling);
pinned-ledger prompt; full-ledger re-insertion at each work turn
(token-charged). Compaction-summary baseline DEFERRED (registered: requires
a summarizer policy; revisit at G4-equivalent). Standing controls:
wrong-span, rate-matched random-timing, zero-selector bitwise identity.

**Held-out generality.** Val/final sessions include one obligation type
absent from training (registered: "every function body ends with a comment
'# reviewed'"). Expectation registered NOW: the detector may safely ABSTAIN
on unseen types (scores as base behavior there); a false press is a
failure. Precision stays primary.

**Metrics.** Per-opportunity adherence (micro) + per-session macro;
stale-action rate (obeying a superseded obligation); conflict adoption;
parse/exec validity (paired); cumulative prompt tokens per arm; activation
rate; per-example JSON with full transcript, ledger states, activations,
and checker results.

**Gates.** (1) selector closes >= 0.5 of the base->oracle adherence gap on
val; (2) cost-adjusted: selector adherence >= re-insertion adherence - 2pts
at <= 50% of its cumulative prompt tokens, OR beats it outright; (3) paired
parse loss == 0; (4) stale-action rate <= half of base's. Final untouched
seeds only if val gates pass.

**Seeds.** dev 12.6M / train 12.65M / calib 12.7M / val 12.75M / final
12.8M (untouched).

**Stop.** Gates missed after one registered tau/dose recalibration => stop;
autopsy; T0/T1 results stand.

## T2 CONTRACT v2 (supersedes the draft; merges sol's 13 MUSTs + fable's 7)

**Compaction (MUST-1).** ONE survival rule for base/selector/oracle/controls:
context truncates to the last K turns (K=8/12/16 by stratum) at registered
compaction turns; the ledger does NOT survive for these arms (obligations
live only in surviving turns). Prompt baselines apply their token-charged
insertions on top of the same rule from the harness ground-truth ledger
(stated: oracle-informed baselines). No per-arm survival policies.

**Address candidates (MUST-2).** Candidates = every obligation-like sentence
in surviving context, INCLUDING superseded versions and distractor prose
quotes; scored against generator ground truth (latest version); accuracy on
superseded-present and distractor-present cases reported separately.

**Abstain mechanism (MUST-3).** The address stage has a null option: press
only if max address score > theta, calibrated on the calib split, frozen.
Registered gate: unseen-type false-press count == 0 over >= 64 registered
unseen-type opportunities; seen-type false-press rate <= 2%.

**Held-out types (MUST-4).** Two: (a) "# reviewed" comment rule, scored by
a registered tokenize/source-text rule (NOT ast — comments are discarded);
(b) an unseen FORMAT of a trained type (naming rule in an unseen template)
at a TRAINED moment class, where the syntax head fires and address+abstain
must discriminate. Neither supports a generality claim alone; both are
reported as OOD probes with abstention/adherence/false-press separated.

**Opportunities & denominators (S1, sol-1).** The generator emits immutable
opportunity records: (session, work-turn, obligation-id, moment-class);
annotation opportunities are per-argument. Micro = per-opportunity across
all sessions; macro = per-session mean; BOTH gated. Missed/invalid stay in
all denominators, including stale.

**Arms.** base; selector (learned timing + learned address + abstain);
oracle/oracle; parser-timed (regex timing + learned address — named);
pinned-ledger; full-ledger re-insertion (exact: live-ledger only, canonical
serialization, inserted immediately before each work turn). Controls:
always-on/oracle, shuffled-timing/wrong-span, zero-selector bitwise,
retention-only N/A (single survival rule). Factorial diagnostics
(learned/oracle, oracle/learned) run on the dev split for triage.

**Component gates (MUST-6).** Own-rollout moment precision >= 0.95, recall
>= 0.8; conditional address accuracy >= 0.9 under the MUST-2 candidate set;
the MUST-3 false-press gates. All from per-example JSON.

**Behavioral gates (MUST-5, repaired arithmetic).** N = 96 sessions per
split (registered); minimum oracle headroom for gate 1 to bind:
A_oracle - A_base >= 0.10 (else T2 is inconclusive-by-design, recorded).
Gate 1: closure >= 0.5, McNemar-paired. Gate 2 (cost): with C = logical
input tokens summed over the session (registered definition; no KV
assumptions) and precondition A_reinsert >= A_base:
PASS iff (A_sel >= A_reinsert - 0.02 AND C_sel <= 0.5 * C_reinsert) OR
(A_sel >= A_reinsert + 0.02 AND C_sel <= C_reinsert). C_sel > C_reinsert
never passes. Gate 3: paired parse loss == 0 AND paired exec/task-success
loss == 0. Gate 4 (stale): binds only if base stale opportunities >= 24
per split; then stale rate <= 0.5 * base's.

**Semantics (sol-7).** Adherence scoring via the AST/exec checker with the
registered target-function policy; task success (execution test) gated in
Gate 3, not parse alone.

**Provenance (sol-10).** Only scripted user turns author ledger changes;
distractor text has no authority; unauthorized-write count == 0 asserted
structurally (the harness owns the ledger — recorded as such, no learned
write path at T2).

**Freeze (sol-11/12/13, S5).** Session counts, generator distributions,
decoding (greedy, max-new per turn = 120), checker version, fixture hash,
evidence schema (raw output, true opportunities, true/predicted moments,
predicted addresses + scores, spotlight rows/spans, compaction events,
config hashes, paired-arm identity) — all frozen at the pre-run audit
commit; a post-build pre-run hash audit is a registered step.

**Scope notes (S2/S3/S4).** The process rule is CUT from T2 (undefined —
deferred to a later registration). T2 training rollout policy: base + oracle
rollouts (plan text now matches practice or the deviation is recorded).
Summary-baseline deferral carries the clause: no usefulness or 7B gate may
be claimed against summarize-at-compaction before it runs.

## T2 CONTRACT v3 (v2 + sol round-2 repairs; fable round-2 SIGN-OFF stands)

- **Compaction repaired (supersedes v2 MUST-1 rendering):** the canonical
  LIVE ledger (current obligations, canonical serialization) SURVIVES every
  compaction identically for base / selector / oracle / zero-selector /
  controls — memory is the ledger's job; the wire is tested on SELECTION.
  Conversation turns truncate to the last K turns (K=8/12/16 by stratum) at
  registered turns for all arms. Superseded/distractor text lives in
  turns (and dies with them); the live ledger never contains it.
  Pinned-ledger baseline = the same surviving ledger ADDITIONALLY repeated
  immediately before every work turn (placement registered; tokens charged);
  re-insertion baseline as registered.
- **Opportunity records:** (opportunity-id, session, turn, obligation-id,
  target-object, moment-class, active-expected-value, superseded-values,
  scorer-id); annotation opportunities are per-argument with target-object
  = arg name. Stale rate: numerator = opportunities whose output obeys a
  DISTINCT superseded value; denominator = opportunities having >= 1
  distinct superseded value; invalid/missed outputs denominator-only.
- **Active/absent counterfactuals (registered set):** each val/final split
  contains >= 48 paired work turns with identical request syntax where a
  trained-type obligation is (a) active, (b) absent, (c) cleared, (d)
  present only as superseded/distractor text. Address/abstain metrics
  reported on this set separately; false-press gates apply per cell.
- **Freeze list extended:** timing head = linear 4-way {none,prefix,doc,
  hint} over h20; address = 64-d query-key scorer with null threshold
  theta; training = Adam 1e-3, 30 epochs, class weights [1,20,20,20],
  batch 512, 192 training sessions (base + oracle rollouts, policy fixed
  NOW); tau and theta calibrated ONCE on the calib split (grids
  {0.5..0.98} and theta over score quantiles {0.5..0.95}, tie-break:
  highest recall then lowest tau/theta), then frozen; beta=2, current-row
  one-token activation, layers 20-27 inherited. ANY validation gate miss
  stops T2 — no post-validation recalibration; the single registered
  fallback (address-head capacity: 128-d) may be invoked once only for an
  address-accuracy miss, on a fresh seed block 12.85M.
- **Absolute floors (owner-registered):** macro AND micro A_selector >=
  0.70 on val; A_selector - A_base >= 0.10. The >= 24 stale-opportunity
  binding condition refers to GENERATOR-DEFINED stale opportunities.

## T2b REGISTRATION (2026-08-30 — new round, per the T2 inconclusive-by-
## design outcome; requires sol+fable clearance before build)

Finding motivating T2b: T2 sessions show no selection failure (oracle
headroom +0.016) — a small clean surviving ledger is simply read. The
selector's proven regime is INTERFERENCE (S0: three format-identical
conflicting notes -> base 46%; S3: N=32 -> base 4%). T2b tests whether that
regime, occurring inside multi-turn steered sessions, is fixed by the
selector.

Delta from CONTRACT v3 (everything else inherited unchanged):
1. Distractor turns now emit S0-style interference: bare format-identical
   "Note: <SENT>" lines with CONFLICTING values for ACTIVE types (no
   "old thread"/"not authoritative" framing), 2-4 per active type per
   session, scheduled so >= 2 conflicting notes sit inside the surviving
   window of each scored work turn. The ledger remains the sole registered
   authority (its header says so), surviving compaction as in v3.
2. Sessions add a second wave of conflicts after each compaction
   (post-compaction work turns face fresh interference).
3. Selector heads RETRAINED on the T2b train split (12.90M block) with the
   IDENTICAL frozen recipe (incl. theta = max abstain + eps); calib
   12.93M; dev 12.95M; val 12.96M; final untouched 12.97M.
4. Gates unchanged from v3 (headroom precondition >= 0.10 at dev shakeout
   binds first; absolute floors; cost gate; component gates; counterfactual
   cells re-verified by the generator unit tests on the new distribution).
5. Stop: headroom < 0.10 again => the boundary finding is CONFIRMED
   (multi-turn sessions with a surviving authoritative ledger do not
   exhibit fixable selection failure even under S0-style interference) and
   the program closes with that as the T2 chapter; no third design.
