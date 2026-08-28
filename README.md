# Stencil: a separate wire for a model's sense of its current task

A new theory about the brain says knowledge and focus live in different
mechanisms. The brain stores what it knows in its wiring, while slow electrical
waves sweep across that wiring and decide which circuits are switched on at any
given moment. Knowledge in one place, what am I doing right now in another.

Today's AI models do not have that split. What a model knows and what job it is
currently doing share the same limited memory and compete for space. That
competition may be part of why an assistant on a long job slowly forgets its
instructions or drifts out of character — that is the motivating hunch, not
something this project proves about deployed assistants.

This project builds the split. A tiny separate wire runs alongside the model
and carries only the job description, nothing else.

## Established foundations (toy scale, fully receipted in archive/)

1. **The wire works where nothing else can.** With the instruction buried
   beyond a mathematically impassable attention gap (verified by calculus:
   exact-zero gradients), the wired model scored 100% where the best possible
   instruction-blind score is 12.5% — every seed, bit-reproducible.
2. **Focus is readable.** A linear probe decodes the model's active task
   straight off the wire: 87.5% at 32-way (chance 3.1%).
3. **Focus is steerable.** Transplanting the wire state made the same frozen
   wiring execute a different stored rule 45 out of 45 times — the wave
   choosing the circuit.
4. **Honest negatives, kept honest by pre-registration:** on tasks whose whole
   state is "the most recent instruction," a trivial latch matches or beats
   the oscillator; wire adoption during training is not always reliable.

## The current experiment (GPT2-PLAN.md)

Retrofit the wire onto **GPT-2 small** with its knowledge frozen — literally:
the trunk's weights never train and a test asserts them bitwise unchanged —
and test whether the same model, windowed so instructions genuinely fall out
of attention's reach, holds dynamically-updated instructions better with the
wire than without it. Every claim carries a deterministic verification
(GPT2-PLAN.md lists all nine). Work log: WORKLOG.md.
