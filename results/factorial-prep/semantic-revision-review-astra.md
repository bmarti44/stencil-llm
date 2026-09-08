Fit-on: none. Development-on: the same two original audited Kimi conversations, exposed attempt-01 responses and synthetic CPU controls. Evaluated-on: none. Prompt development uses exposed DEV evidence; this is not fresh validation.

# Semantic updater revision — independent Astra review

2026-09-07 · Round 1 · Reviewer: gpt-6-astra, xhigh, native session `/root/maintenance_revision_review`. Explicit user-requested Astra xhigh replaces the historical Opus assignment. Author-disjoint from Sol's prompt/test change and the parent's registration. Purpose: bounded code and readiness review of the semantic clarification and prospective attempt 02; threat model: trusted but fallible model and operators. The active protocol path is absent; archived protocol and current ledger context were read. Only this review file was written. No inference, network/GPU access, benchmark or old frozen larger-result reads, source edits or commits.

**Score:** 95 / 100

**Verdict:** PASS — code/readiness for separately frozen attempt 02 only.

## Findings

No open high/critical findings. No additional in-scope defect identified.

The six static `semantic_job` instructions define durable obligations, distinguish permissions from requirements, exclude project descriptions and unadopted quotations, permit multiple obligations, ground global/task scope in the user's instruction, and preserve existing obligations through no-change turns. They separate current source authority from history/state context and updater guidance. Exact targets and ordered restoration remain specified by the existing wire/lifecycle instructions. Read together, these requirements do not make the task impossible or prohibit using historical context to resolve a current reference.

The added guidance contains no conversation-specific language/version requirements, task handles, gold keys, expected operations, target IDs or examples. Its general distinctions respond to exposed DEV failures, as the lineage states. The new test checks static guidance and source/history separation; it does not claim model comprehension or semantic correctness.

## Independent verification

Removing only the added `semantic_job` dictionary field makes the complete updater AST identical to frozen commit `5d499362eb4e7537631a06b10201b6e52e2c1f8e`. Thus compiler behavior, schema, source authority, atomic rejection, state hashing, caps and all prior prompt instructions remain unchanged. The six guidance strings total 1,424 characters.

Compared directly with that commit, nine other bound files are byte-identical: launcher, driver, bank, register, loop, renderer, journal, reviewed DEV bank and trunk hash receipt. The original recipe remains a byte-exact prefix of the registration; attempt 02 is appended prospectively. This identity check does not rehash model weights or certify current GPU availability.

Independent CPU validation: `PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_focus_maintenance_updater.py tests/test_maintenance_dev_check.py` — **20 passed**. Ruff and scoped `git diff --check` also pass. These tests exercise the consumer and audit path with synthetic/fake-decoder inputs; no model or real network requests ran.

Reviewed SHA256 identities:

- `src/stencil/focus/maintenance_updater.py`: `57a49409bbca3d2173fa9b22014e5aa54082ca29c6a9e0bd8638d3aa990c7ba9`
- `tests/test_focus_maintenance_updater.py`: `01656b049ad9a3d7a79721fe41a18370d8edc249bc22aa3850d4772c09d09980`
- `results/factorial-prep/DEV-UPDATER-CHECK.md`: `e84c5b9ce653bcfc193f393480d6d93c0dc77dd34629209056fb394fe41e62d3`

## Prospective reading and limits

Attempt 02 keeps exactly 16 scheduled, sequential single-attempt calls, two self-carried eight-turn trajectories and 48 correlated effective views. The unchanged launcher requires committed clean bound files, writes the freeze before serving, enforces the 900-second reservation including startup/receipts/cleanup, and records deadline or cleanup failure. There is no worker, retry, gold reset, scoring relaxation or bundled further experiment. Actual capacity and timing remain run outcomes.

The addendum preserves all semantic and transaction errors and registers the three-failure stop-loss. Any error defeats perfect maintenance on these exposed seeds; zero errors only supports preparing a fresh screen. The previous **0/48 complete views and 0/2 trajectories**, and both observed high-severity empirical findings in [attempt-01's accuracy review](../quick-checks/maintenance-dev-01/accuracy-review-astra.md), remain true and unresolved as historical results. This code review neither closes them nor proves the prompt hypothesis, automation benefit, task competence or parity with manual prose. The reviewed change is ready to freeze for the single bounded DEV experiment described in [the registration](DEV-UPDATER-CHECK.md).
