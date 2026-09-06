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
