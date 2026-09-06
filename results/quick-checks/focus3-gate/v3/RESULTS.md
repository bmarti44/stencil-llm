# FOCUS-3 gate v3 — pre-written reading (2026-09-06)

New user-authorized registration after the v2 bank/spec mismatch. Fit/train/tune:
NONE. Fit-on: existing ft and seed0 relations checkpoints, with the historical
admission development-influence caveats in LABELS.md. Evaluated-on: new synthetic
v3 prose/values, setup seed30311 and gate seed30312. No sealed/benchmark inputs.
Astra re-authors inherited gpt-5.5 scenarios: no independent-author claim for v3.
All eight standing paraphrases are fixed before CPU probe scores and used without
score-based selection. Both directions of v2 and all eight are reported. Runtime
admission segment A is the latest up-to-three preceding user sentences, each with
user: prefix, including earlier sentences of this message; segment B stays
[user] target. Previous-user context matches the available user-only runtime API.
Relation encoding, thresholds .94/.50/.50/.50, admission .95/none-pair .98,
splitter, checkers, request/schema/default-row renderer, greedy cap64 and no
masking are unchanged. Every scored span is logged, even if a relation consumes it.
No outcome-based rescue, filtering, fitting, threshold change or repeat gate.

Bank: 16 setup (4/family), 64 gate (16/family), same four families, six requests
per episode, separate seeded lists. Natural varied standing instructions, overrides,
cancellations, completions, switches/returns; hard-none and prose checks retained.
All bank/source/checkpoint hashes and this reading commit before setup inference.
Diagnostic probe is authorized development inspection, not selection or fitting.

PRE-GATE STOP, first on CPU: replay C and O through all 16 setup episodes using
ordinary user messages only in C. Initial gold ordering admissions must be16/16.
Also require every gold standing admission (tags and new tasks) and replacement,
and every gold cancellation/completion (8 events), to apply to the actual gold
source row. A missing target or merely out-of-scope live target is not retired.
Check exact source text/scope/kind/version/status against O at each gold event.
Any miss -> INELIGIBLE-ADMISSION; stop before loading the trunk or opening gate
inference. Retain all setup per-turn records and traces, including probabilities.
No generated-response metrics are claimed for this CPU eligibility replay.
If eligible, wait for GPU/flags/lock to clear, claim own RUNNING.flag, run O setup
competence>=15/16 using v2 cues; otherwise INELIGIBLE. Recheck C eligibility on
that setup's traces before gate. No retries or setup-selected bank changes.

C/O/N/T definitions, exact state comparison at EVERY task answer (including
initial admission and default rows), scoring, and v2 endpoint readings unchanged.
PASS requires all: C register-exact>=48/64 and>=12/16 in each family; absolute
C/O stale-execution distance<=4/64 and final-success distance<=4/64; C false
retirements<=2/64 (includes missing gold admissions); C breakage<=2/64; C stale<T
stale; zero contradictory recaps; all1536 gate records. N descriptive. No population
or statistical superiority claim. O receives gold events only, never answers.

Fresh cap10800 GPU-held seconds includes load, setup, classification and generation.
V2's measured64 projection3505s fits; conservative original cap projection9454s.
After16 O setup episodes, project elapsed+1.25*slowest_episode*64*4; above10770s
stops INCOMPLETE. Exactly64 or none: no48 fallback in this registration. Deadline
checked cooperatively, no signals/termination/background launches. Empty compute
list and all quick-check RUNNING.flags required under brief .review.lock claim;
write/remove only own flag. Missing work/budget INCOMPLETE; overflow/invariant FAIL.

Same-run artifacts: CPU probe table, setup-admission records/traces/summary,
setup/gate records and traces if eligible (all v2 raw prompt/token/EOS/score,
probabilities/logits/model inputs, gold/applied state, provenance, timing fields),
summary, audits and RESULTS.md. Pre-written reading stays above appended outcome.

## Outcome — INELIGIBLE-ADMISSION

The registered pre-gate stop fired on the complete CPU setup replay. No GPU
claim, trunk load, generated answer, or C/O/N/T gate inference occurred.
The 64-episode gate bank remains unevaluated. GPU charge: **0 / 10800 seconds**.
CPU runtime for the 96 setup updates (excluding classifier load/hash checks):
19.306524 seconds. Check40h held the GPU initially and completed naturally
before preflight; no process was signalled. No GPU flag was needed for this CPU stop.

| Setup obligation | Applied / required |
|---|---:|
| Initial standing ordering rule | **16 / 16** |
| Initial global tag rule | **16 / 16** |
| Override replacement | **0 / 4** |
| New task's standing ordering rule on switch | **0 / 4** |
| Cancellation retires its actual gold target | **0 / 4** |
| Completion retires its actual gold target | **0 / 4** |

Thus standing admissions/replacements are32/40 and retirements0/8. Each family
admits all4 initial ordering rules and all4 tag rules. All8 cancellation/completion
targets still have status live; changing the current task does not count as
retiring a row. No missing-target or absence-as-success interpretation is used.
The mandatory cancellation/completion requirement fails independently of the
conservative additional replacement/new-task checks.

### Admission diagnostic and remaining failure

The complete [P(rule) table](probe.md) reports v2 plus eight standing paraphrases,
both directions, with legacy and training-faithful inputs/logits in
[probe.json](probe.json) and [probe-original.json](probe-original.json).
All eight forms were specified before scoring and retained without selection.
For actual v2 task G0n0A, legacy one-off wording is0.025982/0.026251 (asc/desc);
corrected context raises it to0.488488/0.346745, still below0.95. Standing variants
are0.995771–0.996647. With readable task Inventory the one-off wording reaches
0.972086/0.965954 in faithful context; that result is task-name dependent and
cannot be generalized to the v2 bank. The setup's actual initial ordering-rule
scores span0.995442–0.996621 and all16 are admitted.

The new bottleneck is observed with admitted ordering targets present. Of240
relation pairs,228 are gold none and12 are gold-positive (four each supersedes,
cancels, completes). All240 apply none. Proposals:239 none; one incorrect
reinstates on a live cancellation target (P=0.5934), blocked by the existing
inactive-target condition. Gold-label probabilities on the12 positive pairs:
supersedes0.0218–0.1213; cancels0.0057–0.0800; completes0.0128–0.0249.
This measures missed transitions on this setup, not a universal classifier limit.

All four switched-task standing rules individually exceed admission0.95
(P(rule)0.9547–0.9768), but their eligible relation pairs fail the frozen
P(none)>=0.98 guard, so none are admitted. All32 applied events across the
setup are initial admissions. Thresholds/encoding/bank were not changed after
preflight; no fitting, training, outcome-based repair or rerun occurred.

### Evidence and scope

Freeze commit **b6e40442** precedes the only setup inference pass. The pre-written
reading above is unchanged. [Summary](summary.json),
[eligibility summary](setup-admission/summary.json), all96 same-pass
[per-turn records](setup-admission/records/) and16 [register traces](setup-admission/traces/)
are retained. All184 scored spans have admission probabilities/logits/model
inputs, including relation-consumed spans; before/after states, gold/applied
events,240 pair scores, rendered row sets and agreement are recorded. Overflow0.
No generated-response fields or downstream success/stale/breakage claims are
invented for this CPU-only replay.

[Runtime replay audit](audit.json) passes all96 records, gold state, applied
state, admission inputs, live sets, agreement and frozen hashes. An
[independent recount](independent-admission-audit.json) reproduces event counts
from source IDs/statuses and all saved probabilities from raw logits.
25 targeted tests pass; one existing legacy side-effect inventory xfail;
two sealed-input hash tests deliberately deselected. Ruff and diff checks pass.
The original v2 bank recompiles identically, and its historical artifacts are
preserved. No sealed IFEval/BFCL contents were read, nothing fit/trained, no
background launch, signal/termination or push. Local commits use explicit paths
and force-add the registered results. The frozen stop ends this experiment;
there is no64-episode gate verdict or authorization for another repair here.
