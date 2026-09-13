# Forward design review: what direction actually clears the bar?

You are reviewing the Stencil repository at /home/bmarti44/stencil-llm as an
independent adversarial reviewer. Use MAXIMUM reasoning effort.

**Do not read anything under `data/bench/`.** It holds evaluation benchmarks and
recorded responses; reading it would contaminate the work.

Write ONLY this review file. Do not edit code.

## Why you are being asked again

You have just reviewed this work twice and rejected the direction both times:
`results/reviews/2026-09-13-a-screen-backontrack-astra.md` (OFF TRACK, 20%) and
`results/reviews/2026-09-13-a-screen-direction-astra.md` (OFF TRACK, 15%). Read
BOTH before starting; every finding in them stands and you should not re-derive
them.

Your second review ended: *"I cannot disprove the usefulness of selective rule
revision as a general research problem. I can reject the present claim that
Candidate A is already a defensible substantive recombination."*

**Brian's request now, verbatim: "have astra do another review and provide
recommendations for how best to move forward that has a better likelihood of
success."**

So this review is CONSTRUCTIVE. The critique is done and accepted. Produce the
design.

## The goal that must be satisfied

One published HuggingFace model artifact that keeps focus on the relevant
instructions over a long-horizon agentic coding session, PROVEN to outperform
the same artifact with the modification switched off. Brian's additional
criteria: a novel, useful recombination of techniques that is **not** technical
novelty from a meaningless permutation; a significant difference; and a good
chance of actually working based on current research — in AI and in any other
academic field.

**The bar is 25% on your artifact-success forecast**, using the definition you
set in your last review (published, reproducible, practically meaningful and
statistically supported improvement over the disabled counterpart; evidence for
the recombination beyond matched SFT; transfer beyond generator shortcuts;
reproducible packaging). A direction at >= 25% clears it.

## The resources that actually exist

Be concrete and cost-aware; do not propose anything that cannot be built and run
here.

- **Compute:** ONE NVIDIA GB10, 119 GB unified memory, SHARED with a peer
  session. Realistically a handful of GPU-hours, not hundreds. Contexts <= 4,096
  tokens. GPU is currently PAUSED by Brian and will only restart for a justified
  experiment.
- **Trunk:** Qwen3-4B at `deploy/stencil_focus/build/hub-4b` (frozen); Qwen3-1.7B
  also available; a 30B MoE exists but is off the critical path.
- **Already built and paid for:** a 624-session generator with executable
  contract/functional/regression/protected suites (`src/stencil/a_train_pool.py`,
  `src/stencil/a_screen_pool/`, `src/stencil/a_screen.py`); a complete 48-session
  `off` baseline; a trained CF LoRA (134 steps); a published sentence classifier
  (`bmarti44/assistant-memory-sentence-classifier`); the FOCUS-3 register runtime
  (`src/stencil/focus3.py`); vendored MemoryCode and BFCL v3 multi-turn runners.
- **Process constraints:** never fit, select or tune on any evaluation benchmark
  or recorded response; one registration per result; measured budgets before GPU
  launches; results reported with exhaustive readings.

## What I need from you

### 1. Three to five concrete candidate directions, ranked

For EACH, give:

- **The claim**, in one sentence, in the form "X beats X-with-the-modification-off
  on Y".
- **The intervention.** Training objective, inference-time mechanism, data
  construction, or combination. Say exactly what the artifact's off-switch turns
  off.
- **The workload and its oracle.** What tasks, where they come from, what makes
  the scoring deterministic, and critically: **what makes it defeat the trivial
  policies** — always-newest, always-oldest, flip-on-cancellation-language,
  copy-the-existing-implementation, and recency in general. Your last review
  showed the current screen fails exactly this.
- **The evaluation design.** Unit, N, estimand, test, and the power that N
  actually buys. Be honest where N is small.
- **Cost** in GPU-hours on the hardware above, split into CPU-only and GPU steps.
- **Prior art position.** What is already occupied, and what is genuinely left.
- **Your numeric forecast**, and what would most likely kill it.

Include at least one direction that is **inference-time only** (no training) —
the original artifact concept in `plan/BACK-ON-TRACK-PLAN.md` section G was an
inference-time session-memory package, and candidate A drifted into training.
Say which framing has the better odds and why.

### 2. The one you recommend, and the first week of it

Give the concrete first steps, CPU-only where possible, with the go/no-go
decision each step buys and its cost. Brian values quick, accurate, autonomous
execution and treats over-engineering as a defect.

### 3. Honest alternatives

If your best direction is still below 25%, say so plainly and rank "publish the
negative result and stop" among the options. Do not manufacture optimism. If the
goal as stated is unreachable with this compute, say what a reachable
restatement of it would be.

### 4. Research beyond AI

Brian explicitly wants other academic domains searched, not as vocabulary but as
design. Your last review's outside-field section (belief revision, retraction
economics, separation logic, version control, legal drafting) was the most
useful part of it. Push further: which of those converts into a *measurable
experiment* here, and what exactly would it measure?

### 5. What would change your forecast most

Name the single cheapest measurement that would move your number the furthest in
either direction, and say what result would move it which way.

## Output

End with one line:

`RECOMMENDATION — <direction name> — <N>% artifact-success forecast, <above|below>
25%; <the first concrete step>.`

Grade any new findings low/medium/high/critical. Cite files as
`/home/bmarti44/stencil-llm/<path>:<line>` and papers with links. Never soften a
prior finding.
