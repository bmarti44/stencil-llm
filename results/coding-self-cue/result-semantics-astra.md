# Coding self-cue — independent semantic result audit (FINAL)

Reviewer: native Astra at requested xhigh reasoning, `/root/prose_data_review`, 2026-09-08. Author-disjoint from Kimi data, Sol implementation and parent's registration. Prior data review was preparatory, not blind validation. Fit-on: none; exposed DEV only. Parent explicitly authorized review of completed project batches while the fixed run continues. No feedback reaches the worker; no reruns, repairs, model calls, data/prompt/code/parameter edits or run-record changes are performed. This file is the sole reviewer output.

**FINAL: the registered screen does not pass; the fixed same-response recipe is parked.** Reviewed scope: all four projects, all 72 actual H/C/M requests and all 24 C raw recaps. Frozen commit `cf33e861`; approved bank SHA256 `925d58b6654b06de015b5090ff602db76012c13df044320e299092dd75e357f3`. Projects 0–2 were recorded as a PARTIAL audit during the fixed run; their findings remain below. Project 3 and final accounting were reviewed only after the parent's terminal/cleanup notice. No interim finding changed the run.

Accounting is complete, but model evidence is technically **INCOMPLETE**: four output caps, 68/72 technically complete responses, driver exit 2. Separately, completed responses contain executable, parser and recap failures. This is not a semantic null inferred from an interrupted call. M also fails the control prerequisite, so this run does not establish manual parity. Prior updater/reader failures stay parked, and no capped call earns a larger-cap rerun or near-identical prompt repair.

| Arm | Valid submissions | Cumulative functionality passes | Current-obligation passes | Complete turn passes | Complete project trajectories |
| --- | --- | --- | --- | --- | --- |
| H | 22/24 | 12/24 | 16/24 | 10/24 | 0/4 |
| C | 8/24 | 3/24 | 7/24 | 2/24 | 0/4 |
| M | 23/24 | 15/24 | 17/24 | 12/24 | 0/4 |

These totals preserve the saved consumer outcomes, including checks on retained state after rejected submissions. Passing an invalid-input check with a null stub does not turn that stub into useful code. Direct-source findings below do not silently alter the finite-check totals.

Across the **entire observed C prefix**, including optional immediate-work statements: **12/24 are complete and unambiguously correct, 2/24 have the specifically documented contextual ambiguities, 7/24 omit applicable content without a definite contrary assertion, and 3/24 contain definite incorrect claims**. The charitable count is 14/24 complete/correct; neither reading approaches the required 24/24. An error row can also have omissions, but is counted once in this partition. The two capped C responses have complete visible prefixes and are included in this descriptive semantic audit; they receive no executable or capacity credit. Standing-rule meaning alone is sometimes better than whole-prefix accuracy, as the per-turn tables show.

## Project 0 — exhibit labels

### Recorded executable results

These are the saved finite-check outcomes on each arm's actual applied state. They are not corrected using the raw proposed code, semantic recaps or oracle solutions.

| Arm | Valid submissions | Cumulative functionality passes | Current-obligation passes | Complete turn passes |
| --- | --- | --- | --- | --- |
| H | 5/6 | 3/6 | 3/6 | 2/6 |
| C | 5/6 | 3/6 | 3/6 | 2/6 |
| M | 6/6 | 6/6 | 4/6 | 4/6 |

H/C pass complete turns 3 and 5; M passes 0, 2, 3 and 5. No arm has a completely passing project trajectory. Calls 0 and 1 remain parser failures: H submitted the whole module, while C put `module.py` on a separate line after a plain Python fence. Their workspaces retain the title stub until turn 3. The failed earlier title therefore explains H/C's cumulative functional failures at turns 1–2; later index/full-label code was applied normally. All three arms accept boolean `number` values at turns 1 and 4 despite explicit exclusion, causing the saved obligation failures. C also accepts explicit-null `room` at turn 4 (`chk-r4-o4`).

### Six C raw recaps

Raw prefix meaning is auditable even when the submission parser rejects the response. This does not convert call 1 into a valid submission. Accurate immediate coding requirements are permitted alongside standing obligations, without inventing future/global scope.

| Turn / call | Standing-rule meaning | Additional interpretation |
| --- | --- | --- |
| 0 / 1 | Correct global ERR-for-invalid rule. | Accurate immediate title-validation summary; parser still rejects the response. |
| 1 / 4 | Correct ERR baseline and stable ascending-length token sort. | Padding/output details are current work requirements; no false future promotion. “Three-digit” is ordinary padding shorthand, not an explicit truncation claim. |
| 2 / 7 | Correct wall-labels optional None exception. | The parenthetical “optional, but permitted” qualifies “return None instead of ERR”; it does not require abandoning the permitted baseline. |
| 3 / 10 | Correct replacement plus continuing task exception. | The global object baseline is followed by the explicit wall-labels None permission. Read together, this is baseline-plus-exception decomposition, despite awkward “instead of … None” wording. |
| 4 / 13 | Correct object result for this gallery-index request and stable length sort. | Recap requires a present room to be a valid string; actual submitted code contradicts that recap for null. |
| 5 / 16 | Correct restored ERR/optional-None alternatives for the current edit. | The extra sentence saying the function “must return a list with a fourth element” omits the explicit optional-key condition. The preceding bullet supplies that condition contextually; a standalone unconditional reading would be wrong. Report this as ambiguity, not a definite invented rule. |

All six recaps identify the applicable standing-rule meaning. Across the entire prefix including optional immediate-work statements, **five are unambiguous and one has the turn-5 conditional-output ambiguity**; a contextual reading credits all six. No definite false global/future promotion is identified. This is separate from executable correctness and does not establish a working mechanism.

### Direct-source code audit beyond the finite checks

The following are source-derived findings from actual submissions/workspaces. Illustrative edge inputs were **not executed**, and saved check scores above are unchanged.

1. **HIGH — Required dependency use is missing in the final edit.** At turn 5 the user explicitly says to keep using `label_title` for the first element; none of H/C/M calls it. M also never calls `index_entry`, instead assigning a locally reconstructed string to a variable with that name, contrary to the explicit dependency-call/prevalidation request. H/C do call `index_entry` but omit the required boolean exclusion in their local number validation. This is actual-code noncompliance despite all three recorded turn-5 check sets passing. In all three real pre-turn states, `label_title` supports subtitles; independently rebuilding the title loses that behavior in `label_full`.

2. **MEDIUM — Invalid booleans are accepted beyond the tested index cases.** All three arms' `label_full` implementations at turns 2 and 5 use `isinstance(year, int)` without excluding bool, even though the natural request explicitly excludes booleans. Their turn-5 number validation has the same defect. The recorded turn-1/4 number failures are observed executions; the year/final-number cases here are static findings, not additional run measurements.

3. **MEDIUM — Empty cleaned pieces remain in rendered labels.** Applied M turn-0 title code, all turn-3 title code, and all turn-2/5 full-label code validate that some cleaned token exists but then join the unfiltered cleaned sequence. A mixed name such as `vase !!!` therefore retains a trailing space rather than joining only surviving tokens. Artist and room construction use the same pattern. The submitted H turn-0 proposal has additional invalid-name handling problems, but it was rejected and never became workspace state.

4. **MEDIUM — M places room text before tags and bypasses validation when rebuilding the index.** Its turn-4 index produces the room suffix on the numeric prefix before appending tags, whereas the request appends the room to the completed index line. Its turn-5 inline reconstruction repeats that ordering and ignores invalid/non-cleanable room values instead of obtaining the actual dependency's invalid result. Existing room tests have no tags, so the ordering defect is not exposed by their saved results. C's separate null-room failure is already visible in the recorded checks.

At turn 2 all arms inline title construction. The turn-2 expression `label_title(record)` establishes the expected first-element value; turn 5's explicit “keep using” directive makes the missing call independently decisive without relying on whether equivalent inlining would have been acceptable earlier. No arm's later state was silently repaired to restore that dependency.

### Batch integrity

Read exactly the 18 completed turn records and corresponding saved HTTP receipts. All raw outputs match the assistant content in the saved HTTP bodies, and request/response JSON, base64, byte lengths and hashes reconcile. All 18 responses are HTTP 200 with `stop` finishes. The bank hash matches the approved data. Every same-arm pre-module equals its preceding actual post-module; pre/post hashes match. Natural messages match the correct frozen source/request prefix. Canonical history appends only a valid extracted code fence; rejected responses append no fabricated code. Current check IDs equal the initial-plus-cumulative-functional and current-obligation sets. No semantic repair, cross-arm state substitution or prose-prefix carry is present in this reviewed batch.

## Project 1 — lighting cues

### Recorded executable results

| Arm | Valid submissions | Cumulative functionality passes | Current-obligation passes | Complete turn passes |
| --- | --- | --- | --- | --- |
| H | 6/6 | 2/6 | 2/6 | 1/6 |
| C | 0/6 | 0/6 | 0/6 | 0/6 |
| M | 6/6 | 2/6 | 2/6 | 1/6 |

H/M pass only turn 1 completely. C calls 19/22/25/28/31 omit the required path on the fence's opening line; call 34 reaches the 768-token cap. Every C patch remains unapplied and every C workspace remains the initial stubs. C's prose is not used to repair these failures. H/M's gap feature fails `f2a` from turn 2 onward. Their turn-4 compaction edits introduce actual runtime failures on previously working list inputs (H calls `.get` on a list; M reads uninitialized `tol`); those actual dependencies remain present at turn 5. No arm passes the whole trajectory.

### Six C raw recaps

| Turn / call | Semantic assessment | Reason |
| --- | --- | --- |
| 0 / 19 | Incomplete permission coverage | Correct invalid-string baseline; stating the live tie rule is harmless. The explicit choice of either run representation is absent. This is an omission, not evidence that the recap forbids object runs. |
| 1 / 22 | Correct | Invalid-string and first-seen tie rules are complete for this scheduler edit; no runs are produced. |
| 2 / 25 | Correct | Global fallback plus task-specific duration-first exception and remaining input-order tie are accurately decomposed; extra current gap requirements are allowed. |
| 3 / 28 | Incorrect additional requirement; incomplete permission coverage | Correct invalid-string rule rejects the assistant error-object suggestion, and the duration exception is retained. However, the recap incorrectly says this integration function accepts dictionary-form `cues`, even with an optional `gap`; the current request requires a cue list. The run-representation permission is also omitted. |
| 4 / 31 | Incorrect lifecycle claim | Invalid-string and run alternatives are correct. But the explicit sentence requiring `schedule_cues` to use original order contradicts the user's instruction that this untouched function keeps its documented duration-first behavior. Cancelling the rule binds subsequent edits, not that existing dependency. The general version rule is stated; it does not require version fields inside run objects. |
| 5 / 34 | Correct observed prefix | Invalid-string, restored first-seen ordering, returned-object version and optional run alternatives are all present. Extra tol/gap/detail statements are accurate current work requirements. The complete prefix is visible before truncated code; this gives no executable credit to the capped call. |

Thus **3/6 prefixes are complete and correct, 1/6 omits a permission without asserting its opposite, and 2/6 contain definite incorrect additional/lifecycle claims**. Turn 3 also has an omission. General references to the first-seen rule alongside its explicit local exception are credited by meaning. Merely listing a live but irrelevant rule is not a failure; the turn-4 failure is its concrete false statement about the preserved scheduler.

### Additional direct-source code findings

5. **MEDIUM — H/M omit explicit type exclusions, including cases their passing turn does not cover.** Both compaction implementations accept bool samples (observed `o0b`, and later `o4b`). The applied H/M scheduling definitions accept bool `at`/`dur`; M also fails to validate that `id` is a string at turns 1–2. Both gap/tolerance extensions accept bool parameters. These contradict natural type requirements. H/M turn-1 finite checks pass despite their missing validation.

6. **MEDIUM — Wrapper input boundaries and optional-value handling remain wrong.** H/M turn-3 and turn-5 renderers delegate nested dictionary cue inputs without first requiring a list, and the final versions similarly permit nested sample dictionaries. Saved `o3d` and `o5d/e` expose these boundaries. M's final renderer treats explicit-null `detail` as absent, contrary to the request; this latter case is a static finding. M also overwrites `cues` with the gap wrapper and then iterates its string keys when producing detail order, so a valid combined gap/detail request takes its invalid branch. H/M preserve their actual dependent scheduling/compaction failures, rather than secretly substituting the reference implementations.

The rejected C proposals have further visible code defects, but they never become applied state: turn 1 sorts before validating elements, turn 2 charges a gap before the first cue and omits some shape checks, turn 3 explicitly allows the forbidden nested wrapper, and turn 5 is incomplete. These observations explain why raw proposals cannot substitute for the recorded consumer outcome; they are not added executed tests or corrected scores.

### Batch integrity

All 18 project-1 saved wire bodies, JSON, base64, lengths and hashes reconcile with the exact issued messages and raw outputs. Source/request prefixes, same-arm pre/post modules and their hashes, canonical history and exact current check sets reconcile independently. There are 17 `stop` responses and one recorded `length` response; the capped call is technically incomplete but its retained-state checks and slot accounting are recorded. Parser failures append no generated code and the cap does not reset the module. No rejected recap or code is forwarded as assistant history.

## Project 2 — puzzle scores

### Recorded executable results

| Arm | Valid submissions | Cumulative functionality passes | Current-obligation passes | Complete turn passes |
| --- | --- | --- | --- | --- |
| H | 6/6 | 2/6 | 6/6 | 2/6 |
| C | 3/6 | 0/6 | 4/6 | 0/6 |
| M | 6/6 | 2/6 | 6/6 | 2/6 |

H/M pass turns 0–1 completely, then fail the drop functionality from turn 2 onward; the failed totals propagate into their final integration result. C calls 37/40/43 are parser failures (multiple fences or missing fence path), so `solve_total` remains the initial stub throughout. Its later rank/summary patches apply, and its final nonempty entries are rejected by that real stub dependency. C's four current-obligation passes include turns 0 and 2, whose retained null stubs happen to return the required invalid value; these are not complete-turn or useful-functionality successes. There is no passing project trajectory in any arm.

### Six C raw recaps

| Turn / call | Semantic assessment | Reason |
| --- | --- | --- |
| 0 / 37 | Correct | Null-for-malformed is scoped to the current function; additional immediate scoring requirements are accurate. The malformed fence remains rejected. |
| 1 / 40 | Incomplete | Null baseline and preservation of untouched code are correct, but the new leaderboard alphabetical tie rule—including its explicit case-sensitive meaning—is absent. |
| 2 / 43 | Incorrect immediate requirement | The recap correctly limits the alias to this function and does not adopt the assistant champion suggestion. However, saying `drop` takes precedence if both keys are present directly contradicts the requirement to reject their coexistence. |
| 3 / 46 | Correct | Null baseline plus the new equal-total input-order rule are explicit. “Maintain existing behavior” is reasonably qualified by the immediately stated tie change. |
| 4 / 49 | Ambiguous indirect ordering coverage | New invalid-string convention and non-retroactivity are explicit; the exact two-key shape excludes the unadopted champion suggestion. “Validate and order … using rank_board” names the correct preserved dependency, but does not itself restate the current first-seen tie rule. Credit if a named, already-established dependency contract is sufficient; otherwise this is an ordering omission, not a contrary ordering rule. |
| 5 / 52 | Incomplete adopted-field meaning | Correct current invalid result, old-function preservation, and entries-only champion key/board-only two-key shape. It does not specify that champion means the top-ranked name, or null for an empty entries list. Ordering is again only indirectly specified through rank_board. No false global or retroactive adoption is asserted. |

Overall: **2/6 complete and explicit, 1/6 correct under a contextual dependency-contract reading, 2/6 incomplete, and 1/6 definite incorrect additional claim**. Charitable ordering credit makes 3/6 complete; it does not supply the missing champion empty-case/value semantics in turn 5. These are recap assessments only; no rejected code is repaired.

### Additional direct-source code findings

7. **MEDIUM — H/M confuse place order with point order and accept explicit-null drop values.** Their turn-2 implementations sort finishing places ascending and discard from that list, removing high-scoring placements instead of the lowest base-point scores. This is already exposed by `chk-r2-f1/f2`, and the same real code supplies wrong totals to the final renderer. Separately, present-null `drop`/`discard` is treated as absence, contrary to the non-negative-integer contract. M detects coexistence by non-null values rather than key presence, so one null alias can also bypass the required two-key rejection. The latter input cases are static findings, not additional executions.

8. **MEDIUM — M and applied C preserve extra input row fields in rank outputs.** M's turn-1/3 and C's applied turn-3 rankers return sorted original row dictionaries instead of the requested `{name, total}` row shape. H constructs that specified shape. This is a direct shape limitation beyond the saved rank cases, which contain no extra fields; no new test was run.

All three applied final renderers use their actual `solve_total` and `rank_board` dependencies. H/M's early helper and validation behavior otherwise remain unchanged when the global invalid convention changes; the final newly edited renderers translate null rejection into the required string. The final champion field is introduced only for the entries form, and no prior working summary adopts the earlier non-authoritative suggestion. C's rejected turn-0 scoring proposal would accept a missing places key as an empty list, but that proposal never entered its workspace.

### Batch integrity

All 18 project-2 request/response bodies, JSON, base64, lengths and hashes reconcile; all finish with `stop`. Exact frozen source/request prefixes, actual per-arm pre/post state and hashes, canonical histories and current check sets reconcile independently. Three C parse failures retain prior state and append no generated assistant code. The later applied C rank and render definitions operate with the unrepaired scoring stub. No cross-arm or reference-code substitution appears.

## Project 3 — tray placement

### Recorded executable results

| Arm | Valid submissions | Cumulative functionality passes | Current-obligation passes | Complete turn passes |
| --- | --- | --- | --- | --- |
| H | 5/6 | 5/6 | 5/6 | 5/6 |
| C | 0/6 | 0/6 | 0/6 | 0/6 |
| M | 5/6 | 5/6 | 5/6 | 5/6 |

H/M pass turns 0–4 on the saved finite checks. C calls 55/58/61/64/67 all fail the fence-path contract, leaving every target as its initial stub. Calls 69/70/71 all reach the 768-token cap: none applies a patch, and H/M's existing turn-4 plan code is checked against the new stop-feature requirements. Their saved failures therefore describe retained pre-upgrade code; the truncated proposals are not repaired, applied or credited. No complete project trajectory passes.

### Six C raw recaps

| Turn / call | Semantic assessment | Reason |
| --- | --- | --- |
| 0 / 55 | Correct | Invalid marker, reading-order selection and free dict-key order are stated. Selecting the filled slots in that order supplies the requested ordered placement result; no contrary returned-coordinate rule is asserted. |
| 1 / 58 | Correct | Same three live obligations; reading-order selection governs first_open. The declined checksum is not adopted. General wording is read as the current-edit obligations, not a request to rewrite finished code. |
| 2 / 61 | Incomplete permission coverage | Reading order is retained and BAD is the correct immediate-request marker. Listing it under “for this request” is allowed; it is not evidence of a new global marker rule. Free dict-key order is omitted. |
| 3 / 64 | Incomplete scope/permission coverage | Reporting lists correctly use column-first order, and the rejected colleague quotation is not adopted. The recap omits both free key order and the global reading-order meaning that remains applicable to reporting single-slot first_open; mentioning reading order only for allocation does not cover that output. It does not explicitly forbid the retained meaning, so this is an omission. |
| 4 / 67 | Incomplete permission coverage; overbroad phrasing noted | Current allocation reading order, successful top-level ok and immediate batching/default-summary requirements are correct. Free key order is omitted. “For all functions” omits write/edit-time qualification; contextual current-edit scope avoids a definite retroactive assertion, but a literal demand that every existing function now return an ok dict would be wrong. This sensitivity does not change its incomplete classification. |
| 5 / 70 | Incomplete permission coverage | Allocation reading order and ok are retained, reporting-list exception remains explicitly reporting-scoped, and the immediate stop-mode fields are identified. Free key order is omitted. The phrase putting the stop fields “in reading order” is reasonably understood to order the coordinate list, not the scalar bid. Visible recap is complete before the capped code. |

Thus **2/6 prefixes are complete/correct and 4/6 omit applicable content**. Correctly scoped extra reporting information in the final allocation recap is not itself stale leakage. The current-request BAD/INVALID markers are not automatically promoted to durable rules merely because the prefix also contains standing obligations.

### Additional direct-source code findings

9. **MEDIUM — Present null values bypass explicit option validation in applied code.** H/M turn-3 `summarize_occupancy` treat `list_open: null` as absence rather than the required INVALID result. M's turn-2 `assign_slots` likewise treats `skip: null` as absence although a present skip must be a list; its turn-4 `plan_report` passes that same invalid batch through its actual permissive dependency. H's skip validation rejects the null value. These are source-derived static findings beyond the saved cases, not extra executions or score changes. They qualify the apparent perfect H/M finite-check prefix.

H/M's applied code correctly preserves first_open reading order while introducing column-first reporting lists; the allocation integration uses default summary options and does not apply the reporting list exception globally. It calls the actual assignment/summary functions, carries completed placements as extra blocked cells, and adds ok only to the newly written plan result. Boolean counts/coordinates explicitly permitted by this project are correctly treated as integers, rather than importing the other projects' bool exclusions.

Rejected C proposals show additional defects: the first summary compares coordinate tuples against the tray's list pairs, and the later plan rebuilds an absent skip as explicit null. The final capped C proposal updates occupied cells before checking shortfall, while the capped M proposal exits before validating later batches. These are observations about unapplied partial submissions, not completed implementation claims. H's partial final proposal also has not demonstrated validation of later skip conflicts against the frozen completed occupancy. The only applied state at this point remains each arm's saved turn-4 code (or C stubs).

## Final integrity, resource evidence and interpretation

Independently reconciled **all 72** saved requests/responses: exact base64 bytes, body lengths, SHA256 hashes, JSON, issued native messages and returned assistant content. All HTTP statuses are 200; 68 finishes are `stop`, four are `length` (calls 34/69/70/71). There are 15 parser failures (H 1, C 14) and four capacity failures (H 1, C 2, M 1), with no transport failures. All 72 check sets and slots are recorded. Same-arm actual pre/post modules and hashes, source/request prefixes, canonical histories and exact initial/cumulative-functional/current-obligation check IDs reconcile. Invalid/capped responses retain state and append no fabricated code. Valid code, including its comments/docstrings, persists; outside-fence recap prose does not. No oracle replacement or cross-arm state repair appears in these records.

Saved usage reconciles with local prompt counts on every call: 157,919 prompt + 26,922 completion = **184,841 tokens**. Per arm, H uses 57,986 + 8,297; C uses 37,433 + 10,293; M uses 62,500 + 8,332. C's smaller prompt total is partly the consequence of rejected code never entering history, so these totals do not establish a useful-work efficiency gain. Summed HTTP elapsed time is 1,178.775 seconds; driver elapsed time is 1,212.160 seconds. The lifecycle records exit 2, successful log/stop/remove operations, `cleaned: true`, and **1,714.459 seconds** of owned GPU reservation within the 3,600-second ceiling. Review involved no additional model calls or code executions.

The conjunction fails independently on capacity eligibility, C executable completeness, C recap completeness and M control completeness. Completed failures justify parking this fixed same-response recipe under the prospectively registered stop-loss; the capped final implementations remain incomplete evidence rather than proof of their hypothetical finished semantics. No statistical significance, equivalence, general coding benefit, or human-time saving follows from four exposed Python DEV projects. The broader goal—including useful automatic parity with competent manual prose on a fresh, larger executable study—remains unproved.
