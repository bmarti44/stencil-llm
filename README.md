# Stencil: keeping a frozen language model on the current instructions

Stencil studies how a frozen chat model can keep following the instructions a
user gave earlier in a long conversation: which sentences must be remembered,
how they are re-supplied at request time, and whether steering the model's
attention toward them adds anything beyond restating them in prose. The name
comes from Earl Miller's "mobile stencil" account of cortical waves
([Picower article](https://picower.mit.edu/news/cognition-and-consciousness-arise-analog-computations-says-new-theory),
[Neuron paper](https://www.cell.com/neuron/fulltext/S0896-6273(23)00506-8)).
That theory motivated the split between stored knowledge and current focus; the
experiments here neither test the biology nor demonstrate a wave.

## Status (2026-09-11)

The program is executing the back-on-track plan in
[plan/BACK-ON-TRACK-PLAN.md](plan/BACK-ON-TRACK-PLAN.md): one narrow method
question (does a learned attention controller beat prose restatement and fixed
steering when the correct rules are supplied?), one product question (can the
live set of instructions be maintained automatically and rendered as a reminder
on a MemoryCode-derived workload?), and an honest artifact release. Results land
under `results/<name>/RESULTS.md` with a registered test and an interval each.
Resume from the latest STATE entry in [plan/LEDGER.md](plan/LEDGER.md).

The one trained model with a public-benchmark number, the sentence classifier
(rule / fact / none, bge-small-en-v1.5 fine-tune), is being published as
`bmarti44/assistant-memory-sentence-classifier` on the Hugging Face Hub.

## Headline result: selective retention under cache eviction (Qwen3-1.7B, Multi-IF)

On 909 Multi-IF conversations (484 distinct source prompts), earlier user
instructions were evicted from the KV cache before the final query, then partly
restored by pinning selected historical columns and echoing their text.

| Arm | Aged-instruction compliance (pooled) |
|---|---|
| full context | 65.2% |
| evicted | 16.7% |
| classifier-selected pins only | 57.2% |
| classifier-selected pins + echo | 59.2% |
| role/recency rule pins (no training) | 60.5% |

Registered components C1 and C3 passed (conversation-clustered t, Holm). C2
failed: the parameter-free role/recency rule beat the trained 133M-parameter
selector by about 3.5 points at matched pinned columns, so learned selection has
no demonstrated advantage on this dialogue style. The registered safety rule
recorded one invalid output in a pinned arm versus zero for full context, so the
leg is reported NOT SUPPORTED under that rule. No echo-only arm was run, so the
value of the pins given the echo is not yet identified; that is experiment 1 of
the current plan. Records: `results/qwen/multiif-evict-909-prequery-v2/`
(911 files, all tracked), `LEDGER-PLAN.md` (LEG B OUTCOME). Reproduce:
`uv run python scripts/multiif_evict.py` (about 21 GPU-hours on the GB10; use
`--limit` for a smoke run).

## The baseline to beat: restating the current rules in prose

Across every harness tried, restating the correct current rules in prose at
request time is the strongest simple mechanism. No structured or internal
mechanism has beaten it by more than about two points, and several lost to it:

- larger-test-v2 (Qwen3-30B-A3B, 64 authored 16-round coding episodes): a rule
  register beat no reminder on delivery (35 wins / 0 losses / 28 ties,
  p = 3e-11), but a plain prose reminder tied or beat the register on every
  family, and the register lost semantic integration 45 vs 52 (p = .0078).
- FOCUS-2d (256 episodes): placement plus eviction 143/256 vs prose restatement
  176/256.
- FOCUS-3 v8 diagnostic (Qwen3-4B, 64 reused-template episodes, no verdict
  assigned): automatic register 57/64, oracle register 63/64, no reminder
  29/64, with 25 false admissions in 21 episodes. Earlier FOCUS-3 versions
  (v1 to v8) stopped INELIGIBLE on CPU admission counters and never ran their
  GPU gate; see `results/quick-checks/focus3-gate/`.

The program's practical objective is therefore automatic maintenance of
correct reminders at acceptable cost, not beating a hand-written reminder
([results/CURRENT-GOAL.md](results/CURRENT-GOAL.md)).

## The internal wave: a learned attention-allocation result, narrowly stated

A 264k-parameter controller (`src/stencil/wave.py`) reads layer-20 hidden states
of frozen Qwen3-1.7B and emits, at every generated token, a pre-softmax bias over
prompt positions, trained by completion loss through the frozen attention path.
On a sealed synthetic coding harness (96 sessions, correct live ledger supplied
every request), adherence rose from 25.2% (base) to 44.8% (wave), against 38.3%
for a hand oracle, 37.4% for a proxy field and 43.0% for prose reinsertion
(which also broke 30 works versus 21). One seed, no p-value.

Qualifications that travel with this result: the harness supplies the correct
ledger, so it tests attention allocation given the rules, not discovering them;
the W3b readout could not decode the governing rule from the field; the
controller reduced MMLU from 48.05 to 45.83 and failed GSM8K noninferiority; the
comment-rule rows (0/120 in every arm) were unmeasurable under a checker bug
(`src/stencil/t2_runner.py`, fixed in the current plan) and carry no evidence.
The W3 override experiment failed both of its registered gates; the qualified
positive is W3a (wave 55.1 vs reinsertion 53.1 vs base 36.6 on one registered
unseen rendering). Reports: `results/internal-wave-report.md`,
`results/w3-results-sol.md`. Reproduce: `uv run python scripts/w_seal.py`
(checkpoint `results/qwen/w0-ce.pt`, tracked).

## Earlier constructions (parked, not closed)

- GPT-2 focus cache: a frozen GPT-2 with instructions kept out of attention's
  reach followed them at 100% versus 4.3% with the state zeroed; transplanting
  the state switched rules 28/32. The gap is guaranteed by the construction.
  `results/gpt2-report.md`, `scripts/run_gpt2_arms.py`.
- SELECTOR: a learned 5-bit span address plus attention spotlight lifted a
  32-obligation named-query task from 3.9% to 88.3% (n = 128). The task is
  solvable by dictionary lookup and no retrieval or LoRA baseline was run.
  `results/selector-report.md`, `scripts/selector_s3_final.py`.

## Negative results (each with its record)

| Recipe | Evidence | Reading |
|---|---|---|
| Static always-on attention bias on cache columns | n = 196, monotone -4.6 | solid negative |
| Deficit-gated bias, synthetic conf-v45 bank | n = 1024, +0.39, p = .389 | solid negative on that bank |
| Mean-difference skill vectors | 18 cells, 0 induction | solid negative |
| MoE router bias (30B-A3B) | competence 16/32 to 7/32, p = .022 | harms competence |
| Trained selector vs role rule (C2) | -3.5 points at matched columns | role rule wins |
| Classifier-gated bias on cache columns (check 28) | n = 20, 4 wins / 1 loss, killed on degeneracy | narrow; not ruled out |
| Function-vector residual steering | operating point chosen on 4 examples | narrow; not ruled out |
| Discrete "press now?" decisions (TIMED-SELECTOR, PRESS-PLAN) | four registered gates failed | closed with autopsies |

Details and per-check records: `results/quick-checks/README.md`,
`results/timed-selector-report.md`, `results/press-plan-report.md`,
`results/CLAIMS-CORRECTIONS.md`.

## Boundaries

- Results span several trunks and task families; each report states its own
  model, data lineage and claim limits. No number is attributed to any runtime
  package until a matching qualification exists.
- Nothing here has been evaluated on real multi-session coding work; the
  MemoryCode-derived screen in the current plan is the first such attempt.
- Evaluation benchmarks are never used to fit, select or tune anything; every
  registration carries a data-lineage line (AGENTS.md).

## Repo map

- `plan/BACK-ON-TRACK-PLAN.md` — the governing plan; `plan/LEDGER.md` — state;
  `plan/PROTOCOL.md` — process rules; `results/reviews/` — adversarial reviews.
- `src/stencil/` — bitwise-deterministic Qwen3 and GPT-2 trunks with attention
  hooks (`qwen3.py`), the wave controller (`wave.py`), session generators
  (`t2_sessions.py`), scorers (`t2_runner.py`), the instruction lifecycle
  runtime (`focus3.py`), statistics (`stats.py`).
- `scripts/` — one entry point per result (see each report); `archive/scripts/`
  — closed programs with `archive/scripts/MAP.md`.
- `results/` — reports, per-example JSON evidence and reviews; `data/classifier/`
  — the labelled sentence data and its provenance (`LABELS.md`).
- `WORKLOG.md`, `LEDGER-PLAN.md`, `AGENTS.md` — decision record and operating
  lessons. Older program plans (`*-PLAN.md`) are closed.

Verification: `make gate-0` runs the test suite, `ruff check` and
`ruff format --check`; `uv run python scripts/check_cleanup_invariants.py --check`
proves the scorers and generators still reproduce the recorded numbers.
