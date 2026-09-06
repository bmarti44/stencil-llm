import json

import pytest

from stencil.focus.slab import SYSTEM_PROMPT, EnvelopeError, Executor, parse_envelope


def test_prompt_example():
    assert '{"calls":[{"op":"test"}],"report":{"status":"ok"}}' in SYSTEM_PROMPT
    assert "report is an object with keys status" in SYSTEM_PROMPT
    assert "test takes no path" in SYSTEM_PROMPT


def test_registered_tolerances():
    log = []
    output = parse_envelope(
        '{"calls":[{"op":"test","path":"policy.py"}],"status":"ok","task":"A","delivery":"staged","verbose":true}',
        log,
    )
    assert output == dict(
        calls=[dict(op="test")], report=dict(status="ok", task="A", delivery="staged")
    )
    assert [x["tolerance"] for x in log] == ["lift_report", "test_path"]
    assert log[0]["dropped"] == dict(verbose=True)
    assert log[1]["path"] == "policy.py"
    assert parse_envelope(json.dumps(output), []) == output


@pytest.mark.parametrize(
    "text",
    [
        '{"calls":[],"status":"ok","verbose":True}',
        '{"calls":[],"status":"ok"}]',
        "[]",
        '{"report":{}}',
        '{"calls":[],"report":null}',
        '{"calls":[],"report":{},"status":"ok"}',
    ],
)
def test_no_unregistered_repairs(text):
    with pytest.raises(EnvelopeError):
        parse_envelope(text)


def test_executor_feedback_and_schema(tmp_path):
    for path in ("core.py", "policy.py"):
        (tmp_path / path).write_text("")
    ex = Executor(tmp_path, [])
    for text in ("{broken", "[]"):
        feedback = ex.run(text)
        assert feedback["executed"] == []
        assert feedback["results"] == [
            dict(error="envelope", expected='{"calls":[...],"report":{"status":"ok"}}')
        ]
    feedback = ex.run(
        '{"calls":[{"op":"test","path":"policy.py","extra":1}],"status":"ok"}'
    )
    assert not feedback["executed"]
    assert feedback["results"] == [dict(error="call schema")]
    assert len(feedback["tolerances"]) == 2


def test_recovery_reproduces_committed_records():
    from stencil.focus.pilot_recovery import FROZEN, recover

    summary, rows = recover()
    assert summary == json.loads((FROZEN / "recovered-summary.json").read_text())
    assert rows == [
        json.loads(x)
        for x in (FROZEN / "recovered-records.jsonl").read_text().splitlines()
    ]
    assert summary["executed_calls"] == 95
    assert sum(len(r["execution"]["executed"]) for r in rows) == 190


def test_gate_token_bytes_and_default():
    from stencil.focus.pilot2 import EXPERTS_IMPLEMENTATION, token_bytes

    assert EXPERTS_IMPLEMENTATION == "grouped_mm"
    assert token_bytes([1, 2], 3) == token_bytes([1, 2, 3], None)
    assert token_bytes([1, 2], 3) != token_bytes([1, 2], None)


@pytest.mark.parametrize("changed,passes", [((), True), ((1,), True), ((1, 2), False)])
def test_parity_gate_threshold_and_literal_records(
    tmp_path, monkeypatch, changed, passes
):
    from types import SimpleNamespace

    import numpy as np

    from stencil.focus import pilot2
    from stencil.focus.loop import DecodeResult

    frozen = [
        r
        for r in pilot2.lines(pilot2.FROZEN / "records.jsonl")
        if r["oracle_checker_results"][0]["mode"] == "sequential"
    ]
    counter = iter(range(64))

    class FakeDecoder:
        def __init__(self, *args, **kwargs):
            self.layers = (8, 16, 24, 32, 40)
            self.handles = []
            self.consumed = [()]

        def close(self):
            pass

        def _hook(self, layer):
            return None

        def __call__(self, requests):
            i = next(counter)
            row = frozen[i]
            assert list(requests[0].prompt_ids) == row["rendered_token_ids"]
            ids = list(row["output_token_ids"])
            if i in changed:
                ids[0] += 1
            return [DecodeResult("", tuple(ids), row["eos"], row["truncated"])], [
                dict(
                    prompt_hidden=np.ones((5, 4), dtype="float16"),
                    generated_mean=np.ones((5, 4), dtype="float16"),
                    generated_forward_tokens=1,
                    decode_seconds=1,
                    deadline_hit=False,
                )
            ]

    layer = SimpleNamespace(
        register_forward_hook=lambda hook: SimpleNamespace(remove=lambda: None)
    )
    model = SimpleNamespace(model=SimpleNamespace(layers=[layer] * 40))
    monkeypatch.setattr(pilot2, "RetainedDecoder", FakeDecoder)
    result = pilot2.parity(model, None, tmp_path, float("inf"))
    assert result["complete"] and result["compared"] == 64
    assert result["passed"] == passes
    assert result["divergences"] == len(changed)
    actual = pilot2.lines(tmp_path / "parity-records.jsonl")
    assert all(actual[i]["first_divergence"] == 0 for i in changed)
