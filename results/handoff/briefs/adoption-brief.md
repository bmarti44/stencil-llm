# Adoption pass (CPU only) for gpt-6-astra: implement the adopted items from the repo assessment (2026-09-06)

Read results/astra-repo-assessment-2026-09-06.txt (the assessment) and results/astra-assessment-adoption.md (the
orchestrator's decisions; implement ONLY the "ADOPT NOW" rows). Register "SLAB-2 Amendment 2" in
tests/fixtures/slab2_cpu_report.md BEFORE code. Continue from HEAD (SLAB-2 Amendment 1 applied; fable's r2 review
results/slab2-review-fable-r2.md may exist — apply any blocking item it lists first).
1. SECURITY-BOUNDARY TESTS for the register (row 2): adversarial tests that quoted text, tool output, assistant
   prose, a user message quoting a system rule, and a structured entry with a forged role cannot create or retire
   rules; explicit entries with wrong/absent authority are rejected and journaled.
2. COMPLETION BY EVIDENCE (row 3): `completes` requires an evidence field — a test receipt (hash of a passing
   hidden/public test run), a confirmed tool result id, or an explicit user event; a model-claimed "done" becomes a
   PROPOSAL (journaled, not committed). Renderer shows pending proposals separately from live rules (one line).
   SLAB-2 episodes: the completes events in the gold schedule carry test-receipt evidence; N/T arms unaffected.
3. CAPABILITY-QUALIFIED SUBSET (row 4): add arm Q to the SLAB-2 driver: per episode, before trajectories, one
   fresh-context probe per task with the correct current rules rendered (no history) — executable success per
   task; the episode is "capability-qualified" if all its tasks pass Q. Register: the larger test reports PASS
   readings on the full 64 AND on the Q-qualified subset (both pre-written; the primary stays the full set);
   pilot 5 reports Q as a diagnostic (cost included in its projection).
4. RERUN-FROM-INTERVENTION DIAGNOSTIC (row 10): a registered CPU-scheduled diagnostic (not run now) that, for a
   fixed DEV subset, replays the trajectory from the point of a false admission with the admission removed, to
   measure the whole-trajectory effect; implement the replay entry point in the driver + a stub test.
5. HELD-OUT FAMILY SUBSETS (row 12): in the 64-episode manifests, preregister subsets by constraint family (rule
   kind mix), interaction structure (lifecycle shape), and domain, such that at least one family/shape/domain is
   absent from DEV; assert in tests; the RESULTS report will show the primary contrast per subset (descriptive).
6. EXTERNAL-MODEL BASELINE ARM X (row 12): scripts/external_baseline.py drives the SAME SLAB-2 bank and renderer
   with an Anthropic API model (ANTHROPIC_API_KEY is in the environment — never print or log it; model id
   'claude-sonnet-5' default, configurable), arms R and N only, same cap/EOS semantics (max_tokens), journaled like
   the local arms, cost meter (tokens, USD estimate from a config table). BUILD AND SMOKE-TEST WITH A MOCK CLIENT
   ONLY; do NOT call the real API (Brian must approve the spend; write the projected token count and cost for
   8 DEV episodes and for the 64-episode bank into the report).
Tests for each; run tests/test_focus_*.py + tests/test_no_side_effect_imports.py; commit only src/stencil/focus/**,
scripts/composition_pilot5.py, scripts/external_baseline.py, tests/**, tests/fixtures/slab2_*, WORKLOG (<= 6 lines)
with explicit pathspecs; no push; no GPU (checks 47-50 own it); never terminate or signal any process; never read
anything under data/bench or evaluation episode content beyond manifests. Report test counts and the API cost
projection.
