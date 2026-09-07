# Pre-launch driver fix (CPU only) for gpt-6-astra: pilot-5 driver items N1/N2 (2026-09-06)

Source: results/slab2-review-fable-r2.md sections "New items from the driver" (N1, N2) and its pre-launch
instruction; plus results/slab2-review-r2-opus-crosscheck.md if that file exists (apply anything it marks blocking).
This is the LAST step before pilot 5 launches. No science change.
1. N2: in scripts/composition_pilot5.py `VLLMDecoder`, add `stop_token_ids=[151645, 151643]` to the completions
   payload (matching results/quick-checks/vllm-qual/request-parameters.json), and raise ValueError when
   `finish_reason == "stop"` and the last returned token id is not one of those terminal ids (never silently set
   eos=None — loop.py:342-344 would then append no terminator and every later prompt in the lane is malformed).
2. N1: raise the HTTP timeout from 300 s to 1200 s (a 2,048-token capped reply at ~6 tok/s per stream is ~330 s).
3. Re-run tests/test_focus_slab2_driver.py and tests/test_focus_slab2.py (+ tests/test_no_side_effect_imports.py);
   add a driver test for the terminal-id guard (mock a stop with a non-terminal last id -> raises).
4. Append a two-line note to tests/fixtures/slab2_cpu_report.md under Amendment 1 recording N1/N2 as applied.
Commit only scripts/composition_pilot5.py, tests/**, tests/fixtures/slab2_cpu_report.md, WORKLOG (<= 4 lines) with
explicit pathspecs; no push; no GPU (check 47 owns it; never touch RUNNING.flag files or containers); never
terminate or signal any process; never read anything under data/bench. Report test counts.

ADDED from the Opus crosscheck (results/slab2-review-r2-opus-crosscheck.md): N1 and N2 are ALREADY EDITED in the
working tree but UNCOMMITTED and UNTESTED (O1) — do not redo them; instead (a) verify the three lines are present
(timeout=1200; stop_token_ids=[151645,151643]; the raise when finish_reason=="stop" and the last id is not
terminal), (b) add the missing assertions/tests for all three, (c) commit them. Also (O2): pilot 5 must launch
from a PINNED, GREEN commit — after committing, run the targeted suite once more, record the exact commit sha in
tests/fixtures/slab2_cpu_report.md, and the pilot-5 run must check out/verify that sha before touching the GPU.
And (H3 headroom): the 12 GPU-h gate's x-factor boundary is 1.3504 while the reserved projection is 11.9972 h at
x1.35 — read the MEASURED x-factor first and do not treat the reserved number as headroom.
