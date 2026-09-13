Three blockers remain: an undercharged death observation, gate readings on incomplete records, and a demonstrated false session success.

**1. Previous four items**

| Item | Disposition |
|---|---|
| F13: interrupted-launch accounting | **PARTIAL.** Silence no longer bounds a charge, but the death observation can carry a timestamp from before termination. |
| F12: spend evidence and eligibility | **PARTIAL.** Missing/empty ledgers and budget refusals work. Missing checkpoints still reach gate calculations. |
| Ceiling and admission margin | **RESOLVED.** The calculation gives **47.2693 minutes**; 50 admits all 96 requests under the registered estimates. [a_screen.py:727](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:727) |
| Registered output cap | **RESOLVED.** The validation prefix refuses 2,048; the summary independently checks the registered constants. [a_screen_run.py:143](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:143), [a_screen_summary.py:285](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:285) |

**2. Accounting, eligibility, and legitimate refusals**

**F13 — high: the observation is backdated.** The runner samples `now` before calling `ledger_observe`; that value survives ledger reading and the PID probe unchanged. Absence at the probe establishes termination by the **probe time**, not by the earlier argument. [a_screen_run.py:263](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:263), [a_screen.py:649](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:649)

I reproduced this with a simulated scheduling delay: observation starts at 300 seconds, the old launch dies at 900, and the probe executes at 1,000. The appended line permanently charges **300 seconds**. Combined with 2,400 seconds of completed work, the real summary prints **GATE PASSED**: 45 minutes charged against **55 minutes actually spent**. The timestamp is written directly into the supposedly fixed evidence. [a_screen.py:651](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:651)

**Fix:** sample the observation timestamp after each successful absence check.

**F12 — medium: incomplete records bypass the short circuit.** Removing only `S48@2` from synthetic CF records, while retaining valid budget evidence, produces **12 PASS lines** and:

> INCOMPLETE (47/48 …); provisional: GATE PASSED

`missing` does not enter `ineligible`; it changes the verdict only after the gates have been calculated. [a_screen_summary.py:365](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:365), [a_screen_summary.py:442](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:442)

**Fix:** bypass contrasts and gates whenever required checkpoints are missing.

The reverse risks are real:

- **Ceiling:** the registered estimates fit. The five-minute admission rule can still refuse work that would finish inside 50 minutes; the timing pilot must establish adequate headroom. [a_screen.py:826](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:826)
- **Unobserved launch:** yes, legitimate low-spend work can be refused. A launch killed after 60 seconds but observed an hour after startup is permanently charged **60 minutes**. I reproduced that. Prompt observation limits this conservative overcharge; a delayed relaunch cannot recover the actual termination time. [a_screen.py:656](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:656)
- **Coverage:** I found no rejection of correctly recorded resumptions. A two-launch, 40-minute control passes. Missing launch evidence appropriately causes refusal. [a_screen.py:817](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:817)

**3. Repository correctness and J**

**High: S35 still awards J = 1 after allocator corruption.** Add `self._n = 0` as the first statement of `OrderBook.collect`, then retain that file while applying ordinary checkpoint-2 gold. **Every suite passes at both checkpoints.**

The public counterexample is straightforward: place an order, collect it, then place another. Both receive **`O1`**, and the second overwrites the first. [s35.py:38](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s35.py:38), [s35.py:253](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s35.py:253)

The existing allocator audit misses this because its write detector excludes `self.save(...)`. It classifies the delegating writer as a pure reader and skips the mutation. [a_screen_mutate.py:601](/home/bmarti44/stencil-llm/scripts/a_screen_mutate.py:601)

**Fix:** include delegating writers in the existing allocator audit and test subsequent insertion and preservation of earlier records.

I found no new demonstrated false **J = 0**. This was not an exhaustive proof of scorer correctness.

**4. Other effects of amendment 7**

PID absence is meaningful only in the launch’s PID namespace; `/proc` visibility is namespace-dependent. The registered wrapper launches normally, and model generation occurs in the runner process, so I found no separate orphaned GPU-worker path in that command. PID recycling conservatively prolongs charges; it does not undercharge them. The demonstrated observation defect is its timestamp. [Linux PID-namespace documentation](https://www.man7.org/linux/man-pages/man7/pid_namespaces.7.html), [gpu_reserve.sh:55](/home/bmarti44/stencil-llm/tools/gpu_reserve.sh:55), [a_screen_run.py:488](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:488)

The original low ambiguity finding is **RESOLVED**: `a = B(); replace(a, ...); a = A()` now reports UNRESOLVED. Current enumeration yields **961 mutants, 131 update sites, zero unresolved sites**. That enumeration does not cover the skipped allocator mutation above. [a_screen_mutate.py:338](/home/bmarti44/stencil-llm/scripts/a_screen_mutate.py:338)

**5. Statistics and five gates**

Still §7 for an eligible, complete evaluation. I recomputed McNemar **0.0625** for 5–0, **0.25** for 3–0, and the zero-discordance interval **±0.0872490536** at N = 48. All five count rules remain unchanged. [a_screen_summary.py:143](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:143), [a_screen_summary.py:195](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:195), [a_screen_summary.py:396](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:396)

**6. Interpretability and verification limits**

All **48 SCREEN and 576 TRAIN content hashes match** their frozen records. The 26 spend-test functions passed using in-memory file adapters; the reproductions exercised the actual summary function. S35 scoring used an in-memory test executor because this workspace is read-only, not the full subprocess audit. No GPU work, repository edits, or `data/bench/` access occurred.

The shortest launch-changing list is:

1. Timestamp death after the successful PID probe.
2. Suppress contrasts and gates when required records are missing.
3. Cover and detect allocator corruption in delegating writers, including S35.

**DO NOT LAUNCH**
