# Phase0 Review — phase0

**Score:** 93 / 100
**Verdict:** PASS (≥90)
**Reviewer model:** codex/gpt-5.6-sol
**Date:** 2026-08-22

## Round log

### Round 2 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 93 / 100 (delta vs prior round: +21)
- Addressed since prior round:
  - Commit `a7b0742` forces the registered cuBLAS value before Torch import at `src/stencil/determinism.py:11-16`, records it at `src/stencil/train.py:185-194`, and protects both facts with the poisoned fresh-process test at `tests/test_determinism.py:27-47`; independent re-probing confirmed the fix.
  - Commit `a7b0742` makes G0 run the strengthened full Phase 0 suite at `Makefile:6-8`; direct config/run-ID checks now live at `tests/test_config.py:29-56`, and real-Git identity/artifact/dirty/force checks live at `tests/test_run_policy.py:24-121`.
  - Commit `a4b0f29` changes the governed Phase 0 status to `in progress` at `README.md:45-50`.
  - `plan/LEDGER.md:15-16` honestly records the Round 1 write-ahead omission, and `plan/LEDGER.md:13` supplies the command, log, canonical artifact, session, budget, and next action for Round 2.
- New or remaining:
  - The new first-loss-versus-final-loss check does not establish that optimizer updates occurred; changing batches makes it pass even with a frozen model. This is low severity and does not block G0 promotion.

### Round 1 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 72 / 100 (delta vs prior round: +72)
- Addressed since prior round:
  - Initial round; there are no prior findings to close.
  - The coder log shows the three registered tests were authored before the implementation, observed failing at collection, and then made green; the exact G0 test selection and Ruff also pass on independent replay.
- New or remaining:
  - The shared determinism module does not force the registered cuBLAS workspace setting when the ambient environment already defines another value.
  - G0 does not exercise the implemented config-hash helper, run identity, run-artifact, or `--force` contracts.
  - Phase 0 is still reported as `not started` after its recorded launch and code landing.
  - The active review was launched without the complete write-ahead ledger record required for reviews.

## Findings

1. **High (resolved 2026-08-22: the value is forced before Torch import, recorded in env.json, and independently re-probed under a poisoned ambient environment) — Ambient cuBLAS state can silently change a run outside its registered identity.** `src/stencil/determinism.py:11-16` now assigns `:4096:8` unconditionally before importing Torch, `src/stencil/train.py:185-194` records the effective value, and `tests/test_determinism.py:27-47` exercises a fresh process starting from `:16:8`. An independent fresh-process probe returned `[":4096:8", true]`; the registered environment and deterministic-algorithm flag are both in force.

2. **Medium (resolved 2026-08-22: the permanent G0 suite now checks config/run identity and the run-directory policy with a real temporary Git repository) — Gate G0 does not protect most of the Phase 0 identity and run-artifact contract.** `Makefile:6-8` now runs the whole Phase 0 suite. `tests/test_config.py:29-56` calls `config_hash` and independently reconstructs the four-term run-ID preimage. `tests/test_run_policy.py:38-121` checks tracked-diff and untracked framing, dangling symlinks, the exact artifact quartet, 200 ordered metric rows, clean/dirty stamping and refusal, existing-run refusal, same-state replacement, and different-state `--force` refusal against `src/stencil/config.py:177-231` and `src/stencil/train.py:125-194`.

3. **Medium (resolved 2026-08-22: the Phase 0 row now reports the required pre-acceptance state) — The governed project status contradicts the recorded phase state.** `README.md:49` now reads `in progress`, consistent with `plan/LEDGER.md:13-23`; green remains correctly deferred until the accepted `gate(G0)` commit.

4. **Low (resolved 2026-08-22: the omission is confessed and the current launch record is complete) — The Phase 0 review launch lacks its required complete write-ahead record.** `plan/LEDGER.md:16` records the Round 1 omission without rewriting history, while `plan/LEDGER.md:13` names the Round 2 command, held session, log path, canonical sol and kimi artifacts, round budget, and post-acceptance command.

5. **Low — The new determinism non-vacuity anchor still passes when training performs no parameter updates.** `tests/test_determinism.py:22-24` and `scripts/verify_determinism.py:14-17` use only `first[0] != first[-1]` to claim that training was non-vacuous. The batches advance every step, so even an unchanged model produces different losses: an adversarial no-optimizer replay of the registered 200 batches produced first/final losses `4.159191608428955` and `4.159383773803711`, satisfying the new assertion. The bitwise-repeat assertion remains valid, but this added anchor does not detect a disconnected optimizer or no-op update.

## Recommendations

1. Replace the loss-change check at `tests/test_determinism.py:24` and `scripts/verify_determinism.py:16-17` with a direct training-effect assertion. Expose the final trained state from `src/stencil/train.py:72-112` through a narrow test helper or result object, then assert at least one parameter byte differs from `initialize_model(config)` while retaining the exact 200-loss bitwise comparison.

## Evidence consulted

- `PLAN.md` in full, especially Section 2, Section 3, Phase 0, Appendix A, Appendix C, and Section 2b's pointer; `plan/PROTOCOL.md`, `plan/LEDGER.md`, `AGENTS.md`, and `README.md`.
- The prior sol and kimi review files, the Round 1 fix brief/allowlist, and read-only diffs and metadata for commits `a4b0f29` and `a7b0742`.
- Current source and gates line-by-line: `src/stencil/config.py`, `src/stencil/determinism.py`, `src/stencil/train.py`, `scripts/verify_determinism.py`, `tests/test_config.py`, `tests/test_determinism.py`, `tests/test_run_policy.py`, `configs/test_tiny.json`, `Makefile`, and `pyproject.toml`.
- `results/logs/codex-agent-phase0-fixes.log`: tests were added before implementation; the poisoned-cuBLAS and dangling-symlink cases failed red; config/run-ID, existing run-policy behavior, and the attempted loss-change anchor passed immediately; the post-fix suite passed 7 tests and Ruff.
- The orchestrator's independent `make gate-0` replay recorded at `plan/LEDGER.md:13` (`7 passed`, Ruff clean).
- Independent read-only probes: poisoned `CUBLAS_WORKSPACE_CONFIG=:16:8` was forced to `:4096:8` with deterministic algorithms enabled; the canonical known-answer hash matched; the four-term run ID was recomputed; and a 200-batch forward-only/no-optimizer trace demonstrated that the new loss-change anchor passes without parameter updates.
