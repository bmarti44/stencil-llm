# Check 49 accuracy review — independent, Opus at maximum reasoning

2026-09-07 · reviewer: Opus 5 (Brian's 2026-09-06 reviewer ruling) · one round · no code edits ·
CPU only, no GPU touched, no `RUNNING.flag`/container/process touched, nothing read under `data/bench`.

Scope reviewed: `results/quick-checks/check49/README.md`, `records.jsonl` (272 lines, all re-scored
independently), `summary.json`, `parity.json`, `cached-parity.json`, `audit.json`, `fit.jsonl`,
`adapter-manifest.json`, `contract.json`, `registration.md`, `data.json`, run/audit logs,
`scripts/focus_check49.py` (625 lines, read in full), `tests/test_focus_check49.py`, freeze
`166598bb`, the brief `results/handoff/briefs/check49-brief.md`, and
`results/dense-focus-research-astra.md`.

---

## 0. Verdict in one paragraph

Every number in the report reproduces exactly from the records — I recomputed all of them
independently and found **zero arithmetic or transcription discrepancies**. Provenance is clean:
reading before inference, adapters frozen before the episodes, bitwise OFF parity. The NO-GO status
is *mechanically* correct: three of five registered bars fail and the frozen `analyze()` evaluated
them without late edits. But the **primary endpoint is scientifically inadmissible**. SWITCH is the
only cell in the whole design where the carrier and the retained transcript are in conflict, and it
is won by the transcript in **36/36 decisions across all three arms** — including the every-request
text comparator. The check registered no positive control that the cell is winnable by anything. So
"M 0/12 all-active" is not a fact about adapters; it is a fact about minimal-pair in-context copying
on a 4B model. Meanwhile the check does contain a strong, registered, controlled positive that the
report under-reports: on the admissible decisions M beats the swapped-label control **8 wins / 0
losses, exact one-sided p = 0.0039**, at zero rule-carrier tokens, 1.35 % *faster* than rendering,
7/8 token-identical to OFF on unrelated work, with bitwise-complete release. **The weight-side line
must not close on this check.**

---

## 1. Freeze and provenance — VERIFIED CLEAN

| Claim | My verification | Result |
|---|---|---|
| Reading written before inference | `166598bb` (2026-09-07 00:22:08) adds `registration.md`, `contract.json`, `data.json`, `cpu-validation.json`, and the entire 625-line `scripts/focus_check49.py` **including the `analyze()` decision function and `bars` dict** (`scripts/focus_check49.py:583-611`). `git diff 166598bb HEAD -- scripts/focus_check49.py` is empty; working tree clean. `plan/LEDGER.md:1219-1227` shows the write-ahead sequence CPU-WRITE-AHEAD → RECIPE FROZEN → FIT/SETUP RECEIPT → COMPLETE. | **Pass** |
| Recipe hash-bound to the run | `cpu-validation.json` `code_sha256=384a23c7…` and `data_sha256=cba72991…`; I recomputed both against the current files — both match, and `run()` asserts them at `scripts/focus_check49.py:308-309`. | **Pass** |
| Adapters frozen before the episodes | `save_pretrained` at `scripts/focus_check49.py:494-501`, before parity, mechanism, preflight and all 180 trajectory calls. On-disk mtime 2026-09-07 00:24:01; `evaluation_preflight.spent_s = 128.596` s, i.e. the adapters existed ~2 min into an 850 s run. I re-hashed all six adapter files: **6/6 byte-count and SHA256 match `adapter-manifest.json`**, and the two `adapter_model.safetensors` SHAs match README:52-53 verbatim. | **Pass** |
| Single shot, no overwrite | `assert not (OUT/'summary.json').exists()` and `assert not ADAPTERS.exists()` (`scripts/focus_check49.py:310-311`); records journaled with `fsync` per call (`scripts/focus_check49.py:45-49`). 272 lines in `records.jsonl`, `assert len(records)==272` at `scripts/focus_check49.py:547`. | **Pass** |
| Trunk untouched | `summary.trunk_tensor_hash_diffs = []`, `trunk_gradient_nonnull = []`, `base_file_hash_diffs = []`. I re-hashed all 13 frozen base files against `contract.frozen_files`: **0 mismatches now**. | **Pass** |
| Adapter-OFF parity 16/16 exact | Original `parity.json`: 16/16 `off_pristine_equal` (pre-fit pristine == post-fit OFF == direct-base-layer bypass), 16/16 `on_effect`, and exactly **one** `greedy_token_equal` false (`baseline/python/2`). Because that row's `off_hash == pristine_hash`, the difference is *not* OFF-vs-pristine; it is full-prefix teacher-forced argmax vs incremental cached greedy — a bf16 kernel-path artifact. `cached-parity.json` (auditor committed at `7447a43f` **before** launch; I read `audit_parity.py` in full) replays the same 16 saved streams with a `DynamicCache` matching the generation path and forces the saved token at each step: I independently rechecked all 16 rows for `off.predicted == saved == pristine.predicted` **and** `off.logits_sha256 == pristine.logits_sha256` — **0 failures**, including `baseline/python/2`. | **Pass** |
| Data lineage | `prepare()` asserts pairwise family disjointness across fit/setup/eval banks (`scripts/focus_check49.py:216-218`). Fit families {offset, scale, floor, cap, greater, substitute, filter, count, sumshift, head, tail, repeat, pad, distance, branch, empty}; setup {square, reverse, join, negate, between, lengths, product, ends}; eval {prefix, rotate, unique, gaps, chunks, runs, indices, windows, alternate, flatten, signruns, histogram}. Disjoint. No `data/bench` reference anywhere in the three scripts. Mechanism results feed no selection (`analyze()` never reads them). | **Pass** |
| Honest failure record | `parity-audit.log` preserves the first auditor attempt's `AssertionError` at `audit_parity.py:28` — it yielded to another Stencil flag *before* model loading, exactly as README:63 says. All 19 relative links in README.md resolve. | **Pass** |

**Nothing in the provenance chain is broken.** The one original `token_diffs=1` is correctly
characterised as a cross-path numerical diagnostic, the original `parity.json`/`summary.json` are
preserved unrewritten, and the resolution is a zero-generation tensor replay.

---

## 2. THE CRITICAL CONFOUND — the SWITCH endpoint is inadmissible

### 2.1 Does the check test what it claims? Plainly: **partly. The primary endpoint does not.**

The design has exactly **one** cell in which the carrier and the model's own retained transcript
disagree — SWITCH. Everything else is either carrier-only or carrier-agrees-with-history:

| Cell | Carrier vs history | What it can show |
|---|---|---|
| SET | no history at all | clean carrier test |
| cold probe | neutral 2-message history, **no code** | clean carrier test |
| HOLD, BACK | carrier **agrees** with history | nothing — confounded by construction |
| SWITCH | carrier **conflicts** with history | the only discriminating cell |
| CLEAR | carrier removed, history retained | tests transcript persistence, not the carrier |

Empirically, HOLD/BACK are confirmed uninformative: M (adapter, no text) and T (text, no adapter)
score **identically** — 11/12 language at both HOLD and BACK, and the single loss in each is
episode 11's length truncation, not a language error.

### 2.2 Three SWITCH decisions per arm, rendered prompt and generation, literal

The SWITCH task is always the **same task family** as the two preceding answers with **one numeric
parameter incremented** (`scripts/focus_check49.py:119` `k = i+2`; `:145` one family per episode).
The maximum-likelihood continuation is therefore to copy the previous answer and bump the constant.
That is precisely what happens, in every arm.

**Arm M (adapter selected, no rule text)** — system message is bare
`"Return only one complete function with the requested name. Use a fenced code block. No explanation or examples."`,
`rule_carrier_positions = 0`:

```
episode/0/M/SWITCH   adapter = js   expected = js
  [user]      Implement eval_prefix_2(xs): Return running sums of integer xs, each increased by 4.
  prev answer ```python\ndef eval_prefix_1(xs):\n    return [x + 3 for x in xs]\n```
  GENERATED   ```python\ndef eval_prefix_2(xs):\n    return [x + 4 for x in xs]\n```     -> language=python  FAIL

episode/3/M/SWITCH   adapter = python   expected = python   (js-initial episode)
  prev answer ```javascript\nfunction eval_gaps_1(xs) {\n  return xs.slice(1).map((val, i) => (val - xs[i]) * 3);\n}\n```
  GENERATED   ```javascript\nfunction eval_gaps_2(xs) {\n  return xs.slice(1).map((val, i) => (val - xs[i]) * 4);\n}\n```   -> language=js  FAIL

episode/9/M/SWITCH   adapter = python   expected = python
  prev answer ```javascript\nfunction eval_flatten_1(xss) {\n  return xss.reduce((acc, xs) => acc.concat(xs.filter(arr => arr.length >= 3)), []);\n}\n```
  GENERATED   ```javascript\nfunction eval_flatten_2(xss) {\n  return xss.reduce((acc, xs) => acc.concat(xs.filter(arr => arr.length >= 4)), []);\n}\n```   -> language=js  FAIL
```

**Arm T (every-request rule rendering in the system message, no adapter)** — the rule *is* present
and *is* the switched rule; `rule_carrier_positions = 12`:

```
episode/0/T/SWITCH   adapter = None   expected = js
  [system]    Return only one complete function with the requested name. Use a fenced code block. No explanation or examples.
              Live rules: (1) Write all code in JavaScript.
  [user] eval_prefix_0 ... [assistant] ```python ... [user] neutral note [assistant] OK
  [user] eval_prefix_1 ... [assistant] ```python\ndef eval_prefix_1(xs):\n    return [x + 3 for x in xs]\n```
  [user]      Implement eval_prefix_2(xs): Return running sums of integer xs, each increased by 4.
  GENERATED   ```python\ndef eval_prefix_2(xs):\n    return [x + 4 for x in xs]\n```     -> language=python  FAIL

episode/3/T/SWITCH   Live rules: (1) Write all code in Python.        expected = python
  prev answer function eval_gaps_1(xs) { const result = []; for (let j = 0; ... 3 * (xs[j+1]-xs[j]) ... }
  GENERATED   function eval_gaps_2(xs) { const result = []; for (let j = 0; ... 4 * (xs[j+1]-xs[j]) ... }   -> language=js  FAIL

episode/9/T/SWITCH   Live rules: (1) Write all code in Python.        expected = python
  prev answer ```javascript\nfunction eval_flatten_1(xss) {\n  return xss.flatMap(arr => arr.length >= 3 ? arr : []);\n}\n```
  GENERATED   ```javascript\nfunction eval_flatten_2(xss) {\n  return xss.flatMap(arr => arr.length >= 4 ? arr : []);\n}\n```   -> language=js  FAIL
```

**Arm X (swapped adapter labels, no text)** — the mirror image, and the tell:

```
episode/1/X/SWITCH   adapter = js (swapped)   expected = python
  prev answer ```python\ndef eval_rotate_1(xs): ... xs[3 % n:] + xs[:3 % n]
  GENERATED   ```python\ndef eval_rotate_2(xs): ... xs[4 % n:] + xs[:4 % n]   -> language=python  PASS

episode/6/X/SWITCH   adapter = python (swapped)   expected = js
  prev answer ```javascript\nfunction eval_indices_1(xs) { ... }
  GENERATED   ```javascript\nfunction eval_indices_2(xs) { ... }             -> language=js  PASS

episode/9/X/SWITCH   adapter = js (swapped)   expected = python
  prev answer ```python\ndef eval_flatten_1(xss): [num for arr in xss for num in arr if len(arr) >= 3]
  GENERATED   ```python\ndef eval_flatten_2(xss): [num for arr in xss for num in arr if len(arr) >= 4]   -> language=python  PASS
```

X "passes" SWITCH 10/12 **while holding the wrong adapter**, purely because its own history is in
the target language. I checked the predictor *"the SWITCH language equals the language of that
arm's own previous answer"* against all 36 SWITCH decisions: **36/36 correct** (the two apparent
exceptions, `episode/10/X` and `episode/11/*`, are cap-96 truncations scored `language='unknown'`;
their literal text still continues the arm's own language). The carrier explains **zero** additional
variance in this cell. The report's own per-stage row (README:34) already contains the proof and
does not draw the inference: M 12/11/**0**/11, T 12/11/**0**/11, X 0/0/**10**/0.

### 2.3 Did the registered eligibility gate pass, and what does it imply?

Yes — and that is exactly the problem. `scripts/focus_check49.py:413-420`:

```python
floors = {
    m: sum(r["success"] for r in baseline if r["id"].startswith(f"baseline/{m}/"))
    for m in MODES
}
floors["default_python"] = sum(
    r["language"] == "python" for r in baseline if r["id"].startswith("baseline/None/")
)
...
if min(floors.values()) < 7:
    raise Stop("INELIGIBLE", "unmodified setup language/competence floor failed")
```

I recomputed: `{'python': 8, 'js': 8, 'default_python': 8}` — all three floors are **8/8, perfect**.
But `baseline` is built at `scripts/focus_check49.py:410-412` from `messages(t, mode=mode)` with
**no history**. The gate certifies *cold single-turn cueing only*. It never establishes that any
carrier can flip the mode against a retained transcript. That property is never measured anywhere
in the check except in the arms themselves, where all three fail.

The one place it could have been caught before the arms opened was the mechanism block
(`scripts/focus_check49.py:502-511`), which runs the five-decision schedule on setup families — but
**with the adapter only, never with text**. `mechanism/python/2` (switch to JS, adapter=js) returned
Python; `mechanism/js/2` (switch to Python, adapter=python) returned JavaScript. Both directions
failed in the setup phase, before the trajectories launched, and the diagnostic had no text arm to
reveal that the cell itself was unwinnable.

Astra's own design document anticipated the mechanism and then did not guard the right cell:
`results/dense-focus-research-astra.md:146` — *"A separate cold-HOLD probe … removes old answer
demonstrations, **distinguishing external control from copying previous answers**"*; and `:85` —
*"Same-history replay … preserves the model's own linguistic/code demonstrations; CLEAR still has to
beat those without deleting them."* A cold control was registered for HOLD and for CLEAR. **None was
registered for SWITCH.**

### 2.4 Plain answer

**The check is NOT INELIGIBLE under its own registered gate** — the gate is stated at
`registration.md` ("Setup requires cued executable/language successes>=7/8 per mode and default
Python>=7/8") and it passed 8/8/8. Calling it INELIGIBLE would be inventing a bar after outcomes.

**But GO condition 2 (the primary endpoint) is inadmissible**, because its conjunction contains a
decision that no arm in the experiment — including the reference carrier — can pass, and the check
carries no evidence that it is passable at all. The correct classification is: **eligible, completed,
and informative on SET / release / competence / cost; uninformative on SWITCH and therefore on
"all-active".** "M 0/12" and the M–X sign test (p = 1) carry no information about adapters. The
narrow factual residue that *does* survive is: *this* adapter at *this* dose does not override its
own transcript — and neither does system-message rendering.

---

## 3. The four claims, separated

I recomputed each from `records.jsonl`. Every README figure reproduced exactly (M/T/X active
language 34/34/10; semantics 33/37/29; joint 25/28/7; syntax 3/3/11; truncations 3/3/7;
presentation 3/6/7; 60-decision execution 41/46/36; syntax 4/4/14; truncation 4/4/9).

### SET — **YES, causally, with the registered control. This is the real positive.**

Same prompt, zero rule text, only the selected adapter differs:

```
episode/3/M/SET   adapter=js       ```javascript\nfunction eval_gaps_0(xs) {\n  return xs.slice(1).map((val, i) => (val - xs[i]) * 2);\n}\n```
episode/3/X/SET   adapter=python   ```python\ndef eval_gaps_0(xs):\n    return [2 * (xs[i+1] - xs[i]) for i in range(len(xs)-1)]\n```
```

M SET language **12/12**, X SET language **0/12** — an exact mirror. Cue-free base default is Python
8/8 (`baseline/None`), so the six JS-initial SETs are genuine flips of the base default. This is a
clean, controlled, text-free mode selection.

**Caveat (MEDIUM, M3):** the effect is carried by the **JS adapter alone**. The Python adapter's
target coincides with the base default, so it has **zero informative trials** — every "Python
adapter works" observation is indistinguishable from adapter-OFF. `fit.jsonl` corroborates: the
Python adapter starts at loss 0.218 (nothing to learn) and ends 0.081; the JS adapter starts at
2.309 and ends 0.498. README:34's "M selects the current adapter without text" should read "the
JavaScript adapter selects its mode against the base default; the Python adapter is untested."

### HOLD — **not demonstrated in the informative configuration; cold-HOLD 10/12 is real but is a re-run of SET.**

At HOLD the adapter and the history agree, and M and T are identical (11/12 each). The cold probe is
the only clean HOLD evidence, and I verified its history contains **no code**:

```
cold/3   adapter=js   expected=js
  [system] Return only one complete function ... No explanation or examples.
  [user]   Pause for a note: the meeting is on Thursday. Acknowledge with OK.
  [asst]   OK
  [user]   Implement eval_gaps_5(xs): Return consecutive differences xs[j+1]-xs[j], each multiplied by 7.
  GEN      ```javascript\nfunction eval_gaps_5(xs) {\n  return xs.slice(1).map((val, i) => (val - xs[i]) * 7);\n}\n```   PASS
```

**Is cold-HOLD real or explained by retained history? Real — there is no code history to explain
it.** Cold language is **12/12** (I recomputed); the two "failures" in the 10/12 headline are pure
task-semantics misses (episodes 0 and 9), not control failures. Six of the twelve are informative
(the JS-initial ones flip the base default); all six pass.

**But cold-HOLD is structurally the same measurement as SET plus one neutral turn.** It shows the
adapter's control survives an unrelated exchange. It does **not** show persistence across
intervening *code* content, because the only cell that would test that (SWITCH) is unwinnable and
the confounded cell (HOLD) is uninformative. Read it as "selection is not disturbed by neutral
content", not as "the weight carrier HOLDs".

### SWITCH — **not tested.** See Section 2. 0/12 for M, 0/12 for T, and the transcript wins 36/36.

### CLEAR — **the carrier's release is bitwise perfect; the reported failure is transcript persistence, and rendering fails it identically.**

Two separate things are being scored under one bar (`scripts/focus_check49.py:606`):

1. **Carrier release — perfect.** M's CLEAR runs under `model.disable_adapter()`
   (`scripts/focus_check49.py:533` gives `selected=None` at CLEAR). The `replay/{i}` reference
   re-runs the identical literal history with the adapter off: **12/12 reproduce M's CLEAR
   token-for-token**. Combined with 16/16 cache-matched OFF/pristine/saved-greedy parity, release of
   the weight carrier is demonstrated to the bit.

2. **Transcript persistence — charged to the adapter, but it is not the adapter's.** I recomputed
   the stale sets:

   | Arm | stale episodes (own CLEAR language == initial mode while fresh-OFF differs) |
   |---|---|
   | M (adapter, released) | **1, 3, 5, 7, 9** |
   | T (text, rule removed) | **1, 3, 5, 7, 9** — *identical* |
   | X (swapped adapter) | none (its history is in the opposite language, so it is never "stale") |

   README:38 states the mechanism correctly (*"Identical OFF computation does not erase earlier
   emitted examples from the transcript"*), but the scoring row at README:16 and the headline
   attribute "five stale JavaScript impositions" to the adapter. **They are transcript
   impositions, and every-request rendering produces exactly the same five.**

Also: CLEAR success is capped by the reference. Fresh-OFF writes Python 12/12 but **executes only
10/12**, and the bar requires the reference to succeed too, so 11/12 needed 10/12 max headroom on the
reference alone. The observed 4/12 is genuinely low, but 5 of the 8 misses are the shared-with-T
stale set and 2 more are reference failures.

---

## 4. The "10 executable losses" — classification, and the check-40k comparison

### 4.1 They are not 10 independent losses. They are 2 episodes.

`analyze()` counts harms per *decision* (`scripts/focus_check49.py:594-597`). The registered
independent unit is the episode: `registration.md` — *"Parameter variants within a family are
related; the independent unit is the 12 episodes, not individual calls."* Because every decision in
an episode copies the previous answer with one constant bumped, **a single semantic error at SET
propagates deterministically through all five decisions.** I verified this: the per-episode semantics
vector is constant across all five stages for every arm in 11 of 12 episodes (the exception, episode
11, is a cap-96 truncation cascade in *all three* arms).

| | M | T | X |
|---|---|---|---|
| Episode-level executable success (SET) | **9/12** | **10/12** | 8/12 |
| Discordant episodes vs T | ep 8 win; ep 2, ep 9 losses | — | — |
| Exact one-sided sign test (harm) | **p = 0.5** | — | — |

The "10 losses / 5 wins across 60 decisions" is a **5× inflation of 1 win / 2 losses on 12 paired
episodes**. Note the two losses run in opposite languages (ep 2 M-Python fails, ep 9 M-JavaScript
fails) and X — also adapter-on — fails ep 2 as well but *passes* ep 9. The literal errors are
ordinary reasoning slips, not carrier artifacts:

```
episode/2/M/SET  (python adapter)  return list(seen)          # set() loses encounter order  -> FAIL
episode/2/T/SET  (no adapter)      seen=set(); result=[]; ... return result                  -> PASS
episode/2/X/SET  (js adapter)      ... yield x;   # `yield` inside a non-generator function  -> FAIL
episode/9/M/SET  (js adapter)      xs.filter(arr => arr.length >= 2)   # tests .length on numbers -> FAIL
episode/9/T/SET  (no adapter)      xss.flatMap(arr => arr.length >= 2 ? arr : [])            -> PASS
episode/9/X/SET  (python adapter)  [num for arr in xss for num in arr if len(arr) >= 2]      -> PASS
```

The same 5× inflation applies to T's presentation column (README:32 shows T 6 vs M 3): **all four of
T's extra presentation failures are episode 3**, where T's first answer dropped the code fence and
every subsequent answer copied the unfenced style. And all seven of X's truncations vs M's three are
episodes 10 and 11, where JavaScript for `signruns`/`histogram` simply does not fit in 96 tokens —
a **length artifact, not a competence effect**.

### 4.2 Is this the check-40k pattern? **No.**

| | check 40k (router bias, 30B-A3B) | check 49 (LoRA, 4B) |
|---|---|---|
| Contrast | text-only 16/32 vs text+bias 7/32 | T 10/12 vs M 9/12 episodes |
| Discordances | wins 2 / losses 11 / ties 19 | wins 1 / losses 2 / ties 9 |
| Effect | −9 tasks, −28.1 pp | −1 episode, −8.3 pp |
| Exact one-sided p | ≪ .05 (R3 "harm" met: losses−wins = 9 ≥ 3) | **0.5** |
| Norm/multiset-preserving control | yes (shuffled bias) | X = swapped adapter, 8/12 |
| Unrelated-work sentinels | n/a | **7/8 token-identical ON vs OFF** |

Check 40k is a large, clean, controlled competence harm. Check 49's competence difference is **one
episode** and is statistically null. Additionally the adapter is essentially inert on unrelated
work: of the eight paired sentinels, **seven are token-for-token identical** with and without the
adapter, and the eighth differs only in JSON whitespace (`'{\n  "result": 135\n}'` vs
`'{"result": 135}'`, same value). There is **no evidence here of a general
"internal-intervention-degrades-reasoning" pattern**; whatever this is, it is either noise or a very
small, dose-specific effect that 12 episodes cannot resolve. Do not merge check 49 into the 40k
narrative.

**And the check's own carrier is undertrained (M2).** `fit.jsonl`: the JS adapter's loss runs
2.309 → 2.036 → … → 0.627 → 0.524 → **0.498**, still descending at the final step, with grad norms
still ≈2.1. Both fits consumed **13.577 s of the registered 600 s ceiling (2.3 %)** — 16 steps, one
epoch, 128 examples. Any inference that "a weight carrier is too weak to beat precedent" is
confounded with a ~42× unspent fitting budget. Astra registered this caveat in advance
(`results/dense-focus-research-astra.md:168`): *"The miniature fit can fail because it is
undertrained; the honest conclusion is then 'no useful carrier under the quick-check budget,' not
'LoRA cannot encode rules.'"*

---

## 5. Bottom line for Brian

### 5.1 Does this close the weight side with "rendering plus masking is the mechanism; weights are for knowledge"?

**No.** That sentence asserts a *comparison*, and check 49 ran the comparison and got a tie at zero
on the only cell that could separate them. On every cell where both carriers worked, the adapter
matched or beat rendering:

| | M (adapter, no text) | T (text, no adapter) |
|---|---|---|
| SET language | 12/12 | 12/12 |
| HOLD / BACK language | 11/12 / 11/12 | 11/12 / 11/12 |
| SWITCH language | 0/12 | **0/12** |
| CLEAR stale impositions | 5 | **5 (identical episodes)** |
| Episode-level executable success | 9/12 | 10/12 (p = 0.5) |
| Rule-carrier input positions | **0** | 576 |
| Trajectory wall time | **188.853 s** | 191.436 s (M is 1.35 % *faster*) |
| Unrelated sentinels vs OFF | **7/8 token-identical** | n/a |
| Carrier release | **bitwise, 12/12 replay + 16/16 parity** | rule text removed |

There is also a strong, registered, controlled positive that the report does not surface. On the
admissible decisions (SET, HOLD, BACK — dropping the cell no carrier can win), using the check's own
exact sign-test formula:

> **M 8/12 vs X 0/12 all-active, 8 wins / 0 losses, exact one-sided p = 1/256 = 0.0039.**

The M−X margin clause of condition 2 (≥3/12 and p ≤ .05) is met **decisively** once the inadmissible
cell is removed; only the absolute ≥10/12 bar still fails, at 8/12.

**Note the governance conflict.** The original brief
(`results/handoff/briefs/check49-brief.md`) pre-registered the NO-GO consequence as *"CLOSE the
weight side for dense models: 'rendering + masking is the mechanism; weights are for knowledge'"*.
The **amendment** that actually governed the run narrows it: `registration.md` — *"A completed NO-GO
closes this registered recipe, not all LoRA methods"*; and README:73 follows the narrow reading. The
amendment is later and was adopted, so **it governs; the brief's blanket sentence must not be
executed.** Record the narrowing explicitly so the broad sentence cannot be quoted later as the
registered outcome.

### 5.2 So did we learn nothing?

We learned four things worth banking, and one non-thing:

1. **Banked:** a 5.9 MB rank-8 q/v LoRA deterministically selects the output programming language on
   a request with no code precedent, against a swapped-label control, at **zero** rule-carrier
   tokens and no latency cost. (SET 12/12, X 0/12; cold 12/12 language.)
2. **Banked:** releasing the weight carrier is **bitwise complete** — 12/12 same-history OFF replays
   reproduce M's CLEAR token-for-token, and 16/16 cache-matched OFF/pristine/saved-greedy parity.
   Weight-carrier release is a solved problem.
3. **Banked:** the adapter is essentially inert on unrelated work (7/8 sentinels token-identical).
4. **Banked (and this is the important one, and it is *not* about weights):** on this 4B model,
   **neither** a selected adapter **nor** an every-request rendered system rule can override the
   model's own prior answers when the next request is a minimal edit of the previous one. The
   transcript wins 36/36. That is a finding about *rendering* too, and it is directly relevant to the
   product: it is the strongest evidence yet that **masking/history-editing, not carrier strength, is
   what SWITCH and CLEAR actually require.**
5. **Not learned:** anything comparative about adapters vs rendering at SWITCH, and therefore
   anything that closes the weight side.

### 5.3 A corrected re-run is warranted. The single defect, and the budget.

**The single defect to fix:** *the check has no positive control that any carrier can flip the mode
against a retained same-family transcript; the registered eligibility gate
(`scripts/focus_check49.py:413-420`) certifies only cold single-turn cueing.* Fix = put that control
**in the gate**, and make the text comparator capable of winning it (render the rule at the
**current user turn** as an explicit switch instruction, not only in the system message behind two
contradicting assistant answers).

**Do the cheap probe first** (Brian's 2026-09-05 quick-test-first rule). Do **not** authorize a full
re-run yet:

- **Probe:** reuse the *setup* families only — they are the designated `setup-on` bank and were
  already opened for the mechanism diagnostic, so no evaluation prompt gets a second look. Rebuild
  the two mechanism five-decision histories (`scripts/focus_check49.py:502-511`) and, at the switch
  position, render the rule as a recency instruction in the current user turn with **no adapter**.
  2 modes × 4 repeats = **8 generations**, ≈ 2–3 GPU-minutes including load.
- **If text-at-recency switches:** the conflict cell is valid, M's 0/12 becomes a real adapter
  deficit, and the corrected re-run is justified.
- **If text-at-recency also fails:** the SWITCH endpoint is a property of 4B-under-precedent, not of
  carriers. Drop SWITCH from the GO conjunction, re-read check 49 as it stands on
  SET/HOLD/CLEAR/competence/cost, and move the switching question to masking (where the check has
  just supplied the motivating evidence) or to a larger trunk.

**Corrected re-run budget, only on a positive probe:** same frozen Qwen3-4B, one GPU run. Four arms
(add T+ = recency-rendered text) → ~400 generations; raise `output_cap` from 96
(`scripts/focus_check49.py:248`) to ~160 to stop episodes 10/11 dying of length in every arm; spend
the registered fitting ceiling instead of 2.3 % of it (e.g. 6 epochs / 96 steps per mode, ≈ 40 s).
At the measured 3.13 s/call plus 57 s load and 120 s cleanup reserve, projection is
**≈ 1,400–1,800 GPU-held seconds against the same 3,600 s allocation** — comfortably one run.

---

## 6. Graded findings

| # | Sev | Finding | Evidence |
|---|---|---|---|
| **H1** | **HIGH** | **Primary endpoint inadmissible.** SWITCH is the only carrier-vs-history conflict cell; the transcript wins 36/36 across all three arms, including the text comparator, and no positive control establishes the cell is winnable. "M 0/12 all-active" and the M–X test (p = 1) carry no information about adapters. The registered gate certifies only cold single-turn cueing. | `scripts/focus_check49.py:413-420` (gate), `:524-537` (schedule/arms), `:586` (all-active conjunction), `:119`/`:145` (minimal-pair variants), `results/quick-checks/check49/README.md:14,34`; records `episode/*/{M,T,X}/SWITCH` |
| **H2** | **HIGH** | **Condition 4's "stale imposition" sub-bar is not carrier-diagnostic.** M and T are stale in the *identical* five episodes (1,3,5,7,9). The metric measures transcript persistence, not carrier persistence, and the bar has no comparator arm. Charging the five to the adapter is a misattribution in the scoring, even though README:38 states the mechanism correctly. | `scripts/focus_check49.py:606,611`; `README.md:16,38`; recomputed stale sets M = T = {1,3,5,7,9}, X = {} |
| **M1** | **MEDIUM** | **"10 executable losses" is a 5× inflation of 2 episode-level losses.** The registered independent unit is the episode; semantics is constant within an episode because each answer copies the previous one. Episode-level: M 9/12 vs T 10/12, 1 win / 2 losses, exact one-sided **p = 0.5**. Same inflation applies to T's presentation column (all 4 extras are episode 3). | `scripts/focus_check49.py:594-597`; `registration.md` ("the independent unit is the 12 episodes"); `README.md:15,36`; `summary.paired_harms` |
| **M2** | **MEDIUM** | **Carrier undertrained.** JS adapter loss 2.309 → 0.498, still descending, grad norm ≈2.1 at the last step; both fits used **13.577 s of a 600 s registered ceiling (2.3 %)**. Any "weights are too weak" reading is confounded with a ~42× unspent budget — a caveat Astra pre-registered. | `fit.jsonl`; `scripts/focus_check49.py:432`; `contract.json` `fit_cap_s=600`; `results/dense-focus-research-astra.md:168` |
| **M3** | **MEDIUM** | **The SET/cold positive is the JS adapter's alone.** The Python adapter's target coincides with the cue-free base default (`baseline/None` 8/8 Python), so it has zero informative trials. README:34's "M selects the current adapter without text" over-generalizes to both adapters. | `README.md:34`; `baseline/None/*` records; `fit.jsonl` python losses 0.218→0.081 |
| **M4** | **MEDIUM** | **The ≥10/12 bar was near-unattainable against the observed task bank.** Episode 0 fails semantics in all three arms; episode 11 truncates at cap 96 in all three arms from HOLD onward. Maximum achievable all-active was exactly 10/12, with zero slack for ordinary task noise. Bar and bank were never compatibility-checked. | `scripts/focus_check49.py:248` (`output_cap=96`), `:611`; `audit.json` episode table; truncation set = episodes 10, 11 only |
| **M5** | **MEDIUM** | **Governance conflict on the NO-GO consequence.** The brief pre-registers "CLOSE the weight side for dense models"; the governing amendment narrows it to "closes this registered recipe, not all LoRA methods". The README follows the narrow reading; record the narrowing so the broad sentence cannot later be cited as the registered outcome. | `results/handoff/briefs/check49-brief.md` (fable GO/NO-GO block) vs `registration.md` para 1; `README.md:73` |
| **L1** | LOW | Condition 5 (shipping) returns **Pass on a vacuous 0-vs-0 tie**: `counts['M']>=counts['T']` is satisfied at 0. README:17 flags this in prose, but the coded bar does not. | `scripts/focus_check49.py:611`; `README.md:17` |
| **L2** | LOW | Truncation is scored `language='unknown'` and `syntax=False`, so the "Required language 34/34/10" row understates language adherence by the truncation counts (3/3/7). All affected records are episodes 10–11; no headline changes. | `scripts/focus_check49.py:167-171`; `README.md:27,30,31` |
| **L3** | LOW | **In-memory adapter tensors were never hashed** before/after the evaluation phase — only non-LoRA params are digested. Adapter invariance across the 180 trajectory calls rests on code inspection plus stable on-disk hashes, not measurement. `registration.md` says "All trunk tensors hashed in memory before/after", which does not cover the carrier. | `scripts/focus_check49.py:400-404`, `:557-559`; `registration.md` para 6 |
| **L4** | LOW | The frozen `bars['clear']` was armed to fail on `parity['token_diffs']==0`, which the run set to 1 from a known-vacuous cross-path (full-prefix vs incremental) comparison. Verdict unaffected (behavioral CLEAR fails 4/12 < 11) and the cache-matched audit resolves it to 16/16; the report is transparent about both. | `scripts/focus_check49.py:611`, `:501` (`replay`); `parity.json`; `cached-parity.json` |
| **P1** | *positive* | **Under-reported result:** on the admissible decisions (SET/HOLD/BACK), M beats the swapped-label control **8 / 0, exact one-sided p = 0.0039** — the condition-2 margin clause met decisively once the inadmissible cell is removed. Plus: 7/8 sentinels token-identical ON vs OFF; 12/12 same-history OFF replay of M's CLEAR; 0 vs 576 carrier positions; M 1.35 % faster than T. These belong in the report. | recomputed from `records.jsonl` using `analyze()`'s own exact-sign formula (`scripts/focus_check49.py:589-591`) |

**No critical findings.** No fabricated, unreproducible, or mis-transcribed number was found; all 272
records, both audits and every headline figure verified.

---

## 7. Recommended edits to the report (no code changes)

1. Retitle away from "two LoRAs … do not SWITCH or CLEAR" to something that survives the T result,
   e.g. *"neither adapter selection nor every-request rendering overrides the retained transcript;
   adapters set and release the mode cleanly at zero token cost."*
2. Add one row to the readings table: **"SWITCH endpoint: no positive control; T also 0/12 — endpoint
   inadmissible; condition 2 is not evaluable as registered."**
3. Report the harm at the registered unit: **1 win / 2 losses on 12 paired episodes, p = 0.5**, with
   the 60-decision count as a secondary, explicitly correlated figure.
4. State that M's and T's five stale CLEAR impositions are the **same five episodes**.
5. State the fitting budget actually spent (13.577 s of 600 s) next to any "miniature/undertrained"
   language.
6. Surface P1 (M vs X 8/0, p = 0.0039 on admissible decisions; 7/8 sentinel token identity).
