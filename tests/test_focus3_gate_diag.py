"""Consumer checks for diagnostic attribution and budget selection, no inference."""

import copy
import json
from types import SimpleNamespace

from scripts import focus3_gate_diag as d
from stencil import focus3 as f


def saved_episode():
    return [d.read(p) for p in sorted((d.V8 / "records").glob("setup_0_00_C_*.json"))]


def test_projection_counts_all_five_arms_and_probes_and_scales_by_resources():
    selection = d.projection(100, [10], 12)
    assert selection["n"] == 64
    assert selection["alternatives"]["64"]["gate_seconds"] == 4000
    assert selection["alternatives"]["64"]["probe_count"] == 96
    assert selection["alternatives"]["64"]["probe_seconds"] == 200
    assert d.projection(100, [18], 12)["n"] == 48
    assert d.projection(100, [25], 12)["n"] == 0


def test_false_admissions_use_exact_unauthorized_consumer():
    records = [d.read(p) for p in sorted((d.V8 / "records").glob("*.json"))]
    found = [
        a
        for ep in sorted({r["episode"] for r in records})
        for a in d.false_rows([r for r in records if r["episode"] == ep])
    ]
    assert len(found) == 11
    assert sum(a["category"] == "one-shot payload request" for a in found) == 8
    assert sum(a["category"] == "inert quote" for a in found) == 3
    assert all(a["probability_rule"] >= 0.95 for a in found)


def test_probe_preserves_candidate_history_and_removes_only_one_rendered_row(
    tmp_path, monkeypatch
):
    rr = saved_episode()
    admission = d.false_rows(rr)[0]
    rec = d.exposures(rr, admission)[-1]
    for r in rr:
        r["generation"] = dict(
            text='{"answer":[],"tag":7}',
            output_ids=[1],
            eos=d.g.focus2.EOS,
            pair_ids=[r["turn_index"] + 5],
        )
        r["score"] = f.score(r["turn"], r["generation"]["text"], [1], d.g.focus2.EOS)
        r["rendered_request"] = f.render(
            r["turn"]["text"], [SimpleNamespace(**row) for row in r["live"]]
        )
    before = copy.deepcopy(rr)
    calls = []

    class Trunk:
        def answer(self, history, text):
            calls.append((copy.deepcopy(history), text))
            return dict(
                text='{ "tag": 7, "answer": [] }',
                output_ids=[2],
                eos=d.g.focus2.EOS,
                prompt_ids=[9],
                pair_ids=[10],
            )

    monkeypatch.setattr(d, "OUT", tmp_path)
    result = d.probe(Trunk(), rr, admission, rec)
    assert rr == before
    assert calls[0][0] == [
        r["generation"] for r in rr if r["turn_index"] < rec["turn_index"]
    ]
    assert calls[0][1] != rec["rendered_request"]
    assert admission["row"]["id"] not in {
        r["id"] for r in json.loads(calls[0][1].splitlines()[1])
    }
    assert result["token_changed"] and result["text_changed"]
    assert not result["semantic_changed"] and not result["score_changes"]
    assert len(list((tmp_path / "probes").glob("*.json"))) == 1
