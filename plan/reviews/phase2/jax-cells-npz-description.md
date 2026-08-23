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

PROVENANCE (corrected after round 1's sol#2/kimi#1 High): current npz sha256
707c5d231984082015f8cc647f4c172f8ff81cd2aa33fbf68b1a56a54756a6ce, generated
2026-08-23 by EXECUTING the pinned checkouts (worker sys.paths the cloned repos and
calls their cell implementations: LinOSS-IMEX from tk-rusch/linoss, damped from
jaredbmit/damped-linoss; equinox pin bumped 0.11.4→0.11.10 by the orchestrator —
0.11.4 is incompatible with the REGISTERED jax==0.4.35, ledgered). The round-1
fixtures (hand-written transcription, b4d9f7aa…) are superseded. Result: no
material equation discrepancy — the upstream implementations reproduce the
registered Section 5.2 update; test 4 passes against the upstream-generated
trajectories. Consumer: tests/test_models.py::test_cell_matches_jax_fixtures
(rtol 1e-5, atol 1e-8, all four state trajectories, both dampings, both seeds).
