# FOCUS-3 v8 diagnostic — registered 2026-09-06

DIAGNOSTIC — the registered eligibility stop was not met; readings are reported but no PASS/FAIL label is assigned; this run informs the admission-detector redesign only.

Direct user authorization permits one five-arm diagnostic despite v8 CPU
ineligibility (12 unauthorized actions: eight payload requests and three inert
quotes admitted, plus one completion of a wrongly admitted row). Prior v8
eligibility and all committed results stand. No runtime repair or threshold change.

Data lineage: fit/train/select/tune in this task = NONE. Frozen relation-v2 seed0
and admission ft-v3 seed0 retain their disclosed development lineage in v6/v8.
Evaluation = committed v4 synthetic bank, setup30321 (16) and gate30322 (64),
reused development templates; no independent-scenario/population inference claim.
No sealed IFEval input, data/bench, or recorded benchmark responses are read.
No fitting uses any diagnostic input or answer.

Use the inherited Qwen3-4B dense bf16 trunk, full independent arm histories,
greedy64, thinking disabled, renderer/checkers and all v8 rules as-is.
C primary (.90/.50/.50/.50); C' alternative (.50/.50/.50/.50); O gold live register;
N none; T naive restate-all. Fixed shuffled arm order uses seed30303.
Run all16 O setup episodes; report competence descriptively, never select by it.
Before any gate inference write selection.json: projected GPU-held time = elapsed
+1.25*slowest O episode*n*5, plus a separately itemized false-admission probe
allowance (two candidate arms, setup v8 exposed-row/turn count scaled by n/16,
1.25*slowest O episode/6 per probe). Choose64 if within7170s; otherwise48
(first12 per family in existing bank order) if within7170s; otherwise stop with
unmeasured work recorded. Selection depends on resource use only.
Fresh cap7200 GPU-held seconds includes load, setup, classifiers, generation,
probes and cleanup. Cooperative deadline at7170s; never signal any process.
Foreground only, own diag/RUNNING.flag under .review.lock; wait for other flags
or Stencil compute, exempt Brian's permanent llama-server. No push.

Report inherited v3 episode endpoints for all arms, pooled and by family:
register-exact at every task answer, stale executions, final success, false
retirements (including missing gold admissions), breakage and contradictory
recaps. N/T register endpoints remain not applicable per v3. Add false ADMISSIONS
as a separate episode-count row and action count; unauthorized actions by family
and label for C/C'. Descriptive paired C-vs-O and C-vs-T endpoint differences
and discordances, no gate decision or statistical superiority labels.

For EVERY false admission, save its source row, admission probability, all later
turns, whether the row is rendered, actual answers/scores, later row status and
paired O/N/T answers/scores. After the complete five-arm gate, probe each rendered
false row once per exposed turn, removing ONLY that row from the CURRENT recap
and retaining the candidate's exact original prior history. Save raw prompt IDs,
output IDs/EOS/text/timing and scores in the same run; never feed probe answers
back into an arm. This measures the immediate effect of rendering that row
conditional on the polluted prior history, not the total causal effect of never
admitting it. Count token/text changes separately from semantic JSON/task/tag,
stale, success and breakage changes. Unrendered rows have zero direct current
recap exposure, not proof of no historical effect. If budget ends, preserve and
report every unfinished probe; do not rerun or imply it was measured.

Sources, bank and frozen checkpoint hashes are committed before O setup. Record
same-run raw per-turn records/traces, selection, summary, effects/probes, resource
use, deterministic saved-record verification, README item, WORKLOG and ledger.
Only new diagnostic files and explicitly named report files are committed.

Outcome: registered; inference has not started.
