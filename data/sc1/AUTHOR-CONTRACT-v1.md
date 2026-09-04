# SC1 authoring contract — delayed-use episodes for the selector comparison (v1 draft, 2026-09-04)

You are writing ORIGINAL, fictional, self-contained multi-turn episodes in which an assistant must use information
stated earlier in the conversation to complete a final request. You are NOT told which memory policy is expected to
win, and you must not consult, paraphrase, or imitate any public benchmark (IFEval, Multi-IF, BFCL, tau-bench,
ACEBench, LongMemEval, MemoryCode, or any other). Do not reuse any names, IDs, values, or phrasings from anything you
have seen in this repository's data/ or results/ directories. Every scenario must be semantically distinct from every
other: changing names or numbers does not make a new scenario.

## Episode shape
- 12-24 scripted turns (user, assistant, tool) totalling 4,096-8,192 tokens before the final user request.
- Two styles, sampled 50:50 per episode (recorded, not balanced after the fact):
  * EDITING: the final request produces a bounded JSON patch or a small text artifact (<= 40 lines) checked by an
    executable schema/content rule (exact required keys/values/lines; forbidden content).
  * TOOL-WORK: the final request is ONE function call into an isolated in-memory database whose complete resulting
    state is checked (target record correct; protected records untouched).
- Indispensable information for the final request: origin USER-stated vs TOOL-returned, sampled 50:50; located OLD
  (before the most recent 1,024 history tokens) vs RECENT, sampled 50:50. Both old tool facts and recent user facts
  must sometimes matter; the episode must not be solvable from role or position alone.
- Scope status of the governing instruction, sampled 25% each: CONTINUING (still applies); OVERRIDDEN (a later user
  turn changes it; the new version governs); CANCELLED-OR-COMPLETED (a later turn cancels it or the task it belonged
  to is verifiably done; it must NOT be applied); SWITCHED (the conversation moves to a different task and back, and a
  persistent user rule still applies across the switch).
- Distractors: benign durable-looking facts and transient chatter, some old and useful, some recent and useless.
  Never a special marker that reveals relevance.
- Entities: fictional names, 6-12 character identifiers, exact values, sampled from a pinned seed per episode
  (record the seed); reject collisions across episodes using the episode data alone.
- The final request must OMIT the literal/rule being tested (no restating it); it must be impossible to pass by a
  no-op, an empty output, or a generic answer.

## Reference and checker
- Provide: the exact expected artifact/state, and a checker specification listing every obligation and invariant.
  One binary pass = ALL obligations and invariants hold. Missing objects, malformed output, stale values (from an
  overridden/cancelled instruction), collateral edits, and unfinished generation FAIL.
- Provide six adversarial mutations that must FAIL the checker: old-ID substitution, cancelled action executed,
  wrong entity, wrong scope, empty output, collateral edit. A reviewer will run them.
- References and checkers are hidden from every memory policy; they never appear in the history text.

## Record format (one JSON object per episode)
{"id": "...", "seed": 0, "style": "editing|tool", "origin": "user|tool", "age": "old|recent",
 "scope": "continuing|overridden|cancelled|switched", "system": "...", "tools": [...schemas or null...],
 "turns": [{"role": "user|assistant|tool", "text": "..."}...], "final_request": "...",
 "initial_state": {...} , "reference": {...}, "checker": {...}, "mutations": [...]}
Setup episodes (32, separate authors' pool, used only to verify model competence and timing) use the same format and
share no story, entity, or task with the 256 final episodes.
