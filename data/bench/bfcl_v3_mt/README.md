# BFCL V3 multi-turn pin

This directory vendors the four BFCL V3 multi-turn categories from Gorilla
tag `v1.3`, commit `ea13468e4423454d0c213704fb87cf7cb3990433`
(Apache-2.0):

- `berkeley-function-call-leaderboard/bfcl_eval/data/BFCL_v3_multi_turn_*.json`
- `berkeley-function-call-leaderboard/bfcl_eval/data/possible_answer/BFCL_v3_multi_turn_*.json`
- `berkeley-function-call-leaderboard/bfcl_eval/data/multi_turn_func_doc/*.json`

The executable checker subset is copied under `vendor/bfcl_eval/` from
`berkeley-function-call-leaderboard/bfcl_eval/eval_checker/multi_turn_eval/`,
including all `func_source_code` environments used by these categories. The
upstream root `LICENSE` is copied beside it. Python trailing whitespace is
normalized so repository diff checks remain clean; executable logic is unchanged.

`cohorts.json` is generated with seed 20260902 after sorting source IDs, then
shuffling each category independently. It contains 8 dev and 16 sealed IDs per
category. Its `sha256` field hashes canonical JSON of the seed and two ID lists;
the file hash is separately pinned in `data/bench/pins-manifest.json`.

`finder_labels.json` deterministically samples 100 spans without replacement
from the dev cohort's tool schemas and system/user instruction sentences. The
candidate order is cohort order, then schema order, then message/sentence
order; sentence boundaries use `stencil.ledger.segment_char_spans`.
