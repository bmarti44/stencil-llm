Focus synthesis — gpt-6-astra, 2026-09-05. Evidence assessment and proposed test; no experiment authorized or run here.

On the frozen Qwen trunk tested here, the working account is that what governs the next answer is what the query
can attend to in context, with a recency-weighted ordering: a current-position instruction > the model's own recent
outputs acting as demonstrations > a standing instruction at an old position. This account is scoped to these histories:
role/wording were not isolated from position, and attention weights were not measured. Checks 31–33 found no useful compact
transplantable task state: extracted vectors, averaged four-column suffix K/V packets, and sustained or one-shot coordinate
replacement failed to supply control despite readable task identity. These recipes are closed; other distributed, nonlinear
or learned representations remain possible. Checks 32/33 also missed their text-competence eligibility bars.
Check 34's actual instruction-cue K/V columns supplied SET and behavioral HOLD without reapplication; K and V jointly
worked, either alone did not, and layers >=12 sufficed for immediate induction. But the same-history all-layer write
reconstructs the text prompt's cache by construction; tiny neutral-prefix changes do not establish general transfer.
Thus the demonstrated route to frozen-trunk “focus” control is placement (where the governing instruction sits) plus
eviction (which own outputs remain), not an added signal; reliable combined control remains unproved. Relative to
Miller, this implements selection and release by changing which context columns exist and where instructions enter;
it establishes neither waves nor transient selection of identified weight circuits. Earlier pin+echo retained old
instructions and placed their text at the current position; evicting stale own outputs is the complementary release.

The decisive evidence is [35](quick-checks/check35/README.md) plus [36](quick-checks/check36/README.md): old-position
SWITCH scored 2/32 after both downstream recomputation and full text rebuild, with identical generated outputs
(not bitwise-identical caches); the current-user text cue scored 27/32. Stale K/V alone therefore cannot explain
the failure. No tested cache arm solved SWITCH; release+recompute reached 17/32, but BACK fell to 14/32, only 5/32 strict.
Across check 35's release arms, CLEAR and its follow-up copied in 25–28/32, versus zero copying and 32/32 impositions
for its neutral-text CLEAR baseline. Yet no arm passed the fixed two-request CLEAR rule: some sorting returned.
Repeated body/EOS deletion also leaves malformed empty assistant turns: even the intact-A control fell from 27/32
to 17/32 after the second deletion. Structure damage is an observed limitation; repair is still a hypothesis.

Yes: Brian's quick-test-first rule warrants one deeper test. Recency, restatement and few-shot imitation are prompting
folklore. New in this record: standing instructions lose to own demonstrations even after recomputation; deleting those
demonstrations restores much of neutral behavior where the tested reminder fails; matched cue K AND V are needed together.
That is a measured mechanism worth checking, not established literature priority.
“Eviction beats text at CLEAR” must mean this neutral reminder: explicit cancellation, an explicit default request,
and text-history editing/re-prefill were not beaten. The larger test must include those stronger alternatives.
This earns a context-management claim if it generalizes safely, not a compact-state, oscillator or Miller claim.
Sources: [31](quick-checks/focus1-probe/README.md), [32/Q4](quick-checks/check32-kv/README.md), [33](quick-checks/check33/README.md),
[34](quick-checks/check34/README.md); accuracy reviews [31](check31-review-fable.md), [32](check32-review-fable.md),
[34](check34-review-fable.md), [35](check35-review-fable.md); [queue](quick-checks/README.md) and [drift assessment](astra-drift-assessment.md).

Proposed larger test: at an instruction change, place the new instruction at the current user position and remove own
outputs under the superseded instruction, preserving valid turns. An oracle change/scope map uses only public instruction
events and turn ownership, never answers; this tests control, not autonomous detection. Frozen Qwen3-4B, bf16/hf_compatible,
greedy, thinking disabled; caps 64 new tokens for synthetic tasks, 256 for Multi-IF. No controller or fitting.
Lineage: fit-on=none; development=checks 31–36 plus fresh synthetic repair fixtures; evaluation=new disjoint synthetic
episodes, then Multi-IF solely as post-development evaluation. No benchmark prompts, responses or scores may alter
templates, policy, repair choice, thresholds or checkers; never access sealed IFEval inputs or sealed BFCL contents.

First, a <=0.5 GPU-h repair check on 32 fresh synthetic episodes: repeat two releases with the same cue still active,
then cancel and ask two neutral questions. Pair intact history, old body/EOS deletion, whole user+assistant-pair deletion,
and replacing the entire assistant body with a period (CPU-verify it is one token) while retaining valid closure.
Keep standing-instruction event turns separate; whole-pair removal includes the user turn. Compare surviving-cache deletion
with the same edited text history rebuilt at matching absolute positions. Score strict validity, active-task and neutral accuracy.
Preselect placeholder replacement for the larger test, since it preserves user facts; whole-pair removal is diagnostic.
Proceed only if placeholder repair has no additional broken episodes, loses <=1/32 active-task successes versus intact
history at each release, and copies >=26/32 at BOTH neutral requests. Otherwise stop; do not promote a lucky variant.

Freeze 256 paired episodes (64 each: sort direction, letter case, field selection, output representation), balanced across
change directions and 0/512-token delays, with fresh operands and two earlier actual model answers retained unscreened.
After SET/HOLD, score SWITCH, an unrefreshed HOLD, BACK, CLEAR and a second neutral request; intervene only at changes.
Include still-active constraints and later-needed user/tool facts, so deleting useful history cannot count as success.
Separate competence fixtures require >=29/32 per cued skill; failure stops the study. Seeds: repair 9053701, competence
9053702, final 9053703; deduplicate inputs across banks. Freeze generators, prompts, scope masks, checker mutations and hashes.
Five paired arms: neither = update the old instruction slot, keep own answers; placement-only = move that update into
the current user turn; eviction-only = old-slot update plus repaired answer removal; both = current placement plus
removal; text-restate = keep answers, explicitly cancel superseded rules and restate all live rules/default at EVERY
scored request. All arms retire superseded cue text identically; CLEAR leaves only baseline rules. Operands remain paired.
For the main comparison, rebuild each edited text history with the same valid renderer; this removes stale-K/V and
malformed-turn explanations; no recompute-free speed claim. Save replies, turn/position/removal maps, scores, impositions and cost.

Primary endpoint: fraction of episodes with ALL five post-change answers satisfying every live constraint and the
task checker, including both neutral answers; invalid/empty/truncated/repetitive outputs are failures, never release.
Use episode-paired exact McNemar tests for both versus placement-only, eviction-only and text-restate, Holm-adjusted
at .05; report paired 95% intervals and each checkpoint/family. Require all three positive/significant and >=5 percentage
points over text-restate. Safety requires zero newly broken episodes versus text-restate, strict schema checks, and no
increase in collateral fact/unchanged-constraint failures; statistical evidence and practical magnitude are separate gates.
Zero new breakages in 256 still allows a one-sided 95% rate bound of 1.16%; it is not proof of harmlessness.

Only after a safe synthetic pass, evaluate Multi-IF turn 3: identify explicit changes/overrides from public instructions
without outcomes, hash-order up to 128 eligible conversations, all if fewer; freeze the slice and disclose exclusions.
Use native turn-3 constraint checkers, score ALL live constraints, and replay identical unscreened own turn-1/2 answers
across arms. Preserve the native current user cue: here “neither” is native full history and “placement” adds a current
recap, not an artificial relocation of the benchmark cue. Report the same paired contrasts and safety; no benchmark
revision or rerun. Synthetic success alone is scoped; safe benefit beyond current text on Multi-IF supports transfer.
SC1's scope/checker code is an alternative for fresh override/cancel episodes; reuse primitives, leaving its shelved study/banks alone.

Cut Q5 learned controllers and Q6 gate searches now, the declined Q2, more vector/packet/dose grids, 1.7B sorting,
cross-model fleets and a revival of SC1 authoring/governance. Cut claims that every transplant route is impossible.
If both ties placement/text, call this prompting; if repair loses CLEAR gains, call release fragile; if safety fails,
do not promote it. Order: CPU freeze/checkers -> repair (0.5 GPU-h) -> synthetic (4 GPU-h) -> frozen Multi-IF (5.5 GPU-h).
Planned total 10 GPU-h; 2 GPU-h reserve, HARD TOTAL <=12 including loads, competence, timing and diagnostics. Foreground
timing pilots must project the fixed work within the cap; otherwise defer/report INCOMPLETE. GPU use for this synthesis: zero.
