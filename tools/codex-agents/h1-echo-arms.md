# Brief: h1-echo-arms — add echo_only and pinned_echo arms to the KV probe (FOCUS LADDER v1, H1)

## Objective
Implement exactly the two new arms registered in LEDGER-PLAN.md "FOCUS LADDER v1 / H1" in
`scripts/ledger_kv_probe.py`, nothing else:
- `echo_only`: evicted (no pins) + the echo.
- `pinned_echo`: pinned (ledger spans kept, exact-column control unaffected) + the echo.
The echo is the registered renderer `stencil.ledger.text_ledger_context(context, entries)` applied to the
last-turn context BEFORE tokenization, with `entries` built from the same aged "Constraint:" spans the
harness already marks (build `Entry` objects with the span text; reuse the existing Entry constructor in
src/stencil/ledger.py — do not invent a template). Assert the echo lands before the final user
`<|im_end|>`, reject any chat-control token inside the echoed text, and record `echo_tokens_added` (int)
and `echo_text_sha256` per session. Because the echo changes the token ids, the prefill for the two echo
arms is a separate forward on the echoed ids; the eviction range must be recomputed for that tokenization
(the prior-history span is the same text, so recompute its token boundaries on the echoed ids — do not
reuse the un-echoed indices). Everything else (dose arms, control matching, provenance, token ids) stays
as in v3.
Per-record additions for EVERY arm: `quoting` (bool: the response reproduces >= 8 consecutive echoed
tokens; always false for non-echo arms) so the summary can report a quoting-excluded secondary pass rate.
Summary additions: per-arm `quoting_rate`, `pass_rate_quoting_excluded`, in-job `gap = full - evicted`
passes, and the four registered contrasts (pinned-evicted, echo_only-evicted, pinned_echo-echo_only,
pinned-pinned_control) as pass-count differences plus recovered fraction of the in-job gap.

## Allowlist
See h1-echo-arms.allow.

## Tests first (TDD, rule 1)
CPU-only, no model load, in tests/test_ledger_kv_probe.py: (a) the echo arm context equals
`text_ledger_context(context, entries)` byte-for-byte and its insertion point precedes the final
`<|im_end|>`; (b) a chat-control token inside a span raises; (c) the eviction range recomputed on echoed
ids covers the same history text (decode both ranges and compare); (d) `quoting` detection on a
synthetic response (8-token overlap true, 7 false, non-echo arm always false); (e) summary contrasts and
recovered fractions from a synthetic 3-session record set. Write them RED first.
Run ONLY targeted tests: `set -o pipefail; uv run pytest -q tests/test_ledger_kv_probe.py tests/test_ledger.py`.
DO NOT run the full suite (a full run took > 2 h last time and timed out the wrapper).

## GPU policy
The GPU is IDLE now (nvidia-smi compute apps = 0) and you may use it to smoke ONLY:
`uv run python scripts/ledger_kv_probe.py --sessions 2 --max-new 64 --out ledger-kv-probe-h1-smoke`
and confirm all six arms produce records with the registered field list. Check
`nvidia-smi --query-compute-apps=pid --format=csv,noheader` is empty immediately before; if not, skip the
smoke. Foreground only. Never terminate or signal any process.

## Acceptance
Targeted tests green; ruff clean on the touched files; smoke record has all six arms and the new fields;
no edits outside the allowlist; commit your work yourself with a clear message before finishing.

## Ledger handoff
Append to WORKLOG.md: files touched, RED->GREEN evidence for each test, the smoke's per-arm field check,
and any deviation from the registered H1 text with the reason.
