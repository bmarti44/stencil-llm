# FOCUS composition package review (fable, one round, 2026-09-06)

Scope: commits a25ec9d7 and 06be38d0 — `src/stencil/focus/{register,renderer,loop,journal,__init__}.py`,
`tests/test_focus_{composition,boundary,event_log,episode}.py`, `tests/fixtures/focus_episode.json`,
`models/stencil-package/**`. Checked against `results/focus-mechanism-composition-v2-astra.md` section 1
and my `results/composition-v2-review-fable.md` (H2: regex-free explicit path; immutable event log).
CPU only via `.venv/bin/python`; no model launched, no GPU, nothing under `data/bench` read; only this
file written. I also ran two scratchpad probes (AST-fence defeats; register/loop edge semantics; a
simulation of transformers' custom_generate dispatch) — results quoted below.

Note: `src/stencil/focus/slab.py` (untracked, mtime 09:52, a concurrent coder's SLAB-1 generator,
`.review.lock` held) appeared mid-review. It is outside scope and untouched, but it is evidence for M1.

## 0. Test run

`pytest tests/test_focus_composition.py tests/test_focus_boundary.py tests/test_focus_event_log.py
tests/test_focus_episode.py -q` -> **60 passed** (0.89 s). `tests/test_focus_*.py` collects 63 (the
extra 3 are pre-existing `test_focus_check43b.py`). The WORKLOG's "158 passed" is the union with the
legacy focus3 and no-side-effect suites; the new package carries 60 tests, not 158. Ruff is clean on
all reviewed files (the 91 errors `ruff check src/stencil/focus` now reports are all in the untracked
`slab.py`). After `slab.py` appeared, `test_all_explicit_modules_import_and_pass_ast_fence` FAILS
(see M1); the 60/60 above was taken before it existed.

## 1. Brian's invariants — verified (register.py unless noted)

- No regex/substring on rule text in the explicit path: true of the shipped code. `re` is not
  imported anywhere; `focus3` is not imported. The only string comparisons on rule content are exact
  `==`/`!=` echo checks against the addressed target (335, 341-342); see L3.
- Masking-only retirement: `Register`, `Version`, `Retirement`, `Entry` are frozen dataclasses;
  `_apply` returns `replace(self, events=..+(e,), versions=.., retirements=..)` (378-384); no status
  field exists to mutate; `live_mask` is derived (285-287). `FrozenInstanceError` asserted in tests.
- Every-request rendering incl. defaults after cancel/complete: `live()` (386-424) appends
  `Version(d, 0)` for any default whose key has no live explicit version; `test_tombstone_exactly_three`
  asserts `live[0].value == "4"` (the default) on all four requests after cancel; episode fixture
  shows the empty live block `[]` when no default is configured.
- `target_version` required for non-add: 318-320 rejects `None`/wrong/ambiguous; `True` is rejected
  by `type(...) is not int` (157). `add` with a target is rejected (343-346, probed).
- Idempotent event ids: identical replay returns `self` (308-312); same id with different content
  raises "event ID collision"; 12 randomized 40-step sequences check both plus `replay == state`.
- Reinstates creates a new version: 328-338 requires the target to be retired, not already
  reinstated, same scope/authority, identical value/text; new `Version(previous=target.version)`.
  Probed: changed value -> rejected; changed scope -> rejected; reinstating v1 while v2 is live ->
  rejected ("same-scope addition requires exact supersedes target").
- Authority: user cannot supersede/cancel a system rule (probed, rejected); developer can retire a
  user rule (probed, accepted); `authenticate` (loop.py:103-122) rejects tool/assistant/quoted/code
  origins and role spoofing (5 parametrized cases + spoof test).

## 2. Renderer (renderer.py) vs the proven FOCUS-3 renderer (src/stencil/focus3.py:258-271)

Correct: tombstone window is exactly three generation requests — `0 <= generation - r.generation < 3`
(52) with the clock advanced once per accepted request (loop.py:264-266); the request that carries
the retirement counts as #1, observed `[1,1,1,0]`. Tombstones are scope-filtered by the retired
version's scope (59; probed: task-A retirement invisible to task B), show reason and current
replacement/default, never the retired value, and mark reinstatement (69-75). Request-kind matching
via `Scope.contains` (90-95) — `final_answer` schema does not govern `tool_call` (tested). Output is
deterministic (`sort_keys`, sorted `request_kinds`, sorted live tuple). Overflow raises
`RenderOverflow` (116-120) rather than dropping rules; without an encoder a token budget also raises.
Token placement (system + history_ids + envelope) and the closure logic (loop.py:287-300) match
`scripts/focus3_gate.py:405-431` given focus2 `EOS=151645` (im_end) / `END=151643`.

Divergences from FOCUS-3's bytes (spec permits a new frozen layout, but none of this has met a model):
(a) header "Active user rules ..." -> "Active rules ..."; instruction sentence reworded; (b) row schema
`{id,version,scope,task_id,text}` -> `{key,version,kind,value,text,scope,provenance,default}`;
(c) FOCUS-3 returned the bare request when nothing was live; the new renderer always emits the
wrapper, including `[]` and an empty "Retired rules (not binding):" line (probed) — so the R arm's
"nothing to say" request is not the raw request; (d) the current-request envelope is
`compact([{role,text,tool_results} per new Message]) + "\n" + Request.text` (loop.py:208-219): two
texts per request (`Message.text` vs `Request.text`) with no defined relation, and tool results
appear as `role:"tool"` JSON inside the user turn. See M3.

## 3. Loop (loop.py)

Exactly one `decoder(rendered)` call (269); no retry, no selection; `tools` is metadata only and a tool
continuation is a new `generate_once` (tested with a `tool` message + `tool_result` kind). Hooks:
`hook` is bound before `install` (249) and `restore()` runs in `finally` (305-313) — verified for
decode failure and partial install; `restore` exceptions are journaled then re-raised; the journal is
appended on every exit path and the cursor advances only after a successful append (tested with a
broken writer). Register transaction commits before render and is atomic (tested: bad target leaves
`register == register()` and the decoder uncalled). Problems: M2, M4, L1, L2, L5.

## 4. Journal (journal.py) vs v2's list

All v2 groups present: raw/rendered messages and token ids; source events; classifier inputs,
scores, abstentions (`classifier_decisions` carries verdict/scores/reason); before/after versions and
live masks; defaults; applicability; output/EOS/truncation; attempted/executed tool calls, results,
artifact hashes; started/finished, cpu/wall/gpu-held seconds, input/output token counts; bias hash,
whole-body intervals, keep mask, absolute positions; failures, fallback reasons;
`oracle_checker_results`. `append` checks the exact field set before opening the file (tested: a bad
record leaves the file byte-identical). `rendered_messages` holds only the current envelope text
(history is in `rendered_token_ids`/session) — acceptable, note it. `oracle_checker_results` is
always `None` with no way to fill it (M4).

## 5. Package scaffold (models/stencil-package)

Contract (transformers 5.16.1, `generation/utils.py`): `load_custom_generate` (454-517) fetches
`custom_generate/generate.py`, requires `trust_remote_code=True` even for a local path, runs
`check_python_requirements` on `custom_generate/requirements.txt`, and returns the module's `generate`.
`generate()` (2372-2389) then calls `custom_generate_function(model=self, **generate_arguments)` where
`generate_arguments` = every named parameter of `GenerationMixin.generate` — `inputs`,
`generation_config`, `logits_processor`, `stopping_criteria`, `prefix_allowed_tokens_fn`,
`synced_gpus`, `assistant_model`, `streamer`, `negative_prompt_ids`, `negative_prompt_attention_mask`
— plus the caller's kwargs; the docstring (2338-2345) says the function "fully replaces the generation
logic, and the return type may differ", so the session-oriented return is allowed.

Simulated (scratchpad, no model): `load_custom_generate(M(), "models/stencil-package",
trust_remote_code=True)` succeeds (requirements 5.16.1 / 2.13.0 / 0.23.1 match the env). But calling
the returned function the way HF does, with those ten named arguments (all `None`) plus
`session=`/`tokenizer=`, raises `ValueError("unsupported generation options")` at generate.py:34-35 —
every time, regardless of user input. Passing `input_ids` (what `model.generate(**tok(...))` sends)
hits the deliberate rejection at 27-30. So with a real HF model the scaffold loads but cannot be
invoked through `model.generate(custom_generate=...)`; only a direct import with an injected
`decoder` works, which is all `test_package_import_and_fake_decoder` exercises. See H1.

The model-backed decoder body (43-74) is otherwise consistent with the gate: greedy, `custom_generate=None`
to avoid recursion, EOS drawn from `generation_config.eos_token_id`, body excludes EOS, truncation =
no EOS and `len >= max_new_tokens`. MANIFEST hashes are null and status is honest ("scaffold-only");
README states `stencil` must be importable from the checkout — the one-download contract is not yet met
and says so (L7).

## 6. Test quality

Meaningful: atomicity, stale/missing targets, cancel-reveals-broader-then-default, reinstatement
links, idempotence/collision, authority spoofing (5 cases), request-kind matching, 3-request window,
determinism/placement/overflow, finally-restore (3 cases), classifier assistive, real writer field set
with an independently enumerated `required` set, 12-seed randomized lifecycle with replay equality,
12-request golden episode with per-request masks/generations/journal rows, cursor-after-append.

Weak/vacuous: `test_explicit_path_never_calls_legacy_helpers` monkeypatches `focus3.<name>`; a
`from stencil.focus3 import scope_of` binding would be unaffected, and the package never imports
focus3, so it can pass with or without a violation — the AST import fence is what actually guards
this. `test_package_import_and_fake_decoder` never goes through `load_custom_generate` or HF's
dispatch (hence H1 was invisible) and its manifest asserts read back two JSON literals. The episode
goldens are byte-exact compact-JSON renderer output; "authored without the renderer" is unverifiable —
treat as a regression snapshot, not an independent oracle. `test_ast_fence_rejects_*` enumerates only
the idioms the fence was written for (see M1 for what it misses).

Missing negatives (behaviour probed correct, untested): add with `target_version`; reinstates with
changed value or scope; key-kind immutability; reinstate while a same-scope version is live; user
superseding a system rule; developer retiring a user rule; tombstone scope filtering; `restore()`
raising; decoder returning a non-str/non-DecodeResult; invalid actuator string; duplicate message id
across requests; session state after decode failure (M2).

## Findings (graded)

- **HIGH — H1** `models/stencil-package/custom_generate/generate.py:8-35`: through HF's own dispatch
  (`generation/utils.py:2372-2389`) the function always raises `ValueError("unsupported generation
  options")` because HF forwards ten named `generate` parameters as keywords and the scaffold rejects
  any kwargs when a model is supplied. The HF entry — the ship contract in v2 section 1 — is
  therefore unusable; only direct import + injected decoder works, and that is all the test covers.
  Fix: accept the HF named parameters, reject only those that are not `None` (keep the `input_ids`/
  `inputs` rejection), take `session` from kwargs, and add a test that calls the function exactly as
  `GenerationMixin.generate` does (or via `load_custom_generate` on the local dir with
  `trust_remote_code=True` and a stub `GenerationMixin`).
- **MEDIUM — M1** `tests/test_focus_boundary.py:12-72`: the AST fence is a deterrent, not a proof.
  Probed defeats that pass: `entry.text.count('cancel')`, `entry.text == 'cancel'`,
  `entry.text[:6] == 'Cancel'`, `entry.text.split()[0] == ...`, `operator.contains(entry.text, ..)`,
  `importlib.import_module('re')`, `__import__('re')`, `fnmatch.fnmatch(entry.text, ..)`,
  `match entry.text: case 'cancel'`, `{'cancel':1}.get(entry.text)`, `entry.text.replace(..)`,
  `'cancel' in retired` (bare name allowlisted at 17-24 — any module may bind a string to `retired`).
  Also its scope is a directory glob (76): the first new module dropped into the package (`slab.py`,
  17 benign container-membership lines) broke it. Fix: enumerate the explicit modules
  (register/renderer/loop/journal) instead of globbing; invert to a positive rule — `.text`/`.value`
  may appear only in dataclass construction, `asdict`, and `==`/`!=` against `target.entry.<same>`;
  ban `operator`, `fnmatch`, `difflib`, `importlib`, `__import__`, `re` by name; add the cases above
  as parametrized negatives.
- **MEDIUM — M2** `src/stencil/focus/loop.py:264-268 vs 285-300`: on decoder failure
  `session.messages` and `rendered_history` already hold the user turn and the tombstone clock has
  advanced, but `history_ids` gets nothing (probed: messages 1, rendered_history 1, history_ids 0).
  The next request's token prompt and message history disagree. Decide one rule (append both only
  after decode, or append the failed user turn to `history_ids` too) and test it.
- **MEDIUM — M3** `src/stencil/focus/renderer.py:94-105`, `loop.py:208-219`: the rendered bytes are
  new relative to FOCUS-3 (section 2 (a)-(d)); in particular the empty-register wrapper and the
  double text (`Message.text` JSON array + `Request.text`) with `role:"tool"` JSON inside the user
  turn. Define one meaning for the request text, render the bare request when nothing is live and no
  tombstone is due (so R equals N there), and freeze the result on DEV before any GPU minute, as v2
  requires.
- **MEDIUM — M4** `loop.py:176`, `journal.py:171`: `oracle_checker_results` is always `None` and no
  API can set it in the same record; the evaluator would have to rewrite journal lines, which is the
  "later reconstruction" v2 forbids. Add an optional `oracle` callback/argument to `generate_once` or
  a keyed companion record written by the same run.
- **MEDIUM — M5** test-count claim and coverage: 60 new tests, not 158; the HF dispatch path is
  untested (H1); `test_explicit_path_never_calls_legacy_helpers` is vacuous; goldens are a renderer
  snapshot. Correct the WORKLOG line and add the H1/M1/M2 tests.
- **LOW — L1** `loop.py:103-108`: message-id uniqueness is checked only within one batch; the same
  `message_id` is accepted again on a later request (probed), so `Source.message_id` provenance is
  not unique per session. Track ids on the session.
- **LOW — L2** `loop.py:185-190`: `classifier_inputs[i].context` embeds the entire `session.messages`
  and full register snapshot per entry — journal lines grew 4.9 kB -> 14.8 kB over five one-entry
  requests with 200-char outputs; O(n^2) over an episode. Store a cursor/hash into the record's own
  `raw_messages`/`before_versions` instead.
- **LOW — L3** `register.py:335, 341-342`: `cancels`/`completes`/`reinstates` compare the supplied
  `value`/`text` string-equal to the target's — acceptable as an echo integrity check (v2: identity
  checks are schema handling) but redundant with `target_version`; document it as such or drop it.
- **LOW — L4** `register.py:399-410`: a user task-local rule under a system global rule of the same
  key is accepted by `apply` but never selected by `live()` (authority wins first) — a silently
  never-applicable entry. Reject at apply time or render it as shadowed.
- **LOW — L5** `loop.py:178-183`: an invalid actuator string is recorded as
  `experimental_flag_state.requested` and consumes a `request_count` before validation.
- **LOW — L6** missing negative tests listed in section 6.
- **LOW — L7** README/MANIFEST honestly declare the unmet one-download contract and null hashes;
  keep the "scaffold-only" status string until the re-host and hash validation are done.
- **LOW — L8** tool-continuation task-handle inheritance is caller discipline (README), not enforced.

Verdict: the register and renderer implement Brian's invariants correctly on every case I could
construct (masking-only, immutable events, target_version, idempotent ids, reinstates-as-new-version,
defaults re-rendered after cancel, three-request tombstones, no regex/focus3 in the explicit path), and
the loop is one-call with finally-restore. Two things need fixing before this scaffold is called an HF
package: the HF dispatch path cannot invoke it at all (H1), and the regex fence is a lint that a
determined or even careless edit walks past and that the next package module already tripped (M1).
The M2-M5 items are build-week corrections; nothing here touches the science.
