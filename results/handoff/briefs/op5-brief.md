# Open problem 5 for gpt-6-astra: COMPLIANCE WITHOUT COMPETENCE — can attention/skill re-weighting be salvaged? (2026-09-07)

Brian's framing, which reframes the whole internal line: "I think what we wanted IS an attention re-weigher, not
memory. At least at this point in the project, that's what we wanted. We wanted to simulate focus, specifically
focusing on the weights that matter the most (the 'skill') to accomplish the current task. So the rule following
went up, but we didn't get better outputs." He is right that attention/skill re-weighting was the intended
mechanism, not memory. The question is whether the recurring failure signature is fatal or fixable.

THE PATTERN TO INVESTIGATE. Every internal lever this program tried raised SURFACE COMPLIANCE while leaving task
quality flat or worse. Verify each of these locally with real numbers and file:line, using
results/full-program-review-astra.md as the corrected claim ledger (several original files still read wrong):
 - The wave attention re-weighter (results/internal-wave-report.md): 25.2% -> 44.8% adherence, beating a hand-built
   policy at 38.3% and reinsertion at 43.0%, but it BROKE 21 base-valid works (reinsertion broke 30); the held-out
   comment rule was 0/120 in EVERY arm; the recurrent variant showed null state-dependence; a later confirmation set
   moved 85.84% -> 86.23% with 59 fixes / 55 breaks, p = 0.389.
 - Router-logit bias (checks 40b-40l): language induction up to 32/32 at alpha 3, yet check 40k paired hidden-test
   success fell 16/32 -> 7/32 (2 wins, 11 losses, p = .022) with all losses valid unbroken JavaScript, and the
   shuffled control also fell; check 40l's competence-direction bias was a reply-length confound; check 40j found the
   lever adds nothing once the rule is rendered.
 - Dense-model routes (checks 31-33, 41, 41b): null or parser-level only.
 - Two-LoRA focus carrier (check 49 + results/check49-review-opus.md): SET causally clean 12/12 vs 0/12 with ZERO
   carrier tokens and 1.35% faster than rendering, cold-HOLD 10/12, adapter-OFF parity exact — but SWITCH was
   inadmissible (transcript won 36/36 in all arms) and the "10 executable losses" was a 5x inflation, correctly
   1 win / 2 losses, p = 0.5. State honestly what this does and does not establish.
Produce a single table of the pattern across all of them: what went UP, what went DOWN or stayed flat, at what dose,
with what control, and whether the competence loss was statistically real or an artifact later corrected.

THEN DEEP WEB RESEARCH (open what you cite; mark unverified; "no known remedy" is a valid answer):
1. Is "compliance without competence" a named, studied phenomenon? Start from the result that an attention-steering
   method reached ~99% format accuracy while task accuracy fell from ~83% to ~48% (DIRECTER, March 2026, Table 1,
   cited in results/dense-focus-research-astra.md), and from AxBench's finding that prompting beats steering with
   the gap widening with scale. Find the mechanistic explanations offered: does a low-rank or low-dimensional edit
   perturb the computation the task needs; is it a dose/geometry problem; is it that surface features are cheaper to
   move than reasoning; is it distribution shift off the model's own manifold?
2. WHAT DO THE METHODS THAT KEPT COMPETENCE DO DIFFERENTLY? Look hard at any attention or representation control
   that reports BOTH improved instruction adherence AND preserved or improved task accuracy on executable or
   verifiable tasks. Candidates to check and extend: PASTA (ICLR 2024), SpotLight (EACL 2026), DIRECTER's own
   instruction-aware attention control with dynamic rejection, ReCoVeR (EMNLP 2025), SKOP (2026), distribution-aware
   steering, geometry-aware/utility-preserving projections, conditional or gated steering that fires only when
   needed, and anything that applies control at the decision token rather than everywhere.
3. LONG-HORIZON / AGENTIC ANGLE: does any of this survive multi-turn, tool-using, long-context settings, or is all
   the evidence single-turn? Anything on control that must persist, switch and release across a trajectory.
4. THE SALVAGE QUESTION: given our evidence, is there a version of internal focus that could plausibly work
   generically for long-horizon agentic coding? Consider specifically: control applied only at decision points
   rather than every token; control CONDITIONED on a detector so it fires rarely; control restricted to a certified
   family with a competence guard that reverts on any executable regression; and the check-49 SET result as the one
   place a carrier already beat its control with zero token cost.
Deliver TOP 3 salvage candidates, ranked, each with a QUICK TEST at <= 1 GPU-hour: pre-written GO/NO-GO with
thresholds, the exact evaluation bank (note that check-49's evaluation families are BURNED by the check-51 exposure,
and held-out sets 1-4 are exposed; data/classifier/heldout/clean-admission-bank-v1.jsonl is clean but is reserved for
the admission screens), the data-lineage line, and what a null closes. Every test MUST measure executable task
quality alongside compliance, paired, with the episode or task as the unit. End with a plain-language verdict for
Brian: was the attention re-weighter the right idea executed badly, or the wrong idea; and if it is salvageable,
the single cheapest experiment that would show it.
Write results/open-problem-5-compliance-competence-astra.md.
PROTECTED: the registered 64-episode larger test is RUNNING on the GPU. CPU and web only. Do not touch the GPU, any
RUNNING.flag, any container, anything under results/larger-test/, or any code. Never signal any process. Never read
anything under data/bench, and do not read evaluation-bank episode CONTENT. Write ONLY that one report file and
commit it with an explicit pathspec (git add -f); no push.
