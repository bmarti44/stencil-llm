The experiment is salvageable without another review loop. **The 71% calculation is correct, but it is not a sound headline for the arm comparison.** There are also two concrete implementation fixes: replay failed replies correctly, and remove the runner’s obsolete minimum training duration.

I used read-only, in-memory execution of the authored test functions; I did not run the temporary-directory pytest harness, read `data/bench/`, or perform GPU work.

1. **CONFIRMED — deleting the fixture was sound.**

   The pool matches `eecde769^`, and all 48 content hashes reproduce the restored freeze `ef802ce2160ee00c`. The amendment-6 operation-specific checks remain, including [s08.py:341](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s08.py:341), [s10.py:363](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s10.py:363), and [s35.py:370](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s35.py:370).

   I reproduced that the public `initialize_bank` refactor now passes every applicable suite at both checkpoints. Removal eliminates a demonstrated false rejection. **This is fine.** It also removes some damage detection; that does not establish equal effects across arms.

2. **REFUTED — identical instruments do not guarantee nondifferential measurement error. Medium.**

   An adapter can change which implementation shapes appear. The concrete missed shape is:

   ```python
   account = self._accounts[account_id]
   self._n = 0
   # otherwise correct operation
   ```

   I reproduced that this S34 corruption still passes every applicable suite at both checkpoints. The tests exercise spending and lookup, but do not create another account after spending. An arm producing this shape more frequently receives more false correctness credit. Conversely, an arm avoiding it receives no measured benefit. [s34.py:64](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s34.py:64), [s34.py:91](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s34.py:91).

   The mutation escape fraction is **not** an estimate of model-output error, nor evidence that errors distribute equally across arms.

   **Fix:** drop the “only equal noise” argument. Treat allocator correctness as incompletely measured; this does not require rebuilding the audit to interpret the narrower contract-state result.

3. **REFUTED as the proposed primary comparison; the reported arithmetic reproduces.**

   For the first 24 sessions, I reproduced **22 in-force, 9 other-state, 17 neither**: 45.8%, 18.8%, 35.4%, and **22/31 = 71.0%**. All reconstructed repository hashes matched those records, and all in-force results matched the saved contract scores. [off.jsonl:1](/home/bmarti44/stencil-llm/results/a-screen/runs/off.jsonl:1).

   **(a) High — conditioning can manufacture an apparent improvement.** The conditional rate legitimately describes an arm’s own decidable outputs. It does not compare a fixed population across arms. For example, changing `(current, stale, neither)` from `(40, 40, 20)` to `(40, 10, 50)` raises the conditional rate from 50% to 80% without producing one additional current-rule success.

   There is also consequential pooling: `other(state)` is not necessarily superseded. Stable sessions never supersede that rule, and many request-1 alternatives have not yet been stated. The script pools these with actual post-change requests. [stale.py:47](/tmp/claude-1000/-home-bmarti44-stencil-llm/14c2306d-603f-4fa8-b992-19e1aefb2f05/scratchpad/stale.py:47).

   On **request 2 in changed sessions**, those same first 24 sessions give **4 current, 6 stale, 8 neither**—**40%**, not 71%, among decidable replies.

   **Fix:** compare unconditional category frequencies on the same changed-session request-2 items; retain the conditional rate as descriptive. Show stable/request-1 results separately.

   **(b) Medium — BOTH is possible, and “states agree here” is wrong.** Every naming suite explicitly excludes the alternative name, so merely implementing both names fails both. [s01.py:155](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s01.py:155).

   But S34’s two missing-record suites use different bank setups. I demonstrated a reply that returns `None` for an unknown ID when an account has tokens, otherwise raises `KeyError`: **both suites pass**, although neither convention permits that distinction. [s34.py:111](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s34.py:111), [s34.py:122](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s34.py:122).

   **Fix:** keep BOTH as a separate, unresolved classification. Do not count it as agreement or successful state discrimination. The first-24 snapshot contained zero BOTH cases.

   **(c) High — reconstruction is correct only along successfully applied histories.** After an invalid first reply, the runner retains the original files; `repo_for` instead returns `None`, losing a potentially successful request 2. It also applies parseable timed-out/truncated outputs that the runner rejected, because it ignores `terminal_reason`. The current reply has the same problem. [stale.py:19](/tmp/claude-1000/-home-bmarti44-stencil-llm/14c2306d-603f-4fa8-b992-19e1aefb2f05/scratchpad/stale.py:19), [stale.py:53](/tmp/claude-1000/-home-bmarti44-stencil-llm/14c2306d-603f-4fa8-b992-19e1aefb2f05/scratchpad/stale.py:53), [a_screen_run.py:580](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:580).

   **Fix:** apply only records marked `applied`; otherwise retain the preceding repository and classify that request as an output failure. Check the existing repository hashes. This bug did not affect the 61-record snapshot I checked: all were applied.

4. **CONFIRMED — matching optimizer steps is the right control for this claim.**

   The question is what adding the counterfactual term does at matched training exposure. Equal compute instead answers which recipe performs better for a fixed resource budget; that is also interpretable, but a different question.

   The trainer uses the same examples, seeded shuffle, accumulation, optimizer and CE term. Its new limit stops after completed updates. The DPO sign and reference subtraction are correct. [a_screen_train.py:325](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:325), [a_screen_train.py:351](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:351), [a_screen_train.py:378](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:378); the formulation matches the [DPO paper](https://arxiv.org/abs/2305.18290).

   **Medium — the runner currently rejects your matched SFT adapter.** It requires at least 7,200 elapsed training seconds. At 360 steps per four hours, 166 steps takes approximately 6,640 seconds. [a_screen_run.py:226](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:226).

   **Fix:** replace that minimum-duration check with validation of the achieved matched step count.

   **166 steps is not demonstrably too few.** With accumulation eight, that is 1,328 examples, or 1.153 epochs. It can change behavior; the count cannot guarantee it will. Also, 62.4 minutes of reference scoring plus exactly twice SFT’s training cost predicts roughly **133**, rather than 166, steps from your quoted throughput. Use the achieved count.

   I would run the proposed bounded screen. Print CE and the reference-relative preference margin separately using values already computed; the current log reports only their combined loss. Debug a training signal that fails to move. A completed null means “no demonstrated benefit from this recipe at this exposure,” not “counterfactual training cannot work.” [a_screen_train.py:393](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:393).

5. **CONFIRMED for the stated synthetic scope; REFUTED as a universal leakage guarantee.**

   I reproduced zero overlap in project names, request texts, file paths and file contents. All 576 TRAIN content hashes also match the freeze.

   Shared vocabulary, implementation idioms and lifecycle phrasing can support template-based generalization. They do not invalidate “works on synthetic sessions of this shape.” TRAIN deliberately shares one construction and explicit convention templates; state direction and precedent are counterbalanced. [a_train_pool.py:733](/home/bmarti44/stencil-llm/src/stencil/a_train_pool.py:733), [a_train_pool.py:934](/home/bmarti44/stencil-llm/src/stencil/a_train_pool.py:934).

   **This is fine within your stated scope.** A win would not establish general agentic coding ability or a specific internal “focus” mechanism.

6. **Yes: misleading differences remain possible through measurement and unequal samples. High if used to declare a winner.**

   The concrete paths are the outcome-dependent denominator, incorrect replay, and differing sensitivity to reply shapes described above. Compare **CF against SFT** for the incremental objective effect; CF against OFF also includes ordinary supervised training.

   Even a valid CF–SFT improvement can reflect better syntax, convention vocabulary or general implementation quality rather than better handling of supersession. The first reply also changes the second prompt and repository. That is a legitimate effect of the whole session policy, but it does not isolate state tracking from competence. [a_screen.py:187](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:187).

   **Fix:** use the same session IDs, retain all outcome categories, and inspect improvements by transition direction alongside the saved functional scores.

7. **Yes: J hides real effects, and the contract measure has its own blind spots. Medium.**

   J requires every suite at both checkpoints, so one unrelated competence failure erases any contract improvement. [a_screen_run.py:631](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:631).

   Conversely, naming checks can pass a correctly named but useless implementation. In the first 24 sessions, **11 of the 22 in-force replies failed the current functional suite**. Contract compliance is measurable there; successful coding is not established. [s01.py:155](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s01.py:155), [off.jsonl:1](/home/bmarti44/stencil-llm/results/a-screen/runs/off.jsonl:1).

   **Fix:** keep contract-state frequencies and functional success alongside each other. Avoid making either conditional on the other. J can remain a stringent secondary outcome.

8. **Medium — the live prefix is not representative enough for an overall futility decision.**

   The runner processes sorted slots: naming first, validation next, missing-record last. The first 24 sessions contain **no missing-record sessions**. An early aggregate can change substantially when that family arrives. [a_screen_pool/__init__.py:20](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/__init__.py:20), [s33.py:593](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s33.py:593).

   **Fix:** monitor comparable family/checkpoint groups and paired items. Do not infer that the overall trajectory cannot recover merely from the current ordered prefix. No further defect requiring another arm, registration or review stage was demonstrated.

**NOT INTERPRETABLE** — correct replay and labels; compare fixed-denominator changed-request outcomes with competence alongside; replace the two-hour SFT guard with matched-step validation.
