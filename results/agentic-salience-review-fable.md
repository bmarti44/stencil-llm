# Review: AGENTIC SALIENCE draft registration — fable, 2026-09-02

Scope: the draft at scratchpad/agentic-salience-draft.md, against LEDGER-PLAN.md:406-436 (PUBLISH GATE, PUBLISH-GATE
BENCHMARKS), WORKLOG.md:2371-2381, results/h1p-review-sol.md:173-183, data/bench/bfcl_v3_mt/finder_labels.json,
scripts/bfcl_mt.py, src/stencil/bfcl.py, src/stencil/salience2.py. CPU-only replays (tokenizer + vendored BFCL
executors + salience2 linguistic backend; no model, no GPU). Sealed-cohort case contents were never opened: every
population statistic below is over the 704 cases NOT in cohorts.json (dev 32 + sealed 64 excluded). Scripts:
scratchpad/fable/{analysis,tokens,evict,oracle}.py. No repo file other than this report was written.

## 0. Replays and recomputations (all numbers I rely on)

R1. finder_recall replay (scripts/bfcl_mt.py:528-551 semantics): shipped weights 77/77 schema + 1/23 sentence = 0.78;
    Multi-IF-held-out weights (results/salience2/linguistic_heldout_no_multiif.json) identical, 78/100 = 0.78. Confirms
    WORKLOG.md:2380 and the draft. Note finder_labels.json contains NO system sentences (the question turns are all
    role=user, 3,180/3,180 messages); the label construction string "system/user sentence spans" is user-only in fact.
R2. Draft's "22 misses score z in [-8.4, -4.4]" does NOT reproduce with the held-out weights and max-over-clauses:
    the 22 misses span z = -8.5 .. -1.2 (sorted: -8.5,-7.0,-7.0,-6.2,-5.9,-5.8,-5.7,-5.5,-5.1,-5.0,-4.5,-4.5,-4.4,
    -4.3,-4.2,-3.7,-3.3,-3.3,-2.5,-2.2,-1.7,-1.2; the hit is +0.5 after the hand floor). Conclusion unchanged
    (confident rejection), the bracket is wrong. LOW.
R3. Token accounting on the 704 non-cohort cases, Qwen3 tokenizer, ground-truth trajectories executed through the
    vendored BFCL environments (tool outputs are the real ones; assistant turns approximated as the ground-truth
    calls rendered as <tool_call> JSON). Final-turn prompt composition (median tokens; share of all final-prompt
    tokens in the category):
      base:              schema 5,073 | user (all turns) 147 | prior-user 110 | tool outputs 144 | assistant 267 | total 5,881 (max 7,827)  shares: schema .90 user .03 tool .03 asst .05
      missing_params:    schema 5,304 | user 147 | prior-user 119 | tool 138 | asst 282 | total 5,947 (max 7,883)   shares: .89/.03/.03/.05
      missing_functions: schema 5,304 | user 160 | prior-user 125 | tool 143 | asst 293 | total 5,939 (max 7,862)   shares: .89/.03/.03/.05
      long_context:      schema 5,304 | user 145 | prior-user 100 | tool 2,811 | asst 274 | total 8,884 (max 72,528) shares: .33/.01/.63/.02
    Cases whose final prompt exceeds K = 8,192 (scripts/bfcl_mt.py:39): base 0/176, missing_params 0/176,
    missing_functions 0/176, long_context 97/176. Schema tokens exceed prior-user tokens in 704/704 cases.
R4. Eviction geometry (long_context, non-cohort, first generation step of each turn): 217/643 generations have a
    prompt > K (89 cases). generate() evicts from column 0 forward (scripts/bfcl_mt.py:300-311, 332-340) and the
    <tools> block is the FIRST thing in the prompt (render_prompt, :108-124). Fraction of schema tokens removed at
    overflowing generations: quantiles 0.03 / 0.20 / 0.41 / 1.00 / 1.00 (min/25/50/75/max); in 89/217 the overflow
    exceeds schema minus the pin budget, i.e. the schema is gone entirely.
R5. Pin budget: arm_context() sets budget = min(len(prior_user_columns), |ledger columns|) (scripts/bfcl_mt.py:266-275)
    and fills it with user entries FIRST, then schema entries (:276, _entry_columns :225-235). Since prior-user
    columns (~100-125) < schema columns (~5,000) in every case, at most ~100 schema tokens are ever pinned. "K1 tool
    schemas — already auto-admitted as schema spans" (draft) is therefore true of the finder and FALSE of the KV pin.
R6. Ground-truth argument literals in turns t >= 1 (4,535 literal occurrences after excluding 85 too-short strings;
    precedence current-user > earlier-user > earlier-tool > earlier-assistant): current user turn 1,918 (42%);
    earlier user turn 891 (20%), of which 781 are NOT in any earlier tool output; earlier tool output 752 (17%);
    earlier assistant call 116 (3%); not found verbatim anywhere 1,673 (37%; mostly composed content strings such as
    post_tweet(content=<file contents>) and file names the model must read from tool output). By category, the
    earlier-user-only share is largest in missing_functions (394; the held-out turn's user text is the fixed "I have
    updated some more functions" prompt, so the parameters live one turn back) and missing_params (224).
R7. Mechanical retention oracle (no labellers): a user sentence in turn t is RETAIN iff a later-turn ground-truth
    call uses a literal that is not present in that later turn's own user text and IS present in the sentence.
    Prevalence over 5,659 non-cohort user sentences: base 5.6%, missing_params 11.1%, missing_functions 17.6%,
    long_context 5.3% (565/5,659 = 10.0% overall). Against this oracle: K2 regex recall 0.811 / precision 0.214;
    held-out salience2 recall 0.065 / precision 0.128; union recall 0.819 / precision 0.206; "retain every user
    sentence" recall 1.000 / precision 0.100. Missed RETAIN sentences are dominated by bare proper nouns
    ("Zeta Corp", "San Francisco", "Rivermist", "Bob", "Omega Industries", "Quasar Ltd.") — no K2 class fires.
R8. K2 selectivity (my prototype of the draft's seven classes; see section 5) on the 704 non-cohort cases: selects
    37.8% of user sentences and 50.8% of user-turn tokens (per category 49.5-52.2%); union with held-out salience2
    39.7% / 52.5%; per-case token selectivity quantiles 0 / .22 / .33 / .52 / .70 / .83 / 1.0 (min/10/25/50/75/90/max),
    36.6% of cases above the draft's 0.60 "keep-all in disguise" line. Salience2 alone selects 5.1% of sentences.
R9. Wilson 95% lower bounds at the draft's floors: recall 0.85 with 15 / 30 / 60 RETAIN positives -> LB 0.62 / 0.70
    / 0.74; precision 0.70 with 60 / 90 selected -> LB 0.58 / 0.60. At the oracle prevalence (~10%), a 150-sentence
    draw contains ~15 RETAIN positives, so the recall floor is decided by 2 sentences.

## 1. Diagnosis and the K1-K3 object (Q1)

1.1 The diagnosis of WHY salience2 fails is right (MEDIUM confidence -> confirmed by R1/R2 and R7: salience2 hits 6.5%
    of oracle-RETAIN sentences). The persistent-constraint object and the BFCL parameter object are different things.
1.2 The claim that the 100-label set is "recall of all user sentences" is right (README: every sampled user sentence is
    a label). But the draft's replacement object (K1-K3) is only PARTLY right, and the evidence is in the checker:
    - BFCL V3 multi-turn scoring (vendor/.../multi_turn_checker.py:106-120, 162-221) is a per-turn STATE check on the
      environment instances plus a RESPONSE-SUBSET check (the model's execution results so far must contain the
      ground-truth results of the current turn). What a later turn needs is therefore: (a) the tool schemas (always;
      every turn issues calls), (b) parameters stated in earlier user turns that the current turn does not restate
      (R6: 20% of later-turn literals; 17% only there), (c) identifiers and content that exist ONLY in earlier tool
      outputs (R6: 17% + most of the 37% "composed" strings: file contents to tweet, ids returned by create/book,
      the "first file in the listing", "the stock I just looked at"), and (d) environment state the model must
      infer from its own earlier calls (cwd after cd). K1 covers (a); K2 covers (b) only for literal-bearing
      sentences and misses proper-noun parameters (R7); K3 (standing directives) is nearly empty on BFCL (5% of
      sentences fire, precision 0.13 against the oracle); (c) and (d) are explicitly "not retained" in the draft.
    - So "losing any of K1-K3 makes a later correct tool call impossible; nothing else in a user/system turn does" is
      half true (nothing else in a USER turn, modulo proper nouns) and misleading about where the long-horizon
      dependency actually lives: in long_context, 63% of the final prompt is tool output and the user turns are 1%.
      HIGH (the object definition excludes the dominant dependency, so a positive result would not mean what the
      publish gate says: "automatic long-horizon agentic benefit").
1.3 The premise "eviction (K=8192) mostly removes tool outputs" is FALSE under this harness (R3-R5). In three of four
    categories eviction never happens (max prompt 7.9k < 8,192), so the KV pin is a no-op and the ledger arm reduces
    to "re-append selected user sentences at the end of the last user message" — the full_echo - full diagnostic
    that H1' found to be noise (results/h1p-review-sol.md). In long_context the first thing evicted is the <tools>
    block, in all three arms, and the pin budget cannot protect it (R5). A ledger-vs-control contrast on long_context
    would be a contrast between two arms that have both lost part or all of their schemas. CRITICAL (harness, not
    the draft's text — but the draft asserts K1 is handled, so the registration must not proceed on that assertion).

## 2. Selective rule vs minimal rule (Q2)

2.1 Under the current harness neither rule tests retention in base/missing_*: nothing is evicted, so the only
    treatment is the echo. Under the minimal rule ("schemas + all prior user turns") the echo is the whole prior
    user text (~110 tokens) and the registered control (control_echo, src/stencil/bfcl.py:703-720) is a CYCLIC
    ROTATION of the same ~110 tokens to the same length: the control would be the ledger's own content re-ordered.
    The draft sees this. It also applies, less visibly, to the selective rule: at ~50% selectivity the control is a
    contiguous rotated window covering half of a ~110-token pool, which overlaps the selected sentences roughly
    half the time by construction. The random-span-from-user-turns control is weak for any rule on BFCL because the
    user-turn pool is tiny (R3). HIGH.
2.2 A token-matched random-span control drawn from TOOL/assistant turns would measure "user-stated parameters vs
    equal tokens of tool text re-injected" — a content control, which is the right comparison for the minimal rule.
    Caveats to register: at turn 1 of missing_params (turn 0 has no ground-truth call) and at every turn 0 the tool
    pool is empty -> the control must fall back to "no echo" (zero added tokens), matched by construction; and tool
    text in the echo can re-inject the very identifiers (c) the ledger arm omits, so the control could WIN for a
    legitimate reason. That is an informative result, not a bug, but it must be a registered possibility.
2.3 Honest choice. The selective rule buys ~50% token selectivity (R8) at the price of: a seven-class regex with its
    own preflight, a 0.21-precision / 0.81-recall relation to what later turns actually need (R7), a selectivity
    that crosses the draft's own 0.60 line in 37% of cases, and a control that is nearly its own content. The
    minimal rule is exactly what the numbers say the finder is on this benchmark ("prior user turns are 3% of the
    prompt; keep them all"), is zero-parameter, and its control is well-defined once redefined. The word the
    publish gate uses is "automatic", not "selective" (LEDGER-PLAN.md:406-412). Recommendation: ADOPT-MINIMAL for
    Leg A's user-turn treatment, with the control re-registered from tool/assistant turns BEFORE any run, and the
    selective rule kept only as a reported-not-gated coverage diagnostic (fraction of oracle-RETAIN sentences the
    regex would have kept) — no label protocol needed for that.
2.4 But neither rule is worth a GPU run until the harness issue in 1.3 is fixed, because the thing that makes the
    benchmark "long-horizon" (long_context; 55% of its cases overflow) is currently a schema-loss test.

## 3. Label protocol (Q3)

3.1 Circularity: the labellers are told to label RETAIN "under the K1-K3 definition", and K2 IS the regex definition.
    Two humans applying "does this sentence contain a quoted string / id / date / number-with-unit / path / ticker
    / contact" will agree with the regex whenever they agree with each other; precision >= 0.70 is then a test of
    regex hygiene, not of whether retention is what later turns need. Against the mechanical oracle (R7) the same
    regex has precision 0.21. HIGH.
3.2 Power: at the oracle prevalence ~10%, 150 sentences hold ~15 RETAIN; recall 0.85 = 13/15, and the Wilson LB at
    the floor is 0.62 (R9). If labellers instead mark ~40% RETAIN (the regex's own selection rate), the test has
    ~60 positives but is the circular test of 3.1. MEDIUM.
3.3 Leakage: (i) the 100 viewed labels are dev-cohort sentences and the new population excludes dev+sealed, so no
    direct reuse — good; (ii) but the regex family is to be prototyped on the 704 non-cohort cases (the brief asked
    me to, and I did: R8 samples from all 704), and the 150 labels are drawn FROM those 704 — the regex is in-sample
    to its own acceptance population. Fix: split the 704 once by seed into a regex-development half and a label half
    before any further regex work, or freeze the regex (hash) with this review's numbers as the disclosed in-sample
    baseline and draw only from the label half. Also register that the reviewers who prototype the regex (fable) do
    not label. MEDIUM. (iii) The stratification "25/50/25/50" over base/missing_params/missing_functions/long_context
    is unexplained; if intended to weight missing_* where earlier-user parameters matter (R6), say so.
3.4 Better protocol (prospective, labeller-free, no leakage surface): register the mechanical oracle of R7 as the
    retention ground truth — it is derived from the shipped ground-truth trajectories and the vendored executors,
    deterministic, and measures exactly "would dropping this sentence remove a literal a later ground-truth call
    needs". Keep human labelling, if at all, for a 50-sentence audit of the oracle's own precision (does a RETAIN
    sentence really carry the literal for the reason a human would say). The one-shot rule and the BLOCKED
    consequence are fine; the "no second repair round without a new draw" clause is good and should stay.

## 4. Smallest implementation and verbatim registration (Q4)

4.1 Harness fixes required before ANY BFCL arm is run (they change what all three arms see):
    a. scripts/bfcl_mt.py generate()/_eviction_end: treat the system+<tools> prefix as never-evictable in ALL arms
       (a fixed prefix sink: keep = [(0, end_of_tools_block)] + arm keep), so the pin budget covers user content
       only and eviction removes what the draft says it removes. Alternatively raise K so that no case overflows and
       drop the KV pin from Leg A entirely (then Leg A is an echo-only test and should be registered as such).
    b. arm_context(): with (a), budget = min(len(prior_columns), |user ledger columns|) without schema entries.
    c. Control: add control_echo_pool = tool+assistant message texts (messages[:-1] with role in {tool, assistant}),
       fall back to zero added tokens when the pool is empty (and record it); one new function in
       src/stencil/bfcl.py (control_echo already takes an arbitrary text list; the pool builder is ~10 lines) and
       one branch in arm_context(). tests/test_bfcl.py: add a case for the empty-pool fallback and for the prefix
       sink (prompt > K must keep every schema column).
    d. Minimal rule: _focus_entries() user_entries = one Entry per prior user message (whole message; provenance
       "prior_user_turn"); delete the extract_instructions call for Leg A (keep for Leg B). ~15 lines.
    e. Oracle preflight (replaces finder_recall for Leg A): a CPU function retention_oracle(case, answers) ->
       set of RETAIN sentences (R7 definition, ~40 lines in src/stencil/bfcl.py) and a preflight that reports the
       arm's coverage of oracle-RETAIN sentences on the dev slice (minimal rule: 1.0 by construction; reported).
       If the selective rule is adopted instead, add src/stencil/params.py with the frozen regex table and
       has_parameter_literal(), and gate on the oracle with floors chosen BEFORE seeing R7 — which is no longer
       possible for me, so the floors must come from a reviewer who has not read this section (sol/kimi).
4.2 Verbatim text to register (my required version; replaces the draft's "Proposed selection rule" and "New held-out
    label protocol" sections):

    LEG A FOCUS RULE (registered 2026-09-0X, before any BFCL arm runs). Ledger arm = tool schemas (system <tools>
    block, never evicted in any arm) + every prior user message verbatim (KV pin over the prior-user columns up to
    the registered budget; text echo of the same messages via ledger.text_ledger_context). No salience finder is
    applied on Leg A; salience2 stays Leg B only. Control arm = same pin budget over prior-user columns (unchanged)
    + token-matched echo drawn by control_echo from the concatenated prior TOOL and ASSISTANT message texts; when
    that pool is empty the control adds zero tokens and the case-turn is recorded control_pool_empty=true.
    Eviction: K = 8192 over the cache excluding the system+tools prefix, which is exempt in all three arms.
    Preflight (CPU, dev slice, reported not gated): fraction of oracle-RETAIN sentences (definition: a prior user
    sentence containing a literal used by a later ground-truth call and absent from that later turn's user text)
    covered by the ledger echo = 1.0 by construction; and per-category eviction incidence and evicted-token
    composition. The registered finder floor of 0.80 on the 100 viewed labels is recorded FAILED (78/100) and
    retired for Leg A; those labels are never reused. Falsifiers unchanged; additionally, if control beats ledger
    with LB > 0, the result is reported as "tool-text re-injection dominates user-turn re-injection" and Leg A
    counts as failed for the publish gate.

    If the orchestrator nevertheless keeps a selective rule, the additional verbatim text must include: the regex
    table by hash; the 704 -> 352/352 seed split with the regex frozen before the label half is touched; the oracle
    definition above as the ground truth; floors set by sol/kimi blind to R7; selectivity reported per case with
    the 0.60 disclosure rule.

## 5. K2 regex family deep-check (Q5)

5.1 Prototype (scratchpad/fable/analysis.py, K2 dict), one class per draft bullet:
    quoted      '...' / "..." / curly quotes (1-120 chars)                       fires on 1,347 sentences; sole class in 602
    ident       letters+digits >= 4 chars, or snake_case                           745; sole 143
    num_unit    currency prefix, or number + unit word (%, psi, shares, gallons, hours, ...)  361; sole 194
    date_time   ISO date, m/d(/y), month-name dates, hh:mm, am/pm, bare 20xx year  263; sole 60
    file_path   slash paths, or name.ext for ~35 extensions                        300; sole 19
    ticker      $TICK, or 2-5 uppercase letters minus a stop list                 387; sole 124
    contact     email, URL, street address, 5-digit / zip, phone                   56; sole 24
    Descriptive only, not tuning: this family fires on 10/23 of the viewed instruction labels; with the schema
    auto-admits that would read 87/100 against the OLD label set. Reported once; no iteration was done.
5.2 False-positive risks observed in BFCL prose (all real samples from the 704):
    - ticker: "START mode", "CWD", "ID", "AM" — uppercase common words; the stop list is ad hoc. Also airport codes
      (LAX, ORD, JFK, SVP) are parameters, so the class is needed but under-specified.
    - quoted: the tweet/message CONTENT strings ('I am on my way', 'Postponing my plans.') — these ARE parameters,
      but also any quoted narrative ("said 'Safety first!'" splits across sentences and the closing quote lands in
      the next sentence, which the segmenter then treats as a bare fragment and the regex misses).
    - num_unit: "convert 60 gallons" — a parameter; "2 to determine the base 10 logarithm" — split by the segmenter,
      the number lands without its unit and is missed; "x" as a unit fires on "5x".
    - date_time: bare "2024" fires on "in 2024 I ..."; "next week" / "this Sunday" are dates BFCL ground truth turns
      into literals (e.g. "09/10, 2024") and the words-only forms are missed.
    - contact: 5-digit ids (ticket 83912, order 12446) are caught by the zip pattern — correct outcome, wrong label;
      "12345-67890" access codes likewise.
    - Systematic MISS class (R7): capitalized proper nouns without digits — company names ("Zeta Corp", "Omega
      Industries", "Quasar Ltd."), places ("San Francisco", "Rivermist", "Silverpine"), people ("Bob", "Samuel
      Fisher"), and @handles/#hashtags ("@RoadsideAssistance", "#RoadTrip") — the most common earlier-user-only
      parameters in the trading/travel/messaging APIs. Adding a "Capitalized multiword / @handle / #tag" class
      would recover most of them and push selectivity well past 0.60.
5.3 CPU test to register (if the selective rule survives): tests/test_params.py with (i) one positive and one
    negative literal per class from synthetic sentences (no BFCL text), (ii) the frozen-table hash, (iii) a
    determinism check that has_parameter_literal is pure, and (iv) the oracle-coverage preflight run on the dev
    slice printing recall/precision against retention_oracle() without asserting a floor (floor comes from the
    registration).

## 6. Findings summary (severity)

F1 CRITICAL  Harness: <tools> block is evicted first and the pin budget cannot protect it (R4, R5); in base /
             missing_* nothing is ever evicted (R3). The draft's K1 claim and the "eviction removes tool outputs"
             premise both fail. scripts/bfcl_mt.py:266-276, :300-311, :332-340.
F2 HIGH      The K1-K3 object omits the dominant long-horizon dependency (tool-output identifiers/content: R6, R3),
             so a Leg A pass would not support "long-horizon agentic benefit" as worded at LEDGER-PLAN.md:406-412.
F3 HIGH      The registered user-turn random-span control is a rotation of a ~110-token pool and is near-identical
             to either rule's echo (R3, src/stencil/bfcl.py:703-720); must be re-registered from tool/assistant text.
F4 HIGH      Label protocol is circular with the regex definition; against a mechanical retention oracle the regex
             has precision 0.21 (R7); the human floor of 0.70 would test something else.
F5 MEDIUM    Regex prototyped on the same 704 cases the labels are drawn from; needs a seed split or a frozen hash
             plus disclosure (3.3). Power at ~15 positives is two sentences (R9).
F6 MEDIUM    Selective rule's selectivity is ~0.5 of user tokens and >0.60 in 37% of cases (R8); its incremental
             claim over "keep all prior user turns" is not there on this benchmark.
F7 LOW       Draft's z bracket [-8.4,-4.4] is wrong (R2); label construction says "system/user" but there are no
             system sentences (R1).

VERDICT: REWORK. Do not append the draft as written. Register the Leg A focus rule text in 4.2 (ADOPT-MINIMAL for
the user-turn treatment) only AFTER the harness fixes 4.1(a)-(c) are implemented with CPU tests and the mechanical
retention oracle 4.1(e) replaces the human label protocol; drop the K2 regex from the gate (keep it, if at all, as
a reported coverage diagnostic with the frozen table hashed and the 704 split by seed before any further look).
