# Stencil: a separate wire for a model's sense of its current task

A theory of how the brain works, proposed by Earl Miller and colleagues at
MIT ([Picower article](https://picower.mit.edu/news/cognition-and-consciousness-arise-analog-computations-says-new-theory),
[Neuron paper](https://www.cell.com/neuron/fulltext/S0896-6273(23)00506-8)),
says knowledge and focus live in different mechanisms. Knowledge is stored in
the wiring (synapses). Focus — *what am I doing right now* — is carried by
electrical waves that sweep across that wiring and decide which circuits are
switched on at any moment. In their words: **"Synapses store representations,
while wave dynamics help determine which representations are active at any
given time."** They call the control waves "mobile stencils." This project is
named after that phrase, and it builds that split into real AI models.

Today's models don't have the split: what a model knows and what job it is
doing share one memory and compete. That competition may be part of why an
assistant on a long job slowly forgets its instructions or drifts (the
motivating hunch — not something proven about deployed assistants).

## What has been proven (each claim has a rerunnable, seed-pinned test)

**1. The split works, causally, on a real model (GPT-2 era).**
GPT-2 small with its weights frozen (checked bit-for-bit) and its attention
narrowed so instructions provably leave its reach (exact-zero calculus, not
assumption). A separate ~5KB state carried the instructions: **100% accuracy
on questions whose evidence was mathematically unreachable, collapsing to
~4% when the state was zeroed.** Swapping the state between sessions made
the same frozen wiring follow different rules (28/32; shuffled control
1/32). Full record: `results/gpt2-report.md` (dual reviewer sign-off).

**2. The Miller mechanism proper: a contentless selector (SELECTOR program).**
The mature design keeps working memory as plain text (a visible "ledger" of
current obligations) and gives the wire one job: decide **which obligation
governs the current moment** and press the model's attention toward it — an
address, never a value (5 bits at 32 obligations). On frozen Qwen3-1.7B,
where the base model collapses to **3.9%** under 32 simultaneous obligations
with lookalike interference, the learned selector restores **88.3%** (sealed
final, untouched seeds) — comparable to re-pasting the entire 503-token
rulebook before every question (84%) at ~1/100th the cost. The selector is
bitwise-invisible when off, span-specific (a wrong address does nothing),
and the model's weights never change. Report: `results/selector-report.md`.

**3. Two honest negatives, fully autopsied.**
- *Waves as storage don't work here:* the literal analog oscillator stored
  exactly one rule and destroyed the rest by superposition — consistent with
  the theory (waves select; synapses store).
- *The wire as a content channel doesn't generalize:* making the wire carry
  novel values (rather than select among visible ones) memorized but never
  generalized within registered attempts; and where it worked, plain text
  storage matched it. Storing things is text's job.

## What works well, honestly bounded

- **Selection/governance** is where the wire wins: whenever the model can
  see or already knows the content but picks the wrong thing to obey, the
  spotlight fixes it — and at scale (32+ obligations) nothing cheap
  substitutes for it.
- **Inspectability:** the focus state is a small object you can read with a
  linear probe, edit, transplant, and carry across context compactions.
- **Boundaries:** at small obligation counts, re-inserting the text wins
  outright; the selector's addresses were trained with supervision (what
  counts as an instruction is taught, not discovered); tasks so far are
  templated with named queries. These are stated, not hidden.

## Why you can trust the numbers

Every model is reimplemented in this repo and parity-checked against pinned
reference weights; training and evaluation are bitwise deterministic from
pinned seeds; success metrics are causal (mechanism-off controls,
wrong-address controls, sealed final seed spaces registered before use);
and every phase was adversarially reviewed by two independent reviewers who
ran their own experiments — the record includes three instrument failures
they caught before false conclusions landed.

## Repo map

- `WORKLOG.md` — the complete decision-by-decision record.
- `SELECTOR-PLAN.md` (+amendments) — the registered protocol of the current
  program. Earlier eras: `GPT2-PLAN.md`, `QWEN-PLAN.md` (closed).
- `src/stencil/` — hand-rolled, parity-proven GPT-2 and Qwen3-1.7B trunks
  with probe/spotlight hooks; task generators; the cache/selector modules.
- `results/` — reports, per-example JSON evidence, reviews.
- `archive/` — the toy-scale era that established the mechanism first.
