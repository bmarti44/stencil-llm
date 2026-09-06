# SLAB-1 bank review (fable, one round, 2026-09-06)

Scope: commit `ac3c5ffa` — `src/stencil/focus/slab.py`, `tests/test_focus_slab.py`,
`tests/fixtures/slab_manifest.json`, `tests/fixtures/slab_dev_golden.json`, the WORKLOG entry —
against `results/focus-mechanism-composition-v2-astra.md` section 2 plus both addenda (40k
contingency; 12 GPU-h, pressure NOT reduced) and my `composition-v2-review-fable.md` M2-M5.
CPU only; no model launched; nothing under `data/bench` read; only this file written. `slab.py`
is unchanged since the commit (`git log -- src/stencil/focus/slab.py`); the targeted suite passes on
the current tree (77 passed, 112 s). Every number below was recomputed by running the module, by
counting with the real Qwen tokenizer (`models/qwen3-30b-a3b-hf/tokenizer.json`, `tokenizers`
0.22.2, tokenizer files only), or by arithmetic on the fixtures. Evaluation content was consumed
as counts and hashes only; DEV content was printed.

## 0. What reproduces

- 1,408 reference turns (56x16 + 16x32) all pass `check()`; 12,608 mutants = 1,408 x 8 fixed
  labels + 688 `relapse:style` + 554 `relapse:format` + 102 `relapse:process`. Exact.
- DEV golden accounting sums: prompt 484,818 / rendered 55,700 / generated 3,085 bytes. Exact.
- Manifest regenerates byte-identical to the fixture; seeds disjoint (`seed*10000 + i` vs
  `+1000+i`, slab.py:275); `public_view()` (108-123) strips `private`, `live`, `retired`,
  `denominators`, `t_text`; hidden cases never enter `Executor` (622-722) or the workspace
  (`materialize`, 441-464, writes only initial files + public cases); read tool is confined to
  `core.py`/`policy.py` (660-664). No benchmark content: all problems come from `_problem`
  (166-268) with our own wording. Own body is defined (docstring 9-11; manifest `own_body`,
  145): the literal decoder output including the tool JSON envelope, mask/bias ineligible. That
  closes my M3 the conservative way (tool-call = unmaskable; contingency cut).
- Relapse accounting matches M5: counted once per (episode, turn, kind) (737-801), denominators
  fixed by schedule (379-381), unexecuted = missing not clean (729-736), R/N compared only on
  jointly observed opportunities (1042-1055), no raw episode-count clause, no absolute completion
  floor (1058-1060; test at test_focus_slab.py:189-220). M2 and M5 closed. M4 (public vs hidden
  surface) closed by separate productions (public case vs hidden cases, 171-267) and the
  `hidden_only` mutant (868-875).

## 1. Fairness of R vs N (question 1)

No gold event or checker internal leaks into the agent surface. The register rows R sees are the
rule (`indent = 4`), which is also what the checker enforces; that is inherent to a rule-following
test, and T carries the same value in prose (373-378), so rendering does not win by wording.
Two real problems:

- **M1 (MEDIUM) — N cannot know the defaults.** After `completes delivery -> draft` (335) the
  live value becomes the task-A default `ready` (281). The string `ready` appears in no request
  text of any eval episode (verified: `"ready" in t.request` is False for all 64x turns); it is
  visible only as a version-0 row in R's rendering and in T's text. Likewise `cancels format ->
  verbose` (332) does not say what replaces it; N can only infer `compact` from the schema
  sentence in every request (360-362). So the process witness is unwinnable for N by
  information, not by memory. Fix: state the defaults once in shared text every arm sees (turn-0
  request or a frozen system prompt): "defaults: format compact; delivery ready".
- **M2 (MEDIUM) — the instrument has no system prompt and the tool schema never reaches the
  model.** `dry_run` builds `Request("", "tool_call")` (917) with `system=""`; `TOOL_SCHEMA`
  (52-68) is passed to `generate_once` as metadata only (loop.py:125-129, never rendered). The
  `python_subset` restriction (61-65) that decides breakage (see H3) is therefore invisible to
  the agent, and whatever system text the harness adds later is outside the manifest hashes
  (125-149). Freeze the system text in the bank and hash it.

N and T are not both specified here (there is no arm builder in this commit); the bank supplies
`t_text` only. T's "Not binding" list persists for the whole episode whereas R's tombstones expire
after three generations (renderer.py:52), so T carries slightly more revocation information than
R after round 13 (LOW; consistent with the spec's "prose may differ", but say it).

## 2. Pressure (question 2) — verified from generated episodes

| Requirement | Achieved | Where |
|---|---|---|
| 3-5 concurrent live rules incl. style | 4-5 every turn (indent is style) | 283-289, 343 |
| 10 retained own bodies of 100-300 tokens before first retirement | **0/640 eval, 0/80 DEV** reference bodies in band: 59-82 Qwen tokens (median 72). Byte stub reports 10/10 | 597-619; 1002-1007 |
| 2-3 task switches, return to earlier task | 3 switches, A->B->A->B; return at turn 7-9 | 293-308 |
| 1-2 overrides | supersede (10), cancel, complete, cancel+reinstate | 328-342 |
| delayed unrefreshed continuations | style: 4-5 delayed turns; format: 4; **process: 0 delayed in 50/64 eval and 8/8 DEV** | 331-336, 379-381 |
| relapse denominators per kind | style 6 / format 5 / process 1 / language 0 (16-round); 22 / 16-18 / 1-4 / 0 (32-round) | manifest `denominators` |

- **H2 (HIGH) — the registered pressure cannot be met by this bank.** The task elicits one
  single-return function inside a three-call envelope; the reference is 59-82 trunk tokens and a
  real model has no reason to write more (the interpreter rejects anything longer, see H3).
  Reading 2 of the spec ("fewer than 48/64 R episodes reach the first retirement with ten prior
  100-300-token own bodies -> INELIGIBLE") is then true by construction, and addendum 2 forbids
  reducing the pressure. `own_body_counts.first_ten_100_300` (1004-1006) is computed on whatever
  `encode` is injected: with the default byte stub it reads 10/10 for every DEV episode, which is
  the number a reader of `accounting.json` will see. Either widen the work per round (e.g. three
  related functions or a multi-key report per request, which needs H3's interpreter fix) so the
  reference lands at 100+ trunk tokens, or take a Brian ruling that narrows the pressure claim to
  the measured ~70-token bodies. In all cases label `own_body_counts` with the tokenizer and
  refuse to emit it under the byte stub.
- The only process-relapse opportunity in 16-round episodes is turn 12, the very turn whose
  request says `completes delivery -> draft.` (335, 371-372): it is an announcement-turn witness,
  not a delayed continuation; 32-round episodes have 1-4 delayed ones. Language is never retired
  (denominator 0 everywhere), so the per-kind relapse clause is vacuous for language and the
  quoted "use JavaScript" payload (366-370, identical string in every episode at turns 6 and 9)
  never sits on a discriminating witness. Add a return-to-A after completion in the 16-round
  family and vary the payload (LOW-MEDIUM; folded into H4's fix).

## 3. Hidden checkers and mutants (question 3)

- **H3 (HIGH) — the interpreter converts ordinary Python into irreparable breakage.** `evaluate`
  (471-594) rejects: a docstring or any second statement (493-494), an annotation (487),
  `abs/min/max/list/sorted` (578-588: only `sum`/`len`), `in`/`not in` (549-550), `//`, `/`,
  `**`, tuples, generator expressions. Probed on DEV-00 turn 0: a correct function with a
  docstring, with `x: list`, or written as `[... for v in list(x)]` each scores
  `{process, breakage}`; a correct body with a continuation line scores `style`. Worse, the edit
  op is append-only (673-684) and a redefinition makes the whole file invalid (495), so one slip
  at turn k poisons every later turn in both public tests (699-707: no receipt ever again ->
  `process` violation) and hidden cumulative checks (805-814: `breakage` every turn). Verified: a
  turn-0 docstring, then a perfect turn 1 -> `{process, breakage}`; a repair attempt by
  redefinition -> same. The spec says "later normal rounds may repair them"; here nothing can.
  Consequences: (i) `breakage`, the paired safety gate, is dominated by idiom rather than by the
  register; (ii) final success (1032-1033) and hence the primary discordance is decided by which
  arm slipped once, not by rule state. Fix: accept the common idioms (at minimum docstring,
  annotations, `abs/min/max/sorted/list/any/all`, `in`, `//`, tuples, genexps, multi-statement
  bodies) or run real CPython in a resource-limited subprocess as the spec's "native tests"
  intended; add a `replace` edit op so repair is possible; and classify unsupported syntax as
  `semantic`, never `breakage`.
- **M3 (MEDIUM) — mutants prove sensitivity only.** Each label is one minimal perturbation of the
  reference (831-898): JS text, 3-space indent, extra report key, dropped `test` call, wrong path,
  constant return, `{`. Only `hidden_only` (return the public expected value) is non-trivial. There
  is no should-pass set, so specificity is untested, and section 3 above found four false
  positives in five probes. Add a negative-control set per turn (renamed variable, reordered
  arithmetic, parenthesised expression, docstring, blank lines) that must score success.
- Witness discrimination: `relapse:style` requires the exact stale indent (764, 773), so a 3-space
  bug is a violation, not a relapse — good. But after the reinstatement at turn 14 the stale value
  is 4, which is also the PEP 8 prior: an arm that never adopted `indent=2` at all scores
  "relapse" at 14-15. The spec requires reporting whether the obsolete trait appeared in prior own
  bodies and scoring attempted vs executed separately; `attempted_relapse` exists (739, 764) but
  no prior-own-body field is recorded. Add `prior_trait_present` (did any earlier executed edit of
  this arm carry the stale value) and `prior_compliance` (did it ever emit the now-live value) to
  `check()` and condition the relapse analysis on them (MEDIUM, part of M3).
- The process witness (790-797) requires exactly `[read, edit, test]` with the receipt hash equal
  to the final workspace hash, i.e. the register's `receipt=test-after-edit` rule is scored as
  "followed the fixed three-call script", conflating a rule with request instructions (LOW).
  Public tests are vacuous for transforms/reports (`[]` -> `[]`, 171, 209; `return []` passes),
  so the receipt gives the agent no self-correction signal (LOW).

## 4. DEV/eval disjointness (question 4)

- **H4 (HIGH) — disjoint by template is nominal; the eval bank is a schedule monoculture.**
  Template IDs differ only by the `dev:`/`eval:` prefix (402). Normalising numbers and the single
  wording phrase (`Extend the workshop` vs `Implement the next service operation`, 352-356), 18 of
  36 request scaffolds are byte-shared across families; the problem productions are disjoint (0
  shared) but the lifecycle schedule — keys, values, `supersedes` at 10, `cancels` at 11,
  `completes` at 12, `cancels+reinstates` at 14, task-A scoping of `delivery` — is identical in
  every DEV and every 16-round eval episode (298-306, 328-342). Across the 64 eval episodes there
  are 15 distinct (length, event schedule) cells, one of which holds 48 episodes; with greedy
  decoding those 48 differ only in the constants `a,b` and the switch turn (9 combinations). The
  spec's iid power table and the exact sign test assume exchangeable independent pairs; under
  near-deterministic replicates the effective n is closer to the number of cells than to 64, and
  the binomial p is anti-conservative. Fix in the generator: draw per seed which key is
  superseded/cancelled/completed, the event turns (within the challenge window), the values
  (indent 2/4/tab-free 3, verbose/compact, draft/ready plus one alternative), which task carries
  the scoped rule, the payload string and its turns; give DEV a schedule family that eval never
  uses. Then "disjoint by template" is true and the power table means something.

## 5. Determinism, manifests, lineage (question 5)

Deterministic (`random.Random(episode_seed)`, 276; manifest regenerates exactly). The manifest pins
`generator_sha256` of the module bytes (430), so any edit — including the fixes above — must
re-freeze the fixture; that is the intended freeze, but note that the frozen hashes cover episode
content and not the rendered prompt or system text (see M2). The lineage line is in the module
docstring (1-2) but absent from the manifest and from the WORKLOG entry, which Brian's rule
requires before registration (LOW: add `data_lineage` to the receipt and one line to WORKLOG).
`rejection_policy` recorded; no rejections occurred. No public benchmark content.

## 6. Realism (question 6)

This is a renderer/state-tracking exerciser, not a coding-agent task. The three calls are executed
as a blind batch (the read excerpt only arrives next turn, 931-941), so "read the target" is
ceremony; edits are append-only into two files; functions are `step_i(x)`; the requests speak the
register's vocabulary (`cancels format -> verbose.`, 371) rather than a user's; the public tests
are `[]`. Within the spec's "tiny in-process modules" this is allowed, but H3 shows where the toy
bites: the interpreter, not the trunk, decides breakage. If Brian wants "something a real coding
agent would face", the minimum is H3's fix plus a `replace` op and interactive read-then-edit
turns; the rule machinery does not need to change.

## 7. Context growth with the real tokenizer (question 7)

Byte counts in the golden are ~3.0 bytes per Qwen token. Measured by replaying `reference()`
outputs through `generate_once` with the Qwen tokenizer injected (`dry_run(encode=...)` for DEV;
a counts-only replay for `slab-eval-48`):

| Round | R prompt (tokens) | N estimate (R minus rendered rule blocks) | note |
|---|---:|---:|---|
| 15 (16-round DEV-00 final) | 19,960 | ~15.8k | fits |
| 15 (32-round eval-48) | 20,752 | 15,799 | |
| 21 | 32,179 | 25,150 | R crosses 32,768 at round 22 (34,288) |
| 26 | 40,369 | 31,936 | R crosses the pinned `max_position_embeddings` 40,960 at round 27 (41,811) |
| 31 (final) | 48,322 | 38,478 | N fits 40,960; R does not |

- **H1 (HIGH, launch-blocking) — the 32-round family overflows in R only.** Rounds 27-31 of every
  32-round episode (16/64 pairs) cannot be generated in R at the model's configured 40,960
  (rounds 22-31 at a 32k budget) while N fits. Under `paired_clauses` an unobserved scheduled
  opportunity sets `complete=False` (1045-1046, 1072), so the run reads INCOMPLETE by
  construction; if the harness instead scores the overflow as a failed final turn, N wins those
  16 pairs for a reason that has nothing to do with rules. Where the tokens go per round (eval-48,
  round 20): envelope 1,938 = rule block 352 + user part 1,582, of which the tool results appear
  twice — once as the tool message `text` (`compact(feedback["results"])`, slab.py:936) and again
  as `tool_results` (937), both serialised inside `compact([...])` at loop.py:220-229 with JSON
  escaping — 676 tokens each — plus the request. The read excerpt (up to 2,048 bytes of the growing
  file, 669) is re-sent every round. Removing the duplicate alone saves ~500-700 tokens per round
  (~16-17k over 32 rounds), bringing the final R prompt to roughly 31-32k: fits 40,960 with margin,
  borderline at 32k. Also cap the read excerpt to the tail (last ~600 bytes) or make the read
  optional after turn 0. The rendered rule block retained in every historical turn (history_ids
  accumulates the whole envelope, loop.py:289-303; ~10.5k tokens over 32 rounds) is the R-N
  context asymmetry the design accepts, but log prompt length per round per arm as a covariate.
- Generation cap: reference outputs are 59-82 tokens against a 512 cap; no truncation risk.
- Cost: prefill of 20k-48k tokens per call on a MoE trunk is unmeasured; the bank's byte-stub
  accounting cannot certify the 12 GPU-h ceiling (the module says so, 26-27). Not re-argued here.

## Findings (graded)

- HIGH — H1: 32-round R prompts reach 48,322 Qwen tokens (>40,960 from round 27; >32,768 from
  round 22); N ~38.5k fits. Cause: tool results serialised twice per envelope (slab.py:936-937,
  loop.py:220-229) plus a full-file read excerpt every round. Guarantees INCOMPLETE or hands N 16
  pairs. Dedupe and trim before any GPU minute; re-measure with the real tokenizer.
- HIGH — H2: own bodies are 59-82 trunk tokens; 0/640 in the registered 100-300 band; the
  byte-stub `own_body_counts` reports 10/10. Reading 2 (INELIGIBLE pressure) is true by
  construction under addendum 2. Widen the per-round work or get a ruling; label the field.
- HIGH — H3: the expression interpreter (471-594) plus append-only edits (673-684, 495) make a
  docstring, annotation, `abs`/`max`/`in`/genexp a permanent, unrepairable `breakage` that fails
  every later turn in both surfaces; the paired breakage gate and the primary are then decided by
  idiom slips, not rule state. Widen the subset or run CPython in a sandbox; add `replace`;
  never score unsupported syntax as breakage.
- HIGH — H4: one lifecycle schedule in 48/64 eval episodes and in all DEV episodes; 15 cells in
  64; 18/36 request scaffolds byte-shared across families. "Disjoint by template" is nominal and
  the iid power/sign test is anti-conservative. Randomise keys/values/turns/scoped task per seed;
  give DEV its own schedule family.
- MEDIUM — M1: post-completion default `ready` (and the cancel replacement) is visible only to
  R/T; N is information-starved on the process witness. M2: no frozen system text; tool schema and
  `python_subset` never reach the model; hashes exclude it. M3: mutants are one-perturbation
  sensitivity checks with no should-pass set (4 false positives in 5 probes); relapse after
  reinstatement conflates PEP 8 prior with stale execution; the spec's prior-own-body trait field
  is missing.
- LOW — process witness = fixed three-call script; language denominator 0 everywhere; identical
  payload string every episode; vacuous public tests; T tombstones unbounded vs R's 3-window;
  one-line `def` and continuation lines fail style; fenced JSON = breakage (state the policy);
  lineage line missing from manifest/WORKLOG.

Verdict: the accounting, leakage boundaries, own-body definition and paired clauses are correct
and every number reproduces; M2-M5 from my v2 review are closed. But as an instrument the bank
cannot yet run the registered test: the long family overflows the trunk's context in R only (H1),
the registered pressure is unreachable by design (H2), the checker's toy interpreter makes
breakage a coin flip on Python idiom with no repair path (H3), and 64 pairs are mostly one
schedule (H4). All four are generator/transport fixes on CPU; none needs a GPU minute, and each
requires re-freezing the manifest and golden.
