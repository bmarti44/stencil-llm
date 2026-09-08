# Next hypothesis: a small supervised current-focus interpreter

2026-09-08. Astra xhigh, native author-disjoint research. Audience: root's next
preparation and budget decision. This is a bounded assessment of one mechanism,
not launch authorization, a general memory survey or an implementation brief.
Fit-on none in this task; all exposed projects remain DEV and excluded from new
fitting and fresh evaluation. No model/training/authoring call, weight load,
download, package change, generated-code execution or benchmark acquisition was
performed. Existing sources and metadata were read; no old case bank was opened.

**Rank 1: prepare a fresh Qwen3-4B LoRA interpreter trained to emit source-grounded
current prose in the existing small `record_focus` shape.** Its explicit cheapest
candidate is final-JSON-only supervised targets with nonthinking inference,
compared with the same unchanged 4B base under the identical mode, prompt, schema,
output allowance and evaluation policy. Use the existing local Hugging Face
nonthinking generation primitive for this isolated probe; native LoRA serving
is not a prerequisite. This is a testable training hypothesis,
not a prediction that answer-only SFT will learn the required interpretation.
The published evidence is sufficient to justify cheap preparation, not sufficient
to justify a full training run or assert that a small dataset will work.

Retain authentic source events, their roles and order. Keep generated guidance
fallible and disposable; the worker's original sources remain authoritative.
Train the interpreter to express current scope, conditions, permissions,
exceptions, adoption and retirement, not just produce salient excerpts or valid
IDs. Preserve wording in a target when an unchanged source clause already states
the applicable instruction; use reviewed scoped prose when cross-message
interpretation is necessary. That label discipline is not an enforced verbatim
copy guarantee, and no new quote field, critic, policy language or resolution
engine is proposed.

The material change is learned conditional interpretation in fresh weights.
It does not reopen the failed untrained nonthinking reader or reasoning pilot,
change their gates, tune their caps, or reuse their examples. A same-base control
is essential to distinguish adaptation from a different model/mode's capability;
comparing new 4B results with the spent 30B run would confound all of those changes.

## Evidence that changes the recommendation

**VerIH supports learnability, with substantial transfer and cost limits.** Its
Qwen3-8B LoRA SFT conflict score rises 46.48→66.37, while aligned performance falls
88.96→84.48 and MATH-500 falls 93.40→85.80. SFT uses 60,000 distilled
reasoning-plus-answer traces in each dataset, rather than a small answer-only
set. The reported multi-turn conflict improvement 40.63→84.53 concerns its
trained RLVR model, not this LoRA baseline. Appendix C's GRPO recipe reports
four H100s and 12–18 hours; it is not a measured local SFT estimate. The main
training problem is system/user hierarchy with verifiable response constraints,
not complete evolving current-focus extraction. Thus hierarchy learning and
some transfer are demonstrated, but cheap 4B learning of our scope/adoption/
permission/exception/retirement/dependency task is not. Do not import its
IFEval-derived data. [Zheng et al., VerIH v5, 1 July 2026, sections 4.2, 5, 6.4,
Appendix C and Tables 1/2/6](https://arxiv.org/html/2511.04694v5).

**Extraction is a useful mechanical distinction, not a completeness theorem.**
LLMLingua-2 learns preserve/discard labels using GPT-4-distilled MeetingBank text
and a small bidirectional encoder. Its reported out-of-domain tasks concern
compression, QA and related outcomes; it does not evaluate our changing
instruction authority. The authors describe extraction as faithful, but their
own discussion identifies detail loss in extractive summarization datasets and
noisy teacher compression. A returned subsequence cannot introduce a new token,
but that is weaker than preserving a condition's meaning or every applicable
instruction. [Pan et al., LLMLingua-2 v2, 12 August 2024, sections 1, 3–5 and
Limitations](https://arxiv.org/html/2403.12968v2).

**Implementation mechanisms exist, without a local training guarantee.** PEFT's
LoRA freezes the original weights and learns low-rank updates; the base remains
resident and training still has activation/optimizer costs. Separate adapters
can add deployment overhead, so generic efficiency descriptions are not our
latency measurements. [Hugging Face PEFT LoRA documentation, current main,
accessed 8 September 2026](https://huggingface.co/docs/peft/main/en/conceptual_guides/lora).
Official SFT documentation distinguishes completion-only from full-sequence loss
and warns through its documented behavior that preparation can truncate to a
maximum length. Prefix masking and length rejection therefore need direct
verification in our own consumer, not assumptions based on a trainer name.
This citation supports loss semantics, not installing TRL or adopting its current
implementation. [Hugging Face TRL SFT Trainer documentation, current main,
accessed 8 September 2026](https://huggingface.co/docs/trl/main/en/sft_trainer).

**Nonthinking and adapter serving are documented, but their exact local
combination remains unqualified.** Qwen3-4B documents a hard
`enable_thinking=False` switch and tool use in both modes. That supports an
explicit final-only target protocol, including direct local generation, not its
semantic adequacy. [Qwen3-4B model
card, Qwen, accessed 8 September 2026](https://huggingface.co/Qwen/Qwen3-4B).
At the existing vLLM pin, `Qwen3ForCausalLM` implements `SupportsLoRA`, including
packed q/k/v mappings; adapter serving selects named modules with explicit LoRA
enablement. These are source-level capabilities, not an executed 4B-adapter
named-tool qualification. [Pinned Qwen3 implementation](https://github.com/vllm-project/vllm/blob/fe9c3d6c5/vllm/model_executor/models/qwen3.py),
[pinned LoRA serving documentation](https://github.com/vllm-project/vllm/blob/fe9c3d6c5/docs/features/lora.md).

My inference from these sources and the local audit is modest: a small learned
interpreter is a better-supported materially different next hypothesis than
another untrained summarization prompt. The evidence does not favor assuming
large-scale RLVR is locally cheap, assuming generic compression preserves live
instructions, or assuming additional reasoning always pays for itself. The
final-only proposal deliberately buys simpler labels and lower potential output
cost at the risk of losing useful reasoning; the unchanged-base comparison and
fresh semantic measurements must decide that risk.

## Why source-preserving alternatives rank lower for this next step

Selecting message IDs and deterministically echoing their original text would
prevent rewriting those selected bytes. Keeping original role labels and order
could also make their provenance clear. It would not prevent an omitted rule,
a selected obsolete statement, a missing exception/adoption antecedent, or a
message that contains both applicable and inapplicable clauses. Whole-message
copies retain such mixed content; span/token deletion can remove a condition or
negation. Literal copying is consequently useful evidence preservation, not
a substitute for current applicability.

An IDs-only output plus original excerpts can be a legitimate **source-evidence
reminder** if that is the prospective claim and the worker interprets it. It
must not be relabeled a complete set of current instructions by grammar alone.
Our worker already retains the complete authentic prefix, so duplicating selected
source text offers an attention/cost hypothesis rather than new source access.
No retrieved primary evidence establishes that this solves the observed
completeness problem. I therefore do not select a second extraction arm or a new
encoder for this first feasibility step. Do not download LLMLingua assets or
borrow its data. If future evidence makes source-evidence reminders preferable,
they need their own prospective claim, not a retrospective passing label on the
failed pilot.

Likewise, free-text SFT does not become safe because it cites an existing message.
Independent target review must distinguish supported paraphrase from a material
change of scope or modality. Exact copying can be used where a self-contained
current clause makes it appropriate, with no new runtime mechanism; the trained
model is still measured for unsupported additions and omissions. A multi-agent
critic tree, compiler or mutable rule registry would add unevidenced moving parts
before the basic learning question is answered.

## Local feasibility: what is now known

[Sol's read-only inventory](inventory-sol.md) identifies existing training
primitives, not an accepted recipe. Root subsequently completed a full CPU
content rehash of all 13 original 4B assets: 8,060,926,626 file bytes in
10.50203125900589 seconds, matching the historical base-only hashes and cached
acquisition revision `1cfa9a7208912126459214e8b04321603b3df60c`.
I read and rehashed [that receipt](base-assets.json); I did not repeat the large
file hash job. This closes the earlier local-byte-availability gap, not
pretraining-data provenance, training feasibility or serving qualification.
The old untracked adapter remains excluded.

The index-declared tensor storage is 8,044,936,192 bytes, about 7.4924 GiB;
file bytes additionally include headers, tokenizer and documentation. I read the
small local config: 36 layers, hidden size 2560, 32 query heads, 8 KV heads,
head dimension 128. For the inventory's illustrative rank-8 q/v-only LoRA,
36 × 8 × [(2560 + 4096) + (2560 + 1024)] = **2,949,120 parameters**.
Four float32 parameter/gradient/Adam arrays would occupy 47,185,920 bytes
(45 MiB), excluding all other overhead. This arithmetic does not size activations,
resident base, logits, workspaces, save/load peaks or effective batch cost.
Rank 8 is a reusable mechanical starting option, not a literature-selected or
newly optimized semantic hyperparameter.

The reported historical 14.14-second, at-most-256-token two-adapter fit and
13.351-GB peak cannot size full conversation prefixes. Neither old 30B generation
rates nor the small technical smoke rate estimates 4B training throughput.
Measure the actual approved input/target lengths and longest-bucket steps first.

The CPU hash job used `/usr/bin/python3`, with a different package environment
from the prospective repository `.venv/bin/python`. The latter is reported as
torch 2.13.0, transformers 5.16.1, PEFT 0.20.0 and accelerate 1.14.0; PEFT and
accelerate are not yet in the project lock. Metadata availability is not
compatibility. Root must select and freeze one environment; no installation or
package mutation is implied by this report.

One concrete protocol distinction is already known: the accepted
`native_reasoning_tool` client requires positive generated reasoning and valid
boundaries, and rejects reasoning markers in its rendered prompt. It cannot
silently consume final-only nonthinking SFT targets. This does not block a cheap
isolated selector test: use the inspected local HF nonthinking generation
primitive, with the same exact chat-template prefix and final JSON-object-plus-
EOS target for base and adapter. Apply strict structural/source-ID validation to
the complete returned object; malformed or capped output remains failure with
no retry or repaired extraction. Preserve prompt and full output IDs, decoded
bytes, actual generation settings, adapter/base identity and timings for both.
No native grammar benefit is assumed for this local probe.

Training and this first evaluation must agree on the exact template, generation
prefix, EOS, loss positions and nonthinking behavior. Only after useful fresh
selector evidence would worker integration require its own measured protocol and
resource qualification; if that integration uses vLLM LoRA, its exact nonthinking
named-tool path must then be checked. The existing 30B thinking qualification
cannot supply it, but requiring a new server path before any semantic evidence
would be an unnecessary feasibility prerequisite.

## Cheapest falsifiable next step

**Prepare one fresh Kimi label-and-length calibration packet, then perform its
CPU-only review and tokenization before any training launch.** This is the
recommended next preparation unit, conditional on root's authoring authorization;
no such authoring was performed or budget granted here. It need not contain a
new set of executable coding projects or a training/serving framework.

The packet should contain independently authored whole conversations spanning
short, longer and change-heavy prefixes, with source-supported complete current
prose targets at their work requests. Use the original task domain's authority,
permission, scope, exception and retirement requirements; do not seed wording,
scenarios, labels or solutions from exposed cases or downloaded benchmarks.
Keep labels independently reviewed against their exact source, including the
source evidence that makes an interpretation applicable. Source IDs are audit
anchors, not a coverage oracle. Whole conversations and shared scenario families
must be assigned to FIT/DEV/withheld roles before expanding their prefixes.
Withheld material must not become gradient or hyperparameter-selection data.

The CPU packet must make the intended final-only local HF format concrete and
record: complete prefix and target token lengths, maximum and distribution by
conversation length, exact template/schema/tokenizer hashes, which target/EOS
positions receive loss, and which prefix/padding positions are masked. Reject
silent truncation, empty target supervision, shifted template boundaries,
ambiguous gold scope or citations that do not support their claims. Do not
simplify away meaningful constraints to make this packet fit. These are
falsifiable failures of the proposed preparation, not failures of model
learnability. Passing establishes a coherent label/format/capacity specification
only; it predicts neither quality nor speed.

The **first later GPU measurement**, only under a separately reviewed bound,
should be one training-mechanics run on approved FIT-only material at the actual
longest sequence bucket, with warm-up and timed steps fixed beforehand. Measure
base load time, step time, peak allocated/reserved memory, loss/mask correctness,
finite and nonzero aggregate adapter updates, absence of trunk gradients and
unchanged trunk identity, adapter save/reload time and bytes. Do not require every
individual LoRA tensor's first gradient to be nonzero: zero-initialized factors
can make that assertion mathematically wrong. This is a resource/mechanics test,
not a transfer experiment or permission for repeated tuning.

Use the measurements to cost the proposed selector-only full run explicitly:
load/hash + planned step count × measured step cost + save + unchanged-base/
adapter local inference + receipts/cleanup. Worker/server integration cost is a
separate later measurement, not prerequisite infrastructure. Include fresh authoring and
review effort separately. Reject or defer the proposal if the selected environment
cannot run it correctly, untruncated contexts do not fit, or the measured total
exceeds the later authorized bound. No numerical training budget, number of
examples, learning rate, epoch count, output cap or success threshold is inferred
from a paper, the 256-token inventory run or spent outcomes.

If mechanics and cost pass, the smallest semantic experiment is one fixed adapter
versus its unchanged base on wholly withheld conversations under identical local
HF settings, without a coding worker or new vLLM deployment. Measure complete-current-focus frequency and explicit omission,
unsupported addition, wrong authority/scope/modality, stale-rule and citation
errors, together with all tokens and wall time. A few correct training examples
or loss reduction does not establish transfer. New vocabulary and independently
authored scenarios matter; slicing more prefixes from one conversation does not
create independent cases. Stop the fixed test as registered rather than use its
failures for immediate prompt, format or cap revisions.

Keep three claims separate: coherent/affordable training mechanics; selector
semantic performance on fresh conversations; and downstream code usefulness.
The failed pilot's perfect-current-focus continuation condition stays binding
for that run. It is **not a universal perfect-selector prerequisite** for future
paired utility work. A later prospective comparison may study imperfect automatic
and manual agents with an absolute usefulness requirement and justified margins,
while reporting semantic defects. Neither ideal manual performance nor
representation superiority is required. Sample size and inferential details
belong to that later adequate fresh registration, not this small feasibility
packet. Selector scores alone cannot establish code utility or the larger goal.

## Evidence gaps and stopping decision

| Material claim | Evidence status | Remaining falsifiable question |
| --- | --- | --- |
| Training can improve instruction prioritization | Direct primary support; method/domain transfer limited | Does this same-base SFT improve current-focus interpretation on fresh conversations? |
| Copying helps source fidelity | Exact-byte benefit follows mechanically; semantic preservation does not | Would any chosen excerpts retain every necessary condition and authority antecedent? Not selected as an extra arm now. |
| Original local 4B bytes are available | Root's full hash receipt, independently read and bound | Freeze selected environment and preserve original trunk during adaptation. |
| Long-context LoRA is cheap enough | Unestablished; short prior mechanics do not size it | Actual length distribution, longest-bucket step/memory and full end-to-end cost. |
| Final-only targets support the isolated selector probe | Direct local HF generation is available; exact training/evaluation agreement still needs checking | Exact nonthinking template, target masking, adapter loading, raw tokens and JSON/EOS behavior. Native named-tool integration is a separate later question. |
| Useful automatic/manual parity is achieved | No; terminal pilot remains incomplete and failed its rule | Prospective fresh worker utility comparison, not a perfection detour or retrospective rescue. |

The primary sources above form the claim-to-source ledger: VerIH methods and
counterresults; extractive-compression methods/limitations; PEFT loss-independent
adapter mechanics; TRL loss/template behavior; Qwen mode contract; and the exact
vLLM serving pin. Dates/versions and access are stated at their citations. All
web sources were accessed 2026-09-08. The PEFT v0.20.0 documentation URL returned
an internal retrieval error; its current main conceptual page was accessible and
is used only for general mechanics, not exact installed-API qualification.

Discovery consisted of bounded searches for LLMLingua-2 methods, the original
Qwen3-4B mode card and vLLM LoRA support, followed by focused reads of VerIH's SFT,
multi-turn and hardware sections and the exact serving implementation. No broad
memory rediscovery, model/data download or benchmark example bank was acquired.
The deep-research planning tool was not available in this native tool set; scope
and progress were recorded in this brief/conversation, and this sole permitted
Markdown file is the canonical deliverable. No separate report-source artifact
or additional output format was created. Structural checks verify the written
Markdown and source links; no rendered-document visual QA is claimed.

Research stops here: the consequential evidence and counterevidence are bounded,
and another generic paper cannot supply clean local labels, long-prefix cost,
exact local HF training/evaluation agreement or fresh semantic transfer. The next uncertainty
requires the concrete packet and measured experiment above, under root's own
registration and budget decision.

## Local input bindings

| Input | SHA-256 |
| --- | --- |
| `results/coding-auto-reasoning/research-next/BRIEF.md` | `b12199619a8d2ac0462aa2e3e0fbf436a812dde8582d92c6be44a8c5d6a38787` |
| `results/coding-auto-reasoning/research-next/inventory-sol.md` | `73d09946c0373e673fdd01a8ba6ef1698e12c0ade9a9aede3391b5ef373cd5c3` |
| `results/coding-auto-reasoning/research-next/base-assets.json` | `4987d6eec20a7628d45d64799cb8b7fc7250870be2e868755880e70b7e2b5227` |
| `results/coding-auto-reasoning/run-01/audit-astra.md` | `a4832c1be23ab6d80773dfa9635ee202d6ee0fde70f6cb8a62ed8bb6bbe1c330` |
| `results/coding-self-cue/research-reset/report-source.md` | `2366f03e82823949c33242926eed54e18996c046595bd6260cd657dabf5cce5f` |
| `results/coding-competence/research-next/report-source.md` | `93bf15f547aabce8e065a7c5c10ba599af4a1ee0e515f200f26fe510a3e0fa5b` |
| `models/qwen3-4b-hf/config.json` | `8ba006f74fecfaaeb392872a60f4a480e7ec9860153d2e1b769ec81f9a147f8a` |

The later research report's no-perfect-manual clarification governs over the
older reset report's universal-prerequisite wording. The terminal audit and all
frozen verdicts remain unchanged. Original base identity is qualified only as
stated in base-assets.json, not as a claim about unknown pretraining contents.
