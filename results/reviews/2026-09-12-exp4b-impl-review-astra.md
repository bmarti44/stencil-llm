**Reviewer: Astra | Model: GPT-6 Astra | Date: 2026-09-12 | Read-only implementation review**

**BLOCK.** Exp 4B can be a legitimate prospective registration and the second policy revision, but the implementation has launch blockers: SCREEN summarization crashes without oracle records; qualification lacks an enforced completeness gate; summaries do not validate record configurations; timeout scoring contradicts the newly appended BUDGET line; and cumulative budget exhaustion is not implemented in the reviewed runner. The frozen item metadata and disclosed fractional numbers reproduce. Both appended tests passed when invoked directly on CPU, but they miss these failures. I wrote no files, ran no models, used no GPU, and did not access `data/bench/`. This review includes the BUDGET line added while the review was running.

1. **[high] Freeze the weighting unit explicitly: the implementation averages regex checks within required families.**

   [REGISTRATION-4B.md:21](/home/bmarti44/stencil-llm/results/memorycode-long/REGISTRATION-4B.md:21) says “mean official family score over the families REQUIRED.” However, [memorycode.py:392](/home/bmarti44/stencil-llm/src/stencil/memorycode.py:392) averages each matching `history_regex` entry. Families can appear repeatedly: item `352-99` has **12 required families but 32 included checks**, with repeated method-decorator checks visible at [items.json:42](/home/bmarti44/stencil-llm/results/memorycode-long/items.json:42). Across the cohort, **98/144 items** have more included checks than distinct required families. This is a material weighting distinction.

   Recomputed checks otherwise pass: **144 unique items and dialogues; 16 SETUP and 128 SCREEN; one query each; zero inapplicable items; zero mismatches** between stored `required`/`structure` and the query rules; and **zero required families without a matching regex**. Correctly formed generation records cannot change the denominator through their output.

   The structure-zero convention is coherent: it gates the entire item score and adds no denominator term, so it does **not arithmetically double-count** missing structure. It deliberately withholds credit for otherwise satisfied conventions when the requested parent structure is absent.

   **Required wording, preserving the implemented estimand:**
   > “For item \(i\), freeze the list of `history_regex` entries whose family belongs to `required_i`. Each retained regex check receives equal weight, including multiple checks belonging to the same family. The item score is their arithmetic mean, with absent required parents scored zero; missing required structure sets the entire item score to zero. Items receive equal weight in the cohort mean.”

   Also validate equal `scores`/`regexes` lengths and required-family coverage before scoring; the current `zip` silently truncates malformed inputs.

2. **[high] The registered SCREEN configuration crashes during summarization.**

   [memorycode_screen.py:897](/home/bmarti44/stencil-llm/scripts/memorycode_screen.py:897) always includes oracle contrasts, while [memorycode_screen.py:1056](/home/bmarti44/stencil-llm/scripts/memorycode_screen.py:1056) correctly defaults SCREEN to base/focus only. Therefore oracle contrasts pass empty arrays into `_paired_mean_bootstrap`.

   At [memorycode_screen.py:654](/home/bmarti44/stencil-llm/scripts/memorycode_screen.py:654), `sum(sample) / n` executes before the later conditional handling of `n == 0`. I reproduced **`ZeroDivisionError` through `phase_summarize` with all 128 base/focus pairs and no oracle records**. Empty primary input also crashes.

   **Required change:** return an explicit empty result before entering the bootstrap loop: `n=0`, null mean/bounds, zero wins/losses/ties, and the registered no-discordance p-value convention. Reject unequal input lengths rather than silently truncating them.

   Extend the consumer test at [test_memorycode.py:694](/home/bmarti44/stencil-llm/tests/test_memorycode.py:694) to cover a complete SCREEN with **zero** oracle records, an incomplete primary, and an empty primary. Its existing partial-oracle fixture conceals this failure.

3. **[high] Qualification needs its own complete, mechanical decision.**

   The three numerical ingredients are correctly available:

   - `mean_fraction_required.oracle`;
   - `output_failure_excess_over_base.focus.excess_fraction`;
   - `contrasts.focus_vs_base.fraction_required_bootstrap.upper_points`.

   `_failure_excess` implements the registered focus-only discordance at [memorycode_screen.py:744](/home/bmarti44/stencil-llm/scripts/memorycode_screen.py:744). The threshold permits **zero** focus-only failures at \(n=16\), and **six** at \(n=128\).

   But [memorycode_screen.py:806](/home/bmarti44/stencil-llm/scripts/memorycode_screen.py:806) defines primary completeness using base/focus alone; oracle means use whichever records exist. No qualification Boolean is produced. An in-memory consumer check with **16 base/focus pairs and one oracle record** returned `primary_complete=true`, oracle mean `.3`, failure excess `0`, and positive upper bound—satisfying all three numerical comparisons on an incomplete qualification cohort.

   **Required change:** emit a qualification object requiring the exact 16 frozen items, valid terminal base/focus/oracle records for every item, and all three registered inequalities. Make the SCREEN launch consume that decision. Missing qualification records must mean INCOMPLETE, rather than qualification failure or success.

   I agree with the proposed interpretation of condition (c), under the independent-dialogue sampling assumption: a frozen SETUP-only stop rule can prevent SCREEN without selecting SCREEN outcomes or changing its estimator. Publish stopped SETUP runs and prohibit subsequent tuning or pooling into SCREEN. Also describe `upper == 0` accurately: it fails this gate but does not demonstrate strictly negative harm.

4. **[high] Summary completeness does not establish configuration or scoring validity.**

   Model loading and normal routing are correct: [memorycode_screen.py:297](/home/bmarti44/stencil-llm/scripts/memorycode_screen.py:297) selects the 4B configuration/checkpoint, and [memorycode_screen.py:382](/home/bmarti44/stencil-llm/scripts/memorycode_screen.py:382) produces `setup_long-4b-role_evicted/`. The two tokenizer files have identical SHA-256 hashes. `_record_matches` rejects a 1.7B record during a 4B resume.

   The summary path, however, reads records and checks only IDs and arm presence at [memorycode_screen.py:811](/home/bmarti44/stencil-llm/scripts/memorycode_screen.py:811). It labels the model from the CLI at line 847. I reproduced a **4B, confirmatory, PROVEN** summary from synthetic records marked `model="1.7b"`.

   There is also a subset path: completeness is calculated before inapplicable items are skipped at [memorycode_screen.py:829](/home/bmarti44/stencil-llm/scripts/memorycode_screen.py:829). Making one frozen item inapplicable yielded `primary_complete=true`, `n_primary=127`, and PROVEN. This does not occur with today’s verified metadata, but the consumer does not enforce the registered \(N\).

   Legacy recomputation using saved `per_family`, `structure_present`, and current item metadata reproduced fresh scoring on the inspected SETUP records. The fallback at [memorycode_screen.py:714](/home/bmarti44/stencil-llm/scripts/memorycode_screen.py:714), however, substitutes the old output-dependent `fraction` when scores are absent.

   **Required changes:** validate model/configuration manifests and terminal scoring records during summarization; require the exact registered primary cohort and scored count; reject the old-fraction fallback for confirmatory records; restrict Exp 4B confirmatory readings to model `4b`. Add `window` and `budget_tokens` to `_record_matches`’ comparison keys at [memorycode_screen.py:425](/home/bmarti44/stencil-llm/scripts/memorycode_screen.py:425); both currently can differ while matching succeeds.

5. **[high] Timeout handling contradicts the new BUDGET line.**

   The appended [REGISTRATION-4B.md:115](/home/bmarti44/stencil-llm/results/memorycode-long/REGISTRATION-4B.md:115) explicitly states that a timeout “scores 0.0 on the primary.” At [memorycode_screen.py:563](/home/bmarti44/stencil-llm/scripts/memorycode_screen.py:563), only `strict` is forced false. `_required_fraction_of` likewise ignores `timed_out`.

   A compliant synthetic generation subjected to the runner’s timeout score override retained **`fraction_required=1.0`**.

   **Required change:** force `fraction_required=0.0` on terminal timeouts in the generation record and apply the same rule during legacy recomputation. Add a test where otherwise compliant output times out. This implements the currently written registration without changing its outcome definition.

6. **[high] Chunk limits exist; the registered cumulative stopping rule does not.**

   [memorycode_screen.py:475](/home/bmarti44/stencil-llm/scripts/memorycode_screen.py:475) enforces a per-invocation budget using remaining arms at their full deadlines. The reviewed runner does not accumulate generation seconds across resumptions or enforce the total/SCREEN ceilings. `fraction_reading` at [memorycode_screen.py:682](/home/bmarti44/stencil-llm/scripts/memorycode_screen.py:682) cannot distinguish a complete run that exhausted its budget. The reservation wrapper merely waits for the command at [gpu_reserve.sh:55](/home/bmarti44/stencil-llm/tools/gpu_reserve.sh:55).

   **Required change:** implement cumulative accounting in the runner or identify and register the exact launch-driver implementation. Reconstruct spending from terminal records across chunks, stop on the registered ceiling, and expose budget exhaustion to summarization so it produces INCOMPLETE even if the last completed generation crossed the ceiling.

   The requested hypothetical arithmetic is feasible across repeated slices:

   | \(t_{\max}\) | \(1.5t_{\max}\times48\) SETUP | \(1.5t_{\max}\times256\) SCREEN | Total, 304 generations |
   |---|---:|---:|---:|
   | 150 s | 3.00 h | 16.00 h | **19.00 h** |
   | 200 s | 4.00 h | 21.33 h | **25.33 h** |

   With 300-second deadlines, SETUP needs 15 minutes remaining and SCREEN 10, so new items stop starting at minutes **35** and **40** respectively. Ignoring loading/packing overhead, constant 150-second generations fit five SETUP or eight SCREEN items per slice; at 200 seconds, four or six. That gives approximately **20 or 26 slices**, respectively. Pilot and parity spending are additional.

   The pilot added during review is substantially faster. Recomputed directly from [memorycode-long-4b.json:5](/home/bmarti44/stencil-llm/results/timing-pilot/memorycode-long-4b.json:5):

   - \(t_{\max}=47.641592214\) s; mean \(=38.500614041\) s.
   - Total ceiling \(=21,724.566050\) s, **6.034602 h**.
   - SCREEN ceiling \(=18,294.371410\) s, **5.081770 h**.
   - Expected main generation time at the pilot mean: **3.251163 h**; SETUP **30.800491 min**.

   Freeze the **full-precision pilot value** as authoritative. The displayed equation at [REGISTRATION-4B.md:121](/home/bmarti44/stencil-llm/results/memorycode-long/REGISTRATION-4B.md:121) is literally incorrect: \(1.5\times47.6\times256=18,278.4\), not 18,294. Also replace the assertion that the factor “absorbs contention” with “the fixed spending allowance is 1.5 times the measured pilot rate; exhaustion remains INCOMPLETE.”

7. **[medium] The statistics are usable, but the power and sign-test interpretation need correction.**

   For nonempty, equal-length inputs, resampling paired differences is correct. `random.Random(seed)` isolates and resets the RNG; ties remain in the bootstrap and are excluded from the sign test. The endpoint indices at [memorycode_screen.py:661](/home/bmarti44/stencil-llm/scripts/memorycode_screen.py:661) are **250 and 9749**, giving order statistics **251 and 9750**: trimming 250 draws from either end. This is a defensible central-order-statistic convention; specify it explicitly because percentile conventions differ. Coverage is approximate, rather than an exact finite-sample guarantee. [NumPy quantile conventions](https://numpy.org/doc/stable/reference/generated/numpy.quantile.html), [SciPy bootstrap documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html).

   The sign test is a useful directional companion: it tests equal win/loss probability among nonzero differences. It does not test the same mean-effect null as the bootstrap interval. [Sign-test definition](https://www.statsmodels.org/stable/generated/statsmodels.stats.descriptivestats.sign_test.html).

   The 1.7B SETUP calculation reproduces **−5.166986 points**, interval **[−10.556584, −0.428417]**, sample SD **10.681173**, and sign \(p=0.0703125\). At \(N=128\), \(s/\sqrt N=0.944091\) points, or **1.888182** if spread doubles. A normal-approximation 80%-power calculation gives detectable gains of approximately **2.645 or 5.290 points**.

   The sentence “A positive reading needs most items to move in the same direction” at [REGISTRATION-4B.md:63](/home/bmarti44/stencil-llm/results/memorycode-long/REGISTRATION-4B.md:63) is false. Four gains of 1.0 and 124 ties produce **+3.125 points [0.78125, 6.25]**, sign \(p=.125\), and satisfy the efficacy gate.

   **Required wording:**
   > “The bootstrap interval determines the primary efficacy reading. The sign test is a descriptive directional companion and may disagree. Strict compliance is descriptive and cannot establish or rescue the claim. Approximate 80%-power detectable gains are 2.6 points at the observed SETUP spread and 5.3 points at twice that spread; these are planning approximations.”

   This preserves exactly one primary claim. The existing “secondary, never as the gate” wording at registration line 31 is already sufficient to exclude strict from the efficacy decision. `--primary fraction` changes the reading and its label, not generation.

8. **[medium] The new-registration status is defensible; disclose the first-query restriction and instrument repairs precisely.**

   [Plan J:220](/home/bmarti44/stencil-llm/plan/BACK-ON-TRACK-PLAN.md:220) explicitly registers the model/estimand change and consumes revision two. Revision one and its SCREEN-informed CPU diagnostics are already disclosed in inherited [REGISTRATION.md:144](/home/bmarti44/stencil-llm/results/memorycode-long/REGISTRATION.md:144). I found no SCREEN generation records in either cohort root. The generated short SETUP and LONG SETUP dialogues have **zero overlap with LONG SCREEN dialogues**.

   Consequently, these disclosed development looks do not themselves make the prospective 4B SCREEN non-confirmatory. They do make the SETUP comparisons post hoc, as stated.

   The remaining omission is that `_required_fraction_of` uses **only `generations[0]`**, at [memorycode_screen.py:713](/home/bmarti44/stencil-llm/scripts/memorycode_screen.py:713), even for multi-query short items. The disclosed short means reproduce as **.031250 / .098958 / .203125 / .255208** under that restriction. Averaging the required-score generations within each short item instead gives **.093576 / .132986 / .224479 / .278125**. These are different descriptive summaries.

   **Required disclosure:**
   > “The post-hoc 4B short-cohort fractional analysis uses only the first query of each of the 16 items, matching the LONG protocol. The oracle qualification threshold was chosen after these descriptive outcomes were available.”

   Also link the instrument-repair disclosure at [LEDGER.md:3668](/home/bmarti44/stencil-llm/plan/LEDGER.md:3668): cumulative oracle replay and the Unicode speaker-parser repair, including regeneration of the LONG SETUP focus output for `314-49`. “Corrected oracle” alone does not disclose that focus regeneration. Correct the last registration entry’s “only oracle reads labels” shorthand to the precise label-use wording already present in the registration.

9. **[medium] The 14-GB reservation excludes a larger CPU loading peak on unified memory.**

   [memorycode_screen.py:297](/home/bmarti44/stencil-llm/scripts/memorycode_screen.py:297) constructs the model before loading the checkpoint and casting to bf16. Its parameter constructors use the default floating dtype at [qwen3.py:254](/home/bmarti44/stencil-llm/src/stencil/qwen3.py:254) and [qwen3.py:373](/home/bmarti44/stencil-llm/src/stencil/qwen3.py:373). PyTorch starts with float32 as that default. [PyTorch dtype documentation](https://docs.pytorch.org/docs/2.14/generated/torch.set_default_dtype.html).

   Recomputing from the 4B configuration and constructors gives **4,022,468,096 parameters**: the float32 model alone occupies **16.089872 GB**, before checkpoint tensors and process overhead. A simultaneously resident bf16 checkpoint brings tensor storage to approximately **24.134809 GB**. The pilot records CUDA allocator peaks only, after loading, at [timing_pilot.py:151](/home/bmarti44/stencil-llm/scripts/timing_pilot.py:151) and line 158. Its **9.662109 GiB reserved** measurement does not bound that loading peak.

   **Required change:** increase the current loader’s reservation to cover loading tensors plus process overhead, or implement and substantiate a lower-memory loading path. Label the pilot’s `/2**30` measurements as GiB. This is a resource-accounting correction, not another policy revision.

**Minimum edits before SETUP-LONG 4B launch:**

- Specify regex-check weighting, bootstrap/sign-test interpretation, and the missing development disclosures.
- Fix empty bootstrap handling and add the zero-oracle SCREEN consumer case.
- Validate record configurations, terminal scores, exact primary \(N\), and complete three-arm qualification.
- Implement zero fractional credit for timeouts, including legacy recomputation.
- Enforce cumulative budget exhaustion using the full-precision pilot ceiling.
- Correct the loading-memory reservation and run the targeted CPU regression checks for these changes.
