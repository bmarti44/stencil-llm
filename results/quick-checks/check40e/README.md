# Check40e — router transfer to TypeScript and SQL

Unregistered synthetic SET screen, 2026-09-05; pre-outcome recipe commit `6d28b09c`.

## OFF default distributions (reported first)

- **P1:** raw identities {'Python': 32}; unbroken semantic outputs {'Python': 32}; broken 0/32.
- **P2:** raw identities {'JSON': 32}; unbroken semantic outputs {'JSON': 25, 'broken': 7}; broken 7/32.

## Fixed reading and outcome

**No demonstrated transfer in this check.** P1 does not flip at alpha3. The non-language pair was **not tested for flipping** because SQL failed cued competence; it is INELIGIBLE, not a negative SQL-routing result.

**P1, Python → TypeScript: NOT.**
Correct addressed success 0/32, breakage 0/32; shuffled addressed success 0/32. Paired OFF-Python to correct-TypeScript flips: **0/32**.

Cued competence (16 each): {'Python': 16, 'TypeScript': 16}.

| Arm | Raw identities | Unbroken semantic outputs | Target success | Broken | Truncated |
|---|---|---|---:|---:|---:|
| OFF | {'Python': 32} | {'Python': 32} | 0/32 | 0/32 | 0 |
| correct | {'Python': 32} | {'Python': 32} | 0/32 | 0/32 | 0 |
| shuffled | {'Python': 32} | {'Python': 32} | 0/32 | 0/32 | 0 |
| swapped | {'Python': 32} | {'Python': 32} | 0/32 | 0/32 | 0 |
| text-cue | {'TypeScript': 32} | {'TypeScript': 32} | 32/32 | 0/32 | 0 |

Top-8 overlap: mean **75.5208%**, range 37.5–100%; all-layer >90% exclusion = False. [All layer expert IDs and overlaps](P1-profile-statistics.json).

Broken records by arm/identity: {}.


**P2, JSON → SQL: INELIGIBLE.**

Cued competence (16 each): {'JSON': 15, 'SQL': 0}. All 16 SQL replies are exactly `SELECT * FROM table WHERE value <operator> <threshold>;`, using the intended filter but the wrong identifier `table` instead of the supplied `items` (for example, `SELECT * FROM table WHERE value > 33;`). The restricted checker rejects them; `table` is also an unquoted SQLite keyword. This is a table-naming/instruction-following failure in this fixture, not evidence that the model cannot write SQL. The frozen >=14/16 gate therefore excludes P2 profiles and intervention arms. No query, cue or table-name repair was applied.

| Arm | Raw identities | Unbroken semantic outputs | Target success | Broken | Truncated |
|---|---|---|---:|---:|---:|
| OFF | {'JSON': 32} | {'JSON': 25, 'broken': 7} | 0/32 | 7/32 | 0 |
| correct | not run | not run | — | — | — |
| shuffled | not run | not run | — | — | — |
| swapped | not run | not run | — | — | — |
| text-cue | not run | not run | — | — | — |

Broken records by arm/identity: {'OFF:JSON': 7}.

Example P2_screen_04/OFF (>97): returned values 98 and 97; only 98 qualifies.
Example P2_screen_10/OFF (>=54): returned only value 54, omitting qualifying value 93.
Example P2_screen_12/OFF (>50): returned values 50 and 86; only 86 qualifies.

## Design and limits

Go and gofmt were absent, so P1 uses the authorized TypeScript fallback. The TS checker requires a real type annotation, parses TS, transpiles to JS, parses JS and executes an arithmetic-only function. Python uses its AST and an arithmetic interpreter. Both require the requested function name and correct numeric result. Untyped JavaScript is recorded but is outside the paired checker.

P2 checks JSON row objects against a Python reference, or parses restricted SELECT/WHERE and executes against the in-prompt table with SQLite. Wrong rows, malformed/out-of-pair output, bad fences and truncation count as breakage. P2 uncued asks for matching rows as a list without naming JSON; its system prompt is format-neutral because the inherited function-specific system is inappropriate for this task. SQL cue explicitly replaces the row-list answer.

GENERALIZES requires target semantic success ≥20/32, correct breakage ≤2/32, shuffled target success ≤4/32; otherwise MARGINAL at ≥12/32, else NOT. Competence requires ≥14/16 per side. The reading was fixed before outcomes; no prompt, dose, cap, checker or outcome-driven changes were made. The prewritten 16-task resource fallback was not needed; all scheduled screens/baselines retain 32 tasks.

Same Qwen3-30B-A3B bf16/check40b-c loader, raw-router hook and generated-token profile extraction; alpha 3 sustained through prefill/decode, all 48 layers, fresh KV and greedy 64-token caps. Mean raw logits pool all actual competence replies, weighted by generated non-EOS tokens, without success filtering. The tested correct bias points toward TypeScript; swapped is opposite; shuffled preserves per-layer norms with seed40052. Generation/task seed40050. There is no dose/setup search in this check.

Fit/train: none. Competence uses 16 paired synthetic tasks per pair. Only P1 qualifies for profile extraction (all 32 cued replies). P1 evaluation uses 32 separate tasks; P2 receives only the 32-task OFF baseline. Numeric ranges/statements are disjoint from competence. No benchmark, sealed IFEval/BFCL input, or recorded benchmark response was read. This measures two narrow synthetic output behaviors; it does not establish a universal skill selector.

## Execution and verification

256 same-run generation records, 6546 generated tokens; **803.824/3600 seconds** (13.40 GPU-minutes), including model load and cleanup. Peak allocated 57.65 GiB; overrun 0.000s. [Initial projection](projection.json), [measured projection](measured-projection.json).

192 canonical CPU checker cases and negative/threshold fixtures passed, along with inherited real-HF router slot/OFF/schedule tests. The real 48-layer raw-logit contract and grouped kernel parity/dispatch/OFF checks passed during loading. CPU audit reproduces all consumer scores, prompts/token IDs, profile means/top8 overlaps, centered/opposite/shuffled biases, screen totals and readings. No extra GPU generations for audit.

Foreground execution only; all quick-check flags coordinated under the review lock; Brian pid2705 excluded from availability blocking and untouched. The flag was removed after model cleanup. No process signals, termination, fitting, background launch or push.

Artifacts: [summary](summary.json), [records](records.jsonl), [CPU audit](audit.json), [CPU preflight](cpu.json), [runtime](runtime.json), [kernel](kernel.json), [prewritten reading](prewritten-reading.md), [source freeze](freeze.json), [run log](run.log), [inventory](artifact-inventory.json).

`P1-profiles.pt` contains float32 means/centered/shuffled tensors [2,48,128], three alpha3 biases [48,128], and 32 per-task dictionaries with float64 logit sums [48,128], non-EOS counts and source record IDs. Each per-task dictionary is also saved under `profiles/` during the same run. Profile-freeze JSON binds each tensor file before intervention outcomes. No P2 profile tensor exists because competence failed. Inventory lists artifact sizes and SHA-256 hashes.
