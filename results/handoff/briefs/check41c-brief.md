# Quick check 41c for gpt-6-astra: NEURONS INSIDE THE FAVORED EXPERTS of Qwen3-30B-A3B (2026-09-05)

Brian's direction: "we want to focus more on the neurons." Dense-model neuron attempts failed (check 41: frequency
selection, 0/64; check 41b: gradient attribution, junk first tokens). Hypothesis: neurons inside the experts that the
JavaScript routing profile favors are specialized enough to carry the skill, unlike shared dense-model neurons.
Reuse the 40b/40c/40d plumbing (model, profiles, parsers, task bank, 64-token caps, seeds 41043); router bias OFF
unless an arm says otherwise.
DESIGN (write the reading BEFORE running):
- CANDIDATES: per layer, the experts whose profile margin (JS - Python mean router logit) is in the top 2 of 8; their
  FFN intermediate neurons (act_fn(gate)*up, before down_proj) are the candidate pool.
- SELECTION BY ACTIVATION PATCHING (not gradient): on 16 uncued fit tasks, run the JS-cued twin to get per-neuron
  activations at the decision position (the fence-label token, per check 40b review); for candidate neurons in
  batches (per expert per layer), patch the uncued run's activations to the cued values and measure the shift in the
  JS-vs-Python first-token logit contrast c; rank neurons by mean shift; select top-k, k in {100, 400, 1600}; report
  layer/expert distribution and how much of the total cued-vs-uncued shift the selected set explains (patch all
  selected together vs patch everything).
- ACTUATORS on 8 setup tasks: (i) CLAMP the selected neurons to their cued mean profile (sustained at every generated
  position, applied only when the token is routed through that expert); (ii) SCALE by (1+g), g in {1, 3}; each with
  router bias OFF and with router bias alpha 3 ON. Pick the best OFF-bias cell by (JS induced, then breakage); freeze.
- SCREEN (32 fresh uncued tasks, single-shot SET): arms correct (neurons only, bias OFF), correct+bias (neurons + alpha 3),
  bias-only reference (from 40c, no regeneration), shuffled neurons (random matched size within the same experts),
  OFF, text-cue. Score language by parsers, task check, breakage, first token.
- READING (fixed): NEURONS SUFFICE if correct (bias OFF) yields valid JS >= 20/32 with breakage <= 2/32 and shuffled
  <= 4/32; NEURONS ADD if correct+bias beats bias-only on task pass or breakage by >= 4/32 with JS >= 30/32;
  MARGINAL if correct >= 12/32; else NEURONS DO NOT CARRY IT on this trunk — state plainly.
Cost cap 1.5 GPU-h (project first; scale to 16 tasks if needed and record). RUNNING.flag protocol; never signal.
Unregistered, disclosed; outputs under results/quick-checks/check41c/; item 41c in results/quick-checks/README.md
(5 lines); WORKLOG entry (<= 6 lines). Commit with explicit pathspecs (git add -f for results); no push. Foreground
only; never terminate or signal any process; never read the sealed IFEval input file or the sealed BFCL cohort
contents; nothing fit or trained (patching/ranking is measurement).

## REVISION (Brian, 2026-09-05, before this check started): target the FINER level that routing does not separate
Routing already separates Python from JavaScript; neurons inside a JS-favored expert should carry distinctions WITHIN
JavaScript. PRIMARY target = within-language STYLE with the router bias holding the language:
- JS style pair: MODERN (const/let + arrow functions + template literals) vs LEGACY (var + function declarations +
  string concatenation). Checker: parse with node --check, then count style markers via regex/AST on the parsed code
  (arrow "=>" and const/let vs "function " and var); a reply is MODERN if >= 2 modern markers and 0 legacy declarations,
  LEGACY if the reverse; else MIXED. Record the uncued default style distribution first (with router bias alpha 3
  holding JS).
- Optional Python pair (if time): COMPREHENSION vs explicit LOOP for list-building tasks (ast-based checker).
- SELECTION: as before, but the patching contrast is the style decision (patch from a MODERN-cued vs LEGACY-cued run at
  the first style-revealing token); candidates = neurons inside the top-2 JS experts per layer.
- ACTUATORS/SCREEN: as before (clamp / scale; shuffled within the same experts; OFF; written style cue "Use modern
  ES6 style." / "Use old-style var and function declarations." as the bar), router bias alpha 3 ON in all style arms.
- READING (fixed): NEURONS SELECT THE VARIANT if the addressed style is produced >= 20/32 (valid JS, task pass) with
  breakage <= 2/32 and shuffled <= 4/32 off-default; MARGINAL >= 12/32; else NOT. The coarse language arm (neurons
  only, bias OFF) remains as a SECONDARY reading with its original thresholds.
