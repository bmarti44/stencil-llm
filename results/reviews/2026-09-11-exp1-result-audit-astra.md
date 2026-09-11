**The numerical results reproduce exactly. The report needs substantive corrections to its causal claims and its explanation of the artifact decision.** This audit used only read-only CPU reconstruction of saved artifacts; no model, GPU, network, or `data/bench/` contents were accessed.

I independently decoded and hashed the first-user messages in all 909 original records: **484 sources = 425 pairs + 59 singletons**. Seed-0 sampling from sorted hashes reproduces `selection.json` exactly, including the minimum-`ci` choice. The selected cohort contains **128 distinct sources and conversations**, drawn from 112 paired sources and 16 singletons. All 128 new records have schema 2 and matching source/key/eviction metadata; all **131 manifest entries** match their files. The registered sampling procedure is at [REGISTRATION.md:27](/home/bmarti44/stencil-llm/results/qwen/multiif-echo-only-128/REGISTRATION.md:27), implemented at [multiif_echo_only.py:66](/home/bmarti44/stencil-llm/scripts/multiif_echo_only.py:66).

The independently recomputed source-mean aged-adherence points are:

| Arm | Mean |
|---|---:|
| `full` | 62.500000 |
| `evicted` | 12.630208 |
| `clf_pinned` | 53.190104 |
| `clf_pinned_echo` | 57.356771 |
| `role_pinned` | 59.049479 |
| `clf_echo_only` | 54.687500 |
| `role_echo_only` | 66.666667 |

Using selection order, `numpy.random.default_rng(0)`, 10,000 source bootstrap resamples, percentile endpoints, and an independently calculated exact two-sided binomial sign test:

| Contrast | Mean | 95% bootstrap interval | Wins / losses / ties | Two-sided p |
|---|---:|---:|---:|---:|
| D1 | +2.669271 | [−1.757813, +7.291667] | 19 / 14 / 95 | 0.486850241665 |
| D2 | −7.617188 | [−13.085938, −2.083333] | 16 / 37 / 75 | 0.005486344877 |
| D3 | +11.979167 | [+6.184896, +17.709961] | 44 / 15 / 69 | 0.000203721857 |

These confirm every reported numerical entry in [RESULTS.md:14](/home/bmarti44/stencil-llm/results/qwen/multiif-echo-only-128/RESULTS.md:14) and [summary.json:16](/home/bmarti44/stencil-llm/results/qwen/multiif-echo-only-128/summary.json:16).

**Findings**

1. **HIGH — D2 is misrepresented as the effect of adding pins to an echo.**

   The report says “DEMONSTRATED HARM of pins given the role-rule echo” and “Adding KV pins to the role echo loses 7.6 points.” But D2 compares **role pin-only against role echo-only**. The former uses the original context; no role echo is present. Its pins also use a classifier-sized token budget, sometimes cutting sentences: I found partial-sentence pinning in 70/128 conversations. See [RESULTS.md:27](/home/bmarti44/stencil-llm/results/qwen/multiif-echo-only-128/RESULTS.md:27), [multiif_evict.py:271](/home/bmarti44/stencil-llm/scripts/multiif_evict.py:271), and [multiif_evict.py:838](/home/bmarti44/stencil-llm/scripts/multiif_evict.py:838).

   **DEMONSTRATED HARM is the correct registered directional label for choosing the role-pinned policy over role echo-only.** It does not identify an adverse incremental effect of pins conditional on echo. Correct the table and the artifact rationale accordingly; D1 supplies the actual pin-increment-given-echo comparison.

2. **HIGH — D3’s “same echo budget” and recency-selection interpretation overstate what was tested.**

   Only the role echo has an enforced 256-token ceiling. The classifier echo reuses the original selected text without that packing rule, exactly as registered. Independently reconstructed rendered lengths, including headers, are:

   | Policy | Mean tokens | Range |
   |---|---:|---:|
   | Classifier echo | 48.28125 | 0–160 |
   | Role echo | 76.21094 | 31–184 |

   The role echo is longer in **125/128** conversations; the remaining three prompts are identical. **Every candidate sentence fits in every conversation:** zero packing stops and zero empty role echoes. Thus this cohort tests retaining all prior-user candidate sentences against classifier filtering; it never exercises recency selection under a binding budget. The implementation follows [REGISTRATION.md:41](/home/bmarti44/stencil-llm/results/qwen/multiif-echo-only-128/REGISTRATION.md:41) and [multiif_echo_only.py:149](/home/bmarti44/stencil-llm/scripts/multiif_echo_only.py:149). The largest rendered role echo is documented at [conv-184.json:23](/home/bmarti44/stencil-llm/results/qwen/multiif-echo-only-128/conv-184.json:23).

   D3 validly establishes that the **registered role-echo policy** outperformed the registered classifier-echo policy here. Replace “at the same echo budget” and avoid attributing the gain specifically to recency selection or selection quality independently of retained content and length. See the offending claims at [RESULTS.md:28](/home/bmarti44/stencil-llm/results/qwen/multiif-echo-only-128/RESULTS.md:28) and [RESULTS.md:44](/home/bmarti44/stencil-llm/results/qwen/multiif-echo-only-128/RESULTS.md:44).

3. **MEDIUM — Keeping the classifier primary for Exp 4 can be defensible, but the stated justification is false and must be separated from D3.**

   D3’s registered decision rule unambiguously selects the **role rule as the default text selector** here. Nevertheless, Exp 4 evaluates a different bundle: classifier admission plus lifecycle relations over long coding sessions. Exp 1 does not test that bundle or establish which policy must win there. Retaining the classifier as a prospective Exp 4 primary can therefore be an independent research choice; it is **not a favorable conclusion about the classifier drawn from D3**. See [REGISTRATION.md:95](/home/bmarti44/stencil-llm/results/qwen/multiif-echo-only-128/REGISTRATION.md:95) and [plan section G:56](/home/bmarti44/stencil-llm/plan/BACK-ON-TRACK-PLAN.md:56).

   The claim that the classifier register is “the only policy” capable of carrying instructions from outside the window is false: the specified fallback does precisely that by reading the truncated-away region. Moreover, Exp 1 never tested budget-constrained selection over a long discarded region. See [RESULTS.md:46](/home/bmarti44/stencil-llm/results/qwen/multiif-echo-only-128/RESULTS.md:46) and [plan section G:78](/home/bmarti44/stencil-llm/plan/BACK-ON-TRACK-PLAN.md:78).

   **Answer:** D3 requires the role default for its registered text-package interpretation; it does not statistically require changing the primary of a distinct prospective bundle experiment. Preserve that distinction explicitly in RESULTS and G, remove the exclusivity claim, and describe classifier maintenance as an unproven Exp 4 hypothesis. No additional arm is needed.

4. **MEDIUM — Timing qualification and stopping safeguards were not implemented exactly as specified, although the recorded work stayed within budget.**

   The pilot’s maximum context was **1,322 tokens**, while the actual role arm reaches **1,414**. Thus maximum-context qualification did not cover the longest new-arm input. Compare [timing-pilot/multiif.json:51](/home/bmarti44/stencil-llm/results/timing-pilot/multiif.json:51), [conv-674.json:1095](/home/bmarti44/stencil-llm/results/qwen/multiif-echo-only-128/conv-674.json:1095), and the maximum-context requirement at [plan:360](/home/bmarti44/stencil-llm/plan/BACK-ON-TRACK-PLAN.md:360).

   The runner has count-based chunks but no reservation-time or cumulative-budget check. The wrapper records an ETA and waits; it does not enforce the registered five-minute stop-start rule. See [REGISTRATION.md:117](/home/bmarti44/stencil-llm/results/qwen/multiif-echo-only-128/REGISTRATION.md:117), [multiif_echo_only.py:174](/home/bmarti44/stencil-llm/scripts/multiif_echo_only.py:174), and [gpu_reserve.sh:45](/home/bmarti44/stencil-llm/tools/gpu_reserve.sh:45).

   Recorded conversation-loop time totals **4,598.40 seconds**, plus **174.59 seconds** for replay: **79.55 minutes**, excluding unrecorded startup/reservation overhead. The four conversation-loop totals are 32.68, 16.73, 18.24, and 8.99 minutes. There is no observed budget-exhaustion failure, but these qualification/enforcement limitations are undisclosed in RESULTS.

5. **LOW — Reporting and verification omissions need correction.**

   Report the explicitly required **zero empty role echoes**, measured execution time with its exclusions, and label the arm means **source means**, not “pooled.” The zero-count requirement is at [REGISTRATION.md:50](/home/bmarti44/stencil-llm/results/qwen/multiif-echo-only-128/REGISTRATION.md:50); the misleading heading is at [RESULTS.md:10](/home/bmarti44/stencil-llm/results/qwen/multiif-echo-only-128/RESULTS.md:10).

   The four supplied tests cover elementary statistics, summary behavior and packing, but do not test source-selection determinism, replay gating, or schema-2 generation end to end. See [test_multiif_echo_only.py:36](/home/bmarti44/stencil-llm/tests/test_multiif_echo_only.py:36). I inspected rather than executed the write-producing tests; the independent all-record checks above verify actual selection and packing.

**Reuse, safety, and readings**

The **8/8 replay satisfies the registered reuse gate**, including the correct first eight selected conversations and saved output lengths. It is sampled compatibility evidence, not proof covering every reused arm/output. The replay artifact retains equality flags and lengths rather than regenerated token sequences, so its comparisons cannot be independently repeated from that artifact alone. Supporting evidence is favorable: the current tokenizer matches the original recorded hash, and the current imported harness functions have unchanged ASTs relative to the historical harness matching the original hash. See [replay.json:1](/home/bmarti44/stencil-llm/results/qwen/multiif-echo-only-128/replay.json:1) and [multiif_echo_only.py:115](/home/bmarti44/stencil-llm/scripts/multiif_echo_only.py:115).

I found **no cross-arm output leakage**. Both echoes reconstruct from saved prior-user sentences; the role construction does not consume the preceding classifier-arm response. Every generation gets a fresh cache. Shared earlier assistant history is the registered common history. See [multiif_echo_only.py:190](/home/bmarti44/stencil-llm/scripts/multiif_echo_only.py:190) and [multiif_evict.py:336](/home/bmarti44/stencil-llm/scripts/multiif_evict.py:336).

Safety counts and every reported excess reproduce. Invalid and timed-out counts are zero for all arms; degenerate/truncated counts are:

| Arm | Degenerate | Truncated |
|---|---:|---:|
| full | 41 | 35 |
| evicted | 12 | 12 |
| clf_pinned | 32 | 28 |
| clf_pinned_echo | 28 | 27 |
| role_pinned | 26 | 23 |
| clf_echo_only | 33 | 31 |
| role_echo_only | 33 | 31 |

Thus all excesses are nonpositive, as reported at [RESULTS.md:34](/home/bmarti44/stencil-llm/results/qwen/multiif-echo-only-128/RESULTS.md:34). Safety definitions, generated lengths, decoded output text, zero new-arm pins, eviction coordinates, header accounting and chronological packing all pass reconstruction. Benchmark instruction scoring itself was not rerun under the prohibition on benchmark access.

Under [PROTOCOL rule 3:19](/home/bmarti44/stencil-llm/plan/PROTOCOL.md:19), **D1 insufficient evidence** is correct: its interval covers +2, so neither dispensability nor equivalence is established. **D2 demonstrated harm** is correct for the policy comparison, subject to finding 1. **D3 role-rule default** follows the registration exactly.

The descriptive role-versus-full difference is **+4.1667 points**. “Descriptive, not registered” and “on this cohort” appropriately restrict it to the observed means; replacing “recovers at least” with “had a higher observed mean” would avoid suggesting demonstrated noninferiority. See [RESULTS.md:30](/home/bmarti44/stencil-llm/results/qwen/multiif-echo-only-128/RESULTS.md:30).

**VERDICT: REJECT the current interpretation; retain the numerical results and sealed outputs.**

**Minimum edits:** correct D2’s causal wording; describe D3’s unequal lengths and nonbinding budget; preserve its registered role-default reading while explicitly separating Exp 4’s prospective classifier hypothesis; remove the “only policy” claim; disclose timing/stopping limitations and add the missing counts/costs. No new arm or outcome rerun is needed to correct this report.

Brian: The arithmetic is solid, and the role echo clearly wins this registered policy comparison on the exposed cohort. Keep the Exp 4 classifier primary only as an explicitly unproven maintenance hypothesis, while removing claims that Exp 1 demonstrated harm from adding pins to echo or validated long-window recency selection.
