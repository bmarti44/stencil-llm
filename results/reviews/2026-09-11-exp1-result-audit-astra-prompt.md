You are Astra (gpt-6-astra), adversarial author-disjoint RESULT AUDITOR (plan rule D1: one result audit per registration). Maximum reasoning effort. READ-ONLY access to /home/bmarti44/stencil-llm; write nothing; run no model/GPU/network; do not read data/bench/ contents (you may read results/ and scripts/). Print your audit as Markdown to stdout.

Audit Exp 1: registration results/qwen/multiif-echo-only-128/REGISTRATION.md, results results/qwen/multiif-echo-only-128/RESULTS.md, summary.json, manifest.json, replay.json, selection.json, per-source records conv-*.json (schema 2), script scripts/multiif_echo_only.py (+ scripts/multiif_evict.py it imports), tests/test_multiif_echo_only.py.

Check, with file:line citations:
1. Registration fidelity: were the arms, budget (E=256 incl. header), packing rule, estimands D1/D2/D3, tests, margin, safety columns and readings executed exactly as registered? Any deviation not disclosed in RESULTS.md?
2. Numbers: recompute the seven arm means, the three contrasts (mean, bootstrap interval with seed 0 / 10,000 resamples, sign test counts and p) from the records and confirm or refute RESULTS.md. Confirm n=128 distinct sources (425 pairs + 59 singletons structure) and that no source contributes two conversations.
3. Reuse validity: the five old arms were reused after an 8/8 replay; is that sufficient, and is there any leakage between arms (e.g. the new arms' echo text derived from outputs)?
4. Readings: are D1 "insufficient evidence", D2 "demonstrated harm", D3 "role rule default" the correct labels under plan/PROTOCOL.md rule 3? Is the descriptive "role_echo_only > full" statement appropriately hedged?
5. The artifact decision drawn in RESULTS.md's last section and in plan/BACK-ON-TRACK-PLAN.md section G (classifier register stays primary for Exp 4; fallback = role rule over the truncated-away region): is that a defensible reading of D3, or does D3 require the role rule as the primary? Answer with reasoning, not a new arm.
Grade each finding low/medium/high/critical. End with: VERDICT (ACCEPT / ACCEPT WITH EDITS / REJECT), the minimum edits, and a two-sentence note to Brian.
