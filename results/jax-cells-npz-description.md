# Binary-artifact description: tests/fixtures/jax_cells.npz

Prose description per the batch-5-UPHOLD presentation contract (PROTOCOL v1.22) — the
first PRESENT binary artifact row; hash and size alone do not satisfy presentation.

Contents (numpy .npz, all arrays fp64 except noted): for each seed in {0, 1} —
`seed{s}_inputs` (512 x 256, N(0,1) draws from stream `fixtures:input`),
`seed{s}_A` (64, softplus-parameterized log-spaced modes drawn via `fixtures:a`),
`seed{s}_B1` (64 x 256), `seed{s}_B2` (64 x 64), `seed{s}_Wa`/`seed{s}_Wb` (64 x 64,
N(0, 0.02) via `fixtures:b`/`fixtures:glu`), `seed{s}_initial` (4 x 64: y1,z1,y2,z2
via `fixtures:init`); and per damping label in {undamped (G=0), damped (G=1e-2)} the
reference trajectories `seed{s}_{label}_{y1,z1,y2,z2}` (each 512 x 64). `metadata` is
a JSON string recording pinned commits (tk-rusch/linoss @ 05a8353…, jaredbmit/
damped-linoss @ 450b546…), jax/numpy versions, shapes, seeds, dtype.

PROVENANCE (final, after sol round-2 #10/#11): current npz sha256
41208bb72da558721d2c9ae11a220ed17f7ab62f2a5f6f2276e580b2df6cfd6d, generated
2026-08-23 with the FULL 512-step cases executed by the genuine upstream pipelines
(`apply_linoss_imex` from tk-rusch/linoss; `DampedIMEX1Layer._recurrence` from
jaredbmit/damped-linoss; z recovered via the exact identity z_{k+1}=(y_{k+1}-y_k)/dt;
the round-2 affine adapter is deleted). Initial states are explicit zeros —
unregistered in the fixture spec, and production cells initialize to zeros, so this
is the conservative reading; nonzero-initial coverage lives in test 1's closed form.
Equinox pin 0.11.10 (0.11.4 incompatible with the registered jax==0.4.35).
Supersedes b4d9f7aa… (hand transcription, round 1) and 707c5d23… (adapter, round 2).
Result: no material equation discrepancy; test 4 passes against upstream-generated
trajectories AND reconstructs every input/parameter from the registered named
streams in-test, asserting exact archive equality before the trajectory compare. Consumer: tests/test_models.py::test_cell_matches_jax_fixtures
(rtol 1e-5, atol 1e-8, all four state trajectories, both dampings, both seeds).
