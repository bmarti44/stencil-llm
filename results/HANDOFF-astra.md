# HANDOFF PROMPT for gpt-6-astra — Stencil focus mechanism (written 2026-09-06, evening)

You are taking over as the orchestrating engineer for the Stencil project at /home/bmarti44/stencil-llm (Brian
Martin's repo; GB10 machine, one GPU, aarch64, CUDA 13). Read this file, then AGENTS.md, then the files it points
to, before doing anything. Work autonomously; report in plain language; never stop on a blocker — research your
way through it.

## THE GOAL (Brian's standing instruction, verbatim)
"continue finding a generalized way to implement a miller inspired focus mechanism. use fable, sol, and kimi sub
agents to review your work for accuracy. do not over engineer. make sure you can iterate quickly to prove out a
hypothesis, and only continue after you have adequate proof on a larger implementation. if you get stuck, do not
stop, spin up fable, sol, and kimi sub agents to do deep web research to get you unstuck."

Miller's idea: knowledge is stored in the weights ("synapses store"); a separate selection process decides which
stored competency/instruction governs now ("waves select"): SET, HOLD, SWITCH, CLEAR. The practical target: an AI
coding agent that keeps the right instructions in focus over long sessions — remembers standing rules, notices
when they change or are cancelled, switches tasks cleanly, does not relapse into old habits. Brian later
sharpened it: the agent must be auditable and generic; automatic control from natural conversation is the
remaining research problem; steering the model's internal skills is worth shipping ONLY if it makes the model
better at the task (it did not); a rule/skill baked into an adapter is worth testing; an off-task probe (predict
a violation from hidden state before generation) is worth testing.

## HARD RULES (never violate)
- Eval-data separation: NEVER fit/select/tune on any evaluation benchmark data. NEVER run or read
  data/bench/ifeval_input_data.jsonl (sealed; only tests/test_sealed_guard.py may read it). Do not modify
  data/bench/* or results/qwen/b4-multiif-base. Write the data-lineage line (fit-on / evaluated-on, disjoint)
  FIRST in every registration and brief. Never lift probe/benchmark exemplars into label specs or prompts.
- Pre-register: write the pass/fail READING before running anything; one look at a held-out; no threshold or
  prompt changes after the look; INCOMPLETE/INELIGIBLE are not nulls; never shrink N silently.
- Review: every result gets a one-round accuracy review by an independent reviewer ("fable" = Claude agent;
  Opus for data audits; kimi-k3 via ollama writes data). Reviewers write only their review file.
- Process ownership: register every background launch (`echo $! >> .stencil-owned-pids`); never stop a process you
  did not launch without Brian; stop/rm only your own containers; GPU coordination via RUNNING.flag files under
  results/quick-checks/<check>/ — wait for any other flag to clear; never signal other processes.
- results/* is gitignored: commit registered artifacts with `git add -f` and explicit pathspecs; NEVER commit files
  > 10 MB (keep streamed journals out with size+sha256 manifests); no push unless the orchestrator says so; HF_TOKEN
  is in the environment — never print it; Hub push only after the registered PUBLISH GATE as bmarti44/stencil.
  ANTHROPIC_API_KEY is in the environment — never print it; do not spend on it without Brian's approval.
- Do not over-engineer. Rank hypotheses -> quick prove/disprove check (<= 1 GPU-h) -> review -> only then a larger
  implementation. Three failures of the same bar = park the line.
- Register design rulings (Brian): no string matching/regex in the register path (typed fields or classifiers);
  retirement by masking, NEVER deleting history; every live obligation rendered in EVERY request; one HF repo
  download ships everything (frozen trunk + classifier weights + controller code + custom_generate).
- GPU budget for the registered larger test: 12 GPU-hours for the run itself (prior pilots are development
  cost); pre-registered 12-round fallback if the projection is 12-15 h; never fewer arms.

## WHAT IS PROVEN (with reviewed evidence)
- The instruction half: an external RULE REGISTER (immutable event log; versions; scope; kind; provenance; live
  view = mask; `target_version` required; idempotent events; reinstates = new version) + EVERY-REQUEST RENDERING of
  all live obligations controls a frozen trunk end to end. Check 42: rendering cadence decisive (151/192 vs 131).
  FOCUS-3 oracle 63/64 vs ~30 baselines. Built and reviewed: src/stencil/focus/{register,renderer,loop,journal}.py,
  models/stencil-package/ (HF custom_generate; real dispatch tested), 159+ tests.
- Attention MASKING of the model's own stale outputs = certified reversible RELEASE (checks 40h/40i) — but adds
  nothing when the rule is rendered (40j); kept as a flagged contingency triggered only by measured relapse.
- First real arm signal (pilot 4): substitution traits — delivery->ready after `completes`: R 20/33, T 15/44,
  N 0/37.
- Backend: vLLM bf16 (vllm/vllm-openai:cu130-nightly, VLLM_BATCH_INVARIANT=1, prefix caching, max-num-seqs 4)
  QUALIFIED: deterministic across three passes; HF path differs on 4 distinct prompts of 48 (near-ties,
  disclosed); one frozen backend for all arms is the validity rule (results/quick-checks/vllm-qual/).

## WHAT IS CLOSED (do not reopen without a NEW hypothesis)
- Router-logit bias skill steering on the MoE (40g/40j/40k/40l): flips language only on a weak prompt prior;
  HARMS competence at the certified dose (16/32 -> 7/32, p=.022); competence-direction bias = reply-length
  confound. Oracle-correct bias = open and unfunded.
- Dense-model activation/neuron/SAE/KV-transplant steering (31-33, 41, 41b, 43/43b; both research memos).
- Concept-level routing (43/43b).

## WHAT IS PARKED (assistive only; reopen conditions in the reviews)
- Automatic admission (standing-rule detection) — checks 44/44b/44c NO-GO (recall 64-73%; root cause: phrasing
  coverage — cue-less rules, multi-rule lists; and a splitter ceiling); check 46 (frozen 30B trunk as updater,
  zero-shot) NO-GO but best recall yet (79%/90%; relations 89%, supersedes 87%).
- Relation refits (v3 NO-GO; held-out-3 is a harder bank, not a regression; v2 ships assistive).

## THE MODEL
Trunk: Qwen3-30B-A3B (MoE) at models/qwen3-30b-a3b-hf (bf16). Candidate switch: Qwen 3.8 27B dense (local FP8 +
GGUF under /home/bmarti44/models/qwen3.8-27b*; no bf16 yet — 54 GB download needs Brian's disk OK; disk ~96% full).
VERIFIED: Qwen3.8-27B = 48 linear-attention (GatedDeltaNet) + 16 full-attention layers -> KV-mask release reaches
only 16 layers; recurrent state is not maskable; the backend must be re-qualified for a hybrid model.
Small dense models for classifiers/proxies: models/qwen3-1.7b-hf, models/qwen3-4b-hf. Encoder: bge-small.

## QUEUE STATE AT HANDOFF (check the scratchpad chain logs and results/quick-checks/README.md)
GPU order (each gated on the previous and on RUNNING.flag): check 47 (Qwen 3.8 27B screen) -> 48 (Qwen3-4B
generative register-updater LoRA; fresh fable held-out-4; readings in the brief) -> 49 (two rank-8 LoRAs as the
persistent focus selector on 4B: SET/HOLD/SWITCH/BACK/CLEAR, arms M/T/X, astra's five GO conditions) -> 50 (skill
adapters per language: SKILL-GAIN / SELECT / SWITCH-CLEAR) -> pilot 5 (SLAB-2 simplified harness, 8 DEV episodes
x R/N/T at 16 rounds; ELIGIBLE readings in the brief) -> the LARGER TEST (64 fresh agentic episodes, R vs N
primary, O/T nested, Q capability-qualified subset, per-kind relapse, <= 12 GPU-h) -> check 45 (off-task probe on
recovered hidden states, leave-episodes-out, AUROC >= .85 bar).
CPU in flight: SLAB-2 fable closing review (results/slab2-review-fable-r2.md); adoption build of the repo
assessment items (results/astra-assessment-adoption.md: security-boundary tests; completes-by-evidence; Q arm;
rerun-from-intervention diagnostic; held-out-family subsets; external-model baseline arm X built with a mock
client — do NOT run it without Brian's approval of the API spend).
Data: audited corpora under data/classifier/relations/ (kimi-*.jsonl + review/*-patch.jsonl); fable author-
disjoint held-outs 1-4 under data/classifier/heldout/ (held-out-4 pair is UNTOUCHED — one look, for check 48).

## HOW TO WORK
- Briefs live in the session scratchpad (/tmp/claude-1000/-home-bmarti44-stencil-llm/<session>/scratchpad/); each
  check has <name>-brief.md and a chain script; prepend post-reboot-common.md (RUNNING.flag protocol) to GPU briefs.
- One check = pre-written README readings -> recipe commit -> run -> results (README, records <= 10 MB, summary,
  freeze hashes) -> 5-line item in results/quick-checks/README.md -> WORKLOG (<= 6 lines) -> fable review ->
  orchestrator addendum with corrections -> memory note.
- Reviewers: fable (Claude general-purpose agent, one round, writes results/<check>-review-fable.md); Opus for
  data audits (data/classifier/review/); kimi-k3:cloud via ollama (http://127.0.0.1:11434) writes data (drivers
  data/classifier/kimi_gen_*.py; ~35 rows per call; domains via cksum seeds).
- Research when stuck: launch two independent deep-web-research passes (astra with `codex --search exec`, fable
  with WebSearch), same brief, reconcile, adopt the ranked top-3 as quick checks with GO bars.

## THE NEXT DECISIONS (in order)
1. Pilot 5 ELIGIBLE? -> set the larger-test GO (results/larger-test/REGISTRATION.md first; freeze commit; run
   inside 12 GPU-h). INELIGIBLE -> fix on CPU with a registered amendment; do NOT reduce pressure.
2. Check 48 SCREEN-GO? -> registered full-data fit + larger validation of the 4B updater; PARTIAL -> use the
   passing half automatically; NO-GO -> report per-family errors; next lever is data for the missing families.
3. Check 49/50 GO? -> register the 27B LoRA-as-focus follow-up; NO-GO -> close the weight side for dense models
   ("rendering + masking is the mechanism; weights are for knowledge") with the citations in both memos.
4. Check 47 SWITCH-CANDIDATE? -> ask Brian for the 54 GB bf16 download; re-qualify backend + renderer golden;
   larger test on the dense trunk only if it fits 12 GPU-h.
5. After a larger-test PASS: PUBLISH GATE -> bmarti44/stencil on the Hub; write-up with the claim ceilings from
   results/focus-mechanism-composition-v2-astra.md and the assessment's "neuroscience is motivation, not
   validation" framing; include all four failed pilots.

## KEY FILES
AGENTS.md; LEDGER-PLAN.md; WORKLOG.md; results/quick-checks/README.md (items 31-50); results/focus-mechanism-
composition-v2-astra.md (+ addenda); results/composition-v2-review-fable.md; results/composition-pilot-{1..4}
reviews; results/slab2-review-fable*.md; results/{reuse,updater,dense-focus,throughput}-research-{astra,fable}.md;
results/astra-repo-assessment-2026-09-06.txt + results/astra-assessment-adoption.md; results/relations-classifier-
report.md; src/stencil/focus/**; scripts/composition_pilot5.py; models/stencil-package/; memory (Claude):
~/.claude/projects/-home-bmarti44-stencil-llm/memory/stencil-state-2026-09-03.md (running log of every result).
