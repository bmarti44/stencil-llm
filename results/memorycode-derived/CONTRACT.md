# Exp 3a contract: MemoryCode-derived automatic-maintenance screen

Written 2026-09-11 before any GPU spend (plan/BACK-ON-TRACK-PLAN.md, section B, Exp 3).
Every choice below is fixed here; the implementation (`src/stencil/memorycode.py`,
`scripts/memorycode_screen.py`, `tests/test_memorycode.py`) may not add scientific
choices. The evaluation is labelled MEMORYCODE-DERIVED: no number here is comparable
to the MemoryCode paper's native protocol.

## Source

`vendor/memorycode` at sha `1ab87e119b2f9a498de8075219e1c07f6041b394`
(`data/bench/pins-manifest.json`; Apache-2.0). 360 dialogues; each dialogue is a list
of sessions with `type`, `text` (a mentor/mentee script, speaker-prefixed lines),
`session_regex`, `history_regex`, `session_eval_query`, `history_eval_query`, and a
per-session list of live instruction ids (`dialogue["instructions"][s]`, pairs
`[pivot_id, update_index]` into `topics.json`).

## Unit, items, split

- ITEM = (dialogue id, session index s) with s ≥ 1 and `history_regex` non-empty:
  the mentee must write code for each `history_eval_query` of session s while
  following every instruction live at session s, some of which were introduced or
  updated in EARLIER sessions.
- Eligibility of an item: the full native history prompt (all sessions 0..s) is at
  most 3,584 Qwen3 tokens (contexts ≤ 4,096 including a 512-token completion), and
  session s has at least one prior session containing an `instruction-add` or
  `instruction-update` type (otherwise the reminder arms have nothing to remember).
- Split by DIALOGUE (template family): eligible items are grouped by dialogue id,
  dialogues are shuffled with `random.Random(0)`, and items are drawn one per dialogue
  in that order: the first 16 → SETUP (3b), the next 64 → SCREEN (3c). No dialogue
  contributes to both. The item list is written to `items.json` before any GPU run.

## Prompt rendering (native single-message format; no chat re-rendering)

The native MemoryCode prompt is one user message; the derived evaluation keeps it:

```
<|im_start|>user
This is a thread of dialogues between you and your mentor {mentor}:
 {THREAD}
{REMINDER}Based on information provided, write a {history_eval_query}. Do not provide
example usage. You must follow all the latest coding guidelines provided by your
mentor, including any possible updates.<|im_end|>
<|im_start|>assistant
<think>

</think>

```

- `history` arm: THREAD = sessions 0..s verbatim, each prefixed by
  `\n\n Session {i} \n\n` (native); REMINDER empty.
- Reminder arms (`restate_all`, `auto`, `oracle`): THREAD = session s only (all
  earlier sessions dropped: eviction is TEXT TRUNCATION, explicitly not the Multi-IF
  positional-eviction runner); REMINDER = the rendered ledger followed by a blank line.
- One generation per `history_eval_query` of the item (an item can have several);
  greedy; `max_new = 512`; per-generation deadline 300 s; hand-rolled bitwise
  deterministic `stencil.qwen3.Qwen3` (Qwen3-1.7B; Qwen3-4B only on the registered
  3b retry). Prior mentee answers are never generated: the thread is the dataset text.

## Candidate sentences (label-independent) and the common renderer

- Candidates = every sentence (by `focus3.sentences`) of every MENTOR line
  (`{mentor}:` prefix) in sessions 0..s−1, in order, tagged with (session, line,
  sentence index). Mentee lines are never candidates. No label is read.
- Renderer (identical for the three reminder arms):
  `Earlier mentor instructions restated verbatim:` followed by `- <sentence>` lines in
  CHRONOLOGICAL order. Budget E = 256 Qwen3 tokens INCLUDING the header. Packing: walk
  the arm's selected sentences NEWEST-FIRST and stop at the first sentence that does
  not fit (no skipping ahead); render the kept sentences chronologically. An empty
  selection renders nothing (REMINDER empty) and is counted.

## Arms

| arm | selected sentences |
|---|---|
| `history` | none (full history in the thread; the competence reference) |
| `restate_all` | every candidate sentence (newest-first packing decides what survives the budget) |
| `auto` | the LIVE set maintained by the frozen FOCUS-3 lifecycle runtime (below), texts of live rows |
| `oracle` | the label-derived live set: for every `[pivot, update]` in `dialogue["instructions"][s]`, the instruction text `topics.json["instructions"][pivot]["text"][update]`; rendered with the same header, budget and packing (newest = highest session of introduction) |

Only `oracle` reads `dialogue["instructions"]`, `session_regex`, `history_regex` or
session `type`; `tests/test_memorycode.py` asserts the other arms are built from
`text` alone.

## The `auto` adapter (frozen FOCUS-3 runtime on ordinary coding conversations)

`focus3.Runtime(FrozenClassifier(...))` with the registered frozen heads
(`data/classifier/model/ft` admission, `data/classifier/model/relations-v2/seed0`
relations, its frozen thresholds), CPU only.

- Initial scope: `runtime.task = "MAIN"` before the first update (label-independent;
  one default task scope per dialogue), so ordinary instructions receive scope `MAIN`
  instead of `None` (`focus3.scope_of`) and are admissible. Task-switch phrases
  ("Work on task A") do not occur in MemoryCode and are left as-is.
- Message stream: each MENTOR line of sessions 0..s−1, in order, is one message with
  `role="user"`; mentee lines are skipped (the runtime ignores non-user roles
  anyway). A mentor line with more than four sentences is fed as consecutive windows
  of at most four sentences (the runtime skips messages with > 4 sentences,
  `focus3.py:303`); each window is one `update` call with the same turn index.
  AMENDMENT 2 (2026-09-11, instrument fix before any GPU spend, Astra round 3): each
  window gets its OWN turn index. Row ids are `turn:start` with `start` relative to the
  window text, so two windows of one line under one turn collided and silently dropped
  rows (six admissions, five rows on a six-sentence line). `turns` records
  (session, line, window) per turn; chronology is unchanged. The auto phase was rerun.
- Overflow: the runtime skips a message when the register holds more than 16 rows
  (`focus3.py:303`). Overflow events are counted per item and reported; an item on
  which any overflow occurred is still scored (the live set is whatever the runtime
  holds), and the overflow count is a column of the error table.
- Live set for rendering = every row with `status == "live"` and scope `MAIN` or `*`,
  any kind, ordered by (admission turn, span start). AMENDMENT 2: `Register.live(task,
  kind)` also filters on `kind` ("sort" vs "all", a harness notion MemoryCode text does
  not carry), so the implementation applies the scope filter only; recorded so the
  discrepancy between this line's original wording and `memorycode.auto_live` is explicit.
- Non-vacuous check (before 3b launches): over the 16 SETUP items the `auto` adapter
  must admit at least one sentence and apply at least one `supersedes` / `cancels`
  relation; otherwise the adapter is INACTIVE, the screen does not launch, and that
  is the result.

## Outcome and checker

- Checker = the vendored official `compute_score(text, object_type, regex)` from
  `vendor/memorycode/code/evaluate_model_output.py` (with `extract_objects`), called
  exactly as `compute_dialogue_score` does for `history_regex`: for each generation,
  the mean over regex families of `compute_score`, ignoring `None` (object absent).
- PRIMARY per-item outcome (binary): STRICT compliance = every `history_regex` check
  that is applicable (non-`None`) scores 1.0 on every generation of the item. An item
  with no applicable check on some generation is scored on the remaining checks; an
  item with no applicable check at all is INAPPLICABLE and excluded from the primary
  with its count reported.
  AMENDMENT 3 (2026-09-11, before any GPU spend, Astra round 3): applicability is FROZEN
  from the task query before generation (`memorycode.required_families`, stored per query
  in `items.json`): class-side families (class, class decorator, method*, attribute) are
  required when the query names a class or method; function-side families when it names
  a function or names neither; variable, import and comment always. A generation that
  omits a REQUIRED parent object scores 0.0 on that family (omission is failure, the
  official `None` is kept only for non-required families). The primary cohort is fixed
  before generation: an item is INAPPLICABLE only when no query requires any of its
  families (0 of the 80 items); no arm's output can change the denominator.
  AMENDMENT 3b (Astra round 4): the query's required STRUCTURE (a class when the query
  names a class/method by whole-word match, else a function; `memorycode.required_structure`,
  stored per query in `items.json`) is enforced before strict scoring: a generation without
  the required class/function is strict-FALSE regardless of its convention scores.
- Secondary (descriptive): the native-style fractional history score per item.
- Convention compliance is the outcome; functional correctness is neither measured
  nor claimed (no code execution).
- Checker qualification (`tests/test_memorycode.py`): for each regex family present in
  the SETUP+SCREEN items (variable / function / class / method-annotation / comment /
  import / …): a compliant fixture, a violating fixture, a stale-value fixture (old
  convention), the required text inside a string literal or comment (must NOT count),
  and malformed code (scores 0). The family list is enumerated from `items.json`.
  Known limitation of the official checker, recorded on 2026-09-11 while writing the
  fixtures and NOT patched (the checker is used unmodified): comments are collected with
  `re.findall(r"#.*")` over the extracted code, so a `#` inside a string literal counts as
  a comment for the `comment` family. All other families read AST objects and are immune.
- Items enumerated 2026-09-11 (`items.json`): 320 candidate (dialogue, session) pairs, 108
  within 3,584 tokens, one per dialogue (the earliest fitting history session, s = 1..4);
  16 SETUP + 64 SCREEN items, 202 `history_eval_query` generations per arm in total.

## Error table for `auto` (all label-derived, reported, never gated)

- false admission: an admitted sentence from a session whose `type` contains no
  `instruction` component (pure filler), or from a mentor line that contains no
  instruction topic text (case-insensitive containment of the topic's first 6 words)
  — AMENDMENT 1 (2026-09-11, instrument fix with disclosure, before any GPU spend): the
  mentor scripts paraphrase the topic text ("For function names, we want you to start
  them with 'd_' as a prefix" for topic "always start function names with 'd_'"), so the
  6-word containment alone flagged every admitted instruction sentence as a false
  admission on the first 8 items. A line now STATES a topic when it contains the topic's
  first 6 words OR the topic's key literal (`scripts/memorycode_screen.topic_keys`: the
  affix of a `.*_m$` regex, the decorator/import name of a list regex, the object word of
  a boolean regex). The column stays descriptive and never gated.
- missed instruction: an `instruction-add` / `instruction-update` session among
  0..s−1 from which nothing was admitted
- missed update: a session with `instruction-update` whose newer text was admitted
  while the older text stayed live (no `supersedes` applied)
- stale-rule execution: a generation that satisfies a superseded regex of the same
  pivot and fails the live one
- overflow events; empty reminders; tokens used per arm.

## 3b competence qualification (16 SETUP items, one run)

Eligibility: `history` strict compliance ≥ 6/16 on Qwen3-1.7B. Retention headroom
(`oracle` − `history`) is reported, not gated. If 1.7B fails, ONE retry on Qwen3-4B
with the same four arms; if that fails too, the screen is INELIGIBLE and the 64 SCREEN
items are never opened.

## 3c screen (64 SCREEN items)

Primary: `auto` vs `restate_all`, exact McNemar on discordant items, two-sided p, and
the conservative paired interval of results/astra-research-blockers.md:199 (separate
97.5% Clopper-Pearson intervals for b/N and c/N, difference by union bound).
Descriptive: `auto` vs `oracle`, `history` vs everything, the error table.
Readings: ship `auto` if the lower bound on (auto − restate_all) is above −2 points
AND the error table is published; otherwise the package defaults to restate-all /
role rule and the automatic maintainer ships opt-in with its error table. N = 64 is a
SCREEN (8 wins / 0 losses one-sided p = .0039); a positive triggers a registered
N = 256 follow-up; a null is "not demonstrated at N = 64"; even perfect agreement cannot
establish matching within 2 points at N = 64 (0.98^64 = 27%).

## Budget, artifacts, stopping

Budget from the Exp 0 pilot (`memorycode` family: 4 longest SETUP prompts, 512-token
generation) × generations × 1.5. Artifacts under `results/memorycode-derived/`:
`items.json`, `setup/item-<id>.json`, `setup/summary.json` (eligibility line),
`64/item-<id>.json`, `64/summary.json`, `RESULTS.md`, `manifest.json`. Items are
written atomically as they complete; chunks ≤ 50 minutes; INCOMPLETE on budget
exhaustion, never rescued.

BUDGET (Exp 0 pilot 2026-09-11, `results/timing-pilot/memorycode.json`, 4 longest SETUP history
prompts, 2,446-3,002 context tokens, 512-token cap; co-resident at the time: the peer's E2 run
(~8 GB) and my own full pytest run): max 85.7 s/generation (one outlier; the other three
42-44 s), 11.7-12 tok/s, peak 6.46 GB allocated / 7.97 GB reserved. 3b ceiling = 1.5 × 85.7 s ×
(4 arms × 40 SETUP generations) = 5.7 GPU-h worst case (every generation at the cap); expected
about 2 h. 3c ceiling = 1.5 × 85.7 s × (4 × 162) = 23 GPU-h worst case: 3c launches only after
3b's measured mean seconds/generation gives a ceiling ≤ 8 GPU-h; otherwise 3c is amended
BEFORE launch to one generation per item (the first `history_eval_query`) and that amendment
is recorded here with the numbers.
