# POST-REBOOT NOTE (2026-09-05, power outage at ~18:27; machine up since 18:27)
The previous codex sessions died mid-task; the scratchpad was wiped. Artifacts committed in git are the only state.
GPU: a llama-server owned by Brian (pid 2705, Qwen3.8-27B Q4, ~16 GB) now runs permanently on the GPU. It is NOT a
Stencil job: treat the GPU as available for Stencil when no OTHER compute process (a .venv python) is present; never
touch pid 2705. Memory budget: 128 GB total minus the llama-server; Qwen3-30B-A3B bf16 (~61 GB) still fits. Coordinate
with other Stencil GPU checks via results/quick-checks/<check>/RUNNING.flag files (write yours while running, delete
after; wait if another Stencil flag exists). Never signal any process. All committed prior results stand; re-read the
relevant README/records rather than redoing completed work. Commit with explicit pathspecs; no push.
# Check 49 for gpt-6-astra (GPU <= 30 min, Qwen3-4B dense proxy): LoRA-AS-FOCUS — can a baked adapter HOLD a rule with no text? (2026-09-06)

Fable's dense-focus research (results/dense-focus-research-fable.md; read astra's results/dense-focus-research-
astra.md too if present and reconcile) closes activation/SAE/neuron steering for dense models with citations and
names ONE untested weight-side lever: "Prompt Baking" — distil a rendered rule into a small LoRA so the adapter
HOLDS the rule with no text (the Miller property), and adapter-off = CLEAR. Run fable's QC-A exactly:
- Model: models/qwen3-4b-hf (dense, bf16). Rule: the 40j/40k literal "Live rules: (1) Write all code in
  JavaScript." Bake: rank-16 LoRA (attention+MLP), trained to match the WITH-RULE model's greedy outputs (or KL on
  its next-token distributions) on 200-400 AUTHORED prompts you write (coding requests of varied shape; never the
  32 evaluation tasks; never benchmark items); a few minutes on the GPU. Data lineage: fit-on = your authored bake
  prompts + the model's own with-rule outputs; evaluated-on = the 32 check-40k tasks (hidden tests; disclosed
  second look; no selection) + 16 CLEAR tasks.
- Arms on the 32 tasks (paired): text-only rule (baseline, 4B) | adapter ON, NO text | adapter OFF, no text (=
  OFF baseline). Executable JS via node with the hidden tests; Python/JS identity; breakage. CLEAR: 16 further
  authored arithmetic tasks with the adapter OFF after ON — Python expected.
- PRE-WRITTEN READINGS (fable's GO): adapter-no-text executable-correct JS >= 26/32 AND paired competence
  (losses - wins vs text-only) <= 3 AND CLEAR Python >= 13/16 with adapter OFF AND broken <= 2/32 -> GO: LoRA-as-
  focus HOLDS with no text on the 4B proxy; authorize QC-B (27B) and QC-C (two-adapter interference + 20-round
  HOLD vs rendering under long history) as registered follow-ups. Otherwise NO-GO -> CLOSE the weight side for
  dense models: "rendering + masking is the mechanism; weights are for knowledge" (cite the evidence).
- Also report: adapter size, bake time, and whether adapter OFF reproduces the base model token-for-token on 16
  parity prompts (must be zero diffs — it is a separate weight file).
RUNNING.flag under results/quick-checks/check49/; never signal; outputs (README with readings, bake prompts,
records <= 10 MB, adapter under data/classifier/model/focus-lora-js-4b/ out of git with hashes); item 49 in
results/quick-checks/README.md; WORKLOG (<= 6 lines). Commit with explicit pathspecs; no push; never read anything
under data/bench.

AMENDMENT (orchestrator, after astra's results/dense-focus-research-astra.md "Ranked quick check 1 — two LoRAs as
the persistent focus selector"): ADOPT astra's contract as the registered recipe for this check, reconciled with
fable's QC-A: two rank-8 q/v LoRAs on frozen bf16 Qwen3-4B (mode A = Python, mode B = JavaScript), 128 newly
authored checked examples per mode (CPU-authored reference solutions, <= 96 tokens each under the real tokenizer;
independent executable checkers; mutants validate the consumer), one epoch, cap 256, batch 8, AdamW 1e-4, alpha 8,
one seed, 600-second fitting ceiling. Setup eligibility: cued unmodified A and B each execute >= 7/8; cue-free
default Python >= 7/8. Then 12 independent episodes x 5 decisions (SET, HOLD after one neutral exchange, SWITCH,
BACK, CLEAR; counterbalanced A->B->A / B->A->B), arms M (selected adapter, NO rule text) | T (every-request rule
rendering, no adapter) | X (swapped adapter labels, no text); cold-HOLD probe (carrier kept, old answers removed);
fresh-context OFF and same-history OFF references at each CLEAR; 16 unrelated competence sentinels with/without an
adapter. Rebuild cache/state from the literal history on every adapter change (no masking). Total upper
allocation 272 generations; <= 3,600 GPU-held seconds including load/fit/cleanup. GO = astra's five conditions
verbatim (10/12 M episodes all-active on language AND semantics; cold-HOLD >= 10/12; M > X by >= 3 with exact
paired p <= .05; no new executable failure/truncation in M where paired T succeeds and M all-active >= T; CLEAR
matches fresh OFF >= 11/12 with zero stale impositions and OFF replay parity; shipping relevance = more successes
than T or equal with >= 50% fewer rule-carrier input positions and <= 10% more inference time). INCOMPLETE /
INELIGIBLE are not nulls. Save the two adapters for check 50 (data/classifier/model/focus-lora-4b/{python,js}).
