# ruff: noqa: E501
"""PRESS-PLAN H4: the T0.1 trace writer must round-trip every event field
exactly and produce a stable content digest (trace is evidence; silent
lossiness would poison every offline rung)."""
import torch

from stencil.t2_trace import TraceWriter, load_trace


def _event(i):
    return {
        "seed": 13_000_000 + i, "work_turn": 3, "step": 7 + i,
        "pred_type": "prefix",
        "h20": torch.arange(8, dtype=torch.float16) + i,
        "timing_logits": torch.tensor([0.1, 0.2, 0.3, 0.4]) * (i + 1),
        "candidates": [
            {"type": "prefix", "value": "calc", "source": "live", "span": (5, 9)},
            {"type": "prefix", "value": "util", "source": "distractor", "span": (40, 44)},
        ],
        "qk_scores": [1.5 + i, -0.5],
        "cos_scores": [0.9, 0.1],
        "ledger": {"prefix": "calc"},
        "cell": "active",
    }


def test_round_trip(tmp_path):
    p = tmp_path / "trace.pt"
    w = TraceWriter(p)
    w.add_event(_event(0))
    w.add_event(_event(1))
    w.add_work({"seed": 13_000_000, "work_turn": 3, "arm": "base", "parse": True, "exec_ok": False, "adherent": {"op1": True}})
    w.close()
    tr = load_trace(p)
    assert len(tr["events"]) == 2 and len(tr["works"]) == 1
    e = tr["events"][0]
    assert e["seed"] == 13_000_000 and e["candidates"][1]["source"] == "distractor"
    assert torch.equal(e["h20"], torch.arange(8, dtype=torch.float16))
    assert tr["works"][0]["exec_ok"] is False


def test_digest_stable_and_order_sensitive(tmp_path):
    a, b, c = tmp_path / "a.pt", tmp_path / "b.pt", tmp_path / "c.pt"
    for path, order in ((a, (0, 1)), (b, (0, 1)), (c, (1, 0))):
        w = TraceWriter(path)
        for i in order:
            w.add_event(_event(i))
        w.close()
    assert load_trace(a)["digest"] == load_trace(b)["digest"]
    assert load_trace(a)["digest"] != load_trace(c)["digest"]


def test_unclosed_writer_refuses_load(tmp_path):
    p = tmp_path / "t.pt"
    w = TraceWriter(p)
    w.add_event(_event(0))
    # no close() -> load must fail loudly, not return partial data
    import pytest
    with pytest.raises(FileNotFoundError):
        load_trace(p)
