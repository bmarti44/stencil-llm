# TIMED-SELECTOR program report — per-moment governance of code generation

**Question:** can a contentless, per-moment attention spotlight keep a frozen
model governed by its obligations during long, steered, feedback-driven
coding sessions? **Answer: the mechanism — yes, proven; the learned
safety-constrained selector — no, not at this design point; and plain text
re-insertion beats even the oracle at session scale.** The program closed at
its registered stop rule after one validation run, no rescues.

## Registered ladder

| Phase | Result |
|---|---|
| T0 oracle (honest instruments, fresh seeds) | +21.9 pts parse-gated, ZERO parse loss (b=2 selected; b=4 rejected by the strict gate); wrong-sentence control harms; random-moment control null |
| T1 learned timing+address | == oracle (closure 1.00); later QUALIFIED: timing is obligation-blind syntax detection (probe: fires 32/32 with no obligations present); address was forced-choice — no component had read an obligation; three registered arms initially unrun, later executed at their expected signatures |
| T2 (multi-turn, v3 contract, 3-round design review) | INCONCLUSIVE-BY-DESIGN: oracle headroom +0.016 < 0.10 — with a small surviving authoritative ledger, session failures are not selection failures |
| T2b (S0-style in-session interference; cleared by both reviewers after 2 fixes) | headroom BINDS (+0.193 dev / +0.145 val): selection failure is real in sessions and the ORACLE fixes it. Learned selector: dev closure 0.12, VAL closure 0.00 (14 applied presses in 14,794 steps) — GATE MISS; program closed |
| Baselines (val, n=1238 opportunities) | base 32.0% / oracle 46.5% / selector 32.0% / re-insertion 52.9% |

All T2b numbers are from the post-fix rerun with the registered selector
(see Process record: the original evaluations loaded an unregistered
checkpoint via an import side effect; dev aggregates were unchanged by the
rerun, the val selector row changed 32.3 -> 32.0).

## The three findings that matter

1. **In-session selection failure is real and mechanism-fixable.** Under
   format-identical conflicting notes inside multi-turn sessions, a frozen
   model's obligation adherence collapses (32-38%), and the hand-guided
   per-moment spotlight recovers a large fraction (+14.5 to +19.3). Code
   validity is NOT free at session scale, unlike T0's zero-parse-loss
   result: paired against base on val, the oracle loses 7 parse / 11 exec
   of 409 works (gains 3 / 5) — a small real cost (dev: 0 / 0 lost). The
   Miller-style transient press works inside agentic session dynamics,
   not just single prompts, at a ~1.7% validity tax at this scale.
2. **The safety/recall trade defeated the learned selector here.** With
   zero-false-press frozen as a hard constraint (one false press can break
   syntax — measured), the calibrated threshold kept only ~25% of live
   presses, because type-matched lookalike candidates make the address
   max-score a poor live-vs-quoted discriminator. Address accuracy was
   perfect (130/130); the abstain mechanism is where the design fails.
   At validation the registered selector all but stopped acting: a
   direct press audit (results/qwen/t2b-press-audit.json) counted 14
   applied presses and 941 timing fires across 14,794 generation steps
   (non-applied fires were rejected downstream by the theta threshold or
   an out-of-ledger address; the audit does not split the two). 407/409
   works produced decoded code strings identical to base's — and the
   code string is the scorers' entire input, so those works score
   identically by construction; the 2 differing works left paired
   parse/exec outcomes and aggregate adherence unchanged — closure 0.00;
   stopped per contract.
3. **At session scale with a small ledger, text re-insertion wins on
   adherence** (52.9% vs oracle's 46.5%) — repeating ~40 tokens of
   authoritative text next to the work is stronger than steering attention
   to a distant copy. It is not a free win: on val it churns validity
   (paired vs base: 24 parse / 30 exec lost, 17 / 46 gained — net exec
   +16, net parse -7). Combined with the earlier program's flip side (at N=32 obligations and
   Q&A shape, the selector matched re-insertion at 1/100th the cost), the
   cost-benefit boundary is now mapped from both sides.

## Where the selector stands after both programs

Proven: contentless per-moment addressing on a frozen trunk (SELECTOR
program: sealed 3.9%->88.3% at N=32; G1-codegov +21.9 under conflict).
Bounded: learned autonomous pressing under a strict safety constraint in
open session dynamics (this program's negative). The honest deployment
recipe today is: keep the ledger, re-insert it when small, and reach for
the spotlight when obligations are many and token budgets matter.

## Process record

Three-round design review before any build; two clearance fixes that
prevented corrupted counterfactual labels (a substring-match bug my own
unit tests had blessed); one registered fallback never triggered; both
stop rules fired exactly as written.

One CRITICAL caught only at the closing sol verification: the shakeout
script imported the selector-training script for a helper, and that
script retrained on import — silently overwriting the recalibrated
zero-false-press checkpoint with the defective quantile-theta version
before every evaluation. Every originally reported selector arm ran an
unregistered selector, and the earlier claim that the calibration bug
was "caught before any gated run" was false. Fix: helper moved to the
library, training body guarded, a static regression test forbids
top-level work in imported scripts, and the full T2b chain (train ->
recalibrate -> dev -> val) was rerun with the registered artifact.
Training reproduced the recorded counts, thresholds, and calibration
statistics exactly (12329/837/134 examples, quantile theta 172002.445,
address accuracy 130/130; the original checkpoint was overwritten in
place, so a bitwise tensor comparison is not possible); dev aggregates
were unchanged; the val selector row moved 32.3 -> 32.0 (closure
0.02 -> 0.00). The same closing review found "validity intact"
unsupported; per-work paired parse/exec records are now saved for every
arm (paired_vs_base in the shakeout JSONs) and the findings above quote
them.

Evidence: results/qwen/t2*.json, t2b*.json, per-run logs (r2 = post-fix
rerun), reviews in results/. All numbers reproduce from pinned seeds.
