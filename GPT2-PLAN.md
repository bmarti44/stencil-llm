# GPT-2 + Oscillator: Testing the Knowledge/Focus Split on a Real Model

## Context — what we are proving (Brian's framing, the project's north star)

The brain theory: **knowledge and focus live in different mechanisms** — knowledge stored in the wiring, slow waves sweeping across it deciding which circuits are on right now. Today's models don't have that split; knowledge and current-job share one memory and compete. This project builds the split: a tiny separate wire carrying only the job description.

The toy phases established the mechanism with proofs: the wire carries instructions across a provably impassable gap (100% vs a 12.5% ceiling); the current job is *linearly readable* off the wire (87.5% at 32-way, chance 3.1%); and transplanting the wire-state makes the same wiring execute a different stored circuit — 45/45, knowledge untouched. That last result IS the theory's claim in miniature: the wave decided which circuit ran.

What was never shown: the split working on a **real model with real knowledge**. Brian's directive: retrofit the oscillator onto **GPT-2 small (124M)**, reframe the repo around this, keep it minimal, and back **every claim with a deterministic verification** so the oscillator's contribution is proved, not asserted.

Settled by Brian: clean pivot (old phases archived, history untouched); **2 arms** — the same model with and without the oscillator; **frozen trunk** — GPT-2's weights never train, so "knowledge in one place" is literal and bitwise-checkable; **2 seeds per arm** (4 fine-tune runs).

## The experiment

**Question:** does windowed GPT-2 + wire hold its instructions over a long, dynamic stream better than the same windowed GPT-2 without the wire — knowledge identical in both, by construction?

**The pressure (why focus needs its own carrier here):** attention restricted to a **64-token sliding window** in fine-tuning and eval (12 layers × 63 = 756-token max receptive field < 1024-token sequences). Instructions stated early and *updated mid-stream* genuinely leave attention's reach by query time — and unreachability is **provable per position** with the existing exact-zero-Jacobian machinery. The model's knowledge (word meanings, the `X -> Y` completion pattern) stays fully available; only *which job applies now* is out of reach — precisely the knowledge/focus separation, imposed by construction.

**The task (natural-language rules, deterministic by construction):** templated English over a vetted vocabulary where every answer is exactly one GPT-2 token. Instructions are word-mapping rules — `New rule: reply to "cat" with "dog".` — in an instruction zone (first ~256 tokens), **updated over time** (`Update: reply to "cat" with "bird" now.`) at stream-scheduled points; deterministic filler sentences between (template + seeded streams, no external corpus); queries in the final zone: `cat ->` scored exact-match on the single answer token. Two format demonstrations (using rules whose statements are *in-window*) sit near the query zone, so the *format* is always visible while the *rule identities* are not. 4 concurrent rules per sequence (the compositional lesson), 8 candidate mappings each. Answers never appear in the input (separate-target loss — the leakage lesson). Schedules: train family + held-out **drought/burst** families + sealed validation/final offsets — the Task D holdout design, reused.

**The arms (identical trainable budget, data, steps; trunk frozen in both):**
- **base**: windowed GPT-2 + per-head sigmoid gates (12×12=144) driven by the *current token's* embedding — stateless; provably cannot know an out-of-window rule.
- **osc**: identical, except gates driven by the existing `OscillatorController` (B₁ ∈ R^{64×768} reading GPT-2's embeddings) — the only persistent path.
Gates init 1.0 (exact no-op at start) in both.

**Read-out** (sealed final offset, both seeds): accuracy at query time vs **distance since the queried rule's last statement** and vs **updates absorbed**. The base arm's beyond-window accuracy is ceiling-limited *by proof*; the osc arm beats it iff the wire adopted. Then the **dial tests on the trained osc arm**: linear probe reads the four active rules off the wire; wire transplant swaps them (with a shuffle control) — the waves-select-circuits demo on a real language model.

## Deterministic verifications (every claim has a test)

1. **Weight-conversion parity**: our GPT-2 implementation reproduces reference logits on a fixed 32-prompt battery; captured once at conversion, asserted by hash thereafter (`test_gpt2_parity`).
2. **Bitwise training determinism**: two short fine-tunes in-process → identical losses and parameters (`torch.equal`).
3. **Inert wire**: gates bypassed → osc arm logits **bitwise identical** to vanilla windowed GPT-2 (`test_graft_inert_bitwise`). The graft provably adds nothing until trained.
4. **Frozen knowledge**: after fine-tuning, every trunk tensor bitwise unchanged (`test_trunk_frozen_bitwise`) — "knowledge in one place," literally.
5. **The doorless room on GPT-2**: exact-zero Jacobian from beyond-window rule positions to query logits in the base arm; nonzero via the wire in the osc arm (`test_unreachable_zero_grad_gpt2`).
6. **Hand-executed generator fixture** before the generator is coded (the protocol that has caught real bugs every time); fixture-exact test.
7. **Sealed holdout**: validation vs final offsets; final-eval refuses without the fleet-freeze marker (existing mechanism).
8. **Single-token invariant**: every vetted word round-trips the GPT-2 tokenizer as one token, asserted at build (`test_vocab_single_token`).
9. **Dial verifications on the trained osc arm**: probe accuracy vs chance; transplant flip-rate; **shuffle control** (a shuffled wire state must not flip answers systematically).

## Repo reframe (clean pivot)

- `archive/` ← `PLAN.md`, `plan/`, toy coder briefs (`tools/codex-agents/`), moved untouched with a pointer README. History preserved.
- New root `README.md`: the knowledge/focus story verbatim as the frame; the three toy proofs as established foundations (with their numbers); this experiment as the project.
- New root `GPT2-PLAN.md`: this plan (governing doc).
- `src/stencil/` stays as the library (oscillator, gates, determinism, streams, config reused as-is). New: `src/stencil/gpt2.py` (minimal GPT-2 stack in our harness: pre-LN blocks, learned positions, windowed attention, gate hooks), `src/stencil/nl_task.py` (templated task), `scripts/convert_gpt2.py` (one-time HF weight download → our state dict + parity capture), `scripts/run_gpt2_arms.py` (the 4 runs + evals + dial tests).
- All existing tests keep passing (library regression).

## Implementation steps (minimal, in order)

0. **Feasibility gate (no training, ~1h):** convert weights, parity test; then a prompt battery asking frozen windowed GPT-2 to complete `X -> Y` with rule + demos fully **in-window**. If the pretrained model can't do the format even with everything visible, both arms get the *same* minimal adapter (lm_head bias only), recorded. This gate decides viability before any training.
1. Repo reframe commit (archive + new READMEs + this plan as GPT2-PLAN.md).
2. Coder pass A: `gpt2.py` + conversion + verifications 1–4.
3. Coder pass B: `nl_task.py` + fixture (I hand-execute first) + verifications 6–8.
4. Coder pass C: zero-Jacobian test (5) + arms runner + dial-test harness (9).
5. **4 fine-tune runs** (~1M trainable params, 1024 ctx, batch 8–16, ~8k steps ≈ ~1h/run; all four inside a day with margin), sealed final evals, dial tests.
6. `results/gpt2-report.md`: the two drift curves, the verdict, the dial numbers; one sol xhigh results review (held session; loop only while high/critical findings remain).

Process: light, per standing ruling — hand-executed fixture, deterministic tests, ledger entries, ONE sol xhigh plan-review round before implementation (fix criticals/highs, no endless looping), one results review at the end.

## Verification (end-to-end)

- All 9 deterministic verifications green before the fleet; existing library suite still green.
- One run spot-checked bit-reproducible.
- Verdict from the sealed final offset only: **osc beats base by >5 points beyond the window on held-out schedules, both seeds, with osc's in-window accuracy ≥ base's** (no trade-off hiding); otherwise "no benefit at this scale," recorded honestly.
- Dial results reported with the shuffle control alongside.
