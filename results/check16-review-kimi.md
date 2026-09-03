# Check 16 review — kimi-k3 (2026-09-02)

# results/check16-review-kimi.md — cross-model review, quick check 16 (kimi-k3, no shell)

Scope note: I have no execution environment in this review. Everything below is recomputed or reasoned from the pasted artifacts only. The brief's item-2 **nearest-neighbour paraphrase audit cannot be run by me** — it is marked UNVERIFIED-BY-ME and remains outstanding. (I also cannot write the file myself; this content is the deliverable for `results/check16-review-kimi.md`.)

---

## Item 1 — Recompute totals, columns, safety from the 20 rows

Arm sums over 20 sessions (each `aged_pass` column summed; denominator Σ`n_aged`):

| quantity | recomputed | claimed | verdict |
|---|---|---|---|
| Σ n_aged | 56 | /56 denominator | ✓ |
| CLF pinned | 38 | 38 | ✓ |
| CLF pinned+echo | 44 | 44 (= Σh1p full 44 ✓) | ✓ |
| CLF exact-column control | 16 | 16 | ✓ |
| CLFB pinned / echo / control | 29 / 37 / 19 | 29 / 37 / 19 | ✓ |
| h1p cross-check | full 44, evicted 14, finder pinned 37, finder echo 48 | matches checks 4–16 | ✓ |
| Σ CLF_cols | 846, mean **42.3** | "mean 42" | ✓ |
| Σ finder budget cols | 932, mean **46.6** | "finder 47" | ✓ |
| column ratio | 846/932 = **0.9077** | 0.91x | ✓ |
| Σ n_sel / Σ n_cands | **74 / 116** | 74/116 | ✓ |
| Σ CLFB_cols | 625, mean 31.25 = **0.67x** of finder; CLFB_cols ≤ budget in **20/20** | conservative bound | ✓ |
| coverage | mean **0.8896**, 17/20 ≥ 0.8 (fails: s12 0.375, s15 0.388, s16 0.739) | 0.89 (17/20) | ✓ |
| metrics.json | train n 15258 = 4904+5435+4919 = 10357+4046+434+421 ✓; heldout 438 = 181+149+108 = 238+200 ✓; acc/recall match README | — | ✓ |

**Safety — REFUTED.** The claim "0 truncated / 0 degenerate" (brief and README budget note) is false per the rows. Five arm-runs carry `truncated: true` **and** `degenerate: true`:
- **s18 CLF_pinned** — the headline pinned arm itself,
- **s19 CLFB_pinned_echo**,
- s11 CLF_control, s15 CLF_control, s15 CLFB_control.

That is 2 truncations in selector arms, 3 in controls — 5/120 arm-runs. Any of the three possible scopes of the "0/0" sentence (all arms / selector arms / unclipped pinned arm) is contradicted. This does not touch the efficacy totals but the sentence must be corrected before registration.

Secondary observations: echo is net-positive (38→44) but not monotone — it hurts in s7 (1→0), s14 (2→1), s15 (3→2), and CLFB echo collapses in s19 (1→0 with the degenerate output). CLF unclipped exceeds the finder budget in 3/20 sessions (s4 26>20, s5 41>36, s17 57>51): "0.91x" is a mean, not per-session; the CLFB arm is the honest per-session bound and never exceeds.

**Grade: totals / columns / coverage — CONFIRMED. Safety clause — REFUTED (wording; must fix).**

## Item 2 — Lineage

Holds: LABELS.md's explicit prohibition (no IFEval/Multi-IF/BFCL/tau-bench/S2/B3, "not even by paraphrase"); both reviewer statements of no `data/bench/` contact; Opus's 19-pattern IFEval scan over all 10,812 stable rows → 11 exact-form drops; `train_sha` (e7b6ec…) pins the artifact; sources enumerated (kimi 10,357 / kimi-ctx 4,046 / sol-enrich 421 / opus-enrich 434).

Qualifications:
1. **Paraphrase audit outstanding.** The specified check (100 training rows nearest in bge-small embedding to the b3 constraint sentences) is exactly the right test and I cannot run it here. It must be run, archived (IDs + cosines + judgments), and attached before Multi-IF.
2. **Probe-informed curation (mild, disclose).** The check-13→15 diagnoses (one-off-imperative precision gap; the check-15c formatting-rule blind spot) directly shaped sol's 160 paired hard negatives and the "generic formatting rules belong in the enrichment" direction. No b3 *instances* entered training, but b3 *failure modes* steered what was written. b3 has now influenced both mechanism selection **and** data curation — say so in the model card.
3. **"Author-disjoint" heldout is mislabeled.** Train contains opus-enrich (434) and sol-enrich (421); the entire heldout is opus-heldout (238) + sol-heldout (200) — the same two authors sit on both sides. It is disjoint only from kimi's 14,403 core rows, at row level, not author level. sol-heldout 0.77 vs opus-heldout 0.815 shows author-style sensitivity; a fourth-author set is needed before claiming transfer.
4. Bookkeeping: "530 drops / 98 relabels" does not reconcile with the excerpts I can see (≥506 documented drops; relabel trail incomplete). Publish the applied-patch ledger.

**Grade: CONFIRMED-WITH-QUALIFICATIONS** (instance-clean per all available evidence; NN audit unrun; two disclosures required).

## Item 3 — Fairness vs the finder

- **Columns:** headline 38-vs-37 is at 0.9077x mean cost — fair to slightly favourable to CLF; the 3/20 exceedances are bounded by CLFB (≤ budget 20/20, 29/37 vs control 19), so the conclusion doesn't depend on them.
- **Control:** post-clamp construction confirmed structurally — in all 20 rows, control `pinned_cols` equals its own arm's column count (both CLF and CLFB families). Control 16 (unclipped) / 19 (clipped): the clipped control exceeding the unclipped one is odd-looking but they are different random column sets at different budgets; harmless. On the three under-covered sessions (12/15/16) control ≈ pinned — consistent with the known coverage-conflation caveat, not with mis-construction.
- **Threshold:** from the README chronology (I could not open `clf_probe_check.py`): 0.5 is in force in checks 13–16 with no intervening tuning, and the threshold sweep (0.5/0.65/0.8) runs on the 438-row heldout and postdates check 16 (thr-0.65 probe queued as check 17). So CLF_THR=0.5 was fixed before check 13, and threshold selection is heldout-based, not probe-based. **Guardrail:** if check 17 reads well at 0.65, the adoption rationale must cite the heldout sweep, never the probe delta, and the choice must be frozen before any Multi-IF run.
- **Statistical caution:** 38 vs 37 on n=56 is parity, not a win. The carry-forward claim is "parity-or-better at 0.91x columns, with a generic artifact" plus the budget-matched echo trend 29→34→37.

**Grade: CONFIRMED (fair), with the noise caveat.**

## Item 4 — Taxonomy-drop dispute (sol 344 vs Opus 11)

**Opus's instance-level policy is right for this artifact; sol's category-level purge is wrong for a generic selector headed to Multi-IF.**

Reasoning: Multi-IF's constraints *are* formatting rules — exactly the functional category sol's policy removes from the positive class. The cost already showed up once: check 15c's 0.23 score on the title rule. A classifier trained with formatting rules systematically absent from `rule` learns a taxonomy-shaped blind spot, which is simultaneously (a) adversarial for the post-development evaluation and (b) wrong for real users, who issue plain-language formatting rules constantly. Also note the negative-leakage irony: a purge executed by someone who knows the taxonomy is itself taxonomy-informed.

Leakage risk of each:
- **Opus (keep plain-language instances):** category/taxonomy anticipation — training deliberately spans the same constraint *types* the benchmark tests. Multi-IF then measures a category-anticipated generic capability, and reporting it as benchmark-naive would overstate the claim. This is acceptable *because format-following is the target capability*, provided it is disclosed.
- **Sol (drop 344):** no category leakage, but capability sabotage on the exact target distribution, uninterpretable heldout behaviour on formatting rules, and a false "clean" claim (absence-by-design is still contact).

Model card must state: training instances are hand-written and benchmark-disjoint at the instance level (exact phrasings/templates/markers excluded by scan); constraint-*type* overlap with IFEval/Multi-IF is deliberate; Multi-IF/BFCL results are "category-anticipated, instance-clean"; the separately registered no-contact family (already in LABELS.md) carries the clean claim; the probe-informed curation loop (item 2.2) is disclosed; the applied patch set and `train_sha` are named.

**Grade: Opus policy — CONFIRMED as correct. Sol's 344-row taxonomy subset — revert/restore in the shipped artifact (keep his relabels and the duplicate/malformed-context hygiene drops).**

## Item 5 — Register before Multi-IF 909 / BFCL

- **Arms:** full, evicted, CLF_pinned, CLF_pinned_echo, exact-column control, CLFB pinned/echo. No taxonomy finder exists on Multi-IF, so the clip rule must be pre-registered (fixed span cap or fixed evictable-column fraction — decide now, not after).
- **Control:** exact-column, constructed post-clamp at each arm's own pinned_cols, fixed seed, construction-code hash.
- **Budget:** the cap rule, plus a commitment to report the pinned-column distribution (mean ratio vs evictable columns).
- **Threshold:** freeze 0.5 or 0.65 from the heldout sweep before the first benchmark run; single headline; decision logged as heldout-sourced.
- **Safety:** pre-register truncation/degenerate counting (count as failures, or dual-report) — only after correcting check 16's false "0/0" claim (5 arm-run truncations exist, incl. the headline pinned arm at s18).
- **Lineage:** archive `train_sha`, code hashes (`train_classifier.py`, `clf_score_sessions.py`, splitter version, probe scripts), LABELS.md, both review patches, the patch ledger; run and archive the item-2 NN paraphrase audit; publish the taxonomy-overlap disclosure and the heldout-composition disclosure (same two authors in train-enrich and heldout).
- **Scope:** b3 declared mechanism-selection set; Multi-IF 909 + BFCL declared the first post-development benchmarks; no-contact family declared next; primary metric, trunk model, and eviction configuration fixed.

**Grade: required-actions list; none optional.**

---

## Verdict

Every efficacy number in the claim recomputes exactly from the rows (38/44/16; 29/37/19; 56 denominator; 0.9077x columns; 74/116; 0.89 coverage, 17/20); the finder comparison is fair and the threshold history is clean. Two qualifications block full confirmation: the "0 truncated / 0 degenerate" clause is **false as written** (5 truncated+degenerate arm-runs, including s18 CLF_pinned) and must be corrected; and the embedding nearest-neighbour paraphrase audit — the crux of the lineage claim — could not be run by me and remains outstanding. Policy call: Opus's instance-level drop policy is the right one; sol's taxonomy purge must be reverted for the shipped artifact and the category-overlap disclosed on the model card.

VERDICT: CONFIRMED-WITH-QUALIFICATIONS