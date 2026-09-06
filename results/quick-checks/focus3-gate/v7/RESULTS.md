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
