# Adversarial review — GENERALIZING SELECTION / G0 PILOT registration

Review date: 2026-09-02. Registered target: `LEDGER-PLAN.md` at commit
`1fa355d`, lines 441–477. Guard target: commit `e19f67f`. I also inspected the
current coder brief, the four research artifacts named in the brief, the
2026-09-02 worklog from `eval-data-guard` onward, the relevant cache and
template paths, and the in-flight CPU helper/tests without treating unfinished
coder work as accepted implementation.

No GPU/model process was launched, no process was signalled, and no tracked
repository file other than this report was written.

## Bottom line

The registration is not presently a clean generalization experiment. The
third leakage instance is real and has three layers:

1. The policy family itself was designed after inspecting Multi-IF and BFCL,
   and the shipped `salience2` policy was structurally hand-tuned and
   backend-selected on Multi-IF/IFBench outcomes. Refitting only its numeric
   weights does not undo that development-set use.
2. `salience2` is fit on B3, whose constraint taxonomy and validity machinery
   are explicitly IFEval-derived; S2 is a B3 held-out-template set, not an
   independent evaluation family.
3. The claimed mechanical firewall does not cover either route and is
   bypassable by ordinary script naming, imported loaders, top-level code, and
   a shell pipeline.

Independently, the registered decision statistic sums single-span effects even
though the registration acknowledges non-additivity. A top-three diagnostic
cannot validate the policy sets actually being selected. Thus even perfectly
disjoint data would not make the current winner rule sound.

## Findings, ordered by severity

### G0R-1 — CRITICAL — Multi-IF/BFCL influenced the policy class and the shipped candidate

The registration says that nothing, “including the choice among zero-parameter
policies,” is chosen on Multi-IF or BFCL, and calls the later application to
those families zero-shot (`LEDGER-PLAN.md:452-460`). The same registration says
the program was triggered by measured `salience2` behavior on Multi-IF and BFCL
(`LEDGER-PLAN.md:443-445`). The synthesis uses the discovered BFCL column-0
schema failure to prescribe role protection (`results/research-generalizing-synthesis.md:23-24`)
and selects the policy menu after comparing recommendations that were based on
those benchmark results (`results/research-generalizing-synthesis.md:30-36`).

More directly, the `salience2` segmenter was revised from actual Multi-IF error
lists (`tests/test_salience2.py:50-59`), its committed module reports Multi-IF
and IFBench gates and says the linguistic backend was chosen by those gates
(`src/stencil/salience2.py:41-56`), and its hand floors are code rather than
fitted parameters (`src/stencil/salience2.py:473-498`). The brief nevertheless
places it among “zero-training policies” eligible to win
(`tools/codex-agents/g0-oracle-pilot.md:38-48`). `salience2` is trained, and its
architecture, features, floors, segmenter, and backend were evaluation-informed.

This does not make `salience2` useless. It makes Multi-IF, IFBench/S2, and BFCL
development or post-development test sets for this policy family, not untouched
confirmation sets. A new weight file fit on B3 cannot erase information already
embedded in code and policy choice.

### G0R-2 — CRITICAL — IFEval and S2 enter through B3; directory separation is not corpus separation

The declared fit lineage includes B3 prompts, buried variants, and B3 prose
(`src/stencil/salience2.py:35-39,1105-1114`; `WORKLOG.md:2414-2416`). B3 states
that each constraint maps to a vendored IFEval instruction ID and is checked by
the deployment checkers (`src/stencil/b3_gen.py:2-10`). Its v4.3 registry is a
list of IFEval instruction classes (`src/stencil/b3_gen43.py:88-103`), and its
canonical/mutation verifier instantiates `ifeval.instructions_registry`
(`src/stencil/b3_gen43.py:554-582`). This is benchmark-taxonomy and verifier
transfer even though the 541 row texts were phrase/kwargs-deduplicated.

S2 is registered as “data/b3 held-out templates” (`LEDGER-PLAN.md:319-328`).
The `salience2` fit synthesizes buried B3 examples with template parity 0
(`src/stencil/salience2.py:972-1011,1105-1114`), while its held-out buried test
uses the same generator and parity 1 (`tests/test_salience2.py:699-704`). That
is a within-generator template split, not a new corpus family. It directly
contradicts the later statement that S2 is an evaluation set under
`data/bench/` and is disjoint “by construction” (`LEDGER-PLAN.md:441-442`).

Accordingly, S2 cannot support an independent generalization claim for a
policy containing `salience2`; IFEval cannot be described as having had no
influence. Exact-row separation is true but materially narrower.

### G0R-3 — HIGH — the guard is demonstrably bypassable and cannot support “mechanically enforced”

The AST test recognizes only two forbidden literal roots
(`tests/test_eval_data_separation.py:13-20`), scans only immediate `*.py` files
under two directories (`tests/test_eval_data_separation.py:107-111`), follows
only calls to functions defined in the same file
(`tests/test_eval_data_separation.py:33-42,67-104`), and deliberately exempts
three complete scripts (`tests/test_eval_data_separation.py:8-12,67-70`). It
does not track imported loaders, aliases/constants, `os.path.join`/`joinpath`,
module-level flow in an innocuously named script, nested packages, tools, shell
scripts, `vendor/ifeval`, or the actual `data/b3` S2 family. Prefixing a loader
with `eval_` explicitly exempts its name from fit classification
(`tests/test_eval_data_separation.py:23-30`); this is a naming convention, not
information-flow enforcement.

The shell hook is expressly textual and disclaims indirection
(`tools/hooks/pretool_guard.py:2-9`). Its fit regex omits `oracle`, `select`,
`rank`, and `build` (`tools/hooks/pretool_guard.py:24-30`), while allowed reader
or runner tokens exempt a whole segment (`tools/hooks/pretool_guard.py:32-37,61-80`).
A CPU replay of `decision()` returned `None` for each of:

```text
python3 scripts/g0_oracle.py --input data/bench/multiif_en.jsonl
python3 scripts/build_ranker.py data/bench/bfcl_v3_mt
git show HEAD:data/bench/multiif_en.jsonl | python3 scripts/fit_finder.py -
```

The last bypass occurs because a single `|` is not a segment delimiter and a
leading `git` token is allowed (`tools/hooks/pretool_guard.py:53-69`). A clean
wrapper can also call an imported evaluation loader because the AST graph is
file-local. This is not a malicious same-UID objection; these are ordinary
fallible-agent forms. The guard is useful defense in depth, but the registration
must not cite it as proof of complete separation.

### G0R-4 — CRITICAL — additive recovery cannot select a policy under joint eviction

The research correctly says single-span utilities are non-additive
(`results/research-generalizing-synthesis.md:39-44`) and recommends evaluating
selected sets under joint eviction (`results/research-generalizing-sol.md:25-30`).
The registration instead performs one joint check only for the top three
single-span utilities (`LEDGER-PLAN.md:463-465`), and the brief selects policies
by the sum of positive single-span utilities they retain
(`tools/codex-agents/g0-oracle-pilot.md:32-48`).

This can reverse a winner. If two spans are redundant copies, evicting either
alone can have utility zero while evicting both has a large loss. Neither is in
the single-span top three, their summed mass is zero, yet retaining either may
recover the entire joint loss. Synergy gives the opposite failure. The
top-three delta is a diagnostic for one set and says nothing about the five
policy-specific complements.

Every policy must therefore be scored by jointly evicting the exact columns it
would discard at budget B. Single-span utilities may remain explanatory
readouts, but cannot govern policy promotion or the G1 branch.

### G0R-5 — HIGH — the registered signal rule is approximately a coin flip under its own null

Signal is declared when the fraction of candidates above the null p90 merely
“exceeds 0.10” (`LEDGER-PLAN.md:466-469`). At the maximum 30 x 12 = 360
candidates per corpus, that means at least 37 exceedances. Even granting a
fixed, known p90 and independent spans, under the null

```text
P[Binomial(360, 0.10) >= 37] = 0.4557686379.
```

Requiring this in two independent corpora still false-passes with probability
about 0.2077. Estimated quantiles, within-dialogue dependence, ties, and reuse
of the same null pool make the nominal interpretation less—not more—secure.
This is not a registered statistical test of signal.

The “nulls” are also random content deletions, not numerical no-ops. They can
remove genuinely useful text and can overlap candidates or one another unless
explicitly forbidden. They are a matched random-span background distribution,
not a noise floor. A true numerical noise control is a no-op eviction/cache
restore; semantic background and implementation noise must be reported
separately.

### G0R-6 — HIGH — the eligible pool and B are not deployment-matched or executable unambiguously

The brief constructs candidates from system/schema, user, assistant, and tool
messages without excluding the current query or recent window
(`tools/codex-agents/g0-oracle-pilot.md:27-30`). It then runs BM25 over “ALL
candidate spans” with the current user turn as query
(`tools/codex-agents/g0-oracle-pilot.md:41-42`). As written, BM25 can retrieve
the query from itself. The same problem lets current-query attention and
recency dominate an experiment intended to study delayed need.

System/schema spans are simultaneously oracle candidates, free protection in
the role rule, and declared never-evictable for every BFCL arm
(`LEDGER-PLAN.md:461-465,474-476`; `tools/codex-agents/g0-oracle-pilot.md:38-46`).
Measuring or charging oracle mass for columns that deployment exempts makes
policy recoveries incomparable. The protected prefix and fixed recent window
must be outside both the candidate pool and B.

Finally, “B = total tokens of the top-25% candidates” does not define what
“top” means, whether 25% is by count or unique token mass, how to round, whether
B is per dialogue or global, whether the four sinks count, or how partial and
oversized spans are handled (`tools/codex-agents/g0-oracle-pilot.md:38-48`).
Outputs store only whole kept-span indices, while recent+sinks is token-based.
Different reasonable implementations yield different winners.

### G0R-7 — HIGH — the oracle is useful, but not “label-free need” or fully deployment-matched

The APIGen reference is the gold tool call (`LEDGER-PLAN.md:456-459`;
`tools/codex-agents/g0-oracle-pilot.md:21-25`). Gold continuation tokens are
labels. The accurate name is “reference-conditioned counterfactual utility”:
self-labeled on OASST2 and gold-conditioned on APIGen.

For OASST2, every stored greedy reference token was the full-cache argmax at
the moment it was generated (`tools/codex-agents/g0-oracle-pilot.md:18-20`).
Teacher-forced NLL delta then measures margin/support for that model-chosen
path. After an evicted run would first diverge, later teacher-forced tokens
remain on the full-cache path. This is a valid local sensitivity measure, not
trajectory success or semantic necessity. APIGen uses gold prior trajectories,
and OASST2 uses corpus prior assistant turns, whereas the gate harness rolls
model responses; the cache intervention can be matched while the history
distribution is not.

There is another important conditioning: the whole context is prefilled before
the old span is removed, so later tokens' K/V states can already carry mediated
information from it. The estimand is the marginal value of direct access to
that span's columns at the decision time, conditional on all surviving cached
states. That is appropriate for read-time eviction at that exact point, but it
cannot label write-time retention need or total information provenance without
an earlier-eviction/leave-group-out diagnostic.

The cache-position concern itself is resolved. The cited class name is wrong:
`QwenFocusCache` has no `evict`; the method is `KVCache.evict`. It deletes
physical post-RoPE K/V columns but intentionally does not reduce logical
`cache.length` (`src/stencil/qwen3.py:60-85`). New Q/K positions use that
unchanged logical offset (`src/stencil/qwen3.py:300-317,342-343`). Therefore
surviving keys and continuation tokens retain original absolute RoPE positions;
there is no re-indexing shift.

### G0R-8 — HIGH — recovery branches and uncertainty permit incompatible readings

“Null-adjusted recovery” has no registered formula. Plausible choices include
subtracting each paired null before clipping, subtracting aggregate null mass,
or normalizing relative to a random policy; they differ with negative utilities
and zero denominators. “The best is in [0.50, 0.80)” is not a scalar rule across
two corpora. A policy at (0.90 chat, 0.20 tool) can be called best by its mean,
worst-corpus value, or per-corpus ranks. Multiple policies can clear 0.80, and
no tie-break is registered (`LEDGER-PLAN.md:469-473`).

Thirty dialogue clusters per corpus are then used both to compare five policies
and to make an irreversible “G1 not built” choice, with no confidence bound or
separate selection/confirmation split. The 0.80/0.50 constants are defensible
as explicitly heuristic advancement thresholds, but not as evidence-strength
thresholds without a dialogue-clustered uncertainty rule.

The ToolACE fallback trigger, top-three tie handling, p90 scope (per corpus,
role, dialogue, or matching stratum), missing-null behavior, truncated/empty
self-reference behavior, and macro versus token-weighted aggregation are also
unregistered (`tools/codex-agents/g0-oracle-pilot.md:18-25,27-36,50-54`).

### G0R-9 — MEDIUM — attention, BM25, and rendering have post-registration degrees of freedom

The brief says only to document after implementation which attention
layers/heads are averaged (`tools/codex-agents/g0-oracle-pilot.md:45-46`). The
existing trunk probe records the last query row, averaged over heads, only at
layers 20 onward (`src/stencil/qwen3.py:253-267`); it does not implement a mean
over all current-turn query tokens. The choice between those definitions can
change the control ranking and must be frozen before results.

BM25 tokenization, k1, b, query-term frequency, tie-breaks, candidate exclusion,
and budget packing are unspecified. Tool rendering is copied from the
BFCL-developed template path (`tools/codex-agents/g0-oracle-pilot.md:21-25`),
whose exact non-thinking prefix is hand-rendered in `scripts/bfcl_mt.py:106-143`.
That is a reasonable model protocol, but its bytes and provenance must be
frozen and disclosed; “read the BFCL template only” is still a BFCL-derived
design choice. The output metadata lists a model hash but not tokenizer,
template/renderer, policy implementation, or reference-generation hashes
(`tools/codex-agents/g0-oracle-pilot.md:50-54`).

### G0R-10 — MEDIUM — 30+30 is a useful engineering pilot, not the smallest decisive experiment

With 12 candidates plus 12 backgrounds, the nominal cost is about 26
reference-continuation passes per dialogue (full, 24 single evictions, and one
joint check), or roughly 1,560 passes before policy-joint fixes. Two first-N
dialogues per corpus are not a safe timing projection for contexts ranging up
to 16k. Token counts for the entire drawn subset are available on CPU, so the
timing smoke should be length-stratified before extrapolation.

For mechanics, 8+8 dialogues with at most eight eligible spans is enough to
exercise cache cloning, no-op equality, RoPE preservation, duplicate groups,
both renderers, and every policy. For choosing a policy, 30+30 may still be too
small; no sample size is “decisive” until the estimand's clustered variance or
a precision target is registered. A fast two-stage design is preferable:

- G0a: 8+8, at most eight spans, engineering/timing only; no policy promotion.
- G0b: retain 30+30 (or a variance-derived N) only after G0a passes, score exact
  policy sets jointly, and use a dialogue-clustered lower confidence bound.

Cut the BFCL-named argmax parse/match readout from gating—it is incoherent on
the teacher-forced path after a divergence and no BFCL rows are allowed in the
pilot. Keep it only as an APIGen renderer diagnostic. Add one synthetic unique-
fact positive control and one no-op eviction control as harness tests, not as
fit examples. Add leave-group-out for verbatim duplicates, as already warned
in `results/research-generalizing-fable.md:136-152`.

## Direct answers to the five questions

1. **Leakage/lineage:** No. Exact rows under `data/bench/` no longer enter the
   current numeric `salience2` refit, but policy design/backend selection used
   Multi-IF/IFBench/BFCL, B3 imports IFEval taxonomy/checkers, and S2 shares the
   B3 generator. The guard is bypassable by common script and loader forms and
   cannot enforce manual policy choice. OASST2/APIGen also require a normalized
   exact/near-duplicate audit against evaluation messages/schemas; directory
   names and subset hashes alone do not prove content disjointness.
2. **Oracle validity:** It is a sound local, reference-conditioned measure of
   marginal direct-KV support at read time. It is not a label-free tool-corpus
   measure, not total semantic need, not write-time need, and not trajectory
   success. Non-additivity makes the current recovery rule invalid. Random
   content spans are a background, not a noise floor. Qwen's actual
   `KVCache.evict` preserves original RoPE positions and logical continuation
   positions; no positional re-indexing bug was found.
3. **Decision rules:** The constants are pre-stated but not operationally tight
   or statistically defensible. The 0.10 rule has no alpha control; recovery,
   B, cross-corpus best, ties, and fallback behavior are ambiguous. The 0.80 and
   0.50 thresholds can be retained as heuristic branch thresholds only after
   joint recovery and clustered uncertainty are defined.
4. **Minimality/speed:** Keep 30+30 only as G0b selection after an 8+8
   engineering smoke. Reduce G0a to eight eligible spans, use CPU length
   stratification, and replace the uninformative 12+12 additive matrix with
   exact per-policy joint replays. Add no-op, unique-fact, and duplicate-group
   checks; remove BFCL-named parsing from gating.
5. **Generality claim:** With the present history, the strongest honest claim
   is: “On Qwen3 under this fixed template, budget, and cache intervention, a
   policy frozen after OASST2/APIGen selection was evaluated without further
   parameter changes on Multi-IF and BFCL.” It may report the observed deltas
   and uncertainty. If the same protocol were instead frozen before any contact
   with two genuinely untouched families, it could claim observed cross-corpus
   transfer to those two families on the named model/harness/budget—not universal
   generality. In the present history it may not call Multi-IF/BFCL unseen, claim a general
   selector, claim transfer beyond the two benchmark families/model/budget, use
   S2 as independent corroboration for `salience2`, or claim support for Miller's
   theory. A clean “zero-shot generalization” claim now requires at least one
   separately named benchmark family that was not previously inspected or used
   in code/policy design.

The model card must state: all prior Multi-IF/BFCL/IFEval/IFBench/S2 contact;
fit/select corpora with revisions, hashes, licenses and dedup results; which
references are self-generated versus gold; exact policy/renderer/tokenizer/model
hashes; protected-prefix/recent-window rules and whether their cost is outside
B; per-corpus joint results with dialogue-clustered intervals and no pooled
masking; negative/zero denominator behavior; the offline gold/human-history
limitation; and that the NLL oracle measures model-specific direct-column
sensitivity rather than human value or end-task necessity.

## VERDICT: UNSOUND

The following exact text changes are required before any G0 result may govern a
policy or a generality claim. They are ordered by severity.

1. **Replace `LEDGER-PLAN.md:442` and the corpus-separation claim at lines
   453–460 with:**

   > DEVELOPMENT LINEAGE: Multi-IF, BFCL V3, IFEval/IFBench, and S2/B3 were
   > inspected before this registration and influenced the candidate policy
   > family, role protections, `salience2` segmenter/floors/backend, and
   > evaluation harness. They are not untouched confirmation sets. G0 outcome
   > selection is restricted to the frozen OASST2 and APIGen-MT subsets named
   > in `data/g0/MANIFEST.json`; no result from Multi-IF, BFCL, IFEval/IFBench,
   > S2, or a model response to those sets may alter parameters, thresholds,
   > policy eligibility, budget, renderer, or tie-breaks after this amendment.
   > Later Multi-IF/BFCL results are post-development evaluations. A zero-shot
   > generalization claim requires a separately registered benchmark family
   > with no prior data, response, label, checker, template, or policy-design
   > contact. S2 is a within-B3 template holdout and is not independent evidence
   > for a B3-trained policy.

2. **Replace policy item (d) in `LEDGER-PLAN.md:463-465` and the brief at
   `tools/codex-agents/g0-oracle-pilot.md:43-44` with:**

   > (d) `salience2` linguistic finder, whose numeric weights are fit on B3 and
   > whose segmenter, floors, features, and backend were developed using
   > Multi-IF/IFBench results. Report it as an evaluation-informed diagnostic;
   > it is trained and is INELIGIBLE to become the zero-training winner or to
   > set either the G0 or G1 branch.

   Also change every occurrence of “zero-parameter policies” to
   “frozen candidate policies” and reserve “zero-training” for policies with no
   fitted artifact and no benchmark-informed tuning.

3. **Replace the additive recovery definition and top-three governing rule at
   `LEDGER-PLAN.md:463-473` / brief lines 32–48 with:**

   > For every eligible policy p, construct its exact whole-span keep set Kp at
   > B and jointly evict E\\Kp, where E is the eligible span set. Also jointly
   > evict E and perform a no-eviction run. Let L0 be full-cache mean reference
   > NLL, LE the NLL after jointly evicting E, and Lp the NLL after jointly
   > evicting E\\Kp. Fix epsilon=1e-6 NLL. If LE-L0 <= epsilon, set that
   > dialogue's promotion recovery to zero and separately report all three
   > signed NLLs; otherwise R_p=(LE-Lp)/(LE-L0), retained signed and not clipped.
   > Aggregate R_p as an equal-weight mean over every drawn dialogue. Single-span
   > utilities and the top-three sum-versus-joint delta are diagnostics only and
   > never select a policy. A policy must also beat a deterministic matched-
   > random whole-span policy with a paired dialogue-clustered 95% lower bound
   > above zero.

4. **Replace the signal sentence at `LEDGER-PLAN.md:466-469` with:**

   > Random role/length/age-matched content spans are a semantic background, not
   > a numerical noise floor. Numerical validity requires a no-op eviction whose
   > tokenwise logits/NLL equal a restored full-cache run at the registered
   > tolerance. For each corpus and dialogue i, estimate the background p90 from
   > null spans in all other dialogues, compute z_i as the within-dialogue
   > fraction of candidate utilities strictly above that p90 minus 0.10, and
   > declare signal only if the fifth percentile of 10,000 dialogue-resampled
   > means of z_i (PRNG seed 20260903) is greater than zero in BOTH corpora. Use
   > the linear sample-quantile convention; exact ties do not exceed the p90.
   > A missing matching stratum fails the dialogue before any utility is read.

5. **Insert before candidate construction in both registration and brief:**

   > The eligible set E contains only prior-turn spans that deployment may
   > actually evict. Exclude the system/tool-schema prefix, the first four sink
   > columns, the complete current user turn/query, and the fixed recent window;
   > those columns remain present in every oracle and policy run and are outside
   > B. BM25 indexes E only and never indexes its current-turn query. Null spans
   > are distinct, non-overlapping with their candidate and with other nulls,
   > and drawn only from E; an unavailable matching stratum causes a
   > pre-registered skip, not an after-result substitution.

6. **Replace the definition of B with:**

   > For each dialogue, B=floor(0.25 times the number of unique token columns in
   > E). Every policy ranks whole spans and uses the same greedy packer: visit
   > ranks in order, keep a span iff all of its not-yet-kept columns fit under B,
   > otherwise skip it; never keep a partial span. Break score ties by earlier
   > registered span index. Prefix, sinks, current query, and recent window are
   > common free invariants outside B. Report the common cap B and each policy's
   > achieved unique-column mass; the cap, not an oracle-ranked span set, is the
   > fixed budget.

7. **Replace the policy branch at `LEDGER-PLAN.md:469-473` with:**

   > Define C_{p,c} as the one-sided 95% dialogue-cluster bootstrap lower bound
   > for joint recovery of eligible policy p on corpus c, and M_p=min(C_{p,chat},
   > C_{p,tool}). Let p* maximize M_p, breaking ties by larger mean point
   > recovery and then the fixed policy order (role rule, recent+sinks, BM25).
   > If M_{p*} >= 0.80, freeze p* and do not build G1. If 0.50 <= M_{p*} < 0.80,
   > register G1 before fitting it. If M_{p*} < 0.50, report unsupported
   > generality and keep the publish gate closed. The signal gate is evaluated
   > first; if it fails, no recovery branch is interpreted. The `salience2` and
   > attention-mass diagnostics are ineligible for p*.

8. **Replace “label-free, deployment-matched” and the cache class name with:**

   > G0 reference-conditioned, cache-intervention-matched oracle:
   > utility(s)=mean teacher-forced NLL on the fixed later reference after
   > `KVCache.evict` jointly removes the registered columns minus full-cache
   > NLL. OASST2 references are self-generated greedy continuations; APIGen
   > references are gold labels. This estimates marginal direct-column support
   > conditional on surviving cached states and the fixed reference path; it is
   > not total semantic need, write-time importance, or trajectory success.
   > `KVCache.evict` retains original post-RoPE keys and logical absolute
   > continuation positions; a CPU unit test and the no-op model smoke must
   > verify cache restoration/non-aliasing before G0a.

9. **Replace “disjoint by construction and enforced by ...” with:**

   > Exact project paths are separated by convention and checked by a
   > defense-in-depth scanner; the scanner is not an information-flow proof.
   > Before any gate run, a committed lineage manifest must enumerate every
   > fit/select/evaluation path, generated-response root, imported loader,
   > checker/template dependency, and normalized exact/near-duplicate collision.
   > The G0 entry point must allowlist only the two manifest-pinned `data/g0`
   > subset paths and refuse all other input roots.

   Add guard regression tests for the three concrete bypass commands in G0R-3,
   imported `eval_*` loaders, module-level fitting under a neutral filename,
   `joinpath`/`os.path.join`, nested packages, generated-response roots, B3/S2,
   and `vendor/ifeval`. Scan recursively. Do not treat renaming to `eval_*` or
   the presence of an allowed token anywhere in a pipeline as proof of safety.

10. **Insert the following frozen-policy details before the first run:**

    > BM25 uses the current user text as query and prior eligible spans only,
    > Unicode-normalized lowercase word tokens, k1=1.5, b=0.75, the stated IDF
    > equation, span-index tie-breaks, and the common whole-span packer. Attention
    > mass is averaged over all heads and the pre-registered layer set [name it]
    > and over [all current-user query rows OR the final query row—choose one
    > now]; it excludes protected/current columns. OASST2 generation fixes the
    > exact chat-template bytes, non-thinking prefix, EOS set, greedy decoding,
    > max_new=256, and empty/truncated-reference disposition. ToolACE is used
    > only if the APIGen revision cannot be downloaded or its license is rejected
    > before any reference/model run; the trigger and chosen corpus are written
    > to the manifest before execution. Metadata hashes the tokenizer, chat/tool
    > renderers, policy code, reference records, model, corpora, and commit.

11. **Replace the generality sentence at `LEDGER-PLAN.md:459-460` and use this
    exact model-card claim unless an untouched benchmark is added:**

    > On the named Qwen3 checkpoint, fixed non-thinking templates, protected
    > prefix/recent-window policy, and registered token budget, the frozen
    > selector chosen on OASST2/APIGen was evaluated without further parameter
    > changes on Multi-IF and BFCL V3. These are post-development evaluations:
    > both families influenced earlier system design. Results establish only the
    > reported behavior in these harnesses; they do not establish a universal
    > selector, transfer to other models/budgets/agents, independence of S2 from
    > B3, or evidence for Miller's neuroscience theory.
