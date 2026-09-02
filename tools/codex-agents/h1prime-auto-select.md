# Brief: h1prime-auto-select — H1′ automatic-selection replication in the KV probe

## Objective
Implement exactly LEDGER-PLAN.md "H1′ — automatic-selection replication" in scripts/ledger_kv_probe.py:
1. `--focus auto|oracle` (default oracle = current behaviour, so H1 stays reproducible). With `auto`, the focus
   spans for the last turn are the spans SELECTED by the registered salience finder on the raw history text
   (reuse exactly the path scripts/ledger_eval.py uses: src/stencil/salience2.py DEFAULT_BACKEND + the ledger's
   selection of aged entries; hash the finder weights/probe/hybrid files into meta as ledger_eval does). No
   "Constraint:" marks may be read by any arm in auto mode (assert the marks are stripped from what the arms
   see, or that the finder is called on unmarked text — whichever the harness makes cleanest; document it).
   Record per session: `auto_coverage` = fraction of the oracle-marked aged constraints whose span is covered
   (>= 50% token overlap) by an automatically selected span; `auto_extra` = number of selected spans not
   overlapping any mark. Reported, not gated.
2. New arm `full_echo` (no eviction + echo). Drop the wave-dose arms in auto mode (`--dose` empty by default
   when `--focus auto`).
3. `invalid_output` per record: empty response, response that is only whitespace/punctuation, or any
   chat-control token in the decoded response (decode with specials preserved). Summarize per arm.
4. Fix the echo span bleed fable found (results/h1-review-fable.md, "dangling ' Constraint' token"): the span
   window for the echo must end at the clause boundary; add a test that the rendered echo for a marked span
   contains no trailing " Constraint" fragment and no reminder sentence.
5. Summary: the H1′ integer-count safety table (timeouts, truncation events, degenerate sessions,
   invalid_output events, each vs full), the four registered contrasts + `full_echo - full`, recovered
   fractions, and the paired bootstrap CI already present.

## Allowlist
See h1prime-auto-select.allow.

## Tests first (TDD, rule 1)
CPU-only, no model load: (a) `--focus auto` routes span selection through the salience finder and never reads
marks (monkeypatch the finder; assert the marked-span reader is not called); (b) auto_coverage/auto_extra on a
synthetic marked history; (c) invalid_output detection table; (d) echo bleed regression; (e) summary safety
table and full_echo contrast from synthetic records. RED first.
Run ONLY: `set -o pipefail; uv run pytest -q tests/test_ledger_kv_probe.py tests/test_ledger.py tests/test_salience2.py`.
DO NOT run the full suite.

## GPU policy
Check `nvidia-smi --query-compute-apps=pid --format=csv,noheader`; if empty you may run ONE smoke:
`uv run python scripts/ledger_kv_probe.py --focus auto --sessions 2 --max-new 64 --out ledger-kv-probe-h1p-smoke`
and verify the seven arms + new fields. Foreground only; never terminate or signal any process. If the GPU is
busy, skip the smoke and say so.

## Acceptance
Targeted tests green; ruff clean on touched files; oracle mode output for 1 session is byte-identical to the H1
harness (regression: run the CPU record-schema test on results/qwen/ledger-kv-probe-h1/session-000.json);
no edits outside the allowlist; commit your work yourself before finishing.

## Ledger handoff
Append to WORKLOG.md: files touched, RED->GREEN evidence, how marks are kept away from the arms in auto mode,
smoke field check (or why skipped), and any deviation from the registered H1′ text with the reason.
