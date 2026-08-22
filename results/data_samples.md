# Phase 1 decoded data samples

`-> ANSWER` marks an input position whose logits predict the next token.

## Task A — cued rule application (N=8 miniature)

### Sample 1

`cue[0] | distractor[3] | distractor[1] | distractor[1] | distractor[4] | distractor[5] | distractor[2] | distractor[10] | distractor[0] | QRY | symbol[1] -> ANSWER | symbol[0]`

Metadata: `{'cue_index': 0, 'operand_index': 1, 'distractor_draws': [3, 1, 1, 4, 5, 2, 10, 0], 'answer_index': 0}`

### Sample 2

`cue[0] | distractor[5] | distractor[13] | distractor[7] | distractor[7] | distractor[13] | distractor[1] | distractor[0] | distractor[2] | QRY | symbol[5] -> ANSWER | symbol[6]`

Metadata: `{'cue_index': 0, 'operand_index': 5, 'distractor_draws': [5, 13, 7, 7, 13, 1, 0, 2], 'answer_index': 6}`

### Sample 3

`cue[1] | distractor[6] | distractor[12] | distractor[4] | distractor[9] | distractor[10] | distractor[7] | distractor[12] | distractor[3] | QRY | symbol[14] -> ANSWER | symbol[4]`

Metadata: `{'cue_index': 1, 'operand_index': 14, 'distractor_draws': [6, 12, 4, 9, 10, 7, 12, 3], 'answer_index': 4}`

## Task B — switching (R=3 miniature)

### Sample 1

`cue[4] | distractor[3] | distractor[1] | distractor[1] | distractor[4] | distractor[5] | distractor[2] | distractor[10] | distractor[0] | QRY | symbol[1] -> ANSWER | symbol[4] | cue[3] | distractor[5] | distractor[13] | distractor[7] | distractor[7] | QRY | symbol[5] -> ANSWER | symbol[8] | cue[7] | distractor[13] | distractor[1] | distractor[0] | distractor[2] | distractor[6] | distractor[12] | distractor[4] | QRY | symbol[14] -> ANSWER | symbol[2]`

Metadata: `{'cue_indices': [4, 3, 7], 'active_rule_indices': [4, 3, 7], 'operand_indices': [1, 5, 14], 'delay_lengths': [8, 4, 7], 'distractor_draws': [[3, 1, 1, 4, 5, 2, 10, 0], [5, 13, 7, 7], [13, 1, 0, 2, 6, 12, 4]]}`

### Sample 2

`cue[1] | distractor[9] | distractor[10] | distractor[7] | distractor[12] | distractor[3] | QRY | symbol[11] -> ANSWER | symbol[8] | cue[6] | distractor[4] | distractor[7] | distractor[3] | distractor[11] | distractor[0] | distractor[10] | distractor[0] | QRY | symbol[8] -> ANSWER | symbol[10] | cue[5] | distractor[2] | distractor[5] | distractor[9] | distractor[5] | distractor[7] | distractor[3] | distractor[0] | distractor[7] | QRY | symbol[5] -> ANSWER | symbol[7]`

Metadata: `{'cue_indices': [1, 6, 5], 'active_rule_indices': [1, 6, 5], 'operand_indices': [11, 8, 5], 'delay_lengths': [5, 7, 8], 'distractor_draws': [[9, 10, 7, 12, 3], [4, 7, 3, 11, 0, 10, 0], [2, 5, 9, 5, 7, 3, 0, 7]]}`

### Sample 3

`cue[5] | distractor[9] | distractor[5] | distractor[1] | distractor[11] | distractor[4] | distractor[10] | QRY | symbol[13] -> ANSWER | symbol[9] | cue[3] | distractor[12] | distractor[12] | distractor[2] | distractor[5] | distractor[9] | QRY | symbol[5] -> ANSWER | symbol[8] | cue[5] | distractor[6] | distractor[3] | distractor[13] | distractor[7] | QRY | symbol[5] -> ANSWER | symbol[7]`

Metadata: `{'cue_indices': [5, 3, 5], 'active_rule_indices': [5, 3, 5], 'operand_indices': [13, 5, 5], 'delay_lengths': [6, 5, 4], 'distractor_draws': [[9, 5, 1, 11, 4, 10], [12, 12, 2, 5, 9], [6, 3, 13, 7]]}`

## Task M — in-window (P=4, queries=2 miniature)

### Sample 1

`key[20] | symbol[7] | key[7] | symbol[13] | key[13] | symbol[10] | key[2] | symbol[12] | QRY | key[13] -> ANSWER | symbol[10] | key[7] -> ANSWER | symbol[13]`

Metadata: `{'key_indices': [20, 7, 13, 2], 'value_indices': [7, 13, 10, 12], 'query_pair_positions': [2, 1]}`

### Sample 2

`key[7] | symbol[9] | key[3] | symbol[14] | key[29] | symbol[11] | key[12] | symbol[2] | QRY | key[12] -> ANSWER | symbol[2] | key[7] -> ANSWER | symbol[9]`

Metadata: `{'key_indices': [7, 3, 29, 12], 'value_indices': [9, 14, 11, 2], 'query_pair_positions': [3, 0]}`

### Sample 3

`key[30] | symbol[13] | key[17] | symbol[13] | key[11] | symbol[12] | key[4] | symbol[13] | QRY | key[30] -> ANSWER | symbol[13] | key[4] -> ANSWER | symbol[13]`

Metadata: `{'key_indices': [30, 17, 11, 4], 'value_indices': [13, 13, 12, 13], 'query_pair_positions': [0, 3]}`

## Task M — beyond-window (P=4, queries=2 miniature)

### Sample 1

`key[20] | symbol[7] | key[7] | symbol[13] | key[13] | symbol[10] | key[2] | symbol[12] | distractor[3] | distractor[1] | distractor[1] | distractor[4] | distractor[5] | distractor[2] | distractor[10] | distractor[0] | distractor[5] | distractor[13] | distractor[7] | distractor[7] | distractor[13] | distractor[1] | distractor[0] | distractor[2] | distractor[6] | distractor[12] | distractor[4] | distractor[9] | distractor[10] | distractor[7] | distractor[12] | distractor[3] | distractor[4] | distractor[7] | distractor[3] | distractor[11] | distractor[0] | distractor[10] | distractor[0] | distractor[2] | distractor[5] | distractor[9] | distractor[5] | distractor[7] | distractor[3] | distractor[0] | distractor[7] | distractor[9] | distractor[5] | distractor[1] | distractor[11] | distractor[4] | distractor[10] | distractor[12] | distractor[12] | distractor[2] | distractor[5] | distractor[9] | distractor[6] | distractor[3] | distractor[13] | distractor[7] | distractor[2] | distractor[8] | distractor[9] | distractor[4] | distractor[0] | distractor[8] | distractor[12] | distractor[6] | distractor[1] | distractor[0] | distractor[1] | distractor[0] | distractor[9] | distractor[3] | distractor[5] | distractor[1] | distractor[4] | distractor[9] | distractor[13] | distractor[1] | distractor[0] | distractor[3] | distractor[6] | distractor[4] | distractor[11] | distractor[2] | distractor[0] | distractor[12] | distractor[9] | distractor[6] | distractor[10] | distractor[8] | distractor[0] | distractor[0] | distractor[3] | distractor[8] | distractor[10] | distractor[10] | distractor[8] | distractor[7] | QRY | key[13] -> ANSWER | symbol[10] | key[7] -> ANSWER | symbol[13]`

Metadata: `{'key_indices': [20, 7, 13, 2], 'value_indices': [7, 13, 10, 12], 'query_pair_positions': [2, 1], 'gap_length': 94, 'gap_draws': [3, 1, 1, 4, 5, 2, 10, 0, 5, 13, 7, 7, 13, 1, 0, 2, 6, 12, 4, 9, 10, 7, 12, 3, 4, 7, 3, 11, 0, 10, 0, 2, 5, 9, 5, 7, 3, 0, 7, 9, 5, 1, 11, 4, 10, 12, 12, 2, 5, 9, 6, 3, 13, 7, 2, 8, 9, 4, 0, 8, 12, 6, 1, 0, 1, 0, 9, 3, 5, 1, 4, 9, 13, 1, 0, 3, 6, 4, 11, 2, 0, 12, 9, 6, 10, 8, 0, 0, 3, 8, 10, 10, 8, 7]}`

### Sample 2

`key[7] | symbol[9] | key[3] | symbol[14] | key[29] | symbol[11] | key[12] | symbol[2] | distractor[7] | distractor[11] | distractor[4] | distractor[10] | distractor[2] | distractor[13] | distractor[4] | distractor[8] | distractor[7] | distractor[6] | distractor[4] | distractor[10] | distractor[7] | distractor[0] | distractor[11] | distractor[13] | distractor[6] | distractor[0] | distractor[7] | distractor[5] | distractor[2] | distractor[13] | distractor[11] | distractor[9] | distractor[12] | distractor[9] | distractor[5] | distractor[0] | distractor[7] | distractor[7] | distractor[0] | distractor[11] | distractor[0] | distractor[13] | distractor[9] | distractor[7] | distractor[2] | distractor[1] | distractor[7] | distractor[9] | distractor[5] | distractor[2] | distractor[13] | distractor[8] | distractor[10] | distractor[8] | distractor[5] | distractor[9] | distractor[7] | distractor[11] | distractor[13] | distractor[13] | distractor[4] | distractor[13] | distractor[0] | distractor[1] | distractor[0] | distractor[6] | distractor[0] | distractor[5] | distractor[11] | distractor[7] | distractor[4] | distractor[4] | distractor[9] | distractor[0] | distractor[12] | distractor[13] | distractor[10] | distractor[10] | distractor[6] | distractor[7] | distractor[2] | distractor[1] | distractor[7] | distractor[6] | distractor[3] | distractor[9] | distractor[10] | distractor[9] | distractor[10] | distractor[3] | distractor[8] | distractor[12] | distractor[7] | distractor[10] | distractor[0] | distractor[4] | distractor[0] | distractor[13] | distractor[4] | distractor[4] | distractor[11] | distractor[1] | QRY | key[12] -> ANSWER | symbol[2] | key[7] -> ANSWER | symbol[9]`

Metadata: `{'key_indices': [7, 3, 29, 12], 'value_indices': [9, 14, 11, 2], 'query_pair_positions': [3, 0], 'gap_length': 94, 'gap_draws': [7, 11, 4, 10, 2, 13, 4, 8, 7, 6, 4, 10, 7, 0, 11, 13, 6, 0, 7, 5, 2, 13, 11, 9, 12, 9, 5, 0, 7, 7, 0, 11, 0, 13, 9, 7, 2, 1, 7, 9, 5, 2, 13, 8, 10, 8, 5, 9, 7, 11, 13, 13, 4, 13, 0, 1, 0, 6, 0, 5, 11, 7, 4, 4, 9, 0, 12, 13, 10, 10, 6, 7, 2, 1, 7, 6, 3, 9, 10, 9, 10, 3, 8, 12, 7, 10, 0, 4, 0, 13, 4, 4, 11, 1]}`

### Sample 3

`key[30] | symbol[13] | key[17] | symbol[13] | key[11] | symbol[12] | key[4] | symbol[13] | distractor[8] | distractor[2] | distractor[1] | distractor[4] | distractor[8] | distractor[11] | distractor[1] | distractor[9] | distractor[8] | distractor[4] | distractor[6] | distractor[8] | distractor[0] | distractor[1] | distractor[2] | distractor[12] | distractor[2] | distractor[11] | distractor[12] | distractor[1] | distractor[8] | distractor[8] | distractor[6] | distractor[4] | distractor[1] | distractor[3] | distractor[0] | distractor[5] | distractor[5] | distractor[9] | distractor[13] | distractor[8] | distractor[9] | distractor[6] | distractor[11] | distractor[9] | distractor[1] | distractor[1] | distractor[2] | distractor[1] | distractor[5] | distractor[8] | distractor[4] | distractor[13] | distractor[12] | distractor[13] | distractor[10] | distractor[13] | distractor[9] | distractor[9] | distractor[2] | distractor[11] | distractor[1] | distractor[6] | distractor[4] | distractor[0] | distractor[8] | distractor[6] | distractor[13] | distractor[6] | distractor[12] | distractor[9] | distractor[13] | distractor[2] | distractor[12] | distractor[13] | distractor[9] | distractor[10] | distractor[4] | distractor[3] | distractor[1] | distractor[4] | distractor[9] | distractor[11] | distractor[8] | distractor[12] | distractor[11] | distractor[13] | distractor[0] | distractor[12] | distractor[2] | distractor[3] | distractor[11] | distractor[0] | distractor[5] | distractor[6] | distractor[11] | distractor[10] | distractor[13] | distractor[4] | distractor[4] | distractor[1] | distractor[2] | distractor[10] | QRY | key[30] -> ANSWER | symbol[13] | key[4] -> ANSWER | symbol[13]`

Metadata: `{'key_indices': [30, 17, 11, 4], 'value_indices': [13, 13, 12, 13], 'query_pair_positions': [0, 3], 'gap_length': 94, 'gap_draws': [8, 2, 1, 4, 8, 11, 1, 9, 8, 4, 6, 8, 0, 1, 2, 12, 2, 11, 12, 1, 8, 8, 6, 4, 1, 3, 0, 5, 5, 9, 13, 8, 9, 6, 11, 9, 1, 1, 2, 1, 5, 8, 4, 13, 12, 13, 10, 13, 9, 9, 2, 11, 1, 6, 4, 0, 8, 6, 13, 6, 12, 9, 13, 2, 12, 13, 9, 10, 4, 3, 1, 4, 9, 11, 8, 12, 11, 13, 0, 12, 2, 3, 11, 0, 5, 6, 11, 10, 13, 4, 4, 1, 2, 10]}`
