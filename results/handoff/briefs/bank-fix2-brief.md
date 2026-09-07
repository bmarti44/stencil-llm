# CPU fix pass for gpt-6-astra: harness defects found by fable's re-pilot review (2026-09-06)

Read results/composition-pilot-2-review-fable.md fully. Register the amendment (in results/quick-checks/
composition-pilot-2/README.md, an "Amendment 2" section written BEFORE code) and then fix, arm-neutrally:
1. NEWLINE BOUNDARY on `edit` append: 0/95 model edits end with "\n" and the Executor appends raw, so "...]def
   step_1" breaks the module from round 1 in every lane. Insert a newline boundary in the append semantics (update
   edit_semantics; refresh DEV fixture hashes); re-run pilot_recovery on the pilot-1 records expecting integration
   success to recover with style-only residue; report the recovered final-success and per-kind counts.
2. INDENT OBLIGATION rendering: "add indent -> 3." is cryptic against a strong 4-space prior; 0/95 edits followed
   it, including after the supersede to 2. Add ONE gloss sentence to the renderer's kind=style value rendering
   (e.g. "indent 3 = block bodies indented by exactly 3 spaces") — this is a value-rendering rule, not a layout
   change; record it as a registered renderer amendment with a new golden (the frozen golden is superseded by
   amendment, keep the old one). Then on the CPU there is no way to test compliance; mark "round-0 compliance
   check on the DEV screen" as a required gate of the next GPU pilot: if compliance stays 0, swap the style trait
   (e.g. naming convention or docstring-first) before the larger test — pre-write that rule now.
3. BACKEND RULING conditions (fable): record in the amendment that (a) backend selection is outcome-blind and
   supersedes the <=1-divergence gate, (b) schedule-level determinism must be verified (cold/warm single-stream,
   mixed-arm concurrency 4, D=0), (c) EOS/cap/context semantics identical across arms, (d) the ship claim reports
   backend identity, HF<->backend divergence with first positions, run-to-run D=0, controller hashes, and either
   an end-to-end DEV subset on the custom_generate path or an explicit "package path outcome-unvalidated" line;
   hidden-state artifacts are HF-only (teacher-forced prefill).
4. Interface residue: journal (not repair) Python-literal True/False; T's cumulative re-emission stays as-is (T is
   the comparator; its truncation counts as breakage symmetrically — say so); the batch-N fabricated arrays are moot
   (batch dropped).
Tests for each; run all tests/test_focus_*.py + tests/test_no_side_effect_imports.py; commit with explicit
pathspecs (src/stencil/focus/**, tests/**, fixtures, results/quick-checks/composition-pilot-2/README.md, WORKLOG
<= 6 lines); no push; no GPU (vLLM qualification is running; never touch its container or flag); never terminate
or signal any process; never read anything under data/bench or evaluation episode content.
