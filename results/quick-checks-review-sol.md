# Adversarial review — quick checks and proposed generalizing-selection simplification

Review date: 2026-09-02. Target commit: `d9c6b79`. I read the requested quick-check scripts, logs, and row artifacts; the H1′ session records and metadata; the active G0 registration and Amendment v2; the three prior G0 reviews; the last WORKLOG entry; and the relevant H1′, Multi-IF, and BFCL harness code. All recomputation was CPU-only. I launched no model or GPU process, signalled no process, and wrote no repository file other than this report.

## Bottom line

The simplification is directionally right: stop using a weak, indirect NLL proxy to choose the product and test the simple role-based product on task outcomes. But the quick checks do **not** establish that the role rule beats the finder independently of its 1.90x column budget, and they do not test the proposed product (role pin **plus echo**, with BM25 overflow and protected system/schema columns). Multi-IF and BFCL remain development families. The simplification is adoptable only after the rule, budget, controls, component arms, outcome floors, and no-contact boundary are frozen as specified at the end.

## Findings

### QCR-1 — HIGH — the reported AUROCs are right, but the semantic conclusion is not identified by this test

The saved rows exactly reproduce the logs:

| check | readout | recomputed AUROC |
|---|---:|---:|
| leave-one-out | mean utility | 0.494221 |
| leave-one-out | utility/span-token | 0.482047 |
| leave-one-out | max delta | 0.516 |
| leave-one-out | sum-positive | 0.509 |
| leave-one-out | top-3 | 0.512 |
| leave-one-out | flips / flips-from-correct | 0.496 / 0.496 |
| keep-one-in | mean utility | 0.518262 |
| keep-one-in | fraction of all-evicted gap | 0.517 |
| keep-one-in | top-3 | 0.630 |
| keep-one-in | flips-back | 0.601 |
| keep-one-in | utility/span-token (not reported) | **0.480351** |

The negative result for the **implemented readout** is credible: the session-paired mean keep-minus-control utility is positive in only 8/20 LOO sessions and 10/20 keep-one-in sessions; simple session-cluster bootstraps include zero in both cases. The stronger sentence in `results/quick-checks/README.md:13-14`—that the oracle measures content reproduction rather than standing-constraint adherence—is not established, for four reasons.

1. The treatment and control examples are not matched units. There are 63 finder spans averaging 14.79 columns and 103 fragmented control spans averaging 9.05 columns. Total mass happens to be 932 columns in each class, because `matched_control_spans` matches the **union** per session (`scripts/ledger_kv_probe.py:340-360`), but the oracle scripts replay each resulting contiguous fragment as a separate AUROC example (`results/quick-checks/oracle_check.py:45-53`; `oracle_check_keepin.py:48-56`). The keep-one-in mean AUROC of 0.518 reverses to 0.480 after the simplest span-length normalization. The top-3 value of 0.630 is therefore not clean evidence of a constraint signal.
2. The controls are not uniformly “task sentences.” Decoding them shows mixtures of task text, prior assistant output, the synthetic reminder, whitespace, and chat-template delimiters. For example, session 0 includes a 16-token assistant-prefix fragment and a 35-token reminder-plus-assistant fragment. `README.md:12-13` gives one possible content interpretation as if it were the construction rule; it is not.
3. The 96-token reference is truncated for 17/20 sessions: the corresponding full-arm generations have median length 219.5 and range 19–512 (`oracle_check.py:38`; `oracle_check_keepin.py:39`). This systematically misses late-acting length, ending, and postscript constraints.
4. The first token is never counterfactually rescored. `first_logits` is computed with the full cache, then reused for the first loss after the cache is evicted (`oracle_check.py:19-32,41-49`; `oracle_check_keepin.py:20-33,42-52`). Thus token 1 has delta exactly zero in every intervention. This is only 1/96 dilution, not an explanation for AUROC 0.49, but it confirms that the implementation is not the literal registered estimand.

BF16 zeros are not the main failure. None of the 166 saved mean utilities is exactly zero, although 13/63 treatment and 31/103 control LOO utilities have magnitude at most `1e-6` and many flip readouts are zero. The full-cache greedy path plus BF16 internal states does compress the dynamic range; it does not explain the control-unit and outcome-alignment defects.

The defensible conclusion is narrower:

> On these 20 B3 development sessions, this 96-token, direct-KV, reference-conditioned loss readout does not usefully rank finder spans above the fragmented matched-column background. It does not determine whether a span is needed for standing-constraint adherence.

A full-continuation reference and recomputation of the first counterfactual logit would repair the horizon and first-token defects, but not the target mismatch, cached mediation, control fragmentation, or non-additivity. An outcome-level oracle—greedy generation followed by the registered constraint checker under exact policy-set eviction—is the right instrument for adherence. The role quick check is already a small version of that instrument. Under the “do not over-engineer” burden test, another full-length span-NLL campaign is not worth running; retain these rows as a diagnostic and remove them from selection/promotion logic.

### QCR-2 — HIGH — the role arithmetic is exact, but higher budget remains a live explanation for the +4 over the finder

I recomputed the role table from `role_rule_rows.json` and the H1′ session records:

| arm | aged passes / 56 |
|---|---:|
| full | 44 |
| evicted | 14 |
| finder pinned | 37 |
| finder exact-column control | 18 |
| role pinned | 41 |
| role exact-column control | 26 |

Therefore `(41-14)/(44-14) = 27/30 = 0.90`, role-minus-own-control is `+15`, finder-minus-own-control is `+19`, and role-minus-finder is `+4`. The per-session statements in `results/quick-checks/README.md:20-21` are also exact: role versus finder is `+` in 4 sessions, `-` in 1, and tied in 15; role versus full is `+` in 3, `-` in 5, and tied in 12. The +4 finder margin is five gains offset by one loss, with a session-cluster bootstrap interval that includes zero (macro difference 0.0625, approximate percentile 95% interval `[-0.0167, 0.1542]`; a one-sided sign test over the five non-ties is `6/32 = 0.1875`). It is a development hint, not comparative evidence.

The budget arithmetic needs more precise wording. Role pins 1,772 columns versus the finder's 932 across 9,008 evictable columns: **1.90x** the finder mass. “20%” is the pooled `1772/9008 = 19.67%`; the mean of the 20 session fractions is 21.64%, with range 7.36%–35.13%, and 7/20 sessions exceed Amendment v2's 25% cap. The finder uses 10.35% pooled. Thus this quick role arm is not a fixed-25% policy evaluation.

The role control is fair for one narrow question. `role_rule_check.py:33-37` calls the same nearest-position exact-column matcher as H1′, so role versus 26 tests whether prior-user columns beat an equal mass of nearby non-user/markup/assistant columns. It does: +15 passes, positive in 13 sessions, negative in 1, tied in 6. But `+15` at 1,772 columns and `+19` at 932 columns are not comparable effect sizes; outcome response to retained mass is nonlinear. The higher-mass control itself scores 26 versus 18 for the finder control, an +8 indication that mass changes the baseline.

The exact cheap control that settles “does budget alone explain role's +4 over finder?” is:

> **finder-plus-filler at role mass:** on each of the same 20 contexts, start with the frozen H1′ finder columns; add target-blind columns from the evictable range outside all prior-user content, using the already frozen nearest-position tie rule, until the unique retained mass equals that session's role mass; then run the same `run_arm`, `max_new=512`, and aged checker. Store `finder_plus_filler - role` per-constraint and per-session. If filler is impossible, the session fails the diagnostic rather than being replaced or omitted.

This arm holds finder signal and total mass fixed while withholding the extra user-role content. The existing role control remains the complementary specificity arm. No claim that role “beats the finder” or that its gain is budget-independent is permitted without this result. The simplification does not need such a claim: it may choose role on simplicity and auditability, explicitly as a development decision.

### QCR-3 — HIGH — the H1′ intervention/scoring path is matched, but the proposed pin-plus-echo product has not been tested

`role_rule_check.py` does reproduce the important H1′ mechanics:

- it reads the identical saved `context_token_ids` and `evict_range` (`role_rule_check.py:17,21`), and refuses a decode/re-encode mismatch (`:22-25`);
- it selects only prior user turns (`:26-32`);
- it calls the identical `ledger_kv_probe.run_arm` with the saved range, `max_new=512`, and 300-second deadline (`:42-46`); and
- it constructs the same B3 checker row and slices the same saved `n_aged` prefix (`:38-48`; compare `scripts/ledger_kv_probe.py:647-672`).

The quick run used the same checkpoint and tokenizer. Its Qwen implementation hash differs from the original H1′ metadata (`results/qwen/ledger-kv-probe-h1p/meta.json:1`) because the trunk was generalized/fixed for 4B before this quick run; the 1.7B numerical branch remained the legacy path and WORKLOG records the 1.7B parity fixture as unchanged. This is a disclosed provenance delta, not evidence of a semantic mismatch.

However, the proposed policy is **not** this arm. The quick script runs only `pinned` and `pinned_control` (`role_rule_check.py:42-47`). It never echoes the role text, never invokes BM25 overflow, and has no system/schema prefix in this B3 harness. H1′'s finder-based `pinned_echo=48` does not establish role-based pin-plus-echo behavior; broader echoes can increase copying and truncation.

The named evaluation runners also do not yet implement the proposed product:

- Multi-IF's `text_ledger` arm re-appends salience-selected aged entries and performs no KV eviction/pinning (`scripts/ledger_eval.py:780-795`). As-is, it can test only the role **echo/surfacing component**, not role-based KV retention.
- BFCL constructs finder entries and a schema/finder-derived budget (`scripts/bfcl_mt.py:174-212,257-281`), then evicts from column 0 while keeping only arm-selected spans (`:314-340`). As acknowledged in the brief, this can discard the system/schema prefix in base and control. The protected-prefix fix must land, be CPU-tested, and be hash-bound before any arm is run.

Launching either current runner and labeling it “ROLE RULE” would test a different mechanism. The final registration below makes Multi-IF explicitly an echo-component leg and BFCL the pin-plus-echo pressure leg, with component and mass controls.

### QCR-4 — MEDIUM — the role result and full H1′ safety clause are not independently auditable from the quick artifact

`role_rule_check.py:46-49` computes a full generated object and per-constraint score vector, but writes only `aged_pass`, token count, truncation, a derived degeneracy Boolean, and pin count. It discards generated text/token IDs, the score vector, `rep4`, timeout, and invalid-output fields. Consequently:

- `truncated=1` and `degenerate=1` for role are arithmetically reproducible from the saved Booleans and satisfy the H1′ comparisons against full's 1 and 2;
- the claimed 41/56 cannot be independently re-run through the checker from the saved role output; and
- H1′ also requires zero timeouts and invalid-output no worse than full (`LEDGER-PLAN.md:397-398`), but those fields are absent, so the phrase “safety ... within the integer clause” in `README.md:20` is not fully verified.

This does not invalidate a disclosed quick development probe, but it prevents treating it as confirmatory evidence. Every subsequent one-shot arm must store the complete generated token IDs/text, checker vector, pin/control columns, timeout, truncation, `rep4`, invalid-output, echo-copy, model/tokenizer/code hashes, and per-case policy inputs in the same run.

### QCR-5 — HIGH — cutting G0 changes the lineage claim; Multi-IF and BFCL are development sets, and B3 is now a selector-development set too

Amendment v2 already correctly records that Multi-IF, BFCL, IFEval/IFBench, and S2/B3 influenced the policy family and harness (`LEDGER-PLAN.md:482-491`). The quick role decision adds direct outcome contact: `role_rule_check.py:16,38-48` reads `data/b3/mt-train-300.jsonl` labels/checker kwargs and uses its 20 outcomes to prefer the role rule. Therefore:

- B3/H1′ is a **selector-development probe**;
- Multi-IF 909 is a **post-development evaluation of the echo component**;
- BFCL dev and sealed cohorts are **post-development evaluations of the product**—sealing row identities does not make the already inspected family zero-shot; and
- cutting OASST2/ToolACE G0 removes the only planned disjoint-corpus selection/confirmation stage. It is no longer permissible to say the selector was “chosen on OASST2/ToolACE,” “chosen elsewhere,” or selected by 0.80 oracle recovery.

I found no new direct benchmark-row leakage in the quick scripts: the oracle scripts read only H1′ B3 artifacts, and the role script reads only B3. There is a new enforcement blind spot worth recording: the selection scripts live under `results/quick-checks/`, while `tests/test_eval_data_separation.py:107-110` scans only non-recursive `src/stencil/*.py` and `scripts/*.py`. That scanner would not stop a future quick-check script from reading `data/bench/`. This is defense-in-depth, not an information-flow proof; the present scripts themselves do not cross the declared path boundary.

The separately registered no-contact family is therefore the **first** eligible zero-shot evaluation. Before contact, it must satisfy all of the following: no prior project or agent inspection of any family data, metadata-derived task design, examples, labels, checker, template, schemas, baseline/model responses, or sibling benchmark from the same generator; no policy, renderer, budget, arm, endpoint, threshold, or tie-break may change after the family is named; exact/near-duplicate and shared-generator/taxonomy checks against B3, Multi-IF, BFCL, IFEval/IFBench, S2, and all selection corpora are recorded; the cohort and official scoring path are frozen before outputs are read; and failure is reported without replacing the family or tuning and retrying. One untouched family supports only a “zero-shot result on [name]” claim, not universal generalization.

### QCR-6 — LOW — the role rule itself is plain engineering, not Miller-inspired selection

Static protection by message role is an invariant/whitelist: it does not use current need, select an item at read time, clear an active set, or implement oscillation, burst, phase, synchrony, or neural routing. The role rule itself should be called **plain protocol engineering**. Only the overflow path—lossless archive, current-query BM25 retrieval, and transient verbatim echo—has a defensible high-level analogy to demand-time item reactivation. The complete system may be described as “Miller-inspired engineering” solely in that functional/analogical sense; neither a positive result nor the role rule is evidence for Miller's neuroscience theory. This is consistent with the project's own synthesis (`results/research-generalizing-synthesis.md:23-28`) and prior sol review (`results/g0-registration-review-sol.md:354-366,544-551`).

## Burden test: what is lost by cutting the G0 oracle pilot?

The cut loses four things:

1. a disjoint OASST2/tool-corpus stage for selecting among role, recent+sinks, and BM25;
2. a quantitative map of model-specific direct-column support and a possible training target for G1;
3. the pre-registered 0.80 recovery reason for not building G1; and
4. evidence about whether the same ranking proxy works in generic chat and tool trajectories.

It does **not** lose direct evidence that the shipped mechanism improves instruction adherence or tool success—the NLL pilot could never supply that. It also does not justify declaring G1 unnecessary on scientific grounds; G1 is simply removed from the current product scope. Given the flawed control units, weak signal, substantial GPU cost, and the availability of direct checker outcomes, those losses are acceptable. Preserve the oracle work as a negative diagnostic, state that policy choice is engineering-led and development-informed, and spend the finite evaluation budget on exact product/control arms and the no-contact family.

## VERDICT: ADOPT-WITH-FIXES

Adopt the simplification, but do not launch Multi-IF, BFCL, or name a zero-shot claim until the following text is registered verbatim (paths/hashes represented by brackets must be filled, not left open):

> ### GENERALIZING SELECTION — ROLE-RETRIEVE-ECHO v1 (registered before any new arm outcome)
>
> **Supersession and scope.** G0 Amendment v2's OASST2/ToolACE loss-oracle selection and conditional G1 branches are cancelled before producing governing pilot results. The committed quick-check loss rows are a B3 development diagnostic only: they show no useful ranking signal for the implemented 96-token reference-conditioned direct-column readout and do not establish “content need,” adherence need, or oracle recovery. No selector is claimed to have been chosen on OASST2/ToolACE, and no G1 conclusion is drawn. The candidate below is chosen as a simple, parameter-free engineering rule after inspection of B3/H1′, Multi-IF, BFCL, IFEval/IFBench, and S2 behavior.
>
> **Frozen rule.** At each assistant generation step, build all token coordinates from one encoding of the exact unaugmented rendered prompt using tokenizer hash `[TOKENIZER_SHA]`. Let `P` be the union of (i) columns 0–3; (ii) the complete rendered system turn, including every currently available tool schema and its chat-template delimiters; (iii) the complete current user turn and delimiters; and (iv) the 256 columns immediately preceding the current user turn. `P` is retained in every non-full arm, is outside every selector/control pool, and is free of charge against `B`. Let `E` be all columns before the current user turn that are not in `P`. Let `B=floor(0.25*|E|)` unique columns.
>
> Candidate items are complete prior-user-message content spans; their charged mass is the unique columns in `E` that they cover. If their union costs at most `B`, select all of them. Otherwise rank complete prior user messages by BM25 against the current user message only, using Unicode NFKC, lowercase `\w+` word tokens, `k1=1.5`, `b=0.75`, `idf(t)=log(1+(N-df(t)+0.5)/(df(t)+0.5))`, no query-term-frequency suppression, descending score, then earlier source-turn index. Greedily select a whole message iff all of its not-yet-selected charged columns fit; otherwise skip it; never partially select a message. `B=0` selects nothing. Reorder selected messages chronologically and append their exact raw text once with `stencil.ledger.text_ledger_context`; no summary, rewrite, label, answer literal, assistant text, or tool output is added. Record raw and echoed token spans and exact echo-token overhead. The lossless raw history remains archived; BM25 is used only in the overflow case.
>
> **Capacity.** BFCL pressure arms use `K=8192` total post-prefill cache columns. After adding the echo, every pressure arm retains `P`, the complete echo/current suffix, and its registered pin/control set, then evicts the oldest remaining columns until exactly `min(K,prompt_length)` columns remain. If mandatory protected-plus-echo columns alone exceed `K`, or if the requested pin/control mass cannot fit, the case is a preflight failure and the gate fails; no protected column may be evicted, no budget may be enlarged, and no case may be replaced. Multi-IF's text-runner leg performs no KV eviction and is explicitly an echo-component evaluation, not retention evidence.
>
> **Exact controls.** For each treatment generation, construct a MASS CONTROL with the same number of unique charged KV columns and the exact same number of added prompt tokens as the role treatment. Control source columns come from `E` outside every prior-user content span, use the same age bucket and nearest-position rule with higher-column tie-break at equal distance, exclude chat-control tokens, and are rendered chronologically. An unavailable exact match fails that case before generation; it is never substituted or excluded after outcomes. Before any claim that role beats the H1′ finder, run the separate B3 development diagnostic FINDER-PLUS-FILLER: retain the frozen H1′ finder columns and add target-blind non-user columns by that same rule to exactly the role mass in each session. Store complete outputs and per-constraint score vectors. This diagnostic does not select or tune the frozen role rule.
>
> **Multi-IF post-development leg.** Cohort is the already frozen 909 conversations / 1,805 late turns. Arms are `base` (the frozen recorded native response), `role_echo` (the frozen rule's selected text appended, no KV intervention), and `mass_echo_control` (exact added-token control, no KV intervention). Primary cells are all aged FIXABLE constraint outcomes, with truncated outputs scored as-is. `role_echo` passes only if both one-sided 97.5% conversation-clustered lower bounds, `role_echo-base` and `role_echo-mass_echo_control`, are strictly greater than zero; selected-source coverage of aged eligible constraints is at least 0.90; timeout rate is at most 0.02 in every generated arm; truncation excess versus both base and control is at most 0.02; the one-sided 97.5% clustered upper bound on stale-constraint adoption excess versus base is below 2.0 percentage points; and the role arm's degenerate-turn count (`truncated OR repeated-4gram fraction >0.5`) and invalid-output count are each no greater than the corresponding count in either base or control. All 909 conversations are required. This leg is reported as post-development echo/surfacing behavior and cannot support a KV-retention or zero-shot claim.
>
> **BFCL V3 post-development leg.** The existing 32-case dev and 64-case sealed cohorts, official cumulative checker, non-thinking renderer, `max_new=512`, and 300-second per-turn deadline remain fixed. Model choice follows the already registered deterministic preflight: run 1.7B on dev; use it iff full-arm final-pass is at least 0.15, otherwise use 4B iff it reaches 0.15; if neither does, do not open the sealed run. The finder-recall floor is deleted because the frozen rule has no finder. Before any model run, CPU tests must prove on every constructible prompt that system/schema columns are in `P`, survive every pressure arm, are outside pin/control budgets, and that treatment/control unique-column and echo-token counts match.
>
> BFCL arms are: `full` (no eviction, no echo; descriptive ceiling), `pressure_base` (`P` protected, `K=8192`, no old-user pin and no echo), `role_echo_only` (`P` protected, role text echoed, original selected old-user columns not pinned), `role_pin_echo` (the shipped product), and `mass_pin_echo_control` (the exact mass/echo control). Histories are model-rolled within arm and cases are paired by source episode. Primary endpoint is official final episode pass on all 64 sealed cases. Product success requires the one-sided 97.5% episode-clustered lower bounds for `role_pin_echo-pressure_base` and `role_pin_echo-mass_pin_echo_control` both to be strictly greater than zero. Call the result `RETENTION+REINJECTION` only if the corresponding lower bound for `role_pin_echo-role_echo_only` is also strictly greater than zero; if the two product bounds pass but that incremental-retention bound does not, call it `REINJECTION-ONLY`; every other outcome is `FAIL/DO NOT CLAIM BENEFIT`. `full` is a ceiling readout, not assumed to dominate and not a promotion denominator.
>
> BFCL safety binds every scored case and no safety event is excluded: timeout rate at most 0.02 in every non-full arm; truncation excess of `role_pin_echo` versus both `pressure_base` and control at most 0.02; degenerate-session count (`truncated OR repeated-4gram fraction >0.5`) no greater than both comparators; parsed tool-call validity of `role_pin_echo` no more than 0.02 below either comparator; invalid-output count no greater than either comparator; and echo-copy rate (at least eight consecutive echoed tokens) no more than 0.02 above the mass control. Truncated, invalid, degenerate, and echo-copy cases remain in the primary denominator. Report all outcomes by the four registered BFCL categories; no category can be omitted or pooled away.
>
> **Records and identity.** Every generation record written in the same run contains source ID, exact rendered-context hash and token IDs, `P/E/B/K`, selected/ranked items and BM25 scores, treatment/control/echo spans, generated token IDs and text, complete checker vector/result, timeout, truncation, repeated-4gram fraction, invalid-output, echo-copy, and the hashes of model, tokenizer, renderer, policy code, scorer/checker tree, cohort, seed, and thresholds. Resume refuses any identity mismatch. Missing arms, incomplete controls, protected-prefix violations, or missing record fields fail closed.
>
> **Lineage and claims.** B3/H1′ is selector development. Multi-IF and BFCL are post-development evaluations because their data, responses, labels/checkers/templates, and observed behavior influenced the policy family and harness. They are never described as unseen, untouched, confirmatory, or zero-shot. Passing both supports only: “On the named Qwen checkpoint and frozen harnesses, a parameter-free role/retrieval/echo rule chosen during B3/Multi-IF/BFCL development improved the registered outcomes on the two development families.” It does not show optimality over the finder, transfer to other families/models/budgets, or support for Miller's neuroscience theory. The role invariant is plain protocol engineering; BM25-at-read-time plus transient echo may be called Miller-inspired engineering only as a functional analogy.
>
> **No-contact family.** Zero-shot wording is forbidden until a later committed registration, made after the policy, renderer, controls, budget, code, model, and all thresholds above are frozen, names one benchmark family and revision before any project member or agent opens its data, examples, metadata-derived task structure, labels, checker, template, schemas, baseline responses, or sibling family from the same generator. That registration fixes a blind acquisition/cohort procedure, official endpoint, sample size, exact arms, failure handling, and one-sided 97.5% paired/clustered lower-bound floors against both pressure base and exact mass control. A manifest must show no exact/near duplicate and no shared generator/template/taxonomy with B3, Multi-IF, BFCL, IFEval/IFBench, S2, or selection corpora. After opening, benchmark contact may implement only the frozen harness adapter; it may not alter the policy or registration. Failure is terminal for that family's claim and cannot trigger family replacement or tuning. A pass licenses only “zero-shot on `[FAMILY]` under `[MODEL/K/BUDGET]`,” not universal generalization.
