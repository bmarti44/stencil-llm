# Brief: function-vector-focus — Miller's wave on the WEIGHTS: switch on the circuit for an evicted instruction via a function/task vector, instead of (and in addition to) re-reading its text

## Objective
Brian (2026-09-03): "the memories we were turning up were outside the model weights ... we need to turn up the focus on
the weights." Every Qwen wave arm so far biased attention toward CACHE columns (content) and degenerated (checks 4-28).
Miller's wave selects ENSEMBLES IN THE WIRING (the circuit for the current rule), transiently, with clearing. The
testable transformer analogue is a function/task vector (Todd et al. 2024 "Function Vectors in LLMs"; Hendel et al.
2023 "In-Context Learning Creates Task Vectors"): a direction in the residual stream at one layer, extracted as the mean
difference of hidden states between contexts WITH an instruction and WITHOUT it, added during generation so the model
follows the instruction with no instruction text in view. Build it as arms of the corrected-ordering probe
(scripts/clf_probe_check.py, eviction pre-query, 20 H1' sessions, aged constraints / 56; existing arms full 44,
evicted 10, clf_pinned 41, clf_pinned_echo 46, clf_control 13):
1. Vector extraction (GPU, ~minutes; results/qwen/fv-vectors/): for each aged-constraint TYPE present in the 20
   sessions (from the sessions' instruction_id_list; e.g. lowercase, word-count max/min, keyword frequency, forbidden
   words, postscript, title, bullet count), build N >= 16 minimal pairs from data/b3/train-v43.jsonl (dev corpus,
   NOT the 20 probe sessions and NOT any benchmark): the same prompt with and without that constraint sentence.
   Record the residual stream at the final prompt token for layers L in {8, 12, 16, 20, 24}; the function vector for
   (type, L) = mean(with) − mean(without). Save vectors, N, norms, cosine similarity between types (report).
2. Arms (all under pre-query eviction, the evicted constraint text NOT in view):
   fv_inject — for each evicted aged constraint of a known type, add alpha * v(type, L) to the residual stream at
     layer L at EVERY generated position (transient: only during this reply; nothing is added for constraints whose
     type has no vector — counted); alpha and L chosen by a SMALL registered grid on 4 dev-corpus conversations
     (not the probe): alpha in {0.5, 1.0, 2.0} x L in {12, 16, 20}, picking the largest alpha at which the base
     model's greedy output on those 4 conversations is not degenerate (rep4 test); record the choice BEFORE the probe.
   fv_inject_echo — fv_inject on top of clf_pinned_echo (does the circuit add anything to re-injection?).
   fv_clear — fv_inject with the vector REMOVED after the first 64 generated tokens (Miller's clearing; reported).
   Keep every existing arm. Safety per arm as registered (timeouts, truncated, degenerate = rep4 > 0.5 on
   non-truncated, invalid); wave_kill_rule: degenerate > 2/20 kills the arm.
3. Deterministic battery (CPU with a stub trunk where possible; GPU parts when idle): alpha = 0 -> bitwise clf_pinned
   logits; a vector of zeros -> bitwise; injection only at the registered layer and positions; removal at token 64
   restores the unmodified forward bitwise thereafter.
4. Pre-registered reading (write it into the summary before running): helps iff fv_inject >= 30/56 (recovers >= 2/3
   of the 41 − 10 pin gap without any text in view) with paired wins > losses vs evicted and not killed; strong iff
   fv_inject_echo > 46 with wins > losses; harmful iff killed or fv_inject < evicted + 5.
GPU policy: the GPU is BUSY (BFCL shakedown preflight, then the registered 909 restart is queued). Build and test on
CPU; write the exact GPU commands (vector extraction, grid, probe) to WORKLOG; do NOT launch model processes. The
orchestrator schedules the GPU steps. NEVER read the sealed IFEval input file; never touch data/bench/*.

## Allowlist
See function-vector-focus.allow.

## Tests first (TDD, rule 1)
RED first: pair construction from train-v43 (with/without the constraint sentence; N per type), vector arithmetic on
stub states, injection hook placement and the alpha=0/zero-vector identity, the clearing schedule, summary fields.
Run ONLY tests/test_clf_probe_check.py tests/test_function_vector*.py. DO NOT run the full suite.

## Acceptance
CPU tests green; ruff clean; deferred GPU commands recorded; commit EARLY.

## Ledger handoff
Append to WORKLOG.md: constraint types found in the 20 sessions and their pair counts, the grid procedure, the exact
GPU commands in order, ambiguities and choices.
