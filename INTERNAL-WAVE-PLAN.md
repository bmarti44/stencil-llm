# INTERNAL-WAVE-PLAN v2 — the wave generated inside

v1 reviews (checkpoint i): fable CLEARED with 8 required edits; sol NOT
CLEARED with 3 CRITICAL + 7 HIGH. All folded. The honest claim after
review: this program re-poses the closed learned-relevance question
with ONE genuinely new axis — the training signal (behavioral CE
through the frozen trunk's differentiable attn_bias path, utility-
shaped, no hard threshold) — supervised on canonical adherent
completions. Timing and address EMERGE from that signal or they do
not; they are not "discovered from reward" and the plan does not claim
"no proxy labels". Success means: continuous cost-sensitive control
passes behavioral validity where discrete certified selection could
not. The liveness problem is not claimed to disappear.

## The bar

Closure >= 0.50 of oracle headroom on dev under the T0.3 validity rule
with no parser, no checker feedback (see FEEDBACK MODE), and no
ledger-span lookup at inference. The wave must ALSO beat the
CLOSED-LINE CONTROL ARM (frozen T2b selector timing + fixed-beta press
via the existing selector arm) and survive the DISTILLATION PROBE: fit
a thresholded discriminator (h20 -> press) on the wave's own gain
decisions; if it reproduces >= 90% of them AND, substituted at replay,
matches the wave's closure, the wave is a re-parameterized
discriminator and the differentiability claim FAILS regardless of
closure.

## FEEDBACK MODE (frozen; sol CRITICAL 2)

All W* training and replays use feedback_mode="none": environment
turns carry the fixed neutral text "[checker] (no feedback available
this session)" identically for every arm (train, base, wave, oracle,
reinsertion, closed-line control). The win claim is thereby literal:
no checker signal exists anywhere in the loop.

## W0.0 — canonical reference builder (sol CRITICAL 1; gates W0)

A deterministic builder maps (session, work turn) -> canonical
adherent code: function name {prefix}_{fn} (ledger prefix value; bare
{fn} if prefix inactive); a one-line docstring ALWAYS present, opening
with the ledger doc value when active and with the registered neutral
opener "Compute." (not in POOLS) when inactive; args typed with the
hint value when active
(untyped when inactive), body implementing sess.ops[wt]. Registered
verification over every train work BEFORE training: parses, executes
(OP_TESTS), satisfies every active obligation via score_work,
satisfies NO cleared/stale obligation, and records prompt length,
target ids, and row alignment. Any failure -> fix the builder, rerun;
the builder is frozen at zero failures.

Training loss: ORDINARY CE over EVERY canonical continuation token
(teacher-forced on the canonical code, not on base outputs), plus L1
on the gain (sum reduction, lambda 0.01). This supervises full
adherent completions; moment-level effects are measured, not
supervised in isolation.

## W0.05 — field parameterization ceiling (sol HIGH 7 + fable 3;
gates the architecture freeze)

The v1 field (total row mass <= beta_max) is dose-starved vs the
proven press (2.0 per span token, mass 20-30) — it cannot express the
oracle. Candidate parameterizations, selected by a TRAIN-SEED-ONLY
deterministic oracle-field ceiling test (hand-built fields at oracle
moments/spans, exact proposed parameterization, feedback_mode none):
  (A) peak-normalized: b = g * softmax/max(softmax), per-token cap g;
  (B) per-position bounded: b_i = beta_max * sigmoid(e_i), e from
      q/K logits (no normalization).
Ceiling grid: beta_max in {2, 4}. Selection rule (frozen): smallest
(parameterization, beta_max) whose ceiling shows (i) correct-position
benefit (moment CE improvement >= 20% vs zero field), (ii)
wrong-position non-vacuity (measurable degradation, proving the test
can fail), (iii) the T0.3 validity rule on a 12-session train-seed
replay. Preference order on ties: A2, B2, A4, B4 (lowest dose first;
the T0 rejection of hard b=4 is registered as known tension). If NO
cell passes, the program closes at W0.05 (the field cannot express
useful pressing — an honest negative about the parameterization
family). Every replay in the program emits a per-press gain histogram
artifact.

## W0 — stateless wave

Architecture (frozen AFTER W0.05 selects the field; shape-TDD only
before): q/k normalized (F.normalize) with registered temperature 8.0;
W_q, W_k: 2048->64 with bias; gain head 2048->1; low-gain init
(w_g zero-init so g starts at beta_max/2... registered: bias init
-2.0, weight zero -> g starts at beta_max*sigmoid(-2)=0.12*beta_max).
Exact parameter count 264,321 (two 2048x64+64 maps + 2049). K = the
prompt's h20 states [0:P) computed AFTER feedback-mode substitution,
recomputed whenever the prompt changes; bias/query row j-1 targets
token j; prompt columns exactly [0, P); one shared field at layers
20-27 via a padded [1, 1, T, T] tensor; batch 1 with gradient
accumulation 8; trunk grad-enabled with requires_grad=False on all
trunk params, layers 0-19 under no_grad (split-forward; the doubled
lower-trunk cost is disclosed, not optimized). Registered pre-training
smoke: max-length forward+backward peak memory and wall time.

Training (frozen): Adam(1e-3, 0.9/0.999, 1e-8, no wd), 20 epochs over
the 40 TRAIN seeds (13,400,000..39), shuffle generator seed 0, init
seed 0, final-epoch checkpoint (no selection); held seeds
13,400,040..47 for G-W0c.

Gates (all on artifacts, before any dev replay):
- G-W0a connectivity battery (sol HIGH 6): with the REAL trunk CE loss
  (no L1): finite nonzero grads separately for W_q, W_k, w_g; nonzero
  dCE/dbias; a detached bias FAILS the check (self-test); zero field
  is bitwise base-equivalent; wrong-position vs correct-position
  hand fields produce distinguishable logits.
- G-W0b overfit-1: canonical-token CE on seed 13,400,000 falls >= 50%.
- G-W0c held CE improvement >= 10% AND the ablation battery (sol HIGH
  8): zero-field vs full; K-permutation (WHERE); gain-sequence
  permutation across rows (WHEN); uniform field at matched gain;
  per-cell (active/cleared/stale/absent) reporting. The battery is
  reported, not gated, EXCEPT: if the uniform field at matched gain
  reproduces >= 90% of the CE gain, the wave is an indiscriminate
  boost and W0 CLOSES.

W0 dev replay (13,450,000..23; arms: base, wave, oracle (once),
reinsertion, closed-line control): headroom >= 0.10 precondition
(one re-draw on 13,455,000..23, used for NOTHING else); decision
table (validity-fail dominates every band):
- infrastructure/gradient failure -> fix implementation, no verdict;
- G-W0b/c failure -> W0 CLOSES;
- validity fail (any closure) -> W0 CLOSES;
- closure >= 0.25 + validity -> W1;
- closure in [0.10, 0.25) + validity -> partial result recorded, W1
  proceeds (W1 IS the registered next architecture; the v1
  "wider heads" rescue is CUT);
- closure < 0.10 -> W0 CLOSES.

## W1 — recurrence

GRU(64) over h20_t, reset per session, carried across works; update
schedule frozen: state updates at EVERY generation step from h20_t;
prompt tokens do NOT enter the state (the state sees only what the
trunk computed while generating). q_t, g_t from [h20_t; s_t]. Same
loss/optimizer; fresh dev block 13,460,000..23 (disclosed; no reuse of
W0's). Temporal-state probe (sol HIGH 9): predecessor-state
PERMUTATION (swap s_t sequences across matched sessions, preserving
current h20_t) and matched reset — BOTH must degrade held CE by >= 10%
relative AND degrade replay adherence, else the result is recorded as
"stateless suffices" (a finding; no W2).
Decision table:
- closure >= 0.50 + validity + temporal probe passes -> dev WIN ->
  fresh registration for sealed validation (13,500,000..95; headroom
  >= 0.10, closure >= 0.50, validity, NO redraw);
- closure >= 0.50 + validity, temporal probe fails -> stateless
  result; no W2; program records the win as W0-class;
- closure [0.25, 0.50) + validity -> partial close;
- else -> close.

## W2 — transplant (only after a W1 dev WIN with temporal probe)

Paired sessions with IDENTICAL visible candidate text but different
prior authority histories (constructed: same final window, different
aged-out set/clear sequences); arms own-state / donor-state /
shuffled-state / reset-state at identical moments; the claim requires
donor-state governance to track the DONOR's authority history against
identical visible text. Fully registered + reviewed before running.

## Seeds and accounting

train 13,400,000..39; held 13,400,040..47; W0 dev 13,450,000..23;
redraw 13,455,000..23; W1 dev 13,460,000..23; sealed val
13,500,000..95. PRESS-PLAN's open-ended 13,300,000+ certification
namespace is BOUNDED to [13,300,000, 13,400,000) and closed with that
program. No other block overlaps anything registered.

## Frozen rules

Trunk bitwise frozen; press/gain logs + histograms for every replay;
pipefail; no top-level work in imported scripts; reviews at (i) this
v2, (ii) W0.05 selection + W0 results, (iii) W1 results / W2
registration, (iv) close; loop while high/critical; halting is
success; every number recomputed from artifacts.
