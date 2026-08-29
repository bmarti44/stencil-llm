# SELECTOR program report — the contentless governor (Miller-faithful split)

**Claim proven:** on frozen Qwen3-1.7B with working memory stored as visible
text, a learned, contentless wire — a hard span address (5 bits at N=32) fed
to an attention spotlight — restores governance where selection is the
bottleneck. Sealed final (untouched seeds, n=128, N=32 obligations):
**base 3.9% → selector 88.3%** (oracle 96.9%, net closure 0.91, address
accuracy 89.8%). Zero-selector is bitwise-identical to the base model; the
trunk is frozen throughout; wrong-address controls are at floor (0-3%).

## The registered ladder (all gates passed; every result seed-pinned)

| Phase | Result |
|---|---|
| S0 admission (retuned once) | base fails honestly: ~46% at N=8; errors are PRIMACY-driven authority-boundary confusions (p=6.6e-8) |
| S1 oracle (fresh block) | spotlight {20-27} beta=2: 75% rescue, 0 broken; wrong-span 2.8%; beta=4 correctly rejected by broken==0 |
| S2 learned (n=128 paired) | address 128/128; 43% -> 89% == oracle (closure 1.00) |
| S3-A0 scale admission | N=32: base 5%, full-ledger re-insertion 84% @ 503 tok/query — selection fails even with text re-supplied |
| S3-A1 oracle at N=32 | 78.7% rescue, 0 broken, wrong-span 0/61 (beta=4 via registered dose re-check) |
| S3-A2 learned at N=32 | 3.9% -> 78.9% val (closure 0.91) |
| SEALED FINAL | **3.9% -> 88.3%**, closure 0.91 |

## Honest boundaries

- At small N, text re-insertion solves the task outright (100% @ ~123
  tokens/query); the selector's win there is cost + properties only. At
  N=32 the selector matches/beats re-insertion (88% vs 84%) at ~1/100th
  the token cost — the registered regime where no cheap substitute exists.
- Supervised: the selector was trained with span-address labels (the
  structured focus.set world); autonomous salience remains open.
- Synthetic task, fixed templates, named queries; "apply the obligation to
  ongoing work" (implicit governance) is the natural next question.
- The prompt baseline (restating the authority instruction) does not fix
  the failure (+4 pts pooled); a trunk fine-tune could match accuracy but
  cannot provide zero-identity, per-moment addressability, or a frozen
  trunk — the claims this program is about.

Prior arcs: GPT-2 mechanism proof and the fused-cache negative
(results/gpt2-report.md, WORKLOG.md); reviews in results/.
Evidence files: results/qwen/s1-oracle.json, s2-selector.json, s3-a0.json,
s3-a1-oracle.json, s3-a2-selector.json, s3-final-sealed.json,
s3-selector-weights.pt. All reproducible from pinned seeds.
