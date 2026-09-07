# Probe-data readiness inventory for gpt-6-astra (CPU ONLY, read-only accounting) — 2026-09-07

Brian's question: can probes measure how aligned the model currently is with its task, fitted contrastively on
aligned versus misaligned examples, with a small 4B judge as the fallback if probes fail? Before any fitting, produce
an exact inventory of what we already have, so the fit can start the moment the research reports land.
PROTECTED: the registered 64-episode larger test is RUNNING. CPU only, read-only accounting. Do not touch the GPU,
any RUNNING.flag, any container, anything under results/larger-test/ (you may COUNT its checkpoint records without
reading their scientific content), or any code. Never signal any process. Never read anything under data/bench.
Deliver results/probe-data-inventory-astra.md answering exactly:
1. LABELS: across results/quick-checks/composition-pilot-{5,6,7} (and the larger test's checkpoints, counted only),
   how many rounds carry a per-obligation adherence outcome from the hidden checkers? Break down by arm, by
   obligation kind (language / indent / format / delivery), by adhered versus violated, and by whether the round is
   a CHANGE round for that obligation. Give the counts, not estimates.
2. MATCHED PAIRS: how many cells exist where the SAME episode and round were run in two or more arms and the arms
   DISAGREE on an obligation (one adhered, one violated)? This is the contrastive set Brian is asking for. Report it
   per obligation kind, and separately report LOCK pairs: within one lane, the last compliant round and the first
   locked round (the lock is defined in results/composition-pilot-5-review-opus.md).
3. HIDDEN STATES: state plainly whether ANY saved run contains model hidden states, and where. Confirm or refute
   that the vLLM path does not expose them and that recovery requires a teacher-forced HF forward pass over saved
   transcripts. If recovery is required, cost it precisely: number of forward passes, tokens per pass from the real
   tokenizer, and the projected GPU-minutes at the measured prefill rate, for (a) all rounds and (b) the matched-pair
   subset only. State the storage in bytes for five layers at float16 for both options.
4. TEXT-ONLY FEATURES: what is available right now with NO GPU at all — the emitted text, the rendered prompt, the
   tool results, the trailer, the diff against the previous file? Enough to fit a text-side baseline detector today?
5. THE MECHANISABLE SPLIT: for each obligation kind, say whether a violation is exactly checkable by code (so a
   validator beats any probe or judge) or not. This determines what a detector is FOR: predicting failure BEFORE
   generation, versus catching what code cannot check.
6. LEAKAGE AND SPLITS: what is the correct split for fitting (leave-episodes-out, and leave-obligation-kind-out for
   genericity)? Which banks and episodes are exposed, per the handoff exposure table? Write the data-lineage line a
   future fit must use, and name anything that would contaminate the running experiment or its evaluation bank.
7. VERDICT: with the counts in hand, is a contrastive probe fit feasible now, at what GPU cost, and what is the
   minimum viable version? Say plainly if the answer is that we should wait for the larger test's records.
Write ONLY that one report file; commit with an explicit pathspec (git add -f); no push.
