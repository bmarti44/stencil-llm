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

Miller's work motivates an engineering distinction between storing
information and selecting what to use now. Stencil studies explicit retention
and retrieval around a frozen language model. These experiments do not test
the biological theory or demonstrate a wave mechanism.

## Current result (2026-09-04): selective retention under cache eviction

On frozen Qwen3-1.7B, selected historical KV pins plus text reinjection
substantially recovered aged-instruction compliance lost under pre-query
eviction. On 909 Multi-IF conversations, the combined arm scored 59.2%,
versus 16.7% after eviction and 65.2% with full context. Its C1/C3
statistical components were positive, but Leg B was NOT SUPPORTED under the
registered safety rule: one invalid output per relevant pinned arm versus
zero for full context. A parameter-free role rule matched or beat the learned
classifier at equal pinned columns (C2 failed), so learned selection has no
demonstrated advantage on this dialogue style. Every amplification / "wave"
variant tried on this trunk (attention bias on cache columns: always-on,
dosed, deficit-gated, classifier-gated; and residual-stream function-vector
steering) degenerated or under-delivered and is closed with data. The BFCL
agentic leg is registered and its preflight is running; no sealed result
exists yet. Records: `LEDGER-PLAN.md` (LEG B OUTCOME, LEG A), `WORKLOG.md`,
`results/quick-checks/README.md`, `results/astra-program-review.md`.

FOCUS-3 v4 stopped **INELIGIBLE-ADMISSION** on CPU after runtime input parity
and DEV calibration: transitions applied to the correct source rows were 8/12
(required 11/12), and admissions were 32/36. The registered stop prevented GPU
evaluation; the 64-episode v4 gate remains unrun.
[Results and diagnostics](results/quick-checks/focus3-gate/v4/RESULTS.md).

## Earlier headline: the internal wave (superseded, kept for the record)

A tiny trained controller (264k parameters) riding on the frozen trunk
lifted rule-following 25% -> 45% on a sealed synthetic coding harness
(`results/internal-wave-report.md`). That result stands on its harness, but
later amplification experiments did not establish a general remedy, and it
is no longer the program's current claim.

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
   hard-threshold actuator, and label-based training. The internal-wave
   experiment improved this synthetic task; later amplification experiments
   did not establish a general remedy.
   `results/timed-selector-report.md`, `results/press-plan-report.md`.
4. **Focus is steerable; its audit trail is sparse but never wrong (W3).**
   Overriding the wave's focus makes the model adopt the pointed-at rule
   (+42 points, p ≈ 4×10⁻¹²) though with some collateral effects (gate
   failed, honestly recorded). Decoding "what is it focusing on?" speaks
   rarely — but when it speaks it was correct 73/73 times.

## Honest boundaries (stated, not hidden)

- Results span several trunks and task families; each report states its own model, data lineage and claim limits.
- "Reads meaning, not wording" is proven for one unseen phrasing — not for
  arbitrary paraphrases.
- The wave has no memory: recurrence added nothing measurable under the
  tested architecture; the Miller wave's *temporal* claims (rhythms,
  state transplant) remain open, honestly scoped.
- Instructions with no checker and no clean syntax (pure human steering)
  are outside every test so far — flagged as the hardest next frontier.

## Why you can trust the numbers

Each experiment reports its parity checks, decoding conditions and provenance; quick screens and formally registered runs have different evidential strength.

## Repo map

- `WORKLOG.md` — the full decision record. `AGENTS.md` — the operating
  lessons that keep this honest.
- `LEDGER-PLAN.md` + `WORKLOG.md` — the current retention/selector evaluation.
  `BENCH-WAVE-PLAN.md` — the benchmark-wave program (closed).
  `INTERNAL-WAVE-PLAN.md`, `PRESS-PLAN.md`, `TIMED-SELECTOR-PLAN.md`,
  `SELECTOR-PLAN.md`, `GPT2-PLAN.md` — closed programs, oldest last.
- `src/stencil/` — parity-proven GPT-2 and Qwen3-1.7B trunks with
  spotlight hooks; the wave controller (`wave.py`); task generators;
  scorers.
- `results/` — reports, per-example JSON evidence, review records,
  research surveys. `archive/` — the toy-scale era.
