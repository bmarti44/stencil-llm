# Disposable SC1 round-5 cue repair

Candidate status: Amendment 2 is proposed in `../STAGE1-CLAUSES.md`; the orchestrator must adopt it, regenerate the snapshot/manifest and obtain independent review before Stage 2 acceptance. The current snapshot contains adopted DRAFT v2 + Amendment 1 + the revised contract, with committed byte-range provenance. The proposed law is not falsely presented as already adopted.

These eight fictional sources are informed harness fixtures, never isolated production authoring or reusable setup/final sources. The sampled author names are factor draws, not claims about who wrote the fixtures. Source identities have a round5 suffix. Work, task specifications, reference outputs, seeds and factor assignments match the reviewed bank. Data lineage: fit-on = none; evaluated-on = disposable SC1 smoke and CPU fixtures only. No benchmark prompts/responses, model/scorer execution or policy-outcome tuning supplied this repair.

Each source now supplies its entire `incidental_sentences` array. Expansion orders only those authored sentences with the existing filler seed and uses the source's ordered `filler_turns` layout. There is no executable prose generator or shared padding bank. Authored incidental named-card and preserved-record templates match necessary templates; the same fictional task domains occur in necessary and incidental contexts across these disposable sources. Bases preserve source-authored causal order; necessary and incidental pieces may share a turn. The historical 512-item recognizer is retained solely for regression and the newest-user guard. Exhausted source text or capacity fails; the compiler cannot invent more text.

All turns remain capped at 600 text tokens; history acceptance is 4096–8192 tokens, expansion targets at least 4608 after a complete round-robin batch, and every episode has U >= 2B and a budget skip. The newest eligible old user is never expansion-designated and contains no historical pool sentence. Its base is necessary in smoke-01 and smoke-03 and incidental in the other six sources. OLD decisive-fact positions are 1, 4, 3, 7, 1 and 1, preserving causal ordering and all original age draws.

## Cue contingency audit

Method: `cue_candidate_rows` renders public messages with the real local Qwen3-4B tokenizer, rebuilds necessary-evidence offsets from unique authored quotes, and calls the common unscored `build_sc1_candidates`. Positive means token overlap with necessary decisive-fact/trajectory evidence; negative means outside those intervals, not necessarily semantically useless. Initial-state prose and the canonical smoke-05 trace are outside that label. Public form uses fixed, unfitted regular expressions for these disposable fixtures; labels never enter policy selection. Exact pool membership is the original unfitted recognizer. All tables count eligible old candidate pieces, including pieces from RECENT sources.

The regression reads all eight actual historical episodes using `git show 318a90c26e5f5fcf241ad23e3007eb61da1b0273`, re-tokenizes them and rebuilds evidence spans; saved historical candidate coordinates are not trusted. `../cue-regression-318a90c.json` retains the complete recomputed before tables. `validation.json` contains the complete after tables, including every joint form/role/position cell.

| Public stratum | Before positive | Before negative | After positive | After negative |
| --- | ---: | ---: | ---: | ---: |
| All old candidates | 25 | 1590 | 16 | 579 |
| Historical pool form | 0 | 1539 | 0 | 0 |
| Index 1, all sources | 6 | 0 | 3 | 49 |
| Index 1, OLD sources | 6 | 0 | 3 | 49 |
| Newest old user, all sources | 0 | 8 | 2 | 7 |
| Newest old user, OLD sources | 0 | 6 | 2 | 5 |

The historical bank fails all three registered counterexamples: pool membership marks 1,539 negatives with no positives; index 1 has six positives and no negatives; newest-old-user has eight negatives and no positives. The new bank passes the mixed-label assertions. This is a smoke regression, never a production balancing quota, factor-resampling rule or policy-retention filter.

| Public form (after) | Positive | Negative |
| --- | ---: | ---: |
| code | 6 | 179 |
| edit | 6 | 155 |
| other | 0 | 8 |
| previous | 2 | 80 |
| return | 1 | 79 |
| switch | 1 | 78 |

| Role | Before positive | Before negative | After positive | After negative |
| --- | ---: | ---: | ---: | ---: |
| tool | 2 | 1182 | 2 | 367 |
| user | 23 | 408 | 14 | 212 |

| Message index | Before positive | Before negative | After positive | After negative |
| --- | ---: | ---: | ---: | ---: |
| 0 | 12 | 101 | 7 | 43 |
| 1 | 6 | 0 | 3 | 49 |
| 2 | 7 | 236 | 1 | 114 |
| 3 | 0 | 158 | 1 | 35 |
| 4 | 0 | 391 | 1 | 116 |
| 5 | 0 | 1 | 0 | 1 |
| 6 | 0 | 391 | 1 | 114 |
| 7 | 0 | 8 | 2 | 7 |
| 9 | 0 | 296 | 0 | 98 |
| 11 | 0 | 8 | 0 | 2 |

Every joint form/role/position cell with positives also has negatives. Those cells are shown below; zero-positive cells are retained in the full JSON report.

| Public form | Role | Index | Positive | Negative |
| --- | --- | ---: | ---: | ---: |
| code | tool | 1 | 1 | 5 |
| code | tool | 3 | 1 | 1 |
| code | user | 1 | 2 | 12 |
| code | user | 4 | 1 | 1 |
| code | user | 7 | 1 | 5 |
| edit | user | 0 | 4 | 9 |
| edit | user | 2 | 1 | 19 |
| edit | user | 7 | 1 | 1 |
| previous | user | 0 | 2 | 7 |
| return | user | 6 | 1 | 4 |
| switch | user | 0 | 1 | 5 |

`test_round5_matched_contexts_through_bank` supplies two disposable causal contexts with byte-identical code observations at user positions 1 and 7. The same full edit instructions also switch relevance at user position 0. Each observation/instruction is necessary in one context and incidental in the other. Both pass references and all six negatives, including type-valid semantic negatives. `test_round5_incidental_expansion_can_share_evidence_turn` also checks that appended source text and necessary evidence share turn 1, and reconstructs every appended byte from the submitted source array. Missing, empty, duplicate, exhausted and historical-pool content are rejected through the bank consumer.

## Regenerated geometry

| Episode | Age | Fact index | History | U columns | B | Budget skips | Max turn | Newest old user |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| smoke-00 | OLD | 1 | 4869 | 2067 | 256 | 61 | 524 | 7 |
| smoke-01 | OLD | 4 | 4648 | 2375 | 256 | 71 | 482 | 7 |
| smoke-02 | OLD | 3 | 4775 | 2237 | 256 | 68 | 524 | 7 |
| smoke-03 | OLD | 7 | 4645 | 2168 | 256 | 65 | 434 | 7 |
| smoke-04 | RECENT | 11 | 4883 | 1997 | 256 | 58 | 493 | 7 |
| smoke-05 | OLD | 1 | 4702 | 2461 | 256 | 77 | 584 | 7 |
| smoke-06 | OLD | 1 | 4875 | 1938 | 256 | 60 | 511 | 7 |
| smoke-07 | RECENT | 11 | 4777 | 2017 | 256 | 60 | 535 | 7 |

All eight references pass and all 48 generated negatives fail. Designation in `rule_pin_composition` means membership in expansion-designated turns; it is not a semantic relevance label. Existing policy/pressure diagnostics remain in validation.json and do not govern source selection.

## Reproduction and limits

After committing source/code/contract changes, run on CPU:

```sh
CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 uv run python scripts/sc1.py snapshot
CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 uv run python scripts/sc1.py smoke
CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 uv run python scripts/sc1.py validate data/sc1/smoke
```

The snapshot producer automatically includes every adopted `SC1 AMENDMENT N` section, even across unrelated editorial sections, and records immutable commit/range hashes. It does not consume the proposal file. A consumer regression invokes the actual CLI in a temporary Git repository with Amendments 1–3, verifies later editorial appends are excluded, and rejects a self-consistent record that omits an adopted amendment. The pre-repair contract is preserved byte-for-byte in `../AUTHOR-CONTRACT-v3.md`.

`smoke` loads only the local tokenizer and hashes checkpoint/classifier files; no model or trained scorer is instantiated. Manifest SHA-256, manifest ID, snapshot hashes, commit IDs and exact test results are recorded in WORKLOG.md. The two sealed-guard hash tests require separate clarification of the user's no-read rule; they are not silently mocked or counted as passed.

This bank establishes the recorded regressions, not production-wide semantic cue compliance, source independence, model determinism or provider isolation. Independent source-law review remains binding. Earlier rejection and measurements remain in the historical commit, the review file, WORKLOG and the before-audit JSON. Endpoint N=256, policies, exact test and all gates are unchanged.
