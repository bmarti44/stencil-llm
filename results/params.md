# Phase 2 parameter matching

Trainable parameters only; frozen buffers are excluded and embeddings are included.
Widths are the first multiples of 8 within 1% of the M1b count.

| variant | d_ff | trainable parameters |
|---|---:|---:|
| b0_full | 1024 | 3,183,104 |
| b0_local | 1024 | 3,183,104 |
| b1 | 1024 | 3,187,200 |
| b2 | 1008 | 3,185,296 |
| m1 | 1024 | 3,213,968 |
| m1b | 1024 | 3,214,096 |
