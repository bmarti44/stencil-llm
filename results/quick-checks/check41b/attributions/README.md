# Attribution arrays

`00.npz` through `31.npz` correspond, in order, to `banks.json`'s 32 fit tasks.
Each array is float32 with shape (36 layers, 9728 intermediate neurons). The
trunk forward and backward use bfloat16; values are promoted to float32 before
multiplication, differencing and saving. Layer indices are zero based.

- `x`: uncued SiLU(gate) * up, immediately before down_proj, at the final prompt position.
- `gradient`: dc/dx for that position, using autograd with frozen model parameters.
- `attribution`: x * gradient, computed before averaging across tasks.
- `JavaScript_x`, `Python_x`: the same position with the corresponding textual cue.
- `JavaScript_difference`, `Python_difference`: cued activation minus uncued x.

`aggregate.npz` contains `attribution`, the signed mean of the 32 per-task
attributions; `uncued_mean`, `JavaScript_mean`, `Python_mean`; and
`JavaScript_difference`, `Python_difference`, each cued mean minus uncued mean.
Means accumulate in float64 and are saved as float32. Top-k selection uses the
absolute value of the signed mean attribution, with its sign retained. The
clamp uses the stored mean for the selected coordinates and target language.

`../decision-records.jsonl` maps task IDs to these files and records contrast,
top-1 predictions, actual uncued first tokens, and cued/uncued prompt token IDs.
`../neuron-sets.json` records all selected indices, signs, per-layer counts,
matched random controls and check41 frequency-set intersections. The consumer
is `scripts/focus_check41b.py`; `../audit-source.py.txt` independently recomputes
arrays, selection, grid choice, parser scores and intervention positions.
