# Quick check 10 verification — generic write-time selector

Date: 2026-09-03  
Reviewer: sol  
Scope: `results/quick-checks/README.md` item 10; `self_extract_turn2_{check.py,rows.json,.log}`; the 20 records and metadata under `results/qwen/ledger-kv-probe-h1p/`; `scripts/ledger_kv_probe.py`.  
Execution: CPU-only, foreground, no model/GPU process, no process signal, and no repo write except this report.

## Bottom line

The literal output counts reproduce: over 56 aged constraints, SELF pinned scores 36, SELF pinned+echo scores 43, the recorded finder scores 37/48, full scores 44, evicted scores 14, and the recorded SELF control scores 22. The extractor prompt really does contain only one prior user turn at a time plus a fixed metaprompt; it contains no assistant answer, final query, `Constraint:` mark, checker label, or oracle span. All 96 unique pre-clamp selections in this run were located by the normalized-substring path; the Jaccard fallback selected none.

The interpretation needs substantial qualification. The SELF control is not exact-column matched to the SELF treatment that was actually run: it was constructed before 14 reminder spans were removed, so it pins 1,485 columns while SELF pins 1,303. SELF is also not cost-matched to the finder: it pins 1,303 versus 932 columns and adds 1,601 versus 1,215 echo tokens. Finally, the reported `0.87` and 41 extras are measured against the finder's selected spans before clamping, not against oracle standing instructions. The formula can exceed 1.0 and does so in session 08. These defects do not change the recorded 36/43 outputs, but they invalidate “exact-column control,” equal-budget “matches the finder,” and the claimed causal explanation that 41 harmful extras account for the echo gap.

## 1. Independent arithmetic

I loaded exactly 20 check-10 rows (`session` 0 through 19) and exactly 20 H1′ session records. The check-10 copy of every per-session H1′ count, `n_aged`, and finder column count matches the source H1′ record. Every H1′ `aged_pass` also equals the sum of its stored aged score-vector prefix. There were no linkage mismatches.

### Claimed totals

| quantity | recomputed |
|---|---:|
| sessions | 20 |
| aged constraints | 56 |
| SELF pinned | 36/56 |
| SELF pinned+echo | 43/56 |
| SELF nominal control | 22/56 |
| H1′ full | 44/56 |
| H1′ evicted | 14/56 |
| H1′ finder pinned | 37/56 |
| H1′ finder pinned+echo | 48/56 |
| H1′ echo-only | 37/56 |
| H1′ finder control | 18/56 |
| recorded coverage, macro mean | 0.8690493576 |
| recorded sessions with coverage >= 0.8 | 16/20 |
| recorded extras | 41 |

The log's rounded `0.869`, `16/20`, 41, and totals JSON all agree with the rows. The SELF rows retain only per-session `aged_pass`, not the constraint score vectors or generated text, so the 36/43/22 values can be summed but cannot be independently re-scored through the checker from this artifact. H1′ does retain the necessary score vectors and output records.

### Safety counts

| arm | aged pass | truncated sessions | degenerate sessions | comparison with H1′ full |
|---|---:|---:|---:|---|
| H1′ full | 44 | 1 | 2 | baseline |
| H1′ finder pinned | 37 | 0 | 0 | lower on both |
| H1′ finder pinned+echo | 48 | 0 | 1 | lower on both |
| SELF pinned | 36 | 0 | 0 | lower on both |
| SELF pinned+echo | 43 | 1 | 1 | equal truncation, lower degeneration |
| SELF nominal control | 22 | 1 | 4 | equal truncation, **two more degenerate sessions** |

SELF pinned+echo's sole truncated/degenerate event is session 16. The control truncates in session 05 and is degenerate in sessions 04, 05, 12, and 17. H1′ full has zero timeouts, but check 10 discards `timed_out`, `rep4`, `invalid_output`, quoting, generated token IDs, text, and per-constraint scores from `run_arm`; therefore those SELF safety fields cannot be audited or aggregated from the saved rows. In particular, three of the four control degenerations can only be inferred to be repetition events from the saved boolean and non-truncation state, not independently recomputed.

## 2. The prompt is isolated as claimed

The operative prompt is the fixed `ASK` string at `self_extract_turn2_check.py:43-45`. For every prior user turn, the code constructs a fresh chat context as:

`ASK.format(turn=context[a:b])` plus the empty assistant opener (`self_extract_turn2_check.py:79-81`).

`P._user_turns` returns only the text between that turn's `<|im_start|>user` and `<|im_end|>` boundaries (`scripts/ledger_kv_probe.py:168-181`). The loop excludes the final user turn with `uturns[:-1]`. I decoded and checked all 20 stored H1′ contexts:

- each extracted slice is exactly one source user prompt with literal `Constraint:` removed;
- no decoded context contains `Constraint:`;
- the extraction input has no earlier/later assistant answer, no final query, no scoring row, no `instruction_id_list`, no marked mirror, and no oracle span;
- the 4B is frozen, in eval mode, and decoded greedily by argmax for at most 256 tokens, stopping at `<|im_end|>` (`self_extract_turn2_check.py:20-39`).

The comment at line 77 (“everything before the last user turn”) is inaccurate, but the executed code is correctly per-turn. The module docstring is also stale when it says the “SAME frozen 1.7B” performs extraction: Qwen3-4B performs extraction and Qwen3-1.7B runs the scored arms.

The matcher itself is not an oracle path. It lowercases and collapses whitespace, searches the prior eviction range, and maps a quote back through tokenizer offsets (`self_extract_turn2_check.py:84-121`). Reconstructing all matches produced 96 unique pre-clamp spans, all by direct substring; the Jaccard fallback contributed zero. All hits landed in user turns, although the implementation searches the whole prior history and should be restricted to the quote's source turn for robust handling of duplicated text.

Several 4B outputs also quote the extraction metaprompt itself (“Quote verbatim ... later replies”). That text does not occur in the stored conversation, so it produced no matched span in this run.

## 3. What `coverage = 0.87` and `extras = 41` actually measure

### Finding QC10#1 — MEDIUM — the reported coverage is finder overlap, not oracle instruction coverage

At `self_extract_turn2_check.py:131-133`, `keepc` is `r["keep"]`: the H1′ taxonomy finder's selections. The code computes

`sum_c sum_s overlap(c, s) / sum_c len(c)`

over finder spans and SELF spans. It does not read the marked oracle constraints for this metric. It also sums overlapping predictions without deduplication. Consequently it is not bounded by 1; session 08 records 1.15. Coverage/extras are calculated before the later clamp/drop loop.

Exact reconstruction gives:

| definition | result |
|---|---:|
| recorded finder-overlap formula | macro 0.869049; 16/20 >= 0.8 |
| finder overlap using unique token columns | macro 0.859615 |
| oracle-clause recall, >= 50% gold-token coverage | 52/56 pooled = 0.928571; macro 0.933333; 17/20 >= 0.8 |
| oracle token-mass coverage | macro 0.878167 |

The clamp removes no covered oracle clause, so oracle clause recall is the same before and after its 14 whole-span drops. For context, the H1′ finder itself covered 54/56 oracle clauses (macro 0.966667) with seven zero-overlap extras. Thus `0.87` is reproducible but must be labeled “pre-clamp overlap with finder-selected token spans,” not “coverage of standing instructions.”

### Exact accounting of the 41 extras

“Extra” means a selected SELF span with zero token overlap with a finder-selected span, again before clamping. The 41 are:

- 27 one-off or continuation task sentences, such as “Write a short account ...” and “Now extend/revise ...”; and
- 14 standalone copies of “Every earlier constraint from this conversation still applies to this reply as well.”

Against the actual marked oracle rather than the finder, there are 44 zero-overlap spans: 30 task/continuation spans plus the same 14 standalone reminders. The difference is three “Now add a brief closing section ...” spans that the finder also selected, so they are not finder-relative extras. Four additional 4B lines combine a task, one or more real constraints, and the reminder into one long matched span; because those spans overlap a constraint/finder span, neither extras metric counts their task/reminder tails.

The task sentences are not obviously harmful. These sessions ask the model to continue or revise a newsletter piece, so the original subject and continuation request are useful durable task state even though they are not scored aged constraints. Their presence can plausibly help generation. The reminder is semantically different: it carries no concrete rule, consumes budget, can become wrong after a revocation, but can also cue the model to apply retained constraints. This run does not isolate either effect, so “41 extra spans dilute the echo” is unsupported.

### The echo clamp does drop content

The control is built at line 138, then the loop at lines 140-152 calls `P.echo_context` and removes any whole span that cannot be rendered. Exact reconstruction found:

- 14 standalone reminder spans are removed from `aged` and `keep`, 13 columns each, for 182 columns total;
- in four other sessions (06, 07, 11, 13), the reminder is the tail of a longer matched span. `echo_context` clamps those 52 reminder columns out of the rendered echo entry, but the caller leaves the original longer `keep` span intact, so the 52 columns remain pinned;
- the saved `matched` lists are post-drop (82 spans total), while `coverage`, `extras`, and `n_pin` describe the 96-span pre-drop selection.

Therefore only 27 of the 41 finder-relative extras survive as whole extra spans in the scored echo. Four uncounted embedded reminder tails remain pinned but are not echoed.

## 4. Column accounting and comparison fairness

### Finding QC10#2 — HIGH — the claimed exact-column SELF control is not exact

`matched_control_spans(keep, ...)` is called before the 14 whole reminder spans are removed. The treatment then runs with the reduced `keep`, while `control` is never recomputed (`self_extract_turn2_check.py:138-158`). This affects 14/20 sessions.

| session | nominal SELF columns (`n_pin`) | actual SELF columns | control columns | finder columns |
|---:|---:|---:|---:|---:|
| 00 | 101 | 88 | 101 | 79 |
| 01 | 83 | 70 | 83 | 42 |
| 02 | 82 | 69 | 82 | 43 |
| 03 | 63 | 50 | 63 | 27 |
| 04 | 62 | 49 | 62 | 20 |
| 05 | 81 | 68 | 81 | 36 |
| 06 | 99 | 99 | 99 | 59 |
| 07 | 93 | 93 | 93 | 60 |
| 08 | 91 | 78 | 91 | 53 |
| 09 | 77 | 64 | 77 | 40 |
| 10 | 47 | 47 | 47 | 64 |
| 11 | 82 | 82 | 82 | 40 |
| 12 | 29 | 29 | 29 | 48 |
| 13 | 89 | 89 | 89 | 50 |
| 14 | 40 | 27 | 40 | 25 |
| 15 | 30 | 17 | 30 | 49 |
| 16 | 82 | 69 | 82 | 46 |
| 17 | 95 | 82 | 95 | 51 |
| 18 | 94 | 81 | 94 | 70 |
| 19 | 65 | 52 | 65 | 30 |
| **total** | **1,485** | **1,303** | **1,485** | **932** |
| **mean** | **74.25** | **65.15** | **74.25** | **46.60** |

The control's 22/56 is a real recorded output, but it is not an exact-column null for the 36/56 treatment. It receives 182 more retained columns and has four degenerate sessions versus zero for SELF pinned. No causal specificity conclusion should use this control.

### Finding QC10#3 — HIGH — SELF versus finder is same-data but not same-budget

The favorable part of the comparison is sound: both methods act on the same 20 stored H1′ contexts; the scored target is the same 1.7B checkpoint; both use `run_arm` and the same checker wrapper; and each session's copied finder/full counts agree with the H1′ source record.

The resource comparison is not controlled:

- SELF pins 1,303 actual columns, mean 65.15, versus finder 932, mean 46.60: SELF uses 39.8% more total pin mass and exceeds finder mass in 17/20 sessions.
- Reconstructed SELF echoes add 1,601 tokens, mean 80.05, versus the H1′ finder's recorded 1,215, mean 60.75: SELF uses 31.8% more echo tokens.
- At the session level, SELF pinned beats/ties/loses to finder in 4/11/5 sessions; SELF echo beats/ties/loses to finder echo in 1/13/6.

Thus 36 versus 37 and 43 versus 48 are valid descriptive effectiveness counts, but not evidence of equal-cost matching or equivalence. There is no registered equivalence margin or paired equivalence test. “Reaches the full-context ceiling” is also too strong: 43 is close to full's 44 on this small development set, but closeness is not an equivalence result, and finder+echo itself scores 48.

A small provenance qualification also applies: H1′ was generated with `src/stencil/qwen3.py` hash `5122ec...`, while check 10 ran after the 4B parity change with hash `81a0ab...`. The 1.7B checkpoint hash is unchanged (`13bfab...`), and the worklog records that the 1.7B path and parity fixture remained unchanged, so this is not evidence of an outcome defect. A confirmatory comparison should nevertheless run all arms under one code manifest.

## 5. Leakage and selection-set status

### Prompt wording

The prompt explicitly defines the desired operation: identify an “instruction, rule, or constraint” that must be followed “in later replies.” That is strong task instruction, but it is generic and contains no benchmark taxonomy, expected quote, mark, final query, or checker information. It is the selector algorithm, not a hidden-answer leak. The accurate claim is “frozen/no task-specific fine-tuning”; “training-free” should not be read as saying the pretrained 4B has never seen similar language.

### Matcher

The normalized-substring matcher uses only extractor text and prior history, and its fallback was unused. It has no oracle input. Its whole-history search could map duplicate text to the wrong occurrence; registration should bind each completion to its source turn and match only inside that turn.

### Synthetic reminder

Quoting “Every earlier constraint ... still applies” is not a hidden-oracle cheat: it is literally visible in the user turn and identifies no concrete constraint. It is, however, synthetic benchmark scaffolding that resolves persistence explicitly and is not guaranteed in deployment. Four embedded reminder tails remain in pinned K/V, so check 10 does not fully remove its possible generation effect. A no-reminder ablation is required before claiming performance on implicit standing instructions.

### Finding QC10#4 — MEDIUM — the check-10 pipeline was selected on B3

The exact prompt was unchanged across checks 7-10, so “no prompt tuning” is supported. The whole pipeline was not untouched: item 9 inspected failures on these same 20 sessions, diagnosed the sentence/Jaccard matcher, and item 10 introduced direct substring matching in response. Git history shows the check-9 commit at 20:15 and check-10 at 20:28; their code diff is the matcher change. B3 is therefore correctly a development/selection set for choosing this selector and matcher. Check 10 is descriptive development evidence, not a held-out estimate.

The finder comparison has a different lineage problem. The H1′ finder weights hash is `6bd0e8...`; the corresponding training code included this exact `data/b3/mt-train-300.jsonl`, so finder selection is in-sample on these rows. Those old weights also included Multi-IF prompts/responses, as already recorded in `WORKLOG.md:2400-2408`. The current clean refit is `a3d156...`, but it is not the finder that produced the recorded 37/48. This does not leak into the frozen 4B extractor, but any future Multi-IF comparison against the old H1′ finder would be invalid.

No quick-check-10 code reads Multi-IF or BFCL. The selection-specific no-contact boundary can still be frozen now, but the project has previously used Multi-IF and BFCL development artifacts for other components. Any broad “untouched benchmark” wording would therefore be false; a separately registered no-contact family is needed for a strict zero-shot claim.

### Finding QC10#5 — MEDIUM — the saved SELF artifact is insufficient for full replay

Unlike H1′, the quick-check rows omit raw per-turn 4B completion token IDs/text before line cleanup, matched method/source-turn records, pre-clamp span lists, clamp/drop reasons, rendered echo text/token IDs, 1.7B generated text/token IDs, score vectors, rep4, timeout, invalid-output, and quoting fields. They also contain no self-contained provenance manifest. The script runs work at import time and writes rows non-atomically. Arithmetic can be verified, and selection can be reconstructed from H1′ plus `extracted_lines`, but the scored outputs cannot be independently decoded and re-scored.

## 6. Graded findings

| ID | severity | finding | consequence |
|---|---|---|---|
| QC10#1 | medium | `0.87` is a pre-clamp, double-counting overlap with finder selections, not oracle coverage; it reaches 1.15 in one session | relabel/recompute coverage before external evaluation |
| QC10#2 | high | control built before drops: 1,485 control versus 1,303 treatment columns | `22` is not an exact-column control result for SELF |
| QC10#3 | high | SELF uses +39.8% pin columns and +31.8% echo tokens versus finder; no equivalence test | 36/43 versus 37/48 is not a fair equal-budget “match” |
| QC10#4 | medium | matcher was changed after inspecting check 9 on the same B3 rows; old finder is trained on those rows and on Multi-IF | B3 is selection/development only; old finder cannot enter Multi-IF confirmation |
| QC10#5 | medium | SELF rows omit outputs, score vectors, and most safety/provenance fields | no independent checker/safety replay is possible |
| QC10#6 | medium | 41-extra causal story is wrong: 14 are dropped, surviving task spans may help, and four embedded reminders remain pinned | precision cannot be blamed for the five-point echo gap |
| QC10#7 | low | comments/docstring misstate whole-history input and “same 1.7B” extraction | documentation/provenance correction only |

No critical finding. The two high findings block use of this artifact as a controlled selector-vs-finder or selector-vs-null experiment; they do not refute that the saved SELF generations scored 36/43.

## 7. What must be registered before Multi-IF/BFCL evaluation

Before any benchmark model run, freeze and commit the following:

1. **Exact selector identity.** Hash the 4B checkpoint (`8a65ac...` in this checkout), config, tokenizer (`aeb133...`), Qwen implementation, exact `ASK` bytes, chat wrapper, BF16/greedy decoding, stop rule, 256-token extraction limit, line parser, normalization, substring matching, fallback threshold/tie-break, and allowed roles. State explicitly whether BFCL schemas/system/tool turns are always retained or processed; check 10 covers prior USER turns only.
2. **Final post-clamp selection semantics.** Match within the originating turn; decide prospectively whether ongoing task sentences and the reminder are retained, echoed, or rejected; represent multi-sentence outputs as bounded source sentences rather than one large span. Register a no-reminder synthetic ablation before benchmark contact.
3. **A valid null.** Build controls only after every filter/clamp/drop, and assert per session that deduplicated treatment/control column sets have equal cardinality and are disjoint. Store the actual sets. Do the same for echo-token cost if the echo comparison is intended to be cost-matched.
4. **Fair comparator budgets.** Register either (a) per-session cost matching for SELF and finder, or (b) separate unconstrained effectiveness and efficiency curves. Report pin columns, echo tokens, and total context/cache cost. Do not call 36≈37 or 43≈44 “matching/equivalence” without a prospective margin and paired test.
5. **Metrics.** Define oracle clause recall with one-to-one matching, unique-token coverage, and precision/extras against an explicit gold—not against another selector. Compute all metrics from the final spans that reach each arm. Register primary Multi-IF/BFCL outcome, clustering unit, confidence/test procedure, safety limits, and treatment of degenerate/truncated/invalid/quoting outputs.
6. **Clean lineage and stop rule.** Record B3 as used for prompt/pipeline choice and exclude it from validation claims. Freeze the selector now; do not alter it from Multi-IF/BFCL responses. If the finder remains a comparator, use and hash a clean no-Multi-IF fit rather than H1′'s `6bd0e8...` weights, and do not tune it on BFCL's inspected labels. Treat the already-accessed benchmarks as post-development evaluation, not globally untouched data; use a separately registered no-contact family for a strict zero-shot claim.
7. **Replay-complete artifact.** In one code revision/run manifest, save raw 4B completions per source turn, cleaned lines, match method and char/token coordinates, pre/post-clamp sets and reasons, actual pin/control columns, rendered echo and token cost, all 1.7B outputs/token IDs, complete score vectors, rep4/timeout/truncation/invalid/quoting flags, hashes, commit, invocation, and timestamps. Run all compared arms on the same stored histories and software manifest.

**VERDICT: CONFIRMED-WITH-QUALIFICATIONS.** The 36/43/22 and H1′ comparison totals are authentic, and the extractor is single-user-turn, mark-free, and oracle-free at inference. The current artifact does **not** establish an exact-column null, equal-budget parity with the finder, or that 41 harmful extras explain the remaining gap; those issues must be corrected and frozen before Multi-IF/BFCL.
