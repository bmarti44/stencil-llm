# ruff: noqa: E501
"""BENCH-WAVE runner library (B0.3): IFEval loading, scoring, and the
single KV-cached greedy generator every arm uses.

Scoring wraps the vendored upstream verifiers (vendor/ifeval, from
lm-eval's pinned copy of Google's code) — strict + loose, four metrics.
langdetect's internal randomness is pinned at import. The single-use
invariant lives with the CALLERS: nothing here touches the 541 with a
model; sealed jobs do that once.
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT / "vendor") not in sys.path:
    sys.path.insert(0, str(ROOT / "vendor"))

import langdetect  # noqa: E402

langdetect.DetectorFactory.seed = 0

from ifeval import utils as ifeval_utils  # noqa: E402

TMPL = "<|im_start|>user\n{p}<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
EOS = {151645, 151643}
MAX_NEW = 1024  # registered candidate; frozen at checkpoint ii
WAVE_LAYERS = range(20, 28)


def load_ifeval(path):
    return [json.loads(line) for line in open(path)]


def score_response(row, response):
    """four booleans/lists for one prompt via the vendored upstream code.

    REGISTERED PIN: upstream build_description draws from the global
    `random` module when kwargs are invalid — in the 541 exactly two
    rows (keys 1122, 1129: letter_frequency with non-a-z letters) are
    random-state-sensitive. We seed per-row by key so scoring is a pure
    function of (row, response), order-independent."""
    import random
    random.seed(row["key"])
    return ifeval_utils.process_results(row, [response])


def aggregate(per_prompt):
    """the four registered IFEval metrics from per-prompt score dicts."""
    n = len(per_prompt)
    return {
        "prompt_level_strict_acc": sum(p["prompt_level_strict_acc"] for p in per_prompt) / n,
        "inst_level_strict_acc": ifeval_utils.agg_inst_level_acc(
            [p["inst_level_strict_acc"] for p in per_prompt]),
        "prompt_level_loose_acc": sum(p["prompt_level_loose_acc"] for p in per_prompt) / n,
        "inst_level_loose_acc": ifeval_utils.agg_inst_level_acc(
            [p["inst_level_loose_acc"] for p in per_prompt]),
    }


def generate_cached(m, tok, prompt, bias_fn=None, max_new=MAX_NEW, deadline_s=None):
    """THE generator for every arm: pinned template, KV-cached greedy,
    registered EOS/max_new. bias_fn(h20, prompt_len, past_len) -> bias
    tensor (t, past_len + t) or None, computed from the SAME forward's
    layer-20 input via a mid-forward hook (train/test same-position
    semantics; h20 is (b, t, d)); applied at layers 20-27. Base arm
    passes bias_fn=None. Returns (text, n_generated, truncated)."""
    import torch

    from stencil.qwen3 import KVCache

    ids = tok.encode(TMPL.format(p=prompt)).ids
    P = len(ids)
    cache = KVCache()
    out = []

    def make_hook(past):
        def hook(h20):
            row = bias_fn(h20, P, past)
            if row is None:
                return None
            return {layer: row for layer in WAVE_LAYERS}
        return (20, hook)

    t0 = time.monotonic()
    timed_out = False
    with torch.no_grad():
        hook = make_hook(0) if bias_fn is not None else None
        logits = m(torch.tensor([ids], device="cuda"), cache=cache, bias_hook=hook)
        nxt = int(logits[0, -1].argmax())
        while nxt not in EOS and len(out) < max_new:
            if deadline_s is not None and time.monotonic() - t0 > deadline_s:
                timed_out = True
                break
            out.append(nxt)
            hook = make_hook(cache.length) if bias_fn is not None else None
            logits = m(torch.tensor([[nxt]], device="cuda"), cache=cache, bias_hook=hook)
            nxt = int(logits[0, -1].argmax())
    return tok.decode(out), len(out), len(out) >= max_new, timed_out


def make_wave_bias_fn(ctrl, state):
    """the registered consumer adapter (v3.1/v3.2): at prefill, stash the
    prompt's h20 as ledger keys AND bias the SCORED final row from its
    own h20 (the first response token — or the loglikelihood decision
    row — is wave-influenced); per generation step, bias the current
    row over prompt positions. Same-position semantics throughout."""
    import torch

    def bias_fn(h20, P, past):
        if past == 0:
            state["K"] = h20[0, :P].float()
            row_p = ctrl(h20[0, P - 1:P].float(), state["K"])
            b = torch.zeros(P, P, device="cuda")
            b[-1, :P] = row_p[0]
            state["prefill_field"] = row_p.detach()
            return b
        row_p = ctrl(h20[0, -1:].float(), state["K"])
        row = torch.zeros(1, past + 1, device="cuda")
        row[0, :P] = row_p[0]
        return row
    return bias_fn


def wave_hook_for_prefill(ctrl, P):
    """single-forward loglikelihood variant of the adapter: returns a
    (layer, fn) bias_hook that biases only the final (scored) row."""
    import torch

    def hook(h20):
        K = h20[0, :P].float()
        row_p = ctrl(h20[0, P - 1:P].float(), K)
        b = torch.zeros(P, P, device="cuda")
        b[-1, :P] = row_p[0]
        return {layer: b for layer in WAVE_LAYERS}
    return (20, hook)


def provenance_pins(root, extra_files=()):
    """the registered resume pin set (v4.1): sha256 of trunk, tokenizer,
    the execution modules, and the vendored IFEval verifier tree, plus
    any extra files (controllers, datasets, the sealed runner)."""
    import hashlib
    from pathlib import Path as _P
    root = _P(root)
    files = [
        "models/qwen3-1.7b.pt",
        "models/qwen3-1.7b-hf/tokenizer.json",
        "src/stencil/bench.py",
        "src/stencil/qwen3.py",
        "src/stencil/wave.py",
    ]
    pins = {}
    for f in files:
        pins[f] = hashlib.sha256((root / f).read_bytes()).hexdigest()
    tree = hashlib.sha256()
    for vf in sorted((root / "vendor" / "ifeval").glob("*.py")):
        tree.update(vf.read_bytes())
    pins["vendor/ifeval(tree)"] = tree.hexdigest()
    for f in extra_files:
        pins[str(f)] = hashlib.sha256((root / f).read_bytes()).hexdigest()
    return pins


def make_deficit_hook(ctrl, state, prompt_spans, tau, b_max):
    """v4.5 deficit-triggered adapter (registered): the FROZEN wave's
    q/k scores select the governing constraint span per generated row
    (first-index tie-break); each biased layer then gates per head on
    the measured post-softmax mass (zero bias when psi >= tau).
    prompt_spans: list of (start, end) token spans of the prompt's
    Constraint: sentences. state stashes K at prefill and logs every
    selection into state['log']."""
    import torch
    import torch.nn.functional as F

    def fn(h20):
        if "K" not in state:  # prefill: stash keys; NO intervention
            state["K"] = h20[0].float()
            state.setdefault("log", [])
            return {}
        q = F.normalize(ctrl.W_q(h20[0, -1:].float()), dim=-1)
        k = F.normalize(ctrl.W_k(state["K"]), dim=-1)
        scores = (q @ k.T)[0]
        if not prompt_spans:
            return {}
        span_scores = [float(scores[a:b].mean()) for a, b in prompt_spans]
        best = max(range(len(prompt_spans)), key=lambda i: (span_scores[i], -i))
        a, b = prompt_spans[best]
        T_total = state["cache_len"] + 1
        mask = torch.zeros(T_total, dtype=torch.bool, device="cuda")
        mask[a:b] = True
        state["log"].append({"span": best, "score": round(span_scores[best], 4)})
        return {layer: (mask, tau, b_max) for layer in WAVE_LAYERS}
    return (20, fn)


def generate_deficit(m, tok, prompt, ctrl, prompt_spans, tau, b_max,
                     max_new=MAX_NEW, deadline_s=None):
    """cached greedy generation with the deficit-triggered wave."""
    import torch

    from stencil.qwen3 import KVCache

    ids = tok.encode(TMPL.format(p=prompt)).ids
    cache = KVCache()
    out = []
    state = {}
    hook = make_deficit_hook(ctrl, state, prompt_spans, tau, b_max)
    t0 = time.monotonic()
    timed_out = False
    with torch.no_grad():
        state["cache_len"] = 0
        logits = m(torch.tensor([ids], device="cuda"), cache=cache, deficit_hook=hook)
        nxt = int(logits[0, -1].argmax())
        while nxt not in EOS and len(out) < max_new:
            if deadline_s is not None and time.monotonic() - t0 > deadline_s:
                timed_out = True
                break
            out.append(nxt)
            state["cache_len"] = cache.length
            logits = m(torch.tensor([[nxt]], device="cuda"), cache=cache, deficit_hook=hook)
            nxt = int(logits[0, -1].argmax())
    return tok.decode(out), len(out), len(out) >= max_new, timed_out, state.get("log", [])
