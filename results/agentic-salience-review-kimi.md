# Agentic-salience draft review — kimi-k3 (2026-09-02)

# results/agentic-salience-review-kimi.md

Cross-model review, kimi-k3. Read-only; no processes touched; no files written anywhere else. All material cited is from the pasted draft, registered PUBLISH GATE / PUBLISH-GATE BENCHMARKS text, WORKLOG.md:2371-2381, the 23 viewed `instruction_sentence` labels, `scripts/bfcl_mt.py` (`finder_recall`, control construction excerpt), and the `multi_turn_long_context_0` case excerpt. Line numbers beyond WORKLOG are section-level because the pasted sources are unnumbered.

---

## Q1 — Is the diagnosis right, and is K1–K3 the right object?

**F1 — Diagnosis confirmed. Grade: low (no defect).**
The evidence is internally consistent: `finder_recall()` scores 78/100 = 0.78 with the by-kind decomposition 77/77 (tool_schema, auto-hit via the `hit = True` branch in `scripts/bfcl_mt.py::finder_recall`) and 1/23 (instruction_sentence). The 22 misses reportedly sit at z ∈ [−8.4, −4.4] — *confident* rejection, which is the signature of a train/test object mismatch, not borderline calibration. The 23 viewed misses split into exactly the two phenomenological classes the draft names: parameterized task requests (`card_2108`/`abc123xyz`/`December 15, 2024` — miss_param_184; `$MSFT`/`100-share` — long_context_109) and narrative context (`I'm going to San Francisco.` — miss_param_85; `an unexpected hiccup arose` — long_context_197). salience2 was trained on the Multi-IF/IFEval object (persistent formatting constraints); BFCL user sentences do not look like that object. Diagnosis stands.

**F2 — K1–K3 covers only half of what BFCL's checker actually needs. Grade: medium.**
BFCL V3 multi-turn checker semantics (per WORKLOG.md:2378, open question (2), and the vendored `multi_turn_checker.py`): scoring runs on **cumulative conversation prefixes**; per-turn ground truth is a sequence of expected calls *with literal argument values* against cumulative file-system/API state. What later turns therefore need from earlier turns:
- **(a) Literal parameters from earlier user turns** — covered by K2. Confirmed in `multi_turn_long_context_0`: turn 3's `sort` requires `final_report.pdf` in `temp`, both quoted literals from turn 1 ("Move 'final_report.pdf' ... to 'temp' directory"). `path` shows `mv` before `sort`/`diff` — the arguments must survive to be re-emitted.
- **(b) State produced by tools/assistant calls** — *not covered*. The long_context_118 sequence ("my watchlist" → "the first one" → "my latest order") needs watchlist contents and order ids that exist **only in tool outputs**. The draft explicitly excludes tool/assistant content ("they are the material eviction removes... disclosed, not gated"), and the registered K=8192 eviction (`scripts/bfcl_mt.py`, `K = 8192`) removes exactly that mass first.

Consequence: if Leg A fails, it may fail on the (b) axis no finder operating on user sentences can fix; if it passes, the pass is confined to user-parameter retention. This is acceptable *for this leg's estimand* (paired ledger−control with equal context isolates the user-span choice), but the scope limit must travel into the registration verbatim — see T7. The draft discloses it in prose; disclosure is not currently part of the registered object.

**F3 — K1 is bookkeeping. Grade: low.** Schemas are already admitted unconditionally (`hit=True` branch). Keeping K1 in the label rubric is fine; do not let it re-enter the acceptance test (F6).

---

## Q2 — Selective rule vs minimal alternative

**F4 — The minimal rule structurally collapses the registered control. Grade: high (if adopted); resolves to: adopt selective.**
The registered control is "random-span control (token-matched echo from prior user turns, same template, same pin budget)" (PUBLISH-GATE BENCHMARKS, arms sentence; `control_echo` in `stencil/bfcl.py`). If ledger = "schemas + all prior user turns," then on BFCL — where user turns are short and tool outputs/schemas dominate the 8192 context — the token-matched control drawn *from user turns* is a near-duplicate of the ledger echo. The primary estimand, paired-by-episode LB(ledger − control) > 0 at one-sided α = 0.025, becomes ~0 by construction, and the registered falsifier "ledger beats base but not control" becomes *structurally likely to fire*. The draft's proposed remedy — re-register the control from tool/assistant spans — is a change to a **registered control made after the dev preflight outcome (0.78 < 0.80, WORKLOG.md:2380) was viewed**, breaking the gate's precondition "(all) registered before outcomes are viewed" (PUBLISH GATE, sentence 1). That is the over-reach, not the regex family.

What a user-turn control measures under eviction dominated by tool outputs: the marginal value of echoing *the chosen* user tokens vs *random* user tokens. That is exactly the H1′ thesis (the right span, retained) and it stays identifiable only while selectivity is meaningfully below 100%. The minimal rule would silently redefine the experiment from "span choice matters" to "any user echo suffices."

**F5 — The 0.60 selectivity clause is the correct guard; strengthen reporting. Grade: medium.** Register it verbatim (T9), and require the full per-case selectivity distribution (median/IQR), not only a per-case fraction — a few literal-dense long_context cases can hide a mean near 0.6 while most cases are at 0.9.

**Answer: selective.** It is the honest, non-over-engineered choice: zero changes to registered arms/control/budgets (K=8192, pin budget, echo budget unchanged per draft), one frozen regex block, one frozen union predicate. The minimal rule is the one with hidden specification cost.

---

## Q3 — Is the new label protocol adequate and prospectively honest?

Population arithmetic recomputed: 4 files × 200 rows = 800 cases (WORKLOG:2373); 800 − 32 dev − 64 sealed = **704** ✓. Strata 25+50+25+50 = 150 ✓. Draw seed 20260903 ≠ cohort seed 20260902 ✓. Hash-before-score ordering (draw → sha256 commit → blind labels → label-file sha256 commit → score once) is correct in structure.

**F6 — Schema spans must be excluded from the 150. Grade: high.** The old 100-label file was 77/23 schemas/sentences, and schemas auto-hit (`hit=True`). That made the failed 0.80 floor 0.77 *vacuously* padded — the binding constraint was really ~1/23 ≈ 0.043 of slack. Any schema item admitted into the new 150 re-introduces the same gaming vector against the 0.85 recall floor. The population sentence ("user/system sentences") is ambiguous on this. Fix in T2.

**F7 — Floor semantics are ambiguous: point estimate vs Wilson LB. Grade: medium.** Recomputed at n=150:
- Point-estimate gate: recall needs ≥ **128/150** (128/150 = 0.8533 ≥ 0.85; 127/150 = 0.8467 fails).
- If the Wilson 95% LB must clear 0.85: needs ≥ **137/150** (LB(136/150) ≈ 0.8494 < 0.85; LB(137/150) ≈ 0.8574 ≥ 0.85).
The draft ("recall ≥ 0.85 AND precision ≥ 0.70, Wilson 95% lower bounds reported") does not say which binds. That is a post hoc wiggle worth ±9 labels. Fix in T1.

**F8 — Rubric/rule circularity is acceptable but must be named. Grade: medium.** Labellers annotate RETAIN/DROP *under the K1–K3 definition* while the mechanism is the K2 regex union; the floors then measure fidelity of the regex to human literal-spotting, not whether the sentence is genuinely needed by a later checker state. That is fine as a *pre-registered fidelity test* — but the registration should say so, or a future reader will cite 0.85 as evidence of downstream utility. Fix in T8 wording.

**F9 — Provenance of the viewed 100 vs the sealed 64. Grade: medium.** The 100-span labels were drawn with seed 20260902, the *same* seed family as the cohorts (WORKLOG:2374). Case ids among the 23 viewed misses include miss_param_184, miss_func_181, long_context_197, long_context_118 — indices up to 197, i.e., drawn across all 200 rows/category, with no stated exclusion of the sealed 64. The regex family in the draft conspicuously enumerates the literal types visible in those 23 (card ids, `abc123xyz`, passport number, `.txt` files, `$MSFT`, `30.0 psi`, street addresses). If any viewed label came from a sealed case, the mechanism was partially designed on sealed content (sentence-level, not outcome-level — a real but bounded leak). Require a committed split-membership statement (T4). The new 150 explicitly excludes the 96 cohort cases, which closes the forward path.

**F10 — "One shot" contradicts "no second repair round without a new draw." Grade: medium.** As written, serial re-draws are permitted, nullifying the multiplicity protection. Fix in T5: failure is reported and any re-attempt is a *new registration* with prior failures named — not silent iteration.

**F11 — Missing reporting requirements. Grade: low.** Add: Cohen's κ between labellers, RETAIN prevalence, and per-category recall/precision. Recomputed: at n=25 per-cell (base and missing_functions strata), the Wilson half-width at p̂=0.85 is ≈ **±0.14** — per-category numbers will be noisy; report them anyway so F12's gap is visible.

**F12 — No freeze/no-dev-tuning clause. Grade: medium.** The draw-then-hash ordering protects the 150, but nothing forbids iterating the regex on dev-slice sentences or the viewed 100 before "freezing." Register freeze-before-any-measurement (T3).

Net: the protocol is prospectively honest *in architecture*; it needs T1–T6 to be watertight.

---

## Q4 — Smallest implementation and verbatim registration

**Implementation (all CPU, no GPU, no model processes; consistent with the HARD RULES):**
1. `src/stencil/salience2.py`: add a module-level `LITERAL_PATTERNS: tuple[tuple[str, re.Pattern], ...]` (frozen, hashable block) and `has_parameter_literal(text: str) -> bool`. No changes to `extract_instructions` / `LinguisticModel`.
2. Ledger-arm span predicate (the point where user spans are chosen for echo/pin; today it is the `else: hit = bool(extract_instructions(...))` branch pattern in `scripts/bfcl_mt.py::finder_recall` and its counterpart in the arm path): `select(s) = extract_instructions(s, held-out) or has_parameter_literal(s)`. One predicate change.
3. `finder_recall` (or `scripts/finder_labels_v2.py`): extend to compute recall **and** precision on RETAIN + Wilson 95% LB, reading the hashed v2 label file. CPU-only (note: `DEFAULT_BACKEND`/`LinguisticModel` load must stay a CPU weight-blob load; no CUDA path).
4. `stencil/bfcl.py::summarize_records`: add per-case `selected_user_tokens / total_user_tokens` (selectivity), emitted into the record JSON.
5. `tests/test_literal_regex.py` (new, CPU, table-driven — see Q5) plus one selectivity unit test on a synthetic record.
Overflow rule (low-grade finding): when selected tokens exceed the pin/echo budget, register the trim order (e.g., salience-ranked first, then literal order) — currently unregistered.

**Register verbatim in LEDGER-PLAN.md:** the K1–K3 definition **including the tool-output and bare-named-entity scope limits** (T7); the union predicate formula; the regex block *as text* plus its sha256; the freeze clause (T3); floors-with-point-estimate semantics (T1); the 150-draw protocol with T2/T4/T5/T6 amendments (population, segmentation, seed 20260903, strata 25/50/25/50, labeller blinding and order, one-shot semantics, κ/prevalence/per-category reporting); the unchanged-control sentence quoted from PUBLISH-GATE BENCHMARKS; the selectivity clause (T9); and explicit retirement of the old preflight line "finder recall ≥ 0.80 on 100 labelled BFCL instruction/schema spans" (else two floors coexist and can be cited selectively).

---

## Q5 — Regex family deep-check (K2)

Literal classes in the draft: quoted strings; identifier tokens (`card_2108`, `abc123xyz`); number-with-unit-or-currency; date/time; path/filename-with-extension; ticker (`$MSFT`); email/URL/address.

**False-positive risks in BFCL prose:**
- **Filename/path class** matching decimals: `30.0 psi` must match *number+unit*, not file `30.0` — require ≥1 letter in the extension and ≥1 letter/underscore in the stem. Similarly guard `e.g.`, `v1.3`, `0.80`.
- **Identifier class** matching versions/plain numbers: require (letter ∧ digit) or an underscore in the token — excludes bare `8192`, `2024`, `83214`; catches `abc123xyz`, `card_2108`, `Kj8#mP9$vL2`-style tokens (quoted anyway).
- **`$` disambiguation:** `$\d` = currency, `$[A-Z]+` = ticker (`$MSFT`); otherwise `$100` becomes a ticker FP.
- **Address class is the weakest.** "456 Oakwood Avenue, Rivermist, 83214" needs a street-suffix list {Avenue, Street, St., Road, Rd., Lane, Drive, Boulevard} + leading house number; a looser pattern will FP on any "at 456 …" prose. Keep it narrow or drop it (the `30.0 psi` literal retains that sentence anyway at sentence-level union).
- **Quoted strings:** in BFCL user prose, quotes are almost always parameters (grep pattern `'budget analysis'`, message body `'Hi Sam, …'`, `'Critical Order Assistance'`, `'annual_report.txt'`). Low FP. Keep.
- **Dates:** patterns must cover `December 15, 2024`, `June 15th 2024`, and the odd `this Sunday 09/10, 2024` (MM/DD + comma-year). Low FP.

**Recall gaps that are by design and must be disclosed (grade: medium):** unquoted proper nouns (`San Francisco` — miss_param_85; `Los Angeles` — miss_func_151; `Lara Croft` appears unquoted), airport codes (`JFK`, `LAX` — a 2–4-letter all-caps class would FP on prose acronyms; reject), relative dates (`next week`), ordinals/indices (`the first one`, `latest order`). Sentence-level union saves most cases — miss_func_171's `card_8283` retains the whole JFK→Beijing sentence — but the *only-parameter-is-a-bare-name* sentences are dropped. On the 23 viewed misses, the union rule would have flipped roughly 13/23 to RETAIN; the residual drops are concentrated in missing_params — which is why T6's per-category recall is mandatory.

**CPU test:** `tests/test_literal_regex.py`, parametrized, runnable as
`CUDA_VISIBLE_DEVICES='' uv run pytest -q tests/test_literal_regex.py`
Positives: `card 'card_2108'`, token `abc123xyz`, `$MSFT`, `June 15th 2024`, `December 15, 2024`, `09/10, 2024`, `'annual_report.txt'`, `'Hi Sam, my travel plans have changed.'`, `user@example.com`, `https://example.com/x`, `30.0 psi` (unit class, **assert not** filename class), `456 Oakwood Avenue` (if narrowed address class retained). Negatives expected to *not match* — locked as documentation of the disclosed gap: `I'm going to San Francisco.`, `During this adventure, an unexpected hiccup arose.`, `Could you tell me the details of my latest order?`. FP guards: `$100` → currency not ticker; `0.80 floor`, `v1.3`, `8192` → no match. Pure-regex module import only; the LinguisticModel weight load is not needed for this test.

---

## VERDICT

**VERDICT: ADOPT-SELECTIVE** — the minimal alternative is rejected (F4: it collapses the registered control and would force a post-hoc control redefinition after outcomes were viewed). Adoption is conditional on the following exact text changes, in this order, before the draft is appended to LEDGER-PLAN.md:

- **T1 (floors):** Replace the floor sentence with: "The floors bind the **point estimates**: recall ≥ 0.85 AND precision ≥ 0.70 on RETAIN at n=150 (recall requires ≥128/150). Wilson 95% lower bounds are reported for transparency and do not bind."
- **T2 (draw):** Append to the population bullet: "Items are user/system **sentences only**; tool-schema spans are excluded (K1 auto-admission is not retested — the old 77/77 auto-hits make any schema inclusion a recall-padding vector). Sentence segmentation is the finder's own segmenter, registered by hash."
- **T3 (freeze):** Add: "The K2 regex block (registered verbatim + sha256), thresholds, and the union predicate are frozen and committed BEFORE (a) the 150-draw and (b) any selectivity measurement on dev-slice sentences. No tuning on the dev slice or on the viewed 100 labels."
- **T4 (provenance):** Commit a split-membership statement for the 100 viewed labels (which of dev/sealed/non-cohort each case-id belongs to; required overlap with sealed 64: **zero**) and restate that the 150 are drawn exclusively from the 704 non-cohort cases.
- **T5 (one shot):** Replace "Fail → Leg A is BLOCKED …, no second repair round without a new draw" with: "Fail → Leg A is BLOCKED. The failed measurement is reported; any repair re-attempt is a new registration with its own draw and hashes, and all failed attempts are named in the model card. No silent iteration."
- **T6 (reporting):** Add required reports: Cohen's κ, RETAIN prevalence, per-category recall/precision with Wilson intervals (25-item cells carry ≈ ±0.14 half-widths — reported, not hidden), and the dev selectivity distribution (median/IQR).
- **T7 (scope):** Register the K1–K3 definition *with* its limits verbatim: "Tool/assistant content is not retained; later-turn referents existing only in tool outputs are outside this mechanism. Unquoted named entities (cities, personal names), airport codes, relative dates, and ordinal/index references are outside K2; per-category recall makes the cost visible."
- **T8 (construct honesty):** State: "The floors measure fidelity of the finder to the registered K1–K3 object (human vs regex literal-spotting), not downstream checker utility; Leg A itself is the utility test."
- **T9 (selectivity guard):** Register the 0.60 clause verbatim, plus the per-case distribution report and the budget-overflow trim order.
- **T10 (old floor):** Explicitly retire "finder recall ≥ 0.80 on 100 labelled BFCL instruction/schema spans" in PUBLISH-GATE BENCHMARKS as superseded, so no dual floor remains citable, and record the reviewers' rejection of the minimal alternative with the F4 rationale.

Required implementation surface (smallest): `src/stencil/salience2.py` (`LITERAL_PATTERNS` + `has_parameter_literal`), the single union-predicate change at the user-span selection point, the v2 `finder_recall` scorer (recall+precision+Wilson, CPU), selectivity in `summarize_records`, and `tests/test_literal_regex.py`. No GPU or model process is needed for any of it.