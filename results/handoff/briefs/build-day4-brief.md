# Build brief (CPU only) for gpt-6-astra: composition v2, Day 4 — fix the package review findings (2026-09-06)

Fable's code review results/focus-package-review-fable.md (read it fully; file:line cited). Continue from the current
src/stencil/focus/ (Days 1-3; run all tests/test_focus_*.py first). Fix, in this order, without over-engineering:
H1 custom_generate/generate.py must work through the REAL HF dispatch: transformers 5.16.1 generation/utils.py
   forwards named args as kwargs (generation_config, logits_processor, stopping_criteria, prefix_allowed_tokens_fn,
   synced_gpus, assistant_model, streamer, negative_prompt_ids, negative_prompt_attention_mask, use_model_defaults,
   ...) — accept and ignore/forward them per the HF custom-generate contract (cite the doc), and add a CPU test that
   calls `model.generate(custom_generate=<local dir>, trust_remote_code=True, ...)` on a TINY randomly initialised
   HF causal LM (e.g. a 2-layer config built in the test; no download, no GPU) with the focus session injected, and
   asserts exactly one forward-generation and the journal record. Also local-only loading of assets.
M2 decode failure must leave session state consistent: either roll back messages/rendered_history/clock atomically
   or record the failed request as a journaled failure with history_ids appended; add a test that the next request
   after a failure renders consistent bytes.
M4 same-run oracle/checker writer: journal API accepts hidden checker results per round from the evaluation harness
   (inaccessible to the model) and writes them in the same run; remove the always-None field; test it.
M1 AST fence: keep it as a deterrent but make it honest — document its limits in the test docstring; add the obvious
   idioms fable listed (.count, .find, startswith/endswith, fnmatch, importlib of re, operator.contains) to the scan;
   do not chase completeness. Fix the directory glob so untracked files in the package do not break it.
M5 make test_explicit_path_never_calls_legacy_helpers non-vacuous (monkeypatch legacy helpers to raise; run the
   golden episode).
LOW: reject duplicate message ids across requests; stop embedding full history in every journal classifier context
   (reference by message ids); drop or document the value-equality echo checks; make "user task rule under a same-key
   system rule never applies" explicit (journal a shadowed reason); validate the actuator string before recording.
M3 (renderer bytes vs FOCUS-3) is NOT for today: leave the layout; it is frozen on DEV in the Day 5 pilot.
Commit only src/stencil/focus/**, models/stencil-package/**, tests/test_focus_*.py, tests/fixtures/focus_*, WORKLOG
(<= 6 lines) with explicit pathspecs; run all tests/test_focus_*.py + tests/test_no_side_effect_imports.py; no push;
no GPU; never terminate or signal any process; never read anything under data/bench. Report test counts.
