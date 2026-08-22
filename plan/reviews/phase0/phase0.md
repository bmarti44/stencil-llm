# Phase0 Review — phase0

**Score:** 72 / 100
**Verdict:** FAIL (<75)
**Reviewer model:** codex/gpt-5.6-sol
**Date:** 2026-08-22

## Round log

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

1. **High — Ambient cuBLAS state can silently change a run outside its registered identity.** `src/stencil/determinism.py:7` uses `os.environ.setdefault`, so an inherited `CUBLAS_WORKSPACE_CONFIG` value such as the also-deterministic `:16:8` survives instead of being replaced by the registered `:4096:8`. A fresh-process probe with a conflicting value confirmed that the module preserves it. The setting is neither part of the run identity at `src/stencil/config.py:201-210` nor recorded in `env.json` by `src/stencil/train.py:171-192`; consequently, the same config and Git identity can select different cuBLAS deterministic modes without a different run ID or an audit record. This violates the exact Section 3 setting and the same-machine/same-config bitwise contract.

2. **Medium — Gate G0 does not protect most of the Phase 0 identity and run-artifact contract.** `Makefile:6-10` selects only three tests, while `tests/test_config.py:23-30` hashes `canonical_json` directly and never calls the delivered `config_hash` helper at `src/stencil/config.py:72-74`, much less `git_identity`/`run_id` at `src/stencil/config.py:167-210`. No permanent test invokes `run`, artifact creation, dirty-run refusal, existing-directory refusal, or guarded `--force` replacement at `src/stencil/train.py:124-192`. The coder's one-time CLI smoke run is useful evidence but is not a regression gate; these registered deliverables can break or be deleted while `make gate-0` remains green.

3. **Medium — The governed project status contradicts the recorded phase state.** `README.md:49` still says Phase 0 is `not started`, while `plan/LEDGER.md:13-18` records Phase 0 as launched, code landed, and G0 green. PLAN rule 5 requires the row to change to `in progress` upon entering the phase; green should wait for the accepted gate commit, but `not started` is already false.

4. **Low — The Phase 0 review launch lacks its required complete write-ahead record.** The top state at `plan/LEDGER.md:13` still describes topic registration and this review command as future work even though `plan/reviews/phase0/topics.txt:1` is committed and the review is running. It does not record the active review log path or expected canonical artifact as required by the ledger schema at `plan/LEDGER.md:7-9`. This weakens cold-start recovery during the review, although the wrapper log itself remains available.

## Recommendations

1. In `src/stencil/determinism.py:7`, assign the registered value unconditionally before importing Torch, and add a fresh-process regression test that begins with a conflicting ambient value and asserts both the final environment value and `torch.are_deterministic_algorithms_enabled()`.

2. Extend `tests/test_config.py:23-30` to call `config_hash` itself and independently check the four-term `run_id` preimage with a fixed `GitIdentity`. Add real-filesystem tests for `git_identity` framing and `src/stencil/train.py:124-192`: clean versus dirty eligibility, all four artifacts and 200 metric rows, refusal without `--force`, same-state replacement, and different-state refusal. Keep the tests mock-free by using a temporary real Git repository.

3. Change `README.md:49` to `in progress` now; change it to the exact green state only in the final accepted `gate(G0): ...` commit.

4. Record the missed write-ahead event honestly in the next `plan/LEDGER.md` entry, including the review command, `results/logs/codex-phase0-phase0.log`, and `plan/reviews/phase0/phase0.md`; include complete write-ahead records before subsequent review launches.

## Evidence consulted

- `PLAN.md` in full, especially Section 2, Section 3, Phase 0, Appendix A, Appendix C, and Section 2b's pointer.
- `plan/PROTOCOL.md`, `plan/LEDGER.md`, `AGENTS.md`, `README.md`, `plan/reviews/phase0/topics.txt`, and `plan/reviews/phase0/artifacts.txt`.
- `src/stencil/config.py`, `src/stencil/determinism.py`, `src/stencil/train.py`, `scripts/verify_determinism.py`, `tests/test_config.py`, `tests/test_determinism.py`, `configs/test_tiny.json`, `Makefile`, `pyproject.toml`, and `uv.lock`.
- Read-only Git history and diffs for commits `dcf5d28`, `875552a`, and `16bc1ea`.
- `results/logs/codex-agent-phase0-scaffold.log`: test-first file creation, the observed red collection run, the green rerun, CLI smoke checks, exact gate output, and determinism verification.
- Dirty smoke-run artifacts under `results/1e399510d86b/`: `config.json`, `env.json`, `metrics.jsonl`, and `DONE`.
- Independent no-cache replay: the three exact G0 tests passed (`3 passed`), Ruff passed, and `scripts/verify_determinism.py` reported two identical 200-step loss sequences.
- Independent arithmetic/behavior probes: the canonical JSON SHA-256 matched `0d3dca5c...fdc3d61`; the four-term run ID matched an independent computation; a fresh import preserved a deliberately conflicting `CUBLAS_WORKSPACE_CONFIG`, reproducing finding 1.
