# Build brief (CPU only) for gpt-6-astra: composition v2, Day 2 — strip the regex layer; immutable event log (2026-09-06)

Fable's v2 review (results/composition-v2-review-fable.md, finding H2) found that src/stencil/focus3.py binds scope,
kind, request kind, task handle and the reinstatement veto with regexes (scope_of, kind_of, request_kind,
selected_task, cancellation_message) and that Register.retire mutates status in place. Brian's rule: no string
matching in the register; classifiers or explicit typed fields only. Continue from the Day 1-2 package in
src/stencil/focus/ (read its WORKLOG entry and tests first; run them):
1. Make the explicit path regex-free: scope/kind/request-kind/task-handle come ONLY from the typed entry or declared
   request metadata; any semantic judgment goes through the classifier hook (assistive; abstain path). Add a test that
   imports src/stencil/focus/* and asserts none of its modules reference the `re` module or str.find/in-substring
   heuristics on rule text (an AST scan test), and that focus3's regex helpers are never called on the explicit path
   (fence them behind a clearly named legacy module used only by the FOCUS-3 gate scripts; do not break
   scripts/focus3_gate.py or its tests — run tests/test_focus3*.py if present).
2. Confirm the register is an immutable event log + derived live view (no in-place status mutation; retirement =
   live-view mask; history queries return every version with its transition evidence). Add property-style tests:
   replaying the event log reproduces the live view; no event ever disappears; idempotent event ids.
3. Add the named session-state fields fable asked for (register events, live view, request bindings, journal cursor,
   experimental flag state) and a stub-decoder whole-episode CPU dry run test: 12 requests with add / supersede /
   cancel / complete / reinstate / tool continuation, asserting the rendered bytes at each step (golden file under
   tests/fixtures/) and the journal records.
Commit only src/stencil/focus/**, tests/test_focus_*.py, tests/fixtures/focus_*, src/stencil/focus3_legacy*.py if
created, WORKLOG (<= 6 lines) with explicit pathspecs; run the targeted tests + tests/test_no_side_effect_imports.py;
no push; no GPU; never terminate or signal any process; never read anything under data/bench. Report test counts.
