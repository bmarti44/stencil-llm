**SC1 Stage 2 acceptance review — astra — 2026-09-04**

Reviewed `318a90c26e5f5fcf241ad23e3007eb61da1b0273`. **Reject this Stage 2 freeze.** Residual R3 and R7, and fable V1–V3, are closed. Amendment enactment, snapshot identity, manifest verification and the required tests pass. One HIGH blocker remains: **fable H1/N1 — cue compliance**. The new placement guard closes its specified local shortcut, but the frozen irrelevant-only filler law and revised smoke positions still permit relevance shortcuts expressly prohibited by the reconciled contract. This requires source-law/artifact repair, not a text-only correction.

Scope: trusted but fallible authors/operators; only defects that could change SC1's decision, leak, or defeat reproduction block. Inputs were the two v3 reviews, the round-4 WORKLOG handoff, appended Amendment 1, both v2/reconciled contracts, the snapshot/provenance, smoke artifacts and their consumers. Active `plan/` paths are absent; process context came from `archive/plan/PROTOCOL.md` and the archived STATE at `archive/plan/LEDGER.md:13`. The explicit review-only write restriction governs instead of ledger updates. Prior reviewer files were not changed.

**Execution and identity evidence.**

- Required command, with bytecode and pytest-cache writes disabled:
  `CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run pytest -q tests/test_sc1.py tests/test_eval_data_separation.py tests/test_sealed_guard.py`
  — **141 passed, 1 warning in 368.68 seconds**. No deselections or mocked sealed checks. The warning is the existing invalid escape in `scripts/b2_gsm8k.py:9`.
- Actual `verify_manifest`, `load_manifest_bank`, `verify_snapshot` and real-tokenizer `validate_bank` passed. Eight references pass; all 48 required negatives fail. Recomputed expanded episodes and the entire validation report equal the frozen artifacts, and exported grammar equals `SCHEMA`.
- Additional inline CPU probes restored only the relevant `eff241b` functions in memory, extracting their ASTs from `git show`, and called the new permanent tests directly with temporary banks. **All eight counterfactual cases detect the restored defect**: four duplicate-JSON cases, two positional-text cases, and two placement cases. No repository implementation was modified and no whole old-version suite was claimed.
- All commands were foreground, with no background launches or process signals. No model/scorer weights were instantiated, fitted or run. Manifest verification hashed checkpoint/classifier bytes; tokenizer loading used local `tokenizers.Tokenizer.from_file` only. Sealed IFEval reads occurred solely inside the authorized `tests/test_sealed_guard.py` checks. I did not read that input myself or read sealed BFCL cohort contents. Probe banks were temporary; the only authored repository file is this report. Bytecode/cache suppression does not suppress the requested tests.

`318a90c` differs from artifact commit `75dec30` only in WORKLOG. All executable/test bytes match manifest `harness_commit` `c7f9b387c2acdf11325f638d43fd08890c81321c`. The 27 files under `data/sc1` are tracked.

| Artifact | Independently verified identity |
| --- | --- |
| Manifest ID | `a3966c05d50c878bb3cda64e817fc8e6476a8b767ee21738fa04baa94bc7d04c` |
| Manifest file SHA-256 | `2c7aa51d086ac9eb9200a32a102bb3d2f92ac4822d22c8a2c4516f3126d699d0` |
| Frozen file hashes | 45, all verified by the real consumer |
| Snapshot SHA-256 | `c610e67f4f7fd25f3a7263bcb9b6644cbbdc2881ddec1323f8a58221acb7e653` |
| Snapshot byte length | 83,953 |
| Recomputed bank hash | `940ecc74c499119a6c17750115e517f409470c7554f83acb77967950a41b57a2` |

**Finding closure.** References below are at `318a90c`; test names are in `tests/test_sc1.py`.

| Finding | Disposition and discriminating evidence |
| --- | --- |
| **astra R3 / F6 — HIGH: duplicate-member public JSON** | **CLOSED (resolved).** `validate_trace`, `src/stencil/sc1_episodes.py:1112`, uses `object_pairs_hook=public_pairs`; duplicate names raise before member loss. Only `JSONDecodeError` is swallowed as incidental syntax, so duplicate rejection propagates. `test_astra_r3_duplicate_public_members_through_bank` (`:2043`) covers duplicate wrapper, nested wrapper, pretty array and non-state duplicate through the actual bank, retaining an incidental non-state positive. Restoring the exact old `validate_trace` makes all four tests fail with `DID NOT RAISE ValueError`. Existing multiline tests also pass. |
| **astra R7 / F7 — MEDIUM residual: positional text identity** | **CLOSED (resolved).** `validate_attack`, episodes `:1261`, compares normalized text lines at ordered indices. `test_astra_r7_ordered_text_witness_through_bank` (`:2561`) accepts both swapped and reused line values, then rejects missing linked public evidence. Restoring the exact old function rejects both valid positive sources with `inapplicable semantic attack: wrong scope`. Raw scope/entity and original-permissions cases remain green. |
| **fable V1 / N3 — MEDIUM: live-ledger test coupling** | **CLOSED (resolved).** `test_fable_n3_snapshot_manifest_survives_live_ledger_append` (`:2271`) checks the three recorded byte ranges, appends a later top-level ledger section in a temporary repository, and passes snapshot production, manifest and Stage 1 consumers. Changed snapshot bytes and missing Stage 1 ranges are rejected. Its identity assertion no longer consumes the future ledger tail. |
| **fable V2 — LOW: missing snapshot producer/stale science** | **CLOSED (resolved).** `produce_snapshot`/`verify_snapshot`, `scripts/sc1.py:267/318`, implement committed byte-range production and verification. Actual `main(["snapshot"])` is exercised by the N3 consumer test with a tokenizer trap. The frozen snapshot now contains Amendment 1. I reconstructed it independently from the recorded Git commits; I did not invoke the writing producer in this checkout. |
| **fable V3 / N5 — LOW: proposal-dependent registered test** | **CLOSED (resolved).** `test_fable_n5_abandoned_determinism_disposition` (`:2410`) reads the adopted snapshot. N3 also reconstructs its temporary amendment from frozen parts. N10's append-only historical WORKLOG check remains. |
| **New mandatory placement law** | **CLOSED as an implementation requirement.** `validate_filler_placement`, episodes `:1782`, uses the common unscored candidates, including qualifying straddling turns. It rejects designation or any pool sentence anywhere in the newest eligible old user turn. Expansion calls it at `:1545`; bank validation recomputes expansion. `test_amendment_filler_newest_old_user_through_bank` (`:2634`) covers later filler promoted to user and pool text inserted into an undesignated base. Removing only this guard makes both tests fail with `DID NOT RAISE ValueError`. All eight positive layouts pass. |
| **fable H1/N1 — HIGH residual: induced population/cue compliance** | **OPEN — blocker below.** Reporting and the local placement repair are complete; neither establishes the broader binding relevance rule. This continues the unresolved v3 population disposition, rather than opening a new review scope. |

Other previously closed R1, R2, R4, R5, R6, R8 mechanics; F8/F11/F16; M2; and N2–N4/N6–N10 remain closed within their earlier stated scope. Their consumer regressions passed. This review does not convert fixture-based evidence into proof of actual model determinism or provider isolation.

**Orchestrator dispositions are enacted verbatim.**

All nine quoted paragraphs in astra's A–H replacements, including both B paragraphs, occur verbatim in the adopted amendment. Fable's complete clause-1 replacement, registry receipt sentence, and clause 3/6/11 precisions also occur verbatim. `STAGE1-CLAUSES.md` equals the exact adopted ledger amendment bytes.

Decision (a) is binding at `LEDGER-PLAN.md:1304`, with no recognizable-filler exception. The reconciled contract retains the relevance prohibition at `:73` and explicitly extends it to recognizable filler at `:215`. The newest-user law is defined at ledger `:1404` and enforced as above. Independent review is required by `:1433`; this report supplies that review and does **not** accept compliance.

Decision (b) is enacted at ledger `:1538`: abandoned-study cost is reported separately; eight GPU-hours are cumulative **within each registered study**, including determinism, initialization, interruptions and resumptions. Predecessor IDs, allocation hashes, loss evidence, abandoned seconds and cumulative program effort must be recorded before any newly registered restart, with a new root and new sources. This is an adopted operational obligation; the documentary N5 test is not evidence that a real restart disclosure occurred. The per-study meter remains `COST_CAP = 8 * 3600`, and existing cost/refusal/source-reuse tests pass.

Decisions (c)/(d) are reconciled in the snapshot and sanitized contract/grammar. The contract diff preserves the v2 contract at `AUTHOR-CONTRACT-v2.md`, replaces the broad state-return allowance with the adopted boundary, clarifies that expansion verifies authored age, and adds the numerical, source, transport and text-witness requirements. No relevance waiver was slipped into the author-facing material.

**Exact snapshot construction.**

All three source commits are `022c0347c46f0ac59a5bbffb000627193c908e9a`. Half-open ranges and hashes were recomputed from `git show` bytes, compared with current source ranges and concatenated without separators:

| Ordered part | Source/range | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| DRAFT v2 | `LEDGER-PLAN.md [91091,128466)` | 37,375 | `3365b4f983f5c0f60431075d46477112d84bc5a6beebf0b45177f621c6b78f38` |
| Amendment 1 | `LEDGER-PLAN.md [128466,152203)` | 23,737 | `c6d4a8e118d90a67bcbee5d74ac1f06509f0c3824e95958a9c1e7e43aa42a04a` |
| Reconciled contract | `data/sc1/AUTHOR-CONTRACT.md [0,22841)` | 22,841 | `2f0b81cf1800f0e0168940630909dc797ea91ec4b7a4970a650e938878ede6d3` |

At this commit the amendment is the final ledger section. Thus the three-part recipe also equals fable's initial through-EOF recipe: **61,112 ledger bytes + 22,841 contract bytes**. Later editorial entries do not extend the recorded ranges. The sidecar is manifest-bound provenance, not snapshot content. Snapshot, provenance, contract and grammar hashes match the executable manifest.

**Independent cue review — fails the binding source law.**

Method: load the real 4B tokenizer, re-expand and validate all eight sources, then call `render_episode`, `build_sc1_candidates`, `select_policy(..., "rule")`, and `pin_composition`. A necessary-evidence candidate is one whose token interval overlaps the registered necessary decisive-fact or trajectory intervals. This is an audit label, never an input to selection. Public trace state at smoke-05 turn 5 is reported separately; a candidate outside those intervals is described as *non-evidence*, not automatically as semantically useless. Formulaic pool statements are incidental by source reading and construction.

The cue recognizer is the fixed, unfitted expression `candidate["text"].strip() in FILLER`. Position and role summaries use only public message index/role. No diagnostic classifier was fitted, no trained scorer was called, and no generated policy outcome informed this audit.

| Episode | Age | History | U columns | Non-designated U | Exact-pool columns | Columns after pool removal | Rule filler/all pieces | Rule evidence columns |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| smoke-00 | OLD | 4649 | 1866 | 62 | 1763 | 103 | 24/25 | 0 |
| smoke-01 | OLD | 4656 | 2086 | 101 | 1950 | 136 | 24/26 | 4 |
| smoke-02 | OLD | 4686 | 2105 | 95 | 1972 | 133 | 24/25 | 0 |
| smoke-03 | OLD | 4664 | 1879 | 62 | 1766 | 113 | 24/25 | 0 |
| smoke-04 | RECENT | 4629 | 1783 | 14 | 1727 | 56 | 24/25 | 0 |
| smoke-05 | OLD | 4627 | 2432 | 163 | 2226 | 206 | 24/25 | 0 |
| smoke-06 | OLD | 4681 | 1887 | 61 | 1766 | 121 | 24/26 | 3 |
| smoke-07 | RECENT | 4659 | 1970 | 16 | 1916 | 54 | 25/26 | 0 |

B=256 throughout. Budget skips are respectively 164,187,186,164,156,217,163,175; echo omissions are 11 throughout. Maximum turn lengths are 462,505,508,459,452,560,468,504. Every newest eligible old user is non-designated turn 7 with no pool sentence. These numbers reproduce the current README/validation report.

**Marker/form alone gives a consequential shortcut.** Of 1,615 old candidate pieces, 1,539 are exact pool sentences: **95.29% of pieces and 15,086/16,008 = 94.24% of columns**. None overlaps necessary evidence. All 25 necessary-evidence pieces survive the fixed marker exclusion. Among the remaining 76 pieces, 51 are outside the necessary intervals, so marker absence does not perfectly identify relevance. Nevertheless the remaining **54–206 columns per episode all fit B**, including all 15 necessary OLD dependencies across the six OLD sources.

I verified that last implication through the harness's own unchanged admission function: filter only exact pool sentences, then call `admit_whole_spans(rank_rule(remaining), evict_range, B)`. Every remaining piece is admitted and every complete necessary dependency on all six OLD episodes is pinned. The registered unfiltered rule retains **zero complete necessary OLD dependencies**, only seven overlapping evidence columns in total, while 193/203 admitted pieces are from filler-designated turns. This is a source-geometry counterfactual, not a proposed extra production arm or a measured classifier advantage. It demonstrates why the cue is material to the comparison.

**Position alone also reveals useful evidence on this smoke bank.** Candidate turn 1 has exactly six pieces across the eight episodes. All six are the full decisive fact, one in each OLD source; the two RECENT sources contribute no turn-1 candidates. Thus a public index alone recovers every OLD decisive fact without a false positive in that stratum or in the observed common candidate bank. All 25 necessary-evidence pieces occur in turns 0–2. The fixed predicate `message_index <= 2` retains all 25 plus 337 non-evidence pieces and excludes 1,253 non-evidence pieces. Turn 7 is always an incidental user piece, eight for eight. The trace at smoke-05 turn 5 is an additional public-state piece; RECENT dependencies are at turns 10–11 and 9–11. These positions are disclosed smoke properties, not a claim about uncommissioned production sources.

**Role alone does not recover the complete relevance labeling.** User candidates contain 23 evidence/408 non-evidence pieces; tool candidates contain 2 evidence/1,182 non-evidence pieces. Both roles have positives and negatives. User-only labeling has recall 23/25 but precision 23/431. Mixed roles therefore close neither the form shortcut nor the fixed-position shortcut. No class-imbalanced raw accuracy is used as evidence: always calling a piece non-evidence would already score 98.45% here.

**Why this remains HIGH / exact required repair and regression.** `src/stencil/sc1_episodes.py:68` defines a closed subject×verb×place prose pool expressly incapable of supplying a decisive fact; `expand_source:1444–1499` appends it only to non-evidence/non-trace turns. The new guard changes which user turn is newest, while preserving that public-form/irrelevance association. The reconciled contract explicitly says recognizable filler has no exception. A study on this bank can favor rejecting a known prose form while being presented as satisfying a no-cue relevance law. Hash integrity and a correct McNemar implementation cannot fix that population mismatch. This is the single continuing H1/N1 blocker; the marker and position measurements are two manifestations of it.

Required repair **under the current no-exception ruling**:

1. Reconcile the expansion law prospectively so its public filler forms cannot serve as an irrelevance label. Use source-authored necessary and incidental content with overlapping public forms; do not reserve a recognizable sentence/template family exclusively for irrelevant padding. The expander must not invent decisive facts. Replace the uniform smoke ordering with lawful source-specific layouts: index 1 must not identify every OLD decisive fact, and the newest eligible old user must not be uniformly incidental. Preserve factor assignments, causal text/event order, age, turn caps, the new no-formulaic-newest-user guard, and endpoint/N/policy/gates. Revise the conflicting fixed-pool clause before re-freezing if the repair requires it; do not waive relevance through a README disclaimer.
2. Add a **bank-consumer cue regression** alongside the existing pressure/placement tests. Include matched disposable sources where the same public sentence/template form is necessary in one context and incidental in another, with the same role and eligible position; require both references and semantic-negative suites to validate. Include OLD smoke layouts with both evidence and incidental eligible pieces at index 1, and both necessary and incidental newest eligible old users, without pool text there. Recompute the public-form/role/position contingency tables from the real tokenizer/common candidate builder. The present bank must fail the smoke cue-compliance assertions: its pool-form group has 1,539 negatives/zero positives, index 1 has six positives/zero negatives, and newest-old-user has eight negatives/zero positives. Apply these regression examples to disposable smoke, not as factor-balancing quotas or policy-retention filters on production sources.
3. Independently review the repaired source/expansion law and regenerated eight-source evidence, then regenerate the snapshot, provenance, grammar, episodes and manifest and rerun the requested suite. Keep this report's cue counterexamples in the review history. Passing matched fixtures alone is not proof of production-wide semantic compliance; source review remains binding.

A different ruling that explicitly narrows the scientific population would require a further prospective Stage 1 amendment and independent disposition under text C. **No such exception is adopted at `318a90c`; this review does not supply one.**

**Unchanged v2 decision and non-blocking limits.**

The 37,375-byte v2 section is exactly the `eff241b` section, and `AUTHOR-CONTRACT-v2.md` is exactly the pre-change contract. `src/stencil/sc1.py` is byte-unchanged; AST comparison also finds `run_study`, `analyze` and `verify_determinism` unchanged. The endpoint remains complete executable success on N=256 pairs; one-sided exact McNemar p<=.05; adoption requires b−c>=13, paired excess flags U<=2, paired excess corruption K=0, and mean clf latency<=1.25×rule. Setup remains full>=24/32 and full−evicted>=8/32. Neither the amendment nor the repaired validators changes those numbers or the 75:25 age draw. Their targeted arithmetic/gate tests pass.

Non-blocking: the existing SyntaxWarning; historical README sections clearly marked superseded; host-local advisory locking; JSON-syntax-only automatic trace scanning with non-JSON state prose assigned to semantic review; and the absence of real model determinism, GPU timing, production authors/version registration and provider-isolation evidence in this CPU artifact review. Those future prerequisites do not justify executing models or commissioning sources here. Abandoned-cost prose is now enacted but has not been demonstrated on a real restart. No additional blocking parser, leakage, numerical-test or artifact-identity defect was found in the requested delta.

VERDICT: REJECT
