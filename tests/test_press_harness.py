# ruff: noqa: E501
"""PRESS-PLAN H1/H2 harness tests — red-first.

H1: the "policy" arm's callable returns (candidate_span | None,
diagnostics); the RUNNER applies the registered guards (threshold on
diagnostics["score"], ledger-membership of the span) and applies the
surviving span verbatim.
H2: per-step press-event log records pre-guard decision, rejection
reason ("below-threshold" | "out-of-ledger"), and applied span.

Uses a fake model/tokenizer so guard logic and logging are exercised
deterministically on CPU; H3 (wrong-span non-vacuity on the real model)
lives in test_press_harness_gpu.py.
"""
import torch

from stencil.t2_runner import run_policy_session


class FakeTok:
    """Vocab of single characters; id == ord(char)."""

    def encode(self, text):
        class Enc:
            def __init__(self, t):
                self.ids = [ord(c) for c in t]
                self.offsets = [(i, i + 1) for i in range(len(t))]
        return Enc(text)

    def decode(self, ids):
        return "".join(chr(i) for i in ids)


class FakeModel:
    """Emits a fixed string then the ``` terminator; records the
    attn_bias passed at each generation step."""

    def __init__(self, emit="x`````"):
        self.emit = emit
        self.biases = []

    def __call__(self, toks, attn_bias=None):
        self.biases.append(attn_bias)
        step = min(len(self.biases) - 1, len(self.emit) - 1)
        nxt = ord(self.emit[step])
        out = torch.full((1, toks.shape[1], 130000), -1e9)
        out[0, -1, nxt] = 0.0
        return out


PROMPT = "PROMPT with ledger sentence here."
LEDGER_SPANS = {"prefix": (7, 22)}  # token span of the "ledger sentence" region


def run(policy, threshold=0.5):
    model, tok = FakeModel(), FakeTok()
    log = []
    run_policy_session(model, tok, PROMPT, LEDGER_SPANS, policy,
                       threshold=threshold, press_log=log, max_new=6)
    return model, log


def test_policy_span_applied_verbatim():
    # candidate inside the ledger region, score above threshold -> applied
    policy = lambda model, toks, ptxt, text: ((8, 12), {"score": 0.9})
    model, log = run(policy)
    applied = [e for e in log if e["applied"] is not None]
    assert applied and applied[0]["applied"] == (8, 12)
    assert applied[0]["rejected"] is None
    # the bias actually carried the span columns at that step
    step_bias = model.biases[applied[0]["step"]]
    assert step_bias is not None
    b = next(iter(step_bias.values()))
    assert float(b[-1, 8:12].min()) > 0 and float(b[-1, :8].max()) == 0


def test_guard_below_threshold():
    policy = lambda model, toks, ptxt, text: ((8, 12), {"score": 0.4})
    model, log = run(policy, threshold=0.5)
    assert all(e["applied"] is None for e in log)
    rej = [e for e in log if e["pre_guard"] is not None]
    assert rej and all(e["rejected"] == "below-threshold" for e in rej)
    assert all(ab is None for ab in model.biases)


def test_guard_out_of_ledger():
    # span outside every ledger sentence span -> rejected AFTER threshold
    policy = lambda model, toks, ptxt, text: ((0, 3), {"score": 0.9})
    model, log = run(policy)
    rej = [e for e in log if e["pre_guard"] is not None]
    assert rej and all(e["rejected"] == "out-of-ledger" for e in rej)
    assert all(ab is None for ab in model.biases)


def test_null_decision_logged():
    policy = lambda model, toks, ptxt, text: (None, {"score": float("-inf")})
    model, log = run(policy)
    assert len(log) > 0
    assert all(e["pre_guard"] is None and e["applied"] is None and e["rejected"] is None for e in log)


def test_certification_failure_event_is_pre_structural_guard():
    """PRESS-PLAN: the certification failure event is a non-NULL decision
    surviving the numeric threshold BEFORE the ledger-membership guard —
    derivable from the log as pre_guard != None and rejected != 'below-threshold'."""
    policy = lambda model, toks, ptxt, text: ((0, 3), {"score": 0.9})
    _, log = run(policy)
    failures = [e for e in log if e["pre_guard"] is not None and e["rejected"] != "below-threshold"]
    assert failures  # out-of-ledger events DO count as certification failures
