# H1 artifact review — sol, spec adversary (xhigh)

Date: 2026-09-02  
Scope: `FOCUS LADDER v1 / H1`, `results/qwen/ledger-kv-probe-h1/`  
Execution: CPU-only, foreground, no model process, no process signals.

## Verdict first

**REFUTED.** The artifact arithmetic is exact and the retention contrasts are real on this marked/oracle-focus harness. The wave conclusion is also exactly right. The orchestrator's overall `ADVANCE-RETENTION` decision is nevertheless wrong under the registered rules: `pinned_echo` truncated in 1/20 sessions while `full` truncated in 0/20, an excess of **+5 percentage points**, above the registered **+2-point** cap. Thus safety is not intact and the literal catch-all outcome is `FAIL / DO NOT ADVANCE`, not `ADVANCE-RETENTION` (`LEDGER-PLAN.md:355`, `LEDGER-PLAN.md:357`, `LEDGER-PLAN.md:364`, `WORKLOG.md:2342`, `WORKLOG.md:2345`).

The compact reading is:

- **Confirmed:** all recorded scores and aggregate numbers; exact-column control; positive oracle-focus retention contrasts; quotation-excluded contrast; wave kill.
- **Refuted:** the registered H1 decision label `ADVANCE-RETENTION`.
- **Not shown:** automatic/target-blind KV retention, or a general Miller-style focus mechanism.

## Findings

### H1-review#1 — HIGH — `ADVANCE-RETENTION` ignores a registered truncation failure

The registered safety rule is “truncation excess over `full` <= +2 pts,” and `ADVANCE-RETENTION` additionally requires “safety intact” (`LEDGER-PLAN.md:355-358`, `LEDGER-PLAN.md:364-369`). The worklog instead reports the raw candidate count—“pinned_echo trunc 1”—and immediately declares all four conditions satisfied without converting it to a rate or comparing it with `full` (`WORKLOG.md:2344-2345`).

Recomputed from the records:

- `full`: 0/20 truncated = 0%;
- `pinned_echo`: 1/20 truncated = 5%; excess over `full` = **+5 pts > +2 pts**;
- `pinned`: 2/20 truncated = 10%; excess over `full` = **+10 pts > +2 pts**.

The `pinned_echo` failure is session 016 (`results/qwen/ledger-kv-probe-h1/session-016.json:1911`, `results/qwen/ledger-kv-probe-h1/session-016.json:1914`). The two `pinned` truncations are sessions 003 and 016 (`results/qwen/ledger-kv-probe-h1/session-003.json:2320`, `results/qwen/ledger-kv-probe-h1/session-003.json:2323`, `results/qwen/ledger-kv-probe-h1/session-016.json:1237`, `results/qwen/ledger-kv-probe-h1/session-016.json:1240`). The aggregate counts are also visible at `results/qwen/ledger-kv-probe-h1/summary.json:43-74` and `results/qwen/ledger-kv-probe-h1/summary.json:98-107`.

All three numerical efficacy predicates do pass:

- `pinned > pinned_control`: 33 > 20;
- `pinned_echo > echo_only`: 46 > 36;
- `pinned_echo` recovery from eviction: `(46 - 15) / (41 - 15) = 31/26 = 1.1923076923 >= 0.85`.

Timeout safety passes (0 in every arm), and the degeneracy comparison passes for the candidate (`pinned_echo` 1 <= `full` 2). Those facts do not waive the separate truncation cap. Even the narrowest reading—apply safety only to the advancing candidate—fails because `pinned_echo` itself is +5 pts. `RE-INJECTION-ONLY` also does not apply: `echo_only` recovery is only `21/26 = 0.8076923077 < 0.85`, and `pinned_echo > echo_only`. The registered “every other outcome” rule therefore yields **`FAIL / DO NOT ADVANCE`**.

This is decision-changing, not cosmetic: H3 explicitly requires H1 `ADVANCE-RETENTION` (`LEDGER-PLAN.md:375-379`).

### H1-review#2 — MEDIUM — H1 is marked/oracle focus, not target-blind selection

The registration is clear: the focus set is the harness's marked `Constraint:` spans and must be labelled “marked/oracle focus” (`LEDGER-PLAN.md:348-354`). The runner implements exactly that: it calls `constraint_span_records`, keeps every earlier-turn marked span, and echoes those same spans (`scripts/ledger_kv_probe.py:133-152`, `scripts/ledger_kv_probe.py:401-415`). No salience model chooses the H1 spans. Hashing `salience2` artifacts in meta does not make this path automatic (`results/qwen/ledger-kv-probe-h1/summary.json:25-36`).

Therefore the H1 echo arms do **not** deserve “target-blind” in the project's registered sense. They are blind to eventual pass/fail outcomes, but they receive an oracle annotation of which text is a constraint. H1 shows causal effects **conditional on correct oracle focus**:

- retaining marked aged constraint K/V improves over eviction and exact-column non-constraint retention;
- re-injecting marked aged constraints improves over eviction;
- marked-span KV retention adds on top of marked-span re-injection.

H1 does not show that an automatic salience system finds the right spans, that it avoids stale/irrelevant spans, or that automatic selected-span KV retention preserves these effects.

The 113-conversation `text_ledger` slice is relevant but separate. It records real salience, `automatic=true`, and 221/221 automatic turns (`results/qwen/ledger-eval/summary.json:23-27`, `results/qwen/ledger-eval/summary.json:58-68`, `results/qwen/ledger-eval/summary.json:85-89`). Its pooled all-constraint text result is `0.72923 - 0.70154 = +2.76923` points with exploratory McNemar `p=0.012373` (`results/qwen/ledger-eval/summary.json:308-340`). But that block is explicitly `secondary_all_constraints_descriptive`; the clustered selected and all-eligible text gates are false, and the primary claim is invalid on the 113 slice (`results/qwen/ledger-eval/summary.json:352-396`). Also, that text arm re-injects all aged automatically admitted ledger entries, while query-conditioned top-k selection is used by the neural arm (`scripts/ledger_eval.py:780-811`).

Jointly, the two artifacts support: “automatic salience-based text re-injection has a promising pooled descriptive effect, while oracle-marked KV retention has a positive small-harness contrast.” They do **not** compose into proof of automatic target-blind KV retention.

### H1-review#3 — MEDIUM — `full` is not a ceiling once the prompt receives an oracle recency intervention

The worklog calls 46/56 “above the full ceiling” (`WORKLOG.md:2343`). The number is correct; “ceiling” is not. `full` retains the original context but does not re-inject the marked constraints immediately before the final answer. `pinned_echo` changes both availability and recency, so it can legitimately outperform original full context. The appropriate description is “above the unmodified-full arm,” not “above a ceiling.”

There is no evidence of a mechanical verifier-input leak. The runner builds one original constraint row, generates every arm, and scores every response against that same row (`scripts/ledger_kv_probe.py:420-440`). The model, however, is deliberately given the oracle constraint text at a privileged recent position. That is the treatment and an external-validity limitation.

The quotation replay is informative:

- Both echo arms quote in the same 8/20 sessions: 000, 002, 008, 010, 012, 014, 015, 018.
- `pinned_echo`: quoted 19/23 = 0.826087; non-quoting 27/33 = 0.818182.
- `echo_only`: quoted 16/23 = 0.695652; non-quoting 20/33 = 0.606061.
- The retention-on-echo contrast remains in both strata: +3/23 among quoting sessions and +7/33 among non-quoting sessions.
- Against `full`, `pinned_echo` is +1/23 in the quoting-session stratum and +4/33 in the non-quoting stratum.

Thus the 46 > 41 result is not confined to responses detected as quotations. Quoting responses do pass more often than non-quoting responses in both echo arms, but barely so for `pinned_echo` (+0.79 pt) and more for `echo_only` (+8.96 pts). This is not a causal quotation effect: the same eight sessions are intrinsically easier under `full` too (18/23 versus 23/33). Moreover, the registered detector catches only an exact run of at least eight echoed tokens (`scripts/ledger_kv_probe.py:39-40`, `scripts/ledger_kv_probe.py:155-166`); it does not exclude shorter keyword copying or paraphrase that a constraint verifier may reward. The correct qualification is “not explained solely by detected 8-token quotation,” not “oracle cue leakage ruled out.”

### H1-review#4 — MEDIUM — the registered `invalid output` metric is absent

H1 registers per-arm invalid output alongside truncation, timeout, repetition, degeneracy, and quotation (`LEDGER-PLAN.md:355-357`). The arm writer records text, length, truncation, timeout, rep4, generated IDs, and cache counts, but no invalid-output field (`scripts/ledger_kv_probe.py:228-233`). The summary likewise has no invalid-output aggregation (`scripts/ledger_kv_probe.py:308-327`; emitted artifact fields at `results/qwen/ledger-kv-probe-h1/summary.json:43-141`).

Consequently every number that exists in `summary.json` can be recomputed, but the registered invalid-output count cannot. Assuming it is zero would be unregistered inference. This omission does not rescue or cause finding #1; it is an independent artifact-completeness defect.

### H1-review#5 — MEDIUM — provenance does not close the v2 “full hash set” item or prove one uninterrupted process

The prior verification explicitly left “full provenance hash set” open for the next probe (`LEDGER-PLAN.md:287-288`). H1 hashes the runner, model, corpus, tokenizer, Qwen code, several wave/salience files, and vendored IFEval (`results/qwen/ledger-kv-probe-h1/summary.json:25-41`). It omits direct H1 dependencies:

- `src/stencil/ledger.py`, which renders/inserts the echo (`scripts/ledger_kv_probe.py:133-152`);
- `src/stencil/e2.py`, which extracts the marked spans (`scripts/ledger_kv_probe.py:352-354`, `scripts/ledger_kv_probe.py:401-406`);
- `src/stencil/causal_moments.py`, which supplies the scorer (`scripts/ledger_kv_probe.py:352-354`, `scripts/ledger_kv_probe.py:437-440`).

The meta also records no Git commit, run id, invocation, start time, or finish time. The externally supplied script commit is consistent: the recorded runner SHA-256 `fddd7d...db2a1c` (`results/qwen/ledger-kv-probe-h1/summary.json:31`) exactly matches the `9c7e1ac:scripts/ledger_kv_probe.py` blob, and the current direct dependencies are unchanged from that commit. That is enough for this review's replay, but the artifact is not self-contained provenance.

The registered anti-mixing condition is satisfied in the important paired sense: a shared meta names all nine arms and `max_new=512`, every one of the 20 session records contains exactly those nine arms, and the runner completes the arm loop before atomically writing a session record (`results/qwen/ledger-kv-probe-h1/summary.json:3-24`, `scripts/ledger_kv_probe.py:386-389`, `scripts/ledger_kv_probe.py:425-454`). However, the runner can resume by skipping existing records (`scripts/ledger_kv_probe.py:386-389`), so the artifact alone cannot prove that sessions 000-019 came from one uninterrupted OS process. It proves one configuration/artifact job and within-session arm pairing, which is the scientifically important claim.

## Independent recomputation

I loaded exactly `session-000.json` through `session-019.json`, with no gaps or extras. The 20 raw arm objects begin at:

`session-000.json:1124`, `session-001.json:1529`, `session-002.json:1412`, `session-003.json:1697`, `session-004.json:1160`, `session-005.json:1630`, `session-006.json:1779`, `session-007.json:1344`, `session-008.json:1402`, `session-009.json:1644`, `session-010.json:1464`, `session-011.json:1805`, `session-012.json:1598`, `session-013.json:1456`, `session-014.json:2617`, `session-015.json:1421`, `session-016.json:1150`, `session-017.json:1501`, `session-018.json:1492`, and `session-019.json:1955`, all under `results/qwen/ledger-kv-probe-h1/`.

The CPU replay produced **zero discrepancies**:

- 180/180 stored verifier score vectors replay exactly from the response text against the original corpus row: 729/729 booleans total, including 504/504 aged booleans (56 aged constraints x 9 arms).
- 180/180 `aged_pass` values equal `sum(scores[:aged_n])`; every arm's `aged_n` equals its session `n_aged`.
- 180/180 generated-ID arrays decode to the stored text and match stored `n`.
- 180/180 rep4 values recompute bit-for-bit from generated IDs; maximum absolute error 0.
- 180/180 truncation and degeneracy flags recompute exactly from `n >= 512` and `truncated or rep4 > 0.5`.
- All echo texts, SHA-256 values, added-token counts, and echoed context token IDs reconstruct exactly from the stored base context and marked spans.
- All 180 quotation flags replay exactly using the registered eight-token rule.

### Arm aggregates

| arm | score-derived pass / n (rate) | trunc | timeout | mean rep4 | rep4 > .5 | degenerate | quoting | pass with quoting excluded |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| full | 41/56 (0.7321428571) | 0 | 0 | 0.10312780129775452 | 2 | 2 | 0/20 | 41/56 (0.7321428571) |
| evicted | 15/56 (0.2678571429) | 0 | 0 | 0.043388461955294735 | 1 | 1 | 0/20 | 15/56 (0.2678571429) |
| pinned | 33/56 (0.5892857143) | 2 | 0 | 0.13107790672470584 | 1 | 2 | 0/20 | 33/56 (0.5892857143) |
| pinned_control | 20/56 (0.3571428571) | 0 | 0 | 0.07747346257529439 | 1 | 1 | 0/20 | 20/56 (0.3571428571) |
| echo_only | 36/56 (0.6428571429) | 0 | 0 | 0.06686920231826077 | 1 | 1 | 8/20 (0.4) | 20/33 (0.6060606061) |
| pinned_echo | 46/56 (0.8214285714) | 1 | 0 | 0.1266610874769665 | 1 | 1 | 8/20 (0.4) | 27/33 (0.8181818182) |
| pinned_wave_d0.5 | 31/56 (0.5535714286) | 2 | 0 | 0.18233267992287408 | 2 | 2 | 0/20 | 31/56 (0.5535714286) |
| pinned_wave_d1.0 | 36/56 (0.6428571429) | 3 | 0 | 0.2130197093118545 | 3 | 4 | 0/20 | 36/56 (0.6428571429) |
| pinned_wave_d3.0 | 38/56 (0.6785714286) | 11 | 0 | 0.5677873394357035 | 12 | 12 | 0/20 | 38/56 (0.6785714286) |

These match `summary.json` exactly (`results/qwen/ledger-kv-probe-h1/summary.json:42-141`).

### Gaps, contrasts, recovered fractions, and bootstrap

The in-job gap is `41 - 15 = 26` passes, equivalently `26/56 = 0.46428571428571425` (`results/qwen/ledger-kv-probe-h1/summary.json:142-165`). Every registered contrast recomputes:

| contrast | pass difference | fraction of 26-pass gap |
|---|---:|---:|
| pinned - evicted | +18 | 18/26 = 0.6923076923 |
| echo_only - evicted | +21 | 21/26 = 0.8076923077 |
| pinned_echo - echo_only | +10 | 10/26 = 0.3846153846 |
| pinned - pinned_control | +13 | 13/26 = 0.5 |

Additional decision quantities:

- `pinned_echo` total recovery from eviction: `(46-15)/26 = 31/26 = 1.1923076923`;
- best raw wave dose: d3.0;
- best-wave recovery: `(38-15)/26 = 23/26 = 0.8846153846`;
- deterministic 2,000-resample session-paired bootstrap for `pinned - pinned_control`: mean `0.2375`, 95% percentile interval `[0.07083333333333333, 0.3958333333333333]`, seed 0. It differs slightly from pooled `13/56 = 0.2321428571` because the registered bootstrap weights sessions equally rather than constraints equally (`scripts/ledger_kv_probe.py:280-305`, `results/qwen/ledger-kv-probe-h1/summary.json:166-174`).

### Exact-column control

Confirmed for every session. Recomputed `pinned` / `pinned_control` runtime columns are:

`000 89/89; 001 60/60; 002 61/61; 003 45/45; 004 44/44; 005 61/61; 006 79/79; 007 74/74; 008 73/73; 009 60/60; 010 72/72; 011 60/60; 012 56/56; 013 70/70; 014 43/43; 015 57/57; 016 65/65; 017 77/77; 018 78/78; 019 50/50.`

The reconstructed column sets also have equal cardinality, are disjoint, and lie within the eviction range in all 20 sessions. This agrees with the v3 construction/assertions (`scripts/ledger_kv_probe.py:168-188`, `scripts/ledger_kv_probe.py:236-246`, `scripts/ledger_kv_probe.py:416-419`, `scripts/ledger_kv_probe.py:445`). Representative raw pairs are `results/qwen/ledger-kv-probe-h1/session-000.json:1716`, `results/qwen/ledger-kv-probe-h1/session-000.json:1846`, `results/qwen/ledger-kv-probe-h1/session-019.json:2742`, and `results/qwen/ledger-kv-probe-h1/session-019.json:2898`.

## Literal wave decision

The orchestrator's wave reading is exactly right:

- d0.5: 31 passes, 2/20 degenerate, 2 truncations. The degeneracy count is at the allowed boundary because the kill condition is strictly `> 2/20`, but 31 < plain `pinned` 33, so there is no amplification gain.
- d1.0: 36 > 33, but 4/20 degenerate > 2/20 (and 3 truncations).
- d3.0: 38 > 33 and is the best raw dose, but 12/20 degenerate > 2/20 (and 11 truncations).

Thus **every gaining dose fails the registered degeneracy rule**, and the only dose at the boundary does not gain. Amplification is not creditable on this harness (`results/qwen/ledger-kv-probe-h1/summary.json:109-140`, `results/qwen/ledger-kv-probe-h1/summary.json:163-165`). This portion of `WORKLOG.md:2345` is confirmed.

## Ranked next rung

Because finding #1 changes H1 to `FAIL / DO NOT ADVANCE`, none of these is authorized *as a continuation of a passed H1* without first recording that failed gate. Ranked for adequate proof before scaling while avoiding over-engineering:

1. **(a) Automatic-selection replication of H1 on the same 20 sessions.** This is the minimal missing bridge and the cheapest falsifier of the external-validity gap. Freeze the salience-selection path and all H1 metrics/rules before running; retain the exact-column control and the same arm pairing. Label it a new diagnostic replication, not a retroactive rescue and not independent confirmation, because it reuses the same sessions. It directly answers whether the oracle retention contrast survives automatic span choice.
2. **(b) The 909 Multi-IF `text_ledger` confirmation under ROUND 7.** This is the first justified larger implementation proof after the cheap bridge. It tests the automatic re-injection product on the registered cohort and has separate support from the 113 slice, whose text arm passes ROUND 7 truncation safety (`results/qwen/ledger-eval/summary.json:129-158`). It does not prove KV retention or wave amplification, so report it as re-injection evidence only.
3. **(c) An H3 trust-region wave pilot.** Do last. H3's explicit precondition—H1 `ADVANCE-RETENTION`—is unmet, and every gaining fixed wave dose already fails the small-harness rule. Building DIRECTER-style rejection now adds mechanism and policy complexity before automatic selection and the simpler product baseline are established. That is over-engineering on the current evidence.

## Final verdict

**H1 reading: REFUTED.** Arithmetic, oracle-focus retention signal, exact-column control, and wave kill are confirmed. The registered decision is **`FAIL / DO NOT ADVANCE`**, not `ADVANCE-RETENTION`, because `pinned_echo` exceeds the full-arm truncation rate by +5 points against a +2-point cap. Ranked next rung: **(a) automatic-selection H1 replication, then (b) 909 text re-injection confirmation, then (c) H3 trust-region wave pilot.**
