# Options memo: getting a small model to apply stated coding conventions (2026-09-12)

Inputs: the Astra floor consult (`2026-09-12-exp4-floor-consult-astra.md`), two web-research
reports (`2026-09-12-web-research-steering-and-compliance.md`,
`2026-09-12-web-research-small-model-compliance.md`), Exp 3b (`results/memorycode-derived/setup/`)
and the Exp 4 SETUP-LONG records (`results/memorycode-long/setup_long-role_evicted/`). Brian's
goal: one published HF artifact that keeps following the relevant instructions over a long
coding session, proven against the identical artifact with the modification off.

## 1. What we actually know tonight

- **The floor is real but was over-read.** Exp 3b: strict 0/16 on every arm at Qwen3-1.7B,
  mean per-family fraction .05-.12. SETUP-LONG (12 complete items at the time of the consult):
  strict 0/12 on base, focus and oracle; paired focus − base on the fraction −3.2 points
  (0 improvements, 4 declines, 8 ties). A 0/16 arm only bounds the true rate below 17%.
- **Two instrument bugs were hiding in the oracle and the candidate set; both fixed before any
  SCREEN generation (rule D2, disclosed in the ledger):**
  1. The oracle rendered the current session's instruction *events* (empty on filler
     sessions) instead of the cumulative live set. Repaired by replaying events through the
     session; the implied regex set now equals the dataset's `history_regex` on all 224 items.
  2. The speaker regex was ASCII-only; every mentor line of the six long and five short
     dialogues with the mentor "Jean-Aimé" was dropped, so the focus arm had zero candidates
     on them. Repaired with a name-based split (research code and package adapter).
  The oracle arm on all 16 SETUP-LONG items, the focus arm on 314-49, and the Exp 3b oracle
  are being regenerated now; every other output is preserved.
- **The literature predicts this floor.** Qwen3-1.7B follows a single coding-style
  constraint 44% of the time (MultiCodeIF) and code-style instructions 13% of the time
  (IFEvalCode); four simultaneous conventions at 44% each gives roughly 4% strict. Frontier
  models also collapse on MemoryCode's long histories (GPT-4o 94.5 → 30.5) and even on six
  style constraints in one prompt (Claude-3.5-Sonnet 0.01 on StyleMBPP). The task is a
  compositional-compliance task, and the mentor's conventions are counter-intuitive ones that
  oppose strong Python priors, the class that fails 10-100% regardless of phrasing.
- **"Verbalizes but does not apply" is the documented signature**, not a bug: probe accuracy
  97% with knows-but-violates rates up to 99%; thinking traces that talk about the rule are
  anti-correlated with obeying it for exact-form constraints.

### Update after the instrument repair (02:31Z)

With the corrected oracle regenerated on both cohorts the floor holds. SETUP-LONG, 16 items,
1.7B: strict 0/16 on base, focus and oracle; mean fraction base .120, focus .069, oracle .063;
prompt lengths equal on every item; the dense oracle reminder (17-21 rules, 250 tokens)
produced 13 unparsable and 13 capped outputs against base's 4 and 11. Exp 3b, 16 short
items: strict 0/16 on all four arms; oracle fraction rose from .051 to .112 once it carried
the full live set (37.5 tokens on average). The contracted Qwen3-4B retry of Exp 3b is
running; the 128-item SCREEN remains unlaunched.

## 2. What the evidence says will NOT work (do not spend GPU on these)

| Idea | Why not | Evidence |
|---|---|---|
| Rewording, reformatting or relocating the reminder | Measured null twice at large N (Cliff's δ < 0.01; BF10 0.05-0.10) | 2604.07192, 2605.10039 |
| Asking the model to restate the rules first | It already does, then violates them | 2604.28031, 2604.07192 |
| Self-critique without an external checker | Net negative below ~3.8B; ties blind resampling at 0.5-1.5B | 2410.23496, 2606.31511 |
| LLM-written synopsis / memory systems / RAG over history | Perfect instruction chain reproduces the collapse; Mem0 3.4 vs 82.4 long-context on rule application; compaction raised violations 0% → 30% | MemoryCode ablation, 2507.05257, 2606.22528 |
| Thinking mode or chain-of-thought | Exact-form constraints lose ~8.5 pp under thinking; 1.7B loses 3.5 pp prompt-strict (we already run non-thinking) | 2606.09662 |
| Whole-output constrained decoding | 15-43 points of task accuracy lost at 3B; incomplete grammars lose up to 97% correctness | 2605.26128, 2606.21619 |
| Pushing attention-bias strength until compliance appears | Every method degenerates past a cliff; "format right, content wrong" is the default failure | GUIDE Δ>5, PASTA 91.5% format / 18.6% correct |
| Repairing the 16-row register first | Admission precision, retirement and overflow are three separate failures, and fixing them cannot make the model comply | Astra consult, `auto/summary.json` |

## 3. Options that can plausibly work, ranked

Probabilities are Astra's planning ranges, adjusted by the two reports; none is a power
calculation. Every item is a NEW registration (rule D9); amendment 1 already used one of the
two permitted policy revisions.

| Rank | Option | Chance of a PROVEN artifact | GPU-h | What it costs the claim |
|---|---|---|---|---|
| 1 | **Qwen3-4B trunk**, same mechanism, same control | 25-45% (Astra 10-25% before qualification; IFEval +13 pp, code-style 13 → 18%) | ~8 at 4B speeds, after a 1 GPU-h qualification | Artifact renamed `stencil-focus-qwen3-4b`; nothing claimed about 1.7B |
| 2 | **Sparser, fresh-authored long workload** (1-2 conventions live at a time, long filler, rules that fit the budget), per-constraint primary with frozen denominator | 45-65% (Astra's top pick) | ~8 | Claim narrows to "sparse-instruction retention over long coding sessions"; workload must be authored, never selected from MemoryCode successes |
| 3 | **Per-constraint (fractional) primary** on the current workload, denominator frozen from the query | 10-20% alone; the SETUP-LONG fraction currently moves the wrong way | ~7 | Proves average partial compliance, not full compliance |
| 4 | **Attention bias on the reminder span** (GUIDE/SpotLight family; the repo's `bias_hook` path) | 5-15% at 1.7B (DIRECTER at 1B: +0.3 pp); 15-30% at 4B for structural conventions (SpotLight Qwen2.5-3B 0.42 → 0.53) | 2-3 for a registered arm + custom attention in the package + re-proving the off switch | Artifact becomes "modified attention path", must ship the dose and its degeneration table |
| 5 | **RLVR (GRPO) on synthetic, held-out-family convention data** | Highest ceiling of anything here (+17 pp on unseen constraints at 8B) and the only option that produces a genuinely modified model | Multi-day program, 20+ GPU-h | New program; regression gates (HumanEval/IFEval) required; no 1.7B precedent |
| 6 | Relevance ranking of evicted sentences (encoder/BM25) instead of newest-first | 5-15% | ~8 | Helps only when useful sentences are displaced by filler (e.g. 352-99's reminder was MacBooks and Discord) |
| 7 | Verifier-gated regeneration or narrow constrained decoding at `def` | Mechanically strong **but the only verifier we have is the benchmark's own regex**, so it leaks labels into the intervention; not admissible on MemoryCode | — | Admissible only on an authored workload whose rules come with a generic linter |

## 4. The one diagnostic to run before choosing

**pass@k on the corrected oracle arm.** Inverse IFEval showed models at 47-55% single-sample
compliance on counter-conventional instructions reach ~90% with best-of-32: the capability
exists and the greedy policy fails. If Qwen3-1.7B's oracle arm has pass@8 > 0 on the
SETUP-LONG items, the floor is a sampling-policy floor and inference-time levers (bias,
ranking, 4B) have room; if pass@8 = 0 at 1.7B and > 0 at 4B, the 4B trunk is the minimum
viable artifact; if both are 0, the workload itself is beyond this model band and option 2 is
the only honest path. Cost: 16 items × 8 samples × 2 trunks with batched `transformers`
sampling, roughly 1 GPU-h total. Registered as a diagnostic (no claim attached), temperature
fixed in advance, regex-only judge.

## 5. Recommended sequence (Brian decides; nothing below starts without a registration)

1. **Now (running):** regenerate the oracle/focus arms invalidated by the instrument repair;
   re-read SETUP-LONG with a correct oracle. If the oracle is still 0/16 strict, the
   registered 128-item SCREEN is left unrun and reported as such (Astra: defensible to run,
   but it would most likely read NOT PROVEN for lack of resolution; SETUP cannot issue
   SCREEN's terminal reading, so the report says "primary not run, reason, data").
2. **Exp 3b 4B retry** (already in the contract; 16 items, 4 arms, ~1 GPU-h) with the
   repaired oracle. Gate: history ≥ 6/16.
3. **pass@8 diagnostic** on the oracle arm at 1.7B and 4B (~1 GPU-h).
4. Register ONE of: 4B trunk on the existing LONG items (if 2 and 3 pass), or the
   sparse-instruction authored workload (if 4B also floors). Per-constraint primary with a
   frozen denominator in either case; strict reported alongside.
5. Attention bias only as a registered secondary arm on whichever trunk passes step 3, with
   a degeneration table and task-correctness column in the same run.
6. RLVR stays the long-shot program if the inference-time bundle cannot be proven.

## 6. What stays true about the package regardless

The published mechanism (verbatim restatement of truncated-away user sentences, token-matched
window, off switch) is the construction the literature endorses for rules that would
otherwise be *deleted* from the context (Constraint Pinning: 30% → 0% violations after
compaction at ~47 tokens; verbatim rule quoting 37% → 77% in RepoComplianceBench). It does
not help a rule that is present but unattended, which is the oracle-arm case. The artifact
therefore remains the right shape for the claim; the trunk and the workload decide whether
the claim can be measured.
