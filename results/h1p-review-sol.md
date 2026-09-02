# H1′ artifact review — sol, spec adversary (xhigh)

Date: 2026-09-02  
Scope: `FOCUS LADDER v1 / H1′`, `results/qwen/ledger-kv-probe-h1p/`  
Execution: CPU-only, foreground, no model process, no process signals.

## Verdict first

**CONFIRMED-WITH-QUALIFICATIONS.** The artifact is internally sound and the orchestrator chose the literal registered branch correctly. Recomputed from the 20 session records:

- `pinned = 37 > pinned_control = 18`;
- `pinned_echo = 48 > echo_only = 37`;
- total `pinned_echo` recovery is `(48 - 14) / (44 - 14) = 34/30 = 1.1333333333 >= 0.85`;
- every arm passes every integer-count safety comparison.

Therefore H1′ is **`ADVANCE-RETENTION`** under `LEDGER-PLAN.md:388-404`. This is unlike H1: its single candidate truncation exceeded H1's zero-tolerance percentage clause, whereas H1′ was prospectively registered with event counts and the H1′ candidate has 0 truncations versus `full`'s 1 (`LEDGER-PLAN.md:381-400`; `results/qwen/ledger-kv-probe-h1p/summary.json:100-110,147-307`).

The qualifications matter to what may be claimed:

1. Selection is automatic and mark-free **at runtime**, but the frozen finder was trained with supervised examples derived from this same `mt-train-300.jsonl` source corpus. H1′ is an in-sample mechanism diagnostic, not held-out evidence that automatic selection generalizes.
2. Stripping marks before turns 1/2 are generated changes every H1′ history relative to H1. The H1-to-H1′ count changes are small and statistically unremarkable, but the two jobs do not differ only in selector.
3. `full_echo - full = +2` is 3 constraint fixes versus 1 break (`p = 0.625` paired exact); it supplies no evidence of benefit in the non-evicted product regime.
4. Quotation exclusion is not a de-leak control. Every detected quoted fragment is itself a checker-required literal.

No critical or high finding was found. The registered decision is confirmed; the stronger readings “held-out target-blind selection,” “pure replication of H1 with only selector changed,” and “benefit without eviction” are not.

## Findings

### H1p-review#1 — MEDIUM — runtime selection is automatic, but it is evaluated on a source corpus used to fit the finder

There is **no direct runtime oracle-span leak** in the auto path at commit `cd73dad`:

- Prior-turn and final prompts have literal `Constraint:` removed before any history generation (`scripts/ledger_kv_probe.py:157-159,602-630`).
- The auto branch rejects any marked context, calls `salience2.extract_instructions` separately on each unmarked user turn, and retains only spans from turns earlier than the last (`scripts/ledger_kv_probe.py:230-255`). It never invokes `e2.constraint_span_records`.
- The marked mirror is constructed with the same already-generated assistant text. It is used to count the aged scoring targets and to report selection coverage; the generation loop receives only base/echo token IDs, automatic `keep`, an eviction range, and the matched control (`scripts/ledger_kv_probe.py:625-655,657-685`). The checker row is passed only after generation at lines 669-676.
- The eviction range depends only on first/final chat markers (`scripts/ledger_kv_probe.py:144-154`). Echo entries come from automatic `aged_recs` (`scripts/ledger_kv_probe.py:633-642`). Control matching sees automatic `keep` plus the eviction range, not the marked mirror (`scripts/ledger_kv_probe.py:340-360,643-646`).

I decoded all 20 stored contexts and histories: none contains `Constraint:`, every original user turn equals the corresponding corpus prompt with only that literal label removed, rerunning the linguistic finder reproduces every stored `keep` span, and rebuilding the marked mirror reproduces every recorded `auto_coverage` / `auto_extra`. The meta's runtime-isolation claim is therefore true (`results/qwen/ledger-kv-probe-h1p/meta.json:32-38`; `WORKLOG.md:2359-2365`).

But this is not held-out selection. The linguistic model's loader includes `data/b3/mt-train-300.jsonl` by default and derives positive spans from its `Constraint:` annotations before removing the marker and recasing the text (`src/stencil/salience2.py:827-860`). `training_docs` includes those examples in the synthetic training corpus (`src/stencil/salience2.py:1105-1113`), and the test regenerates the committed default weights from that full training set bit-for-bit (`tests/test_salience2.py:603-607`). H1′ then takes the first 20 rows of that exact source file (`scripts/ledger_kv_probe.py:571-573`). The model is a low-dimensional inspectable cue model rather than a text-identity memorizer, and marks are not an inference feature, but the evaluated clauses helped determine its fitted weights.

The coverage replay explains the `0.967`:

- 63 automatic spans were selected against 56 aged oracle clauses.
- 54/56 clauses meet the implementation's `>= 50%` gold-token coverage rule (micro recall `0.9642857143`). The reported `0.9666666667` is the macro mean of 18 sessions at 1.0 and sessions 005/016 at 2/3 (`results/qwen/ledger-kv-probe-h1p/summary.json:310-414`; raw session fields at `session-005.json:2934-2935` and `session-016.json:1949-1950`).
- The two nominal misses are not semantic misses: the finder selected the narrower phrase “in lowercase letters only” from both “write the whole reply in lowercase letters only” clauses, but that prediction covers less than half of the gold token window.
- Seven zero-overlap extras are real: the task-like sentence “Now add a brief closing section for the same newsletter piece” in sessions 000, 007, 010, 012, 015, 016, and 018.

So the finder essentially re-found the marked constraints on this data. The task still counts as **automatic in the operational, inference-time sense** required by the registered H1′ text: selection decisions were produced by the frozen algorithm from unmarked text, not copied from a runtime oracle. It does **not** count as held-out, target-blind generalization evidence. That distinction must accompany the result and is precisely why the sealed BFCL/random-span and native-pressure legs remain necessary.

### H1p-review#2 — MEDIUM — H1′ changes the base histories, so H1 versus H1′ is not a one-factor selector comparison

Auto mode removes the labels before generating turns 1 and 2, then places those new responses into all final-turn contexts (`scripts/ledger_kv_probe.py:609-624`). That is required to keep marks out of every arm, but it changes the input distribution, not merely the focus selector.

Direct H1/H1′ replay on the same 20 corpus rows found:

- 0/20 `history_token_ids` arrays are equal;
- 0/20 `context_token_ids` arrays are equal;
- H1′ `full` 44 versus H1 `full` 41 consists of 5 constraint fixes and 2 breaks (two-sided exact paired `p = 0.453125`);
- H1′ `evicted` 14 versus H1 `evicted` 15 consists of 1 fix and 2 breaks (`p = 1.0`).

Thus the higher full count and lower evicted count are fully consistent with ordinary sensitivity to mark removal and regenerated history. They are not an integrity anomaly, but neither can they be attributed to automatic selection. The valid H1′ evidence is its **in-job** paired factorial contrasts, for which all seven arms share each same unmarked history. Cross-job changes from H1's `+18/+21/+10/+13` to H1′'s `+23/+23/+11/+19` are descriptive only.

### H1p-review#3 — MEDIUM — the exact-column control is valid, but it is not always a non-constraint control

Column accounting is exact in all 20 records: selected/control set cardinalities are equal, sets are disjoint, all control columns lie within the eviction range, and the runtime `pinned_cols` counts match. The per-session pairs are:

`000 79/79; 001 42/42; 002 43/43; 003 27/27; 004 20/20; 005 36/36; 006 59/59; 007 60/60; 008 53/53; 009 40/40; 010 64/64; 011 40/40; 012 48/48; 013 50/50; 014 25/25; 015 49/49; 016 46/46; 017 51/51; 018 70/70; 019 30/30.`

The construction guarantees only “not selected by the finder,” however. It does not exclude gold constraints, because doing so would itself require the oracle (`scripts/ledger_kv_probe.py:340-360`). In five sessions the nearest-column control therefore retains 34 token memberships from incompletely selected gold clauses:

- sessions 004, 007, 016, and 017 retain the omitted bullet suffix `, each starting with '* '.`;
- sessions 005 and 016 retain the omitted lowercase-clause head `write the whole reply` (session 016 contributes both kinds).

The source clauses are visible in `data/b3/mt-train-300.jsonl:5,6,8,17,18`; representative selected/control coordinates are `results/qwen/ledger-kv-probe-h1p/session-004.json:6-38`, `session-005.json:6-46`, `session-007.json:6-54`, `session-016.json:6-54`, and `session-017.json:6-46`.

This is accidental overlap, **not oracle leakage**: it follows mechanically from matching near the complement of an automatic partial span. It makes “exact-column control” true but “non-constraint control” false for those cases. Because useful constraint fragments enter the control, the contamination would ordinarily attenuate, not manufacture, the observed `37 - 18 = +19` specificity contrast. The decision predicate remains satisfied, but the correct interpretation is “selected spans beat equal-mass nearby non-selected columns,” not “selected constraints beat columns known to contain no constraint information.”

The coverage schema also warrants precision in reporting. `auto_coverage` is one-way gold coverage; a prediction can cover a gold without a reciprocal precision condition, and `auto_extra` counts only predictions with zero gold-token overlap (`scripts/ledger_kv_probe.py:258-279`). The two narrow lowercase predictions are consequently neither covered golds nor extras. “Macro coverage 0.967; seven zero-overlap extras” is exact. “54 TP, 7 FP, 2 FN” would not follow from this metric without a separate one-to-one matcher.

### H1p-review#4 — LOW — `full_echo - full = +2` is within noise and does not establish non-evicted benefit

The raw result is correct: `46 - 44 = +2`, or `2/30 = 0.0666666667` of the induced full-minus-evicted gap (`results/qwen/ledger-kv-probe-h1p/summary.json:40-50,112-145`). At the constraint level it is 3 fixes versus 1 break; the two-sided exact paired test is `p = 0.625`. At the registered clustering unit, the mean session-normalized difference is `+0.0333333`, an exact sign-flip test is also `p = 0.625`, and a diagnostic session bootstrap interval is `[-0.05, 0.1166667]`. None was a registered gate, but all answer the brief's noise question consistently.

`full_echo` is the best in-job view of recency when original K/V is already present. It supplies no reliable evidence that echo improves the non-evicted regime, and no evidence of harm either. The positive result is instead concentrated in the forced-eviction contrasts: automatic selected-span retention and re-injection restore performance after prior-history eviction. H1′ must not be reported as a normal-context product gain.

### H1p-review#5 — LOW — detected quotation is required-literal compliance, not an independent de-leak test

Quotation flags replay exactly under the registered eight-token rule (`scripts/ledger_kv_probe.py:327-338`):

| arm | quoting sessions | quoted-stratum pass | non-quoting pass |
|---|---:|---:|---:|
| `echo_only` | 6/20 | 12/16 = 0.750 | 25/40 = 0.625 |
| `pinned_echo` | 7/20 | 18/20 = 0.900 | 30/36 = 0.833 |
| `full_echo` | 6/20 | 12/17 = 0.706 | 34/39 = 0.872 |

These reproduce the summary's 0.30/0.35/0.30 quotation rates and quotation-excluded rates (`results/qwen/ledger-kv-probe-h1p/summary.json:88-122`). Quoting responses pass more for `echo_only` (+12.5 points) and `pinned_echo` (+6.7), but less for `full_echo` (-16.6). This is selection, not a causal effect of quoting: quotation status is post-treatment and literal-heavy sessions have a different checker mix.

I decoded every matched eight-token window in all 19 flagged arm-session responses. Every match is part of a required exact title or required `P.P.S.` line; none matches the ledger header or one of the seven extra task sentences. Removing such sessions preferentially removes exactly the outcomes that title/postscript checkers reward. The quotation-excluded rate therefore cannot establish absence of echo leakage.

The retention-on-echo contrast is nevertheless not solely a detector artifact. On the union of quoting sessions, `pinned_echo - echo_only = 18/20 - 14/20 = +4/20` (4 fixes, 0 breaks). On the 13 sessions where neither arm quotes, it is `30/36 - 23/36 = +7/36` (9 fixes, 2 breaks). The safe wording is “the contrast persists outside detected eight-token quotation,” not “quotation leakage ruled out.”

### H1p-review#6 — LOW — provenance is sufficient for this review but is not self-contained

The artifact is tracked as 22 files, and the recorded runner SHA-256 `51eb5349...` exactly matches the `cd73dad:scripts/ledger_kv_probe.py` blob. The corpus, model, tokenizer, Qwen code, finder code/weights, benchmark wrapper, and vendored checker tree hashes also matched the reviewed `cd73dad` revisions (`results/qwen/ledger-kv-probe-h1p/meta.json:19-38`).

The meta still omits the Git commit, invocation/run id/timestamps, `src/stencil/ledger.py` (echo rendering), and `src/stencil/causal_moments.py` (score-vector wrapper). The runner can also resume by skipping existing session records (`scripts/ledger_kv_probe.py:590-605`), so the files demonstrate one configuration and within-session arm pairing, not one uninterrupted OS process. The externally supplied commit plus successful independent replay closes the practical review question, but future confirmatory artifacts should hash all direct dependencies and record the commit/invocation.

## Independent recomputation

I loaded exactly `session-000.json` through `session-019.json`, with no gaps or extra session records. Every record has exactly the seven registered arms and `max_new = 512` (`results/qwen/ledger-kv-probe-h1p/summary.json:3-18`). CPU replay produced zero substantive discrepancies:

- **140/140** verifier score vectors replay exactly from stored response text through the vendored checkers: **567/567** booleans total, including **392/392** aged booleans (56 aged constraints × 7 arms).
- **140/140** `aged_pass` and `aged_n` fields reproduce.
- **140/140** generated-ID arrays decode exactly to stored text and equal stored `n`.
- **140/140** rep4 values, truncation flags, degeneracy flags, invalid-output flags, and quotation flags reproduce exactly.
- **20/20** base contexts, histories, selected span lists, echo contexts, echo SHA-256s, echo added-token counts, eviction ranges, and exact-column controls reconstruct.
- Re-running `summarize_records` reproduces the complete stored summary. The sole bit-level difference from the equivalent count formula is the already-explained one-ulp duplicate: top-level `recovered_frac_pinned = 0.7666666666666666` is computed from floating rates, while the contrast entry is exactly `23/30 = 0.7666666666666667` (`scripts/ledger_kv_probe.py:693-695`; `summary.json:126-140,416-417`).

### Arm aggregates

| arm | aged pass / 56 | trunc | timeout | mean rep4 | rep4 > .5 | degenerate | invalid | quoting | pass excluding quoting sessions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `full` | 44 | 1 | 0 | 0.0881390964 | 1 | 2 | 1 | 0/20 | 44/56 |
| `evicted` | 14 | 0 | 0 | 0.0437690358 | 1 | 1 | 1 | 0/20 | 14/56 |
| `pinned` | 37 | 0 | 0 | 0.0561865108 | 0 | 0 | 0 | 0/20 | 37/56 |
| `pinned_control` | 18 | 1 | 0 | 0.0941451028 | 2 | 2 | 0 | 0/20 | 18/56 |
| `echo_only` | 37 | 0 | 0 | 0.0851493358 | 1 | 1 | 1 | 6/20 | 25/40 |
| `pinned_echo` | 48 | 0 | 0 | 0.0980956848 | 1 | 1 | 0 | 7/20 | 30/36 |
| `full_echo` | 46 | 1 | 0 | 0.0851066001 | 1 | 2 | 1 | 6/20 | 34/39 |

The compact aggregates match `results/qwen/ledger-kv-probe-h1p/summary.json:40-123`. Event locations also replay: `full` truncates in session 014 and has rep4/invalid degeneration in 017; `evicted` and `echo_only` have the 017 rep4/invalid event; `pinned` has none; `pinned_control` degenerates in 011/015 (011 truncates); `pinned_echo` has rep4 degeneration in 004; and `full_echo` mirrors full's 014 truncation and 017 rep4/invalid event. Representative raw evidence is `session-014.json:3073-3076,3593-3602,4661-4664,5181-5190` and `session-017.json:1351-1418,1760-1786,1972-2008`.

### Contrasts, recovery, and paired direction

The in-job gap is `44 - 14 = 30` passes (`30/56 = 0.5357142857`). All registered contrasts reproduce:

| contrast | pass difference | fraction of 30-pass gap | constraint-level fixes / breaks |
|---|---:|---:|---:|
| `pinned - evicted` | +23 | 23/30 = 0.7666666667 | 23 / 0 |
| `echo_only - evicted` | +23 | 23/30 = 0.7666666667 | 25 / 2 |
| `pinned_echo - echo_only` | +11 | 11/30 = 0.3666666667 | 13 / 2 |
| `pinned - pinned_control` | +19 | 19/30 = 0.6333333333 | 22 / 3 |
| `full_echo - full` | +2 | 2/30 = 0.0666666667 | 3 / 1 |

These agree with `results/qwen/ledger-kv-probe-h1p/summary.json:124-145`. The stored session-paired bootstrap for `pinned - pinned_control` also reproduces exactly: mean `0.3416666667`, 95% percentile interval `[0.1666666667, 0.5083333333]`, 2,000 resamples, seed 0 (`summary.json:418-426`).

The third registered condition uses total recovery from `evicted`, not merely the incremental `pinned_echo - echo_only` contrast: `34/30 = 1.1333333333`. For context, plain pinning and echo-only each recover `23/30 = 0.7666666667`; hence `RE-INJECTION-ONLY` would not trigger even without its additional `pinned_echo <= echo_only` requirement.

### Integer-count safety table

| arm | timeout events (must be 0) | trunc events (must be <= 2) | degenerate (must be <= 2) | invalid (must be <= 1) | safe |
|---|---:|---:|---:|---:|---:|
| `full` | 0 | 1 | 2 | 1 | yes |
| `evicted` | 0 | 0 | 1 | 1 | yes |
| `pinned` | 0 | 0 | 0 | 0 | yes |
| `pinned_control` | 0 | 1 | 2 | 0 | yes |
| `echo_only` | 0 | 0 | 1 | 1 | yes |
| `pinned_echo` | 0 | 0 | 1 | 0 | yes |
| `full_echo` | 0 | 1 | 2 | 1 | yes |

The thresholds come directly from H1′: truncation `<= full + 1`, degeneracy `<= full`, invalid `<= full` (`LEDGER-PLAN.md:397-400`). With `full = 1/2/1`, all summary `safe` flags are correct (`results/qwen/ledger-kv-probe-h1p/summary.json:147-307`).

## Literal H1′ decision

1. `pinned > pinned_control`: `37 > 18` — pass.
2. `pinned_echo > echo_only`: `48 > 37` — pass.
3. `pinned_echo` recovery: `(48 - 14)/(44 - 14) = 34/30 = 1.1333 >= 0.85` — pass.
4. Safety intact under the prospectively registered integer counts — pass for the candidate and, more strongly, for every arm.

**Outcome: `ADVANCE-RETENTION`.** The decision in `WORKLOG.md:2383-2386` is correct. What advances is a frozen-finder, automatic-at-runtime retention/re-injection mechanism on a small forced-eviction diagnostic. No wave/amplification claim returns, no held-out selector-generalization claim follows, and the `full_echo` diagnostic does not show a normal-context gain.

## Ranked next step toward the publish gate

1. **(c) First, perform the smaller CPU-only BFCL preflight disposition already forced by the evidence.** The BFCL harness is no longer something to wait for: its handoff is present (`WORKLOG.md:2371-2381`). Its immutable 100-label finder preflight currently reports `78/100 = 0.78`, below the registered `>= 0.80` floor, specifically 77/77 schema spans and only 1/23 user-instruction spans (`WORKLOG.md:2380`; threshold at `LEDGER-PLAN.md:432-434`). Independently replay that count, verify the label/hash and selection semantics, and record the preflight as failed before spending GPU. Do not tune on those 100 viewed labels. If BFCL remains Leg A, the honest recovery path is a prospectively specified finder repair followed by a new untouched labelled set, or a governed decision that the present BFCL leg is blocked. This cheap step determines whether the current publish-gate path is runnable.
2. **(a) Then run the registered Multi-IF 909 `text_ledger` confirmation on 1.7B**, if the project continues the ladder while BFCL is resolved. H1′ explicitly names it as the next rung after `ADVANCE-RETENTION` (`LEDGER-PLAN.md:403-404`), and H1′ now satisfies that precondition. It tests automatic re-injection at scale, but it neither independently validates KV retention nor satisfies the word “agentic”; the publish registration says a Multi-IF-only pass is insufficient (`LEDGER-PLAN.md:429-436`). Do not describe its ~30 GPU-hours as opening the publish gate by itself.
3. **(b) Run BFCL GPU preflights before its sealed cohort, but not as “wait for the harness.”** The harness and sealed/dev cohorts already exist. Full base-competence and variance preflights should wait until the failed finder floor is dispositioned and the registered chat-shim/non-thinking/4B-parity blockers are closed (`LEDGER-PLAN.md:421-434`; `WORKLOG.md:2375-2380`). A failing CPU floor makes a GPU preflight now wasteful and cannot authorize the sealed cohort.

After those steps, the registered route still requires the BFCL sealed ledger-versus-random-span result and native-pressure S2 at >=8k; H1′ and Multi-IF alone cannot meet the publish gate.

## Final verdict

**H1′ reading: CONFIRMED-WITH-QUALIFICATIONS.** All artifact arithmetic, score vectors, automatic-runtime selection records, exact-column accounting, contrasts, recovered fractions, quoting flags, and integer safety results reproduce. The literal result is **`ADVANCE-RETENTION`**. The result is in-sample for the finder, H1/H1′ histories are not identical, `full_echo - full` is noise, and quotation exclusion is not a leak control. Ranked next step: **(c) disposition the already-failed BFCL finder preflight on CPU; then (a) Multi-IF 909; then (b) the remaining BFCL GPU preflights before any sealed run.**
