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
| T2b (S0-style in-session interference; cleared by both reviewers after 2 fixes) | headroom BINDS (+0.193 dev / +0.145 val): selection failure is real in sessions and the ORACLE fixes it. Learned selector: dev closure 0.12, VAL closure 0.02 — GATE MISS; program closed |
| Baselines (val, n=1238 opportunities) | base 32.0% / oracle 46.5% / selector 32.3% / re-insertion 52.9% |

## The three findings that matter

1. **In-session selection failure is real and mechanism-fixable.** Under
   format-identical conflicting notes inside multi-turn sessions, a frozen
   model's obligation adherence collapses (32-38%), and the hand-guided
   per-moment spotlight recovers a large fraction (+14.5 to +19.3) with
   code validity intact. The Miller-style transient press works inside
   agentic session dynamics, not just single prompts.
2. **The safety/recall trade defeated the learned selector here.** With
   zero-false-press frozen as a hard constraint (one false press can break
   syntax — measured), the calibrated threshold kept only ~25% of live
   presses, because type-matched lookalike candidates make the address
   max-score a poor live-vs-quoted discriminator. Address accuracy was
   perfect (130/130); the abstain mechanism is where the design fails.
   Closure 0.02 at validation; stopped per contract.
3. **At session scale with a small ledger, text re-insertion wins outright**
   (52.9% vs oracle's 46.5%) — repeating ~40 tokens of authoritative text
   next to the work is stronger than steering attention to a distant copy.
   Combined with the earlier program's flip side (at N=32 obligations and
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
unit tests had blessed); a calibration bug caught before any gated run;
one registered fallback never triggered; both stop rules fired exactly as
written. Evidence: results/qwen/t2*.json, t2b*.json, per-run logs,
reviews in results/. All numbers reproduce from pinned seeds.
