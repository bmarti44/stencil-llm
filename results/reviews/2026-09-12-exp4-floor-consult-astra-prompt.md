You are Astra, consulted read-only under rule D10 of plan/BACK-ON-TRACK-PLAN.md ("a result
whose reading is not in the exhaustive list" / "a registration choice the plan does not
cover"). Do NOT read anything under data/bench/. No models, GPU, network or file writes.
Recompute any number you rely on from the records named below.

Goal (Brian, rev 7): one published HF model artifact (`bmarti44/stencil-focus-qwen3-1.7b`,
deploy/stencil_focus/) that keeps following the relevant instructions over a long coding
session, PROVEN against the identical artifact with the modification off. The proof is Exp 4
(results/memorycode-long/REGISTRATION.md with amendments 1-2 and the BUDGET line): paired
strict convention compliance, focus (role_evicted restatement of the truncated-away mentor
sentences, 256-token budget, token-matched window W=3,584) vs base, N=128 SCREEN-LONG,
Qwen3-1.7B only.

The stuck condition (observed tonight, before any SCREEN-LONG generation):
1. Exp 3b (results/memorycode-derived/setup/, 16 SHORT items that fit 3,584 tokens, 4 arms):
   strict compliance 0/16 on EVERY arm including `oracle` (the label-derived live
   instructions, 16-34 tokens, restated right before the request). Mean fraction: history
   .057, restate_all .082, auto .120, oracle .051. Eligibility gate (history >= 6/16) FAILED →
   INELIGIBLE at 1.7B; the contract's one retry on Qwen3-4B is queued on the GPU now
   (results/memorycode-derived/setup-4b/ when it exists).
2. Exp 4 SETUP-LONG (results/memorycode-long/setup_long-role_evicted/, 9 of 16 items done;
   the rest are generating): strict False on every arm of every item, base/focus/oracle
   alike. Fractions move a little (e.g. 314-49 .364 all arms; 302-49 base .214 vs focus .143).
   The focus reminder kept 16-20 sentences (241-256 tokens) of 172-2,075 evicted candidates;
   the oracle reminder is 1-2 sentences on most items and EMPTY on several (no instruction
   live at that session in the labels).
3. Spot checks of the generations (read a few records): the model writes plausible code and
   even paraphrases the conventions in prose ("function names must start with gn_") and then
   does not apply them. The checker (vendor/memorycode compute_score, CONTRACT.md amendments
   3/3b) is right on the examples inspected.

Reading: the registered primary cannot move on this trunk (a floor at strict; the ceiling arm
is zero). Running the 128-item SCREEN as registered would almost surely read NOT PROVEN for
lack of resolution, not because the mechanism is useless. The plan has no reading for this.

Candidate paths (Brian asked for the most likely options; each is a NEW registration, none may
be slipped into the current run; the artifact must stay "same model with the modification
off" as the control):
 a. Trunk to Qwen3-4B (artifact renamed), keeping everything else; gated on the 3b 4B retry.
 b. Change the primary estimand from strict to the fractional family score (paired mean
    difference, bootstrap interval) on the existing trunk.
 c. Attention amplification of the reminder span (the repo's pre-softmax additive bias path,
    `src/stencil/qwen3.py` bias_hook; Exp 2a's `fixed_bias` arm design; the internal-wave
    controller w0-ce). Repo history: static bias −4.6 (n=196), gated cache-column bias
    degenerated 5/20 (check 28), wave +1.7 over prose reinsertion (1 seed, more breakage).
    Requires a custom attention forward in the remote code and re-proving the off-switch.
 d. LLM-written synopsis ("rules in force" note rewritten every N turns by the model itself,
    MemGPT/Mem0 style), injected like the current reminder.
 e. Relevance ranking of the evicted sentences (encoder similarity / BM25 to the request)
    instead of newest-first packing.
 f. Register repair: eviction instead of skip at the 16-row cap, higher admission precision,
    make the relations head actually retire rows (0 relations applied on SETUP-LONG,
    results/memorycode-long/auto/summary.json).
 g. Reminder placement/phrasing: system-level "apply these conventions" block, or a
    checklist format, or few-shot examples of applying a convention.
 h. A different/derived workload where small models can comply at all (e.g. a subset of
    MemoryCode families the 1.7B model follows under oracle; or a narrower compliance
    outcome), registered with the floor measured first.

Questions:
1. Which of a-h (or something not listed) are the most LIKELY to yield a PROVEN reading
   within ~10 GPU-hours, honestly ranked, with the mechanism of why each would or would not
   escape the floor? Use the repo's own evidence (Exp 1 RESULTS.md: role_echo_only +11.98 on
   Multi-IF where the trunk CAN comply; FOCUS-3 v8 on Qwen3-4B 57/64 vs 29/64; larger-test-v2
   on 30B) and the records above.
2. What is the smallest registered quick test for each of your top three (items, arms,
   outcome, n, what reading kills it)?
3. Is there any reading of the Exp 4 SETUP-LONG + 3b data under which the registered SCREEN
   should still run as is? Say so if yes.
4. Any defect in how we are interpreting the floor (checker, applicability freezing,
   prompt construction, the empty oracle reminders) that would change the diagnosis?

Output: numbered findings with file:line evidence, a ranked recommendation table
(option, probability of PROVEN, GPU-h, what it costs the artifact's claim), and the three
quick tests. Constraints to respect: never fit/select/tune on evaluation benchmarks; one
control = same artifact with the flag off; Apache-2.0 / transformers-only packaging
preferred but a modified attention path is allowed if it is the only way. End with
"No files written, models/GPU/network used, or data/bench/ contents read."
