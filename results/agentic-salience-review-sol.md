# AGENTIC SALIENCE draft registration review — sol

Date: 2026-09-02  
Scope: prospective BFCL Leg A repair in `agentic-salience-draft.md`  
Execution: CPU-only, foreground, no model process, no process signal, no sealed model run. The existing CPU suite `CUDA_VISIBLE_DEVICES='' uv run pytest -q tests/test_bfcl.py` passed 11/11.

## Bottom line

The diagnosis is substantially right: salience2 recognizes persistent response constraints, whereas BFCL mostly presents stateful task requests and parameters. The proposed repair is not ready to register. K1–K3 is not a complete account of the information BFCL later turns need; the K2 regex does not yet exist as an exact prospective object; the proposed “untouched” 704-case label pool contains extensive task-family and exact-text recurrence from the viewed dev labels; and the current candidate/control code does not implement the arm descriptions faithfully.

The next draft should use the minimal, role-based policy—schemas plus all completed prior user turns—and call it exactly that, not “selective salience.” Its control must be newly and exactly registered against prior tool/assistant content, with schemas common to candidate and control. The old 100-label finder result remains a failed preflight, but no replacement finder-label gate is needed for a policy that has no finder.

No critical finding was found because this is still a pre-registration draft and no BFCL outcome was spent. Four high findings block adoption as written.

## Independently recomputed facts

- The old result is exactly 78/100: 77/77 `tool_schema` items are declared hits and salience2 finds 1/23 `instruction_sentence` items. This follows the scorer literally (`scripts/bfcl_mt.py:528-550`) and the file contains 77 and 23 items (`data/bench/bfcl_v3_mt/finder_labels.json:4-821`). Its SHA-256 is exactly `eb2120e00869baeb4624cd317df5727721b7074d02928449f2ed2b58b8ce55e1`, agreeing with `WORKLOG.md:2377-2380`.
- The draft's logit interval is wrong for the committed default finder. Replaying `DEFAULT_LINGUISTIC.logit` over every clause gives maximum-clause logits for the 22 misses from **-8.395317 to -1.267946**, not `[-8.4, -4.4]`. All are below the registered zero-logit decision threshold, so the qualitative miss diagnosis survives, but “rejects them confidently” is overstated for the upper tail (`agentic-salience-draft.md:6-8`; `src/stencil/salience2.py:688-708`).
- The corpus arithmetic is correct: 4 categories x 200 cases = 800; 32 dev + 64 sealed leaves 704, exactly 176 per category. The proposed 25/50/25/50 draw sums to 150 but samples the balanced population with category weights 1:2:1:2 (`data/bench/bfcl_v3_mt/cohorts.json:2-103`; `agentic-salience-draft.md:43-47`).
- The “704 untouched cases” are not text- or task-family-disjoint from the viewed 100 labels. Of the 23 viewed instruction-sentence strings, **22 occur as substrings in the proposed pool, for 55 occurrences; 3 recur as exact whole messages, for 8 occurrences**. More broadly, **304** non-cohort user-message occurrences exactly equal one of the **133** unique dev messages. BFCL variants share the same underlying numbered task: for example, `base_0` and `long_context_0` have identical questions (`data/bench/bfcl_v3_mt/cases_base.jsonl:1`; `data/bench/bfcl_v3_mt/cases_long_context.jsonl:1`). The cohort contains 84 distinct numeric task IDs, and 240 of the nominal 704 remainder cases are cross-category siblings of one of those IDs (`data/bench/bfcl_v3_mt/cohorts.json:3-101`).
- A CPU oracle-history replay of the 32-case dev slice produced 147 next-generation prompts. Eleven unmodified prompts exceeded K=8192, in four long-context cases. Across those 11 contexts, the prefix eviction removed 241,035 token-column occurrences: **199,685 tool = 82.8448%**, **39,709 schema = 16.4744%**, **993 boilerplate = 0.4120%**, **465 user = 0.1929%**, and **183 assistant = 0.0759%**. This uses the exact Qwen tokenizer, the harness renderer, ground-truth calls, and the registered prefix eviction (`scripts/bfcl_mt.py:39,106-143,300-340`). It confirms the brief's premise that native pressure is chiefly tool-output pressure.
- On those same oracle histories, every one of the 115 generation contexts having a prior user turn gets `budget == len(prior_user_columns)`: 12,609/12,609 prior-user columns in aggregate. Thus the current control pins **all** prior-user columns, while the candidate uses that equal cardinality for selected user columns first and then schema columns. Current salience2 selects only 293/12,609 = **2.3237%** of prior-user columns, with zero selected in 99/115 contexts (`scripts/bfcl_mt.py:174-212,225-297`). This is not the registered “random-span” KV control.
- The current string control is not total with the real tokenizer. CPU construction raised `ValueError` for dev `multi_turn_miss_func_181` turn 5 and `multi_turn_long_context_33` turn 2; trying the complete current +/-8 target window produced no exact round-trip candidate. `_control_context` also lets the first `control_echo` round-trip error escape (`scripts/bfcl_mt.py:238-254`; `src/stencil/bfcl.py:99-116`). The passing test uses only a whitespace toy tokenizer and cannot expose this (`tests/test_bfcl.py:93-107`).

## Findings

### Agentic-salience#1 — HIGH — K1–K3 omits state-bearing tool results and generated actions

The first sentence of the proposed object says losing K1–K3 makes a later correct call impossible and “nothing else” does (`agentic-salience-draft.md:18-27`). BFCL contradicts that completeness claim.

The checker is cumulative in two distinct ways:

1. Stateful class instances are reused on subsequent calls/turns (`vendor/bfcl_eval/eval_checker/multi_turn_eval/multi_turn_utils.py:39-62`). After every non-empty ground-truth turn, all public simulator state must equal ground truth (`vendor/bfcl_eval/eval_checker/multi_turn_eval/multi_turn_checker.py:100-110,162-194`).
2. The response check for the current turn accepts required execution results found anywhere in all model execution results so far; the checker explicitly documents earlier-turn invocation as the reason (`vendor/bfcl_eval/eval_checker/multi_turn_eval/multi_turn_checker.py:72-78,112-118,197-217`).

Later calls therefore need more than persistent directives and user-side literals. In dev case `multi_turn_miss_param_107`, the user asks for “that order”; `place_order` creates and returns `order_id=12446`, and later ground truth calls `get_order_details(12446)` and `cancel_order(12446)` (`data/bench/bfcl_v3_mt/cases_missing_params.jsonl:108`; `data/bench/bfcl_v3_mt/answers_missing_params.jsonl:108`; generated-ID semantics at `vendor/bfcl_eval/eval_checker/multi_turn_eval/func_source_code/trading_bot.py:379-398`). Flight booking similarly generates booking and transaction IDs in tool output for later operations (`vendor/bfcl_eval/eval_checker/multi_turn_eval/func_source_code/travel_booking.py:466-496,549-573,819-855`). Those values need not exist in any user sentence.

Assistant tool-call text is also the action trace of what the agent actually did. It can be necessary to resolve later references when the environment response is terse. Tool schemas, earlier user intent/parameters, generated calls, returned identifiers/results, and accumulated state are the honest information classes. K1–K3 covers only the first two plus an almost orthogonal instruction-following class. The draft's disclosure that tool/assistant retention is “separate, unregistered” is honest, but it prevents K1–K3 from being called *the* object for general long-horizon agentic work.

Required disposition: either add a K4 state-bearing tool/action trace and register its extractor, or narrow the experiment to “role-based retention of prior user requests on BFCL.” The latter is the smaller and cleaner option.

### Agentic-salience#2 — HIGH — the new label pool is not untouched

Excluding only the 96 full case IDs does not separate BFCL's shared task families. The four category files are transformations of the same numbered tasks, and exact questions recur across them (`data/bench/bfcl_v3_mt/cases_base.jsonl:1`; `data/bench/bfcl_v3_mt/cases_long_context.jsonl:1`). The recomputed 22/23 substring recurrence and 304 full-message recurrences mean a seed-20260903 draw from the advertised pool can directly redraw viewed language.

This is a leakage problem even though no one tunes on the new labels: the K2 class list was designed after seeing the old 100, and the proposed acceptance sample contains the same strings and sibling tasks. A fresh hash does not make repeated content fresh. If a selective repair remains, split by underlying numeric task ID across all four categories before drawing, exclude hashes of every viewed sentence and its containing message, and freeze the implementation hash before the draw. The 704 number must then change; 84 task IDs are already represented in dev/sealed, leaving 116 task IDs or 464 category cases before exact-text de-duplication.

### Agentic-salience#3 — HIGH — the current arm/control mechanics do not match either proposal

Schemas are not simply “retained.” They are appended after selected user entries to a list that is truncated at a budget capped by the number of prior-user columns (`scripts/bfcl_mt.py:263-281`). With the current selective finder, the budget is inflated by the large schema set, so it equals all prior-user columns in every recomputed eligible dev context. Candidate pinning spends those columns on the few selected user tokens and then an initial slice of schemas; control pinning spends them on every prior-user column (`scripts/bfcl_mt.py:266-297`). If all user turns become entries under the minimal alternative, they consume the whole budget before a schema column is reached. Neither construction implements “schemas + all prior user turns.”

The echo comparison is also unstable across within-turn tool steps. Candidate extraction always excludes the last user location (`scripts/bfcl_mt.py:180-200`), but control text takes user messages from `messages[:-1]` (`scripts/bfcl_mt.py:282-286`). After an assistant/tool message has been appended and the generation loop repeats (`scripts/bfcl_mt.py:391-434`), `messages[:-1]` includes the current user turn. Candidate and control then draw from different temporal domains.

Finally, the real-tokenizer failures above make the control non-total. These are blocking design/implementation errors, not details to repair after registration or after a sealed run.

### Agentic-salience#4 — HIGH — K2 and its proposed gold are circular and under-specified

There is no K2 regex in the repository: the only definition is an English list in the draft (`agentic-salience-draft.md:21-24,29-34`). It does not fix delimiters, Unicode handling, boundaries, unit/address lexicons, date formats, overlap precedence, sentence segmentation, or whether a match returns a span or a Boolean. “Fixed regex family, registered” is therefore not yet true.

The labelers are then asked to label under K1–K3 (`agentic-salience-draft.md:48-51`). Under a literal reading, K2 membership is defined by the regex being evaluated, so the labels test whether humans imitate the regex. Under a semantic reading, the gold is “information needed later,” but K1–K3 neither defines that temporal counterfactual nor covers tool outputs. The protocol must choose one object. Recall/precision against a gold defined by the candidate itself cannot validate downstream salience.

### Agentic-salience#5 — MEDIUM — the 150-label gate has unregistered sampling and weak uncertainty

Positive features are the one-shot rule, independent labels, tie-break, pre-score hash, and “failure blocks Leg A” (`agentic-salience-draft.md:43-52`). They prevent an iterative rescue on the new scores.

They do not make the proposed gate adequate:

- no exact sentence enumerator/order, PRNG algorithm, duplicate policy, or cap per task family is registered;
- the actual 704-case question population contains 2,777 user messages and zero system messages, so “user/system sentences” does not test K1 schemas;
- 25/50/25/50 overweights `missing_params` and `long_context` two-fold relative to the balanced population, but no weighting or per-stratum gate is specified;
- no minimum RETAIN or DROP denominator is fixed, so recall or precision can be unstable or undefined;
- the thresholds gate point estimates while Wilson lower bounds are only reported. Even with the unrealistically favorable denominator 150, the smallest raw recall pass is 128/150 = 0.8533 with Wilson lower bound **0.7879**, and the smallest raw precision pass is 105/150 = 0.7000 with lower bound **0.6224**.

If selective K2 were retained, the sampler, label manual, minimum class counts, stratum estimand, and whether point estimates or Wilson bounds govern must all be verbatim registration. Under the recommended minimal policy, delete this gate rather than repair it.

### Agentic-salience#6 — MEDIUM — a positive minimal result supports a role policy, not a complete salience mechanism

The publish gate asks for automatic benefit on a long-context/long-horizon/agentic benchmark (`LEDGER-PLAN.md:406-412`). An all-prior-user rule is automatic and BFCL is agentic, so a prospective win can meet that literal benchmark requirement. But because 82.8448% of the recomputed evicted mass is tool output, a tool/assistant control is active and often causally useful, not inert noise. `ledger - control` would estimate **which role source is more useful to retain/re-inject under this BFCL workload**. It would not establish a general ontology of salience, and non-evicted gains remain re-injection/recency rather than retention.

That narrower test is preferable to a seven-class regex whose validity gate is leaky and circular. The model card must say “automatic role-based user-history retention/re-injection on BFCL,” report the actual-eviction stratum, and retain the existing “retention/re-injection, not amplification” qualification (`LEDGER-PLAN.md:407-412,421-436`).

## Answers to the brief

### 1. Diagnosis and BFCL semantics

Diagnosis: **yes**, with the numeric logit correction above. Salience2 explicitly targets clauses constraining the model's future output and is a cue-logistic classifier with hand floors (`src/stencil/salience2.py:2-27,474-508`). Its own known-miss list includes task-like constructions and world-knowledge-only cues (`src/stencil/salience2.py:57-64`). BFCL user text is instead a sequence of executable requests, partial specifications, and anaphoric follow-ups.

K1–K3 as the complete retained object: **no**. BFCL later turns need prior user values and intents, simulator/tool-returned IDs and observations, and knowledge of prior generated actions/state. The checker compares cumulative simulator state and cumulative execution results, not instruction-sentence retention. K3 can still matter for a general agent, but BFCL does not validate it.

### 2. Selective versus minimal

Choose the **minimal role policy** for the next draft. It has no learned or hand-written semantic boundary, no label gate, and no claim that a regex knows which parts of a task will matter later. Keep all completed prior user turns; keep current schemas; compare against the same schema retention plus an equal budget drawn prospectively from completed tool/assistant content.

The control is deliberately hard: tool outputs dominate evicted mass and may carry the exact later-needed identifier. It measures user/schema prioritization versus execution-trace prioritization. A win is meaningful but narrow; a loss is also meaningful and should block a user-only BFCL claim. A token-matched user control under the all-user alternative is not a control at all. In the current code it already pins every prior-user token on all 115 eligible replayed dev contexts.

### 3. Label protocol and leakage

As written: **not adequate**. The one-shot/block rule is prospectively honest, but task-family recurrence, exact text recurrence, circular gold, unspecified sampling, unequal-stratum estimand, and unfixed class denominators defeat the intended untouched validation. The dev slice and the 100 labels may be openly declared development evidence, but they cannot also recur in the acceptance population. Under the minimal choice, remove the new label protocol entirely.

### 4. Smallest implementation

For the minimal policy, no change to `src/stencil/salience2.py` is needed.

1. `scripts/bfcl_mt.py`
   - Replace `_focus_entries` with a role-aware extractor returning: all current schema spans, all completed user-message spans strictly before the current turn, and all completed assistant/tool content spans strictly before the current turn.
   - Pass an explicit current-turn boundary into `arm_context`; do not infer it from `messages[:-1]`.
   - Rewrite `arm_context` so schema pins are common to ledger/control, user versus tool/assistant pin cardinality is exact, and echo added-token cardinality is exact.
   - Replace `finder_recall` with a CPU structural preflight reporting schema/user coverage, candidate/control pin counts, echo counts, source-role purity, special-token exclusion, and construction failures.
   - Record policy version, exact source sets, seeds, tokenizer hash, K, per-generation budgets, and actual removed-token role counts in artifacts.
2. `src/stencil/bfcl.py`
   - Replace or supplement `control_echo` with an ID-level, source-agnostic deterministic control builder. String decode/re-encode cannot be the equality mechanism because it is already non-total.
3. `tests/test_bfcl.py`
   - Add real-Qwen-tokenizer regressions for the two reproduced failures, temporal-domain exclusion after within-turn tool steps, full schema/user coverage, exact ledger/control pin cardinality, exact echo-token cardinality, role purity, special-token exclusion, and deterministic hash selection. Retain the existing toy unit but do not treat it as the real-tokenizer proof.

The minimum targeted CPU command is:

```bash
CUDA_VISIBLE_DEVICES='' uv run pytest -q tests/test_bfcl.py
```

No finder weights, K2 labels, or new salience module belong in this implementation.

### 5. K2 regex deep-check

The draft names these literal families but does not define any of them sufficiently to compile:

| family | boundary questions and BFCL false-positive risk |
|---|---|
| quoted string | Straight/curly, single/double, balanced/unbalanced, and maximum length must be fixed. A naive single-quote regex fires on contractions and possessives (`I'm`, `let's`, `that's`). |
| structured identifier | The grammar for underscore/hyphen/alphanumeric IDs must be fixed. Broad mixed-alphanumeric matching catches ordinary product/version tokens; narrow matching misses bare numeric IDs and credentials. |
| order/ticket ID | A bare integer is indistinguishable from an amount/date without a registered contextual prefix such as `order`, `ticket`, `id`, or `#`. Context matching can select descriptive prose mentioning an ID field rather than a supplied value. |
| number plus unit | The unit lexicon, pluralization, spacing, signs, decimals, and ranges must be fixed. Counts in narrative prose and ordinals can select non-parameters; units omitted in follow-ups are missed. |
| currency amount | Symbols and ISO codes must be separated from tickers. `$250` is money; `$MSFT` is not. Currency words in prose can be non-parameters. |
| date | ISO, month-name, slash, comma, and relative dates need an explicit grammar. Slash dates are ambiguous; versions/ratios can match numeric forms; `next week` and `this Sunday` are parameters but not literals under a strict rule. |
| time | AM/PM, 24-hour, seconds, and timezone forms need boundaries. Ratios and colon prose can look time-like. |
| file path / filename | POSIX, Windows, bare filename, allowed extensions, spaces, and trailing punctuation must be defined. A naive `word.word` pattern catches abbreviations, decimals, domains, and sentence-final punctuation. |
| ticker | Require a separate `$[A-Z]{1,5}`-style class if that is intended. It conflicts with currency symbols and misses unprefixed symbols/airport/currency codes. |
| email / URL | Scheme-less URLs, ports, fragments, Unicode domains, `@mentions`, and trailing punctuation require explicit handling. Broad `@` matching conflates handles with email. |
| postal address | This cannot be made language-general with one honest regex. Number-plus-capitalized-words overmatches dates/counts; a street-suffix lexicon is locale-specific and will miss many valid addresses. |

Important semantic misses remain even if every family is implemented perfectly: unquoted named entities, enum choices, natural-language requested content, ordinals such as “the first one,” anaphora such as “that order,” and values existing only in tool output. Adding patterns for examples observed in the viewed labels would be prohibited tuning, not a principled repair.

If K2 is ever revived, register the literal pattern strings verbatim and expose matches with `(class, start, end)` provenance. Add a synthetic-only CPU table before inspecting any held-out draw:

- one positive and at least two near-negative cases for every family;
- contractions/possessives versus single quotes;
- `$250` versus `$MSFT`;
- `v1.3`, `3.14`, `example.com`, `report.txt.`, `09/10/2024`, and Windows/POSIX paths;
- unbalanced/nested quotes and long adversarial punctuation strings;
- deterministic spans, no special-token matches, and no overlapping duplicate output;
- an integration conversation proving that a K2 hit retains the whole registered sentence and still excludes the current user turn.

The test must use no BFCL viewed-label text and run as:

```bash
CUDA_VISIBLE_DEVICES='' uv run pytest -q tests/test_parameter_literals.py
```

No such test can validate the present draft because there are no pattern strings to test.

## Exact registration text required

Do not append `agentic-salience-draft.md` as written. Replace its sections “What focus must retain,” “Proposed selection rule,” “Minimal alternative,” and “New held-out label protocol” with the following text, and delete the K2 label draw entirely:

> ## BFCL Leg A finder disposition and automatic role policy (prospective)
> The registered 100-item finder preflight is FAILED at 78/100 (77/77 auto-admitted schemas; 1/23 user sentences). Those 100 viewed items are development evidence only and are never reused for tuning or acceptance. No threshold is retroactively changed.
>
> BFCL Leg A does not claim a complete ontology of long-horizon salience. BFCL's checker is stateful and later turns may require prior user intent, prior generated calls, simulator state, and values returned only by tools. This leg tests the smaller automatic policy “retain/re-inject completed prior user turns while retaining current tool schemas.” A positive result supports automatic role-based user-history retention/re-injection on BFCL; it does not establish selective sentence salience or general tool-state memory.
>
> At each generation, let `P` be the rendered prompt before ledger echo; `S` be every token column whose offset overlaps a currently available tool-schema JSON object; `U` be every content-token column of user messages in completed turns strictly before the current turn; and `R` be every non-special content-token column of assistant and tool messages in completed turns strictly before the current turn. Current-turn user, assistant, and tool content and all chat/control-marker columns are excluded from `U` and `R`. The turn boundary is passed explicitly by the runner and is invariant across within-turn tool steps.
>
> Arms remain `base | ledger | control`. `base` is unchanged. `ledger` pins `S union U` and appends all completed prior user messages in chronological order under the existing ledger template. `control` pins `S` plus exactly `|U|` distinct columns from `R` and appends exactly the same number of token IDs as the ledger echo body, drawn from `R`. Thus schemas are common to ledger/control, incremental pin cardinality is identical, and echo cardinality is identical. The control is an active prior-execution-trace control, not an inert sham.
>
> Control selection is version-independent and deterministic: rank each eligible `R` column by `sha256("20260902\0" + case_id + "\0" + turn_index + "\0" + step_index + "\0" + column_index)` and use the lowest-ranked distinct columns for pinning; cycle through that same ranked list for the control echo body. Echo insertion is performed at token-ID level immediately before the current user's closing `<|im_end|>`, using the same fixed header/separator token IDs in ledger and control; equality is asserted on added ID count, not decode/re-encode length. No selected body ID may be a chat/control special token.
>
> Construction invariants are prospective blockers: when `U` is nonempty, `R` must be nonempty; for every generation whose `P` exceeds `K=8192`, `|R| >= |U|` and `|S union U| <= K-1` must hold. Any invariant failure in dev blocks the sealed run. Any invariant failure in the one-shot sealed run blocks Leg A rather than changing the source pool, budget, or fallback. Per generation the artifact records `|S|`, `|U|`, `|R|`, both pin counts, both echo counts, source-role counts, prompt length, eviction occurrence, and removed-token role counts.
>
> The BFCL finder-label preflight is retired after its recorded failure; the role policy has no learned or regex finder and therefore no replacement recall/precision gate. CPU preflight requires exact schema coverage, exact completed-prior-user coverage, ledger/control pin-count equality, ledger/control echo-count equality, source-role purity, special-token exclusion, deterministic replay, and zero construction failures on the full 32-case dev slice. Base competence, BASE-vs-BASE determinism, trunk/chat-template blockers, sealed cohort, primary paired lower bound, Holm correction, ROUND 7 safety, and echo-copy exclusion remain unchanged.
>
> Reporting is mandatory by BFCL category and by whether native eviction occurred. Any gain where native eviction did not occur is described as re-injection/recency. Because tool/assistant content can itself be necessary, `ledger - control` estimates a BFCL role-retention policy contrast. The result is never described as proof that tool/assistant history is irrelevant or that K1–K3 is a complete agentic-memory object.

Also replace `LEDGER-PLAN.md:432-434` (“finder recall >= 0.80 ...”) with the CPU structural preflight paragraph above, and replace `LEDGER-PLAN.md:424-426`'s control description with “active prior-execution-trace control, schema-common and exactly matched in incremental pin and echo token counts.” The final code hashes and the exact token-ID special-token set must be appended to the registration before any dev model preflight.

## VERDICT

**REWORK** — specifically, re-draft toward the minimal role-based policy above. Do not adopt the selective K2 repair, do not draw the 150 labels, and do not spend a BFCL GPU preflight or sealed outcome until the role domains, budgets, token-ID control, and structural blockers are implemented and registered verbatim.
