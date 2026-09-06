# FOCUS-3 gate — pre-written reading (2026-09-06)

Fit/train/select: NONE. Relations = frozen seed0 three GPU epochs, commit952079b8,
S/C/Cm/R=.94/.50/.50/.50; new-rule admission uses ft P(rule)>=.95 and every
eligible pair P(none)>=.98. The admission model has disclosed IFEval/probe
influence and an unreconciled historical recipe (data/classifier/LABELS.md).
This package is not development-independent. No sealed benchmark input is read.
Evaluation = new independent gpt-5.5-authored prose templates, seeded fresh
synthetic lists (30301 gate,30302 setup); template repetitions are disclosed,
so fixed-cohort feasibility counts are descriptive, not population inference.
Author fixture, generated inputs, source and all model/config hashes freeze in
Git before inference. No thresholds, prompts, cap, arm, or checker rescue.

64 gate episodes,16 each override/cancel/complete-and-move-on/switch-and-return;
16 setup episodes (4/family), all6 complete user+assistant pairs =12 turns.
Sort and JSON/tag obligations; every episode has quoted/hypothetical/tool-claim
hard-none prose, initial admission, change, unrefreshed continuation and final
request. Each list is distinct from its sorted/reversed forms. Setup and gate
use separate value ranges and authored scenario templates. All answers are fresh,
unscreened, greedy Qwen3-4B dense bf16 hf_compatible, thinking disabled, cap64.
Each arm owns its full conversation; ordinary fresh full-history prefill per
request, no masking, eviction, weight update, output sharing or forced successes.
This gate measures sort/tag compliance, not retained arbitrary-fact recall.

C: candidate sentence spans x eligible versions, frozen relation head, source
identity/explicit task-scope grammar, independent rule-head admission, register.
O: ground-truth admission and changes, same register and renderer. No gold goes
into C. N: no register or added text. T: append-only raw rule statements (gold
statement boundaries, no live-state decisions), including all superseded and
other-task rules; all ever-stated rules of the current request kind are rendered.
T receives no corrected live recap. C/O render inside EVERY task request's user
message; sort schema/tag constraints are absent on prose requests. Provenance
is logged with own-output intervals and live version sets, but never consumed.
Task switch suspends applicability; explicit return restores it. No masking
means mask un-release and affected masked-column counts are zero; switch-back
applicability/reactivated output-column counts and final success are separate.
Fail-safe none protects retirement only; confidently wrong none can permit bad
admission. Report admitted_beside_live separately from gold contradictory recaps.

Endpoints are episode counts: stale execution = any post-change sort answer
exactly executes an inapplicable old ordering on a pre-frozen discriminator;
false retirement = any gold-live row missing/changed/shadowed in C's rendered
set, INCLUDING initial admission misses; final success = final task answer and
tag exactly correct; breakage = any post-change invalid-schema/empty/truncated/
repetitive reply (FOCUS-2 JSON/equality/repetition primitives). Non-JSON prose is
allowed on prose turns; capped replies are broken, retained, never excluded.
REGISTER AGREEMENT compares source-turn/span IDs, version, scope, kind and text
at every task answer, including initial admission. Register-exact requires all
such turns equal. Contradictory recap = repeated evaluator gold key in one recap;
map all source spans to semantic order/tag keys before inference, including
hard-none cancellation claims, never supply that key map to C.

PASS requires ALL: absolute C/O stale-count distance<=4/64, absolute C/O final-
success distance<=4/64, C false retirements<=2/64, C breakage<=2/64, C stale<T
stale, C register-exact>=48/64 and>=12/16 in EVERY family, zero contradictory
recap episodes. N is descriptive; no retirement/agreement performance attributed
to N or T. These are practical margins, no statistical superiority claim.
All planned arms/turns required. O gold state/checkers must agree by CPU audit.
Missing work/budget -> INCOMPLETE; invariant/fail-open overflow -> FAIL. Setup
uses direct per-request current rule/tag cues and requires >=15/16 strict final
successes; failure -> INELIGIBLE and no gate. Setup scores do not filter episodes.
A failed completed gate stays FAIL; no output-based repair or rerun.

Cost before setup: at15 tokens/s,96 setup+1536 gate generations,64-token cap,
600s load and25% reserve:1.25*(600+1632*64/15)=9454s<10800s. Include classifier,
model load, setup and inference in elapsed GPU-held time. After all16 setup,
project from slowest full setup episode (including classification timing), four
arms/episode, plus already elapsed and25% reserve. Choose64 if within3h;
otherwise choose48 (12/family,first12 fixed indices) ONLY on this resource rule,
record selection before gate, and require36 exact/9 per family, margins3,
false retirement<=1,breakage<=1 (conservative floor of scaled2/64). If48 fails
projection, stop INCOMPLETE. Deadline checked before and within each generation;
no signals, retries or forced termination. Foreground only. GPU claim requires
empty nvidia-smi compute list and no results/quick-checks/*/RUNNING.flag, with
atomic flag under .review.lock; remove only our own flag after natural cleanup.

Required same-run records: exact user/rendered prompt, full prompt IDs, raw
reply/token IDs/EOS, score, gold/applied events, pair inputs/logits/probabilities,
admission diagnostics, before/after registers, C/O rendered sets/agreement,
provenance intervals/versions, switch-back flags/counts, timings. Per-episode
register traces and summaries accompany raw records. Source hashes checked at
launch and completion. PASS is feasibility on this frozen synthetic cohort only.
