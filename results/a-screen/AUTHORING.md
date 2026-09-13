# Authoring brief: SCREEN pool sessions for the six-family candidate-A screen

Governing document: `results/a-screen/REGISTRATION-A-SCREEN.md` (read §1, §5, §6, §10).
Schema: `src/stencil/a_screen.py` (`Session`, `Request`, `Turn`). Exemplar that passes every
self-check: `src/stencil/a_screen_pool/s02.py`. One module per slot, `src/stencil/a_screen_pool/sNN.py`,
exposing `build() -> Session` with `id="SNN"`. Never read `data/bench/`. Do not reuse the
pre-check projects (inventory, mailer, catalog, auth, ledger, exporter, settings, queue), the
development projects (kvstore, fileio, users, config) or the exemplar (ticketing). Each slot has
its own domain (table below); package names must be unique and not collide with stdlib or
installed packages.

## Family states (use these exact state keys and meanings everywhere)

Targets (the family that changes or stays; two states):
- `naming`: `verb_noun` | `noun_verb` — names of NEW public methods/functions (existing names stay).
  Contract test: `hasattr` on the required name AND `not hasattr` on the other spelling.
- `validation`: `api` | `storage` — where input validation lives. `api`: the public entry function
  raises `ValueError` on invalid input and the lower (storage/model) layer does NOT raise when
  called directly with the same invalid value. `storage`: the lower layer raises `ValueError` when
  called directly and the public function lets it propagate (no separate pre-check; test via a
  spy/monkeypatch that the lower layer was called with the invalid value, or that the lower layer
  raises). Both suites must pass on their own gold and fail on the other state's gold.
- `missing_record`: `none` | `raise` — an action on an unknown id returns `None` (and changes
  nothing) vs raises `KeyError`.

Supports (stated once in the prefix, never changes; the session fixes ONE state):
- `return_shape`: `dataclass` | `dict` — public operations return dataclass instances vs plain dicts.
- `error_surface`: `wrap` | `propagate` — lower-layer exceptions (I/O, transport, parsing) are wrapped
  in a package exception class vs propagate raw.
- `logging`: `warn` | `silent` — the notable condition the request names emits EXACTLY ONE
  `logging.warning` (assert count == 1 with caplog) vs emits no log record at all.

Registration §10 coverage rule: every contract test covers every operation the contract wording
names; count-sensitive checks assert exact counts; if existing code predates a rule, the rule text
either grandfathers it explicitly or the test covers the migration.

## Lifecycle classes

- `stable`: `state_at = (A, A)`; `event` is a plausible but contract-irrelevant user message.
- `replacement`: `state_at = (A, B)`; `event` states the new convention B for new code.
- `scope`: `state_at = (A, B)`; `event` introduces a scoped exception ("for <scope>, use B") and
  request 2 is unambiguously inside that scope (request 1 was outside it).
- `reinstatement`: prefix states A (turn 8–10) AND later replaces it with B (turn 12–13);
  `state_at = (B, A)`; `event` reinstates A. `rule_turns` includes the replacement turn too.

## Session shape and sizes (measured with `uv run python scripts/a_screen_tokens.py SNN`)

- `files`: 3–4 small modules (≤ ~60 lines total) with an `__init__.py`; existing code follows the
  initial state (that is the stale precedent the screen is about).
- `prefix`: exactly 16 alternating user/assistant turns of realistic work on THIS project (README,
  design questions, pasted test drafts, tracebacks, snippets). Turns 0–7: 150–250 tokens each;
  turns 8–15: 50–150 each, with the support statement at turn 8 (assistant ack at 9) and the
  target statement at turn 10 (ack at 11). Prefix total MUST be ≥ 2,450 tokens so that the
  packing policy drops at least one turn before request 1 (the test enforces it), and turns 8–15
  must total ≤ ~1,300 so the rule turns survive request 2.
- Two `Request`s, same or different target file; request 2's gold builds on request 1's gold UNDER
  THE STATE IN FORCE AT CHECKPOINT 1 (see `_gold2` in the exemplar). Gold for both states at both
  checkpoints; functional tests name-agnostic (getattr helper) and state-agnostic; regression tests
  pin existing behaviour; `contract_tests` keyed by state; `support_tests` for the support state.
- Request texts never mention the contract states (the history carries them).
- Start the module with `# ruff: noqa: E501` and a one-line docstring naming slot, domain, families.

## Verification (must pass before you report done)

    uv run pytest -q tests/test_a_screen.py -k "SNN"     # every test for your slot
    uv run python scripts/a_screen_tokens.py SNN          # sizes, surviving turns
    uv run ruff check src/stencil/a_screen_pool/sNN.py && uv run ruff format src/stencil/a_screen_pool/sNN.py

Do not edit any file other than your own `sNN.py` modules. Do not commit.

## Slots

| slot | target | support | lifecycle | domain |
|---|---|---|---|---|
| S01 | naming | return_shape | stable | recipes |
| S02 | naming | return_shape | replacement | ticketing (exemplar, done) |
| S03 | naming | return_shape | scope | library loans |
| S04 | naming | return_shape | reinstatement | parking permits |
| S05 | naming | return_shape | stable | gym memberships |
| S06 | naming | return_shape | replacement | seed catalog |
| S07 | naming | error_surface | scope | bus timetable |
| S08 | naming | error_surface | reinstatement | chess ratings |
| S09 | naming | error_surface | stable | plant watering |
| S10 | naming | error_surface | replacement | podcast feeds |
| S11 | naming | error_surface | scope | invoice numbering |
| S12 | naming | logging | reinstatement | room booking |
| S13 | naming | logging | stable | pet vaccinations |
| S14 | naming | logging | replacement | wine cellar |
| S15 | naming | logging | scope | bike repairs |
| S16 | naming | logging | reinstatement | coupon codes |
| S17 | validation | return_shape | stable | classroom attendance |
| S18 | validation | return_shape | replacement | weather stations |
| S19 | validation | return_shape | scope | board-game lending |
| S20 | validation | return_shape | reinstatement | donation pledges |
| S21 | validation | return_shape | stable | conference talks |
| S22 | validation | error_surface | replacement | shift scheduling |
| S23 | validation | error_surface | scope | warehouse bins |
| S24 | validation | error_surface | reinstatement | garden plots |
| S25 | validation | error_surface | stable | music playlists |
| S26 | validation | error_surface | replacement | translation glossary |
| S27 | validation | error_surface | scope | film festival |
| S28 | validation | logging | reinstatement | tax receipts |
| S29 | validation | logging | stable | fleet fuel logs |
| S30 | validation | logging | replacement | apartment maintenance |
| S31 | validation | logging | scope | book club |
| S32 | validation | logging | reinstatement | gallery loans |
| S33 | missing_record | return_shape | stable | course grades |
| S34 | missing_record | return_shape | replacement | laundry tokens |
| S35 | missing_record | return_shape | scope | bakery orders |
| S36 | missing_record | return_shape | reinstatement | volunteer hours |
| S37 | missing_record | return_shape | stable | river gauges |
| S38 | missing_record | error_surface | replacement | museum tickets |
| S39 | missing_record | error_surface | scope | drone flight logs |
| S40 | missing_record | error_surface | reinstatement | scholarship applications |
| S41 | missing_record | error_surface | stable | trail reports |
| S42 | missing_record | error_surface | replacement | beekeeping hives |
| S43 | missing_record | logging | scope | radio schedule |
| S44 | missing_record | logging | reinstatement | lost and found |
| S45 | missing_record | logging | stable | choir roster |
| S46 | missing_record | logging | replacement | carpool |
| S47 | missing_record | logging | scope | tool library |
| S48 | missing_record | logging | reinstatement | farm-share boxes |
