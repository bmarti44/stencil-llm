# Check43b — frozen reading and execution choices

Unregistered, disclosed, authorized quick check; no fitting or training.
Profile-on: all 32 committed check43 cued Python donor outputs, without filtering.
Select-on: the existing eight check43 Python setup prompts (development reuse).
Evaluate-on: fresh generated banks seeds 96063/96064, Python and JavaScript,
with four prompt formulations; no fit/profile/setup prompt overlap. Same reduction
families recur, so this tests new instances/formulations, not new task families.
Sanity-on: first eight frozen check40c uncued tasks, deliberately reused positive
controls with frozen check40b JS bias times 3/4 (its stored tensor is alpha4).
No evaluation benchmark or sealed input is used. All weights stay frozen.

Teacher-force all existing donor non-EOS outputs. Save raw router logits at EVERY
generated token, plus decoded token/absolute-position maps. Locate each identity literal d after its accumulator assignment (a or acc);
assert literal 0/1. Pair1 first diverges at the variable name, not identity. Report d-2,
d-1,d,d+1 and operator positions. Primary direction uses equal-example means over
[d-2,d-1,d] (two predictors plus the identity token itself). The identity token's
own router logits condition on that literal and predict its successor; they do
not predict the literal. Save all-generated and identity-only directions as
DIAGNOSTICS ONLY. No outcome-driven position/direction selection.
b=(mean_SUM-mean_PRODUCT)/2, expert-center, zero outside layers 7–34.
Sustain the bias on prefill and every decode prediction, as in check43.

Finite setup grid: this ONE primary direction, target band Frobenius norms equal
to frozen JS alpha2 then alpha3 restricted to layers7–34 (~6.8058,10.2087).
At each norm run +b, -b, stable shuffled +b and -b, eight prompts each. Shuffle
uses one expert permutation per layer, seed96062, held fixed across doses/tasks.
Run neutral OFF on all eight BEFORE any selection or setup bias. Run the eight
JS alpha3 sanity requests in the SAME engine; require >=6 valid unbroken JS/8,
otherwise INVALID and no concept conclusion. Save actual dispatch/mixture changes.
Norm equality calibrates magnitude only, and does not assume equal efficacy.
The ~9x figure refers to 6.81/0.722; the alpha3 band is 10.21 (~14.13x old unit).

CONCEPT SELECTED if -b executable PRODUCT>=6/8, malformed<=1/8 and shuffled-minus
PRODUCT<=1/8. Safe qualification additionally requires +b SUM>=6/8 and malformed
<=1/8, both shuffle signs malformed<=1/8, and paired addressed success>=6/8.
Select the FIRST safe cell in low-to-high order after completing the fixed grid.
MARGINAL if any -b has >=3/8 executable PRODUCT but no cell is selected; otherwise
CLOSE concept-level routing on this trunk operationally under this tested recipe.
If the core SELECTED criterion holds but safety fails, disclose SELECTED/NO SAFE
SET and stop; no final is allowed without a safe cell. No dose/direction rescue.

If safe: commit one chosen tensor/hash/dose and setup records BEFORE fresh final.
Final: 8 tasks per seed/language (32), seven arms +b/-b/shuffled+/shuffled-/OFF/
text-SUM/text-PRODUCT; score complete executable functions using unchanged check43
bounded interpreter. Report paired address specificity against swapped, stable
shuffle and OFF, exact one-sided McNemar with Holm, seed/language cells and newly
malformed outputs. Inherit check43 final gates: paired>=24/32, each language>=12/16,
each seed/language>=5/8, advantage>=8/32 over each comparator with Holm p<=.05,
newly malformed<=1/32 per sign, text competence>=15/16 per language/operation,
OFF/shuffle well-formed>=30/32. Collateral: 16 separately authored explicit-cue
tasks, OFF and both signs; require no new task failure versus OFF. Report final
PASS/FAIL/INELIGIBLE separately from the setup reading; no final-based selection.

Cap includes load, kernel, profiling and cleanup: 1440 seconds for setup; increase
to 2700 only after safe selection for final. Cooperative deadlines, no signals.
Before each phase project remaining generations at the slowest measured rate
with 25% reserve: 96 tokens/request for setup; for final, max(64, observed mean
concept-output length), bounded above by the unchanged 96-token request cap; stop INCOMPLETE/COST if over budget. No regeneration/resume.
Foreground only; atomically publish RUNNING.flag under .review.lock after checking
other flags and .venv compute processes; ignore Brian's permanent llama-server.
Delete our flag after natural cleanup. Explicit path commits; no push.
