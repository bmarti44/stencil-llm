# SC1 Stage 2 acceptance review (round 4) — fable (2026-09-04, CPU-only, read-only)

Reviewed HEAD 318a90c26e5f5fcf241ad23e3007eb61da1b0273. Freeze identity per the handoff: science/contract/source repair
022c034, executable/test commit c7f9b38 (manifest `harness_commit`), artifact freeze 75dec30, WORKLOG-only 318a90c.
Verified: every manifest-hashed code/contract/snapshot file at 318a90c hashes to the manifest entry, so the candidate
is code@c7f9b38 == code@318a90c, data@75dec30. Inputs: results/sc1-harness-v3-review-{astra,fable}.md, WORKLOG.md
"SC1 round-4 handoff", LEDGER-PLAN.md "SC1 AMENDMENT 1" (line 1292 to EOF), data/sc1/STAGE1-CLAUSES.md,
AUTHOR-CONTRACT.md vs AUTHOR-CONTRACT-v2.md, registration-snapshot.{md,json}, data/sc1/smoke/* (manifest, README,
validation, eight sources/episodes), the code diff 1612f69..318a90c (scripts/sc1.py, src/stencil/sc1_episodes.py,
tests/test_sc1.py; src/stencil/sc1.py unchanged).

Hard rules kept: CPU only (`CUDA_VISIBLE_DEVICES=''`); no model or GPU process (only the `tokenizers` Qwen3-4B
tokenizer file); foreground only; no process signalled; no sealed IFEval input or BFCL cohort file read by me (the
sealed-guard test was run as instructed, it is the one file allowed to touch that path); no repo write except this
file (`git status` clean before and after). Probes ran as pytest modules from the scratchpad
(`probe/test_snapshot.py`, `probe/test_cue.py`, `probe/test_old.py`; harness functions only; the old-behaviour
module is `git show 1612f69:src/stencil/sc1_episodes.py` loaded under a private module name; the registration-log
fixture from tests/test_sc1.py was imported so nothing could append to WORKLOG.md).

## What I ran

- `CUDA_VISIBLE_DEVICES='' uv run pytest -q -p no:cacheprovider tests/test_sc1.py tests/test_eval_data_separation.py
  tests/test_sealed_guard.py` -> **141 passed, 1 warning (pre-existing b2_gsm8k SyntaxWarning) in 371 s**;
  collected 135 + 2 + 4. This resolves the handoff's "unresolved command conflict": the two sealed-hash tests were
  run, not deselected, and pass; no sealed content was read by the reviewer.
- Snapshot arithmetic (probe/test_snapshot.py, all assertions hold): LEDGER-PLAN.md is 152,203 bytes; the DRAFT v2
  heading starts at byte 91,091, the AMENDMENT 1 heading at 128,466; `registration-snapshot.md` (83,953 bytes,
  sha256 c610e67f...e653) == ledger[91091:128466] + ledger[128466:152203] + AUTHOR-CONTRACT.md (22,841 bytes) with no
  inserted bytes, and == ledger[91091:] + contract (the two recipes in clause 1 coincide, as the reconciliation
  paragraph claims); the three part hashes/lengths equal registration-snapshot.json; ledger[128466:] is byte-equal
  to data/sc1/STAGE1-CLAUSES.md; ledger[:128466] is byte-equal to the whole 1612f69 ledger (nothing above the
  amendment changed, the DRAFT v2 section is unchanged from the v3 snapshot's first 37,375 bytes); the amendment is
  the last `## ` heading; AUTHOR-CONTRACT-v2.md == the 1612f69 contract; `verify_snapshot()` returns the sidecar.
- `verify_manifest(data/sc1/smoke/manifest.json)` -> OK: manifest_id a3966c05...7d04c, file sha256 2c7aa51d...699d0,
  harness_commit c7f9b38, 45 files (44 + registration-snapshot.json), `science_parts` == `verify_snapshot()`;
  `load_manifest_bank` -> 8 episodes; grammar.json == SCHEMA == manifest grammar. Every frozen episode equals a fresh
  `expand_source` (validate_bank's check_frozen path is what the 135 tests exercise; the h1 test re-renders all eight).
- Old-behaviour discrimination (probe/test_old.py, 9 cases, new tests executed against the 1612f69 episodes module):
  the four `test_astra_r3_duplicate_public_members_through_bank` blocks -> "DID NOT RAISE" on old code;
  `test_astra_r7_ordered_text_witness_through_bank[swap|reuse]` -> old code raises `inapplicable semantic attack:
  wrong scope`; `test_amendment_filler_newest_old_user_through_bank[designation|base]` -> "DID NOT RAISE" on old code;
  `test_fable_h1_pressure_binds_on_every_smoke_episode` -> `KeyError: newest_eligible_old_user_turn` on old code. All
  pass on 318a90c. So every new finding-named test fails on the old behaviour.
- Cue measurement on the frozen bank with the harness's own `render_episode`, `build_sc1_candidates`, `select_policy`
  (clf arm with hand-built scorers), `pin_composition`, real tokenizer — table below.

## (1) Residual findings closed

| Finding | Status | Evidence |
|---|---|---|
| astra R3/F6 residual (duplicate-member public JSON) | CLOSED | `validate_trace` decodes with `object_pairs_hook=public_pairs` (episodes:1144–1152) raising `ValueError("duplicate object name in public JSON")` before any member is lost; only `json.JSONDecodeError` is treated as incidental prose (:1161), so the semantic rejection propagates. Test: four wrapper/nested/pretty/non-state variants through `validate_bank` on the real smoke-05 tool turn; positive with incidental non-state JSON retained. Fails on old (DID NOT RAISE, measured). Grammar `state_trace` text and contract updated. |
| astra R7/F7 residual (positional text identity) | CLOSED | text branch keeps `original` as an ordered list and computes `changes` at ordered indices (`i >= len(original) or v != original[i]`, :1302–1310); JSON branch unchanged. Test: swap and repeated-value witnesses validate through the whole bank (reference passes, witness schema-valid), then evidence removed -> "semantic attack". Fails on old (measured: `inapplicable semantic attack`). |
| fable V1 (test bound to live ledger tail) | CLOSED | `test_fable_n3` asserts heading prefix, contract suffix, per-part hash/length/range and *containment* in the live source file, then appends a new `## Later editorial entry` section to a temp ledger and re-runs `snapshot` + `verify_manifest` + `verify_stage_freezes` -> identical output. |
| fable V2 (no snapshot producer) | CLOSED | `produce_snapshot`/`verify_snapshot` + `main(["snapshot"])` (scripts:267–367, :1467); parts must match committed bytes; manifests carry `science_parts` and the sidecar hash; `verify_stage_freezes` demands equal `science_parts`. The test invokes the real CLI in a committed temp repository with a tokenizer trap. |
| fable V3 (tests bound to proposal file) | CLOSED | `test_fable_n5` reads the frozen snapshot; the n3 fixture reconstructs the amendment from snapshot part 2, not from STAGE1-CLAUSES.md. |
| all 18 v2/v3 findings | remain CLOSED | their tests are in the 135 and passed. |

## (2) Orchestrator dispositions enacted verbatim

Checked sentence-by-sentence against the two v3 reviews (grep -F on distinctive sentences, then read in full):
A (preamble), B (three-part snapshot + seed sentence), C (relevance rule binding, no filler exception, Stage 2
deferred to this review), D, E, F, G (separate abandoned-cost reporting, 8 h cap cumulative per registered study), H
(projection) are present verbatim in clauses 1, 5, 6, 8, 9, 12, 13; fable's clause-1 replacement and the clause 2, 3,
6, 11 precisions are present verbatim. Decision (a)'s additional law — "the expander must never place formulaic
filler as the newest eligible old user turn" — is enacted as clause 4 text, SCHEMA `expansion` text, contract
paragraph, `validate_filler_placement` (episodes:1782–1792; called on the final rendered layout inside
`expand_source`, hence on every `validate_bank`/`validate_episode` re-expansion), the `newest_eligible_old_user_turn`
audit field, two negative bank-consumer tests and the eight positive checks. The implemented definition matches the
clause: greatest `message_index` among user candidates in the unscored universe, which by construction contains only
complete pieces inside `[P, R)` (straddling pieces are excluded, so a straddling turn qualifies through its complete
pieces); the guard rejects designation and any pool sentence in that turn's text, including authored base text.
Decision (c): producer mode exists; provenance recorded. Decision (b): clause 12 == G.

## (3) Independent cue review — frozen source/expansion law and the eight smoke episodes

Measured through `select_policy(layout, tok, "clf", scorer)` with scorers that see only one cue (score >= 0.5 is
eligible, then newest-first, as in `rank_clf`), plus the rule arm; "retained" = every necessary OLD evidence token
interval (`layout_audit.intervals`) fully inside the admitted columns. Column composition of U by provenance:

| ep | age | U | pool-sentence cols | filler-turn base cols | incidental (turn 7) cols | evidence cols | marker-only | oldest-first | role(user)-only | const-1 | rule |
|---|---|---:|---:|---:|---:|---:|---|---|---|---|---|
| smoke-00 | old | 1866 | 1763 | 41 | 26 | 36 | 2/2 (103 cols pinned) | 2/2 | 0/2 | 0/2 | 0/2 |
| smoke-01 | old | 2086 | 1950 | 35 | 40 | 61 | 3/3 (136) | 3/3 | 0/3 | 0/3 | 0/3 |
| smoke-02 | old | 2105 | 1972 | 38 | 28 | 67 | 3/3 (133) | 3/3 | 0/3 | 0/3 | 0/3 |
| smoke-03 | old | 1879 | 1766 | 51 | 28 | 34 | 2/2 (113) | 2/2 | 0/2 | 0/2 | 0/2 |
| smoke-04 | recent | 1783 | 1727 | 42 | 14 | 0 | n/a | n/a | n/a | n/a | n/a |
| smoke-05 | old | 2432 | 2226 | 43 | 87 | 76 | 3/3 (206) | 3/3 | 0/3 | 0/3 | 0/3 |
| smoke-06 | old | 1887 | 1766 | 60 | 27 | 34 | 2/2 (121) | 2/2 | 0/2 | 0/2 | 0/2 |
| smoke-07 | recent | 1970 | 1916 | 38 | 16 | 0 | n/a | n/a | n/a | n/a | n/a |

Also: a regex on the pool template gives the same result as pool membership; a "hex literal present" marker retains
1/2–2/3 (distractor literals share the cue, e.g. smoke-03 turn 2, smoke-06 turn 2); newest-first position (the rule)
retains 0/6, with 24 filler pieces + the turn-7 incidental piece pinned in every episode (matches README/validation).

Findings:

- **Marker alone recovers relevance on all six OLD smoke episodes.** Pool sentences are 94–95% of U; everything that
  is not a pool sentence (evidence, distractors, incidental bases) totals 103–206 columns < B = 256, so a scorer that
  merely says "not a pool sentence" retains every OLD dependency with budget to spare. On this bank the budget never
  forces discrimination *among authored content*; a clf win over rule here would be entirely explained by
  filler rejection versus user-first recency. This is exactly the population clause 5 registers ("may chiefly
  compare rejection of formulaic filler against user-first recency ... not a measured classifier advantage").
- **Oldest-first position alone also recovers 6/6**, because every smoke source authors its OLD dependency at turns
  0–2 and the incidental user turn at index 7 (README discloses both). This is a property of the eight
  informed-session fixtures, not of the law: the law only requires the dependency to end before R and forbids filler
  in the newest eligible old user turn; it does not fix where authors place evidence.
- **Role alone does not recover** (0/6): user-only eligibility admits the filler user turn first. The law does
  force governing events into user turns and only user/tool pieces into U, but distractors are user turns too.
- **Does the frozen law itself reveal authored relevance by marker, role or position?** No. Evidence and distractors
  share the grammar, literal streams (seeded hex/`N` identifiers appear in both), roles and the same 600-token cap;
  the new placement law removes the one mechanical shortcut astra named (formulaic text in the position the rule
  pins first) and adds no marker: the newest eligible old user turn is now authored prose, which may be evidence or
  incidental at the author's choice. Its only systematic effect is on power, not correctness: the rule always pins
  that turn first, so if production authors habitually make it the governing instruction, rule retains evidence and
  the arms converge (ceiling); `newest_eligible_old_user_turn` + `layout_audit.turns[].necessary_evidence` already
  record this per source, so it is auditable in Stage 3 and in analysis.
- **The disclosed filler pool is, by construction, a marker of irrelevance that dominates U in production as well**
  (history >= 4,608 with authored bases of a few hundred tokens implies ~85–95% pool columns). The amendment declines
  an exception for recognizable filler and instead registers the claim limit in clause 5. That is a coherent
  disposition: the relevance rule binds *authored* content (distractors vs. evidence), and the SC1 adoption decision
  is made against the registered claim, which already says what a win can mean. It cannot make SC1 decide wrongly
  relative to that claim; it bounds generality, which is disclosed.

Disposition: I explicitly accept compliance of the frozen source/expansion law with the contract's relevance rule
(marker/role/position) at the law level, on the measurements above; the eight smoke fixtures are cue-recoverable
(marker 6/6, oldest-first 6/6) and are correctly labelled disposable and disclosed; production compliance of
*authored* content remains the Stage 3 semantic-review obligation the amendment already assigns. Non-blocking
recommendation (post-hoc computable from frozen episodes with frozen functions, so it need not enter the freeze):
report per production source, and in `analysis.json`, whether a marker-only (pool-membership) selector and an
oldest-first selector retain every OLD dependency, exactly as computed above, so a clf-over-rule result can be
quantitatively attributed to filler rejection versus authored-content discrimination.

## (4) Snapshot and manifest

Snapshot == exact concatenation as defined (both recipes), hashes match registration-snapshot.json and the manifest,
`verify_manifest` and `verify_snapshot` pass, every manifest file hash matches the committed bytes at 318a90c, 45
files, 8 episode identities (see "What I ran").

## (5) Amendment leaves v2 science unchanged

ledger[:128466] at 318a90c is byte-identical to the entire 1612f69 ledger, so the DRAFT v2 section (endpoint, N,
factor distribution, policy algorithms, adoption gates) is untouched. The amendment text itself contains no endpoint,
N, McNemar/CP, gate or adoption statement; its only "expressly states otherwise" items are operational (cost
projection formula, abandoned-cost reporting, source-validation/transport laws, snapshot identity), none of which
alters what is tested or how adoption is decided.

## (6) Tests

141 passed (135 + 2 + 4), no failures, no skips, no deselection; sealed-guard tests included.

## Non-blocking notes

- N1. `produce_snapshot` reads the amendment from data/sc1/STAGE1-CLAUSES.md (`AMENDMENT` constant). Consumers use
  only `verify_snapshot` (sidecar + `git show`), so renaming the proposal file after the freeze breaks the producer
  only, never a gate or a test. Keep the file in place or note the path in WORKLOG when it moves.
- N2. Clause 1 carries both the "through EOF, two parts" sentence (fable) and the "three parts" law (astra) plus the
  reconciliation paragraph; verified identical bytes at this freeze. Fine as registered; after Stage 2 the sidecar
  ranges are the operative identity.
- N3. In `validate_trace`, non-`JSONDecodeError` `ValueError`s from `raw_decode` (e.g. Python's 4,300-digit int
  limit on a huge number inside incidental prose JSON) propagate as a source rejection with a non-SC1 message. It is a
  rejection, not an acceptance, so it cannot leak or mis-decide; an author would see an unhelpful error.
- N4. `verify_manifest` now shells out to `git show` for each snapshot part, so production consumers require the
  repo checkout at the recorded commits to be present (already true for `harness_commit`). Document in the run
  checklist.
- N5. The README's "V3 pressure and cue audit" is retained as historical and superseded; the round-4 table matches my
  recomputation (U, non-designated columns, rule composition, newest-old-user = 7) on all eight.

## Divergence from astra (results/sc1-stage2-review-astra.md, REJECT on H1/N1)

astra measures the same thing (marker and oldest-position recover the smoke evidence) and grades it HIGH because the
reconciled contract says "recognizable filler has no exception" while the law's closed prose pool is a known
irrelevance form. I grade it non-blocking under the burden test: (i) the filler-dominated population and its claim
limit are already registered text (clause 5), so an adoption decision made under it is not "wrong" relative to the
registered claim; (ii) the authored-content relevance rule is unaffected by the pool and is a Stage 3 review item
either way; (iii) the remedy astra implies (a filler law whose sentences can carry decisive facts, or a narrower
population amendment) changes the science population and therefore belongs to a prospective amendment with its own
review, not to a freeze gate; (iv) the attribution diagnostic above is post-hoc computable from frozen artifacts. If
the orchestrator wants the contract sentence and the pool law to agree literally, the text-only route is to add to
clause 5 a sentence that the disclosed pool is a shared, known-irrelevant form excluded from the authored-content
relevance rule, with the claim limit already stated; that is a wording reconciliation, not a code or artifact change.
Tie-break needed only on severity, not on facts.

## VERDICT: ACCEPT STAGE 2 FREEZE at 318a90c

No blocker: nothing found can make SC1 decide wrongly relative to its registered claim, leak private fields or
evicted history, or be unreproducible. R3/R7 residuals and V1–V3 are closed with tests that fail on the old
behaviour (measured); the dispositions are enacted verbatim; the snapshot is the exact defined concatenation and
every manifest hash verifies; v2 science is byte-unchanged; the cue review accepts the law (with the smoke bank's
marker/oldest-position recoverability disclosed and the Stage 3 diagnostic recommended). Acceptance of the freeze
does not authorize production authoring, model determinism or GPU execution.
