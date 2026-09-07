# Composition design v2 for gpt-6-astra (2026-09-06): revise after 40g, 40j, the fable review, and the reuse research

Inputs (read all, CPU): your results/focus-mechanism-composition-astra.md; results/composition-design-review-fable.md
(one-round review: numbers correct; HIGH — C-vs-R does not isolate the actuator, 512-token/16-round caps incompatible
with tool rounds, absolute breakage bar unmeetable; MEDIUM — profiles must be indexed by request form, expected C-R
~0; cut list; keep 40i whole-body mask); results/quick-checks/check40g/README.md (INVALID at the positive control:
JS 3/8 on the 40e request form); results/quick-checks/check40j/README.md (R1: a rendered live rule gives 16/16 JS in
the hard form single-shot AND after six retained Python answers; bias-only 0/16; bias/mask add nothing; registered
consequence: actuator out of default shipping; rendering-only primary); results/reuse-research-fable.md and, if it
exists, results/reuse-research-astra.md (your own; prior-art reuse verdicts — use what is drop-in/adapt: HF
custom_generate as the ship form; create_masks_for_generate keep-masks; ReBIND "relapse"/tombstones; Snowball
ceiling; NLSI for scope matching; do not force anything).
Brian's rules: do not over-engineer; quick prove/disprove first; only continue to a larger implementation after
adequate proof; never delete history (masking only); no string matching in the register (classifiers); one HF repo
download ships the whole thing; eval-data separation (never fit/select/tune on any evaluation benchmark; data-lineage
line first).

Write results/focus-mechanism-composition-v2-astra.md (replace v1's role; keep v1 as history) containing:
1. FIRST-SHIP v1 SCOPE (the cut list applied): explicit structured rule entry ({action,key,scope,kind,value,
   target_version?}) + frozen relation classifier for entry validation/relations (v3 if it passes its GO) + the
   register (versions/status/provenance; masking-only retirement) + every-request renderer (all live obligations incl.
   defaults; request-kind matching; ReBIND-style tombstone lines for recently retired rules — state it as a
   hypothesis to test, not a fact) + one-generate loop + same-run journal + custom_generate packaging. Actuator (JS
   bias + 40i whole-body mask) behind a flag, OFF by default, certified only on the 40c request form. Automatic
   admission (44c) is assistive until it passes its GO. No task-type head, discovery, multi-family library, prefix-
   cache sharing, fact-preserving mask.
2. THE LARGER TEST, revised: arms R (rendering-only, classifier/explicit-entry driven), N (nothing), T (evaluator-
   authored correct text restated every request), O (gold events + renderer) and OPTIONAL O_off/O_on for the
   actuator flag if cheap (the clean actuator contrast the review asked for; may be cut to save GPU). Primary
   contrast R > N (and R vs T descriptive; O vs R = perception/state-binding gap). Fix the caps (realistic per-round
   token budget for tool rounds — justify from 40i/40j measured throughput), keep only the paired breakage clause,
   recompute power by exact enumeration, keep <= 6 GPU-h with measured (not assumed) costs from a DEV pilot; episode
   generator = StaminaBench-style procedural bank authored by us with our own supersede/cancel/complete/reinstate
   events and executable hidden checkers (name the generator design; no external benchmark data; data-lineage line).
   Pre-written PASS/FAIL/INELIGIBLE readings. Include the "relapse" endpoint (stale execution after a revoked rule)
   explicitly.
3. RELAPSE PRESSURE: 40j's harness showed no relapse. Specify the ONE 20-minute screen (rule load, distance, own-
   output count) that would show relapse if it exists, so we know whether the mask arm has any job — or argue it
   should go straight into the larger test.
4. BUILD PLAN for the week with the GPU queue (44c, relations v3 already queued), what is CPU-only, and the odds.
CPU only; no model launch; no repo edits except the report; never read anything under data/bench.

ADDENDUM (fable's 40j review, results/check40j-review-fable.md): R1 stands. Own-output imitation IS present at the
style level (P2 text-only copied 4-space indent 16/16 vs 0/16 fresh) — the rule wins on the axis it names, history
wins on every axis it is silent about; relapse will show first on STYLISTIC rules. Do not run another arithmetic
screen; put per-turn rule-violation instrumentation BY RULE KIND (language, style, format, process) into the larger
test, with 3-5 concurrent rules incl. stylistic ones and 10-20 prior own turns of 100-300-token bodies. Keep
bias+mask behind a flag as a contingent arm triggered only by a measured relapse floor (mask = the useful half).
Also: the combined arm's bare replies violated the system prompt's code-block default — a hidden actuator cost.
