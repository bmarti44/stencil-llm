# LEG B OUTCOME review — fable (2026-09-04)

Scope: LEDGER-PLAN.md "SELECTOR v2 — POST-DEVELOPMENT EVALUATION, LEG B" + Amendments 1-3 + "LEG B OUTCOME";
artifact results/qwen/multiif-evict-909-prequery-v2 (meta.json, summary.json, conv-000..908.json); harness
scripts/multiif_evict.py. Everything below was recomputed from the 909 records on CPU (scratch scripts
recompute.py / recompute2.py; no model process launched; the sealed IFEval file was not read).

## 1. Recomputation from the 909 records — all reported numbers reproduce exactly

Records: 909, ci 0..908 contiguous, 909 unique keys, key order identical to data/bench/multiif_en.jsonl
(sha256 3a3d2af3… = meta). Schema asserted on every record. aged == all[:len(turn_{t-1} ids)] holds in every arm
of every record (0 violations); aged total 2,276; last_turn = 3 in 896 conversations, 2 in 13 (20 aged constraints
are turn-1 constraints checked at turn 2 — a minor deviation from the registered wording "introduced in turns 1-2,
checked at turn 3"; disclose, no effect).

| arm | aged pass/n | rate | all pass/n | conv-mean |
|---|---|---|---|---|
| full | 1483/2276 | 0.6516 | 2082/3185 | 0.6560 |
| evicted | 379/2276 | 0.1665 | 1139/3185 | 0.1635 |
| clf_pinned | 1302/2276 | 0.5721 | 2016/3185 | 0.5725 |
| clf_pinned_echo | 1348/2276 | 0.5923 | 2019/3185 | 0.5945 |
| clf_control | 747/2263 | 0.3301 | 1514/3167 | 0.3273 |
| role_pinned | 1377/2276 | 0.6050 | 2085/3185 | 0.6074 |

Contrasts (conversation-clustered; continuity-corrected t lower bound per src/stencil/stats.py, sha256 = meta;
independent re-implementation, not summarize_records):

| contrast | n | mean (pts) | LB (cont.) | LB (plain t) | t | p one-sided | win/loss/tie |
|---|---|---|---|---|---|---|---|
| C1 echo − control | 904 | +26.844 | +24.712 | +24.823 | +21.8 | < 1e-15 (reported 0.0) | 497/66/341 |
| C2 clf_pinned − role_pinned | 909 | −3.493 | −4.785 | −4.675 | −5.0 | 1.000 | 60/128/721 |
| C3 half-gap recovery | 909 | +18.473 | +16.730 | +16.840 | +18.5 | < 1e-15 | 576/141/192 |
| echo − full (descriptive) | 909 | −6.151 | −8.235 | −8.125 | −5.2 | 1.000 | 185/287/437 |

Holm (alpha 0.05, 3 contrasts): C1 p≈0 ≤ 0.0167 pass; C3 p≈0 ≤ 0.025 pass; C2 p=1.000 > 0.05 fail. Matches
summary.json. The exact "0.0" p-values are t_cdf underflow at t ≈ 20 with df ≈ 900; write them as p < 1e-15.
Recovered fraction (pooled rates): (0.5923−0.1665)/(0.6516−0.1665) = 0.878 (conversation-mean version 0.875);
"0.88" is correct. For reference: clf_pinned recovers 0.836, role_pinned 0.904 of the gap.
C2 exact sign test on the 188 discordant conversations: P(wins ≤ 60) = 3.9e-7 — the C2 failure is a genuine
statistical result, not a clause artifact.

Safety counts recomputed from the raw text/ids (invalid_output(text), truncated = n_generated ≥ 512, degenerate =
truncated or 4-gram repetition > 0.5) agree with every recorded flag (0 mismatches):
full 0/208/241/0; evicted 0/54/54/0; clf_pinned 0/162/192/1; clf_pinned_echo 0/187/222/1; clf_control 0/76/87/0;
role_pinned 0/164/194/1 (timed_out/truncated/degenerate/invalid); quoting 153 on clf_pinned_echo.
Truncation clause (≤ 209) and degenerate clause (≤ 241) hold for every arm; the invalid clause (≤ 0) fails for the
three pinned arms. summary.json's `full_run_allowed_by_preflight: false` is the stale 12 GPU-h field (cap amended
to 24 GPU-h; 20.9 GPU-h used) — cosmetic.

## 2. The invalid outputs and the control_impossible conversations, concretely

The harness definition (registered by reference: `invalid_output` in scripts/multiif_evict.py, hash e1c08f31… =
meta = commit 965f110, 2026-09-03 12:13, before the run started 16:10): empty text, OR no alphanumeric character,
OR a chat-control token (<|im_start|>, <|im_end|>, <|endoftext|>) in the decoded text. No output in any arm of any
record contains a chat-control token (0/5,449). Every invalid event is the NO-ALPHANUMERIC branch.

- conv 278 (key 1886:11:en), arm clf_pinned_echo: turn-3 prompt "Wrap your whole response with double quotation
  marks." The output is 512 tokens of `"  \n` repeated (tail ids 1,2303,1,18611…), rep4 = 0.988, zero alnum chars.
  It is simultaneously truncated, degenerate and invalid. Other arms in this conversation: full, clf_pinned and
  role_pinned are also truncated+degenerate (rep4 0.41/0.01/0.01, thousands of alnum chars); evicted and control
  are short and clean. Aged pass 0/2 for every arm except full (1/2).
- conv 534 (key 2653:18:en), arms clf_pinned AND role_pinned: same prompt pattern ("Wrap your whole response with
  double quotation marks."). Output is `"  \n"  \n**"  \n**  \n**  \n…` for 512 tokens, rep4 0.984, zero alnum. The
  classifier spans and the role spans are IDENTICAL column sets ([[39,65],[417,434]]), so the two arms received
  byte-identical inputs and produced byte-identical outputs: this is ONE generation event counted in two arms, not
  two independent breaches. full (336 tokens, clean, 2/3 aged), echo (170 tokens, clean, 1/3), control (256, clean)
  were fine here.

So the "three breaches" are two distinct degenerate-loop events, both already counted by the degenerate clause
(which passes with margin 19-49 events). The clause fails only because full happened to have zero outputs with no
alphanumeric character; full's 241 degenerate outputs include one with 28 alnum chars (conv 34, a Kannada repetition
loop) — the boundary is a knife edge, exactly the zero-baseline vacuity fable/sol flagged for Leg A. In this run
"invalid" is empirically a strict subset of "degenerate"; the two clauses were meant to catch different failure
modes (control-token leakage / empty output vs looping), and here they double-count the same event.

control_impossible (5, all excluded from C1 only; C1 n = 904 confirmed; C2/C3/safety keep them, n = 909):
ci 145 (1476:16:en) evict width 147, pinned 79, available 68, 4/4 sentences selected; ci 358 (2192:11:en) width 119,
60 vs 59, 4/5; ci 613 (2859:10:en) width 515, 303 vs 212, 9/12 (the classifier kept eight sentences of quantum-
entanglement passage as "facts"); ci 769/770 (334:1 and 334:5, same base prompt) width 131/132, 72/73 vs 59, 5/6
("My company's name is Color Paper." etc. kept as facts). All are short histories where the selector kept more
than half of the evictable range; every other arm ran and scored normally in each; recorded exactly per Amendment
3 (control null, arithmetic consistent, schema-asserted). Their exclusion is neutral for C1 (excluding them cannot
favour the treatment; sensitivity in section 4 shows C1 is insensitive to far larger exclusions).

## 3. Application of the registered outcome rules — correct, conservative, one-way; one omission

Registered text: "Any arm breaching safety fails its contrasts regardless of pass counts." All three contrasts
involve a breaching arm (C1: echo; C2: clf_pinned and role_pinned; C3: echo), so all three contrasts fail as
registered. The orchestrator's "NOT SUPPORTED under the registered text" is the literal and most conservative
reading (AGENTS.md: take the most conservative reading; do not negotiate). Alternative readings I considered and
reject as grounds for a different verdict: (a) "invalid was meant for control-token leakage, and these are
degenerate loops already governed by the passing degenerate clause" — true in substance, but the definition was
committed and hashed before any outcome, so it IS the registered definition; changing it now is a retroactive
clause change; (b) "534 is one event, not two" — irrelevant, 1 > 0 in each arm. The reading is not two-way.

Completeness — two items the OUTCOME entry should state explicitly:
1. The triggered rule is "C1 or C3 fails -> the mechanism's benefit on Multi-IF-style dialogue is reported as
   unsupported at this selector quality AND the classifier is NOT iterated on Multi-IF results (further selector
   work goes back to the classifier data, never to the benchmark)". The entry states the first half only. The
   no-iteration constraint is the operative consequence and must be written down, because section 5's C2
   diagnostic is a Multi-IF result and is exactly the kind of thing that rule forbids feeding back into training.
2. "C2 fails alone -> the role rule is registered as the selector for this dialogue style" is NOT triggered (C2
   did not fail alone). The orchestrator applies it "descriptively"; that is acceptable wording provided the entry
   says the registration of the role rule is NOT made. Note C2's statistical failure is independent of the safety
   clause (p = 1.000, sign test 3.9e-7), so "the role rule beats the classifier at equal columns" is a supported
   descriptive claim either way.
3. Dead gate: "all three pass with safety intact -> ADVANCE to Leg A" was never the mechanism by which Leg A was
   authorized — Leg A was registered 2026-09-03 and its preflight authorized at 17:41 the same day, before this
   outcome (WORKLOG). Under the registered Leg B verdict the ADVANCE condition is unmet; the ledger should state
   explicitly that Leg A proceeds under its own prior registration and is not conditioned on Leg B, otherwise the
   two entries read as contradictory.

Wording that may be claimed: "Under the registered Leg B protocol the benefit claim is not supported (safety
clause breached by one no-alphanumeric degenerate loop per pinned arm against a zero baseline in full). Disclosed:
the registered contrasts C1 (+26.8 pts, LB +24.7) and C3 (+18.5, LB +16.7; 0.88 of the eviction gap recovered)
pass their tests; the classifier does not beat the recency-clipped user-role rule at equal columns (−3.5, LB −4.8)."
Not claimable: "Leg B passed", "the selector recovers 88% of the gap" as a registered result, or "role rule
registered".

## 4. Quoting (153/909 on the echo arm) — does not change the interpretation, but label it honestly

- Quoting is measured ONLY on clf_pinned_echo (detect_quoting returns False by construction for every other arm);
  the "0" in the other arms' quoting column is not a measurement. Applying the same detector to the other arms'
  outputs against the rendered echo text fires on full 94, clf_pinned 97, role_pinned 90, control 13, evicted 0 —
  i.e. about 10% of responses restate an 8-token run of a prior instruction with NO echo present. The echo-specific
  excess is therefore ~60 conversations (~6.5%), not 153.
- 148/153 first matches are instruction-sentence text, 5 are the echo header line.
- Quoting is not a pass mechanism: echo-arm aged rate is 0.537 on quoting conversations vs 0.606 on the rest
  (full: 0.646 vs 0.658 on the same split); 25/153 quoting outputs are degenerate.
- Sensitivity: excluding all 153 quoting conversations, C1 = +26.6 (LB +24.2, n = 752) and C3 = +19.3 (LB +17.5,
  n = 756); excluding the two invalid conversations, C1 +26.9 / C2 −3.5 / C3 +18.6. Nothing moves.

## 5. Model card and next registration

Model card (add to the registered verbatim line): "On Multi-IF (909 English conversations, post-development), the
registered Leg B evaluation did not support the benefit claim: the safety clause `invalid ≤ full` was breached by
one no-alphanumeric degenerate loop in each pinned arm against zero in full (full had 241 degenerate outputs; the
clause was vacuous at a zero baseline). Disclosed contrasts: echo-pinned retention +26.8 pts over matched random
columns and 0.88 of the eviction gap recovered; the learned selector was 3.5 pts WORSE than a recency-clipped
prior-user-turn rule at the same column budget. Quoting of echoed instructions occurred in 17% of echo-arm outputs
(~10% baseline without echo) and was associated with lower, not higher, pass rates."

Re-run under Leg A's clause (invalid ≤ full + 1): NOT warranted, and it would not be what it looks like. Generation
is greedy and deterministic: the 145 superseded records of the crashed prequery run are byte-identical to the v2
records in all 870 arm texts and score vectors. A "prospectively registered re-run" of the same 909 conversations
with the same selector, trunk and harness would reproduce these records and pass by construction — it is a
retroactive clause change with extra GPU hours. What IS warranted: (i) leave the Leg B verdict as registered;
(ii) any NEW leg (a different cohort — e.g. Multi-IF non-English or a held-out Multi-IF split — or the no-contact
family) registers, before outcomes, `invalid` = chat-control token or empty output, counted separately from
degenerate (an output already counted degenerate is not double-counted), with the Leg A one-event tolerance and a
vacuity guard when full's count is 0; (iii) no clause change is applied to this run.

What C2 implies for the selector program (diagnostic disclosure; per the triggered rule it must NOT be used to
iterate the classifier on Multi-IF): in 459/909 conversations the classifier's columns and the recency rule's
columns are identical (the constraint sentences sit at the tail of the prior user turns, so recency at the same
budget reproduces the selection); in the 450 where they differ the classifier is 7.1 pts worse (LB −9.7). Where
they differ, the classifier's extra columns are almost all turn-1 sentences (4,100 vs 136 turn-2 columns) while the
recency rule's extra columns cover turn-2 tail text the classifier rejected (1,975 turn-2 columns); the loss is on
the later aged constraints (index 1: 308/448 vs 334/448; index 2: 109/215 vs 164/215; index 0 tie). The classifier
selected 74% of turn-2 candidate sentences and 49% of turn-1; 126/909 task-opening sentences were kept. Even with
the echo, clf_pinned_echo − role_pinned = −1.3 (p 0.94). Two consequences: (a) on this dialogue style the role
rule is the right comparator AND the right selector — but note its budget was set by the classifier's column
count, so a deployable role rule still needs its own budget rule (untested here); (b) the classifier's value must
be demonstrated where constraints/facts are not recency-aligned (BFCL tool facts, long interleaved histories) —
Leg A is the correct next test; if Leg A shows the same pattern, the learned selector should be retired in favour
of role+recency and the classifier program's remaining claim narrowed to fact retention.

## 6. Leakage and lineage — clean

- Harness sha256 e1c08f31… = meta = HEAD = commit 965f110 (12:13 09-03); records 16:10 09-03 → 13:00 09-04
  (summary 13:00:42); OUTCOME commit e783081 at 13:02:09, records commit ab8d6b9 13:02:36; all 911 files tracked
  (`git ls-files` = 911). Data, trunk, tokenizer, ledger.py, selector_v2.py, stats.py hashes all match meta;
  classifier file hashes match the registered LEG B list (head.pt 191b3372…, safetensors 22328135…).
- Superseded prequery run: harness 1947e6d0… = commit 5c743f1 (Amendment 2), same selector/data hashes; its 145
  records match v2 byte-for-byte in every arm text (870/870) — Amendment 3 changed only the control_impossible path.
- Selector scoring is context-free on prior USER sentences with the frozen threshold 0.5 (meta); no fitting occurs
  in the harness; the sealed IFEval file is not touched by the harness (module docstring and code); Multi-IF is a
  development benchmark and is labelled as such in the registration.
- No ordering issue: the outcome text was written after the summary; nothing in the run depended on viewing an
  outcome. The one governance loose end is the dead ADVANCE gate (section 3, item 3).

## VERDICT: CONFIRMED-WITH-QUALIFICATIONS

The orchestrator's numbers, contrasts, Holm outcome, recovered fraction, safety counts and the literal application
of the safety clause are all correct and reproduced exactly; the verdict NOT SUPPORTED is the only reading the
registered text admits. Qualifications: (1) state the triggered no-iteration consequence and that the role rule is
NOT registered; (2) close the dead ADVANCE-to-Leg-A gate explicitly; (3) do not propose a same-cohort re-run under
the Leg A clause — deterministic generation makes it a retroactive clause change; register the corrected invalid
definition only for new cohorts; (4) disclose that the invalid events are no-alphanumeric degenerate loops (two
events, one shared by clf_pinned/role_pinned with identical inputs), that quoting is measured on the echo arm only
with a ~10% no-echo baseline, and that role_pinned's budget came from the classifier.
