# Zero-GPU settling replay for gpt-6-astra: check 47's dense outputs through the frozen consumer (2026-09-06)

Source: results/check47-review-opus.md (HIGH findings 2-4) and the addendum appended to
results/quick-checks/check47/README.md. The dense trunk's 0/32 execution figure is a parser artifact: stripping the
leading ```json fence and re-parsing with the FROZEN consumer yields 32/32 well-formed envelopes and 0/32 style
violations (vs the MoE's 30/32). Settle it on the record at zero GPU cost.
1. Register, BEFORE code, a fourth parser tolerance `strip_leading_fence` (a sibling of the three the MoE already
   receives) in the SLAB v1 tolerance set used by check 47's consumer: a single leading fenced block wrapper around
   an otherwise well-formed envelope is stripped and the tolerance is journaled per reply. Do NOT change SLAB-2
   (its prompt already mandates one fenced block) and do NOT re-run any model.
2. Replay the 32 SAVED dense responses and the 32 saved MoE responses from check 47's records through the frozen
   consumer with that tolerance enabled, and report the corrected table side by side: executed, caps, breakage,
   final success, per-kind violations, round-0 indent compliance, and the tolerance counts fired per trunk (state
   the MoE's `test_path` tolerance rate, 32/32, beside it).
3. Report the corrected reading explicitly: the harness comparison in check 47 is INELIGIBLE as run; with the
   tolerance applied, what does the dense-vs-MoE compliance comparison actually show on the 2 genuinely matched
   pairs and on the 32 unmatched-history rounds (label the latter descriptive only).
4. Do NOT change check 47's registered verdict: STAY on the MoE stands on the conjunctive cost clause and the
   48 GatedDeltaNet + 16 full-attention architecture. This replay corrects the RECORD, not the decision.
Outputs under results/quick-checks/check47-replay/ (README with the registration and the corrected tables,
records <= 10 MB); a 5-line item in results/quick-checks/README.md; WORKLOG (<= 4 lines). CPU only; no GPU; no
container; never signal any process; commit with explicit pathspecs (git add -f); no push; never read anything
under data/bench.
