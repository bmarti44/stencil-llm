# Build brief (CPU only) for gpt-6-astra: SLAB-2 — the SIMPLIFIED larger-test harness (2026-09-06)

Ruling (orchestrator, under Brian's do-not-over-engineer rule, on fable's pilot-4 diagnosis results/composition-
pilot-4-review-fable.md — read it fully): four pilots each found new defects in the custom JSON tool-envelope
harness; SIMPLIFY. Keep run.py, loop.py, renderer.py, register, journal UNCHANGED. Replace the episode interface in
src/stencil/focus/slab.py (as a new module slab2.py; keep slab.py for history):
1. INTERFACE: the model answers each round with ONE fenced code block containing the WHOLE target file (path
   stated on the fence line or a fixed one-file-per-task convention), followed by a one-line report trailer
   (`report: task=<letter> status=<ok|blocked> delivery=<short string>`) — no JSON envelope. The harness writes the
   file, runs the public tests, returns a bounded tool result (test summary + function list; never the file back).
   Re-emission is free: scoring uses changed_code (diff vs the last parsable snapshot). Reply cap 1024 tokens;
   context budget assertion per arm (paired_context_gate) with 16-round episodes ONLY for now (32-round lanes
   dropped; fable: they overflow at ~round 20 with whole files).
2. TRAITS AND WITNESSES (fable items 1, 9): every rule carries a LITERAL value in its text (e.g. "indent 3 = block
   bodies indented by exactly 3 spaces"; "format compact = the trailer omits delivery"); register a T-FLOOR
   PRE-CHECK: a trait enters the success/relapse scoring only if the every-request-text comparator T satisfies it
   >= 50% on the DEV pilot (omission traits the model never performs are excluded from success and reported as
   diagnostics); substitution traits (delivery -> ready after completes; indent value after supersedes) are the
   primary relapse witnesses — they showed the first real arm signal (R 20/33 vs N 0/37).
3. FINAL SUCCESS = hidden integration tests + the still-live obligations that passed the T-floor pre-check; stale
   execution / wrong skill / breakage as before (breakage = invalid program / empty or capped reply / malformed
   trailer only).
4. Same rule kinds (language/style/format/process), same lifecycle events (supersedes/cancels/completes/
   reinstates), same DEV/eval disjointness and manifests (regenerate the 64 + 8 episodes under SLAB-2 with the
   same seeds; hashes re-frozen; data-lineage line), same arms R/N/T (O nested), gold events in DEV only.
5. Tests: reference solutions pass through the real path; mutants fail their witnesses; should-pass set; a full
   CPU stub-decoder dry run of all 72 episodes with REAL-tokenizer accounting (max context per arm; tokens per
   lane); the pilot-4 literal outputs are NOT reused as fixtures (different interface) — author 6 fixture replies.
6. COST GATE (re-registered): the 12 GPU-h budget applies to the REGISTERED 64-episode run itself (prior pilots are
   development cost, stated explicitly); pre-written pilot-5 readings: ELIGIBLE = executed (parsed trailer + file
   written) >= 90%, caps <= 2%, T-floor traits >= 2 kinds with nonzero denominators in >= 2 episodes, R final
   success >= 5/8 on DEV, measured projection (R/N x64 + O/T x16 at 16 rounds) <= 12 GPU-h; if the projection is
   between 12 and 15 h, the pre-registered fallback is 12-round episodes (state it now), never fewer arms.
Commit only src/stencil/focus/slab2.py, tests/test_focus_slab2.py, tests/fixtures/slab2_*, WORKLOG (<= 6 lines)
with explicit pathspecs; run the targeted tests + tests/test_no_side_effect_imports.py; no push; no GPU (checks
46-50 own it; never touch their flags/containers); never terminate or signal any process; never read anything
under data/bench. Report test counts, per-arm max context, and the token-per-lane accounting.
