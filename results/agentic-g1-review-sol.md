codex
## Verdict

G1 is not a registered pass.

The always-on oracle is the registered negative. G1b is a valuable exploratory result showing that sparse, decision-timed attention can work, but it is outside the registered “dose/site re-check,” and its reported validity is lower than base. Under [AGENTIC-PLAN.md](/home/bmarti44/stencil-llm/AGENTIC-PLAN.md:52), the current program should stop before G2.

If the owner wants to continue—and the G1b mechanism is promising enough to justify it—register a successor **timed-selector program**. Do not retroactively broaden AGENTIC-PLAN.

## Findings

### CRITICAL — G1b is not the permitted dose/site re-check

The registered oracle spotlights the whole authoritative obligations block, with one allowed “dose/site” re-check in [AGENTIC-PLAN.md:19](/home/bmarti44/stencil-llm/AGENTIC-PLAN.md:19).

G1b changes three other dimensions:

- whole block → relevant individual sentence
- all task/generation rows → current prediction row only
- continuous activation → regex-selected decision moments

See [agentic_g1b.py:35](/home/bmarti44/stencil-llm/scripts/agentic_g1b.py:35), [agentic_g1b.py:49](/home/bmarti44/stencil-llm/scripts/agentic_g1b.py:49), and [agentic_g1b.py:71](/home/bmarti44/stencil-llm/scripts/agentic_g1b.py:71).

That is an actuator-policy redesign, not a dose/site re-check. It also uses the same 64 cases after observing the always-on failure and tries both β=2 and β=4 at [agentic_g1b.py:20](/home/bmarti44/stencil-llm/scripts/agentic_g1b.py:20).

Required record:

> Registered G1 always-on oracle failed. A post-failure exploratory timed-oracle redesign achieved 90.1% mean compliance and eliminated measured conflict adoption, motivating a separately registered timed-selector program.

Do not say “G1 passed via the registered re-check,” as [WORKLOG.md:457](/home/bmarti44/stencil-llm/WORKLOG.md:457) currently does.

### HIGH — Even under the broadened interpretation, the literal validity gate missed

The plan requires “no degradation of code validity” at [AGENTIC-PLAN.md:21](/home/bmarti44/stencil-llm/AGENTIC-PLAN.md:21).

The evidence reports:

- base validity: 0.953, or 61/64
- timed β=2: 0.938, or 60/64
- timed β=4: 0.938, or 60/64

See [agentic-g1b.json:14](/home/bmarti44/stencil-llm/results/qwen/agentic-g1b.json:14), [agentic-g1b.json:28](/home/bmarti44/stencil-llm/results/qwen/agentic-g1b.json:28), and [agentic-g1b.json:42](/home/bmarti44/stencil-llm/results/qwen/agentic-g1b.json:42).

In a deterministic paired evaluation, one additional broken case is degradation. No tolerance was registered. The earlier selector program enforced `broken == 0`; this gate cannot now reinterpret “no degradation” as “approximately unchanged.”

### HIGH — The admission gate is also qualified, not cleanly passed

The plan says base **per-obligation** compliance must be between 20% and 80% at [AGENTIC-PLAN.md:18](/home/bmarti44/stencil-llm/AGENTIC-PLAN.md:18). Prefix compliance is 95.3%, outside that band, while doc and hint are inside it in [agentic-g1.json:3](/home/bmarti44/stencil-llm/results/qwen/agentic-g1.json:3).

The worklog silently interprets the criterion as mean compliance. Conservatively, admission passed for two obligations but not the prefix obligation. That does not erase the doc/hint result, but “G1 admission passed” overstates the registered result.

### HIGH — “Code validity” is not a sound metric

Both scripts define validity as “a `def` regex matched and the substring `return` appears anywhere”:

- [agentic_g1.py:61](/home/bmarti44/stencil-llm/scripts/agentic_g1.py:61)
- [agentic_g1b.py:84](/home/bmarti44/stencil-llm/scripts/agentic_g1b.py:84)

This accepts syntax errors, `return` in comments/docstrings, undefined names, and code implementing the wrong operation.

The compliance checks also have holes:

- Docstrings recognize only `"""`, not `'''`, and can match an unrelated/module docstring.
- Hint compliance passes when only some arguments are annotated, because it checks every annotation it found—not every argument.
- The first regex-matching `def` may not be the intended function.
- Generated code is not saved, so these errors cannot be audited or rescored.

`generate_codegov()` does not retain a request/operation identifier in `CodeGovSession`; the request is discarded after interpolation at [qwen_task.py:249](/home/bmarti44/stencil-llm/src/stencil/qwen_task.py:249). A semantic checker therefore cannot currently test sum/max/product/subtraction behavior.

Before any successor run, use:

- `ast.parse()` and `compile()`
- an explicit target-function policy
- `ast.get_docstring()`
- annotation checks over every required argument
- deterministic execution tests for the requested operation
- a timeout/restricted subprocess
- raw generated code in every evidence record

The current G1b artifact is aggregate-only because `run()` retains no records at [agentic_g1b.py:102](/home/bmarti44/stencil-llm/scripts/agentic_g1b.py:102). That is not triageable.

### HIGH — The plan contains no learned timing-selector phase

G1b supplies two oracle facts:

1. **when** an obligation should press
2. **which** obligation sentence should press

The existing named-query selector does not solve either for implicit code generation. Yet G2 goes directly to a benchmark and G3 says the selector “runs during generation” at [AGENTIC-PLAN.md:25](/home/bmarti44/stencil-llm/AGENTIC-PLAN.md:25) and [AGENTIC-PLAN.md:34](/home/bmarti44/stencil-llm/AGENTIC-PLAN.md:34). No phase trains or gates the new moment selector.

A successor plan needs an S2-equivalent phase before runtime assembly.

## Moment-detector honesty

The regex detector is causal: it examines only the generated prefix, not future tokens or the desired value. Therefore it does not leak answer content.

But it is still an oracle. It hardcodes:

```text
after "def"         → select prefix sentence
after triple quote  → select docstring sentence
after argument ":"  → select type-hint sentence
```

That mapping at [agentic_g1b.py:49](/home/bmarti44/stencil-llm/scripts/agentic_g1b.py:49) contains the desired governance category. G1b proves that such timing and addressing are sufficient; it does not prove a learned selector can infer them.

There are two honest paths:

### Structured detector

Deploy an incremental Python parser/regex scheduler. Call the system a **parser-timed contentless selector**. This is likely the simplest and strongest engineering baseline.

### Learned detector

Train a classifier over frozen h20 state with labels:

```text
NONE, prefix-span, doc-span, hint-span, ...
```

Use direct CE, hard argmax/threshold, fixed β, and no regex at learned evaluation. Train on both base and oracle rollouts so it sees its own likely prefix distribution. Evaluate on its own autoregressive rollouts, not teacher-forced prefixes.

Mandatory diagnostics:

- moment precision and recall, with precision primary because false activations are destructive
- address accuracy conditioned on true moments
- false-activation rate on comments, strings, prose, ordinary expressions, and tool output
- behavioral compliance
- semantic validity
- correct-time/wrong-span and wrong-time/correct-span ablations
- parser-timed baseline
- always-on baseline
- zero-selector bitwise baseline

A one-token activation is also narrow. It works here because `qz`, `Computes`, and `int` are short. G2 must register whether activation lasts one token or until a syntactic unit ends; that cannot be adjusted after observing failures.

## Always-on failure

It does not invalidate the earlier short-answer S2/S3 results.

Those tasks generated a short value for which the selected ledger span was relevant to nearly every output token. In G1, code generation needs the task request, syntax, earlier identifiers, and local structure for most tokens. Continuous spotlighting suppresses that working context.

The distinction is mechanistically sound. The always-on implementation is especially aggressive: it biases every row from `Task:` onward in all eight layers at [agentic_g1.py:47](/home/bmarti44/stencil-llm/scripts/agentic_g1.py:47), while G1b changes only the current prediction row.

What the negative does invalidate is any general claim that the prior always-on selector can simply be deployed during long generation. A viable agentic selector now requires sparse temporal control. G1b demonstrates the oracle ceiling for that extra controller, not its learned solution.

## What G2 must register before implementation

Under the current plan, do not build G2. For a successor timed-selector plan, freeze the following first.

### Benchmark contract

- Exact tiny-repo fixture and hash.
- Exact scripted turns, update/reversal schedule, and environment outputs.
- Turn counts and balanced 20/40/60-turn strata.
- Exact compaction turns and what survives compaction.
- Context/token budgets and decoding configuration.
- Ledger set/update/clear precedence and canonical serialization.
- Which sources may author ledger changes.
- Every expected governance opportunity defined independently of whether the model emits a detector-triggering prefix.
- Missed actions and invalid outputs counted as noncompliant, never removed from denominators.
- Per-session macro metrics plus per-opportunity micro metrics.

### Timing and addressing

- Structured-parser versus learned-detector arms.
- Moment label generator.
- Activation start and termination.
- Hard address representation.
- Fixed layers and β.
- Threshold calibration data and immutable threshold.
- Negative/non-governance positions.
- Held-out syntax, formatting, comments, strings, multiple functions, and tool-call contexts.

Use factorial arms for triage:

| Timing | Address | Purpose |
|---|---|---|
| off | off | bitwise base |
| oracle | oracle | attainable ceiling |
| learned | oracle | timing test |
| oracle | learned | addressing test |
| learned | learned | actual system |
| always-on | oracle | known destructive control |
| shuffled | oracle/wrong | non-vacuity |

### Metrics and gates

Register numerical gates before training:

- moment precision/recall
- conditional address accuracy
- compliance at scripted governance opportunities
- stale-action and conflict-adoption rates
- syntax/compile/test validity
- task success
- unauthorized-write count
- selector activation rate
- token, latency, and ledger-size costs
- learned closure of the paired base→oracle gain

Use a strict paired validity criterion or state a tolerance now. Do not repeat the ambiguous “no degradation.”

### Evidence discipline

Every session artifact must contain:

- seed and config hash
- full prompt/transcript
- raw generated code/tool call
- ledger state before and after every turn
- compaction event
- true governance moments
- predicted activations and addresses
- attention intervention rows/spans
- checker results and failure category
- baseline/selector pairing

The G1 scripts also import Torch without first loading the repository determinism setup at [agentic_g1.py:13](/home/bmarti44/stencil-llm/scripts/agentic_g1.py:13) and [agentic_g1b.py:11](/home/bmarti44/stencil-llm/scripts/agentic_g1b.py:11). Fix that before claiming bit-reproducibility.

Bottom line: the timed oracle is an important positive mechanistic discovery, but it is not the registered G1 pass. Record the current program as stopped and, if continuing, make timing selection the explicit new research object rather than smuggling it through a “dose/site” allowance.
