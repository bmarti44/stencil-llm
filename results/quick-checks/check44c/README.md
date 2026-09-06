# Check 44c — pre-written reading (2026-09-06)

Fit-on = kimi-admission.jsonl with admission-opus-patch.jsonl label replacements,
opus-admission-enrich.jsonl, and kimi-admission-2.jsonl after CPU full-message
Astra review in admission-2-astra-patch.jsonl. The latter patch changes 122 rows,
including dropping five unfilled authoring placeholders; no new messages added.
Evaluation = fresh author-disjoint fable-admission-heldout-3.jsonl, ONCE after
committed weight/threshold freeze. heldout-2 is a disclosed SECOND LOOK regression
only. v8 SETUP is a development diagnostic, never fit or threshold-selection data.
No benchmark, sealed IFEval input, or data/bench content may be opened. No fitting
except this tagger. No current evaluation responses may enter training.

C2 = BAAI/bge-small-en-v1.5 at revision
5c38ec7c405ec4b44b94cc5a9bb96e735b38267a, fully fine-tuned encoder plus dropout .1
and linear 3-class token head (O,B,I). Whole message is context. No sentence
splitter in C2's candidate path. Explicit non-user role guard. Fast tokenizer
character offsets; gold-overlapping tokens become B then I; special/pad labels
ignored. Argmax BIO decode: B begins a new run, I extends (or starts if orphan),
O/special closes. Adjacent B starts separate spans. Run character extent is first
token start to last token end; confidence = mean P(B)+P(I) across its tokens.
Message any-rule score = max decoded span confidence (0 when no span).
No role token, history, auxiliary heads, scope/key prediction or runtime guards.
512 tokens maximum; no truncation; overflow messages abstain and stay in all
reported denominators. Ideal token-run ceiling is 100% when each gold span maps
to a distinct nonempty run; report measured ceiling, exact-edge representability
and overflows. Inside-token gold edges and shared-token spans are caveats.

No author scenario IDs are supplied. Split conservatively by whole source
GENERATION BATCH within domain (never by message). Python Random(0) shuffles sorted
(domain,source) groups. First select one batch from each of six distinct domains;
then add remaining shuffled whole groups only if they improve distance to 10%
of messages. Report actual DEV fraction and >=6 domains. This preserves within-
batch scenarios and quote pairs; it is NOT domain-disjoint or a proof against
cross-batch semantic relatives. Exact normalized message duplicates fail loudly.
This grouping choice is flagged for review. Neither labels nor model outcomes
choose groups. Both fit and DEV are validated before fitting.

Recipe fixed: seeds 0/1/2, seed0 designated; final checkpoint only; 3 epochs,
batch32, AdamW lr3e-5, weight decay .01, fp32, grad clip1, 6% linear warmup and
linear decay (same scheduler as 44b). No class weights, early stopping, seed
selection or hyperparameter search. First10 updates of seed0 are the training
pilot: project total cost, require within cap, per-seed cooperative timeout4x
pilot estimate. Cap3600 cumulative GPU-allocation seconds, including load/save.
CPU calibration happens after GPU release. Foreground only; never signal any
process. Wait for other Stencil RUNNING.flags/compute jobs, exempt Brian's llama-
server; exclusive own flag removed on natural exit. No push; explicit commits.

DEV only: choose lowest feasible span threshold t (>=) at <=2% false-admission
messages among gold-empty DEV; admitted sets nested, so this maximizes one-to-one
overlap recall. Include above1 abstention. C-THEN-B combination is motivated by
44b's disclosed heldout-2 review, prospectively tested here: admit C2 spans first;
otherwise admit B's sentence if B ft-v3 seed0 >=.95 and C2 max P(B)+P(I) inside
that sentence >=t_low. Suppress fallback sentences overlapping already admitted
C2 spans; B sentences are non-overlapping. t_low is lowest feasible on the SAME
DEV with the same <=2% total empty-message admission budget. B uses unchanged
44b message-wise sentence head/history/overflow behavior. Report normalized DEV
sentence overlap with B's committed fit_ids. Freeze both arms for all three
seeds before opening heldout-3; do not select between seeds or arms after look.

GO is mechanically determined by PRIMARY seed0 C2+B: heldout-3 overlap micro
recall >=85%, payload gold-empty false admissions <=3%, quoted gold-empty <=3%,
zero non-user admissions (all families must have support), AND SETUP <=2/96 turns
with ANY unmatched admitted span, with 36/36 admit events recovered. Separately
report whether C2 alone passes the same bars. Count 4 supersedes events separately
from 36 admits, with one-to-one matching. Report request-template false admits.
GO registers the frozen combination runtime swap and authorizes gate v9 with
admission = explicit structured entry OR frozen automatic candidate, both
reported. Otherwise NO-GO; explicit entry remains first ship, no v9 authorization.
No v9 execution is included in this check.

Report exact/overlap micro P/R, positive-message macro R and predicted-message
macro P, message P/R, family rates with one-sided95% Clopper-Pearson upper bounds,
scenario bounds when author scenario IDs exist. Point rates govern GO; bounds
are uncertainty statements, not population certification. CPU4-thread latency
excludes loading; report all-message and warm(exclude first) p50/p95; combination
cost includes both heads and merge, regardless of fallback usage. Journal every
message's inputs, token offsets/BIO distributions, decoded spans/confidence,
thresholded admissions, B proposals, scores, overflow and timing during the same
one-shot run. Audit by recomputing saved records without inference.
