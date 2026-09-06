# Saved-record verification

`CUDA_VISIBLE_DEVICES='' .venv/bin/python -m scripts.focus3_gate_v8 --mode audit`
verifies the frozen recipe/checkpoint hashes, normalized sentence-group split
identities, DEV/family/Fable metrics, and exact runtime records using the stored
classifiers' scores. It performs no model inference or fitting. This is a
saved-score accounting check, not a second scientific CPU replay.

`CUDA_VISIBLE_DEVICES='' .venv/bin/python -m scripts.audit_focus3_v8` independently
counts actions, created rows and changed prior rows from before/after snapshots.
Every change must have an exact action/span/provenance id; no row may disappear.
It independently matches actions against the gold event multiset and recomputes
raw softmax probabilities at1e-12 tolerance. Each relation input is normalized
and rendered by the trainer and must match the saved runtime model input.
Completion targets must have the explicitly completed task's non-global scope;
reinstatements require the span's admitted key and valid retired status.

The observer was committed before CPU outcomes. Its first invocation aborted
because the training normalizer requires author/source metadata that runtime
pair objects do not contain. Adding observer-only source provenance reached a
second mismatch: relation prose can omit a payload suffix retained by admission.
The observer now associates the spans by source offset and uses the admission
span, matching the runtime consumer. Initial and source-only failure logs remain
in this directory. These are observer repairs only; scientific sources and
frozen data/model/record hashes remain unchanged. No new inference or score
selection occurred. The final independent audit passes96records,59actions,
50new rows,12status changes,214pairs,184admission spans and zero unexplained changes.
