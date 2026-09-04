# SC1 draft registration review — fable (2026-09-04, CPU-only, read-only)

Reviewed: LEDGER-PLAN.md:860-910 (SC1 DRAFT v1); data/sc1/AUTHOR-CONTRACT.md:1-45; results/astra-research-blockers.md
§3 (:94-148) and §5 (:177-206); results/astra-program-review.md G1 (:55-57); LEDGER-PLAN.md:793-821 (LEG B OUTCOME +
addendum). Code consulted for reuse/fairness claims: src/stencil/bfcl.py, scripts/multiif_evict.py,
src/stencil/selector_v2.py, src/stencil/qwen3.py:88-100. No GPU, model, or sealed benchmark file was touched.

VERDICT: SOUND-WITH-FIXES. The estimand, exact test, and adoption logic are correct and the power table reproduces
exactly. The draft cannot be registered as written because (a) the rule arm's candidate set, the echo drop order, and
the admission rule are not the same procedure the existing core implements and are not specified precisely enough to
implement one way; (b) half the design (RECENT-age episodes) is structurally concordant under the "most recent 1,024
tokens always kept" clause, so the registered power cells are for a discordance the design mostly forbids; (c) the
author list includes sessions that have read the selector diagnostics, contradicting the contract's own
contamination clause; (d) the operational-limit clause is ambiguous in a way that changes the adoption decision.
All are text fixes; replacement text is at the end.

## Power recomputation (CPU, python3, exact enumeration; scratchpad sc1_power.py)

Method: M ~ Binomial(N, q); B | M ~ Binomial(M, (q+δ)/(2q)); reject when P[Binomial(M, .5) >= B] <= .05 (exact
binomial tail via integer comb). N = 256.

| q | δ = .05 power | δ = .05 AND b−c >= 13 | δ = .10 power |
|---|---:|---:|---:|
| .10 | 0.7822 | 0.5191 | — |
| .20 | **0.5086** | 0.4972 | 0.9736 |
| .30 | 0.3822 | 0.3822 | 0.8857 |
| .40 | 0.3157 | 0.3157 | — |

Every cell in astra's table (blockers.md:131-138) and the LEDGER line (:903-904) reproduces to the reported
precision. Additional facts: realized one-sided size under the null at q = .20 is 0.0378 (conservative, as expected
of an exact test); a true 3-point gain at q = .20 has 24% power; fewer than 5 discordant pairs can never reject
(5-of-5 gives 0.03125). The joint gate at q = .10 costs 26 points of power (0.78 -> 0.52): with few discordant
pairs, "p <= .05" is reachable at b − c = 5..12 but the 13-net-pass floor is not. This is by design (adoption, not
test) but should be stated so nobody reads "78%" as the probability of adoption.

## 1. VALIDITY

**V1 (HIGH) — admission rule contradicts the only implemented core and is underspecified.** LEDGER:878 and :880 say
"admits whole spans in rank order while they fit B, skips oversize spans, continues". The registered Leg A core does the
opposite: `budget_history_spans` breaks at the first span that does not fit (src/stencil/bfcl.py:363-366, `break`),
and Leg A's text registers "the first that does not fit ends the fill" (LEDGER:661). Either is defensible; SC1 must
say which and the harness brief must say "new function, not `budget_history_spans`". Skip-and-continue also needs a
stated terminal condition (continue through the whole ranked list; never split a span; B is a hard cap on pinned
columns clipped to the evictable range) or two coders will implement two different fills.

**V2 (HIGH) — "most recent 1,024 history tokens always kept" is a new clause with no defined geometry.** Neither
`context_layout` (bfcl.py:67-122; evict_range ends at the current user marker) nor multiif_evict.py:145-170
implements a retained recent window. Undefined: (i) is C (LEDGER:874) counted before or after removing the window;
(ii) is a candidate span straddling the window boundary a candidate at all, and if so is it pinned in part; (iii) are
spans inside the window eligible for pins/echo (they would be retained twice: in cache and in echo). Register: window
= the last 1,024 tokens of the history immediately before the current user message; evict_range =
(protected_end, history_end − 1,024); C = its width; candidates are generated only from messages whose token span
lies wholly inside evict_range (a message straddling the boundary contributes only the columns before the boundary,
sentence-level candidates that straddle are dropped and counted); nothing inside the window is a candidate for pins
or echo. Also, in-contract episodes (4,096-8,192 history tokens, LEDGER/CONTRACT:11) give C >= ~2,800, so
floor(0.25 C) >= 700 > 256 for every valid episode: the min() is dead and B = 256 always. Say "B = 256 columns
(the 0.25 C branch cannot bind under the contract's length range; kept for out-of-range smoke episodes only)".

**V3 (HIGH) — echo drop order is unspecified and decides what the model sees.** E = 256 tokens including header and
labels while B = 256 columns: the echo cannot carry all pinned spans plus a header and per-entry `- user (turn 7):`
labels, so some pinned spans are dropped from the echo in every episode. LEDGER:878-879 says only "echoes admitted
spans chronologically within E". Which spans are dropped — the oldest (chronological fill) or the lowest-ranked? The
two choices favour different arms: chronological-drop hurts the rule (whose ranking is recency) less than the clf.
Register: fill the echo in the arm's own admission order until the next whole entry would exceed E, then RENDER the
kept entries chronologically. Leg A's echo is "most probable first" (LEDGER:666) and its renderer `render_echo`
(bfcl.py:382-393) emits `- role: "text"` with no turn label; SC1 needs a new renderer with the turn label and a
token-counted cap.

**V4 (HIGH) — operational limit clause is ambiguous and the two readings disagree.** LEDGER:894 "clf-only
invalid/truncated/repetitive episodes (vs rule) <= 2". Reading A: #{episodes where union-flag(clf) AND NOT
union-flag(rule)} <= 2. Reading B: #{flag(clf)} − #{flag(rule)} <= 2. With rule flagged on 5 and clf on 7, A can be 7
(fail) while B is 2 (pass). Astra's text ("Record each flag and their episode-level union", blockers.md:148) supports A.
Register A explicitly. Astra's latency limit (mean total latency <= 1.25x rule) is dropped to "reported" in the draft
(LEDGER:901) — acceptable, but say "the latency limit from the source design is deliberately NOT a gate" so the
omission is not read as an oversight.

**V5 (MEDIUM) — "collateral state corruption" undefined for EDITING episodes** (LEDGER:895). Editing episodes have
no state; their checker's forbidden-content/extra-key obligations already score 0. Register: collateral = tool-work
episodes only, "a protected record changed or a non-target record created/deleted"; "attributable to clf only" =
collateral(clf) AND NOT collateral(rule) on the same episode; the count is reported per arm as well.

**V6 (MEDIUM) — repetitive definition has no implemented counterpart.** "a normalized 4-token block repeated >= 8
times" (LEDGER:897). `repeated_4gram_fraction` (multiif_evict.py:290-295) measures a fraction; `echo_copy_flag`
(bfcl.py:1057-1067) detects copying from the echo; neither counts consecutive block repeats. Register "the same
4-token block at 8 consecutive block positions (32 tokens), normalized = lowercased, whitespace-collapsed token ids"
and require a unit test with a positive and a negative fixture. Also register that truncation is evaluated first and
repetitive is evaluated on ALL generations (the Leg A "non-truncated only" rule, LEDGER:687-689, would otherwise be
inherited silently) — the union flag makes the order irrelevant for the gate but not for the reported taxonomy.

**V7 (MEDIUM) — setup gate cannot be shown to have been run "BEFORE any final outcome is opened"** (LEDGER:883). The
harness must refuse to launch the final run unless a committed setup summary (pass = true, setup-episode hash list)
exists, and must write final records under a directory whose summary is produced only by a separate `--summarize`
invocation. Otherwise "not opened" is a promise, not a mechanism (the w_seal/w3a lesson in AGENTS.md).

**V8 (LOW) — G1-style loophole check.** The primary contrast is clf vs rule with both arms independently budgeted, so
the G1 failure mode (mechanism success declared while the learned-selector question goes unanswered) is closed. The
remaining way to satisfy the registration without answering the question is structural concordance (P1 below), not a
clause loophole. "Otherwise the rule is chosen" (LEDGER:895) correctly makes no claim that the rule is better.

## 2. FAIRNESS

**F1 (HIGH) — the rule arm's candidate set is not defined; "same admission and echo procedure" does not fix it.**
clf candidates are sentence pieces of prior user messages plus newline-then-sentence-then-128-token chunks of tool
messages, with chat-control/special-token rows dropped (bfcl.py:221-300; LEDGER:654-660). LEDGER:880 "rule —
prior-user spans newest-first, then prior-tool spans newest-first" does not say whether a rule "span" is a sentence
piece, a whole message, or a chunk. Whole-message spans with skip-and-continue at B = 256 would skip most user
messages and admit small ones; sentence spans would take the newest ~256 user tokens. Register: both arms rank the
SAME candidate list (the registered segmenter with the unsafe-row drop applied before ranking), and differ only in
the ranking key — clf: (score desc, message_index desc, char_start asc); rule: (role != user, message_index desc,
char_start desc). The registered `role_pinned_spans` (multiif_evict.py:271-288) pins whole user turns and reads the
classifier budget; it must NOT be reused (G1, LEDGER:817-818).

**F2 (MEDIUM) — the rule as specified is structurally blind to tool-origin facts, and the registration should say
so.** With B = 256 and 12-24 turns of user text, prior-user sentences alone exhaust B in essentially every episode, so
"then prior-tool spans" never executes and the rule never pins tool output. Half the episodes (CONTRACT:17-19, TOOL
origin 50%) are therefore decided for the rule by the 1,024-token window alone. That is a legitimate deployable rule
(it is the C2 winner), but a clf win over it demonstrates "learned selector beats newest-user-text", not "learning
beats rules". Two options: (a) disclose in the registration that the comparator is the C2 rule and that a stronger
parameter-free comparator (role-interleaved newest-first) is not tested; (b) add `rule_mixed` (newest-first across
both roles) as a REPORTED, non-gated third arm (+~2.5 GPU-h at the setup-measured rate; if the 8 GPU-h cap does not
hold it, drop it). I recommend (a) now and (b) only if the setup timing leaves >= 3 GPU-h of headroom.

**F3 (LOW) — independence of the rule from the classifier is enforceable and should be tested.** Require that the
rule function takes (candidates, evict_range, B) only, that the harness computes rule pins before loading the
classifier, and that a unit test asserts identical rule output with the scorer stubbed to return constant 0 and
constant 1.

**F4 (LOW) — B = 256 and E = 256.** B = 256 is ~3-6% of history under the contract range (vs 25% in Legs A/B); it is
a deliberate small-dose test and defensible because both arms share it and the echo re-injects the same text. E = 256
is ~one echo token per pinned column; with header/labels it will hold ~200-220 span tokens, so both arms lose 15-20%
of their pins from the echo (V3). Defensible once V3 is registered. Note that the 1,024-token window plus 256 pins
plus 256 echo tokens means both arms retain ~1,500 of 4,096-8,192 history tokens; the "evicted" diagnostic retains
1,024. The setup headroom gate (full − evicted >= 8/32) is therefore measuring headroom above a 1,024-token recency
baseline, which is what a deployable comparator must beat — good.

**F5 (LOW) — tool chunking symmetry.** Line-first splitting of tool JSON (bfcl.py:196-202, :249-256) breaks records
across candidates; both arms inherit it. The clf scores each line without context (selector_v2.py:105, :125-131), so
an identifier line separated from its label line scores on the line alone. Symmetric, but it means the clf's
tool-side advantage depends on how authors format tool returns; the contract must not instruct authors on tool-output
formatting beyond "realistic JSON or plain text" (it currently says nothing, which is right).

## 3. CONTAMINATION

**C1 (HIGH) — the author list violates the contract's own isolation clause.** LEDGER:863-866 names fable, gpt-6-astra,
Opus, and kimi-k3 as authors who "receive only the contract". fable (this session) and astra have read the Leg B C2
diagnostic ("classifier under-selects turn-2 tail text", LEDGER:814-816), the selector label spec
(data/classifier/LABELS.md:18-40), and the segmentation/threshold; Opus and kimi wrote and reviewed the classifier's
training data (LABELS.md:5-7). An author who knows the classifier fires on "from now on"/"always" sentences and
under-selects tail text can, without intent, write histories that favour or disfavour it. Fix (cheap, enforceable):
authors are FRESH sessions with no repo access, tool access, or prior conversation, given the contract text only;
the launcher records the session provenance (model id, empty prior context, the exact contract sha256); reviewers of
this registration (astra, fable, kimi per LEDGER:907) and everyone who touched data/classifier/ are excluded from
authoring in their reviewing/authoring contexts — the same model family may author in a fresh session. Record this as
a data-lineage line.

**C2 (MEDIUM) — the contract presupposes repo exposure.** CONTRACT:6-7 "Do not reuse any names, IDs, values, or
phrasings from anything you have seen in this repository's data/ or results/ directories" is incoherent with "receive
only the contract" — a contract-only author has no repository. Replace with a positive rule (below). Also
CONTRACT:5-6 lists benchmark names; naming them is harmless for exclusion but primes the families; "any public
benchmark or dataset" suffices.

**C3 (MEDIUM) — "no sibling stories" is not enforceable as written.** CONTRACT:7-8 and blockers.md:112 assert semantic
distinctness but register no check. Enforceable minimum: (i) each episode declares a `domain` tag and `task` one-liner;
(ii) at most 3 final episodes per (author, domain); (iii) mechanical collision check across ALL 288 episodes — no
shared 6-12 character identifier, no shared fictional proper name, and 8-gram Jaccard overlap between any two
histories < 0.05 after removing the system/tool-schema block; (iv) the independent reviewer marks any pair sharing
plot, entity roles, or tool family AND task as siblings; siblings are replaced from a NEW seed before hashing, never
after. Setup/final disjointness is the same check across pools.

**C4 (MEDIUM) — "checker + six mutations" is not yet sufficient for a non-vacuous pass.** CONTRACT:31-36 asks for a
"checker specification"; a specification is prose until it runs. Register: the checker is executable (a declarative
JSON checker evaluated by the harness's checker runner, see §5); at freeze the reviewer's runner must show reference
-> PASS, each of the six mutations -> FAIL, and two additional mechanical checks: (a) the final request text and the
system prompt contain none of the reference's indispensable literals (string match against the values the checker
requires), and (b) the checker is canonicalizing — JSON outputs are parsed and compared structurally (key order and
whitespace irrelevant; numbers compared as values; strings exact), text artifacts compared line-normalized (strip
trailing whitespace, collapse blank runs). Without (b) both arms fail concordantly on formatting and the run measures
JSON hygiene. Mutations are authored by the episode's author; that is fine because the reviewer runs them and adds
one of their own choosing if any mutation is trivial (the empty-output mutation is always trivial).

**C5 (LOW) — selector-derived knowledge in the contract.** The 1,024-token window and 4,096-8,192 range
(CONTRACT:11, :17-18) are shared-arm parameters, not classifier knowledge. Sentence segmentation, the 128-token tool
chunk, the 192-token scorer truncation and the 0.5 threshold are NOT in the contract — keep it that way. Authors must
compute "old/recent" without the trunk tokenizer; register that the harness recomputes `age` from the rendered token
layout and reports realized counts, overriding the author label (the author label is a target, not a measurement).

**C6 (LOW) — "authors do not know which policy is expected to win"** is only true for fresh sessions (C1). A session
that has read this repo knows C2's outcome.

## 4. POWER / COST

**P1 (HIGH) — structural concordance on the RECENT half makes the registered power cells optimistic for this
design.** By CONTRACT:17-18, RECENT means the indispensable information lies inside the most recent 1,024 history
tokens, which both arms ALWAYS retain (LEDGER:873-874). On those episodes the arms differ only in which non-essential
spans they add, so a discordant pair needs a distractor-induced error — rare. Effective discordance is then
q ≈ q_old/2 and the overall gain δ ≈ δ_old/2: a registered 5-point overall gain requires the classifier to win the
OLD stratum by ~10 points, and the q = .20 cell (51%) is the power for a discordance the design mostly forbids. The
RECENT stratum is still worth having as a "do no harm" control, but not at 50%. Register age sampling OLD:RECENT =
75:25 (expected 192/64), which keeps the marginal estimand simple (still an independent draw from a frozen mixture,
blockers.md:113-114), and state the power line as "for the frozen 75:25 mixture, at overall discordance q". If the
50:50 split is kept, the power line must say the q = .10 row is the realistic one (78%, 52% with the gate).

**P2 (MEDIUM) — 40-64 author-hours is not realistic for 288 hand-authored episodes of 4,096-8,192 tokens.** Astra's
estimate (blockers.md:142) is 6-10 minutes per scenario; an episode here is 3,000-6,000 words of coherent scripted
dialogue with tool schemas, an initial state, a reference, an executable checker, six mutations, and seed-sampled
entities, plus independent review of all of it (CONTRACT:35-36, LEDGER:906). Model authors generate a 6k-token
episode in minutes, but the reviewer must read every history for sibling detection and marker leakage; at 15-25
minutes per episode all-in, 288 episodes are 70-120 hours. Register 80-120 h or adopt P3.

**P3 (recommendation) — cheapest cut that preserves independence: a scenario spec + deterministic expander.**
Authors write a compact SPEC (300-800 tokens): entities (from seed), the governing instruction and its scope
trajectory (continuing/overridden/cancelled/switched with the turn at which it changes), the indispensable fact with
origin (user/tool) and target age, 4-8 unique distractor facts, the final request, the expected artifact/state, and a
declarative checker. A registered EXPANDER renders the 12-24-turn history: it interleaves the spec's content turns with
filler sub-tasks drawn by seed from a large pool of UNRELATED fictional mini-tasks (written once, reviewed once,
shared across episodes and disclosed as shared filler), places the indispensable turn to hit the target age given the
trunk tokenizer, and renders tool returns from a small fixed library of 6-10 fictional tool families backed by one
generic in-memory record store (create/update/delete/get/list on typed tables). Mutations are generated mechanically
from the spec (swap in the overridden value; execute the cancelled action; wrong entity from the same table; wrong
scope = apply the switched-away rule; empty output; collateral edit of a protected record). This cuts authoring to
the spec plus review (~5-8 minutes each, ~35-50 h total), makes the checker executable by construction, makes
old/recent placement exact, and keeps the semantic source unique per episode. Two guards must be registered: the
filler pool must be large and role-mixed enough that relevance is not recoverable from surface form (CONTRACT:24-25;
require that a trivial bag-of-words classifier trained on 32 setup episodes cannot separate indispensable from filler
sentences above AUC 0.6 — a CPU check), and the expander code is frozen and hashed with the episodes.

**P4 (LOW) — GPU cost.** 576 final generations + 128 setup generations at ~8k prompt tokens and <= 256 new tokens on
4B (2x 1.7B per token, LEDGER:419; Leg B measured 82.6 s per 6-arm conversation on 1.7B, LEDGER:810) is plausibly
20-40 s per arm-episode, i.e. 4-8 GPU-h. The cap is tight; the registration correctly measures timing at the setup gate
and must add: "if the setup-measured projection exceeds 8 GPU-h, defer without shrinking N" (blockers.md:148 has this
sentence; the LEDGER dropped it).

## 5. THE MISSING PIECES — what the harness coder brief must contain

1. Renderer: Qwen3 chat template, non-thinking (`enable_thinking=False`, empty think block if the template emits
   one), tool schemas inside the system block; tool turns rendered the way `_message_locations` (bfcl.py:134-193)
   detects them so role = tool is recoverable; byte-identical framing across arms; the echo inserted inside the final
   user message as in Leg A (LEDGER:666) with header "Earlier context restated verbatim:" (bfcl.py:37) and entries
   `- <role> (turn <n>): "<text>"` JSON-escaped.
2. Layout: reuse `context_layout` (bfcl.py:67-122) then apply the 1,024-token window (V2): evict_range =
   (protected_end, history_end − 1024); assert protected_end < history_end − 1024 else the episode is out of contract
   (hard fail before any generation, counted).
3. Candidates: refactor `select_history_spans` (bfcl.py:221-321) so candidate generation + unsafe drop is a scorer-free
   function; the clf arm scores with `ClassifierScorer` (selector_v2.py:77-145, `scorer_truncated_candidates`
   reported); the rule arm ranks the identical list (F1). Candidates outside evict_range are dropped and counted.
4. Admission: NEW `admit_whole_spans(ranked, B)` skip-and-continue (V1); NOT `budget_history_spans` (bfcl.py:344-379,
   which breaks) and NOT `role_pinned_spans` (multiif_evict.py:271-288, which reads the classifier budget). Pin
   columns clipped to evict_range; no partial spans; `clamp_pins_newest_first` (bfcl.py:334-341) unused.
5. Echo: NEW builder — fill in admission order until the next whole entry would exceed E = 256 trunk-tokenizer
   tokens including header, render chronologically (V3); CONTROL_MARKERS/special-token drop (bfcl.py:38, :296-300);
   any chat-control token in an echo is a hard safety failure; record echo tokens actually used per arm.
6. Eviction/generation: reuse `prefill_with_eviction` (src/stencil/qwen3.py:88-100; eviction_timing "pre-query",
   keep = protected prefix + pins + window) via the `run_arm` pattern (multiif_evict.py:320-400: cache columns before /
   after, pinned_cols, truncated, EOS handling); temperature 0, max_new 256; the intervention counter for amplification
   and steering asserted == 0 per generation and written into the record; 40,960-position guard.
7. Output parsing: TOOL-WORK — `parse_tool_calls` (bfcl.py:965-1006) and `normalize_call` (:1017); exactly one call
   required (0 or >1 = invalid); EDITING — JSON parse of the first fenced or bare JSON object, or the raw text for text
   artifacts; invalid = parser/schema failure per LEDGER:896.
8. In-memory DB executor: NEW (BFCL's `execute_call_strings` bfcl.py:1127-1145 runs vendored BFCL environments and
   cannot host fictional schemas). Generic record store (typed tables, id-keyed records, create/update/delete/get/list),
   initial_state loaded per episode, the single call applied, full resulting state diffed against `reference`, protected
   records enumerated in the checker. No file, network, or eval; pure Python; deterministic.
9. Checker runner: declarative checker JSON (`state_equals`, `protected_unchanged`, `json_equals` with canonicalization,
   `required_lines`, `forbidden_substrings`, `max_lines`); a `--validate` mode that runs reference -> PASS and the six
   mutations -> FAIL for every episode and writes a validation manifest (C4); the same runner scores the run.
10. Flags: NEW `repeated_block_run(ids, block=4, runs=8)` with unit tests (V6); truncated = hit max_new without a
    complete valid output; invalid as in 7; per-episode union flag; collateral flag (V5).
11. Freeze/hash: episode files canonical-JSON sha256 (pattern `_canonical_json` bfcl.py:935), manifest with the
    classifier tree hash (`_tree_hashes` multiif_evict.py:667-673, must equal the LEG B sha256), trunk checkpoint
    (models/qwen3-4b.pt) and tokenizer hashes, contract sha256, expander/code tree hash; `_check_or_write_meta`
    pattern (multiif_evict.py:707-713) refusing to run against a different manifest.
12. Resume: one atomic record per episode containing BOTH arms (blockers.md:123 "record paired case rows in the same
    run"; `atomic_json` bfcl.py:1079); `resume_indices` pattern (multiif_evict.py:472-486) keyed by episode id AND
    episode hash; a resume never regenerates an existing arm output; setup and final in separate directories; the
    final run refuses to start without a committed setup summary with pass = true (V7).
13. Determinism preflight: two fresh processes on 2 smoke episodes produce identical token ids in both arms (Leg A
    preflight (2), LEDGER:701-702); smoke episodes are the coder's 8 synthetic ones, never reused (LEDGER:908).
14. Summary: b, c, exact p by integer arithmetic (Fraction), Clopper-Pearson 97.5% intervals (scipy `binomtest`
    `proportion_ci` or exact bisection), D_hat, marginal rates, adoption-rule fields, realized factor counts (harness-
    recomputed age), per-stratum success, latency per arm including CPU scoring, pins/echo used, failure taxonomy.

## Exact replacement text

LEDGER:863-866 (authors) — replace "authored under data/sc1/AUTHOR-CONTRACT.md by authors (kimi-k3, fable,
gpt-6-astra, Opus) who receive only the contract; no benchmark item, diagnostic, selector score, or repo example is
shown to any author; authors do not know which policy is expected to win." with:
"authored under data/sc1/AUTHOR-CONTRACT.md by FRESH model sessions (no repository, tool, or prior-conversation
access; contract text only; model id, contract sha256 and empty-context provenance recorded per episode). Sessions
that reviewed this registration or touched data/classifier/ do not author; the same model family may author in a
fresh session. No benchmark item, diagnostic, selector score, or repo example is shown to any author; a fresh session
cannot know which policy is expected to win."

LEDGER:873-876 (shared arm text) — replace "most recent 1,024 history tokens always kept; pin cap B = min(256,
floor(0.25 x C)) where C = evictable history columns; echo cap E = 256 tokenizer tokens including header and source
labels;" with:
"the window = the last 1,024 trunk-tokenizer tokens of history immediately before the final user message is always
kept; evict_range = (protected_end, history_end − 1,024), C = its width; candidates come only from columns inside
evict_range (a message straddling the window boundary contributes only its pre-boundary sentence pieces; straddling
pieces are dropped and counted); nothing inside the window is a pin or echo candidate; pin cap B = 256 columns
(= min(256, floor(0.25 C)); the 0.25 C branch cannot bind for in-contract lengths and exists only for smoke inputs);
echo cap E = 256 trunk-tokenizer tokens including header and per-entry role/turn labels;"

LEDGER:877-881 (arms) — replace with:
"  Both arms rank the SAME candidate list: sentence pieces of prior user messages and newline-first, sentence-split,
  128-token-chunked pieces of prior tool messages (the Leg A segmenter), after the chat-control/special-token drop.
  clf  — ranks by P(rule)+P(fact) from the frozen classifier (threshold irrelevant to ranking; reported), ties by
         message_index desc then char_start asc.
  rule — ranks by (role: user before tool), then message_index desc, then char_start desc; a pure function of the
         candidate list, evict_range and B; reads no classifier scores, quotas, counts, or echo lengths (unit test:
         identical output with the scorer stubbed to 0 and to 1).
  Admission (both): walk the ranked list; admit a span whole if its clipped column count fits the remaining B; skip
  it otherwise and continue to the end of the list; never split a span.
  Echo (both): fill in admission order until the next whole entry would exceed E; render the kept entries in
  chronological order with role and turn labels. Pinned spans dropped from the echo are counted per arm.
  DISCLOSED: the rule is the C2 winner (newest user text first); with B = 256 it will rarely reach tool spans. A clf
  win demonstrates an advantage over this deployable rule, not over all parameter-free rules."

CONTRACT:17-18 (age) and LEDGER factor text — replace "located OLD (before the most recent 1,024 history tokens) vs
RECENT, sampled 50:50" with "located OLD (before the most recent 1,024 history tokens) vs RECENT, sampled 75:25 (OLD
is where the policies can differ; RECENT is a do-no-harm control). The harness recomputes age from the rendered
tokens and reports realized counts; the author label is a target."

LEDGER:903-904 (power) — replace with: "Power (fable + astra, CPU, exact enumeration; sampling probabilities, not a
claim about SC1's discordance): N = 256, one-sided α = .05: true 5-point gain — 78.2% at overall discordance q = .10,
50.9% at q = .20, 38.2% at q = .30; with the b − c >= 13 adoption gate 51.9% / 49.7% / 38.2%; 10-point gain 97.4% at
q = .20, 88.6% at q = .30. RECENT-age episodes are near-certainly concordant, so the realistic overall q is low; the
q = .10 row is the planning row."

LEDGER:894-895 (operational limits) — replace "clf-only invalid/truncated/repetitive episodes (vs rule) <= 2; zero
checker-detected collateral state corruption attributable to clf only." with: "U = #{episodes where the union flag
(invalid OR truncated OR repetitive) is set for clf and NOT for rule} <= 2; K = #{tool-work episodes where clf's
resulting state changed a protected record or created/deleted a non-target record and rule's did not} = 0. Each flag
and the union are reported per arm. The source design's latency limit (mean clf latency <= 1.25x rule) is reported,
not gated, by decision."

LEDGER:896-897 (definitions) — append: "repetitive = the same normalized 4-token block at >= 8 consecutive block
positions; evaluated on every generation, truncated or not; unit-tested. Invalid for tool-work additionally = zero or
more than one tool call."

LEDGER:905-906 (cost) — replace with: "Cost cap: 8 GPU-h total (setup + two final arms); if the setup-measured
projection exceeds it, defer without shrinking N. Authoring: 256 + 32 episodes via the registered scenario-spec +
expander (data/sc1/EXPANDER.md, frozen and hashed with the episodes) ~35-50 author-hours; hand-authored fallback
80-120 h. Each episode's executable checker, reference (PASS) and six mutations (FAIL) validated by the harness's
--validate runner and signed by an independent reviewer before hashing; sibling check (identifier/name collision,
8-gram Jaccard < 0.05, <= 3 finals per author x domain) passed before hashing."

CONTRACT:6-8 — replace "Do not reuse any names, IDs, values, or phrasings from anything you have seen in this
repository's data/ or results/ directories. Every scenario must be semantically distinct from every other: changing
names or numbers does not make a new scenario." with: "Invent every name, identifier, value, organisation, and
phrasing; do not draw on any public dataset, benchmark, or prior example. Every scenario must be semantically
distinct from every other scenario you write: a different domain, task, and plot — changing names or numbers does not
make a new scenario. Declare a `domain` tag and a one-line `task` per episode; write at most 3 episodes per domain."

CONTRACT:31-36 — replace "a checker specification listing every obligation and invariant" with "an EXECUTABLE checker
in the declarative form below (state_equals / protected_unchanged / json_equals / required_lines /
forbidden_substrings / max_lines); JSON is compared structurally (key order and whitespace irrelevant), text
line-normalized. The final request and system prompt must not contain any literal the checker requires."

CONTRACT:44-45 — replace "Setup episodes (32, separate authors' pool, ...)" with "Setup episodes (32) are written by
sessions that write no final episode, use the same format, and share no domain, story, entity, or task with the 256
final episodes (checked mechanically across pools)."
