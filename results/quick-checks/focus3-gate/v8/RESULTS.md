# FOCUS-3 v8 step D — registration (2026-09-06)

Last user-authorized iteration before escalation to Brian. No further iteration,
corrective replay, threshold change or post-score tuning is authorized.

Data lineage: fit-on = committed v7 admission training rows plus >=200 manually
authored sentence-level NONE one-shot requests with payloads across >=10 domains
and >=100 manually authored STANDING-rule positives with nearby payload context,
saved verbatim in data/classifier/ft-enrich-requests.jsonl. The agent writes all
example content in-session; no content-generating script or gate-bank sentence.
Exact bank-sentence overlap exclusion is permitted only as a contamination guard.
DEV = seed-specific 10% normalized-sentence-identity-group split, disjoint from
fit. Evaluate-on = author-disjoint fable-validation* rule/fact held-out once for
fixed seed0 after all models freeze; compare committed v7 predictions on identical
input hashes. This historically reused held-out is diagnostic, not an unseen test.
No benchmark, recorded benchmark response, data/bench or sealed IFEval read.
Historical v7 taxonomy-category patch exceptions remain disclosed and unchanged.

## Frozen rulings (before fitting or running)

1. Admission ft-v3: exactly one refit for each seed0/1/2; seed0 always ships,
   final epoch only. Inherit v7 architecture, pinned BGE revision, paired inputs,
   CLS+4 role features, dropout .1, 3 epochs, batch32, AdamW3e-5, weight decay .01,
   warmup .06, linear schedule, clip1, unweighted CE, max192/only-first training
   truncation and runtime overflow abstention. Admission P(rule)>=.95 unchanged.
   No oversampling, new threshold or seed selection. Report overall DEV metrics
   and NONE admissions on the new request family, including support counts.
   Save data/split/recipe/model hashes and raw DEV/held-out logits; safetensors
   stay local and hash-bound, other checkpoint metadata is committed.
2. COMPLETES: before transition precedence, exclude completion proposals whose
   target scope differs from the completed task's scope or is global (*).
   Keep the existing atomic whole-task completion check and admission bound.
   Unit-test single/multiple targets, global and sibling scope preservation.
3. REINSTATES: require the span itself to pass rule admission without overflow,
   its own admitted semantic key to equal the target's key (no generic-span
   target-key fallback), and target status cancelled or completed. Remove the
   embedded-old-text admission bypass for v8. Cancellation messages cannot
   reinstate: conservatively veto messages with direct cancellation/revocation
   language or any threshold-positive cancels proposal. Apply this only to
   reinstatement; leave other relation decisions and positive admission bound
   unchanged. Unit-test own-key mismatch, both valid statuses, superseded/live
   rejection, low admission/overflow, quoted old text, and cancellation veto.
4. Everything else inherits v7: relation v2 seed0, C thresholds .90/.50/.50/.50,
   C' .50/.50/.50/.50, renderer, histories, banks setup30321/gate30322, readings.
   Preserve earlier runtime behavior via explicit v8 policy flag. ONE CPU setup
   replay must give 36/36 admissions, >=11/12 correct-source transitions, zero
   unauthorized applications and zero overflow; otherwise INELIGIBLE and STOP.
5. Only if CPU eligible: inherited O setup >=15/16, then 64 episodes x C,C',O,N,T,
   greedy64 tokens. Primary exact>=48/64 and >=12/16 each family; C/O stale and
   final-success distances<=4/64; false retirements<=2/64; breakage<=2/64;
   stale C<T; zero contradictory recaps. Secondary reading separate.
   Cap10800 GPU-held seconds including refits; post-setup projection spent +
   1.25*slowest O setup episode*64*5 <=10770. Cooperative cap, no signals.
6. Foreground only; claim v8/RUNNING.flag under .review.lock, wait for other
   Stencil flags and compute processes, exempt Brian's llama-server pid2705.
   Never signal/terminate any process. Preserve prior results and unrelated
   files. Explicit-path force-add commits, README item, WORKLOG, ledger, dated
   relation report; no push. Failed CPU replay ends this gate for escalation.

## v7 cause examination (committed traces, no new inference)

The four reinstatements are setup_1_00 through setup_1_03, turn4, target0:90.
The span is “Reply exactly even.”; admission P(rule) is respectively
.9665188155, .9644694860, .9655144405, .9660175844. Relation P(reinstates) is
.8882029104, .8763505664, .6869024531, .7863613426 (all >=.50).
Each target is a cancelled task sorting row. relation_key(span)=instruction,
but v7 substitutes sort-order from the target, calls it same-key, and permits
the transition because admission passes. This is the direct consumer cause.
The span occurs later in a cancellation episode, not in the cancellation
message itself; the own-key requirement is therefore the operative repair.

The v7 completion's extra row1:0 in setup_2_01 is a falsely admitted inert quote
with scope S2n1A, the same scope as the completed task. Scope filtering alone
cannot repair that polluted same-task row; no extra quote filter is authorized.
The v7 false admissions are ten one-shot requests plus four inert quotes (14
total), as shown by its committed RESULTS, rather than fourteen payload requests.

## Outcome — 2026-09-06

**INELIGIBLE; final-iteration stop-loss applied.** Three refits, the one Fable
diagnostic and the single CPU setup replay completed. The zero-unauthorized bar
fails. No trunk load, O setup, five-arm gate, C' trajectory, corrective replay or
post-score tuning occurred. The gate is closed pending Brian's decision;
[escalation summary](ESCALATION.md) records the remaining failure modes.

| CPU criterion | v8 | required | v7 |
|---|---:|---:|---:|
| Initial ordering admissions |16/16|16/16|16/16|
| Initial tag admissions |16/16|16/16|16/16|
| Switched-task admissions |4/4|4/4|4/4|
| Total authorized admissions |**36/36**|36/36|36/36|
| Correct-source transitions |**11/12**|>=11/12|11/12|
| Unauthorized applications |**12 in 12 records**|0|19|
| Unauthorized admissions |11|0|14|
| Unauthorized reinstatements |0|0|4|
| Unauthorized completions |1|0|1|
| Overflow records |0|0|0|
| Records / traces |96/16|96/16|96/16|
| Cross-key positive proposals dropped |9|diagnostic|10|

Transition recall is supersedes3/4, cancels4/4, completes4/4. Reinstates has zero
gold support, so the absence of false reinstatements does not establish recall.
The unchanged supersedes miss is setup_0_02, P(supersedes)=.5708061676 below .90.
Relation v2, its thresholds and all earlier relation held-out results stand.

The 11 false admissions comprise **eight one-shot payload requests and three
inert quotes**. Payload admission P(rule) ranges .951546638–.980053958; quotes
range .961266665–.976170941. The original setup_0_01 quote remains admitted at
.976170941. Relative to v7, three previous payload errors and one quote error
disappear, while a new payload false admission appears in setup_3_02: the net
payload change is10→8, not ten errors repaired. Full spans and probabilities
are retained in `independent-audit.json` and the raw records.

All four “Reply exactly even.” reinstatement proposals remain visible and apply
as none. Their own key is instruction; each cancelled target's key is sort-order.
New admission probabilities are .955295298, .953612860, .955429129, .947626198:
three still pass admission, and the own-key requirement rejects them; the fourth
also fails admission. No standalone admission escapes the retained positive
proposal bound. There are21 raw reinstatement proposals overall, none applied.

The one unauthorized completion is again setup_2_01 target1:0, previously
polluted by an inert quote. Its scope equals the completed task S2n1A, so it
passes the authorized scope rule along with the real ordering row. No global
row is retired by completion. The scoped guard's synthetic consumer tests pass;
it cannot remove false rules that already have the right task scope.

## Corpus and DEV

All300 enrichment examples were hand-written in-session as explicit JSONL
content:200 NONE and100 STANDING across ordering, tables, code, translation,
inventory, calendar, cooking, geometry, logs and travel (20 NONE/10 rules each).
Each target is exactly one unchanged runtime sentence span; payload forms
include arrays, tuples, objects, escaped CSV, inline code blocks, and multiline
CSV/code in nearby context. Every standing positive has nearby payload context.
No scripted content generation, bank-derived example or oversampling was used.

The base20634 rows are byte-bound to v7's committed `training-rows.json`;
all300 additions survive deduplication/exact bank exclusion. Final20934 rows:
7451none,7731rule,5752fact. The v7 historical282 taxonomy-category patch exceptions
remain; this is a preserved lineage, not a new clean-data claim. No benchmark or
recorded benchmark response was newly read or added. Corpus and source hashes
are in `data-counts.json` and `recipe-freeze.json`.

| Seed | Fit / DEV | DEV correct | Rule admissions at .95 | Non-rule admissions at .95 | New-family NONE admissions | New-family rule admissions |
|---|---:|---:|---:|---:|---:|---:|
|0|18841 / 2093|1989 (95.03%)|668/719|18/1374 (1.31%)|0/21 (0%)|7/8|
|1|18840 / 2094|1977 (94.41%)|719/773|11/1321 (0.83%)|0/20 (0%)|7/7|
|2|18841 / 2093|1985 (94.84%)|722/763|16/1330 (1.20%)|0/18 (0%)|7/7|

The family DEV samples are small and overlap across seeds; do not pool them as
independent evidence. Splits group normalized sentence identity across roles,
labels and context variants; they do not establish paraphrase/scenario separation.
The expanded corpus changes DEV membership relative to v7, so overall DEV is
not a paired comparison. Zero observed family DEV admissions did not transfer
to the gate bank's longer request/payload sentences. Seed0 is fixed throughout;
all seeds run3epochs/1767updates with the inherited recipe.

## Fable diagnostic — one inference, after model freeze

Exactly363 author-disjoint rows, same full rows and source-file SHA-256 as v7.
Only ft-v3 seed0 was inferred; ft-v2 logits were reused from committed v7 records.
Zero full-model-input overlap with fit/DEV; the historical sentence-only collision
“Thanks, that fixed it.” has different context. No held-out data informed fitting,
thresholds, seeds or any correction. This reused set remains diagnostic.

| Metric | ft-v2 | ft-v3 seed0 | delta |
|---|---:|---:|---:|
| Argmax correct |318/363 (87.60%)|318/363 (87.60%)|0, **0.00pp**|
| Rule admissions at .95 |111/124|111/124|0|
| Non-rule admissions at .95 |5/239 (2.09%)|8/239 (3.35%)|+3, **+1.26pp**|

## Verification, artifacts and resource use

122 targeted CPU tests pass, one existing expected failure. Fourteen lifecycle
failures were observed before implementing the v8 guards. Tests cover global
and sibling scope preservation, multiple task completions, own-key admission,
status restrictions, admission boundary/overflow, old-text bypass rejection,
cancellation veto and the actual GPU-launch refusal after ineligibility.
No full-suite invocation or prohibited input reads. Lint and whitespace checks
pass on the scoped changes.

The saved-score runtime audit exactly reproduces96 records without inference
and recomputes DEV/Fable metrics and sentence-group splits. Independent raw
softmax/trainer-input/state accounting passes:59 actions,50 new rows,12 old-row
status changes,214 relation pairs,184 admission spans, zero unexplained changes.
The independent observer initially stopped on missing synthetic audit provenance,
then on matching a prose-only relation span to a payload-bearing admission span;
it now supplies observer provenance and joins spans by source offset, as the
runtime does. Both initial logs are preserved; no scientific source, model,
threshold, record or frozen outcome changed. See `independent-audit-method.md`.
The inherited gold_none.guard_admitted metric is the retired .50 none diagnostic,
not the runtime's admission decision.

GPU-held time is **269.749111/10800 seconds (4.50 minutes)**, entirely admission
refitting. CPU setup replay took16.508058 seconds. No gate cost projection is
needed after ineligibility; all primary/secondary gate readings remain unmeasured.
The foreground fit removed its own RUNNING.flag on natural exit. No process was
signalled or terminated, and no push occurred.

Registration b4b2a0dd; data/implementation freeze be91543c; three model freezes
8ca17554; diagnostic363a9a1d precedes replay. Checkpoint metadata, heads, raw DEV
logits and manifests are committed; encoder safetensors stay local and hash-bound
as registered. [Model inventory](../../../../data/classifier/model/ft-v3/README.md).
This final authorized iteration ends INELIGIBLE with escalation, not another fix.
