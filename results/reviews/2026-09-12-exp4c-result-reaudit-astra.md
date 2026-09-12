VERDICT: ACCEPT  
READING: NOT PROVEN, FINAL

The corrected evidence is technically valid and complete. The registered decision rule prescribes **NOT PROVEN, FINAL**, with the interim-look deviation disclosed. Finding numbers below retain the first audit’s numbering and severities.

1. **High — resolved: reminder provenance.** Independently reconstructed **139/139** focus sessions. Every corrected boundary equals the package’s base-window cut; every kept span slices the source thread correctly, identifies the correct message, and reproduces the reminder in the registered packing order. Counts and thread digests also match.

   The original example, `267-29`, now correctly records boundary **55,669**, **543** evicted sentences, and first kept span **[54,031, 54,107)** in message **581**. The [repair report](/home/bmarti44/stencil-llm/results/memorycode-long/screen_long_4c-4b-package-role_evicted/reprovenance-4c.json) reconciles all 139 changes.

   Against pre-repair commit `8edaf894`, **only `reminder_sources` changed in the terminal records**. All **278 raw-output files are byte-identical**; prompts, reminders, generated tokens, scores and failure flags are unchanged. Previous provenance remains recoverable from the preserved raw files and Git. The current and superseded summaries differ **only in `git_sha`**.

2. **High — disclosed procedural deviation; nonblocking under this re-audit’s instructions.** The owner-directed inspections at **75 and 100 pairs** violated the original no-interim-look clause. [RESULTS-4C.md](/home/bmarti44/stencil-llm/results/memorycode-long/RESULTS-4C.md:143) explicitly records that deviation. Receipts establish completion at the original frozen **N = 139**, without extension, regeneration or early termination. Acceptance preserves this history and applies to the complete, nonpositive terminal report.

3. **Low — verified: the mechanical reading reproduces.** Independent calculations give mean off **0.084470691333**, mean on **0.104926881175**, and difference **+2.045618984235 percentage points**. Sample SD is **0.125930811275**; paired **t(138) = 1.915138312290**, **p = 0.057543815387**, with primary 95% interval **[−0.066400621456, +4.157638589925] points**.

   Because that interval includes zero, [the registered row](/home/bmarti44/stencil-llm/results/memorycode-long/REGISTRATION-4C.md:156) selects **NOT PROVEN, FINAL**. The bootstrap companion reproduces **[+0.142973961496, +4.304961824152] points**; wins/losses/ties are **25/17/97**, sign-test **p = 0.279956238529**. Neither companion replaces the primary. Both descriptive subsets also reproduce.

4. **Medium — resolved: failure wording.** Failures reproduce as **60/139 off versus 61/139 on**, with **9 on-only and 8 off-only**. The difference is **+0.719424460432 points**, 95% interval **[−5.165744659443, +6.604593580306]**, paired-t **p = 0.809361539233**. Noninferiority remains unresolved; neither increased failures nor equivalence is established. The corrected wording reflects this. Strict compliance reproduces as **0 versus 1**, McNemar **p = 1**, interval **[−3.094313722028, +4.502737563390] points**.

5. **Low — verified: qualification and frozen identities remain intact.** Frozen items, candidate definitions and qualification artifacts are unchanged. All **44 qualification-call receipts** are byte-identical to the pre-repair versions; comparisons reproduce **16/16 off/plain matches** and **8/8 package replays**. The eight timing calls give **t_max = 68.688911280944 seconds**, hence **N = min(196, floor(28,800 / (3t_max))) = 139**. All ten package files other than weight shards match their recorded hashes.

6. **Low — verified: completeness and budget.** There are **139 valid terminal pairs**, **278 linked raw outputs**, and **556 attempt rows**, comprising 278 starts and 278 ends. No missing, duplicate, extra or open attempts were found. Candidate order and arm alternation match registration. Generation spending is **9,101.324 / 28,643.276 seconds**; evaluation overhead **371.982 / 2,700 seconds**; qualification **2,749.020 / 3,600 seconds**. All six process receipts end cleanly.

7. **Low — verified: scoring, prompts and validator behavior.** All **278 re-scores**, failure dictionaries, decoded outputs and EOS transformations match. All **278 prompts** reconstruct exactly at **3,584 tokens**. Every focus reminder fits 256 tokens; mean usage is **246.064748201439**. The complete in-memory analysis reproduces the saved summary. Deliberately corrupted sentence, count, boundary and missing-provenance cases are rejected through the actual record validator.

8. **Low — chronology substantially corrected; one wording qualification remains.** [RESULTS-4C.md:9](/home/bmarti44/stencil-llm/results/memorycode-long/RESULTS-4C.md:9) says no statistic changed “between them,” following a description of all three summaries. Literally, the first defective summary reported **n = 0** and INCOMPLETE. Numerical invariance is verified between the **second and current summaries**, across the provenance repair. This wording issue does not invalidate the corrected evidence or alter its prescribed reading.

**No HF release is authorized by this result.** I wrote no files, loaded no models, used no GPU, and read nothing under `data/bench/`.
