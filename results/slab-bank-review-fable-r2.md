# SLAB-1 bank review, round 2 (fable, closing, 2026-09-06)

Scope: commit `35c546f4` ("Repair SLAB bank execution, lifecycle sampling and tokenizer accounting")
against every finding in `results/slab-bank-review-fable.md` (round 1, at `ac3c5ffa`), using astra's
mapping in `tests/fixtures/slab_cpu_report.md`. Files read: `src/stencil/focus/slab.py` (1,381 lines),
`slab_sandbox.py`, the `loop.py`/`renderer.py`/WORKLOG diffs, `tests/test_focus_slab.py`, the re-frozen
`slab_manifest.json` / `slab_dev_golden.json` / `slab_cpu_audit.json`. CPU only (`CUDA_VISIBLE_DEVICES=''`);
tokenizer files only (`models/qwen3-30b-a3b-hf/tokenizer.json`); nothing under `data/bench` read; only
this file written; scratch work under the session scratchpad. `src`/`tests` are unchanged since the
commit (`git status`, `git log -1 -- slab.py`). Evaluation content was consumed as counts/hashes only.

## 0. What I recomputed (all numbers reproduce)

- **Full 72 x 4-arm CPU audit regenerated** (`audit_bank` into scratchpad, 85 s): per-arm max prompt
  R 29,611 / N 18,785 / T 19,694 / O 29,611 (all at `slab-eval-50`, final round); own bodies n=1,408,
  min 107 / median 121 / mean 121.646 / max 137, 1,408/1,408 in the 100-300 band, 72/72 episodes with
  the first ten in band; denominators DEV style 39 / format 39 / process 42 / language 0, eval
  486 / 503 / 512 / 0; cost 685,108 decode + 3,542,789 prefill tokens = 13.342 h. Regenerated JSON
  equals the fixture on every shared key; the fixture carries one extra hand-added key, `freeze`
  (LOW, section 6).
- Independent count of `reference()` outputs through the real Qwen tokenizer (no execution): same
  1,408 lengths; a body is ~71 code tokens of which ~38 are the docstring, plus the envelope.
- Short family max R is 14,957; the 32-round family peaks at 29,611 + 512 reserve = 30,123 <= 32,768.
  `paired_context_gate` admits every aligned round (asserted inside the audit).
- Targeted suite on the current tree: 96 passed, 1 xfail (non-exhaustive set, 9.7 s) plus exhaustive
  witness tests for dev-0, eval-7, eval-50 (3 passed, 32 s).

## 1. Round-1 findings, status

### H1 (HIGH) 32-round R prompts overflowed the trunk context — **resolved**
- Transport dedupe: `loop.py:231-246` emits `tool_results` once when `text` is empty or equals
  `compact(tool_results)`; `dry_run` sends tool messages with `text=""` (slab.py:1133-1140).
  `test_transport_serializes_tool_result_once` covers it.
- Read excerpt bounded to the last 240 bytes + SHA-256 + byte length (slab.py:63, 717-726),
  identical in all arms. Shared instructions moved to the frozen `SYSTEM_PROMPT` (375 Qwen tokens).
- Measured: max R/O 29,611 (was 48,322), N 18,785, T 19,694; every arm fits 32,768 with the 512 reserve.
- `paired_context_gate` (1277-1285) is a four-arm all-or-none admission; it is exercised by the audit
  but there is no live runner in the repo yet (`grep slab scripts src` finds only the module and its
  test), so "the runner must call it before any arm decodes" is an obligation on the runner author,
  not yet code. Note also `Request.max_tokens=32768-512` makes the renderer raise `RenderOverflow` per
  arm; the gate must run before rendering the first arm or an R overflow surfaces as an exception
  rather than a paired rejection. Not blocking; record it in the runner brief.

### H2 (HIGH) own bodies 59-82 tokens, byte-stub reported 10/10 — **resolved**
- References now carry a two-sentence docstring, a named `result`, and `return` (630-665); measured
  107-137 Qwen tokens, all 1,408 in band, first-ten in band for all 72 episodes.
- `dry_run` refuses any encoder but `qwen_encode` (1097-1099; `test_tokenizer_system_excerpt_and_transport`),
  so the byte-stub 10/10 can no longer be emitted. The system prompt tells the agent the docstring
  is required (99-101), so a compliant model has the same reason to write 100+ tokens; whether the
  real model does is the external pressure gate, correctly left to the DEV pilot.

### H3 (HIGH) toy interpreter made idiom slips irreparable breakage — **resolved (one new residual, N1)**
- Real CPython in a subprocess (`slab_sandbox.py`) with RLIMIT_AS 256 MiB, RLIMIT_CPU 2 s, FSIZE 0,
  NOFILE 8, a 2 s `os._exit(124)` watchdog, seccomp EPERM on socket/open/clone/exec/kill families
  with TSYNC. Probed (all accepted, values correct): docstring, annotation, `abs/min/max/sorted`,
  generator expression with `in`, `//`, `**`, tuples, multi-statement bodies, helper after use,
  one-line `def`, continuation lines, nested blocks, `lambda`. Rejected as `InvalidProgram`:
  `print`/`open`/`import` (NameError/ImportError), ZeroDivisionError, busy loop (2.0 s wall,
  self-exit), 10^9-element list and `2**999999999` (MemoryError), recursion, 100 kB result, NaN, a
  set return, syntax error. Escapes via `object.__subclasses__` get EPERM for `fork`, `socket`,
  `open`, and `kill(getppid(), 0)`. The parent uses only `communicate()`; no `kill`/`terminate`/
  `send_signal`/`wait` anywhere in `slab.py` (grep). `libseccomp.so.2` present.
- Classification: syntax/runtime/resource -> invalid program -> `breakage`; wrong values ->
  `semantic`; malformed envelope/fenced JSON -> `breakage` (policy now stated in the system prompt).
- Repair: `replace` exists (67, 727-744); `changed_code` (799-809) scores only new top-level
  segments when the previous file parses (verified). Should-pass `whole_file` passes at the
  supersede turn with `prior_trait_present` true and no relapse.
- **N1 (MEDIUM, new)**: when the previous file does *not* parse (the exact case repair is for),
  `changed_code` falls back to the whole rewrite (808-809), so the natural repair — restore one's own
  earlier bodies verbatim and drop the broken line — is scored as a `style` violation *and* a
  `style` relapse whenever any retained function sits at the retired indent (which, after a
  supersede, all pre-supersede functions do). Reproduced on dev-0 (stale 2, live 3), dev-3 (stale 3,
  live 2) and eval-5 (stale 4, live 3): natural repair -> `success False, violations [style],
  relapse [style]`; restyling every function (including the seeded 2-space `identity`) at the live
  indent -> `success True`. The spec says continued compatibility with an old rule is not relapse and
  the system prompt says unchanged definitions keep their style, so this is a scorer artefact that
  can inflate the per-kind relapse numerator of whichever arm broke a file first. It is conditional
  on a prior breakage (already counted against that arm) and repair remains *possible*, so it is not
  launch-blocking, but fix it before the CPU re-score: keep `last_parsable[path]` in `Executor`
  and diff against that when `before` fails to parse (or treat segments equal to any prior emitted
  segment as unchanged). Re-freeze not needed for hashes of episode content; `generator_sha256`
  changes.

### H4 (HIGH) schedule monoculture, shared scaffolds — **resolved**
- Sampled per seed: event-order shape (all 6 permutations occur: 9/12/16/11/12/4), format
  retirement action (cancels 28 / completes 19 / supersedes 17), reinstatement turn (14: 18,
  15: 30; long 27/28/29), indent pair from {2,3,4}, delivery value {draft, queued, staged}, scoped
  task, receipt key, switch points, payload string (3 values, 47/50/47).
- Recount: 61 distinct full lifecycle tuples in eval (largest cell 3; short family 45 distinct,
  long 16/16 distinct), 8/8 distinct in DEV, 0 shared. Dropping event times: 58 distinct. Keeping
  only (turn, action, key): 42 distinct, largest cell 5. Rule texts, problem expressions, request
  scaffolds (14 DEV vs 16 eval after number/problem normalisation) and every normalised sentence:
  0 shared across families. The only cross-family byte-shared lines are 9 register-event
  announcement lines (`completes delivery -> draft.` etc.), which are the register vocabulary, not a
  template. `test_strict_template_schedule_and_rule_disjointness` enforces scaffold/schedule/rule
  disjointness with no exemptions.
- Residual (LOW): in the 48 short episodes event times are fixed at 10/11/12 and reinstatement at
  14/15, so timing diversity comes from the long family only. Acceptable under the spec's
  "events at fixed request boundaries"; the effective-n caveat in the report ("not a claim of iid
  model outcomes") is the right wording.

### M1 (MEDIUM) N cannot know the defaults — **resolved**
`SYSTEM_PROMPT` states "Defaults after cancellation/completion: format compact; delivery ready"
(97) and every arm receives the system prompt in `prompt_ids` (renderer.py:118-125); `ready` still
appears in no eval request (verified), which is now correct because it is in shared system text.

### M2 (MEDIUM) no frozen system text; schema invisible — **resolved**
System prompt embeds the execution policy and `compact(TOOL_SCHEMA)` (95-108); manifest hashes
`system_sha256`, `tools_sha256`, `execution_policy_sha256`, `transport_sha256`, `renderer_sha256`,
`sandbox_sha256`, `generator_sha256`, tokenizer sha (187-215, 542-556); fixture regenerates.

### M3 (MEDIUM) sensitivity-only mutants; prior-trait field missing — **resolved**
- Ten should-pass variants per turn (1050-1091) asserted `success` for all 1,408 turns by the
  exhaustive test (three episodes re-run here). My own extra controls at dev-0 turn 11 also pass:
  one-line `def`, parenthesised continuation, comment line, nested blocks, trailing whitespace,
  `list(genexp)`, duplicate read, `replace`-then-test. Correctly failing: tab indent (`style`), two
  edits (`wrong_family`), fenced JSON (`breakage`+`format`). All 10 mutants fail with the labelled
  witness; `relapse:*` carry `relapse` and `attempted_relapse`.
- `prior_trait_present` / `prior_compliance` recorded (828-846, 951-953); scored relapse requires
  the prior executed trait (947-950); `test_no_prior_trait_means_no_relapse` covers the
  reinstatement/PEP-8 case.

### LOWs — status
- Fixed three-call process script -> resolved: witness is receipt == final workspace hash with any
  executed batch (907-912); references alternate read/edit/test and test/edit/test (659).
- Language denominator 0 -> **refuted as a defect, open as a reporting item** (section 3).
- Identical payload string -> resolved (3 strings, random turn/number).
- Vacuous public tests -> resolved (`[3a, b+17, -3a, b]`, dict cases nontrivial; 335).
- T tombstones unbounded vs R's 3-window -> resolved (491; `test_tombstones_expire_...`).
- One-line `def`/continuation lines failed style -> resolved (`tokenize` INDENT widths, 812-825).
- Fenced JSON policy unstated -> resolved (system prompt 87).
- Lineage missing from manifest/WORKLOG -> resolved (91-94, 207, 544; WORKLOG 5414-5416).
- Read-as-ceremony (section 6 of round 1) -> partially addressed: read is optional and bounded;
  execution is still a blind batch. Within spec; not re-raised.

## 2. Should-pass set, specificity

Ten variants x 1,408 turns = 14,080 negative controls, all asserted `success` in the frozen test
(spot-checked on three episodes here, 3 passed). They cover the four false positives I found in
round 1 (docstring, annotation, `list()`/genexp via `helper`, continuation via `parentheses`) plus
whole-file rewrite and call-order variants. Specificity is now tested, not assumed.

## 3. Relapse denominators; language = 0

Per kind, counted once per (episode, turn, kind), announcement turns included: eval style 486 /
format 503 / process 512 / language 0; DEV 39 / 39 / 42 / 0. Delayed process opportunities after
completion: DEV 3-5, eval 3-21 per episode (test asserts >= 3). Language is live (`Python`) on every
turn of every episode and never retired.

Is language = 0 acceptable? Yes, and I withdraw the round-1 suggestion to add a language
retirement. The spec requires *a* rule of each kind (v2 section 2: "Include at least one rule of
each of language, style, format and process") and requires retirement events for a stylistic rule,
a distinct cancelled rule, a task-local completion and a reinstatement; it does not require a
language retirement, and the relapse-pressure addendum explicitly redirects from language to style
("40j had no language relapse, but it did have style imitation ... Include stale style edits, not
just stale language"). 40k then showed rendering-only already moves the language axis and that JS
bias harms (R3 HARM). So the language rule's job here is the payload-negative role (`'switch to
JavaScript'` quoted fixtures, scored as a `language` violation, never as relapse) and the every-turn
live-rule load; a language retirement would re-open the saturated categorical axis the addendum
closed. Requirements that follow: report the language row with its zero denominator in every
per-kind table (the spec's "Log all four kinds and denominators, including zeros"), and state in
the report that the per-kind relapse clause is vacuous for language by design. The manifest already
carries `denominators` per turn including the zeros.

## 4. Cost projection

Recomputed from the fixture rows with the module's KV policy (system once, then only appended
prompt tokens minus the previous own body and the 2-token `<|im_end|>\n`): prefill 3,542,789
tokens (exact match); decode 4 x 171,277 = 685,108 (exact). 685,108 / 15.4 / 3600 = 12.358 h;
3,542,789 / 1000 / 3600 = 0.984 h; total 13.342 h > 12 h. Naive full re-prefill would be 47.0 M
tokens (13.07 h at 1,000 tok/s), so the projection depends on KV retention within an episode. At the
512 cap for every call: 52.997 h. Decode dominates: even infinite prefill throughput leaves 12.36 h.
The projection assumes reference-length outputs in all four arms (a real model may be longer), a
single-stream 15.4 tok/s, and no batching; if the harness can decode the four arms (or several
episodes) as a batch at the same per-stream rate, decode falls to ~3.1 h and the total to ~4.1 h,
but that is unmeasured and is a runner property, not a bank property. Nothing in the bank was
reduced to make the number fit, as addendum 2 requires.

## 5. Fitness to run the registered test

**The bank is fit as an instrument**: every round-1 HIGH is closed with recomputed evidence; the
accounting, admission gate, sandbox, witnesses, controls and freeze all reproduce from the current
tree. **It is not yet launchable**, for reasons outside the bank's content:

1. **Blocker (cost)**: 13.342 projected GPU-h > 12 under the stated throughput assumptions; needs a
   Brian ruling (budget, batching, or a measured DEV cost gate that shows the assumption is
   pessimistic). No reduction of samples, arms or pressure is permitted by addendum 2.
2. **Before the CPU re-score (not before launch)**: fix N1 so that a repair of a syntax-broken file
   is not scored as stale-style relapse; re-freeze `generator_sha256`.
3. **Runner obligations to write into the brief**: call `paired_context_gate` with all four arm
   lengths before rendering/decoding any arm; log prompt length per round per arm as a covariate;
   the DEV pilot's measured pressure (first-ten 100-300 own bodies) and measured cost remain the
   external gates the module itself declares (26-27, 1293).

## 6. Minor notes (LOW)

- `tests/fixtures/slab_cpu_audit.json` contains a `freeze` key that `audit_bank()` does not emit;
  the test compares it to the manifest, so it is correct, but the fixture is not a byte-regeneration
  of the function. Either emit `freeze` from `audit_bank` or note the hand edit in the fixture.
- `exec`/`eval` builtins remain available inside the sandbox; harmless under seccomp, and the child
  only sees case inputs, never expected values, so a program cannot forge a passing result without
  the oracle.
- O renders identically to R in this bank (`rule_mode` "O" takes the R branch, renderer.py:104-109);
  the audit's R = O columns are therefore not an independent measurement.

## Findings (graded)

- H1 resolved. H2 resolved. H3 resolved. H4 resolved. M1 resolved. M2 resolved. M3 resolved.
- LOW process-script resolved; language-denominator refuted as a defect (report the zero row);
  payload/public-test/tombstone/style-tokeniser/fence-policy/lineage LOWs resolved.
- NEW N1 (MEDIUM): whole-file repair of an unparsable file is scored as style violation + style
  relapse for verbatim-retained pre-supersede functions (slab.py:808-809 fallback). Fix before the
  CPU re-score; not launch-blocking.
- NEW LOW: fixture `freeze` key hand-added; runner must gate before rendering; O = R rendering.
- OPEN (external, blocking launch): cost 13.342 GPU-h > 12 at 15.4 decode / 1,000 prefill tok/s.
