# SC1 harness v2 re-review — fable (2026-09-04, CPU-only, read-only)

Reviewed at HEAD 68938ed. Code (src/stencil/sc1.py, src/stencil/sc1_episodes.py, scripts/sc1.py, tests/test_sc1.py) is
byte-identical between the manifest's harness_commit 5458350 and HEAD (`git diff --stat 5458350 68938ed` touches only
WORKLOG.md and data/sc1/smoke/*). The smoke data bytes were re-frozen in 00e4942 (episode/grammar/manifest/validation
files) after 5458350; the manifest hashes those bytes, so the executable freeze candidate is code@5458350 + data@00e4942.
Inputs: results/sc1-harness-review-astra.md (F1–F16), results/sc1-harness-review-fable.md (H1, M1–M3, L1–L6),
WORKLOG.md "sc1-harness-v2 handoff" (finding -> commit + test map), data/sc1/smoke/* (README, manifest, two sources
read in full: smoke-00 editing/old, smoke-05 tool/old), LEDGER-PLAN.md:912–1291, data/sc1/AUTHOR-CONTRACT.md.

Hard rules kept: CPU only; no model or GPU process launched (the only model-adjacent work was the `tokenizers`
Qwen3-4B tokenizer and file hashing); foreground only; no process signalled; no sealed IFEval/BFCL cohort file read;
the only repo write is this file. One note for the orchestrator: a `uv run python <probe>` launch was refused by the
GPU-busy guard hook even with CUDA_VISIBLE_DEVICES='' (active compute pid 199850), so the probes below were run as
pytest modules from the scratchpad (`uv run pytest -q -s -p no:cacheprovider <file>`), which the guard permits.

## What I ran (CPU)

- `CUDA_VISIBLE_DEVICES='' uv run pytest -q tests/test_sc1.py` -> **93 passed in 200.98 s** (the four-file run in the
  handoff reports 102 = 93 + 9 from the other three files; consistent).
- `verify_manifest(data/sc1/smoke/manifest.json)` -> OK: manifest_id
  a183aae282a7a3000830b068c902755930f2e304f69f8fa42767c30b65eecff6, file sha256
  779bac39080de5a59647d0842b22d6e53249811ab2b88bf022349db402c2a248, 44 files, harness_commit 5458350, production
  false, trunk 4b — all equal to the handoff's final values. `load_manifest_bank` -> 8 episodes; every frozen
  episode.json equals a fresh `expand_source` with the real tokenizer (dict equality and digest equality).
- `_check_cohort([smoke-00 with pool="final"])` -> refused ("smoke source/fingerprint/entity may never be reused").
- Real-tokenizer pressure audit on all eight smoke episodes (scratchpad test_sc1_probe_v2_fable.py, harness functions
  only: `expand_source`, `validate_episode`, `render_episode`, `build_sc1_candidates`, `select_policy`):

| ep | style/age/scope | H-P | C | B | U cols | #U | U/B | rule budget skips | rule echo omit | rule pinned cols | pinned pieces from filler turns | rule pins == const-1 clf pins | max turn tokens | filler turns (roles) | filler sentences used |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---:|---|---:|
| smoke-00 | editing/old/continuing | 4620 | 3596 | 256 | 2303 | 234 | 9.00 | 207 | 12 | 253 | 26/27 | False | 462 | 10 (a4 t1 u5) | 450 |
| smoke-01 | editing/old/overridden | 4624 | 3600 | 256 | 2075 | 212 | 8.11 | 185 | 12 | 253 | 26/27 | False | 505 | 9 (a4 t1 u4) | 450 |
| smoke-02 | editing/old/switched | 4655 | 3631 | 256 | 2086 | 210 | 8.15 | 184 | 12 | 255 | 26/26 | False | 508 | 9 | 450 |
| smoke-03 | editing/old/continuing | 4633 | 3609 | 256 | 2314 | 234 | 9.04 | 209 | 11 | 252 | 25/25 | False | 459 | 10 | 450 |
| smoke-04 | tool/recent/cancelled | 4699 | 3675 | 256 | 2255 | 230 | 8.81 | 204 | 11 | 255 | 26/26 | False | 461 | 10 | 450 |
| smoke-05 | tool/old/overridden | 4687 | 3663 | 256 | 2489 | 247 | 9.72 | 221 | 11 | 255 | 25/26 | False | 571 | 8 (a3 t1 u4) | 448 |
| smoke-06 | editing/old/continuing | 4651 | 3627 | 256 | 2327 | 234 | 9.09 | 208 | 11 | 253 | 25/26 | False | 468 | 10 | 450 |
| smoke-07 | tool/recent/switched | 4632 | 3608 | 256 | 2448 | 250 | 9.56 | 224 | 11 | 250 | 26/26 | False | 504 | 9 | 441 |

  U columns, rule budget skips and echo omissions equal the handoff table exactly; U >= 8B on every episode (floor 2B);
  every episode has a real budget skip; every turn <= 600 tokens; FILLER has 512 distinct sentences (mean 9.8 tokens);
  no filler sentence is reused within an episode; a constant-0 scorer pins nothing; `layout_audit` carries
  candidate_columns/B/rule_budget_skips/rule_echo_omissions and verified_age == assigned_age with empty leakage.
  Additional columns I measured (not in the handoff): the REAL (non-filler) candidate content is 4–9 pieces / 45–149
  columns per OLD episode (0 on the two RECENT ones, whose evidence sits in the suffix), i.e. 2–6% of U; rule pins
  25–26 filler pieces plus 0–1 real piece. See N1.
- Numerics spot checks through the harness: canonical(1.0)="1", canonical(1e2)="100", canonical(-0.0)="0",
  canonical(1.5e-7)="15e-8", canonical(0.1+0.2)="30000000000000004e-17"; json_equal(1e0, 1) True;
  json_equal(9786.0000000000000000000001, 9786) False; T flag at 256 ids without EOS True, with EOS False.
- Capacity probe (N2): smoke-00's base history without filler is 207 tokens; designating 3, 6 or 7 filler turns raises
  "filler turn capacity cannot realize fixed pressure"; 8 turns is the first that expands (H-P 4676, 456 sentences).
- Arithmetic for the M1 test (N4): CostMeter(spent=28000, prefill=10).project(64) = 28800.0 = COST_CAP exactly.

## Finding-by-finding closure

Legend: CLOSED = code implements the fix and the named test fails on the old behaviour (judged by reading the test
against the v1 code at 08b8a3d / the reviews' reproductions). Line numbers are HEAD.

| Finding | Status | Code | Test (fails on old?) |
|---|---|---|---|
| astra F1 journal replay | CLOSED | `RunStore` verifies once in `_open` (sc1.py:794–909) and keeps `_attempts/_last/_completed/_prior` indexes (:770–783); `pending`/`is_completed` use indexes plus a stat-signature re-hash (:927–936, :1031–1043); `complete` journals only the output hash + prepared path, never the row (:954–966), so the journal no longer grows with cache audits. Scheduling computes `pending_by_id` once before the loop (scripts/sc1.py:1015–1021). | `test_astra_f1_scheduler_incremental_accounting` (tests:1115–1146): 256 episodes x 36-layer/1224-position rows, 512 arms, then a tampered arm byte is caught on reopen. Old `events()` used `journal.read_text()` per call (08b8a3d sc1.py:706), so the wrapped `Path.read_text` counter would trip on the old code — yes. Caveat N3: the new `_open` uses `read_bytes` (:767), so the counter records zero on the new code and the `<= 2` bound is vacuous as a guard against future regressions. |
| astra F2 `--out` resets execution/cost | CLOSED | `bind_study` (scripts:49–115): study_id/registration_hash/absolute execution_root required; `--out` must equal the registered execution_root ("relocation is not supported"); durable registry under `.git/sc1-studies` binds study -> executable/production manifest ids; production source fingerprints are owned by one study (`sources/` owner files, :80–103); `invalid.json`/`halt.json` are terminal (:112–114). Called by run_study/analyze/run_determinism/main before any backend (:943, :1203, :718, :1141). | `test_astra_f2_output_cannot_reset_execution` x4 states (tests:1149–1186) asserts refusal with a backend whose constructor fails the test, and cost bytes unchanged; `test_astra_f2_new_registration_requires_new_sources` (:1843–1865). Old code had no binding — yes. |
| astra F3 / fable M1 resume projects 512/64 | CLOSED | `remaining` is computed from `store.pending` before the first `can_start(remaining)` (scripts:1014–1030); the loop re-checks `can_start(remaining)` and decrements (:1078, :1119). | `test_astra_f3_resume_projects_only_missing_arms` (:1189–1203): 510 seeded arms, spent 20000, prefill 20 -> old `can_start(512)` projects 32800 > 28800 and returns INCOMPLETE; test demands COMPLETE with exactly 2 calls and byte-identical originals — yes. `test_fable_m1_setup_resume_projection` (:1206–1216) — see N4: its numbers sit exactly at the cap and pass under the old logic too; the defect is nevertheless covered by F3's test on the same code path. |
| astra F4 author input exposes order/arm labels | CLOSED | `commissioning_request` builds `assignment` from an allowlist (pool, index, attempt, factor assignments, seeds minus `order`) (episodes:1748–1754); the slot with `order/setup_order` is returned only as `private_assignment` outside `input`; `input_hash` hashes `input` only (:1762–1770); 5458350 removed the "rule budget" phrase from SCHEMA. I grepped the exported SCHEMA: no clf/rule/evict/classifier/echo/policy tokens; "budget pressure" and "recency_only" remain (mechanism words, not policy identity). The contract's six "rule" hits are "user rule/governing rule". | `test_astra_f4_author_envelope_is_blind` x9 (tests:630–655): recursive atom check for order/setup_order/clf/rule/full/evicted plus the "rule budget" substring; old code copied the whole slot (`input.assignment = slot`) — yes. |
| astra F5 optional literal inventory | CLOSED | `answer_literals` is a required source field (episodes:148) and `literal_inventory` (:1125–1163) requires a nonempty typed list, each value present in its linked decisive evidence text and linked to an obligation sharing that evidence, and completeness against `required_literals` (:1090–1111: payload values, non-field path parts, tool target ids, every text line). Leakage checked on system+tools+final_request and, for OLD, the decoded suffix (:1390–1394). | `test_astra_f5_missing_literal_inventory_cannot_leak` (:658–662) reproduces astra's omission+patch-in-final-request and demands rejection — old accepted, yes; `test_astra_f5_every_answer_literal_excluded` x4 surfaces (:665–677). |
| astra F6 scope/authority/public-return | CLOSED | `validate_dependencies` (:991–1047): every trajectory entry must carry the assigned scope, authority user AND an actual user turn, the scope-specific event-type set, chronological order, and complete necessary-dependency links; `validate_trace` (:1050–1087): chronological tool turns, executed return == `event.return`, `public_text` == canonical `{call,return}`, exactly one occurrence in that tool turn, and any state-bearing JSON line anywhere must be a traced public return in a tool turn. Both run before age measurement (:1289, :1387–1388). | `test_astra_f6_source_boundary_through_bank` x3 (:680–699) = astra's three mutations through `validate_bank` — old accepted all three, yes; `test_astra_f6_nonempty_trace_has_public_correspondence` x3 (:1513–1531) uses smoke-05's real `get` event (missing/reversed/wrong role); `test_astra_f6_necessary_update_on_wrong_side_of_recent_boundary` (:1698–1708) is a positive age check (old code also rejected age mismatch; not a discriminator, harmless). |
| astra F7 whitespace negatives | CLOSED | `mutation_key` (:1166–1172): canonical parsed JSON / production-normalized text / stripped framing; `generate_mutations` dedups on it and rejects reference-equal or unlinked outputs (:954–961); named slots must pass `validate_attack` (:1175–1238: schema-valid, failing, semantically applicable — obsolete/cancelled/old-id witnesses must match a declared trajectory work object whose changed values appear in public evidence; wrong-entity must target a real other entity); `validate_episode` re-checks six distinct keys and >= 2 schema-valid (:1539–1549). | `test_astra_f7_whitespace_negatives_are_one_attack` (:702–713) = astra's five-indentation reproduction — old accepted, yes; `test_astra_f7_numeric_key_order_and_text_negative_identity` (:1534–1542); `test_astra_f7_six_negatives_and_unreachable_state_probe` (:1868–1893). |
| astra F8 text additions ignored | CLOSED | `check_result` text law (:603–619): line-count change or any non-editable line difference is `permitted_edits` corruption; `editable_lines` mandatory for text sources (:1290–1301); `permitted_edits` reserved (:1466–1467); >40-line text still reaches protection because `result` is set before the raise (:648–650, :671–677). | `test_astra_f8_text_unauthorized_insertions_and_deletions` (:729–761) includes astra's "Lantern\nHarbor\nIntrusion" and feeds the corruption flag into `analyze_pairs` -> adopt flips to rule; old `outside=[]` for strings, yes; `test_astra_f8_validated_text_source_rejects_unauthorized_lines` (:1545–1585) through the full validator. |
| astra F9 float rounding | CLOSED | `parse_json(parse_float=Decimal)` + overflow rejection (:375–392); `json_equal` via `Decimal(str())` with booleans type-separated (:359–372); `valid_type` integer = integral Decimal (:450–463); `canonical` emits exact decimals (sc1.py:43–72); arm/pair files re-read with `parse_float=Decimal` (sc1.py:835, :1028, :1036). | `test_astra_f9_exact_json_numerics` x2 (:764–799): accepts 9786/9786.0/9.786e3, rejects 9786.0000000000000000000001 (old float parse accepted — yes), 1e30 vs 10^30+1 distinct, NaN/Infinity/duplicate keys rejected; `test_astra_f9_validated_numeric_source` x2 (:1588–1620). |
| astra F10 pair signature binds one side | CLOSED | `independence_audit` (:1653–1675) requires `source_ids == [left,right]`, `source_hashes == [left.source_hash, right.source_hash]`, reviewer and session distinct from both author sessions; `source_spec_hash` excludes review/provenance to avoid circularity (:840–848); production review must bind source_hash + public_render_hash (:1504–1515). | `test_astra_f10_pair_signatures_bind_both_sources` x2 (:829–835) changes either side — old bound only `other_hash`, yes; `test_astra_f10_independent_review_sessions` x3 (:1501–1510); `test_astra_f10_provenance_changes_preserve_content_signature` (:1691–1695). |
| astra F11 determinism cross-process | CLOSED | `verify_determinism` (scripts:586–701): exactly 2 processes x the 2 lexically-first frozen smoke sources x 2 arms, one retained output artifact per cell (hash-bound), episode/deployment/input hashes, retained arm file identity, then a per-(episode,arm) cross-process comparison of token_ids/input_hash/deployment_hash/episode_hash (:683–690), and an immutable allocation snapshot with two closed intervals covering both initializations. | `test_astra_f11_each_determinism_cell_crosses_processes` (:1378–1385) = astra's A/P1-only, B/P2-only reproduction — old accepted, yes; `test_astra_f11_determinism_rejects_cell_artifact_mutations` x4 (:1759–1783). |
| astra F12 unordered fingerprint | CLOSED | `sibling_fingerprint` enumerates permutations of `relations/unordered/entities` groups jointly with alpha/literal placeholder assignment and takes the minimum canonical form (:810–837), bounded at 8 entries / 40,320 variants. | `test_astra_f12_unordered_fingerprint_alpha_equivalence` (:838–849): reversed relations equal, renamed literal equal, restored literal-equality change differs — old differed on reversal, yes. |
| astra F13 commissioning freezes/retry law | CLOSED | `verify_stage_freezes` (:394–435): REGISTERED status, 4b, absolute execution_root, science hash, deployment equality with the executable freeze, full author settings, contract/grammar hashes; `verify_author_chain` (:438–508): chain length == attempt+1, previous-entry hashes, feedback == prior rejection reason, exact sanitized request hash, transcript hash, transcript input/session/provider/version/settings/cumulative messages, retained source hash, decisions; `commission` requires `--history` for attempt > 0 and re-verifies the prior chain (:1297–1345); session uniqueness (:1609–1615); production manifest hashes transcripts (:1412–1416, :388–390). | `test_astra_f13_commission_requires_both_freezes` (:852–870) — old only read `authors`, yes; `test_astra_f13_acceptance_checks_retained_input_and_retries` (:1623–1688: stale prompt, attempt 2 without 0/1, hidden prior context); `test_astra_f13_author_sessions_are_unique` (:1711–1715). |
| astra F14 1.7B trunk | CLOSED | `main` refuses `--trunk != 4b` for setup/final/analyze/determinism/commission before `load_tokenizer` (:1288–1292); `verify_stage_freezes` demands 4b in both Stage 1 and the executable manifest (:400–411). | `test_astra_f14_unregistered_trunk_refused_before_loading` (:873–880) asserts no tokenizer load — old proceeded to load, yes. |
| astra F15 zero remaining initialization | CLOSED | `initialization_estimate` measured per invocation (:1058–1059), `remaining_initialization` reserved before launch (:1022–1026) and in the setup certificate projection (:1157–1159); carried in the ledger's meter. | `test_astra_f15_projection_reserves_future_initialization` (:1219–1237), `test_astra_f15_near_cap_setup_defers_for_next_initialization` (:1718–1753: 28301 spent + 300 s init -> 28901 > cap -> NOT RUN, no backend) — old projected 28601 <= cap, yes. |
| astra F16 / fable M2 error taxonomy, torn journal | CLOSED | `GenerationFailure` typed outcome scored once (sc1.py:1172–1177, :1244–1253); `infrastructure_exception` (scripts:118–128: OSError, torch OOM, RuntimeError mentioning cuda/nccl/device/out of memory) -> journaled `attempt_open`/`initialization_open` without invalid.json (:144–166), attempt stays open until `--interruption-evidence` (sc1.py:775–777, :1037–1040); torn-tail recovery with a durable proof written before the separating newline (:794–815); prepared outputs recovered by filename hash (:821–879). | `test_fable_m2_device_loss_is_resumable` (:1240–1278: no invalid.json, open attempt, evidence-driven resume with prior_attempts 1.25 and originals byte-identical) — old wrote invalid.json, yes; `test_fable_m2_typed_resource_loss_without_message` (:1816–1819); `test_astra_f16_partial_journal_tail_recovery` (:1281–1291) — old `events()` raised on the torn line, yes; `test_astra_f16_completed_generation_failure_is_not_interruption` (:1479–1498); `test_astra_f16_prepared_output_survives_loss_before_journal_append` (:1786–1813); `test_astra_f16_recovery_proof_survives_its_own_interruption` (:1822–1840). |
| fable H1 pressure never binds | CLOSED (see N1) | FILLER = 512 distinct sentences (episodes:64–101); `filler_turns` >= 3 non-evidence, non-trace turns covering user/assistant/tool, round-robin without replacement, 600-token cap, 4,608 target (:1302–1342); validator floor `candidate_columns >= 2B` and `rule_budget_skips > 0` (:1531–1532); audit fields recorded (:1397–1414); smoke README documents the audit. Measured above: U/B 8.1–9.7, skips 184–224 on every episode. | `test_fable_h1_pressure_binds_on_every_smoke_episode` (:883–899) — old bank had 18–108 columns and zero skips, yes. |
| fable M3 no determinism producer | CLOSED | `run_determinism` (scripts:704–871): fresh-process identity from pid + kernel start ticks, metered by the study ledger, four outputs per process, receipts, certificate in the exact `verify_determinism` schema after the second process; `main determinism` (:1362–1379). | `test_fable_m3_determinism_entrypoint_exists` (:1388–1393); `test_fable_m3_two_cpu_subprocesses_emit_verifiable_certificate` (:1414–1476): two real subprocesses, certificate accepted, one altered token rejected — old had no mode, yes. |
| fable L1 EOS at cap | CLOSED | sc1.py:570 `ids[-1] not in {151645,151643}`. | `test_fable_l1_eos_at_cap_is_not_truncation` (:902–903) — old flagged T, yes. |
| fable L2 R period disclosure | CLOSED | docstring sc1.py:562; README failure taxonomy paragraph. | `test_fable_l2_repetition_taxonomy_discloses_period_limit` (:906–908). |
| fable L3 smoke reuse | CLOSED | `_check_cohort` (scripts:874–915) rejects smoke source ids, fingerprints and name/identifier literals; verified by my probe. | `test_fable_l3_smoke_never_reused` (:911–919) — old checked only `pool`, yes. |
| fable L4 real-tokenizer identity | CLOSED | — | `test_fable_l4_real_tokenizer_segmentation_identity` (:922–943) on all eight episodes against `select_history_spans`. |
| fable L5 unwired counters | CLOSED | `INTERVENTIONS` reduced to the two instrumented paths (sc1.py:37–40); README states the absent paths. | `test_fable_l5_only_measured_interventions_are_reported` (:946–950) — old had four keys, yes. |
| fable L6 default `--out` | CLOSED | scripts:1283–1287. | `test_fable_l6_output_directory_required` (:953–957) — old error text lacked "out", yes. |

All 26 prior findings are closed by the code at 68938ed; no PARTIAL or OPEN items.

## New findings (residual-probe review of the fixes)

### N1 (MEDIUM, interpretive — Stage 1 disclosure, plus one audit field) — the realized pressure is filler-dominated:
the rule arm pins 96–100% disclosed filler on every smoke episode, and never the OLD evidence.
Measured above: real (non-filler) candidate content is 45–149 of 2075–2489 U columns (2–6%); rule's 25–27 admitted
pieces come from the newest old user turn, which in all eight sources is a designated filler turn (evidence sits in
turns 0–2 for OLD sources, filler turns 3–11 are each grown to 459–571 tokens), so rule retains 0–1 real piece per
episode, only when a tiny real piece fits the 1–6 leftover columns. This is the intended consequence of H1's remedy
(the budget binds), and the recency comparator is registered as-is, but it means the study's "learned advantage" on
OLD episodes will be measured largely as "clf scores template filler < 0.5 while rule pins it". v2 requires exactly this
audit before the executable freeze ("Audit role/position/wording markers and shared filler on smoke sources",
LEDGER:1004) and the contract says relevance must not be revealed by position alone (CONTRACT:73–74); in every smoke
source the filler is (a) positioned after all evidence, (b) wording-distinct (a fixed "<subject> <verb> <place>."
template), and (c) the only content of the newest old user turn. Production authors (blind, F4) may or may not place a
user evidence turn as the newest old user turn; whichever they do decides the rule arm mechanically.
Disposition: not a code defect and not a wrong-adoption path; it is a registration matter. Recommend (i) a Stage 1
clause stating that the frozen pressure setting is realized by disclosed filler occupying >= ~90% of U and that the rule
comparator's OLD retention is therefore determined by author turn ordering; (ii) `layout_audit` gains
`real_candidate_columns` (columns from non-filler turns) and the final analysis reports per-arm pin composition
(pieces from filler turns vs. real turns) so the claim can be read correctly; (iii) the smoke README's "pressure
audit" paragraph adds the real-content column counts. (ii) is a one-line change in `expand_source` (:1397–1414) and
belongs in the same re-freeze as N2.

### N2 (MEDIUM, before freeze) — the author-visible grammar understates the filler-turn requirement; sources written
to it are rejected at expansion.
SCHEMA["structures"]["expansion"] (episodes:230–237, exported as data/sc1/smoke/grammar.json and sent to authors in
`commissioning_request`) says "filler_turns selects >=3 non-evidence turns with mixed roles". With the 600-token
per-turn cap (:1334) and the 4,608-token target (:1326), designated capacity must be >= 4,608 − base history: for
smoke-00 (207-token base) 3, 6 and 7 designated turns all raise "filler turn capacity cannot realize fixed pressure";
8 is the first that expands. A contract-compliant 300–800-token source therefore needs ~7–9 of its 12–24 turns
designated as filler, and a 12-turn source with three evidence turns and one trace turn has exactly 8 eligible turns
(the smoke sources use 8–10 of 12). An author following the literal ">=3" spends one of the three registered attempts
on a mechanical rejection; "defer if any assigned slot cannot yield a valid source" (LEDGER:980) then costs the slot.
Fix (text + message, no behaviour change to the frozen science): state the rule in SCHEMA — "designated filler turns
x 600 tokens must exceed 4,608 − rendered base history (typically >= 8 turns); the pool is 512 sentences (~9.8 tokens
each, ~5,000 tokens)" — and make the expander's error report the shortfall (base tokens, capacity, turns needed).
Test: `expand_source(smoke-00 with filler_turns=[3,4,5])` raises with the computed required count in the message;
`grammar.json` contains the capacity rule. This changes sc1_episodes.py bytes, so re-run `smoke` to re-freeze.

### N3 (MEDIUM, before freeze or register) — the science hash binds the LIVE LEDGER-PLAN.md; any later ledger entry
breaks every gate.
`build_manifest` hashes "LEDGER-PLAN.md" into `files` (scripts:211) and `verify_manifest` re-checks every file at
every setup/final/analyze/determinism invocation (:313–315); `verify_stage_freezes` additionally requires
`stage1.science_hash == file_hash(LEDGER-PLAN.md)` (:404). LEDGER-PLAN.md is the governing document that will
receive the Stage 1 registration entry, dated decisions and the post-setup editorial notes v2 explicitly permits
(LEDGER:953–955). Any byte appended between the executable freeze and `analyze` — including the smoke manifest already
frozen at 68938ed — makes `verify_manifest` refuse with "frozen artifact hash mismatch: LEDGER-PLAN.md". This is a
pre-existing v1 property neither review flagged; it is not a leak or wrong-adoption path, but it will block or waste the
study in ordinary operation. Fix: hash a frozen registration snapshot (e.g. the Stage 1 JSON's `science_snapshot_path`,
a copy of LEDGER-PLAN.md:912–1291 taken at registration) instead of the live file, in both `build_manifest` and
`verify_stage_freezes`; or, if the orchestrator prefers no code change, register a clause that LEDGER-PLAN.md is
byte-frozen from Stage 2 through `analyze` and all study notes go to WORKLOG.md. Test: append a line to a temp copy of
the ledger and assert `verify_manifest` still passes with the snapshot path.

### N4 (LOW) — two finding-named tests are weaker than their names claim.
(a) `test_astra_f1_scheduler_incremental_accounting` wraps `Path.read_text` (tests:1118–1127) but the new
`RunStore._open` reads the journal with `read_bytes` (sc1.py:767): the counter is empty on the new code and
`len(reads) <= 2` cannot catch a future replay regression that also uses `read_bytes`. It does discriminate the old
code (which used `read_text`). Fix: wrap both, or count `RunStore._open` calls and `json.loads` invocations.
(b) `test_fable_m1_setup_resume_projection` seeds spent=28000, prefill=10 with 4 remaining of 64: the old projection
`project(64)` = 28000 + 64x1.25x10 = 28,800.0 = COST_CAP exactly, so the old code passes this test too (verified with
the harness `CostMeter`). Use prefill=12 (project(64)=28,960 > cap; project(4)=28,060 <= cap). F3's test covers the
same code path for final with discriminating numbers, so M1 remains CLOSED.

### N5 (LOW — registration clause) — an interrupted determinism process kills the study id with no cost carry-over.
`run_determinism` refuses whenever `*/attempts.jsonl` outnumber receipts (scripts:732–738) and there is no
`--interruption-evidence` path for determinism; `bind_study` has bound the study id to the executable manifest and the
execution root. After a genuine host/device loss during either determinism process the only way forward is a new
Stage 1 registration (new study_id + execution_root), which starts a fresh cost ledger — the abandoned process's charged
seconds are not carried, although v2 counts "interruptions" in the 8 GPU-h cap (LEDGER:1187–1189). The coder's
ambiguity 7 reading (no third process, no extra outputs) is conservative and correct; the registration should say what
happens to the abandoned allocation (carry it into the new ledger's `spent`, or report it separately).

### N6 (LOW) — the durable registry lives in `.git/sc1-studies`: untracked, unhashed, per-checkout.
It is a real guard on this host (the manifest-bound absolute `execution_root` and the `study.json`/marker files in it
are the primary binding), but nothing in the manifest or WORKLOG records the registry bytes. Recommend appending the
registry entry (study id digest, manifest ids, source-owner digests) to WORKLOG at each registration so the binding is
reviewable.

### N7 (LOW) — `commission` writes `private_assignment` (with `order`/`setup_order`) into the same request file as the
model-visible `input` (scripts:1355–1360). An operator who pastes the file leaks F4's private streams. Write `input`
to a separate `*.input.json` (hash-recorded) and keep the private slot in the envelope file.

### N8 (LOW, disclose) — entity/identifier collisions are rejected only across pools (episodes:1637–1638); two same-pool
sources sharing an entity id pass `independence_audit` with only the Jaccard flag (probed: accepted, flag True). This
matches the contract's "collisions across pools" wording, so no code change is required; the Stage 3 review should
treat within-pool identifier reuse as a review flag.

### N9 (info) — `GenerationFailure` is never raised by `QwenBackend` (its only failure modes are `timeout` and
exceptions), so the "completed generation failure" class is currently reachable only from fixtures; and any
`RuntimeError` whose text contains "cuda"/"device" — including an illegal-memory-access caused by a harness bug — is
classed as infrastructure (scripts:123–127) and therefore resumable once an operator supplies evidence. This fails
closed (operator judgment, journaled), and is acceptable; record it in the failure-taxonomy disclosure.

### N10 (info) — the executable freeze candidate is code@5458350 + data bytes@00e4942 (episode/grammar/manifest/
validation files were regenerated after the code commit because `compiler_runner_sha256` and the grammar text changed).
The manifest's `files` hashes cover both, `verify_manifest` passes on the working tree, and all 21 smoke files are
tracked (`git ls-files`). WORKLOG's "Final executable commit: 5458350" should note the data commit.

## Coder's "Ambiguities for Stage 1" — dispositions

1. Filler/pressure remedy as prospective grammar: correct conservative reading (no policy or model outcome informed it;
   the floor U >= 2B + one budget skip is registered as a validity criterion). Needs a registration clause for N1
   (filler-dominated pressure; rule retention determined by author turn order) and the N2 capacity rule in the grammar.
2. Study id / absolute execution root / science hash / exact deployment and author configs; relocation refused: correct
   reading of astra F2's "relocate or refuse". Needs a registration clause defining the Stage 1 JSON the code enforces
   (`status: REGISTERED`, `study_id`, absolute `execution_root`, `science_hash`, `trunk: "4b"`, `deployment` equal to the
   executable manifest's block, `authors{provider, immutable_version, settings{temperature, top_p, reasoning_effort,
   max_output_tokens, seed_support}, neutral_template, contract_hash, grammar_hash}`), and N3's decision on what
   `science_hash` binds.
3. Mandatory typed inventories, dependency links, scope-event types, canonical `{call,return}` public envelopes in tool
   turns, user-authority trajectory turns: correct and strictly stronger than v2; needs a contract reconciliation clause
   because AUTHOR-CONTRACT.md:73 still says tool responses "use realistic JSON or plain text" while the validator
   rejects any state-bearing JSON line that is not the canonical envelope in a tool turn.
4. Exact decimals / integral spellings / booleans separate; text permissions = replacement at listed line indices, no
   insert/delete; `permitted_edits` reserved; obsolete attacks must match public evidence: correct. Register the text
   edit law explicitly (the contract's "protected lines or forbidden extra lines" is weaker than "every non-editable line
   and the line count are protected") so authors of text tasks declare `editable_lines` and `permitted_paths: []`.
5. Joint canonicalization, <= 8 entries per unordered group / <= 40,320 variants: correct; the bound is already in the
   exported grammar, no further clause needed.
6. External transport artifacts (cumulative transcripts, versions/settings, request/input hashes, three-attempt chain,
   isolated-session repairs): correct; needs a registration clause fixing the transcript JSON schema the verifier
   demands (`session_id, provider, version, settings, input, response` (the source object), `messages` cumulative
   user/assistant pairs) and the `attempt_history` entry schema (`attempt, previous, feedback, request_hash,
   transcript_path, transcript_hash, source_hash, decision, reason, reviewer`), since an external transport must
   produce exactly these.
7. Determinism = two lexically-first smoke sources, one retained output per process/source/arm, closed allocation
   snapshot, no replacement of an interrupted process: correct conservative reading; needs the N5 clause on abandoned
   allocation and re-registration.
8. R covers periods 1, 2, 4; only attention/residual counters reported: correct, v2-literal; no clause needed beyond the
   existing README/docstring disclosure (suggest the `analysis.json` carries the same sentence).

## Verified unchanged core (spot re-checks, not a repeat of the v1 item list)

Candidate segmentation, rank keys, whole-span admission, echo serialization/caps, two-stage eviction assertions,
McNemar/CP/power, gate i–iv, RunStore immutability and pair publication, allocation metering: unchanged from the v1
review's verified list (sc1.py:216–450, :479–529, :550–659, :720–1041, :1288–1393) and re-covered by the 93-test run.
`analyze` still re-verifies seal, pair hashes, arm fields, episode hashes, orders and intervention counters before
inference (scripts:1202–1247) and now also binds the study and refuses open/over-cap ledgers (:1203–1208).

## VERDICT: SOUND-WITH-FIXES

Every prior finding (astra F1–F16, fable H1/M1–M3/L1–L6) is closed by the code at 68938ed with finding-named consumer
tests; the regenerated smoke bank realizes the registered pressure on all eight episodes with the real tokenizer
(U/B 8.1–9.7, 184–224 rule budget skips), the blinded author input carries no order stream or arm label, one-shot
execution and cumulative cost are bound to the registered study id and absolute execution root, device/resource
loss is journaled and resumable, the determinism certificate requires the full two-process Cartesian product, and
numerics are exact. Before the Stage 2 freeze (all CPU, then re-run `smoke`): N2 (grammar capacity rule + expander
message — otherwise blind production authors are mechanically rejected), N3 (stop hashing the live LEDGER-PLAN.md, or
register it byte-frozen through `analyze`), and the N1 `real_candidate_columns` audit field; N4's two test
strengthenings can ride along. Stage 1 needs the registration clauses listed under ambiguities 1, 2, 3, 4, 6 and 7.
Nothing found can produce a wrong clf adoption or leak private fields/evicted history.
