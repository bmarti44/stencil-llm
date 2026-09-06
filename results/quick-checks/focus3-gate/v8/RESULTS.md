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
