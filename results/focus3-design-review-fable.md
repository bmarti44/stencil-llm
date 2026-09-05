# FOCUS-3 design review (fable, one round, CPU-only) — commit 900fc6a

Scope: results/focus3-design-astra.md (D) and data/classifier/LABELS-RELATIONS.md (L),
judged against Brian's approved ship form (one HF repo with custom code; frozen trunk;
small pairwise classifier as a second weight file; custom Cache subclass carrying the
register and per-column provenance; release = attention mask inside forward, never
deletion; live rules rendered into each request; loop inside generate(); classifier
updates the register and fails safe to none). Evidence read: quick-checks README items
31-39, check35/36/37/38/39 READMEs and my check35/36/38 reviews, focus-synthesis-astra.md,
astra-research-blockers.md section 2, LABELS.md, finetune_classifier.py, the frozen
model/ft assets, src/stencil/qwen3.py (the check35 eviction primitive), and the
installed transformers 5.16.1 source (cache_utils, masking_utils, generation/utils,
modeling_qwen3). No model launched; no sealed IFEval/BFCL content read; no repo edit
besides this file.

## VERDICTS

- results/focus3-design-astra.md: **SOUND-WITH-FIXES**. The mask formulation is the
  measured primitive and the packaging is realistic on 5.16.1, but (a) the doc
  disowns the direct evidence it has, (b) the gate can pass with a classifier that
  never emits a relation, and (c) the pair unit is under-specified so `supersedes`
  cannot produce its replacement text. Fixes D1-D6 are required before the contract
  step (D §6 order step 1); the rest are wording.
- data/classifier/LABELS-RELATIONS.md: **SOUND-WITH-FIXES**. Labels are mutually
  exclusive per row and the illustrations are free of benchmark/probe content, but
  "same key" is undefined (authors will split none/supersedes/new-rule three ways on
  the same item), the reinstating message's live-version row has no label, and the
  none-prevalence of fit/held-out data does not match deployment. Fixes L1-L4 before
  kimi authoring starts.

## 1. Runtime loop and mask vs. what checks 35/39 measured

Equivalence (D:36) is right. `KVCache.evict` (src/stencil/qwen3.py:70-85) drops
columns by `index_select`, keeps `length` (RoPE offset) and the survivors' K/V; the
causal mask is built from the physical column count (qwen3.py:302) and new queries
are rotated at `cache.length` (qwen3.py:404). Softmax over the survivors equals
softmax with `-inf` on the dropped columns, so a per-request additive mask on a
never-deleted cache is the same computation for every prefill/decode query. The
check35 review (section 1) verified exactly that primitive: the evicted positions
were the generated tokens + EOS at all 36 layers, K and V, positions not reduced.

**D1 (high) D:37-38 — the doc disowns direct evidence of its own primitive.** "Neither
check tested this mask" is false in the useful direction. The design masks own-output
body + generated EOS and keeps renderer text (header, empty think block, trailing
newline) visible. That is precisely check35 `evict_answers` (generated tokens + EOS,
positions preserved) and check37's `body_eos/surviving` arm (check37/README.md
Results table): body_eos/surviving scored 31/30 at the two releases, 32/32 at both
neutrals, 1 broken episode — equal to intact (30/30/32/32, 1 broken) on n=32. The
damage the doc worries about appeared in `body_eos/rebuilt` (28/23, 11 broken), i.e.
in the TEXT rebuild of a malformed history, which a mask never performs, and in
check35 S4 (28 -> 17 after two evictions) under a protocol with unanswered filler
user turns (check35 review F4/F6; check38 review 2.4). Check39's placeholder is the
one that is NOT this primitive (it writes a fresh "." K/V; a mask cannot). So the
evidence ranking is: mask primitive = check35 S3/S4 c2 + check37 body_eos/surviving
(favourable on one task, n=32, monotone release only); placeholder = check39 (not
applicable). Replace D:37-38 with:

> Check 35's `evict_answers` and check 37's `body_eos/surviving` arm are this mask
> by construction (generated tokens + EOS removed, positions and survivor K/V kept,
> renderer text retained): check 37 body_eos/surviving scored 31/30 at the releases
> and 32/32 at both neutrals with 1 broken episode, equal to intact (n=32, one sort
> task). Its `rebuilt` mode (28/23, 11 broken) rebuilds the malformed text history
> and does not apply to a mask that never rebuilds. Check 35 S4 (28 -> 17 after two
> evictions) was measured with unanswered filler user turns and does not transfer
> cleanly. Check 39's placeholder repair writes a new "." column and is not this
> primitive; do not cite it as validation. What no check tested: masking with
> renderer recaps in the request, multi-rule union masks, and un-release (D5).

**D5 (medium) D:39, D:42 — un-release is a never-tested cache state.** All evidence is
monotone: once released, a column stays gone. The design flips masks back on at a
task resume and after a one-reply exception expires (D:11, D:12, D:14). Columns
computed while a set S was masked become visible alongside S, whose K/V never
attended to them either; this is neither the intact nor the rebuilt state of any
check. Add to D:39: "Un-release (task resume, exception expiry) produces columns
that were computed under a mask now lifted; no check has measured that state. The
gate's task-switch family is the first measurement; report its final-task success
separately from the other three families." Keep "task suspension/resume" in the CPU
list (D:42) but note it only checks bookkeeping.

**D7 (low) D:28 — pending final token epoch.** State which mask the pending token is
forwarded under: "Forward the pending token under the epoch that sampled it (R_t),
then commit R_{t+1}." Its tag equals its body's, so it is masked whenever the body
is; the sentence removes an implementation ambiguity, nothing more.

**D8 (low) D:29 — "-inf".** In 5.16.1 the eager path fills with `torch.finfo(dtype).min`
(masking_utils.eager_mask) and the SDPA path passes a boolean mask; say "masked
(boolean False / dtype-min additive), never a finite penalty".

Prefix-cache claim (D:41): correct, and slightly understated. K/V of column j at
layer L depend on every mask in force when j was computed, so two sessions with the
same token prefix and different release histories hold different tensors; a
token-keyed prefix cache (vLLM automatic prefix caching, SGLang RadixAttention) would
serve the wrong K/V silently. Within one session there is no issue because nothing
is ever recomputed. One addition: because the recap is rendered inside every user
message, cross-session sharing already stops at the first request, so the practical
loss is small; say so.

## 2. HF packaging on transformers 5.16.1 (verified against the venv source)

Lock check: uv.lock pins transformers 5.16.1 and `.venv` has 5.16.1 / torch 2.13;
the system `python3` has 5.2.0. D:49 is right; add "run only via `uv run`".

What works, with the concrete hooks (replace D:45's second sentence with this):

- `Focus3Cache(Cache)`: `Cache.__init__(layer_class_to_replicate=DynamicLayer)`;
  `DynamicLayer.update` is `torch.cat` append-only; `get_seq_length`/`get_mask_sizes`
  return the physical length, which is what the design needs. `generate` keeps a
  user-passed cache untouched (`_prepare_cache_for_generation` returns early on
  `model_kwargs["past_key_values"]`; tuples raise). Add the register, provenance
  tags, event log and pending token as plain attributes; override `crop`,
  `reorder_cache`, `batch_repeat_interleave`, `batch_select_indices` to raise (they
  are the beam/assisted/continuous-batching entry points).
- Positions: `Qwen3Model.forward` derives `position_ids` from
  `past_key_values.get_seq_length()` when none are given, and 5.16.1's
  `prepare_inputs_for_generation` does NOT compute them from an attention-mask cumsum
  (verified: it only passes `position_ids` through). So positions advance over all
  physical columns automatically; still pass explicit `position_ids` as D:39 says.
- The mask, two viable routes: (i) a 2D `attention_mask` of shape (1, past+q) with 0
  at released columns — `create_causal_mask` ANDs it in as `padding_mask_function`,
  constant across queries, exactly R_t's semantics; or (ii)
  `create_causal_mask(..., and_mask_function=lambda b,h,q,kv: allowed[b, kv],
  allow_is_causal_skip=False)` inside an overridden `Focus3Model.forward`, passing
  the result as `attention_mask={"full_attention": mask}` (Qwen3Model.forward skips
  mask creation when it receives a dict). Route (ii) uses the vmap path (torch>=2.6).
  Either way, the override must live in `forward`, because `generate` builds the mask
  dict itself only for compileable caches.
- Attention backend: `flash_attention_mask` returns None or the 2D mask and FA2
  un-pads from it, so interior zeros corrupt the sequence rather than mask it; flex
  needs a BlockMask. Raise unless `config._attn_implementation in {"eager","sdpa"}`.
- Second weight file: `from_pretrained` loads only files named in the safetensors
  index, so `classifier.safetensors` is ignored by the trunk loader; fetch it with
  `transformers.utils.hub.cached_file(repo, "classifier.safetensors", revision=...)`
  in an overridden `from_pretrained` classmethod and build the two BERT branches from
  a config inside the bundle. Both tokenizers via `AutoTokenizer.from_pretrained(repo,
  subfolder="classifier_tokenizer")`.
- The custom loop: overriding `generate(messages=...)` on the remote-code class is
  fine. The sanctioned alternative is the hub `custom_generate/generate.py`
  mechanism (`model.generate(custom_generate=repo, trust_remote_code=True)`); either
  is acceptable, name the choice.

What breaks (replace D:60 with the reasons, not just the list):

> vLLM/SGLang/TGI cannot run this package without a dedicated engine adapter: they
> load architectures from their own model registry (trust_remote_code only affects
> config/tokenizer code), their paged/flash kernels take no per-column mask,
> automatic prefix caching and RadixAttention key K/V blocks by token IDs (D:41
> violation), and their OpenAI-style chat endpoints are stateless, so there is no
> carrier for `Focus3Cache` between calls. Beam, assisted/speculative decoding and
> continuous batching call `crop`/`reorder_cache`/batch selection, which this cache
> refuses. Cache quantization/offloading rewrite layers and drop the tags.

## 3. Pairwise classifier and admission

**D3 (medium) D:65-67, L:6-7 — the pair unit is under-specified.** B is the whole new
message, but the data rows (L:7, L:42 `target_span`) are per (target, span), and an
accepted `supersedes` needs a verbatim replacement span (D:67, D:70). A 5-way head
over (rule, whole message) cannot say which sentence is the replacement; "accept a
replacement only when its rule span and target are unique" has no defined selector.
Replace D:65's second sentence with:

> The pair unit is (target version, candidate span). B is `[previous user]
> {prev_or_empty}\n[user] {new_user_message}\n[span] {candidate sentence}`, the
> candidate coming from the existing sentence splitter; the label applies to that
> span against that target. For k spans and m eligible versions batch k*m pairs,
> k <= 4 and m <= 16 (overflow -> none + diagnostics). `supersedes` uses the
> classified span verbatim as the replacement text; `reinstates` copies the
> referenced original; `cancels`/`completes` need no text.

and make L:6 say the same ("Input: old rule ... , new message, the candidate span,
optional previous user turn").

**D4 (medium) D:69 with LABELS.md:19-20 — "fails safe to none" is not quite true.** The
frozen admission head labels "sentences that change or cancel an earlier rule" as
`rule`. If the relation head is confidently `none` (P(none) >= .98) on a real cancel
or replacement, D:69 admits that sentence as a NEW key: nothing is retired (safe),
but the recap now renders both "Start with a weather note" and "Stop adding the
weather note". Uncertain heads are blocked by the all-none requirement; confidently
wrong ones are not. Two fixes: (1) count this in the gate (D2 below, "contradictory
recap"); (2) in D:69 add "A span admitted as new-rule while any eligible version of
the same task/global scope is live is flagged `admitted_beside_live` in diagnostics;
the gate reports the count." Do not add a lexical veto (it would be a heuristic the
data process forbids).

The head's disclosed development influence (LABELS.md:10-14) is not a contamination
problem for the gate — the 64 episodes are fresh and never touch the probe — but it
is a provenance problem for shipping: `provenance.json` cannot describe a head whose
training composition does not reproduce (LABELS.md:46-48). D:4 already blocks on
reconciliation; keep it. Optional, zero cost: initialise the relation encoder from
base `BAAI/bge-small-en-v1.5` instead of `model/ft/encoder` (D:63), so only the
admission branch carries the history; the fresh relation data is the only thing the
relation branch should know.

Other checks: pair limit 512 fits the encoder (`max_position_embeddings` 512). Labels
are mutually exclusive per row (L:7) and `new-rule` is correctly kept out of the
softmax. Scope/version handling (D:11-15) is deterministic and consistent; one gap:
say explicitly that the rendered set G_t excludes versions shadowed on the current
request's scope (a global v1 with a task-scoped v2 exception renders only v2 while
that task is selected), otherwise the recap carries two contradictory rows. Thresholds
(.98/.95) are declared proposals; fine. Latency (D:71) is marked unmeasured; fine.

## 4. LABELS-RELATIONS.md readiness for kimi authoring

**L1 (high) L:12, L:15, L:27 — "same key" is undefined.** Every none/supersedes/new-rule
decision hinges on whether two instructions share a key, and the spec never says
how an author decides. Insert after L:9:

> Key identity: two instructions share a key when they cannot both be obeyed on the
> overlapping scope (a direct conflict: ascending vs descending; Celsius vs
> Fahrenheit; glossary required vs no glossary) OR the new message explicitly refers
> to replacing/withdrawing the old one ("instead", "rather than the earlier", "drop
> that requirement"). Compatible additions ("also number the scenes" while "keep
> scenes short" is live) are `none` for the pair and `new-rule` for the message.
> Different subject matter is always a different key even in the same domain.

**L2 (medium) L:24-26 — the reinstating message's live-version row has no label.**
"Go back to sorting by supplier" while v2 (shelf) is live: the (v1 inactive, msg)
row is `reinstates`; the (v2 live, msg) row is unspecified — `supersedes` needs a
verbatim replacement span the message lacks. Add to L:24: "The currently live
same-key version receives `none` on a reinstating message; its shadowing is derived
by precedence from the new version's later turn (D:11), not annotated."

**L3 (medium) L:12, L:17, L:33 — scope wording authors will misread.** "mismatched
scopes" (L:12) must mean "a task-scoped update against a rule of a different task",
because a narrower update against a global rule of the same key is `supersedes` on
the intersection (L:15, L:17B). And the one-reply `supersedes` (L:17B, L:33; D:70)
contradicts LABELS.md's single-reply -> none in a way authors will get wrong half
the time. Recommend CUTTING it: label one-reply conflicts `none` for the pair; the
exception is in the current request text anyway, which is the position that wins
(check38 review 2.3), and removing it also removes a mask flip the following turn
(D5). Replacement for L:33 first sentence: "Single-reply constraints are `none` for
persistent admission AND for every pair; they are answered from the request text
and never enter the register." If Brian keeps the temporary exception, L:17B must
say "label `supersedes`, scope `single-reply`" explicitly.

**L4 (medium) L:46-50 — prevalence and held-out power.** At inference nearly every
pair is `none` (one message against up to 64 versions), but the fit set is 20% none
and the held-out has ~80 positives per label. A zero-error observation on 80 items
bounds the per-label error at 3.7% (95%); the gate's ZERO false retirements over
roughly 64 x 6 x 5 ~ 2,000 pair decisions needs a per-pair false-positive rate
under ~5e-4, which no held-out of this size can show — the gate is the binding test
and the spec should say so. Changes: (a) fit rows: 1,000 per positive label plus
>= 2,000 `none`, of which >= 800 are hard negatives (same domain, near-key, quoted,
tool-role, wrong task); (b) held-out: 400 positive pairs + >= 1,500 `none` pairs
(>= 500 hard), and report the false non-none rate at .98 with its denominator;
(c) specify `label: null` and `message_new_rule` for `old_rule=null` rows, and
`message_new_rule: false` on pair rows unless a separate admitted span exists.

**L6 (low) illustrations** — no benchmark markers or probe wording; the generic-word
hits in existing data (glossary, Celsius, shelf, acronyms) are different sentences;
"start with a weather note" overlaps IFEval only at the constraint-TYPE level that
LABELS.md:9-10 already discloses. Sealed files were not opened. Fine as written.

**L7 (low) L:41** — add two hard cases: "compatible addition on a live task (none +
new-rule)" and "reinstates vs supersedes with a changed value".

Held-out authoring by fable (L:49) is compatible with this review as long as the
illustrations stay development-only, as L:48 says.

## 5. The 64-episode feasibility gate

Endpoints and reading (D:81-84) are frozen, mechanical and honest about the ceiling
(D:86). Cost: check39 ran 1,152 generations of <= 64 tokens in 16.6 GPU-min; the
gate is 1,152 + 36 generations of <= 96 tokens with longer prompts (recap + 256-token
delays) plus <= 3 s CPU per turn, so 45-90 min projected; the 3 GPU-h cap holds
with the 25% reserve. The 12-episode setup projection rule (D:80) is adequate.

**D2 (high) D:83-84 — the gate can PASS without the classifier ever emitting a
relation.** C's PASS terms are: stale <= half N, `stale OR broken` fewer, successes
>= N, zero new breakage, zero false retirements, successes >= O-2. An all-none
relation head plus `new-rule` admission of every replacement sentence satisfies all
of them: nothing is ever retired (zero false retirements by construction), both old
and new rules are rendered, and the trunk follows the later/current one often enough
to halve N's stale count (check38: current-turn text alone 27/32). The question
"does a classifier-driven register control what governs" is then unanswered, and
the register is not doing anything the recap text is not. The blockers doc's own
sketch had the missing endpoint ("active-state agreement"); it was dropped. Add to
D:81 a fifth endpoint and to D:83 a PASS term:

> register agreement = at every scored turn C's rendered set G_t (ids/versions/
> scopes) equals O's; an episode is register-exact if all its turns agree. A
> contradictory recap = two rendered rows with the same gold key on one turn.
> PASS additionally requires C register-exact in >= 48/64 episodes and >= 12/16 in
> every family, and zero contradictory-recap episodes. Report the applied-vs-gold
> event confusion (supersedes/cancels/completes/reinstates/none) by family.

Two smaller points: (a) D:79 says arms "independently admit initial rules" — then O
is not "oracle register" at setup; say O admits by gold too, else O's own admission
errors leak into "O must reproduce its frozen gold transitions exactly". (b) D:76
"independent authored scenario families" — name an author who wrote no relation
data (L:51 requires family separation but not author separation).

## 6. Cuts

1. One-reply temporary exception (D:70, L:17B, L:33): cut (L3). Removes a label cell,
   a mask flip, and a LABELS.md contradiction.
2. `completes` on sub-units (L:23B): cut for v1; task-level completes only. Sub-unit
   lifetimes are the confusable case and the gate has no sub-unit family.
3. Optional: `reinstates` and the complete-reopen family together. Reopening without
   restating text is the only case that needs it; if cut, the 4-way head saves ~1,000
   rows and 100 held-out items, and the family's 16 episodes go to override/cancel.
   Keep only if Brian wants reopen in v1.
4. Do not add a render-only or mask-only arm to the gate (D:86 is right to say
   there is none); the register-agreement endpoint answers the classifier question
   without a fourth arm. Attribution of mask benefit is a later, larger test.
5. Drop `[previous user]` from A/B? No — keep; "cancel that" needs it (D:8).
6. Initialise the relation encoder from base bge (D4) — a cut of inherited history,
   not of work.

## 10-line summary

1. Design SOUND-WITH-FIXES; LABELS-RELATIONS SOUND-WITH-FIXES; no UNSOUND file.
2. Mask == position-preserving eviction holds; the doc wrongly says no check tested it — check35 evict_answers and check37 body_eos/surviving (31/30/32/32, 1 broken = intact) ARE this primitive; check39 placeholder is not.
3. Un-release (task resume, exception expiry) is a cache state no check measured; flag it and read the task-switch family separately.
4. Prefix-cache claim correct: K/V carry the mask trajectory; token-keyed caches serve wrong tensors.
5. Packaging realistic on 5.16.1: `Cache(layer_class_to_replicate=DynamicLayer)`, mask via 2D padding mask or `and_mask_function` in an overridden forward, positions come from physical `get_seq_length` (no cumsum trap), reject FA2/flex; vLLM/TGI break on registry, kernels, token-keyed APC and stateless chat API.
6. Pair unit under-specified: B must include the candidate span or `supersedes` has no replacement text (D3).
7. Fail-safe caveat: admission head labels cancels as `rule`; a confidently-none relation head admits the cancel as a new key -> contradictory recap (D4).
8. Gate loophole: an all-none classifier plus new-rule admission passes every term; add a register-agreement endpoint (>=48/64 register-exact, zero contradictory recaps) (D2).
9. LABELS-RELATIONS: define "same key" (L1), label the live version on reinstatement (L2), fix scope wording and cut the one-reply supersedes (L3), raise none prevalence and held-out none count (L4); illustrations are clean.
10. Cuts: one-reply exception, sub-unit completes, optionally reinstates+reopen; init relation encoder from base bge; cost fits 3 GPU-h.
