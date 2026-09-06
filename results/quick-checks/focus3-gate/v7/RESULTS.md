# FOCUS-3 v7 step C — registration (2026-09-06)

User-authorized continuation from committed v6 INELIGIBLE. Fit-on: the original
ft admission corpus/patch policy plus deduplicated sentence-level NONE examples
from the 150 quoted/reported/inert Opus enrich-2 messages and hard-none quoted
Kimi transitions/relations. No gate-bank sentence may enter fit or DEV. The
historical ft lineage and taxonomy-category patch exceptions remain disclosed;
no benchmark inputs or recorded benchmark responses are used. Calibrate-on:
10% sentence-identity-grouped DEV, seed-specific, disjoint from fit. Evaluate-on:
existing author-disjoint fable-validation* rule/fact held-out ONCE for designated
seed0 after all models freeze; compare original ft on that same single pass.
This repeated historical validation is diagnostic, never an unseen-test claim.
Relation v2 and its disclosed second-look results stand; do not reevaluate them.

## Frozen rulings, before running

1. KEY IDENTITY: supersedes/cancels/completes/reinstates only apply if proposal
   key equals target rule key. For an admitted span use its semantic key slug;
   otherwise use the relation head's target key (explicit recognizable field
   references still constrain identity). Provenance IDs remain separate. Drop
   cross-key positives before precedence/admission and count them diagnostically.
   Dropped cross-key positives cannot consume spans or veto new-key admission;
   every remaining threshold-positive pair still bounds admission before kind,
   status or reinstatement filtering. Add CPU consumer tests for all four labels.
2. Admission v2: one refit per seed0/1/2, final epoch only; seed0 always ships.
   Existing ft recipe: base BAAI/bge-small-en-v1.5 revision
   5c38ec7c405ec4b44b94cc5a9bb96e735b38267a, paired context/[role] text,
   CLS+4 role features, dropout.1, 3 epochs, batch32, AdamW3e-5,
   weight_decay.01, warmup.06 with existing linear schedule, clip1,
   unweighted cross-entropy, max192 and only-first context truncation in training.
   Runtime overflow abstention unchanged. Derive quoted negatives from source
   annotations before outcomes; retain complete sentence wrappers, never bare
   quoted imperatives. Dedup/group normalized sentence identity. Source/gate exact
   overlap exclusions recorded before fit. No held-out reads until freeze.
   DEV reports argmax and fixed P(rule)>=.95 operating point; .95 is binding,
   so no DEV or held-out threshold/seed selection. Store all seeds under
   data/classifier/model/ft-v2/seedN and use seed0; safetensors out of git,
   checkpoints and metadata hash-bound by manifest.
3. Everything else inherits v6: relation v2 seed0 C thresholds .90/.50/.50/.50,
   C' .50/.50/.50/.50, positive-proposal admission bound, renderer, histories,
   banks setup30321/gate30322 and readings. ONE CPU replay: 36/36 admissions,
   >=11/12 correct-source transitions, zero unauthorized/overflow, else INELIGIBLE
   and STOP before trunk/O/gate; no corrective replay or post-score tuning.
4. If eligible: O setup >=15/16; gate64 episodes C,C',O,N,T, greedy64 tokens.
   Primary exact>=48/64 and>=12/16 per family; C/O stale and final-success
   distances<=4/64; false retirements<=2/64; breakage<=2/64; stale C<T;
   zero contradictory recaps. Same secondary reading separately, no substitution.
   Cap10800 GPU-held seconds including admission refits. Projection after setup
   = spent + 1.25*slowest O setup episode*64*5; require<=10770. Cooperative
   deadline only; incomplete run INCOMPLETE, no process signals/termination.
5. Foreground only. Claim v7/RUNNING.flag under review lock; wait for other flags
   and other GPU compute processes; Brian's llama-server pid2705 is exempt and
   untouched. Never read sealed IFEval or data/bench. Preserve committed prior
   results, explicit-path force-add commits, no push. Results, CPU records,
   diagnostic counts, manifests/hashes, README, WORKLOG and dated relation report.

## Outcome — 2026-09-06

**INELIGIBLE.** All three admission refits and the one Fable diagnostic inference
completed. The single CPU replay passes the authorized admission and transition
floors but fails the zero-unauthorized requirement. Stop applied: no trunk load,
O setup, gate generation, C' trajectory, corrective replay, or post-score tuning.
Seed30322 was used only for the required sentence-overlap exclusion, not scored.

| CPU criterion | v7 | required | v6 |
|---|---:|---:|---:|
| Initial ordering admissions |16/16|16/16|16/16|
| Initial tag admissions |16/16|16/16|16/16|
| Switched-task admissions |4/4|4/4|3/4|
| Total authorized admissions |**36/36**|36/36|35/36|
| Correct-source transitions |**11/12**|>=11/12|11/12|
| Unauthorized applications |**19 in19records**|0|2|
| Overflow records |0|0|0|
| Records / traces |96/16|96/16|96/16|
| Cross-key positive proposals dropped |10|diagnostic|not enforced|

Transition recall: supersedes3/4, cancels4/4, completes4/4; reinstates N/A,
zero gold support. The unchanged miss is setup_0_02's standing-order switch,
P(supersedes)=.570806<.90. The relation model, thresholds and its prior held-out-2
results are unchanged; no additional relation held-out evaluation was performed.

The specific setup_3_02 key mismatch is repaired: the order span's .949289
supersedes proposal against global TAG is dropped. Its admission P(rule)=.979750
and it becomes a new task-B ordering row. The ten dropped proposals are
seven sort-order→tag and three sort-order→instruction (the latter target false
payload admissions); five supersedes and five cancels. None applies to its wrong key.
Original storage keys, versioning, and renderer are preserved; semantic slugs
are separate metadata. Unnamed/anaphoric relation proposals inherit the head's
nominated target key, as registered; this does not prove semantic correctness.

The admission refit regresses this setup despite its modest Fable improvement:

- **14 unauthorized admissions:** ten one-shot sort-request/payload sentences
  are mistaken for standing rules, plus four inert quoted sentences. The
  original setup_0_01 quoted sample remains admitted, now P(rule)=.978070
  (v6 .960425). Other inert false admissions have P(rule)=.962262–.964633.
- **Four unauthorized reinstatements:** “Reply exactly even.” in each cancellation
  episode passes the unchanged reinstatement admission prerequisite at
  P(rule)=.964469–.966519 and the relation head nominates the cancelled sorting
  row. The generic-span target-key fallback does not reject these proposals.
- **One unauthorized completion:** setup_2_01's valid task completion also retires
  its falsely admitted inert quoted row1:0, a consequence of earlier pollution
  of the register. The authorized task ordering completion still passes.

These are measurements of the combined frozen v7 runtime, not isolated causal
estimates of each modification. No benchmark/gate-sentence fitting or new quote
veto was used to repair the observed outcomes.

## Admission corpus and DEV

The pinned six admission patch files from ft/metrics.json yield20054 original-
lineage rows. Selected source messages:150Opus enrich-2,61hard-none quoted Kimi
transitions,273hard-none quoted Kimi relations. Their verbatim sentence spans
produce582NONE rows. Two duplicate sentences are removed; zero exact gate-bank
sentence exclusions. Final20634: none7251, rule7631, fact5752. Source annotations,
role, preceding sentence context, source row and offsets are retained for every
added example in training-rows.json. No bare-quote reauthoring or gate example
is introduced. Full source counts and dropped rows are in data-counts.json.

Fit18571/DEV2063 per seed; normalized sentence identity is grouped globally,
including role/label/context variants. This guarantees sentence-identity
separation, not scenario/paraphrase independence. DEV never reads Fable.
Three full epochs/1743updates per seed; final checkpoint only, seed0 fixed.
DEV uses the registered fixed.95 operating point, with no threshold selection.

| Seed | DEV argmax correct | rule admitted / gold | nonrule admitted / gold | added-negative DEV admissions |
|---|---:|---:|---:|---:|
|0|1954/2063 (94.72%)|709/765|16/1298|1/64|
|1|1959/2063 (94.96%)|733/784|12/1279|1/66|
|2|1961/2063 (95.06%)|703/757|8/1306|1/61|

The original ft lineage is not a new clean-data claim: its282 taxonomy-category
patch-drop exceptions persist. Pinning the historical six admission patches
avoids newer relation patch files entering the old broad glob. Equal20054-row
cardinality is not proof of exact old training-row identity; the present broad
historical loader gives20069 after later patches. This distinction and the
pre-replay version-preservation correction are recorded in
implementation-correction.md. No fitting recipe changed during training.

## Fable diagnostic: one inference after an unscored preflight

Exactly363 rows from fable-validation.jsonl (the file matching the requested
fable-validation* glob). After all three seeds froze, one evaluation invocation
stopped before model loading/inference: “Thanks, that fixed it.” occurs in both
independently authored sources, with empty training context versus a specific
assistant debugging reply in Fable. Preserve the first receipt/log; correct the
evaluation identity preflight to full paired-input-plus-role disjointness,
retain author separation, report the one sentence-only collision. No row,
weight, threshold, label or split changed. The resumed evaluation makes ONE
inference pass per model, with durable inference-start and raw per-row logits.

| Fable metric | original ft | ft-v2 seed0 | delta |
|---|---:|---:|---:|
| Argmax correct |315/363 (86.78%)|318/363 (87.60%)|+3, **+0.83pp**|
| Rule admitted at.95 |114/124|111/124|−3|
| Nonrule admitted at.95 |9/239|5/239|−4|

Original ft accuracy exactly reproduces its historical Fable metric. The set
has already been used historically; this is a diagnostic comparison, not an
unseen evaluation or model-selection signal. Original model files are unchanged.
Confusion matrices, full raw logits, labels, input hashes and preflight evidence
are retained in heldout.json / heldout-records.jsonl and correction receipts.

## Verification and resource use

**96 targeted tests pass, one existing expected failure.** CPU tests exercise
cross-key rejection for all four labels, admission after rejection, same-key
positive veto before status filtering, target-key fallback, unchanged cross-task
version counts, split grouping and full evaluation-input identity. Lint and
whitespace checks pass. No full-suite invocation.

The saved-record audit replays96records exactly without model inference and
recomputes all DEV/Fable metrics and split identities. Independent action/state,
raw-softmax and trainer-rendering checks pass:66actions,57new rows,12status
changes, zero unexplained mutations. There are229relation pairs and184admission
spans. All10cross-key proposals remain raw in the trace and none applies.
The inherited `diagnostics.gold_none.guard_admitted` field counts the retired
P(none)>=.50 diagnostic; **it is not the v7 admission decision**.

GPU-held time **264.589652/10800seconds (4.41minutes)**, entirely admission refits.
CPU replay16.232166wall seconds; no O-setup projection needed after ineligibility.
Own RUNNING.flag removed naturally. Foreground only; no signals/termination,
sealed IFEval or data/bench reads, gate generations, or push.

Registration301d219d; pre-replay version correction8d132bac; all three seed
checkpoints frozen7d6f4a04; unscored evaluation correctiondd975fbe; diagnostic
result32b86473 precedes CPU replay. Initial and corrected recipe/model-freeze
receipts remain available; the corrections never alter model tensors or data.
Seed manifests hash local safetensors, committed tokenizer/head/DEV metadata.
No claim that all historical corpus bytes or undocumented paraphrases were
independently recovered follows from these receipts. The requested step C ends
at the registered INELIGIBLE stop; the five-arm gate remains unexecuted.
