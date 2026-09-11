# License inventory (2026-09-11)

Component-by-component ownership and terms, written before any Hub push
(plan/BACK-ON-TRACK-PLAN.md, section C). Verify the "upstream" rows against the
upstream repositories before relicensing anything.

| Component | Path | Owner / origin | Terms found in repo | Notes |
|---|---|---|---|---|
| Stencil code, plans, reports | `src/`, `scripts/`, `tools/`, `tests/`, `plan/`, `results/*.md` | Brian Martin (with AI coding agents) | root `LICENSE` = GPL-2.0 | Sole human author. Plan default: relicense Brian-owned code to Apache-2.0 at Release 1; the root `LICENSE` is unchanged until that step. |
| Wave runtime package | `deploy/stencil_wave/` | Brian Martin | model card says `apache-2.0`; no LICENSE file in the folder | Conflicts with the root GPL-2.0 declaration; resolved at Release 1 (archived if pins are dispensable). |
| Sentence classifier weights | `data/classifier/model/ft/` (published as `bmarti44/assistant-memory-sentence-classifier`) | Brian Martin; fine-tune of `BAAI/bge-small-en-v1.5` | base model MIT (`5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`) | Released under MIT with base attribution. |
| Lifecycle (relations-v2) classifier weights | `data/classifier/model/relations-v2/` | same as above | base model MIT | Release 1, MIT. |
| Wave / selector checkpoints | `results/qwen/w0-ce.pt`, `w0-proxy.pt`, `s3-selector-weights.pt` | Brian Martin | none stated | Trained on synthetic generator output; Release 1 under the code license. |
| Classifier training / held-out sentences | `data/classifier/` | written by kimi-k3, reviewed by sol and Opus, held-out partly by fable; commissioned by Brian | none stated | Model-written text; no benchmark content by policy (`LABELS.md`). Release 1 as a labelled reconstruction, CC-BY-4.0 recommended. |
| Multi-IF records | `results/qwen/multiif-evict-909-prequery-v2/` | derived from Meta Multi-IF (`data/bench/multiif_en.jsonl`) | Multi-IF is released by Meta under its own terms (CC-BY-NC-4.0 per its card; verify) | Records contain benchmark prompts; not part of any Hub release. |
| BFCL evaluator | `vendor/bfcl_eval/` | UC Berkeley Gorilla project | Apache-2.0 (`vendor/bfcl_eval/LICENSE`) | Vendored unchanged. |
| IFBench checker | `vendor/ifbench/` | AllenAI IFBench | no license file vendored; upstream Apache-2.0 (verify) | Add the upstream LICENSE file at Release 1. |
| IFEval checker | `vendor/ifeval/` | Google Research | no license file vendored; upstream Apache-2.0 (verify) | Add the upstream LICENSE file at Release 1. |
| NLTK data | `vendor/nltk_data/` | NLTK project | per-package (mostly Apache-2.0 / CC) | Evaluation only. |
| Qwen3 trunks | `models/qwen3-*` (gitignored) | Alibaba Qwen | Apache-2.0 | Never redistributed by this repo. |
| GPT-2 small | `models/gpt2-small.pt` (gitignored) | OpenAI | MIT (modified) | Never redistributed. |
| MemoryCode (to be vendored, Exp 3) | `vendor/memorycode/` | Cohere Labs Community | Apache-2.0 | Pin the sha in `data/bench/pins-manifest.json`. |

Decisions taken by default (Brian may override): classifier releases under MIT;
Brian-owned code to Apache-2.0 at Release 1 (a root `LICENSE` swap plus SPDX
headers are not required for the classifier push and are not done yet); vendored
components keep their own licenses and get their LICENSE files added where missing.
