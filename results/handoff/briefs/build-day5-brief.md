# Day 5 for gpt-6-astra: DEV pilot of the composed package on the GPU — cost, pressure, competence, renderer freeze (2026-09-06)

Governing: results/focus-mechanism-composition-v2-astra.md section 2 + addenda (12 GPU-h budget; actuator OFF —
check 40k read R3 harm; 40l pending is diagnostic only), fable's bank review results/slab-bank-review-fable.md and
the bank fix pass WORKLOG entry (read it; confirm all four HIGHs closed and manifests re-frozen; if any HIGH is
still open, STOP and report — do not pilot on a broken bank). Package: src/stencil/focus/**, models/stencil-package/.
Pilot (GPU; write results/quick-checks/composition-pilot/RUNNING.flag; never signal; one model load; cap 1.5 GPU-h):
1. Wire the real trunk: Qwen3-30B-A3B HF bf16 through custom_generate (the package's dispatch path, not a bypass);
   KV retained within an episode; greedy; per-round cap 512 generated tokens; the frozen system prompt; the real tool
   executor (sandboxed) from slab.py. Pre-flight on CPU-stub first, then GPU.
2. Run the DEV episodes (8; both 16- and 32-round shapes present) under arms R (register + every-request rendering,
   explicit entry driven by gold events for DEV only — state that clearly), N (ordinary history), T (evaluator
   text restated every request) — O is identical to R on DEV when events are gold; say so. All arms, all DEV
   episodes, if the cap allows; otherwise the fixed subset rule from v2 (freeze which before starting).
3. JOURNAL, in the same run, every field of v2 plus: per round the HIDDEN STATE at the last prompt token for layers
   {8, 16, 24, 32, 40} (bf16 -> float16 .npy per round, keyed by episode/round/arm) — this is for check 45 (off-task
   probe) and costs no extra forward; also the mean hidden state over the generated tokens for the same layers.
4. Measure and report: per-arm max context tokens (must be <= 32,768 with margin), own-body token distribution vs
   the 100-300 band, relapse opportunities and observed relapse per rule kind per arm (with denominators), final
   success / stale execution / wrong skill / breakage per episode and arm, truncation rate (cap gate 2%), tokens
   and seconds per round, prefill and decode tok/s, GPU-held wall time — then the COST PROJECTION for the full
   4-arm x 64 (+ O/T subset) run against 12 GPU-h with measured numbers only.
5. RENDERER FREEZE: the exact rendered bytes of R for one DEV episode are committed as the frozen layout (golden)
   after the pilot; no changes to the layout after this commit without a registered amendment.
6. PRE-WRITTEN readings: ELIGIBLE = projection <= 12 GPU-h AND max context fits AND truncation <= 2% AND R's own
   bodies mostly in band AND at least one arm shows measurable relapse opportunities with nonzero denominators per
   kind; else INELIGIBLE with the failing item (fix on CPU; no silent shrinking of N). Also report the DEV-only
   contingent mask trigger check (v2 section 3: >= 15% relapse on some kind, >= 20 opportunities, >= 2 episodes).
Data lineage: DEV episodes only (family disjoint from the 64 evaluation episodes by template and seed — never open
an evaluation episode); no benchmark data; gold events used only in DEV. Outputs under results/quick-checks/
composition-pilot/ (README with readings, records, hidden-state .npy under a hidden/ subdir — git add -f only the
README/summary/records, NOT the .npy; list them in a manifest with hashes), item in results/quick-checks/README.md
(5 lines), WORKLOG (<= 6 lines). Commit with explicit pathspecs; no push; never terminate or signal any process;
never read anything under data/bench.

ADDED after fable's round-2 bank review (results/slab-bank-review-fable-r2.md): (a) FIRST fix N1 on CPU — when the
previous file is unparsable, changed_code (slab.py:808-809) falls back to the whole rewrite so a verbatim repair is
scored as style violation + relapse; diff against the last PARSABLE snapshot instead; add the test; re-freeze
fixtures; (b) the runner must call paired_context_gate before rendering any arm; (c) COST: the CPU projection is
13.34 GPU-h sequential (decode-bound) vs 12. In the pilot MEASURE batched decoding: run the four arms of one episode
as a batch of 4 sequences (and/or 4 episodes of one arm) with independent KV/masks, verify per-sequence outputs are
byte-identical to sequential greedy on one DEV episode (batch invariance check; if not identical, report and fall
back to sequential), and report the projection BOTH ways (sequential and batched) against 12 GPU-h. Report the
language relapse row as zero-by-design.
