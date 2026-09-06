# Check 40j accuracy review (fable, one round, 2026-09-06)

Scope: results/quick-checks/check40j/{README.md, records.jsonl, tasks.json, freeze.json,
summary.json, audit.json, run.log}, scripts/focus_check40j.py, prior context 40g/40i/42 and
results/composition-design-review-fable.md. CPU only; tokenizer decode and node/python scorer
re-runs only; no model launch; nothing under data/bench read.

## Verdict

R1 is correctly applied under the pre-committed reading, every number in the README
reproduces from records.jsonl, and "actuator out of default shipping, rendering-only primary"
is the right engineering decision now. The screen is at ceiling, so it cannot show additivity
and was never able to; that limits what R1 means, and the README already says so. One
provenance nit (audit.json was not produced by the committed audit()), one scoring blind spot
(10/16 bare replies in the combined arm violate the system prompt's code-block default and are
not counted), and one reading the README missed that matters for the next test: own-output
imitation IS visible in these records at the style level, and the mask demonstrably removes it.

## What was verified (all PASS unless marked)

1. Commit order. Recipe commit 3dddc28e at 08:42:20; resources.json (written by run() after
   the `git log -1` recipe lookup) at 08:42:26; runtime.json (post-load) 08:48:46; last record
   08:56:11; result commit 1b7ffb0f at 08:59:25. run() asserts the working script equals the
   committed blob before touching the GPU. prewritten-reading.md and the script are unchanged
   between the two commits (git blobs e5472214 / 13f74daa match the working tree; focus3.py
   blob 8541b529 matches freeze.json a4b319b5). Readings preceded inference.
2. Bias tensor. bias_sha256 = bda3d63e... on all 64 bias-arm records, null on all 160 others;
   equals the single hash in 40g/records.jsonl and the JS-bias hash in 40i/records.jsonl;
   file SHA 5776dfab... equals 40g/artifact-inventory.json. The bias was live, not just
   hashed: with byte-identical inputs and greedy decoding, text+bias diverges from text-only
   on 16/16 P1 tasks (fence label javascript -> js, one-line bodies) and bias-only diverges
   from OFF on 2/16 (parenthesisation only, still Python).
3. Cache-prefix sharing (P2). For every episode the four P2 arms carry the identical
   519-token cache_prefix_token_ids (one SHA per episode), the identical 65-token current
   input, and the rule appears only in the seventh user turn (six history user turns have no
   rule). History records chain 0/114/195/276/357/438 -> 519, each turn 53 input + 28
   generated (27 body + EOS). Decoded tail of the P2 input confirms the literal
   "Live rules: (1) Write all code in JavaScript." line directly above the request.
4. Mask traces. 32 masked generations, each with masked_positions = union of six body
   ranges [86,113]...[491,518] = 162 positions, every forward (prefill + each decode step)
   carrying the same masked set, absolute_length 519, no placeholders; non-mask arms have
   empty masks and null mask_event on all 192 records. Decoded masked span = exactly
   "```python\ndef ...\n```" (fence + label + code); EOS, headers, and user turns unmasked.
   Functional confirmation: P2 text+mask output is bytewise identical to the fresh-session
   P1 text-only output on 12/16 tasks, and 4-space-indent imitation drops from 16/16
   (P2 text-only) to 0/16 (P2 text+mask). The mask masked what it claimed and removed the
   history's influence on the output.
5. Scorer. Independent re-score of all 128 P1/P2 replies plus 16 sampled history replies
   with python `ast`+exec and node `vm.runInNewContext` (no TypeScript library): 144/144
   agree with the stored valid_skill; zero replies parse as both Python and JS; zero
   fence errors; all 96 history replies are correct Python, all 128 target replies correct
   in their emitted language.
6. Tallies and statistics. Per-arm JS/Python/broken/fence/first-token counts reproduce the
   README tables exactly. CP 95% for 16/16 = 0.025^(1/16) = 79.41%; 0/16 upper 20.59%;
   Bonferroni 97.5% CP upper for 0/16 = 1-0.0125^(1/16) = 23.96%, so the conservative
   paired-gain interval is +/-23.96 pp as stated. wins/losses/ties 0/0/16.
7. Task freshness. tasks() regenerates from seed 401006 after excluding every expression in
   40e and 40g banks (audit asserts equality with tasks.json); 16x7 = 112 fresh expressions.

## Findings

- LOW (provenance): audit.json contains fields (actual_input_tokens, boundary_fixtures,
  recipe_git_blobs_verified=17, independent_accounting, mask_positions_range ...) that the
  committed `audit()` in focus_check40j.py does not write; the committed audit writes seven
  keys. The extended audit that produced this file is not in the repo (no untracked file in
  check40j/). The records are self-verifying and I re-verified them, so no result changes;
  but "17 recipe-commit git blobs audited" and "boundary fixtures PASS" are currently claims
  from unrecorded code. Either commit the audit code or narrow the README words.
- MEDIUM (scoring blind spot, supports the decision): text+bias+mask emits 10/16 replies
  with no fence at all. The 40e system prompt says "Default to a code block defining the
  requested function unless the user specifies another format." Bare replies violate that
  default; the scorer counts them correct and not broken. The actuator therefore has a
  measurable presentation cost here that the headline "16/16 everywhere" hides. This is a
  reason for, not against, keeping the actuator out of default shipping.
- LOW (renderer discrepancy): the requested literal cue is shorter and plainer than
  focus3.render's "Active user rules for this request ... JSON ... Apply these rules while
  answering the request below. Current user request:" wrapper. Direction of risk: if the
  JSON wrapper were weaker than the literal, text-only could fall below ceiling and leave
  room for the actuator. Prior evidence against that: check 42 measured the actual JSON
  renderer (Qwen3-4B, real conversational bank) with 0 constraint failures in the A arm and
  A 99 vs BOTH 78 all-five. So the discrepancy does not weaken R1's direction, but it does
  mean the shipped renderer has never been run on Qwen3-30B in this harness. Fold that into
  the larger test (which uses the production renderer anyway); no separate screen.
- OBSERVATION (missed reading, important for next design): own-output imitation is present
  in 40j, just not on the scored axis. P2 text-only copies the six Python answers' 4-space
  indent on 16/16 tasks while P1 text-only (same rule, empty history) uses 2-space on 16/16;
  the language flip is governed by the rule, the style is governed by the history. The rule
  wins on the categorical dimension it names; the history wins on every dimension the rule
  is silent about. Relapse will therefore appear first on rules that compete with own
  style, not on "which language".

## Is the pressure too weak to show relapse?

Yes, on the scored axis. A one-item categorical language rule, rendered at distance zero in
the same user turn, on a one-line arithmetic function, against six 27-token own answers, is
a ceiling condition: text cues have been 32/32 or 16/16 on every form tested (40c/40d/40e/
41b/40j), including 40d's text SWITCH after JS history (32/32). No arm can beat 16/16, so
"adds nothing" was the only reachable outcome once P2 text-only hit ceiling. R1's correct
scope is "at this pressure", which the README states.

What pressure would be needed (from the 42 and 40j records, not speculation):
- Rule load: several simultaneous live rules (3-5), at least one that changes the natural
  default of the request type and one that is purely stylistic (indent, semicolons, naming,
  keep outer parentheses). 40j shows the model already ignores the rule's silence and copies
  its own style; a rule on that axis is where the six retained answers actually push back.
- Distance: irrelevant when the renderer runs every request at distance zero. Distance only
  bites a non-rendered rule, and that arm is already dead (42 settled it).
- Own-output count and length: 6 x 27 tokens did nothing on the categorical axis. To find
  the floor you need 10-20 prior own turns of 100-300-token bodies, i.e. real agentic code
  edits, not one-liners.
- Request form: edits to an existing file in the "wrong" language, or tool-call turns, where
  the rule conflicts with the visible artifact rather than with an empty default.

One more 20-minute arithmetic screen is not worth it: the harness cannot leave the ceiling on
the language axis, and a style-rule variant would still be an arithmetic one-liner. Go
straight to the larger agentic test with a rendering-only primary, and instrument relapse
there directly: per-turn rule-violation rate against turn index and cumulative own-output
tokens, per rule kind (categorical vs stylistic). Keep the JS bias + whole-body mask behind
a flag as a contingent arm, launched only if the rendering-only arm shows a violation floor
(say >= 15% of turns on some rule kind); 40j's mask result (bytewise restoration of the
fresh-session output on 12/16) says the mask is the half of the actuator worth keeping for
that contingency, and the fence loss says the bias is the half that costs presentation.

## Answers to the two direct questions

- Is R1 correctly applied? Yes. The fixed rule was text-only >= 14/16 in both phases;
  observed 16/16 and 16/16, complete run, no enlargement. The README's hedges (n=16, one
  harness, +/-23.96 pp gain interval, not an equivalence proof) are accurate and sufficient.
- Is "actuator out of default shipping" right now? Yes. Stack: bias alone is weaker than a
  plain prompt prior (40g 3/8, 40j 0/16 with the bias provably live); rendered text is at
  ceiling on every form tested; masking is dominated by rendering where both were measured
  (42); the combined arm's only visible effect here is presentation drift (bare functions
  10/16, js fences) that violates the system default. Ship the register + every-request
  render; keep bias+mask behind a flag with the 40i certificate; decide the contingent arm
  from measured relapse in the agentic test, not from another arithmetic screen.
