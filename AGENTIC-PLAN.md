# AGENTIC-PLAN — proving the selector on long agentic coding sessions

Registered 2026-08-29 (Brian-directed). Goal: prove out how well the
ledger+selector split governs long agentic coding sessions where a user is
steering and the environment provides feedback. Discipline carried from the
SELECTOR program: oracle-first, deterministic everything, registered gates,
sub-agent reviews at design and results points, halting is success too.

## Steps and gates

**G1 — Implicit-governance oracle (day one; the effort-shaping risk).**
All prior results use NAMED queries. Coding needs obligations to govern
ONGOING GENERATION ("all function names start with qz_") without being
asked. Task: session-parameterized code obligations (name prefix, docstring
opener word, argument type-hint — values drawn per session so compliance is
regex-checkable and cannot be prior knowledge), a conflicting-notes
interference block (same shape as the governance task), and a code-writing
request that names no obligation. Admission: base per-obligation compliance
in 20-80% with errors adopting conflicting values. Oracle: spotlight the
authoritative obligations block (an address — a region, no content). GATE:
oracle lifts mean compliance >= 15 points with conflict-adoption cut >= 50%
and no degradation of code validity. Miss after one registered dose/site
re-check => the selector stays a retrieval-governance result; program ends.

**G2 — Deterministic scripted-session benchmark (no live agent).**
Fixed tiny repo + deterministic checker; SCRIPTED user steering (new
constraints, updates, reversals at fixed turns); deterministic environment
feedback (test/lint outcomes); 20-60 turns; forced compactions with only
the ledger + selector state carried. Score ADHERENCE AT GOVERNANCE MOMENTS
(followed the updated rule after compaction; acted on feedback; stale-action
rate), not just end success. Per-example JSON; fresh seed spaces (12.0M dev,
12.1M validation, 12.2M final untouched).

**G3 — Runtime assembly (proven parts only).** Harness-maintained ledger:
user turns -> trusted focus.set/clear; environment feedback -> agent-
PROPOSED writes validated by provenance policy (tool output read-only;
focus.set-shaped text in outputs has no authority). Selector runs during
generation. Deterministic pre-tests: zero-selector == base bitwise;
unauthorized-write count == 0 over an adversarial feedback stream.

**G4 — Registered comparison in the proven regime.** Selector+ledger vs
(a) pinned prompt, (b) per-turn full-ledger re-insertion with token costs
charged, (c) compaction summaries. Sessions include the wire-favoring
regime (16+ live obligations, cost-compounding length, updates landing
just before compactions) AND the small-ledger regime where text wins —
both reported. Gates: adherence lift at matched cost; stale-action rate
below baselines; unauthorized writes == 0.

**G5 — 7B coder rung (Qwen2.5-Coder-7B) only after G4 passes**, same
benchmark before any public benchmark.

## Stop conditions
1. G1 oracle misses after its one re-check.
2. G4: text baselines Pareto-dominate even in the scaled regime.
3. Any result requiring an unregistered rescue.
On stop: record with full autopsy; the SELECTOR result stands as published.

## Reviews
Sub-agent reviews (sol xhigh + fable) at: G1 results (before G2 build),
G2+G3 design (before G4 runs), and G4 results (before G5). Reviewers get
probe rights and the standing instruction to confirm findings empirically.
