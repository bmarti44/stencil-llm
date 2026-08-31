# Stencil: teaching a frozen AI model where to focus

A theory of how the brain works, proposed by Earl Miller and colleagues at
MIT ([Picower article](https://picower.mit.edu/news/cognition-and-consciousness-arise-analog-computations-says-new-theory),
[Neuron paper](https://www.cell.com/neuron/fulltext/S0896-6273(23)00506-8)),
says knowledge and focus live in different mechanisms. Knowledge is stored
in the wiring (synapses). Focus — *what am I doing right now* — is carried
by electrical waves that sweep across that wiring and decide which circuits
are on at any moment: **"Synapses store representations, while wave dynamics
help determine which representations are active at any given time."** They
call the control waves "mobile stencils." This project is named after that
phrase, and it builds the split into real AI models.

Today's models don't have the split: what a model knows and what job it is
doing share one memory and compete. That may be part of why an assistant on
a long job slowly forgets its standing instructions and drifts.

## The headline result: the internal wave

A **tiny trained controller (264k parameters — 0.015% of the model)** rides
alongside a completely frozen Qwen3-1.7B, reads its hidden state at every
step, and generates an "attention spotlight" pointing the model at whichever
standing instruction matters right now. Nobody tells it when or where to
point. It is trained by one signal only: ordinary "make the correct next
word likelier" gradients flowing **through the frozen model itself**.

On a sealed, one-shot, never-touched test set (96 multi-turn coding
sessions), the wave:

- lifted rule-following from **25% to 45%** — recovering *more* than the
  hand-built reference press it learned from;
- beat the standard fix (re-pasting the rules as text), which broke more
  code and failed the safety rule the wave passed;
- **improved** code quality while doing it (parse rate 85% → 93%);
- beat an identical twin trained with old-style labels — proving the
  gradient training signal, not the architecture, is the active ingredient;
- and in a second sealed test where its training phrasing was **completely
  removed from every prompt**, still won (36% → 55%) — it points at
  instructions by their role, not by memorized wording.

Every number above is from a preregistered, hash-pinned, single-attempt run,
independently recomputed by two adversarial reviewers, with a full
reproduction audit matching every generated output. Report:
`results/internal-wave-report.md`.

## The road there (each step has a rerunnable, seed-pinned record)

1. **The split works causally (GPT-2 era).** A frozen GPT-2 with
   instructions provably out of attention's reach: a separate ~5KB state
   carried them — 100% vs ~4% when zeroed; transplanting the state made the
   same wiring follow different rules. `results/gpt2-report.md`.
2. **The contentless selector (SELECTOR era).** Working memory stays plain
   text; a learned 5-bit address presses attention toward the governing
   rule. Under 32 simultaneous obligations, base 3.9% → selector 88.3%
   (sealed), at ~1/100th the cost of re-pasting the rulebook.
   `results/selector-report.md`.
3. **Four honest negatives that mapped the boundary (TIMED-SELECTOR and
   PRESS-PLAN eras).** Every attempt to make a *discrete, certified* "press
   now?" decision failed its registered gates — threshold scoring, trained
   discrimination, learned state, blind rhythm — each closed with a full
   autopsy. The autopsies revealed the two real culprits: a brittle
   hard-threshold actuator, and label-based training. The wave fixes both.
   `results/timed-selector-report.md`, `results/press-plan-report.md`.
4. **Focus is steerable; its audit trail is sparse but never wrong (W3).**
   Overriding the wave's focus makes the model adopt the pointed-at rule
   (+42 points, p ≈ 4×10⁻¹²) though with some collateral effects (gate
   failed, honestly recorded). Decoding "what is it focusing on?" speaks
   rarely — but when it speaks it was correct 73/73 times.

## Honest boundaries (stated, not hidden)

- All results are on one 1.7B model and a synthetic coding harness with
  machine-checkable rules. External benchmarks are the current program
  (`BENCH-WAVE-PLAN.md`), starting with IFEval.
- "Reads meaning, not wording" is proven for one unseen phrasing — not for
  arbitrary paraphrases.
- The wave has no memory: recurrence added nothing measurable under the
  tested architecture; the Miller wave's *temporal* claims (rhythms,
  state transplant) remain open, honestly scoped.
- Instructions with no checker and no clean syntax (pure human steering)
  are outside every test so far — flagged as the hardest next frontier.

## Why you can trust the numbers

Models are reimplemented in-repo and parity-checked bit-for-bit against
pinned reference weights; everything is deterministic from pinned seeds;
sealed tests are one attempt with artifact hashes pinned before running;
success metrics are causal (matched controls, ablations, wrong-target
controls); and every phase was adversarially reviewed by two independent
reviewers who reran the numbers themselves — the record includes more than
a dozen instrument errors and overclaims they caught (several of them
mine) before false conclusions could land. `WORKLOG.md` is the complete
decision-by-decision record, retractions included.

## Repo map

- `WORKLOG.md` — the full decision record. `AGENTS.md` — the operating
  lessons that keep this honest.
- `BENCH-WAVE-PLAN.md` — current program (real benchmarks).
  `INTERNAL-WAVE-PLAN.md`, `PRESS-PLAN.md`, `TIMED-SELECTOR-PLAN.md`,
  `SELECTOR-PLAN.md`, `GPT2-PLAN.md` — closed programs, oldest last.
- `src/stencil/` — parity-proven GPT-2 and Qwen3-1.7B trunks with
  spotlight hooks; the wave controller (`wave.py`); task generators;
  scorers.
- `results/` — reports, per-example JSON evidence, review records,
  research surveys. `archive/` — the toy-scale era.
