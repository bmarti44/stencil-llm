# Stencil

A separate wire for an AI model's sense of its current task, with proofs instead of benchmarks.

This README explains the project in plain language and maps every part of the repository to that explanation. PLAN.md is the authoritative specification. This file explains, PLAN.md governs.

## The idea in plain language

A new theory about the brain says knowledge and focus live in different mechanisms. The brain stores what it knows in its wiring, while slow electrical waves sweep across that wiring and decide which circuits are switched on at any given moment. Knowledge in one place, what am I doing right now in another.

Today's AI models do not have that split. What a model knows and what job it is currently doing share the same limited memory and compete for space. That is why an assistant on a long job slowly forgets its instructions or drifts out of character. The instructions get crowded out.

This project builds the split. A tiny separate wire runs alongside the model and carries only the job description, nothing else.

## The three results, if it works

Result one is proof the wire works, designed so it cannot be faked. We give the model an instruction and then bury it so far back in the past that the model's normal memory physically cannot reach it. Not usually fails to reach it. Cannot, the way a room with no doors cannot be entered. We verify that with calculus before training anything, showing the buried instruction has exactly zero influence on the answer through the normal path. Then we ask the model to follow the instruction. The normal model can still make an educated guess from what it does see, so it is not at zero — but its best possible score is a guessing ceiling we compute exactly in advance, and it provably cannot beat it. The model with the wire scores far above that ceiling. Since there was no other path, the instruction must have traveled through the wire.

Result two is that the wire is a dial you can read and turn. Look at it and you can see which task the model believes it is on. Overwrite it and the model switches tasks on command. In today's large models this information exists but is smeared across billions of numbers, and finding it is like picking one voice out of a stadium. Here it lives at a known address.

Result three is a check that adding the wire does not make a somewhat larger model worse at ordinary language.

## Why it matters

Anyone who has used an AI assistant on a long job has watched it lose the thread. With this design, the job description has its own lane and never competes with content for space, so staying on task should not degrade with job length in the way it does today — a claim this project tests at small scale and finite horizons, not a guarantee about arbitrary lengths. There is a safety angle too. A dial at a known address can be watched like a dashboard light, so drift in a model's sense of its job becomes something you can see and correct rather than something you discover after the fact.

## How the repository delivers each claim

| plain-language claim | where it lives | how it is proven |
|---|---|---|
| the wire itself | `src/stencil/oscillator.py` (the wire's memory, a bank of tiny pendulums that keep ringing), `src/stencil/gates.py` (where the wire plugs into the model), variants `m1` and `m1b` in `src/stencil/model.py` | a test clamps the wire to neutral and checks the model becomes bit-for-bit identical to one with no wire, so the wire adds nothing until it acts |
| the room with no doors | Task A in `src/stencil/data.py` plus the narrow-memory base model in `model.py` | `test_cue_unreachable_exact_zero_grad` shows by calculus that the buried instruction has exactly zero influence through normal memory |
| the normal model cannot beat its guessing ceiling | variants `b0_local` and `b1` in `model.py` (b1 is the published memoryless gate deployed in Qwen's production models, at the granularity that matches ours) | Gate G3.1 requires both to score at or below a pre-computed guessing ceiling, and the zero-influence test explains why they must |
| the model with the wire succeeds | training runs of `m1` and `m1b` via `scripts/run_matrix.py` | Gate G3.2 requires high accuracy across three independent random seeds |
| no way to fake it | `src/stencil/determinism.py`, `scripts/verify_determinism.py` | rerunning the same experiment twice must produce bit-for-bit identical numbers, and every run logs its exact configuration |
| read the dial | `src/stencil/probes.py` | Gate G4, a simple readout must identify the model's current task from the wire at least 95 percent of the time |
| turn the dial | `src/stencil/patching.py` | Gate G4, copying the wire's contents from one conversation into another must switch the model's task at least 90 percent of the time |
| does the wire carry only the job, or content too | Task M in `data.py`, a memory quiz probing whether the model routes facts through the wire | pre-registered bands in PLAN.md Appendix C measure any content routing instead of hiding it; strong routing forces the separation claim to be withdrawn, and a low score is reported as "no evidence of routing," not proof of purity |
| how should the wire's memory fade | `m1` never fades, `m1b` learns how fast to fade, `b2` always fades, all in `oscillator.py` and `model.py` | Phase 3 records which wins with the prediction written down first, Phase 5 maps the tradeoff in `results/tradeoff.md` |
| a bigger model is not made worse | Phase 6 configs plus `src/stencil/evaluate.py` | Gate G6, ordinary language ability within 1 percent of the plain model at 125M parameters |
| predictions written down first | PLAN.md Appendix C and its amendment log | every pass bar was frozen before any experiment ran, and later edits are dated and logged |
| the receipts | `results/` (data_samples.md, params.md, summary.md, mechanism.md, tradeoff.md, REPORT.md, and POSTMORTEM.md if the project dies) | generated tables and figures, ending in a report with its own plain-language section |
| all work is adversarially reviewed | `tools/` codex wrappers, `docs/reviews/` | PLAN.md Section 2b: code written and reviewed by independent model runs; no work accepted with an open high or critical finding |

## Project stages and status

| stage | plain meaning | gate | status |
|---|---|---|---|
| Phase 0 | build the lab bench, prove reruns are identical | G0 | not started |
| Phase 1 | build the puzzle generators, prove them exact | G1 | not started |
| Phase 2 | build the models, prove the doorless room and the inert wire | G2 | not started |
| Phase 3 | the main event, the wire crosses where nothing else can | G3 | not started |
| Phase 4 | read the dial, turn the dial | G4 | not started |
| Phase 5 | map how the wire's memory should fade | tradeoff.md | not started |
| Phase 6 | scale up, confirm no harm | G6 | not started |
| Phase 7 | write the report, decide what is next | REPORT.md | not started |

Every green gate flips its row in this table in the same commit, per PLAN.md rule 5.

## What this does not show

This is a proof of concept. The models are tiny and the tasks are simple puzzles. Passing every gate proves the mechanism is real, shows exactly where it lives, and shows it can be steered. It does not prove it makes large models better. The wire also only tracks instructions that appear in the input. A model that figures out its task from context alone is a future version, not this one. And if the wire turns out to smuggle general content, that weakens the whole story, which is why a test for exactly that is built in rather than left unasked.

## Where the details live

PLAN.md holds the full specification, every architecture decision, every threshold, and every pass or fail rule, together with the prior-art map that scopes what is and is not new here. If this file and PLAN.md ever disagree, PLAN.md wins and this file has a bug.
