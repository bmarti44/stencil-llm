# Build brief (CPU only) for gpt-6-astra: composition v2, Days 1-2 — explicit register, renderer, one-generate loop, journal (2026-09-06)

Governing design: results/focus-mechanism-composition-v2-astra.md section 1 (FIRST-SHIP v1 SCOPE) — implement exactly
that, nothing from the cut list. Reuse the existing FOCUS-3 controller code (src/stencil/focus3.py, src/stencil/
focus_cache.py, src/stencil/admission.py, scripts/focus3_gate.py — read them first; keep their proven renderer rules:
every-request rendering of ALL live obligations including defaults after cancel/complete). Do not launch any model;
do not touch the GPU (check 44c / relations v3 / 40k own it); do not edit files under results/quick-checks/ or
data/classifier/; never read anything under data/bench.

Deliverables (new package src/stencil/focus/ with tests under tests/test_focus_*.py; all CPU; pytest targeted):
1. register.py — immutable event history + derived live view. Entry schema {action: add|supersedes|cancels|completes|
   reinstates, key, scope{task_handle?, request_kinds?}, kind: language|style|format|process, value, text?,
   target_version?, event_id, source{role, message_id, span?}}. Rules per v2: target_version required for any op on an
   existing rule; reject missing/ambiguous/stale targets, unsupported scope intersections, incompatible same-scope
   additions; idempotent by event_id; a malformed transaction changes nothing; reinstates creates a NEW version
   referencing the retired one; retirement is a live-view mask (never deletion); narrower declared exception shadows
   only in its scope; cancellation reveals the broader rule or the configured default. Optional classifier hook:
   `validate(entry, context) -> Decision` interface with an ABSTAIN path (assistive only; journaled; never
   reinterprets an explicit action). No regex/keyword/substring semantics anywhere (explicit ID/enum equality only).
2. renderer.py — one frozen layout: compact ordered live block (global, task, request-local, with provenance tags),
   then a labelled retired/tombstone block (first three generation requests after retirement: "Retired: <key> v<n>; no
   longer binding in <scope>; replaced by <key> v<m> | default <value>"), then the request; request-kind matching
   (final-answer schema never rendered on a tool-call envelope; system code-block default applies to code answers);
   deterministic bytes; a `render(register, request) -> RenderedRequest` with the exact token-level placement used by
   focus3 (cite the function you copied). Overflow returns an explicit error, never drops obligations.
3. loop.py — `generate_once(session, new_messages, decoder, tools=None, actuator="off")`: authenticate entry ->
   validate/classify -> atomic live-view update -> applicability -> render -> install optional experimental hook/mask
   (interfaces only; actual hook = existing check-40i code path referenced, not reimplemented) -> ONE decoder call
   (injected callable; tests use a fake decoder) -> restore in finally -> return literal output + session state.
   No retry/selection/self-grading. Tool results come back as another request.
4. journal.py — same-run append-only JSONL writer with the full field list from v2 ("Write the same-run journal...");
   dry-assert the field list through the real writer in a test.
5. custom_generate/ layout scaffold at models/stencil-package/ (generate.py entry that wires the loop over an HF
   model when one is provided; requirements.txt; MANIFEST.json with asset hashes placeholders; README documenting
   session args/returns). Must import and run with the fake decoder on CPU. No weights copied.
Tests to write and pass (CPU, targeted): wrong/stale target_version rejected; quoted/tool/assistant negatives cannot
acquire authority; cancel restores broader rule then default; reinstate creates a new version; tombstone renders for
exactly three requests; request-kind matching; renderer determinism (byte-equal across calls); loop calls the
decoder exactly once and restores hooks on exceptions; journal field list complete; package imports.
Process: commit with explicit pathspecs only the files you create/edit (src/stencil/focus/**, tests/test_focus_*.py,
models/stencil-package/**, WORKLOG entry <= 6 lines); run `pytest tests/test_focus_*.py tests/test_no_side_effect_imports.py -q`
before committing; no push; never terminate or signal any process; foreground only. Report the test counts in your
final message.
