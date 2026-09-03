# Review: LEG A (BFCL V3 multi-turn) registration DRAFT — fable, 2026-09-03

Scope: WORKLOG.md:2565-2607 (the draft), tools/codex-agents/bfcl-evict-v2.md (+ .allow), LEDGER-PLAN.md:406-440 (publish gate,
registered Leg A/B benchmarks) and :554-621 (LEG B + amendments 1-2), results/agentic-salience-review-fable.md,
results/harness-review-{sol,fable}.md, results/quick-checks/README.md items 25-27, scripts/bfcl_mt.py, src/stencil/bfcl.py,
src/stencil/selector_v2.py, src/stencil/ledger.py, src/stencil/qwen3.py:88-131, scripts/multiif_evict.py:120-402,
data/bench/bfcl_v3_mt/README.md + cohorts.json (ids only), data/classifier/LABELS.md. CPU only; no model, no GPU, no process
touched; the sealed cohort's case contents and data/bench/ifeval_input_data.jsonl were never opened. Measurements below are
over the 32-case DEV slice only (scratchpad devslice.py: ground-truth trajectories executed through the vendored BFCL
environments, assistant turns rendered as the ground-truth calls in <tool_call> JSON, Qwen3 tokenizer counts); the contact
screen (contact.py) is a repo-wide + cache name grep; the tokenizer check (trunc.py) used the bge encoder tokenizer only.

## 0. Recomputations and measurements (everything numeric I rely on)

M1. Dev-slice eviction geometry (K = 8192, protected prefix = system + <tools> block, trigger = prefix + history columns > K
    before the current user turn is prefilled): base 0/8 cases trigger (max prompt 7,133), missing_params 0/8 (max 6,590),
    missing_functions 0/8 (max 7,167), long_context 4/8 cases, 12/40 user turns. Prefix median 5,494 columns, so the evictable
    history must exceed ~2,700 columns to trigger. At the 12 triggering turns: evictable 1,780 / 1,941 / 2,158 / 3,376 / 4,045 /
    35,784 / 35,918 / 35,942 / 37,527 / 37,569 / 37,606 / 37,711 columns; prior-USER columns 24-308; TOOL columns 1,351-37,298
    (>= 76% of the evictable range in every triggering turn, >= 99% in the seven giant ones); assistant 21-286.
    B = 25% of evictable = 445 / 485 / 539 / 844 / 1,011 / 8,946 / 8,979 / 8,985 / 9,381 / 9,392 / 9,401 / 9,427 columns.
M2. Tool-output line statistics (192 dev tool messages, real executor outputs): EVERY message is a single line
    (BFCL executors return str(result) of a dict/list; newlines inside strings are repr-escaped). Message tokens quantiles
    1 / 12 / 22 / 44 / 81 / 31,665 (min / 25 / 50 / 75 / 90 / max); 15 messages exceed 512 tokens (all in long_context, the
    directory listings / file dumps). "Split tool output on newlines, cap 40 lines, longest first" is therefore a no-op: the
    candidate is the whole message.
M3. Registered scorer on tool lines: ClassifierScorer (src/stencil/selector_v2.py:44-51) encodes ("(no context)", "[role]
    text") with truncation="only_first", max_length=192, and the encoder's model_max_length is 512. With the bge tokenizer,
    a second segment of ~300 tokens RAISES `Truncation error: Sequence to truncate too short to respect the provided
    max_length` (the first segment is 5 tokens and cannot absorb the overflow). At least 15 dev tool messages (> 512 tokens)
    and several more in the 192-512 range will crash the registered scorer as written, or force the coder into an
    unregistered truncation choice.
M4. Full arm feasibility: two of eight dev long_context cases reach 41,185 and 43,967 prompt tokens, above Qwen3's
    max_position_embeddings 40,960 (1.7B and 4B). "full (no eviction; K unlimited)" is undefined for those cases; the
    proportion in the sealed 16 is unknown but the dev rate is 2/8.
M5. Power of the registered primary (long_context, 16 sealed cases, final all-or-nothing pass, cluster = case, continuity
    100/16 = 6.25 pts, t_{0.95,15} = 1.753, Holm's tightest step alpha/3 -> t_{0.9833,15} ~ 2.36). Per-case differences
    d in {-100, 0, +100}; with w net wins and no reversals: w=5 -> mean 31.25, sd 47.9, LB(0.05) = +4.0 but LB(0.0167) = -3.3;
    w=6 -> LB(0.0167) = +1.75. With one reversal (7 wins, 1 loss): LB(0.0167) = -5.3. So the first Holm step needs >= 6 of 16
    cases flipped from fail to pass with zero reversals; at the dev trigger rate only ~8 sealed long_context cases evict at
    all, and the 1.7B base rate on long_context is 2.5% (results/agentic-bench-synthesis.md:20). A1 and A3 on this primary
    are not tests; they are a registered null.
M6. Timeline (git): results/agentic-salience-review-fable.md (R6: 17% of later-turn literals live only in earlier TOOL
    output) committed 46d1424 2026-09-02 15:30; the classifier data spec with "Tool-output lines carrying identifiers the
    user later relies on are facts (role tool)" committed 6ce3506 2026-09-02 20:28; kimi's first pass with 947 tool-role
    rows 21:29. The tool-role fact label post-dates, by five hours, a BFCL population analysis that motivated it.
M7. Contact screen (26,249 files: tracked tree, results/, session scratchpads, memory, HF cache): ToolTalk 0 repo hits;
    CoSQL/SParC 0 (one false positive in an nltk tagger weights file); ConvFinQA 0; API-Bank 0. InfiniteBench, LongBench,
    MT-Eval, ToolSandbox, LongMemEval, LoCoMo, tau-bench appear in results/agentic-bench-*.md / research-*.md (design
    consideration = contact). HF hub cache holds datasets--Salesforce--APIGen-MT-5k (multi-turn function-calling data;
    never referenced by repo code, but present on the host — disclose, and exclude the APIGen family).
M8. Harness facts that bind the coder: render_prompt (scripts/bfcl_mt.py:108-146) wraps every tool response in an
    `<|im_start|>user ... <tool_response>` block, so scripts/multiif_evict.py's `rfind("<|im_start|>user\n")` split
    (run_arm :346-349) and `user_turns()` (:125-138) would treat tool responses as user turns: the "current user turn"
    at any step > 0 of a turn would be the last tool response, and role_pinned would pin tool text. The current harness
    re-renders and re-prefills the WHOLE prompt at every step of every turn (run_case :383-392) and evicts from column 0
    (generate :316-325). TEXT_LEDGER_HEADER is "Earlier user instructions restated verbatim:" (ledger.py:27).

## 1. Registration as an AGENTIC retention test (Q1)

1.1 Protected prefix + pre-query eviction: right, and the fix to my CRITICAL. Two things are unregistered:
    (a) when the trigger is evaluated and how often. With re-render-per-step (M8) the cache would be rebuilt at every tool
    step; the trigger (prefix + history > K) is evaluated at step 0 of turn t, but at step s > 0 the "history" now
    includes the current turn's own tool outputs and the split marker lands on a tool_response block. Register: ONE
    eviction decision per user turn, taken at step 0 with the split located by MESSAGE INDEX (the turn-t user message),
    and the KV cache PERSISTS across steps within the turn (assistant + tool-response tokens appended; never re-evicted).
    (b) what "exceeds K" means: register `prefix_columns + history_columns > K` measured before the current user message
    is prefilled; the current turn's tool outputs may push the cache past K within the turn (37k-column tool dumps, M1)
    and that is accepted and recorded, identical across arms. HIGH (a), MEDIUM (b).
1.2 "Arms on identical context ids per turn" is impossible under the harness as written and the draft does not say which
    of two designs it means. In run_case each arm generates its OWN trajectory (its calls -> its tool outputs), so from turn
    2 on the arms' histories diverge and nothing is paired except the case id; the exact-column control then matches
    columns of a DIFFERENT history. The Leg B design (history by base, arms differ at the scored turn) has a BFCL analog:
    TEACHER-FORCED per-turn evaluation — the history before turn t is the ground-truth trajectory (ground-truth calls
    executed through the vendored environments, exactly what my measurement did), every arm generates turn t (with its own
    within-turn tool steps), and turn t is scored by multi_turn_checker on decoded_turns = ground_truth[:t] + [arm's turn t].
    This gives identical context ids per turn across arms, a paired per-turn unit (~5 turns/case; 40 dev long_context
    turns of which 12 evict), no cascade of early failures into later turns, and a well-posed retention question ("given
    the correct history, does retention of it change the next turn?"). The free-running trajectory (what the BFCL
    leaderboard reports) should be RUN AND REPORTED for base and clf_pinned_echo (2 arms, not 6), never gated. HIGH.
1.3 Primary cohort. long_context final pass with n=16 cannot pass A1/A3 (M5). Two changes restore a test without touching
    the sealed cohort: (i) primary UNIT = per-turn pass under teacher forcing (1.2), clustered by case; (ii) primary
    POPULATION = every sealed turn at which eviction fires (any category; on the dev pattern only long_context turns, ~24
    of the sealed 16 x ~5 turns), with the non-evicting turns reported as the echo-only stratum. Cluster count stays
    16 for the continuity term but the per-cluster mean is continuous, and a +25-pt per-turn effect on 8 evicting cases
    is detectable; final all-or-nothing pass stays REPORTED. If Brian wants the all-or-nothing estimand gated, the only
    honest route is a larger long_context cohort drawn now by seed from the never-viewed remainder (disclosed: my R3-R8
    population statistics covered all 176 long_context cases in aggregate, no contents were read by a human). HIGH.
1.4 Two-way readings that the outcome rules do not close:
    - A3 with full - base <= 0: a small trunk on 37k-column contexts can be WORSE than evicted (and 2/8 dev cases exceed
      the position limit, M4). Then 0.5 x (full - base) is negative and A3 passes for any arm >= base. Register: A3 is
      evaluated only if full - base > 0 on the primary; otherwise it is recorded "full is not a ceiling here; A3
      uninformative" and A1/A2 carry the leg. Register what full does above 40,960 columns: those turns are excluded from
      A3 (recorded), not silently truncated.
    - A2 pass because of COLUMNS, not tool retention: role_pinned = all prior user turns (24-308 columns, M1) against a
      classifier pin of up to 9,427 columns is a column contrast, not a selection contrast; the Multi-IF helper
      (role_pinned_spans) hard-errors when user columns cannot fill the budget, so the coder will have to invent a
      clipping rule. Register a column-matched parameter-free comparator: recency_pinned = all prior user columns +
      the most recent prior TOOL columns up to the classifier's column count (falls back to fewer columns only when the
      evictable range is short, recorded). Then A2 = clf_pinned_echo - recency_pinned reads "learned selection beats
      recency at equal columns and roles"; user-only role_pinned stays REPORTED so "tool retention matters" is a
      descriptive comparison (recency_pinned - role_pinned), not a gate. HIGH.
    - A1 pass because of the ECHO TOKENS: clf_control has pins and no echo, so A1 = (pins + echo) - (pins). This is
      the Leg B C1 shape, but the REGISTERED Leg A control (LEDGER-PLAN.md:421-423, synthesis rule 2) is "token-matched
      echo ... same template, same pin budget": the draft silently drops the control echo. On BFCL the echo can be
      thousands of tool-text tokens (B up to 9.4k columns, M1), so the nonspecific-text confound is far larger than
      Multi-IF's 24-78 tokens. Register control echo = the control spans' decoded text rendered through the same
      template (exact-column control spans have text by construction), so A1 holds tokens, template and residency
      constant; and CAP the echo at a registered budget (see 2.3). HIGH.
    - A1/A2/A3 pass on the echo-only stratum (no eviction) would be the full_echo - full diagnostic H1' found to be noise;
      the draft discloses this for the non-overflow categories — fine — but the primary definition must exclude
      non-evicting turns (1.3), otherwise the sealed long_context turns that never evict (28/40 on the dev pattern) dilute
      and can carry the contrast.
1.5 Ordering: pre-query eviction before the current user message is right (Amendment 2 lineage), provided the split is by
    message index (M8), not by the last `<|im_start|>user` marker.

## 2. Selector over user + TOOL spans (Q2)

2.1 Newline splitting is a no-op (M2): every BFCL tool message is one line, so the "line" is a 1-31,665-token dict repr.
    Three consequences: (a) the registered scorer CRASHES above ~185 second-segment tokens (M3) — the harness cannot run
    as registered; (b) a kept "line" of 9k columns vs B: the draft's "filled by probability then recency" does not say
    whether a span larger than the remaining budget is skipped, head-truncated or tail-truncated; (c) the classifier
    (bge-small, 192-token training window, trained on hand-written short tool-fact sentences) has never seen a 500-token
    Python repr — its keep/none decision on such an input is not a selection, it is a coin with unknown bias.
    Required registration: tool-message candidates = the message split on newlines, then every piece longer than
    T = 128 tokens (registered constant) chunked into consecutive 128-token pieces at token boundaries (the last piece may
    be shorter); NO cap on candidates per message (CPU cost: 37k tokens / 128 = 290 chunks per turn, trivial); scoring
    input for every candidate (user or tool) truncated to the classifier's window by `truncation="longest_first"` with
    max_length 192 — under T = 128 this never truncates, and the harness must ASSERT no candidate exceeds 192 tokens.
    Pins = kept candidates ordered by (P desc, recency), added WHOLE while they fit in B; the first that does not fit
    stops the fill (no partial spans, no sub-threshold spans ever added; B is a cap, not a target). CRITICAL (a), HIGH (b,c).
2.2 Re-execution / injection hazards of echoing tool text verbatim inside the user turn:
    - the header "Earlier user instructions restated verbatim:" attributes tool output to the user; register a neutral
      header for Leg A ("Earlier context restated verbatim:") and per-entry prefixes "user:" / "tool:".
    - tool text can carry `<tool_response>`, `<tool_call>`, `</tool_call>`, or chat-control tokens (BFCL's file system
      lets earlier turns write arbitrary strings that later `cat` returns). Register fail-closed: any candidate whose text
      contains `<|im_`, `<tool_call`, `</tool_call`, `<tool_response`, `</tool_response` is dropped from pins AND echo and
      counted (`echo_dropped_control_tokens`). sol's CTRL-1 asked for exactly this on Leg B.
    - an echoed error line ("Error: ... not found") or an echoed success line can trigger a retry or a skipped call; this
      is not a bug, it is the mechanism's cost, and it is exactly what the tool-call-validity and invalid-call safety
      counts measure — keep them, and add "calls repeated verbatim from the ground-truth history" as a reported count.
    - echo-copy: copying an identifier from echoed tool text into a call is the TASK. The registered Leg A safety line
      "echo-copy exclusion" (LEDGER-PLAN.md:423) must be explicitly superseded for Leg A: echo-copy rate reported, no
      exclusion; the draft says "reported, not gated" but does not say it overrides :423. MEDIUM.
    - echo size: with B up to 9.4k columns the echo alone can add 9k tokens and push the echo arm past the position limit
      that the evicted arms were built to avoid. Register an echo cap E = 1,024 tokens (most probable spans first, whole
      spans), recorded per turn; pins stay at B. MEDIUM.
2.3 Same-role-pool exact-column control: the right null for A1 (position, role and count matched; only selection differs)
    — with three registrations: (i) pool shortfall: the user pool is 24-308 columns and a keep-all classifier can pin most
    of it, leaving fewer non-pinned user columns than pinned ones (Multi-IF raises RuntimeError); register "shortfall
    filled from the other role's pool, recorded per turn as control_role_shortfall"; (ii) nearest-column matching inside
    a single 31k-token tool message picks the columns ADJACENT to the pinned chunk — near-duplicate content (a directory
    listing's neighbouring entries). That is still the correct null (same role, same message, same position) but the
    write-up must not call it "random"; (iii) the control gets the echo of its own spans (1.4). MEDIUM.
2.4 role_pinned as parameter-free comparator: right idea, wrong budget on BFCL (1.4). Keep it reported; gate on
    recency_pinned.
2.5 Budget B = 25% of evictable: on the giant turns B = 9.4k columns and, together with the 5.5k prefix, the pinned arms
    keep ~15k columns — "eviction" then removes 75% of a history the trunk could not use anyway. Fine as a registered
    constant, but report the pinned-column count per turn and the fraction of B used; do not let B be "amended" after
    the coverage preflight.

## 3. Contrasts, safety, preflights (Q3)

3.1 Contrasts: A1-A3 as in 1.4 (control echo; recency comparator; A3 conditional on full - base > 0). Per-turn unit,
    Holm over three at 0.05 — consistent with Leg B. Note LEDGER-PLAN.md:422 registered alpha 0.025 "Holm with Leg B";
    the draft uses 0.05 within-leg; state which supersedes.
3.2 Safety clause: the ROUND 7 integer clause per arm vs full on the primary cohort is fine; two gaps: (a) "invalid tool
    calls <= full + 1" must define invalid = a <tool_call> block that fails parse_tool_calls or call_to_python (the
    existing fields), counted per turn; (b) src/stencil/bfcl.py:summarize_records still implements the RATE-based ROUND 7
    (0.02 caps, arms base/ledger/control, alpha 0.025) — the brief says rework, so register that the integer clause
    REPLACES it. LOW.
3.3 Base competence floor 15% on the dev slice (final pass, all categories): the floor protects the wrong cohort. With the
    primary on evicting long_context turns, register the floor on the primary unit: base per-turn pass on dev
    long_context turns >= 15% (6/40) AND overall final pass >= 15%; if either fails on 1.7B the 4B trunk is used and both
    re-checked; if 4B fails too the leg is void (no third trunk). The synthesis's 1.7B numbers (7.8-10.3% overall, 2.5%
    long_context) predict the fallback; register the 4B path now so it is not a post-hoc choice. MEDIUM.
3.4 Determinism on 4 cases: fine; name the 4 (first dev id per category) so the choice is not made after seeing timings.
3.5 Coverage preflight: reported, no floor — right (no reuse of the 100 labels). Add one pre-committed disclosure rule:
    if the classifier keeps 0 tool candidates on the dev long_context turns, A2 is declared uninformative BEFORE the sealed
    run (the leg then tests user-span selection only). That is a reading rule, not a tuning rule.
3.6 Cost cap 12 GPU-h: Leg B needed 22 GPU-h for 909 single-generation conversations; Leg A is 64 cases x 6 arms x ~5
    turns x 1-3 steps, with 37k-token prefills on the giant turns (M1) and a 512-token max_new. The cap will be exceeded;
    "amend before viewing outcomes" is acceptable, but register the amendment path now (cap 30 GPU-h; if the projection
    exceeds it, the 6-arm design is cut to 4 arms — drop role_pinned and clf_pinned, which are reported-only under 1.4 —
    never the cohort). Also register that the dev preflight and the sealed run use the SAME trunk. MEDIUM.

## 4. Lineage (Q4)

4.1 What makes BFCL a development benchmark here (all of it must be said): (i) the schema-first layout and the 1/23 finder
    failure shaped the protected prefix and the retirement of the finder; (ii) my population analysis of all 704 non-cohort
    cases (results/agentic-salience-review-fable.md R3-R8: 17% of later-turn literals live only in tool output; 63% of the
    long_context prompt is tool text) motivated selecting over TOOL spans and, five hours later, the tool-role "fact" label
    in data/classifier/LABELS.md (M6); (iii) finder_labels.json (100 dev-cohort spans) were viewed and are retired;
    (iv) this draft's tool-line splitting rule was written knowing BFCL's output style. None of these touched the sealed
    64 (never run; results/qwen has no bfcl directory; git ls-files results has no bfcl artifact), and no BFCL sentence,
    API name or template is in data/classifier (grep for the eight API class names, `tool_response`, `<tool_call>`,
    `current_directory_content` and the review's example strings: 0 hits).
4.2 Paths by which BFCL content can still reach the selector or the harness's choices AFTER this registration:
    (a) the coverage preflight (dev slice) -> any later change to T, B, E, the header, the threshold or the chunker is
        tuning on BFCL: register the constants now and hash the harness before the preflight;
    (b) the 4B fallback decision consumes dev outcomes: registered rule, allowed;
    (c) the cost amendment consumes dev timings: registered path, allowed;
    (d) "selector work returns to the classifier data (tool-line examples)" after a failure: writing tool-line examples
        after seeing which BFCL tool lines were missed IS BFCL contact (the LABELS.md tool-fact clause already has that
        shape). Register: any post-Leg-A classifier data is written WITHOUT access to BFCL records, and its examples are
        nearest-neighbour audited against the dev slice as the scope-exemplar patch was against the probe;
    (e) the reviewers' population statistics (704 cases) remain the one human-mediated channel: disclose.
4.3 Model card (replace LEDGER-PLAN.md:600-603's clause for BFCL with): "BFCL V3 multi-turn is a development benchmark for
    this system: its prompt layout and an early finder failure shaped the protected-prefix harness, and aggregate
    statistics over non-cohort BFCL cases (where later tool calls draw their arguments from) motivated selecting over tool
    output and the tool-role label in the selector's training spec. No BFCL item, API name, output or paraphrase entered
    training; the 64-case sealed cohort was run once, after registration. BFCL results are a post-development evaluation,
    not zero-shot transfer."

## 5. No-contact family for the zero-shot claim (Q5)

Screened without opening any item (M7). Excluded by contact: Multi-IF, IFEval, IFBench, BFCL, tau/tau2, RULER, LongMemEval,
LoCoMo, InfiniteBench, LongBench, MT-Eval, ToolSandbox, SEQUOR, HANDBOOK/SOP-Bench, VerIFY, Lost-in-Conversation (named in
results/agentic-bench-* or research-*), APIGen-MT (in the host's HF cache), GSM8K/MMLU (data/bench). Candidates with zero hits
in the tracked tree, results/, scratchpads, memory and caches, all with predefined user turns, programmatic checkers and no
LLM user/judge:
  F1 ToolTalk (Microsoft, MIT): multi-turn tool-use conversations with predefined user turns, deterministic mocked APIs,
     exact action-match scoring; later turns rely on ids returned by earlier calls — the agentic sibling of BFCL.
  F2 CoSQL (with SParC as the same family; CC BY-SA 4.0): conversational text-to-SQL, execution-accuracy checker; later
     questions elide entities and constraints fixed in earlier turns — retention of user-stated facts and constraints.
  F3 ConvFinQA (MIT): multi-turn numerical QA over a filing; exact-match with tolerance; later questions reference
     earlier answers and quantities — retention of derived facts under long documents (native pressure without tool text).
  Alternate if a licence or format blocks one: API-Bank level-1/2 dialogues (0 hits; check licence before naming it).
Contact screen to register (run BEFORE any item is fetched, results committed): (1) case-insensitive grep of the family
name, its canonical file names, split names and example ids over `git ls-files`, results/, every session scratchpad and
memory file, and ~/.cache/huggingface; (2) `git log -S<name>` over the whole history; (3) the three reviewers' research
reports and the bench synthesis are read for the name; (4) data/classifier nearest-neighbour audit of 200 sampled family
sentences against all training rows (cosine < 0.9 on bge; exact/near-duplicate count reported) AFTER the family is fetched
but BEFORE any run; (5) a written statement that the harness constants (K, B, T, E, threshold, header) are the Leg A
values, hashed, and that nothing is changed after the family is opened; (6) the family's dev/sealed split is drawn by seed
and the sealed half is hashed before any generation.

## 6. Findings register

| id | sev | finding | fix |
|---|---|---|---|
| L1 | CRITICAL | Registered scorer crashes on tool lines > ~185 tokens (M3); "newline split" is a no-op on BFCL (M2) | 2.1: 128-token chunking, longest_first, assertion |
| L2 | HIGH | "Identical context ids per turn" is impossible under free-running trajectories; design unspecified (1.2) | teacher-forced per-turn primary; free-running reported |
| L3 | HIGH | Primary = long_context final pass, n=16, needs >= 6/16 flips with 0 reversals (M5); registered null | primary unit = per-turn pass on evicting turns (1.3) |
| L4 | HIGH | Control drops the registered token-matched echo; echo can be thousands of tool tokens (1.4) | control echo + echo cap E |
| L5 | HIGH | A2 comparator is column-confounded and hard-errors at BFCL user-column counts (1.4) | recency_pinned gated, role_pinned reported |
| L6 | HIGH | Eviction decision per step vs per turn, split by marker vs message index, cache persistence unregistered (1.1, M8) | 1.1 text |
| L7 | HIGH | Budget fill with spans larger than the remaining budget unspecified (2.1b) | whole-span fill, B a cap |
| L8 | MEDIUM | A3 sign and the full arm above 40,960 positions (M4) | A3 conditional; exclusions recorded |
| L9 | MEDIUM | Tool-text echo header/prefix, control-token fail-close, echo-copy exclusion override (2.2) | 2.2 text |
| L10 | MEDIUM | Control pool shortfall on the tiny user pool; "random" wording (2.3) | shortfall rule, wording |
| L11 | MEDIUM | Competence floor on the wrong cohort; 4B path; cost cap predictably exceeded (3.3, 3.6) | 3.3/3.6 text |
| L12 | MEDIUM | Lineage: tool-role label post-dates BFCL population analysis; post-failure "tool-line examples" path is BFCL contact (4.1-4.2) | model-card text 4.3; rule 4.2(d) |
| L13 | LOW | summarize_records still rate-based ROUND 7 / old arms; alpha 0.025 vs 0.05 unstated; 4 determinism cases unnamed | 3.1, 3.2, 3.4 |

## VERDICT: UNSOUND as drafted (SOUND-WITH-FIXES once the text below is adopted; no GPU minute should be spent on the draft's
harness because it cannot run (L1) and its primary cannot pass (L3)).

## Exact text changes (replace the corresponding draft sentences; everything else in the draft stands)

Harness, eviction bullet — replace with:
"- Eviction: one decision per user turn t >= 2, taken at step 0 of the turn, before the turn-t user message is prefilled:
  if prefix_columns + history_columns > K = 8192, evict the evictable range = all columns after the protected prefix and
  before the turn-t user message (located by message index, never by the last <|im_start|>user marker, because tool
  responses are rendered inside user blocks), keeping the arm's pins. The KV cache persists across the steps of a turn
  (assistant and tool-response tokens are appended; no re-render, no second eviction); the cache may exceed K within a
  turn and this is recorded (columns after each step), identical across arms. Recorded per turn: evicted, columns before /
  after, evictable size, pinned columns, budget used, echo tokens."

Harness, history/turn design — add after the eviction bullet:
"- Histories are TEACHER-FORCED: before turn t every arm sees the ground-truth trajectory (ground-truth calls of turns
  < t executed through the vendored environments, rendered as <tool_call> JSON + <tool_response>), so context ids are
  identical across arms at every turn. Each arm generates turn t with its own within-turn tool steps (MAX_STEPS 20,
  deadline 300 s); turn t is scored by multi_turn_checker on ground_truth[:t] + [the arm's turn t]. The free-running
  trajectory (BFCL's own protocol) is run for base and clf_pinned_echo only and REPORTED (final pass), never gated."

Selector bullet — replace with:
"- Selector: candidates = sentences of prior USER messages (registered splitter) and prior TOOL messages split on newlines,
  then every piece longer than T = 128 tokens (Qwen3 tokenizer) chunked into consecutive 128-token pieces; no cap on
  candidates. Scored WITHOUT context, role 'user' / 'tool', by the registered artifact with truncation='longest_first',
  max_length 192; the harness asserts no candidate exceeds 192 encoder tokens. keep iff P(rule)+P(fact) >= 0.5. Pins =
  kept candidates ordered by (P desc, recency), added whole while they fit in B = 25% of evictable columns; the first that
  does not fit ends the fill; sub-threshold candidates are never added; B is a cap. Any candidate containing <|im_,
  <tool_call, </tool_call, <tool_response or </tool_response is dropped from pins and echo and counted. Echo =
  text_ledger_context with header 'Earlier context restated verbatim:' and per-entry prefixes 'user:' / 'tool:', most
  probable spans first, capped at E = 1,024 tokens (whole spans), placed inside the turn-t user message and fixed for all
  steps of the turn."

Arms bullet — replace 'clf_control (...)' and 'role_pinned (...)' with:
"clf_control (exact-column control from the SAME role pool as the pins, user and tool columns in the same proportion,
nearest free column, built after the echo clamp; pool shortfall in one role is filled from the other role and recorded;
the control arm receives the ECHO of its own spans' decoded text under the same template and cap, so A1 holds tokens,
template, position and residency constant) | recency_pinned (all prior user columns + the most recent prior tool columns
up to the classifier's column count; parameter-free) | role_pinned (all prior user columns, nothing from tool output;
REPORTED only)".

Registered contrasts — replace with:
"Primary unit = per-turn pass under teacher forcing at turns where eviction fired (any category; cluster = case;
continuity 100/k); one-sided cluster-robust; Holm alpha 0.05 over three (supersedes the 0.025 cross-leg alpha at
LEDGER-PLAN.md:422 for this leg): A1 clf_pinned_echo - clf_control > 0; A2 clf_pinned_echo - recency_pinned > 0;
A3 clf_pinned_echo - base > 0.5 x (full - base), evaluated only if full - base > 0 on the primary (else recorded
'full is not a ceiling; A3 uninformative'); turns whose full-arm prompt exceeds 40,960 positions are excluded from A3
and counted. Reported, not gated: final all-or-nothing pass per arm (teacher-forced and free-running), the non-evicting
turns (echo-only stratum), role_pinned and recency_pinned - role_pinned, tool-call validity, echo-copy rate (NO exclusion:
this supersedes the 'echo-copy exclusion' at LEDGER-PLAN.md:423 for Leg A, because copying a tool-returned identifier is
the task), calls repeated verbatim from history, columns and echo tokens per arm and turn."

Safety — append: "invalid = a <tool_call> block failing parse_tool_calls or call_to_python, counted per turn; the integer
clause replaces the rate-based ROUND 7 fields in src/stencil/bfcl.py:summarize_records."

Preflights — replace (1) and (4) with:
"(1) base competence on the dev slice with the 1.7B trunk: overall final pass >= 15% AND per-turn pass on the 40 dev
long_context turns >= 15%; if either fails, the 4B trunk is used for the whole leg and both re-checked; if 4B also fails
the leg is void. The preflight and the sealed run use the same trunk. (2) BASE-vs-BASE determinism on the first dev id of
each category. (4) seconds per case and the projected sealed cost; cap 30 GPU-h; if exceeded, the arm set is cut to
base | clf_pinned_echo | clf_control | recency_pinned | full before any sealed outcome is viewed; the cohort is never cut."
Add: "(5) constants K, B, T, E, threshold, header and the harness sha256 are recorded before the preflight and are not
changed after it; any change re-registers the leg."

Outcome rules — append: "A2 is declared uninformative before the sealed run if the selector keeps zero tool candidates on
the dev long_context evicting turns (reported). Any classifier data written after this leg is authored without access to
BFCL records and nearest-neighbour audited against the dev slice."

Data lineage paragraph — replace the second sentence with the model-card text in section 4.3 above, and add: "The tool-role
fact label (data/classifier/LABELS.md, 2026-09-02 20:28) post-dates the BFCL population analysis (results/agentic-salience-
review-fable.md, 15:30) that motivated it; the sealed cohort was not part of that analysis."

No-contact family — append to the draft's last sentence: "Candidates, screened by name only (results/leg-a-review-fable.md
section 5): ToolTalk, CoSQL/SParC, ConvFinQA; the registered contact screen runs before any item is fetched."
