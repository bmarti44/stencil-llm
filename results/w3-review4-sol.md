codex
Not cleared — one **HIGH** remains.

[test_reinsertion_reminder_clean](/home/bmarti44/stencil-llm/tests/test_s0c_clean.py:80) does not exercise `run_session`; it duplicates the corrected boolean and calls `ledger_text` directly. It would have passed against the previously buggy runner.

Extract final prompt construction into a pure helper used by [run_session](/home/bmarti44/stencil-llm/src/stencil/t2_runner.py:149), then test that helper after reinsertion. The W3a job must apply its zero-occurrence assertion to this final arm-specific prompt immediately before tokenization. This also prevents accidental reuse of the still-unclean standalone path in `w0_replay.py`.

The current one-line runner fix is correct, and 13.8M remains untouched; no rebind is needed.
