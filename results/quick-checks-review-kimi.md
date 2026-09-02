# Quick-checks review — kimi-k3 (2026-09-02)

# Quick-checks review — kimi-k3 (cross-model review, 2026-09-02)

Intended destination: `results/quick-checks-review-kimi.md`. No processes launched, no files read or written; everything below is recomputed from the pasted logs/rows/source. Means, counts, totals, and pairings were independently re-derived; AUROC values are accepted as computed (rank data unavailable, heavy ties make recomputation from rounded logs unreliable anyway). Line numbers for `role_rule_check.py` are counted from the pasted source (±1).

---

## Recomputed totals (independent verification)

### LOO oracle (`oracle_check_loo.log`)
- Span counts from rows: keep = 63, control = 103, total 166 evictions ✓ (matches summary).
- keep sum re-added = **0.333** → mean **0.0053** ✓; control sum = **0.4537** → mean **0.0044** ✓; both medians exactly 0.0000 ✓.
- Per-session paired recompute (mean keep − mean control): mean **0.0031** ✓; **but I count 7 positive / 9 negative / 4 exactly-zero sessions, not "8/20"** (borderline sessions s03, s11, s12 sit at ±2e-4, below the 4-decimal log resolution; not alarming, flagged low).
- Readout AUROCs 0.482 / 0.516 / 0.509 / 0.512 / 0.496 accepted (ranks unavailable); README's "0.48–0.52" ✓.

### Keep-in oracle (`oracle_check_keepin.log`)
- 166 evictions ✓; keep sum re-added = **11.3455** → mean **0.1801** ✓; control sum = **16.7938** → mean **0.1630** ✓.
- Gap range: **0.80 (s03, s17) – 3.92 (s16)**, not the README's "2–4" (17/20 sessions are in [2.1, 3.9]; low-severity wording).
- Max single-span recovery is **1.54 (s05)**, not "up to 1.2"; and controls reach **1.14 (s05)** and 1.13 (s13) — i.e., the largest recoveries occur on *both* keep and control spans. AUROC 0.518 / 0.630 / 0.601 accepted.

### Role rule (`role_rule_rows.json` × log × README)
Recomputed from the 20 rows directly:

| arm | recompute | claimed | |
|---|---|---|---|
| n (aged) | 56 | 56 | ✓ |
| full | 44 | 44 | ✓ |
| evicted | 14 | 14 | ✓ |
| finder pinned | 37 | 37 | ✓ |
| finder control | 18 | 18 | ✓ |
| ROLE | 41 | 41 | ✓ |
| role control | 26 | 26 | ✓ |

- Recovery (41−14)/(44−14) = 27/30 = **0.900** ✓. Finder recovery (unstated) = 23/30 = **0.767**.
- Budget: role pin cols sum 1772, mean **88.6** (README "89" ✓); evictable sum 9008; ratio 1772/9008 = **19.7%** ("20%" ✓). Finder mean 932/20 = **46.6** ("47" ✓).
- Pairings: vs finder **+4/−1/=15** ✓ (wins s00, s06, s07, s09; loss s15). Vs full **+3/−5/=12** ✓ (wins s14, s17, s18 — note ROLE sometimes *beats full*, consistent with eviction-as-denoising). Vs own control (not in README, computed): **+13/−1/=6**, one-sided sign p ≈ 0.0009 (two-sided ≈ 0.002). Vs finder per-session sign p ≈ 0.19 — *not* decisive at session level; constraint-level pairing (McNemar) is unavailable from the pasted rows.
- Safety: role truncated 1 / degenerate 1 — both are **s03** (double-flagged in one session) ✓. README's "(full: 1 / 2)" is **not verifiable** from the pasted rows (H1' arm records not included) — taken on trust, flagged low. Note role-control degenerate = 2 (s04, s17), which the README doesn't mention.

---

## Item 1 — Loss-delta oracle

**F1.1 [MEDIUM] The LOO test has no *resolution*, not no *signal* — README overclaims.** With Qwen in bf16 and near-zero base NLLs (`base 0.000`–`0.211`), single-span evictions produce bit-identical continuations on high-confidence tokens: medians are exactly 0.0000 in both groups, most entries are ±0.0, and with mass ties AUROC gravitates to 0.5 by construction — 0.494 is what a *dead instrument* reads, not what *absent utility* looks like. The keep-in arm directly refutes "no utility": single spans recover up to 1.54 nats of a 0.8–3.9 nat gap (oracle_check_keepin.log s05/s08/s14). Rewrite the README line as "NO RESOLUTION at LOO granularity" (`README.md` bullet 1).

**F1.2 [HIGH] The program-level conclusion is correct, but it rests on keep-in, not LOO — and keep-in's own control is contaminated.** Controls are the task sentences the continuation also needs: control mean 0.163 nats (with control recoveries of 1.14/1.13 nats in s05/s13) vs keep 0.180 — a near-null margin over an *active* null. The 0.63 top-3 "signal" is exactly what the content-reproduction account predicts: constraint sentences carry quote-heavy tokens (numbers, exact strings) the continuation must echo. So "the loss oracle measures need-to-reproduce-content, not standing-constraint adherence" is **supported** — by the keep-in confound structure, not by the LOO null, which is uninformative.

**F1.3 [MEDIUM] Named flaws, triaged.** 96-token prefix: real (late-acting constraints invisible; IFEval-style early-acting constraints partially captured, aged constraints not). bf16 zeros: real and *fatal to LOO specifically* (F1.1). First-token dilution: minor once top-k readouts exist (they mitigate; top-3/flips still ≤0.63). Controls-as-task-sentences: the decisive one (F1.2).

**F1.4 Would a cheap fix rescue it? No — and this is where "do not over engineer" bites.** (a) Full-length reference fixes only the prefix blindness; bf16 resolution and the construct confound remain. (b) An outcome-level oracle is the construct-correct fix — but it already exists: it is `role_rule_check.py` (checker outcomes, 361 s/20 sessions). On the *registered pilot corpora* (OASST2 / ToolACE) no checkers exist, so an outcome oracle there requires synthetic constraint injection — i.e., b3-style templating, re-opening the taxonomy-matching hole v2 items 1–2 just closed. Conclusion: the loss oracle cannot be cheaply converted into an adherence measure on the corpora it was registered for. **Cut it as a selection instrument; retain the keep-in deltas as a reported diagnostic/limitation; register a citation bar: no ΔNLL-recovery number may be presented as constraint-adherence evidence.** Do not rebuild.

---

## Item 2 — ROLE RULE

**F2.1 Arithmetic: all verified** (table above), including the three headline claims (41/56, 0.90 recovery, 20% budget) and both stated pairings. One unreproducible-by-design value: full-arm safety 1/2 (LOW, trust in H1' records).

**F2.2 Semantics reproduction: confirmed by construction, with two unverifiable-from-paste points [LOW×2].** `role_rule_check.py`: same recorded ids and evict range (L21 `ids = r["context_token_ids"]; lo, hi = r["evict_range"]`); re-encode guard with skip (L24–25; no skips in the log — tokenization identity held in all 20); prior user turns only (L26 `P._user_turns(context)[:-1]`); spans clipped into the evict range and empties dropped (L31–32); pinned-column count by column union, not span sum (L33); control via the probe's own `P.matched_control_spans` (L35); same `P.run_arm(...)` path (L45) with aged scoring `sum(score_row_constraints(row, g["text"])[:n_aged])` (L46–47) using H1'-recorded `n_aged` (L40). H1' arms are *read from recorded JSONs* (L48), not re-scored — so "same scoring as H1'" holds for the role arms via the shared scorer. Unverifiable from the paste: (i) whether the generation params `0.0, 512, 300.0` (L45) equal the H1' originals — a mismatch would silently change role arms relative to recorded arms; recommend a one-line assertion against the recorded probe config in the registration. (ii) Whether `matched_control_spans` role-matches its windows; from behavior (s15 control 3/3 > role 1/3) the control clearly *can* retain decisive user content — see F2.3.

**F2.3 [MEDIUM] Control fairness: levels 26 vs 18 are not comparable; margins are the right comparison and they are only partially so.** Each control is column-matched to its own treatment (verified: `pinned_cols` identical between role arms in every row) — so 26 (of 89 null columns) passing more than 18 (of 47) is *expected*, not a flaw. But the matcher draws real context windows: at 89 columns the null covers ~20% of the range and captures user-turn fragments by chance — the role null is a *harder* (better) null than the finder's. The finder's +19 is therefore measured against an easier floor than the role rule's +15; raw margin ordering (+19 > +15) understates role, ceiling proximity (role 3 from full; finder 7) cuts the other way. Cleanest common scale is recovery-of-eviction-gap: **role 0.900 vs finder 0.767**, with the caveat that role spends ~2× the columns.

**F2.4 [HIGH — attribution is open] Higher budget alone does not explain the gain over the *random* null (26 at equal columns), but it may explain the +4 over the *finder* (89 vs 47 columns).** Paired reading: role > own control decisively (13/1, p≈0.002); role > finder only suggestively (4/1, p≈0.19); role ≈ full (net −2, 3W/5L/12T) with three sessions where eviction *beats* full. **Exact settling control (run on b3, ~20 GPU-min at observed rates, registered *before* the benchmark evals):** **RB = role-at-finder-budget** — per session, pin prior user turns oldest-first whole-turn until cumulative union columns ≥ the H1'-recorded `finder_pin_cols` for that session, clip the final span from the right to exact equality, evict the rest; plus an exact-column null at that count; same `run_arm`/scoring path. Decision rule: RB ≥ 38 total → structure does the work at equal budget; RB ≤ 37 → the +4 is budget, and the mechanistic claim (not the selector's registration) dies. Report either way. The symmetric finder-at-89 run is optional.

---

## Item 3 — Burden test on the proposed simplification

**What is lost by cutting the G0 loss-oracle pilot (honest accounting):**
1. **[HIGH] Provenance, not evidence quality.** The pilot was the only leg that could have *falsified* the role rule off-benchmark or promoted (b)/(c) over it. That falsification power was already near-foregone: quick check 3 (BM25 coverage 0.37 at finder budget vs 0.13 random, recency 0.02) plus F1.2/F1.4 (the oracle can't measure adherence on checker-free corpora anyway) mean the pilot's selection readout would have ranked policies by a construct the quick checks just discredited. The genuine loss is the wording "chosen on OASST2/ToolACE" in v2 item 8 — the selector is now **chosen on the b3 dev probe**, and every claim line must say so.
2. **[LOW] Plumbing shakedown at scale** — mostly substituted: role_rule_check exercised the same `run_arm`/`evict`/scoring path on 20 sessions × 2 arms on top of H1's own runs.
3. **[NONE] The ΔNLL recovery table and the 1k-dialogue feasibility gate** — moot once the instrument is demoted.

**What must be registered verbatim so no outcome reads two ways** — full text in the Verdict block; the load-bearing pieces: exact pin construction incl. clipping; **the overflow rule when user-turn columns exceed B, with the ranker and tie-breaks frozen *now* (a post-hoc ranker choice = the leakage pattern being escaped; on b3 the overflow never fires — 19.7% < B = 25% — so the deployed mechanism there is pure role pinning)**; arms full/evicted/ROLE/exact-column-control; floors on recovery, paired CI vs own control, and safety; BFCL protected-prefix fix as a named precondition with a mechanical test; generation params pinned; and the disclosure sentences.

**Miller-inspired?** Plain engineering. Defensible shared properties: read-time, zero-training, selection-free at observed budgets. But Miller's selection is *content* gating under capacity pressure; pinning all user turns by structural role is the synthesis's "**protocol invariants are protected by role**" finding implemented verbatim — a schema prior, not selection. The only selection-flavored component (overflow ranker) never fired on this probe. Register wording: "parameter-free role-structural retention rule (read-time, no fitted parameters)"; prohibit "Miller-inspired" in any claim line.

---

## Item 4 — Leakage/lineage

**F4.1 [HIGH] Development-set status reaffirmed and one notch stronger.** The role rule was chosen not only after the BFCL/Multi-IF analyses (v2 item 0) but after *reading outcomes on the b3 probe*: **b3 is now a selection set**, not merely an informing dataset. Multi-IF and BFCL are development sets; their evaluations are post-development evaluations, wording ceiling unchanged (v2 item 8 as rewritten). S2 remains excluded for anything fitted and non-independent regardless (v2 item 1).

**F4.2 [MEDIUM] No new leakage in the quick-check scripts — verified at source level.** `role_rule_check.py` reads only `data/b3/mt-train-300.jsonl` (L16) and `results/qwen/ledger-kv-probe-h1p/session-*.json` (L17); the oracle logs derive from the same 20 probe sessions; reference = the FULL arm's *own greedy output on dev data* (self-distillation on dev — no benchmark content; caution [LOW]: this self-reference pattern must not be repeated on `data/bench/` without registration, and `data/b3` is IFEval-taxonomy-derived, so all b3 evidence is taxonomy-matched evidence — disclose alongside).

**F4.3 [HIGH] The no-contact family is now load-bearing and its registration must state:** named before any opening; contact screen covering data, model responses, labels, checkers, templates, and *design influence* (pin construction, B, overflow ranker, floors, tie-breaks); model never run on it; harness from untouched public source; content-hash audit vs `data/g0` and `data/b3` where licenses permit; **and at naming time its paths are added to `tests/test_eval_data_separation.py` `FORBIDDEN_PATHS` plus the guard is hardened for the bypass forms in my prior F1.2 (`os.path.join`, f-strings, env-sourced paths, cross-module delegation)** — otherwise the third-leakage pattern repeats through a door we already know is open.

---

## Required registration text (verbatim, for LEDGER-PLAN.md before any run)

```
SIMPLIFICATION — G0 RESTRUCTURE (registered 2026-09-02, before any benchmark run)
1. The G0 loss-oracle pilot is CANCELLED as a selection instrument and demoted to a diagnostic.
   Cause (dev-probe quick checks, results/quick-checks/): LOO has no resolution in bf16 (medians
   0.0000 both groups); keep-in shows utility exists but its controls (task sentences) carry
   equal content-reproduction utility (keep 0.180 vs control 0.163 mean nats); the measure is
   need-to-reproduce-content, not standing-constraint adherence. CITATION BAR: no ΔNLL-recovery
   number may be cited as constraint-adherence evidence anywhere.
2. CANDIDATE SELECTOR, defined verbatim: the ROLE RULE. Protected in every arm and never
   evictable, outside all pools and outside B: system prompt + tool schemas, columns 0–3, the
   current user turn, the 256 columns preceding it. PIN POOL = ALL prior user turns: token spans
   on the pinned-tokenizer ids, clipped to the evictable range [lo, hi), unioned. B = 25% of
   evictable columns (unchanged from v2 item 3). OVERFLOW (frozen now): if union columns > B,
   pin whole user turns oldest-first until the next turn would exceed B, then fill the residual
   from that turn's first columns onward; no ties possible; any other ranker is ineligible unless
   separately registered before eval contact. Evict everything else in the range. No parameters,
   no training, no outcome is consulted in the selection.
3. EVIDENCE STATUS (verbatim disclosure in every report): motivated by prior Multi-IF/BFCL
   analyses and SELECTED on the data/b3 mt-train-300 dev probe after reading its outcomes
   (ROLE 41/56 aged constraints vs finder 37, exact-column control 26, full 44, evicted 14;
   recovery 0.90; role budget 19.7% of evictable vs finder 10.4%; paired vs own control 13/1/6,
   vs finder 4/1/15). b3 is a development selection set and IFEval-taxonomy-matched.
4. ATTRIBUTION CONTROL (precondition of any mechanistic claim; run on b3 before the eval
   report): RB = role-at-finder-budget (whole user turns oldest-first to each session's recorded
   finder_pin_cols, final span right-clipped to exact equality) + exact-column null; RB ≥ 38 →
   structure; RB ≤ 37 → budget; reported either way.
5. EVALUATIONS, post-development only. Multi-IF 909 via the text_ledger runner; BFCL V3 only
   AFTER the protected-prefix harness fix (system + tool schemas never evicted in EVERY arm —
   asserted by test; pin budget over user/tool columns only; same-role-pool controls).
   ARMS (both benches): full / all-evicted / ROLE / ROLE exact-column control
   (matched_control_spans semantics; same column count per session; role-pool matched where the
   scheduler defines one). Optional non-gating fifth arm: recent+sinks.
   Generation: greedy (temp 0.0), 512 new tokens, seeds fixed per bench; model id recorded.
   FLOORS (pre-committed): primary = recovery (ROLE − evicted)/(full − evicted), micro-averaged
   per bench with macro reported; PASS iff recovery ≥ 0.80 AND clustered-bootstrap 95% LB ≥ 0.70
   AND ROLE beats its exact-column control with paired 95% CI excluding 0, on the bench.
   SAFETY FLOORS: truncated and degenerate rates (same is_degenerate) ≤ the full arm's on each
   bench; any excess counts against the arm; s03-type double-flags reported per session.
   REPORTED NON-GATING: pinned-column fraction vs B, overflow events (expected 0 at B=25%),
   per-session pairing tables.
6. CLAIM WORDING (ceiling): "a parameter-free role-structural retention rule, motivated by prior
   analyses and selected on an IFEval-taxonomy-matched dev probe, holds on the two development
   benchmark families it was designed around" — a post-development evaluation. "Zero-shot" and
   "Miller-inspired" are both barred; "read-time, parameter-free, role-structural" is the
   approved descriptor. v2 item 8's "chosen on OASST2/ToolACE" wording is withdrawn.
7. NO-CONTACT FAMILY: named in a later registration BEFORE any contact; passes the contact
   screen (no data/response/label/checker/template contact; no design influence on pin
   construction, B, overflow rule, floors, or tie-breaks; model never run on it; harness from
   untouched public source; content-hash audit vs data/g0 and data/b3 where licenses permit);
   its paths are added to tests/test_eval_data_separation.py FORBIDDEN_PATHS and the guard is
   hardened (os.path.join / f-string / env-var / cross-module forms) at naming time. It alone may
   carry a zero-shot-transfer claim, with this selector's dev-probe provenance disclosed.
8. v2 otherwise stands: policies (d)/(e) remain controls; S2 remains excluded for fitted
   policies and is secondary-only otherwise; budget and protected-prefix computation identical
   in probe, eval, and any deployment harness.
```

VERDICT: ADOPT-WITH-FIXES — cancel the G0 loss-oracle pilot as the selection instrument and demote it to a registered diagnostic (construct is content-reproduction, not adherence; LOO was no-resolution, not no-signal); register the ROLE RULE as candidate selector; evaluate post-development on Multi-IF 909 and BFCL only under the verbatim arms/floors/safety/overflow text above; run the RB budget-attribution control on b3 before any mechanistic claim; keep Multi-IF/BFCL labelled development sets with b3 disclosed as the selection set, and pre-register the no-contact family with the contact screen and guard hardening before it is opened.